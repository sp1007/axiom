---
id: T026
title: COFF object writer
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T024, T003a]
priority: 43
status: done
attempts: 1
paths: [bootstrap/axiom0/src/obj/coff, tests/obj]
spec: [0185, .claude/skills/axiom-x64-backend/references/pe-coff.md, spec/SPEC-04-core-extensibility.md]
started: 2026-10-05 20:19:37
finished: 2026-10-05 20:38:42
covers: [REQ-OWNER-006, REQ-TOOL-001]
---
# T026 — COFF object writer

## Goal
Write deterministic COFF (.obj) files from the object model.

## Scope
- Headers, sections, symbols (long names via string table), relocations REL32/ADDR64/ADDR32NB, TimeDateStamp 0.
- `--emit=obj` is wired into `axiom0 build` by T028; this task is exercised through the C test driver `tests/obj/cdriver_coff.c` (T004 glob) and `exec` manifests.
- Fixture inputs (`.c`, hand-made `.obj`) live under `tests/obj/fixtures/` — the only place where binaries are not git-ignored; generated outputs are never committed.
- **Cross-link oracle (test only, never the production path):** the system toolchain (`gcc`/`ld` from
  MSYS2 ucrt64) links our objects, so the COFF writer is validated independently of our own PE
  linker (T027) — a later failure is then clearly in the linker, not the object file. Codegen does
  not exist yet, so the fixture objects are built by a C test driver in `tests/obj` through
  objmodel + encoder (T024) and written by this writer.

## Acceptance
- [ ] objdump -x/-d accepts outputs and shows expected symbols/relocations; byte-identical across two runs.
- [ ] Cross-link: fixture object defining `main` (`mov eax, 42; ret`) → `gcc fixture.obj -o t.exe` → exit code 42.
- [ ] Cross-link with relocations: fixture `main` calls an external C function from a fixture `.c` (REL32) and reads a data word through an ADDR64 relocation in `.data`; linked by gcc it returns the checksum the test expects; a `.rdata` string `Xin chào thế giới` is passed to the C helper, which writes it and the test compares the 22 bytes.
- [ ] Cross-link tests report SKIP (not FAIL) when `gcc` is not on PATH, so the suite still runs on a machine without MSYS2.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T026-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-05 20:19:37 started (attempt 1) T026-impl
- 2026-10-05 20:38:42 accepted by QA -> done
- 2026-10-06 02:24:25 covers += REQ-OWNER-006 (metadata only)
- 2026-10-06 02:31:22 covers += REQ-TOOL-001 (metadata only)
