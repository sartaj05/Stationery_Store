# Delhi Stationery Store

A Django storefront for stationery products, customer orders, cart checkout, and store operations. The public site uses Django templates with a session-based cart. Product and order data are stored in SQLite for local development.

## Current features

- Product catalogue with categories, search, discount prices, stock, and uploaded images
- Sample catalogue with local illustrations while there are no active products; active database products replace the sample catalogue automatically
- Guest direct orders and authenticated cart checkout
- Customer profiles, order history, order tracking, cancellation, and reorder
- Permission-scoped staff workspace for product, category, order, customer, bulk request, stock, invoice, and CSV workflows
- Seven standard staff groups for store managers, catalogue, inventory, orders, bulk requests, and customer support
- Bulk order enquiries and manual follow-up status
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

Open `http://127.0.0.1:8080/`. After migrations, run `python manage.py setup_store_roles` to create the standard groups. Assign users to groups in Django admin; users must also have `is_staff=True` to sign in through the Django admin, while the custom staff workspace is permission-based. The staff workspace is at `/accounts/staff/` and routes each user to their first permitted module.

## Feature notes

Sample products are in-memory display objects. They are not inserted into the database and cannot be ordered. Once an active database product exists, only real active products are shown. Uploaded product images use Django's media storage.

Cart checkout currently creates one `Order` row per cart product. Each order keeps the purchased product name, brand, category, and unit price; changing catalogue data does not rewrite order history, and products referenced by orders cannot be deleted. UPI payments begin in a pending-verification state; staff can record verified transactions and full or partial refunds. No payment gateway or webhook is connected yet. Automated coverage lives in `store/tests.py` and `accounts/tests.py`, with GitHub Actions CI.

## Project documentation

- [Feature gap and roadmap](docs/feature-gap-and-roadmap.md)
- [Python and Django interview preparation](docs/interview-preparation.md)
- Existing manuals, setup guides, checklists, and roadmap documents are in `docx/`.

## Before production

Set `DEBUG=False`, move `SECRET_KEY` into an environment variable, configure production hosts and HTTPS, use PostgreSQL, configure durable media storage and backups, and add automated coverage for checkout, stock, order access, and dashboard permissions.
