from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import book_category
from .models import Book, stock


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


# ==========================================
# ADD CATEGORY
# ==========================================

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


# ==========================================
# EDIT CATEGORY
# ==========================================

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


# ==========================================
# DELETE CATEGORY
# ==========================================

@login_required
def category_delete(request, category_id):

    category = get_object_or_404(
        book_category,
        id=category_id
    )

    if request.method == "POST":

        category_name = category.name

        category.delete()

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