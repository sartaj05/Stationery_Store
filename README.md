# Delhi Stationery Store

A Django storefront for stationery products, customer orders, cart checkout, and store operations. The public site uses Django templates with a session-based cart. Product and order data are stored in SQLite for local development.

## Current features

- Product catalogue with category filters, SKU/barcode search, pagination, sorting, discount prices, stock, and uploaded images
- Sample catalogue with local illustrations while there are no active products; active database products replace the sample catalogue automatically
- Guest direct orders and authenticated cart checkout
- Customer profiles, order history, order tracking, cancellation, and reorder
- Permission-scoped staff workspace for product, category, order, customer, bulk request, stock, invoice, and CSV workflows
- Seven standard staff groups for store managers, catalogue, inventory, orders, bulk requests, and customer support
- Inventory movement history for sales, cancellations, restocks, opening balances, and reasoned manual adjustments
- Immutable order status timelines with email updates for checkout and status changes
- Delivery zone serviceability and fee lookup by six-digit PIN code, with dispatch and tracking details
- Bulk quote builder with emailed seven-day acceptance links, stock-checked conversion, and linked fulfilment orders
- Production environment settings for secret keys, PostgreSQL, HTTPS, SMTP, and a persistent media volume
- Automated Django tests for checkout, stock, cancellation, profiles, and dashboard access, with GitHub Actions CI

## Run locally on Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8080
```

Open `http://127.0.0.1:8080/`. Local settings use SQLite and Django debug mode. Copy `.env.example` to `.env` if you want to customize development settings; install dependencies from `requirements.txt` first so the settings loader can read it. After migrations, run `python manage.py setup_store_roles` to create the standard groups. Assign users to groups in Django admin; users must also have `is_staff=True` to sign in through the Django admin, while the custom staff workspace is permission-based. The staff workspace is at `/accounts/staff/` and routes each user to their first permitted module.

## Feature notes

Sample products are in-memory display objects. They are not inserted into the database and cannot be ordered. Once an active database product exists, only real active products are shown. Uploaded product images use Django's media storage.

Cart checkout currently creates one `Order` row per cart product. Each order keeps the purchased product name, brand, category, SKU, barcode, and unit price; changing catalogue data does not rewrite order history, and products referenced by orders cannot be deleted. UPI payments begin in a pending-verification state; staff can record verified transactions and full or partial refunds. No payment gateway or webhook is connected yet. Stock changes are written to an append-only movement ledger; history starts at the inventory rollout, with existing balances recorded as opening stock. Order status changes create immutable history and send email to the account or optional checkout email. Delivery zones store exact PIN-code serviceability, fee, and ETA; staff add a carrier or tracking reference before dispatch. With no zones configured, checkout remains open with zero delivery fee; after the first zone exists, unlisted or inactive PIN codes are blocked. Bulk requests can be converted into quoted line items; customers accept a time-limited quote and receive linked orders after live stock validation. Email delivery requires a configured mail backend; current send attempts fail silently when mail is unavailable. Automated coverage lives in `store/tests.py` and `accounts/tests.py`, with GitHub Actions CI.

Inventory staff can open **Inventory History** from the staff workspace, add stock from low-stock alerts, or make a signed adjustment with a required reason. Catalogue-only staff cannot change stock; new products start at zero unless the user also has the inventory permission.

## Project documentation

- [Feature gap and roadmap](docs/feature-gap-and-roadmap.md)
- [Production readiness and backup guide](docs/production-readiness.md)
- [Python and Django interview preparation](docs/interview-preparation.md)
- Existing manuals, setup guides, checklists, and roadmap documents are in `docx/`.

## Production setup

Copy `.env.production.example` to `.env` for a single-server deployment, replace every placeholder, and use a private secret store on managed platforms. Production mode refuses to start with debug enabled or without a secret key, allowed hosts, PostgreSQL settings, and a persistent media path. Follow the [production readiness guide](docs/production-readiness.md) for static collection, HTTPS, SMTP, backup, and restore steps. Run `python manage.py check --deploy` before each release.
