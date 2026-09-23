from django.urls import path

from . import views


urlpatterns = [
    path("", views.activity_list, name="activity_list"),
    path("read-all/", views.mark_all_activities_read, name="mark_all_activities_read"),
    path("<int:activity_id>/read/", views.mark_activity_read, name="mark_activity_read"),
]
