from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from properties.models import Property, Room
from .utils import MAX_RENTAL_MONTHS, MIN_RENTAL_MONTHS, format_duration, lease_end_date, next_rent_due_date


class RentalRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="rental_requests")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="rental_requests")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="rental_requests")
    move_in_date = models.DateField()
    duration_months = models.PositiveSmallIntegerField(
        "Rental duration (months)",
        default=MIN_RENTAL_MONTHS,
        validators=[MinValueValidator(MIN_RENTAL_MONTHS), MaxValueValidator(MAX_RENTAL_MONTHS)],
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    owner_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.tenant_id and self.tenant.role != "TENANT":
            raise ValidationError("Only tenant accounts can request a property for rent.")
        if self.tenant_id and self.property_id and self.property.owner_id == self.tenant_id:
            raise ValidationError("A property owner cannot request their own property.")
        if self.room_id and self.room.property_id != self.property_id:
            raise ValidationError("The selected room does not belong to this property.")
        if self.move_in_date and self.move_in_date < timezone.localdate():
            raise ValidationError("Move-in date cannot be in the past.")

                                                                           
                                                                            
                                                                                  
    def end_date(self):
        return lease_end_date(self.move_in_date, self.duration_months)

    def duration_display(self):
        return format_duration(self.duration_months)

    def __str__(self):
        return f"Request #{self.pk} - {self.tenant.username} - {self.property.title}"


class Booking(models.Model):
    class DepositStatus(models.TextChoices):
        NOT_COLLECTED = "NOT_COLLECTED", "Not collected"
        HELD = "HELD", "Held by owner"
        PARTIALLY_RETURNED = "PARTIALLY_RETURNED", "Partially returned"
        RETURNED = "RETURNED", "Returned"
        DEDUCTED = "DEDUCTED", "Deducted after inspection"

    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        CANCELLED = "CANCELLED", "Cancelled"
        COMPLETED = "COMPLETED", "Completed"

    rental_request = models.OneToOneField(RentalRequest, on_delete=models.PROTECT, related_name="booking")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, null=True, blank=True, related_name="bookings")
    start_date = models.DateField()
    duration_months = models.PositiveSmallIntegerField(
        "Rental duration (months)",
        default=MIN_RENTAL_MONTHS,
        validators=[MinValueValidator(MIN_RENTAL_MONTHS), MaxValueValidator(MAX_RENTAL_MONTHS)],
    )
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.CONFIRMED, db_index=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    deposit_status = models.CharField(max_length=20, choices=DepositStatus.choices, default=DepositStatus.NOT_COLLECTED)
    agreement_file = models.FileField(upload_to="rental_agreements/%Y/%m/", blank=True, null=True)
    agreement_notes = models.TextField(blank=True)
    move_in_notes = models.TextField(blank=True)
    move_out_notes = models.TextField(blank=True)
    move_in_confirmed = models.BooleanField(default=False)
    move_out_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        if self.tenant_id and self.tenant.role != "TENANT":
            raise ValidationError("Only tenant accounts can have rental bookings.")
        if self.property_id and self.property.owner.role != "OWNER":
            raise ValidationError("A rental property must belong to a property owner.")
        if self.room_id and self.room.property_id != self.property_id:
            raise ValidationError("The selected room does not belong to this property.")

                                                                          
    def end_date(self):
        return lease_end_date(self.start_date, self.duration_months)

    def duration_display(self):
        return format_duration(self.duration_months)

    def next_rent_due(self, today=None):
        """Next date rent is due for this booking (None once the stay is over)."""
        return next_rent_due_date(self.start_date, self.duration_months, today or timezone.localdate())

    def monthly_rent(self):
        return self.room.rent if self.room else self.property.rent

    def __str__(self):
        return f"Booking #{self.pk} - {self.property.title}"


class ExtensionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting owner review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Not approved"
        CANCELLED = "CANCELLED", "Cancelled"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="extension_requests")
    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="extension_requests")
    additional_months = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(60)])
    tenant_note = models.TextField(blank=True)
    owner_note = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["booking"], condition=models.Q(status="PENDING"), name="one_pending_extension_per_booking")]

    def clean(self):
        if self.booking_id and self.tenant_id and self.booking.tenant_id != self.tenant_id:
            raise ValidationError("This rental does not belong to the selected tenant.")

    def __str__(self):
        return f"Extension for booking #{self.booking_id} ({self.get_status_display()})"


class BookingReminder(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="sent_reminders")
    reminder_type = models.CharField(max_length=30, default="EXPIRY_5_DAYS")
    reminder_date = models.DateField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["booking", "reminder_type", "reminder_date"], name="unique_booking_reminder_type_date")]

    def __str__(self):
        return f"{self.reminder_type} for booking #{self.booking_id}"
