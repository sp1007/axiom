# T082c QA Report — Port capability and region checking to Axiom

- **Verdict**: PASS

## Files changed
- compiler/own/cap.ax
- compiler/own/mod.ax
- tests/selfhost/cap/qa_own_cap.ax

## Checks Performed
1. **Architecture & Boundary Check**:
   - python tools/archcheck.py: 0 violations.
2. **Selfhost Verification**:
   - python tools/axtest.py selfhost/cap/qa_own_cap.ax: PASS across [interp], [native], and [native-O1].

VERDICT: PASS round=0
