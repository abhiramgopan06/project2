from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.payment_history, name="history"),
    path("owner/", views.owner_payment_history, name="owner_history"),
    path("booking/<int:booking_pk>/pay/", views.make_payment, name="make_payment"),
    path("result/<int:payment_pk>/", views.payment_result, name="result"),
]
