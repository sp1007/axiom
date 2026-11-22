# T498c report — the oracle passes by-value aggregates of any size

## Summary
The MIR interpreter put every by-value call argument into a fixed 256-byte `InterpValue` slot
(`vals: [32]u64`). `prepare_call_args_from_term` cut the copy at 256 bytes and `frame_init` copied 256 bytes
into the parameter, so `fn f(a: [1024]u8)` saw only the first 256 bytes. A closure capture above 256 bytes was
worse: it was copied into its slot at full size, which wrote past the slot.

## Design
- The call-argument buffer is still `n` InterpValue slots, so the inline fast path for values up to 256 bytes
  does not change. A larger value is copied byte-exact into a **spill area appended to the same buffer**,
  and the buffer grows when that happens. The value's slot holds a descriptor:
  `vals[0]` = byte offset from the buffer start, `vals[1]` = size, `vals[2]` = `INTERP_ARG_SPILL_MAGIC`.
  - Offsets, not pointers, so the descriptor stays valid when the buffer is reallocated.
  - The spill area lives in the same allocation, so each existing
    `heap_free(call_args, args_bytes, align_of<InterpValue>())` frees it with no extra bookkeeping.
    `prepare_call_args_from_term` returns the final pointer and returns the grown size through `out_args_bytes`.
- `value.ax`: `interp_arg_store` (inline or spill) and `interp_arg_load` (copies a spilled argument in full,
  up to the parameter's storage size, otherwise the slot).
- `frame.ax` `frame_init`: takes the parameter's storage size from the local layout (the distance to the next
  local, or to the end of storage) and calls `interp_arg_load`. It does not call `type_size` again. It reads
  the descriptor only when the parameter storage is larger than a slot and the magic matches. Small
  parameters therefore can never be misread, and a caller that does not spill falls back to the old slot
  copy. Today the thread entry, fiber, drop-glue and `main` callers only pass scalars.
- `interp.ax` `prepare_call_args_from_term`: both closure captures and terminator arguments go through
  `interp_arg_store`. No size is clamped any more.
- There is no hard cap. The spill size is the argument's own type size, so no interpreter-limit diagnostic is
  needed.
- Return values were already correct for MIR calls: the caller allocates `max(dest_sz, 256)` and
  `frame_cleanup` copies the full return local. The sched path copies `caller_dest_sz`. The new tests cover a
  4 KiB array and a 616-byte struct returned by value.
- Paths checked that need no change:
  - Enum, tuple and struct construction and closure-object construction copy through place pointers, not
    through `InterpValue`.
  - `eval_operand`'s 256-byte clamp only applies to const operands, which are scalars or strings.
  - The intrinsic paths read only the scalar `vals[0]`/`vals[1]`.

## Tests (`tests/run/interp_big_args/`, all modes interp / native / native-O1, exact `// stdout:`)
- `array_args.ax`:
  - `[255]u8`, `[256]u8`, `[257]u8`, `[300]u8`, `[1024]u8` and `[4096]u8` by value, checking the element count
    and the last-element tag.
  - Scalars before and after a spilled `[300]u8` argument (slots after a spill).
  - `[1024]u8` passed twice sums to 1024.
- `struct_self_return.ax`:
  - A 616-byte struct built and returned by value, then passed by value.
  - By-value `self` method, and a by-value `self` method that returns a new big struct.
  - A `[4096]u8` returned by value.
- `enum_closure.ax`:
  - Tuple variant payload `([300]u8, u32, u64)` passed by value and matched.
  - `Option<[1024]u8>` passed by value.
  - A closure capturing a `[300]u8`, and a closure taking a `[300]u8` argument alongside a capture.
- Regression proof: the HEAD-equivalent compiler `_workspaces/artifacts/compiler-cache/axiomc2_O1_b64ea0de4626c290.exe`
  (same interp sources as HEAD) fails all three files in `[interp]`. It prints `256` for `[257]u8`/`[300]u8`,
  `244` of 600 for the struct, and `236` of 300 for the enum payload. Native passed already.

## Results (snapshot `build-snap-T498c`, HEAD 01ab165 + T498c, stage-0 clang Release)
- `tools/build_axiomc.py --out build --stage 3`:
  - STAGE1 OK.
  - `FIXED-POINT (O1) OK` with axiomc2 == axiomc3, sha256 `861fde14...`.
  - `STAGE0-GUARD OK`.
  - Log: `_workspaces/T498c_build.log`.
- `axtest --no-cache run/interp_big_args`: TOTAL 9 PASS 9, WEAK-NATIVE 0.
- `tools/taskgate.py --task T498c --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  - TASKGATE exit 0, `TOTAL 142 PASS 142 FAIL 0`, BASELINE OK.
  - archcheck clean (232 files).
  - WEAK-NATIVE 0 in the task's own/changed tests.
  - Log: `_workspaces/T498c_taskgate.log`.
  - The first gate run failed 4 `bundles_current.test` because the snapshot bundles were stale after I removed
    an unused import. Refreshing the snapshot fixed it, and the compiler binary did not change.
- `axtest --exclude-requires axiom0-internal -j 2 run conformance/p12 selfhost/interp selfhost/interp_opt`:
  - `TOTAL 3525 PASS 3525 FAIL 0`.
  - WEAK-NATIVE 125, all in existing tests outside this change.
  - Log: `_workspaces/T498c_suites.log`.
- Interp speed: `run --interp` wall time, old (HEAD-equivalent cache compiler) vs new, interleaved, minimum of
  N runs. The machine was shared with other tasks. Log: `_workspaces/T498c_timing.log`.

  | Bundle | Runs | Old (s) | New (s) | Change |
  |---|---|---|---|---|
  | `selfhost/lex/qa_lex_all.ax` | 3 | 1.80 | 1.67 | -7.4 % |
  | `selfhost/parse/qa_parse_interp.ax` | 3 | 16.25 | 16.40 | +0.9 % |
  | `selfhost/typeck/qa_typeck_all.ax` | 5 | 45.74 | 44.86 | -1.9 % |

  A first 3-run typeck sample showed +17.7 % (old 53–67 s, new 63 s). That is machine noise: the 5-run
  repeat shows -1.9 %. Stdout is identical in every run. There is no measurable slowdown, because the fast
  path is unchanged and the spill branch only runs for arguments above 256 bytes.

## Spec deviations
none

## Follow-ups
- `tests/run/array_copy/large_and_edge.ax` (T498) has a comment saying large arrays are read through a view
  because of the 256-byte oracle limit. That limit is gone. The file is not in this task's paths, so the
  comment is left as is.

## Files changed
- compiler/interp/value.ax
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- tests/run/interp_big_args/array_args.ax
- tests/run/interp_big_args/struct_self_return.ax
- tests/run/interp_big_args/enum_closure.ax
- _workspaces/reports/T498c-report.md

STATUS: COMPLETE round=0
