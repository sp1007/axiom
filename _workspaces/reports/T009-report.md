# T009 Report

## Task: Diagnostics engine (model, code registry, human + JSON renderers)

## Summary of Work
Implemented the diagnostics data model and rendering pipelines exactly to specification. 

1. **Code Registry**: Created `bootstrap/axiom0/src/diag/codes.def` and the 18 area seed files (e.g., `codes/LEX.def`, `codes/TYPE.def`, etc.) using a Python script to populate all initial X-macro error definitions from the specification. Implemented string lookup mapping functions in `registry.c`.
2. **DiagSink and Sort**: Implemented `AxDiagSink` in `sink.c` to deeply copy diagnostic values (messages, labels, notes, fixes) using an `AxArena`. Enforced the canonical stable sorting logic according to emission order, area, and start position.
3. **Renderers**:
   - Implemented `ax_diag_render_json` in `render_json.c` outputting the required v1 JSON schema. 
   - Implemented `ax_diag_render_human` in `render_human.c` outputting the visual layout with carets, multi-line spans, severity prefixes, and source gutter logic.
4. **Unit Tests**: Created `tests/unit/diag/test_diag.c` and `diag_unit.test` covering basic lookups, rendering for both formats, and sorting logic. The tests pass. Code is C11 compliant, warning-free, and adheres to the architecture check.

## Round 1

- Removed `gen.py` as it was outside task paths.
- Added assertions to the `diag_qa_edge_cases` test in `test_diag.c` to properly assert the multi-line CRLF unicode output of both human and JSON renderers.
- Blocked on fixing the archcheck failure in `bootstrap/axiom0/src/kernel/base.c` because it is outside the allowed `paths:` for this task (`paths: [bootstrap/axiom0/src/diag, tests/unit/diag]`).

## Files changed
- bootstrap/axiom0/src/diag/codes.def
- bootstrap/axiom0/src/diag/codes/CAP.def
- bootstrap/axiom0/src/diag/codes/CONST.def
- bootstrap/axiom0/src/diag/codes/DRIVER.def
- bootstrap/axiom0/src/diag/codes/DROP.def
- bootstrap/axiom0/src/diag/codes/FFI.def
- bootstrap/axiom0/src/diag/codes/ICE.def
- bootstrap/axiom0/src/diag/codes/INIT.def
- bootstrap/axiom0/src/diag/codes/IO.def
- bootstrap/axiom0/src/diag/codes/LEX.def
- bootstrap/axiom0/src/diag/codes/LINK.def
- bootstrap/axiom0/src/diag/codes/MOVE.def
- bootstrap/axiom0/src/diag/codes/NAME.def
- bootstrap/axiom0/src/diag/codes/PARSE.def
- bootstrap/axiom0/src/diag/codes/PAT.def
- bootstrap/axiom0/src/diag/codes/TRAIT.def
- bootstrap/axiom0/src/diag/codes/TYPE.def
- bootstrap/axiom0/src/diag/codes/UNSAFE.def
- bootstrap/axiom0/src/diag/codes/VERIFY.def
- bootstrap/axiom0/src/diag/diag.h
- bootstrap/axiom0/src/diag/registry.c
- bootstrap/axiom0/src/diag/sink.c
- bootstrap/axiom0/src/diag/render_json.c
- bootstrap/axiom0/src/diag/render_human.c
- tests/unit/diag/test_diag.c
- tests/unit/diag/diag_unit.test

## Round 2

- Verified that `gen.py` has been removed.
- Verified that the `diag_qa_edge_cases` test successfully passes, proving the implementation handles multi-line spans, CRLF, and unicode characters correctly.
- Base archcheck failure was extracted and fixed in T112 by the architect.
- Re-ran the test suite in the snapshot and verified all tests pass (0 failures).

STATUS: COMPLETE round=2
