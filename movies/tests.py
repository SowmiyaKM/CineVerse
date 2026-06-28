from django.test import TestCase
from django.core.exceptions import ValidationError

from .validators import validate_youtube_url
from .utils import get_youtube_video_id


class YouTubeValidationTests(TestCase):

    def test_valid_standard_url(self):
        url = "https://www.youtube.com/watch?v=abc123XYZ"
        validate_youtube_url(url)

    def test_valid_short_url(self):
        url = "https://youtu.be/abc123XYZ"
        validate_youtube_url(url)

    def test_invalid_domain(self):
        url = "https://example.com/video"

        with self.assertRaises(ValidationError):
            validate_youtube_url(url)

    def test_javascript_xss_attack(self):
        url = "javascript:alert('XSS')"

        with self.assertRaises(ValidationError):
            validate_youtube_url(url)


class YouTubeVideoIdTests(TestCase):

    def test_extract_standard_video_id(self):
        url = "https://www.youtube.com/watch?v=LuPB43YSgCs"

        self.assertEqual(
            get_youtube_video_id(url),
            "LuPB43YSgCs"
        )

    def test_extract_short_video_id(self):
        url = "https://youtu.be/LuPB43YSgCs"

        self.assertEqual(
            get_youtube_video_id(url),
            "LuPB43YSgCs"
        )

    def test_invalid_url_returns_none(self):
        url = "https://google.com"

        self.assertIsNone(
            get_youtube_video_id(url)
        )