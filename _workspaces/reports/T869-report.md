# T869 Report: E20.5 ABI stability tiers, versioned symbol exports, .axmeta binary compatibility & axiomc abi-check conformance suite

## Summary

Implemented Milestone **E20.5** (`T869`) by constructing the comprehensive end-to-end conformance test suite in `tests/conformance/p20/e20_5_abi_stability_compat/` per `spec/SPEC-114-abi-stability-versioning-binary-compat.md`, `REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`, and invariants `INV-SABI-001`, `INV-SABI-002`, `INV-SABI-003`:

1. **Master Conformance Oracle & Live Multi-Module Probe (`e20_5_abi_stability_compat_oracle.test`, `e20_5_abi_stability_compat_oracle.py`, `e20_5_abi_stability_compat_probe.ax.in`)**:
   - Assembles live compiler modules `compiler/abi/stability/mod.ax`, `compiler/abi/fingerprint/mod.ax`, `compiler/abi/compat_diff/mod.ax`, and `compiler/driver/abi_cmd/mod.ax` (with kernel, source, span, interner, diag, format, json, and query DB dependencies).
   - Verifies byte-identical execution parity across `--interp` and native `-O0` compilation (compiled at most once per `<120s` resource budget).
   - Proves differential agreement (`--interp` vs native `-O1 --verify-each`) across all 4 standalone `.ax` conformance fixtures (`0 WEAK-NATIVE`).
   - Audits linked production binaries confirming zero leaked `.axmeta`, `.axdb`, `.axmir`, `.axoracle`, or `.axlto` metadata sections or tokens.

2. **Standalone Conformance Fixtures (`tests/conformance/p20/e20_5_abi_stability_compat/`)**:
   - `abi_tiers_and_opaque_handle_evolution.ax` + `.stdout`: Certified 3-tier ABI separation (Tier 1 internal `extern "axiom"` with open-world optimizations, Tier 2 `.axmeta` package interface, Tier 3 `@abi(stable, version = "1.0")` frozen binary boundary; `AXS-ABI-001..003`), opaque handle evolution across 3 versions where internal field additions, size changes, and alignment shifts behind `@opaque` pointer handles preserve downstream consumer compatibility without recompilation and keep public `AbiFingerprint` strictly invariant (`0104 §11-12`, `tasks/0452 §193.16-17`, `AXS-ABI-013`, `INV-SABI-001`), and compile-time rejection of `@opaque` by-value instantiation (`AX_ABI_OPAQUE_BY_VALUE` = 222).
   - `boundary_type_rejection_firewall.ax` + `.stdout`: Certified stable ABI firewall (`AXS-ABI-004`, `REQ-ECO-8734`), allowed stable types (scalars, pointer handles, canonical `StableView<T>`, `StableStr`, allocator-paired `StableBuffer<T>`; `AXS-ABI-010..015`), compile-time rejection of unstable types with `AX_ABI_UNSTABLE_TYPE` (capturing closures, unrepr'd ADTs, uninstantiated generics, bare fat pointers `view`/`mut_view`/`Str`, raw slices by value, `dyn Trait`, unallocated `String`/`Vec`; `AXS-ABI-017`), raw generic export rejection (`AX_FFI_GENERIC_EXPORT`; `AXS-ABI-016`), and extensible struct header verification (`AX_ABI_EXTENSIBLE_MISSING_HEADER`; `AXS-ABI-011`).
   - `fingerprint_triple_and_symbol_versioning.ax` + `.stdout`: Certified three independent 128-bit BLAKE3 fingerprint domains (`ApiFingerprint`, `SemanticFingerprint`, `AbiFingerprint`; `AXS-ABI-020..024`, `tasks/0583 §324.2`, `tasks/0739 §493.21-23`, `INV-SABI-002`), invariance under non-inlined private edits vs inlined MIR vs physical layout shifts, deterministic `@symbol_version` mangling (`axiom_<pkg>_<mod>_<ident>@<version>` vs `@@<version>`), Windows PE/COFF `.edata` export aliases (`ident_v1_0` vs `ident`), multi-version coexistence in shared libraries, and duplicate symbol version rejection (`AX_ABI_SYMBOL_VERSION_DUPLICATE`; `AXS-ABI-030..032`).
   - `abi_check_semver_compliance_matrix.ax` + `.stdout`: Certified `axiomc abi-check` SemVer compliance matrix (`AXS-ABI-040..042`, `REQ-PKG-022`, `REQ-PKG-024`), 3-way change classification (`compatible`, `minor-additive`, `major-breaking`), policy enforcement across patch, minor, major, downgrade, and no-semver modes with exact exit codes (0=PASS, 1=`AX_ABI_BREAKING_CHANGE`, 2=`AX_ABI_SEMVER_MISMATCH`), and JSON/text diagnostic report serialization.

3. **Normative Traceability Mapping (`README.md`)**:
   - Mapped every `SPEC-114` requirement (`AXS-ABI-001`..`053`, `REQ-ECO-8734`, `REQ-PKG-022`, `REQ-PKG-024`, `INV-SABI-001`..`003`) to concrete conformance fixtures.

## Verification

Executed:
```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p20/e20_5_abi_stability_compat
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

- tests/conformance/p20/e20_5_abi_stability_compat/README.md
- tests/conformance/p20/e20_5_abi_stability_compat/abi_check_semver_compliance_matrix.ax
- tests/conformance/p20/e20_5_abi_stability_compat/abi_check_semver_compliance_matrix.stdout
- tests/conformance/p20/e20_5_abi_stability_compat/abi_tiers_and_opaque_handle_evolution.ax
- tests/conformance/p20/e20_5_abi_stability_compat/abi_tiers_and_opaque_handle_evolution.stdout
- tests/conformance/p20/e20_5_abi_stability_compat/boundary_type_rejection_firewall.ax
- tests/conformance/p20/e20_5_abi_stability_compat/boundary_type_rejection_firewall.stdout
- tests/conformance/p20/e20_5_abi_stability_compat/e20_5_abi_stability_compat_oracle.py
- tests/conformance/p20/e20_5_abi_stability_compat/e20_5_abi_stability_compat_oracle.test
- tests/conformance/p20/e20_5_abi_stability_compat/e20_5_abi_stability_compat_probe.ax.in
- tests/conformance/p20/e20_5_abi_stability_compat/fingerprint_triple_and_symbol_versioning.ax
- tests/conformance/p20/e20_5_abi_stability_compat/fingerprint_triple_and_symbol_versioning.stdout

## Status

STATUS: COMPLETE round=0
