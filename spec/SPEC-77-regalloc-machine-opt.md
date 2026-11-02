# SPEC-77 — Register Allocation, Instruction Selection & Late Machine Optimization

## Tóm tắt
Tài liệu chuẩn hóa kiến trúc cấp phát thanh ghi quét tuyến tính (Linear-Scan Register Allocation), lựa chọn lệnh theo mẫu (Pattern-Matching Instruction Selection), chuyển đổi nhánh không rẽ nhánh (`cmovcc`/`setcc` If-Conversion), mô hình chi phí vi kiến trúc và tối ưu hóa máy hậu cấp phát (Post-RA Machine Peephole Optimization) cho `axiomc` (Epic `E15.8`, chạy đầu tiên trong Phase 15 để tăng tốc chính trình biên dịch `axiomc`):
- **Phân tích độ sống & khoảng sống (`AXS-RA-010..015`)**: Định nghĩa phân tích độ sống ngược trên CFG theo thứ tự RPO tất định, khoảng sống (`LiveInterval`) kèm vị trí sử dụng (`UsePos`), lớp thanh ghi theo ABI (`Gpr`, `Xmm`, `Vec128`/`Vec256` từ `SPEC-04 AXS-EXT-050/053`), và trọng số tràn thanh ghi theo độ sâu vòng lặp $10^d$ (`REQ-OPT-201`, `REQ-OPT-202`).
- **Cấp phát quét tuyến tính, hợp nhất lệnh gán & tích hợp khung ngăn xếp (`AXS-RA-020..027`)**: Quy định thuật toán Linear Scan ở `-O1`/`-O2`, tô màu trước cho ràng buộc thanh ghi cố định (`RCX` cho phép dịch biến thiên, `RAX`/`RDX` cho `div`/`idiv`/`mul`), clobber qua lệnh gọi hàm ABI, hợp nhất `mov` (Copy Coalescing), tái sử dụng khe tràn (Spill-Slot Coloring) và lưu/khôi phục thanh ghi callee-saved (`RBX`, `RBP`, `RDI`, `RSI`, `R12`–`R15`, `XMM6`–`XMM15`) trong `FrameLayout`.
- **Lựa chọn lệnh, `cmovcc` không rẽ nhánh & mô hình chi phí vi kiến trúc (`AXS-MCOPT-001..014`)**: Tách biệt ngữ nghĩa ISA với chi phí vi kiến trúc (độ trễ vs. thông lượng, `REQ-OPT-197..200`); gộp địa chỉ `base + index * scale + disp` vào `lea` và toán hạng bộ nhớ; giảm cường độ nhân/chia hằng số; chuyển đổi nhánh kim cương thuần khiết sang `cmovcc`/`setcc` khi không có bẫy tràn số, lệnh gọi hàm hay tác dụng phụ bộ nhớ (`REQ-OPT-205..208`, `REQ-OPT-369..370`).
- **Tối ưu hóa Peephole hậu cấp phát & bảo toàn cờ `EFLAGS` (`AXS-MCOPT-020..026`)**: Loại bỏ `mov r, r`, phép toán đồng nhất và nhảy thừa; rút gọn `mov r, 0` → `xor r, r` và `cmp r, 0` → `test r, r` chỉ khi cờ `EFLAGS` đã chết (`REQ-OPT-033`); tuyệt đối cấm xóa hoặc đẩy lệnh qua rào cản `volatile`, `atomic`, bẫy `Assert` hoặc lệnh gọi hàm (`REQ-OPT-015`, `REQ-OPT-030..036`, `REQ-OPT-371..372`).

Status: draft (T627, 2026-11-03). Owner: axiom-architect.
Rule IDs `AXS-RA-NNN` and `AXS-MCOPT-NNN` are stable and never renumbered.
Consolidates: `0162 §36–40`, `0182` (`REGALLOC-001` / `FRAME-001`), `0235` (`MACHINE-IR-004`), `0237` (`MACHINE-IR-006`), `0252` (`COMPILER-010`), `tasks/0406` (`BOOTSTRAP-147`), `tasks/0553` (`BOOTSTRAP-294`), `tasks/0557` (`BOOTSTRAP-298`), `tasks/0559` (`BOOTSTRAP-300`), and `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..060`).
Covers: `REQ-OPT-015`, `REQ-OPT-030`, `REQ-OPT-031`, `REQ-OPT-032`, `REQ-OPT-033`, `REQ-OPT-197`, `REQ-OPT-198`, `REQ-OPT-199`, `REQ-OPT-200`, `REQ-OPT-201`, `REQ-OPT-202` (and governs implementation/QA tasks `T063`, `T628`, `T629` covering `REQ-OPT-034..036`, `REQ-OPT-203..205`, `REQ-OPT-207..208`, `REQ-OPT-212`, `REQ-OPT-218`, `REQ-OPT-369..372`).
Consumers: `T063` (`compiler/target/x64`, `tests/mc/regalloc`), `T628` (`compiler/lir`, `compiler/backend/peephole`, `tests/mc/isel_peephole`), `T629` (`tests/conformance/p15/e15_8_regalloc_isel`).

---

## 1. Pipeline Position, Architectural Boundary & Microarchitectural Cost Model

**AXS-MCOPT-001 — Machine-Level Optimization Boundary (`REQ-OPT-015`, `REQ-OPT-031`, `REQ-OPT-371`, `REQ-OPT-372`).**
Target-specific optimizations — pattern-matching instruction selection, linear-scan register allocation, register copy coalescing, instruction scheduling, and post-RA peephole optimization — MUST be performed at the LIR and Machine IR levels (`LirBody` → `X64MIBody`).
1. Machine-level passes operate solely on virtual and physical registers, stack frame slots, concrete addressing modes (`X64Mem`), condition flags (`EFLAGS`), basic-block control flow, ABI calling-convention descriptors, and target feature flags, without accessing AST, HIR, ownership lattice states, capability regions, or high-level source type abstractions (`INV-LAYER-005`, `REQ-OPT-031`).
2. The late machine optimization stage is the final optimization step in the compilation pipeline and never defines or alters language semantics (`REQ-OPT-371`).
3. The final post-RA Machine IR (`X64MIBody` paired with `X64FrameLayout`) MUST remain a structured, inspectable, and verifier-checked intermediate representation prior to binary byte emission (`x64_emit_mi_body_obj`, `REQ-OPT-372`).
[0162 §36-40; 0237 §1-3, §59; tasks/0559 §1-4, AFINAL-20/44/46/50; SPEC-04 AXS-EXT-053]

**AXS-MCOPT-002 — Semantic Preservation Across Optimization Profiles (`REQ-OPT-030`, `REQ-OPT-197`, `REQ-OPT-212`).**
Neither microarchitectural cost modeling, instruction selection, branchless if-conversion, linear-scan register allocation, instruction scheduling, nor post-RA peephole optimization may change the observable behavior of an Axiom program:
- Return values, exit codes, stdout/stderr byte streams, deterministic `Drop` execution order (`INV-SEM-003`), checked-arithmetic overflow/division-by-zero/bounds traps (`INV-ORACLE-001`), `volatile` memory transactions, and `atomic` memory orderings MUST be preserved identically across `--interp`, `-O0`, `-O1`, and `-O2`.
- Profile-guided optimization data (`--pgo-use`, `E15.6`) influences only profitability weights (spill weights, branch layout, hot/cold splitting) and MUST NEVER alter program semantics (`REQ-OPT-212`).
[0182 §23, AREG-29..36; 0237 §1, §55, AMOPT-20/39; tasks/0406 §30, AMICRO-20/35; tasks/0553 ACTRL-20/53/86]

**AXS-MCOPT-003 — Separation of ISA Semantics and Microarchitectural Cost (`REQ-OPT-198`, `REQ-OPT-199`, `REQ-OPT-200`).**
Target instruction legality and microarchitectural cost are strictly separate concerns:
1. **Legality first (`REQ-OPT-198`):** An instruction selection or peephole rewrite candidate is legal if and only if the target ISA supports its operand encodings and its execution is semantically equivalent to the input LIR/Machine IR sequence for all possible runtime inputs (including edge values `i64.MIN`, `0`, `-1`, `NaN`, and `-0.0`).
2. **Advisory cost model (`REQ-OPT-199`):** `TargetCostModel` influences only optimization choices among legal candidates. Cost-model uncertainty or absence of CPU subtarget tuning may reduce optimization aggressiveness (falling back to a simpler legal sequence) but never invalidates correctness.
3. **Distinct cost dimensions (`REQ-OPT-200`):** Every machine instruction descriptor in `TargetCostModel` models three orthogonal dimensions:
   - `latency`: execution delay in cycles from input readiness to result availability (governs critical-path length and `cmovcc` chain profitability).
   - `throughput_rcp`: reciprocal throughput in quarter-cycles per instruction (governs loop-body issue-port saturation).
   - `code_bytes`: encoded instruction length in bytes (governs instruction-cache footprint and `-Oz` size optimization).
[tasks/0406 §30, AMICRO-21..23, AMICRO-34/43; tasks/0559 AFINAL-48]

**AXS-MCOPT-004 — Explicit Register-Pressure and Spill-Cost Participation (`REQ-OPT-201`, `REQ-OPT-202`).**
1. **Register pressure awareness (`REQ-OPT-201`):** Peak live register pressure per register class (`Gpr`, `Xmm`, `Vec128`/`Vec256`) MUST participate in profitability decisions for expression tree scheduling, address-mode folding, rematerialization, and branchless if-conversion. When live pressure in a basic block is at or above the allocatable physical register count $K_{\mathrm{class}}$ ($K_{\mathrm{Gpr}} = 14$ on x86-64 with `RSP` and `RBP` reserved), transformations that extend live ranges or materialize additional simultaneous temporaries are suppressed unless they fold away a memory load.
2. **Explicit spill cost (`REQ-OPT-202`):** Spill cost is modeled explicitly as the weighted sum of store and reload penalties across all definitions and uses of a virtual register, scaled by loop nesting depth (`AXS-RA-015`).
[0182 §13; 0235 §20-21, §30-31; tasks/0406 §30, AMICRO-24/25; tasks/0557 AREG-41]

**AXS-MCOPT-005 — Dependency-Preserving Deterministic Scheduling (`REQ-OPT-203`, `REQ-OPT-204`, `REQ-OPT-218`).**
1. **Data and flag dependencies (`REQ-OPT-203`):** Any intra-block instruction reordering or fusion MUST preserve all true (`RAW`), anti (`WAR`), and output (`WAW`) dependencies on physical/virtual registers, stack slots, and `EFLAGS`.
2. **Effect and memory barriers (`REQ-OPT-204`):** Memory stores with unproven non-aliasing, `volatile` loads/stores, `atomic` operations, hardware/compiler fences, trapping instructions (`X64_MI_ASSERT`, `idiv`, `div`), and `call` instructions act as strict scheduling barriers across which dependent or observable operations MUST NOT be reordered.
3. **Deterministic tie-breaking (`REQ-OPT-218`):** All worklists, priority queues, liveness sets, and candidate rankings in instruction selection, register allocation, and scheduling break ties by deterministic ordinal IDs (`LirBbId`, instruction index, `LirVRegId`), never by memory address or hash-table bucket order (`INV-KERN-002`, `INV-DET-001`).
[0237 §56, AMOPT-35/36/40; tasks/0406 §30, AMICRO-26/27/41]

---

## 2. Register Classes, Liveness Analysis & Live Intervals

**AXS-RA-010 — Register Classes and Physical Register Units (`SPEC-04 AXS-EXT-050`, `AXS-EXT-053`, `AXS-EXT-060`).**
Every virtual register in LIR and pre-RA Machine IR belongs to exactly one `RegClass`:
1. `RegClass.Gpr`: 8/16/32/64-bit general-purpose integer and pointer registers (`RAX=0`, `RCX=1`, `RDX=2`, `RBX=3`, `RSP=4`, `RBP=5`, `RSI=6`, `RDI=7`, `R8=8` .. `R15=15`).
2. `RegClass.Xmm`: 32/64-bit scalar IEEE-754 floating-point registers (`XMM0=0` .. `XMM15=15`, delivered in `E12.2`).
3. `RegClass.Vec128` / `RegClass.Vec256`: 128-bit and 256-bit SIMD vector registers (`XMM0`–`XMM15` and `YMM0`–`YMM15`, delivered in `E12.3`/`E12.4`).
Sub-register widths (`AL`/`AX`/`EAX`/`RAX` and `XMMi`/`YMMi`) share the same underlying physical register unit index $i \in 0..15$. Overlapping live intervals MUST NEVER be assigned to overlapping register units (`AREG-21/22`, `ARA-21..23`). `RSP` (and `RBP` whenever frame-pointer addressing is active) is permanently reserved and excluded from the allocatable set (`ARA-28`).
[0162 §5-6; 0182 §6, AREG-20..22; 0235 §3-6, ARA-20..23, ARA-28; 0252 ARALLOC-23/24/51; SPEC-04 AXS-EXT-050/053/060]

**AXS-RA-011 — Target ABI Caller-Saved vs. Callee-Saved Register Partition.**
For `CallConv.Win64` (`x86_64-windows`, `SPEC-04 AXS-EXT-052/060`):

| Register Class | Caller-Saved (Volatile across `call`) | Callee-Saved (Non-Volatile across `call`) | Reserved |
|---|---|---|---|
| `Gpr` | `RAX`, `RCX`, `RDX`, `R8`, `R9`, `R10`, `R11` (7 regs) | `RBX`, `RSI`, `RDI`, `R12`, `R13`, `R14`, `R15` (+ `RBP` if FP omitted) | `RSP`, `RBP` (frame base) |
| `Xmm` / `Vec128` | `XMM0`, `XMM1`, `XMM2`, `XMM3`, `XMM4`, `XMM5` (6 regs) | `XMM6`, `XMM7`, `XMM8`, `XMM9`, `XMM10`, `XMM11`, `XMM12`, `XMM13`, `XMM14`, `XMM15` (10 regs) | none |
| `Vec256` | `YMM0`–`YMM5` full; upper 128 bits of `YMM6`–`YMM15` | Lower 128 bits (`XMM6`–`XMM15`) only | none |

The allocator queries these sets from `TargetDesc` rather than hard-coding register numbers in generic interval logic (`AREG-40`).
[0182 §8-10; 0235 §14-15, §32-34; 0252 §36-37, ARALLOC-28/29/36/52/53; tasks/0557 AREG-27/40]

**AXS-RA-012 — Deterministic Linear Instruction Numbering.**
Prior to liveness analysis, basic blocks of `X64MIBody` are linearized in deterministic reverse post-order (RPO) such that natural loop bodies occupy contiguous block index ranges. Each machine instruction $k = 0, 1, \dots, N-1$ is assigned an even program point $p_{\mathrm{use}}(k) = 2k$ for input operand reads and an odd program point $p_{\mathrm{def}}(k) = 2k + 1$ for output definitions and call/instruction clobbers. Block boundaries are recorded as `[block_start(b), block_end(b))`.
[0182 §3; 0235 §7; tasks/0557 §6-7]

**AXS-RA-013 — Backward CFG Liveness Analysis (`REQ-OPT-203`, `REQ-OPT-218`).**
1. **Local block summary:** For each basic block $B$, `use[B]` is the set of virtual registers read at $2k \in B$ before any definition in $B$, and `def[B]` is the set of virtual registers written at $2k + 1 \in B$.
2. **Iterative fixed-point equations:** Iterating over blocks in reverse RPO order until no bitset changes:
   $$\mathrm{live\_out}[B] = \bigcup_{S \in \mathrm{succ}(B)} \mathrm{live\_in}[S], \qquad \mathrm{live\_in}[B] = \mathrm{use}[B] \cup \bigl(\mathrm{live\_out}[B] \setminus \mathrm{def}[B]\bigr)$$
3. **Loop liveness closure:** Any virtual register $v \in \mathrm{live\_in}[H]$ at a natural loop header $H$ is marked live across the entire loop span $[p_{\mathrm{start}}(H), p_{\mathrm{end}}(L_{\max}))$ through the furthest loop latch $L_{\max}$, preventing a loop-invariant register from being prematurely expired inside the loop body.
4. **Representation:** `use`, `def`, `live_in`, and `live_out` are represented as dense `u64`-word bitsets indexed by `LirVRegId.v`, guaranteeing deterministic convergence.
[0182 §2; 0235 §8, §21; 0252 §50, ARALLOC-44/47; tasks/0557 §5]

**AXS-RA-014 — Live Intervals and Use-Positions.**
From `live_in`/`live_out` and backward instruction traversal, the allocator constructs one `LiveInterval` per virtual register $v$:
```text
UseKind = MustBeReg | MayBeMem | FixedReg(phys_reg: i32) | CopyHint(reg_or_vreg: i32)

UsePos {
    pos: u32,           // 2*k for use, 2*k + 1 for def
    kind: UseKind,
    loop_depth: u8,
}

LiveRange {
    start: u32,         // inclusive program point
    end: u32,           // exclusive program point (start < end)
}

LiveInterval {
    vreg: LirVRegId,
    reg_class: RegClass,
    ranges: [LiveRange],        // sorted, non-overlapping half-open intervals
    uses: [UsePos],             // sorted by pos ascending
    assigned_reg: i32,          // physical register index or REG_NONE
    spill_slot: i32,            // stack slot id or -1
    copy_hint_vreg: LirVRegId,  // coalescing partner or LIR_VREG_NONE
    fixed_reg_hint: i32,        // ABI or instruction fixed preference or REG_NONE
    crosses_call: bool,         // true if any call point 2*c+1 lies inside ranges[]
    remat_kind: u8,             // REMAT_NONE | REMAT_CONST | REMAT_STACK_ADDR
    remat_val: i64,             // constant value or frame slot id
    spill_weight: u64,
}
```
Two `LiveInterval`s $I_1, I_2$ **interfere** if and only if they belong to the same `RegClass` (or overlapping register units) and there exist ranges $[s_1, e_1) \in I_1.\mathrm{ranges}$ and $[s_2, e_2) \in I_2.\mathrm{ranges}$ such that $\max(s_1, s_2) < \min(e_1, e_2)$.
[0182 §4-6; 0235 §7, §11-15; 0252 §6-8; tasks/0557 §6-12]

**AXS-RA-015 — Loop-Depth Spill-Weight Model and Rematerialization Priority (`REQ-OPT-201`, `REQ-OPT-202`, `REQ-OPT-212`).**
1. **Loop nesting depth:** Each basic block $B$ has a natural loop nesting depth $d(B) \in 0..6$ (clamped at 6 to prevent `u64` overflow).
2. **Spill weight formula (`REQ-OPT-202`):** For a virtual register interval $I$ of total length $L(I) = \max(1, \max end_i - \min start_i)$:
   $$\mathrm{spill\_weight}(I) = \frac{\sum_{u \in I.\mathrm{uses}} w(u) \cdot 10^{\min(u.\mathrm{loop\_depth},\, 6)} \cdot M_{\mathrm{remat}}(I)}{L(I)}$$
   where:
   - $w(u) = 100$ for a `MustBeReg` operand (reloading requires a scratch register + instruction),
   - $w(u) = 50$ for a `MayBeMem` operand (can fold `[rbp - disp]` directly into the instruction),
   - $M_{\mathrm{remat}}(I) = 1$ if $I$ is rematerializable (`REMAT_CONST` or `REMAT_STACK_ADDR`, since rematerialization avoids a memory store and load) and $M_{\mathrm{remat}}(I) = 2$ otherwise.
3. **Unsplittable / precolored intervals:** Precolored fixed-register intervals and reload/spill intervals created for a single instruction ($L(I) \le 2$) have $\mathrm{spill\_weight}(I) = \mathrm{u64.MAX}$ and MUST NEVER be selected as spill victims.
4. **PGO weight override (`REQ-OPT-212`):** When `--pgo-use` basic-block execution counts are available (`E15.6`), the static factor $10^{d(u)}$ is replaced by the normalized block execution count $\max(1, \mathrm{count}(B))$ without changing allocation legality.
[0182 §12-13; 0235 §20-23; 0252 §18-19; tasks/0406 §30, AMICRO-24/25/35; tasks/0557 §18-19]

---

## 3. Linear-Scan Register Allocation, Constraints, Coalescing & Frame Integration

**AXS-RA-020 — Compilation Profile Policy (`-O0` vs. `-O1`/`-O2`).**
- At `-O0`, `axiomc` retains the fast deterministic single-pass stack-slot allocator (`T025`/`T025b`) for minimum compilation latency.
- At `-O1` and `-O2`, `axiomc` runs the linear-scan register allocator (`T063`) with copy coalescing, loop-depth-weighted spill selection, spill-slot lifetime coloring, and callee-saved register tracking.
- Both allocators satisfy the same Machine IR verifier contract (`AXS-RA-027`) and produce identical observable program execution (`AXS-MCOPT-002`).
[0252 §27, ARALLOC-45; T063]

**AXS-RA-021 — Linear-Scan Register Allocation Algorithm.**
For each `RegClass` independently, unhandled `LiveInterval`s are sorted deterministically by `(first_start_pos, vreg.v)`. The allocator maintains `active` (intervals currently occupying a physical register at `cur.start`) and `inactive` (assigned intervals currently in a lifetime hole at `cur.start`):
1. **State transition at `cur.start`:**
   - Expire every $A \in \mathrm{active}$ with $A.\mathrm{last\_end} \le \mathrm{cur.start}$ and release $A.\mathrm{assigned\_reg}$ to the free pool.
   - Move any $A \in \mathrm{active}$ covering a hole at `cur.start` to `inactive`, and reactivate any $B \in \mathrm{inactive}$ whose range now covers `cur.start`.
2. **Constraint-filtered candidate pool:** From the allocatable registers of `cur.reg_class`, exclude:
   - Registers held by `active` intervals or by `inactive` intervals whose ranges intersect `cur.ranges`.
   - Fixed registers clobbered at any instruction point $p \in \mathrm{cur.ranges}$ (`AXS-RA-022`).
   - All caller-saved (volatile) registers if `cur.crosses_call == true` (`AXS-RA-023`).
3. **Preference order among legal free registers:**
   - First, `cur.fixed_reg_hint` or the physical register already assigned to `cur.copy_hint_vreg` (enabling zero-cost copy coalescing, `AXS-RA-024`).
   - Second, if `cur.crosses_call == false`, the lowest-indexed free **caller-saved** register (`RAX`, `RCX`, `RDX`, `R8`, `R9`, `R10`, `R11` for `Gpr`; `XMM0`–`XMM5` for `Xmm`), avoiding callee-saved save/restore traffic.
   - Third, if `cur.crosses_call == true` (or all caller-saved registers are busy), a free **callee-saved** register (`RBX`, `RSI`, `RDI`, `R12`–`R15` for `Gpr`; `XMM6`–`XMM15` for `Xmm`), preferring one already marked in `used_callee_saved` before opening a new callee-saved register.
4. **Spill / preemption resolution when no register is free:**
   - Let $M \in \mathrm{active}$ be the non-fixed active interval with minimum `(spill_weight, -last_end, vreg.v)`.
   - If $\mathrm{cur.spill\_weight} > M.\mathrm{spill\_weight}$ and $M.\mathrm{assigned\_reg}$ is legal for `cur` across all of `cur.ranges` (respecting `cur.crosses_call` and fixed clobbers), preempt $M$: evict $M$ to a spill slot (or split $M$ at `cur.start`), assign $M.\mathrm{assigned\_reg}$ to `cur`, and insert `cur` into `active`.
   - Otherwise, assign `cur` to a spill slot (or rematerialize it at its uses if `cur.remat_kind != REMAT_NONE`).
[0182 §11-14; 0235 §24-26, ARA-21..33, ARA-41/42; 0252 §21-22, §37; tasks/0557 §21-22, AREG-20..35, AREG-45]

**AXS-RA-022 — Fixed-Register Precoloring, Clobbers, and Two-Address Tied Operands.**
x86-64 instructions with fixed architectural register requirements or destructive two-address operands MUST be modeled explicitly before and during linear scan:
1. **Variable shift counts (`shl`, `shr`, `sar` by register):** x86-64 requires the shift count in `CL` (`REG_RCX`). Instruction selection / RA emits `mov rcx, v_count` at $2k$, marks `REG_RCX` as fixed-clobbered at $2k..2k+1$, and forbids allocating the shifted destination operand `ops[0]` to `REG_RCX` (`X64_VERIFY_ERR_SHIFT_REG_CLASS`).
2. **Division, remainder, and widening multiply (`idiv`, `div`, `mul`):**
   - `idiv divisor` / `div divisor` reads dividend `RDX:RAX` and writes quotient `RAX` and remainder `RDX`.
   - `RAX` and `RDX` are marked fixed-clobbered across the instruction point $2k..2k+1$. Any other virtual register live across $2k$ cannot reside in `RAX` or `RDX`, and the divisor operand MUST be allocated to a register $\notin \{\text{RAX}, \text{RDX}\}$ or a memory operand (`X64_VERIFY_ERR_IDIV_FORM`).
3. **Destructive two-address binary operations (`add`, `sub`, `imul`, `and`, `or`, `xor`, `shl`, `shr`, `sar`):** In x86-64 `op dst, src`, `dst` is both read and overwritten. Lowering emits `mov v_dst, v_lhs` followed by `op v_dst, v_rhs`, tying `v_dst` to `v_lhs` via `copy_hint_vreg` so linear scan coalesces `v_dst` and `v_lhs` into the same physical register whenever `v_lhs` dies at the operation (`ARA-25`, `AREG-25`).
4. **Dedicated spill scratch registers:** To guarantee forward progress when an instruction has multiple spilled operands and all other registers are live in `active`, `R10` and `R11` (and `XMM15` for `Xmm`) may be reserved as reload/spill scratch registers for the duration of a single instruction $2k..2k+1$ (or evicted with localized spill/reload around $2k$).
[0182 §6-7, AREG-23; 0235 §11-13, §29, §32, ARA-24..26; 0252 §9-11, ARALLOC-25..27; tasks/0557 §9-11, AREG-24..26]

**AXS-RA-023 — Call Boundary Clobbers and ABI Register Marshaling.**
At every `X64_MI_CALL` instruction at position $2c$:
1. Argument registers (`RCX`, `RDX`, `R8`, `R9`, `XMM0`–`XMM3`) are fixed uses at $2c$, and return registers (`RAX`, `XMM0`) are fixed defs at $2c + 1$.
2. Every volatile register in the active `CallConv` (`RAX`, `RCX`, `RDX`, `R8`–`R11`, `XMM0`–`XMM5` on Win64) is clobbered at $2c + 1$.
3. Any virtual register $v$ whose live interval spans across the call ($s \le 2c$ and $e > 2c + 1$) has `crosses_call = true` and MUST either be allocated to a callee-saved register or spilled to its stack frame slot before $2c$ and reloaded before its next use after $2c + 1$ (`AREG-24/25`, `ARA-27`, `ARALLOC-52/53`).
[0182 §8-10, AREG-24/25; 0235 §14-15, ARA-27/36; 0252 §12, ARALLOC-28/36/52/53; tasks/0557 AREG-27]

**AXS-RA-024 — Copy Coalescing and Parallel-Copy Resolution.**
1. **Copy coalescing (`AREG-34`, `ARA-34`):** For every register copy `mov v_dst, v_src` where `v_dst` and `v_src` share the same `RegClass`, `v_dst` records `copy_hint_vreg = v_src` (and vice versa). If linear scan assigns both to the same physical register $R$, the resulting `mov R, R` is eliminated either immediately during post-RA rewrite or by the peephole pass (`AXS-MCOPT-022`). Coalescing MUST NOT merge two intervals if doing so would violate fixed-register or call-clobber constraints.
2. **Parallel-copy cycle breaking (`ARA-35`, `ARALLOC-43`):** Simultaneous register transfers at ABI argument setup or control-flow join edges are modeled as a parallel assignment $\{dst_i \leftarrow src_i\}$. Transfer dependencies form a directed graph whose out-degree-0 nodes are emitted first; any cycle $R_1 \leftarrow R_2 \leftarrow \dots \leftarrow R_k \leftarrow R_1$ is broken deterministically using a scratch register (`R10`/`R11`) so no live source register is overwritten before being read.
[0182 §15-16; 0235 §10, §27-28, ARA-34/35; 0252 §20, ARALLOC-43; tasks/0557 §20, AREG-34]

**AXS-RA-025 — Spill-Slot Allocation, Lifetime Coloring, and Reload/Spill Code Generation.**
1. **Typed spill slots (`AREG-26`, `ARALLOC-31`):** Every spilled virtual register $v$ is allocated a stack frame slot with byte size $\max(8, \mathrm{size}(v))$ and byte alignment $\max(8, \mathrm{align}(v))$ (16 bytes for `Vec128` / `XMM` spills, 32 bytes for `Vec256`).
2. **Spill-slot lifetime coloring (`AREG-29`, `ARA-38`, `ARALLOC-32`):** `StackSlotAllocator` maintains a list of spill slots per `(size, align)` bucket, each tracking the union of `LiveRange`s of virtual registers assigned to that slot. A newly spilled interval $I$ reuses the lowest-numbered existing spill slot in its bucket whose ranges do not intersect $I.\mathrm{ranges}$; otherwise a new spill slot is allocated.
3. **Isolation from address-taken locals (`AREG-30..32`, `AFRAME-26`, `ARALLOC-56`):** Compiler spill slots are disjoint from source-level stack slots (`LirStackSlot` addressed by `LIR_INST_STACK_ADDR`). A spill slot is never address-taken, never aliases any `view`/`mut_view` capability or raw pointer in safe Axiom code, and never shares storage with an active local object.
4. **Spill/reload insertion and memory folding (`AREG-27/28`, `ARA-30..33`):**
   - If a spilled virtual register has `remat_kind == REMAT_CONST`, each read reloads the immediate via `mov r_scratch, imm`; if `remat_kind == REMAT_STACK_ADDR`, each read reloads the address via `lea r_scratch, [rbp - slot_disp]`, eliminating stack store traffic altogether.
   - Otherwise, a definition of a spilled register emits `mov [rbp - spill_disp], r_def` immediately after the defining instruction, and a read either folds `[rbp - spill_disp]` directly into the instruction (when x86-64 encoding permits a memory operand and the other operand is a register or immediate) or emits `mov r_scratch, [rbp - spill_disp]` immediately before the instruction.
   - Spill/reload insertion MUST NOT reorder or eliminate any `volatile`, `atomic`, or trapping instruction (`AREG-47/48`).
[0182 §17-19, AREG-26..35; 0235 §16-19, §22-23, ARA-29..33, ARA-38; 0252 §14-19, §32, ARALLOC-30..35, ARALLOC-54..56; tasks/0557 §14-19, AREG-28..33, AREG-47..50]

**AXS-RA-026 — Callee-Saved Register Tracking and `FrameLayout` Integration.**
1. **Two-phase frame layout (`0182 XLIX`, `0252 §30-36`, `SPEC-04 AXS-EXT-054`):**
   - Pre-RA analysis records local stack slots (`lir.slots`) and call-site outgoing argument / shadow-space requirements (`body.shadow_space`, `body.stack_args_size`).
   - Post-RA frame lowering (`compiler/target/x64/frame.ax`) combines local stack slots, colored spill slots, and the set of callee-saved registers (`RBX`, `RSI`, `RDI`, `R12`–`R15`, and `XMM6`–`XMM15`) into `X64FrameLayout` and rewrites all `X64_OP_FRAME` operands to concrete `[rbp - disp]` memory operands.
2. **Callee-saved preservation (`AFRAME-23`, `ARA-37`, `ARALLOC-29`):** Every callee-saved register modified by the function body MUST be saved in the prologue before its first write and restored in the exact reverse order in every epilogue before `ret`.
3. **Alignment, shadow space, and stack probes (`INV-PIPE-005`, `AFRAME-21/22`):**
   - On Windows x64 (`CallConv.Win64`), any function that emits a `call` (or has `shadow_space > 0`) reserves at least `X64_MIN_SHADOW_SPACE = 32` bytes of shadow space at the bottom of the frame.
   - Total stack allocation below the saved frame pointer (`callee_saved_bytes + frame_size`) MUST be a multiple of 16 bytes so `RSP` is 16-byte aligned before every `call` instruction (`(frame_size + 56) % 16 == 0` when the 7 non-volatile GPRs are pushed after `push rbp`).
   - Whenever `frame_size >= X64_PAGE_PROBE_THRESHOLD` (4096 bytes), the prologue emits the inline 4096-byte page probe loop touching each guard page in descending order before adjusting `RSP` (`ADR-0003`, `INV-PIPE-005`).
[0182 §25-30, AFRAME-20..30; 0235 ARA-37; 0252 §30-36, §41, ARALLOC-29/39..42; SPEC-04 AXS-EXT-054]

**AXS-RA-027 — Post-RA Machine IR Verifier Contract (`INV-PIPE-005`).**
Before byte encoding, `x64_verify_checked(body, layout)` MUST return `X64_VERIFY_OK` (`0`), certifying:
1. Every register operand `X64_OP_REG` names a valid physical register (`0 <= reg <= 15`, no virtual registers remaining, `ARA-39/40`) and no `X64_OP_FRAME` operand remains unresolved.
2. No instruction has two memory operands (`X64_VERIFY_ERR_MEM_MEM`).
3. Every opcode's operand kinds satisfy x86-64 encoding rules (`X64_VERIFY_ERR_OPERAND_FORM`, `X64_VERIFY_ERR_IMUL_FORM`, `X64_VERIFY_ERR_LEA_FORM`, `X64_VERIFY_ERR_SHIFT_REG_CLASS`, `X64_VERIFY_ERR_SHIFT_FORM`, `X64_VERIFY_ERR_IDIV_FORM`).
4. Frame invariants hold: `shadow_space == 0 || shadow_space >= 32` (`X64_VERIFY_ERR_SHADOW_SPACE`), `(frame_size + 56) % 16 == 0` when `shadow_space > 0` (`X64_VERIFY_ERR_ALIGNMENT`), and `frame_size >= shadow_space` (`X64_VERIFY_ERR_FRAME_SIZE`).
Any failure of `x64_verify_checked` on compiler-generated Machine IR is a fatal internal compiler error (`AX_ICE_INTERNAL` with `data.stage = "x64_verify"`, exit code 3, `AXD-042`).
[0182 §24; 0235 §48; 0252 §42-43, ARALLOC-22/50; tasks/0557 §25, AREG-36/44/51; ADR-0003]

---

## 4. Pattern-Matching Instruction Selection & Branchless If-Conversion

**AXS-MCOPT-010 — Scaled-Index Address Mode Formation and `lea` Selection (`REQ-OPT-205`).**
During LIR → Machine IR instruction selection (`compiler/lir` and `compiler/target/x64/isel.ax`), address and wrapping arithmetic trees matching:
$$\mathrm{addr} = \mathrm{base} + \mathrm{index} \times \mathrm{scale} + \mathrm{disp}$$
where `scale` $\in \{1, 2, 4, 8\}$ (either a multiplication by $1, 2, 4, 8$ or a left shift `index << k` with $k \in \{0, 1, 2, 3\}$) and `disp` fits in signed 32-bit `i32` (`-2147483648..=2147483647`), are lowered as follows:
1. **Memory operand folding:** When `addr` is the pointer operand of `LIR_INST_LOAD` or `LIR_INST_STORE`, the address tree is folded directly into the load or store's `X64Mem { base, index, scale, disp, is_rip: false }` operand without emitting separate `imul`/`shl`/`add` instructions.
2. **`lea` arithmetic selection:** When `addr` is computed by `LIR_INST_OFFSET`, `LIR_INST_STACK_ADDR`, or a non-trapping (wrapping) 64-bit integer addition/shift tree, instruction selection emits a single `lea dst, [base + index*scale + disp]` instruction (`X64_MI_LEA`). This computes the linear combination in one three-operand non-destructive instruction without clobbering `base`, `index`, or `EFLAGS`.
3. **Checked-arithmetic exclusion (`REQ-OPT-205`, `ACTRL-46`, `AFINAL-32`):** Operations that check for signed or unsigned overflow (`LIR_INST_SADD_OVERFLOW`, `LIR_INST_UADD_OVERFLOW`, `LIR_INST_SSUB_OVERFLOW`, `LIR_INST_USUB_OVERFLOW`, `LIR_INST_SMUL_OVERFLOW`, `LIR_INST_UMUL_OVERFLOW`) MUST NOT be folded into `lea`, because `lea` never updates `EFLAGS.OF` or `EFLAGS.CF` required by the subsequent `X64_MI_ASSERT` overflow check.
[0162 §8, §39; tasks/0406 §30, AMICRO-28; tasks/0559 §12-13, AFINAL-25/32]

**AXS-MCOPT-011 — Immediate and Single-Use Memory Operand Folding (`REQ-OPT-205`).**
1. **32-bit signed immediate folding:** When an operand of `add`, `sub`, `and`, `or`, `xor`, `cmp`, `test`, or `mov` is a `LIR_INST_CONST` whose value fits in signed 32-bit `i32` (`-2^31 .. 2^31 - 1`), instruction selection folds the immediate directly as `X64_OP_IMM` instead of allocating a temporary register and emitting a preceding `mov reg, imm64`.
2. **Immediate shift counts:** When the shift count of `LIR_INST_SHL`, `LIR_INST_SHR`, or `LIR_INST_SAR` is a compile-time constant $c$, instruction selection emits `shl`/`shr`/`sar dst, (c & mask)` with `X64_OP_IMM` (where `mask` is `63` for 64-bit operands and `31` for 32-bit operands), avoiding `RCX` precoloring and register copies.
3. **Memory-operand folding barrier (`REQ-OPT-204`, `REQ-OPT-205`):** A single-use `LIR_INST_LOAD` in the same basic block may be folded into the source memory operand of an arithmetic or comparison instruction only if the load is non-volatile, non-atomic, and no store, call, or trapping instruction intervenes between the load and its use.
[0162 §39; 0237 §14-15; tasks/0406 §30, AMICRO-27/28]

**AXS-MCOPT-012 — Strength Reduction of Constant Multiplication, Division, and Remainder (`REQ-OPT-205`).**
For compile-time constant operands in arithmetic instructions:
1. **Power-of-two and small-constant multiplication (wrapping / non-checked):**
   - `x * (2^k)` ($0 \le k < 64$) lowers to `shl dst, k` (or `mov dst, 0` for $x \times 0$, `mov dst, x` for $x \times 1$).
   - `x * 3`, `x * 5`, and `x * 9` lower to `lea dst, [x + x*2]`, `lea dst, [x + x*4]`, and `lea dst, [x + x*8]` respectively.
   - Checked multiplications (`LIR_INST_SMUL_OVERFLOW`, `LIR_INST_UMUL_OVERFLOW`) retain `imul`/`mul` + `jo`/`jb` trap checks unless range analysis (`E15.3`) has already proven the multiplication cannot overflow.
2. **Unsigned division and remainder by constants (`LIR_INST_UDIV`, `LIR_INST_UREM`, `LIR_INST_UDIV_OVERFLOW`, `LIR_INST_UREM_OVERFLOW`):**
   - For a non-zero power-of-two divisor $d = 2^k$ ($k \ge 0$), unsigned division never overflows or traps: `x / 2^k` lowers to `shr dst, k`, and `x % 2^k` lowers to `and dst, (2^k - 1)`.
   - For general non-zero constant divisors $d > 1$, unsigned division may lower to a 64-bit magic-number high-multiply (`mul`) and shift sequence that is bit-exact over all `u64` inputs.
3. **Signed division and remainder by constants (`LIR_INST_DIV`, `LIR_INST_REM`, `LIR_INST_SDIV_OVERFLOW`, `LIR_INST_SREM_OVERFLOW`):**
   - When the divisor is a compile-time constant $d \notin \{0, -1\}$, neither division-by-zero nor `i64.MIN / -1` signed overflow can occur, so the `Assert` trap check is provably unreachable.
   - For $d = 2^k$ ($1 \le k < 63$), signed division rounds toward zero by adding the sign bias $(2^k - 1)$ when $x < 0$ before shifting right arithmetically by $k$:
     ```text
     mov r_tmp, r_src
     sar r_tmp, 63          // -1 if r_src < 0, else 0
     shr r_tmp, (64 - k)    // (2^k - 1) if r_src < 0, else 0
     add r_src, r_tmp
     sar r_src, k
     ```
   - Signed remainder `x % 2^k` is computed as `x - (x / 2^k) * 2^k` (or masked sign-adjusted remainder), preserving negative remainder sign (`(-7) % 4 == -3`) identically to `idiv`.
[0162 §16-17, §39; tasks/0406 §30, AMICRO-28; tasks/0553 ACTRL-44..46]

**AXS-MCOPT-013 — Branchless If-Conversion (`cmovcc` / `setcc`) Legality and Cost Contract (`REQ-OPT-207`, `REQ-OPT-208`, `REQ-OPT-369`, `REQ-OPT-370`).**
1. **Optional representation transform (`REQ-OPT-208`, `REQ-OPT-369`, `REQ-OPT-370`):** An `if`/`else` expression or conditional assignment in Axiom source does not require a conditional branch instruction (`jcc`) in machine code. The compiler may convert a conditional control-flow diamond (`bb_head` branching on condition $C$ to single-predecessor blocks `bb_then` and `bb_else`, both jumping to `bb_join`) or a boolean value assignment into straight-line branchless instructions (`cmp`/`test` + `cmovcc` or `setcc` + `movzx`).
2. **Strict legality preconditions (`REQ-OPT-207`, `ACTRL-26..46`):** If-conversion is legal if and only if **every** instruction inside `bb_then` and `bb_else` satisfies:
   - **No observable side effects (`ACTRL-29..36`):** No function calls (`LIR_INST_CALL` / `X64_MI_CALL`), no I/O or foreign calls, no `Drop` glue, no memory writes (`LIR_INST_STORE`), no `volatile` reads/writes, and no `atomic` operations or fences.
   - **No traps or panics (`ACTRL-35/46`):** No `LIR_TERM_ASSERT` / `X64_MI_ASSERT`, no checked arithmetic (`*_OVERFLOW`), and no potentially trapping division/remainder (`div`, `idiv`, `rem`, `urem` by a variable or zero).
   - **No unsafe memory speculation (`ACTRL-42`):** Neither arm performs a pointer dereference (`LIR_INST_LOAD`) unless the address is a non-volatile local stack slot (`LirStackSlot`) guaranteed valid on entry to `bb_head`.
3. **Profitability and register-pressure gate (`REQ-OPT-199..201`, `AXS-MCOPT-004`):**
   - Each arm of the diamond contains at most `MAX_CMOV_INSTS = 4` pure scalar instructions.
   - Evaluating both arms before `cmovcc` increases live register demand by at most 2 registers and does not push block register pressure above the allocatable `Gpr` limit.
   - If the branch condition is statically known or profiled (`--pgo-use`) as highly predictable ($P(\text{taken}) > 0.95$ or $< 0.05$, e.g., loop exit or cold error check) and the arm has $> 1$ instruction, branched `jcc` is retained so the cold arm is not needlessly executed on the critical path (`tasks/0553 §42`).
4. **x86-64 `cmovcc` encoding rules:**
   - x86-64 `cmovcc dst_reg, src_reg_or_mem` (opcode `0F 40+cc /r`) supports 16-bit, 32-bit, and 64-bit register destinations and register/memory sources, never immediate sources and never 8-bit operands.
   - When an arm yields an immediate constant, instruction selection materializes the immediate into a register before `cmovcc`; when selecting `1` vs. `0` from condition flags, instruction selection emits `setcc reg8` + `movzx reg64, reg8` (or `xor reg, reg` before `cmp` + `setcc`).
[tasks/0406 §30, AMICRO-30/31; tasks/0553 §1-2, §42, §46-49, ACTRL-20..56, ACTRL-81..84; tasks/0559 §11]

**AXS-MCOPT-014 — Branch Probability Discipline (`REQ-OPT-036`, `REQ-OPT-212`).**
The machine optimizer and block-layout engine MUST NOT invent branch probabilities from variable names or syntactic ordering assumptions (`REQ-OPT-036`). Branch weights come solely from:
1. Structural CFG properties: loop backedges are predicted taken; `LIR_TERM_ASSERT` failure edges and `LIR_TERM_UNREACHABLE` blocks are marked cold.
2. Profile-guided execution counts (`--pgo-use`, `E15.6`).
Cold blocks (`Assert` failure traps) remain semantically reachable and executable whenever their guard condition fails (`ACTRL-76/77`).
[0237 §35; tasks/0553 §45, ACTRL-22/23/52/53/76/77]

---

## 5. Post-RA Machine Optimization & Peephole Engine

**AXS-MCOPT-020 — Post-RA Peephole Architecture (`REQ-OPT-015`, `REQ-OPT-030`, `REQ-OPT-031`, `REQ-OPT-371`, `REQ-OPT-372`).**
The post-RA machine optimizer (`compiler/backend/peephole`, delivered in `T628`) runs on physical `X64MIBody` after register allocation and `X64FrameLayout` slot rewriting and immediately before final `x64_verify` and binary encoding:
- All transformations operate on structured `X64MI` instruction nodes and `X64Op` operands — never via textual assembly string matching (`tasks/0559 §7`).
- Every rewrite is local to a single `X64MIBb` (or adjacent basic-block branch terminators) and preserves `X64MIBody` well-formedness (`AFINAL-21/22/41`).
[0237 §1-3, §17; tasks/0559 §1-7, AFINAL-20..22, AFINAL-41..50]

**AXS-MCOPT-021 — Explicit `EFLAGS` Liveness and Dead-Flag Contract (`REQ-OPT-033`).**
Condition flags (`EFLAGS`: `CF`, `OF`, `ZF`, `SF`, `PF`) are modeled explicitly as a physical machine resource (`0237 §9-11`, `tasks/0559 §8-9`, `AFINAL-23`):
1. **Instruction flag classification:**
   - `FLAGS_DEF` (overwrites `EFLAGS` without reading prior flags): `X64_MI_ADD`, `X64_MI_SUB`, `X64_MI_IMUL`, `X64_MI_MUL`, `X64_MI_AND`, `X64_MI_OR`, `X64_MI_XOR`, `X64_MI_SHL`, `X64_MI_SAR`, `X64_MI_SHR`, `X64_MI_CMP`, `X64_MI_TEST`. (Note: shift by immediate `0` does not modify flags and is eliminated when `imm == 0`).
   - `FLAGS_USE` (reads `EFLAGS`): `X64_MI_JCC`, `X64_MI_SETCC`, `X64_MI_CMOVCC`, `X64_MI_ASSERT` (which encodes the `jo`/`jb`/`je` trap check for checked arithmetic).
   - `FLAGS_PRESERVE` (neither reads nor modifies `EFLAGS`): `X64_MI_MOV`, `X64_MI_LEA`, `X64_MI_PUSH`, `X64_MI_POP`, `X64_MI_JMP`.
   - `FLAGS_KILL` (destroys `EFLAGS` or exits the function without reading `EFLAGS`): `X64_MI_CALL`, `X64_MI_IDIV`, `X64_MI_RET`.
2. **Dead-flag predicate (`flags_are_dead_after(inst)`):** Scanning forward from `inst.next` within the same basic block `mbb`:
   - Skip instructions in `FLAGS_PRESERVE`.
   - If the first non-preserving instruction is in `FLAGS_DEF` or `X64_MI_RET` or `X64_MI_CALL` or `X64_MI_IDIV`, then `EFLAGS` are **provably dead** after `inst` (`true`).
   - If the scan reaches an instruction in `FLAGS_USE` (`jcc`, `setcc`, `cmovcc`, `assert`) or reaches the end of `mbb` without encountering a `FLAGS_DEF` or `FLAGS_KILL` instruction, `EFLAGS` are **conservatively live** (`false`).
3. **Mandatory flag-preservation rule (`REQ-OPT-033`, `AMOPT-24`, `AFINAL-23`):**
   - No instruction in `FLAGS_DEF` (including algebraic identities such as `add r, 0`, `sub r, 0`, `or r, 0`, `xor r, 0`, `and r, -1`) may be deleted or replaced by a `FLAGS_PRESERVE` instruction (`mov`, `lea`) unless `flags_are_dead_after(inst)` is `true`.
   - No instruction in `FLAGS_PRESERVE` (such as `mov r, 0` or `lea r, [r + c]`) may be replaced by a `FLAGS_DEF` instruction (such as `xor r, r` or `add r, c`) unless `flags_are_dead_after(inst)` is `true`.
[0237 §9-11, AMOPT-24; tasks/0559 §8-9, AFINAL-23]

**AXS-MCOPT-022 — Redundant Move and Identity Instruction Elimination (`REQ-OPT-033`).**
The post-RA peephole pass eliminates the following redundant instructions:
1. **Self-move (`mov r, r`):** `X64_MI_MOV` where `ops[0].kind == X64_OP_REG`, `ops[1].kind == X64_OP_REG`, `ops[0].reg == ops[1].reg`, and `size == 8` is unconditionally deleted (`mov` is in `FLAGS_PRESERVE`).
2. **Back-to-back reverse copy (`mov r1, r2; mov r2, r1`):** When `mov r1, r2` (both 64-bit `X64_OP_REG`) is immediately followed in the same basic block by `mov r2, r1`, the second instruction `mov r2, r1` is deleted.
3. **Overwrite of dead register copy (`mov r1, src1; mov r1, src2`):** When `mov r1, src1` is immediately followed by `mov r1, src2` where `src2` does not read `r1` (neither as `src2.reg` nor as `src2.mem.base`/`src2.mem.index`), the first `mov r1, src1` is deleted.
4. **No-op `lea` (`lea r, [r + 0]`):** `X64_MI_LEA` with `ops[0].reg == ops[1].mem.base`, `ops[1].mem.index == REG_NONE`, `ops[1].mem.disp == 0`, `ops[1].mem.is_rip == false`, and `size == 8` is unconditionally deleted (`lea` is in `FLAGS_PRESERVE`).
5. **Algebraic no-ops (`add r, 0`, `sub r, 0`, `or r, 0`, `xor r, 0`, `shl r, 0`, `shr r, 0`, `sar r, 0`):** Deleted **if and only if** `ops[0].kind == X64_OP_REG`, `ops[1].kind == X64_OP_IMM`, `ops[1].imm == 0`, `size == 8`, and `flags_are_dead_after(inst)` is `true` (`REQ-OPT-033`).
[0237 §2, §7-9, §17, AMOPT-29/30; tasks/0559 §15-16]

**AXS-MCOPT-023 — Flag-Safe Target Idiom Peepholes (`xor r, r` and `test r, r`).**
1. **Zero-register materialization (`mov r, 0` → `xor r, r`):** An instruction `mov r, 0` (`ops[0].kind == X64_OP_REG`, `ops[1].kind == X64_OP_IMM`, `ops[1].imm == 0`) is rewritten in-place to `xor r, r` **if and only if** `flags_are_dead_after(inst)` is `true` (`AXS-MCOPT-021`). If `EFLAGS` are live (for instance, between a comparison/checked operation and a branch/assert), `mov r, 0` MUST remain `mov r, 0`.
2. **Comparison against zero (`cmp r, 0` → `test r, r`):** An instruction `cmp r, 0` (`ops[0].kind == X64_OP_REG`, `ops[1].kind == X64_OP_IMM`, `ops[1].imm == 0`) is rewritten to `test r, r` (`ops[0] = reg(r)`, `ops[1] = reg(r)`), which has a shorter encoding, avoids immediate decoding, and sets `ZF`, `SF`, `PF` identically with `CF = 0` and `OF = 0`.
3. **Strength-reduced addition/subtraction of `0` in `lea` (`lea r1, [r2 + 0]` → `mov r1, r2`):** When `lea r1, [r2 + 0]` has `index == REG_NONE`, `disp == 0`, and `is_rip == false`, it rewrites to `mov r1, r2` (or is deleted if `r1 == r2`).
[0237 §14-18; tasks/0559 §10, §17-18, §31-32]

**AXS-MCOPT-024 — Memory, Volatile, Atomic, and Call Barriers (`REQ-OPT-032`, `REQ-OPT-034`, `REQ-OPT-035`).**
1. **Non-eliminable side-effecting instructions (`REQ-OPT-032`):** The machine optimizer MUST NEVER delete or skip:
   - Any `volatile` memory load or store (`SPEC-04 AXS-EXT-051`, `@at` / `Mmio` / `Volatile`),
   - Any `atomic` read, write, read-modify-write (`lock ...`), or fence (`mfence`/`lfence`/`sfence`),
   - Any potentially trapping instruction (`X64_MI_ASSERT`, `X64_MI_IDIV`),
   - Any `X64_MI_CALL` instruction.
2. **Redundant stack store elimination (`REQ-OPT-034`):** Given two adjacent stores `mov [rbp - disp1], r1` and `mov [rbp - disp2], r2` in the same basic block, the first store may be eliminated **if and only if** both operands refer to the exact same non-volatile, non-atomic stack-frame address (`base == REG_RBP`, `index == REG_NONE`, `disp1 == disp2`, `size1 == size2`, `is_rip == false`). Stores through arbitrary base pointers (`base != REG_RBP`) MUST NOT be eliminated unless proven dead and non-volatile/non-atomic (`REQ-OPT-034`).
3. **Store-to-load forwarding and call barriers (`REQ-OPT-035`):** Given a stack-frame store `mov [rbp - disp], r1` followed by a load `mov r2, [rbp - disp]` of identical width in the same basic block:
   - If no instruction between the store and load writes to `[rbp - disp]`, modifies `r1`, performs an unknown-base memory store, executes a `volatile`/`atomic` operation, or executes a `call`, the load is rewritten to `mov r2, r1` (and eliminated if `r1 == r2`).
   - Store-to-load forwarding MUST NEVER cross an intervening `X64_MI_CALL` or potential alias mutation (`REQ-OPT-035`).
[0237 §5-6, §19-22, AMOPT-25..32; tasks/0559 §21-22, §27, AFINAL-26..31]

**AXS-MCOPT-025 — Control-Flow and Branch Peephole Optimizations.**
Within `X64MIBody`:
1. **Redundant fall-through jump removal:** If the last instruction of basic block `b` is an unconditional `jmp target_bb` (`X64_MI_JMP`) where `target_bb == (b + 1)` (the immediately following basic block in emission order), the `jmp` instruction is removed so execution falls through directly with zero branch overhead.
2. **Branch condition inversion over fall-through:** If basic block `b` ends with `jcc cc, (b + 1)` followed immediately by `jmp target_else`, it is rewritten to `jcc (cc ^ 1), target_else` (inverting the condition code `cc ^ 1`) and the fall-through `jmp (b + 1)` is removed.
3. **Trivial jump-to-jump threading:** If `jmp target_bb` or `jcc cc, target_bb` targets a block `target_bb` that contains only a single unconditional `jmp final_bb` (and `final_bb != target_bb`, preventing infinite loop collapse), the branch target is redirected to `final_bb`.
[0237 §33-38, AMOPT-33/34; tasks/0559 §19]

**AXS-MCOPT-026 — Post-Optimization Verification and Provenance Preservation (`INV-PIPE-005`, `REQ-OPT-371`, `REQ-OPT-372`).**
1. Every peephole transformation preserves the source span and debug location mapping of the transformed instruction (`SPEC-04 AXS-EXT-054`, `AMOPT-41`, `AFINAL-36`).
2. After the post-RA peephole pass completes on `X64MIBody`, `x64_verify(body, layout)` MUST be invoked before `x64_emit_mi_body_obj` / `x64_emit_mi_body_mc` encodes the instructions into section bytes (`INV-PIPE-005`, `AFINAL-42/50`).
[0237 §57-59, AMOPT-41/42; tasks/0559 §29, §33-34, AFINAL-36/42/50]

---

## 6. Canonical Axiom Examples (Positive & Negative Cases)

All examples use canonical Axiom surface syntax (`=` for bindings and assignment, `.` for paths; no `:=`, no `var`, no `::`).

### 6.1 Positive — Scaled-Index `lea` Addressing and Loop Register Allocation (`AXS-RA-015`, `AXS-RA-021`, `AXS-MCOPT-010`)
```axiom
module examples.regalloc_lea

pub fn weighted_dot(xs: view<[i64]>, ys: view<[i64]>, n: usize) -> i64 {
    let mut acc: i64 = 0i64
    let mut i: usize = 0
    while i < n {
        // Loop depth d = 1 -> spill_weight scaled by 10^1.
        // `acc`, `i`, `n`, and slice base pointers stay in physical GPRs
        // (`RBX`, `RSI`, `RDI`, `R12`..`R15` / volatile GPRs) with zero stack spills.
        // Indexing `xs[i]` and `ys[i]` folds `base + i * 8` into `[base + index*8]`.
        acc = acc + xs[i] * ys[i]
        i = i + 1
    }
    acc
}
```

### 6.2 Positive — High Register Pressure, Call Clobbers, and Fixed-Register `idiv` / Shifts (`AXS-RA-022`, `AXS-RA-023`, `AXS-RA-025`, `AXS-RA-026`)
```axiom
module examples.regalloc_pressure

fn step_helper(v: i64) -> i64 {
    v + 1i64
}

pub fn high_pressure_kernel(seed: i64, shift: u32, denom: i64) -> i64 {
    // Live ranges spanning across `step_helper(a0)` have `crosses_call = true`
    // and are assigned to callee-saved GPRs (`RBX`, `RSI`, `RDI`, `R12`..`R15`)
    // or spilled to colored stack slots `[rbp - disp]`.
    let a0 = seed + 1i64
    let a1 = seed + 2i64
    let a2 = seed + 3i64
    let a3 = seed + 4i64
    let a4 = seed + 5i64
    let a5 = seed + 6i64
    let a6 = seed + 7i64
    let a7 = seed + 8i64
    let a8 = seed + 9i64
    let a9 = seed + 10i64

    let c = step_helper(a0)

    // Variable shift precolors shift count into `RCX` (`CL`).
    let shifted = (a1 + a2 + a3 + a4) << shift

    // Signed division precolors dividend into `RDX:RAX` and clobbers both `RAX` and `RDX`.
    let quot = (shifted + a5 + a6 + a7 + a8 + a9 + c) / denom
    quot
}
```

### 6.3 Positive — Branchless `cmovcc` If-Conversion on Pure Diamond (`AXS-MCOPT-013`, `REQ-OPT-369`, `REQ-OPT-370`)
```axiom
module examples.branchless_cmov

pub fn clamp_i64(x: i64, lo: i64, hi: i64) -> i64 {
    // Both arms of each `if` are pure, trap-free scalar values.
    // Lowered to `cmp` + `cmovl` / `cmovg` without conditional branches (`jcc`).
    let low_clamped = if x < lo { lo } else { x }
    let res = if low_clamped > hi { hi } else { low_clamped }
    res
}
```

### 6.4 Negative (Transformation Rejected) — Checked/Trapping Arm Forbidden in `cmovcc` (`AXS-MCOPT-013`, `REQ-OPT-207`)
```axiom
module examples.no_speculate_trap

pub fn guarded_divide(x: i64, d: i64) -> i64 {
    // NEGATIVE IF-CONVERSION CASE:
    // The `else` arm performs `x / d`, which traps when `d == 0` or `x == i64.MIN && d == -1`.
    // Speculatively evaluating `x / d` before a `cmov` when `d == 0` would trap!
    // By `AXS-MCOPT-013` (precondition 2) and `REQ-OPT-207`, the backend MUST keep
    // the conditional branch `cmp d, 0; je bb_zero` and MUST NOT if-convert to `cmov`.
    if d == 0i64 {
        0i64
    } else {
        x / d
    }
}
```

### 6.5 Negative (Transformation Rejected) — Live `EFLAGS` Barrier on `xor r, r` and Identity Elimination (`AXS-MCOPT-021`, `REQ-OPT-033`)
```axiom
module examples.eflags_barrier

pub fn checked_add_with_zero(a: i64, b: i64) -> i64 {
    // Checked addition lowers to:
    //   add rax, rcx          ; sets OF on signed 64-bit overflow
    //   assert NO_OVERFLOW    ; reads EFLAGS.OF (`jo` trap)
    // NEGATIVE PEEPHOLE CASE:
    // Any instruction inserted or optimized between `add` and `assert` (or before `jcc`/`setcc`)
    // has `flags_are_dead_after == false`. By `AXS-MCOPT-021` (`REQ-OPT-033`):
    //   1. `add rax, 0` MUST NOT be eliminated if a subsequent `jcc`/`setcc` reads ZF/SF/OF.
    //   2. `mov rdx, 0` MUST NOT be rewritten to `xor rdx, rdx` while `EFLAGS.OF` is live.
    a + b
}
```

---

## 7. Requirement & Conformance Traceability Matrix

| Requirement | Summary | Canonical Rule(s) in SPEC-77 | Delivering / Verifying Tasks |
|---|---|---|---|
| `REQ-OPT-015` | Target-specific optimizations (scheduling, peephole, coalescing) run at Machine IR level | `AXS-MCOPT-001`, `AXS-RA-024`, `AXS-MCOPT-020` | `T627`, `T063`, `T628`, `T629` |
| `REQ-OPT-030` | Post-RA machine optimizer MUST NOT change program semantics | `AXS-MCOPT-002`, `AXS-MCOPT-020` | `T627`, `T628`, `T629` |
| `REQ-OPT-031` | Machine optimizer operates solely on physical registers, memory, flags, CFG, ABI, and target features | `AXS-MCOPT-001`, `AXS-MCOPT-020` | `T627`, `T628` |
| `REQ-OPT-032` | Never eliminate dead instructions with volatile, atomic, trap, or unproven call side effects | `AXS-MCOPT-024` | `T627`, `T628`, `T629` |
| `REQ-OPT-033` | Never eliminate an identity operation or clobber flags if `EFLAGS` modification is subsequently used | `AXS-MCOPT-021`, `AXS-MCOPT-022`, `AXS-MCOPT-023` | `T627`, `T628`, `T629` |
| `REQ-OPT-034` | Peephole store elimination requires proven deadness and no volatile/atomic/aliasing effects | `AXS-MCOPT-024` | `T628`, `T629` |
| `REQ-OPT-035` | No store-to-load forwarding across an intervening call or unproven alias | `AXS-MCOPT-024` | `T628`, `T629` |
| `REQ-OPT-036` | Branch probabilities rely on static CFG structure, compiler hints, or PGO data | `AXS-MCOPT-014` | `T628` |
| `REQ-OPT-197` | Microarchitecture optimization never changes Axiom semantics | `AXS-MCOPT-002` | `T627`, `T063`, `T628` |
| `REQ-OPT-198` | ISA semantics and microarchitecture cost are distinct | `AXS-MCOPT-003` | `T627`, `T628` |
| `REQ-OPT-199` | Cost models influence optimization decisions only | `AXS-MCOPT-003`, `AXS-MCOPT-013` | `T627`, `T628` |
| `REQ-OPT-200` | Latency and throughput are distinct cost dimensions | `AXS-MCOPT-003` | `T627`, `T628` |
| `REQ-OPT-201` | Register pressure participates in profitability decisions | `AXS-MCOPT-004`, `AXS-RA-015`, `AXS-MCOPT-013` | `T627`, `T063`, `T628` |
| `REQ-OPT-202` | Spill cost is modeled explicitly | `AXS-MCOPT-004`, `AXS-RA-015` | `T627`, `T063` |
| `REQ-OPT-203` | Instruction scheduling preserves all semantic dependencies | `AXS-MCOPT-005`, `AXS-RA-013` | `T063`, `T629` |
| `REQ-OPT-204` | Memory, atomic, volatile, and foreign effects constrain scheduling | `AXS-MCOPT-005`, `AXS-MCOPT-011` | `T063`, `T628` |
| `REQ-OPT-205` | Instruction fusion / complex addressing requires semantic equivalence | `AXS-MCOPT-010`, `AXS-MCOPT-011`, `AXS-MCOPT-012` | `T628`, `T629` |
| `REQ-OPT-207` | Branch optimization preserves observable evaluation order | `AXS-MCOPT-013` | `T628`, `T629` |
| `REQ-OPT-208` | Branchless transformation is optional optimization, not semantic lowering | `AXS-MCOPT-013` | `T628`, `T629` |
| `REQ-OPT-212` | PGO changes profitability decisions, never semantics | `AXS-MCOPT-002`, `AXS-RA-015`, `AXS-MCOPT-014` | `T063`, `T628` |
| `REQ-OPT-218` | Machine scheduling and allocation are deterministic under reproducible configuration | `AXS-MCOPT-005`, `AXS-RA-012`, `AXS-RA-013`, `AXS-RA-021` | `T063`, `T629` |
| `REQ-OPT-369` | Optimal machine control flow may be transformed into `select` / `cmovcc` / masked operations | `AXS-MCOPT-013` | `T628`, `T629` |
| `REQ-OPT-370` | An `if` in Axiom does not mandate a machine branch when semantics are preserved | `AXS-MCOPT-013` | `T628`, `T629` |
| `REQ-OPT-371` | Late machine optimization is the final optimization step and does not define semantics | `AXS-MCOPT-001`, `AXS-MCOPT-020`, `AXS-MCOPT-026` | `T629` |
| `REQ-OPT-372` | Final machine function representation remains an IR prior to byte encoding | `AXS-MCOPT-001`, `AXS-MCOPT-020`, `AXS-MCOPT-026` | `T629` |

---

## 8. Sources
- `docs/base/specs/0162 - AXIOM LIR v0.1.md` (§5–12, §16–20, §27, §36–40, §43)
- `docs/base/specs/0182 - XLVIII — REGALLOC-001 Register Allocation.md` (§1–35, `AREG-20..36`, `XLIX — FRAME-001`, `AFRAME-20..30`)
- `docs/base/specs/0235 - MACHINE-IR-004 — Register Allocation.md` (§1–51, `ARA-20..44`)
- `docs/base/specs/0237 - 1. Mục tiêu.md` (`MACHINE-IR-006 — Machine Optimization & Peephole Optimization`, §1–60, `AMOPT-20..42`)
- `docs/base/specs/0252 - COMPILER-010 — Register Allocation + SpillReload + Frame Integration.md` (§1–51, `ARALLOC-20..60`)
- `docs/base/tasks/0406 - BOOTSTRAP-147 — CPU Microarchitecture-Aware Optimization & Instruction-Level Optimization.md` (§1–30, `AMICRO-20..45`)
- `docs/base/tasks/0553 - BOOTSTRAP-294 — AXIOM PREDICATION, CONTROL-FLOW IF-CONVERSION & BRANCH OPTIMIZATION ENGINE.md` (§1–55, `ACTRL-20..100`)
- `docs/base/tasks/0557 - BOOTSTRAP-298 — AXIOM REGISTER ALLOCATION, SPILL & RELOAD ENGINE.md` (§1–36, `AREG-20..51`)
- `docs/base/tasks/0559 - BOOTSTRAP-300 — AXIOM LATE MACHINE OPTIMIZATION & FINAL MACHINE IR ENGINE.md` (§1–38, `AFINAL-20..50`)
- `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-050..060`), `spec/invariants.md` (`INV-DET-001`, `INV-PIPE-004..005`, `INV-ORACLE-001..002`), `spec/decisions/ADR-0003-backend-pipeline-robustness.md`
