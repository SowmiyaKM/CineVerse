from django.core.management.base import BaseCommand
from booking.models import Show, Seat


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        movie_names = [
            "Avatar: Fire and Ash",
            "Minions & Monsters",
            "Voicemails for Isabelle",
            "Spider-Man: Brand New Day",
            "Obsession"
        ]

        shows = Show.objects.filter(movie__title__in=movie_names)

        for show in shows:

            if show.seats.exists():
                self.stdout.write(
                    f"Show {show.id} already has seats"
                )
                continue

            for row in ["A", "B", "C"]:
                for num in range(1, 6):

                    Seat.objects.create(
                        show=show,
                        seat_number=f"{row}{num}"
                    )

            self.stdout.write(
                f"Created 15 seats for Show {show.id}"
            )