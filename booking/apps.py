from django.apps import AppConfig


class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):

        from apscheduler.schedulers.background import BackgroundScheduler
        from .tasks import release_expired_seats

        scheduler = BackgroundScheduler()

        scheduler.add_job(
            release_expired_seats,
            'interval',
            seconds=30
        )

        scheduler.start()