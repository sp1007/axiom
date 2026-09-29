# BOOTSTRAP-449 — OPTIMIZATION PIPELINE, COST MODEL, AUTO-VECTORIZATION, INLINING, ESCAPE ANALYSIS & ZERO-COST ABSTRACTION CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của task này là khóa optimizer của Axiom sao cho:

```text
abstraction cao
        ↓
semantic cost = 0 nếu không cần thiết
        ↓
native machine code tối ưu
```

Axiom không được biến generic, trait, iterator, closure, struct-method hoặc wrapper thành overhead runtime chỉ vì chúng tồn tại ở source level.

---

## 449.1 — Optimization philosophy

Optimizer phải ưu tiên:

1. correctness;
2. predictable semantics;
3. performance;
4. binary size;
5. compile time.

Thứ tự giữa 3–5 có thể thay đổi theo build profile.

---

## 449.2 — Zero-cost abstraction

Một abstraction được coi là zero-cost khi compiler có thể loại bỏ toàn bộ representation/runtime overhead không cần thiết.

Ví dụ:

```text
trait
generic function
iterator
small closure
struct method
```

có thể compile thành code tương đương implementation trực tiếp.

---

## 449.3 — Không cam kết “luôn bằng C”

Axiom không đưa ra guarantee rằng mọi chương trình luôn nhanh hơn hoặc bằng C/C++.

Thay vào đó compiler phải cung cấp optimization facilities đủ mạnh để đạt native performance tương đương trong các trường hợp semantics tương đương.

---

## 449.4 — Optimization correctness

Mọi optimization phải preserve observable language semantics.

---

## 449.5 — Observable behavior

Observable behavior bao gồm:

```text
return values
memory effects
volatile accesses
atomic ordering
I/O
panic/abort
thread synchronization
FFI calls
```

---

## 449.6 — Optimization pipeline

Pipeline canonical:

```text
HIR
 ↓
MIR
 ↓
MIR canonicalization
 ↓
SSA
 ↓
scalar optimization
 ↓
memory optimization
 ↓
loop optimization
 ↓
vectorization
 ↓
lowering
 ↓
LIR
 ↓
target optimization
 ↓
Machine IR
 ↓
register allocation
 ↓
machine scheduling
 ↓
peephole optimization
```

---

## 449.7 — Optimization passes

Passes phải có explicit contract:

```text
input IR
output IR
preserved analyses
required analyses
cost
```

---

## 449.8 — Pass manager

Optimizer dùng pass manager thay vì hard-coded một chuỗi khổng lồ.

---

## 449.9 — Analysis manager

Các analysis có thể được cache:

```text
DominatorTree
LoopInfo
AliasInfo
RangeInfo
EscapeInfo
CallGraph
TypeInfo
```

---

## 449.10 — Analysis invalidation

Transform làm thay đổi IR phải invalidate các analysis liên quan.

---

## 449.11 — Canonicalization

MIR trước optimization phải được canonicalize để giảm các dạng biểu diễn tương đương.

---

## 449.12 — Constant folding

Ví dụ:

```text
x = 4 * 8
```

→

```text
x = 32
```

---

## 449.13 — Constant propagation

Giá trị constant được propagate qua CFG khi an toàn.

---

## 449.14 — Sparse propagation

Compiler ưu tiên sparse/value-based propagation thay vì scan toàn function nếu phù hợp.

---

## 449.15 — Dead code elimination

Code không có observable effect được loại bỏ.

---

## 449.16 — Dead store elimination

Store bị overwrite trước khi observable/read được loại bỏ khi safe.

---

## 449.17 — Dead argument elimination

Internal functions có thể loại bỏ argument không được dùng nếu call graph cho phép.

Không áp dụng tùy tiện cho stable ABI/FFI exports.

---

## 449.18 — CFG simplification

Optimizer loại bỏ:

```text
empty blocks
constant branches
unreachable blocks
redundant jumps
```

---

## 449.19 — Branch folding

Branch có điều kiện compile-time/known runtime được simplify.

---

## 449.20 — Jump threading

Các branch chain redundant được nối trực tiếp khi có lợi.

---

# 449.21 — SSA

MIR optimization dùng SSA hoặc SSA-like representation.

---

## 449.22 — SSA value

Mỗi SSA definition có single assignment.

---

## 449.23 — Phi node

CFG merge sử dụng:

```text
phi
```

hoặc equivalent block parameter representation.

---

## 449.24 — Memory SSA

Memory-dependent operations có thể sử dụng Memory SSA.

---

## 449.25 — Memory SSA purpose

Giúp optimizer reason về:

```text
load
store
call
memory clobber
```

---

## 449.26 — Stack promotion

Local allocation có thể được promote nếu escape analysis chứng minh không escape.

---

## 449.27 — Scalar replacement

Struct/aggregate có thể được split thành scalar values.

Ví dụ:

```text
Vec2{x, y}
```

có thể trở thành:

```text
x
y
```

nếu address không observable.

---

## 449.28 — Aggregate elimination

Temporary aggregate không cần materialize trong memory nếu ABI/observable semantics cho phép.

---

## 449.29 — Copy propagation

Redundant copies được loại bỏ.

---

## 449.30 — Load forwarding

Known store → load được forward khi alias analysis chứng minh an toàn.

---

## 449.31 — Store-to-load forwarding

```text
*p = x
y = *p
```

có thể trở thành:

```text
y = x
```

nếu không có intervening observable modification.

---

# 449.32 — Alias analysis

Alias analysis là thành phần quan trọng nhưng không được giả định mạnh hơn semantics cho phép.

---

## 449.33 — Default alias model

Axiom không mặc định giả định mọi pointer/reference là `noalias`.

---

## 449.34 — Proven non-alias

Compiler có thể chứng minh non-alias thông qua:

```text
ownership
local allocation
distinct objects
scope
type/layout
explicit contracts
```

---

## 449.35 — Explicit noalias contract

Có thể hỗ trợ metadata/attribute:

```text
@noalias
```

nhưng chỉ hợp lệ khi programmer contract đúng.

---

## 449.36 — Unsafe aliasing

Unsafe code có thể tạo alias patterns compiler không chứng minh được.

Optimizer không được dựa vào false assumptions từ safe-looking syntax.

---

## 449.37 — FFI aliasing

FFI boundary phải có conservative alias assumptions trừ khi contract khai báo rõ.

---

# 449.38 — Bounds-check elimination

Safe array/slice access có thể có bounds check.

Optimizer phải cố loại bỏ check khi range analysis chứng minh index hợp lệ.

---

## 449.39 — Loop bounds

Ví dụ:

```text
for i in 0..n {
    a[i] = ...
}
```

compiler phải có khả năng suy ra:

```text
0 <= i < n
```

và loại bỏ check trong loop body nếu `n <= length(a)` được chứng minh.

---

## 449.40 — Range analysis

Compiler duy trì abstract ranges:

```text
[min, max]
```

hoặc equivalent symbolic constraints.

---

## 449.41 — Check hoisting

Một bounds check invariant có thể được đưa ra ngoài loop.

---

## 449.42 — Check fusion

Multiple compatible checks có thể được hợp nhất.

---

## 449.43 — Unchecked operations

`unsafe` unchecked access vẫn tồn tại như escape hatch.

---

## 449.44 — Unsafe ≠ optimization requirement

Programmer không phải dùng unsafe chỉ để đạt performance khi optimizer có thể eliminate checks.

---

# 449.45 — Escape analysis

Escape analysis phân loại object/value:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

---

## 449.46 — NoEscape allocation

Heap allocation NoEscape có thể:

```text
stack promote
scalar replace
eliminate
```

---

## 449.47 — FunctionEscape

Có thể stack-allocate nếu lifetime kết thúc sau call hoặc compiler chứng minh callee không retain.

---

## 449.48 — ThreadEscape

Object chuyển sang thread khác phải được coi escaped trừ khi synchronization semantics cho phép chứng minh khác.

---

## 449.49 — GlobalEscape

Global/static storage không được stack promote.

---

## 449.50 — Allocation elimination

Nếu allocation chỉ tạo temporary không observable:

```text
allocate
initialize
read
drop
```

có thể biến mất hoàn toàn.

---

## 449.51 — Allocator call visibility

Custom allocator có thể làm allocation observable.

Trong trường hợp đó optimizer không được silently eliminate nếu semantics yêu cầu allocator callback.

---

## 449.52 — Destructor visibility

`drop` có side effect thì object không được loại bỏ chỉ vì value không được dùng.

---

## 449.53 — Pure destructor

Nếu compiler biết destructor không có observable effect, optimization có thể mạnh hơn.

---

# 449.54 — Inlining

Inlining là optimization chính.

---

## 449.55 — Inline candidates

Compiler có thể inline:

```text
small functions
generic functions
struct methods
trait static dispatch
closures
property-like accessors
```

---

## 449.56 — `@inline`

Attribute cho compiler hint:

```text
@inline
```

---

## 449.57 — `@noinline`

Ngăn inline trừ trường hợp compiler bắt buộc transform vì correctness/toolchain requirement.

---

## 449.58 — Inline heuristic

Heuristic xem xét:

```text
function size
call frequency
loop nesting
branch count
register pressure
code size
hotness
target CPU
```

---

## 449.59 — Recursive inline

Recursive functions có bounded inline depth.

---

## 449.60 — Generic inline

Monomorphized generic code có thể inline như ordinary function.

---

## 449.61 — Trait devirtualization

Nếu static dispatch:

```text
T: Trait
```

và concrete T known:

```text
trait call
→ direct function
```

---

## 449.62 — Dynamic dispatch

`dyn Trait` là explicit runtime dispatch.

---

## 449.63 — Dynamic devirtualization

Compiler có thể devirtualize dynamic call nếu concrete type được chứng minh duy nhất.

---

## 449.64 — Devirtualization guard

Nếu runtime type có thể thay đổi, compiler có thể generate guarded specialization:

```text
if type == A
    direct call
else
    dynamic dispatch
```

---

## 449.65 — Closure optimization

Closure được biểu diễn conceptually:

```text
code pointer
+
environment
```

---

## 449.66 — Closure elimination

Non-capturing closure có thể trở thành ordinary function pointer.

---

## 449.67 — Capturing closure scalarization

Nếu environment không escape, environment allocation có thể biến mất.

---

# 449.68 — Generic specialization

Generic monomorphization cho phép optimizer biết concrete types.

---

## 449.69 — Generic constant propagation

Const generic:

```text
Array<T, N>
```

cho phép specialize theo `N`.

---

## 449.70 — Generic code bloat

Compiler không được tạo vô hạn duplicate machine code.

---

## 449.71 — Generic deduplication

Equivalent generated implementations có thể share machine code.

---

## 449.72 — Partial specialization

Compiler có thể specialize phần code phụ thuộc type/const parameter.

---

## 449.73 — Specialization policy

Specialization phải deterministic.

---

# 449.74 — Loop optimization

Optimizer hỗ trợ:

```text
loop invariant code motion
induction variables
strength reduction
unrolling
peeling
fusion
fission
unswitching
```

---

## 449.75 — Loop invariant code motion

Expression không phụ thuộc loop iteration có thể move ra ngoài.

---

## 449.76 — Induction variable optimization

Compiler nhận diện:

```text
i += 1
```

và related expressions.

---

## 449.77 — Strength reduction

Ví dụ multiplication bằng constant có thể được thay bằng cheaper operations nếu target có lợi.

---

## 449.78 — Loop unrolling

Unroll dựa trên cost model.

---

## 449.79 — Loop unrolling limit

Không được unroll vô hạn gây code explosion.

---

## 449.80 — Loop fusion

Hai loop tương thích có thể merge nếu semantics cho phép.

---

## 449.81 — Loop vectorization

Compiler có thể biến:

```text
for i ...
    a[i] += b[i]
```

thành SIMD.

---

# 449.82 — SIMD model

Axiom có:

```text
portable SIMD
```

và target-specific SIMD intrinsics.

---

## 449.83 — Auto-vectorization

Compiler có thể tự vectorize scalar loops.

---

## 449.84 — Vectorization legality

Phải kiểm tra:

```text
dependencies
aliasing
memory alignment
side effects
control flow
```

---

## 449.85 — Runtime alias checks

Compiler có thể generate runtime checks để vectorize:

```text
if non-overlap
    vector loop
else
    scalar loop
```

nếu cost model thấy có lợi.

---

## 449.86 — Alignment optimization

Known alignment có thể giúp chọn vector instructions phù hợp.

---

## 449.87 — Unaligned SIMD

Compiler có thể dùng unaligned operations khi target hỗ trợ và cost có lợi.

---

## 449.88 — Reduction vectorization

Compiler hỗ trợ reductions:

```text
sum
min
max
```

theo floating-point semantics.

---

## 449.89 — Floating-point strictness

Floating-point reassociation không được tự động phá semantics strict.

---

## 449.90 — Fast-math

Có thể có explicit profile/attribute:

```text
@fast_math
```

cho phép relaxed FP transformations.

---

## 449.91 — Fast-math scope

Fast-math phải explicit và machine-readable.

---

## 449.92 — NaN/Infinity semantics

Strict mode preserve defined IEEE behavior.

---

## 449.93 — Integer overflow

Optimizer phải respect Axiom integer overflow semantics:

```text
checked
wrapping
saturating
```

tùy operation/type/context.

---

# 449.94 — Branch optimization

Compiler dùng:

```text
branch probability
profile data
control-flow simplification
```

---

## 449.95 — Likely/unlikely

Có thể hỗ trợ hints:

```text
@likely
@unlikely
```

nhưng chỉ là optimization hints.

---

## 449.96 — PGO branch data

PGO có thể cung cấp real execution frequencies.

---

## 449.97 — Hot/cold splitting

Hot và cold blocks có thể được tách để cải thiện instruction cache.

---

## 449.98 — Function hot/cold partitioning

Large functions có thể split cold paths.

---

# 449.99 — Cache locality

Optimizer/linker có thể cải thiện:

```text
instruction locality
data locality
function layout
```

---

## 449.100 — Function ordering

PGO có thể reorder functions.

---

# 449.101 — Register pressure

Optimization phải xét register pressure.

---

## 449.102 — Over-inlining control

Inlining có thể làm register pressure tăng và làm code chậm hơn.

Cost model phải tính điều này.

---

## 449.103 — Register allocation feedback

Backend có thể phản hồi:

```text
spill count
register pressure
```

cho optimization pipeline.

---

## 449.104 — Spill-aware optimization

Optimizer có thể tránh transformations tạo quá nhiều spills.

---

# 449.105 — Instruction selection awareness

High-level optimizer không được giả định target instruction costs giống nhau.

---

## 449.106 — Target cost model

Target backend cung cấp:

```text
latency
throughput
instruction size
register cost
branch cost
vector width
```

ở mức cần thiết.

---

## 449.107 — Cost model abstraction

Optimizer dùng target-independent interface.

---

## 449.108 — Target-specific optimization

Backend có thể bổ sung machine-specific transforms.

---

## 449.109 — Peephole optimization

Machine IR hỗ trợ local transformations.

Ví dụ:

```text
redundant move
```

→ loại bỏ.

---

## 449.110 — Instruction combining

Pattern:

```text
add
shift
load
compare
```

có thể combine thành target instruction nếu tồn tại.

---

## 449.111 — Addressing mode optimization

x86-64/AArch64 backend có thể fold arithmetic vào addressing mode khi có lợi.

---

## 449.112 — Load/store optimization

Machine optimizer có thể combine hoặc eliminate redundant memory operations.

---

# 449.113 — ABI optimization

Return/argument lowering phải được tối ưu theo ABI.

---

## 449.114 — Scalar return optimization

Small aggregates có thể return trong registers nếu ABI cho phép.

---

## 449.115 — SRet elimination

Compiler không được materialize unnecessary hidden return storage khi ABI/optimization cho phép scalarize.

---

## 449.116 — Tail calls

Tail-call optimization khi ABI + semantics cho phép.

---

## 449.117 — Must-tail

Explicit tail-call contract có thể yêu cầu backend bảo đảm điều kiện ABI hoặc báo lỗi.

---

# 449.118 — `@inline` semantics

`@inline` là **strong hint**, không phải guarantee machine code inline.

---

## 449.119 — `@always_inline`

Có thể hỗ trợ stronger directive cho compiler-internal/high-performance code.

Nếu impossible do ABI/recursion/backend constraints → diagnostic hoặc fallback policy rõ ràng.

---

## 449.120 — `@noinline`

Ngăn optimizer inline function khi legal.

---

## 449.121 — Cold functions

```text
@cold
```

có thể hướng compiler tối ưu layout/size.

---

# 449.122 — Allocation-aware optimization

Optimizer phải biết function effects:

```text
@allocates
@no_alloc
```

---

## 449.123 — No-allocation contract

`@no_alloc` violation phải diagnostic nếu statically provable.

---

## 449.124 — Blocking-aware optimization

`@no_block` giúp scheduler/compiler reasoning.

---

## 449.125 — Panic-aware optimization

`@no_panic` có thể hỗ trợ control-flow optimization.

---

## 449.126 — Effect metadata

Effect metadata từ 446/441 được dùng làm optimization input.

---

# 449.127 — Interprocedural optimization

Compiler hỗ trợ analysis xuyên function boundaries.

---

## 449.128 — Call graph

Call graph nodes:

```text
function
method
closure
FFI boundary
dynamic dispatch
```

---

## 449.129 — SCC analysis

Recursive call groups được phân tích theo strongly connected components.

---

## 449.130 — Constant argument propagation

Caller có thể truyền known constants để specialize callee.

---

## 449.131 — Function cloning

Compiler có thể clone function cho hot/constant cases.

---

## 449.132 — Clone budget

Code growth phải được giới hạn.

---

# 449.133 — Link-time optimization

Axiom linker/compiler có thể thực hiện cross-object optimization khi intermediate representation hoặc suitable metadata được available.

---

## 449.134 — LTO modes

```text
none
thin
full
```

---

## 449.135 — Thin LTO

Các module giữ summary:

```text
size
hotness
calls
dependencies
```

để quyết định optimization mà không load toàn bộ program.

---

## 449.136 — Full LTO

Có thể merge relevant IR toàn chương trình.

---

## 449.137 — LTO and binary packages

Binary-only library không cần expose internal IR.

---

## 449.138 — LTO boundary

Closed binary package là optimization boundary.

---

# 449.139 — Profile-guided optimization

PGO dùng runtime profile.

---

## 449.140 — Instrumentation

Compiler tạo instrumentation build.

---

## 449.141 — Profile merge

Nhiều runs có thể merge profile.

---

## 449.142 — Profile validation

Profile được kiểm tra compatibility.

---

## 449.143 — PGO decisions

Có thể ảnh hưởng:

```text
inlining
branch layout
function ordering
unrolling
specialization
```

---

# 449.144 — Optimization profiles

Axiom chuẩn hóa:

```text
debug
balanced
release
size
```

---

## 449.145 — Debug optimization

Giữ debug quality cao hơn aggressive transformation.

---

## 449.146 — Balanced

Compile time và runtime performance cân bằng.

---

## 449.147 — Release

Aggressive optimization.

---

## 449.148 — Size

Ưu tiên code size nhưng không phá semantics.

---

# 449.149 — Compile-time budget

Optimizer có budget:

```text
time
memory
IR size
code growth
```

---

## 449.150 — Adaptive optimization

Nếu budget gần vượt:

```text
skip expensive pass
```

thay vì compiler OOM.

---

## 449.151 — Function-level budget

Large functions có thể nhận budget riêng.

---

## 449.152 — Hot function budget

PGO/hotness có thể allocate optimization budget lớn hơn cho hot functions.

---

## 449.153 — Cold function budget

Cold code ưu tiên compile speed/size.

---

# 449.154 — Optimization diagnostics

Compiler có thể xuất:

```text
optimization remarks
```

---

## 449.155 — Inline remark

Ví dụ:

```text
inlined: foo
reason: small_hot_function
```

---

## 449.156 — Missed inline

Ví dụ:

```text
not_inlined: bar
reason: code_growth
```

---

## 449.157 — Bounds-check remark

```text
bounds_check:
    eliminated
reason:
    loop_range_proves_valid
```

---

## 449.158 — Allocation remark

```text
allocation:
    eliminated
reason:
    no_escape
```

---

## 449.159 — Vectorization remark

```text
vectorized:
    yes
width:
    8
```

---

## 449.160 — Missed vectorization

Diagnostic phải nêu lý do machine-readable:

```text
loop-carried-dependency
unknown-alias
unsupported-operation
cost-too-high
```

---

# 449.161 — Optimization explain API

AI/tooling có thể query:

```text
why_not_inline(FunctionId)
why_not_vectorize(LoopId)
why_allocation_remains(ValueId)
why_bounds_check_remains(LocationId)
why_devirtualization_failed(CallId)
```

---

## 449.162 — Optimization provenance

Mỗi important optimization có thể record:

```text
pass
input
decision
reason
cost
```

---

## 449.163 — AI optimization loop

Agent có thể:

```text
benchmark
→ inspect profile
→ query missed optimization
→ modify source
→ rebuild
→ benchmark
```

---

# 449.164 — Benchmark integration

Axiom benchmark runner có thể record:

```text
runtime
throughput
latency
binary size
compile time
memory
```

---

## 449.165 — Regression detection

Build system có thể compare current vs baseline.

---

## 449.166 — No optimizer gaming

Compiler test suite phải kiểm tra semantics, không chỉ assembly pattern.

---

## 449.167 — Assembly inspection

Tool:

```text
axiom emit asm
```

cho phép inspect generated assembly.

---

## 449.168 — Machine IR inspection

Developer/AI có thể inspect:

```text
MIR
LIR
Machine IR
```

---

## 449.169 — Optimization pipeline dump

Có thể dump IR sau từng pass.

---

## 449.170 — Deterministic optimization

Cùng source/config/compiler/target phải produce cùng optimization decisions trong deterministic mode.

---

# 449.171 — UB-aware optimization

Optimizer có thể tận dụng language-defined UB.

---

## 449.172 — Safe subset

Safe code phải có semantics compiler có thể reason về.

---

## 449.173 — Unsafe subset

Unsafe code có thể expose UB.

Optimizer được phép assume program không thực hiện UB theo language contract.

---

## 449.174 — Volatile

Volatile access không được eliminate/merge tùy tiện.

---

## 449.175 — Atomic

Atomic semantics phải preserve memory ordering.

---

## 449.176 — Fence

Fence không được remove nếu observable synchronization semantics thay đổi.

---

## 449.177 — Concurrency optimization

Compiler được reorder ordinary operations nếu memory model cho phép.

Không được reorder atomic operations trái memory order.

---

## 449.178 — FFI call

Opaque foreign call được coi là potentially side-effecting theo contract.

---

## 449.179 — Pure FFI

Có thể đánh dấu foreign function:

```text
@pure
```

nếu contract đáng tin cậy.

---

# 449.180 — String optimization

UTF-8 strings có thể được tối ưu như byte arrays khi semantics cho phép.

---

## 449.181 — Small value optimization

Compiler có thể scalarize small strings/views/structs.

---

## 449.182 — String literal deduplication

Identical immutable literals có thể share storage.

---

## 449.183 — Constant data merging

Equivalent immutable constants có thể merge.

---

# 449.184 — Enum optimization

Compiler có thể sử dụng:

```text
niche
tag compression
branch simplification
```

---

## 449.185 — Option optimization

`Option<T>` có thể có same representation as T khi niche tồn tại.

---

## 449.186 — Match optimization

Pattern matching có thể lower thành:

```text
branch tree
jump table
binary search
bit test
```

tùy target/cost.

---

# 449.187 — Switch optimization

Integer/enum switch có thể chọn:

```text
jump table
binary tree
linear chain
```

---

## 449.188 — Range pattern optimization

Range patterns có thể lower thành compare/range check hiệu quả.

---

# 449.189 — Async optimization

Async state machines phải được tối ưu như ordinary stateful code.

---

## 449.190 — State elimination

State fields không cần thiết có thể bị eliminate.

---

## 449.191 — Async allocation elimination

Future/task allocation có thể stack-promote nếu không escape.

---

## 449.192 — Suspend-point analysis

Chỉ state sống qua suspend point mới cần preserve.

---

# 449.193 — Iterator optimization

Iterator abstraction phải có khả năng zero-cost.

---

## 449.194 — Iterator fusion

Chains như:

```text
map
filter
map
```

có thể fuse thành một loop.

---

## 449.195 — Iterator allocation elimination

Temporary iterator objects có thể biến mất hoàn toàn.

---

# 449.196 — Trait optimization

Static trait dispatch phải inline/devirtualize được.

---

## 449.197 — Dynamic trait boundary

`dyn Trait` vẫn giữ dynamic dispatch nếu compiler không chứng minh được concrete type.

---

# 449.198 — Optimization contract for language design

Các abstraction sau **không được mặc định yêu cầu runtime object**:

```text
struct methods
traits
generic functions
const generics
small closures
iterators
Option
Result
enums
```

---

# 449.199 — Final zero-cost principle

Axiom principle:

```text
If an abstraction has no observable runtime semantics,
the compiler may erase its runtime representation completely.
```

---

# 449.200 — Hard invariants

1. Optimizer phải preserve semantics.
2. Optimization pipeline có pass manager.
3. Analysis có dependency/invalidation contract.
4. MIR có SSA hoặc SSA-equivalent representation.
5. Memory optimization có thể dùng Memory SSA.
6. Constant folding bắt buộc.
7. Constant propagation bắt buộc.
8. CFG simplification bắt buộc.
9. DCE bắt buộc.
10. Copy propagation được hỗ trợ.
11. Load/store forwarding được hỗ trợ.
12. Alias analysis là first-class.
13. Compiler không giả định mọi pointer `noalias`.
14. Ownership facts có thể hỗ trợ alias analysis.
15. FFI aliasing mặc định conservative.
16. Bounds-check elimination được hỗ trợ.
17. Range analysis được hỗ trợ.
18. Safe code không cần unsafe chỉ để loại bỏ bounds check nếu compiler chứng minh được.
19. Escape analysis được hỗ trợ.
20. NoEscape allocation có thể stack-promote.
21. Scalar replacement được hỗ trợ.
22. Allocation elimination được hỗ trợ.
23. Destructor side effects phải được preserve.
24. Inlining là optimization chính.
25. `@inline` là hint mạnh, không mặc định guarantee.
26. `@noinline` được hỗ trợ.
27. Static trait dispatch có thể devirtualize.
28. Dynamic dispatch chỉ được loại bỏ khi compiler chứng minh được.
29. Closure environment có thể scalarize/eliminate.
30. Generic specialization được hỗ trợ.
31. Generic code bloat phải có control.
32. Loop optimization là first-class.
33. Auto-vectorization được hỗ trợ.
34. SIMD legality phải xét dependency/alias/side effects.
35. Runtime alias checks có thể dùng để vectorize.
36. Floating-point reassociation strict không được tự động phá semantics.
37. Fast-math phải explicit.
38. Integer overflow semantics phải được preserve.
39. Branch optimization được hỗ trợ.
40. Hot/cold layout được hỗ trợ.
41. Register pressure phải được đưa vào cost model.
42. Backend có thể phản hồi spill pressure.
43. Instruction selection có target cost model.
44. Machine peephole optimization được hỗ trợ.
45. Addressing-mode optimization được hỗ trợ.
46. ABI lowering phải được optimization-aware.
47. Tail calls được hỗ trợ khi ABI cho phép.
48. LTO được hỗ trợ.
49. Thin LTO có thể dùng summaries.
50. Binary-only package vẫn là optimization boundary.
51. PGO là optional.
52. PGO data phải có identity/validation.
53. Optimization profiles được chuẩn hóa.
54. Optimizer có time/memory/code-growth budget.
55. Adaptive optimization có thể bỏ pass expensive khi budget cạn.
56. Optimization decisions có thể được giải thích.
57. Missed optimization reasons phải machine-readable.
58. AI có thể query optimization decisions.
59. MIR/LIR/Machine IR có thể inspect.
60. Assembly output có thể inspect.
61. Optimization phải deterministic trong deterministic build mode.
62. Volatile semantics phải preserve.
63. Atomic memory ordering phải preserve.
64. FFI side effects phải được conservative nếu không có contract.
65. Enum/Option niche optimization được hỗ trợ.
66. Match/switch lowering được target-aware.
67. Async state machines được tối ưu.
68. Iterator chains có thể fuse.
69. Struct-first methods không tạo implicit runtime overhead.
70. Generic/trait abstraction không tạo overhead nếu static resolution đủ.
71. Dynamic dispatch chỉ tồn tại khi semantics yêu cầu hoặc optimization không thể loại bỏ.
72. Axiom không yêu cầu programmer manually flatten abstraction để có native performance.
73. Compiler có thể optimize abstraction xuyên nhiều layer.
74. Binary size là một cost dimension độc lập runtime speed.
75. Compile time là một cost dimension độc lập runtime speed.
76. Optimization phải tránh code explosion.
77. Unsafe UB có thể được tận dụng theo language contract nhưng safe semantics không được phá.
78. `Result`/`Option` phải có khả năng compile thành branch/value representation đơn giản.
79. `async`, iterator, closure phải có đường zero-allocation khi escape analysis cho phép.
80. **Axiom optimizer phải biến abstraction thành machine code trực tiếp và hiệu quả khi có thể, thay vì bắt programmer trả “runtime tax” cho cấu trúc ngôn ngữ hiện đại.**

**BOOTSTRAP-449 hoàn tất.**

---

# BOOTSTRAP-450 — RUNTIME PERFORMANCE, BENCHMARK SUITE, CODE-SIZE BUDGET, STARTUP LATENCY & PERFORMANCE REGRESSION CONTRACT

Task tiếp theo sẽ khóa **tiêu chuẩn đo lường** của Axiom.

Không chỉ nói “nhanh”, Axiom cần một hệ thống benchmark có thể chứng minh:

```text
compile time
runtime
latency
throughput
memory
allocation
binary size
startup time
code generation quality
```

và phân biệt rõ:

```text
language overhead
compiler overhead
runtime overhead
library overhead
OS/platform overhead
```

để tránh tình trạng optimizer “trông có vẻ tốt” nhưng thực tế tạo binary lớn, startup chậm hoặc compile quá lâu.