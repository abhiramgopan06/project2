import json
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from bookings.reminders import expiry_reminders_for, rent_reminders_for
from bookings.models import Booking, RentalRequest
from properties.models import Property
from maintenance.models import MaintenanceTicket, Notification

from .forms import ProfileForm, RegistrationForm
from .models import EmailVerification, User

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 10
OTP_RESEND_SECONDS = 30
MAX_OTP_ATTEMPTS = 5


def _new_otp():
    """Make a random 6-digit code (uses `secrets`, which is safe for security codes)."""
    return f"{secrets.randbelow(900000) + 100000:06d}"


def _mask_email(email):
    """john.doe@gmail.com -> jo****e@gmail.com (shown on the OTP page)."""
    name, _, domain = email.partition("@")
    if len(name) <= 2:
        return f"{name[0]}***@{domain}" if name else email
    return f"{name[:2]}{'*' * (len(name) - 3)}{name[-1]}@{domain}"


def _send_otp(user):
    """Create a new OTP for the user, save only its hash, and email the real code."""
    now = timezone.now()
    code = _new_otp()
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            "otp_hash": make_password(code),
            "expires_at": now + timedelta(minutes=OTP_EXPIRY_MINUTES),
            "attempts": 0,
            "verified": False,
            "last_sent_at": now,
        },
    )
    name = user.first_name or user.username
    text_body = (
        f"Hello {name},\n\n"
        f"Your Rental Platform verification code is: {code}\n\n"
        f"It expires in {OTP_EXPIRY_MINUTES} minutes. If you did not create an account, you can ignore this email.\n\n"
        "- Rental Platform"
    )
    html_body = render_to_string("accounts/email/otp_email.html", {
        "name": name, "code": code, "minutes": OTP_EXPIRY_MINUTES,
    })
    send_mail(
        "Your Rental Platform verification code",
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_body,
        fail_silently=False,
    )


def _remove_pending_registrations(username="", email=""):
    """Delete accounts that registered but never verified, so the same username/email can be reused.

    Only users who are inactive AND have an unverified OTP record are removed.
    Accounts that an admin disabled never have that record, so they are safe.
    """
    pending = User.objects.filter(is_active=False, email_verification__verified=False)
    query = Q(pk__in=[])
    if username:
        query |= Q(username__iexact=username)
    if email:
        query |= Q(email__iexact=email)
    pending.filter(query).delete()


def _verify_context(user, verification, **extra):
    """Everything the OTP page needs to draw itself."""
    now = timezone.now()
    wait = 0
    if verification.last_sent_at:
        wait = max(0, int(OTP_RESEND_SECONDS - (now - verification.last_sent_at).total_seconds()))
    context = {
        "email": user.email,
        "masked_email": _mask_email(user.email),
        "resend_wait": wait,
        "attempts_left": max(0, MAX_OTP_ATTEMPTS - verification.attempts),
        "locked": verification.attempts >= MAX_OTP_ATTEMPTS,
        "expired": now > verification.expires_at,
        "expiry_minutes": OTP_EXPIRY_MINUTES,
        "console_email": settings.EMAIL_BACKEND.endswith("console.EmailBackend"),
    }
    context.update(extra)
    return context


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        _remove_pending_registrations(
            username=request.POST.get("username", "").strip(),
            email=request.POST.get("email", "").strip().lower(),
        )
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                _send_otp(user)
            except Exception:
                user.delete()
                messages.error(request, "We could not send the verification email. Please check the email address and try again.")
                return render(request, "accounts/register.html", {"form": form})
            request.session["pending_verification_user_id"] = user.pk
            messages.success(request, f"We sent a 6-digit code to {user.email}.")
            return redirect("accounts:verify_email")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


def verify_email(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    user_id = request.session.get("pending_verification_user_id")
    if not user_id:
        messages.info(request, "Please create an account first.")
        return redirect("accounts:register")

    try:
        user = User.objects.get(pk=user_id, is_active=False)
        verification = user.email_verification
    except (User.DoesNotExist, EmailVerification.DoesNotExist):
        request.session.pop("pending_verification_user_id", None)
        messages.error(request, "This verification session is no longer valid. Please register again.")
        return redirect("accounts:register")

    if request.method == "POST":
        if request.POST.get("action") == "resend":
            seconds_since = (timezone.now() - verification.last_sent_at).total_seconds()
            if seconds_since < OTP_RESEND_SECONDS:
                messages.warning(request, "Please wait a few seconds before asking for another code.")
            else:
                try:
                    _send_otp(user)
                    messages.success(request, f"A new code was sent to {user.email}.")
                except Exception:
                    messages.error(request, "We could not send a new code. Please try again.")
            return redirect("accounts:verify_email")

        code = "".join(request.POST.get("otp", "").split())
        if not code.isdigit() or len(code) != OTP_LENGTH:
            messages.error(request, "Enter the 6-digit code from your email.")
            return redirect("accounts:verify_email")

        if verification.attempts >= MAX_OTP_ATTEMPTS:
            messages.error(request, "Too many wrong attempts. Please request a new code.")
            return redirect("accounts:verify_email")

        if timezone.now() > verification.expires_at:
            messages.error(request, "This code has expired. Please request a new one.")
            return redirect("accounts:verify_email")

        verification.attempts += 1
        if check_password(code, verification.otp_hash):
            verification.verified = True
            verification.save(update_fields=["verified", "attempts"])
            user.is_active = True
            user.save(update_fields=["is_active"])
            request.session.pop("pending_verification_user_id", None)
            request.session["verified_username"] = user.username
            messages.success(request, "Email verified! You can now log in with your username and password.")
            return redirect("accounts:login")

        verification.save(update_fields=["attempts"])
        left = MAX_OTP_ATTEMPTS - verification.attempts
        if left > 0:
            messages.error(request, f"That code is not correct. You have {left} attempt{'s' if left != 1 else ''} left.")
        else:
            messages.error(request, "That code is not correct. Please request a new code.")
        return redirect("accounts:verify_email")

    return render(request, "accounts/verify_email.html", _verify_context(user, verification))


def _google_configured():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def google_login(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    if not _google_configured():
        messages.warning(request, "Google sign-in is not set up yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET to the .env file (see AUTH_SETUP.md).")
        return redirect("accounts:login")
    state = secrets.token_urlsafe(32)
    request.session["google_oauth_state"] = state
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(url)


def google_callback(request):
    if not _google_configured():
        return redirect("accounts:login")
    state = request.GET.get("state")
    expected_state = request.session.pop("google_oauth_state", None)
    if not state or state != expected_state:
        return HttpResponseBadRequest("Google sign-in could not be verified. Please try again.")
    if request.GET.get("error"):
        messages.info(request, "Google sign-in was cancelled.")
        return redirect("accounts:login")
    code = request.GET.get("code")
    if not code:
        messages.error(request, "Google sign-in did not return a valid code.")
        return redirect("accounts:login")

    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    token_request = urllib.request.Request("https://oauth2.googleapis.com/token", data=token_data, method="POST")
    token_request.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(token_request, timeout=10) as response:
            token_json = json.loads(response.read().decode())
        access_token = token_json.get("access_token")
        if not access_token:
            raise ValueError("No Google access token")
        user_request = urllib.request.Request("https://openidconnect.googleapis.com/v1/userinfo")
        user_request.add_header("Authorization", f"Bearer {access_token}")
        with urllib.request.urlopen(user_request, timeout=10) as response:
            google_user = json.loads(response.read().decode())
    except Exception:
        messages.error(request, "Google sign-in could not be completed. Please try again.")
        return redirect("accounts:login")

    email = google_user.get("email", "").strip().lower()
    if not email or not google_user.get("email_verified"):
        messages.error(request, "Google did not provide a verified email address.")
        return redirect("accounts:login")

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        base_username = "".join(ch for ch in email.split("@")[0].lower() if ch.isalnum() or ch in "._-")[:120] or "googleuser"
        username = base_username
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            counter += 1
            username = f"{base_username}{counter}"
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=google_user.get("given_name", ""),
            last_name=google_user.get("family_name", ""),
            role=User.Role.TENANT,
            is_active=True,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

    if not user.is_active:
        waiting = EmailVerification.objects.filter(user=user, verified=False).first()
        if waiting is None:
            messages.error(request, "This account is disabled. Please contact support.")
            return redirect("accounts:login")
        waiting.verified = True
        waiting.save(update_fields=["verified"])
        user.is_active = True
        user.save(update_fields=["is_active"])
    login(request, user)
    messages.success(request, f"Welcome, {user.first_name or user.username}!")
    return redirect("accounts:dashboard")


def user_login(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    prefill_username = request.session.pop("verified_username", "")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        prefill_username = username
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(next_url)
            return redirect("accounts:dashboard")

        waiting = User.objects.filter(
            username__iexact=username, is_active=False, email_verification__verified=False
        ).first()
        if waiting and waiting.check_password(password):
            request.session["pending_verification_user_id"] = waiting.pk
            messages.info(request, "Your email is not verified yet. Enter the code we sent you, or request a new one.")
            return redirect("accounts:verify_email")
        messages.error(request, "Invalid username or password.")

    return render(request, "accounts/login.html", {"prefill_username": prefill_username})


def technician_login(request):
    if request.user.is_authenticated:
        if request.user.role == "TECHNICIAN":
            return redirect("maintenance:technician_tickets")
        return redirect("accounts:dashboard")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == "TECHNICIAN":
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}!")
            return redirect("maintenance:technician_tickets")
        messages.error(request, "Invalid technician username or password.")
    return render(request, "accounts/technician_login.html")


@login_required
def user_logout(request):
    if request.method != "POST":
        return redirect("accounts:dashboard")
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("core:home")


@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.role == "ADMIN":
        return redirect("accounts:admin_dashboard")
    if request.user.role == "OWNER":
        return redirect("accounts:owner_dashboard")
    if request.user.role == "TECHNICIAN":
        return redirect("maintenance:technician_tickets")
    return redirect("accounts:tenant_dashboard")


@login_required
def admin_dashboard(request):
    if not (request.user.is_superuser or request.user.role == "ADMIN"):
        messages.error(request, "Access denied.")
        return redirect("accounts:dashboard")
    return redirect("core:admin_dashboard")


@login_required
def owner_dashboard(request):
    if request.user.role != "OWNER":
        messages.error(request, "Access denied. Owner access is required.")
        return redirect("accounts:dashboard")
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)[:5]
    properties = Property.objects.filter(owner=request.user)
    active_bookings = Booking.objects.filter(property__owner=request.user, status=Booking.Status.CONFIRMED).select_related("property", "room")
    monthly_rent = sum((booking.monthly_rent() for booking in active_bookings if booking.end_date() >= timezone.localdate()), start=0)
    today = timezone.localdate()
    active_bookings_list = [booking for booking in active_bookings if booking.end_date() >= today]
    expiring_count = sum(1 for booking in active_bookings_list if 0 <= (booking.end_date() - today).days <= 30)
    from bookings.models import ExtensionRequest
    stats = {
        "property_count": properties.count(),
        "available_count": properties.filter(available=True).count(),
        "pending_requests": RentalRequest.objects.filter(property__owner=request.user, status=RentalRequest.Status.PENDING).count(),
        "active_bookings": len(active_bookings_list),
        "monthly_rent": monthly_rent,
        "expiring_rentals": expiring_count,
        "extension_requests": ExtensionRequest.objects.filter(booking__property__owner=request.user, status=ExtensionRequest.Status.PENDING).count(),
        "open_tickets": MaintenanceTicket.objects.filter(property__owner=request.user, status__in=[MaintenanceTicket.Status.OPEN, MaintenanceTicket.Status.ASSIGNED, MaintenanceTicket.Status.ACCEPTED, MaintenanceTicket.Status.IN_PROGRESS]).count(),
    }
    return render(request, "accounts/owner_dashboard.html", {"notifications": notifications, "stats": stats})


@login_required
def tenant_dashboard(request):
    if request.user.role != "TENANT":
        messages.error(request, "Access denied. Tenant access is required.")
        return redirect("accounts:dashboard")
    bookings = Booking.objects.filter(tenant=request.user, status=Booking.Status.CONFIRMED).select_related("property", "room")
    today = timezone.localdate()
    active_bookings = [booking for booking in bookings if booking.end_date() >= today]
    context = {
        "rent_reminders": rent_reminders_for(request.user),
        "expiry_reminders": expiry_reminders_for(request.user),
        "active_bookings": active_bookings,
        "active_rental_count": len(active_bookings),
        "pending_requests": RentalRequest.objects.filter(tenant=request.user, status=RentalRequest.Status.PENDING).count(),
        "notifications": Notification.objects.filter(recipient=request.user, is_read=False)[:5],
    }
    return render(request, "accounts/tenant_dashboard.html", context)


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})
