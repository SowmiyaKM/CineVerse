import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


def send_booking_email_async(booking):
    """
    SAFE ENTRY POINT
    (no threading, no async crash risk on Render)
    """
    try:
        return send_booking_email(booking)
    except Exception as e:
        logger.error(f"EMAIL TRIGGER FAILED: {e}")
        return False


def send_booking_email(booking):
    """
    Reliable email sender with safe retry
    """

    max_retries = 2  # keep small to avoid Render timeout

    for attempt in range(max_retries):

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
            booking.retry_count = 0
            booking.save(update_fields=["email_sent", "retry_count"])

            logger.info(f"Email sent successfully to {booking.email}")
            return True

        except Exception as e:

            logger.error(f"Email attempt {attempt + 1} failed: {e}")

            booking.retry_count = (booking.retry_count or 0) + 1
            booking.save(update_fields=["retry_count"])

    logger.error(f"Email FAILED permanently for booking {booking.id}")
    return False