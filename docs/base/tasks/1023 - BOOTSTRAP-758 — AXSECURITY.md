# BOOTSTRAP-758 — AXSECURITY

**Title:** Native Security Enforcement, Access Control, Sandbox, Capability Enforcement, Security Context & Mandatory Security Runtime 5.0  
**Namespace:** `AXSECURITY`  
**Phase:** Axiom Civilization Runtime / Native Security Enforcement Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

# 1. Mục tiêu

`AXSECURITY` là **enforcement plane** của Axiom.

Các tầng trước quyết định những thành phần khác nhau:

```text
AXIDENTITY
    │
    │ Who?
    ▼
AXAUTH
    │
    │ Authenticated?
    ▼
AXTRUST
    │
    │ Trusted under which evidence/policy?
    ▼
AXCAPABILITY
    │
    │ What authority exists?
    ▼
AXPOLICY
    │
    │ Does this request satisfy policy?
    ▼
AXSECURITY
    │
    │ Enforce
    ▼
RESOURCE
```

`AXSECURITY` là nơi cuối cùng trước resource boundary.

Nó phải đảm bảo:

> Một operation không được thực hiện chỉ vì caller tuyên bố rằng operation đó được phép.

---

# 2. Security architecture

```text
                    AXIDENTITY
                         │
                         ▼
                      AXAUTH
                         │
                         ▼
                      AXTRUST
                         │
                         ▼
                   AXCAPABILITY
                         │
                         ▼
                     AXPOLICY
                         │
                         ▼
                  ┌──────────────┐
                  │ AXSECURITY   │
                  │              │
                  │ enforcement  │
                  │ sandbox      │
                  │ domains      │
                  │ contexts     │
                  │ isolation    │
                  │ audit        │
                  └──────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      AXPROCESS       AXMEMORY       AXIPC
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                  protected resource
```

---

# 3. Strong boundary

## AXSECURITY sở hữu

- security context;
- enforcement boundary;
- access checks;
- capability enforcement;
- policy enforcement integration;
- security domains;
- sandbox profiles;
- process security identity;
- resource protection metadata;
- security labels;
- mandatory restrictions;
- privilege boundaries;
- security transitions;
- syscall/operation interception;
- protected object access;
- security event boundary;
- security audit hooks;
- security failure handling;
- security simulation.

## Không sở hữu

### AXAUTH

Authentication.

### AXTRUST

Trust evaluation.

### AXCAPABILITY

Capability issuance/delegation.

### AXPOLICY

Policy language/evaluation.

### AXIDENTITY

Identity lifecycle.

### AXPROCESS

Process/thread implementation.

### AXMEMORY

Memory implementation.

### AXIPC

IPC transport.

---

# 4. Fundamental invariant

Không có đường tắt:

```text
authenticated
    ≠
authorized
    ≠
enforced
```

Và:

```text
capability
    ≠
automatic access
```

Capability phải đi qua enforcement boundary phù hợp.

---

# 5. Security context

Core model:

```text
security_context {
    context_id
    principal
    session
    security_domain
    capabilities
    authentication_assurance
    trust_state
    policy_snapshot
    process
    tenant
    labels
}
```

Context là snapshot cho một enforcement decision.

---

# 6. Security domain

```text
security_domain {
    domain_id
    parent_domain
    policy_ref
    isolation_profile
    capability_namespace
    resource_namespace
}
```

Security domain tạo boundary giữa các authority spaces.

---

# 7. Domain hierarchy

```text
SYSTEM
 ├── USER
 │    ├── APPLICATION_A
 │    └── APPLICATION_B
 │
 └── SERVICE
      ├── SERVICE_X
      └── SERVICE_Y
```

Child domain không tự động có toàn bộ authority của parent.

---

# 8. Domain transition

Transition:

```text
domain_A
   ↓
domain_B
```

phải explicit.

Có thể yêu cầu:

```text
capability
+
policy
+
security transition rule
```

---

# 9. Privilege boundary

Security boundary phải xác định rõ:

```text
unprivileged
       ↓
privileged
```

Không được có implicit privilege escalation thông qua:

- FFI;
- handle conversion;
- IPC;
- environment variable;
- shared memory;
- dynamic loading.

---

# 10. Security label

Resource có thể mang:

```text
security_label {
    classification
    categories[]
    domain
}
```

Ví dụ:

```text
classification = INTERNAL
categories = {FINANCE}
```

AXSECURITY dùng label như enforcement input.

---

# 11. Mandatory security controls

Một operation có thể bị chặn bởi:

```text
capability
policy
sandbox
resource label
domain boundary
system security state
```

Final allow chỉ xảy ra khi **mọi mandatory control** đều pass.

---

# 12. Security decision composition

Conceptual:

```text
final_allow =
    authenticated
    AND capability_valid
    AND policy_allow
    AND sandbox_allow
    AND domain_allow
    AND resource_state_allow
```

Một lớp mandatory deny là đủ để reject.

---

# 13. Enforcement request

```text
security_request {
    context
    operation
    resource
    arguments_metadata
    flags
    deadline
}
```

Không đưa raw secret vào request nếu không cần.

---

# 14. Enforcement result

```text
security_result {
    decision
    reason
    policy_version
    security_domain
    obligations
    audit_event_ref
}
```

Decision:

```text
ALLOW
DENY
REQUIRE_REAUTH
REQUIRE_CAPABILITY
REQUIRE_SANDBOX
INDETERMINATE
```

---

# 15. Enforcement point

Mỗi protected subsystem phải có enforcement point:

```text
AXSTORAGE → file enforcement
AXNETWORK → socket/network enforcement
AXPROCESS → process enforcement
AXMEMORY → memory protection enforcement
AXIPC → endpoint enforcement
AXWINDOW → window/security enforcement
AXDEVICE → device enforcement
```

Không được chỉ có một security check ở application API layer.

---

# 16. Defense in depth

Ví dụ file:

```text
Application API
      ↓
AXSECURITY
      ↓
AXSTORAGE security boundary
      ↓
native filesystem
```

Nếu application bypass được wrapper, lower-level boundary vẫn phải bảo vệ resource.

---

# 17. Kernel/native boundary

Axiom native runtime có thể có:

```text
user-mode AXSECURITY
          ↓
native security boundary
          ↓
kernel / privileged runtime
```

Những tài nguyên đặc biệt phải được enforce ở privileged boundary.

---

# 18. Security syscall

Conceptual:

```text
security_check(handle, operation)
```

nhưng hot paths nên tránh syscall nếu capability/security context đã đủ local và immutable.

---

# 19. Fast-path authorization

Common case:

```text
security context
       ↓
capability handle
       ↓
rights mask
       ↓
resource generation
       ↓
policy cache
       ↓
ALLOW
```

Nếu tất cả invariant còn hợp lệ:

```text
no expensive security operation
```

---

# 20. Slow path

Slow path khi:

- capability expired;
- revocation epoch changed;
- policy changed;
- security domain changed;
- resource state changed;
- authentication assurance expired;
- external trust changed.

Flow:

```text
fast check
   ↓
mismatch
   ↓
slow validation
   ↓
new security snapshot
   ↓
retry operation
```

---

# 21. Security context cache

Cache key:

```text
security_context_key {
    principal
    session_epoch
    capability_epoch
    policy_version
    security_domain
}
```

---

# 22. Context immutability

Một security context đang được dùng không được mutate giữa check và enforcement.

Nếu state thay đổi:

```text
new context
```

được tạo.

---

# 23. TOCTOU protection

Không:

```text
check(resource)
   ↓
resource changes
   ↓
use(resource)
```

nếu resource security state có thể thay đổi.

Sử dụng:

```text
generation
epoch
atomic operation
```

hoặc privileged revalidation.

---

# 24. Resource generation

Protected object có:

```text
security_generation
```

Authorization result có thể bind vào generation.

Nếu:

```text
decision.generation != resource.generation
```

→ re-evaluate.

---

# 25. Capability enforcement

AXSECURITY gọi:

```text
capability_check()
```

từ AXCAPABILITY.

Nó không tự fabricate capability.

---

# 26. Policy enforcement

AXSECURITY gọi:

```text
policy_evaluate()
```

từ AXPOLICY.

Không tự parse policy source.

---

# 27. Authentication enforcement

AXSECURITY kiểm tra:

```text
session authenticated?
session valid?
assurance sufficient?
```

Nguồn session state là AXAUTH.

---

# 28. Reauthentication

Nếu policy yêu cầu:

```text
REQUIRE_REAUTH
```

AXSECURITY trả về structured result:

```text
REAUTH_REQUIRED
```

Application có thể gọi AXAUTH.

AXSECURITY không giả lập successful authentication.

---

# 29. Capability request

Nếu thiếu capability:

```text
REQUIRE_CAPABILITY
```

Không có API:

```text
security.auto_grant(...)
```

Capability phải được cấp bởi authorized authority.

---

# 30. Sandbox

Sandbox profile:

```text
sandbox_profile {
    profile_id
    allowed_syscalls
    allowed_resources
    allowed_domains
    network_policy
    filesystem_policy
    process_policy
    device_policy
    memory_policy
}
```

---

# 31. Sandbox principle

Sandbox là **maximum authority boundary**.

Capability/policy chỉ có thể giảm thêm authority.

```text
sandbox
   ∩
capability
   ∩
policy
```

là effective authority.

---

# 32. Sandbox cannot amplify

Nếu sandbox cấm:

```text
NETWORK.CONNECT
```

thì capability:

```text
NETWORK.CONNECT
```

không thể override sandbox.

---

# 33. Sandbox inheritance

Process child có thể inherit sandbox:

```text
parent sandbox
       ↓
child sandbox
```

Child có thể bị:

```text
same
stricter
```

Không được tự nâng thành broader sandbox.

---

# 34. Sandbox profiles

Baseline:

```text
MINIMAL
STANDARD
SERVER
DESKTOP
PLUGIN
UNTRUSTED
DEVICE
SYSTEM
CUSTOM
```

Profiles là templates, không phải security guarantees tự thân.

---

# 35. Syscall filtering

AXSECURITY có thể giới hạn native operations:

```text
PROCESS.SPAWN
MEMORY.MAP_EXECUTE
NETWORK.CONNECT
DEVICE.OPEN
```

Mỗi operation có security class.

---

# 36. Executable memory

Đặc biệt:

```text
MEMORY.EXECUTE
```

phải chịu:

- W^X;
- sandbox;
- capability;
- policy.

JIT runtime phải sử dụng explicit security transition.

---

# 37. Dynamic code loading

Loading executable code:

```text
module.load()
```

có thể yêu cầu:

```text
MODULE.LOAD
+
trusted code policy
+
sandbox compatibility
```

Unsigned/untrusted module không tự động được elevated authority.

---

# 38. Device access

Device:

```text
GPU
CAMERA
MICROPHONE
USB
PCI
```

phải có capability/resource policy.

AXSECURITY enforcement:

```text
device capability
+
sandbox
+
policy
```

---

# 39. Network security

AXNETWORK owns transport.

AXSECURITY owns:

```text
CONNECT authorization
BIND authorization
LISTEN authorization
PORT access
network zone restrictions
```

Không reimplement TCP/IP.

---

# 40. IPC security

AXIPC owns transport.

AXSECURITY kiểm soát:

```text
endpoint access
message authority
capability transfer
service access
domain crossing
```

---

# 41. IPC capability transfer

Flow:

```text
Process A
   │
   │ capability
   ▼
AXIPC
   │
   ▼
AXSECURITY
   │
   ├── transfer allowed?
   ├── attenuation valid?
   └── receiver domain allowed?
   │
   ▼
Process B
```

---

# 42. Process creation

Operation:

```text
PROCESS.SPAWN
```

có thể yêu cầu:

```text
PROCESS.SPAWN capability
+
policy
+
sandbox profile
```

Child security context phải được constructed explicitly.

---

# 43. Child authority

Child không mặc định inherit toàn bộ parent authority.

Default:

```text
child_authority <= parent_authority
```

có thể là strict subset.

---

# 44. Environment sanitization

Security-sensitive process creation phải kiểm soát:

- environment;
- inherited handles;
- inherited capabilities;
- working directory;
- executable;
- dynamic library search path.

Không để environment variable trở thành privilege escalation vector.

---

# 45. Handle inheritance

Parent có handle:

```text
WRITE file
```

child chỉ nhận:

```text
READ
```

nếu policy yêu cầu attenuation.

---

# 46. Shared memory

Shared memory phải có:

```text
owner
participants
rights
security_domain
lifetime
```

Mapping shared memory không tự động cấp quyền đọc/ghi resource backing.

---

# 47. Memory protection

AXSECURITY phối hợp AXMEMORY:

```text
READ
WRITE
EXECUTE
```

Security policy có thể giới hạn:

```text
MAP_EXECUTE
MAP_SHARED
PIN_MEMORY
DMA
```

---

# 48. DMA

DMA-capable memory là privileged resource.

Yêu cầu:

```text
device capability
+
memory capability
+
IOMMU/security policy
```

nếu platform hỗ trợ.

---

# 49. Security domain crossing

Cross-domain operation:

```text
Domain A → Domain B
```

phải có explicit trust/authority bridge.

Không tự động tin object từ domain khác.

---

# 50. Cross-domain object

Một object có thể expose:

```text
public interface
```

thay vì toàn bộ underlying authority.

Đây là nguyên tắc least authority.

---

# 51. Object security descriptor

```text
security_descriptor {
    owner
    security_domain
    label
    policy_ref
    capability_epoch
    generation
}
```

---

# 52. Owner

Owner có thể có administrative relationship, nhưng:

```text
owner ≠ unlimited authority
```

nếu mandatory security policy cấm operation.

---

# 53. Security inheritance

Resource creation có thể inherit:

```text
security_domain
label
policy
```

từ parent.

Inheritance phải được snapshot tại creation.

---

# 54. Explicit security transition

Ví dụ process sandbox:

```text
spawn()
  ↓
security_transition
  ↓
child context
```

Transition object:

```text
security_transition {
    source_domain
    target_domain
    restrictions
    required_authority
}
```

---

# 55. Security profile

```text
security_profile {
    profile_id
    sandbox
    mandatory_rules
    resource_limits
    isolation
    audit_level
}
```

Profile phải versioned.

---

# 56. Profile activation

```text
load
 ↓
validate
 ↓
compile
 ↓
test
 ↓
activate
```

Giống policy activation.

---

# 57. Mandatory rules

Một security profile có thể đặt:

```text
mandatory_deny
mandatory_authentication
mandatory_encryption
mandatory_audit
mandatory_sandbox
```

AXPOLICY không được override mandatory controls.

---

# 58. Security labels

Labels có thể hỗ trợ:

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
SYSTEM
```

Đây là descriptive security metadata.

Semantics cụ thể do policy/profile định nghĩa.

---

# 59. Label flow

Data/resource labels có thể có flow constraints:

```text
source label
      ↓
operation
      ↓
destination label
```

Ví dụ policy có thể cấm chuyển dữ liệu từ restricted resource sang public destination.

---

# 60. Data-flow enforcement

AXSECURITY có thể expose:

```text
security_check_flow(source, destination, operation)
```

để subsystem gọi trước data transfer.

---

# 61. Export control

Resource có thể yêu cầu:

```text
EXPORT
```

capability riêng.

Policy có thể kiểm tra:

```text
destination
purpose
tenant
classification
```

---

# 62. Security obligations

AXPOLICY có thể yêu cầu:

```text
REQUIRE_AUDIT
REQUIRE_ENCRYPTION
REQUIRE_REAUTH
REQUIRE_SECURE_CHANNEL
```

AXSECURITY phải enforce trước operation.

---

# 63. Obligation transaction

Nếu operation yêu cầu audit:

```text
authorization
 ↓
audit preparation
 ↓
operation
```

Nếu audit bắt buộc nhưng audit sink unavailable:

```text
DENY
```

nếu policy/profile yêu cầu fail-closed.

---

# 64. Protected operations

Mọi native privileged operation phải có security classification:

```text
operation_metadata {
    operation_id
    resource_type
    required_rights
    security_class
}
```

---

# 65. Security classes

Ví dụ:

```text
NORMAL
SENSITIVE
PRIVILEGED
SYSTEM
CRITICAL
```

Class chỉ là dispatch metadata, không phải automatic security ranking.

---

# 66. Privileged operations

Ví dụ:

```text
PROCESS.DEBUG
PROCESS.TERMINATE_OTHER
MEMORY.MAP_EXECUTE
DEVICE.CONTROL
SECURITY.MODIFY_POLICY
SECURITY.GRANT_CAPABILITY
```

cần privileged authority.

---

# 67. Debug access

Debugging another process:

```text
PROCESS.DEBUG
```

không được cấp chỉ vì caller là local process.

Cần explicit authority.

---

# 68. Security administration

Policy/capability/security-profile modification là control-plane operations.

Ví dụ:

```text
SECURITY.POLICY.ACTIVATE
SECURITY.CAPABILITY.REVOKE
SECURITY.DOMAIN.MODIFY
```

phải có administrative authority.

---

# 69. Self-administration

Process không được tự cấp:

```text
SECURITY.ADMIN
```

bằng cách sửa security context của chính nó.

---

# 70. Security context construction

Context creation:

```text
identity
 +
authentication
 +
capabilities
 +
domain
 +
sandbox
 +
policy
```

phải qua trusted security path.

---

# 71. Context serialization

Không serialize security context như ordinary struct rồi import vào process khác.

Remote context phải được reconstructed từ authenticated evidence.

---

# 72. Security token

AXSECURITY có thể tạo short-lived:

```text
enforcement_token
```

nhưng token không thay thế capability.

Nó chỉ đại diện cho một verified security decision trong bounded context.

---

# 73. Decision binding

Enforcement token phải bind:

```text
principal
session
capability_epoch
policy_version
resource
operation
resource_generation
expiry
```

---

# 74. No stale decision

Nếu:

```text
policy_version changed
```

token cũ có thể invalid.

Tương tự:

```text
resource_generation changed
capability_epoch changed
session revoked
```

---

# 75. Revocation

AXSECURITY phải có integration với:

```text
AXAUTH session revocation
AXCAPABILITY revocation
AXPOLICY changes
AXTRUST changes
```

nhưng không sở hữu source-of-truth của từng hệ thống.

---

# 76. Emergency revocation

Security administrator có thể:

```text
revoke_session
revoke_capability
disable_domain
quarantine_process
```

Emergency actions phải được audit.

---

# 77. Quarantine

Process/domain có thể chuyển:

```text
ACTIVE
 ↓
QUARANTINED
```

Trong quarantine:

- network có thể bị restricted;
- IPC có thể bị restricted;
- resource writes có thể bị blocked;
- process vẫn có thể được giữ để diagnostics.

Exact restrictions do security profile.

---

# 78. Quarantine không phải kill

AXSECURITY không tự kill process chỉ vì quarantine.

Termination thuộc AXPROCESS/AXAPPLICATION theo authorized request.

---

# 79. Security events

Baseline:

```text
SECURITY_CHECK
SECURITY_ALLOW
SECURITY_DENY
CAPABILITY_REJECTED
POLICY_REJECTED
SANDBOX_REJECTED
DOMAIN_CROSSING
PRIVILEGE_TRANSITION
SESSION_REVOKED
CAPABILITY_REVOKED
PROCESS_QUARANTINED
```

---

# 80. Audit minimization

Không audit toàn bộ request payload mặc định.

Audit record:

```text
event_id
timestamp
principal_id
session_id
resource_id
operation
decision
reason_code
policy_version
domain_id
```

Sensitive payload phải explicit opt-in.

---

# 81. Tamper resistance

Security audit có thể dùng:

```text
append-only
hash chaining
signed checkpoints
```

AXCRYPTO cung cấp primitives.

Persistent audit backend thuộc dedicated audit/storage subsystem.

---

# 82. Failure semantics

Security subsystem failure trên critical operation:

```text
INDETERMINATE
```

Policy/profile quyết định:

```text
FAIL_CLOSED
```

hoặc explicit domain-specific fallback.

Không mặc định fail-open.

---

# 83. Fail-safe

Nếu security metadata không thể xác minh:

```text
deny protected operation
```

đối với security-critical paths.

---

# 84. Availability exception

Một số non-security-critical resources có thể có explicit degraded mode.

Ví dụ:

```text
read-only public resource
```

Nhưng degraded behavior phải được policy xác định trước.

---

# 85. Async security

Most security checks nên synchronous và cực nhanh.

Nếu cần external state:

```text
security_check_async()
```

có thể sử dụng:

```text
AXTASK
AXASYNC
```

Không block security worker.

---

# 86. Security check fusion

Compiler/runtime có thể fuse:

```text
capability check
+
policy check
+
sandbox check
```

thành một optimized security path.

---

# 87. Static security specialization

Nếu compiler biết:

```text
cap<File, READ>
```

và operation là:

```text
FILE.READ
```

có thể generate specialized check.

Runtime vẫn phải enforce dynamic constraints.

---

# 88. Security ABI

```text id="axsecurity"
AXSECURITY_ABI_1
```

gồm:

```text
security_context_handle
security_request
security_result
security_descriptor
security_domain_handle
sandbox_handle
```

---

# 89. Native API

Baseline:

```text
security_context_create()
security_context_get()
security_context_validate()

security_check()
security_check_async()
security_enforce()

security_get_descriptor()
security_set_descriptor()

security_domain_create()
security_domain_get()
security_domain_transition()
security_domain_suspend()
security_domain_resume()

sandbox_create()
sandbox_load_profile()
sandbox_activate()
sandbox_validate()

security_label_get()
security_label_set()

security_quarantine_process()
security_release_quarantine()

security_revoke_session()
security_revoke_capability()

security_policy_check()

security_start_audit()
security_stop_audit()

security_start_trace()
security_stop_trace()

security_simulate()
security_replay()

security_get_stats()
security_get_capabilities()
```

---

# 90. Compiler-facing primitives

```text
security_require()
security_require_capability()
security_require_authentication()
security_require_assurance()
security_enter_domain()
security_restrict()
```

Ví dụ:

```text
fn read_secret(cap: cap<File, READ>) {
    security_require(cap)
    ...
}
```

Compiler có thể preserve capability type information.

---

# 91. Resource integration ABI

Mỗi protected subsystem nên expose:

```text
resource_security_check(
    security_context,
    operation,
    resource
)
```

Nhưng implementation được specialize theo subsystem.

---

# 92. Canonical file flow

```text
application
    │
    ▼
AXSTORAGE
    │
    ▼
AXSECURITY enforcement point
    │
    ├── session valid?
    ├── sandbox allows?
    ├── capability allows?
    ├── policy allows?
    ├── resource generation valid?
    └── obligations satisfied?
    │
    ▼
ALLOW
    │
    ▼
filesystem operation
```

---

# 93. Canonical process spawn

```text
caller
  │
  ▼
AXSECURITY
  │
  ├── PROCESS.SPAWN capability
  ├── policy
  ├── sandbox profile
  └── child security context
  │
  ▼
AXPROCESS
  │
  ▼
child
```

---

# 94. Canonical IPC

```text
sender
  │
  ▼
AXIPC
  │
  ▼
AXSECURITY
  │
  ├── endpoint access
  ├── capability transfer
  ├── attenuation
  └── domain boundary
  │
  ▼
receiver
```

---

# 95. Canonical device access

```text
application
    ↓
device capability
    ↓
AXPOLICY
    ↓
AXSECURITY
    ├── sandbox
    ├── device restrictions
    ├── authentication assurance
    └── domain
    ↓
AXDEVICE
```

---

# 96. Canonical quarantine

```text
security event
      ↓
authorized security action
      ↓
AXSECURITY
      ↓
QUARANTINED
      ├── restrict network
      ├── restrict IPC
      ├── restrict writes
      └── preserve diagnostics
```

---

# 97. Deterministic simulation

Security simulation phải mô phỏng:

- capability changes;
- policy versions;
- resource generations;
- session expiration;
- sandbox transitions;
- domain transitions;
- revocation;
- race conditions;
- failed security providers.

---

# 98. Race simulation

Đặc biệt test:

```text
authorization success
        vs
capability revoke
```

```text
policy decision
        vs
policy activation
```

```text
session validation
        vs
session revoke
```

```text
resource check
        vs
resource generation change
```

---

# 99. Security replay

Replay phải dùng recorded metadata:

```text
request
context snapshot
policy version
capability epoch
resource generation
decision
```

Không cần lưu secrets.

---

# 100. AI boundary

AI có thể:

- phân tích security events;
- giải thích DENY;
- tìm authority escalation path;
- phát hiện sandbox gaps;
- phân tích capability graph;
- mô phỏng security policy;
- đề xuất least-authority reductions.

AI không được:

- tự grant privilege;
- bypass sandbox;
- disable mandatory policy;
- suppress security audit;
- forge security context;
- resurrect revoked session/capability;
- tự activate security profile.

---

# 101. Performance architecture

Security phải **không biến mọi operation thành expensive policy interpreter call**.

Kiến trúc:

```text
                    request
                       │
                       ▼
                 ┌───────────┐
                 │ FAST PATH │
                 └─────┬─────┘
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
          handle     rights    epochs
             │         │         │
             └─────────┼─────────┘
                       ▼
                   ALLOW
                       │
                    operation

                       │
                 mismatch/failure
                       ▼
                 ┌───────────┐
                 │ SLOW PATH │
                 └───────────┘
                       │
               full evaluation
```

---

# 102. Fast-path requirements

Không allocation.

Không network.

Không dynamic policy parsing.

Không global lock.

Không cryptographic operation trừ khi explicit proof/token validation yêu cầu.

---

# 103. Security cache locality

Security context có thể được giữ trong:

- thread-local execution context;
- process-local immutable structure;
- per-core cache.

Nhưng cache không được trở thành authority source độc lập.

---

# 104. NUMA

Large servers:

```text
per-NUMA security cache
per-domain immutable policy snapshot
sharded capability tables
```

giảm cross-node traffic.

---

# 105. Locking

Read path:

```text
lock-free / RCU-like
```

khi phù hợp.

Mutation:

```text
sharded locks
atomic epochs
copy-on-write snapshots
```

---

# 106. No hidden security allocations

A normal:

```text
FILE.READ
```

không nên tạo heap object cho:

```text
policy result
capability check
security context
```

nếu fast path có thể dùng stack/register values.

---

# 107. Security compiler optimization

Compiler có thể:

- inline capability checks;
- specialize rights;
- constant-fold static sandbox restrictions;
- eliminate redundant checks;
- hoist immutable checks;
- fuse security predicates.

Nhưng compiler **không được eliminate check** nếu dependency có thể thay đổi.

---

# 108. Security check elimination

Ví dụ:

```text
same immutable capability
same resource generation
same policy snapshot
same operation
```

→ một check có thể cover một bounded sequence.

Compiler/runtime phải prove điều kiện này.

---

# 109. No security check hoisting across mutation

Không được:

```text
check WRITE
   ↓
resource authority changes
   ↓
write
```

với check cũ.

---

# 110. Definition of Done

`AXSECURITY 5.0` hoàn tất khi có:

- security context;
- security domains;
- domain hierarchy;
- domain transitions;
- resource security descriptors;
- security labels;
- mandatory controls;
- authorization enforcement;
- capability enforcement;
- policy enforcement;
- authentication-session validation;
- sandbox;
- sandbox profiles;
- syscall restrictions;
- process security;
- child security context;
- handle inheritance controls;
- IPC security;
- capability transfer enforcement;
- shared-memory security;
- memory protection integration;
- executable-memory restrictions;
- device security;
- network security boundary;
- cross-domain security;
- data-flow controls;
- export controls;
- security obligations;
- enforcement tokens;
- generation/epoch protection;
- TOCTOU protection;
- revocation integration;
- quarantine;
- emergency security actions;
- audit hooks;
- tamper-resistant audit integration;
- fail-closed security profiles;
- async external-security checks;
- fast path;
- slow path;
- security caching;
- NUMA optimization;
- compiler integration;
- native security ABI;
- deterministic simulation;
- security replay;
- fault/race injection;
- AI security boundary;
- 40 invariants.

**AXSECURITY 5.0 → FROZEN.**

---

# 111. Security stack sau BOOTSTRAP-758

Axiom hiện có một security architecture khá hoàn chỉnh:

```text
┌──────────────────────────────────────────────┐
│                 AXSECURITY                   │
│              ENFORCEMENT PLANE               │
│                                              │
│ sandbox / isolation / access enforcement     │
└──────────────────────▲───────────────────────┘
                       │
┌──────────────────────┴───────────────────────┐
│                  AXPOLICY                    │
│          authorization decision              │
└──────────────────────▲───────────────────────┘
                       │
┌──────────────────────┴───────────────────────┐
│               AXCAPABILITY                   │
│       authority / rights / delegation        │
└──────────────────────▲───────────────────────┘
                       │
┌──────────────────────┴───────────────────────┐
│                   AXAUTH                      │
│       authentication / security session      │
└──────────────────────▲───────────────────────┘
                       │
┌──────────────────────┴───────────────────────┐
│                   AXTRUST                     │
│        trust / evidence / evaluation          │
└──────────────▲───────────────────▲────────────┘
               │                   │
          ┌────┴────┐         ┌────┴─────┐
          │ AXCERT  │         │ AXIDENTITY│
          └────▲────┘         └──────────┘
               │
          ┌────┴────┐
          │AXCRYPTO │
          └─────────┘
```

Điểm quan trọng là **không một module nào trong chuỗi trên được phép trở thành “god security module”**.

Mỗi tầng chỉ có một trách nhiệm rõ ràng:

```text
AXIDENTITY   = WHO
AXCERT       = WHAT CREDENTIAL/EVIDENCE
AXTRUST      = WHAT IS TRUSTED
AXAUTH       = PROVE CONTROL
AXCAPABILITY = WHAT AUTHORITY EXISTS
AXPOLICY     = WHAT IS ALLOWED IN THIS CONTEXT
AXSECURITY   = ENFORCE
```

---

# BOOTSTRAP-759 — AXAUDIT

**Native Security Audit, Event Provenance, Tamper-Evident Log, Compliance Evidence & Security Telemetry Runtime 5.0**

Task tiếp theo sẽ tách **audit/evidence** khỏi `AXSECURITY`.

Điều này quan trọng vì security enforcement không nên vừa là:

```text
authorization engine
+
sandbox
+
audit database
+
forensic system
```

Kiến trúc kế tiếp:

```text
AXAUTH ────────┐
AXCAPABILITY ──┤
AXPOLICY ──────┤
AXSECURITY ────┤
AXPROCESS ─────┤
AXNETWORK ─────┤
AXSTORAGE ─────┤
                ▼
            AXAUDIT
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    events   provenance  evidence
       │        │        │
       └────────┼────────┘
                ▼
       tamper-evident log
                │
                ▼
          audit storage
```

`AXAUDIT` sẽ là **evidence plane**: ghi nhận *điều gì đã xảy ra, bởi context nào, dưới policy/version nào, với resource/authority nào*, nhưng không được biến audit thành một cơ chế cấp quyền hoặc thay đổi security decision.