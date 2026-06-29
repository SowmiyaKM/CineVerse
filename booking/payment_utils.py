import hmac
import hashlib
from django.conf import settings


# 🔐 Verify Razorpay signature (server-side security)
def verify_payment_signature(order_id, payment_id, signature):

    if not order_id or not payment_id or not signature:
        return False

    message = f"{order_id}|{payment_id}"

    generated_signature = hmac.new(
        settings.RAZORPAY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(generated_signature, signature)