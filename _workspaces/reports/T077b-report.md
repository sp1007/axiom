# T077b Report: Port source DB to Axiom

## Task Summary
Ported the source database and span tracking module from C to pure Axiom under `compiler/source/`, covering `Span`, `LineCol`, UTF-8 scalar counting and validation, line map construction, binary-search line/column locator, span text slicing, and `SourceDatabase` management with deduplication. Fully validated across interpreter, native, and native-O1 modes.

## Files changed
- compiler/source/manager.ax
- compiler/source/mod.ax
- compiler/source/span.ax
- tests/selfhost/source/qa_source_manager.ax
- tests/selfhost/source/qa_source_span.ax

## Key Deliverables & Validation
1. **Span & LineCol Representation (`compiler/source/span.ax`)**:
   - `Span` (FileId, u32 start, u32 end) and `LineCol` (u32 line, u32 col_bytes, u32 col_chars).
   - `span_new`, `span_none`, `span_is_none`, `span_len`, `span_contains`, `span_contains_offset`, `span_merge`.
   - Verified in `tests/selfhost/source/qa_source_span.ax`.

2. **Source Database (`compiler/source/manager.ax`)**:
   - `SourceFile` and `SourceDatabase` with arena allocation for string/path storage.
   - Dynamic line-map builder indexing start offsets of every line (`\n`, `\r\n`).
   - UTF-8 scalar validation and scalar counting for multi-byte Unicode characters (accents, emojis).
   - Binary search line locator (`source_db_line_col`) computing 1-based line, 1-based byte column, and 1-based char column.
   - Text slicing (`source_db_span_text`), path lookup, and content hashing.
   - Verified in `tests/selfhost/source/qa_source_manager.ax`.

3. **Acceptance Criteria & Metrics**:
   - Total source module line count: 434 lines (budget ≤ 1,500 lines).
   - Test suite: 6/6 passing across `[interp]`, `[native]`, and `[native-O1]`.
   - Archcheck: 0 violations across 188 files.
   - Requirements coverage: REQ-DRV-021 covered.

STATUS: COMPLETE round=0
