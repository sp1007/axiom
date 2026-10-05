# T112 report
## Summary
Added `archcheck:allow(INV-LAYER-006)` pragmas to `ax_ice_failv` in `bootstrap/axiom0/src/kernel/base.c` where `fputs`, `vfprintf`, `fprintf`, `fflush`, and `abort` are called. This resolves the architecture violations caused by the ICE reporter terminating the process.
## Files changed
- bootstrap/axiom0/src/kernel/base.c
## Tests
Tests were run via `ctest --output-on-failure` in `build-snap-T112/bootstrap/axiom0/build`.
- `axiom0-unit`: Passed
- `ct_unit_kernel_cdriver_ice`: Passed
`archcheck.py` was run and reports 0 violations.
## Spec deviations
none
## Follow-ups
none

STATUS: COMPLETE round=0
