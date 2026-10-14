from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from books.models import Book, stock
from sales.models import Sale, SaleItem
from suppliers.models import supplier

from .models import Return, ReturnBatch


class ReturnTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="staff",
            password="staff-password",
        )
        self.client.force_login(self.user)
        self.supplier = supplier.objects.create(
            name="Test Supplier",
            email="supplier@example.com",
            phone_number="9800000000",
            address="Test address",
        )
        self.book = Book.objects.create(
            title="Returned Book",
            author="Test Author",
            publication_year=2026,
            price="25.00",
            supplier=self.supplier,
        )
        self.stock = stock.objects.create(book=self.book, quantity=5)

        self.sale = Sale.objects.create(
            book=self.book,
            quantity=2,
            total_price="50.00",
        )
        self.sale_item = SaleItem.objects.create(
            sale=self.sale,
            book=self.book,
            quantity=2,
            unit_price="25.00",
            total_price="50.00",
        )

    def test_admin_add_return_renders_native_admin_workflow(self):
        admin_user = get_user_model().objects.create_superuser(
            username="returns-admin",
            email="returns-admin@example.com",
            password="strong-password-123",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:retur_return_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Record Return")
        self.assertContains(response, "Find Bill")

    def test_admin_can_edit_and_delete_return_records(self):
        admin_user = get_user_model().objects.create_superuser(
            username="returns-editor",
            email="returns-editor@example.com",
            password="strong-password-123",
        )
        return_record = Return.objects.create(
            sale=self.sale,
            sale_item=self.sale_item,
            return_quantity=1,
            return_date=timezone.localtime(self.sale.sale_at).date(),
            return_amount="25.00",
            return_type="Refund",
            reason="Damaged copy",
            return_status="Completed",
        )
        model_admin = __import__("django.contrib.admin", fromlist=["site"]).site._registry[
            Return
        ]
        request = RequestFactory().get("/")
        request.user = admin_user

        self.assertTrue(model_admin.has_change_permission(request, return_record))
        self.assertTrue(model_admin.has_delete_permission(request, return_record))

    def test_admin_return_list_includes_pdf_download(self):
        admin_user = get_user_model().objects.create_superuser(
            username="returns-pdf-admin",
            email="returns-pdf-admin@example.com",
            password="test-password",
        )
        batch = ReturnBatch.objects.create(
            sale=self.sale,
            return_date=timezone.localtime(self.sale.sale_at).date(),
            total_amount="25.00",
        )
        Return.objects.create(
            batch=batch,
            sale_item=self.sale_item,
            return_quantity=1,
            return_date=batch.return_date,
            return_amount="25.00",
            return_type="Refund",
            reason="Damaged copy",
            return_status="Completed",
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse("admin:retur_return_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Download PDF")
        self.assertContains(response, reverse("return_report", args=[batch.pk]))

        pdf_response = self.client.get(reverse("return_report", args=[batch.pk]))
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")

    def test_return_decreases_sale_amount_by_exact_refund(self):
        response = self.client.post(
            reverse("return_create"),
            {
                "bill_id": self.sale.id,
                "return_item": [self.sale_item.id],
                f"quantity_{self.sale_item.id}": "1",
                "return_date": timezone.localtime(self.sale.sale_at).date().isoformat(),
                "return_type": "Refund",
                "reason": "Damaged copy",
                "return_status": "Completed",
                "submit_return": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.sale.refresh_from_db()
        self.sale_item.refresh_from_db()
        self.stock.refresh_from_db()
        self.assertEqual(self.sale.total_price, 25)
        self.assertEqual(self.sale_item.total_price, 25)
        self.assertEqual(self.stock.quantity, 6)
        self.assertEqual(Return.objects.count(), 1)
        self.assertEqual(ReturnBatch.objects.get().total_amount, 25)

# Create your tests here.
