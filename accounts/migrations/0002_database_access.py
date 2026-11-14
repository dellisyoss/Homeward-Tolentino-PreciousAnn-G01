from django.db import migrations


# Django authenticates users on the server. Supabase's API roles must not read
# passwords or sessions, even if the project's Data API is later enabled.
TABLES = (
    "users",
    "users_groups",
    "users_user_permissions",
    "auth_group",
    "auth_group_permissions",
    "auth_permission",
    "django_content_type",
    "django_session",
    "django_migrations",
)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("sessions", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;',
            reverse_sql=migrations.RunSQL.noop,
        )
        for table in TABLES
    ]
