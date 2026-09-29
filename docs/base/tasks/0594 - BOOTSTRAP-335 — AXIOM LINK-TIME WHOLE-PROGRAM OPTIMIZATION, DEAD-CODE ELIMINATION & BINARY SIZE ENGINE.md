# BOOTSTRAP-335 — AXIOM LINK-TIME WHOLE-PROGRAM OPTIMIZATION, DEAD-CODE ELIMINATION & BINARY SIZE ENGINE

Sau 334, Axiom đã có scheduler đủ mạnh để thực thi build graph song song/local/remote. Bước tiếp theo hợp lý là hoàn thiện **tầng tối ưu ở biên cuối của chương trình**.

Mục tiêu:

> **Binary cuối cùng chỉ chứa những gì thực sự cần, đồng thời tận dụng toàn bộ thông tin mà compiler biết về toàn chương trình.**

Đây là nơi Axiom có thể biến mục tiêu “binary nhỏ như ASM” thành một mục tiêu kỹ thuật thực tế hơn.

---

## 1. Vấn đề

Trong compilation thông thường:

```text
source
  ↓
module
  ↓
object
  ↓
link
  ↓
binary
```

Mỗi object thường phải bảo tồn khá nhiều thứ vì compiler không biết toàn chương trình.

Axiom có:

- Whole-Program Analysis
- `.axif`
- Semantic summaries
- ABI contracts
- Component metadata
- Incremental graph
- LTO
- PGO
- Effect analysis
- Escape analysis
- Trait information
- Generic specialization

Vì vậy linker có thể trở thành một **semantic optimization boundary**, thay vì chỉ:

```text
resolve symbols
+ relocate
```

---

# 2. Pipeline mới

```text
Verified MIR
    ↓
Semantic Optimization
    ↓
Code Generation
    ↓
Object Files
    ↓
Link Graph
    ↓
Whole Program Reachability
    ↓
Dead Code Elimination
    ↓
Global Devirtualization
    ↓
Generic Specialization
    ↓
Constant Propagation
    ↓
Section Folding
    ↓
Identical Code Folding
    ↓
Data Elimination
    ↓
Binary Layout Optimization
    ↓
Machine-Level Finalization
    ↓
Executable
```

Không phải tất cả pass đều chạy ở link time.

Một số pass có thể được đẩy lên compiler trước linker nếu thông tin đã đủ.

---

# 3. Root set

DCE phải bắt đầu bằng việc xác định:

```text
ProgramRoots
```

Root có thể là:

```text
@entry
@export
public ABI symbol
FFI callback
dynamic plugin symbol
reflection-reachable declaration
component service
OS-required entry
startup constructor
interrupt handler
GPU kernel entry
```

---

# 4. Không được coi mọi public symbol là root

Ví dụ:

```text
pub fn helper() {}
```

không đồng nghĩa:

```text
helper must be emitted
```

Nếu module/package không export binary symbol và không có dynamic reachability:

```text
helper → removable
```

Điều này rất quan trọng cho binary size.

---

# 5. Reachability graph

Compiler tạo:

```text
ReachabilityGraph
```

Node:

```text
Function
Global
TypeMetadata
VTable
ComptimeArtifact
Resource
Section
Symbol
```

Edge:

```text
DirectCall
IndirectCall
DataReference
VTableReference
FFI
Reflection
ComponentExport
RuntimeRegistration
GPULaunch
Initializer
```

---

# 6. Static reachability

Ví dụ:

```text
main()
 ├── foo()
 │    └── bar()
 └── baz()
```

Nếu:

```text
unused()
```

không có inbound reachable edge:

```text
unused → eliminated
```

---

# 7. Indirect calls

Đây là điểm khó.

```text
f = choose_function()
f(x)
```

Compiler không thể đơn giản coi toàn bộ function set là reachable.

Axiom dùng:

```text
CallTargetSet
```

Ví dụ:

```text
CallTargetSet = {foo, bar}
```

thay vì:

```text
all functions
```

---

# 8. Trait dynamic dispatch

```text
dyn Trait
```

không nên kéo toàn bộ implementation vào binary.

Whole-program analysis tìm:

```text
actual implementations reachable
```

Nếu chỉ có:

```text
impl Renderer for VulkanRenderer
```

thì implementation khác có thể loại bỏ nếu không có dynamic boundary giữ lại.

---

# 9. Dynamic boundary

Nếu component có:

```text
@export
fn create_renderer()
```

compiler không thể loại bỏ implementation mà external code có thể yêu cầu.

Dynamic boundary phải được khai báo:

```text
DynamicReachabilityContract
```

---

# 10. Reflection boundary

Compile-time reflection:

```text
comptime
```

không tự động tạo runtime reachability.

Nhưng:

```text
runtime_reflection
```

có thể.

Ví dụ:

```text
reflect_by_name("Foo")
```

phải tạo metadata/reachability contract.

---

# 11. Runtime registration

Một số API sử dụng registration:

```text
register(Foo)
```

Compiler phải nhận diện registration edge nếu semantic contract khai báo.

Không được DCE một object chỉ vì không có call trực tiếp.

---

# 12. Constructor / initializer

Global initialization:

```text
static x = init()
```

có thể có side effect.

Compiler phân loại:

```text
PureInitializer
EffectfulInitializer
UnknownInitializer
```

Pure initializer không reachable có thể loại.

Effectful initializer phải được bảo toàn nếu root domain yêu cầu.

---

# 13. Effect-aware DCE

Nếu:

```text
fn foo() -> i32 {
    return 10
}
```

và result không dùng:

```text
foo()
```

có thể loại bỏ nếu:

```text
Effects(foo) = Pure
```

Nhưng:

```text
foo() // writes file
```

không được loại.

---

# 14. Effect lattice

Whole-program DCE dùng:

```text
Pure
ReadOnly
LocalMutation
Allocation
Synchronization
IO
Foreign
Panic
Uncertain
```

Một node chỉ được loại khi compiler chứng minh side effect không observable.

---

# 15. Observable behavior

Axiom không được tối ưu dựa trên:

> “Có vẻ như không ai quan tâm.”

Phải chứng minh không có observable effect theo language semantics.

Observable có thể gồm:

- output
- file/OS operation
- synchronization
- atomics
- volatile
- FFI
- panic
- process exit
- component interaction
- GPU external effect
- explicitly observable timing semantics nếu API contract yêu cầu

---

# 16. Whole-program constant propagation

Ví dụ:

```text
const ENABLE_LOG = false
```

sau specialization:

```text
if ENABLE_LOG {
    logging()
}
```

→ cả nhánh có thể biến mất.

---

# 17. Cross-module constant propagation

`.axif` phải cho phép compiler biết:

```text
const MAX = 1024
```

nếu constant public semantic contract.

Compiler có thể propagate qua package boundary.

---

# 18. Global function specialization

Ví dụ:

```text
fn process<T: Numeric>(x: T)
```

chương trình chỉ dùng:

```text
process<i32>()
```

thì specialization có thể chỉ giữ:

```text
process_i32
```

nếu ABI/dynamic boundary không yêu cầu generic body.

---

# 19. Generic explosion control

Không được:

```text
N generic instances
→ N copies
```

một cách mù quáng.

Compiler dùng:

```text
SpecializationCostModel
```

để cân bằng:

```text
code size
compile time
performance
```

---

# 20. Generic sharing

Nếu hai instantiation có cùng machine representation:

```text
Foo<i32>
Foo<u32>
```

compiler có thể share code nếu semantics cho phép.

Nhưng signedness không được bỏ qua nếu ảnh hưởng overflow/comparison semantics.

---

# 21. Trait devirtualization

Nếu:

```text
dyn Trait
```

nhưng whole-program chứng minh chỉ có:

```text
ConcreteType
```

thì:

```text
virtual call
```

→

```text
direct call
```

---

# 22. Speculative devirtualization

Có thể tạo:

```text
if type == KnownType
    direct_call
else
    fallback_dynamic_call
```

Chỉ khi runtime type identity contract cho phép.

---

# 23. Vtable elimination

Nếu toàn bộ dynamic dispatch đã được devirtualize:

```text
vtable
```

có thể biến mất.

Điều này giúp:

- binary size
- cache locality
- startup
- indirect branch reduction

---

# 24. Closure elimination

Closure:

```text
fn(x) { x + 1 }
```

nếu không escape có thể:

```text
inline
```

hoặc biến thành ordinary function.

Environment có thể bị scalarize.

---

# 25. Function merging

Hai function machine-equivalent:

```text
foo()
bar()
```

có thể cùng trỏ đến một implementation.

```text
foo ─┐
     ├── shared_body
bar ─┘
```

Đây là:

```text
Identical Code Folding
```

nhưng phải giữ ABI/symbol semantics.

---

# 26. Semantic-equivalent vs byte-identical

Không được merge chỉ vì:

```text
bytes happen to match
```

nếu:

- debug identity
- address identity
- function pointer identity
- exported symbol identity

làm chúng observable.

Compiler phải kiểm tra:

```text
FunctionIdentityObservability
```

---

# 27. Function pointer identity

Nếu Axiom cho phép:

```text
foo == bar
```

thì merge có thể thay đổi semantics.

Vì vậy:

```text
FunctionAddressObservable
```

là một fact.

Nếu không observable:

```text
ICF allowed
```

---

# 28. Data folding

Ví dụ:

```text
const A = "hello"
const B = "hello"
```

có thể share storage nếu immutable và identity không observable.

```text
A ─┐
   ├── "hello"
B ─┘
```

---

# 29. Mutable data không được merge

```text
static mut A
static mut B
```

không thể tự động merge vì:

```text
& A != & B
```

có thể observable trong unsafe/FFI.

---

# 30. Read-only data merging

Các immutable constants có thể merge nếu:

```text
same representation
same alignment
same semantic value
identity not observable
```

---

# 31. String pooling

Compiler có thể pool:

```text
"hello"
"hello"
"hello"
```

thành một immutable storage.

Nhưng nếu ABI yêu cầu mỗi string object có identity riêng:

```text
no merge
```

---

# 32. Section garbage collection

Object writer nên tạo section-level graph:

```text
.text.foo
.text.bar
.rodata.x
.data.y
```

DCE có thể loại bỏ từng section.

---

# 33. Function sections

Axiom compiler nên hỗ trợ:

```text
one logical function → independently discardable code unit
```

để linker có granularity tốt.

---

# 34. Data sections

Tương tự:

```text
global variable
constant
vtable
metadata
registration record
```

được tách đủ nhỏ để DCE.

---

# 35. COMDAT / weak semantics

Target ABI layer phải map Axiom semantic identity sang:

```text
COMDAT
weak
linkonce
private
local
```

nếu target hỗ trợ.

Nhưng đây là representation detail.

---

# 36. Binary size budget

Build profile có thể:

```text
@profile(size)
```

hoặc CLI:

```text
axiom build --opt=size
```

Scheduler/optimizer biết:

```text
SizeBudget
```

---

# 37. Size optimization không được phá correctness

Các lựa chọn:

```text
inline
noinline
merge
specialize
share
```

đều là optimization decisions.

Semantic behavior phải giữ nguyên.

---

# 38. Size vs speed profile

Axiom nên có:

```text
speed
balanced
size
tiny
debug
```

Không phải language semantics.

Chỉ là optimizer policy.

---

# 39. Tiny profile

Mục tiêu:

```text
minimum binary size
```

có thể:

- hạn chế inline
- aggressive DCE
- merge functions
- merge constants
- remove metadata
- minimal runtime
- no unnecessary unwinding
- no unnecessary reflection
- target-specific instruction selection

---

# 40. Runtime trimming

Nếu chương trình chỉ cần:

```text
allocator
```

không link:

```text
network
async
filesystem
reflection
GUI
```

Đây là consequence của runtime component architecture.

---

# 41. Startup trimming

Không cần:

```text
thread runtime
```

→ không include thread initialization.

Không cần:

```text
async
```

→ không include executor.

---

# 42. Metadata stripping

Binary release có thể loại:

```text
source map
debug metadata
AI semantic metadata
internal compiler metadata
```

nhưng giữ metadata cần cho:

- dynamic loading
- ABI
- runtime reflection
- crash diagnostics

nếu contract yêu cầu.

---

# 43. Debug information independence

Debug artifact:

```text
program.debug.axdbg
```

tách khỏi executable nếu target hỗ trợ.

Do đó:

```text
release binary
```

có thể nhỏ mà vẫn giữ debug artifact bên ngoài.

---

# 44. Whole-program ABI reasoning

Compiler có thể biết:

```text
foo()
```

chỉ được gọi nội bộ.

Nếu ABI không observable:

```text
internal calling convention
```

có thể tối ưu.

Ví dụ:

```text
struct 3 fields
```

có thể truyền registers thay vì memory.

---

# 45. Internal ABI vs exported ABI

Đây là ranh giới quan trọng:

```text
Internal
→ optimizer tự do

Stable ABI
→ representation contract cố định
```

Không được áp dụng internal optimization làm thay đổi stable ABI.

---

# 46. Link-time ABI adapter elimination

Nếu:

```text
Axiom internal
→ ABI adapter
→ Axiom internal
```

và compiler chứng minh adapter không cần thiết:

```text
adapter eliminated
```

---

# 47. FFI boundary

Ví dụ:

```text
Axiom → C
```

không được optimize xuyên qua C function tùy tiện.

Nhưng nếu FFI contract có summary:

```text
effects = ReadOnly
noalias
nothrow
```

thì optimizer có thể dùng những facts.

---

# 48. Foreign summaries

`.axif`/FFI metadata có thể chứa:

```text
ForeignSummary {
    effects
    memory_reads
    memory_writes
    noalias
    purity
    may_panic
    may_callback
}
```

Uncertain → conservative.

---

# 49. Component boundary

Dynamic component:

```text
host → component
```

không được whole-program DCE xuyên boundary nếu component có thể được thay thế độc lập.

Nếu component được link statically:

```text
static_component
```

và contract cho phép whole-program optimization:

```text
cross-boundary optimization
```

có thể bật.

---

# 50. Hot reload compatibility

Hot-reloadable function không được merge/eliminate theo cách phá:

```text
reload identity
symbol identity
state migration
```

Optimizer phải nhận:

```text
HotReloadBoundary
```

---

# 51. GPU binary DCE

GPU kernels cũng có reachability:

```text
CPU launch
   ↓
GPU kernel
```

Kernel không được gọi:

```text
→ eliminate
```

Nếu runtime reflection/dispatch có thể gọi kernel:

```text
→ root
```

---

# 52. Multi-target DCE

Một source có:

```text
@cfg(os="windows")
foo()

@cfg(os="linux")
bar()
```

Build Windows:

```text
bar → absent
```

Build Linux:

```text
foo → absent
```

Không để unused target branch lọt vào binary.

---

# 53. LTO modes

```text
None
Thin
Full
Auto
```

### None

Module-local optimization.

### Thin

Summary-based cross-module optimization.

### Full

Whole-program IR.

### Auto

Compiler quyết định dựa trên size/time/resource budget.

---

# 54. Incremental LTO

Không phải thay đổi một function là rebuild toàn bộ chương trình.

Whole-program summaries:

```text
FunctionFingerprint
CallGraphFingerprint
EffectFingerprint
LayoutFingerprint
```

giúp giới hạn invalidation.

---

# 55. PGO integration

PGO cung cấp:

```text
hot
cold
size-critical
branch probability
call frequency
```

Dùng để quyết định:

```text
inline
clone
merge
specialize
layout
```

Không thay đổi semantics.

---

# 56. Binary layout optimization

Sau DCE:

```text
hot code
cold code
startup code
rare code
```

có thể được nhóm.

Mục tiêu:

```text
instruction cache
I-TLB
page locality
startup
```

---

# 57. Function ordering

PGO:

```text
main
 ↓
foo
 ↓
bar
```

thì layout có thể đặt chúng gần nhau.

Cold functions đưa sang cold section.

---

# 58. Page-aware layout

Binary size không chỉ là byte count.

Có:

```text
file size
mapped size
text pages
rodata pages
startup working set
```

Optimizer nên có nhiều metrics.

---

# 59. Deployment profiles

Ví dụ:

```text
TinyBinary
FastStartup
MaxThroughput
LowMemory
Embedded
Mobile
Server
```

Optimizer chọn policy phù hợp.

---

# 60. Final Binary Analyzer

Axiom nên có:

```text
axiom size
axiom size --why
axiom size --diff old.axbin new.axbin
```

Output:

```text
.text       812 KB
.rodata     120 KB
.data        21 KB
.runtime     32 KB
.metadata     4 KB
```

---

# 61. “Why is this here?”

Đây là tính năng rất hữu ích.

Ví dụ:

```text
axiom size --why FooRenderer
```

Compiler trả:

```text
FooRenderer
  ← vtable Renderer
  ← dynamic dispatch site #42
  ← exported component service
```

Hoặc:

```text
logging
  ← RuntimeInit
  ← @runtime(log)
```

---

# 62. “Why wasn't this eliminated?”

Ví dụ:

```text
axiom optimize --why-not-remove foo
```

Compiler:

```text
foo cannot be removed because:

ROOT:
    @export

or:

EFFECT:
    ForeignCall

or:

DYNAMIC:
    reachable through ServiceRegistry
```

Đây là nền tảng rất tốt cho AI tooling.

---

# 63. Binary provenance

Mỗi symbol/section cuối cùng có thể truy ngược:

```text
BinarySection
 → MachineFunction
 → MIR Function
 → HIR Declaration
 → SourceSpan
 → Package
```

---

# 64. AI-friendly binary explanation

Compiler có thể xuất JSON:

```text
{
  "symbol": "Foo::bar",
  "size": 184,
  "reachable_from": ["main"],
  "effects": ["ReadMemory"],
  "specialized": true,
  "inlined": false,
  "reason_retained": "direct-call"
}
```

AI agent có thể tự phân tích binary.

---

# 65. CompilerDB additions

```text
WholeProgramDB
ReachabilityDB
CallGraphDB
RootSetDB
DceDB
DevirtualizationDB
SpecializationDB
CodeFoldingDB
DataFoldingDB
SectionGraphDB
BinaryLayoutDB
SizeAnalysisDB
BinaryProvenanceDB
```

---

# 66. APIs

```text
compute_program_roots()

build_reachability_graph()
compute_call_targets()

run_whole_program_dce()

devirtualize_calls()
specialize_generics()

fold_identical_functions()
fold_readonly_data()

eliminate_unused_metadata()
trim_runtime()

optimize_binary_layout()

analyze_binary_size()
explain_symbol_reachability()
explain_retained_code()

compare_binary_size()
generate_size_report()
```

---

# 67. Implementation tree

```text
compiler/
└── whole_program/
    ├── roots/
    ├── reachability/
    ├── callgraph/
    ├── indirect_calls/
    ├── devirtualization/
    ├── specialization/
    ├── dce/
    ├── data_dce/
    ├── code_folding/
    ├── runtime_trim/
    ├── section_gc/
    ├── layout/
    ├── pgo/
    ├── size/
    ├── provenance/
    └── explain/
```

---

# 68. Invariants

```text
AWP-01
Every retained binary entity must have a valid reachability reason.

AWP-02
Every removed entity must be proven semantically unreachable or unobservable.

AWP-03
Dynamic boundaries must conservatively define reachable entities.

AWP-04
FFI boundaries must be treated according to their explicit contracts.

AWP-05
Unknown foreign effects prevent unsafe elimination.

AWP-06
Reflection reachability must be explicit.

AWP-07
Function merging must preserve observable function identity.

AWP-08
Data merging must preserve observable storage identity.

AWP-09
Stable ABI boundaries must never be changed by internal optimization.

AWP-10
Hot-reload boundaries must preserve component identity and lifecycle contracts.

AWP-11
Generic specialization must preserve generic semantics.

AWP-12
Devirtualization must preserve dynamic dispatch semantics.

AWP-13
Runtime trimming must preserve required runtime services.

AWP-14
GPU reachability must account for host/device launch paths.

AWP-15
Target-specific elimination must occur only after target configuration is semantically resolved.

AWP-16
PGO information may influence optimization but never semantic validity.

AWP-17
Optimization profiles may change code generation but never language semantics.

AWP-18
Binary layout optimization must preserve ABI and relocation correctness.

AWP-19
Debug/source provenance must remain valid for retained entities.

AWP-20
Size optimization must not introduce undefined behavior.

AWP-21
Incremental whole-program optimization must produce semantically equivalent results to clean optimization.

AWP-22
Cache reuse must require valid semantic fingerprints.

AWP-23
Remote and local whole-program optimization must be semantically equivalent.

AWP-24
Every optimization transformation must have a legality proof.

AWP-25
The final executable must remain traceable to verified compiler artifacts.
```

---

# 69. Definition of Done

BOOTSTRAP-335 hoàn thành khi Axiom có:

- Whole-program reachability graph.
- Root discovery.
- Static call graph.
- Indirect-call target analysis.
- Trait devirtualization.
- Dynamic dispatch pruning.
- Whole-program DCE.
- Data DCE.
- Effect-aware elimination.
- Generic specialization.
- Generic code sharing.
- Function merging.
- Read-only data merging.
- String pooling.
- Section-level garbage collection.
- Runtime trimming.
- Reflection reachability.
- FFI reachability.
- Component reachability.
- Hot-reload protection.
- GPU kernel reachability.
- Cross-target elimination.
- Incremental LTO.
- Thin/Full/Auto LTO.
- PGO integration.
- Function layout optimization.
- Binary page locality optimization.
- Size profiles.
- Binary-size analyzer.
- “Why retained?” diagnostics.
- “Why not eliminated?” diagnostics.
- Binary provenance.
- AI-readable binary reports.
- ABI firewall integration.
- `.axif` summary integration.
- Incremental build integration.
- Remote build integration.
- Artifact system integration.

## Nguyên tắc khóa của 335

> **Linker của Axiom không chỉ nối các object file. Nó là điểm cuối nơi compiler có thể chứng minh rằng phần lớn chương trình không cần tồn tại trong binary cuối cùng.**

Và đặc biệt:

> **“Không được gọi trực tiếp” không đồng nghĩa với “có thể xóa”; chỉ được xóa khi compiler chứng minh nó không reachable và không có observable effect qua bất kỳ boundary nào.**

Đây là điều giúp Axiom vừa hướng tới **binary cực nhỏ**, vừa tránh kiểu “size optimization bằng cách đoán”.