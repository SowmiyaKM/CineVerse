from django.shortcuts import render, get_object_or_404
from .models import Movie
from booking.models import Show
import re
from django.core.paginator import Paginator
from django.db.models import Count


def home(request):

    movies = Movie.objects.all()

    # Multi-select filters
    selected_genres = request.GET.getlist("genre")
    selected_languages = request.GET.getlist("language")

    if selected_genres:
        movies = movies.filter(
            genre__in=selected_genres
        )

    if selected_languages:
        movies = movies.filter(
            language__in=selected_languages
        )

    # Sorting
    sort_by = request.GET.get("sort", "title")

    if sort_by == "title":
        movies = movies.order_by("title")

    elif sort_by == "-title":
        movies = movies.order_by("-title")

    # Dynamic filter counts (optimized)
    genre_query = Movie.objects.all()

    if selected_languages:
        genre_query = genre_query.filter(
            language__in=selected_languages
        )

    genre_counts = (
        genre_query
        .values("genre")
        .annotate(total=Count("id"))
        .order_by("genre")
    )

    language_query = Movie.objects.all()

    if selected_genres:
        language_query = language_query.filter(
            genre__in=selected_genres
        )

    language_counts = (
        language_query
        .values("language")
        .annotate(total=Count("id"))
        .order_by("language")
    )

    # Pagination (5 movies per page)
    paginator = Paginator(
        movies,
        5
    )

    page_number = request.GET.get("page")

    movies = paginator.get_page(page_number)

    return render(request, "movies/home.html", {
        "movies": movies,
        "genre_counts": genre_counts,
        "language_counts": language_counts,
        "selected_genres": selected_genres,
        "selected_languages": selected_languages,
        "sort_by": sort_by,
    })


def extract_video_id(url):

    if not url:
        return None

    patterns = [
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:

        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def movie_detail(request, pk):

    movie = get_object_or_404(Movie, pk=pk)

    video_id = extract_video_id(movie.trailer_url)

    shows = Show.objects.filter(movie=movie)

    return render(request, "movies/detail.html", {
        "movie": movie,
        "video_id": video_id,
        "shows": shows
    })