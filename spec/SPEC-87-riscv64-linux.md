# SPEC-87 — RISC-V 64 (RV64GC) Backend, LP64D psABI & Linux ELF64 Platform

**Status:** Canonical v0.1 | **Phase:** P16 (`E16.7`: `T677`–`T680`) | **Prefix:** `AXS-RV64-NNN`
**Sources:** `0152 §59`; `tasks/0522 §1–160` (`ABACKEND-20..60`); `tasks/0784 §562.135–140, §562.200`; `ADR-0003`; `SPEC-04`; `SPEC-31`; `SPEC-34`; `SPEC-40`; `SPEC-41`; `SPEC-42`; `SPEC-44`; `SPEC-50`; `SPEC-51`; `SPEC-52`; `SPEC-54`; `SPEC-55`; `SPEC-77`; `SPEC-80`; `SPEC-81`; `SPEC-82`; `SPEC-83`; `SPEC-86`; `spec/invariants.md` (`INV-RISCV-001`..`003`).

## Tóm tắt

Đặc tả này ấn định kiến trúc backend hạng nhất cho đích **`riscv64-linux`** (`TargetId.Riscv64Linux`: `Arch.RiscV64`, `Os.Linux`, `CallConv.RiscV`, `ObjectFormat.Elf64`) trên nền tập lệnh cơ sở mô-đun **`RV64GC`** (`RV64IMAFD_Zicsr_Zifencei_C`) cùng đồ thị mở rộng tường minh (`+v`, `+zba`, `+zbb`, `+zbc`, `+zbs`, `+zbkb`, `+zicond`, `+zacas`, mở rộng bảo mật và mở rộng tùy biến).
Tài liệu quy định chi tiết `DataLayout` 64-bit little-endian, `RegisterFile` (`x0..x31` với `x0` hằng `0` không cấp phát và `sp`/`gp`/`tp` dành riêng, `f0..f31` kèm bất biến **NaN-boxing** cho `f32`, `v0..v31` vector khả mở `RVV`), hạ tầng chọn lệnh **không thanh ghi cờ** (*flagless ISel*) với hợp nhất so sánh-nhánh, chuỗi kiểm tra tràn số nguyên hai thanh ghi, chia có rào chắn, nguyên tử RVWMO (`AMO*`, `LR`/`SC`, `FENCE`), `Volatile`/MMIO (`FENCE io, io`) và ép kiểu bão hòa dấu phẩy động bảo toàn `NaN -> 0`.
Phần ABI chuẩn hóa quy ước gọi hàm **`LP64D`** (`CallConv.RiscV`: mở rộng dấu bắt buộc cho cả `i32` lẫn `u32`, làm phẳng struct dấu phẩy động phần cứng `{FP}`/`{FP,FP}`/`{INT,FP}`/`{FP,INT}`, tách biên `a7` + ngăn xếp, truyền tham chiếu cho kiểu `> 16` byte, `sret` ẩn trong `a0`, hàm bất định tham số `...`, căn chỉnh ngăn xếp 16 byte không vùng đỏ và thăm dò trang 4 KiB).
Cuối cùng, đặc tả đóng đinh bộ kiểm chứng máy `verify_mc`, mở rộng giả lệnh, bộ mã hóa nhị phân 32-bit + nén 16-bit `RVC`, đối tượng/liên kết `ELF64` (`EM_RISCV = 243`, cặp định vị lại `R_RISCV_PCREL_HI20` + `R_RISCV_PCREL_LO12_I`/`S` chạy đúng không cần `R_RISCV_RELAX`), TLS Variant I qua `tp`, `.eh_frame` DWARF và giao diện nhân Linux `std.sys.linux_riscv64` (`ecall`).

---

## 1. Target Identity, Modular `RV64GC` Feature DAG, `DataLayout` & `RegisterFile` (`AXS-RV64-001`..`011`)

**AXS-RV64-001 — `TargetId.Riscv64Linux` & Orthogonal `TargetBackend` Contract (`ABACKEND-20, 60`).** `TargetId.Riscv64Linux` (`--target riscv64-linux`, CLI alias `riscv64-unknown-linux-gnu`) binds `(Arch.RiscV64, Os.Linux, CallConv.RiscV, ObjectFormat.Elf64)` (`SPEC-04 AXS-EXT-052`, `SPEC-81 AXS-TGTD-002`, where `CallConv.RiscV` is the canonical spelling of `SPEC-81`'s `CallConv.RiscvLp64d`). The backend implements the common `TargetBackend` compiler contract (`ABACKEND-20, 60`, `REQ-TGT-166`, `REQ-TGT-206`) with strict orthogonal separation across ISA lowering (`compiler/target/riscv64/isel`), calling convention (`compiler/abi/riscv64`), instruction encoding (`compiler/target/riscv64/encode`), ELF64 object emission (`compiler/obj/elf_riscv64`), static/dynamic ELF64 linking (`compiler/link/elf_riscv64`), and Linux host runtime (`std/sys/linux_riscv64`). Freestanding RISC-V targets (`Arch.RiscV64, Os.None`, `--profile freestanding` / `kernel`) reuse the ISA, ABI, verifier, and encoder without linking `std.sys.linux_riscv64` (`tasks/0522 §1, §151, §154`, `tasks/0784 §562.135–140`). [0152 §59; tasks/0522 §1, §151, §154, §159, ABACKEND-20, ABACKEND-60; tasks/0784 §562.135–140; SPEC-04 AXS-EXT-052; SPEC-81 AXS-TGTD-001..003; REQ-TGT-166, REQ-TGT-206]

**AXS-RV64-002 — Register-Neutral, Flagless & Address-Semantic `LIR` Boundary (`ABACKEND-21..25`).** Axiom `LIR` entering the RISC-V backend satisfies five architectural neutrality invariants (`tasks/0522 §15–17, §24–28, §33–34, §70–72, §156, §159, ABACKEND-21..25`, `SPEC-81 AXS-TGTD-029`, `REQ-TGT-167..171`):
1. `LIR` never encodes ISA-specific physical registers (`x0..x31`, `f0..f31`, `v0..v31`) (`ABACKEND-21`, `REQ-TGT-167`).
2. `LIR` never requires or assumes an ISA condition-code / flags register (`RFLAGS` or `NZCV`) (`ABACKEND-22`, `REQ-TGT-168`).
3. `LIR` models comparisons, conditional branches, selects, and checked-overflow operations in value/predicate form suitable for flagless two-register ISAs (`ABACKEND-23`, `REQ-TGT-169`).
4. `LIR` distinguishes fixed-width SIMD values from runtime-length scalable vector operations (`ABACKEND-24`, `REQ-TGT-170`).
5. `LIR` preserves structured semantic address expressions (`Base + Index * Scale + Offset` with alignment, provenance, volatility, and atomic ordering) until RV64 target lowering (`ABACKEND-25`, `REQ-TGT-171`). [tasks/0522 §15–17, §24–28, §33–34, §70–72, §156, §159, ABACKEND-21..25; SPEC-81 AXS-TGTD-029; REQ-TGT-167..171]

**AXS-RV64-003 — Modular `RV64GC` Baseline Expansion & Explicit `TargetFeatureSet` DAG (`ABACKEND-28..29, 48`).** `RV64I` is the architectural 64-bit integer root; hosted `riscv64-linux` defaults to **`RV64GC`**, expanded internally into modular explicit feature bits `{ i, m, a, f, d, zicsr, zifencei, c }` rather than an opaque monolith (`tasks/0522 §2–5, §159 ABACKEND-28`, `SPEC-81 AXS-TGTD-007..009`, `REQ-TGT-174`). Optional extensions form a validated prerequisite DAG:

| Feature Flag | Architectural Meaning | Implied Prerequisites |
|---|---|---|
| `+m`, `+a`, `+zicsr`, `+zifencei`, `+c` | Integer mul/div, atomics (`Zaamo`+`Zalrsc`), CSR access, `FENCE.I`, 16-bit `RVC` | `i` (mandatory in hosted `RV64GC`) |
| `+f`, `+d` | IEEE-754 single (`FLEN>=32`) and double (`FLEN=64`) hardware FP | `+f -> +zicsr`; `+d -> { +f, +zicsr }` |
| `+zba`, `+zbb`, `+zbc`, `+zbs`, `+zbkb` | Address generation (`SH1/2/3ADD`, `ADD.UW`), bit-manip (`CLZ`/`CTZ`/`CPOP`/`MIN`/`MAX`/`ORC.B`/`REV8`), carryless mul, single-bit ops, crypto bit-pack | `i` |
| `+zicond` | Integer conditional zero (`CZERO.EQZ`, `CZERO.NEZ`) | `i` |
| `+zacas` | Atomic compare-and-swap (`AMOCAS.W`, `AMOCAS.D`, 128-bit `AMOCAS.Q`) | `+a` |
| `+v` | RISC-V Vector 1.0 (`v0..v31`, `VLEN >= 128`, `ELEN = 64` application profile) | `{ +d, +zicsr }` |
| `+zicfiss`, `+zicfilp` | Shadow stack and indirect-branch landing pad CFI extensions (`tasks/0522 §95`) | `+zicsr` |

Vendor or custom extensions (`X*`) require an explicit `CustomExtensionDesc` declaring feature bit, opcode space, operand classes, clobbers, memory/CSR side effects, and disassembly format (`tasks/0522 §119–121, §124, ABACKEND-48`, `REQ-TGT-194`). Instructions lacking their required feature bit in the active `TargetFeatureSet` are **never** selected or encoded (`ABACKEND-29`, `REQ-TGT-175`). Unknown feature names (e.g. `"avx2"`, `"lse"`), contradictory toggles (e.g. `+d,-f` or `+v,-d`), or disabling mandatory `LP64D` baseline features (`-f`, `-d`, `-a`, `-m`) on hosted `riscv64-linux` are rejected with `AX_TARGET_UNKNOWN_FEATURE` or `AX_TARGET_FEATURE_CONFLICT`. [tasks/0522 §2–5, §95, §119–121, §124, §159, ABACKEND-28..29, ABACKEND-48; SPEC-44; SPEC-81 AXS-TGTD-007..009; REQ-TGT-174, REQ-TGT-175, REQ-TGT-194]

**AXS-RV64-004 — `riscv64-linux` `DataLayout` & Native Atomic Widths (`tasks/0522 §3, §31, §47, §55, §76, §83–84`).** `TargetId.Riscv64Linux` fixes `Endian.Little`, `XLEN = 64` (`pointer_width_bits = 64`, `usize`/`isize` = `64` bits), `FLEN = 64`, `stack_align = 16`, `red_zone = 0`, `max_Fundamental_align = 16`, and `page_size = 4096`:
- **Primitive `(size, align)` in bytes:** `bool`, `i8`, `u8` = `(1, 1)`; `i16`, `u16` = `(2, 2)`; `i32`, `u32`, `f32`, `char` = `(4, 4)`; `i64`, `u64`, `f64`, thin `*const T`/`*mut T`, `fn(...)` = `(8, 8)`; fat views/slices/`dyn Trait` pointers = `(16, 8)`; `i128`, `u128` = `(16, 16)` (`2 * XLEN` natural alignment per RISC-V psABI).
- **Lock-free atomic widths:** `{1, 2, 4, 8}` bytes (`bool`, `i8..i64`, `u8..u64`, thin pointers) are natively lock-free via `A`-extension `LR.{W,D}`/`SC.{W,D}` and `AMO*.{W,D}` (`SPEC-31 AXS-ATM-010`). `16`-byte (`i128`/`u128`) atomics are lock-free only when `+zacas` (`AMOCAS.Q` on even-odd GPR pairs) is enabled and otherwise lower via lock-sharded runtime helpers in hosted mode or emit `AX_TARGET_UNSUPPORTED_OP` where lock-free hardware execution is mandated. [tasks/0522 §3, §31, §47, §55, §76, §83–84; SPEC-31 AXS-ATM-010; SPEC-81 AXS-TGTD-005]

**AXS-RV64-005 — General-Purpose Integer `RegisterFile` (`x0..x31`) & Hardwired `x0` (`ABACKEND-45`).** `Arch.RiscV64` defines 32 64-bit integer registers `x0..x31` (`RegClass.GPR64`):

| Physical Regs | ABI Names | Role & Preservation | Allocatable? |
|---|---|---|---|
| `x0` | `zero` | Hardwired constant `0` (`ZeroReg`, `reg_unit_mask = 0`; writes discard result) | Never (`ZeroReg`) |
| `x1` | `ra` | Return address link register; caller-saved (saved in non-leaf prologues) | Scratch in body once saved |
| `x2` | `sp` | Stack pointer (`sp % 16 == 0` at calls/syscalls, `red_zone = 0`) | Never (`Reserved`) |
| `x3`, `x4` | `gp`, `tp` | Platform global pointer & Variant I TLS thread pointer | Never (`Reserved`) |
| `x5..x7`, `x28..x31` | `t0..t2`, `t3..t6` | Temporary registers; caller-saved (`t1`/`t3`/`t6` also stub/veneers scratch) | Yes |
| `x8` | `s0` / `fp` | Frame pointer / callee-saved register `0` | Only when FP omitted |
| `x9`, `x18..x27` | `s1`, `s2..s11` | Callee-saved general registers | Yes (callee-saved) |
| `x10..x11` | `a0..a1` | Integer/pointer arguments `0..1` & return values `0..1`; caller-saved | Yes |
| `x12..x17` | `a2..a7` | Integer/pointer arguments `2..7` (`a7` = Linux syscall number); caller-saved | Yes |

`x0` (`zero`) is a dedicated architectural sink/zero operand (`JAL x0, off`, `JALR x0, 0(ra)`, `ADDI rd, x0, imm`, `SLTU rd, x0, rs`) and **must never** be allocated by the register allocator to hold a live variable (`tasks/0522 §8, §100–102, ABACKEND-45`, `REQ-TGT-191`). [tasks/0522 §6–12, §100–102, ABACKEND-45; SPEC-81 AXS-TGTD-015..016; REQ-TGT-191]

**AXS-RV64-006 — Reserved Architectural Registers (`sp`, `gp`, `tp`, `s0/fp`) (`ABACKEND-45`).** `x2` (`sp`), `x3` (`gp`), and `x4` (`tp`) are permanently `Reserved` across all compilation profiles on `riscv64-linux`: compiler-generated instructions never allocate, spill, or clobber `gp` or `tp` (`tasks/0522 §10–12, §87–88, §101–102, ABACKEND-45`, `REQ-TGT-191`). `x8` (`s0`/`fp`) is `Reserved` whenever frame pointers are active (`-O0`, `--panic unwind`, functions with dynamic stack allocation, or `--frame-pointers=always`) and joins the callee-saved allocatable pool only when leaf/frame-pointer omission applies (`tasks/0522 §55–56`). [tasks/0522 §10–12, §55–56, §87–88, §101–102, ABACKEND-45; REQ-TGT-191]

**AXS-RV64-007 — Floating-Point `RegisterFile` (`f0..f31`) & `f32` NaN-Boxing Invariant.** With `+f` and `+d` active (`FLEN = 64`), `Arch.RiscV64` provides 32 64-bit floating-point registers `f0..f31` plus `fcsr` (`frm` + `fflags`):
- **Caller-saved FPRs:** `f0..f7` (`ft0..ft7`), `f10..f11` (`fa0..fa1`, FP args `0..1` and FP returns `0..1`), `f12..f17` (`fa2..fa7`, FP args `2..7`), and `f28..f31` (`ft8..ft11`).
- **Callee-saved FPRs:** `f8..f9` (`fs0..fs1`) and `f18..f27` (`fs2..fs11`).
- **`f32` NaN-Boxing Invariant (`tasks/0522 §13, §42–45`):** Whenever `+d` (`FLEN = 64`) is enabled, every single-precision `f32` value residing in an `f` register MUST be **NaN-boxed** with upper bits `[63:32] = 0xFFFF_FFFF` and the IEEE-754 binary32 payload in `[31:0]`. Hardware `FLW`, `FMV.W.X`, and `.S` arithmetic instructions automatically write `0xFFFF_FFFF` into `[63:32]`; consuming an improperly NaN-boxed 64-bit `f` register in a `.S` instruction interprets it as canonical quiet `NaN` (`0x7FC0_0000`). Bitcasts `u32 -> f32` MUST emit `FMV.W.X` (never `FMV.D.X`), and spilling/reloading a live `f32` uses `FSW`/`FLW` (or full 64-bit `FSD`/`FLD` preserving the NaN-box). [tasks/0522 §6–7, §13, §42–45; SPEC-41 AXS-FLT-001; SPEC-81 AXS-TGTD-015]

**AXS-RV64-008 — Scalable Vector `RegisterFile` (`v0..v31`) vs Fixed-Width SIMD (`ABACKEND-24, 44`).** When `+v` (`RVV 1.0`) is enabled, registers `v0..v31` (`v0` predicate mask register, plus control state `vl`, `vtype`, `vcsr`) are modeled as a dedicated runtime-length scalable `RegClass.VR` parameterized by `(SEW, LMUL)` via `vsetvli` / `vsetivli`, and **must never** be modeled as fixed-width 128/256/512-bit vector registers (`tasks/0522 §14, §70–75, ABACKEND-24, ABACKEND-44`, `REQ-TGT-170`, `REQ-TGT-190`). Fixed-width Core SIMD values (`SPEC-42`) lower to deterministic scalar/GPR/FPR code on baseline `RV64GC` or explicit `vsetivli`-bounded `vl` sequences under `+v`. [tasks/0522 §14, §70–75, ABACKEND-24, ABACKEND-44; SPEC-42; REQ-TGT-170, REQ-TGT-190]

**AXS-RV64-009 — Uniform 64-Bit GPR Width & `*W` Sign-Extending Word Operations (`tasks/0522 §3, §6, §18–23`).** Unlike `x86_64` (`EAX` zero-extends into `RAX`) and `AArch64` (`W0` zero-extends into `X0`), RV64 GPRs have no separate 32-bit subregister view: all GPR reads/writes observe 64 bits, and RV64 word instructions (`ADDIW`, `ADDW`, `SUBW`, `SLLIW`, `SRLIW`, `SRAIW`, `SLLW`, `SRLW`, `SRAW`, `MULW`, `DIVW`, `DIVUW`, `REMW`, `REMUW`, `LW`) **sign-extend bit 31 into bits `[63:32]`** (`SEXT.W rd, rs` = `ADDIW rd, rs, 0`). Zero-extending a 32-bit `u32` in a GPR into 64 bits requires `ADD.UW rd, rs, x0` (`+zba`) or `SLLI rd, rs, 32; SRLI rd, rd, 32` (or `LWU` when loading from memory). [tasks/0522 §3, §6, §18–23; SPEC-81 AXS-TGTD-015]

**AXS-RV64-010 — Semantically Transparent Register Allocation & Call Clobbers (`ABACKEND-32`).** Register allocation (`SPEC-77 AXS-RA-010`) maps virtual registers onto allocatable GPRs/FPRs — biasing hot short-lived values toward the `RVC` 3-bit compressible subset `x8..x15` (`s0..s1, a0..a5`) and `f8..f15` (`fs0..fs1, fa0..fa5`) when `+c` is enabled — while remaining 100% semantically transparent (`tasks/0522 §66–69, §113, §130, §147, ABACKEND-32`, `REQ-TGT-178`). Every `CALL` / `JALR ra` carries explicit clobber masks for `ra`, `t0..t6`, `a0..a7`, `ft0..ft11`, `fa0..fa7`, `fcsr` (and `v0..v31`, `vl`, `vtype` under standard non-vector `CallConv.RiscV` when `+v` is enabled). [tasks/0522 §66–69, §113, §130, §147, ABACKEND-32; SPEC-77 AXS-RA-010; SPEC-81 AXS-TGTD-019..020; REQ-TGT-178]

**AXS-RV64-011 — CPU Microarchitectural Cost Models & Peephole Soundness (`ABACKEND-41..42`).** CPU tuning profiles (`generic-rv64`, dual-issue in-order, out-of-order superscalar) guide instruction scheduling, `LUI+ADDI` / `AUIPC+ADDI` fusion placement, unrolling, and `+zicond` vs branch selection purely as code-quality decisions (`tasks/0522 §114–118, ABACKEND-42`, `REQ-TGT-188`). Target-specific peepholes (`MV` elision, redundant `SEXT.W` elimination across `*W` producers, `Zba`/`Zbb`/`Zbs` strength reduction) **never** alter Core overflow/div-zero panics, `f32` NaN-boxing, `Volatile` observability, or RVWMO atomic ordering (`ABACKEND-41`, `REQ-TGT-187`). [tasks/0522 §114–118, ABACKEND-41..42; SPEC-77 AXS-MCOPT-026; REQ-TGT-187, REQ-TGT-188]

---

## 2. Flagless Instruction Selection, Checked Arithmetic, Atomics & FP Lowering (`AXS-RV64-012`..`020`)

**AXS-RV64-012 — Flagless Integer Comparisons, Materialized Booleans & Branch Fusion (`ABACKEND-22..23`).** Because RISC-V has no condition-code register (`tasks/0522 §15–17, §24–27, §103–110, ABACKEND-22..23`, `REQ-TGT-168..169`), `compiler/target/riscv64/isel` lowers integer predicates by use context:
- **Materialized `bool` (`0` or `1` in GPR):** `a < b` -> `SLT rd, a, b` (`SLTU` unsigned, `SLTI`/`SLTIU` 12-bit signed immediate); `a > b` -> `SLT/SLTU rd, b, a`; `a <= b` -> `SLT/SLTU t, b, a; XORI rd, t, 1`; `a >= b` -> `SLT/SLTU t, a, b; XORI rd, t, 1`; `a == 0` -> `SEQZ rd, a` (`SLTIU rd, a, 1`); `a != 0` -> `SNEZ rd, a` (`SLTU rd, x0, a`); `a == b` / `a != b` -> `XOR t, a, b` followed by `SEQZ` / `SNEZ` (`SUB t, a, b` when `b` is not an immediate). Note that unsigned `u32` comparisons (`BLTU`/`BGEU`/`SLTU`) require operands to agree on upper-bit extension (both sign-extended per `LP64D` or both zero-extended — comparing `0x8000_0000` sign-extended `0xFFFF_FFFF_8000_0000` against `0x0000_0001` via `SLTU` yields `0` (`0xFFFF_FFFF_8000_0000 > 1`), preserving exact unsigned 32-bit order iff **both** operands are consistently sign-extended or both zero-extended!).
- **Compare-branch fusion (`tasks/0522 §103–110`):** When a comparison feeds a conditional branch with no materialized boolean consumer, ISel fuses both into a single `B`-type branch (`BEQ`, `BNE`, `BLT`, `BGE`, `BLTU`, `BGEU`, swapping `(rs1, rs2)` for `>` and `<=`) without allocating a temporary `0`/`1` GPR.
- **Conditional select (`Select(cond, t_val, f_val)`):** With `+zicond`, lowers to `CZERO.EQZ t0, t_val, cond; CZERO.NEZ t1, f_val, cond; OR rd, t0, t1`; on baseline `RV64GC`, lowers to a short branch diamond or mask select (`NEGW`/`SUB mask, x0, cond`). [tasks/0522 §15–17, §24–27, §103–110, ABACKEND-22..23; REQ-TGT-168, REQ-TGT-169]

**AXS-RV64-013 — Flagless Two-Register Checked Integer Overflow Sequences (`tasks/0522 §15–25, §134`).** Axiom checked integer arithmetic (`SPEC-40 AXS-INT-001`, `SPEC-81 AXS-TGTD-030`) lowers on RV64 without hardware overflow flags via exact flagless sequences:
- **Unsigned `u64` add / sub:** `ADD s, a, b; SLTU ovf, s, a; BNE ovf, x0, .Lpanic_ovf` (`u64` sub: `SLTU ovf, a, b; SUB d, a, b; BNE ovf, x0, .Lpanic_ovf`). For `u32`: zero-extend `a, b` to 64 bits, execute 64-bit `ADD`/`SUB`, and branch to `.Lpanic_ovf` if `(res >> 32) != 0`, then sign-extend bit 31 via `ADDIW rd, res, 0` when required by `LP64D`.
- **Signed `i64` add / sub:** `ADD s, a, b; SLT t0, s, a; SLT t1, b, x0; BNE t0, t1, .Lpanic_ovf` (`i64` sub: `SUB d, a, b; SLT t0, a, b; SLT t1, d, x0; BNE t0, t1, .Lpanic_ovf`). For `i32` (and `i8`/`i16`): compute 64-bit `ADD`/`SUB` on sign-extended 64-bit inputs, compute truncated `ADDIW s32, s64, 0` (or `SEXT.B`/`SEXT.H` / shift pair), and `BNE s64, s32, .Lpanic_ovf`.
- **Checked `mul`:** `u64`: `MUL lo, a, b; MULHU hi, a, b; BNE hi, x0, .Lpanic_ovf`; `i64`: `MUL lo, a, b; MULH hi, a, b; SRAI sign, lo, 63; BNE hi, sign, .Lpanic_ovf`; `i32`: `MUL p64, sext(a), sext(b); ADDIW p32, p64, 0; BNE p64, p32, .Lpanic_ovf`; `u32`: `MUL p64, zext(a), zext(b); SRLI hi, p64, 32; BNE hi, x0, .Lpanic_ovf`.
- **Checked `neg` & shift (`<<`, `>>`):** Signed `-a` branches to `.Lpanic_ovf` when `a == T.MIN` before `SUB`/`SUBW rd, x0, a`. Shifts check `BGEU shamt, bit_width, .Lpanic_shift` prior to `SLL`/`SLLW`/`SRL`/`SRLW`/`SRA`/`SRAW` (which mask hardware shift amounts to 5 or 6 bits). [tasks/0522 §15–25, §134; SPEC-40 AXS-INT-001; SPEC-81 AXS-TGTD-030]

**AXS-RV64-014 — Guarded Division/Remainder & 128-Bit Legalization (`ABACKEND-30`).** Because RISC-V `M`-extension `DIV`, `DIVU`, `DIVW`, `DIVUW`, `REM`, `REMU`, `REMW`, and `REMUW` **never trap in hardware** (`x / 0 == -1`, `x % 0 == x`, `T.MIN / -1 == T.MIN`, `T.MIN % -1 == 0`), lowering Axiom `/` and `%` MUST emit explicit pre-check branches (`BEQ divisor, x0, .Lpanic_div0`, plus `divisor == -1 && dividend == T.MIN -> .Lpanic_ovf` for signed types) before the `DIV*`/`REM*` instruction (`SPEC-40`, `SPEC-81 AXS-TGTD-030`). `128`-bit integers (`i128`, `u128`) legalize into `(lo, hi)` GPR pairs using flagless `SLTU` carry/borrow chains (`ADD lo, a_lo, b_lo; SLTU carry, lo, a_lo; ADD hi, a_hi, b_hi; ADD hi, hi, carry`, and `SLTU borrow, a_lo, b_lo; SUB lo, a_lo, b_lo; SUB hi, a_hi, b_hi; SUB hi, hi, borrow`), partial-product `MUL`/`MULHU` expansion, and pure-Axiom 128-bit division/remainder intrinsics (`ABACKEND-30`, `REQ-TGT-176`). Any `LIR` operation without a semantics-preserving legal expansion on the active target/profile is rejected cleanly with `AX_TARGET_UNSUPPORTED_OP` (`ABACKEND-30`, `REQ-TGT-176`). [tasks/0522 §18–21, §128, §134, ABACKEND-30; SPEC-40; SPEC-81 AXS-TGTD-029..032; REQ-TGT-176]

**AXS-RV64-015 — 64-Bit Constant Materialization & `+0x800` Sign-Extension Compensation (`tasks/0522 §23, §36–38`).** RV64 materializes integer constants deterministically by range:
1. **`[-2048, 2047]`:** Single `ADDI rd, x0, simm12` (compressible to `C.LI` for `[-32, 31]`).
2. **Signed 32-bit `[-2^31, 2^31 - 1]`:** `LUI rd, hi20` + `ADDIW rd, rd, lo12` where `hi20 = ((val + 0x800) >> 12) & 0xFFFFF` and `lo12 = sext12(val & 0xFFF)` (equivalently `sext32(val - (hi20 << 12)) ∈ [-2048, 2047]`). Here `+0x800` compensates for `ADDIW` sign-extending bit 11; in particular, for `val ∈ [0x7FFF_F800, 0x7FFF_FFFF]` (including `i32.MAX = 0x7FFF_FFFF`), `hi20 = 0x80000` (`LUI` loads `-0x8000_0000`) and `ADDIW` wraps modulo `2^32` with `lo12 ∈ [-2048, -1]` before sign-extending bit 31 (`0`) into bits `[63:32]`.
3. **Full 64-bit constants outside `[-2^31, 2^31 - 1]`:** Synthesized via deterministic upper-half materialization + `SLLI` + `ADDI` steps (at most 8 instructions, or `+zbs` `BSETI` single-bit powers of two) or a `.rodata` 8-byte literal load (`AUIPC` + `LD`). Specifically, positive 64-bit constants in `[0x0000_0000_7FFF_F800, 0x0000_0000_7FFF_FFFF]` MUST NOT use `LUI rd, 0x80000; ADDI rd, rd, lo12` directly because `LUI` sign-extends bit 31 on RV64 (`0xFFFF_FFFF_8000_0000`), requiring either `LUI + ADDIW` (per item 2, since bit 31 of the resulting 32-bit value is `0`), zero-extension (`ADD.UW` / shift pair), or `LI` shift-add synthesis. [tasks/0522 §23, §36–38]

**AXS-RV64-016 — `[rs1 + simm12]` Load/Store Addressing & `+zba` Indexed Lowering (`ABACKEND-25`).** RV64 base memory instructions (`LB`, `LBU`, `LH`, `LHU`, `LW`, `LWU`, `LD`, `SB`, `SH`, `SW`, `SD`, `FLW`, `FLD`, `FSW`, `FSD`) provide **only** register-plus-signed-12-bit-offset addressing `offset(rs1)` (`offset ∈ [-2048, 2047]`) (`tasks/0522 §28–35`). Target-independent `LIR` addresses (`Base + Index * Scale + Offset`, `ABACKEND-25`, `REQ-TGT-171`) lower to:
- Direct `offset(base)` when `Index` is absent and `Offset ∈ [-2048, 2047]`.
- `SH1ADD` / `SH2ADD` / `SH3ADD addr, idx, base` when `+zba` is enabled and `Scale ∈ {2, 4, 8}` (or `SLLI tmp, idx, log2(Scale); ADD addr, base, tmp` on baseline `RV64GC`), folding residual `Offset ∈ [-2048, 2047]` into `Offset(addr)`.
- Large displacements `Offset ∉ [-2048, 2047]`: when `Offset ∈ [-0x8000_0800, +0x7FFF_F7FF]` (`[-2^31 - 2048, +2^31 - 2049]`), split with `+0x800` carry compensation into `LUI t0, hi20; ADD t0, base, t0; LD/SD val, lo12(t0)` where `hi20 = ((Offset + 0x800) >> 12) & 0xFFFFF` and `lo12 = sext12(Offset & 0xFFF) ∈ [-2048, 2047]`. When `Offset ∉ [-0x8000_0800, +0x7FFF_F7FF]` — specifically including `[+0x7FFF_F800, +0x7FFF_FFFF]`, where `hi20 = 0x80000` causes 64-bit `LUI t0, 0x80000` to sign-extend to `-0x8000_0000` and `ADD` to miscompute the address by `-2^32` — materialize `Offset` into `t0` via `AXS-RV64-015` (`LUI + ADDIW` for `[+0x7FFF_F800, +0x7FFF_FFFF]`, or 64-bit `LI` synthesis outside `[-2^31, 2^31 - 1]`) followed by `ADD t0, base, t0; LD/SD val, 0(t0)`. [tasks/0522 §28–35, ABACKEND-25; REQ-TGT-171]

**AXS-RV64-017 — RVWMO `A`-Extension Atomics (`AMO*`, `LR`/`SC`, `FENCE`) (`ABACKEND-34`).** `compiler/target/riscv64/isel` lowers `SPEC-31` atomics onto the RISC-V Weak Memory Ordering (RVWMO) model (`tasks/0522 §76–84, ABACKEND-34`, `REQ-TGT-180`) over naturally aligned addresses:
- **Loads & Stores (`32`/`64`-bit `LW`/`LD`, `SW`/`SD`; `8`/`16`-bit `LB`/`LBU`/`LH`/`LHU`, `SB`/`SH`):**
  - `Relaxed`: plain load / store; `Acquire` load: `LW`/`LD` + `FENCE r, rw`; `Release` store: `FENCE rw, w` + `SW`/`SD`.
  - `SeqCst` (RISC-V Unprivileged Table A.6 trailing-sync/leading-sync mapping): `SeqCst` store emits `FENCE rw, w; SW/SD` (or `AMOSWAP.{W,D}.AQRL x0, val, (addr)`); `SeqCst` load emits `FENCE rw, rw; LW/LD; FENCE r, rw`, guaranteeing total `SeqCst` store-to-load `FENCE rw, rw` ordering across harts.
- **Read-Modify-Write (`fetch_add`, `fetch_sub` via `-val`, `fetch_and`, `fetch_or`, `fetch_xor`, `swap`, `fetch_min`/`max`):** `AMO{SWAP,ADD,XOR,AND,OR,MIN,MAX,MINU,MAXU}.{W,D}` with `.aq` (`Acquire`), `.rl` (`Release`), or `.aqrl` (`AcqRel` / `SeqCst`). Sub-word `8`/`16`-bit RMW and `fetch_nand` lower to a masked 32-bit aligned `LR.W`/`SC.W` loop.
- **Compare-Exchange (`CAS`):** Constrained forward-progress-guaranteed `LR.{W,D}` / `SC.{W,D}` loop (`<= 16` dynamic base instructions in the reservation set, zero loads/stores/FP/CSR/system ops inside the `LR`..`SC` window, and only forward conditional exit on mismatch; or single-instruction `AMOCAS.{W,D,Q}` when `+zacas` is active), applying `.aq`/`.rl` and `FENCE r, rw` on failure `Acquire`/`SeqCst`.
- **Fences:** `fence(Acquire)` -> `FENCE r, rw`; `fence(Release)` -> `FENCE rw, w`; `fence(AcqRel | SeqCst)` -> `FENCE rw, rw`; `compiler_fence` -> scheduling barrier emitting `0` instructions. [tasks/0522 §76–84, ABACKEND-34; SPEC-31 AXS-ATM-001..008, AXS-ATM-010, AXS-ATM-014..027, AXS-ATM-040..041; REQ-TGT-180]

**AXS-RV64-018 — `Volatile<T>` & `@at(...)` MMIO Ordering (`FENCE io, io`) (`ABACKEND-35`).** `Volatile<T>` and `Mmio<T>` (`SPEC-51`, `SPEC-55`) emit exact-width single-instruction memory operations (`LB`/`LBU`/`LH`/`LHU`/`LW`/`LWU`/`LD`, `SB`/`SH`/`SW`/`SD`) never dead-stripped, CSE-merged, widened, split, or reordered across volatile/atomic operations (`tasks/0522 §85–86, ABACKEND-35`, `REQ-TGT-181`). Because RVWMO separates memory bits (`r`, `w`) from device I/O bits (`i`, `o`), MMIO barrier intrinsics emit `FENCE io, io` (device-to-device) or `FENCE iorw, iorw` (DMA memory + MMIO serialization). [tasks/0522 §85–86, ABACKEND-35; SPEC-51; SPEC-55; REQ-TGT-181]

**AXS-RV64-019 — IEEE-754 `F`/`D` Floating-Point & `NaN -> 0` Saturating Casts (`tasks/0522 §42–46, §134`).** Floating-point operations (`SPEC-41`) lower to deterministic round-to-nearest-even (`rne`) `F`/`D` instructions (`FADD.{S,D}`, `FSUB.{S,D}`, `FMUL.{S,D}`, `FDIV.{S,D}`, `FSQRT.{S,D}`, `FSGNJ/FSGNJN/FSGNJX.{S,D}`, `FEQ/FLT/FLE.{S,D}`), emitting `FMADD.{S,D}` **only** on explicit `fma` calls (never silent contraction across `*` and `+`). Because RISC-V hardware `FCVT.{W,WU,L,LU}.{S,D} rd, fs1, rtz` maps `+Inf` **and `NaN` both to `+T.MAX`** whereas Axiom mandates **`NaN -> 0`** (`SPEC-41`, `SPEC-81 AXS-TGTD-031`), every saturating float-to-int cast `x as Int` MUST explicitly clear `NaN`: `FCVT.{W,WU,L,LU}.{S,D} rd, fs1, rtz; FEQ.{S,D} t0, fs1, fs1; BNE t0, x0, .Lok; LI rd, 0; .Lok:` (or `CZERO.EQZ rd, rd, t0` under `+zicond`), followed by range clamping for `i8`/`u8`/`i16`/`u16`. [tasks/0522 §42–46, §134; SPEC-41 AXS-FLT-001; SPEC-81 AXS-TGTD-031]

**AXS-RV64-020 — Inline Assembly Machine-Visible Effects (`ABACKEND-49`).** `unsafe` inline assembly on `riscv64` (`SPEC-50`) must declare all operand register classes (`r` GPR, `f` FPR, `v` RVV under `+v`), early-clobbers, explicit register clobbers, `"memory"` / `"fcsr"` side effects, and trap/diverging attributes (`tasks/0522 §122–124, ABACKEND-49`, `REQ-TGT-195`). Declaring `x0` as a writable value register, clobbering `sp`/`gp`/`tp` (or reserved `s0/fp`), or referencing disabled ISA registers fails closed before encoding. [tasks/0522 §122–124, ABACKEND-49; SPEC-50; REQ-TGT-195]

---

## 3. RISC-V `LP64D` Calling Convention (`CallConv.RiscV`) & Frame Layout (`AXS-RV64-021`..`031`)

**AXS-RV64-021 — `CallConv.RiscV` (`LP64D`) Boundary & Core Type Independence (`ABACKEND-26..27`).** `CallConv.RiscV` implements the official **RISC-V ELF psABI `LP64D`** (`XLEN = 64`, `FLEN = 64`) calling convention for both `extern "C"` FFI and default Axiom `fn` calls on `riscv64-linux` (`tasks/0522 §47–63, ABACKEND-26..27`, `SPEC-04 AXS-EXT-052`, `REQ-TGT-172..173`). Parameter and return classification is an exclusive `compiler/abi/riscv64` backend lowering concern and **never** a Core type-system rule (`ABACKEND-27, 58`, `REQ-TGT-173`, `REQ-TGT-204`). In freestanding profiles where hardware `f`/`d` are disabled (`Os.None`), `TargetDesc` selects the `LP64` integer-only psABI (`tasks/0522 §47`). [tasks/0522 §47–63, ABACKEND-26..27, ABACKEND-58; SPEC-04 AXS-EXT-052; REQ-TGT-172, REQ-TGT-173, REQ-TGT-204]

**AXS-RV64-022 — Integer/Pointer Registers (`a0..a7`) & Mandatory `i32`/`u32` Sign-Extension (`tasks/0522 §47–49`).** Up to 8 integer/pointer scalar slots are passed in `a0..a7` (`x10..x17`), and up to 2 integer/pointer return slots are returned in `a0, a1` (`x10, x11`). **Critical `LP64D` 32-Bit Sign-Extension Invariant:** Both signed `i32` **and unsigned `u32`** (and `char`) scalars passed in `a0..a7`, stack slots, or returned in `a0..a1` MUST be held **sign-extended from bit 31 into bits `[63:32]`** (`SEXT.W` = `ADDIW rd, rs, 0`; loading a `u32` via `LWU` zero-extends and MUST be followed by `ADDIW` or replaced by `LW` before crossing a `CallConv.RiscV` boundary). Narrower `< 32`-bit scalars (`bool`, `u8`, `u16` zero-extended; `i8`, `i16` sign-extended) are widened to 64 bits at call and return boundaries. [tasks/0522 §47–49; SPEC-50]

**AXS-RV64-023 — Floating-Point Scalar Arguments & Returns (`fa0..fa7`) (`tasks/0522 §47, §50–51`).** For named parameters under `LP64D`, up to 8 floating-point scalars (`f32` NaN-boxed with `[63:32] = 0xFFFF_FFFF`, `f64` in `[63:0]`) are passed in `fa0..fa7` (`f10..f17`) independently of `a0..a7`. If all 8 FPRs `fa0..fa7` are exhausted while GPRs `a0..a7` remain free, subsequent named scalar `f32`/`f64` arguments are passed in the next available GPR `a[g]` (`f32` in bits `[31:0]`, `f64` in `[63:0]`) before spilling to 8-byte stack slots (`riscv-elf-psabi-doc`, `tasks/0522 §50–51`). Scalar `f32` and `f64` return values use `fa0` (`f10`). [tasks/0522 §47, §50–51]

**AXS-RV64-024 — Hardware Floating-Point Struct Flattening (`{FP}`, `{FP, FP}`, `{INT, FP}`, `{FP, INT}`) (`tasks/0522 §50–52`).** For **named** arguments and return values under `LP64D`, trivial structs (recursively flattening nested structs and fixed arrays `[N]T`, excluding `union`s, misaligned `@repr(packed)` fields, zero-length bitfields, and non-trivial `Drop` types) undergo hardware FP flattening **before** general integer composite classification:
1. **`{ FP }` (1 leaf FP field `f32` or `f64`):** Passed in `fa[f]` if `>= 1` FPR is free; returned in `fa0`.
2. **`{ FP, FP }` (2 leaf FP fields, each `f32` or `f64`, including mixed `{f32, f64}` and `{f64, f32}`):** Passed in `(fa[f], fa[f+1])` iff **`>= 2` FPRs** remain available; returned in `(fa0, fa1)`. If `< 2` FPRs remain available, no partial FPR split occurs — the entire struct falls back to `AXS-RV64-025`.
3. **`{ INT, FP }` or `{ FP, INT }` (1 leaf integer/pointer scalar of width `<= 64` bits and 1 leaf FP scalar `f32` or `f64`):** Passed with the integer leaf in `a[g]` (widened/sign-extended per `AXS-RV64-022`) and the FP leaf in `fa[f]` (NaN-boxed if `f32`) iff **both `>= 1` GPR and `>= 1` FPR** remain available; returned in `(a0, fa0)` regardless of field declaration order. Otherwise falls back to `AXS-RV64-025`. [tasks/0522 §50–52]

**AXS-RV64-025 — General Composites `<= 16` Bytes, `i128`/`u128` & Split `a7` + Stack Boundary (`tasks/0522 §48–49, §52, §55`).** Zero-sized Axiom types (`size == 0`) consume `0` registers and `0` stack bytes. Scalars of width `2 * XLEN` (`i128`, `u128`, `size = 16, align = 16`) and non-FP-flattened trivial composites with `1 <= size <= 16` bytes classify as follows:
- **`1 <= size <= 8` bytes:** Packed little-endian into 1 GPR `a[g]` (or one 8-byte stack slot when `a0..a7` are full); returned in `a0`.
- **`9 <= size <= 16` bytes (including `i128`/`u128` and 16-byte views/fat pointers):** Passed in 2 consecutive GPRs `(a[g], a[g+1])` (`low 8` bytes in `a[g]`, `high` bytes in `a[g+1]`) when `>= 2` GPRs remain free. **Split `a7` Rule (named arguments):** When **exactly 1 GPR (`a7`)** remains free in a non-variadic argument slot, the low 8 bytes pass in `a7` and the upper 8 bytes pass at `[sp + 0]` on the stack. When `0` GPRs remain free, the value passes on the stack aligned to `max(8, align_of(T))` (`16` bytes for `i128`/`u128` and `@align(16)` structs). Returned in `(a0, a1)`. [tasks/0522 §48–49, §52, §55]

**AXS-RV64-026 — Composites `> 16` Bytes by Caller-Copy Reference & Hidden `sret` in `a0` (`tasks/0522 §52–54`).**
- **Arguments (`size > 16` bytes, or types with non-trivial `Drop` / pinned address identity):** The caller allocates an aligned temporary copy in its own stack frame (`max(8, align_of(T))`) and passes the 64-bit address as a single pointer argument in `a[g]` (or an 8-byte pointer slot on the stack if `a0..a7` are full) — large structs are **never** copied inline into outgoing stack slots (`tasks/0522 §52`).
- **Indirect return (`sret`, `size > 16` bytes):** Returned in the same manner as a first named argument: the caller allocates result storage and passes the hidden pointer in **`a0` (`x10`)**, consuming `a0` so explicit GPR parameters start at `a1..a7` (`tasks/0522 §53–54`; contrast AArch64 `X8`). [tasks/0522 §52–54]

**AXS-RV64-027 — Variadic `extern "C" fn(fixed..., ...)` Rules & `va_list` (`tasks/0522 §47–48, §55, §140`).** Named arguments preceding `...` follow normal `LP64D` rules (`AXS-RV64-022..026`). Variadic arguments at and after `...` **never** use FPRs `fa0..fa7`; instead, they follow the base integer convention (`a0..a7` then stack, with C default promotions `f32 -> f64`, `<32`-bit ints -> sign-extended 32-bit in GPR). Any variadic (`...`) argument with `16`-byte (`2 * XLEN`) alignment and `size <= 16` (`i128`, `u128`, `@align(16)` struct) MUST be passed in an **even-aligned GPR pair** `(a0:a1, a2:a3, a4:a5, a6:a7)` (skipping `a[2k+1]` if odd; if only `a7` remains, `a7` is left unused and the full 16 bytes go to a 16-byte-aligned stack offset). Consequently, a variadic callee spills remaining `a[k]..a7` contiguously below incoming `[sp + 0]`, and `va_list` on `riscv64-linux` is a single 8-byte pointer `*mut u8` (`size = 8, align = 8`). [tasks/0522 §47–48, §55, §140; SPEC-50]

**AXS-RV64-028 — Outgoing Stack Argument Layout (`tasks/0522 §48, §55`).** Stack-passed arguments are laid out in left-to-right parameter order starting at `[sp + 0]` in the caller's pre-allocated outgoing argument region. Every stack slot is a multiple of `8` bytes aligned to at least `8` bytes, and `16`-byte-aligned arguments pad upward to the next `16`-byte boundary relative to `sp`. [tasks/0522 §48, §55]

**AXS-RV64-029 — Callee-Saved Preservation, 16-Byte `sp` Alignment & Zero Red Zone (`ABACKEND-33`).** Callees preserve `sp` (`x2`), `s0..s11` (`x8..x9`, `x18..x27`), and `fs0..fs11` (`f8..f9`, `f18..f27`). `sp` MUST satisfy `sp % 16 == 0` at every `CALL` / `JALR ra` and `ECALL` boundary (`tasks/0522 §55–57, §131, ABACKEND-33`, `REQ-TGT-179`). `riscv64-linux` defines **zero red zone (`red_zone = 0`)**: compiler-generated code must never read or write any byte at `[sp - k]` (`k > 0`) below the current `sp` (`tasks/0522 §55`). [tasks/0522 §55–57, §131, ABACKEND-33; REQ-TGT-179]

**AXS-RV64-030 — Canonical RV64 Frame Layout, Prologue/Epilogue & Leaf Elision (`ABACKEND-33`).** For a non-leaf function (or a leaf function with spills/locals), `frame_size` is rounded up to a multiple of `16` bytes:
1. **Prologue:** Decrement `sp` by `frame_size` (`ADDI sp, sp, -frame_size` / `C.ADDI16SP` for `frame_size <= 2048`, or `LI t0, -frame_size; ADD sp, sp, t0` for larger frames after probing), store `SD ra, (frame_size - 8)(sp)` and `SD s0, (frame_size - 16)(sp)`, establish `ADDI s0, sp, frame_size` when frame pointers are active (`[s0 - 8] == saved ra`, `[s0 - 16] == prev s0`, matching the standard RISC-V psABI frame chain), and save modified `s1..s11` and `fs0..fs11`.
2. **Epilogue:** Restore `fs0..fs11`, `s1..s11`, `s0`, and `ra`, increment `sp` by `frame_size`, and execute `RET` (`JALR x0, 0(ra)` / `C.JR ra`).
3. **Leaf elision:** Pure leaf functions requiring `0` stack bytes and modifying no callee-saved registers omit `sp`, `ra`, and `s0` instructions completely (`tasks/0522 §58–60`). [tasks/0522 §55–63, §131, ABACKEND-33; REQ-TGT-179]

**AXS-RV64-031 — 4 KiB Stack Guard-Page Probing (`ADR-0003`, `tasks/0522 §55, §131`).** Whenever a static frame allocation or dynamic stack allocation exceeds `4096` bytes (`page_size`), the prologue emits a deterministic downward loop touching every `4096`-byte page (`ADDI t0, sp, -4096; SD x0, 0(t0)` repeated before final `sp` commit) so safe Axiom code can never jump over the OS stack guard page (`ADR-0003`, `tasks/0522 §55, §131`, `SPEC-81 AXS-TGTD-037`, `SPEC-83 AXS-A64-021`). [ADR-0003; tasks/0522 §55, §131; SPEC-81 AXS-TGTD-037; SPEC-83 AXS-A64-021]

---

## 4. Machine Verification, RV64GC + `RVC` Encoding, ELF64 `EM_RISCV` Linking & TLS (`AXS-RV64-032`..`042`)

**AXS-RV64-032 — Mandatory Pre-Encoding Machine Verification (`verify_mc`) (`ABACKEND-31, 50`).** `verify_mc` executes after register allocation, prologue/epilogue insertion, and pseudo expansion, and **strictly before** binary encoding (`tasks/0522 §100–102, §148–150, ABACKEND-31, ABACKEND-50`, `SPEC-81 AXS-TGTD-036..038`, `REQ-TGT-177`, `REQ-TGT-196`). It enforces:
1. Zero surviving virtual registers and exact `RegClass` (`GPR64` vs `FPR64` vs `VR`) compatibility on every operand.
2. Zero live value definitions assigned to `x0`, zero writes/clobbers to reserved `gp`/`tp` (and `s0` when frame-pointer reserved), and `sp % 16 == 0` at every `CALL`/`JALR ra` and `ECALL`.
3. `ra` save/restore balance in non-leaf functions and balanced callee-saved `s0..s11`/`fs0..fs11` spills/reloads.
4. Exact immediate bounds/alignments (`simm12`, 6-bit RV64 `shamt`, even `B`/`J` offsets, non-zero `RVC` `nzimm` constraints, `r'` ∈ `x8..x15`/`f8..f15`), legal constrained `LR`/`SC` windows (`AXS-RV64-017`), and active `TargetFeatureSet` coverage (`ABACKEND-29`).
Compiler-generated violations fail closed with `AX_ICE_INTERNAL` (`stage = "mc_verify"`, exit code `3`, zero artifact output); deserialized/hand-written Machine IR tests report `AX_VERIFY_MC_ILLEGAL` (`ABACKEND-50`, `REQ-TGT-196`). [tasks/0522 §100–102, §148–150, ABACKEND-31, ABACKEND-50; SPEC-81 AXS-TGTD-036..038; REQ-TGT-177, REQ-TGT-196]

**AXS-RV64-033 — Pseudo-Instruction Expansion Before Final Encoding (`ABACKEND-46`).** All architectural and compiler pseudo-instructions (`LI`, `LA`, `LLA`, `MV` -> `ADDI rd, rs, 0`, `NOT` -> `XORI rd, rs, -1`, `NEG`/`NEGW` -> `SUB`/`SUBW rd, x0, rs`, `SEXT.W` -> `ADDIW rd, rs, 0`, `SEQZ`/`SNEZ`/`SLTZ`/`SGTZ`, `FMV.S`/`FABS.S`/`FNEG.S` -> `FSGNJ*`, `FMV.D`/`FABS.D`/`FNEG.D`, `J` -> `JAL x0, off`, `JR` -> `JALR x0, 0(rs)`, `RET` -> `JALR x0, 0(ra)`, `CALL`/`TAIL` -> `AUIPC ra/t1` + `JALR ra/x0`) MUST be expanded into concrete verified machine instructions before entering the final byte encoder (`tasks/0522 §63–65, ABACKEND-46`, `REQ-TGT-192`). [tasks/0522 §63–65, ABACKEND-46; REQ-TGT-192]

**AXS-RV64-034 — Little-Endian RV64GC 32-Bit Base Instruction Formats (`R`, `R4`, `I`, `S`, `B`, `U`, `J`) (`tasks/0522 §64–65, §149–150`).** All 32-bit RV64 instructions carry bits `[1:0] == 0b11` (`[4:2] != 0b111`), are 2-byte parcel-aligned (`4`-byte aligned when `-c`), and serialize little-endian across seven canonical formats (`compiler/target/riscv64/encode`):

| Format | Bit Layout `[31 .. 0]` | Representative RV64GC Instructions |
|---|---|---|
| `R` | `funct7[31:25] \| rs2[24:20] \| rs1[19:15] \| funct3[14:12] \| rd[11:7] \| opcode[6:0]` (`AMO`: `funct5[31:27]\|aq[26]\|rl[25]`) | `ADD`/`SUB`/`ADDW`/`SUBW`/`SLT`/`SLTU`, `MUL*`/`DIV*`/`REM*`, `AMO*`/`LR`/`SC`, `FADD*`/`FEQ*` |
| `R4` | `rs3[31:27] \| fmt[26:25] \| rs2[24:20] \| rs1[19:15] \| rm[14:12] \| rd[11:7] \| opcode[6:0]` | `FMADD.{S,D}`, `FMSUB.{S,D}`, `FNMSUB.{S,D}`, `FNMADD.{S,D}` |
| `I` | `imm[11:0][31:20] \| rs1[19:15] \| funct3[14:12] \| rd[11:7] \| opcode[6:0]` (RV64 shifts: `shamt[5:0]` in `[25:20]`) | `ADDI`/`ADDIW`/`SLTI`/`SLTIU`, `LB..LD`/`LWU`/`FLW`/`FLD`, `JALR`, `ECALL`/`EBREAK`, `FENCE`, `CSR*` |
| `S` | `imm[11:5][31:25] \| rs2[24:20] \| rs1[19:15] \| funct3[14:12] \| imm[4:0][11:7] \| opcode[6:0]` | `SB`, `SH`, `SW`, `SD`, `FSW`, `FSD` |
| `B` | `imm[12][31] \| imm[10:5][30:25] \| rs2[24:20] \| rs1[19:15] \| funct3[14:12] \| imm[4:1][11:8] \| imm[11][7] \| opcode[6:0]` | `BEQ`, `BNE`, `BLT`, `BGE`, `BLTU`, `BGEU` (`±4 KiB`, `imm[0] = 0`) |
| `U` | `imm[31:12][31:12] \| rd[11:7] \| opcode[6:0]` | `LUI` (`0x37`), `AUIPC` (`0x17`) |
| `J` | `imm[20][31] \| imm[10:1][30:21] \| imm[11][20] \| imm[19:12][19:12] \| rd[11:7] \| opcode[6:0]` | `JAL` (`0x6F`, `±1 MiB`, `imm[0] = 0`) |

Every encoded instruction satisfies deterministic `decode(encode(I)) == I` round-trip verification (`tasks/0522 §64–65, §149–150`). [tasks/0522 §64–65, §149–150; SPEC-81 AXS-TGTD-035]

**AXS-RV64-035 — 16-Bit `RVC` Compressed Instruction Encoding (`C` Extension) (`ABACKEND-43`).** When `+c` is enabled (default in `RV64GC`), eligible relocation-free instructions deterministically compress into 16-bit little-endian parcels (`op[1:0] ∈ {0b00, 0b01, 0b10}`, formats `CR`, `CI`, `CSS`, `CIW`, `CL`, `CS`, `CA`, `CB`, `CJ`, with 3-bit `r' = reg - 8` addressing `x8..x15` and `f8..f15`) (`tasks/0522 §39–41, §111–113, ABACKEND-43`, `REQ-TGT-189`):
- **Supported RV64C subset:** `C.ADDI4SPN`, `C.ADDI16SP` (`nzimm != 0`, 16-byte step), `C.LW`/`C.LD`/`C.FLD`, `C.SW`/`C.SD`/`C.FSD`, `C.LWSP`/`C.LDSP` (`rd != x0`), `C.FLDSP`, `C.SWSP`/`C.SDSP`/`C.FSDSP`, `C.LI`, `C.LUI` (`rd ∉ {x0, x2}`, `nzimm != 0`), `C.ADDI`, `C.ADDIW`, `C.SLLI`, `C.SRLI`/`C.SRAI`, `C.ANDI`, `C.MV` (`rd != x0, rs2 != x0`), `C.ADD`, `C.SUB`/`C.XOR`/`C.OR`/`C.AND`/`C.SUBW`/`C.ADDW`, `C.J` (`±2 KiB`), `C.BEQZ`/`C.BNEZ` (`±256 B`, `rs1' ∈ x8..x15`), `C.JR` (`rs1 != x0`), `C.JALR` (`rs1 != x0`), `C.EBREAK` (`0x9002`), and `C.UNIMP` (`0x0000`). RV32-only `C.JAL` and `C.FLW`/`C.FSW`/`C.FLWSP`/`C.FSWSP` (reassigned on RV64C to `C.ADDIW` and `C.LD`/`C.SD`/`C.LDSP`/`C.SDSP`) MUST NEVER be emitted on RV64.
- **Semantic neutrality (`ABACKEND-43`):** `RVC` compression is strictly an encoding/code-size optimization; disabling `-c` or running at `-O0` produces identical observable program behavior (`REQ-TGT-189`). [tasks/0522 §39–41, §111–113, ABACKEND-43; REQ-TGT-189]

**AXS-RV64-036 — Branch Relaxation & Inter-Section Call Range Extension (`tasks/0522 §25, §29, §61, §90–94, §109–110`).** Intra-function `C.BEQZ`/`C.BNEZ` branches exceeding `±256 B` widen to 32-bit `BEQ`/`BNE` (`±4 KiB`), and `B`-type conditional branches exceeding `±4 KiB` relax deterministically to an inverted `B`-type branch (`+8` bytes) skipping an unconditional `JAL x0, target` (`±1 MiB`) or `AUIPC t6, hi20; JALR x0, lo12(t6)` (`±2 GiB`), updating all label offsets and `.eh_frame` `DW_CFA_advance_loc` deltas before emission. Inter-section direct calls emit `AUIPC ra, %pcrel_hi(sym); JALR ra, %pcrel_lo(1b)(ra)` (`R_RISCV_CALL_PLT = 19`, `±2 GiB`), or linker-synthesized range-extension stubs via caller-saved `t1`/`t3`. [tasks/0522 §25, §29, §61, §90–94, §109–110]

**AXS-RV64-037 — ELF64 `EM_RISCV` Object Serialization, `e_flags` & `.riscv.attributes` (`ABACKEND-38`).** Object serialization (`compiler/obj/elf_riscv64`) is strictly separated from instruction encoding (`tasks/0522 §89–90, §141, ABACKEND-38`, `REQ-TGT-184`):
- **ELF64 Header:** `ELFCLASS64 = 2`, `ELFDATA2LSB = 1`, `e_machine = EM_RISCV = 243`, `SHT_RELA` relocations with explicit signed `r_addend`, and `PT_GNU_STACK` (`PF_R | PF_W`, non-executable).
- **`e_flags`:** `EF_RISCV_RVC (0x0001)` when `+c` is enabled, ORed with float-ABI bits `EF_RISCV_FLOAT_ABI_DOUBLE (0x0004)` for `LP64D` (`e_flags = 0x0005` on baseline `RV64GC` `LP64D`; `EF_RISCV_FLOAT_ABI_SOFT = 0x0000` for freestanding `LP64`).
- **`.riscv.attributes` section:** `sh_type = SHT_RISCV_ATTRIBUTES = 0x7000_0003`, format version `'A'` (`0x41`), vendor `"riscv\0"`, file sub-subsection (`Tag_file = 1`) recording `Tag_RISCV_stack_align (4) = 16` and canonical normalized `Tag_RISCV_arch (5)` string (baseline `"rv64i2p1_m2p0_a2p1_f2p2_d2p2_c2p0_zicsr2p0_zifencei2p0"` plus enabled sorted extensions). [tasks/0522 §89–90, §141, ABACKEND-38; SPEC-80 AXS-ELFS-021; REQ-TGT-184]

**AXS-RV64-038 — Explicit `EM_RISCV` Relocations & Paired `PCREL_HI20` / `PCREL_LO12` Indirection (`ABACKEND-37`).** `compiler/obj/elf_riscv64` and `compiler/link/elf_riscv64` implement explicit RISC-V ELF psABI relocation semantics (`tasks/0522 §29–30, §89–94, §141, ABACKEND-37`, `REQ-TGT-183`):

| Relocation (`r_type`) | ID | Field / Formula (`V` before `+0x800` split) |
|---|---:|---|
| `R_RISCV_NONE` / `R_RISCV_32` / `R_RISCV_64` | `0` / `1` / `2` | None / `word32 = S + A` / `word64 = S + A` |
| `R_RISCV_RELATIVE` / `R_RISCV_COPY` / `R_RISCV_JUMP_SLOT` | `3` / `4` / `5` | Dynamic `B + A` / copy / `.got.plt` lazy/eager PLT slot |
| `R_RISCV_TLS_DTPMOD64` / `R_RISCV_TLS_DTPREL64` / `R_RISCV_TLS_TPREL64` | `7` / `9` / `11` | Dynamic 64-bit TLS module ID / DTP-relative (`S+A-0x800`) / TP-relative (`S+A+tls_off`) |
| `R_RISCV_BRANCH` / `R_RISCV_JAL` | `16` / `17` | `B`-type `±4 KiB` (`S + A - P`) / `J`-type `±1 MiB` (`S + A - P`) |
| `R_RISCV_CALL` / `R_RISCV_CALL_PLT` | `18` / `19` | `AUIPC + JALR` pair (`S + A - P`, `±2 GiB`, direct or PLT-eligible) |
| `R_RISCV_GOT_HI20` / `R_RISCV_TLS_GOT_HI20` / `R_RISCV_TLS_GD_HI20` | `20` / `21` / `22` | `U`-type `AUIPC` high 20 bits of `G + GOT - P` (GOT / TLS IE / TLS GD) |
| `R_RISCV_PCREL_HI20` / `R_RISCV_PCREL_LO12_I` / `R_RISCV_PCREL_LO12_S` | `23` / `24` / `25` | `U`-type `hi20(S + A - P)` / `I`-type `lo12` / `S`-type `lo12` (**via `AUIPC` label**) |
| `R_RISCV_TPREL_HI20` / `LO12_I` / `LO12_S` / `TPREL_ADD` | `29` / `30` / `31` / `32` | Static TLS `LE`: `hi20(S+A-tp)` / `I`-type `lo12` / `S`-type `lo12` / `ADD rd, rs1, tp` tag |
| `R_RISCV_ADD32` / `R_RISCV_SUB32` / `R_RISCV_32_PCREL` | `35` / `39` / `57` | `word32 += S + A` / `word32 -= S + A` / `word32 = S + A - P` (`.eh_frame` / tables) |
| `R_RISCV_RVC_BRANCH` / `R_RISCV_RVC_JUMP` / `R_RISCV_RELAX` | `44` / `45` / `51` | `CB`-type `±256 B` / `CJ`-type `±2 KiB` / optional linker-relaxation marker |

**Critical Paired `PCREL_LO12` Indirection Rule:** In `.Lpcrel_hiN: auipc rd, %pcrel_hi(sym + A)`, `AUIPC` carries `R_RISCV_PCREL_HI20` (or `GOT_HI20` / `TLS_GOT_HI20` / `TLS_GD_HI20`) referencing `sym` with `r_addend = A`, whereas the paired `I`-type (`R_RISCV_PCREL_LO12_I = 24`) or `S`-type (`R_RISCV_PCREL_LO12_S = 25`) consumer MUST set **`r_sym` to the local `.Lpcrel_hiN` symbol at the `AUIPC` instruction** (`r_addend = 0`, or explicit offset per psABI). The linker locates the `HI20` relocation at `P_auipc = S(.Lpcrel_hiN)`, computes $V = S_{\text{target}} + A_{\text{hi}} - P_{\text{auipc}} \in [-\text{0x8000\_0800}, +\text{0x7FFF\_F7FF}]$, patches `AUIPC` with $\text{hi20}(V) = ((V + \text{0x800}) \gg 12) \ \& \ \text{0xFFFFF}$, and patches the `LO12` consumer with $\text{lo12}(V) = \text{sext12}(V \ \& \ \text{0xFFF}) = V - (\text{sext}(\text{hi20}(V)) \ll 12) \in [-2048, 2047]$. Overflow ($V \notin [-\text{0x8000\_0800}, +\text{0x7FFF\_F7FF}]$) emits `AX_LINK_RELOC_OUT_OF_RANGE`. [tasks/0522 §29–30, §89–94, §141, ABACKEND-37; REQ-TGT-183]

**AXS-RV64-039 — Relaxation-Independent Relocation Sequences (`ABACKEND-47`).** Every relocation-bearing sequence emitted by `compiler/target/riscv64` (`AUIPC + ADDI/LD/SD`, `AUIPC + JALR`, `LUI + ADD + ADDI/LD/SD` TLS `LE`) MUST be complete and architecturally valid **without** optional linker relaxation (`R_RISCV_RELAX = 51` or `gp` `__global_pointer$` rewriting) (`tasks/0522 §91–94, ABACKEND-47`, `REQ-TGT-193`). `compiler/link/elf_riscv64` safely ignores `R_RISCV_RELAX` markers in external C/assembly `.o`/`.a` inputs by default, guaranteeing deterministic layout without code-shrinking multi-pass hazards. [tasks/0522 §91–94, ABACKEND-47; REQ-TGT-193]

**AXS-RV64-040 — Static, `PIE` & `.so` ELF64 Linking (`GOT`, `PLT`, `/lib/ld-linux-riscv64-lp64d.so.1`).** `compiler/link/elf_riscv64` links static executables (`ET_EXEC` / `static-pie`), dynamic `PIE` executables (`PT_INTERP = "/lib/ld-linux-riscv64-lp64d.so.1\0"`), and shared libraries (`ET_DYN` `.so`) with `PT_GNU_RELRO` (`DF_BIND_NOW`), zero `DT_TEXTREL` (`AX_LINK_TEXTREL_FORBIDDEN`), `.rela.dyn` (`R_RISCV_RELATIVE`, `R_RISCV_64`, `R_RISCV_TLS_*`), and `.rela.plt` (`R_RISCV_JUMP_SLOT`) (`SPEC-80`, `SPEC-82 AXS-ELFD-001..030`). Each 16-byte RV64 PLT stub emits `1: AUIPC t3, %pcrel_hi(got_slot); LD t3, %pcrel_lo(1b)(t3); JALR t1, t3; ADDI x0, x0, 0` paired with the 32-byte PLT0 resolver header (`t0..t3`). Input objects/archives/shared libraries with `e_machine != EM_RISCV (243)` or incompatible float-ABI `e_flags` are rejected with `AX_LINK_ARTIFACT_TARGET_MISMATCH`. [tasks/0522 §89–94, §141; SPEC-80; SPEC-82 AXS-ELFD-001..030]

**AXS-RV64-041 — RISC-V Variant I Thread-Local Storage (`tp` / `x4`: `LE`, `IE`, `GD`) (`ABACKEND-36`).** `riscv64-linux` implements **ELF TLS Variant I** (`tasks/0522 §12, §87–88, §90, ABACKEND-36`, `SPEC-82 AXS-ELFD-021, AXS-ELFD-040`, `REQ-TGT-182`): `tp` (`x4`) points one byte past the TCB directly to byte `0` of the static `PT_TLS` block (`tp + 0` = start of static TLS; dynamic `DTV` entries point to `module_tls_base + 0x800`):
- **Local-Exec (`LE`, static / non-preemptible executable):** `LUI t0, %tprel_hi(sym)` (`R_RISCV_TPREL_HI20`) + `ADD t0, t0, tp, %tprel_add(sym)` (`R_RISCV_TPREL_ADD`) + `ADDI/LD/SD rd, t0, %tprel_lo(sym)` (`R_RISCV_TPREL_LO12_I` / `S`).
- **Initial-Exec (`IE`, external TLS from executable):** `1: AUIPC t0, %tls_ie_pcrel_hi(sym)` (`R_RISCV_TLS_GOT_HI20`) + `LD t0, %pcrel_lo(1b)(t0)` (`R_RISCV_PCREL_LO12_I`, GOT entry carrying `R_RISCV_TLS_TPREL64 = 11`) + `ADD rd, t0, tp`.
- **General-Dynamic (`GD`, `-fPIC` `.so`):** `1: AUIPC a0, %tls_gd_pcrel_hi(sym)` (`R_RISCV_TLS_GD_HI20`) + `ADDI a0, a0, %pcrel_lo(1b)` (`R_RISCV_PCREL_LO12_I` onto a 16-byte `(R_RISCV_TLS_DTPMOD64 = 7, R_RISCV_TLS_DTPREL64 = 9)` GOT descriptor) + `CALL __tls_get_addr@plt`. [tasks/0522 §12, §87–88, §90, ABACKEND-36; SPEC-82 AXS-ELFD-021, AXS-ELFD-040; REQ-TGT-182]

**AXS-RV64-042 — Debug Provenance, DWARF `.eh_frame` Unwind Metadata & `EBREAK` Traps (`ABACKEND-39..40`).** Source spans, inlined frames, and variable locations survive lowering into DWARF v5 `.debug_line`/`.debug_info` where representable (`tasks/0522 §98–99, ABACKEND-39`, `REQ-TGT-185`). `compiler/obj/elf_riscv64` emits `.eh_frame` (plus `.eh_frame_hdr` `PT_GNU_EH_FRAME` under `--panic unwind`) matching exact generated prologue/epilogue semantics (`ABACKEND-40`, `REQ-TGT-186`): DWARF registers `0..31` = `x0..x31`, `32..63` = `f0..f31`, `96..127` = `v0..v31`, return-address column = `1` (`ra`), `CIE` `code_alignment_factor = 1` (supporting mixed 16-bit `RVC` + 32-bit instructions), `data_alignment_factor = -8`, and `DW_EH_PE_pcrel | DW_EH_PE_sdata4` FDE pointers (`R_RISCV_32_PCREL = 57`, `ADD32`/`SUB32` `35`/`39`). Checked panics route to the Axiom panic runtime (`exit 101` or DWARF unwind with `Drop` cleanup), whereas architectural traps (`unreachable` in trap mode, FFI no-unwind barrier `SPEC-54 AXS-PAN-020`, post-`_start` guard) emit `C.EBREAK` (`0x9002`) / `EBREAK` (`0x0010_0073`) or illegal `C.UNIMP` (`0x0000`) / `UNIMP` (`0xC000_1073`). [tasks/0522 §98–99, ABACKEND-39..40; SPEC-54 AXS-PAN-020; SPEC-81 AXS-TGTD-033; REQ-TGT-185, REQ-TGT-186]

---

## 5. Linux RISC-V Host Runtime (`std.sys.linux_riscv64`), Conformance, Examples & Traceability (`AXS-RV64-043`..`051`)

**AXS-RV64-043 — Linux `riscv64` Kernel Syscall ABI (`ecall`) & `asm-generic/unistd.h` Numbers.** On `riscv64-linux`, user-space enters the Linux kernel via `ECALL` (`0x0000_0073`): syscall number in `a7` (`x17`), up to 6 arguments in `a0..a5` (`x10..x15`), and signed 64-bit return value in `a0` (`x10`), where `a0 ∈ [-4095, -1]` encodes `-errno` (`Err(SysError(-a0))`) and the kernel preserves `sp`, `gp`, `tp`, `ra`, `s0..s11`, and `a1..a7` (`0152 §59`, `tasks/0522 §1, §151, §154`, `tasks/0784 §562.138–140`, `SPEC-04 AXS-EXT-110`):

| Domain | Canonical Linux `riscv64` (`asm-generic/unistd.h` + RISC-V arch) Syscall Numbers (`a7`) |
|---|---|
| Console, File & FS | `SYS_dup3 = 24`, `SYS_mkdirat = 34`, `SYS_unlinkat = 35`, `SYS_ftruncate = 46`, `SYS_faccessat = 48`, `SYS_openat = 56`, `SYS_close = 57`, `SYS_pipe2 = 59`, `SYS_getdents64 = 61`, `SYS_lseek = 62`, `SYS_read = 63`, `SYS_write = 64`, `SYS_pread64 = 67`, `SYS_pwrite64 = 68`, `SYS_readlinkat = 78`, `SYS_newfstatat = 79`, `SYS_fstat = 80`, `SYS_fsync = 82`, `SYS_renameat2 = 276` |
| Virtual Memory | `SYS_brk = 214`, `SYS_munmap = 215`, `SYS_mremap = 216`, `SYS_mmap = 222`, `SYS_mprotect = 226`, `SYS_madvise = 233` |
| Process, Threads & Time | `SYS_exit = 93`, `SYS_exit_group = 94`, `SYS_futex = 98`, `SYS_nanosleep = 101`, `SYS_clock_gettime = 113`, `SYS_clock_nanosleep = 115`, `SYS_sched_yield = 124`, `SYS_rt_sigaction = 134`, `SYS_rt_sigprocmask = 135`, `SYS_getpid = 172`, `SYS_gettid = 178`, `SYS_clone = 220`, `SYS_execve = 221`, `SYS_wait4 = 260`, `SYS_getrandom = 278`, `SYS_clone3 = 435` |
| Async I/O & Sockets | `SYS_eventfd2 = 19`, `SYS_epoll_create1 = 20`, `SYS_epoll_ctl = 21`, `SYS_epoll_pwait = 22`, `SYS_socket = 198`, `SYS_bind = 200`, `SYS_listen = 201`, `SYS_connect = 203`, `SYS_getsockname = 204`, `SYS_sendto = 206`, `SYS_recvfrom = 207`, `SYS_setsockopt = 208`, `SYS_shutdown = 210`, `SYS_accept4 = 242`, `SYS_io_uring_setup = 425`, `SYS_io_uring_enter = 426` |
| RISC-V Architecture | `SYS_riscv_hwprobe = 258` (runtime CPU/extension probing for `+v`, `+zba`, `+zbb`, `+zbs`, `+zicond`), `SYS_riscv_flush_icache = 259` (SMP cross-hart I-cache flush beyond local `FENCE.I`) |

`SYS_fstat = 80` and `SYS_newfstatat = 79` populate the 128-byte generic Linux 64-bit `struct stat` (`st_mode: u32` at offset `16`, `st_size: i64` at offset `48`). [0152 §59; tasks/0522 §1, §151, §154; tasks/0784 §562.138–140; SPEC-04 AXS-EXT-110; SPEC-80 AXS-ELFS-040..049; T679]

**AXS-RV64-044 — `std.sys.linux_riscv64` Host Interface, `_start` Stack ABI & 208-Byte Fiber Context Switch.** `std/sys/linux_riscv64` implements the complete `SPEC-04 AXS-EXT-110` host contract (`mmap`/`mremap`/`munmap` allocator, file/console I/O, `"/proc/self/exe"` `readlinkat`, `clock_gettime`, `clone`+`futex` threads, `riscv_hwprobe` runtime dispatch, and `io_uring`/`epoll`) while keeping OS startup strictly outside the OS-independent `Arch.RiscV64` backend (`0152 §59`, `tasks/0522 §1, §151, §154`, `tasks/0784 §562.138–140`):
- **ELF `_start` entry (`--profile hosted`):** Kernel enters `_start` with `sp % 16 == 0` pointing to `[argc: u64, argv[0..argc]: *const u8, NULL, envp[0..]: *const u8, NULL, auxv[0..]: Elf64_Auxv]` (and `a0` holding `rtld_fini` in dynamic `PIE` mode or `0` in static mode). `_start` zeroes `LI s0, 0` and `LI ra, 0` to terminate DWARF/frame unwind chains cleanly without clobbering `gp` or `tp`, extracts `argc`/`argv`/`envp`, maintains `sp % 16 == 0`, calls `__ax_start_main` / `main`, places the `i32` exit status (sign-extended) into `a0`, loads `LI a7, 94` (`SYS_exit_group`), executes `ECALL`, and emits a trailing `C.EBREAK` / `EBREAK`.
- **Stackful fibers (`std/sys/linux_riscv64/fiber.ax`, `SPEC-34 AXS-EXEC-054`):** Context-switch saves and restores the 16-byte-aligned **208-byte** `LP64D` callee-saved state (`s0..s11` = 12 GPRs, `fs0..fs11` = 12 FPRs, `ra`, and `sp` = `26 * 8` bytes).
- **Freestanding / kernel profiles (`--profile freestanding`, `kernel`):** Zero `std.sys.linux_riscv64` code is linked and `e_entry` binds directly to the user `@entry` symbol (`SPEC-52 AXS-FRE-002..004, AXS-FRE-010, AXS-FRE-022..023`). [0152 §59; tasks/0522 §1, §151, §154; tasks/0784 §562.138–140; SPEC-04 AXS-EXT-110; SPEC-34 AXS-EXEC-054; SPEC-52 AXS-FRE-002..004, AXS-FRE-010, AXS-FRE-022..023; SPEC-80 AXS-ELFS-033]

**AXS-RV64-045 — Deterministic Parallel Compilation & `TargetFingerprint` Cache Identity (`ABACKEND-54..55`).** Backend incremental and artifact cache keys (`SPEC-22`, `SPEC-24`) incorporate `(SemanticFingerprint, TargetId.Riscv64Linux, TargetFeatureSet, CallConv.RiscV, OptProfile, CodegenFingerprint)` so toggles such as `+v`, `+zba`, `+zbb`, `+zicond`, or `-c` never collide in cache (`tasks/0522 §142, §159, ABACKEND-54`, `SPEC-81 AXS-TGTD-003`, `REQ-TGT-200`). Parallel per-function backend lowering, register allocation, `RVC` compression, and ELF64 emission are strictly deterministic functions producing bit-for-bit identical `.o` and executable images regardless of thread count (`tasks/0522 §142, §159, ABACKEND-55`, `SPEC-81 AXS-TGTD-047`, `REQ-TGT-201`). [tasks/0522 §142, §159, ABACKEND-54..55; SPEC-81 AXS-TGTD-003, AXS-TGTD-047; REQ-TGT-200, REQ-TGT-201]

**AXS-RV64-046 — Core Language Non-Leakage & `TargetBackend` Portability Boundary (`ABACKEND-56..60`).** RISC-V backend mechanics (`RVC` compression, `+0x800` `HI20`/`LO12` carry compensation, paired `PCREL_LO12` indirection, `f32` NaN-boxing, `LP64D` `u32` sign-extension, flagless compare-branch fusion) **never** leak into Axiom Core surface syntax (`tasks/0522 §151–160, ABACKEND-56`, `REQ-TGT-202`). Adding the flagless RV64 register architecture (`ABACKEND-57`, `REQ-TGT-203`), the `LP64D` psABI (`ABACKEND-58`, `REQ-TGT-204`), and `EM_RISCV` ELF64 object emission (`ABACKEND-59`, `REQ-TGT-205`) requires **zero** modifications to Axiom's lexer, parser, name resolver, type checker, ownership/capability checker, or MIR semantics; the `TargetBackend` contract is the sole portability boundary of the native compiler (`ABACKEND-60`, `SPEC-81 AXS-TGTD-048..049`, `REQ-TGT-206`). [tasks/0522 §151–160, ABACKEND-56..60; SPEC-81 AXS-TGTD-048..049; REQ-TGT-202..206]

**AXS-RV64-047 — Cross-Target Differential Conformance & Four-Pillar Certification (`ABACKEND-51..53`).** Certification of `riscv64-linux` (`T678`–`T680`) enforces that all backends pass the common target-independent conformance suites (`ABACKEND-51`, `REQ-TGT-197`), semantic correctness is judged by observable execution rather than assembly golden files (`ABACKEND-52`, `REQ-TGT-198`), and equivalent Axiom programs exhibit identical observable exit codes, stdout, panics, and memory effects across `--interp`, `x86_64-linux`, `aarch64-linux`, `wasm32`, and `riscv64-linux` (`0152 §59`, `tasks/0522 §125–153, §159, ABACKEND-53`, `SPEC-81 AXS-TGTD-044..045`, `REQ-TGT-199`):

| Verification Pillar | Gate / Suite | Asserted Contract |
|---|---|---|
| 1. `LP64D` ABI & `verify_mc` | `ABIVerifier` + `verify_mc` (`tests/mc/riscv64_isel`) | `x0`/`sp`/`gp`/`tp` invariants, `i32`+`u32` sign-extension, `{FP}`/`{FP,FP}`/`{INT,FP}` flattening, `a7`+stack split, `a0` `sret`, flagless overflow/div-zero, `NaN -> 0` before encoding (`T678`) |
| 2. RV64GC + `RVC` Encoding | `EncoderVerifier` (`tests/encode/riscv64`) | `decode(encode(I)) == I` across 32-bit `R/R4/I/S/B/U/J` and 16-bit `RVC` parcels; golden assembly tests code quality only, never semantic truth (`ABACKEND-43, 52`, `T679`) |
| 3. `EM_RISCV` ELF64 & Linker | `verify_elf_image` (`tests/selfhost/obj`, `tests/selfhost/link`) | `e_flags = 0x0005`, `.riscv.attributes`, paired `PCREL_HI20`+`LO12_I/S` via `AUIPC` label without `R_RISCV_RELAX`, `GOT`/`PLT`, Variant I `tp` TLS, `.eh_frame` (`ABACKEND-36..40, 47`, `T679`) |
| 4. Differential Execution | `tools/axtest.py` (`tests/conformance/p16/e16_7_riscv64`) | Execution on native RV64 Linux or `qemu-riscv64` matches `--interp`, `x86_64-linux`, and `aarch64-linux` byte-for-byte across arithmetic, atomics, FP `NaN`, ABI structs, closures, `dyn Trait`, `Drop`, TLS, and UTF-8 `"Xin chào thế giới"` (`ABACKEND-51..53`, `T680`) |

**AXS-RV64-048 — Diagnostics Referenced by `SPEC-87`.** `riscv64-linux` reuses the canonical `DRIVER`, `TARGET`, `VERIFY`, `LINK`, and `ICE` diagnostic codes (`spec/diagnostics.md` §10–11, `tasks/0522 §100–102, §148–150, §159, ABACKEND-50`):

| Code | Area | Sev | Delivering Task | Condition on `riscv64-linux` |
|---|---|---|---|---|
| `AX_DRIVER_UNKNOWN_TARGET` | `DRIVER` | `error` | `T016`/`T654` | Unrecognized `--target <triple>` (`AXS-RV64-001`) |
| `AX_TARGET_UNKNOWN_FEATURE` | `TARGET` | `error` | `T476`/`T654`/`T678` | Unknown feature name (e.g. `"avx2"`, `"lse"`) or forbidden removal of hosted `LP64D` baseline (`-f`, `-d`, `-a`, `-m`) (`AXS-RV64-003`) |
| `AX_TARGET_FEATURE_CONFLICT` | `TARGET` | `error` | `T654`/`T678` | Contradictory feature toggles (e.g. `+d,-f` or `+v,-d`) (`AXS-RV64-003`) |
| `AX_TARGET_FEATURE_MISMATCH` | `TARGET` | `error` | `T476`/`T678` | Calling a `@target_feature("v")` or `@target_feature("zbb")` function from baseline `RV64GC` code without `unsafe` or runtime `riscv_hwprobe` guard (`AXS-RV64-003`) |
| `AX_TARGET_UNSUPPORTED_OP` | `TARGET` | `error` | `T655`/`T678` | `LIR` operation or lock-free width cannot be legally expanded on the active RV64 target/profile without altering semantics (`AXS-RV64-004`, `AXS-RV64-014`) |
| `AX_VERIFY_MC_ILLEGAL` | `VERIFY` | `error` | `T655`/`T678` | Deserialized Machine IR violates `verify_mc` (`x0` live def, `gp`/`tp` write, `GPR`/`FPR` mismatch, misaligned `sp`, unexpanded pseudo-op, illegal `RVC` operand, or broken `LR`/`SC` loop; `AXS-RV64-032..033`) |
| `AX_LINK_BAD_OBJECT` / `AX_LINK_BAD_ARCHIVE` | `LINK` | `error` | `T066`/`T657`/`T679` | Malformed ELF64 `ET_REL` `.o`, `.a` archive, or `.so` (`AXS-RV64-037`, `AXS-RV64-040`) |
| `AX_LINK_ARTIFACT_TARGET_MISMATCH` | `LINK` | `error` | `T766`/`T679` | Input `.o`/`.a`/`.so`/`.axmi` has `e_machine != EM_RISCV (243)` or incompatible float-ABI `e_flags` / `TargetFingerprint` (`AXS-RV64-037`, `AXS-RV64-040`) |
| `AX_LINK_RELOC_OUT_OF_RANGE` | `LINK` | `error` | `T027`/`T679` | `R_RISCV_BRANCH` (`±4 KiB`), `R_RISCV_JAL` (`±1 MiB`), `R_RISCV_PCREL_HI20` (`±2 GiB`), or `R_RISCV_RVC_*` overflows its architectural range (`AXS-RV64-038`) |
| `AX_LINK_TEXTREL_FORBIDDEN` | `LINK` | `error` | `T658`/`T679` | Non-PIC relocation (`R_RISCV_64`, `R_RISCV_32`) targets a read-only/executable segment in a `PIE` or `.so` link (`AXS-RV64-040`) |
| `AX_ICE_INTERNAL` (`stage = "mc_verify"`) | `ICE` | `error` | `T655`/`T678` | Compiler-generated RV64 Machine IR failed `verify_mc` or `ABIVerifier` before encoding (`AXS-RV64-032`) |

**AXS-RV64-049 — Canonical Positive Examples (`=` and `.` Syntax).**

```axiom
// Example 1: LP64D {INT, FP} hardware flattening (a1 + fa0), u32 sign-extension, >16-byte indirect sret
// in a0, view/mut_view capabilities, flagless checked arithmetic, and UTF-8 output on --target riscv64-linux.
// Compiled with: axiomc build --target riscv64-linux lp64d_demo.ax -o lp64d_demo
module demo.riscv64_lp64d

use std.io.println

@repr(C)
pub struct TaggedSample {
    pub tag: u32
    pub weight: f64
}

@repr(C)
pub struct Digest24 {
    pub head: i64
    pub checksum: i64
    pub scaled: i64
}

// LP64D: Digest24 (24 bytes > 16) uses hidden sret pointer in a0;
// base passes in a1; sample ({u32, f64}) flattens into a2 (sign-extended u32) + fa0 (f64);
// lanes (16-byte view<[i64]>) passes in (a3, a4) (AXS-RV64-022..026).
pub fn compute_digest(base: i64, sample: TaggedSample, lanes: view<[i64]>) -> Digest24 {
    let rounded = sample.weight as i64
    let mut sum: i64 = (sample.tag as i64) + rounded
    let mut i: usize = 0
    while i < len(lanes) {
        sum = sum + lanes[i]
        i = i + 1
    }
    return Digest24 {
        head: base
        checksum: sum
        scaled: base * rounded
    }
}

pub fn add_delta(dst: mut_view<Digest24>, delta: i64) {
    dst.checksum = dst.checksum + delta
}

pub fn main() -> i32 {
    println("Xin chào thế giới")
    let s = TaggedSample { tag: 4u32, weight: 6.0 }
    let items: [4]i64 = [2, 8, 10, 10]
    let mut d = compute_digest(5, s, view(items))
    add_delta(mut_view(d), 2)
    if d.checksum == 42 && d.scaled == 30 {
        return 0
    }
    return 1
}
```

```axiom
// Example 2: Feature-gated +zbb bit-manipulation helper and RVWMO SeqCst atomic RMW (AMOADD.D.AQRL)
// Compiled with: axiomc build --target riscv64-linux --target-feature +zbb rv64_atomic.ax -o rv64_atomic
module demo.riscv64_atomic_zbb

use std.sync.atomic.{Atomic, Ordering}

@target_feature("zbb")
pub fn step_nonzero(mask: u64) -> u64 {
    if mask == 0u64 {
        return 0u64
    }
    return 2u64
}

pub fn main() -> i32 {
    let counter = Atomic<u64>.new(40u64)
    let delta = unsafe { step_nonzero(1u64) }
    let prev = counter.fetch_add(delta, Ordering.SeqCst)
    let now = counter.load(Ordering.Acquire)
    if prev == 40u64 && now == 42u64 {
        return 0
    }
    return 1
}
```

**AXS-RV64-050 — Canonical Negative Examples (`=` and `.` Syntax).**

```axiom
// Example 1: Calling a @target_feature("v") RVV function from baseline RV64GC code without unsafe
// or runtime riscv_hwprobe feature guard is rejected (AX_TARGET_FEATURE_MISMATCH, AXS-RV64-003).
module demo.riscv64_bad_rvv_call

@target_feature("v")
pub fn rvv_reduce_lane(x: i64) -> i64 {
    return x + 1
}

pub fn baseline_rv64gc_caller(x: i64) -> i64 {
    return rvv_reduce_lane(x) //~ ERROR AX_TARGET_FEATURE_MISMATCH
}
```

```axiom
// Example 2: Requesting a foreign x86 feature on --target riscv64-linux is rejected at compile time
// with AX_TARGET_UNKNOWN_FEATURE (AXS-RV64-003, AXS-RV64-048).
module demo.riscv64_bad_foreign_feature

@target_feature("avx2") //~ ERROR AX_TARGET_UNKNOWN_FEATURE
pub fn wrong_isa_ext(x: i32) -> i32 {
    return x
}
```

**AXS-RV64-051 — Requirement, Invariant & Task Traceability Matrix (`E16.7`: `REQ-TGT-166`..`REQ-TGT-206`).**

| Task | Scope | Invariant | Covered Requirements | Primary Test Suites |
|---|---|---|---|---|
| `T677` | `SPEC-87`: Canonical RISC-V 64 (`RV64GC`) flagless ISA, `RegisterFile`, `CallConv.RiscV` (`LP64D`), RV64+`RVC` encoding, `EM_RISCV` ELF64 & `std.sys.linux_riscv64` specification | `INV-RISCV-001`..`003` | `REQ-TGT-166`..`REQ-TGT-175` | `spec/SPEC-87-riscv64-linux.md` |
| `T678` | `compiler/abi/riscv64` & `compiler/target/riscv64/isel`: RV64 `TargetDesc`/`IsaTable`, `LP64D` ABI (`{FP}`/`{FP,FP}`/`{INT,FP}` flattening, `u32` sext, `a7`+stack split, `a0` `sret`), flagless ISel, RVWMO atomics & `verify_mc` | `INV-RISCV-001` | `REQ-TGT-176`..`REQ-TGT-181`, `REQ-TGT-187`..`REQ-TGT-188`, `REQ-TGT-190`..`REQ-TGT-191` | `tests/mc/riscv64_isel`, `tests/selfhost/abi`, `tests/selfhost/isel` |
| `T679` | `compiler/target/riscv64/encode`, `compiler/obj/elf_riscv64`, `compiler/link/elf_riscv64` & `std/sys/linux_riscv64`: pseudo expansion, 32-bit + `RVC` encoder, `EM_RISCV` ELF64 paired `PCREL_HI20`/`LO12` relocations, `PIE`/`GOT`/`PLT`/TLS, `.eh_frame`, `_start` & `ecall` | `INV-RISCV-002` | `REQ-TGT-185`..`REQ-TGT-186`, `REQ-TGT-189`, `REQ-TGT-192`..`REQ-TGT-196` | `tests/encode/riscv64`, `tests/selfhost/encode`, `tests/selfhost/obj`, `tests/selfhost/link` |
| `T680` | End-to-end E16.7 RV64GC + `RVC` encoding goldens, `LP64D` ABI, relaxation-free `EM_RISCV` ELF64 & cross-ISA differential execution conformance suite | `INV-RISCV-003` | `REQ-TGT-197`..`REQ-TGT-206` | `tests/conformance/p16/e16_7_riscv64` |

Detailed requirement mapping across `REQ-TGT-166`..`REQ-TGT-206` (`tasks/0522 §159`, `ABACKEND-20..60`):

| Requirement(s) | Corpus Anchor | Canonical `SPEC-87` Rule(s) | Board Task(s) |
|---|---|---|---|
| `REQ-TGT-166`, `REQ-TGT-167` | `ABACKEND-20..21` | `AXS-RV64-001`, `AXS-RV64-002` (common `TargetBackend` contract & physical-reg-free `LIR`) | `T677` |
| `REQ-TGT-168`, `REQ-TGT-169` | `ABACKEND-22..23` | `AXS-RV64-002`, `AXS-RV64-012` (flagless `LIR` & two-register compare/branch fusion) | `T677` |
| `REQ-TGT-170`, `REQ-TGT-171` | `ABACKEND-24..25` | `AXS-RV64-002`, `AXS-RV64-008`, `AXS-RV64-016` (fixed vs scalable vectors & semantic addresses) | `T677` |
| `REQ-TGT-172`, `REQ-TGT-173` | `ABACKEND-26..27` | `AXS-RV64-021`..`027` (`CallConv.RiscV` `LP64D` classification outside Core types) | `T677` |
| `REQ-TGT-174`, `REQ-TGT-175` | `ABACKEND-28..29` | `AXS-RV64-003` (modular `RV64GC` feature DAG & non-emission of unavailable instructions) | `T677` |
| `REQ-TGT-176`, `REQ-TGT-177` | `ABACKEND-30..31` | `AXS-RV64-014`, `AXS-RV64-032` (legal expansion / `AX_TARGET_UNSUPPORTED_OP` & `verify_mc`) | `T678` |
| `REQ-TGT-178`, `REQ-TGT-179` | `ABACKEND-32..33` | `AXS-RV64-010`, `AXS-RV64-029`..`031` (transparent RA & `LP64D` 16B frame/stack probing) | `T678` |
| `REQ-TGT-180`, `REQ-TGT-181` | `ABACKEND-34..35` | `AXS-RV64-017`, `AXS-RV64-018` (RVWMO `AMO*`/`LR`/`SC`/`FENCE` & `Volatile`/`FENCE io, io`) | `T678` |
| `REQ-TGT-182`..`REQ-TGT-184` | `ABACKEND-36..38` | `AXS-RV64-037`, `AXS-RV64-038`, `AXS-RV64-041` (`tp` Variant I TLS, explicit relocs, ELF64 split) | `T659`, `T679`, `T685`, `T686` |
| `REQ-TGT-185`, `REQ-TGT-186` | `ABACKEND-39..40` | `AXS-RV64-042` (DWARF v5 provenance & `.eh_frame` CFI matching RV64 frames) | `T679` |
| `REQ-TGT-187`, `REQ-TGT-188` | `ABACKEND-41..42` | `AXS-RV64-011` (semantic-preserving target peepholes & CPU cost models) | `T678` |
| `REQ-TGT-189` | `ABACKEND-43` | `AXS-RV64-035` (`RVC` 16-bit compression as pure encoding/code-size optimization) | `T679` |
| `REQ-TGT-190`, `REQ-TGT-191` | `ABACKEND-44..45` | `AXS-RV64-005`, `AXS-RV64-006`, `AXS-RV64-008` (scalable `RVV` `v0..v31` & reserved `x0`/`sp`/`gp`/`tp`) | `T678` |
| `REQ-TGT-192`, `REQ-TGT-193` | `ABACKEND-46..47` | `AXS-RV64-033`, `AXS-RV64-039` (pre-encoding pseudo expansion & relaxation-free sequences) | `T679` |
| `REQ-TGT-194`..`REQ-TGT-196` | `ABACKEND-48..50` | `AXS-RV64-003`, `AXS-RV64-020`, `AXS-RV64-032`, `AXS-RV64-048` (custom extensions, inline asm effects, diagnosable failures) | `T679` |
| `REQ-TGT-197`..`REQ-TGT-199` | `ABACKEND-51..53` | `AXS-RV64-047` (common conformance suites, execution over golden asm, cross-target equivalence) | `T680` |
| `REQ-TGT-200`, `REQ-TGT-201` | `ABACKEND-54..55` | `AXS-RV64-045` (`TargetFingerprint` cache keys & deterministic parallel codegen) | `T680` |
| `REQ-TGT-202`..`REQ-TGT-206` | `ABACKEND-56..60` | `AXS-RV64-001`, `AXS-RV64-046` (zero Core syntax/type/frontend leakage & `TargetBackend` portability boundary) | `T680` |

## Sources

0152 §59; tasks/0522 §1–160 (`ABACKEND-20..60`); tasks/0784 §562.135–140, §562.200; ADR-0003; `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..054`, `AXS-EXT-060..062`, `AXS-EXT-070..074`, `AXS-EXT-101..102`, `AXS-EXT-110`); `spec/SPEC-31-atomics.md`; `spec/SPEC-34-executors-fibers.md`; `spec/SPEC-40-integers.md`; `spec/SPEC-41-floating-point.md`; `spec/SPEC-42-simd.md`; `spec/SPEC-44-cpu-features-multiversioning.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-51-raw-memory-volatile-mmio-layout.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-55-fixed-address-declarations.md`; `spec/SPEC-77-regalloc-machine-opt.md`; `spec/SPEC-80-linux-x86-64-elf-static.md`; `spec/SPEC-81-target-desc-isa-conformance.md`; `spec/SPEC-82-linux-elf-dynamic.md`; `spec/SPEC-83-aarch64-linux.md`; `spec/SPEC-86-wasm32-backend.md`; `spec/invariants.md` (`INV-RISCV-001..003`); `spec/diagnostics.md`.
