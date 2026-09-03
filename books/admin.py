from django.contrib import admin

# Register your models here.
from .models import book,stock,book_category
admin.site.register(book_category)
admin.site.register(book)
admin.site.register(stock)
