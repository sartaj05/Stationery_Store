# Delhi Stationery Interview Preparation

Project walkthrough and technical discussion points for a Python and Django developer interview at the two-plus-year experience level.

## Project summary

Delhi Stationery is a Django web store for stationery products. The public site uses Django templates and server-rendered views. Customers can browse products, search by product or category, place a direct order, or sign in and use a session-based cart. Registered customers can save delivery details, view their order history, cancel eligible orders and reorder. Store operations are handled through a custom dashboard available to Django superusers.

The project uses SQLite for local development. Products, categories, orders, customer profiles and bulk order requests are Django models. Product photos are uploaded to media storage. When there are no active database products, the storefront shows non-purchasable sample products with local static illustrations; sample data is not written to the database.

## A 90-second project walkthrough

> I built a Django stationery store with a server-rendered customer storefront and a custom operations dashboard. Customers can browse a product catalogue, place a direct order, or sign in to check out a session-based cart. The application tracks stock, stores customer delivery details, and lets customers review, cancel eligible, or reorder their own orders. Store superusers manage the catalogue, order statuses, bulk enquiries and restocking through a custom dashboard. I also added an empty-catalogue experience that uses local sample illustrations without polluting the real product database. The next improvements I would prioritize are automated tests, staff permissions, and order-line price snapshots so historical totals cannot change when a product price is edited.

Use this as a framework and describe only work you personally completed. Add measured outcomes only when you have actual evidence.

## Architecture map

| Layer | Project location | Responsibility |
| --- | --- | --- |
| Project configuration | `DelhiStationery/settings.py`, `DelhiStationery/urls.py` | Apps, middleware, templates, database, static/media files and route inclusion |
| Store domain | `store/models.py`, `store/forms.py`, `store/views.py`, `store/urls.py` | Product catalogue, orders, cart, stock checks, bulk enquiries and customer-facing flows |
| Accounts and operations | `accounts/models.py`, `accounts/forms.py`, `accounts/views.py`, `accounts/urls.py` | Customer profile, sign-in, dashboard workflows and CSV exports |
| Presentation | `templates/store/`, `templates/accounts/` | Django templates for storefront, checkout, customer pages and dashboard |
| Frontend assets | `static/store/`, `static/accounts/` | CSS, JavaScript and static sample product illustrations |
| Uploaded product files | `MEDIA_ROOT` | Product images uploaded through the product form |

## Data model and request flows

### Main models

- `Category` has a unique name and slug and groups products.
- `Product` stores catalogue text, price, optional discount, stock, image, active/featured flags and creation time.
- `Order` stores customer and delivery fields, one product, quantity, payment method, current status and internal note.
- `CustomerProfile` is one-to-one with Django's `User` and stores phone and delivery address details.
- `BulkOrderRequest` stores an organisation's request, current follow-up status and an internal note.

### Cart checkout

The cart is kept in the session. On checkout, the view rebuilds cart items from active database products, validates stock, enters a database transaction, requests row locks with `select_for_update()`, creates orders and decrements stock. The cart is cleared after successful checkout.

Current design limitation: checkout creates a separate `Order` for each product rather than a parent order with line items. The order refers to the live `Product` record, and `total_price()` reads the current product price. A product price edit can therefore affect a historical order total; deleting a product also deletes linked orders because the foreign key uses cascade behavior. A stronger design snapshots product name, SKU and unit price into an `OrderItem` when the purchase is created and protects or soft-deletes products that have been ordered.

`select_for_update()` behavior depends on the database backend. SQLite is convenient for development, while a production database such as PostgreSQL is needed to exercise row-level locking semantics.

## Technical questions with project-based answers

### Why use a Django session for the cart?

It keeps the cart available across pages without requiring a cart database model or a frontend framework. At checkout, the server reloads each product from the database and validates current stock and prices instead of trusting client-submitted totals. A persisted cart model would be useful for cross-device carts, recovery after login, and analytics.

### How do you prevent overselling?

The app checks stock before adding or updating quantities and checks again during checkout inside a transaction. It requests a row lock for each product before order creation and stock reduction. I would deploy on a backend with row-level locking and add concurrent checkout tests before relying on this under production traffic.

### Why is a database transaction useful at checkout?

Order creation and inventory changes belong together. If an exception occurs partway through, the transaction allows those changes to roll back instead of leaving an order without the corresponding stock reduction, or stock reduced without an order.

### How are permissions applied to the operations dashboard?

The current implementation uses `login_required` and a `user_passes_test` check for `is_superuser`. That is simple for a small owner-operated store, but it grants all dashboard capability to superusers and has no staff role split. I would introduce Django groups and per-action permissions for order processing, catalogue editing, customer data and exports.

### What is the difference between static files and media files?

Static files are application assets deployed with the code, such as CSS, JavaScript and the sample SVG illustrations. Media files are uploaded by users or administrators, such as product photos, and need separate persistence and access configuration in production.

### What would you test first?

I added Django tests for sample-catalogue behavior, guest ordering, cart checkout, stock shortage, cancellation and stock restoration, customer order ownership, profile validation, and dashboard access. GitHub Actions runs the Django system check, checks for model changes without migrations, and runs the test suite on pushes and pull requests. I would extend this with concurrency tests against PostgreSQL and feature-specific tests as the roadmap is implemented.

### What security and deployment issues would you address?

The development settings currently have `DEBUG=True`, a committed development `SECRET_KEY`, localhost-only hosts and SQLite. Before deployment I would move secrets to environment configuration, set `DEBUG=False`, configure real hosts and HTTPS, use a production database, persist uploaded media, schedule backups and add error monitoring. I would also review the phone-based order lookup because a phone number alone is not strong proof of ownership.

### What is the payment behavior today?

Orders store either `COD` or `UPI` as a selected payment method. There is no payment gateway integration or verified payment state, so I would describe UPI as an order preference rather than an online payment feature. A real integration needs provider callbacks, idempotent transaction handling, failure and refund states, and secure secret storage.

## Python and Django topics to prepare

- Python data structures, mutability, iterators, context managers, exceptions and decorators
- Object-oriented design, composition, interfaces and when to keep a function simple
- Django request/response lifecycle, URL routing, middleware, views, forms and template context
- Model relationships, migrations, constraints, indexes and query optimization with `select_related()` and `prefetch_related()`
- Authentication, authorization, CSRF protection, input validation and safe file uploads
- Atomic transactions, database isolation, row locking and idempotency
- Unit tests, integration tests, fixtures, the Django test client and CI checks
- Static versus media files, environment settings, logging, deployment and backup strategy

For each topic, prepare one example from this project, one trade-off, and one improvement you would make.

## Honest limitations to discuss

- Automated tests cover the main current flows; parallel checkout behavior still needs PostgreSQL-backed coverage.
- Dashboard access is superuser-only; separate staff permissions are not implemented.
- Cart checkout creates one order row per product and does not snapshot historical prices.
- Deleting a product cascades to its related order rows.
- UPI is a stored choice, not a connected payment gateway.
- Current development settings are not production-ready.
- Customer order lookup uses phone and optional numeric order ID, so stronger ownership verification is a future improvement.

Being precise about current behavior and explaining a safe next step is stronger than claiming a planned capability is complete.

## Resume bullet templates

Use only bullets that match your contribution. Replace bracketed values with verified measurements, or remove them.

- Built a Django stationery storefront with product search, category filtering, direct orders and authenticated cart checkout.
- Implemented stock validation and transactional order creation for product checkout; added [verified test count or coverage result] automated checks.
- Developed a custom superuser dashboard for product, order, customer, bulk enquiry and inventory workflows.
- Added a non-purchasable empty-catalogue experience with locally served sample illustrations and automatic switching to active database products.

## Demonstration sequence

1. Open the home page and point out the sample catalogue behavior when the database has no active products.
2. Show product search, category filtering and a real product detail page.
3. Place a direct order or sign in and demonstrate cart checkout.
4. Explain where stock validation occurs and why checkout uses a transaction.
5. Open the customer order history and explain ownership filtering.
6. Sign in as a superuser and show product, order, bulk request and low-stock management.
7. Close with the next engineering steps: automated tests, staff permissions and immutable order-line prices.
