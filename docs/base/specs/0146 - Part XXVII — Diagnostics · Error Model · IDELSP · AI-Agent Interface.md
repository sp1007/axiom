# Part XXVII — Diagnostics · Error Model · IDE/LSP · AI-Agent Interface

Đây là phần rất đáng đầu tư cho Axiom, vì mục tiêu của chúng ta không chỉ là **compiler nhanh**, mà còn là:

> **Compiler phải dễ hiểu đối với con người và dễ sửa đối với AI agent.**

Một compiler hiện đại không nên coi:

```text
error: something went wrong
```

là output chính.

Axiom sẽ coi **diagnostic là một structured semantic object**, còn text/terminal/LSP/AI đều chỉ là các cách render object đó.

---

# XXVII.1. Diagnostic Không Phải String

Không thiết kế:

```text
Diagnostic = String
```

mà:

```text
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans
    notes
    help
    suggestions
    related_diagnostics
    semantic_context
}
```

Sau đó renderer mới quyết định hiển thị thế nào.

---

# XXVII.2. Diagnostic Pipeline

```text
Compiler
   │
   ▼
Diagnostic Object
   │
   ├── CLI renderer
   ├── JSON renderer
   ├── LSP adapter
   ├── IDE renderer
   └── AI-agent renderer
```

Một lỗi chỉ cần được tạo **một lần**.

---

# XXVII.3. Severity

Axiom v0.1:

```text
error
warning
info
hint
```

Không có hàng chục mức severity.

---

# XXVII.4. Error Code Là Stable Identity

Ví dụ:

```text
AX_TYPE_0001
AX_MOVE_0001
AX_VIEW_0001
AX_DROP_0001
AX_TRAIT_0001
AX_ASYNC_0001
AX_CONC_0001
AX_ABI_0001
AX_RUNTIME_0001
```

Code là identity của diagnostic class.

---

# XXVII.5. Code Không Được Chứa Line Number

Không:

```text
AX_TYPE_42
```

nếu `42` là line.

Line/column là location.

Code phải ổn định qua source restructuring.

---

# XXVII.6. Diagnostic ID và Error Code

Nên phân biệt:

```text
ErrorCode
DiagnosticInstanceId
```

Ví dụ:

```text
code = AX_MOVE_0003
instance = D-91A4
```

`instance` dùng để liên kết diagnostics trong một compilation.

---

# XXVII.7. Primary Span

Một diagnostic phải có:

```text
primary_span
```

là vị trí chính gây lỗi.

Ví dụ:

```axiom
consume(x)
use(x)
```

`use(x)` là primary span.

---

# XXVII.8. Secondary Span

Compiler có thể chỉ ra nguyên nhân:

```text
AX_MOVE_0003:
value used after move
```

Primary:

```text
use(x)
```

Secondary:

```text
consume(x)
```

với label:

```text
value was moved here
```

---

# XXVII.9. Tốt Hơn Error Message Một Dòng

CLI:

```text
error[AX_MOVE_0003]: use of moved value `x`

  --> main.ax:12:5
   |
10 | let x = Buffer.new()
11 | consume(x)
   |         - value moved here
12 | print(x)
   |       ^ value used after move
   |
help: pass a view instead of transferring ownership
```

Nhưng đây chỉ là **renderer**.

Diagnostic object vẫn giữ dữ liệu cấu trúc.

---

# XXVII.10. Diagnostic Suggestion

Suggestion phải có:

```text
replacement
range
confidence/category
```

Ví dụ:

```text
Suggestion {
    range: ...
    replacement: "view(x)"
}
```

Không phải:

```text
help: maybe change this
```

---

# XXVII.11. Machine-Appplicable Fix

Phân biệt:

```text
help
```

và:

```text
machine_fix
```

Ví dụ:

```text
AX_IMPORT_0002

help:
  import `math.vector`

machine_fix:
  add `import math.vector { Vec2 }`
```

AI/IDE có thể áp dụng trực tiếp.

---

# XXVII.12. Không Được Đề Xuất Fix Nếu Không Chắc

Compiler không nên đưa:

```text
suggestion:
  remove this line
```

nếu semantics không chắc chắn.

Rule:

> **Machine-applicable suggestion must preserve semantics according to compiler's known proof.**

Nếu chỉ là heuristic:

```text
category = advisory
```

không gắn `machine_fix`.

---

# XXVII.13. Diagnostic Context

Một diagnostic có thể có:

```text
semantic_context {
    symbol
    type
    expected_type
    actual_type
    ownership_state
    capability
    trait_requirement
}
```

Ví dụ:

```json
{
  "code": "AX_TYPE_0004",
  "expected": "i32",
  "found": "Text"
}
```

---

# XXVII.14. Nhưng Không Dump Compiler Internals Mặc Định

Không hiển thị:

```text
TypeId(1847)
HIRNode(9912)
RegionVariable(R17)
```

cho người dùng.

Những thông tin này chỉ trong:

```text
--debug
--explain
--trace
```

---

# XXVII.15. `axiom explain`

Một CLI rất hữu ích:

```text
axiom explain AX_MOVE_0003
```

Output:

```text
AX_MOVE_0003 — Use After Move

Meaning:
  An owning value was transferred and is no longer available
  at the point where it is used.

Common causes:
  ...
```

---

# XXVII.16. Diagnostic Documentation

Mỗi error code nên có:

```text
definition
why
examples
common fixes
exceptions
related rules
spec references
```

Ví dụ:

```text
AX_VIEW_0002
→ ACAP-...
→ AMEM-...
```

---

# XXVII.17. Diagnostic ↔ Specification

Đây là một lợi thế lớn.

Diagnostic:

```text
AX_VIEW_0002
```

có thể liên kết:

```text
SPEC
ACAP-30
AMEM-65
```

Compiler developer có thể truy ngược:

```text
error
→ invariant
→ specification
→ test
```

---

# XXVII.18. Diagnostic ↔ Test

Mỗi error class phải có negative tests:

```text
AX_MOVE_0003
├── test_001
├── test_002
└── test_003
```

Do đó nếu compiler thay đổi error code/message:

```text
conformance test
```

có thể phát hiện.

---

# XXVII.19. Không Freeze Exact English Message

Không nên coi:

```text
"value used after move"
```

là API ổn định.

API ổn định là:

```text
AX_MOVE_0003
```

và structured fields.

Message có thể cải thiện.

---

# XXVII.20. Diagnostic Schema

Đề xuất:

```text
Diagnostic {
    id: DiagnosticId
    code: ErrorCode
    severity: Severity

    message: Text

    primary: Span
    secondary: [LabeledSpan]

    notes: [Text]
    helps: [Text]

    fixes: [Fix]

    related: [DiagnosticId]

    semantic: Optional<DiagnosticContext>
}
```

---

# XXVII.21. Span

Span không nên chỉ là:

```text
line
column
```

Mà:

```text
Span {
    file_id
    start_byte
    end_byte
}
```

Line/column được tính khi render.

Điều này hỗ trợ UTF-8 chính xác.

---

# XXVII.22. UTF-8

Axiom source là UTF-8.

Compiler internally dùng byte offsets:

```text
start_byte
end_byte
```

Renderer chuyển thành:

```text
line
column
```

---

# XXVII.23. Unicode Column

Phải phân biệt:

```text
byte offset
code point column
display column
```

Terminal có thể dùng display width.

LSP có encoding contract riêng.

Compiler không được nhầm chúng.

---

# XXVII.24. File Identity

Diagnostic dùng:

```text
FileId
```

không dùng path string làm identity nội bộ.

Path mapping xảy ra renderer layer.

---

# XXVII.25. Generated Source

Nếu lỗi xuất hiện trong generated source:

```text
generated.ax
```

compiler phải có source mapping:

```text
generated span
→ originating source span
```

Nếu có.

---

# XXVII.26. Comptime Diagnostics

Comptime có thể phát sinh lỗi:

```text
AX_COMPTIME_0001
```

nhưng nên liên kết:

```text
source call
+
comptime execution site
```

Ví dụ:

```text
error[AX_COMPTIME_0001]: compile-time file access denied

  --> schema.ax:20:14
   |
20 | comptime load_schema("schema.json")
   |              ^^^^^^^^^^^^^^^^^^^^^^
   |
note: filesystem access is not enabled for this compilation
help: declare the required compile-time capability
```

---

# XXVII.27. Build Diagnostics

Build errors cũng phải structured:

```text
AX_BUILD_0001
AX_DEP_0001
AX_CACHE_0001
AX_TARGET_0001
AX_ABI_0001
```

Không trộn chúng với type errors.

---

# XXVII.28. Runtime Diagnostics

Runtime/panic có thể sử dụng cùng model:

```text
AX_PANIC_...
AX_RUNTIME_...
```

nhưng phải phân biệt:

```text
compile-time diagnostic
runtime diagnostic
```

---

# XXVII.29. Panic Report

Ví dụ:

```text
panic[AX_PANIC_0002]: index out of bounds

thread: main
at: src/main.ax:42:17

index: 10
length: 4
```

Debug build có thể thêm stack trace.

Release có thể có:

```text
minimal panic
```

---

# XXVII.30. Panic Không Cần Heap

Đã chốt.

Compiler/runtime không nên bắt panic machinery phải allocate.

Ví dụ:

```text
static message
stack formatting
direct stderr/write
```

tùy profile.

---

# XXVII.31. LSP

Axiom nên cung cấp native language server:

```text
axiom-lsp
```

nhưng LSP adapter không chứa compiler semantics riêng.

```text
LSP
 ↓
Compiler frontend APIs
```

---

# XXVII.32. LSP Features

MVP:

```text
diagnostics
hover
go to definition
go to declaration
find references
rename
completion
signature help
formatting
```

Sau:

```text
semantic tokens
code actions
inlay hints
type hierarchy-like trait info
```

---

# XXVII.33. Hover

Hover:

```axiom
Vec2
```

có thể:

```text
struct Vec2 {
    x: f32
    y: f32
}
```

và:

```text
module: math.vector
visibility: pub
```

Không cần runtime reflection.

---

# XXVII.34. Ownership Hover

Đây là feature rất đáng giá cho Axiom.

Ví dụ:

```text
x: Buffer
ownership: owned
```

Một view:

```text
v: view<u8>
capability:
  owner: x
  access: read
  region: x[0..128]
```

Chỉ hiện khi người dùng bật semantic hints.

---

# XXVII.35. Type Hover

Ví dụ:

```text
foo(x)
```

IDE:

```text
x
type: Buffer
state: moved
```

rất hữu ích khi debug ownership.

---

# XXVII.36. Trait Resolution Hover

Hover:

```text
x.display()
```

có thể:

```text
resolved method:
    Display.display
impl:
    Display for User
dispatch:
    static
```

Hoặc:

```text
dispatch:
    dynamic
```

nếu `dyn Trait`.

---

# XXVII.37. `dyn Trait` Diagnostic

Nếu:

```axiom
let x: dyn Trait = ...
```

không object-safe:

```text
AX_TRAIT_0012
trait cannot be used as dyn Trait
```

secondary diagnostics chỉ ra method/associated item gây vấn đề.

---

# XXVII.38. AI-Agent Output

Đây là phần đặc biệt quan trọng.

CLI:

```text
axiom check --format=json
```

không được chỉ serialize terminal text.

Nó serialize:

```json
{
  "diagnostics": [
    {
      "code": "AX_MOVE_0003",
      "severity": "error",
      "primary": {...},
      "secondary": [...],
      "fixes": [...]
    }
  ]
}
```

---

# XXVII.39. AI Không Cần Parse Human Text

AI agent không phải đọc:

```text
error: ...
--> ...
help: ...
```

rồi đoán.

Nó nhận:

```text
code
span
semantic_context
fixes
related
```

---

# XXVII.40. Diagnostic Fingerprint

Một diagnostic có:

```text
fingerprint
```

dựa trên:

```text
code
primary semantic location
relevant symbol identity
```

không dựa trên message.

Điều này giúp agent biết:

```text
same error
```

sau mỗi compilation iteration.

---

# XXVII.41. AI Fix Loop

Ví dụ:

```text
Agent
 ↓
edit source
 ↓
axiom check --format=json
 ↓
AX_MOVE_0003
 ↓
read semantic_context
 ↓
apply fix
 ↓
check
```

Không cần prompt AI:

> “hãy đọc terminal và tự suy nghĩ xem lỗi gì”.

---

# XXVII.42. Fix Confidence

Có thể chia:

```text
safe
suggested
speculative
```

Chỉ:

```text
safe
```

được phép IDE/agent auto-apply mặc định.

---

# XXVII.43. Code Action

LSP:

```text
CodeAction {
    title
    kind
    edits
    diagnostic_ids
}
```

Ví dụ:

```text
"Borrow value as read-only view"
```

→ edit:

```text
consume(x)
```

thành:

```text
consume(view(x))
```

**chỉ khi compiler chứng minh API signature phù hợp.**

---

# XXVII.44. AI Agent Must Not Modify Semantics Silently

Compiler có thể nói:

```text
suggested:
clone x
```

nhưng agent không nên tự động áp dụng nếu:

```text
Clone
```

có thể tốn chi phí lớn hoặc thay đổi semantics/performance.

Vì vậy:

```text
machine_fix
```

chỉ áp dụng khi semantics-preserving theo đúng contract.

Còn:

```text
clone
change ownership
change API
```

là `advisory`.

---

# XXVII.45. Explain Mode

Một tính năng rất hữu ích:

```text
axiom explain AX_VIEW_0007
```

và:

```text
axiom explain --at src/main.ax:42
```

Compiler có thể giải thích:

```text
owner
capabilities
conflicts
lifetime
```

theo semantic graph.

---

# XXVII.46. Ownership Graph

Compiler debug output:

```text
axiom inspect --ownership src/main.ax
```

Ví dụ:

```text
x
├── owner
├── view v1 [READ, 0..100]
└── view v2 [READ, 50..80]
```

Nếu:

```text
mut_view m1 [WRITE, 20..60]
```

thì:

```text
CONFLICT:
m1 overlaps v1
m1 overlaps v2
```

---

# XXVII.47. Capability Graph

Đây có thể trở thành một trong những công cụ nổi bật của Axiom:

```text
axiom inspect --capabilities file.ax
```

Output:

```text
Owner: buffer
  ├── READ  [0..128]
  ├── READ  [128..256]
  └── WRITE [256..512]
```

Compiler đã có region model nên việc này tự nhiên.

---

# XXVII.48. Trait Graph

```text
axiom inspect --traits User
```

có thể:

```text
User
├── Display
├── Send
├── Share
└── Clone
```

và:

```text
Display
└── implemented by User
```

---

# XXVII.49. MIR Diagnostics

Developer mode:

```text
axiom inspect --mir
axiom inspect --verified-mir
```

Đặc biệt:

```text
axiom inspect --verified-mir
```

phải cho thấy:

```text
ownership state
capability facts
drop points
```

nếu yêu cầu.

---

# XXVII.50. Compiler Internal Errors

Không được trộn:

```text
user error
```

với:

```text
compiler bug
```

Ví dụ:

```text
AX_MOVE_0003
```

là user program invalid.

Trong khi:

```text
AXC_INTERNAL_0001
```

là compiler internal failure.

---

# XXVII.51. ICE — Internal Compiler Error

Nếu compiler gặp invariant violation:

```text
internal compiler error
```

phải tự động tạo artifact:

```text
source hash
compiler version
target
profile
stage
stack
MIR if available
diagnostics
```

---

# XXVII.52. Privacy

Compiler không được mặc định upload source code.

Crash artifact local:

```text
.axiom/crash/
```

Nếu user muốn submit thì explicit.

---

# XXVII.53. Compiler Panic vs User Panic

Phân biệt rõ:

```text
AX_PANIC_...
```

program panic.

và:

```text
AXC_INTERNAL_...
```

compiler bug.

Đây là hai domain hoàn toàn khác.

---

# XXVII.54. Error Namespace

Tôi đề xuất namespace chuẩn:

```text
AX_LEX_
AX_PARSE_
AX_NAME_
AX_TYPE_
AX_TRAIT_
AX_GENERIC_
AX_MOVE_
AX_COPY_
AX_VIEW_
AX_DROP_
AX_MATCH_
AX_CONST_
AX_COMPTIME_
AX_ASYNC_
AX_CONC_
AX_ATOM_
AX_UNSAFE_
AX_FFI_
AX_ABI_
AX_GPU_
AX_MODULE_
AX_PACKAGE_
AX_BUILD_
AX_RUNTIME_
AX_PANIC_
AX_LINK_
AX_TARGET_
```

Compiler internal:

```text
AXC_INTERNAL_
```

---

# XXVII.55. Diagnostic Categories Không Phải Semantic Rules

Một rule:

```text
AOWN-30
```

có thể produce:

```text
AX_COPY_0002
AX_DROP_0001
```

Diagnostic category phục vụ UX.

Invariant phục vụ language correctness.

---

# XXVII.56. Localization

Không nên đưa localization vào compiler semantic layer.

Compiler tạo:

```text
code
structured data
```

renderer mới dịch message.

Do đó tương lai:

```text
English
Vietnamese
Chinese
Japanese
```

không ảnh hưởng compiler.

---

# XXVII.57. Stable JSON Schema

`--format=json` cần version:

```text
diagnostic_schema_version
```

Ví dụ:

```text
"schema": 1
```

Có thể evolve mà không phá agent tooling.

---

# XXVII.58. JSON Không Được Là AST Dump

AI không cần:

```text
entire AST
entire compiler state
```

mặc định.

Output phải:

```text
small
precise
actionable
```

Có option:

```text
--verbose-json
```

cho compiler developers.

---

# XXVII.59. AI-Oriented Semantic Query

Ngoài diagnostics, có thể hỗ trợ:

```text
axiom query
```

Ví dụ:

```text
axiom query --symbol foo --json
```

trả:

```json
{
  "kind": "function",
  "type": "(view<Buffer>) -> Result<i32, Error>",
  "effects": ["read"],
  "dispatch": "static"
}
```

---

# XXVII.60. AI-Oriented Type Query

```text
axiom query --type User
```

có thể trả:

```text
size
alignment
copy
drop
send
share
repr
abi
fields
methods
traits
```

---

# XXVII.61. AI-Oriented Ownership Query

```text
axiom query --ownership x --at 42
```

trả:

```text
state: OWNED
capabilities:
  - READ
dependencies:
  none
```

Đây sẽ cực kỳ hữu ích khi AI agent sửa compiler hoặc sửa Axiom application.

---

# XXVII.62. Compiler as a Tool API

Cuối cùng, compiler không chỉ là:

```text
axiom source.ax
```

mà có thể có API:

```text
check()
parse()
resolve()
typecheck()
lower_mir()
verify()
optimize()
emit()
query()
explain()
```

AI harness có thể gọi từng stage.

---

# XXVII.63. Không Cho AI Agent Chạm Semantic Core Tùy Ý

Agent có thể:

```text
query
inspect
run tests
apply fixes
```

nhưng semantic rules vẫn phải đến từ:

```text
SPEC
```

không phải từ prompt của agent.

Nguyên tắc:

> **AI can implement semantics; AI cannot define semantics implicitly.**

Nếu agent muốn thay semantics:

```text
SPEC change
→ invariant change
→ tests change
→ compiler change
```

---

# XXVII.64. Diagnostics và Harness

Khi agent sửa compiler:

```text
Agent
 │
 ├── read SPEC
 ├── inspect diagnostics
 ├── inspect MIR
 ├── run Oracle
 ├── run regression
 └── run differential
```

Không cần agent “nhớ” toàn bộ compiler architecture.

---

# XXVII.65. Bộ Invariant Part XXVII

### Diagnostic model

**ADIAG-20 — Diagnostics Are Structured Semantic Objects**

**ADIAG-21 — Diagnostic Codes Are Stable Semantic Categories**

**ADIAG-22 — Human Messages Are Renderings Of Diagnostics**

**ADIAG-23 — Diagnostics Have Precise Source Spans**

**ADIAG-24 — Primary And Secondary Locations Are Distinct**

**ADIAG-25 — Machine Fixes Are Explicitly Represented**

**ADIAG-26 — Unsafe Suggestions Must Not Be Presented As Safe Fixes**

**ADIAG-27 — Diagnostic Identity Does Not Depend On Human Message Text**

### Source / Unicode

**ADIAG-28 — Internal Locations Use Stable File And Byte Spans**

**ADIAG-29 — Display Columns Are Distinct From Byte Offsets**

**ADIAG-30 — UTF-8 Source Is Handled Without Ambiguous Character Positions**

### Specification

**ADIAG-31 — Diagnostics Can Reference Normative Specification Rules**

**ADIAG-32 — Diagnostic Classes Have Negative Conformance Tests**

**ADIAG-33 — Compiler Error Codes Are Independent Of Source Line Numbers**

### IDE

**ADIAG-34 — LSP Diagnostics Are Derived From Compiler Diagnostics**

**ADIAG-35 — LSP Does Not Implement Independent Language Semantics**

**ADIAG-36 — Semantic Queries Use Compiler Semantic State**

**ADIAG-37 — Ownership And Capability State May Be Exposed As Debug Information**

### AI

**ADIAG-38 — Machine-Readable Diagnostics Are First-Class**

**ADIAG-39 — JSON Diagnostics Have A Versioned Schema**

**ADIAG-40 — AI Agents Need Not Parse Human-Oriented Error Messages**

**ADIAG-41 — Machine Fixes Must Be Semantically Justified**

**ADIAG-42 — Advisory Suggestions Are Distinct From Safe Machine Fixes**

**ADIAG-43 — Semantic Queries Are Available In Machine-Readable Form**

**ADIAG-44 — AI Agents Cannot Implicitly Redefine Language Semantics**

### Compiler failures

**ADIAG-45 — Compiler Internal Failures Are Distinct From User Program Errors**

**ADIAG-46 — Internal Compiler Failures Preserve Reproduction Context**

**ADIAG-47 — Compiler Crash Artifacts Do Not Imply Source Upload**

---

# XXVII.66. Kiến trúc cuối

Axiom bây giờ có ba lớp giao tiếp rất rõ:

```text
                    AXIOM COMPILER
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
           Human       IDE        AI Agent
              │          │          │
            Text        LSP       JSON/API
              │          │          │
              └──────────┼──────────┘
                         ▼
                 Diagnostic Object
```

Đây là kiến trúc tốt hơn rất nhiều so với việc xây compiler trước rồi sau đó “thêm LSP/AI support”.

---

# XXVII.67. Một nguyên tắc mới nên freeze

> **ADIAG-48 — One Semantic Diagnostic, Many Renderings.**

Một lỗi chỉ có một semantic identity.

Nó có thể được render thành:

```text
CLI
JSON
LSP
IDE popup
documentation
AI context
```

nhưng không tạo năm hệ thống error khác nhau.

---

# XXVII.68. Và một nguyên tắc lớn hơn

Từ Part XXV + XXVI + XXVII:

```text
SPEC
 ↓
INVARIANT
 ↓
SEMANTIC MODEL
 ↓
ORACLE
 ↓
COMPILER
 ↓
DIAGNOSTIC
 ↓
TEST
```

đây gần như trở thành **closed loop** của Axiom.

Nếu một feature mới xuất hiện, agent không được chỉ viết code compiler.

Nó phải đi theo:

```text
Feature
 ↓
Semantic rule
 ↓
Invariant
 ↓
Oracle behavior
 ↓
Positive test
 ↓
Negative test
 ↓
Diagnostic
 ↓
Compiler implementation
 ↓
Optimization test
 ↓
ABI test nếu cần
```

Đây là nền tảng rất phù hợp với mục tiêu **Axiom tự phát triển bằng AI agents nhưng vẫn kiểm soát được chất lượng compiler**.

---

## Tiếp theo — Part XXVIII

**Debugging · Tooling · Profiler · Sanitizer · Trace · Performance Introspection**

Phần này sẽ khóa cách Axiom cho phép nhìn xuyên từ:

```text
source
→ ownership
→ capability
→ MIR
→ optimization
→ ABI
→ machine code
→ CPU performance
```

nhưng **không biến những công cụ debug đó thành runtime overhead của release build**.