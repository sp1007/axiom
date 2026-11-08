# T873 Report: E20.7 Dynamic components, plugin discovery, cross-boundary ownership/capability isolation & hot-reload state migration conformance suite

## Summary

Implemented and certified Milestone **E20.7** (`T873`) end-to-end conformance suite in `tests/conformance/p20/e20_7_dynamic_components_hot_reload/` per `spec/SPEC-115-dynamic-components-plugins-hot-reload.md`, `tasks/0584`, `tasks/0856`, `REQ-ECO-8734`, `INV-COMP-001`, and `INV-COMP-002`:

1. **Master Multi-Module Conformance Oracle (`e20_7_dynamic_components_hot_reload_oracle.test` + `.py` + `_probe.ax.in`)**:
   - Bundles the self-hosted compiler modules (`compiler.component.interface`, `compiler.component.verify`, compiler kernel & ABI stability) and standard library runtime modules (`std.component.loader`, `std.component.hot_reload`) with `e20_7_dynamic_components_hot_reload_probe.ax.in`.
   - Executes across `--interp`, native `-O0 --verify-each`, native `-O1 --verify-each`, and native `-O2 --verify-each` with exact byte-for-byte identical output parity across all 4 execution tiers:
     - `probe[compiler_vtable_and_boundary]`: vtable sizing, BLAKE3-128 interface fingerprinting, ComponentId syntax checking, and `AX_COMP_*` diagnostic taxonomy.
     - `probe[discovery_and_negotiation]`: `.axcomp` binary section header inspection, SemVer 2.0 Caret range compatibility, dual `AbiFingerprint` & `TargetTripleFingerprint` host verification, duplicate registration rejection, capability subset/attenuation/revocation, and type-safe interface dispatch table binding.
     - `probe[box_handles_and_epoch_leases]`: `ComponentBox<T>` custom allocator deallocation routing, `ComponentHandleTable<T>` slot allocation, retrieval, stale generation detection, stale epoch detection, and `EpochTracker` / `ComponentLease` unload safety.
     - `probe[multi_epoch_hot_reload]`: 5-phase hot-reload coordinator, Epoch 1 -> Epoch 2 fast-path schema identity, Epoch 2 -> Epoch 3 schema evolution with registered migration hook, quiesce timeout rollback with 0 state loss, migration failure rollback with 0 state loss, and deferred retired epoch unmapping.
   - Differential verification across all 4 standalone `.ax` fixtures (`--interp` vs native `-O1 --verify-each`).
   - Clean production image audit ensuring zero leaked `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, or `.axlto` metadata tokens.

2. **Standalone Conformance Fixtures (`.ax` + `.stdout`)**:
   - `interface_negotiation_and_capabilities.ax` (+ `.stdout`):
     - Validates ComponentId syntax (`<vendor>.<namespace>.<name>`, `AXS-COMP-002`).
     - Validates SemVer 2.0 Caret matching across compatible minor updates (`v1.0.0` -> `v1.1.0`), incompatible majors (`v1.0.0` vs `v2.0.0`), prerelease isolation, and 0.y.z boundaries (`AXS-COMP-011`).
     - Verifies cryptographic dual environment checks rejecting mismatched `AbiFingerprint` (`AX_COMP_ABI_MISMATCH` = 236) and `TargetTripleFingerprint` (`AX_COMP_TARGET_MISMATCH` = 234; `AXS-COMP-012`).
     - Verifies duplicate registration prevention (`AX_COMP_DUPLICATE_REGISTRATION` = 233; `AXS-COMP-002`).
     - Verifies capability manifests, host granted capability subset enforcement, monotonic capability attenuation, and runtime capability revocation (`AX_COMP_CAPABILITY_DENIED` = 237, `AX_COMP_CAPABILITY_REVOKED` = 245; `AXS-COMP-013`, `AXS-COMP-014`).
     - Verifies type-safe 128-bit `InterfaceFingerprint` dispatch table binding and `AX_COMP_INTERFACE_NOT_FOUND` (247; `AXS-COMP-015`).
   - `boundary_firewall_and_allocator_isolation.ax` (+ `.stdout`):
     - Validates boundary firewall permitting safe boundary types (scalars, `ComponentBox<T>`, `ComponentHandle<T>`, opaque pointers, and leased views) while rejecting raw pointer escapes (`AX_COMP_RAW_POINTER_ESCAPE` = 238) and plain host heap collections (`AX_COMP_CROSS_ALLOCATOR_VIOLATION` = 239; `AXS-COMP-020`).
     - Verifies `ComponentBox<T>` originating-allocator deallocation routing through `AllocatorVTable` and rejection of null vtables (`AX_COMP_CROSS_ALLOCATOR_VIOLATION` = 239; `AXS-COMP-021`).
     - Verifies generational `ComponentHandle<T>` slot table: slot reuse generation bumping, stale generation detection (`AX_COMP_STALE_HANDLE` = 240), epoch advance token migration, stale epoch detection, and out-of-bounds access rejection (`AXS-COMP-022`).
   - `epoch_leases_and_unload_protection.ax` (+ `.stdout`):
     - Validates `EpochTracker` and `ComponentLease` reference counting across borrows, background tasks, ephemeral callbacks, and GPU fences (`AXS-COMP-023`, `AXS-COMP-024`).
     - Verifies strict physical unload blocking while `active_leases > 0` (`AX_COMP_UNLOAD_ACTIVE_LEASES` = 241).
     - Verifies quiescence phase rejection of new leases (`AX_COMP_COMPONENT_QUIESCING` = 246; `AXS-COMP-031`).
     - Verifies ephemeral callback detachment during quiescence.
     - Verifies sequential lease draining and verified clean unload transition upon zero active leases.
   - `multi_epoch_hot_reload_and_state_migration.ax` (+ `.stdout`):
     - Validates 5-phase hot-reload coordinator (`HotReloadManager`: `Quiesce` -> `ExportState` -> `LoadNewEpoch` -> `MigrateState` -> `Resume`; `AXS-COMP-030`..`037`).
     - Validates multi-epoch live progression: Epoch 1 -> Epoch 2 zero-copy fast-path identity when `StateSchemaId` matches, Epoch 2 -> Epoch 3 schema evolution with registered migration hook (`AXS-COMP-034`).
     - Validates transactional rollback guarantees with zero state loss:
       * Rollback on quiesce timeout (`AX_COMP_QUIESCE_TIMEOUT` = 242; `AXS-COMP-031`, `AXS-COMP-036`).
       * Rollback on migration hook failure (`AX_COMP_HOT_RELOAD_MIGRATION_FAILED` = 244; `AXS-COMP-034`, `AXS-COMP-036`).
       * Rollback on unregistered schema mismatch (`AX_COMP_HOT_RELOAD_SCHEMA_MISMATCH` = 243; `AXS-COMP-034`, `AXS-COMP-036`).
     - Validates deferred physical unmapping of retired epochs blocked by active leases and permitted upon full lease drainage (`AXS-COMP-037`).

3. **Canonical Syntax Compliance (`axiom-syntax`)**:
   - Strictly canonical Axiom surface syntax across all conformance tests: `=` for bindings/assignments (no `:=`, no `var`), `.` for module and type paths (no `::`), and clean LF line endings.

## Verification

Executed:
```bash
python build-snap-T873/tools/axtest.py --root build-snap-T873 --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p20/e20_7_dynamic_components_hot_reload
```
Result:
```
WEAK-NATIVE 0
TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0
```

Executed:
```bash
python tools/archcheck.py
```
Result:
```
archcheck: 204 files scanned, 0 violations
```

Executed:
```bash
python .claude/skills/axiom-tasks/scripts/reqcov.py --strict
```
Result:
```
requirements: 32308
  v1-core  implemented=5864
  v1-full  implemented=6637  planned=2194
  post-v1  epic=17535  planned=78
gaps: 0
COVERAGE OK
```

Executed:
```bash
python .claude/skills/axiom-tasks/scripts/harness_check.py
```
Result:
```
HARNESS OK
```

Executed:
```bash
python .claude/skills/axiom-tasks/scripts/taskctl.py changes T873
```
Result: zero REFUSED lines.

## Files changed

- tests/conformance/p20/e20_7_dynamic_components_hot_reload/README.md
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/boundary_firewall_and_allocator_isolation.ax
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/boundary_firewall_and_allocator_isolation.stdout
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/e20_7_dynamic_components_hot_reload_oracle.py
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/e20_7_dynamic_components_hot_reload_oracle.test
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/e20_7_dynamic_components_hot_reload_probe.ax.in
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/epoch_leases_and_unload_protection.ax
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/epoch_leases_and_unload_protection.stdout
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/interface_negotiation_and_capabilities.ax
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/interface_negotiation_and_capabilities.stdout
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/multi_epoch_hot_reload_and_state_migration.ax
- tests/conformance/p20/e20_7_dynamic_components_hot_reload/multi_epoch_hot_reload_and_state_migration.stdout

## Status

STATUS: COMPLETE round=0
