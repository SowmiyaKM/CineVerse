from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.db.models import Count, Q
from django.db.models.functions import TruncHour
from django.utils import timezone
from datetime import timedelta

from .models import Seat


@staff_member_required
def admin_analytics(request):

    cached_data = cache.get("admin_dashboard")

    if cached_data:
        return render(
            request,
            "booking/admin_dashboard.html",
            cached_data
        )

    now = timezone.now()

    # Revenue Analytics (Database-level aggregation)
    daily_revenue = (
        Seat.objects.filter(
            status="booked",
            booked_at__date=now.date()
        ).count() * 150
    )

    weekly_revenue = (
        Seat.objects.filter(
            status="booked",
            booked_at__gte=now - timedelta(days=7)
        ).count() * 150
    )

    monthly_revenue = (
        Seat.objects.filter(
            status="booked",
            booked_at__gte=now - timedelta(days=30)
        ).count() * 150
    )

    # Most Popular Movies
    popular_movies = (
        Seat.objects
        .filter(status="booked")
        .values("show__movie__title")
        .annotate(
            total_bookings=Count("id")
        )
        .order_by("-total_bookings")[:5]
    )

    # Busiest Shows (Occupancy Rate)
    busiest_shows = (
        Seat.objects
        .values(
            "show__id",
            "show__movie__title"
        )
        .annotate(
            total_seats=Count("id"),
            booked_seats=Count(
                "id",
                filter=Q(status="booked")
            )
        )
        .order_by("-booked_seats")[:5]
    )

    # Add occupancy percentage
    for show in busiest_shows:

        if show["total_seats"] > 0:

            show["occupancy_rate"] = round(
                (show["booked_seats"] / show["total_seats"]) * 100,
                2
            )

        else:

            show["occupancy_rate"] = 0

    # Peak Booking Hours
    peak_hours = (
        Seat.objects
        .filter(status="booked")
        .annotate(
            hour=TruncHour("booked_at")
        )
        .values("hour")
        .annotate(
            total=Count("id")
        )
        .order_by("-total")[:5]
    )

    # Cancellation Rate
    # No cancellation feature exists yet, so this is calculated safely
    total_completed = Seat.objects.filter(
        status="booked"
    ).count()

    total_cancelled = 0

    if total_completed > 0:

        cancellation_rate = f"{round((total_cancelled / total_completed) * 100, 2)}%"

    else:

        cancellation_rate = "0%"

    context = {
        "daily_revenue": daily_revenue,
        "weekly_revenue": weekly_revenue,
        "monthly_revenue": monthly_revenue,
        "popular_movies": popular_movies,
        "busiest_shows": busiest_shows,
        "peak_hours": peak_hours,
        "cancellation_rate": cancellation_rate,
    }

    # Cache for 1 minute
    cache.set(
        "admin_dashboard",
        context,
        60
    )

    return render(
        request,
        "booking/admin_dashboard.html",
        context
    )