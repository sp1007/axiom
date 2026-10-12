# T052b Report

## Summary
Fixed `test_archcheck.py` to match the actual C source code and `tools/archcheck_rules.txt` by correcting the hardcoded layer order from `own < mir` to `mir < own`.

## Files changed
- tools/tests/archcheck/test_archcheck.py

STATUS: COMPLETE round=0
