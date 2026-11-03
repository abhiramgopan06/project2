"""Helpers for rental duration calculations.

Kept free of Django imports so they are trivial to unit-test.
"""
import calendar
from datetime import timedelta

MIN_RENTAL_MONTHS = 1
MAX_RENTAL_MONTHS = 60

                                                                  
REMINDER_DAYS_BEFORE = 5


def add_months(start, months):
    """Return ``start`` moved forward by ``months`` calendar months.

    If the target month is shorter than the start day (e.g. 31 Jan + 1 month),
    the result is clamped to the last day of the target month.
    """
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return start.replace(year=year, month=month, day=day)


def lease_end_date(start, months):
    """Last day of the stay, inclusive.

    A 12-month rental starting 1 Jan 2027 ends on 31 Dec 2027.
    """
    if start is None or not months:
        return None
    return add_months(start, months) - timedelta(days=1)


def format_duration(months):
    """Human-friendly duration: 1 month, 6 months, 1 year, 1 year 6 months."""
    if not months:
        return ""
    years, rem = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if rem:
        parts.append(f"{rem} month{'s' if rem != 1 else ''}")
    return " ".join(parts)


def next_rent_due_date(start, months, today):
    """The next day rent is due, or None if every rent date has already passed.

    Rent is due on the same day of each month as the move-in date, once for
    every month of the stay. A stay starting 10 Jan for 3 months has rent due
    on 10 Jan, 10 Feb and 10 Mar.
    """
    if start is None or not months:
        return None
    for month_number in range(months):
        due = add_months(start, month_number)
        if due >= today:
            return due
    return None
