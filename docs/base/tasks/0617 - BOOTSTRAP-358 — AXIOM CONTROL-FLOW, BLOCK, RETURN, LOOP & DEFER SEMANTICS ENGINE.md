# BOOTSTRAP-358 — AXIOM CONTROL-FLOW, BLOCK, RETURN, LOOP & DEFER SEMANTICS ENGINE

Sau Expression → Closure → Function/Call, bước tiếp theo là đóng băng **control-flow semantics**. Đây là lớp quyết định chính xác chương trình chạy theo thứ tự nào, giá trị nào còn sống, điểm nào có thể thoát function, và cleanup nào bắt buộc xảy ra.

Mục tiêu:

> **Control flow phải đơn giản ở source, nhưng MIR phải biểu diễn được chính xác mọi đường đi mà không cần suy đoán lại semantics.**

---

## 1. Control-flow model

Axiom Core có các control-flow primitive:

```text
block
if
match
loop
while
for
break
continue
return
defer
panic
```

Trong đó:

- `if`, `loop`, `return` là language control flow;
- `match` được xử lý bởi Pattern Engine;
- `for` là iteration syntax;
- `defer` là deterministic cleanup scheduling;
- `panic` là exceptional control flow nhưng không phải exception object model.

Tất cả cuối cùng được lower về CFG/MIR.

---

# 2. Block expression

Block là expression:

```text
{
    let a = 10;
    let b = 20;
    a + b
}
```

có type:

```text
i32
```

Giá trị cuối cùng là block result.

Nếu block kết thúc bằng:

```text
;
```

thì kết quả là:

```text
unit
```

Ví dụ:

```text
{
    foo();
}
```

→ `unit`.

---

# 3. Block không tạo runtime object

Block chỉ tạo:

```text
lexical scope
control-flow region
lifetime region
```

Không có:

```text
block object
scope object
runtime environment
```

Compiler có thể hoàn toàn eliminate block.

---

# 4. Scope và lifetime

Ví dụ:

```text
{
    let x = Resource();
    use(x);
}

use(x);
```

`x` kết thúc semantic lifetime khi block kết thúc.

Compiler phải schedule:

```text
DROP(x)
```

trước khi flow rời block.

Không phụ thuộc block có được inline hay không.

---

# 5. `if` expression

```text
let x = if condition {
    10
} else {
    20
};
```

hai nhánh phải có type tương thích.

Ví dụ:

```text
if condition {
    10
} else {
    20
}
```

→ `i32`.

Nhưng:

```text
if condition {
    10
} else {
    "hello"
}
```

là type error nếu không có một common type hợp lệ.

Axiom không tự tạo `Any` để giải quyết.

---

# 6. `if` không bắt buộc else

Statement context:

```text
if condition {
    do_work();
}
```

→ `unit`.

Expression context:

```text
let x = if condition {
    10
};
```

không hợp lệ nếu không có semantics xác định giá trị khi false.

Điều này tránh implicit `null`.

---

# 7. Condition type

`if` yêu cầu:

```text
bool
```

Axiom không có C-style truthiness mặc định:

```text
if 1
if pointer
if string
```

không hợp lệ.

Muốn kiểm tra phải viết rõ:

```text
if x != 0
```

hoặc API predicate.

---

# 8. Short-circuit

Đã frozen ở Expression Engine:

```text
a && b
a || b
```

luôn lazy.

CFG tương ứng:

```text
evaluate a
   ↓
branch
 ┌─┴─────┐
false   true
 ↓       ↓
result  evaluate b
          ↓
        result
```

Optimizer có thể simplify nếu proof hợp lệ.

---

# 9. `loop`

Core primitive:

```text
loop {
    work();
}
```

là infinite loop về mặt control flow nếu không có exit.

Compiler không coi nó là implicit function recursion.

---

# 10. `break`

```text
loop {
    if done {
        break;
    }

    work();
}
```

`break` chuyển control flow tới loop exit.

Nếu loop là expression:

```text
let x = loop {
    if ready {
        break value;
    }
};
```

thì `x` nhận giá trị từ `break`.

---

# 11. Loop result typing

Ví dụ:

```text
let x = loop {
    if condition {
        break 42;
    }
};
```

→ `x: i32`.

Nhưng:

```text
loop {
    if a {
        break 1;
    }

    if b {
        break "hello";
    }
}
```

→ type error vì break values không thống nhất.

Nếu loop không bao giờ break:

```text
loop {
    work();
}
```

type:

```text
never
```

hoặc equivalent divergent type.

---

# 12. `continue`

```text
loop {
    if skip {
        continue;
    }

    work();
}
```

`continue` chuyển tới loop continuation point.

Compiler phải biết rõ:

```text
continue_target
```

để Drop/Defer chạy đúng.

---

# 13. Cleanup trước `break`

Ví dụ:

```text
loop {
    let resource = acquire();

    if done {
        break;
    }

    use(resource);
}
```

`break` phải cleanup:

```text
DROP(resource)
```

trước khi ra khỏi block.

Không thể jump trực tiếp qua cleanup.

MIR phải biểu diễn:

```text
break
 ↓
cleanup block
 ↓
loop exit
```

---

# 14. Cleanup trước `continue`

Tương tự:

```text
loop {
    let resource = acquire();

    if skip {
        continue;
    }
}
```

phải:

```text
DROP(resource)
→ continue target
```

---

# 15. `return`

```text
return value;
```

là function-exit control flow.

Trước return, compiler phải thực hiện cleanup của tất cả scope cần thoát.

Ví dụ:

```text
fn foo() {
    let a = A();
    {
        let b = B();
        return result;
    }
}
```

cleanup:

```text
DROP(b)
DROP(a)
RETURN(result)
```

theo reverse initialization order.

---

# 16. Return value và cleanup

Return value phải được materialize trước khi cleanup có thể invalidate nguồn của nó.

Ví dụ:

```text
return make_value();
```

không có vấn đề.

Nhưng:

```text
return obj.field;
```

compiler phải đảm bảo semantics của value extraction trước khi `obj` bị Drop.

Đây là một lý do MIR cần distinction:

```text
Move
Copy
Borrow/View
```

trước cleanup.

---

# 17. Diverging expression

Axiom có type:

```text
never
```

cho expression không bao giờ hoàn thành bình thường:

```text
panic(...)
return ...
loop {...}
```

Ví dụ:

```text
let x: i32 = if condition {
    42
} else {
    panic("error")
};
```

hợp lệ vì:

```text
join(i32, never) = i32
```

---

# 18. `never` không phải `unit`

Phân biệt:

```text
unit
```

= function/block hoàn thành nhưng không trả dữ liệu.

```text
never
```

= control flow không tiếp tục.

Điều này rất quan trọng cho type checking.

---

# 19. `panic`

Axiom không có exception object model trong Core.

```text
panic("invalid state");
```

là divergent control flow.

Profile có thể:

```text
abort
unwind
```

nhưng source semantics vẫn xác định:

```text
normal continuation = impossible
```

---

# 20. `panic` không phải `Result`

```text
Result<T, E>
```

là recoverable control flow.

```text
panic
```

là unrecoverable/error-runtime control flow.

Không tự động convert:

```text
panic → Err
```

hoặc:

```text
Err → panic
```

---

# 21. `defer`

Axiom nên có `defer` ở Core vì nó giải quyết cleanup/rollback cực kỳ hữu ích mà không cần exception-centric model.

Ví dụ:

```text
fn process() {
    let file = open();

    defer {
        file.close();
    }

    work();
}
```

Semantic:

> block `defer` được đăng ký tại điểm execution và chạy khi control flow rời khỏi scope tương ứng.

---

# 22. Defer không phải Drop

Đây là distinction quan trọng.

`Drop`:

```text
type-level ownership cleanup
```

`defer`:

```text
scope-level control-flow cleanup
```

Ví dụ:

```text
let x = Resource();

defer {
    log("finished");
}
```

`defer` không thay thế Drop.

---

# 23. Defer execution order

Nếu:

```text
defer A;
defer B;
defer C;
```

thì khi scope thoát:

```text
C
B
A
```

tức:

> LIFO registration order.

Điều này phù hợp với nested resource acquisition.

---

# 24. Defer capture

Ví dụ:

```text
let x = resource();

defer {
    close(x);
}
```

`defer` phải capture semantic dependency vào `x`.

Compiler phải bảo đảm `x` còn hợp lệ khi defer chạy.

Không được:

```text
DROP(x)
...
defer uses x
```

nếu defer chạy sau Drop.

---

# 25. Defer và move

Ví dụ:

```text
let x = Resource();

defer {
    use(x);
}

consume(x);
```

Compiler phải phát hiện conflict:

```text
x moved
+
defer still requires x
```

Diagnostic phải chỉ ra:

```text
x is captured by deferred cleanup
therefore the later move is invalid
```

---

# 26. Defer và return

```text
fn foo() {
    defer cleanup();
    return value;
}
```

semantic:

```text
evaluate value
run defer
return value
```

Nếu defer thay đổi global state, observable semantics phải phản ánh điều đó.

---

# 27. Defer và panic

Nếu profile `unwind`:

```text
panic()
```

phải chạy cleanup/defer theo unwind contract.

Nếu profile `abort`:

```text
panic()
```

có thể terminate ngay theo runtime policy.

Do đó `defer` semantics phải gắn với panic profile.

---

# 28. Defer không được suspend

Để tránh một hệ thống async phức tạp, Core rule:

```text
defer {
    await foo();
}
```

không hợp lệ.

Cleanup trong defer phải synchronous.

Nếu cần async cleanup:

```text
await resource.close_async();
```

phải được gọi explicitly trước khi scope kết thúc.

Không có:

```text
AsyncDrop
```

trong Core.

---

# 29. Loop lowering

`while`:

```text
while condition {
    body
}
```

được lower thành:

```text
loop {
    if !condition {
        break;
    }

    body;
}
```

`for` cũng nên là syntax layer dựa trên iterator protocol/library semantics.

Core MIR cuối cùng không cần giữ `while`/`for`.

---

# 30. `for`

Ví dụ:

```text
for item in collection {
    process(item);
}
```

semantic resolution tạo:

```text
iterator = IntoIterator::into_iter(collection)
```

sau đó:

```text
loop {
    match iterator.next() {
        Some(item) => process(item),
        None => break,
    }
}
```

Pattern Engine xử lý destructuring.

Expression Engine xử lý calls.

Control-flow Engine xử lý loop.

---

# 31. Iterator ownership

`for` phải tôn trọng ownership.

```text
for item in collection
```

có thể consume collection.

Trong khi:

```text
for item in view(collection)
```

chỉ đọc.

Không có implicit copying cả collection chỉ để iterate.

---

# 32. Loop variable lifetime

```text
for item in collection {
    use(item);
}
```

`item` là binding mới mỗi iteration semantic.

Nếu `item` là non-Copy value:

```text
item
```

có thể được move từ iterator.

Compiler không tạo hidden clone.

---

# 33. Loop labels

Axiom nên hỗ trợ label rõ ràng:

```text
'outer: loop {
    loop {
        if done {
            break 'outer;
        }
    }
}
```

Nhưng label chỉ là compile-time control-flow identity.

Không phải runtime string.

---

# 34. `break value` và nested loop

Ví dụ:

```text
let result = 'search: loop {
    for item in items {
        if found(item) {
            break 'search item;
        }
    }
};
```

Compiler phải resolve:

```text
target loop = search
result type = item type
```

và cleanup mọi scope nằm giữa break site và target.

---

# 35. CFG representation

Control-flow HIR/MIR sử dụng explicit basic blocks:

```text id="wdyq5p"
BasicBlock {
    id
    statements[]
    terminator
}
```

Terminator:

```text id="3f7e7s"
Goto
Branch
Switch
Call
Return
Unreachable
Invoke/Unwind
```

Không để nested AST control flow tồn tại tới backend.

---

# 36. Cleanup CFG

Compiler tạo cleanup regions:

```text id="1h1c0e"
NormalExit
BreakExit
ContinueExit
ReturnExit
PanicExit
UnwindExit
```

Mỗi exit được route qua các cleanup cần thiết.

Ví dụ:

```text id="8r2bcr"
body
 ↓
return
 ↓
defer cleanup
 ↓
drop b
 ↓
drop a
 ↓
return
```

---

# 37. Cleanup ordering

Mặc định:

```text id="d52j9v"
defer blocks
+
owned locals
```

phải có ordering xác định.

Đề xuất:

```text id="m2g7b1"
1. Materialize return value
2. Execute defers in reverse registration order
3. Drop locals/resources in reverse initialization order
4. Leave scope
```

Nếu một defer phụ thuộc vào resource, compiler phải bảo đảm dependency ordering; không được chỉ áp dụng một thứ tự text-based mù quáng.

---

# 38. Drop/defer dependency graph

Thay vì chỉ có stack cleanup đơn giản, compiler nên xây:

```text id="2w6c8d"
CleanupGraph
```

Ví dụ:

```text id="k1i4f9"
defer C → requires X
Drop X
```

Compiler biết:

```text C must execute before Drop X
```

Nếu programmer tạo dependency không hợp lệ:

```text id="m3o2ag"
defer uses moved/dropped resource
```

→ compile error.

Điều này mạnh hơn một cleanup stack đơn giản.

---

# 39. No hidden cleanup on arbitrary jumps

Mọi control-flow edge:

```text id="z3cz5j"
break
continue
return
panic
goto-like internal edge
```

nếu có thể vượt scope boundary phải đi qua cleanup elaboration.

Compiler không cho phép một edge "nhảy xuyên" Drop/Defer.

---

# 40. `goto`

Axiom Core **không nên có programmer-facing arbitrary `goto`**.

Lý do:

- phá structured ownership;
- làm cleanup graph khó hiểu;
- gây khó khăn cho compiler proof;
- không cần thiết cho performance.

Compiler IR vẫn có:

```text id="7ps1l9"
Goto
```

nhưng source-level `goto` không thuộc safe Core.

Nếu cần machine-level control flow:

```text id="c4x7qn"
unsafe/system
```

có thể có một escape hatch riêng.

---

# 41. Structured control flow

Core source control flow:

```text id="8y2g1f"
if
match
loop
while
for
break
continue
return
```

đủ để biểu diễn structured programs.

Compiler vẫn có CFG tự do bên dưới.

---

# 42. Unreachable code

Ví dụ:

```text
return;

foo();
```

`foo()` unreachable.

Compiler nên cảnh báo:

```text
AXM-W358-001
unreachable code
```

nhưng warning policy không được biến thành semantic difference.

Nếu code có side-effect nhưng unreachable, nó không thực thi.

---

# 43. Reachability analysis

Control-flow engine tính:

```text id="8qk5j9"
Reachable
Unreachable
MaybeReachable
Divergent
```

Thông tin này phục vụ:

- exhaustiveness;
- dead-code elimination;
- ownership verification;
- Drop insertion;
- diagnostics.

---

# 44. Definite initialization

Control-flow phải tích hợp initialization analysis.

Ví dụ:

```text
let x: i32;

if condition {
    x = 10;
}

use(x);
```

Compiler thấy:

```text
condition == true  → initialized
condition == false → uninitialized
```

→ reject.

Nhưng:

```text
if condition {
    x = 10;
} else {
    x = 20;
}

use(x);
```

→ valid.

---

# 45. Move analysis across branches

Ví dụ:

```text
let x = Resource();

if condition {
    consume(x);
}

use(x);
```

Compiler phải reject nếu branch có thể consume `x`.

State join:

```text
Owned
+
Moved
=
Partially/ConditionallyMoved
```

không thể coi là Owned.

---

# 46. Drop analysis across branches

Ví dụ:

```text
let x = Resource();

if condition {
    drop(x);
}
```

Sau `if`, compiler phải biết:

```text
x may be Dropped
```

và không được Drop lần nữa.

Đây là lý do ownership state phải tích hợp CFG join.

---

# 47. Loop fixed-point

Ownership/control-flow analysis trên loop phải đạt fixed point.

Ví dụ:

```text
loop {
    if condition {
        break;
    }

    mutate(x);
}
```

Compiler phải chứng minh trạng thái `x` ổn định qua back-edge.

Không được chỉ phân tích một lần theo source order.

---

# 48. Control-flow effect

Mỗi expression/block có:

```text id="c0b1km"
ControlFlowEffect {
    MayReturn
    MayBreak
    MayContinue
    MayPanic
    MaySuspend
    NeverReturns
}
```

Điều này giúp các compiler pass khác không phải phân tích AST lại.

---

# 49. CompilerDB bổ sung

Task này thêm:

```text id="2p7xub"
ControlFlowDB
BlockDB
LoopDB
BranchDB
BreakDB
ContinueDB
ReturnDB
DeferDB
CleanupDB
CleanupGraphDB
ReachabilityDB
DefiniteInitDB
ControlFlowEffectDB
LabelDB
UnwindDB
```

Query:

```text id="x5kq3e"
build_cfg(FunctionId)
resolve_break(BreakId)
resolve_continue(ContinueId)
resolve_return(ReturnId)
analyze_reachability(FunctionId)
build_cleanup_graph(FunctionId)
analyze_defer(FunctionId)
analyze_definite_init(FunctionId)
analyze_control_flow_effect(ExprId)
```

---

# 50. HIR

```text id="7d0l2w"
HirBlock
HirIf
HirLoop
HirBreak
HirContinue
HirReturn
HirDefer
HirPanic
```

Nhưng sau lowering, MIR chỉ còn CFG primitives.

---

# 51. MIR cleanup representation

Có thể dùng:

```text id="i9s3a4"
CLEANUP_SCOPE_ENTER
CLEANUP_SCOPE_EXIT
DEFER_REGISTER
DROP
```

Sau cleanup elaboration, các abstraction này được biến thành explicit CFG.

Ví dụ:

```text id="e7lqf0"
return value
```

→

```text id="6g0z4h"
tmp_return = value

goto cleanup_1

cleanup_1:
    execute_defer_C
    goto cleanup_2

cleanup_2:
    drop x
    goto return_block

return_block:
    return tmp_return
```

Sau đó optimizer có thể simplify toàn bộ graph.

---

# 52. Zero-cost requirement

`defer` không được mặc định tạo runtime stack object.

Ví dụ:

```text id="3vuj9g"
defer close(file);
```

có thể compile thành:

```text id="p3s1v4"
direct cleanup call
```

Nếu compiler chứng minh cleanup không cần:

```text id="4shy2e"
dead-code elimination
```

có thể loại bỏ.

---

# 53. Invariants

Đóng băng:

```text id="a0i1bj"
ACF-01  Every executable function has an explicit control-flow graph.

ACF-02  Evaluation order is deterministic.

ACF-03  Blocks create lexical and lifetime scopes but no mandatory runtime objects.

ACF-04  Block result type is explicitly resolved.

ACF-05  `if` conditions require bool.

ACF-06  Expression `if` requires compatible branch result types.

ACF-07  `never` can inhabit any compatible control-flow join.

ACF-08  `unit` and `never` are distinct semantic types.

ACF-09  Every break targets exactly one resolved loop.

ACF-10  Every continue targets exactly one resolved loop.

ACF-11  Loop break values have one resolved result type.

ACF-12  Return always executes required scope cleanup.

ACF-13  Break always executes crossed-scope cleanup.

ACF-14  Continue always executes crossed-scope cleanup.

ACF-15  Defer executes in reverse registration order.

ACF-16  Defer is distinct from Drop.

ACF-17  Defer cannot implicitly suspend.

ACF-18  Deferred code cannot access invalid or already-moved state.

ACF-19  Drop order is deterministic.

ACF-20  No source-level control-flow edge may bypass required cleanup.

ACF-21  Arbitrary source-level `goto` is not part of Safe Core.

ACF-22  Unreachable code cannot affect runtime behavior.

ACF-23  Definite initialization is path-sensitive.

ACF-24  Move state is path-sensitive.

ACF-25  Drop state is path-sensitive.

ACF-26  Loop analysis reaches a fixed point.

ACF-27  Control-flow effects are explicit compiler facts.

ACF-28  Panic behavior participates in cleanup semantics according to profile.

ACF-29  Cleanup elaboration occurs before final ownership verification.

ACF-30  Control-flow lowering preserves ownership, capability, effect and evaluation-order semantics.
```

---

## 54. Kiến trúc sau BOOTSTRAP-358

Axiom hiện có chuỗi front-end rất rõ:

```text
Source
  ↓
Parser
  ↓
Module / Name Resolution
  ↓
Type / Trait Resolution
  ↓
Expression / Operator Resolution
  ↓
Closure / Capture Analysis
  ↓
Function / Call Resolution
  ↓
★ Control Flow + Cleanup Elaboration
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership
Capability
Effect
Escape
Concurrency
  ↓
Verified MIR
```

Điểm đáng chú ý nhất của task này là **Drop, defer, return, break, continue không còn là những cơ chế rời rạc**. Chúng đều đi qua một **Cleanup Graph** chung.

Nhờ vậy Axiom có thể giữ được cả ba mục tiêu cùng lúc:

```text
syntax đơn giản
        +
deterministic resource management
        +
zero-cost compiled cleanup
```

mà không cần GC, exception object, hidden reference counting hay programmer-written lifetime annotations.