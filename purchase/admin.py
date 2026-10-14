from io import BytesIO

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.urls import path, reverse
from django.utils import timezone
from log.utils import record_activity
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

from .models import Purchase, PurchaseItem


class PurchaseForm(forms.ModelForm):
    order_date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "min": timezone.localdate().isoformat(),
                "max": timezone.localdate().isoformat(),
            }
        ),
    )

    class Meta:
        model = Purchase
        fields = "__all__"

    def clean_order_date(self):
        value = self.cleaned_data["order_date"]
        if value != timezone.localdate():
            raise forms.ValidationError("The order date must be today.")
        return value


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    min_num = 1
    validate_min = True
    fields = ("book", "quantity", "unit_price", "total_price")
    readonly_fields = ("total_price",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    form = PurchaseForm
    inlines = (PurchaseItemInline,)
    list_display = ("id", "supplier", "order_date", "payment_status", "payment_method", "total_cost", "bill_link")
    list_filter = ("payment_status", "payment_method", "order_date", "supplier")
    search_fields = ("supplier__name",)
    date_hierarchy = "order_date"
    ordering = ("-order_date", "-id")
    readonly_fields = ("total_cost",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/bill/",
                self.admin_site.admin_view(self.bill_view),
                name="purchase_purchase_bill",
            )
        ]
        return custom + urls

    @admin.display(description="Bill")
    def bill_link(self, obj):
        return format_html(
            '<a href="{}">PDF</a>',
            reverse("admin:purchase_purchase_bill", args=[obj.pk]),
        )

    def bill_view(self, request, object_id):
        purchase = self.get_object(request, object_id)
        if purchase is None:
            return self._get_obj_does_not_exist_redirect(request, object_id)
        purchase_items = purchase.items.select_related("book")
        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer, pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm
        )
        rows = [
            ["Purchase bill", f"#{purchase.pk}"],
            ["Supplier", purchase.supplier.name],
            ["Order date", purchase.order_date.strftime("%Y-%m-%d")],
            ["Payment", purchase.get_payment_status_display()],
            ["Method", purchase.get_payment_method_display()],
            ["", "", "", ""],
            ["Book", "Quantity", "Unit price", "Total"],
        ]
        rows.extend(
            [
                [item.book.title, item.quantity, str(item.unit_price), str(item.total_price)]
                for item in purchase_items
            ]
        )
        rows.append(["", "", "Total", str(purchase.total_cost)])
        table = Table(rows, colWidths=[90 * mm, 25 * mm, 35 * mm, 35 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 6), (-1, 6), colors.lightgrey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 7), (-1, -1), "RIGHT"),
                ]
            )
        )
        document.build([table])
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="purchase-{purchase.pk}.pdf"'
        return response

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        purchase = form.instance
        items = purchase.items.select_related("book")
        summary = ", ".join(
            f"{item.quantity} {item.book.title}"
            for item in items
        )
        record_activity(
            request,
            f"Purchase order #{purchase.pk} was "
            f'{"updated" if change else "created"} from {purchase.supplier.name}: '
            f"{summary}. Total cost: Rs. {purchase.total_cost}.",
        )

    def delete_model(self, request, obj):
        purchase_id = obj.pk
        super().delete_model(request, obj)
        record_activity(request, f"Purchase order #{purchase_id} was deleted.")
