# T499c QA Gate Report

## Round 0

### 1. Code review & acceptance checks
- **`compiler/types/typeck.ax`**:
  - `Select-String -Path 'compiler/types/typeck.ax' -Pattern 'exhaust|if false|PatInterval|EXH_|AX_PAT_'` confirms NO exhaustiveness logic remains in `typeck.ax` other than the 1-line delegation `tc_match_check_exhaustiveness` -> `match_check_exhaustiveness_with_tv` (`compiler/types/typeck.ax:5987-5997`, called at `:8512`), and NO `if false {}` reference remains.
- **`compiler/types/exhaust.ax`**:
  - Verified superseded old checker functions (`match_check_exhaust_bool_or_enum`, `match_check_tuple_exhaustiveness`, unused interval helpers) were deleted while preserving `PatInterval`, `PatInterval128`, `get_pat_interval`, and `get_pat_interval_128`.
  - Audited `ExPt128` 128-bit biased unsigned arithmetic:
    - `i128` (`-170141183460469231731687303715884105728..=170141183460469231731687303715884105727`) and `u128` (`0..=340282366920938463463374607431768211455`) domain bounds, two's-complement negation, carry in `ex_u128_inc`, and borrow in `get_pat_interval_128` exclusive ranges (`e.start_lo == 0`) are exact.
    - `char` domain `0x0000..=0x10FFFF` explicitly inserts surrogate split points `0xD800` and `0xE000` in `ex_int_segments` and skips `0xD800..=0xDFFF` via `ex_is_char_surrogate`.
    - `TypeVarTable` resolution (`type_vars_resolve`) is applied in both `match_check_exhaustiveness_with_tv` and `ex_col`.
    - Empty/inverted intervals (`start > end` or `x..x`) produce `EXH_EMPTY` -> `AX_PAT_UNREACHABLE` warning and do not satisfy exhaustiveness.
    - `TY_UNIT` is classified as `EXC_SINGLE` with arity `0`.
    - Bare enum with refutable payload (`Opt.Some(1)` + `Opt.None`) emits `AX_PAT_NON_EXHAUSTIVE`.

### 2. Compiler build in snapshot (`build-snap-T499c/`)
- `python tools/build_axiomc.py --out build --root . --stage 2` -> `BUILD-AXIOMC OK`:
  - `REUSED D:\projects\compiler\new lang\build-snap-T499c\build\dir_stage2_O1\axiomc2.exe` (`size=9004544`, `sha256=5b5d4d11a5105b0c962c13f25dea85d5d37821187d8ce9d1f81f8c5d85cf9749`, matching engineer's `FIXED-POINT (O1) OK` and `STAGE0-GUARD OK` build).

### 3. Boundary cross-check (step 5) & own tests
Added two adversarial boundary tests under T499c's `paths:` and refreshed `build-snap-T499c/` via `taskctl.py snapshot T499c` (`36 generator(s), 60 file(s)`):
- `tests/ui/exhaust_unified/qa_boundary_seams.ax`:
  - `char` missing `'\u{D7FF}'` and missing `'\u{E000}'` around surrogate hole (`AX_PAT_NON_EXHAUSTIVE`)
  - `u128` missing single value `2^64` across lo/hi carry boundary (`AX_PAT_NON_EXHAUSTIVE`)
  - `i128` missing `-1i128`, `0i128`, `i128_min`, `i128_max` (`AX_PAT_NON_EXHAUSTIVE`)
  - Empty/inverted ranges `5u8..=3u8`, `5u8..5u8`, `0u8..0u8` (`AX_PAT_UNREACHABLE` + `AX_PAT_NON_EXHAUSTIVE`)
  - `TY_UNIT` duplicate `_` arm (`AX_PAT_UNREACHABLE`)
  - Inferred `let n = Option.None; match n { Option.Some(true) => 1, Option.None => 0 }` (`AX_PAT_NON_EXHAUSTIVE`)
- `tests/run/exhaust_unified/qa_boundary_complete.ax` (exact `stdout:`, all 3 modes):
  - `char` exact surrogate boundary values `'\u{D7FF}'`/`'\u{E000}'` and straddling `'\0'..='\u{10FFFF}'`
  - `u128` exclusive `0u128..18446744073709551616u128` (borrow across lo/hi) + `18446744073709551616u128..=u128_max`
  - `i128` exclusive `i128_min..0i128` + `0i128..=i128_max`
  - `TY_UNIT` complete match

Run in `build-snap-T499c/`:
- `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter exhaust_unified -j 2 --verbose`
  -> `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

### 4. Native-evidence spot-proof (step 4a)
- Confirmed all 3 run tests under `tests/run/exhaust_unified/` (`enum_payloads_and_nested.ax`, `structs_and_ranges.ax`, `qa_boundary_complete.ax`) check exact `stdout:` and run in `interp`, `native`, and `native-O1` (`WEAK-NATIVE: 0`).
- Mutated `stdout:` in `build-snap-T499c/tests/run/exhaust_unified/qa_boundary_complete.ax` (`42\n` -> `99\n`) and ran `--no-cache --filter run/exhaust_unified/qa_boundary_complete -j 2 --verbose`:
  - Mutated: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all FAILED with `stdout differs at byte 27`), `MUTATED_EXIT=1`.
  - Restored: `TOTAL 3 PASS 3 FAIL 0` (`interp`, `native`, `native-O1` all PASS).

### 5. Per-task gate (`tools/taskgate.py` inside `build-snap-T499c/`)
Command:
`python tools/taskgate.py --task T499c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T499c.json`

Summary:
- root `D:/projects/compiler/new lang/build-snap-T499c`, HEAD `c64480a988bf`, compiler `D:/projects/compiler/new lang/build-snap-T499c/build/axiomc2.exe`, `-j 2`
- change set: 31 file(s) (working tree of `build-snap-T499c` vs HEAD; 10 engineer files + 2 QA tests + 19 changed regenerated selfhost bundles)
- wall time: `930.1 s` (axtest `921.9 s`)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 9 | 15 | 15 | 0 | 0 | 0 | 4 |
| affected | 81 | 128 | 127 | 0 | 1 | 0 | 23 |
| smoke | 33 | 54 | 54 | 0 | 0 | 0 | 17 |
| **total (dedup)** | 112 | 180 | 179 | 0 | 1 | 0 | 39 |

- Affected-set derivation: `exact` (9 `exhaust_unified` tests), `compiler: generator check of a bundle embedding compiler.types.exhaust`, `test: changed test file` (regenerated selfhost bundles incl. `selfhost/typeck/qa_typeck_all.ax`, `selfhost/typeck_traits/qa_typeck_traits_all.ax`, `selfhost/types/qa_types_exhaust.ax`), `compiler: map compiler/types -> tests/typeck` & `tests/ui/typeck`; `unmatched changed files: none`.
- Smoke: `seed=364869406`, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax` + 30 per-group draws.
- Cache: `CACHED 39, miss 7, uncacheable 56, stored 7, dep_source exact, verification sample seed=1007138623 n=20 of 49 hits, mismatch none, rejected {}, producer snapshot`.
- `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`.
- `Baseline: BASELINE OK`, `Failing ids: none`.
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`.
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 19 s`.
- `axtest: TOTAL 180 PASS 179 FAIL 0 SKIP 1 XFAIL 0` (`TASKGATE T499c exit=0`).

### 6. Board & harness hygiene
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T499c` -> exit 0, 0 `REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

### Findings
None.

### Follow-ups
- Pre-existing `typeck.ax` gap (outside T499c scope): `check_pat` for `HIR_PAT_TUPLE` (`compiler/types/typeck.ax:5930`) only accepts `TY_TUPLE` and rejects `()` against `TY_UNIT` with `AX_TYPE_MISMATCH`, even though `compiler/types/exhaust.ax` already supports `TY_UNIT` `()` patterns.

## Files changed
- tests/ui/exhaust_unified/qa_boundary_seams.ax
- tests/run/exhaust_unified/qa_boundary_complete.ax

VERDICT: PASS round=0
