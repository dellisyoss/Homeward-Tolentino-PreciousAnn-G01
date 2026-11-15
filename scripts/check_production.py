"""Verify production settings and HTTPS/static behavior without creating data."""
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["DJANGO_SETTINGS_MODULE"] = "homeward.production"
os.environ.setdefault("RENDER_EXTERNAL_HOSTNAME", "homeward-check.onrender.com")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "")

import django

django.setup()

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.management import call_command
from django.db import OperationalError
from django.test import Client


def main():
    call_command("check", deploy=True, fail_level="WARNING")
    call_command("collectstatic", interactive=False, verbosity=0)
    host = os.environ["RENDER_EXTERNAL_HOSTNAME"]
    client = Client(HTTP_HOST=host, enforce_csrf_checks=True)
    assert not settings.DEBUG
    assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE

    response = client.get("/")
    assert response.status_code == 301
    assert response["Location"] == f"https://{host}/"

    # Match Render's HTTPS forwarding header rather than bypassing the proxy setting.
    https = {"HTTP_X_FORWARDED_PROTO": "https"}
    response = client.get("/accounts/login/", **https)
    assert response.status_code == 200
    assert response.cookies[settings.CSRF_COOKIE_NAME]["secure"]
    assert "max-age=31536000" in response["Strict-Transport-Security"]
    assert client.post("/accounts/login/", {}, **https).status_code == 403
    assert client.get("/accounts/profile/", **https).status_code == 302
    assert client.get("/missing-page/", **https).status_code == 404

    response = client.get(staticfiles_storage.url("css/homeward.css"), **https)
    assert response.status_code == 200
    assert "immutable" in response["Cache-Control"]
    response.close()

    # This is the only real database query: read-only SELECT 1 through the health endpoint.
    assert client.get("/health/", **https).status_code == 200
    with patch("homeward.views.connection.cursor", side_effect=OperationalError("private detail")):
        response = client.get("/health/", **https)
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable"}

    print("Production checks passed: HTTPS, CSRF, secure cookies, static files, errors, and Supabase health.")
    print("No application data or migrations were created.")


if __name__ == "__main__":
    main()
