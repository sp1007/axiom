# BOOTSTRAP-578 — COMPILER INSTRUCTION SCHEDULING 3.0
## DEPENDENCY GRAPH, LATENCY/THROUGHPUT MODEL, LIST SCHEDULING, RESOURCE CONSTRAINTS, REGISTER-PRESSURE-AWARE SCHEDULING, TRACE SCHEDULING, LOAD/STORE SCHEDULING, CPU PIPELINE MODEL & TARGET-SPECIFIC MACHINE OPTIMIZATION

**Trạng thái: COMPLETED / LOCKED**

`578` định nghĩa tầng scheduling cuối của backend Axiom. Mục tiêu không chỉ là tạo instruction hợp lệ mà còn sắp xếp chúng để tận dụng:

- instruction-level parallelism;
- CPU execution ports/units;
- latency và throughput;
- out-of-order execution;
- register pressure;
- load/store pipeline;
- branch prediction;
- instruction-cache;
- code size.

Scheduler **không được biến semantic correctness thành một heuristic**: mọi dependency và ordering cần thiết phải được bảo toàn.

---

# 578.1. Vị trí trong pipeline

```text
Optimized MIR
     ↓
Machine Lowering
     ↓
Register Allocation 577
     ↓
Machine IR
     ↓
Dependency Analysis
     ↓
Scheduling
     ↓
Machine Cleanup
     ↓
Prologue/Epilogue
     ↓
Machine Encoding
```

---

# 578.2. Scheduler input

Scheduler nhận Machine IR đã:

- legalize;
- register-allocated;
- spill-resolved;
- SSA-destroyed.

---

# 578.3. Scheduler output

Output là Machine IR có thứ tự instruction xác định.

---

# 578.4. Scheduling unit

Scheduling có thể thực hiện theo:

```text
basic block
extended block
trace
loop
region
function
```

---

# 578.5. Basic-block scheduling

Baseline scheduler phải hỗ trợ instruction scheduling trong basic block.

---

# 578.6. Instruction dependency graph

Mỗi scheduling region tạo DAG:

```text id="3v7r2m"
Instruction
    ↓
Dependency Graph
    ├── Data
    ├── Memory
    ├── Control
    ├── Register
    └── Resource
```

---

# 578.7. Data dependency

Nếu instruction B cần kết quả của A:

```text id="m2p8z5"
A → B
```

---

# 578.8. RAW

Read-after-write dependency phải được bảo toàn.

---

# 578.9. WAR

Write-after-read dependency được tạo khi physical register/resource semantics yêu cầu.

---

# 578.10. WAW

Write-after-write dependency phải được giữ khi cùng resource.

---

# 578.11. Register-unit dependency

Partial-register overlap phải tạo dependency chính xác.

---

# 578.12. Implicit register dependency

Implicit defs/uses của instruction phải nằm trong graph.

---

# 578.13. Memory dependency

Memory operations phải được schedule dựa trên Memory SSA và alias information.

---

# 578.14. Volatile memory

Volatile access tạo hard ordering constraints theo language/target semantics.

---

# 578.15. Atomic memory

Atomic operations phải giữ memory-order semantics.

---

# 578.16. Fence

Fence là scheduling barrier tương ứng với memory model.

---

# 578.17. Call dependency

Call được xem là resource/memory boundary theo effect + ABI contract.

---

# 578.18. Unknown call

Unknown external call phải được xử lý conservatively.

---

# 578.19. Pure call

Pure call có thể được schedule linh hoạt hơn nhưng vẫn phải respect dependencies.

---

# 578.20. Exception dependency

Instruction có thể panic/throw phải giữ ordering cần thiết với cleanup/unwind edges.

---

# 578.21. Control dependency

Branches và control-sensitive operations phải giữ semantic control dependencies.

---

# 578.22. Speculation

Một instruction chỉ được speculate nếu:

```text id="f4n7q0"
no observable side effect
+
safe under target semantics
+
575 proof
```

---

# 578.23. Load speculation

Load có thể được hoist nếu memory/exception semantics cho phép.

---

# 578.24. Faulting load

Nếu load có thể fault/panic và việc fault observable, không được tùy tiện speculate.

---

# 578.25. Non-faulting load

Target-specific non-faulting semantics có thể cho phép scheduling mạnh hơn.

---

# 578.26. Store motion

Store chỉ được reorder khi memory model chứng minh an toàn.

---

# 578.27. Dependency reduction

Scheduler có thể loại redundant dependency khi canonical analysis chứng minh independence.

---

# 578.28. Latency model

Mỗi target instruction có latency estimate.

---

# 578.29. Throughput model

Mỗi instruction có reciprocal throughput estimate.

---

# 578.30. Resource model

Target mô tả execution resources:

```text id="n7p3d1"
ALU
AGU
LOAD
STORE
FP
SIMD
BRANCH
SPECIAL
```

---

# 578.31. Resource occupancy

Instruction có thể consume một hoặc nhiều execution resources.

---

# 578.32. Port model

ISA target có thể khai báo execution-port candidates.

---

# 578.33. Resource conflicts

Scheduler không tạo schedule vượt resource capacity trong model.

---

# 578.34. Unknown resource model

Nếu target resource information không đầy đủ, scheduler dùng conservative generic model.

---

# 578.35. CPU model

Target CPU description:

```text id="j0q9s5"
ISA
features
latency
throughput
resources
cache hints
branch hints
```

---

# 578.36. Generic CPU

Compiler phải có generic baseline CPU model.

---

# 578.37. CPU-specific model

User có thể chọn CPU microarchitecture profile.

---

# 578.38. CPU model mismatch

CPU-specific scheduling không được dùng nếu binary có thể chạy trên CPU không hỗ trợ assumptions tương ứng.

---

# 578.39. Target feature identity

CPU model phải trở thành một phần của artifact/build identity.

---

# 578.40. Scheduler objective

Cost function:

```text id="2c8v6x"
latency
+
throughput
+
resource pressure
+
register pressure
+
code size
+
branch behavior
```

---

# 578.41. Critical path

Scheduler xác định critical-path length.

---

# 578.42. Critical-path priority

Instructions trên critical path được ưu tiên khi latency dominant.

---

# 578.43. Ready list

Scheduler duy trì ready instructions không còn unsatisfied dependencies.

---

# 578.44. List scheduling

Baseline scheduling algorithm là list scheduling.

---

# 578.45. Priority function

Priority có thể kết hợp:

```text id="7f3n0w"
criticality
slack
resource pressure
register pressure
latency
hotness
```

---

# 578.46. Deterministic priority

Tie-break sử dụng stable instruction ID.

---

# 578.47. Forward scheduling

Có thể schedule từ đầu region.

---

# 578.48. Backward scheduling

Có thể schedule từ cuối region khi giảm register pressure hoặc latency.

---

# 578.49. Bidirectional scheduling

Advanced scheduler có thể chọn hướng dựa trên region characteristics.

---

# 578.50. Register-pressure awareness

Scheduler phải account live-register pressure.

---

# 578.51. Pressure increase

Không ưu tiên instruction chỉ vì latency nếu nó gây spill nguy hiểm.

---

# 578.52. Pressure decrease

Instruction kết thúc lifetime của value có thể được ưu tiên.

---

# 578.53. Spill-aware scheduling

Nếu scheduling tạo thêm spill do lifetime kéo dài, scheduler phải cân nhắc chi phí.

---

# 578.54. Post-allocation scheduling

Vì `577` đã assign physical registers, scheduler phải tôn trọng physical register dependencies.

---

# 578.55. Pre-allocation scheduling

Axiom có thể schedule một số machine patterns trước allocation nếu cần.

---

# 578.56. Pre/post scheduling distinction

Pre-allocation scheduling không được giả định physical-register identity chưa tồn tại.

---

# 578.57. Two-address constraints

Scheduler phải respect tied operands.

---

# 578.58. Fixed-register constraints

Fixed-register instruction dependencies phải được model.

---

# 578.59. Register pressure across calls

Scheduler phải account values sống qua calls.

---

# 578.60. Callee-saved registers

Scheduler không được phá save/restore semantics.

---

# 578.61. Prologue scheduling

Một số prologue instructions có thể được schedule khi target/ABI cho phép.

---

# 578.62. Epilogue scheduling

Epilogue instructions phải respect all exits/unwind paths.

---

# 578.63. Stack operations

Stack loads/stores phải được đưa vào memory/resource graph.

---

# 578.64. Spill operations

Spill/reload được schedule như ordinary memory instructions nhưng có priority phù hợp.

---

# 578.65. Load/store queues

Target model có thể mô tả load/store resource pressure.

---

# 578.66. Load-use latency

Scheduler phải biết latency từ load đến dependent use.

---

# 578.67. Load clustering

Independent loads có thể được nhóm khi target hưởng lợi.

---

# 578.68. Store clustering

Stores có thể được nhóm khi không phá dependency.

---

# 578.69. Memory-level parallelism

Scheduler có thể ưu tiên independent loads để tăng MLP.

---

# 578.70. Cache-aware scheduling

Chỉ sử dụng cache information nếu target model đáng tin cậy.

---

# 578.71. Prefetch

Compiler-generated prefetch chỉ được thêm bởi optimization pass và phải có profitability contract.

---

# 578.72. Prefetch scheduling

Prefetch không được tạo dependency giả không cần thiết.

---

# 578.73. Branch scheduling

Branch latency và predictor behavior có thể influence ordering.

---

# 578.74. Fall-through preference

Hot fall-through path được ưu tiên.

---

# 578.75. Branch inversion

Branch inversion chỉ được thực hiện khi CFG/semantics verifier cho phép.

---

# 578.76. Trace scheduling

Hot traces có thể được schedule across basic-block boundaries.

---

# 578.77. Trace safety

Trace scheduling phải preserve compensation/control paths.

---

# 578.78. Compensation code

Nếu instruction được hoist qua branch, cần compensation code nếu required.

---

# 578.79. Code-size limit

Trace scheduling bị giới hạn bởi code-size budget.

---

# 578.80. Hyperblock

Predication/select-based regions có thể được scheduler xử lý như một region.

---

# 578.81. Predication

Chỉ dùng target predication khi semantic equivalence được đảm bảo.

---

# 578.82. Speculative execution

Speculative scheduling phải phân biệt:

```text id="q7v4s2"
safe speculation
unsafe speculation
```

---

# 578.83. Safe speculation

Pure arithmetic thường có thể speculate nếu overflow/FP semantics không thay đổi.

---

# 578.84. Unsafe arithmetic speculation

Checked overflow/panic-producing operations phải giữ behavior.

---

# 578.85. FP scheduling

Floating-point instructions phải respect FP environment semantics.

---

# 578.86. NaN

Scheduler không được giả định NaN impossible.

---

# 578.87. Signed zero

FP transformation phải preserve signed-zero behavior nếu strict FP mode.

---

# 578.88. Fast FP

Relaxed FP policy có thể cho scheduler thêm freedom.

---

# 578.89. SIMD scheduling

SIMD resources được target model mô tả.

---

# 578.90. FMA

Fused operations chỉ được tạo bởi optimization/target legalization khi semantics cho phép.

---

# 578.91. Instruction fusion

Scheduler có thể favor producer-consumer patterns được CPU fuse.

---

# 578.92. Macro-fusion

Target model có thể khai báo branch/compare fusion opportunities.

---

# 578.93. Micro-op model

Scheduler có thể dùng approximate µop/resource model.

---

# 578.94. Model accuracy

Microarchitecture model là profitability information, không phải semantic authority.

---

# 578.95. In-order targets

Scheduler phải support CPU không có out-of-order execution.

---

# 578.96. Out-of-order targets

Scheduler vẫn hữu ích cho code layout, resource pressure và latency chains.

---

# 578.97. Very wide OoO CPU

Scheduler có thể ưu tiên throughput/resource balancing.

---

# 578.98. Small CPU

Scheduler có thể ưu tiên code size và register pressure.

---

# 578.99. Embedded target

Scheduling profile phải có low-memory/low-power options.

---

# 578.100. Code-size-aware scheduling

Instruction ordering không được làm binary phình lên nếu equivalent compact ordering tồn tại và profile ưu tiên size.

---

# 578.101. Alignment interaction

Scheduling phải account possible alignment changes do later layout.

---

# 578.102. NOP insertion

Alignment NOPs chỉ được thêm bởi layout/encoder stages khi cần.

---

# 578.103. Instruction bundling

Nếu target yêu cầu bundles, scheduler phải tạo bundle-aware schedule.

---

# 578.104. Bundle legality

Không tạo bundle illegal.

---

# 578.105. VLIW

Axiom target abstraction phải cho phép explicit VLIW scheduling.

---

# 578.106. Packet scheduling

Instructions trong cùng packet phải satisfy resource constraints.

---

# 578.107. Dependency graph validation

Scheduler phải verify schedule không violate graph.

---

# 578.108. Cycle detection

Dependency graph cycle phải được phân loại:

```text id="c0z8p3"
legitimate serialization
or
compiler bug
```

---

# 578.109. Memory dependency conservatism

Unknown alias → conservative ordering.

---

# 578.110. Alias relaxation

Known NoAlias có thể remove unnecessary memory edges.

---

# 578.111. Effect integration

`573` effect summary được sử dụng để xác định scheduling freedom.

---

# 578.112. Pure operation

Pure operation có thể reorder theo data dependencies.

---

# 578.113. IO

IO operation có ordering semantics.

---

# 578.114. Allocation

Observable allocation effects phải preserve order.

---

# 578.115. Resource destruction

Drop/release operations phải respect lifetime order.

---

# 578.116. Lock operations

Lock acquire/release là synchronization boundaries.

---

# 578.117. Atomic ordering

Acquire/release/seq-cst semantics constrain scheduler.

---

# 578.118. Thread-local operations

TLS operations phải respect runtime semantics.

---

# 578.119. Async suspension

No ordinary instruction may move across await/suspend boundary without explicit async lowering contract.

---

# 578.120. Async resume

Resume/suspend state transitions are control barriers.

---

# 578.121. Panic

Potential panic operation may constrain following observable operations.

---

# 578.122. Unwind

Instructions contributing to unwind state must preserve required ordering.

---

# 578.123. Debug stepping

Debug mode may use restricted scheduler policy.

---

# 578.124. Debug locations

Instruction motion phải update source-location metadata.

---

# 578.125. Debug policy

`-O0` scheduler prioritizes source-level predictability.

---

# 578.126. Optimization policy

`-O2/-O3` prioritize execution performance.

---

# 578.127. Size policy

`-Os/-Oz` prioritize compactness.

---

# 578.128. Power policy

Optional target profile can penalize high-power instruction sequences.

---

# 578.129. Thermal policy

Compiler may support energy-aware cost model without changing semantics.

---

# 578.130. Profile-guided scheduling

PGO hotness may influence scheduling.

---

# 578.131. Profile uncertainty

Stale profile data must not become semantic assumptions.

---

# 578.132. Missing profile

Use static heuristics.

---

# 578.133. Branch probability

Branch probabilities can affect trace scheduling.

---

# 578.134. Loop frequency

Loop depth/frequency influences latency priorities.

---

# 578.135. Critical-path calculation

Scheduler computes weighted critical paths using target latency model.

---

# 578.136. Resource pressure

Scheduler estimates execution-unit pressure.

---

# 578.137. Pressure balancing

When two ready instructions have similar priority, resource-balancing can select between them.

---

# 578.138. Slack

Instructions with high slack can be delayed.

---

# 578.139. Latency hiding

Independent operations can fill dependency latency slots.

---

# 578.140. Long-latency operation

Loads/divisions/special operations receive appropriate priority.

---

# 578.141. Division scheduling

Independent instructions may be scheduled during long division latency.

---

# 578.142. Dependency chain breaking

Optimizer `576` may transform expressions to shorten dependency chains before scheduling.

---

# 578.143. Scheduler does not invent algebra

Scheduler itself should not perform semantic algebraic transformations.

---

# 578.144. Machine combine

Small target-specific combines may be delegated to machine optimization stage.

---

# 578.145. Post-schedule cleanup

Cleanup may remove redundant moves or NOPs introduced during scheduling.

---

# 578.146. Cleanup verification

Cleanup transformations remain subject to `575`.

---

# 578.147. Scheduling transaction

```text id="1g9m0b"
MachineIR
   ↓
Schedule candidate
   ↓
Dependency verification
   ↓
Target legality verification
   ↓
Commit
```

---

# 578.148. Failed schedule

Invalid candidate phải rollback.

---

# 578.149. Deterministic schedule

Stable IDs + deterministic priority ensure reproducibility.

---

# 578.150. Parallel scheduling

Independent scheduling regions có thể schedule song song.

---

# 578.151. Parallel determinism

Parallel scheduler không được thay đổi canonical artifact.

---

# 578.152. Scheduling cache

Schedule cache identity phải bao gồm:

```text id="6z4y9a"
MachineIR
target
CPU model
ABI
scheduler version
optimization profile
PGO profile
```

---

# 578.153. Cache safety

Stale CPU model không được reuse.

---

# 578.154. Target-independent scheduler core

Core scheduler không hard-code x86/AArch64 behavior.

---

# 578.155. Target model API

```text id="4u7k3s"
latency(inst)
throughput(inst)
resources(inst)
constraints(inst)
fusion(instA, instB)
```

---

# 578.156. Resource reservation

Scheduler dùng reservation model để dự đoán resource occupancy.

---

# 578.157. Resource model fallback

Nếu target không cung cấp detailed reservation, dùng coarse class-based model.

---

# 578.158. Instruction itinerary

Target có thể cung cấp itinerary cho instruction classes.

---

# 578.159. Machine-readable target data

Target scheduling model phải có thể serialize trong backend target description.

---

# 578.160. Backend extensibility

Thêm CPU model mới không cần sửa scheduler core.

---

# 578.161. x86-64 scheduling

Phải hỗ trợ:

- GPR;
- SIMD;
- load/store;
- branch;
- execution-port model;
- fusion hints.

---

# 578.162. AArch64 scheduling

Phải hỗ trợ:

- integer;
- FP/SIMD;
- load/store;
- branch;
- CPU-specific resource models.

---

# 578.163. WASM scheduling

WASM không có native CPU register scheduler ở cùng tầng; target backend được phép bỏ qua hoặc thực hiện stack-machine canonicalization.

---

# 578.164. Cross-target correctness

Một scheduler không được tạo target-specific semantic assumption.

---

# 578.165. ISA legality

Scheduler không chịu trách nhiệm sửa instruction illegal; legality phải được target legalization đảm bảo.

---

# 578.166. Register allocation interaction

Scheduler sau allocation phải không tạo register interference mới.

---

# 578.167. Stack-frame interaction

Scheduler không được phá frame offsets.

---

# 578.168. Call frame

Stack adjustments liên quan call phải preserve ABI.

---

# 578.169. Tail calls

Tail-call sequence phải được xem là scheduling barrier/structured region khi ABI yêu cầu.

---

# 578.170. Return

Return instruction ordering phải preserve epilogue semantics.

---

# 578.171. Barrier instruction

Target barrier có thể cấm scheduling xuyên qua nó.

---

# 578.172. Serialization instruction

CPU serialization semantics phải được model.

---

# 578.173. Privileged instructions

Privileged/special instructions có hard scheduling constraints.

---

# 578.174. Inline asm barrier

Asm có `memory`/register clobber phải constrain scheduler theo declaration.

---

# 578.175. Unknown intrinsic

Unknown intrinsic được xem conservative.

---

# 578.176. Runtime calls

Runtime helper calls lấy effect/ABI metadata từ runtime contract.

---

# 578.177. Instruction count

Scheduler statistics ghi nhận instruction count trước/sau.

---

# 578.178. Critical path statistics

Compiler có thể xuất:

```text id="v8r3q0"
critical_path
resource_pressure
dependency_depth
```

---

# 578.179. Performance diagnostics

Optimization report có thể giải thích:

> instruction X bị trì hoãn vì dependency Y.

---

# 578.180. AI diagnostics

AI tooling có thể query scheduler facts nhưng không được override correctness.

---

# 578.181. Benchmarking

Scheduler benchmark phải đo:

```text id="p5z8h1"
runtime
code size
compile time
```

---

# 578.182. Microbenchmark suite

Phải cover:

```text id="f2x6n9"
integer chains
FP chains
SIMD
loads
stores
branches
calls
atomics
```

---

# 578.183. Stress tests

Large basic blocks không được gây quadratic/unbounded scheduler memory.

---

# 578.184. Scheduling budget

Scheduler có hard time/memory budget.

---

# 578.185. Fallback scheduler

Nếu advanced scheduler vượt budget:

```text id="j6q0x5"
→ fast list scheduler
```

---

# 578.186. Compile-time guarantee

Scheduler luôn terminate.

---

# 578.187. Semantic equivalence

Scheduled Machine IR phải observable-equivalent với input Machine IR.

---

# 578.188. Verification

Sau scheduling phải chạy:

```text id="2c9w7m"
dependency verifier
machine verifier
ABI verifier
memory-order verifier
unwind verifier
```

khi applicable.

---

# 578.189. Reference execution

Critical scheduler transformations có thể được kiểm tra bằng differential execution.

---

# 578.190. Fuzzing

Random legal Machine IR + scheduling phải không tạo invalid machine code.

---

# 578.191. Miscompile corpus

Mọi scheduling bug phải được giảm về regression test.

---

# 578.192. Deterministic artifact

Scheduler output là deterministic với cùng:

```text id="0m8p3x"
source snapshot
compiler
target
CPU model
ABI
optimization profile
PGO
```

---

# 578.193. No runtime scheduler dependency

Scheduling là compile-time; binary không cần runtime scheduler metadata.

---

# 578.194. Zero semantic runtime overhead

Machine code không phải trả thêm cost chỉ vì compiler đã dùng scheduling analysis.

---

# 578.195. Hardware evolution

CPU model có thể được thêm mà không thay đổi language semantics.

---

# 578.196. Scheduler quality

Scheduler được phép bỏ qua optimization nếu model không đủ confidence.

---

# 578.197. Conservative fallback

Unknown hardware behavior → conservative schedule.

---

# 578.198. Global invariant

Mọi scheduler policy:

```text id="c4h9w2"
Fast
Balanced
Aggressive
Size
Debug
```

phải tạo machine code hợp lệ và semantic-equivalent.

---

# 578.199. FINAL HARD INVARIANT

> **Instruction Scheduler của Axiom chỉ được thay đổi thứ tự thực thi ở mức machine khi dependency, memory model, ABI, register constraints, exception/unwind semantics và target legality vẫn được bảo toàn. Latency, throughput, execution resources, register pressure, cache/branch behavior và PGO chỉ là cơ sở profitability; chúng không bao giờ trở thành semantic authority. Scheduler có thể sử dụng nhiều chiến lược và target-specific models nhưng phải deterministic, bounded, rollbackable và verifiable.**

# 578.200. LOCK

**BOOTSTRAP-578: LOCKED.**

---

# NEXT — BOOTSTRAP-579

## COMPILER MACHINE CODE FINALIZATION 3.0
### PROLOGUE/EPILOGUE, STACK FRAME FINALIZATION, FRAME POINTER ELIMINATION, STACK PROBING, STACK CLASH PROTECTION, TAIL CALLS, UNWIND CFI, TLS, SECURITY INSTRUMENTATION & FINAL MACHINE IR VERIFICATION

Pipeline tiếp theo:

```text
Optimized Machine IR
        │
        ▼
Register Allocation 577
        │
        ▼
Instruction Scheduling 578
        │
        ▼
Stack Frame Finalization
        │
        ├── Frame Size
        ├── Alignment
        ├── Spill Slots
        ├── Callee Saves
        ├── Local Stack
        └── Dynamic Stack
        │
        ▼
Prologue / Epilogue
        │
        ▼
CFI / Unwind
        │
        ▼
Security Instrumentation
        │
        ▼
Final Machine IR
        │
        ▼
Machine Verification
        │
        ▼
Machine Encoder
```

`579` sẽ là lớp **chốt Machine IR trước khi encoder biến nó thành bytes**; đặc biệt phải giải quyết chính xác stack frame, unwind, stack protection và mối quan hệ giữa ABI `421`, memory model `423`, debug/unwind `440`, security `445/490` và machine backend.