import redis.asyncio as aioredis
import orjson
import logging

from sentinel.config import REDIS_HOST, REDIS_PORT, IDEMPOTENCY_TTL, SIGNAL_CHANNEL

logger = logging.getLogger("sentinel.broker")

class RedisBroker:

    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT) -> None:
        self._host = host
        self._port = port
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._redis = aioredis.Redis(
            host=self._host,
            port=self._port,
            decode_responses=False,     
        )
        await self._redis.ping()
        logger.info("Redis connected @ %s:%s", self._host, self._port)

    async def disconnect(self) -> None: 
        if self._redis:
            await self._redis.aclose()
            logger.info("Redis connection closed")

    async def check_idempotency(self, order_id: str) -> bool:
        key = f"sentinel:seen:{order_id}"
        was_set = await self._redis.set(key, 1, nx=True, ex=IDEMPOTENCY_TTL)

        if was_set:
            logger.debug("Order %s is NEW — processing", order_id)
            return True

        logger.warning("Order %s is a DUPLICATE — skipping", order_id)
        return False

    async def publish_signal(self, signal_data: dict) -> int:
        payload = orjson.dumps(signal_data)
        receivers = await self._redis.publish(SIGNAL_CHANNEL, payload)
        logger.info( 
            "Published signal to %s → %d subscriber(s)",
            SIGNAL_CHANNEL,
            receivers,
        )
        return receivers
