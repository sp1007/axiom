# Task T043 Report

## Round 0
- Implemented const folding, dead code elimination, and CFG simplification.
- Added tests for const folding.

## Round 1
- Fixed missing opt feature advertisement in --features output by adding it to ax_pipeline_stages in pipeline.c. This unblocked the -O1 variant execution for all tests in the suite.
- QA-provided differential tests for DCE pass successfully with no regressions.

## Files changed
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/opt/opt.c
- bootstrap/axiom0/src/opt/opt.h
- tests/diff/opt/const_fold.ax
- tests/diff/opt/qa_dce.ax
- tests/opt/const_fold_run.ax
- tests/opt/qa_dce_run.ax
STATUS: COMPLETE round=1
