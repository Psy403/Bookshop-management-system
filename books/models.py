from django.db import models
from suppliers.models import supplier
# Create your models here.
class book_category(models.Model):
    name = models.CharField()

    def __str__(self):
        return self.name

    
class book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    publication_date = models.DateField()
    isbn = models.CharField(max_length=13, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    supplier = models.ForeignKey(supplier, on_delete=models.CASCADE)
    book_category = models.ForeignKey(book_category, on_delete=models.CASCADE, null=True, blank=True)


    def __str__(self):
        return self.title

class stock(models.Model):
    book = models.OneToOneField(book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.book.title} - {self.quantity} in stock"
    




