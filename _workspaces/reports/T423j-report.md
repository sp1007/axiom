# T423j — GNU ld cross-link oracle links the async I/O host providers

## Root cause
`tests/link/dll/gnu_ld_run_oracle.py` step 1b builds `axiom_host_rt.lib` from the Windows host-provider modules
(`std/sys/windows/*.ax`). Its provider list had heap, io, fs, process, time, thread and fiber but not `iocp.ax`, the
only module that defines the `__ax_host_aio_*` functions (IOCP and Winsock reactor). The in-house linker links the
same programs because `pipe_add_host_providers` (`compiler/driver/pipeline.ax`) adds the provider module on demand
for a linked exe or dll. With `--emit=obj` (`pipe_wants_host_providers` returns false) the object only references
`__ax_host_aio_*`, so the oracle has to supply them. The five T428a tests under `tests/run/async/addr_stable_locals/`
are the first `tests/run` programs to use the real reactor, which is why the symbols `__ax_host_aio_close` and
`__ax_host_aio_cancel` were reported undefined.

The compiler is correct, so `compiler/driver/pipeline.ax` was not touched.

## Fix
`tests/link/dll/gnu_ld_run_oracle.py`: added `("iocp", [win_sys_dir / "iocp.ax"])` to `provider_specs`, so it is
compiled to an object and packed into `axiom_host_rt.lib`. No test is skipped and there is no exclusion list.
`_workspaces/baseline-failures.txt`: removed the `link/dll/gnu_ld_run.test` line and left a note in the comment.

## Verification (snapshot `build-snap-T423j/`)
The snapshot was configured as Release. A Debug axiom0 overflows the stack at stage 1 (rc 0xC00000FD), the same as
the other snapshots, which use Release.
- `python tools/build_axiomc.py --out build --root . --stage 2`: `FIXED-POINT (O1) OK`,
  sha256 `ab15b62bbfdd21dc70f505f948585436c395b28d444d97e139f26fb20feac744`. The compiler is unchanged by this task,
  so this only confirms a fresh compiler from HEAD.
- `python tools/axtest.py --no-cache -j 2 -v --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal link/dll/gnu_ld_run.test`:
  `PASS link/dll/gnu_ld_run.test` (`TOTAL 1 PASS 1 FAIL 0`).
- `python tools/taskgate.py --task T423j --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`
  (log `_workspaces/T423j_taskgate.log`): `TOTAL 63 PASS 63 FAIL 0`, failing ids none, archcheck clean,
  smoke OK. It reports `BASELINE NOW PASSING: link/dll/gnu_ld_run.test`. The snapshot does not copy lock files, so it
  used the old baseline file; the removed line is the one that now passes.

## Spec deviations / questions
None.

## Files changed
- tests/link/dll/gnu_ld_run_oracle.py
- _workspaces/baseline-failures.txt
- _workspaces/reports/T423j-report.md

STATUS: COMPLETE round=0
