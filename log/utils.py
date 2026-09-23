def record_activity(request, description, action=None):
    request.activity_log_description = description
    if action:
        request.activity_log_action = action
from .models import ActivityLog


LOW_STOCK_THRESHOLD = 20


def notify_low_stock(book, quantity, previous_quantity=None):
    """Create one notification when stock crosses below the low-stock threshold."""
    crossed_threshold = (
        quantity < LOW_STOCK_THRESHOLD
        and (
            previous_quantity is None
            or previous_quantity >= LOW_STOCK_THRESHOLD
        )
    )
    if not crossed_threshold:
        return

    ActivityLog.objects.create(
        user=None,
        action="STOCK",
        path="/books/stock/",
        status_code=200,
        details=(
            f'Book "{book.title}" stock is low ({quantity} remaining). '
            "Please consider restocking it."
        ),
    )
