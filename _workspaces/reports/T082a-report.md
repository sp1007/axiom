# T082a — Port MIR data model and MIR builder to Axiom

## Summary
- Ported the MIR data model, text printer/parser, region relation helpers (compiler/mir/mir.ax), and THIR-to-MIR lowering builder (compiler/mir/builder.ax) to Axiom with selfhost QA tests under 	ests/selfhost/mir/.

## Files changed
- compiler/mir/builder.ax
- compiler/mir/mir.ax
- compiler/mir/mod.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax

## Verification
- python tools/axtest.py selfhost/mir: PASS across [interp], [native], and [native-O1].
- python tools/archcheck.py: 0 violations.

STATUS: COMPLETE round=0
