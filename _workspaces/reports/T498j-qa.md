# T498j QA Gate Report — Fix `ui/backend_ice/sat_u128_emit_mc.test` RBP displacement after T498h

## Round 0

### Scope & Diff Audit
- Audited `_workspaces/tasks/doing/T498j-fix-sat-u128-emit-mc-frame-displacement.md`, `_workspaces/reports/T498j-report.md` (ends with `STATUS: COMPLETE round=0`), and `tests/ui/backend_ice/sat_u128_emit_mc.test`.
- Confirmed `tests/ui/backend_ice/sat_u128_emit_mc.test` documents the post-`T498h` frame layout (`sub rsp, 0x90`, 8B `sret` slot `_0` at `[rbp-0x10]`, `copy _1` at `[rbp-0x60]`/`[rbp-0x58]`, `copy _2` at `[rbp-0x70]`/`[rbp-0x68]`), pins both `48 81 ec 90 00 00 00` and `48 03 45 90 48 13 55 98 49 b8 ff ff ff ff ff ff ff ff 49 0f 42 c0 49 0f 42 d0`, and leaves `tests/ui/backend_ice/sat_u128_lowered.mir` and `compiler/` untouched.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T498j`: exit 0, 0 `REFUSED` lines (stages `_workspaces/reports/T498j-report.md` and `tests/ui/backend_ice/sat_u128_emit_mc.test`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).

### Verification (inside `build-snap-T498j/` only)
1. **Stage-2 build**:
   - `python tools/build_axiomc.py --out build --root . --stage 2`
   - Result: `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T498j\build\axiomc2.exe size=8686592 sha256=43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6` (exit 0).
2. **Direct machine-code inspection**:
   - `.\build\axiomc2.exe inspect --emit=mc tests/ui/backend_ice/sat_u128_lowered.mir` (exit 0)
   - Verified emitted bytes contain:
     - Prologue `55 48 89 e5 48 81 ec 90 00 00 00` (`sub rsp, 0x90` -> pinned `48 81 ec 90 00 00 00`)
     - Hidden `sret` save `48 89 4d f0` (`mov [rbp-0x10], rcx`)
     - `copy _1` load `48 8b 45 a0 48 8b 55 a8` (`[rbp-0x60]`/`[rbp-0x58]`)
     - 128-bit `SatAdd` `48 03 45 90 48 13 55 98 49 b8 ff ff ff ff ff ff ff ff 49 0f 42 c0 49 0f 42 d0` (`add rax, [rbp-0x70]; adc rdx, [rbp-0x68]; mov r8, -1; cmovb rax, r8; cmovb rdx, r8`).
3. **Suite `ui/backend_ice`**:
   - `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v ui/backend_ice`
   - Result: `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (exit 0):
     - `PASS ui/backend_ice/sat_u128_emit_lir.test`
     - `PASS ui/backend_ice/sat_u128_emit_mc.test`
     - `PASS ui/backend_ice/sat_u128_emit_mi.test`
4. **Mutation spot-proof (inside `build-snap-T498j/` only)**:
   - Perturbed `48 03 45 90` -> `48 03 45 91` in `build-snap-T498j/tests/ui/backend_ice/sat_u128_emit_mc.test` and ran `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v ui/backend_ice/sat_u128_emit_mc.test`: `FAIL ui/backend_ice/sat_u128_emit_mc.test` (`TOTAL 1 PASS 0 FAIL 1`, exit 1).
   - Restored byte-identical (SHA256 `5FD49C47C9BA735C30575ACAED2E52040CBA05E2F6CFAE64744E9D0C13F892CB` verified identical) and re-ran: `PASS ui/backend_ice/sat_u128_emit_mc.test` (`TOTAL 1 PASS 1 FAIL 0`, exit 0).
5. **Taskgate**:
   - Command: `python tools/taskgate.py --task T498j --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T498j.json`

### taskgate T498j (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T498j`, HEAD `0107fecf30a0`, compiler `D:/projects/compiler/new lang/build-snap-T498j/build/axiomc2.exe`, `-j 2`
- change set: 2 file(s) (working tree of build-snap-T498j vs HEAD)
  - `_workspaces/reports/T498j-report.md`
  - `tests/ui/backend_ice/sat_u128_emit_mc.test`
- wall time: 25.9 s (axtest 22.2 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| affected | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| smoke | 33 | 54 | 54 | 0 | 0 | 0 | 3 |
| **total (dedup)** | 34 | 55 | 55 | 0 | 0 | 0 | 3 |

Counts per group:

| group | ids | failing | parts |
|---|---|---|---|
| build_native | 1 | 0 | smoke |
| conformance | 1 | 0 | smoke |
| diff | 2 | 0 | smoke |
| driver | 1 | 0 | smoke |
| encode | 1 | 0 | smoke |
| fuzz | 1 | 0 | smoke |
| hir | 1 | 0 | smoke |
| inspect | 1 | 0 | smoke |
| lex | 1 | 0 | smoke |
| link | 1 | 0 | smoke |
| link2 | 1 | 0 | smoke |
| lir | 1 | 0 | smoke |
| mc | 1 | 0 | smoke |
| mir | 1 | 0 | smoke |
| modules | 1 | 0 | smoke |
| obj | 1 | 0 | smoke |
| opt | 1 | 0 | smoke |
| opt2 | 1 | 0 | smoke |
| parse | 1 | 0 | smoke |
| perf | 1 | 0 | smoke |
| programs | 1 | 0 | smoke |
| resolve | 1 | 0 | smoke |
| run | 2 | 0 | smoke |
| selfhost | 1 | 0 | smoke |
| std | 1 | 0 | smoke |
| tools | 1 | 0 | smoke |
| typeck | 1 | 0 | smoke |
| ui | 3 | 0 | affected, own, smoke |
| unit | 1 | 0 | smoke |
| verify | 1 | 0 | smoke |

Affected-set derivation (rule per id; rules in `tools/axtest_affected.py`):

- `ui/backend_ice/sat_u128_emit_mc.test` <- test: changed test file
- no-op (select nothing): `_workspaces/reports/T498j-report.md`
- unmatched changed files: none

Smoke: seed=2485767284, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`; picks build_native=`build_native/qa_assert_and_backedge_fixups.ax`, conformance=`conformance/p5/0114_prog_a_hello.ax`, diff=`diff/004-arith-neg.ax`, driver=`driver/no_args.test`, encode=`encode/axiom/qa_encode_reloc_and_sym.ax`, fuzz=`fuzz/qa_seed_test.ax`, hir=`hir/basic.ax`, inspect=`inspect/async_layout.test`, lex=`lex/L08_byte_literal.ax`, link=`link/objdump_validate.test`, link2=`link2/multi_mod_pkg`, lir=`lir/add.test`, mc=`mc/isel/vs1_return.ax`, mir=`mir/int128/shift_i8_rhs_check.test`, modules=`modules/std_root.test`, obj=`obj/determinism/string_symbols.test`, opt=`opt/const_fold_run.ax`, opt2=`opt2/qa_boundary_sroa_inline_seam.ax`, parse=`parse/async/async_fn_and_await.ax`, perf=`perf/loop.ax`, programs=`programs/word_count.ax`, resolve=`resolve/simple.ax`, run=`run/basic/001-return.ax`, selfhost=`selfhost/intrinsics/qa_unreachable_abort.ax`, std=`std/core/qa_primitives.ax`, tools=`tools/build_axiomc_fallback/stage1_failure_is_not_a_seed_failure.test`, typeck=`typeck/async/await_outside_async_neg.ax`, ui=`ui/cfg/labeled_loop_err.ax`, unit=`unit/kernel/hash_vectors_current.test`, verify=`verify/drop/cond_drop_flag_ok.test`

Cache: CACHED 3, miss 1, uncacheable 12, stored 1, dep_source exact, verification sample seed=1646626465 n=20 of 21 hits, mismatch none, rejected {}, producer snapshot
WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests
Baseline (`D:\projects\compiler\new lang\build-snap-T498j\_workspaces\baseline-failures.txt`): BASELINE OK
Failing ids: none
archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations
smoke-check (tests/smoke.list): OK; est. worst-case draw 17 s
axtest: `TOTAL 55 PASS 55 FAIL 0 SKIP 0 XFAIL 0` (exit 0)

TASKGATE T498j exit=0

### Findings
None.

## Files changed
(none)

VERDICT: PASS round=0
