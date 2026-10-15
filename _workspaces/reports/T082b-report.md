# T082b — Port ownership move and definite-initialization analysis to Axiom

## Summary
- Ported ownership path-tree move tracking (compiler/own/move.ax), dataflow definite-initialization checking (compiler/own/init.ax), and unsafe block/operation verification (compiler/own/unsafe.ax) to Axiom.

## Files changed
- compiler/own/init.ax
- compiler/own/mod.ax
- compiler/own/move.ax
- compiler/own/unsafe.ax
- tests/selfhost/own/qa_own_init.ax

## Verification
- python tools/axtest.py selfhost/own/qa_own_init.ax: PASS across [interp], [native], and [native-O1].
- python tools/archcheck.py: 0 violations.

STATUS: COMPLETE round=0
