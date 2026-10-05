# T105 report

## Summary
Fixed requirement extraction for C14 in Round 3. Wrote an improved block parser (`extract_c14_v8.py`) to correctly identify paragraphs containing normative keywords (phải, không được, must, shall, invariant) and dynamically expand the context window backwards to include the introductory paragraphs when the keyword appears in a list item, a code block, or a short sentence fragment.
This addresses all QA findings:
- Replaced naive sentence fragment extraction with context-aware inclusion (e.g. "phải khác nhau" now correctly includes its preceding list of states).
- Context properly crosses code blocks boundaries (e.g. "phải được policy xử lý" correctly merges with the prior list).
- Maintained section citations per QA requirements (e.g. `tasks/0906 §92`).
- Removed hallucinated `[quy định chi tiết]` placeholders.
- Deduplication is run explicitly.

## Files changed
- spec/requirements/raw/C14.md

STATUS: COMPLETE round=3
