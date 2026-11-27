from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse


class HealthTests(SimpleTestCase):
    @patch("homeward.views.connection")
    def test_health_checks_database_and_disables_caching(self, database):
        database.cursor.return_value.__enter__.return_value.fetchone.return_value = (1,)
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("no-store", response["Cache-Control"])
        database.cursor.return_value.__enter__.return_value.execute.assert_called_once_with("SELECT 1")

    @patch("homeward.views.connection")
    def test_database_failure_does_not_expose_connection_details(self, database):
        database.cursor.side_effect = OperationalError("private connection details")
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "private connection details", status_code=503)

    def test_health_does_not_accept_post(self):
        self.assertEqual(self.client.post(reverse("health")).status_code, 405)


@override_settings(DEBUG=False)
class ErrorPageTests(SimpleTestCase):
    def test_missing_page_uses_friendly_template(self):
        response = self.client.get("/missing-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "URLconf", status_code=404)

    @patch(
        "django.templatetags.static.StaticNode.handle_simple",
        side_effect=RuntimeError("private static file failure"),
    )
    def test_server_error_page_renders_when_static_file_resolution_fails(self, static_url):
        client = Client(raise_request_exception=False)
        with self.assertLogs("django.request", level="ERROR"):
            response = client.get(reverse("home"))

        static_url.assert_called_once()
        self.assertTemplateUsed(response, "500.html")
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertNotContains(response, "private static file failure", status_code=500)
