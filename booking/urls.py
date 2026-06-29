from django.urls import path
from . import views
from .views import create_payment_order, razorpay_webhook
from .admin_dashboard import admin_analytics


app_name = "booking"


urlpatterns = [
    path("show/<int:show_id>/", views.show_detail, name="show_detail"),

    path("lock/<int:show_id>/", views.lock_seats, name="lock_seats"),

    path("confirm/<int:show_id>/", views.confirm_booking, name="confirm_booking"),

    path("payment/create/<int:show_id>/", create_payment_order, name="create_payment_order"),

    path("payment/webhook/", razorpay_webhook, name="razorpay_webhook"),

    # EMAIL TEST ROUTE
    path("test-email/", views.test_email, name="test_email"),

    # Admin Analytics Dashboard
    path(
        "admin/analytics/",
        admin_analytics,
        name="admin_analytics"
    ),
]