# Voice Agent Phases

**Last updated:** 2026-09-25
**Current state:** Core backend, business REST APIs, agent orchestration, and business tools complete; RAG, Voice I/O, and production hardening remain.
**Latest test result:** 47 passed.

## Status Summary

| Phase | Area | Status |
| --- | --- | --- |
| 1 | Core infrastructure and authentication | Complete |
| 2 | Customer management | Complete |
| 3 | Tool registry and execution | Complete |
| 4 | Agent orchestration | Complete for current providers |
| 5 | RAG | Pending |
| 6 | Voice I/O | Pending |
| 7 | Appointment business tools & REST API | Complete |
| 8 | Order business tools & REST API | Complete |
| 9 | Support-ticket business tools & REST API | Complete |
| 10 | Calls and webhooks | Pending |
| 11 | Evaluation framework | Partial scaffolding |
| 12 | Production deployment and hardening | Pending |

## Completed

### Phase 1: Core Infrastructure and Authentication

- FastAPI application and health endpoints
- SQLAlchemy database/session setup
- Environment-based settings
- User registration, login, JWT validation, and current-user lookup
- Argon2 password hashing
- Authenticated API dependencies

### Phase 2: Customer Management

- Customer model and user ownership
- Customer CRUD API (`/customers`)
- Repository and Pydantic schema layers
- Search by name, email, phone, and company
- Cross-user access protection

### Phase 3: Tool Registry and Execution

- Extensible tool registry
- Tool metadata and JSON schemas
- Authenticated `user_id` injection by the executor
- Unknown-tool, duplicate-tool, invalid-argument, and tool-error handling
- Customer-first validation for customer-scoped actions

### Phase 4: Agent Orchestration

- Ollama and Anthropic provider adapters
- Multi-round tool-calling loop
- Bounded in-memory conversation memory
- Input guardrails
- Tool-result serialization
- False-success protection: the agent no longer confirms an action when the action tool failed or was never called

### Phases 7-9: Business Tools & REST APIs

Implemented tools & endpoints:

- **Appointments** (`/appointments`):
  - Agent tools: `book_appointment`, `list_appointments`, `cancel_appointment`
  - REST CRUD: `POST /appointments`, `GET /appointments`, `GET /appointments/{id}`, `PATCH /appointments/{id}`, `POST /appointments/{id}/cancel`, `DELETE /appointments/{id}`
- **Orders** (`/orders`):
  - Agent tools: `create_order`, `list_orders`
  - REST CRUD: `POST /orders`, `GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}`, `DELETE /orders/{id}`
- **Support Tickets** (`/support-tickets`):
  - Agent tools: `create_support_ticket`, `list_support_tickets`, `update_support_ticket`
  - REST CRUD: `POST /support-tickets`, `GET /support-tickets`, `GET /support-tickets/{id}`, `PATCH /support-tickets/{id}`, `DELETE /support-tickets/{id}`

All operations enforce authenticated-user ownership and customer ownership validation. Centralized rollback error handling is now included across all repository and tool write operations.

## Remaining Work

### Phase 5: RAG

The RAG modules exist as a starting structure. Production document ingestion, embedding storage, retrieval quality, citations, and agent integration remain.

### Phase 6: Voice I/O

STT, TTS, telephony, and WebSocket streaming are not integrated into the running API.

### Phase 10: Calls and Webhooks

Call lifecycle APIs, provider webhooks, recordings, and event verification remain.

### Phase 11: Evaluation

Datasets, metrics, and failure-analysis modules need a repeatable evaluation pipeline connected to real agent runs.

### Phase 12: Deployment and Hardening

- Alembic migrations
- CI/CD and coverage gates
- production secret management
- observability dashboards and tool failure metrics
- retries, rate limits, and load testing

## Resolved Bugs & Improvements

1. **False Success After Tool Failure**: Suppressed hallucinated confirmations if tools failed or were skipped (regression covered in `tests/test_agent.py`).
2. **`datetime.utcnow()` Deprecation**: Replaced deprecated `datetime.utcnow` with timezone-aware `utc_now` callable across all SQLAlchemy models.
3. **Transaction Rollback Protection**: Added explicit `db.rollback()` handling on commit exceptions in repositories and tools.
4. **Tool-to-REST Integration Verification**: Added automated integration tests verifying that rows created by agent tools are immediately retrievable via the REST API.

## Next Recommended Order

1. **Phase 6: Voice I/O**: Implement STT, TTS, and WebSocket audio streaming (`/ws/voice`).
2. **Phase 5: RAG**: Implement document chunking, embedding store, and a retrieval tool for the agent.
3. **Phase 10: Telephony & Webhooks**: Connect Twilio or SIP telephony.
4. **Phase 12: Deployment & Migrations**: Add Alembic database migrations and production setup.
