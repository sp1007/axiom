---
id: T052d
title: Fix missing tests/run/native_abi for gatecheck
phase: P6-ownership
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
depends: []
priority: 71
status: todo
paths: [tests/run/native_abi, tools/gatecheck.py]
---
# T052d — Fix missing tests/run/native_abi for gatecheck

## Goal
Fix MS-P5 check in `gatecheck.py` failing due to missing `tests/run/native_abi`.

## Scope
- Either create a dummy test in `tests/run/native_abi` or fix `gatecheck.py` to handle the missing directory gracefully if it's intentionally empty.
