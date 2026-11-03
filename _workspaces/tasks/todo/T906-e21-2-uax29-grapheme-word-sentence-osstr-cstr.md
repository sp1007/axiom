---
id: T906
title: E21.2 UAX #29 grapheme/word/sentence segmentation, OsStr/CStr & zero-copy text cursors
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T904, T905]
priority: 216
status: todo
attempts: 0
paths: [std/text/unicode/segment, std/text/os_str, std/text/cursor, tests/run/std_unicode_segment]
spec: [spec/SPEC-121-text-unicode-complete.md, 0089, tasks/0332, tasks/0608]
covers: [REQ-RT-461, REQ-RT-462, REQ-RT-463, REQ-RT-464, REQ-RT-465, REQ-RT-466, REQ-RT-467, REQ-RT-468, REQ-RT-469, REQ-RT-470, REQ-RT-471, REQ-RT-472, REQ-RT-473, REQ-RT-474, REQ-RT-475, REQ-RT-476, REQ-RT-477, REQ-RT-478, REQ-RT-479, REQ-RT-480, REQ-RT-481, REQ-RT-482, REQ-RT-483, REQ-RT-484, REQ-RT-485, REQ-RT-486, REQ-RT-487, REQ-RT-488, REQ-RT-489, REQ-RT-490, REQ-RT-491, REQ-RT-492, REQ-RT-493, REQ-RT-494, REQ-RT-495]
---
# T906 — E21.2 UAX #29 grapheme/word/sentence segmentation, OsStr/CStr & zero-copy text cursors

## Goal
Implement UAX #29 extended grapheme cluster, word, and sentence segmentation iterators, `OsStr`/`OsString` and `CStr`/`CString` boundary types, and zero-copy text scanners in `std.text` per `spec/SPEC-121-text-unicode-complete.md`.

## Scope
- Implement `std/text/unicode/segment` (`GraphemeIter`, `WordIter`, `SentenceIter` implementing UAX #29 state machines including CRLF, Regional_Indicator flag pairs, Extended_Pictographic ZWJ emoji sequences, and Hangul/Indic conjunct clusters; `0089 §9-14`, `tasks/0332 §22-25`).
- Implement `std/text/os_str` (`OsStr`, `OsString`, `CStr`, `CString` with explicit interior-NUL error checking, lossless UTF-16/WTF-8 Windows wide-string round-tripping, and fallible `to_str()` validation; `tasks/0332 §26-34`).
- Implement `std/text/cursor` (`TextCursor`, `LineIter`, UTF-8 lossy decoding `String.from_utf8_lossy` with `U+FFFD` replacement, and zero-copy delimiter splitting; `tasks/0608 §17-22`).
- Add run tests in `tests/run/std_unicode_segment`.

## Acceptance
- [ ] Run tests in `tests/run/std_unicode_segment` verify UAX #29 grapheme/word/sentence boundaries (ZWJ sequences, combining diacritics in `Xin chào thế giới`, regional indicators), `CStr`/`CString` interior-NUL rejection, and `OsString` UTF-16 round-tripping in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T906-report.md` with exact `## Files changed`.

## Out of scope
- Font shaping and GUI text rendering (`P24 E24.2`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T906/build` and `python tools/axtest.py --compiler build-snap-T906/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
