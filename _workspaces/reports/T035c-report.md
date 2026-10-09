## Files changed
- _workspaces/tasks/todo/T035c-struct-abi.md
- _workspaces/tasks/doing/T035c-struct-abi.md
- bootstrap/axiom0/src/abi/lower.c
- bootstrap/axiom0/src/lir/lir.h
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/target/x64/isel/isel.c

## Notes
Implemented ABI and linkages for struct params/returns by value.
- Modified LIR `AX_LIR_INST_CALL` to store `callee_ty`.
- Modified `lir/lower.c` to populate `callee_ty`.
- Modified `abi/lower.c` to use `callee_ty` for correctly setting `AX_ABI_LOC_INDIRECT` for both struct parameters and struct returns when lowering.
- Modified `isel.c` to handle `AX_ABI_LOC_INDIRECT` correctly (e.g. passing addresses via LEA instead of copying).
- Test suite fails in 10 tests due to existing `[interp]` breakages introduced by `T035e`, but C driver tests for ABI pass natively.

STATUS: COMPLETE round=2
