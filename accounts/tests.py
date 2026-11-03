from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import reverse

from .models import EmailVerification, User


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class AuthenticationTests(TestCase):
    def setUp(self):
        self.tenant = User.objects.create_user(
            username="tenant1", email="tenant@example.com", password="StrongPass123!", role=User.Role.TENANT
        )
        self.owner = User.objects.create_user(
            username="owner1", email="owner@example.com", password="StrongPass123!", role=User.Role.OWNER
        )

    def _register(self, username="newtenant", email="newtenant@example.com"):
        return self.client.post(reverse("accounts:register"), {
            "username": username, "first_name": "New", "last_name": "Tenant",
            "email": email, "phone": "9876543210", "role": "TENANT",
            "password1": "StrongPass123!", "password2": "StrongPass123!",
        })

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_registration_requires_email_verification(self, mock_otp, mock_send_mail):
        response = self._register()
        self.assertRedirects(response, reverse("accounts:verify_email"))
        user = User.objects.get(username="newtenant")
        self.assertFalse(user.is_active)
        self.assertTrue(check_password("123456", user.email_verification.otp_hash))
        mock_send_mail.assert_called_once()
        self.assertEqual(mock_send_mail.call_args[0][3], ["newtenant@example.com"])

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_correct_otp_activates_account_and_returns_to_login(self, mock_otp, mock_send_mail):
        self._register(username="verifieduser", email="verified@example.com")
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "123456"})
        self.assertRedirects(response, reverse("accounts:login"), fetch_redirect_response=False)
        user = User.objects.get(username="verifieduser")
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verification.verified)
        login_page = self.client.get(reverse("accounts:login"))
        self.assertContains(login_page, 'value="verifieduser"')
        login = self.client.post(reverse("accounts:login"), {"username": "verifieduser", "password": "StrongPass123!"})
        self.assertRedirects(login, reverse("accounts:dashboard"), target_status_code=302)

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_wrong_otp_does_not_activate_account(self, mock_otp, mock_send_mail):
        self._register(username="wrongotp", email="wrongotp@example.com")
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "000000"}, follow=True)
        self.assertRedirects(response, reverse("accounts:verify_email"))
        self.assertContains(response, "not correct")
        self.assertFalse(User.objects.get(username="wrongotp").is_active)
        self.assertEqual(EmailVerification.objects.get(user__username="wrongotp").attempts, 1)

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", side_effect=["111111", "222222"])
    def test_resend_sends_a_fresh_code_that_replaces_the_old_one(self, mock_otp, mock_send_mail):
        self._register(username="resender", email="resender@example.com")
        self.client.post(reverse("accounts:verify_email"), {"action": "resend"})
        self.assertEqual(mock_send_mail.call_count, 1)
        EmailVerification.objects.filter(user__username="resender").update(
            last_sent_at=timezone.now() - timedelta(seconds=31))
        self.client.post(reverse("accounts:verify_email"), {"action": "resend"})
        self.assertEqual(mock_send_mail.call_count, 2)
        self.client.post(reverse("accounts:verify_email"), {"otp": "111111"})
        self.assertFalse(User.objects.get(username="resender").is_active)
        response = self.client.post(reverse("accounts:verify_email"), {"otp": "222222"})
        self.assertRedirects(response, reverse("accounts:login"))

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_expired_otp_is_rejected(self, mock_otp, mock_send_mail):
        self._register(username="expired", email="expired@example.com")
        EmailVerification.objects.filter(user__username="expired").update(
            expires_at=timezone.now() - timedelta(minutes=1))
        self.client.post(reverse("accounts:verify_email"), {"otp": "123456"})
        self.assertFalse(User.objects.get(username="expired").is_active)

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_five_wrong_codes_lock_until_resend(self, mock_otp, mock_send_mail):
        self._register(username="locked", email="locked@example.com")
        for _ in range(5):
            self.client.post(reverse("accounts:verify_email"), {"otp": "000000"})
        self.client.post(reverse("accounts:verify_email"), {"otp": "123456"})
        self.assertFalse(User.objects.get(username="locked").is_active)
        page = self.client.get(reverse("accounts:verify_email"))
        self.assertContains(page, "Too many wrong attempts")

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_unverified_user_can_register_again_with_same_details(self, mock_otp, mock_send_mail):
        self._register(username="retry", email="retry@example.com")
        response = self._register(username="retry", email="retry@example.com")
        self.assertRedirects(response, reverse("accounts:verify_email"))
        self.assertEqual(User.objects.filter(username="retry").count(), 1)

    @patch("accounts.views.send_mail")
    @patch("accounts.views._new_otp", return_value="123456")
    def test_login_before_verifying_goes_to_otp_page(self, mock_otp, mock_send_mail):
        self._register(username="early", email="early@example.com")
        self.client.logout()
        fresh = self.client_class()
        response = fresh.post(reverse("accounts:login"), {"username": "early", "password": "StrongPass123!"})
        self.assertRedirects(response, reverse("accounts:verify_email"))

    @patch("accounts.views.send_mail", side_effect=Exception("smtp down"))
    def test_failed_email_does_not_leave_a_half_made_account(self, mock_send_mail):
        response = self._register(username="nomail", email="nomail@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nomail").exists())

    def test_login_page_has_register_link_then_google_button(self):
        html = self.client.get(reverse("accounts:login")).content.decode()
        self.assertLess(html.index("Don't have an account?"), html.index("Continue with Google"))
        self.assertIn(reverse("accounts:google_login"), html)

    @override_settings(GOOGLE_CLIENT_ID="", GOOGLE_CLIENT_SECRET="")
    def test_google_login_without_credentials_shows_a_message_instead_of_crashing(self):
        response = self.client.get(reverse("accounts:google_login"), follow=True)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertContains(response, "not set up yet")

    def test_owner_cannot_open_tenant_dashboard(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("accounts:tenant_dashboard"))
        self.assertEqual(response.status_code, 403)


    def test_dashboard_access_is_restricted_to_the_matching_role(self):
        from django.urls import reverse
        from maintenance.models import Technician
        technician = User.objects.create_user(
            username="dashboardtech", email="dashboardtech@example.com",
            password="StrongPass123!", role=User.Role.TECHNICIAN
        )
        admin = User.objects.create_superuser(
            username="dashboardadmin", email="dashboardadmin@example.com",
            password="StrongPass123!"
        )
        Technician.objects.create(
            owner=self.owner, user=technician, name="Dashboard Technician",
            email=technician.email, specialization="General"
        )
        dashboard_urls = {
            "tenant": reverse("accounts:tenant_dashboard"),
            "owner": reverse("accounts:owner_dashboard"),
            "technician": reverse("maintenance:technician_tickets"),
            "admin": reverse("core:admin_dashboard"),
        }
        users = {
            "tenant": self.tenant,
            "owner": self.owner,
            "technician": technician,
            "admin": admin,
        }
        for user_role, user in users.items():
            self.client.force_login(user)
            for dashboard_role, url in dashboard_urls.items():
                response = self.client.get(url)
                if user_role == dashboard_role:
                    self.assertEqual(
                        response.status_code, 200,
                        f"{user_role} should access {dashboard_role} dashboard"
                    )
                else:
                    self.assertEqual(
                        response.status_code, 403,
                        f"{user_role} must not access {dashboard_role} dashboard"
                    )

    def test_logout_requires_post(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:dashboard"), target_status_code=302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_goes_back_to_the_page_the_user_came_from(self):
        response = self.client.post(
            reverse("accounts:login") + "?next=/properties/",
            {"username": "tenant1", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, "/properties/")

    def test_login_ignores_next_pointing_to_another_website(self):
        response = self.client.post(
            reverse("accounts:login") + "?next=https://evil.example.com/",
            {"username": "tenant1", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("accounts:dashboard"), target_status_code=302)


class RoleDashboardRenderingTests(TestCase):
    def setUp(self):
        self.tenant = User.objects.create_user(username="dashboardtenant", email="dashboardtenant@example.com", password="StrongPass123!", role=User.Role.TENANT)
        self.owner = User.objects.create_user(username="dashboardowner", email="dashboardowner@example.com", password="StrongPass123!", role=User.Role.OWNER)

    def test_tenant_dashboard_renders_rental_overview(self):
        self.client.force_login(self.tenant)
        response = self.client.get(reverse("accounts:tenant_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current rentals")
        self.assertContains(response, "Payments & receipts")

    def test_owner_dashboard_renders_management_sections(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("accounts:owner_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Agreements & handover")
        self.assertContains(response, "Property expenses")
        self.assertContains(response, "Extension requests")
