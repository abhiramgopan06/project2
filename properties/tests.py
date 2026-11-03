from datetime import timedelta

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, RentalRequest
from .forms import PropertyForm
from .models import Amenity, Property, Room


class PropertyAuthorizationTests(TestCase):
    def setUp(self):
        self.owner1 = User.objects.create_user(username="owner1", email="o1@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.owner2 = User.objects.create_user(username="owner2", email="o2@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="tenant", email="t@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.property = Property.objects.create(
            owner=self.owner1, title="Test Home", description="A comfortable test property.",
            property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Road",
            number_of_rooms=2, rent=15000, available=True,
        )
        Amenity.objects.create(name="WiFi")

    def test_public_list_shows_available_property(self):
        response = self.client.get(reverse("properties:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Home")

    def test_owner_cannot_edit_another_owners_property(self):
        self.client.force_login(self.owner2)
        response = self.client.get(reverse("properties:update", args=[self.property.pk]))
        self.assertEqual(response.status_code, 404)

    def test_tenant_cannot_open_owner_property_list(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("properties:owner_property_list"))
                                                                      
                                                                  
        self.assertRedirects(response, reverse("accounts:dashboard"), target_status_code=302)


class PropertyMapLocationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", email="o@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.model_data = {
            "title": "Map Home", "description": "Has coordinates.", "property_type": Property.PropertyType.HOUSE,
            "location": "Kochi", "address": "Test Road", "number_of_rooms": 2, "rent": 15000,
        }
        self.form_data = {**self.model_data, "amenities": []}

    def test_property_without_coordinates_has_no_map(self):
        property_ = Property.objects.create(owner=self.owner, **self.model_data)
        self.assertFalse(property_.has_map_location)
        self.assertEqual(property_.map_embed_url, "")

    def test_property_with_coordinates_builds_map_embed_url(self):
        property_ = Property.objects.create(owner=self.owner, latitude=9.9312, longitude=76.2673, **self.model_data)
        self.assertTrue(property_.has_map_location)
        self.assertIn("9.9312", property_.map_embed_url)
        self.assertIn("76.2673", property_.map_embed_url)

    def test_form_rejects_only_one_coordinate(self):
        form = PropertyForm(data={**self.form_data, "latitude": 9.9312})
        self.assertFalse(form.is_valid())
        self.assertIn("longitude", form.errors)

    def test_form_accepts_both_coordinates_or_neither(self):
        form = PropertyForm(data={**self.form_data, "latitude": 9.9312, "longitude": 76.2673})
        self.assertTrue(form.is_valid())
        form = PropertyForm(data=self.form_data)
        self.assertTrue(form.is_valid())


class PropertyDeleteProtectionTests(TestCase):
    """A property or room that already has a booking must not crash when deleted."""

    def setUp(self):
        self.owner = User.objects.create_user(username="owner", email="o@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="tenant", email="t@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.property = Property.objects.create(
            owner=self.owner, title="Booked Home", description="A home that has a booking.",
            property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Road",
            number_of_rooms=1, rent=12000, available=True,
        )
        self.room = Room.objects.create(property=self.property, room_number="101", rent=5000)
        start = timezone.localdate() + timedelta(days=5)
        rental_request = RentalRequest.objects.create(
            tenant=self.tenant, property=self.property, room=self.room, move_in_date=start, duration_months=3,
        )
        Booking.objects.create(
            rental_request=rental_request, tenant=self.tenant, property=self.property,
            room=self.room, start_date=start, duration_months=3,
        )
        self.client.force_login(self.owner)

    def test_property_with_booking_is_not_deleted_and_shows_message(self):
        url = reverse("properties:delete", args=[self.property.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("properties:owner_property_detail", args=[self.property.pk]))
        self.assertTrue(Property.objects.filter(pk=self.property.pk).exists())

    def test_room_with_booking_is_not_deleted(self):
        url = reverse("properties:room_delete", args=[self.property.pk, self.room.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("properties:owner_property_detail", args=[self.property.pk]))
        self.assertTrue(Room.objects.filter(pk=self.room.pk).exists())

    def test_property_without_bookings_can_still_be_deleted(self):
        empty = Property.objects.create(
            owner=self.owner, title="Empty Home", description="No bookings here.",
            property_type=Property.PropertyType.HOUSE, location="Kochi", address="Other Road",
            number_of_rooms=1, rent=9000, available=True,
        )
        response = self.client.post(reverse("properties:delete", args=[empty.pk]))
        self.assertRedirects(response, reverse("properties:owner_property_list"))
        self.assertFalse(Property.objects.filter(pk=empty.pk).exists())


class PropertyRoleTests(TestCase):
    def test_only_owner_can_list_property(self):
        from accounts.models import User
        tenant = User.objects.create_user(username="tenant_role", email="tenant_role@example.com", password="Pass12345", role=User.Role.TENANT)
        property_obj = Property(owner=tenant, title="Test Home", description="A test property", property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Road", rent=10000)
        with self.assertRaises(ValidationError):
            property_obj.full_clean()


class PropertyExpenseTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="expenseowner", email="expenseowner@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.other_owner = User.objects.create_user(username="otherexpenseowner", email="otherexpense@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="expensetenant", email="expensetenant@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.property = Property.objects.create(owner=self.owner, title="Expense Home", description="Test property.", property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Road", number_of_rooms=1, rent=12000)

    def test_owner_can_record_an_expense_for_their_property(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("properties:owner_expenses"), {"property": self.property.pk, "category": "MAINTENANCE", "amount": "1250.00", "expense_date": timezone.localdate().isoformat(), "description": "Tap repair"})
        self.assertRedirects(response, reverse("properties:owner_expenses"))
        from .models import PropertyExpense
        self.assertEqual(PropertyExpense.objects.get().amount, 1250)

    def test_owner_cannot_record_expense_for_another_owner_property(self):
        other_property = Property.objects.create(owner=self.other_owner, title="Other Expense Home", description="Test property.", property_type=Property.PropertyType.HOUSE, location="Kochi", address="Other Road", number_of_rooms=1, rent=10000)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("properties:owner_expenses"), {"property": other_property.pk, "category": "OTHER", "amount": "100", "expense_date": timezone.localdate().isoformat(), "description": "Not mine"})
        self.assertEqual(response.status_code, 200)
        from .models import PropertyExpense
        self.assertFalse(PropertyExpense.objects.exists())

    def test_tenant_cannot_access_owner_expenses(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("properties:owner_expenses"))
        self.assertRedirects(response, reverse("accounts:dashboard"), target_status_code=302)
