from django.core.management.base import BaseCommand
from booking.models import Movie, Show, Seat
from datetime import datetime, timedelta


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        movie_names = [
            "Avatar: Fire and Ash",
            "Minions & Monsters",
            "Voicemails for Isabelle",
            "Spider-Man: Brand New Day",
            "Obsession"
        ]

        base_time = datetime(2026, 6, 27, 10, 0)

        for movie in Movie.objects.filter(title__in=movie_names):

            existing_shows = Show.objects.filter(movie=movie).count()

            # 🔥 Ensure 3 shows per movie
            for i in range(3 - existing_shows):
                show = Show.objects.create(
                    movie=movie,
                    show_time=base_time + timedelta(hours=(existing_shows + i) * 3)
                )

                # 🔥 Immediately create seats for each new show
                for row in ["A", "B", "C"]:
                    for num in range(1, 6):
                        Seat.objects.create(
                            show=show,
                            seat_number=f"{row}{num}"
                        )

            self.stdout.write(f"{movie.title} synced (shows + seats)")