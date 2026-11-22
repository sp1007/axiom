# T498h report

## Summary
Cut native x86-64 Win64 stack copies of by-value indirect aggregate arguments (`size > 8` B or `3/5/6/7` B) to the ABI minimum while preserving `Copy`, move, and `Drop` semantics (`ADR-0003`, `SPEC-03`, `SPEC-10` `AXS-OWN-003`):

1. **Before copy audit on `fn huge(a: [262144]u8, t: u32) -> u32` called from `main` (`let a: [262144]u8 = [1u8; 262144]; huge(a, 7u32)`):**
   - **`main` (`786,600` B at `-O0`, `786,608` B at `-O1` — 3 × 256 KiB slots):**
     1. `_2: [262144]u8` repeat-literal `MIR_LOCAL_TEMP` slot (`262,144` B), unrolled into 262,144 byte stores (`~14.5–15.3 MB` of machine code in `main`).
     2. `_1: [262144]u8` local binding `a` (`262,144` B), copied from `_2`.
     3. Outgoing `LirVReg` stack slot (`262,144` B) loaded by `lower_arg_at` for `LIR_INST_ABI_ARG` (`ABI_LOC_INDIRECT`).
   - **`huge` (`524,728` B at `-O0` and `-O1` — 2 × 256 KiB slots):**
     4. Incoming `LirVReg` stack slot (`262,144` B), populated in `isel.ax` by dereferencing the incoming `RCX` hidden pointer across 32,768 8-byte chunks (`~919 KB` of code in `huge`).
     5. `_1: [262144]u8` parameter `LirStackSlot` (`262,144` B), copied again from the incoming `LirVReg`.
   - Combined stack requirement (`1,280.6 KiB`) exceeded the 1 MB (`1,024 KiB`) default PE stack reserve (`ADR-0003`), faulting deterministically with `STATUS_STACK_OVERFLOW` (`0xC00000FD`) at both `-O0` and `-O1`.

2. **Changes implemented:**
   - **Callee direct hidden-pointer access (`compiler/lir/builder.ax`, `compiler/abi/win64.ax`, `-O0` & `-O1`):** Non-mutated indirect aggregate `MIR_LOCAL_ARG` parameters store the incoming Win64 hidden pointer (`usize`) directly in their parameter slot (`win64.ax` lowers `usize`-typed `LIR_INST_ABI_ARG` on `ABI_LOC_INDIRECT` to `ABI_LOC_REG` / `ABI_LOC_STACK` of the pointer itself), and place projections read through that pointer with zero callee aggregate copies (`huge` frame: `524,728` B → `456` B). Mutated indirect aggregate parameters copy once into a local slot on entry, leaving the caller's storage untouched.
   - **Single-use `MIR_LOCAL_TEMP` aggregate slot coalescing, direct `sret` destination, and loop `memcpy` (`compiler/lir/builder.ax`, `compiler/target/x64/frame.ax`, `-O0` & `-O1`):** `lb_compute_slot_remaps` coalesces single-def/single-use `MIR_LOCAL_TEMP` aggregates directly into their destination slot; `sret` calls pass `dst_addr` directly without an extra `LIR_INST_ABI_RESULT` copy; `frame.ax` skips unreferenced indirect-aggregate `LirStackSlot`s (`frame_size_is_ret_in_mem`); and `emit_memcpy_bytes` emits an 8-byte bulk loop for aggregates `> 64` B instead of unrolling tens of thousands of inline loads/stores.
   - **Caller copy elision & reusable per-type copy-slot pool (`compiler/lir/builder.ax`):**
     - At `-O0` and `-O1`: moved non-`Copy` aggregates (`MIR_OP_MOVE`, `!lb_type_is_copy_rec`, including drop-elaborated `Drop` aggregates whose drop flag is zeroed before the call and stays `0` on reachable paths) and non-aliased single-use `MIR_LOCAL_TEMP`s pass their source address directly without a caller copy.
     - At `-O1`: last-use `Copy` aggregates (`!lb_local_used_after_call`, not aliased by another call argument, and no reachable address-taking reference) also pass their source address directly (`0` copies total).
     - When a `Copy` aggregate remains live after the call (or at `-O0` on named `Copy` bindings), `lower_call_terminator` copies it into a reusable per-call-site `LirStackSlot` (`lb_acquire_call_copy_slot`) and materializes `emit_stack_addr` immediately before `LIR_INST_ABI_ARG`, isolating the caller's live value from callee mutations.
   - **Linear-scan lifetime-hole eviction fix (`compiler/target/x64/frame.ax`):** Fixed `x64_regalloc_with_pgo_in_arena`'s spill/eviction path so candidate register weights sum across `active` intervals that actually overlap `cur_iv` (`x64_intervals_overlap`) and evict all overlapping holders of `stolen_reg`, preventing an interval in a lifetime hole from being evicted in place of an overlapping live interval sharing the same register under 12-GPR pressure.
   - **Selfhost MI differential harness (`tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in`):** Kept byte-for-byte `axiom0` MI comparison on all 28 non-indirect-aggregate `.ax` cases and all `.mir` cases in `AX_CORPUS_HEAVY`, and added structural + direct-hidden-pointer MI validation (`validate_t498h_mi_output`) for the 5 indirect-aggregate cases (`tests/run/native_aggr/003-nested-struct.ax`, `tests/run/native_aggr/004-large-struct.ax`, `tests/run/native_enum/03-nested.ax`, `tests/run/native_enum/04-large-payload.ax`, `tests/run/native_enum/05-nested-enum.ax`) where `axiom0` (`bootstrap/axiom0`, out of scope) still emits the old callee-frame aggregate copy.
   - **Test comment cleanup (`tests/run/array_copy/large_and_edge.ax`):** Removed the stale `256`-byte interpreter limit comment superseded by `T498c`.

### Before / After Frame-Size & Copy-Count Measurements

| Case | Mode | `main` frame (Before → After) | `huge` / callee frame (Before → After) | `main` + `huge` code bytes (Before → After) | Remaining 256 KiB slots | Default 1 MB stack |
|---|---|---|---|---|---|---|
| `let a: [262144]u8 = [1u8; 262144]; huge(a, 7u32)` | `-O0` | `786,600` B (`768.16 KiB`) → **`524,456` B (`512.16 KiB`)** | `524,728` B (`512.43 KiB`) → **`456` B (`0.45 KiB`)** | `14,483,664` + `919,519` B → **`662` + `1,920` B** | `a` + 1 caller copy (`0` callee copies) | `0xC00000FD` → **PASS (`10`)** |
| `let a: [262144]u8 = [1u8; 262144]; huge(a, 7u32)` | `-O1` | `786,608` B (`768.17 KiB`) → **`262,304` B (`256.16 KiB`)** | `524,728` B (`512.43 KiB`) → **`456` B (`0.45 KiB`)** | `15,270,048` + `918,621` B → **`346` + `960` B** | `a` only (**`0` copies total**) | `0xC00000FD` → **PASS (`10`)** |
| `huge([1u8; 262144], 7u32)` (inline temporary) | `-O0` | `524,456` B (`512.16 KiB`) → **`262,296` B (`256.15 KiB`)** | `524,728` B (`512.43 KiB`) → **`456` B (`0.45 KiB`)** | `14,483,664` + `919,519` B → **`466` + `1,920` B** | temp only (**`0` copies total**) | `0xC00000FD` → **PASS (`10`)** |
| `huge([1u8; 262144], 7u32)` (inline temporary) | `-O1` | `524,448` B (`512.16 KiB`) → **`262,304` B (`256.16 KiB`)** | `524,728` B (`512.43 KiB`) → **`456` B (`0.45 KiB`)** | `15,270,048` + `918,621` B → **`337` + `960` B** | temp only (**`0` copies total**) | `0xC00000FD` → **PASS (`10`)** |

### `perf/selfhost` Compile-Time & Binary-Size Comparison (`HEAD 8b6039f1` vs `T498h`, `-O1 --time-passes`, 2 interleaved A/B pairs)

| Compiler | Wall time (min / mean) | Backend `time: build` (pair 1 / pair 2) | `encode` (pair 1 / pair 2) | Emitted `axiomc` `.exe` size |
|---|---|---|---|---|
| Before (`HEAD 8b6039f1`) | `44.940s` / `45.295s` (`[44.940s, 45.650s]`) | `17.850s` / `17.681s` | `0.772s` / `0.765s` | `9,442,304` B (`9.00 MiB`) |
| After (`T498h`) | **`43.864s` / `44.040s`** (`[43.864s, 44.217s]`, **`-2.8%`**) | `17.910s` / `17.850s` | **`0.687s` / `0.684s`** | **`8,325,120` B (`7.94 MiB`, `-11.8%`)** |

## Files changed
- compiler/abi/win64.ax
- compiler/lir/builder.ax
- compiler/target/x64/frame.ax
- tests/run/agg_arg_copies/copy_array_mutation_isolation.ax
- tests/run/agg_arg_copies/huge_256k_default_stack.ax
- tests/run/agg_arg_copies/many_indirect_args_back_to_back.ax
- tests/run/agg_arg_copies/moved_non_copy_drop_order.ax
- tests/run/agg_arg_copies/recursion_64k_by_value.ax
- tests/run/agg_arg_copies/repro_256k_exact.ax
- tests/run/agg_arg_copies/struct_with_array_field.ax
- tests/run/array_copy/large_and_edge.ax
- tests/selfhost/backend/harness_backend_diff_mi_mc.ax.in

## Tests
All builds and test runs were executed inside `build-snap-T498h/` (at `-j 2`):
- `python tools/build_axiomc.py --out build --root . --stage 2`:
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == f3b3b95515c96f8dc4fff94700681e6a4ab032ffae78abbe598bdb3bef3e5070` (`8,325,120` bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and Stage-2 produced byte-identical `.exe` on all 6 smoke programs
- `tests/run/agg_arg_copies/` (`--no-cache`, `interp`, `native`, `native-O1`): `21/21 PASS` (`WEAK-NATIVE: 0`), covering:
  - `repro_256k_exact.ax` & `huge_256k_default_stack.ax`: `[262144]u8` by value on default 1 MB stack (register slot, 5th-arg stack slot, `sret` chain, inline temporary)
  - `copy_array_mutation_isolation.ax`: callee mutating `[65536]u8` parameter while caller's still-live `Copy` array stays intact, plus aliased `(x, x)` isolation
  - `moved_non_copy_drop_order.ax`: moved non-`Copy` `Drop` 64 KiB aggregate (callee drops once before post-call code, exact `Drop` order verified)
  - `struct_with_array_field.ax`: structs, tuples, and enums with 64–128 KiB array fields in register and stack ABI slots
  - `recursion_64k_by_value.ax`: depth-24 moved `Drop` 64 KiB recursion (`1.5 MiB` logical payload in `< 1 MB` default stack at `-O0` and `-O1`) + depth-12 `Copy` 64 KiB recursion
  - `many_indirect_args_back_to_back.ax`: back-to-back 14-ABI-arg calls mixing `sret` + 6 indirect aggregates + scalars across `> 64` B `memcpy` loop splits and 12-GPR pressure
  - Mutation liveness verified on `huge_256k_default_stack.ax` and `many_indirect_args_back_to_back.ax` (`3/3 FAIL` across `interp`, `native`, `native-O1` when mutated; `3/3 PASS` restored)
- Full `run/`, `diff/`, `mc/`, `selfhost/{abi,isel,frame,lir,own_mir_verify}` sweep: `TOTAL 3358 PASS 3347 FAIL 0 SKIP 11 XFAIL 0`
- `selfhost/backend` & `selfhost/obj_link_driver` (`--no-cache`): `qa_backend_interp.ax`, `qa_backend_native.ax`, `qa_obj_link_driver_diff.ax` all `PASS` (`0 FAIL`, `WEAK-NATIVE: 0`)
- `python tools/taskgate.py --task T498h --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`:
  - `TASKGATE T498h exit=0` (`TOTAL 301 PASS 289 FAIL 0 SKIP 12 XFAIL 0`: own `24/24`, affected `241/241`, smoke `53/53`)
  - `BASELINE OK` (`Failing ids: none`)
  - `WEAK-NATIVE: 0` in task's own/changed tests
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
  - `smoke-check (tests/smoke.list): OK`

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
