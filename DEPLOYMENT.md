# Deploy Homeward on Render

The application is prepared for deployment. A live deployment is **not verified
yet**. Finish the steps below, then keep the actual Render URL for submission.

## 1. Merge the deployment increment

From the application folder in PowerShell:

```powershell
git status
git add .env.example .gitattributes .python-version requirements.txt build.sh render.yaml homeward/settings.py homeward/production.py homeward/urls.py homeward/views.py homeward/tests.py templates/base.html templates/404.html templates/500.html static scripts/test_accounts.py scripts/check_production.py README.md DEPLOYMENT.md
git diff --cached --stat
git commit -m "Prepare production settings and Render deployment"
git push -u origin feature/production-deployment
```

Create a pull request from `feature/production-deployment` into `main`, review it,
and merge it. Then:

```powershell
git switch main
git pull --ff-only origin main
```

Do not stage `.env`, `.venv/`, `staticfiles/`, or Python cache folders. The
provided `.gitignore` excludes them. The SDD PDF is not needed for deployment.

## 2. Create the Render service

1. Sign up or log in at https://dashboard.render.com, using GitHub if convenient.
2. Choose **New > Blueprint**.
3. Connect `dellisyoss/Homeward-Tolentino-PreciousAnn-G01`.
4. Select branch **main**, and keep **Blueprint Path** as `render.yaml`.
5. If asked for a Root Directory, leave it blank. The GitHub repository already
   starts in your local `Homeward/homeward` folder; `manage.py` is at its root.
6. Render will read the service settings from `render.yaml`. Review that it is
   one **Python web service on the Free plan**, with no Render database.
7. Enter the requested database values privately:

   | Variable | Value |
   | --- | --- |
   | `DB_HOST` | The exact Supabase Session pooler host from your local `.env` |
   | `DB_USER` | Your Supabase pooler username from `.env` |
   | `DB_PASSWORD` | Your current Supabase database password |

   Paste the values **without the surrounding quotes used in `.env`**. Keep
   `DB_PORT=5432`, `DB_NAME=postgres`, and `DB_SSLMODE=require` as supplied.
   Render generates a new production `DJANGO_SECRET_KEY`; do not replace it
   with your local development key. Keep it stable on subsequent deployments.
8. Click **Deploy Blueprint** and wait for the web service to become **Live**.

The build installs dependencies, runs Django's production checks, collects
static files, and applies migrations. Gunicorn runs the app on Render's port.
Render supplies the public hostname, which the production settings add to the
allowed hosts and CSRF origins. The service deploys future merged changes from
`main` automatically.

If `homeward` is already used, Render may give this service a different URL.
Use the actual URL shown in the service dashboard; do not guess it.

## 3. Verify the live application

Use your actual HTTPS URL for each check:

- `/health/` returns `{"status": "ok"}`.
- `/accounts/signup/` creates a Member, validates duplicate emails and passwords,
  and displays a success message.
- `/accounts/login/` accepts the new account and opens the Member dashboard.
- `/accounts/profile/` displays only the current user's profile. Editing it
  changes only their name, email, and contact number.
- A Member opening `/dashboard/admin/` or `/accounts/manage/users/` gets 403.
- Logout returns to login. Private pages require login again.
- An Administrator opens the custom dashboard and Manage users panel, can
  create/edit a test account, and can deactivate/reactivate it.
- `/admin/` remains 404, and an arbitrary missing URL shows the friendly 404 page.
- HTTP requests redirect to HTTPS, and the browser displays no debug traceback.

Your existing local accounts are already in Supabase and also work on Render.
If no Administrator exists, run this locally against the same Supabase database:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

This does not require a Render shell and does not enable Django's admin panel.
Do not add administrator passwords or database credentials to the repository.

Copy the actual live URL for your submission and share it in this conversation
so its public pages can be checked. The deployment requirement is complete only
after the hosted application is live and verified.

## Local verification commands

The two new packages, WhiteNoise and Gunicorn, are listed in `requirements.txt`.
They have already been installed in the current workspace. For another checkout:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

To verify changes:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts/test_accounts.py
.\.venv\Scripts\python.exe scripts/check_production.py
```

The account test runner uses a disposable PostgreSQL schema and removes it.
The production check runs with `homeward.production`, checks HTTPS/CSRF/cookies,
collects and serves hashed static files, and performs a read-only database health
query. It does not apply migrations or create application data. The hostname
used by that local check is a temporary test value, not a deployed URL.

Local `manage.py runserver` still uses development settings. Gunicorn is used by
Render's Linux server, rather than as the local Windows development server.

## Hosting notes

Render Free services sleep after 15 minutes without traffic and can take about a
minute to wake up. Open the site before a demonstration. Account data remains in
Supabase rather than Render's temporary filesystem. User uploads are outside
this account phase; production file storage will need configuring before pet
photo uploads are introduced.

References: [Render Django deployment](https://render.com/docs/deploy-django),
[Blueprint setup](https://render.com/docs/infrastructure-as-code),
[Render environment variables](https://render.com/docs/environment-variables),
[Free service behavior](https://render.com/docs/free),
[Django deployment checklist](https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/).

## Password reset (PD2)

Local development prints password reset emails in the runserver terminal. Click
**Forgot your password?**, enter an active account's email, and use the link
printed in the terminal.

To enable real delivery on Render:

1. Add and verify a sending domain in [Resend](https://resend.com/docs/dashboard/domains/introduction).
2. In the Render service's environment settings, set `RESEND_API_KEY` to a
   Resend sending key and `PASSWORD_RESET_FROM_EMAIL` to an address on that
   verified domain. Save and redeploy. Keep the API key out of Git.
3. Request a reset for a demo account whose inbox you control, open the email
   link, change the password, and verify you can log in with the new password.

The reset link is shown on the deployed login page when both variables are
configured. Render Free can reach the email API over HTTPS.
