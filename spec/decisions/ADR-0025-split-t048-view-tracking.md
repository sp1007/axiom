# ADR-0025: Split T048 for View Tracking Implementation

## Context
Task T048 ("Views & capabilities: view/mut_view, regions, conflicts, escapes") is blocked because the fundamental capability tracking structures in `ax_mir_cap_tracker` and their integration into `ax_own_check` and `syntax/typeck` do not exist yet. Implementing all of this along with region tracking, conflict detection, and view escapes in one task is too large and complex.

## Options Considered
1. **Unblock and proceed**: Do all the work in T048. Too large.
2. **Split the task**: Create a prerequisite task for basic capability tracking and syntax integration, and then do the region/conflict logic in a subsequent task. 

## Decision
We choose option 2. We will split T048 into two smaller tasks:
- **T124**: Basic capability tracking & syntax for views (implementing `ax_mir_cap_tracker`, `own.c`, `syntax/typeck`).
- **T125**: Views & capabilities: view/mut_view, regions, conflicts, escapes (the remainder of the original T048).

## Consequences
- T048 will be superseded by T124.
- Better isolation of fundamental ownership infrastructure changes from complex capability conflict rules.
