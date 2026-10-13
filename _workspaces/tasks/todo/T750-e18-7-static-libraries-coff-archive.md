---
id: T750
title: E18.7 Static libraries: COFF archive (.lib) writer and reader, --kind
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T218]
priority: 700
status: todo
attempts: 0
paths: [compiler/obj, compiler/link, compiler/driver, tests/link/lib]
spec: [0164, 0217, 0099, tasks/0369, 0185]
covers: [REQ-OWNER-006]
---
# T750 — E18.7 Static libraries: COFF archive (.lib) writer and reader, --kind

## Goal
`axiomc build --kind lib` produces a standard COFF archive (.lib) from Axiom modules, and executables can link against .lib archives (ours and standard third-party/C ones).

## Scope
- Driver: unified `--kind exe|obj|lib|dll` (default exe); `--emit=obj` kept as alias of `--kind obj`.
- COFF archive writer: `!<arch>` signature, first/second linker members (symbol index), long-name member, deterministic member order and zero timestamps.
- Archive reader in the PE linker: symbol-index lookup, pull only members that resolve undefined symbols, iterate to a fixed point; COFF short import objects recognised.
- `-l<name>` / `-L<dir>` and `@link("name")` resolution order documented.

## Acceptance
- [ ] An Axiom library built as .lib is linked into an Axiom exe; unused members are not pulled in.
- [ ] A .lib/.a produced by the system toolchain (gcc + ar on a C object in test fixtures) is consumed and called via FFI.
- [ ] objdump / ar list our archive correctly.
- [ ] Full test suite passes; outputs byte-identical across two runs.
- [ ] Report `_workspaces/reports/T750-report.md` with exact `## Files changed`.

## Out of scope
- Other targets/formats (ELF/Mach-O libraries are E16.10); Axiom-ABI dynamic components (E20.7).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Owner requirement REQ-OWNER-006, roadmap epic E18.7: implemented in axiomc (Axiom, `compiler/`) right after self-hosting (P18 opens after P10). The C core emits only .obj/.exe but its data models reserve these artifact kinds (SPEC-04, T003a).
- The P18 planning task T218 may split this task; keep this id for the first slice.
- All Axiom code uses canonical syntax (axiom-syntax).

## Log
- 2026-10-06 02:24:25 covers += REQ-OWNER-006 (metadata only)
