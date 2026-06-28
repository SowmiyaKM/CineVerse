import logging
import threading
import time

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


logger = logging.getLogger(__name__)


def send_booking_email_async(booking):

    thread = threading.Thread(
        target=send_booking_email,
        args=(booking,),
        daemon=True
    )

    thread.start()


def send_booking_email(booking):

    max_retries = 3

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
                subject="Movie Ticket Confirmation",
                body="Your booking has been confirmed.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[booking.email]
            )

            email.attach_alternative(
                html_message,
                "text/html"
            )

            email.send()

            booking.email_sent = True
            booking.save()

            return

        except Exception as e:

            booking.retry_count += 1
            booking.save()

            logger.error(
                f"Email delivery failed: {e}"
            )

            time.sleep(3)
            