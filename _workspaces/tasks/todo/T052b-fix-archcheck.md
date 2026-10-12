---
id: T052b
title: Fix test_archcheck.py layer order
phase: P6-ownership
owner: axiom-backend
reviewer: axiom-architect
model: sonnet
depends: []
priority: 70
status: todo
paths: [tools/test_archcheck.py, tools/archcheck_rules.txt]
spec: []
---
# T052b — Fix test_archcheck.py layer order

## Goal
Fix `archcheck_selftest` failing due to layer order mismatch.

## Scope
- Update `tools/test_archcheck.py` which hardcodes `own < mir` to match the actual C source code and `tools/archcheck_rules.txt` which use `mir < own`.

## Acceptance
- `archcheck_selftest` passes successfully.
