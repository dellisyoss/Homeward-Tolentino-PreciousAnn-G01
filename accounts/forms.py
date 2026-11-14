from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


def clean_unique_email(email, instance=None):
    email = User.objects.normalize_email(email)
    users = User.objects.filter(email__iexact=email)
    if instance is not None and instance.pk:
        users = users.exclude(pk=instance.pk)
    if users.exists():
        raise forms.ValidationError("An account with this email already exists.")
    return email


def style_fields(fields):
    for field in fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = "form-check-input"
        elif isinstance(field.widget, forms.Select):
            field.widget.attrs["class"] = "form-select"
        else:
            field.widget.attrs["class"] = "form-control"


class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "full_name", "contact_number")
        labels = {"full_name": "Full name", "contact_number": "Contact number (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self.fields)
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["full_name"].widget.attrs["autocomplete"] = "name"
        self.fields["contact_number"].widget.attrs["autocomplete"] = "tel"

    def clean_email(self):
        return clean_unique_email(self.cleaned_data["email"], self.instance)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "full_name", "contact_number")
        labels = {"full_name": "Full name", "contact_number": "Contact number (optional)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self.fields)

    def clean_email(self):
        return clean_unique_email(self.cleaned_data["email"], self.instance)


class AdminUserCreationForm(RegistrationForm):
    class Meta(RegistrationForm.Meta):
        fields = ("email", "full_name", "contact_number", "role", "is_active")
        labels = {**RegistrationForm.Meta.labels, "is_active": "Active account"}


class AdminUserUpdateForm(ProfileForm):
    class Meta(ProfileForm.Meta):
        fields = (*ProfileForm.Meta.fields, "role", "is_active")
        labels = {**ProfileForm.Meta.labels, "is_active": "Active account"}


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        max_length=100,
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email", "autofocus": True}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "autocomplete": "current-password"}
        )

    def clean_username(self):
        # AuthenticationForm uses the name 'username' for the login identifier,
        # while our user model identifies accounts by email.
        return User.objects.normalize_email(self.cleaned_data["username"])
