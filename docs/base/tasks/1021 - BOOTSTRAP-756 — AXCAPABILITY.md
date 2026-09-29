# BOOTSTRAP-756 — AXCAPABILITY

**Title:** Native Capability, Authority Token, Delegation, Attenuation, Object Rights & Least-Authority Security Runtime 5.0  
**Namespace:** `AXCAPABILITY`  
**Phase:** Axiom Civilization Runtime / Native Capability & Authority Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXCAPABILITY` là primitive authorization layer nằm giữa authenticated identity/session và resource enforcement.

Nó biến:

```text
authenticated principal
        +
explicit authority
        +
resource/object identity
        +
rights
```

thành:

```text
capability
```

và cho phép capability được:

- giữ;
- truyền;
- giới hạn;
- delegate;
- revoke;
- expire;
- audit;
- kiểm tra;
- sử dụng qua IPC/process boundary.

Kiến trúc:

```text
AXIDENTITY
     │
     ▼
AXAUTH
     │
     │ authenticated principal
     ▼
AXCAPABILITY
     │
     ├── capability
     ├── rights
     ├── scope
     ├── delegation
     ├── attenuation
     ├── expiration
     └── revocation
     │
     ▼
AXSECURITY
     │
     ├── authorization
     ├── sandbox
     └── enforcement
```

---

# 2. Strong boundary

## AXCAPABILITY sở hữu

- capability object;
- authority token;
- resource/object binding;
- rights;
- scopes;
- attenuation;
- delegation;
- capability derivation;
- capability lineage;
- capability expiration;
- revocation metadata;
- capability transfer;
- capability sealing;
- capability validation primitive;
- least-authority composition;
- capability sets;
- delegation constraints;
- capability audit metadata.

## AXCAPABILITY không sở hữu

### AXAUTH

Authentication.

### AXTRUST

Trust evaluation.

### AXSECURITY

Final authorization policy và enforcement.

### AXIDENTITY

Identity lifecycle.

### AXPROCESS

Process/address-space/thread ownership.

### AXIPC

IPC transport.

### AXMEMORY

Memory mapping/allocation.

### AXSTORAGE

Persistent storage.

---

# 3. Fundamental distinction

Axiom không nên coi:

```text
identity == authority
```

Một identity có thể tồn tại mà không có capability đối với resource.

```text
principal
   │
   ├── capability A → file X / READ
   ├── capability B → database Y / QUERY
   └── capability C → device Z / CONTROL
```

---

# 4. Capability semantics

Capability là:

```text
unforgeable authority reference
```

gắn với:

```text
resource
+
rights
+
constraints
```

Conceptual:

```text
capability {
    capability_id
    object_id
    rights
    scope
    constraints
    issuer
    holder
    expiry
    lineage
}
```

---

# 5. Capability ≠ permission

Permission thường là:

```text
principal + policy + resource → decision
```

Capability là:

```text
authority object → permitted operation
```

AXCAPABILITY hỗ trợ cả hai mô hình, nhưng capability phải là một primitive độc lập.

---

# 6. Object identity

Capability không được bind vào raw pointer:

```text
capability.pointer = 0x123456
```

Không được.

Phải bind vào stable object identity:

```text
object_id
object_generation
```

hoặc kernel/security handle.

---

# 7. Object reference

```text
capability_object_ref {
    object_type
    object_id
    generation
}
```

Một object bị destroy rồi tạo lại tại cùng địa chỉ không được làm capability cũ hợp lệ trở lại.

---

# 8. Generation protection

Ví dụ:

```text
object_id = 42
generation = 7
```

sau destroy:

```text
object_id = 42
generation = 8
```

Capability `(42,7)` phải fail.

---

# 9. Capability handle

Native representation:

```text
capability_handle
```

phải:

- opaque;
- type-safe;
- generation-safe;
- non-forgeable trong security domain;
- không phụ thuộc virtual address.

---

# 10. Rights model

Core rights:

```text
READ
WRITE
EXECUTE
CREATE
DELETE
OPEN
CLOSE
QUERY
MODIFY
CONTROL
SHARE
DELEGATE
ADMIN
```

Không phải resource nào cũng hỗ trợ tất cả rights.

---

# 11. Rights bitset

Để hot path nhanh:

```text
capability_rights : u64
```

hoặc larger fixed-width bitmap nếu cần.

Compiler có thể specialize:

```text
if rights & READ != 0
```

thành fast path.

---

# 12. Resource-specific rights

Core rights chỉ là baseline.

Subsystem có thể định nghĩa:

```text
FILE_APPEND
SOCKET_BIND
GPU_SUBMIT
WINDOW_PRESENT
DATABASE_QUERY
DATABASE_WRITE
PROCESS_SPAWN
```

nhưng namespace phải tránh collision.

---

# 13. Rights monotonicity

Capability attenuation chỉ được:

```text
remove authority
```

không được:

```text
add authority
```

Ví dụ:

```text
READ | WRITE
      ↓
READ
```

hợp lệ.

```text
READ
 ↓
READ | WRITE
```

không hợp lệ.

---

# 14. Attenuation

```text
capability_attenuate(parent, restrictions)
```

tạo:

```text
child capability
```

với authority ≤ parent.

---

# 15. Scope attenuation

Parent:

```text
database:* / READ
```

Child:

```text
database:users / READ
```

Child không thể trở thành:

```text
database:payments / WRITE
```

---

# 16. Constraint attenuation

Có thể giới hạn:

```text
time
resource
operation
bytes
rate
location/domain
process
tenant
purpose
```

Ví dụ:

```text
WRITE
max_bytes = 4096
expires = T+10m
```

---

# 17. Capability constraint

```text
capability_constraints {
    max_operations
    max_bytes
    expiry
    audience
    purpose
    resource_scope
    tenant_scope
}
```

Constraints phải monotonic.

---

# 18. Time constraints

Capability có thể có:

```text
not_before
expires_at
```

Dùng monotonic/session-relative semantics khi phù hợp.

Nếu dựa vào wall clock thì phải ghi rõ clock domain.

---

# 19. Absolute expiration

```text
expires_at
```

sau thời điểm đó capability invalid.

Không tự động renew nếu không có authority mới.

---

# 20. Operation limits

Capability có thể giới hạn:

```text
max_uses
max_bytes
max_objects
```

Counter update phải atomic.

---

# 21. Rate limits

Capability có thể mang:

```text
rate_limit
burst_limit
window
```

Nhưng implementation có thể delegate enforcement tới AXSECURITY.

---

# 22. Audience

Capability có thể giới hạn:

```text
audience = service_A
```

Không được dùng cho:

```text
service_B
```

nếu không nằm trong scope.

---

# 23. Purpose binding

Capability có thể yêu cầu:

```text
purpose = backup
```

Không được dùng cho:

```text
analytics
```

nếu policy cấm.

---

# 24. Tenant binding

Multi-tenant capability:

```text
tenant = T1
resource = database.users
```

không tự động có authority:

```text
tenant = T2
```

---

# 25. Process binding

Capability có thể giới hạn holder:

```text
process_id
process_generation
```

Process restart tạo generation mới.

Capability cũ có thể bị invalid.

---

# 26. Thread binding

Không nên mặc định bind capability vào thread.

Capability thường bind:

```text
principal/process/security context
```

Thread binding chỉ là explicit specialized constraint.

---

# 27. Delegation

```text
parent capability
        ↓
delegate
        ↓
child capability
```

Child authority không được vượt parent.

---

# 28. Delegation right

Không phải capability nào cũng được delegate.

Phải có:

```text
DELEGATE
```

right.

Ví dụ:

```text
READ | DELEGATE
```

có thể tạo child READ capability.

```text
READ
```

không được delegate.

---

# 29. Delegation depth

Có thể giới hạn:

```text
max_delegation_depth
```

Ví dụ:

```text
root → child → grandchild
```

depth = 2.

---

# 30. Delegation lineage

Mỗi delegated capability có:

```text
parent_capability_id
delegation_id
depth
```

để audit và revocation.

---

# 31. Capability lineage

```text
root
 ├── child-A
 │    └── child-A1
 └── child-B
```

Revoking root có thể invalidate toàn bộ descendants nếu policy chọn cascading revocation.

---

# 32. Revocation

Capability có thể bị revoke trước expiration.

```text
ACTIVE
   ↓
REVOKED
```

Revocation phải có generation/epoch.

---

# 33. Revocation model

Baseline hỗ trợ:

```text
INDIVIDUAL
LINEAGE
ISSUER
SUBJECT
RESOURCE
EPOCH
```

Không bắt buộc mọi backend phải hỗ trợ toàn bộ.

---

# 34. Revocation performance

Không kiểm tra một persistent database cho mỗi authorization operation.

Có thể dùng:

```text
revocation_epoch
sharded revocation map
generation counters
bloom/filter-assisted lookup
```

nhưng false positive từ optimization không được biến thành unauthorized allow.

---

# 35. Capability epoch

Resource có:

```text
authority_epoch
```

Capability chứa:

```text
issued_epoch
```

Nếu:

```text
issued_epoch < current_epoch
```

capability có thể bị invalidated.

---

# 36. Sealed capabilities

Một capability có thể được seal:

```text
seal(capability)
```

Sau đó application code không thể sửa metadata/rights.

Chỉ AXCAPABILITY/privileged security backend có thể unseal/inspect theo policy.

---

# 37. Forgery resistance

Capability không được forge bằng cách đoán:

```text
object_id
rights
```

Một capability representation phải có protected integrity.

---

# 38. Software capability representation

Có thể dùng:

```text
capability_handle
```

trỏ tới kernel/security-managed table:

```text
handle
 ↓
capability table
 ↓
object + rights + constraints
```

Đây là mô hình phù hợp native OS.

---

# 39. Token capability representation

Đối với cross-process/remote:

```text
signed/encrypted capability token
```

có thể được sử dụng.

Token phải có:

```text
issuer
subject/audience
object
rights
constraints
expiry
nonce/id
integrity protection
```

---

# 40. Local vs remote capability

### Local

```text
opaque kernel/runtime handle
```

### IPC

```text
capability transfer
```

### Remote

```text
cryptographically protected authority token
```

Không được giả định local handle có thể gửi trực tiếp qua network.

---

# 41. IPC transfer

AXIPC hỗ trợ capability attachment:

```text
message
 ├── payload
 └── capability attachment
```

AXCAPABILITY xác định:

```text
which rights are transferred
```

AXIPC vận chuyển.

---

# 42. Transfer attenuation

Sender có:

```text
READ | WRITE
```

gửi receiver:

```text
READ
```

hợp lệ.

Sender không thể transfer:

```text
ADMIN
```

nếu không sở hữu authority đó.

---

# 43. Handle transfer

Capability transfer có thể tạo receiver-specific handle:

```text
sender_handle
      ↓
AXIPC
      ↓
receiver_handle
```

Hai handle không nhất thiết có cùng numeric value.

---

# 44. Capability duplication

Duplicate:

```text
dup(capability)
```

không làm tăng aggregate authority.

Nếu quota/usage-count là constraint, duplication phải share hoặc correctly account constraint state.

---

# 45. Linear authority

Một số capabilities có thể cần move semantics:

```text
move(capability)
```

Sau move:

```text
source = invalid
destination = valid
```

Useful cho:

- exclusive device;
- transaction;
- one-shot authority.

---

# 46. Consumable capability

Capability có thể là:

```text
ONE_SHOT
LIMITED
REUSABLE
```

Ví dụ:

```text
ONE_SHOT
```

sau successful use:

```text
CONSUMED
```

---

# 47. Atomic consumption

One-shot capability phải consume atomically với operation authorization.

Không được:

```text
check
   ↓
context switch
   ↓
consume
```

dẫn đến double-use.

---

# 48. Object lifecycle integration

Capability phải xử lý:

```text
object destroyed
object recreated
object migrated
object renamed
```

Object identity không được phụ thuộc display name.

---

# 49. Rename safety

Nếu:

```text
file A → renamed → file B
```

capability object identity vẫn giữ nguyên nếu underlying object giữ identity.

Nếu object mới được tạo thì capability cũ không tự chuyển sang object mới.

---

# 50. Resource hierarchy

Một capability có thể giới hạn subtree:

```text
filesystem:/data/project/
```

Child:

```text
filesystem:/data/project/logs/
```

Canonical resource path phải tránh ambiguity.

---

# 51. Namespace binding

Capability có thể bind namespace:

```text
namespace_id
object_id
```

Điều này ngăn cùng object ID ở namespace khác được nhầm là cùng object.

---

# 52. Capability set

```text
capability_set {
    capabilities[]
}
```

Có thể dùng để truyền một authority context.

---

# 53. Set semantics

Set có thể hỗ trợ:

```text
intersection
attenuate
filter
merge
```

Nhưng:

```text
merge(A,B)
```

chỉ hợp lệ nếu caller đã có authority đối với cả A và B.

---

# 54. Intersection

Intersection:

```text
A ∩ B
```

chỉ giữ authority chung.

Ví dụ:

```text
A = READ | WRITE
B = READ
A ∩ B = READ
```

---

# 55. No privilege amplification

Các operation:

```text
merge
clone
delegate
transfer
deserialize
resume
```

không được tạo quyền mới.

---

# 56. Capability serialization

Local capability handle không serialize trực tiếp.

Remote transferable capability phải dùng explicit:

```text
capability_export()
capability_import()
```

và policy.

---

# 57. Export

Export có thể yêu cầu:

```text
EXPORT
```

authority riêng.

Không phải mọi capability đều transferable.

---

# 58. Import

Import phải verify:

```text
integrity
issuer
audience
expiry
resource
rights
delegation
```

và gọi AXTRUST khi external trust evidence cần được đánh giá.

---

# 59. Capability issuer

```text
capability_issuer {
    issuer_id
    authority_domain
    signing_key_ref
}
```

Signing keys thuộc AXCRYPTO.

Trust của issuer thuộc AXTRUST.

---

# 60. Capability token format

Logical:

```text id="ylp24h"
capability_token {
    version
    issuer
    audience
    object
    rights
    constraints
    issued_at
    expires_at
    delegation
    token_id
    integrity
}
```

---

# 61. Token confidentiality

Capability token có thể chứa sensitive metadata.

Profile có thể yêu cầu:

```text
AEAD encryption
```

Integrity luôn phải được bảo đảm.

---

# 62. Token replay

Nếu token có replay-sensitive semantics:

```text
token_id
nonce
counter
```

phải được kiểm tra.

Không phải mọi reusable capability đều cần replay cache; semantics phải explicit.

---

# 63. Capability proof

Trong remote context:

```text
capability token
+
proof of possession
```

có thể cần thiết.

Đặc biệt với high-value authority.

---

# 64. Bearer capability

Bearer token:

```text
whoever possesses token
```

có authority.

Do đó cần:

- short lifetime;
- audience binding;
- secure transport;
- optional proof-of-possession.

---

# 65. Proof-of-possession capability

Token bind với key:

```text
token
   ↓
public_key
```

Caller phải prove private-key possession.

AXAUTH/AXCRYPTO cung cấp proof mechanisms.

AXCAPABILITY quản lý authority binding.

---

# 66. Capability + authentication

Không nên mặc định:

```text
authenticated → all capabilities
```

Flow:

```text
AXAUTH
  ↓
principal
  ↓
capability lookup/presentation
  ↓
AXCAPABILITY
  ↓
AXSECURITY
```

---

# 67. Capability + trust

External capability token:

```text
token
 ↓
AXCERT / AXTRUST
 ↓
issuer trusted?
 ↓
AXCAPABILITY
```

Trust result không tự biến thành capability.

---

# 68. Capability + policy

AXSECURITY có thể combine:

```text
capability
+
policy
+
resource state
```

để quyết định authorization.

---

# 69. Final authorization boundary

Canonical:

```text
request
   │
   ▼
authenticated session
   │
   ▼
capability
   │
   ▼
AXSECURITY policy
   │
   ▼
ALLOW / DENY
   │
   ▼
resource
```

AXCAPABILITY không tự bypass AXSECURITY enforcement.

---

# 70. Native API

Baseline:

```text
capability_create()
capability_import()
capability_export()

capability_get_object()
capability_get_rights()
capability_get_constraints()

capability_check()
capability_attenuate()

capability_delegate()
capability_transfer()

capability_revoke()
capability_revoke_lineage()

capability_seal()
capability_validate()

capability_duplicate()
capability_move()
capability_consume()

capability_intersect()
capability_set_create()
capability_set_add()
capability_set_remove()

capability_bind_process()
capability_bind_session()
capability_bind_audience()
capability_bind_purpose()

capability_set_expiry()
capability_set_quota()

capability_start_trace()
capability_stop_trace()

capability_simulate()
capability_replay()

capability_get_stats()
capability_get_provider_info()
```

---

# 71. Compiler integration

Axiom compiler có thể hiểu capability types:

```text
cap<file, READ>
cap<socket, WRITE>
cap<gpu, SUBMIT>
```

Compiler không cần runtime reflection để kiểm tra type-level resource category.

---

# 72. Capability generic types

Conceptual:

```text
cap<T, Rights>
```

Ví dụ:

```text
cap<File, READ>
cap<Database, QUERY>
```

`Rights` có thể là compile-time constant.

---

# 73. Compile-time attenuation

Nếu:

```text
cap<File, READ|WRITE>
```

thì:

```text
attenuate<READ>()
```

có thể tạo:

```text
cap<File, READ>
```

Compiler biết child không thể có WRITE.

---

# 74. Runtime authority

Không phải mọi authority đều compile-time known.

Dynamic capabilities:

```text
capability_handle
```

vẫn cần runtime validation.

---

# 75. Unsafe escape hatch

Raw OS handles có thể được import bằng:

```text
unsafe
```

nhưng conversion:

```text
raw_handle → capability
```

phải đi qua explicit security boundary.

Không được tự động biến mọi integer thành capability.

---

# 76. FFI

FFI có thể nhận:

```text
capability_handle
```

nhưng ABI phải xác định rõ:

```text
ownership
duplication
close
transfer
rights
```

---

# 77. Capability lifetime

Capability lifecycle:

```text
CREATED
   ↓
ACTIVE
   ↓
TRANSFERRED
   ↓
ACTIVE
   ↓
REVOKED
   ↓
CLOSED
```

Alternative:

```text
ACTIVE → CONSUMED
```

cho one-shot capability.

---

# 78. Crash semantics

Process crash:

```text
process capability handles
```

có thể tự invalid nếu capability scoped to process.

Delegated remote capabilities không nhất thiết invalid, tùy binding.

---

# 79. Checkpoint semantics

Checkpoint phải preserve:

```text
capability identity
authority epoch
expiration
revocation state
```

nhưng không được restore revoked authority.

---

# 80. Deterministic simulation

Simulation hỗ trợ:

```text
create
attenuate
delegate
transfer
revoke
expire
consume
check
```

với virtual clock.

---

# 81. Trace

Trace event:

```text
CAP_CREATED
CAP_ATTENUATED
CAP_DELEGATED
CAP_TRANSFERRED
CAP_CHECKED
CAP_DENIED
CAP_REVOKED
CAP_EXPIRED
CAP_CONSUMED
```

Không log secret token material.

---

# 82. Performance

Hot path:

```text
capability_handle
        ↓
generation check
        ↓
rights mask
        ↓
constraint check
        ↓
ALLOW
```

Mục tiêu là vài memory loads + integer operations trong common case.

---

# 83. Fast-path layout

Capability table entry nên compact:

```text
object_id
generation
rights
flags
expiry
authority_epoch
```

Metadata hiếm dùng để separate cold storage.

---

# 84. Per-process capability table

Process có thể có:

```text
local_cap_table
```

giống concept native handle table.

Lookup:

```text
handle → table[index] → generation
```

---

# 85. Revocation fast path

Resource/authority epoch có thể được cache.

Ví dụ:

```text
cap.epoch == object.current_epoch
```

→ valid.

Mismatch:

```text
→ slow validation path
```

---

# 86. No global authorization lock

Capability checks không được yêu cầu một global mutex.

Sử dụng:

- immutable metadata;
- atomic epochs;
- sharded revocation maps;
- lock-free read paths khi phù hợp.

---

# 87. Security-critical mutation

Các operation:

```text
delegate
revoke
consume
change_epoch
```

phải có atomic semantics.

---

# 88. Memory safety

Capability handle không phải raw pointer.

Invalid handle:

```text
CAP_INVALID
```

thay vì memory access.

---

# 89. Namespace isolation

Capability từ security domain A không được tự động hợp lệ trong domain B.

Phải có explicit trust/transfer boundary.

---

# 90. AI boundary

AI có thể:

- phân tích capability graphs;
- phát hiện authority dư thừa;
- tìm delegation chains;
- giải thích authorization failures;
- đề xuất attenuation;
- mô phỏng capability flows.

AI không được:

- tự cấp capability;
- tự tăng rights;
- bỏ qua revocation;
- bypass AXSECURITY;
- forge capability token;
- tự export secret authority.

---

# 91. Formal invariants

### CAP-INV-01
Capability không đồng nhất với identity.

### CAP-INV-02
Authentication không tự tạo toàn quyền authority.

### CAP-INV-03
Capability phải bind vào stable object identity.

### CAP-INV-04
Raw virtual address không phải capability identity.

### CAP-INV-05
Object generation phải chống stale-handle reuse.

### CAP-INV-06
Capability rights phải được biểu diễn rõ ràng.

### CAP-INV-07
Capability attenuation không được tăng authority.

### CAP-INV-08
Delegation không được tăng authority.

### CAP-INV-09
Delegation phải yêu cầu `DELEGATE` authority khi policy yêu cầu.

### CAP-INV-10
Capability child không vượt rights của parent.

### CAP-INV-11
Capability child không vượt scope của parent.

### CAP-INV-12
Capability child không vượt expiry của parent.

### CAP-INV-13
Capability constraints phải monotonic trong attenuation.

### CAP-INV-14
Capability không transferable nếu policy cấm transfer.

### CAP-INV-15
Capability export phải explicit.

### CAP-INV-16
Capability import phải verify integrity.

### CAP-INV-17
External capability issuer phải được trust-evaluate khi required.

### CAP-INV-18
Capability token không được coi raw session ID là authority.

### CAP-INV-19
Bearer capability phải được xử lý theo bearer semantics.

### CAP-INV-20
Proof-of-possession capability phải verify key possession.

### CAP-INV-21
Capability replay protection phải explicit khi capability semantics yêu cầu.

### CAP-INV-22
Capability expiration phải được enforce.

### CAP-INV-23
Capability revocation phải invalidate authority theo configured scope.

### CAP-INV-24
Revocation epoch không được quay ngược.

### CAP-INV-25
One-shot capability phải consume atomically.

### CAP-INV-26
Capability duplication không được tạo privilege amplification.

### CAP-INV-27
Capability transfer phải preserve hoặc attenuate rights.

### CAP-INV-28
Capability handle phải generation-safe.

### CAP-INV-29
Capability metadata không được chứa plaintext cryptographic secrets trong default trace.

### CAP-INV-30
Capability serialization không được expose local opaque handles như portable authority.

### CAP-INV-31
Capability set merge không được tạo authority ngoài input capabilities.

### CAP-INV-32
Capability intersection không được tạo authority mới.

### CAP-INV-33
Process-scoped capabilities phải obey process-generation semantics.

### CAP-INV-34
Session-scoped capabilities phải obey session lifecycle.

### CAP-INV-35
Checkpoint restore không được resurrect revoked authority.

### CAP-INV-36
Capability hot-path validation phải không phụ thuộc network.

### CAP-INV-37
AXCAPABILITY không tự quyết định final application authorization policy.

### CAP-INV-38
AXCAPABILITY không reimplement cryptographic primitives.

### CAP-INV-39
AI không được tạo hoặc nâng authority trái policy.

### CAP-INV-40
`AXCAPABILITY 5.0` phải duy trì least-authority và monotonic attenuation.

---

# 92. Definition of Done

`AXCAPABILITY 5.0` hoàn tất khi có:

- stable object identity;
- generation-safe handles;
- rights model;
- resource-specific rights;
- scopes;
- constraints;
- attenuation;
- delegation;
- delegation depth;
- delegation lineage;
- revocation;
- revocation epochs;
- capability expiration;
- audience binding;
- purpose binding;
- tenant binding;
- process/session binding;
- capability transfer;
- IPC integration;
- local capability handles;
- remote capability tokens;
- bearer capability semantics;
- proof-of-possession capability;
- capability export/import;
- capability sealing;
- one-shot capabilities;
- consumable capabilities;
- quota constraints;
- capability sets;
- intersection;
- safe merge;
- capability serialization;
- checkpoint semantics;
- crash semantics;
- deterministic simulation;
- fault injection;
- audit tracing;
- compiler capability types;
- runtime capability handles;
- FFI ABI;
- AXAUTH integration;
- AXTRUST integration;
- AXCRYPTO integration;
- AXIPC integration;
- AXPROCESS integration;
- AXMEMORY integration;
- AXSECURITY enforcement boundary;
- performance fast path;
- 40 invariants.

**AXCAPABILITY 5.0 → FROZEN.**

---

# BOOTSTRAP-757 — AXPOLICY

**Native Authorization Policy, Rule Engine, Resource Policy, Conditional Access & Policy Compilation Runtime 5.0**

Kiến trúc tiếp theo:

```text
                  AXAUTH
                     │
                     ▼
             authenticated principal
                     │
                     ▼
              AXCAPABILITY
                     │
                     ├───────────────┐
                     │               │
                     ▼               ▼
                authority         resource
                     │               │
                     └──────┬────────┘
                            ▼
                         AXPOLICY
                            │
                  ┌─────────┼─────────┐
                  ▼         ▼         ▼
              conditions  context   constraints
                  │         │         │
                  └─────────┼─────────┘
                            ▼
                       policy decision
                            │
                            ▼
                       AXSECURITY
                            │
                            ▼
                        ENFORCE
```

`AXPOLICY` sẽ tách riêng **“authority capability là gì”** khỏi **“trong context cụ thể này, operation có được phép hay không”**. Đây là bước cần thiết trước khi hoàn thiện `AXSECURITY` thành lớp enforcement thống nhất cho toàn bộ Axiom OS/runtime.