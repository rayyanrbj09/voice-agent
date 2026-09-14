# Voice Agent Phases

**Last updated:** 2026-09-14
**Current state:** Core backend and agent orchestration complete; integrations and production hardening remain.
**Latest test result:** 43 passed.

## Status Summary

| Phase | Area | Status |
| --- | --- | --- |
| 1 | Core infrastructure and authentication | Complete |
| 2 | Customer management | Complete |
| 3 | Tool registry and execution | Complete |
| 4 | Agent orchestration | Complete for current providers |
| 5 | RAG | Pending |
| 6 | Voice I/O | Pending |
| 7 | Appointment business tools | Complete; API routes pending |
| 8 | Order business tools | Complete; API routes pending |
| 9 | Support-ticket business tools | Complete; API routes pending |
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
- Customer CRUD API
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

### Phases 7-9: Business Tools

Implemented tools:

- `book_appointment`, `list_appointments`, `cancel_appointment`
- `create_order`, `list_orders`
- `create_support_ticket`, `list_support_tickets`, `update_support_ticket`

These tools write to or read from the database and enforce authenticated-user ownership. They are available through the agent, but dedicated REST CRUD endpoints are not yet implemented.

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
- retries, transaction rollback, rate limits, and load testing

## Resolved Bug: False Success After Tool Failure

The logs exposed a serious behavior: an internal tool could fail while the LLM returned a successful-looking message. The database correctly contained no new appointment/order/ticket, but the API response claimed that one had been created.

The implemented fix is:

1. The executor validates required arguments.
2. Tool errors are returned to the orchestration loop as error results.
3. The final response guard checks the latest tool result.
4. Unsupported or failed action claims are replaced with a failure/request-for-details response.

This behavior is covered by regression tests in `tests/test_agent.py`.

## Next Recommended Order

1. Add integration tests that verify successful tool calls create rows in all three business tables.
2. Add REST endpoints for appointments, orders, and support tickets.
3. Improve error propagation and rollback behavior.
4. Add persistent memory and provider-independent end-to-end tests.
5. Implement RAG and voice integrations.
