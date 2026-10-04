# Delhi Stationery Upcoming Feature Roadmap

The original ten feature areas are implemented in the repository. The next work should close a privacy and operations gap before expanding the product. A secure order lookup and a rehearsed staging release matter more to launch than adding a gateway or a React frontend immediately.

## Priority 0: before a real-customer pilot

| Work item | Why it matters | Acceptance criteria |
| --- | --- | --- |
| Secure public order lookup | The current lookup accepts a phone number and/or sequential order ID without ownership verification. Phone-only search returns all matching orders, while an ID alone can return one. Results include names, phone numbers, delivery addresses, purchase totals, payment state, and status history. | Require a logged-in owner or a private high-entropy token scoped to one order; expire/revoke links; rate-limit attempts; return only minimal details; avoid raw-token logging and referrer leakage. |
| Deploy a production-like staging environment | Deployment settings in source control do not create a working deployment. | Real PostgreSQL, TLS, allowed hosts, static files, durable media, secret-store values, SMTP, and deployment checks all work in staging. |
| Rehearse database and media recovery | Product images live outside the database and must be restored with it. | Restore the PostgreSQL dump and matching media archive to an isolated environment; verify products, images, orders, logins, staff permissions, and checkout. |
| Confirm pilot payment and fulfilment procedures | UPI is recorded and verified by staff; delivery is updated manually. | Customer-facing wording and staff steps clearly explain COD/manual UPI; staff can reconcile a transaction and update dispatch details without implying an automated provider integration. |

## Priority 1: first improvements after the pilot is safe

| Feature | Benefit | Suggested implementation slice |
| --- | --- | --- |
| Parent orders and order items | A cart purchase needs one order identity, address, payment state, and delivery fee rather than one order row per product. | Add `Order` and `OrderItem` models, a checkout grouping identifier for legacy rows, a staged data migration, then change checkout, cancellation, invoices, customer history, and staff workflows. |
| PostgreSQL concurrency coverage | SQLite does not provide equivalent row-lock behavior for the oversell protection design. | Add a PostgreSQL CI or staging job for concurrent attempts to buy the last units and for duplicate quote acceptance. |
| Email outbox and retries | Synchronous best-effort email can be lost when the provider is down. | Persist notification events transactionally, deliver them with a worker, retry transient errors, and expose delivery state to staff. Choose a queue only when deployment operations can support it. |
| Monitoring and structured logs | A running process alone does not show failed checkout, mail, or database health. | Add an error-reporting service, health endpoint, request/error logs with sensitive data redacted, and alerts for database and mail failures. |
| Payment-provider integration | Automated confirmation, capture, and refunds require a provider integration. | Select a provider; build a test-mode flow, verify webhook signatures, store unique provider event IDs, make event handling idempotent, then add reconciliation and refund callbacks. |

## Priority 2: scale operations when demand proves the need

| Feature | When to consider it | Guardrail |
| --- | --- | --- |
| Carrier integration | Staff are spending too much time on manual labels and status entry. | Start with one fulfilment partner and verify webhook signatures and retry/idempotency behavior. |
| Quote PDF and revision history | Schools or offices need formal, printable offers or revised pricing. | Preserve each accepted version and its prices; do not silently edit a customer-approved quote. |
| Barcode scan-to-stock | Receiving products by keyboard is slow or error-prone. | Build a staff-only scan workflow that records each stock movement and handles unknown codes explicitly. |
| Search and catalogue analytics | Database query time or customer findability becomes a measured issue. | Inspect query plans and add indexes first; introduce an external search service only for measured needs. |
| React customer interface or FastAPI service | A separate product requirement needs richer client interactions or an independent API. | Keep Django as the system of record, define API contracts and authentication, and create a separate demonstrable project scope. Do not add these technologies solely to increase the stack list. |

## Suggested sequence

1. Close the phone-only tracking exposure.
2. Deploy to staging and prove PostgreSQL, HTTPS, email, media persistence, and restore.
3. Run a controlled COD/manual-UPI pilot with a short release checklist.
4. Measure support issues and store workload.
5. Build parent-order grouping and PostgreSQL concurrency coverage.
6. Add provider integrations or queue-based notifications only when the business workflow needs them.

## Decision rule

The current feature set is enough to demonstrate practical Django skills in an interview. Feature count is not a substitute for a safe customer release. For a real pilot, close the Priority 0 gates first; for interviews, prepare to explain the implemented design, the tracking privacy issue and its fix, and the order-row grouping trade-off honestly.
