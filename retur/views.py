from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from xml.sax.saxutils import escape

from books.models import stock
from log.utils import record_activity
from sales.models import Sale, SaleItem
from .models import Return, ReturnBatch


@login_required
def return_list(request):
    returns = Return.objects.select_related(
        "sale", "sale__book", "sale_item", "sale_item__book", "batch"
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
    bill_id = request.POST.get("bill_id", request.GET.get("bill_id", "")).strip()
    sale = None
    return_items = []
    if bill_id.isdigit():
        sale = Sale.objects.prefetch_related("items__book", "items__returns").filter(
            id=int(bill_id)
        ).first()
        if sale:
            for item in sale.items.all():
                returned = sum(r.return_quantity or item.quantity for r in item.returns.all())
                item.remaining_quantity = max(item.quantity - returned, 0)
                if item.remaining_quantity:
                    return_items.append(item)
            if not sale.items.exists():
                returned = sum(r.return_quantity or sale.quantity for r in sale.returns.all())
                sale.remaining_quantity = max(sale.quantity - returned, 0)
                sale.unit_price = sale.total_price / sale.quantity
                if sale.remaining_quantity:
                    return_items.append(sale)

    if request.method == "POST" and request.POST.get("submit_return"):
        return_item_ids = request.POST.getlist("return_item")
        return_date = request.POST.get("return_date", "").strip()
        return_type = request.POST.get("return_type", "").strip()
        reason = request.POST.get("reason", "").strip()
        return_status = request.POST.get("return_status", "").strip()

        context = {
            "bill_id": bill_id,
            "sale": sale,
            "return_items": return_items,
            "return_date": return_date,
            "return_type": return_type,
            "reason": reason,
            "return_status": return_status,
        }

        if not all([sale, return_item_ids, return_date, return_type, reason, return_status]):
            messages.error(request, "All return fields are required.")
            return render(request, "books/return_form.html", context)

        try:
            parsed_date = date.fromisoformat(return_date)
        except (TypeError, ValueError):
            messages.error(request, "Select a valid sale, quantity, and date.")
            return render(request, "books/return_form.html", context)

        try:
            with transaction.atomic():
                sale = Sale.objects.select_for_update().prefetch_related(
                    "items__returns"
                ).get(id=sale.id)
                sale_date = timezone.localtime(sale.sale_at).date()

                if parsed_date != sale_date:
                    messages.error(
                        request,
                        f"The return date must be {sale_date.strftime('%B %d, %Y')}, "
                        "the same date as the sale.",
                    )
                    return render(request, "books/return_form.html", context)

                batch = ReturnBatch.objects.create(sale=sale, return_date=parsed_date)
                total_amount = Decimal("0")
                selected = {str(item.id): item for item in sale.items.all()}
                if not selected:
                    selected = {str(sale.id): sale}
                for item_id in return_item_ids:
                    item = selected.get(item_id)
                    quantity_text = request.POST.get(f"quantity_{item_id}", "").strip()
                    quantity = int(quantity_text)
                    returned = sum(r.return_quantity or item.quantity for r in item.returns.all())
                    remaining = item.quantity - returned
                    if quantity <= 0 or quantity > remaining:
                        raise ValueError("Return quantity exceeds the remaining quantity.")
                    book = item.book
                    unit_price = getattr(item, "unit_price", sale.total_price / sale.quantity)
                    amount = unit_price * quantity
                    book_stock = stock.objects.select_for_update().get(book=book)
                    Return.objects.create(
                        batch=batch, sale=None if hasattr(item, "sale") else sale,
                        sale_item=item if hasattr(item, "sale") else None,
                        return_quantity=quantity, return_date=parsed_date,
                        return_amount=amount, return_type=return_type,
                        reason=reason, return_status=return_status,
                    )
                    book_stock.quantity += quantity
                    book_stock.save(update_fields=["quantity"])
                    book.is_available = True
                    book.save(update_fields=["is_available"])
                    total_amount += amount
                batch.total_amount = total_amount
                batch.save(update_fields=["total_amount"])
        except stock.DoesNotExist:
            messages.error(request, "Stock record does not exist for one of the selected books.")
            return render(request, "books/return_form.html", context)
        except ValueError as error:
            messages.error(request, str(error))
            return render(request, "books/return_form.html", context)

        messages.success(request, "Return recorded and stock has been restocked.")
        record_activity(
            request,
            f"Return recorded for bill {sale.id}, refund amount Rs. {batch.total_amount}.",
            action="RETURN",
        )
        return redirect("return_report", batch_id=batch.id)

    return render(request, "books/return_form.html", {
        "bill_id": bill_id, "sale": sale, "return_items": return_items,
    })


@login_required
def return_report(request, batch_id):
    batch = get_object_or_404(ReturnBatch.objects.select_related("sale"), id=batch_id)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="return-report-{batch.id}.pdf"'
    document = SimpleDocTemplate(response, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm)
    styles = getSampleStyleSheet()
    data = [["Return ID", str(batch.id)], ["Bill ID", str(batch.sale_id)],
            ["Date", batch.return_date.strftime("%B %d, %Y")],
            ["Store", getattr(settings, "BOOKSHOP_NAME", "Book Shop Management")]]
    rows = [["S.N.", "Books", "Quantity", "Per Unit Price", "Return Amount"]]
    for index, item in enumerate(batch.items.select_related("sale_item__book", "sale__book"), 1):
        source = item.sale_item or item.sale
        rows.append([str(index), escape(source.book.title), str(item.return_quantity),
                     f"Rs. {item.return_amount / item.return_quantity:.2f}",
                     f"Rs. {item.return_amount:.2f}"])
    story = [Paragraph(getattr(settings, "BOOKSHOP_NAME", "Book Shop Management"), styles["Title"]),
             Paragraph("Return Report", styles["Heading2"]), Table(data, colWidths=[35*mm, 125*mm]),
             Spacer(1, 8), Table(rows)]
    story[-1].setStyle(TableStyle([("GRID", (0,0), (-1,-1), .5, colors.grey),
                                   ("BACKGROUND", (0,0), (-1,0), colors.lightgrey)]))
    story.append(Paragraph("Thank you for shopping with us.", styles["Normal"]))
    document.build(story)
    return response
