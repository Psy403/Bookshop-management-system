from decimal import Decimal
from datetime import date

from django.db import models

from books.models import Book
from suppliers.models import supplier


class Purchase(models.Model):
    PAYMENT_PENDING = "pending"
    PAYMENT_PARTIAL = "partial"
    PAYMENT_PAID = "paid"
    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_PENDING, "Pending"),
        (PAYMENT_PARTIAL, "Partially paid"),
        (PAYMENT_PAID, "Paid"),
    )
    METHOD_CASH = "cash"
    METHOD_BANK_TRANSFER = "bank_transfer"
    METHOD_CREDIT = "credit"
    METHOD_OTHER = "other"
    PAYMENT_METHOD_CHOICES = (
        (METHOD_CASH, "Cash"),
        (METHOD_BANK_TRANSFER, "Bank transfer"),
        (METHOD_CREDIT, "Credit"),
        (METHOD_OTHER, "Other"),
    )

    supplier = models.ForeignKey(supplier, on_delete=models.PROTECT, related_name="purchases")
    order_date = models.DateField(default=date.today)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_PENDING
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default=METHOD_CASH
    )
    total_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    def recalculate_total(self):
        total = sum((item.total_price for item in self.items.all()), Decimal("0.00"))
        if self.total_cost != total:
            type(self).objects.filter(pk=self.pk).update(total_cost=total)
            self.total_cost = total
        return total

    def __str__(self):
        return f"Purchase #{self.pk}"


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase, on_delete=models.CASCADE, related_name="items"
    )
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    received_quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00"), editable=False
    )

    def save(self, *args, **kwargs):
        if self.quantity < 1:
            raise ValueError("Purchase quantity must be at least 1.")
        if self.received_quantity > self.quantity:
            raise ValueError("Received quantity cannot exceed purchased quantity.")
        unit_price = Decimal(str(self.unit_price))
        if unit_price < 0:
            raise ValueError("Purchase unit price cannot be negative.")
        self.total_price = unit_price * self.quantity
        result = super().save(*args, **kwargs)
        if self.purchase_id:
            self.purchase.recalculate_total()
        return result

    def delete(self, *args, **kwargs):
        purchase = self.purchase
        result = super().delete(*args, **kwargs)
        if purchase.pk:
            purchase.recalculate_total()
        return result

    def __str__(self):
        return f"{self.purchase} - {self.book.title}"
