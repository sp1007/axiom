# SPEC-83 — Canonical AArch64 ISA Backend, AAPCS64 ABI & aarch64-linux ELF64 Specification

- **Status:** draft (T661, 2026-11-03)
- **Owner:** `axiom-architect`
- **Consolidates:** `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`), `spec/SPEC-31-atomics.md`, `spec/SPEC-40-integers.md`, `spec/SPEC-41-floating-point.md`, `spec/SPEC-42-simd.md`, `spec/SPEC-52-freestanding-runtime-composition.md`, `spec/SPEC-77-regalloc-machine-opt.md`, `spec/SPEC-80-linux-x86-64-elf-static.md`, `spec/SPEC-81-target-desc-isa-conformance.md`, `spec/SPEC-82-linux-elf-dynamic.md`, `0163`, `0193`, `tasks/0518`, `tasks/0521`, `tasks/0524`, `tasks/0784`
- **Covers:** `REQ-TGT-113`, `REQ-TGT-114`, `REQ-TGT-115`, `REQ-TGT-116`, `REQ-TGT-117`, `REQ-TGT-118`, `REQ-TGT-119`, `REQ-TGT-120`, `REQ-TGT-121`, `REQ-TGT-122` (and specifies the E16.3 contract for `T662`, `T663`, `T664`: `REQ-TGT-123`, `REQ-TGT-125`..`REQ-TGT-144`, `REQ-TGT-148`..`REQ-TGT-165`)
- **Consumers:** `compiler/target/aarch64/isel`, `compiler/target/aarch64/encode`, `compiler/abi/aapcs64`, `compiler/obj/elf_aarch64`, `compiler/link/elf_aarch64`, `std/sys/linux_aarch64`, `tests/mc/aarch64_isel`, `tests/encode/aarch64`, `tests/conformance/p16/e16_3_aarch64_linux`, `T662`, `T663`, `T664`

## Tóm tắt

Tài liệu `SPEC-83` chốt đặc tả chuẩn cho kiến trúc backend AArch64 (ARM64) của Axiom, quy ước gọi hàm `CallConv.Aapcs64`, bộ chọn lệnh và mã hóa lệnh 32 bit cố định, hạ tầng SIMD NEON / nguyên tử, và định dạng đối tượng/tệp thực thi ELF64 trên `aarch64-linux` (Epic `E16.3`):
1. **Mô tả đích `aarch64-linux` và tệp thanh ghi `RegisterFile` (`AXS-A64-001`..`012`):** Tách biệt hoàn toàn tầng ISA `AArch64` (tái sử dụng cho Linux, macOS, Android, Windows ARM64) khỏi ngữ nghĩa lõi và `Axiom LIR` (`AARM-20..23`); mô hình hóa chính xác quan hệ bí danh 64/32 bit `X0..X30` / `W0..W30` qua `RegUnit` (`AARM-24`), thanh ghi ngăn xếp chuyên biệt `SP` (`AARM-25`), thanh ghi không `XZR`/`WZR` (`AARM-26`), `X29` (`FP`), `X30` (`LR`, `AARM-34`), thanh ghi nháp liên thủ tục `X16`/`X17` (`IP0`/`IP1`), thanh ghi nền tảng `X18`, các góc nhìn `Q/D/S/H/B` của `V0..V31` (`AARM-41`), và cờ điều kiện `NZCV` (`AARM-27`).
2. **Quy ước gọi hàm `CallConv.Aapcs64` và hạ tầng khung ngăn xếp `STP`/`LDP` (`AXS-A64-013`..`023`):** Truyền tham số nguyên/con trỏ qua `X0..X7`, dấu phẩy động/vector và khối đồng nhất `HFA`/`HVA` (tối đa 4 phần tử) qua `V0..V7`, cấu trúc `<= 16` byte trong tối đa 2 thanh ghi GPR, cấu trúc `> 16` byte qua con trỏ do hàm gọi cấp phát, địa chỉ trả về gián tiếp trong `X8` (`XR` / `sret`, không chiếm `X0`, `AARM-32`), tập bảo toàn bởi hàm được gọi `X19..X28` và `D8..D15`, căn chỉnh `SP` 16 byte nghiêm ngặt (`AARM-37`), không có vùng đỏ (`red_zone = 0`) trên Linux (`AARM-36`), và prologue/epilogue ghép cặp `STP X29, X30, [SP, #-N]!` / `LDP`.
3. **Chọn lệnh AArch64, hằng số tức thời, tràn số, nguyên tử và NEON (`AXS-A64-024`..`037`):** Hiện thực hóa hằng số bằng lệnh dịch 12 bit, mặt nạ bit logic và chuỗi `MOVZ`/`MOVN`/`MOVK`; địa chỉ `[base, #imm]`, pre/post-index và `ADRP` + `:lo12:`; kiểm tra tràn số có dấu/không dấu (`ADDS`/`SUBS`/`B.VS`/`B.CS`, `SMULL`/`UMULL`, kiểm tra chia cho `0` và `INT_MIN / -1` trước `SDIV`/`UDIV`); nguyên tử `LDAR`/`STLR`, vòng lặp LL/SC `LDXR`/`STLXR`, mở rộng Armv8.1-A `+lse` (`CAS`/`LDADD`/`SWP`), rào cản `DMB ISH`, và vector NEON 128 bit.
4. **Mã hóa 32 bit, định vị lại ELF64 `EM_AARCH64 = 183`, veneer ±128 MiB và `std.sys.linux_aarch64` (`AXS-A64-038`..`049`):** Bộ mã hóa từ máy 32 bit little-endian tất định (sau cổng `verify_mc`), bảng định vị lại ELF64 AArch64 (`R_AARCH64_CALL26`, `R_AARCH64_ADR_PREL_PG_HI21`, `:lo12:`, GOT/PLT dùng `X16`/`X17`, TLS `TPIDR_EL0`), cầu nối nhảy xa veneer khi vượt ±128 MiB (`AARM-56`), và giao diện syscall nhân Linux AArch64 (`X8` số syscall theo `asm-generic/unistd.h`, `X0..X5` tham số, `SVC #0`).

---

## 1. `aarch64-linux` Target Description & AArch64 `RegisterFile` (`AXS-A64-001`..`012`)

**AXS-A64-001 — `aarch64-linux` `TargetDesc` Record & Orthogonal AArch64 ISA Layer.** `compiler/target/desc` registers `aarch64-linux` (accepting CLI `--target aarch64-linux` and canonical aliases `aarch64-unknown-linux-gnu` / `aarch64-unknown-linux-musl`) as an immutable `TargetDesc` record (`0193 §1–2`, `tasks/0521 §17, §60–63, AARM-20..22, AARM-30`, `SPEC-81 AXS-TGTD-002..005`, `REQ-TGT-114`, `REQ-TGT-116`):
- `target_id = TargetId.AArch64Linux`, `arch = Arch.AArch64`, `os = Os.Linux`, `pointer_width_bits = 64`, `endian = Endian.Little`;
- `default_call_conv = CallConv.Aapcs64`, `object_format = ObjectFormat.Elf`, `archive_format = ArchiveFormat.GnuAr`, `image_format = ImageFormat.ElfExec` (`ElfDyn` for PIE/`.so`);
- `default_cpu_features = { neon, fp }`, `stack_align = 16`, `shadow_space = 0`, `red_zone = 0`, `page_size = 4096` (with ELF segment alignment `0x10000` for 4 KiB / 64 KiB kernel compatibility, `AXS-A64-040`).
The `Arch.AArch64` ISA backend (`RegisterFile`, `IsaTable`, instruction selector, register allocator, `verify_mc`, and 32-bit encoder) is OS-independent and shared across `aarch64-linux`, `aarch64-macos` (`E16.4`), `aarch64-android` (`E16.5`), and `aarch64-windows` (`E16.12`) (`0193 §2, AARCH64-28`, `AARM-20, 22, 30`, `REQ-TGT-114`, `REQ-TGT-116`). [0193 §1–2, AARCH64-28; tasks/0521 §17, §60–63, AARM-20..22, AARM-30; SPEC-81 AXS-TGTD-002..005; REQ-TGT-114, REQ-TGT-116]

**AXS-A64-002 — Zero x86 Leakage in `Axiom LIR` & Four-Layer Verification Separation.** `Axiom LIR` is strictly target-independent and contains zero x86-specific or AArch64-specific physical registers (`RAX`, `RCX`, `X0`, `W0`, `SP`, `XZR`), flags (`RFLAGS`, `NZCV`), addressing modes (`[base + index * scale + disp]`), or opcodes (`LEA`, `ADRP`, `STP`, `B.EQ`) (`0193 §29–31, AARCH64-20..22`, `tasks/0521 §1–3, §154–156, AARM-21, AARM-64..65, AARM-70`, `REQ-TGT-113`, `REQ-TGT-115`, `REQ-TGT-158..159`, `REQ-TGT-164..165`). Compilation enforces four distinct verification gates where each layer proves its own invariant class (`tasks/0521 §151–155`, `REQ-TGT-113`): (1) `SemanticVerifier` (`Verified MIR`), (2) `ABIVerifier` (`CallConv.Aapcs64` lowering, `AARM-69`, `REQ-TGT-163`), (3) `MachineVerifier` (`compiler/backend/verify_mc`, `AARM-68`, `REQ-TGT-162`), and (4) `EncoderVerifier` (32-bit instruction field legality, `AARM-54`, `REQ-TGT-148`). [0193 §29–32, AARCH64-20..22; tasks/0521 §151–156, AARM-21, AARM-54, AARM-64..70; REQ-TGT-113, REQ-TGT-115, REQ-TGT-148, REQ-TGT-158..165]

**AXS-A64-003 — AArch64 `TargetFeatureSet` Implication DAG & Explicit Feature Legality.** `TargetDesc` defines the AArch64 `TargetFeatureSet` implication graph (`tasks/0521 §81–95, AARM-42, AARM-47, AARM-53, AARM-67`, `tasks/0784 §562.29–34, §562.71–75`, `SPEC-81 AXS-TGTD-007..009`, `REQ-TGT-136`, `REQ-TGT-141`, `REQ-TGT-147`, `REQ-TGT-161`):
- Baseline Armv8.0-A features on `aarch64-linux`: `{ fp, neon }` (`neon` $\rightarrow$ `fp`; attempting to disable `-neon` or `-fp` on hosted `aarch64-linux` is rejected with `AX_TARGET_UNKNOWN_FEATURE`).
- Optional features: `lse` (Armv8.1-A Large System Extensions), `fp16` ($\rightarrow$ `fp`), `dotprod` ($\rightarrow$ `neon`), `crc`, `aes` ($\rightarrow$ `neon`), `sha2` ($\rightarrow$ `neon`), `sha3` ($\rightarrow$ `sha2`), `rcpc` (Armv8.3-A `LDAPR`), `pauth` (Pointer Authentication, `AARM-53`), `bti` (Branch Target Identification), `sve` ($\rightarrow$ `neon`), and `sve2` ($\rightarrow$ `sve`).
NEON, SVE, SME, LSE, and PAC are target capabilities, never Core language concepts (`AARM-42, 47, 53`, `REQ-TGT-136, 141, 147`), and the backend never emits an instruction whose required feature bit is absent from the active function's `TargetFeatureSet` (`AARM-67`, `REQ-TGT-161`). [tasks/0521 §81–95, AARM-42, AARM-47, AARM-53, AARM-67; tasks/0784 §562.29–34, §562.71–75; SPEC-81 AXS-TGTD-007..009; REQ-TGT-136, REQ-TGT-141, REQ-TGT-147, REQ-TGT-161]

**AXS-A64-004 — 64-Bit `X0..X30` & 32-Bit `W0..W30` Aliasing via `RegUnit` Bitmasks.** The AArch64 general-purpose register bank consists of 31 64-bit registers `X0..X30` (`RegClass.GPR64`) and their lower 32-bit subregister views `W0..W30` (`RegClass.GPR32`) (`0193 §3–4, AARCH64-23..24`, `tasks/0521 §18, §41, AARM-23..24`, `tasks/0784 §562.60–61`, `SPEC-81 AXS-TGTD-014..015`, `REQ-TGT-117`, `REQ-TGT-118`). For every $n \in [0, 30]$, `Xn` and `Wn` share the identical fundamental `RegUnit` bit (`unit_mask = 1u128 << n`, `hw_encoding = n`). Writing to `Wn` computes a 32-bit result and architecturally zeroes bits `[32..64)` of `Xn`; register allocation and liveness treat any write to `Wn` or `Xn` as defining and clobbering the shared `RegUnit` $n$. [0193 §3–4, AARCH64-23..24; tasks/0521 §18, §41, AARM-23..24; tasks/0784 §562.60–61; REQ-TGT-117, REQ-TGT-118]

**AXS-A64-005 — Dedicated Stack Pointer `SP` (`WSP`) Isolation from General Allocation.** The stack pointer `SP` (and its 32-bit view `WSP`, `hw_encoding = 31`, `role = RegRole.Reserved`) is a dedicated architectural stack pointer, **never** an ordinary allocatable GPR (`0193 §3, §6, §32, AARCH64-25`, `tasks/0521 §19, AARM-25`, `tasks/0784 §562.63`, `SPEC-81 AXS-TGTD-017`, `REQ-TGT-119`). `SP` may appear only as the base register of memory addressing operands, in `ADD`/`SUB` immediate/extended-register stack adjustments, and in `MOV` to/from a GPR (`ADD Xd, SP, #0` / `ADD SP, Xn, #0`). `verify_mc` rejects any instruction that uses `SP` where the `IsaTable` operand constraint requires `GPR64` without `AllowSP`. [0193 §3, §6, §32, AARCH64-25; tasks/0521 §19, AARM-25; tasks/0784 §562.63; REQ-TGT-119]

**AXS-A64-006 — Architectural Zero Registers `XZR`/`WZR` & Encoding `31` Disambiguation.** `XZR` (64-bit) and `WZR` (32-bit) are explicit architectural zero registers (`role = RegRole.ZeroReg`, `hw_encoding = 31`, `reg_unit_mask = 0`) that read as `0` and discard writes (`tasks/0521 §20, AARM-26`, `tasks/0784 §562.62–63`, `SPEC-81 AXS-TGTD-017`, `REQ-TGT-120`). Although `SP`/`WSP` and `XZR`/`WZR` both encode as hardware register number `31` (`0b11111`), they have distinct `PhysRegId`s in `Machine IR`: `XZR`/`WZR` are forbidden as a memory base register, and `SP`/`WSP` are forbidden in instructions that interpret `31` as `XZR` (such as `ORR`, `MUL`, `STR Xt`, or `CBZ`). [tasks/0521 §20, AARM-26; tasks/0784 §562.62–63; SPEC-81 AXS-TGTD-017; REQ-TGT-120]

**AXS-A64-007 — Frame Pointer `X29` (`FP`) & Link Register `X30` (`LR`) Modeling.** `X29` is the architectural Frame Pointer (`FP`), and `X30` is the architectural Link Register (`LR`) written by `BL` and `BLR` with the return address `PC + 4` and consumed by `RET` (`0193 §6, §18, AARCH64-26`, `tasks/0521 §49–55, AARM-34`, `REQ-TGT-128`). `X30` is modeled explicitly in `RegisterFile` as call-clobbered (`implicit_defs` of `BL`/`BLR`, `implicit_uses` of `RET`); any non-leaf function (or function that modifies `X30`) must save `X30` in its stack frame before executing a nested call and restore it before `RET` (`REQ-TGT-128`). [0193 §6, §18, AARCH64-26; tasks/0521 §49–55, AARM-34; REQ-TGT-128]

**AXS-A64-008 — Intra-Procedure Call Scratch Registers `X16` (`IP0`) & `X17` (`IP1`).** `X16` (`IP0`) and `X17` (`IP1`) are caller-saved intra-procedure call scratch registers (`0193 §6`, `tasks/0521 §48, §100–101`). Under AAPCS64, linker range-extension veneers (`AXS-A64-042`), PLT dynamic resolver stubs (`AXS-A64-043`), parallel-move cycle breaking (`compiler/abi/aapcs64`), and large-frame prologue/epilogue adjustments (`AXS-A64-021`) may clobber `X16` and `X17`; live values must never be held in `X16` or `X17` across any `BL`, `BLR`, or tail-call `B` boundary. [0193 §6; tasks/0521 §48, §100–101]

**AXS-A64-009 — Platform Register `X18` Reservation Policy.** AAPCS64 designates `X18` as the Platform Register (used for TEB on Windows ARM64, kernel/platform state on macOS/iOS, and shadow-call-stack on Android) (`tasks/0521 §60–62, AARM-30`, `tasks/0784 §562.14, §562.76`, `SPEC-81 AXS-TGTD-017`). To guarantee portable object safety and zero platform register corruption across all AArch64 targets, `RegisterFile` marks `X18` as `RegRole.Reserved` by default (never allocated as general storage). [tasks/0521 §60–62, AARM-30; tasks/0784 §562.14, §562.76; SPEC-81 AXS-TGTD-017]

**AXS-A64-010 — FP/SIMD Register Bank `V0..V31` & `Q/D/S/H/B` Views.** The AArch64 FP/NEON register bank comprises 32 128-bit registers `V0..V31`, each modeled with a single fundamental `RegUnit` (`unit_mask = 1u128 << (32 + n)`, `hw_encoding = n`) and five width-typed views (`0193 §3–4`, `tasks/0521 §22, §42, §64, AARM-41`, `tasks/0784 §562.70`, `SPEC-81 AXS-TGTD-015..016`, `REQ-TGT-135`): `Qn` / `Vn.16B..2D` (`128`-bit, `RegClass.Vec128`), `Dn` (`64`-bit, `RegClass.FPR64`), `Sn` (`32`-bit, `RegClass.FPR32`), `Hn` (`16`-bit), and `Bn` (`8`-bit). Writing to any scalar/narrow view `Bn`/`Hn`/`Sn`/`Dn` zeroes the upper bits `[width..128)` of `Vn` (`AARM-41`, `REQ-TGT-135`). [0193 §3–4; tasks/0521 §22, §42, §64, AARM-41; tasks/0784 §562.70; REQ-TGT-135]

**AXS-A64-011 — Condition Flags `NZCV`, Thread Pointer `TPIDR_EL0` & Non-GPR `PC`.** AArch64 condition flags `NZCV` (`Negative`, `Zero`, `Carry`, `oVerflow` in `PSTATE`) are modeled as a dedicated `RegClass.Flags` resource (`role = RegRole.FlagsReg`, `0193 §10–11, AARCH64-27`, `tasks/0521 §21, §23–24, AARM-27`, `tasks/0784 §562.60, §562.66–67`, `SPEC-81 AXS-TGTD-027`, `REQ-TGT-121`). Instructions that set flags (`ADDS`, `SUBS`, `ANDS`, `CMP`, `CMN`, `TST`, `CCMP`, `FCMP`) declare `implicit_defs = NZCV`, and flag consumers (`B.cond`, `CSEL`, `CSINC`, `CSINV`, `CSNEG`, `CSET`, `ADC`, `SBC`, `CCMP`) declare `implicit_uses = NZCV`. The program counter `PC` is never an addressable GPR (`tasks/0521 §21`), and thread-local storage reads the system register `TPIDR_EL0` via `MRS Xd, TPIDR_EL0`. [0193 §10–11, AARCH64-27; tasks/0521 §21, §23–24, AARM-27; tasks/0784 §562.60, §562.66–67; REQ-TGT-121]

**AXS-A64-012 — Semantic-Preserving Register Allocation Over AArch64 `RegisterFile`.** Both `LinearScan` (`-O0`, `-O1`) and `Hybrid/Graph` (`-O2`, `-Os`, `-Oz`) register allocators (`SPEC-77`, `SPEC-81 AXS-TGTD-019`) operate unchanged on the AArch64 `RegisterFile` (`0193 §19–20`, `tasks/0521 §10, §40, AARM-28`, `REQ-TGT-122`). Register assignment, live-range splitting, move coalescing, and stack slot spilling/reloading are strictly transparent to ownership, `view`/`mut_view` capabilities, and deterministic `Drop` semantics (`AARM-28`, `REQ-TGT-122`). [0193 §19–20; tasks/0521 §10, §40, AARM-28; SPEC-81 AXS-TGTD-019..020; REQ-TGT-122]

---

## 2. `CallConv.Aapcs64` Calling Convention & `STP`/`LDP` Frame Lowering (`AXS-A64-013`..`023`)

**AXS-A64-013 — Integer, Pointer, 128-Bit Integer & Fat-Pointer Passing in `X0..X7`.** Under `CallConv.Aapcs64` (`compiler/abi/aapcs64`), scalar integer and pointer arguments (`i8..i64`, `u8..u64`, `isize`, `usize`, `bool`, `char`, raw pointers, single-word `view<T>`/`mut_view<T>`, and `fn` pointers) are assigned left-to-right to the 8 general-purpose argument registers `X0..X7` (`Next General-purpose Register Number`, `NGRN` $\in [0, 8]$, `0193 §5, §16–17`, `tasks/0521 §43–44, AARM-29`, `REQ-TGT-123`):
- Narrow integers (`i8`, `u8`, `i16`, `u16`, `bool`) are sign- or zero-extended to 32 bits in `W0..W7` by both caller and callee.
- 16-byte two-word fat pointers (`Str`, `view<[T]>`, `mut_view<[T]>`, `view<dyn Trait>`) have 8-byte alignment and occupy the next two consecutive available GPRs `(X[NGRN], X[NGRN+1])` if `NGRN <= 6` (or pass on the stack with `NGRN = 8` if `NGRN == 7`).
- 128-bit integers (`i128`, `u128`) have 16-byte natural alignment: per AAPCS64, if `NGRN` is odd, `NGRN` is rounded up to the next even register number (`X0:X1`, `X2:X3`, `X4:X5`, or `X6:X7`, skipping the intervening odd register); on return, `i128`/`u128` and 2-word fat pointers are returned in `X0` (low 64 bits / `ptr`) and `X1` (high 64 bits / `len` or `vtable`). [0193 §5, §16–17; tasks/0521 §43–44, AARM-29; REQ-TGT-123]

**AXS-A64-014 — Floating-Point, Vector & `HFA`/`HVA` Classification in `V0..V7`.** Scalar floating-point (`f32` in `S0..S7`, `f64` in `D0..D7`), 64/128-bit SIMD vector (`Q0..Q7`), Homogeneous Floating-point Aggregate (`HFA`), and Homogeneous Short-Vector Aggregate (`HVA`) arguments are assigned left-to-right to `V0..V7` (`Next SIMD and Floating-point Register Number`, `NSRN` $\in [0, 8]$), independently of `NGRN` (`0193 §5`, `tasks/0521 §43–45, AARM-29, AARM-31`, `REQ-TGT-123`, `REQ-TGT-125`):
- An aggregate is an **HFA** (or **HVA**) if and only if after flattening nested fields/arrays it contains **1 to 4 leaf members** all of the identical floating-point type (`f32` or `f64`) or identical 64/128-bit vector type, with no tail/inter-field padding (`@repr(C)` or canonical Axiom layout).
- An HFA/HVA with $k \in [1, 4]$ members occupies $k$ consecutive registers `V[NSRN]..V[NSRN + k - 1]` if `NSRN + k <= 8`; otherwise `NSRN` is set to `8` and the entire HFA/HVA is passed by value on the stack.
- An HFA/HVA return value with $k \in [1, 4]$ members is returned directly in `V0..V[k-1]`. [0193 §5; tasks/0521 §43–45, AARM-29, AARM-31; REQ-TGT-123, REQ-TGT-125]

**AXS-A64-015 — Non-HFA/HVA Composite Argument & Return Classification (`<= 16` Bytes vs `> 16` Bytes).** Non-empty aggregates (`struct`, `tuple`, `enum`, `[N]T`) that are neither HFA nor HVA are classified by total byte size (`tasks/0521 §12, §45, §107, AARM-31`, `REQ-TGT-125`):
1. **Zero-sized types (`size == 0`):** Consume 0 registers and 0 stack bytes.
2. **Small composites (`1 <= size <= 16` bytes):** Partitioned into $M = \lceil \text{size} / 8 \rceil \in \{1, 2\}$ 8-byte doublewords. For arguments, if `NGRN` (aligned up to an even register if `align_of(T) == 16`) satisfies `NGRN + M <= 8`, the composite is passed in `X[NGRN]..X[NGRN + M - 1]`; otherwise `NGRN = 8` and the composite is copied to the outgoing stack argument area. For return values, `1 <= size <= 16` composites are returned directly in `X0` (and `X1` when $M = 2$).
3. **Large composites (`size > 16` bytes, or non-`Copy` by-value aggregates requiring caller temporary copy):** For call arguments, the caller allocates a 16-byte-aligned temporary copy in its own frame, copies the value into it, and passes the 64-bit pointer to that copy as a single pointer argument in `X[NGRN]` (or on the stack if `NGRN == 8`). [tasks/0521 §12, §45, §107, AARM-31; REQ-TGT-125]

**AXS-A64-016 — Indirect Result Location Register `X8` (`XR` / `sret`).** When a function returns a non-HFA/HVA composite with `size > 16` bytes, the caller allocates a result buffer aligned to `max(16, align_of(Ret))` and passes its address in the Indirect Result Location Register `X8` (`XR`) immediately before `BL`/`BLR` (`tasks/0521 §45–47, AARM-32`, `SPEC-81 AXS-TGTD-011`, `REQ-TGT-126`). Unlike `x86_64` (`RCX` on `Win64`, `RDI` on `SysV64`), passing `sret` in `X8` on AAPCS64 **does not** consume `X0` (`NGRN` still starts at `0` for the first explicit parameter). Because `X8` is caller-saved across nested calls, a non-leaf callee returning via `sret` saves incoming `X8` to a local register or stack slot in its prologue and writes the final aggregate to that address before `RET` (`AARM-32`, `REQ-TGT-126`). [tasks/0521 §45–47, AARM-32; SPEC-81 AXS-TGTD-011; REQ-TGT-126]

**AXS-A64-017 — Outgoing Stack Arguments (`NSAA`) & Zero Shadow Space.** `CallConv.Aapcs64` defines `shadow_space = 0` (`0193 §5, §8`, `tasks/0521 §43, §59`). Stack arguments (`Next Stacked Argument Address`, `NSAA`, starting at `[SP + 0]`) are placed in left-to-right parameter order: each argument's offset is aligned to `max(8, align_of(T))` and its size is rounded up to the next multiple of 8 bytes. [0193 §5, §8; tasks/0521 §43, §59]

**AXS-A64-018 — Caller-Saved vs Callee-Saved Registers (`X19..X28`, Low 64-Bit `D8..D15`).** Under `CallConv.Aapcs64` (`0193 §6`, `tasks/0521 §48, AARM-33`, `REQ-TGT-127`):
- **Callee-saved:** `X19..X28` (10 GPRs), `X29` (`FP`), `SP`, and the **low 64 bits `D8..D15`** of vector registers `V8..V15` (8 `f64` units).
- **Caller-saved (call-clobbered):** `X0..X17`, `X30` (`LR`), `V0..V7` (all 128 bits), the **upper 64 bits `[64..128)` of `V8..V15`**, `V16..V31` (all 128 bits), and `NZCV`. Any function holding a 128-bit `Q8..Q15` vector value live across a `BL`/`BLR` call must spill or rematerialize the upper 64 bits (`AARM-33`, `REQ-TGT-127`). [0193 §6; tasks/0521 §48, AARM-33; REQ-TGT-127]

**AXS-A64-019 — Mandatory 16-Byte `SP` Alignment & Zero Red Zone on `aarch64-linux`.** AAPCS64 and the Linux AArch64 kernel mandate `SP % 16 == 0` at every public function entry, before every outgoing `BL`/`BLR`, and at every instruction that uses `SP` as a memory base address (hardware raises an `SP` alignment fault if `SP % 16 != 0` on memory access) (`0193 §8, AARCH64-35`, `tasks/0521 §54, §59, AARM-35..37`, `REQ-TGT-129..131`). Linux AArch64 provides **no red zone** (`red_zone = 0`): signal handlers may overwrite memory below `SP` at any instruction boundary, so leaf functions must never access `[SP - offset]` without first decrementing `SP` (`AARM-36`, `REQ-TGT-130`). [0193 §8, AARCH64-35; tasks/0521 §54, §59, AARM-35..37; REQ-TGT-129, REQ-TGT-130, REQ-TGT-131]

**AXS-A64-020 — `STP`/`LDP` Paired Frame Prologue/Epilogue & Leaf Elision.** Frame lowering (`compiler/target/aarch64/isel`) models register save/restore semantically before selecting paired instructions (`0193 §7–8, §18, AARCH64-35`, `tasks/0521 §54–58, AARM-34..35`, `REQ-TGT-128..129`):
- **Non-leaf / frame-allocating functions:** Round total frame size $N$ up to a multiple of `16`. For $N \le 504$, emit `STP X29, X30, [SP, #-N]!` followed by `MOV X29, SP` (`ADD X29, SP, #0`), save modified callee-saved registers in pairs (`STP X19, X20, [SP, #16]`, `STP D8, D9, [SP, #off]`), and restore in reverse order in the epilogue (`LDP X19, X20, [SP, #16]` ... `LDP X29, X30, [SP], #N` + `RET`). If an odd number of callee-saved registers is used, the final register is saved with `STR` inside the 16-byte-aligned frame.
- **Pure leaf functions:** When a function makes zero calls, does not modify `X30` or `X19..X28`/`D8..D15`, and requires zero stack slots, frame allocation and `STP X29, X30` are omitted and the function returns directly via `RET` (`0193 §18`, `tasks/0521 §58`). [0193 §7–8, §18, AARCH64-35; tasks/0521 §54–58, AARM-34..35; REQ-TGT-128, REQ-TGT-129]

**AXS-A64-021 — Large Stack Frame Lowering (`> 504` Bytes) & 4 KiB Stack Probes.** Because `STP`/`LDP` pre/post-indexed signed 7-bit scaled immediates cover $[-512, 504]$ in 8-byte steps, when total frame size $N > 504$ bytes, the prologue emits `STP X29, X30, [SP, #-save_size]!`, `MOV X29, SP`, and subtracts the remaining local/outgoing size via `SUB SP, SP, #rem` (using `LSL #12` + low 12-bit `SUB`, or materializing large sizes in `X16` and `SUB SP, SP, X16, UXTX`). For frames with $N \ge 4096$ bytes, the prologue emits a deterministic 4 KiB page-probing loop (`SUB SP, SP, #4096` + `STR XZR, [SP]`) so no guard page can be skipped (`ADR-0003`, `SPEC-81 AXS-TGTD-037`). [ADR-0003; SPEC-81 AXS-TGTD-037]

**AXS-A64-022 — Variadic `extern "C"` AAPCS64 Calls & `va_list` Layout.** Unlike Apple Darwin ARM64 (`E16.4`), standard `CallConv.Aapcs64` on `aarch64-linux` passes variadic arguments using the normal `X0..X7` and `V0..V7` register assignment rules (with variadic `f32` promoted to `f64` in `D0..D7`) (`tasks/0521 §151`, `SPEC-50 AXS-UNS-032`). The AAPCS64 `va_list` representation is the 32-byte `@repr(C)` struct `{ __stack: *mut void, __gr_top: *mut void, __vr_top: *mut void, __gr_offs: i32, __vr_offs: i32 }`. [tasks/0521 §151; SPEC-50 AXS-UNS-032]

**AXS-A64-023 — Calling Convention Mapping & Tail-Call (`B` / `BR`) Legality.** On `aarch64-linux`, default Axiom `fn`, `extern "C" fn`, and `extern "system" fn` lower to `CallConv.Aapcs64`. Eligible `@tailcall` sites (`SPEC-73 AXS-INL-032`, `tasks/0521 §53`) that require no caller-allocated outgoing stack growth restore `X29`/`X30` and callee-saved registers in the epilogue and jump via `B target` (direct) or `BR X16` / `BR X17` (indirect, never `BR X19..X28` after restore). [tasks/0521 §53, §60–62; SPEC-73 AXS-INL-032]

---

## 3. AArch64 Instruction Selection, Immediates, Addressing, Overflow, Atomics & NEON (`AXS-A64-024`..`037`)

**AXS-A64-024 — Arithmetic, Logical Bitmask & `MOVZ`/`MOVN`/`MOVK` Immediate Materialization.** `compiler/target/aarch64/isel` lowers `LIR` integer constants according to AArch64 immediate encoding classes (`0193 §12–13`, `tasks/0521 §76–77`, `tasks/0784 §562.65`):
1. **12-bit shifted arithmetic immediates (`ADD`/`SUB`/`ADDS`/`SUBS`/`CMP`/`CMN`):** Unsigned `uimm12` $\in [0, 4095]$ with optional `LSL #12` ($u \times 2^{12}$). Negated constants in $[-4095, -1]$ fold by flipping `ADD` $\leftrightarrow$ `SUB` (`CMP` $\leftrightarrow$ `CMN`).
2. **Logical bitmask immediates (`AND`/`ORR`/`EOR`/`ANDS`/`TST`):** Repeating $2^k$-bit ($k \in \{1..6\}$) contiguous non-trivial run of ones rotated by `immr`, encoded in the 13-bit `(N, immr, imms)` field.
3. **16-bit halfword move sequences (`MOVZ`/`MOVN`/`MOVK`):** Arbitrary 32-bit and 64-bit constants not representable as a single `ORR` bitmask immediate are materialized in 1 to 4 instructions: choose `MOVZ` (when $\ge 2$ of the four 16-bit halfwords are `0x0000`) or `MOVN` (when $\ge 2$ halfwords are `0xFFFF`) for the first non-trivial halfword, followed by `MOVK Xd, #imm16, LSL #{16, 32, 48}` only for remaining halfwords that differ from the base fill (`0x0000` for `MOVZ`, `0xFFFF` for `MOVN`). [0193 §12–13; tasks/0521 §76–77; tasks/0784 §562.65]

**AXS-A64-025 — Integer Arithmetic, Multiply-Accumulate, Bitwise & Bitfield Combining.** Instruction selection maps scalar 32-bit (`W`) and 64-bit (`X`) operations (`0193 §9`, `tasks/0521 §25–33, §74–75`):
- Wrapping/unchecked `add`/`sub`/`mul`: `ADD`, `SUB`, `NEG` (`SUB Xd, XZR, Xm`), `MUL` (`MADD Xd, Xn, Xm, XZR`), and fused `MADD`/`MSUB` (`a ± b * c`).
- Bitwise & shifts: `AND`, `ORR`, `EOR`, `MVN` (`ORN Xd, XZR, Xm`), `BIC`, `ORN`, `EON`, `LSLV`/`LSRV`/`ASRV`/`RORV` (with shift count masked mod 32 or 64 per `SPEC-40 AXS-INT-014`).
- Bitfield & bit-count intrinsics: constant shifts/zero-extensions/sign-extensions/bit-extractions combine into `UBFM` (`LSL`/`LSR`/`UXTB`/`UXTH`), `SBFM` (`ASR`/`SXTB`/`SXTH`/`SXTW`), `BFM`, and `EXTR` (`ROR`); `leading_zeros` $\rightarrow$ `CLZ`, `trailing_zeros` $\rightarrow$ `RBIT` + `CLZ`, `reverse_bits` $\rightarrow$ `RBIT`, `swap_bytes` $\rightarrow$ `REV`/`REV16`/`REV32`, and `count_ones` $\rightarrow$ `FMOV Dn, Xn` + `CNT Vd.8B, Vn.8B` + `ADDV Bd, Vd.8B` + `UMOV Wd, Vd.B[0]` (or `CNT` when `+cssc` is present). [0193 §9; tasks/0521 §25–33, §74–75; SPEC-40 AXS-INT-014..016]

**AXS-A64-026 — Checked Integer Overflow Lowering (`ADDS`/`SUBS`/`B.VS`, `SMULL`/`UMULL`, 128-Bit Carry Chains).** Checked, wrapping, saturating, and overflowing integer operations (`SPEC-40 AXS-INT-006..013`) lower to exact AArch64 flag sequences (`tasks/0521 §15, §25–29`, `SPEC-81 AXS-TGTD-030`):
- **Checked 32/64-bit `add`/`sub`:** Signed addition/subtraction emits `ADDS`/`SUBS` + `B.VS panic_overflow`; unsigned addition emits `ADDS` + `B.CS panic_overflow`; unsigned subtraction emits `SUBS` + `B.CC panic_overflow` (note that on AArch64 `SUBS`, `C = 1` means **no borrow** and `C = 0` (`B.CC` / `B.LO`) means unsigned borrow/underflow). Narrow `i8`/`i16`/`u8`/`u16` checked ops sign/zero-extend or shift into the top of `Wn` before `ADDS`/`SUBS`.
- **Checked multiplication:** 32-bit signed `i32` uses `SMULL Xd, Wn, Wm` + `CMP Xd, Wd, SXTW` + `B.NE panic_overflow`; 32-bit unsigned `u32` uses `UMULL Xd, Wn, Wm` + `TST Xd, #0xFFFFFFFF00000000` (`LSR Xtmp, Xd, #32; CBNZ Xtmp, panic_overflow`). 64-bit signed `i64` uses `MUL Xlo, Xn, Xm` + `SMULH Xhi, Xn, Xm` + `CMP Xhi, Xlo, ASR #63` + `B.NE panic_overflow`; 64-bit unsigned `u64` uses `MUL Xlo, Xn, Xm` + `UMULH Xhi, Xn, Xm` + `CBNZ Xhi, panic_overflow`.
- **128-bit `i128`/`u128` (`(Xlo, Xhi)`):** Wrapping add/sub expand to `ADDS Xd_lo, Xa_lo, Xb_lo` + `ADC Xd_hi, Xa_hi, Xb_hi` and `SUBS Xd_lo, Xa_lo, Xb_lo` + `SBC Xd_hi, Xa_hi, Xb_hi`; checked 128-bit add/sub replace the high limb with `ADCS`/`SBCS` and branch on `B.VS` (`i128`) or `B.CS`/`B.CC` (`u128`). [tasks/0521 §15, §25–29; SPEC-40 AXS-INT-006..013; SPEC-81 AXS-TGTD-030]

**AXS-A64-027 — Guarded `SDIV`/`UDIV` & `MSUB` Remainder Lowering.** Because AArch64 hardware `SDIV` and `UDIV` **never trap** (returning `0` on division by zero and returning `INT_MIN` on `INT_MIN / -1`), instruction selection always emits explicit pre-check branches before `SDIV`/`UDIV` (`0193 §9`, `tasks/0521 §30`, `SPEC-81 AXS-TGTD-033`, `REQ-TGT-029`):
1. For both signed and unsigned `/` and `%`, emit `CBZ Xdivisor, panic_div_zero` (unless divisor is a proven non-zero constant).
2. For signed `/` (`checked`), emit the `lhs == T.MIN && rhs == -1` check (`CMN Xrhs, #1` + `B.NE ok` + compare `Xlhs == T.MIN` + `B.EQ panic_overflow`); for signed `%`, `T.MIN % -1` yields `0` without overflow.
3. Remainder `a % b` is computed via `SDIV`/`UDIV Xquot, Xa, Xb` followed by `MSUB Xrem, Xquot, Xb, Xa` (`Xrem = Xa - Xquot * Xb`). [0193 §9; tasks/0521 §30; SPEC-40 AXS-INT-008; SPEC-81 AXS-TGTD-033]

**AXS-A64-028 — Condition Codes, `CBZ`/`CBNZ`/`TBZ`/`TBNZ` & Branchless `CSEL`/`CSINC`/`CSET`.** Target-neutral `LirCmp` and conditional control flow lower to AArch64 condition codes (`EQ=0`, `NE=1`, `CS/HS=2`, `CC/LO=3`, `MI=4`, `PL=5`, `VS=6`, `VC=7`, `HI=8`, `LS=9`, `GE=10`, `LT=11`, `GT=12`, `LE=13`, `AL=14`) (`0193 §9–11`, `tasks/0521 §70–73, AARM-27, AARM-45`, `tasks/0784 §562.66–67`, `REQ-TGT-121`, `REQ-TGT-139`):
- Comparisons against `0` fuse with branches into `CBZ`/`CBNZ` (`== 0` / `!= 0`) and single-bit tests `(x & (1 << bit)) ==/!= 0` fuse into `TBZ`/`TBNZ Rt, #bit, label`.
- Short-circuit `&&`/`||` chains of pure comparisons may fuse into `CMP` + `CCMP`.
- Boolean materialization lowers to `CSET Wd, cond` (`CSINC Wd, WZR, WZR, invert(cond)`), and pure trap-free diamond branches lower to `CSEL`, `CSINC`, `CSINV`, or `CSNEG` (`AARM-45`, `REQ-TGT-139`). [0193 §9–11; tasks/0521 §70–73, AARM-27, AARM-45; tasks/0784 §562.66–67; REQ-TGT-121, REQ-TGT-139]

**AXS-A64-029 — Load/Store Addressing Modes & Paired `LDP`/`STP` Access.** AArch64 is a strict load/store architecture (`0193 §14–15`, `tasks/0521 §34, §37–39, AARM-38..39`, `tasks/0784 §562.64`, `REQ-TGT-132..133`). Address expressions remain semantic in `LIR` (`AARM-38`, `REQ-TGT-132`) and lower to AArch64 addressing modes (`AARM-39`, `REQ-TGT-133`):
- **Unsigned scaled offset:** `[Xn|SP, #uimm12 * size]` for 1-, 2-, 4-, 8-, and 16-byte accesses (`LDRB`/`STRB`, `LDRH`/`STRH`, `LDR`/`STR` `W`/`X`/`B`/`H`/`S`/`D`/`Q`, and sign-extending `LDRSB`/`LDRSH`/`LDRSW`).
- **Unscaled signed 9-bit offset:** `LDUR`/`STUR [Xn|SP, #simm9]` for byte offsets in $[-256, 255]$ that are negative or not a multiple of access size.
- **Pre-indexed & post-indexed:** `[Xn|SP, #simm9]!` and `[Xn|SP], #simm9`.
- **Register offset with extend/shift:** `[Xn|SP, Xm, LSL #log2(size)]` or `[Xn|SP, Wm, {UXTW|SXTW} #log2(size)]`.
- **Paired 7-bit scaled signed offset:** `LDP`/`STP` (and `LDPSW`) `[Xn|SP, #simm7 * scale]` for adjacent 32-bit, 64-bit, or 128-bit loads/stores (`simm7` $\in [-64, 63]$). [0193 §14–15; tasks/0521 §34, §37–39, AARM-38..39; tasks/0784 §562.64; REQ-TGT-132, REQ-TGT-133]

**AXS-A64-030 — PC-Relative Page Addressing (`ADRP` + `:lo12:`) & Literal Pools.** References to module `static` items, string/float constants in `.rodata`, vtables, and functions lower to 4 KiB page-relative two-instruction sequences (`0193 §24, §38`, `tasks/0521 §35–36, §78, AARM-40`, `tasks/0784 §562.68`, `REQ-TGT-134`):
- **Address materialization:** `ADRP Xd, sym` (`R_AARCH64_ADR_PREL_PG_HI21`, ±4 GiB range) followed by `ADD Xd, Xd, :lo12:sym` (`R_AARCH64_ADD_ABS_LO12_NC`).
- **Folded load/store:** When the address is used solely by a naturally aligned load/store, the `:lo12:` offset folds directly into `LDR`/`STR Rt, [Xd, :lo12:sym]` (`R_AARCH64_LDST{8..128}_ABS_LO12_NC`).
- **PC-relative literal loads:** Constants within ±1 MiB may use `LDR Wt/Xt/St/Dt/Qt, label` with range verification (`tasks/0784 §562.68`). [0193 §24, §38; tasks/0521 §35–36, §78, AARM-40; tasks/0784 §562.68; REQ-TGT-134]

**AXS-A64-031 — Strict IEEE-754 Scalar Floating-Point & Hardware Saturating Casts.** Scalar `f32` (`Sn`) and `f64` (`Dn`) operations preserve strict IEEE-754 semantics (`0193 §9`, `tasks/0521 §66–69, AARM-43..44`, `SPEC-41 AXS-FLT-010..022`, `SPEC-81 AXS-TGTD-031`, `REQ-TGT-137..138`):
- Arithmetic & comparisons: `FADD`, `FSUB`, `FMUL`, `FDIV`, `FSQRT`, `FNEG`, `FABS`, `FMINNM`/`FMAXNM`, `FRINTN`/`FRINTM`/`FRINTP`/`FRINTZ`, `FCMP`, `FCCMP`, and `FCSEL`.
- Fused multiply-add (`FMADD`, `FMSUB`, `FNMADD`, `FNMSUB`, and vector `FMLA`/`FMLS`) is selected **only** when explicitly requested via `std.math.fma` or authorized by `@fast_math` (`AARM-44`, `REQ-TGT-138`).
- Saturating float-to-integer casts (`as i32`/`u32`/`i64`/`u64`, `SPEC-41 AXS-FLT-022`) map directly to single-instruction AArch64 `FCVTZS` and `FCVTZU`, which architecturally convert `NaN -> 0` and clamp out-of-range values to `[T.MIN, T.MAX]`. [0193 §9; tasks/0521 §66–69, AARM-43..44; SPEC-41 AXS-FLT-010..022; REQ-TGT-137, REQ-TGT-138]

**AXS-A64-032 — 128-Bit NEON SIMD Vector Lowering (`V0..V31`).** Portable `Vector<T, N>` and `Mask<N>` operations (`SPEC-42`, `SPEC-74`) lower to baseline 128-bit NEON instructions with lane arrangement specifiers `.16B` (`16x8`), `.8H` (`8x16`), `.4S` (`4x32`), and `.2D` (`2x64`) (`tasks/0521 §64–65, §93–95, AARM-41..42`, `tasks/0784 §562.70–73`, `REQ-TGT-135..136`):
- Integer & FP lane arithmetic: `ADD`/`SUB`/`MUL` (`.16B`/`.8H`/`.4S`/`.2D`), `SMAX`/`UMAX`/`SMIN`/`UMIN`, `SQADD`/`UQADD`/`SQSUB`/`UQSUB`, `SHL`/`SSHR`/`USHR`, and `FADD`/`FSUB`/`FMUL`/`FDIV`/`FSQRT` (`.4S`/`.2D`).
- Bitwise & masked select: `AND`/`ORR`/`EOR`/`BIC`/`MVN` (`.16B`) and bitwise select `BSL Vd.16B, Vtrue.16B, Vfalse.16B` (`Vd` holds the all-ones/all-zeroes lane mask from `CMEQ`/`CMGT`/`CMHI`/`FCMEQ`/`FCMGT`/`FCMGE`).
- Broadcast, lane insert/extract & shuffles: `DUP Vd.<T>, Wn/Xn` (or `DUP Vd.<T>, Vn.<T>[lane]`), `INS`, `UMOV`/`SMOV`, `TBL` (arbitrary byte permutation), `EXT`, `ZIP1`/`ZIP2`, `UZP1`/`UZP2`, `TRN1`/`TRN2`.
- Horizontal reductions: `ADDV`, `SADDLV`/`UADDLV`, `SMAXV`/`UMAXV`/`SMINV`/`UMINV`, `FMAXNMV`/`FMINNMV`, and pairwise `ADDP`/`FADDP` for `.2D` reductions.
- Wider `256`-bit (`v256`) and `512`-bit (`v512`) portable vectors split deterministically in the legalizer into 2 or 4 128-bit `V` registers (`SPEC-81 AXS-TGTD-029`). Scalable `SVE`/`SVE2` (`+sve`) uses separate predicate registers `P0..P15` and `Z0..Z31` without assuming compile-time fixed width (`tasks/0521 §93–94`, `tasks/0784 §562.72–73`). [tasks/0521 §64–65, §93–95, AARM-41..42; tasks/0784 §562.70–73; REQ-TGT-135, REQ-TGT-136]

**AXS-A64-033 — Weakly-Ordered Memory Model & Acquire/Release Atomic Load/Store (`LDAR`/`STLR`, `DMB ISH`).** Because AArch64 has a weakly-ordered multi-copy-atomic memory model (unlike x86-64 TSO), `compiler/target/aarch64/isel` maps `Atomic<T>` loads, stores, and fences (`SPEC-31 AXS-ATM-020..035`) to explicit AArch64 ordering instructions (`tasks/0521 §81, §85–88, §121–123, AARM-46`, `tasks/0784 §562.74`, `REQ-TGT-140`):
- **Atomic Load:** `Ordering.Relaxed` $\rightarrow$ `LDRB`/`LDRH`/`LDR` (`W`/`X`); `Ordering.Acquire` and `Ordering.SeqCst` $\rightarrow$ Load-Acquire `LDARB`/`LDARH`/`LDAR` (or `LDAPRB`/`LDAPRH`/`LDAPR` for `Acquire` when `+rcpc` is enabled and `SeqCst` is not required).
- **Atomic Store:** `Ordering.Relaxed` $\rightarrow$ `STRB`/`STRH`/`STR` (`W`/`X`); `Ordering.Release` and `Ordering.SeqCst` $\rightarrow$ Store-Release `STLRB`/`STLRH`/`STLR` (releasing `STLR` followed by `LDAR` satisfies full `SeqCst` store-load ordering on Armv8-A).
- **Fences:** `atomic_fence(Acquire)` $\rightarrow$ `DMB ISHLD`; `atomic_fence(Release | AcqRel | SeqCst)` $\rightarrow$ `DMB ISH`; `compiler_fence` emits a zero-byte scheduling barrier with `InstrEffectFlags.Barrier`. [tasks/0521 §81, §85–88, §121–123, AARM-46; tasks/0784 §562.74; SPEC-31 AXS-ATM-020..035; REQ-TGT-140]

**AXS-A64-034 — Baseline Armv8.0-A LL/SC Atomic RMW & CAS Loops (`LDXR`/`LDAXR`, `STXR`/`STLXR`).** When `+lse` is not enabled in `TargetFeatureSet`, atomic read-modify-write (`fetch_add`, `fetch_sub`, `fetch_and`, `fetch_or`, `fetch_xor`, `swap`) and `compare_exchange` / `compare_exchange_weak` expand to Load-Exclusive / Store-Exclusive retry loops (`tasks/0521 §81, §83–84, AARM-48`, `REQ-TGT-142`):
- Select `LDXR` (`Relaxed`/`Release`) or `LDAXR` (`Acquire`/`AcqRel`/`SeqCst`) and `STXR` (`Relaxed`/`Acquire`) or `STLXR` (`Release`/`AcqRel`/`SeqCst`) for 8/16/32/64-bit widths (`B`/`H`/`W`/`X`, or `LDXP`/`LDAXP` + `STXP`/`STLXP` for 128-bit).
- RMW loop: `.Lretry: ld[a]xr Rold, [Xptr]` $\rightarrow$ compute `Rnew` $\rightarrow$ `st[l]xr Wstatus, Rnew, [Xptr]` $\rightarrow$ `cbnz Wstatus, .Lretry`. No memory access, spill/reload, or function call may appear between `LD*XR` and `ST*XR`.
- CAS loop: on comparison mismatch (`CMP Rold, Rexpected; B.NE .Lfail`), `.Lfail` executes `CLREX` to clear the exclusive monitor before continuing. [tasks/0521 §81, §83–84, AARM-48; REQ-TGT-142]

**AXS-A64-035 — Optional Armv8.1-A `+lse` Large System Extensions (`CAS`/`LDADD`/`SWP`).** When `+lse` is enabled in `TargetFeatureSet` (`--target-feature +lse` or `@target_feature("lse")`), `compiler/target/aarch64/isel` lowers 8/16/32/64-bit atomic RMW and strong CAS directly to single-instruction LSE atomics (`tasks/0521 §82, AARM-47`, `REQ-TGT-141`):
- `compare_exchange` $\rightarrow$ `CAS` / `CASA` (`Acquire`) / `CASL` (`Release`) / `CASAL` (`AcqRel`/`SeqCst`) (and `CASP*` for 128-bit aligned pairs).
- `swap` $\rightarrow$ `SWP` / `SWPA` / `SWPL` / `SWPAL`.
- `fetch_add` $\rightarrow$ `LDADD*` (negating the operand for `fetch_sub`); `fetch_and` $\rightarrow$ `MVN` + `LDCLR*`; `fetch_or` $\rightarrow$ `LDSET*`; `fetch_xor` $\rightarrow$ `LDEOR*`; `fetch_max`/`fetch_min` $\rightarrow$ `LDSMAX*`/`LDUMAX*`/`LDSMIN*`/`LDUMIN*`. [tasks/0521 §82, AARM-47; REQ-TGT-141]

**AXS-A64-036 — Volatile & Device/MMIO Ordering Preservation (`DSB`/`DMB`/`ISB`).** Volatile loads/stores (`Volatile<T>`) and MMIO register accesses (`Mmio<T>`, `MmioRO<T>`, `MmioWO<T>`, `SPEC-51 AXS-MEM-001..008`) lower to single-instruction non-merging, non-elidable `LDR*`/`STR*` marked with `InstrEffectFlags.Volatile` (`tasks/0521 §89–90, AARM-49..50`, `REQ-TGT-143..144`). Hardware memory barriers in `std.arch.aarch64` / `std.mem` lower to `DMB SY` / `DMB ISH`, `DSB SY` / `DSB ISH` (Device/DMA synchronization), and `ISB` (instruction stream synchronization), and instruction scheduling never reorders volatile or MMIO operations across each other or across barriers (`AARM-49..50`, `REQ-TGT-143..144`). [tasks/0521 §89–90, AARM-49..50; SPEC-51 AXS-MEM-001..008; REQ-TGT-143, REQ-TGT-144]

**AXS-A64-037 — AArch64 Pre-Encoding `verify_mc` Invariants.** Before any instruction is encoded (`AARM-54`, `AARM-68..69`, `REQ-TGT-148`, `REQ-TGT-162..163`), `compiler/backend/verify_mc` enforces all ten general Machine IR invariants (`SPEC-81 AXS-TGTD-037`) plus AArch64-specific rules (`0193 §32, AARCH64-34`, `tasks/0521 §98, §151–155`):
1. `SP`/`WSP` vs `XZR`/`WZR` operand legality per `IsaTable` constraint (`AXS-A64-005..006`);
2. Natural alignment of scaled `LDR`/`STR` (`offset % size == 0`) and `LDP`/`STP` (`offset % scale == 0`, and distinct destination registers `Rt != Rt2` on `LDP` loads);
3. Exclusive monitor pairing (`ST*XR` status register `Ws` must not alias `Xt` or base `Xn`, and no memory op or call intervenes between `LD*XR` and `ST*XR`);
4. 16-byte `SP` alignment (`frame_stack_delta % 16 == 0`) at every `SP`-based memory access and `BL`/`BLR` call site, and `X30` (`LR`) preservation in every non-leaf function. [0193 §32, AARCH64-34; tasks/0521 §98, §151–155, AARM-54, AARM-68..69; SPEC-81 AXS-TGTD-037; REQ-TGT-148, REQ-TGT-162, REQ-TGT-163]

---

## 4. 32-Bit Instruction Encoding, `EM_AARCH64` ELF64 Relocations, Veneers & `std.sys.linux_aarch64` (`AXS-A64-038`..`049`)

**AXS-A64-038 — Fixed-Width 32-Bit Little-Endian A64 Instruction Encoding & Round-Trip Decoding.** Every AArch64 A64 instruction is encoded by `compiler/target/aarch64/encode` as a single 4-byte aligned (`sh_addralign >= 4`) 32-bit little-endian word (`u32`) directly from verified Machine IR without an external assembler or LLVM (`0193 §21–22, AARCH64-33, AARCH64-36..37`, `tasks/0521 §97, AARM-54, AARM-57, AARM-59`, `REQ-TGT-148`, `REQ-TGT-151`, `REQ-TGT-153`):
- **Data Processing — Immediate:** `ADD`/`SUB`/`ADDS`/`SUBS` (`sf:op:S:100010:sh:imm12:Rn:Rd`), Logical (`sf:opc:100100:N:immr:imms:Rn:Rd`), `MOVZ`/`MOVN`/`MOVK` (`sf:opc:100101:hw:imm16:Rd`), `ADR`/`ADRP` (`op:immlo:10000:immhi:Rd`), Bitfield `SBFM`/`BFM`/`UBFM` (`sf:opc:100110:N:immr:imms:Rn:Rd`), and `EXTR`.
- **Branches & System:** `B`/`BL` (`op:00101:imm26`), `B.cond` (`01010100:imm19:0:cond`), `CBZ`/`CBNZ` (`sf:011010:op:imm19:Rt`), `TBZ`/`TBNZ` (`b5:011011:op:b40:imm14:Rt`), `BR`/`BLR`/`RET` (`1101011:opc:11111:000000:Rn:00000`), `SVC #imm16` (`11010100000:imm16:00001`), `BRK #imm16` (`11010100001:imm16:00000`), `DMB`/`DSB`/`ISB`/`CLREX`, and `MRS`/`MSR`.
- **Data Processing — Register, Multiply, Conditional & FP/NEON:** Shifted/extended register `ADD`/`SUB`/`AND`/`ORR`/`EOR`, `MADD`/`MSUB`/`SMULL`/`UMULL`/`SMULH`/`UMULH`, `SDIV`/`UDIV`, `CSEL`/`CSINC`/`CSINV`/`CSNEG`, `CCMP`, scalar `FADD`/`FSUB`/`FMUL`/`FDIV`/`FSQRT`/`FCMP`/`FCVTZS`/`FCVTZU`/`FMOV`, and 128-bit NEON vector encodings.
- **Loads, Stores & Atomics:** Unsigned scaled (`size:111:V:01:opc:imm12:Rn:Rt`), unscaled/pre/post-index (`size:111:V:00:opc:0:imm9:idx:Rn:Rt`), register offset, paired `LDP`/`STP` (`opc:101:V:type:L:imm7:Rt2:Rn:Rt`), `LDXR`/`STLXR`/`LDAR`/`STLR` (`size:001000:o2:L:o1:Rs:o0:Rt2:Rn:Rt`), and `+lse` `CAS*`/`LDADD*`/`SWP*`.
For every instruction $I$, `decode(encode(I)) == I` (`SPEC-81 AXS-TGTD-035`). [0193 §21–22, AARCH64-33, AARCH64-36..37; tasks/0521 §97, AARM-54, AARM-57, AARM-59; REQ-TGT-148, REQ-TGT-151, REQ-TGT-153]

**AXS-A64-039 — Intra-Function Conditional Branch Relaxation (`±1 MiB` / `±32 KiB`).** In AArch64 A64, `B.cond` and `CBZ`/`CBNZ` encode a signed 19-bit word offset (`imm19 << 2`, range $\pm 1\text{ MiB}$), and `TBZ`/`TBNZ` encode a signed 14-bit word offset (`imm14 << 2`, range $\pm 32\text{ KiB}$), whereas unconditional `B` encodes a signed 26-bit word offset (`imm26 << 2`, range $\pm 128\text{ MiB}`) (`tasks/0521 §100, AARM-56`, `REQ-TGT-150`). Before final encoding, branch relaxation checks every intra-function branch displacement: if a `B.cond`/`CBZ`/`CBNZ`/`TBZ`/`TBNZ` target lies outside its signed field range, it is deterministically relaxed to the inverted short branch jumping over an unconditional `B target` (`B.!cond .+8; B target`). [tasks/0521 §100, AARM-56; SPEC-82 AXS-ELFD-020; REQ-TGT-150]

**AXS-A64-040 — ELF64 `EM_AARCH64 = 183` Object & Image Layout (`ET_REL`, `ET_EXEC`, `ET_DYN`).** `compiler/obj/elf_aarch64` and `compiler/link/elf_aarch64` reuse the format-neutral ELF64 object and linker infrastructure (`SPEC-80`, `SPEC-82`) while separating ISA encoding from ELF serialization (`0193 §25, AARCH64-30, AARCH64-39`, `tasks/0521 §102–103, AARM-57`, `REQ-TGT-151`):
- `Elf64_Ehdr`: `EI_CLASS = ELFCLASS64 (2)`, `EI_DATA = ELFDATA2LSB (1)`, `e_machine = EM_AARCH64 (183 / 0xB7)`, `e_flags = 0`.
- Static executables (`ET_EXEC`): Default image base `0x0040_0000` with `PT_LOAD` segment alignment `p_align = 0x10000` (`64 KiB`, satisfying both `4 KiB` and `64 KiB` page-size Linux AArch64 kernels) and strict W^X permissions (`PF_R | PF_X`, `PF_R`, `PF_R | PF_W`, plus non-executable `PT_GNU_STACK`).
- Dynamic `PIE` (`ET_DYN`) & `.so` (`--kind dll`): `PT_INTERP = "/lib/ld-linux-aarch64.so.1\0"`, Full RELRO (`PT_GNU_RELRO` + `DT_BIND_NOW`), `.dynsym`/`.gnu.hash`/`.dynamic`, and deterministic GNU `ar` static archives (`lib<name>.a`). [0193 §25, AARCH64-30, AARCH64-39; tasks/0521 §102–103, AARM-57; SPEC-80; SPEC-82; REQ-TGT-151]

**AXS-A64-041 — Canonical ELF64 `EM_AARCH64` Relocation Table (`Elf64_Rela`).** `compiler/obj/elf_aarch64` emits explicit 24-byte `Elf64_Rela` records (`0193 §23–24, AARCH64-31`, `tasks/0521 §78–80, §99, AARM-51..52, AARM-55`, `REQ-TGT-149`), where $S$ is symbol VMA, $A$ is `r_addend`, $P$ is instruction/field VMA, $G$ is GOT slot VMA, and $\text{Page}(X) = X \ \& \ \sim\text{0xFFF}$:

| ELF64 `r_type` | ID | Target Field / Instruction | Computation | Range / Alignment Check |
|---|---|---|---|---|
| `R_AARCH64_ABS64` | `257` | 64-bit data pointer | $S + A$ | Full 64-bit |
| `R_AARCH64_ABS32` | `258` | 32-bit data word | $S + A$ | $[-2^{31}, 2^{32}-1]$ |
| `R_AARCH64_PREL32` | `261` | 32-bit PC-rel data (`.eh_frame`) | $S + A - P$ | Signed 32-bit $[-2^{31}, 2^{31}-1]$ |
| `R_AARCH64_ADR_PREL_LO21` | `274` | `ADR Xd, sym` (`immlo:immhi`) | $S + A - P$ | $[-2^{20}, 2^{20}-1]$ ($\pm 1\text{ MiB}$) |
| `R_AARCH64_ADR_PREL_PG_HI21` | `275` | `ADRP Xd, sym` (`immlo:immhi`) | $(\text{Page}(S + A) - \text{Page}(P)) \gg 12$ | $[-2^{20}, 2^{20}-1]$ pages ($\pm 4\text{ GiB}$) |
| `R_AARCH64_ADD_ABS_LO12_NC` | `277` | `ADD Xd, Xn, :lo12:sym` (`imm12`) | $(S + A) \ \& \ \text{0xFFF}$ | No overflow check (`_NC`) |
| `R_AARCH64_LDST8_ABS_LO12_NC` | `278` | `LDRB`/`STRB` (`imm12`) | $(S + A) \ \& \ \text{0xFFF}$ | 1-byte aligned |
| `R_AARCH64_JUMP26` | `282` | `B target` (`imm26`) | $(S + A - P) \gg 2$ | $[-2^{27}, 2^{27}-4]$ ($\pm 128\text{ MiB}$, 4B aligned) |
| `R_AARCH64_CALL26` | `283` | `BL target` (`imm26`) | $(S + A - P) \gg 2$ | $[-2^{27}, 2^{27}-4]$ ($\pm 128\text{ MiB}$, 4B aligned) |
| `R_AARCH64_LDST16_ABS_LO12_NC` | `284` | `LDRH`/`STRH` (`imm12`) | $((S + A) \ \& \ \text{0xFFF}) \gg 1$ | 2-byte aligned |
| `R_AARCH64_LDST32_ABS_LO12_NC` | `285` | `LDR`/`STR Wt/St` (`imm12`) | $((S + A) \ \& \ \text{0xFFF}) \gg 2$ | 4-byte aligned |
| `R_AARCH64_LDST64_ABS_LO12_NC` | `286` | `LDR`/`STR Xt/Dt` (`imm12`) | $((S + A) \ \& \ \text{0xFFF}) \gg 3$ | 8-byte aligned |
| `R_AARCH64_LDST128_ABS_LO12_NC` | `299` | `LDR`/`STR Qt` (`imm12`) | $((S + A) \ \& \ \text{0xFFF}) \gg 4$ | 16-byte aligned |
| `R_AARCH64_ADR_GOT_PAGE` | `311` | `ADRP Xd, :got:sym` | $(\text{Page}(G) - \text{Page}(P)) \gg 12$ | $\pm 4\text{ GiB}$ |
| `R_AARCH64_LD64_GOT_LO12_NC` | `312` | `LDR Xd, [Xn, :got_lo12:sym]` | $(G \ \& \ \text{0xFFF}) \gg 3$ | 8-byte aligned |
| `R_AARCH64_TLSIE_ADR_GOTTPREL_PAGE21` | `541` | `ADRP Xd, :gottprel:sym` | $(\text{Page}(G_{\text{tls}}) - \text{Page}(P)) \gg 12$ | $\pm 4\text{ GiB}$ |
| `R_AARCH64_TLSIE_LD64_GOTTPREL_LO12_NC` | `542` | `LDR Xd, [Xn, :gottprel_lo12:sym]` | $(G_{\text{tls}} \ \& \ \text{0xFFF}) \gg 3$ | 8-byte aligned |
| `R_AARCH64_TLSLE_ADD_TPREL_HI12` | `549` | `ADD Xd, Xn, :tprel_hi12:sym` | $(\text{tprel}(S + A) \gg 12) \ \& \ \text{0xFFF}$ | `< 16 MiB` TLS offset |
| `R_AARCH64_TLSLE_ADD_TPREL_LO12_NC` | `551` | `ADD Xd, Xn, :tprel_lo12_nc:sym` | $\text{tprel}(S + A) \ \& \ \text{0xFFF}$ | No overflow check |

Dynamic `.rela.dyn`/`.rela.plt` tables use `R_AARCH64_RELATIVE (1027)`, `R_AARCH64_GLOB_DAT (1025)`, `R_AARCH64_JUMP_SLOT (1026)`, and `R_AARCH64_TLS_TPREL (1030)`. [0193 §23–24, AARCH64-31; tasks/0521 §78–80, §99, AARM-51..52, AARM-55; REQ-TGT-149]

**AXS-A64-042 — Linker Long-Branch Range-Extension Veneers (`±128 MiB` `CALL26`/`JUMP26`).** When linking an executable or shared library where a `R_AARCH64_CALL26` (`BL`) or `R_AARCH64_JUMP26` (`B`) target satisfies $|S + A - P| \ge 2^{27}$ (`128 MiB`), `compiler/link/elf_aarch64` automatically synthesizes a deterministic 12-byte range-extension veneer (`__veneer_<sym>`) placed within $\pm 128\text{ MiB}$ of $P$ and redirects the `B`/`BL` instruction to the veneer (`tasks/0521 §100–101, AARM-56`, `tasks/0784 §562.69`, `REQ-TGT-150`):
```text
__veneer_<sym>:
    adrp x16, <target_page>         // R_AARCH64_ADR_PREL_PG_HI21
    add  x16, x16, :lo12:<target>   // R_AARCH64_ADD_ABS_LO12_NC
    br   x16
```
Because `X16` (`IP0`) is reserved by AAPCS64 as the intra-procedure call scratch register (`AXS-A64-008`), the veneer preserves `X0..X7`, `X8` (`XR`), `X30` (`LR`), and all callee-saved registers (`tasks/0521 §100–101`). If even the veneer or an `ADRP` target exceeds $\pm 4\text{ GiB}$, the linker reports `AX_LINK_RELOC_OUT_OF_RANGE`. [tasks/0521 §100–101, AARM-56; tasks/0784 §562.69; REQ-TGT-150]

**AXS-A64-043 — AArch64 Dynamic Linking (`GOT`/`PLT` with `X16`/`X17`) & `TPIDR_EL0` TLS Lowering.** In dynamic `PIE` and `.so` builds on `aarch64-linux` (`tasks/0521 §79–80, AARM-51..52`, `SPEC-82`, `REQ-TGT-145..146`):
- External/preemptible globals and taken function addresses load from `.got` via `ADRP Xd, :got:sym` (`R_AARCH64_ADR_GOT_PAGE`) + `LDR Xd, [Xd, :got_lo12:sym]` (`R_AARCH64_LD64_GOT_LO12_NC`).
- External function calls (`BL sym@PLT`) target a 16-byte AArch64 `.plt[n]` entry using `X16`/`X17` (`ADRP X16, got_plt[n]` + `LDR X17, [X16, :lo12:got_plt[n]]` + `ADD X16, X16, :lo12:got_plt[n]` + `BR X17`).
- `@thread_local static` variables read the AArch64 thread pointer `MRS Xbase, TPIDR_EL0` (`0xD53BD040`, where Linux AArch64 places the TLS blocks at positive offsets after the 16-byte TCB header `max(16, align)`): `Local-Exec` adds `:tprel_hi12:` + `:tprel_lo12_nc:`; `Initial-Exec` loads the TP offset from `.got` via `R_AARCH64_TLSIE_ADR_GOTTPREL_PAGE21` + `R_AARCH64_TLSIE_LD64_GOTTPREL_LO12_NC`. [tasks/0521 §79–80, AARM-51..52; SPEC-82; REQ-TGT-145, REQ-TGT-146]

**AXS-A64-044 — Linux AArch64 Kernel Syscall ABI (`X8`, `X0..X5`, `SVC #0`) & `asm-generic/unistd.h` Table.** In `--profile hosted` on `aarch64-linux`, `std/sys/linux_aarch64` invokes the Linux kernel directly via `SVC #0` (`0xD400_0001`) without requiring `libc` (`0193 §26`, `SPEC-04 AXS-EXT-110`, `SPEC-80 AXS-ELFS-040..041`):
- **Register contract:** Syscall number in `X8`, up to 6 arguments in `X0, X1, X2, X3, X4, X5`, and 64-bit signed return value in `X0`. Kernel return values in `[-4095, -1]` represent `-errno` and map deterministically to negated host error kinds (`-1` `ENOENT`, `-2` `EACCES`/`EPERM`, `-3` `EEXIST`, `-4` `EINVAL`/`ENAMETOOLONG`, `-5` `ETIMEDOUT`/`EAGAIN`, `-9` other; `SPEC-80 AXS-ELFS-041`). `SVC #0` preserves `X1..X7`, `X8`, `X19..X29`, `X30`, and `SP` (clobbering `X0` and volatile SIMD registers per kernel ABI).
- **`asm-generic/unistd.h` exclusivity (zero legacy x86/ARM32 syscalls):** Linux AArch64 omits deprecated legacy syscalls — `open`, `creat`, `stat`, `lstat`, `access`, `rename`, `mkdir`, `rmdir`, `unlink`, `readlink`, `dup2`, `pipe`, `fork`, `vfork`, `epoll_create`, `epoll_wait`, and `accept` **do not exist** on `aarch64-linux` and must never be emitted. All `*at`/modern `asm-generic/unistd.h` numbers are used with `AT_FDCWD = -100`:

| Subsystem | `aarch64-linux` Syscall Numbers (`X8`, `asm-generic/unistd.h`) |
|---|---|
| Console, File & FS | `SYS_dup3 = 24`, `SYS_mkdirat = 34`, `SYS_unlinkat = 35`, `SYS_ftruncate = 46`, `SYS_faccessat = 48`, `SYS_openat = 56`, `SYS_close = 57`, `SYS_pipe2 = 59`, `SYS_getdents64 = 61`, `SYS_lseek = 62`, `SYS_read = 63`, `SYS_write = 64`, `SYS_pread64 = 67`, `SYS_pwrite64 = 68`, `SYS_readlinkat = 78`, `SYS_newfstatat = 79`, `SYS_fstat = 80`, `SYS_fsync = 82`, `SYS_renameat2 = 276` |
| Virtual Memory | `SYS_brk = 214`, `SYS_munmap = 215`, `SYS_mremap = 216`, `SYS_mmap = 222`, `SYS_mprotect = 226`, `SYS_madvise = 233` |
| Process, Threads & Time | `SYS_exit = 93`, `SYS_exit_group = 94`, `SYS_futex = 98`, `SYS_nanosleep = 101`, `SYS_clock_gettime = 113`, `SYS_clock_nanosleep = 115`, `SYS_sched_yield = 124`, `SYS_rt_sigaction = 134`, `SYS_rt_sigprocmask = 135`, `SYS_getpid = 172`, `SYS_gettid = 178`, `SYS_clone = 220`, `SYS_execve = 221`, `SYS_wait4 = 260`, `SYS_getrandom = 278` |
| Async I/O & Sockets | `SYS_eventfd2 = 19`, `SYS_epoll_create1 = 20`, `SYS_epoll_ctl = 21`, `SYS_epoll_pwait = 22`, `SYS_socket = 198`, `SYS_bind = 200`, `SYS_listen = 201`, `SYS_connect = 203`, `SYS_getsockname = 204`, `SYS_setsockopt = 208`, `SYS_sendto = 206`, `SYS_recvfrom = 207`, `SYS_shutdown = 210`, `SYS_accept4 = 242`, `SYS_io_uring_setup = 425`, `SYS_io_uring_enter = 426` |

`SYS_fstat = 80` and `SYS_newfstatat = 79` populate the 128-byte generic Linux AArch64 `struct stat` (`st_mode: u32` at byte offset `16`, `st_size: i64` at byte offset `48`). [0193 §26; SPEC-04 AXS-EXT-110; SPEC-80 AXS-ELFS-040..049; T663]

**AXS-A64-045 — `std.sys.linux_aarch64` Host Interface, Stackful Fibers (`fiber_*`) & Freestanding Separation.** `std/sys/linux_aarch64` implements the complete `SPEC-04 AXS-EXT-110` host contract (`alloc`/`realloc`/`dealloc` via `SYS_mmap = 222` / `SYS_mremap = 216` / `SYS_munmap = 215`, console/file/fs I/O, `exe_path` via `SYS_readlinkat = 78` on `"/proc/self/exe"`, `monotonic_ns` via `SYS_clock_gettime = 113`, `thread_spawn` via `SYS_clone = 220` + `SYS_futex = 98`, and `io_uring`/`epoll` async I/O) while keeping OS startup and syscalls strictly outside the OS-independent `Arch.AArch64` backend (`0193 §26, §33 AARCH64-38`). Stackful fibers (`std/sys/linux_aarch64/fiber.ax`, `SPEC-34 AXS-EXEC-054`) context-switch the 160-byte 16-byte-aligned AAPCS64 callee-saved state (`X19..X28`, `X29`, `X30`, `SP`, and `D8..D15`) via `STP`/`LDP`. In `--profile freestanding` and `--profile kernel`, zero `std.sys.linux_aarch64` code is linked and `e_entry` binds directly to the user `@entry` function (`SPEC-52 AXS-FRE-003..010`). [0193 §26, §33 AARCH64-38; SPEC-04 AXS-EXT-110; SPEC-34 AXS-EXEC-054; SPEC-52 AXS-FRE-003..010]

**AXS-A64-046 — Linux AArch64 `_start` ELF Entry Stack ABI (`argc`, `argv`, `envp`, `auxv`).** At process entry on `aarch64-linux`, the kernel enters `_start` with `SP` 16-byte aligned pointing to `[argc: u64, argv[0..argc]: *const u8, NULL, envp[0..]: *const u8, NULL, auxv[0..]: Elf64_Auxv]` (and `X0` holding the dynamic loader `rtld_fini` callback in dynamic `PIE` mode or `0` in static mode) (`0193 §26–27`). In `--profile hosted`, `compiler/link/elf_aarch64` synthesizes `_start`:
1. Clear `MOV X29, #0` and `MOV X30, #0` to terminate AAPCS64 frame-pointer and DWARF unwind chains cleanly at the root frame.
2. Load `X1 = [SP]` (`argc`), compute `X2 = SP + 8` (`argv`) and `X3 = X2 + (X1 + 1) << 3` (`envp`), and store them into `__ax_linux_argc`, `__ax_linux_argv`, and `__ax_linux_envp` via `ADRP` + `STR` (`:lo12:`).
3. Maintain `SP % 16 == 0`, call the Axiom entry wrapper (`BL __ax_start_main` / `BL main`), move the `i32` exit code into `W0`, materialize `MOV X8, #94` (`SYS_exit_group`), execute `SVC #0`, and emit a trailing architectural trap `BRK #0x1` (`0xD420_0020`). [0193 §26–27; SPEC-80 AXS-ELFS-033; T663]

**AXS-A64-047 — `.eh_frame` / `.eh_frame_hdr` DWARF Unwind Metadata & `BRK` Trap ABI (`AARM-58`).** `compiler/obj/elf_aarch64` emits target-ABI-compliant DWARF Call Frame Information in `.eh_frame` (plus sorted binary-search `.eh_frame_hdr` `PT_GNU_EH_FRAME` when `--panic unwind` is enabled) without exposing unwind tables in Core semantics (`tasks/0521 §104, §156 AARM-58`, `SPEC-54`, `REQ-TGT-152`):
- **AArch64 DWARF CFI mapping:** `X0..X30` map to DWARF registers `0..30`, `SP` = `31`, `V0..V31` (`D8..D15`) = `64..95`, return-address column = `30` (`LR`), `CIE` code alignment factor = `4`, data alignment factor = `-8`, and FDE initial-location pointers use `DW_EH_PE_pcrel | DW_EH_PE_sdata4` (`R_AARCH64_PREL32`), recording `STP X29, X30, [SP, #-N]!` (`DW_CFA_def_cfa_offset N`, `DW_CFA_offset X29/X30`), `MOV X29, SP` (`DW_CFA_def_cfa_register 29`), and callee-saved `X19..X28`/`D8..D15` offsets.
- **Panic vs architectural trap separation (`SPEC-81 AXS-TGTD-033`):** Checked overflow, division by zero, bounds failure, `assert`, and `panic` lower to the Axiom panic runtime (`exit 101` under `--panic abort`, or DWARF stack unwinding with reverse-order `Drop` cleanup under `--panic unwind`), whereas explicit hardware traps (trap-mode `unreachable`, FFI no-unwind abort barrier `SPEC-54 AXS-PAN-010`, post-`_start` guard) emit `BRK #0x1` (`0xD420_0020`) or `UDF #0` (`0x0000_0000`). [tasks/0521 §104, §156 AARM-58; SPEC-54; SPEC-81 AXS-TGTD-033; REQ-TGT-152]

**AXS-A64-048 — Deterministic Codegen, `TargetFingerprint` Cache Identity & Optimization Isolation (`AARM-59..60, AARM-64..66`).** For a fixed source snapshot, `TargetFingerprint`, and optimization profile, AArch64 instruction selection, register allocation, 32-bit encoding, and ELF64 emission are byte-for-byte deterministic (`0193 §33 AARCH64-33`, `tasks/0521 §136, §156 AARM-59..60`, `REQ-TGT-153..154`). Incremental and artifact cache keys (`SPEC-22`, `SPEC-24`) include `(SemanticFingerprint, TargetId.AArch64Linux, TargetFeatureSet, CallConv.Aapcs64, OptProfile, CodegenFingerprint)` (`AARM-60`, `REQ-TGT-154`). Target-independent `OptIR` passes never depend on AArch64 instructions (`AARM-64`, `REQ-TGT-158`), target-dependent AArch64 scheduling/peepholes begin strictly after `LIR` target lowering (`AARM-65`, `REQ-TGT-159`), and unsupported operations either expand legally without altering semantics or emit `AX_TARGET_UNSUPPORTED_OP` (`AARM-66`, `REQ-TGT-160`). [0193 §33 AARCH64-33; tasks/0521 §124–128, §136, §149–150, AARM-59..60, AARM-64..66; REQ-TGT-153, REQ-TGT-154, REQ-TGT-158, REQ-TGT-159, REQ-TGT-160]

**AXS-A64-049 — E16.3 Cross-Target Conformance & Four-Layer Verification Matrix (`AARM-61..63, AARM-68..70`).** Certification of the `aarch64-linux` backend (`T662`–`T664`) enforces four orthogonal verification pillars (`0193 §28, §32`, `tasks/0521 §137–142, §151–158, AARM-61..63, AARM-68..70`, `REQ-TGT-155..157`, `REQ-TGT-162..165`):

| Verification Pillar | Gate / Suite | Asserted Contract |
|---|---|---|
| 1. ABI & Machine IR Verification | `ABIVerifier` + `verify_mc` (`tests/mc/aarch64_isel`) | `X/W` alias safety, `SP` vs `XZR` legality, `X30` save/restore, 16B `SP` alignment, `HFA`/`HVA` & `X8` `sret` lowering before encoding (`AARM-68..69`, `REQ-TGT-162..163`) |
| 2. 32-Bit Encoding & Disassembly Goldens | `EncoderVerifier` (`tests/encode/aarch64`) | `decode(encode(I)) == I` round-trip and reference disassembler byte vectors; golden assembly is quality testing, never semantic authority (`AARM-54, 61..62`, `REQ-TGT-148, 155..156`) |
| 3. ELF64 `EM_AARCH64` Relocation & Veneers | `verify_elf_image` (`tests/selfhost/obj`, `tests/selfhost/link`) | `ADRP`+`:lo12:` page crossings, `±128 MiB` `CALL26`/`JUMP26` veneers via `X16`, `GOT`/`PLT`, `TPIDR_EL0` TLS, `.eh_frame`, and byte-identical determinism (`AARM-55..59`) |
| 4. Differential Cross-ISA Execution | `tools/axtest.py` (`tests/conformance/p16/e16_3_aarch64_linux`) | Adversarial execution (overflow, div-by-zero, LL/SC & `+lse` atomics, volatile, `NaN`/`-0.0`, `HFA`, `X8` `sret`, closures, `dyn Trait`, `Drop`, TLS, NEON, UTF-8 `"Xin chào thế giới"`) under ARM64 Linux / `qemu-aarch64` matches `--interp` and `x86_64` byte-for-byte (`AARM-63`, `REQ-TGT-157, 165`) |

---

## 5. Diagnostics, Canonical Examples & Traceability (`AXS-A64-050`..`053`)

**AXS-A64-050 — Diagnostics Referenced by `SPEC-83`.** `aarch64-linux` reuses the canonical `DRIVER`, `TARGET`, `VERIFY`, `LINK`, `FFI`, `UNSAFE`, and `ICE` diagnostic codes (`spec/diagnostics.md` §10–11, `tasks/0521 §147–150`):

| Code | Area | Sev | Delivering Task | Condition on `aarch64-linux` |
|---|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | `T016`/`T654` | Unrecognized `--target <triple>` (`AXS-A64-001`) |
| `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | `error` | `T476`/`T654`/`T662` | Unknown feature name (e.g. `"avx2"` on `aarch64-linux`) or forbidden removal of baseline `-neon`/`-fp` on hosted `aarch64-linux` (`AXS-A64-003`) |
| `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | `error` | `T654`/`T662` | Contradictory feature toggles (e.g. `+sve,-neon`) (`AXS-A64-003`) |
| `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | `error` | `T476`/`T662` | Calling a `@target_feature("lse")` or `@target_feature("sve")` function from baseline code without `unsafe` or runtime feature guard (`AXS-A64-003`, `AXS-A64-035`) |
| `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | `error` | `T655`/`T662` | `LIR` operation cannot be legally expanded on the active AArch64 target/profile without altering semantics (`AXS-A64-048`, `AARM-66`) |
| `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | `error` | `T655`/`T662` | Deserialized Machine IR violates `verify_mc` (`SP`/`XZR` misuse, `X/W` class mismatch, misaligned `LDP`/`STP` or `SP`, missing `X30` save, or illegal `STXR` pair; `AXS-A64-037`) |
| `AX_LINK_BAD_OBJECT` | `LINK` | `error` | `T066`/`T663` | Malformed ELF64 `ET_REL` `.o` or external `.so` (`AXS-A64-040`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `T766`/`T663` | Input `.o`/`.a`/`.so`/`.axmi` has `e_machine != EM_AARCH64 (183)` or mismatched `TargetFingerprint` (`AXS-A64-040`, `AXS-A64-048`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `error` | `T027`/`T663` | `ADRP` (`±4 GiB`), `PREL32` (`±2 GiB`), `ADR` (`±1 MiB`), or non-relaxable relocation overflows its A64 field (`AXS-A64-041..042`) |
| `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | `error` | `T658`/`T663` | Non-PIC relocation (`R_AARCH64_ABS64`, `R_AARCH64_ABS32`) targets a read-only/executable segment in a `PIE` or `.so` link (`AXS-A64-040..041`) |
| `AX_ICE_INTERNAL` (`stage = "mc_verify"`) | `ICE` | `error` | `T655`/`T662` | Compiler-generated AArch64 Machine IR failed `verify_mc` or `ABIVerifier` before encoding (`AXS-A64-002`, `AXS-A64-037`) |

**AXS-A64-051 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: AAPCS64 HFA in V0..V2, >16-byte indirect sret in X8 (preserving X0 for the first int arg),
// view/mut_view capabilities, checked arithmetic, and UTF-8 output on --target aarch64-linux.
// Compiled with: axiomc build --target aarch64-linux aapcs64_demo.ax -o aapcs64_demo
module demo.aarch64_aapcs64

use std.io.println

@repr(C)
pub struct Vec3f {
    pub x: f32
    pub y: f32
    pub z: f32
}

@repr(C)
pub struct FrameSummary {
    pub tag: i64
    pub checksum: i64
    pub scaled_sum: i64
}

// AAPCS64: sret buffer address passed in X8 (XR); tag passed in X0 (NOT shifted to X1!);
// v passed as 3-element f32 HFA in S0, S1, S2 (AXS-A64-013..016).
pub fn summarize_hfa(tag: i64, v: Vec3f, weights: view<[i64]>) -> FrameSummary {
    let lane_total = ((v.x + v.y + v.z) as i64)
    let mut acc: i64 = 0
    let mut i: usize = 0
    while i < len(weights) {
        acc = acc + weights[i]
        i = i + 1
    }
    return FrameSummary {
        tag: tag
        checksum: lane_total + acc
        scaled_sum: tag * lane_total
    }
}

pub fn bump_in_place(summary: mut_view<FrameSummary>, delta: i64) {
    summary.checksum = summary.checksum + delta
}

pub fn main() -> i32 {
    println("Xin chào thế giới")
    let v = Vec3f { x: 2.0f32, y: 3.0f32, z: 5.0f32 }
    let w: [4]i64 = [1, 2, 3, 24]
    let mut out = summarize_hfa(4, v, view(w))
    bump_in_place(mut_view(out), 2)
    if out.checksum == 42 && out.scaled_sum == 40 {
        return 0
    }
    return 1
}
```

```axiom
// Example 2: Armv8.1-A +lse feature-gated atomic RMW (LDADDAL) and freestanding @entry _start
// Compiled with: axiomc build --target aarch64-linux --target-feature +lse lse_atomic.ax -o lse_atomic
module demo.aarch64_lse_atomic

use std.sync.atomic.{Atomic, Ordering}

@target_feature("lse")
pub fn add_seqcst_lse(counter: view<Atomic<u64>>, step: u64) -> u64 {
    return counter.fetch_add(step, Ordering.SeqCst)
}

pub fn main() -> i32 {
    let counter = Atomic<u64>.new(40u64)
    let prev = unsafe { add_seqcst_lse(view(counter), 2u64) }
    let now = counter.load(Ordering.Acquire)
    if prev == 40u64 && now == 42u64 {
        return 0
    }
    return 1
}
```

**AXS-A64-052 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Calling an Armv8.1-A @target_feature("lse") function from baseline Armv8.0-A code
// without unsafe or runtime feature detection is rejected (AX_TARGET_FEATURE_MISMATCH, AXS-A64-003).
module demo.aarch64_bad_lse_call

@target_feature("lse")
pub fn fast_cas_step(x: i64) -> i64 {
    return x + 1
}

pub fn baseline_caller(x: i64) -> i64 {
    return fast_cas_step(x) //~ ERROR AX_TARGET_FEATURE_MISMATCH
}
```

```axiom
// Example 2: Using an x86-only feature name on --target aarch64-linux is rejected at compile time
// with AX_TARGET_UNKNOWN_FEATURE (AXS-A64-003, AARM-67).
module demo.aarch64_bad_x86_feature

@target_feature("avx2") //~ ERROR AX_TARGET_UNKNOWN_FEATURE
pub fn wrong_isa_feature(x: i32) -> i32 {
    return x
}
```

**AXS-A64-053 — Requirement, Invariant & Task Traceability Matrix (`E16.3`: `REQ-TGT-113`..`REQ-TGT-165`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T661` | `SPEC-83`: Canonical AArch64 ISA `RegisterFile`, `CallConv.Aapcs64`, 32-bit encoding, NEON/atomics, `EM_AARCH64` ELF64 relocations/veneers & `std.sys.linux_aarch64` specification | `INV-AARCH-001`..`003` | `REQ-TGT-113`..`REQ-TGT-122` | `spec/SPEC-83-aarch64-linux.md` |
| `T662` | `compiler/abi/aapcs64` & `compiler/target/aarch64/isel`: AArch64 `TargetDesc`/`IsaTable`, `CallConv.Aapcs64` (`HFA`/`HVA`, `<=16`B, `X8` `sret`), `STP`/`LDP` frame lowering, scalar/FP/NEON/atomic/volatile ISel & `verify_mc` | `INV-AARCH-001` | `REQ-TGT-123`, `REQ-TGT-125`..`REQ-TGT-133`, `REQ-TGT-135`..`REQ-TGT-144` | `tests/mc/aarch64_isel`, `tests/selfhost/abi`, `tests/selfhost/isel` |
| `T663` | `compiler/target/aarch64/encode`, `compiler/obj/elf_aarch64`, `compiler/link/elf_aarch64` & `std/sys/linux_aarch64`: 32-bit A64 encoder, branch relaxation, `EM_AARCH64` ELF64 relocations, `±128 MiB` veneers, `.eh_frame`, `_start` & `SVC #0` syscalls | `INV-AARCH-002` | `REQ-TGT-134`, `REQ-TGT-148`..`REQ-TGT-154` | `tests/encode/aarch64`, `tests/selfhost/encode`, `tests/selfhost/obj`, `tests/selfhost/link` |
| `T664` | End-to-end E16.3 AArch64 encoding goldens, AAPCS64 ABI, ELF64 veneers & `x86_64` vs `aarch64` differential execution conformance suite | `INV-AARCH-003` | `REQ-TGT-155`..`REQ-TGT-165` | `tests/conformance/p16/e16_3_aarch64_linux` |

Detailed requirement mapping across `REQ-TGT-113`..`REQ-TGT-165` (`tasks/0521 §155–158`, `AARM-20..70`):

| Requirement(s) | Corpus Anchor | Canonical `SPEC-83` Rule(s) | Board Task(s) |
|---|---|---|---|
| `REQ-TGT-113`, `REQ-TGT-115` | `0521 §155`, `AARM-21` | `AXS-A64-002` (four-layer verification & zero x86 leakage in `LIR`) | `T661` |
| `REQ-TGT-114`, `REQ-TGT-116` | `AARM-20`, `AARM-22` | `AXS-A64-001` (`TargetId.AArch64Linux` & orthogonal `TargetBackend` contract) | `T661`, `T693` |
| `REQ-TGT-117`, `REQ-TGT-118` | `AARM-23`, `AARM-24` | `AXS-A64-004` (`X0..X30` / `W0..W30` `RegUnit` aliasing & upper-32 zeroing) | `T661` |
| `REQ-TGT-119`, `REQ-TGT-120` | `AARM-25`, `AARM-26` | `AXS-A64-005`, `AXS-A64-006` (dedicated `SP` vs `XZR`/`WZR` encoding `31`) | `T661` |
| `REQ-TGT-121`, `REQ-TGT-122` | `AARM-27`, `AARM-28` | `AXS-A64-011`, `AXS-A64-012`, `AXS-A64-028` (`NZCV` flags & semantic-preserving RA) | `T661` |
| `REQ-TGT-123`, `REQ-TGT-125`, `REQ-TGT-126` | `AARM-29`, `AARM-31..32` | `AXS-A64-013`..`017` (`X0..X7`, `V0..V7` `HFA`/`HVA`, `<=16`B composites, `X8` `sret`) | `T662`, `T694` |
| `REQ-TGT-124` | `AARM-30` | `AXS-A64-001`, `AXS-A64-009` (OS-independent ISA vs platform ABI & `X18` policy) | `T693`–`T696` (`E16.12`) |
| `REQ-TGT-127`..`REQ-TGT-131` | `AARM-33`..`AARM-37` | `AXS-A64-007`, `AXS-A64-018`..`021` (`X19..X28`/`D8..D15`, `LR`, `STP`/`LDP`, 16B `SP`, no red zone) | `T662`, `T693`, `T694` |
| `REQ-TGT-132`, `REQ-TGT-133`, `REQ-TGT-134` | `AARM-38`..`AARM-40` | `AXS-A64-029`, `AXS-A64-030`, `AXS-A64-041` (semantic LIR addr, A64 modes, `ADRP`+`:lo12:`) | `T662`, `T663` |
| `REQ-TGT-135`..`REQ-TGT-139` | `AARM-41`..`AARM-45` | `AXS-A64-003`, `AXS-A64-010`, `AXS-A64-028`, `AXS-A64-031`..`032` (NEON `V0..V31`, strict FP/FMA, `CSEL`) | `T662` |
| `REQ-TGT-140`..`REQ-TGT-144` | `AARM-46`..`AARM-50` | `AXS-A64-033`..`036` (`LDAR`/`STLR`, LL/SC `LDXR`/`STLXR`, `+lse`, `DMB ISH`, volatile/MMIO) | `T662` |
| `REQ-TGT-145`, `REQ-TGT-146`, `REQ-TGT-147` | `AARM-51`..`AARM-53` | `AXS-A64-003`, `AXS-A64-041`, `AXS-A64-043` (`TPIDR_EL0` TLS, `X16`/`X17` `GOT`/`PLT`, `pauth`) | `T658`, `T665`, `T687` |
| `REQ-TGT-148`..`REQ-TGT-154` | `AARM-54`..`AARM-60` | `AXS-A64-037`..`042`, `AXS-A64-044`..`048` (post-`verify_mc` 32b encode, relocs, veneers, `.eh_frame`, determinism, cache key) | `T663`, `T686`, `T690`–`T695` |
| `REQ-TGT-155`..`REQ-TGT-165` | `AARM-61`..`AARM-70`, `0521 §158` | `AXS-A64-002`..`003`, `AXS-A64-037`, `AXS-A64-048`..`049` (cross-ISA equivalence, optimization/feature/verifier gates, single `TargetBackend` contract) | `T664`, `T696` |

## Sources

0163 §1–22; 0193 §1–40 (`AARCH64-20..40`); `tasks/0518` §1–151 (`AMACHINE-20..120`); `tasks/0521` §1–158 (`AARM-20..70`); `tasks/0524` §1–113 (`ABACKEND-61..100`); `tasks/0784` §562.1–200; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-110`); `spec/SPEC-22-incremental-compilation.md`; `spec/SPEC-24-artifact-format-module-interfaces.md`; `spec/SPEC-31-atomics.md`; `spec/SPEC-34-executors-fibers.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-42-simd.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-73-inlining-specialization-devirt.md`; `spec/SPEC-77-regalloc-machine-opt.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-82-linux-elf-dynamic.md`; `spec/invariants.md` (`INV-TGTD-001..003`, `INV-AARCH-001..003`); `spec/diagnostics.md`; `ADR-0001`; `ADR-0002`; `ADR-0003`; `ADR-0011`.
