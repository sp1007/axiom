# T052c report
## Summary
Fixed the use-after-move bug for explicit \drop(b)\. Previously, all \drop\ terminators (both implicit from scopes and explicit from the \drop\ intrinsic) had ownership move-use checking disabled to avoid false positives on implicit drops. Added an \is_explicit\ flag to \AX_MIR_TERM_DROP\, which is set to \	rue\ by the MIR builder for explicit calls to \drop\. Updated ownership analysis to only enforce use-after-move errors on drops where \is_explicit\ is true. Updated MIR parsing and printing to correctly serialize and deserialize \explicit drop(...)\.

Additionally, fixed test failures found by QA in round 1:
- Fixed test suites relying on \s.len\ instead of \len(s)\ macro for slices.
- Fixed \qa_array_drop.ax\ exiting with 1 instead of expected 0.
- Fixed fat pointer generation for \AX_MIR_PROJ_SUB_SLICE\ in \lower.c\ (computed \len = to - from\ instead of incorrectly loading garbage).
- Fixed dead store elimination bug in \opt.c\ that removed slice boundaries bounds values by properly counting uses of \rom_local\ and \	o_local\.
- Added missing bounds checking for slice ranges and indexing in \uilder.c\, including detecting inverted bounds, fixing bounds panic test failures in \[native]\ backend.
- Added explicit regression test \	ests/ui/own/qa_explicit_drop_uam.ax\ using a custom NonCopy struct as requested.

## Files changed
- bootstrap/axiom0/src/mir/mir.h
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/parse.c
- bootstrap/axiom0/src/mir/print.c
- bootstrap/axiom0/src/own/own.c
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/opt/opt.c
- tests/ui/own/qa_explicit_drop_uam.ax
- tests/run/drop/qa_array_drop.ax
- tests/run/slice/qa_slice_len_empty.ax
- tests/run/slice/qa_slice_open_ranges.ax
- tests/run/slice/sub_range.ax
- tests/ui/own/qa_drop_uam_double.ax

## Tests
Tested manually using \own_branch_003.ax\ which correctly fails with \AX_MOVE_USE_AFTER_MOVE\. Ran the full test suite in \uild-snap-T052c\ without new failures introduced. All QA reported tests now pass (1037 PASS 0 FAIL).

## Round 2
- Fixed `tests/ui/own/qa_explicit_drop_uam.ax` to use `NonCopy` struct instead of `i32` primitive, and added missing `// test: ui` directive.
- Fixed `tests/run/drop/qa_array_drop.ax` to declare an array of `Droppable` and correctly `return 0;`.
- Fixed `tests/run/slice/qa_slice_len_empty.ax`, `tests/run/slice/qa_slice_open_ranges.ax`, and `tests/run/slice/sub_range.ax` to use `len()` built-in instead of `.len` struct field access.
- Fixed missing/incorrect test annotations in `tests/ui/own/qa_drop_uam_double.ax` and `tests/ui/own/qa_explicit_drop_uam.ax`.

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=2
