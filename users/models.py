from django.db import models
from django.contrib.auth.models import User

class Staff(models.Model):

    ROLE_CHOICE=(
        ("staff", "STAFF"),
        ("admin", "ADMIN")
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    # name = models.CharField(max_length=100)
    phone = models.IntegerField(max_length=10)
    email = models.EmailField(unique= True)
    address = models.TextField()



    def __str__(self):
        return self.name
# Create your models here.
