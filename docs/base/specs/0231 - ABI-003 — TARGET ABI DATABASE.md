Tiếp tục. Sau `ABI-002`, ta khóa **ABI-003 — Target ABI Database & Classification Engine**. Đây là phần giúp Axiom hỗ trợ nhiều CPU/OS mà không biến compiler thành một đống `if x86 && windows ...`.

# ABI-003 — TARGET ABI DATABASE

## 1. Mục tiêu

Tách hoàn toàn 3 thứ:

```text
Axiom Type System
        ↓
Target Description
        ↓
ABI Convention
```

Ví dụ cùng:

```text
struct Vec2 {
    x: f64
    y: f64
}
```

có thể có ABI khác nhau trên:

```text
x86-64 Linux
x86-64 Windows
AArch64 Linux
AArch64 macOS
WASM
RISC-V64
```

Compiler không được viết:

```text
if (type == Vec2 && arch == X86_64) ...
```

mà phải hỏi:

```text
ABIClassifier.classify(type, target_abi)
```

---

# 2. TargetDescription

Đề xuất cấu trúc:

```text
TargetDescription {
    architecture
    vendor
    operating_system
    environment

    pointer_width
    endian

    features

    registers
    register_classes

    stack
    alignment

    calling_conventions
    object_format

    tls_model
    atomic_capabilities
    unwind_model
}
```

Ví dụ:

```text
x86_64-linux-gnu
```

về mặt compiler có thể tương ứng:

```text
architecture = x86_64
os           = linux
environment  = gnu
pointer_width = 64
endian       = little
object_format = ELF
default_abi  = SysV64
```

Còn:

```text
x86_64-windows-msvc
```

sẽ có:

```text
architecture = x86_64
os           = windows
environment  = msvc
object_format = PE/COFF
default_abi  = Win64
```

---

# 3. ABIConvention

Không nên nhét ABI vào `TargetDescription`.

Một target có thể hỗ trợ nhiều convention:

```text
ABIConvention {
    name

    integer_argument_policy
    float_argument_policy
    vector_argument_policy

    aggregate_argument_policy
    aggregate_return_policy

    stack_policy

    register_save_policy

    variadic_policy
    return_policy

    unwind_policy

    special_rules
}
```

Ví dụ một target có:

```text
AxiomNative
C
System
Fast
VectorCall
```

nếu platform hỗ trợ.

---

# 4. Register Classes

Đây là abstraction quan trọng.

Ví dụ x86-64:

```text
GPR64
GPR32
GPR16
GPR8

XMM
YMM
ZMM

FLAGS

STACK
```

AArch64:

```text
GPR
FPR
SIMD
```

RISC-V:

```text
GPR
FPR
VECTOR
```

Machine backend biết register thật.

ABI classifier chỉ cần biết:

```text
IntegerRegisterClass
FloatRegisterClass
VectorRegisterClass
```

---

# 5. Register aliases

Machine IR phải biết:

```text
RAX
EAX
AX
AL
```

là cùng physical register resource.

Tương tự:

```text
XMM0
YMM0
ZMM0
```

có quan hệ overlap.

Đây là vấn đề **Machine IR**, không nên để ABI classifier xử lý trực tiếp.

ABI chỉ yêu cầu:

```text
GPR
XMM
```

Machine backend resolve thành physical register.

---

# 6. Argument location model

Không nên dùng một enum quá đơn giản như:

```text
Register
Stack
```

Nên:

```text
ABILocation =
    Reg(class, index)
    Stack(offset)
    Indirect(pointer_location)
    Split(parts[])
    Ignore
```

Ví dụ:

```text
Pair<u64,u64>
```

có thể:

```text
Split [
    Reg(GPR, 0),
    Reg(GPR, 1)
]
```

hoặc:

```text
Stack(offset=32)
```

---

# 7. LocationPart

Để hỗ trợ aggregate phức tạp:

```text
LocationPart {
    value_offset
    value_size
    location
}
```

Ví dụ:

```text
struct S {
    a: u64
    b: f64
}
```

có thể:

```text
a → GPR0
b → FPR0
```

ABIPlan:

```text
Split [
    { offset: 0, size: 8, location: GPR0 },
    { offset: 8, size: 8, location: FPR0 }
]
```

---

# 8. Không nên dùng layout để suy ra ABI

Đây là lỗi kiến trúc cần tránh.

Hai struct có layout:

```text
16 bytes
```

không nhất thiết có cùng ABI.

Ví dụ:

```text
struct A {
    a: u64
    b: u64
}
```

và:

```text
struct B {
    a: f64
    b: f64
}
```

đều 16 bytes nhưng ABI classification có thể khác.

Vì vậy:

```text
TypeLayout != ABIClassification
```

---

# 9. TypeLayout

Ta cần một subsystem riêng:

```text
LayoutEngine
```

trả:

```text
TypeLayout {
    size
    alignment
    fields[]
    niches
    padding
    representation
}
```

ABI classifier nhận:

```text
Type
+
TypeLayout
+
TargetABI
```

---

# 10. Aggregate classification

Đề xuất interface:

```text
classify_argument(
    type,
    layout,
    abi
) -> ABIClass
```

và:

```text
classify_return(
    type,
    layout,
    abi
) -> ABIClass
```

Không nhất thiết argument và return có cùng rule.

---

# 11. Recursive aggregate classification

Ví dụ:

```text
struct Outer {
    a: u64,
    b: Vec2,
}
```

Classifier phải recursively inspect:

```text
Outer
 ├── u64
 └── Vec2
      ├── f64
      └── f64
```

sau đó quyết định:

```text
Register
Split
Memory
```

---

# 12. ABI classification không được sửa type

Ví dụ:

```text
Vec2
```

không được biến thành:

```text
Tuple<f64,f64>
```

trong type system chỉ để phục vụ ABI.

Thay vào đó:

```text
Vec2
 ↓
ABI classification
 ↓
[FPR0,FPR1]
```

Đây là lowering.

---

# 13. HFA/HVA

AArch64 có những quy tắc đặc biệt đối với homogeneous aggregates.

Ví dụ:

```text
struct Float4 {
    a: f32
    b: f32
    c: f32
    d: f32
}
```

ABI có thể phân loại thành homogeneous floating-point aggregate.

Do đó ABI database phải có concept:

```text
HomogeneousAggregate {
    element_class
    element_count
}
```

Không hard-code riêng trong AArch64 backend.

---

# 14. x86-64 SysV classification

Đối với SysV AMD64, aggregate classification phức tạp hơn chỉ:

```text
size <= 16 → registers
```

Có các class kiểu:

```text
INTEGER
SSE
SSEUP
X87
X87UP
COMPLEX_X87
MEMORY
```

Axiom nên model chúng trong ABI plugin/database:

```text
SysV64Class
```

sau đó normalize về generic:

```text
IntegerRegister
FloatRegister
VectorRegister
Memory
Split
```

---

# 15. Windows x64

Windows x64 có quy tắc khác.

Đặc biệt cần model:

```text
shadow/home space
```

và:

```text
RCX
RDX
R8
R9
XMM0-XMM3
```

theo loại argument.

Do đó:

```text
Win64ABI
```

phải tự mô tả:

```text
argument registers
shadow space
stack alignment
return rules
aggregate rules
```

Không được đưa logic này vào generic call lowering.

---

# 16. AArch64

AArch64 cần:

```text
X0-X30
V0-V31
SP
```

và ABI rules cho:

```text
integer
float
SIMD
HFA/HVA
aggregate
indirect return
```

AArch64 sẽ là target rất tốt để kiểm chứng kiến trúc ABI vì nó khác x86-64 đủ nhiều.

---

# 17. RISC-V64

RISC-V64:

```text
x0-x31
f0-f31
```

và ABI:

```text
RV64I
RV64GC
...
```

Phải để target feature quyết định availability của floating-point register class.

---

# 18. WASM

WASM là trường hợp đặc biệt.

Không có register ABI kiểu CPU.

Do đó:

```text
WASM ABI
```

có thể classification:

```text
i32
i64
f32
f64
v128
```

Aggregate phải lower thành:

```text
multiple scalar values
```

hoặc memory/linear-memory representation.

Điều này chứng minh một điểm:

> ABI abstraction không được phụ thuộc vào register machine.

---

# 19. ABI parameter modes

Ta nên có:

```text
ParamMode =
    Direct
    Indirect
    Expand
    Coerce
    Ignore
```

Ví dụ:

```text
i64
→ Direct

LargeStruct
→ Indirect

struct { f32, f32 }
→ Expand

特殊 ABI
→ Coerce
```

---

# 20. Coercion

Một ABI có thể yêu cầu:

```text
source type
→ ABI carrier type
```

Ví dụ aggregate được truyền như integer/vector.

Nhưng:

```text
ABI coercion
```

chỉ tồn tại trong ABI layer.

Không được tạo implicit source-level conversion.

---

# 21. `sret`

ABI classifier phải trả:

```text
ReturnPlan {
    mode: Direct | Indirect
    locations[]
    hidden_parameters[]
}
```

Ví dụ:

```text
LargeStruct
```

→

```text
ReturnPlan {
    mode: Indirect,
    hidden_parameters: [
        SRetPointer
    ]
}
```

Sau đó Call Lowering mới quyết định pointer nằm ở:

```text
RDI
RCX
X0
...
```

tùy ABI.

---

# 22. `sret` và parameter shifting

Ví dụ SysV conceptual:

```text
fn make(a: i64) -> Big
```

sau ABI:

```text
make(sret, a)
```

Nếu `sret` chiếm argument register:

```text
sret → RDI
a    → RSI
```

Nhưng Windows có rule khác.

Do đó:

```text
sret
```

phải được biểu diễn như hidden argument trước khi physical allocation.

---

# 23. Return location

Không nên để function return instruction tự biết:

```text
RAX
XMM0
```

Mà:

```text
ReturnPlan
    ↓
Machine Return Lowering
```

Ví dụ:

```text
ReturnPlan {
    parts: [
        { class: Integer, index: 0 }
    ]
}
```

Target backend map:

```text
Integer 0 → RAX
```

---

# 24. Call-site ABI

Callee ABI chưa đủ.

Mỗi call site cần:

```text
CallABIPlan
```

vì call có:

```text
arguments
hidden arguments
return
tail-call eligibility
variadic
unwind
clobbers
```

Ví dụ:

```text
Call {
    callee
    args
    abi_plan
}
```

---

# 25. Tail calls

ABI-003 nên định nghĩa:

```text
TailCallEligibility
```

Ví dụ:

```text
TailCall =
    Allowed
    Forbidden
    RequiresThunk
```

Tail call phụ thuộc:

- calling convention
- argument layout
- return ABI
- stack frame
- callee/caller ABI
- variadic state
- unwind
- security ABI requirements

Không thể đơn giản:

```text
call → jump
```

---

# 26. ABI thunk

Nếu hai ABI khác nhau:

```text
Axiom → C
```

có thể cần:

```text
Axiom function
      ↓
ABI thunk
      ↓
C function
```

Thunk chịu trách nhiệm:

```text
argument conversion
return conversion
register shuffle
stack adaptation
```

Không cần runtime.

---

# 27. ABI database nên là data-driven

Đây là quyết định kiến trúc quan trọng.

Không nên:

```text
compiler/backend/x86_64/calls.rs
compiler/backend/aarch64/calls.rs
```

mỗi nơi tự chứa ABI logic.

Nên:

```text
compiler/
    abi/
        generic/
        sysv64/
        win64/
        aapcs64/
        wasm/
```

và:

```text
machine/
    x86_64/
    aarch64/
    riscv64/
    wasm/
```

Phân biệt:

```text
ABI
```

với:

```text
Instruction Set
```

---

# 28. Target matrix

Ban đầu chỉ cần:

| Target | Object | ABI |
|---|---|---|
| x86-64 Linux | ELF | SysV64 |
| x86-64 Windows | PE/COFF | Win64 |
| AArch64 Linux | ELF | AAPCS64 |
| AArch64 macOS | Mach-O | Darwin/AAPCS64 |
| RISC-V64 Linux | ELF | RV64 ABI |
| WASM32 | WASM | WASM |
| WASM64 | WASM | WASM64 |

Không cần implement tất cả ngay.

Nhưng **data model phải đủ tổng quát ngay từ đầu**.

---

# 29. ABI testing

Mỗi ABI cần test độc lập:

```text
scalar_args
scalar_returns

float_args
float_returns

small_struct_args
small_struct_returns

large_struct_args
large_struct_returns

mixed_structs

nested_structs

arrays

vectors

Option

Result

view

mut_view

dyn Trait

closures

variadic

sret

tail_call
```

---

# 30. Cross-compiler ABI tests

Đây là phần cực kỳ quan trọng khi bootstrap.

Ví dụ Axiom:

```text
extern "C" fn test(a: i64, b: f64) -> i64
```

được gọi từ C:

```text
C → Axiom
```

và:

```text
Axiom → C
```

Hai chiều phải kiểm tra.

Có thể dùng compiler C hiện có làm **ABI oracle**, nhưng chỉ trong testing/bootstrap.

Không biến nó thành dependency của Axiom.

---

# 31. ABI fuzzing

Có thể tự động sinh:

```text
struct S0 { ... }
struct S1 { ... }
...
```

với combinations:

```text
i8
i32
i64
f32
f64
arrays
nested structs
enums
Option
Result
```

Sau đó sinh C declarations tương ứng và kiểm tra:

```text
Axiom result == C result
```

Đây sẽ là một trong những hệ thống fuzzing giá trị nhất của compiler.

---

# 32. ABI-003 invariants

Đóng băng:

### ABI-60
**Target Description Is Independent From Source Types**

### ABI-61
**ABI Convention Is Independent From Instruction Set**

### ABI-62
**Type Layout Is Distinct From ABI Classification**

### ABI-63
**ABI Classification Is Target-Specific**

### ABI-64
**Argument And Return Classification May Differ**

### ABI-65
**Aggregate Classification Is Recursive**

### ABI-66
**ABI Classification Does Not Modify Source Type Identity**

### ABI-67
**ABI Locations Are Abstract Before Physical Register Assignment**

### ABI-68
**Register Classes Are Target Resources**

### ABI-69
**Physical Register Names Do Not Leak Into Generic ABI**

### ABI-70
**Indirect Return Is Represented As Hidden ABI Parameter**

### ABI-71
**Hidden Parameters Participate In Normal ABI Allocation**

### ABI-72
**ABI Coercion Does Not Create Source-Level Conversion**

### ABI-73
**Call-Site ABI Is Explicitly Represented**

### ABI-74
**Tail Calls Require ABI Compatibility**

### ABI-75
**ABI Mismatch Requires Explicit Lowering/Thunk**

### ABI-76
**WASM ABI Does Not Depend On CPU Registers**

### ABI-77
**ABI Rules Are Data-Driven Where Practical**

### ABI-78
**ABI Verification Precedes Machine Lowering**

### ABI-79
**Foreign ABI Compatibility Is Tested Independently**

### ABI-80
**ABI Testing Must Include Cross-Language Calls**

---

# 33. Kiến trúc sau ABI-003

Ta hiện có:

```text
                 Typed HIR
                     │
                     ▼
                    MIR
                     │
          ┌──────────┴──────────┐
          │ Semantic Verifier   │
          └──────────┬──────────┘
                     ▼
               Verified MIR
                     │
                     ▼
                ABI Lowering
                     │
                     ▼
                  ABI MIR
                     │
              ┌──────┴──────┐
              │ ABI Engine  │
              └──────┬──────┘
                     │
          ┌──────────┴───────────┐
          │ Target ABI Database  │
          └──────────┬───────────┘
                     ▼
                  ABIPlan
                     │
                     ▼
                  Axiom LIR
                     │
                     ▼
              Target Legalization
                     │
                     ▼
                Machine IR
```

Đến đây Axiom đã có một ranh giới rất sạch:

> **Semantic compiler quyết định chương trình có ý nghĩa gì. ABI compiler quyết định giá trị đó đi qua binary interface như thế nào. Machine backend quyết định CPU thực hiện nó bằng instruction nào.**

Đây là cách tránh việc compiler về sau biến thành một khối backend khổng lồ.

---

# Bước tiếp theo: LIR-002 — CALL/RETURN/STACK MODEL

Bây giờ mới đến phần cực kỳ quan trọng tiếp theo:

**thiết kế Axiom LIR để biểu diễn ABIPlan mà chưa phụ thuộc CPU.**

Ta cần định nghĩa cụ thể các instruction như:

```text
ARG
PARAM
CALL
TAILCALL
RET
SRET
STACK_ALLOC
STACK_ADDR
LOAD
STORE
COPY
MOVE
PHI
BRANCH
```

và đặc biệt:

```text
CALL foo(...)
```

sẽ được hạ thành:

```text
ABI argument assignment
        ↓
register moves
        ↓
stack stores
        ↓
CALL
        ↓
return-value extraction
```

Đây cũng là lúc phải giải quyết một vấn đề lớn của Axiom: **làm sao giữ SSA/optimization mạnh nhưng vẫn hỗ trợ register allocator, stack frame, sret, variadic, tail-call và inline assembly mà không làm LIR trở thành LLVM clone.**