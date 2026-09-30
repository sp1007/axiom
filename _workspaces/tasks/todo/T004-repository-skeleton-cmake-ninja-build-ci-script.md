---
id: T004
title: Repository skeleton, CMake/Ninja build, CI script
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 5
status: todo
attempts: 0
paths: [bootstrap/axiom0/CMakeLists.txt, bootstrap/axiom0/src/driver, .gitignore, README.md, tools/ci.sh, tools/ci.ps1]
spec: [0152, 0263, 0172]
---
# T004 — Repository skeleton, CMake/Ninja build, CI script

## Goal
Create the repository layout from axiom-c-stage0 and a build that produces `axiom0.exe` with gcc and clang.

## Scope
- Directory skeleton with a README per module dir (one line: purpose + layer).
- CMakeLists.txt globbing src/**/*.c (CONFIGURE_DEPENDS), C11, warnings-as-errors flags for gcc/clang, Debug/Release, optional sanitizers option.
- src/driver/main.c: `axiom0 version` and usage text; exit codes documented; stdout/stderr switched to binary mode on Windows at startup (axiom-c-stage0 "Byte-exact I/O").
- .gitignore: build*/, *.exe/*.obj outside tests fixtures, _workspaces/artifacts/.
- tools/ci.sh (bash) and tools/ci.ps1: configure+build gcc and clang, run tests (if runner exists) and archcheck (if exists).

## Acceptance
- [ ] `cmake -S bootstrap/axiom0 -B build -G Ninja && cmake --build build` succeeds with gcc and with clang, zero warnings.
- [ ] `build/axiom0.exe version` prints a version line and exits 0; its stdout contains `\n` and no `\r` (checked by piping to `od -c`).
- [ ] Toolchain recorded in the report (gcc/clang/cmake/ninja versions from MSYS2 ucrt64).
- [ ] tools/ci.sh runs end-to-end on this machine.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T004-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
