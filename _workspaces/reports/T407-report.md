# T407 Report — E11.2: LIR Atomic Operations & x86-64 Instruction Selection/Encoding

## Summary

Implemented `E11.2` (`AXS-ATM-040..045`) across `compiler/lir/` and `compiler/target/x64/`:

1. **LIR Data Model & Formatting (`compiler/lir/{lir.ax,mod.ax}`)**:
   - Added `LIR_INST_ATOMIC_LOAD`, `LIR_INST_ATOMIC_STORE`, `LIR_INST_ATOMIC_RMW`, `LIR_INST_ATOMIC_CAS`, `LIR_INST_FENCE`, and `LIR_INST_PAUSE` along with `LIR_ATOMIC_RMW_{XCHG,ADD,SUB,AND,OR,XOR}` and `LIR_ORDER_{RELAXED,ACQUIRE,RELEASE,ACQ_REL,SEQ_CST}` (`AXS-ATM-040`).
   - Extended `LirInst` with `ordering`, `fail_ordering`, `rmw_op`, `is_weak`, `is_compiler_only`, and `cas_ok`.
   - Updated `lir_print_inst` to emit deterministic textual LIR (`atomic_load.b<W>`, `atomic_store.b<W>`, `atomic_rmw.b<W>`, `atomic_cas.b<W>`, `atomic_fence`, `compiler_fence`, `atomic_pause`).

2. **MIR -> LIR Atomic Lowering (`compiler/lir/builder.ax`)**:
   - Implemented `lower_atomic_stmt` to lower `MIR_STMT_ATOMIC` (`MIR_ATOMIC_LOAD`, `MIR_ATOMIC_STORE`, `MIR_ATOMIC_XCHG`, `MIR_ATOMIC_CMPXCHG`, `MIR_ATOMIC_CMPXCHG_WEAK`, `MIR_ATOMIC_ADD`, `MIR_ATOMIC_SUB`, `MIR_ATOMIC_AND`, `MIR_ATOMIC_OR`, `MIR_ATOMIC_XOR`, `MIR_ATOMIC_FENCE`, `MIR_ATOMIC_COMPILER_FENCE`, `MIR_ATOMIC_SPIN_HINT`).
   - Queried `type_field_offset` on `CasResult<T>` so both field `0` (`ok: bool`) and field `1` (`val: T`) are written at their exact ABI/layout offsets for all atomic widths (`b8`, `b16`, `b32`, `b64`).

3. **x86-64 Instruction Encoding (`compiler/target/x64/{encode.ax,mod.ax}`)**:
   - Added 8/16/32/64-bit `MOV`/`XCHG`/`ADD`/`SUB`/`AND`/`OR`/`XOR`/`CMP`/`TEST` sizing helpers (`0x66` operand-size prefix for 16-bit, `REX.W` for 64-bit, `REX` byte-register encoding for `SIL`/`DIL`/`BPL`/`SPL`/`R8B..R15B`).
   - Implemented `x64_xchg_rr`, `x64_xchg_mr`, `x64_lock_xadd_mr`, `x64_lock_cmpxchg_mr`, `x64_lock_{add,sub,and,or,xor}_mr`, `x64_mfence`, `x64_pause`, and `x64_jcc8` (`AXS-ATM-041..044`).

4. **x86-64 Instruction Selection, Liveness, RegAlloc & Frame Emission (`compiler/target/x64/{isel.ax,frame.ax}`)**:
   - Lowered `LIR_INST_ATOMIC_LOAD`, `LIR_INST_ATOMIC_STORE` (`MOV` for `Release`/`Relaxed`, `XCHG` for `SeqCst`), `LIR_INST_ATOMIC_RMW` (`XCHG`, `LOCK XADD`, negated `LOCK XADD`, and `X64_MI_ATOMIC_RMW_LOOP` CAS loop for `AND`/`OR`/`XOR`), `LIR_INST_ATOMIC_CAS` (`LOCK CMPXCHG` + `SETE`), `LIR_INST_FENCE` (`MFENCE` for `SeqCst`, `X64_MI_COMPILER_BARRIER` for `Acquire`/`Release`/`AcqRel` and `compiler_fence`), and `LIR_INST_PAUSE` (`PAUSE`) in both baseline (`x64_isel_raw_in_arena`) and optimized (`x64_isel_opt_in_arena`) isel paths (`AXS-ATM-041..045`).
   - Prevented load/store forwarding and dead-store elimination across atomic instructions and barriers (`AXS-ATM-045`).
   - Updated liveness analysis, register-allocation physical register def/use masks (`RAX`/`RDX`/`R8` clobbers), Machine IR verification, and section encoding (`frame.ax`) for all atomic Machine IR opcodes.

## Files changed

- compiler/lir/builder.ax
- compiler/lir/lir.ax
- compiler/lir/mod.ax
- compiler/target/x64/encode.ax
- compiler/target/x64/frame.ax
- compiler/target/x64/isel.ax
- compiler/target/x64/mod.ax
- tests/encode/atomics/encode_atomics.ax
- tests/lir/atomics/atomic_ops_lir.ax
- tests/lir/atomics/atomic_ops_lir.test
- tests/run/concurrency/atomics_native/atomics_native.ax
- tests/selfhost/abi/qa_abi_boundary_seam.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/abi/qa_abi_win64_classify.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/encode/qa_encode_edge_cases.ax
- tests/selfhost/encode/qa_encode_instructions.ax
- tests/selfhost/encode/qa_encode_relocs_and_frames.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax

## Verification

- `python build-snap-T407/tools/axtest.py --root build-snap-T407 --build-dir build-snap-T407/build --compiler build-snap-T407/build/axiomc2.exe -j 1 lir/atomics encode/atomics run/concurrency/atomics_native mir/atomics ui/concurrency/atomics`: `TOTAL 15 PASS 15 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).
- `python build-snap-T407/tools/axtest.py --root build-snap-T407 --build-dir build-snap-T407/build --compiler build-snap-T407/build/axiomc2.exe -j 1 selfhost/lir/bundles_current.test selfhost/encode/bundles_current.test selfhost/isel/bundles_current.test selfhost/abi/bundles_current.test selfhost/backend/bundles_current.test selfhost/driver/bundles_current.test`: `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0`.
- `python build-snap-T407/tools/archcheck.py`: `archcheck: 194 files scanned, 0 violations`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T407`: `0 REFUSED`.

STATUS: COMPLETE round=0
