"""Emails tenants whose rent is due in exactly 5 days.

Run it once a day:   python manage.py send_rent_reminders
(use Task Scheduler on Windows or cron on Linux/Mac to run it every morning).
While EMAIL_BACKEND is the console backend, the emails print in the terminal.
"""
from datetime import timedelta

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookings.models import Booking
from bookings.utils import REMINDER_DAYS_BEFORE


class Command(BaseCommand):
    help = "Send an email to tenants whose rent is due in 5 days."

    def handle(self, *args, **options):
        today = timezone.localdate()
        reminder_date = today + timedelta(days=REMINDER_DAYS_BEFORE)

        bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).select_related(
            "tenant", "property", "room"
        )

        sent = 0
        for booking in bookings:
            if booking.next_rent_due(today) != reminder_date:
                continue
            if not booking.tenant.email:
                continue

            send_mail(
                subject=f"Rent reminder - {booking.property.title}",
                message=(
                    f"Hello {booking.tenant.first_name or booking.tenant.username}, "
                    f"your rent of ₹{booking.monthly_rent()} for '{booking.property.title}' "
                    f"is due on {reminder_date} ({REMINDER_DAYS_BEFORE} days from now)."
                ),
                from_email=None,
                recipient_list=[booking.tenant.email],
                fail_silently=True,
            )
            sent += 1

        self.stdout.write(f"Sent {sent} rent reminder(s).")
