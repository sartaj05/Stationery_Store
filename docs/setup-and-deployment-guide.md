# Delhi Stationery Setup and Deployment Guide

This guide covers local setup, the production settings already present in the repository, and the remaining release work. The commands and configuration are a starting point; they do not create a cloud database, hosting account, domain, or object-storage bucket. The app has not yet been deployed to a production host.

## Requirements

- Python 3.11 (the version used by GitHub Actions)
- Git
- Windows PowerShell for the commands below; macOS/Linux can use equivalent virtual-environment activation commands
- PostgreSQL client tools (`pg_dump` and `pg_restore`) on the administration host used for backups
- A PostgreSQL server, HTTPS endpoint/reverse proxy, durable media storage, and SMTP provider for a deployed environment

## Local development on Windows

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_store_roles
python manage.py runserver 8080
```

Open `http://127.0.0.1:8080/`. Local defaults use SQLite, development debug mode, and Django's console email backend. `runserver` is for local development only.

To create a staff account, create or select a Django user, mark the user as staff when Django admin access is required, and assign the appropriate standard group. Run `python manage.py setup_store_roles` after migrations and whenever a fresh database needs the standard groups.

## Environment settings

Copy `.env.production.example` as a checklist only. Replace every example value, keep secrets in the hosting provider's secret manager, and do not commit a populated `.env` file.

| Variable group | Purpose |
| --- | --- |
| `DJANGO_ENV`, `DJANGO_DEBUG`, `DJANGO_SECRET_KEY` | Select production behavior, disable debug, and provide a private random key. |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Restrict valid host headers and allow the actual HTTPS origins used for forms. |
| `DJANGO_USE_POSTGRES`, `POSTGRES_*` | Select PostgreSQL and supply its database, user, password, host, port, TLS mode, and connection lifetime. |
| `DJANGO_MEDIA_ROOT` | Point to a durable, backed-up mount for uploaded product images. A container's temporary disk is not durable storage. |
| `DJANGO_SECURE_SSL_REDIRECT`, cookie flags, HSTS values | Enable HTTPS behavior once the TLS proxy is correctly configured. Set proxy forwarding only when the trusted proxy overwrites the header from the verified TLS connection. |
| `DJANGO_EMAIL_*`, `DJANGO_DEFAULT_FROM_EMAIL` | Configure SMTP credentials and the sender used by status/quote email. |

Generate a production key without adding it to the repository:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The production settings refuse to start with debug enabled, no secret key, no allowed host, no PostgreSQL configuration, or no explicit persistent media root. Confirm that database TLS requirements match the chosen provider.

## First deployment checklist

1. Choose a hosting platform that can run a supported WSGI/ASGI application, PostgreSQL, and persistent media storage. Provision a least-privilege database user.
2. Configure the environment values above in the platform's secret and environment settings. Do not copy the sample credentials into production.
3. Configure TLS at the hosting proxy, then configure the app's HTTPS redirect and secure cookies. Trust forwarded protocol headers only from a proxy that replaces client-supplied values.
4. Build the release from a clean, reviewed commit and install `requirements.txt`.
5. Run the deployment checks and release commands from the repository root:

   ```powershell
   python manage.py check --deploy
   python manage.py makemigrations --check --dry-run
   python manage.py test
   python manage.py migrate --noinput
   python manage.py collectstatic --noinput
   python manage.py setup_store_roles
   ```

6. Configure the platform's production WSGI or ASGI server and static-file service. Do not serve production traffic with `runserver`.
7. Verify login, CSRF-protected forms, checkout, inventory, invoice output, static files, uploaded product images, staff permissions, SMTP delivery, and the chosen backup destination in staging.
8. Disable public order lookup or replace it with ownership-checked access before real customer data is exposed. The current page accepts a phone number and/or sequential order ID and reveals personal/delivery details. See the [roadmap](upcoming-feature-roadmap.md).
9. Rehearse a full database and media restore in an isolated environment before opening a customer pilot.

Use Django's official [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) and [security guidance](https://docs.djangoproject.com/en/5.2/topics/security/) for the host-specific details. `check --deploy` is one release check; it does not replace the full security, performance, error-reporting, and operations review.

## Back up PostgreSQL and uploaded media

The repository contains `scripts/backup_postgres.ps1`. Run it on a secured Windows administration host with PostgreSQL client tools installed. The process needs `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, optional port/TLS settings, and `DJANGO_MEDIA_ROOT` available in its environment. Store credentials in the approved secret store; avoid putting the password in shell history.

```powershell
.\scripts\backup_postgres.ps1 -BackupDirectory "E:\EncryptedBackups\DelhiStationery"
```

It creates a custom-format PostgreSQL dump and a compressed archive of the media root in the specified directory. Keep backups separate from the application host, restrict access, set a retention policy, and monitor backup completion. The script does not configure scheduled execution, encrypt the backup itself, upload to offsite storage, or prove that a backup can be restored.

Example database restore outline to an isolated restore database:

```powershell
pg_restore --clean --if-exists --no-owner --dbname="$env:RESTORE_DATABASE_URL" .\delhi-stationery-backup.dump
```

Restore the matching media archive into the restore environment's configured media root. Then verify that product images load, staff can sign in, orders and quote links are consistent, and checkout behaves correctly. Never test destructive restore commands against the production database.

## Go-live checklist

- [ ] Public lookup is disabled or replaced by authenticated/token-authorized access to one order, with rate limiting and minimal data disclosure.
- [ ] The production host uses PostgreSQL, HTTPS, secure cookies, a private secret, and explicit allowed hosts.
- [ ] Static files and user-uploaded media have the configured production storage path.
- [ ] The release checks, migrations, and test suite pass on staging settings.
- [ ] Real SMTP delivery is confirmed; failures have an owner and monitoring path.
- [ ] A PostgreSQL and media backup is created, then restored and verified in an isolated environment.
- [ ] Store staff can carry out the documented COD/manual-UPI and manual-dispatch process.
- [ ] A responsible person is assigned to application errors, database capacity, backups, and customer support.

Do not claim production readiness until the app has passed these checks in the actual hosting environment. Django recommends a deliberate release review and running `check --deploy` with production settings; see the [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
