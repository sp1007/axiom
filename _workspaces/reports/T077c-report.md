# T077c Report: Port Diagnostics Emitter to Axiom

## Summary
Implemented the pure-Axiom diagnostics emitter (`compiler/diag/`) and self-host test suite (`tests/selfhost/diag/`):
- `compiler/diag/code.ax` (193 LOC): `DiagCode`, `Severity`, `FixApplicability`, and all 133 `AX_*` diagnostic code constants plus `diag_code_default_severity`, `diag_code_is_valid`, and `diag_code_domain_base` mirroring `bootstrap/axiom0/src/diag/codes.def` and `bootstrap/axiom0/src/diag/diag.c`.
- `compiler/diag/emitter.ax` (402 LOC): `DiagLabel`, `DiagEdit`, `DiagFix`, `DiagDataKind`, `DiagDataValue`, `DiagDataEntry`, `Diagnostic`, `DiagSink`, `diag_emit`, `diag_sort` (deterministic insertion sort by `(file_id, start, end, code)`), and query helpers.
- `compiler/diag/format.ax` (496 LOC): `DiagBuffer`, `CODE_NAMES_DATA` / `CODE_NAMES_OFF` table for all 133 diagnostic codes, UTF-8 / tab-aware human snippet renderer with multi-line carets, secondary labels, notes, helps, and suggested fixes (`diag_format_human`).
- `compiler/diag/json.ax` (346 LOC): JSON v1 (`"schema_version": 1`) renderer (`diag_format_json`) with RFC 8259 string escaping, forward-slash path normalization, and byte-exact structural parity with `axiom0 --error-format=json`.
- `compiler/diag/mod.ax` (45 LOC): Module re-exports for `compiler/diag`.
- `compiler/diag/` total LOC: **1,482 LOC** (strictly within the $\le 1,500$ LOC budget).
- Self-host tests (`tests/selfhost/diag/qa_diag_codes.ax`, `qa_diag_emitter.ax`, `qa_diag_format_json.ax`): 9/9 passing across `[interp]`, `[native]`, and `[native-O1]`, including byte-exact JSON v1 differential verification against `axiom0`.

## Files changed
- compiler/diag/code.ax
- compiler/diag/emitter.ax
- compiler/diag/format.ax
- compiler/diag/json.ax
- compiler/diag/mod.ax
- tests/selfhost/diag/qa_diag_codes.ax
- tests/selfhost/diag/qa_diag_emitter.ax
- tests/selfhost/diag/qa_diag_format_json.ax

STATUS: COMPLETE round=0
