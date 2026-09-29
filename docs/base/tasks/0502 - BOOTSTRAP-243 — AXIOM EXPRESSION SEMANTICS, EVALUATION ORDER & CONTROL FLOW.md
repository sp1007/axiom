# BOOTSTRAP-243 — AXIOM EXPRESSION SEMANTICS, EVALUATION ORDER & CONTROL FLOW

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là task rất quan trọng. Nếu 242 quyết định **expression là gì**, thì 243 quyết định **expression xảy ra như thế nào**.

Mục tiêu:

> **Axiom phải có evaluation semantics hoàn toàn deterministic ở cấp ngôn ngữ, nhưng optimizer vẫn được phép reorder mọi thứ không observable.**

---

# 1. Nguyên tắc trung tâm

Axiom phân biệt:

```text
Semantic Evaluation Order
        ≠
Physical Instruction Order
```

Ví dụ:

```axiom
let x = foo() + bar()
```

Ngôn ngữ phải định nghĩa thứ tự `foo()` và `bar()`.

Nhưng sau khi compiler chứng minh chúng độc lập, machine code có thể:

```text
parallelize
reorder
inline
vectorize
eliminate
```

miễn là observable behavior không thay đổi.

---

# 2. Evaluation model

Expression được mô hình hóa:

```text
Expression
    ↓
Evaluate operands
    ↓
Perform operation
    ↓
Produce value
    ↓
Apply semantic effects
```

Mỗi expression có:

```text
Value
Effects
ControlFlow
OwnershipTransitions
CapabilityAccesses
```

---

# 3. Observable behavior

Một thứ được coi là observable nếu có thể ảnh hưởng tới:

```text
return value
Result
panic
termination
I/O
volatile access
atomic behavior
synchronization
FFI behavior
external resource state
program-visible timing contracts
```

Timing thông thường **không** được coi là semantic observable behavior.

---

# 4. Pure expression

Ví dụ:

```axiom
let x = a + b
```

nếu `a`, `b` và `Add` đều pure:

```text
Effects = {}
```

Compiler có toàn quyền:

```text
constant fold
CSE
reorder
vectorize
eliminate
```

---

# 5. Effectful expression

Ví dụ:

```axiom
print("hello")
```

có:

```text
Effect = IO
```

Optimizer không được loại bỏ hoặc reorder tùy ý.

---

# 6. Evaluation order của binary operator

Axiom v1 quy định:

```text
left operand
    ↓
right operand
    ↓
operator
```

Ví dụ:

```axiom
a() + b()
```

semantic order:

```text
a()
b()
+
```

---

# 7. Nhưng optimizer có thể reorder?

Có, nếu compiler chứng minh:

```text
a()
```

và:

```text
b()
```

không có observable dependency.

Ví dụ hai pure functions:

```axiom
a() + b()
```

machine code có thể tính:

```text
b()
a()
```

hoặc song song.

---

# 8. Side effect dependency

Nếu:

```axiom
foo() + bar()
```

và `foo()`:

```text
writes global state
```

còn `bar()` đọc state đó:

```text
ReadAfterWrite dependency
```

thì semantic order phải được preserved.

---

# 9. Function arguments

Axiom v1 chọn evaluation order:

```text
arguments từ trái sang phải
```

Ví dụ:

```axiom
foo(a(), b(), c())
```

semantic:

```text
a()
b()
c()
foo(...)
```

---

# 10. Optimizer exception

Compiler có thể reorder arguments nếu chứng minh dependency không tồn tại.

Ví dụ:

```text
a()
b()
```

pure/independent:

```text
b()
a()
```

được phép ở machine level.

---

# 11. Why deterministic source order?

Điều này giúp:

```text
debugging
reasoning
FFI
resource lifetime
side effects
AI analysis
```

đơn giản hơn rất nhiều.

Programmer không phải nhớ các rule kiểu:

> “thứ tự argument evaluation phụ thuộc compiler.”

---

# 12. Function call

Semantic:

```text
evaluate callee
evaluate arguments L→R
validate callable preconditions
invoke
receive result
```

---

# 13. Callee expression

Ví dụ:

```axiom
get_fn()(x)
```

Compiler:

```text
evaluate get_fn()
evaluate x
call returned callable
```

---

# 14. Method call

```axiom
x.foo(a, b)
```

semantic order:

```text
evaluate receiver
evaluate a
evaluate b
invoke foo
```

Method resolution đã xảy ra compile-time; runtime không cần lookup nếu static dispatch.

---

# 15. Field access

```axiom
x.field
```

evaluate `x`, sau đó access field.

Nếu `x` là place:

```text
x.field
```

compiler có thể giữ dưới dạng place mà không materialize intermediate value.

---

# 16. Indexing

```axiom
a[i]
```

semantic:

```text
evaluate a
evaluate i
perform index operation
```

Bounds checking thuộc semantic safety.

---

# 17. Index assignment

```axiom
a[i] = value
```

order:

```text
evaluate destination base
evaluate index
evaluate value
perform write
```

Nhưng compiler phải bảo toàn capability/alias semantics.

---

# 18. Assignment

```axiom
x = expression
```

semantic:

```text
evaluate RHS
validate destination
perform assignment
```

Destination không được đọc như ordinary value chỉ để tính assignment.

---

# 19. Compound assignment

```axiom
x += y
```

không được semantic hóa thành:

```text
x = x + y
```

một cách ngây thơ vì `x` có thể có side effects khi indexing/property access.

Nó là một operation có destination access semantics riêng.

---

# 20. Example

```axiom
a[f()] += g()
```

semantic structure:

```text
evaluate a
evaluate f()
evaluate g()
read/modify/write destination
```

Compiler phải đảm bảo destination được xác định đúng một lần.

---

# 21. Assignment result

Axiom nên quy định assignment có type:

```text
unit
```

không phải giá trị của RHS.

Do đó:

```axiom
let x = (a = b)
```

không được dùng như C-style assignment expression.

Điều này giảm một lượng lớn ambiguity.

---

# 22. Chained assignment

```axiom
a = b = c
```

không hợp lệ trong Core v1.

Thay bằng:

```axiom
b = c
a = b
```

rõ ràng hơn.

---

# 23. Destructuring assignment

Nếu Axiom hỗ trợ:

```axiom
(a, b) = value
```

semantic phải được định nghĩa như một atomic logical assignment operation.

RHS được evaluate trước.

Destination writes sau đó.

---

# 24. Destructuring initialization

```axiom
let (a, b) = value
```

khác assignment.

Ownership verifier theo dõi từng field/value binding.

---

# 25. Temporary values

Temporary có lifetime:

```text
từ thời điểm tạo
→ đến cuối semantic scope/use được định nghĩa
```

Compiler có thể physicalize khác đi.

---

# 26. Temporary không đồng nghĩa allocation

```axiom
foo(make_value())
```

không có nghĩa:

```text
heap allocation
```

Compiler có thể:

```text
register
SSA
stack
caller-allocated
inline
```

---

# 27. Temporary ownership

Nếu temporary là owning non-Copy:

```axiom
foo(make_buffer())
```

ownership chuyển vào parameter nếu callable yêu cầu ownership.

Không tạo clone ngầm.

---

# 28. Temporary view

```axiom
foo(view(x))
```

view chỉ tồn tại trong context được phép.

Compiler verifier đảm bảo không escape.

---

# 29. Drop timing

Drop semantic timing phải deterministic.

Ví dụ:

```axiom
{
    let a = A()
    let b = B()
}
```

cleanup:

```text
drop(b)
drop(a)
```

---

# 30. Reverse initialization order

Rule:

> local owning values được cleanup theo reverse initialization order, trừ khi semantic dependency yêu cầu khác.

Điều này phù hợp với frozen ownership model.

---

# 31. Early return

```axiom
fn foo() -> i32 {
    let a = A()
    let b = B()

    return 42
}
```

semantic:

```text
return value
↓
drop(b)
drop(a)
↓
return
```

---

# 32. `break`

```axiom
loop {
    let x = A()

    if done {
        break
    }
}
```

`x` phải được cleanup trước khi control flow rời scope.

---

# 33. `continue`

Tương tự:

```text
x cleanup
↓
continue
↓
next iteration
```

---

# 34. Panic

Nếu panic profile là unwind:

```text
panic
↓
cleanup active owning values
↓
unwind
```

Nếu abort:

```text
panic
↓
terminate
```

Không yêu cầu cleanup nếu process abort semantics đã chọn.

---

# 35. Panic không phải exception

Axiom không có ordinary exception propagation.

Recoverable failure:

```text
Result<T,E>
```

Unrecoverable:

```text
panic
```

---

# 36. `?`

```axiom
let x = foo()?
```

semantic:

```text
evaluate foo()
inspect Result
    Ok → continue
    Err → return Err
```

Nếu return Err:

```text
active locals cleanup
↓
return
```

---

# 37. Option `?`

Tương tự:

```text
Some → unwrap
None → propagate
```

---

# 38. `if`

```axiom
if condition {
    A
} else {
    B
}
```

semantic:

```text
evaluate condition
if true → A
else → B
```

Chỉ một branch được evaluate.

---

# 39. `if` condition side effect

```axiom
if next() > 0 {
    foo()
}
```

`next()` luôn xảy ra trước branch selection.

---

# 40. `match`

```axiom
match value {
    A => foo()
    B => bar()
}
```

semantic:

```text
evaluate scrutinee
↓
match pattern
↓
evaluate selected branch only
```

---

# 41. Pattern guard

Nếu sau này Axiom hỗ trợ guard:

```text
pattern
↓
evaluate guard
↓
branch
```

guard chỉ được evaluate nếu pattern match.

---

# 42. Match exhaustiveness

Exhaustiveness là compile-time property.

Runtime không được có:

```text
default magic branch
```

nếu compiler đã chứng minh exhaustive.

---

# 43. Loop

```axiom
loop {
    body
}
```

semantic infinite loop nếu không có control transfer.

Compiler có thể chứng minh unreachable code.

---

# 44. While

```axiom
while condition {
    body
}
```

semantic:

```text
condition
↓
if false exit
if true body
↓
repeat
```

---

# 45. For

```axiom
for x in collection {
    body
}
```

semantic sugar:

```text
iterator
↓
next()
↓
Some(x)
↓
body
↓
next()
...
None
↓
exit
```

Không tạo runtime abstraction bắt buộc.

---

# 46. Iterator temporary

Iterator owning value:

```axiom
for x in make_iterator() {
    ...
}
```

được cleanup đúng scope sau khi loop kết thúc.

---

# 47. `break value`

Axiom v1 nên **không thêm `break value` vào Core**.

Nếu cần loop trả value, có thể dùng explicit loop/result abstraction sau.

Lý do:

```text
break
```

giữ control-flow model đơn giản hơn.

---

# 48. `continue`

`continue` chuyển tới iteration condition/header theo loop kind.

---

# 49. Labels

Axiom v1 có thể cho labeled loops nếu cần:

```text
'outer: loop { ... }
```

nhưng không nên mở rộng thành general goto.

---

# 50. `goto`

**Không có `goto` trong safe Core v1.**

System/unsafe layer có thể cung cấp machine-level control primitives nếu thực sự cần.

---

# 51. Return

`return e`:

```text
evaluate e
↓
check return type
↓
cleanup active locals
↓
function exit
```

---

# 52. Return value ownership

Nếu return owning value:

```axiom
return buffer
```

ownership chuyển ra caller.

Không Drop `buffer` trước khi transfer.

---

# 53. Return view

Nếu:

```axiom
fn first(...) -> view<T>
```

capability verifier phải chứng minh returned view provenance vẫn valid.

Không được trả view vào local stack storage.

---

# 54. Scope

Scope được định nghĩa semantic bởi:

```text
block
function
loop body
match branch
closure body
comptime block
```

không phải physical stack frame.

---

# 55. Scope exit

Mọi exit:

```text
normal
return
break
continue
propagate
panic-unwind
```

đều phải đi qua cleanup semantics thích hợp.

---

# 56. Cleanup graph

MIR nên explicit hóa cleanup:

```text
NormalExit
ReturnExit
BreakExit
ContinueExit
PropagateExit
PanicUnwindExit
```

→ cleanup blocks.

---

# 57. Drop elaboration

AST/HIR không cần explicit mọi Drop.

Compiler:

```text
Typed HIR
 ↓
MIR
 ↓
Ownership analysis
 ↓
Drop elaboration
```

sau đó MIR có Drop instructions.

---

# 58. Drop order và optimization

Compiler có thể eliminate:

```text
Drop
```

chỉ nếu chứng minh resource destructor có no observable effect và semantic rules cho phép.

Không được tự ý bỏ Drop của resource có observable external effect.

---

# 59. Destructive Drop

Ví dụ File:

```text
Drop(File)
```

có external effect:

```text
release OS handle
```

không được optimizer tùy ý loại bỏ.

---

# 60. Pure Drop

Một type có compiler-proven trivial Drop có thể bị scalarized/eliminated.

Ví dụ:

```text
struct SmallValue
```

không resource.

---

# 61. Evaluation order vs ownership

Ví dụ:

```axiom
foo(a, move(b))
```

compiler phải đảm bảo argument evaluation order trước khi ownership transition tương ứng được materialized.

---

# 62. Evaluation order vs views

```axiom
foo(view(a), mut_view(a))
```

có conflict.

Không được dùng evaluation order để “né” capability conflict.

Toàn bộ call phải fail nếu capability requirements không đồng thời hợp lệ.

---

# 63. Evaluation order vs aliasing

```axiom
foo(a[i], a[j])
```

compiler không được assume `i != j` nếu không chứng minh.

Capability/alias verifier xử lý overlap.

---

# 64. Short-circuit `&&`

```axiom
a && b
```

semantic:

```text
evaluate a
if false → false
otherwise evaluate b
```

`b` không được evaluate khi `a == false`.

---

# 65. Short-circuit `||`

```axiom
a || b
```

semantic:

```text
evaluate a
if true → true
otherwise evaluate b
```

---

# 66. Optimizer và short-circuit

Compiler có thể simplify:

```text
true && x
```

→ `x`

nếu `true` là compile-time constant.

Nhưng:

```text
false && side_effect()
```

có thể eliminate `side_effect()` vì semantic rule vốn đã nói nó không được execute.

---

# 67. `&&` / `||` không phải ordinary traits

Đây là frozen decision.

Không cho custom type định nghĩa short-circuit bằng arbitrary trait.

Nếu cần logical abstraction, dùng function/trait rõ ràng.

---

# 68. Ternary operator

Axiom v1 **không thêm `?:`**.

`if` đã là expression:

```axiom
let x = if cond { a } else { b }
```

đủ expressive.

---

# 69. Null-coalescing

Không có:

```text
??
?. 
```

vì Axiom dùng:

```text
Option
match
if
```

và không có null trong safe Core.

---

# 70. Sequence operator

Không có comma operator kiểu C:

```text
(a(), b())
```

Nếu cần sequence:

```axiom
{
    a()
    b()
}
```

---

# 71. Expression statement

Expression được phép xuất hiện ở statement position nếu:

```text
its value is intentionally discarded
```

Compiler có thể warning nếu expression trả Result mà không xử lý.

---

# 72. Discarded Result

Ví dụ:

```axiom
foo() // Result<T,E>
```

nếu Result là must-handle type:

→ diagnostic/warning theo error policy.

Explicit discard:

```axiom
let _ = foo()
```

hoặc cơ chế discard đã được standard library/error system quy định.

---

# 73. Evaluation of function arguments and ownership

Nếu:

```axiom
foo(make_a(), make_b())
```

semantic:

```text
make_a()
make_b()
call foo
```

Nếu `make_a()` panics:

```text
make_b()
```

không chạy.

---

# 74. Partial evaluation

Nếu:

```axiom
foo(constant, side_effect())
```

compiler có thể constant-fold `constant` nhưng không được loại bỏ/reorder `side_effect()` trái semantic effect rules.

---

# 75. FFI calls

FFI được coi là potentially effectful trừ khi contract nói rõ.

Ví dụ:

```text
extern "C" fn foo(...)
```

mặc định conservative.

---

# 76. Volatile

Volatile access là observable.

Compiler không được:

```text
remove
merge
cache
reorder
```

ngoài semantics volatile đã quy định.

---

# 77. Atomic

Atomic operations có memory-order semantics.

Evaluation order của source expression không tự thay thế happens-before model.

---

# 78. Synchronization

Mutex:

```axiom
lock.acquire()
critical()
lock.release()
```

synchronization effects tạo ordering constraints.

Optimizer không được phá vỡ chúng.

---

# 79. Resource effects

File/socket/process operations:

```text
Effect = ExternalResource
```

có observable state.

Compiler phải preserve semantic ordering.

---

# 80. Compiler intrinsic

Intrinsic chỉ được reorder nếu intrinsic specification cho phép.

Không phải cứ mang tên `intrinsic` là compiler được làm mọi thứ.

---

# 81. Undefined behavior

Axiom safe Core cố tránh UB.

Nếu semantic precondition bị vi phạm:

```text
safe code → compile-time rejection
unsafe/system → explicit contract violation
```

Machine-level undefined behavior chỉ được tồn tại trong clearly-defined unsafe boundary/foreign contract.

---

# 82. Overflow

Integer overflow behavior đã frozen:

```text
checked
wrapping
saturating
```

theo operation/type/profile semantics.

Không C-style signed-overflow UB.

---

# 83. Division

Division phải có defined semantics cho:

```text
divide by zero
signed minimum / -1
```

theo numeric system.

Không để backend tự quyết định.

---

# 84. Unreachable

Compiler có thể xác định:

```text
never
return
panic
exhaustive match
```

và mark CFG edges unreachable.

---

# 85. Dead code

Dead code có thể bị loại bỏ sau semantic checking.

Important:

> **Code có thể unreachable vẫn phải type-check và verify nếu nó là source code hợp lệ trong Complete Semantic Mode.**

---

# 86. Constant conditions

```axiom
if false {
    bad_code()
}
```

không được bỏ qua type checking chỉ vì condition constant.

Semantic correctness trước optimization.

---

# 87. Compile-time branch

`@cfg`/comptime selection khác ordinary constant `if`.

Code bị loại bởi configuration có thể không cần semantic-check trong target configuration.

---

# 88. Control-flow graph

MIR CFG:

```text
Entry
 ↓
Condition
 ├── True → Body
 │           ↓
 │        Continue/Header
 │
 └── False → Exit
```

mọi control flow đều explicit.

---

# 89. Structured CFG

Core v1 không có arbitrary jump.

Control-flow primitives:

```text
if
match
loop
while
for
break
continue
return
panic
?
```

đủ để tạo structured CFG.

---

# 90. Why no arbitrary goto?

Lợi ích:

```text
ownership analysis đơn giản
drop insertion deterministic
definite initialization đơn giản
capability lifetime dễ chứng minh
optimizer dễ canonicalize
AI reasoning dễ hơn
```

---

# 91. Internal goto vẫn tồn tại

Compiler IR **được phép** có arbitrary basic-block edges.

Điều này cực kỳ quan trọng:

```text
Source language
    structured

MIR
    arbitrary CFG
```

Programmer không bị giới hạn backend.

---

# 92. CFG normalization

Ví dụ:

```axiom
if cond {
    foo()
} else {
    bar()
}
baz()
```

MIR:

```text
entry
 ↓
branch
 ├── B1 → foo → merge
 └── B2 → bar → merge
                ↓
               baz
```

---

# 93. Dominance

MIR/SSA sau này sử dụng:

```text
dominators
post-dominators
loops
control dependence
```

để optimization và verification.

---

# 94. Evaluation order encoded in MIR

MIR không cần giữ source syntax nhưng phải preserve semantic order.

Ví dụ:

```axiom
foo(a(), b())
```

MIR conceptual:

```text
t0 = call a
t1 = call b
t2 = call foo(t0,t1)
```

Optimizer sau đó mới reorder nếu legal.

---

# 95. Effect dependencies in MIR

MIR nodes có EffectInfo:

```text
Read
Write
IO
Atomic
Volatile
Synchronize
Foreign
Panic
Allocate
Drop
```

Optimizer dùng chúng để xác định reorder legality.

---

# 96. Semantic barrier

Một operation có effect tạo dependency edges.

Ví dụ:

```text
IO1
IO2
```

phải giữ semantic order nếu cùng observable stream/resource.

---

# 97. Pure computation islands

Giữa hai effect barriers:

```text
IO
 ↓
pure computations
 ↓
IO
```

optimizer có thể tối ưu mạnh phần pure region.

Đây là cách Axiom đạt performance mà vẫn deterministic.

---

# 98. Memory operations

Ordinary memory read/write có alias semantics.

Không phải mọi load/store đều là global barrier.

Nếu compiler chứng minh:

```text
A != B
```

thì:

```text
load A
store B
```

có thể reorder.

---

# 99. Capability → alias facts

Frozen capability analysis cung cấp:

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

Optimizer sử dụng chúng.

`UNKNOWN` không được coi là independent.

---

# 100. Invariants — FROZEN

```text id="4gqv6x"
AEVAL-20
Axiom defines deterministic source-level evaluation semantics.

AEVAL-21
Semantic evaluation order is distinct from physical machine instruction order.

AEVAL-22
Optimizer may reorder operations only when observable semantics are preserved.

AEVAL-23
Binary operands are semantically evaluated left-to-right.

AEVAL-24
Function arguments are semantically evaluated left-to-right.

AEVAL-25
Method receivers are evaluated before method arguments.

AEVAL-26
Index base is evaluated before index expression.

AEVAL-27
Assignment evaluates the RHS before performing the destination write.

AEVAL-28
Assignment expressions have type unit.

AEVAL-29
Chained C-style assignment expressions are not part of Core v1.

AEVAL-30
Compound assignment has explicit destination semantics.

AEVAL-31
Destination expressions are not evaluated as ordinary values merely to perform assignment.

AEVAL-32
Temporary values do not imply heap allocation.

AEVAL-33
Temporary ownership follows normal ownership semantics.

AEVAL-34
Temporary views obey capability lifetime rules.

AEVAL-35
Scope exit performs required deterministic cleanup.

AEVAL-36
Owning locals are dropped in reverse initialization order by default.

AEVAL-37
Early return performs required cleanup before function exit.

AEVAL-38
Break performs required cleanup before leaving its scope.

AEVAL-39
Continue performs required cleanup before starting the next iteration.

AEVAL-40
Result propagation performs required cleanup before returning.

AEVAL-41
Option propagation performs required cleanup before returning.

AEVAL-42
Panic-unwind performs required cleanup according to the selected panic profile.

AEVAL-43
Panic-abort does not require normal unwinding semantics.

AEVAL-44
Drop timing is semantic even when physical storage is optimized.

AEVAL-45
Drop may be eliminated only when its observable semantic effects are proven absent.

AEVAL-46
Resource-releasing Drop is observable and cannot be arbitrarily eliminated.

AEVAL-47
Pure/trivial cleanup may be optimized away when legal.

AEVAL-48
Return of an owning value transfers ownership rather than dropping the returned value.

AEVAL-49
Returned views preserve provenance and capability validity.

AEVAL-50
Returning a view to invalid local storage is rejected.

AEVAL-51
If conditions are evaluated before branch selection.

AEVAL-52
Only the selected if branch is evaluated.

AEVAL-53
Match scrutinees are evaluated before pattern selection.

AEVAL-54
Only the selected match branch is evaluated.

AEVAL-55
Loop conditions are evaluated according to the loop semantics.

AEVAL-56
For iteration uses the iterator protocol.

AEVAL-57
Iterator ownership and cleanup follow normal ownership semantics.

AEVAL-58
Break and continue are structured control-flow operations.

AEVAL-59
Arbitrary source-level goto is not part of safe Core v1.

AEVAL-60
MIR may contain arbitrary basic-block control-flow edges.

AEVAL-61
Source control flow is lowered into explicit MIR CFG.

AEVAL-62
Short-circuit && evaluates its right operand only when required.

AEVAL-63
Short-circuit || evaluates its right operand only when required.

AEVAL-64
Logical short-circuit operators are not arbitrary trait overloads.

AEVAL-65
Axiom has no C-style ternary operator in Core v1.

AEVAL-66
Axiom has no comma sequence operator in Core v1.

AEVAL-67
Observable effects are preserved in semantic order.

AEVAL-68
Pure computations may be reordered when dependencies permit.

AEVAL-69
I/O effects are observable.

AEVAL-70
Volatile operations are observable.

AEVAL-71
Atomic operations obey their specified atomic and ordering semantics.

AEVAL-72
Synchronization operations establish required ordering constraints.

AEVAL-73
Foreign calls are conservatively treated according to their FFI contracts.

AEVAL-74
External resource effects are observable.

AEVAL-75
Memory operations may be reordered when alias and effect analysis proves legality.

AEVAL-76
Unknown aliasing is never treated as independence.

AEVAL-77
Capability-derived no-alias facts may enable reordering.

AEVAL-78
Evaluation order is independent of optimization level.

AEVAL-79
Evaluation order is independent of target instruction selection.

AEVAL-80
Constant folding cannot bypass semantic type checking.

AEVAL-81
Dead-code elimination occurs only after semantic validation.

AEVAL-82
Unreachable source code remains subject to Complete Semantic Mode validation.

AEVAL-83
Configuration-eliminated code may be excluded according to @cfg semantics.

AEVAL-84
Integer overflow behavior is defined by numeric semantics rather than C-style signed-overflow UB.

AEVAL-85
Division exceptional cases have defined language semantics.

AEVAL-86
Never expressions create non-returning control-flow edges.

AEVAL-87
Return transfers control after required cleanup.

AEVAL-88
Panic is distinct from recoverable Result/Option propagation.

AEVAL-89
No exception-based hidden control flow exists in Core v1.

AEVAL-90
Control-flow semantics are independent of physical stack layout.

AEVAL-91
Scope is a semantic lifetime concept, not necessarily a physical stack frame.

AEVAL-92
Temporary lifetime does not imply physical materialization.

AEVAL-93
Ownership transitions are preserved when evaluation is lowered.

AEVAL-94
Capability conflicts cannot be bypassed through evaluation ordering.

AEVAL-95
Evaluation ordering cannot manufacture alias independence.

AEVAL-96
Effect information is attached to semantic operations.

AEVAL-97
MIR preserves required semantic evaluation dependencies.

AEVAL-98
Optimization passes must preserve AEVAL semantics.

AEVAL-99
The semantic oracle defines observable evaluation behavior.

AEVAL-100
No optimizer transformation may change observable program behavior.
```

---

# 101. Một quyết định rất đáng chú ý

Axiom hiện đang có một mô hình khá đẹp:

```text
SOURCE
  │
  │ deterministic semantics
  ▼
HIR
  │
  │ explicit evaluation dependencies
  ▼
MIR
  │
  │ proof of independence
  ▼
OPTIR
  │
  │ aggressive reordering
  ▼
MACHINE CODE
```

Nghĩa là programmer có thể reasoning theo một model đơn giản:

> **Mọi thứ xảy ra theo thứ tự rõ ràng.**

Trong khi compiler vẫn có quyền làm:

```text
inline
reorder
CSE
LICM
vectorize
parallelize
fuse
eliminate
```

nếu chứng minh được không thay đổi observable semantics.

Đây chính là cách tránh cả hai cực:

```text
C/C++:
quá nhiều behavior phụ thuộc subtle UB/compiler rules

Java/C#/GC languages:
runtime semantics nặng hơn cần thiết

Axiom:
deterministic semantic model
+
aggressive proof-based optimization
```

---

## TASK TIẾP THEO

### **BOOTSTRAP-244 — AXIOM PLACE MODEL, LVALUE/RVALUE SEMANTICS & MEMORY ACCESS LOWERING**

Đây là task rất quan trọng để nối 243 với MIR/ownership.

Nó sẽ giải quyết chính xác:

```text
value
place
temporary
field
index
slice
view
mut_view
load
store
move
copy
address-taking
raw pointer
place projection
partial move
partial initialization
write destination
read source
```

Đặc biệt sẽ đóng băng **Place Model**:

```text
x
x.field
x[i]
x[start:end]
...
```

được compiler biểu diễn như thế nào mà **programmer không cần `&`, `*`, `&mut`, lifetime**, nhưng compiler vẫn có đủ thông tin để làm ownership, alias analysis, register allocation và machine-code generation.

Đây gần như là mảnh ghép cuối để Axiom có một mô hình bộ nhớ **mạnh như systems language nhưng không bắt programmer “vật lộn” với pointer/reference**.