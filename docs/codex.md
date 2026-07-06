# WHATSAPPGPT Backend Migration Specification

## Goal

Transform the existing Flask prototype into a production-ready SaaS backend using FastAPI.

The objective is to build V1 Backend only.

No frontend.

No Docker deployment automation.

No real container creation.

Only APIs, architecture, models and services.

Old Flask application remains as reference.

app.py must not be modified.

Treat it as legacy code.

---

## Repository Information

Project name:

WHATSAPPGPT

Current branch:

web_WhatsGPT

Ignore these folders completely:

app_version/

data/

test/

Do not scan them.

Do not migrate them.

Do not use them.

---

## Existing Assets

Database schema already exists.

Use existing SQL files as source of truth.

database/

01_extensions.sql

02_enums.sql

03_tables.sql

04_indexes.sql

05_seed.sql

Documentation already prepared.

docs/

api.md

architecture.md

states.md

workflows.md

workers.md

webhook.md

retrieval.md

redis.md

security.md

stack.md

roadmap.md

env.md

Companies examples already exist.

companies/

Each company contains static knowledge files.

Keep this design.

---

## Tech Stack

Backend

FastAPI

SQLAlchemy 2

Pydantic v2

Alembic

PostgreSQL

Redis

RQ

JWT Authentication

bcrypt

httpx

Docker SDK placeholder only

WAHA Core

Gemini

OpenRouter

Python 3.12

---

## Folder Structure

Create:

backend/

app/

api/

core/

db/

models/

schemas/

services/

repositories/

workers/

utils/

main.py

alembic/

requirements.txt

.env.example

README.md

Do not remove existing database folder.

Do not remove companies folder.

Do not delete app.py.

---

## Authentication

Implement:

POST /auth/register

POST /auth/login

POST /auth/logout

POST /auth/refresh

GET /auth/me

JWT authentication.

Role system:

ADMIN

CUSTOMER

Password hashing:

bcrypt

---

## Companies

Implement APIs from docs/api.md

Companies support:

one company

↓

one WAHA container

↓

one reserved port

↓

one default session

↓

one WhatsApp account

Company statuses:

TRIAL

ACTIVE

EXPIRED

SUSPENDED

Trial duration:

7 days maximum

Trial may finish earlier if Gemini free keys become exhausted.

Customer may upgrade before trial ends.

---

## Plans

Use existing plans table.

Seed already exists.

Basic Plan.

No billing implementation required.

Subscriptions only.

---

## WAHA

Current version:

WAHA Core

Session name always:

default

No multi-session.

No WAHA Plus.

Implement service layer only.

services/waha_service.py

Methods:

create_instance()

get_status()

get_qr()

restart()

stop()

Leave Docker implementation as TODO.

No docker.from_env execution.

No real container creation.

Only architecture.

WAHA states:

CREATED

STARTING

WAITING_QR

CONNECTED

DISCONNECTED

FAILED

---

## Knowledge Design

Static knowledge remains filesystem based.

companies/{slug}/

prompt.txt

examples.json

sales_guidelines.json

objections.json

Dynamic knowledge belongs to PostgreSQL.

knowledge_faq

knowledge_products

knowledge_services

company_profiles

Implement CRUD APIs.

---

## Conversation Memory

Redis based.

conversation:{company_id}:{customer_id}

store last 5 messages

TTL = 7 days

Rate limit cache:

rate_limit:{company_id}

TTL 60 seconds

Provider rotation:

provider_rotation:{company_id}

TTL 1 hour

WAHA status cache:

waha_status:{company_id}

TTL 5 minutes

Dashboard cache:

dashboard_stats:{company_id}

TTL 5 minutes

---

## Webhook Pipeline

Implement architecture matching docs/webhook.md

Webhook flow:

Validate Company

Validate Message Type

Ignore Group

Ignore Broadcast

Ignore Status

Load Company Config

Load Conversation Memory

Retrieve Knowledge

Build Prompt

Call Provider

Save Message

Update Stats

Send Reply

Done

---

## AI Providers

Gemini

OpenRouter

Use ai_providers table.

Encrypted keys.

Provider rotation support.

Gemini trial keys supported.

OpenRouter paid mode supported.

No OpenAI implementation required yet.

Only architecture placeholder.

---

## Workers

Create workers package.

Implement placeholders.

CreateContainerWorker

ReconnectWorker

AnalyticsWorker

ReportWorker

CleanupWorker

No scheduling implementation required.

Only architecture.

RQ ready.

Redis ready.

---

## Reports

Daily

Weekly

Monthly

Generate service only.

No PDF generation.

No email delivery.

Only backend preparation.

---

## Alembic

Initialize Alembic.

Connect it to SQLAlchemy models.

Do not modify existing SQL files.

SQL files remain source documentation.

Alembic is for future migrations only.

---

## Security

JWT

bcrypt

RBAC

Encrypted provider keys

Audit logs

Webhook validation

Redis rate limiting

Secure settings management

---

## Environment Variables

Prepare .env.example

DATABASE_URL=

REDIS_URL=

JWT_SECRET=

ENCRYPTION_KEY=

DOCKER_HOST=

OPENROUTER_API_KEY=

WAHA_MASTER_API_KEY=

BACKEND_URL=

FRONTEND_URL=

---

## Deliverables

Generate complete FastAPI backend architecture.

Generate SQLAlchemy models.

Generate Pydantic schemas.

Generate repositories.

Generate services.

Generate routers.

Generate dependencies.

Generate authentication.

Generate Redis integration.

Generate Alembic setup.

Generate requirements.txt.

Generate README.md.

Keep app.py untouched.

Treat app.py as legacy reference only.

Do not generate frontend.

Do not generate Next.js.

Do not implement Docker execution.

Do not inspect:

app_version/

data/

test/

Read documentation from docs/.

Follow docs as source of truth.
