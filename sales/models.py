from decimal import Decimal

from django.conf import settings
from django.db import models
from books.models import Book


class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)

    quantity = models.PositiveIntegerField(default=0)
    total_price=models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.book.title if self.book_id else f"Sale #{self.pk}"

    def recalculate_total(self):
        total = sum(
            (item.total_price for item in self.items.all()),
            Decimal("0.00"),
        )
        quantity = sum(item.quantity for item in self.items.all())
        type(self).objects.filter(pk=self.pk).update(
            quantity=quantity,
            total_price=total,
            book_id=self.book_id,
        )
        self.quantity = quantity
        self.total_price = total
        return total


class SaleItem(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )
    book = models.ForeignKey(Book, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.sale_id} - {self.book.title}"

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        preserve_total = (
            self.pk
            and update_fields is not None
            and set(update_fields).issubset({"total_price"})
        )
        if not preserve_total:
            self.total_price = Decimal(str(self.unit_price)) * self.quantity
        result = super().save(*args, **kwargs)
        if not preserve_total:
            self.sale.recalculate_total()
        return result