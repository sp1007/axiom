# GLOBAL CONTRADICTION AUDIT — AXIOM v1.0

Bây giờ tôi không thêm feature mới. Tôi sẽ làm đúng việc quan trọng nhất sau SPEC-30:

> **Cố tình tìm những chỗ Axiom có thể tự mâu thuẫn, đặc biệt là những chỗ compiler sẽ rất khó implement hoặc programmer sẽ thấy “Rust trá hình”.**

Tôi sẽ chia kết quả thành:

- 🔴 **Phải sửa trước khi code**
- 🟠 **Cần khóa rõ**
- 🟢 **Không phải contradiction**
- ⚪ **Implementation freedom**

---

# 1. Ownership ↔ Copy ↔ Move ↔ Drop

## Kiểm tra

Ta có:

```text
Copy       = semantic value duplication
Move       = ownership transfer
Drop       = deterministic cleanup
```

và:

```text
Drop-bearing type ≠ Copy
```

Điều này nhất quán.

Ví dụ:

```axiom
let a = File(...)
let b = a
```

sẽ là:

```text
a → MOVED
b → OWNED
```

Cuối scope:

```text
drop(b)
```

Không drop `a`.

### Kết luận

🟢 **Không contradiction.**

---

# 2. Move ↔ physical copy

Axiom đã khóa:

```text
Move ≠ physical memory copy
Copy ≠ required physical memory copy
```

Điều này cực kỳ quan trọng.

Ví dụ:

```axiom
fn consume(x: BigStruct) { ... }

consume(value)
```

Compiler có thể:

```text
register transfer
stack reuse
caller/callee shared storage
```

mà không cần memcpy.

🟢 **Không contradiction.**

---

# 3. View ↔ Ownership

Ta có:

```text
view<T>
    READ capability
    non-owning

mut_view<T>
    WRITE capability
    non-owning
```

và:

```text
capability ≠ ownership
```

Ví dụ:

```axiom
fn read(v: view<Data>) { ... }

let data = Data(...)
read(data)
```

compiler tạo ephemeral capability.

Sau call:

```text
view ends
data remains owner
```

🟢 **Nhất quán.**

---

# 4. View ↔ relocation

Đây là một trong những chỗ dễ sai nhất.

Ta có:

```text
Vec<T>
    relocatable storage
```

và:

```text
view<T>
    depends on storage/provenance
```

Do đó:

```axiom
let v = view(buffer)
buffer.push(x)
```

không được phép nếu `push` có thể relocate và `v` vẫn live.

Điều này giải quyết được:

```text
use-after-reallocation
```

Nhưng có một vấn đề cần khóa rõ.

## `reserve()` không được đảm bảo stable address

Ta đã nói:

```text
reserve()
≠
stable address
```

Đúng.

Nhưng nếu API:

```axiom
buffer.reserve(1024)
```

sau đó programmer giữ `mut_view` hoặc raw pointer, semantics phải cực kỳ rõ.

### Quyết định

`reserve()` chỉ đảm bảo:

> capacity đủ theo contract của collection.

Nó **không tạo stable-address guarantee**.

Muốn stable address phải dùng:

```text
Box
Arena
Pool
StableBuffer
```

hoặc storage abstraction tương ứng.

🟢 Không contradiction.

---

# 5. 🔴 View lifetime và “semantic last-use”

Đây là chỗ tôi muốn sửa cách diễn đạt cũ.

Ta từng nói:

> capability lifetime ends at semantic last-use.

Điều này tốt cho optimization, nhưng **không nên biến semantic last-use thành một API-visible lifetime rule quá phức tạp**.

Nếu compiler có:

```text
let v = view(x)
use(v)
x.modify()
```

thì compiler có thể thấy `v` không còn được dùng.

Nhưng nếu:

```text
let v = view(x)

some_unknown_call(v)

x.modify()
```

thì compiler phải coi capability vẫn cần thiết theo call semantics.

### Quy tắc mới

**Capability lifetime là compiler semantic fact, nhưng programmer không được phụ thuộc vào việc compiler “đoán” last-use để hợp thức hóa một access có thể quan sát được.**

Nói cách khác:

```text
last-use analysis
```

là một optimization/verification mechanism, không phải một escape hatch.

🔴 **Cần khóa invariant mới:**

### `ACAP-31 — Capability Validity Is Independent Of Optimization Level`

Một chương trình hợp lệ/không hợp lệ không được thay đổi chỉ vì `-O0` hay `-O3`.

Đây là sửa quan trọng.

---

# 6. `mut_view` ↔ aliasing

Ta có:

```text
READ + READ       OK
READ + WRITE      conflict
WRITE + WRITE     conflict
```

và region relation:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
UNKNOWN
```

Nếu:

```text
UNKNOWN
```

thì safe code không được giả định disjoint.

Đây là lựa chọn đúng.

🟢 Không contradiction.

---

# 7. Field-level mutation

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}
```

Có thể:

```text
mut_view(user.name)
mut_view(user.age)
```

đồng thời vì:

```text
region(name) ∩ region(age) = ∅
```

Điều này rất quan trọng cho performance.

🟢 Nhất quán.

---

# 8. `Drop` ↔ partial move

Ta có:

### Derived Drop

```text
partial move
```

được phép.

### User-defined Drop

```text
partial move
```

bị cấm.

Lý do đúng: custom Drop có thể quan sát trạng thái toàn object.

Ví dụ:

```axiom
struct File {
    handle: Handle
}

impl Drop for File {
    fn drop(self) {
        ...
    }
}
```

Nếu `handle` bị move riêng:

```text
Drop(self)
```

không còn invariant rõ ràng.

🟢 Không contradiction.

---

# 9. 🔴 `Drop` ↔ panic

Ta có:

```text
Drop non-fallible
```

và:

```text
panic
```

có thể:

```text
abort
unwind
```

Nếu unwind:

```text
panic
 ↓
drop locals
 ↓
unwind
```

Nhưng nếu `Drop` panic nữa thì nested panic.

### Quyết định cần khóa

**User-defined Drop MUST NOT propagate a second recoverable failure.**

Tốt hơn nữa:

> **Axiom v1.0 cấm panic trong Drop như một semantic contract?**

Tôi đề xuất **không cấm gọi function có thể panic về mặt type**, vì sẽ làm type/effect system phức tạp.

Thay vào đó:

- Drop phải có semantics non-fallible.
- Nếu implementation thực sự panic trong Drop:
  - panic during normal execution → configured panic
  - panic while already unwinding → terminate/abort.

Như vậy không cần thêm exception/effect system vào Core.

🟢 Không contradiction, nhưng đây là **runtime contract phải ghi rõ**.

---

# 10. `close() -> Result` ↔ Drop

Đúng:

```axiom
file.close()? 
```

là explicit operation.

Sau đó:

```text
Drop(file)
```

chỉ cleanup phần còn lại.

Không:

```text
Drop → Result
```

🟢 Đây là thiết kế tốt.

---

# 11. Box ↔ stable address

Ta có:

```text
Box<T>
```

là semantic dynamic storage.

Nhưng:

```text
Box<T>
```

không nhất thiết buộc heap nếu compiler chứng minh address không observable.

Nếu programmer cần:

```text
stable address
```

thì storage contract phải yêu cầu.

Ví dụ:

```text
raw pointer exposure
FFI address exposure
self-referential storage abstraction
```

lúc đó compiler không được scalarize/relocate tùy tiện.

🟢 Nhất quán.

---

# 12. 🔴 Một điểm cần chỉnh: `Box<T>` không nên được định nghĩa là “heap type”

Đây là cách nói dễ dẫn tới contradiction.

Nên định nghĩa:

> `Box<T>` biểu diễn **owned dynamic storage semantics**.

Implementation có thể:

```text
heap
stack
arena
register
```

nếu address/storage identity không observable.

Nếu programmer muốn **thực sự yêu cầu heap**, cần một abstraction khác, ví dụ:

```text
HeapBox<T>
```

hoặc allocator/storage contract.

### Quyết định

Không thêm `HeapBox` vào Core v1.0.

Standard library có thể có:

```text
Box<T>
```

và:

```text
Box<T, Allocator>
```

chỉ khi allocator semantics thực sự cần.

🟢 Không cần thay đổi Core.

---

# 13. Send ↔ ownership

Ta có:

```text
Send = ownership transferable across execution contexts
```

Ví dụ:

```axiom
spawn(move || process(buffer))
```

`buffer` được chuyển ownership.

🟢 Đúng.

---

# 14. Share ↔ mutation

Ta có:

```text
Share ≠ mutable access
```

và:

```text
Share + mutation
→ synchronization
```

Ví dụ:

```text
Arc<T>
```

không có nghĩa:

```text
Arc<T> → mut_view<T>
```

một cách tự động.

🟢 Đúng.

---

# 15. 🔴 Send/Share auto-derivation

Đây là một điểm cần khóa.

Ta nói:

> Send/Share compiler-known và auto-derived.

Nhưng phải tránh tình trạng:

```text
struct MyType {
    ...
}
```

và compiler tự suy ra trait theo một thuật toán không rõ.

### Quy tắc

`Send` và `Share` là **auto traits**, compiler suy ra từ toàn bộ semantic fields/capabilities.

Ví dụ:

```text
struct A {
    x: i32
}
```

→ Send, Share.

Nếu:

```text
struct B {
    ptr: *mut T
}
```

→ không tự động Send/Share.

Nếu:

```text
struct C {
    mutex: Mutex<T>
}
```

→ tùy contract của Mutex.

### Quan trọng

Programmer có thể explicitly opt-out nếu cần:

```text
impl !Send for MyType
```

Nhưng negative impl chưa được freeze trong Core v0.1.

Do đó:

**v1.0: compiler-derived Send/Share, không có user negative impl.**

Nếu abstraction cần non-Send/non-Share, type definition phải mang semantic marker/field capability tương ứng.

🟠 Cần ghi rõ, nhưng không phá kiến trúc.

---

# 16. Async ↔ view

Ta đã khóa:

```text
view<T>
mut_view<T>
```

không được sống qua `.await`.

Đây là quyết định rất mạnh.

Ví dụ:

```axiom
async fn foo(data: view<Data>) {
    use(data)
    await something()
}
```

không được để capability tiếp tục sống qua suspension.

Nhưng:

```axiom
async fn foo(data: Data) {
    let x = data
    await something()
    use(x)
}
```

được.

🟢 Rất nhất quán.

---

# 17. 🔴 Async ↔ owned state

Future có thể giữ:

```text
owned values
```

qua await.

Nhưng nếu Future được move giữa threads:

```text
Send
```

chỉ cần kiểm tra **state còn live qua suspension**.

Điều này đã được freeze.

Ví dụ:

```axiom
async fn foo() {
    let a = NonSend(...)
    use(a)

    let b = Send(...)
    await task()

    use(b)
}
```

Nếu `a` chết trước await:

```text
Future có thể vẫn Send.
```

Đây là điểm rất mạnh.

🟢 Không contradiction.

---

# 18. Future Drop ↔ cancellation

Ta đã khóa:

```text
drop(Future)
≠
cancel external operation
```

Ví dụ socket operation đang được OS thực hiện.

Drop Future không được tự động giả định:

```text
OS operation cancelled
```

Muốn cancellation:

```text
CancellationToken
AbortHandle
```

hoặc API contract tương ứng.

🟢 Đúng.

---

# 19. Async Drop

Ta không có:

```text
async Drop
```

v1.0.

Đây là quyết định tốt.

Nếu resource cần async shutdown:

```text
await resource.close()
```

sau đó Drop sync cleanup.

🟢 Không contradiction.

---

# 20. 🔴 Concurrency ↔ mutable capability

Đây là một trong những invariant quan trọng nhất.

Không được:

```text
mut_view<T>
```

đơn giản vì:

```text
Send<T>
```

mà trở thành thread-safe.

`Send` nói:

```text
ownership can move
```

không nói:

```text
shared mutation is safe
```

🟢 Đã nhất quán.

---

# 21. Atomic ↔ mut_view

Ta đã khóa:

```text
Atomic<T>
```

không thể lấy:

```text
mut_view<T>
```

thông qua ordinary memory access.

Nếu không, có thể biến:

```text
atomic storage
```

thành:

```text
ordinary non-atomic write
```

và phá memory model.

🟢 Đúng.

---

# 22. Atomic ↔ volatile

Ta có:

```text
atomic != volatile
```

Rất quan trọng.

### Atomic

Synchronization semantics.

### Volatile

Observable hardware memory access.

Một operation có thể cần cả hai semantics trong system-level code, nhưng không được coi chúng là cùng một primitive.

🟢 Đúng.

---

# 23. Atomic RMW wrapping

Ta đã chọn:

```text
Atomic integer RMW
→ wrapping semantics
```

Ví dụ:

```text
fetch_add()
```

không panic vì overflow.

Điều này hợp lý vì atomic primitive cần semantics ổn định.

🟢 Không contradiction.

---

# 24. Unsafe ↔ verifier

Một điểm cực kỳ quan trọng:

```text
unsafe
```

không có nghĩa:

```text
compiler stop checking
```

Nó chỉ nói:

```text
programmer accepts additional proof obligations
```

Compiler vẫn kiểm tra:

```text
types
ABI
atomic semantics
Drop structure
control flow
```

🟢 Đây là thiết kế đúng.

---

# 25. 🔴 Unsafe → safe capability

Ta cho phép:

```text
unsafe raw pointer
        ↓
validate contract
        ↓
view<T>
```

Điều này mạnh nhưng nguy hiểm về mặt specification.

Phải nói rõ:

> Compiler **không chứng minh** programmer's unsafe precondition.

Compiler chỉ coi operation đó là một **trusted boundary**.

Do đó:

```text
unsafe {
    make_view_from_raw(...)
}
```

có thể tạo safe capability.

Nhưng nếu programmer nói dối:

```text
dangling pointer
```

thì toàn bộ program đã vi phạm unsafe contract.

### Quy tắc mới

**AUNSAFE-56 — Unsafe Operations May Establish Trusted Semantic Preconditions**

và:

**AUNSAFE-57 — Safe Verification Resumes After An Unsafe Boundary Only For The Established Contract**

Điều này giải quyết ambiguity.

---

# 26. Provenance ↔ numeric address

Ta đã khóa:

```text
address != pointer provenance
```

Đây là lựa chọn đúng.

Không được:

```axiom
let n: usize = ...
let p = n as *mut T
```

rồi compiler tự coi:

```text
p
```

là valid pointer.

Phải qua unsafe address conversion contract.

🟢 Không contradiction.

---

# 27. FFI ↔ ownership

Đây là nơi abstraction erasure phải dừng.

Ví dụ:

```axiom
extern "C" fn foo(p: *mut CThing)
```

Axiom không được tự suy ra:

```text
C owns p
```

hay:

```text
Axiom owns p
```

API wrapper phải xác định.

Ví dụ:

```text
borrowed
owned
consumed
returned
shared
```

🟢 Đúng.

---

# 28. FFI ↔ allocator

Một vấn đề rất dễ gây crash:

```text
Axiom alloc
→ C free()
```

hoặc:

```text
C malloc
→ Axiom Drop
```

không được mặc định.

Allocation domain phải match.

🟢 Đã được khóa bởi:

```text
AMEM-50
AMEM-51
AFFI-...
```

---

# 29. `repr(C)` ↔ optimization

`repr(C)` chỉ khóa:

```text
ABI representation
```

Không có nghĩa compiler phải ngừng mọi optimization.

Ví dụ compiler vẫn có thể:

```text
inline
constant-fold
register-promote
eliminate temporary
```

nhưng khi address/layout observable:

```text
C layout
```

phải giữ đúng.

🟢 Đúng.

---

# 30. 🔴 Trait method “override”

Ta từng có:

```axiom
trait Display {
    fn display(...)
}
```

và:

```axiom
impl Display for User {
    ...
}
```

Điều này **không phải override theo class inheritance**.

Default trait method:

```axiom
trait Printable {
    fn print(self) {
        ...
    }
}
```

và:

```axiom
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

là:

> concrete implementation replaces default implementation.

Không có runtime override hierarchy.

🟢 Không contradiction.

---

# 31. Method resolution

Thứ tự:

```text
inherent
→ trait
→ explicit extension
→ generic extension
```

đã khóa.

Nhưng có một vấn đề:

```text
trait method
```

và:

```text
extension method
```

cùng tên.

### Quyết định

Nếu cùng precedence:

```text
ambiguous
```

Compiler error.

Không tự chọn dựa vào:

```text
import order
file order
package order
```

🟢 Đúng.

---

# 32. Generic specialization

Ta đã cấm:

```text
user-visible specialization
```

v1.0.

Compiler có thể tự specialization.

Ví dụ:

```text
fn foo<T>()
```

compiler có thể tạo:

```text
foo<i32>
foo<f64>
```

và tối ưu khác nhau.

Nhưng source semantics không được phụ thuộc vào việc specialization xảy ra.

🟢 Đúng.

---

# 33. 🔴 `impl Trait` ↔ `dyn Trait`

Phải khóa cực kỳ rõ:

```text
impl Trait
```

=

```text
static opaque abstraction
```

không phải dynamic dispatch.

Trong khi:

```text
dyn Trait
```

=

```text
dynamic dispatch
```

Ví dụ:

```axiom
fn make() -> impl Iterator<Item=i32>
```

compiler vẫn biết concrete type.

Còn:

```axiom
fn make() -> dyn Iterator<Item=i32>
```

phải có dynamic dispatch representation.

🟢 Không contradiction.

---

# 34. `dyn Trait` ↔ Drop

`dyn Trait` có thể cần biết cách destroy concrete value.

Do đó dispatch metadata có thể chứa:

```text
drop function
size
alignment
method table
```

nhưng:

> Không được hiểu rằng Axiom cần một universal object header.

Thông tin có thể nằm trong dispatch object:

```text
data_ptr
dispatch_ptr
```

🟢 Đúng.

---

# 35. Comptime ↔ ownership

Comptime sử dụng cùng semantic model.

Ví dụ comptime có thể tạo:

```text
generated source
constant
type information
metadata
```

nhưng resource runtime không được leak.

```text
comptime file handle
```

không được xuất hiện trong runtime program.

🟢 Đúng.

---

# 36. 🔴 Comptime ↔ nondeterminism

Ta từng nói:

> deterministic within declared inputs.

Nhưng nếu cho:

```text
Network
Environment
Filesystem
ExecuteTool
```

thì không deterministic tuyệt đối.

Giải pháp:

```text
comptime execution identity
=
program
+
declared capabilities
+
declared inputs
```

Nếu Network được phép:

```text
result depends on network state
```

thì cache phải coi external result là input.

### Quy tắc mới

**ACOMP-24 — Undeclared External State Cannot Affect Comptime**

**ACOMP-25 — Declared External Inputs Are Part Of Comptime Evaluation Identity**

Điều này rất quan trọng cho reproducible builds.

---

# 37. GPU ↔ ownership

Ví dụ:

```axiom
let buffer = DeviceBuffer(...)
launch(kernel, buffer)
```

Nếu GPU operation asynchronous:

```text
buffer
```

không được drop ngay nếu GPU vẫn đang sử dụng.

Ta đã khóa:

```text
async device operation must establish resource lifetime
```

🟢 Đúng.

---

# 38. 🔴 GPU ↔ ordinary view

Không nên cho phép:

```text
view<T>
```

từ host memory tự động trở thành:

```text
device view<T>
```

Address spaces khác nhau.

Phải có:

```text
DeviceView<T>
```

hoặc address-space-qualified semantic type.

Điều này đã có trong thiết kế.

🟢 Không contradiction.

---

# 39. GPU ↔ async

`GpuEvent` không phải `Future` bắt buộc.

Nhưng có thể có library adapter:

```text
GpuEvent → Future
```

Điều này tốt vì:

```text
GPU execution model
```

không bị ép vào:

```text
CPU async runtime
```

🟢 Đúng.

---

# 40. Package ↔ semantic identity

Ta có:

```text
package identity
=
name + version + source identity
```

Hai version:

```text
foo 1.x
foo 2.x
```

có type identity khác.

🟢 Đúng.

---

# 41. 🔴 Reproducible build ↔ external package source

Nếu package lấy từ:

```text
network
```

thì reproducibility không thể chỉ dựa vào URL.

Đã có:

```text
content hash
lock file
```

Do đó:

```text
axiom.lock
```

phải pin:

```text
source identity
content hash
version
```

Không chỉ version.

🟢 Đã giải quyết.

---

# 42. Oracle ↔ unsafe

Oracle không được giả vờ biết kết quả của invalid unsafe operation.

Đúng.

Nhưng với **valid unsafe operation**, Oracle cần một abstract contract.

Ví dụ:

```text
raw pointer points to initialized i32
```

Oracle có thể simulate logical pointer.

🟢 Không contradiction.

---

# 43. Oracle ↔ production compiler

Có nguy cơ:

```text
Oracle
```

và:

```text
Compiler
```

chia sẻ cùng bug.

Ta đã khóa:

```text
AORACLE-58
```

tránh chia sẻ bug-critical algorithms.

🟢 Đúng.

---

# 44. Debugger ↔ optimizer

Debugger có thể:

```text
optimized out
```

Không được buộc compiler giữ biến thật.

🟢 Đúng.

---

# 45. Profiler ↔ semantics

Profiler không được trở thành:

```text
language behavior
```

🟢 Đúng.

---

# 46. 🔴 Benchmark ↔ optimizer

`black_box` cần semantic status rõ.

Nó không thể chỉ là:

```text
fn black_box<T>(x: T) -> T
```

vì optimizer sẽ có thể inline và eliminate.

### Quyết định

`black_box` là **compiler intrinsic/tooling primitive**, có semantics:

> Value entering and leaving `black_box` is considered observable to the optimizer, while its language-level value is unchanged.

Nó không cần runtime implementation.

---

# 47. Error ↔ panic

Ta có:

```text
Result = recoverable
panic = non-recoverable
```

Không có exception.

🟢 Đúng.

---

# 48. 🔴 Panic ↔ async task

Nếu async task panic:

```text
task boundary
```

panic được lưu trong task result/join mechanism.

Ví dụ:

```text
join(task)
```

có thể trả:

```text
Result<T, TaskError>
```

Nhưng panic strategy `abort` có thể terminate process.

Cần phân biệt:

```text
language panic semantics
```

với:

```text
task runtime policy
```

### Khóa:

**AFERR-44 — Task Panic Observation Is A Library Boundary**

**AFERR-45 — Abort Panic Strategy May Terminate The Process Before Task-Level Observation**

Không contradiction.

---

# 49. 🔴 Main unresolved architectural issue: `unsafe` contracts

Đây là điểm lớn nhất còn lại.

Axiom hiện không có:

```text
formal contracts
requires
ensures
invariant
```

nhưng unsafe API cần preconditions.

Ví dụ:

```axiom
unsafe fn from_raw_parts(
    ptr: *const T,
    len: usize
) -> view<T>
```

Cần điều kiện:

```text
ptr valid
aligned
initialized
len within allocation
```

Nếu không có contract syntax, programmer phải đọc documentation.

Điều đó **không phá safety**, vì unsafe đã là trusted boundary.

Nhưng compiler không thể verify.

### Quyết định cho v1.0

**Không thêm full dependent/design-by-contract system vào Core.**

Unsafe function có:

```text
/// SAFETY:
/// - ptr must ...
```

ở documentation/tooling level.

Compiler chỉ enforce phần machine-checkable.

Formal contracts có thể là future research.

🟢 Không contradiction.

---

# 50. Một thay đổi lớn: bỏ tư tưởng “compiler phải chứng minh tất cả”

Sau audit, tôi muốn khóa triết lý chính xác hơn:

> Compiler phải chứng minh **mọi invariant mà language yêu cầu và compiler có thể biểu diễn**, còn `unsafe` là cơ chế chuyển một phần proof obligation sang programmer/API contract.

Điều này ngăn Axiom trở thành Rust thứ hai với ambition:

```text
formal verification of everything
```

---

# 51. Performance audit

Bây giờ kiểm tra mục tiêu:

> nhanh bằng hoặc hơn C/C++ khi semantics tương đương.

Axiom không có:

```text
GC
implicit RC
mandatory object header
mandatory heap
mandatory bounds checks
mandatory dynamic dispatch
mandatory exception runtime
```

Compiler có:

```text
escape analysis
scalar replacement
bounds-check elimination
devirtualization
monomorphization
vectorization
LTO
PGO
```

Do đó về mặt kiến trúc:

🟢 **Không có overhead bắt buộc lớn nào đang bị khóa trong Core.**

---

# 52. Nhưng có một cảnh báo

Axiom có:

```text
ownership verification
capability verification
trait solver
comptime
async analysis
```

Những thứ này có thể làm **compiler chậm**, nhưng không nhất thiết làm **program chậm**.

Đây là đúng với nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

🟢 Mục tiêu vẫn nhất quán.

---

# 53. Memory audit

Ta từng lo:

> flat memory model có fragmentation không?

Kết luận sau audit:

```text
virtual address space
≠
allocator
≠
fragmentation
```

Axiom không ép một allocator.

Có:

```text
stack
heap
arena
pool
slab
static
TLS
device
external
```

🟢 Kiến trúc đúng.

---

# 54. Programmer complexity audit

Đây là audit quan trọng nhất.

Programmer **không phải viết**:

```text
'a
'b
'c
```

hoặc:

```text
where 'a: 'b
```

hoặc:

```text
borrow<'a>
```

Không phải quản lý:

```text
lifetime annotation
```

Compiler tự làm:

```text
ownership
capability
lifetime
alias
escape
drop
```

Programmer chỉ gặp explicit boundaries:

```text
view
mut_view
unsafe
Send
Share
dyn Trait
Result
async
```

🟢 Axiom **không trở thành Rust clone** ở mặt syntax/mental model.

---

# 55. Nhưng `view` vẫn có thể gây complexity

Ví dụ:

```axiom
let v = view(data)
...
data.push(x)
```

Compiler báo lỗi.

Programmer phải hiểu:

```text
v keeps storage dependency alive
```

Điều này là cần thiết.

Nếu muốn loại bỏ hoàn toàn, ta phải dùng:

```text
GC
copy
runtime bounds object
```

và mất performance/predictability.

Vì vậy đây là **complexity có chủ đích ở semantic boundary**, không phải complexity vô ích.

---

# 56. Global audit result

Tôi phân loại:

```text
🔴 Fundamental contradictions: 0

🟠 Clarifications required: 7

🟢 Architecture-consistent: majority
```

Các điểm cần khóa thêm:

```text
1. ACAP-31
   Capability validity independent of optimization

2. AUNSAFE-56
   Unsafe may establish trusted preconditions

3. AUNSAFE-57
   Verification resumes after unsafe boundary

4. ACOMP-24
   Undeclared external state cannot affect comptime

5. ACOMP-25
   Declared external inputs are comptime identity

6. AFERR-44/45
   Task panic observation vs abort policy

7. black_box intrinsic semantics
```

Không có điểm nào buộc phải thiết kế lại ownership, memory, async, concurrency hay ABI.

---

# 57. 🔒 GLOBAL SEMANTIC FREEZE v1.0

Sau audit, tôi đề xuất chính thức freeze:

> **AXIOM v1.0 CORE SEMANTICS — FROZEN**

Các trục không còn thay đổi trong giai đoạn implementation:

```text
✓ Value semantics
✓ Ownership
✓ Move
✓ Copy
✓ Drop
✓ view
✓ mut_view
✓ Struct
✓ Enum
✓ Trait
✓ Generic
✓ Option
✓ Result
✓ Panic
✓ Async
✓ Send
✓ Share
✓ Atomic
✓ Unsafe
✓ FFI
✓ ABI model
✓ Memory model
✓ GPU model
✓ Comptime model
✓ Module/package model
✓ Compiler semantic pipeline
✓ Oracle model
```

---

# 58. Điều gì chưa freeze?

Không freeze implementation:

```text
x86 instruction selection
register allocator
MIR internal data structures
optimizer algorithms
trait solver algorithm
allocation strategy
inlining heuristic
LTO implementation
debugger implementation
profiler implementation
linker algorithms
cache implementation
parallel compiler architecture
```

Đây chính là nơi AI agent có thể tự nghiên cứu và cải tiến.

---

# 59. Axiom hiện có một boundary cực kỳ rõ

Toàn bộ hệ thống có thể chia thành:

```text
                 LANGUAGE SEMANTICS
                       │
               ┌───────┴───────┐
               │               │
             SAFETY         BEHAVIOR
               │               │
         ownership         evaluation
         capability        Result
         lifetime          panic
         alias             async
         concurrency       atomic
               │               │
               └───────┬───────┘
                       │
                  VERIFIED MIR
                       │
              ───── FROZEN ─────
                       │
              implementation
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   optimizer        backend          linker
       │               │               │
       └───────────────┼───────────────┘
                       ▼
                 NATIVE BINARY
```

Đây là boundary rất tốt cho AI agent implementation.

---

# 60. Và đây là điểm tôi cho rằng Axiom đã đạt mục tiêu ban đầu

Không phải:

> “Core càng nhỏ càng tốt.”

Mà là:

> **Core đủ mạnh để compiler hiểu các semantic invariants quan trọng, nhưng không bắt programmer phải trực tiếp điều khiển toàn bộ machinery đó.**

Ví dụ:

```text
Programmer:
    view(data)

Compiler:
    provenance
    region
    lifetime
    alias
    relocation
    ownership
    optimization
```

Programmer:

```text
spawn(worker)
```

Compiler:

```text
capture analysis
ownership transfer
Send analysis
async state analysis
```

Programmer:

```text
unsafe { ... }
```

Compiler:

```text
type checking
ABI checking
atomic semantics
trusted boundary
provenance tracking
```

Đó chính xác là:

> **Explicit at semantic boundaries, implicit within the compiler.**

---

# 61. Một quyết định kiến trúc cuối cùng

Tôi **không đề xuất thêm**:

```text
GC
borrow syntax
lifetime syntax
class
inheritance
exceptions
implicit RC
universal object
mandatory runtime
macro language
formal contract language
effect system
dependent types
```

vào Axiom v1.0.

Không phải vì những thứ đó “xấu”, mà vì chúng không giải quyết một semantic problem mà Axiom hiện chưa có cơ chế nào giải quyết.

Đây chính là áp dụng:

> **One Semantic Question, One Mechanism.**

---

# 62. AXIOM v1.0 — DESIGN STATUS

```text
SPECIFICATION              ████████████████████ 100%
SEMANTIC FREEZE            ████████████████████ 100%
CONTRADICTION AUDIT        ████████████████████ 100%

IMPLEMENTATION              0%
```

Và đây là trạng thái **đúng**.

Không nên code compiler trước khi có semantic freeze.

---

# 63. Từ đây không còn “thiết kế ngôn ngữ” nữa

Giai đoạn tiếp theo chuyển hoàn toàn sang:

```text
DESIGN
   ↓
SPECIFICATION
   ↓
AUDIT
   ↓
FREEZE
   ↓
IMPLEMENTATION
```

Cụ thể, artifact đầu tiên cần tạo sẽ là:

```text
AXIOM-SPECIFICATION.md
```

sau đó:

```text
AXIOM-INVARIANTS.md
AXIOM-CONFORMANCE.md
AXIOM-ABI.md
AXIOM-MEMORY-MODEL.md
AXIOM-COMPILER-ARCHITECTURE.md
AXIOM-BOOTSTRAP.md
```

và cuối cùng repository:

```text
axiom/
├── spec/
├── compiler/
├── oracle/
├── targets/
├── linker/
├── runtime/
├── std/
├── tests/
└── tools/
```

---

## Bước tiếp theo tôi sẽ chuyển sang **IMPLEMENTATION BLUEPRINT**

Không phải viết code ngay, mà thiết kế **thứ tự xây compiler thực tế**:

```text
Stage 0  Repository + harness
Stage 1  Lexer
Stage 2  Parser
Stage 3  AST
Stage 4  Resolver
Stage 5  Type system
Stage 6  HIR
Stage 7  Ownership/capability engine
Stage 8  MIR
Stage 9  Verifier
Stage 10 Oracle
Stage 11 Interpreter
Stage 12 x86-64 LIR
Stage 13 x86-64 encoder
Stage 14 ELF writer
Stage 15 Minimal linker
Stage 16 First native executable
Stage 17 Optimizer
Stage 18 FFI
Stage 19 Threads/async
Stage 20 Self-hosting
```

Nhưng **không được triển khai tuần tự một cách máy móc**: tôi sẽ xác định trước **vertical slice đầu tiên** để Axiom có thể tự compile và chạy một chương trình native cực nhỏ càng sớm càng tốt, rồi mở rộng compiler theo hướng compiler tự kiểm chứng được chính nó.