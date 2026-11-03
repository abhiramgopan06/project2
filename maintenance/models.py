from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from bookings.models import Booking
from properties.models import Property, Room


class Technician(models.Model):
    """A repair person that a property owner can assign to tickets.

    Each technician also gets their own login account (the `user` field)
    so they can log in and see their own list of assigned tickets.
    """


    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="technicians",
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="technician_profile",
    )
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    experience = models.PositiveSmallIntegerField(default=0, help_text="Years of relevant work experience")
    description = models.TextField(blank=True, help_text="Describe the technician’s skills and services")
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MaintenanceTicket(models.Model):
    """A repair/issue reported by a tenant for a property they are renting.

    Life cycle: OPEN -> ASSIGNED -> IN_PROGRESS -> RESOLVED -> CLOSED
    """

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        EMERGENCY = "EMERGENCY", "Emergency"

    class Status(models.TextChoices):
        OPEN = "OPEN", "New request"
        ASSIGNED = "ASSIGNED", "Assigned"
        ACCEPTED = "ACCEPTED", "Accepted"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        RESOLVED = "RESOLVED", "Completed"
        CLOSED = "CLOSED", "Closed"
        REJECTED = "REJECTED", "Declined"

    tenant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_tickets")
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name="maintenance_tickets")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_tickets")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="maintenance_tickets")
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    title = models.CharField(max_length=200)
    description = models.TextField()
    tenant_photo = models.ImageField(upload_to="maintenance/reported/%Y/%m/", blank=True, null=True)
    resolution_photo = models.ImageField(upload_to="maintenance/resolved/%Y/%m/", blank=True, null=True)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN, db_index=True)
    owner_note = models.TextField(blank=True)
    technician_note = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    materials_used = models.TextField(blank=True)
    work_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    work_minutes = models.PositiveIntegerField(default=0)
    requires_revisit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Maintenance Work Order"
        verbose_name_plural = "Maintenance Work Orders"

    def clean(self):
        if self.tenant_id and self.tenant.role != "TENANT":
            raise ValidationError("Only tenants can create maintenance requests.")
        if self.booking_id:
            if self.booking.tenant_id != self.tenant_id:
                raise ValidationError("The booking does not belong to this tenant.")
            if self.booking.property_id != self.property_id:
                raise ValidationError("The booking does not belong to this property.")
            if self.booking.status != Booking.Status.CONFIRMED:
                raise ValidationError("Maintenance requests require a confirmed booking.")
        if self.room_id and self.room.property_id != self.property_id:
            raise ValidationError("The selected room does not belong to this property.")
        if self.technician_id and self.technician.owner_id != self.property.owner_id:
            raise ValidationError("The technician must belong to the property owner.")
        if self.technician_id and not self.technician.available:
            raise ValidationError("The selected technician is currently unavailable.")

    def preparation_total(self):
        return self.preparation_items.count()

    def preparation_done(self):
        return self.preparation_items.filter(is_completed=True).count()

    def mark_resolved(self):
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save(update_fields=["status", "resolved_at", "updated_at"])

    def mark_closed(self):
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])

    def __str__(self):
        return f"Work order #{self.pk} - {self.title}"


class MaintenanceMessage(models.Model):
    """Simple conversation between the tenant and assigned technician."""
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_messages")
    message = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message #{self.pk} on work order #{self.ticket_id}"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="maintenance_notifications")
    title = models.CharField(max_length=150)
    message = models.TextField(max_length=500)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"


class TechnicianReport(models.Model):
    """A concern raised by a technician for administrator review."""
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name="reports")
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.SET_NULL, null=True, blank=True, related_name="technician_reports")
    subject = models.CharField(max_length=180)
    description = models.TextField(max_length=2000)
    status = models.CharField(max_length=20, choices=[("OPEN", "Open"), ("REVIEWING", "Reviewing"), ("RESOLVED", "Resolved")], default="OPEN")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Technician report #{self.pk}: {self.subject}"


class TechnicianPreparationItem(models.Model):
    ticket = models.ForeignKey(MaintenanceTicket, on_delete=models.CASCADE, related_name="preparation_items")
    title = models.CharField(max_length=180)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.title} - Work #{self.ticket_id}"
