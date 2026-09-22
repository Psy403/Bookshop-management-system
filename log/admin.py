from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "action",
        "path",
        "status_code",
        "ip_address",
        "details",
    )
    list_filter = ("action", "status_code", "created_at")
    search_fields = ("user__username", "path", "details", "ip_address")
    readonly_fields = (
        "user",
        "action",
        "path",
        "status_code",
        "ip_address",
        "details",
        "created_at",
    )
    date_hierarchy = "created_at"
