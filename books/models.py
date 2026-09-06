from django.db import models
from suppliers.models import supplier

class book_category(models.Model):
    name = models.CharField()
    description=models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name

    
class Book(models.Model):
    book_category = models.ForeignKey(book_category, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publication_date = models.DateField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    supplier = models.ForeignKey(supplier, on_delete=models.CASCADE)
    is_available=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class stock(models.Model):
    book = models.OneToOneField(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.book.title} - {self.quantity} in stock"
    




