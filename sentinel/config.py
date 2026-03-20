"""
JARS Sentinel - Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All environment variables in one place. Loads from .env via python-dotenv.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# Redis
# ------------------------------------------------------------------
REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

# ------------------------------------------------------------------
# Sentinel Behavior
# ------------------------------------------------------------------
IDEMPOTENCY_TTL: int = int(os.getenv("IDEMPOTENCY_TTL", "5"))
SIGNAL_CHANNEL: str = os.getenv("SIGNAL_CHANNEL", "jars:signals")
