# BOOTSTRAP-356 — AXIOM CLOSURE, LAMBDA & CAPTURE ANALYSIS ENGINE

Đây là bước tiếp theo sau Expression Resolution. Mục tiêu là biến closure/lambda thành một abstraction **zero-cost**, trong đó programmer viết rất ngắn nhưng compiler tự quyết định capture, ownership, layout, lifetime, Send/Share và khả năng stack/register/heap elimination.

---

## 1. Triết lý

Axiom không coi closure là một "object runtime".

```text
let f = |x| x + offset
```

về semantic chỉ là:

```text
callable value
+
captured environment
```

Compiler được phép biến nó thành:

```text
struct Closure_17 {
    offset: i32
}

fn Closure_17_call(self: view<Closure_17>, x: i32) -> i32 {
    x + self.offset
}
```

hoặc thậm chí loại bỏ hoàn toàn environment nếu có thể inline.

Không có mặc định:

- heap allocation;
- GC;
- object header;
- vtable;
- reference counting;
- dynamic dispatch.

---

# 2. Closure là một kiểu anonymous compile-time

Mỗi closure có một anonymous type duy nhất:

```text
let a = |x| x + 1;
let b = |x| x + 1;
```

`a` và `b` **không cùng một nominal closure type**, dù source giống nhau.

Compiler tạo:

```text
ClosureTypeId(a)
ClosureTypeId(b)
```

Điều này giúp:

- monomorphization;
- layout tối ưu;
- capture analysis;
- static dispatch.

---

# 3. Closure signature

Closure:

```text
|x: i32, y: i32| x + y
```

có semantic signature:

```text
(i32, i32) -> i32
```

Compiler lưu:

```text
ClosureSignature {
    params
    return_type
    effects
    async
    unsafe
}
```

Closure có thể là:

```text
sync
async
unsafe
comptime
```

nhưng các thuộc tính này không được suy đoán mơ hồ.

---

# 4. Capture analysis

Ví dụ:

```text
let offset = 10;

let f = |x| x + offset;
```

Compiler phát hiện:

```text
free_variables = { offset }
```

Sau đó xác định capture mode.

Các mode semantic:

```text
READ
MUTATE
MOVE
```

Không yêu cầu programmer viết:

```text
|&offset|
|&mut offset|
|move offset|
```

trong Core.

---

# 5. Capture READ

```text
let offset = 10;

let f = |x| x + offset;
```

`offset` chỉ được đọc.

Compiler có thể tạo:

```text
Closure {
    offset: i32
}
```

hoặc tối ưu thành:

```text
constant 10
```

nếu capture thực tế không cần thiết.

---

# 6. Capture MOVE

Ví dụ:

```text
let buffer = make_buffer();

let f = || consume(buffer);
```

Nếu closure cần sở hữu `buffer`, compiler xác định:

```text
capture(buffer, MOVE)
```

Sau khi closure được tạo:

```text
buffer
```

không còn usable bên ngoài.

Semantics này được kiểm tra bằng Ownership Analysis.

---

# 7. Capture MUTATE

Ví dụ:

```text
let count = 0;

let f = || {
    count += 1;
};
```

Compiler phát hiện closure cần:

```text
WRITE(count)
```

và phải bảo đảm closure có exclusive capability phù hợp.

Nếu closure tồn tại đồng thời với code khác vẫn truy cập `count`, compiler phải phát hiện conflict.

Không được âm thầm tạo shared mutable reference.

---

# 8. Capture analysis dựa trên USE, không dựa trên syntax

Ví dụ:

```text
let x = large_object();

let f = || {
    use_only(x.field);
};
```

Compiler không nhất thiết phải capture toàn bộ `x`.

Có thể capture:

```text
x.field
```

nếu ownership/layout/provenance cho phép.

Đây là **field-sensitive capture**.

Mục tiêu:

```text
capture_size ↓
register_pressure ↓
cache_pressure ↓
```

---

# 9. Partial capture

Ví dụ:

```text
struct Data {
    a: i64,
    b: i64,
    c: i64
}

let d = Data(...);

let f = || d.a;
```

Compiler có thể biểu diễn environment:

```text
Closure {
    d.a
}
```

thay vì:

```text
Closure {
    d
}
```

nhưng chỉ khi không phá ownership semantics của `d`.

Nếu `d` có custom Drop hoặc invariant phụ thuộc toàn object, compiler phải giữ semantic ownership phù hợp.

---

# 10. Closure environment không phải object

Closure environment:

```text
ClosureEnv
```

là compiler-generated aggregate.

Không có:

```text
object header
class metadata
runtime type id
GC metadata
```

trừ khi programmer **explicitly** chuyển closure sang dynamic callable abstraction.

---

# 11. Static dispatch mặc định

Ví dụ:

```text
fn apply<T>(f: T, x: i32) -> i32
where T: Fn(i32) -> i32
{
    f(x)
}
```

Compiler mặc định monomorphize:

```text
apply<Closure_17>
```

Do đó call có thể trở thành direct call/inlining.

Không tạo:

```text
virtual_call
```

---

# 12. Dynamic callable

Nếu cần runtime polymorphism, programmer phải yêu cầu explicit abstraction:

```text
dyn Fn(i32) -> i32
```

Lúc này compiler có thể tạo:

```text
data_pointer
call_pointer
```

hoặc representation tương đương.

Dynamic dispatch là semantics explicit.

---

# 13. Closure → Function Pointer

Closure **không tự động** convert thành function pointer nếu nó capture state.

Ví dụ:

```text
let offset = 10;

let f = |x| x + offset;
```

không thể:

```text
fn_ptr = f
```

vì function pointer không chứa environment.

Một closure không capture:

```text
let f = |x: i32| x * 2;
```

có thể decay thành function pointer khi ABI yêu cầu.

---

# 14. Closure → `dyn Fn`

Conversion này tạo dynamic callable representation.

Ví dụ:

```text
let f = |x| x + offset;

let callback: dyn Fn(i32) -> i32 = f;
```

Compiler tạo explicit erased representation.

Điều này có thể:

- yêu cầu storage;
- tạo dispatch metadata;
- thay đổi calling convention.

Vì vậy không được xảy ra implicit.

---

# 15. Closure lifetime

Closure có thể giữ captured values.

Ví dụ:

```text
let x = make_buffer();

let f = || use(x);
```

Nếu closure sống lâu hơn scope ban đầu, `x` phải được move vào closure hoặc có storage contract thích hợp.

Compiler không cho phép:

```text
closure sống lâu
+
capture borrowed local
```

nếu local đã hết lifetime.

Nhưng programmer không phải viết lifetime annotation.

Compiler tự giải bài toán.

---

# 16. Closure escape analysis

Compiler phân loại closure:

```text
NoEscape
LocalEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
```

Ví dụ:

```text
fn foo() {
    let x = 10;

    let f = |y| x + y;

    f(20);
}
```

Closure có:

```text
NoEscape
```

Compiler có thể loại bỏ hoàn toàn closure object.

Có thể biến thành:

```text
inline arithmetic
```

---

# 17. Return closure

Ví dụ:

```text
fn make_adder(x: i32) {
    return |y| x + y;
}
```

Closure phải mang `x`.

Compiler có thể tạo:

```text
Adder {
    x: i32
}
```

và return theo ABI phù hợp.

Không bắt buộc heap allocation.

ABI có thể dùng:

```text
register return
caller-allocated return
stack return
aggregate return
```

tùy target.

---

# 18. Closure capture và ownership

Ví dụ:

```text
let x = Resource();

let f = || use(x);
```

Nếu `use(x)` yêu cầu move:

```text
capture(x, MOVE)
```

Nếu chỉ đọc:

```text
capture(x, READ)
```

Nếu mutate:

```text
capture(x, MUTATE)
```

Capture analysis phải chạy **trước** final ownership verification nhưng sử dụng cùng semantic model.

---

# 19. Closure creation có thể consume biến

Ví dụ:

```text
let buffer = Buffer(...);

let f = || consume(buffer);

consume(buffer);
```

phải lỗi vì:

```text
buffer
```

đã được move vào closure.

Diagnostic:

```text
AXM-E356-001

`buffer` was moved into closure `Closure_17`
at this expression.

Later use is invalid.
```

---

# 20. Closure và `mut_view`

Ví dụ:

```text
let data = ...;

let f = || {
    mutate(data);
};
```

Nếu capture cần exclusive capability:

```text
mut_view(data)
```

compiler phải giữ capability đến đúng lifetime của closure.

Do đó:

```text
mutate(data)
```

ở bên ngoài trong thời gian closure còn active có thể bị reject.

Đây là cách Axiom giữ memory safety mà không cần programmer viết:

```text
&mut
```

---

# 21. Closure và multiple captures

Ví dụ:

```text
let a = ...
let b = ...

let f = || {
    use(a);
    mutate(b);
}
```

Environment có semantic:

```text
READ(a)
WRITE(b)
```

Hai capture được kiểm tra độc lập.

Nếu:

```text
a
```

và

```text
b
```

là hai field disjoint của cùng struct, compiler có thể cho phép.

---

# 22. Closure và Send

Closure có thể được `Send` nếu:

```text
all captured state: Send
+
closure execution semantics: Send-compatible
```

Ví dụ:

```text
let file = File(...);

spawn(|| use(file));
```

Compiler kiểm tra closure environment.

Không cần programmer thêm:

```text
impl Send for Closure
```

---

# 23. Closure và Share

Closure chỉ `Share` nếu toàn bộ captured state đáp ứng Share semantics.

Một closure capture:

```text
Arc<Atomic<i32>>
```

có thể Share.

Closure capture:

```text
mut_view<T>
```

thường không thể Share.

Compiler không suy luận Share chỉ vì closure syntax trông "read-only".

---

# 24. Async closure

Axiom hỗ trợ:

```text
let f = async |x| {
    await something(x)
};
```

Semantic:

```text
Closure
+
Future-producing callable
```

Capture analysis phải xác định biến nào sống qua suspension point.

Ví dụ:

```text
let buffer = make_buffer();

let f = async || {
    use(buffer);
    await io();
    use(buffer);
};
```

`buffer` phải trở thành state của Future.

---

# 25. Async closure state minimization

Không phải toàn bộ closure environment phải sống qua `.await`.

Compiler phân tích:

```text
before await
after await
```

Nếu:

```text
x
```

không được dùng sau await:

```text
x
```

không cần trở thành Future state.

Pipeline:

```text
Closure Capture Analysis
        ↓
Async Liveness
        ↓
State Field Selection
        ↓
Coroutine Lowering
```

---

# 26. Closure recursion

Closure tự tham chiếu:

```text
let f = || f();
```

không được compiler tự động tạo infinite-sized closure.

Các trường hợp recursive closure cần explicit indirection/handle hoặc named function.

Ví dụ khuyến nghị:

```text
fn recurse(...) { ... }
```

Nếu cần dynamic recursive callable:

```text
dyn Fn(...)
```

hoặc một library indirection.

---

# 27. Closure identity

Closure identity **không phải runtime object identity**.

Hai closure:

```text
let a = |x| x + 1;
let b = |x| x + 1;
```

không được so sánh bằng `==` mặc định.

Không có implicit equality cho closure.

Chỉ có:

```text
callability
capture state
type identity
```

---

# 28. Closure layout

Compiler được tự do layout:

```text
Closure {
    capture_a
    capture_b
    capture_c
}
```

có thể:

- reorder fields;
- pack;
- eliminate fields;
- scalarize;
- split environment;
- place values in registers.

Trừ khi closure được đưa qua một ABI có layout contract.

Closure layout không phải public ABI mặc định.

---

# 29. Closure optimization

Các optimization quan trọng:

```text
ClosureInlining
ClosureEnvironmentElimination
CaptureMinimization
CaptureScalarReplacement
ClosureSpecialization
ClosureDeduplication
LambdaConstantPropagation
NonEscapingClosureElimination
ClosureCallDevirtualization
ClosureDeadCaptureElimination
```

Ví dụ:

```text
let f = |x| x + 10;
let y = f(20);
```

có thể trở thành:

```text
y = 30;
```

không tồn tại closure ở binary.

---

# 30. Closure ABI

Có ba trường hợp:

### Static closure

```text
T: Fn(...)
```

ABI:

```text
closure environment
+
direct function
```

thường được tối ưu hoàn toàn.

### Function pointer

```text
fn(i32) -> i32
```

ABI chỉ có code pointer.

### Dynamic callable

```text
dyn Fn(i32) -> i32
```

ABI chứa erased callable representation.

Ba loại này phải được phân biệt rõ.

---

# 31. CompilerDB bổ sung

Task này thêm:

```text
ClosureDB
ClosureTypeDB
ClosureCaptureDB
ClosureEnvDB
ClosureCallDB
ClosureConversionDB
ClosureEscapeDB
ClosureLayoutDB
ClosureSendShareDB
ClosureAsyncDB
ClosureOptimizationDB
LambdaDB
CallableDB
FnTraitDB
```

Query:

```text
analyze_closure(ClosureId)
capture_set(ClosureId)
capture_mode(ClosureId, VariableId)
closure_type(ClosureId)
closure_signature(ClosureId)
closure_effect(ClosureId)
closure_escape(ClosureId)
closure_layout(ClosureId)
closure_send(ClosureId)
closure_share(ClosureId)
lower_closure(ClosureId)
```

---

# 32. HIR representation

Resolved closure:

```text
HirClosure {
    closure_id
    signature
    captures[]
    body
    effect
    async_info
}
```

Capture:

```text
ClosureCapture {
    source_place
    mode
    capability
    field_projection
}
```

---

# 33. MIR representation

Closure creation có thể hạ thành:

```text
MAKE_CLOSURE {
    function = Closure_17_call
    environment = [...]
}
```

nhưng đây là semantic MIR operation.

Optimizer có thể biến nó thành:

```text
function pointer
```

hoặc loại bỏ hoàn toàn.

---

# 34. Không để closure phá ownership model

Invariant quan trọng:

> Closure capture chỉ là một cách khác để giữ ownership/capability; nó không phải escape hatch khỏi ownership verifier.

Ví dụ:

```text
let f = || {
    raw_pointer_write(...)
};
```

Nếu unsafe:

```text
unsafe
```

thì closure vẫn phải được kiểm tra các semantic facts khác.

Unsafe không biến closure thành "compiler bỏ qua".

---

# 35. Closure + comptime

Closure có thể xuất hiện trong comptime:

```text
const VALUE = comptime {
    let f = |x| x * 2;
    f(20)
};
```

Closure ở đây tồn tại trong Comptime VM.

Compiler có thể hoàn toàn eliminate closure.

Không có runtime closure object được tạo chỉ vì closure xuất hiện trong comptime.

---

# 36. Closure + GPU

Closure mặc định không được phép trở thành GPU kernel callable.

GPU kernel có ABI riêng.

Nếu compiler cho phép device-side closure:

```text
@kernel
```

hoặc một cơ chế GPU-specific phải xác định:

```text
capture storage domain
capture address space
capture legality
capture layout
```

Không được implicit capture Host memory vào Device code.

---

# 37. Closure diagnostics

Ví dụ:

```text
AXM-E356-007

Closure captures `buffer` by move.

`buffer` is therefore unavailable after closure creation.

If shared ownership is intended, use an explicit shared-storage type.
```

Hoặc:

```text
AXM-E356-011

Closure cannot be sent to another execution domain.

Captured value:
    `state: LocalState`

Reason:
    LocalState is not Send.
```

Compiler nên hiển thị **capture dependency graph**, không chỉ một dòng lỗi.

---

# 38. Capture graph

Compiler xây:

```text
Closure
 ├── READ  a
 ├── MOVE  b
 ├── WRITE c.field
 └── READ  d.x
```

Sau đó chuyển thành capability requirements:

```text
READ(a)
MOVE(b)
WRITE(c.field)
READ(d.x)
```

Graph này được dùng bởi:

- ownership verifier;
- Send/Share;
- escape analysis;
- async lowering;
- optimizer;
- diagnostics.

---

# 39. Invariants

Đóng băng:

```text
ACLOS-01  Every closure has a unique compiler-generated closure type.

ACLOS-02  Closure types have no implicit runtime object header.

ACLOS-03  Capture mode is compiler-derived from actual use.

ACLOS-04  Capture cannot bypass ownership verification.

ACLOS-05  MOVE capture transfers ownership.

ACLOS-06  READ capture requires valid read capability.

ACLOS-07  MUTATE capture requires valid exclusive write capability.

ACLOS-08  Captured values remain valid for closure lifetime.

ACLOS-09  A closure cannot outlive captured storage.

ACLOS-10  Partial capture is permitted when ownership semantics remain valid.

ACLOS-11  Custom Drop may restrict partial capture.

ACLOS-12  Non-escaping closures may be completely eliminated.

ACLOS-13  Static closure dispatch is preferred by default.

ACLOS-14  Dynamic callable dispatch requires explicit dynamic abstraction.

ACLOS-15  Capturing closures cannot implicitly become plain function pointers.

ACLOS-16  Non-capturing closures may convert to compatible function pointers.

ACLOS-17  Closure Send is derived from captured state.

ACLOS-18  Closure Share is derived from captured state.

ACLOS-19  Closure cannot implicitly make non-Send state Send.

ACLOS-20  Closure cannot implicitly make mutable state shared.

ACLOS-21  Async closures obey await lifetime rules.

ACLOS-22  Values dead before await need not enter Future state.

ACLOS-23  Recursive closures require explicit finite indirection.

ACLOS-24  Closure identity is not runtime object identity.

ACLOS-25  Closure layout is compiler-controlled unless ABI explicitly freezes it.

ACLOS-26  Closure environment may be scalarized or eliminated.

ACLOS-27  Closure creation cannot implicitly allocate heap storage.

ACLOS-28  Closure in comptime does not imply runtime closure generation.

ACLOS-29  Host captures cannot implicitly cross GPU storage domains.

ACLOS-30  Closure lowering must preserve ownership, capability, effect and evaluation semantics.
```

---

## 40. Vị trí mới trong compiler

Pipeline hiện tại:

```text
Name Resolution
      ↓
Type / Trait Resolution
      ↓
Expression / Operator Resolution
      ↓
★ Closure / Lambda / Capture Analysis
      ↓
Async Analysis
      ↓
Pattern Lowering
      ↓
Typed HIR
      ↓
MIR
      ↓
Ownership + Capability Verification
```

Điểm quan trọng của thiết kế này là **closure không cần một runtime riêng**.

Một closure đơn giản:

```text
let f = |x| x + offset;
```

có thể cuối cùng biến thành đúng một hàm machine bình thường với `offset` truyền bằng register.

Một closure phức tạp có thể trở thành một aggregate.

Một closure dynamic mới cần erased callable representation.

Và nếu compiler chứng minh closure không cần tồn tại, **closure biến mất hoàn toàn khỏi binary**.