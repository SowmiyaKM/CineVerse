from django.utils import timezone
from .models import Seat


def release_expired_seats():

    expired_seats = Seat.objects.filter(
        status='locked',
        locked_until__lt=timezone.now()
    )

    count = expired_seats.count()

    expired_seats.update(
        status='available',
        locked_until=None
    )

    if count:
        print(f"{count} expired seats released")