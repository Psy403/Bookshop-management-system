from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import ActivityLog


@login_required
def activity_list(request):
    activities = ActivityLog.objects.select_related("user").all()[:200]
    return render(request, "log/activity_list.html", {"activities": activities})
