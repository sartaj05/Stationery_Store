# Delhi Stationery Feature Gap and Roadmap

## Current project

Delhi Stationery is a Django 5.2 server-rendered store. It includes a public catalogue, product search and category filtering, direct product orders, a session cart, authenticated checkout, customer profiles and order history, phone-based order lookup, bulk enquiries, and a custom dashboard.

The staff workspace uses Django permissions and groups to scope catalogue, inventory, order, bulk-request, and customer-account access. Superusers retain full access; the `setup_store_roles` management command creates the standard staff groups. Store operations include product/category management, order and enquiry status updates, customer history, restocking, invoices, and CSV exports.

The sample catalogue is generated in memory and appears only when there are no active products in the database. It is not seed data and does not create orderable database products. The sample product illustrations are now served from the app's static files, so the empty-state catalogue does not depend on Unsplash or another external image host.

## Ten recommended features

| Priority | Feature | Current gap | Suggested first slice |
| --- | --- | --- | --- |
| 1 | Automated tests and CI | Implemented: Django tests now cover the core storefront and access flows, and GitHub Actions runs checks and tests for pushes and pull requests. | Expand regression coverage as each feature lands; keep CI green before merging changes. |
| 2 | Staff roles and permissions | Implemented: scoped Django permissions protect staff modules, templates hide unavailable actions, and `python manage.py setup_store_roles` creates seven standard groups. | Assign each staff account only the group needed for its work; review permissions whenever a new staff feature is added. |
| 3 | Order items and price snapshots | Snapshot implementation complete: every order row stores product name, brand, category and unit price at purchase time; existing rows are backfilled, totals use the snapshot, and referenced products are protected from deletion. Cart checkout still creates one order row per product rather than grouping a multi-product cart under a single order number. | Consider parent-order grouping and SKU snapshots when receipts or fulfilment need one order record for a whole cart. |
| 4 | Payment lifecycle | Implemented manual lifecycle: orders track unpaid/pending/verified/failed/partial-refund/refunded states, transaction and refund references, refund amount, and timestamps; staff updates validate the transitions. No gateway or webhook is connected. | Select a payment provider, then add signed, idempotent webhook processing in the provider's test environment before live payment acceptance. |
| 5 | Inventory movement history | Implemented: sales, cancellations, restocks, opening balances and signed manual adjustments create immutable records with actor, reason, timestamp and optional order; stock cannot be edited through catalogue forms or the admin list. Existing quantities are seeded as opening balances; older sales cannot be reconstructed. | Add reconciliation reports and a controlled stock-count workflow if the store begins periodic physical counts. |
| 6 | Order status history and customer notifications | Implemented: immutable status events show on customer tracking, account order history and staff detail pages; customers with an account email or optional checkout email are notified at order placement and each status change. Existing orders receive a current-state baseline event. Email uses Django's configured backend and delivery failures are best-effort. | Configure a real production mail backend and monitor delivery failures; add queued retries if volume requires them. |
| 7 | Delivery zones and tracking | Delivery copy is static and there is no postal-code serviceability check, delivery charge, dispatch assignment or carrier tracking number. | Make serviceable pincodes, delivery fee rules and delivery state configurable, then add a tracking reference to orders. |
| 8 | Bulk quote to order conversion | Bulk requests can be marked `QUOTED` or `CONVERTED`, but there is no quote builder or conversion workflow. | Let staff prepare quantities and a quote, share it with the requester, and convert an accepted quote into an order. |
| 9 | Product discovery and catalogue operations | Search and category filtering exist, but the public catalogue has no pagination, SKU/barcode workflow, customer reviews, wishlist or promotion rules. | Start with pagination and SKU fields; add wishlist, reviews or coupons after customer demand is validated. |
| 10 | Production deployment and operations | Settings use `DEBUG=True`, an in-file development secret, localhost-only hosts and SQLite. Uploaded media has no durable production storage configured. | Move secrets to environment configuration, use PostgreSQL, configure HTTPS, persistent media, backups, error monitoring and a deployment checklist. |

## Suggested delivery order

Automated tests and CI, scoped staff roles, immutable order price snapshots, a manual payment lifecycle, inventory movement history, and order status notifications are in place. Next add delivery zones and tracking. Bulk conversion and catalogue enhancements can follow as fulfilment matures and customer usage becomes clearer.

## Important behavior to retain

- Keep sample products outside the database and non-orderable.
- Show the real active database catalogue as soon as at least one active product exists.
- Keep inactive database products out of the public catalogue.
- Preserve stock checks at both cart interaction and checkout.
- Scope customer order history to the logged-in customer.

## Release acceptance checklist

- Migrations apply cleanly on a fresh database.
- Tests cover quantity validation, stock reduction, stock restoration on allowed cancellation, and order visibility.
- Dashboard access is checked for anonymous users, ordinary customers, staff users and superusers.
- Historical totals remain unchanged after product prices are edited, and referenced products cannot be deleted.
- A checkout failure leaves both inventory and the cart in a consistent state.
- No production secret or debug setting is committed to source control.
