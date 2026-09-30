---
id: T024
title: Object model + x86-64 encoder core (validated vs GNU as)
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T007, T005, T003a]
priority: 41
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/objmodel, bootstrap/axiom0/src/target/x64/encode, tests/encode, tools/gen_encode_tests.py]
spec: [0184, 0180, 0233, 0254, .claude/skills/axiom-x64-backend, spec/SPEC-04-core-extensibility.md]
---
# T024 — Object model + x86-64 encoder core (validated vs GNU as)

## Goal
Encode x86-64 instructions directly to bytes with target-neutral relocations.

## Scope
- objmodel: Section{name,kind,flags,align,bytes,relocs}, Symbol, Relocation{offset,kind,symbol,addend}.
- Encoder for: mov (r/r, r/imm, r/m, m/r, imm64), movzx/movsx, lea, add/sub/and/or/xor/cmp/test, imul, cqo/cdq, idiv/div, neg/not, shl/shr/sar (cl & imm), setcc, jcc/jmp rel8/rel32, call rel32, call [rip+disp32], ret, push/pop, int3; all GPRs incl. r8–r15 and byte regs; ModRM/SIB/disp8/disp32/RIP-relative edge cases.
- tools/gen_encode_tests.py generates expectation tables using GNU as + objdump (checked into tests/encode).

## Acceptance
- [ ] Encoding tables pass for every form × register class × addressing edge case (RSP/R12 SIB, RBP/R13 disp).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T024-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
