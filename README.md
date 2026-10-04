# Delhi Stationery

Delhi Stationery is a Django storefront and store-operations application for a local stationery business. Customers can browse products, place direct or cart orders, and follow order updates. Staff use permission-scoped tools to manage the catalogue, inventory, orders, delivery areas, and bulk quotes.

## Project status

The repository contains ten implemented feature areas and a broader set of storefront and account workflows. It is a substantial portfolio project and a good base for a controlled pilot. It is **not ready for public launch yet**: the public order lookup accepts a phone number and/or sequential order ID without verifying ownership. A phone-only search returns all matching orders; an order ID alone can return one order. Results include personal and delivery details. Replace this with authenticated access or a private, high-entropy per-order tracking link with expiry and rate limiting before exposing real customer orders. A real staging deployment and database-plus-media restore rehearsal are also outstanding.

The project has not been deployed to a production host. Payment status is managed by staff; there is no payment gateway or webhook. Delivery is managed by staff; there is no carrier API. Keep checkout on Cash on Delivery or manual UPI verification until a payment integration is implemented and reviewed.

## Feature overview

The ten major feature areas are automated checks and CI, scoped staff permissions, order snapshots, payment-state management, inventory history, order history and email, delivery zones and tracking, bulk quotes, catalogue discovery, and production configuration. Read the [feature inventory](docs/project-feature-inventory.md) for precise scope and limitations, and the [upcoming roadmap](docs/upcoming-feature-roadmap.md) for launch gates and follow-on work.

Other core workflows include a sample catalogue for an empty store, category filters, guest direct orders, authenticated cart checkout, customer profiles, cancellation and reorder, invoices, and CSV exports. Sample products are display-only; they are not database records and cannot be ordered.

## Technology stack

- Python 3.11 in CI; Django 5.2
- Django templates, HTML, CSS, and JavaScript
- SQLite for local development; PostgreSQL for staging and production settings
- Django ORM, sessions, built-in authentication and permissions
- Pillow for product images; `psycopg` for PostgreSQL; `python-dotenv` for local environment loading
- Django's test framework and GitHub Actions

React and FastAPI are not used in this repository. If you are learning them, list them separately as learning skills or demonstrate them in a separate project.

## Local setup on Windows

Install Python 3.11 and Git, then run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_store_roles
python manage.py runserver 8080
```

Open `http://127.0.0.1:8080/`. Development defaults to SQLite and Django debug mode. Copy `.env.example` to `.env` to adjust local settings. Never use the development secret or Django's `runserver` for a public production site.

See the [setup and deployment guide](docs/setup-and-deployment-guide.md) for environment variables, release commands, backups, and go-live checks.

## Architecture

| Area | Location | Responsibility |
| --- | --- | --- |
| Project config | `DelhiStationery/` | Settings, URL routes, WSGI entry point |
| Store domain | `store/` | Products, orders, payment state, quotes, inventory, delivery rules |
| Accounts and staff | `accounts/` | Customer profiles, staff permissions, workspace and exports |
| UI | `templates/`, `static/` | Server-rendered pages, styles and client-side behavior |
| Operations | `.github/workflows/`, `scripts/`, `docs/` | CI, backup script and project documentation |

## Checks

CI runs the Django system check, migration consistency check, and test suite on pushes and pull requests. Run the same checks locally with:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Before a production release, configure the production environment and run `python manage.py check --deploy`. Follow Django's [deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) as well as this project's [production readiness guide](docs/production-readiness.md).

## Documentation

- [Project feature inventory](docs/project-feature-inventory.md)
- [Upcoming feature roadmap](docs/upcoming-feature-roadmap.md)
- [Setup and deployment guide](docs/setup-and-deployment-guide.md)
- [Feature gap and implementation notes](docs/feature-gap-and-roadmap.md)
- [Production readiness and backups](docs/production-readiness.md)
- [Python and Django interview preparation](docs/interview-preparation.md)
- Existing Word files are in `docx/`; review the Markdown guides above for the current project state.
