from django.contrib import admin

# Register your models here.
from .models import Book,book_category
admin.site.register(book_category)
admin.site.register(Book)

