# T423e QA report

## Round 0

### 1. Code review & static checks
- **Zero placeholder function-name lists in `compiler/`**:
  `Select-String -Path "build-snap-T423e\compiler\**\*.ax" -Pattern "__ax_thread_self_entry|__ax_fiber_self_entry"` -> **0 hits**.
- **Exact `@lang("self_entry")` attribute matching**:
  - `compiler/interp/interp.ax` (`is_self_entry_fn_item`, lines 1349–1389) and `compiler/lir/builder.ax` (`has_self_entry_attr`, lines 466–501) both iterate `(*func).attrs` and match strictly: attribute name `"lang"` (len 4), exactly one unnamed argument (`arg != 0 && arg.next == 0 && arg.name.v == 0`), `HIR_EXPR_LITERAL` with `literal.kind == 3u8` (string), `str_len == 10`, exact bytes `"self_entry"`. Rejects `@lang("self_entry_x")`, `@lang("self")`, `@lang("self_entr")`, `@other("self_entry")`, multi-arg/named-arg `@lang(...)`, and unmarked `fn __ax_thread_self_entry`.
  - Both `resolve_const_op_val` (`compiler/interp/interp.ax:1391-1409`) and `lb_format_fn_item_sym_name` (`compiler/lir/builder.ax:955-967`) resolve the `HirItem` by `SymbolId` and inspect `attrs` rather than deduplicated `HirItem.name`, so `mb_dedup_mono_names` renaming (`__ax_thread_self_entry$s<sym>`) never breaks rewriting in either mode.
  - `exec_assign_repeat` (`compiler/interp/interp.ax:2495`) now routes `MIR_RVALUE_REPEAT` constant operands through `resolve_const_op_val`, keeping `[placeholder; N]` consistent between interp and native.
  - `tests/std/channel/gen_tests.py` (`read_source`, lines 1095–1098) now reads live `ROOT` sources instead of `git show HEAD:...`.
- **`std/` adoption & bundle freshness**:
  - `Select-String -Path "build-snap-T423e\std\**\*.ax" -Pattern "__ax_fiber_self_entry|__ax_thread_self_entry|self_entry"` confirms `std/thread/mod.ax` and `std/fiber/mod.ax` both declare `@lang("self_entry") fn __ax_thread_self_entry(ctx: *mut u8) -> i64` and `__ax_fiber_self_entry` is retired (0 hits in `std/`).
  - All 10 `gen_tests.py --check` scripts (`tests/std/fiber`, `tests/std/async/{executor,structured,waker,waker_qa}`, `tests/std/channel`, `tests/std/sync`, `tests/conformance/p11/{e11_3_threads_sync,e11_5_executors}`, `tests/perf/p11_executor`) exited 0 in `build-snap-T423e/`.

### 2. Isolated snapshot build (`build-snap-T423e/`)
- Command: `python tools/build_axiomc.py --out build --root . --stage 2` (inside `build-snap-T423e/`)
- Result: `STAGE1 OK`, `SEED-A (O1) OK`, `STAGE2 (O1) OK`, `STAGE3 (O1) OK`, `FIXED-POINT (O1) OK` (`sha256=8e5644ca9eb4ebe7a16bab359fc20e40cddb5d40557a1f6bc9909b99d1de455d`, 8,970,752 bytes, seeded `B==C`), `STAGE0-GUARD OK`.

### 3. Boundary cross-check & QA adversarial test (step 5)
- Added `tests/run/self_entry_placeholder/qa_self_entry_seams.ax` covering:
  - Near-miss attributes (`@lang("self_entry_x")`, `@lang("self")`, `@lang("self_entr")`) and unmarked plain function staying ordinary functions (incl. inside `[__ax_thread_self_entry; 2]`).
  - Stacked attributes (`@lang("ignored_first_tag") @lang("self_entry")`) verifying full attribute-list traversal.
  - Two modules both declaring `@lang("self_entry") fn __ax_thread_self_entry`, each instantiated with multiple concrete types (`u16`, `[3]i64`, `u8`, `[2]i64`), exercising direct call `__ax_thread_self_entry(raw)` (`MIR_TERM_CALL`), struct field `HolderA { cb: __ax_thread_self_entry, ... }`, tuple `(3i64, __ax_thread_self_entry)`, array repeat `[__ax_thread_self_entry; 2]`, and array literal `[__ax_thread_self_entry, __ax_thread_self_entry]`.
- Refreshed snapshot: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T423e` -> `HEAD 2dbbd76 + 123 changed`, 60 bundles regenerated in 26s.
- Command: `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/self_entry_placeholder` (inside `build-snap-T423e/`)
- Result: `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (all 6 tests x `interp`, `native`, `native-O1`, every test asserts exact `stdout:`).

### 4. Native-evidence spot-proof (step 4a)
- Mutated expected stdout `2116\n` -> `2117\n` in `build-snap-T423e/tests/run/self_entry_placeholder/qa_self_entry_seams.ax` only and ran `python tools/axtest.py --compiler build/axiomc2.exe --no-cache -j 2 --filter run/self_entry_placeholder/qa_self_entry_seams`:
  - Mutated run: `MUT_EXIT= 1`, `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, and `native-O1` all failed with `stdout differs at byte 66`).
  - Restored run: `RESTORE_EXIT= 0`, `TOTAL 3 PASS 3 FAIL 0`.

### 5. Per-task gate (`tools/taskgate.py`)
Command (inside `build-snap-T423e/`):
`python tools/taskgate.py --task T423e --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423e.json`

- root `D:/projects/compiler/new lang/build-snap-T423e`, HEAD `2dbbd763dcc4`, compiler `D:/projects/compiler/new lang/build-snap-T423e/build/axiomc2.exe`, `-j 2`
- change set: 135 file(s) (working tree of `build-snap-T423e` vs HEAD, incl. 12 regenerated selfhost bundles that changed)
- wall time: 1591.0 s (axtest 1576.6 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 142 | 385 | 375 | 0 | 4 | 6 | 0 |
| affected | 415 | 852 | 836 | 0 | 16 | 0 | 0 |
| smoke | 33 | 56 | 56 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 460 | 926 | 904 | 0 | 16 | 6 | 0 |

Counts per group: `build_native` (1), `conformance` (38), `diff` (2), `driver` (18), `encode` (2), `fuzz` (1), `hir` (1), `inspect` (1), `lex` (1), `link` (1), `link2` (1), `lir` (56), `mc` (47), `mir` (9), `modules` (6), `obj` (1), `opt` (1), `opt2` (1), `parse` (1), `perf` (6), `programs` (1), `resolve` (1), `run` (59), `selfhost` (68), `std` (107), `tools` (1), `typeck` (6), `ui` (20), `unit` (1), `verify` (1) — **0 failing in every group**.
- `unmatched changed files: none`
- `WEAK-NATIVE: 13 in the run; 0 in the task's own/changed tests`
- `Baseline: BASELINE OK`, `Failing ids: none`
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 22 s`
- `TASKGATE T423e exit=0`

### 6. Harness & change-set hygiene
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423e`: exit 0, 0 `REFUSED` lines.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
none

## Files changed
- tests/run/self_entry_placeholder/qa_self_entry_seams.ax

VERDICT: PASS round=0
