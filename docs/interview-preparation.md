# Delhi Stationery Python and Django Interview Preparation

This guide helps a Python developer with two or more years of experience explain the Delhi Stationery project accurately. It covers the architecture, ten delivered feature slices, design trade-offs, likely interview questions, and practice topics. Use the examples as prompts and describe only work you personally completed.

## Stack and experience framing

The repository uses Python 3.11 in CI, Django 5.2, Django templates, HTML, CSS, JavaScript, the Django ORM, SQLite locally, PostgreSQL deployment settings, Django sessions and permissions, Pillow, `psycopg`, `python-dotenv`, Django's test runner, and GitHub Actions. It does not use React or FastAPI. If those are skills you are currently learning, label them as learning or show them through a separate project; do not list them as technologies used in this application.

For a 2.3-year Python/Django profile, anchor answers in specific responsibilities: the models or flows you built, the tests you wrote, the review feedback you handled, and the trade-offs you can explain. Do not present the project as production experience: it has not been deployed to a live host, and no production metrics are available.

## A 90 second project walkthrough

> I built Delhi Stationery as a server-rendered Django store for a local stationery business. Customers can browse a searchable catalogue, use SKU or barcode lookup, place a direct order, or sign in and check out a session cart. The operations dashboard uses Django permissions and staff groups to separate catalogue, inventory, order, bulk-request, and customer-account work. Checkout updates stock inside a transaction, and the store records immutable inventory movements and order-status history. Order rows keep product, price, delivery, SKU, and barcode snapshots so later catalogue edits do not change historical records. Staff can prepare a bulk quote, send a seven-day acceptance link, and convert it into linked orders after stock and delivery checks. The project has a Django regression suite and a GitHub Actions workflow. Local development uses SQLite; staging and production settings require PostgreSQL, environment secrets, HTTPS settings, and a durable media path.

The repository had 45 Django tests at its last recorded verification. Recheck that count after future changes. The application has not been deployed to a production host, and it does not connect to a payment gateway or a carrier API. The public order lookup accepts a phone number and/or sequential order ID without verifying ownership and displays personal and delivery details. Treat this as a privacy defect, fix it before a pilot, and discuss the mitigation honestly if asked.

## Project architecture

| Layer | Location | Responsibility |
| --- | --- | --- |
| Project settings and route entry | `DelhiStationery/settings.py`, `DelhiStationery/urls.py` | Environment settings, middleware, installed apps, templates and URL inclusion |
| Store domain | `store/models.py`, `store/forms.py`, `store/views.py`, `store/services.py` | Catalogue, checkout, quotes, stock movements, status history and delivery rules |
| Accounts and staff workflows | `accounts/models.py`, `accounts/views.py`, `accounts/roles.py` | Customer profiles, staff permissions, dashboard modules and CSV exports |
| Presentation | `templates/store/`, `templates/accounts/` | Server-rendered customer, checkout and staff pages |
| Static and uploaded files | `static/`, `MEDIA_ROOT` | CSS, JavaScript, local sample illustrations and uploaded product images |
| Operations | `.github/workflows/`, `scripts/backup_postgres.ps1`, `docs/` | CI, backup example, setup and release guidance |

The empty-state sample catalogue is built in memory. It does not create fake products in the database and cannot be ordered. When the store has active products, the real catalogue replaces the sample view.

## Feature implementation map

| Feature | Current implementation | Useful interview discussion |
| --- | --- | --- |
| Automated tests and CI | Django tests cover storefront, checkout, permissions and the ten feature slices. GitHub Actions runs checks, migration consistency and tests. | How to isolate behavior in tests and keep schema changes visible in CI. |
| Staff roles | Django permissions and groups scope catalogue, inventory, orders, bulk requests, delivery zones and customer accounts. `setup_store_roles` creates the standard groups. | Why authorization belongs on the server as well as in templates. |
| Order access privacy | Account history is scoped to the logged-in customer, but public tracking accepts a phone number and/or sequential order ID without proving ownership and can reveal personal/delivery details. | How to distinguish a lookup identifier from an authentication factor; propose account ownership or a high-entropy per-order token, expiry, rate limiting, and minimal disclosure. |
| Order snapshots | Each order row preserves product name, brand, category, SKU, barcode and unit price. Referenced products cannot be deleted. | How a historical record differs from a live catalogue relationship. |
| Payment lifecycle | Staff can record pending, verified, failed and refund states with references and timestamps. | The difference between recording a payment choice and integrating a provider. |
| Inventory ledger | Sales, allowed cancellations, restocks, opening balances and adjustments create immutable movements with actor and reason. | How to reconcile a stock balance with an append-only movement history. |
| Order history and email | Status changes create immutable timeline events. Optional account or checkout email receives best-effort status messages. | Why history and notifications are separate concerns and where retry queues would fit. |
| Delivery management | Exact PIN zones define serviceability, delivery fee and ETA. Orders snapshot the PIN and fee; staff add carrier details before dispatch. | Why delivery promises are validated at checkout and captured on the order. |
| Bulk quotes | Staff create line items with agreed prices and a seven-day acceptance link. Acceptance rechecks live stock and serviceability and creates linked orders. | Atomic conversion, price snapshots, idempotent acceptance and grouped stock validation. |
| Catalogue discovery | Public pagination, sorting, category filtering, and search by name, brand, SKU or barcode. Staff can edit and export unique codes. | How to preserve filters through page links and query the effective sale price. |
| Production configuration | Environment-driven secrets, debug, host, PostgreSQL, HTTPS, email and media settings. A PowerShell backup script covers the database and media directory. | Which parts are implemented locally and which still depend on the chosen hosting platform. |

## Data model and important trade-offs

### One order row per product

`Order` stores a customer and delivery snapshot plus one product, quantity, unit price, and delivery fee. Cart checkout therefore creates one order row per cart product. A multi-product cart does not have one parent order identifier yet. Bulk quotes link the resulting product-order rows to their originating request with a many-to-many relation.

An interviewer may ask whether a normalized `Order` and `OrderItem` split would be better. Explain that it would make a whole cart share one order status, payment record, address and delivery fee. The current row-per-product design keeps the existing direct-order flow simple, but duplicates customer and fulfilment data for cart items. Parent-order grouping is a known follow-on migration.

### Product and price snapshots

Orders keep the purchased product name, brand, category, SKU, barcode and unit price. Totals use the snapshot values, not the current product price. `Product` uses a protected relationship so a product with order history cannot be deleted accidentally. This preserves receipts and totals when a catalogue item changes.

### Inventory movements

`InventoryMovement` records a signed quantity delta and a reason. Checkout and bulk acceptance record sales. Allowed cancellations restore stock. Staff restocks and manual adjustments include an actor and reason. Existing stock was recorded as an opening balance when the ledger was introduced; older individual sales cannot be reconstructed from that balance.

### Concurrency and transactions

Checkout runs within `transaction.atomic()`, locks product rows with `select_for_update()` on supported databases, verifies stock again, creates orders, and writes movements before commit. The cart is cleared only after success. Bulk acceptance groups requested quantities by product before checking stock, so repeated lines cannot pass separate checks against the same balance.

SQLite is used for local development, where row-level lock behavior differs from PostgreSQL. A production-like concurrency test should run against PostgreSQL and exercise two buyers requesting the final units at the same time.

## Project-based technical questions

### How do you prevent overselling?

The app checks stock while customers edit the cart and checks again during checkout. Inside one atomic transaction, it locks each product row on databases that support row locks, checks available quantities, creates the order records, decreases stock, and writes inventory movements. If an exception interrupts the operation, the database rolls back those changes together. I would test concurrent checkouts against PostgreSQL before relying on this under production traffic.

### Why use `transaction.atomic()` here?

Order creation and stock movement form one business operation. A transaction prevents the database from committing only half of that work. For example, the store should not keep an order if the related stock decrement failed.

### Why save price snapshots instead of reading `Product.price` later?

The catalogue price describes what a customer can buy now. An order price describes what the customer agreed to pay at purchase time. The order stores its own price and product labels, which protects totals, invoices and history from future catalogue edits.

### What is the risk in one order row per product?

Every cart item gets a separate order ID and status timeline. This can make customer support, refunds, delivery fees and whole-cart cancellation harder. A parent order with child items would model a cart purchase more naturally. I would add it with a staged data migration that groups rows by a durable checkout identifier; creating that identifier safely is part of the design.

### How are staff roles enforced?

Views use Django authentication and custom permission checks. Standard groups collect permissions into store jobs. The templates hide actions the current user cannot use, but view checks remain the actual security boundary. I would add authorization tests for every new route and inspect object-level access where users can act on individual records.

### How is payment verified?

The store records a payment method and a manual payment status. Staff can enter a transaction reference when marking a payment verified, and refunds require a reference and a valid amount. UPI selection is not itself proof of payment. A provider integration still needs signed webhook validation, idempotency, failure handling, refund callbacks and secret rotation.

### How do stock changes stay auditable?

The application routes stock changes through a service that updates the product balance and writes an immutable movement in the same transaction. The signed quantity explains the effect; the reason and actor explain why it happened. Existing balances became opening movements at rollout, so the ledger has a clear start date.

### What happens if status email fails?

The current send is best-effort and failure does not roll back an order-status change. That keeps a mail outage from blocking fulfilment. Production volume would justify a durable queue, retry policy and delivery-failure monitoring.

### How do delivery fees remain consistent?

The store looks up an exact six-digit PIN code and snapshots the fee and PIN onto an order. Once any delivery zones exist, unlisted or inactive PIN codes are rejected. Staff must enter a carrier or tracking reference before moving an order to dispatch. Carrier APIs are not connected.

### How does bulk quote conversion avoid partial orders?

The customer link is a UUID token with an expiry. Acceptance locks the request, checks that it is still quoted and unexpired, loads all lines, groups quantities by product, locks products, validates stock and delivery serviceability, then creates the order rows and inventory movements in one transaction. A repeated acceptance is rejected after conversion. The delivery fee is applied once across the linked rows.

### Why paginate and sort in the database?

The real catalogue query is filtered and ordered before pagination. This avoids loading every product into application memory and produces stable pages. Price sorting uses the effective price by falling back from a discount to the original price. The sample catalogue is small and in memory, so it is sorted and paginated in Python.

### What changes between development and production settings?

Development uses SQLite and a development-only fallback key. Staging and production require debug off, an environment-provided secret, allowed hosts, PostgreSQL credentials and a persistent media root. HTTPS cookies, redirect and HSTS values are configurable. The code does not configure a hosting provider, create PostgreSQL resources, move uploads to object storage or deploy the site.

## Python and Django topics to prepare

For each topic, prepare one definition, one example from the project and one trade-off.

### Python

- Lists, tuples, dictionaries and sets, including lookup and mutation costs.
- Mutable default arguments and safe alternatives such as `None` or a factory.
- Iterators, generators, comprehensions and lazy evaluation.
- Exceptions, custom exceptions, context managers and `try`/`finally` cleanup.
- Decorators, closures, argument forwarding and when a plain function is clearer.
- Classes, inheritance, composition, dataclasses and Python protocols.
- `is` versus `==`, truthiness, `None`, and object identity.
- GIL behavior, threads, processes and asynchronous I/O trade-offs.
- Type hints, static analysis and readable public interfaces.

### Django

- Request and response flow through middleware, URL routing, views, forms and templates.
- Model relationships, migrations, constraints, indexes and data migrations.
- `QuerySet` laziness, N+1 queries, `select_related()` and `prefetch_related()`.
- `transaction.atomic()`, `select_for_update()` and backend differences.
- Authentication versus authorization, Django permissions, CSRF and session security.
- Form validation, model validation, file upload checks and trust boundaries.
- Django test cases, fixtures, test client, mail outbox and test database behavior.
- Static files, user-uploaded media, production settings and management commands.

### SQL and system design

- Primary and foreign keys, unique constraints, check constraints and indexes.
- Transaction isolation, lock contention, deadlocks and retry boundaries.
- Designing an order / order-item schema and preserving historical prices.
- Making payment webhooks idempotent with a provider event ID and unique constraint.
- Moving email work to an outbox or background queue without losing events.
- Database backups, media backups, restore testing and recovery objectives.

## Scenarios to practise

1. Two customers submit the final unit at the same time. Explain the transaction, row lock, stock check and PostgreSQL test.
2. A product price changes after an order. Explain snapshots and protected records.
3. A quote is accepted twice from two browser tabs. Explain request locking, terminal status and an optional idempotency key.
4. An email provider is down after checkout. Explain why order creation should still succeed and how a queue could retry delivery.
5. An online-payment webhook arrives twice or out of order. Explain signature checks, provider event IDs, idempotent writes and allowed state transitions.
6. A store has a million products. Explain database indexes, search strategy, pagination limits, query plans and when to introduce a search service.
7. A production restore returns the database but not the product photos. Explain why database and media backups need a shared recovery plan.

For planned functionality, state clearly that it is a design proposal. Do not describe a gateway, carrier API, notification queue or live deployment as complete.

## Behavioral examples to prepare

Use the STAR structure: describe the situation, your responsibility, the specific actions you took, and the verified result. Choose real examples from your own work for each prompt.

- A defect you traced across a Django view, form, model or template.
- A migration that needed to preserve existing data.
- A design decision where you chose a simpler first version and documented its limit.
- A test that caught a regression before release.
- A code review comment that changed your implementation.
- A production issue or deadline, if you have a real example from another project.

Do not invent traffic, revenue, response-time or availability metrics for this project. If asked for scale, describe what you measured and what you have not measured.

## Resume bullet examples

Use these only if they match your contribution. Add numbers only when you can verify them.

- Built a Django storefront with product search, category filters, sortable pagination, direct orders and authenticated cart checkout.
- Added transactional stock updates with an immutable movement ledger for sales, cancellations, restocks and manual adjustments.
- Implemented scoped Django staff permissions, order-status history, delivery zones and customer-facing quote acceptance.
- Added order price and product-code snapshots, plus tests and GitHub Actions checks for core customer and staff workflows.
- Configured production-mode settings for PostgreSQL, environment secrets, HTTPS options and persistent media storage.

## Demonstration sequence

1. Show the in-memory sample catalogue and explain that it does not create database products.
2. Search the real catalogue by product name, SKU or barcode; demonstrate sorting and pagination.
3. Add an item to the cart and explain the stock recheck at checkout.
4. Open customer history and show how order snapshots preserve the purchased price.
5. Sign in as staff and show a scoped workspace, inventory movement and order status history.
6. Prepare a bulk quote, open its acceptance link and explain the stock validation before conversion.
7. End with the honest follow-on work: parent orders, a payment provider, carrier APIs, queued email and an actual production deployment.

## Interview day checklist

- Practise the walkthrough until it fits in 90 seconds without listing every feature.
- Be ready to draw the order, product, quote, inventory and status-history relationships.
- Explain one test and one migration you worked on in detail.
- State the row-per-product order limitation and its consequences.
- Separate recorded UPI method from verified online payment.
- Separate production-ready configuration code from an actual deployed environment.
- Keep explanations tied to decisions, evidence and trade-offs rather than feature names alone.
