from django.contrib import messages
from django.contrib.auth.decorators import login_required
from decimal import Decimal, InvalidOperation

from django.db.models import ProtectedError, Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from bookings.models import Booking

from .forms import PropertyExpenseForm, PropertyForm, PropertyImageForm, PropertyVerificationDocumentForm, RoomForm
from .models import Property, PropertyExpense, PropertyImage, PropertyVerificationDocument, Room, SavedProperty


def property_list(request):
    """Public/tenant property discovery page. Only currently available listings are shown."""
    properties = (
        Property.objects.filter(available=True)
        .select_related("owner")
        .prefetch_related("images", "amenities", "rooms")
    )

    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    property_type = request.GET.get("property_type", "").strip()
    min_rent = request.GET.get("min_rent", "").strip()
    max_rent = request.GET.get("max_rent", "").strip()

    if query:
        properties = properties.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
            | Q(address__icontains=query)
        )
    if location:
        properties = properties.filter(location__icontains=location)
    if property_type in dict(Property.PropertyType.choices):
        properties = properties.filter(property_type=property_type)

    rent_error = ""
    min_value = max_value = None
    if min_rent:
        try:
            min_value = Decimal(min_rent)
            if min_value < 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError, ValueError):
            rent_error = "Minimum rent must be a valid non-negative number."
        else:
            properties = properties.filter(rent__gte=min_value)
    if max_rent:
        try:
            max_value = Decimal(max_rent)
            if max_value < 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError, ValueError):
            rent_error = "Maximum rent must be a valid non-negative number."
        else:
            properties = properties.filter(rent__lte=max_value)
    if min_value is not None and max_value is not None and min_value > max_value:
        rent_error = "Minimum rent cannot be greater than maximum rent."
        properties = Property.objects.none()

    sort = request.GET.get("sort", "newest")
    sort_options = {"newest": "-created_at", "rent_low": "rent", "rent_high": "-rent", "title": "title"}
    properties = properties.order_by(sort_options.get(sort, "-created_at"))
    saved_ids = set()
    if request.user.is_authenticated and getattr(request.user, "role", "") == "TENANT":
        saved_ids = set(SavedProperty.objects.filter(user=request.user).values_list("property_id", flat=True))

    paginator = Paginator(properties, 9)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    return render(
        request,
        "properties/property_list.html",
        {
            "properties": page_obj,
            "page_obj": page_obj,
            "property_types": Property.PropertyType.choices,
            "filters": request.GET,
            "rent_error": rent_error,
            "result_count": paginator.count,
            "sort": sort,
            "saved_ids": saved_ids,
        },
    )


def property_detail(request, pk):
    property_obj = get_object_or_404(
        Property.objects.select_related("owner").prefetch_related("images", "rooms", "amenities"),
        pk=pk,
    )
    can_report_property = False
    if request.user.is_authenticated and getattr(request.user, "role", "") == "TENANT":
        today = timezone.localdate()
        active_bookings = Booking.objects.filter(
            tenant=request.user,
            property=property_obj,
            status=Booking.Status.CONFIRMED,
            start_date__lte=today,
        )
        can_report_property = any(
            booking.end_date() and booking.end_date() >= today
            for booking in active_bookings
        )
    return render(
        request,
        "properties/property_detail.html",
        {"property": property_obj, "can_report_property": can_report_property,
         "is_saved": request.user.is_authenticated and SavedProperty.objects.filter(user=request.user, property=property_obj).exists() if getattr(request.user, "role", "") == "TENANT" else False},
    )


def owner_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if request.user.role != "OWNER":
            messages.error(request, "Owner access is required.")
            return redirect("accounts:dashboard")
        return view_func(request, *args, **kwargs)
    wrapped.__name__ = view_func.__name__
    wrapped.__doc__ = view_func.__doc__
    return wrapped


@owner_required
def owner_property_list(request):
    properties = Property.objects.filter(owner=request.user).prefetch_related("images", "rooms")
    return render(request, "properties/owner_property_list.html", {"properties": properties})


@owner_required
def property_create(request):
    if request.method == "POST":
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            form.save_m2m()
            messages.success(request, "Property created successfully.")
            return redirect("properties:owner_property_detail", pk=property_obj.pk)
    else:
        form = PropertyForm()
    return render(request, "properties/property_form.html", {"form": form, "page_title": "Add Property"})


@owner_required
def property_update(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Property updated successfully.")
            return redirect("properties:owner_property_detail", pk=property_obj.pk)
    else:
        form = PropertyForm(instance=property_obj)
    return render(request, "properties/property_form.html", {"form": form, "page_title": "Edit Property", "property": property_obj})


@owner_required
def property_delete(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        try:
            property_obj.delete()
        except ProtectedError:
                                                                             
                                                                          
                                                                      
                                                           
            messages.error(
                request,
                "This property has bookings or maintenance tickets, so it cannot be deleted. "
                "Edit the property and untick 'Available' to hide it instead.",
            )
            return redirect("properties:owner_property_detail", pk=property_obj.pk)
        messages.success(request, "Property deleted successfully.")
        return redirect("properties:owner_property_list")
    return render(request, "properties/property_confirm_delete.html", {"property": property_obj})


@owner_required
def owner_property_detail(request, pk):
    property_obj = get_object_or_404(
        Property.objects.prefetch_related("images", "rooms", "amenities"),
        pk=pk,
        owner=request.user,
    )
    image_form = PropertyImageForm()
    verification_form = PropertyVerificationDocumentForm()
    return render(request, "properties/owner_property_detail.html", {"property": property_obj, "image_form": image_form, "verification_form": verification_form})


@owner_required
def property_image_add(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method != "POST":
        return redirect("properties:owner_property_detail", pk=pk)
    form = PropertyImageForm(request.POST, request.FILES)
    if form.is_valid():
        image = form.save(commit=False)
        image.property = property_obj
        image.save()
        messages.success(request, "Property image uploaded successfully.")
    else:
        messages.error(request, "Please select a valid image.")
    return redirect("properties:owner_property_detail", pk=pk)


@owner_required
def property_image_delete(request, pk, image_pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    image = get_object_or_404(PropertyImage, pk=image_pk, property=property_obj)
    if request.method == "POST":
        was_primary = image.is_primary
        image.delete()
        if was_primary:
            replacement = property_obj.images.first()
            if replacement:
                replacement.is_primary = True
                replacement.save()
        messages.success(request, "Property image deleted successfully.")
    return redirect("properties:owner_property_detail", pk=pk)


@owner_required
def room_create(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.property = property_obj
            room.save()
            messages.success(request, "Room added successfully.")
            return redirect("properties:owner_property_detail", pk=pk)
    else:
        form = RoomForm()
    return render(request, "properties/room_form.html", {"form": form, "property": property_obj, "page_title": "Add Room"})


@owner_required
def room_update(request, pk, room_pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    room = get_object_or_404(Room, pk=room_pk, property=property_obj)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, "Room updated successfully.")
            return redirect("properties:owner_property_detail", pk=pk)
    else:
        form = RoomForm(instance=room)
    return render(request, "properties/room_form.html", {"form": form, "property": property_obj, "room": room, "page_title": "Edit Room"})


@owner_required
def room_delete(request, pk, room_pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    room = get_object_or_404(Room, pk=room_pk, property=property_obj)
    if request.method == "POST":
        try:
            room.delete()
        except ProtectedError:
                                                                                  
            messages.error(
                request,
                "This room has bookings, so it cannot be deleted. "
                "Edit the room and untick 'Available' to hide it instead.",
            )
            return redirect("properties:owner_property_detail", pk=pk)
        messages.success(request, "Room deleted successfully.")
        return redirect("properties:owner_property_detail", pk=pk)
    return render(request, "properties/room_confirm_delete.html", {"property": property_obj, "room": room})


@login_required
def toggle_saved_property(request, pk):
    if request.method != "POST" or request.user.role != "TENANT":
        messages.error(request, "Only tenants can save properties.")
        return redirect("properties:list")
    property_obj = get_object_or_404(Property, pk=pk, available=True)
    saved, created = SavedProperty.objects.get_or_create(user=request.user, property=property_obj)
    if not created:
        saved.delete()
        messages.info(request, "Property removed from your saved list.")
    else:
        messages.success(request, "Property saved for later.")
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("properties:list")


@login_required
def saved_properties(request):
    if request.user.role != "TENANT":
        messages.error(request, "Saved properties are available to tenant accounts.")
        return redirect("accounts:dashboard")
    saved = SavedProperty.objects.filter(user=request.user, property__available=True).select_related("property", "property__owner").prefetch_related("property__images", "property__amenities", "property__rooms")
    return render(request, "properties/saved_properties.html", {"saved_properties": saved})


@owner_required
def upload_verification_document(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    if request.method == "POST":
        form = PropertyVerificationDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.property = property_obj
            document.save()
            property_obj.verification_status = Property.VerificationStatus.PENDING
            property_obj.save(update_fields=["verification_status"])
            messages.success(request, "Document submitted. The admin team must review it before the verified label appears.")
        else:
            messages.error(request, "Please upload a valid document and try again.")
    return redirect("properties:owner_property_detail", pk=pk)


@login_required
def owner_expenses(request):
    if request.user.role != "OWNER":
        messages.error(request, "Only property owners can manage property expenses.")
        return redirect("accounts:dashboard")
    expenses = PropertyExpense.objects.filter(property__owner=request.user).select_related("property")
    form = PropertyExpenseForm(request.POST or None, request.FILES or None, owner=request.user)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        if expense.property.owner_id != request.user.id:
            messages.error(request, "You can only add expenses to your own properties.")
        else:
            expense.save()
            messages.success(request, "Property expense saved.")
            return redirect("properties:owner_expenses")
    total = sum((item.amount for item in expenses), Decimal("0.00"))
    return render(request, "properties/owner_expenses.html", {"expenses": expenses, "form": form, "total": total})
