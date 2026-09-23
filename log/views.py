from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from .models import ActivityLog, ActivityLogRead


@login_required
def activity_list(request):
    activities = ActivityLog.objects.select_related("user").all()
    search = request.GET.get("search", "").strip()
    date_value = request.GET.get("date", "").strip()
    if search:
        activities = activities.filter(
            user__username__icontains=search
        ) | activities.filter(user__first_name__icontains=search) | activities.filter(
            user__last_name__icontains=search
        )
    if date_value and parse_date(date_value):
        activities = activities.filter(created_at__date=parse_date(date_value))
    page_obj = Paginator(activities.distinct(), 10).get_page(request.GET.get("page"))
    return render(request, "log/activity_list.html", {
        "page_obj": page_obj, "search": search, "date_value": date_value,
    })


@login_required
def mark_activity_read(request, activity_id):
    if request.method == "POST":
        activity = get_object_or_404(ActivityLog, id=activity_id)
        ActivityLogRead.objects.get_or_create(user=request.user, activity=activity)
    return redirect(request.POST.get("next") or "activity_list")


@login_required
def mark_all_activities_read(request):
    if request.method == "POST":
        unread_ids = ActivityLog.objects.exclude(
            reads__user=request.user
        ).values_list("id", flat=True)
        ActivityLogRead.objects.bulk_create(
            [
                ActivityLogRead(user=request.user, activity_id=activity_id)
                for activity_id in unread_ids
            ],
            ignore_conflicts=True,
        )
    return redirect(request.POST.get("next") or "activity_list")
