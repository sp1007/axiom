# T166 report — AX0-FIX-11: branch-fixup capacity in the axiom0 native emitter

## Summary
Fixed the per-function fixed-capacity branch-fixup and basic-block offset arrays in the frozen Stage-0 native emitter (`bootstrap/axiom0/src/driver/build_native/build.c`, `SPEC-00-bootstrap.md` §1/§6, `SPEC-20-selfhost.md` §6/§7) and audited every fixed-size array/buffer in `bootstrap/axiom0/src/driver/build_native/`:

1. **Dynamic `bb_offsets` and `fixups` with bounds check (`build.c`)**:
   - Replaced `uint32_t bb_offsets[1024]` and `struct { uint32_t fixup; uint32_t target; } fixups[1024]` with heap-allocated arrays (`ax_xcalloc` sized to `mi_body->bb_count` for `bb_offsets` and pre-counted `AX_X64_MI_JMP`/`AX_X64_MI_JCC`/`AX_X64_MI_ASSERT` capacity + `ax_grow_array` fallback for `fixups`).
   - Added explicit range validation on every branch target (`fixups[i].target < bb_count`) and patch offset (`fixups[i].fixup + 4 <= text_sec->bytes_len`) before patching `rel32`. Out-of-range targets or offsets now free the buffers and abort via `AX_ICE(...)` rather than silently patching or corrupting stack memory.
   - Freed `bb_offsets` and `fixups` on every exit path.
2. **Eliminated fixed-buffer truncation hazards in `build.c`**:
   - Replaced `char name_buf[256]`, `char formatted_msg[256]`, and `char obj_path[1024]` with exact-sized `ax_xmalloc` allocations freed after use so long mangled symbol names, panic messages, or output paths can never silently truncate.
3. **Regression and stress tests**:
   - Added `tests/run/parity/backend/many_branch_fixups.ax` (1,500 grouped `if`s across 15 `if x >= g` groups: 5,160 machine basic blocks, 6,070 `JMP`/`JCC` instructions, 6,370 total branch fixups; verifies stdout `1125750\n` and exit code `42`).
   - Added `tests/build_native/gen_stress_4096_jumps.py` and `tests/build_native/stress_4096_jumps.ax` (1,600 grouped `if`s across 16 `if x >= g` groups: 5,263 machine basic blocks, 6,474 `JMP`/`JCC` instructions, 6,674 total branch fixups; verifies stdout `1280800\n` and exit code `77`).
4. **Baseline update**:
   - Removed `selfhost/obj_link_driver/axiomc_e2e.test` (`T491`) from `_workspaces/baseline-failures.txt` after verifying that it passes with the rebuilt `axiom0` / `axiomc1` / `axiomc2`.

## Audit of Fixed-Capacity Arrays and Buffers in `bootstrap/axiom0/src/driver/build_native/`

| File & Line | Declaration / Buffer | Verdict & Rationale |
|---|---|---|
| `build.c:167` | `(const uint8_t[]){0xE8, 0, 0, 0, 0}` (5 bytes) | **Bounded by construction** — exact 5-byte x86-64 `call rel32` instruction encoding template. |
| `build.c:219, 230, 242` | `char *name = malloc(sv.len + 32)` for `".Lconst_%u_%.*s"` | **Bounded by construction** — dynamically sized to `sv.len + 32`; prefix `".Lconst_"` (8) + `uint32_t` (≤ 10) + `"_"` (1) + NUL (1) = 20 ≤ 32 bytes. |
| `build.c:253` | `char *name = malloc(32)` for `".Lconst_%u"` | **Bounded by construction** — `".Lconst_"` (8) + `uint32_t` (≤ 10) + NUL (1) = 19 ≤ 32 bytes. |
| `build.c:406` | `char cstr_name[64]` for `".Lcstr_%d"` | **Bounded by construction** — `".Lcstr_"` (7) + `int` (≤ 11 chars) + NUL (1) = 19 ≤ 64 bytes. |
| `build.c:504` | `char name_buf[256]` for function symbol name | **Fixed in this task** — replaced with `ax_xmalloc(name.len + 1)` for mangled names (and `ax_xmalloc(32)` for `"__ax_fn_%u"`), preventing silent symbol-name truncation on names ≥ 256 bytes. |
| `build.c:515` | `uint32_t bb_offsets[1024]` | **Fixed in this task** — replaced with `ax_xcalloc(bb_count ? bb_count : 1, sizeof(uint32_t))` where `bb_count = mi_body->bb_count`, freed after patching. |
| `build.c:516` | `struct { uint32_t fixup; uint32_t target; } fixups[1024]` | **Fixed in this task** — replaced with `ax_xcalloc(fixup_cap ? fixup_cap : 1, sizeof(AxBranchFixup))` (exact pre-counted capacity + `ax_grow_array` fallback), checked against `bb_count` and `text_sec->bytes_len` via `AX_ICE`, and freed after patching. |
| `build.c:563` | `char formatted_msg[256]` for `"panic: %s\n"` | **Fixed in this task** — replaced with `ax_xmalloc(strlen(msg) + 10)` and freed after emitting into `.rdata`, preventing silent truncation of panic messages > 247 bytes. |
| `build.c:569` & `data_syms.c:43` | `char panic_sym_name[64]` for `".Lpanic.%u"` | **Bounded by construction** — `".Lpanic."` (8) + `uint32_t` (≤ 10) + NUL (1) = 19 ≤ 64 bytes. |
| `build.c:576, 578, 579` | `(const uint8_t[]){...}` (4, 4, 5 bytes) | **Bounded by construction** — fixed x86-64 machine instruction operand/call encoding templates (`disp32`, `imm32`, `call rel32`). |
| `build.c:623` | `char obj_path[1024]` for `"%s.obj"` | **Fixed in this task** — replaced with `ax_xmalloc(strlen(ax_opt_build_o) + 5)` and freed on all return paths, preventing path truncation on output paths ≥ 1020 bytes. |
| `build.c:639` | `const char *inputs[] = { obj_path }` (1 element) | **Bounded by construction** — 1-element array passed with literal `count = 1` to `ax_pe_link`. |
| `data_syms.c:21` | `char sym_name[64]` for `".Lstr.%u.%u"` | **Bounded by construction** — `".Lstr."` (6) + `uint32_t` (≤ 10) + `"."` (1) + `uint32_t` (≤ 10) + NUL (1) = 28 ≤ 64 bytes. |

## Files changed
- _workspaces/baseline-failures.txt
- bootstrap/axiom0/src/driver/build_native/build.c
- tests/build_native/gen_stress_4096_jumps.py
- tests/build_native/stress_4096_jumps.ax
- tests/run/parity/backend/many_branch_fixups.ax

## Tests
1. **Failure observed first on unfixed `axiom0`**:
   - Built unfixed `axiom0.exe` at HEAD `1752d89a94bd` and ran `python tools/axtest.py --compiler <unfixed-axiom0.exe> --no-cache --verbose --filter run/parity/backend/many_branch_fixups.ax`:
     - `PASS run/parity/backend/many_branch_fixups.ax [interp]`
     - `CRASH run/parity/backend/many_branch_fixups.ax [native]: axiom0 build died with status 3221225477` (`0xC0000005`)
     - `CRASH run/parity/backend/many_branch_fixups.ax [native-O1]: axiom0 build died with status 3221225477` (`0xC0000005`)
2. **Regression & stress tests on fixed `axiom0` and `axiomc2`**:
   - `python tools/axtest.py --root build-snap-T166 --compiler build-snap-T166/build/axiom0.exe --no-cache --verbose -j 2 --filter many_branch_fixups` -> `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
   - `python tools/axtest.py --root build-snap-T166 --compiler build-snap-T166/build/axiom0.exe --no-cache --verbose -j 2 --filter stress_4096_jumps` -> `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
   - `python tools/axtest.py --root build-snap-T166 --compiler build-snap-T166/build/axiomc2.exe --no-cache --verbose -j 2 --filter many_branch_fixups` -> `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
   - `python tools/axtest.py --root build-snap-T166 --compiler build-snap-T166/build/axiomc2.exe --no-cache --verbose -j 2 --filter stress_4096_jumps` -> `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1`; `WEAK-NATIVE 0`).
3. **Stage 1–3 bootstrap fixed point (`tools/build_axiomc.py --out build-snap-T166/build --stage 3 --force`)**:
   - `STAGE1 OK`: `build-snap-T166/build/axiomc1.exe` (`26,334,720` bytes, `sha256 = 6a9c2eb776b36fd2...`, `wall = 59.64s`)
   - `STAGE2 (O1) OK`: `build-snap-T166/build/dir_stage2_O1/axiomc2.exe` (`8,142,848` bytes, `sha256 = fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`)
   - `STAGE3 (O1) OK`: `build-snap-T166/build/dir_stage3_O1/axiomc3.exe` (`8,142,848` bytes, `sha256 = fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`)
   - `FIXED-POINT (O1) OK: sha256(axiomc2_O1) == sha256(axiomc3_O1) == fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`
4. **Rebuilt `axiomc1` verification (`axiomc_e2e.test` and previously crashing programs)**:
   - `python tools/axtest.py --root build-snap-T166 --compiler build-snap-T166/build/axiomc2.exe --build-dir build-snap-T166/build --no-cache --verbose -j 2 --filter selfhost/obj_link_driver/axiomc_e2e.test` -> `PASS selfhost/obj_link_driver/axiomc_e2e.test`, `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`.
   - Verified `axiomc1 inspect --emit=thir` and `axiomc1 build` against `axiomc2` on:
     - `tests/run/comptime/scalar_const.ax`: `thir` byte-identical (`sha256 = E799926B8768C47B...`), `.exe` byte-identical (`sha256 = 4C308FF6AB3FAAD1...`), both exit `91`.
     - `tests/run/parity/backend/const_table_str.ax`: `thir` byte-identical (`sha256 = 3F7D337BD8B263C2...`), `.exe` byte-identical (`sha256 = F55277D6631C4282...`), both exit `0` with identical stdout.
     - `tests/run/parity/backend/qa_narrow_const_repeat_and_print_int_edges.ax`: `thir` byte-identical (`sha256 = 9BF8552AA8292850...`), `.exe` byte-identical (`sha256 = 63286E8075ADBE1A...`), both exit `0` with identical stdout.
5. **Byte-identical output spot-check (`axiom0` unfixed vs fixed)**:
   - Spot-checked 36 `tests/run/**` programs (144 builds: `--emit=obj` and `.exe` at `-O0` and `-O1`): **144/144 builds 100% byte-identical**.
   - Spot-checked the full stage-1 `axiomc` bundle object (`28,281,885` bytes at `-O0`, `28,200,826` bytes at `-O1`, 3,625 functions): `.rdata` (`299,872` bytes), all COFF relocations, the symbol table, the string table, and **3,624/3,625 `.text` functions are 100% byte-identical**; the sole changed function is `exec_assign_binop` (1,076 branch fixups, 11 differing bytes where the overflowing fixups previously corrupted `bb_offsets[]`).
6. **Per-task gate, unit tests, and harness checks**:
   - `python tools/taskgate.py --task T166 --root build-snap-T166 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`: `TOTAL 58 PASS 58 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `archcheck: clean (exit 0)`, `TASKGATE T166 exit=0`.
   - `build-snap-T166/build/axiom0-unit.exe`: `UNIT 71 tests, 0 failed`.
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

## Spec deviations
none

## Follow-ups
- Add a `pool build_native: build_native/stress_4096_jumps.ax` entry to `tests/smoke.list` once a task with `tests/smoke.list` in `paths:`/`locks:` runs.

STATUS: COMPLETE round=0
