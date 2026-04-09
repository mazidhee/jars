import asyncio
import contextlib
import hmac
import hashlib
import time
import logging
from typing import Optional

import orjson
import websockets
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
    InvalidHandshake,
)

from sentinel.config import (
    BYBIT_API_KEY,
    BYBIT_API_SECRET,
    BYBIT_WS_URL,
    BYBIT_WS_PING_INTERVAL,
    RECONNECT_BASE_DELAY,
    RECONNECT_MAX_DELAY,
    RECONNECT_MAX_ATTEMPTS,
    TRADER_PROFILE_ID,
)
from sentinel.models import Signal, OrderWebsocketMessage
from sentinel.broker import Broker

logger = logging.getLogger("sentinel.ws")

ACTIONABLE_STATUSES = frozenset({"Filled", "PartiallyFilled"})


class BybitWSClient:

    def __init__(self, broker: Broker) -> None:
        self._broker = broker
        self._ws: Optional[ClientConnection] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._running = False
        self._consecutive_failures = 0

    @staticmethod
    def _generate_auth_payload() -> dict:
        if not BYBIT_API_KEY or not BYBIT_API_SECRET:
            raise RuntimeError(
                "BYBIT_API_KEY and BYBIT_API_SECRET must be set in env"
            )
        expires = int((time.time() + 10) * 1000)
        signature = hmac.new(
            BYBIT_API_SECRET.encode("utf-8"),
            f"GET/realtime{expires}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        return {
            "op": "auth",
            "args": [BYBIT_API_KEY, expires, signature],
        }

    async def _authenticate(self) -> None:
        auth_msg = self._generate_auth_payload()
        await self._ws.send(orjson.dumps(auth_msg))

        raw = await asyncio.wait_for(self._ws.recv(), timeout=10)
        resp = orjson.loads(raw)

        if not resp.get("success"):
            raise RuntimeError(
                f"Bybit auth failed: {resp.get('ret_msg', resp)}"
            )
        logger.info(
            "Authenticated with Bybit (conn_id=%s)", resp.get("conn_id")
        )

    async def _subscribe(self) -> None:
        sub_msg = {"op": "subscribe", "args": ["order"]}
        await self._ws.send(orjson.dumps(sub_msg))

        raw = await asyncio.wait_for(self._ws.recv(), timeout=10)
        resp = orjson.loads(raw)

        if not resp.get("success"):
            raise RuntimeError(
                f"Subscription to 'order' failed: {resp.get('ret_msg', resp)}"
            )
        logger.info("Subscribed to order stream")



    async def _keepalive(self) -> None:
        while self._running:
            try:
                await asyncio.sleep(BYBIT_WS_PING_INTERVAL)
                if self._ws:
                    await self._ws.send(orjson.dumps({"op": "ping"}))
                    logger.debug("Ping sent")
            except ConnectionClosed:
                logger.warning("Ping failed — connection already closed")
                break
            except asyncio.CancelledError:
                break

    async def _handle_message(self, raw: bytes | str) -> None:
        try:
            data = orjson.loads(raw)
        except orjson.JSONDecodeError:
            logger.error("Failed to parse message: %s", raw[:200])
            return

        op = data.get("op")
        if op in ("pong", "ping", "auth"):
            return

        topic = data.get("topic")
        if topic != "order":
            return

        orders = data.get("data")
        if not orders:
            return

        for order_raw in orders:
            status = order_raw.get("orderStatus", "")
            if status not in ACTIONABLE_STATUSES:
                logger.debug(
                    "Ignoring order %s with status=%s",
                    order_raw.get("orderId"),
                    status,
                )
                continue

            order_id = order_raw.get("orderId", "")
            if not order_id:
                logger.error("Order missing orderId — skipping: %s", order_raw)
                continue

            is_new = await self._broker.check_idempotency(order_id)
            if not is_new:
                continue

            try:
                signal = Signal.model_validate(order_raw)
            except Exception as e:
                logger.error(
                    "Failed to validate order %s: %s", order_id, e
                )
                continue

            signal_dict = signal.model_dump()
            if TRADER_PROFILE_ID:
                signal_dict["trader_profile_id"] = TRADER_PROFILE_ID
            await self._broker.publish_signal(signal_dict)
            logger.info(
                "Signal dispatched: %s %s %s @ %s",
                signal.side,
                signal.qty,
                signal.symbol,
                signal.price,
            )


    async def _listen(self) -> None:
        async for raw in self._ws:
            await self._handle_message(raw)

    def _backoff_delay(self) -> float:
        delay = min(
            RECONNECT_BASE_DELAY * (2 ** self._consecutive_failures),
            RECONNECT_MAX_DELAY,
        )
        return delay

    async def _connect_once(self) -> None:
        logger.info("Connecting to %s", BYBIT_WS_URL)
        self._ws = await websockets.connect(
            BYBIT_WS_URL,
            ping_interval=None,
            ping_timeout=None,
            close_timeout=10,
            max_size=2**20,
        )

        await self._authenticate()
        await self._subscribe()

        self._ping_task = asyncio.create_task(
            self._keepalive(), name="bybit-keepalive"
        )

        self._consecutive_failures = 0
        logger.info("Sentinel is LIVE — listening for order fills")

        try:
            await self._listen()
        finally:
            self._ping_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._ping_task

    async def run_forever(self) -> None:
        self._running = True
        attempt = 0

        while self._running:
            try:
                await self._connect_once()
            except asyncio.CancelledError:
                logger.info("Sentinel cancelled — shutting down")
                break
            except (
                ConnectionClosed,
                ConnectionClosedError,
                ConnectionClosedOK,
                InvalidHandshake,
                OSError,
                RuntimeError,
            ) as exc:
                self._consecutive_failures += 1
                attempt += 1

                if RECONNECT_MAX_ATTEMPTS and attempt >= RECONNECT_MAX_ATTEMPTS:
                    logger.critical(
                        "Max reconnect attempts (%d) exhausted — giving up",
                        RECONNECT_MAX_ATTEMPTS,
                    )
                    raise

                delay = self._backoff_delay()
                logger.warning(
                    "Connection lost (%s). Reconnecting in %.1fs "
                    "(attempt #%d, consecutive_failures=%d)",
                    exc,
                    delay,
                    attempt,
                    self._consecutive_failures,
                )
                await asyncio.sleep(delay)
            except Exception as exc:
                logger.critical("Unexpected error: %s", exc, exc_info=True)
                raise
            finally:
                if self._ws:
                    await self._ws.close()
                    self._ws = None

    async def shutdown(self) -> None:
        logger.info("Shutdown requested")
        self._running = False
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
        if self._ws:
            await self._ws.close()



