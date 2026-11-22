# T499b QA — Tuple patterns in the exhaustiveness checker

## Round 0

### Scope & Code Review
- Reviewed `compiler/types/exhaust.ax` (`match_check_tuple_exhaustiveness`, lines 690–1424) and `compiler/types/typeck.ax` (`tc_match_check_exhaustiveness`, lines 407 and 6059–6062).
  - Column-wise Maranget usefulness matrix handles `SINGLE` (tuples and structs by declared field order/name), `BOOL` (`false`/`true`), `ENUM` (variant index via `thir_get_pat_variant`, tuple/struct variant payloads), `INT` (`<= 64`-bit signed/unsigned integers via biased order-preserving unsigned encoding + `char` `0..=0x10FFFF`, exact disjoint segment splitting), and `OPAQUE` (`i128`/`u128` and other types, wildcard/binding only).
  - Nested and top-level or-patterns (`HIR_PAT_OR`) are expanded; guarded arms are checked for reachability without contributing to the covering matrix.
  - Incomplete signature check in `ex_useful_int` delegates to `D(P)` (`ex_default`), which is sound and exact per Maranget's theorem.
  - Unknown patterns are handled conservatively (cover nothing in `P`, assumed useful in `q`).
  - `compiler/types/typeck.ax` routes `TY_TUPLE` scrutinees to `match_check_tuple_exhaustiveness` and leaves non-tuple scrutinees on the existing checker (cleanup tracked in follow-up `T499c`).
- Verified `tests/run/tuple_expr_names/match_and_destructure.ax` has its trailing workaround `_` arm removed and passes in `interp`, `native`, and `native-O1` with exact `stdout:`.
- Verified `tests/std/num/static_dispatch_xfail.ax` has its `// xfail:` directive removed and passes in `interp`, `native`, and `native-O1` with `stdout: 231\n`.
- Verified all new/touched run tests declare exact `stdout:` (`WEAK-NATIVE: 0` in own/changed tests).

### Boundary Cross-Checks (Step 5)
Added two adversarial test files under T499b's `paths:` and refreshed `build-snap-T499b/`:
- `tests/ui/exhaust_tuple/qa_boundary_missing.ax`: signed `i8` min/max boundaries (`-128..=126` missing `127`, `-127..=127` missing `-128`), exclusive `u8` range (`0u8..255u8` missing `255u8`), struct-in-tuple missing `(Flag { a: false, b: false }, _)`, enum with `bool` payload missing `(OptBool.Some(false), _)`, enum with struct-variant payload missing `(Ev.Pair { x: false, y: false }, _)`, opaque `i128` in tuple, and guarded arm `(true, x) if x => 1` not covering `(true, _)`.
- `tests/run/exhaust_tuple/qa_edge_cases.ax`: nested or-patterns in tuple columns, overlapping and exclusive+point `u8` ranges, exact `i8` min/max split (`-128`, `-127..=126`, `127`), struct-in-tuple exhaustive match, tuple-variant enum + or-pattern in tuple, deeply nested `((bool, OptBool), (u8, bool))` exhaustive match, and guarded arm followed by unguarded fallback — all 3 modes (`interp`, `native`, `native-O1`) with exact `stdout:`.

### Build, Native-Evidence & Gate Evidence (inside `build-snap-T499b/`)
1. **Snapshot refresh**:
   `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T499b`
   -> `HEAD 2dbbd76 + 15 changed, 0 deleted file(s) of T499b`, `bundles regenerated in build-snap-T499b: 36 generator(s), 60 file(s), 25s`.
2. **Stage-2/3 compiler build**:
   `python tools/build_axiomc.py --out build --root . --stage 2`
   -> `BUILD-AXIOMC OK` (`axiomc2.exe`, 9,032,192 bytes, `sha256=32783c83906c9ca689578c1a99a2a858c5b225ce813837928f32708df8138e9d`).
   - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 32783c83906c9ca689578c1a99a2a858c5b225ce813837928f32708df8138e9d` (`seeded B==C`).
   - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`).
3. **Own, changed, and QA adversarial tests (`--no-cache`)**:
   `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter exhaust_tuple --filter tuple_expr_names/match_and_destructure --filter std/num/static_dispatch_xfail -j 2 --verbose`
   -> `TOTAL 24 PASS 24 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
4. **Native-evidence spot-proof (Step 4a)**:
   Mutated `stdout:` in `build-snap-T499b/tests/run/exhaust_tuple/bool_pairs.ax` (`10\n` -> `99\n`) and ran `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache --filter run/exhaust_tuple/bool_pairs --verbose`:
   - Mutated: `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed with `stdout differs at byte 20`, exit 1).
   - Restored: `TOTAL 3 PASS 3 FAIL 0` (`interp`, `native`, `native-O1` all PASS, exit 0).
5. **Per-task gate (`taskgate.py`)**:
   `python tools/taskgate.py --task T499b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T499b.json`

### taskgate T499b (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T499b`, HEAD `2dbbd763dcc4`, compiler `D:/projects/compiler/new lang/build-snap-T499b/build/axiomc2.exe`, `-j 2`
- change set: 34 file(s) (15 task/QA files + 19 regenerated selfhost bundles)
- wall time: 895.2 s (axtest 878.0 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 12 | 24 | 24 | 0 | 0 | 0 | 0 |
| affected | 84 | 137 | 136 | 0 | 1 | 0 | 0 |
| smoke | 32 | 55 | 55 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 114 | 190 | 189 | 0 | 1 | 0 | 0 |

- Affected-set derivation: exact dependency match for all 12 own/changed tests + compiler map (`compiler/types` -> `tests/typeck`, `tests/ui/typeck`) + all selfhost bundles embedding `compiler.types.exhaust`/`compiler.types.typeck` + their `bundles_current.test` checks; unmatched changed files: none.
- Smoke: seed=962374413 (32 groups incl. `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`).
- Cache: `CACHED 0, miss 48, uncacheable 54, stored 47, dep_source exact, verification sample seed=2126957463 n=12 of 12 hits, mismatch none`.
- `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
- `Baseline: BASELINE OK`, `Failing ids: none`
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 22 s`
- `axtest: TOTAL 190 PASS 189 FAIL 0 SKIP 1 XFAIL 0 (exit 0)`
- `TASKGATE T499b exit=0`

6. **Board & harness checks**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T499b` -> exit 0, 16 files staged, 0 `REFUSED`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.

### Findings
None.

### Notes / Follow-ups
- Pre-existing (out of scope for T499b): during adversarial testing, constructing an enum struct-variant (`Ev.Pair { x: true, y: false }`) triggered MIR verifier `AX_VERIFY_TYPE_MISMATCH: enum aggregate variant field count mismatch` (exhaustiveness checking itself handled `Ev.Pair { ... }` cleanly in `qa_boundary_missing.ax`).

### Rebase gate (HEAD 26da17f)
- Snapshot `build-snap-T499b/` verified at HEAD `26da17f0` (post-T423e rebase, 16 task/QA files + regenerated selfhost bundles).
- **Stage-2/3 compiler build**: `python tools/build_axiomc.py --out build --root . --stage 2`
  - `BUILD-AXIOMC OK` (`axiomc2.exe`, 9,029,120 bytes, `sha256=8ce19800f0b6edf4704c78dc93b3608786b39129790def7e042163d7a064c19f`).
  - `FIXED-POINT (O1) OK` (`sha256(axiomc2_O1) == sha256(axiomc3_O1)`, `[seeded B==C]`).
  - `STAGE0-GUARD OK` (byte-identical `.exe` on 6 smoke programs, `O1`, incl. `Xin chào thế giới`).
- **Per-task gate (`taskgate.py`)**: `python tools/taskgate.py --task T499b --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T499b.json`
  - `change set: 35 file(s)` (16 task/QA files + 19 regenerated selfhost bundles, incl. the 9 rebased bundles); wall time `804.5 s` (`axtest 795.1 s`).
  - `own`: 12 ids / 24 results (`24 PASS, 0 FAIL`); `affected`: 84 ids / 137 results (`136 PASS, 0 FAIL, 1 SKIP`); `smoke` (seed `2590651530`): 32 ids / 51 results (`51 PASS, 0 FAIL`); **total (dedup)**: 114 ids / 186 results (`185 PASS, 0 FAIL, 1 SKIP, 0 XFAIL`).
  - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`; `Baseline: BASELINE OK`; `Failing ids: none`.
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`; `smoke-check (tests/smoke.list): OK; est. worst-case draw 19 s`.
  - `Cache: CACHED 0, miss 58, uncacheable 56, stored 58, dep_source exact, mismatch none`.
  - `TASKGATE T499b exit=0`.
- **Board & harness checks**: `taskctl.py changes T499b` -> exit 0, 16 files staged, 0 `REFUSED`; `harness_check.py` -> `HARNESS OK`.

## Files changed
- tests/ui/exhaust_tuple/qa_boundary_missing.ax
- tests/run/exhaust_tuple/qa_edge_cases.ax
- _workspaces/reports/T499b-qa.md

VERDICT: PASS round=0
VERDICT: PASS round=0 (rebase)
