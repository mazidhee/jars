import asyncio
import hmac
import hashlib
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from typing import Dict

import httpx

from worker.config import BYBIT_BASE_URL, MAX_CONCURRENT_EXECUTIONS
from worker.db import (
    fetch_active_followers,
    decrypt_api_secret,
    insert_signal,
    insert_trade,
    acquire_user_lock,
    release_user_lock,
)

logger = logging.getLogger("worker.execution")

BYBIT_ORDER_ENDPOINT = "/v5/order/create"

BYBIT_ERROR_MAP = {
    10001: "insufficient_balance",
    10003: "order_not_found",
    10004: "sign_error",
    10005: "permission_denied",
    10006: "too_many_requests",
    10010: "invalid_order_qty",
    110007: "insufficient_balance",
    110012: "insufficient_balance",
    110017: "reduce_only_rejected",
    170131: "insufficient_balance",
}


def _sign_request(api_key: str, api_secret: str, params: str, timestamp: str, recv_window: str = "5000") -> str:
    payload = f"{timestamp}{api_key}{recv_window}{params}"
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def _compute_follower_qty(
    master_qty: Decimal,
    allocation_percent: Decimal,
    copy_mode: str,
) -> Decimal:
    if copy_mode == "fixed_amount":
        return master_qty
    ratio = allocation_percent / Decimal("100")
    raw = master_qty * ratio
    return raw.quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


async def _place_order_for_follower(
    client: httpx.AsyncClient,
    follower: dict,
    signal: dict,
    decrypted_secret: str,
    follower_qty: Decimal,
) -> dict:
    if follower_qty <= 0:
        return {"status": "skipped", "reason": "zero_qty", "latency_ms": 0}

    order_body = {
        "category": "linear",
        "symbol": signal["symbol"],
        "side": signal["side"],
        "orderType": "Market",
        "qty": str(follower_qty),
        "timeInForce": "GTC",
        "orderLinkId": str(uuid.uuid4()),
    }

    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    params_str = json.dumps(order_body, separators=(",", ":"))

    signature = _sign_request(
        follower["api_key"],
        decrypted_secret,
        params_str,
        timestamp,
        recv_window,
    )

    headers = {
        "X-BAPI-API-KEY": follower["api_key"],
        "X-BAPI-SIGN": signature,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-RECV-WINDOW": recv_window,
        "Content-Type": "application/json",
    }

    start = time.monotonic()

    try:
        resp = await client.post(
            f"{BYBIT_BASE_URL}{BYBIT_ORDER_ENDPOINT}",
            headers=headers,
            json=order_body,
            timeout=10.0,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        data = resp.json()

        ret_code = data.get("retCode", -1)
        if ret_code == 0:
            result_data = data.get("result", {})
            return {
                "status": "filled",
                "order_id": result_data.get("orderId"),
                "filled_amount": float(follower_qty),
                "filled_price": float(signal["price"]),
                "latency_ms": latency_ms,
            }
        else:
            error_category = BYBIT_ERROR_MAP.get(ret_code, "unknown_error")
            error_msg = data.get("retMsg", "unknown")
            return {
                "status": "failed",
                "error": f"[{error_category}] {error_msg} (code={ret_code})",
                "latency_ms": latency_ms,
            }
    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "error": "request_timeout", "latency_ms": latency_ms}
    except Exception as e:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {"status": "failed", "error": str(e), "latency_ms": latency_ms}


async def execute_copy_trades(signal: dict, trader_profile_id: str) -> bool:
    followers = await fetch_active_followers(trader_profile_id)

    if not followers:
        logger.info("No active followers for trader %s", trader_profile_id)
        return True

    signal_db_id = str(uuid.uuid4())
    side_val = signal["side"].lower()
    order_type_val = signal.get("order_type", "Market").lower()

    await insert_signal({
        "id": signal_db_id,
        "leader_profile_id": trader_profile_id,
        "symbol": signal["symbol"],
        "side": side_val,
        "order_type": order_type_val,
        "quantity": float(signal["qty"]),
        "price": float(signal["price"]),
        "raw_exchange_response": None,
        "emitted_at": datetime.fromtimestamp(
            int(signal["timestamp"]) / 1000, tz=timezone.utc
        ) if signal.get("timestamp") else datetime.now(timezone.utc),
    })

    secret_cache: Dict[str, str] = {}
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)

    async def _execute_single(client: httpx.AsyncClient, follower: dict) -> None:
        subscriber_id = str(follower["subscriber_id"])

        locked = await acquire_user_lock(subscriber_id)
        if not locked:
            logger.warning("Could not acquire lock for subscriber %s, skipping to prevent double-spend", subscriber_id)
            await insert_trade({
                "id": str(uuid.uuid4()),
                "signal_id": signal_db_id,
                "subscription_id": str(follower["subscription_id"]),
                "exchange_key_id": str(follower["exchange_key_id"]),
                "status": "failed",
                "side": side_val,
                "requested_amount": 0,
                "filled_amount": None,
                "filled_price": None,
                "fee_paid": None,
                "fee_currency": None,
                "error_message": "double_spend_lock_contention",
                "latency_ms": 0,
                "executed_at": None,
            })
            return

        try:
            master_qty = Decimal(str(signal["qty"]))
            allocation = Decimal(str(follower["allocation_percent"]))
            follower_qty = _compute_follower_qty(master_qty, allocation, follower["copy_mode"])

            if follower["is_shadow_mode"]:
                await insert_trade({
                    "id": str(uuid.uuid4()),
                    "signal_id": signal_db_id,
                    "subscription_id": str(follower["subscription_id"]),
                    "exchange_key_id": str(follower["exchange_key_id"]),
                    "status": "filled",
                    "side": side_val,
                    "requested_amount": float(follower_qty),
                    "filled_amount": float(follower_qty),
                    "filled_price": float(signal["price"]),
                    "fee_paid": None,
                    "fee_currency": None,
                    "error_message": None,
                    "latency_ms": 0,
                    "executed_at": datetime.now(timezone.utc),
                })
                logger.info("SHADOW | subscriber=%s | %s %s %s", subscriber_id, side_val, follower_qty, signal["symbol"])
                return

            key_id = str(follower["exchange_key_id"])
            if key_id not in secret_cache:
                secret_cache[key_id] = decrypt_api_secret(follower["api_secret_encrypted"])

            async with semaphore:
                result = await _place_order_for_follower(
                    client, follower, signal, secret_cache[key_id], follower_qty,
                )

            await insert_trade({
                "id": str(uuid.uuid4()),
                "signal_id": signal_db_id,
                "subscription_id": str(follower["subscription_id"]),
                "exchange_key_id": str(follower["exchange_key_id"]),
                "status": result["status"],
                "side": side_val,
                "requested_amount": float(follower_qty),
                "filled_amount": result.get("filled_amount"),
                "filled_price": result.get("filled_price"),
                "fee_paid": None,
                "fee_currency": None,
                "error_message": result.get("error"),
                "latency_ms": result.get("latency_ms", 0),
                "executed_at": datetime.now(timezone.utc) if result["status"] == "filled" else None,
            })

            if result["status"] == "filled":
                logger.info(
                    "EXECUTED | subscriber=%s | %s %s %s @ %s | %dms",
                    subscriber_id, signal["side"], follower_qty,
                    signal["symbol"], signal["price"], result.get("latency_ms", 0),
                )
            else:
                logger.error(
                    "FAILED  | subscriber=%s | %s | %dms",
                    subscriber_id, result.get("error"), result.get("latency_ms", 0),
                )
        finally:
            await release_user_lock(subscriber_id)

    async with httpx.AsyncClient() as client:
        tasks = [_execute_single(client, f) for f in followers]
        await asyncio.gather(*tasks, return_exceptions=True)

    secret_cache.clear()

    logger.info("Execution complete: %d followers for signal %s", len(followers), signal_db_id)
    return True
