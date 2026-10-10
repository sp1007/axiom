# ADR-0020 — rescope-t121-paths

## Tóm tắt
Thêm `bootstrap/axiom0/src/driver/pipeline.c` vào phạm vi (paths) của task T121.

## Context
Task T121 is blocked because the implementer needs to modify `bootstrap/axiom0/src/driver/pipeline.c` to integrate the dataflow analysis into the compiler pipeline, but this file is missing from the task's `paths`.

## Options
1. **Split the task:** Create a new task solely for pipeline integration, making T121 depend on it or vice versa.
2. **Rescope T121 (Chosen):** Add `bootstrap/axiom0/src/driver/pipeline.c` to the `paths` of T121.

## Decision
We choose Option 2. Adding the pipeline file to `paths` is the simplest and most direct way to unblock the task. A split is unnecessary as pipeline registration is a minor wiring step integral to making the dataflow analysis run.

## Consequences
- T121 can now modify `pipeline.c` to register the pass.
- No new tasks are created.
