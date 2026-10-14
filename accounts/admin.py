from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect

from django.contrib import messages
from django.utils import timezone
from django.db import transaction

from log.models import ActivityLog
from .forms import StaffCreationForm
from .models import ContactEmail, ContactNumber, ProfileChangeRequest, User, ModulePermission

admin.site.site_header = "Bookshop Management"
admin.site.site_title = "Bookshop Admin"
admin.site.index_title = "Workspace overview"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = StaffCreationForm
    readonly_fields = ("contact_numbers_display", "contact_emails_display")

    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {
            "fields": (
                "role",
                "middle_name",
                "phone_number",
                "contact_numbers_display",
                "contact_emails_display",
                "hiring_date",
                "profile_picture",
                "avatar_choice",
            ),
        }),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "middle_name",
                    "last_name",
                    "phone_number",
                    "role",
                    "hiring_date",
                    "email",
                    "is_active",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    list_display = (
        "id",
        "username",
        "first_name",
        "middle_name",
        "last_name",
        "phone_number",
        "hiring_date",
        "email",
        "role",
        "is_active",
    )

    list_filter = ("role",)
    search_fields = ("username", "first_name", "middle_name", "last_name", "email", "phone_number")
    ordering = ("first_name", "last_name", "username")
    list_per_page = 20

    @admin.display(description="Contact numbers")
    def contact_numbers_display(self, obj):
        return ", ".join(obj.contact_numbers.values_list("number", flat=True))

    @admin.display(description="Additional email addresses")
    def contact_emails_display(self, obj):
        return ", ".join(obj.contact_emails.values_list("email", flat=True))

    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(request, obj, post_url_continue)
        if response.status_code in (301, 302, 303, 307, 308):
            return redirect("admin:accounts_user_add")
        return response


@admin.register(ContactNumber)
class ContactNumberAdmin(admin.ModelAdmin):
    list_display = ("user", "number")
    search_fields = ("user__username", "number")
    list_select_related = ("user",)


@admin.register(ContactEmail)
class ContactEmailAdmin(admin.ModelAdmin):
    list_display = ("user", "email")
    search_fields = ("user__username", "email")
    list_select_related = ("user",)


@admin.register(ModulePermission)
class ModulePermissionAdmin(admin.ModelAdmin):

    list_display = (
        "role",
        "module_name",
        "can_view",
        "can_add",
        "can_edit",
        "can_delete",
    )

    list_filter = ("role", "module_name")
    search_fields = ("role", "module_name")


@admin.register(ProfileChangeRequest)
class ProfileChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "requested_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "requested_at")
    search_fields = ("user__username", "user__email", "first_name", "last_name")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    exclude = ("password_hash",)
    actions = ("approve_requests", "reject_requests")

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = type(obj).objects.filter(pk=obj.pk).values_list(
                "status", flat=True
            ).first()

        decision = (
            obj.status
            if previous_status == "PENDING" and obj.status in {"APPROVED", "REJECTED"}
            else None
        )
        if obj.status != "PENDING" and decision is None:
            obj.password_hash = ""
        super().save_model(request, obj, form, change)
        if decision == "APPROVED":
            self._approve_profile_change(request, obj)
        elif decision == "REJECTED":
            self._reject_profile_change(request, obj)

    @transaction.atomic
    def _approve_profile_change(self, request, change):
        user = User.objects.select_for_update().get(pk=change.user_id)
        user.username = change.username or user.username
        user.first_name = change.first_name
        user.middle_name = change.middle_name
        user.last_name = change.last_name
        requested_emails = [
            email.strip() for email in change.email.splitlines() if email.strip()
        ]
        user.email = requested_emails[0] if requested_emails else ""
        requested_numbers = [
            number.strip()
            for number in change.contact_numbers.splitlines()
            if number.strip()
        ]
        user.phone_number = requested_numbers[0] if requested_numbers else ""
        if change.password_hash:
            user.password = change.password_hash
        user.save()

        user.contact_emails.all().delete()
        ContactEmail.objects.bulk_create(
            [
                ContactEmail(user=user, email=email)
                for email in requested_emails[1:]
            ]
        )
        user.contact_numbers.all().delete()
        ContactNumber.objects.bulk_create(
            [ContactNumber(user=user, number=number) for number in requested_numbers]
        )
        change.status = "APPROVED"
        change.reviewed_by = request.user
        change.reviewed_at = timezone.now()
        change.password_hash = ""
        change.save(
            update_fields=("status", "reviewed_by", "reviewed_at", "password_hash")
        )
        ActivityLog.objects.create(
            user=user,
            recipient=user,
            details=f"Your profile change request was approved by {request.user.username}.",
        )

    @transaction.atomic
    def _reject_profile_change(self, request, change):
        change.status = "REJECTED"
        change.reviewed_by = request.user
        change.reviewed_at = timezone.now()
        change.password_hash = ""
        change.save(
            update_fields=("status", "reviewed_by", "reviewed_at", "password_hash")
        )
        ActivityLog.objects.create(
            user=change.user,
            recipient=change.user,
            details=f"Your profile change request was rejected by {request.user.username}.",
        )

    @admin.action(description="Approve selected profile changes")
    def approve_requests(self, request, queryset):
        approved = 0
        for change in queryset.filter(status="PENDING"):
            self._approve_profile_change(request, change)
            approved += 1
        self.message_user(request, f"{approved} profile change(s) approved.", messages.SUCCESS)

    @admin.action(description="Reject selected profile changes")
    def reject_requests(self, request, queryset):
        rejected = 0
        for change in queryset.filter(status="PENDING"):
            self._reject_profile_change(request, change)
            rejected += 1
        self.message_user(request, f"{rejected} profile change(s) rejected.", messages.WARNING)