---
id: T946
title: E21.11 — @derive(Validate) RFC 9457 422 JSON errors, comptime OpenAPI 3.1 & air-gapped /docs
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T945, T573, T936]
priority: 258
status: todo
attempts: 0
paths: [std/web/validate, std/web/openapi, tests/run/std_web_openapi]
spec: [spec/SPEC-152-web-framework-openapi-extractors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-171, REQ-STD-177]
---
# T946 — E21.11 — @derive(Validate) RFC 9457 422 JSON errors, comptime OpenAPI 3.1 & air-gapped /docs

## Goal
Implement the declarative `@derive(Validate)` validation system with RFC 9457 HTTP 422 JSON problem details, compile-time OpenAPI 3.1 schema generation, and air-gapped offline Swagger UI interactive documentation at `/docs`.

## Scope
- In `std/web/validate`, implement validation attributes and trait:
  * Support field attributes: `@range(min = 1, max = 100)`, `@length(min = 3, max = 50)`, `@email`, `@regex(pattern = "^[a-z]+$")`.
  * When input validation fails during extractor execution, automatically abort handler invocation and return an RFC 9457 compliant `application/problem+json` response with status code 422, detailing invalid fields and error codes.
- In `std/web/openapi`, generate OpenAPI 3.1 metadata:
  * Extract paths, HTTP methods, operation IDs, parameter schemas, request bodies, and response types at compile-time using `TypeInfo` and `@derive(Serialize)` schemas.
  * Serve generated JSON schema at `/openapi.json`.
- In `std/web/docs`, embed offline Swagger UI distribution assets (HTML, JS, CSS) into the binary using `@embed_str` (`T573`):
  * Serve the interactive explorer at `/docs` with zero external network access or CDN dependencies, ensuring functional documentation inside air-gapped enterprise environments.

## Acceptance
- [ ] Run tests in `tests/run/std_web_openapi` verify that invalid input payloads receive HTTP 422 responses formatted as RFC 9457 JSON with exact field error locations.
- [ ] Schema test verifies that `/openapi.json` matches the OpenAPI 3.1 JSON Schema specification.
- [ ] Offline doc test verifies `/docs` serves complete self-contained HTML/JS/CSS without external URL requests.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T946-report.md` with exact `## Files changed`.

## Out of scope
- Third-party API client generation from OpenAPI (client export is in `E20.8`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T946/build` and `python tools/axtest.py --compiler build-snap-T946/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:35:00 created by axiom-architect (ADR-0039 P21 std.web expansion)
