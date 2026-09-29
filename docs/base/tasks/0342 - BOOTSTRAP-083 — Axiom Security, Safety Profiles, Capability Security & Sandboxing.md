# BOOTSTRAP-083 — Axiom Security, Safety Profiles, Capability Security & Sandboxing

**Trạng thái: FROZEN**

Phần này cần làm rõ một điểm rất quan trọng:

> **Memory safety không đồng nghĩa với security.**  
> Một chương trình có thể không có use-after-free nhưng vẫn có thể đọc file bí mật, mở socket, gọi syscall nguy hiểm hoặc làm rò rỉ dữ liệu.

Vì vậy Axiom sẽ tách:

```text
Memory Safety
    ↓
Resource Safety
    ↓
Concurrency Safety
    ↓
Execution Safety
    ↓
Capability Security
    ↓
Platform Security
```

---

# 1. Hai tầng an toàn

Axiom phân biệt:

```text
Safety
= chương trình không vi phạm semantic invariants

Security
= chương trình chỉ có quyền thực hiện những hành động được cấp
```

Ví dụ:

```ax
let x = buffer[i]
```

Memory-safe không có nghĩa chương trình được phép đọc `buffer`.

Quyền truy cập file/socket/process là vấn đề security.

---

# 2. Safe không phải sandbox

Một chương trình Axiom safe:

```text
không use-after-free
không double-drop
không data race
không dangling view
```

nhưng vẫn có thể:

```text
open("/secret")
connect(...)
spawn(...)
```

nếu các API đó được chương trình sử dụng và môi trường cho phép.

---

# 3. Capability-based security

Đối với những môi trường cần sandbox, Axiom sử dụng mô hình:

```text
Capability = quyền + đối tượng/quyền truy cập cụ thể
```

Ví dụ conceptual:

```text
FileCapability
NetworkCapability
ProcessCapability
DeviceCapability
```

Không cấp capability → code không thể thực hiện operation tương ứng trong sandbox.

---

# 4. Không dùng global ambient authority làm nền tảng

Không nên để API kiểu:

```ax
File.open("/etc/foo")
```

tự động có quyền chỉ vì process đang chạy với user phù hợp.

Trong security-sensitive profile có thể yêu cầu:

```ax
File.open(fs_cap, path)
```

Quyền được truyền vào như dữ liệu/capability.

---

# 5. Nhưng không ép capability parameter vào mọi chương trình

Đây là điểm để tránh over-design.

Hosted application thông thường vẫn có thể dùng:

```ax
File.open(path)
```

nếu build/runtime profile cho phép ambient OS authority.

Capability-oriented API là **security profile/library model**, không phải bắt buộc toàn bộ Core syntax.

---

# 6. Security profile

Axiom hỗ trợ profile ở build/execution level.

Conceptual:

```text
standard
freestanding
sandboxed
restricted
deterministic
kernel/system
```

Profile không được thay đổi semantics của language Core.

Nó giới hạn những capability/platform operations được phép sử dụng.

---

# 7. Compiler không phải security boundary tuyệt đối

Compiler có thể kiểm tra:

```text
memory safety
ownership
capability
FFI contracts
unsafe obligations
```

nhưng không thể tự bảo đảm:

```text
OS kernel security
CPU security
malicious hardware
filesystem ACL
external process behavior
```

Platform vẫn là security authority cuối cùng.

---

# 8. `unsafe` không phá toàn bộ verifier

Đã frozen:

```text
unsafe
```

cho phép programmer thực hiện machine-level operations.

Nhưng:

```text
unsafe ≠ disable compiler
```

Ví dụ:

```ax
unsafe {
    let p = ...
}
```

sau boundary, compiler vẫn theo dõi:

```text
ownership
capability
lifetime
resource
Send/Share
```

khi các facts có thể được xác lập.

---

# 9. Unsafe establishes trusted facts

Mô hình:

```text
Safe
  ↓
Unsafe operation
  ↓
Trusted precondition established
  ↓
Safe verification resumes
```

Ví dụ:

```text
raw pointer
    ↓ unsafe validation
valid region
    ↓
mut_view<T>
    ↓
ordinary safe code
```

---

# 10. Không cho unsafe tự động tạo mọi quyền

Một unsafe block không có nghĩa:

```text
"compiler tin tất cả mọi thứ từ đây trở đi"
```

Nó chỉ cho phép các operation thuộc unsafe set.

Các invariant khác vẫn tồn tại.

---

# 11. Trusted code

Một số compiler/runtime/platform components có thể cần:

```text
trusted implementation
```

Ví dụ:

```text
allocator
scheduler
OS wrapper
atomic primitive
FFI adapter
```

Đây là trusted computing base của từng subsystem.

Không biến toàn bộ application thành trusted code.

---

# 12. Narrow unsafe

Khuyến nghị:

```ax
fn safe_api(...) {
    unsafe {
        // very small machine-level operation
    }

    // safe implementation
}
```

thay vì:

```ax
unsafe fn giant_application(...)
```

Axiom tooling nên có thể thống kê unsafe surface.

---

# 13. Unsafe audit metadata

Tooling có thể báo:

```text
unsafe blocks: 7
unsafe functions: 2
FFI boundaries: 4
raw pointer operations: 11
trusted contracts: 5
```

AI agent cũng có thể truy vấn thông tin này.

---

# 14. `/// SAFETY:` documentation

Axiom đã quyết định không có full dependent contract system trong Core v1.

Nhưng unsafe APIs nên hỗ trợ convention:

```ax
/// SAFETY:
/// ptr must reference at least `len` initialized T values.
/// memory must remain valid for the returned view.
unsafe fn from_raw_parts(...)
```

Compiler/tooling có thể parse và expose metadata.

---

# 15. Không biến documentation thành proof

`SAFETY:` comment không phải compiler proof.

Nó là:

```text
human/tooling contract
```

Compiler chỉ có thể kiểm tra những phần machine-checkable.

---

# 16. Sandbox

Sandbox là execution environment hạn chế:

```text
filesystem
network
process creation
environment
clock
randomness
device access
syscalls
```

Axiom program không tự thoát sandbox chỉ bằng:

```text
unsafe
```

---

# 17. Unsafe không bypass OS sandbox

Nếu OS/container/WASM runtime chặn:

```text
open
socket
exec
```

thì:

```text
unsafe
```

không được coi là cơ chế bypass.

Axiom compiler không cấp thêm privilege.

---

# 18. WASM

WASM là một môi trường rất phù hợp với model này.

Axiom WASM program có thể chỉ nhận:

```text
imports
```

mà host cấp.

Ví dụ:

```text
console.log
filesystem.read
network.request
```

Không import → không có capability tương ứng.

---

# 19. Host imports là capabilities

Trong WASM target:

```text
Host
  │
  ├── console
  ├── filesystem
  ├── network
  └── clock
       ↓
    Axiom module
```

Axiom không giả định tất cả imports tồn tại.

---

# 20. Comptime sandbox

Đã frozen trong Comptime model:

```text
ReadSource
ReadMetadata
```

là capability mặc định.

Các quyền mạnh hơn:

```text
ReadFilesystem
WriteGenerated
ExecuteTool
Environment
Network
Time
Random
```

phải được cấp rõ ràng.

---

# 21. Comptime không được bypass security

```text
comptime
```

không có quyền đặc biệt để:

```text
đọc secrets
ghi arbitrary filesystem
chạy process
```

nếu build environment không cấp capability.

---

# 22. Build security

Build script/comptime có thể tạo supply-chain risk.

Do đó build graph phải biết:

```text
source
dependency
comptime code
external input
tool execution
```

và cache identity phải phụ thuộc các external inputs liên quan.

---

# 23. Dependency trust

Package dependency không được tự động trở thành:

```text
trusted compiler code
```

Một package bình thường chỉ có quyền của chương trình sử dụng nó.

Compiler plugins/trusted backend components là category riêng.

---

# 24. Native application privilege

Native Axiom executable cuối cùng vẫn chịu:

```text
OS permission
user identity
sandbox/container
MAC policy
code-signing policy
```

Axiom không tạo một security layer giả lập thay thế OS.

---

# 25. System calls

Syscall API thuộc system layer.

Ví dụ:

```text
Linux
Windows
macOS
iOS
Android
```

có thể expose low-level interfaces.

Nhưng syscall access không mặc định là safe high-level operation.

---

# 26. Privileged operations

Các operation như:

```text
raw device access
kernel interface
interrupt setup
page table manipulation
process injection
```

thuộc system/unsafe boundary.

Không nằm trong ordinary application API.

---

# 27. Handles

OS handle:

```text
Fd
WinHandle
MachPort
DeviceHandle
```

là machine-level values.

Handle không tự động chứng minh:

```text
valid
owned
alive
authorized
```

---

# 28. Typed handles

Axiom nên ưu tiên:

```text
Handle<File>
Handle<Socket>
Handle<Device>
```

hoặc concrete wrappers.

Điều này ngăn việc vô tình truyền:

```text
SocketHandle
```

vào API yêu cầu:

```text
FileHandle
```

---

# 29. Handle generation

Logical handles có thể sử dụng:

```text
index + generation
```

để phát hiện stale references.

Đã phù hợp với:

```text
AMEM-39
```

nhưng đây là library/runtime strategy, không phải bắt buộc mọi handle.

---

# 30. Secrets

Axiom nên có library/system abstraction cho dữ liệu nhạy cảm:

```text
Secret<T>
SecureBuffer
```

Không đưa `Secret<T>` thành primitive Core.

---

# 31. Secret memory zeroization

Khi semantic contract yêu cầu:

```text
Secret<T>
```

có thể đảm bảo explicit zeroization khi Drop.

Nhưng compiler không được optimize thao tác zeroization thành:

```text
nothing
```

nếu contract yêu cầu observable secure erase.

---

# 32. Zeroization là security contract

Thông thường:

```ax
memory[0..n] = 0
```

có thể bị optimizer loại nếu không observable.

Đối với:

```text
SecureBuffer
```

compiler phải nhận biết secure-zero effect.

---

# 33. Secure memory không phải memory-safe primitive

`SecureBuffer` vẫn phải tuân:

```text
ownership
capability
Drop
bounds
concurrency
```

Zeroization không thay thế memory safety.

---

# 34. Constant-time cryptography

Axiom không thể hứa:

```text
mọi code đều constant-time
```

nhưng system/crypto library có thể cung cấp explicit contract:

```text
@constant_time
```

nếu sau này đủ semantic definition.

---

# 35. Không đưa `@constant_time` vào Core v1 nếu chưa có verifier

Quan trọng:

Không nên có attribute chỉ mang tính trang trí:

```ax
@constant_time
fn ...
```

mà compiler không thể kiểm tra.

Có thể giữ reserved/system namespace trước.

---

# 36. Side-channel

Memory safety không ngăn:

```text
timing leak
cache leak
branch predictor leak
power analysis
spectre-like effects
```

Đây là security concern cấp compiler/platform/hardware.

Axiom chỉ nên cung cấp các primitive cần thiết để crypto/system libraries xây dựng mitigation.

---

# 37. Speculative execution

Compiler optimization không được phá semantic security contracts mà compiler đã nhận biết.

Nhưng Axiom Core không hứa một chương trình bình thường tự động chống mọi speculative side-channel.

---

# 38. Memory barriers

Đã có distinction:

```text
compiler barrier
CPU fence
atomic ordering
volatile
```

Không gộp chúng thành một “security barrier”.

---

# 39. Information flow

Axiom Core v1 không nên có full taint/dependent information-flow type system.

Ví dụ:

```text
Secret<T>
Public<T>
```

có thể tồn tại ở library/tooling level sau này.

---

# 40. Không over-design security type system

Một hệ:

```text
Secret<T>
Public<T>
Trusted<T>
Untrusted<T>
Encrypted<T>
Decrypted<T>
...
```

nếu đưa toàn bộ vào Core sẽ làm type system phức tạp mạnh.

Axiom chỉ giữ những security properties thực sự cần semantic enforcement.

---

# 41. Untrusted input

Safe memory semantics đảm bảo:

```text
malformed input
```

không tự tạo:

```text
buffer overflow
dangling pointer
invalid memory access
```

Nhưng application vẫn phải validate business/data semantics.

---

# 42. Parser/security

Các thư viện parser nên hướng tới:

```text
Result<T, ParseError>
```

thay vì panic trên dữ liệu không tin cậy.

---

# 43. Resource exhaustion

Memory safety không ngăn:

```text
allocate 1 TB
spawn 1 million tasks
open millions of files
```

Do đó sandbox/security profile có thể giới hạn:

```text
memory
CPU
file descriptors
threads
tasks
GPU resources
```

Nhưng đây là runtime/OS policy.

---

# 44. Capability quotas

Một capability có thể mang quota:

```text
FileSystemCapability
    max_bytes
    allowed_paths

NetworkCapability
    allowed_hosts
    allowed_ports
```

Đây là library/runtime/platform abstraction.

---

# 45. Path security

Filesystem capability không nên mặc định chỉ kiểm tra string prefix.

Ví dụ:

```text
"/safe/"
```

không đủ để chứng minh path resolution an toàn trong mọi filesystem semantics.

Security library/system layer phải xử lý:

```text
symlink
mount
race
canonicalization
OS-specific path semantics
```

---

# 46. Network security

`NetworkCapability` có thể giới hạn:

```text
protocol
address
port
direction
```

nhưng TLS/certificate verification vẫn là library concern.

---

# 47. Process capability

Process creation nên có explicit capability/profile.

Không nên coi:

```text
spawn(...)
```

là một primitive vô điều kiện trong sandbox.

---

# 48. Environment variables

Environment là external authority.

Comptime đã coi:

```text
Environment
```

là external capability.

Runtime cũng nên coi environment access là resource/platform operation.

---

# 49. Time

Clock access có security/reproducibility implications.

Do đó:

```text
Time
```

không phải intrinsic constant.

Comptime `Time` đã là explicit capability.

Runtime clock cũng là explicit platform API.

---

# 50. Randomness

Phân biệt:

```text
deterministic PRNG
cryptographic RNG
hardware RNG
```

Không gọi tất cả là `random()`.

Crypto randomness phải có stronger API contract.

---

# 51. Secure randomness

System/crypto layer có thể cung cấp:

```text
SecureRandom
```

với OS/hardware-backed source.

Không đưa crypto RNG thành Core primitive.

---

# 52. Thread security

`Send` và `Share` là safety properties.

Chúng không phải security authorization.

Ví dụ một object có thể `Send` nhưng vẫn chứa secret mà programmer không muốn truyền sang domain khác.

Security policy nằm ở higher layer.

---

# 53. GPU security

Device memory access cũng cần:

```text
ownership
capability
device identity
resource lifetime
```

GPU kernel không được mặc định có quyền truy cập mọi host/device memory.

---

# 54. Device capability

GPU/device APIs nên yêu cầu explicit:

```text
Device
DeviceBuffer
DeviceView
```

để resource identity rõ ràng.

---

# 55. FFI là trust boundary

FFI:

```text
Axiom
 ↓
Foreign code
```

không được giả định foreign code tuân Axiom invariants.

Foreign function có thể:

```text
mutate memory
retain pointer
free memory
spawn thread
call callback
```

nếu contract cho phép.

---

# 56. FFI wrapper

Preferred architecture:

```text
Unsafe FFI
    ↓
small validation wrapper
    ↓
safe Axiom API
```

Không để toàn bộ application gọi raw FFI.

---

# 57. Foreign ownership

Đã frozen:

```text
Borrowed
OwnedByAxiom
OwnedByForeign
Shared
HandleOnly
```

Không đoán ownership.

---

# 58. Callback security

Foreign callback phải có contract về:

```text
calling convention
thread/domain
lifetime
reentrancy
ownership
exception behavior
```

Không coi function pointer đơn thuần là đủ.

---

# 59. Reentrancy

Security/correctness-sensitive APIs cần có thể chỉ rõ:

```text
reentrant
non-reentrant
callback may occur during call
```

Không suy luận callback behavior chỉ từ function type.

---

# 60. Panic/exception boundary

Axiom panic không tự xuyên qua FFI.

Foreign exception cũng không tự xuyên vào Axiom panic mechanism.

Wrapper phải chuyển đổi explicit.

---

# 61. ABI security

ABI contract phải xác định:

```text
layout
calling convention
ownership
alignment
lifetime
error behavior
unwind behavior
```

Sai ABI là correctness/security bug, không phải “compiler tự sửa”.

---

# 62. Dynamic libraries

Dynamic symbol lookup:

```text
Symbol<T>
```

không chứng minh symbol thực sự có type T.

Do đó lookup từ foreign library là unsafe/trusted boundary.

---

# 63. Code loading

Dynamic loading nên thuộc system layer.

Security profile có thể cấm:

```text
dlopen
LoadLibrary
dynamic code generation
JIT
```

nếu environment yêu cầu.

---

# 64. JIT

Axiom compiler/runtime không mặc định chứa JIT.

Nếu ứng dụng cần JIT:

```text
JIT runtime
```

là explicit dependency/capability.

---

# 65. Executable memory

Memory có quyền:

```text
R
W
X
```

khác nhau.

System allocator/memory API phải giữ permission contract.

Không mặc định biến mọi allocated memory thành executable.

---

# 66. W^X

Platform/system layer có thể hỗ trợ policy:

```text
write xor execute
```

nhưng đây không phải semantic invariant của Core.

---

# 67. Memory protection

Low-level API có thể expose:

```text
VirtualMemory
Protect
Map
Unmap
```

với unsafe/system contracts.

Live capabilities vẫn phải được xử lý đúng.

---

# 68. No dangling capability even under security APIs

Ví dụ:

```text
unmap(memory)
```

không được phép khi:

```text
view
```

vẫn live.

Security-sensitive API không được bypass ordinary capability verification.

---

# 69. Privilege separation

Axiom application architecture nên hỗ trợ:

```text
main process
    ↓
restricted worker
    ↓
minimal capabilities
```

nhưng process isolation là OS/runtime/library feature.

---

# 70. Capability passing

Capabilities có thể được truyền:

```text
function
thread
task
channel
process boundary
```

theo ownership semantics.

Nếu capability có thể cross-domain:

```text
Send
```

phải được thỏa.

---

# 71. Capability revocation

Không phải mọi capability đều có thể revoke.

Những resource cần revocation nên dùng handle indirection:

```text
Capability
   ↓
Handle
   ↓
Authority table
```

để có thể invalidate.

Raw `view<T>` không phải revocable security capability.

---

# 72. Distinguish memory capability from authority capability

Axiom có:

```text
view<T>
mut_view<T>
```

là **memory access capability**.

Nhưng:

```text
FileCapability
NetworkCapability
DeviceCapability
```

là **authority/resource capabilities**.

Không gộp hai khái niệm thành một generic security primitive.

---

# 73. Capability graph

Compiler/runtime có thể conceptualize:

```text
Owner
 ├── memory capability
 ├── resource capability
 └── execution capability
```

nhưng implementation có thể erase abstraction khi không cần.

---

# 74. Security capability không nhất thiết runtime object

Một capability compile-time/build-time có thể chỉ là:

```text
permission fact
```

và biến mất khi executable được tạo.

---

# 75. No mandatory capability runtime

Native program không sử dụng sandbox:

```text
không cần capability runtime
```

Security machinery chỉ link khi cần.

---

# 76. Security metadata

Compiler artifact `.axmeta` có thể chứa:

```text
unsafe surface
FFI boundaries
required runtime components
required platform capabilities
target features
security-relevant contracts
```

Tooling có thể inspect trước khi chạy.

---

# 77. Build-time capability declaration

Package/application có thể khai báo:

```text
requires:
    filesystem
    network
    process
```

Build tool có thể dùng để audit.

Không biến declaration này thành security guarantee nếu OS/runtime không enforce.

---

# 78. Least privilege

Security tooling có thể cảnh báo:

```text
declared filesystem capability
but package only accesses X
```

và hỗ trợ giảm quyền.

Đây là tooling optimization/security analysis, không phải Core semantic requirement.

---

# 79. Auditability

Axiom nên làm cho security boundary dễ tìm:

```text
unsafe
extern
@syscall
@interrupt
@kernel
dynamic loading
raw pointer
resource capability
```

Không giấu chúng sau magic syntax.

---

# 80. Security-sensitive compiler optimizations

Optimizer phải bảo toàn:

```text
volatile
atomic
secure-zero
FFI effects
IO effects
synchronization
```

Không được áp dụng ordinary DCE/CSE nếu làm mất semantic security contract.

---

# 81. Constant-time optimization boundary

Nếu sau này Axiom có verified constant-time abstraction, compiler phải coi timing-sensitive operations là semantic contract.

Nếu chưa có verifier:

```text
compiler không tuyên bố constant-time
```

chỉ vì source code nhìn có vẻ branchless.

---

# 82. Cryptography should live above Core

Core cung cấp:

```text
integer
bit operations
SIMD
memory
atomic
unsafe
```

Crypto library cung cấp:

```text
AES
SHA
ChaCha
ECC
RSA
TLS
```

System layer cung cấp:

```text
OS secure RNG
hardware crypto
TPM/secure enclave
```

---

# 83. Secure enclave / TPM

Các resource như:

```text
TPM
Secure Enclave
Android Keystore
Windows CNG
```

là platform APIs.

Không trở thành language primitive.

---

# 84. Mobile security

iOS/Android target có security model riêng.

Axiom phải tôn trọng:

```text
sandbox
entitlements
permissions
code signing
platform lifecycle
```

Không cố abstract away những security differences làm mất semantics.

---

# 85. Kernel / embedded

Freestanding/kernel Axiom có thể không có:

```text
OS
filesystem
network
runtime
allocator
```

nhưng vẫn giữ:

```text
ownership
capability
memory safety
```

trừ những phần explicitly unsafe/system.

---

# 86. Trusted kernel code

Kernel có thể cần:

```text
unsafe
volatile
raw pointers
MMIO
interrupts
page tables
```

Axiom không cấm.

Mục tiêu là:

> **unsafe cho phép xây dựng hệ thống thấp tầng, nhưng phần còn lại của code vẫn hưởng safe verification.**

---

# 87. Safety profile không làm language fork

Không tạo:

```text
Axiom Safe
Axiom Kernel
Axiom Embedded
Axiom Sandbox
Axiom GPU
```

thành những ngôn ngữ khác nhau.

Chúng là:

```text
Axiom Core
+
target/profile policies
```

---

# 88. Security profile inheritance

Một module/package có thể yêu cầu capability mạnh hơn dependency.

Build system phải phát hiện requirement graph.

Ví dụ:

```text
App
 └── package A
      └── package B
           └── requires network
```

→ application có thể cần network capability.

---

# 89. Dependency cannot silently escalate authority

Package import không nên tự động cấp:

```text
filesystem
network
process
```

cho toàn bộ program.

Build/runtime environment quyết định authority.

---

# 90. Comptime dependency isolation

Một package có comptime code đọc filesystem phải khai báo external capability.

Nếu không:

```text
build rejected
```

thay vì silently granting access.

---

# 91. Reproducible builds

Security và reproducibility giao nhau.

Nếu comptime đọc:

```text
Time
Random
Environment
Network
```

thì kết quả có thể thay đổi.

Dependency graph phải record input.

---

# 92. Hermetic build

Build profile có thể yêu cầu:

```text
no network
no arbitrary filesystem
no environment
no time
```

ngoài những inputs explicitly provided.

Đây là profile rất quan trọng cho CI/supply-chain security.

---

# 93. Deterministic sandbox

Trong deterministic profile:

```text
time
random
environment
network
```

bị hạn chế hoặc được virtualize.

Compiler cache không được sử dụng stale result nếu external input thay đổi.

---

# 94. Compiler itself

`axiomc` phải phân biệt:

```text
compiler trust
source trust
package trust
build tool trust
runtime trust
platform trust
```

Không nên coi source code là trusted chỉ vì compiler đang compile nó.

---

# 95. Malicious source

Source có thể:

```text
unsafe
comptime
FFI
```

nhưng compiler phải không để source:

```text
thoát sandbox của compiler
ghi arbitrary compiler memory
thực thi arbitrary host commands
```

trừ capability được cấp.

---

# 96. Compiler security boundary

Đặc biệt:

```text
comptime execution
```

chạy trong compiler environment nhưng phải sandbox.

Compiler crash:

```text
ICE
```

khác với:

```text
program requested privileged operation
```

---

# 97. Security diagnostics

Compiler/tooling nên đưa diagnostics machine-readable:

```text
SEC001
required capability: filesystem.read
profile: sandboxed
operation: File.open
status: denied
```

AI agent có thể hiểu trực tiếp.

---

# 98. Security explain mode

Ví dụ:

```text
axiom explain security
```

có thể trả:

```text
Unsafe boundaries: 4
FFI boundaries: 2
External capabilities: filesystem.read, network.connect
Dynamic code loading: none
Required runtime: allocator, async
```

---

# 99. Design principle

Toàn bộ security model quy về:

```text
Memory safety
    → compiler verification

Resource authority
    → explicit capability

Machine escape
    → unsafe

Platform privilege
    → OS/runtime

Build authority
    → comptime/build capabilities

Foreign trust
    → explicit FFI contract
```

Không một cơ chế nào cố làm tất cả.

---

# 100. Frozen Invariants — `ASEC-20..100`

**ASEC-20** — Memory safety and security are distinct properties.

**ASEC-21** — Safe code preserves Axiom semantic safety invariants.

**ASEC-22** — Safe code does not imply absence of security vulnerabilities.

**ASEC-23** — Security authority is distinct from memory capability.

**ASEC-24** — Resource authority may be represented through explicit capabilities.

**ASEC-25** — Security capabilities are not equivalent to `view<T>` or `mut_view<T>`.

**ASEC-26** — `view<T>` and `mut_view<T>` remain memory-access capabilities.

**ASEC-27** — File/network/device/process authority may require explicit capability APIs.

**ASEC-28** — Ordinary hosted APIs need not expose capability parameters when ambient OS authority is intentionally used.

**ASEC-29** — Sandboxed profiles may require explicit authority capabilities.

**ASEC-30** — Unsafe does not disable the entire compiler verifier.

**ASEC-31** — Unsafe operations may establish trusted semantic preconditions.

**ASEC-32** — Safe verification resumes after a valid unsafe boundary.

**ASEC-33** — Unsafe code cannot arbitrarily manufacture compiler security facts.

**ASEC-34** — Unsafe surface should remain auditable.

**ASEC-35** — Unsafe is not an optimization mode.

**ASEC-36** — Unsafe is required only where machine-level invariants cannot otherwise be proven.

**ASEC-37** — Unsafe APIs should document safety preconditions.

**ASEC-38** — Safety documentation is not equivalent to compiler proof.

**ASEC-39** — Sandboxing is an execution/environment property.

**ASEC-40** — Unsafe does not inherently bypass OS or host sandboxing.

**ASEC-41** — Axiom does not grant OS privileges merely through language syntax.

**ASEC-42** — WASM host imports represent explicit host authority boundaries.

**ASEC-43** — Comptime external effects require explicit capabilities.

**ASEC-44** — Comptime cannot bypass its sandbox through unsafe.

**ASEC-45** — Build-time capabilities are distinct from runtime capabilities.

**ASEC-46** — Package dependencies do not silently escalate application authority.

**ASEC-47** — External build inputs participate in dependency and cache identity.

**ASEC-48** — Hermetic builds may restrict external filesystem/network/environment/time/random access.

**ASEC-49** — Reproducible builds may restrict nondeterministic external capabilities.

**ASEC-50** — OS system calls belong to the system layer.

**ASEC-51** — Privileged system operations are explicit system/unsafe operations.

**ASEC-52** — Raw OS handles do not imply authorization.

**ASEC-53** — Typed handles provide semantic identity but do not automatically establish privilege.

**ASEC-54** — Handle validity and security authority are distinct properties.

**ASEC-55** — Revocable authority may require indirection or runtime-managed handles.

**ASEC-56** — Capability passing follows Axiom ownership and Send semantics where applicable.

**ASEC-57** — Resource capabilities do not implicitly bypass lifetime verification.

**ASEC-58** — FFI is a foreign trust boundary.

**ASEC-59** — Foreign code is not assumed to satisfy Axiom safety invariants.

**ASEC-60** — FFI ownership must be explicit.

**ASEC-61** — FFI callbacks require explicit lifetime, ABI and execution-domain contracts.

**ASEC-62** — Foreign exceptions do not automatically become Axiom panics.

**ASEC-63** — Axiom panics do not automatically cross foreign ABI boundaries.

**ASEC-64** — Dynamic symbol lookup does not prove foreign symbol type correctness.

**ASEC-65** — Dynamic code loading is an explicit system capability.

**ASEC-66** — Executable memory is an explicit system-level concern.

**ASEC-67** — Security-sensitive memory operations preserve capability validity.

**ASEC-68** — Live memory capabilities prevent invalidating storage operations.

**ASEC-69** — Secure memory abstractions remain subject to ordinary ownership and lifetime rules.

**ASEC-70** — Security-sensitive zeroization may constitute an observable semantic contract.

**ASEC-71** — Optimizers must not eliminate required secure-zero operations.

**ASEC-72** — Constant-time behavior is not claimed without an explicit enforceable contract.

**ASEC-73** — Side-channel resistance is not implied by memory safety.

**ASEC-74** — Cryptographic algorithms belong primarily to libraries/system backends.

**ASEC-75** — Secure randomness is distinct from ordinary deterministic randomness.

**ASEC-76** — Resource exhaustion is distinct from memory safety.

**ASEC-77** — Runtime/OS profiles may impose resource quotas.

**ASEC-78** — Security profiles must not create incompatible language forks.

**ASEC-79** — Safety/security profiles constrain capabilities rather than redefining Core type semantics.

**ASEC-80** — Freestanding and kernel programs may omit ordinary runtime/security components.

**ASEC-81** — Freestanding programs retain Core safety semantics unless explicitly using unsafe/system facilities.

**ASEC-82** — Kernel/device access may require unsafe and volatile operations.

**ASEC-83** — GPU/device authority is explicit.

**ASEC-84** — GPU memory safety follows the GPU capability model.

**ASEC-85** — Host/device boundaries remain security boundaries where applicable.

**ASEC-86** — Compiler trust, source trust, package trust and platform trust are distinct.

**ASEC-87** — Comptime execution must not gain unrestricted compiler-host authority.

**ASEC-88** — Compiler sandboxing is independent from application sandboxing.

**ASEC-89** — Compiler ICE is distinct from a source-requested privileged operation failure.

**ASEC-90** — Security-relevant compiler diagnostics are machine-readable.

**ASEC-91** — Security explainability is available through compiler/tooling metadata.

**ASEC-92** — Artifact metadata may describe required capabilities and unsafe/FFI boundaries.

**ASEC-93** — Capability requirements may be propagated through the dependency graph.

**ASEC-94** — Least-privilege analysis may be provided by tooling without changing Core semantics.

**ASEC-95** — Security policies cannot manufacture false memory-safety facts.

**ASEC-96** — Optimizations preserve security contracts that are part of observable semantics.

**ASEC-97** — Security mechanisms are linked only when required by the selected profile/program.

**ASEC-98** — Axiom does not require a monolithic security runtime.

**ASEC-99** — Security abstractions should remain erasable where their semantics permit.

**ASEC-100** — All security mechanisms preserve ownership, capability, memory, concurrency, async, GPU, comptime and FFI invariants.

---

## Kiến trúc sau BOOTSTRAP-083

Đến đây Axiom đã có một chuỗi khá hoàn chỉnh:

```text
Language
   │
   ├── Type
   ├── Ownership
   ├── Capability
   ├── Drop
   ├── Concurrency
   ├── Async
   ├── Comptime
   │
   ├── Memory / Allocation
   ├── Collections
   ├── SIMD / Numeric
   ├── GPU
   │
   ├── I/O / Resources
   ├── FFI / ABI
   ├── Build / Package
   │
   └── Security / Sandbox
            │
            ▼
       Platform / OS
```

**Một nguyên tắc đặc biệt đáng giữ:** Axiom không cố biến security thành một type-system khổng lồ. Memory safety được compiler chứng minh; authority do capability/environment quản lý; machine escape nằm trong `unsafe`; còn privilege cuối cùng thuộc OS/platform.

### Bước kiến trúc tiếp theo

**BOOTSTRAP-084 — Axiom Reflection, Metaprogramming, Derive & Compile-Time Generation Deep Model**

Phần này sẽ khóa hẳn ranh giới giữa:

```text
generic
comptime
reflection
derive
code generation
macro
runtime reflection
```

và đặc biệt giải quyết vấn đề rất quan trọng cho Axiom: **làm sao để AI có thể tự sinh code/type/boilerplate mạnh như macro/procedural macro nhưng không biến compiler thành một hệ thống khó kiểm soát.**