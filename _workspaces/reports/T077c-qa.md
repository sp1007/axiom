# T077c QA Report

## Round 0
- `taskctl.py changes T077c`: 8 files under `compiler/diag/` and `tests/selfhost/diag/`, 0 `REFUSED` lines.
- `tools/archcheck.py`: 0 violations.
- Line count budget: `compiler/diag/*.ax` is 1,482 LOC ($\le 1,500$ LOC budget).
- Self-host test suite (`tests/selfhost/diag/`): `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0` across `[interp]`, `[native]`, and `[native-O1]`, including byte-exact JSON v1 differential verification against `axiom0 --error-format=json`.

VERDICT: PASS round=0
