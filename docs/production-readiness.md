# Production readiness

The repository contains production-oriented configuration, but the project has not been deployed to a production host. The settings select local SQLite for development and require PostgreSQL and persistent media storage in staging or production. They fail early when the secret key, allowed hosts, PostgreSQL credentials, or persistent media root are missing. Production secrets belong in the hosting provider's secret store; do not commit a populated `.env` file.

**Release blocker:** the public `track_order` view accepts a phone number and/or sequential order ID without verifying ownership. A phone-only search returns all matching orders; an ID alone can return one. The results include customer name, phone, address, product, total, payment state, and status history. Before exposing real customer orders, require an authenticated owner or a private high-entropy per-order token with expiry and rate limiting. Restrict each lookup to one authorized order and minimize disclosed fields. This privacy change is not implemented yet.

## Configure a deployment

1. Copy `.env.production.example` to `.env` for a single-server deployment, or enter each variable in the platform's environment and secret settings.
2. Generate a new secret with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. Set it as `DJANGO_SECRET_KEY`; do not use the example value.
3. Set `DJANGO_ALLOWED_HOSTS` to the site's hostnames and `DJANGO_CSRF_TRUSTED_ORIGINS` to the matching HTTPS origins.
4. Configure the managed PostgreSQL host, database, application user, password, and TLS mode. Use a dedicated database account with only the permissions the app needs.
5. Mount durable storage at `DJANGO_MEDIA_ROOT`. This directory contains uploaded product images; container-local storage is not durable.
6. Configure a real SMTP backend and sender address before relying on email notifications.
7. Configure the reverse proxy to terminate HTTPS. Set `DJANGO_TRUST_X_FORWARDED_PROTO=True` only when the trusted proxy replaces incoming `X-Forwarded-Proto` headers with the verified connection scheme.

Use an isolated staging environment first. Confirm the proxy's forwarded-protocol behavior, CSRF trusted origins, production static-file serving, and uploaded-image persistence there. Do not expose order lookup until the privacy blocker above is resolved.

## Release commands

Run these commands in the deployment environment after environment variables are available:

```sh
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py setup_store_roles
```

Serve `STATIC_ROOT` through the chosen static server or CDN. Serve the media mount from a controlled media service or object-storage integration. The project does not upload images to a cloud bucket automatically.

`check --deploy` reports HSTS subdomain and preload warnings when those optional flags remain off. Enable them only when every affected subdomain is HTTPS-only and the domain owner has approved browser preload submission.

## Database and media backups

Run `scripts/backup_postgres.ps1` from a Windows administration host with the PostgreSQL client installed and the `POSTGRES_*` and `DJANGO_MEDIA_ROOT` variables available. Pass a backup directory on an encrypted, access-controlled volume. The script creates one custom-format PostgreSQL dump and one compressed media archive with a UTC timestamp. The script does not schedule backups, encrypt archives itself, copy them offsite, or validate the restore.

```powershell
.\scripts\backup_postgres.ps1 -BackupDirectory "E:\EncryptedBackups\DelhiStationery"
```

Keep database and media backups on storage separate from the application host, retain copies according to the business recovery policy, and perform periodic restore drills. A database dump without its matching media files will not restore product images.

Example restore outline:

```sh
pg_restore --clean --if-exists --no-owner --dbname="$RESTORE_DATABASE_URL" backup.dump
```

Restore media into the configured durable media volume, then verify product images, checkout, order history, staff roles, outbound email, and PIN serviceability before directing customer traffic to the restored service.

## Go-live acceptance

- Public order lookup is disabled or authorizes one order through an account or private high-entropy token; request attempts are rate-limited.
- `DJANGO_ENV=production`, `DJANGO_DEBUG=False`, a unique secret, and explicit allowed hosts are set.
- PostgreSQL and the persistent media volume are available and backed up together.
- HTTPS redirects and secure cookies work through the configured proxy.
- HSTS is enabled after HTTPS is confirmed for the production hostname.
- `check --deploy`, migrations, static collection, and the Django test suite pass in the release pipeline.
- A database-and-media restore has been rehearsed in a non-production environment.
- The release owner has rehearsed COD/manual UPI verification, cancellation/refund record-keeping, and manual dispatch procedures.

The code is a strong implementation foundation, but configuration alone does not mean the application is production-ready. Apply Django's [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) to the real host and review its [security guidance](https://docs.djangoproject.com/en/5.2/topics/security/) before release.
