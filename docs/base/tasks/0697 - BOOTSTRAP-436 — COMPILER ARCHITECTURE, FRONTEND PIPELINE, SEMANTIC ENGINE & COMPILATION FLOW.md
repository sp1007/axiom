# BOOTSTRAP-436 — COMPILER ARCHITECTURE, FRONTEND PIPELINE, SEMANTIC ENGINE & COMPILATION FLOW

**Trạng thái: COMPLETED / LOCKED**

Sau 420–435, Axiom đã khóa gần như toàn bộ **ngôn ngữ, ABI, memory, runtime, toolchain và verification**.

Task này ghép chúng thành một compiler architecture thực sự có thể implement.

Mục tiêu:

> **Một source Axiom phải đi qua một pipeline rõ ràng, mỗi phase có input/output/invariant riêng, có thể incremental, cache được, song song hóa được và cuối cùng phát ra machine code native mà không cần LLVM/GCC/Clang.**

---

# 436.1 — Tổng quan compiler

Kiến trúc:

```text
Source Files
    │
    ▼
Workspace / Package Loader
    │
    ▼
Lexer
    │
    ▼
Parser
    │
    ▼
AST
    │
    ▼
Name Resolution
    │
    ▼
HIR / Semantic AST
    │
    ├──────────────► Documentation / IDE / AI Queries
    │
    ▼
Type Checking
    │
    ▼
Trait / Generic Resolution
    │
    ▼
Ownership / Effect Checking
    │
    ▼
Const / Comptime Evaluation
    │
    ▼
Layout / ABI Resolution
    │
    ▼
MIR
    │
    ▼
Optimization
    │
    ▼
Low-level IR
    │
    ▼
Instruction Selection
    │
    ▼
Machine Code
    │
    ▼
Object File
    │
    ▼
Axiom Linker
    │
    ▼
Native Artifact
```

---

# 436.2 — Compiler phải là một hệ thống query

Compiler không nên là một chuỗi function khổng lồ:

```text
compile(source) -> binary
```

Mà phải là:

```text
Query Database
```

với các query như:

```text
parse(file)
module(file)
resolve(name)
type_of(expr)
layout_of(type)
trait_impl(trait, type)
const_eval(expr)
lower(function)
codegen(function)
```

Điều này là nền tảng cho incremental compilation và LSP.

---

# 436.3 — Compiler database

Compiler database giữ:

```text
SourceFiles
PackageGraph
ModuleGraph
AST
SymbolTable
TypeTable
TraitTable
ComptimeResults
LayoutTable
MIR
IR
CodegenArtifacts
Diagnostics
```

Các entry được cache theo dependency.

---

# 436.4 — Source identity

Mỗi source file có:

```text
FileId
ContentHash
Path
PackageId
ModuleId
```

`FileId` là internal identity.

`ContentHash` dùng cho incremental compilation.

---

# 436.5 — Compilation unit

Compilation unit mặc định là module/function-level semantic unit tùy phase.

Không nhất thiết:

```text
1 source file = 1 object file
```

Compiler có quyền grouping để tối ưu.

---

# 436.6 — Package graph

Trước khi semantic compilation:

```text
workspace
 ↓
packages
 ↓
dependencies
 ↓
modules
```

phải được resolve.

---

# 436.7 — Module graph

Module graph chứa:

```text
imports
exports
visibility
re-exports
initialization dependencies
```

---

# 436.8 — Compilation phases

Các phase chính:

```text
P0  configuration
P1  source loading
P2  lexing
P3  parsing
P4  declaration collection
P5  name resolution
P6  type checking
P7  trait/generic solving
P8  ownership/effect checking
P9  comptime
P10 layout/ABI
P11 HIR → MIR
P12 MIR optimization
P13 MIR → LIR
P14 instruction selection
P15 register allocation
P16 machine emission
P17 object generation
P18 linking
P19 artifact validation
```

---

# 436.9 — Phase independence

Mỗi phase phải có:

```text
input contract
output contract
diagnostic contract
dependency contract
cache key
verification invariant
```

---

# 436.10 — Lexer

Input:

```text
UTF-8 bytes
```

Output:

```text
TokenStream
```

Token chứa:

```text
kind
span
literal/value
```

---

# 436.11 — Lexer must not type-check

Lexer chỉ nhận diện lexical structure.

Không quyết định:

```text
type
scope
trait
overload
```

---

# 436.12 — Parser

Parser:

```text
TokenStream → AST
```

Parser không thực hiện full semantic checking.

---

# 436.13 — Error-recovered AST

AST có thể chứa:

```text
ErrorNode
MissingToken
UnknownSyntax
```

để LSP tiếp tục hoạt động.

---

# 436.14 — AST ownership

AST là syntax representation.

Không nhúng quá nhiều backend-specific information vào AST.

---

# 436.15 — Declaration collection

Compiler quét module trước để thu:

```text
functions
structs
enums
traits
impls
constants
statics
type aliases
imports
```

---

# 436.16 — Two-pass declarations

Ví dụ:

```text
fn a() { b() }

fn b() {}
```

phải hợp lệ mà không phụ thuộc thứ tự source, nếu module semantics cho phép.

---

# 436.17 — Symbol table

Symbol:

```text
SymbolId
name
kind
module
visibility
span
declaration
generic parameters
```

---

# 436.18 — Name resolution

Resolution phải deterministic.

Không được phụ thuộc vào hash-map iteration order.

---

# 436.19 — Scope tree

Compiler tạo:

```text
GlobalScope
ModuleScope
FunctionScope
BlockScope
PatternScope
GenericScope
```

---

# 436.20 — Shadowing

Axiom cho phép local shadowing theo syntax đã định nghĩa.

Compiler phải resolve lexical scope trước khi type-check expression.

---

# 436.21 — Imports

Import resolution:

```text
local module
→ package
→ dependency
```

theo module graph.

---

# 436.22 — Visibility checking

Resolution phải kiểm tra:

```text
private
package
pub
```

ngay tại semantic boundary.

---

# 436.23 — HIR

AST không đủ tốt cho optimization.

Axiom tạo:

```text
HIR = High-level Intermediate Representation
```

HIR giữ semantic information.

---

# 436.24 — HIR mục tiêu

HIR phải dễ dùng cho:

```text
type checking
ownership
trait resolution
comptime
desugaring
semantic queries
```

---

# 436.25 — Syntax sugar lowering

Ví dụ:

```text
for x in items { ... }
```

được lowering thành iterator protocol tương ứng.

Tương tự:

```text
method call
operator
try
defer
syntactic shorthand
```

---

# 436.26 — Preserve source mapping

Mọi HIR node quan trọng phải giữ source origin:

```text
SourceSpan
Origin
ExpansionOrigin
```

để diagnostic/debugging.

---

# 436.27 — Type checking architecture

Type checker sử dụng:

```text
expected type
actual expression
constraints
environment
```

theo bidirectional checking.

---

# 436.28 — Inference variables

Ví dụ:

```text
x := foo()
```

Compiler tạo inference variable:

```text
T0
```

rồi giải constraints.

---

# 436.29 — Constraint system

Constraints có thể là:

```text
T == i32
T == U
T: Trait
T <: dyn Trait
```

và conversion constraints.

---

# 436.30 — Constraint solving

Solver phải deterministic.

Nếu nhiều solution hợp lệ nhưng không có rule ưu tiên rõ ràng:

```text
ambiguous
```

---

# 436.31 — No magical inference

Inference không được tự động tạo:

```text
arbitrary conversions
```

để làm expression compile.

---

# 436.32 — Type normalization

Compiler canonicalizes:

```text
aliases
generic substitutions
associated types
const parameters
```

thành canonical `TypeId`.

---

# 436.33 — Type interning

Equivalent canonical types dùng chung internal representation khi có thể.

Ví dụ:

```text
i32
i32
```

không cần tạo hàng nghìn type objects riêng.

---

# 436.34 — Trait solver

Trait solver nhận:

```text
Goal:
    T: Trait
```

và trả:

```text
Proven
Disproven
Ambiguous
Overflow
```

---

# 436.35 — Trait solver separation

Trait solver không được phụ thuộc backend.

Nó phải chạy trong:

```text
axiom check
LSP
comptime
codegen
```

---

# 436.36 — Generic substitution

Generic function:

```text
fn max<T: Ordered>(...)
```

sau inference:

```text
T = i32
```

tạo specialization request.

---

# 436.37 — Monomorphization request

Compiler tạo:

```text
InstanceKey {
    function
    type_arguments
    const_arguments
}
```

---

# 436.38 — Generic cache

Nếu cùng:

```text
foo<i32>
```

được gọi ở 100 nơi:

```text
1 specialization
```

trừ khi backend quyết định clone/outline.

---

# 436.39 — Generic recursion

Compiler phát hiện recursive instantiation.

Ví dụ:

```text
Foo<Foo<Foo<...>>>
```

vượt limit phải diagnostic.

---

# 436.40 — Method resolution

Method call:

```text
v.length()
```

được resolve theo:

```text
inherent methods
trait methods
extension methods
```

với priority rules deterministic.

---

# 436.41 — Struct-first method lowering

```text
v.length()
```

hạ xuống conceptual:

```text
length(v)
```

sau khi method resolution hoàn tất.

---

# 436.42 — Trait dispatch

Static:

```text
T: Trait
```

→ direct specialized function.

Dynamic:

```text
dyn Trait
```

→ vtable dispatch.

---

# 436.43 — Dynamic interface representation

Conceptual:

```text
DynObject {
    data_ptr
    vtable_ptr
}
```

Không có hidden dynamic dispatch.

---

# 436.44 — Ownership checking phase

Ownership checking chạy sau semantic type resolution đủ để biết:

```text
Copy
Drop
Move
Borrow/view
```

---

# 436.45 — Ownership flow graph

Compiler track:

```text
variable state
field state
scope
control-flow path
```

---

# 436.46 — Control-flow-aware ownership

Ví dụ:

```text
if condition {
    move x
}

use x
```

compiler phải merge flow states chính xác.

---

# 436.47 — Partial initialization

Compiler track:

```text
struct S {
    a initialized
    b uninitialized
}
```

để drop chính xác.

---

# 436.48 — Cleanup graph

Compiler xây cleanup edges cho:

```text
return
break
continue
panic
exception
scope exit
```

---

# 436.49 — `defer` lowering

`defer` được biến thành cleanup action.

Không cần runtime stack riêng nếu compiler có thể statically lower.

---

# 436.50 — Drop lowering

Conceptual:

```text
scope exit
 ↓
drop resources
 ↓
return
```

---

# 436.51 — Error propagation lowering

```text
x := try foo()
```

được lower thành control flow:

```text
call foo
inspect Result
Ok → continue
Err → return Err
```

Không cần exception machinery.

---

# 436.52 — Panic lowering

Panic mode:

```text
abort
```

→ direct panic/abort path.

Nếu:

```text
unwind
```

→ cleanup + unwind landing structures.

---

# 436.53 — Effect metadata

Compiler tracks optional effects:

```text
may_panic
may_allocate
may_block
may_io
unsafe
```

---

# 436.54 — Effect checking

Attributes như:

```text
@no_alloc
@no_panic
@no_block
```

được kiểm tra xuyên call graph khi semantics yêu cầu.

---

# 436.55 — Comptime phase

Comptime requests được xử lý qua semantic interpreter:

```text
HIR
→ Const IR
→ evaluate
→ ConstValue
```

---

# 436.56 — ConstValue

Represent:

```text
integer
float
bool
char
array
tuple
struct
enum
string
type
```

---

# 436.57 — Comptime cache

Cache key:

```text
function identity
arguments
const generics
target context
compiler version
dependencies
```

---

# 436.58 — Comptime failure

Nếu comptime evaluation fail:

```text
compile-time diagnostic
```

Không biến thành runtime panic.

---

# 436.59 — Layout phase

Layout engine nhận:

```text
TypeId
TargetDataModel
RepresentationAttributes
```

trả:

```text
Layout {
    size
    alignment
    fields
    offsets
    niches
}
```

---

# 436.60 — Layout cache

Layout của cùng:

```text
TypeId + Target
```

chỉ cần tính một lần.

---

# 436.61 — Recursive layout

Compiler phải detect:

```text
struct Node {
    next: Node
}
```

và reject nếu recursive value layout vô hạn.

Indirection giải quyết recursion.

---

# 436.62 — ABI lowering

Type layout được chuyển thành:

```text
ABIArgument
ABIReturn
```

theo target ABI.

---

# 436.63 — MIR

Sau HIR semantic validation:

```text
HIR → MIR
```

MIR là representation cho:

- control flow;
- explicit temporaries;
- ownership cleanup;
- calls;
- branches;
- memory operations.

---

# 436.64 — MIR basic block

Mỗi block:

```text
BlockId
instructions[]
terminator
```

---

# 436.65 — MIR terminators

Các loại chính:

```text
return
jump
branch
switch
call
unreachable
panic
invoke
```

---

# 436.66 — Explicit control flow

Không giữ high-level constructs nếu backend không cần.

Ví dụ:

```text
match
```

được lower thành branch/switch structure.

---

# 436.67 — SSA strategy

Axiom low-level optimization IR nên hỗ trợ SSA.

MIR không nhất thiết phải pure SSA nếu ownership representation dễ hơn.

---

# 436.68 — MIR memory model

MIR phân biệt:

```text
value
place
address
load
store
```

Điều này rất quan trọng với mô hình memory của Axiom.

---

# 436.69 — Place representation

Một `place` biểu diễn location có thể chứa value:

```text
local
field
array element
dereference
```

---

# 436.70 — Value/place separation

Ví dụ:

```text
x = y
```

phân biệt:

```text
read(y)
write(x)
```

tránh nhầm value với addressable storage.

---

# 436.71 — Bounds-check representation

Array/slice access ban đầu có:

```text
bounds_check
```

Optimizer có thể loại bỏ khi chứng minh được safety.

---

# 436.72 — Unsafe access

Unchecked access được đánh dấu:

```text
unsafe_load
unsafe_store
```

để optimizer không nhầm semantic contract.

---

# 436.73 — MIR verification

Sau lowering:

```text
verify_mir()
```

kiểm tra:

- SSA/def-use nếu áp dụng;
- block validity;
- type validity;
- terminators;
- ownership cleanup;
- unreachable states.

---

# 436.74 — Optimization pipeline

Mặc định:

```text
canonicalize
→ constant fold
→ simplify CFG
→ dead code elimination
→ inline
→ scalar replacement
→ bounds-check elimination
→ escape analysis
→ allocation optimization
→ loop optimization
→ vectorization
→ target lowering
```

Thứ tự chính xác có thể thay đổi theo optimization strategy.

---

# 436.75 — Optimization legality

Mỗi optimization phải respect:

```text
overflow semantics
floating-point semantics
memory model
atomic ordering
volatile
unsafe contracts
ABI
panic behavior
```

---

# 436.76 — Inlining

Inlining được quyết định bởi cost model.

Không inline tất cả.

---

# 436.77 — Generic optimization

Generic specializations có thể được optimize independently.

---

# 436.78 — Monomorphization bloat control

Compiler có thể:

```text
share identical generated code
outline cold paths
merge equivalent functions
```

nếu ABI/semantics cho phép.

---

# 436.79 — Escape analysis

Compiler phân loại allocation:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

theo BOOTSTRAP-423.

---

# 436.80 — Stack promotion

Nếu:

```text
heap allocation
+
NoEscape
```

compiler có thể chuyển thành stack storage.

---

# 436.81 — Allocation elimination

Nếu object chỉ tồn tại để truyền qua vài function:

```text
allocation
→ scalar values
```

nếu semantics cho phép.

---

# 436.82 — Register allocation

Target backend thực hiện:

```text
virtual registers
→ physical registers
```

Các chiến lược có thể:

```text
linear scan
graph coloring
hybrid allocator
```

Backend chọn dựa trên optimization profile.

---

# 436.83 — Calling convention lowering

Trước machine emission:

```text
Axiom call
→ target ABI call sequence
```

---

# 436.84 — Stack frame lowering

Compiler xác định:

```text
locals
spills
saved registers
outgoing arguments
alignment
cleanup state
```

---

# 436.85 — Instruction selection

Input:

```text
low-level IR
```

Output:

```text
MachineInstruction
```

Instruction selector target-specific.

---

# 436.86 — Target-independent IR

Phần lớn optimization phải chạy trước target-specific lowering.

Mục tiêu:

```text
one optimizer
many backends
```

---

# 436.87 — Target-specific lowering

Các phần target-specific:

```text
SIMD
atomic instructions
calling convention
addressing modes
ABI
register classes
```

---

# 436.88 — Instruction legalization

Nếu IR có operation target không hỗ trợ:

```text
operation
→ legal instruction sequence
```

---

# 436.89 — Instruction scheduling

Backend có thể reorder instructions để tận dụng pipeline CPU nhưng phải respect:

```text
dependencies
memory ordering
volatile
atomic
exceptions/panic
```

---

# 436.90 — Register allocation verification

Sau allocation phải kiểm tra:

```text
no conflicting registers
valid spills
valid stack slots
ABI preserved registers
```

---

# 436.91 — Machine instruction representation

```text
MachineInstruction {
    opcode
    operands
    flags
    source_location
}
```

---

# 436.92 — Machine encoding

Theo BOOTSTRAP-420:

```text
MachineInstruction
→ EncodedInstruction
```

với:

```text
bytes
fixups
size
```

---

# 436.93 — Object generation

Backend tạo:

```text
sections
symbols
relocations
debug info
```

---

# 436.94 — Link phase

Compiler driver đưa object graph vào Axiom linker:

```text
objects
+
static archives
+
system libraries
→
linked image
```

---

# 436.95 — Linker is separate

Compiler backend không được biết toàn bộ executable layout.

Linker chịu trách nhiệm:

```text
symbol resolution
layout
relocations
imports
exports
entry point
```

---

# 436.96 — Artifact validation

Sau linking:

```text
validate_artifact()
```

kiểm tra:

```text
headers
entry point
sections
relocations
symbol consistency
architecture
```

---

# 436.97 — Compiler pipeline error boundaries

Nếu phase fail:

```text
parse failure
→ no semantic compile
```

Nhưng diagnostic recovery có thể tiếp tục để tìm thêm lỗi.

---

# 436.98 — Semantic invalidation

Thay đổi source chỉ invalidate các query phụ thuộc.

Ví dụ:

```text
function body changed
```

có thể invalidate:

```text
MIR
optimization
codegen
object
```

nhưng không nhất thiết invalidate:

```text
public API
downstream type checking
```

---

# 436.99 — Public/private dependency

Compiler graph phân biệt:

```text
semantic dependency
ABI dependency
implementation dependency
```

---

# 436.100 — Public interface artifact

Có thể cache:

```text
package.api
```

gồm semantic public declarations.

Downstream compiler không cần parse toàn bộ dependency source.

---

# 436.101 — Binary interface artifact

Native packages có thể cung cấp:

```text
ABI metadata
symbols
layouts
calling conventions
```

để FFI/linking.

---

# 436.102 — Compilation caching levels

```text
L0 source
L1 AST
L2 semantic/HIR
L3 comptime
L4 MIR
L5 optimized IR
L6 object
L7 linked artifact
```

Không phải project nào cũng cần lưu mọi level.

---

# 436.103 — Cache selection

Release builds có thể cache sâu.

Development builds ưu tiên latency thấp.

---

# 436.104 — Query invalidation

Mỗi query khai báo dependencies.

Ví dụ:

```text
type_of(expr)
depends on:
    AST(expr)
    resolved symbols
    generic environment
```

---

# 436.105 — Parallel query evaluation

Independent queries có thể chạy parallel.

Compiler database phải tránh deadlock.

---

# 436.106 — Cycle handling

Semantic cycles như:

```text
trait A depends on B
B depends on A
```

phải được solver xử lý theo rule rõ ràng.

Internal query cycles không được làm compiler deadlock.

---

# 436.107 — Cancellation

Compilation/LSP query có thể cancel.

Cancellation không được corrupt database.

---

# 436.108 — Thread-safe compiler database

Compiler database phải hỗ trợ concurrent reads.

Mutations được serialize/controlled.

---

# 436.109 — Deterministic query results

Query result không được phụ thuộc:

```text
thread scheduling
hash-map order
filesystem enumeration order
```

---

# 436.110 — Hashing

Axiom dùng stable hashing cho:

```text
source
semantic entities
types
comptime
IR
artifacts
```

Cryptographic hash có thể dùng cho artifact identity.

---

# 436.111 — Incremental hash strategy

Không hash lại toàn bộ workspace khi một file nhỏ thay đổi.

File-level content hashes kết hợp dependency hashes.

---

# 436.112 — Compiler memory management

Compiler itself có thể sử dụng GC/arena/reference counting nội bộ nếu implementation thấy phù hợp.

Điều này **không ảnh hưởng language runtime**.

---

# 436.113 — Compiler arena

AST/HIR/IR thường phù hợp với arena allocation:

```text
parse
→ arena
→ discard entire compilation state
```

---

# 436.114 — Compiler ownership

Compiler implementation có thể dùng ownership model riêng phù hợp host implementation.

Language rule “no mandatory GC” áp dụng cho **Axiom programs**, không áp dụng bắt buộc cho compiler implementation.

---

# 436.115 — Diagnostic propagation

Mỗi phase trả:

```text
Success
SuccessWithDiagnostics
Failure
```

Không dùng exception-like hidden control flow làm semantic requirement.

---

# 436.116 — Error tolerance

Compiler có thể tiếp tục sau non-fatal errors.

Nhưng backend không được generate executable được đánh dấu valid nếu semantic errors chưa được giải quyết.

---

# 436.117 — Partial compilation

`axiom check` có thể tạo semantic model dù source lỗi.

`axiom build` không được phát hành artifact thành công nếu có error diagnostics.

---

# 436.118 — Error severity gate

```text
warning → build allowed
error → build rejected
```

trừ explicit experimental mode.

---

# 436.119 — AI semantic interface

Compiler database expose:

```text
query_symbol
query_type
query_definition
query_references
query_members
query_traits
query_layout
query_diagnostics
query_cfg
```

---

# 436.120 — AI code repair

AI agent có thể:

```text
edit source
→ axiom check --json
→ query semantic model
→ apply fix
```

Compiler không tự quyết định code architecture thay AI.

---

# 436.121 — Compiler-generated suggestions

Compiler chỉ cung cấp:

```text
fact
diagnostic
fix
semantic information
```

Không cố gắng viết cả application cho developer.

---

# 436.122 — Debug pipeline

Compiler phải có mapping:

```text
source
→ HIR
→ MIR
→ machine instruction
```

để debugger có thể map native instruction về source.

---

# 436.123 — Debug location

Mỗi instruction có thể giữ:

```text
source file
line
column
inline origin
```

---

# 436.124 — Inline debug chain

Nếu:

```text
foo()
```

được inline vào:

```text
bar()
```

debug info vẫn giữ:

```text
foo source
→ inlined into bar
```

---

# 436.125 — Panic source location

Panic có thể report:

```text
file
line
function
```

nếu debug information/runtime support enabled.

---

# 436.126 — Async lowering

Async function:

```text
async fn foo()
```

được lower thành state machine.

Pipeline:

```text
HIR async
→ MIR state machine
→ ordinary codegen
```

---

# 436.127 — Async frame layout

Frame chứa:

```text
state
locals surviving suspension
future result
cleanup state
```

---

# 436.128 — Async allocation elimination

Nếu future không escape:

```text
future frame
→ stack
```

có thể được tối ưu.

---

# 436.129 — Closure lowering

Closure:

```text
|x| x + y
```

được lower thành:

```text
code pointer
+
environment
```

---

# 436.130 — Closure environment

Chỉ capture những values thực sự được sử dụng.

Compiler xác định:

```text
capture by value
capture by view/reference
```

theo ownership semantics.

---

# 436.131 — Closure allocation

Heap allocation không bắt buộc.

Escape analysis quyết định.

---

# 436.132 — Iterator lowering

Iterator syntax có thể được monomorphized/inlined.

Không tạo virtual dispatch nếu static type biết concrete iterator.

---

# 436.133 — Dynamic iterator

Nếu dùng dynamic trait:

```text
dyn Iterator
```

thì dispatch dynamic là explicit.

---

# 436.134 — Match lowering

Compiler chọn:

```text
jump table
binary decision tree
linear branches
bit-test
```

tùy pattern/cost model.

---

# 436.135 — Pattern exhaustiveness

Đã được type checker xác nhận trước lowering.

Backend không phải tự hiểu semantic pattern matching.

---

# 436.136 — Switch lowering

Enum discriminant có thể lower thành:

```text
integer switch
```

với niche optimization nếu layout engine cho phép.

---

# 436.137 — String optimization

String literals được đặt trong read-only data khi target cho phép.

Không runtime allocation cho literal.

---

# 436.138 — UTF-8 invariant

Compiler source/string literal parser phải preserve UTF-8 bytes chính xác.

---

# 436.139 — Bounds-check elimination

Compiler có thể prove:

```text
0 <= i < len
```

và loại bỏ check.

Nếu không chứng minh được:

```text
check remains
```

---

# 436.140 — No speculative unsafe elimination

Compiler không được loại bounds check chỉ vì “có vẻ đúng”.

Phải dựa trên proven constraints/defined optimization rule.

---

# 436.141 — Alias analysis

Alias analysis dùng conservative assumptions.

Compiler chỉ áp dụng `noalias` khi contract hợp lệ.

---

# 436.142 — Volatile

Volatile accesses không được optimize away/reorder ngoài semantics cho phép.

---

# 436.143 — Atomic lowering

Atomic operation:

```text
MIR Atomic
→ target atomic instruction/library fallback
```

theo target capabilities.

---

# 436.144 — Unsupported atomic

Nếu target không hỗ trợ operation:

```text
compiler/runtime fallback
```

nếu ABI/runtime contract cho phép.

Nếu không:

```text
compile-time error
```

---

# 436.145 — SIMD lowering

Portable SIMD:

```text
vector operation
→ target SIMD
```

hoặc scalar fallback khi semantics/library cho phép.

---

# 436.146 — CPU feature specialization

Compiler có thể hỗ trợ:

```text
target feature
```

để specialize code.

Không được phát sinh illegal instruction trên target không hỗ trợ feature.

---

# 436.147 — Function multiversioning

Có thể hỗ trợ sau:

```text
generic version
SSE/AVX version
NEON version
```

dispatch explicit/runtime-supported.

---

# 436.148 — Link-time optimization

LTO là optional compiler/linker mode.

Pipeline:

```text
multiple MIR/LIR units
→ global optimization
→ machine code
```

hoặc object-level optimization tùy implementation.

---

# 436.149 — Thin LTO-like strategy

Có thể dùng summary-based optimization để giảm memory.

Không bắt buộc phải copy mô hình LLVM.

---

# 436.150 — Whole-program optimization

Compiler có thể loại bỏ:

```text
unused private functions
unused generic instances
unused runtime components
```

khi visibility/linkage cho phép.

---

# 436.151 — Dead code elimination

Dead code elimination phải tôn trọng:

```text
volatile
extern
exported symbol
constructor/init side effects
FFI visibility
```

---

# 436.152 — Startup lowering

Native executable có:

```text
platform entry
→ Axiom startup
→ runtime initialization
→ main
→ exit
```

Nếu freestanding:

```text
platform entry
→ user entry
```

---

# 436.153 — Runtime initialization

Chỉ initialize runtime components được sử dụng.

---

# 436.154 — Global initialization

Static/global initialization phải được xác định rõ:

```text
constant initialization
runtime initialization
```

---

# 436.155 — Initialization order

Không cho phép initialization order phụ thuộc filesystem/module enumeration.

Dependency graph quyết định thứ tự.

---

# 436.156 — Global destructor

Không mặc định tạo hidden global destructor registry.

Nếu platform/runtime cần cleanup, mechanism phải explicit.

---

# 436.157 — Linker garbage collection

Axiom linker có thể loại bỏ sections không reachable.

---

# 436.158 — Root set

Linker roots:

```text
entry point
exports
externally referenced symbols
runtime-required symbols
explicit retain
```

---

# 436.159 — Section-level elimination

Codegen nên emit functions/data vào sections đủ granular để linker có thể loại bỏ unused pieces.

---

# 436.160 — Symbol visibility

Backend phải encode:

```text
local
hidden/internal
global
weak
exported
```

theo object format.

---

# 436.161 — Native library output

Compiler có thể dừng sau:

```text
object
static library
dynamic library
```

không nhất thiết executable.

---

# 436.162 — Build graph artifacts

Mỗi node có artifact type:

```text
source
semantic
IR
object
archive
shared library
executable
WASM
```

---

# 436.163 — Artifact dependency graph

Ví dụ:

```text
libA source
   ↓
libA object
   ↓
libA.a
   ↓
app object
   ↓
app.exe
```

---

# 436.164 — Compiler/linker boundary

Compiler chịu:

```text
source → object
```

Linker chịu:

```text
objects → final image
```

Build driver orchestrates cả hai.

---

# 436.165 — Linker script/config

Axiom có thể có linker configuration cho advanced users:

```text
sections
memory regions
entry
exports
```

nhưng default linker layout tự động.

---

# 436.166 — Embedded/freestanding

Embedded users có thể cung cấp:

```text
link layout
startup symbol
memory regions
interrupt vectors
```

mà không cần standard OS runtime.

---

# 436.167 — WASM pipeline

WASM không cần giả lập native object pipeline hoàn toàn.

Có backend:

```text
MIR
→ WASM IR
→ WASM binary
```

nhưng vẫn dùng chung semantic/frontend infrastructure.

---

# 436.168 — WASM ABI

ABI layer xác định:

```text
exports
imports
linear memory
function ABI
string representation
```

---

# 436.169 — Mobile targets

iOS/Android target khác nhau ở:

```text
ABI
object format
startup
system frameworks/libraries
code signing/package integration
```

Language semantics không thay đổi.

---

# 436.170 — Code signing boundary

Code signing không phải semantic compiler feature.

Build/package pipeline tích hợp platform signing khi cần.

---

# 436.171 — Compiler architecture dependency rule

```text
Frontend
```

không được import:

```text
ELFWriter
PEWriter
MachOWriter
```

Semantic layers phải target-neutral.

---

# 436.172 — Backend dependency rule

Backend có thể phụ thuộc:

```text
ABI
TargetDataModel
MachineISA
ObjectFormat
```

nhưng không nên phụ thuộc parser.

---

# 436.173 — Linker dependency rule

Linker không cần hiểu:

```text
Axiom syntax
AST
type checker
ownership
```

Nó chỉ xử lý object-level contracts.

---

# 436.174 — Testing boundaries

Mỗi phase có test riêng.

Ví dụ:

```text
Parser test
```

không cần invoke native linker.

---

# 436.175 — Compiler bootstrap implementation order

Implementation order được khóa thành:

```text
1. Source/lexer
2. Parser
3. AST
4. Symbols/modules
5. Type system
6. Traits/generics
7. Ownership
8. Const/comptime
9. HIR
10. MIR
11. Interpreter/reference evaluator
12. x86-64 backend
13. ELF object writer
14. Axiom linker
15. Linux executable
16. PE/COFF
17. Windows executable
18. AArch64
19. Mach-O
20. WASM
21. LSP
22. self-hosting
```

---

# 436.176 — Bootstrap compiler scope

Stage đầu tiên không cần full language.

Bootstrap subset phải đủ để viết compiler tiếp theo.

Subset gồm:

```text
primitive types
struct
enum
functions
arrays
slices
modules
if
while
match
generic basics
traits basics
Result
Option
explicit allocation
```

Các feature nâng cao có thể bootstrap sau.

---

# 436.177 — Bootstrap artifact

Mục tiêu đầu tiên:

```text
axiom-bootstrap
```

có thể:

```text
compile simple Axiom
→ x86-64 ELF
```

---

# 436.178 — First executable

Canonical test:

```text
fn main() -> i32 {
    42
}
```

Pipeline:

```text
parse
→ typecheck
→ MIR
→ x86-64
→ ELF
→ link
→ execute
→ 42
```

---

# 436.179 — Second milestone

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(20, 22)
}
```

Expected:

```text
42
```

---

# 436.180 — Third milestone

Struct-first method:

```text
struct Counter {
    value: i32
}

fn increment(self: Counter) -> Counter {
    Counter { value: self.value + 1 }
}
```

Compiler phải resolve:

```text
counter.increment()
```

thành method call chính xác.

---

# 436.181 — Fourth milestone

Trait:

```text
trait Value {
    fn value(self) -> i32
}

impl Value for Counter {
    fn value(self) -> i32 {
        self.value
    }
}
```

Static dispatch phải compile thành direct call sau monomorphization/resolution.

---

# 436.182 — Fifth milestone

Ownership:

```text
let a := Resource(...)
let b := a
```

Compiler phải hiểu:

```text
a → moved
b → owner
```

và emit cleanup cho `b`.

---

# 436.183 — Sixth milestone

Result:

```text
fn foo() -> Result<i32, Error>
```

`try` lowering thành CFG.

---

# 436.184 — Seventh milestone

Comptime:

```text
const X: i32 = 20 + 22
```

được evaluate compile-time.

---

# 436.185 — Eighth milestone

Generic:

```text
fn identity<T>(x: T) -> T {
    x
}
```

specialization:

```text
identity<i32>
```

---

# 436.186 — Ninth milestone

Concurrency:

```text
spawn(...)
join(...)
```

lower thành runtime/thread ABI.

---

# 436.187 — Tenth milestone

Self-hosting:

```text
Axiom compiler source
→ bootstrap compiler
→ native Axiom compiler
→ rebuild itself
```

---

# 436.188 — Compiler repository structure

Đề xuất:

```text
compiler/
├── driver/
├── source/
├── lexer/
├── parser/
├── ast/
├── symbols/
├── modules/
├── types/
├── traits/
├── generics/
├── ownership/
├── comptime/
├── hir/
├── mir/
├── optimizer/
├── abi/
├── target/
├── codegen/
│   ├── x86_64/
│   ├── aarch64/
│   └── wasm/
├── object/
│   ├── elf/
│   ├── coff/
│   └── macho/
├── linker/
├── runtime/
├── diagnostics/
├── lsp/
├── formatter/
└── tests/
```

---

# 436.189 — Core compiler libraries

Internal APIs nên được chia:

```text
libaxiom_source
libaxiom_lexer
libaxiom_parser
libaxiom_semantic
libaxiom_ir
libaxiom_codegen
libaxiom_object
libaxiom_linker
```

Tên thực tế có thể thay đổi.

---

# 436.190 — No circular architecture

Dependency direction:

```text
source
 ↓
lexer
 ↓
parser
 ↓
semantic
 ↓
HIR
 ↓
MIR
 ↓
optimizer
 ↓
codegen
 ↓
object
 ↓
linker
```

Không được có:

```text
parser → linker
type checker → ELF writer
lexer → optimizer
```

---

# 436.191 — Compiler service API

LSP và CLI dùng:

```text
CompilerSession
CompilerDatabase
BuildSession
DiagnosticStore
```

thay vì gọi compiler binary con liên tục.

---

# 436.192 — One-shot API

Vẫn phải hỗ trợ:

```text
compile(project)
```

trong một process.

Daemon không phải dependency.

---

# 436.193 — Incremental API

Compiler database có:

```text
set_file()
invalidate()
query()
```

---

# 436.194 — Snapshot model

LSP request sử dụng immutable-ish project snapshot.

Một request không bị thay đổi giữa chừng bởi editor event mới.

---

# 436.195 — Compiler snapshot isolation

Nếu editor gửi:

```text
version 10
```

rồi:

```text
version 11
```

kết quả version 10 không được ghi đè semantic state của version 11.

---

# 436.196 — Architecture invariants

Các invariant cuối cùng của BOOTSTRAP-436:

1. Compiler có semantic query architecture.
2. AST và semantic representation tách biệt.
3. HIR giữ semantic information.
4. MIR biểu diễn explicit control/data flow.
5. Backend không phụ thuộc frontend.
6. Linker không phụ thuộc semantic compiler.
7. Incremental compilation là first-class.
8. Query dependencies được tracking.
9. Cache key phải chứa đầy đủ semantic inputs.
10. Cache hit tương đương cache miss.
11. Deterministic query results.
12. Parallel compilation không thay đổi semantics.
13. LSP dùng compiler semantic database.
14. Ownership được lower thành explicit cleanup.
15. `Result` propagation thành explicit control flow.
16. Async thành state machine.
17. Closure thành code + environment.
18. Generic static dispatch được monomorphize.
19. Dynamic dispatch chỉ xuất hiện khi explicit.
20. Layout engine độc lập với parser.
21. ABI lowering độc lập với language syntax.
22. Instruction selection target-specific.
23. Optimization tôn trọng language memory/overflow/atomic semantics.
24. Bounds checks chỉ được loại khi compiler có căn cứ hợp lệ.
25. Unsafe không được tự động biến thành safe.
26. Machine encoding dùng backend riêng.
27. Object generation dùng object writer riêng.
28. Linking dùng Axiom linker.
29. Final native artifact không cần LLVM/GCC/Clang.
30. WASM có backend riêng nhưng dùng chung frontend.
31. Freestanding compilation không cần std runtime.
32. Compiler daemon optional.
33. One-shot compiler luôn hoạt động.
34. Compiler implementation có thể self-host.
35. Mỗi phase có contract và verifier.
36. Error recovery không được tạo executable thành công khi còn semantic errors.
37. Compiler có thể hoạt động trên source chưa hoàn chỉnh cho LSP.
38. Compiler database không phụ thuộc thứ tự filesystem/hash-map.
39. Bootstrap path phải có khả năng tạo executable native đầu tiên.
40. Toàn bộ architecture phải cho phép thay backend mà không viết lại frontend.

---

# BOOTSTRAP-436.197 — Compiler architecture đã khóa

Kiến trúc Axiom hiện có hình dạng:

```text
                    ┌───────────────┐
                    │ Source/Build  │
                    └───────┬───────┘
                            ▼
                    ┌───────────────┐
                    │ Lexer/Parser  │
                    └───────┬───────┘
                            ▼
                         AST
                            │
                    ┌───────▼────────┐
                    │ Semantic DB    │◄──── LSP / AI
                    └───────┬────────┘
                            ▼
                    Name Resolution
                            ▼
                     Type / Trait
                            ▼
                  Ownership / Effects
                            ▼
                       Comptime
                            ▼
                      Layout / ABI
                            ▼
                           HIR
                            ▼
                           MIR
                            ▼
                     Optimization
                            ▼
                         Low IR
                            ▼
                    ┌───────┴────────┐
                    ▼                ▼
                 x86-64           AArch64
                    │                │
                    └───────┬────────┘
                            ▼
                    Machine Encoder
                            ▼
                       Object File
                            ▼
                     Axiom Linker
                            ▼
                    EXE / ELF / Mach-O
                         / WASM
```

**BOOTSTRAP-436 hoàn tất.**

---

# BOOTSTRAP-437 — INTERMEDIATE REPRESENTATION (HIR/MIR/LIR), SSA, MEMORY SSA, CONTROL FLOW & OPTIMIZATION CONTRACT

Đây là bước tiếp theo.

Sau khi pipeline compiler đã được khóa, cần khóa **IR thật sự** trước khi bắt đầu thiết kế optimizer và backend implementation.

Trọng tâm của BOOTSTRAP-437:

```text
AST
 ↓
HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine IR
```

và đặc biệt phải giải quyết dứt điểm:

- SSA;
- memory SSA;
- basic block;
- CFG;
- phi values;
- load/store;
- alias;
- aggregate lowering;
- calling convention;
- pointer/address representation;
- atomic/volatile;
- panic/unwind;
- async state machine;
- ownership cleanup;
- optimization boundaries;
- debug/source mapping;
- representation đủ đơn giản để compiler tự implement nhưng đủ mạnh để đạt hiệu năng C/C++.

**BOOTSTRAP-437 bắt đầu từ đây.**