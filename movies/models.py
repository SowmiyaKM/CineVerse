from django.db import models
from .validators import validate_youtube_url


class Movie(models.Model):

    GENRE_CHOICES = [
        ("Action", "Action"),
        ("Comedy", "Comedy"),
        ("Drama", "Drama"),
        ("Horror", "Horror"),
        ("Romance", "Romance"),
        ("Sci-Fi", "Sci-Fi"),
        ("Thriller", "Thriller"),
    ]

    LANGUAGE_CHOICES = [
        ("Tamil", "Tamil"),
        ("English", "English"),
        ("Hindi", "Hindi"),
        ("Telugu", "Telugu"),
        ("Malayalam", "Malayalam"),
    ]

    title = models.CharField(
        max_length=200,
        db_index=True
    )

    description = models.TextField()

    genre = models.CharField(
        max_length=50,
        choices=GENRE_CHOICES,
        default="Action",
        db_index=True
    )

    language = models.CharField(
        max_length=50,
        choices=LANGUAGE_CHOICES,
        default="Tamil",
        db_index=True
    )

    poster = models.URLField(
        blank=True,
        null=True,
        help_text="Paste a direct image URL for the movie poster"
    )

    trailer_url = models.URLField(
        validators=[validate_youtube_url]
    )

    def __str__(self):
        return self.title