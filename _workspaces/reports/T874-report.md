# T874 Report — E20.6 Canonical native SDK, declarative .axsdk sysroot metadata, AXTOOLCHAIN descriptor & toolchain distribution specification (`SPEC-116`)

## Summary

Implemented task **T874** by drafting the canonical specification `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` for Milestone **E20.6** (Phase `P20`), establishing the formal architecture and operational requirements for Axiom's C-free Native SDK (`.axsdk`), declarative sysroot metadata, target/ABI/object-pipeline descriptors (`AXTOOLCHAIN`), domain-separated cryptographic fingerprinting (`SdkFingerprint`, `ToolchainFingerprint`), deterministic `axiom.lock` SDK pinning, and hermetic toolchain/sysroot archive distribution (`REQ-ECO-8736`, `REQ-PKG-022`):

1. **Architectural Separation of Compiler, Platform SDK, and Sysroot (`SPEC-116 §1`, `AXS-SDK-001`..`AXS-SDK-009`)**:
   - Enforced tripartite separation of concerns: Compiler (`axiomc` — language semantics, type checker, borrow checker, MIR, optimizations, LIR, code generation), Platform SDK (`.axsdk` — platform ABI metadata, syscall tables, dynamic import stubs, CRT startup contracts, OS availability limits), and Sysroot (isolated filesystem root).
   - Codified the **C-Free Native SDK Invariant (`AXS-SDK-002`)**: Axiom never hard-codes ambient host OS paths (`C:\Windows`, `C:\Program Files (x86)\Windows Kits`, `/usr/include`, `/Library/Developer/...`), never executes a third-party C compiler (`gcc`, `clang`, `cl.exe`), and never parses C `.h` headers to compile pure Axiom code.
   - Enforced **Ambient Host Path Fallback Prohibition (`AXS-SDK-004`)**: Under hermetic compilation (`--hermetic` or default workspace builds), any fallback to ambient host OS paths without an explicitly configured `--sysroot` or installed `.axsdk` fails immediately with `AX_SDK_HOST_FALLBACK_DENIED`.
   - Guaranteed universal cross-compilation host independence (`AXS-SDK-005`), freestanding vs hosted profile separation (`AXS-SDK-006`), modular runtime decoupling (`AXS-SDK-007`), language semantic core invariance across SDK versions (`AXS-SDK-008`), and purely declarative manifest authority without imperative build scripts (`AXS-SDK-009`).

2. **Declarative `.axsdk` Manifest & Platform Sysroot Schema (`SPEC-116 §2`, `AXS-SDK-010`..`AXS-SDK-024`)**:
   - Specified authoritative top-level manifest schema `sdk.toml` (`[sdk]`, `[target]`, `[os]`, `[capabilities]`, `[crt]`, `[linker]`).
   - Specified declarative syscall and dynamic import stub tables (`.axstub.toml`) for PE DLLs (`kernel32.dll`, `ntdll.dll`), ELF shared objects (`libc.so.6`, `libm.so.6`), Darwin text-based stubs (`.tbd`), and Android Bionic stubs.
   - Specified executable subsystem startup contracts (`console`, `windows`, `posix`, `freestanding`, `reactor`), entry symbols, and CRT init sections.
   - Formulated compile-time API availability gating via `@available(os = ..., min_version = ...)` (`AXS-SDK-015`), rejecting unguarded calls to APIs newer than deployment target with `AX_SDK_API_UNAVAILABLE`.
   - Standardized weak and optional linkage contracts (`Required`, `WeakLinked`, `RuntimeResolved`), Windows import libraries and DLL forwarders, Linux direct syscall tables, Android Bionic multi-API sysroots without NDK dependency, WASM/WASI virtual imports, bare-metal embedded linker script fragments, precompiled `std` `.axmeta` interface integration, and the canonical on-disk sysroot file tree layout.

3. **`AXTOOLCHAIN` Descriptors across Tier-1 and Tier-2 Targets (`SPEC-116 §3`, `AXS-SDK-025`..`AXS-SDK-034`)**:
   - Specified `toolchain.toml` schema covering 4 Tier-1 targets (`x86_64-windows` [LLP64, COFF/PE], `x86_64-linux` [LP64, ELF64], `aarch64-linux` [LP64, ELF64], `aarch64-macos` [LP64, Mach-O 64]) and 4 Tier-2 targets (`aarch64-windows` [LLP64, COFF/PE-ARM64], `aarch64-android` [LP64, ELF64], `wasm32` [ILP32, WASM], `riscv64-linux` [LP64, ELF64]).
   - Specified ABI calling conventions (`win64`, `sysv64`, `aapcs64`, `darwin_arm64`, `lp64d`), register preservation, struct sizing/packing/alignment (`@repr(packed)`, `@align(N)`), SIMD and hard/soft-float register contracts.
   - Specified native direct machine code emission (`DirectEmission` for COFF, ELF64, Mach-O, WASM), relocation models (`static`, `pic`, `pie`), native Axiom linker integration (`AxiomLinker`), DWARF 5 / Windows SEH / Mach-O Compact Unwind debug and unwind pipelines, and reproducible platform signing (macOS ad-hoc `LC_CODE_SIGNATURE` and Windows Authenticode stubs).

4. **Domain-Separated Cryptographic Fingerprints & `axiom.lock` Pinning (`SPEC-116 §4`, `AXS-SDK-035`..`AXS-SDK-042`)**:
   - Specified 256-bit BLAKE3 domain-separated `SdkFingerprint` (over `b"AXIOM_SDK_FINGERPRINT_V1\x00"`, normalized triple, canonical manifest, and sorted Merkle root of sysroot files).
   - Specified 256-bit BLAKE3 domain-separated `ToolchainFingerprint` (over `b"AXIOM_TOOLCHAIN_FINGERPRINT_V1\x00"`, toolchain metadata, compiler binary hash, and backend descriptors).
   - Specified declarative `axiom.lock` `[sdk]` and `[toolchain]` pinning schemas.
   - Enforced strict fingerprint verification under `--locked` and `--frozen`, rejecting any mismatch with `AX_SDK_LOCK_MISMATCH`.
   - Integrated fingerprints directly into `CompilerDB` build graph action cache keys.

5. **Hermetic Distribution, Offline Mirrors & CLI (`SPEC-116 §5`, `AXS-SDK-043`..`AXS-SDK-055`)**:
   - Specified content-addressed distribution archives (`.axsdk`, `.axtoolchain`) with Zstandard compression, normalized POSIX paths, `mtime = 0`, normalized permissions (`0644`/`0755`), and Ed25519 digital signatures (`SPEC-113` integration).
   - Specified immutable side-by-side local installation cache (`~/.axiom/sdks/`, `~/.axiom/toolchains/`) with atomic extraction and read-only enforcement.
   - Specified air-gapped local mirror protocol (`--mirror`, `--offline`).
   - Specified complete CLI subcommands: `axiomc sdk list|install|verify|inspect|pin` and `axiomc toolchain list|install|default|verify|pin` with deterministic exit codes (`0`, `1`, `2`, `3`, `4`, `5`).
   - Codified the **Two-Machine Bit-for-Bit Workspace Reproducibility Contract (`AXS-SDK-055`, `REQ-PKG-022`)**.

6. **Index, Diagnostics & Invariants Integration**:
   - Updated `spec/INDEX.md` with `SPEC-116` metadata row, rule prefix `AXS-SDK-NNN`, and functional area coverage entry.
   - Updated `spec/diagnostics.md` with 13 canonical diagnostic codes (`AX_SDK_*`).
   - Registered Section 57 in `spec/invariants.md` with `INV-SDK-001`, `INV-SDK-002`, and `INV-SDK-003` (with valid `since:` tags pointing to `T875`, `T876`, `T877`).

## Verification

Executed verification suite:
- `python tools/archcheck.py` → 200 files scanned, 0 violations.
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → requirements: 32308, gaps: 0 / COVERAGE OK.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → HARNESS OK.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T874` → verified all modified and created files match task scope.

## Files changed

- spec/SPEC-116-sdk-sysroot-toolchain-distribution.md
- spec/INDEX.md
- spec/diagnostics.md
- spec/invariants.md

## Status

STATUS: COMPLETE round=0
