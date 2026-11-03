from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, RentalRequest
from maintenance.models import MaintenanceTicket, Technician, TechnicianPreparationItem
from properties.models import Property


class TechnicianPreparationTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="workowner", email="workowner@example.com", password="StrongPass123!", role=User.Role.OWNER)
        self.tenant = User.objects.create_user(username="worktenant", email="worktenant@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.tech_user = User.objects.create_user(username="worktech", email="worktech@example.com", password="StrongPass123!", role=User.Role.TECHNICIAN)
        self.property = Property.objects.create(owner=self.owner, title="Repair Home", description="A test property.", property_type=Property.PropertyType.HOUSE, location="Kochi", address="Test Lane", number_of_rooms=1, rent=10000, available=False)
        rental_request = RentalRequest.objects.create(tenant=self.tenant, property=self.property, move_in_date=timezone.localdate() - timedelta(days=10), duration_months=6)
        self.booking = Booking.objects.create(rental_request=rental_request, tenant=self.tenant, property=self.property, start_date=rental_request.move_in_date, duration_months=6)
        self.technician = Technician.objects.create(owner=self.owner, user=self.tech_user, name="Test Technician", email="worktech@example.com", specialization="Plumbing")
        self.work = MaintenanceTicket.objects.create(tenant=self.tenant, property=self.property, booking=self.booking, technician=self.technician, title="Water leak", description="Water is leaking below the kitchen sink.", status=MaintenanceTicket.Status.ASSIGNED)

    def test_accepting_job_creates_preparation_checklist(self):
        self.client.force_login(self.tech_user)
        response = self.client.post(reverse("maintenance:accept_ticket", args=[self.work.pk]))
        self.assertRedirects(response, reverse("maintenance:technician_tickets"))
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, MaintenanceTicket.Status.ACCEPTED)
        self.assertEqual(self.work.preparation_items.count(), 7)

    def test_technician_cannot_start_until_checklist_is_complete(self):
        self.client.force_login(self.tech_user)
        self.client.post(reverse("maintenance:accept_ticket", args=[self.work.pk]))
        response = self.client.post(reverse("maintenance:start_ticket", args=[self.work.pk]))
        self.assertRedirects(response, reverse("maintenance:technician_tickets"))
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, MaintenanceTicket.Status.ACCEPTED)
        for item in self.work.preparation_items.all():
            self.client.post(reverse("maintenance:update_preparation_item", args=[item.pk]), {"completed": "yes"})
        self.client.post(reverse("maintenance:start_ticket", args=[self.work.pk]))
        self.work.refresh_from_db()
        self.assertEqual(self.work.status, MaintenanceTicket.Status.IN_PROGRESS)

    def test_technician_dashboard_uses_assigned_work_language(self):
        self.client.force_login(self.tech_user)
        response = self.client.get(reverse("maintenance:technician_tickets"))
        self.assertContains(response, "My assigned work")
        self.assertNotContains(response, "My Tickets")
        self.assertNotContains(response, "Ticket #")
