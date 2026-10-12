# ADR-0007: Architecture Layer Order for MIR and Ownership

## Tóm tắt
Quyết định thứ tự các tầng kiến trúc giữa MIR và Ownership. MIR (Mid-level IR) là tầng cơ sở, Ownership checker hoạt động dựa trên MIR, do đó MIR phải nằm dưới Ownership (`mir < own`).

## Context
During the P6 gate checks (T052), it was discovered that `test_archcheck.py` expects the dependency order `own < mir`. However, the actual C source code and `tools/archcheck_rules.txt` correctly use the order `mir < own`. The Ownership subsystem relies on the Mid-level IR (MIR) to perform its analysis.

## Decision
The canonical layer order is `mir < own`. The Mid-level IR (MIR) does not depend on Ownership (own). The Ownership analysis depends on MIR.

## Consequences
- `test_archcheck.py` must be updated to expect `mir < own` to fix the `archcheck_selftest` failure.
- `tools/archcheck_rules.txt` remains correct with `mir < own`.
- Enforces the invariant that AST lowers to MIR, and then Ownership is checked on the MIR.
