---
id: T936
title: E21.2 — Linear-time, bounded-memory Thompson PikeVM / Lazy DFA std.regex & ReDoS immunity
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T905]
priority: 246
status: todo
attempts: 0
paths: [std/regex, tests/run/std_regex]
spec: [spec/SPEC-121-text-unicode-complete.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-395]
---
# T936 — E21.2 — Linear-time, bounded-memory Thompson PikeVM / Lazy DFA std.regex & ReDoS immunity

## Goal
Implement `std.regex` featuring linear-time execution, bounded memory consumption, Thompson NFA PikeVM / on-the-fly Lazy DFA simulation, Unicode property classes, and guaranteed immunity to ReDoS (zero catastrophic backtracking).

## Scope
- Implement regular expression compiler in `std/regex`:
  * Parse standard regex syntax: literals, character classes (`[a-z]`, `\d`, `\w`, `\s`), Unicode property classes (`\p{L}`, `\p{N}`), repetition (`*`, `+`, `?`, `{m,n}`), alternation (`|`), submatch capture groups `(...)`, non-capturing groups `(?:...)`.
  * Compile AST to linear Thompson bytecode instructions (`Match`, `Char`, `Class`, `Split`, `Jump`, `Save`).
- Implement dual execution engines:
  * **Lazy DFA**: Cache dynamically constructed DFA states up to a bounded memory limit (e.g. 2 MiB); transitions execute in $O(1)$ time per input byte.
  * **PikeVM**: Fallback engine tracking thread states for full capture-group extraction without unbounded recursion.
- Enforce strict linear-time $O(M \cdot N)$ execution and ReDoS immunity: no exponential backtracking paths can ever exist.
- Support cooperative cancellation via periodic token checks.

## Acceptance
- [ ] Run tests in `tests/run/std_regex` verify standard matching, capture group extraction, and replacement over UTF-8 input strings in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] ReDoS stress tests verify that known catastrophic backtracking patterns (e.g. `(a+)+$`) complete in linear time ($< 5\text{ ms}$) on 10,000-character inputs.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T936-report.md` with exact `## Files changed`.

## Out of scope
- Backreferences (`\1`) or lookaround assertions requiring non-regular backtracking search.
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T936/build` and `python tools/axtest.py --compiler build-snap-T936/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:25:00 created by axiom-architect (ADR-0039 P21 std.regex expansion)
