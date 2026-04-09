import logging
from typing import List, Optional

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from cryptography.fernet import Fernet

from worker.config import DATABASE_URL, REDIS_URL, BALANCE_LOCK_TTL, get_fernet_key

logger = logging.getLogger("worker.db")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=False)
    return _redis


async def acquire_user_lock(subscriber_id: str) -> bool:
    r = await get_redis()
    key = f"worker:lock:{subscriber_id}"
    acquired = await r.set(key, "1", nx=True, ex=BALANCE_LOCK_TTL)
    return bool(acquired)


async def release_user_lock(subscriber_id: str) -> None:
    r = await get_redis()
    key = f"worker:lock:{subscriber_id}"
    await r.delete(key)


FETCH_ACTIVE_FOLLOWERS_SQL = text("""
    SELECT
        s.id               AS subscription_id,
        s.subscriber_id,
        s.copy_mode,
        s.allocation_percent,
        s.reserved_amount,
        s.is_shadow_mode,
        k.id               AS exchange_key_id,
        k.api_key,
        k.api_secret_encrypted,
        k.exchange_name
    FROM subscriptions s
    JOIN exchange_keys k
        ON k.user_id = s.subscriber_id
        AND k.is_valid = true
    WHERE s.trader_id = :trader_profile_id
      AND s.sub_status = 'active'
    ORDER BY s.subscriber_id
""")

INSERT_SIGNAL_SQL = text("""
    INSERT INTO signals (id, leader_profile_id, symbol, side, order_type, quantity, price, raw_exchange_response, emitted_at, created_at)
    VALUES (:id, :leader_profile_id, :symbol, :side, :order_type, :quantity, :price, :raw_exchange_response, :emitted_at, NOW())
    ON CONFLICT DO NOTHING
    RETURNING id
""")

INSERT_TRADE_SQL = text("""
    INSERT INTO trades (id, signal_id, subscription_id, exchange_key_id, status, side, requested_amount, filled_amount, filled_price, fee_paid, fee_currency, error_message, latency_ms, created_at, executed_at, updated_at)
    VALUES (:id, :signal_id, :subscription_id, :exchange_key_id, :status, :side, :requested_amount, :filled_amount, :filled_price, :fee_paid, :fee_currency, :error_message, :latency_ms, NOW(), :executed_at, NOW())
""")

INSERT_MARKET_TRADE_SQL = text("""
    INSERT INTO market_trades (trade_id, symbol, side, price, qty, timestamp)
    VALUES (:trade_id, :symbol, :side, :price, :qty, :timestamp)
    ON CONFLICT DO NOTHING
""")


async def fetch_active_followers(trader_profile_id: str) -> list:
    async with async_session() as session:
        result = await session.execute(
            FETCH_ACTIVE_FOLLOWERS_SQL,
            {"trader_profile_id": trader_profile_id}
        )
        return [dict(row._mapping) for row in result.fetchall()]


async def insert_signal(signal_params: dict) -> Optional[str]:
    async with async_session() as session:
        result = await session.execute(INSERT_SIGNAL_SQL, signal_params)
        await session.commit()
        row = result.fetchone()
        return str(row[0]) if row else None


async def insert_trade(trade_params: dict) -> None:
    async with async_session() as session:
        await session.execute(INSERT_TRADE_SQL, trade_params)
        await session.commit()


async def bulk_insert_market_trades(trades: List[dict]) -> bool:
    if not trades:
        return True
    try:
        async with async_session() as session:
            await session.execute(INSERT_MARKET_TRADE_SQL, trades)
            await session.commit()
            return True
    except Exception as e:
        logger.error("Bulk insert to market_trades failed: %s", e)
        return False


def decrypt_api_secret(encrypted_bytes: bytes) -> str:
    f = Fernet(get_fernet_key())
    return f.decrypt(encrypted_bytes).decode()
