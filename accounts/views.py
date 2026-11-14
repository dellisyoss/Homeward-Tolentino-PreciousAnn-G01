from django.contrib import messages
from django.db import IntegrityError, transaction
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import RegistrationForm
from .models import User


class SignUpView(CreateView):
    form_class = RegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        # Only fields explicitly listed in RegistrationForm can be submitted.
        form.instance.role = User.Role.MEMBER
        try:
            with transaction.atomic():
                response = super().form_valid(form)
        except IntegrityError:
            # Handle two registrations for the same email arriving together.
            if not User.objects.filter(email__iexact=form.cleaned_data["email"]).exists():
                raise
            form.add_error("email", "An account with this email already exists.")
            return self.form_invalid(form)
        messages.success(self.request, "Your account was created successfully.")
        return response
