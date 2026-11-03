"""Helpers for rent-due and rental-expiry reminders."""
from datetime import timedelta

from django.utils import timezone

from .models import Booking
from .utils import REMINDER_DAYS_BEFORE


def rent_reminders_for(tenant):
    today = timezone.localdate()
    bookings = Booking.objects.filter(tenant=tenant, status=Booking.Status.CONFIRMED).select_related("property", "room")
    reminders = []
    for booking in bookings:
        due_date = booking.next_rent_due(today)
        if due_date is None:
            continue
        days_left = (due_date - today).days
        if days_left <= REMINDER_DAYS_BEFORE:
            reminders.append({"booking": booking, "due_date": due_date, "days_left": days_left, "amount": booking.monthly_rent()})
    return reminders


def expiry_reminders_for(tenant):
    today = timezone.localdate()
    latest = today + timedelta(days=5)
    bookings = Booking.objects.filter(tenant=tenant, status=Booking.Status.CONFIRMED).select_related("property", "room")
    reminders = []
    for booking in bookings:
        end_date = booking.end_date()
        if end_date and today <= end_date <= latest:
            reminders.append({"booking": booking, "end_date": end_date, "days_left": (end_date - today).days})
    return reminders
