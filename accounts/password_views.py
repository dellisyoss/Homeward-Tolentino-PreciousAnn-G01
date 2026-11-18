from django.conf import settings
from django.contrib.auth import views
from django.shortcuts import render


class PasswordResetView(views.PasswordResetView):
    def dispatch(self, request, *args, **kwargs):
        if not settings.PASSWORD_RESET_ENABLED:
            return render(request, "registration/password_reset_unavailable.html", status=503)
        return super().dispatch(request, *args, **kwargs)
