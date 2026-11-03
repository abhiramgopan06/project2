from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("google/login/", views.google_login, name="google_login"),
    path("google/callback/", views.google_callback, name="google_callback"),
    path("login/", views.user_login, name="login"),
    path("technician-login/", views.technician_login, name="technician_login"),
    path("logout/", views.user_logout, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("owner-dashboard/", views.owner_dashboard, name="owner_dashboard"),
    path("tenant-dashboard/", views.tenant_dashboard, name="tenant_dashboard"),
    path("profile/", views.profile, name="profile"),
]
