---
id: T042
title: Native: rodata, relocations, stdout via kernel32 (UTF-8 greeting)
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T041, T040]
priority: 62
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/link, bootstrap/axiom0/src/obj, tests/run/native_str, tests/run/str, tools/tests/console_check.py]
spec: [0186, 0187, 0185]
covers: [REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006]
---
# T042 — Native: rodata, relocations, stdout via kernel32 WriteFile

## Goal
hello.exe prints `Xin chào thế giới` natively (UTF-8 end to end).

## Scope
- .rdata section, RIP-relative addressing, import GetStdHandle/WriteFile, runtime print helpers generated as machine code or Axiom-level intrinsic stubs.
- Remove every `// native-after: T042` directive from tests/run/str (ADR-0005 §1).
- Console output (ADR-0006 §9): the startup stub calls `SetConsoleOutputCP(65001)` when stdout is a console (`GetConsoleMode` succeeds) and restores the previous code page before `ExitProcess`; output always goes through `WriteFile` with the raw UTF-8 bytes. No UTF-16 conversion in machine code (std.io does that in Axiom, T074).
- `tools/tests/console_check.py` (Python `ctypes`, standard library): allocates a console, runs an executable attached to it and reads the screen buffer with `ReadConsoleOutputCharacterW`.

## Acceptance
- [ ] hello.exe prints `Xin chào thế giới\n`: exact UTF-8 bytes when stdout is a pipe or a file (runner) — this is the gate.
- [ ] Console glyphs, machine-checked (ADR-0005 §16): `python tools/tests/console_check.py hello.exe "Xin chào thế giới"` reads the greeting back from the console screen buffer; it may report SKIP only when no console can be allocated in the session (the reason is printed). The code page is restored after exit (checked by the helper).
- [ ] All stdout run tests pass natively.
- [ ] `grep -rn "native-after: T042" tests` prints nothing.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T042-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 02:31:23 covers += REQ-TYP-001, REQ-TYP-002, REQ-TYP-003, REQ-TYP-004, REQ-TYP-005, REQ-TYP-006 (metadata only)
