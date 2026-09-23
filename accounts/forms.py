from django import forms
from django.contrib.auth.forms import UserCreationForm

from .avatar_options import AVATAR_OPTIONS
from .models import ProfileChangeRequest, User


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


class ProfileChangeRequestForm(forms.ModelForm):
    avatar_choice = forms.ChoiceField(
        choices=[(option["id"], option["name"]) for option in AVATAR_OPTIONS],
        widget=forms.RadioSelect,
    )

    contact_numbers = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Enter one contact number per line.",
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = ProfileChangeRequest
        fields = ("first_name", "middle_name", "last_name", "contact_numbers", "email", "avatar_choice")

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
