from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import admin as django_admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.sessions.backends.db import SessionStore
from django.core import mail
from django.test import RequestFactory
from django.urls import reverse
from django.test import TestCase, override_settings
from PIL import Image
from sales.models import Sale
from .forms import StaffCreationForm
from .models import AccountCreationRequest, ContactEmail, ProfileChangeRequest
from log.models import ActivityLog


class StaffAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin-password",
        )
        self.client.force_login(self.admin_user)

    def test_user_change_page_loads_with_contact_numbers_display(self):
        user = get_user_model().objects.create_user(
            username="existing-staff",
            password="staff-password",
        )

        response = self.client.get(
            reverse("admin:accounts_user_change", args=(user.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contact numbers")

    def test_adding_staff_returns_to_add_staff_page(self):
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "username": "new-staff",
                "first_name": "New",
                "middle_name": "Test",
                "last_name": "Staff",
                "phone_number": "9800000000",
                "role": "STAFF",
                "hiring_date": "2026-09-23",
                "email": "new.staff@example.com",
                "is_active": "on",
                "password1": "a-strong-password-123",
                "password2": "a-strong-password-123",
            },
        )

        self.assertRedirects(response, reverse("admin:accounts_user_add"))
        self.assertTrue(
            get_user_model().objects.filter(username="new-staff").exists()
        )


class StaffAuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff-user",
            password="valid-test-password-123",
        )

    def test_landing_page_is_staff_login_and_dashboard_requires_authentication(self):
        login_response = self.client.get("/")
        dashboard_response = self.client.get(reverse("dashboard"))

        self.assertEqual(login_response.status_code, 200)
        self.assertTemplateUsed(login_response, "accounts/staff_login.html")
        self.assertRedirects(
            dashboard_response,
            f'{reverse("staff_login")}?next={reverse("dashboard")}',
        )

    def test_landing_page_stays_sign_in_when_a_session_is_already_authenticated(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("staff_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_login.html")
        self.assertContains(response, "Welcome back")

    def test_login_page_shows_branded_staff_sign_in(self):
        response = self.client.get(reverse("staff_login"))

        self.assertContains(response, "Ganesh Pustak Pasal")
        self.assertContains(response, "Smarter inventory,")
        self.assertContains(response, "Inventory Management")
        self.assertContains(response, "Fast &amp; Easy Billing")
        self.assertContains(response, "Sales Overview &amp; Reports")
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertContains(response, reverse("signup"))
        self.assertNotContains(response, "Your bookshop, in good hands")
        self.assertNotContains(response, "Secure sign in")
        self.assertNotContains(response, "Staff workspace")
        self.assertNotContains(
            response,
            "Staff accounts are created by your administrator.",
        )
        self.assertNotContains(response, "Your session ends when you close this browser.")
        self.assertNotContains(response, "Continue with Google")
        self.assertContains(response, "New here?")
        self.assertContains(response, "Create account")

    def test_signup_page_displays_maintenance_message_and_returns_to_login(self):
        response = self.client.get(reverse("signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/signup.html")
        self.assertContains(response, "Less hassle")
        self.assertContains(response, "Full name")
        self.assertContains(response, "First name")
        self.assertContains(response, "Middle name")
        self.assertContains(response, "Last name")
        self.assertContains(response, "Enter your username")
        self.assertContains(response, "Step 1 / 4")
        self.assertContains(response, "Progress saved automatically")

    def test_signup_request_is_saved_with_a_hashed_password(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "New",
                "middle_name": "Staff",
                "last_name": "Member",
                "username": "new-bookshop-staff",
                "email": "new.staff@gmail.com",
                "phone_number": "9800000000",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account request submitted")
        account_request = AccountCreationRequest.objects.get(
            username="new-bookshop-staff"
        )
        self.assertEqual(account_request.status, "PENDING")
        self.assertNotEqual(account_request.password_hash, "Harbor!Maple?River#7391")
        self.assertTrue(
            check_password("Harbor!Maple?River#7391", account_request.password_hash)
        )
        self.assertFalse(
            get_user_model().objects.filter(username="new-bookshop-staff").exists()
        )

    def test_signup_request_rejects_duplicate_username_and_invalid_phone(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "New",
                "middle_name": "",
                "last_name": "Member",
                "username": self.user.username.upper(),
                "email": "new.staff@gmail.com",
                "phone_number": "12345",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already in use.")
        self.assertContains(response, "Enter a valid 10-digit phone number.")
        self.assertEqual(AccountCreationRequest.objects.count(), 0)

    def test_signup_validation_returns_to_the_step_with_invalid_fields(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "New",
                "middle_name": "",
                "last_name": "Member",
                "username": "new-bookshop-staff",
                "email": "not-an-email",
                "phone_number": "9800000000",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_step"], 1)
        self.assertContains(response, 'data-active-step="1"')
        self.assertEqual(AccountCreationRequest.objects.count(), 0)

    def test_signup_request_rejects_non_gmail_email(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "New",
                "middle_name": "",
                "last_name": "Member",
                "username": "new-bookshop-staff",
                "email": "new.staff@example.com",
                "phone_number": "9800000000",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not valid email address.")
        self.assertEqual(AccountCreationRequest.objects.count(), 0)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admin_can_approve_account_request(self):
        administrator = get_user_model().objects.create_superuser(
            username="signup-admin",
            email="signup-admin@example.com",
            password="admin-password-123",
        )
        self.client.post(
            reverse("signup"),
            {
                "first_name": "Approved",
                "middle_name": "",
                "last_name": "Staff",
                "username": "approved-staff",
                "email": "approved.staff@gmail.com",
                "phone_number": "9811111111",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )
        account_request = AccountCreationRequest.objects.get(username="approved-staff")
        self.assertTrue(
            ActivityLog.objects.filter(
                recipient=administrator,
                details__contains="New account request from Approved Staff.",
            ).exists()
        )
        self.client.force_login(administrator)
        dashboard_response = self.client.get("/admin/")
        self.assertEqual(
            dashboard_response.context["admin_dashboard_stats"]["pending_requests"],
            1,
        )

        response = self.client.post(
            reverse("admin:accounts_accountcreationrequest_changelist"),
            {
                "action": "approve_requests",
                "_selected_action": [account_request.pk],
            },
        )

        self.assertEqual(response.status_code, 302)
        created_user = get_user_model().objects.get(username="approved-staff")
        self.assertTrue(created_user.is_active)
        self.assertFalse(created_user.is_staff)
        self.assertTrue(created_user.check_password("Harbor!Maple?River#7391"))
        account_request.refresh_from_db()
        self.assertEqual(account_request.status, "APPROVED")
        self.assertEqual(account_request.password_hash, "")
        self.assertTrue(
            ActivityLog.objects.filter(
                recipient=created_user,
                details__contains="account request was approved",
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["approved.staff@gmail.com"])
        self.assertIn("approved", mail.outbox[0].subject.lower())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_admin_can_reject_account_request_and_clear_password_hash(self):
        administrator = get_user_model().objects.create_superuser(
            username="signup-reject-admin",
            email="signup-reject-admin@example.com",
            password="admin-password-123",
        )
        self.client.post(
            reverse("signup"),
            {
                "first_name": "Rejected",
                "middle_name": "",
                "last_name": "Staff",
                "username": "rejected-staff",
                "email": "rejected.staff@gmail.com",
                "phone_number": "9811111111",
                "password": "Harbor!Maple?River#7391",
                "confirm_password": "Harbor!Maple?River#7391",
            },
        )
        account_request = AccountCreationRequest.objects.get(username="rejected-staff")
        self.client.force_login(administrator)

        response = self.client.post(
            reverse("admin:accounts_accountcreationrequest_changelist"),
            {
                "action": "reject_requests",
                "_selected_action": [account_request.pk],
            },
        )

        self.assertEqual(response.status_code, 302)
        account_request.refresh_from_db()
        self.assertEqual(account_request.status, "REJECTED")
        self.assertEqual(account_request.password_hash, "")
        self.assertFalse(
            get_user_model().objects.filter(username="rejected-staff").exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["rejected.staff@gmail.com"])
        self.assertIn("update", mail.outbox[0].subject.lower())

    def test_successful_login_creates_browser_session(self):
        response = self.client.post(
            reverse("staff_login"),
            {
                "username": self.user.username,
                "password": "valid-test-password-123",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        login_activity = ActivityLog.objects.get(details=f'User "{self.user.username}" logged in.')
        self.assertEqual(login_activity.recipient, self.user)

    def test_staff_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse("staff_logout"))
        self.assertEqual(get_response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        post_response = self.client.post(reverse("staff_logout"))

        self.assertRedirects(post_response, reverse("staff_login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        logout_activity = ActivityLog.objects.get(
            details=f'User "{self.user.username}" logged out.'
        )
        self.assertEqual(logout_activity.recipient, self.user)

    def test_tab_close_endpoint_requires_post_and_ends_session(self):
        self.client.force_login(self.user)

        get_response = self.client.get(reverse("staff_tab_logout"))
        self.assertEqual(get_response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

        post_response = self.client.post(reverse("staff_tab_logout"))

        self.assertEqual(post_response.status_code, 204)
        self.assertNotIn("_auth_user_id", self.client.session)
        logout_activity = ActivityLog.objects.get(
            details=f'User "{self.user.username}" logged out when their tab closed.'
        )
        self.assertEqual(logout_activity.recipient, self.user)

    def test_staff_creation_rejects_duplicate_username(self):
        form = StaffCreationForm(
            data={
                "username": self.user.username,
                "first_name": "Existing",
                "middle_name": "Staff",
                "last_name": "Member",
                "phone_number": "9800000000",
                "role": "STAFF",
                "hiring_date": "2024-01-01",
                "email": "existing@example.com",
                "is_active": "on",
                "password1": "valid-test-password-123",
                "password2": "valid-test-password-123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class DashboardTests(TestCase):
    def test_dashboard_shows_sales_revenue_instead_of_stock_count(self):
        user = get_user_model().objects.create_user(
            username="dashboard-staff",
            password="valid-test-password-123",
        )
        self.client.force_login(user)

        Sale.objects.create(quantity=1, total_price="12.00")
        Sale.objects.create(quantity=2, total_price="24.00")

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_revenue"], 36)
        self.assertContains(response, "Rs. 36.00")
        self.assertNotIn("total_stock", response.context)


class StaffProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile-staff",
            password="valid-test-password-123",
            first_name="Current",
            middle_name="Kept",
            last_name="Name",
            email="current@gmail.com",
            phone_number="9800000000",
        )
        self.client.force_login(self.user)

    def test_profile_shows_current_picture_editor_and_requested_fields(self):
        ContactEmail.objects.create(user=self.user, email="secondary@gmail.com")
        self.user.contact_numbers.create(number="9811111111")
        self.user.contact_numbers.create(number="9822222222")
        response = self.client.get(reverse("profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your current profile avatar")
        self.assertContains(response, "data-profile-picture-edit")
        self.assertContains(response, "First Name")
        self.assertContains(response, "Last Name")
        self.assertContains(response, "Email")
        self.assertContains(response, "Contact Number")
        self.assertContains(response, "Middle Name")
        self.assertContains(response, "Username")
        self.assertContains(response, "New Password")
        self.assertContains(response, 'value="profile-staff"')
        self.assertContains(response, 'value="current@gmail.com"')
        self.assertContains(response, 'value="Current"')
        self.assertContains(response, 'value="Kept"')
        self.assertContains(response, 'value="Name"')
        self.assertContains(response, 'value="secondary@gmail.com"')
        self.assertContains(response, 'value="9800000000"')
        self.assertContains(response, 'value="9811111111"')
        self.assertContains(response, 'value="9822222222"')

    def test_profile_change_request_preserves_uneditable_middle_name(self):
        response = self.client.post(
            reverse("profile"),
            {
                "submit_profile_change": "1",
                "username": "profile-updated",
                "first_name": "Requested",
                "middle_name": "Changed",
                "last_name": "Update",
                "email_entry": ["requested@gmail.com", "second@gmail.com"],
                "contact_entry": ["9800000000", "9811111111"],
                "new_password": "Orbit!Cedar?Lantern#4829",
                "confirm_new_password": "Orbit!Cedar?Lantern#4829",
            },
        )

        self.assertRedirects(response, reverse("profile"))
        change = ProfileChangeRequest.objects.get(user=self.user)
        self.assertEqual(change.username, "profile-updated")
        self.assertEqual(change.first_name, "Requested")
        self.assertEqual(change.last_name, "Update")
        self.assertEqual(change.middle_name, "Changed")
        self.assertEqual(change.email, "requested@gmail.com\nsecond@gmail.com")
        self.assertEqual(change.contact_numbers, "9800000000\n9811111111")
        self.assertNotEqual(change.password_hash, "Orbit!Cedar?Lantern#4829")
        self.assertTrue(check_password("Orbit!Cedar?Lantern#4829", change.password_hash))

    def test_profile_change_request_notifies_administrators(self):
        administrator = get_user_model().objects.create_superuser(
            username="profile-notification-admin",
            email="admin@gmail.com",
            password="valid-admin-password-123",
        )
        response = self.client.post(
            reverse("profile"),
            {
                "submit_profile_change": "1",
                "username": self.user.username,
                "first_name": self.user.first_name,
                "middle_name": self.user.middle_name,
                "last_name": self.user.last_name,
                "email_entry": [self.user.email],
                "contact_entry": [self.user.phone_number],
            },
        )
        self.assertRedirects(response, reverse("profile"))

        notification = ActivityLog.objects.get(
            recipient=administrator,
            details="profile-staff has applied for profile changes.",
        )
        self.assertEqual(notification.user, self.user)
        self.client.force_login(administrator)
        admin_dashboard_response = self.client.get("/admin/")
        self.assertContains(admin_dashboard_response, notification.details)

    def test_profile_change_validates_gmail_and_ten_digit_contacts(self):
        response = self.client.post(
            reverse("profile"),
            {
                "submit_profile_change": "1",
                "username": self.user.username,
                "first_name": "Requested",
                "middle_name": "Kept",
                "last_name": "Update",
                "email_entry": ["invalid@example.com"],
                "contact_entry": ["12345"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not valid email address.")
        self.assertContains(response, "data-profile-validation-errors")
        self.assertEqual(ProfileChangeRequest.objects.count(), 0)

        response = self.client.post(
            reverse("profile"),
            {
                "submit_profile_change": "1",
                "username": self.user.username,
                "first_name": "Requested",
                "middle_name": "Kept",
                "last_name": "Update",
                "email_entry": ["valid@gmail.com"],
                "contact_entry": ["12345"],
            },
        )

        self.assertContains(response, "The contact number should be of 10 digits.")
        self.assertContains(response, "data-profile-validation-errors")
        self.assertEqual(ProfileChangeRequest.objects.count(), 0)

    def test_profile_change_rejects_taken_username_and_mismatched_password(self):
        get_user_model().objects.create_user(
            username="already-used",
            password="some-current-password-932",
        )

        response = self.client.post(
            reverse("profile"),
            {
                "submit_profile_change": "1",
                "username": "already-used",
                "first_name": "Current",
                "middle_name": "Kept",
                "last_name": "Name",
                "email_entry": ["current@gmail.com"],
                "contact_entry": [],
                "new_password": "Orbit!Cedar?Lantern#4829",
                "confirm_new_password": "Different!Cedar?Lantern#4829",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already in use.")
        self.assertContains(response, "The passwords do not match.")
        self.assertEqual(ProfileChangeRequest.objects.count(), 0)

    def test_admin_approval_applies_primary_and_additional_emails(self):
        admin_user = get_user_model().objects.create_superuser(
            username="profile-admin",
            email="admin@gmail.com",
            password="valid-admin-password-123",
        )
        change = ProfileChangeRequest.objects.create(
            user=self.user,
            first_name="Approved",
            username="approved-username",
            last_name="Profile",
            middle_name="ApprovedMiddle",
            email="primary@gmail.com\nsecondary@gmail.com",
            contact_numbers="9800000000\n9811111111",
            password_hash=make_password("Approved!Password#4972"),
        )
        request = RequestFactory().post("/admin/accounts/profilechangerequest/")
        request.user = admin_user
        request.session = SessionStore()
        request._messages = FallbackStorage(request)

        profile_admin = django_admin.site._registry[ProfileChangeRequest]
        change.status = "APPROVED"
        profile_admin.save_model(request, change, form=None, change=True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "primary@gmail.com")
        self.assertEqual(self.user.username, "approved-username")
        self.assertEqual(self.user.middle_name, "ApprovedMiddle")
        self.assertTrue(self.user.check_password("Approved!Password#4972"))
        change.refresh_from_db()
        self.assertEqual(change.password_hash, "")
        self.assertEqual(
            list(self.user.contact_emails.values_list("email", flat=True)),
            ["secondary@gmail.com"],
        )
        self.assertEqual(
            list(self.user.contact_numbers.values_list("number", flat=True)),
            ["9800000000", "9811111111"],
        )
        self.assertTrue(
            ActivityLog.objects.filter(
                recipient=self.user,
                details="Your profile change request was approved by profile-admin.",
            ).exists()
        )
        self.client.force_login(self.user)
        profile_response = self.client.get(reverse("profile"))
        self.assertContains(
            profile_response,
            "Your profile change request was approved by profile-admin.",
        )
        self.assertContains(profile_response, 'value="approved-username"')
        self.assertContains(profile_response, 'value="Approved"')
        self.assertContains(profile_response, 'value="ApprovedMiddle"')
        self.assertContains(profile_response, 'value="Profile"')
        self.assertContains(profile_response, 'value="secondary@gmail.com"')
        self.assertContains(profile_response, 'value="9811111111"')

    def test_admin_rejection_keeps_profile_unchanged_and_notifies_user(self):
        administrator = get_user_model().objects.create_superuser(
            username="rejecting-admin",
            email="reject-admin@gmail.com",
            password="valid-admin-password-123",
        )
        change = ProfileChangeRequest.objects.create(
            user=self.user,
            username="rejected-username",
            first_name="Rejected",
            middle_name="Rejected",
            last_name="Rejected",
            email="rejected@gmail.com",
            contact_numbers="9999999999",
            password_hash=make_password("Rejected!Password#2497"),
        )
        request = RequestFactory().post("/admin/accounts/profilechangerequest/")
        request.user = administrator
        request.session = SessionStore()
        request._messages = FallbackStorage(request)

        profile_admin = django_admin.site._registry[ProfileChangeRequest]
        change.status = "REJECTED"
        profile_admin.save_model(request, change, form=None, change=True)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "profile-staff")
        self.assertEqual(self.user.first_name, "Current")
        self.assertEqual(self.user.middle_name, "Kept")
        self.assertEqual(self.user.last_name, "Name")
        self.assertEqual(self.user.email, "current@gmail.com")
        self.assertEqual(self.user.phone_number, "9800000000")
        self.assertFalse(self.user.check_password("Rejected!Password#2497"))
        change.refresh_from_db()
        self.assertEqual(change.status, "REJECTED")
        self.assertEqual(change.password_hash, "")
        self.assertTrue(
            ActivityLog.objects.filter(
                recipient=self.user,
                details="Your profile change request was rejected by rejecting-admin.",
            ).exists()
        )
        self.client.force_login(self.user)
        profile_response = self.client.get(reverse("profile"))
        self.assertContains(profile_response, 'value="profile-staff"')
        self.assertContains(profile_response, 'value="Current"')
        self.assertContains(profile_response, 'value="Kept"')
        self.assertContains(profile_response, 'value="Name"')
        self.assertContains(profile_response, 'value="current@gmail.com"')
        self.assertContains(profile_response, 'value="9800000000"')

    def test_profile_picture_can_be_updated_separately(self):
        image_data = BytesIO()
        Image.new("RGB", (1, 1), color="blue").save(image_data, format="PNG")
        image = SimpleUploadedFile(
            "profile.png",
            image_data.getvalue(),
            content_type="image/png",
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("profile"),
                    {
                        "update_profile_picture": "1",
                        "profile_picture": image,
                    },
                )

                self.assertRedirects(response, reverse("profile"))
                self.user.refresh_from_db()
                self.assertTrue(self.user.profile_picture.name.endswith("profile.png"))

                response = self.client.post(
                    reverse("profile"),
                    {
                        "update_profile_picture": "1",
                        "avatar_choice": "2",
                    },
                )

                self.assertRedirects(response, reverse("profile"))
                self.user.refresh_from_db()
                self.assertFalse(self.user.profile_picture)
                self.assertEqual(self.user.avatar_choice, 2)
