from __future__ import annotations

import hashlib
import hmac
import uuid
from functools import lru_cache

import razorpay

from app.config import settings
from app.utils.errors import api_error


DEMO_SIGNATURE = "demo_signature"


@lru_cache
def get_razorpay_client() -> razorpay.Client:
    if not settings.razorpay_enabled:
        raise api_error(503, "Razorpay is not configured", "razorpay_not_configured")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


async def create_order(amount_rupees: float, receipt: str, notes: dict[str, str] | None = None) -> dict:
    amount = int(round(amount_rupees * 100))
    if not settings.razorpay_enabled:
        return {
            "id": f"order_demo_{uuid.uuid4().hex[:18]}",
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {},
            "mode": "demo",
        }

    client = get_razorpay_client()
    return client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes or {},
        }
    )


def verify_signature(order_id: str, payment_id: str, signature: str) -> None:
    if not settings.razorpay_enabled:
        if order_id.startswith("order_demo_") and payment_id.startswith("pay_demo_") and signature == DEMO_SIGNATURE:
            return
        raise api_error(503, "Razorpay is not configured", "razorpay_not_configured")

    generated_signature = hmac.new(
        settings.razorpay_key_secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if generated_signature != signature:
        raise api_error(400, "Payment signature verification failed", "invalid_payment_signature")
