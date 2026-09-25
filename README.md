# Voice Agent

FastAPI backend for an authenticated customer assistant with customer search, appointments, orders, support tickets, REST APIs, and LLM tool orchestration.

## Current Status

The core backend, REST APIs, and agent workflow are implemented. The application can authenticate users, manage customers, manage appointments, orders, and support tickets via REST endpoints or LLM tools, and expose conversational agent chat through `POST /agent/chat`.

The latest full test run passed **47 tests** with 0 failures.

## Implemented

### API and authentication

- `GET /` and `GET /health` in [app/main.py](app/main.py)
- `POST /auth/register`, `POST /auth/login`, and `GET /auth/me` in [app/api/auth.py](app/api/auth.py)
- JWT authentication and Argon2 password hashing in [app/core/security.py](app/core/security.py)
- Environment configuration through pydantic-settings in [app/core/config.py](app/core/config.py)
- Authenticated customer CRUD routes in [app/api/customers.py](app/api/customers.py)
- Authenticated appointment CRUD and cancellation routes in [app/api/appointments.py](app/api/appointments.py)
- Authenticated order CRUD routes in [app/api/orders.py](app/api/orders.py)
- Authenticated support ticket CRUD routes in [app/api/support.py](app/api/support.py)
- `POST /agent/chat` in [app/api/agent.py](app/api/agent.py)

### Database and Repositories

- [app/db/models.py](app/db/models.py) defines `users`, `customers`, `appointments`, `orders`, and `support_tickets` tables. Uses timezone-aware UTC datetime defaults.
- [app/db/repositories.py](app/db/repositories.py) provides isolated, user-scoped data access with transaction rollback protection on errors.

### Agent and tools

- Ollama and Anthropic provider adapters in [app/agent/orchestrator.py](app/agent/orchestrator.py)
- Bounded in-memory conversation history in [app/agent/memory.py](app/agent/memory.py)
- Input validation in [app/agent/guardrails.py](app/agent/guardrails.py)
- Tool registry and authenticated user-context injection in [app/tools/registry.py](app/tools/registry.py) and [app/tools/executor.py](app/tools/executor.py)
- Customer search by name, email, phone, or company
- Appointment booking, listing, and cancellation
- Order creation and listing
- Support ticket creation, listing, and updates

All customer-scoped tools and REST routes verify that records belong to the authenticated user. The LLM cannot provide or override `user_id`; the backend injects it.

## Customer-First Workflow

For appointment, order, and support-ticket actions, the agent must resolve a customer before calling the action tool:

```text
search_customer -> customer_id -> book/create/update tool
```

The executor rejects missing required arguments and provides customer-resolution guidance when `customer_id` is absent.

## Tool Failure and False-Success Bug

An earlier agent behavior allowed the LLM to return text such as "I booked the appointment" after an internal tool had failed, or after only `search_customer` had run. This caused misleading API responses and made the database appear empty even though the response claimed success.

The fix is implemented in [app/agent/orchestrator.py](app/agent/orchestrator.py): final responses are inspected for action claims, claims are rejected when no action tool ran, success claims are suppressed when the latest tool result contains an error, and the user receives a failure message instead of fabricated confirmation.

The regression is covered by tests for both unsupported action claims and failed-tool success claims.

## Quick Start

Create `.env` in the project root:

```env
DATABASE_URL=sqlite:///./voice_agent.db
JWT_SECRET_KEY=replace-with-a-random-secret-at-least-32-characters
AGENT_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b
```

Install and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open Swagger UI at `http://localhost:8000/docs`.

For Docker, use `docker compose up --build`.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
```

Latest verified result: **47 passed**.

## Remaining Work

- Complete Phase 6: Voice I/O (STT, TTS, WebSocket bidirectional streaming).
- Complete Phase 5: RAG ingestion, embeddings, and retrieval integration.
- Complete Phase 10: Telephony (Twilio/SIP) and call webhook workflows.
- Replace startup `create_all` with Alembic migrations.
- Add persistent conversation memory and production session storage.
- Add CI, coverage thresholds, structured tool-result metrics, and end-to-end provider tests.

## Repository Documents

- [PHASES.md](PHASES.md): current completion status and roadmap
- [DECISIONS.md](DECISIONS.md): architecture and implementation decisions
- [TEST_RESULTS.md](TEST_RESULTS.md): latest test evidence and warnings
