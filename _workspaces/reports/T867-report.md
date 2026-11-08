# T867 Report: E20.5 @abi(stable) Boundary Typechecker, Layout Verifier & AbiFingerprint/ApiFingerprint Engine

## Summary

Implemented Milestone **E20.5** (`T867`) in the self-hosted Axiom compiler (`compiler/abi/stability/mod.ax` and `compiler/abi/fingerprint/mod.ax`) per `SPEC-114 §§1..3 & §6`, `REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-SABI-001`, and `INV-SABI-002`:

1. **`@abi(stable)` Boundary Typechecker & Layout Verifier (`compiler/abi/stability/mod.ax`)**:
   - Implemented `compiler.abi.stability` enforcing the Stable Axiom ABI Type System across `@abi(stable)` dynamic shared library boundaries (`AXS-ABI-001`..`017`, `INV-SABI-001`).
   - Permitted types: fixed-width primitive scalars (`i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`, `bool`), raw machine pointers (`*const T`, `*mut T`), canonical stable views (`StableView<T>`, `StableMutView<T>`, `StableStr`), allocator-paired owned buffers (`StableBuffer<T>`), explicit tagged enums (`@repr(u8..u64)`), and encapsulated `@opaque` handles.
   - Enforced compile-time rejection of unstable types (`AXS-ABI-017`): capturing closures (`UNSTABLE_CLOSURE_CAPTURING`), unrepr ADTs (`UNSTABLE_UNREPR_ADT`), uninstantiated generic exports (`AX_FFI_GENERIC_EXPORT`), bare fat pointers (`view<T>`, `mut_view<T>`, `Str`), and bare trait objects (`dyn Trait`), emitting structured `AX_ABI_UNSTABLE_TYPE` diagnostics with causal details.
   - Implemented extensible struct layout validation (`AXS-ABI-011`): verified presence of mandatory `AbiHeader` (`abi_version: u32, struct_size: u32`), emitting `AX_ABI_EXTENSIBLE_MISSING_HEADER` on invalid headers.
   - Implemented `@opaque` handle type isolation (`AXS-ABI-013`): allowed handle passing via pointer (`*mut T` / `*const T`), and strictly rejected instantiation or passing/returning by value outside the defining module with `AX_ABI_OPAQUE_BY_VALUE`.
   - Implemented symbol version group validation (`AXS-ABI-030`): detected duplicate `@symbol_version` strings and conflicting multiple `default = true` implementations, emitting `AX_ABI_SYMBOL_VERSION_DUPLICATE`.

2. **Deterministic Cryptographic Fingerprint Engine (`compiler/abi/fingerprint/mod.ax`)**:
   - Implemented `compiler.abi.fingerprint` calculating distinct, deterministic 128-bit digests for the three independent fingerprint domains (`AXS-ABI-020`..`024`, `INV-SABI-002`):
     - `ApiFingerprint` (domain `"AXIOM-API-v1\0"`): hashes exported item names, parameter names/types/order, return types, public struct fields, and enum variants/discriminants. Strictly invariant under private function body modifications, comments, formatting, and optimization flags.
     - `SemanticFingerprint` (domain `"AXIOM-SEM-v1\0"`): incorporates `ApiFingerprint` with normalized inlined MIR function bodies, comptime constant values, and capability/effect contracts (`Pure`, `ReadsMem`, `WritesMem`, `NoPanic`). Strictly invariant under non-inlined body edits.
     - `AbiFingerprint` (domain `"AXIOM-ABI-v1\0"`): incorporates target platform descriptor (`arch`, `os`, `pointer_width`, `endianness`, `cpu_features`), calling conventions (`Win64`, `SysV64`, `AAPCS64`, `C`), physical type sizes, alignments, field offsets, extensible headers, and `@symbol_version` strings.
   - Enforced the **Opaque Handle Layout Isolation Guarantee** (`AXS-ABI-013`, `AXS-ABI-023 §3`, `INV-SABI-001`): internal field additions or layout modifications behind an `@opaque` pointer handle do not alter the public `AbiFingerprint`.
   - Verified that physical layout modifications (changing field offsets, struct sizes, calling conventions, symbol versions) immediately alter `AbiFingerprint`.

3. **End-to-End Verification & Differential Parity (`tests/run/abi_stability/`)**:
   - Added oracle test suite and multi-tier probe bundle (`abi_stability.test`, `abi_stability_oracle.py`, `abi_stability_probe.ax.in`):
     - Executed the bundled real compiler modules across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` verifying byte-identical probe output parity.
   - Added standalone `.ax` + `.stdout` fixtures:
     - `boundary_typeck_firewall.ax`: verified scalar validation, extensible struct header checking, unstable closure/ADT rejection, and duplicate symbol version rejection.
     - `opaque_handle_isolation.ax`: verified opaque handle pointer safety, by-value rejection, and internal layout isolation.
     - `fingerprint_invariance_triple.ax`: verified independent `ApiFingerprint`, `SemanticFingerprint`, and `AbiFingerprint` invariance across private body edits, `@inline` changes, and layout modifications.

## Verification

Executed:
```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/abi_stability
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
archcheck: 199 files scanned, 0 violations
```

Executed:
```bash
python .claude/skills/axiom-tasks/scripts/reqcov.py --strict
```
Result:
```
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

- compiler/abi/stability/mod.ax
- compiler/abi/fingerprint/mod.ax
- tests/run/abi_stability/abi_stability.test
- tests/run/abi_stability/abi_stability_oracle.py
- tests/run/abi_stability/abi_stability_probe.ax.in
- tests/run/abi_stability/boundary_typeck_firewall.ax
- tests/run/abi_stability/boundary_typeck_firewall.stdout
- tests/run/abi_stability/opaque_handle_isolation.ax
- tests/run/abi_stability/opaque_handle_isolation.stdout
- tests/run/abi_stability/fingerprint_invariance_triple.ax
- tests/run/abi_stability/fingerprint_invariance_triple.stdout

STATUS: COMPLETE round=0
