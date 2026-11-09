---
id: T733
title: E17.9 — MIR abstract interpretation for TOCTOU, path traversal, command sinks & SARIF emitter
phase: P17-debugging-runtime-introspectio
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T732]
priority: 204
status: todo
attempts: 0
paths: [compiler/analysis/zeroday, compiler/driver/sarif, tests/ui/zeroday_io, tests/sarif]
spec: [spec/SPEC-151-zero-day-static-analysis.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-CORE-034, REQ-DBG-116]
---
# T733 — E17.9 — MIR abstract interpretation for TOCTOU, path traversal, command sinks & SARIF emitter

## Goal
Implement taint analysis and control-flow pattern detection for TOCTOU file races, path traversal, shell injection, and weak legacy crypto misuse, plus the standard SARIF 2.1 report emitter.

## Scope
- In `compiler/analysis/zeroday`, implement path-sensitive taint tracking and operation sequencing:
  * Detect Time-of-Check to Time-of-Use file races (`stat`/`exists` followed by `open`/`write` instead of atomic flags `O_CREAT | O_EXCL`), reporting `AX_IO_TOCTOU_RACE`.
  * Track untrusted string inputs (HTTP queries, command-line arguments, environment variables) flowing into filesystem paths without sanitization, reporting `AX_IO_TAINTED_PATH_TRAVERSAL`.
  * Track untrusted inputs flowing into subprocess execution or shell sinks without argument escaping, reporting `AX_IO_TAINTED_COMMAND_SINK`.
  * Detect usage of algorithms from `std.crypto.legacy` (`Sha1`, `Md5`, `Des`) flowing into modern password hashing, signature, or TLS transport sinks without explicit suppression, reporting `AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`.
- Implement `compiler/driver/sarif`:
  * Format static analysis findings into OASIS SARIF 2.1 schema compliant JSON (`--emit=sarif`).
  * Include exact source code locations, rule metadata, CWE mappings (e.g. CWE-190, CWE-416, CWE-367, CWE-22, CWE-78, CWE-327), and code snippet contexts.

## Acceptance
- [ ] Negative UI tests in `tests/ui/zeroday_io` verify static detection of TOCTOU races, path traversal, command sinks, and legacy crypto misuse.
- [ ] Golden tests in `tests/sarif` verify that emitted SARIF 2.1 JSON validates cleanly against the official SARIF schema validator.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T733-report.md` with exact `## Files changed`.

## Out of scope
- Dynamic fuzzing verification (handled in `E17.8`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T733/build` and `python tools/axtest.py --compiler build-snap-T733/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:15:00 created by axiom-architect (ADR-0039 P17 static zero-day analysis expansion)
