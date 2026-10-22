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

## Screenshots
<img width="1920" height="970" alt="SS2" src="https://github.com/user-attachments/assets/49a2eab2-8eb1-4666-9810-11ca27bdc712" />
<img width="1920" height="969" alt="SS1" src="https://github.com/user-attachments/assets/461786f3-5b1f-4fc2-8220-acf29d14e04d" />
<img width="1920" height="1022" alt="Plans4" src="https://github.com/user-attachments/assets/944000f0-0df6-47f8-8de1-d348943f356a" />
<img width="1920" height="1019" alt="Plans3" src="https://github.com/user-attachments/assets/91c2593c-a111-46c2-8057-ee689f8558ff" />
<img width="1920" height="1023" alt="Plans2" src="https://github.com/user-attachments/assets/d90a3935-0dc3-4e94-be82-50c81ca2f603" />
<img width="1920" height="1022" alt="Plans1" src="https://github.com/user-attachments/assets/17b4a776-8452-4dc2-8248-1db7746047e8" />
<img width="1920" height="1026" alt="Health1" src="https://github.com/user-attachments/assets/118f3435-65c7-4b83-b832-808455196640" />
<img width="1920" height="1016" alt="{FD8441EE-90AF-4F08-97B5-9A52700951F3}" src="https://github.com/user-attachments/assets/d0181122-358a-4cfd-a3f1-be90f1091715" />
<img width="1920" height="1017" alt="{D66CCD3E-9FF7-43DD-B9BA-3EC6F9709E2D}" src="https://github.com/user-attachments/assets/07ab65bc-3f79-4cc9-9ddf-c5df4fe3b577" />
<img width="1920" height="1020" alt="{CCDE5945-63B1-4769-9E1D-86A9FC64A5FC}" src="https://github.com/user-attachments/assets/113a6c2f-4eec-421d-ae75-a3268aa8aa55" />
<img width="1920" height="1020" alt="{C140B688-08A8-447B-81FE-C89CD4416463}" src="https://github.com/user-attachments/assets/3e3e2393-49f0-4b0d-a39c-e974af6b9876" />
<img width="1915" height="1023" alt="{BFCABF1B-632F-4CED-8733-34E2526A1435}" src="https://github.com/user-attachments/assets/bacf3564-9d7e-450d-871e-4306d25579bc" />
<img width="1920" height="1020" alt="{BB7D1234-D846-4860-A410-4754ED21DDDC}" src="https://github.com/user-attachments/assets/0e1eed63-3ea2-4881-a6ac-07bb73d72b72" />
<img width="1920" height="1023" alt="{A281A9F3-318A-4194-8967-14D27A3C12F0}" src="https://github.com/user-attachments/assets/f9b067e1-5704-46e1-95b9-5b4e5439028e" />
<img width="1919" height="1023" alt="{8319856F-0112-4D21-9E19-E896AC2D39A9}" src="https://github.com/user-attachments/assets/8b2c2124-178b-4e5b-9657-8e3cb77360c0" />
<img width="1920" height="1026" alt="{49557B0A-5E7B-422B-9C19-CB416F252EB4}" src="https://github.com/user-attachments/assets/779b5b6e-a03e-4a40-965f-441bf1f4d167" />
<img width="1920" height="1024" alt="{8227E171-094E-48CE-861B-809FB7F25D6B}" src="https://github.com/user-attachments/assets/4f848432-1256-40b0-a175-fca2cbe06d0b" />
<img width="1920" height="1023" alt="{7591CFE9-12F8-43FA-966D-0B8E21C1EE9E}" src="https://github.com/user-attachments/assets/9d873cd5-e16d-4a94-91ce-b72469baa4fa" />
<img width="1920" height="1022" alt="{538CFFC9-4551-491A-9639-D29AF952C060}" src="https://github.com/user-attachments/assets/46431ad1-e9ca-4324-ae6e-5c5be542f343" />
<img width="1920" height="1021" alt="{6BCE9235-57F9-49A6-A5C2-2261D4321B79}" src="https://github.com/user-attachments/assets/ec34526d-d2e3-41e6-90a2-fea6a89da2dd" />
<img width="1919" height="1020" alt="{4FB7E43D-1A8F-4314-9285-D5A68BEE96BB}" src="https://github.com/user-attachments/assets/b87e2746-2d54-4190-9499-e0ad4dd5ea5c" />
<img width="1920" height="1021" alt="{4A79DF06-4272-4595-813A-5C69925C8600}" src="https://github.com/user-attachments/assets/ca52ac8e-b9c7-40c1-af90-8fbbeed7dcc0" />
<img width="1920" height="1020" alt="{3C54E11B-E87A-4666-8742-0967F24054D6}" src="https://github.com/user-attachments/assets/95f41315-09ef-4032-be98-c46b65199728" />
<img width="1919" height="1019" alt="{2CA8122C-D830-476A-ACEB-369340EDBBE2}" src="https://github.com/user-attachments/assets/9c60d8a7-46c5-4b7f-91b4-660331fbec00" />
<img width="1920" height="1022" alt="{0D3D2037-B391-429B-9709-DE57C6F166B3}" src="https://github.com/user-attachments/assets/7a66b6fb-551a-4aa8-b2de-8339d8d96e21" />
