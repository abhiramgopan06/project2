from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from properties.models import Property


class PropertyReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        REVIEWING = "REVIEWING", "Under Review"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    class Reason(models.TextChoices):
        INACCURATE = "INACCURATE", "Inaccurate Information"
        SCAM = "SCAM", "Suspected Scam"
        DUPLICATE = "DUPLICATE", "Duplicate Listing"
        UNAVAILABLE = "UNAVAILABLE", "Property Unavailable"
        INAPPROPRIATE = "INAPPROPRIATE", "Inappropriate Content"
        OTHER = "OTHER", "Other"

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="property_reports")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField(validators=[MinLengthValidator(10)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.pk} - {self.property.title}"
