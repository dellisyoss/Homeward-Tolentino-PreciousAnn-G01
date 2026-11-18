from django.urls import path

from . import views

app_name = "cases"

urlpatterns = [
    path("", views.case_list, name="list"),
    path("new/", views.case_create, name="create"),
    path("zones/", views.zone_manage, name="zones"),
    path("zones/<int:pk>/edit/", views.zone_manage, name="zone_edit"),
    path("<int:pk>/", views.case_detail, name="detail"),
]
