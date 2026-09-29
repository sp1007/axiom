# BOOTSTRAP-125 — Compiler Frontend Architecture & Incremental Compiler Database

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là khóa kiến trúc frontend/compiler database để Axiom có thể:

- compile project rất lớn;
- incremental cực nhanh;
- chạy song song;
- hỗ trợ IDE;
- hỗ trợ AI agent;
- cache ổn định;
- không rebuild toàn bộ khi chỉ sửa một hàm;
- giữ nguyên semantic correctness.

Nguyên tắc trung tâm:

> **Compiler không phải một pipeline chạy một lần từ trên xuống dưới. Compiler là một cơ sở dữ liệu semantic có thể truy vấn, cache, invalidate và tính lại từng phần.**

---

# 1. Kiến trúc tổng thể

Frontend hoàn chỉnh:

```text
                    Source Files
                         │
                         ▼
                    ┌─────────┐
                    │ SourceDB│
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │ Lexer   │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │   CST   │
                    └────┬────┘
                         │
                         ▼
                    ┌─────────┐
                    │   AST   │
                    └────┬────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Resolver     Syntax      IDE queries
             │
             ▼
          TypeDB
             │
       ┌─────┴──────┐
       ▼            ▼
 Trait Solver    ConstDB
       │            │
       └─────┬──────┘
             ▼
          Comptime
             │
             ▼
            HIR
             │
             ▼
            MIR
```

Nhưng implementation thực tế không phải:

```text
compile()
    lexer()
    parser()
    resolver()
    typecheck()
    ...
```

mà là:

```text
CompilerDB
    query(SourceFileId)
    query(AST)
    query(TypeOf(expr))
    query(TraitSolution)
    query(HIR(FunctionId))
    query(MIR(FunctionId))
```

Mỗi query có dependency graph và cache riêng.

---

# 2. CompilerDB là trung tâm

Đề xuất:

```text
CompilerDB {
    SourceDB
    PackageDB
    ModuleDB
    SyntaxDB
    DeclarationDB
    TypeDB
    TraitDB
    ConstDB
    GenericDB
    ComptimeDB
    HIRDB
    MIRDB
    DiagnosticDB
    SourceMapDB
    LayoutDB
    AbiDB
    CodegenDB
    BuildDB
}
```

Không có một object `Compiler` khổng lồ chứa mọi trạng thái mutable.

---

# 3. Database query model

Mọi semantic computation quan trọng trở thành query:

```text
parse(file)
module(file)
declarations(module)
resolve(name)
type_of(expr)
trait_solve(goal)
const_eval(expr)
comptime_expand(item)
lower_hir(function)
lower_mir(function)
verify_mir(function)
optimize(function)
lower_abi(function)
```

Ví dụ:

```text
TypeOf(ExprId)
```

phụ thuộc:

```text
Expr
NameResolution
ExpectedType
GenericSubstitution
```

Nếu những thứ này không thay đổi:

> **TypeOf được lấy từ cache.**

---

# 4. Input và derived query

Phân biệt rất rõ:

### Input

```text
SourceFile
PackageManifest
CompilerConfig
Target
Environment
ComptimeExternalInput
```

### Derived

```text
Tokens
CST
AST
Declarations
Resolution
Types
TraitSolutions
HIR
MIR
Layout
ABI
Codegen
```

Input thay đổi → compiler invalidate derived data liên quan.

---

# 5. SourceDB

```text
SourceFile {
    id: SourceFileId
    path: Path
    content: SourceText
    revision: RevisionId
}
```

Không dùng path làm identity duy nhất.

`SourceFileId` ổn định trong CompilerDB session.

---

# 6. Source revision

Mỗi file có revision:

```text
SourceFile
    revision 100
        ↓ edit
    revision 101
```

Compiler không nhất thiết discard toàn bộ file semantic state.

---

# 7. Incremental text representation

Không nhất thiết copy toàn bộ source mỗi lần user gõ một ký tự.

IDE mode có thể dùng:

```text
rope / piece table / persistent text structure
```

Nhưng compiler semantic layer chỉ cần nhìn thấy:

```text
SourceRevision
```

và source spans.

Implementation của text storage không phải language semantic.

---

# 8. Source span

Mọi AST/HIR/MIR diagnostic-relevant node nên giữ:

```text
SourceSpan {
    file: SourceFileId
    start: Offset
    end: Offset
}
```

Có thể mở rộng:

```text
SyntaxContext
ExpansionId
Origin
```

cho generated/comptime code.

---

# 9. Stable IDs

Compiler dùng ID thay vì pointer trực tiếp:

```text
PackageId
ModuleId
FileId
DeclarationId
FunctionId
StructId
FieldId
EnumId
VariantId
TraitId
TypeId
ExprId
StmtId
PatternId
GenericParamId
GenericInstanceId
LocalId
BasicBlockId
InstructionId
```

Lợi ích:

- cache;
- serialization;
- parallelism;
- incremental rebuild;
- debug;
- AI inspection.

---

# 10. Generational IDs

Các entity có thể dùng:

```text
Index + Generation
```

Ví dụ:

```text
DeclarationId {
    index: u32
    generation: u32
}
```

Tránh stale handle sau mutation/revision.

---

# 11. Không dùng memory address làm identity

Không:

```text
pointer == declaration identity
```

vì compiler database có thể:

- compact;
- parallelize;
- serialize;
- reload cache.

Identity phải logical.

---

# 12. Interning

Type là candidate quan trọng nhất.

Ví dụ:

```text
i32
```

chỉ nên có một canonical:

```text
TypeId(42)
```

trong database scope phù hợp.

Tương tự:

```text
Vec<i32>
```

có thể canonicalize thành:

```text
TypeId(107)
```

---

# 13. Type interning

Concept:

```text
TypeInterner {
    Primitive
    Tuple
    Struct
    Enum
    Array
    Function
    GenericParam
    GenericInstance
    TraitObject
    View
    MutView
    RawPointer
}
```

Structural equality của type được chuyển thành ID equality khi đã intern.

---

# 14. Nominal types

Không được intern hai nominal declaration khác nhau thành cùng type chỉ vì layout giống nhau.

Ví dụ:

```ax
struct UserId(u64);
struct ProductId(u64);
```

phải là:

```text
UserId != ProductId
```

dù:

```text
size(UserId) == size(ProductId)
```

---

# 15. ModuleDB

```text
Module {
    id
    package
    parent
    children
    files
    imports
    exports
}
```

Module graph được duy trì riêng khỏi package graph.

---

# 16. Module cycle

Module cycle có thể được hỗ trợ.

Ví dụ:

```text
A imports B
B imports A
```

nếu declaration graph cho phép.

Resolver phải có phase:

```text
collect declarations
→ establish module namespaces
→ resolve bodies
```

Không resolve toàn bộ body ngay khi gặp import.

---

# 17. Package cycle

Package cycle:

```text
A → B → A
```

**reject**.

Đây là build-system invariant đã frozen.

---

# 18. Declaration collection

Frontend nên có ít nhất 2 phase:

```text
Phase 1:
    collect declarations

Phase 2:
    resolve declaration bodies
```

Ví dụ:

```ax
fn a() -> i32 {
    b()
}

fn b() -> i32 {
    10
}
```

không phụ thuộc declaration order.

---

# 19. Name resolution

Resolver xử lý:

```text
local
parameter
function
type
module
trait
associated item
generic parameter
import
prelude
```

và tạo:

```text
ResolvedName {
    declaration: DeclarationId
    kind
}
```

---

# 20. Không dùng string lookup ở mọi nơi

Sau resolution:

```ax
foo()
```

không nên tiếp tục được biểu diễn semantic bằng:

```text
"foo"
```

mà:

```text
Call {
    callee: FunctionId(123)
}
```

Tên chỉ còn cần cho:

- diagnostics;
- debug;
- tooling;
- symbol generation.

---

# 21. Shadowing

```ax
let x = 1;

{
    let x = 2;
}
```

Resolver tạo:

```text
LocalId(10)
LocalId(21)
```

Không dùng string `"x"` để distinguish.

---

# 22. Type checking

Type checker hoạt động trên resolved AST/HIR:

```text
Expr
 ↓
ExpectedType
 ↓
Infer
 ↓
Unify
 ↓
Constraints
 ↓
Solve
 ↓
TypeId
```

---

# 23. Type inference

Axiom cho inference nhưng không để inference trở thành theorem prover.

Ví dụ:

```ax
let x = Vec.new();
```

nếu không đủ information:

```text
EINFER_AMBIGUOUS
```

thay vì compiler đoán arbitrary type.

---

# 24. Unification

Type checker cần unification variables:

```text
T0
T1
T2
```

Ví dụ:

```text
Vec<T0>
=
Vec<i32>
```

→

```text
T0 = i32
```

---

# 25. Constraint graph

Type inference tạo constraints:

```text
T0 == i32
T1 == Vec<T0>
T2: Iterator
```

Sau đó solve.

Không trực tiếp mutate type node tùy tiện.

---

# 26. Trait solver

Trait solver là query độc lập:

```text
SolveTrait(
    goal = T: Display
)
```

trả:

```text
Proven
NotProven
Ambiguous
Error
```

Có memoization.

---

# 27. Trait solver cache

Ví dụ:

```text
Solve(Vec<i32>: Display)
```

được cache.

Generic instances khác nhưng cùng canonical goal có thể reuse result.

---

# 28. Cycle detection

Ví dụ trait:

```text
A<T> requires B<T>
B<T> requires A<T>
```

solver phải phát hiện cycle.

Không được infinite recursion.

---

# 29. Solver fuel/depth

Mọi recursive query có giới hạn:

```text
solver_depth
comptime_steps
type_recursion
generic_instantiation
```

vượt giới hạn:

```text
controlled diagnostic
```

không compiler stack overflow.

---

# 30. Generic instance database

```text
GenericInstance {
    definition: DeclarationId
    substitutions: [TypeId]
    const_args: [...]
    target: TargetId
}
```

Canonical key:

```text
GenericDefinition
+
CanonicalSubstitution
+
TargetRelevantConfiguration
```

---

# 31. Monomorphization

Ví dụ:

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

với:

```text
max<i32>
max<f64>
max<User>
```

Compiler tạo concrete instances khi cần.

---

# 32. Generic deduplication

Nếu hai source paths yêu cầu cùng:

```text
max<i32>
```

không generate machine code hai lần.

---

# 33. HIR

HIR là semantic representation sau:

- syntax sugar;
- name resolution;
- basic desugaring;
- type information.

Ví dụ:

```ax
user.greet()
```

có thể thành semantic:

```text
Call(
    ResolvedFunction(greet),
    [View(user)]
)
```

---

# 34. HIR không phải MIR

HIR giữ cấu trúc gần source.

MIR tập trung:

- control flow;
- ownership;
- capabilities;
- explicit operations;
- cleanup.

---

# 35. HIR incremental boundary

Nếu sửa body:

```ax
fn foo() {
    ...
}
```

thì declaration signature không đổi.

Các module phụ thuộc signature không nên bị rebuild semantic toàn bộ.

---

# 36. Interface fingerprint

Mỗi module/package có:

```text
InterfaceFingerprint
```

bao gồm:

```text
public declarations
public types
public traits
generic signatures
associated types
ABI contracts
repr
exports
comptime-visible metadata
```

---

# 37. Implementation fingerprint

Riêng:

```text
ImplementationFingerprint
```

gồm:

```text
private body
optimization
target CPU
LTO
codegen configuration
```

---

# 38. Ví dụ incremental

File:

```text
math.ax
```

có:

```ax
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

sửa:

```ax
pub fn add(a: i32, b: i32) -> i32 {
    a - b
}
```

Interface không đổi.

Do đó downstream type checking có thể reuse.

Chỉ codegen/semantic body liên quan phải invalidate.

---

# 39. Nếu đổi signature

```ax
pub fn add(a: i64, b: i64) -> i64
```

InterfaceFingerprint thay đổi.

Compiler phải invalidate:

```text
callers
generic constraints
ABI
machine code
dependent modules
```

---

# 40. Query dependency graph

Compiler duy trì:

```text
Query A
   ↓ depends
Query B
   ↓ depends
Input C
```

Khi `C` thay đổi:

```text
invalidate(B)
invalidate(A)
```

nhưng chỉ những query thực sự phụ thuộc.

---

# 41. Salsa-like architecture

Axiom có thể dùng **query database model tương tự Salsa**, nhưng không nên khóa implementation vào một framework bên thứ ba.

Đề xuất:

```text
Axiom CompilerDB Query Engine
```

có:

- memoization;
- dependency tracking;
- revision;
- cancellation;
- parallel query;
- cycle detection.

Có thể tham khảo Salsa nhưng implementation cuối cùng thuộc Axiom compiler.

---

# 42. Query purity

Derived query nên có semantics:

```text
same inputs
→ same result
```

Ngoại lệ chỉ qua explicit external capability:

```text
comptime
filesystem
environment
target
```

và những dependency đó phải được đưa vào query identity.

---

# 43. No hidden global compiler state

Không:

```text
global mutable type table
global mutable current module
global random ID
global environment lookup
```

nếu có thể tránh.

Điều này rất quan trọng cho:

- parallel compile;
- deterministic compile;
- compiler server;
- IDE;
- AI agents.

---

# 44. Parallel queries

Ví dụ:

```text
Module A
Module B
Module C
```

nếu không dependency:

```text
        CompilerDB
       /    |     \
      A     B      C
      ↓     ↓      ↓
   parallel evaluation
```

---

# 45. Query cancellation

IDE scenario:

```text
user types
user types again
user types again
```

Compiler không nên hoàn thành query cũ nếu kết quả đã obsolete.

Query có cancellation token/revision check.

---

# 46. Compiler server

Axiom compiler nên hỗ trợ:

```text
axc server
```

giữ:

```text
CompilerDB
SourceDB
TypeDB
cache
```

trong memory.

IDE edit:

```text
edit source
→ new revision
→ invalidate affected queries
→ recompute
```

Không khởi động compiler process từ đầu cho từng request.

---

# 47. CLI và compiler server dùng cùng engine

Không tạo:

```text
IDE compiler
CLI compiler
LSP compiler
```

thành ba implementation.

Tất cả:

```text
             CompilerDB
             /    |    \
           CLI   LSP   AI API
```

---

# 48. IDE queries

CompilerDB phải hỗ trợ query:

```text
type_at(position)
definition_at(position)
references_of(symbol)
completion_at(position)
signature_help(position)
hover(position)
diagnostics(file)
semantic_tokens(file)
```

Đây không phải “plugin layer” riêng.

Chúng là read queries của compiler database.

---

# 49. AI compiler API

Axiom nên có machine-readable interface:

```text
axc inspect symbol
axc inspect type
axc inspect trait
axc explain diagnostic
axc query dependencies
axc query callers
axc query ownership
axc query MIR
```

Ví dụ:

```text
axc inspect type std::vec::Vec<i32>
```

trả JSON/schema ổn định.

---

# 50. AI không cần parse compiler text

Thay vì:

```text
Error: cannot move...
help: ...
```

AI API nhận:

```json
{
  "code": "EOWN_MOVE_AFTER_MOVE",
  "location": {...},
  "entity": "LocalId(42)",
  "state": "MOVED",
  "required": "OWNED",
  "suggestions": [...]
}
```

Wording có thể thay đổi.

Machine schema ổn định.

---

# 51. DiagnosticDB

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    machine_data
    fixits
}
```

Fix-it:

```text
TextEdit {
    file
    range
    replacement
}
```

---

# 52. Diagnostic không được mutate semantics

Compiler diagnostics là output.

Không để:

```text
diagnostic engine
→ semantic decision
```

Ngược lại:

```text
semantic query
→ diagnostic
```

---

# 53. Error recovery semantic

Compiler có thể tạo error node:

```text
ErrorExpr
ErrorType
ErrorPattern
```

để tiếp tục phân tích.

Nhưng:

> Error node không bao giờ được xem là valid semantic proof.

---

# 54. Compilation phases và cache

Cache levels:

```text
L0  in-memory query cache
L1  process-local
L2  workspace cache
L3  global artifact cache
L4  optional remote cache
```

Mỗi level phải validate fingerprint.

---

# 55. Persistent semantic cache

Có thể serialize:

```text
.axcache
```

nhưng không cache raw memory pointers.

Cache record dùng:

```text
logical IDs
canonical types
fingerprints
source hashes
compiler semantic version
```

---

# 56. Compiler version

Cache identity bắt buộc chứa:

```text
CompilerSemanticVersion
```

Nếu semantic compiler thay đổi:

```text
cache miss
```

Không reuse artifact không tương thích.

---

# 57. Target identity

Cache cũng chứa:

```text
TargetTriple
CPUFeatures
ABI
OS
ObjectFormat
```

Ví dụ:

```text
x86_64-windows-msvc
```

khác:

```text
x86_64-linux-gnu
```

---

# 58. Configuration identity

Bao gồm:

```text
profile
features
cfg values
panic mode
LTO
debug
sanitizer
comptime inputs
```

---

# 59. Comptime dependency

Nếu:

```ax
const VERSION = comptime read_file("version.txt");
```

thì:

```text
version.txt
```

phải trở thành dependency của query.

Sửa file → invalidate comptime result.

Không được có hidden dependency.

---

# 60. Environment dependency

Nếu comptime được cấp:

```text
Environment
```

thì các environment keys đã đọc phải được tracking.

Ví dụ:

```text
AXIOM_BUILD_MODE
```

thay đổi → cache identity thay đổi.

---

# 61. Query granularity

Không nên chỉ cache:

```text
whole module
```

Mà cache ở nhiều mức:

```text
file
declaration
function
expression
type
trait goal
generic instance
comptime invocation
```

Tuy nhiên không phải mọi query đều cần persistent disk cache.

---

# 62. Function-level incremental compilation

Ví dụ:

```ax
fn a() { ... }
fn b() { ... }
fn c() { ... }
```

sửa `b`.

Nếu:

```text
a không phụ thuộc b
c không phụ thuộc b
```

thì:

```text
MIR(a) cached
MIR(c) cached
```

và chỉ `b` recompute.

---

# 63. Inline dependency

Nếu compiler inline `b()` vào `a()`:

implementation fingerprint của `b` trở thành dependency của optimized `a`.

Nếu `b` thay đổi:

```text
a's codegen cache
```

có thể invalidate dù public interface không đổi.

Đây là lý do phải phân biệt:

```text
semantic dependency
vs
optimization/codegen dependency
```

---

# 64. Type dependency vs implementation dependency

Nếu:

```ax
fn foo() -> User
```

thì caller phụ thuộc semantic vào:

```text
User
foo signature
```

không nhất thiết phụ thuộc body `foo`.

Nếu inlining:

```text
caller
```

có thêm implementation dependency.

---

# 65. Stable ABI cache

ABI MIR cache phải phụ thuộc:

```text
Type layout
Target ABI
Calling convention
repr
Compiler ABI version
```

Không reuse nếu ABI contract thay đổi.

---

# 66. Incremental MIR

MIR có thể cache per function:

```text
MIR(FunctionId)
```

nhưng ownership verification phải chạy lại nếu semantic dependencies thay đổi.

Không được tin cache một cách mù quáng.

---

# 67. Verified MIR cache

Có thể cache:

```text
VerifiedMIRArtifact
```

nếu:

```text
source semantic fingerprint
compiler verifier version
type environment
target-relevant rules
```

khớp.

Nếu verifier thay đổi:

```text
reverify
```

---

# 68. Optimization cache

Optimization cache phải tách khỏi semantic cache:

```text
Verified MIR
      ↓
OptIR
```

Thay đổi optimization flags không cần frontend rebuild.

Ví dụ:

```text
debug
release
size
```

có thể dùng cùng semantic artifacts.

---

# 69. Codegen parallelism

Một khi generic instances và functions đã resolved:

```text
Function A → backend worker 1
Function B → backend worker 2
Function C → backend worker 3
```

Object sections sau đó merge deterministic.

---

# 70. Deterministic parallelism

Parallel compile không được làm:

```text
output depends on thread scheduling
```

Mọi ordering observable phải canonicalize.

Ví dụ:

```text
symbol order
section order
metadata order
diagnostic order
```

được sort/canonicalize.

---

# 71. Compiler memory management

Compiler itself không cần tuân thủ freestanding restrictions của target program.

Compiler có thể dùng:

```text
heap
arena
GC-like internal structures
parallel workers
hash tables
```

Điều này rất quan trọng.

Không nên hy sinh compiler implementation chỉ vì target language không có GC.

---

# 72. Compiler arenas

Các object có lifetime theo compiler phase có thể dùng arena:

```text
AST arena
HIR arena
temporary inference arena
diagnostic arena
```

CompilerDB logical IDs vẫn là identity.

---

# 73. Persistent data structures

Những structures cần revision sharing có thể dùng:

```text
persistent map
persistent vector
copy-on-write
structural sharing
```

nhưng đây là implementation choice.

Semantic architecture không phụ thuộc.

---

# 74. Database transaction

Một edit có thể được coi là:

```text
Revision N
   ↓
Input update
   ↓
Revision N+1
```

Không mutate semantic world giữa chừng theo kiểu khó rollback.

---

# 75. Snapshot

IDE query nên có:

```text
CompilerSnapshot
```

đại diện cho một revision.

Ví dụ:

```text
snapshot A
```

vẫn có thể tồn tại trong lúc:

```text
snapshot B
```

được tạo.

Điều này giúp cancellation và concurrent IDE requests.

---

# 76. Thread safety của CompilerDB

CompilerDB phải hỗ trợ:

```text
many readers
controlled writers
parallel derived queries
```

Không để từng query tự do mutate global state.

---

# 77. Query purity và memoization

Concept:

```text
Query<Input> → Output
```

có thể memoize.

Nếu query cần side effect:

```text
external capability
```

phải trở thành explicit input/dependency.

---

# 78. Build graph integration

CompilerDB không thay thế BuildDB.

```text
BuildDB
    ↓
Package graph
    ↓
CompilerDB per package/module
```

Build system quyết định **cái gì cần compile**.

CompilerDB quyết định **semantic result của cái đó**.

---

# 79. Package boundary

Mỗi package có:

```text
public interface
private implementation
metadata
artifact
```

Package dependency không cần expose toàn bộ source.

`.axmeta` cung cấp public semantic information.

---

# 80. `.axmeta`

Metadata cần đủ để downstream compile mà không cần source:

```text
public declarations
types
traits
generic definitions/metadata
associated items
ABI contracts
repr
exports
attributes
comptime-visible data
compiler semantic version
dependency identity
```

---

# 81. Generic source visibility

Có hai chiến lược:

### Monomorphize từ source

Downstream cần generic body.

### Generic metadata

`.axmeta` chứa canonical generic representation/HIR cần thiết.

Axiom nên hướng tới:

> **Generic compilation metadata phải đủ để downstream compiler instantiate mà không nhất thiết cần source text.**

Điều này đặc biệt hữu ích cho binary distribution.

---

# 82. Privacy

Private implementation không được leak semantic metadata không cần thiết.

Ví dụ:

```ax
pub fn foo() -> PublicType
```

không cần expose:

```text
private HelperStruct
```

nếu không nằm trong public signature/comptime-visible contract.

---

# 83. Compiler pipeline sau 125

Kiến trúc implementation hiện tại:

```text
Source
 ↓
SourceDB
 ↓
Lexer
 ↓
CST
 ↓
AST
 ↓
Resolver
 ↓
TypeDB / TraitDB / ConstDB
 ↓
Comptime
 ↓
HIR
 ↓
MIR
 ↓
Independent Verification
 ↓
OptIR
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine
```

Nhưng phía dưới là:

```text
             ┌──────────────────────┐
             │      CompilerDB      │
             │                      │
             │  Query + Cache +     │
             │  Dependency +        │
             │  Revision +         │
             │  Parallelism        │
             └──────────────────────┘
```

---

# 84. AI/IDE/CLI cùng một semantic engine

```text
                    CompilerDB
                 /      |       \
                /       |        \
              axc      LSP       AI
               |         |         |
             build     hover     inspect
             check     goto      explain
             test      rename    analyze
```

Không có semantic duplication.

---

# 85. CompilerDB invariants

### `ACDB-20`
All derived semantic information is represented as queryable compiler state.

### `ACDB-21`
Inputs are distinguished from derived queries.

### `ACDB-22`
Query results are memoizable where semantically valid.

### `ACDB-23`
Query dependencies are tracked explicitly.

### `ACDB-24`
Hidden external dependencies are forbidden.

### `ACDB-25`
Source revisions are explicit.

### `ACDB-26`
Semantic identity does not depend on memory addresses.

### `ACDB-27`
Stable logical IDs are used for compiler entities.

### `ACDB-28`
Nominal type identity is preserved across interning.

### `ACDB-29`
Equivalent structural types may be canonicalized.

### `ACDB-30`
Generic instances have canonical identities.

### `ACDB-31`
Trait queries detect cycles.

### `ACDB-32`
Trait queries terminate under configured resource limits.

### `ACDB-33`
Name resolution produces stable declaration references.

### `ACDB-34`
Semantic queries do not depend on source declaration order unless explicitly specified.

### `ACDB-35`
Interface and implementation dependencies are distinguished.

### `ACDB-36`
Incremental recompilation invalidates only affected queries.

### `ACDB-37`
Changing private implementation does not invalidate unrelated public semantic consumers.

### `ACDB-38`
Changing public interface invalidates dependent semantic consumers.

### `ACDB-39`
Optimization dependencies are distinct from frontend semantic dependencies.

### `ACDB-40`
Compiler revisions invalidate incompatible cached semantic results.

### `ACDB-41`
Target identity participates in target-dependent cache keys.

### `ACDB-42`
Comptime external inputs participate in dependency tracking.

### `ACDB-43`
Environment dependencies cannot be hidden from cache identity.

### `ACDB-44`
Parallel query evaluation preserves semantic determinism.

### `ACDB-45`
Compiler cancellation cannot corrupt committed database state.

### `ACDB-46`
IDE queries and CLI compilation use the same semantic database model.

### `ACDB-47`
AI compiler interfaces consume structured semantic information.

### `ACDB-48`
Diagnostics reference stable source spans and semantic entities.

### `ACDB-49`
Persistent caches never depend on raw process memory addresses.

### `ACDB-50`
Cached Verified MIR is valid only under the verifier/compiler identity that produced it.

### `ACDB-51`
Cache hits and clean compilation are semantically equivalent.

### `ACDB-52`
Compiler parallelism cannot affect semantic output.

### `ACDB-53`
Error recovery nodes cannot act as semantic proof.

### `ACDB-54`
CompilerDB does not become part of target-program runtime.

### `ACDB-55`
Compiler implementation may use independent memory-management strategies.

### `ACDB-56`
Package metadata is sufficient for supported downstream compilation scenarios.

### `ACDB-57`
Generic instantiation does not require recompiling unrelated generic instances.

### `ACDB-58`
Source-level edits are represented as new revisions rather than uncontrolled global mutation.

### `ACDB-59`
Compiler snapshots are isolated enough for concurrent tooling queries.

### `ACDB-60`
Semantic correctness is independent of incremental vs clean compilation.

---

# 86. Một quyết định kiến trúc quan trọng

Từ đây, Axiom compiler **không nên được thiết kế như Clang-style monolithic pass pipeline**.

Mô hình đúng hơn là:

```text
                 ┌───────────────────────┐
                 │       CompilerDB      │
                 └───────────────────────┘
                    ↑   ↑   ↑   ↑   ↑
                    │   │   │   │   │
                  AST  Type HIR MIR ABI
                    │   │   │   │   │
                    └───┴───┴───┴───┘
                            │
                      Query Engine
                            │
                 Dependency + Cache
```

Điều này đặc biệt phù hợp với mục tiêu Axiom là **AI-friendly**: AI có thể hỏi compiler những câu semantic cụ thể thay vì phải đọc hàng nghìn dòng compiler log.

---

# BOOTSTRAP-126 — Lexer, Token Model & Lossless Syntax Infrastructure

Bước tiếp theo sẽ đi xuống tầng thấp nhất của frontend: **lexer**.

Task 126 sẽ khóa:

```text
UTF-8 source
    ↓
Unicode validation
    ↓
Normalization
    ↓
Lexer
    ↓
Token
    ↓
Trivia
    ↓
CST
```

và giải quyết những vấn đề rất thực tế:

- token representation;
- identifier interning;
- Unicode XID;
- keyword recognition;
- numeric literals;
- string/char/raw literals;
- escape processing;
- comments;
- nested block comments;
- source offsets;
- UTF-8 byte offset vs Unicode codepoint;
- zero-copy lexing;
- incremental lexing khi sửa một ký tự;
- lexer error recovery;
- malformed UTF-8;
- deterministic tokenization;
- memory layout của token;
- cách CST giữ comment/formatting mà AST không phải mang theo toàn bộ trivia;
- lexer performance trên file hàng MB/GB;
- và đặc biệt **incremental lexer** để IDE phản hồi gần như tức thời.