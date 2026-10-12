---
id: T052b
title: Fix test_archcheck.py layer order
phase: P6-ownership
owner: axiom-backend
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: []
priority: 70
status: doing
paths: [tools/tests/archcheck/test_archcheck.py, tools/archcheck_rules.txt]
spec: []
attempts: 1
started: 2026-10-12 09:45:12
---
# T052b — Fix test_archcheck.py layer order

## Goal
Fix `archcheck_selftest` failing due to layer order mismatch.

## Scope
- Update `tools/tests/archcheck/test_archcheck.py` which hardcodes `own < mir` to match the actual C source code and `tools/archcheck_rules.txt` which use `mir < own`.

## Acceptance
- `archcheck_selftest` passes successfully.

## Log
- 2026-10-12 09:45:12 started (attempt 1) 
