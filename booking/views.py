from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
from django.conf import settings

from .models import Booking, Show, Seat
from .payment_gateway import create_razorpay_order
from .payment_utils import verify_payment_signature
from .idempotency import is_duplicate, mark_processed


# ----------------------------
# TEST EMAIL
# ----------------------------
def test_email(request):

    try:
        send_mail(
            "TEST EMAIL",
            "If you received this, Gmail SMTP is working.",
            settings.DEFAULT_FROM_EMAIL,
            ["sowmiyakmk@gmail.com"],
            fail_silently=False
        )

        return HttpResponse("EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        return HttpResponse(f"EMAIL ERROR: {e}")


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

        amount = seats.count() * 150 * 100
        order = create_razorpay_order(amount)

        seat_data = [
            {
                "id": seat.id,
                "seat_number": seat.seat_number
            }
            for seat in seats
        ]

        return render(request, "booking/confirm.html", {
            "show_id": show_id,
            "seats": seat_data,
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
        payment_id = request.POST.get("payment_id", "TEST_PAYMENT")

        print("\n========== DEBUG ==========")
        print("EMAIL:", customer_email)
        print("SEAT IDS:", seat_ids)
        print("PAYMENT ID:", payment_id)
        print("===========================\n")

        with transaction.atomic():

            seats = Seat.objects.select_for_update().filter(
                id__in=seat_ids,
                status="locked"
            )

            print("SEATS FOUND:", seats.count())
            print("CUSTOMER EMAIL:", customer_email)

            if not seats.exists():
                return render(request, "booking/timeout.html")

            expired = any(
                seat.locked_until and seat.locked_until < timezone.now()
                for seat in seats
            )

            if expired:
                return render(request, "booking/timeout.html")

            for seat in seats:
                seat.status = "booked"
                seat.booked_at = timezone.now()
                seat.locked_until = None
                seat.save()

        if seats.exists() and customer_email:

            try:
                print("CREATING BOOKING OBJECT...")

                booking = Booking.objects.create(
                    email=customer_email,
                    show=seats[0].show,
                    seat_numbers=", ".join([s.seat_number for s in seats]),
                    payment_id=payment_id,
                    theater_name="MovieMax Cinema"
                )

                print("BOOKING CREATED:", booking.id)
                print("SENDING EMAIL NOW...")

                # ✅ FIXED EMAIL (NO BROKEN ASYNC)
                try:
                    send_mail(
                        subject=f"Booking Confirmed - {booking.show}",
                        message=f"""
Hi,

Your booking is confirmed!

Seats: {booking.seat_numbers}
Theater: {booking.theater_name}

Enjoy your movie 🎬
""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[booking.email],
                        fail_silently=False
                    )
                except Exception as e:
                    print("EMAIL SEND ERROR:", e)

                print("EMAIL SENT (OR ATTEMPTED)")

            except Exception as e:
                print("BOOKING/EMAIL ERROR:", str(e))

        return render(request, "booking/success.html", {
            "seats": list(seats.values("seat_number"))
        })

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
# RAZORPAY WEBHOOK (SAFE)
# ----------------------------
@csrf_exempt
def razorpay_webhook(request):

    if request.method == "POST":

        data = json.loads(request.body)

        payment_entity = data.get("payload", {}).get("payment", {}).get("entity", {})

        payment_id = payment_entity.get("id")
        order_id = payment_entity.get("order_id")
        signature = request.headers.get("X-Razorpay-Signature")

        if is_duplicate(payment_id):
            return JsonResponse({"status": "duplicate ignored"})

        if not verify_payment_signature(order_id, payment_id, signature):
            return JsonResponse({"status": "invalid signature"}, status=400)

        mark_processed(payment_id)

        seats = Seat.objects.filter(status="locked")

        for seat in seats:
            seat.status = "booked"
            seat.booked_at = timezone.now()
            seat.locked_until = None
            seat.save()

        return JsonResponse({"status": "payment successful"})

    return JsonResponse({"status": "invalid request"})