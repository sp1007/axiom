# T139 Report — axtest cross-mode agreement and native-evidence report for run tests

## Summary

Implemented leg serialization, cross-mode agreement checking for `run` tests, weak native evidence reporting (`WEAK-NATIVE` / `"weak_native_evidence"`), and the `stdout-file:` directive with `--bless` support in `tools/axtest.py`. Updated `tests/lir/*.test` and `tests/hir/more.test` to use `stdout-file:` and `{compiler}`, paired all 17 previously orphaned `.lir` files in `tests/lir/` with `.test` manifests, re-blessed drifted Category C goldens after diff review, documented Category C status in `tests/lir/COVERAGE.md`, added 7 self-tests in `tools/tests/axtest/test_axtest.py`, and updated `tests/README.md`.

## Deliverables

1. **Leg isolation (`tools/axtest.py`)**:
   - `Runner.run_entries` normalizes modes in fixed order (`interp`, then `native`, then `native-O1`).
   - `main()` groups entries per test file and dispatches `execute_group` to each worker thread so all legs of a single test execute sequentially in one worker and never overlap under `-j > 1`.
2. **Cross-mode agreement for `run` tests (`tools/axtest.py`)**:
   - `Runner.run_entries` shares a per-test context across legs. When `interp` executes without hitting `INTERP_LIMIT_EXIT` (`AX_DRIVER_INTERP_`) and passes its own directives, its `Observed` exit code and stdout bytes are recorded.
   - Each subsequent `native` / `native-O1` leg compares its observed exit code and stdout bytes against `interp` (using `byte_diff`), failing with `interp/native disagree` on any mismatch.
   - Single-mode tests (`modes:`), skipped legs, and interpreter-limit runs are not compared across modes.
3. **Native-evidence report (`tools/axtest.py`)**:
   - Added `is_weak_native_evidence(entry, out)`: `True` when a `run` test's `native` or `native-O1` leg executed (not `SKIP`), expected exit is `0` (or default `0`), and no `stdout`, `stderr`, `stdout-contains`, `stderr-contains`, or `stdout-file` directive is present.
   - `--json` adds `"weak_native_evidence": bool` on each entry in `"results"` and `"weak_native": int` in `"counts"`.
   - Text output prints `WEAK-NATIVE n` immediately before the final `TOTAL n PASS p FAIL f SKIP s XFAIL x` line, and with `--verbose` lists `WEAK    <entry>` for each weak entry.
4. **Golden comparison for inspect manifests (`stdout-file:`)**:
   - Added `"stdout-file": "single"` directive to `tools/axtest.py` (`judge`, `entries_for`, and `run_exec(..., bless=...)`).
   - Updated all 36 `tests/lir/*.test` manifests for `tests/lir/*.mir` to use `stdout-file: <stem>.lir` (creating `tests/lir/qa_edge_cond_br.lir` to replace inline `stdout:`).
   - Added 17 `tests/lir/<stem>.test` manifests (`001-return.test`..`010-early-return.test` and `t117_*.test`) for the 17 previously orphaned `.lir` files in `tests/lir/` that inspect `tests/run/basic/<stem>.ax`.
   - Updated `tests/hir/more.test` to use `{compiler}` and `stdout-file: more.hir`, blessing `tests/hir/more.hir`.
   - Updated `tests/lir/COVERAGE.md` to document that `tests/lir/*.lir` goldens are Category C (self-snapshot / regression) evidence per ADR-0034.
5. **Golden drift review (`tests/lir/*.lir`)**:
   - 30 of the 35 existing `.mir`-backed `.lir` goldens matched `axiom0` byte-for-byte without change.
   - `abi_arg.lir`, `abi_result.lir`, `call.lir`: Re-blessed for the legitimate T033 (`1df0efe`) call lowering change (evaluating all call arguments and destination `stack_addr slot0` before `abi_arg` instructions to prevent nested call clobbering, and emitting direct `call __ax_fn_1;` instead of indirect register call).
   - `offset.lir`: Previously committed as UTF-16LE with BOM/CRLF in T023; re-blessed as UTF-8 LF with T035a (`4edbc19`) lowering `AX_MIR_BINOP_OFFSET` to `add`.
   - `qa_multi_branch.lir`: Previously committed as UTF-16LE with BOM/CRLF in T023; re-blessed as UTF-8 LF (identical text content).
   - `001-return.lir` matched byte-for-byte; `002-arithmetic.lir`..`010-early-return.lir` and `t117_*.lir` (16 files) were re-blessed to match current MIR/LIR lowering after T034/T035a/T051/T054b/T134.
6. **Self-tests & documentation (`tools/tests/axtest/test_axtest.py`, `tools/tests/axtest/stubcc.py`, `tests/README.md`)**:
   - Added 7 unit tests in `test_axtest.py` covering cross-mode agreement PASS, stdout disagreement FAIL with byte diff, exit-code disagreement FAIL, interp-limit exemption, `weak_native_evidence` JSON/text reporting, `stdout-file:` match/mismatch/`--bless`, and `-j 8` leg serialization via `//@ touch-dir`.

## Verification

- `python build-snap-T139/tools/tests/axtest/run_selftests.py`:
  - `Ran 72 tests in 134.468s — OK (SELFTEST 72 tests, 0 failures, 0 errors)`
- `python build-snap-T139/tools/axtest.py --compiler build-snap-T139/build/axiom0.exe --root build-snap-T139 -j 8 --filter run/host/fs/` (20 consecutive runs):
  - All 20 runs: `rc=0`, `WEAK-NATIVE 8 | TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`
- `python build-snap-T139/tools/axtest.py --compiler build-snap-T139/build/axiom0.exe --root build-snap-T139 --verbose lir/ hir/more.test`:
  - `WEAK-NATIVE 0 | TOTAL 54 PASS 54 FAIL 0 SKIP 0 XFAIL 0`
- Full suite run in `build-snap-T139` (`-j 1 --verbose`):
  - `WEAK-NATIVE 319` reported across the full suite.
  - Cross-mode agreement immediately caught 5 existing `run` tests (10 native entries: `run/method/builtins.ax`, `run/method/inherent_methods.ax`, `run/method/qa_run.ax`, `run/native_str/qa_print_int.ax`, `run/str/qa_print_int.ax`) where `--interp` prints expected ASCII digits via `print_int(...)` (`5\n15\n`, `30\n40\n40\n44\n44\n`, `42\n`, `42`) while native codegen emits NUL bytes (`0x00`) of the same length and exits 0. Note: `run/native_str/qa_print_int.ax` and `run/str/qa_print_int.ax` had a blank line before `// stdout: 42`, so their `stdout:` directive was previously ignored by `split_header`.
  - With `-O2` (`RelWithDebInfo`) `axiom0.exe` and `--timeout-scale 2`, `selfhost/backend/qa_backend_unit.ax`, `selfhost/drop/qa_drop_d11.ax`, and `selfhost/obj_link_driver/axiomc_e2e.test` all pass (`TOTAL 7 PASS 7 FAIL 0 SKIP 0 XFAIL 0`).

## Follow-ups

- **Native `print_int` emits NUL bytes (`0x00`) instead of ASCII digits**: Caught by T139's new cross-mode agreement check on `tests/run/method/builtins.ax`, `tests/run/method/inherent_methods.ax`, `tests/run/method/qa_run.ax`, `tests/run/native_str/qa_print_int.ax`, and `tests/run/str/qa_print_int.ax` (also remove the blank line between `// test: run` and `// stdout: 42` in the two `qa_print_int.ax` files during T145).

## Files changed

- tests/README.md
- tests/hir/more.hir
- tests/hir/more.test
- tests/lir/001-return.test
- tests/lir/002-arithmetic.lir
- tests/lir/002-arithmetic.test
- tests/lir/003-branches.lir
- tests/lir/003-branches.test
- tests/lir/004-loops.lir
- tests/lir/004-loops.test
- tests/lir/005-fib.lir
- tests/lir/005-fib.test
- tests/lir/006-trap-overflow.lir
- tests/lir/006-trap-overflow.test
- tests/lir/007-trap-divzero.lir
- tests/lir/007-trap-divzero.test
- tests/lir/008-step-limit.lir
- tests/lir/008-step-limit.test
- tests/lir/009-call-depth.lir
- tests/lir/009-call-depth.test
- tests/lir/010-early-return.lir
- tests/lir/010-early-return.test
- tests/lir/COVERAGE.md
- tests/lir/abi_arg.lir
- tests/lir/abi_arg.test
- tests/lir/abi_result.lir
- tests/lir/abi_result.test
- tests/lir/add.test
- tests/lir/bit_and.test
- tests/lir/bit_or.test
- tests/lir/bit_xor.test
- tests/lir/bitnot.test
- tests/lir/call.lir
- tests/lir/call.test
- tests/lir/const.test
- tests/lir/div.test
- tests/lir/icmp_eq.test
- tests/lir/icmp_ne.test
- tests/lir/icmp_sge.test
- tests/lir/icmp_sgt.test
- tests/lir/icmp_sle.test
- tests/lir/icmp_slt.test
- tests/lir/icmp_uge.test
- tests/lir/icmp_ugt.test
- tests/lir/icmp_ule.test
- tests/lir/icmp_ult.test
- tests/lir/load.test
- tests/lir/mul.test
- tests/lir/neg.test
- tests/lir/not.test
- tests/lir/offset.lir
- tests/lir/offset.test
- tests/lir/qa_edge_cond_br.lir
- tests/lir/qa_edge_cond_br.test
- tests/lir/qa_multi_branch.lir
- tests/lir/qa_multi_branch.test
- tests/lir/rem.test
- tests/lir/shl.test
- tests/lir/shr.test
- tests/lir/stack_addr.test
- tests/lir/store.test
- tests/lir/sub.test
- tests/lir/t117_bitwise.lir
- tests/lir/t117_bitwise.test
- tests/lir/t117_panic.lir
- tests/lir/t117_panic.test
- tests/lir/t117_qa_neg_i8_min.lir
- tests/lir/t117_qa_neg_i8_min.test
- tests/lir/t117_qa_u8_bitwise_not.lir
- tests/lir/t117_qa_u8_bitwise_not.test
- tests/lir/t117_shifts.lir
- tests/lir/t117_shifts.test
- tests/lir/t117_unary.lir
- tests/lir/t117_unary.test
- tests/lir/t117_width_exact.lir
- tests/lir/t117_width_exact.test
- tests/lir/wrapping_add.test
- tests/lir/wrapping_mul.test
- tests/lir/wrapping_sub.test
- tools/axtest.py
- tools/tests/axtest/stubcc.py
- tools/tests/axtest/test_axtest.py

## Status

STATUS: COMPLETE round=0
