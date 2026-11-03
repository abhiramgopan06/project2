from django.urls import path

from . import views

app_name = "properties"

urlpatterns = [
    path("", views.property_list, name="list"),
    path("saved/", views.saved_properties, name="saved"),
    path("<int:pk>/save/", views.toggle_saved_property, name="toggle_saved"),
    path("owner/<int:pk>/verification-document/", views.upload_verification_document, name="verification_upload"),
    path("<int:pk>/", views.property_detail, name="detail"),
    path("owner/", views.owner_property_list, name="owner_property_list"),
    path("owner/expenses/", views.owner_expenses, name="owner_expenses"),
    path("owner/add/", views.property_create, name="create"),
    path("owner/<int:pk>/", views.owner_property_detail, name="owner_property_detail"),
    path("owner/<int:pk>/edit/", views.property_update, name="update"),
    path("owner/<int:pk>/delete/", views.property_delete, name="delete"),
    path("owner/<int:pk>/images/add/", views.property_image_add, name="image_add"),
    path("owner/<int:pk>/images/<int:image_pk>/delete/", views.property_image_delete, name="image_delete"),
    path("owner/<int:pk>/rooms/add/", views.room_create, name="room_create"),
    path("owner/<int:pk>/rooms/<int:room_pk>/edit/", views.room_update, name="room_update"),
    path("owner/<int:pk>/rooms/<int:room_pk>/delete/", views.room_delete, name="room_delete"),
]
