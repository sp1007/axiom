# T142: Objdump Validation on Real `.exe`/`.obj` Outputs, Wire `tests/obj/cdriver_coff.c`, and Finish `{compiler}` Placeholder Migration — Implementation Report

## Summary

1. **Real `.exe` and `.obj` external-oracle validation (`tests/link/objdump_validate.py` + `tests/link/objdump_validate.test`)**:
   - Added a stage-neutral Python 3 stdlib test script (`tests/link/objdump_validate.py`) and exec manifest (`tests/link/objdump_validate.test`, no `requires: axiom0-internal`) that builds **28** real `.ax` programs across all 6 required categories (`numeric`, `drop`, `str`/`UTF-8`, `ffi`, `std` `fs`/`io`/`process`/`alloc`, and multi-function programs with `.rdata` tables) using both `{compiler} build` (`.exe`) and `{compiler} build --emit=obj` (`.obj`).
   - Validates every `.exe` and `.obj` with `objdump -x`, `objdump -d`, and `objdump -p`:
     - Fails immediately (exit 1, never `SKIP`) if `objdump` is missing on `PATH` (ADR-0034 §7), or if `objdump` exits non-zero / reports `"file format not recognized"`.
     - Asserts zero `(bad)` instructions in `objdump -d` disassembly.
     - Asserts the PE entry point (`start address` in `objdump -x` and `ImageBase + AddressOfEntryPoint` in `objdump -p`) lies strictly within `.text` (`[vma, vma + size)`).
     - Asserts section characteristics: `.text` has `CODE|EXECUTE|READ` and NOT `WRITE`; `.rdata` (when present) has `READ` only (not `WRITE`, not `EXECUTE`); `.data` (when present) has `READ|WRITE` and NOT `EXECUTE`.
     - Asserts every expected `KERNEL32.dll` import (pinned per program in `TEST_CASES` from each program's known host calls, never read from compiler output) and `USER32.dll` import (`wsprintfA` in `qa_extern_c_multidll.ax`) appears in the PE import table (`objdump -p`).
     - Asserts every relocation record in `RELOCATION RECORDS FOR [.text]` (and `[.rdata]` when present) uses a valid COFF x86-64 relocation type (`IMAGE_REL_AMD64_REL32`, `IMAGE_REL_AMD64_ADDR64`, `IMAGE_REL_AMD64_ADDR32NB`) and targets a symbol either defined in the COFF symbol table or listed as external (`UND`), never `*ABS*` or unknown.
     - Executes each built `.exe` with its pinned CLI args / environment variables and verifies the exact exit code and stdout bytes.
   - Includes a 6-case negative self-test suite (plus standalone `--corrupt-check <path>` mode) verifying that deliberately corrupted `.exe`/`.obj` files fail `validate_exe` / `validate_obj`.

2. **Wire `tests/obj/cdriver_coff.c` into `axtest.py` (`tests/obj/cdriver_coff.test`)**:
   - Deleted placeholder `tests/obj/dummy.test` and added `tests/obj/cdriver_coff.test` (`cmd: {build}/tests/ct_obj_cdriver_coff`, `exit: 0`, `timeout: 60`, `stdout-contains: PASS`, `requires: axiom0-internal`).
   - Updated `tests/obj/cdriver_coff.c` to fail (`return 1`, printing `FAIL: gcc not on PATH (ADR-0034 section 7)`) instead of printing `SKIP` when `gcc` is missing on `PATH`, resolve `tests/obj/fixtures/c_helper.c` whether invoked from the repo root (`axtest.py`), `build/` (`ctest`), or `__FILE__`, and remove temporary `.obj`/`.exe` artifacts on exit.

3. **Migrate `{build}/axiom0` -> `{compiler}` across `tests/driver/` and `tests/verify/`**:
   - Replaced `{build}/axiom0` with `{compiler}` in all **17** `tests/driver/*.test` manifests and all **19** `tests/verify/**/*.test` manifests (**36** manifests total).
   - Before/after count of `grep -rlE "\{build\}/axiom0([ .]|$)" tests --include=*.test`:
     - **Before**: **36** files (17 in `tests/driver/`, 19 in `tests/verify/`; `tests/hir/more.test` was already migrated in T139, and `tests/unit/diag/diag_unit.test` + `tests/unit/kernel/kernel_unit.test` invoke `{build}/axiom0-unit` with `requires: axiom0-internal`).
     - **After**: **0** files. All 21 remaining `{build}` references in `tests/**/*.test` invoke internal C test binaries (`ct_*` or `axiom0-unit`) and carry `requires: axiom0-internal`.

4. **Strengthen `tests/driver/build_emit_obj.test` / `tests/driver/cross_link_oracle.py`**:
   - Updated `tests/driver/cross_link_oracle.py` to fail immediately if `gcc` is missing on `PATH` (ADR-0034 §7) and to cross-link both `tests/driver/test.ax` (exit 0) and a non-trivial self-contained program `tests/driver/fixtures/nontrivial_self_contained.ax` (`.rdata` `const TABLE: Table`, multi-function calls `step_mul` + `combine`, wrapping arithmetic intrinsics, exit code `42`) via `gcc -nostdlib -Wl,--entry=ax_main`.
   - **Why checked arithmetic / bounds checks cannot link with `gcc -nostdlib -Wl,--entry=ax_main`**: Checked arithmetic (`+`, `-`, `*`, `/`, `%`) and dynamic array indexing lower to `AX_X64_MI_ASSERT`, which emits an external `IMAGE_REL_AMD64_REL32` relocation targeting `axiom_panic`. Because `axiom_panic` is synthesized at PE link time by `ax_pe_link` (`bootstrap/axiom0/src/link/pe/linker.c`) rather than emitted into `--emit=obj`, linking an object that references `axiom_panic` under `gcc -nostdlib -Wl,--entry=ax_main` without a companion runtime object fails with `undefined reference to 'axiom_panic'`.

## Files changed

- `tests/link/objdump_validate.py` — new Python 3 stdlib oracle validating 28 real `.ax` programs built to `.exe` and `.obj` via `objdump -x`, `-d`, `-p`, plus 6 negative corruption checks
- `tests/link/objdump_validate.test` — new exec manifest running `tests/link/objdump_validate.py {compiler} {tmp} {root}` (stage-neutral, no `requires: axiom0-internal`)
- `tests/obj/cdriver_coff.c` — fail (exit 1) instead of `SKIP` when `gcc` is missing on `PATH`, locate `c_helper.c` across working directories, and clean up temporary `.obj`/`.exe` files
- `tests/obj/cdriver_coff.test` — new exec manifest running `{build}/tests/ct_obj_cdriver_coff` (`requires: axiom0-internal`)
- `tests/obj/dummy.test` — deleted placeholder manifest replaced by `tests/obj/cdriver_coff.test`
- `tests/driver/cross_link_oracle.py` — fail if `gcc` is missing on `PATH` and cross-link both `tests/driver/test.ax` (exit 0) and `tests/driver/fixtures/nontrivial_self_contained.ax` (exit 42) with `gcc -nostdlib -Wl,--entry=ax_main`
- `tests/driver/fixtures/nontrivial_self_contained.ax` — new self-contained helper program (`.rdata` `const TABLE: Table`, `step_mul` + `combine` calls, wrapping arithmetic intrinsics, exit 42)
- `tests/driver/build_emit_obj.test` — replace `{build}/axiom0` with `{compiler}` and set `timeout: 60`
- `tests/driver/build_missing_o.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/build_ok.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/build_stack_reserve.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/check_err.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/check_ok.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/features.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/help.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/inspect.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/json.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/no_args.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/options.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/run_interp_args.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/run_ok.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/time_passes.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/unknown_opt.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/driver/version.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/bad_target.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/call_signature.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/type_mismatch.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/type_mismatch_binop.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/type_mismatch_cast.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/uninit_cond.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/uninit_use.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/unknown_local.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/unknown_local_storage.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/unterminated_block.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/conditional_move.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/double_drop.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/missing_drop.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/missing_drop_no_unreachable.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/overwrite_owned.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/qa_conditional_double_drop.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/qa_loop_move.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/return_moved.test` — replace `{build}/axiom0` with `{compiler}`
- `tests/verify/own/use_after_move.test` — replace `{build}/axiom0` with `{compiler}`

## Test results

1. **Build (`gcc` and `clang`, 0 warnings)**:
   - `cmake --build build-snap-T142/build` (GCC 15.2.0, `-std=c11 -Wall -Wextra -Wpedantic -Werror`): 0 warnings, 0 errors.
   - `cmake -S build-snap-T142/bootstrap/axiom0 -B build-snap-T142/build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Debug -DCMAKE_C_FLAGS_DEBUG="-O2 -g" && cmake --build build-snap-T142/build` (Clang 22.1.4, `-std=c11 -Wall -Wextra -Wpedantic -Werror`): 0 warnings, 0 errors.

2. **Negative verification of `tests/link/objdump_validate.py` on corrupted `.exe` and `.obj`**:
   - Built-in 6-case negative suite runs on every invocation of `objdump_validate.py` (`OBJDUMP-VALIDATE ok: 28 programs (.exe + .obj) + 6 negative checks passed`).
   - Standalone `--corrupt-check` verification on a corrupted `.exe` (8 `0x06` `push es` invalid x86-64 opcodes patched into `.text`) and a corrupted `.obj` (relocation `SymbolTableIndex` patched to `0xFFFFFFFF` / `*ABS*`):
     ```
     $ python tests/link/objdump_validate.py --corrupt-check bad_opcode.exe
     FAIL: bad_opcode.exe: 8 '(bad)' instruction(s) in disassembly; first: 140002000:	06                   	(bad)
     (exit code 1)

     $ python tests/link/objdump_validate.py --corrupt-check bad_reloc.obj
     FAIL: bad_reloc.obj: relocation in .text at 0x8a targets unknown symbol '*ABS*'
     (exit code 1)
     ```
   - Missing `objdump` on `PATH` verification:
     ```
     FAIL: mandatory external oracle 'objdump' not found on PATH (ADR-0034 section 7)
     (exit code 1)
     ```

3. **Targeted test runs (`-j 1`)**:
   - `python build-snap-T142/tools/axtest.py --compiler build-snap-T142/build/axiom0.exe --root build-snap-T142 driver/build_emit_obj link/objdump_validate obj/cdriver_coff -j 1 --verbose` -> `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`
   - `python build-snap-T142/tools/axtest.py --compiler build-snap-T142/build/axiom0.exe --root build-snap-T142 driver link obj verify -j 1 --verbose` + `selfhost/obj_link_driver/axiomc_e2e` + `selfhost/driver/qa_driver_inspect_diff_a` -> all `PASS`, `FAIL 0 SKIP 0`.

4. **Full suite run (`-j 1`)**:
   - `python build-snap-T142/tools/axtest.py --compiler build-snap-T142/build/axiom0.exe --root build-snap-T142 -j 1`: 2714/2715 passed on first pass (1 transient OS paging crash on `selfhost/driver/qa_driver_inspect_diff_a.ax [interp]` under concurrent system load); immediate re-run of `selfhost/driver/qa_driver_inspect_diff_a` passed all 3 modes (`TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`).

## Follow-ups

1. **Latent bug in `__ax_host_print_int` runtime stub (`bootstrap/axiom0/src/link/pe/linker.c` and `compiler/link/pe/linker.ax`) + ignored `// stdout:` directive in `qa_print_int.ax`**:
   - In `bootstrap/axiom0/src/link/pe/linker.c` (`emit_runtime_stubs`, lines 155–221) and `compiler/link/pe/linker.ax`, `__ax_host_print_int` allocates a 64-byte stack frame (`sub $0x40, %rsp`), sets `rdi = rsp + 0x20` (`lea 0x20(%rsp), %rdi`), and writes formatted ASCII digits backwards into `[rsp .. rsp + 0x20)`. However, `[rsp .. rsp + 0x20)` is the 32-byte Win64 home/shadow space for the subsequent `call GetStdHandle(-11)` (`mov $-11, %ecx; call *__imp_GetStdHandle(%rip)`). `GetStdHandle` overwrites its 32-byte shadow space at `[rsp + 8 .. rsp + 0x28)` with zeros before `WriteFile` is called, causing `print_int(42)` in native executables to output `b"\x00\x00"` (2 NUL bytes) instead of `b"42"`. Changing `lea 0x20(%rsp), %rdi` to `lea 0x38(%rsp), %rdi` places the digit buffer above the 32-byte shadow space (`[rsp + 0x20 .. rsp + 0x38)`).
   - This bug went undetected because both `tests/run/str/qa_print_int.ax` and `tests/run/native_str/qa_print_int.ax` have a blank line on line 2 before `// stdout: 42` on line 3; `tools/axtest.py`'s `split_header` stops parsing directives at the first non-comment line, so `// stdout: 42` was silently ignored in both files.

2. **Unused variable warnings under `-DNDEBUG` (`Release` / `RelWithDebInfo`) in `tests/mc/isel/cdriver_abi*.c`**:
   - In `tests/mc/isel/cdriver_abi.c`, `tests/mc/isel/cdriver_abi_edge.c`, `tests/mc/isel/cdriver_abi_qa.c`, and `tests/mc/isel/cdriver_abi_qa2.c`, `AxAbiSig` variables (`sig`, `sig1`, `sig2`, `sig3`, `sig_4`, `sig_ret5`) are only referenced inside `assert(...)`, triggering `-Werror,-Wunused-variable` when built with `-DNDEBUG`.

STATUS: COMPLETE round=0
