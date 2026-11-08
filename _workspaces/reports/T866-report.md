# T866 Report — E20.5 Canonical Axiom ABI stability tiers, versioned symbol contracts, AbiFingerprint/ApiFingerprint & binary compatibility specification (`SPEC-114`)

STATUS: COMPLETE

## Tóm tắt

Đã hoàn thành đặc tả chính tắc `spec/SPEC-114-abi-stability-versioning-binary-compat.md` cho Epic **E20.5** (`T866`), quy định toàn diện kiến trúc ba tầng ABI của ngôn ngữ Axiom (`Internal Axiom ABI`, `Package Interface ABI` `.axmeta`, `Stable Binary ABI` `@abi(stable)` / `@repr(C)` / `@repr(transparent)`), bốn chiều tương thích (`Source`, `Semantic`, `ABI`, `Binary`), hệ thống kiểu nhị phân ổn định (`Stable Axiom ABI Type System`) và việc từ chối các kiểu không ổn định tại thời điểm biên dịch (`REQ-ECO-8734`, `REQ-PKG-024`), bộ ba hàm băm định danh độc lập (`ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint`), cơ chế đánh số phiên bản ký hiệu liên kết (`@symbol_version`), và công cụ phân loại tương thích nhị phân / SemVer tự động `axiomc abi-check` (`REQ-PKG-022`). Đồng thời đã cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-SABI-001`..`INV-SABI-003` với `since: T867`..`T869`).

## Summary of Decisions & Deliverables

1. **The Three ABI Tiers Architecture & Boundary Firewall (`SPEC-114 §1`, `AXS-ABI-001`..`AXS-ABI-004`, `REQ-PKG-024`)**:
   - Specified the three explicit ABI tiers: **Internal Axiom ABI** (default, freely optimizable across compiler versions without stability constraints), **Package Interface ABI** (`.axmeta` / `.axmi` semantic & verified MIR template interface for separate compilation and package distribution), and **Stable Binary ABI** (explicit opt-in via `@abi(stable)`, `@repr(C)`, or `@repr(transparent)`).
   - Codified the non-equivalence laws: `SourceComp ≠ AbiComp`, `SemanticComp ≠ AbiComp`, `AbiComp ≠ BinaryComp`.
   - Established the explicit opt-in principle: `pub` indicates source/module visibility only and never implies binary export or ABI stability. Universal implicit ABI freezing is forbidden.
   - Formalized the **Stable ABI Firewall**: every `@abi(stable)` boundary is statically validated, rejecting unstable types at compile time with `AX_ABI_UNSTABLE_TYPE`.

2. **Stable Axiom ABI Type System (`SPEC-114 §2`, `AXS-ABI-010`..`AXS-ABI-017`, `REQ-ECO-8734`, `REQ-PKG-024`)**:
   - Defined allowed fixed-width scalars: `i8..i64`, `u8..u64`, `f32`, `f64`, strict 1-byte `bool` (normalized 0/1), `isize`/`usize`, and platform C lowering for 128-bit integers (`i128`/`u128`).
   - Specified extensible struct evolution: mandatory `AbiHeader { abi_version: u32, struct_size: u32 }` header, append-only field evolution, and runtime size/version checking (omission emits `AX_ABI_EXTENSIBLE_MISSING_HEADER`).
   - Specified tagged enums with mandatory explicit integer representation (`@repr(u8..u64)`), non-payload fieldless enums, C-compatible tagged union payload layout, and `@non_exhaustive` evolution.
   - Specified `@opaque` handle types providing 100% data encapsulation; attempts to instantiate, query size, or pass by value outside the defining module emit `AX_ABI_OPAQUE_BY_VALUE`.
   - Specified canonical borrowed views (`StableView<T>`, `StableStr`) with 16-byte fixed C layouts, UTF-8 string invariants, and zero-cost conversions from Axiom views.
   - Specified explicit allocator-paired buffers (`StableBuffer<T>`, `AllocatorVTable`) and exported deallocator functions to eliminate cross-DLL/cross-heap CRT deallocation undefined behavior.
   - Specified erased generic exports: prohibition of unmonomorphized generic dynamic exports (`AX_FFI_GENERIC_EXPORT`), favoring explicit monomorphization or stable vtable dispatch.
   - Specified compile-time firewall rejection for capturing closures, unrepr'd ADTs, raw generics, bare internal fat pointers, raw slices, and internal trait objects (`AX_ABI_UNSTABLE_TYPE`).

3. **Three-Tier Fingerprinting Architecture (`SPEC-114 §3`, `AXS-ABI-020`..`AXS-ABI-024`, `REQ-PKG-022`)**:
   - Defined domain-separated 128-bit BLAKE3 hashes: `ApiFingerprint` (`"AXIOM-API-v1\0"` for public syntactic interface), `SemanticFingerprint` (`"AXIOM-SEM-v1\0"` for inlined MIR bodies, comptime evaluation, and effect contracts), and `AbiFingerprint` (`"AXIOM-ABI-v1\0"` for physical layout, calling conventions, and symbol versions).
   - Formulated the exact canonical calculation, invariance properties, and invalidation triggers for each fingerprint.
   - Specified storage in `.axmeta` and early-cutoff caching across compilation and linking stages.

4. **Symbol Versioning & SemVer Compatibility Classifier (`SPEC-114 §4–§5`, `AXS-ABI-030`..`AXS-ABI-042`, `REQ-ECO-8734`, `REQ-PKG-022`)**:
   - Specified the `@symbol_version("1.0")` attribute, canonical mangling (`axiom_<pkg>_<mod>_<ident>@@<ver>`), multi-version coexistence in single binaries, Windows PE `.edata` alias mapping, ELF GNU symbol versioning, and hot-reload state migration fallback.
   - Specified the three-way compatibility classifier: `compatible` (implementation fixes, patch bump), `minor-additive` (new exports, extensible struct append, minor bump), `major-breaking` (removed symbols, altered layout/calling convention, requires major bump).
   - Specified the `axiomc abi-check --old <base.axmeta> --new <cand.axmeta> --semver <old>:<new>` CLI tool and diagnostics (`AX_ABI_BREAKING_CHANGE`, `AX_ABI_SEMVER_MISMATCH`, `AX_ABI_SYMBOL_VERSION_DUPLICATE`).
   - Updated `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md` (`INV-SABI-001`..`INV-SABI-003` with `since: T867`..`T869`).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `requirements: 32308 ... gaps: 0 / COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T866` → verified all modified/created files match the task card's `paths:` and `locks:` declarations.

## Files changed

- spec/SPEC-114-abi-stability-versioning-binary-compat.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
