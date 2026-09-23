from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
    )
    action = models.CharField(max_length=20)
    path = models.CharField(max_length=255)
    status_code = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Activity log"
        verbose_name_plural = "Activity logs"

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} {self.action} {self.path}"


class ActivityLogRead(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
    activity = models.ForeignKey(ActivityLog, on_delete=models.CASCADE, related_name="reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "activity"), name="unique_activity_read")
        ]
