from django.contrib.auth import get_user_model
from django.contrib import admin
from django.test import Client, TestCase
from django.urls import reverse
from django.test import RequestFactory

from accounts.context_processors import account_header
from .models import ActivityLog, ActivityLogRead


class ActivityReadTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff",
            password="staff-password",
        )
        self.activity = ActivityLog.objects.create(
            user=self.user,
            details="Test activity",
        )

    def test_mark_activity_read_accepts_valid_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.get(reverse("dashboard"))
        token = response.cookies["csrftoken"].value

        response = client.post(
            reverse("mark_activity_read", args=(self.activity.pk,)),
            {"next": reverse("dashboard")},
            HTTP_X_CSRFTOKEN=token,
        )

        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(
            ActivityLogRead.objects.filter(
                user=self.user,
                activity=self.activity,
            ).exists()
        )


class ActivityLogAdminPermissionsTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            password="admin-password",
        )
        self.client.force_login(self.admin_user)
        self.model_admin = admin.site._registry[ActivityLog]

    def test_activity_logs_are_view_only_in_admin(self):
        self.assertFalse(self.model_admin.has_add_permission(self.admin_user))
        self.assertFalse(self.model_admin.has_change_permission(self.admin_user))
        self.assertFalse(self.model_admin.has_delete_permission(self.admin_user))

    def test_activity_log_contains_only_event_fields(self):
        field_names = {field.name for field in ActivityLog._meta.fields}
        self.assertEqual(
            field_names,
            {"id", "user", "recipient", "details", "created_at"},
        )

    def test_notification_feed_excludes_notifications_for_other_recipients(self):
        other_user = get_user_model().objects.create_user(
            username="other-staff",
            password="some-valid-password-948",
        )
        private_activity = ActivityLog.objects.create(
            user=other_user,
            recipient=other_user,
            details="Private profile decision",
        )
        request = RequestFactory().get("/")
        request.user = self.admin_user

        context = account_header(request)

        self.assertNotIn(private_activity, context["recent_notifications"])

    def test_activity_log_add_url_is_not_available(self):
        response = self.client.get("/admin/log/activitylog/add/")

        self.assertEqual(response.status_code, 403)
