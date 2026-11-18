from django.contrib.auth import views as auth_views
from django.urls import path

from .password_views import PasswordResetView

from .views import (
    AccountLogoutView,
    EmailLoginView,
    ProfileUpdateView,
    ProfileView,
    SignUpView,
    UserCreateView,
    UserListView,
    UserUpdateView,
)

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
    path("password-reset/sent/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("manage/users/", UserListView.as_view(), name="user_list"),
    path("manage/users/create/", UserCreateView.as_view(), name="user_create"),
    path("manage/users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
]
