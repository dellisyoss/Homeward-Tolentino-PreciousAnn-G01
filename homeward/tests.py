from unittest.mock import patch

from django.db import OperationalError
from django.test import SimpleTestCase, override_settings
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
    def test_missing_page_uses_friendly_template(self):
        response = self.client.get("/missing-page/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")
        self.assertNotContains(response, "URLconf", status_code=404)
