# T872 Report: E20.7 std.component dynamic plugin loader, version/capability negotiator, epoch lease table & state-hand-off hot-reload runtime

## Summary

Implemented Milestone **E20.7** (`T872`) in the Axiom standard library (`std/component/loader/mod.ax` and `std/component/hot_reload/mod.ax`) per `spec/SPEC-115-dynamic-components-plugins-hot-reload.md`, `tasks/0584`, `tasks/0856`, and `REQ-ECO-8734`:

1. **`std.component.loader` Dynamic Plugin Loader & Pre-Flight Negotiator (`std/component/loader/mod.ax`)**:
   - Pre-flight `.axcomp` discovery and header inspection directly from raw component image bytes/registry BEFORE executing component init code (`AXS-COMP-010`, `AXS-COMP-005`).
   - Bit-for-bit `AbiFingerprint` and `TargetTripleFingerprint` dual verification against the host environment (`AXS-COMP-012`, `AX_COMP_ABI_MISMATCH`, `AX_COMP_TARGET_MISMATCH`).
   - Load-time SemVer 2.0 Caret (`^`) range compatibility negotiation with strict pre-release isolation (`AXS-COMP-011`, `AX_COMP_VERSION_INCOMPATIBLE`).
   - Component identifier syntax parsing and validation (`<vendor>.<namespace>.<name>`, `AXS-COMP-002`).
   - Duplicate registration rejection for active `(ComponentId, SemVer)` tuples (`AX_COMP_DUPLICATE_REGISTRATION`).
   - `CapabilityGrant` bitmask verification: host granted capability subset enforcement, monotonic attenuation, and runtime dynamic revocation (`AXS-COMP-013`, `AXS-COMP-014`, `AX_COMP_CAPABILITY_DENIED`).
   - Type-safe 128-bit `InterfaceFingerprint` dispatch table binding and vtable lookup (`AXS-COMP-015`).

2. **`std.component.hot_reload` Generational Handles, Epoch Leases & Hot-Reload Runtime (`std/component/hot_reload/mod.ax`)**:
   - `AllocatorVTable` and `ComponentBox<T>` originating-allocator deallocation routing (`AXS-COMP-021`, `AX_COMP_CROSS_ALLOCATOR_VIOLATION`).
   - Generational `ComponentHandle<T>` slot table (`ComponentHandleTable`) with 32-bit index, 32-bit generation, and 32-bit epoch tokens; detects stale generation, dangling slots, and stale epoch accesses (`AXS-COMP-022`, `AX_COMP_STALE_HANDLE`).
   - `EpochTracker` and `ComponentLease` active borrow/task/callback/GPU fence reference counting; strictly protects against physical library unloads (`FreeLibrary`/`dlclose`/unmap) while `active_leases > 0` (`AXS-COMP-023`, `AXS-COMP-024`, `AX_COMP_UNLOAD_ACTIVE_LEASES`).
   - 5-phase transactional `HotReloadManager` state machine (`AXS-COMP-030`..`037`):
     - `Quiesce`: gates new inbound invocations, detaches active callbacks, and drains active epoch leases within a configured timeout window (`AX_COMP_QUIESCE_TIMEOUT` on expiration).
     - `ExportState`: extracts serialized snapshot tagged with `StateSchemaId`.
     - `LoadNewEpoch`: stages candidate epoch library alongside active epoch, verifies `.axcomp` headers, SemVer range, fingerprints, and granted capabilities.
     - `MigrateState`: executes zero-copy identity migration when `StateSchemaId` matches (`AXS-COMP-033`), or dispatches to registered `@hot_reload_migration` hook when schemas differ; aborts with `AX_COMP_HOT_RELOAD_MIGRATION_FAILED` on missing or failed migration.
     - `Resume`: atomically swaps active epoch pointer to Candidate Epoch N+1, advances generational handle table epoch token, transitions Epoch N to `Retired`, and triggers deferred physical unload only after `active_leases == 0`.
   - Transactional rollback guarantee: any error or timeout across Phases 1–4 evicts candidate epoch and resumes active epoch immediately with zero state loss (`AXS-COMP-036`).

3. **Comprehensive Tests (`tests/run/component_hot_reload/`)**:
   - Multi-module oracle probe bundle (`component_hot_reload.test`, `component_hot_reload_oracle.py`, `component_hot_reload_probe.ax.in`):
     - Validates end-to-end integration of `std.component.loader` and `std.component.hot_reload` across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` with exact byte-identical stdout comparison.
   - Standalone run fixtures (passing across `--interp`, `native-O0`, `native-O1`):
     - `preflight_discovery_and_negotiation.ax` (+ `.stdout`): tests pre-flight parsing, ABI/target mismatch rejection, SemVer caret matching, duplicate registration rejection, capability attenuation/revocation, and vtable dispatch binding.
     - `component_box_and_epoch_leases.ax` (+ `.stdout`): tests `ComponentBox` custom allocator routing, generational handle stale-generation/epoch defense, and `ComponentLease` unload guard.
     - `multi_epoch_hot_reload_and_rollback.ax` (+ `.stdout`): tests multi-epoch hot-reload (Epoch 1 -> Epoch 2 fast path, Epoch 2 -> Epoch 3 migration, Candidate Epoch 4 failure rollback with zero state loss, and deferred retired epoch unmapping).

## Verification

Executed:
```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/component_hot_reload
```
Result:
```
WEAK-NATIVE 0
TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0
```

Executed:
```bash
python tools/archcheck.py
```
Result:
```
archcheck: 202 files scanned, 0 violations
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

## Files changed

- std/component/hot_reload/mod.ax
- std/component/loader/mod.ax
- tests/run/component_hot_reload/component_box_and_epoch_leases.ax
- tests/run/component_hot_reload/component_box_and_epoch_leases.stdout
- tests/run/component_hot_reload/component_hot_reload.test
- tests/run/component_hot_reload/component_hot_reload_oracle.py
- tests/run/component_hot_reload/component_hot_reload_probe.ax.in
- tests/run/component_hot_reload/multi_epoch_hot_reload_and_rollback.ax
- tests/run/component_hot_reload/multi_epoch_hot_reload_and_rollback.stdout
- tests/run/component_hot_reload/preflight_discovery_and_negotiation.ax
- tests/run/component_hot_reload/preflight_discovery_and_negotiation.stdout

## Status

STATUS: COMPLETE round=0
