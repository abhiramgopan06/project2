from datetime import timedelta

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking, BookingReminder
from maintenance.models import Notification


class Command(BaseCommand):
    help = "Send each tenant one reminder five days before their rental ends."

    def handle(self, *args, **options):
        today = timezone.localdate()
        sent = 0
        bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).select_related("tenant", "property")
        for booking in bookings:
            if booking.end_date() != today + timedelta(days=5):
                continue
            try:
                with transaction.atomic():
                    BookingReminder.objects.create(booking=booking, reminder_type="EXPIRY_5_DAYS", reminder_date=today)
            except IntegrityError:
                continue
            message = (
                f"Your rental at {booking.property.title} is due to end on {booking.end_date():%d %B %Y}. "
                "If you would like to stay longer, submit an extension request from My Bookings. "
                "The property owner must approve the request before the rental period changes."
            )
            Notification.objects.create(
                recipient=booking.tenant,
                title="Your rental ends in 5 days",
                message=message,
                link=reverse("bookings:my_bookings"),
            )
            if booking.tenant.email:
                send_mail("Rental expiry reminder - 5 days remaining", message, None, [booking.tenant.email], fail_silently=True)
            sent += 1
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} rental expiry reminder(s)."))
