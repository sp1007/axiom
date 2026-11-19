# T444c QA Report — build_axiomc/bootstrap reuse stage binaries by content hash of their inputs, not mtime

## Round 0

### 1. Change-set & harness audit
- Engineer report `_workspaces/reports/T444c-report.md` ends with `STATUS: COMPLETE round=0`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T444c` exits 0 with zero `REFUSED` lines:
  ```
  stage _workspaces/reports/T444c-report.md
  stage tools/bootstrap.py
  stage tools/build_axiomc.py
  stage tools/tests/build_axiomc/run_selftests.py
  stage tools/tests/build_axiomc/test_build_axiomc.py
  ```
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).
- Snapshot refresh (`python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T444c`):
  ```
  snapshot D:\projects\compiler\new lang\build-snap-T444c  (refreshed: HEAD eca6645 + 5 changed, 0 deleted file(s) of T444c)
  bundles regenerated in build-snap-T444c: 36 generator(s), 154 file(s), 63s
  ```

### 2. Acceptance criteria verification

1. **Self-tests & full-tree hashing cost (< 2 s)**:
   - Command (inside `build-snap-T444c`): `python tools/tests/build_axiomc/run_selftests.py -v`
   - Result: `SELFTEST 25 tests, 0 failures, 0 errors` (2.564 s total; 22 engineer tests + 3 QA boundary/adversarial tests).
   - Full-tree hashing cost on the live tree:
     - `bootstrap/axiom0` (170 files): `0.044s`
     - `compiler/**/*.ax` + `std/**/*.ax|toml` (257 files): `0.09s`–`0.14s` (`T444c: hashed 257 compiler/std source files in 0.11s`), well below the 2.0 s target.

2. **Real `python tools/build_axiomc.py --out build` inside `build-snap-T444c` (REUSED -> backdated edit REBUILT -> `--force` byte-identical -> REUSED)**:
   - Unchanged inputs run prints `REUSED` for stage 0, stage 1, and stage 2:
     ```
     REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
     INPUTS: 257 source files hashed in 0.13s (sources b6daf4ddfb041241)
     REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (inputs b372e08eeb0758fd)
     STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=0.00s, peak_ws=0.0MB, peak_commit=0.0MB)
     REUSED D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe (inputs 2021320f4f621c53)
     STAGE2 (O1) OK: D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe [dir=D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1] (8142848 bytes, sha256=fa1d7d6dc3d4e41c, wall=0.00s, peak_ws=0.0MB, peak_commit=0.0MB)
     BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc2.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=8142848 sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1
     ```
   - After modifying `build-snap-T444c/std/core/cmp.ax` and setting its mtime back to `1000000000.0` (older than `axiomc1.exe` mtime `1795048809.56`), running `python tools/build_axiomc.py --out build --stage 1` detects the content hash mismatch and prints `REBUILT`:
     ```
     cmp.ax mtime: 1000000000.0 axiomc1 mtime: 1795048809.5587468
     REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
     INPUTS: 257 source files hashed in 0.14s (sources 0de4fb5533709e21)
     REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (sources changed: std/core/cmp.ax)
     STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=118.87s, peak_ws=2182.6MB, peak_commit=2412.4MB)
     BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=26334720 sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083
     ```

3. **`--force` behaviour and byte-identical output**:
   - Restoring `std/core/cmp.ax` and running `python tools/build_axiomc.py --out build --stage 1 --force` forces a rebuild with `(reuse not requested)` and produces a byte-identical `axiomc1.exe` (`sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083`, `26334720` bytes):
     ```
     REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
     INPUTS: 257 source files hashed in 0.12s (sources b6daf4ddfb041241)
     REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (reuse not requested)
     STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=96.24s, peak_ws=2184.1MB, peak_commit=2414.1MB)
     BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=26334720 sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083
     ```
   - Subsequent `python tools/build_axiomc.py --out build` reuses stage 0, the forced stage-1 binary, and the stage-2 binary (`sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`, `8142848` bytes).

### 3. Boundary cross-check / adversarial tests added (step 5)
Added 3 adversarial tests to `tools/tests/build_axiomc/test_build_axiomc.py`:
- `BootstrapReuse.test_added_and_deleted_source_files_and_truncation_over_three_files`: verifies that adding a new backdated `.ax` file triggers a rebuild naming the added path, deleting an `.ax` file triggers a rebuild naming the deleted path, and changing >3 files formats the rebuild reason with the first 3 sorted paths plus `(+2 more)`.
- `BootstrapReuse.test_empty_binary_schema_change_and_fallback_candidate_reuse`: verifies that deleting `dir_stage2_O1/axiomc2.exe` falls back to top-level `axiomc2_O1.exe`/`axiomc2.exe` via `find_reusable` and restores the stage directory copy without recompiling; truncating all candidate binaries to 0 bytes triggers a rebuild with `(previous binary is empty)`; and an unknown manifest schema version triggers a rebuild with `(input manifest schema changed)`.
- `Stage0Reuse.test_build_axiomc_main_end_to_end_and_force`: tests the full `build_axiomc.main()` seam end-to-end (`ensure_stage0` -> `bootstrap.main` -> copying `axiomc2.exe.inputs.json` to `axiomc.exe.inputs.json` -> `axiomc2.exe version` smoke check), verifying reuse on the second run and stage-1/2 rebuild on `--force`.

### 4. Per-task gate (`tools/taskgate.py --task T444c`)

### taskgate T444c (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T444c`, HEAD `eca6645c7193`, compiler `D:/projects/compiler/new lang/build-snap-T444c/build/axiomc2.exe`, `-j 2`
- change set: 5 file(s) (working tree of build-snap-T444c vs HEAD)
  - `_workspaces/reports/T444c-report.md`
  - `tools/bootstrap.py`
  - `tools/build_axiomc.py`
  - `tools/tests/build_axiomc/run_selftests.py`
  - `tools/tests/build_axiomc/test_build_axiomc.py`
- wall time: 164.6 s (axtest 10.0 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| affected | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| smoke | 30 | 49 | 49 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 30 | 49 | 49 | 0 | 0 | 0 | 0 |

Counts per group:

| group | ids | failing | parts |
|---|---|---|---|
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
| typeck | 1 | 0 | smoke |
| ui | 1 | 0 | smoke |
| unit | 1 | 0 | smoke |
| verify | 1 | 0 | smoke |

Affected-set derivation (rule per id; rules in `tools/axtest_affected.py`):

- tool self-tests `tools/tests/archcheck` <- tools: test_archcheck.py names tools/bootstrap.py
- tool self-tests `tools/tests/build_axiomc` <- tools: run_selftests.py names tools/bootstrap.py
- tool self-tests `tools/tests/gatecheck` <- tools: test_gatecheck.py names tools/bootstrap.py
- tool self-tests `tools/tests/taskgate` <- tools: test_taskgate.py names tools/bootstrap.py
- no-op (select nothing): `_workspaces/reports/T444c-report.md`
- unmatched changed files: none

Smoke: seed=406956181, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`; picks conformance=`conformance/p5/0114_prog_a_hello.ax`, diff=`diff/opt/const_fold.ax`, driver=`driver/no_args.test`, encode=`encode/axiom/qa_encode_reloc_and_sym.ax`, fuzz=`fuzz/qa_seed_test.ax`, hir=`hir/types.ax`, inspect=`inspect/async_layout.test`, lex=`lex/L02_tuple_index.ax`, link=`link/lib/coff_lib.test`, link2=`link2/multi_mod_pkg`, lir=`lir/div.test`, mc=`mc/regalloc/fixed_regs_o2.ax`, mir=`mir/int128/shift_i8_rhs_check.test`, modules=`modules/std_root.test`, obj=`obj/determinism/string_symbols.test`, opt=`opt/const_fold_run.ax`, opt2=`opt2/inline_scc_and_attributes.ax`, parse=`parse/async/async_fn_and_await.ax`, perf=`perf/loop.ax`, programs=`programs/expr_interp.ax`, resolve=`resolve/R01_basic.ax`, run=`run/numeric/qa_div_zero.ax`, selfhost=`selfhost/intrinsics/qa_intrinsic_seams.ax`, std=`std/core/qa_mem.ax`, typeck=`typeck/async/await_outside_async_neg.ax`, ui=`ui/typeck/type_unknown.ax`, unit=`unit/kernel/hash_vectors_current.test`, verify=`verify/drop/cond_drop_flag_ok.test`

Cache: CACHED 0, miss 0, uncacheable 11, stored 0, dep_source exact, verification sample seed=1714515607 n=19 of 19 hits, mismatch none, rejected {}, producer snapshot
WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests
Baseline (`D:\projects\compiler\new lang\build-snap-T444c\_workspaces\baseline-failures.txt`): BASELINE OK
Failing ids: none
Tool self-tests: `tools/tests/archcheck` PASS (SELFTEST 55 tests, 0 failures, 0 errors, 6.0 s); `tools/tests/build_axiomc` PASS (SELFTEST 25 tests, 0 failures, 0 errors, 2.9 s); `tools/tests/gatecheck` PASS (SELFTEST 39 tests, 0 failures, 0 errors, 35.8 s); `tools/tests/taskgate` PASS (SELFTEST 44 tests, 0 failures, 0 errors, 93.5 s)
archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations
axtest: `TOTAL 49 PASS 49 FAIL 0 SKIP 0 XFAIL 0` (exit 0)

TASKGATE T444c exit=0

## Files changed
- tools/tests/build_axiomc/test_build_axiomc.py

### 5. Findings
None.

VERDICT: PASS round=0
