from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    details = models.TextField(verbose_name="Event")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Activity log"
        verbose_name_plural = "Activity logs"

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username}: {self.details}"


class ActivityLogRead(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    activity = models.ForeignKey(ActivityLog, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "activity"), name="unique_activity_read")
        ]
