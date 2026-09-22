from django.conf import settings
from django.db import models
from books.models import Book


class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)


    quantity = models.PositiveIntegerField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2)
    sale_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.book.title


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