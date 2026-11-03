from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, ExtensionRequest, RentalRequest
from maintenance.models import MaintenanceTicket, Technician, TechnicianReport
from payments.models import Payment
from properties.models import Property, PropertyExpense
from .forms import PropertyReportForm
from .models import PropertyReport


def home(request):
    available = Property.objects.filter(available=True)
    featured = available.select_related("owner").prefetch_related("images", "amenities", "rooms")[:6]
    return render(request, "home.html", {
        "featured_properties": featured,
        "available_count": available.count(),
        "verified_count": available.filter(verification_status=Property.VerificationStatus.VERIFIED).count(),
    })


@login_required
def about(request):
                                                                      
                                                        
    if request.user.role != User.Role.TENANT:
        messages.info(request, "The About Us page is available to tenants only.")
        return redirect("accounts:dashboard")
    return render(request, "core/about.html")


def _admin_only(request):
    return request.user.is_authenticated and (request.user.is_superuser or request.user.role == User.Role.ADMIN)


def _has_active_rental(user, property_obj):
    """Return True only when the user is currently renting this property."""
    if not user.is_authenticated or user.role != User.Role.TENANT:
        return False

    today = timezone.localdate()
    bookings = Booking.objects.filter(
        tenant=user,
        property=property_obj,
        status=Booking.Status.CONFIRMED,
        start_date__lte=today,
    )
    return any(booking.end_date() and booking.end_date() >= today for booking in bookings)


@login_required
def report_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

                                                                      
                                                                         
                                                                             
    if not _has_active_rental(request.user, property_obj):
        messages.warning(
            request,
            "You cannot report this property because you do not have an active rental booking for it. "
            "Only the tenant currently renting the property can submit a report."
        )
        return redirect("properties:detail", pk=pk)

    existing = PropertyReport.objects.filter(
        property=property_obj,
        reporter=request.user,
        status__in=[PropertyReport.Status.OPEN, PropertyReport.Status.REVIEWING],
    ).exists()
    if existing:
        messages.info(request, "You already have an active report for this property.")
        return redirect("properties:detail", pk=pk)

    if request.method == "POST":
        form = PropertyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.property = property_obj
            report.reporter = request.user
            report.save()
            if property_obj.owner.email:
                send_mail(
                    f"Property report received - {property_obj.title}",
                    f"A user reported your property '{property_obj.title}'. Reason: {report.get_reason_display()}. Please review the listing.",
                    None, [property_obj.owner.email], fail_silently=True,
                )
            messages.success(request, "Your report has been submitted to the platform team.")
            return redirect("properties:detail", pk=pk)
    else:
        form = PropertyReportForm()
    return render(request, "core/report_property.html", {"form": form, "property": property_obj})


@login_required
def my_reports(request):
    reports = PropertyReport.objects.filter(reporter=request.user).select_related("property")
    return render(request, "core/my_reports.html", {"reports": reports})


@login_required
def admin_dashboard(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    context = {
        "total_users": User.objects.count(),
        "owners": User.objects.filter(role=User.Role.OWNER).count(),
        "tenants": User.objects.filter(role=User.Role.TENANT).count(),
        "technicians": User.objects.filter(role=User.Role.TECHNICIAN).count(),
        "properties": Property.objects.count(),
        "available_properties": Property.objects.filter(available=True).count(),
        "pending_requests": RentalRequest.objects.filter(status=RentalRequest.Status.PENDING).count(),
        "confirmed_bookings": Booking.objects.filter(status=Booking.Status.CONFIRMED).count(),
        "completed_bookings": Booking.objects.filter(status=Booking.Status.COMPLETED).count(),
        "pending_extensions": ExtensionRequest.objects.filter(status=ExtensionRequest.Status.PENDING).count(),
        "pending_verification": Property.objects.filter(verification_status=Property.VerificationStatus.PENDING).count(),
        "property_expenses": PropertyExpense.objects.aggregate(total=Sum("amount"))["total"] or 0,
        "successful_payments": Payment.objects.filter(status=Payment.Status.SUCCESS).count(),
        "payment_total": Payment.objects.filter(status=Payment.Status.SUCCESS).aggregate(total=Sum('amount'))['total'] or 0,
        "open_tickets": MaintenanceTicket.objects.filter(status__in=[MaintenanceTicket.Status.OPEN, MaintenanceTicket.Status.ASSIGNED, MaintenanceTicket.Status.IN_PROGRESS]).count(),
        "open_reports": PropertyReport.objects.filter(status__in=[PropertyReport.Status.OPEN, PropertyReport.Status.REVIEWING]).count(),
        "recent_reports": PropertyReport.objects.select_related("property", "reporter")[:8],
        "recent_bookings": Booking.objects.select_related("tenant", "property")[:8],
        "stats": [("Users", User.objects.count()), ("Owners", User.objects.filter(role=User.Role.OWNER).count()), ("Tenants", User.objects.filter(role=User.Role.TENANT).count()), ("Properties", Property.objects.count()), ("Available", Property.objects.filter(available=True).count()), ("Pending Requests", RentalRequest.objects.filter(status=RentalRequest.Status.PENDING).count()), ("Confirmed Rentals", Booking.objects.filter(status=Booking.Status.CONFIRMED).count()), ("Completed Rentals", Booking.objects.filter(status=Booking.Status.COMPLETED).count()), ("Pending Extensions", ExtensionRequest.objects.filter(status=ExtensionRequest.Status.PENDING).count()), ("Properties Awaiting Verification", Property.objects.filter(verification_status=Property.VerificationStatus.PENDING).count()), ("Recorded Property Expenses", PropertyExpense.objects.aggregate(total=Sum("amount"))["total"] or 0), ("Open Maintenance Work", MaintenanceTicket.objects.filter(status__in=[MaintenanceTicket.Status.OPEN, MaintenanceTicket.Status.ASSIGNED, MaintenanceTicket.Status.IN_PROGRESS]).count())],
    }
    return render(request, "core/admin_dashboard.html", context)


@login_required
def admin_reports(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    reports = PropertyReport.objects.select_related("property", "reporter")
    status = request.GET.get("status", "").strip()
    if status in dict(PropertyReport.Status.choices):
        reports = reports.filter(status=status)
    return render(request, "core/admin_reports.html", {"reports": reports, "statuses": PropertyReport.Status.choices, "selected_status": status})


@login_required
def admin_report_update(request, pk):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    report = get_object_or_404(PropertyReport.objects.select_related("property", "reporter"), pk=pk)
    if request.method == "POST":
        status = request.POST.get("status")
        note = request.POST.get("admin_note", "").strip()
        if status not in dict(PropertyReport.Status.choices):
            messages.error(request, "Invalid report status.")
        else:
            report.status = status
            report.admin_note = note
            report.save(update_fields=["status", "admin_note", "updated_at"])
            if report.reporter.email:
                send_mail(
                    f"Property report update - {report.property.title}",
                    f"Your report #{report.pk} is now {report.get_status_display()}.\n\nAdmin note: {note or 'No additional note.'}",
                    None, [report.reporter.email], fail_silently=True,
                )
            messages.success(request, "Report updated and the reporter was notified.")
            return redirect("core:admin_reports")
    return render(request, "core/admin_report_update.html", {"report": report, "statuses": PropertyReport.Status.choices})


                                                                             
                                                                   
                                                                         
                                                                        
                                                           
                                                                             


@login_required
def admin_users(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    users = User.objects.all().order_by("username")
    role = request.GET.get("role", "").strip()
    if role in dict(User.Role.choices):
        users = users.filter(role=role)
    return render(request, "core/admin_users.html", {
        "users": users,
        "roles": User.Role.choices,
        "selected_role": role,
    })


@login_required
def admin_user_detail(request, pk):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    tenant = get_object_or_404(User, pk=pk)

                                                                    
                                                                  
                                                      
    context = {"tenant": tenant}
    if tenant.role == User.Role.TENANT:
        context["rental_requests"] = RentalRequest.objects.filter(tenant=tenant).select_related("property", "room")
        context["bookings"] = Booking.objects.filter(tenant=tenant).select_related("property", "room")
        context["payments"] = Payment.objects.filter(tenant=tenant).select_related("booking__property")
        context["tickets"] = MaintenanceTicket.objects.filter(tenant=tenant).select_related("property")
    elif tenant.role == User.Role.OWNER:
        context["owned_properties"] = Property.objects.filter(owner=tenant)
    elif tenant.role == User.Role.TECHNICIAN:
        technician = Technician.objects.filter(user=tenant).first()
        context["technician"] = technician
        if technician:
            context["assigned_tickets"] = MaintenanceTicket.objects.filter(technician=technician).select_related("property", "tenant")

    return render(request, "core/admin_user_detail.html", context)


@login_required
def admin_properties(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    properties = Property.objects.select_related("owner").order_by("-created_at")
    availability = request.GET.get("available", "").strip()
    if availability == "yes":
        properties = properties.filter(available=True)
    elif availability == "no":
        properties = properties.filter(available=False)
    return render(request, "core/admin_properties.html", {
        "properties": properties,
        "selected_availability": availability,
    })


@login_required
def admin_property_detail(request, pk):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    property_obj = get_object_or_404(Property.objects.select_related("owner"), pk=pk)
    return render(request, "core/admin_property_detail.html", {
        "property": property_obj,
        "rental_requests": RentalRequest.objects.filter(property=property_obj).select_related("tenant", "room"),
        "bookings": Booking.objects.filter(property=property_obj).select_related("tenant", "room"),
        "tickets": MaintenanceTicket.objects.filter(property=property_obj).select_related("tenant"),
    })


@login_required
def admin_rental_requests(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    requests_qs = RentalRequest.objects.select_related("tenant", "property", "room")
    status = request.GET.get("status", "").strip()
    if status in dict(RentalRequest.Status.choices):
        requests_qs = requests_qs.filter(status=status)
    return render(request, "core/admin_rental_requests.html", {
        "requests": requests_qs,
        "statuses": RentalRequest.Status.choices,
        "selected_status": status,
    })


@login_required
def admin_payments(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    payments = Payment.objects.select_related("tenant", "booking__property")
    status = request.GET.get("status", "").strip()
    if status in dict(Payment.Status.choices):
        payments = payments.filter(status=status)
    return render(request, "core/admin_payments.html", {
        "payments": payments,
        "statuses": Payment.Status.choices,
        "selected_status": status,
    })


@login_required
def admin_maintenance(request):
    if not _admin_only(request):
        return HttpResponseForbidden("Administrator access is required.")
    tickets = MaintenanceTicket.objects.select_related("tenant", "property", "technician")
    status = request.GET.get("status", "").strip()
    if status in dict(MaintenanceTicket.Status.choices):
        tickets = tickets.filter(status=status)
    return render(request, "core/admin_maintenance.html", {
        "tickets": tickets,
        "technician_reports": TechnicianReport.objects.select_related("technician", "ticket", "technician__user"),
        "statuses": MaintenanceTicket.Status.choices,
        "selected_status": status,
    })
