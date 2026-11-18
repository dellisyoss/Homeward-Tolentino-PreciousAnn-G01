# Homeward

Homeward: Lost Pet Alert & Street Sighting Tracker. Full-stack Django project
for IM2 Project Development 1, adapted from the `campusconnect reference` beside
this project, with simple Bootstrap templates and Supabase PostgreSQL.

## Increment 5: production settings and deployment preparation

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

Previously implemented: case-insensitive email login, session logout,
Member and Administrator dashboards, and server-side role checks. Every login
goes to the user's own dashboard. Logged-out users are redirected to login;
authenticated users requesting the other role's dashboard receive HTTP 403.
Logout is a CSRF-protected POST action. Navbar links match the user's role.

Previously implemented: own-profile viewing and editing, plus a custom
administrator user-management panel. Profiles can update name, email, and contact
number, while roles and authentication flags are excluded from profile forms.
The panel lists/searches accounts, creates Members or Administrators with hashed
passwords, and edits details, role, and active status. Deactivation preserves
records and prevents login and access to protected pages. Reactivation restores
access. There is no hard-delete action.

Administrators edit their own details through My profile, so they cannot disable
or demote themselves in the panel. Accounts created with `createsuperuser` are
protected from panel edits; their owners can still update their own profiles.
Panel-created administrators use the Homeward `ADMIN` role, with no Django
superuser or staff privileges. The built-in Django admin remains disabled.

Production settings, HTTPS/secure cookies, static-file serving, friendly error
pages, and a database health endpoint are now included. `render.yaml` defines a
Render Free Python service deploying `main`, with Supabase remaining the database.
The application code for the account phase is implemented; the hosted deployment
is not yet verified. Follow [DEPLOYMENT.md](DEPLOYMENT.md) to finish publishing
and check the actual live URL before submitting.

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
redirects to login with a success message.
Try missing required fields, invalid email, mismatched/weak passwords, and
registering the same email again with different capitalization.

## Verify profiles and user management

No new packages or database migrations are needed for increment 4.

1. Log in as a Member and open **My profile** at `/accounts/profile/`.
2. Choose **Edit profile**, change your name/contact number, and save.
3. Change your email and verify that you remain logged in. After logout, use
   the new email to log in. Another account's email must be rejected, including
   different capitalization of it.
4. Open `/accounts/manage/users/` as a Member; access must be denied.
5. Log in as an Administrator and choose **Manage users**. Search by email/name,
   create a test Member, and edit its details. Passwords are set on creation;
   editing user details leaves the existing password unchanged.
6. Clear **Active account** on the test user and save. That user must be unable
   to log in or use an existing session to open protected pages. Re-enable it to
   restore access. The user row is kept throughout.
7. The panel also supports creating/promoting another Administrator. The current
   administrator's own row links to My profile, and protected administrator
   accounts have no panel edit link. Forged requests to edit them return 403.

Profile URLs never take a user ID; they always refer to the logged-in user.
Management URLs take a user ID but are restricted to the Administrator role.
All save forms require CSRF tokens, and GET requests do not change account data.

## Verify login and dashboards

No new packages or database migrations are needed if increment 2's migrations
have already been applied.

1. Register a Member at `/accounts/signup/`.
2. Log in at `/accounts/login/`; the Member dashboard is `/dashboard/member/`.
3. As a Member, request `/dashboard/admin/` directly; access must be denied.
4. Click Logout, then request `/dashboard/member/` again; it must send you to login.
5. Create an Administrator from the terminal if you do not already have one:

   ```powershell
   .\.venv\Scripts\python.exe manage.py createsuperuser
   ```

   Enter an email, full name, and password at the prompts. Our custom manager
   assigns the `ADMIN` role. This command creates an account; it does not enable
   Django's built-in admin site, which remains unavailable at `/admin/`.

6. Log in with that administrator account. It opens `/dashboard/admin/`, showing
   account totals. Direct access to `/dashboard/member/` must be denied.

The dashboard entry point `/dashboard/` routes either role to its own page.
Login always uses that entry point; a submitted `next` URL cannot send a user
to another role's dashboard or an external site.

Run the account regression and permission tests:

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

## GitHub workflow for the final increment

Repository: `https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01`.
Keep it public. The previous four increments are merged into `main`.
Increment 5 belongs on `feature/production-deployment`, as the original instructions
require subsequent updates through branches and pull requests.

```powershell
git status
git add .env.example .gitattributes .python-version requirements.txt build.sh render.yaml homeward/settings.py homeward/production.py homeward/urls.py homeward/views.py homeward/tests.py templates/base.html templates/404.html templates/500.html static scripts/test_accounts.py scripts/check_production.py README.md DEPLOYMENT.md
git diff --cached --stat
git commit -m "Prepare production settings and Render deployment"
git push -u origin feature/production-deployment
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

## Remaining submission steps

1. Review/commit this increment and merge its pull request into `main`.
2. Deploy the merged `main` on Render using [DEPLOYMENT.md](DEPLOYMENT.md).
3. Verify the hosted account flows and keep the actual public URL for submission.

Each increment should be reviewed and committed before starting the next.
Public registration creates Members only. The SDD's reference to an "admin site"
will be implemented as custom Django templates and views, because the assignment
prohibits the built-in Django admin. Pet cases, sightings, zones, and reports
remain outside this account phase; a shelter directory is excluded by the SDD.

## Deployment target

The configured host is **Render**, with Supabase remaining the database. The
production settings module is `homeward.production`. Local development continues
to use `homeward.settings`. WhiteNoise serves the collected static assets, and
Gunicorn runs Django on Render. No SQLite database is configured.

You need GitHub, Supabase, and Render accounts. Keep credentials in `.env` locally
and Render's environment-variable settings in production. The GitHub repository
root is the local `Homeward/homeward` folder, so leave Render's Root Directory
blank. See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete numbered setup steps.

References: [Supabase database connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[Supabase Data API settings](https://supabase.com/docs/guides/api/securing-your-api),
[Render Django deployment](https://render.com/docs/deploy-django).

## Project Development 2 · Lost-pet case management (F-02)

With your Supabase database credentials in `.env`, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 8001
```

1. As an Administrator, open **Manage zones** and add a zone.
2. As a Member, open **Report a lost pet**. Enter the pet's details, the time
   lost in Philippine time, and the last-known location. Choose a zone and
   save. One JPEG, PNG, or WebP photo is optional (up to 2 MB and 12 megapixels).
3. Open **Browse active cases** to view Lost or Stale cases. Choose **My cases**
   to see your own cases at any status.
4. From a case you own, choose **Edit case** to correct details, change its
   status, or replace or remove its photo. Choose **Delete case** and confirm
   to permanently remove it. Administrators can edit and delete any case.

Django saves cases, zones, and status history in Supabase PostgreSQL. Each
new case starts as Lost. Status history records who changed the status and
when, and a Closed case cannot be reopened. Homeward stores resized JPEGs in
PostgreSQL in place of the SDD's photo URL, so photos survive Render restarts
and follow the same viewing permissions as the case.
