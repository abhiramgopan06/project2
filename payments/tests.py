from django.test import TestCase
from django.urls import reverse



class OwnerPaymentHistoryTests(TestCase):
    def setUp(self):
        from accounts.models import User
        from bookings.models import Booking, RentalRequest
        from properties.models import Property
        from django.utils import timezone
        from datetime import timedelta
        self.owner = User.objects.create_user(username="payowner", email="payowner@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="paytenant", email="paytenant@example.com", password="StrongPass123!", role=User.Role.TENANT)
        property_obj = Property.objects.create(owner=self.owner, title="Payment Home", description="Test home.", property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Road", number_of_rooms=1, rent=10000)
        rental_request = RentalRequest.objects.create(tenant=self.tenant, property=property_obj, move_in_date=timezone.localdate() + timedelta(days=1), duration_months=6)
        self.booking = Booking.objects.create(rental_request=rental_request, tenant=self.tenant, property=property_obj, start_date=rental_request.move_in_date, duration_months=6)

    def test_owner_can_view_only_their_payment_records(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("payments:owner_history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tenant payment records")

    def test_tenant_cannot_open_owner_payment_history(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("payments:owner_history"))
        self.assertRedirects(response, reverse("accounts:dashboard"), target_status_code=302)
