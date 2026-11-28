# T428p Report — Fix generic close split after `view<..>` / `mut_view<..>` in generic lists

## Summary
Routed closing-`>` parsing for `view<T>` / `mut_view<T>` types and generic parameter lists through a shared `expect_closing_gt` helper backed by `split_gt` per `SPEC-02` `AXS-GRM-057`, so `>`, `>>`, `>=`, and `>>=` split cleanly everywhere a capability type or generic list closes.

## Closing-`>` audit (`compiler/syntax/parse.ax`)
Every closing-`>` / `<...>` site in `compiler/syntax/parse.ax` was audited:

| Site | Lines | Before | After |
|---|---|---|---|
| `expect_closing_gt` (new helper) | ~1005–1017 | — | Added helper calling `split_gt` for `TOK_SHR` (`>>` -> `>`), `TOK_GT_EQ` (`>=` -> `=`), `TOK_SHR_EQ` (`>>=` -> `>=`), advancing on `TOK_GT`, or reporting `AX_PARSE_EXPECTED_TOKEN` / `MSG_EXPECTED_GT`. |
| `parse_generic_args` | ~1135 | Inline `split_gt` `if`/`else if` chain | Calls `expect_closing_gt(mut_view(*parser))`. |
| `parse_view_type` (`TYPE_VIEW`: `view<T>` / `mut_view<T>`) | ~1333 | `expect(..., TOK_GT, ...)` (bypassed `split_gt`, breaking `Option<view<[S]>>`, `Option<mut_view<Self>>`, `>>>`, `>>=`, `>=`) | Calls `expect_closing_gt(mut_view(*parser))`. Works in both committed and tentative (`try_generic_args`) parses with rollback via `split_rollback`. |
| `parse_generic_params` (`<T: Bound, U>`) | ~2429–2442 | `while more_before(..., TOK_GT)` and `expect(..., TOK_GT, ...)` (bypassed `split_gt`, breaking `type Alias<T>= ...` and `type Alias<T: Trait<U>>= ...`) | Loop stops on `TOK_GT`, `TOK_SHR`, `TOK_GT_EQ`, `TOK_SHR_EQ`; closing `>` calls `expect_closing_gt(mut_view(*parser))`. |
| `parse_path_type` / `parse_path_pattern` / `parse_dot_suffix` / `parse_path_expr` | ~1254–1256, ~1482, ~1682, ~1703, ~1737, ~2071 | All delegate to `parse_generic_args` or `try_generic_args` | Already routed through `expect_closing_gt` via `parse_generic_args`; no direct `TOK_GT` consumption. |
| `parse_pointer_type`, `parse_array_or_slice_type`, `parse_fn_type`, `parse_tuple_type`, `TYPE_DYN` (`parse_bounds`) | ~1275–1389 | No own closing `>`; delegate inner types to `parse_type` / `parse_bounds` | Already split via inner `parse_generic_args` / `parse_view_type`; no change needed. |

## Tests added (`tests/parse/view_in_generic_args/`)
- `view_generic_parse.ax` (`// test: ui`, `// exit: 0`): covers `Option<view<[S]>>`, `Option<mut_view<Self>>` in an `impl`, `Result<view<S>, Option<view<[u8]>>>` (`>>>`), `let x: Option<view<S>>= Option.None;` (`>>=` split), `let y: view<S>= view(s);` (`>=` split), `type Alias<T>= i32;` and `type AliasBound<T: Marker<i32>>= i32;` (`>=` / `>>=` split in generic params), and `id<view<[i32]>>(view(arr))` (tentative expression generic args with `view<..>`).
- `view_slice_option_run.ax` (`// test: run`, `modes: interp native`, exact `// stdout: 15\n-1\n`): passes `Option<view<[i32]>>` (`Option.Some(v)` and `Option.None`) to `sum_opt`, reads through the slice view, and prints the sums.
- `unbalanced_view_gt.ax` + `unbalanced_view_gt.test`: negative case verifying unbalanced `fn bad(x: view<S>>) {}` outside any generic list still exits `1` with `AX_PARSE_UNCLOSED_DELIMITER`.

## Verification (inside `build-snap-T428p/`, HEAD `d57010be`)

### Stage-2 / Stage-3 fixed point (`-O1` and `-O0`)
Command: `python tools/build_axiomc.py --out build --root . --opt both --stage 3`
- `STAGE1 OK`: `axiomc1.exe` (`34980352` bytes, `sha256=4bca96078c2af7c1`)
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == b757c3d718e78cd3f2217cd4a23c2e3c0a8b9e49f58d95686f245a4d2dd05465` (`9366528` bytes)
- `FIXED-POINT (O0) OK`: `sha256(axiomc2_O0) == sha256(axiomc3_O0) == b697c35d678af571826060adc55ce33f4c8bcc7feed4176e042d9efe8142dcc9` (`20542464` bytes)
- `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`)
- `BUILD-AXIOMC OK`

### Targeted tests
Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --filter parse/view_in_generic_args --no-cache -j 2 --verbose`
- `TOTAL 5 PASS 5 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)
  - `PASS parse/view_in_generic_args/unbalanced_view_gt.test`
  - `PASS parse/view_in_generic_args/view_generic_parse.ax`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [interp]`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [native]`
  - `PASS parse/view_in_generic_args/view_slice_option_run.ax [native-O1]`

### Taskgate (`tools/taskgate.py`)
Command: `python tools/taskgate.py --task T428p --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428p.json`
- `TASKGATE T428p exit=0`
- `axtest`: `TOTAL 257 PASS 256 FAIL 0 SKIP 1 XFAIL 0` (`exit 0`)
  - `parse`: 48 ids, 0 failing
  - `ui` (`ui/parse` + smoke): 28 ids, 0 failing
  - `selfhost` (incl. `selfhost/parse/*`, `selfhost/parser/*`, and `bundles_current.test` across all affected groups): 47 ids, 0 failing
  - `conformance`: 6 ids, 0 failing
  - `smoke`: 35 ids, 0 failing
- `WEAK-NATIVE`: `0` in own/changed tests (`3` in the full run)
- `Baseline`: `BASELINE OK` (`Failing ids: none`)
- `archcheck`: clean (`exit 0`, 252 files scanned, 0 violations)
- `smoke-check (tests/smoke.list)`: `OK`

### Hygiene (from main repo root)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428p`: 6 staged files, `0 REFUSED`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`

## Files changed
- `compiler/syntax/parse.ax`
- `tests/parse/view_in_generic_args/view_generic_parse.ax`
- `tests/parse/view_in_generic_args/view_slice_option_run.ax`
- `tests/parse/view_in_generic_args/unbalanced_view_gt.ax`
- `tests/parse/view_in_generic_args/unbalanced_view_gt.test`

## Status
STATUS: COMPLETE round=0
