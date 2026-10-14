def record_activity(request, description, action=None):
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    return ActivityLog.objects.create(user=user, details=description)
from django.contrib import messages

from .models import ActivityLog


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
