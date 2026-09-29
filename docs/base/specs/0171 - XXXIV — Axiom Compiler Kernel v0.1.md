Tiếp tục. Từ đây tôi chuyển hẳn từ **design/specification** sang **implementation architecture**. Việc đầu tiên là khóa **Compiler Kernel v0.1**, vì mọi subsystem phía sau đều phụ thuộc nó.

# XXXIV — Axiom Compiler Kernel v0.1

Mục tiêu của Kernel không phải compile Axiom ngay. Nó tạo nền móng để toàn bộ compiler phía sau có:

- ID ổn định
- source/span chính xác
- diagnostics có cấu trúc
- interning
- arena
- query/incremental compilation
- cache
- session isolation
- deterministic behavior

---

# 1. Kernel không biết Axiom semantics

Đây là boundary cực kỳ quan trọng.

```text
compiler/kernel
        ↑
lexer
parser
resolver
typeck
...
```

Kernel **không được biết**:

```text
ownership
traits
MIR
x86
ELF
Drop
view
async
```

Kernel chỉ cung cấp infrastructure.

---

# 2. Repository

Tôi chốt:

```text id="9tq8aw"
compiler/
├── kernel/
│   ├── id.ax
│   ├── span.ax
│   ├── source.ax
│   ├── arena.ax
│   ├── interner.ax
│   ├── symbol.ax
│   ├── type_id.ax
│   ├── diagnostic.ax
│   ├── query.ax
│   ├── cache.ax
│   ├── session.ax
│   ├── config.ax
│   └── tests/
```

Không tạo một `kernel.ax` khổng lồ.

---

# 3. Stable IDs

Axiom compiler không dùng pointer làm semantic identity.

Ta định nghĩa:

```text id="6j9r3p"
FileId
PackageId
ModuleId

SymbolId
TypeId
TraitId
FunctionId
FieldId
VariantId
ImplId

LocalId
BlockId
ExprId
StmtId
PatternId
ItemId

InstrId
AllocationId

QueryId
DiagnosticId
```

Mỗi ID là typed ID.

Ví dụ concept:

```text id="v1m6c8"
struct FunctionId {
    index: u32
}
```

Không cho:

```text id="3j2x9n"
FunctionId ↔ TypeId
```

implicit conversion.

Điều này loại được một lớp bug cực lớn trong compiler.

---

# 4. Không dùng string làm identity

Sai:

```text id="8x3m5p"
functions["main"]
```

Đúng:

```text id="6y7q1k"
FunctionId(42)
```

Tên:

```text id="9s2v5m"
StringId
```

được dùng để lookup.

Semantic identity:

```text id="0q4k8r"
FunctionId
```

là thứ compiler giữ.

---

# 5. String Interner

Identifier:

```text id="1m9q7v"
"hello"
```

được intern:

```text id="6c3p8x"
StringId
```

Nếu xuất hiện 100.000 lần:

```text id="f4r7w2"
"foo"
```

thì chỉ có một interned representation.

Nhưng:

```text id="5x2m9k"
StringId != SymbolId
```

Tên và declaration identity khác nhau.

---

# 6. Source Database

```text id="n6r1v8"
SourceDatabase
├── FileId
├── SourceText
├── LineMap
├── ContentHash
└── ModuleId
```

Ví dụ:

```text id="7w4k2z"
FileId(12)
    ↓
"fn main() {}"
```

---

# 7. Span

Freeze:

```text id="c2q7m5"
Span {
    file: FileId
    start: u32
    end: u32
}
```

Byte offsets.

Không lưu:

```text id="0v8n4p"
line
column
```

trong semantic span.

Line/column là presentation layer.

---

# 8. Tại sao byte span?

Vì:

```text id="4m9x2k"
source[start..end]
```

là O(1) identity.

Line/column có thể tính từ `LineMap`.

Ngoài ra byte span tương thích tốt với:

- UTF-8
- diagnostics
- editor protocol
- source hashing
- incremental parsing

---

# 9. Source identity

`FileId` chỉ có ý nghĩa trong compilation session.

Không được cache dựa vào:

```text id="p3x7r1"
FileId = 42
```

vì session khác có thể cũng có `FileId = 42`.

Persistent identity:

```text id="k8m2v5"
SemanticKey =
    PackageId
  + CanonicalPath
  + ContentHash
```

---

# 10. Compiler Session

Một compile invocation:

```text id="v5q9n1"
CompilerSession
```

chứa:

```text id="8k2m6r"
SourceDatabase
StringInterner
SymbolTable
TypeInterner
Diagnostics
QueryDatabase
Cache
CompilerConfig
TargetConfig
```

Không có global semantic singleton.

---

# 11. Tại sao không global state?

Nếu có:

```text id="3m8q7x"
GLOBAL_SYMBOL_TABLE
GLOBAL_TYPE_CACHE
```

sẽ phá:

- parallel compilation
- deterministic tests
- multiple compiler sessions
- IDE incremental compilation
- server mode

Axiom compiler phải cho phép:

```text id="p7v2k4"
Session A
Session B
Session C
```

chạy đồng thời mà không semantic interference.

---

# 12. Diagnostics

Diagnostic là object có cấu trúc:

```text id="f3m8q1"
Diagnostic {
    severity
    code
    message
    primary_span
    labels
    notes
    suggestions
    related
}
```

Ví dụ:

```text id="z5q2m7"
AX_OWN_0001
Use of moved value
```

Không coi message text là identity.

---

# 13. Diagnostic code ≠ DiagnosticId

Rất quan trọng.

```text id="8m3v6q"
DiagnosticId
```

là identity của một diagnostic instance.

Trong khi:

```text id="y7k2p4"
AX_OWN_0001
```

là semantic error code.

100 lỗi:

```text id="m4q8x1"
AX_OWN_0001
```

có thể có 100 `DiagnosticId`.

---

# 14. Diagnostic JSON

Compiler phải hỗ trợ:

```bash id="q8v3m1"
axiom check --diagnostics=json
```

Ví dụ:

```json
{
  "code": "AX_OWN_0001",
  "severity": "error",
  "message": "use of moved value",
  "primary": {
    "file": "src/main.ax",
    "start": 42,
    "end": 43
  }
}
```

AI tooling có thể consume trực tiếp.

---

# 15. Arena

Compiler internal objects có thể dùng arena:

```text id="2v7m5q"
AstArena
HirArena
MirArena
DiagnosticArena
```

Điều này không liên quan Axiom program memory semantics.

Đây là implementation detail của compiler.

---

# 16. Typed Arena IDs

Không trả:

```text id="1q6x9r"
*Node
```

ra khắp compiler.

Thay:

```text id="9v3m7k"
ExprId
TypeId
ItemId
```

Compiler ownership sẽ dễ kiểm soát hơn.

---

# 17. Type Interner

Type:

```text id="m3x8q2"
i32
```

chỉ có một `TypeId`.

Tương tự:

```text id="q6v1k9"
view<i32>
```

canonicalize thành một TypeId.

---

# 18. Type identity

Ví dụ:

```text id="v9q4m2"
Vec<i32>
```

và:

```text id="x7m3p8"
Vec<i32>
```

trong cùng semantic universe phải có cùng `TypeId`.

Nhưng:

```text id="k2n8r5"
foo::Vec<i32>
bar::Vec<i32>
```

có thể khác nhau.

Package identity tham gia semantic identity.

---

# 19. Query System

Đây là phần quan trọng nhất của Kernel.

Thay vì compiler pipeline cứng:

```text id="2m8q5x"
compile_everything()
```

ta có query:

```text id="n7v3k1"
parse(FileId)
resolve(ModuleId)
hir(ItemId)
type(TypeQuery)
mir(FunctionId)
verified_mir(FunctionId)
abi(FunctionId)
object(ObjectQuery)
```

Query chỉ tính khi cần.

---

# 20. Query property

Mỗi query:

```text id="4q8m1z"
Input
→ Dependencies
→ Value
```

Ví dụ:

```text id="p6v2n9"
mir(FunctionId(10))
```

phụ thuộc:

```text id="x3m7q5"
TypedHir(FunctionId(10))
Type information
Trait resolution
Ownership facts
```

Nếu dependency không đổi:

```text id="v8k2m4"
cache hit
```

---

# 21. Query không được side effect ngầm

Query:

```text id="j5q9x2"
type(...)
```

không được:

```text id="m1v7k4"
write_file()
network()
mutate_global_state()
```

Nếu cần external input:

```text id="n4x8q6"
declared input
```

phải trở thành dependency.

---

# 22. Query cycle

Một query có thể vô tình:

```text id="k8m3q1"
A → B → C → A
```

Query system phải phát hiện.

Diagnostic/compiler internal error:

```text id="AXC_INTERNAL_..."
```

không phải program error.

---

# 23. Query determinism

Cùng input:

```text id="4n7x2m"
Q(input)
```

phải cho cùng semantic result.

Không được phụ thuộc:

```text id="8q1v5p"
hash-map iteration
thread scheduling
filesystem order
wall clock
random
```

---

# 24. Parallel queries

Nếu:

```text id="p5m9q3"
type(A)
type(B)
type(C)
```

không phụ thuộc nhau, scheduler có thể chạy:

```text id="x7k2v8"
A ─┐
B ─┼── parallel
C ─┘
```

Nhưng kết quả phải deterministic.

---

# 25. Query cache

Cache:

```text id="w3q8m1"
QueryKey
    ↓
InputFingerprint
    ↓
Output
    ↓
DependencyFingerprint
```

Nếu fingerprint giống:

```text id="z9v4k2"
reuse
```

---

# 26. Không serialize pointer

Cache không được ghi:

```text id="n6x2q8"
pointer address
arena index without semantic identity
```

Persistent cache chỉ lưu semantic representation.

Ví dụ:

```text id="v5m1q7"
TypeId
```

của session phải remap khi load cache.

---

# 27. Cache layers

Chốt:

```text id="h8q3m1"
Source Cache
     ↓
AST Cache
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

Không nhất thiết tất cả đều persistent trong v0.1.

Ban đầu:

```text id="y2m7q5"
AST/HIR in-memory
MIR/Object persistent
```

sau đó mở rộng.

---

# 28. Query boundary

Frontend:

```text id="j3v8n2"
parse
resolve
hir
type
```

Middle:

```text id="k6q1m9"
ownership
capability
mir
verify
```

Backend:

```text id="r4x7p3"
optimize
lir
machine
object
```

Không để backend gọi ngược:

```text id="bad"
backend → parser
```

---

# 29. Compiler Configuration

Config phải immutable sau khi Session khởi tạo:

```text id="w8m2q5"
CompilerConfig {
    edition
    optimization
    debug
    panic_mode
    target
    features
    diagnostics
}
```

Không để pass tự thay đổi global config.

---

# 30. Target Configuration

Tách:

```text id="q4v9m1"
CompilerConfig
```

và:

```text id="x7k3p8"
TargetConfig
```

Target:

```text id="n2m6q5"
architecture
os
abi
endianness
pointer_width
features
object_format
```

Frontend chỉ nhìn những target properties mà semantics thực sự cho phép.

---

# 31. Semantic vs implementation IDs

Cực kỳ quan trọng:

```text id="y8q2m4"
FunctionId
```

là semantic.

Nhưng:

```text id="v3k7n1"
MachineBlockId
RegisterId
MachineInstrId
```

là backend implementation.

Không trộn.

---

# 32. Kernel API tối thiểu

Sau này các subsystem có thể gọi:

```text id="q6m1v8"
session.source(...)
session.diagnostics(...)
session.parse(...)
session.resolve(...)
session.types(...)
session.query(...)
session.cache(...)
```

Nhưng không được phép truy cập trực tiếp database nội bộ của subsystem khác.

---

# 33. Pass Manager

Sau Kernel sẽ có:

```text id="r8x3m5"
PassManager
```

Mỗi pass khai báo:

```text id="j2q7v4"
InputInvariant
OutputInvariant
RequiredFacts
InvalidatedFacts
```

Ví dụ:

```text id="k5m9x1"
BoundsCheckElimination

requires:
    VerifiedMIR
    RangeFacts

produces:
    OptimizedMIR

preserves:
    OwnershipSafety
    CapabilitySafety
```

---

# 34. Hard semantic checkpoint

Đây là checkpoint tuyệt đối:

```text id="v7q2m8"
Typed HIR
    ↓
Ownership/Capability
    ↓
MIR
    ↓
Verifier
    ↓
╔══════════════════════╗
║     VERIFIED MIR     ║
╚══════════════════════╝
    ↓
Optimizer
```

Sau Verified MIR:

> Compiler không được phép "sửa" semantics vì backend.

Nếu optimizer phát hiện MIR invalid:

```text
AXC_INTERNAL_...
```

---

# 35. Oracle

Oracle chạy song song:

```text id="p8m4x2"
Source
 ↓
Compiler
 ↓
Verified MIR ───────────┐
                        │
                        ▼
                     Oracle
                        │
                        ▼
                    Reference
```

Native:

```text id="q7v3n9"
Verified MIR
 ↓
Optimize
 ↓
Backend
 ↓
Executable
```

Harness so sánh:

```text id="z1m6k4"
Oracle behavior
==
Native behavior
```

---

# 36. Kernel first milestone

### KERNEL-001

Implement:

```text id="6x9q2m"
FileId
ModuleId
SymbolId
TypeId
FunctionId
FieldId
VariantId
LocalId
BlockId
InstrId
DiagnosticId
```

### KERNEL-002

```text id="m4v8q1"
SourceDatabase
Span
LineMap
ContentHash
```

### KERNEL-003

```text id="q7n3x5"
StringInterner
TypeInterner
```

### KERNEL-004

```text id="p2k8m6"
Diagnostics
JSON output
```

### KERNEL-005

```text id="v9q1x4"
CompilerSession
CompilerConfig
TargetConfig
```

### KERNEL-006

```text id="x3m7q2"
Query engine
```

### KERNEL-007

```text id="n8v4k1"
Incremental cache
```

---

# 37. Test đầu tiên

Ngay cả trước Lexer:

```bash id="f3m8q7"
axiom check empty.ax
```

với:

```axiom id="b4n2v8"
```

file rỗng.

Compiler phải trả:

```text
exit 0
```

và:

```json
{
  "diagnostics": []
}
```

---

# 38. Sau đó mới Lexer

Vertical slice:

```text id="j8q2m5"
"fn main() {}"
```

Lexer:

```text id="q4v7n1"
FN
IDENT(main)
LPAREN
RPAREN
LBRACE
RBRACE
EOF
```

Parser:

```text id="x6m3p9"
FunctionDecl
```

Resolver:

```text id="r1v8k4"
FunctionId
```

Type checker:

```text id="m7q2x5"
return = unit
```

MIR:

```text id="p3n9v6"
RETURN unit
```

Verifier:

```text id="z8k4m1"
valid
```

LIR:

```text id="q5x7n2"
RETURN
```

Machine:

```asm
ret
```

---

# 39. Nhưng `main` chưa phải entry point của ELF

Đúng theo thiết kế trước:

```text id="e4v8m2"
_start
  ↓
Axiom startup
  ↓
main
  ↓
exit
```

Vì vậy vertical slice đầu tiên có thể dùng:

```text id="r7q3n5"
@entry
fn main()
```

và startup layer tối thiểu.

---

# 40. Kernel invariant set

Tôi chốt thêm:

```text id="AKERNEL-24"
All compiler semantic identities use typed IDs.

AKERNEL-25
Session-local IDs are not persistent cache identities.

AKERNEL-26
Source spans use byte offsets.

AKERNEL-27
Diagnostics have stable semantic codes.

AKERNEL-28
Diagnostic IDs are instance identities.

AKERNEL-29
Compiler sessions have no hidden global semantic state.

AKERNEL-30
Query results are deterministic.

AKERNEL-31
Query dependencies are explicit.

AKERNEL-32
Parallel query evaluation preserves semantic results.

AKERNEL-33
Persistent caches use semantic fingerprints.

AKERNEL-34
Compiler-internal failures are distinct from program failures.

AKERNEL-35
Kernel has no dependency on target backend.

AKERNEL-36
Kernel has no dependency on Axiom runtime.

AKERNEL-37
Kernel abstractions are independent of source-language ownership semantics.
```

---

# 41. Một quyết định lớn: compiler viết bằng gì?

Đây là chỗ cần thực tế.

Ta **không nên cố viết toàn bộ compiler production bằng Axiom ngay lập tức**, vì chưa có Axiom compiler.

Bootstrap:

```text id="w5m9q2"
Stage 0
    C++/Rust/another implementation
          ↓
     axiom-bootstrap
          ↓
Stage 1
    compiler written in Axiom subset
          ↓
Stage 2
    compiler written in full Axiom
```

Nhưng Stage 0 phải **tối thiểu**.

Không xây:

```text id="n2q7v4"
100,000 LOC C++ compiler
```

rồi gọi đó là bootstrap.

---

# 42. Bootstrap Compiler

`ax-bootstrap` chỉ cần hiểu subset:

```text id="k8x3m1"
fn
struct
enum
let
var
if
while
return
calls
arrays
basic generics
basic ownership
basic view
```

và compile được compiler kernel.

Nó có thể sử dụng:

```text id="q4m7v9"
system linker
```

tạm thời.

Không được định nghĩa semantics khác production compiler.

---

# 43. Bootstrap strategy

Tôi chốt:

```text id="r9x2m6"
Stage 0
Minimal external bootstrap
       │
       ▼
Stage 1
Axiom compiler frontend
       │
       ▼
Stage 2
Axiom compiler + MIR
       │
       ▼
Stage 3
Axiom compiler + own backend
       │
       ▼
Stage 4
Self-hosted compiler + linker
```

Không cần chờ toàn bộ stdlib.

Compiler có thể dùng một **bootstrap core subset**.

---

# 44. Điều này dẫn tới thứ tự implementation thật

Không phải:

```text
stdlib
→ compiler
```

mà:

```text
Kernel
 ↓
Lexer
 ↓
Parser
 ↓
Resolver
 ↓
HIR
 ↓
Type checker
 ↓
Ownership
 ↓
MIR
 ↓
Verifier
 ↓
LIR
 ↓
x86 backend
 ↓
Encoder
 ↓
ELF
 ↓
Linker
 ↓
Minimal Core
 ↓
Bootstrap compiler
 ↓
Self-host
 ↓
Full Std
```

Đây là thứ tự có dependency hợp lý nhất.

---

# 45. Và từ đây không nên tiếp tục "thiết kế lan rộng"

Phần architecture đã đủ để bắt đầu code.

**Task kế tiếp là KERNEL-001 → KERNEL-007**, sau đó lập tức làm vertical slice:

```text
empty.ax
   ↓
fn main() {}
   ↓
x86-64 machine code
   ↓
ELF
   ↓
axiom-link
   ↓
executable
```

Một khi binary `main() {}` thực sự chạy được, chúng ta sẽ có **Axiom compiler skeleton thực sự**, và từ đó các task tiếp theo sẽ là implementation từng vertical slice thay vì tiếp tục tạo thêm spec.