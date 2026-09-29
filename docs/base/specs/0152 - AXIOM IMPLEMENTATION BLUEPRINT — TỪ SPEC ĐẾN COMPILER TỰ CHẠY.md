# AXIOM IMPLEMENTATION BLUEPRINT — TỪ SPEC ĐẾN COMPILER TỰ CHẠY

Bây giờ chuyển hẳn từ **Language Design** sang **Engineering**.

Mục tiêu không phải xây từng module đến 100% rồi mới sang module tiếp theo. Cách đó dễ tạo ra một compiler “đẹp nhưng chưa bao giờ chạy được”.

Axiom nên được xây theo **vertical slices**:

> **Mỗi milestone phải tạo ra một hệ thống chạy được, kiểm chứng được, rồi mới mở rộng.**

---

# 1. Kiến trúc implementation cuối

```text
                    ┌──────────────────┐
                    │   Axiom Source   │
                    └────────┬─────────┘
                             │
                        Lexer / Parser
                             │
                             ▼
                           AST
                             │
                         Resolver
                             │
                             ▼
                            HIR
                             │
                        Type Checker
                             │
                             ▼
                       Typed HIR
                             │
              ┌──────────────┴──────────────┐
              │                             │
       Ownership/Capability           Trait/Generic
              │                             │
              └──────────────┬──────────────┘
                             ▼
                            MIR
                             │
                         Verifier
                             │
                             ▼
                      Verified MIR
                             │
                  ┌──────────┴──────────┐
                  │                     │
                Oracle               Optimizer
                  │                     │
                  │                     ▼
                  │                    LIR
                  │                     │
                  │                Target Backend
                  │                     │
                  │                     ▼
                  │                Machine IR
                  │                     │
                  │                Encoder
                  │                     │
                  │                     ▼
                  │                   Object
                  │                     │
                  └──────────────►   Linker
                                        │
                                        ▼
                                  Native Binary
```

Điểm quan trọng:

**Oracle nằm song song với production backend**, không nằm trong runtime của chương trình.

---

# 2. Không bắt đầu bằng parser

Đây là thay đổi quan trọng so với cách xây compiler thông thường.

Trước parser phải xây:

```text
spec/
tests/
oracle model/
diagnostic model/
IR contracts/
```

Vì nếu không:

```text
parser → compiler code → semantic assumptions
```

sẽ dần trở thành specification ngầm.

Axiom phải đi ngược:

```text
SPEC
 ↓
INVARIANT
 ↓
TEST
 ↓
IMPLEMENTATION
```

---

# 3. Repository chính thức

Tôi đề xuất repository:

```text
axiom/
│
├── spec/
│   ├── SPEC-01-lexical.md
│   ├── SPEC-02-grammar.md
│   ├── ...
│   ├── SPEC-30-conformance.md
│   │
│   ├── memory-model.md
│   ├── ownership.md
│   ├── capability.md
│   ├── concurrency.md
│   ├── async.md
│   ├── ffi-abi.md
│   └── invariants.md
│
├── compiler/
│   ├── source/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── typeck/
│   ├── hir/
│   ├── traits/
│   ├── ownership/
│   ├── capability/
│   ├── drop/
│   ├── async/
│   ├── mir/
│   ├── verifier/
│   ├── optimizer/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   ├── object/
│   ├── linker/
│   └── driver/
│
├── oracle/
│
├── targets/
│   ├── x86_64/
│   ├── aarch64/
│   ├── riscv64/
│   ├── wasm32/
│   └── ...
│
├── runtime/
│   ├── startup/
│   ├── panic/
│   ├── unwind/
│   ├── thread/
│   └── async/
│
├── std/
│
├── tests/
│
├── tools/
│
└── bootstrap/
```

---

# 4. Compiler implementation language

Có một vấn đề thực tế:

> Axiom chưa tồn tại, vậy compiler đầu tiên viết bằng gì?

Không nên cố self-host ngay.

## Stage 0

Dùng một implementation language tạm thời có:

- filesystem
- process
- hash map
- Unicode
- testing
- debugger
- concurrency

để xây bootstrap compiler.

Nhưng:

> **Implementation language của Stage 0 không phải một phần của Axiom semantics.**

---

# 5. Bootstrap compiler phải có “semantic independence”

Không được để:

```text
Axiom semantics
    ↓
Rust/C++ library behavior
    ↓
Axiom behavior
```

Ví dụ nếu compiler host dùng Rust:

```text
Rust Vec
Rust ownership
Rust integer overflow
```

không được vô tình trở thành semantics của:

```text
Axiom Vec
Axiom ownership
Axiom arithmetic
```

Host implementation chỉ là implementation detail.

---

# 6. Stage 0 — Compiler Kernel

Trước parser đầy đủ, xây:

```text
compiler/
├── ids
├── spans
├── source
├── diagnostics
├── arena
├── interner
├── symbol
├── type-id
└── test-framework
```

### Stable IDs

Mọi semantic object nên dùng ID:

```text
FileId
ModuleId
SymbolId
TypeId
TraitId
FunctionId
FieldId
VariantId
LocalId
BlockId
InstrId
AllocationId
DiagnosticId
```

Không truyền object graph bằng raw pointers trong compiler implementation nếu không cần.

---

# 7. Source database

Compiler cần một source abstraction:

```text
SourceDatabase
```

Có:

```text
FileId
SourceText
Span
LineMap
ModuleId
```

Mọi diagnostic dùng:

```text
FileId + byte range
```

không dùng line/column làm identity.

Line/column chỉ là presentation.

---

# 8. Interning

Các object xuất hiện cực nhiều:

```text
Type
Name
Generic parameter
Trait reference
Constant
```

nên intern.

Ví dụ:

```text
TypeId(42)
NameId(17)
```

thay vì copy string/type tree liên tục.

Điều này vừa nhanh compiler vừa làm equality rẻ.

---

# 9. Diagnostic engine trước parser

Ví dụ:

```text
Diagnostic {
    code: AX_PARSE_0001
    severity: Error
    primary: Span
    secondary: [...]
    notes: [...]
    helps: [...]
    fixes: [...]
}
```

Parser chỉ emit semantic diagnostic object.

CLI mới quyết định:

```text
human
json
lsp
```

---

# 10. Stage 1 — Lexer

Lexer phải cực kỳ đơn giản và deterministic.

Output:

```text
Token {
    kind
    span
}
```

Không resolve identifier ở lexer.

Ví dụ:

```text
foo
```

chỉ là:

```text
IDENT
```

Không phải `FunctionName`.

---

# 11. Token model

Nên có token categories:

```text
IDENT
INT
FLOAT
STRING
BYTE_STRING
CHAR       // nếu char được freeze
KEYWORD
OPERATOR
PUNCT
EOF
```

Không để lexer chứa semantic logic.

---

# 12. Lexer test

Mỗi token:

```text
source
→ tokens
```

có golden test.

Đặc biệt:

```text
1
1u32
1.0
1e10
0xff
0b101
```

và:

```text
"a"
b"..."
```

---

# 13. Stage 2 — Parser

Parser tạo:

```text
AST
```

AST **không cần chứa semantic type**.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST:

```text
FunctionDecl
 ├── name
 ├── params
 ├── return_type
 └── body
      └── BinaryExpr(+)
```

---

# 14. Parser không kiểm tra ownership

Không làm:

```text
parser sees:
x = y
→ move
```

Đó là việc của HIR/type/ownership.

Đây là một boundary phải giữ rất sạch.

---

# 15. Stage 3 — Resolver

Resolver biến:

```text
identifier
```

thành:

```text
SymbolId
```

Ví dụ:

```text
x
```

→

```text
LocalId(7)
```

Không còn phụ thuộc vào string lookup sau semantic lowering.

---

# 16. Name resolution

Thứ tự đã freeze:

```text
local
↓
parameter
↓
current module
↓
explicit import
↓
re-export
↓
prelude
```

Resolver phải implement đúng thứ tự này.

---

# 17. Stage 4 — HIR

HIR là nơi AST bắt đầu trở thành semantic representation.

Ví dụ:

```text
HIR::Call {
    function: FunctionId,
    args: [...]
}
```

thay vì:

```text
Call {
    callee_name: "foo"
}
```

---

# 18. Tại sao cần HIR?

Vì AST tối ưu cho:

```text
source structure
```

HIR tối ưu cho:

```text
semantic analysis
```

MIR tối ưu cho:

```text
execution
```

Ba thứ không nên trộn.

---

# 19. Stage 5 — Type system

Đây là subsystem rất lớn.

```text
TypeKind
├── Bool
├── Integer
├── Float
├── Unit
├── Never
├── Tuple
├── Struct
├── Enum
├── Array
├── Function
├── Closure
├── View
├── MutView
├── RawPointer
├── GenericParam
├── AppliedGeneric
├── DynTrait
└── ImplTrait
```

---

# 20. Type identity

Không dùng string comparison.

Ví dụ:

```text
Vec<i32>
```

phải canonicalize thành:

```text
TypeId
```

và:

```text
Vec<i32>
```

ở hai nơi phải cùng `TypeId`.

---

# 21. Type checking không làm ownership hoàn chỉnh

Đây là boundary rất quan trọng.

Type checker:

```text
x: Vec<i32>
```

Ownership checker:

```text
x = MOVED
```

Capability checker:

```text
view(x)
```

Drop checker:

```text
drop(x)
```

Các subsystem phối hợp nhưng không nên gom thành một giant checker.

---

# 22. Stage 6 — Trait solver

Trait solver có:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Không bao giờ:

```text
guess
```

Nếu:

```text
AMBIGUOUS
```

→ compile error.

---

# 23. Trait solver cache

Các query:

```text
T: Trait
```

xuất hiện rất nhiều.

Cần cache:

```text
TraitQueryKey
→ TraitQueryResult
```

Nhưng cache phải invalidatable theo semantic environment/package fingerprint.

---

# 24. Stage 7 — Ownership engine

Đây là “trái tim” của Axiom.

Không bắt đầu bằng borrow checker.

Thay vào đó xây:

```text
OwnershipState
```

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

và:

```text
Place
```

Ví dụ:

```text
x
x.field
x.field.subfield
array[i]
```

---

# 25. Place-based ownership

Compiler cần biểu diễn:

```text
Place {
    root: LocalId,
    projections: [...]
}
```

Ví dụ:

```axiom
user.profile.name
```

thành:

```text
user
 → field(profile)
 → field(name)
```

Điều này cho phép partial move.

---

# 26. Ownership state machine

Ví dụ:

```text
let x = Foo()
```

```text
x: UNINIT → OWNED
```

Sau:

```text
let y = x
```

```text
x → MOVED
y → OWNED
```

Sau:

```text
drop(y)
```

```text
y → DROPPED
```

---

# 27. Copy

Nếu:

```text
T: Copy
```

thì:

```text
let y = x
```

không chuyển ownership.

Semantic:

```text
x → OWNED
y → OWNED
```

nhưng là hai value identity.

---

# 28. Stage 8 — Capability engine

Capability là một subsystem riêng.

```text
Capability {
    owner
    region
    access
    lifetime
    provenance
}
```

Access:

```text
READ
WRITE
```

---

# 29. Region engine

Region relation:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Compiler không cần luôn biết exact byte address.

Nó cần biết:

> Có khả năng overlap hay không?

---

# 30. Capability conflict

Ví dụ:

```text
view(x.a)
mut_view(x.b)
```

Nếu:

```text
a ∩ b = ∅
```

→ valid.

Nhưng:

```text
view(x)
mut_view(x.a)
```

→ conflict.

---

# 31. Stage 9 — Drop elaboration

Đây là bước biến ownership semantics thành MIR cleanup.

Ví dụ:

```axiom
fn foo() {
    let a = A()
    let b = B()
    return
}
```

MIR semantic:

```text
DROP b
DROP a
RETURN
```

---

# 32. Drop elaboration phải chạy sau ownership analysis

Không nên parser/type checker tự chèn Drop.

Pipeline:

```text
Typed HIR
 ↓
Ownership analysis
 ↓
Move analysis
 ↓
Drop elaboration
 ↓
MIR
```

---

# 33. Stage 10 — MIR

MIR nên là IR **ownership-aware nhưng machine-neutral**.

Ví dụ:

```text
%1 = CONST 10
%2 = CONST 20
%3 = ADD %1, %2
RETURN %3
```

---

# 34. MIR Place

Memory operations:

```text
FIELD_PLACE
INDEX_PLACE
DEREF_PLACE
```

để verifier hiểu:

```text
load/store/drop
```

đang tác động lên object nào.

---

# 35. MIR ownership instructions

Các instruction:

```text
COPY
MOVE
DROP
VIEW
VIEW_MUT
```

là semantic instructions.

Sau khi verified:

```text
ownership metadata
```

có thể được erase.

---

# 36. Stage 11 — Verifier

Verified MIR là checkpoint quan trọng nhất.

Verifier phải kiểm tra:

```text
type
ownership
capability
drop
control flow
match exhaustiveness
async rules
atomic rules
unsafe boundaries
```

Nếu MIR chưa verified:

> **Không được đưa vào optimizer/backend.**

---

# 37. Đây là một security boundary

Pipeline:

```text
MIR
 ↓
Verifier
 ↓
Verified MIR
```

Optimizer chỉ nhận:

```text
Verified MIR
```

Điều này ngăn optimizer vô tình “tối ưu” một chương trình semantic-invalid.

---

# 38. Stage 12 — Oracle

Oracle nhận Verified MIR.

Có thể chạy:

```text
axiom interpret file.ax
```

Ví dụ:

```text
fn main() {
    print("hello")
}
```

Oracle phải chạy được trước native backend.

---

# 39. Vertical Slice #1

Đây là milestone đầu tiên thực sự quan trọng.

Chỉ cần:

```text
fn main() {
    return
}
```

Compiler phải:

```text
parse
→ resolve
→ typecheck
→ HIR
→ MIR
→ verify
→ Oracle
```

Chưa cần native binary.

---

# 40. Vertical Slice #2

Thêm:

```axiom
fn main() {
    let x = 42
}
```

Compiler phải test:

```text
let
integer
local
Drop/Copy classification
```

---

# 41. Vertical Slice #3

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    let x = add(10, 20)
}
```

Đến đây có:

```text
function
call
integer
return
```

---

# 42. Vertical Slice #4 — Native

Bây giờ mới xây:

```text
MIR
 ↓
LIR
 ↓
x86-64
 ↓
machine code
 ↓
ELF
```

và:

```text
fn main() {}
```

phải tạo executable.

Đây là **First Native Axiom Program**.

---

# 43. Không cần assembler

x86 backend có thể trực tiếp encode:

```text
machine bytes
```

Ví dụ:

```text
MOV
ADD
RET
CALL
JMP
```

Object writer tạo ELF.

Không cần:

```text
Axiom → assembly text → assembler
```

Điều này phù hợp mục tiêu cuối cùng:

> compiler tự chủ.

---

# 44. Stage 13 — Minimal ELF writer

Ban đầu chỉ cần:

```text
ELF64
x86_64
Linux
```

Support:

```text
.text
.rodata
.data
.bss
.symtab
.strtab
.rela.text
```

đủ để chạy chương trình cơ bản.

---

# 45. Stage 14 — Minimal linker

Không cần linker “đầy đủ” ngay.

Đầu tiên:

```text
one object
→ executable
```

Sau đó:

```text
multiple objects
→ symbol resolution
→ relocation
```

Sau nữa:

```text
static libraries
dynamic libraries
TLS
PIE
debug
```

---

# 46. Stage 15 — `print`

Không đưa `print` vào language.

Tạo:

```text
std/io
```

và hosted runtime:

```text
startup
```

`main()` vẫn là language concept.

`print()` là library.

---

# 47. Stage 16 — Strings

Implement:

```text
Text
Bytes
```

nhưng không cần Unicode hoàn chỉnh ngay.

Compiler cần:

```text
string literal
```

được lower thành read-only static data.

---

# 48. Stage 17 — Struct

Sau primitive execution:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

MIR phải support:

```text
AGGREGATE
FIELD
LOAD
STORE
```

---

# 49. Stage 18 — Enum

Sau struct:

```axiom
enum Option<T> {
    None,
    Some(T),
}
```

Compiler cần:

```text
tag
payload
match
```

Đây là nơi test algebraic data thực sự bắt đầu.

---

# 50. Stage 19 — Ownership

Sau struct/enum:

```text
Move
Copy
Drop
partial move
```

được test thực tế.

Đây là lúc Axiom bắt đầu khác biệt rõ với C.

---

# 51. Stage 20 — Views

Implement:

```text
view<T>
mut_view<T>
```

và các test:

```text
read
mutation
alias
disjoint fields
relocation
escape
return
```

---

# 52. Stage 21 — Collections

Chỉ sau khi ownership/view đã ổn định mới xây:

```text
Vec
String
Map
```

Nếu làm `Vec` trước ownership verifier, rất dễ phải viết lại toàn bộ.

---

# 53. Stage 22 — Traits/generics

Sau concrete types:

```text
generic
trait
impl
associated type
static dispatch
dyn Trait
```

---

# 54. Stage 23 — Comptime

Comptime phải dùng:

```text
HIR
Typed HIR
MIR
Oracle
```

**không tạo một mini-language riêng.**

Đây là điểm rất quan trọng.

---

# 55. Stage 24 — Async

Không bắt đầu bằng executor.

Đầu tiên:

```text
async fn
await
Future representation
state-machine lowering
```

Sau đó mới:

```text
executor
waker
IO integration
```

---

# 56. Stage 25 — Threads

Sau synchronous concurrency:

```text
Thread
spawn
join
Send
Share
Mutex
Channel
```

---

# 57. Stage 26 — Atomics

Atomic phải test với:

```text
Oracle scheduler
```

và native stress tests.

Không được chỉ test:

```text
single-thread result
```

---

# 58. Stage 27 — FFI

Đầu tiên:

```text
extern "C"
```

chỉ:

```text
i32
u32
pointer
struct repr(C)
```

Sau đó mở rộng.

---

# 59. Stage 28 — Cross target

Sau x86-64 ELF:

```text
AArch64 ELF
x86_64 Windows
AArch64 Mach-O
WASM
RISC-V
```

Không nên xây tất cả cùng lúc.

---

# 60. Stage 29 — Self-hosting

Compiler source bắt đầu chuyển sang:

```text
compiler/
*.ax
```

nhưng **không chuyển toàn bộ cùng lúc**.

Trước tiên:

```text
lexer.ax
parser.ax
ast.ax
```

sau đó:

```text
hir.ax
typeck.ax
mir.ax
```

---

# 61. Stage 30 — Compiler compiles itself

Mục tiêu:

```text
Axiom compiler
    compiled by bootstrap compiler
         ↓
axiomc
         ↓
axiomc builds axiomc
```

Sau đó:

```text
axiomc₁
→ axiomc₂
→ axiomc₃
```

và reproducibility test.

---

# 62. Nhưng có một cải tiến quan trọng

Không nên đợi đến Stage 30 mới test self-hosting.

Ngay từ Stage 4, cần có:

```text
bootstrap/
self_build_test/
```

để compiler architecture luôn:

```text
self-hostable
```

Không cho bootstrap dependency len vào semantic core.

---

# 63. AI-agent architecture

Với cách bạn đang dùng AI agent để xây Axiom, tôi đề xuất compiler repository có thêm:

```text
.ai/
├── invariants/
├── architecture/
├── decisions/
├── tasks/
├── failures/
├── benchmarks/
└── verification/
```

Mỗi task:

```text
TASK-ID
SPEC references
invariants
dependencies
implementation
tests
Oracle tests
acceptance criteria
```

Agent không được tự “sáng tạo semantics”.

---

# 64. Agent workflow

Mỗi task:

```text
READ SPEC
   ↓
READ INVARIANTS
   ↓
SEARCH EXISTING IMPLEMENTATION
   ↓
PLAN
   ↓
IMPLEMENT
   ↓
UNIT TEST
   ↓
CONFORMANCE TEST
   ↓
ORACLE TEST
   ↓
NEGATIVE TEST
   ↓
RUN FULL SUITE
   ↓
COMMIT
```

Nếu phát hiện contradiction:

```text
STOP IMPLEMENTATION
↓
create design issue
↓
update SPEC
↓
update invariant
↓
update tests
↓
resume
```

Không được sửa semantics âm thầm trong code.

---

# 65. Harness cho compiler

Đây là lúc ý tưởng **Genesis Harness** trước đây trở nên rất hữu ích.

Harness nên biết:

```text
spec
invariant
test
oracle
compiler
target
```

và có command kiểu:

```text
axiom-harness check AXOWN-30
```

hoặc:

```text
axiom-harness verify ownership
```

---

# 66. Compiler acceptance command

Cuối cùng cần:

```text
axiom test
```

nhưng bên dưới chạy:

```text
lexer tests
parser tests
semantic tests
negative tests
oracle tests
optimization tests
ABI tests
target tests
```

và:

```text
axiom conformance
```

chạy bộ đầy đủ hơn.

---

# 67. Build graph của chính compiler

Không nên để compiler build bằng script khổng lồ.

Ban đầu có thể dùng bootstrap tooling.

Nhưng build graph phải biểu diễn được:

```text
source
→ generated source
→ compiler object
→ runtime
→ executable
```

để sau này Axiom compiler có thể tự build.

---

# 68. Một quyết định quan trọng về backend

Không xây:

```text
x86 backend
ARM backend
WASM backend
```

bằng cách copy code.

Phải có:

```text
Target-independent LIR
```

sau đó mỗi backend implement:

```text
TargetLowering
InstructionSelector
RegisterFile
CallingConvention
Encoder
ObjectWriter
```

---

# 69. x86-64 backend đầu tiên

Cấu trúc:

```text
targets/x86_64/
├── target.axiom
├── abi/
├── legalize/
├── isel/
├── machine/
├── regalloc/
├── encoder/
└── elf/
```

Ban đầu:

```text
integer
float
load/store
call
return
branch
```

là đủ.

---

# 70. Không xây optimizer trước khi native backend chạy

Sai lầm phổ biến:

```text
parser
→ optimizer 100%
→ backend
```

Axiom nên:

```text
MIR
→ naive LIR
→ native
```

trước.

Sau đó:

```text
correctness
→ optimization
```

---

# 71. Baseline backend

Backend đầu tiên phải cực kỳ ngu nhưng đúng.

Ví dụ:

```text
every local
→ stack slot
```

```text
every operation
→ direct instruction
```

```text
no register allocation sophistication
```

Sau khi chạy được:

```text
native correctness
```

mới tối ưu.

---

# 72. Tại sao cách này quan trọng?

Nếu compiler đã có:

```text
Oracle
+
naive backend
```

thì mọi optimizer sau này đều có oracle:

```text
MIR
→ Oracle result
```

so với:

```text
optimized MIR
→ Oracle result
```

và:

```text
native result
```

Ba tầng đối chiếu.

---

# 73. Optimization ladder

```text
-O0
 ↓
constant folding
 ↓
dead code elimination
 ↓
copy propagation
 ↓
simplify CFG
 ↓
inline
 ↓
scalar replacement
 ↓
bounds-check elimination
 ↓
devirtualization
 ↓
vectorization
 ↓
LTO
 ↓
PGO
```

Không implement tất cả cùng lúc.

---

# 74. Ownership optimization

Một lợi thế đặc biệt của Axiom:

Compiler biết ownership.

Ví dụ:

```axiom
fn make() -> Big {
    let x = Big(...)
    x
}
```

Compiler biết:

```text
return = ownership transfer
```

nên có thể:

```text
construct directly in caller return slot
```

không cần:

```text
temporary
memcpy
heap allocation
```

Đây là một nguồn zero-cost abstraction rất mạnh.

---

# 75. Capability optimization

Sau verification:

```text
view
mut_view
```

không cần tồn tại runtime nếu representation không observable.

Compiler có thể lower:

```text
view<T>
```

thành:

```text
pointer
length
```

hoặc chỉ:

```text
pointer
```

nếu extent compile-time.

---

# 76. Ownership erasure

Sau:

```text
Verified MIR
```

compiler không cần carry:

```text
OWNED
MOVED
DROP state
```

vào machine code nếu không cần.

Chỉ giữ những effect runtime thực sự cần:

```text
destructor
deallocation
synchronization
```

Đây chính là:

> **Abstraction Erasure.**

---

# 77. Compiler performance

Compiler cần profiling ngay từ đầu.

Các metric:

```text
parse time
resolve time
typecheck time
trait solving
ownership analysis
MIR construction
optimization
codegen
link
memory peak
cache hit rate
```

Đừng chỉ benchmark executable.

Compiler chậm sẽ làm AI-agent development cực chậm.

---

# 78. Incremental compilation

Ngay từ đầu thiết kế dependency graph:

```text
source
→ API fingerprint
→ semantic fingerprint
→ codegen fingerprint
```

Không đợi đến cuối mới thêm incremental.

---

# 79. Một module thay đổi private implementation

Ví dụ:

```text
foo.ax
```

private body đổi nhưng:

```text
public API
```

không đổi.

Consumer không cần typecheck lại.

Có thể cần codegen lại tùy:

```text
inline
LTO
generic
```

Nhưng semantic invalidation không lan toàn project.

---

# 80. Compiler development order cuối cùng

Tôi chốt thứ tự:

```text
00  Spec / invariants / tests
01  Compiler kernel
02  Source database
03  Diagnostics
04  Lexer
05  Parser
06  Resolver
07  AST → HIR
08  Type system
09  Trait solver
10  Ownership
11  Capability
12  Drop
13  MIR
14  Verifier
15  Oracle
16  MIR interpreter
17  LIR
18  x86-64 baseline
19  ELF object writer
20  minimal linker
21  first native executable
22  structs/enums
23  collections
24  generics/traits
25  optimizer
26  FFI
27  async
28  concurrency
29  atomics
30  comptime
31  GPU
32  other targets
33  self-hosting
34  reproducible bootstrap
```

---

# 81. Nhưng vertical slices chạy xuyên suốt

Không phải:

```text
01 → 02 → 03 → ... → 34
```

một chiều.

Thực tế:

```text
                ┌──────── Lexer
                │
                ├──────── Parser
                │
                ├──────── Resolver
                │
                ├──────── Type
                │
                ├──────── MIR
                │
                ├──────── Oracle
                │
                └──────── Native
                         ↓
                    FIRST BINARY
```

sau đó từng feature mới đi qua **toàn bộ pipeline**.

---

# 82. Vertical Slice #1 chính thức

Axiom đầu tiên phải compile:

```axiom
fn main() {}
```

và tạo:

```text
hello
```

native executable.

Test:

```text
axiom build hello.ax
./hello
echo $?
```

expected:

```text
0
```

---

# 83. Vertical Slice #2

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() {
    let x = add(20, 22)
}
```

Native compiler phải tạo đúng:

```text
42
```

thông qua return/exit hoặc test harness.

---

# 84. Vertical Slice #3

```axiom
struct Point {
    x: i32
    y: i32
}

fn sum(p: Point) -> i32 {
    p.x + p.y
}
```

Kiểm tra:

```text
struct layout
field projection
Move
Drop classification
return ABI
```

---

# 85. Vertical Slice #4

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

và:

```text
match
?
```

Đây là lúc algebraic control flow hoạt động.

---

# 86. Vertical Slice #5

```axiom
fn sum(v: view<Array<i32, 4>>) -> i32 {
    ...
}
```

Kiểm tra:

```text
owner
view
region
read capability
return
```

---

# 87. Vertical Slice #6

```axiom
fn modify(v: mut_view<Array<i32, 4>>) {
    ...
}
```

Kiểm tra:

```text
exclusive write
alias rejection
```

---

# 88. Vertical Slice #7

```axiom
fn consume(x: Buffer) {
}

fn main() {
    let x = Buffer(...)
    consume(x)
    use(x) // error
}
```

Compiler phải phát:

```text
AX_MOVE_...
```

Oracle không cần chạy vì source invalid.

---

# 89. Vertical Slice #8

```axiom
async fn foo() -> i32 {
    ...
}
```

chưa cần OS async.

Chỉ cần:

```text
async lowering
Future
await
state machine
Oracle
```

---

# 90. Vertical Slice #9

```axiom
spawn(move || work(data))
```

kiểm tra:

```text
capture
ownership transfer
Send
```

---

# 91. Vertical Slice #10

```axiom
Atomic<i32>
```

kiểm tra:

```text
load
store
CAS
ordering
```

---

# 92. Đây mới là điểm Axiom có thể bắt đầu “tự chứng minh”

Mỗi feature mới phải đi theo:

```text
language feature
        ↓
spec rule
        ↓
invariant
        ↓
Oracle
        ↓
compiler
        ↓
native backend
        ↓
conformance
```

Không có feature nào được phép chỉ tồn tại trong compiler implementation.

---

# 93. Compiler architecture đã đủ để bắt đầu

Tại thời điểm này, chúng ta có:

```text
✓ Language specification
✓ Semantic model
✓ Memory model
✓ Ownership model
✓ Capability model
✓ Concurrency model
✓ Async model
✓ ABI model
✓ GPU model
✓ Build model
✓ Oracle
✓ Diagnostics
✓ Tooling
✓ Native pipeline
✓ Conformance
✓ Global contradiction audit
✓ Implementation order
```

Đây là điểm mà **thiết kế Axiom có thể chính thức chuyển sang implementation**.

---

## Bước tiếp theo: **AXIOM COMPILER KERNEL SPEC**

Tôi sẽ không nhảy ngay vào lexer.

Phần tiếp theo cần khóa **compiler internal contracts** trước:

```text
CompilerContext
SourceDatabase
FileId / Span
Interners
SymbolId
TypeId
FunctionId
ModuleId
HIR IDs
MIR IDs
Arena ownership
Query system
Dependency graph
Diagnostic engine
Pass manager
Compiler invariants
Thread-safety của compiler
Incremental compilation
Cache boundaries
```

Đây là phần quyết định compiler có trở thành một codebase vài trăm nghìn dòng khó bảo trì hay một compiler mà **AI agent có thể tự nghiên cứu → sửa → test → chứng minh** một cách có hệ thống.