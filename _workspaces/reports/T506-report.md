# T506 — E13.2 — Canonical raw memory, volatile, MMIO, unions, packed/aligned repr & address spaces specification (SPEC-51)

## Summary
- Authored `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` (`AXS-MEM-001`..`AXS-MEM-053`), starting with a Vietnamese `## Tóm tắt` section and specifying:
  - **Volatile & Hardware Memory Barriers (`AXS-MEM-001`..`004`)**: Three-protocol memory taxonomy (`Ordinary != Atomic != Volatile`), `volatile_load`, `volatile_store`, `volatile_copy`, `volatile_set_memory`, exact-width non-tearing guarantees on naturally aligned `1`, `2`, `4`, and `8`-byte scalar/MMIO accesses (`MOV r8/r16/r32/r64`), strict non-elision/non-coalescing/non-reordering contracts in MIR (`MirStmtKind.VolatileLoad`/`VolatileStore`) and LIR (`LIR_MEM_FLAG_VOLATILE`), and `compiler_fence` vs hardware barriers (`memory_barrier` -> `MFENCE`, `write_barrier` -> `SFENCE`, `read_barrier` -> `LFENCE`).
  - **Typed MMIO Register Wrappers (`AXS-MEM-005`..`006`)**: `@repr(transparent)` lang-item wrappers `Volatile<T>`, `Mmio<T>`, `MmioRO<T>`, and `MmioWO<T>` (`ADR-0001 §2`, `SPEC-04 AXS-EXT-023/043`) that lower ordinary field reads/writes (`uart.ctrl = v`, `uart.status`) directly to single-width volatile operations, enforce compile-time read-only (`AX_TYPE_MMIO_WRITE_READONLY`) and write-only (`AX_TYPE_MMIO_READ_WRITEONLY`) direction checks, and provide explicit `read`, `write`, `modify`, `set_bits`, `clear_bits`, `test_bits`, `extract_bits`, and `insert_bits` bit manipulation helpers.
  - **Untagged `union`, `MaybeUninit<T>`, `ManuallyDrop<T>` & `bitcast` (`AXS-MEM-010`..`015`)**: Overlapping `union` storage layout (`size = align_up(max_field_size, align)`, `align = max_field_align`, all fields at offset `0`), `Copy` or `ManuallyDrop<T>` field requirement (`AX_TYPE_UNION_NON_COPY_FIELD`), single-field union literal initialization (`AX_TYPE_UNION_INIT_FIELD_COUNT`), safe union field writes, `unsafe` union field reads/pattern matching (`AX_UNSAFE_REQUIRED`), `MaybeUninit<T>` (`uninit`, `zeroed`, `new`, `write`, `assume_init`, `as_ptr`, `as_mut_ptr`), `ManuallyDrop<T>`, non-semantic padding & explicit boundary endianness (`REQ-FFI-031`, `REQ-RES-137`, `REQ-RES-163`), and size/validity-checked `std.mem.bitcast<From, To>` (`AX_TYPE_BITCAST_SIZE_MISMATCH`, `REQ-RES-160`, `REQ-RES-161`).
  - **Physical Layout Control (`@repr(C)`, `@repr(packed)`, `@align(N)`), Unaligned Access & Address Spaces (`AXS-MEM-020`..`024`)**: Minimal Core ABI freeze (`REQ-CORE-449`) and `@repr(C)` layout freeze (`REQ-ABI-063`), power-of-two `@align(N)` and `@repr(packed(N))` validation (`AX_TYPE_INVALID_ALIGN`, `AX_TYPE_CONFLICTING_REPR`), safe by-value copy loads/stores on `@repr(packed)` fields vs prohibition of `view<T>`, `mut_view<T>`, or aligned `*const T`/`*mut T` creation to unaligned packed fields (`AX_TYPE_UNALIGNED_PACKED_REF`, `REQ-ABI-036`, `REQ-ABI-041`), raw/foreign pointer-to-view alignment and validity preconditions (`REQ-CAP-130`, `REQ-CAP-152`, `REQ-FFI-099`, `REQ-RES-136`), `read_unaligned`/`write_unaligned`, and explicit `@addr_space(N)` pointer qualifiers (`AX_TYPE_ADDR_SPACE_MISMATCH`).
- Updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-MEM-001`..`INV-MEM-004`).
- **Round 1 QA Fix (Finding 1)**: Replaced all occurrences of Rust-style `::` turbofish syntax (`::<...>`) in `spec/SPEC-51-raw-memory-volatile-mmio-layout.md` and `spec/diagnostics.md` (lines 561, 564) with canonical Axiom `<...>` generic arguments (`size_of<T>()`, `align_of<T>()`, `bitcast<f32, u32>(1.0f32)`, `MaybeUninit<bool>.zeroed()`, `needs_drop<ManuallyDrop<T>>()`), leaving `0` `::` strings in `SPEC-51` and the `T506` additions in `spec/diagnostics.md` and `spec/invariants.md`.

## Files changed
- `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`
- `spec/INDEX.md`
- `spec/diagnostics.md`
- `spec/invariants.md`

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` — `COVERAGE OK` (0 gaps)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` — `HARNESS OK`
- `python tools/gatecheck.py --no-run` — `GATECHECK OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T506` — 4 allowed files, 0 `REFUSED`

STATUS: COMPLETE round=1
