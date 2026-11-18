from django.urls import include, path
from django.views.generic import TemplateView

from accounts.views import AdminDashboardView, MemberDashboardView, dashboard_redirect
from .views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("accounts/", include("accounts.urls")),
    path("cases/", include("cases.urls")),
    path("dashboard/", dashboard_redirect, name="dashboard"),
    path("dashboard/member/", MemberDashboardView.as_view(), name="member_dashboard"),
    path("dashboard/admin/", AdminDashboardView.as_view(), name="admin_dashboard"),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
