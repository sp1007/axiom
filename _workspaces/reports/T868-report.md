# T868 Report: E20.5 Versioned Symbol Mangling/Export Tables, .axmeta Binary Compatibility Checker & axiomc abi-check SemVer Diff CLI

## Summary

Implemented Milestone **E20.5** (`T868`) in the self-hosted Axiom compiler (`compiler/abi/compat_diff/mod.ax` and `compiler/driver/abi_cmd/mod.ax`) per `SPEC-114 §§4..5`, `REQ-ECO-8734`, `REQ-PKG-022`, and `REQ-PKG-024`:

1. **Versioned Symbol Mangling & Export Table Metadata Engine (`compiler/abi/compat_diff/mod.ax`)**:
   - Implemented canonical versioned symbol mangling per `SPEC-114 §4`:
     - Mangled exports: `axiom_<pkg>_<mod>_<ident>@@<version>` for default exports (`default = true`) and `axiom_<pkg>_<mod>_<ident>@<version>` for non-default historical versions (`default = false`).
     - Windows PE/COFF `.edata` export table alias generation (`SPEC-114 §4 AXS-ABI-031`): unadorned export `<ident>` for default versions and decorated export `<ident>_v<ver>` for version-specific entries.
     - Implemented `validate_versioned_export_coexistence`: verified that multiple ABI versions of an exported function can coexist cleanly in a shared library without symbol or export alias collision (`REQ-ECO-8734`), rejecting duplicates and conflicting multiple default exports with `AX_ABI_SYMBOL_VERSION_DUPLICATE`.

2. **`.axmeta` Binary & API Compatibility Diff Engine (`compiler/abi/compat_diff/mod.ax`)**:
   - Implemented `diff_interface_descriptors` comparing baseline (`old`) and candidate (`new`) `.axmeta` interface descriptors, classifying differences into individual items and overall compatibility classes (`AXS-ABI-040`):
     - `identical` (`COMPAT_CLASS_IDENTICAL`): both `AbiFingerprint` and `ApiFingerprint` are identical and implementation hash is unchanged.
     - `implementation-only` (`COMPAT_CLASS_IMPL_ONLY`): `AbiFingerprint` and `ApiFingerprint` are identical; only private body/implementation changed.
     - `minor-additive` (`COMPAT_CLASS_MINOR_ADDITIVE`): new exported functions/structs/enums, new `@symbol_version` definitions, relaxed capability preconditions, or fields appended to `@extensible` structs with version bump and preserved offsets.
     - `major-breaking` (`COMPAT_CLASS_MAJOR_BREAKING`): removed exported functions/structs/enums, altered struct field offsets/sizes/alignments, fields added to non-extensible structs, modified function parameter counts/types, altered calling conventions, changed return types, tightened capability sets, removed `@symbol_version` tags, or altered enum discriminant values.
   - Implemented structured formatters `render_diff_text` and `render_diff_json` emitting human-readable and deterministic JSON reports conforming to `SPEC-114 §5 AXS-ABI-041`.

3. **`axiomc abi-check` SemVer Compatibility Enforcer & CLI Driver (`compiler/driver/abi_cmd/mod.ax`)**:
   - Implemented CLI argument parsing and driver execution for `axiomc abi-check --old <base.axmeta> --new <cand.axmeta> --semver <old_ver>:<new_ver> [--format text|json]`:
     - Full option validation (`--old`, `--new`, `--semver`, `--format`, `--json`, `--help`).
     - SemVer parser and increment classifier (`evaluate_semver_bump`) parsing `major.minor.patch` and classifying transitions into `BUMP_PATCH`, `BUMP_MINOR`, `BUMP_MAJOR`, and `BUMP_DOWNGRADE`.
     - Strict SemVer policy matrix enforcement (`SPEC-114 §5 AXS-ABI-040..041`):
       - Patch release (`1.2.3 -> 1.2.4`): permits `identical` and `implementation-only`; rejects `minor-additive` with exit code `2` (`AX_ABI_SEMVER_MISMATCH`) and rejects `major-breaking` with exit code `1` (`AX_ABI_BREAKING_CHANGE`).
       - Minor release (`1.2.3 -> 1.3.0`): permits `identical`, `implementation-only`, and `minor-additive`; rejects `major-breaking` with exit code `1` (`AX_ABI_BREAKING_CHANGE`).
       - Major release (`1.2.3 -> 2.0.0`): permits `major-breaking`, `minor-additive`, and compatible changes with exit code `0`.
       - Invalid options, missing inputs, or malformed arguments exit with code `3`.

4. **Comprehensive Test Suite & Oracle Probe (`tests/run/abi_compat_diff/`)**:
   - Multi-module oracle test suite (`abi_compat_diff.test`, `abi_compat_diff_oracle.py`, `abi_compat_diff_probe.ax.in`):
     - Assembled full compiler modules (`stability`, `fingerprint`, `compat_diff`, `abi_cmd` + dependencies) and verified byte-identical probe execution parity across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each`.
   - Standalone fixtures:
     - `struct_evolution_compat.ax`: verified field offset shifts, alignment changes, non-extensible struct breakages, and extensible struct field append with header version bump.
     - `signature_capability_compat.ax`: verified calling convention breaks, parameter count breaks, return type changes, passing mode breaks, capability tightening (breaking), and capability relaxation (additive).
     - `semver_policy_enforcement.ax`: verified SemVer bump evaluation and enforcement of patch, minor, and major release policy matrix and exit codes.
     - `symbol_version_coexistence.ax`: verified `@symbol_version("1.0")` + `@symbol_version("2.0")` mangling (`@` vs `@@`), PE export aliases, clean shared-library export coexistence, and duplicate version rejection (`REQ-ECO-8734`).

## Verification

Executed:
```bash
python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/abi_compat_diff
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

- compiler/abi/compat_diff/mod.ax
- compiler/driver/abi_cmd/mod.ax
- tests/run/abi_compat_diff/abi_compat_diff.test
- tests/run/abi_compat_diff/abi_compat_diff_oracle.py
- tests/run/abi_compat_diff/abi_compat_diff_probe.ax.in
- tests/run/abi_compat_diff/semver_policy_enforcement.ax
- tests/run/abi_compat_diff/semver_policy_enforcement.stdout
- tests/run/abi_compat_diff/signature_capability_compat.ax
- tests/run/abi_compat_diff/signature_capability_compat.stdout
- tests/run/abi_compat_diff/struct_evolution_compat.ax
- tests/run/abi_compat_diff/struct_evolution_compat.stdout
- tests/run/abi_compat_diff/symbol_version_coexistence.ax
- tests/run/abi_compat_diff/symbol_version_coexistence.stdout

## Status

STATUS: COMPLETE round=0
