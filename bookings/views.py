from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from properties.models import Property, Room
from .forms import BookingAgreementForm, RentalRequestForm
from .models import Booking, ExtensionRequest, RentalRequest
from .reminders import rent_reminders_for


def tenant_required(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")
    if request.user.role != "TENANT":
        messages.error(request, "Tenant access is required.")
        return redirect("accounts:dashboard")
    return None


def owner_required(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.get_full_path()}")
    if request.user.role != "OWNER":
        messages.error(request, "Owner access is required.")
        return redirect("accounts:dashboard")
    return None


@login_required
def create_request(request, property_pk):
    blocked = tenant_required(request)
    if blocked:
        return blocked

    property_obj = get_object_or_404(
        Property.objects.prefetch_related("rooms"), pk=property_pk, available=True
    )

    if property_obj.owner_id == request.user.id:
        messages.error(request, "You cannot request your own property.")
        return redirect("properties:detail", pk=property_pk)

    active_request = RentalRequest.objects.filter(
        tenant=request.user,
        property=property_obj,
        status__in=[RentalRequest.Status.PENDING, RentalRequest.Status.APPROVED],
    ).first()
    if active_request:
        messages.info(request, "You already have an active request for this property.")
        return redirect("bookings:my_requests")

    if request.method == "POST":
        form = RentalRequestForm(request.POST, property_obj=property_obj)
        if form.is_valid():
            rental_request = form.save(commit=False)
            rental_request.tenant = request.user
            rental_request.property = property_obj
            rental_request.save()

            send_mail(
                subject=f"New rental request for {property_obj.title}",
                message=(
                    f"{request.user.get_full_name() or request.user.username} has requested "
                    f"your property '{property_obj.title}' from {rental_request.move_in_date} "
                    f"for {rental_request.duration_display()}. Please review it from your owner dashboard."
                ),
                from_email=None,
                recipient_list=[property_obj.owner.email],
                fail_silently=True,
            )
            messages.success(request, "Rental request submitted successfully.")
            return redirect("bookings:my_requests")
    else:
        form = RentalRequestForm(property_obj=property_obj)

    return render(request, "bookings/request_form.html", {"form": form, "property": property_obj})


@login_required
def my_requests(request):
    blocked = tenant_required(request)
    if blocked:
        return blocked
    requests = RentalRequest.objects.filter(tenant=request.user).select_related("property", "room")
    return render(request, "bookings/my_requests.html", {"requests": requests})


@login_required
def my_bookings(request):
    blocked = tenant_required(request)
    if blocked:
        return blocked
    bookings = Booking.objects.filter(tenant=request.user).select_related("property", "room", "rental_request")
    for booking in bookings:
        booking.has_pending_extension = booking.extension_requests.filter(status=ExtensionRequest.Status.PENDING).exists()
    return render(
        request,
        "bookings/my_bookings.html",
        {"bookings": bookings, "rent_reminders": rent_reminders_for(request.user)},
    )


@login_required
def owner_requests(request):
    blocked = owner_required(request)
    if blocked:
        return blocked
    requests = RentalRequest.objects.filter(property__owner=request.user).select_related("tenant", "property", "room")
    return render(request, "bookings/owner_requests.html", {"requests": requests})


@login_required
@transaction.atomic
def approve_request(request, pk):
    blocked = owner_required(request)
    if blocked:
        return blocked
    rental_request = get_object_or_404(
        RentalRequest.objects.select_for_update().select_related("tenant", "property", "room"),
        pk=pk,
        property__owner=request.user,
    )
    if request.method != "POST":
        return redirect("bookings:owner_requests")
    if rental_request.status != RentalRequest.Status.PENDING:
        messages.warning(request, "Only pending requests can be approved.")
        return redirect("bookings:owner_requests")
    if not rental_request.property.available:
        messages.error(request, "This property is currently unavailable.")
        return redirect("bookings:owner_requests")
    if rental_request.room and not rental_request.room.available:
        messages.error(request, "The selected room is no longer available.")
        return redirect("bookings:owner_requests")

    conflicting = Booking.objects.filter(
        property=rental_request.property,
        status=Booking.Status.CONFIRMED,
    )
    if rental_request.room:
        conflicting = conflicting.filter(room=rental_request.room)
    if conflicting.exists():
        messages.error(request, "This property or room already has a confirmed booking.")
        return redirect("bookings:owner_requests")

    rental_request.status = RentalRequest.Status.APPROVED
    rental_request.save(update_fields=["status", "updated_at"])

    booking = Booking.objects.create(
        rental_request=rental_request,
        tenant=rental_request.tenant,
        property=rental_request.property,
        room=rental_request.room,
        start_date=rental_request.move_in_date,
        duration_months=rental_request.duration_months,
    )

    if rental_request.room:
        rental_request.room.available = False
        rental_request.room.save(update_fields=["available"])
        if not rental_request.property.rooms.filter(available=True).exists():
            rental_request.property.available = False
            rental_request.property.save(update_fields=["available"])
    else:
        rental_request.property.available = False
        rental_request.property.save(update_fields=["available"])

    send_mail(
        subject=f"Rental request approved - {rental_request.property.title}",
        message=(
            f"Your rental request for '{rental_request.property.title}' has been approved. "
            f"Booking #{booking.pk} starts on {booking.start_date} for {booking.duration_display()} "
            f"(until {booking.end_date()})."
        ),
        from_email=None,
        recipient_list=[rental_request.tenant.email],
        fail_silently=True,
    )
    messages.success(request, f"Request #{rental_request.pk} approved and booking #{booking.pk} created.")
    return redirect("bookings:owner_requests")


@login_required
@transaction.atomic
def reject_request(request, pk):
    blocked = owner_required(request)
    if blocked:
        return blocked
    rental_request = get_object_or_404(RentalRequest, pk=pk, property__owner=request.user)
    if request.method != "POST":
        return redirect("bookings:owner_requests")
    if rental_request.status != RentalRequest.Status.PENDING:
        messages.warning(request, "Only pending requests can be rejected.")
        return redirect("bookings:owner_requests")

    rental_request.status = RentalRequest.Status.REJECTED
    rental_request.save(update_fields=["status", "updated_at"])
    send_mail(
        subject=f"Rental request rejected - {rental_request.property.title}",
        message=f"Your rental request for '{rental_request.property.title}' was rejected by the owner.",
        from_email=None,
        recipient_list=[rental_request.tenant.email],
        fail_silently=True,
    )
    messages.success(request, "Rental request rejected.")
    return redirect("bookings:owner_requests")


@login_required
def request_extension(request, booking_pk):
    blocked = tenant_required(request)
    if blocked:
        return blocked
    booking = get_object_or_404(Booking.objects.select_related("property", "room"), pk=booking_pk, tenant=request.user, status=Booking.Status.CONFIRMED)
    if booking.end_date() < timezone.localdate():
        messages.error(request, "This rental has already ended. Contact the property owner for assistance.")
        return redirect("bookings:my_bookings")
    if ExtensionRequest.objects.filter(booking=booking, status=ExtensionRequest.Status.PENDING).exists():
        messages.info(request, "You already have an extension request awaiting owner review.")
        return redirect("bookings:my_bookings")
    if request.method == "POST":
        try:
            months = int(request.POST.get("additional_months", "1"))
        except (TypeError, ValueError):
            months = 0
        note = request.POST.get("tenant_note", "").strip()
        if months < 1 or months > 24 or booking.duration_months + months > 60:
            messages.error(request, "Choose an extension between 1 and 24 months. The total rental duration cannot exceed 60 months.")
        else:
            extension = ExtensionRequest.objects.create(booking=booking, tenant=request.user, additional_months=months, tenant_note=note)
            from maintenance.models import Notification
            Notification.objects.create(recipient=booking.property.owner, title="Rental extension request", message=f"{request.user.username} requested an additional {months} month(s) for {booking.property.title}.", link=reverse("bookings:owner_extensions"))
            send_mail("Rental extension request", f"{request.user.username} requested an additional {months} month(s) for {booking.property.title}.", None, [booking.property.owner.email], fail_silently=True)
            messages.success(request, "Your extension request has been sent to the property owner.")
            return redirect("bookings:my_bookings")
    return render(request, "bookings/extension_request.html", {"booking": booking})


@login_required
def owner_extensions(request):
    blocked = owner_required(request)
    if blocked:
        return blocked
    extensions = ExtensionRequest.objects.filter(booking__property__owner=request.user).select_related("booking", "booking__property", "tenant")
    return render(request, "bookings/owner_extensions.html", {"extensions": extensions})


@login_required
@transaction.atomic
def review_extension(request, extension_pk, decision):
    blocked = owner_required(request)
    if blocked:
        return blocked
    extension = get_object_or_404(ExtensionRequest.objects.select_for_update().select_related("booking", "tenant", "booking__property"), pk=extension_pk, booking__property__owner=request.user)
    if request.method != "POST" or decision not in {"approve", "reject"}:
        return redirect("bookings:owner_extensions")
    if extension.status != ExtensionRequest.Status.PENDING:
        messages.info(request, "This extension request has already been reviewed.")
        return redirect("bookings:owner_extensions")
    extension.owner_note = request.POST.get("owner_note", "").strip()
    extension.reviewed_at = timezone.now()
    if decision == "approve":
        extension.status = ExtensionRequest.Status.APPROVED
        extension.booking.duration_months += extension.additional_months
        extension.booking.save(update_fields=["duration_months", "updated_at"])
        result = f"Your rental extension for {extension.booking.property.title} was approved. New end date: {extension.booking.end_date():%d %b %Y}."
    else:
        extension.status = ExtensionRequest.Status.REJECTED
        result = f"Your rental extension request for {extension.booking.property.title} was not approved. Please contact the owner for details."
    extension.save(update_fields=["status", "owner_note", "reviewed_at"])
    from maintenance.models import Notification
    Notification.objects.create(recipient=extension.tenant, title="Rental extension update", message=result, link=reverse("bookings:my_bookings"))
    send_mail("Rental extension update", result, None, [extension.tenant.email], fail_silently=True)
    messages.success(request, "Extension request reviewed.")
    return redirect("bookings:owner_extensions")


@login_required
def owner_rentals(request):
    blocked = owner_required(request)
    if blocked:
        return blocked
    rentals = Booking.objects.filter(property__owner=request.user).select_related("tenant", "property", "room")
    return render(request, "bookings/owner_rentals.html", {"rentals": rentals})


@login_required
def manage_agreement(request, booking_pk):
    blocked = owner_required(request)
    if blocked:
        return blocked
    booking = get_object_or_404(Booking.objects.select_related("tenant", "property", "room"), pk=booking_pk, property__owner=request.user)
    form = BookingAgreementForm(request.POST or None, request.FILES or None, instance=booking)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Rental agreement and handover details were updated.")
        return redirect("bookings:owner_rentals")
    return render(request, "bookings/manage_agreement.html", {"form": form, "booking": booking})
