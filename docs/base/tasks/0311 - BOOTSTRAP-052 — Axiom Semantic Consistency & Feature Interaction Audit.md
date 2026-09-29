Tiếp tục.

# BOOTSTRAP-052 — Axiom Semantic Consistency & Feature Interaction Audit

Đây là một mốc quan trọng: **không thêm feature mới**. Mục tiêu là kiểm tra xem các quyết định từ 020–051 có thực sự tạo thành **một hệ thống semantic nhất quán** hay đang có những điểm mâu thuẫn.

Kết luận tổng thể sau audit:

> **Mô hình hiện tại có thể thống nhất được. Không cần thay đổi kiến trúc nền tảng.**
>
> Tuy nhiên có một số điểm phải khóa lại ở cấp semantic để compiler không có nhiều cách hiểu khác nhau.

---

# 1. Ownership × Drop

Ví dụ:

```axiom
fn f() {
    let a = Resource()
    let b = a
}
```

Nếu `Resource` là `Drop + !Copy`:

```text
a: OWNED
     ↓ move
b: OWNED
a: MOVED
```

Cuối scope:

```text
drop(b)
```

Không được:

```text
drop(a)
```

### Kết luận

Không mâu thuẫn.

Khóa:

> **Ownership state là nguồn sự thật duy nhất cho việc Drop.**

---

# 2. Ownership × partial move

```axiom
struct S {
    a: ResourceA
    b: ResourceB
}

let x = S { ... }

let y = x.a
```

Sau đó:

```text
x.a = MOVED
x.b = OWNED
```

Nếu Drop được compiler-derived:

```text
drop(x.b)
```

được phép.

Nếu `S` có user-defined Drop:

```text
partial move
```

→ reject.

Điều này đã thống nhất với memory model.

---

# 3. Ownership × async

Ví dụ:

```axiom
async fn f() {
    let data = Buffer.new()
    await something()
    use(data)
}
```

Compiler biến thành:

```text
Future {
    state
    data
}
```

`data` sống qua suspension nên trở thành state field.

Không có vấn đề.

---

# 4. View × async

Ngược lại:

```axiom
async fn f(data: view<Buffer>) {
    await something()
    use(data)
}
```

Không được mặc định chấp nhận.

Lý do:

```text
owner
 ↓
view
 ↓
await
 ↓
future migration / owner lifetime uncertainty
```

### Quy tắc

`view` không được sống qua `.await` trừ khi compiler có execution/storage contract chứng minh provenance vẫn valid.

Đây là **semantic safety rule**, không phải optimization rule.

---

# 5. Owned value × await

Owned value:

```axiom
let data = Buffer.new()
await something()
use(data)
```

được phép.

Compiler tự đưa `data` vào Future state nếu cần.

---

# 6. View × thread

```axiom
thread::spawn(|| use(data_view))
```

không được mặc định cho phép.

Closure có thể escape execution domain.

Compiler phải kiểm tra:

```text
capture
+
view lifetime
+
Send
```

---

# 7. Owned value × thread

```axiom
let data = Buffer.new()

thread::spawn(move || {
    process(data)
})
```

Nếu `Buffer: Send`:

```text
data ownership
      ↓
Move
      ↓
new execution domain
```

hợp lệ.

---

# 8. Send × view

Một `view<T>` có thể được gửi sang thread **chỉ nếu capability provenance và owner lifetime được chứng minh phù hợp**.

Không nên định nghĩa đơn giản:

```text
view<T>: Send
```

mà không xét provenance.

### Khóa:

> **Send là property của giá trị/capability cùng với lifetime/provenance contract, không chỉ của underlying T.**

---

# 9. Share × view

```axiom
Arc<T>
```

có thể tạo:

```text
view<T>
```

cho nhiều readers nếu `T: Share`.

Điều này hoàn toàn phù hợp.

---

# 10. Share không tạo mutable view

Đặc biệt:

```axiom
Arc<T>
```

không tự động cho:

```text
mut_view<T>
```

Nếu muốn mutation:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

---

# 11. `mut_view` × concurrency

Hai capability:

```text
mut_view<T> a
mut_view<T> b
```

chỉ safe nếu:

```text
DISJOINT
```

hoặc abstraction synchronization phù hợp.

Nếu:

```text
UNKNOWN
```

→ reject.

---

# 12. Vec × view × relocation

Đây là một trong những interaction nguy hiểm nhất.

```axiom
let v = Vec.new()
let x = v.view()

v.push(value)
```

Nếu `push()` có thể relocate storage thì `x` không được còn live tại thời điểm relocation.

Compiler có thể:

```text
reject
```

hoặc yêu cầu capability kết thúc trước mutation.

Đây là điểm rất mạnh của Axiom:

> Không cần programmer hiểu `capacity`, `pointer invalidation`, `reallocation` để tránh dangling view.

---

# 13. `reserve()` không giải quyết vấn đề

Không được suy luận:

```text
reserve(100)
```

→ pointer forever stable.

Vì contract của `Vec` vẫn là relocatable.

Nếu cần stable address:

```text
Box
Arena
Pool
stable-storage abstraction
```

---

# 14. Arena × view

```axiom
let arena = Arena.new()

let x = arena.alloc(...)
let v = x.view()
```

`v` không thể sống lâu hơn arena.

Nếu arena bị Drop:

```text
v live
arena destroyed
```

→ compile error.

---

# 15. Arena × async

Tương tự:

```text
arena
 ↓
view
 ↓
await
```

chỉ hợp lệ nếu arena storage contract tồn tại qua Future lifetime.

Nếu không:

→ reject.

---

# 16. Box × view

```axiom
let x = Box.new(data)
let v = view(x)
```

Hợp lệ.

Nếu `Box` bị move:

```text
move(x)
```

thì capability `v` phải được xử lý theo ownership transition.

Không được tồn tại một view trỏ vào storage mà ownership đã chuyển theo cách làm provenance không còn hợp lệ.

---

# 17. Box × stable address

Nếu API yêu cầu:

```text
stable address
```

thì Box contract bảo vệ điều đó.

Compiler không được scalarize storage thành register.

---

# 18. Generic × Drop

```axiom
fn consume<T>(x: T) {
}
```

Nếu `T: Drop`:

```text
drop(x)
```

được compiler chèn theo instantiated semantics.

Nếu `T: Copy`:

```text
```

không có Drop obligation.

Trait solver cung cấp thông tin cho MIR.

---

# 19. Generic × Send

```axiom
fn spawn<T: Send>(x: T)
```

sau monomorphization compiler biết chính xác T.

Không cần runtime trait check.

---

# 20. Generic × Share

Tương tự:

```axiom
fn shared<T: Share>(...)
```

là compile-time constraint.

Không có runtime metadata nếu static dispatch.

---

# 21. Generic × dyn Trait

Có hai abstraction hoàn toàn khác:

```text
T: Trait
```

→ static polymorphism.

```text
dyn Trait
```

→ dynamic polymorphism.

Không được tự động chuyển từ một loại sang loại kia.

---

# 22. Generic × FFI

Không thể export:

```axiom
@export("foo")
fn foo<T>(x: T)
```

với generic chưa specialize.

Compiler phải yêu cầu concrete ABI representation.

Ví dụ:

```text
foo_i32
foo_f64
```

hoặc một wrapper concrete.

---

# 23. `dyn Trait` × FFI

Không FFI-safe mặc định.

Vì representation có thể chứa:

```text
data pointer
vtable pointer
```

nhưng Axiom không muốn biến layout nội bộ thành ABI contract.

Muốn FFI phải có explicit ABI wrapper.

---

# 24. Closure × FFI

Capturing closure:

```text
code + environment
```

không tự động C ABI.

Cần adapter:

```text
fn(context: *mut void, ...)
```

hoặc tương đương.

---

# 25. Async × FFI

Future không phải ABI object mặc định.

Không:

```text
extern "C" async fn
```

với ý nghĩa tự động tương thích C.

Cần explicit polling/callback/opaque handle ABI.

---

# 26. Comptime × ownership

Comptime sử dụng **cùng semantic model**.

Ví dụ:

```axiom
comptime {
    let x = Resource()
}
```

Compiler execution environment phải Drop `x`.

Nhưng resource này không được âm thầm trở thành runtime resource.

---

# 27. Comptime × generated code

Một declaration được comptime tạo ra phải quay lại pipeline:

```text
generated declaration
        ↓
resolution
        ↓
typing
        ↓
ownership
        ↓
capability
        ↓
ABI
```

Không có “generated code bypass”.

---

# 28. Comptime × unsafe

```axiom
comptime {
    unsafe { ... }
}
```

không được bypass sandbox.

Có hai hệ thống khác nhau:

```text
semantic safety
comptime capability sandbox
```

Unsafe chỉ xử lý phần thứ nhất.

---

# 29. Reflection × optimization

Compile-time reflection:

```text
size_of<T>()
offset_of(...)
```

có thể bị compiler fold.

Runtime metadata chỉ tồn tại khi explicitly materialized.

Do đó:

```text
reflection ≠ mandatory runtime
```

---

# 30. Trait × method resolution

Thứ tự vẫn:

```text
1. inherent
2. trait
3. imported extension
4. generic extension
```

Không có interaction gây ambiguity ngoài trường hợp compiler đã quy định.

---

# 31. Trait × specialization

Không cho arbitrary overlapping specialization.

Điều này cực kỳ quan trọng.

Nếu cho:

```text
impl<T> Trait for T
impl<T: X> Trait for T
```

một cách tự do, trait solver có thể trở nên không deterministic.

V1 giữ:

> **Controlled specialization only.**

---

# 32. Trait × default implementation

```axiom
trait A {
    fn f(...) { ... }
}
```

và:

```axiom
impl A for X {
    fn f(...) { ... }
}
```

implementation cụ thể thắng default.

Không cần `override`.

---

# 33. Panic × Drop

```axiom
let a = Resource()
panic("error")
```

Drop chạy theo panic profile.

Nếu unwind:

```text
panic
 ↓
unwind
 ↓
drop initialized resources
```

Nếu abort:

```text
panic
 ↓
abort
```

không cần unwind runtime.

---

# 34. Panic × async

Future panic có cùng semantic model.

Executor quyết định cách quan sát:

```text
JoinHandle
Result
task failure
```

Không biến panic thành exception.

---

# 35. Panic × thread

Thread có thể kết thúc vì panic.

`join()` quan sát kết quả theo runtime API.

Không làm thay đổi ownership semantics.

---

# 36. Panic × FFI

Không được để Axiom panic tự do xuyên C ABI.

Foreign boundary cần catch/convert ở wrapper hoặc terminate theo ABI policy.

---

# 37. Drop × FFI

Foreign resource:

```text
OwnedByAxiom
```

có thể được cleanup bởi Drop.

Nhưng:

```text
Drop
```

không được propagate `Result`.

Nếu cleanup có thể fail:

```axiom
resource.close()?
```

trước Drop.

---

# 38. Atomic × view

`Atomic<T>` không biến thành ordinary:

```text
mut_view<T>
```

vì atomic semantics khác ordinary memory semantics.

Phải thao tác qua atomic API.

---

# 39. Atomic × volatile

Không hợp nhất:

```text
atomic
```

và:

```text
volatile
```

Chúng giải quyết hai vấn đề khác nhau:

```text
atomic    → concurrency/order
volatile  → observable machine access
```

---

# 40. Atomic × GPU

GPU atomic mở rộng semantics với scope:

```text
thread
block/workgroup
device
system
```

nhưng vẫn nằm trong cùng memory model.

---

# 41. GPU × ownership

DeviceBuffer:

```text
owned device storage
```

có ownership semantics.

Kernel launch phải giữ storage sống đến khi operation hoàn thành.

---

# 42. GPU × Drop

Ví dụ:

```text
launch(buffer)
drop(buffer)
```

không được giải phóng device storage nếu operation còn in-flight.

Compiler/runtime phải có:

```text
in-flight retention
```

---

# 43. GPU × view

DeviceView là capability.

Kernel không được giữ view vượt qua lifetime của underlying device storage.

---

# 44. GPU × async

Hai abstraction này có thể kết hợp:

```text
launch kernel
     ↓
GpuEvent
     ↓
await event
```

`await` không tự biến GPU synchronization thành CPU full fence.

`GpuEvent` mang semantics hoàn thành riêng.

---

# 45. GPU × FFI

Foreign GPU handle:

```text
CUdeviceptr
VkBuffer
MTLBuffer
...
```

không tự động trở thành:

```text
DeviceBuffer<T>
```

phải explicit import/ownership contract.

---

# 46. Allocation × FFI

Axiom không đoán:

```text
who allocated this?
who frees it?
```

ABI phải nói rõ.

Ví dụ:

```text
OwnedByAxiom
OwnedByForeign
Borrowed
```

---

# 47. Allocation × optimizer

Allocation là semantic MIR operation.

Nhưng:

```text
ALLOC
```

không nhất thiết thành:

```text
malloc
```

Backend có thể biến thành:

```text
stack
register
arena
pool
caller allocation
```

nếu contract cho phép.

---

# 48. Stable address × optimization

Đây là boundary quan trọng:

```text
address observable
```

→ storage identity trở thành semantic.

Không được optimize away.

---

# 49. Value identity × storage identity

Audit xác nhận ba khái niệm phải giữ độc lập:

```text
Value Identity
Storage Identity
Logical Identity
```

Ví dụ:

```text
Vec element
```

có thể thay đổi physical address nhưng vẫn giữ logical identity thông qua Handle.

---

# 50. Handle × view

Không được coi:

```text
Handle<T>
```

là capability.

Handle chỉ là:

```text
logical identity
```

Muốn access phải resolve thành valid capability.

---

# 51. Method × ownership

```axiom
x.foo()
```

không phải một semantic exception.

Compiler resolve thành:

```text
foo(x)
```

với receiver mode:

```text
Self
view<Self>
mut_view<Self>
```

Ownership checker xử lý như function call bình thường.

---

# 52. Operator × ownership

```axiom
a + b
```

nếu lower qua trait:

```text
Add::add(a, b)
```

thì ownership semantics của call vẫn được áp dụng.

Không có “operator magic” bypass.

---

# 53. Index × capability

```axiom
x[i]
```

nếu read:

```text
view
```

nếu mutable:

```text
mut_view
```

Compiler có thể optimize bounds check sau khi capability/region analysis hoàn thành.

---

# 54. `?` × Drop

Ví dụ:

```axiom
let resource = acquire()?
let x = operation()?
```

Nếu `operation()` trả error:

```text
resource
   ↓
Drop
   ↓
return Err
```

Đây là một trong những lý do deterministic Drop cực kỳ quan trọng.

---

# 55. `?` × async

```axiom
let x = async_call().await?
```

Pipeline:

```text
await
 ↓
Poll
 ↓
Result
 ↓
?
```

Không có conflict.

---

# 56. `?` × FFI

Foreign error phải được wrapper chuyển thành:

```text
Result<T,E>
```

Không để foreign ABI tự động throw/panic vào Axiom.

---

# 57. `?` × GPU

Host API:

```text
launch(...) -> Result<GpuEvent, GpuError>
```

được phép.

Nhưng GPU kernel không nhất thiết có host-style Result runtime.

Kernel error/trap là target-specific.

---

# 58. Module × initialization

Audit xác nhận:

> Module import không được tạo hidden runtime initialization.

Nếu module có static state runtime:

```text
static
```

thì semantics phải explicit.

---

# 59. Comptime × module

Comptime dependency:

```text
module A
 ↓
comptime dependency B
```

là build-time dependency.

Không được biến thành runtime dependency nếu generated output không cần.

---

# 60. Package × runtime

Một package có thể chứa:

```text
library code
+
runtime component
```

nhưng artifact chỉ link phần reachable/required.

---

# 61. Runtime × async

Program:

```axiom
fn main() {
    ...
}
```

không dùng async:

```text
async executor
```

không được tự động link.

---

# 62. Runtime × thread

Không dùng thread:

```text
thread runtime
```

không cần tồn tại trong artifact.

---

# 63. Runtime × allocator

Freestanding:

```text
fn main() ...
```

có thể không có heap allocator.

Nếu chương trình không allocate dynamic storage:

```text
heap runtime = absent
```

---

# 64. Runtime × panic

Nếu compiler chứng minh program không có panic path hoặc profile abort:

```text
panic runtime
```

có thể được loại bỏ phần không reachable.

---

# 65. Runtime × reflection

Không runtime reflection:

```text
metadata runtime
```

không được link.

---

# 66. Runtime × GPU

CPU-only binary:

```text
GPU runtime = absent
```

đã thống nhất.

---

# 67. Runtime × FFI

FFI không đồng nghĩa:

```text
libc
```

Axiom system layer có thể trực tiếp emit syscall/ABI call.

---

# 68. Standard library × third-party dependency

Core standard library phải:

```text
Axiom implementation
+
compiler intrinsics
+
system ABI
```

không phụ thuộc bắt buộc vào:

```text
C runtime
C++ runtime
third-party GC
third-party allocator
```

---

# 69. Một điều chỉnh nhỏ rất quan trọng

Không nên nói:

> “Axiom không bao giờ dùng third-party library.”

Điều chính xác hơn:

> **Axiom Core/standard runtime không có third-party dependency bắt buộc.**

Application vẫn có thể import package bên ngoài.

---

# 70. ABI × optimizer

ABI lowering phải xảy ra **sau semantic verification**.

Không để ABI representation ảnh hưởng ngược lại ownership semantics.

Pipeline:

```text
Typed HIR
 ↓
MIR
 ↓
Verification
 ↓
Semantic optimization
 ↓
Representation
 ↓
ABI
 ↓
LIR
```

---

# 71. Representation × generic

Hai specialization:

```text
Vec<u8>
Vec<u64>
```

có thể có physical representation khác nếu optimization yêu cầu.

Generic source semantics không yêu cầu cùng layout.

---

# 72. Representation × FFI

Chỉ:

```text
@repr(...)
```

mới tạo representation contract.

Default layout vẫn compiler-controlled.

---

# 73. Debug × optimization

Debug information không được thay đổi semantics.

Compiler có thể:

```text
optimized variable
```

không còn physical location cố định.

Debug mapping phải biểu diễn:

```text
source variable
→ value/location history
```

khi có thể.

---

# 74. Unsafe × optimizer

Một điểm rất quan trọng:

> `unsafe` không có nghĩa compiler được phép bỏ qua semantic invariants còn lại.

Unsafe chỉ nói:

```text
programmer established a precondition
```

Ví dụ raw pointer → safe view.

Sau boundary:

```text
safe capability verification
```

tiếp tục.

---

# 75. Unsafe × aliasing

Nếu programmer tạo hai mutable capabilities từ raw pointers và chúng overlap:

```text
undefined/invalid unsafe contract
```

nhưng compiler không được vì thấy `unsafe` mà biến toàn bộ chương trình thành “anything goes”.

Các semantic boundaries khác vẫn giữ.

---

# 76. Compiler verifier architecture

Audit dẫn đến một invariant kiến trúc:

```text
                 ┌───────────────┐
                 │ Ownership     │
                 ├───────────────┤
                 │ Capability    │
                 ├───────────────┤
                 │ Drop          │
                 ├───────────────┤
                 │ Send / Share  │
                 ├───────────────┤
                 │ Async         │
                 ├───────────────┤
                 │ GPU legality  │
                 ├───────────────┤
                 │ FFI legality  │
                 └───────┬───────┘
                         ↓
                  Verified MIR
                         ↓
                   Optimization
```

**Không optimizer nào được bypass Verified MIR.**

---

# 77. Đây là boundary cực kỳ quan trọng

Không được:

```text
MIR
 ↓
optimizer
 ↓
"ồ optimization này làm ownership proof biến mất"
```

Ownership/capability semantics phải được resolve trước.

Sau đó chúng có thể **erase** nếu không còn cần runtime representation.

---

# 78. Semantic proof vs runtime representation

Ví dụ:

```text
mut_view<T>
```

compiler verify:

```text
exclusive
valid provenance
valid lifetime
```

Sau đó machine code có thể chỉ còn:

```text
pointer + length
```

hoặc thậm chí scalarized registers.

Proof biến mất.

**Semantics không biến mất; representation biến mất.**

---

# 79. Interaction với LTO

LTO không được re-interpret language semantics.

Nó nhận:

```text
verified semantic artifacts
```

và tối ưu representation.

---

# 80. Interaction với backend

Backend không biết:

```text
trait solver
ownership rules
borrow rules
Send solver
```

Nó chỉ nhận các invariants đã được đóng gói trong IR.

---

# 81. Interaction với AI

AI có thể hỏi:

```text
Why is this rejected?
Why is this allocation necessary?
Why can't this view cross await?
Why isn't this type Send?
Why isn't this call inlined?
```

Semantic compiler trả lời.

AI không được phép “sửa” semantic bằng cách tự suy đoán.

---

# 82. Những điểm cần **freeze bổ sung**

Audit phát hiện 6 boundary cần ghi thành invariant mới:

### A. Capability + async

Capability không được tự động cross suspension.

### B. Capability + relocation

Relocatable storage không được relocate khi dependent capability còn live.

### C. Send + provenance

Send phải xét cả capability/provenance.

### D. Unsafe

Unsafe không bypass verifier sau boundary.

### E. Runtime

Runtime component là capability-driven/reachability-driven.

### F. Optimization

Optimization chỉ được chạy trên semantic invariants đã được verify.

---

# BOOTSTRAP-052 — Frozen Consistency Invariants

```text
ASEM-20   Ownership and Drop form one consistent resource-lifetime model.
ASEM-21   Moved values are never dropped from the moved-from state.
ASEM-22   Partial moves are allowed only where Drop semantics permit them.
ASEM-23   Owned values may cross await when their ownership remains valid.
ASEM-24   Non-owning capabilities cannot cross suspension without a valid storage/execution contract.
ASEM-25   Cross-execution ownership transfer requires Send validity.
ASEM-26   Send validity includes relevant capability/provenance constraints.
ASEM-27   Share does not imply mutable concurrent access.
ASEM-28   Mutable capability conflicts are checked across execution domains.
ASEM-29   Relocatable storage cannot move while dependent capabilities remain live.
ASEM-30   Reserve does not establish permanent address stability.
ASEM-31   Arena lifetime bounds capabilities derived from arena storage.
ASEM-32   Stable-address contracts constrain storage optimization.
ASEM-33   Generic Drop behavior is resolved before final code generation.
ASEM-34   Generic Send/Share constraints are compile-time properties.
ASEM-35   Static generic dispatch does not require runtime trait metadata.
ASEM-36   Dynamic trait representation is explicit and ABI-sensitive.
ASEM-37   Generic declarations cannot be exported through an unresolved foreign ABI.
ASEM-38   Dynamic trait values are not automatically FFI-safe.
ASEM-39   Capturing closures are not automatically FFI-safe.
ASEM-40   Futures are not automatically FFI-safe.
ASEM-41   Comptime execution uses the same core semantic safety rules.
ASEM-42   Comptime sandbox rules are independent from unsafe semantics.
ASEM-43   Generated declarations re-enter normal semantic verification.
ASEM-44   Compile-time reflection does not imply runtime metadata.
ASEM-45   Trait method resolution remains deterministic under all abstraction forms.
ASEM-46   Arbitrary overlapping specialization is not permitted.
ASEM-47   Panic cleanup follows the same ownership/Drop model.
ASEM-48   Panic does not become a recoverable exception automatically.
ASEM-49   Axiom panic does not cross foreign ABI boundaries implicitly.
ASEM-50   Fallible resource cleanup is explicit rather than encoded in Drop.
ASEM-51   Atomic semantics remain distinct from ordinary capability semantics.
ASEM-52   Volatile semantics remain distinct from atomic semantics.
ASEM-53   GPU synchronization extends, rather than replaces, the memory model.
ASEM-54   In-flight GPU operations retain required storage lifetime.
ASEM-55   Foreign GPU handles do not implicitly become owned device storage.
ASEM-56   Foreign allocation ownership must be explicitly specified.
ASEM-57   Module import does not imply runtime initialization.
ASEM-58   Runtime components are independently linkable.
ASEM-59   Unused runtime components must not be mandatory dependencies.
ASEM-60   FFI does not imply a C runtime dependency.
ASEM-61   ABI lowering occurs after semantic verification.
ASEM-62   Representation contracts do not redefine source-level ownership semantics.
ASEM-63   Debug information cannot alter program semantics.
ASEM-64   Unsafe boundaries cannot disable unrelated semantic verification.
ASEM-65   Safe verification resumes after an unsafe boundary for established contracts.
ASEM-66   Optimization operates only on semantically verified IR.
ASEM-67   Optimization may erase semantic machinery only after its obligations are discharged.
ASEM-68   Erasing a proof representation does not erase the corresponding language semantics.
ASEM-69   Backend code generation cannot reinterpret source-level semantic rules.
ASEM-70   LTO preserves previously established semantic invariants.
ASEM-71   Runtime behavior must remain consistent across optimization levels.
ASEM-72   Comptime-generated code is semantically equivalent to ordinary source code after insertion.
ASEM-73   Capability provenance remains valid across all optimization transformations.
ASEM-74   Observable storage identity constrains optimization.
ASEM-75   Logical identity is distinct from physical storage identity.
ASEM-76   Handle values are not memory capabilities.
ASEM-77   Method syntax cannot bypass ownership or capability verification.
ASEM-78   Operator syntax cannot bypass ownership or capability verification.
ASEM-79   Error propagation cannot bypass deterministic cleanup.
ASEM-80   Async error propagation preserves Future and Drop semantics.
ASEM-81   GPU error handling does not implicitly become host exception handling.
ASEM-82   FFI wrappers explicitly translate foreign failure semantics.
ASEM-83   Semantic verification precedes representation erasure.
ASEM-84   Semantic verification precedes ABI lowering.
ASEM-85   Semantic verification precedes aggressive optimization.
```

---

# Kết luận của 052

Sau audit, kiến trúc hiện tại **không cần thêm một hệ thống safety thứ hai**.

Đây là điều rất đáng giữ.

Axiom hiện có thể quy về một chuỗi khá sạch:

```text
                    SOURCE
                      │
                      ▼
              ┌───────────────┐
              │ Type / Trait  │
              └───────┬───────┘
                      ▼
              ┌───────────────┐
              │ Ownership     │
              │ Capability    │
              │ Drop          │
              └───────┬───────┘
                      ▼
              ┌───────────────┐
              │ Concurrency   │
              │ Async / GPU   │
              │ FFI           │
              └───────┬───────┘
                      ▼
                VERIFIED MIR
                      │
             ┌────────┴────────┐
             ▼                 ▼
       Semantic Opt       Representation
             │                 │
             └────────┬────────┘
                      ▼
                   LIR
                      ▼
                Machine IR
                      ▼
                 Native Code
```

Điểm quan trọng nhất:

> **Tất cả các feature lớn của Axiom cuối cùng đều hội tụ về Verified MIR.**

Không có:

```text
Rust safety engine
GPU safety engine
Async safety engine
FFI safety engine
```

tách rời nhau.

Chúng là các verifier khác nhau trên **cùng một semantic model**.

---

# BOOTSTRAP-053 — Compiler Architecture & Verified MIR Design

Bước kế tiếp nên chuyển hẳn từ **“Axiom nên có semantics gì?”** sang:

> **“Compiler phải được xây như thế nào để thực thi chính xác tất cả semantics đó?”**

053 sẽ khóa:

```text
Lexer
Parser
AST
Resolver
HIR
Typed HIR
MIR
SSA
Ownership verifier
Capability verifier
Drop elaborator
Trait solver
Async lowering
Closure lowering
Pattern lowering
Comptime VM
GPU legality
FFI checker
Semantic optimizer
LIR
Machine IR
Object writer
Linker
```

và đặc biệt là **định nghĩa cấu trúc MIR cụ thể** — đây sẽ là nền móng để AI agent bắt đầu thực sự viết compiler Axiom thay vì tiếp tục chỉ viết specification.