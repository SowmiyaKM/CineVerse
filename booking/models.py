from django.db import models
from django.utils import timezone
from datetime import timedelta
from movies.models import Movie


class Show(models.Model):

    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='shows'
    )

    show_time = models.DateTimeField()

    def __str__(self):
        return f"{self.movie.title} - {self.show_time}"


class Seat(models.Model):

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('locked', 'Locked'),
        ('booked', 'Booked'),
    ]

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='seats'
    )

    seat_number = models.CharField(max_length=10)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    locked_until = models.DateTimeField(
        null=True,
        blank=True
    )

    booked_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def lock_for_two_minutes(self):
        self.status = 'locked'
        self.locked_until = timezone.now() + timedelta(minutes=2)
        self.save()

    def unlock(self):
        self.status = 'available'
        self.locked_until = None
        self.save()

    def book(self):
        self.status = 'booked'
        self.booked_at = timezone.now()
        self.locked_until = None
        self.save()

    def __str__(self):
        return f"{self.show.movie.title} - {self.seat_number}"


# NEW MODEL (ADDED ONLY)
class Booking(models.Model):

    email = models.EmailField()

    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE
    )

    seat_numbers = models.TextField()

    payment_id = models.CharField(
        max_length=200,
        blank=True,
        default="TEST_PAYMENT"
    )

    theater_name = models.CharField(
        max_length=200,
        default="MovieMax Cinema"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    email_sent = models.BooleanField(
        default=False
    )

    retry_count = models.IntegerField(
        default=0
    )

    def __str__(self):
        return f"{self.email} - {self.show.movie.title}"


# IMPORTANT: Auto cleanup function
def release_expired_locks():

    now = timezone.now()

    Seat.objects.filter(
        status='locked',
        locked_until__lt=now
    ).update(
        status='available',
        locked_until=None
    )