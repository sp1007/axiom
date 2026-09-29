# BOOTSTRAP-415 — DROP ELABORATION & RESOURCE LIFETIME LOWERING

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 411, 413, 414  
**Mục tiêu:** biến ownership + initialization + Drop semantics thành **cleanup graph chính xác trong MIR**, để compiler có thể tối ưu lifetime mà không làm thay đổi semantics.

Đây là bước rất quan trọng đối với Axiom vì nó quyết định liệu mô hình **“compiler quản lý lifetime, programmer không viết lifetime/borrow”** có thực sự vừa an toàn vừa có hiệu năng cao hay không.

---

## 415.1. Nguyên tắc cốt lõi

Axiom phân biệt:

```text
Ownership
    ↓
semantic responsibility

Drop
    ↓
resource destruction

Storage lifetime
    ↓
physical storage existence
```

Ba thứ này **không đồng nhất**.

Ví dụ:

```axiom
let x = File.open(...)
```

có thể có:

```text
semantic resource lifetime:
    x owns File

physical storage:
    register / stack / heap / optimized away
```

Compiler không được suy ra rằng `Drop` = `free(memory)`.

---

# 415.2. Drop là semantic operation

Trong MIR:

```text
DROP(place)
```

có nghĩa:

> thực hiện destruction semantics của value tại `place`.

Nó **không nhất thiết** có nghĩa:

```text
free(address)
```

Ví dụ:

```text
DROP(File)
```

có thể:

```text
close(fd)
release handle
decrement internal resource
```

nhưng storage của struct có thể vẫn tồn tại.

---

# 415.3. Storage Deallocation là operation khác

Axiom phân biệt:

```text
DROP
DEALLOC
```

Ví dụ:

```text
Box<File>
```

có thể semantic sequence:

```text
DROP(File)
DEALLOC(storage)
```

nhưng compiler có quyền biến thành một sequence tương đương.

---

# 415.4. Drop Elaboration

Trước Drop Elaboration:

```text
MIR
    ownership states
    implicit destruction requirements
```

Sau Drop Elaboration:

```text
MIR
    explicit DROP
    explicit cleanup edges
    explicit drop flags
    explicit exceptional cleanup
```

Pipeline:

```text
Typed MIR
   ↓
Ownership verification
   ↓
Drop requirement analysis
   ↓
Drop elaboration
   ↓
Cleanup CFG
   ↓
Drop verification
   ↓
Verified MIR
```

---

# 415.5. Drop Scope

Mỗi resource-bearing value có một semantic drop scope.

Ví dụ:

```axiom
fn f() {
    let a = A()
    let b = B()
}
```

mặc định:

```text
enter scope
    acquire a
    acquire b

exit scope
    drop b
    drop a
```

LIFO.

---

# 415.6. Nested Scope

```axiom
fn f() {
    let a = A()

    {
        let b = B()
    }

    use(a)
}
```

Cleanup:

```text
inner scope:
    drop b

outer scope:
    drop a
```

`b` không thể sống semantic vượt quá scope nếu không được moved/returned/captured theo một transformation hợp lệ.

---

# 415.7. Move Transfers Drop Responsibility

```axiom
let a = Resource()
let b = a
```

Nếu `Resource` là non-Copy:

```text
a:
    OWNED → MOVED

b:
    UNINITIALIZED → OWNED
```

Drop responsibility chuyển:

```text
a → b
```

Không có:

```text
drop(a)
```

sau move.

---

# 415.8. Return Transfers Responsibility

```axiom
fn create() -> Resource {
    let x = Resource()
    return x
}
```

Compiler:

```text
x = OWNED

return x

x → RETURNED
function cleanup:
    do not DROP(x)
```

Caller nhận ownership.

---

# 415.9. Partial Move

Ví dụ:

```axiom
struct Pair {
    a: ResourceA
    b: ResourceB
}

let x = Pair(...)
let y = x.a
```

Semantic state:

```text
x.a = MOVED
x.b = OWNED
```

Compiler phải tạo partial-drop state.

Khi scope kết thúc:

```text
DROP(x.b)
```

nhưng:

```text
DROP(x.a)
```

không được thực hiện.

---

# 415.10. Drop Flags

Đối với aggregate có partial initialization/move, compiler có thể tạo:

```text
drop_flag(x.a)
drop_flag(x.b)
```

Semantic:

```text
if initialized(x.a):
    DROP(x.a)

if initialized(x.b):
    DROP(x.b)
```

Nhưng đây là **semantic model**, không bắt buộc có runtime boolean.

Compiler có thể:

- constant-fold;
- path-specialize;
- eliminate;
- encode state trong CFG.

---

# 415.11. Drop Flags không được lộ ra ABI

Drop flags là compiler implementation detail.

Không được:

```text
struct layout:
    user fields
    hidden drop flag
```

trừ khi ABI/storage contract thực sự yêu cầu.

Điều này giữ struct compact.

---

# 415.12. Compiler ưu tiên CFG thay vì Runtime Drop Flag

Ví dụ:

```axiom
if condition {
    let x = Resource()
    ...
}
```

thay vì:

```text
runtime flag initialized_x
```

compiler có thể tạo:

```text
BB_then:
    init x
    ...
    DROP x
    goto BB_join

BB_else:
    goto BB_join
```

Không cần runtime flag.

---

# 415.13. Drop Flag chỉ khi CFG không đủ

Ví dụ phức tạp:

```axiom
let x: Resource

if a {
    x = create()
}

if b {
    consume(x)
}
```

Nếu compiler không thể prove state tĩnh, có thể cần semantic drop-state representation.

Nhưng optimizer phải cố gắng biến nó thành CFG/path specialization.

---

# 415.14. Drop và `defer`

Ví dụ:

```axiom
{
    let a = A()

    defer {
        cleanup()
    }

    let b = B()
}
```

cleanup order:

```text
DROP b
run defer
DROP a
```

theo semantic registration ordering đã khóa ở 414.

Compiler phải materialize thứ tự này trong cleanup graph.

---

# 415.15. Multiple `defer`

```axiom
defer A
defer B
defer C
```

khi scope thoát:

```text
C
B
A
```

Nếu resource Drop cũng tồn tại, toàn bộ cleanup ordering phải được biểu diễn thành một **Cleanup Chain**.

---

# 415.16. Cleanup Chain

Mỗi lexical scope có thể có:

```text
CleanupScope {
    scope_id
    cleanup_entries[]
    parent_scope
}
```

Mỗi entry:

```text
CleanupEntry {
    kind
    order
    ownership_state
    action
}
```

Ví dụ:

```text
Scope 3:
    #1 DROP(a)
    #2 DEFER(x)
    #3 DROP(b)
```

Exit path tạo:

```text
b → defer(x) → a
```

---

# 415.17. Cleanup Edge

CFG có thể có:

```text
normal edge
return edge
break edge
continue edge
panic edge
unwind edge
```

Tất cả phải đi qua cleanup cần thiết.

Ví dụ:

```text
BB10
  |
  | return
  v
Cleanup_B
  |
  v
Cleanup_A
  |
  v
Return
```

---

# 415.18. Cleanup Không được Double-Execute

Compiler phải chứng minh:

```text
mỗi cleanup obligation
    executes 0 hoặc 1 lần
```

Không được:

```text
DROP x
...
DROP x
```

trừ khi `x` đã được reinitialized giữa hai lần.

---

# 415.19. Reinitialization

Ví dụ:

```axiom
let x = Resource()

drop(x)

x = Resource2()
```

state:

```text
x: OWNED
 ↓
DROP
 ↓
DROPPED
 ↓
ASSIGN
 ↓
OWNED
```

Cleanup cuối scope chỉ Drop `Resource2`.

---

# 415.20. Explicit `drop(x)`

Nếu programmer viết:

```axiom
drop(x)
```

compiler coi đây là ownership state transition:

```text
OWNED → DROPPED
```

Không được implicit Drop thêm lần nữa.

---

# 415.21. `drop` không nhất thiết giải phóng storage

Sau:

```axiom
drop(x)
```

`x` vẫn có thể có physical storage.

Nhưng semantic value:

```text
INVALID/DROPPED
```

không thể được dùng.

---

# 415.22. Assignment Sau Drop

```axiom
drop(x)
x = new_value
```

hợp lệ nếu type cho phép reinitialization.

Compiler:

```text
DROPPED → INIT → OWNED
```

---

# 415.23. Drop và Copy

Nếu:

```text
T: Copy
```

thì copy của `T` phải không tạo thêm destruction obligation độc lập.

Do đó:

```text
Copy + Drop
```

bị cấm như đã khóa ở memory model.

Nếu không:

```text
a = Resource()
b = copy(a)
```

có thể dẫn tới double destruction.

---

# 415.24. Clone

`Clone` khác `Copy`.

```axiom
let b = a.clone()
```

có thể tạo:

```text
a owns resource A
b owns resource B
```

mỗi object có Drop obligation riêng.

Compiler không được coi `Clone` là bitwise copy.

---

# 415.25. Drop Order của Struct

Ví dụ:

```axiom
struct S {
    a: A
    b: B
    c: C
}
```

default destruction:

```text
c
b
a
```

trừ khi type định nghĩa custom Drop semantics.

---

# 415.26. Custom Drop

Nếu type có:

```axiom
impl Drop for S {
    fn drop(self) { ... }
}
```

compiler phải coi toàn bộ `S` là một destruction unit.

Do đó:

```text
partial move
```

phải bị hạn chế nếu custom Drop cần toàn aggregate.

Đây là lý do đã khóa:

> custom Drop ⇒ không cho partial move mặc định.

---

# 415.27. Derived Drop

Nếu compiler tự sinh Drop:

```text
struct S {
    a: A
    b: B
}
```

compiler biết chính xác từng field.

Có thể:

```text
move s.a
```

và cuối scope chỉ:

```text
drop s.b
```

---

# 415.28. Panic During Drop

Drop không được tạo ra một trạng thái resource không thể kiểm soát.

Đề xuất Core rule:

```text
Drop must not propagate recoverable error.
```

Nếu Drop panic trong unwind:

```text
panic during active unwind
```

→ terminate/abort.

Điều này tránh:

```text
panic
  ↓
drop
  ↓
panic
  ↓
ambiguous cleanup
```

---

# 415.29. Explicit `close()` cho Fallible Cleanup

Ví dụ File:

```axiom
file.close() -> Result<(), Error>
```

khác:

```text
Drop(File)
```

`close()` có thể fail.

Drop phải có semantics deterministic và không yêu cầu caller xử lý error.

Pattern:

```axiom
file.close()?
```

sau đó Drop chỉ xử lý trạng thái còn lại nếu type định nghĩa như vậy.

---

# 415.30. Drop State Machine

Mỗi Drop-bearing value có semantic state:

```text
UNINIT
   ↓
OWNED
   ↓
MOVED
   ↓
DROPPED
```

và:

```text
OWNED
   ↓
PARTIALLY_MOVED
   ↓
PARTIAL_DROP
   ↓
DROPPED
```

Các transition bất hợp lệ:

```text
MOVED → READ
DROPPED → READ
DROPPED → MOVE
MOVED → DROP
```

trừ các transition compiler định nghĩa riêng cho state machine cleanup.

---

# 415.31. Drop Elaboration với Closure

Closure:

```axiom
let f = || use(resource)
```

Nếu closure capture ownership:

```text
closure.environment.resource
```

trở thành một field semantic của closure object.

Khi closure bị Drop:

```text
DROP(environment.resource)
```

được compiler sinh tự động.

---

# 415.32. Closure Move

```axiom
let f = move_capture(resource)
let g = f
```

Nếu closure non-Copy:

```text
f → MOVED
g → OWNED
```

Drop responsibility của captured resources chuyển cùng closure.

---

# 415.33. Async State Machine

Đây là trường hợp đặc biệt quan trọng.

```axiom
async fn f() {
    let x = Resource()
    await something()
    use(x)
}
```

`x` sống qua suspension.

Compiler phải chuyển semantic ownership của `x` vào coroutine state:

```text
CoroutineFrame.x
```

Không được Drop `x` tại suspension.

---

# 415.34. Async Drop

Nếu task bị cancel trước khi resume:

```text
Task
 ↓
Cancel
 ↓
Drop coroutine frame
 ↓
Drop all live fields
```

Compiler phải tạo cleanup path cho:

```text
partially initialized coroutine frame
```

Đây là một trong những nơi drop flags/path-sensitive cleanup thực sự cần thiết.

---

# 415.35. Thread Spawn

Nếu closure được spawn:

```axiom
spawn(|| use(x))
```

và closure phải sống độc lập với caller:

```text
x
 ↓
capture MOVE
 ↓
closure environment
 ↓
task
```

Caller không còn ownership của `x`.

Khi task hoàn tất:

```text
DROP(task closure)
```

và captured resources được drop.

---

# 415.36. Exception/Unwind Cleanup

Nếu profile hỗ trợ unwind:

```text
panic
 ↓
cleanup landing path
 ↓
Drop/Defer
 ↓
caller unwind
```

Cleanup graph phải đảm bảo resource destruction không phụ thuộc vào normal return.

---

# 415.37. Abort Profile

Nếu profile:

```text
panic = abort
```

thì panic path có thể:

```text
PANIC → ABORT
```

và không cần generate full unwind cleanup.

Nhưng normal:

```text
return
break
continue
scope exit
```

vẫn phải cleanup.

Đây là một nguồn tối ưu binary rất đáng kể.

---

# 415.38. `no_unwind`

FFI hoặc function có thể có contract:

```text
no_unwind
```

Compiler đảm bảo function không thoát bằng unwind.

Nếu vi phạm:

```text
terminate
```

thay vì crossing ABI boundary.

---

# 415.39. Lifetime Elision

Sau Drop Elaboration, optimizer được phép phát hiện:

```text
DROP(T)
```

không có observable effect.

Nếu:

```text
T
```

trivially destructible:

```text
DROP(T)
```

có thể xóa hoàn toàn.

---

# 415.40. Trivial Drop

Compiler phân loại type:

```text
TrivialDrop
NonTrivialDrop
ConditionalDrop
```

`TrivialDrop`:

```text
DROP(x)
```

không có semantic effect.

Do đó:

```text
DROP
```

chỉ là verifier concept, không nhất thiết tồn tại ở machine code.

---

# 415.41. Drop Elision

Nếu:

```axiom
let x = SmallStruct(...)
use(x)
```

và `SmallStruct` trivial:

```text
no cleanup code
```

được generate.

Nếu nontrivial nhưng compiler chứng minh destructor không observable trong context:

```text
drop may be eliminated
```

chỉ khi semantic rules cho phép.

---

# 415.42. Lifetime Shortening

Compiler có thể phát hiện:

```axiom
{
    let x = Resource()
    use(x)
}
```

và nếu không có observable dependency sau `use`:

```text
DROP(x)
```

có thể thực hiện sớm.

Nhưng:

> lifetime shortening không được thay đổi thứ tự observable destructor effects.

Do đó mặc định compiler chỉ shortening khi proof hợp lệ.

---

# 415.43. Lifetime Extension

Compiler cũng có thể kéo dài physical lifetime:

```text
stack slot
register
heap allocation
```

miễn là:

```text
observable Drop semantics
```

không thay đổi.

Ví dụ scalar replacement:

```text
struct Pair { a, b }
```

có thể biến thành:

```text
register a
register b
```

nếu address/layout không observable.

---

# 415.44. Stable Address Barrier

Nếu programmer yêu cầu stable storage:

```axiom
Box<T>
```

và address được expose:

```text
address observable
```

compiler không được:

```text
relocate
scalarize
duplicate storage
```

nếu những transformation đó phá contract.

Đây là một **optimization barrier**.

---

# 415.45. Drop + FFI

FFI function có thể giữ resource.

Ví dụ:

```text
extern "C" fn close_handle(...)
```

Compiler cần contract:

```text
ownership consumed?
borrowed?
returns ownership?
may fail?
may panic?
```

Nếu contract không rõ:

```text
unsafe FFI boundary
```

không được tự suy luận destructor semantics.

---

# 415.46. Drop + Shared Ownership

Với:

```text
Arc<T>
```

Drop semantic của `Arc` là:

```text
decrement refcount
```

không đồng nghĩa immediate:

```text
DROP(T)
```

`T` chỉ được destroy khi last strong owner biến mất.

Đây là library-level implementation nhưng compiler vẫn cần hiểu một số ownership traits để tối ưu/verify.

---

# 415.47. Drop + Atomic Shared

Với concurrent reference counting:

```text
Arc<T>
```

last-owner detection có synchronization semantics.

Compiler **không được** loại bỏ/reorder atomic operations như ordinary Drop.

Do đó Drop effect metadata phải có:

```text
atomic ordering requirements
```

khi cần.

---

# 415.48. Cleanup Graph

Compiler tạo:

```text
CleanupGraph
```

gồm:

```text
CleanupNode
    Drop
    Defer
    ResourceRelease
    CoroutineCleanup
    TaskCleanup

CleanupEdge
    sequencing
    conditional
    exceptional
```

Mục tiêu:

```text
CFG
+
CleanupGraph
→
Explicit Cleanup MIR
```

---

# 415.49. CompilerDB

Thêm:

```text
DropElaborationDB
DropScopeDB
DropStateDB
DropFlagDB
CleanupGraphDB
CleanupPathDB
ResourceLifetimeDB
TrivialDropDB
DropOptimizationDB
UnwindCleanupDB
CoroutineCleanupDB
TaskCleanupDB
```

---

# 415.50. Proof Artifacts

```text
DropElaborationProof
DropOrderProof
DropUniquenessProof
PartialMoveDropProof
CleanupPathProof
CleanupReachabilityProof
DropFlagProof
TrivialDropProof
DropElisionProof
LifetimeShorteningProof
LifetimeExtensionProof
AsyncCleanupProof
TaskCancellationCleanupProof
UnwindCleanupProof
FFIDropContractProof
```

---

# 415.51. Invariants `ADROP`

```text
ADROP-01  Every Drop obligation has a unique semantic owner.
ADROP-02  A moved value is never dropped by its old owner.
ADROP-03  A dropped value is never dropped again without reinitialization.
ADROP-04  Partial moves produce field-sensitive cleanup.
ADROP-05  Custom Drop prevents invalid partial destruction.
ADROP-06  Cleanup ordering is deterministic.
ADROP-07  Defer ordering is deterministic.
ADROP-08  Normal scope exit executes required cleanup.
ADROP-09  Return paths execute required cleanup.
ADROP-10  Break paths execute required cleanup.
ADROP-11  Continue paths execute required cleanup.
ADROP-12  Panic/unwind paths execute required cleanup when enabled.
ADROP-13  Abort profiles do not generate unnecessary unwind cleanup.
ADROP-14  Drop does not implicitly mean memory deallocation.
ADROP-15  DEALLOC is distinct from DROP.
ADROP-16  Trivial Drop may be eliminated.
ADROP-17  Nontrivial Drop may only be eliminated with semantic proof.
ADROP-18  Lifetime shortening preserves observable destruction order.
ADROP-19  Lifetime extension preserves observable destruction order.
ADROP-20  Stable-address contracts prevent invalid relocation.
ADROP-21  Closure environments own captured resources correctly.
ADROP-22  Async frames own values crossing suspension correctly.
ADROP-23  Cancelled tasks clean partially initialized frames correctly.
ADROP-24  Spawned tasks own moved captures correctly.
ADROP-25  FFI ownership contracts govern destruction.
ADROP-26  Shared ownership destruction respects synchronization semantics.
ADROP-27  Cleanup cannot create use-after-drop.
ADROP-28  Cleanup cannot create double-drop.
ADROP-29  Every cleanup path is verified before code generation.
ADROP-30  Drop elaboration preserves source-level resource semantics.
```

---

## 415.52. Kiến trúc cuối

Sau 415, phần resource lifetime của Axiom có dạng:

```text
             Ownership
                 │
                 ▼
          Initialization
                 │
                 ▼
            Ownership
            Verification
                 │
                 ▼
          Drop Requirement
             Analysis
                 │
                 ▼
        ┌─────────────────┐
        │ Drop Elaboration│
        └────────┬────────┘
                 ▼
           Cleanup Graph
                 │
                 ▼
        Explicit Cleanup MIR
                 │
                 ▼
          Drop Verification
                 │
                 ▼
          Semantic Optimize
                 │
          ┌──────┴──────┐
          ▼             ▼
    Drop Elimination  Lifetime
                      Optimization
```

Điểm quan trọng nhất:

> **Axiom không bắt programmer quản lý lifetime bằng syntax; thay vào đó compiler biến ownership thành một Cleanup Graph có thể chứng minh.**

Điều này cho phép programmer viết code gần với C/C++ về độ đơn giản, nhưng compiler vẫn có đủ thông tin để đảm bảo **không double-free, use-after-move, leak do ownership sai, hoặc cleanup thiếu trên các control-flow path**.

**BOOTSTRAP-415 — SPECIFIED / FROZEN.**