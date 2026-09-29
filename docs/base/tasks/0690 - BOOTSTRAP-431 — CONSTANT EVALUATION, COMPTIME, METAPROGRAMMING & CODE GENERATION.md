# BOOTSTRAP-431 — CONSTANT EVALUATION, COMPTIME, METAPROGRAMMING & CODE GENERATION

431 khóa toàn bộ **compile-time computation** của Axiom. Mục tiêu là có comptime đủ mạnh để xây thư viện, tối ưu compiler và hỗ trợ AI/tooling, nhưng **không biến Axiom thành một ngôn ngữ có hai hệ runtime phức tạp**.

---

## 431.1 — Mục tiêu

Axiom có ba mức:

```text
constant
    ↓
comptime
    ↓
code generation / metaprogramming
```

Trong đó:

- `constant` — biểu thức compile-time đơn giản.
- `comptime` — chương trình nhỏ chạy bởi compiler.
- metaprogramming — tạo/biến đổi declaration hoặc metadata.
- code generation — tạo semantic entities/IR có kiểm soát.

---

# 431.2 — Nguyên tắc cốt lõi

Comptime phải:

```text
deterministic
sandboxed
resource-bounded
cacheable
reproducible
type-safe
```

Không được mặc định có:

```text
network access
filesystem write
process execution
environment mutation
unbounded execution
```

---

# 431.3 — Constant expression

Ví dụ:

```text
const SIZE: usize = 1024 * 1024
```

Compiler evaluate trực tiếp.

---

# 431.4 — Constant evaluation không phải runtime execution

Ví dụ:

```text
const X: i32 = calculate()
```

Nếu `calculate()` đủ điều kiện comptime, compiler chạy nó tại compile time.

Runtime binary không cần chứa computation đó.

---

# 431.5 — `const fn`

Một function có thể được đánh dấu:

```text
const fn factorial(n: u64) -> u64 {
    if n <= 1 {
        return 1
    }

    n * factorial(n - 1)
}
```

Có thể gọi ở compile time.

---

# 431.6 — Const function cũng chạy runtime được

```text
x := factorial(n)
```

nếu `n` runtime thì function vẫn có thể được compile thành machine code bình thường.

Một implementation duy nhất phục vụ cả hai context.

---

# 431.7 — Const eligibility

`const fn` không được thực hiện operation mà compiler không thể sandbox.

Ví dụ mặc định không cho:

```text
const fn load() {
    network_request()
}
```

---

# 431.8 — Const call graph

Nếu:

```text
const fn A() {
    B()
}
```

thì `B()` phải comptime-compatible nếu A được evaluate compile-time.

Compiler kiểm tra toàn bộ reachable call path trong evaluation.

---

# 431.9 — Compile-time context

Các context tự động yêu cầu constant:

```text
const X = ...
array<T, N>
```

và những nơi grammar/semantic quy định giá trị phải biết tại compile time.

---

# 431.10 — Explicit comptime block

Để programmer yêu cầu compile-time execution:

```text
comptime {
    generate_tables()
}
```

Block này không được emit trực tiếp thành runtime code.

---

# 431.11 — Comptime expression

Có thể dùng:

```text
x := comptime calculate()
```

khi cần force evaluation.

Nếu không evaluate được → compile error thay vì fallback runtime.

---

# 431.12 — `comptime` không phải macro

```text
comptime foo()
```

thực hiện computation.

Macro/code generation là layer khác.

---

# 431.13 — Comptime types

Comptime có thể thao tác với:

```text
type
value
metadata
```

nhưng mỗi category có API rõ ràng.

---

# 431.14 — Type values

Compiler meta-layer có thể biểu diễn:

```text
Type
```

Ví dụ:

```text
comptime {
    t := type_of(MyStruct)
}
```

---

# 431.15 — Type introspection

Compiler intrinsic:

```text
type_of<T>()
```

hoặc equivalent compile-time form.

Có thể lấy:

```text
name
size
alignment
fields
methods
traits
```

nếu metadata visibility cho phép.

---

# 431.16 — Reflection không mặc định runtime

Introspection compile-time **không có nghĩa** binary phải chứa reflection metadata.

Nếu chương trình không yêu cầu runtime reflection:

```text
no RTTI
no type names
no field metadata
```

được emit.

---

# 431.17 — Compile-time field inspection

Ví dụ conceptual:

```text
comptime {
    for field in fields(User) {
        ...
    }
}
```

Compiler chạy loop này trong comptime evaluator.

---

# 431.18 — Compile-time type queries

Hỗ trợ các query từ 430:

```text
sizeof<T>()
alignof<T>()
implements<T, Trait>()
```

và:

```text
field_count<T>()
```

nếu metadata API cung cấp.

---

# 431.19 — Compile-time constants

Cho phép:

```text
const MAX = 1024
const MASK = 0xFF
const ENABLED = true
```

---

# 431.20 — Constant propagation

Compiler có thể tự propagate:

```text
const A = 10
const B = A * 20
```

mà không cần programmer viết `comptime`.

---

# 431.21 — Constant folding

Machine-independent IR được fold:

```text
3 * 7
```

→

```text
21
```

---

# 431.22 — Floating constant folding

Được phép nếu compiler tuân thủ floating semantics 430.

`@fast_math` có thể mở rộng optimization rules.

---

# 431.23 — Compile-time branching

```text
comptime if condition {
    ...
}
```

được evaluate tại compile time.

Code branch không được chọn có thể bị loại hoàn toàn.

---

# 431.24 — Compile-time loop

```text
comptime for i in 0..16 {
    ...
}
```

phục vụ generated declarations/data.

---

# 431.25 — Compile-time recursion

Được phép nhưng có depth/step limit.

Ví dụ:

```text
const FIB_20 = fib(20)
```

hợp lệ.

---

# 431.26 — Evaluation fuel

Comptime evaluator có giới hạn:

```text
max_steps
max_recursion
max_memory
max_output
max_generated_entities
```

tránh compiler bị treo vì comptime program.

---

# 431.27 — Diagnostic khi vượt giới hạn

Ví dụ:

```text
E431201 COMPTIME_LIMIT

compile-time evaluation exceeded
maximum evaluation steps: 10,000,000
```

Compiler nên chỉ rõ call stack comptime.

---

# 431.28 — Comptime stack trace

Diagnostic:

```text
comptime evaluation failed

foo() 
 └─> build_table()
      └─> calculate()
           └─> division by zero
```

rất hữu ích cho AI agent.

---

# 431.29 — Compile-time panic

Comptime có thể fail:

```text
panic("invalid configuration")
```

Compiler biến failure thành diagnostic.

Không tạo runtime panic.

---

# 431.30 — Comptime Result

Có thể dùng:

```text
const VALUE: Result<i32, Error> = ...
```

Nếu `Err`, declaration không hợp lệ nếu context yêu cầu successful constant.

---

# 431.31 — Allocation trong comptime

Comptime evaluator có thể có **compiler-owned temporary heap**.

Ví dụ xử lý:

```text
String
Vec
Map
```

trong comptime.

Những allocation này không đi vào executable.

---

# 431.32 — Comptime memory

Comptime memory là sandbox riêng:

```text
source
    ↓
comptime VM/interpreter
    ↓
temporary memory
    ↓
result
    ↓
discard
```

Không sử dụng trực tiếp process heap của compiler.

---

# 431.33 — Runtime allocation không được vô tình gọi

Nếu function gọi runtime allocator mà không có comptime implementation:

```text
const X = runtime_alloc()
```

→ compile-time error.

---

# 431.34 — Const data generation

Comptime có thể tạo:

```text
const TABLE: [u16; 256] = ...
```

Compiler embed data trực tiếp vào binary.

---

# 431.35 — Lookup table generation

Ví dụ:

```text
const SIN_TABLE = comptime generate_sine_table(1024)
```

Runtime chỉ load static data.

---

# 431.36 — SIMD data generation

Có thể generate:

```text
const LUT: [f32; 1024]
```

cho DSP/ML/graphics.

---

# 431.37 — Compile-time validation

Ví dụ:

```text
comptime assert(sizeof<MyStruct>() == 32)
```

Nếu false:

```text
E431301 COMPTIME_ASSERT_FAILED
```

---

# 431.38 — Static assertions

Syntax ngắn:

```text
static_assert(sizeof(Header) == 64)
```

được lower thành compile-time assertion.

---

# 431.39 — Compile-time string processing

Cho phép:

```text
const VERSION = concat("Axiom ", "1.0")
```

và:

```text
comptime hash("hello")
```

---

# 431.40 — Compile-time UTF-8 validation

String literal UTF-8 được compiler validate.

Comptime API có thể inspect code points/bytes.

---

# 431.41 — Compile-time parser

Axiom có thể viết parser chạy comptime:

```text
const CONFIG = comptime parse_config("""
...
""")
```

Đây là use case quan trọng cho metaprogramming.

---

# 431.42 — Comptime file access

**Không mặc định cho phép arbitrary filesystem access.**

Thay vào đó compiler cung cấp explicit resource API nếu build system cho phép.

Ví dụ conceptual:

```text
comptime read_resource("schema.json")
```

phải:

- được build system khai báo;
- nằm trong dependency graph;
- có content hash;
- reproducible.

---

# 431.43 — Resource dependency hashing

Nếu comptime đọc resource:

```text
schema.json
```

thay đổi → cache entry liên quan phải invalidated.

---

# 431.44 — Network access

Comptime không được network mặc định.

Nếu build tool cần network:

```text
external build step
```

không phải language comptime.

---

# 431.45 — Environment variables

Environment không được implicit dependency.

Nếu cần:

```text
build configuration
```

phải được truyền explicit vào compiler/build system.

---

# 431.46 — Current time/randomness

Không cho:

```text
const BUILD_TIME = now()
```

nếu mục tiêu reproducible build.

Build metadata phải explicit:

```text
build_timestamp
```

được compiler/build system inject.

---

# 431.47 — Randomness

Comptime random generator chỉ được dùng nếu seed explicit.

```text
comptime rng(seed)
```

→ deterministic.

---

# 431.48 — Side-effect model

Comptime function nên chia:

```text
pure
resource
generation
```

Compiler biết dependency type.

---

# 431.49 — Pure comptime

Pure computation:

```text
const X = fibonacci(20)
```

có thể cache aggressively.

---

# 431.50 — Resource-dependent comptime

Nếu phụ thuộc file/schema/config:

```text
cache key
=
source hash
+
resource hashes
+
compiler version
```

---

# 431.51 — Comptime cache

Kết quả comptime có thể cache theo:

```text
module
function identity
arguments
compiler version
target
resource fingerprints
```

---

# 431.52 — Cross-build cache

Cache comptime phải phân biệt:

```text
target-independent
target-dependent
```

Ví dụ:

```text
hash("hello")
```

target-independent.

Trong khi:

```text
sizeof<usize>()
```

target-dependent.

---

# 431.53 — Comptime determinism

Cùng:

```text
source
compiler version
target
inputs
```

phải tạo cùng kết quả comptime.

---

# 431.54 — Host/target separation

Compiler chạy trên host A nhưng target B.

Comptime phải xác định rõ đang evaluate theo:

```text
host
```

hay:

```text
target
```

Mặc định:

**language semantics = target configuration**, không phải host.

---

# 431.55 — Target-dependent constant

```text
sizeof<usize>()
```

dùng target ABI.

Ví dụ x86-64:

```text
8
```

---

# 431.56 — Host-only compiler API

Compiler API như:

```text
AST inspection
diagnostics
code generation
```

chạy trong host compiler environment.

Không trộn với target runtime APIs.

---

# 431.57 — Metaprogramming

Metaprogramming là khả năng tạo language entities:

```text
struct
enum
fn
impl
const
```

---

# 431.58 — Declaration generation

Conceptual:

```text
comptime generate_struct("Vec", fields)
```

Compiler tạo declaration semantic.

Không generate raw source text bắt buộc.

---

# 431.59 — AST generation

Axiom có thể expose structured syntax API:

```text
Expr
TypeExpr
Decl
Pattern
```

nhưng đây là **meta API**, không phải runtime type.

---

# 431.60 — Token generation

Macro layer có thể tạo token stream:

```text
TokenStream
```

và parse lại bằng compiler.

---

# 431.61 — Prefer semantic generation

Nếu có thể, ưu tiên:

```text
semantic declaration API
```

thay vì:

```text
string concatenation
```

Ví dụ không nên:

```text
generate("fn foo() { ... }")
```

nếu có API structured.

---

# 431.62 — Hygiene

Macro/code generation phải có hygienic identifier handling.

Compiler-generated local:

```text
tmp
```

không được vô tình capture user `tmp`.

---

# 431.63 — Explicit capture

Nếu macro muốn access identifier từ caller scope, phải có explicit mechanism.

---

# 431.64 — Macro namespace

Generated entities phải có source origin:

```text
generated_by
macro_id
source_span
```

để diagnostics truy ngược.

---

# 431.65 — Macro errors

Ví dụ:

```text
macro `derive_serializable` failed

generated field:
    User.email

reason:
    unsupported type: RawSocket
```

---

# 431.66 — Derive-like generation

Axiom có thể hỗ trợ:

```text
@derive(Serializable)
struct User {
    ...
}
```

Compiler invokes registered compile-time generator.

---

# 431.67 — Generated implementation

Conceptual output:

```text
impl Serializable for User {
    ...
}
```

nhưng compiler không nhất thiết phải tạo source file vật lý.

---

# 431.68 — Serialization example

```text
@derive(Serializable, Debug)
struct User {
    id: u64
    name: String
}
```

Comptime generator inspect fields and emit specialized implementation.

Runtime:

```text
user.serialize()
```

→ static dispatch.

Không cần reflection.

---

# 431.69 — Generic derive

```text
@derive(Serializable)
struct Container<T: Serializable> {
    value: T
}
```

Generated implementation preserves generic constraint.

---

# 431.70 — Code generation and generics

Generated generic code phải đi qua cùng:

```text
type checker
trait resolver
ownership checker
```

Không có “unsafe semantic bypass” chỉ vì code do compiler generate.

---

# 431.71 — Generated code ownership

Compiler-generated code có ownership semantics giống source code.

---

# 431.72 — Generated code diagnostics

Error phải hiển thị cả:

```text
user source
generator source
generated semantic entity
```

khi cần.

---

# 431.73 — Macro expansion order

Pipeline:

```text
parse
 ↓
declarations
 ↓
macro discovery
 ↓
comptime expansion
 ↓
expanded AST/semantic graph
 ↓
type checking
 ↓
lowering
```

Macro-generated declarations có thể được type-checked như ordinary declarations.

---

# 431.74 — Recursive generation

Macro không được vô hạn tự generate.

Compiler giới hạn:

```text
expansion_depth
generated_nodes
generated_bytes
```

---

# 431.75 — Compile-time generic specialization

Comptime có thể inspect generic type:

```text
comptime if implements<T, SIMD> {
    ...
}
```

để generate optimized implementation.

---

# 431.76 — Specialization boundary

Không cho comptime silently tạo semantics khác với generic contract.

Specialized implementation vẫn phải satisfy trait/API contract.

---

# 431.77 — Compile-time feature detection

```text
comptime if target.arch == "x86_64" {
    ...
}
```

được phép.

---

# 431.78 — Target feature query

Ví dụ:

```text
target.has("avx2")
target.has("neon")
```

cho phép chọn implementation.

---

# 431.79 — CPU dispatch

Comptime không thay thế runtime CPU dispatch.

Nếu binary cần chạy trên nhiều CPU:

```text
if cpu_has_avx2() {
    avx2_impl()
} else {
    scalar_impl()
}
```

Runtime dispatch vẫn tồn tại.

---

# 431.80 — Platform conditional compilation

Có thể:

```text
comptime if target.os == Windows {
    ...
}
```

nhưng nên có shorthand attribute:

```text
@target(os = "windows")
```

cho declaration-level filtering.

---

# 431.81 — Dead generated code elimination

Nếu comptime condition loại branch:

```text
comptime if false {
    ...
}
```

branch không được emit.

---

# 431.82 — No runtime comptime marker

`comptime` không tạo runtime instruction.

---

# 431.83 — Comptime VM

Implementation recommendation:

```text
Axiom source
    ↓
AST / typed IR
    ↓
Comptime IR
    ↓
interpreter
```

Không cần compile comptime code thành native machine code mỗi lần.

---

# 431.84 — Why interpreter first

Interpreter:

- dễ sandbox;
- deterministic;
- dễ giới hạn resource;
- dễ debug;
- dễ cache.

Sau này có thể JIT compile comptime hot paths nếu cần.

---

# 431.85 — Comptime IR reuse

Comptime evaluator nên dùng subset mở rộng của Axiom IR thay vì tạo một ngôn ngữ hoàn toàn khác.

Mục tiêu:

```text
one language
two execution contexts
```

---

# 431.86 — Unsupported operation

Nếu evaluator gặp:

```text
syscall
raw OS handle
runtime thread
```

mà context không cho phép:

```text
E431401 NON_COMPTIME_OPERATION
```

---

# 431.87 — Comptime concurrency

Không cho arbitrary thread spawning trong comptime.

Compiler có thể internally parallelize independent evaluations, nhưng semantic result không phụ thuộc execution order.

---

# 431.88 — Comptime async

Không cần async trong comptime v0.

Comptime phải hoàn thành synchronously.

---

# 431.89 — Comptime ownership

Comptime vẫn tuân theo move/drop semantics.

Tuy nhiên temporary allocations được compiler-owned và tự giải phóng khi evaluation kết thúc.

---

# 431.90 — Compile-time drop

Destructor có side effects observable không nên được chạy trong constant evaluation nếu side effect không được sandbox/define.

Các comptime types nên ưu tiên pure/trivial cleanup.

---

# 431.91 — Constant value serialization

Kết quả comptime phải có canonical representation:

```text
ConstValue
```

gồm:

```text
integer
float
bool
char
string
array
tuple
struct
enum
```

và các giá trị compiler-supported khác.

---

# 431.92 — Embed constant into binary

Compiler lower:

```text
const TABLE = ...
```

thành read-only data section khi phù hợp.

---

# 431.93 — Mutable static initialization

Nếu:

```text
static X: SomeType = ...
```

không thể static-initialize trực tiếp, compiler phải dùng initialization mechanism rõ ràng.

Không silently chạy arbitrary constructor trước `main`.

---

# 431.94 — Compile-time generated machine data

Có thể generate:

```text
const CODE: [u8; N]
```

nhưng **không mặc định cho phép arbitrary machine code injection**.

Executable code phải đi qua compiler/linker semantics.

---

# 431.95 — Embedded resources

Comptime có thể generate binary resources:

```text
const ICON: []const u8 = embed("icon.png")
```

nếu build system khai báo resource.

---

# 431.96 — Resource embedding

Resource hash phải nằm trong dependency graph để incremental compilation chính xác.

---

# 431.97 — Build reproducibility

Compiler build output phải reproducible nếu:

```text
same source
same compiler
same target
same explicit inputs
```

---

# 431.98 — AI-friendly metadata

Comptime-generated entities phải giữ metadata:

```text
origin
generator
inputs
dependencies
generated hash
```

Điều này giúp AI agent hiểu:

> declaration này do đâu sinh ra và thay đổi input nào sẽ làm nó thay đổi.

---

# 431.99 — Comptime API stability

Core comptime API phải nhỏ.

V0 chỉ cần:

```text
comptime
const
const fn
static_assert
type queries
target queries
basic reflection
generation hooks
```

Không đưa toàn bộ compiler internals vào language API.

---

# 431.100 — Conformance tests

```text
CT-001   const arithmetic
CT-002   const fn
CT-003   recursive const fn
CT-004   const generic
CT-005   const array
CT-006   const struct
CT-007   const enum
CT-008   constant folding
CT-009   comptime block
CT-010   forced comptime
CT-011   comptime branch
CT-012   comptime loop
CT-013   comptime allocation
CT-014   comptime limits
CT-015   comptime diagnostics
CT-016   static_assert
CT-017   type introspection
CT-018   sizeof/alignof
CT-019   trait introspection
CT-020   field introspection
CT-021   compile-time string processing
CT-022   resource dependency
CT-023   deterministic evaluation
CT-024   target-dependent evaluation
CT-025   target-independent cache
CT-026   macro generation
CT-027   hygiene
CT-028   derive generation
CT-029   generated generic implementation
CT-030   generated-code diagnostics
CT-031   generated-code ownership
CT-032   feature detection
CT-033   resource embedding
CT-034   no-runtime-reflection build
CT-035   reproducible build
```

---

# 431.101 — Final contract

Axiom comptime chính thức:

```text
                 AXIOM
                   │
        ┌──────────┴──────────┐
        │                     │
     RUNTIME               COMPTIME
        │                     │
 native machine          sandboxed evaluator
        │                     │
 executable              ConstValue
                              │
                 ┌────────────┴────────────┐
                 │                         │
             constants                generation
                                         │
                                  AST / semantic entities
```

Nguyên tắc quan trọng nhất:

> **Comptime là một execution context của chính Axiom, không phải một ngôn ngữ thứ hai.**

Vì vậy programmer có thể viết một thuật toán một lần:

```text
const fn make_table(...)
```

và compiler có thể chạy nó lúc build hoặc emit nó thành machine code khi gọi với runtime input.

**BOOTSTRAP-431 hoàn tất.**

---

# BOOTSTRAP-432 — MODULE SYSTEM, PACKAGE MODEL, NAMESPACE, DEPENDENCY GRAPH & BUILD SEMANTICS

Task kế tiếp sẽ khóa cách Axiom tổ chức project lớn:

```text
source files
    ↓
modules
    ↓
packages
    ↓
dependencies
    ↓
interfaces
    ↓
incremental compilation
    ↓
native artifacts
```

Đặc biệt sẽ giải quyết **package không phụ thuộc package manager bên thứ ba**, module visibility, cyclic dependency, import/export, build profiles, cross-compilation, dependency hashing và cách compiler biết chính xác phần nào cần rebuild.