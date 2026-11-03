from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("request/<int:property_pk>/", views.create_request, name="create_request"),
    path("my-requests/", views.my_requests, name="my_requests"),
    path("my-bookings/", views.my_bookings, name="my_bookings"),
    path("owner/requests/", views.owner_requests, name="owner_requests"),
    path("owner/requests/<int:pk>/approve/", views.approve_request, name="approve_request"),
    path("owner/requests/<int:pk>/reject/", views.reject_request, name="reject_request"),
    path("booking/<int:booking_pk>/extend/", views.request_extension, name="request_extension"),
    path("owner/extensions/", views.owner_extensions, name="owner_extensions"),
    path("owner/extensions/<int:extension_pk>/<str:decision>/", views.review_extension, name="review_extension"),
    path("owner/rentals/", views.owner_rentals, name="owner_rentals"),
    path("owner/rentals/<int:booking_pk>/agreement/", views.manage_agreement, name="manage_agreement"),
]
