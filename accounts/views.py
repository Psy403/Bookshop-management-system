from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from books.models import Book, stock


# ==========================================
# STAFF LOGIN
# ==========================================

def staff_login(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if not user.is_active:
                messages.error(
                    request,
                    "Your account has been deactivated."
                )

                return render(
                    request,
                    "accounts/staff_login.html"
                )

            login(request, user)

            if request.POST.get("remember_me"):
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "accounts/staff_login.html"
    )


@login_required
def staff_logout(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("staff_login")


@login_required
def dashboard(request):

    total_books = Book.objects.count()

    total_stock = sum(
        stock.quantity
        for stock in stock.objects.all()
    )

    context = {
        "total_books": total_books,
        "total_stock": total_stock,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )