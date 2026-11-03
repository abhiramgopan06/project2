from django.contrib import admin
from .models import Booking, BookingReminder, ExtensionRequest, RentalRequest


@admin.register(RentalRequest)
class RentalRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "property", "room", "move_in_date", "duration_months", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tenant__username", "tenant__email", "property__title")
    list_select_related = ("tenant", "property", "room")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "property", "room", "start_date", "duration_months", "end_date", "status", "deposit_amount", "deposit_status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("tenant__username", "tenant__email", "property__title")
    list_select_related = ("tenant", "property", "room")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ExtensionRequest)
class ExtensionRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "booking", "tenant", "additional_months", "status", "created_at", "reviewed_at")
    list_filter = ("status", "created_at")
    search_fields = ("tenant__username", "booking__property__title")
    readonly_fields = ("created_at", "reviewed_at")


@admin.register(BookingReminder)
class BookingReminderAdmin(admin.ModelAdmin):
    list_display = ("booking", "reminder_type", "reminder_date", "sent_at")
    list_filter = ("reminder_type", "reminder_date")
    readonly_fields = ("booking", "reminder_type", "reminder_date", "sent_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
