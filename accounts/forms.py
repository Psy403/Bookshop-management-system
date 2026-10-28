from django import forms
from django.contrib.auth.forms import UserCreationForm, password_validation
from django.core.validators import EmailValidator

from .avatar_options import AVATAR_OPTIONS
from .models import AccountCreationRequest, ProfileChangeRequest, User


class StaffCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    middle_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    phone_number = forms.CharField(max_length=20, required=True)
    hiring_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "phone_number",
            "role",
            "hiring_date",
            "email",
            "is_active",
        )

    def clean_role(self):
        role = self.cleaned_data["role"]
        if role != "STAFF":
            raise forms.ValidationError("New accounts created here must have the Staff role.")
        return role


class AccountCreationRequestForm(forms.ModelForm):
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirm_password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = AccountCreationRequest
        fields = (
            "first_name",
            "middle_name",
            "last_name",
            "username",
            "email",
            "phone_number",
        )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already in use.")
        if AccountCreationRequest.objects.filter(
            username__iexact=username,
            status="PENDING",
        ).exists():
            raise forms.ValidationError("A request for this username is already pending.")
        return username

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        if (
            len(phone_number) != 10
            or not phone_number.isascii()
            or not phone_number.isdigit()
        ):
            raise forms.ValidationError("Enter a valid 10-digit phone number.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if not email.lower().endswith("@gmail.com"):
            raise forms.ValidationError("Not valid email address.")
        try:
            EmailValidator()(email)
        except forms.ValidationError as error:
            raise forms.ValidationError("Not valid email address.") from error
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "The passwords do not match.")
        elif password:
            candidate = User(
                username=cleaned_data.get("username", ""),
                first_name=cleaned_data.get("first_name", ""),
                last_name=cleaned_data.get("last_name", ""),
                email=cleaned_data.get("email", ""),
            )
            try:
                password_validation.validate_password(password, candidate)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data


class ProfileChangeRequestForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "profile-form-input"}),
    )
    email = forms.CharField(widget=forms.HiddenInput, required=False)
    contact_numbers = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    new_password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "profile-form-input",
                "autocomplete": "new-password",
                "placeholder": "Enter a new password",
            },
            render_value=False,
        ),
    )
    confirm_new_password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "profile-form-input",
                "autocomplete": "new-password",
                "placeholder": "Confirm the new password",
            },
            render_value=False,
        ),
    )

    class Meta:
        model = ProfileChangeRequest
        fields = (
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "contact_numbers",
        )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        for field_name in ("username", "first_name", "middle_name", "last_name"):
            self.fields[field_name].widget.attrs["class"] = "profile-form-input"

    def clean_username(self):
        username = self.cleaned_data["username"]
        queryset = User.objects.filter(username__iexact=username)
        if self.user:
            queryset = queryset.exclude(pk=self.user.pk)
        if queryset.exists():
            raise forms.ValidationError("This username is already in use.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password or confirm_new_password:
            if new_password != confirm_new_password:
                self.add_error("confirm_new_password", "The passwords do not match.")
            elif new_password:
                try:
                    password_validation.validate_password(new_password, self.user)
                except forms.ValidationError as error:
                    self.add_error("new_password", error)
        return cleaned_data

    def clean_email(self):
        addresses = [
            address.strip()
            for address in self.cleaned_data["email"].splitlines()
            if address.strip()
        ]
        validate_email = EmailValidator()
        for address in addresses:
            if not address.lower().endswith("@gmail.com"):
                raise forms.ValidationError("Not valid email address.")
            try:
                validate_email(address)
            except forms.ValidationError as error:
                raise forms.ValidationError("Not valid email address.") from error
        return "\n".join(addresses)

    def clean_contact_numbers(self):
        numbers = [
            number.strip()
            for number in self.cleaned_data["contact_numbers"].splitlines()
            if number.strip()
        ]
        if any(len(number) != 10 or not number.isascii() or not number.isdigit() for number in numbers):
            raise forms.ValidationError("The contact number should be of 10 digits.")
        return "\n".join(numbers)


class ProfilePictureForm(forms.Form):
    avatar_choice = forms.ChoiceField(
        choices=[(option["id"], option["name"]) for option in AVATAR_OPTIONS],
        required=False,
        widget=forms.RadioSelect,
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "class": "sr-only",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        if not self.errors and not cleaned_data.get("profile_picture") and not cleaned_data.get("avatar_choice"):
            raise forms.ValidationError("Choose an avatar or select a profile photo.")
        return cleaned_data

    def clean_profile_picture(self):
        picture = self.cleaned_data.get("profile_picture")
        if picture and picture.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Profile pictures must be 2 MB or smaller.")
        if picture and picture.content_type not in (
            "image/jpeg",
            "image/png",
            "image/webp",
        ):
            raise forms.ValidationError("Use a JPEG, PNG, or WebP image.")
        return picture
