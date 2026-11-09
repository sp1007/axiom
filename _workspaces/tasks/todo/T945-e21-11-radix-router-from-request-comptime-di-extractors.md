---
id: T945
title: E21.11 — Radix tree router, FromRequest typed extractors & comptime DI verification
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T944, T558]
priority: 257
status: todo
attempts: 0
paths: [std/web/router, std/web/extract, tests/run/std_web_routing]
spec: [spec/SPEC-152-web-framework-openapi-extractors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-171, REQ-STD-177]
---
# T945 — E21.11 — Radix tree router, FromRequest typed extractors & comptime DI verification

## Goal
Implement the high-performance radix tree router and compile-time validated dependency-injection handler extractors (`Path<T>`, `Query<T>`, `Json<T>`, `Header<T>`, `State<T>`) without runtime RTTI.

## Scope
- In `std/web/router`, implement zero-allocation radix tree matching:
  * Exact segment matching, wildcard prefix match (`/static/*filepath`), and parameterized segment extraction (`/api/v1/items/{item_id}`).
  * Route registration for standard HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `HEAD`, `OPTIONS`.
- In `std/web/extract`, implement the `FromRequest` trait contract:
  * `Path<T>`: deserialize path parameters into typed structs or scalar values.
  * `Query<T>`: deserialize URL query string key-value parameters.
  * `Json<T>`: deserialize JSON request body via `std.json` with streaming buffer bounds.
  * `Header<T>`: extract typed HTTP headers.
  * `State<T>`: extract application-shared concurrency state (`Arc<AppState>`).
- Enforce compile-time verification of handler signatures:
  * In `compiler/types` or derive expansion, inspect endpoint function parameters using `TypeInfo`.
  * Ensure that all parameter types implement `FromRequest` and that only one body-consuming extractor is registered per handler (`AX_TYPE_DUPLICATE_BODY_EXTRACTOR`).

## Acceptance
- [ ] Run tests in `tests/run/std_web_routing` verify radix router path matching, parameter extraction, and method dispatch across `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Compile-time tests verify that handler functions with invalid parameter types or duplicate body extractors are rejected with descriptive compile errors.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T945-report.md` with exact `## Files changed`.

## Out of scope
- OpenAPI schema generation (handled in `T946`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T945/build` and `python tools/axtest.py --compiler build-snap-T945/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:35:00 created by axiom-architect (ADR-0039 P21 std.web expansion)
