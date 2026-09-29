Tiếp tục. Phần SIMD đã được chốt trước đó, nên không lặp lại. Ta chuyển sang lớp còn thiếu rất quan trọng:

# Axiom — IDE, LSP, Refactoring & AI-native Tooling v0.1

Mục tiêu:

> **Compiler là nguồn sự thật duy nhất; IDE, LSP và AI agent chỉ là các client của compiler.**

Không xây một parser/type checker riêng cho IDE.

---

## 1. Kiến trúc tổng thể

```text
                    Axiom Compiler Core
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
       LSP              CLI Tools          AI Tools
        │                  │                  │
    VS Code/IDE       check/build/...    Agent/Claude/...
        │
    Editor UI
```

Compiler cung cấp semantic database:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
```

IDE không tự suy luận lại các bước này.

---

# 2. LSP là lớp giao tiếp

Axiom nên hỗ trợ:

```text
Language Server Protocol
```

với:

```text
axiom lsp
```

IDE gửi:

```text
text/document position
```

Axiom trả:

```text
type
definition
references
completion
diagnostics
hover
rename
semantic tokens
code actions
```

---

# 3. Incremental semantic database

Đây là điểm cực kỳ quan trọng.

Không được:

```text
mỗi lần gõ một ký tự
→ compile toàn project
```

Thay vào đó:

```text
File changed
    ↓
syntax dependency
    ↓
semantic dependency
    ↓
invalidate affected nodes
    ↓
recompute only necessary facts
```

Có thể tận dụng chính:

```text
Semantic Interface Fingerprint
```

đã thiết kế cho build system.

---

# 4. Query-based compiler

Compiler frontend nên có dạng khái niệm:

```text
query(file)
query(module)
query(item)
query(type)
query(trait_impl)
query(symbol)
query(reference)
query(layout)
```

Mỗi query có dependency.

Ví dụ:

```text
type_of(expr42)
```

phụ thuộc:

```text
resolve(expr42)
type_of(name)
generic_context
```

---

# 5. Không tạo “IDE semantic engine”

Sai kiến trúc:

```text
Compiler parser
Compiler type checker

IDE parser
IDE type checker
IDE resolver
```

Đây là hai nguồn sự thật và cuối cùng sẽ lệch nhau.

Đúng:

```text
Axiom compiler semantic engine
            ↑
        LSP server
```

---

# 6. Completion

Khi gõ:

```axiom
foo.
```

LSP hỏi compiler:

```text
receiver type = Foo
```

compiler trả:

```text
methods
fields
trait methods
extension functions
```

theo đúng method-resolution rules đã chốt:

```text
inherent
→ trait impl
→ imported extension
→ generic extension
```

---

# 7. Completion phải semantic

Không chỉ autocomplete text.

Ví dụ:

```axiom
let x: Vec<i32> = ...
x.
```

IDE có thể biết:

```text
push
pop
len
capacity
reserve
...
```

và loại bỏ những thứ không callable trên `Vec<i32>`.

---

# 8. Method ambiguity

Nếu:

```axiom
foo.bar()
```

có hai extension:

```text
A::bar(Foo)
B::bar(Foo)
```

compiler đã định nghĩa:

```text
AX_METHOD_0001
```

IDE dùng chính diagnostic đó.

Không tự đưa ra luật khác.

---

# 9. Go to Definition

```text
Cmd/Ctrl + click
```

compiler trả:

```text
Definition {
    file
    span
    symbol_id
}
```

Không nên chỉ dựa vào tên.

---

# 10. Symbol ID

Mỗi declaration có semantic ID nội bộ:

```text
SymbolId
```

Ví dụ:

```text
package://foo@1.2.0/module/math::Vec::length
```

Nhưng ID nội bộ không nhất thiết chính là linker symbol.

Phân biệt:

```text
Source Identity
Semantic Identity
ABI Symbol Identity
```

---

# 11. Find References

Compiler có semantic graph:

```text
Symbol
 ↓
Reference set
```

Do đó:

```text
Find all references
```

không cần grep text.

---

# 12. Rename

Ví dụ đổi:

```text
Vec
```

thành:

```text
Vector
```

chỉ đổi đúng symbol.

Không đổi:

```text
"Vec"
```

trong string.

Không đổi:

```text
Vec
```

của package khác nếu không cùng semantic identity.

---

# 13. Rename generic/type parameters

Cũng hỗ trợ:

```axiom
fn max<T>(a: T, b: T)
```

rename:

```text
T → Item
```

mà không đụng tới `T` ngoài scope.

---

# 14. Refactoring

Axiom compiler đã có HIR nên có thể cung cấp semantic transformations:

```text
extract function
inline function
extract variable
rename
change signature
move item
organize imports
```

Nhưng phải phân biệt:

```text
machine-safe transformation
```

với:

```text
semantic suggestion
```

---

# 15. Code action

Compiler có thể trả:

```text
CodeAction {
    title
    edits
    applicability
}
```

Ví dụ:

```text
Convert to match
Add missing match arm
Import trait
Qualify ambiguous method
```

---

# 16. Exhaustive match IDE support

Vì compiler đã có pattern checker:

```text
match value {
}
```

IDE có thể yêu cầu:

```text
generate missing cases
```

Compiler trả chính xác các constructor còn thiếu.

Không cần IDE tự phân tích enum.

---

# 17. Import management

Compiler biết dependency graph.

IDE có thể:

```text
add import
remove unused import
sort imports
detect ambiguous imports
```

Không nên chỉ sort alphabetically; phải tôn trọng semantic grouping nếu Axiom sau này có quy ước.

---

# 18. Semantic highlighting

Không chỉ:

```text
keyword = blue
string = green
```

Axiom có thể highlight:

```text
type
trait
function
method
variable
constant
mutable variable
field
enum variant
module
generic parameter
macro/build entity
```

và đặc biệt:

```text
owned value
view
mut_view
```

nếu người dùng bật semantic ownership highlighting.

---

# 19. Ownership visualization

Đây có thể là một tính năng rất mạnh.

Ví dụ source:

```axiom
let buffer = Vec<i32>.new()
let v = view(buffer)
sum(v)
```

IDE có thể hiển thị semantic flow:

```text
buffer
  │
  └── READ capability
          │
          └── sum()
```

Không hiển thị lifetime syntax phức tạp.

---

# 20. Khi có move

```axiom
let file = File.open(path)?
consume(file)
file.read()
```

IDE:

```text
file
 │
 └── MOVE → consume()
               │
               └── file becomes MOVED
```

Điều này phù hợp triết lý:

> compiler làm việc phức tạp, programmer thấy mô hình đơn giản.

---

# 21. View conflict visualization

Ví dụ:

```axiom
let a = mut_view(x)
let b = mut_view(x)
```

IDE có thể chỉ rõ:

```text
a ───── WRITE ─────┐
                    ├── OVERLAP
b ───── WRITE ─────┘
```

và:

```text
a: field x.a
b: field x.b
```

thì:

```text
DISJOINT
```

---

# 22. Async visualization

Compiler biết state machine.

IDE có thể hiển thị:

```text
async fn download()
        │
        ├── State 0
        │
        ├── await socket.read()
        │
        ├── State 1
        │     └── buffer
        │
        └── State 2
```

Không cần programmer viết state machine.

---

# 23. “Why?” diagnostics

Đây là tính năng tôi rất muốn Axiom có.

Ví dụ:

```text
axiom explain AX_VIEW_0001
```

hoặc IDE:

> Why can't this view escape?

Compiler trả:

```text
view originates from:
    buffer

buffer lifetime ends:
    function foo()

view is returned from:
    foo()

therefore:
    returned capability would outlive its owner
```

Không cần đưa ra thuật ngữ borrow checker.

---

# 24. `axiom explain`

CLI:

```text
axiom explain <diagnostic-id>
```

Ví dụ:

```text
axiom explain AX_MOVE_0003
```

trả:

```text
Meaning
Why it happened
What semantic rule applies
Possible fixes
```

---

# 25. AI agent API

Đây là nơi Axiom có thể khác biệt mạnh.

Thay vì AI phải đọc text compiler:

```text
build failed
```

compiler có API structured:

```text
CompilationResult {
    diagnostics[]
    changed_symbols[]
    generated_artifacts[]
    semantic_facts[]
}
```

---

# 26. AI không được sửa semantics

AI agent:

```text
observe
→ reason
→ edit source
→ invoke compiler
→ inspect diagnostics
→ repeat
```

Compiler:

```text
judge
```

AI:

```text
assistant
```

Không để AI “quyết định” type/lifetime semantics.

---

# 27. Semantic query API

Có thể expose:

```text
axiom query symbol
axiom query type
axiom query references
axiom query layout
axiom query effects
axiom query ownership
```

Ví dụ:

```text
axiom query type src/foo.axiom:42:17
```

trả JSON:

```json
{
  "type": "Vec<i32>",
  "copy": false,
  "drop": true,
  "storage": "dynamic",
  "relocation": "may_relocate"
}
```

---

# 28. Compiler facts vs implementation details

Cần chia:

### Semantic facts

```text
Copy = false
Drop = true
Send = true
```

### Optimization facts

```text
inlined = true
vectorized = true
allocation_eliminated = true
```

### Target facts

```text
register = rax
section = .text
```

AI/IDE phải biết loại nào là ổn định.

---

# 29. Stable semantic API

Axiom nên cam kết:

```text
AX diagnostic codes
semantic query schema
LSP behavior
```

ổn định hơn:

```text
MIR internal node names
optimizer internals
machine IR
```

---

# 30. AI-friendly project map

Có thể có:

```text
axiom inspect --project
```

trả:

```text
packages
modules
public APIs
dependencies
traits
implementations
entry points
tests
benchmarks
unsafe boundaries
FFI boundaries
```

AI agent không cần đọc toàn bộ repository.

---

# 31. Unsafe map

Một tool rất hữu ích:

```text
axiom inspect --unsafe
```

hiển thị:

```text
unsafe blocks
unsafe functions
raw pointer operations
FFI calls
MMIO
reinterpretation
custom allocators
```

Ví dụ:

```text
src/gpu/memory.axiom:41
    unsafe pointer arithmetic

src/platform/win32.axiom:12
    extern "system"

src/image/jpeg.axiom:93
    FFI buffer conversion
```

---

# 32. Dependency map

```text
axiom inspect --deps
```

cho:

```text
app
 ├── image
 │    ├── codec
 │    └── math
 └── network
```

Có thể thêm:

```text
semantic dependency
ABI dependency
native dependency
build dependency
```

---

# 33. Binary inspection

Không nên bắt user dùng `objdump`.

```text
axiom inspect binary app.exe
```

hiển thị:

```text
format: PE
arch: x86_64
entry: ...
sections:
  .text
  .rdata
  .data
  .pdata
imports:
exports:
TLS:
debug:
```

Linux:

```text
format: ELF64
ABI: SysV
...
```

---

# 34. Disassembler

Axiom toolchain nên có:

```text
axiom disasm app
```

nhưng disassembler là tool, không phải compiler core.

Architecture:

```text
Machine bytes
 ↓
Target decoder
 ↓
Machine IR
 ↓
human-readable assembly
```

---

# 35. Object inspector

```text
axiom objdump
```

không nhất thiết tên này; có thể:

```text
axiom inspect --object
```

hiển thị:

```text
sections
symbols
relocations
imports
exports
debug
TLS
```

---

# 36. Reproducibility diagnostics

Build system đã yêu cầu deterministic builds.

Tool:

```text
axiom build --verify-reproducible
```

có thể:

```text
build A
build B
compare artifacts
```

và chỉ ra:

```text
difference:
    debug path
    timestamp
    symbol ordering
```

---

# 37. Build graph visualization

```text
axiom graph
```

```text
package A
 ├── package B
 ├── package C
 │    └── package D
 └── std
```

Có thể xuất:

```text
json
dot
svg
```

SVG là output tool, không phải compiler dependency.

---

# 38. IDE architecture

Tôi đề xuất:

```text
axiom/
├── compiler/
├── tools/
│   ├── lsp/
│   ├── debugger/
│   ├── profiler/
│   ├── sanitizer/
│   ├── formatter/
│   ├── doc/
│   ├── disasm/
│   └── inspector/
└── integrations/
    ├── vscode/
    ├── vim/
    └── ...
```

IDE plugin rất mỏng.

---

# 39. Không viết VS Code logic riêng

VS Code extension chủ yếu:

```text
start axiom lsp
start axiom debug
```

và hiển thị UI.

Semantic logic nằm trong Axiom.

---

# 40. Language Server process model

Có thể:

```text
IDE
 ↓
axiom lsp
 ↓
shared compiler daemon
```

Compiler daemon giữ:

```text
AST
HIR
symbol index
type cache
dependency graph
```

trong RAM.

---

# 41. Compiler daemon

```text
axiom serve
```

có thể phục vụ:

- LSP
- IDE
- AI agent
- background diagnostics
- incremental builds.

---

# 42. Nhưng build vẫn phải deterministic

Daemon cache chỉ là performance optimization.

Kết quả semantic phải giống:

```text
cold compiler
```

và:

```text
warm compiler
```

---

# 43. Compiler cache corruption

Nếu cache lỗi:

```text
delete cache
recompute
```

Không được để cache trở thành nguồn semantics.

---

# 44. AI agent workflow

Ví dụ AI muốn thêm function:

```text
Agent
 ↓
read semantic project map
 ↓
edit source
 ↓
axiom check --diagnostic=json
 ↓
receive AX_...
 ↓
axiom query/explain
 ↓
edit
 ↓
test
 ↓
build
```

Đây rất phù hợp với mục tiêu Axiom được xây dựng bằng AI agent.

---

# 45. Compiler should expose “semantic diff”

Một tính năng cực mạnh:

```text
axiom diff old new
```

Ví dụ:

```text
Public API:
    + Vec<T>::retain()

ABI:
    unchanged

Trait implementations:
    + Send for Foo

Unsafe surface:
    + 1 block

Dependencies:
    unchanged
```

---

# 46. Package API compatibility

Build system có thể dùng:

```text
axiom api-check
```

so sánh version:

```text
v1.2
vs
v1.3
```

Phát hiện:

```text
removed public function
changed parameter type
changed trait requirement
changed repr(C) layout
changed ABI
```

---

# 47. ABI compatibility

Đặc biệt:

```text
@repr(C)
extern "C"
```

phải được kiểm tra khác với Axiom internal ABI.

Ví dụ:

```text
Axiom ABI changed
```

không nhất thiết là lỗi.

Nhưng:

```text
C ABI changed
```

có thể phá binary compatibility.

---

# 48. Tooling invariants bổ sung

```text
AIDE-01  Compiler Is The Semantic Source Of Truth
AIDE-02  IDE Does Not Reimplement Type Checking
AIDE-03  LSP Uses Compiler Semantic Facts
AIDE-04  Semantic Queries Are Structured
AIDE-05  Symbol Identity Is Semantic
AIDE-06  Rename Is Semantic
AIDE-07  Reference Search Is Semantic
AIDE-08  Completion Is Type-Aware
AIDE-09  Refactoring Uses Compiler Facts
AIDE-10  Diagnostics Are Shared By CLI And IDE
AIDE-11  Ownership State May Be Visualized
AIDE-12  View Provenance May Be Visualized
AIDE-13  Async State May Be Visualized
AIDE-14  Unsafe Boundaries Are Inspectable
AIDE-15  ABI And Source Identity Are Distinct
AIDE-16  Optimization Facts Are Distinguished From Semantic Facts
AIDE-17  Target Facts Are Distinguished From Language Facts
AIDE-18  Compiler Cache Cannot Change Semantics
AIDE-19  Cold And Warm Compilation Are Semantically Equivalent
AIDE-20  AI Agents Consume Structured Compiler Facts
AIDE-21  AI Cannot Replace Compiler Semantic Verification
AIDE-22  Binary/Object Inspection Is First-Class Tooling
AIDE-23  Reproducibility Is Inspectable
AIDE-24  API/ABI Compatibility Can Be Compared
AIDE-25  IDE Plugins Remain Thin
```

---

# 49. Một quyết định kiến trúc lớn đã xuất hiện

Đến đây Axiom có thể chia thành **5 lớp hoàn chỉnh**:

```text
┌───────────────────────────────────────────┐
│ Developer / AI Tooling                    │
│ IDE • LSP • Debug • Profile • Inspect     │
├───────────────────────────────────────────┤
│ Package / Build                           │
│ Registry • Cache • Dependencies • PGO     │
├───────────────────────────────────────────┤
│ Compiler                                  │
│ AST • HIR • Type • Verify • MIR • LIR     │
├───────────────────────────────────────────┤
│ Native Toolchain                          │
│ Encoder • Object • Linker • Debug Info    │
├───────────────────────────────────────────┤
│ Platform                                  │
│ OS • ABI • CPU • GPU • Firmware           │
└───────────────────────────────────────────┘
```

Và điểm quan trọng:

**không lớp nào cần biến lớp phía trên thành một phần của ngôn ngữ.**

---

# 50. Kiến trúc Axiom hiện đã khá hoàn chỉnh

Nếu gom toàn bộ những gì đã chốt:

```text
                    AXIOM
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Language       Compiler       Toolchain
       │              │              │
  Types/Values      MIR/LIR      Object/Linker
  Ownership         Verify       PE/ELF/Mach-O
  Traits            Optimize     WASM
  Async             Backend
  GPU
  FFI
       │
       ↓
  Core Library
       │
       ↓
  Std / Platform
```

Đây không còn là một danh sách feature rời rạc nữa; nó đã có một **mô hình kiến trúc thống nhất**.

---

## Bước tiếp theo

Phần tiếp theo tôi sẽ chuyển sang thứ quan trọng nhất còn thiếu ở **language semantics**:

### **Module, visibility, initialization, global state, compile-time execution và macro/code-generation model**

Đặc biệt phải giải quyết dứt điểm:

```text
const
static
thread_static
comptime
reflection
generated code
conditional compilation
attributes
macro?
build-time generation
```

và quan trọng nhất:

> **Axiom có cần macro như Rust/C++ hay có thể loại bỏ gần như hoàn toàn macro bằng `comptime` + reflection + code generation có kiểm soát?**

Đây là một quyết định có ảnh hưởng trực tiếp tới độ đơn giản của cả ngôn ngữ.