from django.urls import path

from . import views


urlpatterns = [
    path("", views.return_list, name="return_list"),
    path("add/", views.return_create, name="return_create"),
    path("<int:batch_id>/report/", views.return_report, name="return_report"),
]
