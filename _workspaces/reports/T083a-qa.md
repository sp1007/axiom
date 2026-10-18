# T083a QA Report — Port MIR interpreter and host oracle to Axiom

## Round 0

### Checks Performed & Evidence

1. **Task report & change-set verification (`taskctl.py changes T083a`)**
   - `_workspaces/reports/T083a-report.md` ends with `STATUS: COMPLETE round=0`.
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083a` exited 0 with 0 `REFUSED` lines; all 12 implementation/test files are within `paths: [compiler/interp, tests/selfhost/interp]`.

2. **Snapshot build (`build-snap-T083a/build`)**
   - Command: `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build` (inside `build-snap-T083a/`)
   - Result: Built 128 targets (`axiom0.exe`, `axiom0-unit.exe`, C driver test binaries) with **0 warnings, 0 errors**.

3. **Architecture & layer check (`archcheck.py`)**
   - Command: `python tools/archcheck.py` (inside `build-snap-T083a/`)
   - Result: `archcheck: 188 files scanned, 0 violations`.
   - Verified `compiler/interp/{mod,value,oracle,frame,interp}.ax` use canonical Axiom syntax (`=` only, `.` paths only) and delegate all host operations through `std.core.host` (no raw `extern "system"` FFI, matching ADR-0002 §6).

4. **Acceptance criteria verification**
   - **Completeness & readability (`compiler/interp/`)**:
     - `compiler/interp/value.ax` (1,067 lines): `InterpValue`, `InterpAlloc`, `InterpHostState`, `MirBodyMap`, `InterpCtx`, synthetic address allocation (`0x10000000` runtime / `0x20000000` comptime), raw pointer validation (`interp_validate_raw_ptr`, `interp_validate_ptr_arith`, `interp_find_synth_addr`, `interp_resolve_synth_ptr`), constant aggregate/string registration, diagnostic/panic/UB/limit reporting (`AX_UNSAFE_INTERP_UB`, `AX_DRIVER_INTERP_STEP_LIMIT`, `AX_DRIVER_INTERP_STACK_LIMIT`, `AX_FFI_NOT_IN_ORACLE`, `AX_CONST_DIV_ZERO`, `AX_CONST_OVERFLOW`, `AX_CONST_EVAL_LIMIT`).
     - `compiler/interp/oracle.ax` (882 lines): Full 21-function `std.core.host` intrinsic oracle (`heap_alloc`, `heap_realloc`, `heap_free`, `stdio`, `open`, `read`, `write`, `close`, `file_size`, `args_count`, `arg`, `env_get`, `exe_path`, `exit`, `remove`, `mkdir`, `metadata`, `dir_open`, `dir_next`, `dir_close`, `monotonic_ns`), file/directory handle lifecycle tracking and cleanup, stdout capture into `DiagBuffer`, and monotonic clock enforcement.
     - `compiler/interp/frame.ax` (639 lines): `CallFrame` lifecycle, `MirBodyMap`, and place projection evaluation (`MIR_PROJ_DEREF`, `MIR_PROJ_FIELD`, `MIR_PROJ_DOWNCAST`, `MIR_PROJ_INDEX`, `MIR_PROJ_SUB_SLICE`) with runtime bounds checking and panics.
     - `compiler/interp/interp.ax` (2,616 lines): 64-bit two's-complement / 16-bit chunked wrapping arithmetic & overflow helpers, all MIR rvalues (`USE`, `REF`, `BINARY_OP`, `OVERFLOWS_BINARY_OP`, `UNARY_OP`, `CAST`, `DISCRIMINANT`, `LEN`, `AGGREGATE`, `REPEAT`), all MIR terminators (`GOTO`, `RETURN`, `SWITCH_INT`, `ASSERT`, `DROP`, `CALL`, `UNREACHABLE`), builtin intrinsics, `@intrinsic` operations, closure capture forwarding, on-demand HIR->MIR lowering + drop elaboration, `interp_run`, and comptime `interp_eval_const_expr_into`.
     - `compiler/interp/mod.ax` (118 lines): Public module re-exports.
   - **Unit & execution parity tests (`tests/selfhost/interp/`)**:
     - Command: `python tools/axtest.py --compiler build/axiom0.exe -v selfhost/interp` (inside `build-snap-T083a/`)
     - Result: `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0` (`qa_interp_unit.ax`, `qa_interp_exec_a.ax`, `qa_interp_exec_b.ax` all pass in `[interp]`, `[native]`, and `[native-O1]`).
     - Verified exit code and stdout parity (`"fib=2\nsum=150\n"` -> `129`, panics -> `101`, UB -> `125`, step/stack limits -> `124`, non-oracle FFI -> `1`).
   - **Full test suite**:
     - Ran full suite in `build-snap-T083a` (`1,827` test runs total; re-ran contended parallel tests sequentially with `-j 1`/`-j 2`: `TOTAL 30 PASS 30 FAIL 0` and `TOTAL 9 PASS 9 FAIL 0`).

5. **Boundary & Seam Cross-Check (QA Tests Added)**
   - Extended `tests/selfhost/interp/unit_main.ax.in` (`qa_interp_unit.ax`):
     - One-past-the-end synthetic address resolution (`interp_find_synth_addr` at `host_ptr + size == base_addr + size`).
     - Pointer arithmetic out-of-bounds (`interp_validate_ptr_arith` at `base_addr + size + 1`) and unmapped base address (`0x77770000`) reporting `AX_UNSAFE_INTERP_UB` (`exit_code == 125`).
     - Host oracle boundary checks for `stdio(2) == 2`, `stdio(3) == -4`, `close(1) == 0`, and `close(99) == -4`.
     - `heap_free` on a non-heap stack allocation (`call_depth == 1 != -1`) reporting `INTERP_MSG_UB_FREE_NON_HEAP` (`AX_UNSAFE_INTERP_UB`, `exit_code == 125`).
   - Extended `tests/selfhost/interp/exec_b_main.ax.in` (`qa_interp_exec_b.ax`):
     - Comptime evaluation step limit exceeded (`max_steps: 2` -> `!ok` with `AX_CONST_EVAL_LIMIT`).
     - `MIR_PROJ_SUB_SLICE` valid slice projection + indexing (`arr[1..3][0] + arr[1..3][1] == 50`) and out-of-bounds sub-slice (`arr[3..1]`, `start > end` -> panic `101`).
     - Shift amount out-of-range (`1i32 << 32i32` -> panic `101`).
   - Regenerated bundles with `python tests/selfhost/interp/gen_interp_tests.py`, refreshed `build-snap-T083a`, and re-verified `TOTAL 9 PASS 9 FAIL 0 SKIP 0 XFAIL 0`.

### Findings
None.

## Files changed
- tests/selfhost/interp/unit_main.ax.in
- tests/selfhost/interp/exec_b_main.ax.in
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp/qa_interp_exec_b.ax

## Verdict
VERDICT: PASS round=0
