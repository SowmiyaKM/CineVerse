import hmac
import hashlib
from django.conf import settings


# 🔐 Verify Razorpay signature (server-side security)
def verify_payment_signature(order_id, payment_id, signature):

    message = f"{order_id}|{payment_id}"

    generated_signature = hmac.new(
        settings.RAZORPAY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return generated_signature == signature