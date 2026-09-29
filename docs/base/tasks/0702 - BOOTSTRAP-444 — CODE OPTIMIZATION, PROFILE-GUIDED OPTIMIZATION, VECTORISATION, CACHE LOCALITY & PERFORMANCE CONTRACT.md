# BOOTSTRAP-444 — CODE OPTIMIZATION, PROFILE-GUIDED OPTIMIZATION, VECTORISATION, CACHE LOCALITY & PERFORMANCE CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Sau 443, Axiom đã có đường đi hoàn chỉnh:

```text
Source
  ↓
Semantic IR
  ↓
MIR
  ↓
LIR
  ↓
Machine IR
  ↓
Object
  ↓
Axiom Linker
  ↓
Native Artifact
```

444 khóa phần quyết định **chất lượng mã máy**.

Mục tiêu không phải tạo một optimizer khổng lồ ngay từ đầu, mà xây một pipeline có thể tiến hóa:

```text
correctness first
    ↓
canonicalization
    ↓
local optimization
    ↓
CFG optimization
    ↓
memory optimization
    ↓
scalar optimization
    ↓
loop optimization
    ↓
vectorization
    ↓
target optimization
    ↓
LTO
    ↓
machine optimization
```

Nguyên tắc quan trọng:

> **Mọi optimization đều là phép biến đổi semantics-preserving, trừ khi người dùng explicit cho phép relaxed semantics.**

---

# 444.1 — Optimization pipeline

Compiler:

```text
HIR
 ↓
MIR
 ↓
MIR canonicalization
 ↓
MIR optimization
 ↓
LIR lowering
 ↓
LIR optimization
 ↓
Machine IR
 ↓
Machine optimization
```

---

# 444.2 — Optimization levels

Axiom chuẩn hóa:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
```

Ý nghĩa:

| Mode | Mục tiêu |
|---|---|
| `-O0` | compile nhanh, debug |
| `-O1` | optimization nhẹ |
| `-O2` | optimization production mặc định |
| `-O3` | aggressive performance |
| `-Os` | giảm kích thước |
| `-Oz` | tối thiểu kích thước |

---

# 444.3 — Không gắn optimization với semantics

`-O3` không được thay đổi semantics hợp lệ của chương trình.

---

# 444.4 — Fast math

Floating-point optimization mạnh hơn chỉ được bật bằng explicit mode/attribute.

Ví dụ conceptual:

```text
@fast_math
fn calculate(...)
```

---

# 444.5 — Floating-point contract

Mặc định:

```text
IEEE-compatible semantics
```

trong giới hạn target ABI.

---

# 444.6 — Fast-math permissions

Có thể cho phép:

```text
reassociation
approximate reciprocal
flush-to-zero
ignore signed zero
ignore NaN distinctions
```

nhưng phải là explicit compilation contract.

---

# 444.7 — Integer semantics

Optimizer phải biết operation là:

```text
checked
wrapping
saturating
```

Không được tự ý biến đổi giữa ba loại.

---

# 444.8 — Undefined behavior boundary

Unsafe UB có thể cho optimizer các giả định mạnh hơn.

Safe Axiom code không được dựa vào UB để tối ưu.

---

# 444.9 — Canonicalization

Pass đầu tiên chuẩn hóa:

```text
constant forms
casts
branches
arithmetic
aggregate operations
```

---

# 444.10 — Constant folding

```text
2 + 3
```

→

```text
5
```

---

# 444.11 — Constant propagation

Nếu:

```text
x := 10
y := x + 5
```

có thể trở thành:

```text
y := 15
```

---

# 444.12 — Comptime boundary

Những gì `comptime` đã tính được không được tính lại runtime.

---

# 444.13 — Dead code elimination

Code không thể reachable được loại bỏ.

---

# 444.14 — Dead store elimination

Store không bao giờ được đọc có thể loại bỏ nếu không có observable side effect.

---

# 444.15 — Dead allocation elimination

Allocation có thể loại bỏ nếu:

```text
allocation
→ no observable use
```

---

# 444.16 — Pure function elimination

Function được đánh dấu/p chứng minh pure có thể bị loại nếu result không dùng.

---

# 444.17 — Side-effect model

IR phải phân biệt:

```text
Pure
ReadMemory
WriteMemory
Atomic
Volatile
IO
Panic
Unknown
```

---

# 444.18 — Volatile barrier

Volatile operation không được dead-code eliminate.

---

# 444.19 — Atomic barrier

Atomic semantics không được biến thành ordinary load/store.

---

# 444.20 — IO barrier

IO calls được coi là observable side effects.

---

# 444.21 — Common subexpression elimination

Ví dụ:

```text
a = x * y
b = x * y
```

có thể reuse kết quả nếu memory/effects không thay đổi.

---

# 444.22 — Global value numbering

MIR hỗ trợ nhận diện expressions tương đương vượt basic block.

---

# 444.23 — Algebraic simplification

Ví dụ:

```text
x + 0 → x
x * 1 → x
x & 0 → 0
```

chỉ khi semantics cho phép.

---

# 444.24 — Overflow-aware optimization

Ví dụ:

```text
checked_add
```

không được biến thành wrapping add.

---

# 444.25 — Strength reduction

Ví dụ:

```text
x * 8
```

→ shift khi target semantics và cost model cho phép.

---

# 444.26 — Division optimization

Constant division có thể lower thành:

```text
multiply
shift
correction
```

nếu chính xác.

---

# 444.27 — Branch simplification

```text
if true { A } else { B }
```

→

```text
A
```

---

# 444.28 — Branch folding

Các CFG edges không cần thiết được loại bỏ.

---

# 444.29 — Jump threading

Compiler có thể bypass intermediate branches.

---

# 444.30 — Tail duplication

Small blocks có thể được duplicate để loại branch.

---

# 444.31 — If conversion

Conditional branches có thể chuyển thành:

```text
select
conditional move
```

nếu target cost model có lợi.

---

# 444.32 — Branch prediction metadata

IR có thể chứa:

```text
likely
unlikely
profile_probability
```

nhưng đây là optimization hint, không phải semantic guarantee.

---

# 444.33 — Function inlining

Inlining là optimization quan trọng nhất cho Axiom zero-cost abstractions.

---

# 444.34 — Inline policy

Compiler xem xét:

```text
function size
call frequency
hotness
recursion
code size
target
```

---

# 444.35 — `@inline`

User có thể yêu cầu:

```text
@inline
```

nhưng không được hiểu là absolute machine-code guarantee.

---

# 444.36 — `@noinline`

Ngăn inlining:

```text
@noinline
```

---

# 444.37 — Always-inline

Nếu cần hard requirement:

```text
@always_inline
```

Compiler phải diagnostic nếu không thể thỏa mãn.

---

# 444.38 — Recursive inline

Compiler đặt giới hạn để tránh code explosion.

---

# 444.39 — Generic inline

Monomorphized generics có thể inline như ordinary functions.

---

# 444.40 — Trait dispatch optimization

Static trait calls có thể inline hoàn toàn.

---

# 444.41 — Dynamic dispatch devirtualization

Nếu compiler chứng minh receiver chỉ có một implementation:

```text
dyn Trait
```

có thể được devirtualize.

---

# 444.42 — Speculative devirtualization

Có thể dùng guarded specialization nếu runtime check rẻ và explicit optimization profile cho phép.

---

# 444.43 — Closure optimization

Closure:

```text
code pointer + environment
```

có thể được:

```text
inline
specialize
environment scalar-replace
```

---

# 444.44 — Closure allocation elimination

Nếu closure không escape:

```text
heap closure
```

có thể trở thành stack/register representation hoặc bị loại hoàn toàn.

---

# 444.45 — Escape analysis

Compiler phân loại:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

---

# 444.46 — Stack promotion

Heap object không escape có thể chuyển thành stack allocation.

---

# 444.47 — Scalar replacement

```text
struct Point { x, y }
```

có thể biến thành:

```text
x register
y register
```

nếu address không observable.

---

# 444.48 — Aggregate elimination

Temporary structs có thể không bao giờ tồn tại trong memory.

---

# 444.49 — Copy elimination

Compiler loại các copy không cần thiết.

---

# 444.50 — Move elimination

Move giữa temporary values có thể biến mất ở MIR/LIR.

---

# 444.51 — Ownership information

Ownership analysis từ 423 cung cấp optimization facts nhưng không được thay đổi semantics.

---

# 444.52 — Noalias information

Compiler chỉ sử dụng `noalias` khi contract/proof hợp lệ.

Không suy đoán tùy tiện.

---

# 444.53 — Alias analysis

Các mức:

```text
NoAlias
MustAlias
MayAlias
Unknown
```

---

# 444.54 — Memory SSA

Memory operations được biểu diễn bằng memory-def/use chains.

---

# 444.55 — Load forwarding

Store rồi load cùng location có thể forward value nếu alias analysis chứng minh an toàn.

---

# 444.56 — Store forwarding

```text
*p = x
y = *p
```

→

```text
y = x
```

nếu không có intervening modification.

---

# 444.57 — Load elimination

Repeated load có thể reuse nếu memory state không thay đổi.

---

# 444.58 — Store merging

Adjacent compatible stores có thể merge.

---

# 444.59 — Store sinking

Store có thể chuyển gần hơn tới điểm thực sự cần nếu side effects vẫn đúng.

---

# 444.60 — Store hoisting

Store có thể move khỏi loop nếu semantics cho phép.

---

# 444.61 — Loop invariant code motion

Expression không thay đổi trong loop có thể đưa ra ngoài.

---

# 444.62 — Loop canonicalization

Loop được normalize thành dạng:

```text
preheader
header
body
latch
exit
```

---

# 444.63 — Loop induction variables

Compiler nhận diện:

```text
i += constant
```

và các induction variable tương đương.

---

# 444.64 — Induction simplification

Có thể thay multiply/add sequence bằng induction variable.

---

# 444.65 — Loop unrolling

Hot/small loops có thể unroll.

---

# 444.66 — Partial unrolling

Không nhất thiết unroll toàn bộ.

---

# 444.67 — Loop peeling

Một số iterations đầu có thể tách ra để simplify main loop.

---

# 444.68 — Loop unswitching

Invariant condition có thể được đưa ra ngoài loop.

---

# 444.69 — Loop fusion

Hai loops tương thích có thể merge.

---

# 444.70 — Loop fission

Loop có thể tách để cải thiện locality/vectorization.

---

# 444.71 — Loop interchange

Nested loops có thể đổi thứ tự khi dependencies cho phép.

---

# 444.72 — Dependence analysis

Compiler phải kiểm tra memory dependencies trước loop transformations.

---

# 444.73 — Bounds-check elimination

Array access:

```text
a[i]
```

có thể bỏ bounds check nếu compiler chứng minh:

```text
0 <= i < length(a)
```

---

# 444.74 — Range analysis

Compiler duy trì:

```text
lower_bound
upper_bound
```

cho values.

---

# 444.75 — Loop bounds proof

Ví dụ:

```text
for i in 0..n {
    a[i]
}
```

có thể có zero bounds checks nếu:

```text
n <= a.length
```

đã được chứng minh.

---

# 444.76 — Check hoisting

Một bounds check invariant có thể đưa ra ngoài loop.

---

# 444.77 — Check elimination không cần unsafe

Safe code vẫn đạt zero-cost access khi compiler chứng minh được safety.

---

# 444.78 — Explicit unchecked access

Unsafe API vẫn có thể cung cấp unchecked load/store.

---

# 444.79 — Vectorization

Compiler có vectorizer target-independent trước:

```text
vector operations
```

sau đó target lowering.

---

# 444.80 — SIMD abstraction

Portable vector:

```text
Vec<T, N>
```

có thể lower thành:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

---

# 444.81 — Vector legality

Vectorizer kiểm tra:

```text
dependencies
alignment
aliasing
exceptions/panic
overflow
```

---

# 444.82 — Vector cost model

Không vectorize chỉ vì có thể.

Compiler so sánh:

```text
scalar cost
vector cost
setup cost
cleanup cost
```

---

# 444.83 — Scalar remainder

Loop vectorized có thể có:

```text
vector loop
+
scalar remainder
```

---

# 444.84 — Masked vectorization

Target hỗ trợ masked instructions có thể xử lý remainder/bounds hiệu quả.

---

# 444.85 — Alignment

Compiler phân biệt:

```text
known aligned
possibly aligned
unaligned
```

---

# 444.86 — Unaligned access

Không được giả định mọi architecture có cùng cost/semantics.

---

# 444.87 — Prefetch

Compiler có thể thêm prefetch khi cost model/profile cho thấy lợi ích.

---

# 444.88 — Software prefetch

Là optimization hint, không semantic guarantee.

---

# 444.89 — Cache locality

Optimizer có thể tối ưu:

```text
data layout
loop order
blocking
tiling
```

---

# 444.90 — Struct layout optimization

Mặc định layout ổn định.

Compiler **không được tự ý reorder public/ABI-visible fields**.

---

# 444.91 — Private struct layout

Private/non-ABI-visible types có thể được tối ưu representation nếu address/layout không observable.

---

# 444.92 — Field packing

Internal representation có thể optimize padding khi semantics cho phép.

---

# 444.93 — AoS / SoA

High-performance library có thể cung cấp:

```text
ArrayOfStructs
StructOfArrays
```

Không tự động đổi public data layout nếu có observable layout.

---

# 444.94 — PGO

Profile-guided optimization là optional.

Pipeline:

```text
instrument
→ run
→ collect profile
→ merge profile
→ optimize
```

---

# 444.95 — Profile format

Profile phải chứa:

```text
function identity
call edges
branch frequencies
loop frequencies
target
compiler/profile version
```

---

# 444.96 — Profile identity

Function identity phải dùng stable semantic identity thay vì source line đơn thuần.

---

# 444.97 — PGO invalidation

Thay đổi function semantics có thể invalidate profile.

---

# 444.98 — Sample PGO

Axiom có thể hỗ trợ sample-based profiles sau.

---

# 444.99 — Instrumentation PGO

Bootstrap implementation ưu tiên instrumentation PGO vì dễ kiểm soát.

---

# 444.100 — Hot/cold splitting

Functions/blocks có thể được phân thành:

```text
hot
cold
```

---

# 444.101 — Cold code

Error/panic paths có thể đưa khỏi hot path.

---

# 444.102 — Panic path optimization

Code:

```text
if invalid {
    panic(...)
}
```

có thể giữ hot path sạch.

---

# 444.103 — Result optimization

`Result<T,E>` success path không được yêu cầu allocation.

---

# 444.104 — Option optimization

Nullable/niche representation có thể làm:

```text
Option<&T>
```

có cùng size với pointer.

---

# 444.105 — Iterator optimization

Iterator abstractions phải có khả năng:

```text
inline
fuse
remove temporary
vectorize
```

---

# 444.106 — Zero-cost abstraction contract

Một abstraction không được tạo runtime overhead **chỉ vì abstraction đó tồn tại**, nếu compiler có đủ information để eliminate nó.

---

# 444.107 — Dynamic abstraction boundary

`dyn Trait` có runtime cost:

```text
data pointer
vtable lookup
indirect call
```

và đây là cost có chủ đích.

---

# 444.108 — Static vs dynamic

Compiler không tự biến static dispatch thành dynamic dispatch chỉ để giảm compile time nếu làm thay đổi performance contract.

---

# 444.109 — Code-size tradeoff

Inlining/vectorization có thể làm binary lớn hơn.

Cost model phải cân bằng:

```text
speed
size
compile_time
```

---

# 444.110 — Instruction combining

Machine-independent IR có canonical operations:

```text
add
mul
shift
compare
select
load
store
```

Machine backend combine thành target instructions.

---

# 444.111 — Target-specific combines

Ví dụ conceptual:

```text
multiply + add
```

→ fused instruction khi target hỗ trợ.

---

# 444.112 — FMA semantics

FMA không được tự động dùng nếu nó làm thay đổi floating-point semantics ngoài contract.

---

# 444.113 — Address-mode folding

Machine backend có thể fold:

```text
load(base + index*scale + offset)
```

thành một target addressing mode.

---

# 444.114 — LEA-like optimization

Address arithmetic có thể lower thành native address-generation instruction.

---

# 444.115 — Strength reduction target-aware

Một phép toán rẻ trên target này có thể đắt trên target khác.

Cost model target-specific.

---

# 444.116 — Register pressure

Optimizer phải biết:

```text
register pressure
```

trước aggressive transformations.

---

# 444.117 — Spill-aware optimization

Inlining/unrolling/vectorization không nên tạo quá nhiều spills.

---

# 444.118 — Register allocation feedback

Pipeline có thể:

```text
optimize
→ allocate
→ detect pressure
→ revise selected transformations
```

---

# 444.119 — Machine scheduling

Backend sắp xếp instructions dựa trên:

```text
latency
throughput
dependencies
resources
```

---

# 444.120 — CPU pipeline model

Target CPU model có:

```text
instruction latency
throughput
resource usage
```

ở mức đủ cho optimizer.

---

# 444.121 — Generic CPU baseline

Compiler không được yêu cầu CPU-specific tuning để tạo binary portable.

---

# 444.122 — CPU tuning

User có thể chọn:

```text
-march=native
```

hoặc Axiom equivalent.

---

# 444.123 — Explicit CPU target

Ví dụ:

```text
target.cpu = "..."
```

---

# 444.124 — Feature set

Compiler hỗ trợ:

```text
baseline
features+
```

---

# 444.125 — CPU dispatch

Library có thể có nhiều implementation:

```text
baseline
sse
avx2
neon
```

và chọn runtime.

---

# 444.126 — Function multiversioning

Compiler có thể generate:

```text
foo.baseline
foo.avx2
```

---

# 444.127 — Runtime dispatch overhead

Dispatch chỉ xảy ra ở boundary; inner loop được specialized.

---

# 444.128 — PGO + CPU dispatch

PGO có thể giúp chọn common path nhưng không được phá correctness.

---

# 444.129 — Cache-aware data structures

Standard library có thể cung cấp cache-friendly containers.

Compiler không cần tự động biến mọi structure.

---

# 444.130 — False sharing

Concurrency optimizer không tự động thay đổi synchronization semantics.

Library có thể cung cấp:

```text
@cache_aligned
```

---

# 444.131 — Cache-line alignment

Target metadata có thể expose cache line size.

---

# 444.132 — Prefetch distance

Không hard-code universal prefetch distance.

---

# 444.133 — Memory bandwidth optimization

Vectorization và blocking có thể tối ưu throughput.

---

# 444.134 — NUMA optimization

NUMA-aware allocation/placement thuộc platform/runtime layer.

---

# 444.135 — Parallelization

Compiler **không tự động biến ordinary loops thành multithreaded loops** mặc định.

Parallelism phải explicit/library-driven.

---

# 444.136 — Parallel loop

Library abstraction có thể lower thành thread pool/work stealing.

---

# 444.137 — GPU lowering boundary

GPU kernels có pipeline riêng:

```text
Axiom source
→ GPU semantic subset
→ GPU IR
→ GPU backend
```

Không ép CPU optimizer xử lý GPU.

---

# 444.138 — CPU/GPU shared semantics

Common semantic layer:

```text
types
comptime
generics
traits
```

nhưng execution model tách biệt.

---

# 444.139 — Tensor optimization

Tensor library có thể dùng specialized kernels.

Compiler không cần biến language core thành ML compiler.

---

# 444.140 — Auto-vectorization diagnostics

AI tooling có thể query:

```text
why_not_vectorized(loop)
```

---

# 444.141 — Optimization remarks

Compiler có thể emit:

```text
optimized
not_optimized
missed
```

với reason.

---

# 444.142 — Example diagnostic

```text
OPT44201:
loop not vectorized

reason:
possible alias between a and b

suggestion:
provide non-aliasing contract
```

---

# 444.143 — AI optimization interface

Compiler semantic database cung cấp:

```text
function.cost()
loop.analysis()
alias.analysis()
vectorization.status()
inline.status()
```

---

# 444.144 — No opaque optimizer

Optimizer không nên là black box hoàn toàn đối với tooling.

---

# 444.145 — Optimization explanation

Developer có thể yêu cầu:

```text
axiom explain-opt foo
```

để xem các transformation.

---

# 444.146 — Optimization trace

Compiler debug mode có:

```text
pass
input IR hash
output IR hash
changed
reason
```

---

# 444.147 — Pass manager

Compiler có pass manager:

```text
PassManager
    add(pass)
    run(module)
```

---

# 444.148 — Analysis manager

Analysis cache:

```text
DominatorTree
LoopInfo
AliasAnalysis
RangeAnalysis
MemorySSA
CallGraph
ProfileInfo
```

---

# 444.149 — Analysis invalidation

Pass phải khai báo analysis nào nó invalidate.

Đây là điều kiện quan trọng để optimizer vừa nhanh vừa đúng.

---

# 444.150 — Pass determinism

Cùng:

```text
source
target
compiler version
optimization configuration
profile
```

phải tạo cùng optimization decisions.

---

# 444.151 — Parallel optimization

Independent functions có thể optimize song song.

---

# 444.152 — Function-level parallelism

Đây là primary parallelization strategy trong bootstrap compiler.

---

# 444.153 — Module-level optimization

Cross-module passes chạy sau function-local optimization.

---

# 444.154 — LTO optimization

LTO có thể:

```text
inline
devirtualize
constant-propagate
internalize
dead-strip
```

cross module.

---

# 444.155 — ThinLTO summary

Summary gồm:

```text
size
hotness
calls
exports
dependencies
```

---

# 444.156 — Incremental LTO

Chỉ re-optimize affected graph khi có thể.

---

# 444.157 — Linker interaction

443 linker nhận optimized object/IR và thực hiện:

```text
GC
layout
relocation
relaxation
```

---

# 444.158 — Machine optimization boundary

Sau register allocation, chỉ machine-safe transformations được phép.

---

# 444.159 — Peephole optimizer

Machine backend có local peephole pass.

Ví dụ conceptual:

```text
mov rax, 0
```

→

```text
xor eax, eax
```

chỉ khi target semantics/cost model phù hợp.

---

# 444.160 — Instruction shortening

Có thể chọn encoding nhỏ hơn khi semantics giống nhau.

---

# 444.161 — Code-size optimization

Backend có thể ưu tiên:

```text
short encoding
fewer instructions
smaller literal pools
```

---

# 444.162 — I-cache optimization

Hot code layout được linker hỗ trợ.

---

# 444.163 — Branch layout

Compiler/linker có thể đặt likely path fall-through.

---

# 444.164 — Function ordering

PGO có thể reorder functions theo call graph.

---

# 444.165 — Data ordering

PGO có thể reorder read-mostly data khi safe.

---

# 444.166 — Literal pools

AArch64 backend cần xử lý literal pool placement/range.

---

# 444.167 — Constant islands

Backend phải đảm bảo reachability của literal constants.

---

# 444.168 — Relocation-aware optimization

Optimization không được tạo relocation ngoài range mà backend/linker không xử lý được.

---

# 444.169 — Debug preservation

Optimization phải cập nhật source/debug mapping.

---

# 444.170 — Optimized-out variables

Debug info phải báo biến đã optimized out thay vì tạo giá trị giả.

---

# 444.171 — Step-through semantics

Debug mode có thể giảm aggressive transformations.

---

# 444.172 — `-O0` correctness

`-O0` vẫn phải thực hiện các transformations cần thiết cho correctness/lowering.

---

# 444.173 — Sanitizer interaction

Sanitizer instrumentation phải xảy ra tại phase phù hợp để không bỏ mất lỗi cần phát hiện.

---

# 444.174 — Bounds sanitizer

Có thể instrument những checks mà optimizer chưa chứng minh được.

---

# 444.175 — Address sanitizer

Nếu tích hợp sau này, sanitizer runtime là optional component.

---

# 444.176 — Undefined behavior sanitizer

Unsafe UB detection có thể dùng instrumentation/debug profile.

---

# 444.177 — Optimization + sanitizer

Compiler phải có pipeline riêng:

```text
semantic optimization
→ instrumentation
→ target optimization
```

để instrumentation không bị loại nhầm.

---

# 444.178 — Benchmark harness

Axiom toolchain có:

```text
axiom bench
```

để đo:

```text
runtime
binary size
compile time
memory
```

---

# 444.179 — Performance regression

CI lưu baseline:

```text
execution_time
code_size
compile_time
peak_memory
```

---

# 444.180 — No arbitrary benchmark winner

Compiler chỉ báo measurement.

Không tự tuyên bố optimization "tốt hơn" nếu benchmark không chứng minh.

---

# 444.181 — Benchmark reproducibility

Benchmark metadata:

```text
CPU
OS
compiler
flags
input
profile
```

---

# 444.182 — Hardware counters

Nếu platform hỗ trợ, benchmark tool có thể đọc:

```text
cycles
instructions
branches
cache misses
```

---

# 444.183 — Performance model

Compiler cost model không được nhầm với benchmark thực tế.

---

# 444.184 — Static cost estimate

Compiler có thể estimate:

```text
instruction count
register pressure
code size
```

---

# 444.185 — Runtime cost metadata

AI tooling có thể query:

```text
allocations
branches
calls
vector width
possible blocking
```

---

# 444.186 — Effect-aware optimization

Optimizer phải hiểu metadata:

```text
@no_alloc
@no_panic
@no_block
```

---

# 444.187 — Contract preservation

Nếu function có:

```text
@no_alloc
```

optimizer không được introduce hidden allocation.

---

# 444.188 — `@no_block`

Optimization không được biến code thành blocking operation.

---

# 444.189 — `@no_panic`

Compiler phải reject code path có thể panic nếu contract được khai báo strict.

---

# 444.190 — Unsafe optimization

Unsafe không có nghĩa "optimizer tắt".

Unsafe code vẫn được optimize dựa trên semantics đã khai báo.

---

# 444.191 — `volatile`

Compiler giữ observable volatile ordering theo target memory model.

---

# 444.192 — Atomics

Atomic ordering không được weaken ngoài permitted transformation.

---

# 444.193 — Lock optimization

Compiler không tự loại mutex lock/unlock chỉ vì chúng có vẻ redundant nếu synchronization semantics có thể observable.

---

# 444.194 — Concurrency optimization

Compiler chỉ reorder ordinary memory operations khi memory model cho phép.

---

# 444.195 — Async optimization

Async state machines có thể:

```text
remove states
merge states
inline poll
eliminate allocations
```

---

# 444.196 — Future allocation elimination

Nếu Future không escape executor boundary:

```text
heap state
```

có thể được stack/register allocated.

---

# 444.197 — Async frame layout

Unused captured state được loại bỏ.

---

# 444.198 — Iterator + async fusion

Nested abstractions có thể fuse nếu semantics cho phép.

---

# 444.199 — Optimization architecture

Toàn bộ hệ thống:

```text
                ┌──────────────┐
                │     HIR      │
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │     MIR      │
                └──────┬───────┘
                       ▼
          ┌────────────────────────┐
          │ Analysis Infrastructure│
          │ SSA / MemorySSA / CFG  │
          │ Alias / Range / Loop   │
          └───────────┬────────────┘
                      ▼
               MIR Optimizer
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
   Scalar           Memory         Loop
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Vectorizer
                      ▼
                 LIR Optimizer
                      ▼
               Machine Lowering
                      ▼
             Register Allocation
                      ▼
              Machine Optimizer
                      ▼
                  Object
                      ▼
                  Linker
                      ▼
              Native Artifact
```

---

# 444.200 — Hard invariants

1. Optimization không thay đổi semantics hợp lệ.
2. `-O0` vẫn phải đúng.
3. `-O3` không phải semantic mode.
4. Fast-math phải explicit.
5. Integer overflow semantics phải được bảo toàn.
6. Checked/wrapping/saturating arithmetic không được trộn.
7. Volatile không được loại bỏ.
8. Atomic semantics không được biến thành ordinary memory operations.
9. IO là observable side effect.
10. Unsafe code vẫn được optimize.
11. Alias information phải có cơ sở hợp lệ.
12. Không tự suy đoán `noalias`.
13. Memory SSA là nền tảng cho memory optimization.
14. Bounds-check elimination phải dựa trên proof/range analysis.
15. Safe code có thể đạt zero-cost bounds checks khi compiler chứng minh được.
16. Inlining là optimization, không phải semantic requirement mặc định.
17. `@noinline` phải được tôn trọng.
18. `@inline` không được coi là absolute guarantee.
19. Generic specialization phải được optimize như native code.
20. Static trait dispatch phải có khả năng zero-overhead.
21. Dynamic dispatch giữ runtime dispatch cost khi không devirtualize được.
22. Closure allocation phải được loại bỏ khi escape analysis cho phép.
23. Temporary aggregate có thể scalar-replace.
24. Heap allocation không escape có thể stack-promote.
25. Loop transformations phải preserve dependencies.
26. Vectorization phải có legality analysis.
27. Vectorization phải có target-aware cost model.
28. Floating-point reassociation phải tuân contract.
29. Register pressure phải được tính vào optimization decisions.
30. Machine scheduler phải target-aware.
31. Machine optimizer chỉ được thực hiện transformations hợp lệ với target.
32. PGO là optional.
33. PGO profile phải target-aware.
34. PGO phải deterministic với cùng profile/input.
35. Parallel optimization phải deterministic.
36. Analysis invalidation phải explicit.
37. Optimization passes phải có dependency contract.
38. Debug/source mapping phải được cập nhật sau optimization.
39. Optimized-out values không được giả mạo.
40. Sanitizer pipeline phải bảo toàn instrumentation.
41. Async state machines có thể được optimize aggressively.
42. Async allocation không phải bắt buộc.
43. Iterator abstraction phải có zero-cost path.
44. Platform-specific optimization không được xâm nhập language semantics.
45. CPU-specific instructions phải được bảo vệ bởi target feature contract.
46. Baseline code không được chứa instruction ngoài baseline feature set.
47. Function multiversioning phải giữ baseline fallback khi yêu cầu portability.
48. Compiler có thể giải thích optimization decisions.
49. AI tooling có thể query optimization analysis.
50. Performance measurement phải tách khỏi compiler opinion.
51. Code-size optimization phải là first-class target.
52. Runtime speed và binary size là hai objective độc lập.
53. Optimizer không được biến abstraction thành runtime overhead khi information cho phép loại bỏ.
54. Compiler không tự thêm parallelism.
55. Compiler không tự thêm allocation.
56. Compiler không tự thêm locking.
57. Compiler không tự thêm hidden runtime calls nếu semantics không yêu cầu.
58. LTO là optional nhưng native.
59. Linker và optimizer có contract rõ ràng.
60. **Axiom phải có đường tối ưu từ high-level abstractions → machine code mà không cần LLVM/GCC/Clang.**

**BOOTSTRAP-444 hoàn tất.**

---

# BOOTSTRAP-445 — SECURITY MODEL, MEMORY SAFETY BOUNDARY, SANDBOX, TRUST MODEL & SECURE NATIVE CODE CONTRACT

Đây là bước tiếp theo vì sau khi đã khóa:

- semantics,
- memory,
- ownership,
- concurrency,
- ABI,
- runtime,
- platform,
- linker,
- optimizer,

Axiom cần khóa câu hỏi cuối cùng ở tầng native:

> **Phần nào compiler bảo đảm, phần nào programmer chịu trách nhiệm, và đâu là ranh giới giữa safe / unsafe / FFI / OS / hardware?**

Kiến trúc tiếp theo sẽ phân thành:

```text
                 AXIOM PROGRAM
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          SAFE CODE           UNSAFE CODE
             │                   │
       compiler guarantees   explicit responsibility
             │                   │
             └─────────┬─────────┘
                       ▼
                    FFI/API
                       │
              ┌────────┴────────┐
              ▼                 ▼
             OS             Hardware
```

và đặc biệt sẽ khóa:

```text
safe memory
raw pointers
FFI trust boundary
unsafe blocks
integer/pointer provenance
data races
uninitialized memory
MMIO
executable memory
sandbox
capability model
supply-chain metadata
artifact trust
compiler trust boundary
bootstrap trust
```

**BOOTSTRAP-445 là task kế tiếp của chuỗi.**