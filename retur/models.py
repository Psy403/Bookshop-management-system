from django.db import models
from sales.models import Sale

# Create your models here.
class Return(models.Model):
    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="returns",
    )
    return_quantity = models.PositiveIntegerField(null=True, blank=True)
    return_date = models.DateField()
    return_amount = models.DecimalField(max_digits=10, decimal_places=2)
    return_type = models.CharField(max_length=50)
    reason = models.TextField()
    return_status = models.CharField(max_length=50)