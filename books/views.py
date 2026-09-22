from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import book_category
from .models import Book, stock
from retur.models import Return
from log.utils import record_activity


@login_required
def book_stock_list(request):

    books = Book.objects.select_related(
        "book_category",
        "supplier"
    ).prefetch_related(
        "stock"
    ).order_by("title")

    total_books = Book.objects.count()

    total_stock = sum(
        item.stock.quantity
        for item in books
        if hasattr(item, "stock")
    )
    returned_by_book = {}
    for item in Return.objects.select_related("sale__book", "sale_item__book"):
        book_id = (
            item.sale_item.book_id
            if item.sale_item
            else item.sale.book_id
            if item.sale
            else None
        )
        if book_id:
            returned_by_book[book_id] = (
                returned_by_book.get(book_id, 0) + (item.return_quantity or 0)
            )
    for book in books:
        book.returned_quantity = returned_by_book.get(book.id, 0)

    context = {
        "books": books,
        "total_books": total_books,
        "total_stock": total_stock,
    }

    return render(
        request,
        "books/book_stock_list.html",
        context
    )


@login_required
def category_list(request):

    categories = book_category.objects.all().order_by("name")

    search = request.GET.get("search", "").strip()

    if search:
        categories = categories.filter(name__icontains=search)

    context = {
        "categories": categories,
        "search": search,
        "total_categories": book_category.objects.count(),
    }

    return render(
        request,
        "books/category_list.html",
        context
    )




@login_required
def category_add(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        # Check empty name
        if not name:
            messages.error(
                request,
                "Category name is required."
            )

            return render(
                request,
                "books/category_form.html",
                {
                    "form_title": "Add Category",
                    "button_text": "Add Category",
                    "name": name,
                    "description": description,
                }
            )

        # Check duplicate category
        if book_category.objects.filter(
            name__iexact=name
        ).exists():

            messages.error(
                request,
                "A category with this name already exists."
            )

            return render(
                request,
                "books/category_form.html",
                {
                    "form_title": "Add Category",
                    "button_text": "Add Category",
                    "name": name,
                    "description": description,
                }
            )

        # Create category
        book_category.objects.create(
            name=name,
            description=description
        )

        record_activity(
            request,
            f'Category "{name}" was created.',
            action="CREATE",
        )
        messages.success(
            request,
            "Category added successfully."
        )

        return redirect("category_list")

    return render(
        request,
        "books/category_form.html",
        {
            "form_title": "Add Category",
            "button_text": "Add Category",
        }
    )


@login_required
def category_edit(request, category_id):

    category = get_object_or_404(
        book_category,
        id=category_id
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get(
            "description",
            ""
        ).strip()

        # Check empty name
        if not name:

            messages.error(
                request,
                "Category name is required."
            )

            return render(
                request,
                "books/category_form.html",
                {
                    "form_title": "Edit Category",
                    "button_text": "Update Category",
                    "category": category,
                    "name": name,
                    "description": description,
                }
            )

        # Check duplicate category
        duplicate = book_category.objects.filter(
            name__iexact=name
        ).exclude(
            id=category.id
        ).exists()

        if duplicate:

            messages.error(
                request,
                "A category with this name already exists."
            )

            return render(
                request,
                "books/category_form.html",
                {
                    "form_title": "Edit Category",
                    "button_text": "Update Category",
                    "category": category,
                    "name": name,
                    "description": description,
                }
            )

        category.name = name
        category.description = description

        category.save()

        record_activity(
            request,
            f'Category "{name}" was updated.',
            action="UPDATE",
        )
        messages.success(
            request,
            "Category updated successfully."
        )

        return redirect("category_list")

    return render(
        request,
        "books/category_form.html",
        {
            "form_title": "Edit Category",
            "button_text": "Update Category",
            "category": category,
            "name": category.name,
            "description": category.description,
        }
    )



@login_required
def category_delete(request, category_id):

    category = get_object_or_404(
        book_category,
        id=category_id
    )

    if request.method == "POST":

        category_name = category.name

        category.delete()

        record_activity(
            request,
            f'Category "{category_name}" was deleted.',
            action="DELETE",
        )
        messages.success(
            request,
            f'Category "{category_name}" deleted successfully.'
        )

        return redirect("category_list")

    return render(
        request,
        "books/category_confirm_delete.html",
        {
            "category": category,
        }
    )