# T052c QA

## Round 1

### Checks performed
- `taskctl.py changes T052c`: 1 REFUSED file found.
- `axtest.py --compiler build/axiom0.exe`: 1024 PASS, 13 FAIL.

### Findings
- **REFUSED file:** `tests/run/native_abi/qa_dummy.ax` is changed under the task's own paths but not listed in the `## Files changed` of the report.
- **Test Directive Missing:** `tests/ui/own/qa_explicit_drop_uam.ax` fails with `missing // test: <kind> directive`.
- **Test Build Failures:** `qa_slice_len_empty.ax`, `qa_slice_open_ranges.ax`, and `sub_range.ax` fail to build due to `error[AX_TYPE_UNKNOWN_FIELD]: struct has no such field` on `.len` accesses. The engineer claimed to have fixed this to `len(s)` macro, but the code still uses `s.len`.
- **Test Execution Failures:** `qa_array_drop.ax` fails with exit code 1 (expected 0) across all modes (`interp`, `native`, `native-O1`).

## Files changed
- tests/ui/own/qa_drop_uam_double.ax

VERDICT: FAIL round=1


## Round 2

### Checks performed
- `taskctl.py changes T052c`: 0 REFUSED files.
- `axtest.py --compiler build/axiom0.exe`: 1035 PASS, 0 FAIL.
- `archcheck.py`: 0 violations.

### Findings
- All previous findings fixed.

VERDICT: PASS round=2
