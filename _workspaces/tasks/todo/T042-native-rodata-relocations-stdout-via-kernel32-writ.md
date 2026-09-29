---
id: T042
title: Native: rodata, relocations, stdout via kernel32 WriteFile
phase: P5-language
owner: axiom-backend
reviewer: axiom-qa
depends: [T041, T040]
priority: 62
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, bootstrap/axiom0/src/target/x64, bootstrap/axiom0/src/link, bootstrap/axiom0/src/obj, tests/run/native_str]
spec: [0186, 0187, 0185]
---
# T042 — Native: rodata, relocations, stdout via kernel32 WriteFile

## Goal
hello.exe: string output natively.

## Scope
- .rdata section, RIP-relative addressing, import GetStdHandle/WriteFile, runtime print helpers generated as machine code or Axiom-level intrinsic stubs.

## Acceptance
- [ ] All stdout run tests pass natively; hello world exe.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T042-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
