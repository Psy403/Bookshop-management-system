from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from xml.sax.saxutils import escape

from books.models import Book, stock
from log.utils import record_activity
from .models import Sale, SaleItem


@login_required
def sale_list(request):
    sales = Sale.objects.prefetch_related("items__book", "items__returns").select_related(
        "book"
    ).order_by("-sale_at")
    sales = list(sales)
    for sale in sales:
        sale.display_items = list(sale.items.all())
        if not sale.display_items:
            sale.display_items = [sale]
        if sale.items.exists():
            sale.returned_quantity = sum(
                (return_item.return_quantity or item.quantity)
                for item in sale.display_items
                for return_item in item.returns.all()
            )
            sale.remaining_quantity = sum(
                item.quantity for item in sale.display_items
            ) - sale.returned_quantity
        else:
            sale.returned_quantity = 0
            sale.remaining_quantity = sale.quantity

    total_sales = len(sales)

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

        book_ids = request.POST.getlist("book")
        quantity_texts = request.POST.getlist("quantity")

        if not book_ids or len(book_ids) != len(quantity_texts):
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
            requested_items = {}
            for book_id, quantity_text in zip(book_ids, quantity_texts):
                quantity = int(quantity_text)
                if quantity <= 0:
                    raise ValueError
                requested_items[int(book_id)] = requested_items.get(int(book_id), 0) + quantity
        except (TypeError, ValueError):
            messages.error(
                request,
                "Quantity must be a valid number."
            )

            return render(
                request,
                "sales/sale_form.html",
                {"books": books}
            )

        with transaction.atomic():
            selected_books = list(
                Book.objects.select_for_update().filter(id__in=requested_items)
            )
            if len(selected_books) != len(requested_items):
                messages.error(request, "One or more selected books are invalid.")
                return render(request, "sales/sale_form.html", {"books": books})

            line_items = []
            total_price = Decimal("0")
            for book in selected_books:
                quantity = requested_items[book.id]
                book_stock = stock.objects.select_for_update().get(book=book)
                if book_stock.quantity < quantity:
                    messages.error(request, f"Only {book_stock.quantity} copies of {book.title} are available.")
                    return render(request, "sales/sale_form.html", {"books": books})
                line_total = book.price * quantity
                line_items.append((book, quantity, line_total))
                total_price += line_total

            first_book, first_quantity, _ = line_items[0]
            sale = Sale.objects.create(
                book=first_book,
                quantity=sum(item[1] for item in line_items),
                total_price=total_price
            )
            for book, quantity, line_total in line_items:
                SaleItem.objects.create(
                    sale=sale,
                    book=book,
                    quantity=quantity,
                    unit_price=book.price,
                    total_price=line_total,
                )
                book_stock = stock.objects.get(book=book)
                book_stock.quantity -= quantity
                book_stock.save(update_fields=["quantity"])
                book.is_available = book_stock.quantity > 0
                book.save(update_fields=["is_available"])

        record_activity(
            request,
            f"{len(line_items)} book type(s) sold, total quantity "
            f"{sum(item[1] for item in line_items)}, total Rs. {total_price}.",
            action="SALE",
        )
        messages.success(
            request,
            "Sale completed successfully. Stock has been updated."
        )

        return redirect("sale_report", sale_id=sale.id)

    return render(
        request,
        "sales/sale_form.html",
        {"books": books}
    )


@login_required
def sale_report(request, sale_id):
    sale = get_object_or_404(
        Sale.objects.prefetch_related("items__book"),
        id=sale_id,
    )
    generated_at = timezone.localtime(sale.sale_at)
    items = list(sale.items.all())
    if not items:
        items = [sale]

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="sale-report-{sale.id}.pdf"'
    )

    document = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            alignment=1,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ThankYou",
            parent=styles["Normal"],
            alignment=1,
            fontSize=10,
            textColor=colors.HexColor("#475569"),
            spaceBefore=18,
        )
    )

    report_data = [
        ["Date", generated_at.strftime("%B %d, %Y")],
        ["Time", generated_at.strftime("%I:%M:%S %p")],
        ["Store", getattr(settings, "BOOKSHOP_NAME", "Book Shop Management")],
    ]
    items_data = [
        [
            "S.N.",
            "Books",
            "Quantity",
            "Per Unit Price",
            "Books Price",
            "Total Price",
        ],
    ]
    for index, item in enumerate(items, start=1):
        book = item.book
        quantity = item.quantity
        unit_price = item.unit_price if hasattr(item, "unit_price") else book.price
        line_total = item.total_price
        items_data.append([
            str(index),
            escape(book.title),
            str(quantity),
            f"Rs. {unit_price:.2f}",
            f"Rs. {line_total:.2f}",
            f"Rs. {line_total:.2f}",
        ])

    story = [
        Paragraph(
            getattr(settings, "BOOKSHOP_NAME", "Book Shop Management"),
            styles["ReportTitle"],
        ),
        Paragraph("Sales Report", styles["Heading2"]),
        Spacer(1, 6),
    ]
    metadata_table = Table(report_data, colWidths=[35 * mm, 125 * mm])
    metadata_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#334155")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([metadata_table, Spacer(1, 14)])

    items_table = Table(
        items_data,
        colWidths=[14 * mm, 48 * mm, 22 * mm, 30 * mm, 30 * mm, 30 * mm],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#334155")),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            items_table,
            Paragraph(
                "Thank you for shopping with us. We look forward to serving you again!",
                styles["ThankYou"],
            ),
        ]
    )
    document.build(story)
    return response