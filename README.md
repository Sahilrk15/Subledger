# SubLedger - SaaS Subscription & Billing System

A clean billing backend built with **FastAPI + SQLAlchemy**: plans, customers, subscriptions, invoices, payments and an
append-only ledger. Routes, services, repositories, models, schemas, config and DB logic are kept in separate layers.

> Design documentation (ERD, service and repository tables, business-rule ownership, design pattern, invoice and payment flows) is in **[DESIGN.md](DESIGN.md)**.

## Tech stack
Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, PostgreSQL (Docker) / SQLite (local and tests), pytest, Docker Compose.

## Project structure
```
app/
  main.py            FastAPI app, error handler, router registration
  config.py          environment-based settings
  db.py              engine, session, Base, per-request transaction
  dependencies.py    dependency injection wiring
  exceptions.py      domain errors
  models/            SQLAlchemy models + enums
  schemas/           Pydantic request / response models
  repositories/      database access only
  services/          business rules and workflows
  routes/            HTTP endpoints
  utils/billing.py   billing period calculation
tests/               pytest suite (36 tests)
postman/             Postman collection
DESIGN.md            low-level design
```

## Setup option A - Docker (recommended)
Requires Docker Desktop to be running.

```bash
docker compose up --build
```
* API: http://localhost:8000
* Swagger UI: http://localhost:8000/docs
* Health check: http://localhost:8000/health

Stop with `Ctrl+C`, then `docker compose down` (add `-v` to also delete the database volume).

Run the tests inside the container (in a second terminal while it is up):
```bash
docker compose exec api pytest -q
```

## Setup option B - local (no Docker)
```bash
python -m venv .venv

# activate the virtual environment
#   Windows (PowerShell):  .venv\Scripts\Activate.ps1
#   Windows (cmd):         .venv\Scripts\activate.bat
#   macOS / Linux:         source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # macOS / Linux: cp .env.example .env
uvicorn app.main:app --reload
```
Uses a local SQLite file (`subledger.db`) by default. Swagger UI is at http://localhost:8000/docs.

## Running the tests
```bash
pytest -q
```
Tests use an in-memory SQLite database, so no setup is needed. They cover every business rule:
price > 0, unique email, inactive plan, duplicate active subscription, invoice amount from plan price,
overpayment, partial and full payment status, failed payment, append-only ledger and `reference_id` traceability,
plus atomic rollback and unit tests of `PaymentService` with fake repositories.

## Configuration
| Variable | Default | Meaning |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./subledger.db` | SQLAlchemy database URL (Docker Compose sets PostgreSQL) |
| `INVOICE_DUE_DAYS` | `7` | Days between invoice issue date and due date |

See `.env.example`.

## API list
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/plans` | Create a subscription plan |
| GET | `/plans` | List plans (`?status=active`) |
| GET | `/plans/{plan_id}` | Get one plan |
| PATCH | `/plans/{plan_id}` | Update / deactivate a plan (`{"status": "inactive"}`) |
| POST | `/customers` | Create a customer |
| GET | `/customers` | List customers |
| GET | `/customers/{customer_id}` | Fetch customer details |
| GET | `/customers/{customer_id}/ledger` | Fetch customer ledger history (`?entry_type=`, `?invoice_id=`) |
| POST | `/subscriptions` | Create a subscription (`"activate": false` creates a pending one) |
| GET | `/subscriptions` | List subscriptions (`?customer_id=`, `?status=`) |
| GET | `/subscriptions/{subscription_id}` | Fetch one subscription |
| PATCH | `/subscriptions/{subscription_id}/activate` | Activate a pending subscription |
| PATCH | `/subscriptions/{subscription_id}/cancel` | Cancel a subscription |
| POST | `/invoices/generate` | Generate an invoice for a subscription |
| GET | `/invoices/{invoice_id}` | Fetch invoice details |
| POST | `/payments/record` | Record a payment attempt (success or failed) |
| GET | `/health` | Health check |

List endpoints accept `skip` and `limit`. Errors return `{"detail": "..."}` with 404 (not found), 409 (conflict / duplicate / wrong state),
400 (business rule broken) or 422 (invalid input).

### Quick walkthrough (Swagger or Postman)
1. `POST /plans` `{"name":"Pro","billing_cycle":"monthly","price":"499.00","currency":"INR"}`
2. `POST /customers` `{"name":"Asha Patil","email":"asha@example.com","company_name":"Acme"}`
3. `POST /subscriptions` `{"customer_id":1,"plan_id":1}`
4. `POST /invoices/generate` `{"subscription_id":1}` -> invoice with `amount_due 499.00`, status `issued`
5. `POST /payments/record` `{"invoice_id":1,"amount":"200.00","currency":"INR","status":"success","provider_reference":"pg_001"}` -> `partially_paid`
6. `POST /payments/record` `{"invoice_id":1,"amount":"299.00","currency":"INR","status":"success","provider_reference":"pg_002"}` -> `paid`
7. `GET /customers/1/ledger` -> `invoice_created`, `payment_success`, `payment_success`

A ready-made Postman collection is in `postman/SubLedger.postman_collection.json` (import it, then run the folders in order;
ids are saved to collection variables automatically).

## Assumptions
* Amounts are decimals with two places; JSON responses return them as strings (`"499.00"`) to avoid float errors.
* Creating a subscription activates it by default. Passing `"activate": false` creates a `pending` one that can be activated later.
* The billing period starts on the subscription start date; `current_period_end` is exclusive.
* An invoice is created with status `issued`; its due date is `INVOICE_DUE_DAYS` after the issue date.
* `amount_due` is a snapshot of the plan price when the invoice is generated; later plan price changes do not alter existing invoices.
* Existing active subscribers can still be invoiced after their plan is deactivated (only *new* subscriptions are blocked).
* Failed payment attempts are stored and written to the ledger, but never change `amount_paid` or the invoice status.
* Ledger `reference_id` is `INV-<invoice id>` for invoice events and `PAY-<payment attempt id>` for payment events.
* Customer emails are stored lower-case, so `A@x.com` and `a@x.com` count as the same email.
* Each API request is one database transaction (committed on success, rolled back on any error).

## Limitations
* No real payment gateway, authentication, frontend, taxes or proration (out of scope in the brief).
* Tables are created on startup with `create_all`; there are no migrations (Alembic would be the next step).
* Invoices are never moved to `overdue` automatically (no scheduler) and there is no endpoint to void an invoice; the statuses exist in the model for future use.
* Subscriptions do not auto-renew: `current_period_*` does not advance, and the next invoice is generated with an explicit `period_start` / `period_end`.
* Cancelling a subscription does not void its unpaid invoices.
* Payments are one-by-one; there are no refunds.
