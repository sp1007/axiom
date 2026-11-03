---
id: T907
title: E21.2 Unicode normalization, UAX #29 segmentation & case mapping conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T906]
priority: 217
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_2_text_unicode]
spec: [spec/SPEC-121-text-unicode-complete.md, 0089, tasks/0332, tasks/0608]
covers: [REQ-RT-496, REQ-RT-497, REQ-RT-498, REQ-RT-499, REQ-RT-500, REQ-RT-501, REQ-RT-502, REQ-RT-503, REQ-RT-504, REQ-RT-505, REQ-RT-506, REQ-RT-507, REQ-RT-508, REQ-RT-509, REQ-RT-510, REQ-RT-511, REQ-RT-512, REQ-RT-513, REQ-RT-514, REQ-RT-515, REQ-RT-516, REQ-RT-517, REQ-RT-518, REQ-RT-519, REQ-RT-520, REQ-RT-521, REQ-RT-522]
---
# T907 — E21.2 Unicode normalization, UAX #29 segmentation & case mapping conformance suite

## Goal
Certify E21.2 exit criteria with an end-to-end Unicode conformance suite validating normalization idempotence (`NFC`/`NFD`/`NFKC`/`NFKD`), UAX #29 grapheme/word/sentence test vectors, full case mapping/folding, and `OsStr`/`CStr` safety.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_2_text_unicode` checking official Unicode Normalization and UAX #29 GraphemeBreak/WordBreak/SentenceBreak test vectors (`0089 §9-14`, `tasks/0332 §19-25`).
- Verify normalization idempotence and canonical equivalence across Vietnamese precomposed and decomposed strings (`Xin chào thế giới`), Hangul jamo/syllables, and multi-mark sequences.
- Verify full case folding (`ß` ↔ `SS`, Greek sigma, Turkish/Lithuanian-independent default rules) and malformed UTF-8 rejection / `U+FFFD` lossy recovery.
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_2_text_unicode` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T907-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T907/build` and `python tools/axtest.py --compiler build-snap-T907/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
