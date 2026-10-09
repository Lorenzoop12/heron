# ADR 0001: Expose triage as an HTTP service with FastAPI

- Status: accepted
- Date: Module 6

## Context

Triage is consumed by other systems (the mail gateway wants a verdict at
delivery time; the SOC dashboard shows flagged messages) that should not
depend on our Python internals or shell out to a CLI. We need a stable,
documented, language-agnostic interface.

## Decision

Expose a small REST API built with FastAPI:

- `POST /triage` — synchronous triage of one raw RFC 5322 message
- pydantic models define the wire format, decoupled from the internal
  dataclasses in `models.py` (hexagonal boundary: domain vs adapter)
- storage is a port: endpoints depend on the `VerdictRepository` Protocol and
  receive an implementation through FastAPI `Depends`; the SQLite
  `VerdictStore` is the only adapter today (tests inject an in-memory fake)
- errors use RFC 9457 problem details (`application/problem+json`)
- OpenAPI schema and interactive docs are generated automatically

## Alternatives considered

- **Flask**: mature, but no built-in validation/OpenAPI; we would rebuild
  what pydantic already gives us.
- **Milter / SMTP hook**: the "real" integration point for a mail
  gateway, but couples us to one MTA and complicates local development;
  a gateway-side adapter can call this API instead.
- **Message queue worker**: right choice if volume grows (a busy gateway
  triages thousands of messages a minute); deferred (see Consequences).

## Consequences

- The API is synchronous; a slow LLM-backed check (Module 8) would block
  a gateway. If that lands on the hot path, introduce an async queue and
  verdict callbacks (new ADR).
- The service is stateless except for the optional verdict store,
  configured via `HERON_DB` (12-factor).
