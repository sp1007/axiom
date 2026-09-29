# BOOTSTRAP-161 — Security Model, Unsafe Boundary, Constant-Time & Memory-Safety Hardening
**STATUS: FROZEN / COMPLETED**

> **Axiom phải cho phép lập trình hệ thống ở mức rất thấp mà không biến toàn bộ ngôn ngữ thành unsafe. Safe code phải có các bảo đảm mạnh về memory safety, capability safety và data-race safety; unsafe chỉ là nơi programmer nhận trách nhiệm đối với những điều compiler không thể chứng minh.**

Đây là bước nối trực tiếp từ `BOOTSTRAP-160`, nhưng phạm vi lớn hơn debugger: nó xác định **ranh giới tin cậy của toàn bộ Axiom**.

---

# 1. Mô hình security tổng thể

Chốt:

```text
                         Axiom Program
                              │
                ┌─────────────┴─────────────┐
                │                           │
             SAFE CODE                  UNSAFE CODE
                │                           │
                ▼                           ▼
        Compiler proves              Programmer contract
        required invariants          + compiler checks
                │                           │
                └─────────────┬─────────────┘
                              ▼
                         Verified MIR
                              │
                              ▼
                         Optimization
                              │
                              ▼
                           Machine
```

Điểm quan trọng:

**Unsafe không phải một “lỗ thủng” xuyên qua verifier.**

Nó là một **trusted boundary có contract**.

---

# 2. Safe code phải đảm bảo những gì?

Safe Core v0.1 đảm bảo:

```text
No use-after-move
No double-drop
No invalid safe capability
No dangling safe view
No invalid initialization read
No safe data race
No invalid safe mutation alias
No safe access outside valid region
No invalid enum state
```

Đây là những semantic guarantees.

---

# 3. Safe không có nghĩa “không thể crash”

Ví dụ:

```ax
panic("failed");
```

hoặc:

```text
divide by zero
explicit bounds failure
failed Result unwrap
OS failure
```

có thể vẫn xảy ra tùy API/semantics.

Memory safety ≠ total program correctness.

---

# 4. Safe cũng không có nghĩa chống mọi security bug

Axiom không thể tự chứng minh:

```text
authentication logic
business logic
cryptographic algorithm correctness
server authorization policy
```

Compiler chỉ đảm bảo các invariant thuộc language/runtime contract.

---

# 5. Unsafe boundary

Syntax đã có:

```ax
unsafe {
    ...
}
```

và:

```ax
unsafe fn ...
```

Chốt semantics:

> Unsafe chỉ cho phép thực hiện các operation cần trusted assumptions; nó không tắt toàn bộ compiler verification.

---

# 6. Unsafe operation classes

Ví dụ:

```text
raw pointer dereference
pointer arithmetic
integer → pointer conversion
arbitrary address access
volatile hardware access
packed unaligned access
FFI with unchecked contract
inline assembly
manual allocation/deallocation
device-specific memory operation
```

---

# 7. Unsafe không tự động cho phép UB

Axiom không nên có khái niệm:

```text
unsafe => anything is valid
```

Thay vào đó:

```text
unsafe operation
 ↓
required preconditions
 ↓
programmer establishes contract
 ↓
compiler records trusted fact
 ↓
safe verification resumes
```

---

# 8. Trusted facts

Ví dụ conceptual:

```text
raw pointer p
```

programmer biết:

```text
p points to initialized T
p is aligned
region has sufficient size
region is writable
```

Unsafe operation có thể establish:

```text
TrustedCapability {
    provenance
    region
    access
    alignment
    initialization
}
```

Verifier tiếp tục từ đó.

---

# 9. Trusted fact có phạm vi

Không được:

```text
unsafe {
    assume p valid
}

1000 lines later:
*p
```

vẫn tự động coi `p` valid.

Trusted fact có:

```text
scope
provenance
dependencies
invalidation conditions
```

---

# 10. Fact invalidation

Ví dụ:

```text
p → valid view
```

sau:

```text
deallocation
relocation
reallocation
owner drop
```

fact phải bị invalidated.

Đây là phần rất quan trọng để unsafe không phá toàn bộ capability model.

---

# 11. Raw pointer ≠ capability

Giữ nguyên:

```text
*const T
*mut T
```

là machine-level values.

Chúng không tự động có:

```text
ownership
lifetime
safe access capability
```

---

# 12. Integer → pointer

Không được:

```ax
let p: *mut T = address as *mut T;
```

và sau đó compiler tự coi nó là safe pointer.

Đây vẫn là unsafe/system operation.

---

# 13. Pointer provenance

Axiom duy trì:

```text
Address
≠
Pointer Provenance
```

Một integer chứa địa chỉ đúng không đồng nghĩa nó có quyền truy cập allocation đó.

---

# 14. Pointer arithmetic

Pointer arithmetic:

```text
p + n
```

là unsafe/system.

Compiler không phải chịu trách nhiệm chứng minh arbitrary arithmetic đúng.

Nhưng khi programmer muốn quay lại safe access:

```text
raw pointer
 ↓
unsafe validation/contract
 ↓
view<T>
```

thì capability verification tiếp tục.

---

# 15. Manual memory

Axiom Core không khuyến khích:

```text
malloc/free
```

ở source-level bình thường.

Nhưng system layer có thể expose:

```text
allocate
deallocate
resize
map
unmap
```

dưới unsafe/storage contracts.

---

# 16. Double free

Nếu unsafe code vi phạm contract:

```text
deallocate(x)
deallocate(x)
```

đó là programmer responsibility.

Nhưng safe wrappers quanh allocator vẫn có thể đảm bảo:

```text
ownership
exactly-once cleanup
```

---

# 17. Unsafe wrapper principle

Đây là mô hình rất quan trọng:

```text
unsafe implementation
        ↓
safe abstraction
        ↓
ordinary safe application
```

Ví dụ `Vec`, `Box`, `Mutex`, GPU buffers, filesystem APIs... có thể chứa unsafe internals.

Programmer sử dụng abstraction không cần unsafe.

---

# 18. Unsafe surface minimization

Compiler/library nên khuyến khích:

```text
small unsafe core
+
large safe API
```

thay vì:

```text
unsafe everywhere
```

---

# 19. Unsafe auditability

Mỗi unsafe block nên có source provenance:

```text
UnsafeSite {
    FunctionId
    SourceSpan
    Operations
    TrustedFacts
}
```

Compiler có thể:

```text
axc inspect unsafe
```

---

# 20. Safety explanation

Ví dụ:

```text
Unsafe operation:
    dereference p

Required:
    initialized(T)
    aligned(p, T)
    readable(p, sizeof(T))
    valid_provenance(p)

Established by:
    validation at foo.ax:42
```

AI và programmer có thể inspect.

---

# 21. `/// SAFETY:`

Đã từng đề xuất documentation contract.

Chốt hỗ trợ tooling:

```ax
/// SAFETY:
/// p must point to an initialized, aligned T
/// with readable storage for one T.
unsafe fn read_raw(p: *const T) -> T {
    ...
}
```

Compiler **không coi comment là proof**.

Nó chỉ là documentation/audit metadata.

---

# 22. Formal contracts

Không đưa full dependent contracts vào Core v0.1.

Không biến Axiom thành:

```text
requires(...)
ensures(...)
invariant(...)
```

mọi nơi.

Thay vào đó dùng:

```text
compiler-verifiable facts
+
unsafe trusted contracts
```

và có thể mở rộng contract language sau.

---

# 23. Memory safety hardening

Verifier phải bảo đảm:

```text
Initialized
Moved
Dropped
Capability-valid
```

không thể bị optimization phá.

Optimization chỉ hoạt động sau verification.

---

# 24. Bounds safety

Safe indexing:

```ax
a[i]
```

phải có proof:

```text
0 <= i < len(a)
```

hoặc runtime check.

Optimizer có thể eliminate check khi proof tồn tại.

---

# 25. Bounds check failure

Không phải UB.

Ví dụ:

```text
invalid index
→ panic/trap
```

theo profile.

---

# 26. Integer overflow

Axiom giữ semantics đã frozen:

Không có signed-overflow UB kiểu C.

Các operation có semantics xác định:

```text
checked
wrapping
saturating
```

và ordinary arithmetic có profile/operation semantics rõ ràng.

---

# 27. Division

Các trường hợp đặc biệt như:

```text
divide by zero
MIN / -1
```

phải có semantics xác định theo integer model.

Không để compiler tự biến thành undefined behavior.

---

# 28. Uninitialized memory

Không được đọc:

```text
UNINIT
```

trong safe code.

Verifier track:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
```

---

# 29. `MaybeUninit`-like functionality

Có thể tồn tại trong system/low-level library dưới dạng abstraction tương đương `Uninit<T>`.

Nhưng:

```text
Uninit<T>
```

không được phép implicit convert thành `T`.

Phải có proof/operation initialization.

---

# 30. Type validity

Không phải mọi bit pattern đều nhất thiết là valid value của mọi type.

Ví dụ enum:

```text
valid discriminant
```

phải được tôn trọng.

Unsafe `bitcast` phải kiểm tra representation contract.

---

# 31. Bitcast

Giữ distinction:

```text
CAST
```

và:

```text
BITCAST
```

`BITCAST` chỉ hợp lệ nếu:

```text
size
alignment
representation validity
```

được thỏa mãn.

---

# 32. Packed structs

```ax
@repr(packed)
struct Header { ... }
```

có thể tạo unaligned fields.

Việc lấy typed aligned view tới field packed phải là unsafe hoặc compiler phải tạo safe unaligned operation.

---

# 33. Volatile

Volatile là:

```text
observable machine memory access
```

Không được optimizer:

```text
remove
merge
reorder
```

như ordinary memory nếu semantics không cho phép.

---

# 34. Atomic

Atomic không phải volatile.

Atomic có:

```text
atomicity
ordering
synchronization
```

Volatile có:

```text
observable access
```

Hai khái niệm vẫn tách biệt.

---

# 35. Constant-time

Đây là extension rất đáng giá cho Axiom.

Core không nên tuyên bố:

```text
all code is constant-time
```

Nhưng system/security layer nên có:

```text
@constant_time
```

hoặc profile tương đương.

---

# 36. Constant-time semantics

Với secret-dependent code, compiler phải biết các transformation nào bị hạn chế.

Ví dụ:

```text
secret
 ↓
branch
```

có thể leak timing.

Compiler không nên tự động biến mọi code thành constant-time.

---

# 37. Secret data

Đề xuất compiler-known marker:

```text
Secret<T>
```

hoặc:

```text
@secret
```

Nhưng **không nên biến nó thành primitive ownership type**.

Nó là information-flow/security metadata.

---

# 38. Secret propagation

Nếu:

```text
x : Secret<i32>
```

thì derived values có thể được đánh dấu:

```text
Secret
```

theo information-flow analysis.

---

# 39. Secret sink

Các operation như:

```text
branch
memory index
array index
system call
IO
timing-sensitive operation
```

có thể là security-sensitive sinks tùy policy.

Compiler/tooling cảnh báo hoặc reject trong constant-time profile.

---

# 40. Constant-time ≠ optimizer disabled

Không:

```text
@constant_time
→ -O0
```

Mục tiêu:

```text
constant-time constraints
+
aggressive legal optimization
```

---

# 41. Constant-time optimization

Compiler có thể:

```text
select
masking
branchless operations
```

nếu transformation chứng minh giữ constant-time contract.

---

# 42. Timing model limitation

Axiom không thể đảm bảo tuyệt đối:

```text
same wall-clock time on every CPU
```

vì microarchitecture, cache, frequency, interrupts...

Do đó constant-time contract phải được định nghĩa theo **observable control/data dependencies** và target security model.

---

# 43. Cache side channels

Không tuyên bố rằng `@constant_time` tự động chống mọi cache side-channel.

Có thể có các profile mạnh hơn trong tương lai:

```text
constant_control_flow
constant_memory_access
constant_microarchitectural
```

nhưng Core v0.1 chỉ nên đóng băng contract ở mức có thể kiểm chứng.

---

# 44. Zeroization

Axiom đã có security zeroization distinction.

Nếu programmer yêu cầu:

```text
secure_zero(secret)
```

thì compiler không được optimize thành:

```text
nothing
```

chỉ vì value không còn được đọc.

---

# 45. Dead-store elimination và secret

Ordinary:

```text
x = 0;
```

có thể bị DSE.

Nhưng:

```text
secure_zero(x)
```

là observable security operation.

Memory optimizer phải giữ.

---

# 46. Secure drop

Có thể có:

```text
SecretBuffer
```

với Drop thực hiện zeroization.

Drop semantics vẫn:

```text
exactly once
```

nhưng physical zeroing là observable security effect.

---

# 47. Cryptography

Axiom không nên đưa crypto primitives vào language Core.

Thay vào đó:

```text
std::crypto
```

hoặc external audited library.

Compiler chỉ cung cấp:

```text
safe memory
constant-time tooling
secure zeroization
FFI
SIMD
```

---

# 48. FFI security boundary

FFI:

```text
Axiom ↔ foreign code
```

là trust boundary.

Foreign function không được mặc định coi là:

```text
pure
noalias
safe
nonblocking
thread-safe
```

---

# 49. FFI contracts

Có thể khai báo:

```text
extern "C" {
    fn foo(...) -> ...;
}
```

Compiler mặc định conservative.

Nếu cần contract:

```text
@ffi_effect(...)
@noalias(...)
@constant_time(...)
```

thì đây là system/trusted boundary và phải có semantics rõ ràng.

---

# 50. Không cho programmer giả mạo auto traits

Giữ nguyên:

```text
Send
Share
Copy
Drop
FfiSafe
GpuLegal
```

không thể “khai báo cho compiler tin” chỉ bằng unsafe.

Ví dụ không cho:

```text
unsafe impl Send for DangerousType
```

trong Core v0.1 theo kiểu tùy tiện.

Trusted system primitives có cơ chế đặc biệt.

---

# 51. Data race security

Safe code:

```text
no data races
```

được verifier đảm bảo.

Unsafe có thể tạo race nếu contract sai.

Nhưng optimizer vẫn phải bảo toàn semantics của IR đã được chấp nhận.

---

# 52. Race ≠ deadlock

Axiom có thể đảm bảo:

```text
no safe data race
```

nhưng không hứa:

```text
no deadlock
no starvation
no livelock
```

vì đây là higher-level concurrency properties.

---

# 53. Capability security

Axiom capability model ban đầu chủ yếu là memory capabilities.

Mở rộng hợp lý:

```text
system capability
```

ví dụ:

```text
FileCapability
NetworkCapability
ProcessCapability
DeviceCapability
```

nhưng đây là **library/system-level capabilities**, không biến mọi OS permission thành Core type.

---

# 54. Principle of least authority

Library API nên có khả năng nhận capability cụ thể:

```text
fn load(file: FileCapability)
```

thay vì:

```text
global filesystem access
```

Điều này phù hợp với runtime composition.

---

# 55. No hidden global authority

Không tự động có:

```text
global allocator
global filesystem
global RNG
global network
global executor
```

đã frozen trong runtime/std architecture.

Security model củng cố nguyên tắc này.

---

# 56. Sandbox

Comptime đã có sandbox.

System/runtime cũng có thể có sandbox profile:

```text
freestanding
sandboxed
hosted
privileged
kernel
device
```

Compiler không tự cấp quyền runtime.

---

# 57. Privileged code

Kernel/driver code cần:

```text
unsafe
system APIs
target-specific ABI
volatile
interrupt
MMIO
```

nhưng vẫn hưởng lợi từ:

```text
type checking
ownership
initialization
capability tracking
```

ở nơi có thể.

---

# 58. Inline assembly

Inline asm:

```text
unsafe asm(...)
```

là system boundary.

Phải khai báo:

```text
inputs
outputs
clobbers
memory effects
flags
volatile
```

đã thống nhất với LIR.

---

# 59. Compiler barriers

Phân biệt:

```text
compiler barrier
CPU fence
atomic operation
volatile operation
```

Không được thay thế lẫn nhau.

---

# 60. Security-sensitive optimization

Optimizer hierarchy:

```text
Semantic proof
    >
Verified safety fact
    >
Security contract
    >
Optimization fact
    >
Profile
    >
Cost heuristic
```

Nếu constant-time contract xung đột với optimization:

```text
security contract wins
```

trong profile nơi contract được yêu cầu.

---

# 61. Security contract không được thay đổi semantics âm thầm

Ví dụ:

```text
@constant_time
```

nếu compiler không thể đáp ứng contract:

```text
compile error
```

không được:

```text
warning
→ emit insecure code
```

nếu attribute được định nghĩa là hard contract.

---

# 62. Security diagnostics

Ví dụ:

```text
E_UNSAFE_PRECONDITION
E_INVALID_POINTER_PROVENANCE
E_UNINITIALIZED_READ
E_INVALID_BITCAST
E_CONSTANT_TIME_VIOLATION
E_SECRET_BRANCH
E_SECRET_INDEX
E_FORBIDDEN_FFI_ASSUMPTION
```

---

# 63. Security inspection

Đề xuất:

```text
axc inspect unsafe foo
axc inspect safety foo
axc inspect provenance foo
axc inspect secrets foo
axc inspect constant-time foo
axc inspect security foo
```

---

# 64. Security provenance

Compiler có thể trả:

```text
secret x
 ↓
y = hash(x)
 ↓
z = y & mask
 ↓
memory index
 ↓
constant-time violation
```

AI có thể đọc trực tiếp graph này.

---

# 65. Unsafe coverage

Project tooling:

```text
axc audit unsafe
```

cho:

```text
unsafe sites
FFI sites
asm sites
trusted contracts
missing SAFETY documentation
```

---

# 66. Unsafe không phải “black box”

Đây là quyết định rất quan trọng.

Không:

```text
unsafe {
    verifier disabled
}
```

Mà:

```text
unsafe {
    specific unprovable operation
}
```

sau đó verifier tiếp tục kiểm tra mọi thứ có thể kiểm tra.

---

# 67. Safe abstraction boundary

Ví dụ library implementation:

```text
unsafe raw allocation
 ↓
validate
 ↓
construct Box<T>
 ↓
safe API
```

`Box<T>` sau khi được tạo phải tuân thủ toàn bộ ownership/drop/capability rules.

---

# 68. Security + optimization

Compiler được phép:

```text
inline
vectorize
reorder
scalarize
remove allocation
eliminate bounds check
```

miễn là:

```text
semantic safety
+
security contract
+
observable behavior
```

được bảo toàn.

---

# 69. Security + debug

Debug metadata không được vô tình trở thành runtime security leak.

Release:

```text
strip symbols
strip source paths
strip semantic security metadata
```

có thể được cấu hình.

---

# 70. Security + crash

Crash/panic diagnostics trong production có thể chọn:

```text
full
minimal
redacted
```

để tránh leak:

```text
secret values
memory contents
paths
internal symbols
```

---

# 71. Security + logging

Không tự động stringify mọi value `Secret<T>`.

Ví dụ:

```text
Secret<T>
```

khi debug/log:

```text
<redacted>
```

nếu policy yêu cầu.

---

# 72. Security policy profiles

Đề xuất:

```text
normal
hardened
constant-time
freestanding
kernel
sandbox
```

Nhưng profile chỉ thay đổi **security requirements/tooling**, không thay đổi Core type semantics.

---

# 73. Không biến Axiom thành ngôn ngữ “chỉ safe”

Axiom vẫn phải cho phép:

```text
OS kernel
driver
embedded
allocator
runtime
compiler
database engine
game engine
GPU runtime
```

nên unsafe phải đủ mạnh để tiếp cận machine-level.

Mục tiêu là:

```text
safe by default
low-level when explicitly required
```

---

# 74. Không biến Axiom thành Rust clone

Đây là điểm cần khóa.

Axiom **không** sao chép:

```text
'a
&'a T
&'a mut T
borrow syntax
lifetime annotations
```

Ownership/capability/lifetime vẫn là **compiler semantic model**.

Programmer chủ yếu thấy:

```text
T
view<T>
mut_view<T>
Box<T>
Rc<T>
Arc<T>
*const T
*mut T
unsafe
```

---

# 75. Không biến compiler thành GC

Security model không được dẫn tới:

```text
runtime tracing
object headers
write barriers
GC pauses
```

Safe memory safety của Axiom vẫn dựa trên:

```text
ownership
capability
initialization
drop
compiler analysis
```

---

# 76. Security TCB

Trusted Computing Base cần giữ nhỏ:

```text
Language Specification
+
Compiler Frontend
+
Verifier
+
Backend correctness boundary
+
Trusted system/FFI contracts
```

Optimizer không phải authority.

---

# 77. Defense in depth

Axiom có nhiều lớp:

```text
Type System
     ↓
Ownership
     ↓
Capability
     ↓
Initialization
     ↓
Drop
     ↓
Concurrency
     ↓
Unsafe Contract
     ↓
Verifier
     ↓
Optimizer Legality
     ↓
ABI
     ↓
Backend
```

Một optimization pass không được bỏ qua các lớp trên.

---

# 78. Formal verification tương lai

Architecture phải mở đường cho:

```text
formal proof
SMT-assisted verification
symbolic execution
model checking
```

nhưng không bắt buộc Core v0.1.

---

# 79. Compiler-assisted contracts tương lai

Sau này có thể:

```text
requires x < n
ensures result >= 0
```

và compiler có thể prove bằng range analysis/SMT.

Nhưng hiện tại:

```text
Core v0.1
```

không phụ thuộc SMT.

---

# 80. Invariants

Đóng băng:

### `ASEC-20`
Safe Axiom code has compiler-enforced memory-safety invariants.

### `ASEC-21`
Safe code cannot perform invalid ownership transitions.

### `ASEC-22`
Safe code cannot read uninitialized values.

### `ASEC-23`
Safe code cannot create dangling capabilities.

### `ASEC-24`
Safe code cannot perform conflicting mutable capabilities.

### `ASEC-25`
Safe code cannot contain compiler-defined data races.

### `ASEC-26`
Unsafe operations form explicit trusted boundaries.

### `ASEC-27`
Unsafe does not disable all compiler verification.

### `ASEC-28`
Unsafe operations have explicit semantic preconditions.

### `ASEC-29`
Trusted facts have bounded provenance and validity.

### `ASEC-30`
Trusted facts are invalidated when their prerequisites cease to hold.

### `ASEC-31`
Raw pointers do not automatically become safe capabilities.

### `ASEC-32`
Integer addresses do not establish pointer provenance.

### `ASEC-33`
Unsafe pointer arithmetic does not create ownership.

### `ASEC-34`
Unsafe code cannot fabricate compiler-derived semantic traits arbitrarily.

### `ASEC-35`
Safe abstractions may encapsulate unsafe implementation.

### `ASEC-36`
Unsafe surface should remain auditable.

### `ASEC-37`
Unsafe sites retain source provenance.

### `ASEC-38`
Safety documentation does not itself constitute compiler proof.

### `ASEC-39`
Memory safety is distinct from total program correctness.

### `ASEC-40`
Bounds failures are not C-style undefined behavior.

### `ASEC-41`
Integer overflow semantics remain defined.

### `ASEC-42`
Invalid bitcasts are rejected unless representation validity is established.

### `ASEC-43`
Packed representation does not silently imply aligned access.

### `ASEC-44`
Volatile and atomic semantics remain distinct.

### `ASEC-45`
Compiler barriers and CPU fences remain distinct.

### `ASEC-46`
Secure zeroization is observable when explicitly requested.

### `ASEC-47`
Dead-store elimination cannot remove required secure zeroization.

### `ASEC-48`
Constant-time is an explicit security contract, not a universal language guarantee.

### `ASEC-49`
Constant-time contracts constrain optimization only where required.

### `ASEC-50`
A constant-time contract failure is a compiler diagnostic when the contract is mandatory.

### `ASEC-51`
Secret data may participate in compiler security analysis.

### `ASEC-52`
Secret metadata does not automatically imply runtime reflection.

### `ASEC-53`
Constant-time does not claim to eliminate every microarchitectural side channel.

### `ASEC-54`
FFI is a trust boundary.

### `ASEC-55`
Foreign functions are conservative unless explicit verified contracts exist.

### `ASEC-56`
Unsafe cannot silently strengthen FFI guarantees.

### `ASEC-57`
System capabilities are explicit rather than hidden global authorities.

### `ASEC-58`
Sandbox and privilege profiles are distinct from Core type semantics.

### `ASEC-59`
Privileged/kernel code may use unsafe machine-level facilities.

### `ASEC-60`
Inline assembly is an explicit unsafe/system boundary.

### `ASEC-61`
Inline assembly must declare relevant inputs, outputs, clobbers and memory effects.

### `ASEC-62`
Security contracts participate in optimization legality.

### `ASEC-63`
Optimization cannot override mandatory security contracts.

### `ASEC-64`
Security metadata does not become mandatory production runtime state.

### `ASEC-65`
Debugging must not automatically expose secret values.

### `ASEC-66`
Production diagnostics may redact security-sensitive information.

### `ASEC-67`
Security tooling remains optional for ordinary production execution.

### `ASEC-68`
The security model does not require tracing GC.

### `ASEC-69`
The security model does not require programmer-written lifetimes.

### `ASEC-70`
The security model does not require borrow-checker syntax.

### `ASEC-71`
Safe abstraction remains the default application programming model.

### `ASEC-72`
Low-level system programming remains expressible through explicit unsafe facilities.

### `ASEC-73`
The verifier remains the correctness boundary before optimization.

### `ASEC-74`
Optimization cannot create a safety proof retroactively.

### `ASEC-75`
Security analysis must remain deterministic and inspectable.

### `ASEC-76`
Security diagnostics have stable machine-readable identities.

### `ASEC-77`
AI tooling may consume safety/security provenance but cannot define security semantics.

### `ASEC-78`
Future formal verification mechanisms must integrate without weakening Core semantics.

### `ASEC-79`
The trusted computing base should remain as small as practical.

### `ASEC-80`
Axiom security is defense-in-depth rather than reliance on a single mechanism.

---

# Một quyết định rất quan trọng đã được khóa

Axiom hiện không đi theo hai cực:

```text
C/C++
→ programmer tự chịu gần như tất cả
```

hay:

```text
Rust-like
→ programmer phải biểu diễn ownership/lifetime rất nhiều trên source
```

mà đi theo hướng thứ ba:

```text
                    AXIOM

          Programmer-facing model
        ───────────────────────────
        Value
        view<T>
        mut_view<T>
        Box<T>
        Rc<T>
        Arc<T>
        unsafe
        raw pointer khi cần

                    ↓

          Compiler semantic model
        ───────────────────────────
        Ownership
        Capability
        Region
        Provenance
        Lifetime
        Initialization
        Drop
        Alias
        Escape
        Send / Share
        Effect
        Security facts

                    ↓

              Verified MIR
```

**Đây chính là nơi Axiom có thể khác biệt đáng kể:** compiler làm phần công việc phức tạp, thay vì bắt programmer viết toàn bộ bằng tay.

---

# BOOTSTRAP-162 — Diagnostics, Error Recovery, Compiler UX & AI-Native Compiler Interface

Bước kế tiếp nên khóa **compiler UX**.

Với kiến trúc hiện tại, Axiom không nên chỉ có:

```text
error: expected ';'
```

mà compiler phải có một **diagnostic engine có cấu trúc**, đủ mạnh cho cả:

- programmer,
- IDE,
- debugger,
- build system,
- CI,
- AI agent.

Mục tiêu là một lỗi có thể được biểu diễn đồng thời thành:

```text
Human explanation
        +
Source spans
        +
Semantic facts
        +
Suggested fixes
        +
Machine-readable error code
        +
Compiler/IR provenance
        +
AI-readable structured representation
```

và đặc biệt phải giải quyết một vấn đề rất quan trọng của Axiom:

> **Compiler càng tự động nhiều — ownership, lifetime, alias, specialization, vectorization, layout, async lowering, optimization — thì compiler càng phải giải thích được “tại sao” một cách có cấu trúc, thay vì chỉ nói “không hợp lệ”.**