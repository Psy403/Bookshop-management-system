from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse
from django.test import TestCase

from suppliers.models import supplier
from log.models import ActivityLog
from log.utils import notify_low_stock

from .models import Book, stock


class BookAdminTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="a-strong-password-123",
        )
        self.supplier = supplier.objects.create(
            name="Test Supplier",
            email="supplier@example.com",
            phone_number="9800000000",
            address="Supplier address",
        )
        self.client.force_login(self.admin_user)

    def test_book_add_form_uses_selling_price_and_hides_availability(self):
        response = self.client.get(reverse("admin:books_book_add"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Initial stock")
        self.assertNotContains(response, "stock_quantity")
        self.assertContains(response, "Selling price")
        self.assertNotContains(response, "name=\"is_available\"")

    def test_book_can_be_added_and_gets_zero_stock(self):
        response = self.client.post(
            reverse("admin:books_book_add"),
            {
                "title": "Book with stock",
                "author": "Test Author",
                "publication_year": "2026",
                "price": "10.00",
                "cost_price": "7.00",
                "supplier": self.supplier.pk,
                "language": "English",
                "edition": "First",
            },
        )

        self.assertEqual(response.status_code, 302)
        book = Book.objects.get(title="Book with stock")
        self.assertEqual(stock.objects.get(book=book).quantity, 0)

    def test_add_stock_opens_purchase_id_receiving_form(self):
        response = self.client.get(reverse("admin:books_stock_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Purchase ID")
        self.assertNotContains(response, "Manually fill stock data")

    def test_stock_dustbin_removes_requested_quantity(self):
        book = Book.objects.create(
            title="Deletable Stock",
            author="Author",
            publication_year=2026,
            price="10.00",
            supplier=self.supplier,
        )
        stock_record = stock.objects.create(book=book, quantity=50)

        response = self.client.post(
            reverse("admin:books_stock_remove_stock", args=[stock_record.pk]),
            {"quantity": "20"},
        )

        self.assertRedirects(response, reverse("admin:books_stock_changelist"))
        stock_record.refresh_from_db()
        self.assertEqual(stock_record.quantity, 30)
        self.assertTrue(
            ActivityLog.objects.filter(
                details__contains="20 copies of Deletable Stock were deleted"
            ).exists()
        )

    def test_stock_admin_does_not_allow_manual_quantity_changes(self):
        book = Book.objects.create(
            title="Stocked Book",
            author="Test Author",
            publication_year=2026,
            price="10.00",
            supplier=self.supplier,
        )
        stock.objects.create(book=book, quantity=50)

        response = self.client.post(
            reverse("admin:books_stock_change", args=(book.stock.pk,)),
            {
                "book": book.pk,
                "quantity": "500",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(stock.objects.get(book=book).quantity, 50)


class LowStockNotificationTests(TestCase):
    def setUp(self):
        self.supplier = supplier.objects.create(name="Test Supplier")
        self.book = Book.objects.create(
            title="Low Stock Book",
            author="Test Author",
            publication_year=2026,
            price="10.00",
            supplier=self.supplier,
        )

    def test_notification_names_book_when_stock_crosses_below_threshold(self):
        stock.objects.create(book=self.book, quantity=20)

        stock_record = stock.objects.get(book=self.book)
        stock_record.quantity = 19
        stock_record.save(update_fields=["quantity"])

        notification = ActivityLog.objects.get(details__contains="Low Stock Book")
        self.assertIn("Low Stock Book", notification.details)
        self.assertIn("stock level is only 19", notification.details)

    def test_threshold_crossing_queues_a_sweetalert_warning(self):
        stock_record = stock.objects.create(book=self.book, quantity=20)
        request = RequestFactory().post("/")
        request.user = AnonymousUser()
        request.session = {}
        request._messages = FallbackStorage(request)

        stock_record.quantity = 19
        stock_record.save(update_fields=["quantity"], request=request)

        notification_messages = list(get_messages(request))
        self.assertEqual(len(notification_messages), 1)
        self.assertEqual(
            str(notification_messages[0]),
            "Low Stock Book stock level is only 19. Please consider restocking it.",
        )
        self.assertIn("low-stock", notification_messages[0].tags)

    def test_low_stock_notification_is_not_repeated_while_already_below_threshold(self):
        stock_record = stock.objects.create(book=self.book, quantity=19)
        stock_record.quantity = 18
        stock_record.save(update_fields=["quantity"])

        self.assertEqual(ActivityLog.objects.filter(details__contains="Low Stock Book").count(), 1)

    def test_notification_is_broadcast_without_specific_user(self):
        notify_low_stock(self.book, 19, previous_quantity=20)

        self.assertTrue(
            ActivityLog.objects.filter(
                user__isnull=True,
                details__contains="Low Stock Book",
            ).exists()
        )

# Create your tests here.
