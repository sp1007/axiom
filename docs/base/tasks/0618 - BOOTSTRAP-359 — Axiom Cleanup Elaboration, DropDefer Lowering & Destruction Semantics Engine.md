# BOOTSTRAP-359 — Axiom Cleanup Elaboration, Drop/Defer Lowering & Destruction Semantics Engine

Đây là bước tiếp theo sau `BOOTSTRAP-358`. Mục tiêu của task này là biến các quy tắc `Drop`, `defer`, `return`, `break`, `continue`, `panic` thành **một cơ chế cleanup duy nhất ở compiler**, để sau này async, exception/unwind, closure, coroutine và optimizer không phải tự xử lý từng trường hợp riêng.

---

## 1. Mục tiêu

Axiom có nhiều cơ chế có thể làm scope kết thúc sớm:

```axiom
return x
break value
continue
panic(...)
```

và nhiều nguyên nhân cần cleanup:

```axiom
Drop<T>
defer { ... }
```

Compiler phải đảm bảo:

> **Mọi đường thoát khỏi scope đều đi qua đúng cleanup cần thiết, đúng thứ tự, đúng một lần.**

Đồng thời cleanup phải:

- deterministic;
- không double-drop;
- không drop moved value;
- không sử dụng capability đã hết hạn;
- không tạo hidden allocation;
- không tạo runtime overhead nếu có thể loại bỏ;
- hoạt động giống nhau ở debug/release;
- tương thích với async lowering;
- tương thích với panic abort/unwind;
- tối ưu được thành code máy trực tiếp.

---

# 2. Một Cleanup Model duy nhất

Không xây riêng:

```text
DropEngine
DeferEngine
ReturnCleanupEngine
PanicCleanupEngine
```

mà compiler sử dụng:

```text
Cleanup Engine
    │
    ├── Drop actions
    ├── Defer actions
    ├── Capability release
    ├── Storage release
    ├── Guard release
    └── Control-flow continuation
```

Mỗi scope có:

```text
CleanupScope {
    scope_id
    parent_scope
    entered_actions
    deferred_actions
    owned_values
    live_capabilities
    storage_regions
    exit_edges
}
```

---

# 3. Cleanup không phải runtime object

Đây là điểm rất quan trọng.

Source:

```axiom
fn test() {
    let file = open();
    defer {
        log("done");
    }

    use(file);
}
```

không có nghĩa compiler tạo:

```text
CleanupObject
```

hay:

```text
DeferList
```

ở runtime.

Compiler biến nó thành control flow tương đương:

```text
use(file)

log("done")
drop(file)

return
```

Nếu `defer` không cần thiết hoặc có thể constant-fold/eliminate, optimizer có thể loại bỏ hoàn toàn.

### Invariant

> `defer` là compile-time control-flow construct, không phải runtime abstraction.

---

# 4. Cleanup Stack

Compiler duy trì một **semantic cleanup stack** trong MIR construction.

Ví dụ:

```axiom
fn f() {
    let a = A();
    defer A1();

    {
        let b = B();
        defer B1();

        work();
    }

    work2();
}
```

Compiler conceptually có:

```text
Scope S0
    Drop(a)
    Defer(A1)

Scope S1
    Drop(b)
    Defer(B1)
```

Khi S1 kết thúc:

```text
Defer(B1)
Drop(b)
```

Khi S0 kết thúc:

```text
Defer(A1)
Drop(a)
```

---

# 5. Thứ tự cleanup

Axiom phải phân biệt:

### Registration order

```axiom
defer A()
defer B()
defer C()
```

cleanup:

```text
C
B
A
```

Tức:

> `defer` chạy theo LIFO.

---

## 5.1 Drop order

Các owning local được drop theo reverse initialization order:

```axiom
let a = A();
let b = B();
let c = C();
```

→

```text
drop(c)
drop(b)
drop(a)
```

---

# 6. Nhưng không dùng thứ tự đơn giản một cách mù quáng

Ví dụ:

```axiom
let a = A();

defer {
    use(a);
}
```

Không thể:

```text
drop(a)
defer(use(a))
```

vì `defer` cần `a`.

Do đó compiler xây dependency graph:

```text
defer(A) ──depends──> a
```

và đảm bảo:

```text
defer(A)
drop(a)
```

### Quy tắc

> Cleanup ordering phải thỏa dependency graph trước khi áp dụng reverse-registration/reverse-initialization ordering.

Nếu dependency không thể thỏa mãn → compile error.

---

# 7. Defer Capture Semantics

Đây là vấn đề rất dễ gây bug.

Axiom phải quyết định `defer` capture theo **giá trị semantic tại thời điểm đăng ký**, không phải tạo một closure runtime tùy tiện.

Ví dụ:

```axiom
let x = 10;

defer {
    print(x);
}

x = 20;
```

Axiom cần quy định rõ.

Đề xuất:

### `defer` capture theo closure semantics

Compiler phân tích:

```text
READ x
```

hoặc:

```text
MUTATE x
```

hoặc:

```text
MOVE x
```

theo body của defer.

Nhưng vì defer chạy khi scope kết thúc, ownership verifier phải tính:

```text
x
 └── reserved by defer
```

---

# 8. Defer không được tạo alias bí mật

Ví dụ:

```axiom
let x = Resource();

defer {
    use(x);
}
```

không được coi như:

```text
x
 ├── owner
 └── hidden reference
```

mà compiler biểu diễn dependency:

```text
DeferAction
    uses x
```

Ownership verifier biết `x` không được move/drop trước defer.

Đây là một ví dụ điển hình của nguyên tắc:

> **Compiler có thể dùng reference/closure/internal pointer trong implementation, nhưng programmer không cần quản lý nó.**

---

# 9. Move + Defer

Trường hợp:

```axiom
let x = Resource();

defer {
    use(x);
}

consume(x);
```

phải bị reject nếu `consume(x)` move ownership của `x`.

Ví dụ:

```text
x
 │
 ├── required by DeferAction
 │
 └── Move → consume()
```

→ conflict.

Compiler diagnostic:

```text
error: value `x` is required by deferred cleanup
note: `x` is captured by defer at line ...
note: moving `x` here would invalidate the deferred action
```

---

# 10. Drop + Defer interaction

Ví dụ:

```axiom
let x = Resource();

defer {
    close(x);
}
```

Nếu `x` cũng có `Drop`, compiler không được tự động:

```text
close(x)
drop(x)
```

trừ khi semantics của `Drop` xác định điều đó.

`defer` và `Drop` là **hai semantic actions khác nhau**.

Điều này cho phép:

```axiom
defer {
    transaction.rollback();
}
```

trong khi `Drop(transaction)` có thể chỉ giải phóng storage.

---

# 11. Explicit `drop(x)`

Axiom hỗ trợ:

```axiom
drop(x);
```

nhưng semantic nghĩa là:

> kết thúc ownership obligation của `x` tại vị trí đó.

Sau đó:

```axiom
use(x);
```

→ error.

Compiler chuyển:

```text
Owned(x)
```

thành:

```text
Dropped(x)
```

và cleanup cuối scope **không được drop lại**.

---

# 12. Partial Move

Ví dụ:

```axiom
struct Pair {
    a: A,
    b: B
}

let p = Pair(...);

let x = p.a;
```

Sau đó:

```text
p
├── a = Moved
└── b = Owned
```

Cleanup:

```text
drop(p.b)
```

không:

```text
drop(p.a)
```

---

## 12.1 Custom Drop

Nếu:

```axiom
impl Drop for Pair { ... }
```

thì partial move mặc định bị cấm:

```axiom
let x = p.a; // error
```

vì `Drop<Pair>` cần toàn bộ invariant của `Pair`.

Đây là quy tắc rất quan trọng để tránh compiler phải mô phỏng destructor invariant phức tạp.

---

# 13. Cleanup Graph

`CleanupGraph` là cấu trúc trung tâm.

Ví dụ:

```text
Scope S
│
├── Defer D1
├── Drop A
├── Defer D2
├── Drop B
└── Drop C
```

Compiler xây:

```text
CleanupGraph

D2 ──> B
D1 ──> A
C
```

và dependency edges:

```text
D2 -> B
D1 -> A
```

Sau đó topological ordering + semantic ordering rules tạo cleanup sequence.

---

# 14. Cleanup Chains

Mỗi scope exit được lower thành một cleanup chain.

Ví dụ:

```axiom
fn f() {
    let a = A();

    {
        let b = B();

        if condition {
            return;
        }
    }
}
```

MIR conceptually:

```text
return_edge
    ↓
cleanup S1
    ↓
drop(b)
    ↓
cleanup S0
    ↓
drop(a)
    ↓
return
```

Không duplicate toàn bộ cleanup code nếu nhiều exit path.

Compiler có thể tạo:

```text
cleanup.block.1
cleanup.block.2
cleanup.block.3
```

và share chúng.

---

# 15. Cleanup Sharing

Ví dụ có:

```text
return
break
continue
panic
```

nhiều path cùng thoát khỏi một scope.

Compiler không nên sinh:

```text
drop(a)
drop(b)
```

4 lần.

Thay vào đó:

```text
exit → cleanup_scope_2 → cleanup_scope_1 → destination
```

Mỗi cleanup scope là một reusable CFG fragment.

---

# 16. Return Value và Cleanup

Ví dụ:

```axiom
fn f() -> Result {
    let x = X();
    return make_result(x);
}
```

Return value phải được materialize trước cleanup nếu nó phụ thuộc vào local.

Conceptual:

```text
tmp_return = make_result(move x)

cleanup

return tmp_return
```

Không được:

```text
drop(x)
make_result(x)
```

---

# 17. Return Value Storage

Compiler có thể tối ưu:

```text
temporary
```

thành:

```text
caller-provided return slot
```

nếu ABI cho phép.

Vì vậy semantic model:

```text
return value exists before cleanup
```

nhưng physical implementation có thể là:

```text
construct directly into caller return slot
cleanup locals
ret
```

---

# 18. `break value`

Ví dụ:

```axiom
let result =
    loop {
        let x = compute();

        if ready {
            break x;
        }
    };
```

`x` phải được move/materialize vào loop result trước cleanup của iteration scope.

Conceptual:

```text
result_slot = move(x)

cleanup_iteration_scope

jump loop_exit
```

---

# 19. `continue`

`continue` phải chạy cleanup của toàn bộ scope nằm giữa vị trí hiện tại và loop body boundary.

Ví dụ:

```axiom
loop {
    let x = Resource();

    defer cleanup_x();

    if skip {
        continue;
    }
}
```

Phải:

```text
cleanup_x()
drop(x)
continue
```

Không được jump trực tiếp về loop header.

---

# 20. `panic`

Nếu profile:

```text
panic = abort
```

compiler có thể giảm cleanup đáng kể nếu semantics profile xác định process termination ngay lập tức.

Nếu:

```text
panic = unwind
```

thì panic phải đi qua cleanup graph.

Do đó:

```text
PanicMode
    Abort
    Unwind
    Custom
```

là compilation profile.

---

# 21. Unwind Cleanup

Nếu unwind được bật:

```text
normal CFG
     │
     └── panic edge
             ↓
       cleanup graph
             ↓
       unwind handler
```

Cleanup phải **không được chạy hai lần** nếu control flow đã đi qua một cleanup block.

Compiler gắn:

```text
CleanupScopeId
CleanupActionId
```

và verification đảm bảo uniqueness.

---

# 22. Drop không được fail

`Drop` không trả:

```axiom
Result
```

và không được propagate error.

Ví dụ không cho:

```axiom
impl Drop for File {
    fn drop(self) -> Result<...>
}
```

Nếu resource release có khả năng thất bại:

```axiom
file.close() -> Result
```

phải được gọi explicit.

Sau đó `Drop<File>` chỉ thực hiện best-effort/final resource release theo contract.

---

# 23. Drop trong Panic/Unwind

Nếu Drop gây panic trong quá trình unwind:

```text
panic
 ↓
drop(a)
 ↓
panic again
```

không được tạo double-unwind phức tạp.

Profile mặc định nên:

```text
double panic during unwind → terminate
```

Điều này giữ semantics đơn giản và runtime nhỏ.

---

# 24. Capability Cleanup

Cleanup không chỉ dành cho Drop.

Ví dụ:

```axiom
let v = mut_view(x);
```

khi scope kết thúc, capability:

```text
mut_view(x)
```

không còn tồn tại.

Compiler không cần runtime operation.

Đó là:

```text
semantic cleanup
```

chứ không phải:

```text
machine cleanup
```

Sau optimization:

```text
mut_view
```

thường biến mất hoàn toàn.

---

# 25. Guard Cleanup

Ví dụ:

```axiom
lock.lock()
```

trả:

```text
Guard
```

Guard có Drop:

```text
Drop(Guard)
    → unlock
```

Như vậy synchronization tự nhiên tích hợp với Cleanup Engine.

Ví dụ:

```axiom
{
    let guard = mutex.lock();
    modify(data);
}
```

lower:

```text
guard = lock()
modify(data)
unlock()
```

không cần một hệ thống riêng cho mutex unlock.

---

# 26. Async Compatibility

Cleanup Engine phải chạy **trước async lowering hoàn chỉnh**.

Ví dụ:

```axiom
async fn f() {
    let resource = acquire();

    defer {
        cleanup(resource);
    }

    await operation();
}
```

`resource` và defer dependency phải được xác định trước.

Sau đó Async Lowering quyết định:

```text
resource → Future state field
```

nếu sống qua await.

Cleanup action cũng trở thành một phần của state-machine exit path.

Không được để async compiler tự phát minh cleanup semantics mới.

---

# 27. Cancellation

Nếu Future bị drop:

```axiom
let future = f();
drop(future);
```

thì cleanup của **Future state** phải chạy theo ownership semantics.

Nhưng:

> Drop Future không tự động có nghĩa là hủy một external operation.

Ví dụ socket operation đã được OS/runtime submit thì cancellation contract phải thuộc executor/I/O abstraction.

Cleanup Engine chỉ chịu trách nhiệm cleanup **owned state của Future**.

---

# 28. Cleanup và Closure

Closure:

```axiom
let f = || use(resource);
```

có capture.

Nếu closure bị drop:

```text
Drop(closure)
```

thì captured owning fields được cleanup theo closure layout.

Compiler không cần một ClosureCleanupEngine riêng.

Nó chỉ dùng:

```text
Cleanup Engine
```

---

# 29. Cleanup và Generic

Generic:

```axiom
fn process<T>(x: T) {
    ...
}
```

nếu `T: Drop`, cleanup cần biết destructor semantics của specialization.

Sau monomorphization:

```text
process<Resource>
```

→ cleanup có thể trực tiếp inline Drop.

Nếu `T` không có Drop:

```text
cleanup = no-op
```

và optimizer loại bỏ hoàn toàn.

---

# 30. Zero-Cost Requirement

Các construct sau không được tạo overhead nếu semantic không cần:

```text
defer
Drop
view
mut_view
cleanup scope
ownership state
capability state
```

Tất cả đều phải có khả năng biến mất trước Machine IR.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    defer {}
    return a + b;
}
```

machine code phải tương đương:

```text
return a + b
```

Không được có runtime cleanup stack.

---

# 31. Cleanup Elaboration Pipeline

Pipeline:

```text
Typed HIR
   ↓
MIR construction
   ↓
Scope/Drop/Defer discovery
   ↓
Cleanup dependency analysis
   ↓
CleanupGraph construction
   ↓
Exit-path classification
   ↓
Cleanup chain synthesis
   ↓
Drop/Defer elaboration
   ↓
Unwind edge elaboration
   ↓
Capability cleanup verification
   ↓
Cleanup correctness verification
   ↓
Verified MIR
   ↓
Optimization
```

---

# 32. Cleanup Actions

Chuẩn hóa:

```text
CleanupAction =
    DropValue
    ExecuteDefer
    ReleaseCapability
    ReleaseGuard
    ReleaseStorage
    RunUnwindCleanup
```

Compiler không được cho phép một action tùy ý phá vỡ ownership semantics.

---

# 33. Cleanup Destination

Mỗi cleanup chain có:

```text
CleanupDestination =
    Return
    Break
    Continue
    Panic
    Unwind
    ScopeExit
```

Ví dụ:

```text
CleanupChain {
    scope: S3
    actions: [...]
    destination: Break(L2)
}
```

---

# 34. Cleanup Verification

Verifier phải kiểm tra:

### C1
Mỗi Drop obligation được xử lý đúng một lần.

### C2
Moved value không bị Drop.

### C3
Dropped value không bị Drop lần nữa.

### C4
Partial move chỉ drop phần còn sở hữu.

### C5
Defer dependency còn valid khi chạy.

### C6
Không cleanup action nào dùng capability đã hết hạn.

### C7
Không exit path bypass cleanup.

### C8
Không cleanup action chạy hai lần.

### C9
Return value được materialize trước khi dependency bị drop.

### C10
Unwind path obey cleanup graph.

### C11
Cleanup ordering thỏa dependency graph.

### C12
Async state cleanup tương thích với Future ownership.

---

# 35. CompilerDB

Thêm các database:

```text
CleanupDB
CleanupScopeDB
CleanupActionDB
CleanupDependencyDB
CleanupGraphDB
CleanupChainDB
CleanupDestinationDB

DropDB
DropObligationDB
DropElaborationDB

DeferDB
DeferCaptureDB
DeferDependencyDB

UnwindCleanupDB
CleanupVerificationDB
CleanupOptimizationDB
```

Các query quan trọng:

```text
cleanup_scope(FunctionId, ScopeId)
cleanup_actions(ScopeId)
cleanup_dependencies(ScopeId)
cleanup_graph(FunctionId)
cleanup_chain(ExitId)
drop_obligations(FunctionId)
defer_actions(FunctionId)
cleanup_destination(ExitId)
verify_cleanup(FunctionId)
```

---

# 36. MIR additions

MIR semantic layer cần hỗ trợ:

```text
DROP place
DEFER action
CLEANUP_SCOPE scope_id
CLEANUP_JUMP destination
```

Nhưng đây có thể là **pre-elaboration MIR**.

Sau cleanup elaboration:

```text
DROP
DEFER
CLEANUP_SCOPE
```

được lower thành ordinary CFG:

```text
CALL
STORE
LOAD
BRANCH
GOTO
RETURN
```

với machine-visible effects của Drop/Defer được giữ lại.

Điều này rất quan trọng:

> Sau Cleanup Elaboration, backend không cần hiểu `return`, `defer`, ownership hay scope.

---

# 37. Cleanup Fingerprint

Cleanup semantics phải nằm trong incremental compiler fingerprint.

Nếu thay đổi:

```axiom
defer { ... }
```

chỉ những function/cleanup graph phụ thuộc mới cần re-lower.

Không cần rebuild toàn compiler graph.

---

# 38. Diagnostic model

Diagnostics phải chỉ ra **đường ownership/cleanup**, không chỉ báo lỗi tại một dòng.

Ví dụ:

```text
error AXCLN-014:
cannot move `file`

`file` is required by deferred cleanup

  12 | let file = open();
     |     ---- owner created here

  13 | defer {
  14 |     file.flush();
  15 | }
     |     deferred use registered here

  18 | consume(file);
     |         ^^^^ move occurs here

cleanup path:
scope exit → defer@13 → drop(file)
```

Đây là loại diagnostic đặc biệt quan trọng đối với triết lý:

> Compiler quản lý complexity, programmer chỉ cần hiểu semantic conflict.

---

# 39. Optimizations

Cleanup Engine xuất ra metadata để optimizer thực hiện:

### Drop elimination

Nếu resource không có observable Drop:

```text
drop(x)
```

→ eliminate.

### Empty defer elimination

```text
defer {}
```

→ eliminate.

### Cleanup fusion

```text
drop(a)
drop(b)
drop(c)
```

→ một cleanup block.

### Cleanup sinking

Chỉ chạy cleanup tại path thật sự cần.

### Cleanup hoisting

Nếu action có thể thực hiện sớm hơn mà không thay đổi semantics.

### Drop inlining

```text
Drop<T>
```

→ inline implementation.

### Drop specialization

Generic Drop được specialize theo concrete type.

### Cleanup block deduplication

Các CFG cleanup sequence giống nhau dùng chung block.

### Dead cleanup elimination

Nếu compiler chứng minh value đã moved hoặc resource không còn live.

---

# 40. Một nguyên tắc rất quan trọng

Không được để optimizer **suy ra cleanup semantics**.

Đúng:

```text
Semantic analysis
    ↓
Cleanup Graph
    ↓
Verified MIR
    ↓
Optimization
```

Không được:

```text
Optimization
    ↓
"có vẻ như không cần drop"
```

Optimizer chỉ được loại bỏ cleanup **sau khi semantic verifier đã chứng minh cleanup đó không observable hoặc không cần thiết**.

---

# 41. Invariants

Đóng băng các invariant:

```text
ACLN-01  Every owned resource has exactly one semantic cleanup obligation.

ACLN-02  Moved values are never dropped.

ACLN-03  Dropped values are never dropped again.

ACLN-04  Partial moves drop only remaining owned subplaces.

ACLN-05  Custom Drop forbids invalid partial destruction.

ACLN-06  Every scope exit passes through required cleanup.

ACLN-07  Cleanup ordering satisfies dependency constraints.

ACLN-08  Defer actions execute in reverse registration order
         unless dependency ordering requires a different valid order.

ACLN-09  Owned locals are dropped in reverse initialization order
         subject to dependency constraints.

ACLN-10  A defer action cannot access an invalid value.

ACLN-11  A defer capture creates no implicit programmer-visible alias.

ACLN-12  Explicit drop invalidates the value immediately.

ACLN-13  Cleanup actions execute at most once per ownership obligation.

ACLN-14  Return values are materialized before dependent locals are destroyed.

ACLN-15  break-value expressions preserve ownership across loop cleanup.

ACLN-16  continue executes all required intermediate cleanup.

ACLN-17  panic follows the selected panic profile.

ACLN-18  Unwind cleanup cannot execute the same action twice.

ACLN-19  Drop cannot propagate recoverable failure.

ACLN-20  Drop during active unwind cannot create uncontrolled nested unwind.

ACLN-21  Capability cleanup is semantically distinct from machine deallocation.

ACLN-22  Guard release uses the same cleanup machinery.

ACLN-23  Async state cleanup uses the same semantic cleanup model.

ACLN-24  Closure captured resources use the same cleanup model.

ACLN-25  Generic cleanup semantics are specialization-independent.

ACLN-26  Cleanup constructs introduce no mandatory runtime allocation.

ACLN-27  Cleanup semantics are independent of optimization level.

ACLN-28  Cleanup verification occurs before optimization.

ACLN-29  Cleanup elaboration preserves source-to-machine provenance.

ACLN-30  Equivalent cleanup graphs may be merged without changing semantics.
```

---

# 42. Kết quả cuối của BOOTSTRAP-359

Sau task này, Axiom có một nguyên lý rất mạnh:

```text
                 ┌───────────────┐
                 │  Scope Exit   │
                 └───────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       return          break          panic
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  Cleanup Graph
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
           defer        drop       guards
             │           │           │
             └───────────┼───────────┘
                         ↓
                  Verified MIR
                         ↓
                     Optimize
```

Như vậy `Drop`, `defer`, lock guard, capability lifetime, closure destruction, Future destruction và unwind **không còn là những hệ thống rời rạc**.

Đây là nền tảng để Axiom có thể vừa **đơn giản với lập trình viên**, vừa cho compiler một mô hình ownership/destruction đủ mạnh để đạt hiệu năng native.