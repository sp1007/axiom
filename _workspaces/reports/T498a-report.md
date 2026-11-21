# T498a report

## Summary
I reproduced the bug on HEAD 6d190d4, which T498's QA could not do. With the HEAD axiomc2 (sha256 88fa98f2...), the exact T498 program
(`tests/run/agg_odd_size/repro.ax`) prints `0` natively at O0 and O1 and `4` in interp. Five of the six new tests and the
restored `[3]u16` version of `tests/run/array_copy/nested_and_field.ax` fail natively at HEAD. Only the 12-byte no-regression
test passes. T498's QA variants probably passed because a whole-struct copy reads the neighbouring bytes
along with the widened field: the 8-byte load from the source and 8-byte store to the destination write `tag` back unchanged. The clobber shows only where the
6-byte value comes from a separate temporary: a struct literal, `s.x = [..]` or an element store `a[i] = ..`.

**Root cause**: in `compiler/target/x64/isel.ax`, both instruction selectors widen these accesses:
- O0 (`x64_isel_raw_in_arena`): `LIR_INST_LOAD` and `LIR_INST_STORE` handled every size `<= 8` with a single access and
  rounded a size that is not 1/2/4/8 up to 8 (`load_sz = 8u32` / `size = 8u32`). The indirect `LIR_INST_ABI_RESULT` in
  `isel_raw_lower_abi` did the same.
- O1: `isel_opt_lower_load_store_inst` (LOAD and STORE, in both the direct-stack-slot and the general address form) and
  `LIR_INST_ABI_RESULT` in `isel_opt_lower_abi_call_inst` widened the same way.
So a store of a 3/5/6/7-byte aggregate wrote 1 to 5 bytes past its end, into the next field, element or stack slot.
A load read past its end. objdump of the repro at HEAD shows `mov QWORD PTR [rax],rcx` for the `vals` store. The fixed build emits
`mov DWORD PTR [rax],ecx; shr rcx,0x20; mov WORD PTR [rax+0x4],cx`.

**Fix**: only isel changed. The LIR builder, ABI and frame code needed no change, and the locked files are untouched.
- `isel_size_is_odd_aggregate(size)` returns true for 3, 5, 6 and 7.
- `isel_emit_odd_store_mem` / `isel_emit_odd_store_slot` store the low `size` bytes of RCX as 4+2+1 pieces
  (`isel_chunk_size` decomposition) and shift RCX right between pieces.
- `isel_emit_odd_load_mem` / `isel_emit_odd_load_slot` set RCX = 0, then build the value from the top byte down with 1- and
  2-byte loads and `shl rcx,16`. A 1- or 2-byte load keeps the upper bits of RCX; a 4-byte load would clear them. The vreg slot
  receives the value zero-extended to 8 bytes, and nothing past the object is read.
- All six sites above use these helpers. The O1 odd-size STORE path does not set the RCX cache tag, because RCX is shifted.
- Win64 passes and returns 3/5/6/7-byte aggregates by reference. The `abi/win64.ax` classification and
  `isel_type_is_ret_in_mem` agree on this, and the by-reference copy loops (indirect `ABI_ARG`) already used exact chunks.
- `tests/run/array_copy/nested_and_field.ax` is back to the `[3]u16` field its author wanted.

The fixed point holds: `FIXED-POINT (O1) OK` dafee55d... (seeded B==C) and `STAGE0-GUARD OK`.

## Files changed
- compiler/target/x64/isel.ax
- tests/run/agg_odd_size/repro.ax
- tests/run/agg_odd_size/u8_arrays.ax
- tests/run/agg_odd_size/u16_arrays.ax
- tests/run/agg_odd_size/tuple_and_array.ax
- tests/run/agg_odd_size/pass_return_copy.ax
- tests/run/agg_odd_size/size12_tail4.ax
- tests/run/array_copy/nested_and_field.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax.in
- _workspaces/reports/T498a-report.md

## Tests
Everything ran in `build-snap-T498a/`. Stage-0 was built with clang 22 Release. `build_axiomc.py --out build` reported STAGE1 OK, SEED/STAGE2/STAGE3 (O1) OK,
`FIXED-POINT (O1) OK` and `STAGE0-GUARD OK` (log `_workspaces/T498a_build2.log`).
- Reproduction at HEAD (HEAD axiomc2 88fa98f2..., `axtest --no-cache run/agg_odd_size`): all 10 native and native-O1 legs of
  repro, u8_arrays, u16_arrays, tuple_and_array and pass_return_copy FAIL. Examples: repro prints `0\n0 5 10 15` instead of
  `4\n4 5 10 15`; a `[3]R3` element store zeroes the next element; the `[7]u8` store zeroes `g`. Interp passes and
  size12_tail4 passes. With `[3]u16`, `run/array_copy/nested_and_field.ax` FAILS its native legs at HEAD.
- Fixed compiler, `axtest --no-cache run/agg_odd_size run/array_copy`: TOTAL 39 PASS 39 FAIL 0, WEAK-NATIVE 0.
- objdump of the repro exe: HEAD emits `mov QWORD PTR [rax],rcx`. The fixed build emits `mov DWORD PTR [rax],ecx; shr rcx,0x20;
  mov WORD PTR [rax+0x4],cx`, and its loads are `mov cx,[..+4]; shl rcx,0x10; ...`.
- Full taskgate (`tools/taskgate.py --task T498a ... -j 2`, log `_workspaces/T498a_taskgate.log`, wall 335 s):
  TOTAL 206 PASS 191 FAIL 3 SKIP 12. archcheck is clean and WEAK-NATIVE is 0 in the task's own tests. **New failure:
  `selfhost/isel/qa_isel_all.ax`** (3 legs): check `qa_isel_frame_seam_and_edge_cases` returns 203. Its unit test
  `test_non_pow2_small_aggregate_and_closure_call` asserts the buggy behaviour itself: "LOAD [6]u8 ... size 6 promoted to
  8-byte MOV" and "STORE [6]u8 ... promoted to 8-byte MOV" (it fails when `size != 8u8`). It also checks fixed MI indices.
- With the corrected expectations below (applied in the snapshot only, bundle regenerated in the snapshot):
  `axtest --no-cache selfhost/isel` gives TOTAL 4 PASS 4.
- Acceptance groups, with the patched template in the snapshot (`axtest --gate -j 2 run/ conformance/p12 conformance/vs0 selfhost/lir selfhost/x64 selfhost/isel
  selfhost/encode`, log `_workspaces/T498a_groups.log`):
  TOTAL 3646 PASS 3646 FAIL 0. WEAK-NATIVE is 122 for the whole run and 0 in run/agg_odd_size and nested_and_field. The taskgate also
  reported 0 in the task's own and changed tests.

## Selfhost isel unit check updated
`tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax.in` is a hand-written template, not a generated bundle. Its check
encoded the buggy 8-byte access. The orchestrator added the file to this task's `paths`, and the patch below is applied in the main tree.
The updated test expects:
- 2-byte loads at +4 and +0;
- a 4-byte store at +0 and a 2-byte store at +4;
- no 8-byte `[mem]` MOV anywhere in the block;
- the shifted MI indices: LOAD 3..10, STORE 11..15, CALL 16..18.

Round 2 taskgate, after `taskctl snapshot T498a` regenerated the bundles; the axiomc build was REUSED (sha256 dafee55d...):
`TOTAL 203 PASS 191 FAIL 0 SKIP 12`, `BASELINE OK`, no failing ids, archcheck clean, WEAK-NATIVE 0 in the task's own and changed
tests (log `_workspaces/T498a_taskgate2.log`, wall 351 s).

```diff
-        // inst 1: LOAD [6]u8 from ptr vreg 0 -> size 6 promoted to 8-byte MOV without shift truncation
+        // inst 1: LOAD [6]u8 from ptr vreg 0 -> exact-width 2+2+2 loads into RCX (T498a: never an 8-byte access)
-        // inst 2: STORE [6]u8 from vreg 1 to ptr vreg 0 -> size 6 promoted to 8-byte MOV
+        // inst 2: STORE [6]u8 from vreg 1 to ptr vreg 0 -> exact-width 4+2 stores (T498a)
-        // inst 4: ABI_RESULT INDIRECT for [6]u8 -> single 8-byte load/store pair
+        // inst 4: ABI_RESULT INDIRECT for [6]u8 -> exact-width loads, one 8-byte store to the vreg slot
 (checks: replace from "// LOAD [6]u8: insts 3..6" up to and including the m_call binding with)
+    // LOAD [6]u8 (T498a): inst 3 MOV RAX, [frame#1]; 4 MOV RCX, 0; 5 MOV (sz=2) RCX, [RAX+4]; 6 SHL RCX, 16;
+    // 7 MOV (sz=2) RCX, [RAX+2]; 8 SHL RCX, 16; 9 MOV (sz=2) RCX, [RAX+0]; 10 MOV [frame#2], RCX
+    let m_ld_hi = unsafe { bb_inst_at(mbb0, 5) };
+    let m_ld_lo = unsafe { bb_inst_at(mbb0, 9) };
+    let m_load_store = unsafe { bb_inst_at(mbb0, 10) };
+    if (unsafe { (*m_ld_hi).opcode }) != X64_MI_MOV || (unsafe { (*m_ld_hi).size }) != 2u8 ||
+       (unsafe { (*m_ld_hi).ops[1].kind }) != X64_OP_MEM || (unsafe { (*m_ld_hi).ops[1].mem.disp }) != 4 ||
+       (unsafe { (*m_ld_lo).opcode }) != X64_MI_MOV || (unsafe { (*m_ld_lo).size }) != 2u8 ||
+       (unsafe { (*m_ld_lo).ops[1].mem.disp }) != 0 ||
+       (unsafe { (*m_load_store).opcode }) != X64_MI_MOV || (unsafe { (*m_load_store).ops[0].kind }) != X64_OP_FRAME {
+        return 203;
+    }
+    // STORE [6]u8 (T498a): 11 MOV RAX, [frame#1]; 12 MOV RCX, [frame#2]; 13 MOV (sz=4) [RAX], RCX; 14 SHR RCX, 32;
+    // 15 MOV (sz=2) [RAX+4], RCX
+    let m_st_lo = unsafe { bb_inst_at(mbb0, 13) };
+    let m_st_hi = unsafe { bb_inst_at(mbb0, 15) };
+    if (unsafe { (*m_st_lo).opcode }) != X64_MI_MOV || (unsafe { (*m_st_lo).size }) != 4u8 ||
+       (unsafe { (*m_st_lo).ops[0].kind }) != X64_OP_MEM || (unsafe { (*m_st_lo).ops[0].mem.disp }) != 0 ||
+       (unsafe { (*m_st_hi).opcode }) != X64_MI_MOV || (unsafe { (*m_st_hi).size }) != 2u8 ||
+       (unsafe { (*m_st_hi).ops[0].mem.disp }) != 4 {
+        return 204;
+    }
+    // No access through a register base may be wider than the 6-byte aggregate.
+    let mut cur_mi = unsafe { (*mbb0).first_inst };
+    while (cur_mi as usize) != 0 {
+        let k0 = unsafe { (*cur_mi).ops[0].kind };
+        let k1 = unsafe { (*cur_mi).ops[1].kind };
+        if (unsafe { (*cur_mi).opcode }) == X64_MI_MOV && (k0 == X64_OP_MEM || k1 == X64_OP_MEM) &&
+           (unsafe { (*cur_mi).size }) == 8u8 {
+            return 206;
+        }
+        cur_mi = unsafe { (*cur_mi).next };
+    }
+    // CALL closure: inst 16 is MOV RCX, [frame#1 + 0]; inst 17 is MOV R10, [frame#3 + 0]; inst 18 is CALL R10
+    let m_sret = unsafe { bb_inst_at(mbb0, 16) };
+    let m_call = unsafe { bb_inst_at(mbb0, 18) };
```

## Spec deviations
none

## Follow-ups
- `inspect --emit=mc` prints every MOV of the repro with a REX.W 8-byte encoding (`48 8b 48 04`, `48 89 08`), but the
  real `build` output uses the correct widths (`66 89 08`, `89 08`). The mc dump does not show the operand size. This is a low-priority
  triage item in the inspect emitter, unrelated to this miscompile, and it occurs with both HEAD and the fixed compiler.

STATUS: COMPLETE round=0
