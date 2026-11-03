from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "phone", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "phone", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        ("Rental Platform", {"fields": ("phone", "profile_image", "role")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Rental Platform", {"fields": ("email", "phone", "role")}),
    )
