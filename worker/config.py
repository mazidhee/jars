import os
import sys
import base64
from dotenv import load_dotenv

load_dotenv()

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "market.trades")
KAFKA_DLQ_TOPIC = os.getenv("KAFKA_DLQ_TOPIC", "market.trades.dlq")
KAFKA_GROUP = os.getenv("KAFKA_GROUP", "jars-worker-group")

DATABASE_USER = os.getenv("DATABASE_USER", "postgres")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "postgres")
DATABASE_NAME = os.getenv("DATABASE_NAME", "jarsdb")
DATABASE_HOST = os.getenv("DATABASE_HOST", "db")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_URL = (
    f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}"
    f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    print("FATAL: SECRET_KEY is not set. Worker cannot decrypt API secrets.", file=sys.stderr)
    sys.exit(1)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

BYBIT_BASE_URL = os.getenv("BYBIT_BASE_URL", "https://api-testnet.bybit.com")

BUFFER_MAX_SIZE = int(os.getenv("WORKER_BUFFER_MAX_SIZE", "500"))
BUFFER_FLUSH_INTERVAL = float(os.getenv("WORKER_BUFFER_FLUSH_INTERVAL", "1.0"))
MAX_CONCURRENT_EXECUTIONS = int(os.getenv("MAX_CONCURRENT_TRADES", "100"))

BALANCE_LOCK_TTL = int(os.getenv("BALANCE_LOCK_TTL", "10"))


def get_fernet_key() -> bytes:
    raw = SECRET_KEY[:32].encode().ljust(32, b'\0')
    return base64.urlsafe_b64encode(raw)
