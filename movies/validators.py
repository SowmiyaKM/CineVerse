from django.core.exceptions import ValidationError
from urllib.parse import urlparse, parse_qs


def validate_youtube_url(url):
    parsed = urlparse(url)

    allowed_domains = [
        "youtube.com",
        "www.youtube.com",
        "youtu.be"
    ]

    if parsed.scheme not in ["http", "https"]:
        raise ValidationError(
            "Only HTTP and HTTPS URLs are allowed."
        )

    if parsed.netloc not in allowed_domains:
        raise ValidationError(
            "Only YouTube URLs are allowed."
        )

    video_id = None

    # Short URL
    if parsed.netloc == "youtu.be":
        video_id = parsed.path.strip("/")

    # Standard watch URL
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]

    # Shorts
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/shorts/")[1]

    if not video_id:
        raise ValidationError(
            "Please enter a valid YouTube video URL."
        )