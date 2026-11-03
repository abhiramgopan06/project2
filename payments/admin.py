from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "booking", "amount", "payment_method", "status", "transaction_id", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    search_fields = ("tenant__username", "tenant__email", "booking__property__title", "transaction_id")
    readonly_fields = ("transaction_id", "created_at", "updated_at")
    list_select_related = ("tenant", "booking", "booking__property")
