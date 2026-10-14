from django.contrib import admin
from django import forms
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from log.utils import record_activity
from purchase.models import Purchase, PurchaseItem

# Register your models here.
from .models import Book, book_category, stock


class BookAdminForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = "__all__"
        labels = {"price": "Selling price"}


@admin.register(book_category)
class BookCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    form = BookAdminForm
    list_display = ("title", "author", "book_category", "price", "stock_level", "is_available")
    list_filter = ("book_category", "is_available", "language")
    search_fields = ("title", "author", "isbn", "supplier__name")
    list_select_related = ("book_category", "supplier", "stock")
    ordering = ("title",)
    list_per_page = 25
    exclude = ("stock_quantity", "is_available")

    @admin.display(description="Stock", ordering="stock__quantity")
    def stock_level(self, obj):
        return obj.stock.quantity if hasattr(obj, "stock") else 0

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            stock(book=obj, quantity=0).save(request=request)
        record_activity(
            request,
            f'Book "{obj.title}" was {"updated" if change else "added"} '
            f"to the catalogue.",
        )

    def delete_model(self, request, obj):
        title = obj.title
        super().delete_model(request, obj)
        record_activity(request, f'Book "{title}" was removed from the catalogue.')


@admin.register(stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("book", "quantity", "stock_status", "receive_stock_link", "remove_stock_link")
    list_filter = ("quantity",)
    search_fields = ("book__title", "book__author")
    list_select_related = ("book",)
    ordering = ("quantity", "book__title")
    fields = ("book", "quantity")
    readonly_fields = ("book", "quantity")

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "add/",
                self.admin_site.admin_view(self.receive_stock_view),
                name="books_stock_add",
            ),
            path(
                "receive-from-purchase/",
                self.admin_site.admin_view(self.receive_stock_view),
                name="books_stock_receive_from_purchase",
            ),
            path(
                "<path:object_id>/remove-stock/",
                self.admin_site.admin_view(self.remove_stock_view),
                name="books_stock_remove_stock",
            ),
        ]
        return custom_urls + urls

    @admin.display(description="Receive from purchase")
    def receive_stock_link(self, obj):
        return format_html(
            '<a href="{}?purchase_id=">Receive</a>',
            reverse("admin:books_stock_receive_from_purchase"),
        )

    def receive_stock_view(self, request):
        purchase_id = request.POST.get("purchase_id", request.GET.get("purchase_id", "")).strip()
        purchase = None
        items = []
        if purchase_id.isdigit():
            purchase = get_object_or_404(Purchase, pk=purchase_id)
            items = list(purchase.items.select_related("book").order_by("book__title"))
            for item in items:
                item.remaining_quantity = item.quantity - item.received_quantity

        context = {"purchase": purchase, "items": items, "purchase_id": purchase_id}
        if request.method == "POST" and request.POST.get("receive_stock"):
            received_items = []
            try:
                with transaction.atomic():
                    locked_items = list(
                        PurchaseItem.objects.select_for_update()
                        .select_related("book")
                        .filter(purchase_id=purchase_id)
                    )
                    requested_receipts = []
                    for item in locked_items:
                        amount = int(
                            request.POST.get(f"receive_{item.pk}", "0") or 0
                        )
                        remaining = item.quantity - item.received_quantity
                        if amount < 0 or amount > remaining:
                            raise ValueError(
                                f"Receive quantity for {item.book.title} must be "
                                f"between 0 and {remaining}."
                            )
                        requested_receipts.append((item, amount))

                    for item, amount in requested_receipts:
                        if amount:
                            book_stock = (
                                stock.objects.select_for_update()
                                .filter(book=item.book)
                                .first()
                            )
                            if book_stock is None:
                                book_stock = stock(book=item.book, quantity=amount)
                                book_stock.save(request=request)
                            else:
                                book_stock.quantity += amount
                                book_stock.save(
                                    update_fields=["quantity"],
                                    request=request,
                                )
                            item.received_quantity += amount
                            item.save(update_fields=["received_quantity"])
                            item.book.is_available = True
                            item.book.save(update_fields=["is_available"])
                            received_items.append((amount, item.book.title))
            except (TypeError, ValueError) as error:
                self.message_user(request, str(error), level="error")
                return render(request, "admin/books/receive_stock.html", context)

            if received_items:
                summary = ", ".join(
                    f"{amount} {title}" for amount, title in received_items
                )
                record_activity(
                    request,
                    f"Stock received from purchase order #{purchase_id}: {summary}.",
                )
                self.message_user(request, "Stock received successfully.")
            else:
                self.message_user(
                    request,
                    "No stock quantity was entered.",
                    level="warning",
                )
            return redirect("admin:books_stock_receive_from_purchase")

        return render(request, "admin/books/receive_stock.html", context)

    @admin.display(description="Remove stock")
    def remove_stock_link(self, obj):
        return format_html(
            '<a href="{}" title="Remove stock" aria-label="Remove stock">🗑</a>',
            reverse("admin:books_stock_remove_stock", args=[obj.pk]),
        )

    def remove_stock_view(self, request, object_id):
        stock_record = get_object_or_404(
            stock.objects.select_related("book"), pk=object_id
        )
        if request.method == "POST":
            try:
                amount = int(request.POST.get("quantity", "0"))
            except (TypeError, ValueError):
                amount = 0
            if amount < 1 or amount > stock_record.quantity:
                return render(
                    request,
                    "admin/books/remove_stock.html",
                    {
                        "stock_record": stock_record,
                        "error": (
                            f"Enter a quantity between 1 and "
                            f"{stock_record.quantity}."
                        ),
                    },
                )
            stock_record.quantity -= amount
            stock_record.save(update_fields=["quantity"], request=request)
            record_activity(
                request,
                f"{amount} copies of {stock_record.book.title} were deleted "
                f"from stock; {stock_record.quantity} remain.",
            )
            self.message_user(request, "Stock quantity removed successfully.")
            return redirect("admin:books_stock_changelist")
        return render(
            request,
            "admin/books/remove_stock.html",
            {"stock_record": stock_record},
        )

    @admin.display(description="Status")
    def stock_status(self, obj):
        return "Low stock" if obj.quantity < 20 else "Healthy"
