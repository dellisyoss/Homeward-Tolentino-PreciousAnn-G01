# Homeward

Homeward: Lost Pet Alert & Street Sighting Tracker. Full-stack Django project
for IM2 Project Development 1, adapted from the `campusconnect reference` beside
this project, with simple Bootstrap templates and Supabase PostgreSQL.

## Increment 2: email accounts and registration

Implemented: project setup and public registration with a unique email, required
full name, optional contact number, and matching validated passwords. Django
hashes passwords. Accounts default to Member; registration cannot assign admin
permissions. Owners and community participants share the Member role.

The custom `accounts.User` model maps to the SDD's `users` table. Its Python
`password` field stores Django's encoded hash in `password_hash`, and
`date_joined` maps to `created_at`. Django uses a bigint identity for `user_id`
and timezone-aware timestamps, and adds its standard authentication fields.
Email uniqueness is also enforced case-insensitively in PostgreSQL; a database
check restricts roles to `MEMBER` and `ADMIN`.

Login/logout, protected dashboards, profile editing, custom user administration,
and deployment are still upcoming. This is not the completed submission.

Use Python 3.15 with Django 6.1.3, matching the reference environment.
From this folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

If `py` or `python` opens the Microsoft Store, use the installed interpreter:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.15-64\python.exe" -m venv .venv
```

Generate a secret key, then paste the output into `DJANGO_SECRET_KEY` in `.env`:

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Wrap the secret in single quotes in `.env`. Never commit `.env`.
If `.env` already exists, edit it instead of copying over it.

## Supabase setup

1. Create a Supabase project and save its database password privately.
2. Open **Connect**, select **Session pooler**, and use port **5432**.
3. Copy the exact host and username shown there into `DB_HOST` and `DB_USER`
   in `.env`. The username usually looks like `postgres.YOUR_PROJECT_REF`.
4. Set `DB_PASSWORD` to the database password, wrapped in single quotes.
   Leave `DB_NAME=postgres`, `DB_PORT=5432`, and `DB_SSLMODE=require`.
5. For a database used only by this Django app, disable the Supabase Data API
   in the project's API settings. Django connects directly to PostgreSQL;
   it does not need the REST API or any Supabase API keys.

Use the pooler host from your own project's Connect dialog. Do not guess it.
No Supabase Auth configuration or JavaScript database client is needed.
Keep the password exactly as created; these separate fields need no URL encoding.

Run the configuration check:

```powershell
.\.venv\Scripts\python.exe manage.py check
```

This checks Django configuration; it does not verify the database connection.
To check the real connection without creating tables:

```powershell
.\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('PostgreSQL connection OK')"
```

The custom user model is now configured before the first migration. Create the
tables using the committed Django migrations (not the Supabase SQL editor):

```powershell
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
```

The migrations enable Row Level Security on the Django account, permission,
session, and migration tables. No policies grant Supabase API users access to
these private records. Django connects as the server-side database role, which
can manage them. Keep the Data API disabled for this Django-only project.

Start the development server:

```powershell
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/accounts/signup/ to register. Successful registration
returns to the home page with a success message. Login is a later increment.
Try missing required fields, invalid email, mismatched/weak passwords, and
registering the same email again with different capitalization.

## Verify increment 2

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts/test_accounts.py
```

The test script creates a uniquely named temporary schema in your PostgreSQL
database, runs Django's account tests there, and removes that schema in a
`finally` block. It does not create test users in your application's tables or
need permission to create a separate database. The schema name is printed so it
can be identified if the process is forcibly stopped before cleanup. Use this
script for Supabase instead of plain `manage.py test`.

## GitHub workflow

Repository: `https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01`.
Keep it public. The initial commit and setup PR are already on `main`.
Increment 2 belongs on `feature/email-accounts`, as the original instructions
require subsequent updates through branches and pull requests.

```powershell
git status
git add accounts homeward/settings.py homeward/urls.py templates/base.html templates/registration/signup.html scripts/test_accounts.py README.md
git diff --cached --stat
git commit -m "Add email-based user model and registration"
git push -u origin feature/email-accounts
```

Review the staged files before committing. `.env`, `.venv/`, `venv/`, and
`__pycache__/` must not be included.

Open a pull request into `main`, review and merge it on GitHub, then:

```powershell
git switch main
git pull --ff-only origin main
```

Repeat with a new branch and pull request for each following increment. Keep
real progress commits; do not manufacture or backdate history. The final version
must be merged into `main`.

## Remaining increments

1. Login/logout, protected Member/Admin dashboards, and permission checks.
2. Own-profile viewing/editing and a custom administrator user management panel.
3. Remaining account/permission tests, production settings, and Render deployment.

Each increment should be reviewed and committed before starting the next.
Public registration creates Members only. The SDD's reference to an "admin site"
will be implemented as custom Django templates and views, because the assignment
prohibits the built-in Django admin. Pet cases, sightings, zones, and reports
remain outside this account phase; a shelter directory is excluded by the SDD.

## Deployment target

The proposed host is **Render**, with Supabase remaining the database. Blender
is a 3D application. Deployment configuration will be added after the account
features so that the final merged `main` can be deployed and verified.
You will need GitHub, Supabase, and Render accounts; keep credentials in `.env`
locally and the host's environment-variable settings in production.

References: [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Supabase Data API settings](https://supabase.com/docs/guides/api/securing-your-api),
[Render Django deployment](https://render.com/docs/deploy-django).
