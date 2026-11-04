---
id: T750
title: E18.7 — Static libraries: COFF archive (.lib) writer and reader, --kind
phase: P18-compiler-architecture-2-0
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T772]
priority: 700
status: done
attempts: 1
paths: [compiler/obj, compiler/link, compiler/driver, tests/link/lib]
locks: [tests/selfhost/obj, tests/selfhost/link, tests/selfhost/driver, tests/selfhost/obj_link_driver]
spec: [spec/SPEC-26-windows-artifact-kinds.md, 0164, 0217, 0099, tasks/0369, 0185]
covers: [REQ-OWNER-006, REQ-LNK-057, REQ-LNK-058, REQ-LNK-059, REQ-LNK-060, REQ-LNK-061, REQ-LNK-062, REQ-LNK-063, REQ-LNK-064, REQ-LNK-065, REQ-LNK-066, REQ-LNK-067, REQ-LNK-068, REQ-LNK-069, REQ-LNK-070, REQ-LNK-071, REQ-LNK-072, REQ-LNK-211, REQ-LNK-212, REQ-LNK-213, REQ-LNK-214, REQ-LNK-215, REQ-LNK-216, REQ-LNK-217, REQ-LNK-218, REQ-LNK-219, REQ-LNK-220, REQ-LNK-221, REQ-LNK-222, REQ-LNK-223, REQ-LNK-224, REQ-LNK-225, REQ-LNK-226]
started: 2026-11-03 22:52:05
finished: 2026-11-04 15:12:11
---
# T750 — E18.7 — Static libraries: COFF archive (.lib) writer and reader, --kind

## Goal
`axiomc build --kind lib` produces a standard COFF archive (`.lib`) from Axiom modules, and executables can link against `.lib` archives (ours and standard third-party/C ones) per `spec/SPEC-26-windows-artifact-kinds.md`.

## Scope
- Driver: unified `--kind exe|obj|lib|dll` (default `exe`); `--emit=obj` kept as alias of `--kind obj`.
- COFF archive writer: `!<arch>` signature, first/second linker members (symbol index), long-name member, deterministic member order and zero timestamps (`0185`).
- Archive reader in the PE linker: symbol-index lookup, pull only members that resolve undefined symbols, iterate to a fixed point; COFF short import objects recognised.
- `-l<name>` / `-L<dir>` and `@link("name")` resolution order implemented per `spec/SPEC-26-windows-artifact-kinds.md`.

## Acceptance
- [ ] An Axiom library built as `.lib` is linked into an Axiom exe; unused members are not pulled in.
- [ ] A `.lib`/`.a` produced by the system toolchain (`gcc` + `ar` on a C object in test fixtures) is consumed and called via FFI.
- [ ] `objdump` / `ar` list our archive correctly.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); outputs byte-identical across two runs.
- [ ] Report `_workspaces/reports/T750-report.md` with exact `## Files changed`.

## Out of scope
- Other targets/formats (ELF/Mach-O libraries are E16.10); Axiom-ABI dynamic components (E20.7).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Paths re-pathed to canonical `compiler/<module>` layout by T076 (ADR-0005 §8, SPEC-20 §8).
- Owner requirement `REQ-OWNER-006`, roadmap epic E18.7: implemented in `axiomc` (Axiom, `compiler/`) right after self-hosting (P18 opens after P10). The C core emits only `.obj`/`.exe` but its data models reserve these artifact kinds (SPEC-04, T003a).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T750/build` and `python tools/axtest.py --compiler build-snap-T750/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom code uses canonical syntax (`axiom-syntax`).

## Log
- 2026-10-06 02:24:25 covers += REQ-OWNER-006 (metadata only)
- 2026-11-03 03:00:20 refined by T218 (depends on T772 SPEC-26)
- 2026-11-03 12:20:45 started (attempt 1) 
- 2026-11-03 22:51:48 requeue: restart (not charged: attempt refunded)
- 2026-11-03 22:52:05 started (attempt 1) T750-impl
- 2026-11-04 15:12:11 accepted by QA -> done
