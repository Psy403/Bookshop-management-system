from datetime import timedelta

from django.utils import timezone

from .avatar_options import AVATAR_OPTIONS
from log.models import ActivityLog


def account_header(request):
    if not request.user.is_authenticated:
        return {"avatar_options": AVATAR_OPTIONS, "recent_notifications": []}

    return {
        "avatar_options": AVATAR_OPTIONS,
        "recent_notifications": ActivityLog.objects.select_related("user").order_by(
            "-created_at"
        )[:10],
        "unread_notification_count": ActivityLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count(),
    }
