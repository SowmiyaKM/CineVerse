import razorpay
from django.conf import settings
import uuid


# ✅ SAFE CLIENT INIT (prevents crash if settings missing)
client = razorpay.Client(
    auth=(
        getattr(settings, "RAZORPAY_KEY_ID", ""),
        getattr(settings, "RAZORPAY_SECRET", "")
    )
)


# 🔐 Create Razorpay order (safe + stable)
def create_razorpay_order(amount, currency="INR"):

    if not amount:
        raise ValueError("Amount is required for Razorpay order")

    idempotency_key = str(uuid.uuid4())

    order_data = {
        "amount": int(amount),  # already passed in paise from view
        "currency": currency,
        "payment_capture": 1
    }

    try:
        order = client.order.create(
            data=order_data,
            headers={
                "X-Idempotency-Key": idempotency_key
            }
        )
        return order

    except Exception as e:
        print("Razorpay Order Error:", e)
        return {
            "id": None,
            "amount": amount,
            "currency": currency
        }