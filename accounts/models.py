from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="STAFF",
    )

    def __str__(self):
        return self.username


class ModulePermission(models.Model):

    MODULE_CHOICES = [
        ("dashboard", "Dashboard"),
    ]

    role = models.CharField(
        max_length=20,
        choices=User.ROLE_CHOICES,
        default="STAFF",
    )

    module_name = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
    )

    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("role", "module_name")

    def __str__(self):
        return f"{self.get_role_display()} - {self.module_name}"