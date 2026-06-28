from django.core.management.base import BaseCommand
from booking.models import Movie, Show, Seat


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        for movie in Movie.objects.all():

            shows = Show.objects.filter(movie=movie).order_by("id")

            # 🔥 STEP 1: Keep only first 3 shows, delete extra empty ones
            for extra_show in shows[3:]:
                if extra_show.seats.count() == 0:
                    extra_show.delete()

            shows = Show.objects.filter(movie=movie).order_by("id")[:3]

            # 🔥 STEP 2: Ensure seats exist for valid shows
            for show in shows:

                if show.seats.exists():
                    continue

                for row in ["A", "B", "C"]:
                    for num in range(1, 6):
                        Seat.objects.create(
                            show=show,
                            seat_number=f"{row}{num}"
                        )

            self.stdout.write(f"{movie.title} cleaned + synced")