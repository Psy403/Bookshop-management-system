from .avatar_options import AVATAR_OPTIONS
from books.models import Book, stock
from log.models import ActivityLog
from log.utils import visible_activities_for
from sales.models import Sale
from .models import AccountCreationRequest, ProfileChangeRequest


def account_header(request):
    if not request.user.is_authenticated:
        return {"avatar_options": AVATAR_OPTIONS, "recent_notifications": []}

    notifications = visible_activities_for(request.user)
    unread = notifications.exclude(reads__user=request.user)
    return {
        "avatar_options": AVATAR_OPTIONS,
        "recent_notifications": notifications.select_related("user").order_by("-created_at")[:10],
        "unread_notification_count": unread.count(),
    }


def admin_dashboard(request):
    if not request.path == "/admin/" or not request.user.is_authenticated or not request.user.is_staff:
        return {}

    low_stock_books = list(
        Book.objects.select_related("stock").filter(stock__quantity__lt=20).order_by(
            "stock__quantity", "title"
        )[:5]
    )
    recent_sales = list(Sale.objects.order_by("-sale_at")[:6])
    return {
        "admin_dashboard_stats": {
            "books": Book.objects.count(),
            "low_stock": stock.objects.filter(quantity__lt=20).count(),
            "revenue": sum((sale.total_price for sale in recent_sales), 0),
            "pending_requests": (
                ProfileChangeRequest.objects.filter(status="PENDING").count()
                + AccountCreationRequest.objects.filter(status="PENDING").count()
            ),
        },
        "admin_low_stock_books": low_stock_books,
        "admin_recent_sales": recent_sales,
        "admin_recent_activity": visible_activities_for(request.user).select_related(
            "user"
        ).order_by("-created_at")[:5],
    }
