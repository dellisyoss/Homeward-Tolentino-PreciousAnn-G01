from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "full_name", "contact_number")
        labels = {"full_name": "Full name", "contact_number": "Contact number (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["full_name"].widget.attrs["autocomplete"] = "name"
        self.fields["contact_number"].widget.attrs["autocomplete"] = "tel"

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
