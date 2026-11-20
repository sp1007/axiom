# T820 Report — Fix regression (fullrun-1 / T434): formatter emits synthetic `@derive` `ITEM_IMPL` nodes

## Summary & Root Cause
- **Root cause**: `T434` (`bda3bb63`) updated `parse_synthetic_item()` in `compiler/syntax/parse.ax` so synthetic `@derive(...)` `ITEM_IMPL` nodes are attributed to `source_span.file.v` with a zero-length span (`sp.start == source_span.start`, `sp.end == source_span.start`) rather than `FileId { v: 0u32 }` / `start == 0`.
- `cst_is_synthetic_item()` in `compiler/fmt/cst/mod.ax:535-548` only checked `file_id.v != 0u32 && sp.file.v == 0u32` or `!is_first && k == ITEM_IMPL && sp.start == 0u32`. Because synthetic `@derive(...)` `ITEM_IMPL` items now carry a non-zero `FileId` and non-zero `start` offset, all callers (`compiler/fmt/cst/mod.ax:701`, `compiler/fmt/printer/mod.ax:3102,3118`, `compiler/fmt/verify/mod.ax:1256`) treated them as real items, leaking synthetic `impl` blocks into formatted output and failing exact-match, idempotence, and AST-equivalence checks across:
  1. `run/fmt_engine/fmt_engine.test`
  2. `run/fmt_cli/fmt_cli.test`
  3. `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test`

## Fix
- **`compiler/fmt/cst/mod.ax`**: Updated `cst_is_synthetic_item()` to treat zero-length-span `ITEM_IMPL` nodes (`k == ITEM_IMPL && sp.end <= sp.start`) as synthetic, while retaining the legacy `file_id.v != 0u32 && sp.file.v == 0u32` and `!is_first && k == ITEM_IMPL && sp.start == 0u32` checks. Verified in `compiler/syntax/parse.ax` (`parse_item` / `parse_impl_item`) that every real source `impl` block begins with a non-empty token (`impl`, `unsafe`, or `@`), so `sp.end > sp.start` always holds for real `ITEM_IMPL` nodes (including at byte offset 0). `T434`'s `FileId` attribution in `compiler/syntax/parse.ax` was left untouched.
- **`tools/affected_map.txt`**: Added `tests/run/fmt_engine tests/run/fmt_cli tests/conformance/p19/e19_2_formatter` to the `compiler/syntax` row so future `compiler/syntax/parse.ax` changes automatically trigger formatter suites during `--affected` gates.
- **`tests/run/fmt_cli/fmt_cli_probe.ax.in` & `tests/run/fmt_cli/fmt_cli_oracle.py`**: Added `test_derive_and_real_impl_regression()` (`probe[derive_and_real_impl]`), executed under `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`, testing:
  1. `@derive(Copy, Clone, Eq)` at byte offset 0 alongside a real user `impl Point` block (exact formatted match, AST equivalence, `orig_item_count == fmt_item_count == 2`, idempotence).
  2. `@derive(Copy, PartialEq)` after other top-level items alongside a real user `impl Vec2` block (exact formatted match, AST equivalence, `orig_item_count == fmt_item_count == 4`, idempotence).
  3. Real user `impl Counter` block at byte offset 0 (exact formatted match, AST equivalence, `orig_item_count == fmt_item_count == 1`, idempotence — proving real `impl` blocks at offset 0 are preserved).

## Verification (`build-snap-T820`, `-j 2`)
- **Snapshot**: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T820` → `HEAD 58b4e97 + 5 changed`, `bundles regenerated in build-snap-T820: 36 generator(s), 60 file(s), 36s`.
- **Stage-3 Bootstrap (`python tools/build_axiomc.py --out build --stage 3`)**:
  - `STAGE1 OK`: `axiomc1.exe` (`28,271,104` bytes, `sha256=9991398e59539ceb`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d` (`8,535,040` bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`O1`, incl. `Xin chào thế giới`).
- **Focused `--no-cache` formatter & derive runs (`build/axiomc2.exe`, `-j 2`)**:
  - `--filter fmt_engine`: `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
  - `--filter fmt_cli`: `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (including new `probe[derive_and_real_impl]`)
  - `--filter e19_2_formatter`: `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
  - `--filter parse/derive`: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (confirming `T434` behavior intact)
- **Map check**: `python tools/axtest_affected.py --check-map` → `MAP-CHECK OK` (exit 0).
- **Task gate (`python tools/taskgate.py --task T820 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`)**:
  - Exit `0`: `TOTAL 80 PASS 80 FAIL 0 SKIP 0 XFAIL 0` (own 13/33, affected 13/33, smoke 30/47; dedup 43 ids / 80 results)
  - `BASELINE OK`, `WEAK-NATIVE: 0 in the task's own/changed tests`
  - Tool self-tests: `tools/tests/axtest` PASS (145/145), `tools/tests/taskgate` PASS (44/44)
  - `archcheck`: `229 files scanned, 0 violations` (exit 0)
- **Change set check**: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T820` → exit `0`, `0 REFUSED`.

## Files changed
- compiler/fmt/cst/mod.ax
- tests/run/fmt_cli/fmt_cli_oracle.py
- tests/run/fmt_cli/fmt_cli_probe.ax.in
- tools/affected_map.txt

STATUS: COMPLETE round=0
