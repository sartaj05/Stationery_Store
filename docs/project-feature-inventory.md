# Delhi Stationery Project Feature Inventory

This inventory describes the repository as it exists today. It groups the work into ten major feature areas rather than counting every page, model, and button as a separate feature. It is intended for project review, launch planning, demonstrations, and honest interview discussion.

## At a glance

The project has **10 major feature areas implemented in code**, plus the foundational storefront, customer-account, and staff workflows they depend on. “Implemented” means the application code and local workflows exist; it does not mean a production host, payment provider, carrier service, or real email service is already operating.

| # | Feature area | What is in the repository | Important boundary |
| --- | --- | --- | --- |
| 1 | Automated tests and CI | Django test suite; GitHub Actions checks configuration, migration consistency, and tests on pushes and pull requests. | Production database concurrency still needs a staging test against PostgreSQL. |
| 2 | Staff roles and permissions | Standard staff groups and server-side permission checks for catalogue, inventory, orders, bulk requests, delivery areas, and customer-account work. | A group must be assigned to a staff account; template visibility is not the security boundary. |
| 3 | Order product and price snapshots | Each order row preserves purchased product labels, SKU/barcode, unit price, delivery PIN, and delivery fee. Product history is protected from accidental deletion. | A cart with several products creates several order rows; it does not yet have one parent order number. |
| 4 | Manual payment lifecycle | Cash on Delivery and UPI choices; staff can record verification, transaction references, and partial or full refunds. | No gateway, payment capture, webhook, or automated settlement is connected. |
| 5 | Inventory movement history | Sales, cancellations, restocks, opening balances, and manual adjustments write append-only movements with quantity, actor/reason where available, and time. | The ledger starts at rollout; earlier individual stock changes cannot be reconstructed. |
| 6 | Order timeline and customer email | Order status transitions are preserved as history; status email is attempted for account or checkout email addresses. | Email is best-effort and synchronous; configure a mail provider and add monitoring/retries for dependable delivery. |
| 7 | Delivery serviceability and tracking | Staff maintain six-digit PIN zones, fees, and estimated days; dispatch requires a carrier or tracking reference. | No carrier API, live label creation, or delivery webhook exists. With no zones configured, checkout defaults to zero delivery fee. |
| 8 | Bulk quotes and conversion | Staff create itemized quotes with agreed prices and an expiring acceptance link. Acceptance rechecks stock/serviceability and creates linked order rows atomically. | The current implementation has no downloadable quote PDF, revision workflow, or payment terms. |
| 9 | Catalogue discovery | Category filters, pagination, sorting, and search by product name, brand, SKU, or barcode; staff can manage and export product codes. | Barcode lookup is text search; there is no camera scanner or stock-receiving scan flow. |
| 10 | Production configuration and backup tooling | Environment-based deployment settings, PostgreSQL configuration, secure-cookie/HTTPS options, SMTP settings, persistent media root, and a PostgreSQL-plus-media PowerShell backup script. | No production platform is configured, no live deployment exists, and the restore process has not been rehearsed on a real environment. |

## Foundational workflows

- Public storefront and sample catalogue for an empty store. Sample products are in-memory display objects, not orderable database products.
- Database catalogue with categories, active/inactive products, pricing and uploaded product images.
- Guest direct order and authenticated session-cart checkout.
- Customer profile, account order history, reorder, and allowed cancellation flows.
- Staff workspace, product/category operations, stock alerts, invoices, customer history, and CSV exports.

## Technology stack

| Concern | Technology |
| --- | --- |
| Language/runtime | Python 3.11 in CI |
| Web framework | Django 5.2 |
| User interface | Django templates, HTML, CSS, JavaScript |
| Data access | Django ORM |
| Local database | SQLite |
| Staging/production database settings | PostgreSQL through `psycopg` |
| Authentication and access | Django sessions, users, groups, and model permissions |
| Images | Pillow and Django media storage |
| Environment loading | `python-dotenv` for local development |
| Automated workflow | Django test runner and GitHub Actions |

React and FastAPI are not part of this repository. They can be added to a separate portfolio project when there is a working example to demonstrate.

## Launch assessment

This is a strong portfolio project and a reasonable **controlled-pilot candidate after the release gates below**. It is not ready to expose real customer data publicly yet.

### Must address before serving real customers

1. **Protect order tracking.** The public tracking form accepts a phone number and/or sequential order ID without verifying ownership. Phone-only lookup returns all matching orders; an ID alone can return one order. The page displays name, phone, address, product, payment state, total, and status history. Require a logged-in owner or use a private, high-entropy token scoped to one order, with expiry, rate limiting, and minimal data disclosure. Avoid logging raw tokens or exposing them in referrers.
2. **Complete a real staging deployment.** Configure PostgreSQL, TLS/reverse proxy, allowed hosts, static files, persistent media, and secrets in the selected hosting environment. Run migrations and `check --deploy` against those actual settings.
3. **Prove recovery.** Create a backup and restore both PostgreSQL data and product media into a separate test environment. Record the steps and verify that the restored application works.
4. **Verify customer communications.** Send a real test email through the chosen SMTP provider and check logs/alerts for delivery failures. Email currently is best-effort.
5. **Rehearse the store's payment process.** For an initial pilot, COD and staff-verified UPI can be workable if the customer instructions and staff reconciliation process are clear. Do not present UPI as automatically verified.

For a small pilot, a full payment gateway or carrier integration is not automatically required if the business deliberately handles those tasks manually. They become necessary when the operational model requires automated confirmation, refunds, labels, or tracking updates.

## Interview framing

Present the project as a Django server-rendered commerce and operations application. Discuss transactional checkout, database-backed permissions, price snapshots, an auditable inventory ledger, quote conversion, and the trade-offs that remain. Be explicit that the app has not been deployed, the payment state is staff-managed, and delivery is not connected to a carrier API.

For a 2.3-year Python/Django profile, explain the code you personally wrote and reviewed. Do not claim React or FastAPI implementation based on learning alone, and do not invent traffic, revenue, uptime, or production metrics.
