import logging
import json
from confluent_kafka import Producer

logger = logging.getLogger("worker.dlq")

_producer = None

def _get_producer(broker: str) -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": broker,
            "client.id": "worker-dlq-producer",
        })
    return _producer


def send_to_dlq(broker: str, dlq_topic: str, original_value: bytes, error_msg: str) -> None:
    producer = _get_producer(broker)
    envelope = {
        "original_payload": original_value.decode("utf-8", errors="replace"),
        "error": error_msg,
    }
    try:
        producer.produce(
            topic=dlq_topic,
            value=json.dumps(envelope).encode("utf-8"),
        )
        producer.poll(0)
        logger.warning("Message pushed to DLQ topic '%s': %s", dlq_topic, error_msg)
    except Exception as e:
        logger.error("Failed to push to DLQ: %s", e)
