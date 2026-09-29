# BOOTSTRAP-008 — FUNCTIONS + ABI EXECUTION MODEL

BOOT-007 đã chốt **Value / Place / CFG / evaluation / assignment**. Bước này chốt cách một function Axiom thực sự đi qua compiler và trở thành một lời gọi native.

Mục tiêu:

> **Function semantics hoàn toàn độc lập với calling convention. ABI chỉ là phép biến đổi representation sau MIR.**

Pipeline:

```text
Axiom source
    ↓
Typed HIR
    ↓
MIR
    ↓
verified MIR
    ↓
ABI classification
    ↓
LIR
    ↓
Machine IR
    ↓
register allocation
    ↓
machine code
```

---

# 1. Function trong Axiom

Function là primitive behavior chính:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

Semantic function:

```text
Function {
    id
    name
    parameters[]
    return_type
    body
    calling_convention
    visibility
}
```

Không có object:

```text
this
vtable
object header
```

trong function bình thường.

---

# 2. Function type

Function type:

```text
fn(i32, i32) -> i32
```

là một type thực.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

var f = add;
```

`f` có thể mang function value.

Ở backend, một non-capturing function value có thể là:

```text
function pointer
```

nhưng đó là representation.

---

# 3. Function declaration và definition

Axiom cho phép declaration trước definition.

Ví dụ:

```axiom
fn main() -> i32 {
    return add(20, 22);
}

fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

Resolver phải collect declarations trước khi resolve body.

Đã phù hợp với COMPILER-002.

---

# 4. Không overload function v1

Không cho:

```axiom
fn foo(x: i32) {}
fn foo(x: i64) {}
```

trong cùng namespace.

Lý do:

- name resolution đơn giản
- ABI symbol ổn định
- diagnostics rõ
- compiler AI-friendly
- tránh overload resolution phức tạp

Generic function thay thế phần lớn nhu cầu:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

---

# 5. Parameter là semantic ownership boundary

Ví dụ:

```axiom
fn consume(x: Buffer)
```

`x` là owning parameter.

Call:

```axiom
consume(a);
```

→ ownership chuyển:

```text
a ──MOVE──> parameter x
```

Sau call:

```text
a = Moved
```

---

# 6. Copy parameter

```axiom
fn square(x: i32) -> i32
```

Call:

```axiom
square(a);
```

với `i32: Copy`:

```text
COPY a → argument
```

Không invalidate `a`.

---

# 7. View parameter

```axiom
fn print(x: view<String>)
```

Call:

```axiom
print(s);
```

Compiler tạo ephemeral read capability:

```text
s
 │
 └──→ view
       │
       └──→ call
```

Capability chỉ sống đủ cho call.

Không có hidden allocation.

---

# 8. Mutable view parameter

```axiom
fn clear(x: mut_view<Buffer>)
```

Call:

```axiom
clear(buffer);
```

Compiler tạo:

```text
WRITE capability
```

và trong thời gian call:

```text
buffer
    │
    └── exclusive WRITE
```

Các read/write conflict khác bị verifier chặn.

---

# 9. Function return

Ví dụ:

```axiom
fn make() -> Buffer {
    var b = Buffer();
    return b;
}
```

Semantic:

```text
b
 ↓
MOVE
 ↓
return value
```

Không có:

```text
COPY
```

nếu `Buffer` không Copy.

---

# 10. Return không đồng nghĩa heap

Điểm này cần đóng băng mạnh.

```axiom
fn make_point() -> Point {
    return Point { x: 20, y: 22 };
}
```

không có nghĩa:

```text
heap allocate Point
```

Compiler có thể:

```text
caller allocates return storage
```

hoặc:

```text
register return
```

hoặc:

```text
multiple registers
```

hoặc:

```text
hidden sret
```

tùy ABI/layout.

---

# 11. MIR function call

Ví dụ:

```axiom
fn main() -> i32 {
    return add(20, 22);
}
```

MIR:

```text
bb0:
    %0 = const i32 20
    %1 = const i32 22

    %2 = call FunctionId(add)(%0, %1)

    return %2
```

MIR **không biết**:

```text
RDI
RSI
RAX
stack
```

---

# 12. ABI lowering

Sau MIR:

```text
CALL add(%0, %1)
```

ABI classifier quyết định:

```text
arg0 → GPR
arg1 → GPR
return → GPR
```

trên target cụ thể.

LIR có thể trở thành:

```text
ABI_ARG %0 → vreg0
ABI_ARG %1 → vreg1
CALL add
ABI_RESULT → vreg2
```

Sau register allocation mới:

```asm
mov edi, 20
mov esi, 22
call add
```

Ví dụ trên chỉ minh họa; **không hard-code System V vào MIR**.

---

# 13. Calling convention

Function mặc định:

```text
Axiom ABI
```

Nhưng ABI lowering phải hỗ trợ:

```text
Axiom
C
system
fastcall / platform-specific
extern ABI
```

Ví dụ:

```axiom
extern "C" fn c_function(x: i32) -> i32;
```

Function type phải mang calling-convention information khi cần.

---

# 14. Internal ABI vs external ABI

Đây là điểm rất quan trọng cho hiệu năng.

Function private:

```axiom
fn helper(...)
```

có thể được compiler dùng internal ABI tối ưu.

Ví dụ compiler có thể:

```text
split aggregate
scalarize argument
eliminate unused parameter
specialize
inline
```

Nhưng:

```axiom
pub extern "C" fn api(...)
```

phải giữ ABI contract.

Do đó:

```text
private/internal
    → optimized ABI

extern/public ABI boundary
    → frozen ABI contract
```

---

# 15. Symbol name

Function:

```axiom
fn add(a: i32, b: i32) -> i32
```

không nhất thiết symbol là:

```text
add
```

Axiom ABI có thể mangled:

```text
_ZN3foo3add...
```

hoặc một scheme riêng.

Nhưng:

```axiom
@export("add")
fn add(...)
```

thì symbol external phải là:

```text
add
```

Không được để linker tự đoán.

---

# 16. `pub` không đồng nghĩa exported symbol

```axiom
pub fn foo() {}
```

chỉ nói:

```text
source-level visibility
```

Không nhất thiết tạo external linker symbol.

Muốn ABI/export boundary:

```axiom
@export("foo")
pub extern "C" fn foo() {}
```

Đây giúp compiler dead-strip được symbol nội bộ.

---

# 17. Recursive function

Ví dụ:

```axiom
fn factorial(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }

    return n * factorial(n - 1);
}
```

MIR:

```text
bb0:
    %c = cmp n, 1
    cond_br %c, bb1, bb2

bb1:
    %one = const 1
    return %one

bb2:
    %one = const 1
    %next = sub n, %one
    %r = call factorial(%next)
    %result = mul n, %r
    return %result
```

Không cần compiler special-case recursion.

---

# 18. Tail call

Ví dụ:

```axiom
fn f(x: i32) -> i32 {
    return g(x);
}
```

Semantic MIR vẫn:

```text
CALL g
RETURN result
```

Optimization/ABI phase có thể nhận ra:

```text
tail-call eligible
```

và biến thành:

```text
TAILCALL g
```

Không nên đưa `TAILCALL` vào source semantics mặc định.

---

# 19. Stack frame không thuộc function semantics

Function:

```axiom
fn add(a: i32, b: i32) -> i32
```

có thể cuối cùng:

```asm
add:
    lea eax, [rdi+rsi]
    ret
```

Không có stack frame.

Không được mặc định:

```text
push rbp
mov rbp, rsp
```

Axiom compiler phải cho phép **zero-frame function**.

---

# 20. Local variable không phải stack variable

```axiom
fn f() -> i32 {
    let x = 42;
    return x;
}
```

`x` có thể:

```text
register
```

Không cần:

```text
stack slot
```

Nếu:

```axiom
unsafe {
    // address observable
}
```

hoặc ABI/storage contract yêu cầu address thì compiler mới phải materialize storage thích hợp.

---

# 21. Address-taking

Core không có reference syntax `&x`.

Raw pointer:

```axiom
let p = unsafe { raw_address(x) };
```

hoặc API system tương ứng.

Điểm quan trọng:

> **Lấy địa chỉ là hành động làm storage identity trở nên observable.**

Sau đó optimizer bị ràng buộc bởi:

```text
AMEM-55
AMEM-70
```

---

# 22. Function pointer

Function pointer không capture state:

```text
fn(i32) -> i32
```

có thể trỏ tới:

```axiom
fn square(x: i32) -> i32 {
    return x * x;
}
```

Call:

```axiom
f(10)
```

MIR:

```text
CALL_INDIRECT f(%10)
```

Đây khác:

```text
CALL square
```

---

# 23. Dynamic function call không được tự động inline

Nếu function pointer không thể resolve:

```text
CALL_INDIRECT
```

optimizer có thể devirtualize nếu chứng minh target duy nhất.

Nhưng không được giả định.

---

# 24. Closure chưa xử lý ở BOOT-008

Closure sẽ dùng cùng function model:

```text
code pointer
+
environment
```

nhưng thuộc BOOT-025/COMPILER-006.

Điều quan trọng là ABI model hiện tại phải đủ để sau này biểu diễn:

```text
CALL closure(code, environment, args...)
```

mà không sửa MIR architecture.

---

# 25. Aggregate argument

Ví dụ:

```axiom
struct Point {
    x: i32,
    y: i32
}

fn sum(p: Point) -> i32 {
    return p.x + p.y;
}
```

MIR:

```text
CALL sum(%p)
```

Không nói:

```text
pass via stack
```

ABI classifier sau này quyết định.

---

# 26. Aggregate return

```axiom
fn make() -> Point {
    return Point { x: 20, y: 22 };
}
```

Có thể:

```text
return registers
```

hoặc:

```text
hidden sret
```

hoặc:

```text
mixed register + memory
```

Tùy target ABI.

---

# 27. `sret`

LIR có:

```text
SRET
```

Ví dụ semantic:

```text
make() -> Point
```

ABI có thể lower thành:

```text
make(Point* return_storage)
```

nhưng đây là **ABI transformation**, không phải Axiom source semantics.

---

# 28. Caller-allocated return

Compiler nên ưu tiên:

```text
caller owns destination
```

khi aggregate return cần storage.

Ví dụ:

```axiom
var p = make_point();
```

có thể hạ thành:

```text
caller storage for p
        ↓
make_point(&p_storage)
```

Nhưng pointer chỉ tồn tại trong ABI representation.

Không có nghĩa source language có hidden reference semantics.

---

# 29. Parameter evaluation order

Vẫn giữ:

```text
left → right
```

Ví dụ:

```axiom
f(a(), b(), c());
```

phải:

```text
a()
b()
c()
CALL f
```

ABI lowering không được làm:

```text
b()
a()
c()
```

nếu có observable effect.

Optimizer chỉ được reorder khi semantics preserved.

---

# 30. Call cleanup

Ví dụ:

```axiom
fn f() {
    consume(make_resource());
}
```

Nếu temporary được tạo:

```text
evaluate
→ transfer ownership to parameter
```

thì sau call **caller không drop lại object đã transferred**.

Đây là chỗ cực dễ tạo double-drop.

MIR ownership state phải thể hiện:

```text
temporary
    ↓ MOVE
callee parameter
    ↓
callee owns
```

---

# 31. Panic trong callee

```axiom
fn f() -> i32 {
    panic();
}
```

MIR:

```text
CALL panic
UNREACHABLE
```

Caller không nhận một ordinary `i32`.

Không cần exception object.

Nếu panic=abort:

```text
process terminates
```

Nếu panic=unwind:

```text
unwind runtime
```

được thêm sau.

---

# 32. `Result` không phải ABI exception

```axiom
fn f() -> Result<i32, Error>
```

vẫn chỉ là ordinary return value.

`?`:

```axiom
let x = f()?;
```

hạ thành CFG:

```text
call f
switch result

Ok(x)
    ↓ continue

Err(e)
    ↓ cleanup
    ↓ return Err(e)
```

Không có hidden unwind.

---

# 33. Variadic functions

Axiom source:

```axiom
extern "C" fn printf(fmt: *const u8, ...);
```

chỉ ở FFI/system layer.

MIR call phải biết:

```text
variadic = true
calling_convention = C
```

ABI lowering chịu trách nhiệm:

- register classification
- varargs save area
- stack arguments
- platform rules

Không đưa variadic complexity vào ordinary Axiom functions.

---

# 34. Function ABI descriptor

Chốt internal representation:

```text
FunctionABI {
    calling_convention
    params[]
    return_info
    varargs
    unwind_mode
    visibility
    linkage
}
```

Mỗi parameter:

```text
ABIParam {
    source_type
    layout
    passing_mode
}
```

Passing mode:

```text
Direct
Indirect
Split
Ignore
Expand
Coerce
```

---

# 35. ABI classification

Ví dụ:

```text
i32
```

→ Direct.

```text
Point { i32, i32 }
```

→ có thể Direct/Split/Indirect.

```text
large struct
```

→ thường Indirect.

```text
unit
```

→ Ignore.

```text
never
```

→ no return.

Nhưng đây là **target-specific ABI policy**, không phải universal rule.

---

# 36. Function declaration ABI boundary

Compiler nên có:

```text
Source Function
      ↓
Semantic Function
      ↓
ABI Function
      ↓
LIR Function
      ↓
Machine Function
```

Không nên mutate source function object thành ABI-lowered object.

Lý do:

```text
MIR inspection
```

phải vẫn cho programmer thấy:

```text
fn make() -> Point
```

chứ không:

```text
fn make(Point* sret) -> void
```

---

# 37. LIR call model

LIR:

```text
CALL {
    target
    calling_convention
    args
    results
    memory_effect
    unwind
}
```

ABI args được explicit:

```text
ABI_ARG
ABI_RESULT
SRET
```

Nhưng LIR vẫn chưa biết physical register.

---

# 38. Call clobber

Machine backend biết:

```text
caller_saved
callee_saved
```

Ví dụ function call có thể phá:

```text
v0
v1
v2
```

Register allocator phải spill/live-range split nếu cần.

Đây là lý do register allocation không thể bỏ qua call.

---

# 39. Function attributes

BOOT-008 chỉ cần một số semantic attributes:

```text
@entry
@export
@inline
@noinline
@cold
```

Nhưng:

```text
@inline
```

chỉ là optimization hint.

Không phải correctness guarantee.

`@noinline` cũng tương tự.

Không cho source programmer điều khiển register allocation.

---

# 40. Entry point

Chốt lại:

```text
fn main() -> i32
```

là semantic program entry của hosted Axiom program.

Platform startup:

```text
_start
WinMain / entry
Darwin startup
Android entry
...
```

là linker/runtime/startup concern.

Ví dụ Linux freestanding:

```text
_start
    ↓
axiom_main
    ↓
sys_exit(return_code)
```

Không cần libc.

Nhưng compiler không biến `main` thành `_start` trong semantic MIR.

---

# 41. First complete multi-function program

Sau BOOT-008:

```axiom
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn twice(x: i32) -> i32 {
    return add(x, x);
}

fn main() -> i32 {
    return twice(21);
}
```

Expected:

```text
exit code = 42
```

Pipeline:

```text
add
 ↓
twice
 ↓
main
 ↓
ELF
 ↓
Axiom linker
 ↓
native executable
```

---

# 42. Recursion test

```axiom
fn factorial(n: i32) -> i32 {
    if n <= 1 {
        return 1;
    }

    return n * factorial(n - 1);
}

fn main() -> i32 {
    return factorial(5);
}
```

Expected:

```text
120
```

Test này đồng thời kiểm tra:

- function symbols
- call
- return
- stack frame
- recursion
- ABI
- CFG
- comparison
- branch
- arithmetic

---

# 43. Mutual recursion

Nên có test:

```axiom
fn even(x: i32) -> bool {
    if x == 0 {
        return true;
    }
    return odd(x - 1);
}

fn odd(x: i32) -> bool {
    if x == 0 {
        return false;
    }
    return even(x - 1);
}
```

Để kiểm tra resolver không phụ thuộc declaration order.

---

# 44. ABI test suite

Harness nên thêm:

```text
tests/abi/
├── scalar_args/
├── scalar_returns/
├── aggregate_args/
├── aggregate_returns/
├── nested_calls/
├── recursion/
├── extern_c/
├── function_pointer/
└── varargs/
```

Stage-0 chỉ cần:

```text
scalar
aggregate
recursion
```

`extern_c` có thể compile-check trước khi linker FFI hoàn chỉnh.

---

# 45. BOOT-008 invariants

Đề xuất:

```text
AFN-20 Function identity is semantic
AFN-21 Function declarations resolve before body analysis
AFN-22 Function overload is not part of v1
AFN-23 Parameter passing follows ownership semantics
AFN-24 Copy parameters do not consume source
AFN-25 Owning parameters consume non-Copy arguments
AFN-26 View parameters create bounded capabilities
AFN-27 Mutable view parameters require exclusive access
AFN-28 Return transfers ownership when required
AFN-29 Return does not imply heap allocation
AFN-30 Function calls preserve evaluation order
AFN-31 MIR calls do not encode physical registers
AFN-32 ABI lowering occurs after semantic MIR
AFN-33 Internal ABI may be optimized
AFN-34 External ABI is explicit and stable
AFN-35 ABI lowering may use sret
AFN-36 ABI lowering may use caller-allocated returns
AFN-37 Aggregate representation is target-specific
AFN-38 Function pointers are explicit indirect calls
AFN-39 Tail calls are optimization/ABI decisions
AFN-40 Stack frame is not source semantics
AFN-41 Zero-frame functions are valid
AFN-42 Recursion requires no special semantic mechanism
AFN-43 Panic is distinct from Result
AFN-44 Variadic functions are ABI/FFI concerns
AFN-45 Entry startup is separate from function semantics
AFN-46 pub visibility does not imply binary export
AFN-47 Exported symbols require explicit ABI/export contract
AFN-48 Calling convention is part of ABI identity
```

---

# 46. BOOT-008 Gate

Milestone chỉ PASS khi:

```text
[✓] multiple functions
[✓] forward function references
[✓] scalar parameters
[✓] scalar returns
[✓] owning parameters
[✓] Copy parameters
[✓] view parameters
[✓] mutable view parameters
[✓] ownership-aware return
[✓] function calls
[✓] indirect function representation prepared
[✓] recursion
[✓] mutual recursion
[✓] evaluation order

[✓] internal ABI separation
[✓] ABI classification layer
[✓] caller/callee model
[✓] aggregate ABI model
[✓] sret representation
[✓] zero-frame functions
[✓] entry-point separation

[✓] MIR interpreter
[✓] native x86_64
[✓] -O0
[✓] MIR/native differential
[✓] compile-fail diagnostics
[✓] regression
```

---

## Một nguyên tắc lớn được chốt ở BOOT-008

Axiom có thể được nhìn như **4 thế giới nối tiếp nhau**:

```text
┌────────────────────────────────────────────┐
│              SOURCE SEMANTICS              │
│                                            │
│ let / var / function / ownership / Place  │
└─────────────────────┬──────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│                  MIR                       │
│                                            │
│ Value / Place / CFG / Call / Drop         │
└─────────────────────┬──────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│                 ABI/LIR                    │
│                                            │
│ Direct / Indirect / Split / sret / args   │
└─────────────────────┬──────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│             MACHINE WORLD                  │
│                                            │
│ registers / stack / calling convention    │
└────────────────────────────────────────────┘
```

**Không được để tầng dưới rò ngược lên tầng trên.**

Ví dụ source:

```axiom
fn make() -> Point
```

vẫn là `Point` ở semantic MIR dù x86-64 ABI cuối cùng biến nó thành `sret`.

Đây chính là thứ sẽ cho phép Axiom sau này có **một frontend duy nhất nhưng nhiều backend native** mà không phải thiết kế lại semantics.

### Bước kế tiếp: **BOOTSTRAP-009 — Struct + Layout Model**

Khi đó ta sẽ chốt `struct`, field, nominal type, nested aggregate, field projection, layout, alignment, padding, `@repr(C)`, ZST và bắt đầu kiểm tra **Axiom value semantics ↔ physical memory representation**. Đây là bước nền trực tiếp cho ownership/capability và ABI aggregate.