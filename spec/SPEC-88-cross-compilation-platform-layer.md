# SPEC-88 — Cross-Compilation, `@cfg` Target Matrix, Hermetic Sysroot/SDK & 3-Level OS Platform Layer

**Status:** draft (T681, 2026-11-04) | **Owner:** axiom-architect | **Phase:** P16 (`E16.8`: `T681`–`T684`) | **Prefixes:** `AXS-XCMP-NNN`, `AXS-PLAT-NNN`
**Consolidates:** `0097 §1–61` (`AOS-01..35`); `0220 §1–40` (`AOS-20..40`); `tasks/0336 §15–24, §49–52, §73–80` (`AFFI2-20..100`); `tasks/0453 §194.1–194.44` (`ATARGET-20..50`); `tasks/0587 §1–40` (`ATARGET-01..30`); `tasks/0518 §151` (`AMACHINE-91..95`); `tasks/0524 §112–113` (`ABACKEND-93..100`).
**Covers:** `REQ-TOOL-001`, `REQ-TGT-080`..`REQ-TGT-084`, `REQ-TGT-318`..`REQ-TGT-326`; integrates with `ADR-0002`, `ADR-0003`, `ADR-0006`, `SPEC-02`, `SPEC-04`, `SPEC-20`, `SPEC-21`, `SPEC-22`, `SPEC-23`, `SPEC-24`, `SPEC-26`, `SPEC-27`, `SPEC-44`, `SPEC-50`, `SPEC-51`, `SPEC-52`, `SPEC-53`, `SPEC-54`, `SPEC-60`, `SPEC-61`, `SPEC-80`..`SPEC-87`, `spec/invariants.md` (`INV-XCMP-001`..`003`), and `spec/diagnostics.md`.
**Consumers:** `T682` (`compiler/hir/cfg`, `compiler/driver/cross`), `T683` (`std/os`, `compiler/link/sysroot`), `T684` (`tests/conformance/p16/e16_8_cross_compile`), `E16.10` (`T685`–`T688`), `E16.11` (`T689`–`T692`), `E16.12` (`T693`–`T696`).

## Tóm tắt

Đặc tả này ấn định kiến trúc **biên dịch chéo đơn nhị phân** (*single-binary cross-compilation*), ma trận biên dịch có điều kiện **`@cfg(...)`**, cơ chế **sysroot/SDK kín** (*hermetic sysroot*) không phụ thuộc trình biên dịch bên thứ ba (`REQ-TOOL-001`), và mô hình **3 tầng hệ điều hành & nền tảng** của Axiom.
Mọi bản dựng phân tách nghiêm ngặt ba miền **`Build`**, **`Host`**, và **`Target`**: ngữ nghĩa Core và frontend hoàn toàn độc lập với ISA (`REQ-TGT-080`, `REQ-TGT-322`..`326`), `Axiom LIR` là biên khả chuyển ngữ nghĩa duy nhất trước hợp đồng `TargetBackend` tự thân khả tự biên dịch (`REQ-TGT-081`..`084`, `REQ-TGT-324`..`325`), còn định trị `const`/`comptime` (`size_of<T>()`, `align_of<T>()`, `usize`/`isize`, thứ tự byte) luôn tham số hóa theo `TargetDesc` của đích thay vì máy chủ biên dịch.
Thuộc tính cấu trúc `@cfg(...)` thay thế hoàn toàn bộ tiền xử lý văn bản kiểu C: trình biên dịch phân tích cú pháp **toàn bộ** nhánh (kể cả nhánh không kích hoạt), kiểm chứng tập khóa/giá trị đóng (`AX_NAME_INVALID_CFG_PREDICATE`), rồi cắt tỉa AST sang HIR **trước** bước phân giải tên và kiểm kiểu.
Khi liên kết chéo, `axiomc` tích hợp sẵn kho stub nhập khẩu hệ thống thuần Axiom (`kernel32`/`ntdll`/`ws2_32`/`bcrypt`, `libc`/`libm`/`libdl`/`libpthread`, Bionic, `libSystem.B.dylib`, `wasi_snapshot_preview1`), tuyệt đối không dò đường dẫn thư viện của máy chủ, và bảo đảm đầu ra tất định từng byte giữa các hệ điều hành chủ (`Windows`, `Linux`, `macOS`; `REQ-TGT-319`..`320`).
Cuối cùng, tầng hệ điều hành tách thành **Mức 1** (`std.io`, `std.fs`, `std.path`, `std.env`, `std.process`, `std.time`, `std.thread`, `std.sync`, `std.net` — API khả chuyển, UTF-8, `!Copy` + `Drop` + `close() -> Result`), **Mức 2** (`std.os.{windows,linux,macos,android,wasi,unix}` — mở rộng đặc thù OS dưới `@cfg` với handle mờ định kiểu an toàn), và **Mức 3** (`std.sys.*` — ABI hệ thống thô nội bộ định tuyến tĩnh từ `std.core.host`).

---

## 1. Unified Multi-Target Compiler, `Build`/`Host`/`Target` Isolation & Backend Contract (`AXS-XCMP-001`..`010`)

**AXS-XCMP-001 — Unified Single-Binary Cross-Compiler & Zero Third-Party Toolchain Dependency (`REQ-TOOL-001`, `ATARGET-01, 20, 49`).** Every native `axiomc` binary is a universal multi-target compiler (`tasks/0453 §194.1, §194.43`, `tasks/0587 §1, §13`, `0097 §27, §54`). A single `axiomc` executable embeds all registered `TargetDesc` descriptors, `CallConvDesc` ABI engines, `IsaTable` instruction selectors, `verify_mc` / `verify_wasm` machine verifiers (`SPEC-81`), native machine encoders (`x86_64`, `aarch64`, `riscv64`, `wasm32`), binary container writers (`PE32+/COFF`, `ELF64`, `Mach-O 64`, `.wasm`, `.axmi`; `SPEC-24`), static archive builders (`COFF .lib`, `GNU ar .a`, `BSD ar .a`; `SPEC-26`, `SPEC-80`, `SPEC-84`), and static/dynamic image linkers (`SPEC-26`, `SPEC-27`, `SPEC-80`, `SPEC-82`..`SPEC-87`). Invoking `axiomc build --target <triple>` (or declaring `[build] target = "<triple>"` in `axiom.toml`, defaulting to the host triple only when omitted) emits final runnable executables, static libraries, shared libraries, relocatable objects, and `.wasm` modules from any supported host OS without invoking `clang`, `gcc`, `cl.exe`, `link.exe`, `ld`, `lld`, `ld64`, `as`, `ar`, `wasm-ld`, or `codesign` (`REQ-TOOL-001`). Passing an unregistered `<triple>` terminates immediately with `AX_DRIVER_UNKNOWN_TARGET` (exit code `2`; `spec/diagnostics.md` §10.7). [0097 §27, §54; tasks/0453 §194.1, §194.43, ATARGET-20, ATARGET-49; tasks/0587 §1, §13, ATARGET-01; SPEC-04 AXS-EXT-052; SPEC-81 AXS-TGTD-001..003; REQ-TOOL-001]

**AXS-XCMP-002 — Canonical Target Matrix & Triple Normalization (`0097 §3`, `tasks/0453 §194.2–3`, `tasks/0587 §1–4`).** `compiler/driver/cross` parses `--target <triple>` case-sensitively, maps vendor-expanded LLVM/GNU aliases deterministically to a canonical `TargetId` (`SPEC-81 AXS-TGTD-002`), and constructs an immutable `TargetSpec`:

| Canonical Triple | Accepted CLI / Manifest Aliases | `Arch` | `Os` | `Env` | `CallConv` | Object / Image Format | Ptr / Endian | Governing Spec / Epic |
|---|---|---|---|---|---|---|---|---|
| `x86_64-windows` | `x86_64-pc-windows-msvc`, `x86_64-windows-msvc` | `X86_64` | `Windows` | `msvc` | `Win64` | `COFF` / `PE32+` (`.exe`, `.dll`, `.lib`) | `64` / Little | `SPEC-04`, `SPEC-26`, `SPEC-43` |
| `aarch64-windows` | `aarch64-pc-windows-msvc`, `arm64-pc-windows-msvc` | `AArch64` | `Windows` | `msvc` | `WinArm64` | `COFF 0xAA64` / `PE32+` | `64` / Little | `SPEC-81`, `SPEC-83`, `E16.12` (`T693`–`T696`) |
| `x86_64-linux` | `x86_64-unknown-linux-gnu`, `x86_64-linux-gnu` | `X86_64` | `Linux` | `gnu` | `SysV64` | `ELF64` (`EM_X86_64`: `ET_REL`, `ET_EXEC`, `ET_DYN`, `.a`) | `64` / Little | `SPEC-80`, `SPEC-82` |
| `x86_64-linux-musl` | `x86_64-unknown-linux-musl` | `X86_64` | `Linux` | `musl` | `SysV64` | `ELF64` (`EM_X86_64`) | `64` / Little | `SPEC-80`, `SPEC-82` |
| `aarch64-linux` | `aarch64-unknown-linux-gnu`, `aarch64-linux-gnu` | `AArch64` | `Linux` | `gnu` | `Aapcs64` | `ELF64` (`EM_AARCH64 = 183`) | `64` / Little | `SPEC-83` |
| `aarch64-linux-musl` | `aarch64-unknown-linux-musl` | `AArch64` | `Linux` | `musl` | `Aapcs64` | `ELF64` (`EM_AARCH64 = 183`) | `64` / Little | `SPEC-83` |
| `riscv64-linux` | `riscv64-unknown-linux-gnu`, `riscv64gc-unknown-linux-gnu` | `RiscV64` | `Linux` | `gnu` | `RiscV` (`LP64D`) | `ELF64` (`EM_RISCV = 243`) | `64` / Little | `SPEC-87` |
| `riscv64-linux-musl` | `riscv64-unknown-linux-musl`, `riscv64gc-unknown-linux-musl` | `RiscV64` | `Linux` | `musl` | `RiscV` (`LP64D`) | `ELF64` (`EM_RISCV = 243`) | `64` / Little | `SPEC-87` |
| `aarch64-macos` | `aarch64-apple-darwin`, `arm64-apple-darwin` | `AArch64` | `Macos` | `darwin` | `Aapcs64Darwin` | `Mach-O 64` (`CPU_TYPE_ARM64`, BSD `.a`) | `64` / Little | `SPEC-84`, `E16.11` (`T689`–`T692`) |
| `x86_64-macos` | `x86_64-apple-darwin` | `X86_64` | `Macos` | `darwin` | `SysV64` | `Mach-O 64` (`CPU_TYPE_X86_64`, BSD `.a`) | `64` / Little | `SPEC-84`, `E16.11` (`T689`–`T692`) |
| `aarch64-android` | `aarch64-linux-android`, `aarch64-linux-android<21..99>` | `AArch64` | `Android` | `bionic` | `Aapcs64` | `ELF64` (`ET_DYN` 16 KiB `PIE` / `.so`) | `64` / Little | `SPEC-85` |
| `wasm32-wasi` | `wasm32` (default `--profile hosted`), `wasm32-wasip1`, `wasm32-unknown-wasi` | `Wasm32` | `Wasi` | `wasi` | `Wasm` | `.wasm` v1 (`linking` v2, GNU `.a`) | `32` / Little | `SPEC-86` |
| `wasm32-freestanding` | `wasm32` (with `--profile freestanding`), `wasm32-unknown-unknown`, `wasm32-none` | `Wasm32` | `None` | `""` | `Wasm` | `.wasm` v1 (`--profile freestanding`) | `32` / Little | `SPEC-52`, `SPEC-86` |
| `<arch>-uefi` | `x86_64-unknown-uefi`, `aarch64-unknown-uefi` | `X86_64` / `AArch64` | `Uefi` | `""` | `Win64` / `Aapcs64` | `PE32+` (`IMAGE_SUBSYSTEM_EFI_APPLICATION`) | `64` / Little | `0097 §38`, `0220 §11`, `SPEC-52` |
| `<arch>-none` | `x86_64-unknown-none`, `aarch64-unknown-none`, `riscv64-unknown-none` | `X86_64` / `AArch64` / `RiscV64` | `None` | `""` | Arch default | `ELF64` / `--format bin` (`freestanding`/`kernel`) | `64` / Little | `0097 §12`, `0220 §12`, `SPEC-52`, `SPEC-55` |

Per `SPEC-81 AXS-TGTD-002` and `SPEC-86 AXS-WASM-001`, bare `wasm32` (`--target wasm32` or `[build] target = "wasm32"`) normalizes to `wasm32-wasi` (`TargetId.Wasm32Wasi`) under the default `--profile hosted` (and `--profile system`) and to `wasm32-freestanding` (`TargetId.Wasm32Freestanding`) when combined with `--profile freestanding` (or `--profile kernel`). Canonical diagnostics, cache paths (`target/<canonical-triple>/<profile>/`), and `.axmi` metadata always record the normalized canonical triple (`x86_64-windows`, `aarch64-linux`, `wasm32-wasi`, `wasm32-freestanding`, …) regardless of which CLI alias was typed (`tasks/0453 §194.3`, `tasks/0587 §3`). [0097 §3; 0220 §5–12, §32; tasks/0453 §194.2–3; tasks/0587 §1–4; SPEC-52; SPEC-80..87; SPEC-81 AXS-TGTD-002; SPEC-86 AXS-WASM-001]

**AXS-XCMP-003 — Strict Three-Domain Separation: `Build` vs `Host` vs `Target` (`tasks/0453 §194.4–6, §194.39`, `tasks/0587 §2, §23`, `ATARGET-02, 21, 45`).** Every compilation session maintains three explicit machine descriptors (`BuildConfiguration { build_spec, host_spec, target_spec }`):
1. **`Build` (`build_spec`):** The physical machine executing `axiomc` (and running the compiler's sandboxed `comptime` interpreter loop).
2. **`Host` (`host_spec`):** The machine where the compiled tool/compiler binary itself is intended to run (equal to `build_spec` for ordinary cross-builds; distinct in Canadian-cross builds of `axiomc` itself).
3. **`Target` (`target_spec`):** The machine or VM for which `axiomc` evaluates `@cfg`, `DataLayout`, `usize`/`isize`, calling conventions, `LIR` lowering, object emission, and linking.
Build-time helper tools, procedural generators, or code-generators compiled during a build (`ArtifactRole.HostTool`) execute in a separate `CompilerDB` target partition parameterized by `build_spec` and **never** share `TargetParameterized` or `TargetSpecific` query results, `.axmi` interfaces, or link inputs with `ArtifactRole.TargetArtifact` (`tasks/0453 §194.39`, `ATARGET-45`). Furthermore, `Target` is strictly orthogonal to `RuntimeProfile` (`hosted`, `freestanding`, `kernel`, `system`; `tasks/0453 §194.6`, `SPEC-52 AXS-FRE-002`). [tasks/0453 §194.4–6, §194.39, ATARGET-21, ATARGET-45; tasks/0587 §2, §23, ATARGET-02; SPEC-52 AXS-FRE-002]

**AXS-XCMP-004 — Frontend Target Isolation, Common `TargetBackend` Contract & Self-Hostable Native Backends (`REQ-TGT-080`..`REQ-TGT-084`, `REQ-TGT-322`..`REQ-TGT-326`).** Axiom enforces five non-negotiable architectural invariants across all targets (`tasks/0518 §151 AMACHINE-91..95`, `tasks/0524 §112–113 ABACKEND-97..100`):
1. **Frontend ISA Isolation (`AMACHINE-91`, `ABACKEND-97`, `REQ-TGT-080`, `REQ-TGT-322`):** Lexing (`SPEC-01`), grammar parsing (`SPEC-02`), Core surface syntax, name resolution, type inference, trait solving, capability/ownership/race verification (`SPEC-10`..`12`, `SPEC-30`), `Drop` elaboration, and `Verified MIR` MUST NOT depend on or expose ISA-specific registers, condition flags, instruction encodings, or object relocation mechanics.
2. **Additive Target Extensibility (`ABACKEND-98`, `REQ-TGT-323`):** Adding a new target to `axiomc` MUST NOT require modifying existing Core syntax or Core semantic rules (`0097 §2`, `AOS-02`).
3. **`Axiom LIR` Semantic Portability Boundary & Common `TargetBackend` Contract (`AMACHINE-92`, `ABACKEND-99..100`, `REQ-TGT-081`, `REQ-TGT-324`..`REQ-TGT-326`):** Frontend stages determine *what* a program means; backends determine *how* that exact meaning executes on hardware or a VM (`tasks/0524 §113`, `REQ-TGT-326`). `Axiom LIR` (`SPEC-81 AXS-TGTD-039..043`) is the sole semantic portability boundary of the native compiler (`REQ-TGT-324`). Every target backend implements one common `TargetBackend` contract (`TargetDesc`, `CallConvDesc`, `IsaTable`, `Legalizer`, `verify_mc`/`verify_wasm`, `Encoder`, `ObjectWriter`, `ImageLinker`; `REQ-TGT-081`) and is **forbidden** from redefining Core overflow, NaN, aliasing, atomic, `Drop`, or panic semantics (`ABACKEND-100`, `REQ-TGT-325`).
4. **Zero Semantic Dependency on LLVM or Bootstrap Backends (`AMACHINE-93..94`, `REQ-TGT-082`..`REQ-TGT-083`):** Language semantics have zero dependency on LLVM IR or C UB (`REQ-TGT-082`; Axiom's `axiom0` stage-0 bootstrap in C11 uses zero LLVM per `SPEC-00` and `SPEC-20`), and the self-hosted `axiomc` compiler replaces bootstrap codegen completely with native Axiom target backends (`REQ-TGT-083`).
5. **Self-Hostable Backend Implementation (`AMACHINE-95`, `REQ-TGT-084`):** Every native Axiom backend (`TargetDesc` tables, pattern ISel, register allocator, machine verifier, encoder, object writer, and linker) is expressible as deterministic, arena-allocated pure Axiom data structures and functions with zero C/C++ backend libraries, enabling `axiomc` to cross-compile itself (`Host != Build`) to every hosted 64-bit target (`x86_64-windows`, `aarch64-windows`, `x86_64-linux`, `aarch64-linux`, `riscv64-linux`, `aarch64-macos`, `x86_64-macos`). [0097 §1–2, §57, AOS-01..02, AOS-35; tasks/0518 §151, AMACHINE-91..95; tasks/0524 §112–113, ABACKEND-97..100; SPEC-20; SPEC-81 AXS-TGTD-001, AXS-TGTD-039..043; REQ-TGT-080..084, REQ-TGT-322..326]

**AXS-XCMP-005 — Three-Tier Multi-Target Query & Cache Partitioning (`tasks/0453 §194.12, §194.30–32`, `tasks/0587 §5–6, §33`, `REQ-TGT-319`).** `CompilerDB` (`SPEC-21`) and `.axiom-cache` (`SPEC-22`) classify every compiler query into one of three target-sensitivity tiers (`ATARGET-05..06, 26..27, 40`, `ABACKEND-94`):
- **Tier A — `TargetIndependent` (keyed only by `SourceFingerprint` / `ManifestFingerprint`; shared 100% across all targets):** source file byte loading, UTF-8 validation & CRLF-to-LF normalization (`SPEC-01`), token lexing, S0/S1 AST construction prior to `@cfg` pruning (`SPEC-02`), `axiom.toml` manifest parsing, and module path discovery.
- **Tier B — `TargetParameterized` (keyed by `(ModuleId, CfgEnvFingerprint, DataLayoutFingerprint, Profile, SafetyProfile, PanicStrategy)`):** `@cfg(...)` AST-to-HIR pruning, import & name resolution, typechecking, trait resolution, `const`/`comptime` evaluation, `@derive` expansion (`SPEC-61`), ownership/capability/concurrency verification, `Verified MIR`, and target-neutral `OptIR` (`SPEC-70`..`SPEC-73`).
- **Tier C — `TargetSpecific` (keyed by full 128-bit `TargetFingerprint` + `OptProfile` + `CodeModel` + `LinkProfile` + `SysrootFingerprint`):** target-costed `OptIR` passes (`SPEC-74` SIMD cost models, target inlining thresholds), `Axiom LIR` ABI lowering, `Legalizer`, instruction selection, register allocation (`SPEC-77`), `verify_mc`/`verify_wasm`, binary encoding, `.obj`/`.o`/`.wasm` + `.axmi` serialization, and final linking (`REQ-TGT-319`). [tasks/0453 §194.12, §194.30–32, ATARGET-26..27, ATARGET-40; tasks/0587 §5–6, §33, ATARGET-05..06; tasks/0524 §112, ABACKEND-94; SPEC-21; SPEC-22 AXS-INC-021; REQ-TGT-319]

**AXS-XCMP-006 — Cross-Target `const` & `comptime` Evaluation Semantics (`0097 §4–6`, `0220 §30, §35`, `tasks/0453 §194.7–9, §194.38`, `tasks/0587 §23–25`, `SPEC-60 AXS-CTM-013`).** When cross-compiling (`build_spec != target_spec`), all `const` initializers, array length expressions `[N]T`, `@at(...)` constant address expressions (`SPEC-55`), and `comptime` functions/blocks (`SPEC-60`) execute inside the compiler's deterministic evaluator on `Build` **strictly under `target_spec`'s `DataLayout` and `TargetDesc`** (`ATARGET-17..18, 22..24, 44`):
1. **Target Layout & Pointer Width:** `size_of<T>()`, `align_of<T>()`, `offset_of<T, F>()` (`SPEC-61`), `usize` / `isize` bit width (`32` bits on `wasm32-*` with `usize.MAX = 0xFFFF_FFFF`; `64` bits on 64-bit targets with `usize.MAX = 0xFFFF_FFFF_FFFF_FFFF`), checked `usize`/`isize` overflow boundaries (`AX_CONST_OVERFLOW`), pointer-to-`usize` widths, `@repr(C)` field padding, and `enum` tag/niche layouts use **`target_spec`** exclusively and **never** inspect `build_spec` host pointer width or alignment (`0097 §4–6`, `AOS-03..04`).
2. **Target Endianness & IEEE-754 Canonicalization:** `to_ne_bytes()` / `from_ne_bytes()` (`SPEC-40`), bitcasts (`SPEC-51`), static data-section byte lowering (`SPEC-60 AXS-CTM-034`), and relocation addends serialize in **`target_spec.endian`**, while `comptime` floating-point operations follow deterministic IEEE-754 round-to-nearest-even and canonicalize quiet `NaN` bit patterns (`0x7FC0_0000` for `f32`, `0x7FF8_0000_0000_0000` for `f64`; `SPEC-41`, `SPEC-60 AXS-CTM-013`).
3. **Zero Host Ambient Leakage:** `comptime` evaluation forbids reading host environment variables (`std.env`), host filesystems (`std.fs`), host wall clocks (`std.time`), host network sockets, or host `extern` FFI (`AX_CTM_CAPABILITY_DENIED` / `AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN`; `0220 §30`, `AOS-37`, `SPEC-53 AXS-SEC-011`, `SPEC-60 AXS-CTM-003`), ensuring host environment state never leaks silently into target binaries. [0097 §4–6, AOS-03..04; 0220 §30, §35, AOS-37; tasks/0453 §194.7–9, §194.38, ATARGET-22..24, ATARGET-44; tasks/0587 §23–25, ATARGET-17..18; SPEC-40; SPEC-41; SPEC-53 AXS-SEC-011; SPEC-60 AXS-CTM-003, AXS-CTM-013, AXS-CTM-034]

**AXS-XCMP-007 — Target-Parameterized Layout Intrinsics & `std.target` Constants (`0220 §35`, `SPEC-02 AXS-GRM-056`).** Layout and target-property introspection intrinsics use canonical generic call syntax `size_of<T>() -> usize` and `align_of<T>() -> usize` (`SPEC-02 AXS-GRM-056`, with `<T>` placed directly after the function identifier — never `::<>` or `.<>`). In addition, `std.target` exposes compile-time `const` target facts derived solely from `target_spec`:
- `POINTER_WIDTH_BITS: u32` (`32` or `64`), `POINTER_SIZE_BYTES: usize` (`4` or `8`);
- `IS_LITTLE_ENDIAN: bool` (`true` on all v1 P16 targets);
- `CACHE_LINE_BYTES: usize` (`128` on `aarch64-macos` Apple Silicon performance cores; `64` on `x86_64`, `aarch64-linux`/`android`/`windows`, `riscv64-linux`, and `wasm32`);
- `MIN_PAGE_SIZE_BYTES: usize` (`16384` on `aarch64-macos` and `aarch64-android`; `65536` on `wasm32`; `4096` on `x86_64-*`, `aarch64-linux`, `aarch64-windows`, and `riscv64-linux`).
All `std.target` constants are pure `comptime`-evaluatable values requiring zero runtime syscalls. [0220 §35; SPEC-02 AXS-GRM-056; SPEC-80..87]

**AXS-XCMP-008 — Cross-Host Byte-for-Byte Reproducibility & Path Normalization (`REQ-TGT-320`, `ABACKEND-95`, `tasks/0453 §194.42`, `tasks/0587 §22`, `ATARGET-16, 47..48`).** Compiling the identical source tree, `axiom.toml`, `--target <triple>`, compiler version, CLI flags, and hermetic sysroot on a `Windows` host, a `Linux` host, and a `macOS` host MUST emit **byte-for-byte identical** `.obj`/`.o`/`.wasm`, `.axmi`, `.lib`/`.a`, and linked `.exe`/`.dll`/`PIE`/`.so`/`MH_EXECUTE`/`.dylib`/`.wasm` binaries (`REQ-TGT-320`):
1. **Newline Normalization:** Source ingestion normalizes `\r\n` to `\n` (`SPEC-01`) so CRLF vs LF git checkouts on Windows vs Unix never alter spans, hashes, string multi-line literals, or embedded metadata.
2. **Forward-Slash Workspace Path Canonicalization:** Every workspace-relative path serialized into `.axmi` interfaces, `.axmeta` containers (`SPEC-24`), archive headers, panic `SourceLocation` tables (`file:line:col`), DWARF v5 / `CodeView` debug sections (with automatic workspace-root prefix remapping or explicit `--remap-path-prefix <from>=<to>`), and linker map outputs uses UTF-8 forward slashes (`/`) regardless of whether the host OS separator is `\` or `/`.
3. **Zero Host Nondeterminism:** Archive member timestamps (`0`), UID/GID (`0`), file permissions (`0644` / `0755`), PE/COFF `TimeDateStamp` (`0` or deterministic BLAKE3 truncation), ELF `NT_GNU_BUILD_ID` (BLAKE3-128), Mach-O `LC_UUID` & SHA-256 `LC_CODE_SIGNATURE` (`SPEC-84 AXS-MACHO-021, AXS-MACHO-025, AXS-MACHO-032`), section ordering, symbol sorting, and parallel `--jobs N` codegen (`SPEC-23`) are 100% deterministic and independent of wall clock, PID, thread scheduling, or ASLR. [0097 §55; tasks/0453 §194.42, ATARGET-47..48; tasks/0524 §112, ABACKEND-95; tasks/0587 §22, ATARGET-16; SPEC-23; SPEC-24; SPEC-84 AXS-MACHO-021, AXS-MACHO-025, AXS-MACHO-032; REQ-TGT-320]

**AXS-XCMP-009 — Multi-Target Artifact Isolation & Target-Mismatch Link Rejection (`REQ-TGT-319`, `SPEC-22`, `SPEC-24`).** Build outputs default to isolated per-target directories `target/<canonical-triple>/<profile>/` so building `--target x86_64-windows`, `--target aarch64-linux`, and `--target wasm32-wasi` sequentially or concurrently in one workspace preserves all warm caches without overwriting or poisoning artifacts (`tasks/0453 §194.30–32`, `tasks/0587 §4, §33`). Every `.axmi`, `.obj`/`.o`/`.wasm`, and `.lib`/`.a` carries/validates target identity (`TargetFingerprint` / machine magic / ABI flags); passing an input artifact compiled for target `T_1` to a compile or link targeting `T_2 != T_1` is rejected deterministically with `AX_LINK_ARTIFACT_TARGET_MISMATCH` (`data.expected_target`, `data.found_target`; `SPEC-24 AXS-ART-022..023`). [tasks/0453 §194.30–32; tasks/0524 §112, ABACKEND-94; tasks/0587 §4, §32–33; SPEC-22 AXS-INC-021; SPEC-24 AXS-ART-022..023; REQ-TGT-319]

**AXS-XCMP-010 — Actionable Unsupported-Target Requirement Diagnostics (`REQ-TGT-321`, `ABACKEND-96`, `tasks/0587 §36`).** When a source program or CLI invocation requests an ABI, linkage artifact kind, hardware feature, atomic width, address-space qualifier, or runtime capability not supported by the active `(TargetSpec, Profile)` pair, `axiomc` emits a structured diagnostic (`AX_TARGET_UNSUPPORTED_OP`, `AX_TARGET_UNKNOWN_FEATURE`, `AX_TARGET_FEATURE_CONFLICT`, `AX_TARGET_FEATURE_MISMATCH`, `AX_TARGET_API_LEVEL_TOO_LOW`, or `AX_DRIVER_PROFILE_FORBIDDEN_CAP`) whose `data.target` field records the canonical target triple and whose message/notes state the exact unsupported target requirement (`REQ-TGT-321`). Backends MUST NEVER silently degrade atomic ordering, silently drop overflow checks, or crash with an ICE on unsupported target features. [tasks/0524 §112, ABACKEND-96; tasks/0587 §36, ATARGET-27; SPEC-81 AXS-TGTD-029..032; REQ-TGT-321]

---

## 2. `@cfg(...)` Conditional Compilation Grammar, Predicate Matrix & Prune-Before-Resolve (`AXS-XCMP-011`..`020`)

**AXS-XCMP-011 — Structured `@cfg(...)` Attribute Only; Zero Textual Preprocessor (`0097 §9–10, AOS-06..07`, `0220 §34`, `SPEC-04 AXS-EXT-091`, `tasks/0587 §9`).** Axiom has no C-style `#ifdef` / `#if` / `#define` textual preprocessor and never performs token-level splicing or unparsed conditional skipping (`0097 §9, AOS-06..07`). Conditional compilation is expressed solely via the structured attribute `@cfg(<CfgPred>)`. Attaching multiple `@cfg` attributes to the same construct (`@cfg(P1)` followed by `@cfg(P2)`) evaluates identically to `@cfg(all(P1, P2))`. [0097 §9–10, AOS-06..07; 0220 §34, AOS-38; tasks/0453 §194.26; tasks/0587 §9, ATARGET-07; SPEC-04 AXS-EXT-091]

**AXS-XCMP-012 — `@cfg(...)` Predicate EBNF Grammar & Boolean Combinators (`SPEC-02 AXS-GRM-024`, `SPEC-04 AXS-EXT-091`, `AXS-XCMP-016`).** In Phase 1 (`AXS-XCMP-017`), `@cfg(...)` is parsed by the S1 recursive attribute grammar (`Attribute` / `AttrArgList` / `AttrArg` in `AXS-XCMP-016`, extending `SPEC-02 AXS-GRM-024`), so nested `IDENT = STR` predicates inside `all(...)`, `any(...)`, and `not(...)` (for example, `@cfg(all(target_os = "linux", target_arch = "x86_64"))` and `@cfg(not(profile = "freestanding"))`) construct nested `AttrArg` nodes directly rather than `CallArgs` expressions and never trigger `AX_PARSE_ASSIGN_IN_EXPR` or `AX_PARSE_UNCLOSED_DELIMITER` (`SPEC-02 AXS-GRM-043`, `AXS-GRM-073`). In Phase 2 (`compiler/hir/cfg`), every `@cfg` `Attribute` node MUST conform to the `CfgAttr` / `CfgPred` schema (containing exactly one top-level `CfgPred`, optional trailing comma allowed):

```ebnf
CfgAttr = "@" , "cfg" , "(" , CfgPred , [ "," ] , ")" ;
CfgPred = "all" , "(" , [ CfgPred , { "," , CfgPred } , [ "," ] ] , ")"
        | "any" , "(" , [ CfgPred , { "," , CfgPred } , [ "," ] ] , ")"
        | "not" , "(" , CfgPred , [ "," ] , ")"
        | IDENT , "=" , STR
        | IDENT ;
```

Boolean combinator evaluation over the active `CfgEnv` is total and side-effect-free:
- `all()` (zero arguments) evaluates to `true`; `all(p_1, ..., p_n)` evaluates to `true` iff every `p_i` evaluates to `true`.
- `any()` (zero arguments) evaluates to `false`; `any(p_1, ..., p_n)` evaluates to `true` iff at least one `p_i` evaluates to `true`.
- `not(p)` evaluates to `!eval(p)`.
Token, delimiter, or expression syntax errors inside `@cfg(...)` (such as an unclosed `(` or missing right-hand operand in `@cfg(target_os = )`) report `AX_PARSE_*` in Phase 1 (`AXS-XCMP-017`), whereas syntactically well-formed S1 `Attribute` trees violating `CfgAttr` / `CfgPred` — `@cfg` without parentheses, `@cfg()` with zero arguments, `@cfg(p_1, p_2)` with multiple comma-separated predicates at top level outside `all(...)`/`any(...)`, `not()` or `not(p_1, p_2)` with arity `!= 1`, unknown combinator names (`@cfg(xor(a, b))`), or non-string right-hand sides such as `@cfg(target_pointer_width = 64)` — report `AX_NAME_INVALID_CFG_PREDICATE` in Phase 2 (`AXS-XCMP-020`). [0220 §34; tasks/0587 §9; SPEC-02 AXS-GRM-024, AXS-GRM-043, AXS-GRM-073; SPEC-04 AXS-EXT-091]

**AXS-XCMP-013 — Canonical Built-In `@cfg` Keys & Closed Value Sets (`SPEC-04 AXS-EXT-091`, `0220 §34`, `tasks/0587 §10–11`).** Every built-in `@cfg` key has a fixed syntactic shape (`key = "value"` or bare `key`), cardinality, and closed value domain:

| `@cfg` Key | Form | Cardinality | Closed Canonical Value Set / Semantics |
|---|---|---|---|
| `target_arch` | `key = "val"` | Single | `"x86_64"`, `"aarch64"`, `"wasm32"`, `"riscv64"` |
| `target_os` | `key = "val"` | Single | `"windows"`, `"linux"`, `"macos"`, `"android"`, `"wasi"`, `"uefi"`, `"ios"`, `"none"` |
| `target_env` | `key = "val"` | Single | `"msvc"`, `"gnu"`, `"musl"`, `"bionic"`, `"darwin"`, `"wasi"`, `""` |
| `target_abi` | `key = "val"` | Single | `"win64"`, `"win_arm64"`, `"sysv64"`, `"aapcs64"`, `"apple_arm64"`, `"wasm"`, `"lp64d"`, `"efiapi"` |
| `target_endian` | `key = "val"` | Single | `"little"`, `"big"` |
| `target_pointer_width` | `key = "val"` | Single | `"32"`, `"64"` |
| `target_vendor` | `key = "val"` | Single | `"pc"`, `"apple"`, `"unknown"` |
| `target_family` | `key = "val"` | Multi-set | `"windows"`, `"unix"`, `"wasm"` (`0`..`N` active simultaneously) |
| `target_feature` | `key = "val"` | Multi-set | Any canonical ISA feature name registered in `SPEC-44` / `SPEC-81`..`87` (`"sse2"`, `"sse4.1"`, `"avx"`, `"avx2"`, `"fma"`, `"neon"`, `"aes"`, `"sha2"`, `"crc"`, `"lse"`, `"simd128"`, `"bulk_memory"`, `"atomics"`, `"m"`, `"a"`, `"f"`, `"d"`, `"c"`, `"v"`, `"zba"`, `"zbb"`, `"zbc"`, `"zbs"`, `"zicond"`, `"zacas"`, …). Evaluates `true` iff active in `target_spec.features`; a valid feature belonging to another registered ISA evaluates cleanly to `false`; an unregistered feature string reports `AX_NAME_INVALID_CFG_PREDICATE` |
| `profile` | `key = "val"` | Single | `"hosted"`, `"freestanding"`, `"kernel"`, `"system"` (`SPEC-52 AXS-FRE-002`) |
| `safety_profile` | `key = "val"` | Single | `"safe"`, `"sandbox"`, `"system"` (`SPEC-53 AXS-SEC-002`) |
| `panic` | `key = "val"` | Single | `"unwind"`, `"abort"` (`SPEC-54 AXS-PAN-001`) |
| `debug_assertions` | Bare `ident` | Flag | `true` in debug builds or `--debug-assertions`; `false` in release builds unless overridden |
| `test` | Bare `ident` | Flag | `true` when compiling under `axiomc test` / `--test`; `false` otherwise |
| `feature` | `key = "val"` | Multi-set | Package feature `<name>` declared in `[features]` of the current package's `axiom.toml`; referencing a `<name>` absent from `[features]` reports `AX_NAME_INVALID_CFG_PREDICATE` |

Using a bare key with `= "val"` (e.g., `@cfg(test = "true")`) or a valued key bare (e.g., `@cfg(target_os)`) reports `AX_NAME_INVALID_CFG_PREDICATE`. [0220 §34; tasks/0587 §10–11; SPEC-04 AXS-EXT-091; SPEC-44; SPEC-52..54; SPEC-81..87]

**AXS-XCMP-014 — Exact `TargetId` to `CfgEnv` Valuation Matrix.** Every canonical target populates `CfgEnv` with the following exact built-in target values:

| Canonical Target | `target_arch` | `target_os` | `target_env` | `target_abi` | `target_vendor` | `target_family` | `target_pointer_width` | `target_endian` |
|---|---|---|---|---|---|---|---|---|
| `x86_64-windows` | `"x86_64"` | `"windows"` | `"msvc"` | `"win64"` | `"pc"` | `{"windows"}` | `"64"` | `"little"` |
| `aarch64-windows` | `"aarch64"` | `"windows"` | `"msvc"` | `"win_arm64"` | `"pc"` | `{"windows"}` | `"64"` | `"little"` |
| `x86_64-linux` | `"x86_64"` | `"linux"` | `"gnu"` | `"sysv64"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `x86_64-linux-musl` | `"x86_64"` | `"linux"` | `"musl"` | `"sysv64"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `aarch64-linux` | `"aarch64"` | `"linux"` | `"gnu"` | `"aapcs64"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `aarch64-linux-musl` | `"aarch64"` | `"linux"` | `"musl"` | `"aapcs64"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `riscv64-linux` | `"riscv64"` | `"linux"` | `"gnu"` | `"lp64d"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `riscv64-linux-musl` | `"riscv64"` | `"linux"` | `"musl"` | `"lp64d"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `aarch64-macos` | `"aarch64"` | `"macos"` | `"darwin"` | `"apple_arm64"` | `"apple"` | `{"unix"}` | `"64"` | `"little"` |
| `x86_64-macos` | `"x86_64"` | `"macos"` | `"darwin"` | `"sysv64"` | `"apple"` | `{"unix"}` | `"64"` | `"little"` |
| `aarch64-android` | `"aarch64"` | `"android"` | `"bionic"` | `"aapcs64"` | `"unknown"` | `{"unix"}` | `"64"` | `"little"` |
| `wasm32-wasi` | `"wasm32"` | `"wasi"` | `"wasi"` | `"wasm"` | `"unknown"` | `{"wasm"}` | `"32"` | `"little"` |
| `wasm32-freestanding` | `"wasm32"` | `"none"` | `""` | `"wasm"` | `"unknown"` | `{"wasm"}` | `"32"` | `"little"` |
| `x86_64-uefi` / `aarch64-uefi` | `"x86_64"` / `"aarch64"` | `"uefi"` | `""` | `"efiapi"` / `"aapcs64"` | `"unknown"` | `{}` | `"64"` | `"little"` |
| `<arch>-none` | `<arch>` | `"none"` | `""` | Arch default | `"unknown"` | `{}` | `"64"` | `"little"` |

[0097 §3, §33–38; 0220 §5–12, §32–34; tasks/0453 §194.2–3, §194.36; tasks/0587 §1–4, §11; SPEC-80..87]

**AXS-XCMP-015 — Strict Namespace Separation & Checked Custom `--cfg` Flags (`tasks/0587 §10`, `ATARGET-09`).** Target properties (`target_*`), CPU features (`target_feature = "..."`), runtime/safety/panic profiles, and package features (`feature = "..."`) occupy **strictly separate namespaces**:
1. Shorthand bare OS/arch identifiers such as `@cfg(windows)`, `@cfg(linux)`, `@cfg(unix)`, or `@cfg(x86_64)` are **invalid** in Axiom and report `AX_NAME_INVALID_CFG_PREDICATE` with a machine-applicable fix-it (`@cfg(target_os = "windows")`, `@cfg(target_family = "unix")`, `@cfg(target_arch = "x86_64")`).
2. User-defined `--cfg <key>` or `--cfg <key>="<val>"` flags are accepted in `@cfg(...)` **only** when `<key>` and its permitted value set are explicitly declared in `axiom.toml` `[build.cfg]` (or `--check-cfg`), guaranteeing that every misspelled key or value (e.g. `@cfg(target_os = "win32")`, `@cfg(target_os = "osx")`, `@cfg(target_arch = "amd64")`, `@cfg(target_arch = "arm64")`) is caught at compile time with `AX_NAME_INVALID_CFG_PREDICATE`. [tasks/0587 §10, ATARGET-09]

**AXS-XCMP-016 — Valid `@cfg(...)` Placement Sites & S1 Attribute Grammar Extensions (`SPEC-02 AXS-GRM-024`, `tasks/0453 §194.26–27`, `tasks/0587 §9`).** In self-hosted `axiomc` (extending `SPEC-02` S0 attributes and item/member/field/variant placement per `SPEC-02 AXS-GRM-024` and `SPEC-02 §12`), the S1 grammar extends both nested attribute argument lists and attribute placement sites:

```ebnf
Attribute   = "@" , IDENT , [ AttrArgList ] ;
AttrArgList = "(" , [ AttrArg , { "," , AttrArg } , [ "," ] ] , ")" ;
AttrArg     = IDENT , "=" , Expr
            | IDENT , AttrArgList
            | Expr ;
UseDecl     = { Attribute } , [ Visibility ] , "use" , UseTree ;
FieldInit   = { Attribute } , IDENT , [ ":" , Expr ] ;
MatchArm    = { Attribute } , Pattern , [ "if" , Expr ] , "=>" , Expr ;
Stmt        = { Attribute } , ( LetStmt | AssignStmt | ExprStmt ) , Term | ";" ;
```

**S1 Nested Attribute-Argument Disambiguation (`SPEC-02 AXS-GRM-024, AXS-GRM-037, AXS-GRM-043, AXS-GRM-073`):**
1. The opening `(` of an outer or nested `AttrArgList` MUST NOT have `NL_BEFORE` (`SPEC-02 AXS-GRM-024`); inside `( ... )`, line breaks are ignored (`mode_on = false`).
2. When an `AttrArg` begins with `IDENT` followed immediately (without `NL_BEFORE`) by `(`, the S1 parser tentatively parses `IDENT , AttrArgList` and commits iff the matching `)` is immediately followed by `,` or the enclosing `)`. This permits arbitrary nesting of `IDENT = Expr` and nested combinators inside `@cfg(all(target_os = "linux", target_arch = "x86_64"))` and `@cfg(not(profile = "freestanding"))` without invoking `CallArgs` (`SPEC-02 AXS-GRM-043`, `AXS-GRM-073`), while lowering expression-only `IDENT ( ... )` forms (such as `@at(image_self())`) identically to call `Expr` nodes; if an infix, postfix, or `as` continuation token follows `)` (such as `+` in `@at(image("game.exe") + 0x1A_2B30)`, `SPEC-02 AXS-GRM-037`), the parser backtracks without diagnostics and parses the `AttrArg` via `Expr`.

Combined with `SPEC-02 AXS-GRM-020..036`, the complete closed set of legal `@cfg(...)` targets is:
1. Top-level module items (`fn`, `struct`, `enum`, `trait`, `impl`, `type`, `const`, `static`, `extern "<abi>" { ... }`);
2. `use` and `pub use` declarations (`UseDecl`);
3. Members inside `impl`, `trait`, and `extern` blocks (`ImplMember`, `TraitMember`, `ExternMember`);
4. Named and tuple `struct` declaration fields (`Field`, `TupleField`) and `StructLit` field initializers (`FieldInit`);
5. `enum` declaration variants (`Variant`);
6. `match` expression arms (`MatchArm`);
7. Block statements (`LetStmt`, `AssignStmt`, `ExprStmt`) and block tail expressions.
`@cfg(...)` MUST NOT be placed on a `module a.b.c` file header (`SPEC-02 AXS-GRM-021`: `ModuleDecl` takes no attributes; platform-specific modules gate their items/`pub use` exports instead), on function parameters, or on generic type parameters. [SPEC-02 AXS-GRM-021..037, AXS-GRM-043, AXS-GRM-073, §12; tasks/0453 §194.26–27; tasks/0587 §9]

**AXS-XCMP-017 — Three-Stage Parse-All, Validate-All, Prune-Before-Resolve Semantics (`0097 §9–10`, `tasks/0587 §9`, `ATARGET-07..08`).** `compiler/hir/cfg` executes `@cfg(...)` processing in three strict sequential phases:
1. **Phase 1 — Full Lexical & Syntactic Parse (`TargetIndependent`):** Every source file in the compilation graph is lexed and parsed in full under the S1 grammar (including the recursive `Attribute` / `AttrArgList` / `AttrArg` rules of `AXS-XCMP-016` so nested `key = "val"` predicates inside `@cfg(all(...))`, `@cfg(any(...))`, and `@cfg(not(...))` parse without syntax errors), **including all inactive `@cfg(...)` branches**. Any lexical or grammar error (`AX_LEX_*`, `AX_PARSE_*`, such as `var x = 1`, `&x`, unclosed delimiters, or invalid tokens) inside an inactive `@cfg` construct is diagnosed regardless of the active target (`0097 §10`, `tasks/0587 §9`).
2. **Phase 2 — Total `@cfg` Predicate Validation (Active and Inactive Subtrees):** Before pruning, `compiler/hir/cfg` validates **every** `@cfg(...)` attribute in the AST — including nested `@cfg` attributes inside an outer `@cfg` branch that evaluates to `false` — against `AXS-XCMP-012`..`015`, emitting `AX_NAME_INVALID_CFG_PREDICATE` on any malformed predicate or unknown key/value.
3. **Phase 3 — Deterministic AST-to-HIR Pruning Prior to Name Resolution:** Every AST node whose effective `@cfg` predicate evaluates to `false` is removed completely during AST-to-HIR lowering **before** symbol-table insertion, `use` import resolution, type inference, trait coherence, layout computation, pattern exhaustiveness, or MIR construction:
   - Mutually exclusive `@cfg`-gated items defining the same identifier (e.g., `@cfg(target_os = "windows") fn page_len() -> usize` and `@cfg(target_os = "linux") fn page_len() -> usize`) produce **one** surviving HIR item with zero `AX_NAME_DUPLICATE` error; if two overlapping `@cfg` predicates both evaluate to `true` on the active target, `AX_NAME_DUPLICATE` fires on the surviving definitions.
   - Pruned `use` imports are never resolved, allowing `@cfg(target_os = "linux") use std.os.linux.Epoll` to coexist cleanly with `@cfg(target_os = "windows") use std.os.windows.OwnedHandle` in the same file.
   - Struct memory layout, `StructLit` missing-field checks, `enum` tag sizing, and `match` exhaustiveness / unreachable-arm checks (`AX_PAT_NONEXHAUSTIVE`, `AX_PAT_UNREACHABLE`) operate strictly on the surviving post-prune fields, variants, and arms. [0097 §9–10, AOS-06..07; 0220 §34; tasks/0453 §194.26–27; tasks/0587 §9, ATARGET-07..08]

**AXS-XCMP-018 — Structural `@cfg(...)` Pruning vs Value-Level `if comptime` (`SPEC-60 AXS-CTM-021`, `tasks/0587 §9, §25`).** `std.target.cfg` / `if comptime` (`SPEC-60 AXS-CTM-021`) evaluates boolean target constants *after* name resolution and typechecking, requiring both the `then` and `else` branches to reference in-scope names and well-typed expressions on every target. Conversely, `@cfg(...)` prunes *before* name resolution (`AXS-XCMP-017`) and MUST be used whenever target-conditional code imports target-gated `std.os.*` modules, declares `extern` OS symbols, or accesses `@cfg`-gated struct fields or enum variants (`0097 §10`, `tasks/0453 §194.26–27`). [0097 §10; tasks/0453 §194.26–27; tasks/0587 §9, §25; SPEC-60 AXS-CTM-021]

**AXS-XCMP-019 — Portable Public Signature Stability & `.axmi` Interface Recording (`0097 §10–11, AOS-08`, `SPEC-24`).** Portable Level-1 `std` modules (`AXS-PLAT-001`, `AXS-PLAT-007`..`012`) MUST NOT alter public item names, public struct fields, public enum variants, or public function signatures across hosted targets via `@cfg`; `@cfg` inside Level-1 `std` modules is restricted to private implementation bodies and internal `std.sys.*` routing (`0097 §11`, `AOS-08`). Emitted `.axmi` module interfaces (`SPEC-24`) serialize the post-prune target-resolved public HIR surface alongside `(TargetFingerprint, CfgEnvFingerprint)`. [0097 §10–11, AOS-08; 0220 §1, §34; tasks/0453 §194.27; tasks/0587 §32; SPEC-24 AXS-ART-010..013]

**AXS-XCMP-020 — `AX_NAME_INVALID_CFG_PREDICATE` Diagnostic Specification.** `AX_NAME_INVALID_CFG_PREDICATE` (severity `error`, area `NAME`) highlights the exact offending identifier, literal, or argument list inside `@cfg(...)` and populates `data`:
- `data.key`: offending predicate key string (or `""` when structural/arity error);
- `data.value`: offending string value when `key = "val"` fails closed-set validation;
- Common machine-applicable fix-its: bare `windows`/`linux`/`macos`/`android`/`wasi` -> `target_os = "<os>"`; bare `unix` -> `target_family = "unix"`; bare `x86_64`/`aarch64`/`wasm32`/`riscv64` -> `target_arch = "<arch>"`; `"win32"` -> `"windows"`; `"osx"`/`"darwin"` (under `target_os`) -> `"macos"`; `"amd64"` -> `"x86_64"`; `"arm64"` -> `"aarch64"`. [tasks/0587 §10, §36; spec/diagnostics.md §3, §11]

---

## 3. Hermetic Cross-Linking, `--sysroot` / `--target-sdk` & Built-In OS Import Stubs (`AXS-XCMP-021`..`028`)

**AXS-XCMP-021 — Hermetic Cross-Linker & Zero Host-Filesystem Contamination (`REQ-TOOL-001`, `tasks/0453 §194.20–23, §194.41`, `tasks/0587 §13–15, §22`).** Whenever `target_spec != build_spec` — and unconditionally under `--hermetic` even when `target_spec == build_spec` — `axiomc`'s native linkers (`compiler/link/*`) **MUST NEVER** search, read, or fall back to ambient host OS directories (`/lib`, `/lib64`, `/usr/lib`, `/usr/local/lib`, `/Library/Developer/CommandLineTools/SDKs`, `/Applications/Xcode.app/...`, `C:\Windows\System32`, MSVC `VC\Tools\MSVC`, Windows Kits registry entries) or host linker environment variables (`LIBRARY_PATH`, `LD_LIBRARY_PATH`, `DYLD_LIBRARY_PATH`, `LIB`) (`ATARGET-11, 29..32, 46`). Cross-compilation succeeds out-of-the-box on an offline machine with zero target OS SDK installed for all pure-Axiom and `std`-using programs (`REQ-TOOL-001`). [0097 §27, §54; tasks/0453 §194.20–23, §194.41, ATARGET-29..32, ATARGET-46; tasks/0587 §13–15, §22, ATARGET-11; REQ-TOOL-001]

**AXS-XCMP-022 — Deterministic `--sysroot`, `--target-sdk` & `-L` Resolution Order (`tasks/0453 §194.20–21`, `tasks/0587 §14`).** `compiler/link/sysroot` resolves `@link("<name>")` and `-l<name>` libraries for `target_spec` in one fixed, deterministic six-step order:
1. Explicit CLI `-L <dir>` search paths in exact left-to-right CLI order;
2. Target-scoped manifest directories `[target.<canonical-triple>] lib_dirs = [...]` in `axiom.toml` (resolved relative to the workspace root);
3. Explicit `--target-sdk <dir>` (`<dir>/lib/<canonical-triple>/`, then `<dir>/lib/`);
4. Explicit `--sysroot <dir>` (`<dir>/usr/lib/<multiarch>/`, `<dir>/usr/lib/`, `<dir>/lib/` for ELF/Mach-O; `<dir>/lib/<arch>/` for Windows COFF; `<dir>/lib/wasm32-wasi/` for WASI);
5. Bundled Axiom target library directory `<axiom-root>/lib/axiom/targets/<canonical-triple>/`;
6. **Built-in hermetic Axiom OS import stub catalog** (`compiler/link/sysroot`, `AXS-XCMP-023`..`026`).
If `--sysroot <dir>` or `--target-sdk <dir>` is explicitly supplied on the CLI and `<dir>` does not exist or cannot be read as a directory, `axiomc` aborts immediately with `AX_DRIVER_SYSROOT_NOT_FOUND` (exit code `2`) without probing fallback paths. If an explicit external C library (e.g., `-lz`, `-lsqlite3`) is absent from steps `1`–`6`, `axiomc` emits `AX_LINK_LIBRARY_NOT_FOUND` (`data.library`; `spec/diagnostics.md` §11). [tasks/0453 §194.20–21, ATARGET-30; tasks/0587 §14, ATARGET-11; SPEC-26 AXS-WLIB-003; SPEC-82 AXS-ELFD-031; SPEC-84 AXS-MACHO-028]

**AXS-XCMP-023 — Built-In Windows (`x86_64` & `aarch64`) PE/COFF System DLL Import Stubs (`SPEC-26`, `E16.12`).** `compiler/link/sysroot` embeds pure-Axiom short-import descriptor tables (`IMAGE_IMPORT_DESCRIPTOR`, ILT/IAT thunks, `__imp_<symbol>` slots; `SPEC-26 AXS-WLIB-030..031`) for both `IMAGE_FILE_MACHINE_AMD64` (`0x8664`) and `IMAGE_FILE_MACHINE_ARM64` (`0xAA64`) covering the documented Win32 baseline DLLs: `kernel32.dll`, `ntdll.dll` (documented Rtl unwind/heap helpers), `ws2_32.dll`, `bcrypt.dll` (`BCryptGenRandom`), `advapi32.dll`, `userenv.dll`, and `api-ms-win-core-synch-l1-2-0.dll` (`WaitOnAddress`, `WakeByAddressSingle`, `WakeByAddressAll`). Cross-linking `--target x86_64-windows` or `--target aarch64-windows` from Linux or macOS requires **zero** Microsoft Windows SDK `.lib` files. [0097 §27, §53–54; 0220 §6; tasks/0587 §15; SPEC-26 AXS-WLIB-030..031; REQ-TOOL-001]

**AXS-XCMP-024 — Built-In Linux (`x86_64`, `aarch64`, `riscv64`) Static Syscall Default & ELF64 Dynamic Stubs (`SPEC-80`, `SPEC-82`, `SPEC-83`, `SPEC-87`).**
1. **Default Pure-Axiom Static Mode:** Hosted `x86_64-linux`, `aarch64-linux`, and `riscv64-linux` executables link `_start` and `std.sys.{linux,linux_aarch64,linux_riscv64}` directly over stable Linux kernel syscalls (`syscall`, `svc #0`, `ecall`) with **zero** `libc`, **zero** `PT_INTERP`, and **zero** `DT_NEEDED` entries (`0220 §2–3, §5`, `AOS-21`).
2. **Dynamic `PIE` / `.so` / `libc`-Interop Mode:** When `--kind dll`, `--link-mode dynamic`, `std.sys.linux_dl` (`dlopen`), or `@link("c" | "m" | "dl" | "pthread")` is requested (`SPEC-82`), `compiler/link/sysroot` synthesizes `DT_NEEDED` + `.gnu.version_r` dynamic symbol imports from built-in arch-keyed stub descriptors (`libc.so.6`, `libm.so.6`, `libdl.so.2`, `libpthread.so.0` with `GLIBC_2.2.5` baseline on `x86_64`, `GLIBC_2.17` on `aarch64`, `GLIBC_2.27`/`GLIBC_2.34` on `riscv64`; or unversioned `libc.so` under `target_env = "musl"`) and emits the canonical `PT_INTERP` (`/lib64/ld-linux-x86-64.so.2`, `/lib/ld-linux-aarch64.so.1`, `/lib/ld-linux-riscv64-lp64d.so.1`, or `/lib/ld-musl-<arch>.so.1`), while also consuming external `.so` and GNU `GROUP`/`INPUT` linker scripts when `--sysroot` is supplied (`SPEC-82 AXS-ELFD-031`). [0220 §2–5, AOS-21; tasks/0587 §15, ATARGET-12; SPEC-80; SPEC-82 AXS-ELFD-031, AXS-ELFD-036..043; SPEC-83; SPEC-87]

**AXS-XCMP-025 — Built-In macOS (`aarch64` & `x86_64`) Mach-O `libSystem.B.dylib` & `.tbd` Stubs (`SPEC-84`, `E16.11`).** Because XNU kernel syscall numbers are unsupported by Apple (`0220 §4, §7`, `SPEC-84 AXS-MACHO-027`), `compiler/link/sysroot` embeds a hermetic export catalog for `/usr/lib/libSystem.B.dylib` (`LC_LOAD_DYLIB`, `compatibility_version = 1.0.0`, deterministic normalized current version) covering all Darwin POSIX, `kqueue`/`kevent64`, `mach_continuous_time`/`clock_gettime_nsec_np`, `_NSGetExecutablePath`, `dlopen`/`dlsym`/`dlclose`, `pthread_*`, and `__ulock_*` symbols used by `std.sys.macos` across `CPU_TYPE_ARM64` and `CPU_TYPE_X86_64`, plus a built-in `.tbd` v3/v4 text-stub reader for optional `--target-sdk <MacOSX.sdk>` framework linking (`SPEC-84 AXS-MACHO-028`) and built-in SHA-256 ad-hoc `LC_CODE_SIGNATURE` signing (`SPEC-84 AXS-MACHO-025`). [0220 §4, §7; SPEC-84 AXS-MACHO-025, AXS-MACHO-027..030; REQ-TOOL-001]

**AXS-XCMP-026 — Built-In Android (`aarch64-android`) Bionic Stubs & WASI (`wasm32-wasi`) Import Catalog (`SPEC-85`, `SPEC-86`).**
1. **Android (`aarch64-android`):** `compiler/link/sysroot` embeds the NDK-free API-level-gated Bionic symbol catalog (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`, `PT_INTERP = "/system/bin/linker64\0"`), enforcing `target.api_level` symbol availability (`AX_TARGET_API_LEVEL_TOO_LOW`) and rejecting private non-NDK system libraries (`AX_LINK_ANDROID_PRIVATE_LIB`; `SPEC-85 AXS-ANDR-012..014`).
2. **WASI (`wasm32-wasi`):** `compiler/link/sysroot` embeds the exact `wasi_snapshot_preview1` `(module, name) -> FuncType` import table (`args_*`, `environ_*`, `clock_time_get`, `fd_*`, `path_*`, `poll_oneoff`, `proc_exit`, `random_get`, `sched_yield`; `SPEC-86 AXS-WASM-029`), emitting only referenced imports into the linked `.wasm` Import section (`id = 2`). [0220 §9–10; SPEC-85 AXS-ANDR-012..014; SPEC-86 AXS-WASM-028..029; REQ-TOOL-001]

**AXS-XCMP-027 — `SysrootFingerprint` Cache Invalidation (`tasks/0453 §194.41`, `tasks/0587 §14, §22`).** `compiler/link/sysroot` computes a 128-bit BLAKE3 `SysrootFingerprint` from the built-in stub catalog schema/content digest plus the sorted `(normalized_forward_slash_relpath, blake3_128)` pairs of every external `.lib`/`.a`/`.so`/`.dylib`/`.tbd`/`.obj`/`.o` resolved under `-L`, `--target-sdk`, or `--sysroot`. Mixing `SysrootFingerprint` into Tier-C link cache keys (`AXS-XCMP-005`) guarantees immediate deterministic rebuilds whenever an external SDK or library file changes (`ATARGET-11, 46`). [tasks/0453 §194.41, ATARGET-46; tasks/0587 §14, §22, ATARGET-11; SPEC-22 AXS-INC-021]

**AXS-XCMP-028 — Freestanding & Kernel Zero-OS Link Invariant (`0097 §12–17`, `0220 §11–13`, `SPEC-52 AXS-FRE-002..003`).** Under `--profile freestanding` or `--profile kernel` (`wasm32-freestanding`, `<arch>-uefi`, `<arch>-none`, or any target compiled with `--profile freestanding`), `compiler/link/sysroot` injects **zero** hosted `_start` / CRT shim, **zero** OS import stubs (`kernel32.dll`, `libc`, `libSystem.B.dylib`, Bionic, `wasi_snapshot_preview1`), and **zero** hidden global constructors (`0097 §15, AOS-12..14`), linking solely `@entry` user/firmware/kernel code and freestanding `std.core` (`SPEC-52 AXS-FRE-010`). [0097 §12–17, AOS-09..14; 0220 §11–13, AOS-23; tasks/0587 §16–20; SPEC-52 AXS-FRE-002..003, AXS-FRE-010]

---

## 4. Three-Level OS & Platform Architecture & Dependency DAG (`AXS-PLAT-001`..`006`)

**AXS-PLAT-001 — Three-Level OS Access Model (`0097 §1, §7–8, §11`, `0220 §1, §37–39`, `tasks/0336 §75–76`, `AOS-01..05, 08, 20, 40`).** Axiom partitions all operating-system and platform interaction into three strictly separated levels:
- **Level 1 — Portable Standard Library (`std.io`, `std.fs`, `std.path`, `std.env`, `std.process`, `std.time`, `std.thread`, `std.sync`, `std.net`):** Target-independent, capability-safe (`view<T>`, `mut_view<T>`) APIs with identical public names, types, UTF-8 string contracts, deterministic `Drop`, and structured `Result<T, E>` errors across every hosted target. Level-1 public signatures **never** expose raw OS descriptors (`HANDLE`, `SOCKET`, `c_int` fd, `mach_port_t`), bare integer `errno`/`GetLastError` return conventions, or `@cfg`-conditional public fields/methods (`AOS-05, 08, 20`).
- **Level 2 — `@cfg`-Gated OS Extension Layer (`std.os.windows`, `std.os.linux`, `std.os.macos`, `std.os.android`, `std.os.wasi`, `std.os.unix`, `std.os.error`):** Explicit opt-in platform-specific modules gated by `@cfg(...)` (`AXS-PLAT-013`..`019`), exposing strongly typed opaque handles (`OwnedHandle`/`BorrowedHandle`, `OwnedFd`/`BorrowedFd`, `OwnedWasiFd`), safe/unsafe handle conversion traits (`AsRaw*`, `IntoRaw*`, `unsafe FromRaw*`), native event-notification descriptors (`IocpHandle`, `Epoll`, `Kqueue`, `EventFd`), Mach ports/timebase, Android `logcat` priorities, and WASI preopened directory capabilities (`0220 §1`, `tasks/0336 §75–76`).
- **Level 3 — Internal Raw OS ABI & Host Provider Layer (`std.sys.*` + `std.core.host`):** Package-internal (`pub(package)`) raw kernel syscalls (`syscall`, `svc #0`, `ecall`), Win32/WinSock2/BCrypt `extern "system"` imports, Darwin `libSystem.B.dylib` imports, Android Bionic imports, and WASI `wasi_snapshot_preview1` imports implementing `std/core/host.ax` (`SPEC-04 AXS-EXT-110`). User packages MUST NOT import private `std.sys.*` internals directly (`SPEC-02 AXS-GRM-023`); low-level OS extensions enter user code exclusively through Level 2 (`std.os.*`) or user-declared `unsafe extern` blocks. [0097 §1, §7–8, §11, AOS-01..05, AOS-08; 0220 §1, §37–39, AOS-20, AOS-40; tasks/0336 §75–76, AFFI2-91..93; SPEC-04 AXS-EXT-110]

**AXS-PLAT-002 — Strict Acyclic Platform Dependency Graph (`0097 §51`, `0220 §38`, `SPEC-52`).** Standard-library and platform packages obey a strict one-way DAG with zero cycles:
1. `std.core` (`Option`, `Result`, `Str`, slice views, `Drop`, `Copy`, `Send`, `Share`, layout intrinsics, and `std.core.host` intrinsic declarations): zero OS dependency; available in all profiles (`hosted`, `freestanding`, `kernel`, `system`).
2. `std.alloc` (`Box`, `Vec`, `String`, `HashMap`): depends only on `std.core` + `heap_alloc`/`heap_realloc`/`heap_free` (or `@global_allocator` in `freestanding`/`kernel`; `SPEC-52 AXS-FRE-012`).
3. `std.sys.{windows,linux,linux_dl,linux_aarch64,linux_riscv64,macos,android,wasi}` (Level 3): depends only on `std.core`; never imports Level 1 (`std.io`, `std.fs`, …) or Level 2 (`std.os.*`).
4. `std.{io,fs,path,env,process,time,thread,sync,net}` (Level 1): depends on `std.core`, `std.alloc`, `std.os.error`, and `std.core.host` (statically routed to Level 3 per `AXS-PLAT-020`); never exposes Level-2 types in public signatures.
5. `std.os.{windows,linux,macos,android,wasi,unix}` (Level 2): depends on `std.core`, `std.alloc`, Level 3 (`std.sys.*`), and Level 1 (`std.fs.File`, `std.net.*`, `std.process.Child`) to implement explicit raw-handle bridge traits (`AsRawHandle` / `AsRawFd` / `AsWasiFd`).
Under `--profile freestanding` or `--profile kernel`, importing any hosted Level-1 OS module or Level-2 `std.os.*` module is rejected at compile time with `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT` (`SPEC-52 AXS-FRE-003`). [0097 §51; 0220 §37–38; SPEC-52 AXS-FRE-002..003, AXS-FRE-012]

**AXS-PLAT-003 — `libc` Non-Requirement & Canonical OS ABI Strategy Per Target (`0097 §7–8`, `0220 §2–10, AOS-21..22`, `tasks/0336 §17–24`).** Axiom is not built on top of a mandatory C standard library (`0220 §2`, `AOS-21`). Each hosted target uses its documented stable OS ABI boundary:
- **Windows (`x86_64-windows`, `aarch64-windows`):** Documented Win32 Unicode `*W`, WinSock2, BCrypt, and Synchronization DLLs (`kernel32.dll`, `ws2_32.dll`, `bcrypt.dll`, `api-ms-win-core-synch-l1-2-0.dll`, `ntdll.dll` documented Rtl unwind/heap helpers); **never** unstable raw NT syscall numbers (`0220 §6`, `tasks/0336 §17`) and **never** `msvcrt.dll` / `ucrtbase.dll` (`SPEC-52`).
- **Linux (`x86_64-linux`, `aarch64-linux`, `riscv64-linux`):** Direct stable Linux kernel syscalls (`syscall`, `svc #0`, `ecall`) by default with zero `libc` (`SPEC-80`, `SPEC-83`, `SPEC-87`); optional `libc.so.6` / `musl` coexistence and `std.sys.linux_dl` (`dlopen`) when dynamically linking C libraries (`0220 §2–5`, `SPEC-82`).
- **macOS (`aarch64-macos`, `x86_64-macos`):** Stable `/usr/lib/libSystem.B.dylib` ABI; **never** direct XNU `svc #0x80` / `syscall` numbers (`0220 §4, §7`, `SPEC-84 AXS-MACHO-027`).
- **Android (`aarch64-android`):** Official Bionic NDK public symbol ABI (`libc.so`, `libm.so`, `libdl.so`, `liblog.so`) plus Bionic-sanctioned `futex`/`epoll` syscalls; **never** private vendor `/system/lib64` libraries (`0220 §9`, `SPEC-85 AXS-ANDR-013..014, AXS-ANDR-016`).
- **WASI (`wasm32-wasi`):** Capability-scoped `wasi_snapshot_preview1` imports (`0220 §10`, `SPEC-86 AXS-WASM-029`). [0097 §7–8; 0220 §2–10, AOS-21..22; tasks/0336 §17–24, AFFI2-58..68; SPEC-80..87]

**AXS-PLAT-004 — Opaque OS Handle Typing, Ownership & Non-Pointer Provenance (`0097 §22–24, AOS-15..16`, `0220 §20–21, AOS-24..26, 39`, `tasks/0336 §15–16, AFFI2-69..71`).** An OS resource identifier (`HANDLE`, `SOCKET`, Unix `fd: i32`, `mach_port_t`, `WasiFd`) is an **opaque kernel capability token**, not a memory pointer (`AOS-25, 39`):
1. OS handles **never** coerce to `*const T`, `*mut T`, `view<T>`, or `mut_view<T>`, and arithmetic or dereference on an OS handle is rejected by the typechecker (`AX_TYPE_OPERATOR` / `AX_SEC_CAPABILITY_FORGERY`, `SPEC-53 AXS-SEC-004`).
2. Owned handle wrappers (`File`, `TcpListener`, `TcpStream`, `UdpSocket`, `Child`, `DynLib`, `OwnedHandle`, `OwnedSocket`, `OwnedFd`, `MachPort`, `OwnedWasiFd`) are `!Copy` types with deterministic single-owner `Drop` (`AOS-15..16, 24`).
3. Borrowed handle views (`BorrowedHandle`, `BorrowedSocket`, `BorrowedFd`, `BorrowedWasiFd`) carry capability region tracking (`SPEC-11`, `AX_CAP_OUTLIVES_OWNER`), cannot outlive their owning handle, and never close the underlying kernel object (`tasks/0336 §16, AFFI2-70`).
4. Sentinel disambiguation: Windows `INVALID_HANDLE_VALUE` (`~0usize`) vs `NULL` (`0usize`) (`0220 §6`) and Unix/WASI negative fds (`< 0`) are checked at the Level-3 boundary before constructing `OwnedHandle` / `OwnedFd` / `OwnedWasiFd`. [0097 §22–24, AOS-15..16; 0220 §6, §20–21, AOS-24..26, AOS-39; tasks/0336 §15–16, AFFI2-69..71; SPEC-10..12; SPEC-53 AXS-SEC-004]

**AXS-PLAT-005 — Dual Resource Cleanup Contract: Infallible `Drop` vs Explicit Fallible `close()` (`0097 §24`, `0220 §21, AOS-27`).** Every owned OS I/O resource in Level 1 and Level 2 provides two complementary reclamation paths:
1. **Automatic `impl Drop`:** Invoked deterministically at scope exit or during unwinding (`SPEC-12`, `SPEC-54`); releases the underlying kernel handle, discards any OS close error, and **never** panics (`AOS-27`). On POSIX/Linux/macOS/Android, `close(fd)` inside Level 3 MUST NOT retry on `EINTR` because the kernel already deallocates `fd` from the process descriptor table before delivering `EINTR`, and retrying would race to close a newly allocated descriptor on another thread (`0220 §5, §26`).
2. **Explicit `pub fn close(mut self: Self) -> Result<(), E>`:** Consumes `self` by value, flushes any buffered user-space state, executes the underlying OS close once, replaces `self`'s internal raw token with the inert closed sentinel so `Drop` is a no-op, and surfaces writeback/close errors (`ENOSPC`, `EIO`, …) in `Result.Err` (`0097 §24`, `0220 §21`, `AOS-27`). [0097 §24; 0220 §5, §21, §26, AOS-27; SPEC-12; SPEC-54]

**AXS-PLAT-006 — Structured `OsError` & Immediate Thread-Local Error Capture (`0097 §25, AOS-17..18`, `0220 §19`, `tasks/0336 §51–52, AFFI2-75`).** `std.os.error` defines the canonical OS error representation shared across Level 1 and Level 2:
- `pub enum ErrorKind`: `NotFound`, `PermissionDenied`, `AlreadyExists`, `WouldBlock`, `InvalidInput`, `InvalidData`, `TimedOut`, `Interrupted`, `UnexpectedEof`, `BrokenPipe`, `ConnectionRefused`, `ConnectionReset`, `ConnectionAborted`, `NotConnected`, `AddrInUse`, `AddrNotAvailable`, `DirectoryNotEmpty`, `IsADirectory`, `NotADirectory`, `OutOfMemory`, `Unsupported`, `Other`.
- `pub struct OsError { pub kind: ErrorKind, pub raw_code: i32 }`: pairs the portable `ErrorKind` classification with the exact lossless platform error code (`GetLastError()` / `WSAGetLastError()` on Windows; positive `errno` from negated `-errno` kernel return or `*__error()` / `*__errno()` on Linux/macOS/Android; positive `__wasi_errno_t` on WASI) (`0097 §25, AOS-17..18`).
Level-3 FFI wrappers (`std.sys.windows`, `std.sys.macos`, `std.sys.android`, `std.sys.linux_dl`) MUST read thread-local `GetLastError()` / `WSAGetLastError()` / `errno` **immediately** after the failing foreign call before any heap allocation, `Drop` cleanup, or formatting call can clobber thread-local OS state (`tasks/0336 §52, AFFI2-75`). [0097 §25, AOS-17..18; 0220 §19; tasks/0336 §51–52, AFFI2-75]

---

## 5. Level 1 — Portable Standard Library OS Contracts (`AXS-PLAT-007`..`012`)

**AXS-PLAT-007 — UTF-8 Public Boundary & Internal Windows UTF-16LE Transcoding (`0220 §6, §19, §30–31`).** All Level-1 APIs (`std.io`, `std.fs`, `std.path`, `std.env`, `std.process`) accept and return valid UTF-8 `Str` and `String` values uniformly across every hosted target. On `x86_64-windows` and `aarch64-windows`, Level 3 (`std.sys.windows`) transcodes UTF-8 to/from null-terminated UTF-16LE (`u16`) internally — using stack-allocated `[264]u16` fast-path buffers and heap fallback with `\\?\` extended-length prefixing when required — and calls exclusively Unicode `*W` Win32 entry points (`CreateFileW`, `DeleteFileW`, `CreateDirectoryW`, `GetFileAttributesExW`, `FindFirstFileW`, `FindNextFileW`, `GetEnvironmentVariableW`, `GetCommandLineW`, `GetModuleFileNameW`), **never** ANSI codepage `*A` APIs (`0220 §6`). Unpaired UTF-16 surrogates or arbitrary non-UTF-8 Unix byte sequences from the host environment return explicit `Err(...)` in Level-1 UTF-8 APIs while remaining losslessly inspectable via Level-2 `std.os.windows` (`WideOsString` / `view<[u16]>`) and `std.os.unix` (`ByteOsString` / `view<[u8]>`). [0220 §6, §19, §30–31; std/fs/fs.ax; std/env/env.ax; std/process/process.ax]

**AXS-PLAT-008 — `std.io`, `std.fs` & `std.path` Portable Contracts (`0220 §19–21`, `std/io/io.ax`, `std/fs/fs.ax`).**
1. **`std.io`:** Provides `Stdin`, `Stdout`, `Stderr`, `IoError`, `print`, `println`, `eprint`, `eprintln`, and buffered readers/writers (`std/io/io.ax`). `println` and `eprintln` emit raw `\n` (`0x0A`) bytes uniformly across Windows, Unix, Android, and WASI with zero implicit C-runtime `\n -> \r\n` text-mode translation (`0097 §55`).
2. **`std.fs`:** Provides `File` (`!Copy`, `impl Drop` + `pub fn close(mut self: File) -> Result<(), FsError>`), `OpenOptions`, `Metadata`, `FsError`, `read`, `read_to_string`, `write`, `remove_file`, `create_dir`, and `read_dir` (`std/fs/fs.ax`). On `wasm32-wasi`, relative paths resolve strictly against preopened directory capabilities (`fd_prestat_get`) without assuming ambient `/` access (`0220 §10`, `SPEC-86 AXS-WASM-029`).
3. **`std.path`:** Provides allocation-free `Path` (`view` wrapper) and owned `PathBuf`, supporting native target path rules plus explicit target-independent `PosixPath` and `WindowsPath` types so cross-compilation and build tools running on any host OS parse both `/` and Windows drive/UNC `\` paths deterministically (`tasks/0587 §22`). [0097 §55; 0220 §10, §19–21; tasks/0587 §22; SPEC-86 AXS-WASM-029; std/io/io.ax; std/fs/fs.ax]

**AXS-PLAT-009 — `std.env` & `std.process` Runtime Authority & Process-Global Safety (`0220 §14, §30–31, AOS-37`, `SPEC-53 AXS-SEC-011`).**
1. **`std.env` (`std/env/env.ax`):** `get(name: Str) -> Option<String>` and `var(name: Str) -> Result<String, EnvError>` query process environment variables strictly at **runtime** (`0220 §30, AOS-37`; rejected in `comptime` and `--safety-profile sandbox` without `EnvCap`, `SPEC-53 AXS-SEC-011`). Because POSIX `setenv`/`unsetenv` mutates global process memory unsafely in the presence of concurrent reader threads (`0220 §30`), Level 1 exposes **no** safe ambient process-environment mutation; per-child environment overrides are configured safely on `std.process.Command.env(key, val)`.
2. **`std.process` (`std/process/process.ax`):** Provides `args() -> Vec<String>`, `exe_path() -> Result<String, ProcessError>`, `exit(code: i32) -> never` (which terminates the OS process immediately without unwinding stack frames or running pending local `Drop` glue; `0220 §14`), and `Command` / `Child` spawning direct argv vectors without shell interpolation (`CreateProcessW` on Windows; `posix_spawn` / `clone`+`execve` on Linux/macOS/Android; returning `Err(ProcessError.Unsupported)` on `wasm32-wasi` preview1). [0220 §14, §30–31, AOS-37; SPEC-53 AXS-SEC-011; std/env/env.ax; std/process/process.ax]

**AXS-PLAT-010 — `std.time` Dual-Clock Separation: Monotonic `Instant` vs Wall-Clock `SystemTime` (`0220 §25, AOS-30`, `std/time/time.ax`).** `std.time` strictly separates monotonic elapsed measurement from civil wall-clock time (`0220 §25, AOS-30`):
- **`Instant` (`std/time/time.ax`):** Monotonic, non-decreasing nanosecond timestamp (`Instant.now() -> Instant`, `duration_since(self: view<Instant>, earlier: view<Instant>) -> Duration`, `elapsed(self: view<Instant>) -> Duration`) backed by `QueryPerformanceCounter` on Windows, `clock_gettime(CLOCK_MONOTONIC)` on Linux/Android/WASI, and `clock_gettime_nsec_np(CLOCK_UPTIME_RAW)` on macOS. Timeout deadlines (`Deadline`, `TimerWheel`; `SPEC-34`, `SPEC-35`) accept **only** `Instant` / `Duration`, never `SystemTime`.
- **`SystemTime`:** Wall-clock timestamp (`SystemTime.now() -> SystemTime`, `duration_since_epoch(self: view<SystemTime>) -> Result<Duration, SystemTimeError>`) backed by `GetSystemTimePreciseAsFileTime` on Windows and `CLOCK_REALTIME` on Linux/macOS/Android/WASI, explicitly surfacing backward NTP/operator clock steps via `Result.Err`. [0220 §25, AOS-30; SPEC-34; SPEC-35; std/time/time.ax]

**AXS-PLAT-011 — `std.thread`, `std.sync` & `std.net` Portable Concurrency & Readiness (`0220 §15–16, §22–24, AOS-28..29`, `SPEC-32`, `SPEC-35`).** Level-1 `std.thread` (`spawn`, `JoinHandle`, `park`/`unpark`, `LocalKey<T>`), `std.sync` (`Mutex`, `RwLock`, `Condvar` over `WaitOnAddress`, `futex`, `__ulock_wait`, or WASM `memory.atomic.wait32`), and `std.net` / `std.async` (`TcpListener`, `TcpStream`, `UdpSocket`, `Reactor` over Windows `IOCP`, Linux `io_uring`/`epoll`, Android `epoll`, macOS `kqueue`, WASI `poll_oneoff`; `SPEC-32`, `SPEC-35`) present a single target-independent safe surface (`AOS-28..29`) with explicit blocking vs non-blocking modes and zero leaked OS readiness structs in Level-1 types. [0220 §15–16, §22–24, AOS-28..29; SPEC-32; SPEC-35]

**AXS-PLAT-012 — Virtual Memory `W^X` Enforcement & Capability-Bound `DynLib` Symbols (`0097 §26`, `0220 §17–18, §28–29, AOS-31..33`, `SPEC-82`).**
1. **`W^X` Page Protection Default (`AOS-33`):** Virtual page allocation APIs reject simultaneous write+execute permissions (`RWX`) by default (`ErrorKind.PermissionDenied`). JIT or dynamic code emission in `--profile system` MUST allocate `RW`, write machine bytes, transition pages to `RX`, and execute architectural instruction-cache synchronization (`FlushInstructionCache` on Windows, `sys_icache_invalidate` on macOS, `__builtin___clear_cache`/DC CVAU+IC IVAU on `aarch64-linux`/`android`, `riscv_flush_icache` on `riscv64-linux`) inside `unsafe` (`0220 §18, AOS-33`, `SPEC-87 AXS-RV64-043`).
2. **Capability-Scoped `DynLib` Lifetimes (`AOS-31..32`):** Loading a shared library (`DynLib.open(path: Str) -> Result<DynLib, OsError>`, backed by `LoadLibraryExW` / `dlopen`) is explicit, symbol resolution (`unsafe fn symbol<T>(self: view<DynLib>, name: Str) -> Result<LibSymbol<T>, OsError>`) requires `unsafe` because foreign symbol signatures are unverified by the OS loader (`AOS-31`), and `LibSymbol<T>` carries a stored capability tied to `view<DynLib>` (`SPEC-11`) so calling or holding `LibSymbol<T>` after `DynLib` is dropped or closed is rejected at compile time with `AX_CAP_OUTLIVES_OWNER` (`0220 §29, AOS-32`). [0097 §26; 0220 §17–18, §28–29, AOS-31..33; SPEC-11; SPEC-82 AXS-ELFD-042; SPEC-87 AXS-RV64-043]

---

## 6. Level 2 — `@cfg`-Gated `std.os.*` Platform Extension Modules (`AXS-PLAT-013`..`019`)

**AXS-PLAT-013 — `std.os.*` Module Layout & `@cfg` Gating Contract (`0097 §11`, `0220 §1, §37`, `T683`).** `std/os/` exposes explicit OS-scoped Level-2 modules whose `pub` declarations and re-exports are gated by `@cfg(...)`:
- `std.os.error` (`@cfg(not(profile = "freestanding"))`): `OsError`, `ErrorKind`;
- `std.os.windows` (`@cfg(target_os = "windows")`): Win32 `RawHandle`/`OwnedHandle`/`BorrowedHandle`, `RawSocket`/`OwnedSocket`/`BorrowedSocket`, `IocpHandle`, UTF-16 `WideOsString` helpers;
- `std.os.unix` (`@cfg(target_family = "unix")`): POSIX `RawFd`/`OwnedFd`/`BorrowedFd`, `AsRawFd`/`IntoRawFd`/`FromRawFd`, `PermissionsExt`, `ExitStatusExt`, `ByteOsString`;
- `std.os.linux` (`@cfg(target_os = "linux")`): re-exports `std.os.unix.*` plus Linux `Epoll`, `EpollEvent`, `EventFd`, `TimerFd`, `PidFd`, `memfd_create`;
- `std.os.macos` (`@cfg(target_os = "macos")`): re-exports `std.os.unix.*` plus Darwin `Kqueue`, `Kevent64`, `MachPort`, `MachTimebase`, `full_fsync`;
- `std.os.android` (`@cfg(target_os = "android")`): re-exports `std.os.unix.*` plus `TARGET_API_LEVEL`, `device_api_level()`, `LogPriority`, `log_write`, `SharedMemoryFd`;
- `std.os.wasi` (`@cfg(target_os = "wasi")`): `WasiFd`/`OwnedWasiFd`/`BorrowedWasiFd`, `PreopenDir`, `FdRights`, `preopen_dirs()`.
Because inactive `@cfg` items are pruned prior to name resolution (`AXS-XCMP-017`), importing a foreign OS module (such as `use std.os.linux.Epoll` when compiling for `--target x86_64-windows` or `use std.os.windows.OwnedHandle` when compiling for `--target aarch64-linux`) fails deterministically at compile time with `AX_NAME_UNRESOLVED_IMPORT` / `AX_NAME_UNRESOLVED`. [0097 §11, AOS-08; 0220 §1, §37, AOS-20, AOS-40]

**AXS-PLAT-014 — `std.os.windows`: Typed Win32 `HANDLE` / `SOCKET` Wrappers & Bridge Traits (`0220 §6, §20–24`, `tasks/0336 §15–17`).** `std.os.windows` models Windows kernel handles and WinSock2 sockets as distinct opaque types (`CloseHandle` != `closesocket`):
- `pub struct RawHandle { pub raw: usize }` (`Copy`, `@repr(transparent)`, with `RawHandle.NULL = RawHandle { raw: 0usize }` and `RawHandle.INVALID = RawHandle { raw: ~0usize }`), `pub struct OwnedHandle` (`!Copy`, `Send`, `Share`, `impl Drop` calling `CloseHandle`, plus `pub fn close(mut self: OwnedHandle) -> Result<(), OsError>`), and `pub struct BorrowedHandle` (capability-bound non-owning view).
- `pub struct RawSocket { pub raw: usize }`, `pub struct OwnedSocket` (`!Copy`, `impl Drop` calling `closesocket`), and `pub struct BorrowedSocket`.
- Explicit Level-1 <-> Level-2 bridge traits implemented for `std.fs.File` / `std.process.Child` (handles) and `std.net.{TcpListener,TcpStream,UdpSocket}` (sockets):
  - `pub trait AsRawHandle { fn as_raw_handle(self: view<Self>) -> RawHandle }`;
  - `pub trait IntoRawHandle { fn into_raw_handle(mut self: Self) -> RawHandle }` (transfers ownership out without closing);
  - `pub trait FromRawHandle { unsafe fn from_raw_handle(raw: RawHandle) -> Self }` (`unsafe`: caller guarantees exclusive ownership of an open kernel handle; calling outside `unsafe` emits `AX_UNSAFE_REQUIRED`);
  and parallel `AsRawSocket`, `IntoRawSocket`, `FromRawSocket`, plus `IocpHandle` (`CreateIoCompletionPort`, `GetQueuedCompletionStatusEx`, `PostQueuedCompletionStatus`). [0220 §6, §20–24, AOS-24..27; tasks/0336 §15–17, AFFI2-69..71; SPEC-50 AXS-UNS-001..005]

**AXS-PLAT-015 — `std.os.unix` & `std.os.linux`: Typed File Descriptors, `Epoll` & Linux Kernel Objects (`0220 §5, §20–26`, `tasks/0336 §18–19`).**
1. **`std.os.unix`:** Defines `@repr(transparent) pub struct RawFd { pub fd: i32 }` (`Copy`, valid iff `fd >= 0`), `pub struct OwnedFd` (`!Copy`, `Send`, `Share`, `impl Drop` calling non-retrying `close(fd)` per `AXS-PLAT-005`, plus `pub fn close(mut self: OwnedFd) -> Result<(), OsError>`), `pub struct BorrowedFd`, and bridge traits `AsRawFd` (`fn as_raw_fd(self: view<Self>) -> RawFd`), `IntoRawFd` (`fn into_raw_fd(mut self: Self) -> RawFd`), and `FromRawFd` (`unsafe fn from_raw_fd(fd: RawFd) -> Self`), alongside `PermissionsExt` (POSIX `u32` mode bits) and `ExitStatusExt` (termination signal inspection).
2. **`std.os.linux`:** Re-exports `std.os.unix.*` and provides safe `OwnedFd`-backed wrappers over Linux-specific kernel facilities across `x86_64`, `aarch64`, and `riscv64`: `Epoll` (`epoll_create1(EPOLL_CLOEXEC)`, `ctl`, `wait`), `EpollEvent`, `EventFd` (`eventfd2` with `EFD_CLOEXEC | EFD_NONBLOCK`), `TimerFd` (`timerfd_create` with `TFD_CLOEXEC`), `PidFd` (`pidfd_open`), and `memfd_create` (`MFD_CLOEXEC`). [0220 §5, §20–26; tasks/0336 §18–19; SPEC-80; SPEC-83; SPEC-87]

**AXS-PLAT-016 — `std.os.macos`: `Kqueue`, `MachPort`, `MachTimebase` & Darwin Durability (`0220 §7, §24–25`, `SPEC-84 AXS-MACHO-027, AXS-MACHO-030`).** `std.os.macos` re-exports `std.os.unix.*` and provides Darwin-native extensions backed strictly by `/usr/lib/libSystem.B.dylib`:
- `Kqueue` (`OwnedFd` over `kqueue()` + `kevent64` readiness batching) and `@repr(C) pub struct Kevent64`;
- `MachPort` (`!Copy` wrapper over `u32` `mach_port_t`, releasing send rights via `mach_port_deallocate(mach_task_self(), port)` in `Drop` — never POSIX `close()`!);
- `MachTimebase { pub numer: u32, pub denom: u32 }` (`mach_timebase_info`);
- `full_fsync(file: view<File>) -> Result<(), OsError>` invoking `fcntl(fd, F_FULLFSYNC)` for physical storage flush guarantees beyond POSIX `fsync` on Apple storage controllers. [0220 §7, §24–25; SPEC-84 AXS-MACHO-027, AXS-MACHO-030]

**AXS-PLAT-017 — `std.os.android`: API-Level Introspection, `logcat` & `SharedMemoryFd` (`0220 §9`, `SPEC-85 AXS-ANDR-001, AXS-ANDR-016`).** `std.os.android` re-exports `std.os.unix.*` and `Epoll`/`EventFd`, and provides:
- `pub const TARGET_API_LEVEL: u32` (reflecting the active `--android-api <N>` / `[target.aarch64-android] api_level`, default `29`) and `pub fn device_api_level() -> u32` (querying the running Bionic runtime API level);
- `pub enum LogPriority { Verbose, Debug, Info, Warn, Error, Fatal }` and safe UTF-8 `pub fn log_write(prio: LogPriority, tag: Str, msg: Str)` backed by `liblog.so` `__android_log_write`;
- `SharedMemoryFd` (`OwnedFd` wrapper over `ASharedMemory_create` when `TARGET_API_LEVEL >= 26`). [0220 §9; SPEC-85 AXS-ANDR-001, AXS-ANDR-016]

**AXS-PLAT-018 — `std.os.wasi`: Capability-Scoped `WasiFd`, `PreopenDir` & `FdRights` (`0220 §10`, `SPEC-86 AXS-WASM-029`).** `std.os.wasi` provides `@repr(transparent) pub struct WasiFd { pub fd: i32 }`, `OwnedWasiFd` (`!Copy`, `Drop` via `fd_close`, `pub fn close(mut self: OwnedWasiFd) -> Result<(), OsError>`), `BorrowedWasiFd`, `AsWasiFd`/`IntoWasiFd`/`FromWasiFd` (`unsafe`), `FdRights` (64-bit capability rights mask), `PreopenDir { fd: BorrowedWasiFd, guest_path: String }`, and `preopen_dirs()`, keeping every filesystem/clock/random operation explicitly capability-scoped. [0220 §10; SPEC-86 AXS-WASM-029]

**AXS-PLAT-019 — Hardware Fault Isolation vs Async-Signal-Safe Notification (`0220 §26–27, AOS-34`).** Synchronous CPU/VM hardware faults (`SIGSEGV`, `SIGBUS`, `SIGILL`, `SIGFPE`, Windows `EXCEPTION_ACCESS_VIOLATION` / `STATUS_STACK_OVERFLOW`, WASM `unreachable`) indicate UB or unrecoverable traps and are **never** caught as recoverable `Result.Err` values (`0220 §27, AOS-34`). Safe process signal handling in `std.os.{unix,windows}` (`CtrlC` / `SignalFd` / `EVFILT_SIGNAL` / Win32 `SetConsoleCtrlHandler` event wakeup) never runs user Axiom closures directly on an interrupted signal frame, delivering notifications strictly through async-signal-safe kernel descriptors or atomic flags (`0220 §26`). [0220 §26–27, AOS-34; SPEC-54]

---

## 7. Level 3 — `std.sys.*` Static Host Dispatch & Diagnostics (`AXS-PLAT-020`..`022`)

**AXS-PLAT-020 — Zero-Overhead `@cfg` Static Dispatch from `std.core.host` to `std.sys.*` (`SPEC-04 AXS-EXT-110`, `ADR-0002`, `T683`).** `std/core/host.ax` binds the `SPEC-04 AXS-EXT-110` host intrinsics (`heap_alloc`, `heap_realloc`, `heap_free`, `stdio`, `open`, `read`, `write`, `close`, `file_size`, `args_count`, `arg`, `env_get`, `exe_path`, `exit`, `remove`, `mkdir`, `metadata`, `dir_open`, `dir_next`, `dir_close`, `monotonic_ns`, plus the concurrency, fiber, and async-I/O host intrinsics `thread_*`, `futex_*` of `SPEC-32 AXS-SYNC-002`, `fiber_*` of `SPEC-34 AXS-EXEC-054`, and `aio_*` of `SPEC-35 AXS-AIO-050`) at compile time via mutually exclusive `@cfg(...)` routing with **zero** runtime vtable indirection:

| Active `@cfg` Target / Mode | Selected Level-3 `std.sys.*` Provider | Underlying OS ABI Mechanism |
|---|---|---|
| `target_os = "windows", target_arch = "x86_64"` | `std.sys.windows` (`std/sys/windows/`) | Win64 `extern "system"` DLL imports (`kernel32`, `ws2_32`, `bcrypt`) |
| `target_os = "windows", target_arch = "aarch64"` | `std.sys.windows` + `std.sys.windows.arm64` (`T695`) | WinArm64 `extern "system"` DLL imports + `x18` TEB |
| `target_os = "linux", target_arch = "x86_64"` | `std.sys.linux` (+ `std.sys.linux_dl` when dynamic) | Direct x86-64 `syscall` (`0F 05`; `SPEC-80`, `SPEC-82`) |
| `target_os = "linux", target_arch = "aarch64"` | `std.sys.linux_aarch64` | Direct A64 `svc #0` (`asm-generic/unistd.h`; `SPEC-83`) |
| `target_os = "linux", target_arch = "riscv64"` | `std.sys.linux_riscv64` | Direct RV64 `ecall` (`asm-generic/unistd.h`; `SPEC-87`) |
| `target_os = "macos"` (`aarch64` / `x86_64`) | `std.sys.macos` | `/usr/lib/libSystem.B.dylib` `extern "C"` imports (`SPEC-84`) |
| `target_os = "android", target_arch = "aarch64"` | `std.sys.android` | Bionic `libc.so` / `liblog.so` + `futex`/`epoll` (`SPEC-85`) |
| `target_os = "wasi", target_arch = "wasm32"` | `std.sys.wasi` | `wasi_snapshot_preview1` `@wasm_import` + `memory.grow` (`SPEC-86`) |
| `profile = "freestanding"` or `profile = "kernel"` | *None* (`0` OS modules compiled) | Any reachable `os_*` host call rejected (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `SPEC-52`) |
| `--interp` (MIR oracle, `ADR-0002`) | Interpreter `host` intrinsic table | Deterministic sandboxed/host oracle dispatch (`ADR-0002`) |

Inactive `std.sys.*` modules are pruned before HIR resolution (`AXS-XCMP-017`), ensuring zero foreign-OS symbols or dead syscall shims ever enter MIR, LIR, or linked artifacts (`0097 §11, §51`, `0220 §37–38`). [0097 §11, §51; 0220 §37–38; ADR-0002; SPEC-04 AXS-EXT-110; SPEC-32 AXS-SYNC-002; SPEC-34 AXS-EXEC-054; SPEC-35 AXS-AIO-050; SPEC-52 AXS-FRE-022; SPEC-80..87]

**AXS-PLAT-021 — Atomic `CLOEXEC` / Non-Inheritable Handle Creation Default (`0220 §19–22`).** Every file descriptor, directory handle, socket, pipe, epoll, kqueue, eventfd, timerfd, or shared-memory descriptor created inside Level 3 (`std.sys.*`) MUST enable close-on-exec / non-inheritance **atomically at creation time** (`O_CLOEXEC`, `SOCK_CLOEXEC`, `EPOLL_CLOEXEC`, `EFD_CLOEXEC`, `TFD_CLOEXEC`, `F_DUPFD_CLOEXEC`, and `SECURITY_ATTRIBUTES.bInheritHandle = 0` on Windows) so concurrent `Command.spawn` calls on other threads never leak private handles into child processes (`0220 §19–22`). Only explicit stdio/handle inheritance entries configured on `std.process.Command` opt into child inheritance. [0220 §14, §19–22]

**AXS-PLAT-022 — Normative Diagnostic Matrix (`SPEC-88`, `spec/diagnostics.md` §10–11).**

| Diagnostic Code | Area / Sev | Emitting Stage | Condition & Governing Rule(s) |
|---|---|---|---|
| `AX_NAME_INVALID_CFG_PREDICATE` | `NAME` (E) | `compiler/hir/cfg` (`T682`) | Malformed `@cfg(...)` arity/syntax (`@cfg()`, `@cfg(a, b)`, `not(a, b)`), non-string value literal, bare OS/arch identifier (`@cfg(windows)`), unknown `@cfg` key, value outside closed canonical set (`@cfg(target_os = "win32")`), or undeclared `--cfg` / `feature` name (`AXS-XCMP-012`..`017`, `AXS-XCMP-020`) |
| `AX_DRIVER_SYSROOT_NOT_FOUND` | `DRIVER` (E) | `compiler/driver/cross` / `compiler/link/sysroot` (`T682`, `T683`) | Explicit `--sysroot <dir>` or `--target-sdk <dir>` path does not exist or is not a readable directory (exit code `2`; `AXS-XCMP-021`..`022`) |
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` (E) | `compiler/driver/cross` | Unknown `--target <triple>` (exit code `2`; `AXS-XCMP-001`..`002`) |
| `AX_NAME_UNRESOLVED_IMPORT` / `AX_NAME_UNRESOLVED` | `NAME` (E) | `compiler/resolve` | Importing or referencing `@cfg`-pruned `std.os.<other>` items on a non-matching target (`AXS-XCMP-017`, `AXS-PLAT-013`) |
| `AX_NAME_DUPLICATE` | `NAME` (E) | `compiler/resolve` | Two items with overlapping `@cfg` predicates both evaluate to `true` on the active target (`AXS-XCMP-017`) |
| `AX_NAME_FREESTANDING_FORBIDDEN_IMPORT` / `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `NAME` / `DRIVER` (E) | `compiler/resolve` / `driver` | Hosted Level-1 or Level-2 `std.os.*` module imported, or `os_*` host capability reached, in `--profile freestanding` or `kernel` (`AXS-XCMP-028`, `AXS-PLAT-002`, `AXS-PLAT-020`; `SPEC-52`) |
| `AX_TARGET_UNSUPPORTED_OP` / `AX_TARGET_UNKNOWN_FEATURE` / `AX_TARGET_FEATURE_CONFLICT` / `AX_TARGET_FEATURE_MISMATCH` / `AX_TARGET_API_LEVEL_TOO_LOW` | `TARGET` (E) | `compiler/target/*` / `link` | Unsupported target operation/ABI, invalid/conflicting CPU feature, unguarded `@target_feature` call, or Android symbol above `target.api_level` (`AXS-XCMP-010`, `AXS-XCMP-026`; `SPEC-44`, `SPEC-81`, `SPEC-85`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` / `AX_LINK_LIBRARY_NOT_FOUND` / `AX_LINK_ANDROID_PRIVATE_LIB` | `LINK` (E) | `compiler/link/*` | Cross-target `.obj`/`.o`/`.wasm`/`.axmi`/`.lib`/`.a` mismatch, missing `-l<name>` in hermetic search paths, or forbidden private Android `.so` (`AXS-XCMP-009`, `AXS-XCMP-021`..`026`; `SPEC-24`, `SPEC-26`, `SPEC-85`) |
| `AX_UNSAFE_REQUIRED` / `AX_CAP_OUTLIVES_OWNER` / `AX_SEC_CAPABILITY_FORGERY` / `AX_CTM_CAPABILITY_DENIED` | `UNSAFE` / `CAP` / `SEC` / `CTM` (E) | `types` / `own` / `comptime` | `FromRawHandle`/`FromRawFd`/`DynLib.symbol` outside `unsafe`, `BorrowedHandle`/`BorrowedFd`/`LibSymbol` escaping owner, handle-to-view forgery, or ambient OS call in `comptime` (`AXS-XCMP-006`, `AXS-PLAT-004`, `AXS-PLAT-012`, `AXS-PLAT-014`..`018`) |

[spec/diagnostics.md §3, §10–11; SPEC-24; SPEC-26; SPEC-44; SPEC-50; SPEC-52; SPEC-53; SPEC-60; SPEC-81; SPEC-85]

---

## 8. Canonical Examples, Conformance Matrix & Traceability (`AXS-PLAT-023`..`024`)

**AXS-PLAT-023 — Canonical Positive & Negative Examples (`=` and `.` Syntax).**

```axiom
// Positive Example 1: Single-source multi-target cross-compilation with @cfg pruning,
// target-parameterized const layout (4 bytes on wasm32-wasi, 8 bytes on 64-bit targets),
// and Level-1 portable UTF-8 output.
// Builds from any host OS without third-party compilers:
//   axiomc build --target x86_64-windows hello_cross.ax -o hello.exe
//   axiomc build --target x86_64-linux   hello_cross.ax -o hello_linux
//   axiomc build --target aarch64-linux  hello_cross.ax -o hello_a64
//   axiomc build --target riscv64-linux  hello_cross.ax -o hello_rv64
//   axiomc build --target aarch64-macos  hello_cross.ax -o hello_macos
//   axiomc build --target aarch64-android hello_cross.ax -o hello_android
//   axiomc build --target wasm32-wasi    hello_cross.ax -o hello.wasm
module demo.hello_cross

use std.io.println

const WORD_BYTES: usize = size_of<usize>()
const PTR_ALIGN: usize = align_of<*const u8>()

struct TargetReport {
    greeting: Str
    os_tag: Str
    word_bytes: usize
}

@cfg(target_os = "windows")
fn current_os_tag() -> Str { "windows" }

@cfg(target_os = "linux")
fn current_os_tag() -> Str { "linux" }

@cfg(target_os = "macos")
fn current_os_tag() -> Str { "macos" }

@cfg(target_os = "android")
fn current_os_tag() -> Str { "android" }

@cfg(target_os = "wasi")
fn current_os_tag() -> Str { "wasi" }

pub fn main() -> i32 {
    let report = TargetReport {
        greeting: "Xin chào thế giới",
        os_tag: current_os_tag(),
        word_bytes: WORD_BYTES,
    }
    println(report.greeting)
    println(report.os_tag)
    @cfg(target_pointer_width = "32")
    let expected: usize = 4
    @cfg(target_pointer_width = "64")
    let expected: usize = 8
    if report.word_bytes == expected && PTR_ALIGN == expected {
        return 0
    }
    return 1
}
```

```axiom
// Positive Example 2: 3-level OS platform boundary — Level-1 portable File with explicit
// fallible close(), bridging cleanly to Level-2 @cfg-gated typed handles without leaking
// OS handle types into the portable public signature.
module demo.platform_handle_bridge

use std.core.result.Result
use std.fs.{File, FsError}

@cfg(target_os = "windows")
use std.os.windows.{AsRawHandle, RawHandle}

@cfg(target_family = "unix")
use std.os.unix.{AsRawFd, RawFd}

@cfg(target_os = "wasi")
use std.os.wasi.{AsWasiFd, WasiFd}

fn has_valid_os_token(file: view<File>) -> bool {
    @cfg(target_os = "windows")
    {
        let h: RawHandle = file.as_raw_handle()
        return h.raw != 0usize && h.raw != ~0usize
    }
    @cfg(target_family = "unix")
    {
        let fd: RawFd = file.as_raw_fd()
        return fd.fd >= 0
    }
    @cfg(target_os = "wasi")
    {
        let fd: WasiFd = file.as_wasi_fd()
        return fd.fd >= 0
    }
}

pub fn verify_log_file(file: File) -> Result<bool, FsError> {
    let valid = has_valid_os_token(view(file))
    file.close()?
    Result.Ok(valid)
}
```

```axiom
// Negative Example 1: @cfg predicate validation & parse-all-before-prune enforcement.
// Compiled on --target x86_64-windows:
module demo.bad_cfg_and_inactive_syntax

@cfg(windows) //~ ERROR AX_NAME_INVALID_CFG_PREDICATE
fn shorthand_os_rejected() -> i32 { 1 }

@cfg(target_os = "win32") //~ ERROR AX_NAME_INVALID_CFG_PREDICATE
fn noncanonical_os_rejected() -> i32 { 2 }

@cfg(target_os = "linux")
fn inactive_branch_still_parsed() -> i32 {
    let broken: = 1 //~ ERROR AX_PARSE_EXPECTED_TYPE
    broken
}
```

```axiom
// Negative Example 2: Importing a pruned foreign std.os module and calling FromRawHandle
// outside unsafe are both rejected at compile time (compiled on --target x86_64-windows).
module demo.bad_foreign_os_and_unsafe_bridge

use std.fs.File
use std.os.linux.Epoll //~ ERROR AX_NAME_UNRESOLVED_IMPORT
use std.os.windows.{FromRawHandle, RawHandle}

pub fn forge_without_unsafe(raw: usize) -> File {
    File.from_raw_handle(RawHandle { raw: raw }) //~ ERROR AX_UNSAFE_REQUIRED
}
```

**AXS-PLAT-024 — Requirement, Invariant, Corpus & Task Traceability Matrix (`E16.8`: `T681`–`T684`).**

| Task | Scope | Invariant(s) | Covered Requirements | Primary Deliverable / Test Suites |
|---|---|---|---|---|
| `T681` | `SPEC-88`: Canonical single-binary cross-compilation, `Build`/`Host`/`Target` isolation, `@cfg` target matrix, hermetic sysroot/stub catalogs & 3-level OS platform layer specification | `INV-XCMP-001`..`003` | `REQ-TOOL-001`, `REQ-TGT-080`..`REQ-TGT-084` | `spec/SPEC-88-cross-compilation-platform-layer.md` |
| `T682` | `compiler/hir/cfg` & `compiler/driver/cross`: `@cfg(...)` parse-all-then-prune-before-resolve evaluator, `AX_NAME_INVALID_CFG_PREDICATE`, target-parameterized `const`/`comptime` layout, and cross-compilation driver | `INV-XCMP-001` | `REQ-TOOL-001`, `REQ-TGT-319`, `REQ-TGT-321`..`REQ-TGT-323` | `tests/run/cfg_target`, `tests/ui/cfg`, `tests/selfhost/hir`, `tests/selfhost/driver` |
| `T683` | `std/os` & `compiler/link/sysroot`: Level-2 `@cfg`-gated `std.os.{windows,linux,macos,android,wasi,unix,error}`, Level-3 `std.sys.*` static host routing, and hermetic `--sysroot` + built-in OS import stub catalogs | `INV-XCMP-002` | `REQ-TOOL-001`, `REQ-TGT-320`, `REQ-TGT-324`..`REQ-TGT-325` | `tests/std/os_platform`, `tests/selfhost/link` |
| `T684` | End-to-end `E16.8` cross-compilation target matrix, `@cfg` positive/negative UI, cross-host byte-for-byte determinism, and 3-level OS platform differential conformance suite | `INV-XCMP-003` | `REQ-TOOL-001`, `REQ-TGT-318`, `REQ-TGT-326` | `tests/conformance/p16/e16_8_cross_compile` |

Detailed requirement and corpus-anchor mapping:

| Requirement / Corpus Anchor | Canonical `SPEC-88` Rule(s) | Board Task(s) |
|---|---|---|
| `REQ-TOOL-001` (`0097 §27, §54`: zero third-party compilers/assemblers/linkers) | `AXS-XCMP-001`, `AXS-XCMP-021`..`028` | `T681`, `T682`, `T683`, `T684` |
| `REQ-TGT-080` (`AMACHINE-91`: frontend ISA independence) | `AXS-XCMP-004`, `AXS-XCMP-005` | `T681` |
| `REQ-TGT-081` (`AMACHINE-92`: common `TargetBackend` contract) | `AXS-XCMP-001`, `AXS-XCMP-004` | `T681` |
| `REQ-TGT-082`..`REQ-TGT-084` (`AMACHINE-93..95`: zero LLVM semantic dependency, replaceable bootstrap, self-hostable native backends) | `AXS-XCMP-004` | `T681` |
| `REQ-TGT-318`, `REQ-TGT-326` (`ABACKEND-93`, `0524 §113`: common semantic conformance & frontend-meaning vs backend-realization split) | `AXS-XCMP-004`, `AXS-PLAT-023`..`024` | `T684` |
| `REQ-TGT-319` (`ABACKEND-94`: backend cache identity includes target & codegen facts) | `AXS-XCMP-005`, `AXS-XCMP-009`, `AXS-XCMP-027` | `T682` |
| `REQ-TGT-320` (`ABACKEND-95`: deterministic reproducible backend compilation across hosts) | `AXS-XCMP-008`, `AXS-XCMP-027` | `T683` |
| `REQ-TGT-321` (`ABACKEND-96`: actionable diagnostics naming unsupported target requirements) | `AXS-XCMP-010`, `AXS-PLAT-022` | `T682` |
| `REQ-TGT-322`..`REQ-TGT-323` (`ABACKEND-97..98`: zero Core syntax leak & additive target extensibility) | `AXS-XCMP-004`, `AXS-XCMP-011`..`019` | `T682` |
| `REQ-TGT-324`..`REQ-TGT-325` (`ABACKEND-99..100`: `Axiom LIR` portability boundary & single semantic compiler) | `AXS-XCMP-004`, `AXS-PLAT-020` | `T683` |
| `0097 §1–61` (`AOS-01..35`) & `0220 §1–40` (`AOS-20..40`: 3-level OS layer, optional `libc`, `!Copy`+`Drop`+`close()`, `OsError`, `Instant`/`SystemTime`, `W^X`, `DynLib`, freestanding) | `AXS-XCMP-011`..`019`, `AXS-XCMP-028`, `AXS-PLAT-001`..`021` | `T681`, `T682`, `T683`, `T684` |
| `tasks/0336 §15–24, §49–52, §73–80` (`AFFI2-58..75, 91..93`: opaque vs borrowed handles, immediate thread-local `errno`/`GetLastError`, cross-target ABI) | `AXS-PLAT-001`, `AXS-PLAT-003`..`006`, `AXS-PLAT-014`..`018` | `T681`, `T683` |
| `tasks/0453 §194.1–44` (`ATARGET-20..50`) & `tasks/0587 §1–40` (`ATARGET-01..30`: `Build`/`Host`/`Target`, 3-tier query sharing, `@cfg` namespaces, hermetic sysroot, target `comptime`) | `AXS-XCMP-001`..`028` | `T681`, `T682`, `T683`, `T684` |

## Sources

0097 §1–61 (`AOS-01..35`); 0220 §1–40 (`AOS-20..40`); tasks/0336 §15–24, §49–52, §73–80 (`AFFI2-20..100`); tasks/0453 §194.1–194.44 (`ATARGET-20..50`); tasks/0518 §151 (`AMACHINE-91..95`); tasks/0524 §112–113 (`ABACKEND-93..100`); tasks/0587 §1–40 (`ATARGET-01..30`); ADR-0002; ADR-0003; ADR-0006; `spec/SPEC-02-grammar.md` (`AXS-GRM-020..037`, `AXS-GRM-043`, `AXS-GRM-056`, `AXS-GRM-073`, §12); `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-091`, `AXS-EXT-110`); `spec/SPEC-20-selfhost.md`; `spec/SPEC-21-query-engine-semantic-db.md`; `spec/SPEC-22-incremental-compilation.md` (`AXS-INC-021`); `spec/SPEC-23-parallel-compilation.md`; `spec/SPEC-24-artifact-format-module-interfaces.md` (`AXS-ART-010..013`, `AXS-ART-022..023`); `spec/SPEC-26-windows-artifact-kinds.md` (`AXS-WLIB-003`, `AXS-WLIB-030..031`); `spec/SPEC-27-separate-compilation-linker-v2.md`; `spec/SPEC-32-threads-sync.md` (`AXS-SYNC-002`); `spec/SPEC-34-executors-fibers.md` (`AXS-EXEC-054`); `spec/SPEC-35-async-io.md` (`AXS-AIO-050`); `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-43-simd-backend.md`; `spec/SPEC-44-cpu-features-multiversioning.md` (`AXS-CPU-003`); `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-001..005`); `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md` (`AXS-FRE-002..003`, `AXS-FRE-010`, `AXS-FRE-012`, `AXS-FRE-022`); `spec/SPEC-53-safety-profiles-capability-security.md` (`AXS-SEC-002`, `AXS-SEC-004`, `AXS-SEC-011`); `spec/SPEC-54-panic-unwinding.md` (`AXS-PAN-001`); `spec/SPEC-55-fixed-address-declarations.md`; `spec/SPEC-60-comptime-2-0.md` (`AXS-CTM-003`, `AXS-CTM-013`, `AXS-CTM-021`, `AXS-CTM-034`); `spec/SPEC-61-reflection-derive.md`; `spec/SPEC-70-optir-ssa-memoryssa.md`; `spec/SPEC-73-inlining-specialization-devirt.md`; `spec/SPEC-74-auto-vectorization.md`; `spec/SPEC-77-regalloc-machine-opt.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md` (`AXS-TGTD-001..003`, `AXS-TGTD-007..009`, `AXS-TGTD-029..032`, `AXS-TGTD-039..043`); `spec/SPEC-82-linux-elf-dynamic.md` (`AXS-ELFD-031`, `AXS-ELFD-036..043`); `spec/SPEC-83-aarch64-linux.md`; `spec/SPEC-84-macos-aarch64-macho.md` (`AXS-MACHO-021`, `AXS-MACHO-025`, `AXS-MACHO-027..030`, `AXS-MACHO-032`); `spec/SPEC-85-android-aarch64-jni.md` (`AXS-ANDR-001`, `AXS-ANDR-012..016`); `spec/SPEC-86-wasm32-backend.md` (`AXS-WASM-001`, `AXS-WASM-028..029`); `spec/SPEC-87-riscv64-linux.md` (`AXS-RV64-043`); `spec/invariants.md` (`INV-XCMP-001..003`); `spec/diagnostics.md`.
