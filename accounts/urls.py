from django.urls import path

from .views import AccountLogoutView, EmailLoginView, SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
]
