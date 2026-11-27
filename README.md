# Homeward

Homeward is a Lost Pet Alert & Street Sighting Tracker built for IM2. Django
handles the backend and renders the frontend through Django templates. The app
uses Supabase PostgreSQL for accounts, sessions, and lost-pet records, and runs
on Render. Python 3.15.2 is pinned in [`.python-version`](.python-version), and
Django 6.1.3 and the other dependencies are pinned in
[`requirements.txt`](requirements.txt).

[Live app on Render](https://homeward-pbjg.onrender.com/) ·
[Public GitHub repository](https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01) ·
[PD2 completion report](docs/Homeward-Tolentino-PreciousAnn-G01-PD2.pdf)

## Project Development 1 — Account Feature

- Registration creates a Member with a case-insensitive unique email, a required
  full name, and an optional contact number. Django validates matching passwords,
  stores a password hash, and displays validation errors or confirmation.
- Members and Administrators sign in by email and land on their own dashboards.
  Protected pages redirect visitors to login. Role checks reject requests for
  the other role's dashboard. Logout ends the session.
- Users view and edit their own name, email, and contact number in **My profile**.
  Administrators use **Manage users** to search, create, edit, deactivate, and
  reactivate accounts through Homeward's custom interface.

## Project Development 2 — Lost-Pet Case Management (F-02)

Members can report, browse, edit, and delete lost-pet cases through the Django
interface. The `cases` app links each case to its owner and zone through foreign
keys. Supabase stores the case, its optional photo, and its status history.

1. As an Administrator, open **Manage zones** and add a zone if the database
   has none. A zone is required before a Member can submit a case.
2. As a Member, use **Report a lost pet**. Enter the pet details, the last-known
   location, and the time lost in Philippine time. The form rejects future dates
   and validates the optional JPEG, PNG, or WebP photo (up to 2 MB and 12 megapixels).
3. Use **Browse active cases** to see summaries of Lost and Stale cases.
   **My cases** shows your own reports at every status.
4. Open a case you own to see its full details, photo, and status history, or
   to edit or delete it. Administrators can access and manage any case. Each
   new case starts as Lost. Status changes record who made the change and
   when. Closed cases stay closed.

PD2 also added password reset. Locally, **Forgot your password?** prints the
reset email in the Django terminal. On Render, delivery uses Resend when
`RESEND_API_KEY` and `PASSWORD_RESET_FROM_EMAIL` are configured. For the PD2 Git
history, see the
[case feature PR into `develop`](https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01/pull/8)
and the [PD2 integration PR into `main`](https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01/pull/9).

## Set up or resume locally

Run the following commands in Windows PowerShell. The repository root is the
folder containing `manage.py`. The existing checkout in this workspace is
`Homeward/homeward`.

### 1. Clone or update the repository

For a fresh checkout, run these commands from the parent folder where you want
the new `homeward` folder.

```powershell
git clone https://github.com/dellisyoss/Homeward-Tolentino-PreciousAnn-G01.git homeward
Set-Location homeward
```

For an existing checkout, open its repository root and review `git status`
before switching branches. Keep any local work and the existing `.env`.

```powershell
git status --short --branch
git switch main
git pull --ff-only origin main
```

If Git reports local changes that would be overwritten or a diverged branch,
resolve that state while preserving the local work before continuing.

### 2. Install the pinned dependencies

Install Python 3.15.2 if needed. Create the virtual environment on a fresh
checkout and reinstall dependencies after updating the repository.

```powershell
if (-not (Test-Path .venv/Scripts/python.exe)) { py -3.15 -m venv .venv }
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the Python launcher opens the Microsoft Store, use the installed interpreter
directly to create the environment, then rerun the dependency install.

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.15-64\python.exe" -m venv .venv
```

### 3. Configure `.env` and Supabase

Reuse the working `.env` from your existing checkout if you are authorized to
use the same database. On a fresh checkout, copy that file privately or create
one from [`.env.example`](.env.example). Fill in the real values before running Django.

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

- Set `DJANGO_DEBUG=True` and `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` for
  local development. For a new `DJANGO_SECRET_KEY`, run the command below and
  paste the result in single quotes in `.env`.
- In the authorized Supabase project's **Connect** dialog, select **Session pooler**.
  Copy the exact host and username to `DB_HOST` and `DB_USER`. Set `DB_PASSWORD`
  to the project's database password in single quotes. Keep `DB_NAME=postgres`,
  `DB_PORT=5432`, and `DB_SSLMODE=require`. Django connects directly to PostgreSQL.
- Keep `.env`, other secret files, `.venv/`, and Python caches out of Git.
  Review staged files before pushing to the public repository.

```powershell
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

See the [Supabase connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).

### 4. Check, migrate, and run

Run each command in order. Review the migration plan and confirm which Supabase
database you are connected to before applying any pending migrations. A local
server pointed at the deployed database shares its data with the Render app.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py migrate --plan
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Open [local login](http://127.0.0.1:8001/accounts/login/),
[local registration](http://127.0.0.1:8001/accounts/signup/), or
[local database health](http://127.0.0.1:8001/health/). The health endpoint
should return HTTP 200 with `{"status": "ok"}`. If port 8001 is in use,
pick an available port and update the browser URL. Press Ctrl+C to stop Django.

For a smoke test, use a test database or designated test accounts. Check
registration, login, logout, profile editing, and both dashboards, then follow
the PD2 case workflow above. An authorized maintainer can create an initial
Administrator with `manage.py createsuperuser` when setting up an empty database.
The account regression script uses a temporary schema in the configured database.

```powershell
.\.venv\Scripts\python.exe scripts/test_accounts.py
```

## Project Development 3 handoff

Start from the PD2 baseline on `main`. Read the PD3 assignment and the approved
SDD before choosing the next feature. Verify the existing account and case flows
using the setup above.

`main` is the stable deployment branch and `develop` is the integration branch.
Fetch both before starting. If `git log` below lists commits, bring `main` into
`develop` with a pull request so the feature branch includes the current baseline.

```powershell
git fetch origin
git log --oneline origin/develop..origin/main
```

After `develop` includes the baseline, replace `your-feature-name` below with
the assigned feature name. On a fresh clone, `git switch develop` creates a
local tracking branch from `origin/develop`.

```powershell
git switch develop
git pull --ff-only origin develop
git switch -c feature/your-feature-name
```

Commit progress with clear messages and push the feature branch. Open a feature
PR into `develop`, then open a `develop` PR into `main` once the increment is
ready. Keep merged feature branches. The PD2 assignment specified a minimum of
two feature branches, two merged PRs into `develop`, and one merged PR from
`develop` into `main`. Use the PD3 brief for its submission requirements.

## Render deployment

[`render.yaml`](render.yaml) defines the Python web service. Render deploys
`main` automatically. [`build.sh`](build.sh) installs dependencies, runs
production checks, collects static files, and applies Django migrations.
Gunicorn loads the Django app with `homeward.production` settings. WhiteNoise
serves static files. Supabase stores application data and pet photos.

Manage production credentials in the Render dashboard. After a merge to
`main`, confirm the deployment and check the
[live database health endpoint](https://homeward-pbjg.onrender.com/health/).
