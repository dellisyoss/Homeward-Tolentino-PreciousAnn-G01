from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("accounts/", include("accounts.urls")),
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
]
