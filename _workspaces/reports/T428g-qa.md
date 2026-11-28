# T428g QA Report (Round 0)

## 1. Code & Spec Audit

Audited `_workspaces/tasks/doing/T428g-fix-typeck-type-lookup-by-bare-name-cross-module-collision.md`, `_workspaces/reports/T428g-report.md`, `git diff -- compiler/types/typeck.ax _workspaces/baseline-failures.txt`, and all new tests under `tests/run/same_name_std_types/` and `tests/modules/same_name_types/`:

- **`lookup_path_type_by_name` (`compiler/types/typeck.ax:5472-5760`)**:
  - **Bound paths (`path.symbol.v != 0 || path.def_dom != 0`)**: Strictly isolated in the bound branch (`5516-5615`) and never fall through to the bare-name walk. Selects strictly by `symbol` (covering top-level `fn`/`const`/`static`/`struct`/`enum`/`type_alias`, enum variants, `extern`/`impl`/`trait` members, and `current_fn` parameters) or by `def_mod` + `def_name` (via `tc_item_matches_def_mod`, skipping shallow `impl` member clones). Forward-referenced `fn`/`const`/`static` signatures are computed idempotently on demand in `tc_resolve_matched_path_item` (with `t_error` cycle guard) and `register_item_sig` (`13548-13778`). Unmatched bound items (e.g., bound `trait` or `module` in type position) emit `AX_NAME_UNRESOLVED` immediately.
  - **Unbound paths (`symbol == 0 && def_dom == 0`)**: Bare-name fallback (`5657-5760`, reached only after generic parameter lookup) skips shallow `impl` member clones, prefers the current module's item (`tc_current_module_anchor`), and emits `AX_NAME_UNRESOLVED` when multiple distinct non-current modules define the bare name (`other_mod_ambiguous`).
- **Bare-name item scan inventory**: Independently scanned `compiler/types/typeck.ax` for `(*cx.hir).items` loops comparing names; confirmed the 10-item inventory in `_workspaces/reports/T428g-report.md` is complete and accurate (the only other loop, `check_atomic_struct_layouts` at L14971, inspects struct attributes `packed`/`repr`/`align`, not item names).
- **`_workspaces/baseline-failures.txt`**: Both `T428g` entries (`conformance/p11/e11_5_executors/spawn_affinity_vs_migration.ax`, `fiber_in_async_and_threads.ax`) and their comment block are cleanly removed, leaving 0 active baseline entries.
- **Scope hygiene**: No edits to resolver, HIR, `docs/`, or `bootstrap/axiom0/`.

## 2. QA Adversarial Tests Added

Added two independent adversarial test packages under `tests/modules/same_name_types/` (written in main repo and mirrored into `build-snap-T428g/`, LF-only line endings):

1. **`tests/modules/same_name_types/qa_forward_and_generic`** (`test: run`, `modes: interp native`, exact `// stdout: 1234 56 7 11 22 33 44\n`):
   - Probes forward-referenced `pub static VAL: i64` and `pub fn helper() -> i64` from module `w` (ordered after `main`) colliding with `a.VAL: bool` and `a.helper() -> bool` (ordered before `main`), plus three distinct generic `struct Wrap<T>` (`main.Wrap`, `a.Wrap`, `w.Wrap`), identical-variant enums `a.Tag.One` / `w.Tag.One`, `a.Item` / `w.Item` aliases, and nested generic arguments `Option<w.Wrap<a.Tag>>` and `Result<a.Wrap<w.Tag>, w.Wrap<a.Tag>>`.
   - Result: `PASS` in `[interp]`, `[native]`, `[native-O1]`; `WEAK-NATIVE 0`.
2. **`tests/modules/same_name_types/qa_generic_arg_mismatch`** (`test: ui`):
   - Probes pure nominal identity (REQ-TYP-072, REQ-MOD-003) across structurally identical `a.S`/`b.S`, `a.Alias`/`b.Alias`, and `a.E`/`b.E` (identical field and variant names): passing `Option.Some(a.mk(1i32))` to `fn takes_opt_b(x: Option<b.S>)`, assigning `a.mk(2i32)` to `b.Alias`, and assigning `a.E.V(3i32)` to `b.E` all produce `AX_TYPE_MISMATCH`.
   - Result: `PASS`.

## 3. Independent Verification (`build-snap-T428g/`, `-j 2`)

- **Binary & source identity**:
  - `build-snap-T428g/build/axiomc2.exe` SHA256 = `9dbfb30db402a63be0cabc51e79b1eefaae0f463713f93bb13df0e545388e409` (matches report fixed-point Stage-2/Stage-3 hash).
  - `compiler/types/typeck.ax` (`BA276B6F75DC0E03...`) and `_workspaces/baseline-failures.txt` (`26EC3C77EC0ABA91...`) verified byte-identical between main repo and `build-snap-T428g/`.
- **Targeted suite (`--filter run/same_name_std_types --filter modules/same_name_types --filter conformance/p11/e11_5_executors --no-cache -j 2 --verbose`)**:
  - `TOTAL 43 PASS 43 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **QA adversarial tests (`--filter modules/same_name_types/qa_ --no-cache -j 2 --verbose`)**:
  - `TOTAL 4 PASS 4 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- **Live mutation spot-proof** (inside `build-snap-T428g/` ONLY on `tests/modules/same_name_types/qa_forward_and_generic/src/main.ax`):
  - Mutated `// stdout: 1234 ` -> `// stdout: 9999 `: `exit=1`, `TOTAL 3 PASS 0 FAIL 3` (`[interp]`, `[native]`, `[native-O1]` all failed with `stdout differs at byte 0`).
  - Restored byte-identical: `exit=0`, `TOTAL 3 PASS 3 FAIL 0`, `WEAK-NATIVE 0`.
- **Task gate (`python tools/taskgate.py --task T428g --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T428g.json`)**:
  - `own`: `9 ids / 19 results` (`19 PASS, 0 FAIL`)
  - `affected`: `85 ids / 136 results` (`135 PASS, 0 FAIL, 1 SKIP` — verified `selfhost/typeck/qa_typeck_all.ax`, `selfhost/typeck_traits/qa_typeck_traits_all.ax`, and `bundles_current` included and passing)
  - `smoke`: `34 ids / 55 results` (`55 PASS, 0 FAIL`, seed `1479536990`)
  - `total (dedup)`: `117 ids / 189 results: TOTAL 189 PASS 188 FAIL 0 SKIP 1 XFAIL 0`
  - `WEAK-NATIVE`: `0 in the task's own/changed tests`
  - `Baseline`: `BASELINE OK`, `Failing ids: none`, `unmatched changed files: none`
  - `archcheck`: `clean (exit 0) — 252 files scanned, 0 violations`
  - `smoke-check (tests/smoke.list)`: `OK; est. worst-case draw 24 s`
  - `TASKGATE T428g exit=0`

## 4. Hygiene Checks (Main Repo Root)

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T428g`: verified exit 0, `0 REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: verified exit 0, `HARNESS OK`.
- Line endings across `tests/modules/same_name_types/**`: verified LF-only (`CRLF_BAD: []`).

## Files changed
- tests/modules/same_name_types/qa_forward_and_generic/axiom.toml
- tests/modules/same_name_types/qa_forward_and_generic/src/a.ax
- tests/modules/same_name_types/qa_forward_and_generic/src/w.ax
- tests/modules/same_name_types/qa_forward_and_generic/src/main.ax
- tests/modules/same_name_types/qa_generic_arg_mismatch/axiom.toml
- tests/modules/same_name_types/qa_generic_arg_mismatch/src/a.ax
- tests/modules/same_name_types/qa_generic_arg_mismatch/src/b.ax
- tests/modules/same_name_types/qa_generic_arg_mismatch/src/main.ax
- _workspaces/reports/T428g-qa.md

## Verdict
VERDICT: PASS round=0
