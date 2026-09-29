# AXIOM COMPILER KERNEL SPEC

Đây là lớp nền mà **toàn bộ compiler phụ thuộc vào**. Tôi đề xuất khóa nó trước khi viết lexer/parser, vì nếu ID, source model, query/incremental và diagnostic thay đổi giữa chừng thì gần như mọi subsystem phía trên đều phải sửa.

Mục tiêu của kernel:

> **Compiler có thể thay đổi implementation nội bộ, nhưng mọi phase nhìn thấy cùng một semantic identity, source identity và dependency identity.**

---

# 1. Kiến trúc Compiler Kernel

Kernel không xử lý ngữ nghĩa Axiom.

Nó cung cấp **hạ tầng chung**:

```text
                    ┌──────────────────────┐
                    │   CompilerSession    │
                    └──────────┬───────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
 SourceDatabase          Symbol/Type IDs       Diagnostics
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                         Query Engine
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
              Dependency Graph       Incremental Cache
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                         Compiler Passes
                               │
                    AST → HIR → MIR → ...
```

Kernel **không được biết**:

- `struct`
- `trait`
- ownership
- `view`
- `mut_view`
- async
- GPU
- ABI
- x86 instruction

Những thứ đó thuộc semantic/compiler layer.

---

# 2. CompilerContext

Không nên truyền 15–20 object qua mọi function.

Nhưng cũng **không nên có một global mutable compiler state**.

Thiết kế:

```text
CompilerSession
├── SourceDatabase
├── SymbolInterner
├── TypeInterner
├── StringInterner
├── ModuleDatabase
├── QueryDatabase
├── DiagnosticStore
├── PackageGraph
├── TargetConfig
├── BuildConfig
├── CacheConfig
└── CompilerOptions
```

Một phase nhận context phù hợp:

```text
fn resolve(ctx: &ResolverContext, module: ModuleId)
fn type_check(ctx: &TypeContext, item: ItemId)
fn lower_mir(ctx: &MirContext, function: FunctionId)
```

Tuy nhiên `&ResolverContext` ở đây chỉ là **compiler implementation concept**, không phải syntax/lifetime của Axiom.

### Quy tắc

Compiler implementation có thể dùng Rust/C++/Axiom hoặc ngôn ngữ bootstrap khác.

Không được để mô hình lifetime của implementation biến thành semantic requirement của Axiom.

---

# 3. CompilerSession

`CompilerSession` đại diện cho một lần biên dịch.

Ví dụ:

```text
CompilerSession {
    compiler_version
    language_version

    target
    profile
    optimization
    panic_strategy

    source_db
    package_graph
    query_db
    diagnostics
    cache

    deterministic_seed
}
```

Session phải **độc lập**.

Không:

```text
global CURRENT_COMPILER
global CURRENT_PACKAGE
global CURRENT_TARGET
```

Điều này rất quan trọng cho:

- parallel compilation
- language server
- IDE
- compiler-as-library
- testing
- multiple targets trong cùng process
- AI agent tooling

---

# 4. FileId

Không dùng path string làm identity.

```text
FileId
```

là ID nội bộ.

Ví dụ:

```text
FileId(0)
FileId(1)
FileId(2)
```

Source database:

```text
FileId
   ↓
SourceFile {
    canonical_identity
    source_text
    source_hash
    line_map
    module
}
```

### File identity

Path:

```text
src/math.ax
```

không nhất thiết đủ để xác định source.

Nên identity thực tế:

```text
SourceIdentity {
    PackageId
    CanonicalPath
}
```

Generated source có thể dùng:

```text
GeneratedSourceIdentity {
    GeneratorId
    ArtifactId
}
```

---

# 5. Span

Đây là một quyết định cực kỳ quan trọng.

**Span dùng byte offset làm identity.**

```text
Span {
    file: FileId
    start: u32
    end: u32
}
```

Ví dụ:

```text
fn add(a: i32, b: i32)
   ^^^^^^^^^^^^^^^^^^^^^
```

Không lưu line/column trong Span.

Line/column được tính từ:

```text
LineMap
```

vì:

- UTF-8
- source edit
- incremental compilation
- Unicode identifier
- diagnostic
- LSP

đều cần source position ổn định.

---

# 6. SourceDatabase

API tối thiểu:

```text
load_file(path) -> FileId
add_virtual_file(identity, text) -> FileId

source(file) -> SourceText
span_text(span) -> Text

line_col(span) -> LineColumn
line_range(file, line) -> Span

source_hash(file) -> Hash
```

Source database phải phân biệt:

```text
physical source
virtual source
generated source
```

Ví dụ `comptime` sinh:

```text
generated/foo.ax
```

không được giả vờ đó là source file bình thường.

---

# 7. Stable IDs

Axiom compiler sẽ có rất nhiều entity.

Không dùng pointer làm semantic identity.

Core IDs:

```text
FileId
PackageId
ModuleId

SymbolId
LocalId

TypeId
TraitId
ImplId

FunctionId
StructId
EnumId
FieldId
VariantId

GenericParamId
AssociatedTypeId

ItemId
ExprId
PatternId

BlockId
InstrId
PlaceId

AllocationId
DiagnosticId
QueryId
```

Mỗi ID có domain riêng.

Không:

```text
u32
```

ở API semantic.

Mà:

```text
struct FunctionId(u32)
struct TypeId(u32)
struct BlockId(u32)
```

để compiler không thể vô tình truyền:

```text
BlockId
```

vào API yêu cầu:

```text
FunctionId
```

---

# 8. Stable ID ≠ Persistent ID

Cần phân biệt hai loại.

### Session ID

```text
FunctionId
TypeId
SymbolId
```

chỉ ổn định trong compiler session.

### Persistent identity

Dùng cho incremental cache:

```text
SemanticKey
```

Ví dụ:

```text
SemanticKey {
    package_identity
    module_identity
    declaration_path
}
```

Do đó:

```text
FunctionId(42)
```

có thể trở thành:

```text
FunctionId(17)
```

sau lần compile khác mà cache vẫn nhận ra đó là cùng function.

Đây là điểm rất quan trọng.

---

# 9. String Interner

Compiler sẽ gặp hàng triệu identifier:

```text
foo
bar
Vector
String
display
...
```

Không nên copy string liên tục.

```text
StringId
```

Ví dụ:

```text
"Vector" → StringId(42)
```

Tên identifier:

```text
Ident {
    name: StringId
    span: Span
}
```

### Interner invariant

Hai string bằng nhau:

```text
"Vector"
"Vector"
```

→ cùng `StringId` trong cùng compiler session.

Nhưng `StringId` không phải semantic identity của symbol.

---

# 10. SymbolId

Đây là distinction cực kỳ quan trọng:

```text
StringId("x")
```

không có nghĩa:

```text
SymbolId(x)
```

Ví dụ:

```axiom
fn foo() {
    let x = 1
}

fn bar() {
    let x = 2
}
```

cả hai đều có:

```text
StringId("x")
```

nhưng là hai:

```text
SymbolId
```

khác nhau.

---

# 11. Symbol

Semantic symbol:

```text
Symbol {
    id: SymbolId
    name: StringId
    kind: SymbolKind
    owner: SymbolOwner
    visibility: Visibility
    span: Span
}
```

`SymbolKind`:

```text
Module
Function
Struct
Enum
Trait
Impl
Field
Variant
Parameter
Local
GenericParam
Const
Static
TypeAlias
```

---

# 12. Arena Allocation

Compiler implementation nên sử dụng arena/interned storage rất mạnh.

Ví dụ:

```text
Arena<AstNode>
Arena<HirNode>
Arena<MirInstruction>
Arena<Type>
```

Thay vì:

```text
Box<Node>
Box<Node>
Box<Node>
```

với ownership phức tạp.

### Nhưng cực kỳ quan trọng:

**Compiler arena không liên quan đến Axiom memory model.**

Nó chỉ là implementation detail của compiler.

Axiom program:

```text
Arena<T>
```

là semantic library abstraction.

Compiler:

```text
Arena<CompilerNode>
```

chỉ là cách compiler quản lý memory.

---

# 13. Arena không được tạo semantic identity

Ví dụ:

```text
TypeId(10)
```

không được đồng nhất với:

```text
arena_address = 0x123456
```

Compiler phải có:

```text
TypeId
```

làm semantic identity.

Điều này cho phép sau này:

- compact arena
- serialize IR
- parallel compiler
- incremental reload
- garbage collect compiler data
- persistent cache

mà semantic identity không thay đổi.

---

# 14. TypeInterner

Type system sẽ có lượng type cực lớn.

Ví dụ:

```text
Vec<i32>
Vec<i32>
Vec<i32>
```

không nên tạo ba semantic type khác nhau.

Type interner:

```text
TypeKey
    ↓
TypeId
```

Ví dụ:

```text
TypeKey = Vec(TypeId(i32))
```

→

```text
TypeId(72)
```

Mọi nơi dùng `Vec<i32>` đều nhận cùng `TypeId`.

---

# 15. Type canonicalization

Các type phải được canonicalize.

Ví dụ:

```text
(i32, f32)
```

luôn có một canonical representation.

Tương tự:

```text
fn(i32) -> i32
```

và generic applied types.

Điều này giúp:

```text
type equality
trait solving
memoization
incremental compilation
optimization
```

đơn giản hơn rất nhiều.

---

# 16. Query System

Đây là phần tôi đặc biệt khuyến nghị Axiom làm ngay từ đầu.

Thay vì:

```text
parse()
resolve()
typecheck()
...
```

theo kiểu pipeline cứng hoàn toàn, dùng query engine:

```text
Query<Key> → Value
```

Ví dụ:

```text
parse(FileId)
resolve(ModuleId)
hir(ItemId)
type(FunctionId)
mir(FunctionId)
verified_mir(FunctionId)
api(ModuleId)
abi(FunctionId)
```

---

# 17. Query có dependency

Ví dụ:

```text
verified_mir(foo)
```

phụ thuộc:

```text
mir(foo)
type(foo)
trait_resolution(...)
ownership(foo)
capability(foo)
drop(foo)
```

Query engine ghi lại dependency:

```text
verified_mir(foo)
        │
        ├── mir(foo)
        ├── type(foo)
        ├── ownership(foo)
        ├── capability(foo)
        └── drop(foo)
```

Nếu source thay đổi:

```text
foo.ax
```

compiler **không compile lại toàn bộ project**.

---

# 18. Incremental invalidation

Ví dụ:

```text
math.ax
 └── fn add()

main.ax
 └── add()
```

Nếu sửa body:

```text
fn add(a, b) -> i32 {
    a + b
}
```

thành:

```text
fn add(a, b) -> i32 {
    a - b
}
```

API vẫn:

```text
fn add(i32, i32) -> i32
```

→ không cần re-typecheck consumer chỉ vì body thay đổi.

Nhưng:

```text
fn add(a: i64, b: i64) -> i64
```

→ API fingerprint thay đổi.

→ consumer cần invalidate.

---

# 19. Query layers

Nên chia:

```text
Source Query
    ↓
Syntax Query
    ↓
Name Query
    ↓
Type Query
    ↓
Semantic Query
    ↓
MIR Query
    ↓
Verified MIR Query
    ↓
Optimization Query
    ↓
Codegen Query
    ↓
Object Query
```

Mỗi tầng có cache riêng.

---

# 20. Query không được có hidden side effect

Một query:

```text
type_of(expr)
```

không được:

- ghi file
- gọi network
- random
- đọc environment
- thay đổi global state

Nếu cần external capability:

```text
comptime
build capability
tool execution
```

phải đi qua boundary được khai báo.

---

# 21. Compiler Determinism

Cùng:

```text
source
compiler version
language version
target
profile
dependencies
configuration
capabilities
```

phải tạo cùng semantic result.

Không được để:

```text
hash-map iteration order
thread scheduling
memory address
host timezone
random seed
```

ảnh hưởng semantic output.

---

# 22. Parallel compiler

Compiler phải được thiết kế để parallel từ đầu.

Có thể:

```text
parse(file A)
parse(file B)
parse(file C)
```

song song.

Hoặc:

```text
typecheck(foo)
typecheck(bar)
typecheck(baz)
```

song song khi dependency cho phép.

Nhưng output phải deterministic.

---

# 23. Không dùng global mutable semantic state

Cấm kiến trúc kiểu:

```text
GLOBAL_SYMBOL_TABLE
GLOBAL_TYPE_TABLE
GLOBAL_CURRENT_MODULE
GLOBAL_DIAGNOSTICS
```

vì nó sẽ phá:

- parallelism
- incremental compilation
- compiler-as-service
- LSP
- testing
- multi-session compilation.

---

# 24. Diagnostic Engine

Diagnostic không phải string.

```text
Diagnostic {
    code
    severity
    message
    primary
    secondary[]
    notes[]
    helps[]
    fixes[]
    semantic_context
}
```

Ví dụ:

```text
AX_MOVE_0003
```

là semantic identity của lỗi.

Message có thể thay đổi.

---

# 25. Diagnostic ID vs Error Code

Phải phân biệt:

```text
ErrorCode
```

và:

```text
DiagnosticId
```

Ví dụ một source có:

```text
x moved here
x used here
```

có thể tạo hai diagnostic instance:

```text
DiagnosticId(100)
DiagnosticId(101)
```

nhưng cùng:

```text
AX_MOVE_0003
```

---

# 26. Machine-readable diagnostic

Compiler phải hỗ trợ:

```bash
axiom check --format=json
```

Ví dụ conceptual:

```json
{
  "code": "AX_MOVE_0003",
  "severity": "error",
  "primary": {
    "file": "main.ax",
    "start": 120,
    "end": 121
  }
}
```

IDE và AI agent không được parse text human-readable để đoán lỗi.

---

# 27. Pass Manager

Mỗi compiler phase phải có contract.

Ví dụ:

```text
Pass {
    name
    input_ir
    output_ir
    required_invariants
    established_invariants
    preserves
}
```

Ví dụ:

```text
OwnershipPass

Input:
    Typed HIR

Requires:
    TYPE_VALID

Produces:
    OWNERSHIP_VALID
```

Sau đó:

```text
CapabilityPass
```

requires:

```text
TYPE_VALID
OWNERSHIP_VALID
```

---

# 28. Verified MIR là checkpoint cứng

Đây là một trong những quyết định quan trọng nhất.

```text
MIR
 ↓
Verifier
 ↓
Verified MIR
 ↓
Optimizer
```

Optimizer **không được tự sửa semantic invariant**.

Nếu optimizer tạo:

```text
invalid ownership
```

thì đó là compiler bug.

Do đó:

```text
Verified MIR
```

là boundary tin cậy.

---

# 29. IR IDs

MIR instruction:

```text
InstrId
```

Block:

```text
BlockId
```

Local:

```text
LocalId
```

Place:

```text
PlaceId
```

Không dùng pointer identity.

Ví dụ:

```text
MirFunction {
    locals: Arena<Local>
    blocks: Arena<BasicBlock>
    instructions: Arena<Instruction>
}
```

---

# 30. Compiler Cache Boundary

Không cache mọi thứ một cách tùy tiện.

Đề xuất:

```text
Source Cache
    ↓
SIF Cache
    ↓
HIR Cache
    ↓
Typed HIR Cache
    ↓
MIR Cache
    ↓
Verified MIR Cache
    ↓
LIR Cache
    ↓
Object Cache
```

Cache key phải bao gồm semantic context cần thiết.

Ví dụ object cache:

```text
SourceHash
CompilerSemanticVersion
Target
ABI
OptimizationProfile
CPUFeatures
DependencyAPIHash
CodegenConfig
```

---

# 31. Semantic vs implementation cache

Không được nhầm:

```text
APIHash
```

với:

```text
CodegenHash
```

Ví dụ thay đổi:

```text
fn foo() {
    let x = 1;
    let y = 2;
    x + y
}
```

thành:

```text
fn foo() {
    3
}
```

API giống nhau.

Semantic result có thể giống.

Nhưng machine code có thể thay đổi.

Do đó:

```text
APIHash == unchanged
CodegenHash == changed
```

---

# 32. Compiler target/profile configuration

Không để backend đọc trực tiếp environment.

Có:

```text
CompilationConfig {
    target
    profile
    optimization
    debug
    panic_strategy
    lto
    cpu_features
    sanitizer
    gpu_target
    deterministic
}
```

Backend chỉ nhận config đã resolve.

---

# 33. TargetDescription

Kernel không hiểu x86.

Nhưng `TargetConfig` có thể tham chiếu:

```text
TargetId
```

và backend resolve:

```text
TargetDescription
```

Sau đó:

```text
TargetDescription {
    architecture
    pointer_width
    endian
    os
    environment
    object_format
    abi
    features
}
```

---

# 34. Internal compiler errors

Compiler crash không được biến thành:

```text
Segmentation fault
```

không giải thích được.

Mọi internal failure phải tạo:

```text
AXC_INTERNAL_xxxx
```

kèm:

```text
compiler version
target
pass
query
source location
IR snapshot
stack trace
cache state
```

Ví dụ:

```text
AXC_INTERNAL_0042

Verifier invariant violated:
Capability references unknown owner.

Pass: VerifiedMIR
Function: foo
```

---

# 35. Compiler panic ≠ Axiom panic

Đây là distinction bắt buộc.

```text
Axiom program panic
```

là semantics của ngôn ngữ.

Trong khi:

```text
compiler internal failure
```

là compiler bug.

Không được dùng chung model.

---

# 36. Compiler Thread Safety

Các object immutable sau khi publish nên có thể đọc đồng thời:

```text
SourceText
Type
SIF
HIR
MIR
TargetDescription
```

Mutable state nên nằm ở:

```text
QueryDatabase
CacheStore
DiagnosticSink
```

và có synchronization rõ ràng.

Mục tiêu cuối:

```text
N worker threads
        ↓
deterministic compiler result
```

---

# 37. Kernel invariants

Tôi đề xuất khóa bộ invariant đầu tiên.

### Compiler identity

```text
ACKERNEL-20
Semantic entities have typed IDs.

ACKERNEL-21
Semantic identity is distinct from memory address.

ACKERNEL-22
Session IDs are distinct from persistent cache identities.

ACKERNEL-23
Different ID domains are not implicitly interchangeable.
```

### Source

```text
ASOURCE-20
Span identity is byte-based.

ASOURCE-21
Line/column are derived presentation data.

ASOURCE-22
Source identity is distinct from filesystem path strings.

ASOURCE-23
Generated source has explicit source identity.

ASOURCE-24
Source text is immutable within a compilation snapshot.
```

### Interning

```text
AINTERN-20
Equal interned strings share identity within a session.

AINTERN-21
String identity is distinct from symbol identity.

AINTERN-22
Canonical types have unique TypeId within a session.

AINTERN-23
Interning does not define language semantics beyond identity equality.
```

### Query

```text
AQUERY-20
Queries are deterministic for identical semantic inputs.

AQUERY-21
Query dependencies are explicitly recorded.

AQUERY-22
Invalidation follows dependency changes.

AQUERY-23
Query evaluation has no undeclared semantic side effects.

AQUERY-24
Query results may be cached.

AQUERY-25
Cache identity is distinct from session object identity.
```

### Parallelism

```text
APAR-20
Independent queries may execute concurrently.

APAR-21
Parallel execution cannot change semantic results.

APAR-22
Compiler semantic state has no hidden global mutable singleton.

APAR-23
Diagnostic ordering is deterministic.
```

### Diagnostics

```text
ADIAG-20
Diagnostic codes are stable semantic categories.

ADIAG-21
Diagnostic instances have independent identity.

ADIAG-22
Machine-readable diagnostics do not depend on human message text.

ADIAG-23
Source spans in diagnostics refer to source database identities.

ADIAG-24
Compiler internal failures are distinct from Axiom program failures.
```

### Passes

```text
APASS-20
Every semantic pass declares its input contract.

APASS-21
Every semantic pass declares the invariants it establishes.

APASS-22
A pass cannot assume an invariant not established by its input contract.

APASS-23
Verified MIR is the semantic verification checkpoint.

APASS-24
Optimization cannot invalidate Verified MIR semantics.
```

### Cache

```text
ACACHE-20
Cache keys include all semantic inputs relevant to the cached result.

ACACHE-21
API identity is distinct from code-generation identity.

ACACHE-22
Cache contents cannot change program semantics.

ACACHE-23
Stale cache entries are safely invalidated or ignored.

ACACHE-24
Cache lookup failure falls back to recomputation.
```

### Determinism

```text
ADET-20
Compilation semantics are independent of thread scheduling.

ADET-21
Compilation semantics are independent of hash-map iteration order.

ADET-22
Compilation semantics are independent of host memory addresses.

ADET-23
Undeclared environment state cannot affect semantic compilation.

ADET-24
Deterministic mode produces reproducible semantic artifacts.
```

---

# 38. Kernel API conceptual

To make this concrete, tôi đề xuất API nội bộ gần như sau:

```text
CompilerSession
    ├── sources() -> SourceDatabase
    ├── queries() -> QueryDatabase
    ├── diagnostics() -> DiagnosticStore
    ├── packages() -> PackageGraph
    ├── target() -> TargetConfig
    └── cache() -> CacheStore
```

Source:

```text
SourceDatabase
    load(...)
    source(FileId)
    span_text(Span)
    line_col(Span)
    hash(FileId)
```

Queries:

```text
QueryDatabase
    parse(FileId)
    resolve(ModuleId)
    hir(ItemId)
    type(TypeQuery)
    mir(FunctionId)
    verified_mir(FunctionId)
    api(ModuleId)
    abi(FunctionId)
    object(ObjectQuery)
```

Diagnostics:

```text
DiagnosticStore
    emit(Diagnostic)
    all()
    errors()
    warnings()
```

Interners:

```text
StringInterner
TypeInterner
SymbolTable
```

---

# 39. Một thay đổi kiến trúc rất đáng làm ngay

Tôi khuyên **không xây compiler như một pipeline function-call đơn giản**:

```text
parse()
 → resolve()
 → typecheck()
 → mir()
 → codegen()
```

mà xây:

```text
                  Query Engine
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
      parse         resolve         package
        │              │
        └───────┬──────┘
                ▼
               HIR
                │
        ┌───────┴────────┐
        ▼                ▼
      types            traits
        │                │
        └───────┬────────┘
                ▼
               MIR
                │
          ownership/capability
                │
                ▼
          Verified MIR
                │
        ┌───────┴────────┐
        ▼                ▼
      Oracle          Optimizer
                         │
                         ▼
                        LIR
```

Điều này ban đầu phức tạp hơn một chút, nhưng về sau sẽ cực kỳ có giá trị cho:

- incremental compilation
- IDE/LSP
- AI coding agent
- `inspect`
- parallel compilation
- compiler daemon
- self-hosting
- huge projects

---

# 40. Milestone KERNEL-001

Không viết lexer ngay.

Trước tiên implementation agent phải tạo được:

```text
compiler/
├── kernel/
│   ├── ids
│   ├── source
│   ├── span
│   ├── interner
│   ├── arena
│   ├── diagnostics
│   ├── query
│   ├── cache
│   ├── session
│   └── config
```

và chạy được:

```text
axiom check empty.ax
```

với:

```axiom
```

→

```text
0 errors
```

Sau đó:

```text
axiom check empty.ax --format=json
```

→ JSON hợp lệ.

---

# 41. Test đầu tiên

### Source

```text
fn main() {}
```

Ở thời điểm kernel chưa có parser, chỉ cần test source database.

Ví dụ:

```text
FileId(0)
Span {
    file: FileId(0),
    start: 0,
    end: 12
}
```

Test:

```text
span_text(span) == "fn main() {}"
```

Sau đó sửa whitespace:

```text
fn  main() {}
```

kiểm tra:

- Span byte chính xác
- line map chính xác
- source hash thay đổi
- FileId không đổi trong session

---

# 42. Query test

Tạo mock query:

```text
parse(FileId)
```

Sau đó:

```text
resolve(ModuleId)
```

ghi dependency:

```text
resolve → parse
```

Sửa source.

Kiểm tra:

```text
parse invalidated
resolve invalidated
```

nhưng query không phụ thuộc source thì:

```text
cache hit
```

Đây chính là nền incremental compiler.

---

# 43. Một nguyên tắc tôi muốn khóa rất mạnh

### Compiler implementation có thể phức tạp.

Nhưng semantic kernel phải:

```text
deterministic
typed
explicit
queryable
cacheable
parallelizable
```

Không nên tối ưu code kernel quá sớm.

Ưu tiên:

```text
correct identity
→ correct dependency
→ correct invalidation
→ deterministic result
→ performance
```

---

# 44. Sau Kernel: Lexer

Khi `KERNEL-001` hoàn thành, thứ tự chính xác nên là:

```text
KERNEL
  ↓
LEXER
  ↓
PARSER
  ↓
AST
  ↓
RESOLVER
  ↓
HIR
  ↓
TYPE SYSTEM
```

Nhưng có một điểm quan trọng:

**Lexer phải được viết theo SPEC-01, không theo “cảm giác giống Rust/C”.**

Ngay từ lexer phải khóa:

- UTF-8
- Unicode identifier
- keyword
- numeric literal
- string
- byte string
- comments
- nested block comments
- operators
- ranges
- `@attributes`
- `?`
- `->`
- `=>`
- `..`
- `..=`

và đặc biệt phải thiết kế lexer sao cho sau này **không cần phá grammar khi thêm generic/trait/comptime**.

### Bước tiếp theo tôi sẽ đi thẳng vào:

**AXIOM LEXICAL SPEC v0.1 — Unicode, identifier, literal, comment, operator và tokenizer state machine**, sau đó thiết kế luôn **token set + golden tests + lexer error codes** để agent có thể bắt đầu code ngay.