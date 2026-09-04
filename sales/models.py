from django.conf import settings
from django.db import models
from books.models import Book


class Sale(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    quantity = models.PositiveIntegerField()
    total_price=models.DecimalField(max_digits=10, decimal_places=2)
    sale_at= models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.book