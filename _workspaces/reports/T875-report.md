# T875 Report — E20.6 Declarative .axsdk sysroot loader, SdkFingerprint verifier, C-free platform import/CRT resolver & AXTOOLCHAIN target registry

## Summary

Implemented task **T875** for Milestone **E20.6** (Phase `P20`), delivering the complete compiler implementation and test suite for the declarative `.axsdk` sysroot loader, cryptographic `SdkFingerprint` verifier, C-free platform import and CRT startup contract resolver, and `AXTOOLCHAIN` target/ABI/object-pipeline registry per `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` (`AXS-SDK-001`..`AXS-SDK-042`, `INV-SDK-001`, `REQ-ECO-8736`, `REQ-PKG-022`):

1. **Declarative `.axsdk` Sysroot Loader & Validator (`compiler/sdk/sysroot/mod.ax`, `SPEC-116 §§1, 2`, `AXS-SDK-001`..`012`, `INV-SDK-001`)**:
   - Implemented `SysrootLoader` and `Sysroot` managing declarative `sdk.toml` and `.axstub.toml` metadata without probing ambient host OS paths (`C:\Windows`, `C:\Program Files (x86)\Windows Kits`, `/usr/include`, `/usr/lib`, `/Library/Developer/...`) or invoking host C toolchains (`cl.exe`, `gcc`, `clang`).
   - Implemented ambient host OS path detection via `sysroot_loader_is_ambient_host_path`. Under hermetic sysroot policy (`is_hermetic = true`), any attempt to resolve platform imports or headers from ambient host paths is strictly rejected with canonical diagnostic `AX_SDK_HOST_FALLBACK_DENIED`.

2. **C-Free Platform Dynamic Import Stubs & CRT Startup Contract Resolver (`SPEC-116 §2`, `AXS-SDK-013`..`024`)**:
   - Implemented `ImportSymbol` and `ImportLibrary` representing platform dynamic import stub contracts across PE DLLs (`kernel32.dll`, `ntdll.dll`), ELF shared objects (`libc.so.6`, `libm.so.6`), Darwin text-based stubs (`libSystem.B.dylib`), Android Bionic stubs, and WASM/WASI virtual imports.
   - Implemented linkage resolution supporting `Required`, `WeakLinked`, and `RuntimeResolved` modes, raising `AX_SDK_IMPORT_STUB_NOT_FOUND` on missing required imports.
   - Implemented `sysroot_resolve_startup_contract` mapping executable subsystems (`console` -> `main`, `windows` -> `WinMain`, `posix` -> `_start`, `freestanding` -> `_start`, `reactor` -> `_initialize`), verifying symbol availability and raising `AX_SDK_STARTUP_CONTRACT_MISMATCH` on missing subsystem entry points.

3. **Compile-Time OS API Availability Gating (`SPEC-116 §2`, `AXS-SDK-015`)**:
   - Implemented semantic target version comparison (`version_triple_cmp`) and Android API level checking.
   - Implemented `sysroot_gate_api_availability` for `@available(os = ..., min_version = ...)` constructs:
     - Rejects unguarded calls to APIs newer than the target deployment baseline with `AX_SDK_API_UNAVAILABLE`.
     - Permits APIs when guarded by runtime feature checks (`is_guarded = true`) or when the target version satisfies the minimum requirement.

4. **Domain-Separated Cryptographic `SdkFingerprint` Calculator & Verifier (`SPEC-116 §4`, `AXS-SDK-035`..`042`, `REQ-PKG-022`)**:
   - Implemented domain-separated 256-bit cryptographic digest over domain constant `AXIOM_SDK_FINGERPRINT_V1\0`, canonical target triple, manifest metadata, and lexicographically sorted sysroot Merkle entries (`sysroot_compute_merkle_root`).
   - Implemented `sysroot_verify_fingerprint` to validate sysroots against `axiom.lock` pinned hashes, rejecting tampered or mismatched sysroots with `AX_SDK_FINGERPRINT_MISMATCH`.

5. **`AXTOOLCHAIN` Target/ABI/Object-Pipeline Registry (`compiler/sdk/toolchain/mod.ax`, `SPEC-116 §3`, `AXS-SDK-025`..`034`, `REQ-ECO-8736`)**:
   - Registered authoritative `TargetDescriptor` profiles for all 4 Tier-1 targets (`x86_64-windows` [LLP64, COFF, win64], `x86_64-linux` [LP64, ELF64, sysv64], `aarch64-linux` [LP64, ELF64, aapcs64], `aarch64-macos` [LP64, Mach-O, darwin_arm64]) and all 4 Tier-2 targets (`aarch64-windows` [LLP64, COFF, aapcs64], `aarch64-android` [LP64, ELF64, aapcs64], `wasm32` [ILP32, WASM, wasm32_default], `riscv64-linux` [LP64, ELF64, lp64d]).
   - Implemented triple alias normalization mapping non-canonical GNU/LLVM triples (e.g., `x86_64-pc-windows-msvc` -> `x86_64-windows`, `arm64-apple-darwin` -> `aarch64-macos`, `wasm32-unknown-wasi` -> `wasm32`) to standard canonical triples.
   - Codified ABI properties: pointer width (32/64), data model, calling conventions, SIMD/float ABI, default page size (4096 / 16384 / 65536), direct object emission format (`COFF`, `ELF64`, `MachO`, `WASM`), native `AxiomLinker` pipeline integration, and unwind format (`WindowsSEH`, `Dwarf5`, `CompactUnwind`).
   - Implemented target validation reporting `AX_SDK_TOOLCHAIN_NOT_FOUND` for unrecognized triples and `AX_SDK_TOOLCHAIN_INCOMPATIBLE` for disabled target pipelines.

6. **Domain-Separated `ToolchainFingerprint` Calculator & Verifier (`SPEC-116 §4`, `AXS-SDK-035`..`042`)**:
   - Implemented domain-separated 256-bit cryptographic digest over domain constant `AXIOM_TOOLCHAIN_FINGERPRINT_V1\0`, canonical target triple, compiler binary hash, ABI calling convention, and object emission format.
   - Implemented `toolchain_verify_fingerprint`, rejecting mismatched toolchain configurations with `AX_SDK_TOOLCHAIN_FINGERPRINT_MISMATCH`.

7. **Multi-Module Oracle Probe & Standalone Run Fixtures (`tests/run/sdk_sysroot/`)**:
   - Developed `sdk_sysroot.test` + `sdk_sysroot_oracle.py` + `sdk_sysroot_probe.ax.in` multi-module oracle test suite executing 4 deep probe tiers across `--interp`, `-O0 --verify-each`, `-O1 --verify-each`, and `-O2 --verify-each` verifying byte-identical output parity.
   - Authored standalone run fixtures:
     - `axsdk_loader_import_crt_hermetic.ax` + `.stdout`: Sysroot loading, hermetic ambient path rejection (`AX_SDK_HOST_FALLBACK_DENIED`), and subsystem CRT startup contract verification.
     - `api_availability_gating_sdk_fingerprint.ax` + `.stdout`: Version triple comparison, availability gating (`AX_SDK_API_UNAVAILABLE`), and `SdkFingerprint` calculation & tamper rejection.
     - `axtoolchain_target_registry_fingerprint.ax` + `.stdout`: Complete 8-target matrix validation, triple alias normalization, and `ToolchainFingerprint` calculation & verification.

## Verification

Executed full verification suite:
- `python tools/archcheck.py` → 202 files scanned, 0 violations.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → requirements: 32308, gaps: 0 / COVERAGE OK.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → HARNESS OK.
- `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/sdk_sysroot` →
  `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0` (`0 WEAK-NATIVE`).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T875` → snapshot refreshed with 11 changed files.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T875` → 0 REFUSED lines.

## Files changed

- compiler/sdk/sysroot/mod.ax
- compiler/sdk/toolchain/mod.ax
- tests/run/sdk_sysroot/api_availability_gating_sdk_fingerprint.ax
- tests/run/sdk_sysroot/api_availability_gating_sdk_fingerprint.stdout
- tests/run/sdk_sysroot/axsdk_loader_import_crt_hermetic.ax
- tests/run/sdk_sysroot/axsdk_loader_import_crt_hermetic.stdout
- tests/run/sdk_sysroot/axtoolchain_target_registry_fingerprint.ax
- tests/run/sdk_sysroot/axtoolchain_target_registry_fingerprint.stdout
- tests/run/sdk_sysroot/sdk_sysroot.test
- tests/run/sdk_sysroot/sdk_sysroot_oracle.py
- tests/run/sdk_sysroot/sdk_sysroot_probe.ax.in

## Status

STATUS: COMPLETE round=0
