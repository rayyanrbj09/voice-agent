# Test Results

**Latest run:** 2026-09-14
**Command:** `.venv\Scripts\python.exe -m pytest tests/ -q`
**Result:** **43 passed, 0 failed**
**Duration:** 10.09 seconds

## Coverage by Area

| Area | Status | Evidence |
| --- | --- | --- |
| Authentication | Passing | registration, login, JWT, invalid-token, and account checks |
| Customer API | Passing | CRUD, validation, authentication, and ownership isolation |
| Tool registry | Passing | registration, lookup, listing, duplicate and unknown-tool handling |
| Tool executor | Passing | user-context injection, required arguments, customer-first errors |
| Business tools | Passing | appointments, orders, support tickets, validation, and ownership |
| Agent orchestration | Passing | provider adapters, tool loop, memory, guardrails, serialization |
| False-success regression | Passing | no success claim after missing action tool or failed tool result |

## Important Regression Covered

The agent previously produced successful-looking messages such as "I booked the appointment" even when an internal tool had failed. The regression test now verifies that a failed action produces a failure/request-for-details response instead.

The test also covers the related case where only `search_customer` ran but the LLM claimed that an appointment, order, or ticket had been created.

## Warnings

The latest run produced 51 warnings:

- Starlette/httpx test-client deprecation warning
- SQLAlchemy warning that `datetime.utcnow()` is deprecated

These warnings do not currently cause test failures. They should be addressed before a production release.

## What the Tests Do Not Prove Yet

- They do not test a live Ollama or Anthropic request.
- They do not test telephony, STT, TTS, WebSocket, or webhook workflows.
- They do not provide end-to-end HTTP routes for appointments, orders, or support tickets because those routes do not yet exist.
- They do not test PostgreSQL migrations or concurrent production traffic.
- They do not prove that every possible LLM wording is caught by the current text guard.

## Recommended Next Tests

1. Add integration tests that call the real registered tools and assert rows in `appointments`, `orders`, and `support_tickets`.
2. Add tests for action-tool failure followed by multiple model response rounds.
3. Add provider contract tests for Ollama and Anthropic normalized tool calls.
4. Add transaction rollback tests for database failures.
5. Add API tests after dedicated business-resource routes are introduced.
