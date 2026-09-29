# BOOTSTRAP-411 — OWNERSHIP, CAPABILITY & EFFECT INTEGRATION

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 409 Type System + 410 Trait/Method Resolution  
**Mục tiêu:** hợp nhất Type, Ownership, Capability và Effect thành **một semantic verification system**, nhưng vẫn giữ cho lập trình viên không phải viết lifetime/borrow annotation.

Đây là một trong những phần quan trọng nhất của Axiom, bởi nó quyết định liệu mục tiêu:

> **“đơn giản hơn C++ nhưng vẫn có hiệu năng native”**

có thực sự đạt được hay không.

---

# 411.1. Bốn hệ thống phải tách biệt

Axiom tuyệt đối không gộp chúng thành một khái niệm:

```text
Type
Ownership
Capability
Effect
```

Ví dụ:

```axiom
fn read_file(file: File) -> Result<Text, IOError>
```

Compiler cần biết:

```text
Type:
    file : File

Ownership:
    file được move hay view?

Capability:
    function được READ filesystem?

Effect:
    function có IO?
```

Một function có thể:

```text
cùng Type
khác Ownership

hoặc:

cùng Type + Ownership
khác Effect
```

---

# 411.2. Ownership là trạng thái semantic

Mỗi value trong MIR có ownership state.

Tập trạng thái cơ bản:

```text
UNINITIALIZED
OWNED
MOVED
PARTIALLY_MOVED
BORROWED_SHARED
BORROWED_MUT
DROPPED
INVALID
```

Compiler theo dõi state-flow của từng value.

Ví dụ:

```axiom
let x = File.open(path)?
let y = x
```

Nếu `File` không `Copy`:

```text
x:
OWNED → MOVED

y:
OWNED
```

Sau đó:

```axiom
x.read()
```

→ compile error.

---

# 411.3. Move không phải physical copy

Đây là invariant rất quan trọng.

```axiom
let y = x
```

không có nghĩa:

```text
memcpy(x → y)
```

Semantic nghĩa là:

```text
ownership(x) → ownership(y)
```

Backend có toàn quyền:

- register move;
- SSA rename;
- pointer move;
- stack slot reuse;
- scalar replacement;
- elide hoàn toàn storage.

Do đó ownership system **không tạo runtime cost**.

---

# 411.4. Copy là semantic contract

Một type chỉ `Copy` khi:

```text
copying value
```

không tạo thêm ownership obligation.

Ví dụ:

```text
i32
f64
bool
small immutable struct
```

có thể Copy.

Nhưng:

```text
File
Socket
Mutex
Box<T>
Vec<T>
```

thường không Copy.

Compiler không quyết định Copy chỉ dựa trên:

```text
"bit pattern có thể copy được"
```

mà dựa trên semantic ownership.

---

# 411.5. Clone khác Copy

Nếu type có:

```axiom
fn clone(self: view<Self>) -> Self
```

thì programmer phải yêu cầu:

```axiom
let y = x.clone()
```

Clone có thể:

- allocate;
- copy buffer;
- increment resource;
- deep-copy graph;
- thực hiện arbitrary computation.

Compiler không được biến Clone thành Copy.

---

# 411.6. Capability Model

Capability đại diện cho **quyền truy cập**.

Core capability tối thiểu:

```text
READ
WRITE
MOVE
DROP
```

Ví dụ:

```text
view<T>
```

tương đương capability:

```text
READ(T)
```

Còn:

```text
mut_view<T>
```

tương đương:

```text
WRITE(T)
```

với exclusive access.

---

# 411.7. Access Matrix

Compiler sử dụng quy tắc:

| Access A | Access B | Kết quả |
|---|---|---|
| READ | READ | OK |
| READ | WRITE | Conflict |
| WRITE | READ | Conflict |
| WRITE | WRITE | Conflict |
| MOVE | anything | Conflict |
| DROP | anything | Conflict |

Nhưng vùng nhớ cũng được đưa vào phép kiểm tra.

Ví dụ:

```axiom
fn update_x(v: mut_view<Vec2>)
fn read_y(v: view<Vec2>)
```

không nhất thiết conflict nếu compiler chứng minh:

```text
x region ∩ y region = ∅
```

---

# 411.8. Region là semantic object

Compiler không chỉ ghi:

```text
view<Vec2>
```

mà theo dõi provenance/region.

Ví dụ:

```axiom
v.x
v.y
```

có thể tạo:

```text
Region(Vec2.x)
Region(Vec2.y)
```

Quan hệ:

```text
DISJOINT
```

cho phép parallel access.

Đây là cơ sở cho:

- data race verification;
- parallelism;
- SIMD;
- GPU;
- zero-copy;
- alias analysis.

---

# 411.9. Unknown Overlap

Nếu compiler không chứng minh được:

```text
A ∩ B = ∅
```

thì mặc định:

```text
UNKNOWN
```

và safe code phải xử lý như có thể overlap.

Không được:

> “Có vẻ như hai vùng này không overlap.”

Ví dụ:

```axiom
fn process(a: mut_view<Array>, b: mut_view<Array>)
```

nếu compiler không biết hai view độc lập:

```text
→ reject
```

hoặc yêu cầu abstraction/library cung cấp invariant disjointness.

---

# 411.10. Compiler có thể suy ra disjointness

Không bắt programmer viết:

```text
borrow(a)
borrow_mut(b)
lifetime(...)
```

Compiler phân tích:

```text
struct Particle {
    position: Vec3
    velocity: Vec3
}
```

và:

```axiom
fn update(
    p: mut_view<Particle>
) {
    ...
}
```

Có thể nội bộ chia:

```text
p.position
p.velocity
```

thành các region độc lập.

Đây là một điểm khác biệt cốt lõi của Axiom:

> **Borrow reasoning là compiler implementation detail, không phải programming-language bureaucracy.**

---

# 411.11. Ownership Graph

Compiler xây:

```text
OwnershipGraph
```

với node:

```text
Value
Field
Aggregate
View
Resource
Storage
```

và edge:

```text
OWNS
CONTAINS
BORROWS
ALIASES
MOVES_TO
DERIVED_FROM
```

Ví dụ:

```text
p
│
├── position
└── velocity
```

Khi:

```axiom
let x = p.position
```

compiler biết:

```text
p.position → MOVED
p.velocity → still valid
```

nếu type/Drop policy cho phép partial move.

---

# 411.12. Partial Move

Struct thông thường:

```axiom
struct User {
    id: u64
    name: String
}
```

có thể:

```axiom
let name = user.name
```

Sau đó:

```text
user.name = MOVED
user.id   = VALID
```

Nhưng `user` không còn được coi là fully initialized.

Compiler phải ngăn:

```axiom
drop(user)
```

nếu Drop implementation không hỗ trợ partial state.

---

# 411.13. Custom Drop

Nếu programmer định nghĩa custom Drop cho struct:

```axiom
struct Resource {
    handle: RawHandle
}

impl Drop for Resource {
    ...
}
```

compiler phải coi toàn bộ object là một ownership unit.

Partial move bị hạn chế vì compiler không thể tự ý phá invariant mà custom Drop có thể yêu cầu.

Điều này là **semantic safety**, không phải hạn chế optimizer.

---

# 411.14. Capability Reborrow nội bộ

Axiom không expose borrow syntax, nhưng compiler có thể tạo temporary capability:

```text
Owner
 ↓
Ephemeral READ capability
 ↓
Function call
 ↓
Capability expires
 ↓
Owner usable
```

Ví dụ:

```axiom
fn inspect(x: view<Data>)

let d = Data(...)
inspect(d)
use(d)
```

Compiler tự tạo view tạm thời.

Không cần:

```text
&d
borrow(&d)
lifetime<'a>
```

---

# 411.15. Escape Analysis

Một view chỉ hợp lệ nếu:

```text
lifetime(view) ⊆ lifetime(owner)
```

Compiler kiểm tra view có:

```text
RETURN
STORE
CAPTURE
ASYNC
THREAD_TRANSFER
```

hay không.

Ví dụ:

```axiom
fn bad(x: Data) -> view<Data> {
    view(x)
}
```

không hợp lệ nếu `x` bị destroy khi function kết thúc.

Compiler có thể báo:

```text
returned view references local owner
```

---

# 411.16. Closure Capture

Closure:

```axiom
let f = || use(x)
```

compiler phân tích:

```text
x
 ↓
READ capture
```

Nếu closure mutate:

```text
WRITE capture
```

Nếu closure lấy ownership:

```text
MOVE capture
```

Programmer không cần chỉ định:

```text
move
ref
mut
```

trong trường hợp compiler có thể suy ra.

---

# 411.17. Async Capture

Async phức tạp hơn closure vì execution có suspension.

Ví dụ:

```axiom
async fn work(x: Data) {
    await io()
    use(x)
}
```

Compiler phải đảm bảo `x` tồn tại qua suspension point.

Nó có thể:

```text
promote x into coroutine state
```

hoặc:

```text
move x into task storage
```

nếu cần.

Đây là **storage transformation**, không phải thay đổi semantic ownership.

---

# 411.18. Thread Transfer

Khi:

```axiom
spawn(|| use(x))
```

compiler kiểm tra:

```text
closure capture
+
thread lifetime
+
Send
```

Nếu closure sống lâu hơn current scope, compiler không cho capture một local capability không thể transfer.

Ví dụ conceptually:

```text
local mutable view
        ↓
spawn
        ↓
cross-thread
```

→ reject nếu không có transfer proof.

---

# 411.19. Send / Share

Axiom dùng trait-based model.

```text
Send<T>
Share<T>
```

Ý nghĩa:

```text
Send<T>
    ownership của T có thể chuyển execution domain

Share<T>
    T có thể được chia sẻ read-only giữa execution domains
```

Đây là trait/property semantic.

Không phải compiler magic riêng cho từng struct.

---

# 411.20. Mutable Sharing

Axiom không coi:

```text
Share<T>
```

là đủ để mutate.

Mutable shared state phải đi qua abstraction:

```text
Atomic<T>
Mutex<T>
RwLock<T>
Channel<T>
Actor<T>
AtomicShared<T>
```

Do đó:

```text
shared
≠
shared mutable
```

---

# 411.21. Effect System

Function có thể có effect:

```text
PURE
ALLOC
IO
FS
NETWORK
THREAD
ASYNC
GPU
UNSAFE
PANIC
SYSTEM
FFI
```

Effect không phải type.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

có thể:

```text
PURE
```

Trong khi:

```axiom
fn read_file(...) -> Result<...>
```

có:

```text
FS + IO
```

---

# 411.22. Effect Inference

Programmer không phải luôn khai báo:

```axiom
fn foo() effects(FS, IO)
```

Compiler có thể infer:

```text
foo
 ↓
read_file
 ↓
FS + IO
```

→ effect(foo):

```text
FS + IO
```

Tuy nhiên public API có thể yêu cầu explicit effect contract khi cần:

- security boundary;
- plugin;
- sandbox;
- FFI;
- capability API;
- audit.

---

# 411.23. Capability và Effect khác nhau

Đây là distinction rất quan trọng.

```text
Effect = function có thể làm gì

Capability = function hiện tại đang có quyền gì
```

Ví dụ:

```text
Effect:
    FS_READ

Capability:
    ReadFilesystem("/tmp/data")
```

Một function có thể **có khả năng thực hiện FS read về mặt semantic**, nhưng caller không cấp capability tương ứng.

→ invocation bị reject.

---

# 411.24. Capability Propagation

Nếu:

```axiom
fn a()
```

gọi:

```axiom
b()
```

và `b` yêu cầu:

```text
Network
```

thì compiler phải biết:

```text
a
```

có:

```text
Network capability
```

hoặc có cơ chế capability acquisition hợp lệ.

Không được silently escalate privilege.

---

# 411.25. Unsafe Boundary

`unsafe` cho phép programmer thực hiện operation mà compiler không thể chứng minh.

Ví dụ:

```axiom
unsafe fn from_raw(p: *mut T) -> ...
```

Nhưng unsafe **không xóa semantic model**.

Sau unsafe boundary:

```text
raw pointer
 ↓
validated capability
 ↓
safe MIR
```

Compiler tiếp tục kiểm tra:

- type;
- ownership;
- effect;
- capability;
- lifetime/provenance contract.

---

# 411.26. FFI

FFI là một capability boundary.

Ví dụ:

```axiom
extern "C" fn memcpy(...)
```

Compiler biết:

```text
ABI = C
unsafe = true
effect = external
```

Ownership/capability của pointer vẫn phải được mô tả hoặc chuyển qua unsafe contract.

Axiom không giả định C function là safe chỉ vì signature hợp lệ.

---

# 411.27. Ownership + Trait Resolution

Đây là điểm nối trực tiếp với BOOTSTRAP-410.

Ví dụ:

```axiom
trait Writer {
    fn write(self: mut_view<Self>, data: view<Bytes>)
}
```

Khi:

```axiom
writer.write(data)
```

compiler phải đồng thời giải:

```text
Method:
    Writer::write

Type:
    writer : Writer

Receiver:
    mut_view<Writer>

Argument:
    view<Bytes>

Capability:
    WRITE(writer)
    READ(data)

Ownership:
    writer remains owned
    data remains owned

Effect:
    IO
```

Method resolution chỉ thành công khi **tất cả semantic constraints** đều hợp lệ.

---

# 411.28. Verification Model

Compiler tạo một `SemanticVerificationState`:

```text
VerificationState {
    Types
    Ownership
    Regions
    Capabilities
    Effects
    Initialization
    DropState
    AsyncState
    ExecutionDomain
    StorageDomain
}
```

Mỗi MIR operation cập nhật state.

Ví dụ:

```text
LOAD
→ READ capability

STORE
→ WRITE capability

MOVE
→ ownership transition

CALL
→ consume/produce capabilities

AWAIT
→ suspension verification

RETURN
→ escape verification

DROP
→ ownership termination
```

---

# 411.29. CompilerDB

Thêm các database:

```text
OwnershipDB
RegionDB
CapabilityDB
EffectDB
EscapeAnalysisDB
DropStateDB
ConcurrencyCapabilityDB
UnsafeContractDB
SemanticVerificationDB
```

Các DB này không phải các checker độc lập hoàn toàn.

Chúng cùng truy vấn:

```text
CompilerDB
```

để tránh việc:

```text
ownership checker nghĩ A
async checker nghĩ B
GPU checker nghĩ C
```

---

# 411.30. Proof Artifacts

Compiler phải sinh được:

```text
OwnershipProof
MoveProof
CopyProof
RegionDisjointnessProof
CapabilityProof
EffectProof
EscapeProof
DropProof
SendProof
ShareProof
UnsafeBoundaryProof
FFIContractProof
```

Ví dụ:

```text
RegionDisjointnessProof

A = Particle.position
B = Particle.velocity

relation:
    DISJOINT

therefore:
    WRITE(A) + READ(B) = valid
```

---

# 411.31. Diagnostic Model

Compiler không chỉ báo:

```text
borrow error
```

mà phải giải thích semantic chain:

```text
EOWN-001

value `x` was moved here
    line 10

ownership transferred to `y`
    line 10

later use occurs here
    line 14

`x` is no longer owned
```

Hoặc:

```text
ECAP-004

mutable access conflicts with existing read capability

write:
    data[0..128]

existing read:
    view(data[64..192])

possible overlap:
    [64..128]
```

Điều này đặc biệt quan trọng với AI agent.

---

# 411.32. Không expose Borrow Checker

Compiler nội bộ có thể sử dụng:

```text
borrow graph
region inference
alias analysis
escape analysis
lifetime constraints
```

nhưng tài liệu ngôn ngữ **không nên yêu cầu programmer học một “borrow language”**.

Programmer chủ yếu suy nghĩ:

```text
Tôi sở hữu value này.
Tôi muốn đọc nó.
Tôi muốn sửa nó.
Tôi muốn chuyển ownership.
```

Compiler suy nghĩ:

```text
region
alias
provenance
lifetime
capability
```

Đây chính là abstraction boundary của Axiom.

---

# 411.33. Khi Compiler Không Chứng Minh Được

Safe code không được dựa trên phỏng đoán.

Có ba lựa chọn:

```text
1. Compiler chứng minh được
   → accept

2. Library abstraction có proof/invariant
   → accept

3. Programmer vượt qua unsafe boundary
   → accept với contract
```

Không có lựa chọn:

```text
4. compiler đoán là chắc đúng
```

---

# 411.34. Zero-Cost Requirement

Ownership/Capability/Effect verification phải là **compile-time semantic system**.

Không được tự động thêm:

```text
reference counting
runtime borrow checks
object headers
GC
hidden locks
hidden synchronization
```

trừ khi programmer chọn một library abstraction có những chi phí đó.

Ví dụ:

```axiom
Box<T>
```

không có RC.

```axiom
Arc<T>
```

có atomic reference counting vì **type semantics yêu cầu**.

---

# 411.35. Các Invariant `ASEM`

```text
ASEM-01  Type identity is independent of ownership.
ASEM-02  Ownership is deterministic.
ASEM-03  Move is an ownership transition.
ASEM-04  Move does not imply physical copying.
ASEM-05  Copy requires semantic copyability.
ASEM-06  Clone is explicit.
ASEM-07  Drop is deterministic.
ASEM-08  Moved values cannot be read.
ASEM-09  Moved values cannot be dropped twice.
ASEM-10  Partial moves are field-sensitive where permitted.
ASEM-11  Custom Drop preserves whole-object invariants.
ASEM-12  READ+READ is valid.
ASEM-13  READ+WRITE requires disjointness.
ASEM-14  WRITE+WRITE requires disjointness.
ASEM-15  MOVE conflicts with active capabilities.
ASEM-16  Unknown overlap cannot be assumed disjoint.
ASEM-17  Views cannot outlive their provenance.
ASEM-18  Escaping views require a valid owner/provenance.
ASEM-19  Closure captures are compiler-inferred.
ASEM-20  Async captures survive suspension correctly.
ASEM-21  Cross-domain transfer requires Send proof.
ASEM-22  Shared access requires Share semantics.
ASEM-23  Mutable shared state requires explicit synchronization.
ASEM-24  Effects are deterministic and inferable.
ASEM-25  Capability is distinct from effect.
ASEM-26  Capability escalation is forbidden.
ASEM-27  Unsafe cannot silently erase verification state.
ASEM-28  FFI boundaries have explicit semantic contracts.
ASEM-29  No ownership/capability violation reaches codegen.
ASEM-30  Verification results are reproducible and explainable.
```

---

# 411.36. Kiến trúc hoàn chỉnh

Sau 411, phần semantic core có hình dạng:

```text
                 ┌──────────────┐
                 │ Name Resolver│
                 └──────┬───────┘
                        ↓
                 ┌──────────────┐
                 │ Type System  │
                 └──────┬───────┘
                        ↓
             ┌──────────┴──────────┐
             ↓                     ↓
       Trait Solver          Generic Solver
             ↓                     ↓
             └──────────┬──────────┘
                        ↓
                 Method Resolution
                        ↓
              ┌─────────┴─────────┐
              ↓                   ↓
         Ownership             Effects
              ↓                   ↓
         Capabilities        Effect Rules
              └─────────┬─────────┘
                        ↓
                Semantic Verification
                        ↓
                       MIR
```

Điểm quan trọng nhất:

> **Ownership, capability và effect không phải ba “tính năng phụ”. Chúng là các chiều khác nhau của cùng một semantic verification state.**

Nhờ vậy Axiom có thể đạt mục tiêu ban đầu: **lập trình viên viết code gần với ngôn ngữ thông thường, còn compiler âm thầm thực hiện phần lớn công việc mà Rust/C++ buộc programmer phải quản lý thủ công.**

**BOOTSTRAP-411 — SPECIFIED / FROZEN.**