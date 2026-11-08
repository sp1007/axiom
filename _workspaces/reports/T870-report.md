# T870 Report — E20.7 Canonical Axiom dynamic components, plugin discovery, cross-boundary ownership/capability handles & hot-reload state migration specification (`SPEC-115`)

STATUS: COMPLETE

## Tóm tắt

Đã hoàn thành đặc tả chính tắc `spec/SPEC-115-dynamic-components-plugins-hot-reload.md` cho Epic **E20.7** (`T870`), quy định toàn diện mô hình thành phần động của Axiom (Axiom Dynamic Component Model beyond raw C ABI), cơ chế khai báo `@component_interface` và `@plugin_export` (`axiom_component_entry`), phân đoạn siêu dữ liệu nhúng `.axcomp` (`ComponentId`, SemVer 2.0, `AbiFingerprint`, `TargetTripleFingerprint`, `StateSchemaId`, `CapabilityManifest`), giao thức khám phá động và thương lượng năng quyền tại thời điểm nạp không có đặc quyền ngầm định (No Ambient Privilege, `CapabilityGrant`), ranh giới cô lập sở hữu và bộ cấp phát bộ nhớ (`ComponentBox<T>`, bảng tay cầm thế hệ `ComponentHandle<T>`, hợp đồng thuê thời kỳ `ComponentLease` bảo vệ việc mượn lát cắt `view`/`mut_view`), liveness guards đối với task/callback/thread/GPU, và giao thức nạp lại nóng 5 pha (`Quiesce` -> `ExportState` -> `LoadNewEpoch` -> `MigrateState` -> `Resume`) với bảo đảm hoàn tác giao dịch (Transactional Rollback) và dỡ bỏ nhị phân an toàn (`UnloadOldEpoch`) (`REQ-ECO-8734`). Đồng thời đã cập nhật `spec/INDEX.md`, `spec/diagnostics.md`, và `spec/invariants.md` (`INV-COMP-001`..`INV-COMP-003` với `since: T871`..`T873`).

## Summary of Decisions & Deliverables

1. **Axiom Dynamic Component Model Architecture (`SPEC-115 §1`, `AXS-COMP-001`..`AXS-COMP-006`, `REQ-ECO-8734`)**:
   - Codified the ontological hierarchy: `Library` (source/MIR unit), `Dynamic Library` (OS binary container), `Dynamic Plugin` (discovered extensibility module), and `Dynamic Component` (explicit ABI, capability manifest, originating allocator pairing, and guarded lifecycle contract).
   - Specified logical `ComponentId = "<vendor>.<namespace>.<name>"` decoupled from physical dynamic library filenames.
   - Specified `@component_interface` lowering into Stable Axiom ABI vtables (`SPEC-114`) with 128-bit `InterfaceFingerprint` verification, hiding compiler internals and non-repr-C fat pointers.
   - Specified single dynamic entry point `@plugin_export fn axiom_component_entry(host_ctx, out_descriptor)` executing zero heavy initialization.
   - Specified the embedded `.axcomp` read-only container section across Windows PE/COFF, Linux ELF, macOS Mach-O, and WASM.
   - Enforced zero mandatory dynamic runtime overhead for statically linked applications and no ambient VM or garbage collector.

2. **Discovery, Version & Capability Negotiation (`SPEC-115 §2`, `AXS-COMP-010`..`AXS-COMP-015`, `REQ-ECO-8734`)**:
   - Specified pre-flight manifest inspection reading `.axcomp` directly from disk without loading dynamic code or executing library initializers (`DllMain`, `.init_array`).
   - Specified load-time SemVer 2.0 range matching with pre-release isolation (`AX_COMP_VERSION_INCOMPATIBLE`).
   - Enforced dual hardware-level fingerprint validation: strict bit-for-bit equality of `AbiFingerprint` and `TargetTripleFingerprint` before initialization (`AX_COMP_ABI_MISMATCH`, `AX_COMP_TARGET_MISMATCH`).
   - Specified capability-based security: mandatory declaration of required capabilities (`CapabilityManifest`), explicit host `CapabilityGrant` policy, and rejection of undeclared/unauthorized privileges (`AX_COMP_CAPABILITY_DENIED`).
   - Specified monotonic capability attenuation and safe runtime revocation.
   - Specified type-safe `acquire_interface<T>()` dispatch binding.

3. **Ownership, Allocator & Memory Isolation (`SPEC-115 §3`, `AXS-COMP-020`..`AXS-COMP-025`, `REQ-ECO-8734`)**:
   - Enforced compile-time prohibition of raw pointer types (`*T`, `*mut T`) across safe `@component_interface` boundaries (`AX_COMP_RAW_POINTER_ESCAPE`).
   - Solved the mixed-allocator heap hazard by requiring `ComponentBox<T>` for cross-boundary owned heap data, routing deallocation directly to the originating component allocator vtable (`AX_COMP_CROSS_ALLOCATOR_VIOLATION`).
   - Specified generation-safe resource handles (`ComponentHandle<T>` = `index: u32, generation: u32`) detecting stale or post-reload access (`AX_COMP_STALE_HANDLE`).
   - Specified epoch-leased borrow tracking (`ComponentLease`), blocking physical library unload while any borrowed `view`, `mut_view`, or `StableStr` remains active (`AX_COMP_UNLOAD_ACTIVE_LEASES`).
   - Specified in-flight execution guards preventing unloading while callbacks, tasks, worker threads, or GPU compute fences remain live.
   - Enforced `@opaque` component object encapsulation preventing client layout coupling.

4. **Deterministic Hot-Reload & State Migration Protocol (`SPEC-115 §4`, `AXS-COMP-030`..`AXS-COMP-037`, `REQ-ECO-8734`)**:
   - Formulated the 5-phase hot-reload state machine:
     - **Phase 1 (Quiesce)**: Gating incoming calls, draining active leases within timeout (`AX_COMP_QUIESCE_TIMEOUT`), detaching event callbacks.
     - **Phase 2 (ExportState)**: Snapshotting typed state annotated with `@hot_reload_state` and 128-bit `StateSchemaId`.
     - **Phase 3 (LoadNewEpoch)**: Loading candidate binary into isolated address space and verifying `.axcomp` manifest, ABI fingerprint, and capabilities prior to migration.
     - **Phase 4 (MigrateState)**: Fast-path identity adoption for identical schemas or invoking versioned migration hook (`migrate_state`) with schema validation (`AX_COMP_HOT_RELOAD_MIGRATION_FAILED`).
     - **Phase 5 (Resume)**: Atomic pointer swap with release memory semantics, advancing generational handle epoch tokens, and unblocking pending operations.
   - Specified transactional rollback guarantee: if staging, manifest verification, or migration fails, candidate is evicted and the old epoch resumes with zero state loss or downtime.
   - Specified deferred physical unmapping (`UnloadOldEpoch` only executed when `active_leases == 0`).

5. **Standard Library `std.component` APIs (`SPEC-115 §5`, `AXS-COMP-040`..`AXS-COMP-043`)**:
   - Specified `std.component.loader` (`ComponentHost`, `Component`, discovery and loading).
   - Specified `std.component.handle` (`ComponentHandle<T>`, `ComponentHandleTable<T>`, `ComponentBox<T>`).
   - Specified `std.component.lease` (`EpochTracker`, `EpochLease`).
   - Specified `std.component.hot_reload` (`HotReloadManager`, transactional reload coordinator).

6. **Diagnostics, Conformance & Invariants (`SPEC-115 §6`, `AXS-COMP-050`..`AXS-COMP-055`, `REQ-ECO-8734`)**:
   - Registered 14 canonical diagnostic codes (`AX_COMP_*`) in `spec/diagnostics.md`.
   - Updated `spec/INDEX.md` with `SPEC-115` and `AXS-COMP-NNN`.
   - Registered `INV-COMP-001`, `INV-COMP-002`, and `INV-COMP-003` in `spec/invariants.md` with `since:` pointing to `T871`, `T872`, `T873`.
   - Provided canonical positive and negative Axiom examples demonstrating interfaces, handles, state migration, and compile-time rejection of boundary leaks (`=` for binding, `.` for paths).

## Verification

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `requirements: 32308 ... gaps: 0 / COVERAGE OK`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T870` → verified all modified/created files match the task card's `paths:` and `locks:` declarations.

## Files changed

- spec/SPEC-115-dynamic-components-plugins-hot-reload.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md
