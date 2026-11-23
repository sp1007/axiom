# T423i — Fix `fullrun-4` R2 (`link/dll/gnu_ld_run.test` host-provider archive & multi-file `--emit=obj` private-fn `SYM_LOCAL`)

## Summary
- Updated `driver_emit_objmodel_filtered_ex` in `compiler/driver/pipeline.ax` so multi-file per-module `--emit=obj` emissions (`for_obj && filter_fid_v != 0u32`) bind module-private functions (`vis.kind == 0u8`, `!has_export`, `!pipe_item_has_entry_attr(...)`, `!pipe_sv_is_main(...)`, `!pipe_sv_has_dollar(...)`) as `SYM_LOCAL` (`IMAGE_SYM_CLASS_STATIC`), matching `for_lib` and preventing symbol collisions between private helpers (e.g., `fn_entry_to_addr`, `fn_exit_to_addr`, `addr_to_fn_exit`) in `std/sys/windows/thread.ax` and `std/sys/windows/fiber.ax`. Single-file `--emit=obj` (`filter_fid_v == 0u32`) and `axiom_rt.obj` remain byte-for-byte unchanged.
- Updated `tests/link/dll/gnu_ld_run_oracle.py` to:
  1. Compile all 7 `std/sys/windows/*.ax` host-provider modules (`heap`, `io`, `fs`, `process`, `time`, plus `thread` with `fiber.ax` and `fiber` with `thread.ax`) into relocatable `.obj` files, validate each via `inspect_coff_external_symbols`, and pack them into `axiom_host_rt.lib` via `axiomc build --kind lib`.
  2. Pass `axiom_host_rt.lib` to GNU `ld` in `verify_test` after `prog.obj` and `axiom_rt.obj` and before MinGW import libraries (`-L ... -lkernel32 ...`).
  3. Extend the `gcc -nostdlib` smoke section to cross-link and execute a program calling `std.core.host.heap_alloc`, `std.core.host.heap_free`, `std.core.host.thread_yield`, and `std.core.host.fiber_destroy` against `axiom_rt.obj` + `axiom_host_rt.lib` (`-lkernel32` and `-lsynchronization` when available).

## Files changed
- `compiler/driver/pipeline.ax`
- `tests/link/dll/gnu_ld_run_oracle.py`

## Verification (in isolated snapshot `build-snap-T423i/`)
- Stage-2/3 build (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6` (8,686,592 bytes)
  - `STAGE0-GUARD OK`
- Targeted `axtest` (`--no-cache -j 2 -v link/dll/gnu_ld_run.test link/dll/rt_tls_and_std_reachability.test link/dll/qa_t431_tls_and_std_reachability_bounds.test link/lib/coff_lib.test`):
  - `TOTAL 4 PASS 4 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
- `taskgate` (`python tools/taskgate.py --task T423i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TASKGATE T423i exit=0`
  - `TOTAL 170 PASS 170 FAIL 0 SKIP 0 XFAIL 0`
  - `BASELINE OK`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `archcheck: 232 files scanned, 0 violations`

STATUS: COMPLETE round=0
