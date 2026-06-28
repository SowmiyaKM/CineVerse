from django.contrib import admin
from .models import Movie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):

    list_display = [
        "title",
        "genre",
        "language"
    ]

    list_filter = [
        "genre",
        "language"
    ]

    search_fields = [
        "title"
    ]