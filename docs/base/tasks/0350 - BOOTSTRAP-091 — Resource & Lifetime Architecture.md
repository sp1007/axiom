# BOOTSTRAP-091 — Resource & Lifetime Architecture

**Trạng thái: FROZEN**

Sau khi đã tách **Value / Ownership / Capability / Storage / Logical Identity**, bước tiếp theo là giải quyết một vấn đề sâu hơn:

> Một chương trình thực tế không chỉ có “memory lifetime”.

File, socket, GPU buffer, thread, async operation, lock, mmap, process, database transaction… đều có vòng đời riêng.

Axiom cần quản lý chúng **đúng**, nhưng không biến programmer thành người viết lifetime graph thủ công.

---

# 1. Sáu loại lifetime

Axiom chính thức phân biệt:

```text
Value Lifetime
Ownership Lifetime
Capability Lifetime
Storage Lifetime
Resource Lifetime
Execution Lifetime
```

Trong đó một số lifetime có quan hệ với nhau nhưng **không đồng nhất**.

Ví dụ:

```text
File
 ├─ logical resource lifetime
 ├─ OS handle lifetime
 ├─ memory wrapper lifetime
 └─ async I/O in-flight lifetime
```

Không được gom tất cả thành một khái niệm `lifetime`.

---

# 2. Value Lifetime

Value lifetime là:

> Khoảng thời gian một value tồn tại ở trạng thái hợp lệ.

Ví dụ:

```text
var x = 10

{
    var y = 20
}
```

`y` kết thúc lifetime khi ra khỏi scope nếu không còn ownership khác.

Compiler có thể rút ngắn physical storage:

```text
register
stack
SSA value
```

nhưng semantic lifetime vẫn được giữ.

---

# 3. Ownership Lifetime

Ownership lifetime trả lời:

> Ai chịu trách nhiệm cuối cùng đối với resource/value?

Ví dụ:

```text
let file = File.open(...)
```

`file` là owner.

Move:

```text
let f2 = file
```

ownership chuyển:

```text
file → moved
f2   → owner
```

Không nhất thiết có physical copy.

---

# 4. Capability Lifetime

Capability lifetime trả lời:

> Trong khoảng thời gian nào một access capability còn hợp lệ?

Ví dụ:

```text
let v = view(buffer)
```

`v` không sở hữu `buffer`.

Do đó:

```text
buffer lifetime
    ────────────────────────

view lifetime
       ─────────────
```

Compiler đảm bảo:

```text
view lifetime ⊆ owner lifetime
```

---

# 5. Storage Lifetime

Storage lifetime là:

> Khoảng thời gian physical storage được đảm bảo tồn tại theo storage contract.

Ví dụ:

```text
Vec<T>
```

có thể relocation.

Trong khi:

```text
StablePool<T>
```

có thể cung cấp stable slot.

Do đó:

```text
logical object lifetime
        ≠
storage lifetime
```

Một object có thể giữ logical identity trong khi storage chuyển địa chỉ.

---

# 6. Resource Lifetime

Đây là phần quan trọng nhất.

Resource lifetime không nhất thiết bằng memory lifetime.

Ví dụ:

```text
File {
    OS handle
}
```

Memory chứa wrapper:

```text
File wrapper
```

có thể tồn tại:

```text
100 ns
```

nhưng OS resource:

```text
file descriptor
```

có thể tồn tại lâu hơn tùy API.

Ngược lại, memory wrapper có thể vẫn tồn tại nhưng resource đã:

```text
closed
```

Do đó cần phân biệt:

```text
MemoryState
ResourceState
```

---

# 7. Resource State Machine

Resource type có thể có state machine.

Ví dụ File:

```text
Uninitialized
     ↓
Open
     ↓
Closed
```

hoặc failure:

```text
Open
  ↓
Close
  ↓
Closed
```

Không cho:

```text
Closed → Open
```

trừ khi API định nghĩa `reopen`.

---

# 8. Closed Resource vẫn là Value

Sau:

```text
file.close()
```

resource đã đóng nhưng value có thể vẫn tồn tại trong semantic model cho tới khi consumed/returned.

Axiom khuyến nghị:

```text
close(self) -> Result<(), Error>
```

tức `close` consume owner.

Ví dụ:

```text
let result = file.close()
```

sau đó không thể:

```text
file.read(...)
```

vì ownership đã được consume.

Điều này đơn giản hơn stateful nullable pointer.

---

# 9. Drop không phải close

Đây là một quyết định quan trọng.

Axiom **không đồng nhất**:

```text
Drop == close
```

Drop là:

> cleanup ownership obligation.

`close()` là:

> explicit resource state transition có thể thất bại.

Ví dụ:

```text
file.close() -> Result
```

có thể báo lỗi.

Trong khi:

```text
Drop(file)
```

không được throw/recoverable-error.

---

# 10. Tại sao Drop không được fallible?

Nếu:

```text
Drop -> Result
```

thì compiler sẽ phải xử lý:

```text
return
    ↓
drop
    ↓
drop fails
    ↓
new error
```

và tệ hơn:

```text
panic
    ↓
drop
    ↓
drop fails
    ↓
another panic
```

Axiom tránh toàn bộ mô hình này.

Do đó:

```text
Drop = non-fallible cleanup
close/release/flush = explicit fallible operation
```

---

# 11. Resource cleanup pattern

Ví dụ:

```text
var file = File.open(path)?

file.write(data)?
file.flush()?

file.close()?
```

Nếu programmer không gọi `close()`:

```text
Drop(file)
```

vẫn thực hiện cleanup cần thiết.

Nhưng nếu cần biết kết quả của close:

```text
close()?
```

phải được gọi explicit.

---

# 12. Drop không nhất thiết deallocate

Điều này kế thừa từ memory model.

```text
Drop(x)
```

có nghĩa:

> hoàn thành ownership/resource cleanup.

Không có nghĩa bắt buộc:

```text
free(address)
```

Ví dụ arena:

```text
drop(object)
```

có thể chỉ chạy destructor semantics.

Arena memory được giải phóng khi:

```text
drop(arena)
```

---

# 13. Resource Lifetime và Handle Lifetime

Ví dụ:

```text
let texture = manager.load(...)
let id = texture.handle()
```

Nếu:

```text
drop(texture)
```

thì:

```text
Handle<Texture>
```

có thể:

- stale;
- vẫn valid nếu manager giữ resource;
- hoặc tham chiếu tới logical resource độc lập.

Điều này **do resource abstraction định nghĩa**.

Không được suy luận:

```text
Handle exists → resource alive
```

---

# 14. Strong Resource Handle

Nếu muốn handle giữ resource sống, abstraction phải nói rõ.

Ví dụ:

```text
ResourceRef<T>
```

có thể semantic là:

```text
shared ownership
+
logical identity
```

trong khi:

```text
Handle<T>
```

chỉ là identity.

Như vậy:

```text
Handle<T>
ResourceRef<T>
Owner<T>
view<T>
```

không bị nhập thành một kiểu.

---

# 15. Resource Dependencies

Resource có thể phụ thuộc resource khác.

Ví dụ:

```text
Material
 ├── Texture
 ├── Shader
 └── Sampler
```

Compiler không nên biến dependency graph này thành lifetime annotations.

Thay vào đó library quản lý:

```text
ResourceManager
```

và dùng:

```text
Handle<Texture>
Handle<Shader>
```

hoặc explicit ownership.

---

# 16. GPU In-flight Lifetime

Ví dụ:

```text
let buffer = DeviceBuffer(...)
let event = gpu.copy(buffer, ...)
drop(buffer)
```

Không được để:

```text
GPU still using buffer
        ↓
buffer memory released
```

Do đó:

> In-flight operation giữ một semantic dependency tới storage.

Có thể implementation dùng:

```text
reference count
event tracking
command queue ownership
fence
deferred destruction
```

nhưng đây là **runtime/library implementation**, không phải programmer-written lifetime.

---

# 17. Async In-flight Lifetime

Tương tự:

```text
let buffer = Buffer(...)
let future = socket.read_async(buffer)
```

Nếu Future còn giữ `buffer`:

```text
Future
   ↓
Buffer
```

thì buffer phải tồn tại tới khi operation hoàn thành hoặc bị hủy theo contract.

Compiler/runtime có thể biểu diễn:

```text
Future state
    └── owned buffer
```

Không cần programmer viết:

```text
'buffer_lifetime
```

---

# 18. Drop Future không tự động có nghĩa cancel I/O

Đây là invariant rất quan trọng.

```text
drop(future)
```

chỉ có nghĩa:

> Future state không còn được giữ.

Không được mặc định:

```text
drop(future)
    ==
cancel external operation
```

Một OS/network/GPU operation có thể đã được submit.

Nếu cần cancellation:

```text
CancellationToken
CancellationHandle
```

phải là abstraction explicit.

---

# 19. Cancellation Lifetime

Cancellation là một lifecycle khác:

```text
Running
   ↓
Cancellation Requested
   ↓
Stopping
   ↓
Completed
```

Cancellation không phải:

```text
panic
```

cũng không phải:

```text
Drop
```

và không phải:

```text
thread termination
```

---

# 20. Thread Lifetime

Thread:

```text
Created
   ↓
Running
   ↓
Completed
```

Owner có thể giữ:

```text
JoinHandle<T>
```

JoinHandle là:

> capability để quan sát/combine execution result.

Nó không nhất thiết sở hữu thread stack trực tiếp.

---

# 21. Thread Drop

Axiom không mặc định:

```text
drop(join_handle)
    → kill thread
```

Đây là behavior nguy hiểm.

Thay vào đó:

```text
drop(join_handle)
```

có thể detach theo API semantics, hoặc API có loại:

```text
JoinHandle
DetachedHandle
```

và programmer phải explicit.

Structured concurrency được ưu tiên.

---

# 22. Structured Concurrency

Mô hình ưu tiên:

```text
scope
 ├── task A
 ├── task B
 └── task C

scope exits
     ↓
children resolved/cancelled according to contract
```

Không tạo vô số task "mồ côi" mà lifecycle không rõ.

Ví dụ abstraction:

```text
TaskScope
```

là library-level.

Core chỉ cần semantics:

```text
async
Future
Send
Drop
```

---

# 23. Lock Lifetime

Mutex:

```text
lock()
    ↓
Guard
    ↓
unlock on Drop
```

Guard chính là ownership-bearing capability.

Ví dụ:

```text
let guard = mutex.lock()?
guard.value += 1
```

Khi guard Drop:

```text
unlock
```

Điều này là trường hợp đặc biệt rất đẹp của Axiom:

```text
Ownership
+
Capability
+
Resource cleanup
```

được kết hợp mà không cần lifetime syntax.

---

# 24. Guard không được Copy

```text
MutexGuard<T>
```

phải:

```text
!Copy
```

và semantic ownership rõ ràng.

Không được:

```text
let b = guard
```

mà vẫn dùng `guard`.

Đây là Move.

---

# 25. Guard-derived View

Nếu:

```text
let guard = mutex.lock()?
let v = guard.view()
```

thì:

```text
v
```

không thể sống lâu hơn:

```text
guard
```

vì sau khi unlock:

```text
v
```

không còn capability hợp lệ.

Compiler xử lý quan hệ này tự động.

Không cần:

```text
'guard
```

hay:

```text
'a
```

---

# 26. Async Lock

Sync guard:

```text
MutexGuard<T>
```

không được mặc định sống qua:

```text
await
```

Ví dụ:

```text
let guard = mutex.lock()?
do_work().await
```

→ compiler reject nếu guard sống qua suspension.

Nếu muốn:

```text
AsyncMutex
AsyncMutexGuard
```

thì abstraction riêng định nghĩa semantics phù hợp.

---

# 27. Memory Lifetime vs Execution Lifetime

Ví dụ:

```text
spawn(fn(x))
```

Nếu execution khác thread/task:

```text
x
```

phải có ownership/capability phù hợp.

Không thể:

```text
local view
    ↓
spawn
    ↓
local owner gone
```

Compiler kiểm tra:

```text
ThreadEscape
TaskEscape
```

và yêu cầu:

```text
Send
```

khi execution có thể migrate.

---

# 28. View Across Await

Mặc định:

```text
view<T>
```

không được sống qua `.await` nếu storage/lifetime không có contract cho phép.

Lý do:

```text
await
 ↓
task suspended
 ↓
other code mutates/relocates owner
```

Có thể làm capability invalid.

Owned values thì khác:

```text
let buffer = Buffer(...)
await operation(buffer)
```

Future state machine có thể sở hữu buffer.

---

# 29. Storage Pinning không phải Core primitive

Axiom tiếp tục giữ:

```text
Pin<T>
```

không phải Core primitive.

Nếu cần stable address:

```text
StableBox
StablePool
PinnedStorage
DMA buffer
MMap
```

là explicit storage contract.

Điều này tránh đưa "pinning" vào mọi async code.

---

# 30. Resource Lifetime Across FFI

Foreign API có thể yêu cầu:

```text
create()
use()
release()
```

Axiom wrapper:

```text
struct ForeignResource {
    handle: RawHandle
}
```

và:

```text
impl Drop for ForeignResource
```

có thể gọi foreign release function.

Nhưng:

```text
release()
```

nếu có thể thất bại thì nên có:

```text
close() -> Result
```

trước Drop.

---

# 31. FFI Ownership Contract

Mỗi foreign resource phải khai báo semantic ownership:

```text
Borrowed
OwnedByAxiom
OwnedByForeign
Shared
HandleOnly
```

Không được suy luận ownership từ:

```text
void*
HANDLE
uint64
```

chỉ dựa trên representation.

---

# 32. Lifetime Graph nội bộ compiler

Axiom compiler không cần expose lifetime graph cho programmer nhưng **nên có** trong internal IR.

Ví dụ:

```text
Owner A
  │
  ├── Capability C1
  ├── Capability C2
  │
  └── Storage S

Async F
  │
  └── retains S

GPU Op G
  │
  └── retains S
```

Compiler/optimizer có thể query:

```text
CanDestroy(A)?
CanRelocate(S)?
CanSuspend(F)?
CanMove(A)?
```

---

# 33. Dependency Graph

Một cách model tốt hơn là coi lifetime dưới dạng dependency:

```text
Capability
    depends_on
Owner

View
    depends_on
Storage

GPUOperation
    depends_on
DeviceStorage

Future
    depends_on
CapturedValues

Guard
    depends_on
Lock
```

Một node chỉ được kết thúc khi không còn dependency bắt buộc.

---

# 34. Không cần lifetime annotation

Ví dụ Rust-style:

```text
fn foo<'a>(x: &'a X) -> &'a Y
```

Axiom không cần syntax tương đương.

Thay vào đó:

```text
fn foo(x: view<X>) -> view<Y>
```

Compiler suy luận provenance:

```text
returned Y view
    depends_on
input X capability/storage
```

Nếu không chứng minh được validity:

```text
compile error
```

---

# 35. Lifetime Inference là compiler analysis

Axiom cho phép compiler thực hiện:

```text
liveness analysis
escape analysis
alias analysis
provenance analysis
ownership analysis
capability analysis
suspension analysis
resource dependency analysis
```

tất cả phía sau compiler.

Điểm quan trọng:

> **Không có lifetime syntax không có nghĩa Axiom không có lifetime semantics.**

Ngược lại, compiler phải có semantics rất mạnh.

---

# 36. Lifetime không phải reference counting

Compiler có thể suy luận:

```text
object dead here
```

và destroy ngay.

Không cần:

```text
atomic refcount++
atomic refcount--
```

nếu ownership graph chứng minh được unique ownership.

RC chỉ xuất hiện khi programmer/library chọn:

```text
Rc<T>
Arc<T>
```

---

# 37. Lifetime không phải GC

GC giải quyết:

> object còn reachable không?

Axiom giải quyết:

> ownership/resource obligation còn tồn tại không?

Hai mô hình khác nhau.

Axiom không cần tracing toàn heap.

---

# 38. Resource Cycle

Ví dụ:

```text
A owns B
B owns A
```

không được tự nhiên trở thành:

```text
garbage collection problem
```

Nếu semantic ownership thực sự tạo cycle, library phải dùng:

```text
Handle
Weak
Arc + Weak
EntityId
```

hoặc thiết kế graph bằng logical identity.

Đây là lý do Handle đặc biệt quan trọng.

---

# 39. Weak References

Axiom không cần Core `Weak<T>`.

Library shared ownership có thể cung cấp:

```text
Weak<T>
```

cho:

```text
Arc<T>
```

semantics.

Weak không giữ resource sống.

Upgrade:

```text
Weak<T> → Option<Arc<T>>
```

nếu resource vẫn tồn tại.

---

# 40. Lifetime và logical identity

Một object có thể:

```text
Handle valid
storage relocated
capability expired
```

đây là trạng thái hoàn toàn hợp lệ.

Ví dụ:

```text
Handle<Entity>
```

sống lâu.

Một `view<Entity>` chỉ sống trong một access scope.

Do đó:

```text
Handle lifetime
    > capability lifetime
```

là bình thường.

---

# 41. Resource resurrection

Axiom không cho phép Drop tự nhiên tạo lại ownership.

Ví dụ:

```text
drop(resource)
```

không được ngầm:

```text
resource manager resurrects it
```

Nếu resource có cache/lazy reload:

```text
Handle
    ↓
ResourceManager
    ↓
reload
```

đó là explicit library semantics.

---

# 42. Finalization không tồn tại

Không có:

```text
finalizer
```

giống GC.

Cleanup deterministic.

Nếu resource cần deferred cleanup:

```text
GPU queue
OS async close
RC
epoch
```

thì library/runtime quản lý explicit mechanism.

---

# 43. Process lifetime

Process wrapper:

```text
Process
```

có:

```text
process resource
```

nhưng:

```text
drop(Process)
```

không mặc định:

```text
kill process
```

Termination phải explicit:

```text
terminate()
kill()
wait()
```

Nếu process đã kết thúc:

```text
Process
```

vẫn có thể là wrapper để đọc `ExitStatus`.

---

# 44. Memory mapping

MMap:

```text
MMap
 └── mapped storage
```

View:

```text
view<T>
```

phụ thuộc vào mapping.

Do đó:

```text
unmap()
```

không được phép khi dependent capability còn live.

Compiler/runtime phải enforce:

```text
MMap lifetime > mapped view lifetime
```

---

# 45. DMA

DMA là trường hợp storage + execution dependency.

```text
CPU
 │
 └── DMA Buffer
          │
          └── Device operation
```

Không thể deallocate buffer trong khi device còn truy cập.

Do đó:

```text
submit(buffer)
```

tạo in-flight dependency.

Completion:

```text
event.wait()
```

hoặc explicit synchronization kết thúc dependency.

---

# 46. Lifetime và compiler optimization

Lifetime semantics phải được xác định **trước** optimization.

Sau đó optimizer có thể:

```text
shorten storage lifetime
eliminate allocation
merge allocations
scalarize
promote stack → register
```

nhưng không được làm:

```text
valid capability
    ↓
physical optimization
    ↓
invalid capability
```

---

# 47. Observable lifetime

Một số lifetime trở thành observable:

```text
Drop side effects
FFI release
volatile access
atomic synchronization
I/O
logging
resource destruction
```

Optimizer không thể tùy tiện loại bỏ.

Ví dụ:

```text
Drop(File)
```

không thể bị DCE chỉ vì wrapper value không còn được dùng.

Vì Drop có semantic effect.

---

# 48. Zero-cost lifetime

Mục tiêu Axiom không phải:

> Không có lifetime machinery.

Mà là:

> Lifetime machinery không tạo overhead runtime nếu compiler chứng minh được nó không cần.

Ví dụ:

```text
view
```

có thể compile thành:

```text
pointer + length
```

hoặc thậm chí:

```text
raw pointer
```

nếu length không cần runtime và bounds đã được chứng minh.

Ownership state có thể biến mất hoàn toàn sau verification.

---

# 49. Lifetime Debug Mode

Debug build có thể bổ sung instrumentation:

```text
generation checks
resource state checks
capability assertions
use-after-close checks
```

nhưng release build có thể loại bỏ những check đã chứng minh được.

Semantics không thay đổi.

---

# 50. Compiler Diagnostic

Axiom nên có diagnostics kiểu:

```text
AOWN-xxx
ACAP-xxx
ARES-xxx
AASYNC-xxx
ACONCUR-xxx
```

Ví dụ:

```text
error ARES-204:
cannot destroy MMap while a dependent view is alive

  mmap: MMap
  view: view<u8>

  dependency:
      view#17 → mmap#4
```

AI/IDE có thể đọc structured form:

```text
{
  "error": "ARES-204",
  "operation": "destroy",
  "resource": 4,
  "dependent_capability": 17
}
```

---

# 51. Các invariant đóng băng

## Lifetime

**ARES-20 — Resource Lifetime Is Distinct From Memory Lifetime**

**ARES-21 — Resource Lifetime Is Distinct From Value Lifetime**

**ARES-22 — Capability Lifetime Is Distinct From Ownership Lifetime**

**ARES-23 — Storage Lifetime Is Distinct From Logical Identity Lifetime**

**ARES-24 — Compiler Tracks Lifetime Dependencies Internally**

**ARES-25 — Programmer Lifetime Annotations Are Not Required In Core**

---

## Ownership / Drop

**ARES-26 — Drop Completes Ownership Cleanup**

**ARES-27 — Drop Is Deterministic**

**ARES-28 — Drop Is Non-Fallible**

**ARES-29 — Drop Does Not Imply Physical Deallocation**

**ARES-30 — Drop Does Not Imply Resource Close Unless The Resource Contract Defines It**

**ARES-31 — Fallible Cleanup Requires Explicit Operation**

**ARES-32 — User-Defined Drop Cannot Propagate Recoverable Failure**

**ARES-33 — Panic During Active Unwind Terminates According To Panic Policy**

---

## Resource State

**ARES-34 — Resource State Is Explicitly Defined By Its Abstraction**

**ARES-35 — Closed Resources Cannot Be Used Through APIs Requiring Open State**

**ARES-36 — Consuming Close Transfers Resource To A Closed State**

**ARES-37 — Resource State Is Not Encoded By Null**

**ARES-38 — Resource Wrappers Need Not Contain Runtime Type Metadata**

---

## Capability

**ARES-39 — A Capability Cannot Outlive Its Required Provenance**

**ARES-40 — A Capability Cannot Outlive Required Storage**

**ARES-41 — Owner Destruction Cannot Invalidate A Live Capability**

**ARES-42 — Relocation Cannot Invalidate A Valid Capability**

**ARES-43 — Structural Mutation Cannot Invalidate A Live Capability**

**ARES-44 — Capability Lifetime Is Verified Before Optimization**

---

## Async / Execution

**ARES-45 — In-Flight Async Operations Retain Required Storage Lifetime**

**ARES-46 — Dropping A Future Does Not Imply External Operation Cancellation**

**ARES-47 — Cancellation Is Distinct From Drop**

**ARES-48 — Cancellation Is Distinct From Panic**

**ARES-49 — Sync Guards Cannot Cross Await By Default**

**ARES-50 — Future State Owns Values Required Across Suspension**

**ARES-51 — Execution Lifetime Does Not Imply Resource Ownership**

---

## GPU / External

**ARES-52 — In-Flight GPU Operations Retain Required Storage**

**ARES-53 — GPU Completion May Release In-Flight Dependencies**

**ARES-54 — DMA Operations Retain Required Buffer Lifetime**

**ARES-55 — External Resources Require Explicit Ownership Contracts**

**ARES-56 — FFI Does Not Implicitly Define Lifetime Semantics**

**ARES-57 — Foreign Resource Cleanup Must Respect Its Ownership Contract**

---

## Concurrency

**ARES-58 — Lock Guards Are Ownership-Bearing Capabilities**

**ARES-59 — Lock Guards Are Not Copyable**

**ARES-60 — Guard-Derived Capabilities Cannot Outlive Their Guard**

**ARES-61 — Thread Completion Establishes Required Join Lifetime Semantics**

**ARES-62 — Dropping A Join Capability Does Not Imply Forced Thread Termination**

---

## Performance

**ARES-63 — Lifetime Verification Has No Required Runtime Representation**

**ARES-64 — Proven Lifetime Checks May Be Eliminated**

**ARES-65 — Proven Ownership Does Not Require Reference Counting**

**ARES-66 — Lifetime Semantics Do Not Require Garbage Collection**

**ARES-67 — Compiler May Shorten Physical Lifetime When Observable Semantics Are Preserved**

**ARES-68 — Resource Side Effects Prevent Invalid Dead-Code Elimination**

---

## Architecture

**ARES-69 — Lifetime Semantics Are Stronger Than Lifetime Syntax**

**ARES-70 — Compiler Complexity Must Not Leak Into Ordinary Lifetime Syntax**

**ARES-71 — Resource, Memory, Capability, Ownership, And Execution Lifetimes Are Separate Semantic Axes**

**ARES-72 — One Lifetime Dependency Must Have One Explicit Semantic Reason**

**ARES-73 — Logical Identity May Outlive Storage And Capability**

**ARES-74 — Handle Lifetime Does Not Imply Resource Lifetime**

**ARES-75 — Lifetime Analysis Must Remain Deterministic**

---

# 52. Mô hình Axiom hiện tại

Sau BOOTSTRAP-091, ta có thể mô tả memory/resource architecture của Axiom bằng:

```text
                         VALUE
                           │
                           ▼
                      OWNERSHIP
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        CAPABILITY       STORAGE       RESOURCE
             │             │             │
          view          relocatable      File
       mut_view         stable           Socket
             │             │             GPU
             └──────┬──────┴──────┬──────┘
                    │               │
                    ▼               ▼
                 IDENTITY       EXECUTION
                 Handle          Thread
                 EntityId        Task
                 ResourceId      Future
                    │               │
                    └───────┬───────┘
                            ▼
                     SYNCHRONIZATION
```

Điểm quan trọng nhất là **không còn một “lifetime system” duy nhất**.

Axiom có một **Lifetime Dependency System** nội bộ compiler.

Programmer chỉ thao tác với các abstraction có ý nghĩa:

```text
Owner
view
mut_view
Handle
Future
Guard
Resource
StableStorage
Send
Share
```

---

# 53. Một ví dụ tổng hợp

Một hệ thống game có:

```text
Entity
Texture
GPU Buffer
Async Loading
```

Có thể có:

```text
EntityId
TextureHandle
DeviceBuffer
Future
```

Luồng:

```text
TextureHandle
      │
      ▼
ResourceManager
      │
      ▼
Texture
      │
      ▼
DeviceBuffer
      │
      ▼
GPU Command
      │
      ▼
GpuEvent
```

Trong lúc đó:

```text
TextureHandle
```

có thể sống rất lâu.

```text
view<Texture>
```

chỉ sống trong một operation.

```text
DeviceBuffer
```

có resource lifetime.

```text
GpuEvent
```

có execution/in-flight lifetime.

Compiler không cần programmer viết một dòng lifetime annotation nào.

---

## Quyết định kiến trúc quan trọng nhất của BOOTSTRAP-091

Axiom không nên cố tạo ra một cơ chế "lifetime vạn năng".

Thay vào đó:

> **Ownership xác định trách nhiệm.  
> Capability xác định quyền truy cập.  
> Storage xác định tính ổn định vật lý.  
> Handle xác định identity.  
> Resource state xác định trạng thái tài nguyên.  
> Execution xác định thời gian chạy.  
> Synchronization xác định thứ tự giữa các execution.**

Compiler nối chúng bằng **dependency analysis**.

Đây chính là hướng cho phép Axiom đạt mục tiêu ban đầu của bạn: **mạnh và an toàn ở tầng semantic, nhưng programmer không phải vật lộn với pointer/reference/lifetime như một phần thường xuyên của code.**

### Bước kiến trúc tiếp theo

Sau lifetime, nền tảng còn thiếu một mảnh rất lớn: **BOOTSTRAP-092 — Axiom Error, Result, Panic, Cancellation & Failure Architecture hợp nhất**, để thống nhất cách xử lý:

```text
Result
Option
panic
trap
abort
OOM
I/O failure
timeout
cancellation
thread failure
async failure
GPU failure
FFI failure
process exit
```

mà vẫn giữ nguyên nguyên tắc **không exception runtime bắt buộc, không hidden allocation, không hidden control-flow cost**.