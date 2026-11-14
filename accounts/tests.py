from unittest.mock import patch

from django.contrib.auth import authenticate
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import RegistrationForm
from .models import User


class RegistrationTests(TestCase):
    def data(self, **changes):
        data = {
            "email": "neighbor@example.com",
            "full_name": "Alex Rivera",
            "contact_number": "09123456789",
            "password1": "River-Trail!8427",
            "password2": "River-Trail!8427",
        }
        data.update(changes)
        return data

    def test_signup_page_has_csrf_and_no_role_selector(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertNotContains(response, 'name="role"')

    def test_registration_hashes_password_and_normalizes_email(self):
        response = self.client.post(reverse("signup"), self.data(email="NEIGHBOR@Example.com"), follow=True)
        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Your account was created successfully.")
        user = User.objects.get(email="neighbor@example.com")
        self.assertTrue(user.check_password(self.data()["password1"]))
        self.assertNotEqual(user.password, self.data()["password1"])
        self.assertEqual(user.full_name, "Alex Rivera")
        self.assertEqual(user.role, User.Role.MEMBER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_public_registration_ignores_privilege_fields(self):
        self.client.post(reverse("signup"), self.data(role="ADMIN", is_staff="true", is_superuser="true"))
        user = User.objects.get()
        self.assertEqual(user.role, User.Role.MEMBER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_contact_number_is_optional(self):
        form = RegistrationForm(data=self.data(contact_number=""))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save().contact_number, "")

    def test_required_fields(self):
        for field in ("email", "full_name", "password1", "password2"):
            with self.subTest(field=field):
                form = RegistrationForm(data=self.data(**{field: ""}))
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_invalid_email(self):
        form = RegistrationForm(data=self.data(email="not-an-email"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_mismatched_passwords(self):
        form = RegistrationForm(data=self.data(password2="Different!4829"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_weak_password(self):
        for password in ("short", "123456789", "password"):
            with self.subTest(password=password):
                form = RegistrationForm(data=self.data(password1=password, password2=password))
                self.assertFalse(form.is_valid())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user("neighbor@example.com", "Existing!8921", full_name="Existing Member")
        response = self.client.post(reverse("signup"), self.data(email="NEIGHBOR@example.com"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_form_creates_no_user(self):
        response = self.client.post(reverse("signup"), self.data(password2="different"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)

    def test_post_requires_csrf(self):
        from django.test import Client

        response = Client(enforce_csrf_checks=True).post(reverse("signup"), self.data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 0)

    def test_database_rejects_case_variant_duplicate_even_without_model_save(self):
        User.objects.create_user("neighbor@example.com", full_name="Alex Rivera")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="NEIGHBOR@example.com", full_name="Other Member")])

    def test_database_rejects_unknown_role(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user("invalid@example.com", full_name="Invalid Role", role="OWNER")

    def test_duplicate_registration_race_shows_form_error(self):
        # Simulate another request inserting the same email after validation.
        User.objects.create_user("neighbor@example.com", full_name="Existing Member")
        with patch.object(RegistrationForm, "clean_email", return_value="neighbor@example.com"), patch.object(
            RegistrationForm, "validate_unique"
        ), patch.object(User, "validate_constraints"):
            response = self.client.post(reverse("signup"), self.data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "An account with this email already exists.")

    def test_email_authentication_uses_django(self):
        user = User.objects.create_user("neighbor@example.com", self.data()["password1"], full_name="Alex Rivera")
        self.assertEqual(authenticate(email=user.email, password=self.data()["password1"]), user)
        self.assertIsNone(authenticate(email=user.email, password="wrong-password"))

    def test_superuser_has_admin_role(self):
        user = User.objects.create_superuser("admin@example.com", "Admin-Pass!8432", full_name="Admin User")
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_superuser_rejects_conflicting_flags(self):
        for changes in ({"is_staff": False}, {"is_superuser": False}, {"role": "MEMBER"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                User.objects.create_superuser("admin@example.com", full_name="Admin User", **changes)

    def test_manager_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("   ", full_name="Alex Rivera")

    def test_django_admin_is_unavailable(self):
        self.assertEqual(self.client.get("/admin/").status_code, 404)

    def test_account_and_session_tables_have_rls(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT relname, relrowsecurity FROM pg_class "
                "WHERE relnamespace = current_schema()::regnamespace "
                "AND relname IN ('users', 'users_groups', 'users_user_permissions', 'django_session')"
            )
            rows = cursor.fetchall()
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(enabled for name, enabled in rows))
