from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from bookings.models import Booking, RentalRequest

from accounts.models import User
from properties.models import Property


class ReportTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", email="owner@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="tenant", email="tenant@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.property = Property.objects.create(
            owner=self.owner, title="Reported Home", description="A property that can be reported.",
            property_type=Property.PropertyType.APARTMENT, location="Kochi", address="Main Road",
            number_of_rooms=1, rent=10000, available=True,
        )

    def make_active_booking(self):
        start = timezone.localdate() - timedelta(days=10)
        rental_request = RentalRequest.objects.create(
            tenant=self.tenant, property=self.property, move_in_date=start, duration_months=1,
        )
        return Booking.objects.create(
            rental_request=rental_request, tenant=self.tenant, property=self.property,
            start_date=start, duration_months=1, status=Booking.Status.CONFIRMED,
        )

    def test_tenant_with_active_booking_can_open_report_form(self):
        self.make_active_booking()
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("core:report_property", args=[self.property.pk]))
        self.assertEqual(response.status_code, 200)

    def test_tenant_without_booking_is_blocked(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("core:report_property", args=[self.property.pk]))
        self.assertRedirects(response, reverse("properties:detail", args=[self.property.pk]))
        self.assertEqual(response.wsgi_request._messages._queued_messages[0].message,
                         "You cannot report this property because you do not have an active rental booking for it. Only the tenant currently renting the property can submit a report.")

    def test_owner_is_blocked_from_reporting(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("core:report_property", args=[self.property.pk]))
        self.assertRedirects(response, reverse("properties:detail", args=[self.property.pk]))

    def test_expired_booking_is_not_allowed_to_report(self):
        start = timezone.localdate() - timedelta(days=90)
        rental_request = RentalRequest.objects.create(
            tenant=self.tenant, property=self.property, move_in_date=start, duration_months=1,
        )
        Booking.objects.create(
            rental_request=rental_request, tenant=self.tenant, property=self.property,
            start_date=start, duration_months=1, status=Booking.Status.CONFIRMED,
        )
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("core:report_property", args=[self.property.pk]))
        self.assertRedirects(response, reverse("properties:detail", args=[self.property.pk]))

    def test_short_report_description_is_rejected(self):
        self.make_active_booking()
        self.client.force_login(self.tenant)
        response = self.client.post(
            reverse("core:report_property", args=[self.property.pk]),
            {"reason": "SCAM", "description": "Looks bad"},
        )
        self.assertEqual(response.status_code, 200)
        from .models import PropertyReport
        self.assertFalse(PropertyReport.objects.exists())
        self.assertContains(response, "at least 20 characters")

    def test_anonymous_user_cannot_report(self):
        response = self.client.get(reverse("core:report_property", args=[self.property.pk]))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('core:report_property', args=[self.property.pk])}")


class ThemeToggleTests(TestCase):
    def test_home_page_has_theme_toggle_and_script(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="theme-toggle"')
        self.assertContains(response, "js/script.js")
        self.assertContains(response, 'data-bs-theme="light"')


class AdminDashboardUpgradeTests(TestCase):
    def setUp(self):
        from accounts.models import User
        self.admin = User.objects.create_superuser(username="upgradeadmin", email="upgradeadmin@example.com", password="StrongPass123!")

    def test_admin_dashboard_displays_platform_controls(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("core:admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pending Extensions")
        self.assertContains(response, "Open Maintenance Work")

    def test_admin_maintenance_page_renders_work_and_technician_reports(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("core:admin_maintenance"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Maintenance Work")
        self.assertContains(response, "Technician Reports")
