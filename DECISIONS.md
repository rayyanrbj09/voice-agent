# Voice Agent Architecture Decisions

**Last updated:** 2026-09-14
**Verified test result:** 43 passed.

## Architecture

```text
HTTP API
  -> authentication and request validation
  -> VoiceAgent orchestration
  -> ToolRegistry / ToolExecutor
  -> user-scoped business tool
  -> SQLAlchemy session
  -> SQLite or PostgreSQL
```

## Decisions

### JWT authentication

JWT bearer tokens are used for stateless API authentication. Passwords are hashed with Argon2 through `pwdlib`. The authenticated backend supplies `user_id` to tools; the LLM never controls it.

### User-scoped data

Customers, appointments, orders, and support tickets carry ownership fields. Queries for customer-scoped records filter by both record ID and authenticated owner ID.

### Tool registry

Tools are registered with a name, description, callable, and input schema. This keeps the orchestration loop provider-independent and allows new business tools to be added without changing the API route.

### Customer-first actions

The model may search a customer by text, but action tools require a resolved `customer_id`. The executor validates required schema fields and returns a clear error when the customer has not been resolved.

### Tool errors are data, not success

Tool failures are returned to the model as error results so it can explain the failure. The backend additionally checks the final text: an action claim is suppressed when the latest tool result failed or when no action tool was called. This was added after observing false confirmations in the API response while database tables remained unchanged.

### Provider adapters

The agent uses a small provider protocol. Ollama is the default local provider; Anthropic is supported when configured. Provider-specific response formats are normalized into internal text and tool-use blocks.

### Database setup

SQLAlchemy models support SQLite for local development and PostgreSQL for deployment. Startup currently uses `Base.metadata.create_all`; schema migrations should be introduced before production changes.

### In-memory conversation memory

Conversation history is bounded and process-local. This is sufficient for the current API prototype but does not survive restarts or support multi-instance deployments. Persistent session storage is a future requirement.

## Implemented Components

- Authentication: `app/api/auth.py`, `app/core/security.py`
- Customer CRUD: `app/api/customers.py`, `app/db/repositories.py`
- Agent: `app/agent/orchestrator.py`, `app/agent/memory.py`, `app/agent/prompts.py`, `app/agent/guardrails.py`
- Tools: `app/tools/registry.py`, `app/tools/executor.py`, `app/tools/customer.py`, `app/tools/appointments.py`, `app/tools/orders.py`, `app/tools/support.py`
- Models: `User`, `Customer`, `Appointment`, `Order`, `SupportTicket`

## Known Limitations

- Business tools do not yet have dedicated REST CRUD routes.
- Tool commits do not yet have a centralized rollback wrapper.
- Tool error responses are intentionally generic at the final-response boundary; richer safe error details are needed.
- RAG and voice modules are not part of the active request path.
- There is no migration system, CI pipeline, coverage gate, or production load test.
- SQLAlchemy emits a `datetime.utcnow()` deprecation warning.
- FastAPI's current test client path emits a Starlette/httpx deprecation warning.

## Security Notes

- Use a random JWT secret of at least 32 bytes in deployed environments.
- Never log passwords, tokens, or sensitive customer data unnecessarily.
- Keep ownership filters in every customer-scoped query.
- Validate webhook signatures before adding the webhook phase.
- Treat LLM output as untrusted text and trust only confirmed tool results for state changes.
