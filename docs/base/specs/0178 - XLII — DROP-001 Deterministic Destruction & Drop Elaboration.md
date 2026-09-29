# XLII — DROP-001: Deterministic Destruction & Drop Elaboration

Đây là bước nối trực tiếp `Ownership + Capability` với MIR.

Mục tiêu:

```text
Typed HIR
   ↓
Ownership Facts
   ↓
Capability Facts
   ↓
Drop Analysis
   ↓
Drop-Elaborated MIR
```

Điểm quan trọng: **Drop là semantic cleanup**, không phải lệnh `free()`.

---

## 1. Nguyên tắc cốt lõi

Axiom giữ 4 khái niệm riêng:

```text
Value lifetime
Resource lifetime
Memory lifetime
Storage lifetime
```

Ví dụ `File`:

```text
File value
   ↓
Drop
   ↓
OS handle released
```

nhưng vùng memory chứa object có thể không cần `free` ngay.

Vì vậy:

```text
DROP(x) ≠ DEALLOC(x)
```

Đây là invariant đã đóng:

```text
AMEM-43  Resource lifetime is distinct from memory lifetime.
AMEM-44  Drop does not necessarily deallocate memory.
```

---

# 2. Khi nào compiler chèn Drop?

Compiler phải tìm mọi control-flow path rời khỏi scope.

Có 5 trường hợp chính:

```text
normal scope exit
return
break
continue
panic/unwind
explicit drop(x)
```

Ví dụ:

```axiom
fn foo() {
    let a = A()
    let b = B()
}
```

→

```text
DROP(b)
DROP(a)
RETURN
```

---

# 3. Thứ tự Drop

Mặc định:

> Drop theo thứ tự ngược với thứ tự initialization/đăng ký ownership.

Ví dụ:

```axiom
let a = A()
let b = B()
let c = C()
```

→

```text
DROP(c)
DROP(b)
DROP(a)
```

Invariant:

```text
ADROP-20
Default destruction order is reverse initialization order.
```

---

# 4. Nếu initialization thất bại giữa chừng

Ví dụ:

```axiom
let a = A()
let b = make_b()? 
let c = C()
```

Nếu `make_b()` trả `Err`:

```text
a = OWNED
b = UNINIT
c = UNINIT
```

cleanup:

```text
DROP(a)
RETURN Err
```

Không được:

```text
DROP(b)
DROP(c)
```

vì chúng chưa được initialize.

---

# 5. `MAYBE_INIT` không được Drop

Ví dụ:

```axiom
var x: T

if cond {
    x = make()
}
```

Nếu scope kết thúc:

```text
x = MAYBE_INITIALIZED
```

Compiler không được đơn giản:

```text
DROP(x)
```

Nếu chương trình hợp lệ, compiler phải chứng minh `x` initialized trước mọi implicit Drop.

Nếu không chứng minh được → compile error.

---

# 6. Partial move

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}
```

```axiom
let u = ...
let name = u.name
```

State:

```text
u
├── name = MOVED
└── age  = OWNED
```

Nếu compiler-derived Drop:

```text
DROP(u.age)
```

Không:

```text
DROP(u.name)
```

---

# 7. Whole move

```axiom
let u = ...
consume(u)
```

Sau:

```text
u = MOVED
```

implicit scope Drop:

```text
nothing
```

Không được tạo:

```text
DROP(u)
```

vì sẽ double-drop.

---

# 8. Custom Drop

Nếu:

```axiom
impl Drop for User {
    ...
}
```

thì object có **destructor semantic obligation**.

Axiom đã chốt:

```text
custom Drop → no partial move
```

Vì destructor user-defined có thể cần invariant toàn object.

Do đó:

```axiom
let name = u.name
```

→ reject nếu `User` có custom Drop.

---

# 9. Compiler-derived Drop

Nếu compiler tự biết cấu trúc Drop:

```text
User
├── name: Drop
└── age: Copy
```

thì compiler có thể generate semantic destructor:

```text
if name owned:
    DROP(name)
```

Không cần user viết destructor.

---

# 10. Explicit `drop(x)`

Axiom cho phép:

```axiom
drop(x)
```

Semantic:

```text
DROP(x)
```

Sau đó:

```text
x = DROPPED
```

Không còn implicit Drop cuối scope.

Ví dụ:

```axiom
let file = open(...)
use(file)

drop(file)

do_expensive_work()
```

Compiler có thể giải phóng resource sớm.

---

# 11. `drop(x)` không nhất thiết free memory

Ví dụ:

```text
drop(Box<T>)
```

có thể:

```text
resource cleanup
storage release
```

nhưng semantic contract chỉ yêu cầu destruction semantics.

Compiler/allocator quyết định memory strategy.

---

# 12. Explicit Drop với live capability

```axiom
let s = ...
let v = view(s)

drop(s)
```

→ reject:

```text
AX_VIEW_0005
cannot drop owner while dependent capability is live
```

Nếu:

```axiom
let s = ...
let v = view(s)
use(v)
drop(v) // nếu explicit capability cleanup được hỗ trợ
drop(s)
```

thì hợp lệ.

Tuy nhiên Axiom không cần bắt programmer phải `drop(v)` trong trường hợp thông thường; liveness analysis tự xác định capability dead.

---

# 13. Capability dead trước owner Drop

Ví dụ:

```axiom
let s = ...
{
    let v = view(s)
    use(v)
}

drop(s)
```

Capability chết trước:

```text
v → DEAD
```

nên:

```text
DROP(s)
```

hợp lệ.

Thậm chí compiler có thể nhận:

```axiom
let v = view(s)
use(v)
drop(s)
```

và biết `v` dead sau `use(v)`.

---

# 14. Early return

Ví dụ:

```axiom
fn foo() -> i32 {
    let a = A()
    let b = B()

    if cond {
        return 42
    }

    0
}
```

Return path:

```text
DROP(b)
DROP(a)
RETURN 42
```

Normal path:

```text
DROP(b)
DROP(a)
RETURN 0
```

Hai paths đều phải cleanup chính xác.

---

# 15. Return ownership

Ví dụ:

```axiom
fn make() -> Text {
    let x = make_text()
    x
}
```

Final expression `x` chuyển ownership cho caller.

Semantic:

```text
MOVE(x)
RETURN
```

Không:

```text
DROP(x)
RETURN
```

Nếu vừa Drop vừa Return thì double destruction.

---

# 16. Return một field

```axiom
fn extract(s: S) -> Text {
    s.name
}
```

Nếu `S` compiler-derived Drop:

```text
MOVE(s.name)
DROP(remaining owned fields)
RETURN name
```

Đây là trường hợp partial move + return.

Ví dụ:

```text
s
├── name → MOVED_TO_RETURN
└── other → OWNED
```

→

```text
DROP(other)
RETURN name
```

---

# 17. `?` và Drop

Đây là lý do `?` phải được xử lý sau ownership.

```axiom
fn foo() -> Result<T, E> {
    let resource = acquire()?
    let value = operation()?
    ...
}
```

Nếu `operation()` trả `Err`:

```text
DROP(value nếu initialized)
DROP(resource)
RETURN Err
```

Không cần exception runtime.

---

# 18. Panic

Nếu panic strategy là `abort`:

```text
PANIC
```

process kết thúc, không cần semantic unwind.

Nếu profile là unwind:

```text
PANIC
 ↓
cleanup active owned values
 ↓
unwind
```

Drop elaborator phải dựa trên panic profile.

Không tạo một exception system mới.

---

# 19. Panic trong Drop

Axiom đã chốt:

- Drop không phải recoverable-error mechanism.
- Drop không propagate `Result`.
- Nếu Drop gây panic trong lúc đang unwind → terminate/abort.

Do đó Drop graph không có:

```text
DROP → Result
```

mặc định.

Semantic:

```text
DROP
```

là non-fallible.

---

# 20. Loop `break`

Ví dụ:

```axiom
while cond {
    let x = acquire()

    if done {
        break
    }
}
```

Khi `break`:

```text
DROP(x)
BREAK
```

Nhưng mỗi iteration có lifetime riêng của `x`.

---

# 21. `continue`

```axiom
while cond {
    let x = acquire()

    if skip {
        continue
    }

    use(x)
}
```

`continue` phải:

```text
DROP(x)
CONTINUE
```

không được bỏ cleanup.

---

# 22. Nested scopes

```axiom
let a = A()

{
    let b = B()
    {
        let c = C()
    }
}
```

→:

```text
DROP(c)
DROP(b)
DROP(a)
```

---

# 23. Drop tree

Thay vì generate Drop trực tiếp từ syntax, tạo:

```text
DropPlan
```

Ví dụ:

```text
DropPlan {
    scope_id
    entries: [
        DropEntry(a),
        DropEntry(b)
    ]
}
```

Mỗi entry chứa:

```text
Place
DropKind
Condition
SourceSpan
```

---

# 24. Conditional Drop

Partial ownership cần:

```text
DROP_IF_OWNED(place)
```

Ví dụ:

```text
s
├── a = MOVED
└── b = OWNED
```

Compiler có thể lower:

```text
DROP_IF_OWNED(s.a)
DROP_IF_OWNED(s.b)
```

nhưng optimizer thường loại bỏ điều kiện đã biết.

Nếu `s.a` chắc chắn MOVED:

```text
DROP_IF_OWNED(s.a)
```

→ eliminated.

---

# 25. MIR Drop operations

MIR đã có:

```text
DROP
DROP_IF_OWNED
```

Thêm semantic distinction:

```text
DROP place
```

là guaranteed owned.

```text
DROP_IF_OWNED place
```

là conditional cleanup.

Verifier đảm bảo:

```text
DROP
```

chỉ áp dụng cho valid ownership state.

---

# 26. Drop elaboration không phải optimizer

Ví dụ:

```text
DROP_IF_OWNED(x)
```

có thể được optimizer biến thành:

```text
nothing
```

nếu `x` chắc chắn moved.

Nhưng Drop elaborator không được tự làm machine-level optimization.

Boundary:

```text
Drop Analysis
    ↓
semantic cleanup
    ↓
MIR
    ↓
optimizer
```

---

# 27. Drop + Move

Ví dụ:

```axiom
let x = ...
let y = x
```

Ownership facts:

```text
x → MOVED
y → OWNED
```

Drop plan:

```text
x → NONE
y → DROP
```

---

# 28. Drop + Copy

```axiom
let x = 42
let y = x
```

cả hai vẫn valid nhưng primitive `i32` không có Drop obligation.

Drop plan:

```text
x → NONE
y → NONE
```

Copy không tạo resource cleanup obligation.

---

# 29. Drop + view

`view<T>` không sở hữu resource.

Do đó:

```text
DROP(view)
```

không có ownership destruction giống owning `T`.

Capability lifetime kết thúc, không phải owner destruction.

Đây là lý do:

```text
Capability lifetime ≠ resource lifetime
```

---

# 30. Drop + `mut_view`

Tương tự:

```text
mut_view<T>
```

là capability, không phải owner.

Khi biến capability chết:

```text
capability → DEAD
```

không gọi destructor của `T`.

---

# 31. Drop order và fields

Ví dụ:

```axiom
struct S {
    a: A
    b: B
}
```

compiler-derived destruction:

```text
DROP(b)
DROP(a)
```

Nhưng nếu user-defined Drop:

```text
impl Drop for S { ... }
```

thì semantic destructor của `S` chạy theo contract; compiler không tự giả định user destructor tương đương field-by-field Drop.

---

# 32. Drop flags

Không nên đưa hidden runtime boolean vào mọi object.

Đây là điểm cực kỳ quan trọng về hiệu năng.

Sai hướng:

```text
struct S {
    ...
    hidden_drop_flag: bool
}
```

Đúng:

```text
compiler tracks ownership state
```

và chỉ materialize drop flags khi control flow thực sự cần.

Ví dụ:

```text
if cond {
    move(s.a)
}
drop(s)
```

Compiler có thể cần internal state/flag để biết `a` còn owned trên runtime path.

Nhưng optimizer có thể:

- eliminate flag
- split control flow
- scalarize fields
- prove state statically.

---

# 33. Drop flag không phải object header

Axiom không có:

```text
mandatory object header
```

Drop flag nếu cần chỉ là:

```text
compiler-generated control state
```

có thể nằm:

```text
register
stack
SSA predicate
control-flow branch
```

không nhất thiết nằm trong object.

---

# 34. Drop plan example

```axiom
fn foo() {
    let a = A()
    let b = B()

    if cond {
        consume(a)
        return
    }

    use(b)
}
```

Semantic DropPlan:

```text
normal exit:
    DROP(b)
    DROP(a)

return branch:
    a = MOVED
    DROP(b)
    RETURN

panic/unwind:
    DROP(b)
    DROP(a) if still owned
```

---

# 35. Implementation

```text
compiler/drop/
├── plan.ax
├── elaborate.ax
├── order.ax
├── partial.ax
├── flags.ax
├── unwind.ax
├── diagnostics.ax
└── tests/
    ├── reverse_order.ax
    ├── move_no_drop.ax
    ├── partial_move.ax
    ├── return_cleanup.ax
    ├── break_cleanup.ax
    ├── continue_cleanup.ax
    ├── panic_cleanup.ax
    └── nested_scope.ax
```

---

# 36. Drop invariants

```text
ADROP-20
Every owning value with Drop obligation is deterministically released.

ADROP-21
Drop order is deterministic.

ADROP-22
Default local destruction is reverse initialization order.

ADROP-23
Moved values are never implicitly dropped.

ADROP-24
Uninitialized values are never dropped.

ADROP-25
Partially moved compiler-derived values drop only remaining owned components.

ADROP-26
User-defined Drop forbids partial move.

ADROP-27
Returned ownership is not dropped by the source scope.

ADROP-28
Early return performs required cleanup.

ADROP-29
Break performs required cleanup.

ADROP-30
Continue performs required cleanup.

ADROP-31
Panic cleanup follows selected panic strategy.

ADROP-32
Drop is not recoverable error propagation.

ADROP-33
Drop does not imply physical deallocation.

ADROP-34
Drop flags are compiler state, not mandatory object fields.

ADROP-35
Drop elaboration preserves ownership semantics.

ADROP-36
Drop elaboration is independent of physical storage placement.

ADROP-37
Drop elaboration is independent of optimization level.

ADROP-38
Capability validity is checked before owner destruction.

ADROP-39
Compiler-generated Drop may support partial ownership state.

ADROP-40
Drop of a capability does not imply destruction of its owner.
```

---

# XLIII — MIR-001: Semantic MIR v0.1

Bây giờ ta đã đủ ba thành phần:

```text
Ownership
Capability
Drop
```

để tạo MIR.

Pipeline chính thức:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
Ownership
 ↓
Capability
 ↓
Drop
 ↓
MIR
 ↓
Verifier
 ↓
Verified MIR
```

MIR phải **đủ thấp để compiler backend dễ xử lý**, nhưng **chưa được dính x86**.

---

## 1. MIR không phải SSA thuần

Axiom MIR dùng:

> **SSA-oriented CFG + explicit Places**

Không ép toàn bộ thành SSA ngay.

Ví dụ:

```text
Local x
Field x.a
Index x[i]
```

vẫn cần identity cho ownership/drop.

---

## 2. MIR block

```text
BasicBlock {
    id: BlockId
    instructions: Vec<Instr>
    terminator: Terminator
}
```

Terminator:

```text
Goto
Branch
Switch
Return
Panic
Trap
Unreachable
```

---

## 3. MIR instruction tối thiểu

```text
CONST
COPY
MOVE
FIELD_PLACE
INDEX_PLACE
LOAD
STORE

VIEW
VIEW_MUT

ALLOC
DEALLOC
DROP
DROP_IF_OWNED

CALL
DYNAMIC_CALL

CAST
CONVERT
AGGREGATE

PHI

BOUNDS_CHECK

ENUM_TAG
ENUM_PAYLOAD

PANIC
TRAP
```

Concurrency/async/atomic sẽ được bổ sung nhưng không cản MIR-001.

---

# 4. Ví dụ đơn giản nhất

Source:

```axiom
fn main() -> i32 {
    42
}
```

MIR:

```text
bb0:
    %0 = CONST i32 42
    RETURN %0
```

Không có:

```text
ALLOC
DROP
runtime call
```

Đây là mục tiêu quan trọng:

> Một chương trình không cần runtime thì MIR không được tự sinh runtime.

---

# 5. `fn main() {}`

```axiom
fn main() {}
```

MIR:

```text
bb0:
    RETURN ()
```

---

# 6. Arithmetic

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

MIR:

```text
bb0:
    %2 = ADD_CHECKED %a, %b
    RETURN %2
```

Nếu:

```axiom
a +% b
```

→

```text
ADD_WRAP
```

Nếu:

```axiom
a +| b
```

→

```text
ADD_SAT
```

Không được biến ba semantics này thành một `ADD` chung quá sớm.

---

# 7. Local variable

```axiom
fn foo() -> i32 {
    let x = 10
    let y = 20
    x + y
}
```

MIR có thể:

```text
bb0:
    %x = CONST i32 10
    %y = CONST i32 20
    %r = ADD_CHECKED %x, %y
    RETURN %r
```

Không bắt buộc stack allocation.

---

# 8. Ownership MOVE trong MIR

```axiom
let y = x
```

semantic MIR:

```text
%y = MOVE x
```

Sau verification:

```text
x = MOVED
y = OWNED
```

Optimizer sau đó có thể eliminate physical move.

---

# 9. COPY

```text
%y = COPY %x
```

Verifier cần biết `x` có `Copy`.

---

# 10. Field access

```axiom
x.a
```

MIR:

```text
%p = FIELD_PLACE x, FieldId(a)
%v = LOAD %p
```

Nếu move:

```text
%v = MOVE %p
```

---

# 11. Assignment

```axiom
x.a = y
```

MIR:

```text
%p = FIELD_PLACE x, a
STORE %p, y
```

Ownership verifier đảm bảo old value của `x.a` được xử lý đúng trước overwrite.

---

# 12. Function call

```axiom
foo(x)
```

MIR:

```text
%r = CALL FunctionId(foo), [x]
```

Ownership mode của argument đã được Typed HIR + ownership phase xác định.

---

# 13. View

```axiom
let v = view(x)
```

MIR:

```text
%v = VIEW x
```

Verifier kiểm:

```text
owner alive
provenance valid
region valid
capability lifetime
```

Sau Verified MIR → LIR, `VIEW` thường bị erase thành address/length hoặc register facts.

---

# 14. Mutable view

```text
%v = VIEW_MUT x
```

Verifier phải xác nhận exclusive WRITE capability.

---

# 15. Bounds check

```axiom
a[i]
```

MIR:

```text
%len = LENGTH a
BOUNDS_CHECK i, %len
%p = INDEX_PLACE a, i
%v = LOAD %p
```

Optimizer có thể loại:

```text
BOUNDS_CHECK
```

nếu range analysis chứng minh safe.

---

# 16. If

```axiom
if cond {
    1
} else {
    2
}
```

MIR:

```text
bb0:
    BRANCH cond, bb1, bb2

bb1:
    %a = CONST i32 1
    GOTO bb3

bb2:
    %b = CONST i32 2
    GOTO bb3

bb3:
    %r = PHI [%a, bb1], [%b, bb2]
    RETURN %r
```

---

# 17. Match

Match được hạ thành:

```text
SWITCH
```

hoặc decision tree.

Ví dụ:

```text
ENUM_TAG
SWITCH
ENUM_PAYLOAD
```

Optimizer/backend có thể đổi representation.

---

# 18. `?`

Ví dụ:

```axiom
let x = foo()?
```

MIR semantic:

```text
%r = CALL foo()
SWITCH_RESULT %r
```

success:

```text
extract Ok
continue
```

failure:

```text
cleanup
RETURN Err
```

Không cần exception mechanism.

---

# 19. Return cleanup

```axiom
fn foo() -> i32 {
    let x = Resource()
    42
}
```

MIR:

```text
bb0:
    %x = CALL Resource
    %r = CONST i32 42
    DROP %x
    RETURN %r
```

---

# 20. MIR ownership checkpoint

Sau Drop elaboration:

```text
MIR
```

vẫn có semantic ownership operations.

Sau verifier:

```text
VERIFIED MIR
```

mới được optimizer tin tưởng.

Invariant:

```text
AMIR-20
Unverified MIR cannot enter semantic optimization.
```

---

# 21. Verified MIR

Verifier kiểm tra:

### Type

```text
operand types
return type
call signatures
casts
```

### Ownership

```text
move state
copy legality
drop legality
partial move
```

### Capability

```text
provenance
live capability
read/write conflicts
escape
relocation
```

### CFG

```text
reachable blocks
terminators
PHI consistency
dominance requirements
```

### Safety

```text
bounds
initialization
unsafe-established contracts
```

---

# 22. Verified MIR invariants

```text
AVMIR-20
Every MIR operand has a valid type.

AVMIR-21
Every local has a valid semantic identity.

AVMIR-22
Every block has exactly one terminator.

AVMIR-23
All branch targets are valid.

AVMIR-24
All PHI inputs correspond to predecessor blocks.

AVMIR-25
No use occurs before required initialization.

AVMIR-26
No moved value is illegally used.

AVMIR-27
No illegal double drop exists.

AVMIR-28
All capability operations satisfy provenance.

AVMIR-29
No live capability is invalidated.

AVMIR-30
All checked accesses have valid bounds semantics.

AVMIR-31
All calls satisfy typed signatures.

AVMIR-32
All return values satisfy function return type.

AVMIR-33
All unsafe-established facts satisfy their recorded contract.

AVMIR-34
Verified MIR is deterministic.

AVMIR-35
Optimization may only consume Verified MIR.

AVMIR-36
Backend lowering cannot reinterpret semantic ownership.

AVMIR-37
Verified MIR contains no unresolved frontend names.

AVMIR-38
Verified MIR is independent of target machine architecture.
```

---

# XLIV — MIR-001 Vertical Slice

Bây giờ **không tiếp tục mở thêm semantic subsystem** ngay. Ta phải bắt đầu build compiler thật.

Mốc đầu tiên:

```text
fn main() -> i32 {
    42
}
```

Pipeline:

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
Type Checker
 ↓
Typed HIR
 ↓
Ownership
 ↓
Capability
 ↓
Drop
 ↓
MIR
 ↓
Verifier
```

Expected MIR:

```text
fn main() -> i32

bb0:
    %0 = CONST i32 42
    RETURN %0
```

Sau đó:

```text
MIR
 ↓
LIR
 ↓
Machine IR
 ↓
ELF
 ↓
axiom-link
 ↓
Linux executable
```

---

# 45. Vertical slice thứ hai

Sau `42`:

```axiom
fn main() -> i32 {
    let x = 10
    let y = 32
    x + y
}
```

Expected:

```text
CONST 10
CONST 32
ADD_CHECKED
RETURN
```

Output:

```text
42
```

---

# 46. Vertical slice thứ ba

Function call:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}

fn main() -> i32 {
    add(20, 22)
}
```

MIR:

```text
add:
    %r = ADD_CHECKED a, b
    RETURN %r

main:
    %r = CALL add(20, 22)
    RETURN %r
```

Sau ABI lowering:

```text
RDI = 20
RSI = 22
CALL add
RAX = result
```

---

# 47. Vertical slice thứ tư

Conditional:

```axiom
fn main() -> i32 {
    let x = 10

    if x > 5 {
        42
    } else {
        0
    }
}
```

→ CFG + comparison + branch + PHI.

Đây là mốc chứng minh:

```text
Parser
+
HIR
+
CFG
+
MIR
+
Backend
```

đã thực sự nối được với nhau.

---

# 48. Thứ tự triển khai thực tế từ đây

Không nên tiếp tục thiết kế hàng chục subsystem trước khi chạy binary.

Thứ tự nên là:

```text
DONE
Kernel
Lexer
Parser
Resolver/HIR
Type System
Trait basics
Ownership
Capability
Drop

NOW
↓
MIR-001
↓
MIR verifier
↓
LIR-001
↓
x86 Machine IR
↓
x86 encoder
↓
ELF writer
↓
axiom-link
↓
hello executable
```

Sau khi vertical slice này chạy:

```text
arithmetic
→ locals
→ functions
→ branches
→ loops
→ structs
→ enums
→ ownership
→ views
→ Drop
→ generics
→ traits
→ closures
→ async
→ concurrency
```

sẽ được thêm từng lát cắt, thay vì xây frontend/backend cô lập.

---

## Mốc cực kỳ quan trọng tiếp theo

**LIR-001** sẽ không cần mở rộng semantics nữa.

Ta sẽ định nghĩa trực tiếp:

```text
Verified MIR
     ↓
Semantic Lowering
     ↓
Axiom LIR
```

và đặc biệt chốt **representation của `Value`, `Place`, aggregate return, memory operation, call convention và virtual register** sao cho một chương trình Axiom đơn giản có thể đi thẳng đến **x86-64 machine code mà không cần LLVM**.