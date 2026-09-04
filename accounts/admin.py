from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, ModulePermission


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
        ("Role Info", {
            "fields": ("role",),
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