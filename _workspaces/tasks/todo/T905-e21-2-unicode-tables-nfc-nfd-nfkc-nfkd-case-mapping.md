---
id: T905
title: E21.2 Compact Unicode property tables, NFC/NFD/NFKC/NFKD normalization & full case mapping
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T904]
priority: 215
status: todo
attempts: 0
paths: [std/text/unicode/tables, std/text/unicode/norm, std/text/unicode/case_map, tests/run/std_unicode_norm]
spec: [spec/SPEC-121-text-unicode-complete.md, 0089, tasks/0332]
covers: [REQ-RT-431, REQ-RT-432, REQ-RT-433, REQ-RT-434, REQ-RT-435, REQ-RT-436, REQ-RT-437, REQ-RT-438, REQ-RT-439, REQ-RT-440, REQ-RT-441, REQ-RT-442, REQ-RT-443, REQ-RT-444, REQ-RT-445, REQ-RT-446, REQ-RT-447, REQ-RT-448, REQ-RT-449, REQ-RT-450, REQ-RT-451, REQ-RT-452, REQ-RT-453, REQ-RT-454, REQ-RT-455, REQ-RT-456, REQ-RT-457, REQ-RT-458, REQ-RT-459, REQ-RT-460]
---
# T905 — E21.2 Compact Unicode property tables, NFC/NFD/NFKC/NFKD normalization & full case mapping

## Goal
Implement compact multi-stage Unicode property tables, streaming `NFC`/`NFD`/`NFKC`/`NFKD` normalizers, and locale-independent full Unicode case mapping/folding in `std.text.unicode` per `spec/SPEC-121-text-unicode-complete.md`.

## Scope
- Implement `std/text/unicode/tables` using two-stage trie tables for `General_Category`, `Canonical_Combining_Class` (`CCC`), canonical/compatibility decompositions, canonical composition pairs, and `Quick_Check` flags so unused tables are dead-stripped (`tasks/0332 §19-24`).
- Implement `std/text/unicode/norm` (`nfd`, `nfc`, `nfkd`, `nfkc`, `is_nfc`, `is_nfd`, `is_nfkc`, `is_nfkd`, plus Hangul syllable `SBase`/`LBase`/`VBase`/`TBase` algorithmic composition and decomposition).
- Implement `std/text/unicode/case_map` (`to_uppercase_full`, `to_lowercase_full`, `to_casefold`, `eq_ignore_unicode_case`, handling multi-scalar SpecialCasing expansions and Vietnamese precomposed/decomposed text).
- Add run tests in `tests/run/std_unicode_norm`.

## Acceptance
- [ ] Run tests in `tests/run/std_unicode_norm` verify `NFC`/`NFD`/`NFKC`/`NFKD` equivalence on Vietnamese (`Xin chào thế giới` composed vs decomposed), Hangul syllables, combining-mark canonical ordering, and full case mapping/folding in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T905-report.md` with exact `## Files changed`.

## Out of scope
- UAX #29 grapheme/word/sentence segmentation and `OsStr`/`CStr` (`T906`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T905/build` and `python tools/axtest.py --compiler build-snap-T905/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
