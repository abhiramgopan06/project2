from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking

from .forms import MockPaymentForm
from .models import Payment


def tenant_only(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.role != "TENANT":
        messages.error(request, "Only tenants can make payments.")
        return redirect("accounts:dashboard")
    return None


@login_required
def payment_history(request):
    blocked = tenant_only(request)
    if blocked:
        return blocked
    payments = Payment.objects.filter(tenant=request.user).select_related("booking", "booking__property", "booking__room")
    totals = payments.aggregate(
        total_paid=Sum("amount", filter=Q(status=Payment.Status.SUCCESS)),
        total_failed=Count("pk", filter=Q(status=Payment.Status.FAILED)),
        total_pending=Count("pk", filter=Q(status=Payment.Status.PENDING)),
    )
    return render(request, "payments/payment_history.html", {"payments": payments, "totals": totals, "invoice_count": payments.count()})


@login_required
@transaction.atomic
def make_payment(request, booking_pk):
    blocked = tenant_only(request)
    if blocked:
        return blocked

    booking = get_object_or_404(
        Booking.objects.select_related("property", "room"),
        pk=booking_pk,
        tenant=request.user,
        status=Booking.Status.CONFIRMED,
    )

    successful = Payment.objects.filter(booking=booking, status=Payment.Status.SUCCESS).first()
    if successful:
        messages.info(request, "This booking has already been paid successfully.")
        return redirect("payments:history")

    amount = booking.room.rent if booking.room else booking.property.rent

    if request.method == "POST":
        form = MockPaymentForm(request.POST)
        if form.is_valid():
            result = form.cleaned_data["simulate_result"]
            payment = Payment.objects.create(
                booking=booking,
                tenant=request.user,
                amount=amount,
                payment_method=form.cleaned_data["payment_method"],
                card_last4=form.cleaned_data.get("card_last4", ""),
                status=Payment.Status.SUCCESS if result == "SUCCESS" else Payment.Status.FAILED,
                failure_reason="Mock payment was intentionally marked as failed." if result == "FAILED" else "",
            )

            if payment.status == Payment.Status.SUCCESS:
                send_mail(
                    subject=f"Payment successful - Booking #{booking.pk}",
                    message=(
                        f"Your mock payment of ₹{payment.amount} for '{booking.property.title}' was successful.\n"
                        f"Transaction ID: {payment.transaction_id}"
                    ),
                    from_email=None,
                    recipient_list=[request.user.email],
                    fail_silently=True,
                )
                send_mail(
                    subject=f"Tenant payment received - Booking #{booking.pk}",
                    message=(
                        f"{request.user.get_full_name() or request.user.username} completed a mock payment "
                        f"of ₹{payment.amount} for '{booking.property.title}'.\n"
                        f"Transaction ID: {payment.transaction_id}"
                    ),
                    from_email=None,
                    recipient_list=[booking.property.owner.email],
                    fail_silently=True,
                )
                messages.success(request, "Payment successful. Your transaction has been recorded.")
            else:
                messages.error(request, "Mock payment failed. You can try again.")

            return redirect("payments:result", payment_pk=payment.pk)
    else:
        form = MockPaymentForm()

    return render(request, "payments/payment_form.html", {"form": form, "booking": booking, "amount": amount})


@login_required
def payment_result(request, payment_pk):
    blocked = tenant_only(request)
    if blocked:
        return blocked
    payment = get_object_or_404(
        Payment.objects.select_related("booking", "booking__property", "booking__room"),
        pk=payment_pk,
        tenant=request.user,
    )
    return render(request, "payments/payment_result.html", {"payment": payment})


@login_required
def owner_payment_history(request):
    if request.user.role != "OWNER":
        messages.error(request, "Only property owners can view owner payment records.")
        return redirect("accounts:dashboard")
    payments = Payment.objects.filter(booking__property__owner=request.user).select_related("tenant", "booking", "booking__property", "booking__room")
    totals = payments.aggregate(
        total_received=Sum("amount", filter=Q(status=Payment.Status.SUCCESS)),
        pending_count=Count("pk", filter=Q(status=Payment.Status.PENDING)),
        failed_count=Count("pk", filter=Q(status=Payment.Status.FAILED)),
    )
    return render(request, "payments/owner_history.html", {"payments": payments, "totals": totals})
