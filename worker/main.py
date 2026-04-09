import asyncio
import json
import uuid
import logging
import time
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaException, KafkaError

from worker.config import (
    KAFKA_BROKER,
    KAFKA_TOPIC,
    KAFKA_DLQ_TOPIC,
    KAFKA_GROUP,
    BUFFER_MAX_SIZE,
    BUFFER_FLUSH_INTERVAL,
)
from worker.db import bulk_insert_market_trades
from worker.execution import execute_copy_trades
from worker.dlq import send_to_dlq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("worker")


def init_consumer() -> Consumer:
    conf = {
        "bootstrap.servers": KAFKA_BROKER,
        "group.id": KAFKA_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "session.timeout.ms": 30000,
        "max.poll.interval.ms": 300000,
    }
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC])
    logger.info("Consumer subscribed to '%s' (group=%s)", KAFKA_TOPIC, KAFKA_GROUP)
    return consumer


async def run() -> None:
    consumer = init_consumer()
    logger.info("Worker is LIVE")

    loop = asyncio.get_running_loop()
    market_trade_buffer: list = []
    last_flush = time.time()

    try:
        while True:
            msg = await loop.run_in_executor(None, consumer.poll, 0.1)
            now = time.time()

            if msg is not None:
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error("Kafka error: %s", msg.error())
                    continue

                raw_value = msg.value()
                try:
                    data = json.loads(raw_value.decode("utf-8"))
                except Exception as e:
                    send_to_dlq(KAFKA_BROKER, KAFKA_DLQ_TOPIC, raw_value, f"JSON decode: {e}")
                    await loop.run_in_executor(None, lambda: consumer.commit(asynchronous=False))
                    continue

                trader_profile_id = data.get("trader_profile_id")
                if not trader_profile_id:
                    logger.warning("Signal missing trader_profile_id, recording to hypertable only")

                market_trade_buffer.append({
                    "trade_id": str(uuid.uuid4()),
                    "symbol": data.get("symbol", "UNKNOWN"),
                    "side": data.get("side", "?"),
                    "price": float(data.get("price", 0)),
                    "qty": float(data.get("qty", 0)),
                    "timestamp": datetime.now(timezone.utc),
                })

                try:
                    if trader_profile_id:
                        await execute_copy_trades(data, trader_profile_id)
                except Exception as e:
                    send_to_dlq(KAFKA_BROKER, KAFKA_DLQ_TOPIC, raw_value, f"Execution error: {e}")
                    logger.error("Execution failed for signal: %s", e)

            time_since_flush = now - last_flush
            should_flush = (
                len(market_trade_buffer) >= BUFFER_MAX_SIZE
                or (len(market_trade_buffer) > 0 and time_since_flush >= BUFFER_FLUSH_INTERVAL)
            )

            if should_flush:
                batch = market_trade_buffer.copy()
                market_trade_buffer.clear()
                last_flush = now

                logger.info("Flushing %d trades to TimescaleDB hypertable", len(batch))
                db_ok = await bulk_insert_market_trades(batch)

                if db_ok:
                    await loop.run_in_executor(None, lambda: consumer.commit(asynchronous=False))
                    logger.info("Batch committed: %d rows inserted", len(batch))
                else:
                    logger.error("DB batch insert failed — offset NOT committed")

    except asyncio.CancelledError:
        logger.info("Worker cancelled")
    except Exception as e:
        logger.critical("Worker crashed: %s", e, exc_info=True)
    finally:
        consumer.close()
        logger.info("Kafka consumer closed")


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
