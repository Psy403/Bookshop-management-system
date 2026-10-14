from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from books.models import Book, stock
from suppliers.models import supplier

from .models import Sale, SaleItem


class SaleAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="sales-admin",
            email="sales-admin@example.com",
            password="strong-password-123",
        )
        self.supplier = supplier.objects.create(
            name="Sales Supplier",
            email="supplier@example.com",
            phone_number="9800000000",
            address="Supplier address",
        )
        self.books = [
            Book.objects.create(
                title="Book One",
                author="Author",
                publication_year=2026,
                price="15.00",
                supplier=self.supplier,
            ),
            Book.objects.create(
                title="Book Two",
                author="Author",
                publication_year=2026,
                price="20.00",
                supplier=self.supplier,
            ),
        ]
        for book in self.books:
            stock.objects.create(book=book, quantity=20)
        self.client.force_login(self.admin)

    def test_sale_admin_accepts_multiple_books_and_calculates_total(self):
        response = self.client.post(
            reverse("admin:sales_sale_add"),
            {
                "total_price": "0.00",
                "items-TOTAL_FORMS": "2",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "1",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-book": self.books[0].pk,
                "items-0-quantity": "2",
                "items-0-unit_price": "12.50",
                "items-1-book": self.books[1].pk,
                "items-1-quantity": "3",
                "items-1-unit_price": "8.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        sale = Sale.objects.get()
        self.assertEqual(sale.quantity, 5)
        self.assertEqual(sale.total_price, Decimal("49.00"))
        self.assertEqual(sale.items.count(), 2)

    def test_sale_item_calculates_line_total(self):
        sale = Sale.objects.create(book=self.books[0], quantity=0)
        item = SaleItem.objects.create(
            sale=sale,
            book=self.books[0],
            quantity=4,
            unit_price="7.25",
            total_price="0.00",
        )

        self.assertEqual(item.total_price, Decimal("29.00"))
        sale.refresh_from_db()
        self.assertEqual(sale.total_price, Decimal("29.00"))

    def test_sale_admin_shows_per_book_quantities_and_pdf_download(self):
        sale = Sale.objects.create(book=self.books[0], quantity=0)
        SaleItem.objects.create(
            sale=sale,
            book=self.books[0],
            quantity=2,
            unit_price="15.00",
            total_price="0.00",
        )
        SaleItem.objects.create(
            sale=sale,
            book=self.books[1],
            quantity=3,
            unit_price="20.00",
            total_price="0.00",
        )

        response = self.client.get(reverse("admin:sales_sale_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Book One: 2")
        self.assertContains(response, "Book Two: 3")
        self.assertContains(
            response,
            reverse("sale_report", args=[sale.pk]),
        )

        bill_response = self.client.get(reverse("sale_report", args=[sale.pk]))
        self.assertEqual(bill_response.status_code, 200)
        self.assertEqual(bill_response["Content-Type"], "application/pdf")
        self.assertIn(f"sale-report-{sale.pk}.pdf", bill_response["Content-Disposition"])

# Create your tests here.
