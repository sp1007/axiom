# T423i QA Gate Report

## Round 0

### 1. Code & Diff Audit
- **`compiler/driver/pipeline.ax`** (`driver_emit_objmodel_filtered_ex`, lines 7726–7736):
  - Verified `restrict_private = for_lib || (for_obj && filter_fid_v != 0u32)` restricts module-private functions (`vis.kind == 0u8`, `!has_export`, `!pipe_item_has_entry_attr`, `!pipe_sv_is_main`, `!pipe_sv_has_dollar`) to `SYM_LOCAL` (`IMAGE_SYM_CLASS_STATIC`) ONLY for `--kind lib` or multi-file per-module `--emit=obj` (`user_file_count > 1` -> `filter_fid_v != 0u32`).
  - Verified single-file `--emit=obj` (`filter_fid_v == 0u32`), `main`, `@export`, `@entry`, `pub`, `$`-qualified symbols, and `axiom_rt.obj` (`pe_build_runtime_coff_obj`) remain untouched.
- **`tests/link/dll/gnu_ld_run_oracle.py`**:
  - Section 1b (lines 215–274): Compiles all 7 `std/sys/windows/*.ax` host providers (`heap`, `io`, `fs`, `process`, `time`, `thread`+`fiber.ax`, `fiber`+`thread.ax`) with `--emit=obj`, validates each with `inspect_coff_external_symbols`, and packs `axiom_host_rt.lib` deterministically via `build --kind lib`.
  - Section 2 (lines 330–403): Cross-links and executes `gcc_host_smoke.ax` calling `std.core.host.{heap_alloc,heap_free,thread_yield,fiber_destroy}` against `axiom_rt.obj` + `axiom_host_rt.lib` (`-lkernel32`, `-lsynchronization` when present), checking `rc == 41` and `stdout == b"host-smoke-ok\n"`.
  - Section 3 (lines 488–511): Passes `axiom_host_rt.lib` on `ld_cmd` AFTER `prog.obj` and `axiom_rt.obj` and BEFORE MinGW import libraries (`-L ... -lkernel32 ...`).
- **`_workspaces/reports/T423i-report.md`**: Ends with `STATUS: COMPLETE round=0` and lists exact `## Files changed`.

### 2. Stage-2/3 Build & Fixed-Point Verification (in `build-snap-T423i/`)
- Command: `python tools/build_axiomc.py --out build --root . --stage 2`
- Result: `BUILD-AXIOMC OK: build/axiomc2.exe size=8686592 sha256=43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6` (exact match with engineer report).

### 3. Targeted `axtest` Verification (in `build-snap-T423i/`)
- Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v link/dll/gnu_ld_run.test link/dll/rt_tls_and_std_reachability.test link/dll/qa_t431_tls_and_std_reachability_bounds.test link/lib/coff_lib.test`
- Result: `TOTAL 4 PASS 4 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`:
  - `PASS link/dll/gnu_ld_run.test`
  - `PASS link/dll/qa_t431_tls_and_std_reachability_bounds.test`
  - `PASS link/dll/rt_tls_and_std_reachability.test`
  - `PASS link/lib/coff_lib.test`
- Confirmed all 10 `tests/run/host/{fs,heap,io}/*.ax` native run tests are discovered and verified by `gnu_ld_run.test`:
  `host/fs/clock.ax`, `host/fs/dir.ax`, `host/fs/file_io.ax`, `host/fs/metadata.ax`, `host/heap/provider_native.ax`, `host/io/args.ax`, `host/io/env.ax`, `host/io/exit7.ax`, `host/io/invalid_handle.ax`, `host/io/write_stdout_stderr.ax`.

### 4. Adversarial Boundary Checks & Native-Evidence Spot-Proof (in `build-snap-T423i/` only)
- **Single-file vs multi-file `--emit=obj` COFF symbol binding**:
  - Single-file `a.ax` (`--emit=obj`): private `fn helper()` emitted with `IMAGE_SYM_CLASS_EXTERNAL (2)` (unchanged).
  - Multi-file `a.ax b.ax` and `b.ax a.ax` (`--emit=obj`): colliding private `fn helper()` emitted with `IMAGE_SYM_CLASS_STATIC (3)` in both objects, while `pub_a`, `c_exp_a` (`@export`), `main`, and `pub_b` remained `IMAGE_SYM_CLASS_EXTERNAL (2)`.
  - Cross-linking `a_multi.obj + b_multi.obj + axiom_rt.obj` with `gcc -nostdlib -Wl,-e,axiom_start -lkernel32` succeeded with zero duplicate-symbol errors and exited with `rc=7`.
  - Inspected `thread.obj` and `fiber.obj`: private helpers (`fn_entry_to_addr`, `fn_exit_to_addr`, `addr_to_fn_exit`) are `STATIC (3)` in both; `__ax_host_thread_current_id` is defined `EXTERNAL (2)` in `thread.obj` (`sec=2`) and undefined `EXTERNAL (2)` in `fiber.obj` (`sec=0`).
- **Mutation spot-proof (in `build-snap-T423i/tests/link/dll/gnu_ld_run_oracle.py`, restored byte-identical)**:
  - Mutated `gcc_host_smoke.exe` expected exit code `41 -> 42` and ran `python tests/link/dll/gnu_ld_run_oracle.py build/axiomc2.exe build/_qa_t423i_tmp/mut_oracle .`
  - Result: failed immediately (`rc=1`, `gcc_host_smoke.exe mismatch: rc=41`), proving live native execution and exit-code checking. Restored `gnu_ld_run_oracle.py` byte-for-byte identical (verified by SHA-256) and removed temp dir.

### 5. `taskgate` Gate Run (in `build-snap-T423i/`)
- Command: `python tools/taskgate.py --task T423i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T423i.json`
- Result: `TASKGATE T423i exit=0`
  - Change set (7 files in snapshot vs HEAD `e4af877cc5d6`): `_workspaces/reports/T423i-report.md`, `compiler/driver/pipeline.ax`, `tests/link/dll/gnu_ld_run_oracle.py`, plus 4 regenerated selfhost bundles (`tests/selfhost/driver/qa_driver_full_{interp,native}.ax`, `tests/selfhost/obj_link_driver/qa_obj_link_driver_{diff,smoke}.ax`).
  - Scope: `own` 0, `affected` 72 ids (120 results), `smoke` 32 ids (55 results), dedup total 101 ids / 170 results.
  - `axtest`: `TOTAL 170 PASS 170 FAIL 0 SKIP 0 XFAIL 0` (exit 0), wall time 342.3 s.
  - `Cache`: CACHED 41, miss 4, uncacheable 50, stored 0, `dep_source=exact`, verification sample `n=20 of 47 hits`, `mismatch none`, `rejected {}`.
  - `WEAK-NATIVE`: 3 in the run; 0 in the task's own/changed tests.
  - `Baseline`: `BASELINE OK` (`Failing ids: none`).
  - `archcheck`: `clean (exit 0)` (`232 files scanned, 0 violations`).
  - `smoke-check (tests/smoke.list)`: `OK`.

### 6. Hygiene
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T423i`: 0 `REFUSED` (`stage _workspaces/reports/T423i-report.md`, `stage compiler/driver/pipeline.ax`, `stage tests/link/dll/gnu_ld_run_oracle.py`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

### Findings
None.

## Files changed
(none)

VERDICT: PASS round=0
