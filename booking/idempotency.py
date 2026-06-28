# Simple in-memory idempotency tracker (can upgrade to Redis later)

PROCESSED_PAYMENTS = set()


def is_duplicate(payment_id):
    return payment_id in PROCESSED_PAYMENTS


def mark_processed(payment_id):
    PROCESSED_PAYMENTS.add(payment_id)