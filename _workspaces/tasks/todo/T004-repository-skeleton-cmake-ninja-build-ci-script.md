---
id: T004
title: Repository skeleton, CMake/Ninja build, CI script
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 10
status: todo
attempts: 0
paths: [bootstrap/axiom0, tests/unit/unit.h, .gitignore, README.md, tools/ci.sh, tools/ci.ps1]
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
- **Driver as registries (ADR-0005 §2):** one file per command `src/driver/cmd_<name>.c` and per inspect emitter `src/driver/emit_<name>.c`; CMake globs them and generates the registration table at configure time (plain C11, no constructor attributes), so a later task adds a file and never edits `main.c` or CMakeLists.txt. This task ships `cmd_version.c`, `cmd_inspect.c` (dispatches `--emit=<name>` through the emitter table; unknown name → usage error, exit 2) and `--features` (prints the empty capability list).
- CMake also globs `tests/unit/**/*.c` into the `axiom0-unit` executable (tiny assertion header `tests/unit/unit.h` in this task) and builds every `tests/**/cdriver_*.c` into its own test executable linked against the compiler sources; with no such files the build still succeeds. After this task nobody edits CMakeLists.txt.
- tools/ci.sh and tools/ci.ps1 are pre-wired: run `tools/axtest.py`, `tools/archcheck.py`, `tools/gatecheck.py` and `tools/fuzz.py --smoke` each only if the file exists, so later tasks do not edit the CI scripts (gate tasks may).
- Binary fixtures are allowed only under `tests/**/fixtures/` (the .gitignore exemption); documented in the top-level README.

## Acceptance
- [ ] `cmake -S bootstrap/axiom0 -B build -G Ninja && cmake --build build` succeeds with gcc and with clang, zero warnings.
- [ ] `build/axiom0.exe version` prints a version line and exits 0; its stdout contains `\n` and no `\r` (checked by piping to `od -c`).
- [ ] Toolchain recorded in the report (gcc/clang/cmake/ninja versions from MSYS2 ucrt64).
- [ ] tools/ci.sh runs end-to-end on this machine.
- [ ] Demonstrated in the report (scratch files, not committed): adding `emit_dummy.c`, `cmd_dummy.c`, `tests/unit/dummy/t.c` and `tests/x/cdriver_y.c` builds and registers them without touching CMakeLists.txt or `main.c`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T004-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Not a "critical" task any more (ADR-0005 §11): runs in parallel with T001. It needs only the axiom-c-stage0 conventions, not SPEC-00/SPEC-04.
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
