from .avatar_options import AVATAR_OPTIONS
from log.models import ActivityLog


def account_header(request):
    if not request.user.is_authenticated:
        return {"avatar_options": AVATAR_OPTIONS, "recent_notifications": []}

    unread = ActivityLog.objects.exclude(reads__user=request.user)
    return {
        "avatar_options": AVATAR_OPTIONS,
        "recent_notifications": ActivityLog.objects.select_related("user").order_by(
            "-created_at"
        )[:10],
        "unread_notification_count": unread.count(),
    }
