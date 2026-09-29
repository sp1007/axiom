# LIX — CODEVIEW-001: Debug IR + CodeView Object Debug Records

Ta tiếp tục theo đúng chuỗi. Mục tiêu của bước này **chưa phải viết PDB linker**, mà xây một lớp Debug IR độc lập để sau này Axiom có thể phát sinh:

```text
Axiom Debug IR
 ├── CodeView / PDB       ← Windows
 ├── DWARF / ELF         ← Linux
 └── future debug format
```

Điểm quan trọng nhất: **debug information không được trở thành một phần của semantic compiler**. Nó chỉ là ánh xạ từ semantic/source entities sang machine entities.

---

# 1. Kiến trúc mới

Pipeline:

```text
Source
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
Optimization
  ↓
LIR
  ↓
Machine IR
  ├──────────────→ Debug IR
  ↓
Register Allocation
  ↓
Frame Layout
  ↓
Machine Code
  ↓
COFF
  ├── .text
  ├── .rdata
  ├── .data
  ├── .pdata
  ├── .xdata
  └── debug$S/debug$T
```

Debug IR nên được tạo **song song với lowering**, không phải sau khi compiler đã quên source information.

---

# 2. Nguyên tắc

Axiom debug phải trả lời được:

> Machine instruction này bắt nguồn từ source nào?

và:

> Khi debugger dừng tại đây, local variable nào đang tồn tại và nằm ở đâu?

Không được yêu cầu optimizer giữ nguyên source structure.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    let c = a + b
    c
}
```

Optimizer có thể biến toàn bộ thành:

```asm
lea eax,[rcx+rdx]
ret
```

Debug vẫn phải có khả năng nói:

```text
EAX ← c
```

nếu `c` còn tồn tại về mặt debug semantics.

---

# 3. Debug information không ảnh hưởng semantics

Invariant:

```text
DEBUG-20
Removing all debug information must not change program semantics.
```

Do đó:

```text
-O0
-O2
-O3
```

có thể có debug fidelity khác nhau nhưng không được thay đổi chương trình.

---

# 4. Source identity

Thêm:

```text
DebugFileId
DebugFunctionId
DebugScopeId
DebugVariableId
DebugTypeId
```

Không dùng:

```text
String filename
String function_name
```

làm identity.

Tên chỉ là metadata.

---

# 5. Source location

```text
SourceLocation {
    file: DebugFileId
    line: u32
    column: u32
}
```

và:

```text
SourceRange {
    start: SourceLocation
    end: SourceLocation
}
```

---

# 6. Span → Debug Location

Compiler đã có:

```text
Span {
    source_file
    start
    end
}
```

Debug layer chuyển:

```text
Span
 ↓
SourceLocation
```

Không duplicate source database.

---

# 7. Machine location

Một local có thể nằm ở:

```text
Register
Stack
Memory
Constant
Undefined
OptimizedOut
```

Model:

```text
DebugLocation =
    RegisterLocation
    StackLocation
    MemoryLocation
    ConstantLocation
    CompositeLocation
    UndefinedLocation
```

---

# 8. Register location

Ví dụ:

```text
a → RCX
```

thì:

```text
DebugRegisterLocation {
    register: DebugRegister
}
```

Không để debug layer phụ thuộc trực tiếp vào internal `PhysRegId`.

Cần mapping:

```text
Axiom PhysReg
      ↓
CodeView Register
```

---

# 9. Stack location

Ví dụ:

```text
a → [RSP + 40]
```

Debug representation:

```text
DebugStackLocation {
    base: DebugRegister
    offset: i32
}
```

Nhưng cần thêm **frame state**.

Vì offset có thể thay đổi giữa:

```text
prologue
body
epilogue
```

---

# 10. Location list

Một biến không nhất thiết ở một nơi.

Ví dụ:

```text
a
 ├── RCX
 ├── [RSP+48]
 └── optimized out
```

Do đó:

```text
DebugLocationRange {
    start: MachineOffset
    end: MachineOffset
    location: DebugLocation
}
```

và:

```text
DebugVariable {
    locations[]
}
```

Đây là abstraction rất quan trọng cho `-O2`.

---

# 11. Constant variable

```axiom id="j5q1k8"
let x = 42
```

nếu optimizer giữ được giá trị:

```text
DebugConstantLocation {
    value = 42
}
```

Debugger có thể hiển thị:

```text
x = 42
```

mà không cần tồn tại memory/register thực tế.

---

# 12. Optimized-out

Nếu không thể xác định giá trị:

```text
DebugLocation = OptimizedOut
```

Debugger nên hiển thị:

```text
x = <optimized out>
```

Không được bịa giá trị.

---

# 13. Debug scope

Ví dụ:

```axiom id="5efc41"
fn foo() {
    let a = 1

    {
        let b = 2
        ...
    }
}
```

có:

```text
FunctionScope
 └── BlockScope
      └── NestedScope
```

Representation:

```text
DebugScope {
    parent
    source_range
    children[]
}
```

---

# 14. Lexical scope ≠ lifetime

Đây là điểm đặc biệt quan trọng với Axiom.

Compiler đã quyết định:

> lifetime semantic có thể ngắn hơn lexical scope.

Vì vậy:

```text
DebugScope
```

và:

```text
OwnershipLifetime
```

**không được dùng chung**.

Debugger có thể thấy:

```text
x
```

trong source scope nhưng compiler đã release resource trước đó.

Khi đó debug variable phải phản ánh trạng thái thực tế.

---

# 15. Debug variable

```text
DebugVariable {
    id
    name
    type
    scope
    declaration_location
    locations[]
    flags
}
```

Flags:

```text
Parameter
Local
Global
Constant
Artificial
Optimized
```

---

# 16. Debug type

Không serialize trực tiếp Typed HIR.

Tạo:

```text
DebugType {
    id
    kind
    name
    size
    alignment
    fields[]
}
```

Kinds:

```text
Primitive
Struct
Enum
Tuple
Array
Pointer
View
Function
GenericInstance
Alias
```

---

# 17. Type identity

Debug type identity:

```text
DebugTypeId
```

phải stable trong một compilation unit.

Nhưng không cần trở thành language type identity.

Ví dụ:

```text
i32
```

có:

```text
TypeId = 17
DebugTypeId = 4
```

---

# 18. Struct debug type

```axiom id="1t6xsp"
struct Vec2 {
    x: f32
    y: f32
}
```

Debug:

```text
DebugStruct {
    name = "Vec2"

    fields = [
        {
            name = "x"
            type = f32
            offset = ...
        },
        {
            name = "y"
            type = f32
            offset = ...
        }
    ]
}
```

Nhưng `offset` phải lấy từ **final layout**, không lấy từ source order.

---

# 19. Compiler-controlled layout

Nếu Axiom compiler reorder/pack/optimize layout:

```text
source:
a
b
c
```

nhưng machine layout:

```text
b
a
c
```

debug info phải phản ánh machine layout thực tế.

Do đó:

```text
DebugType
```

được finalize sau layout computation.

---

# 20. Enum debug

Ví dụ:

```axiom id="z8x3mp"
enum Message {
    Quit,
    Move { x:i32, y:i32 }
}
```

Debug cần:

```text
DebugEnum {
    variants[]
}
```

với:

```text
variant
discriminant
fields
field offsets
```

Niche optimization có thể khiến representation không giống source enum.

Debugger vẫn phải hiểu semantic enum.

---

# 21. Generic type

Ví dụ:

```axiom id="6a4b7f"
Vec<i32>
Vec<f64>
```

Debug type identity phải phân biệt:

```text
Vec<i32>
Vec<f64>
```

không thể chỉ dùng tên:

```text
Vec
```

---

# 22. Monomorphization

Sau monomorphization:

```text
Vec<T>
```

→

```text
Vec<i32>
Vec<f64>
```

Debug IR nên tham chiếu concrete type.

Generic source metadata có thể được giữ thêm cho debugger nâng cao sau này.

---

# 23. Function debug record

```text
DebugFunction {
    id
    name
    linkage_name
    source_range
    type
    scope
    parameters[]
    locals[]
    machine_ranges[]
}
```

`linkage_name` khác source name.

Ví dụ:

```text
source:
foo

linker:
_Z... // nếu Axiom sau này name-mangle
```

Hiện tại Axiom có thể dùng deterministic mangling riêng.

---

# 24. Name mangling

Không dùng C++ mangling.

Axiom cần:

```text
AxiomMangle
```

Ví dụ conceptually:

```text
_ax_fn_foo_i32_i32
```

Nhưng **đừng freeze format này ngay**.

Chỉ cần:

```text
MangledName
```

là compiler-internal abstraction.

Format sẽ được freeze ở ABI/name-mangling milestone.

---

# 25. Inline functions

Optimizer có thể inline:

```text
foo()
```

vào:

```text
bar()
```

Debugger vẫn cần biết:

```text
currently executing:
bar
  inlined foo
```

Do đó:

```text
DebugInlineSite {
    function
    call_site
    parent_inline_site
}
```

---

# 26. Inline tree

Ví dụ:

```text
main
 └── foo
      └── add
```

Debug IR:

```text
InlineScope(main)
 └── InlineScope(foo)
      └── InlineScope(add)
```

Machine instruction có thể reference:

```text
InlineScopeId
```

---

# 27. Machine instruction mapping

Thêm vào Machine IR:

```text
DebugAttachment {
    source_span
    scope
    inline_site
}
```

Ví dụ:

```text
ADD RAX,RDX
```

có:

```text
source_span = line 7 col 10..15
scope = foo
```

---

# 28. Không attach debug info vào mọi machine instruction bắt buộc

Optimizer có thể:

```text
3 instructions
 ↓
1 instruction
```

Không cần preserve 1:1.

Rule:

```text
DEBUG-21
A machine instruction may represent multiple source operations.
```

và:

```text
DEBUG-22
Multiple machine instructions may represent one source operation.
```

---

# 29. Instruction ranges

Debug line table:

```text
DebugLineEntry {
    machine_start
    machine_end
    source_location
}
```

Sau final layout mới biết absolute section offset.

---

# 30. Line table

Ví dụ:

```text
.text+0x00 → line 1
.text+0x05 → line 2
.text+0x08 → line 3
```

Đây là cơ sở để debugger step:

```text
step over
step into
step out
```

---

# 31. Column information

Axiom có thể giữ:

```text
line
column
```

nhưng CodeView line tables có representation riêng.

Debug IR không nên bị giới hạn bởi CodeView.

---

# 32. Debug IR độc lập format

Repository:

```text
compiler/debug/
├── id.ax
├── source.ax
├── location.ax
├── scope.ax
├── variable.ax
├── type.ax
├── function.ax
├── inline.ax
├── line.ax
├── module.ax
├── builder.ax
├── finalize.ax
├── verifier.ax
└── tests/
```

Sau đó:

```text
compiler/debug/codeview/
compiler/debug/dwarf/
```

---

# 33. CodeView layer

CodeView writer nhận:

```text
DebugModule
```

và chuyển thành:

```text
CodeViewObjectDebug {
    symbols
    types
    line_tables
}
```

Không cho CodeView layer truy cập AST/HIR trực tiếp.

---

# 34. COFF debug sections

Windows COFF object có thể mang các section debug như:

```text
.debug$S
.debug$T
```

Axiom writer nên coi chúng là:

```text
SemanticSectionKind::DebugSymbols
SemanticSectionKind::DebugTypes
```

rồi mapping sang CodeView-specific section names.

---

# 35. Không để linker hiểu CodeView quá nhiều

PE linker nên chỉ cần:

```text
COFF section
symbol
relocation
debug contribution
```

Còn:

```text
CodeView records
```

được xử lý bởi PDB/debug linker layer.

---

# 36. PDB architecture

Pipeline dự kiến:

```text
Object Files
 ├── .text
 ├── .pdata
 ├── .xdata
 ├── .debug$S
 └── .debug$T
          ↓
     Axiom Debug Linker
          ↓
        PDB
```

Không nhét PDB writer vào PE linker core.

---

# 37. Debug linker

Repository sau này:

```text
compiler/debug/link/
├── contribution.ax
├── symbol_merge.ax
├── type_merge.ax
├── line_merge.ax
└── pdb.ax
```

---

# 38. Type merging

Nhiều object có:

```text
struct Vec2
```

không được tạo hàng trăm debug type duplicate.

Cần:

```text
DebugTypeKey
```

dựa trên semantic identity:

```text
package
module
type identity
generic arguments
representation
```

---

# 39. Debug type ODR-like identity

Không dùng source name đơn độc.

Hai package có:

```text
math::Vec2
graphics::Vec2
```

phải khác nhau.

---

# 40. Local variable location tracking

Đây sẽ là một trong những phần khó nhất của optimizer.

Ví dụ:

```text
let x = a + b
let y = x * 2
```

Optimizer:

```text
x never materialized
```

Debug:

```text
x = <optimized out>
```

hoặc có thể:

```text
x = DWARF/CodeView expression:
RCX + RDX
```

Sau này có thể hỗ trợ **debug value expressions**.

MVP chưa cần expression evaluator phức tạp.

---

# 41. Debug value expression

Thiết kế sẵn:

```text
DebugValueExpr =
    Const
    Register
    Stack
    Add
    Sub
    Deref
    ExtractBits
    Composite
```

Nhưng CodeView backend có thể chỉ support subset.

---

# 42. Debug info levels

Axiom nên có:

```text
-g0
-g1
-g2
-g3
```

Concept:

```text
-g0
    no debug info

-g1
    line tables

-g2
    functions + types + locals

-g3
    maximum source/debug fidelity
```

Không cần freeze exact flags ngay.

---

# 43. Debug optimization policy

Có:

```text
-O2 -g
```

thì optimizer **không được tắt optimization** chỉ vì debug.

Thay vào đó:

```text
debug fidelity < -O0
```

là chấp nhận được.

Đây là hành vi cần thiết cho production debugging.

---

# 44. Debug verifier

Thêm:

```text
AX_DBG_0001
invalid source location

AX_DBG_0002
invalid machine range

AX_DBG_0003
invalid debug scope

AX_DBG_0004
invalid variable location

AX_DBG_0005
unknown debug type

AX_DBG_0006
invalid inline scope

AX_DBG_0007
debug location overlaps inconsistently

AX_DBG_0008
debug register unavailable

AX_DBG_0009
debug range outside function

AX_DBG_0010
debug information references removed machine entity
```

---

# 45. Debug identity không được ảnh hưởng cache semantics

Build cache:

```text
-O2
```

và:

```text
-O2 -g
```

có thể tạo artifacts khác nhau.

Nhưng semantic cache:

```text
Typed HIR
MIR
Verified MIR
```

không được phụ thuộc vào việc debugger có bật hay không nếu debug metadata không làm thay đổi semantic compilation.

---

# 46. Debug build key

Artifact key thêm:

```text
DebugConfig
```

ở những stage thực sự chứa debug info:

```text
Machine IR + Debug
COFF
PDB
```

Không cần làm:

```text
TypeCheckKey += debug flag
```

---

# 47. Source-to-machine mapping sau register allocation

Đây là điểm rất quan trọng.

Location trước allocation:

```text
x → %v17
```

sau allocation:

```text
x → RBX
```

sau spill:

```text
x → [RSP+48]
```

Do đó debug finalization phải chạy:

```text
sau allocation
sau frame layout
sau spill/reload
```

---

# 48. Debug location pipeline

```text
Source Variable
      ↓
Debug Value
      ↓
Virtual Register / SSA Value
      ↓
Register Allocation
      ↓
Physical Register / Stack
      ↓
Frame Layout
      ↓
Final Debug Location
```

---

# 49. Spill/reload

Nếu:

```text
x → RBX
```

nhưng register pressure làm spill:

```text
x
 ↓
[RSP+80]
```

Debug info phải thay đổi location range.

Ví dụ:

```text
0x10..0x30 → RBX
0x30..0x50 → [RSP+80]
0x50..0x60 → RBX
```

---

# 50. Đây là lý do không thể viết CodeView writer quá sớm

Nếu viết:

```text
MachineInstr → CodeView
```

trước register allocation, debug local variables sẽ sai trong optimized builds.

Kiến trúc đúng:

```text
Debug IR
   ↓
Debug Finalizer
   ↓
CodeView
```

---

# 51. Acceptance test

Source:

```axiom id="b1d5p9"
fn add(a: i32, b: i32) -> i32 {
    let c = a + b
    c
}
```

Compiler:

```text
-O0 -g
```

Expected debugger:

```text
a = ...
b = ...
c = ...
```

---

# 52. Optimized acceptance

```text
-O2 -g
```

Có thể:

```text
a = ...
b = ...
c = <optimized out>
```

hoặc debugger reconstruct được `c`.

**Cả hai đều hợp lệ**, miễn debug info không báo sai.

---

# 53. Breakpoint test

```text
break add
run
```

Debugger phải dừng ở:

```text
source: add.ax
line: fn add(...)
```

không phải:

```text
unknown source
```

---

# 54. Step test

```text
step
```

phải di chuyển theo source line hợp lý.

Không cần từng expression nhỏ ở MVP.

---

# 55. Inline test

```text
-O2 -g
```

nếu:

```text
add()
```

được inline vào `main`.

Debugger phải có khả năng biểu diễn:

```text
main
  inlined add
```

ngay cả khi không có machine-level `CALL add`.

---

# 56. Symbol test

PE phải có:

```text
main
__axiom_start
```

và PDB mapping:

```text
source function
↔ mangled symbol
↔ machine range
```

---

# 57. Debug output separation

MVP build:

```text
axiom build hello.ax
```

→

```text
hello.exe
```

không cần PDB.

Debug build:

```text
axiom build hello.ax --debug
```

→

```text
hello.exe
hello.pdb
```

Executable vẫn chạy độc lập.

---

# 58. No debugger runtime dependency

Axiom application:

```text
hello.exe
```

không link:

```text
axiom_debug_runtime.dll
```

Debug metadata chỉ nằm ngoài executable/PDB hoặc debug sections.

---

# 59. Invariants

```text
ADBG-20
Debug information cannot alter program semantics.

ADBG-21
Debug source identity is distinct from semantic TypeId.

ADBG-22
Debug scopes are distinct from ownership/resource lifetimes.

ADBG-23
Machine locations are represented independently of debug format.

ADBG-24
Variable locations may change over machine instruction ranges.

ADBG-25
Optimized-out variables are represented explicitly.

ADBG-26
Debug types use semantic type identity, not display names alone.

ADBG-27
Final variable locations are resolved after register allocation and frame layout.

ADBG-28
Debug ranges cannot reference removed machine instructions.

ADBG-29
Inline call stacks are represented independently of CodeView.

ADBG-30
Debug IR is target-format independent.

ADBG-31
CodeView is an output format, not the compiler's internal debug model.

ADBG-32
DWARF can be implemented without changing semantic compiler stages.

ADBG-33
Debug configuration affects only artifacts that contain debug information.

ADBG-34
Debug generation is deterministic.

ADBG-35
Debug information may be incomplete under aggressive optimization but must not be incorrect.

ADBG-36
No debug runtime is required for native execution.
```

---

# 60. Repository sau milestone

```text
compiler/
├── debug/
│   ├── id.ax
│   ├── source.ax
│   ├── location.ax
│   ├── scope.ax
│   ├── variable.ax
│   ├── type.ax
│   ├── function.ax
│   ├── inline.ax
│   ├── line.ax
│   ├── module.ax
│   ├── builder.ax
│   ├── finalize.ax
│   ├── verifier.ax
│   │
│   ├── codeview/
│   │   ├── symbols.ax
│   │   ├── types.ax
│   │   ├── lines.ax
│   │   ├── records.ax
│   │   └── writer.ax
│   │
│   └── dwarf/
│       └── ...
```

---

# 61. Một điểm cần khóa ngay: Debug IR không được giữ pointer tới AST

Sai:

```text
DebugVariable {
    ast_node: &ASTNode
}
```

Điều này phá:

- incremental compilation
- serialization
- parallel compilation
- cache
- self-hosting

Đúng:

```text
DebugVariable {
    source_span: SpanId
    semantic_type: TypeId
}
```

Sau đó Debug Builder snapshot thông tin cần thiết.

---

# 62. Debug IR phải serializable

Đây là một lợi thế lớn cho Axiom.

Có thể cache:

```text
Typed HIR
MIR
Machine IR
Debug IR
```

và PDB generation có thể chạy riêng.

Về sau:

```text
axiom debug-link
```

có thể tạo PDB từ object files mà không cần recompile source.

---

# 63. Điều này dẫn tới kiến trúc PDB rất sạch

```text
                 ┌── COFF linker
                 │
COFF objects ────┤
                 │
                 └── Debug linker
                         ↓
                       PDB
```

PE linker không cần biết source AST.

---

# 64. Milestone tiếp theo: `PDB-001`

Sau CODEVIEW-001, bước kế tiếp là:

```text
PDB-001
Axiom PDB Writer
```

Nhưng trước khi viết toàn bộ PDB, ta cần hoàn thành **CodeView record model** đủ cho:

- public symbols
- functions
- locals
- types
- line tables
- inline scopes
- source files

Sau đó mới build MSF/PDB container.

Pipeline sẽ thành:

```text
Debug IR
   ↓
CodeView
   ↓
COFF .debug$S/.debug$T
   ↓
Debug Linker
   ↓
MSF/PDB
   ↓
hello.pdb
```

Và sau PDB, ta sẽ chuyển sang **ELF64/Linux**, dùng chính Debug IR này để xây DWARF thay vì thiết kế lại debug architecture.