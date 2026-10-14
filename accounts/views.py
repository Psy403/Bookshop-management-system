from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db import transaction

from books.models import Book
from sales.models import Sale
from retur.models import Return
from log.models import ActivityLog
from log.utils import record_activity
from .avatar_options import AVATAR_OPTIONS
from .forms import ProfileChangeRequestForm, ProfilePictureForm
from .models import ContactEmail, ProfileChangeRequest, User




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
@require_POST
def staff_logout(request):

    username = request.user.username
    record_activity(
        request,
        f'User "{username}" logged out.',
        action="LOGOUT",
    )
    logout(request)

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("staff_login")


@require_POST
def staff_tab_logout(request):
    if request.user.is_authenticated:
        username = request.user.username
        record_activity(
            request,
            f'User "{username}" logged out when their tab closed.',
            action="LOGOUT",
        )
        logout(request)
    return HttpResponse(status=204)


@login_required
def dashboard(request):

    total_books = Book.objects.count()

    total_revenue = Sale.objects.aggregate(total=Sum("total_price"))["total"] or 0
    total_returns = Return.objects.count()

    context = {
        "total_books": total_books,
        "total_revenue": total_revenue,
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
    saved_contact_numbers = list(
        request.user.contact_numbers.values_list("number", flat=True)
    )
    if request.user.phone_number and request.user.phone_number not in saved_contact_numbers:
        saved_contact_numbers.insert(0, request.user.phone_number)
    initial_profile = {
        "username": request.user.username,
        "first_name": request.user.first_name,
        "middle_name": request.user.middle_name or "",
        "last_name": request.user.last_name,
        "email": "\n".join(
            [request.user.email]
            + list(request.user.contact_emails.values_list("email", flat=True))
        ).strip(),
        "contact_numbers": "\n".join(saved_contact_numbers),
    }

    if request.method == "POST" and "update_profile_picture" in request.POST:
        picture_form = ProfilePictureForm(request.POST, request.FILES)
        form = ProfileChangeRequestForm(user=request.user, initial=initial_profile)
        if picture_form.is_valid():
            uploaded_picture = picture_form.cleaned_data["profile_picture"]
            if uploaded_picture:
                request.user.profile_picture = uploaded_picture
                request.user.save(update_fields=["profile_picture"])
            else:
                previous_picture = request.user.profile_picture
                request.user.profile_picture = None
                request.user.avatar_choice = int(picture_form.cleaned_data["avatar_choice"])
                request.user.save(update_fields=["profile_picture", "avatar_choice"])
                if previous_picture:
                    previous_picture.delete(save=False)
            messages.success(request, "Your profile picture has been updated.")
            return redirect("profile")
    elif request.method == "POST":
        form_data = request.POST.copy()
        form_data["email"] = "\n".join(request.POST.getlist("email_entry"))
        form_data["contact_numbers"] = "\n".join(request.POST.getlist("contact_entry"))
        form = ProfileChangeRequestForm(form_data, user=request.user)
        picture_form = ProfilePictureForm()
        if form.is_valid():
            if pending_request:
                messages.error(request, "You already have a profile change request awaiting approval.")
            else:
                change = form.save(commit=False)
                change.user = request.user
                if form.cleaned_data["new_password"]:
                    change.password_hash = make_password(form.cleaned_data["new_password"])
                change.save()
                for administrator in User.objects.filter(is_active=True, is_staff=True):
                    ActivityLog.objects.create(
                        user=request.user,
                        recipient=administrator,
                        details=f"{request.user.username} has applied for profile changes.",
                    )
                messages.success(request, "Profile changes submitted for admin approval.")
                return redirect("profile")
    else:
        form = ProfileChangeRequestForm(user=request.user, initial=initial_profile)
        picture_form = ProfilePictureForm()

    if request.method == "POST" and "update_profile_picture" not in request.POST:
        email_values = request.POST.getlist("email_entry")
        contact_values = request.POST.getlist("contact_entry")
    else:
        email_values = [value for value in form.initial.get("email", "").splitlines()]
        contact_values = form.initial.get("contact_numbers", "").splitlines()
    email_values = email_values or [""]
    contact_values = contact_values or [""]
    profile_validation_errors = (
        form.errors.get("email", []) + form.errors.get("contact_numbers", [])
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "picture_form": picture_form,
            "avatar_options": AVATAR_OPTIONS,
            "pending_request": pending_request,
            "email_values": email_values,
            "contact_values": contact_values,
            "profile_validation_errors": profile_validation_errors,
        },
    )