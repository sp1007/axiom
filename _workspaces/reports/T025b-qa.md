# QA Report T025b

## Round 1

### Checks performed
- `taskctl changes`: Verified no `REFUSED` lines.
- `cmake --build`: Verified build completes without warnings.
- `axtest.py`: Full suite passes (392 tests, 312 pass, 80 skip, 0 fail).
- `archcheck.py`: Passed (108 files scanned, 0 violations).
- Acceptance criteria: 
  - `main_42.mc`: Encoded bytes manually verified for correct prologue and epilogue layout.
  - Stack probe checks: Executed `ct_mc_frame_cdriver_probe.exe` and `ct_mc_frame_cdriver_probe_edge.exe`. Probe loop generated successfully for large frames and correctly omitted for frames <= 4096 bytes.
  - Verifier unit tests: All negative tests correctly trigger ICEs and match expected regexes.
- Scope checks: Verified only x64 frame lowering, verify, and `emit_mc` paths were changed. No invalid layer bounds breached.
- Boundary cross-check: Found that `frame size consistency violated` rule was not tested. Added a C driver branch and `.test` manifest to exercise it.

### Findings
- No failing issues.

## Files changed
- tests/mc/frame/cdriver_verify.c
- tests/mc/frame/cdriver_verify_framesize.test

VERDICT: PASS round=1
