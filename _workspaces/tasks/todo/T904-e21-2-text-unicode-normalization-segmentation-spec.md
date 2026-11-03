---
id: T904
title: E21.2 Canonical Unicode normalization, UAX #29 segmentation & case mapping specification (SPEC-121)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 214
status: todo
attempts: 0
paths: [spec/SPEC-121-text-unicode-complete.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0089, tasks/0332, tasks/0608]
covers: [REQ-RT-395, REQ-RT-396, REQ-RT-397, REQ-RT-398, REQ-RT-399, REQ-RT-400, REQ-RT-401, REQ-RT-402, REQ-RT-403, REQ-RT-404, REQ-RT-405, REQ-RT-406, REQ-RT-407, REQ-RT-408, REQ-RT-409, REQ-RT-410, REQ-RT-411, REQ-RT-412, REQ-RT-413, REQ-RT-414, REQ-RT-415, REQ-RT-416, REQ-RT-417, REQ-RT-418, REQ-RT-419, REQ-RT-420, REQ-RT-421, REQ-RT-422, REQ-RT-423, REQ-RT-424, REQ-RT-425, REQ-RT-426, REQ-RT-427, REQ-RT-428, REQ-RT-429, REQ-RT-430]
---
# T904 — E21.2 Canonical Unicode normalization, UAX #29 segmentation & case mapping specification (SPEC-121)

## Goal
Consolidate the canonical specification for Axiom's complete Unicode text model—NFC/NFD/NFKC/NFKD normalization, UAX #29 grapheme/word/sentence segmentation, full case mapping/folding, and `OsStr`/`CStr` encoding bridges—into `spec/SPEC-121-text-unicode-complete.md` (`AXS-TXT-*` rule IDs).

## Scope
- Write `spec/SPEC-121-text-unicode-complete.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-TXT-NNN` rules.
- Specify the 4-level text hierarchy (`0089 §2-14`, `tasks/0332 §3-18`): raw `Bytes` (`view<u8>`), validated UTF-8 `Str`/`String` (O(1) byte slicing on valid UTF-8 code-point boundaries, never O(n) character indexing), Unicode scalar `char` (`u21`), and extended grapheme clusters.
- Specify canonical and compatibility normalization (`NFC`, `NFD`, `NFKC`, `NFKD`, Hangul algorithmic composition/decomposition, Canonical_Combining_Class ordering, Quick_Check fast paths; `tasks/0332 §19-25`), locale-independent full Unicode case mapping (`to_lowercase`, `to_uppercase`, `to_casefold` including 1-to-many expansions like `ß` → `SS` and Vietnamese precomposed/combining diacritics), and UAX #29 segmentation (`graphemes`, `words`, `sentences`).
- Specify tree-shakeable Unicode data tables (`REQ-RT-169`: unreferenced Unicode tables are never linked into binaries that do not call normalization/segmentation APIs) and `OsStr`/`OsString`/`CStr`/`CString` WTF-8/UTF-16/NUL-terminated FFI boundaries (`tasks/0332 §26-34`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-121-text-unicode-complete.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-TXT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T904-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of Unicode normalization, case mapping, and segmentation (`T905`–`T906`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T904/build` and `python tools/axtest.py --compiler build-snap-T904/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
