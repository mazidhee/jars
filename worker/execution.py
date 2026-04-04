import asyncio
import hmac
import hashlib
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional

import httpx

from worker.config import BYBIT_BASE_URL, MAX_CONCURRENT_EXECUTIONS
from worker.db import (
    fetch_active_followers,
    decrypt_api_secret,
    insert_signal,
    insert_trade,
)

logger = logging.getLogger("worker.execution")

BYBIT_ORDER_ENDPOINT = "/v5/order/create"


def _sign_request(api_key: str, api_secret: str, params: str, timestamp: str, recv_window: str = "5000") -> str:
    payload = f"{timestamp}{api_key}{recv_window}{params}"
    return hmac.new(
        api_secret.encode("utf-8"),
        payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def _compute_follower_qty(
    master_qty: float,
    allocation_percent: float,
    copy_mode: str,
) -> float:
    if copy_mode == "fixed_amount":
        return master_qty
    ratio = float(allocation_percent) / 100.0
    raw = master_qty * ratio
    return round(raw, 8)


async def _place_order_for_follower(
    client: httpx.AsyncClient,
    follower: dict,
    signal: dict,
    signal_id: str,
    decrypted_secret: str,
) -> dict:
    follower_qty = _compute_follower_qty(
        master_qty=float(signal["qty"]),
        allocation_percent=float(follower["allocation_percent"]),
        copy_mode=follower["copy_mode"],
    )

    if follower_qty <= 0:
        return {"status": "skipped", "reason": "zero_qty"}

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

    import json
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
                "filled_amount": follower_qty,
                "filled_price": float(signal["price"]),
                "latency_ms": latency_ms,
            }
        else:
            return {
                "status": "failed",
                "error": data.get("retMsg", "unknown"),
                "latency_ms": latency_ms,
            }
    except Exception as e:
        latency_ms = int((time.monotonic() - start) * 1000)
        return {
            "status": "failed",
            "error": str(e),
            "latency_ms": latency_ms,
        }


async def execute_copy_trades(signal: dict, trader_profile_id: str) -> bool:
    followers = await fetch_active_followers(trader_profile_id)

    if not followers:
        logger.info("No active followers for trader %s — skipping execution", trader_profile_id)
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
        "emitted_at": datetime.fromtimestamp(int(signal["timestamp"]) / 1000, tz=timezone.utc) if signal.get("timestamp") else datetime.now(timezone.utc),
    })
    logger.info("Signal %s recorded in DB for trader %s", signal_db_id, trader_profile_id)

    secret_cache: Dict[str, str] = {}
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_EXECUTIONS)

    async def _execute_single(follower: dict) -> None:
        if follower["is_shadow_mode"]:
            shadow_qty = _compute_follower_qty(
                float(signal["qty"]),
                float(follower["allocation_percent"]),
                follower["copy_mode"],
            )
            await insert_trade({
                "id": str(uuid.uuid4()),
                "signal_id": signal_db_id,
                "subscription_id": str(follower["subscription_id"]),
                "exchange_key_id": str(follower["exchange_key_id"]),
                "status": "filled",
                "side": side_val,
                "requested_amount": shadow_qty,
                "filled_amount": shadow_qty,
                "filled_price": float(signal["price"]),
                "fee_paid": None,
                "fee_currency": None,
                "error_message": None,
                "latency_ms": 0,
                "executed_at": datetime.now(timezone.utc),
            })
            logger.info("Shadow trade recorded for subscriber %s", follower["subscriber_id"])
            return

        key_id = str(follower["exchange_key_id"])
        if key_id not in secret_cache:
            secret_cache[key_id] = decrypt_api_secret(follower["api_secret_encrypted"])

        async with semaphore:
            async with httpx.AsyncClient() as client:
                result = await _place_order_for_follower(
                    client,
                    follower,
                    signal,
                    signal_db_id,
                    secret_cache[key_id],
                )

        trade_id = str(uuid.uuid4())
        follower_qty = _compute_follower_qty(
            float(signal["qty"]),
            float(follower["allocation_percent"]),
            follower["copy_mode"],
        )

        await insert_trade({
            "id": trade_id,
            "signal_id": signal_db_id,
            "subscription_id": str(follower["subscription_id"]),
            "exchange_key_id": str(follower["exchange_key_id"]),
            "status": result["status"],
            "side": side_val,
            "requested_amount": follower_qty,
            "filled_amount": result.get("filled_amount"),
            "filled_price": result.get("filled_price"),
            "fee_paid": None,
            "fee_currency": None,
            "error_message": result.get("error"),
            "latency_ms": result.get("latency_ms"),
            "executed_at": datetime.now(timezone.utc) if result["status"] == "filled" else None,
        })

        if result["status"] == "filled":
            logger.info(
                "EXECUTED | subscriber=%s | %s %s %s @ %s | %dms",
                follower["subscriber_id"],
                signal["side"],
                follower_qty,
                signal["symbol"],
                signal["price"],
                result.get("latency_ms", 0),
            )
        else:
            logger.error(
                "FAILED  | subscriber=%s | %s | %dms",
                follower["subscriber_id"],
                result.get("error"),
                result.get("latency_ms", 0),
            )

    tasks = [_execute_single(f) for f in followers]
    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(
        "Execution complete: %d followers processed for signal %s",
        len(followers),
        signal_db_id,
    )
    return True
