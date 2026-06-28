from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings
from .models import Booking
from .email_service import send_booking_email_async
from .models import Show, Seat
from .payment_gateway import create_razorpay_order
from .payment_utils import verify_payment_signature
from .idempotency import is_duplicate, mark_processed


# ----------------------------
# SHOW DETAILS
# ----------------------------
def show_detail(request, show_id):

    expired_seats = Seat.objects.filter(
        status="locked",
        locked_until__lt=timezone.now()
    )

    for seat in expired_seats:
        seat.status = "available"
        seat.locked_until = None
        seat.save()

    show = get_object_or_404(Show, id=show_id)
    seats = show.seats.all()

    return render(request, "booking/show_detail.html", {
        "show": show,
        "seats": seats
    })


# ----------------------------
# LOCK SEATS + CREATE ORDER
# ----------------------------
def lock_seats(request, show_id):
    print("ORDER DEBUG:", order)
    print("ORDER ID:", order.get("id"))

    if request.method == "POST":

        seat_ids = request.POST.getlist("seats")

        with transaction.atomic():

            seats = Seat.objects.select_for_update().filter(
                id__in=seat_ids,
                status="available"
            )

            if seats.count() != len(seat_ids):
                return render(request, "booking/timeout.html")

            for seat in seats:
                seat.status = "locked"
                seat.locked_until = timezone.now() + timezone.timedelta(minutes=2)
                seat.save()

        # 💡 CREATE PAYMENT ORDER HERE (IMPORTANT FIX)
        amount = seats.count() * 150 * 100  # paise

        order = create_razorpay_order(amount)

        from django.conf import settings

    return render(request, "booking/confirm.html", {
        "show_id": show_id,
        "seats": seats,
        "order_id": order["id"],
        "amount": amount,
        "RAZORPAY_KEY_ID": settings.RAZORPAY_KEY_ID
    })

    return redirect("/")


# ----------------------------
# CONFIRM BOOKING (POST PAYMENT)
# ----------------------------
def confirm_booking(request, show_id):

    if request.method == "POST":

        seat_ids = request.POST.getlist("seats")
        customer_email = request.POST.get("email")
        payment_id = request.POST.get(
            "payment_id",
            "TEST_PAYMENT"
        )

        with transaction.atomic():

            seats = Seat.objects.select_for_update().filter(
                id__in=seat_ids,
                status="locked"
            )

            expired = False

            for seat in seats:

                if seat.locked_until and seat.locked_until < timezone.now():

                    seat.status = "available"
                    seat.locked_until = None
                    seat.save()

                    expired = True

            if expired:
                return render(
                    request,
                    "booking/timeout.html"
                )

            for seat in seats:

                seat.status = "booked"
                seat.booked_at = timezone.now()
                seat.locked_until = None
                seat.save()

        # NEW: Create booking record
        if seats and customer_email:

            booking = Booking.objects.create(

                email=customer_email,

                show=seats[0].show,

                seat_numbers=", ".join(
                    seat.seat_number
                    for seat in seats
                ),

                payment_id=payment_id,

                theater_name="MovieMax Cinema"
            )

            # NEW: Background email sending
            send_booking_email_async(booking)

        return render(
            request,
            "booking/success.html",
            {
                "seats": seats
            }
        )

    return redirect("/")

# ----------------------------
# PAYMENT ORDER API (OPTIONAL)
# ----------------------------
def create_payment_order(request, show_id):

    show = get_object_or_404(Show, id=show_id)

    amount = show.seats.filter(status="locked").count() * 150 * 100

    order = create_razorpay_order(amount)

    return JsonResponse({
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"]
    })


# ----------------------------
# RAZORPAY WEBHOOK (FIXED SAFE VERSION)
# ----------------------------
@csrf_exempt
def razorpay_webhook(request):

    if request.method == "POST":

        data = json.loads(request.body)

        payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})

        payment_id = payment_entity.get("id")
        order_id = payment_entity.get("order_id")
        signature = request.headers.get("X-Razorpay-Signature")

        # 1. Idempotency check
        if is_duplicate(payment_id):
            return JsonResponse({"status": "duplicate ignored"})

        # 2. Signature verification
        if not verify_payment_signature(order_id, payment_id, signature):
            return JsonResponse({"status": "invalid signature"}, status=400)

        mark_processed(payment_id)

        # ⚠️ IMPORTANT FIX:
        # Only book seats linked to locked state (NOT all seats)
        seats = Seat.objects.filter(status="locked")

        for seat in seats:
            seat.status = "booked"
            seat.booked_at = timezone.now()
            seat.locked_until = None
            seat.save()

        return JsonResponse({"status": "payment successful"})

    return JsonResponse({"status": "invalid request"})