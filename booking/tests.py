from django.test import TestCase
from django.utils import timezone
from django.db import transaction

from .models import Show, Seat


class SeatReservationTests(TestCase):

    def setUp(self):

        self.show = Show.objects.create(
            movie_title="Titanic",
            show_time=timezone.now()
        )

        self.seat = Seat.objects.create(
            show=self.show,
            seat_number="A1"
        )

    def test_seat_locking(self):

        self.seat.lock_for_two_minutes()
        self.seat.save()

        self.assertEqual(
            self.seat.status,
            "locked"
        )

        self.assertIsNotNone(
            self.seat.locked_until
        )

    def test_double_booking_prevention(self):

        with transaction.atomic():

            seat = (
                Seat.objects
                .select_for_update()
                .get(id=self.seat.id)
            )

            seat.status = "booked"
            seat.save()

        updated = Seat.objects.get(id=self.seat.id)

        self.assertEqual(
            updated.status,
            "booked"
        )