from django import forms

from .avatar_options import AVATAR_OPTIONS
from .models import ProfileChangeRequest


class ProfileChangeRequestForm(forms.ModelForm):
    avatar_choice = forms.ChoiceField(
        choices=[(option["id"], option["name"]) for option in AVATAR_OPTIONS],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = ProfileChangeRequest
        fields = ("first_name", "last_name", "email", "avatar_choice", "profile_picture")

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
