from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from books.models import Book, stock
from .models import Sale


@login_required
def sale_list(request):
    sales = Sale.objects.select_related(
        "book"
    ).order_by("-sale_at")

    total_sales = sales.count()

    total_revenue = sum(
        sale.total_price
        for sale in sales
    )

    context = {
        "sales": sales,
        "total_sales": total_sales,
        "total_revenue": total_revenue,
    }

    return render(
        request,
        "sales/sale_list.html",
        context
    )


@login_required
def sale_create(request):

    books = Book.objects.select_related(
        "stock"
    ).order_by("title")

    if request.method == "POST":

        book_id = request.POST.get("book")
        quantity_text = request.POST.get("quantity", "").strip()

        if not book_id or not quantity_text:
            messages.error(
                request,
                "Please select a book and enter quantity."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        try:
            quantity = int(quantity_text)
        except ValueError:
            messages.error(
                request,
                "Quantity must be a valid number."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        if quantity <= 0:
            messages.error(
                request,
                "Quantity must be greater than zero."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        book = get_object_or_404(
            Book,
            id=book_id
        )

        try:
            book_stock = stock.objects.select_for_update().get(
                book=book
            )
        except stock.DoesNotExist:
            messages.error(
                request,
                "Stock record does not exist for this book."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        if book_stock.quantity < quantity:
            messages.error(
                request,
                f"Only {book_stock.quantity} copies are available."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        total_price = book.price * quantity

        with transaction.atomic():

            Sale.objects.create(
                book=book,
                quantity=quantity,
                total_price=total_price
            )

            book_stock.quantity -= quantity
            book_stock.save()

            if book_stock.quantity == 0:
                book.is_available = False
            else:
                book.is_available = True

            book.save(
                update_fields=["is_available"]
            )

        messages.success(
            request,
            "Sale completed successfully. Stock has been updated."
        )

        return redirect("sale_list")

    return render(
        request,
        "sales/sale_form.html",
        {"books": books}
    )