# T003 report
## Summary
Spec-only task. Produced the two canonical specs and one ADR.

- `spec/SPEC-03-core-semantics.md` (rules AXS-SEM-001..092): principles (one semantics for interp
  and native, no UB in safe code, observable behaviour); scalar types and representation (`bool`,
  `char`, unit, `never`, 64-bit `isize`/`usize`); integer literal typing (integer type variable,
  default `i32`, range check with negated-literal folding); checked `+ - *` and unary `-` in every
  build; wrapping/bit intrinsics table (ADR-0004 §1); division/remainder (truncation, zero and
  `MIN / -1` panics); bitwise ops; shifts (amount any integer type, range-checked, arithmetic vs
  logical); comparisons; short-circuit; constant-expression failures (`AX_CONST_*`); evaluation order
  (left to right, calls, places, assignment and compound assignment RHS-first, `let`, `if`/`match`);
  complete `as` table (int↔int modular, `bool`→int, `u8 as char`, checked `u32 as char`, `char`→wide
  ints, `enum as` int, pointer rows for T061a, floats rejected); panic kinds and messages; panic =
  abort, stderr `panic: <msg>`, exit 101; `assert`/`unreachable`/`panic(msg)`; `main` forms and exit
  code mapping; exit codes in tests; oracle step limit (50 000 000, exit 124), call-depth limit, UB
  detection (exit 125); 19 normative test cases SEM-T01..T19.
- `spec/SPEC-00-bootstrap.md` (rules AXS-BOOT-001..070): ladder rules (one milestone at a time,
  out-of-subset diagnostics, interp-first, always-forbidden shortcuts X-*, PASS/BLOCKED); the ladder
  name map (V0..V4, VS#1/VS#2, BOOT-nn → T011/T013, T022, T029, T044, T086, T087); milestones
  MS-P1..MS-P10b with gates; feature table F-* (47 ids, oracle task, native task, milestone);
  first programs FP-01..FP-10 in canonical syntax (0263 §32-39, tasks/0494 §41 greeting, first panic
  test); the machine-readable manifest format (fenced ```` ```milestone ```` JSON blocks, field
  table) and the exact `tools/gatecheck.py` algorithm for T022; 11 manifest blocks; the full
  BOOT-00..38 table with deferrals (BOOT-26 → E14.1, BOOT-27 ladder 2 → E15.4, BOOT-28 → E15.8 with
  the ADR-0005 §7 contingency, BOOT-29 → E18.6/E16.9, BOOT-30 → P16) and the Linux-first inversion
  (0181, R6); which SPEC-03 rules each milestone owns; §9 reserved for T003a's exact self-host subset.
- `spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md` (number reserved with
  `taskctl.py adr-next`): the contested decisions with options and rationale — checked overflow in
  every build (later tasks/0334 + 0032 win over tasks/0327 §4), arithmetic failures are panics not
  traps, panic = abort exit 101, RHS-first assignment, truncating integer `as`, `main` forms, oracle
  limits, manifest format. Revisit: yes (overflow-check cost before P15; unwinding E13.5).

Diagnostic codes were agreed with T002 (registry areas of ADR-0011): there is no INTERP area, so
the oracle limits use `AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT` and
`AX_UNSAFE_INTERP_UB`; out-of-subset constructs use `*_UNSUPPORTED_IN_BOOTSTRAP` codes.

## Files changed
- spec/SPEC-00-bootstrap.md
- spec/SPEC-03-core-semantics.md
- spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md
- _workspaces/reports/T003-report.md

## Tests
Nothing to build (spec-only task).
- A Python check parsed all 11 ```` ```milestone ```` blocks with `json.loads`. It confirmed that the
  fields are exact, the `previous` chain is linear, every gate is a board task, every feature or
  shortcut id is defined in §4 / AXS-BOOT-004, and every F-* id is introduced exactly once
  (47 of 47).
- I checked the SEM-T test values by hand: T13 = 4 + 31 = 35, T18 = rotl(0x81, 9 mod 8) = 3, and
  SEM-T19 gives 1234 - 1200 = 34.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: HARNESS OK.
  `taskctl.py validate`: OK (155 tasks).
- None of the three files contains a CR byte.

## Spec deviations
None. Each corpus conflict that was resolved is recorded in ADR-0012.

## Follow-ups
The architect should file these scope or acceptance notes, because the edits fall outside this
task's paths:
1. T005: inside `axiom0 run --interp`, report exit code 124 together with an `AX_DRIVER_INTERP_*`
   diagnostic as TIMEOUT. Detect an ICE by its banner, not by exit code 3, because the program's
   exit code may be 3 (SPEC-03 AXS-SEM-082).
2. T009/T016: print the ICE banner on stderr in a fixed, documented form.
3. T034: also covers the `assert(c)` and `unreachable()` built-ins (AXS-SEM-072). T041: also covers
   the `panic(msg: Str) -> never` built-in. T042: the native panic path writes the
   `panic: <msg>` line.
4. T021: the `--max-call-depth` option (default 100 000) next to `--step-limit` (AXS-SEM-091).
5. T076: add `spec/SPEC-00-bootstrap.md` to its `paths` (or `locks`) so it can update the MS-P10a
   `must_pass` list after it re-splits the port tasks (AXS-BOOT-052).
6. T003a: reuse the F-* ids of SPEC-00 §4 in `spec/selfhost-subset.tsv` and fill §9.

Round 0 status: COMPLETE round=0 (superseded by round 1 below).

## Round 1
Fixes for QA round 0 (`_workspaces/reports/T003-qa.md`).

### F1: MS-P1 paths
- The MS-P1 `must_pass` list is now `tests/unit/driver`, `tests/unit/kernel`, `tests/unit/source` and
  `tests/unit/diag`. N6 is included: `tests/unit/driver` already exists.
- AXS-BOOT-050 now has a check table. It gives the exact command for each check:
  - `axtest_selftest` runs `python tools/tests/axtest/run_selftests.py` (T005);
  - `archcheck_selftest` runs `python tools/tests/archcheck/run_selftests.py` (T006);
  - `archcheck`, `reqcov`, `harness_check`, `gatecheck`, `differential` and `determinism` are also
    listed.
- `must_pass` holds only tests that `tools/axtest.py` discovers. Self-test scripts appear only as
  checks.
- MS-P1 runs the two self-test checks. AXS-BOOT-051 step 5 now refers to the table.

### F2: native contract between T028 and T037
Decided in ADR-0012 §9, with the options and rationale recorded there. New rules are SPEC-00
AXS-BOOT-006 and AXS-BOOT-007, plus one sentence in SPEC-03 AXS-SEM-001.
- **AXS-BOOT-006:** native code never silently diverges from the oracle. A MIR construct that the
  backend cannot lower yet makes `axiom0 build` report `AX_DRIVER_NOT_YET_SUPPORTED` (data
  `construct="native:<feature>"`, `task` = the delivering native task; AXD-014 family — renamed in
  round 2). Dropping a check is never a BOOTSTRAP-SHORTCUT.
- **AXS-BOOT-007:** VS1 includes checked `+ - *` and unary `-` on `i32`/`i64`. The pipeline is:
  - MIR overflow assert → LIR `check_ovf <kind>`, placed right after the arithmetic op (T023);
  - `jo rel32` to `__ax_panic_<kind>` (T025, using the T024 jcc form);
  - T027 synthesises the stub `and rsp, -16; sub rsp, 32; mov ecx, 101; call [ExitProcess]`
    (corrected in round 2);
  - T042 adds the stderr message.
- FP-10 (i32 overflow → exit 101) is now native in T028 with no `native-after`, and the T029
  differential runs it.
- F-ARITH and F-PANIC native cells, the MS-P4 milestone row and the MS-P4 goal are updated to match.
- Other widths, division, shifts, bounds and `char` checks stay in T037 and are refused natively
  until then.

Board edits implied (for the architect run that applies them):
- **T021:** the i32/i64 overflow run tests (FP-10) get no `native-after`. The division-by-zero and
  shift trap tests keep `native-after: T037`.
- **T023:** scope gains the LIR op `check_ovf <kind>`, lowered from a MIR assert whose failure target
  is a panic, with no block split. Golden LIR test for FP-03.
- **T024:** acceptance confirms `jcc rel32` (in particular `jo`) with a REL32 relocation against an
  undefined symbol.
- **T025:** isel covers `add`/`sub`/`imul`/`neg` followed by `jo` to `__ax_panic_<kind>` for i32/i64.
  Every other MIR construct without native lowering reports `AX_DRIVER_NOT_YET_SUPPORTED`.
  `mi` golden test for FP-10.
- **T027:** synthesise every referenced `__ax_panic_<kind>` stub in the startup code as exactly
  `and rsp, -16; sub rsp, 32; mov ecx, 101; call [ExitProcess]`. Fixture test: an object
  referencing `__ax_panic_overflow` links, and jumping to the stub exits with 101 both when `rsp` ≡ 0
  (mod 16) and when `rsp` ≡ 8 (mod 16) at the jump.
- **T028:** acceptance adds that FP-10 exits 101 natively. A native build of a program with a branch
  (before T033) gets `AX_DRIVER_NOT_YET_SUPPORTED` (`task="T033"`); add a ui test for this, which T033 then
  turns into a run test.
- **T029:** the differential includes FP-10. The "VS1 set" wording becomes "constants, checked
  i32/i64 `+ - *`/neg, locals, return".
- **T033 / T037 / T040 / T042 / T051 / T059 / T061b / T061d:** each removes the matching
  `AX_DRIVER_NOT_YET_SUPPORTED` refusal for its constructs. T037 also covers unsigned and
  8/16-bit overflow checks, division, shifts, bounds and `char` checks, all jumping to the same
  `__ax_panic_<kind>` stubs. T042 makes the stubs write `panic: <message>\n` to stderr.
- **T002 / T009:** register `AX_DRIVER_NOT_YET_SUPPORTED` in the DRIVER area of spec/diagnostics.md
  §10.7 as an AXD-014 (transient) code with data `construct` and `task` (round 2; was wrongly
  `AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP`/AXD-013).
- **T025b:** the machine-IR verifier and frame lowering accept a mid-block `jo rel32` to an external
  symbol (`__ax_panic_<kind>`) that has no epilogue path; add a verifier test for it (round 2, N8).
- **T004 / T007:** `tests/unit/driver` has only `test_registry.c` and no `*.test` manifest, so
  gatecheck sees 0 tests there for MS-P1; add an `exec` manifest that runs the driver unit test
  (round 2, N9).
- **T006:** provide `tools/tests/archcheck/run_selftests.py` as its self-test entry point.

### Notes
- **N1:** every Native-task cell of §4 now names task ids. The "same" cells were spelled out and
  the F-FFI oracle cell is `—`. Extraction rule added to AXS-BOOT-030 and step 4: the task ids are
  the `T\d{3}[a-z]?` tokens of the cell.
- **N2:** "not yet due" changed to "not yet done".
- **N3:** AXS-BOOT-070 rewritten. AXS-SEM-073 is now assigned to MS-P3, MS-P4 and MS-P5. 042, 045
  and 046 are split by feature. MS-P4 and MS-P6 entries were added.
- **N4:** the V4 row now says VS2 ends 0263 §51 VS#2 (BOOT-31..38), with BOOT-36 = T086 and
  BOOT-37..38 = T087.
- **N5:** FP-09 now cites the OWNER.md status note of 2026-10-01 and the CLAUDE.md decision of
  2026-09-29.

### Tests
- I re-validated the manifests with a script:
  - all 11 blocks parse and have exact fields;
  - the `previous` chain is linear and every gate exists;
  - every F/X/check id used is defined;
  - each of the 47 Native-task cells yields at least one existing task id.
- `harness_check.py` prints HARNESS OK.
- None of the files contains a CR byte.

## Files changed
- spec/SPEC-00-bootstrap.md
- spec/SPEC-03-core-semantics.md
- spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md
- _workspaces/reports/T003-report.md

STATUS: COMPLETE round=1

## Round 2

Escalated fix round for the two open round-1 findings and notes N8/N9. Only SPEC-00, SPEC-03,
ADR-0012 and this report changed; spec/diagnostics.md was not edited (outside T003's paths).

### F3: alignment-independent panic stub
- One sequence is now normative, written identically in SPEC-00 AXS-BOOT-007 and ADR-0012 §9:
  `and rsp, -16; sub rsp, 32; mov ecx, 101; call [ExitProcess]`.
- Rationale stated in both texts: the stub is entered by `jo` (a jump, no return address), so `rsp`
  can be 0 or 8 (mod 16) on arrival (function body or frameless leaf). `and rsp, -16` re-aligns,
  `sub rsp, 32` reserves the shadow space, so the `call` has `rsp` ≡ 0 (mod 16). The stub never
  returns, so `rsp` is not restored. T042 keeps the same prologue when it adds the message.
- T027's fixture test must jump to the stub from both alignments (rsp ≡ 0 and ≡ 8 mod 16) and get
  exit 101 each time (AXS-BOOT-007 and the T027 board edit).
- The old `sub rsp, 40` / bare `mov ecx, 101` variants no longer appear anywhere in the T003 files.

### F4: refusal code moved to the AXD-014 family
- `AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP` renamed to `AX_DRIVER_NOT_YET_SUPPORTED` in SPEC-00
  AXS-BOOT-006, SPEC-03 AXS-SEM-001, ADR-0012 (Tóm tắt item 9, §9 decision, Consequences board-edit
  list) and this report's board-edit list.
- Data: `construct="native:<feature id>"` plus `task` = the delivering native task (e.g.
  `task="T033"`); the AXD-013 field `data.epic` is no longer used for it.
- AXS-BOOT-006 now cites AXD-014 and states the transience guarantee (no self-host-subset test may
  expect the code for a feature after its `task` is done) and that it is distinct from the permanent
  AXD-013 `_UNSUPPORTED_IN_BOOTSTRAP` codes (which remain correct for out-of-subset constructs such as
  `@at` and floats in AXS-BOOT-00x / SPEC-03 §2, §cast table).
- Registration in spec/diagnostics.md §10.7 stays a follow-up (T002/T009 board edit).

### N8, N9
- N8: T025b added to the board-edit lists (report and ADR-0012 Consequences): verifier and frame
  lowering accept a mid-block `jo rel32` to an external symbol with no epilogue path.
- N9: T004/T007 board edit added: an `exec` `*.test` manifest under `tests/unit/driver`, so MS-P1's
  `must_pass` path is not empty.

### Re-check
`grep` over the four files: no `AX_DRIVER_UNSUPPORTED_IN_BOOTSTRAP`, no `sub rsp, 40`, no stub text
other than the new one. Remaining `_UNSUPPORTED_IN_BOOTSTRAP` mentions are the AXD-013 out-of-subset
codes (`AX_TYPE_…`, `AX_PARSE_…`), which are correct. All files UTF-8, LF.

## Files changed
- spec/SPEC-00-bootstrap.md
- spec/SPEC-03-core-semantics.md
- spec/decisions/ADR-0012-core-execution-semantics-and-milestones.md
- _workspaces/reports/T003-report.md

STATUS: COMPLETE round=2
