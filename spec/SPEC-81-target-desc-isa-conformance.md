# SPEC-81 — Canonical Declarative TargetDesc, RegisterFile, ISA Tables, Legalizer & Backend Conformance Specification

- **Status:** draft (T653, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-060..062`, `AXS-EXT-070..074`), `spec/SPEC-43-simd-backend-x86.md`, `spec/SPEC-44-cpu-feature-dispatch.md`, `spec/SPEC-77-regalloc-machine-opt.md`, `spec/SPEC-80-linux-x86-64-elf-static.md`, `0162`, `0163`, `tasks/0472`, `tasks/0518`, `tasks/0520`, `tasks/0521`, `tasks/0524`, `tasks/0784`
- **Covers:** `REQ-TGT-004`, `REQ-TGT-005`, `REQ-TGT-006`, `REQ-TGT-007`, `REQ-TGT-008`, `REQ-TGT-009`, `REQ-TGT-010`, `REQ-TGT-011`, `REQ-TGT-285`, `REQ-TGT-286` (and specifies the E16.1 contract for `T654`, `T655`, `T656`: `REQ-TGT-012`..`REQ-TGT-036`, `REQ-TGT-044`..`REQ-TGT-058`, `REQ-TGT-085`..`REQ-TGT-095`, `REQ-TGT-107`..`REQ-TGT-109`, `REQ-TGT-287`..`REQ-TGT-295`)
- **Consumers:** `compiler/target/desc`, `compiler/abi/table`, `compiler/target/isa`, `compiler/backend/verify_mc`, `tests/run/target_desc`, `tests/selfhost/abi`, `tests/mc/isa_table`, `tests/selfhost/backend`, `tests/selfhost/isel`, `tests/conformance/p16/e16_1_target_desc`, `T654`, `T655`, `T656`

## Tóm tắt

Tài liệu `SPEC-81` chốt đặc tả chuẩn cho kiến trúc mô tả đích khai báo (`TargetDesc` / `TargetSpec`), mô hình tệp thanh ghi (`RegisterFile`), bảng tập lệnh (`IsaTable`), bộ hợp thức hóa (`Legalizer`), trình kiểm chứng Machine IR trước mã hóa (`verify_mc`), và hợp đồng tương thích ngữ nghĩa độc lập đích của Axiom (Epic `E16.1`):
1. **Mô tả đích khai báo (`TargetDesc`, `AXS-TGTD-001`..`012`):** Mọi khác biệt kiến trúc/nền tảng (`TargetId`, `TargetFingerprint` 128 bit, `Arch`, `Os`, `Env`, `CallConv`, độ rộng con trỏ, thứ tự byte `Endian`, căn chỉnh tự nhiên/ngăn xếp, `ObjectFormat`, `ArchiveFormat`, `ImageFormat`, đồ thị suy diễn `TargetFeatureSet` cho `AVX2`/`AVX-512`/`NEON`/`SVE`/`RVV`/`RVC`/`LSE`/WASM, và bảng phân loại ABI `CallConvDesc`) được biểu diễn thuần túy bằng bảng dữ liệu tĩnh biên dịch sẵn thay vì rải các nhánh `if target == ...` trong lõi trình biên dịch (`0163 §1`, `tasks/0784 §562.2–16`).
2. **Mô hình `RegisterFile` phân cấp và bí danh thanh ghi (`AXS-TGTD-013`..`023`):** Mô hình hóa thanh ghi vật lý, mặt nạ bit đơn vị thanh ghi cơ sở (`RegUnit`) để phát hiện chồng lấp, quan hệ thanh ghi con/cha tường minh (`RAX`/`EAX`/`AX`/`AL`/`AH`, `ZMM`/`YMM`/`XMM`, `X0`/`W0`, `Q0`/`D0`/`S0`), các thanh ghi kiến trúc dành riêng (`RSP`, `SP`, `XZR`, `X18`, `x0`, `gp`, `tp`), các lớp thanh ghi (`RegClass`), tập bảo toàn bởi hàm gọi/được gọi, và hai tầng cấp phát thanh ghi (`LinearScan` ở `-O0`/`-O1` và `Hybrid/Graph` ở `-O2`).
3. **Bảng tập lệnh `IsaTable`, `Legalizer` và trình kiểm chứng `verify_mc` (`AXS-TGTD-024`..`038`):** Chuẩn hóa bộ chọn lệnh dựa trên mẫu (`Pattern-based ISel`), ràng buộc toán hạng, thanh ghi ngầm định (`RAX:RDX`, `RCX`, clobber khi `CALL`), mô hình hóa cờ điều kiện cho cả ISA dùng thanh ghi cờ (`RFLAGS`, `NZCV`) và ISA không cờ (`RISC-V`, `WASM`), quy tắc mở rộng `Legalizer` bảo toàn tràn số/nguyên tử/`volatile`/tách biệt `trap` phần cứng với `panic`, và cổng kiểm chứng `verify_mc` bắt buộc trước khi mã hóa nhị phân.
4. **Ranh giới khả chuyển ngữ nghĩa LIR và hợp đồng kiểm thử tương thích (`AXS-TGTD-039`..`053`):** `Axiom LIR` là ranh giới khả chuyển ngữ nghĩa duy nhất của trình biên dịch bản địa (`ABACKEND-99..100`); tệp mẫu hợp ngữ (assembly golden) chỉ kiểm tra chất lượng mã chứ không phải thẩm quyền ngữ nghĩa (`ABACKEND-90`); mọi đích biên dịch phải vượt qua bộ kiểm thử đối chiếu chung với trình thông dịch `--interp` (`ABACKEND-61, 91..93`).

---

## 1. Declarative `TargetDesc` Schema, Identity, Data Layout & `TargetFeatureSet` (`AXS-TGTD-001`..`012`)

**AXS-TGTD-001 — Declarative `TargetDesc` Architecture & Zero Scattered Target Branching.** Every compilation target in `axiomc` is described by an immutable, table-driven `TargetDesc` (`TargetSpec`) record in `compiler/target/desc` (`0163 §1`, `tasks/0524 §5–6`, `tasks/0784 §562.2, §562.200 #4–6, #41–42`, `SPEC-04 AXS-EXT-060`). Instruction selection, register allocation, frame lowering, scheduling, encoding, object emission, and ABI lowering query `TargetDesc` tables rather than scattering `if target == ...` chains across the compiler core. Frontend and middle-end phases above `LIR` are strictly target-independent except for querying `pointer_width`, `endian`, `layout_of`, and `@cfg` / `@target_feature` predicates (`SPEC-04 AXS-EXT-061`, `REQ-TGT-004`, `REQ-TGT-005`). [0163 §1; tasks/0518; tasks/0524 §5–6; tasks/0784 §562.2; SPEC-04 AXS-EXT-060..061; REQ-TGT-004, REQ-TGT-005]

**AXS-TGTD-002 — Canonical `TargetId` & Supported Target Triple Matrix.** `compiler/target/desc` normalizes user `--target <triple>` strings into a canonical `TargetId` enum and rejects unknown triples with `AX_DRIVER_UNKNOWN_TARGET` (`tasks/0784 §562.3–4, §562.200 #1, #91–92`, `SPEC-04 AXS-EXT-061`, `REQ-TGT-105`):

| `TargetId` | Canonical Triple | Accepted Vendor/ABI Aliases | `Arch` | `Os` | Default `CallConv` | `ObjectFormat` / `ArchiveFormat` / `ImageFormat` |
|---|---|---|---|---|---|---|
| `X86_64Windows` | `x86_64-windows` | `x86_64-pc-windows-msvc` | `X86_64` | `Windows` | `Win64` | `Coff` / `CoffAr` / `Pe32Plus` (`Pe32PlusDll`) |
| `X86_64Linux` | `x86_64-linux` | `x86_64-unknown-linux-gnu`, `x86_64-unknown-linux-musl` | `X86_64` | `Linux` | `SysV64` | `Elf` / `GnuAr` / `ElfExec` (`ElfDyn`) |
| `AArch64Linux` | `aarch64-linux` | `aarch64-unknown-linux-gnu`, `aarch64-unknown-linux-musl` | `AArch64` | `Linux` | `Aapcs64` | `Elf` / `GnuAr` / `ElfExec` (`ElfDyn`) |
| `AArch64Macos` | `aarch64-macos` | `aarch64-apple-darwin` | `AArch64` | `Macos` | `Aapcs64Darwin` | `MachO` / `BsdAr` / `MachO` |
| `AArch64Android` | `aarch64-android` | `aarch64-linux-android` | `AArch64` | `Android` | `Aapcs64` | `Elf` / `GnuAr` / `ElfDyn` |
| `AArch64Windows` | `aarch64-windows` | `aarch64-pc-windows-msvc` | `AArch64` | `Windows` | `WinArm64` | `Coff` / `CoffAr` / `Pe32Plus` (`Pe32PlusDll`) |
| `Wasm32` | `wasm32` | `wasm32-unknown-unknown`, `wasm32-wasi`, `wasm32-unknown-wasi` | `Wasm32` | `None` / `Wasi` | `WasmBasic` | `Wasm` / `GnuAr` / `Wasm` |
| `Riscv64Linux` | `riscv64-linux` | `riscv64gc-unknown-linux-gnu`, `riscv64-unknown-linux-musl` | `Riscv64` | `Linux` | `RiscvLp64d` | `Elf` / `GnuAr` / `ElfExec` (`ElfDyn`) |

[0163 §1; tasks/0784 §562.3–4, §562.200 #1, #87–92; SPEC-04 AXS-EXT-061, AXS-EXT-070; SPEC-80 AXS-ELFS-001; REQ-TGT-105]

**AXS-TGTD-003 — Deterministic 128-Bit `TargetFingerprint` & Cross-Target Cache Isolation.** Each resolved target configuration computes a deterministic 128-bit BLAKE3 `TargetFingerprint` over `(TargetId, Arch, SubArch, Os, Env, default_call_conv, ObjectFormat, ArchiveFormat, ImageFormat, pointer_width, Endian, DataLayout, cpu_model, tuning_model, enabled_features_mask, disabled_features_mask, CodeModel, RelocModel, TlsModel, Profile, PanicStrategy)` (`tasks/0524 §91, ABACKEND-94`, `tasks/0784 §562.5, §562.151–152, §562.200 #2–3, #102–113`). Target-independent semantic queries (`CompilerDB` AST/HIR/THIR/Verified MIR) exclude physical register assignments and are reusable across targets when `@cfg` inputs match, whereas `CodegenFingerprint`, `.axcache` machine artifacts, `.axmi`, and `.axmeta` embed `TargetFingerprint` to forbid cross-ISA, cross-ABI, or cross-feature unsafe cache reuse (`AX_LINK_ARTIFACT_TARGET_MISMATCH`). [tasks/0524 §91, ABACKEND-94; tasks/0784 §562.5, §562.146–152, §562.200 #2–3, #102–113; SPEC-22 AXS-INC-001; SPEC-24 AXS-ART-022]

**AXS-TGTD-004 — Architecture, OS, Environment & ABI Orthogonal Identity.** `TargetDesc` separates `Arch` (`X86_64`, `AArch64`, `Wasm32`, `Riscv64`), `Os` (`Windows`, `Linux`, `Macos`, `Android`, `Wasi`, `None`), `Env` (`Msvc`, `Gnu`, `Musl`, `Darwin`, `Android`, `Wasi`, `Freestanding`), and `CallConv` (`Win64`, `SysV64`, `Aapcs64`, `Aapcs64Darwin`, `WinArm64`, `WasmBasic`, `RiscvLp64d`, `Interrupt`, `GpuKernel`) as orthogonal fields (`tasks/0784 §562.2, §562.200 #4–6, #88–90`, `SPEC-04 AXS-EXT-052`). Sharing an `Arch` reuses `RegisterFile` and `IsaTable` across OSes (`x86_64-windows` and `x86_64-linux`; `aarch64-linux`, `aarch64-macos`, `aarch64-android`, and `aarch64-windows`). [0163 §1; tasks/0784 §562.2, §562.58, §562.200 #4–6, #88–90; SPEC-04 AXS-EXT-052; SPEC-80 AXS-ELFS-002]

**AXS-TGTD-005 — Pointer Width, Endianness, Natural & Stack Alignment (`DataLayout`).** `TargetDesc.data_layout` specifies (`0163 §1, §7`, `tasks/0524 §31–34`, `tasks/0784 §562.173–175, §562.200 #93–95`):
- `pointer_width_bits`: `64` on `X86_64`, `AArch64`, and `Riscv64`; `32` on `Wasm32` (`usize`/`isize`/raw pointers take exact target pointer width and alignment).
- `endian`: `Endian.Little` on all v1 targets (`Endian.Big` modeled explicitly in the schema so `layout_of` and constant folding never assume host endianness).
- `int_align`: natural alignment for `i8`/`u8` (`1`), `i16`/`u16` (`2`), `i32`/`u32` (`4`), `i64`/`u64` (`8`), and `i128`/`u128` (`16`), `f32` (`4`), `f64` (`8`), `v128` (`16`), `v256` (`32`), `v512` (`64`).
- `stack_align`: `16` bytes at call boundaries on `X86_64`, `AArch64`, `Riscv64`, and `Wasm32` linear shadow stack (`REQ-TGT-040`).
- `max_atomic_width_bits`: `64` (`128` when `cx16`/`lse` is enabled), `page_size`: `4096` (`16384` on `aarch64-macos` / `aarch64-android`, `65536` on `wasm32`). [0163 §1, §7; tasks/0524 §31–34; tasks/0784 §562.173–175]

**AXS-TGTD-006 — Independent `ObjectFormat`, `ArchiveFormat` & `ImageFormat` Dimensions.** `TargetDesc` binds `ObjectFormat` (`Coff`, `Elf`, `MachO`, `Wasm`, `SpirV`), `ArchiveFormat` (`CoffAr`, `GnuAr`, `BsdAr`), and `ImageFormat` (`Pe32Plus`, `Pe32PlusDll`, `ElfExec`, `ElfDyn`, `MachO`, `Wasm`, `RawBinary`) independently of `Arch` (`0163 §1, §18–20`, `tasks/0518 AMACHINE-112..115`, `tasks/0524 §108–109`, `tasks/0784 §562.58, §562.200 #5, #87`, `SPEC-04 AXS-EXT-070`, `REQ-TGT-101..104`). Native object emission writes `.obj`/`.o`/`.wasm` bytes directly from encoded Machine IR without invoking an external assembler (`AMACHINE-112, 114`). [0163 §18–20; tasks/0518 AMACHINE-112..115; SPEC-04 AXS-EXT-070; REQ-TGT-101..104]

**AXS-TGTD-007 — Declarative `TargetFeatureSet` Implication DAG Across Architectures.** `TargetDesc` models ISA extensions as a per-architecture directed acyclic implication graph (`Feature A implies Feature B`) stored in a 64-bit `TargetFeatureSet` bitmask (`tasks/0472 §213.1–5, §213.95 AHW-20..22, AHW-24`, `tasks/0518 §38–40`, `tasks/0784 §562.29–34`, `SPEC-44 AXS-CPU-001..002`, `REQ-TGT-004`):
- **`X86_64`:** baseline `{ sse, sse2 }`; optional `sse3` $\leftarrow$ `ssse3` $\leftarrow$ `sse4.1` $\leftarrow$ `sse4.2` $\leftarrow$ `avx` $\leftarrow$ `avx2` $\leftarrow$ `avx512f` $\leftarrow$ `{ avx512bw, avx512dq, avx512vl }`, `fma` ($\rightarrow$ `avx`), `popcnt`, `lzcnt`, `bmi1`, `bmi2`, `aes`, `pclmulqdq`, `sha`, `cx16`, `amx-tile` $\leftarrow$ `{ amx-int8, amx-bf16 }`.
- **`AArch64`:** baseline `{ neon, fp }`; optional `fp16`, `dotprod` ($\rightarrow$ `neon`), `lse`, `crc`, `aes`, `sha2`, `sha3`, `sve` ($\rightarrow$ `neon`) $\leftarrow$ `sve2`, `rcpc`, `pauth`, `bti`.
- **`Riscv64`:** `riscv64gc` baseline `{ m, a, f, d, c }` (`d` $\rightarrow$ `f`, `c` = `rvc`); optional `v` (`rvv` $\rightarrow$ `d`), `zba`, `zbb`, `zbc`, `zbs`, `zbkb`.
- **`Wasm32`:** baseline `{ mutable-globals, sign-ext, nontrapping-fptoint }`; optional `simd128`, `atomics` ($\rightarrow$ `bulk-memory`), `bulk-memory`, `multivalue`, `reference-types`, `tail-call`, `relaxed-simd` ($\rightarrow$ `simd128`). [tasks/0472 §213.1–5, AHW-20..22, AHW-24; tasks/0784 §562.29–34; SPEC-44 AXS-CPU-001..002; REQ-TGT-004]

**AXS-TGTD-008 — Feature Conflict Detection, Explicit Disable Propagation & Baseline Locks.** Enabling `+feat` transitively enables all features reachable along forward `implies` edges; disabling `-feat` transitively disables every feature that directly or transitively implies `feat` (`tasks/0784 §562.31–33`, `SPEC-44 AXS-CPU-003`). Unknown feature names or attempts to disable mandatory target-ABI baseline features (such as `-sse` or `-sse2` on hosted `x86_64`, or `-neon` on hosted `aarch64`) are rejected with `AX_TARGET_UNKNOWN_FEATURE`; mutually exclusive or contradictory feature requests in the same specification emit `AX_TARGET_FEATURE_CONFLICT`. [tasks/0784 §562.31–33, §562.200 #15–19, #138; SPEC-44 AXS-CPU-003]

**AXS-TGTD-009 — Compile-Time Feature Legality Gate & Zero Hidden Runtime Dispatch.** Target CPU features are known explicitly from `TargetDesc` baseline, `--cpu`, `--target-feature`, or function-level `@target_feature` / `@multiversion` annotations (`tasks/0518 §40–43, AMACHINE-65..67`, `tasks/0524 §103–106, ABACKEND-84..85`, `REQ-TGT-004`, `REQ-TGT-054..056`). The compiler never emits an instruction whose `required_features` are not a subset of the active function's `TargetFeatureSet` (`AMACHINE-67`, `ABACKEND-85`), and never silently injects runtime CPU detection or hidden multi-version dispatch into a binary unless `@multiversion` is explicitly written (`AMACHINE-66`). [tasks/0518 AMACHINE-65..67; tasks/0524 ABACKEND-84..85; SPEC-44 AXS-CPU-010..032; REQ-TGT-004, REQ-TGT-054..056]

**AXS-TGTD-010 — CPU Model vs Microarchitectural Tuning Separation.** `TargetDesc` separates `cpu_model` (which determines baseline legal `TargetFeatureSet`) from `tuning_model` (instruction latency, issue throughput, vector width preference, alignment padding, branch heuristics) (`tasks/0518 §35–38, AMACHINE-63..64`, `tasks/0784 §562.35–38, §562.200 #20–22`, `REQ-TGT-052..053`). Both are included in `TargetFingerprint`, and microarchitectural tuning facts never alter observable program semantics (`AMACHINE-63..64`, `REQ-TGT-052..053`). [tasks/0518 AMACHINE-63..64; tasks/0784 §562.35–38; REQ-TGT-052..053]

**AXS-TGTD-011 — Table-Driven `CallConvDesc` ABI Classification Engine (`compiler/abi/table`).** Each `CallConv` is backed by a declarative `CallConvDesc` table in `compiler/abi/table` specifying ordered GPR, FPR/Vector parameter and return register lists, aggregate classification strategy (`Win64PowerOfTwo8`, `SysV64Eightbyte`, `Aapcs64Hfa2Reg`, `RiscvTwoXlen`, `WasmScalarOrIndirect`), hidden `sret` register (`RCX` on `Win64`, `RDI` on `SysV64`, `X8` indirect result location on `Aapcs64`/`WinArm64`, `a0` on `RiscvLp64d`), `shadow_space`, `red_zone`, `stack_align`, `caller_saved_mask`, `callee_saved_mask`, and parallel-move scratch registers (`0163 §5–7`, `tasks/0518 AMACHINE-48..54`, `tasks/0524 ABACKEND-71..72`, `REQ-TGT-037..043`). [0163 §5–7; tasks/0518 AMACHINE-48..54; tasks/0524 ABACKEND-71..72; REQ-TGT-037..043]

**AXS-TGTD-012 — Pre-Compiled Static `TargetDesc` Tables & Zero Runtime Spec Parsing.** All `TargetDesc`, `RegisterFile`, `CallConvDesc`, and `IsaTable` definitions are compiled directly into `axiomc` as deterministic constant tables (`tasks/0784 §562.8–10, §562.196–197, §562.200 #121–127`, `REQ-TGT-005`). Normal compilation never parses external textual ISA description files or invokes third-party backend generators at runtime. [tasks/0784 §562.8–10, §562.196–197; REQ-TGT-005]

---

## 2. Declarative `RegisterFile` Model, `RegUnit` Bitmasks, Aliasing & Register Classes (`AXS-TGTD-013`..`023`)

**AXS-TGTD-013 — Virtual vs Physical Registers & Semantic Variable Separation.** Virtual registers (`vreg`) represent typed SSA/LIR machine values and are strictly distinct from source/MIR semantic variables (`tasks/0518 §5–6, §18, AMACHINE-23..24`, `REQ-TGT-012..013`). Physical register assignment is an internal backend concern (`AMACHINE-24`, `REQ-TGT-013`): a semantic local may live in a virtual register, a physical register, a stack slot, or be scalarized/eliminated without changing source meaning. [tasks/0518 §5–6, §18, AMACHINE-23..24; REQ-TGT-012, REQ-TGT-013]

**AXS-TGTD-014 — Declarative `PhysicalRegDesc` & `RegUnit` Overlap Bitmasks.** `TargetDesc.register_file` defines a static array of `PhysicalRegDesc` entries (`0163 §2–3`, `tasks/0518 §9–11, AMACHINE-26..27`, `tasks/0784 §562.11–12, §562.16, §562.200 #23–25`, `REQ-TGT-015..016`):
- `id: PhysRegId`, `name: Str`, `hw_encoding: u8`, `width_bits: u16`, `reg_class: RegClassId`, `role: RegRole` (`Allocatable | Reserved | Fixed | ZeroReg | FlagsReg`);
- `reg_unit_mask: u128`: bitmask of fundamental architectural register units (`RegUnit`) covered by this register view;
- `super_reg: Option<PhysRegId>`, `sub_regs: [PhysRegId]`, `bit_offset: u16`.
Two physical registers `r1` and `r2` alias (overlap in hardware state) if and only if `(r1.reg_unit_mask & r2.reg_unit_mask) != 0`. The register allocator, liveness analyzer, and `verify_mc` check interference via `reg_unit_mask` bit operations without hard-coding architecture-specific register names. [0163 §2–3; tasks/0518 §9–11, AMACHINE-26..27; tasks/0784 §562.11–12, §562.16; REQ-TGT-015, REQ-TGT-016]

**AXS-TGTD-015 — Explicit Subregister & Superregister Alias Hierarchy Across ISAs.** `RegisterFile` explicitly encodes subregister/superregister hierarchies (`0163 §2–3`, `tasks/0518 §10–11, AMACHINE-26..27`, `tasks/0784 §562.12, §562.41–42, §562.60–61, §562.200 #52, #61, #68`, `REQ-TGT-015..016`):
- **`X86_64` GPRs:** each 64-bit root `RAX..R15` covers two 8-bit low/high units (`AL` bits `[0..8)`, `AH` bits `[8..16)`) plus upper subregister views `AX` (`[0..16)`), `EAX` (`[0..32)`, writing `EAX` implicitly zero-extends `[32..64)` in `RAX`), and `RAX` (`[0..64)`).
- **`X86_64` SIMD:** `ZMMn` (`512`-bit) $\supset$ `YMMn` (`256`-bit) $\supset$ `XMMn` (`128`-bit) for $n \in [0, 31]$.
- **`AArch64` GPRs & FP/SIMD:** `Xn` (`64`-bit) $\supset$ `Wn` (`32`-bit, writing `Wn` zeroes upper 32 bits of `Xn`) for $n \in [0, 30]$; `Vn`/`Qn` (`128`-bit) $\supset$ `Dn` (`64`-bit) $\supset$ `Sn` (`32`-bit) $\supset$ `Hn` (`16`-bit) $\supset$ `Bn` (`8`-bit) for $n \in [0, 31]$.
- **`Riscv64`:** 64-bit `x0..x31` (`GPR64`) and `f0..f31` (`FPR64` $\supset$ `FPR32` NaN-boxed `f32`). [0163 §2–3; tasks/0518 AMACHINE-26..27; tasks/0784 §562.12, §562.41–42, §562.60–61; REQ-TGT-015, REQ-TGT-016]

**AXS-TGTD-016 — Target-Specific `RegisterClass` & Register Bank Definitions.** Each `RegisterFile` declares its `RegisterClass` table mapping abstract LIR register classes (`SPEC-04 AXS-EXT-050`) to physical register sets (`0163 §4`, `tasks/0518 §7–8, AMACHINE-25`, `tasks/0784 §562.13, §562.200 #28`, `REQ-TGT-014`): `GPR64`, `GPR32`, `GPR16`, `GPR8`, `FPR32`, `FPR64` (`XMM`), `Vec128`, `Vec256`, `Vec512`, `Mask` (`k0..k7`), `Pred` (`p0..p15` SVE), `Flags` (`RFLAGS` on `X86_64`, `NZCV` on `AArch64`), and `Special`. [0163 §4; tasks/0518 §7–8, AMACHINE-25; tasks/0784 §562.13; SPEC-04 AXS-EXT-050; REQ-TGT-014]

**AXS-TGTD-017 — Reserved Architectural Registers & Contextual `SP` vs Zero-Register Rules.** `RegisterFile` marks architectural registers that general register allocation must never assign as ordinary storage (`tasks/0784 §562.14–15, §562.62–63, §562.200 #26–29, #62`):
- **`X86_64`:** `RSP` (`Reserved` stack pointer); `RBP` (`Reserved` when frame pointer is enabled, `Allocatable` when omitted).
- **`AArch64`:** `SP` (`Reserved` stack pointer), `XZR`/`WZR` (`ZeroReg`: reads as `0`, writes discard result; never allocatable as storage and strictly distinguished from `SP` by per-operand encoding constraints even though both share hardware encoding `31`), `X18` (`Reserved` platform/TEB register on `aarch64-macos`, `aarch64-windows`, and `aarch64-android`), `X29` (`FP`), and `X30` (`LR` link register, allocatable only if saved in non-leaf frames).
- **`Riscv64`:** `x0` (`ZeroReg` hardwired zero), `ra (x1)` (return address), `sp (x2)` (`Reserved`), `gp (x3)` (`Reserved` global pointer), `tp (x4)` (`Reserved` thread pointer), and `fp/s0 (x8)` (when frame pointer is enabled). [tasks/0784 §562.14–15, §562.62–63, §562.200 #26–29, #62]

**AXS-TGTD-018 — Caller-Saved, Callee-Saved & Scratch Register Partition.** `RegisterFile` and `CallConvDesc` partition allocatable registers into disjoint `caller_saved_mask` (clobbered across `CALL`) and `callee_saved_mask` (preserved across `CALL`; if written by a function body, recorded in `FrameLayout` and saved/restored in prologue/epilogue), plus dedicated `scratch_regs` for parallel-move cycle breaking and large-displacement materialization (`0163 §6`, `tasks/0518 AMACHINE-48..50`, `tasks/0784 §562.16, §562.200 #38`, `REQ-TGT-037..039`). [0163 §6; tasks/0518 AMACHINE-48..50; REQ-TGT-037..039]

**AXS-TGTD-019 — Dual-Tier Register Allocation Contract (`LinearScan` & `Hybrid/Graph`).** `axiomc` provides two target-parameterized register allocators driven purely by `RegisterFile` and `CallConvDesc` tables (`tasks/0518 §96–97`, `SPEC-77 AXS-RA-010..027`, `REQ-TGT-007`, `REQ-TGT-008`, `REQ-TGT-112`):
1. **`LinearScan` (`-O0`, `-O1`):** Fast deterministic sorted live-interval scan handling fixed-register constraints, call clobbers, and `RegUnit` alias masks (`REQ-TGT-007`).
2. **`Hybrid/Graph` (`-O2`, `-Os`, `-Oz`):** Interference-graph coloring with move coalescing, live-range splitting around call sites, and rematerialization (`REQ-TGT-008`). [tasks/0518 §96–97; SPEC-77 AXS-RA-010..027; REQ-TGT-007, REQ-TGT-008, REQ-TGT-112]

**AXS-TGTD-020 — Physical Stack Slots, Spill/Reload Transparency & Non-Overlapping Slot Coloring.** `StackSlot { id, size, align, kind, live_interval }` represents physical frame storage, never a semantic variable (`tasks/0518 §12–18, AMACHINE-28..30, AMACHINE-57`, `tasks/0524 ABACKEND-73..74`, `REQ-TGT-017..019`, `REQ-TGT-046`). Inserting spill stores and reload loads preserves ownership, `Drop`, capability (`view`/`mut_view`), and provenance semantics (`AMACHINE-28, 57`, `ABACKEND-74`, `REQ-TGT-017`, `REQ-TGT-046`). Stack coloring may reuse a physical `StackSlot` for two locals or spills if and only if their physical live intervals are provably non-overlapping and no live pointer/view alias crosses the boundary (`AMACHINE-30`, `REQ-TGT-019`). [tasks/0518 §12–18, AMACHINE-28..30, AMACHINE-57; tasks/0524 ABACKEND-73..74; REQ-TGT-017..019, REQ-TGT-046]

**AXS-TGTD-021 — Target Addressing Modes & Core Semantic Isolation.** Machine memory operands obey per-target `AddrModeDesc` constraints in `TargetDesc` while keeping `LIR` address expressions target-independent (`0163 §9`, `tasks/0518 §19–23, AMACHINE-31..32`, `tasks/0524 §35–40, ABACKEND-76..77`, `tasks/0784 §562.44–45, §562.64`, `REQ-TGT-020..021`):
- `X86_64`: `[base + index * scale + disp32]` with `scale` $\in \{1, 2, 4, 8\}$ (`RSP` forbidden as `index`) or `[RIP + disp32]`.
- `AArch64`: `[base, #simm9]` unscaled, `[base, #uimm12 * access_size]` unsigned scaled, `[base, Xm/Wm, extend #shift]`, and pre-/post-indexed `[base, #simm9]!` / `[base], #simm9` (`base` is `Xn` or `SP`, never `XZR`).
- `Riscv64`: `[rs1 + simm12]`.
- `Wasm32`: linear memory dynamic `base_i32` + static unsigned `u32` offset immediate (`align` hint $\le$ natural alignment).
Target addressing modes never leak into Core language semantics (`AMACHINE-32`, `ABACKEND-77`, `REQ-TGT-020..021`). [0163 §9; tasks/0518 §19–23, AMACHINE-31..32; tasks/0524 §35–40, ABACKEND-76..77; REQ-TGT-020, REQ-TGT-021]

**AXS-TGTD-022 — Value-Stack & Typed-Local Execution Model for Stack Targets (`Wasm32`).** `Wasm32` is not forced into a fake physical CPU register file (`tasks/0518 AMACHINE-90`, `tasks/0524 §28–29, §42–43, ABACKEND-79`, `tasks/0784 §562.200 #71–75`). Its `RegisterFile` declares virtual-to-typed-local (`i32`, `i64`, `f32`, `f64`, `v128`) and operand-stack lowering plus structured control-flow (`block`/`loop`/`if`/`br`/`br_if`/`br_table`) purely as backend representations of the same `LIR` semantics (`ABACKEND-79`). [tasks/0518 AMACHINE-90; tasks/0524 §28–29, §42–43, ABACKEND-79; tasks/0784 §562.200 #71–75]

**AXS-TGTD-023 — Structural Verification of `RegisterFile` Invariants.** On compiler startup and in `tests/run/target_desc` (`T654`), `compiler/target/desc` validates every registered `TargetDesc.register_file`: (1) every storage register has `reg_unit_mask != 0`; (2) subregister `reg_unit_mask` is a strict or non-strict subset of its `super_reg.reg_unit_mask`; (3) alias queries are symmetric (`aliases(a, b) == aliases(b, a)`); (4) `allocatable_mask & reserved_mask == 0`; and (5) `caller_saved_mask & callee_saved_mask == 0`. [tasks/0784 §562.11–16, §562.200 #23–29; T654]

---

## 3. Declarative `IsaTable`, Pattern-Based Instruction Selection, `Legalizer` & `verify_mc` (`AXS-TGTD-024`..`038`)

**AXS-TGTD-024 — Declarative `IsaTable` & `InstrDesc` Schema (`compiler/target/isa`).** Each target ISA declares a static `IsaTable` of `InstrDesc` entries (`tasks/0518 §34, AMACHINE-46..47`, `tasks/0784 §562.6–10, §562.17–28, §562.200 #8, #30–35`, `REQ-TGT-035..036`):
- `opcode: OpcodeId`, `mnemonic: Str`, `semantic_op: Option<LirOp>`;
- `operands: [OperandConstraint]` (explicit register/immediate/memory/label operands with def/use direction);
- `implicit_uses_mask: u128`, `implicit_defs_mask: u128` (physical `RegUnit` masks read or clobbered implicitly);
- `effect_flags: InstrEffectFlags` (`ReadReg`, `WriteReg`, `ReadMem`, `WriteMem`, `ReadFlags`, `WriteFlags`, `Call`, `Return`, `Branch`, `CondBranch`, `IndirectBranch`, `Trap`, `Atomic`, `Volatile`, `Barrier`, `SideEffect`);
- `required_features: TargetFeatureSet`, `encoding: EncodingForm`, `sched_class: SchedClassId` (`latency`, `throughput`, `size_bytes`). [tasks/0518 §34, AMACHINE-46..47; tasks/0784 §562.17–28; REQ-TGT-035, REQ-TGT-036]

**AXS-TGTD-025 — Operand Constraints, Immediate Predicates & Tied Operands.** `OperandConstraint` specifies per-operand legality predicates validated by instruction selection and `verify_mc` (`tasks/0784 §562.19–21, §562.51, §562.64, §562.200 #14, #57, #64`):
- `RegClass(RegClassId, AccessDir)` (`Use`, `Def`, `UseDef`), `FixedPhysReg(PhysRegId, AccessDir)`, `TiedDefUse(def_idx, use_idx)` (for destructive 2-operand x86 instructions where destination and first source must share a physical register);
- `ImmSigned(bits)` ($[-2^{\text{bits}-1}, 2^{\text{bits}-1}-1]$), `ImmUnsigned(bits)` ($[0, 2^{\text{bits}}-1]$), `ImmShifted(bits, shift)`, `AArch64LogicalImm` (bitmask immediate), `MemAddr(AddrModeKind)`, `RelocSym(RelocKind)`, `CondCode`. [tasks/0784 §562.19–21, §562.51, §562.64]

**AXS-TGTD-026 — Explicit Implicit Register Uses/Defs & Call Clobber Modeling.** Every instruction with fixed architectural register dependencies declares them in `implicit_uses_mask` and `implicit_defs_mask` (`tasks/0518 AMACHINE-46, 48`, `tasks/0784 §562.17–18, §562.43`, `REQ-TGT-035`, `REQ-TGT-037`):
- `X86_64`: `IDIV`/`DIV`/`MUL` implicitly read/write `RAX` and `RDX`; variable shifts (`SHL`/`SHR`/`SAR`/`ROL`/`ROR` by `vreg`) implicitly read `RCX` (`CL`); `CQO`/`CDQ` implicitly read `RAX` and write `RDX`; string ops (`REP MOVSB`/`STOSB`) implicitly use/def `RDI`, `RSI`, `RCX`; `SYSCALL` implicitly reads `RAX` and clobbers `RCX`, `R11`.
- Every `CALL` instruction carries the callee `CallConvDesc.caller_saved_mask` (including volatile vector and flags registers) as its explicit call-clobber set (`AMACHINE-48`, `REQ-TGT-037`). [tasks/0518 AMACHINE-46, 48; tasks/0784 §562.17–18, §562.43; REQ-TGT-035, REQ-TGT-037]

**AXS-TGTD-027 — Condition-Code Modeling Across Flags-Based and Flagless ISAs.** `LIR` represents comparisons abstractly as `LirCmp { pred: CmpPred, lhs, rhs } -> CondValue` without assuming a hardware flags register (`tasks/0518 §30–33, AMACHINE-47, 62`, `tasks/0524 §23–27`, `tasks/0784 §562.43, §562.60, §562.200 #53, #63`, `REQ-TGT-036`, `REQ-TGT-051`):
- **Flags-based ISAs (`X86_64`, `AArch64`):** `CMP`/`TEST`/`SUBS`/`FCMP` declare `WriteFlags` (`implicit_defs = RFLAGS` or `NZCV`), and `Jcc`/`SETcc`/`CMOVcc`/`B.cond`/`CSEL`/`CSINC` declare `ReadFlags` (`implicit_uses = RFLAGS` or `NZCV`). Neither instruction scheduling nor peephole passes may insert a flag-clobbering instruction (`WriteFlags`) between a flag producer and its consumer while `Flags` is live (`AMACHINE-47, 62`, `REQ-TGT-036`, `REQ-TGT-051`).
- **Flagless / Register-Branch ISAs (`Riscv64`, `Wasm32`):** `Riscv64` lowers comparisons directly to compare-and-branch (`beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu`) or GPR boolean set (`slt`, `sltu`, `feq.d`, `flt.d`); `Wasm32` lowers comparisons to `i32` stack boolean ops (`i32.eq`, `i64.lt_s`, `f64.lt`) consumed by `if`/`br_if`/`select`. [tasks/0518 §30–33, AMACHINE-47, 62; tasks/0524 §23–27; REQ-TGT-036, REQ-TGT-051]

**AXS-TGTD-028 — Pattern-Based Instruction Selection Contract.** Instruction selection (`compiler/target/isa` + per-target selectors) uses declarative pattern matching (`LIR` single-instruction and multi-node tree/DAG patterns such as `load(add(base, scale * idx + disp))`, `add(x, shl(y, k))`, compare-and-branch fusion) guarded by operand/immediate/feature predicates and ordered by pattern complexity/cost (`tasks/0518 §45–50, AMACHINE-33..34`, `tasks/0524 §20–22, ABACKEND-63, 80`, `REQ-TGT-006`, `REQ-TGT-022..023`). Instruction selection is target-specific (`AMACHINE-33`, `REQ-TGT-022`) and must preserve the exact semantic contract of the input `LIR` (`AMACHINE-34`, `ABACKEND-63`, `REQ-TGT-023`, `REQ-TGT-288`). [tasks/0518 §45–50, AMACHINE-33..34; tasks/0524 §20–22, ABACKEND-63; REQ-TGT-006, REQ-TGT-022, REQ-TGT-023, REQ-TGT-288]

**AXS-TGTD-029 — Target `Legalizer` Action Table (`Legal`, `Expand`, `Promote`, `Scalarize`, `Reject`).** Before instruction selection, the target legalizer (`compiler/target/isa`) classifies every `(LirOp, LirType, TargetFeatureSet)` tuple into a deterministic `LegalizeAction` (`tasks/0518 §51–55, AMACHINE-35`, `tasks/0524 §17–19, §101–103, ABACKEND-64..65`, `REQ-TGT-006`, `REQ-TGT-024`, `REQ-TGT-289..290`):
1. `Legal`: directly supported by at least one `InstrDesc` enabled under the active `TargetFeatureSet`.
2. `Promote(wider_type)`: narrow integer (`i8`/`i16`) operation widened with explicit sign/zero extension or mask truncation preserving exact width overflow/wrap behavior.
3. `Expand(ExpansionRule)`: multi-instruction sequence (e.g., `i128`/`u128` into `64`-bit limb pairs `ADD`+`ADC` / `SUB`+`SBB` / `ADDS`+`ADC`, or `64`-bit shifts/mul/div on 32-bit targets).
4. `Scalarize` / `SplitVector`: wide SIMD vector (`v256`/`v512`) split into legal `v128` halves or scalar lanes when wider vector features are disabled (`SPEC-43 AXS-SBE-004`).
5. `Reject`: operation cannot be legally realized on the target/profile; rejected at compile time with `AX_TARGET_UNSUPPORTED_OP` (`ABACKEND-65, 96`). [tasks/0518 §51–55, AMACHINE-35; tasks/0524 §17–19, §101–103, ABACKEND-64..65; REQ-TGT-006, REQ-TGT-024, REQ-TGT-289, REQ-TGT-290]

**AXS-TGTD-030 — Overflow-Faithful Integer Legalization.** Legalization of `LIR` integer operations preserves the five distinct numeric families (`checked`, `wrapping`, `saturating`, `overflowing`, `exact div/rem`) (`tasks/0518 §28–29, §51–54, AMACHINE-36`, `SPEC-40 AXS-INT-006..013`, `REQ-TGT-025`). When expanding 128-bit checked addition/subtraction/multiplication or signed `MIN / -1` division on any target, the expanded sequence computes the exact 128-bit overflow predicate and branches to the deterministic panic/trap handler (`AMACHINE-36, 40`, `REQ-TGT-025`, `REQ-TGT-029`). [tasks/0518 §28–29, §51–54, AMACHINE-36, 40; SPEC-40 AXS-INT-006..013; REQ-TGT-025, REQ-TGT-029]

**AXS-TGTD-031 — Strict IEEE-754 Floating-Point Preservation & Explicit `@fast_math` Authorization.** By default, `LIR` and `Machine IR` enforce strict IEEE-754 binary32/binary64 semantics (`tasks/0518 §25–27, AMACHINE-41..42`, `tasks/0784 §562.172, §562.200 #155–159`, `SPEC-41 AXS-FLT-010..016`, `REQ-TGT-030..031`). Instruction selection and legalization never fuse `a * b + c` into hardware `FMA`, never reassociate FP additions, and never drop signed-zero (`-0.0`) or `NaN` propagation unless explicitly authorized by `@fast_math` or an explicit `std.math.fma` intrinsic (`AMACHINE-41..42`, `REQ-TGT-030..031`). Saturating `FloatToInt` casts expand on all targets to explicit `NaN -> 0` and `[T.MIN, T.MAX]` clamping sequences (`SPEC-41 AXS-FLT-022`). [tasks/0518 §25–27, AMACHINE-41..42; SPEC-41 AXS-FLT-010..022; REQ-TGT-030, REQ-TGT-031]

**AXS-TGTD-032 — Atomic, Volatile & Memory-Ordering Preservation in Legalization.** Legalization and instruction selection preserve `Atomic`, `Volatile`, and `Synchronize` (`Fence`) effects (`tasks/0518 §54–55, AMACHINE-37..39, AMACHINE-43..45`, `tasks/0524 §10–14, §18–19, ABACKEND-66..68`, `REQ-TGT-026..028`, `REQ-TGT-032..034`, `REQ-TGT-291..293`):
- Atomic operations are lowered to architecture-compliant atomic sequences (`X86_64` `LOCK XADD`/`LOCK CMPXCHG`/`XCHG`/`MFENCE`; `AArch64` `LDAR`/`STLR`/`LDAXR`+`STLXR` or `LSE` `LDADD`/`CAS`/`SWP` + `DMB ISH`; `Riscv64` `lr.d`/`sc.d`/`amo*.d` + `fence`; `Wasm32` `i32.atomic.*`/`i64.atomic.*` when `+atomics` is enabled).
- Unsupported atomic widths or targets without atomic support are either legally expanded via a lock-free/runtime atomic protocol that preserves happens-before semantics or rejected at compile time with `AX_TARGET_UNSUPPORTED_OP` — **never** silently lowered to ordinary non-atomic loads or stores (`AMACHINE-43`, `ABACKEND-66`, `REQ-TGT-032`, `REQ-TGT-291`).
- `Volatile` loads and stores (`MIR_STMT_VOLATILE_*` / `LIR` `MEM_FLAG_VOLATILE`) carry `InstrEffectFlags.Volatile` in Machine IR and are never eliminated, coalesced, duplicated, or reordered across volatile/atomic/call barriers (`AMACHINE-38, 44`, `ABACKEND-67`, `REQ-TGT-027`, `REQ-TGT-033`, `REQ-TGT-292`). [tasks/0518 AMACHINE-37..39, AMACHINE-43..45; tasks/0524 §10–14, §18–19, ABACKEND-66..68; REQ-TGT-026..028, REQ-TGT-032..034, REQ-TGT-291..293]

**AXS-TGTD-033 — Explicit `TrapBehavior` Modeling & Panic vs Hardware-Trap Separation.** Every `LIR` and `Machine IR` operation carries an explicit `TrapBehavior = Never | DefinedTrap | TargetTrapMapped | Panic | Unreachable` (`tasks/0518 AMACHINE-40`, `tasks/0524 §15–16, ABACKEND-69..70`, `REQ-TGT-029`, `REQ-TGT-294..295`). Target hardware traps (such as x86 `IDIV` `#DE` on `INT_MIN / -1` or division by zero, AArch64 `UDIV` returning `0` on division by zero, RISC-V division returning `-1`, or WASM `unreachable` / integer divide trap) have ISA-divergent behavior and **must never** silently replace an Axiom `Panic` contract (`ABACKEND-70`, `REQ-TGT-295`). Checked division/remainder and bounds/overflow checks always emit explicit pre-check branches to the Axiom panic handler before any trapping hardware instruction executes (`AMACHINE-40`, `REQ-TGT-029`, `REQ-TGT-294..295`). [tasks/0518 AMACHINE-40; tasks/0524 §15–16, ABACKEND-69..70; REQ-TGT-029, REQ-TGT-294, REQ-TGT-295]

**AXS-TGTD-034 — Phi Elimination, Critical-Edge Splitting & Machine Scheduling Preservation.** Machine SSA phi elimination splits critical CFG edges where required and lowers phi nodes via topological parallel-copy resolution (`tasks/0518 AMACHINE-55..56`, `tasks/0524 ABACKEND-78`, `REQ-TGT-044..045`). Pre- and post-RA instruction scheduling (`compiler/opt/mc_sched`) builds a DAG enforcing true (`RAW`), anti (`WAR`), and output (`WAW`) register dependencies (`REQ-TGT-047`), alias-aware memory dependencies (`REQ-TGT-048`), `Atomic`/`Volatile`/`Barrier` ordering (`REQ-TGT-049`), `Call` side effects and ABI clobbers (`REQ-TGT-050`), and `Flags`/condition-code dependencies (`REQ-TGT-051`). [tasks/0518 AMACHINE-55..62; tasks/0524 ABACKEND-78; REQ-TGT-044..051]

**AXS-TGTD-035 — Shared `IsaTable` Encoder/Decoder Consistency (`decode(encode(I)) == I`).** The machine encoder and internal disassembler/decoder consume the same declarative `IsaTable` encoding bit-field descriptors (`tasks/0784 §562.22–28, §562.183, §562.200 #8–12, #119–120`). Every legal `MachineInstr` has a deterministic byte encoding (`REQ-TGT-059`), and decoding the emitted bytes reconstructs the canonical `MachineInstr` (`decode(encode(I)) == I`). [tasks/0784 §562.22–28, §562.183, §562.200 #8–12]

**AXS-TGTD-036 — Mandatory Pre-Encoding Machine IR Verifier (`compiler/backend/verify_mc`).** `Machine IR` is the final compiler abstraction before binary encoding (`AMACHINE-120`, `REQ-TGT-109`). `compiler/backend/verify_mc` executes as a mandatory verification gate immediately before instruction encoding and object emission on every target (`tasks/0518 §130–131, AMACHINE-68..69, AMACHINE-119..120`, `tasks/0524 ABACKEND-81`, `tasks/0784 §562.182, §562.200 #129`, `SPEC-04 AXS-EXT-053..054`, `REQ-TGT-057..058`, `REQ-TGT-108..109`). Invalid `Machine IR` never reaches the binary encoder (`AMACHINE-69`, `REQ-TGT-058`). [tasks/0518 §130–131, AMACHINE-68..69, AMACHINE-119..120; tasks/0524 ABACKEND-81; REQ-TGT-057..058, REQ-TGT-108..109]

**AXS-TGTD-037 — Ten Structural & Semantic Invariants Enforced by `verify_mc`.** `compiler/backend/verify_mc` verifies every `MachineFunction` against `TargetDesc`, `RegisterFile`, `CallConvDesc`, and `IsaTable` (`tasks/0518 §130`, `tasks/0784 §562.182`, `T655`):
1. **Zero unallocated virtual registers:** No `Reg.is_virtual == true` remains in any post-RA instruction operand or memory address.
2. **Opcode & operand arity:** Every instruction's `opcode` exists in the target's `IsaTable` with exact operand count and directions (`Use`/`Def`/`UseDef`).
3. **Register class, fixed-register & tied-operand legality:** Every register operand belongs to the required `RegClassId`, matches `FixedPhysReg` constraints, and satisfies `TiedDefUse(def_idx, use_idx)`.
4. **Reserved & zero-register discipline:** No instruction illegally writes to a `Reserved` register or mistakes `SP` for `XZR` where the `IsaTable` operand constraint forbids `SP` or `XZR`.
5. **Immediate & addressing-mode bounds:** Every immediate satisfies `ImmSigned`/`ImmUnsigned`/`ImmShifted` bit-width predicates, and every `MemoryOperand` satisfies the target's `AddrModeDesc` (`scale` $\in \{1, 2, 4, 8\}$, `index != RSP`, aligned scaled offsets on `AArch64`, `simm12` on `Riscv64`).
6. **Target feature availability:** For every instruction, `(instr.required_features & ~fn_enabled_features) == 0` (`AMACHINE-67`, `ABACKEND-85`).
7. **Zero unexpanded pseudo-ops:** No pre-legalization or abstract ABI placeholder pseudo-instruction remains at the pre-encoding boundary (`AMACHINE-35`).
8. **Implicit-register & condition-code liveness:** Every `ReadFlags` or implicit register use is dominated by a valid definition without an intervening clobber (`AMACHINE-46..47`).
9. **ABI frame, callee-saved & call-site stack alignment:** `FrameLayout` saves and restores every modified register in `callee_saved_mask` (`AMACHINE-49`), and at every `CALL` instruction `(frame_stack_delta % target.stack_align) == 0` (`AMACHINE-51`).
10. **CFG & stack-probe completeness:** Every basic block ends with a valid terminator targeting an in-range block/symbol, and frames allocating `>= 4096` bytes include the required stack probe sequence (`ADR-0003`). [tasks/0518 §130, AMACHINE-35, 46..51, 67..69; tasks/0784 §562.182; ADR-0003; REQ-TGT-057..058, REQ-TGT-108..109]

**AXS-TGTD-038 — Distinguishing User Target Diagnostics from Internal `verify_mc` Failures.** User-facing target configuration or source-feature errors (unknown `--target`, unknown/conflicting `--target-feature`, unguarded `@target_feature` call, or source use of an operation unsupported by the selected target profile) report structured `AX_DRIVER_*` or `AX_TARGET_*` diagnostics with exit code `1` or `2` (`tasks/0518 AMACHINE-101`, `tasks/0524 §100, ABACKEND-96`, `tasks/0784 §562.155–156`, `REQ-TGT-090`). When hand-written or deserialized Machine IR in a verifier test (`tests/mc/isa_table`, `T655`/`T656`) violates `verify_mc`, the verifier reports `AX_VERIFY_MC_ILLEGAL` (carrying `data.rule`, `data.opcode`, `data.detail`); when compiler-generated Machine IR violates `verify_mc` during normal compilation, the compiler reports `AX_ICE_INTERNAL` (`data.stage = "mc_verify"`, exit code `3`) and writes no output artifact (`spec/diagnostics.md AXD-042`). [tasks/0518 AMACHINE-101; tasks/0524 §100, ABACKEND-96; spec/diagnostics.md AXD-042; REQ-TGT-090]

---

## 4. Target-Independent LIR Semantics & Backend Conformance Contract (`AXS-TGTD-039`..`049`)

**AXS-TGTD-039 — Three-Level Backend Semantic Architecture & Axiom LIR as Portability Boundary.** Axiom's native compilation pipeline enforces a strict three-tier semantic boundary (`tasks/0518 AMACHINE-20..22`, `tasks/0524 §1–3, §111–113, ABACKEND-61..62, ABACKEND-99..100`, `REQ-TGT-009..011`, `REQ-TGT-285..287`):
$$\text{Verified MIR / OptIR} \longrightarrow \text{Axiom LIR (Semantic Portability Boundary)} \longrightarrow \text{Target Machine IR} \longrightarrow \text{Target Object / Image}$$
1. `Machine IR` is derived exclusively from `Verified MIR` via `Axiom LIR` (`AMACHINE-20`, `REQ-TGT-009`).
2. `Axiom LIR` is the canonical semantic portability boundary of the native compiler (`ABACKEND-99`): LIR contains zero ISA-specific opcodes (no `LIR.ADD_X86`, `LIR.ADC_ARM`, or `LIR.AMO_RV`, `tasks/0524 §3`).
3. Target backends are free to select any legal target instruction sequence, register assignment, and physical layout, but are **never** free to alter observable LIR semantics (`AMACHINE-21..22`, `ABACKEND-61..62, 88..89, 100`, `REQ-TGT-010..011`, `REQ-TGT-285..287`). No target backend is permitted to act as a second semantic compiler (`ABACKEND-100`). [tasks/0518 AMACHINE-20..22; tasks/0524 §1–3, §111–113, ABACKEND-61..62, ABACKEND-99..100; REQ-TGT-009..011, REQ-TGT-285..287]

**AXS-TGTD-040 — Common `TargetBackend` Stage Pipeline Contract.** Every target backend implements the unified compiler-internal `TargetBackend` pipeline contract (`tasks/0518 §132, AMACHINE-92, 120`, `tasks/0524 §4`, `tasks/0784 §562.1, §562.183`):
`target_desc() -> lower_abi() -> legalize() -> select_isel() -> eliminate_phi() -> regalloc() -> lower_frame() -> schedule_and_peephole() -> relax_branches() -> verify_mc() -> encode() -> emit_object()`. [tasks/0518 §132, AMACHINE-92; tasks/0524 §4; tasks/0784 §562.1, §562.183]

**AXS-TGTD-041 — Explicit LIR `OperationContract` Schema.** Every `Axiom LIR` operation is governed by a formal `OperationContract { inputs, outputs, types, effects, memory_ordering, alignment, trap_behavior, legality }` (`tasks/0524 §7–16, ABACKEND-61`). Any target lowering, legalizer expansion, instruction selection pattern, register spill, or machine peephole rewrite is valid if and only if it preserves the operation's `OperationContract` across all valid inputs (`ABACKEND-61..80`). [tasks/0524 §7–16, ABACKEND-61..80; REQ-TGT-286, REQ-TGT-287]

**AXS-TGTD-042 — Independent Stage Serialization & Stage-Isolated Testing (`AMACHINE-96..99`).** `axiomc inspect` exposes deterministic textual/JSON serialization for every backend boundary (`tasks/0518 §124–129, §143, AMACHINE-96..99`, `tasks/0784 §562.160–164`, `REQ-TGT-085..088`):
- `inspect --emit=target-desc` and `inspect --emit=isa-table`: dump `TargetDesc`, `RegisterFile` (`RegUnit` masks, aliases, classes), `CallConvDesc`, and `IsaTable` descriptors.
- `inspect --emit=lir`: dumps target-lowered/legalized `LIR` (`REQ-TGT-085`).
- `inspect --emit=mc`: dumps pre-RA and post-RA `Machine IR` (`REQ-TGT-085`), enabling independent unit tests for instruction selection (`AMACHINE-97`, `REQ-TGT-086`), register allocation across multiple `RegisterFile` descriptions (`AMACHINE-98`, `tasks/0784 §562.164`, `REQ-TGT-087`), and instruction encoding/decoding round-trips (`AMACHINE-99`, `REQ-TGT-088`). [tasks/0518 §124–129, §143, AMACHINE-96..99; tasks/0784 §562.160–164; REQ-TGT-085..088]

**AXS-TGTD-043 — Assembly Golden Files Are Quality Tests, Never Semantic Authority (`ABACKEND-90`).** Textual assembly emission (`inspect --emit=asm`) is an optional diagnostic and code-quality inspection view (`tasks/0518 AMACHINE-113..114`, `tasks/0524 §87, ABACKEND-88..90`, `REQ-TGT-102..103`). Assembly golden tests verify instruction selection quality, ABI register usage, and code size, but are **not** the semantic authority (`ABACKEND-90`): two backends or optimization levels emitting different instruction sequences that produce identical observable behavior are both semantically conformant (`ABACKEND-88..89`, `AMACHINE-118`, `REQ-TGT-107`). [tasks/0518 AMACHINE-113..114, 118; tasks/0524 §87, ABACKEND-88..90; REQ-TGT-102, REQ-TGT-103, REQ-TGT-107]

**AXS-TGTD-044 — Differential Reference Execution & Common Cross-Target Conformance Suites (`ABACKEND-91..93`).** Machine backend conformance is a mandatory requirement of compiler correctness (`AMACHINE-100`, `REQ-TGT-089`). Every supported target backend must pass the common target-independent semantic conformance suites (covering scalar/128-bit/float arithmetic, overflow panics, structs/enums/pattern matching, ownership, `view`/`mut_view` capabilities, deterministic `Drop`, closures, generics/`dyn Trait`, atomics, and concurrency) and produce identical observable exit codes and stdout to the MIR interpreter oracle `--interp` (`tasks/0518 §126, AMACHINE-100`, `tasks/0524 §81–86, ABACKEND-91..93`, `tasks/0784 §562.169–170`, `REQ-TGT-089`, `REQ-TGT-286`). [tasks/0518 §126, AMACHINE-100; tasks/0524 §81–86, ABACKEND-91..93; REQ-TGT-089, REQ-TGT-286]

**AXS-TGTD-045 — Optimization Profile Semantic Invariance (`-O0`, `-O1`, `-O2`, `-Os`, `-Oz`).** Compilation profiles for debug (`-O0`), speed (`-O1`, `-O2`), and code size (`-Os`, `-Oz`) may alter register allocation tier, instruction selection patterns, loop unrolling, vectorization, inline thresholds, and code alignment padding, but must **never** alter observable language semantics or weaken safety/bounds/overflow checks (`tasks/0518 §139–141, AMACHINE-103..106, AMACHINE-118`, `tasks/0524 §88–89, ABACKEND-86..87`, `REQ-TGT-092..095`, `REQ-TGT-107`). [tasks/0518 §139–141, AMACHINE-103..106, AMACHINE-118; tasks/0524 §88–89, ABACKEND-86..87; REQ-TGT-092..095, REQ-TGT-107]

**AXS-TGTD-046 — Inspectable Machine Explanations & Non-Overridable Verification (`AMACHINE-102`).** `axiomc inspect --emit=mc-explain` emits structured machine decision provenance (instruction selection pattern reason, required target feature, register spill pressure count vs available registers, branch relaxation distance) tagged with `EvidenceKind = Fact | CostModelDecision | Heuristic` (`tasks/0518 §144–146, AMACHINE-102`, `tasks/0784 §562.157–158`, `REQ-TGT-091`). AI agents and developer tools may inspect these explanations, but no external hint or tool may override or bypass `verify_mc` (`AMACHINE-102`, `REQ-TGT-091`). [tasks/0518 §144–146, AMACHINE-102; tasks/0784 §562.157–158; REQ-TGT-091]

**AXS-TGTD-047 — Reproducible Deterministic Backend Compilation.** For a fixed source snapshot, `TargetFingerprint`, and optimization profile, all backend stages (`lower_abi`, `legalize`, `select_isel`, `regalloc`, `schedule`, `encode`, `emit_object`) are purely deterministic functions producing byte-identical machine code and object artifacts (`tasks/0518 AMACHINE-70, 117`, `tasks/0524 §90, ABACKEND-95`, `tasks/0784 §562.153–154`, `REQ-TGT-059`, `REQ-TGT-106`). Randomized register-allocation or instruction-scheduling stress testing requires an explicit `--mc-fuzz-seed <u64>` flag and is never active in production builds (`tasks/0784 §562.154, §562.200 #118`). [tasks/0518 AMACHINE-70, 117; tasks/0524 §90, ABACKEND-95; tasks/0784 §562.153–154; REQ-TGT-059, REQ-TGT-106]

**AXS-TGTD-048 — Cross-Target Semantic Reuse & Zero Core Drift When Adding Targets.** Adding a new target ISA or OS platform requires adding its declarative `TargetDesc`, `RegisterFile`, `CallConvDesc`, `IsaTable`, and target hooks without modifying the lexer, parser, name resolver, type checker, ownership/capability analyzer, trait solver, or MIR verifier (`tasks/0524 ABACKEND-97..98`, `tasks/0784 §562.146–151, §562.198–199, §562.200 #7, #180–184, #197`). [tasks/0524 ABACKEND-97..98; tasks/0784 §562.198–199, §562.200 #7, #180–184, #197]

**AXS-TGTD-049 — Self-Hostable Pure-Axiom Backend Implementation Without LLVM/GCC/Clang.** All `TargetDesc`, `RegisterFile`, `IsaTable`, legalizer, register allocator, `verify_mc`, encoder, and object-writer modules in `compiler/` are implemented in pure safe/system Axiom without depending on LLVM, GCC, Clang, or external assemblers (`tasks/0518 AMACHINE-93..95`, `tasks/0784 §562.200 #123–128`, `REQ-TGT-005`, `REQ-TGT-082..084`). [tasks/0518 AMACHINE-93..95; tasks/0784 §562.200 #123–128; REQ-TGT-005, REQ-TGT-082..084]

---

## 5. Diagnostics, Canonical Examples & Traceability (`AXS-TGTD-050`..`053`)

**AXS-TGTD-050 — Diagnostics Referenced or Introduced by `SPEC-81`.** `SPEC-81` uses the canonical `DRIVER`, `TARGET`, `VERIFY`, `LINK`, and `ICE` diagnostic codes (`spec/diagnostics.md` §10–11):

| Code | Area | Sev | Delivering Task | Condition |
|---|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | `T016`/`T654` | Unknown `--target <triple>` outside the canonical `TargetId` registry (`AXS-TGTD-002`) |
| `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | `error` | `T476`/`T654` | Unknown CPU feature name or forbidden baseline feature removal (e.g. `-sse2` on `x86_64` or `-neon` on hosted `aarch64`) (`AXS-TGTD-007..008`) |
| `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | `error` | `T654` | Mutually exclusive or contradictory target features requested in `--target-feature` or `@target_feature` (`AXS-TGTD-008`) |
| `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | `error` | `T476`/`T654` | Calling a `@target_feature` function or target-gated intrinsic without enabling the required feature in `TargetFeatureSet` (`AXS-TGTD-009`) |
| `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | `error` | `T655` | `LIR` operation, atomic width, or ABI convention cannot be legally expanded on the selected target/profile without violating semantics (`AXS-TGTD-029`, `AXS-TGTD-032`) |
| `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | `error` | `T655` | Hand-written or deserialized Machine IR in a verifier test violates `verify_mc` invariants (unallocated `vreg`, wrong `RegClass`, illegal reserved-register write, missing target feature, unexpanded pseudo-op, or misaligned `CALL` frame) (`AXS-TGTD-036..038`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `T766`/`T654` | `TargetFingerprint`, `Arch`, `Endian`, pointer width, or `CallConv` in an input `.axmi`/`.obj`/`.o` mismatches the active target (`AXS-TGTD-003`) |
| `AX_ICE_INTERNAL` (`stage = "mc_verify"`) | `ICE` | `error` | `T025b`/`T655` | Compiler-generated Machine IR failed `verify_mc` before encoding (exits with code `3` and writes no artifact, `AXS-TGTD-038`) |

**AXS-TGTD-051 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Declarative TargetDesc, RegisterFile RegUnit aliasing, and CallConvDesc query
// Verified in: tests/run/target_desc (T654)
module demo.target_desc_query

pub struct RegDesc {
    pub id: u16,
    pub width_bits: u16,
    pub unit_mask: u64,
    pub is_reserved: bool,
}

pub fn regs_alias(a: view<RegDesc>, b: view<RegDesc>) -> bool {
    return (a.unit_mask & b.unit_mask) != 0u64
}

pub fn accumulate_checked(items: view<[i64]>, scale: i64) -> i64 {
    let mut total: i64 = 0
    let mut i: usize = 0
    while i < len(items) {
        // Lowered through target-independent LIR (checked mul + checked add);
        // x86-64, AArch64, RISC-V, and WASM backends select native instructions
        // while preserving identical overflow-panic semantics (AXS-TGTD-030, AXS-TGTD-039).
        total = total + (items[i] * scale)
        i = i + 1
    }
    return total
}

pub fn main() -> i32 {
    // RAX covers units 0b11 (AL=0b01, AH=0b10); EAX covers 0b11; RBX covers 0b1100.
    let rax = RegDesc { id = 0u16, width_bits = 64u16, unit_mask = 3u64, is_reserved = false }
    let eax = RegDesc { id = 1u16, width_bits = 32u16, unit_mask = 3u64, is_reserved = false }
    let rbx = RegDesc { id = 2u16, width_bits = 64u16, unit_mask = 12u64, is_reserved = false }
    if !regs_alias(view(rax), view(eax)) {
        return 1
    }
    if regs_alias(view(rax), view(rbx)) {
        return 2
    }
    let data: [4]i64 = [3, 4, 5, 9]
    if accumulate_checked(view(data), 2) == 42 {
        return 0
    }
    return 3
}
```

```axiom
// Example 2: Explicit @target_feature gating and mut_view preservation across calls (AXS-TGTD-009, AXS-TGTD-020)
module demo.target_feature_gate

@target_feature("avx2")
pub fn add_lanes_avx2(dst: mut_view<[i32]>, src: view<[i32]>) {
    let mut i: usize = 0
    while i < len(dst) && i < len(src) {
        dst[i] = dst[i] + src[i]
        i = i + 1
    }
}

pub fn main() -> i32 {
    let mut buf: [4]i32 = [10, 20, 30, 40]
    let inc: [4]i32 = [1, 2, 3, 4]
    unsafe {
        // Explicit unsafe call or is_x86_feature_detected("avx2") guard required
        add_lanes_avx2(mut_view(buf), view(inc))
    }
    if buf[0] + buf[3] == 55 {
        return 0
    }
    return 1
}
```

**AXS-TGTD-052 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Calling a @target_feature("avx2") function from baseline code without guard or unsafe
// Rejected with AX_TARGET_FEATURE_MISMATCH (AXS-TGTD-009, AXS-TGTD-050)
module demo.bad_feature_call

@target_feature("avx2")
pub fn kernel_avx2(x: i32) -> i32 {
    return x + 1
}

pub fn caller_baseline(x: i32) -> i32 {
    return kernel_avx2(x) //~ ERROR AX_TARGET_FEATURE_MISMATCH
}
```

```axiom
// Example 2: Unknown target feature name in @target_feature rejected at compile time
// Rejected with AX_TARGET_UNKNOWN_FEATURE (AXS-TGTD-007..008, AXS-TGTD-050)
module demo.bad_unknown_feature

@target_feature("nonexistent_isa_ext") //~ ERROR AX_TARGET_UNKNOWN_FEATURE
pub fn bad_ext() -> i32 {
    return 0
}
```

**AXS-TGTD-053 — Requirement, Invariant & Task Traceability Matrix (`E16.1`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T653` | `SPEC-81`: Canonical declarative `TargetDesc`, `RegisterFile`, `IsaTable`, `Legalizer`, `verify_mc` & backend conformance specification | `INV-TGTD-001`..`003` | `REQ-TGT-004`, `REQ-TGT-005`, `REQ-TGT-006`, `REQ-TGT-007`, `REQ-TGT-008`, `REQ-TGT-009`, `REQ-TGT-010`, `REQ-TGT-011`, `REQ-TGT-285`, `REQ-TGT-286` | `spec/SPEC-81-target-desc-isa-conformance.md` |
| `T654` | `compiler/target/desc` & `compiler/abi/table`: Declarative `TargetDesc` registry, `TargetFingerprint`, `RegisterFile` `RegUnit`/subregister alias tables, `TargetFeatureSet` DAG, and `CallConvDesc` ABI table engine | `INV-TGTD-001` | `REQ-TGT-012`, `REQ-TGT-013`, `REQ-TGT-014`, `REQ-TGT-015`, `REQ-TGT-016`, `REQ-TGT-017`, `REQ-TGT-018`, `REQ-TGT-019`, `REQ-TGT-020`, `REQ-TGT-021`, `REQ-TGT-054`, `REQ-TGT-055`, `REQ-TGT-056` | `tests/run/target_desc`, `tests/selfhost/abi` |
| `T655` | `compiler/target/isa` & `compiler/backend/verify_mc`: Declarative `IsaTable` instruction descriptors, semantic-preserving `Legalizer` hooks, and pre-encoding Machine IR verifier | `INV-TGTD-002` | `REQ-TGT-022`..`REQ-TGT-036`, `REQ-TGT-044`..`REQ-TGT-053`, `REQ-TGT-057`, `REQ-TGT-058`, `REQ-TGT-108`, `REQ-TGT-109` | `tests/mc/isa_table`, `tests/selfhost/backend`, `tests/selfhost/isel` |
| `T656` | End-to-end E16.1 `TargetDesc` tables, `verify_mc` negative verification & target-independent `LIR` differential conformance suite | `INV-TGTD-003` | `REQ-TGT-085`..`REQ-TGT-095`, `REQ-TGT-107`, `REQ-TGT-287`..`REQ-TGT-295` | `tests/conformance/p16/e16_1_target_desc` |

## Sources

0162 §1–40; 0163 §1–22; tasks/0472 §213.1–5, §213.95 (`AHW-20..24`); tasks/0518 §1–151 (`AMACHINE-20..120`); tasks/0520 §1–25; tasks/0521 §1–30; tasks/0524 §1–113 (`ABACKEND-61..100`); tasks/0784 §562.1–200; ADR-0003; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-060..062`, `AXS-EXT-070..074`); `spec/SPEC-43-simd-backend-x86.md`; `spec/SPEC-44-cpu-feature-dispatch.md`; `spec/SPEC-77-regalloc-machine-opt.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/invariants.md` (`INV-PIPE-005..007`, `INV-TGTD-001..003`); `spec/diagnostics.md`.
