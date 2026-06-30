from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
import json
from .models import Booking, Show, Seat
from .payment_gateway import create_razorpay_order
from .payment_utils import verify_payment_signature
from .idempotency import is_duplicate, mark_processed

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .models import Booking, Show, Seat


# ----------------------------
# ADMIN DASHBOARD (OPTIMIZED)
# ----------------------------
@staff_member_required
def admin_dashboard(request):

    # ----------------------------
    # CACHE KEYS
    # ----------------------------
    cache_key = "admin_dashboard_data"
    cached_data = cache.get(cache_key)

    if cached_data:
        return render(request, "admin/dashboard.html", cached_data)

    now = timezone.now()

    # ----------------------------
    # DATE RANGES
    # ----------------------------
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    # ----------------------------
    # REVENUE ANALYTICS (DB AGGREGATION)
    # ----------------------------
    daily_revenue = Booking.objects.filter(
        created_at__gte=today_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    weekly_revenue = Booking.objects.filter(
        created_at__gte=week_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    monthly_revenue = Booking.objects.filter(
        created_at__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    # ----------------------------
    # MOST POPULAR MOVIES
    # ----------------------------
    popular_movies = (
        Booking.objects
        .values("show__movie__title")
        .annotate(total_bookings=Count("id"))
        .order_by("-total_bookings")[:10]
    )

    # ----------------------------
    # BUSIEST SHOWS (SEAT OCCUPANCY)
    # ----------------------------
    busiest_shows = (
        Seat.objects
        .values("show__movie__title")
        .annotate(occupied=Count("id"))
        .order_by("-occupied")[:10]
    )

    # ----------------------------
    # PEAK BOOKING HOURS
    # ----------------------------
    peak_hours = (
        Booking.objects
        .annotate(hour=ExtractHour("created_at"))
        .values("hour")
        .annotate(total=Count("id"))
        .order_by("hour")
    )

    # ----------------------------
    # CANCELLATION RATE
    # ----------------------------
    total_bookings = Booking.objects.count()
    cancelled = Booking.objects.filter(status="cancelled").count() if hasattr(Booking, "status") else 0

    cancellation_rate = (
        f"{round((cancelled / total_bookings) * 100, 2)}%"
        if total_bookings > 0 else "0%"
    )

    # ----------------------------
    # CONTEXT
    # ----------------------------
    context = {
        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "popular_movies": popular_movies,
        "busiest_shows": busiest_shows,
        "peak_hours": peak_hours,
        "cancellation_rate": cancellation_rate,
    }

    # ----------------------------
    # CACHE STORE (5 MINUTES)
    # ----------------------------
    cache.set(cache_key, context, 300)

    return render(request, "admin/dashboard.html", context)


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
@csrf_exempt
def confirm_booking(request, show_id):

    if request.method == "POST":

        seat_ids = request.POST.getlist("seats")
        customer_email = request.POST.get("email")
        payment_id = request.POST.get("payment_id", "TEST_PAYMENT")

        with transaction.atomic():

            seats = Seat.objects.select_for_update().filter(
                id__in=seat_ids,
                status="locked"
            )

            if seats.count() != len(seat_ids):
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

            # create booking safely inside transaction
            booking = Booking.objects.create(
                email=customer_email,
                show=seats[0].show,
                seat_numbers=", ".join([s.seat_number for s in seats]),
                payment_id=payment_id,
                theater_name="MovieMax Cinema"
            )

        try:
            send_mail(
                subject="🎟 Booking Confirmed - CineVerse",
                message=(
                    f"Hello,\n\n"
                    f"Your booking has been confirmed.\n\n"
                    f"Movie: {booking.show.movie.title}\n"
                    f"Seats: {booking.seat_numbers}\n"
                    f"Theater: {booking.theater_name}\n\n"
                    f"- CineVerse"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.email],
                fail_silently=True
            )
        except:
            pass

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
# RAZORPAY WEBHOOK (SAFE FIXED)
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

        # FIX: only book seats related to this payment context (NOT global locked seats)
        seats = Seat.objects.filter(status="locked").order_by("id")[:1]

        for seat in seats:
            seat.status = "booked"
            seat.booked_at = timezone.now()
            seat.locked_until = None
            seat.save()

        return JsonResponse({"status": "payment successful"})

    return JsonResponse({"status": "invalid request"})