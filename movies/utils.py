from urllib.parse import urlparse, parse_qs


def get_youtube_video_id(url):
    parsed = urlparse(url)

    # Short URL format
    if parsed.netloc == "youtu.be":
        return parsed.path[1:]

    # Standard watch URL
    if "youtube.com" in parsed.netloc:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        # Embed URL
        elif parsed.path.startswith("/embed/"):
            return parsed.path.split("/embed/")[1]

        # Shorts URL
        elif parsed.path.startswith("/shorts/"):
            return parsed.path.split("/shorts/")[1]

    return None