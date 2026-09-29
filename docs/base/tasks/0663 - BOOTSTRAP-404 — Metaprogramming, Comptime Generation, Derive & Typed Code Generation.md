# BOOTSTRAP-404 — Metaprogramming, Comptime Generation, Derive & Typed Code Generation

Sau `403`, bước tiếp theo hợp lý là khóa **hệ thống metaprogramming**.

Đây là phần đặc biệt quan trọng đối với Axiom vì mục tiêu của chúng ta không phải tạo một ngôn ngữ có thật nhiều syntax, mà là để **compiler hiểu sâu và tự động sinh phần lớn boilerplate**.

Nguyên tắc nền tảng:

> **Axiom ưu tiên typed generation hơn textual macro.**

Tức là:

```text
Comptime
   ↓
Typed declarations / expressions
   ↓
HIR
   ↓
Normal compiler verification
```

chứ không phải:

```text
string manipulation
   ↓
text source
   ↓
reparse
```

---

# 1. Ba loại metaprogramming

Axiom phân biệt:

```text
1. Compile-time value computation
2. Compile-time declaration generation
3. Compile-time source transformation
```

Core v1 chỉ cần hai loại đầu.

### Value computation

```axiom
const N = comptime fibonacci(20)
```

### Declaration generation

```axiom
@derive(Serialize)
struct User {
    id: u64
    name: String
}
```

Compiler tạo implementation.

---

# 2. Comptime không phải macro

`comptime` là execution trong compiler environment.

Ví dụ:

```axiom
comptime {
    const table = generate_lookup_table()
}
```

Nó chạy code Axiom bình thường theo semantics của compile-time.

Không tạo một ngôn ngữ thứ hai.

---

# 3. Metaprogramming phải type-safe

Generated declaration phải đi qua:

```text
Parser
→ Resolver
→ Type checker
→ Ownership verifier
→ Capability verifier
→ Effect verifier
→ ABI verifier
```

Không có đường tắt:

```text
generator → “compiler tin tôi”
```

trừ những compiler intrinsic đặc biệt đã được trusted.

---

# 4. Type reflection

Comptime có thể nhận `Type`.

Ví dụ:

```axiom
comptime fn inspect<T>() {
    let size = size_of::<T>()
}
```

`Type<T>` là **compile-time value**.

Không tạo runtime type object.

---

# 5. Type metadata

Compiler reflection có thể truy vấn:

```text
name
kind
fields
field types
visibility
attributes
traits
methods
generic parameters
layout
alignment
```

Ví dụ concept:

```axiom
comptime fn fields<T>() -> []FieldInfo
```

---

# 6. Reflection phải tôn trọng visibility

Một package không được dùng comptime reflection để đọc private implementation của package khác.

Ví dụ:

```text
Package A
private field secret
```

Package B:

```text
reflection(A.User)
```

không được nhìn thấy `secret` nếu API policy không cho phép.

---

# 7. Representation reflection

Có hai tầng:

```text
Semantic Reflection
Representation Reflection
```

Semantic:

```text
field name
field type
trait
method
```

Representation:

```text
offset
alignment
size
ABI
```

Representation reflection chỉ được expose khi representation contract cho phép.

---

# 8. Struct generation

Đây là use case chính.

Ví dụ:

```axiom
@derive(Debug)
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Compiler-generated implementation tương đương semantic:

```text
impl Debug for Vec3
```

Nhưng generated implementation không cần xuất hiện như source file thật.

---

# 9. Derive

`@derive(...)` là compiler-known typed generation.

Ví dụ:

```axiom
@derive(
    Clone,
    Debug,
    Serialize,
    Deserialize
)
struct User {
    ...
}
```

Mỗi derive plugin/compiler component nhận:

```text
TypeDefinition
```

và trả:

```text
GeneratedDeclarations
```

---

# 10. Không cho derive tùy tiện sửa type

Derive được phép:

```text
generate methods
generate trait impl
generate helper declarations
generate metadata
```

Không được:

```text
delete field
change field type
change ownership semantics
change ABI
```

trừ khi declaration explicitly requests một representation transform riêng.

---

# 11. Attribute system

Axiom cần một attribute mechanism thống nhất:

```axiom
@inline
@noinline
@repr(C)
@align(64)
@packed
@deprecated
@cfg(...)
@derive(...)
@kernel
```

Attribute phải có schema.

Không phải string tùy ý mà compiler không hiểu.

---

# 12. Attribute namespace

Để tránh collision:

```text
@axiom.inline
@serde.serialize
@gpu.kernel
```

hoặc namespace tương đương.

Core attributes có namespace riêng.

Library/plugin attributes không được giả mạo core semantic.

---

# 13. Attribute validation

Ví dụ:

```axiom
@align(3)
struct Foo {}
```

Compiler reject vì alignment không hợp lệ.

Tương tự:

```axiom
@kernel
fn foo() {
    open_file(...)
}
```

reject vì GPU legality.

Attribute chỉ là metadata nếu compiler đã validate semantic effect của nó.

---

# 14. Typed AST API

Axiom **không nên** expose AST mutation API trong Core v1.

Thay vì:

```text
parse source
modify arbitrary AST
print source
reparse
```

dùng:

```text
DeclarationBuilder
FunctionBuilder
TypeBuilder
TraitImplBuilder
```

hoặc compiler-internal equivalent.

---

# 15. Generated HIR

Pipeline:

```text
Comptime Generator
        ↓
Typed Declaration IR
        ↓
Generated HIR
        ↓
Normal verification
```

Generated HIR có provenance:

```text
generated_from:
    generator_id
    input_types
    comptime_inputs
```

---

# 16. Không textual code generation mặc định

Ví dụ không nên khuyến khích:

```axiom
generate("fn foo() { ... }")
```

Thay vào đó:

```axiom
let f = FunctionBuilder(...)
```

Điều này tránh:

- syntax injection
- escaping
- parser ambiguity
- accidental invalid source
- source formatting problems.

---

# 17. Generated source khi cần

Tuy nhiên build system vẫn có thể sinh `.ax`.

Ví dụ:

```text
schema.json
   ↓
schema compiler
   ↓
schema.generated.ax
```

Đây là **Build Generation**, không phải Core metaprogramming.

File generated sau đó đi qua compiler bình thường.

---

# 18. Compile-time capability

Comptime tiếp tục dùng capability model đã khóa trước đó.

Ví dụ:

```text
ReadSource
ReadMetadata
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

Không có capability thì operation không tồn tại.

---

# 19. Sandbox

Comptime mặc định sandbox.

Ví dụ compiler build hermetic:

```text
ReadFilesystem = denied
Network = denied
ExecuteTool = denied
```

Generator chỉ có:

```text
ReadSource
ReadMetadata
```

thì build vẫn deterministic.

---

# 20. Comptime resource lifetime

Comptime cũng dùng:

```text
ownership
move
drop
capability
```

Không tạo một memory model khác.

Compiler VM có thể allocate heap nội bộ nhưng:

```text
compiler memory
≠
program runtime memory
```

---

# 21. Comptime side effects

Mọi external side effect phải explicit.

Ví dụ:

```text
read file
execute process
network request
environment read
```

được ghi vào build dependency graph.

Do đó:

```text
generator output
```

không thể âm thầm thay đổi theo môi trường.

---

# 22. Reproducible comptime

Trong reproducible mode:

```text
Time
Random
Environment
Network
```

phải bị hạn chế hoặc virtualize.

Random có thể dùng deterministic seed được compiler cấp.

---

# 23. Compile-time errors

Nếu comptime code:

```axiom
comptime fn generate() {
    assert(false)
}
```

thì đây là:

```text
compile-time diagnostic
```

không phải runtime panic.

---

# 24. Comptime panic vs compiler bug

Phải phân biệt:

```text
UserComptimeError
CompilerICE
```

Ví dụ generator gọi:

```axiom
panic("invalid schema")
```

→ diagnostic của user.

Compiler interpreter crash:

```text
segmentation fault inside compiler
```

→ ICE.

---

# 25. Generic specialization

Metaprogramming phối hợp với generics.

Ví dụ:

```axiom
fn serialize<T: Serialize>(x: T)
```

compiler có thể specialize:

```text
Serialize<User>
```

và derive cung cấp implementation.

Không cần reflection runtime.

---

# 26. Specialization phải giữ semantic identity

Compiler không được coi:

```text
generic function
```

và:

```text
specialized function
```

là hai semantic API khác nhau.

Specialization là optimization/code generation consequence.

---

# 27. Compile-time branching

Có:

```axiom
@cfg(target.os == "windows")
```

và:

```axiom
comptime if condition {
    ...
}
```

Khác nhau:

### `@cfg`

Loại bỏ declaration/configuration trước semantic analysis tương ứng.

### `comptime if`

Là compile-time control flow trong một chương trình comptime.

---

# 28. Target-aware generation

Generator có thể hỏi:

```text
target.arch
target.os
target.pointer_width
target.endianness
target.features
```

Nhưng target-dependent information phải lấy từ **target context**, không phải host machine.

Điều này đặc biệt quan trọng cross-compilation.

---

# 29. Compile-time layout generation

Ví dụ FFI:

```axiom
comptime fn generate_bindings<T>() {
    let size = target.size_of<T>()
    ...
}
```

Compiler phải xác định rõ:

```text
host layout
target layout
```

Không được nhầm.

---

# 30. Compile-time generated registries

Axiom có thể dùng comptime để tạo:

```text
command registry
serializer table
RPC dispatch table
reflection table
GPU kernel registry
test registry
plugin table
```

Ví dụ:

```axiom
@register(Command)
struct AddCommand { ... }
```

Compiler tạo registry static.

Không cần runtime reflection.

---

# 31. Link-time metadata

Generated metadata có thể tồn tại ở:

```text
compile-time
object metadata
link-time metadata
runtime metadata
```

Không mặc định đưa mọi metadata vào binary.

---

# 32. Runtime reflection optional

Nếu application cần runtime reflection:

```axiom
@runtime_reflect
struct User { ... }
```

compiler mới emit metadata.

Nếu không:

```text
binary = no reflection metadata
```

Điều này phù hợp mục tiêu binary nhỏ.

---

# 33. Procedural macro không vào Core v1

Không đóng cửa vĩnh viễn.

Nhưng v0.1/v1:

```text
❌ arbitrary procedural macros
❌ arbitrary AST mutation
❌ arbitrary MIR mutation
❌ source-to-source macro language
```

Chỉ cần:

```text
comptime
derive
attributes
typed generation
```

Đã đủ cho phần lớn use case.

---

# 34. Trusted compiler extensions

Sau này compiler có thể hỗ trợ:

```text
CompilerPlugin
```

nhưng phải nằm ngoài safe language semantics.

Plugin có thể:

```text
inspect HIR
generate HIR
provide diagnostics
provide derive
```

Không được tùy ý thay đổi safety rules.

---

# 35. Plugin ABI

Plugin interface cần versioned:

```text
AxiomCompilerPluginABI
```

Plugin khai báo:

```text
compiler API version
semantic API version
target support
capabilities
```

Plugin không được assume compiler internal layout.

---

# 36. AI-friendly generation

Đây là một điểm nên thiết kế riêng cho Axiom.

Compiler có thể expose semantic schema:

```text
TypeSchema
FunctionSchema
TraitSchema
ModuleSchema
BuildSchema
```

AI agent có thể hỏi:

```text
"generate implementation of Trait X for Type Y"
```

và nhận structured API thay vì phải manipulate raw text.

---

# 37. Compiler-generated documentation

Reflection + metadata có thể sinh:

```text
API documentation
JSON schema
FFI headers
language bindings
IDE metadata
```

từ cùng một semantic source.

Không cần parser riêng cho từng tool.

---

# 38. Compile-time serialization

Có thể:

```axiom
@derive(Serialize)
```

và compiler tạo:

```text
serialize<T>
deserialize<T>
```

Nhưng serialization format vẫn là library/domain concern.

Core chỉ cung cấp generation infrastructure.

---

# 39. Comptime cache

Generator output phải cache được.

Cache key:

```text
generator fingerprint
+ input semantic fingerprints
+ comptime dependency fingerprints
+ compiler semantic version
+ target/config
```

Nếu tất cả giống nhau:

```text
comptime cache hit
```

---

# 40. Generated code cache không được bypass verification

Ngay cả cache hit:

```text
cached generated HIR
```

vẫn phải có semantic identity tương thích.

Compiler có thể bỏ qua generation execution, nhưng không được bỏ qua compatibility/verification cần thiết.

---

# 41. CompilerDB bổ sung

```text id="x0j8da"
ComptimeProgramDB
ComptimeExecutionDB
ComptimeInputDB
ComptimeOutputDB
ComptimeCapabilityDB
ComptimeSandboxDB
ComptimeCacheDB
ComptimeDependencyDB

ReflectionDB
TypeReflectionDB
FieldReflectionDB
MethodReflectionDB
TraitReflectionDB
LayoutReflectionDB
TargetReflectionDB

AttributeDB
AttributeSchemaDB
AttributeValidationDB

DeriveDB
DeriveInputDB
DeriveOutputDB

GenerationDB
GeneratedDeclarationDB
GeneratedHIRDB
GeneratedSourceDB
GeneratedProvenanceDB

RuntimeReflectionDB

CompilerPluginDB
CompilerPluginABIDB
CompilerPluginCapabilityDB

SemanticSchemaDB
AISchemaDB
```

---

# 42. Metaprogramming IR

Đề xuất:

## AMETA

Compiler-level representation:

```text
META_TYPE_QUERY
META_FIELD_QUERY
META_METHOD_QUERY
META_TRAIT_QUERY
META_LAYOUT_QUERY

META_CONST_EVAL
META_CFG_EVAL

META_DECLARE_STRUCT
META_DECLARE_ENUM
META_DECLARE_FUNCTION
META_DECLARE_IMPL
META_DECLARE_TRAIT

META_GENERATE
META_ATTACH_ATTRIBUTE
META_EMIT_METADATA
```

AMETA không tồn tại trong runtime.

---

# 43. Provenance model

Generated declaration:

```text
GeneratedNode {
    id
    generator
    inputs
    source_location
    target
}
```

Ví dụ:

```text
User.serialize
```

có thể trace:

```text
User
 ↓
@derive(Serialize)
 ↓
SerializeGenerator
 ↓
GeneratedImpl
 ↓
HIR
 ↓
MIR
```

Debugger/compiler diagnostics có thể dùng trace này.

---

# 44. Proofs

BOOTSTRAP-404 bổ sung:

```text
ComptimeSafetyProof
ComptimeCapabilityProof
ComptimeSandboxProof
ComptimeDeterminismProof

ReflectionVisibilityProof
ReflectionRepresentationProof

AttributeValidityProof
DeriveValidityProof
GeneratedDeclarationProof
GeneratedHIRProof
GeneratedProvenanceProof

TargetContextProof
HostTargetSeparationProof

ComptimeCacheValidityProof
RuntimeReflectionEmissionProof

PluginABIVerificationProof
PluginCapabilityProof

AISchemaConsistencyProof
```

---

# 45. Invariants — AMETA-01 → AMETA-30

**AMETA-01** — Comptime execution phải dùng cùng semantic type/ownership model với runtime khi semantics tương ứng.

**AMETA-02** — Comptime external capability phải được khai báo.

**AMETA-03** — External comptime input phải trở thành BuildGraph dependency.

**AMETA-04** — Sandbox phải enforce capability boundary.

**AMETA-05** — Reproducible mode không được phụ thuộc undeclared nondeterminism.

**AMETA-06** — Host và target comptime context phải phân biệt.

**AMETA-07** — Comptime error phải phân biệt với compiler ICE.

**AMETA-08** — Comptime output phải có deterministic identity.

**AMETA-09** — Comptime cache chỉ valid khi mọi input fingerprint hợp lệ.

**AMETA-10** — Cache hit không được bypass semantic verification cần thiết.

**AMETA-11** — Reflection phải tôn trọng visibility.

**AMETA-12** — Representation reflection phải tôn trọng representation contract.

**AMETA-13** — Runtime type metadata không được emit nếu không được yêu cầu.

**AMETA-14** — `@derive` chỉ được generate declaration hợp lệ.

**AMETA-15** — Derive không được âm thầm thay đổi source type semantics.

**AMETA-16** — Attribute phải được validate theo schema.

**AMETA-17** — Attribute không được tự động tạo semantic authority vượt declaration contract.

**AMETA-18** — Generated declaration phải đi qua normal resolution/type checking.

**AMETA-19** — Generated code phải đi qua ownership verification.

**AMETA-20** — Generated code phải đi qua capability/effect verification.

**AMETA-21** — Generated declaration phải có provenance.

**AMETA-22** — Textual generation không được là đường mặc định cho typed generation.

**AMETA-23** — Generated source phải được đưa trở lại BuildGraph.

**AMETA-24** — Compiler plugin không được phá semantic safety invariants.

**AMETA-25** — Plugin ABI phải versioned.

**AMETA-26** — Plugin capability phải được khai báo.

**AMETA-27** — Generic specialization không được thay đổi observable semantics.

**AMETA-28** — `@cfg` và `comptime if` phải có semantic phase distinction rõ ràng.

**AMETA-29** — AI-facing semantic schema phải phản ánh cùng CompilerDB semantic model.

**AMETA-30** — Không có metaprogramming mechanism nào được phép tạo một “đường tắt” bypass compiler verification.

---

# 46. Kiến trúc sau BOOTSTRAP-404

Axiom lúc này có một chuỗi khá hoàn chỉnh:

```text
                 SOURCE
                    │
                    ▼
                 MODULE
                    │
                    ▼
                 PACKAGE
                    │
                    ▼
              DEPENDENCY GRAPH
                    │
                    ▼
                COMPILERDB
                    │
          ┌─────────┴─────────┐
          │                   │
       COMPTIME            REFLECTION
          │                   │
          ▼                   ▼
      GENERATION            DERIVE
          │                   │
          └─────────┬─────────┘
                    ▼
              GENERATED HIR
                    │
                    ▼
             NORMAL VERIFIER
                    │
                    ▼
                   MIR
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       DEBUG      TEST      PROFILE
          │         │         │
          └─────────┼─────────┘
                    ▼
              MACHINE CODE
```

Và đây là điểm tôi cho rằng rất đáng giữ làm **nguyên tắc kiến trúc lâu dài của Axiom**:

> **Metaprogramming được phép làm compiler biết thêm nhiều thứ, nhưng không được tạo ra một compiler thứ hai nằm ngoài compiler.**

Nhờ vậy Axiom có thể đạt mức tự động hóa rất cao — `derive`, serialization, bindings, registry, reflection, GPU dispatch, RPC, schema generation, AI tooling... — mà **không phải trả giá bằng một hệ thống macro phức tạp, khó debug và khó đảm bảo safety**.