from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Amenities"

    def __str__(self):
        return self.name


class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "APARTMENT", "Apartment"
        HOUSE = "HOUSE", "House"
        VILLA = "VILLA", "Villa"
        STUDIO = "STUDIO", "Studio"
        PG = "PG", "PG / Shared Accommodation"
        OFFICE = "OFFICE", "Office"
        OTHER = "OTHER", "Other"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="properties",
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    location = models.CharField(max_length=150, db_index=True)
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    number_of_rooms = models.PositiveIntegerField(default=1)
    rent = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    available = models.BooleanField(default=True, db_index=True)
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Needs changes"

    verification_status = models.CharField(max_length=12, choices=VerificationStatus.choices, default=VerificationStatus.PENDING, db_index=True)
    verification_note = models.CharField(max_length=300, blank=True)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.owner_id and self.owner.role != "OWNER":
            from django.core.exceptions import ValidationError
            raise ValidationError("Only property owner accounts can list properties for rent.")

    def __str__(self):
        return self.title

    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

    @property
    def has_map_location(self):
        return self.latitude is not None and self.longitude is not None

    @property
    def map_embed_url(self):
        if not self.has_map_location:
            return ""
        delta = Decimal("0.006")
        latitude = Decimal(str(self.latitude))
        longitude = Decimal(str(self.longitude))
        bbox = (
            f"{longitude - delta},{latitude - delta},"
            f"{longitude + delta},{latitude + delta}"
        )
        return f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}&marker={latitude},{longitude}&layer=mapnik"


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/%Y/%m/")
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "-uploaded_at"]

    def save(self, *args, **kwargs):
        if self.is_primary:
            PropertyImage.objects.filter(property=self.property, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        elif not PropertyImage.objects.filter(property=self.property).exclude(pk=self.pk).exists():
            self.is_primary = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Image for {self.property.title}"


class Room(models.Model):
    class RoomType(models.TextChoices):
        SINGLE = "SINGLE", "Single"
        DOUBLE = "DOUBLE", "Double"
        SHARED = "SHARED", "Shared"
        MASTER = "MASTER", "Master"
        OTHER = "OTHER", "Other"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=50)
    room_type = models.CharField(max_length=20, choices=RoomType.choices, default=RoomType.SINGLE)
    rent = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    available = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["room_number"]
        constraints = [
            models.UniqueConstraint(fields=["property", "room_number"], name="unique_room_number_per_property")
        ]

    def __str__(self):
        return f"{self.property.title} - Room {self.room_number}"


class SavedProperty(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_properties")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "property"], name="unique_saved_property_per_user")]

    def __str__(self):
        return f"{self.user} saved {self.property}"


class PropertyVerificationDocument(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="verification_documents")
    document = models.FileField(upload_to="verification_documents/%Y/%m/")
    description = models.CharField(max_length=180, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"Verification document for {self.property.title}"


class PropertyExpense(models.Model):
    class Category(models.TextChoices):
        MAINTENANCE = "MAINTENANCE", "Maintenance"
        UTILITIES = "UTILITIES", "Utilities"
        TAX = "TAX", "Property tax"
        INSURANCE = "INSURANCE", "Insurance"
        CLEANING = "CLEANING", "Cleaning"
        OTHER = "OTHER", "Other"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="expenses")
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.OTHER)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    expense_date = models.DateField(default=timezone.localdate)
    description = models.CharField(max_length=250)
    receipt = models.FileField(upload_to="property_expenses/%Y/%m/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-expense_date", "-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.property.title} - ₹{self.amount}"
