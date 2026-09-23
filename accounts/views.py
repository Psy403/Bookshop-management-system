from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from books.models import Book, stock
from retur.models import Return
from log.utils import record_activity
from .forms import ProfileChangeRequestForm
from .models import ProfileChangeRequest




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
            record_activity(
                request,
                f'User "{user.username}" logged in.',
                action="LOGIN",
            )

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

    username = request.user.username
    logout(request)
    record_activity(
        request,
        f'User "{username}" logged out.',
        action="LOGOUT",
    )

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
    total_returns = Return.objects.count()

    context = {
        "total_books": total_books,
        "total_stock": total_stock,
        "total_returns": total_returns,
    }

    return render(
        request,
        "accounts/dashboard.html",
        context
    )


@login_required
def profile(request):
    pending_request = ProfileChangeRequest.objects.filter(
        user=request.user, status="PENDING"
    ).first()

    if request.method == "POST":
        form = ProfileChangeRequestForm(request.POST, request.FILES)
        if form.is_valid():
            request.user.avatar_choice = int(form.cleaned_data["avatar_choice"])
            if form.cleaned_data.get("profile_picture"):
                request.user.profile_picture = form.cleaned_data["profile_picture"]
            request.user.save(update_fields=["avatar_choice", "profile_picture"])
            if pending_request:
                messages.success(request, "Profile picture updated. Your other changes are still awaiting approval.")
                return redirect("profile")
            change = form.save(commit=False)
            change.user = request.user
            change.save()
            record_activity(
                request,
                "Profile information was submitted for admin approval.",
                action="PROFILE",
            )
            messages.success(request, "Profile changes submitted for admin approval.")
            return redirect("profile")
    else:
        form = ProfileChangeRequestForm(
            initial={
                "first_name": request.user.first_name,
                "middle_name": request.user.middle_name,
                "last_name": request.user.last_name,
                "email": request.user.email,
                "avatar_choice": request.user.avatar_choice,
                "contact_numbers": "\n".join(
                    request.user.contact_numbers.values_list("number", flat=True)
                ),
            }
        )

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "pending_request": pending_request},
    )