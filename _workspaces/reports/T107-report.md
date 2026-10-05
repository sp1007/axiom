# T107: Requirement extraction C16 (core)

## Summary of Work
1. Addressed all Round 8 QA findings by writing a robust Python extraction script (`extract_c16.py`).
2. Deduplication fixed: The script now normalizes statements (ignoring HTML tags like `<br>` and standardizing whitespace) and groups identical requirements using a hash map. Multiple sources are aggregated into the single output row.
3. Missing lists fixed: The script detects when a normative paragraph ends with a colon and groups it with the immediately following Markdown list. The 24-item list in `1015 AXSTREAM` is successfully captured.
4. Missing diagrams fixed: The script recognizes diagrams (fenced code blocks) in normative sections (like "Mục tiêu" in `1040 AXBINARY`) and successfully extracts them, properly formatted with `<br>`.
5. Grouped invariants fixed: The script safely splits code blocks or lists containing `INV-` or rule IDs line-by-line to prevent lumping multiple distinct invariants into a single row.

## Files changed
- spec/requirements/raw/C16.md

STATUS: COMPLETE round=9
