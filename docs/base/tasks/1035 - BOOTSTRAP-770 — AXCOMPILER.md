# BOOTSTRAP-770 — AXCOMPILER

**Title:** Native Axiom Compiler Frontend, Semantic Engine, Type System Integration, Generic/Closure/Pattern Lowering, IR Generation, Optimization Pipeline & Machine-Code Compilation Runtime 5.0  
**Namespace:** `AXCOMPILER`  
**Phase:** Axiom Native Compiler / Language Implementation  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXCOMPILER` là compiler chính thức của ngôn ngữ Axiom.

Pipeline chuẩn:

```text
Axiom Source
    │
    ▼
Lexer
    │
    ▼
Parser
    │
    ▼
Syntax Tree
    │
    ▼
Name Resolution
    │
    ▼
Type / Trait / Generic Analysis
    │
    ▼
Semantic IR
    │
    ▼
Optimization
    │
    ▼
Lowered IR
    │
    ▼
Machine IR
    │
    ▼
Native Code
    │
    ▼
Object Artifact
```

AXCOMPILER phải hỗ trợ:

- native compilation;
- incremental compilation;
- generics;
- traits;
- structs;
- methods;
- functions;
- closures;
- enums;
- pattern matching;
- async/task lowering;
- compile-time evaluation;
- metadata;
- diagnostics;
- debug information;
- optimization;
- vectorization;
- PGO/LTO integration;
- direct machine-code emission;
- PE64/ELF/Mach-O/WASM;
- cross compilation;
- self-hosting.

---

# 2. Triết lý compiler

Axiom compiler phải ưu tiên:

```text
correctness
    ↓
predictable semantics
    ↓
native performance
    ↓
compile-time efficiency
    ↓
small generated artifact
```

Không được đạt performance bằng cách đưa hidden runtime machinery vào mọi program.

---

# 3. Compiler không phải runtime

AXCOMPILER có thể generate runtime calls khi semantics yêu cầu, nhưng:

```text
compiler ≠ runtime
```

Một chương trình đơn giản:

```text
fn main() {
    print("hello")
}
```

không được kéo theo toàn bộ Axiom runtime.

---

# 4. Compiler boundary

AXCOMPILER sở hữu:

- lexical analysis;
- parsing;
- AST;
- name resolution;
- semantic analysis;
- type checking;
- trait resolution;
- generic instantiation;
- closure conversion;
- pattern lowering;
- constant evaluation;
- semantic IR;
- optimization;
- code generation;
- compiler metadata;
- source mapping;
- diagnostics.

Không sở hữu:

```text
AXBUILD      → build graph
AXTOOLCHAIN  → target/toolchain description
AXLINKER     → final linking
AXPACKAGE    → package resolution
AXDEBUG      → debugger
AXDIAGNOSTICS→ crash analysis
```

---

# 5. Compiler pipeline

```text id="compilerpipeline"
              SOURCE
                │
                ▼
             LEXER
                │
                ▼
             PARSER
                │
                ▼
              AST
                │
        ┌───────┴────────┐
        ▼                ▼
   Name Resolver    Syntax Validation
        │                │
        └───────┬────────┘
                ▼
          Semantic Engine
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     Types    Traits   Generics
       │        │        │
       └────────┼────────┘
                ▼
             SIR
                │
                ▼
          Optimization
                │
                ▼
             LIR/MIR
                │
                ▼
          Machine IR
                │
                ▼
          Code Generator
                │
                ▼
          Object Emitter
```

---

# 6. Compilation unit

Compilation unit là đơn vị semantic nhỏ nhất compiler xử lý độc lập.

```text
compilation_unit {
    module
    source_files
    imports
    declarations
}
```

---

# 7. Module

Module identity lấy từ AXPACKAGE/project graph nhưng semantic content do compiler quản lý.

```text
module {
    module_id
    declarations
    imports
    exports
}
```

---

# 8. Source encoding

Axiom source:

```text
UTF-8
```

là encoding mặc định.

Compiler phải reject malformed UTF-8 ở source boundary.

---

# 9. Unicode identifiers

Identifier có thể hỗ trợ Unicode theo canonical identifier policy.

Compiler phải tránh việc hai identifier visually giống nhau nhưng semantic khác nhau do normalization.

---

# 10. Lexer

Lexer chuyển:

```text
UTF-8 source
```

thành token stream.

Token phải retain source span.

---

# 11. Token

```text
token {
    kind
    source_start
    source_end
    flags
}
```

Literal value có thể được intern/cached.

---

# 12. Parser

Parser tạo syntax tree nhưng không thực hiện toàn bộ semantic checking.

Điều này cho phép:

- error recovery;
- IDE parsing;
- incremental syntax updates.

---

# 13. AST

AST giữ cấu trúc source-level:

```text
module
function
struct
enum
trait
impl
expression
statement
pattern
type
```

---

# 14. Syntax tree vs semantic tree

Phải phân biệt:

```text
AST
```

với:

```text
typed semantic representation
```

AST preserve source intent; semantic IR preserve compiler meaning.

---

# 15. Source spans

Mọi declaration/expression/type quan trọng phải có:

```text
source_span
```

để diagnostics/debug metadata.

---

# 16. Name resolution

Name resolution:

```text
identifier
 ↓
scope
 ↓
declaration
 ↓
symbol
```

Không resolve dựa trên textual heuristics.

---

# 17. Scope

Scope types:

```text
module
function
block
pattern
generic
trait
impl
```

---

# 18. Shadowing

Axiom phải định nghĩa rõ shadowing.

Ví dụ:

```text
let x = 1

{
    let x = 2
}
```

Inner `x` có thể shadow outer `x`.

Compiler phải tạo symbol identity khác nhau.

---

# 19. Import resolution

```text
import graphics
```

được resolve qua build/package module graph.

Compiler không tự search arbitrary filesystem.

---

# 20. Visibility

Baseline:

```text
private
module
package
public
```

Visibility là semantic property.

---

# 21. Symbol identity

Mỗi declaration có compiler-internal:

```text
symbol_id
```

Không dùng string name làm unique identity.

---

# 22. Type system integration

Compiler consume core type system đã định nghĩa trong Axiom semantic core:

```text
primitive
integer
float
bool
char
string
array
slice
struct
enum
function
tuple
optional/result-like types
trait
generic
```

---

# 23. Type checking

Mọi expression phải có resolved type trước lowering trừ những trường hợp intentionally deferred.

---

# 24. Type inference

Axiom hỗ trợ inference ở nơi deterministic.

Ví dụ conceptually:

```text
let x = 10
```

compiler infer integer type theo context/default rules.

---

# 25. Explicit type control

Developer có thể override:

```text
let x: i64 = 10
```

Compiler không được silently choose a wider expensive type khi explicit type đã có.

---

# 26. Integer semantics

Compiler phải preserve exact semantics cho:

```text
i8 i16 i32 i64 i128
u8 u16 u32 u64 u128
```

nếu các type đã được core language freeze.

---

# 27. Integer overflow

Compiler must know whether operation is:

```text
checked
wrapping
saturating
unchecked
```

the semantics must be explicit.

---

# 28. Floating-point

Support:

```text
f32
f64
```

với target-aware lowering.

Fast-math phải là explicit optimization policy.

---

# 29. Bool

`bool` phải có semantic values:

```text
true
false
```

ABI representation target-specific.

---

# 30. Character

Axiom `char` phải có semantic definition độc lập representation.

UTF-8 string không được đồng nhất với fixed-width character storage.

---

# 31. String

Compiler phải distinguish:

```text
string value
string slice/view
raw bytes
```

Không tự động convert byte sequence thành valid UTF-8.

---

# 32. Array

Fixed-size array:

```text
[T; N]
```

size là compile-time property.

---

# 33. Slice

Slice representation phải được compiler biết rõ:

```text
pointer/data handle
length
```

hoặc representation đã được core ABI freeze.

Compiler không được biến slice thành heap object mặc định.

---

# 34. Struct

Struct là fundamental aggregate.

Compiler phải tính:

```text
size
alignment
field offsets
padding
ABI classification
```

---

# 35. Struct layout

Default layout phải deterministic.

Có thể có:

```text
native
packed
explicit
```

layout modes.

---

# 36. OOP model

Axiom không cần class object model.

Compiler hỗ trợ:

```text
struct
+
functions
+
methods
+
traits
```

---

# 37. Method lowering

Conceptually:

```text
object.method(x)
```

→

```text
method(object, x)
```

nếu method semantics là receiver-first function.

Không cần implicit object heap allocation.

---

# 38. Method dispatch

Static dispatch mặc định.

Compiler có thể inline/direct-call nếu target known.

---

# 39. Dynamic dispatch

Trait/interface object nếu được dùng phải explicit.

Compiler generate:

```text
data
+
dispatch metadata
```

chỉ khi semantics yêu cầu.

---

# 40. Override

Override resolution được kiểm tra compile-time.

Compiler phải reject:

- signature mismatch;
- incompatible return;
- invalid receiver;
- missing required implementation.

---

# 41. Traits

Trait:

```text
trait Drawable {
    fn draw(...)
}
```

là compile-time contract.

---

# 42. Trait implementation

```text
impl Drawable for Sprite
```

Compiler tạo trait implementation record.

---

# 43. Static trait dispatch

Nếu concrete type known:

```text
generic<T: Drawable>
```

compiler có thể monomorphize/specialize.

---

# 44. Dynamic trait dispatch

Nếu trait object requested:

```text
dyn Drawable
```

compiler generate dynamic dispatch representation.

Không biến mọi trait call thành virtual dispatch.

---

# 45. Generics

Axiom generics phải ưu tiên:

```text
compile-time specialization
```

cho performance.

---

# 46. Generic representation

Generic declaration:

```text
generic function/type
```

được compiler lưu ở semantic IR trước instantiation.

---

# 47. Monomorphization

Ví dụ:

```text
max<i32>
max<f64>
```

có thể generate specialized functions.

---

# 48. Monomorphization deduplication

Nếu nhiều modules instantiate cùng specialization:

```text
same generic
+
same type parameters
+
same semantic environment
```

compiler/cache phải deduplicate.

---

# 49. Generic code bloat

AXCOMPILER phải có optimization:

```text
specialize only where useful
```

Có thể share implementation khi representation/ABI cho phép.

---

# 50. Generic constraints

Generic constraints được resolve trước code generation.

---

# 51. Associated types

Nếu Axiom trait model hỗ trợ associated types:

```text
trait Iterator {
    type Item
}
```

compiler must resolve them statically whenever possible.

---

# 52. Const generics

Có thể support:

```text
[T; N]
```

với `N` compile-time constant.

---

# 53. Compile-time evaluation

Axiom nên có compile-time evaluator:

```text
const
comptime
```

cho phép tính:

- constants;
- array sizes;
- lookup tables;
- type-level values;
- generated metadata.

---

# 54. CTFE

Compile-time function evaluation:

```text
source function
 ↓
CTFE interpreter
 ↓
constant result
```

không được invoke arbitrary runtime effects.

---

# 55. CTFE sandbox

Compile-time code không mặc định được:

- network;
- arbitrary filesystem;
- process creation;
- secret access.

Capability-controlled compile-time effects nếu cần.

---

# 56. Constant folding

Compiler phải fold:

```text
2 + 3
```

thành constant khi semantics cho phép.

---

# 57. Dead code elimination

Unreachable/dead code có thể được eliminated.

Không được remove code có observable side effects.

---

# 58. Control flow

Semantic IR phải biểu diễn:

```text
if
loop
while
for
match
break
continue
return
defer
```

nếu đã được language core xác định.

---

# 59. Match lowering

Pattern matching:

```text
match value {
    ...
}
```

được lower thành optimized decision tree/jump table/branch structure tùy target.

---

# 60. Exhaustiveness

Compiler kiểm tra exhaustive patterns cho enum/sealed pattern domains.

---

# 61. Pattern usefulness

Compiler detect unreachable/redundant pattern arms.

---

# 62. Enum representation

Compiler chọn representation dựa trên:

```text
variant count
payload sizes
ABI
niche optimization
```

nếu semantics cho phép.

---

# 63. Optional/niche optimization

Nullable-like types có thể dùng unused bit patterns để tránh additional storage.

Đây là optimization, không được thay đổi observable semantics.

---

# 64. Closure

Closure:

```text
fn(x) => x + captured
```

được lowering thành environment + function.

---

# 65. Closure capture

Compiler phân tích capture:

```text
by_value
by_mutable_value
by_shared_handle/reference
```

theo memory semantics của Axiom.

---

# 66. No hidden heap allocation

Closure không được mặc định heap allocate.

Compiler phải chọn:

```text
stack
register
inline environment
heap
```

dựa trên escape/lifetime requirements.

---

# 67. Closure escape analysis

Nếu closure không escape:

```text
closure
 ↓
stack/register
```

có thể tránh allocation.

---

# 68. Function pointers

Function pointer là explicit first-class value.

Representation target-specific nhưng ABI stable.

---

# 69. Indirect calls

Compiler có thể optimize indirect call nếu target becomes known:

```text
devirtualization
```

---

# 70. Tail calls

Compiler hỗ trợ tail-call optimization khi:

- ABI cho phép;
- semantics cho phép;
- optimization enabled.

---

# 71. Recursion

Recursive functions phải compile native trực tiếp.

Không cần runtime trampoline mặc định.

---

# 72. Async/task lowering

AXCOMPILER phối hợp với `AXTASK`/`AXASYNC`.

Conceptually:

```text
async fn
   ↓
state machine
   ↓
task representation
```

---

# 73. Async allocation

Compiler phải avoid heap allocation nếu async state machine có thể reside inline trong caller/task storage.

---

# 74. Async state

State machine gồm:

```text
state
captured values
continuation
result
error
```

the exact runtime representation thuộc AXASYNC/AXTASK ABI.

---

# 75. Await lowering

```text
await operation
```

được lower thành suspension point.

---

# 76. Suspension safety

Compiler phải preserve values sống qua suspension.

---

# 77. No GC requirement

AXCOMPILER không được giả định garbage collector tồn tại.

Nếu một library/runtime cung cấp GC riêng, compiler chỉ cần support its explicit ABI.

---

# 78. Memory semantics

Compiler phải tôn trọng Axiom memory model:

```text
explicit ownership/lifetime semantics
+
deterministic destruction where specified
+
no mandatory tracing GC
```

Compiler không tự chèn hidden GC barriers.

---

# 79. Destructors/drop

Nếu core language có deterministic cleanup:

```text
scope exit
 ↓
cleanup chain
```

Compiler phải generate chính xác cleanup paths.

---

# 80. Cleanup lowering

Cleanup phải chạy đúng khi:

```text
return
break
continue
exception/error propagation
normal scope exit
```

the semantics permit.

---

# 81. Error model

Nếu Axiom sử dụng explicit result/error:

```text
Result<T,E>
```

compiler optimize success/error paths where possible.

---

# 82. Exceptions

Nếu exception mechanism tồn tại, compiler phải lower theo target exception ABI.

Không được biến ordinary errors thành exceptions implicitly.

---

# 83. Panic/fatal path

Fatal runtime paths phải be explicit and minimal.

---

# 84. IR architecture

Axiom compiler nên có nhiều IR levels nhưng tránh tạo quá nhiều redundant representations.

Baseline:

```text
AST
 ↓
SIR
 ↓
MIR
 ↓
MIR-Lowered
 ↓
Machine IR
```

---

# 85. SIR

**Semantic IR** giữ:

- resolved symbols;
- types;
- generic information;
- traits;
- control flow;
- ownership/lifetime facts;
- compile-time constants.

---

# 86. MIR

**Mid-level IR** tập trung vào:

- explicit control flow;
- explicit memory operations;
- calls;
- branches;
- aggregates;
- temporaries.

---

# 87. Machine IR

Machine IR gần target:

```text
virtual registers
physical register constraints
instructions
basic blocks
calling convention
```

---

# 88. SSA

MIR có thể sử dụng SSA.

SSA giúp:

- constant propagation;
- dead code elimination;
- common subexpression elimination;
- register allocation preparation.

---

# 89. Memory SSA

Memory dependencies cần representation đủ chính xác để optimize loads/stores mà không phá semantics.

---

# 90. Alias analysis

Compiler cần alias analysis.

Nhưng không được yêu cầu developer viết pointer annotations phức tạp chỉ để compiler optimize ordinary code.

---

# 91. Escape analysis

Compiler phân tích object/value escape để quyết định:

```text
stack
register
inline
heap
```

---

# 92. Stack allocation

Local aggregate có thể được stack allocate nếu lifetime bounded.

---

# 93. Scalar replacement

Struct:

```text
Point { x, y }
```

có thể scalarize thành:

```text
x
y
```

khi profitable.

---

# 94. Register allocation

Machine backend thực hiện:

```text
live range analysis
 ↓
register allocation
 ↓
spill
```

---

# 95. Register allocation strategy

Có thể dùng:

```text
linear scan
graph coloring
hybrid
```

Implementation choice.

Fast compile profile có thể dùng simpler allocator; release có thể dùng advanced allocator.

---

# 96. Instruction selection

Compiler maps MIR → target instructions.

Axiom backend phải có target-independent lowering trước machine-specific selection.

---

# 97. Pattern matching instruction selection

Backend có thể recognize:

```text
multiply + add
bit operations
addressing modes
vector operations
```

và chọn instruction tối ưu.

---

# 98. Peephole optimization

Machine IR có pass:

```text
instruction sequence
 ↓
local rewrite
```

cho compact machine code.

---

# 99. SIMD/vectorization

Compiler phải support:

- explicit vector types;
- auto-vectorization;
- target feature checks.

---

# 100. Auto-vectorization

Loop được vectorize khi dependency analysis chứng minh correctness.

---

# 101. SIMD fallback

Target-specific SIMD specialization có thể coexist với scalar fallback.

---

# 102. CPU dispatch

AXCOMPILER có thể generate:

```text
baseline implementation
optimized implementation
dispatch
```

khi project requests multiversioning.

---

# 103. Inlining

Inlining heuristic dựa trên:

```text
size
hotness
call frequency
optimization profile
code-size budget
```

---

# 104. Always-inline

Developer có thể request explicit forced-inline attribute.

Compiler có thể reject nếu impossible.

---

# 105. No-inline

Developer có thể prevent inlining.

---

# 106. Interprocedural optimization

Compiler có thể optimize across functions/modules khi build mode cho phép.

---

# 107. LTO

AXCOMPILER phải emit sufficient IR/object metadata cho AXLINKER/LTO pipeline.

---

# 108. PGO

Profile metadata được consume để:

- inline;
- branch ordering;
- function placement;
- code layout;
- hot/cold splitting.

---

# 109. Branch optimization

Compiler có thể:

```text
likely
unlikely
profile-guided
```

nhưng correctness không phụ thuộc branch hints.

---

# 110. Code layout

Hot code có thể đặt gần nhau để improve instruction-cache locality.

---

# 111. Cold splitting

Rare error/failure paths có thể được separated from hot path.

---

# 112. Bounds-check elimination

Compiler có thể remove redundant bounds checks khi proof is valid.

Không được assume programmer correctness.

---

# 113. Bounds-check semantics

Nếu bounds checking là language semantic:

```text
invalid index
```

phải có defined failure behavior.

Optimization chỉ được remove check khi compiler chứng minh safe.

---

# 114. Division optimization

Constant division có thể lower thành multiplication/shift sequence khi exact semantics preserved.

---

# 115. Constant propagation

Compiler phải propagate constants across SSA and interprocedural boundaries where safe.

---

# 116. Common subexpression elimination

CSE được phép nếu expressions không có forbidden observable side effects.

---

# 117. Load/store optimization

Compiler có thể reorder memory operations theo Axiom memory model.

Không được áp dụng C-like assumptions nếu Axiom semantics khác.

---

# 118. Atomic operations

Atomic semantics phải map tới target instructions/fences.

Compiler không được weaken requested memory order.

---

# 119. Volatile

Volatile operations preserve required observable access semantics.

---

# 120. Unsafe/native operations

Unsafe operations được compiler đánh dấu:

```text
unsafe
```

và không được silently reinterpret thành safe operation.

---

# 121. Inline assembly

Nếu hỗ trợ:

```text
asm(...)
```

phải có:

- clobbers;
- inputs;
- outputs;
- memory effects;
- target constraints.

---

# 122. FFI

Foreign function declaration:

```text
extern "c" fn ...
```

Compiler phải map đúng foreign ABI.

---

# 123. C interoperability

Axiom có thể gọi C libraries mà không cần compiler dependency vào C.

AXCOMPILER cần hiểu ABI, không nhất thiết hiểu toàn bộ C language.

---

# 124. Foreign struct layout

FFI struct có thể declare:

```text
extern struct
```

với explicit layout.

---

# 125. Link symbols

Compiler emits symbol metadata:

```text
name
visibility
binding
section
type
ABI
```

AXLINKER resolves final symbol relationships.

---

# 126. Object emission

AXCOMPILER có thể trực tiếp emit:

```text
COFF
ELF
Mach-O
WASM
```

thông qua object emitter.

---

# 127. Direct machine code

Primary native path:

```text
MIR
 ↓
instruction selection
 ↓
register allocation
 ↓
machine encoding
 ↓
object emitter
```

Không cần intermediate textual assembly.

---

# 128. Assembly fallback

Compiler có thể emit assembly cho:

- debugging;
- experimentation;
- backend development;
- interoperability.

Không phải canonical path.

---

# 129. Debug information

Compiler emits source mapping:

```text
machine address
 ↔
function
 ↔
file
 ↔
line
 ↔
column
```

AXDIAGNOSTICS/debugger consume it.

---

# 130. Variable location metadata

Compiler có thể emit:

```text
register
stack slot
constant
optimized-out
```

cho debugger.

---

# 131. Optimization debug tradeoff

Debug build:

```text
less optimization
more source fidelity
```

Release:

```text
more optimization
less source fidelity
```

là build profile, không semantic difference.

---

# 132. Compiler diagnostics

Diagnostic:

```text
error
warning
note
help
```

phải có source span.

---

# 133. Diagnostic structure

```text id="diag"
diagnostic {
    severity
    code
    message
    primary_span
    secondary_spans
    notes
    suggestions
}
```

---

# 134. Machine-readable diagnostics

Compiler phải emit:

```text
AXDIAG_1
```

structured diagnostic format.

---

# 135. Error recovery

Parser nên recover sau syntax errors để phát hiện nhiều vấn đề trong một invocation.

Semantic compiler phải tránh cascading nonsense errors.

---

# 136. Suggestions

Compiler có thể provide:

```text
insert
replace
rename
import
type annotation
```

suggestions.

---

# 137. No unsafe auto-fix

Compiler suggestions không tự mutate source trong compiler core.

IDE/build tooling quyết định apply.

---

# 138. Incremental compilation

Compiler cache unit:

```text
module
```

với fingerprints từ AXBUILD.

---

# 139. Incremental parser

IDE mode có thể reuse syntax tree regions unaffected by source edit.

---

# 140. Incremental semantic analysis

Semantic dependency graph cho phép re-analyze affected declarations only.

---

# 141. Compiler server

Persistent compiler service:

```text
AXCOMPILER SERVER
```

giữ:

- parsed modules;
- semantic caches;
- type tables;
- package metadata;
- codegen caches.

---

# 142. Cache correctness

Compiler server cache không được override source/package/toolchain fingerprints.

---

# 143. Parallel compilation

Independent modules compile parallel.

---

# 144. Parallel semantic analysis

Compiler có thể parallelize:

- parsing;
- module resolution;
- type checking;
- generic instantiation;
- code generation.

Shared structures phải immutable hoặc sharded.

---

# 145. Compiler memory

Compiler memory phải ưu tiên:

```text
arena allocation
interning
compact IDs
immutable tables
```

để giảm allocator overhead.

---

# 146. Arena lifetime

Compiler arenas có lifetime:

```text
parse
module
compilation
session
```

Không dùng general-purpose heap cho mọi tiny compiler object nếu arena phù hợp.

---

# 147. Interning

Strings/types/symbol names có thể intern để giảm duplicate memory.

---

# 148. Stable IDs

Compiler dùng integer IDs:

```text
TypeId
SymbolId
ModuleId
FunctionId
BlockId
InstructionId
```

thay vì pointer-heavy graphs wherever practical.

---

# 149. Pointer reduction

Compiler internal representation nên ưu tiên:

```text
integer IDs
arrays
arenas
compact vectors
```

thay vì graph of arbitrary heap pointers.

Điều này phù hợp mục tiêu Axiom về giảm complexity/fragmentation.

---

# 150. Compiler garbage collection

Không yêu cầu GC.

Compiler memory được reclaim theo arena/session lifetime.

---

# 151. Compile-time memory limits

AXBUILD có thể set:

```text
compiler_memory_limit
```

Compiler phải report structured failure thay vì crash nếu possible.

---

# 152. Deterministic compilation

Given:

```text
source
dependencies
compiler
target
options
environment
```

compiler semantic result phải deterministic.

---

# 153. Diagnostic determinism

Trong deterministic mode, diagnostics ordering phải deterministic.

---

# 154. Parallel diagnostic ordering

Parallel compiler jobs có thể hoàn thành khác thứ tự nhưng emitted diagnostics được canonical-sort trước output.

---

# 155. Reproducible machine code

Compiler backend phải hỗ trợ deterministic:

- symbol ordering;
- section ordering;
- generated IDs;
- hash tables where relevant;
- debug metadata normalization.

---

# 156. Compiler randomization

Nếu compiler dùng randomized heuristic:

```text
compiler_seed
```

phải explicit trong reproducible mode.

---

# 157. Optimization levels

Baseline:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
-Ofast-like explicit mode
```

Exact semantics phải được documented.

---

# 158. Fast compile mode

`-O0/-O1` ưu tiên compile latency.

---

# 159. Release mode

`-O2/-O3` ưu tiên runtime performance.

---

# 160. Size mode

`-Os/-Oz` ưu tiên artifact size.

---

# 161. Fast-math

Không được bật ngầm.

Phải explicit vì có thể thay đổi floating-point semantics.

---

# 162. Undefined behavior

Axiom không nên dựa quá mức vào undefined behavior để achieve performance.

Nếu operation invalid, language phải define:

```text
compile-time rejection
runtime trap
checked result
```

theo explicit semantics.

---

# 163. Optimization safety

Optimization must preserve the language abstract machine.

Không được dùng C/C++ UB assumptions nếu Axiom semantics không định nghĩa chúng.

---

# 164. Compile-time feature gates

Compiler có thể conditionally compile:

```text
target
OS
architecture
feature
```

nhưng feature values phải được AXBUILD/AXTOOLCHAIN cung cấp, không tự detect arbitrary environment.

---

# 165. Target intrinsics

Target-specific intrinsics:

```text
simd
atomics
bit operations
CPU instructions
```

được exposed qua standard compiler intrinsics.

---

# 166. Intrinsic lowering

Intrinsic:

```text
@intrinsic
```

được compiler map trực tiếp tới target instruction hoặc defined runtime fallback.

---

# 167. Runtime fallback

Nếu intrinsic có portable fallback:

```text
target supports → instruction
target lacks → fallback
```

semantics identical.

---

# 168. Compile-time target query

Axiom có thể expose:

```text
target.arch
target.os
target.cpu_feature(...)
```

cho compile-time branching.

---

# 169. Generated code metadata

Compiler emits metadata:

```text
compiler_version
language_version
target
ABI
optimization
source_revision
```

theo selected artifact metadata profile.

---

# 170. AI compiler metadata

Compiler should emit machine-readable:

```text
symbol graph
type graph
API contracts
module dependencies
ABI information
source spans
documentation references
```

cho AI tooling.

---

# 171. AI metadata stripping

Release artifact có thể strip AI metadata:

```text
none
minimal
full
```

không làm thay đổi executable semantics.

---

# 172. Compiler plugin model

Compiler core không nên cho arbitrary plugins mutate semantic rules.

Extension points phải be constrained:

```text
lint
diagnostic
codegen backend
macro/compile-time facility
```

và versioned APIs.

---

# 173. Compiler plugins and determinism

Plugin output trở thành build input.

Plugin phải declare:

```text
identity
version
capabilities
inputs
```

---

# 174. Macro system

Nếu Axiom có macros:

```text
source
 ↓
macro expansion
 ↓
AST
```

Macro hygiene phải prevent accidental capture.

---

# 175. Hygienic macros

Generated identifiers phải có syntax context/unique identity.

---

# 176. Macro capabilities

Compile-time macro code không được arbitrary system access mặc định.

---

# 177. Source generation

Macro-generated source phải retain source mapping tới originating macro/source.

---

# 178. Compiler ABI

Native compiler API:

```text
AXCOMPILER_ABI_1
```

---

# 179. Compiler request

```text id="compilerreq"
compile_request {
    source_units
    module_graph
    target
    abi
    compiler_options
    feature_set
    optimization
    debug_mode
    reproducibility_mode
    cache_policy
}
```

---

# 180. Compiler result

```text id="compilerres"
compile_result {
    status
    object_artifacts
    module_metadata
    diagnostics
    interface_hashes
    abi_hashes
    source_maps
    provenance
}
```

---

# 181. Compiler session

```text
compiler_session_open()
compiler_session_close()
```

Session owns caches/arenas.

---

# 182. Compiler APIs

Core API:

```text
compiler_init()
compiler_shutdown()

source_parse()
source_parse_incremental()

module_resolve()
module_analyze()

type_check()
trait_resolve()
generic_instantiate()

ctfe_evaluate()

ir_build()
ir_optimize()
ir_lower()

codegen_compile()
object_emit()

diagnostics_get()

cache_lookup()
cache_store()

compiler_fingerprint()
```

---

# 183. IR inspection

Developer tooling:

```text
axiom compile --emit=ast
axiom compile --emit=sir
axiom compile --emit=mir
axiom compile --emit=machine-ir
axiom compile --emit=obj
```

---

# 184. Optimization inspection

```text
axiom compile --explain-opt
```

có thể hiển thị:

```text
inlined function X
vectorized loop Y
eliminated bounds check Z
```

---

# 185. Assembly inspection

```text
axiom compile --emit=asm
```

chỉ là diagnostic/debug output.

---

# 186. Object inspection

Compiler/toolchain tools có thể inspect:

```text
sections
symbols
relocations
ABI
target
debug
```

---

# 187. Compiler crash boundary

Compiler crash phải integrate AXDIAGNOSTICS.

Crash dump không được phụ thuộc compiler heap còn nguyên vẹn.

---

# 188. Compiler logging

AXLOGGING có thể capture structured compiler events.

---

# 189. Compiler observability

AXOBSERVABILITY metrics:

```text
parse_time
typecheck_time
generic_time
optimization_time
codegen_time
cache_hit
cache_miss
memory_peak
```

---

# 190. Compiler audit

Normal compilation không cần audit.

Security-sensitive compiler actions có thể được AXAUDIT ghi nhận.

---

# 191. Security

AXCOMPILER phải chạy theo AXSECURITY policy.

Compile-time code không được mặc định bypass sandbox.

---

# 192. Secret handling

Compiler diagnostics/cache/metadata không được chứa plaintext secrets.

---

# 193. Package trust

Compiler chỉ consume dependency artifacts đã được AXPACKAGE/AXSECURITY xác định là acceptable theo policy.

---

# 194. Build integration

```text
AXBUILD
   │
   ▼
AXCOMPILER
   │
   ├── cache
   ├── diagnostics
   └── objects
   │
   ▼
AXLINKER
```

---

# 195. Toolchain integration

Compiler lấy:

```text
target
ABI
CPU features
object format
sysroot
SDK
```

từ AXTOOLCHAIN snapshot.

---

# 196. Linker boundary

Compiler không tự perform final global link.

Compiler emits link metadata cho AXLINKER.

---

# 197. Object ownership

Compiler owns generated object artifact until AXBUILD/AXLINKER consumes immutable artifact.

---

# 198. Compiler cache key

Canonical:

```text id="cckey"
source/interface fingerprint
compiler fingerprint
target
ABI
optimization
features
dependencies
```

---

# 199. Cache invalidation

Compiler cache invalidates khi semantic input changes.

Timestamp-only changes không bắt buộc invalidate.

---

# 200. Shared compiler cache

Shared cache artifact phải content-addressed và integrity verified.

---

# 201. Backend architecture

Backend interface:

```text
Backend {
    target
    validate()
    lower()
    optimize()
    allocate()
    emit()
}
```

---

# 202. Backend independence

Frontend không được hard-code x86 assumptions.

---

# 203. Backend targets

Initial:

```text
x86_64
AArch64
WASM32
```

---

# 204. Backend extension

Future:

```text
RISC-V64
GPU
custom accelerator
```

có thể implement backend contract.

---

# 205. GPU compilation

Axiom GPU programming có thể eventually use compiler backend:

```text
Axiom GPU source
 ↓
GPU IR
 ↓
native GPU artifact
```

Không bắt buộc CPU compiler phải giả lập GPU semantics.

---

# 206. CPU/GPU shared semantics

Common language semantics:

```text
types
functions
structs
control flow
```

nhưng target-specific limitations phải explicit.

---

# 207. Compile-time target capability

Compiler reject unsupported constructs early.

Ví dụ:

```text
OS-only API
```

trong WASM target.

---

# 208. Link-time errors

Nếu issue chỉ phát hiện ở symbol resolution:

```text
AXLINKER
```

chịu trách nhiệm final diagnostic.

---

# 209. Compiler error codes

Baseline:

```text id="errors"
COMPILER_PARSE_ERROR
COMPILER_NAME_ERROR
COMPILER_TYPE_ERROR
COMPILER_TRAIT_ERROR
COMPILER_GENERIC_ERROR
COMPILER_CONST_EVAL_ERROR
COMPILER_PATTERN_ERROR
COMPILER_ASYNC_ERROR
COMPILER_ABI_ERROR
COMPILER_TARGET_ERROR
COMPILER_CODEGEN_ERROR
COMPILER_CACHE_ERROR
COMPILER_INTERNAL_ERROR
```

---

# 210. Internal compiler error

ICE phải:

- có stable error identifier;
- preserve source/build context;
- produce diagnostics;
- optionally generate AXDIAGNOSTICS dump.

---

# 211. Compiler test architecture

Tests phải cover:

```text
parser
resolver
type system
traits
generics
CTFE
IR
optimization
backend
ABI
object emission
reproducibility
```

---

# 212. Golden tests

AST/IR/object metadata có thể dùng golden files.

---

# 213. Differential tests

Compiler có thể compare:

```text
-O0
vs
-O3
```

về semantic result.

---

# 214. Backend verification

Generated object phải validate bằng AXTOOLCHAIN/AXLINKER validators.

---

# 215. Fuzzing

Compiler parser/semantic engine có thể fuzz bằng AXRANDOM deterministic seeds.

---

# 216. Deterministic fuzzing

Fuzz input phải có:

```text
seed
compiler_version
target
```

để reproduce.

---

# 217. Self-hosting compiler source

AXCOMPILER cuối cùng phải được viết bằng Axiom:

```text
axiom compiler source
        ↓
Axiom compiler
        ↓
Axiom compiler binary
```

---

# 218. Bootstrap dependency

Trong final self-hosted state:

```text
external C compiler
external C++ compiler
external managed runtime
```

không phải permanent dependency.

---

# 219. Stage comparison

Bootstrap verification:

```text
compiler A
   ↓ compile compiler source
compiler B

compiler B
   ↓ compile same source
compiler C
```

So sánh deterministic output.

---

# 220. Self-hosting milestone

AXCOMPILER 5.0 architectural completion không đồng nghĩa compiler implementation đã hoàn tất.

Nó đóng băng **compiler architecture** để implementation team có thể xây từng subsystem.

---

# 221. Performance architecture

Compiler phải tối ưu cả:

```text
compile speed
runtime speed
binary size
memory usage
```

không chỉ runtime performance.

---

# 222. Fast path

Common source:

```text
small module
few dependencies
no generics
```

phải compile với minimum passes cần thiết.

---

# 223. Pass pipeline selection

Không chạy pass vô ích.

Ví dụ:

```text
-O0
```

không nên chạy full expensive interprocedural optimizer.

---

# 224. Pass manager

Compiler pass manager:

```text
IR
 ↓
pass pipeline
 ↓
IR
```

có dependency declarations giữa passes.

---

# 225. Pass invalidation

Pass phải khai báo preservation:

```text
preserves CFG
preserves types
invalidates alias analysis
...
```

tránh recompute unnecessary analyses.

---

# 226. Analysis cache

Compiler có thể cache:

- dominators;
- loop info;
- alias analysis;
- type facts;
- range facts.

---

# 227. Compile memory locality

Compiler internal structures nên dùng contiguous storage wherever practical.

---

# 228. Pointer minimization

Compiler graph:

```text
ID → array
```

được ưu tiên hơn:

```text
object → object → object
```

khi không cần pointer identity.

---

# 229. Arena allocation

Short-lived compiler data dùng arena để giảm fragmentation.

---

# 230. Thread safety

Compiler sessions phải hỗ trợ parallel compilation.

Read-only semantic tables có thể shared.

---

# 231. Compiler daemon safety

Một compiler daemon không được để state từ project A leak sang project B.

Session/project identity phải isolate.

---

# 232. Reproducible diagnostics

Diagnostics ordering:

```text
file
span
severity
diagnostic_id
```

canonical sort trong deterministic mode.

---

# 233. Compiler configuration

AXCONFIG may provide compiler defaults, but every compilation request receives immutable resolved configuration.

---

# 234. Compiler metadata versioning

Metadata format:

```text
AXCOMPILER_META_1
```

được version độc lập với compiler binary.

---

# 235. Metadata compatibility

Compiler version N có thể đọc metadata M nếu compatibility matrix cho phép.

---

# 236. Source compatibility

Language version:

```text
AXLANG_1
AXLANG_2
...
```

phải được compiler explicit recognize.

---

# 237. Language edition

Axiom có thể có edition:

```text
language_edition
```

để evolve syntax/semantics mà không phá toàn bộ ecosystem.

---

# 238. Edition resolution

Project manifest pin edition.

Compiler không tự switch edition dựa trên source guess.

---

# 239. Deprecation

Compiler warning:

```text
deprecated API
```

có source/package metadata.

---

# 240. Compatibility mode

Legacy source có thể compile under explicit compatibility mode.

---

# 241. Formal invariants

```text id="compinv"
COMP-INV-01
AXCOMPILER phải có deterministic lexical semantics.

COMP-INV-02
Source UTF-8 phải được validate tại source boundary.

COMP-INV-03
Syntax tree và semantic representation phải được phân biệt.

COMP-INV-04
Mọi semantic declaration phải có stable compiler identity.

COMP-INV-05
Name resolution phải deterministic.

COMP-INV-06
Module resolution không được search arbitrary undeclared filesystem state.

COMP-INV-07
Visibility phải được enforce tại compile time.

COMP-INV-08
Mọi typed expression hợp lệ phải có resolved type trước lowering.

COMP-INV-09
Explicit type annotation phải được tôn trọng.

COMP-INV-10
Integer semantics phải preserve exact language-defined behavior.

COMP-INV-11
Floating-point optimizations không được tự ý thay đổi required semantics.

COMP-INV-12
Struct layout phải deterministic.

COMP-INV-13
Method lowering không được yêu cầu hidden object allocation.

COMP-INV-14
Static dispatch phải là default khi target type known.

COMP-INV-15
Dynamic dispatch chỉ được sinh khi language semantics yêu cầu.

COMP-INV-16
Generic specialization phải preserve generic semantics.

COMP-INV-17
Generic instantiation cùng canonical inputs phải produce equivalent specialization.

COMP-INV-18
Compiler không được bắt buộc tracing GC.

COMP-INV-19
Compiler không được chèn hidden ownership/runtime machinery ngoài language semantics.

COMP-INV-20
Deterministic cleanup phải được generate trên mọi required control-flow exit.

COMP-INV-21
Pattern matching phải preserve exhaustiveness semantics.

COMP-INV-22
Unreachable pattern detection phải deterministic.

COMP-INV-23
Closure capture semantics phải explicit và correct.

COMP-INV-24
Closure không được heap allocate mặc định khi escape analysis chứng minh không cần.

COMP-INV-25
Async lowering phải preserve state sống qua suspension.

COMP-INV-26
Compile-time evaluation không được mặc định bypass security sandbox.

COMP-INV-27
Optimization phải preserve Axiom abstract-machine semantics.

COMP-INV-28
Bounds-check elimination chỉ được thực hiện khi correctness được chứng minh.

COMP-INV-29
Atomic operations phải preserve requested memory ordering.

COMP-INV-30
FFI functions phải respect declared foreign ABI.

COMP-INV-31
Machine code generation phải phù hợp target ABI.

COMP-INV-32
Object emission phải phù hợp target object format.

COMP-INV-33
Compiler không được phụ thuộc textual assembly trong direct-codegen path.

COMP-INV-34
Compiler cache hit không được override source/toolchain/target identity.

COMP-INV-35
Parallel compilation không được thay đổi semantic result.

COMP-INV-36
Reproducible compilation phải normalize nondeterministic compiler state.

COMP-INV-37
Compiler diagnostics phải giữ source context chính xác.

COMP-INV-38
Compiler metadata phải versioned.

COMP-INV-39
AI/compiler extensions không được bypass language, security hoặc build contracts.

COMP-INV-40
AXCOMPILER chịu trách nhiệm compile Axiom semantics thành target code; build orchestration, package resolution, final linking và execution thuộc subsystem tương ứng.
```

---

# 242. Definition of Done

`AXCOMPILER 5.0` được freeze khi architecture bao phủ:

- UTF-8 source;
- lexer;
- parser;
- AST;
- source spans;
- name resolution;
- modules;
- imports;
- visibility;
- symbol IDs;
- complete core type integration;
- integer semantics;
- floating-point semantics;
- strings;
- arrays;
- slices;
- structs;
- struct layout;
- methods;
- static dispatch;
- dynamic dispatch;
- traits;
- overrides;
- generics;
- monomorphization;
- specialization;
- associated types;
- const generics;
- CTFE;
- constant folding;
- enums;
- pattern matching;
- exhaustiveness;
- closures;
- capture analysis;
- escape analysis;
- function pointers;
- async lowering;
- task integration;
- deterministic cleanup;
- explicit error model;
- SIR;
- MIR;
- Machine IR;
- SSA;
- memory analysis;
- alias analysis;
- register allocation;
- instruction selection;
- peephole optimization;
- inlining;
- interprocedural optimization;
- LTO;
- PGO;
- vectorization;
- CPU multiversioning;
- bounds-check elimination;
- atomic lowering;
- volatile;
- unsafe;
- inline assembly;
- FFI;
- C ABI;
- symbol metadata;
- COFF;
- ELF;
- Mach-O;
- WASM;
- direct machine-code emission;
- debug metadata;
- source mapping;
- incremental compilation;
- compiler server;
- compiler caches;
- deterministic compilation;
- reproducible compilation;
- compiler diagnostics;
- machine-readable diagnostics;
- compiler plugins/extensions;
- hygienic macros;
- target feature gates;
- target intrinsics;
- AI metadata;
- AXBUILD integration;
- AXTOOLCHAIN integration;
- AXPACKAGE integration;
- AXSECURITY integration;
- AXDIAGNOSTICS integration;
- AXOBSERVABILITY integration;
- AXLOGGING integration;
- AXCONFIG integration;
- native API;
- `AXCOMPILER_ABI_1`;
- self-hosting architecture;
- 40 compiler invariants.

**AXCOMPILER 5.0 → FROZEN.**

---

# BOOTSTRAP-771 — AXASSEMBLER

**Native Machine Instruction Encoding, Assembly Syntax, Register Model, Relocation Emission, Inline Assembly, Object Encoding & Architecture Backend Runtime 5.0**

Sau `AXCOMPILER`, bước tiếp theo là đóng băng lớp thấp hơn trực tiếp phục vụ mục tiêu đặc biệt quan trọng của Axiom:

```text
AXCOMPILER
      │
      ▼
Machine IR
      │
      ▼
AXASSEMBLER
      │
      ├── instruction encoding
      ├── registers
      ├── immediates
      ├── addressing modes
      ├── relocations
      ├── inline assembly
      └── object emission
             │
             ▼
        AX object format
```

Điểm then chốt của `AXASSEMBLER` là **Axiom không cần biến machine instruction thành text assembly rồi gọi assembler bên ngoài**. Compiler có thể encode instruction trực tiếp thành bytes; AXASSEMBLER vẫn cung cấp một abstraction chính thức cho instruction encoding, assembly syntax, inline assembly và backend development.