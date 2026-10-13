---
id: T061d
title: Native catch-up: constant tables in .rdata
phase: P7-abstraction
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T061, T061b]
priority: 83
status: done
attempts: 1
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/obj, tests/run/comptime, tests/run/native_const]
locks: [bootstrap/axiom0/src/driver/build_native/build.c, bootstrap/axiom0/src/driver/emit_obj.c, bootstrap/axiom0/src/driver/emit_mc.c]
spec: [0162, 0185, 0186, spec/decisions/ADR-0004-self-host-subset-additions.md]
covers: []
started: 2026-10-13 17:37:40
finished: 2026-10-13 18:21:40
---
# T061d — Native catch-up: constant tables in .rdata

## Goal
Constant aggregate tables (opcode tables, keyword tables, diagnostic metadata) are emitted once as read-only data and indexed in place — what the compiler written in Axiom needs instead of `static` items (ADR-0004 §2).

## Scope
- Emit each `const` aggregate that is used as a place once into `.rdata`, with ADDR64 relocations for `Str` pointers; uses are RIP-relative addresses, never per-use stack copies.
- Identical tables are emitted once per program; output is deterministic (ordered by symbol name).
- Remove every `// native-after: T061d` directive from tests/run/comptime.

## Acceptance
- [ ] Differential green for the table tests of T061; `grep -rn "native-after: T061d" tests` prints nothing.
- [ ] `--emit=mc` / objdump check: a function indexing a 4 KB table has a frame smaller than 256 bytes (no copy of the table on the stack).
- [ ] Byte-identical rebuild; cross-link oracle (gcc) accepts the object.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T061d-report.md` with exact `## Files changed`.

## Out of scope
- `static` / `static mut` items (E13.3, E13.6).
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-13 17:37:40 started (attempt 1) 
- 2026-10-13 18:21:40 accepted by QA -> done
