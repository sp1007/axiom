# T008 report
## Summary
Implemented `SourceDatabase` handling physical/virtual files, byte spans, and line maps according to specs 0153, 0171, and 0172. Handled BOM by stepping over it in `text` view but keeping the original allocation pointer for freeing. Implemented `LineMap` that treats `\n` and `\r\n` as breaks and maintains accurate 1-based indexing for line, byte columns, and character/Unicode scalar columns. Unit tests added for edge cases like CRLF, BOM, empty files, and multi-byte offset logic.

## Files changed
- bootstrap/axiom0/src/source/source.h
- bootstrap/axiom0/src/source/source.c
- tests/unit/source/test_source.c

## Tests
`python tools/axtest.py --compiler build-snap-T008/build/axiom0.exe`
TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0

## Spec deviations
None

## Follow-ups
None

STATUS: COMPLETE round=0
