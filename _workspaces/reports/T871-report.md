# T871 Report: E20.7 @component_interface & @plugin_export boundary verifier, cross-component ownership/capability/allocator guard & .axcomp emitter

## Summary

Implemented Milestone **E20.7** (`T871`) in the self-hosted Axiom compiler (`compiler/component/interface/mod.ax` and `compiler/component/verify/mod.ax`) per `spec/SPEC-115-dynamic-components-plugins-hot-reload.md`, `spec/SPEC-114-abi-stability-versioning-binary-compat.md`, `REQ-ECO-8734`, and `INV-COMP-001`:

1. **`@component_interface` VTable Lowering & `.axcomp` Descriptor Emitter (`compiler/component/interface/mod.ax`)**:
   - Lowered `@component_interface` trait/function tables and `@plugin_export` entry points (`axiom_component_entry`) into versioned Stable Axiom ABI vtables (`AXS-COMP-003`, `AXS-COMP-004`).
   - Implemented deterministic 128-bit cryptographic digests:
     - `InterfaceFingerprint`: hashes interface name, SemVer version, method slot order, parameter count, parameter types hash, return type name, return passing mode, lease contract status, and unsafe modifier.
     - `TargetTripleFingerprint`: BLAKE3-128 hash of target architecture, OS, vendor, and ABI profile.
     - `StateSchemaId`: 128-bit hash of serializable state types and layouts for hot-reload state tracking.
   - Implemented SemVer 2.0 Caret (`^`) version requirement matching (`AXS-COMP-011`) and `ComponentId` format validation (`<vendor>.<namespace>.<name>`, `AXS-COMP-002`).
   - Implemented the `.axcomp` binary descriptor section (`AXS-COMP-005`):
     - Binary layout: `0x504D4F43` magic ("COMP" ASCII), format version 1, 128-byte header, `ComponentId` string offset/length, SemVer major/minor/patch/prerelease, `AbiFingerprint` (16 bytes), `TargetTripleFingerprint` (16 bytes), `StateSchemaId` (16 bytes), capability table offset/count, and exported interface table offset/count.
     - Serializer `axcomp_serialize_header`, parser `axcomp_parse_header`, and layout validator `axcomp_validate_section` detecting corruption or out-of-bounds offsets.

2. **Cross-Component Boundary Firewall, Allocator Isolation & Hot-Reload Verifier (`compiler/component/verify/mod.ax`)**:
   - Implemented diagnostic taxonomy for dynamic component operations (`AX_COMP_*`, 230u32..244u32, `AXS-COMP-050`).
   - Enforced cross-component boundary isolation rules (`AXS-COMP-020`..`025`):
     - Rejected raw pointer escapes (`*T`, `*mut T`) across safe `@component_interface` method parameters or return types with `AX_COMP_RAW_POINTER_ESCAPE`.
     - Rejected unleased `view<T>` / `mut_view<T>` crossing dynamic boundaries without an explicit `ComponentLease` epoch contract with `AX_COMP_UNLOAD_ACTIVE_LEASES`.
     - Rejected plain host `Box<T>`, `Vec<T>`, or `String` allocations by value across component boundaries with `AX_COMP_CROSS_ALLOCATOR_VIOLATION`, requiring `ComponentBox<T>` or generational `ComponentHandle<T>`.
     - Permitted safe passing modes: `PARAM_PASS_BY_VAL`, `PARAM_PASS_COMPONENT_BOX`, `PARAM_PASS_COMPONENT_HANDLE`, and `PARAM_PASS_OPAQUE_PTR`.
   - Enforced generational handle safety (`ComponentHandle<T>`, `AXS-COMP-022`) detecting stale generation or epoch counters with `AX_COMP_STALE_HANDLE`.
   - Enforced epoch lease tracking (`ComponentLease`, `AXS-COMP-023`) preventing physical library unloading while `active_leases > 0` with `AX_COMP_UNLOAD_ACTIVE_LEASES`.
   - Implemented capability manifest verification (`AXS-COMP-013`): rejected undeclared or ungranted capabilities with `AX_COMP_CAPABILITY_DENIED`.
   - Implemented host component registry checking (`AXS-COMP-002`): rejected duplicate `(ComponentId, SemVer)` registrations with `AX_COMP_DUPLICATE_REGISTRATION`.
   - Implemented `@hot_reload_state` deterministic schema hashing (`compute_state_schema_id`) and `@hot_reload_migration` hook validation (`AXS-COMP-032`, `AXS-COMP-034`):
     - Executed fast-path identity when `active_schema == candidate_schema`.
     - Detected schema changes and rejected missing migration hooks with `AX_COMP_HOT_RELOAD_SCHEMA_MISMATCH`.
     - Detected invalid migration hook signatures with `AX_COMP_HOT_RELOAD_MIGRATION_FAILED`.

3. **Comprehensive Tests (`tests/run/component_interface/`)**:
   - Multi-module oracle probe bundle (`component_interface.test`, `component_interface_oracle.py`, `component_interface_probe.ax.in`):
     - Assembled 16 compiler modules (`compiler.abi.*`, `compiler.component.*`, plus kernel/diag/source dependencies) and verified byte-identical probe output across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
   - Standalone run fixtures:
     - `component_interface_vtable_axcomp.ax` (+ `.stdout`): verified vtable sizing, SemVer caret matching, ComponentId syntax, and `.axcomp` section header serialization/validation round-trip.
     - `boundary_firewall_cross_allocator.ax` (+ `.stdout`): verified compile-time rejection of raw pointer escapes, unleased views, plain host boxes/collections, acceptance of generational handles/boxes/opaque pointers, stale handle detection, active lease unload blocking, capability grants, and duplicate registration checks.
     - `hot_reload_state_schema_migration.ax` (+ `.stdout`): verified deterministic `StateSchemaId` computation, schema distinctness, fast-path schema identity, missing migration rejection, invalid signature rejection, and valid migration transitions.

## Verification

Executed:
```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/component_interface
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
archcheck: 200 files scanned, 0 violations
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

- compiler/component/interface/mod.ax
- compiler/component/verify/mod.ax
- tests/run/component_interface/boundary_firewall_cross_allocator.ax
- tests/run/component_interface/boundary_firewall_cross_allocator.stdout
- tests/run/component_interface/component_interface.test
- tests/run/component_interface/component_interface_oracle.py
- tests/run/component_interface/component_interface_probe.ax.in
- tests/run/component_interface/component_interface_vtable_axcomp.ax
- tests/run/component_interface/component_interface_vtable_axcomp.stdout
- tests/run/component_interface/hot_reload_state_schema_migration.ax
- tests/run/component_interface/hot_reload_state_schema_migration.stdout
- tests/run/component_interface/spec115_edge_cases.ax
- tests/run/component_interface/spec115_edge_cases.stdout

## Status

STATUS: COMPLETE round=0
