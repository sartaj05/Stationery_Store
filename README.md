# Delhi Stationery Store

A Django storefront for stationery products, customer orders, cart checkout, and store operations. The public site uses Django templates with a session-based cart. Product and order data are stored in SQLite for local development.

## Current features

- Product catalogue with categories, search, discount prices, stock, and uploaded images
- Sample catalogue with local illustrations while there are no active products; active database products replace the sample catalogue automatically
- Guest direct orders and authenticated cart checkout
- Customer profiles, order history, order tracking, cancellation, and reorder
- Superuser-only custom dashboard for product, category, order, customer, bulk request, stock, invoice, and CSV workflows
- Bulk order enquiries and manual follow-up status

## Run locally on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8080
```

Open `http://127.0.0.1:8080/`. The custom dashboard is at `/accounts/superadmin/dashboard/`. Product management is currently restricted to Django superusers; ordinary staff users do not yet have a separate role-based access system.

## Feature notes

Sample products are in-memory display objects. They are not inserted into the database and cannot be ordered. Once an active database product exists, only real active products are shown. Uploaded product images use Django's media storage.

Cart checkout currently creates one `Order` row per cart product. `Order` points to the current `Product`, so historical unit prices are not snapshotted. The `UPI` choice is a recorded payment method; a payment provider is not integrated. `store/tests.py` and `accounts/tests.py` currently contain only the empty Django test scaffold.

## Project documentation

- [Feature gap and roadmap](docs/feature-gap-and-roadmap.md)
- [Python and Django interview preparation](docs/interview-preparation.md)
- Existing manuals, setup guides, checklists, and roadmap documents are in `docx/`.

## Before production

Set `DEBUG=False`, move `SECRET_KEY` into an environment variable, configure production hosts and HTTPS, use PostgreSQL, configure durable media storage and backups, and add automated coverage for checkout, stock, order access, and dashboard permissions.
