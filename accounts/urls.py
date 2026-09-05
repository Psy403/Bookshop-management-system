from django.urls import path
from . import views

urlpatterns = [
    path("", views.staff_login, name="staff_login"),
    path("logout/", views.staff_logout, name="staff_logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
]