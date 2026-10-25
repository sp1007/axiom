# T145 Report — Native-evidence sweep (`tests/run` and `tests/std`)

## Summary

Completed the T145 native-evidence sweep across `tests/run/` and `tests/std/` (86 files modified, all strictly within `paths: [tests/run, tests/std]`):

1. **Eliminated `WEAK-NATIVE` across all five required directory groups (`82 -> 0`)**:
   - `tests/run/numeric`: `8 -> 0` (4 files)
   - `tests/run/drop`: `4 -> 0` (2 files)
   - `tests/run/ptr`: `14 -> 0` (7 files)
   - `tests/run/native_*` (`native_abi`, `native_aggr`, `native_const`, `native_enum`, `native_own`, `native_p7`, `native_ptr`, `native_str`): `46 -> 0` (23 files)
   - `tests/std`: `10 -> 0` (5 files)
2. **Eliminated all unit-`main` (`fn main()`) smoke/assert-only tests without observable output or non-zero exit across all of `tests/run` and `tests/std`**, and converted additional `WEAK-NATIVE` files in `run/cap`, `run/cfg`, `run/comptime`, `run/ffi`, `run/init`, `run/method`, `run/mono`, `run/own`, `run/str`, `run/trait2`, and `run/vars`, reducing overall `WEAK-NATIVE` across `run/ std/` from **278** (139 files) to **124** (62 files).
3. **Audited all `// modes: interp` directives in `tests/run` and `tests/std`**:
   - Removed stale `// modes: interp` from 6 tests that now build and pass natively (`-O0` and `-O1`):
     - `tests/run/basic/t117_panic.ax`
     - `tests/run/basic/t117_qa_neg_i8_min.ax`
     - `tests/run/fn/eval_order_panic1.ax`
     - `tests/run/fn/eval_order_panic2.ax`
     - `tests/std/alloc/qa_sort_interp.ax` (added `@link("kernel32")` `__ax_host_heap_alloc` / `__ax_host_heap_free` shim matching sibling `tests/std/alloc/` tests)
     - `tests/std/arena/qa_arena_scale_interp.ax`
   - Added `// reason: oracle-only check` to the 3 genuinely interpreter-only tests that were missing it (`tests/run/basic/008-step-limit.ax`, `tests/run/basic/009-call-depth.ax`, and `tests/run/host/heap/alloc.ax`, which is paired with `tests/run/host/native_undefined_symbol.test`). All 9 remaining `modes: interp` files in `tests/run` and `tests/std` now carry `// reason: oracle-only check`.
4. **Uncovered a real stage-0 (`axiom0`) compiler bug that was previously masked by unit-`main` early `return;`**:
   - `tests/run/comptime/table_str.ax`, `tests/run/comptime/qa_table_struct_str.ax`, and `tests/run/native_const/qa_table_str_empty_and_multitables.ax` test `const` arrays/structs containing `Str` slices.
   - Before T145, `table_str.ax` and `qa_table_struct_str.ax` had `fn main()` with `if len(KEYWORDS[0]) != 2 { return; }` (returning `()` / exit code `0` on failure!), and `qa_table_str_empty_and_multitables.ax` had `return 0;` without `// exit:` or `// stdout:` (`WEAK-NATIVE`).
   - In `axiom0` (both `--interp` and native `.rdata` emission), `Str` elements inside `const` array/struct tables have `ptr = 0, len = 0`, so `table_str.ax` and `qa_table_struct_str.ax` were silently taking the failure branch on line 1 of `main` and reporting `PASS`! Converting failure branches to non-zero exit codes and pinning the hand-computed results immediately exposed this bug (recorded in `## Follow-ups`).

## Acceptance checklist

- [x] `python build-snap-T145/tools/axtest.py --compiler build-snap-T145/build/axiom0.exe --root build-snap-T145 --verbose -j 2 run/ std/` reports `WEAK-NATIVE 0` for `tests/run/numeric`, `tests/run/drop`, `tests/run/ptr`, `tests/run/native_*`, and `tests/std`; other `tests/run/*` directories reduced from 196 to 124 (total `278 -> 124`), with before/after counts and full remaining weak list below.
- [x] `grep -rln "modes: interp$" tests/run tests/std` lists only files with an `"oracle-only check"` reason comment (9 files total, listed below).
- [x] No unit-`main` `// test: run` test (`fn main()`) without an output (`stdout`/`stdout-file`) or a non-zero pinned `exit` remains under `tests/run` and `tests/std`.
- [x] Full test suite verified in `build-snap-T145`; every failure is documented in `## Follow-ups` with test, observations, and diagnosis.
- [x] Report written to `_workspaces/reports/T145-report.md` with all required sections and final status line.

## Verification

### 1. Required 5 directory groups (`WEAK-NATIVE 0`)

Command:
```
python build-snap-T145/tools/axtest.py --compiler build-snap-T145/build/axiom0.exe --root build-snap-T145 --verbose -j 2 run/numeric/ run/drop/ run/ptr/ run/native_abi/ run/native_aggr/ run/native_const/ run/native_enum/ run/native_own/ run/native_p7/ run/native_ptr/ run/native_str/ std/
```
Output:
```
WEAK-NATIVE 0
TOTAL 1033 PASS 1028 FAIL 5 SKIP 0 XFAIL 0
```
(The 5 FAILs are 3 legs of `run/native_const/qa_table_str_empty_and_multitables.ax` and 2 native legs of `run/native_str/qa_print_int.ax`, both documented in `## Follow-ups`.)

### 2. Before / After `WEAK-NATIVE` counts across `tests/run` and `tests/std`

Command:
```
python build-snap-T145/tools/axtest.py --compiler build-snap-T145/build/axiom0.exe --root build-snap-T145 --verbose -j 2 run/ std/
```
Summary line:
- **Before T145**: `WEAK-NATIVE 278` (`TOTAL 1531 PASS 1521 FAIL 10 SKIP 0 XFAIL 0`)
- **After T145**: `WEAK-NATIVE 124` (`TOTAL 1543 PASS 1524 FAIL 19 SKIP 0 XFAIL 0` — +12 native legs added from removing `modes: interp` on 6 tests, all 12 of which pass!)

| Directory group | Before (`WEAK-NATIVE` legs) | After (`WEAK-NATIVE` legs) | Notes |
|---|---:|---:|---|
| `run/numeric` *(required)* | 8 | **0** | 4 files pinned with hand-computed non-zero `exit` |
| `run/drop` *(required)* | 4 | **0** | 2 files pinned (`stdout` / `exit`) |
| `run/ptr` *(required)* | 14 | **0** | 7 files pinned with hand-computed non-zero `exit` |
| `run/native_abi` *(required)* | 4 | **0** | 2 files pinned with hand-computed non-zero `exit` |
| `run/native_aggr` *(required)* | 2 | **0** | 1 file pinned with `exit: 42` |
| `run/native_const` *(required)* | 6 | **0** | 3 files pinned (`exit` / `stdout`, keeping `table_4kb.ax` `exit: 0` for `objdump_validate.py`) |
| `run/native_enum` *(required)* | 10 | **0** | 5 files pinned with hand-computed non-zero `exit` |
| `run/native_own` *(required)* | 10 | **0** | 5 files pinned (`exit` / `stdout`) |
| `run/native_p7` *(required)* | 4 | **0** | 2 files pinned with hand-computed non-zero `exit` |
| `run/native_ptr` *(required)* | 6 | **0** | 3 files pinned with hand-computed non-zero `exit` |
| `run/native_str` *(required)* | 4 | **0** | 2 files pinned (`exit` / `stdout`) |
| `std` *(required)* | 10 | **0** | 5 files pinned with `stdout` |
| `run/cap` | 4 | **0** | 2 unit-`main` files converted |
| `run/cfg` | 12 | **0** | 6 unit-`main` files converted |
| `run/comptime` | 14 | **0** | 7 unit-`main` files converted |
| `run/ffi` | 8 | **0** | 4 files pinned (`exit` / `stdout`) |
| `run/init` | 2 | **0** | 1 unit-`main` file converted |
| `run/method` | 6 | **0** | 3 unit-`main` files pinned with `stdout` |
| `run/mono` | 2 | **0** | 1 unit-`main` file converted |
| `run/own` | 6 | **0** | 3 unit-`main` files converted |
| `run/str` | 4 | **0** | 2 files pinned (`exit` / `stdout`) |
| `run/trait2` | 18 | **12** | 3 unit-`main` files converted |
| `run/vars` | 8 | **0** | 4 unit-`main` files converted |
| `run/array` | 6 | 6 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/basic` | 10 | 10 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/closure` | 18 | 18 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/enum` | 6 | 6 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/fn` | 6 | 6 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/for` | 8 | 8 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/host` | 10 | 10 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/pattern` | 12 | 12 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/result` | 10 | 10 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/slice` | 16 | 16 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/struct` | 8 | 8 | Multi-check `exit: 0` tests with distinct failure codes |
| `run/trait` | 2 | 2 | Multi-check `exit: 0` test with distinct failure codes |
| **Total** | **278** | **124** | **-154 weak-native legs (-77 files)** |

#### Full list of remaining `WEAK-NATIVE` files in `tests/run` (62 files / 124 legs; 0 in required groups, 0 unit-`main`):
1. `run/array/array_basics.ax`
2. `run/array/array_zero.ax`
3. `run/array/qa_nested_arrays.ax`
4. `run/basic/t117_bitwise.ax`
5. `run/basic/t117_qa_u8_bitwise_not.ax`
6. `run/basic/t117_shifts.ax`
7. `run/basic/t117_unary.ax`
8. `run/basic/t117_width_exact.ax`
9. `run/closure/capture_modes.ax`
10. `run/closure/closure_types.ax`
11. `run/closure/fn_pointers.ax`
12. `run/closure/fn_traits.ax`
13. `run/closure/generic_fns.ax`
14. `run/closure/qa_fn_ptr_args.ax`
15. `run/closure/qa_mixed_captures.ax`
16. `run/closure/qa_move_capture.ax`
17. `run/closure/syntax.ax`
18. `run/enum/exhaustiveness.ax`
19. `run/enum/exhaustiveness_wildcard.ax`
20. `run/enum/run_enum.ax`
21. `run/fn/qa_many_args_edge.ax`
22. `run/fn/qa_unit_implicit_return.ax`
23. `run/fn/unit_fns.ax`
24. `run/for/test_for_array.ax`
25. `run/for/test_for_custom_iter.ax`
26. `run/for/test_for_range.ax`
27. `run/for/test_range_standalone.ax`
28. `run/host/fs/clock.ax`
29. `run/host/fs/dir.ax`
30. `run/host/fs/file_io.ax`
31. `run/host/fs/metadata.ax`
32. `run/host/io/invalid_handle.ax`
33. `run/pattern/enum_struct_if_let.ax`
34. `run/pattern/lexer_interp.ax`
35. `run/pattern/qa_destructure.ax`
36. `run/pattern/qa_let_else.ax`
37. `run/pattern/qa_nested_match.ax`
38. `run/pattern/u8_exhaustive.ax`
39. `run/result/qa_test_try_chained.ax`
40. `run/result/test_let_option.ax`
41. `run/result/test_option.ax`
42. `run/result/test_try_option.ax`
43. `run/result/test_try_result.ax`
44. `run/slice/coerce.ax`
45. `run/slice/disjoint_split.ax`
46. `run/slice/qa_slice_len_empty.ax`
47. `run/slice/qa_slice_mutate.ax`
48. `run/slice/qa_slice_mutate_2.ax`
49. `run/slice/qa_slice_open_ranges.ax`
50. `run/slice/sub_range.ax`
51. `run/slice/sum.ax`
52. `run/struct/nested_tuple.ax`
53. `run/struct/point.ax`
54. `run/struct/qa_win64_hidden_return.ax`
55. `run/struct/simple.ax`
56. `run/trait/dispatch.ax`
57. `run/trait2/test_assoc_items.ax`
58. `run/trait2/test_default_method.ax`
59. `run/trait2/test_default_override.ax`
60. `run/trait2/test_derive.ax`
61. `run/trait2/test_ops.ax`
62. `run/trait2/test_supertraits.ax`

### 3. `modes: interp` audit across `tests/run` and `tests/std`

All 9 remaining files matching `modes: interp$` under `tests/run` and `tests/std` carry `// reason: oracle-only check`:

1. `tests/run/basic/008-step-limit.ax` — `// reason: oracle-only check (interpreter --max-steps flag)`
2. `tests/run/basic/009-call-depth.ax` — `// reason: oracle-only check (interpreter --max-call-depth flag)`
3. `tests/run/ffi/interp_extern_rejected.ax` — `// reason: oracle-only check`
4. `tests/run/host/heap/alloc.ax` — `// reason: oracle-only check (paired with tests/run/host/native_undefined_symbol.test)`
5. `tests/run/host/heap/use_after_free.ax` — `// reason: oracle-only check`
6. `tests/run/ptr/oracle_dangling.ax` — `// reason: oracle-only check`
7. `tests/run/ptr/oracle_misaligned.ax` — `// reason: oracle-only check`
8. `tests/run/ptr/oracle_null.ax` — `// reason: oracle-only check`
9. `tests/run/ptr/oracle_oob.ax` — `// reason: oracle-only check`

### 4. Unit-`main` (`fn main()`) audit across `tests/run` and `tests/std`

Verification script checking every `// test: run` `.ax` file under `tests/run` and `tests/std` for `fn main()` without an output (`stdout`/`stdout-file`/`stderr`/`stderr-contains`) or a non-zero pinned `exit`:
```
unit_run_bad count: 0 []
```
(The only two `fn main()` files without output/non-zero exit under `tests/std` are `tests/std/core/qa_driver_std_discovery.ax` and `tests/std/core/qa_generic_method.ax`, which are `// test: ui` compile-error tests with `// expected-exit: 1`.)

### 5. Liveness mutation proof

On `build-snap-T145/tests/run/comptime/table_u8_256.ax`, mutated `// exit: 126` to `// exit: 125`:
```
FAIL run/comptime/table_u8_256.ax [interp] (15 ms): exit code 126, expected 125; stderr:
FAIL run/comptime/table_u8_256.ax [native] (90 ms): exit code 126, expected 125; stderr:
FAIL run/comptime/table_u8_256.ax [native-O1] (84 ms): exit code 126, expected 125; stderr:
WEAK-NATIVE 0
TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0
```
Restored `// exit: 126`:
```
PASS run/comptime/table_u8_256.ax [interp] (20 ms)
PASS run/comptime/table_u8_256.ax [native] (98 ms)
PASS run/comptime/table_u8_256.ax [native-O1] (84 ms)
WEAK-NATIVE 0
TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0
```

### 6. Architecture check and non-selfhost suites

- `python build-snap-T145/tools/archcheck.py --root build-snap-T145`:
  `archcheck: 192 files scanned, 0 violations`
- Non-selfhost suites (`cli/ conformance/ driver/ hir/ link/ lir/ mc/ mir/ modules/ obj/ opt/ parse/ programs/ resolve/ syntax/ ui/ unit/`):
  All `cli/`, `conformance/`, `driver/`, `hir/`, `link/`, `lir/`, `mc/`, `mir/`, `modules/`, `opt/`, `parse/`, `programs/`, `resolve/`, `syntax/`, `ui/`, and `unit/` tests pass (`899/899 PASS`).

## Follow-ups

### 1. Stage-0 (`axiom0`) comptime `Str`-in-`const`-table evaluation/emission bug (newly exposed by T145 — 3 tests, 9 legs)

- **Failing tests**:
  - `run/comptime/table_str.ax` (`[interp]`, `[native]`, `[native-O1]`): `exit code 1, expected 10`
  - `run/comptime/qa_table_struct_str.ax` (`[interp]`, `[native]`, `[native-O1]`): `exit code 1, expected 118`
  - `run/native_const/qa_table_str_empty_and_multitables.ax` (`[interp]`, `[native]`, `[native-O1]`): `exit code 2, expected 0`
- **Observations**:
  - `table_str.ax` defines `const KEYWORDS: [3]Str = ["fn", "let", "return"];` and checks `if len(KEYWORDS[0]) != 2 { return 1; }`.
  - `qa_table_struct_str.ax` defines `const TABLE: [3]Entry = [Entry { name: "zero", code: 0 }, ...];` and checks `if len(e0.name) != 4 || e0.code != 0 { return 1; }`.
  - `qa_table_str_empty_and_multitables.ax` defines `const STRS: [4]Str = ["", "a", "", "bc"];` and `const ITEMS: [3]Item = [...]` and checks `if len(STRS[1]) != 1 { return 2; }`.
  - Inspecting the COFF `.rdata` section emitted by `axiom0` for `qa_table_struct_str.ax` shows the `i32` fields (`101`, `202`, `303`) are emitted at their struct offsets, while every 16-byte `Str` `(ptr, len)` slot in the `const` array is all zeros (`00 00 ...`). In `--interp`, `len(KEYWORDS[0])` and `len(e0.name)` and `len(STRS[1])` likewise evaluate to `0`.
  - Notably, the self-hosted `axiomc` (`compiler.*` in Axiom) compiles `table_str.ax` (`rc=10`), `qa_table_struct_str.ax` (`rc=118`), and `qa_table_str_empty_and_multitables.ax` (`rc=0`, `stdout: OK\n`) **correctly**!
- **Diagnosis**:
  - Stage-0 `src/` comptime evaluator / MIR const lowering drops `Str` slice values inside aggregate `const` initializers (`[N]Str` and `[N]StructWithStr`), zero-initializing their `(ptr, len)` pairs. Prior to T145, `table_str.ax` and `qa_table_struct_str.ax` were unit-`main` (`fn main()`) with `{ return; }` on failure, so they returned `0` on line 1 of `main` and falsely passed; `qa_table_str_empty_and_multitables.ax` had `return 0;` without `// exit: 0`, so `axtest.py` did not check its exit code (`2`). Per T145 rules, the hand-computed expectations are preserved to keep this bug visible.

### 2. Pre-existing native `print_int` NUL-byte stdout bug (5 tests, 10 native legs)

- **Failing tests**:
  - `run/method/builtins.ax` (`[native]`, `[native-O1]`): expected `5\n15\n` (`35 0a 31 35 0a`), got `\x00\n\x00\x00\n` (`00 0a 00 00 0a`)
  - `run/method/inherent_methods.ax` (`[native]`, `[native-O1]`): expected `30\n40\n40\n44\n44\n`, got `\x00\x00\n` x 5
  - `run/method/qa_run.ax` (`[native]`, `[native-O1]`): expected `42\n` (`34 32 0a`), got `\x00\x00\n` (`00 00 0a`)
  - `run/native_str/qa_print_int.ax` (`[native]`, `[native-O1]`): expected `42` (`34 32`), got `\x00\x00` (`00 00`)
  - `run/str/qa_print_int.ax` (`[native]`, `[native-O1]`): expected `42` (`34 32`), got `\x00\x00` (`00 00`)
- **Observations & Diagnosis**:
  - All 5 tests pass `[interp]` with the exact pinned `// stdout:`. In native codegen (`-O0` and `-O1`), `print_int` writes the correct byte count to stdout, but the digit buffer contains `0x00` bytes instead of ASCII digits. Pinning `// stdout:` removed all 5 files from `WEAK-NATIVE` while keeping the pre-existing native `print_int` failure tracked.

### 3. Out-of-scope `tests/selfhost/` bundle and registry refresh (`paths` outside `[tests/run, tests/std]`)

- **Affected tests in `tests/selfhost/`**:
  - `selfhost/backend/` (`tests/selfhost/backend/qa_backend_diff_lir_b.ax`, `qa_backend_diff_mi_mc_b.ax`) embeds source/LIR/MI/MC snapshots for 10 `tests/run/native_*` files modified in T145 (`tests/run/native_aggr/005-empty-struct.ax`, `tests/run/native_enum/01-simple.ax`..`05-nested-enum.ax`, `tests/run/native_own/{branch_moves,loop_moves,moves,str_moves}.ax`).
  - `selfhost/interp_opt/` (`tests/selfhost/interp_opt/qa_interp_opt_bundle.ax`) embeds source snapshots for 7 `tests/run/comptime/*` files modified in T145.
  - `selfhost/obj_link_driver/axiomc_e2e.test` (`tests/selfhost/obj_link_driver/known_divergent.txt`): because `table_str.ax`, `qa_table_struct_str.ax`, and `qa_table_str_empty_and_multitables.ax` now expose the `axiom0` vs `axiomc` runtime exit-code difference (`same-behaviour` -> `different-behaviour`), and several edited `tests/run/` files need `--update-registry`, regenerating `tests/selfhost/` bundles and `known_divergent.txt` requires a follow-up task with `paths: [tests/selfhost]`.

## Files changed

- `tests/run/basic/008-step-limit.ax` — add `// reason: oracle-only check` for interpreter step-limit test
- `tests/run/basic/009-call-depth.ax` — add `// reason: oracle-only check` for interpreter call-depth test
- `tests/run/basic/t117_panic.ax` — remove stale `// modes: interp` so native panic legs run
- `tests/run/basic/t117_qa_neg_i8_min.ax` — remove stale `// modes: interp` so native overflow-panic legs run
- `tests/run/cap/test_cursor_loop_run.ax` — convert unit `main` to `-> i32` and pin `// exit: 65`
- `tests/run/cap/test_view_run.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/cfg/block_val.ax` — convert unit `main` to `-> i32` and pin `// exit: 25`
- `tests/run/cfg/continue.ax` — convert unit `main` to `-> i32` and pin `// exit: 25`
- `tests/run/cfg/if_expr.ax` — convert unit `main` to `-> i32` and pin `// exit: 30`
- `tests/run/cfg/labeled_loop.ax` — convert unit `main` to `-> i32` and pin `// exit: 4`
- `tests/run/cfg/loop_break.ax` — convert unit `main` to `-> i32` and pin `// exit: 10`
- `tests/run/cfg/never_type.ax` — convert unit `main` to `-> i32` and pin `// exit: 53`
- `tests/run/comptime/array_len.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 53`
- `tests/run/comptime/qa_table_struct_str.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 118`
- `tests/run/comptime/qa_table_u8_loop.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 50`
- `tests/run/comptime/scalar_const.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 128`
- `tests/run/comptime/table_str.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 10`
- `tests/run/comptime/table_struct.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 210`
- `tests/run/comptime/table_u8_256.ax` — convert unit `main` to `-> i32` with distinct failure codes and pin `// exit: 126`
- `tests/run/drop/qa_array_drop.ax` — pin `// stdout: 1\n1\n1\n`
- `tests/run/drop/qa_empty_test.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/ffi/process_id.ax` — pin `// exit: 42` when `GetCurrentProcessId() != 0u32`
- `tests/run/ffi/qa_extern_c_multidll.ax` — pin `// stdout: OK\n` after multi-DLL FFI checks
- `tests/run/ffi/repr_c_struct.ax` — return `pt.x + pt.y` and pin `// exit: 30`
- `tests/run/ffi/tick_count.ax` — pin `// exit: 42` when `GetTickCount64()` is monotonic
- `tests/run/fn/eval_order_panic1.ax` — remove stale `// modes: interp` and pin `// stderr: panic: division by zero\n`
- `tests/run/fn/eval_order_panic2.ax` — remove stale `// modes: interp` and pin `// stderr: panic: division by zero\n`
- `tests/run/host/heap/alloc.ax` — add `// reason: oracle-only check` and pin `// exit: 48`
- `tests/run/init/reinit_after_move.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/method/builtins.ax` — pin `// stdout: 5\n15\n`
- `tests/run/method/inherent_methods.ax` — pin `// stdout: 30\n40\n40\n44\n44\n`
- `tests/run/method/qa_run.ax` — pin `// stdout: 42\n`
- `tests/run/mono/qa_test_basic.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/native_abi/qa_dummy.ax` — return computed struct/slice value and pin `// exit: 73`
- `tests/run/native_abi/qa_edge.ax` — return computed aggregate value and pin `// exit: 111`
- `tests/run/native_aggr/005-empty-struct.ax` — return `42` after empty-struct checks and pin `// exit: 42`
- `tests/run/native_const/identical_tables.ax` — convert unit `main` to `-> i32` and pin `// exit: 100`
- `tests/run/native_const/qa_table_str_empty_and_multitables.ax` — pin `// exit: 0` and `// stdout: OK\n` on success path
- `tests/run/native_const/table_4kb.ax` — pin `// exit: 0` and `// stdout: OK\n` while keeping exit code `0` for `objdump_validate.py`
- `tests/run/native_enum/01-simple.ax` — return sum of `color_to_int` results and pin `// exit: 60`
- `tests/run/native_enum/02-payload.ax` — return `v1 + val` and pin `// exit: 84`
- `tests/run/native_enum/03-nested.ax` — return `30` after state transition checks and pin `// exit: 30`
- `tests/run/native_enum/04-large-payload.ax` — return `st2` and pin `// exit: 42`
- `tests/run/native_enum/05-nested-enum.ax` — return `p2 + p3` and pin `// exit: 33`
- `tests/run/native_own/branch_moves.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/native_own/loop_moves.ax` — convert unit `main` to `-> i32` and pin `// exit: 3`
- `tests/run/native_own/moves.ax` — convert unit `main` to `-> i32` and pin `// exit: 30`
- `tests/run/native_own/qa_dummy.ax` — return `b2.a + b3.a` and pin `// exit: 42`
- `tests/run/native_own/str_moves.ax` — pin `// stdout: b\n` from moved string `z`
- `tests/run/native_p7/qa_closure_capture.ax` — return `r1 + r2 + r3` and pin `// exit: 64`
- `tests/run/native_p7/qa_trait_dispatch.ax` — return `v1 + v2` and pin `// exit: 42`
- `tests/run/native_ptr/overlap_copy.ax` — return verified overlap element sum and pin `// exit: 100`
- `tests/run/native_ptr/qa_mem_edge.ax` — return verified zero-count memory intrinsic result and pin `// exit: 86`
- `tests/run/native_ptr/write_bytes_1mb.ax` — return `buf[0] + buf[524288] + buf[1048575]` and pin `// exit: 231`
- `tests/run/native_str/qa_hello_empty.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/native_str/qa_print_int.ax` — pin `// stdout: 42`
- `tests/run/numeric/cast_char.ax` — return computed char-cast check value and pin `// exit: 44`
- `tests/run/numeric/qa_cast_char_edges.ax` — return computed boundary char-cast value and pin `// exit: 224`
- `tests/run/numeric/qa_char_ordering.ax` — return `42` after char ordering checks and pin `// exit: 42`
- `tests/run/numeric/qa_i8_sign_ext_edge.ax` — return computed `i8` sign-extension value and pin `// exit: 195`
- `tests/run/own/branch_reinit_both.ax` — convert unit `main` to `-> i32` and pin `// exit: 30`
- `tests/run/own/copy_vs_move.ax` — convert unit `main` to `-> i32` and pin `// exit: 32`
- `tests/run/own/reinit.ax` — pin `// stdout: b\n` from reinitialized `Str`
- `tests/run/ptr/arena_align.ax` — return computed arena alignment check value and pin `// exit: 45`
- `tests/run/ptr/drop_in_place.ax` — return `142` after `drop_in_place` checks and pin `// exit: 142`
- `tests/run/ptr/field_write.ax` — return `n.a + (n.b as i32) + (n.c as i32)` and pin `// exit: 141`
- `tests/run/ptr/layout_intrinsics.ax` — return sum of layout sizes/alignments and pin `// exit: 44`
- `tests/run/ptr/linked_list.ax` — return sum of linked-list node values and pin `// exit: 60`
- `tests/run/ptr/mem_intrinsics.ax` — return sum of `copy`/`copy_nonoverlapping` buffer values and pin `// exit: 70`
- `tests/run/ptr/sum_walk.ax` — return `total` (`10+20+30+40+50`) and pin `// exit: 150`
- `tests/run/str/qa_hello_empty.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/str/qa_print_int.ax` — pin `// stdout: 42`
- `tests/run/trait2/test_impl.ax` — convert unit `main` to `-> i32` and pin `// exit: 42`
- `tests/run/trait2/test_mut_view.ax` — convert unit `main` to `-> i32` and pin `// exit: 15`
- `tests/run/trait2/test_struct.ax` — convert unit `main` to `-> i32` and pin `// exit: 30`
- `tests/run/vars/compound.ax` — convert unit `main` to `-> i32` and pin `// exit: 59`
- `tests/run/vars/deferred_init.ax` — convert unit `main` to `-> i32` and pin `// exit: 30`
- `tests/run/vars/let_mut.ax` — convert unit `main` to `-> i32` and pin `// exit: 32`
- `tests/run/vars/shadow.ax` — convert unit `main` to `-> i32` and pin `// exit: 13`
- `tests/std/alloc/qa_heap_ffi.ax` — pin `// stdout: OK HeapFFI\n`
- `tests/std/alloc/qa_sort_interp.ax` — remove stale `// modes: interp` and add `@link("kernel32")` heap shim
- `tests/std/arena/qa_arena_scale_interp.ax` — remove stale `// modes: interp`
- `tests/std/fs/qa_binary_file_buf.ax` — pin `// stdout: OK BinaryFileBuf\n`
- `tests/std/fs/qa_path.ax` — pin `// stdout: OK Path\n`
- `tests/std/fs/qa_time_clock.ax` — pin `// stdout: OK TimeClock\n`
- `tests/std/fs/qa_unicode_paths.ax` — pin `// stdout: OK UnicodePaths\n`

STATUS: COMPLETE round=0
