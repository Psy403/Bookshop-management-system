from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.
from django import forms
from log.utils import record_activity

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    min_num = 1
    validate_min = True
    fields = ("book", "quantity", "unit_price", "total_price")
    readonly_fields = ("total_price",)


class SaleAdminForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ("total_price",)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    form = SaleAdminForm
    inlines = (SaleItemInline,)
    list_display = (
        "id",
        "book_summary",
        "quantity_summary",
        "total_price",
        "sale_at",
        "bill_pdf_link",
    )
    list_filter = ("sale_at",)
    search_fields = ("book__title", "items__book__title")
    list_select_related = ("book",)
    date_hierarchy = "sale_at"
    ordering = ("-sale_at",)
    readonly_fields = ("total_price",)

    class Media:
        js = ("sales/admin-sale.js",)

    @admin.display(description="Book")
    def book_summary(self, obj):
        items = list(obj.items.all())
        titles = [item.book.title for item in items]
        return ", ".join(titles) or (obj.book.title if obj.book_id else "-")

    @admin.display(description="Book quantities")
    def quantity_summary(self, obj):
        items = list(obj.items.all())
        if items:
            return ", ".join(
                f"{item.book.title}: {item.quantity}" for item in items
            )
        return obj.quantity

    @admin.display(description="Sale bill")
    def bill_pdf_link(self, obj):
        return format_html(
            '<a href="{}">Download PDF</a>',
            reverse("sale_report", args=[obj.pk]),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items__book")

    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)
        first_book_id = request.POST.get("items-0-book")
        if first_book_id:
            obj.book_id = first_book_id
        return obj

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        sale = form.instance
        sale.recalculate_total()
        items = sale.items.select_related("book")
        summary = ", ".join(
            f"{item.quantity} {item.book.title}"
            for item in items
        )
        record_activity(
            request,
            f"Sale #{sale.pk} was {'updated' if change else 'created'}: "
            f"{summary}. Total sale value: Rs. {sale.total_price}.",
        )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ("sale", "book", "quantity", "unit_price", "total_price")
    search_fields = ("sale__id", "book__title")
    list_select_related = ("sale", "book")
    ordering = ("-sale__sale_at", "book__title")