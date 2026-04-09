import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

IDEMPOTENCY_TTL: int = int(os.getenv("IDEMPOTENCY_TTL", "5"))
SIGNAL_CHANNEL: str = os.getenv("SIGNAL_CHANNEL", "jars:signals")

BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET", "")
TRADER_PROFILE_ID: str = os.getenv("TRADER_PROFILE_ID", "")
BYBIT_WS_URL: str = os.getenv("BYBIT_WS_URL", "wss://stream.bybit.com/v5/private")
BYBIT_WS_PING_INTERVAL: int = int(os.getenv("BYBIT_WS_PING_INTERVAL", "20"))

RECONNECT_BASE_DELAY: float = float(os.getenv("RECONNECT_BASE_DELAY", "1.0"))
RECONNECT_MAX_DELAY: float = float(os.getenv("RECONNECT_MAX_DELAY", "60.0"))
RECONNECT_MAX_ATTEMPTS: int = int(os.getenv("RECONNECT_MAX_ATTEMPTS", "0"))  # 0 = infinite
