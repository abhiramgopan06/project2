from django.contrib import admin

from .models import MaintenanceTicket, Technician, TechnicianPreparationItem


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "email", "specialization", "available")
    list_filter = ("available", "specialization")
    search_fields = ("name", "email", "phone", "owner__username")


@admin.register(MaintenanceTicket)
class MaintenanceTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "tenant", "property", "priority", "status", "technician", "created_at")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("title", "description", "tenant__username", "property__title", "technician__name")
    readonly_fields = ("created_at", "updated_at", "resolved_at", "closed_at")


@admin.register(TechnicianPreparationItem)
class TechnicianPreparationItemAdmin(admin.ModelAdmin):
    list_display = ("ticket", "title", "is_completed", "completed_at")
    list_filter = ("is_completed",)
    search_fields = ("ticket__title", "title")
