from django.urls import path

from . import views


urlpatterns = [
    path("", views.return_list, name="return_list"),
    path("add/", views.return_create, name="return_create"),
]
