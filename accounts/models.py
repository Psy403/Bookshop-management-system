from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    middle_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    hiring_date = models.DateField(default=timezone.localdate)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        null=True,
        blank=True,
    )
    avatar_choice = models.PositiveSmallIntegerField(default=1)

    def __str__(self):
        return self.username


class ContactNumber(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contact_numbers")
    number = models.CharField(max_length=20)

    def __str__(self):
        return self.number


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


class ProfileChangeRequest(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="profile_change_requests",
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    middle_name = models.CharField(max_length=150, blank=True)
    contact_numbers = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_profile_changes",
    )
    review_note = models.TextField(blank=True)

    class Meta:
        ordering = ("-requested_at",)

    def __str__(self):
        return f"{self.user.username} profile change ({self.status})"