Tiếp nối đúng chuỗi, **BOOTSTRAP-603** tập trung vào security boundary và capability model, làm nền cho các subsystem native phía sau.

:::writing{variant="document" id="74163" title="BOOTSTRAP-603 — NATIVE APPLICATION SECURITY BOUNDARY, CAPABILITY SYSTEM, PERMISSIONS & TRUSTED RUNTIME 5.0"}

# BOOTSTRAP-603 — NATIVE APPLICATION SECURITY BOUNDARY, CAPABILITY SYSTEM, PERMISSIONS & TRUSTED RUNTIME 5.0

**Status:** Architecture / Implementation Specification  
**Layer:** Native Runtime / Security  
**Depends on:** BOOTSTRAP-600, BOOTSTRAP-601, BOOTSTRAP-602  
**Primary concern:** Security boundaries, capabilities, permissions, privilege separation, trusted runtime  
**Design goal:** Security mạnh nhưng không biến Axiom thành một hệ thống permission phức tạp trong mọi application.

---

# 603.0 — Mục tiêu

BOOTSTRAP-603 định nghĩa security foundation của Axiom native runtime.

Subsystem phải cung cấp:

1. Security boundary.
2. Capability-based access control.
3. Permission model.
4. Privilege separation.
5. Resource authority.
6. Process/module trust boundaries.
7. Sandboxing integration.
8. Secret access control.
9. File/network/device capabilities.
10. Native OS permission mapping.
11. Runtime capability attenuation.
12. Secure defaults.
13. Explicit privilege escalation.
14. Capability inspection.
15. Audit integration.
16. Secure IPC boundary.
17. Plugin/module isolation.
18. Crash-safe security behavior.
19. Compiler/linker security metadata.
20. Minimal overhead when security features are unused.

Core principle:

> **Code chỉ có quyền làm những gì capability của nó cho phép.**

---

# 603.1 — Security architecture

Mô hình tổng quát:

```text
Application
    ↓
Axiom Security API
    ↓
Capability Runtime
    ├── Capability Registry
    ├── Permission Resolver
    ├── Policy Engine
    ├── Trust Boundary
    ├── Resource Guards
    └── Audit Hooks
             ↓
      Platform Security Adapter
             ↓
 Windows / Linux / macOS / iOS / Android / WASM
```

---

# 603.2 — Security boundary

Security boundary là nơi code không còn được mặc định tin tưởng lẫn nhau.

Boundary có thể nằm giữa:

```text
process
module
plugin
sandbox
IPC peer
external resource
```

---

# 603.3 — Trusted Computing Base

Axiom security TCB tối thiểu:

```text
kernel / OS
Axiom loader
Axiom runtime security core
platform security adapter
```

Application code không thuộc TCB.

---

# 603.4 — Không biến toàn runtime thành TCB

Logging, GUI, application framework và business library không được mặc định trở thành security authority.

---

# 603.5 — Capability model

Capability là một opaque authority token:

```axiom
Capability<FileRead>
```

hoặc:

```axiom
Capability<NetworkConnect>
```

Capability không phải chỉ là boolean permission.

---

# 603.6 — Permission vs capability

Permission:

> chính sách cho phép hoặc từ chối hành động.

Capability:

> authority cụ thể mà code đang sở hữu.

Ví dụ:

```text
permission:
    application may read files

capability:
    read authority for /data/app/
```

---

# 603.7 — Capability principle

Không kiểm tra:

```text
"application có permission không?"
```

ở mọi nơi nếu capability đã xác nhận authority.

Thay vào đó:

```text
operation(capability, resource)
```

---

# 603.8 — Opaque capability

Capability không expose:

```text
pointer
OS handle
filesystem path
kernel object internals
```

trực tiếp.

---

# 603.9 — Capability ownership

Capability là value/handle có ownership semantics rõ ràng.

Copy chỉ được phép nếu capability type cho phép.

---

# 603.10 — Capability attenuation

Capability có thể bị giảm quyền:

```text
full file capability
        ↓
read-only capability
        ↓
specific directory capability
```

Không được tăng quyền bằng attenuation.

---

# 603.11 — Monotonic authority

Một function nhận capability chỉ được:

```text
use
delegate
attenuate
```

không tự tạo capability mạnh hơn.

---

# 603.12 — Capability creation

Capability mới chỉ được tạo bởi:

```text
trusted runtime
OS authority
explicit privileged subsystem
```

---

# 603.13 — Application bootstrap capabilities

Application nhận initial capabilities từ:

```text
deployment manifest
OS sandbox
runtime bootstrap
```

---

# 603.14 — Capability manifest

BOOTSTRAP-601 deployment manifest có thể khai báo:

```text
capabilities:
    filesystem.read
    filesystem.write
    network.connect
```

---

# 603.15 — Default-deny

Capability không được cấp:

```text
→ operation denied
```

---

# 603.16 — Compatibility mode

Native desktop application có thể chạy legacy-compatible mode:

```text
security.mode = native
```

Trong mode này OS permissions là boundary chính.

---

# 603.17 — Hardened mode

```text
security.mode = hardened
```

mọi resource access đi qua explicit capability.

---

# 603.18 — Minimal mode

```text
security.mode = minimal
```

chỉ giữ security primitives cần thiết cho target.

---

# 603.19 — Security profiles

Recommended:

```text
desktop
server
sandbox
embedded
mobile
wasm
```

---

# 603.20 — Capability namespaces

Canonical namespaces:

```text
filesystem
network
process
thread
memory
device
graphics
audio
camera
microphone
ipc
environment
clock
random
debug
```

---

# 603.21 — Filesystem capabilities

Types:

```text
FileRead
FileWrite
DirectoryList
DirectoryCreate
FileDelete
FileRename
FileExecute
```

---

# 603.22 — File capability granularity

Capability có thể giới hạn:

```text
resource
operation
path scope
```

Ví dụ:

```text
Read /app/data/*
```

---

# 603.23 — Path canonicalization

Security check phải canonicalize path trước khi quyết định authority.

Phải chống:

```text
../
symlink escape
junction escape
case confusion
alternate path syntax
```

tùy platform.

---

# 603.24 — Symlink policy

Filesystem capability phải có policy:

```text
follow
deny
follow-within-root
```

Default hardened mode:

```text
follow-within-root
```

---

# 603.25 — TOCTOU

Không dựa vào:

```text
check(path)
→ later open(path)
```

nếu platform có secure descriptor-based operation.

---

# 603.26 — Secure open

Ưu tiên:

```text
resolve + open + verify
```

trong một security-aware operation.

---

# 603.27 — File handle capability

Sau khi file được mở:

```text
FileHandle
```

có thể trở thành capability độc lập với path.

---

# 603.28 — Path capability vs handle capability

Path capability:

> quyền mở resource.

Handle capability:

> quyền thao tác trên resource đã mở.

---

# 603.29 — Directory capability

Directory capability giới hạn descendant resources.

---

# 603.30 — Temporary file capability

Runtime có thể cung cấp:

```axiom
temp.create(capability)
```

không cần cấp toàn filesystem write.

---

# 603.31 — Network capabilities

Types:

```text
NetworkConnect
NetworkListen
NetworkResolve
NetworkRaw
```

---

# 603.32 — Endpoint restriction

Network capability có thể giới hạn:

```text
protocol
host
port
direction
```

---

# 603.33 — DNS capability

DNS resolution có thể tách:

```text
NetworkResolve
```

khỏi:

```text
NetworkConnect
```

---

# 603.34 — Listen capability

Server application cần explicit:

```text
NetworkListen
```

---

# 603.35 — Raw socket capability

Raw networking là elevated capability.

Không cấp mặc định trong hardened profile.

---

# 603.36 — Localhost policy

Localhost không mặc định được coi là harmless.

Security policy phải phân biệt:

```text
loopback
LAN
internet
```

nếu target cần.

---

# 603.37 — Process capabilities

Types:

```text
ProcessSpawn
ProcessSignal
ProcessInspect
ProcessDebug
ProcessTerminate
```

---

# 603.38 — Child process authority

Child process mặc định không tự động nhận toàn bộ parent capabilities.

---

# 603.39 — Capability inheritance

Explicit policy:

```text
inherit-none
inherit-selected
inherit-all
```

Default hardened:

```text
inherit-selected
```

---

# 603.40 — Capability passing

Capability có thể được truyền qua trusted IPC nếu platform hỗ trợ.

---

# 603.41 — Capability duplication

OS resource handle duplication phải tạo capability mới với authority không vượt quá source.

---

# 603.42 — Thread capabilities

Thread creation không mặc định tạo privilege.

Thread inherits execution context nhưng authority propagation phải explicit đối với privileged capabilities.

---

# 603.43 — Memory capabilities

Memory authority gồm:

```text
Allocate
Map
Execute
Protect
SharedMemory
```

---

# 603.44 — W^X principle

Executable memory mặc định:

```text
write XOR execute
```

Không cho:

```text
write + execute
```

trừ target/policy explicitly yêu cầu.

---

# 603.45 — JIT capability

JIT runtime cần:

```text
MemoryJIT
```

explicit capability.

---

# 603.46 — Executable memory

`ExecutableMemory` không được tạo chỉ từ:

```text
MemoryAllocate
```

---

# 603.47 — Memory protection transitions

Cho phép:

```text
RW → RX
```

khi policy cho phép.

Hạn chế:

```text
RWX
```

---

# 603.48 — Dynamic code loading

Dynamic executable loading yêu cầu:

```text
ModuleLoad
```

và tùy target:

```text
ExecutableMemory
```

---

# 603.49 — Library loading

Capability:

```text
LibraryLoad
```

có thể giới hạn:

```text
trusted directories
signed modules
known build IDs
```

---

# 603.50 — DLL/shared library search

Security-sensitive loader không dùng unrestricted search path.

Ưu tiên:

```text
explicit absolute/validated path
known module directory
trusted search scope
```

---

# 603.51 — Module trust

Module metadata:

```text
module_id
build_id
publisher
signature
trust_level
```

nếu platform cung cấp.

---

# 603.52 — Signed module

Optional policy:

```text
require_signed_modules = true
```

---

# 603.53 — Signature verification

Verification thuộc security loader/tooling layer.

Không cần crypto implementation trong language syntax.

---

# 603.54 — Crypto boundary

Axiom security API có thể expose:

```text
hash
MAC
signature
key
random
```

nhưng cryptographic primitives thuộc một subsystem riêng.

---

# 603.55 — Random capability

Secure randomness:

```text
SecureRandom
```

phải đến từ trusted OS/runtime source.

---

# 603.56 — Deterministic random

Testing có thể dùng deterministic RNG.

Không được nhầm với cryptographic random.

---

# 603.57 — Environment capability

Environment variable access:

```text
EnvironmentRead
```

có thể bị giới hạn theo key allowlist.

---

# 603.58 — Secret environment variables

Secret environment variables không tự động được expose vào arbitrary application modules.

---

# 603.59 — BOOTSTRAP-601 Secret integration

`Secret<T>` chỉ được unwrap khi code sở hữu capability tương ứng.

---

# 603.60 — Secret capability

Ví dụ:

```text
SecretRead<DatabaseCredential>
```

---

# 603.61 — Secret non-copy policy

Sensitive secret capability nên hỗ trợ move-only semantics khi phù hợp.

---

# 603.62 — Secret lifetime

Secret value phải có explicit lifetime.

Runtime không giữ bản sao không cần thiết.

---

# 603.63 — Secret zeroization

Memory containing sensitive material có thể được zeroized trước release nếu semantics/optimizer cho phép.

---

# 603.64 — Compiler-aware secret memory

Compiler phải tránh tối ưu hóa zeroization thành no-op khi API yêu cầu secure wipe.

---

# 603.65 — Debugger restriction

Debugger access là privileged capability:

```text
ProcessDebug
```

---

# 603.66 — Diagnostic integration

BOOTSTRAP-602 được phép biết:

```text
capability IDs
security policy status
```

nhưng không log capability secret material.

---

# 603.67 — Audit integration

Security-sensitive decisions có thể emit:

```text
CAPABILITY_GRANTED
CAPABILITY_DENIED
POLICY_CHANGED
MODULE_REJECTED
```

---

# 603.68 — Audit anti-recursion

Security audit failure không được gây recursive security failure.

---

# 603.69 — Permission request

Application có thể request:

```axiom
security.request(NetworkConnect)
```

Nhưng request không đảm bảo được cấp.

---

# 603.70 — Permission decision

Decision:

```text
granted
denied
unavailable
requires_user
```

---

# 603.71 — User approval

Mobile/desktop UI permission prompts thuộc platform adapter.

Core runtime không hiển thị UI.

---

# 603.72 — Permission caching

Granted authority có thể cache theo:

```text
process
session
installation
OS policy
```

tùy platform.

---

# 603.73 — Permission revocation

Capability phải phản ánh revocation khi platform yêu cầu.

---

# 603.74 — Revoked capability

Operation với revoked capability:

```text
SecurityError
```

Không undefined behavior.

---

# 603.75 — Capability generation

Capability handle có generation/version để tránh stale handle.

---

# 603.76 — Capability invalidation

Khi revoked:

```text
generation++
```

---

# 603.77 — Capability lookup

Capability IDs không phải secret.

Capability object itself phải opaque.

---

# 603.78 — Capability forgery

Không thể tạo valid capability bằng:

```text
integer cast
pointer cast
memory copy
string parsing
```

---

# 603.79 — Type safety

Compiler/runtime phải ngăn:

```text
Capability<FileRead>
```

được sử dụng như:

```text
Capability<FileWrite>
```

---

# 603.80 — No ambient authority

Không cho API kiểu:

```axiom
File.open(path)
```

trong hardened capability-only context.

Thay bằng:

```axiom
File.open(file_capability, path)
```

---

# 603.81 — Convenience APIs

Desktop compatibility API có thể tồn tại:

```axiom
File.open(path)
```

nhưng compiler/runtime phải map nó tới ambient capability context.

---

# 603.82 — Ambient context

Ambient authority được coi là compatibility feature, không phải security ideal.

---

# 603.83 — Capability-first APIs

New Axiom standard APIs ưu tiên:

```text
capability + resource
```

---

# 603.84 — GUI capabilities

GUI operations:

```text
WindowCreate
ClipboardRead
ClipboardWrite
ScreenCapture
```

---

# 603.85 — Clipboard

Clipboard read/write có thể là separate capabilities.

---

# 603.86 — Screen capture

Screen capture là privileged capability.

---

# 603.87 — Camera capability

```text
CameraAccess
```

---

# 603.88 — Microphone capability

```text
MicrophoneAccess
```

---

# 603.89 — Audio output

Audio playback không nhất thiết cần same privilege as microphone.

---

# 603.90 — GPU capability

```text
GPUAccess
GPUCompute
GPUMemory
```

có thể được phân tách tùy platform.

---

# 603.91 — Device capability

Generic:

```text
DeviceAccess
```

không tự động cấp raw device access.

---

# 603.92 — IPC capability

Types:

```text
IpcConnect
IpcListen
IpcSend
IpcReceive
```

---

# 603.93 — IPC endpoint authority

Capability có thể giới hạn endpoint:

```text
service://database
```

---

# 603.94 — Message authority

IPC capability có thể giới hạn message classes.

---

# 603.95 — Serialization boundary

Data crossing trust boundary phải được validate.

Không truyền raw pointer.

---

# 603.96 — Shared memory

Shared memory cần:

```text
SharedMemoryCreate
SharedMemoryMap
```

và explicit access mode.

---

# 603.97 — Shared memory permissions

```text
read
write
execute
```

phải được kiểm soát độc lập.

---

# 603.98 — Untrusted input

Tất cả external input:

```text
file
network
IPC
plugin
environment
```

được xem là untrusted.

---

# 603.99 — Parser boundary

Parser phải validate:

```text
length
encoding
structure
resource limits
```

---

# 603.100 — Security resource limits

Mỗi trust boundary có:

```text
max bytes
max objects
max nesting
max messages
max CPU
max memory
```

khi cần.

---

# 603.101 — Resource capability

Capability có thể chứa quota:

```text
NetworkConnect<max_connections=100>
```

hoặc runtime policy tương đương.

---

# 603.102 — Quota enforcement

Quota phải enforced ở trusted layer.

Application không được tự khai báo quota rồi tự tin tưởng.

---

# 603.103 — Rate limit

Security-sensitive APIs có thể có rate limit.

---

# 603.104 — DoS resistance

Capability boundary phải hạn chế resource exhaustion từ untrusted peers.

---

# 603.105 — IPC authentication

IPC peer identity phải được platform adapter cung cấp khi có.

---

# 603.106 — Peer identity

Canonical:

```text
PeerIdentity
```

có thể chứa:

```text
process
user
sandbox
certificate
signature
```

---

# 603.107 — Peer trust

Trust decision:

```text
trusted
untrusted
unknown
```

Không được suy ra chỉ từ process name.

---

# 603.108 — User identity

OS user identity là platform-specific metadata.

Không đưa assumptions POSIX/Windows vào core.

---

# 603.109 — Privilege identity

Runtime có thể query:

```axiom
security.identity()
```

---

# 603.110 — Identity vs capability

Identity không thay thế capability.

Một user identity có thể có nhiều security contexts.

---

# 603.111 — Privilege dropping

Trusted bootstrap code có thể drop privileges.

```axiom
security.drop(capability)
```

Authority loss phải monotonic.

---

# 603.112 — No privilege regain

Sau khi capability bị dropped:

```text
→ không thể lấy lại từ child code
```

trừ trusted re-bootstrap boundary.

---

# 603.113 — Privileged operation

Privileged runtime operation yêu cầu explicit capability.

---

# 603.114 — Capability delegation

```axiom
child = spawn(task, with = [FileRead(data_cap)])
```

Child chỉ nhận capabilities được chỉ định.

---

# 603.115 — Task capability context

Async task context có capability set riêng hoặc immutable inherited set.

---

# 603.116 — Capability context

Context:

```text
CapabilityContext
```

không nên là mutable global dictionary.

---

# 603.117 — Capability lookup performance

Hot operations nên dùng direct opaque handles.

Không lookup string permission mỗi syscall.

---

# 603.118 — Compile-time capability checking

Compiler có thể kiểm tra capability requirements:

```axiom
requires NetworkConnect
fn connect(...) ...
```

---

# 603.119 — Function capability declaration

Syntax đề xuất:

```axiom
@requires(NetworkConnect)
fn connect(...)
```

---

# 603.120 — Capability metadata

Compiler emits:

```text
required_capabilities
```

vào module metadata.

---

# 603.121 — Module capability manifest

Module:

```text
module network_client {
    requires:
        NetworkConnect
}
```

---

# 603.122 — Link-time capability analysis

Linker có thể tính:

```text
application required capabilities
```

---

# 603.123 — Dead capability elimination

Nếu code không dùng network:

```text
NetworkConnect
```

không nên xuất hiện trong final capability manifest.

---

# 603.124 — Capability graph

Tooling có thể visualize:

```text
Application
 ├── FileRead
 ├── NetworkConnect
 └── ProcessSpawn
```

---

# 603.125 — Least privilege analysis

Tooling có thể report:

```text
declared capability
used capability
unused capability
```

---

# 603.126 — No security ranking

Tooling chỉ báo dữ liệu; không tự đưa ra overall security score.

---

# 603.127 — Policy engine

Policy engine input:

```text
request
identity
capability
resource
deployment policy
platform policy
```

Output:

```text
allow
deny
prompt
```

---

# 603.128 — Policy determinism

Same inputs + same policy state phải cho same decision.

---

# 603.129 — Policy version

Every security policy snapshot có:

```text
policy_version
policy_fingerprint
```

---

# 603.130 — Policy reload

Policy changes phải atomic.

Existing operation đang chạy không bị mid-operation corruption.

---

# 603.131 — Revocation semantics

New operations observe new policy.

Already-open resources follow explicit resource lifetime policy.

---

# 603.132 — Policy cache

Permission decision cache phải invalidated khi policy generation thay đổi.

---

# 603.133 — Security generation

Global:

```text
security_generation
```

tăng khi authority/policy thay đổi.

---

# 603.134 — Security events

Events:

```text
CAPABILITY_REQUEST
CAPABILITY_GRANTED
CAPABILITY_DENIED
CAPABILITY_REVOKED
POLICY_RELOADED
SECURITY_BOUNDARY_VIOLATION
```

---

# 603.135 — Denial diagnostics

Denied operation có:

```text
reason_code
capability
resource_class
policy_generation
```

Không ghi secret/resource content nhạy cảm.

---

# 603.136 — Reason codes

Stable machine-readable codes:

```text
NOT_GRANTED
REVOKED
OUT_OF_SCOPE
POLICY_DENIED
PLATFORM_DENIED
RESOURCE_LIMIT
INVALID_CAPABILITY
```

---

# 603.137 — SecurityError

Canonical error:

```axiom
SecurityError {
    code
    operation
    capability_kind
}
```

---

# 603.138 — Error information limits

Không expose:

```text
policy internals
security tokens
secret paths
```

nếu không cần.

---

# 603.139 — Security boundary violation

Attempt to bypass capability:

```text
SECURITY_BOUNDARY_VIOLATION
```

---

# 603.140 — Fail closed

Security subsystem failure trong privileged operation:

```text
deny
```

trừ explicitly documented compatibility behavior.

---

# 603.141 — Fail open prohibition

Không được:

```text
security check failed
→ allow anyway
```

trong hardened mode.

---

# 603.142 — Compatibility fallback

Legacy desktop APIs có thể fallback to OS native permission behavior, nhưng phải được ghi nhận trong security profile.

---

# 603.143 — Sandbox integration

Runtime phát hiện sandbox:

```text
SandboxStatus
```

---

# 603.144 — Sandbox types

Opaque:

```text
OS
Container
AppSandbox
WASM
Custom
None
```

---

# 603.145 — Sandbox doesn't equal capability

Sandbox là platform boundary.

Capability là language/runtime authority.

Hai lớp phải độc lập.

---

# 603.146 — Sandbox escape resistance

Axiom runtime không được cung cấp API cố ý bypass sandbox.

---

# 603.147 — Native syscall boundary

Core runtime không expose arbitrary syscall API trong safe standard library.

---

# 603.148 — Unsafe syscall API

Nếu cần low-level system programming:

```axiom
unsafe.os_call(...)
```

phải explicit unsafe capability/module.

---

# 603.149 — Unsafe code

Unsafe code không tự động có unlimited authority.

Unsafe chỉ bỏ một số compile-time safety guarantees.

---

# 603.150 — Security and unsafe

```text
unsafe != privileged
```

---

# 603.151 — FFI boundary

Foreign function interface là trust boundary.

```text
@unsafe
extern fn ...
```

---

# 603.152 — FFI capability

External function có thể declare:

```text
requires capability
```

---

# 603.153 — Native library trust

FFI library không mặc định được trusted chỉ vì load thành công.

---

# 603.154 — ABI validation

Dynamic module ABI phải được validate trước invocation.

---

# 603.155 — Plugin sandbox

Plugin có thể chạy:

```text
same-process
isolated-process
sandbox
```

---

# 603.156 — Same-process plugin

Same-process plugin phải được coi là fully privileged relative to process memory.

Capability model không thể bảo vệ khỏi malicious native code trong cùng address space nếu plugin có unrestricted raw memory access.

---

# 603.157 — Isolated plugin

Process-isolated plugin mới tạo được security boundary mạnh.

---

# 603.158 — Plugin manifest

Plugin manifest:

```text
plugin_id
version
build_id
required_capabilities
optional_capabilities
sandbox_policy
```

---

# 603.159 — Plugin approval

Deployment/application decides whether required capabilities are granted.

---

# 603.160 — Plugin capability attenuation

Plugin nhận subset:

```text
application capabilities
```

không toàn bộ.

---

# 603.161 — Plugin communication

IPC validates:

```text
message schema
peer identity
capability
resource limits
```

---

# 603.162 — Plugin crash isolation

Isolated plugin crash không được crash parent mặc định.

---

# 603.163 — Plugin diagnostic integration

BOOTSTRAP-602 có thể record:

```text
plugin crash
plugin denied capability
plugin health
```

---

# 603.164 — Security event privacy

Audit events phải tránh log raw secrets.

---

# 603.165 — Capability ID privacy

Opaque capability ID có thể được logged.

Không log underlying secret token.

---

# 603.166 — Token representation

Internal capability token có thể là:

```text
index + generation + MAC
```

hoặc equivalent.

Exact implementation là runtime detail.

---

# 603.167 — Capability forgery resistance

Token validation phải chống:

```text
guessing
stale handles
type confusion
cross-context reuse
```

---

# 603.168 — Cross-process capability

Không truyền raw capability token giữa process nếu token không có process binding.

---

# 603.169 — IPC capability transfer

Transfer protocol tạo receiver-bound capability.

---

# 603.170 — Capability serialization

Capabilities không serialize thành plain integers.

---

# 603.171 — Persistence

Capabilities không mặc định persistent qua restart.

---

# 603.172 — Restart semantics

Process restart:

```text
old capabilities invalid
new bootstrap capabilities issued
```

---

# 603.173 — Crash semantics

Sau crash:

```text
all process-local capabilities invalid
```

---

# 603.174 — Capability lifetime

Capability lifetime có thể:

```text
process
task
resource
session
```

---

# 603.175 — Scoped capabilities

API:

```axiom
with capability:
    ...
```

Capability tự động release/attenuate khi scope kết thúc.

---

# 603.176 — Capability transfer

Move-only capability có thể transfer ownership.

---

# 603.177 — Capability duplication

Duplicable read-only capabilities có thể clone nếu policy cho phép.

---

# 603.178 — Revocable capability

Capability có revocation bit/generation.

---

# 603.179 — Non-revocable capability

Một số OS handles không thể revoke independently.

Runtime phải document platform limitation.

---

# 603.180 — Security status

API:

```axiom
security.status()
```

trả:

```text
profile
sandbox
policy_generation
capability_count
```

Không dump secret.

---

# 603.181 — Capability inspection

Developer tooling có thể:

```text
axiom security inspect
```

---

# 603.182 — Security manifest inspection

Tool:

```text
axiom security manifest app.exe
```

hiển thị required capabilities.

---

# 603.183 — Runtime capability inspection

Tooling có thể xem granted capabilities nếu process policy cho phép.

---

# 603.184 — Capability debugging

Debug build có thể hiển thị:

```text
source
capability kind
grant location
```

---

# 603.185 — Production inspection

Production chỉ expose minimized information.

---

# 603.186 — Security diagnostics integration

Security violations emit structured event:

```text
category = security
```

---

# 603.187 — Diagnostic redaction

Security layer must mark sensitive fields as `Secret<T>` or equivalent before passing to BOOTSTRAP-602.

---

# 603.188 — Configuration boundary

BOOTSTRAP-601 controls policy configuration.

BOOTSTRAP-603 interprets security policy.

---

# 603.189 — Config tampering

Security-critical configuration should support:

```text
signature
integrity hash
trusted source
```

when deployment requires.

---

# 603.190 — Secure configuration loading

Security policy must not be loaded from an untrusted path merely because application config points there.

---

# 603.191 — Policy trust root

Trusted policy source may be:

```text
OS
signed deployment manifest
administrator
embedded application policy
```

---

# 603.192 — Embedded policy

Compiler may embed immutable security baseline.

---

# 603.193 — Policy precedence

Security policy precedence:

```text
platform
→ deployment
→ application
→ runtime attenuation
```

A lower layer cannot grant authority prohibited by higher layer.

---

# 603.194 — Policy monotonicity

Application policy can only:

```text
restrict
```

unless platform explicitly permits delegation.

---

# 603.195 — Security defaults

Default policy:

```text
no raw syscall
no raw device
no arbitrary code loading
no raw process debug
no raw executable memory
```

unless target profile explicitly requires them.

---

# 603.196 — Desktop compatibility

Desktop native apps may request broad filesystem access through explicit deployment profile.

This is compatibility, not recommended capability granularity.

---

# 603.197 — Mobile policy

Mobile targets defer user-visible permission semantics to OS.

---

# 603.198 — WASM policy

WASM capabilities depend entirely on host bindings.

No implicit filesystem/network authority.

---

# 603.199 — Server policy

Server profile supports explicit:

```text
network listen
filesystem
process spawn
```

according to deployment manifest.

---

# 603.200 — Embedded policy

Embedded target may map capabilities to device/RTOS permissions.

---

# 603.201 — Capability compiler metadata

Compiler emits:

```text
.axsec
```

or equivalent metadata containing:

```text
required capability set
security profile
ABI/security version
```

Exact section name is implementation-defined until object format freeze.

---

# 603.202 — Linker capability merge

When linking modules:

```text
required_capabilities =
union(module_requirements)
```

then dead-code elimination removes requirements belonging only to removed code.

---

# 603.203 — Capability conflict

If module requires capability prohibited by deployment:

```text
link/deployment validation failure
```

when statically known.

---

# 603.204 — Runtime capability failure

If not statically known:

```text
SecurityError
```

at operation time.

---

# 603.205 — Security policy compiler

Future tooling may compile high-level security policy into compact runtime representation.

---

# 603.206 — Policy representation

Runtime policy should be compact:

```text
capability
scope
operation
constraints
generation
```

---

# 603.207 — Policy matching

Policy matching should avoid string-heavy operations on hot path.

Use interned IDs / canonical resource descriptors.

---

# 603.208 — Filesystem scope representation

Possible:

```text
root capability ID
relative path
operation mask
```

---

# 603.209 — Network scope representation

Possible:

```text
protocol
address family
host scope
port range
operation mask
```

---

# 603.210 — Process scope representation

Possible:

```text
child-only
same-user
specific executable
specific module
```

---

# 603.211 — Device scope

Device authority identified by stable device class/ID where platform allows.

---

# 603.212 — Capability checks

Checks should be:

```text
O(1)
```

or bounded small complexity for common resource operations.

---

# 603.213 — Policy cache

Policy cache can use:

```text
resource fingerprint
capability generation
policy generation
```

---

# 603.214 — Cache invalidation

Any security policy change increments generation.

---

# 603.215 — Concurrency

Capability registry must be safe under concurrent access.

---

# 603.216 — Lock avoidance

Hot capability checks should not require global mutex.

---

# 603.217 — Immutable policy snapshots

Policy readers may use immutable snapshots with atomic publication.

---

# 603.218 — Security transaction

Policy reload:

```text
parse
validate
compile
publish atomically
```

---

# 603.219 — Invalid policy

Invalid policy must not partially replace active policy.

---

# 603.220 — Fail-safe reload

On policy reload failure:

```text
keep previous valid policy
```

---

# 603.221 — Capability revocation transaction

Revocation must atomically change validity generation.

---

# 603.222 — Race semantics

If operation starts before revocation and completes after it, exact semantics depend on resource type.

This must be documented per capability.

---

# 603.223 — File operation semantics

A file operation already holding an OS descriptor may continue if OS permits.

Future operations requiring new access must respect revocation.

---

# 603.224 — Network semantics

Existing connection may remain active after policy change unless explicit forced revocation exists.

---

# 603.225 — Process semantics

Existing child process is independent unless supervisor policy explicitly terminates it.

---

# 603.226 — Security event ordering

Security events use BOOTSTRAP-602 event sequence where available.

---

# 603.227 — Security event durability

Critical audit events can request durable sink.

---

# 603.228 — Audit failure

If mandatory audit fails, application policy decides:

```text
continue
degrade
terminate
```

Runtime security core must not silently claim event was recorded.

---

# 603.229 — Security status truthfulness

`audit.record()` must report whether durable persistence succeeded when durability is requested.

---

# 603.230 — Security API failures

Every security operation returns explicit failure when authority unavailable.

---

# 603.231 — No silent escalation

Runtime must never automatically request broader capability because a narrow capability failed.

---

# 603.232 — Capability request loop prevention

Application cannot recursively request same denied capability indefinitely through runtime.

---

# 603.233 — User prompt policy

Interactive permission prompt only occurs when deployment/platform explicitly permits prompting.

---

# 603.234 — Headless prompt

Headless server must return:

```text
requires_user
```

or deny according to policy.

Never block waiting for nonexistent UI.

---

# 603.235 — Security timeout

Permission operations may have bounded timeout.

---

# 603.236 — Capability availability

API:

```axiom
security.available(NetworkConnect)
```

returns platform/policy availability, not guaranteed future grant.

---

# 603.237 — Preflight

Application can preflight:

```axiom
security.check(capability, resource)
```

but must still handle operation-time denial.

---

# 603.238 — Check/use race

Preflight is advisory.

Actual resource operation performs authoritative check.

---

# 603.239 — Security boundary crossing

Every crossing:

```text
process
module
IPC
plugin
FFI
```

must define validation responsibility.

---

# 603.240 — IPC framing

IPC messages require:

```text
length
type
version
payload
integrity where needed
```

---

# 603.241 — IPC maximum message

Maximum message size must be bounded.

---

# 603.242 — IPC recursion

Security layer must avoid:

```text
policy decision
→ IPC
→ policy decision
→ IPC
```

deadlock/recursion.

---

# 603.243 — External authorization

Applications can integrate external auth systems, but core runtime only exposes identity/capability primitives.

---

# 603.244 — Authentication vs authorization

Authentication:

> Who is the peer?

Authorization:

> What may the peer do?

Axiom security runtime primarily enforces authorization.

---

# 603.245 — Identity spoofing

Peer identity comes from trusted platform/cryptographic source where possible.

Application-provided strings are not trusted identity.

---

# 603.246 — Security tokens

External bearer tokens remain application data unless converted by trusted authorization layer.

---

# 603.247 — Token logging

Tokens must be typed as secret.

---

# 603.248 — Capability API ergonomics

Common code should remain simple:

```axiom
let file = data_dir.open("a.txt")
```

where `data_dir` itself is a capability-bound directory object.

---

# 603.249 — Capability-bound resource objects

Preferred pattern:

```axiom
DirectoryCapability
FileCapability
NetworkCapability
```

rather than passing raw capability + string repeatedly.

---

# 603.250 — Capability-bound object invariant

A resource object must not outlive its underlying capability.

---

# 603.251 — Resource close

Closing resource invalidates its resource handle.

---

# 603.252 — Use-after-close

Returns deterministic runtime error.

---

# 603.253 — Capability drop

Dropping parent capability must not automatically invalidate already-open child resources unless policy says so.

---

# 603.254 — Explicit revocation

For strong revocation, use revocable capability group.

---

# 603.255 — Capability groups

Example:

```text
NetworkGroup
    Connect
    Resolve
```

Revoking group invalidates descendants.

---

# 603.256 — Group implementation

Could use shared generation object.

---

# 603.257 — No mandatory reference counting

Capability groups should not force heavyweight reference counting on all applications.

---

# 603.258 — Runtime memory model integration

Capability handles are ordinary value types with runtime-managed authority metadata.

---

# 603.259 — No raw pointer semantics

Capability API does not require developers to manipulate raw pointers.

---

# 603.260 — Security with flat memory

Even if Axiom adopts a flat/native memory model, security authority remains orthogonal.

Memory address does not imply capability.

---

# 603.261 — Address-space isolation

Process isolation remains the strong boundary against arbitrary native memory access.

---

# 603.262 — In-process safety limitation

No language-level capability can fully isolate arbitrary unsafe native code in the same process.

This must be explicitly documented.

---

# 603.263 — Safe code

Safe Axiom code cannot forge capability through language-defined operations.

---

# 603.264 — Unsafe code

Unsafe code may bypass language-level restrictions, but OS/process boundary remains authoritative.

---

# 603.265 — Trusted runtime code

Only explicitly trusted runtime modules may access raw platform authority.

---

# 603.266 — Trusted runtime marker

Runtime internals may use:

```text
@trusted
```

or compiler-internal equivalent.

---

# 603.267 — Trusted code review boundary

Trusted runtime must be kept small.

---

# 603.268 — TCB minimization

Security-critical implementation should reside in:

```text
runtime/security/core
runtime/platform/security
```

rather than broad standard library.

---

# 603.269 — Standard library

High-level convenience APIs are not trusted security authority.

---

# 603.270 — Security implementation dependencies

Security core must not depend on:

```text
GUI
network framework
database
logging framework
```

---

# 603.271 — Diagnostics dependency

Security may call BOOTSTRAP-602 emergency diagnostic primitives, but must not depend on normal asynchronous logging.

---

# 603.272 — Crash dependency

Crash subsystem may capture security state:

```text
policy generation
sandbox
profile
```

without exposing secrets.

---

# 603.273 — Config dependency

Security policy reads BOOTSTRAP-601 resolved config snapshot through stable interface.

---

# 603.274 — State dependency

Security state is not application state.

BOOTSTRAP-600 should not persist active capability tokens.

---

# 603.275 — Restart

After restart, capabilities are re-issued from trusted bootstrap policy.

---

# 603.276 — State restore security

Restored application state must not automatically restore privileged authority.

---

# 603.277 — Serialization rule

Never serialize live capability objects as application state.

---

# 603.278 — Capability references

Persist only stable resource identifiers if application semantics require it.

Reauthorization occurs after restore.

---

# 603.279 — State restore denial

If previously available resource is no longer authorized:

```text
restore succeeds
resource access returns SecurityError
```

rather than violating policy.

---

# 603.280 — Configuration fingerprint

Security diagnostics records BOOTSTRAP-601 config fingerprint.

---

# 603.281 — Policy fingerprint

Security subsystem separately computes:

```text
security_policy_fingerprint
```

---

# 603.282 — Fingerprint purpose

Fingerprints identify policy/config versions.

They are not secrets.

---

# 603.283 — Security reproducibility

Crash/diagnostic tooling can determine:

```text
binary
config
security policy
```

combination.

---

# 603.284 — Build-time policy

Compiler may enforce:

```text
forbidden capability
```

for restricted targets.

---

# 603.285 — Deployment validation

Deployment tool checks:

```text
application required capabilities
vs
deployment allowed capabilities
```

---

# 603.286 — CI security validation

CI can fail build if forbidden capability appears.

---

# 603.287 — Capability diff

Tool:

```text
axiom security diff old.axsec new.axsec
```

shows additions/removals.

---

# 603.288 — No security score

Tooling reports capability changes, not a generic security rating.

---

# 603.289 — Capability documentation generation

Compiler can generate:

```text
SECURITY-MANIFEST.md
```

or machine-readable equivalent.

---

# 603.290 — Human-readable manifest

Example:

```text
Application requires:
    filesystem.read: /data/app
    network.connect: api.example.com:443
```

---

# 603.291 — Machine manifest

Canonical machine schema should use stable IDs rather than prose.

---

# 603.292 — Manifest signing

Deployment manifest may be signed.

---

# 603.293 — Signature trust

Trusted key source is platform/deployment specific.

---

# 603.294 — Unsigned development builds

Development may allow unsigned modules.

Production policy can require signatures.

---

# 603.295 — Debug bypass

Debug mode must not silently disable security policy.

A deliberate debug capability may be granted.

---

# 603.296 — Debug capability

```text
DebugControl
```

explicitly grants additional inspection.

---

# 603.297 — Production prohibition

Production deployment can reject binaries requesting `DebugControl`.

---

# 603.298 — Test capabilities

Tests may receive special:

```text
TestControl
```

capabilities.

---

# 603.299 — Test-only metadata

Compiler should strip test-only capabilities from release builds.

---

# 603.300 — Security test harness

Required tests:

```text
forged capability
stale capability
wrong capability type
revocation race
path traversal
symlink escape
policy reload
IPC spoofing
plugin restriction
FFI boundary
secret leakage
```

---

# 603.301 — Fuzzing

Security parsers should be fuzzed:

```text
policy parser
manifest parser
capability metadata parser
IPC decoder
artifact decoder
```

---

# 603.302 — Property tests

Required properties:

```text
attenuation never increases authority
revocation eventually invalidates new operations
policy deny cannot become allow through cache
capability serialization cannot recreate authority
```

---

# 603.303 — Concurrency tests

Test:

```text
concurrent grant
concurrent revoke
policy reload
resource use
task spawn
```

---

# 603.304 — Race detection

Runtime implementation should be testable with race/thread sanitization where available.

---

# 603.305 — Failure injection

Inject:

```text
policy load failure
OS permission failure
handle duplication failure
sandbox query failure
memory allocation failure
```

---

# 603.306 — Security logging

Every security denial can optionally produce BOOTSTRAP-602 event.

---

# 603.307 — Security logging overhead

Disabled audit/security logging must remain cheap.

---

# 603.308 — Security emergency path

If security subsystem itself faults:

```text
deny privileged operation
```

and emit minimal diagnostic.

---

# 603.309 — Fail-closed invariant

For security decision uncertainty:

```text
unknown → deny
```

in hardened mode.

---

# 603.310 — Platform failure

If OS security API returns unexpected error:

```text
SecurityUnavailable
```

rather than treating it as granted.

---

# 603.311 — Compatibility exception

Legacy/native profile may expose direct OS errors where required.

---

# 603.312 — Error mapping

Platform errors map to:

```text
PermissionDenied
NotFound
NotSupported
Revoked
ResourceLimit
SecurityUnavailable
```

while preserving platform code.

---

# 603.313 — Error detail

Detailed platform code may be available to privileged diagnostics tooling.

---

# 603.314 — User-facing security errors

Messages should explain:

```text
operation
required authority
denial category
```

without exposing policy secrets.

---

# 603.315 — Security API example

```axiom
fn load_config(dir: DirectoryRead) -> Result<Config> {
    let file = dir.open("config.axcfg")
    return Config.parse(file)
}
```

The function cannot read outside the directory authority.

---

# 603.316 — Network API example

```axiom
fn fetch(api: NetworkConnect) -> Result<Response> {
    return api.connect("api.example.com", 443)
}
```

---

# 603.317 — Delegation example

```axiom
fn worker(parent: DirectoryRead) {
    let limited = parent.subdirectory("cache")
    spawn(task, with = limited)
}
```

---

# 603.318 — Attenuation invariant

`limited` must never read:

```text
parent scope
```

outside its subtree.

---

# 603.319 — Function requirements

Example:

```axiom
@requires(NetworkConnect)
fn download(...)
```

Compiler records requirement.

---

# 603.320 — Capability injection

Application entrypoint may receive:

```axiom
fn main(args, caps: AppCapabilities)
```

where `AppCapabilities` is generated from deployment manifest.

---

# 603.321 — Generated capability object

Compiler/toolchain may generate:

```text
AppCapabilities.files
AppCapabilities.network
AppCapabilities.process
```

only for requested capabilities.

---

# 603.322 — No unused authority

If application never requests:

```text
ProcessSpawn
```

generated `AppCapabilities.process` should not exist.

---

# 603.323 — Capability discoverability

Developer tooling can inspect generated capability set.

---

# 603.324 — Security boundary API

Minimal:

```axiom
security.check(...)
security.require(...)
security.request(...)
security.drop(...)
security.status(...)
```

---

# 603.325 — `require`

`require(capability)` must fail deterministically if absent.

---

# 603.326 — `check`

`check` is non-throwing/preflight.

---

# 603.327 — `request`

May interact with platform permission mechanism.

---

# 603.328 — `drop`

Irreversibly attenuates current context.

---

# 603.329 — Security scope

```axiom
security.scope(limited_caps) {
    ...
}
```

restores previous context after scope.

---

# 603.330 — Scope safety

Scope restoration must occur even if error/panic propagation occurs where runtime supports structured unwinding.

---

# 603.331 — Async scope

Capability scope must propagate according to explicit task semantics.

---

# 603.332 — Capability context inheritance

Default:

```text
child task receives parent's non-sensitive capabilities
```

Sensitive/high privilege capabilities require explicit delegation.

---

# 603.333 — High-risk capability class

High-risk capabilities:

```text
ProcessDebug
RawDevice
RawSocket
ExecutableMemory
SystemConfig
CredentialAccess
```

must not automatically propagate.

---

# 603.334 — Capability classification

Capabilities can have risk metadata:

```text
normal
sensitive
privileged
system
```

This is descriptive metadata, not a generic security score.

---

# 603.335 — Capability policy

High-risk capabilities require stronger deployment approval.

---

# 603.336 — Security UI

Runtime itself remains UI-neutral.

Platform shell may display permission prompts.

---

# 603.337 — User denial

User denial returns normal `SecurityError`.

No repeated prompt loop.

---

# 603.338 — Permission persistence

Persistence semantics delegated to OS/deployment.

---

# 603.339 — Mobile lifecycle

When application backgrounded/suspended, capabilities may become temporarily unusable.

Operations must handle OS denial.

---

# 603.340 — Capability status

Status can be:

```text
active
temporarily_unavailable
revoked
denied
```

---

# 603.341 — WASM host capability

Host provides explicit imports.

Axiom runtime cannot access host resources not imported.

---

# 603.342 — WASM sandbox invariant

WASM linear memory does not imply host filesystem/network authority.

---

# 603.343 — Native sandbox

Native sandbox policy must be queried at startup.

---

# 603.344 — Security bootstrap report

Startup diagnostics can record:

```text
security profile
sandbox type
policy fingerprint
granted capability count
```

---

# 603.345 — No capability value logging

Never output actual capability token internals.

---

# 603.346 — Capability leak prevention

Capability objects should not implement generic string serialization.

---

# 603.347 — Generic serialization restriction

Compiler rejects serialization of capability types unless explicit safe projection exists.

---

# 603.348 — Equality semantics

Capability equality means:

```text
same authority/resource identity
```

not token byte equality exposed to application.

---

# 603.349 — Hash semantics

Capability can be hashable only through stable opaque identity.

---

# 603.350 — Ordering

Capabilities do not have meaningful ordering.

---

# 603.351 — Capability type system

Each capability kind is distinct at compile time.

---

# 603.352 — Generic capability constraints

Functions may accept:

```axiom
fn read<T: ReadCapability>(cap: T)
```

if useful.

---

# 603.353 — Capability traits

Traits can describe:

```text
Readable
Writable
Connectable
Delegatable
Revocable
```

---

# 603.354 — Trait semantics

Capability trait does not grant authority.

It describes operations supported by an already-authorized capability.

---

# 603.355 — Struct-only integration

Capability objects are ordinary Axiom structs with runtime-managed opaque handles.

No class hierarchy required.

---

# 603.356 — Method integration

Methods:

```axiom
fn read(self: FileRead, ...)
```

follow Axiom struct-first method convention.

---

# 603.357 — Override integration

Platform-specific capability implementations can override behavior through trait/function dispatch without requiring classes.

---

# 603.358 — Dynamic dispatch

Security-critical dispatch must not rely on mutable user-controlled vtables.

---

# 603.359 — Static dispatch preference

Compile-time known capability operations should prefer static dispatch.

---

# 603.360 — Security metadata and generics

Generic functions must preserve capability requirements after monomorphization/specialization.

---

# 603.361 — Capability requirements in IR

Compiler IR includes:

```text
requires_capability
acquire_capability
attenuate_capability
release_capability
```

where needed.

---

# 603.362 — IR validation

IR verifier must reject invalid capability operations:

```text
forge
upgrade
use-after-drop
wrong-kind
```

---

# 603.363 — Linker security verification

Linker validates final capability metadata against object/module metadata.

---

# 603.364 — Loader verification

Native loader/runtime verifies signed/trusted module metadata before granting privileged capabilities where configured.

---

# 603.365 — Runtime module quarantine

Untrusted dynamic module may load into isolated process instead of same process.

---

# 603.366 — Security policy compiler output

Compact policy:

```text
.cap
```

or equivalent.

Exact extension remains implementation detail.

---

# 603.367 — Policy format version

Security policy format must be versioned independently from application config.

---

# 603.368 — Policy parser security

Parser must be:

```text
bounded
non-executable
deterministic
```

---

# 603.369 — No policy scripting

Core security policy must not execute arbitrary user scripts.

---

# 603.370 — Policy expressions

Keep policy language declarative:

```text
allow capability X
scope resource Y
deny operation Z
```

---

# 603.371 — No arbitrary code in policy

Policy evaluation cannot call application functions.

---

# 603.372 — Policy complexity

Avoid general-purpose rule engines in runtime.

---

# 603.373 — Fast path

Common decision:

```text
capability handle valid
+
resource within scope
+
operation allowed
```

→ direct allow.

---

# 603.374 — Slow path

Only complex cases use policy engine.

---

# 603.375 — Security startup cost

Startup policy compilation should be O(policy size).

---

# 603.376 — Runtime check complexity

Common resource checks should be O(1) or bounded.

---

# 603.377 — Memory footprint

Security runtime should use:

```text
immutable policy snapshot
capability table
small generation state
```

rather than heavyweight object graphs.

---

# 603.378 — No GC dependency

Security subsystem must not require garbage collection.

---

# 603.379 — Memory safety

Capability implementation must obey Axiom memory model and cannot depend on GC or borrow checker.

---

# 603.380 — Handle safety

Generation/index validation provides use-after-free protection for runtime-managed capability handles.

---

# 603.381 — Integer overflow

Capability/resource calculations must use checked arithmetic where overflow can affect security.

---

# 603.382 — Canonical resource IDs

Resources should use canonical identifiers to avoid alternate-path authorization bypasses.

---

# 603.383 — File case sensitivity

Path security adapter must respect platform case semantics.

---

# 603.384 — Unicode normalization

Filesystem/network identifiers requiring canonicalization must define Unicode normalization policy per platform.

---

# 603.385 — Homograph handling

Security policy should avoid relying on human-readable names as identity.

---

# 603.386 — DNS security

Network authorization should account for DNS resolution changes if policy is hostname-based.

---

# 603.387 — Hostname capability semantics

If capability says:

```text
api.example.com
```

implementation must define whether authority follows:

```text
hostname
resolved IP
both
```

---

# 603.388 — TLS

TLS authentication belongs to network/security libraries, while capability controls network authority.

---

# 603.389 — Certificate authority

Certificate trust configuration is separate from capability grant.

---

# 603.390 — Network identity distinction

```text
NetworkConnect
```

does not imply:

```text
trusted server
```

---

# 603.391 — File identity distinction

```text
FileRead
```

does not imply:

```text
file contents are trusted
```

---

# 603.392 — Device identity distinction

```text
DeviceAccess
```

does not imply device data is safe.

---

# 603.393 — Trust boundary input validation

Capability grants access; parser validation still required.

---

# 603.394 — Security architecture invariant

```text
authority != trustworthiness of data
```

---

# 603.395 — Security and diagnostics

BOOTSTRAP-602 records security decisions.

BOOTSTRAP-603 decides authorization.

---

# 603.396 — Security and config

BOOTSTRAP-601 provides policy inputs.

BOOTSTRAP-603 validates/executes them.

---

# 603.397 — Security and state

BOOTSTRAP-600 persists application state, never live privilege state.

---

# 603.398 — Security and compiler

Compiler proves/records declared authority requirements.

Runtime enforces actual authority.

---

# 603.399 — Security and OS

OS remains final authority for kernel-protected resources.

Axiom cannot grant more than OS allows.

---

# 603.400 — Security core invariant

The complete authority chain is:

```text
OS authority
    ↓
deployment policy
    ↓
Axiom security policy
    ↓
capability
    ↓
operation
```

A lower layer cannot increase authority beyond the upper boundary.

---

# 603.401 — Required implementation phases

### Phase 1 — Capability primitives

```text
Capability<T>
generation
opaque handle
attenuation
drop
```

### Phase 2 — Filesystem/network

```text
FileRead
FileWrite
NetworkConnect
NetworkListen
```

### Phase 3 — Process/IPC

```text
ProcessSpawn
ProcessDebug
IPC
SharedMemory
```

### Phase 4 — Compiler integration

```text
@requires
capability metadata
IR validation
linker merge
```

### Phase 5 — Platform integration

```text
Windows
Linux
macOS
iOS
Android
WASM
```

### Phase 6 — Sandboxing/trust

```text
plugin isolation
module trust
signature verification
policy enforcement
```

### Phase 7 — Advanced security

```text
revocation
quotas
audit
policy reload
security tooling
```

---

# 603.402 — Required tests

At minimum:

```text
capability forgery
wrong capability type
stale handle
revoked handle
attenuation escape
path traversal
symlink escape
network scope violation
process privilege violation
IPC unauthorized request
plugin overreach
FFI boundary
policy reload
policy corruption
secret leakage
concurrent revoke/use
```

---

# 603.403 — Cross-platform acceptance

Required targets:

```text
Windows x64
Linux x64
Linux ARM64
macOS ARM64
iOS ARM64
Android ARM64
WASM
```

Unsupported platform capability must return:

```text
NotSupported
```

not silently grant access.

---

# 603.404 — Performance acceptance

Common authorized operation must not require:

```text
string permission lookup
global mutex
dynamic policy parsing
```

on every call.

---

# 603.405 — Binary-size acceptance

Applications that do not use advanced security capabilities should not pull:

```text
policy compiler
plugin verifier
signature subsystem
advanced audit
```

into the final binary unnecessarily.

---

# 603.406 — Security acceptance

Must prove:

```text
no capability forgery
no authority escalation through attenuation
no stale capability reuse
no policy-cache bypass
no partial policy reload
no secret serialization
no silent fail-open
```

---

# 603.407 — Developer experience acceptance

Simple application:

```axiom
fn main(caps: AppCapabilities) {
    let file = caps.data.read("hello.txt")
    print(file)
}
```

should not require developers to understand the complete security engine.

---

# 603.408 — Advanced developer experience

Security-sensitive server:

```axiom
fn run(caps: ServerCapabilities) {
    let listener = caps.network.listen(443)

    spawn(worker, with = [
        caps.data.read_only()
    ])
}
```

should make authority explicit and easy to audit.

---

# 603.409 — Final architectural principle

Axiom security should follow:

> **Explicit authority, least privilege, monotonic attenuation, fail-closed enforcement, platform-native isolation, and negligible overhead when unused.**

---

# 603.410 — BOOTSTRAP-603 completion invariant

BOOTSTRAP-603 is complete at architecture level when:

```text
capability model
+
permission model
+
policy engine
+
resource scoping
+
privilege separation
+
sandbox integration
+
IPC security
+
module/plugin trust
+
secret integration
+
compiler metadata
+
IR enforcement
+
linker validation
+
runtime enforcement
+
OS adapters
+
audit integration
+
revocation
+
resource limits
+
security testing
```

đã được định nghĩa đủ để triển khai compiler/runtime mà không cần thiết kế lại security foundation.

---

## Task completion

**BOOTSTRAP-603 — Native Application Security Boundary, Capability System, Permissions & Trusted Runtime 5.0** hoàn tất ở cấp architecture/specification.

**Next task: BOOTSTRAP-604 — Native Application IPC, Inter-Process Communication, Shared Memory & Message Transport Runtime 5.0**

:::