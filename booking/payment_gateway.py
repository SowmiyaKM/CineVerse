import razorpay
from django.conf import settings

client = razorpay.Client(auth=(
    settings.RAZORPAY_KEY_ID,
    settings.RAZORPAY_SECRET
))


def create_razorpay_order(amount, currency="INR"):

    if amount is None:
        raise ValueError("Amount is required")

    amount = int(amount)

    if amount <= 0:
        raise ValueError("Invalid amount")

    order_data = {
        "amount": amount,
        "currency": currency,
        "payment_capture": 1
    }

    order = client.order.create(order_data)
    return order