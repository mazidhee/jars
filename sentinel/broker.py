import redis.asyncio as aioredis
import orjson
import logging
from confluent_kafka import Producer

from sentinel.config import REDIS_HOST, REDIS_PORT, IDEMPOTENCY_TTL

logger = logging.getLogger("sentinel.broker")

class Broker:   

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT) -> None:
        self._host = host
        self._port = port
        self._redis: aioredis.Redis | None = None
        self._kafka_producer: Producer | None = None

    async def connect(self) -> None:
        self._redis = aioredis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=False,     
        )
        await self._redis.ping()
        logger.info("Redis connected @ %s:%s", self._host, self._port)

        self._kafka_producer = Producer({
            'bootstrap.servers': 'kafka:29092', 
            'client.id': 'sentinel-producer',
            'acks': 'all' 
        })
        logger.info("Kafka Producer initialized")

    async def disconnect(self) -> None: 
        if self._redis: 
            await self._redis.aclose()
        if self._kafka_producer:
            self._kafka_producer.flush() 
        logger.info("Broker connections closed")

    async def check_idempotency(self, order_id: str) -> bool:
        key = f"sentinel:seen:{order_id}"
        was_set = await self._redis.set(key, 1, nx=True, ex=IDEMPOTENCY_TTL)

        if was_set:
            return True
        
        logger.warning("Order %s is a DUPLICATE — skipping", order_id)
        return False

    async def publish_signal(self, signal_data: dict) -> None:
        try:
            payload = orjson.dumps(signal_data)
            
            symbol = signal_data.get('symbol', 'UNKNOWN').encode('utf-8')
            
            self._kafka_producer.produce(
                topic='market.trades',
                value=payload,
                key=symbol
            )
            
            self._kafka_producer.poll(0) 
            
            logger.info("Pushed %s signal to Kafka", symbol.decode('utf-8'))
            
        except Exception as e:
            logger.error("Failed to publish signal to Kafka: %s", e)