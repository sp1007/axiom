# ADR-0026 — Rescope T048b to extract sub-ranges and disjoint split into T126

## Tóm tắt
Tách tính năng sub-range và disjoint split từ T048b sang task mới (T126) do cần suy luận logic (symbolic reasoning) phức tạp trong phân tích vùng (region analysis).

## Context
Task T048b originally included sub-range views (`s[a..b]`) and disjoint splits of a `mut_view`. However, implementing sub-ranges requires introducing a new MIR projection kind (`AX_MIR_PROJ_SUB_SLICE`) and necessitates symbolic reasoning in `ax_mir_region_relate` to prove that adjacent or non-overlapping ranges (e.g. `a..b` and `b..c`) are truly disjoint. This is too extensive for a single step.

## Decision
Rescope T048b to only cover basic dynamic-length views (array-to-slice coercion, `len`, bounded indexing, and `Str`). Create a new task T126 to handle sub-range views and disjoint splitting, which will follow T048b.

## Consequences
- Unblocks T048b so it can be completed more predictably.
- A dedicated task T126 is created to properly model and implement the disjointness logic of range bounds in the region analyzer.
