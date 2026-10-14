from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "user",
        "details",
    )
    list_filter = ("created_at",)
    search_fields = ("user__username", "details")
    readonly_fields = (
        "user",
        "details",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
