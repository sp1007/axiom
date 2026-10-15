# T082c — Port capability and region checking to Axiom

## Summary
- Ported iew/mut_view capability conflict tracking, region containment analysis, and borrow lifetime checking (compiler/own/cap.ax) to Axiom.

## Files changed
- compiler/own/cap.ax
- compiler/own/mod.ax
- tests/selfhost/cap/qa_own_cap.ax

## Verification
- python tools/axtest.py selfhost/cap/qa_own_cap.ax: PASS across [interp], [native], and [native-O1].
- python tools/archcheck.py: 0 violations.

STATUS: COMPLETE round=0
