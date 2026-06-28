import razorpay
from django.conf import settings


# 🔐 Razorpay client initialization (safe)
client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_SECRET
))


# 💳 Create Razorpay order
def create_razorpay_order(amount, currency="INR"):

    if not amount:
        raise ValueError("Amount is required for Razorpay order")

    try:
        order_data = {
            "amount": int(amount),  # amount must be in paise
            "currency": currency,
            "payment_capture": 1
        }

        order = client.order.create(order_data)
        return order

    except Exception as e:
        # Log real error (important for debugging)
        print("❌ Razorpay Order Creation Failed:", str(e))

        # Fail clearly instead of returning fake order
        raise Exception("Razorpay order creation failed")