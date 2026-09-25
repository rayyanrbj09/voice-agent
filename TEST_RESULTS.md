# Test Results

**Latest run:** 2026-09-25
**Command:** `.venv\Scripts\python.exe -m pytest tests/ -q`
**Result:** **47 passed, 0 failed**
**Duration:** 13.31 seconds

## Coverage by Area

| Area | Status | Evidence |
| --- | --- | --- |
| Authentication | Passing | registration, login, JWT, invalid-token, and account checks |
| Customer API | Passing | CRUD, validation, authentication, and ownership isolation |
| Appointments API | Passing | CRUD, cancellation, filtering, customer check, cross-user isolation |
| Orders API | Passing | CRUD, conflict handling on order_number, cross-user isolation |
| Support Tickets API | Passing | CRUD, status & priority updates, filtering, cross-user isolation |
| Tool-to-REST Integration | Passing | rows created by agent tools are immediately retrievable via REST API |
| Tool registry | Passing | registration, lookup, listing, duplicate and unknown-tool handling |
| Tool executor | Passing | user-context injection, required arguments, customer-first errors |
| Business tools | Passing | appointments, orders, support tickets, validation, and ownership |
| Agent orchestration | Passing | provider adapters, tool loop, memory, guardrails, serialization |
| False-success regression | Passing | no success claim after missing action tool or failed tool result |

## Important Regressions & Improvements Covered

1. **Tool-to-REST Row Visibility**: Tests verify that appointments, orders, and support tickets created through internal tools are immediately queryable via their respective REST API routes.
2. **False Success Prevention**: A failed action produces a failure/request-for-details response rather than fabricated success text.
3. **Database Rollbacks**: Exception handling now triggers `db.rollback()` across all repository and tool write operations.
4. **Resolved SQLAlchemy Deprecation**: Replaced `datetime.utcnow` with `utc_now` callable, eliminating 50 SQLAlchemy deprecation warnings from the test suite.

## Warnings

The test suite now produces only **1 warning** (reduced from 51):

- Starlette/httpx test-client deprecation warning (`Using httpx with starlette.testclient is deprecated; install httpx2 instead`)

## What the Tests Do Not Prove Yet

- They do not test a live Ollama or Anthropic request.
- They do not test telephony, STT, TTS, WebSocket, or webhook workflows (Phase 6 & 10).
- They do not test PostgreSQL migrations or concurrent production traffic (Phase 12).
