---
id: T731
title: E17.9 — Canonical specification for static C++ zero-day vulnerability scanning (SPEC-151)
phase: P17-debugging-runtime-introspectio
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T217, T316]
priority: 202
status: todo
attempts: 0
paths: [spec/SPEC-151-zero-day-static-analysis.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-151-zero-day-static-analysis.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-CORE-034, REQ-DBG-116]
---
# T731 — E17.9 — Canonical specification for static C++ zero-day vulnerability scanning (SPEC-151)

## Goal
Consolidate the canonical specification for the fast $O(\text{CFG})$ MIR abstract interpretation zero-day vulnerability scanner and SARIF 2.1 emitter into `spec/SPEC-151-zero-day-static-analysis.md` (`AXS-ZDAY-*` rule IDs).

## Scope
- Write `spec/SPEC-151-zero-day-static-analysis.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ZDAY-NNN` rules.
- Specify the abstract interpretation lattice and forward dataflow framework analyzing MIR functions in bounded linear time $O(\text{CFG})$, avoiding heavyweight SMT solver overhead to maintain compilation speed.
- Specify the 10 canonical vulnerability classes modeled after high-severity CVEs (Google Project Zero, Microsoft MSRC):
  1. `AX_VERIFY_UNCHECKED_ALLOC_OVERFLOW`: multiplication/addition overflowing before allocation size parameters.
  2. `AX_VERIFY_TRUNCATING_LEN_CAST`: truncating 64-bit integer lengths to 32-bit before bounds checks.
  3. `AX_UNSAFE_STATIC_USE_AFTER_FREE`: accessing raw pointer places after free or lifetime invalidation.
  4. `AX_UNSAFE_STATIC_DOUBLE_FREE`: releasing raw allocation pointers multiple times on any path.
  5. `AX_UNSAFE_STACK_PTR_ESCAPE`: returning or storing pointers to stack-allocated local variables.
  6. `AX_UNSAFE_UNION_TYPE_CONFUSION`: reading active union variants without type checking or safety guard.
  7. `AX_FFI_UNINIT_PADDING_LEAK`: passing structs with uninitialized alignment padding across FFI boundaries.
  8. `AX_IO_TOCTOU_RACE`: time-of-check to time-of-use filesystem race conditions (`stat` followed by `open`).
  9. `AX_IO_TAINTED_PATH_TRAVERSAL`: passing unvalidated external strings to filesystem operations.
  10. `AX_IO_TAINTED_COMMAND_SINK`: executing process command shells with tainted user arguments.
  11. `AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`: using quarantined `std.crypto.legacy` algorithms in modern cryptographic sinks.
- Specify SARIF 2.1 output format, `axiom audit --zero-day` CLI driver, and `@suppress("rule")` scoped annotations.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-151-zero-day-static-analysis.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-ZDAY-NNN` rules, positive/negative examples, and SARIF 2.1 schema mapping.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T731-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the MIR analysis passes (`T732`–`T734`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T731/build` and `python tools/axtest.py --compiler build-snap-T731/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 static zero-day analysis expansion)
