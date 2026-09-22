from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from django.contrib import messages
from django.utils import timezone

from log.models import ActivityLog
from .models import ProfileChangeRequest, User, ModulePermission


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {
            "fields": ("role", "profile_picture", "avatar_choice"),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role Info", {
            "fields": ("role",),
        }),
    )

    list_display = (
        "username",
        "email",
        "role",
        "is_active",
    )

    list_filter = ("role",)


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


@admin.register(ProfileChangeRequest)
class ProfileChangeRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "requested_at", "reviewed_by", "reviewed_at")
    list_filter = ("status", "requested_at")
    search_fields = ("user__username", "user__email", "first_name", "last_name")
    readonly_fields = ("requested_at", "reviewed_at", "reviewed_by")
    actions = ("approve_requests", "reject_requests")

    @admin.action(description="Approve selected profile changes")
    def approve_requests(self, request, queryset):
        approved = 0
        for change in queryset.filter(status="PENDING").select_related("user"):
            user = change.user
            user.first_name = change.first_name
            user.last_name = change.last_name
            user.email = change.email
            user.avatar_choice = change.avatar_choice
            if change.profile_picture:
                user.profile_picture.save(
                    change.profile_picture.name.split("/")[-1],
                    change.profile_picture.file,
                    save=False,
                )
            user.save()
            change.status = "APPROVED"
            change.reviewed_by = request.user
            change.reviewed_at = timezone.now()
            change.save(update_fields=("status", "reviewed_by", "reviewed_at"))
            ActivityLog.objects.create(
                user=user,
                action="PROFILE",
                path="/admin/accounts/profilechangerequest/",
                status_code=200,
                details="Your profile change request was approved by an administrator.",
            )
            approved += 1
        self.message_user(request, f"{approved} profile change(s) approved.", messages.SUCCESS)

    @admin.action(description="Reject selected profile changes")
    def reject_requests(self, request, queryset):
        pending_changes = list(queryset.filter(status="PENDING").select_related("user"))
        updated = queryset.filter(status="PENDING").update(
            status="REJECTED",
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        for change in pending_changes:
            ActivityLog.objects.create(
                user=change.user,
                action="PROFILE",
                path="/admin/accounts/profilechangerequest/",
                status_code=200,
                details="Your profile change request was rejected by an administrator.",
            )
        self.message_user(request, f"{updated} profile change(s) rejected.", messages.WARNING)