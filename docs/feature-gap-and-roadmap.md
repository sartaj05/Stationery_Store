# Delhi Stationery Feature Gap and Roadmap

## Current project

Delhi Stationery is a Django 5.2 server-rendered store. It includes a public catalogue, product search and category filtering, direct product orders, a session cart, authenticated checkout, customer profiles and order history, phone-based order lookup, bulk enquiries, and a custom dashboard.

The dashboard views currently require a Django superuser. They manage products and categories, update order and enquiry status, view customer history, restock inventory, print invoices, and export CSV files. Timestamps use Django's automatic creation and update fields.

The sample catalogue is generated in memory and appears only when there are no active products in the database. It is not seed data and does not create orderable database products. The sample product illustrations are now served from the app's static files, so the empty-state catalogue does not depend on Unsplash or another external image host.

## Ten recommended features

| Priority | Feature | Current gap | Suggested first slice |
| --- | --- | --- | --- |
| 1 | Automated tests and CI | Implemented: Django tests now cover the core storefront and access flows, and GitHub Actions runs checks and tests for pushes and pull requests. | Expand regression coverage as each feature lands; keep CI green before merging changes. |
| 2 | Staff roles and permissions | Custom dashboard access checks `is_superuser`; there is no limited store-manager or inventory-staff role. | Define Django groups and permissions for catalogue, orders, customers and reports, then enforce them per view. |
| 3 | Order items and price snapshots | A cart creates one `Order` per product. `Order.total_price()` reads the product's current price, and deleting a product cascades to its orders. Product edits or deletions can change or erase historical order data. | Add a checkout/order record with related line items that store product name, SKU, unit price and quantity at purchase time. Protect referenced products or use soft deletion. |
| 4 | Payment lifecycle | `COD` and `UPI` are stored as choices; there is no payment gateway, transaction reference, refund state or verified payment status. | Add explicit payment status and provider reference fields, then integrate a provider in test mode before accepting live payments. |
| 5 | Inventory movement history | Stock decreases and restocks update the product quantity directly; there is no auditable movement ledger. | Record each sale, cancellation, manual adjustment and restock with quantity delta, actor, reason and timestamp. |
| 6 | Order status history and customer notifications | An order stores only its current status and internal note; status changes do not create history or send notifications. | Add status-event records and send email notifications for confirmation, dispatch, delivery and cancellation. |
| 7 | Delivery zones and tracking | Delivery copy is static and there is no postal-code serviceability check, delivery charge, dispatch assignment or carrier tracking number. | Make serviceable pincodes, delivery fee rules and delivery state configurable, then add a tracking reference to orders. |
| 8 | Bulk quote to order conversion | Bulk requests can be marked `QUOTED` or `CONVERTED`, but there is no quote builder or conversion workflow. | Let staff prepare quantities and a quote, share it with the requester, and convert an accepted quote into an order. |
| 9 | Product discovery and catalogue operations | Search and category filtering exist, but the public catalogue has no pagination, SKU/barcode workflow, customer reviews, wishlist or promotion rules. | Start with pagination and SKU fields; add wishlist, reviews or coupons after customer demand is validated. |
| 10 | Production deployment and operations | Settings use `DEBUG=True`, an in-file development secret, localhost-only hosts and SQLite. Uploaded media has no durable production storage configured. | Move secrets to environment configuration, use PostgreSQL, configure HTTPS, persistent media, backups, error monitoring and a deployment checklist. |

## Suggested delivery order

Automated tests and CI are in place. Next add staff permissions and immutable order-item price snapshots because they protect store operations and historical business records. Then add payment and inventory history. Customer notifications, delivery tracking and bulk conversion can follow as the fulfilment workflow matures. Catalogue enhancements should be prioritized from real customer usage.

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
- Historical totals remain unchanged after product prices are edited.
- A checkout failure leaves both inventory and the cart in a consistent state.
- No production secret or debug setting is committed to source control.
