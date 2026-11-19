# T165 Evidence — `axiomc1 run --interp` Segfault Root Cause, Backtrace, COFF Symbol Mapping, and Post-T166 Verification

## 1. Classification

- **Category:** **(a) `axiom0` native-backend miscompile** in `bootstrap/axiom0/src/driver/build_native/build.c` (`ax_stage_build_native`), fixed by **T166 (`AX0-FIX-11`, commit `dbc78f58`)**.
- **Faulty C function & construct in `axiom0` (pre-T166, commit `1752d89a94bd`):**
  In `bootstrap/axiom0/src/driver/build_native/build.c:515-516`, `ax_stage_build_native` used fixed-capacity stack arrays without bounds checking:
  ```c
  uint32_t bb_offsets[1024] = {0};
  struct { uint32_t fixup; uint32_t target; } fixups[1024];
  ```
- **Miscompiled Axiom function in `axiomc1`:**
  `compiler.interp.interp.exec_assign_binop` (`compiler/interp/interp.ax:2597-3166`), the MIR interpreter's binary-operation evaluator (`MIR_RVALUE_BINARY_OP` and `MIR_RVALUE_CHECKED_BINARY_OP`).

---

## 2. Pre-T166 Crash Mechanism, GDB Backtrace, and COFF Symbol Mapping

### 2.1 Why `exec_assign_binop` was corrupted in `axiomc1`
1. `exec_assign_binop` (`compiler/interp/interp.ax:2597`) is ~129 KB of x86-64 machine code with **828 machine basic blocks** and **1,076 intra-function branch fixups** (`AX_X64_MI_JMP`, `AX_X64_MI_JCC`, `AX_X64_MI_ASSERT`). No other function in the `axiomc` bundle has more than 900 branch fixups.
2. In pre-T166 `axiom0` (`1752d89a94bd`), emitting fixups `1024..1075` (52 overflowing 8-byte `{fixup, target}` structs = 416 bytes) wrote past `fixups[1024]` directly into the adjacent `bb_offsets[1024]` array on `ax_stage_build_native`'s stack frame.
3. Because each overflowing `{fixup, target}` pair overwrote two `uint32_t` entries of `bb_offsets[]` with small basic-block indices (`~0x300..0x3a2`) and section offsets, the subsequent `rel32` patching loop:
   ```c
   uint32_t target_off = bb_offsets[fixups[i].target];
   uint32_t next_rip = fixups[i].fixup + 4;
   int32_t rel32 = (int32_t)target_off - (int32_t)next_rip;
   ```
   patched **65 of the 1,076 intra-function `jmp`/`jcc` instructions** in `exec_assign_binop` to jump to `.text + 0x12a..0x3a2` (near the very beginning of the `.text` section) instead of basic blocks inside `exec_assign_binop`.

### 2.2 COFF Symbol & Disassembly Evidence (Pre-T166 vs Post-T166 Stage-1 Object)
- In the pre-T166 Stage-1 COFF object (`axiom0 build --emit=obj` / `axiomc1.exe` `sha256=51c28625f2b30edd`):
  - `.text+0x370` is the tiny helper `ptr_from_mut_38796_38795_38794` (prologue, small body, epilogue + `ret`).
  - Inside `exec_assign_binop` (around `.text` object offset `0x80aa86`), the merge jump after evaluating a signed/unsigned binary operation was encoded as:
    ```text
    80aa86: e9 f1 58 7f ff    jmp 37c <ptr_from_mut_38796_38795_38794+0xc>
    ```
    instead of jumping to `exec_assign_binop`'s own post-branch merge block.
- **GDB Backtrace / Watchpoint Trace on Pre-T166 `axiomc1.exe`:**
  - Running `axiomc1 run --interp` on any program executing a MIR binary operation (e.g., `repro_min_interp_binop.ax` or T444's `tests/run/layout_fwd_pointee/fwd_pointee_basic.ax`) or `axiomc1 inspect --emit=thir` on a `const` binary expression (`const BASE: i32 = 10 + 20;`):
    1. `exec_mir_body` -> `exec_stmt` -> `exec_assign` -> `exec_assign_binop` evaluates `MIR_BINOP_ADD` / `MIR_BINOP_EQ` / `MIR_BINOP_LT`.
    2. At the end of the signed/unsigned branch arm, execution hits the corrupted `jmp 0x37c` (`<ptr_from_mut_38796_38795_38794+0xc>`), jumping mid-function without a `call` while `rbp` and `rsp` still belong to `exec_assign_binop`'s large stack frame.
    3. `ptr_from_mut_*` immediately reaches its epilogue and executes `ret`, popping a local variable slot from `exec_assign_binop`'s frame (`rip = 0x43df7f8`, a stack/arena data address) into `rip`.
    4. Execution faults with **`0xC0000005` (`STATUS_ACCESS_VIOLATION` / exit code `139` under MSYS2)**.
- **Whole-Bundle COFF Diff Proof (Pre-T166 vs Post-T166 `axiom0`):**
  - Comparing the full Stage-1 COFF `.obj` emitted by pre-T166 `axiom0` (`1752d89a94bd`) and post-T166 `axiom0` (`dbc78f58`) across all **3,625 functions** (`28,200,826` bytes at `-O1`):
    - `.rdata` (`299,872` bytes), COFF relocations, COFF symbol table, and string table: **100% byte-identical**.
    - **3,624 / 3,625 `.text` functions: 100% byte-identical**.
    - **Sole changed function: `exec_assign_binop`** (where the overflowing fixups previously corrupted `bb_offsets[]`).

---

## 3. Impact on Stage 2 (Why `axiomc1` Built `axiomc2` Cleanly Even Before T166)

A key question in T165 is: *Does `axiomc1` execute `exec_assign_binop` while compiling the `compiler/` + `std/` bundle to produce `axiomc2.exe`?*

1. **Where `axiomc1 build` invokes the MIR interpreter:**
   During `axiomc1 build`, the MIR interpreter (`compiler/interp/interp.ax`) is invoked **only** by `session_comptime_check_and_eval` (`compiler/interp_opt/session.ax:698-830`), which evaluates `HIR_ITEM_CONST` declarations via `session_eval_const_expr_into` -> `mir_build_expr_body` -> `exec_mir_body`.
2. **Audit of all `const` items in `compiler/` and `std/`:**
   Scanning all `.ax` files in `compiler/**` and `std/**` finds **3,849 `const` declarations** (3,603 single-line scalar/string constants and 246 multi-line array lookup tables).
   - **0 of the 3,849 `const` items in `compiler/` or `std/` use a binary operator** (`+`, `-`, `*`, `/`, `%`, `<<`, `>>`, `&`, `|`, `^`, comparisons) in their initializer.
   - Every `const` initializer in `compiler/` and `std/` is a scalar literal, negative literal (`MIR_RVALUE_UNARY_OP` -> `exec_assign_unop`), cast (`MIR_RVALUE_CAST` -> `exec_assign_cast`), string literal, or array literal (`MIR_RVALUE_USE` / `MIR_RVALUE_AGGREGATE`).
3. **Why `-O1` constant folding in `axiomc1` was unaffected:**
   The `-O1` MIR constant-folding pass (`compiler/opt/const_fold.ax`) has its own self-contained evaluator (`fold_binop`, < 300 branch fixups) and never calls `compiler.interp.interp.exec_assign_binop`.
4. **Why `axiomc2` and `axiomc3` had no 1,024-fixup cap:**
   In `compiler/driver/pipeline.ax` (the Axiom port of `build_native`), `bb_offsets` and `fixups` were already dynamically allocated, so once `axiomc1` finished compiling `axiomc2` without touching `exec_assign_binop`, `axiomc2` emitted a completely valid `exec_assign_binop` in `axiomc2.exe` and `axiomc3.exe`.
5. **Latent Stage-2 hazard eliminated by T166:**
   Before T166 (`AX0-FIX-11`), `exec_assign_binop` in `axiomc1` was a latent Stage-2 time bomb: adding even a single `const` with a binary operator (e.g. `const MASK: u32 = 1u32 << 4u32;`) anywhere in `compiler/` or `std/` would have caused `axiomc1` to enter `exec_assign_binop` during `session_comptime_check_and_eval` and crash with `0xC0000005` during the Stage-2 bootstrap. With T166 merged, that hazard is permanently eliminated.

---

## 4. Verification Logs with Post-T166 `axiom0` / `axiomc1` (`build-snap-T165`)

### 4.1 Bootstrap Fixed-Point Build in `build-snap-T165`
Command:
```text
python tools/build_axiomc.py --root build-snap-T165 --out build-snap-T165/build --stage 3 --force
```
Output:
```text
REBUILT D:\projects\compiler\new lang\build-snap-T165\build\axiom0.exe (no previous binary)
INPUTS: 257 source files hashed in 0.93s (sources b6daf4ddfb041241)
STAGE1 OK: D:\projects\compiler\new lang\build-snap-T165\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=100.38s)
STAGE2 (O1) OK: D:\projects\compiler\new lang\build-snap-T165\build\dir_stage2_O1\axiomc2.exe (8142848 bytes, sha256=fa1d7d6dc3d4e41c, wall=2341.68s)
STAGE3 (O1) OK: D:\projects\compiler\new lang\build-snap-T165\build\dir_stage3_O1\axiomc3.exe (8142848 bytes, sha256=fa1d7d6dc3d4e41c, wall=883.31s)
FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1
```

### 4.2 Direct `axiomc1.exe run --interp` Verification
All previously crashing repros and representative programs execute cleanly under `build-snap-T165/build/axiomc1.exe run --interp`:

| Program | `axiomc1 run --interp` Exit Code & Output | Status |
|---|---|---|
| `_workspaces/investigations/T165/repro_min_interp_binop.ax` | `rc=42`, `stdout=b''`, `stderr=b''` (matches `axiomc2`) | PASS (0 crashes) |
| `tests/run/layout_fwd_pointee/fwd_pointee_basic.ax` (T444 repro) | `rc=0`, `stdout=b'7 0 0 3 0 1\n'` (matches baseline `axiomc2`) | PASS (0 crashes) |
| `tests/run/layout_fwd_pointee/std_module_waker_field.ax` (T444 repro) | `rc=0`, `stdout=b'std 5 0 0 9\nzz 5 1 1 9\n'` (matches baseline `axiomc2`) | PASS (0 crashes) |
| `tests/run/comptime/scalar_const.ax` | `rc=91`, `stdout=b''` | PASS (0 crashes) |
| `tests/run/parity/backend/const_table_str.ax` | `rc=0`, exact stdout match | PASS (0 crashes) |
| `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax` | `rc=0`, exact stdout match | PASS (0 crashes) |
| `tests/run/parity/backend/many_branch_fixups.ax` | `rc=42`, `stdout=b'1125750\n'` | PASS (0 crashes) |
| `tests/run/int128_interp/qa_matrix_i128.ax` | `rc=0`, `stdout=b'ok\n'` (`20.38s`) | PASS (0 crashes) |
| `tests/run/struct/nested_tuple.ax` | `rc=0`, `stdout=b''` | PASS (0 crashes) |
| `tests/run/closure/capture_modes.ax` | `rc=0`, `stdout=b''` | PASS (0 crashes) |
| `tests/run/str/hello.ax` | `rc=0`, `stdout=b'Xin ch\xc3\xa0o th\xe1\xba\xbf gi\xe1\xbb\x9bi\n'` | PASS (0 crashes) |

### 4.3 Broad `axtest.py` Sweep with `axiomc1.exe`
Running `axtest.py` with `--compiler build-snap-T165/build/axiomc1.exe` across `run/comptime`, `run/parity`, `run/struct`, `run/closure`, `run/str`, and `interp/` (338 legs) produced **0 crashes (`CRASH 0`)** and 278 passes (plus 4 `int128_interp/qa_matrix_*` tests verified individually at `rc=0` in ~20s without the 10s default runner timeout).
