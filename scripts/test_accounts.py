"""Run Django's account tests in a disposable PostgreSQL schema.

Supabase usually cannot create Django's separate test database. This runner
uses a unique schema in the configured database and removes only that schema.
"""
import os
from pathlib import Path
import sys
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "homeward.settings")

import django
import psycopg
from psycopg import sql

django.setup()

from django.conf import settings
from django.db import connection, connections
from django.test.runner import DiscoverRunner


def main():
    schema = "homeward_test_" + uuid4().hex
    database = settings.DATABASES["default"]
    # Separate connection stays outside Django's test runner for final cleanup.
    with psycopg.connect(
        dbname=database["NAME"],
        user=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=database["PORT"],
        sslmode=database["OPTIONS"]["sslmode"],
        connect_timeout=10,
        autocommit=True,
    ) as maintenance:
        maintenance.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        print("Testing in disposable schema:", schema, flush=True)
        try:
            connection.close()
            database["OPTIONS"]["options"] = f"-c search_path={schema}"
            database["TEST"]["NAME"] = database["NAME"]
            connection.settings_dict["OPTIONS"] = database["OPTIONS"]
            connection.settings_dict["TEST"]["NAME"] = database["NAME"]
            # Verify isolation before the runner applies any migrations.
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_schema()")
                if cursor.fetchone()[0] != schema:
                    raise RuntimeError("Test schema isolation failed; stopped.")
            labels = sys.argv[1:] or ["accounts"]
            failures = DiscoverRunner(verbosity=2, interactive=False, keepdb=True).run_tests(labels)
        finally:
            connections.close_all()
            maintenance.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            print("Removed disposable test schema.", flush=True)
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
