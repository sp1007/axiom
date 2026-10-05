---
id: T112
title: Fix archcheck violations in kernel base.c
phase: P1-kernel
owner: axiom-architect
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T008]
priority: 14
status: done
attempts: 1
paths: [bootstrap/axiom0/src/kernel/base.c]
spec: []
started: 2026-10-05 15:52:18
finished: 2026-10-05 15:56:40
---
# T112 — Fix archcheck violations in kernel base.c

## Goal
Add `archcheck:allow` pragmas to `kernel/base.c` to fix architecture violations caused by `ax_ice_failv` and `ax_ice_fail` calling IO and abort functions.

## Scope
- Add `/* archcheck:allow(INV-LAYER-006): ICE reporter terminates process */` to `bootstrap/axiom0/src/kernel/base.c` where `fputs`, `vfprintf`, `fprintf`, and `abort` are called.

## Acceptance
- [ ] `archcheck.py` is clean for `bootstrap/axiom0/src/kernel/base.c`.
- [ ] Build warning-free.

## Out of scope
- Any changes to `archcheck_rules.txt`.

## Notes
- `base.c` is the foundational file and contains the ICE fail implementation which must print to stderr and abort. It legitimately violates INV-LAYER-006.

## Log
- 2026-10-05 15:52:18 started (attempt 1) T112-impl
- 2026-10-05 15:56:40 accepted by QA -> done
