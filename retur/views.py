from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from books.models import stock
from log.utils import record_activity
from sales.models import Sale, SaleItem
from .models import Return


@login_required
def return_list(request):
    returns = Return.objects.select_related(
        "sale", "sale__book", "sale_item", "sale_item__book"
    ).all().order_by(
        "-return_date",
        "-id",
    )
    for item in returns:
        item.display_quantity = item.return_quantity or (
            item.sale_item.quantity if item.sale_item else item.sale.quantity
            if item.sale else 0
        )

    context = {
        "returns": returns,
        "total_returns": returns.count(),
        "total_return_amount": sum(item.return_amount for item in returns),
    }

    return render(request, "books/return_list.html", context)


@login_required
def return_create(request):
    sales = list(Sale.objects.prefetch_related("items__book", "items__returns")
                 .select_related("book").order_by("-sale_at"))
    eligible_sales = []
    for sale in sales:
        sale.returned_quantity = sum(
            item.return_quantity
            if item.return_quantity is not None
            else sale.quantity
            for item in sale.returns.all()
        ) if not sale.items.exists() else 0
        if not sale.items.exists() and sale.quantity > sale.returned_quantity:
            sale.remaining_quantity = sale.quantity - sale.returned_quantity
            sale.unit_price = sale.total_price / sale.quantity
            sale.sale_date = timezone.localtime(sale.sale_at).date()
            sale.is_legacy = True
            eligible_sales.append(sale)
        for sale_item in sale.items.all():
            sale_item.returned_quantity = sum(
                item.return_quantity or sale_item.quantity
                for item in sale_item.returns.all()
            )
            sale_item.remaining_quantity = sale_item.quantity - sale_item.returned_quantity
            if sale_item.remaining_quantity > 0:
                sale_item.unit_price = sale_item.unit_price
                sale_item.sale_date = timezone.localtime(sale.sale_at).date()
                eligible_sales.append(sale_item)

    if request.method == "POST":
        sale_item_id = request.POST.get("sale_item", "").strip()
        sale_id = request.POST.get("sale", "").strip()
        return_quantity = request.POST.get("return_quantity", "").strip()
        return_date = request.POST.get("return_date", "").strip()
        return_type = request.POST.get("return_type", "").strip()
        reason = request.POST.get("reason", "").strip()
        return_status = request.POST.get("return_status", "").strip()

        context = {
            "sales": sales,
            "eligible_sales": eligible_sales,
            "sale_id": sale_id,
            "return_quantity": return_quantity,
            "return_date": return_date,
            "return_type": return_type,
            "reason": reason,
            "return_status": return_status,
        }

        if not all(
            [sale_item_id or sale_id, return_quantity, return_date, return_type, reason, return_status]
        ):
            messages.error(request, "All return fields are required.")
            return render(request, "books/return_form.html", context)

        try:
            sale_item = SaleItem.objects.select_related("sale", "book").get(
                id=sale_item_id
            ) if sale_item_id else None
            sale = sale_item.sale if sale_item else Sale.objects.get(id=sale_id)
            parsed_quantity = int(return_quantity)
            parsed_date = date.fromisoformat(return_date)
        except (Sale.DoesNotExist, TypeError, ValueError):
            messages.error(request, "Select a valid sale, quantity, and date.")
            return render(request, "books/return_form.html", context)

        try:
            with transaction.atomic():
                if sale_item:
                    sale_item = SaleItem.objects.select_for_update().select_related(
                        "sale", "book"
                    ).get(id=sale_item.id)
                    sale = Sale.objects.select_for_update().get(id=sale_item.sale_id)
                    book = sale_item.book
                    original_quantity = sale_item.quantity
                else:
                    sale = Sale.objects.select_for_update().select_related("book").get(
                        id=sale.id
                    )
                    book = sale.book
                    original_quantity = sale.quantity
                sale_date = timezone.localtime(sale.sale_at).date()

                if parsed_date != sale_date:
                    messages.error(
                        request,
                        f"The return date must be {sale_date.strftime('%B %d, %Y')}, "
                        "the same date as the sale.",
                    )
                    return render(request, "books/return_form.html", context)

                returned_quantity = sum(
                    item.return_quantity
                    if item.return_quantity is not None
                    else original_quantity
                    for item in (
                        Return.objects.filter(sale_item=sale_item)
                        if sale_item
                        else Return.objects.filter(sale=sale)
                    )
                )
                remaining_quantity = original_quantity - returned_quantity
                if parsed_quantity <= 0 or parsed_quantity > remaining_quantity:
                    messages.error(
                        request,
                        f"Only {remaining_quantity} item(s) remain available for return.",
                    )
                    return render(request, "books/return_form.html", context)

                book_stock = stock.objects.select_for_update().get(book=book)
                unit_price = sale_item.unit_price if sale_item else sale.total_price / sale.quantity
                parsed_amount = unit_price * parsed_quantity
                Return.objects.create(
                    sale=sale if not sale_item else None,
                    sale_item=sale_item,
                    return_quantity=parsed_quantity,
                    return_date=parsed_date,
                    return_amount=parsed_amount,
                    return_type=return_type,
                    reason=reason,
                    return_status=return_status,
                )
                book_stock.quantity += parsed_quantity
                book_stock.save(update_fields=["quantity"])
                book.is_available = True
                book.save(update_fields=["is_available"])
        except stock.DoesNotExist:
            messages.error(request, "Stock record does not exist for this book.")
            return render(request, "books/return_form.html", context)

        messages.success(request, "Return recorded and stock has been restocked.")
        record_activity(
            request,
            f'Book "{book.title}" returned, quantity {parsed_quantity}, '
            f"refund amount Rs. {parsed_amount}. Stock was restocked.",
            action="RETURN",
        )
        return redirect("return_list")

    return render(request, "books/return_form.html", {"eligible_sales": eligible_sales})
