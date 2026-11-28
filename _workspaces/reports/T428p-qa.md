# T428p QA Report (round 0)

## Audit Results

### Code & Spec Audit (`compiler/syntax/parse.ax`, `SPEC-02 AXS-GRM-057`)
- Verified `git diff -- compiler/syntax/parse.ax` and audited every `TOK_GT`, `TOK_SHR`, `TOK_LT`, and `split_gt` site in `compiler/syntax/parse.ax`:
  - `expect_closing_gt` (lines 1005–1017): cleanly splits `TOK_SHR` (`>>` -> `>`), `TOK_GT_EQ` (`>=` -> `=`), `TOK_SHR_EQ` (`>>=` -> `>=`) via `split_gt`, advances on `TOK_GT`, and emits `AX_PARSE_EXPECTED_TOKEN` / `MSG_EXPECTED_GT` otherwise.
  - `parse_generic_args` (line 1135): delegates closing `>` to `expect_closing_gt`.
  - `parse_view_type` (`view<T>` / `mut_view<T>`, line 1333): delegates closing `>` to `expect_closing_gt`, supporting both committed and tentative (`try_generic_args` with `split_rollback`) parses.
  - `parse_generic_params` (lines 2429–2442): loop stops on `TOK_GT`, `TOK_SHR`, `TOK_GT_EQ`, and `TOK_SHR_EQ` and closes via `expect_closing_gt`.
  - All other `<...>` sites (`parse_path_type`, `parse_path_pattern`, `parse_path_expr` / `parse_dot_suffix`) route through `parse_generic_args` or `try_generic_args`; no closing-`>` site bypasses `expect_closing_gt`.
- Negative case (`tests/parse/view_in_generic_args/unbalanced_view_gt.ax` + `.test`): confirmed unbalanced `fn bad(x: view<S>>) {}` outside any generic list exits `1` with `AX_PARSE_UNCLOSED_DELIMITER`.
- Scope hygiene: no edits outside `compiler/syntax/parse.ax` and `tests/parse/view_in_generic_args/` (no `docs/`, no `bootstrap/axiom0/`).

### Artifact & Snapshot Identity
- `build-snap-T428p/build/axiomc2.exe` SHA256: `b757c3d718e78cd3f2217cd4a23c2e3c0a8b9e49f58d95686f245a4d2dd05465` (matches `T428p-report.md`).
- `compiler/syntax/parse.ax` SHA256 (main repo == `build-snap-T428p/`): `30a8c6908e28a14c655806bb6a6f2534910befd6810206a18528b311bae761ac` (byte-identical).

## QA Adversarial Test Added
- `tests/parse/view_in_generic_args/qa_nested_view_close_run.ax` (`// test: run`, `exit: 0`, exact `// stdout: 30\n7\n11\n42\n99\n30\n`):
  - Exercises deep/nested capability generic closes at runtime across all 3 modes (`interp`, `native`, `native-O1`, `WEAK-NATIVE 0`):
    - `view<[i32]>= ...` (`>=` split)
    - `Option<Option<view<[i32]>>>` and `let nested: Option<Option<view<[i32]>>>= ...` (`>>>` and `>>>=` splits)
    - `let x: Option<view<i32>>= ...` (`>>=` split)
    - `let y: Option<Option<view<i32>>>= ...` (`>>>=` split)
    - `mut_view<Option<view<i32>>>` (`>>` split with `mut_view` enclosing `Option<view<i32>>`, mutating the outer `Option` through `mut_view` and reading back)
    - `pick<Option<view<[i32]>>>(Option.Some(v))` (`>>>` split inside tentative expression generic args `try_generic_args`)

## Independent Verification (inside `build-snap-T428p/`, `-j 2`)

### 1. Targeted Tests (`parse/view_in_generic_args`)
Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --filter parse/view_in_generic_args --no-cache -j 2 --verbose`
- `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`):
  - `PASS parse/view_in_generic_args/qa_nested_view_close_run.ax [interp]`
  - `PASS parse/view_in_generic_args/qa_nested_view_close_run.ax [native]`
  - `PASS parse/view_in_generic_args/qa_nested_view_close_run.ax [native-O1]`
  - `PASS parse/view_in_generic_args/unbalanced_view_gt.test`
  - `PASS parse/view_in_generic_args/view_generic_parse.ax`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [interp]`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [native]`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [native-O1]`

### 2. Live Mutation Spot-Proof (inside `build-snap-T428p/` only)
Target: `build-snap-T428p/tests/parse/view_in_generic_args/qa_nested_view_close_run.ax`
- Mutated expected stdout last line (`30\n` -> `31\n`): all 3 modes (`[interp]`, `[native]`, `[native-O1]`) FAILED (`TOTAL 3 PASS 0 FAIL 3`, exit `1`).
- Restored byte-identical from main repo (SHA256 `494c77d0953d83fbb1452e144f2f6c9db090eab915fd19a09d2ea4544f072a74`): all 3 modes PASSED (`TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`, exit `0`).

### 3. Taskgate (`tools/taskgate.py`)
Command: `python tools/taskgate.py --task T428p --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428p.json`
- `TASKGATE T428p exit=0`
- `own`: 4 ids, 8 results (`8 PASS, 0 FAIL, 0 SKIP, 0 XFAIL, 0 CACHED`)
- `affected`: 134 ids, 203 results (`202 PASS, 0 FAIL, 1 SKIP, 0 XFAIL`)
- `smoke`: 34 ids, 55 results (`55 PASS, 0 FAIL, 0 SKIP, 0 XFAIL`)
- `total (dedup)`: 167 ids, `TOTAL 257 PASS 256 FAIL 0 SKIP 1 XFAIL 0` (`exit 0`)
- Groups verified: `parse` (49 ids, 0 failing), `ui` (27 ids, 0 failing), `selfhost` (47 ids, 0 failing, incl. `selfhost/parse/*`, `selfhost/parser/*`, `bundles_current.test`), `conformance` (6 ids, 0 failing), `smoke` (34 ids, 0 failing).
- `WEAK-NATIVE`: `0 in the task's own/changed tests` (`3 in the run`)
- `Baseline`: `BASELINE OK` (`Failing ids: none`)
- `archcheck`: `clean (exit 0) archcheck: 252 files scanned, 0 violations`
- `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 29 s`

### 4. Hygiene (from main repo root)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428p`: `0 REFUSED` (verified after writing this report).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

## Files changed
- `tests/parse/view_in_generic_args/qa_nested_view_close_run.ax`

## Verdict
VERDICT: PASS round=0
