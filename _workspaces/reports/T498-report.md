# T498 report
## Summary
`[N]T` is Copy iff `T` is Copy (SPEC-10 AXS-OWN-003, ADR-0044 §3). Root cause confirmed as the architect
found it: `mb_operand_from_place` in `compiler/mir/builder.ax` forced `is_cp = false` for every `TY_ARRAY`
and emitted `MIR_OP_MOVE`, so the MIR verifier reported `AX_VERIFY_USE_AFTER_MOVE` on the second use. It now
asks `mb_type_is_copy` (which calls `type_is_copy`) for arrays. `str` still moves, and arrays of a non-Copy
element still move. Every builder path that reads a whole array from a place (`let b = a`, call
arguments, return, `[N][M]T`, array field `r.vals`) goes through this function. Temporaries built from
rvalues are still moved, which is correct because they are used once. Nothing else in the builder
special-cases arrays for ownership: `mb_emit_index_bounds_check` and drop enqueueing look at array type
for other reasons. The interpreter, own checker, optimizer and LIR treat `COPY` and `MOVE` of an
aggregate the same way (same load/store), so this change caused no new problems downstream. The bugs
found below already existed with `MOVE`.

The stage-2 == stage-3 fixed point holds (`FIXED-POINT (O1) OK`, seeded B==C; stage-0 guard OK).

## Files changed
- compiler/mir/builder.ax
- tests/run/numeric/mixed_int_matrix/array_copy.ax
- tests/run/array_copy/copy_bindings_args_return.ax
- tests/run/array_copy/nested_and_field.ax
- tests/run/array_copy/large_and_edge.ax
- tests/run/array_copy/zero_len.ax
- tests/ui/array_copy/noncopy_elem_twice.ax
- tests/ui/array_copy/noncopy_elem_bind_twice.ax
- _workspaces/reports/T498-report.md

## Tests
All runs used the snapshot `build-snap-T498`, with stage-0 built by clang Release and `tools/build_axiomc.py --out build`.
- `axtest --compiler build/axiomc2.exe --no-cache run/array_copy ui/array_copy mixed_int_matrix/array_copy`:
  TOTAL 17 PASS 17 FAIL 0, WEAK-NATIVE 0. `mixed_int_matrix/array_copy.ax` was XPASS before the `xfail` line
  was removed and now passes in interp, native and native-O1.
- `tools/taskgate.py --task T498 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  `TOTAL 362 PASS 360 FAIL 0 SKIP 2`, archcheck clean, BASELINE OK, no failing ids, WEAK-NATIVE 0 in the
  task's own and changed tests, `TASKGATE T498 exit=0` (log `_workspaces/T498_taskgate.log`).
- Acceptance groups `run/numeric conformance/p12 conformance/vs0 selfhost/mir selfhost/own`: see the
  "Acceptance groups" line below.

## Spec deviations
- The ui tests expect `AX_MOVE_USE_AFTER_MOVE`, not `AX_VERIFY_USE_AFTER_MOVE`. With a non-Copy element
  array, the own checker (`compiler/own/init.ax`) rejects the second use before MIR verification runs, so
  `AX_MOVE_USE_AFTER_MOVE` is what the user sees. Both codes mean the same rule. The verifier code is
  only a backstop for MIR the checker accepted.

## Follow-ups
1. **FU-T498-FNPTR-INDEX (own/init, a different root cause from T498):** the T422b QA repro
   `let a = hs[0].f; let b = hs[1].f;` (`hs: [2]H`, `H` not Copy, `f: fn(i32) -> i32`) still reports
   `AX_MOVE_USE_AFTER_MOVE`. The MIR is correct (`_5 = copy ((_4)[_6]).1`). The bug is in
   `own_bits_resolve` in `compiler/own/init.ax`: it skips `MIR_PROJ_INDEX` and keeps resolving the
   following `FIELD` projection against the array node, so `hs[i].1` is treated as `hs.1` / `hs`. Also,
   `own_bits_visit_operand` handles COPY like MOVE. The node is the non-Copy array, so it is marked moved.
   Fix: stop resolving at INDEX and do not move on a COPY operand through an index. A move out of an
   indexed non-Copy element must still be rejected. This is outside T498's paths and needs a task owning
   `compiler/own/init.ax`. Every Copy field read through an index of a non-Copy array is affected, not
   only fn pointers.
2. **FU-T498-INTERP-ARG256 (interp):** the oracle passes by-value call arguments in an `InterpValue`
   (`vals: [32]u64`, 256 bytes, `compiler/interp/value.ax`), so any argument larger than 256 bytes is cut
   off. For example, `fn f(a: [300]u8)` sees only the first 256 bytes, while native is correct. This bug
   existed before T498 (it reproduces with the HEAD compiler and with MOVE). The test
   `tests/run/array_copy/large_and_edge.ax` therefore copies the 1 KiB and 4 KiB arrays by binding and reads
   them through a `view`. Once this is fixed, add a run test with a by-value `[1024]u8` argument.
3. **FU-T498-AGG-WIDEN (LIR or native lowering):** in native code, a 3-, 6- or 7-byte aggregate is loaded and
   stored with a widened scalar width (4 or 8 bytes) and overwrites the next field. Repro:
   `struct Rec { tag: u8, vals: [3]u16 }` laid out as vals@0 (6 bytes) and tag@6;
   `Rec { tag: 4u8, vals: [5, 10, 15] }` followed by reading `r.tag` prints 0 natively and 4 in interp.
   The LIR stores `vals` with `load`/`store` of 8 bytes after storing `tag`. `[3]u8` next to a u8 fails the
   same way. This also existed before T498 and is a silent miscompile, so the priority is high.
   `nested_and_field.ax` uses `[4]u16` to avoid it.

Acceptance groups (`axtest --gate --exclude-requires axiom0-internal -j 2 run/numeric conformance/p12
conformance/vs0 selfhost/mir selfhost/own`, log `_workspaces/T498_groups.log`): TOTAL 1541 PASS 1541 FAIL 0,
WEAK-NATIVE 0.

STATUS: COMPLETE round=0
