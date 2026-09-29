# BOOTSTRAP-577 — COMPILER REGISTER ALLOCATION 3.0
## SSA DESTRUCTION, LIVE-RANGE ANALYSIS, LINEAR SCAN, GRAPH/COLORING ALLOCATION, COALESCING, SPILLING, REMATERIALIZATION, CALL-CLOBBERED REGISTERS & TARGET-AWARE REGISTER ASSIGNMENT

**Trạng thái: COMPLETED / LOCKED**

`577` chuẩn hóa register allocation của Axiom từ Machine IR có virtual register thành machine code có **physical register + stack slot**, đồng thời bảo đảm ABI, SIMD, calls, atomics, exceptions, async state và debug information.

Mục tiêu:

> Tối đa hóa hiệu năng thực thi và giảm kích thước binary nhưng không biến register allocator thành một bottleneck của compiler.

---

# 577.1. Vị trí trong backend

```text
Optimized MIR
     ↓
Machine Lowering
     ↓
Machine IR
     ↓
Target Legalization
     ↓
Liveness Analysis
     ↓
Live Intervals
     ↓
Register Allocation
     ├── Physical Registers
     └── Spill Slots
     ↓
SSA Destruction
     ↓
Copy Coalescing
     ↓
Machine Cleanup
     ↓
Scheduling
     ↓
Prologue/Epilogue
     ↓
Encoder
```

---

# 577.2. Virtual register

Machine IR trước allocation sử dụng virtual registers:

```text
%v1
%v2
%v3
```

---

# 577.3. Physical register

Sau allocation:

```text
%v1 → RAX
%v2 → RCX
%v3 → XMM0
```

---

# 577.4. Register class

Mỗi virtual register phải thuộc register class.

```text
GPR
FPR
SIMD
MASK
VECTOR
SPECIAL
```

Target có thể định nghĩa thêm class.

---

# 577.5. Register bank

Backend phải hỗ trợ register bank nếu ISA có nhiều register file.

---

# 577.6. Register aliases

Ví dụ x86:

```text
RAX
EAX
AX
AL
```

phải được biểu diễn như các alias của cùng register resource.

---

# 577.7. Register units

Allocator phải hiểu partial-register overlap.

---

# 577.8. Reserved registers

Backend đánh dấu register dành cho:

- stack pointer;
- frame pointer;
- thread pointer;
- ABI special registers;
- runtime;
- linker/OS conventions.

---

# 577.9. Allocatable registers

Chỉ register được target/ABI đánh dấu allocatable mới được dùng.

---

# 577.10. Caller-saved

Allocator phải biết register bị clobber bởi call.

---

# 577.11. Callee-saved

Nếu function dùng callee-saved register, prologue/epilogue phải preserve nó.

---

# 577.12. Call-preserved analysis

Allocator tính chi phí sử dụng caller/callee-saved register.

---

# 577.13. Call-clobber boundary

Live value qua call không được đặt vào caller-clobbered register trừ khi được spill/move.

---

# 577.14. ABI integration

Register allocation phải lấy calling convention từ `421`, không tự định nghĩa ABI riêng.

---

# 577.15. Return registers

Return values phải được đặt đúng ABI register.

---

# 577.16. Argument registers

Arguments phải được lowered vào đúng register/stack location.

---

# 577.17. Multi-register values

Wide values có thể chiếm nhiều physical registers.

---

# 577.18. Pair constraints

Target có thể yêu cầu register pair.

---

# 577.19. Fixed-register operands

Instruction có thể yêu cầu:

```text
operand → RAX
operand → XMM0
```

Allocator phải satisfy constraint.

---

# 577.20. Register masks

Instruction/call có thể khai báo register clobber mask.

---

# 577.21. Liveness

Allocator sử dụng canonical liveness từ `571`.

---

# 577.22. Live interval

Mỗi virtual register có interval:

```text
[start, end]
```

---

# 577.23. Multiple live ranges

Một value có thể có nhiều disconnected ranges.

---

# 577.24. Live-range splitting

Allocator có thể split một range thành nhiều vùng.

---

# 577.25. Hole awareness

Intervals phải hỗ trợ lifetime holes để giảm register pressure.

---

# 577.26. Use positions

Mỗi use được ghi nhận vị trí và constraint.

---

# 577.27. Def positions

Mỗi definition được ghi nhận.

---

# 577.28. Lifetime precision

Lifetime không được kéo dài hơn cần thiết nếu có thể xác định chính xác.

---

# 577.29. Dead value

Value không có use phải được eliminate trước hoặc trong allocation.

---

# 577.30. Interference

Hai live ranges overlap → không thể dùng cùng register nếu register class/alias conflict.

---

# 577.31. Register interference graph

Aggressive allocator có thể xây graph:

```text
v1 ─── v2
│ ╲
│  ╲
v3 ─── v4
```

---

# 577.32. Graph coloring

Allocator chất lượng cao có thể dùng graph coloring.

---

# 577.33. Chordal optimization

SSA interference graph có thể tận dụng tính chất chordal để allocation hiệu quả hơn.

---

# 577.34. Linear scan

Fast allocator sử dụng linear scan/live intervals.

---

# 577.35. Hybrid allocator

Axiom hỗ trợ:

```text
LinearScan
Greedy
GraphColoring
```

---

# 577.36. Allocator selection

Pass manager chọn allocator dựa trên:

```text
-O level
function size
register pressure
compile budget
target
```

---

# 577.37. O0 allocator

Ưu tiên tốc độ compiler.

---

# 577.38. O1 allocator

Linear/greedy allocator nhanh.

---

# 577.39. O2 allocator

Greedy/hybrid allocator.

---

# 577.40. O3 allocator

Aggressive allocator với splitting/coalescing/rematerialization.

---

# 577.41. Size allocator

Ưu tiên giảm spill/copy/code size.

---

# 577.42. Debug allocator

Ưu tiên location stability và debug usability.

---

# 577.43. Allocation objective

Cost model tối ưu:

```text
execution_cost
+
spill_cost
+
copy_cost
+
register_save_cost
+
code_size
+
compile_time
```

---

# 577.44. Spill

Nếu register không đủ, value được đưa vào stack spill slot.

---

# 577.45. Spill slot

Spill slot phải có:

```text
size
alignment
lifetime
type/layout metadata
```

---

# 577.46. Spill coloring

Các spill slots có non-overlapping lifetime có thể share memory.

---

# 577.47. Spill slot reuse

Allocator phải ưu tiên reuse spill slots.

---

# 577.48. Spill alignment

Alignment phải satisfy type/ABI requirements.

---

# 577.49. Large spill

Large aggregate không nên ép vào một register.

---

# 577.50. Aggregate splitting

Có thể split aggregate thành register/scalar components.

---

# 577.51. Spill cost

Spill cost phụ thuộc:

```text
load frequency
store frequency
loop depth
memory latency
code size
```

---

# 577.52. Loop spill penalty

Spill trong hot loop có penalty cao.

---

# 577.53. Spill avoidance

Allocator phải ưu tiên giữ loop-carried values trong registers.

---

# 577.54. Rematerialization

Một số values có thể tính lại thay vì load từ spill.

Ví dụ:

```text
constant
address calculation
simple immediate operation
```

---

# 577.55. Rematerialization legality

Chỉ được rematerialize nếu operation không có observable effect và semantic-equivalent.

---

# 577.56. Rematerialization cost

So sánh:

```text
recompute_cost
vs
spill_load_cost
```

---

# 577.57. Constant rematerialization

Constants thường không cần spill.

---

# 577.58. Address rematerialization

Address calculation có thể được recompute khi rẻ.

---

# 577.59. Coalescing

Copy:

```text
v1 = v2
```

có thể loại bỏ bằng cách assign cùng physical register.

---

# 577.60. Conservative coalescing

Không coalesce nếu tạo excessive interference.

---

# 577.61. Aggressive coalescing

Có thể dùng ở O3 khi benefit lớn.

---

# 577.62. Copy priority

Copies trong hot path có priority cao hơn cold copies.

---

# 577.63. Phi coalescing

SSA phi copies được ưu tiên coalesce.

---

# 577.64. Parallel copies

SSA destruction có thể tạo parallel copy:

```text
RAX ← RBX
RBX ← RAX
```

không được lower tuần tự sai semantics.

---

# 577.65. Parallel-copy resolver

Backend phải có dedicated parallel-copy resolver.

---

# 577.66. Cycle resolution

Cycle có thể cần temporary register hoặc spill slot.

---

# 577.67. Temporary selection

Chọn register không live hoặc temporary spill slot.

---

# 577.68. SSA destruction

SSA phi nodes được chuyển thành machine copies trên predecessor edges.

---

# 577.69. Critical edges

Phi lowering phải xử lý critical edge bằng edge splitting nếu cần.

---

# 577.70. Phi semantics

Parallel semantics của phi phải được preserve chính xác.

---

# 577.71. Register assignment stability

Allocator phải deterministic.

---

# 577.72. Deterministic tie breaking

Tie-break theo stable IDs:

```text
VirtualRegisterId
LiveRangeId
PhysicalRegisterId
```

---

# 577.73. Parallel allocation

Functions độc lập có thể allocate song song.

---

# 577.74. Deterministic parallel allocation

Parallel execution không được thay đổi artifact.

---

# 577.75. Register pressure analysis

Pressure được tính riêng theo register class.

---

# 577.76. Pressure peak

Allocator phải xác định các pressure peaks.

---

# 577.77. Pressure-aware optimization

`576` có thể query pressure estimate trước unrolling/vectorization.

---

# 577.78. Feedback loop

Optimization có thể rerun khi allocation cho thấy spill pressure quá cao.

---

# 577.79. Allocation-driven cleanup

Sau allocation, dead copies/dead moves có thể được eliminate.

---

# 577.80. Two-address instructions

ISA yêu cầu:

```text
dst = dst + src
```

phải tạo register constraints tương ứng.

---

# 577.81. Three-address legalization

Three-address IR có thể lower thành two-address machine constraints trước allocation.

---

# 577.82. Operand tying

Instruction operands có thể yêu cầu cùng physical register.

---

# 577.83. Early-clobber

Target instruction có early-clobber constraints phải được mô hình hóa.

---

# 577.84. Implicit operands

Instruction implicit đọc/ghi register phải được allocator biết.

---

# 577.85. Register mask correctness

Call/asm register masks là hard constraints.

---

# 577.86. Inline assembly

Inline asm phải khai báo:

```text
inputs
outputs
clobbers
fixed registers
memory effects
```

---

# 577.87. Unknown asm

Không được assume register/memory safety ngoài declared contract.

---

# 577.88. SIMD registers

SIMD register class được allocate độc lập nhưng phải xử lý alias/ABI chính xác.

---

# 577.89. Mask registers

ISA có mask register phải có register class riêng.

---

# 577.90. Vector register width

Allocator phải biết overlapping width khi ISA có subregister vector.

---

# 577.91. Register pressure across calls

Live SIMD/GPR values qua call phải account caller clobber.

---

# 577.92. Callee-saved cost

Allocator phải tính chi phí save/restore.

---

# 577.93. Shrink wrapping

Có thể save callee-saved registers chỉ trên paths cần chúng.

---

# 577.94. Shrink-wrap safety

Phải preserve all exits, panic paths và unwind semantics.

---

# 577.95. Prologue/epilogue integration

Register allocation output phải cung cấp:

```text
used_callee_saved
stack_slots
frame_size
alignment
```

---

# 577.96. Frame layout

Stack frame được finalize bởi backend frame-layout stage.

---

# 577.97. Dynamic stack

Dynamic allocations như `alloca` phải constrain frame/register decisions.

---

# 577.98. Stack pointer register

SP không được allocator sử dụng như general register nếu ABI không cho phép.

---

# 577.99. Frame pointer

Frame pointer có thể omit nếu target/ABI/debug policy cho phép.

---

# 577.100. Frame-pointer elimination

FPO không được phá unwind/debug requirements.

---

# 577.101. Stack alignment

Call-site alignment phải được preserve.

---

# 577.102. Red zone

Target có red-zone phải khai báo explicitly.

---

# 577.103. Interrupt context

Interrupt/special functions có register-preservation rules riêng.

---

# 577.104. Naked functions

Naked functions không sử dụng automatic prologue/epilogue assumptions.

---

# 577.105. Async

Async lowering có thể biến live values thành state-machine fields trước allocation.

---

# 577.106. Suspend boundary

Values sống qua await không được giữ trong ordinary caller-clobbered register.

---

# 577.107. Async frame

Allocator phải coi async frame fields là memory state.

---

# 577.108. Exception/panic edge

Unwind paths phải có valid register/stack locations.

---

# 577.109. Landing pads

Landing-pad live values phải được assign hợp lệ.

---

# 577.110. Debug locations

Allocator phải update variable-location metadata.

---

# 577.111. Location lists

Một source variable có thể chuyển:

```text
register → register
register → stack
stack → register
```

---

# 577.112. Debug optimization

Debug location correctness không được làm sai executable semantics.

---

# 577.113. Register allocation and GC

Axiom core không có mandatory GC nên allocator không phải hỗ trợ GC safepoint scanning.

---

# 577.114. Optional managed runtime

Nếu runtime tương lai yêu cầu safepoint, đó phải là explicit ABI contract.

---

# 577.115. Atomic operations

Atomic operands phải giữ register constraints và memory semantics.

---

# 577.116. Compare-exchange

CAS instructions thường có tied/fixed operands; allocator phải model chính xác.

---

# 577.117. Division instructions

ISA có fixed dividend/divisor registers phải encode constraints.

---

# 577.118. Multiplication

Implicit high/low result registers phải được model.

---

# 577.119. Shift instructions

ISA fixed shift-count register phải được model.

---

# 577.120. Vector reductions

Vector accumulator pressure phải được cost-model.

---

# 577.121. Register class fallback

Nếu preferred class thiếu register, allocator không tự chuyển class nếu ISA không cho phép.

---

# 577.122. Register class constraints

Instruction legality được target backend xác định.

---

# 577.123. Allocation failure

Nếu allocation không khả thi:

```text
split
spill
rematerialize
reallocate
```

theo thứ tự phù hợp.

---

# 577.124. Hard allocation failure

Compiler phải báo diagnostic nội bộ thay vì emit invalid machine code.

---

# 577.125. Spill insertion

Spill/reload instructions phải được đưa vào Machine IR và allocation lại nếu cần.

---

# 577.126. Spill iteration limit

Spill insertion có hard iteration budget.

---

# 577.127. Spill convergence

Allocator phải guarantee termination.

---

# 577.128. Reload coalescing

Reload có thể coalesce với uses khi profitable.

---

# 577.129. Store folding

Spill store có thể fold vào instruction nếu target cho phép.

---

# 577.130. Reload folding

Spill reload có thể fold vào consuming instruction.

---

# 577.131. Memory operand legality

Folded spill access phải satisfy addressing/alignment constraints.

---

# 577.132. Spill placement

Spill/reload được đặt càng gần cần thiết càng tốt.

---

# 577.133. Spill hoisting

Không hoist spill vào hot path nếu không có lợi.

---

# 577.134. Loop spill motion

Spill code có thể move ra loop nếu lifetime semantics cho phép.

---

# 577.135. Register splitting

Split tại:

```text
call
loop boundary
high pressure region
```

---

# 577.136. Split around call

Giảm spill qua caller-clobbered registers.

---

# 577.137. Local allocation

Một function nhỏ có thể dùng local/fast allocator.

---

# 577.138. Global allocation

Function lớn/hot sử dụng global live-range allocator.

---

# 577.139. Hotness

PGO hotness có thể ưu tiên register assignment.

---

# 577.140. Cold blocks

Cold values có thể ưu tiên spill để bảo vệ hot-path registers.

---

# 577.141. Register preference

Allocator có thể có preference:

```text
same-as-input
same-as-output
ABI-return
ABI-argument
```

---

# 577.142. Copy elimination

Register preference phải giảm move instructions.

---

# 577.143. Register reuse

Physical register có thể reuse khi live range kết thúc.

---

# 577.144. Lifetime holes

Allocator phải tận dụng holes.

---

# 577.145. Interval splitting

Splitting không được tạo quá nhiều fragment.

---

# 577.146. Fragment budget

Mỗi value có maximum fragments.

---

# 577.147. Compile-time budget

Allocator phải respect compiler resource budget từ `553`.

---

# 577.148. Memory budget

Graph/interference structures có thể chuyển sang sparse representation khi function lớn.

---

# 577.149. Large-function mode

Function cực lớn không được gây quadratic memory explosion.

---

# 577.150. Sparse interference

Chỉ materialize relevant interference edges.

---

# 577.151. Region-based allocation

Allocator có thể xử lý function theo regions để giảm memory.

---

# 577.152. Register allocation cache

Không cache physical register assignment độc lập với exact Machine IR/target/config.

---

# 577.153. Cache identity

Allocation artifact identity gồm:

```text
MachineIR
target
ABI
CPU features
optimization profile
allocator version
```

---

# 577.154. Reproducibility

Cùng input phải tạo cùng register assignment khi deterministic mode bật.

---

# 577.155. Fast-build nondeterminism

Ngay cả fast mode cũng không được thay đổi semantics; artifact determinism là default.

---

# 577.156. Machine verifier

Sau allocation phải kiểm tra:

```text
no virtual register
all constraints satisfied
no illegal register overlap
```

---

# 577.157. Liveness verifier

Physical register assignment phải không gây interference violation.

---

# 577.158. Spill verifier

Mọi spill/load phải có valid stack slot.

---

# 577.159. ABI verifier

Call/return register locations phải đúng ABI.

---

# 577.160. Call-clobber verifier

Không có live value bị call phá hỏng.

---

# 577.161. Stack verifier

Frame offsets phải hợp lệ.

---

# 577.162. Alignment verifier

Stack/object alignment phải đúng.

---

# 577.163. SSA destruction verifier

Không còn illegal phi/parallel-copy state sau lowering.

---

# 577.164. Debug verifier

Debug location không được tham chiếu physical location không tồn tại.

---

# 577.165. Unwind verifier

Callee-save và frame state phải khớp unwind metadata.

---

# 577.166. Register pressure feedback

Verifier/statistics cung cấp:

```text
peak_pressure
spill_count
reload_count
copy_count
callee_saved_count
```

---

# 577.167. Allocation quality metric

Compiler có thể tính:

```text
spill_cost
move_cost
register_utilization
```

---

# 577.168. No universal allocator winner

Axiom không giả định một allocator luôn tốt nhất.

---

# 577.169. Adaptive allocator

Compiler có thể chọn allocator dựa trên cheap pre-analysis.

---

# 577.170. Allocator fallback

Nếu aggressive allocator vượt budget:

```text
fallback → simpler allocator
```

nhưng phải preserve correctness.

---

# 577.171. Target specialization

Backend có thể cung cấp target-specific allocation heuristics.

---

# 577.172. Generic allocator core

Target-specific code không được duplicate toàn bộ allocator.

---

# 577.173. Target register description

Target backend cung cấp:

```text
registers
classes
aliases
units
costs
constraints
ABI masks
```

---

# 577.174. x86-64

Phải support GPR, XMM/YMM/ZMM, mask registers nếu target feature enabled.

---

# 577.175. AArch64

Phải support GPR, SIMD/FP registers và ABI constraints.

---

# 577.176. WASM

WASM backend không nhất thiết cần native physical-register allocation trước machine emission; target lowering có thể map stack-machine semantics trực tiếp.

---

# 577.177. Register allocator abstraction

```text id="9z1q5x"
RegisterFile
RegisterClass
RegisterUnit
RegisterConstraint
LiveRange
Allocation
SpillPlan
```

---

# 577.178. No ISA-specific assumptions in core

Core allocator chỉ sử dụng target description.

---

# 577.179. Machine instruction interface

Instruction phải expose:

```text
defs
uses
implicit_defs
implicit_uses
clobbers
constraints
```

---

# 577.180. Register allocation API

Conceptual:

```text
allocate(machine_function, target, policy)
    -> AllocationResult
```

---

# 577.181. AllocationResult

```text
AllocationResult {
    assignments
    spill_slots
    frame_requirements
    callee_saved
    statistics
    verifier_state
}
```

---

# 577.182. Policy

```text
Fast
Balanced
Aggressive
Size
Debug
```

---

# 577.183. Verification

`AllocationResult` phải được verify trước khi commit.

---

# 577.184. Transactionality

```text
MachineIR snapshot
      ↓
allocation candidate
      ↓
verify
      ↓
commit
```

---

# 577.185. Failed allocation

Candidate thất bại → rollback.

---

# 577.186. Differential testing

So sánh:

```text
unallocated/reference
vs
allocated
```

qua interpreter/emulator/test backend khi có thể.

---

# 577.187. Randomized allocator testing

Cùng Machine IR có thể chạy nhiều allocation policies để kiểm tra semantic equivalence.

---

# 577.188. Fuzz constraints

Random instruction constraints phải không tạo invalid assignment.

---

# 577.189. Regression corpus

Mọi allocator bug tạo reduced regression test.

---

# 577.190. Performance corpus

Benchmark phải bao gồm:

```text
scalar
SIMD
deep loops
large functions
many calls
high register pressure
async
panic/unwind
FFI
```

---

# 577.191. Compile-time target

Fast allocator phải giữ compiler latency thấp ở `O0/O1`.

---

# 577.192. Quality target

Aggressive allocator phải ưu tiên giảm spill và move trong hot code.

---

# 577.193. Code-size target

Size allocator phải ưu tiên giảm:

```text
spill instructions
move instructions
prologue/epilogue
```

---

# 577.194. No semantic dependence

Register assignment không được thay đổi language-level observable semantics.

---

# 577.195. Memory model

Spills là implementation detail; không được expose như ordinary program memory.

---

# 577.196. Volatile

Volatile operations không được tối ưu hóa thành register-only semantics.

---

# 577.197. MMIO

Memory-mapped IO phải giữ memory ordering/volatility contract.

---

# 577.198. Atomic ordering

Register allocation không được reorder atomic operations.

---

# 577.199. FINAL HARD INVARIANT

> **Sau BOOTSTRAP-577, mọi Machine IR function phải có một allocation hợp lệ hoặc compiler phải fail một cách xác định; không bao giờ được emit machine code với virtual register, register constraint chưa thỏa mãn, interference violation, sai caller/callee-save semantics, sai ABI location, sai stack alignment hoặc sai unwind/debug state. Register allocation được phép dùng nhiều chiến lược và heuristic khác nhau, nhưng cùng một Machine IR + target + ABI + semantic configuration phải luôn tạo ra machine code có observable behavior tương đương.**

# 577.200. LOCK

**BOOTSTRAP-577: LOCKED.**

---

# NEXT — BOOTSTRAP-578

## COMPILER INSTRUCTION SCHEDULING 3.0
### DEPENDENCY GRAPH, LATENCY/THROUGHPUT MODEL, LIST SCHEDULING, RESOURCE CONSTRAINTS, REGISTER-PRESSURE-AWARE SCHEDULING, TRACE SCHEDULING, LOAD/STORE SCHEDULING, CPU PIPELINE MODEL & TARGET-SPECIFIC MACHINE OPTIMIZATION

Pipeline tiếp theo:

```text id="u7c3m9"
Optimized Machine IR
        │
        ▼
Register Allocation 577
        │
        ▼
Dependency Graph
        │
        ├── Data Dependencies
        ├── Memory Dependencies
        ├── Register Dependencies
        ├── Control Dependencies
        └── Resource Dependencies
        │
        ▼
Instruction Scheduler
        │
        ├── Latency
        ├── Throughput
        ├── Port/Unit Pressure
        ├── Register Pressure
        ├── Code Size
        └── Branch/Cache Behavior
        │
        ▼
Scheduled Machine IR
        │
        ▼
578 Verification
        │
        ▼
Machine Encoder
```

`578` sẽ khóa cách Axiom tận dụng **đặc tính pipeline thực của CPU** thay vì chỉ chọn instruction đúng về mặt ISA.