---
id: T944
title: E21.11 — Canonical specification for FastAPI-grade std.web framework (SPEC-152)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T914, T573, T936]
priority: 256
status: todo
attempts: 0
paths: [spec/SPEC-152-web-framework-openapi-extractors.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-152-web-framework-openapi-extractors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-171, REQ-STD-177]
---
# T944 — E21.11 — Canonical specification for FastAPI-grade std.web framework (SPEC-152)

## Goal
Consolidate the canonical specification for the modern, type-safe, dependency-injected web application server `std.web` into `spec/SPEC-152-web-framework-openapi-extractors.md` (`AXS-WEB-*` rule IDs).

## Scope
- Write `spec/SPEC-152-web-framework-openapi-extractors.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-WEB-NNN` rules.
- Specify zero-allocation radix tree routing with parameterized URL segments (`/users/{id:[0-9]+}`).
- Specify compile-time dependency injection and typed parameter extractors (`Path<T>`, `Query<T>`, `Json<T>`, `Header<T>`, `State<T>`, `Extension<T>`) validating extractor contracts via Comptime 2.0 reflection (`TypeInfo`) with zero runtime dynamic type reflection (no RTTI).
- Specify declarative validation via `@derive(Validate)` with constraint attributes (`@range(min, max)`, `@length(min, max)`, `@email`, `@regex`), emitting RFC 9457 compliant HTTP 422 Unprocessable Content JSON error responses.
- Specify compile-time OpenAPI 3.1 schema extraction emitting `/openapi.json` without runtime reflection, and embedding offline Swagger UI HTML/JS/CSS assets via `@embed_str` at `/docs` with zero external CDN dependencies.
- Specify production application server hardening: HTTP/1.1 and HTTP/2 transport, Slowloris read timeouts, strictly enforced `max_body_bytes`, path-traversal resistant static file hosting (`StaticDir` rejecting null bytes, 8.3 short names, and `..`), streaming multipart file uploads, and Server-Sent Events (`SseStream`) / WebSocket upgrade.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-152-web-framework-openapi-extractors.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-WEB-NNN` rules, positive/negative examples, and security architecture diagrams.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T944-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the web server modules (`T945`–`T947`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T944/build` and `python tools/axtest.py --compiler build-snap-T944/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:35:00 created by axiom-architect (ADR-0039 P21 std.web expansion)
