from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from .views import return_create
from .models import Return


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sale",
        "sale_item",
        "return_quantity",
        "return_amount",
        "return_date",
        "return_type",
        "return_status",
        "return_pdf_link",
    )
    list_filter = ("return_type", "return_status", "return_date")
    search_fields = ("sale__id", "sale_item__book__title", "reason")
    list_select_related = ("sale", "sale_item", "sale_item__book", "batch")
    date_hierarchy = "return_date"
    ordering = ("-return_date", "-id")

    @admin.display(description="Return bill")
    def return_pdf_link(self, obj):
        if not obj.batch_id:
            return "-"
        return format_html(
            '<a href="{}">Download PDF</a>',
            reverse("return_report", args=[obj.batch_id]),
        )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "add/",
                self.admin_site.admin_view(self.return_workflow),
                name="retur_return_add",
            ),
        ]
        return custom_urls + urls

    def return_workflow(self, request):
        return return_create(request, template_name="admin/retur/return_form.html")