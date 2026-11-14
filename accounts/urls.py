from django.urls import path

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
    path("profile/", ProfileView.as_view(), name="profile"),
    path("profile/edit/", ProfileUpdateView.as_view(), name="profile_edit"),
    path("manage/users/", UserListView.as_view(), name="user_list"),
    path("manage/users/create/", UserCreateView.as_view(), name="user_create"),
    path("manage/users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
]
