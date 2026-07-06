# WHATSAPPGPT

AI Customer Support SaaS built on WhatsApp.

## Stack

Frontend:

* Next.js 15
* React
* TypeScript
* Tailwind

Backend:

* FastAPI
* SQLAlchemy 2
* PostgreSQL 17
* Redis
* RQ

Messaging:

* WAHA Core

AI:

* Gemini
* OpenRouter

Architecture:

* One Company
* One WAHA Container
* One Port
* One Session (default)
* One WhatsApp Account

Knowledge Sources:

Static:

* prompt.txt
* examples.json
* sales_guidelines.json
* objections.json

Dynamic:

* knowledge_faq
* knowledge_products
* knowledge_services
* company_profiles

Conversation Memory:

* Redis

Current Version:
V1

Goals:

* Authentication
* Dashboard
* Companies
* Subscriptions
* WAHA Integration
* Redis Memory
* Reports
* Trial System
