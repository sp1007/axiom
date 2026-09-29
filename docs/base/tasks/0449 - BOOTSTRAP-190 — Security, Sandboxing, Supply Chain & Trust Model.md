# BOOTSTRAP-190 — Security, Sandboxing, Supply Chain & Trust Model
## FROZEN / COMPLETED

Đây là tầng rất quan trọng vì Axiom hiện đã có:

- `unsafe`
- FFI
- comptime
- external tools
- package manager
- dynamic libraries
- plugins
- build system
- AI tooling

Nếu không có trust model thống nhất, mỗi subsystem sẽ tự tạo một kiểu permission khác nhau và cuối cùng ngôn ngữ trở nên rối.

Quyết định trung tâm:

> **Axiom phân biệt rõ “code được phép làm gì” với “code có đúng về memory/type semantics hay không”. Security không thay thế type system, ownership hay verifier; nó nằm trên chúng.**

---

# 1. Ba lớp Trust

Axiom nên có ba lớp độc lập:

```text
┌──────────────────────────────────────┐
│ Application / Package Trust          │
│ "Tôi có tin code này không?"         │
├──────────────────────────────────────┤
│ Capability / Authority               │
│ "Code này được phép làm gì?"         │
├──────────────────────────────────────┤
│ Language Safety                      │
│ "Code này có vi phạm semantics?"     │
└──────────────────────────────────────┘
```

Ví dụ:

Một package có thể:

```text
trusted source
```

nhưng vẫn không được:

```text
read arbitrary filesystem
```

Ngược lại, một chương trình có quyền đọc file vẫn phải tuân thủ:

```text
ownership
type safety
memory safety
```

---

# 2. Safe ≠ Trusted

Đây là distinction cần đóng băng.

### Safe code

Compiler chứng minh được các invariant của Axiom.

### Trusted code

Người dùng/build system/package policy quyết định tin nguồn đó.

Do đó:

```text
Safe + Untrusted
```

hoàn toàn có thể tồn tại.

Ví dụ package nguồn mở chưa audit nhưng vẫn chỉ dùng safe Axiom.

Ngược lại:

```text
Trusted + Unsafe
```

cũng có thể tồn tại.

Ví dụ kernel/driver.

---

# 3. Trust Boundary

Mỗi boundary phải được compiler/toolchain nhận diện:

```text
Source
  │
  ├── safe Axiom
  │
  ├── unsafe Axiom
  │
  ├── FFI
  │
  ├── comptime external capability
  │
  ├── build tool
  │
  ├── dynamic library
  │
  ├── plugin
  │
  └── OS
```

Boundary không đồng nghĩa với "unsafe".

Ví dụ:

```text
safe Axiom → OS syscall wrapper
```

có thể có API an toàn dù bên dưới sử dụng unsafe.

---

# 4. Unsafe Boundary

`unsafe` tiếp tục giữ semantics đã frozen:

```text
unsafe {
    ...
}
```

cho phép thao tác mà compiler không thể chứng minh hoàn toàn.

Nhưng:

> `unsafe` không cấp quyền OS.

Nó chỉ cấp quyền **bỏ qua một số proof mà programmer phải chịu trách nhiệm**.

Ví dụ:

```text
unsafe pointer dereference
```

không có nghĩa:

```text
unsafe → read filesystem
```

Hai loại authority hoàn toàn khác nhau.

---

# 5. Capability Security

Các external authority nên mô hình hóa thành capabilities.

Ví dụ:

```text
ReadFilesystem
WriteFilesystem
ExecuteProcess
Network
Environment
Time
Random
Device
GPU
```

Comptime đã có capability model.

BOOTP-190 mở rộng nguyên tắc này cho build/tooling/runtime security.

---

# 6. Runtime Capability

Một chương trình có thể được chạy với authority:

```text
Program
 ├── stdout
 ├── filesystem/read
 ├── network
 └── process/execute
```

Nhưng nếu chương trình không nhận:

```text
filesystem/write
```

thì việc có API `write_file()` không tự động cấp quyền.

Authority đến từ execution environment.

---

# 7. Không có Ambient Authority trong Core

Axiom không nên thiết kế:

```text
File.open("/etc/...")
```

ngầm có toàn quyền chỉ vì process đang chạy.

Thay vào đó, OS/library boundary có thể yêu cầu một capability/handle thích hợp.

Ví dụ conceptually:

```text
FileSystem.read(path)
```

sử dụng authority mà process/environment cung cấp.

Điều này đặc biệt hữu ích cho:

- sandbox
- server
- plugin
- build system
- AI-generated code
- package execution

---

# 8. Package không tự động được Trust

Package manager từ BOOTSTRAP-187 chỉ xác định:

```text
identity
version
source
content hash
dependencies
```

Không có nghĩa:

```text
package downloaded = trusted
```

Package policy có thể phân loại:

```text
trusted
verified
unknown
blocked
```

Đây là **distribution policy**, không phải language semantics.

---

# 9. Dependency Trust Graph

Build system có thể tạo:

```text
Application
   │
   ├── Package A
   │     ├── Package C
   │     └── Package D
   │
   └── Package B
         └── Package D
```

kèm authority:

```text
A → filesystem/read
B → network
C → none
D → execute/process
```

Developer có thể inspect:

```text
ax audit
ax trust
ax permissions
ax why-capability network
```

---

# 10. Capability Escalation

Một dependency không được âm thầm nâng authority của application.

Ví dụ:

```text
Application
  └── package A
       └── package B
```

Nếu B cần:

```text
Network
```

build/run policy phải biết.

Không được:

```text
download package
→ package silently gets network
```

---

# 11. Build Scripts

Build scripts là một trust boundary đặc biệt.

Ví dụ:

```text
build.ax
```

có thể cần:

```text
filesystem
environment
process execution
network
```

Build system phải phân biệt:

```text
compile source
```

với:

```text
execute build tool
```

Build script không được mặc định có full authority chỉ vì nó chạy trong quá trình build.

---

# 12. Comptime Security

Comptime đã có capability model.

BOOTSTRAP-190 đóng băng thêm:

```text
comptime authority
≠
runtime authority
```

Ví dụ:

```text
comptime {
    read_source(...)
}
```

không có nghĩa binary runtime được quyền đọc source.

Ngược lại:

```text
runtime
```

không kế thừa authority của compiler.

---

# 13. Comptime Reproducibility

External capability phải tham gia build identity:

```text
source
+ dependency
+ compiler
+ target
+ comptime inputs
+ external capability results
```

Nếu comptime đọc:

```text
environment variable
```

thì giá trị đó là build input.

Nếu đọc:

```text
current time
```

reproducible build phải hạn chế hoặc yêu cầu explicit nondeterminism.

---

# 14. Network During Build

Mặc định:

```text
build → network = denied
```

trong hermetic/reproducible mode.

Nếu package thực sự cần network:

```text
explicit capability
```

và kết quả phải được ghi nhận trong build graph hoặc được vendored/cache.

Điều này ngăn build:

```text
hôm nay → code A
ngày mai → code B
```

mà không ai biết dependency đã thay đổi.

---

# 15. Sandboxed Compilation

Axiom compiler nên hỗ trợ:

```text
sandboxed build
```

với:

```text
filesystem
network
environment
process
device
```

được kiểm soát độc lập.

Profiles:

```text
normal
reproducible
hermetic
offline
sandboxed
```

Không ép mọi developer phải dùng strict sandbox.

---

# 16. AI-Generated Code

AI code phải chịu **exactly the same compiler verification**.

```text
AI generated
     ↓
Source
     ↓
Compiler
     ↓
Type
     ↓
Ownership
     ↓
Capability
     ↓
Verifier
```

Không có:

```text
@ai_trusted
```

cho phép bỏ qua compiler.

AI cũng không được tự động:

```text
mark unsafe
grant capability
modify security policy
```

trừ khi người dùng/build policy explicitly cho phép.

---

# 17. Plugin Security

Plugin:

```text
Application
   ↓
Plugin ABI
   ↓
Dynamic Library
```

phải có contract:

```text
ABI
version
capabilities
lifetime
symbols
state
```

Plugin không tự động có toàn bộ quyền của host.

Host có thể cấp authority hạn chế.

---

# 18. Dynamic Library Trust

Khi load:

```text
library.load(...)
```

hệ thống phải biết:

```text
identity
version
ABI
hash/signature policy
dependencies
required capabilities
```

Không được coi:

```text
dynamic library = trusted because ABI matches
```

ABI compatibility chỉ nói:

> Có thể giao tiếp về mặt binary.

Nó không nói:

> Library an toàn hoặc đáng tin.

---

# 19. Symbol Capability

Dynamic symbol cũng là một capability:

```text
LibraryHandle
    ↓
SymbolHandle<T>
```

`SymbolHandle` phải giữ dependency tới library lifetime.

Không cho:

```text
library unload
    ↓
function pointer remains valid
```

trong safe model.

---

# 20. Code Signing

Package/artifact có thể có signature:

```text
artifact
 + hash
 + signature
 + publisher identity
```

Signature xác nhận:

```text
"artifact này đến từ X"
```

không xác nhận:

```text
"artifact này không có bug"
```

Axiom không được biến chữ ký thành semantic proof.

---

# 21. Supply Chain Integrity

Artifact identity từ BOOTSTRAP-187 đã có:

```text
PackageContentHash
DependencyGraphFingerprint
CompilerSemanticVersion
Target
ABI
Features
ComptimeInputs
BuildProfile
CodegenFingerprint
```

BOOTSTRAP-190 bổ sung trust metadata:

```text
publisher
signature
provenance
build provenance
source identity
dependency provenance
```

---

# 22. Reproducible Artifact Verification

Có thể:

```text
Developer A
     ↓
build
     ↓
artifact hash

Developer B
     ↓
same source/inputs
     ↓
build
     ↓
artifact hash
```

và kiểm tra:

```text
hash A == hash B
```

trong reproducible mode.

Đây là **artifact integrity**, không phải proof compiler đúng.

Compiler correctness đã thuộc BOOTSTRAP-188.

---

# 23. Provenance

Artifact có thể chứa:

```text
source package hash
compiler version
target
dependencies
build profile
comptime inputs
```

nhưng thông tin này không bắt buộc phải embed vào executable.

Có thể để trong:

```text
.axmeta
.axbuild
build manifest
```

để binary vẫn nhỏ.

---

# 24. Sandboxing không phải Language Semantics

Một điểm rất quan trọng:

```text
Axiom Language
```

không cần biết:

```text
Docker
WASM sandbox
Windows AppContainer
Linux seccomp
macOS sandbox
```

Compiler chỉ phát ra:

```text
required capabilities
```

Execution environment quyết định enforcement.

```text
Axiom
 ↓
Capability Manifest
 ↓
OS / Sandbox
```

---

# 25. Capability Manifest

Artifact có thể xuất:

```text
axiom.cap
```

hoặc metadata tương đương:

```text
Capabilities:
    filesystem.read
    network.connect
    process.spawn
```

Nếu chương trình không sử dụng:

```text
network
```

thì không nên khai báo network chỉ vì một dependency có API network nhưng dead code.

Capability analysis có thể kết hợp với reachability.

---

# 26. Least Authority

Compiler/build system nên có khả năng tính:

```text
Declared capabilities
```

và:

```text
Actually reachable capabilities
```

Ví dụ:

```text
Package declares:
    filesystem
    network

Application actually reaches:
    filesystem/read
```

Tooling cảnh báo:

```text
unused authority: network
```

Không tự động thay đổi semantics.

---

# 27. Memory Safety và Security Safety

Hai khái niệm phải tách biệt.

Axiom safe code có thể đảm bảo:

```text
no use-after-free
no double-drop
no safe data race
```

nhưng không đảm bảo:

```text
authentication correctness
SQL injection
logic bugs
bad cryptography
```

Do đó không dùng cụm:

> “memory-safe nên secure”.

Compiler chỉ chứng minh những properties thuộc semantic model.

---

# 28. Constant-Time

BOOTSTRAP-161 đã có security/constant-time.

BOOTP-190 xác định trust boundary:

```text
@constant_time
```

không phải lời hứa chung chung của compiler.

Compiler phải biết contract:

```text
secret-dependent branches forbidden
secret-dependent memory access forbidden
```

trong vùng áp dụng.

Nếu compiler không thể chứng minh:

```text
reject
```

hoặc yêu cầu explicit unsafe/trusted boundary theo contract đã định nghĩa.

---

# 29. Secrets

Axiom không nên có một kiểu:

```text
Secret<T>
```

ở Core chỉ để giải quyết security application-level.

Nhưng compiler/toolchain có thể hỗ trợ metadata:

```text
@secret
```

ở security/system libraries sau này.

Mục tiêu:

- tránh debug dump
- tránh accidental logging
- tránh core dump khi có policy
- zeroization contract

nhưng đây là extension, không làm phình Core v1.

---

# 30. Permissions không được trở thành Type Explosion

Không nên tạo:

```text
FileRead
FileWrite
FileReadWrite
NetworkRead
NetworkWrite
...
```

thành hàng trăm Core type.

Authority nên là:

```text
capability/policy layer
```

trong khi resource types vẫn:

```text
File
Socket
Process
Device
```

như BOOTSTRAP-184.

---

# 31. Trust Model tổng hợp

```text
                 ┌───────────────┐
                 │   Developer   │
                 └───────┬───────┘
                         │
                    source/package
                         ↓
                 ┌───────────────┐
                 │    Compiler   │
                 └───────┬───────┘
                         │
              ┌──────────┴──────────┐
              ↓                     ↓
        Language Safety       Capability Analysis
              │                     │
              ↓                     ↓
       Verified Program      Required Authority
              │                     │
              └──────────┬──────────┘
                         ↓
                 ┌───────────────┐
                 │ Build Policy  │
                 └───────┬───────┘
                         ↓
                 ┌───────────────┐
                 │ Execution Env │
                 └───────────────┘
```

---

# 32. Security Architecture của Axiom

Tổng hợp lại:

```text
Layer 1
Language Safety
    Type
    Ownership
    Capability
    Concurrency
    Memory

Layer 2
Unsafe / FFI
    Explicit trust boundary

Layer 3
Build Authority
    Comptime
    Build scripts
    External tools

Layer 4
Package Trust
    Hash
    Signature
    Provenance
    Dependency graph

Layer 5
Runtime Authority
    Filesystem
    Network
    Process
    Device

Layer 6
OS Enforcement
    Sandbox
    Permissions
    Kernel
```

Không layer nào được giả làm layer khác.

---

# 33. Những thứ Axiom **không** làm

Để tránh overdesign, Core không có:

```text
❌ mandatory capability objects cho mọi function
❌ mandatory sandbox
❌ mandatory package signatures
❌ mandatory network restrictions
❌ mandatory runtime permission system
❌ mandatory security annotations
❌ mandatory cryptographic type hierarchy
❌ mandatory GC
❌ mandatory runtime
```

Axiom chỉ cung cấp **semantic hooks + metadata + tooling** để những hệ thống đó xây được.

---

# Invariants mới — FROZEN

### `ASEC-20`
Language safety và trustworthiness là hai khái niệm độc lập.

### `ASEC-21`
Safe code không đồng nghĩa với trusted code.

### `ASEC-22`
Unsafe không tự động cấp OS authority.

### `ASEC-23`
External authority phải đi qua explicit capability/policy boundary.

### `ASEC-24`
Comptime authority không trở thành runtime authority.

### `ASEC-25`
Runtime authority không trở thành comptime authority.

### `ASEC-26`
Build scripts là trust boundary riêng với ordinary compilation.

### `ASEC-27`
Network/filesystem/process access trong hermetic build phải bị giới hạn mặc định.

### `ASEC-28`
AI-generated code chịu cùng semantic verification như human-written code.

### `ASEC-29`
AI không được bypass compiler verification hoặc tự cấp authority.

### `ASEC-30`
Package identity/hash không đồng nghĩa package trust.

### `ASEC-31`
Signature chứng minh provenance/integrity, không chứng minh semantic correctness.

### `ASEC-32`
ABI compatibility không đồng nghĩa trust hoặc security.

### `ASEC-33`
Dynamic library lifetime phải bao phủ mọi live symbol capability.

### `ASEC-34`
Capability escalation qua dependency phải explicit và observable.

### `ASEC-35`
Unused capabilities có thể được phát hiện bằng reachability analysis.

### `ASEC-36`
Security policy không được thay đổi language semantics.

### `ASEC-37`
Sandbox implementation là execution-environment concern, không phải Core language primitive.

### `ASEC-38`
Memory safety không được quảng bá như proof của application security.

### `ASEC-39`
Constant-time guarantees phải dựa trên explicit compiler-verifiable contracts.

### `ASEC-40`
Security metadata không được trở thành runtime dependency nếu application không yêu cầu.

### `ASEC-41`
Trust metadata phải có provenance rõ ràng.

### `ASEC-42`
Hermetic/reproducible builds phải phân biệt external inputs với deterministic semantic inputs.

### `ASEC-43`
Least-authority analysis không được tự động thay đổi quyền của chương trình mà không có explicit policy.

### `ASEC-44`
Security checks không được làm mất khả năng xây dựng freestanding/runtime-free Axiom programs.

---

# Trạng thái

**BOOTSTRAP-190 — FROZEN / COMPLETED**

Đến đây Axiom đã giải quyết gần như toàn bộ **language/compiler architecture** cốt lõi:

```text
Language
Type
Trait
Ownership
Memory
Capability
Concurrency
Async
GPU
Comptime
Reflection
OS/Process
IR
Verification
Optimization
ABI
Backend
Linker
Runtime
Bootstrap
Build
Package
Testing
Formal Semantics
Tooling
AI Interface
Security
Trust
Supply Chain
```

Nhưng còn một lớp rất lớn trước khi có thể nói kiến trúc Axiom đã tương đối hoàn chỉnh:

# BOOTSTRAP-191 — Diagnostics, Error Recovery, IDE Recovery & Partial-Program Semantics

Trọng tâm lần này sẽ là một vấn đề thực tế mà các compiler thường xử lý chưa tốt:

```text
Code đang viết dở
      ↓
syntax lỗi
      ↓
type chưa resolve
      ↓
trait chưa hoàn thành
      ↓
ownership chưa xác định
```

nhưng **IDE vẫn phải hoạt động tốt**, completion vẫn phải có, diagnostics không được cascade thành 500 lỗi vô nghĩa, và AI agent phải có thể làm việc với **program chưa hoàn chỉnh**.

Nó sẽ thiết kế:

- error-tolerant parser
- missing-token recovery
- error nodes trong SyntaxDB/HIR
- partial type inference
- unknown/error types
- diagnostic suppression/deduplication
- dependency-aware diagnostics
- incremental recovery
- incomplete trait resolution
- incomplete ownership analysis
- IDE completion trên code lỗi
- AI repair suggestions
- diagnostic causal graph
- “one root error → derived errors”
- compiler behavior khi program chưa compile được

Đây là bước cuối rất quan trọng để biến compiler architecture hiện tại thành một **compiler thực sự usable hàng ngày**, thay vì chỉ đúng khi source đã hoàn chỉnh.