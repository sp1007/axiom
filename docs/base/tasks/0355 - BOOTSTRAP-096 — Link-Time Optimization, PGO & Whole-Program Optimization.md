# BOOTSTRAP-096 — Link-Time Optimization, PGO & Whole-Program Optimization

**Trạng thái: FROZEN**

Mục tiêu của task này là hoàn thiện tầng tối ưu **sau khi từng module/generic instance đã được compile**, nhưng trước khi tạo executable cuối cùng.

Axiom cần đồng thời đạt:

```text
Compile nhanh
+
Incremental build tốt
+
Library/module độc lập
+
Whole-program optimization mạnh
+
Binary nhỏ
+
Không cần runtime thừa
```

Nguyên tắc trung tâm:

> **Compiler càng biết nhiều về toàn chương trình thì càng được phép tối ưu mạnh hơn, nhưng không được thay đổi semantic contract.**

---

# 1. Ba tầng tối ưu

Axiom chia tối ưu thành:

```text
Local Optimization
        ↓
Module Optimization
        ↓
Whole-Program Optimization
```

### Local

Biết một function:

```text
foo()
```

### Module

Biết:

```text
foo()
bar()
baz()
```

và quan hệ giữa chúng.

### Whole program

Biết:

```text
main
 ↓
call graph
 ↓
toàn bộ reachable code
```

---

# 2. Không bắt buộc Whole-Program Optimization

Build mặc định vẫn phải hoạt động:

```text
source
→ object
→ linker
→ executable
```

WPO là một optimization layer.

Không được biến nó thành yêu cầu để chương trình chạy đúng.

---

# 3. Object file phải chứa optimization summary

Mỗi `.axo` object có thể chứa:

```text
.text
.rodata
.data
.bss
.symbols
.relocations
.debug
.axmeta
.opt_summary
```

`opt_summary` có thể chứa:

```text
function size
call edges
inline hints
hot/cold hints
visibility
effects
alias facts
generic instance identity
devirtualization candidates
deadness candidates
```

---

# 4. Không cần giữ toàn bộ IR

Đây là quyết định quan trọng để giảm kích thước artifact.

Không mặc định nhúng toàn bộ:

```text
AST
HIR
MIR
OptIR
MachineIR
```

vào object.

Có thể lưu:

```text
minimal semantic metadata
+
optimization summary
+
optional IR cache
```

IR đầy đủ chỉ lưu khi:

```text
LTO
debug
incremental
developer request
```

---

# 5. Thin-LTO style

Axiom nên có hai chế độ:

```text
LTO
ThinLTO
```

### LTO

Toàn bộ IR cần thiết được đưa vào một optimization graph.

Ưu:

- tối ưu mạnh.

Nhược:

- memory lớn;
- compile/link chậm.

### ThinLTO

Module giữ phần lớn code riêng.

Compiler chỉ trao đổi:

```text
summary
+
selected bodies
```

Ưu:

- nhanh;
- parallel tốt;
- phù hợp project lớn.

---

# 6. Mặc định

Release mặc định:

```text
ThinLTO-like
```

Full LTO:

```text
--lto=full
```

Tiny binary:

```text
--opt=size
--lto=full
```

Không bắt buộc người dùng hiểu chi tiết LTO để sử dụng Axiom.

---

# 7. Call Graph

Compiler xây:

```text
CallGraph
```

Ví dụ:

```text
main
 ├── parse
 │    ├── tokenize
 │    └── decode
 └── render
      ├── draw
      └── present
```

Mỗi node:

```text
FunctionId
```

Mỗi edge:

```text
Direct
Indirect
Virtual
Foreign
Async
Callback
Unknown
```

---

# 8. Reachability

Root ban đầu:

```text
main
```

cộng:

```text
@export
entry point
interrupt
syscall entry
FFI callback
reflection materialized symbol
linker-required symbol
```

Từ root:

```text
DFS/BFS
```

để xác định reachable functions.

---

# 9. Dead Code Elimination ở link time

Ví dụ:

```text
fn foo()
fn bar()
fn debug_helper()
fn unused_algorithm()
```

Nếu chỉ:

```text
main → foo
```

thì:

```text
bar
debug_helper
unused_algorithm
```

không xuất hiện trong executable cuối cùng.

---

# 10. Section-level dead stripping

Không chỉ function.

Một function có thể chứa:

```text
hot path
cold path
error path
```

Compiler có thể tách thành sections.

Ví dụ:

```text
.text.hot
.text
.text.cold
```

Linker loại bỏ phần không reachable khi semantic contract cho phép.

---

# 11. Generic + linker dedup

BOOTSTRAP-095 đã cho phép:

```text
Vec<i32>
```

xuất hiện ở nhiều module.

Linker có thể nhận:

```text
Vec_i32_push_A
Vec_i32_push_B
Vec_i32_push_C
```

và phát hiện cùng semantic/code identity.

Kết quả:

```text
Vec_i32_push
```

duy nhất.

---

# 12. COMDAT/linkonce

Generic instance có thể được phát hành dưới dạng:

```text
COMDAT
```

hoặc cơ chế tương đương trên target.

Linker chọn một implementation hợp lệ.

Điều này đặc biệt quan trọng với:

```text
generic libraries
header-like APIs
inline functions
```

---

# 13. Internalization

Nếu:

```text
foo()
```

không được export và chỉ được dùng trong executable:

compiler có thể chuyển:

```text
public/global
```

thành:

```text
internal/private
```

Sau đó optimizer có thêm quyền:

```text
inline
rename
merge
delete
specialize
```

---

# 14. Public không có nghĩa exported

Axiom đã frozen:

```text
pub
```

khác:

```text
@export
```

Do đó:

```text
pub fn helper()
```

không nhất thiết phải giữ symbol ABI-level trong executable.

Chỉ API package/module semantics mới cần được giữ.

---

# 15. Dynamic linking

Nếu function nằm trong:

```text
shared library
```

thì compiler không được giả định nó chết chỉ vì không thấy caller trong executable.

Các symbol:

```text
exported
externally visible
ABI-required
```

là roots tùy theo linking model.

---

# 16. Symbol visibility

Phân biệt:

```text
source visibility
ABI visibility
linker visibility
runtime lookup visibility
```

Ví dụ:

```text
pub
```

không tự động:

```text
runtime symbol
```

---

# 17. Function merging

Nếu:

```text
foo()
bar()
```

có machine code giống nhau:

```text
foo == bar
```

linker/compiler có thể merge.

Nhưng phải kiểm tra:

```text
function address observability
debug semantics
ABI
unwind info
profiling identity
```

---

# 18. Semantic identity vs code identity

Axiom duy trì:

```text
Semantic Function Identity
        ≠
Machine Code Identity
```

Hai function khác nhau có thể dùng chung code.

Ví dụ:

```text
fn foo() -> i32 { 42 }
fn bar() -> i32 { 42 }
```

machine implementation có thể giống nhau.

Nhưng:

```text
address_of(foo)
address_of(bar)
```

nếu observable và khác nhau theo semantic contract, compiler phải giữ identity.

---

# 19. Constant propagation across modules

Module A:

```text
pub const MAX: i32 = 100;
```

Module B:

```text
if x < MAX { ... }
```

WPO có thể biến thành:

```text
if x < 100
```

và tiếp tục optimize.

---

# 20. Cross-module inlining

Ví dụ:

```text
lib.math::abs()
```

được gọi từ application.

Nếu summary cho thấy function nhỏ:

```text
caller
 ↓
inline abs
```

Không cần runtime call.

---

# 21. Cross-module specialization

Ví dụ:

```text
library:

fn process<T: Numeric>(x: T)
```

application chỉ dùng:

```text
process<f32>
```

WPO có thể specialize dựa trên usage thực tế.

Đây là một trong những điểm Axiom có thể vượt mô hình compilation module độc lập truyền thống.

---

# 22. Devirtualization

Nếu:

```text
dyn Trait
```

thực tế tại một call site chỉ có:

```text
TypeA
```

compiler có thể chứng minh:

```text
dynamic dispatch
→ direct call
```

Sau đó:

```text
direct call
→ inline
```

Nhưng chỉ khi proof đầy đủ.

Không được đoán.

---

# 23. Closed-world assumption

WPO có thể sử dụng:

> **Closed World**

khi compiler biết executable hoàn chỉnh.

Nhưng không dùng closed-world cho:

```text
shared library
plugin ABI
dynamic symbol loading
FFI
```

nếu các thành phần đó có thể cung cấp implementation mới.

---

# 24. Dynamic loading

Ví dụ:

```text
load_library("plugin")
```

làm compiler phải coi symbol lookup là:

```text
External/Unknown
```

Không được xóa implementation chỉ vì call graph static không thấy.

---

# 25. FFI boundary

Foreign function:

```text
extern "C" foo(...)
```

mặc định:

```text
Effect = Foreign
```

và conservative.

Compiler không tự giả định:

```text
pure
noalias
nothrow
noescape
```

nếu contract không cung cấp.

---

# 26. Explicit foreign contracts

Trong tương lai có thể có metadata:

```text
@ffi_contract(
    readonly,
    noescape
)
```

nhưng phải là contract có semantic meaning.

Không được tự suy diễn từ tên hàm.

---

# 27. Effect summary

Mỗi function có thể có summary:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

Đã được thiết kế trong OptIR.

WPO sử dụng summary này.

---

# 28. Ví dụ

```text
fn square(x: i32) -> i32 {
    x * x
}
```

Summary:

```text
Read: x
Write: none
Allocate: no
IO: no
Panic: no
Sync: no
```

Compiler có thể optimize rất mạnh.

---

# 29. Không cần `@pure`

Axiom đã quyết định không đưa:

```text
@pure
```

vào Core v1.

Compiler có thể **suy ra** effect facts từ body.

Điều này tránh programmer phải annotate những thứ compiler có thể chứng minh.

---

# 30. Effect summary không phải effect system

Axiom không biến toàn bộ ngôn ngữ thành:

```text
fn foo() -> T
    requires ...
    effects ...
```

Effect summary chủ yếu là:

```text
compiler internal fact
```

và chỉ trở thành ABI/public contract khi thật sự cần.

---

# 31. Interprocedural Constant Propagation

Ví dụ:

```text
fn get_mode() -> i32 {
    3
}
```

Nếu không có observable side effect:

```text
get_mode()
```

có thể trở thành:

```text
3
```

Sau đó:

```text
if mode == 3
```

có thể được constant-fold.

---

# 32. Dead branch elimination

```text
if false {
    expensive()
}
```

→ branch bị loại.

Nhưng compiler phải preserve:

- comptime diagnostics;
- required initialization;
- observable compile-time effects;
- semantic errors.

Code unreachable runtime không có nghĩa compiler được bỏ qua type-checking.

---

# 33. PGO

Axiom hỗ trợ:

```text
Profile-Guided Optimization
```

Hai phase:

```text
Build instrumented
       ↓
Run representative workload
       ↓
Profile
       ↓
Build optimized
```

Profile có thể chứa:

```text
function hotness
branch probabilities
call frequencies
cache behavior hints
value distributions
```

---

# 34. PGO không thay đổi semantics

Profile chỉ ảnh hưởng:

```text
optimization decisions
```

không ảnh hưởng:

```text
program meaning
```

Nếu profile thiếu hoặc sai:

```text
program vẫn đúng
```

chỉ có thể chạy kém tối ưu hơn.

---

# 35. Value profiling

Ví dụ:

```text
if enum == VariantA
```

profile cho thấy 99% là `VariantA`.

Compiler có thể tạo:

```text
fast path VariantA
slow path others
```

nhưng slow path vẫn phải tồn tại nếu semantic contract yêu cầu.

---

# 36. Indirect call profiling

Ví dụ:

```text
callback(x)
```

PGO có thể phát hiện:

```text
90% → foo
8%  → bar
2%  → baz
```

Compiler có thể tạo:

```text
if target == foo:
    inline/fast path
else:
    indirect call
```

Đây là **guarded devirtualization**.

---

# 37. PGO + generic

Generic:

```text
process<T>()
```

có thể có nhiều specialization.

PGO cho biết:

```text
process<f32> = hot
process<i64> = cold
```

Compiler có thể:

```text
f32 → aggressive optimization
i64 → code-size optimization
```

---

# 38. PGO + binary size

Một function cold:

```text
error_handler()
```

không cần:

```text
inline
unroll
vectorize
```

Có thể outline vào:

```text
.text.cold
```

giảm instruction-cache pressure.

---

# 39. Hot/cold splitting

Compiler có thể tách:

```text
foo()
 ├── hot
 └── cold
```

thành:

```text
foo.hot
foo.cold
```

Cold code đặt xa hot code.

---

# 40. Code layout

Final linker cần tối ưu:

```text
function order
basic block order
hot/cold placement
alignment
branch locality
```

Mục tiêu:

```text
I-cache locality
branch prediction
page locality
binary size
```

---

# 41. Function alignment

Không phải mọi function đều cần:

```text
16/32/64 byte alignment
```

Alignment quá lớn làm binary phình.

Compiler/linker cần cost model.

---

# 42. Identical Code Folding

ICF có thể hoạt động:

```text
safe mode
```

chỉ merge khi function identity không observable.

Hoặc:

```text
aggressive mode
```

nếu profile/ABI cho phép.

Axiom nên tránh các mode làm thay đổi semantic behavior.

---

# 43. Dead data elimination

Không chỉ function.

Có thể loại:

```text
unused const
unused static
unused metadata
unused generic tables
unused reflection metadata
unused panic strings
```

Đặc biệt quan trọng với mục tiêu binary nhỏ.

---

# 44. String pooling

Các string literal giống nhau:

```text
"hello"
"hello"
"hello"
```

có thể share storage.

Nhưng nếu address identity của literal là observable theo contract thì phải bảo toàn semantics tương ứng.

---

# 45. Panic string stripping

Trong:

```text
--profile=tiny
```

nếu panic behavior là:

```text
abort
```

compiler có thể giảm metadata/string nếu semantic profile cho phép.

Ví dụ:

```text
panic("detailed message")
```

không được tự xóa message nếu API/diagnostic contract yêu cầu nó.

Do đó panic profile phải định nghĩa rõ.

---

# 46. Runtime component stripping

Một executable:

```text
không async
không thread
không GPU
không reflection
```

không link:

```text
async runtime
thread runtime
GPU runtime
reflection runtime
```

Đây là ALIB2 đã frozen.

WPO/linker thực hiện việc loại bỏ phần không reachable.

---

# 47. Whole-program runtime minimization

Ví dụ chương trình:

```text
main()
 └── File.read()
```

thì executable có thể chỉ kéo vào:

```text
allocator nếu cần
OS file interface
error handling
required startup
```

không phải toàn bộ Standard Library.

---

# 48. Startup minimization

Hosted:

```text
OS startup
→ Axiom entry
→ main
```

Freestanding:

```text
firmware/bootloader
→ @entry
```

Không link:

```text
C runtime
```

trừ khi programmer explicit yêu cầu.

---

# 49. Whole-program allocation analysis

Nếu:

```text
Vec<T>
```

chỉ sống trong một function và không escape:

compiler có thể:

```text
heap allocation
→ stack
```

hoặc:

```text
stack
→ registers/scalarized
```

nếu semantics cho phép.

---

# 50. Whole-program escape analysis

Các mức:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

đã frozen.

WPO cho phép nhìn xuyên nhiều function:

```text
foo()
 → bar()
   → create Vec
```

Nếu toàn bộ chain không escape:

```text
allocation elimination
```

có thể mạnh hơn local optimization.

---

# 51. Whole-program alias analysis

Nếu compiler chứng minh:

```text
a
```

và:

```text
b
```

không overlap:

```text
NoAlias
```

có thể dùng cho:

```text
vectorization
load/store elimination
reordering
```

Nhưng:

```text
UNKNOWN
```

không được biến thành:

```text
NoAlias
```

chỉ vì optimizer muốn nhanh hơn.

---

# 52. Whole-program lifetime shortening

Ví dụ:

```text
let resource = acquire();
use(resource);
large_unrelated_work();
```

Compiler có thể thấy `resource` không còn dùng sau:

```text
use(resource)
```

và rút ngắn lifetime nếu semantics Drop cho phép.

Điều này đã phù hợp:

```text
AMEM-54
```

---

# 53. Không thay đổi Drop order observable

Dù lifetime có thể shorten:

compiler không được tùy tiện thay đổi observable:

```text
Drop ordering
IO effects
resource release
```

Nếu Drop có side effects, đây là semantic behavior.

---

# 54. Whole-program devirtualization

Nếu:

```text
dyn Trait
```

có call site:

```text
draw(x)
```

và closed-world proof:

```text
only Circle implementation reachable
```

→ direct call.

Nếu plugin ABI có thể thêm implementation:

```text
không được devirtualize
```

trừ khi có explicit sealed contract.

---

# 55. Sealed interfaces

Axiom có thể hỗ trợ compiler concept:

```text
closed trait
```

về sau.

Nhưng không cần thêm syntax v1 nếu compiler có thể suy ra closed-world từ module/package visibility.

---

# 56. Async WPO

Compiler có thể:

```text
inline async fn
```

sau đó:

```text
remove unnecessary Future states
```

và:

```text
fuse await chains
```

nếu semantics cho phép.

Đã có:

```text
AwaitFusion
FutureInlining
StateFieldElision
```

từ BOOTSTRAP-038.

---

# 57. Concurrency WPO

Compiler không được tự động loại bỏ:

```text
Atomic
Mutex
Channel
Fence
```

chỉ vì local analysis không thấy vấn đề.

Synchronization semantics là observable.

Nhưng có thể optimize:

```text
uncontended fast path
lock elision
atomic instruction selection
```

khi proof hợp lệ.

---

# 58. Atomic optimization

Ví dụ:

```text
Atomic::load(Relaxed)
```

không thể biến thành:

```text
ordinary load
```

chỉ vì compiler thấy một thread.

Có thể tối ưu instruction theo target nếu vẫn giữ đúng memory-order semantics.

---

# 59. Volatile

Volatile luôn được xem là observable machine operation.

Không:

```text
DCE
CSE
hoist
merge
```

theo cách phá semantics.

Volatile ≠ Atomic.

---

# 60. GPU WPO

Host:

```text
launch(kernel)
```

Device:

```text
kernel
```

có thể tối ưu riêng.

Nhưng:

```text
host/device boundary
```

là ABI/execution-domain boundary.

Không inline xuyên boundary như function CPU bình thường.

---

# 61. FFI boundary

Mặc định:

```text
FFI = optimization barrier
```

trừ khi compiler có explicit contract.

Điều này bảo vệ:

```text
ABI
aliasing
side effects
exceptions
synchronization
```

---

# 62. Linker architecture

Axiom Linker cuối cùng:

```text
Input Reader
      ↓
Object Graph
      ↓
Symbol Resolver
      ↓
Reachability
      ↓
Generic Dedup
      ↓
Dead Stripping
      ↓
ICF / Merge
      ↓
Section Layout
      ↓
Code Layout
      ↓
Relocation
      ↓
Segment Layout
      ↓
Binary Writer
```

---

# 63. Linker không được hiểu Axiom source semantics

Đây là phân chia rất quan trọng.

Compiler quyết định:

```text
semantic optimization
generic specialization
alias facts
effect facts
```

Linker xử lý:

```text
symbols
sections
relocations
layout
binary format
```

Không để linker tự "đoán" ownership hay type semantics.

---

# 64. Axiom Object Graph

Mỗi object cung cấp:

```text
symbols
references
sections
relocations
metadata
optimization summaries
```

Linker xây:

```text
ObjectGraph
```

và tính reachable graph.

---

# 65. Reproducible linking

Cùng:

```text
objects
link options
target
compiler version
```

phải tạo binary deterministic.

Không phụ thuộc:

```text
thread scheduling
hash map iteration
filesystem ordering
```

---

# 66. Parallel linking

Có thể parallel:

```text
symbol processing
relocation preparation
section compression
debug processing
code layout analysis
```

nhưng final output phải deterministic.

---

# 67. Binary size accounting

Axiom nên có:

```text
axiom size
```

hoặc:

```text
axiom build --explain-size
```

Output:

```text
.text             142 KB
.rodata            31 KB
.data               8 KB
.runtime            4 KB
.generic            9 KB
.debug             0 KB
```

và:

```text
largest functions
largest generic families
largest data
unused candidates
```

Điều này cực kỳ hữu ích cho AI agent.

---

# 68. Optimization explanation

Tương tự:

```text
axiom explain-opt foo
```

có thể trả:

```text
foo:
  inlined: bar
  vectorized: loop#2
  bounds-checks removed: 4
  allocation eliminated: 1
  alias proof: a != b
  devirtualized: Trait::method → Type::method
```

Không phải để programmer bắt buộc dùng, mà để debug/compiler tooling/AI.

---

# 69. PGO profile identity

Profile phải gắn với:

```text
target
compiler semantic version
optimization configuration
binary/function identity
```

Không áp profile của binary hoàn toàn khác vào một cách im lặng.

---

# 70. Profile mismatch

Nếu source thay đổi lớn:

```text
profile stale
```

compiler:

```text
ignore
degrade
or warn
```

không được tạo binary sai.

---

# 71. PGO reproducibility

Build không có profile:

```text
deterministic
```

Build có profile:

```text
deterministic given profile
```

Profile itself là build input.

---

# 72. Optimization cache

Cache keys cần bao gồm:

```text
semantic fingerprint
target
CPU features
optimization profile
PGO profile identity
LTO mode
compiler semantic version
```

---

# 73. CPU feature specialization

Ví dụ:

```text
generic binary
```

có thể có:

```text
baseline
AVX2
AVX-512
ARM NEON
SVE
```

Nhưng không được đưa CPU-specific instruction vào binary nếu target contract không cho phép.

Có thể:

```text
dispatch at startup
```

nếu programmer/library yêu cầu multi-versioning.

---

# 74. Function multiversioning

Một API:

```text
dot()
```

có thể có:

```text
dot_scalar
dot_avx2
dot_avx512
```

với dispatcher:

```text
CPU feature detection
→ appropriate implementation
```

Đây là library/compiler optimization, không phải dynamic dispatch object model.

---

# 75. Binary size vs performance

Axiom không có nguyên tắc:

> "luôn tối ưu tốc độ".

Thay vào đó:

```text
correctness
→ semantics
→ optimization profile
→ cost model
```

`--opt=speed` và `--opt=size` có thể tạo code khác nhau.

---

# 76. Tiny binary strategy

Profile `tiny` ưu tiên:

```text
dead stripping
function merging
generic sharing
outlining
no unnecessary inline
runtime stripping
metadata stripping
section GC
string dedup
compact code layout
```

---

# 77. Speed strategy

Profile `speed` ưu tiên:

```text
inlining
specialization
vectorization
PGO
devirtualization
loop optimization
hot code layout
function cloning
```

Có thể chấp nhận binary lớn hơn.

---

# 78. Balanced strategy

Default release:

```text
speed + reasonable size
```

Không cực đoan theo một phía.

---

# 79. Debug không được biến semantics thành khác biệt

Debug/release có thể khác:

```text
optimization
layout
code size
```

nhưng không khác:

```text
ownership semantics
Drop semantics
overflow semantics
panic semantics
atomic semantics
FFI semantics
```

trừ khi profile explicitly thay đổi semantic policy — khi đó phải là một build contract rõ ràng.

---

# 80. Frozen invariants

### Link-time

**ALTO-20 — Link-Time Optimization Is Optional**

**ALTO-21 — Link-Time Optimization Must Preserve Language Semantics**

**ALTO-22 — Linker Operates On Explicit Object Contracts**

**ALTO-23 — Linker Does Not Infer Source Ownership Semantics**

**ALTO-24 — Whole-Program Optimization Requires A Closed-World Contract**

---

### Reachability

**ALTO-25 — Executable Roots Define Initial Reachability**

**ALTO-26 — Unreachable Runtime Code May Be Removed**

**ALTO-27 — Exported ABI Symbols Are Reachability Roots**

**ALTO-28 — Dynamic Lookup Symbols Are Conservative Roots**

**ALTO-29 — FFI Boundaries Are Conservative By Default**

---

### Generic

**ALTO-30 — Generic Instances May Be Deduplicated At Link Time**

**ALTO-31 — Generic Deduplication Must Preserve ABI**

**ALTO-32 — Generic Deduplication Must Preserve Observable Identity**

**ALTO-33 — Generic Code Sharing May Occur Across Modules**

---

### Optimization

**ALTO-34 — Cross-Module Inlining Is Permitted**

**ALTO-35 — Cross-Module Constant Propagation Is Permitted**

**ALTO-36 — Cross-Module Devirtualization Requires Proof**

**ALTO-37 — Cross-Module Escape Analysis Is Permitted**

**ALTO-38 — Cross-Module Alias Analysis Is Permitted**

**ALTO-39 — Unknown Alias Information Must Not Become NoAlias Without Proof**

**ALTO-40 — Synchronization Semantics Must Be Preserved**

**ALTO-41 — Volatile Operations Remain Observable**

---

### PGO

**ALTO-42 — PGO Changes Optimization Decisions, Not Program Semantics**

**ALTO-43 — PGO Profile Is A Build Input**

**ALTO-44 — Stale Profiles Must Not Produce Incorrect Semantics**

**ALTO-45 — PGO Builds Are Deterministic Given Their Profile**

---

### Binary size

**ALTO-46 — Dead Code Elimination Is Mandatory Where Reachability Proves Deadness**

**ALTO-47 — Dead Data Elimination Is Permitted**

**ALTO-48 — Function Merging Is Permitted**

**ALTO-49 — Identical Code Folding Must Respect Observable Identity**

**ALTO-50 — Runtime Components Must Be Linkable Independently**

**ALTO-51 — Unused Runtime Components Must Not Be Required By The Executable**

---

### Determinism

**ALTO-52 — Parallel Optimization Must Be Semantically Equivalent To Serial Optimization**

**ALTO-53 — Reproducible Linking Must Not Depend On Hash Iteration Order**

**ALTO-54 — Optimization Cache Identity Must Include Relevant Build Inputs**

---

### Profiles

**ALTO-55 — Optimization Profiles May Trade Code Size Against Performance**

**ALTO-56 — Tiny Profile Must Prefer Code Sharing And Dead Stripping**

**ALTO-57 — Speed Profile May Prefer Specialization And Inlining**

**ALTO-58 — Debug And Release Must Preserve Core Language Semantics**

---

# 81. Kiến trúc Axiom hiện đạt đến đâu?

Sau 096, pipeline đã khá hoàn chỉnh:

```text
                    AXIOM SOURCE
                         │
                         ▼
              ┌──────────────────┐
              │ Parser / Resolver│
              └────────┬─────────┘
                       ▼
                      HIR
                       │
                       ▼
                 Typed HIR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Traits       Generic      Comptime
       Solver       Engine       Evaluation
          │            │            │
          └────────────┼────────────┘
                       ▼
                      MIR
                       │
                       ▼
              Safety Verification
                       │
                       ▼
                    OptIR
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Alias/Range      Escape        Effect
   Analysis         Analysis      Analysis
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Local Optimization
                       │
                       ▼
               Generic Code Sharing
                       │
                       ▼
                 ABI Lowering
                       │
                       ▼
                   Axiom LIR
                       │
                       ▼
                 Machine IR
                       │
                       ▼
               Object Generation
                       │
              ┌────────┴────────┐
              ▼                 ▼
          Object Graph       PGO Data
              │
              ▼
        Whole Program Graph
              │
       ┌──────┼───────┐
       ▼      ▼       ▼
      LTO    DCE     ICF
       │      │       │
       └──────┼───────┘
              ▼
        Code/Data Layout
              │
              ▼
           Relocation
              │
              ▼
       PE / ELF / Mach-O
           / WASM
```

Điểm quan trọng: **linker của Axiom không còn chỉ là "ghép object".** Nó trở thành một phần của optimization pipeline, nhưng vẫn giữ ranh giới rất rõ giữa **compiler semantic knowledge** và **linker binary knowledge**.

---

# 82. Một quyết định kiến trúc quan trọng đã được chốt

Axiom sẽ không cố tạo ra một "siêu compiler pass" duy nhất.

Thay vào đó:

```text
CompilerDB
    │
    ├── Semantic facts
    ├── Generic instances
    ├── Ownership facts
    ├── Capability facts
    ├── Alias facts
    ├── Effect summaries
    ├── Escape facts
    ├── Layout
    ├── ABI
    └── Optimization summaries
              │
              ▼
         Linker/WPO
```

Điều này rất phù hợp với mục tiêu **AI-friendly compiler**: mỗi quyết định tối ưu đều có thể truy vấn và giải thích thay vì compiler trở thành một khối opaque.

---

# BOOTSTRAP-097 — Axiom Build System, Package Graph & Reproducible Native Builds

Task tiếp theo sẽ khóa phần còn thiếu giữa **compiler/linker** và **project thực tế**:

```text
package
module
workspace
dependency
version
feature
target
cross compilation
build script
comptime
generated source
native libraries
static/shared linking
incremental build
remote/local cache
reproducibility
hermetic build
```

Đặc biệt sẽ giải quyết một vấn đề rất quan trọng đối với mục tiêu của Axiom:

> **Một project lớn có hàng nghìn module/package thì làm thế nào build song song, incremental, offline, deterministic, cross-platform mà không biến build system thành một hệ thống quá phức tạp?**