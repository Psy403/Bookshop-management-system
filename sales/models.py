from django.db import models

# Create your models here.
class sale(models.Model):
    book = models.ForeignKey('books.book', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    sale_date = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.quantity} copies of {self.book.title} sold on {self.sale_date}"