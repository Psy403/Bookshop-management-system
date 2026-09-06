from django.urls import path
from . import views


urlpatterns = [

    # Categories
    path(
        "categories/",
        views.category_list,
        name="category_list"
    ),

    path(
        "categories/add/",
        views.category_add,
        name="category_add"
    ),

    path(
        "categories/<int:category_id>/edit/",
        views.category_edit,
        name="category_edit"
    ),

    path(
        "categories/<int:category_id>/delete/",
        views.category_delete,
        name="category_delete"
    ),
    
    path(
        "stock/",
        views.book_stock_list,
        name="book_stock_list"
    ),
]