from django.contrib import messages
from django.db.models import Q

from .models import ActivityLog


def record_activity(request, description, action=None):
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    recipient = user if action in {"LOGIN", "LOGOUT"} else None
    return ActivityLog.objects.create(
        user=user,
        recipient=recipient,
        details=description,
    )


def visible_activities_for(user):
    return ActivityLog.objects.filter(
        Q(recipient=user) | Q(recipient__isnull=True),
        created_at__gte=user.date_joined,
    )


LOW_STOCK_THRESHOLD = 20


def notify_low_stock(book, quantity, previous_quantity=None, request=None):
    """Broadcast a notification when a book crosses below the low-stock threshold."""
    crossed_threshold = (
        quantity < LOW_STOCK_THRESHOLD
        and (
            previous_quantity is None
            or previous_quantity >= LOW_STOCK_THRESHOLD
        )
    )
    if not crossed_threshold:
        return

    details = (
        f"{book.title} stock level is only {quantity}. "
        "Please consider restocking it."
    )
    ActivityLog.objects.create(
        user=None,
        details=details,
    )
    if request is not None:
        messages.warning(request, details, extra_tags="low-stock")
