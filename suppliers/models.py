from django.db import models

# Create your models here.
class supplier(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    address = models.TextField()
    pan_number = models.CharField(max_length=20,null=True, blank=True)

    def __str__(self):
        return self.name