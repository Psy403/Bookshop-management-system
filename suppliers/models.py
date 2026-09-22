from django.db import models

# Create your models here.
class supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    country = models.CharField(max_length=100, blank=True)
    address = models.TextField()
    pan_number = models.CharField(max_length=20,null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name