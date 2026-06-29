import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_booking_email_async(booking):
    """
    SAFE ENTRY POINT
    (kept name same, but now fast + non-blocking friendly)
    """
    try:
        return send_booking_email(booking)
    except Exception as e:
        logger.error(f"EMAIL TRIGGER FAILED: {e}")
        return False


def send_booking_email(booking):
    """
    Reliable email sender (simplified for production stability)
    """

    try:
        html_message = render_to_string(
            "booking/email_confirmation.html",
            {
                "movie_name": booking.show.movie.title,
                "show_time": booking.show.show_time,
                "seat_numbers": booking.seat_numbers,
                "payment_id": booking.payment_id,
                "theater_name": booking.theater_name,
            }
        )

        email = EmailMultiAlternatives(
            subject="🎟 Movie Ticket Confirmation",
            body="Your booking is confirmed.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.email],
        )

        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        booking.email_sent = True
        booking.save(update_fields=["email_sent"])

        logger.info(f"Email sent successfully to {booking.email}")
        return True

    except Exception as e:
        logger.error(f"Email FAILED: {e}")
        return False