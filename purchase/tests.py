from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from books.models import Book, stock
from suppliers.models import supplier

from .admin import PurchaseForm
from .models import Purchase, PurchaseItem


class PurchaseTests(TestCase):
    def setUp(self):
        self.supplier = supplier.objects.create(
            name="Acme", email="acme@example.com", phone_number="123", address="Kathmandu"
        )
        self.book = Book.objects.create(
            title="A book", author="An author", price="20.00", supplier=self.supplier
        )
        self.other_book = Book.objects.create(
            title="Another book", author="An author", price="30.00", supplier=self.supplier
        )

    def test_items_calculate_line_and_order_totals(self):
        purchase = Purchase.objects.create(supplier=self.supplier, order_date=date.today())
        first = PurchaseItem.objects.create(
            purchase=purchase, book=self.book, quantity=3, unit_price="4.50"
        )
        PurchaseItem.objects.create(
            purchase=purchase, book=self.other_book, quantity=2, unit_price="10.00"
        )
        purchase.refresh_from_db()
        self.assertEqual(first.total_price, Decimal("13.50"))
        self.assertEqual(purchase.total_cost, Decimal("33.50"))

    def test_admin_form_only_accepts_today(self):
        data = {
            "supplier": self.supplier.pk,
            "order_date": date.today() - timedelta(days=1),
            "payment_status": Purchase.PAYMENT_PENDING,
            "payment_method": Purchase.METHOD_CASH,
            "total_cost": "0.00",
        }
        self.assertFalse(PurchaseForm(data).is_valid())

    def test_admin_bill_is_pdf(self):
        user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="password"
        )
        purchase = Purchase.objects.create(supplier=self.supplier, order_date=date.today())
        PurchaseItem.objects.create(
            purchase=purchase, book=self.book, quantity=1, unit_price="4.50"
        )
        self.client.force_login(user)
        response = self.client.get(
            reverse("admin:purchase_purchase_bill", args=[purchase.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_admin_can_receive_stock_from_purchase(self):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            order_date=date.today(),
        )
        item = PurchaseItem.objects.create(
            purchase=purchase,
            book=self.book,
            quantity=10,
            unit_price="4.50",
        )
        user = get_user_model().objects.create_superuser(
            username="stock-admin",
            email="stock-admin@example.com",
            password="strong-password-123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("admin:books_stock_receive_from_purchase"),
            {"purchase_id": purchase.pk, "receive_stock": "Receive selected stock", f"receive_{item.pk}": "6"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(stock.objects.get(book=self.book).quantity, 6)
        item.refresh_from_db()
        self.assertEqual(item.received_quantity, 6)

    def test_admin_cannot_receive_more_than_purchase_quantity(self):
        purchase = Purchase.objects.create(
            supplier=self.supplier,
            order_date=date.today(),
        )
        item = PurchaseItem.objects.create(
            purchase=purchase,
            book=self.book,
            quantity=4,
            unit_price="4.50",
        )
        user = get_user_model().objects.create_superuser(
            username="stock-limit-admin",
            email="stock-limit@example.com",
            password="strong-password-123",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("admin:books_stock_receive_from_purchase"),
            {"purchase_id": purchase.pk, "receive_stock": "Receive selected stock", f"receive_{item.pk}": "5"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must be between 0 and 4")
