from django.contrib import admin
from .models import PropertyReport


@admin.register(PropertyReport)
class PropertyReportAdmin(admin.ModelAdmin):
    list_display = ("id", "property", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("property__title", "reporter__username", "reporter__email", "description")
    list_select_related = ("property", "reporter")
    readonly_fields = ("created_at", "updated_at")
