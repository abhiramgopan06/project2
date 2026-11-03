from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("property/<int:pk>/report/", views.report_property, name="report_property"),
    path("my-reports/", views.my_reports, name="my_reports"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/reports/", views.admin_reports, name="admin_reports"),
    path("admin-dashboard/reports/<int:pk>/update/", views.admin_report_update, name="admin_report_update"),
                                                                             
    path("admin-dashboard/users/", views.admin_users, name="admin_users"),
    path("admin-dashboard/users/<int:pk>/", views.admin_user_detail, name="admin_user_detail"),
    path("admin-dashboard/properties/", views.admin_properties, name="admin_properties"),
    path("admin-dashboard/properties/<int:pk>/", views.admin_property_detail, name="admin_property_detail"),
    path("admin-dashboard/rental-requests/", views.admin_rental_requests, name="admin_rental_requests"),
    path("admin-dashboard/payments/", views.admin_payments, name="admin_payments"),
    path("admin-dashboard/maintenance/", views.admin_maintenance, name="admin_maintenance"),
]
