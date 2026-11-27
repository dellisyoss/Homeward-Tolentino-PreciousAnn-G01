from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from accounts.models import User
from .models import CaseStatusHistory, LostPetCase, Species, Status, Zone


class LostPetCaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(email="owner@example.test", full_name="Case Owner")
        cls.other_member = User.objects.create_user(
            email="neighbor@example.test", full_name="Neighborhood Member",
        )
        cls.admin = User.objects.create_superuser(email="admin@example.test", full_name="Administrator")
        cls.zone = Zone.objects.create(zone_name="Central")

    def setUp(self):
        self.client.force_login(self.owner)

    def report_data(self, **changes):
        return {
            "pet_name": "Pip",
            "species": Species.DOG,
            "color": "Brown",
            "zone": self.zone.pk,
            "last_known_location": "Central park",
            "lost_at": (timezone.localtime() - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S"),
            **changes,
        }

    def new_report_data(self, **changes):
        form = self.client.get(reverse("cases:create")).context["form"]
        return self.report_data(submission_key=form["submission_key"].value()) | changes

    def existing_case(self, **changes):
        data = self.report_data()
        data.update(owner=self.owner, zone=self.zone, lost_at=timezone.now() - timedelta(hours=2))
        return LostPetCase.objects.create(**(data | changes))

    def test_member_creates_case_and_history(self):
        response = self.client.post(reverse("cases:create"), self.new_report_data(), follow=True)

        case = LostPetCase.objects.get()
        self.assertEqual(case.owner, self.owner)
        self.assertEqual(case.zone, self.zone)
        self.assertEqual(case.status, Status.LOST)
        self.assertRedirects(response, reverse("cases:detail", args=[case.pk]))
        self.assertContains(response, "Lost-pet case created.")
        history = case.status_history.get()
        self.assertIsNone(history.old_status)
        self.assertEqual(history.new_status, Status.LOST)
        self.assertEqual(history.changed_by, self.owner)

    def test_future_lost_time_is_rejected(self):
        future = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.client.post(reverse("cases:create"), self.new_report_data(lost_at=future))

        self.assertFormError(response.context["form"], "lost_at", "The time lost cannot be in the future.")
        self.assertFalse(LostPetCase.objects.exists())
        self.assertFalse(CaseStatusHistory.objects.exists())

    def test_invalid_photo_is_rejected(self):
        photo = SimpleUploadedFile("pet.png", b"not an image", content_type="image/png")
        response = self.client.post(reverse("cases:create"), self.new_report_data(photo=photo))

        self.assertFormError(response.context["form"], "photo", "Choose a valid JPEG, PNG, or WebP photo.")
        self.assertFalse(LostPetCase.objects.exists())

    def test_valid_photo_is_stored_and_served_as_jpeg(self):
        original = BytesIO()
        Image.new("RGB", (20, 20), "brown").save(original, format="PNG")
        photo = SimpleUploadedFile("pet.png", original.getvalue(), content_type="image/png")
        self.client.post(reverse("cases:create"), self.new_report_data(photo=photo))

        case = LostPetCase.objects.get()
        response = self.client.get(reverse("cases:photo", args=[case.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertEqual(response.content, bytes(case.photo_data))
        with Image.open(BytesIO(response.content)) as stored:
            self.assertEqual(stored.format, "JPEG")

    def test_all_case_and_zone_views_require_login(self):
        case = self.existing_case()
        routes = [reverse(f"cases:{name}") for name in ("list", "create", "zones")]
        routes.append(reverse("cases:zone_edit", args=[self.zone.pk]))
        routes.extend(
            reverse(f"cases:{name}", args=[case.pk])
            for name in ("detail", "photo", "update", "delete")
        )
        guest = Client()
        for route in routes:
            with self.subTest(route=route):
                self.assertRedirects(
                    guest.get(route), f"{reverse('login')}?next={route}", fetch_redirect_response=False,
                )

    def test_member_can_browse_another_members_active_summary(self):
        active = self.existing_case(description="Private identifying details")
        self.existing_case(pet_name="Closed report", status=Status.CLOSED)
        self.client.force_login(self.other_member)

        response = self.client.get(reverse("cases:list"))
        self.assertContains(response, active.pet_name)
        self.assertNotContains(response, reverse("cases:detail", args=[active.pk]))
        self.assertNotContains(response, active.description)
        self.assertNotContains(response, "Closed report")
        self.assertNotContains(self.client.get(reverse("cases:list"), {"view": "mine"}), active.pet_name)

    def test_member_cannot_view_another_members_active_case(self):
        case = self.existing_case(photo_data=b"case photo")
        self.client.force_login(self.other_member)

        for name in ("detail", "photo"):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(f"cases:{name}", args=[case.pk])).status_code, 404)

    def test_member_cannot_edit_or_delete_another_members_case(self):
        case = self.existing_case()
        self.client.force_login(self.other_member)

        for name in ("update", "delete"):
            with self.subTest(name=name):
                url = reverse(f"cases:{name}", args=[case.pk])
                self.assertEqual(self.client.get(url).status_code, 404)
                self.assertEqual(self.client.post(url, self.report_data(status=Status.FOUND)).status_code, 404)
        case.refresh_from_db()
        self.assertEqual(case.status, Status.LOST)
        self.assertFalse(case.status_history.exists())

    def test_roles_control_reporting_zone_management_and_admin_case_access(self):
        case = self.existing_case()
        zones = reverse("cases:zones")
        self.assertEqual(self.client.get(zones).status_code, 403)
        self.assertEqual(self.client.post(zones, {"zone_name": "Unauthorized"}).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(zones).status_code, 200)
        self.assertEqual(self.client.get(reverse("cases:detail", args=[case.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("cases:delete", args=[case.pk])).status_code, 200)
        create = reverse("cases:create")
        self.assertEqual(self.client.get(create).status_code, 403)
        self.assertEqual(self.client.post(create, self.report_data()).status_code, 403)
        self.assertFalse(Zone.objects.filter(zone_name="Unauthorized").exists())

    def test_case_and_zone_posts_require_csrf(self):
        secure_client = Client(enforce_csrf_checks=True)
        secure_client.force_login(self.owner)
        case = self.existing_case()
        case_routes = [
            reverse("cases:create"),
            reverse("cases:update", args=[case.pk]),
            reverse("cases:delete", args=[case.pk]),
        ]
        for route in case_routes:
            with self.subTest(route=route):
                self.assertContains(secure_client.get(route), 'name="csrfmiddlewaretoken"')
                self.assertEqual(secure_client.post(route, {}).status_code, 403)

        secure_client.force_login(self.admin)
        zones = reverse("cases:zones")
        self.assertContains(secure_client.get(zones), 'name="csrfmiddlewaretoken"')
        self.assertEqual(secure_client.post(zones, {"zone_name": "Missing token"}).status_code, 403)
        self.assertEqual(LostPetCase.objects.count(), 1)
        self.assertEqual(Zone.objects.count(), 1)

    def test_closed_case_cannot_reopen(self):
        case = self.existing_case(status=Status.CLOSED)
        edit = reverse("cases:update", args=[case.pk])
        response = self.client.post(edit, self.report_data(status=Status.LOST))

        self.assertFormError(response.context["form"], "status", "This case cannot change to that status.")
        case.refresh_from_db()
        self.assertEqual(case.status, Status.CLOSED)
        self.assertFalse(case.status_history.exists())

    def test_status_change_records_history_once(self):
        case = self.existing_case()
        edit = reverse("cases:update", args=[case.pk])
        data = self.report_data(status=Status.FOUND)
        response = self.client.post(edit, data)
        self.assertRedirects(response, reverse("cases:detail", args=[case.pk]))
        self.assertEqual(self.client.post(edit, data).status_code, 302)

        case.refresh_from_db()
        self.assertEqual(case.status, Status.FOUND)
        change = case.status_history.get()
        self.assertEqual((change.old_status, change.new_status), (Status.LOST, Status.FOUND))
        self.assertEqual(change.changed_by, self.owner)

    def test_delete_requires_confirmation_and_removes_history(self):
        case = self.existing_case()
        CaseStatusHistory.objects.create(case=case, new_status=Status.LOST, changed_by=self.owner)
        delete = reverse("cases:delete", args=[case.pk])

        self.assertContains(self.client.get(delete), "This permanently deletes the case")
        self.assertTrue(LostPetCase.objects.filter(pk=case.pk).exists())
        self.assertEqual(case.status_history.count(), 1)
        response = self.client.post(delete)
        self.assertRedirects(response, reverse("cases:list", query={"view": "mine"}))
        self.assertFalse(LostPetCase.objects.filter(pk=case.pk).exists())
        self.assertFalse(CaseStatusHistory.objects.filter(case_id=case.pk).exists())

    def test_repeated_report_redirects_to_the_original_case(self):
        create = reverse("cases:create")
        data = self.new_report_data()
        first_response = self.client.post(create, data)
        self.assertEqual(first_response.status_code, 302)
        retry = self.client.post(create, data, follow=True)

        self.assertRedirects(retry, first_response.url)
        self.assertContains(retry, "This case was already submitted.")
        self.assertEqual(LostPetCase.objects.count(), 1)
        self.assertEqual(CaseStatusHistory.objects.count(), 1)
        self.assertEqual(self.client.post(create, self.new_report_data()).status_code, 302)
        self.assertEqual(LostPetCase.objects.count(), 2)

    def test_duplicate_zone_name_is_rejected(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("cases:zones"), {"zone_name": self.zone.zone_name})

        self.assertFormError(response.context["form"], "zone_name", "That zone name already exists.")
        self.assertEqual(Zone.objects.count(), 1)

    @override_settings(DEBUG=False)
    def test_invalid_case_ids_use_the_custom_404(self):
        for route in ("/cases/invalid-id/", reverse("cases:detail", args=[2**63])):
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertContains(response, "Page not found", status_code=404)
                self.assertTemplateUsed(response, "404.html")

    @override_settings(DEBUG=False)
    def test_failed_history_write_rolls_back_case_creation(self):
        self.client.raise_request_exception = False
        data = self.new_report_data()
        with patch.object(CaseStatusHistory.objects, "create", side_effect=IntegrityError("History write failed")):
            with self.assertLogs("django.request", level="ERROR"):
                response = self.client.post(reverse("cases:create"), data)

        self.assertEqual(response.status_code, 500)
        self.assertFalse(LostPetCase.objects.exists())
        self.assertFalse(CaseStatusHistory.objects.exists())
