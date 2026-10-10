# ADR-0019: Split T046 into place model and move dataflow

## Context
Task T046 handles "Place model + move/copy analysis (use-after-move, partial moves)". The basic ownership pipeline, `MOVE.def`, and basic structures (`own.c`, `own.h`) have been partially implemented, but the data flow logic and tests were blocked because they represent a significant complexity boundary and the task scope became too large.

## Decision
Split T046 into two tasks:
1. **T120**: Place model + basic pipeline registration + copy classification. This will capture the progress made so far in establishing the initial structures in `own.c`, `own.h`, and `pipeline.c`.
2. **T121**: Move dataflow analysis (use-after-move, partial moves) and testing. This focuses specifically on the data flow algorithm over MIR places and emission of `AX_MOVE_USE_AFTER_MOVE`.

## Consequences
- Allows landing the groundwork and place model definition in isolation.
- Focuses the dataflow algorithm and diagnostics into a distinct task.
- Unblocks the pipeline.
