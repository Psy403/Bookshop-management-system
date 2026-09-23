from django.db import models
from sales.models import Sale


class ReturnBatch(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="return_batches")
    return_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Return {self.id} for bill {self.sale_id}"


from sales.models import Sale, SaleItem

# Create your models here.
class Return(models.Model):
    batch = models.ForeignKey(
        ReturnBatch,
        on_delete=models.CASCADE,
        related_name="items",
        null=True,
        blank=True,
    )
    sale = models.ForeignKey(
        Sale,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="returns",
    )
    sale_item = models.ForeignKey(
        SaleItem,
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