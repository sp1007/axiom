# BOOTSTRAP-218 — AXIOM CORE SPECIFICATION IMPLEMENTATION BLUEPRINT

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước chuyển quan trọng: từ **“Axiom đã được thiết kế”** sang **“một team compiler có thể bắt tay viết compiler ngay mà không phải tự suy diễn kiến trúc”**.

Mục tiêu của 218 là khóa:

- thứ tự triển khai compiler;
- interface giữa các compiler stage;
- dữ liệu nào được phép đi qua boundary;
- invariant bắt buộc;
- test gate;
- bootstrap strategy;
- vertical slice đầu tiên;
- đường đi từ compiler bootstrap → compiler native → self-hosted;
- cấu trúc repository;
- tiêu chí “phase hoàn thành thật sự”.

---

# 1. Nguyên tắc triển khai

Axiom không nên bắt đầu bằng việc viết toàn bộ frontend rồi cuối cùng mới thử codegen.

Thay vào đó phải có **vertical slice** rất sớm:

```text
Axiom source
    ↓
Lexer
    ↓
Parser
    ↓
Resolver
    ↓
Type checker
    ↓
HIR
    ↓
MIR
    ↓
Ownership verifier
    ↓
Reference interpreter
    ↓
LLVM backend
    ↓
native executable
```

Sau đó từng bước thay thế:

```text
LLVM backend
    ↓
Axiom LIR
    ↓
Axiom machine backend
    ↓
Axiom object writer
    ↓
Axiom linker
```

Cuối cùng:

```text
bootstrap compiler
        ↓
native Axiom compiler
        ↓
self-hosted compiler
```

### Quy tắc quan trọng

**Không được chờ đến khi compiler hoàn chỉnh mới chạy chương trình Axiom đầu tiên.**

Compiler phải có các milestone:

```text
M0: parse được
M1: type-check được
M2: interpret được
M3: compile được native executable
M4: compile được chính compiler
M5: self-host
```

---

# 2. Kiến trúc repository

Repository chuẩn đề xuất:

```text
axiom/
├── compiler/
│   ├── lexer/
│   ├── syntax/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── mir/
│   ├── ownership/
│   ├── capability/
│   ├── effects/
│   ├── patterns/
│   ├── async/
│   ├── comptime/
│   ├── interpreter/
│   ├── opt/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   ├── object/
│   ├── linker/
│   ├── diagnostics/
│   ├── source_map/
│   └── driver/
│
├── runtime/
│   ├── core/
│   ├── allocator/
│   ├── panic/
│   ├── unwind/
│   ├── thread/
│   ├── async/
│   └── platform/
│
├── std/
│   ├── core/
│   ├── collections/
│   ├── strings/
│   ├── io/
│   ├── fs/
│   ├── net/
│   ├── sync/
│   ├── process/
│   ├── math/
│   ├── tensor/
│   └── os/
│
├── targets/
│   ├── x86_64-windows/
│   ├── x86_64-linux/
│   ├── aarch64-linux/
│   ├── aarch64-macos/
│   ├── wasm32/
│   └── ...
│
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── type/
│   ├── traits/
│   ├── ownership/
│   ├── capability/
│   ├── effects/
│   ├── interpreter/
│   ├── codegen/
│   ├── abi/
│   ├── linker/
│   ├── conformance/
│   ├── diagnostics/
│   └── programs/
│
├── docs/
│   ├── spec/
│   ├── design/
│   └── implementation/
│
├── tools/
│   ├── ax/
│   ├── axc/
│   └── test-runner/
│
└── bootstrap/
    ├── stage0/
    ├── stage1/
    └── stage2/
```

Không nhất thiết phải dùng đúng tên thư mục này, nhưng **dependency direction phải được giữ**.

---

# 3. Compiler dependency DAG

Không được để compiler biến thành một dependency graph vòng tròn.

Core dependency:

```text
Source
  ↓
Lexer
  ↓
Syntax
  ↓
Parser
  ↓
AST
  ↓
Resolver
  ↓
TypeDB
  ↓
TraitDB
  ↓
HIR
  ↓
MIR
  ↓
Verification
  ↓
Verified MIR
  ↓
OptIR
  ↓
ABI
  ↓
LIR
  ↓
Machine IR
  ↓
Object
  ↓
Link
```

Các subsystem phụ thuộc:

```text
Diagnostics ────────────────┐
SourceMap ──────────────────┤
CompilerDB ─────────────────┤
                             ↓
mọi semantic subsystem
```

Nhưng:

```text
Backend
  ✗ không được phụ thuộc Parser

Linker
  ✗ không được phụ thuộc TypeChecker

Optimizer
  ✗ không được tự parse source

Interpreter
  ✗ không được tự resolve source

Runtime
  ✗ không được quyết định semantic ownership
```

---

# 4. Phase 0 — Bootstrap Environment

## Mục tiêu

Có thể build compiler đầu tiên bằng một implementation language tạm thời.

Trong bootstrap có thể dùng:

- C++
- Rust
- hoặc ngôn ngữ implementation phù hợp khác.

LLVM/LLD được phép sử dụng.

Nhưng chúng chỉ là **bootstrap implementation dependency**, không phải semantic dependency của Axiom.

### Stage 0

```text
axiomc-bootstrap
    ↓
LLVM IR
    ↓
LLVM
    ↓
LLD/system linker
    ↓
native executable
```

### Gate

Phải build được:

```text
hello.ax
```

thành:

```text
hello.exe
```

hoặc ELF tương ứng.

---

# 5. Phase 1 — Lexer

Lexer phải là **lossless-aware**.

Output không chỉ:

```text
IDENT
NUMBER
STRING
```

mà phải giữ:

```text
TokenKind
SourceSpan
Trivia
RawText
LogicalPosition
```

Ví dụ:

```axiom
let x = 42
```

phải có khả năng tái dựng source tương đương.

### Gate

Test:

- Unicode UTF-8;
- identifier;
- keyword;
- numeric literal;
- string;
- byte string;
- comment;
- newline;
- indentation;
- invalid UTF-8;
- malformed token;
- source mapping.

Không được tiến sang parser nếu lexer chưa có source-span chính xác.

---

# 6. Phase 2 — Lossless Parser

Parser tạo:

```text
Lossless Syntax Tree
```

sau đó mới hạ xuống AST.

Đây là điểm quan trọng cho:

- formatter;
- IDE;
- refactoring;
- diagnostics;
- AI tooling.

Parser phải recovery được:

```axiom
fn foo(
    let x: i32
```

thay vì chết toàn bộ compilation.

### Gate

Parser phải xử lý:

- function;
- struct;
- enum;
- trait;
- impl;
- generic;
- expression;
- pattern;
- match;
- closures;
- async;
- attributes;
- modules;
- imports.

---

# 7. Phase 3 — AST

AST là semantic-friendly representation.

Không để AST trở thành “IR thứ hai”.

Ví dụ:

```text
FunctionDecl
 ├── Name
 ├── GenericParams
 ├── Parameters
 ├── ReturnType
 ├── Attributes
 └── Body
```

AST vẫn giữ source provenance.

### Gate

AST phải represent được toàn bộ Core v1 syntax.

---

# 8. Phase 4 — Name Resolution

Resolution phải deterministic.

Pipeline:

```text
Package
 ↓
Module
 ↓
Imports
 ↓
Declarations
 ↓
Scopes
 ↓
Names
 ↓
Definitions
```

Mỗi name phải resolve thành:

```text
DeclarationId
```

không giữ string name làm identity.

Ví dụ:

```axiom
foo(x)
```

sau resolution:

```text
Call {
    function: FunctionId(123),
    argument: ...
}
```

### Gate

Phải xử lý:

- lexical scope;
- module;
- import;
- shadowing;
- overload;
- methods;
- extension methods;
- generic declarations;
- visibility;
- ambiguity.

**Ambiguous resolution = error.**

Không heuristic.

---

# 9. Phase 5 — Type System

Đây là một trong những phase lớn nhất.

TypeDB:

```text
TypeId
```

phải là interned semantic identity.

Ví dụ:

```text
i32
Vec<i32>
Option<i32>
Result<i32, Error>
```

không được tạo hàng nghìn object type trùng nhau.

### Type checking

```text
AST
 ↓
Resolve
 ↓
Infer
 ↓
Unify
 ↓
Trait constraints
 ↓
Typed HIR
```

### Gate

Phải chứng minh:

- assignment;
- function call;
- generic;
- enum;
- pattern;
- operator;
- indexing;
- method call;
- closure;
- async;
- `view`;
- `mut_view`;
- casts;
- `Option`;
- `Result`.

---

# 10. Phase 6 — Trait Solver

Trait solver nên được tách riêng.

Input:

```text
TraitGoal
```

Output:

```text
Proven
NotProven
Ambiguous
Error
```

Không được có trạng thái:

```text
ProbablyYes
```

Ví dụ:

```axiom
T: Ord
```

solver phải xác định chính xác.

### Gate

Test:

- trait implementation;
- associated type;
- default method;
- generic constraints;
- operator traits;
- blanket impl;
- coherence;
- ambiguity;
- recursion;
- cycle;
- specialization policy.

---

# 11. Phase 7 — HIR

HIR là nơi Axiom bắt đầu có semantic structure rõ ràng.

AST:

```text
what programmer wrote
```

HIR:

```text
what program means
```

Ví dụ method:

```axiom
v.length()
```

HIR:

```text
Call(
    function = length,
    receiver = v
)
```

Extension method, syntactic sugar, implicit ephemeral view... được normalize tại đây.

### Gate

HIR phải loại bỏ những ambiguity/syntax sugar không cần thiết.

---

# 12. Phase 8 — MIR

MIR là **semantic execution representation**.

Ví dụ:

```axiom
let x = foo()
if x > 0 {
    bar(x)
}
```

hạ thành:

```text
bb0:
    x = Call foo
    t0 = Compare x, 0
    Branch t0 -> bb1, bb2

bb1:
    Call bar(x)
    Goto bb3

bb2:
    Goto bb3
```

MIR phải explicit:

- control flow;
- ownership;
- initialization;
- move;
- drop;
- capability;
- effects;
- async suspension;
- resource operations.

### Gate

MIR phải có:

```text
CFG
Place
Operand
RValue
Statement
Terminator
```

và không còn phụ thuộc trực tiếp vào syntax.

---

# 13. Phase 9 — Ownership Verification

Đây là **correctness boundary đầu tiên thực sự quan trọng**.

Input:

```text
MIR
```

Output:

```text
OwnershipVerifiedMIR
```

Kiểm tra:

```text
Initialized?
Moved?
PartiallyMoved?
Dropped?
Copy?
Move?
Drop?
```

Ví dụ:

```axiom
let a = make();
let b = a;
print(a);       // ERROR
```

Compiler phải bắt được trước codegen.

### Gate bắt buộc

Negative tests:

- use-after-move;
- double move;
- double drop;
- use-after-drop;
- partial move;
- custom Drop;
- return-path cleanup;
- panic cleanup;
- loop;
- branch merge;
- early return.

---

# 14. Phase 10 — Capability Verification

Ownership chưa đủ.

Phải kiểm tra:

```text
view
mut_view
alias
provenance
region
lifetime
relocation
```

Ví dụ:

```axiom
let p = view(x)
drop(x)
use(p)
```

→ reject.

Ví dụ:

```axiom
let a = mut_view(x)
let b = mut_view(x)
```

→ reject.

Nhưng:

```axiom
let a = mut_view(x.left)
let b = mut_view(x.right)
```

có thể accept nếu compiler chứng minh:

```text
DISJOINT
```

### Gate

Không được có:

```text
UNKNOWN → DISJOINT
```

Đây là invariant cực kỳ quan trọng.

---

# 15. Phase 11 — Effect Verification

Compiler xây:

```text
EffectInfo
```

Ví dụ:

```text
pure
read
write
allocate
deallocate
drop
atomic
volatile
io
foreign
panic
synchronize
```

Mục tiêu chính không phải để “làm ngôn ngữ functional”.

Mục tiêu là optimizer biết:

> Có được phép reorder/eliminate operation này không?

Ví dụ:

```text
IO
```

không được biến thành dead code chỉ vì return value không được sử dụng.

---

# 16. Phase 12 — Async Lowering

Async chưa cần executor.

Compiler chỉ biến:

```axiom
async fn foo()
```

thành state machine.

Ví dụ:

```text
FutureState {
    state
    local_a
    local_b
}
```

và:

```text
poll()
```

### Gate

Phải kiểm tra:

- values live across await;
- view live across await;
- Send;
- executor migration;
- guard;
- cancellation;
- Drop.

Executor để library/runtime xử lý sau.

---

# 17. Phase 13 — Comptime

Comptime VM:

```text
Axiom source
    ↓
Typed HIR
    ↓
Comptime MIR
    ↓
Comptime interpreter
    ↓
Compile-time value
```

Không compile comptime thành executable runtime.

### Gate

Kiểm tra:

- deterministic;
- sandbox;
- capability;
- dependency tracking;
- cache;
- recursion;
- resource limit;
- generated declarations;
- generated code re-verification.

---

# 18. Phase 14 — Pattern & Exhaustiveness

Đây nên là một compiler subsystem độc lập.

Input:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

Compiler xây pattern matrix.

Kiểm tra:

```text
exhaustive
unreachable
redundant
```

Không dựa vào runtime exception.

### Gate

Test:

- enum;
- Option;
- Result;
- nested pattern;
- tuple;
- struct;
- guards;
- wildcard;
- unreachable arm.

---

# 19. Phase 15 — Verified MIR

Đây là **semantic firewall**:

```text
                  ┌──────────────┐
Source ──────────►│ Semantic     │
                  │ Verification │
                  └──────┬───────┘
                         │
                         ▼
                  VERIFIED MIR
                         │
             ┌───────────┴──────────┐
             ▼                      ▼
          Interpreter            Optimizer
```

Sau điểm này:

> Backend không được tự quyết định program có hợp lệ hay không.

Nó chỉ được transform một program đã verified.

---

# 20. Phase 16 — Reference Interpreter

Đây phải được xây **trước optimizer mạnh**.

`ax-ref`:

```text
Verified MIR
    ↓
Reference Interpreter
    ↓
Observable behavior
```

Đây là semantic oracle.

Ví dụ:

```text
return value
Result
panic
IO
atomic
volatile
termination
```

### Gate

Mọi test semantic quan trọng chạy:

```text
ax-ref
```

sau đó so sánh với native compiler.

---

# 21. Phase 17 — OptIR

Từ:

```text
Verified MIR
```

tạo:

```text
SSA
MemorySSA
AliasInfo
EffectInfo
RangeInfo
EscapeInfo
LoopInfo
TargetInfo
```

rồi:

```text
OptIR
```

Điểm quan trọng:

**OptIR không được trở thành semantic authority.**

MIR vẫn là source of truth.

---

# 22. Phase 18 — ABI Lowering

Đây là boundary:

```text
semantic value
        ↓
physical representation
```

Compiler quyết định:

- register;
- stack;
- memory;
- return convention;
- calling convention;
- aggregate passing;
- scalarization;
- alignment;
- padding;
- ABI attributes.

Ví dụ:

```text
struct Point {
    x: f32
    y: f32
}
```

không có nghĩa machine code bắt buộc phải có một block memory `Point`.

Có thể:

```text
x → XMM0
y → XMM1
```

nếu ABI/optimizer cho phép.

---

# 23. Phase 19 — Axiom LIR

LIR là machine-independent nhưng physical hơn MIR.

Ví dụ:

```text
vreg0 = ADD vreg1, vreg2
STORE [vreg3 + 8], vreg0
CALL symbol_foo
```

Có:

```text
virtual registers
memory operands
calling convention
machine constraints
target features
```

---

# 24. Phase 20 — Machine Backend

Ban đầu **không tự viết toàn bộ backend**.

Bootstrap:

```text
Axiom LIR
   ↓
LLVM IR
   ↓
LLVM backend
```

Sau khi compiler ổn định mới:

```text
Axiom LIR
   ↓
Axiom Machine IR
   ↓
Register allocation
   ↓
Instruction selection
   ↓
Scheduling
   ↓
Encoding
```

### Thứ tự backend tự viết

```text
x86-64
↓
AArch64
↓
WASM
↓
RISC-V
↓
others
```

Không nên cùng lúc triển khai 10 kiến trúc.

---

# 25. Phase 21 — Object Writer

Object writer nhận:

```text
Machine Code
Symbols
Relocations
Sections
Debug Info
TLS
Unwind
Metadata
```

và sinh:

```text
ELF
PE/COFF
Mach-O
WASM
```

Ban đầu:

```text
LLVM/system object writer
```

có thể được dùng.

Sau đó thay bằng:

```text
Axiom ObjectWriter
```

---

# 26. Phase 22 — Linker

Bootstrap:

```text
LLD / system linker
```

Final:

```text
Axiom Linker
```

Pipeline:

```text
AxiomObject
   ↓
SymbolResolver
   ↓
ArchiveReader
   ↓
RelocationEngine
   ↓
SectionLayout
   ↓
DeadStrip
   ↓
TLS
   ↓
Import/Export
   ↓
Debug/Unwind
   ↓
BinaryWriter
```

---

# 27. Phase 23 — Runtime Composition

Runtime **không được link nguyên khối**.

Ví dụ chương trình:

```axiom
fn main() {
    return
}
```

có thể chỉ cần:

```text
Startup
Program
Platform
```

Trong khi:

```axiom
async fn main()
```

mới kéo:

```text
Async
Allocator
Thread
...
```

Runtime dependency graph:

```text
Program
 ├── Startup
 ├── Panic?
 ├── Allocator?
 ├── Thread?
 ├── Async?
 ├── TLS?
 └── IO?
```

Dead stripping phải loại bỏ phần không dùng.

---

# 28. Phase 24 — Self-hosting

Đây là điểm kết thúc bootstrap.

### Stage 0

```text
C++/Rust axiomc
```

compile Axiom.

### Stage 1

Compiler source bắt đầu viết bằng Axiom:

```text
axiom-compiler.ax
```

Stage 0 compile nó:

```text
Stage0 axiomc
     ↓
Stage1 axiomc
```

### Stage 2

Stage1 compile chính source:

```text
Stage1 axiomc
     ↓
Stage2 axiomc
```

Sau đó:

```text
Stage1 ≈ Stage2
```

theo semantic/conformance tests.

Cuối cùng:

```text
Axiom compiler
     │
     ├── lexer
     ├── parser
     ├── resolver
     ├── type checker
     ├── MIR
     ├── verifier
     ├── optimizer
     ├── backend
     ├── object writer
     └── linker
```

đều là Axiom.

---

# 29. Bootstrap strategy tối ưu

Tôi đề xuất **không** làm:

```text
C++ compiler
→ hoàn thiện toàn bộ compiler
→ rewrite toàn bộ bằng Axiom
```

Quá lớn.

Thay vào đó:

### Bootstrap A

```text
Bootstrap frontend
        ↓
LLVM
```

### Bootstrap B

Từng module compiler được viết lại bằng Axiom:

```text
lexer.ax
parser.ax
types.ax
mir.ax
...
```

### Bootstrap C

Compiler Axiom tự compile:

```text
axiomc.ax
    ↓
axiomc-stage1
    ↓
axiomc-stage2
```

---

# 30. Vertical Slice #1

Đây là milestone quan trọng nhất.

Chỉ cần hỗ trợ:

```axiom
fn main() -> i32 {
    let a = 10
    let b = 20
    a + b
}
```

Pipeline:

```text
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
TypeChecker
 ↓
HIR
 ↓
MIR
 ↓
Ownership
 ↓
Reference Interpreter
 ↓
LLVM
 ↓
Native
```

Kết quả:

```text
exit code = 30
```

**Chưa cần:**

- traits;
- async;
- comptime;
- GPU;
- ownership phức tạp;
- generics;
- optimizer mạnh.

Nhưng kiến trúc phải đủ chỗ để thêm chúng mà không phá pipeline.

---

# 31. Vertical Slice #2 — Ownership

```axiom
struct Point {
    x: i32
    y: i32
}

fn main() -> i32 {
    let p = Point { x: 10, y: 20 }
    let q = p
    q.x
}
```

Compiler phải hiểu:

```text
p → Move → q
```

và:

```text
p
```

không còn usable.

---

# 32. Vertical Slice #3 — View

```axiom
fn sum(v: view<[4]i32>) -> i32 {
    ...
}

fn main() -> i32 {
    let data = [1, 2, 3, 4]
    sum(data)
}
```

Compiler phải:

```text
owner
 ↓
ephemeral view
 ↓
call
 ↓
view expires
```

Không heap.

Không reference syntax.

---

# 33. Vertical Slice #4 — Mut View

```axiom
fn increment(v: mut_view<[4]i32>) {
    ...
}
```

Test:

```text
two simultaneous mut_view
```

phải fail.

Test disjoint fields:

```text
mut_view(point.x)
mut_view(point.y)
```

có thể pass.

---

# 34. Vertical Slice #5 — Drop

Tạo resource type:

```axiom
struct File {
    ...
}
```

và:

```text
Drop
```

Compiler phải tự chèn cleanup:

```text
return
panic
branch
loop
```

Không được có:

```text
double close
leak semantic ownership
use after drop
```

---

# 35. Vertical Slice #6 — Generic

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Pipeline:

```text
Trait Solver
 ↓
Generic Instance
 ↓
Monomorphization
 ↓
MIR
```

---

# 36. Vertical Slice #7 — Async

```axiom
async fn foo() -> i32 {
    let x = await_value().await
    x + 1
}
```

Test:

```text
Future state
SuspensionPoint
Live locals
Drop
Send
```

---

# 37. Stage gates

Một phase **không được coi là hoàn thành chỉ vì code compile**.

Mỗi phase phải đạt:

```text
Implementation
+
Unit Tests
+
Negative Tests
+
Integration Tests
+
Invariant Tests
+
Diagnostic Tests
+
Regression Tests
```

Ví dụ Ownership gate:

```text
100% semantic test suite
+
negative ownership suite
+
MIR verifier assertions
+
interpreter agreement
```

---

# 38. Compiler invariant hierarchy

Mỗi stage có invariant riêng.

Ví dụ:

```text
Lexer
  → valid token stream

Parser
  → syntactically structured tree

Resolver
  → every production reference resolved or diagnosed

TypeChecker
  → every typed expression has TypeId

HIR
  → syntax sugar normalized

MIR
  → explicit CFG and semantic operations

Verifier
  → safe semantic invariants proven

OptIR
  → transformations preserve Verified MIR semantics

ABI
  → physical representation satisfies target ABI

LIR
  → legal target-independent machine representation

Machine IR
  → legal target instructions

Object
  → relocations/symbols structurally valid

Linker
  → valid executable image
```

---

# 39. Không cho phép stage “suy đoán”

Đây là một nguyên tắc tôi muốn khóa rất mạnh cho Axiom.

Không được:

```text
Backend đoán ownership
Optimizer đoán alias
Trait solver đoán implementation
Parser đoán missing declaration
Linker đoán ABI
```

Nếu một fact cần thiết:

```text
Query CompilerDB
```

hoặc:

```text
Reject / Diagnostic
```

Điều này cực kỳ quan trọng cho mục tiêu AI-friendly.

---

# 40. CompilerDB là xương sống

Mọi stage sử dụng:

```text
CompilerDB
```

với query kiểu:

```text
type_of(expr)
resolve(name)
layout_of(type)
trait_impl(goal)
ownership_of(place)
capability_of(place)
effects_of(function)
abi_of(function)
escape_of(local)
send_of(type)
share_of(type)
gpu_legal(function)
```

Không truyền những “god object” khổng lồ giữa subsystem.

---

# 41. Incremental compilation

Mỗi semantic entity có fingerprint.

Ví dụ:

```text
FunctionFingerprint
TypeFingerprint
TraitFingerprint
ModuleFingerprint
PackageFingerprint
```

Nếu sửa:

```axiom
fn foo() { ... }
```

không được rebuild toàn bộ compiler graph nếu API semantic không thay đổi.

Dependency:

```text
foo body changed
      ↓
MIR(foo) changed
      ↓
codegen(foo) changed
```

nhưng caller có thể không cần re-typecheck nếu signature không đổi.

---

# 42. First executable roadmap

Đây là roadmap thực tế nhất:

### M0

```text
lexer
parser
AST
```

### M1

```text
resolver
types
```

### M2

```text
HIR
MIR
```

### M3

```text
ownership
reference interpreter
```

### M4

```text
LLVM backend
```

→ **Axiom executable đầu tiên**

### M5

```text
traits
generics
patterns
```

### M6

```text
capabilities
effects
drop
```

### M7

```text
comptime
async
```

### M8

```text
OptIR
optimization
```

### M9

```text
Axiom LIR
```

### M10

```text
x86-64 backend
```

### M11

```text
object writer
```

### M12

```text
linker
```

### M13

```text
self-hosting
```

---

# 43. Không nên triển khai theo thứ tự tài liệu

Đây là một điều rất quan trọng.

Chúng ta đã thiết kế:

```text
GUI
GPU
Networking
Database
AI
Crypto
Scientific Computing
...
```

nhưng **không có nghĩa compiler phải implement chúng theo thứ tự đó**.

Compiler foundation chỉ cần:

```text
Core language
 ↓
Type system
 ↓
Ownership
 ↓
Capabilities
 ↓
MIR
 ↓
Codegen
```

Các subsystem lớn phía trên có thể phát triển song song sau khi Core compiler ổn định.

---

# 44. Phân chia Team AI Agent

Nếu dùng Antigravity/Gemini agent team, tôi đề xuất:

```text
AXIOM-ARCHITECT
       │
       ├── FRONTEND
       │    ├── Lexer Agent
       │    ├── Parser Agent
       │    ├── Resolver Agent
       │    └── Type Agent
       │
       ├── SEMANTICS
       │    ├── Trait Agent
       │    ├── HIR Agent
       │    ├── MIR Agent
       │    ├── Ownership Agent
       │    └── Capability Agent
       │
       ├── EXECUTION
       │    ├── Interpreter Agent
       │    ├── Optimizer Agent
       │    ├── ABI Agent
       │    └── Backend Agent
       │
       ├── PLATFORM
       │    ├── Object Agent
       │    ├── Linker Agent
       │    └── Runtime Agent
       │
       └── VALIDATION
            ├── Test Agent
            ├── Fuzz Agent
            ├── Conformance Agent
            └── Benchmark Agent
```

Nhưng **ARCHITECT phải là semantic authority**, không để nhiều agent tự sửa Core semantics.

---

# 45. Quy tắc agent

Agent làm compiler phải tuân:

```text
Research
 ↓
Design
 ↓
Implement
 ↓
Test
 ↓
Verify
 ↓
Commit
 ↓
Update task state
 ↓
Continue next task
```

Không được:

```text
Implement
 ↓
"looks good"
 ↓
next
```

Mỗi task phải có:

```text
SPEC
IMPLEMENTATION
TEST
VERIFICATION
COMMIT
```

---

# 46. NotebookLM integration

Nếu dùng NotebookLM CLI MCP như workflow trước của bạn, agent nên dùng nó cho:

- ISA documentation;
- ABI;
- PE/ELF/Mach-O;
- LLVM internals;
- OS ABI;
- GPU specifications;
- language design research;
- compiler algorithms.

Nhưng:

> NotebookLM là **research authority**, không phải **semantic authority**.

Semantic authority vẫn là:

```text
Axiom Specification
+
Compiler implementation
+
Conformance tests
```

Agent không được vì một nguồn nghiên cứu nói khác mà tự sửa Axiom semantics.

---

# 47. Definition of Done

Một compiler phase chỉ được đánh:

```text
COMPLETED
```

khi:

```text
[ ] specification mapped
[ ] implementation exists
[ ] public API frozen
[ ] invariants implemented
[ ] positive tests
[ ] negative tests
[ ] edge-case tests
[ ] diagnostics
[ ] regression tests
[ ] integration tests
[ ] deterministic behavior
[ ] no known semantic hole
[ ] documentation
[ ] commit
```

Nếu thiếu một mục:

```text
IN PROGRESS
```

---

# 48. Milestone lớn nhất: Axiom Core Compiler

Sau 218, ta có thể định nghĩa:

```text
AXIOM CORE COMPILER v0
```

bao gồm:

```text
Lexer
Parser
Resolver
Type System
Traits
HIR
MIR
Ownership
Capability
Effects
Patterns
Interpreter
LLVM Backend
```

và có thể compile một subset đủ lớn của Axiom thành native executable.

Đây là **điểm mà Axiom bắt đầu trở thành một ngôn ngữ thực**, thay vì chỉ là specification.

---

# 49. Kiến trúc cuối cùng sau bootstrap

Mục tiêu cuối:

```text
                 AXIOM SOURCE
                       │
                       ▼
              ┌─────────────────┐
              │   FRONTEND       │
              │ Lexer → AST      │
              │ Resolve → HIR    │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ SEMANTIC CORE   │
              │ Type/Trait/MIR   │
              │ Ownership        │
              │ Capability       │
              │ Effect           │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ VERIFIED MIR    │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ OPTIMIZER       │
              │ SSA/MemorySSA   │
              │ Alias/Range     │
              │ Loop/Vector     │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ Axiom LIR       │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ MACHINE BACKEND │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ OBJECT WRITER   │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │ AXIOM LINKER    │
              └────────┬────────┘
                       ▼
               NATIVE BINARY
```

Và toàn bộ compiler cuối cùng được viết bằng:

```text
AXIOM
```

---

# 50. Một quyết định kiến trúc rất quan trọng được khóa

Từ giờ Axiom nên coi:

> **MIR + Verification là trung tâm của ngôn ngữ, không phải LLVM.**

LLVM chỉ là:

```text
bootstrap backend
```

không phải:

```text
Axiom compiler architecture
```

Điều này giúp Axiom sau này tự chủ:

```text
Axiom Semantic Model
        ↓
Axiom MIR
        ↓
Axiom Optimizer
        ↓
Axiom LIR
        ↓
Axiom Backend
        ↓
Axiom Object Writer
        ↓
Axiom Linker
```

và đạt được mục tiêu ban đầu của bạn: **không phụ thuộc compiler bên thứ ba trong trạng thái cuối cùng**.

---

# 51. Các invariant mới của BOOTSTRAP-218

Đề xuất khóa:

```text
ABOOT-218-01
Every compiler phase has an explicit input/output contract.

ABOOT-218-02
Semantic correctness is established before optimization.

ABOOT-218-03
Verified MIR is the semantic firewall between frontend and backend.

ABOOT-218-04
Reference interpretation precedes aggressive optimization.

ABOOT-218-05
Bootstrap dependencies must have an explicit replacement path.

ABOOT-218-06
LLVM is a bootstrap backend, not an Axiom semantic authority.

ABOOT-218-07
System linkers are bootstrap components, not final language dependencies.

ABOOT-218-08
Every completed phase requires positive, negative, invariant and regression tests.

ABOOT-218-09
Compiler stages communicate through typed semantic contracts, not ad-hoc shared state.

ABOOT-218-10
No backend phase may reinterpret unresolved language semantics.

ABOOT-218-11
Self-hosting must be validated by independent bootstrap-stage comparison.

ABOOT-218-12
Axiom compiler behavior must be deterministic for identical semantic inputs.
```

---

## Tiếp theo: BOOTSTRAP-219

Bước hợp lý tiếp theo là **không nhảy ngay vào viết compiler**.

Cần khóa một thứ còn nền tảng hơn:

# **BOOTSTRAP-219 — AXIOM FORMAL SEMANTIC KERNEL & EXECUTION MODEL**

Nó sẽ biến các quyết định rải rác hiện tại thành một **semantic kernel duy nhất**, đặc biệt định nghĩa chính xác:

```text
Value
Place
Storage
Ownership
Capability
Region
Evaluation
Control Flow
Drop
Move
Copy
Call
Return
Panic
Effect
Concurrency
Await
Atomic
Foreign Call
Unsafe Boundary
```

và quan trọng nhất là định nghĩa **small-step / operational semantics của Axiom Core**, đủ chính xác để:

```text
Reference Interpreter
        ↓
MIR
        ↓
Verifier
        ↓
Optimizer correctness
        ↓
Conformance tests
```

đều có thể dựa vào **cùng một semantic authority**.

Đây sẽ là bước khóa nền móng cuối cùng trước khi specification có thể chuyển sang trạng thái **“compiler implementation contract”** thực sự.