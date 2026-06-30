from pathlib import Path
import logging
import os
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-4@_z(jldpu1wq3ky&#)+mp-iw5469tbcppsw3doj&r@em&a*rr'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies',
    'booking.apps.BookingConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MovieProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MovieProject.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ----------------------------
# INTERNATIONALIZATION (FIXED)
# ----------------------------
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True


# ----------------------------
# STATIC / MEDIA
# ----------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"


# ----------------------------
# RAZORPAY CONFIG
# ----------------------------
RAZORPAY_KEY_ID = "rzp_test_T6jHisGzk57H8d"
RAZORPAY_SECRET = "7AVc62iq567BF5ZXQFjZ8Mcm"


# ----------------------------
# CACHE
# ----------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "movie-booking-cache",
    }
}


# ----------------------------
# EMAIL CONFIGURATION (GMAIL SMTP)
# ----------------------------

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER ='sowmiyakmk@gmail.com'
EMAIL_HOST_PASSWORD = 'ekrlfavipxlwwneh'
DEFAULT_FROM_EMAIL = 'sowmiyakmk@gmail.com'

# ----------------------------
# LOGGING (FOR EMAIL DEBUGGING)
# ----------------------------
logging.basicConfig(
    filename="email_debug.log",
    level=logging.INFO,
)


LOGGING = {
    "version": 1,
    "handlers": {
        "file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": "email_errors.log",
        },
    },
    "loggers": {
        "booking.email_service": {
            "handlers": ["file"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

RESEND_API_KEY = os.getenv("RESEND_API_KEY")