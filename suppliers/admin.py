from django.contrib import admin

# Register your models here.

from .models import supplier


@admin.register(supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone_number", "country", "is_active")
    list_filter = ("is_active", "country")
    search_fields = ("name", "contact_person", "email", "phone_number", "pan_number")
    ordering = ("name",)
    list_per_page = 25
