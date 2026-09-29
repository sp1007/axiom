# BOOTSTRAP-191 — Diagnostics, Error Recovery, IDE Recovery & Partial-Program Semantics
## FROZEN / COMPLETED

Đây là phần rất quan trọng nếu Axiom hướng tới **AI-assisted development + IDE-first workflow**.

Một compiler thực tế không chỉ xử lý:

```text
Program hoàn chỉnh → Compile
```

mà thường xuyên phải xử lý:

```text
Program đang được gõ dở
→ thiếu token
→ thiếu type
→ thiếu generic argument
→ trait chưa resolve
→ function chưa viết xong
```

Axiom phải coi đây là **trạng thái hợp lệ của tooling**, nhưng tuyệt đối không coi nó là chương trình hợp lệ để phát hành.

Nguyên tắc trung tâm:

> **Compiler phải có khả năng hiểu một chương trình chưa hoàn chỉnh mà không biến lỗi gốc thành một thác lỗi giả.**

---

# 1. Hai chế độ semantic

Phải phân biệt:

```text
Complete Semantic Mode
```

và:

```text
Partial Semantic Mode
```

### Complete

Dùng cho:

```text
build
release
link
execute
publish
```

Mọi invariant bắt buộc phải được chứng minh.

### Partial

Dùng cho:

```text
IDE
LSP
completion
hover
AI
incremental editing
```

Có thể tồn tại:

```text
Unknown
Error
Incomplete
Unresolved
```

nhưng **không được coi chúng là proof**.

---

# 2. Error không phải Undefined Behavior

Ví dụ:

```axiom
fn foo(x: ) -> i32 {
```

Compiler có thể tạo:

```text
ErrorType
```

nhưng tuyệt đối không được biến nó thành:

```text
i32
```

một cách ngầm định.

Nguyên tắc:

```text
ErrorType may permit analysis to continue
```

nhưng:

```text
ErrorType never provides a safety proof
```

---

# 3. Error Node trong SyntaxDB

Lossless syntax tree đã có từ BOOTSTRAP-126.

Bổ sung:

```text
MissingToken
UnexpectedToken
SkippedTokens
InvalidToken
IncompleteExpression
IncompleteType
IncompletePattern
```

Ví dụ:

```text
foo(
```

có thể trở thành:

```text
CallExpr
├── callee = foo
├── args = []
└── missing_close_paren
```

thay vì parser chết ngay.

---

# 4. Parser Recovery

Parser phải ưu tiên:

```text
continue parsing
```

thay vì:

```text
abort at first error
```

Các chiến lược:

- insertion recovery
- deletion recovery
- synchronization points
- delimiter recovery
- indentation/context recovery nếu sau này cần
- statement boundary recovery

Synchronization points có thể gồm:

```text
}
;
fn
struct
enum
trait
impl
let
return
```

tùy grammar context.

---

# 5. Không sửa source ngầm

Parser có thể **giả định token thiếu để tiếp tục phân tích**, nhưng không được tự động sửa source.

Ví dụ:

```axiom
foo(
bar()
```

Parser nội bộ có thể hiểu:

```text
foo(
    bar()
)
```

để tiếp tục.

Nhưng source thật vẫn giữ nguyên.

Diagnostic:

```text
expected ')'
```

---

# 6. Diagnostic Causal Graph

Đây là một cải tiến quan trọng.

Thay vì 100 lỗi độc lập:

```text
Error A
Error B
Error C
...
```

compiler xây:

```text
Root Error
   │
   ├── derived error
   ├── derived error
   └── derived error
```

Ví dụ:

```text
AEXPR-101
expected expression
    │
    ├── type unavailable
    ├── trait unavailable
    └── return type unavailable
```

IDE có thể hiển thị chủ yếu:

> **Root cause**

thay vì spam.

---

# 7. Diagnostic Dependency

Mỗi diagnostic có thể có:

```text
caused_by
depends_on
suppressed_by
related_to
```

Ví dụ:

```text
Type inference failed
      ↓
Trait resolution failed
      ↓
Method resolution failed
```

Chỉ lỗi đầu tiên nên được coi là root cause.

---

# 8. Diagnostic Deduplication

Nếu 20 compiler subsystem cùng phát hiện:

```text
TypeId = Error
```

không được xuất 20 lỗi giống nhau.

Compiler có:

```text
DiagnosticFingerprint
```

dựa trên:

```text
code
semantic entity
source span
cause
```

để loại bỏ duplicate.

---

# 9. ErrorType

Type system cần một type đặc biệt:

```text
ErrorType
```

với tính chất:

```text
ErrorType ≠ Any
ErrorType ≠ dynamic
ErrorType ≠ Object
```

Nó chỉ có mục đích:

> cho phép semantic analysis tiếp tục.

Ví dụ:

```axiom
let x: ???
let y = x + 1
```

`x` có `ErrorType`.

Compiler không nên tiếp tục báo:

```text
cannot add ErrorType and i32
cannot infer operator
cannot infer return type
...
```

mà nên quy về lỗi gốc:

```text
unknown type
```

---

# 10. Unknown ≠ Error

Nên phân biệt:

```text
Unknown
Error
Known
```

### Unknown

Compiler chưa đủ thông tin.

Ví dụ:

```text
generic type chưa resolve
```

### Error

Compiler đã biết có semantic violation.

Ví dụ:

```text
i32 + String
```

### Known

Thông tin đã xác định.

Điều này giúp incremental analysis chính xác hơn.

---

# 11. Partial Type Inference

Ví dụ người dùng đang gõ:

```axiom
let x = foo(
```

Compiler biết:

```text
callee = foo
```

và có thể lấy signature:

```text
foo(a: Buffer, b: usize) -> Result<...>
```

Do đó completion vẫn có thể đề xuất:

```text
Buffer
usize
```

dù expression chưa hoàn chỉnh.

---

# 12. Partial Trait Resolution

Nếu:

```axiom
x.foo(
```

compiler có thể biết:

```text
Type(x) = MyType
```

và tìm:

```text
inherent methods
trait methods
extensions
```

Nếu một generic argument còn thiếu:

```text
T = Unknown
```

thì trait solver có thể trả:

```text
Ambiguous / Incomplete
```

thay vì:

```text
Trait not implemented
```

---

# 13. Partial Ownership Analysis

Ownership verifier không được biến:

```text
unknown
```

thành:

```text
valid
```

Ví dụ:

```axiom
let x = foo()
bar(x)
x.
```

nếu `bar` chưa resolve được:

```text
ownership after bar = Unknown
```

IDE vẫn có thể tiếp tục.

Nhưng:

```text
build
```

phải yêu cầu:

```text
ownership = proven
```

---

# 14. Partial Capability Analysis

Tương tự:

```text
CapabilityState =
    Proven
    Conflict
    Unknown
    Incomplete
```

Chỉ:

```text
Proven
```

mới đủ điều kiện cho safe compilation.

Không bao giờ:

```text
Unknown → assume no conflict
```

Điều này bảo toàn nguyên tắc `UNKNOWN` không được coi là `NO_ALIAS`.

---

# 15. Completion Engine

Completion phải tận dụng partial semantics:

```text
Source
 ↓
Recovery Parser
 ↓
Partial HIR
 ↓
Partial Type
 ↓
Partial Trait
 ↓
Completion
```

Ví dụ:

```axiom
user.
```

dù file còn 20 lỗi khác, compiler vẫn biết:

```text
user : User
```

và đưa ra member phù hợp.

---

# 16. Completion phải tôn trọng visibility

Không vì đang ở partial mode mà completion hiển thị:

```text
private internal symbol
```

ở nơi không hợp lệ.

Partial analysis cho phép:

```text
unknown
```

nhưng không được phá:

```text
module visibility
privacy
package boundary
```

---

# 17. AI Repair

AI có thể nhận structured diagnostic:

```text
{
  code: "ATYPE-204",
  root_cause: true,
  span: ...,
  expected: "Buffer",
  actual: "String"
}
```

và đề xuất:

```text
change parameter type
convert String → Buffer
change call site
```

Nhưng sau khi AI sửa:

```text
Source
 ↓
Compiler
 ↓
Verification
```

mới xác nhận fix.

---

# 18. Compiler không tự đoán semantic intent

Ví dụ:

```axiom
foo(x)
```

Compiler thấy:

```text
foo(Buffer)
foo(String)
foo(Bytes)
```

Không được tự chọn một overload chỉ vì:

```text
"có vẻ hợp lý"
```

Partial mode có thể trả:

```text
Ambiguous
```

và IDE hiển thị tất cả candidate phù hợp.

---

# 19. Expected Type Context

Một lợi thế của Axiom compiler là completion có thể dùng context.

Ví dụ:

```axiom
let x: Vec<i32> = [
```

compiler biết expected type:

```text
Vec<i32>
```

nên có thể hướng dẫn completion/generation theo context.

Điều này đặc biệt hữu ích cho AI.

---

# 20. Error Recovery không ảnh hưởng Production Semantics

Đây là invariant rất quan trọng.

```text
Partial Semantic Mode
```

chỉ tồn tại để:

```text
analyze
suggest
navigate
recover
```

Không được:

```text
partial proof → executable code
```

Pipeline production vẫn là:

```text
Source
 ↓
Complete Parse
 ↓
Complete Semantic Analysis
 ↓
Verified MIR
 ↓
Codegen
```

---

# 21. Incremental Error Recovery

Khi user sửa:

```text
foo(
```

thành:

```text
foo(x)
```

compiler không nên rebuild toàn bộ semantic graph.

Chỉ invalidation các node phụ thuộc:

```text
CallExpr
 ↓
Type inference
 ↓
Trait resolution
 ↓
dependent diagnostics
```

Root diagnostics không liên quan giữ nguyên.

---

# 22. Diagnostic Stability

Khi user sửa một lỗi:

```text
Root A
```

các lỗi phụ thuộc vào A phải tự động biến mất.

Không được tạo:

```text
Root A fixed
→ 50 new random errors
```

nếu semantic graph chưa thay đổi tương ứng.

---

# 23. Error Recovery trong Generic Code

Ví dụ:

```axiom
fn foo<T: (
```

Compiler phải biết:

```text
GenericParameter T
TraitBound incomplete
```

thay vì bỏ cả function khỏi semantic database.

IDE vẫn có thể:

- navigate tới `T`
- rename `T`
- show docs
- completion trait
- show generic parameter information.

---

# 24. Error Recovery trong Match

Ví dụ:

```axiom
match x {
    Some(v) =>
```

Parser tạo:

```text
MatchArm
├── pattern = Some(v)
├── body = MissingExpression
```

Exhaustiveness analyzer không nên kết luận:

```text
missing None
```

như một lỗi độc lập nếu nguyên nhân thực tế là body chưa hoàn chỉnh.

---

# 25. Error Recovery trong Struct

Ví dụ:

```axiom
struct User {
    name: String,
    age:
}
```

Compiler biết:

```text
field name = String
field age = incomplete type
```

IDE vẫn có thể:

```text
find User
find name
find references
```

---

# 26. Error Recovery trong Trait/Impl

Ví dụ:

```axiom
impl Display for User {
    fn format(
```

Compiler vẫn đăng ký:

```text
Impl(User, Display)
```

nếu declaration identity đủ rõ.

Điều này rất quan trọng cho navigation và completion.

---

# 27. Semantic Tombstones

Khi declaration bị xóa:

```text
fn foo()
```

các reference cũ có thể tạm thời trở thành:

```text
MissingDeclaration
```

thay vì làm toàn bộ graph sụp đổ.

Compiler giữ semantic tombstone trong revision hiện tại để:

- diagnostics
- rename
- code actions
- incremental update

hoạt động ổn định.

---

# 28. Partial Program Database

CompilerDB có thể chứa:

```text
Known
Unknown
Error
Incomplete
Stale
```

nhưng mỗi query phải khai báo mức certainty.

Ví dụ:

```text
TypeQueryResult {
    type
    certainty
}
```

với:

```text
PROVEN
INFERRED
PARTIAL
UNKNOWN
ERROR
```

AI không được nhầm:

```text
INFERRED
```

với:

```text
PROVEN
```

---

# 29. AI Context phải biết Certainty

Đây là điểm rất đáng đóng băng.

Ví dụ AI hỏi:

```text
type_of(x)
```

Compiler trả:

```text
type = Foo
certainty = PROVEN
```

hoặc:

```text
type = Foo<T>
certainty = PARTIAL
```

AI sẽ biết:

> Đây là thông tin chưa hoàn chỉnh.

Điều này giảm hallucination đáng kể.

---

# 30. Error Budget

Một file có thể có hàng trăm lỗi cascade.

Compiler nên có:

```text
diagnostic budget
```

nhưng không đơn giản là:

```text
chỉ hiển thị 20 lỗi đầu
```

Mà ưu tiên:

```text
root causes
high-confidence diagnostics
independent errors
```

và giảm:

```text
derived diagnostics
```

---

# 31. Diagnostic Priority

Có thể xếp loại:

```text
ROOT
BLOCKING
DEPENDENT
INFORMATIONAL
STYLE
```

Ví dụ:

```text
missing type
```

là:

```text
ROOT
```

còn:

```text
cannot infer return expression
```

có thể là:

```text
DEPENDENT
```

IDE mặc định ưu tiên ROOT.

---

# 32. Compiler Error Recovery không làm yếu Safety

Một nguyên tắc phải được nhấn mạnh:

```text
Partial compiler
      ↓
more tolerant
```

không có nghĩa:

```text
Production verifier
      ↓
less strict
```

Ngược lại:

```text
Partial mode
    → tolerate uncertainty

Production mode
    → reject uncertainty
```

---

# 33. Formal Model

Partial semantic state có thể mô hình hóa:

```text
SemanticState =
    Proven(v)
    Unknown
    Incomplete
    Error(e)
```

với một lattice thích hợp cho từng subsystem.

Ví dụ:

```text
          Unknown
         /       \
   Incomplete    Error
         \       /
          Proven
```

Nhưng không nên dùng một lattice duy nhất cho mọi analysis; ownership, type, capability và trait solver có semantics khác nhau.

Do đó mỗi subsystem có domain riêng và CompilerDB kết hợp chúng.

---

# 34. AI Agent Workflow mới

Với BOOTSTRAP-189 + 191:

```text
AI Agent
   ↓
ax query
   ↓
CompilerDB
   ↓
semantic facts
   ↓
edit source
   ↓
ax check
   ↓
structured diagnostics
   ↓
root-cause analysis
   ↓
edit
   ↓
ax test
```

Ngay cả khi source chưa compile được, agent vẫn có thể hỏi:

```text
what is known?
what is unresolved?
what is the root error?
which symbols are affected?
```

---

# 35. Human IDE Workflow

Người dùng:

```text
struct User {
```

IDE lập tức biết:

```text
declaration = User
body = incomplete
```

Người dùng tiếp:

```text
name:
```

IDE biết:

```text
field = name
type = incomplete
```

Người dùng gõ:

```text
String
```

thì semantic graph update cục bộ.

Không cần đợi toàn file hoàn chỉnh.

---

# 36. Production Boundary

Cuối cùng:

```text
                 ┌───────────────────┐
                 │ Partial Program   │
                 └─────────┬─────────┘
                           │
                     Recovery Parser
                           ↓
                    Partial Semantic
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
        IDE               AI             Diagnostics
          │                │                │
          └────────────────┼────────────────┘
                           ↓
                    User fixes source
                           ↓
                  Complete Semantics
                           ↓
                     Verified MIR
                           ↓
                       Codegen
```

**Không có đường tắt từ Partial Semantic tới executable.**

---

# Invariants mới — FROZEN

### `ADIAG-20`
Compiler phải phân biệt Complete Semantic Mode và Partial Semantic Mode.

### `ADIAG-21`
Partial semantic information không được coi là production proof.

### `ADIAG-22`
`ErrorType` chỉ phục vụ recovery/continued analysis và không tương đương `Any`.

### `ADIAG-23`
`Unknown`, `Incomplete`, `Error` và `Known/Proven` phải được phân biệt.

### `ADIAG-24`
Unknown information không được biến thành safe assumption.

### `ADIAG-25`
Parser recovery không được sửa source ngầm.

### `ADIAG-26`
Syntax recovery phải duy trì source fidelity/lossless representation.

### `ADIAG-27`
Diagnostics phải hỗ trợ causal relationships.

### `ADIAG-28`
Derived diagnostics nên được suppress/deduplicate khi root cause đã đủ giải thích.

### `ADIAG-29`
Diagnostic identity phải ổn định trong cùng semantic context.

### `ADIAG-30`
Completion và IDE queries được phép hoạt động trên partial programs.

### `ADIAG-31`
Partial analysis phải tôn trọng visibility, ownership, capability và type rules.

### `ADIAG-32`
Ambiguous semantic resolution không được tự động chọn candidate chỉ vì heuristic.

### `ADIAG-33`
AI phải nhận được certainty/provenance của semantic facts khi sử dụng compiler queries.

### `ADIAG-34`
Automated AI repair phải được complete semantic verification sau khi sửa source.

### `ADIAG-35`
Partial ownership/capability analysis không được cấp quyền code generation.

### `ADIAG-36`
Incremental recovery phải invalidate theo dependency graph.

### `ADIAG-37`
Fixing a root diagnostic phải tự động invalidate các diagnostics phụ thuộc vào nó.

### `ADIAG-38`
Compiler diagnostics phải ưu tiên root causes hơn cascade errors.

### `ADIAG-39`
Diagnostic budget không được làm mất các independent root errors chỉ vì chúng xuất hiện sau.

### `ADIAG-40`
Deleted semantic entities có thể được biểu diễn bằng tombstone trong revision hiện tại.

### `ADIAG-41`
Partial trait/type/generic declarations phải được giữ trong semantic database khi identity đủ xác định.

### `ADIAG-42`
Partial semantic mode không được làm yếu production verifier.

### `ADIAG-43`
Production compilation chỉ được bắt đầu khi tất cả required semantic proofs đạt trạng thái Proven.

### `ADIAG-44`
Mỗi semantic query phải có thể biểu diễn mức độ certainty của kết quả khi cần.

### `ADIAG-45`
Reference/MIR/production semantics vẫn là authority; error recovery chỉ là tooling mechanism.

---

# Trạng thái

**BOOTSTRAP-191 — FROZEN / COMPLETED**

Axiom hiện đã có một điểm khá đặc biệt: **compiler không chỉ là chương trình chuyển source thành machine code, mà là semantic database có thể được IDE, debugger, refactoring và AI truy vấn trong khi source vẫn chưa hoàn chỉnh.**

Chuỗi tiếp theo nên chuyển sang một vấn đề ở cấp **language ecosystem/runtime architecture**:

# BOOTSTRAP-192 — Interoperability, C ABI, C++, Objective-C, Swift, WASM Component Model & Foreign Language Boundaries

Mục tiêu là làm rõ **Axiom có thể sống cùng thế giới hiện tại như thế nào**, thay vì đợi toàn bộ hệ sinh thái chuyển sang Axiom.

Sẽ thiết kế thống nhất:

```text
Axiom
 ├── C ABI
 ├── C++
 ├── Objective-C
 ├── Swift
 ├── Rust
 ├── JVM/CLR boundary nếu cần
 ├── WASM
 ├── system calls
 ├── dynamic libraries
 ├── callbacks
 ├── foreign ownership
 ├── foreign exceptions/panics
 ├── foreign threads
 └── foreign memory
```

Đặc biệt sẽ giải quyết vấn đề rất khó của Axiom:

> **Làm sao giữ mô hình ownership/capability đơn giản của Axiom khi giao tiếp với API C/C++ vốn không có những guarantees đó, mà không biến mọi FFI call thành một đống `unsafe` khó dùng?**