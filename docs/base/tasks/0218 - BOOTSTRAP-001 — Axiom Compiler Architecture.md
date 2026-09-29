Tiếp tục. Sau khi đã chốt `TYPE → ABI → LIR → MACHINE IR → OBJECT → LINK`, bước hợp lý tiếp theo là **BOOTSTRAP-001 — kiến trúc compiler và con đường self-hosting**.

Mục tiêu của phần này là tránh một lỗi rất dễ gặp: thiết kế Axiom rất tốt về ngôn ngữ nhưng compiler lại trở thành một “đống C++ + LLVM” mà cuối cùng không thể tự thoát ra.

# BOOTSTRAP-001 — Axiom Compiler Architecture

## 1. Mục tiêu cuối cùng

Compiler Axiom hoàn chỉnh phải có khả năng:

```text
axiom source
    ↓
Axiom Compiler
    ↓
AST
    ↓
HIR
    ↓
Typed HIR
    ↓
MIR
    ↓
Verified MIR
    ↓
LIR
    ↓
Machine IR
    ↓
Object
    ↓
Axiom Linker
    ↓
Native executable
```

Và quan trọng:

```text
Axiom Compiler
    └── được viết bằng Axiom
```

Không:

```text
Axiom Compiler
    └── phụ thuộc vĩnh viễn vào LLVM
    └── phụ thuộc GCC
    └── phụ thuộc Clang
    └── cần C++ runtime
```

LLVM/Clang có thể được dùng **trong bootstrap**, nhưng không được trở thành một phần kiến trúc bắt buộc của Axiom.

---

# 2. Không nên viết compiler đầu tiên hoàn toàn bằng Axiom

Có một nghịch lý:

> Muốn compiler Axiom được viết bằng Axiom thì trước tiên phải có compiler Axiom.

Do đó nên dùng **3 stage bootstrap**.

### Stage 0 — Bootstrap compiler

Viết bằng một ngôn ngữ host đã có compiler ổn định.

Ví dụ:

```text
C / C++ / Rust
```

Nhưng compiler này phải được thiết kế như một **temporary bootstrap implementation**, không phải kiến trúc vĩnh viễn.

```text
bootstrap/
    parser
    resolver
    typechecker
    MIR
    verifier
    LIR
    x86_64 backend
    object writer
    linker
```

Stage 0 có thể dùng LLVM để tăng tốc giai đoạn đầu.

Nhưng API của compiler phải được thiết kế sao cho:

```text
LLVM backend
```

chỉ là:

```text
Backend::LLVM
```

chứ không phải:

```text
Compiler = LLVM wrapper
```

Đây là khác biệt cực kỳ quan trọng.

---

# 3. Stage 1 — Compiler có backend native đầu tiên

Sau khi frontend ổn định:

```text
Axiom source
    ↓
Stage-0 compiler
    ↓
Axiom LIR
    ↓
Native backend
```

Backend đầu tiên nên là:

> **x86-64**

Vì đây là target rất phù hợp để xây compiler native hoàn chỉnh.

Ta có:

```text
Axiom
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine IR
 ↓
x86-64
 ↓
ELF/PE
```

Lúc này compiler **không còn cần LLVM để tạo machine code**.

LLVM vẫn có thể tồn tại như một backend kiểm chứng:

```text
Axiom LIR
 ├──→ Axiom x86-64 backend
 └──→ LLVM reference backend
```

Sau khi native backend đủ ổn:

```text
LLVM backend
```

trở thành optional.

---

# 4. Stage 2 — Viết compiler bằng chính Axiom

Đây mới là bước self-host.

Ta tạo:

```text
axiomc/
```

và viết lại compiler:

```text
axiomc/
├── lexer.ax
├── parser.ax
├── ast.ax
├── resolver.ax
├── types.ax
├── traits.ax
├── hir.ax
├── mir.ax
├── verifier.ax
├── drop.ax
├── async.ax
├── capability.ax
├── lir.ax
├── machine.ax
├── backend/
│   └── x86_64/
├── object/
├── linker/
└── driver.ax
```

Compiler cũ compile compiler mới:

```text
stage0 axiomc
       │
       ├── compile lexer.ax
       ├── compile parser.ax
       ├── compile ...
       └── compile axiomc.ax
                    ↓
             axiomc-native
```

Sau đó:

```text
axiomc-native
      ↓
compile itself
      ↓
axiomc-native-2
```

Nếu:

```text
axiomc-native
```

có thể compile chính source của nó và tạo ra compiler tương đương:

> Axiom đã đạt self-hosting.

---

# 5. Một nguyên tắc rất quan trọng: Compiler không được biết quá nhiều về target

Tôi đề xuất chia compiler thành 4 tầng lớn:

```text
┌─────────────────────────────┐
│        Frontend             │
│ lexer/parser/type/trait     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Semantic Core          │
│ HIR/MIR/ownership/verifier  │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│      Target-independent      │
│            LIR               │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│       Target Backend         │
│ x86 / ARM / RISC-V / WASM   │
└─────────────────────────────┘
```

Điều này cực kỳ có lợi cho Axiom.

Ví dụ frontend không được có:

```text
if target == x86_64:
```

Backend mới được biết:

```text
RAX
RBX
XMM0
RIP
```

---

# 6. Repository nên chia như thế này

Tôi đề xuất cấu trúc dài hạn:

```text
axiom/
│
├── compiler/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── mir/
│   ├── verifier/
│   ├── optimization/
│   ├── abi/
│   ├── lir/
│   ├── machine/
│   ├── backend/
│   │   ├── x86_64/
│   │   ├── aarch64/
│   │   ├── riscv64/
│   │   └── wasm/
│   ├── object/
│   ├── linker/
│   └── driver/
│
├── runtime/
│   ├── core/
│   ├── alloc/
│   ├── thread/
│   ├── async/
│   ├── panic/
│   └── tls/
│
├── std/
│   ├── collections/
│   ├── io/
│   ├── fs/
│   ├── net/
│   ├── sync/
│   ├── async/
│   ├── unicode/
│   └── os/
│
├── targets/
│   ├── x86_64-linux/
│   ├── x86_64-windows/
│   ├── aarch64-linux/
│   ├── aarch64-macos/
│   ├── wasm32/
│   └── riscv64/
│
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── type/
│   ├── ownership/
│   ├── traits/
│   ├── mir/
│   ├── backend/
│   ├── codegen/
│   ├── linker/
│   └── integration/
│
├── fuzz/
├── examples/
├── benchmarks/
├── docs/
└── tools/
```

Nhưng **không nên triển khai tất cả ngay**.

---

# 7. Compiler core nên cực kỳ modular

Một quyết định tôi muốn chốt:

### Không để frontend gọi trực tiếp backend.

Sai:

```text
Parser
 ↓
x86_64 codegen
```

Đúng:

```text
Parser
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
LIR
 ↓
Backend
```

Mỗi tầng có verifier riêng.

Ví dụ:

```text
verify_ast()
verify_hir()
verify_typed_hir()
verify_mir()
verify_verified_mir()
verify_lir()
verify_machine_ir()
verify_object()
```

Điều này cực kỳ quan trọng khi compiler được AI hỗ trợ phát triển.

---

# 8. Compiler phải có một “semantic authority”

Đây là phần đặc biệt quan trọng đối với Axiom.

Không được để:

```text
type checker
ownership checker
borrow/capability analyzer
MIR optimizer
backend
```

tự hiểu semantics theo cách riêng.

Nên có một nguồn sự thật:

```text
Axiom Semantic Model
```

Ví dụ:

```text
Type
Ownership
Capability
Region
Effect
ExecutionDomain
StorageDomain
Trait
ABI
```

được định nghĩa tập trung.

Các compiler phase chỉ biến đổi representation.

Ví dụ:

```text
Source:
    mut_view<T>

HIR:
    Capability {
        access = WRITE
        provenance = P
    }

MIR:
    BorrowCapability {
        region = R
        access = WRITE
    }

LIR:
    memory operand
```

Sau khi compiler chứng minh capability hợp lệ thì thông tin đó có thể bị erase.

Đây chính là:

> **Semantic information first, machine representation later.**

---

# 9. Ownership checker không phải Borrow Checker kiểu Rust

Đây là điểm tôi muốn giữ nguyên theo hướng chúng ta đã chốt.

Compiler có thể thực hiện:

```text
ownership analysis
lifetime analysis
alias analysis
escape analysis
region analysis
```

nhưng programmer không phải viết:

```text
'a
'b
where ...
```

và cũng không phải liên tục suy nghĩ:

```text
&i32
&mut i32
```

trong code thông thường.

Ví dụ:

```text
fn sum(a: view<i32>, b: view<i32>) -> i32
```

Compiler biết:

```text
READ(a)
READ(b)
```

và kiểm tra chúng.

Trong khi:

```text
fn update(x: mut_view<Data>)
```

có:

```text
WRITE(x)
```

Đây là capability system, không phải một ngôn ngữ lifetime annotation.

---

# 10. Compiler nên có “facts engine”

Tôi đề xuất một thành phần mới:

```text
Semantic Facts Engine
```

Nó lưu các facts compiler đã chứng minh.

Ví dụ:

```text
Fact:
    x owns T

Fact:
    v derives from x

Fact:
    v region = [0..128]

Fact:
    v access = READ

Fact:
    a and b DISJOINT

Fact:
    future F owns x

Fact:
    F cannot migrate

Fact:
    T : Send

Fact:
    T : Share
```

Các phase sau không cần tự suy luận lại từ đầu.

```text
Parser
   ↓
Resolver
   ↓
Type facts
   ↓
Ownership facts
   ↓
Capability facts
   ↓
Concurrency facts
   ↓
MIR
```

Đây sẽ giúp compiler vừa nhanh vừa dễ kiểm chứng.

---

# 11. Diagnostic system phải được thiết kế từ đầu

Axiom nên có diagnostic machine-readable:

```text
AX0012
AX0207
AX0314
```

Ví dụ:

```text
AX0207: conflicting mutable capability

error:
    cannot create mutable view of `buffer`

reason:
    an active read capability exists

active capability:
    `data_view`
    region: buffer[0..1024]
    access: READ

requested capability:
    region: buffer[512..1536]
    access: WRITE

overlap:
    buffer[512..1024]
```

Compiler đồng thời xuất:

```text
human diagnostic
```

và:

```json
{
    "code": "AX0207",
    "phase": "capability",
    "severity": "error",
    "region": "...",
    "related": [...]
}
```

Điều này cực kỳ hữu ích cho IDE và AI agent.

---

# 12. Incremental compilation

Axiom nên hỗ trợ incremental ngay từ kiến trúc.

Module:

```text
foo.ax
```

compile thành semantic artifact:

```text
foo.axm
```

Có thể chứa:

```text
type information
trait information
public signatures
ABI information
generic definitions
comptime information
dependency fingerprints
```

Không nhất thiết chứa machine code.

Sau đó:

```text
foo.ax
 ↓
semantic artifact
 ↓
codegen
```

Nếu chỉ sửa:

```text
foo_internal_function()
```

thì compiler không cần type-check lại toàn bộ project.

---

# 13. Generic compilation

Vì Axiom dùng monomorphization, compiler phải xử lý:

```text
Vec<i32>
Vec<f64>
Vec<MyStruct>
```

nhưng tránh tạo code trùng.

Pipeline:

```text
Generic IR
      ↓
Instantiation
      ↓
Specialized MIR
      ↓
Optimization
      ↓
Machine code
```

Sau đó linker/COMDAT có thể deduplicate.

Điều này tận dụng thiết kế `ALINK-32`.

---

# 14. Compile-time execution

Comptime cũng phải dùng cùng compiler semantic engine:

```text
comptime
   ↓
normal Axiom semantics
   ↓
interpreter / evaluator
```

Không tạo một “ngôn ngữ thứ hai”.

Ví dụ:

```text
comptime {
    generate_table()
}
```

không phải:

```text
Axiom
+
một macro language
+
một scripting language
```

Mà chỉ là Axiom chạy ở compile-time.

---

# 15. AST không nên tồn tại quá lâu

Pipeline nên:

```text
Source
 ↓
AST
 ↓
HIR
```

AST phục vụ syntax.

HIR phục vụ semantic structure.

Ví dụ syntax:

```text
foo.bar(x)
```

AST giữ:

```text
MethodCall(
    receiver = foo,
    name = bar,
    args = [x]
)
```

Sau resolution:

```text
Call(
    function = Symbol#1827,
    args = [foo, x]
)
```

Sau đó method syntax gần như biến mất.

Điều này rất phù hợp triết lý:

> **Syntax sugar nên biến mất càng sớm càng tốt.**

---

# 16. MIR là “trái tim” compiler

Axiom MIR nên là nơi có semantics gần như hoàn chỉnh.

Ví dụ:

```text
var x = Foo()
use(x)
```

MIR có thể:

```text
ALLOC_LOCAL x
CONSTRUCT Foo -> x
CALL use(x)
DROP x
RETURN
```

Sau optimization:

```text
CONSTRUCT Foo
CALL use
DROP Foo
RETURN
```

Nếu `Foo` không có observable storage identity, backend có thể scalarize.

---

# 17. MIR phải explicit hóa những thứ quan trọng

MIR nên explicit:

```text
MOVE
COPY
BORROW_READ
BORROW_WRITE
DROP
ALLOC
DEALLOC
CALL
RETURN
BRANCH
SWITCH
AWAIT
SPAWN
ATOMIC
LOCK
UNLOCK
```

Không nên để backend phải đoán:

> “À, lệnh này có lẽ là move.”

Semantics phải được quyết định trước codegen.

---

# 18. Nhưng MIR không nên chứa machine details

Không:

```text
RAX
RSP
XMM0
```

trong MIR.

MIR:

```text
%tmp = add %a, %b
```

LIR:

```text
v42 = add v17, v19
```

Machine IR:

```text
ADD rax, rcx
```

Phân tầng rất rõ.

---

# 19. Testing strategy

Axiom compiler nên có 5 lớp test.

### Unit

```text
lexer
parser
type
trait
ownership
capability
```

### Semantic tests

```text
valid/
invalid/
```

Ví dụ:

```text
tests/capability/overlap_write.ax
tests/capability/disjoint_write.ax
```

### Codegen tests

```text
Axiom source
→ expected MIR
→ expected LIR
→ expected assembly/object behavior
```

### Differential tests

Trong bootstrap:

```text
Axiom
 ├── Axiom backend
 └── LLVM backend
```

So sánh:

```text
return value
stdout
memory behavior
ABI
```

Không so sánh assembly byte-for-byte.

### Fuzzing

Đặc biệt:

```text
parser
type checker
trait solver
MIR verifier
LIR verifier
object writer
linker
```

---

# 20. Compiler phải tự kiểm tra chính nó

Mỗi compiler stage có verifier.

Ví dụ:

```text
MIRVerifier
```

kiểm tra:

```text
- every SSA/value definition valid
- no use after move
- no invalid capability
- no dangling view
- Drop exactly once
- no conflicting mutation
- valid control flow
- valid async suspension
```

LIR verifier:

```text
- valid types
- valid control flow
- valid memory operation
- valid ABI
```

Machine verifier:

```text
- registers legal
- operands legal
- instruction constraints valid
- stack offsets valid
- calling convention valid
```

Object verifier:

```text
- symbols valid
- relocations valid
- section references valid
```

---

# 21. Một điểm rất quan trọng: Compiler phải có “panic boundary”

Compiler không được:

```text
crash
segmentation fault
```

khi gặp source code sai.

Mỗi phase phải trả:

```text
Result<T, CompilerError>
```

và internal compiler bug phải trở thành:

```text
ICE: Internal Compiler Error
```

với:

```text
phase
function
IR snapshot
source location
compiler version
target
```

Có thể bật:

```text
--emit-ir-on-error
--dump-mir
--dump-lir
--dump-machine
```

để debug compiler.

---

# 22. Build system của Axiom

Không nên phụ thuộc CMake/Make trong dài hạn.

Bootstrap có thể dùng:

```text
CMake / Ninja
```

hoặc tương đương.

Nhưng cuối cùng:

```text
axiom build
```

phải tự build compiler.

Mục tiêu:

```text
bootstrap compiler
       ↓
build axiom compiler
       ↓
axiom compiler
       ↓
axiom build
```

Sau self-host:

```text
axiom build
```

không cần host compiler C/C++.

---

# 23. Compiler distribution

Một Axiom SDK hoàn chỉnh nên có:

```text
axiom
axiomc
axiom-link
axiom-fmt
axiom-test
axiom-doc
axiom-pkg
```

Nhưng không nhất thiết là nhiều executable.

Có thể:

```text
axiom
  ├── build
  ├── run
  ├── test
  ├── fmt
  ├── doc
  ├── check
  └── compile
```

và một compiler core:

```text
libaxiomc
```

---

# 24. Tôi đề xuất thêm một nguyên tắc kiến trúc

## AXIOM-COMPILER-01 — Every Phase Has A Contract

Mỗi phase phải có:

```text
Input representation
Output representation
Invariants
Verifier
Diagnostics
```

Ví dụ:

```text
MIR
```

không chỉ là một struct trong source code.

Nó phải có specification:

```text
MIR Contract
```

và:

```text
MIR Verifier
```

Điều này khiến AI agent có thể tự phát triển compiler mà không “tự nghĩ ra semantics mới”.

---

# 25. Compiler architecture cuối cùng

Tôi đề xuất chốt kiến trúc:

```text
                    ┌──────────────┐
                    │    Source    │
                    └──────┬───────┘
                           ↓
                    ┌──────────────┐
                    │ Lexer/Parser │
                    └──────┬───────┘
                           ↓
                         AST
                           ↓
                    ┌──────────────┐
                    │   Resolver   │
                    └──────┬───────┘
                           ↓
                          HIR
                           ↓
                 ┌────────────────────┐
                 │ Semantic Engine    │
                 │                    │
                 │ Types              │
                 │ Traits             │
                 │ Ownership          │
                 │ Capability         │
                 │ Concurrency        │
                 │ Effects            │
                 └─────────┬──────────┘
                           ↓
                      Typed HIR
                           ↓
                         MIR
                           ↓
                    MIR Verification
                           ↓
                    Drop Elaboration
                           ↓
                    MIR Optimization
                           ↓
                      ABI Lowering
                           ↓
                         LIR
                           ↓
                    LIR Optimization
                           ↓
                   Target Legalization
                           ↓
                     Machine IR
                           ↓
                  Register Allocation
                           ↓
                  Machine Optimization
                           ↓
                    Machine Encoder
                           ↓
                        Object
                           ↓
                     Axiom Linker
                           ↓
                    Native Executable
```

Đây là kiến trúc đủ mạnh để Axiom cuối cùng trở thành một compiler native hoàn chỉnh chứ không phải một frontend bọc LLVM.

---

# 26. Bootstrap roadmap nên chốt như sau

```text
PHASE 0
────────────────────────────
Language specification
        ↓
Reference interpreter/checker
        ↓
Bootstrap compiler


PHASE 1
────────────────────────────
x86-64 backend
        ↓
ELF
        ↓
PE/COFF
        ↓
Axiom linker


PHASE 2
────────────────────────────
Axiom compiler written in Axiom
        ↓
self compile
        ↓
self compile again


PHASE 3
────────────────────────────
AArch64
RISC-V
WASM


PHASE 4
────────────────────────────
Standard library
OS layer
async runtime
network
filesystem
GUI
GPU


PHASE 5
────────────────────────────
LTO
PGO
advanced optimization
auto-vectorization
multiversioning
incremental compilation
distributed build
```

## Và một quyết định quan trọng

**Không nên bắt đầu bằng standard library.**

Thứ tự đúng hơn là:

```text
Language semantics
        ↓
Compiler
        ↓
Native code
        ↓
Object
        ↓
Linker
        ↓
Self-hosting
        ↓
Runtime primitives
        ↓
Core library
        ↓
Standard library
```

Nếu làm ngược, Axiom rất dễ trở thành một ngôn ngữ có thư viện đẹp nhưng compiler/backend yếu.

---

## Bước tiếp theo

Sau BOOTSTRAP-001, phần còn thiếu có ảnh hưởng trực tiếp đến toàn bộ ngôn ngữ là:

# **CORE-ABI-002 / RUNTIME-001 — Core, Runtime và Standard Library boundary**

Ở đó cần chốt chính xác một vấn đề rất quan trọng đối với mục tiêu **“native performance + binary nhỏ + không runtime bắt buộc”**:

```text
Axiom Core
    vs
Axiom Runtime
    vs
Axiom Std
    vs
OS/Platform layer
```

để quyết định **cái gì thực sự được compiler hiểu**, cái gì chỉ là thư viện Axiom, và một chương trình tối giản kiểu:

```text
fn main() {
    return 42
}
```

có thể tạo ra executable nhỏ đến mức nào mà **không kéo theo allocator, thread runtime, async runtime, exception runtime hay GC**.