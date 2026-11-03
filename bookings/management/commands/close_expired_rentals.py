from django.core.management.base import BaseCommand
from django.utils import timezone
from django.urls import reverse

from maintenance.models import Notification

from bookings.models import Booking


class Command(BaseCommand):
    help = "Close rentals whose agreed end date has passed and release their room or property."

    def handle(self, *args, **options):
        today = timezone.localdate()
        closed = 0
        bookings = Booking.objects.filter(status=Booking.Status.CONFIRMED).select_related("property", "room")
        for booking in bookings:
            if booking.end_date() >= today:
                continue
            booking.status = Booking.Status.COMPLETED
            booking.save(update_fields=["status", "updated_at"])
            message = f"Your rental at {booking.property.title} has reached its agreed end date. Contact the property owner if you need help with handover."
            Notification.objects.create(recipient=booking.tenant, title="Rental period completed", message=message, link=reverse("bookings:my_bookings"))
            Notification.objects.create(recipient=booking.property.owner, title="Rental period completed", message=f"The rental for {booking.property.title} by {booking.tenant.username} has ended.", link=reverse("bookings:owner_rentals"))
            if booking.room_id:
                booking.room.available = True
                booking.room.save(update_fields=["available"])
                if booking.property.rooms.filter(available=False).exists() is False:
                    booking.property.available = True
                    booking.property.save(update_fields=["available"])
            else:
                booking.property.available = True
                booking.property.save(update_fields=["available"])
            closed += 1
        self.stdout.write(self.style.SUCCESS(f"Closed {closed} expired rental(s)."))
