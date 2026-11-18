from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import (
    AdminUserCreationForm,
    AdminUserUpdateForm,
    EmailAuthenticationForm,
    ProfileForm,
    RegistrationForm,
)
from .models import User


class UniqueEmailSaveMixin:
    def form_valid(self, form):
        try:
            with transaction.atomic():
                return super().form_valid(form)
        except IntegrityError:
            # Validation alone cannot prevent concurrent duplicate submissions.
            users = User.objects.filter(email__iexact=form.cleaned_data["email"])
            if form.instance.pk:
                users = users.exclude(pk=form.instance.pk)
            if not users.exists():
                raise
            form.add_error("email", "An account with this email already exists.")
            return self.form_invalid(form)


class SignUpView(UniqueEmailSaveMixin, SuccessMessageMixin, CreateView):
    form_class = RegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")
    success_message = "Your account was created successfully. You can now log in."

    def form_valid(self, form):
        form.instance.role = User.Role.MEMBER
        return super().form_valid(form)


class EmailLoginView(LoginView):
    authentication_form = EmailAuthenticationForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["password_reset_enabled"] = settings.PASSWORD_RESET_ENABLED
        return context

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


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    role = None

    def test_func(self):
        return self.request.user.role == self.role


class RoleDashboardView(RoleRequiredMixin, TemplateView):
    pass


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


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class ProfileUpdateView(LoginRequiredMixin, UniqueEmailSaveMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = "accounts/profile_form.html"
    success_url = reverse_lazy("profile")
    success_message = "Your profile was updated successfully."

    def get_object(self, queryset=None):
        # Never accept a user ID from the URL, query string, or submitted data.
        return self.request.user


class AdminRequiredMixin(RoleRequiredMixin):
    role = User.Role.ADMIN


class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "accounts"
    paginate_by = 10

    def get_queryset(self):
        self.search = self.request.GET.get("q", "").strip()[:100]
        users = User.objects.order_by("email")
        if self.search:
            users = users.filter(Q(email__icontains=self.search) | Q(full_name__icontains=self.search))
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.search
        return context


class UserCreateView(AdminRequiredMixin, UniqueEmailSaveMixin, SuccessMessageMixin, CreateView):
    form_class = AdminUserCreationForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("user_list")
    success_message = "The user account was created successfully."
    extra_context = {"page_title": "Create user"}


class UserUpdateView(AdminRequiredMixin, UniqueEmailSaveMixin, SuccessMessageMixin, UpdateView):
    model = User
    context_object_name = "managed_user"
    form_class = AdminUserUpdateForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("user_list")
    success_message = "The user account was updated successfully."
    extra_context = {"page_title": "Edit user"}

    def get_object(self, queryset=None):
        account = super().get_object(queryset)
        if account.pk == self.request.user.pk:
            raise PermissionDenied("Use your profile to edit your own account.")
        if account.is_superuser:
            raise PermissionDenied("This administrator account is protected.")
        return account
