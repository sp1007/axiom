# T500 — E13.1: Canonical unsafe, UB, pointer provenance, FFI/ABI & REQ-OWNER-008 address specification (SPEC-50)

## Tóm tắt
Hoàn thành đặc tả chuẩn `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-001`..`AXS-UNS-053`) cho epic `E13.1` (`T500`–`T505`) và nền tảng địa chỉ cố định của `E13.6` (`T525`–`T529`), hợp nhất các nguồn `0044`, `0071`, `0104`, `0138`, `0181`, `tasks/0282`, `tasks/0339`, `tasks/0367`, `tasks/0395`, `tasks/0413`, `ADR-0001`, `ADR-0034 §8`, `ADR-0036` và yêu cầu của chủ dự án `REQ-OWNER-008` cùng toàn bộ 135 yêu cầu trong `covers:` (`REQ-CAP-*`, `REQ-CORE-*`, `REQ-DIAG-032`, `REQ-FFI-*`, `REQ-UNSAFE-*`). Đồng thời cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, `spec/invariants.md` (`INV-UNS-001`..`INV-UNS-005`) và `spec/SPEC-03-core-semantics.md`.

## Summary of Changes

1. **Created `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-001..053`)**:
   - **§1. The Unsafe Boundary & Trusted Precondition Model (`AXS-UNS-001..007`)**:
     - Defines the narrow `unsafe` boundary (`AUNSAFE-20..22`): `unsafe` authorizes only the seven primitive unsafe operation categories (raw pointer dereference `*p`, pointer arithmetic, `unsafe fn` calls, `extern "<abi>"` calls, `MakeView`/`MakeMutView` raw-pointer-to-capability upgrades, mutable `static` access, and `@addr`/`@at` fixed-address access) while keeping typechecking, definite initialization, move/drop tracking, and safe capability verification fully active.
     - Specifies `unsafe { ... }` blocks (`AXS-UNS-002`), `unsafe fn` contracts (`AXS-UNS-003`), `unsafe trait` / `unsafe impl` symmetry (`AXS-UNS-004`, `AX_UNSAFE_TRAIT_IMPL`, `AX_UNSAFE_UNNECESSARY_IMPL`), and `MakeView`/`MakeMutView` capability creation (`AXS-UNS-005`, `view.from_raw`, `mut_view.from_raw`, `slice.from_raw_parts`, `slice.from_raw_parts_mut`) with immediate resumption of safe capability verification (`AXS-UNS-006`) and explicit traceability for all `REQ-CAP-*` invariants (`AXS-UNS-007`).
   - **§2. Raw Pointer Model, Strict Provenance & Undefined Behavior Taxonomy (`AXS-UNS-010..016`)**:
     - Specifies `*const T` and `*mut T` representation, variance, `Send`/`Share` absence, and no index auto-deref (`AX_TYPE_CANNOT_INDEX`, `ADR-0036`).
     - Formalizes the Strict Provenance model (`(AllocId, Bounds, Perm, AddrSpace)`), `ptr.addr()`, `ptr.with_addr(a)`, `ptr.expose_addr()`, and `ptr.from_exposed_addr(a)` (`AXS-UNS-011`), pointer arithmetic (`offset`, `add`, `sub`, `wrapping_offset`, `byte_add`, `byte_sub`, `AXS-UNS-012`), alignment/initialization/scalar validity (`AXS-UNS-013`), and raw-pointer vs capability aliasing discipline (`AXS-UNS-014`).
     - Establishes the closed 12-category Undefined Behavior catalog (`UB-01..UB-12`, `AXS-UNS-015`) and the deterministic MIR interpreter (`--interp`) UB detector (`AXS-UNS-016`, `AX_UNSAFE_INTERP_UB`, exit code `125`) covering `T502`.
   - **§3. `REQ-OWNER-008`: Address Introspection & Fixed-Address Placement (`AXS-UNS-020..025`)**:
     - Specifies `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) -> *const T`, `address_of_mut(v) -> *mut T`, `addr_of(v) -> usize`, and `f as usize` (`AXS-UNS-020..021`, `AX_TYPE_NOT_A_PLACE`), guaranteeing no move/copy of the inspected place.
     - Unifies `@addr(<expr>)` and `@at(<expr>)` (`ADR-0001`) across module-level `static` items (`AXS-UNS-023`), local `let` bindings (`AXS-UNS-024`), and `fn` items (`AXS-UNS-025`), supporting both compile-time constant addresses and runtime-computed offset expressions (`let base = fn_addr(foo); @addr(base + 0x100) static mut REG: u32;`), alignment/layout validation (`AX_UNSAFE_MISALIGNED_AT`, `AX_UNSAFE_INVALID_AT_LAYOUT`, `AX_UNSAFE_AT_HOSTED`), and exact round-trip identities (`fn_addr(isr) == 0x2000_0000usize`) for `T504` and `E13.6` (`T525`).
   - **§4. Physical Representation, ABI Stability & Foreign Function Interface (`AXS-UNS-030..036`)**:
     - Separates language semantics from physical representation (`AXS-UNS-030`) and specifies `@repr(C)`, `@repr(transparent)` (`AX_FFI_INVALID_TRANSPARENT`), `@repr(IntTy)`, `@packed`, `@align(N)`, and `@abi(stable)` (`AXS-UNS-031`).
     - Specifies `extern "C"` and `extern "system"` imports/exports (`AXS-UNS-032`), `std.ffi.c` type aliases, `CStr`, opaque foreign types (`AX_FFI_OPAQUE_BY_VALUE`), non-capturing C callbacks (`AX_FFI_CAPTURING_CLOSURE_CALLBACK`), conservative optimizer/race-verifier foreign effect summaries (`AXS-UNS-034`), Windows x64 (`Win64`) struct classification for `1, 2, 3, 4, 8, 12, 16, 24`-byte aggregates (`AXS-UNS-035`), and the `ADR-0034 §8` (`OI-12`) external `gcc -shared` C DLL oracle (`AXS-UNS-036`) for `T503`.
   - **§5. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-UNS-050..053`)**:
     - Consolidates all `UNSAFE`, `FFI`, `TYPE`, and `CAP` diagnostics (`AXS-UNS-050`), provides 15 canonical conformance test cases (`UNS-T01..T15`, `AXS-UNS-051`), maps rules to `T501`–`T505` and `T525` (`AXS-UNS-052`), and cross-references all 135 `covers:` requirement IDs (`AXS-UNS-053`).

2. **Updated `spec/INDEX.md`**:
   - Registered `spec/SPEC-50-unsafe-ub-ffi.md` in `§2. Canonical documents`.
   - Added `AXS-UNS-NNN` to `§4. Identifier namespaces`.
   - Linked `SPEC-50` in `§5. Topic → canonical source` for ownership/capability/unsafe, MIR/oracle UB detection, LIR/ABI/FFI, and fixed addresses (`REQ-OWNER-008`).

3. **Updated `spec/diagnostics.md`**:
   - Refined `AX_UNSAFE_REQUIRED`, `AX_UNSAFE_INTERP_UB`, `AX_FFI_NOT_IN_ORACLE`, and `AX_UNSAFE_AT_HOSTED` with `SPEC-50` references and task IDs (`T501`–`T504`, `T525`).
   - Added `AX_UNSAFE_TRAIT_IMPL`, `AX_UNSAFE_UNNECESSARY_IMPL`, `AX_UNSAFE_MISALIGNED_AT`, `AX_UNSAFE_INVALID_AT_LAYOUT`, `AX_FFI_UNKNOWN_ABI`, `AX_FFI_BAD_TYPE`, `AX_FFI_INVALID_TRANSPARENT`, `AX_FFI_OPAQUE_BY_VALUE`, `AX_FFI_GENERIC_EXPORT`, `AX_FFI_CAPTURING_CLOSURE_CALLBACK`, `AX_FFI_VARIADIC_NOT_EXTERN_C`, `AX_TYPE_NOT_A_PLACE`, `AX_CAP_CONFLICT_MUT`, `AX_CAP_OUTLIVES_OWNER`, and `AX_CAP_CONTAINER_RELOC` to `§11`.

4. **Updated `spec/invariants.md`**:
   - Added group `UNS` to `§1` and added `§14. Unsafe boundary, pointer provenance, FFI/ABI, and address introspection (SPEC-50)` defining `INV-UNS-001` (`since: T501`), `INV-UNS-002` (`since: T502`), `INV-UNS-003` (`since: T503`), `INV-UNS-004` (`since: T504`), and `INV-UNS-005` (`since: T505`).

5. **Updated `spec/SPEC-03-core-semantics.md`**:
   - Cross-referenced `SPEC-50` (`AXS-UNS-010..021`) in `AXS-SEM-060` (pointer/address casts and `fn(...) -> usize` / `fn_addr(f)`) and `AXS-SEM-092` (oracle UB detection `UB-01..UB-12`).

## Files changed
- ./spec/SPEC-50-unsafe-ub-ffi.md
- ./spec/INDEX.md
- ./spec/diagnostics.md
- ./spec/invariants.md
- ./spec/SPEC-03-core-semantics.md

## Tests
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS (`unmapped: 0`, `uncovered: 0`).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS (`0 errors`).
- `python tools/gatecheck.py --no-run`: PASS (`status: PASS`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T500`: PASS (`0 REFUSED`, all 5 modified/created files are within `paths:`/`locks:` of `T500`).

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
