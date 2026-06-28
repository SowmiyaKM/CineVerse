import razorpay
from django.conf import settings

client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_SECRET
))

def create_razorpay_order(amount, currency="INR"):

    if not amount:
        raise ValueError("Amount is required")

    order_data = {
        "amount": int(amount),
        "currency": currency,
        "payment_capture": 1
    }

    # IMPORTANT: no try/except hiding errors
    order = client.order.create(order_data)
    return order