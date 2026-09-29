# BOOTSTRAP-267 — AXIOM LINK-TIME CODE GENERATION, LTO, WHOLE-PROGRAM OPTIMIZATION & BINARY SIZE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là task rất quan trọng với mục tiêu của Axiom: **không chỉ code chạy nhanh, mà binary cũng phải nhỏ và không mang theo những thứ chương trình không sử dụng.**

Nguyên tắc trung tâm:

> **Linker không chỉ nối object files. Trong Axiom, link-time là một semantic/codegen optimization boundary có thể nhìn thấy toàn chương trình, nhưng không được thay đổi semantics.**

---

# 1. Vấn đề của compilation truyền thống

Nếu compile độc lập:

```text
A.ax → A.o
B.ax → B.o
C.ax → C.o
```

compiler thường không biết:

```text
A thực sự gọi gì từ B?
B type nào thực sự được dùng?
generic instance nào cần?
trait implementation nào thực sự reachable?
runtime component nào cần?
```

LTO giải quyết vấn đề này.

---

# 2. Axiom không nên chọn một kiểu LTO duy nhất

Cần hỗ trợ nhiều mức:

```text
NoLTO
ThinLTO
FullLTO
WholeProgram
IncrementalLTO
```

---

# 3. NoLTO

Mỗi compilation unit tối ưu chủ yếu độc lập.

Ưu điểm:

- build nhanh
- parallel cao
- incremental tốt

Nhược:

- ít cross-module optimization.

---

# 4. ThinLTO

Trao đổi:

```text
OptimizationSummary
```

thay vì toàn bộ IR.

Cho phép:

```text
cross-module inlining
devirtualization
dead code analysis
specialization
```

với chi phí bộ nhớ thấp hơn Full LTO.

---

# 5. FullLTO

Merge semantic/codegen representation vào một optimization graph lớn hơn.

Cho phép tối ưu mạnh hơn.

---

# 6. WholeProgram

Khi compiler biết executable boundary:

```text
entry points
exports
FFI
reflection
dynamic loading
runtime roots
```

có thể xác định reachable program graph rất chính xác.

---

# 7. Không được hiểu WholeProgram = "xóa tất cả thứ không thấy được"

Có những thứ reachable gián tiếp:

```text
@export
FFI
dynamic symbol
reflection
plugin registration
startup hook
signal callback
OS entry point
```

---

# 8. Vì vậy cần Root Model

Compiler tạo:

```text
RootSet
```

gồm:

```text
ProgramEntry
ExplicitExport
FFIExport
DynamicLoadRoot
ReflectionRoot
RuntimeRoot
StartupRoot
TLSRoot
PlatformRoot
KeepSymbol
```

---

# 9. Reachability graph

```text id="s4w2hz"
RootSet
   │
   ▼
Declaration Graph
   │
   ├── Function
   ├── Type
   ├── Trait
   ├── Generic Instance
   ├── Static
   ├── Resource
   └── Metadata
```

---

# 10. Reachability không chỉ là call graph

Ví dụ:

```text
static TABLE
```

có thể reference:

```text
function pointers
```

thì function đó reachable dù không có direct call.

---

# 11. Các edge cần tracking

```text
Call
Reference
AddressTaken
FunctionPointer
VTable
GenericInstance
StaticData
TypeMetadata
Reflection
FFI
Export
Runtime
ComptimeGenerated
```

---

# 12. Dynamic dispatch

```text
dyn Trait
```

không được làm toàn bộ implementations reachable nếu compiler có thể chứng minh tập concrete types nhỏ hơn.

---

# 13. Nhưng nếu runtime discovery thật sự xảy ra

Ví dụ plugin:

```text
load_library(...)
lookup_symbol(...)
```

compiler phải bảo thủ theo contract.

---

# 14. Reflection

Nếu runtime reflection yêu cầu:

```text
Type<T>
```

thì metadata/type implementation tương ứng trở thành root.

---

# 15. Không dùng reflection → không có reflection runtime

Đây là một nguồn binary-size saving quan trọng.

---

# 16. Runtime composition + LTO

Axiom runtime:

```text
Allocator
Panic
Thread
TLS
Async
IO
Reflection
Unicode
...
```

đã là modular.

LTO có thể tiếp tục loại bỏ phần không reachable.

---

# 17. Ví dụ

Program:

```text
fn main() {
    println("hello")
}
```

không dùng:

```text
network
async
GPU
reflection
database
crypto
```

thì các subsystem đó không được kéo vào binary chỉ vì standard library package tồn tại.

---

# 18. Static library

`.axlib` không đồng nghĩa:

> toàn bộ library phải vào executable.

Chỉ reachable artifacts được materialize/link.

---

# 19. Generic code

Đây là nơi Axiom có lợi thế lớn.

Ví dụ:

```text
Vec<i32>
Vec<f64>
Vec<String>
```

compiler chỉ instantiate những specialization thực sự reachable.

---

# 20. Nhưng monomorphization hoàn toàn có thể làm binary phình

Do đó cần:

```text
SpecializationPolicy
```

---

# 21. Ba lựa chọn

```text
Specialize
Share
Hybrid
```

---

# 22. Specialize

Nếu:

```text
T = i32
```

compiler tạo implementation chuyên biệt.

Có thể tối ưu mạnh:

```text
SIMD
constant propagation
inlining
layout
```

---

# 23. Share

Nếu hai generic instances có code machine tương đương hoặc đủ tương tự:

```text
Vec<A>
Vec<B>
```

có thể dùng shared implementation.

---

# 24. Hybrid

Default nên là:

```text
specialize when profitable
otherwise share
```

---

# 25. Không được dùng code-size heuristic làm thay đổi semantics

Chỉ thay đổi physical implementation.

---

# 26. Cross-module inlining

Compiler có thể inline:

```text
module_a::foo()
```

vào:

```text
module_b::bar()
```

nếu:

```text
visibility/ABI/semantic constraints
```

cho phép.

---

# 27. Stable ABI boundary

Nếu function là:

```text
@abi(stable)
```

compiler không được phá contract bằng internal inlining không phù hợp.

Nhưng có thể dùng:

```text
ABI adapter
```

hoặc optimization phía caller nếu contract cho phép.

---

# 28. Internal function

Không stable ABI:

```text
private
```

có thể inline tự do.

---

# 29. `pub` không đồng nghĩa "không được inline"

Điểm này đã frozen ở API/ABI architecture.

---

# 30. Export boundary

```text
@export
fn foo(...)
```

là external root.

Compiler không được dead-strip symbol đó chỉ vì không thấy local caller.

---

# 31. Address-taken

Nếu:

```text
let f = foo
```

thì `foo` reachable.

---

# 32. Nhưng address-taking không nhất thiết ngăn function optimization

Compiler vẫn có thể:

```text
devirtualize
specialize
clone
fold
```

nếu function identity/ABI semantics cho phép.

---

# 33. Function cloning

Ví dụ:

```text
foo(x)
```

có một hot callsite với:

```text
x known range
```

compiler có thể tạo:

```text
foo.specialized
foo.generic
```

---

# 34. Clone legality

Clone phải giữ:

```text
effects
panic behavior
atomic semantics
volatile
FFI
resource effects
```

---

# 35. Whole-program effect analysis

LTO có thể tổng hợp:

```text
EffectInfo
```

theo call graph.

Ví dụ function:

```text
pure
```

nếu compiler chứng minh không có observable effect.

---

# 36. Nhưng không được tự coi function là pure chỉ vì hiện tại không thấy IO

Foreign call:

```text
extern "C"
```

phải theo FFI contract.

---

# 37. Unknown foreign function

Mặc định conservative:

```text
Read
Write
External
Unknown
```

tùy contract.

---

# 38. Global analysis

LTO có thể phát hiện:

```text
static x
```

chỉ được đọc bởi một function.

Có thể:

```text
constant-fold
private
merge
eliminate
```

nếu không có observable identity.

---

# 39. Address-observable static

Nếu:

```text
address_of(static_x)
```

được dùng và identity observable:

```text
static_x
```

không được scalarize thành giá trị vô danh.

---

# 40. Dead static elimination

Static không reachable và không externally visible có thể loại bỏ.

---

# 41. TLS

TLS cũng có root analysis.

Nếu TLS declaration không reachable:

```text
TLS storage
```

không cần đưa vào binary.

---

# 42. Startup hooks

Startup root phải explicit.

Không được có hidden constructor graph.

---

# 43. Drop at program exit

Do Axiom không bắt buộc static destructor chain:

binary không tự động phải kéo cả destruction runtime vào.

---

# 44. Section GC

Mỗi code/data unit nên hỗ trợ:

```text
function sections
data sections
metadata sections
```

để linker dead-strip chính xác.

---

# 45. Function Sections

Conceptual:

```text
.text.foo
.text.bar
```

---

# 46. Data Sections

```text
.rodata.foo
.data.foo
.bss.foo
```

---

# 47. Metadata Sections

```text
.axmeta
.debug
.unwind
```

có root policy riêng.

---

# 48. Không được dead-strip debug metadata đang được tham chiếu bởi debugger artifact nếu build profile yêu cầu.

---

# 49. ICF — Identical Code Folding

Hai functions:

```text
foo()
bar()
```

nếu machine implementation giống hệt và observable identity không yêu cầu khác biệt:

có thể merge.

---

# 50. Nhưng function address có thể observable

Nếu:

```text
foo != bar
```

hoặc địa chỉ được expose theo semantics/ABI:

không được merge nếu việc merge làm thay đổi observable identity.

---

# 51. Vì vậy ICF cần Identity Analysis

Không chỉ byte comparison.

---

# 52. Data merging

Tương tự:

```text
const A = "hello"
const B = "hello"
```

có thể share storage nếu semantic address identity không observable.

---

# 53. Nếu address observable

Không được merge nếu semantics yêu cầu distinct identity.

---

# 54. String literals

`String`/`Str` semantics phải tách:

```text
value equality
storage identity
```

như memory model đã định nghĩa.

---

# 55. Constant folding toàn chương trình

LTO có thể truyền:

```text
const
comptime
known values
```

qua module boundaries.

---

# 56. Comptime-generated code

Nếu generated code không reachable:

không materialize machine code.

---

# 57. Compile-time execution không đồng nghĩa runtime dependency.

---

# 58. Trait devirtualization

Ví dụ:

```text
fn process<T: Draw>(x: T)
```

nếu whole-program chứng minh:

```text
T = Circle
```

có thể bỏ dynamic/general path.

---

# 59. `dyn Trait`

Nếu concrete implementation duy nhất reachable:

```text
dyn dispatch
```

có thể devirtualize.

Nhưng chỉ khi compiler chứng minh không có externally supplied implementation.

---

# 60. Plugin boundary

Nếu plugin ABI cho phép implementation xuất hiện runtime:

không devirtualize xuyên boundary.

---

# 61. Vtable elimination

Nếu `dyn Trait` không thực sự cần dynamic dispatch sau analysis:

```text
vtable
```

có thể eliminate.

---

# 62. Nhưng không được thay đổi runtime type identity nếu application quan sát identity.

---

# 63. Generic metadata

Không phải generic type nào cũng cần runtime metadata.

Nếu runtime reflection không dùng:

```text
Type<T>
```

không cần materialize.

---

# 64. Binary size pipeline

Đề xuất:

```text id="i6x8f4"
Reachability
    ↓
Generic Pruning
    ↓
Trait/VTable Pruning
    ↓
Cross-module Constant Propagation
    ↓
Specialization
    ↓
Inlining
    ↓
Devirtualization
    ↓
DCE
    ↓
Global DCE
    ↓
Section GC
    ↓
ICF
    ↓
Data Merging
    ↓
Runtime Component Pruning
    ↓
LTO
    ↓
Link
```

Thực tế một số bước sẽ interleave/fixed-point thay vì pipeline tuyến tính.

---

# 65. Fixed-point optimization

Đây là điểm quan trọng.

Ví dụ:

```text
devirtualization
```

→ function trở thành direct call

→ function mới trở nên inlineable

→ inlining

→ code path unreachable

→ DCE

→ runtime component không còn cần.

Vì vậy compiler cần iterative optimization.

---

# 66. Optimization graph

Không nên hard-code một pipeline duy nhất.

Dùng:

```text
OptimizationCoordinator
```

để chạy passes tới fixed point hoặc budget.

---

# 67. Nhưng phải có termination guarantee

Mỗi pass phải có:

```text
monotonic progress metric
```

hoặc iteration budget.

---

# 68. Không được optimizer loop vô hạn

---

# 69. ThinLTO summaries

`.axlib` nên chứa:

```text
OptimizationSummary
```

ví dụ:

```text
FunctionSummary {
    size
    hotness
    effects
    calls
    args
    returnFacts
    visibility
    addressTaken
    inlineCost
}
```

---

# 70. Alias summary

Có thể lưu:

```text
AliasSummary
```

nhưng chỉ những facts được compiler chứng minh.

---

# 71. Ownership summary

Ví dụ:

```text
consumes arg0
returns ownership
borrows arg1 temporarily
```

---

# 72. Capability summary

Ví dụ:

```text
READ arg0 region
WRITE arg1 region
```

---

# 73. Effect summary

```text
Read
Write
Allocate
Drop
Atomic
IO
Foreign
Panic
Synchronize
```

---

# 74. Escape summary

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
```

---

# 75. Những summary này cực kỳ có giá trị

Không chỉ cho optimizer mà còn cho:

```text
IDE
AI
binary analyzer
performance tooling
```

---

# 76. Nhưng summary không phải semantic authority

Authority vẫn là:

```text
Verified MIR
```

---

# 77. Summary stale

Nếu source thay đổi:

```text
summary fingerprint mismatch
```

phải invalidate.

---

# 78. SemanticFingerprint

Đã có.

LTO cache key nên bao gồm:

```text
SemanticFingerprint
TargetId
ABI
FeatureSet
CodegenFingerprint
OptimizationProfile
```

---

# 79. CodegenFingerprint

Có thể thay đổi optimization strategy mà không thay đổi language semantics.

---

# 80. Incremental LTO

Nếu module B không thay đổi:

không nhất thiết rebuild toàn bộ B's summaries.

---

# 81. Cache hierarchy

```text
Source Cache
     ↓
Semantic Cache
     ↓
Verified MIR Cache
     ↓
Optimization Summary Cache
     ↓
LTO Cache
     ↓
Object Cache
     ↓
Link Cache
```

---

# 82. Cache invalidation

Phải phân biệt:

```text
source change
semantic change
ABI change
target change
optimization change
link-root change
```

---

# 83. ABI change

Có thể invalidate downstream package consumers.

---

# 84. Private implementation change

Nếu public semantic/ABI contract không đổi, binary consumers có thể không cần recompile trong một số cache/build scenarios.

---

# 85. Stable ABI package

Compiler có thể ship:

```text
stable public ABI
```

và tối ưu implementation độc lập.

---

# 86. LTO qua stable ABI

Không phải lúc nào cũng được.

Compiler có thể dùng:

```text
ABI adapter
```

hoặc optimization contracts.

---

# 87. PGO + LTO

PGO facts:

```text
hot call
cold branch
branch probability
function hotness
```

được đưa vào LTO.

---

# 88. Nhưng PGO không được thay đổi semantics

---

# 89. Profile khác nhau

```text
speed
size
balanced
debug
```

---

# 90. Size profile

`--profile size` ưu tiên:

```text
dead stripping
code sharing
small-function inlining only when profitable
runtime pruning
ICF
data merging
compressed instructions
section GC
```

---

# 91. Speed profile

Có thể ưu tiên:

```text
specialization
aggressive inlining
vectorization
unrolling
PGO
```

và binary lớn hơn.

---

# 92. Size ≠ "minimize every byte"

Ví dụ một optimization làm code nhỏ hơn nhưng chậm đáng kể.

Profile quyết định tradeoff.

---

# 93. Nhưng semantics luôn đứng trên profile.

---

# 94. Tiny binary mode

Có thể có:

```text
--profile tiny
```

để ưu tiên kích thước cực mạnh.

---

# 95. Không nên hứa "kích thước bằng assembly"

Đây là mục tiêu kỹ thuật, không phải semantic guarantee.

Assembly thủ công có thể bỏ qua rất nhiều metadata/runtime requirements mà compiler phải giữ khi semantics yêu cầu.

---

# 96. Runtime-free

Nếu chương trình không cần:

```text
allocator
thread
async
reflection
IO
```

runtime graph có thể thu gọn.

---

# 97. Freestanding

Có thể đạt:

```text
Axiom code
+
minimal startup
```

mà không link standard runtime.

---

# 98. Binary roots

Root chính:

```text
main
```

cùng với:

```text
exports
platform-required symbols
```

---

# 99. Dynamic linking

Nếu dùng dynamic library:

```text
libA
```

thì linker không được giả định toàn bộ `libA` cần thiết nếu platform/object format hỗ trợ symbol-level extraction.

---

# 100. Shared library exports

Ngược lại, public shared library phải giữ exported ABI surface.

---

# 101. Executable vs shared library

Reachability policy khác nhau.

Executable:

```text
closed-world
```

thường mạnh hơn.

Shared library:

```text
open-world
```

phải bảo vệ exported ABI.

---

# 102. Plugin

Plugin ABI:

```text
open-world
```

vì host có thể discover symbols runtime.

---

# 103. Whole-program boundary

Compiler phải biết:

```text
ClosedWorld
OpenWorld
PluginWorld
FFIWorld
```

---

# 104. ClosedWorld

Cho phép aggressive elimination.

---

# 105. OpenWorld

Giữ external ABI contract.

---

# 106. PluginWorld

Giữ:

```text
explicit exported symbols
ABI descriptors
registration roots
```

---

# 107. FFI

Foreign code có thể gọi vào Axiom.

Do đó:

```text
@export
extern
stable ABI
```

là roots.

---

# 108. Reverse FFI

Axiom gọi C không đồng nghĩa toàn bộ C library code reachable.

Object/linker xử lý symbol-level dependency.

---

# 109. Native library

Một số platform library có implicit initialization or linker semantics.

Target linker contract phải mô tả rõ.

---

# 110. Không được xóa symbol chỉ vì Axiom call graph không thấy nó nếu native platform yêu cầu symbol.

---

# 111. Binary layout

Sau LTO:

```text
Code
ROData
Data
BSS
TLS
Metadata
Unwind
Resources
```

được layout.

---

# 112. Code ordering

PGO có thể đặt hot code gần nhau.

---

# 113. Cold splitting

Cold path:

```text
panic
error
rare branch
```

có thể tách khỏi hot code.

---

# 114. Nhưng panic/error semantics không được mất.

---

# 115. Function alignment

Size profile có thể giảm alignment khi ABI cho phép.

---

# 116. Padding optimization

Linker có thể tối ưu section ordering/padding.

---

# 117. Identical constants

ROData merging có thể giảm duplicate data.

---

# 118. String pooling

Có thể share literal storage khi semantic identity cho phép.

---

# 119. Zero-filled data

Global zero data nên dùng:

```text
.bss
```

thay vì lưu toàn zero bytes.

---

# 120. Compression

Executable compression/packing không nên là Core compiler semantic feature.

Có thể là distribution layer.

---

# 121. Link-time dead metadata

Nếu:

```text
reflection = off
debug = off
```

thì:

```text
.axmeta
debug
```

không cần embed.

---

# 122. Debug artifact

Debug info có thể tách:

```text
app
app.debug
```

giữ runtime binary nhỏ.

---

# 123. Semantic metadata

`.axmeta` cũng có thể tách ngoài binary.

---

# 124. Runtime TypeId

Chỉ materialize nếu application yêu cầu runtime reflection/dynamic type identity.

---

# 125. Vtable

Chỉ giữ vtables reachable.

---

# 126. Vtable entry pruning

Nếu ABI/runtime contract cho phép và compiler chứng minh entry không observable, có thể compact.

---

# 127. Stable ABI caution

Stable ABI có thể yêu cầu layout cố định.

Không được áp dụng internal vtable pruning phá contract.

---

# 128. Trait implementation pruning

Nếu:

```text
impl Draw for Circle
```

không reachable:

implementation code/metadata có thể loại bỏ.

---

# 129. Coherence vẫn được kiểm tra trước pruning

Không được pruning trước semantic resolution rồi dùng kết quả đó để thay đổi trait selection.

---

# 130. Important order

```text
Resolve
→ Typecheck
→ Trait solve
→ Verify
→ Determine semantics
→ Reachability
→ Optimize
```

---

# 131. Không được:

```text
Reachability
→ bỏ impl
→ trait solver thấy ít candidate hơn
→ semantics thay đổi
```

---

# 132. Đây là một invariant rất quan trọng.

---

# 133. Comptime declarations

Tương tự:

Generated declaration phải được resolve/typecheck/verify trước.

Sau đó mới prune nếu không reachable.

---

# 134. Optimization proof

Mỗi LTO transform cần:

```text
Preconditions
Transformation
Preserved facts
Invalidated facts
Validation
```

---

# 135. Translation validation

Sau transform quan trọng:

```text
Before semantics
        ↕
After semantics
```

cần validation ở mức phù hợp.

---

# 136. Differential testing

LTO binary phải so với:

```text
reference interpreter
non-LTO build
```

---

# 137. Observable behavior

So sánh:

```text
return
Result
panic
IO
atomic
volatile
sync
FFI
resource effects
termination
```

---

# 138. Không so sánh assembly byte-for-byte

---

# 139. Machine output khác nhau vẫn hợp lệ.

---

# 140. LTO failure

Nếu compiler không chứng minh được:

```text
safe elimination
```

thì giữ code.

Không được đoán.

---

# 141. Unknown root

Nếu:

```text
dynamic symbol
```

không biết:

```text
keep conservatively
```

---

# 142. Binary-size diagnostics

Axiom nên có:

```text
ax size
```

---

# 143. Ví dụ output

```text
Program size: 183 KB

Code:
  91 KB

ROData:
  42 KB

Runtime:
  18 KB

TLS:
   0 KB

Metadata:
   0 KB

Unwind:
   4 KB

Other:
  28 KB
```

---

# 144. Size attribution

Có thể hỏi:

```text
ax size explain foo
```

---

# 145. Compiler trả:

```text
foo
 ├── Vec<i32>
 ├── allocator
 ├── formatting
 └── UTF-8 validation
```

---

# 146. Đây là cực kỳ hữu ích cho AI.

AI không cần đoán:

> "Có vẻ Vec kéo allocator."

Compiler có thể chứng minh dependency graph.

---

# 147. Reverse attribution

```text
ax size why allocator
```

→

```text
allocator
 ├── Vec
 ├── String
 └── Box
```

---

# 148. Unused feature detection

Compiler có thể:

```text
ax unused
```

cho biết:

```text
package dependency reachable = false
feature code reachable = false
runtime component unused
```

---

# 149. Không nhất thiết warning dependency

Package manager và linker là hai tầng khác nhau.

Một package có thể được dependency nhưng code không được link.

---

# 150. Binary budget

Có thể hỗ trợ:

```text
--max-code-size
--max-binary-size
```

nếu vượt:

```text
diagnostic
```

---

# 151. Nhưng compiler không tự phá semantics để đạt budget.

---

# 152. LTO architecture

```text id="xq7s2f"
              Package Graph
                    │
                    ▼
             .axlib / objects
                    │
                    ▼
             LTO Input Graph
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
    Semantics    Summaries    ABI Facts
        │           │            │
        └───────────┼────────────┘
                    ▼
               Root Analysis
                    │
                    ▼
             Reachability Graph
                    │
                    ▼
            Whole Program Opt
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
     Generic      Trait       Runtime
     Pruning      Pruning     Pruning
        │           │            │
        └───────────┼────────────┘
                    ▼
             Cross-module Opt
                    │
                    ▼
                 OptIR
                    │
                    ▼
             ABI / Codegen
                    │
                    ▼
                Linker
```

---

# 153. CompilerDB additions

```text id="w8n2pk"
LtoDB
ReachabilityDB
OptimizationSummaryDB
WholeProgramDB
RootDB
SizeDB
ProfileDB
LinkGraphDB
```

---

# 154. Important distinction

```text
CompilerDB
    semantic authority

LtoDB
    optimization knowledge

LinkGraphDB
    physical/link dependency knowledge
```

---

# 155. LinkGraphDB không được thay thế semantic graph.

---

# 156. Whole-program graph

Nên có:

```text
ProgramGraph {
    nodes
    edges
    roots
    external_boundaries
    dynamic_boundaries
}
```

---

# 157. Node kinds

```text
Function
Static
TypeMetadata
TraitImpl
VTable
GenericInstance
Resource
RuntimeComponent
Section
Symbol
```

---

# 158. Edge kind

```text
DirectCall
IndirectCall
AddressReference
DataReference
TypeMetadata
VTableReference
FFI
Export
Reflection
Runtime
Startup
TLS
DynamicLoad
```

---

# 159. Indirect call

Compiler có thể có:

```text
TargetSet
```

---

# 160. TargetSet

Ví dụ:

```text
call_indirect f
```

có:

```text
{foo, bar}
```

sau analysis.

---

# 161. Empty target set

Nếu compiler chứng minh call unreachable:

có thể eliminate caller path.

---

# 162. Unknown target set

Không được assume empty.

---

# 163. Security boundary

Indirect calls từ untrusted external ABI phải conservative.

---

# 164. Function pointer equality

Nếu language semantics cho phép compare function pointers/identity, optimizer phải bảo toàn.

---

# 165. Nếu function identity không observable trong safe Core, có nhiều freedom hơn.

---

# 166. Address observability

Một trong những nguyên tắc xuyên suốt Axiom:

```text
Physical identity
```

chỉ quan trọng khi semantic contract expose nó.

---

# 167. Tương tự với allocation

Nếu heap allocation không observable:

```text
allocation elimination
```

---

# 168. Nếu address observable:

```text
storage identity
```

có thể trở thành semantic obligation.

---

# 169. Tương tự function.

---

# 170. Tương tự static.

---

# 171. Tương tự data merging.

---

# 172. Đây là một abstraction:

> **Observable identity creates an optimization boundary.**

---

# 173. LTO không được phá observable identity.

---

# 174. Binary-size optimization và ownership

Ownership cho phép compiler biết:

```text
unique owner
```

→ mạnh hơn về aliasing.

---

# 175. Capability

`mut_view`:

```text
exclusive WRITE
```

→ optimizer có thể derive internal `NO_ALIAS` khi proof đủ.

---

# 176. LTO có thể propagate alias facts xuyên module

Nếu summary chứa proof.

---

# 177. Nhưng summary không được tạo `NO_ALIAS` từ UNKNOWN.

---

# 178. Đây là kế thừa trực tiếp từ `AOPT`/`AVERIFY`.

---

# 179. Effect pruning

Nếu compiler chứng minh function:

```text
does not read global
does not write global
does not IO
```

có thể:

```text
CSE
hoist
eliminate
```

tùy result usage.

---

# 180. Pure function

Nếu return value không dùng:

```text
pure foo()
```

có thể eliminate.

---

# 181. Impure function

Không được eliminate chỉ vì return không dùng.

---

# 182. Ví dụ

```text
write_file()
```

return ignored nhưng IO observable.

Không được xóa.

---

# 183. Atomic

```text
atomic_load()
```

không được coi như ordinary load.

---

# 184. Volatile

Không được merge/eliminate như ordinary memory.

---

# 185. Synchronization

Không được reorder qua semantic happens-before boundary nếu observable behavior thay đổi.

---

# 186. FFI

Unknown foreign effects → conservative.

---

# 187. GPU LTO

Có thể:

```text
host LTO
device LTO
```

riêng.

---

# 188. Kernel reachability

Kernel được launch runtime có thể là dynamic root.

Nếu launch target compile-time known:

chỉ kernel đó cần emit.

---

# 189. GPU pipeline cache

Unused shaders/kernel binaries không cần package vào final artifact nếu không reachable.

---

# 190. WASM

WASM module export là root.

Nếu:

```text
export foo
```

thì giữ `foo` dù Axiom source không gọi.

---

# 191. WASM table

Functions referenced by table có reachability edge.

---

# 192. WASM `call_indirect`

Target sets phải conservative theo table initialization.

---

# 193. Component model

Dynamic imports/exports trở thành external boundary.

---

# 194. Linker

Sau LTO vẫn cần linker để:

```text
relocations
sections
imports
exports
TLS
platform ABI
```

---

# 195. Không biến LTO thành linker

Phân tách:

```text
LTO = semantic/codegen optimization
Linker = binary composition/layout
```

---

# 196. Nhưng chúng phối hợp qua:

```text
LinkGraph
```

---

# 197. LTO output

Có thể tạo:

```text
optimized object
```

hoặc trực tiếp:

```text
AxiomObject
```

tùy architecture.

---

# 198. Incremental build

Default nên tránh FullLTO trong dev.

Ví dụ:

```text
dev       → NoLTO/Thin
release   → ThinLTO
speed     → FullLTO + PGO
size      → FullLTO + aggressive stripping
```

---

# 199. Reproducibility

LTO parallelism phải deterministic.

Ví dụ:

```text
module ordering
symbol ordering
hash seeds
optimization tie-breaking
```

không được phụ thuộc thread scheduling.

---

# 200. Randomized optimization

Nếu có heuristic randomness:

reproducible mode phải seed deterministic hoặc disable.

---

# 201. Cache

LTO cache key:

```text
PackageContentHash
DependencySemanticFingerprint
TargetId
ABI
FeatureSet
OptimizationProfile
PGO fingerprint
CompilerSemanticVersion
CompilerCodegenVersion
```

---

# 202. Link root changes

Nếu thêm:

```text
@export foo
```

reachability graph thay đổi.

Phải invalidate affected link/LTO nodes.

---

# 203. Dynamic loading declaration

Nếu thêm dynamic loading:

```text
whole-program assumption
```

có thể thay đổi từ:

```text
ClosedWorld
```

thành:

```text
OpenWorld
```

---

# 204. Đây có thể invalidate aggressive dead stripping.

---

# 205. ABI boundary

Stable ABI declarations là optimization barriers tương đối.

Không phải tuyệt đối.

---

# 206. Internal representation

`.axlib` nên giữ:

```text
semantic summary
generic metadata
ABI metadata
optimization summary
object code
```

tùy distribution tier.

---

# 207. Binary-only package

Nếu chỉ có object:

compiler vẫn link được nhưng LTO capability giảm.

---

# 208. Rich `.axlib`

Cho phép:

```text
cross-module optimization
```

mà không cần source.

---

# 209. Source package

Có đầy đủ semantic/compiler information.

---

# 210. Security

Không nên tin optimization summary từ package ngoài.

Compiler phải:

```text
verify summary
```

hoặc regenerate/validate.

---

# 211. Không cho package nói:

```text
"NoAlias"
```

rồi compiler tin mù quáng.

---

# 212. Summary trust levels

Có thể:

```text
Derived
Verified
TrustedForeign
Unknown
```

---

# 213. Axiom native summary

Compiler tự sinh:

```text
Verified
```

---

# 214. Foreign summary

Phải có contract.

---

# 215. AI generated summary

Không có authority riêng.

Compiler vẫn verify.

---

# 216. Optimization explain

Axiom có thể:

```text
ax explain opt foo
```

---

# 217. Ví dụ:

```text
foo was not inlined:
  estimated growth: 41 instructions
  threshold: 32
  callsite not hot
```

---

# 218. Hoặc:

```text
allocation eliminated:
  object does not escape
  address not observable
  lifetime proven local
```

---

# 219. Hoặc:

```text
function retained:
  exported ABI symbol
```

---

# 220. Đây là compiler facts cực kỳ hữu ích cho AI.

---

# 221. Binary size report

Có thể tạo:

```text id="2slz4m"
SizeGraph
```

```text
main
 ├─ String
 │   ├─ UTF8 validation
 │   └─ allocator
 └─ println
     └─ IO
```

---

# 222. Treemap

Tooling có thể visualize:

```text
binary
 ├── code
 ├── data
 ├── runtime
 ├── unwind
 └── metadata
```

---

# 223. Dead code report

Compiler có thể biết:

```text
compiled but eliminated
```

khác với:

```text
never instantiated
```

---

# 224. Đây là distinction hữu ích cho performance engineering.

---

# 225. Generic explosion report

Ví dụ:

```text
Vec<T>:
  i32   2.1 KB
  f32   1.9 KB
  Foo   3.8 KB
  Bar   shared with Foo
```

---

# 226. Trait dispatch report

```text
dyn Draw:
  Circle → devirtualized
  Square → retained dynamic
```

---

# 227. Runtime report

```text
Runtime:
  Allocator    8 KB
  Panic        2 KB
  Thread       0
  Async        0
  Reflection   0
```

---

# 228. Điều này trực tiếp phục vụ mục tiêu "runtime chỉ có thứ cần dùng".

---

# 229. Final binary pipeline

```text id="z5d1e7"
Source
  ↓
Semantic compilation
  ↓
Verified MIR
  ↓
OptIR
  ↓
Module optimization
  ↓
.axlib / Object
  ↓
LTO
  ↓
Whole-program reachability
  ↓
Cross-module optimization
  ↓
Runtime pruning
  ↓
Code/Data GC
  ↓
ICF/Data merge
  ↓
Final ABI lowering
  ↓
Object layout
  ↓
Link
  ↓
Binary validation
```

---

# 230. Binary validation

Sau linker cần kiểm tra:

```text
entry point
imports
exports
relocations
section permissions
TLS
unwind
ABI
machine validity
W^X
target features
```

---

# 231. Không coi linker output mặc nhiên đúng

---

# 232. Final semantic check

Không chạy lại toàn bộ typechecker, nhưng cần:

```text
Machine/Object validation
```

và conformance tests.

---

# 233. Linker failure

Nếu symbol unresolved:

```text
diagnostic
```

không tự sinh dummy symbol.

---

# 234. Weak symbols

Platform-specific semantics phải nằm trong linker/ABI layer.

---

# 235. COMDAT

Có thể dùng cho:

```text
generic instances
template-like generated code
```

nhưng Axiom semantics vẫn là authority.

---

# 236. Section GC + COMDAT

Có thể phối hợp:

```text
deduplicate
then prune
```

theo target.

---

# 237. Hot/cold partition

PGO có thể:

```text
.text.hot
.text.unlikely
```

target linker layout.

---

# 238. Binary compression

Distribution:

```text
.axpkg
```

có thể compress binary.

Compiler không coi compression là machine semantics.

---

# 239. Static vs dynamic runtime

Nếu dynamic runtime component được phép:

```text
libaxiom_runtime
```

thì dependency phải explicit.

---

# 240. Default vẫn ưu tiên static/minimal composition

để tránh "DLL hell"/runtime dependency không cần thiết.

---

# 241. Không bắt buộc static linking toàn bộ hệ thống

OS libraries vẫn có thể dynamic.

---

# 242. Axiom chỉ chịu trách nhiệm:

```text
semantic/runtime dependencies của Axiom
```

---

# 243. Platform dependency

Ví dụ Windows:

```text
kernel32
ntdll
user32
```

không phải "third-party compiler/library dependency".

Đây là platform ABI.

---

# 244. Whole-program assumption phải explicit

Compiler build graph lưu:

```text
LinkWorld {
    Closed
    Open
    Plugin
    FFI
}
```

---

# 245. Default executable

Nếu không dynamic loading/foreign callback:

```text
ClosedWorld
```

có thể được sử dụng.

---

# 246. Nếu program sử dụng:

```text
dlopen
LoadLibrary
```

thì dynamic boundary trở thành explicit.

---

# 247. Không được để một `unsafe` call tự động biến toàn program thành unknown.

Unsafe vẫn phải có contract.

---

# 248. Unsafe + external dynamic address

Nếu contract không đủ:

```text
UnknownExternalRoot
```

và compiler bảo thủ.

---

# 249. Đây là cách giữ performance mà không hy sinh safety.

---

# 250. LTO không phải "magic"

Mọi optimization đều phải có proof/contract.

---

# 251. Core semantics unchanged

LTO không được:

```text
thêm syntax
thêm runtime semantics
thay ownership
thay evaluation order
```

---

# 252. Compiler complexity tăng mạnh

Nhưng programmer không cần biết.

Đúng với nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

---

# 253. Invariants — `ALTO-20..120`

```text
ALTO-20
Link-time optimization must preserve Axiom semantics.

ALTO-21
Verified MIR remains the semantic authority.

ALTO-22
LTO may consume semantic summaries but must not replace semantic verification.

ALTO-23
Whole-program optimization operates only after semantic resolution.

ALTO-24
Trait selection must be resolved before reachability pruning.

ALTO-25
Generated declarations must be semantically validated before pruning.

ALTO-26
Reachability is not limited to the direct call graph.

ALTO-27
Exports are roots.

ALTO-28
FFI entry points are roots when explicitly exported.

ALTO-29
Reflection roots are explicit according to reflection contracts.

ALTO-30
Dynamic loading creates explicit open-world boundaries.

ALTO-31
Startup hooks are explicit roots.

ALTO-32
TLS roots are tracked separately.

ALTO-33
Runtime component roots are explicit.

ALTO-34
Indirect calls must use conservative or proven target sets.

ALTO-35
Unknown indirect targets must never be treated as unreachable.

ALTO-36
Function-pointer references create reachability edges.

ALTO-37
Vtable references create reachability edges.

ALTO-38
Static-data references create reachability edges.

ALTO-39
Generic instances are materialized only when semantically reachable.

ALTO-40
Generic specialization must not change semantics.

ALTO-41
Generic code sharing must not change observable behavior.

ALTO-42
Hybrid specialization/code sharing is permitted.

ALTO-43
Cross-module inlining is permitted when semantic and ABI contracts allow.

ALTO-44
Stable ABI boundaries must preserve their declared contract.

ALTO-45
Internal functions may be aggressively optimized.

ALTO-46
Exported symbols must not be eliminated while externally reachable.

ALTO-47
Devirtualization requires a proven target set.

ALTO-48
Dynamic dispatch cannot be removed when runtime extensibility is observable.

ALTO-49
Vtable elimination must preserve observable type/dispatch identity.

ALTO-50
ICF must preserve observable function identity.

ALTO-51
Data merging must preserve observable storage identity.

ALTO-52
Address observability creates an optimization boundary.

ALTO-53
Allocation elimination is valid only when storage identity is unobservable.

ALTO-54
Static elimination requires absence of observable identity and external reachability.

ALTO-55
TLS elimination follows TLS reachability rules.

ALTO-56
Runtime components may be eliminated when unreachable.

ALTO-57
Unused runtime subsystems must not become mandatory dependencies.

ALTO-58
Debug metadata may remain external to the runtime binary.

ALTO-59
Reflection metadata is retained only according to explicit runtime requirements.

ALTO-60
Section garbage collection must respect all semantic and external roots.

ALTO-61
Function/data sections may be independently eliminated when target format permits.

ALTO-62
Optimization passes may iterate toward a fixed point.

ALTO-63
Optimization iteration must have deterministic termination.

ALTO-64
LTO summaries must have explicit fingerprints.

ALTO-65
Stale optimization summaries must not be trusted.

ALTO-66
Optimization summaries are compiler knowledge, not semantic authority.

ALTO-67
Foreign summaries require explicit contracts or conservative treatment.

ALTO-68
Unknown foreign effects must not be optimized away.

ALTO-69
Atomic operations must preserve atomic semantics.

ALTO-70
Volatile operations must preserve observability.

ALTO-71
Synchronization operations must preserve happens-before semantics.

ALTO-72
External resource effects must remain observable.

ALTO-73
Ownership facts may be propagated across module boundaries when proven.

ALTO-74
Capability alias facts may be propagated across module boundaries when proven.

ALTO-75
UNKNOWN alias information must never become NO_ALIAS without proof.

ALTO-76
Effect summaries may enable optimization only when complete enough for the transformation.

ALTO-77
Escape summaries may enable allocation elimination only when proof is sufficient.

ALTO-78
PGO affects optimization decisions but not semantics.

ALTO-79
Optimization profiles cannot alter language semantics.

ALTO-80
Size optimization cannot violate ABI or observable identity.

ALTO-81
Binary-size reduction must not rely on undefined behavior.

ALTO-82
LTO must support incremental invalidation.

ALTO-83
Semantic fingerprint changes invalidate dependent optimization facts.

ALTO-84
ABI changes invalidate dependent ABI/codegen facts.

ALTO-85
Target changes invalidate target-specific codegen facts.

ALTO-86
Optimization-profile changes need not invalidate semantic artifacts.

ALTO-87
LTO caches include target, ABI and codegen identity.

ALTO-88
PGO data participates in artifact identity.

ALTO-89
Parallel LTO must be deterministic.

ALTO-90
Symbol ordering must be deterministic in reproducible builds.

ALTO-91
Section ordering must be deterministic in reproducible builds.

ALTO-92
Optimization heuristics must not depend on nondeterministic iteration order.

ALTO-93
Binary-size reports must distinguish code, data, runtime, metadata and unwind contributions.

ALTO-94
Compiler tooling may explain why an entity remains reachable.

ALTO-95
Compiler tooling may explain why an entity was eliminated.

ALTO-96
Compiler tooling may explain generic specialization/code sharing decisions.

ALTO-97
Compiler tooling may explain devirtualization decisions.

ALTO-98
Compiler tooling may explain runtime component retention.

ALTO-99
Compiler tooling may explain allocation elimination.

ALTO-100
Compiler tooling must report facts rather than fabricated optimization reasons.

ALTO-101
Whole-program optimization must respect open-world boundaries.

ALTO-102
Closed-world assumptions must be explicit in the build/link model.

ALTO-103
Plugin boundaries must remain open to declared runtime extensions.

ALTO-104
Dynamic symbol lookup creates explicit link-time uncertainty.

ALTO-105
WASM exports/imports are reachability boundaries.

ALTO-106
GPU kernel reachability follows host/device launch semantics.

ALTO-107
Comptime execution does not create runtime dependencies unless materialized.

ALTO-108
Generated code must participate in ordinary reachability analysis.

ALTO-109
Dead code elimination must not remove required cleanup semantics.

ALTO-110
Panic and error paths remain reachable when semantically possible.

ALTO-111
Unwind metadata must correspond to retained unwind paths.

ALTO-112
ICF/data merging must account for ABI contracts.

ALTO-113
Stable ABI artifacts may require preserving externally observable layout.

ALTO-114
LTO must not change source-level evaluation order semantics.

ALTO-115
LTO must not weaken ownership/capability verification.

ALTO-116
LTO must not introduce data races.

ALTO-117
LTO must not weaken memory ordering.

ALTO-118
LTO must not silently change floating-point semantics outside explicit fast-math contracts.

ALTO-119
LTO transformations require declared legality conditions.

ALTO-120
A final binary is valid only after object/link/machine validation succeeds.
```

---

# 254. Một điểm kiến trúc rất quan trọng được chốt

Sau task này, Axiom có **3 loại graph hoàn toàn khác nhau**:

```text
Semantic Graph
    ↓
"Chương trình có nghĩa gì?"

Optimization Graph
    ↓
"Có thể biến đổi nó như thế nào?"

Link Graph
    ↓
"Những physical entities nào cuối cùng phải tồn tại?"
```

Không được nhập ba thứ thành một.

Đây là cách tránh một compiler rất dễ rơi vào tình trạng:

> linker thấy cái gì → semantic compiler tưởng cái đó là semantics.

---

# 255. Kiến trúc compiler hiện tại

```text
                         SOURCE
                           │
                           ▼
                 Lossless Syntax / AST
                           │
                           ▼
                     Resolution
                           │
                           ▼
                         HIR
                           │
                           ▼
                    Typed HIR
                           │
                           ▼
                         MIR
                           │
             ┌─────────────┴─────────────┐
             │                           │
       Semantic Verification        Debug Provenance
             │
             ▼
        Verified MIR
             │
             ▼
           OptIR
             │
       ┌─────┴──────┐
       │            │
   Local Opt     LTO/Whole Program
       │            │
       └─────┬──────┘
             ▼
         ABI MIR
             │
             ▼
         Axiom LIR
             │
             ▼
      TargetBackend
             │
      ┌──────┼─────────────┐
      │      │             │
    x86    ARM64         RV64
      │      │             │
      └──────┼─────────────┘
             │
           WASM
             │
             ▼
        Machine/Wasm IR
             │
             ▼
       Machine Verify
             │
             ▼
          Encoding
             │
             ▼
        AxiomObject
             │
             ▼
           Linker
             │
             ▼
        Final Binary
```

---

# 256. Và Axiom hiện đã có một compiler architecture khá hoàn chỉnh

Các phần đã frozen không còn chỉ là ý tưởng ngôn ngữ:

```text
Core semantics
Ownership
Memory
Capabilities
Concurrency
Async
GPU
Comptime
Types
Traits
Generics
Closures
Collections
Strings
Errors
FFI
ABI
Runtime
GUI
Graphics
Networking
Database
Serialization
Crypto
AI/Tensor
Scientific computing
Package/build
Testing/formal semantics
Diagnostics
Security
Cross compilation
Native backends
WASM
Debug/unwind
LTO
Linker
```

Điểm tiếp theo hợp lý **không phải thêm một library feature**, mà là đi sâu vào một phần còn thiếu để compiler thực sự có thể được implement:

## **BOOTSTRAP-268 — AXIOM COMPILER BOOTSTRAP IMPLEMENTATION ARCHITECTURE**

Task này sẽ chốt cách biến toàn bộ specification trên thành compiler thật:

```text
Phase 0   Bootstrap compiler
Phase 1   Lexer/parser
Phase 2   Resolver/TypeDB
Phase 3   HIR
Phase 4   MIR
Phase 5   Ownership/Capability verifier
Phase 6   MIR interpreter
Phase 7   Axiom LIR
Phase 8   x86-64 backend
Phase 9   ARM64/RV64/WASM
Phase 10  Object writer
Phase 11  Linker
Phase 12  Runtime composition
Phase 13  Self-host compiler
Phase 14  Self-host linker
Phase 15  Compiler builds itself
```

Quan trọng nhất, task 268 sẽ xác định **bootstrap strategy cụ thể**, repository layout, crate/module/package boundaries, thứ tự implement thực tế, những phần nào có thể dùng LLVM/LLD ở bootstrap nhưng phải được thay thế khi self-host, và **milestone đầu tiên có thể compile một chương trình Axiom thật thành native executable**.