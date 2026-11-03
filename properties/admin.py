from django.contrib import admin

from .models import Amenity, Property, PropertyExpense, PropertyImage, PropertyVerificationDocument, Room, SavedProperty


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 0


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "property_type", "location", "rent", "available", "verification_status", "created_at")
    list_filter = ("property_type", "available", "verification_status", "amenities")
    search_fields = ("title", "location", "address", "owner__username", "owner__email")
    filter_horizontal = ("amenities",)
    inlines = [PropertyImageInline, RoomInline]
    readonly_fields = ("owner", "title", "description", "property_type", "location", "address", "latitude", "longitude", "number_of_rooms", "rent", "available", "amenities", "created_at", "updated_at")
    fieldsets = (("Listing", {"fields": ("owner", "title", "description", "property_type", "location", "address", "latitude", "longitude", "number_of_rooms", "rent", "available", "amenities", "created_at", "updated_at")}), ("Verification review", {"fields": ("verification_status", "verification_note")}))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ("property", "is_primary", "uploaded_at")
    list_filter = ("is_primary",)
    search_fields = ("property__title", "property__owner__username")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("property", "room_number", "room_type", "rent", "available")
    list_filter = ("room_type", "available")
    search_fields = ("property__title", "room_number")


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(PropertyVerificationDocument)
class PropertyVerificationDocumentAdmin(admin.ModelAdmin):
    list_display = ("property", "description", "uploaded_at")
    search_fields = ("property__title", "property__owner__username", "description")
    readonly_fields = ("property", "document", "description", "uploaded_at")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff


@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ("user", "property", "created_at")
    search_fields = ("user__username", "property__title")
    readonly_fields = ("user", "property", "created_at")
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PropertyExpense)
class PropertyExpenseAdmin(admin.ModelAdmin):
    list_display = ("property", "category", "amount", "expense_date", "created_at")
    list_filter = ("category", "expense_date")
    search_fields = ("property__title", "property__owner__username", "description")
