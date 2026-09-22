from django.db import models

# Create your models here.
class Purchase(models.Model):
    order_date = models.DateField()
    payment_status = models.CharField(max_length=50)
    expected_delivery = models.DateField(null=True, blank=True)
    order_status = models.CharField(max_length=50)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)