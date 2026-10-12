---
gate_model: none
id: T052d
title: Fix missing tests/run/native_abi for gatecheck
phase: P6-ownership
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
depends: []
priority: 71
status: doing
paths: [tests/run/native_abi, tools/gatecheck.py]
attempts: 1
started: 2026-10-12 11:37:28
---
gate_model: none
# T052d — Fix missing tests/run/native_abi for gatecheck

## Goal
Fix MS-P5 check in `gatecheck.py` failing due to missing `tests/run/native_abi`.

## Scope
- Either create a dummy test in `tests/run/native_abi` or fix `gatecheck.py` to handle the missing directory gracefully if it's intentionally empty.

## Log
- 2026-10-12 11:37:28 started (attempt 1) 

## Acceptance
All tests pass.
