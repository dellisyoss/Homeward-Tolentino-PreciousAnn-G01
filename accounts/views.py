from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import EmailAuthenticationForm, RegistrationForm
from .models import User


class SignUpView(CreateView):
    form_class = RegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

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
        messages.success(self.request, "Your account was created successfully. You can now log in.")
        return response


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Every login lands on the user's own role dashboard, regardless of next.
        return reverse("dashboard")


class AccountLogoutView(LogoutView):
    def get_success_url(self):
        return reverse("login")

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, "You have been logged out.")
        return response


@login_required
def dashboard_redirect(request):
    if request.user.role == User.Role.ADMIN:
        return redirect("admin_dashboard")
    if request.user.role == User.Role.MEMBER:
        return redirect("member_dashboard")
    raise PermissionDenied("Your account does not have a valid dashboard role.")


class RoleDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    role = None

    def test_func(self):
        return self.request.user.role == self.role


class MemberDashboardView(RoleDashboardView):
    role = User.Role.MEMBER
    template_name = "dashboard/member.html"


class AdminDashboardView(RoleDashboardView):
    role = User.Role.ADMIN
    template_name = "dashboard/admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_count"] = User.objects.count()
        context["member_count"] = User.objects.filter(role=User.Role.MEMBER).count()
        context["admin_count"] = User.objects.filter(role=User.Role.ADMIN).count()
        return context
