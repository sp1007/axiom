# T165 report — Investigate: `axiomc1` `run --interp` segfault

## Summary
Investigated the `axiomc1` (Stage-1 compiler built by `axiom0`) `run --interp` access violation reported in T444 ("other findings", `ADR-0043` §4, `SPEC-20-selfhost.md` §5–§7):

1. **Classification — (a) `axiom0` native-backend miscompile (resolved by T166 `AX0-FIX-11`, commit `dbc78f58`):**
   - **Faulty C function & construct in `axiom0`:** `ax_stage_build_native` in `bootstrap/axiom0/src/driver/build_native/build.c:515-516` (pre-T166, commit `1752d89a94bd`) declared fixed-capacity per-function stack buffers without bounds checks:
     ```c
     uint32_t bb_offsets[1024] = {0};
     struct { uint32_t fixup; uint32_t target; } fixups[1024];
     ```
   - **Miscompiled Axiom function in `axiomc1`:** `compiler.interp.interp.exec_assign_binop` (`compiler/interp/interp.ax:2597-3166`, ~129 KB of x86-64 machine code, **828 machine basic blocks**, **1,076 intra-function branch fixups** — the only function in `axiomc` exceeding 1,024 branch fixups).
   - **Crash mechanism:** Emitting fixups `1024..1075` (52 overflowing 8-byte `{fixup, target}` records = 416 bytes) overflowed `fixups[1024]` into the adjacent `bb_offsets[1024]` array on `ax_stage_build_native`'s stack, overwriting `bb_offsets` entries with basic-block indices (`~0x300..0x3a2`). The subsequent `rel32` patching loop patched **65 of the 1,076 intra-function `jmp`/`jcc` instructions** in `exec_assign_binop` to jump to `.text+0x12a..0x3a2` (inside `ptr_from_mut_38796_38795_38794` at `.text+0x370`, e.g. `80aa86: e9 f1 58 7f ff  jmp 37c <ptr_from_mut_38796_38795_38794+0xc>`) instead of `exec_assign_binop`'s own merge basic blocks. Whenever `axiomc1` executed a binary operation in the MIR interpreter (`axiomc1 run --interp` on any program with arithmetic/comparisons, or `const` evaluation of a binary operator), execution jumped mid-frame into `ptr_from_mut_*`, executed its `ret` on `exec_assign_binop`'s stack frame, and faulted with `0xC0000005` (`STATUS_ACCESS_VIOLATION` / exit `139`).
   - **Whole-bundle COFF diff proof:** Comparing the Stage-1 COFF `.obj` emitted by pre-T166 `axiom0` (`1752d89a94bd`) and post-T166 `axiom0` (`dbc78f58`) across all **3,625 functions** (`28,200,826` bytes at `-O1`) confirms that `.rdata`, COFF relocations, symbols, string table, and **3,624 / 3,625 `.text` functions are 100% byte-identical**; `exec_assign_binop` is the sole changed function.

2. **Impact on Stage 2 (`axiomc1` compiling `axiomc2`):**
   - During `axiomc1 build`, the MIR interpreter (`compiler/interp/interp.ax`) is invoked **only** by `session_comptime_check_and_eval` (`compiler/interp_opt/session.ax:698-830`), which evaluates `HIR_ITEM_CONST` initializers via `session_eval_const_expr_into` -> `mir_build_expr_body` -> `exec_mir_body`.
   - An exhaustive scan of all **3,849 `const` items** across `compiler/**/*.ax` and `std/**/*.ax` (3,603 single-line scalar/string constants + 246 multi-line array tables) shows that **0 of the 3,849 `const` initializers contain a binary operator** (`+`, `-`, `*`, `/`, `%`, `<<`, `>>`, `&`, `|`, `^`, comparisons). Every `const` item in `compiler/` and `std/` lowers to `MIR_RVALUE_USE`, `MIR_RVALUE_AGGREGATE`, `MIR_RVALUE_UNARY_OP` (`exec_assign_unop`), or `MIR_RVALUE_CAST` (`exec_assign_cast`).
   - Furthermore, the `-O1` MIR constant-folding pass (`compiler/opt/const_fold.ax`) uses its own self-contained `fold_binop` helper (< 300 branch fixups) rather than calling `compiler/interp/interp.ax`.
   - Therefore, pre-T166 `axiomc1` **never executed `exec_assign_binop` while compiling `compiler/main.ax` into `axiomc2.exe`**, and `axiomc`'s own native emitter in `compiler/driver/pipeline.ax` already used dynamically sized buffers (no 1,024-fixup limit), so `axiomc2.exe` and `axiomc3.exe` were completely uncorrupted.
   - However, prior to T166, `exec_assign_binop` in `axiomc1` was a latent Stage-2 bootstrap hazard: adding any `const` item with a binary expression (such as `const MASK: u32 = 1u32 << 4u32;`) to `compiler/` or `std/` would have crashed `axiomc1` during Stage 2. T166 (`AX0-FIX-11`) permanently eliminated this hazard.

3. **Verification with Post-T166 `axiom0` (`dbc78f58` / HEAD `eca6645`):**
   - Rebuilt `axiom0.exe`, `axiomc1.exe` (`sha256=6a9c2eb776b36fd2...`), `axiomc2.exe`, and `axiomc3.exe` (`sha256=fa1d7d6dc3d4e41c...`, Stage-2/3 fixed point verified) in `build-snap-T165/build`.
   - Verified that `axiomc1.exe run --interp` passes with **0 crashes** on `_workspaces/investigations/T165/repro_min_interp_binop.ax` (`rc=42`), the T444 repros (`tests/run/layout_fwd_pointee/fwd_pointee_basic.ax`, `std_module_waker_field.ax`), `tests/run/comptime/scalar_const.ax` (`rc=91`), `tests/run/parity/backend/const_table_str.ax`, `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax`, `tests/run/parity/backend/many_branch_fixups.ax` (`rc=42`), `tests/run/int128_interp/qa_matrix_i128.ax` (`rc=0`), and a broad `axtest.py` sweep across `run/comptime`, `run/parity`, `run/struct`, `run/closure`, `run/str`, and `interp/`.

4. **Proposed Follow-up Task:**
   - **None required.** The underlying `axiom0` branch-fixup overflow (`bb_offsets[1024]` / `fixups[1024]`) and all other fixed-size buffers in `bootstrap/axiom0/src/driver/build_native/` were already fixed and regression-tested in **T166 (`AX0-FIX-11`)**.

## Files changed
- _workspaces/investigations/T165/evidence_backtrace_and_coff_symbols.md
- _workspaces/investigations/T165/repro_min_interp_binop.ax

## Tests
1. **Stage 0–3 bootstrap fixed-point rebuild in `build-snap-T165`**:
   - `python tools/build_axiomc.py --root build-snap-T165 --out build-snap-T165/build --stage 3 --force`:
     - `STAGE1 OK`: `build-snap-T165/build/axiomc1.exe` (`26,334,720` bytes, `sha256=6a9c2eb776b36fd2...`)
     - `STAGE2 (O1) OK`: `build-snap-T165/build/dir_stage2_O1/axiomc2.exe` (`8,142,848` bytes, `sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`)
     - `STAGE3 (O1) OK`: `build-snap-T165/build/dir_stage3_O1/axiomc3.exe` (`8,142,848` bytes, `sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`)
     - `FIXED-POINT (O1) OK`
2. **Direct `axiomc1.exe run --interp` verification**:
   - `_workspaces/investigations/T165/repro_min_interp_binop.ax`: `rc=42` (matches `axiomc2.exe`).
   - `tests/run/layout_fwd_pointee/fwd_pointee_basic.ax` & `std_module_waker_field.ax` (T444 repros): `rc=0`, identical stdout to `axiomc2.exe`, 0 crashes.
   - `tests/run/comptime/scalar_const.ax` (`rc=91`), `tests/run/parity/backend/const_table_str.ax` (`rc=0`), `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax` (`rc=0`), `tests/run/parity/backend/many_branch_fixups.ax` (`rc=42`), `tests/run/int128_interp/qa_matrix_i128.ax` (`rc=0`), `tests/run/struct/nested_tuple.ax` (`rc=0`), `tests/run/closure/capture_modes.ax` (`rc=0`), `tests/run/str/hello.ax` (`rc=0`).
3. **Broad `axtest.py` sweep with `axiomc1.exe`**:
   - `python tools/axtest.py --root build-snap-T165 --compiler build-snap-T165/build/axiomc1.exe --build-dir build-snap-T165/build --exclude-requires axiom0-internal --no-cache -j 2 --filter run/comptime --filter run/parity --filter run/struct --filter run/closure --filter run/str --filter interp/`: **0 crashes (`CRASH 0`)**, 278 PASS.
4. **Per-task gate (`tools/taskgate.py`)**:
   - `python tools/taskgate.py --task T165 --root build-snap-T165 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: `TOTAL 50 PASS 50 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `archcheck: clean (exit 0)`, `TASKGATE T165 exit=0`.

## Spec deviations
none

## Follow-ups
none (resolved by T166 `AX0-FIX-11`)

STATUS: COMPLETE round=0
