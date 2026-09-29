# BOOTSTRAP-757 — AXPOLICY

**Title:** Native Authorization Policy, Rule Engine, Resource Policy, Conditional Access & Policy Compilation Runtime 5.0  
**Namespace:** `AXPOLICY`  
**Phase:** Axiom Civilization Runtime / Native Authorization Policy & Decision Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXPOLICY` là tầng biến:

```text
principal
+
capability/authority
+
requested operation
+
resource
+
runtime context
+
security policy
```

thành:

```text
policy decision
```

Nó trả lời:

> Trong context hiện tại, operation này có đáp ứng policy authorization hay không?

Kiến trúc:

```text
AXAUTH
   │
   ▼
authenticated principal
   │
   ├──────────────────────┐
   ▼                      ▼
AXCAPABILITY           context
   │                      │
   └──────────┬───────────┘
              ▼
          AXPOLICY
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
    rules  conditions obligations
       │      │      │
       └──────┼──────┘
              ▼
        policy decision
              │
              ▼
         AXSECURITY
              │
              ▼
          enforcement
```

---

# 2. Strong boundary

### AXPOLICY sở hữu

- authorization policy;
- policy language;
- policy AST/IR;
- rule evaluation;
- condition evaluation;
- policy compilation;
- policy versioning;
- policy snapshots;
- resource selectors;
- subject selectors;
- context matching;
- obligations;
- deny/allow semantics;
- policy composition;
- policy inheritance;
- policy simulation;
- policy explanation;
- policy testing;
- deterministic evaluation.

### Không sở hữu

**AXAUTH**

- authentication;
- session establishment.

**AXCAPABILITY**

- authority object;
- capability issuance/delegation/attenuation.

**AXSECURITY**

- enforcement;
- sandbox;
- actual privileged operation.

**AXTRUST**

- trust evaluation.

**AXIDENTITY**

- identity lifecycle.

**AXPROCESS**

- process enforcement primitives.

**AXNETWORK**

- network transport.

---

# 3. Fundamental model

Authorization:

```text
decision =
    evaluate(
        policy,
        principal,
        authority,
        resource,
        operation,
        context
    )
```

Không được rút gọn thành:

```text
principal → permission
```

vì cùng một principal có thể có quyền khác nhau tùy:

- resource;
- operation;
- capability;
- tenant;
- purpose;
- time;
- session;
- environment;
- resource state.

---

# 4. Policy decision

Core result:

```text
policy_decision {
    decision
    policy_id
    policy_version
    subject
    resource
    operation
    reasons[]
    obligations[]
    constraints[]
    evaluated_at
}
```

`decision` baseline:

```text
ALLOW
DENY
NOT_APPLICABLE
INDETERMINATE
```

---

# 5. Vì sao không chỉ ALLOW/DENY

`NOT_APPLICABLE`:

```text
rule không match request
```

`INDETERMINATE`:

```text
policy cần một input chưa có
hoặc evaluation failure
```

Điều này quan trọng để phân biệt:

```text
"không có rule cho phép"
```

với:

```text
"rule có thể quyết định nhưng evaluation bị lỗi"
```

---

# 6. Final enforcement semantics

AXPOLICY không trực tiếp mở file, gửi packet hoặc kill process.

Flow:

```text
request
   ↓
AXSECURITY
   ↓
build authorization context
   ↓
AXPOLICY
   ↓
decision
   ↓
AXSECURITY
   ↓
enforce
```

---

# 7. Authorization request

```text
authorization_request {
    principal
    session
    capability[]
    resource
    operation
    purpose
    context
    timestamp
}
```

---

# 8. Principal

Principal có thể là:

```text
USER
SERVICE
PROCESS
DEVICE
APPLICATION
SYSTEM
GROUP
TENANT
```

AXPOLICY không quản lý lifecycle của chúng.

---

# 9. Resource

```text
policy_resource {
    resource_type
    resource_id
    namespace
    owner
    attributes
}
```

Resource ID phải stable.

Không dùng display name làm security identity.

---

# 10. Operation

Operation là canonical identifier:

```text
FILE.READ
FILE.WRITE
FILE.DELETE

PROCESS.SPAWN
PROCESS.TERMINATE

NETWORK.CONNECT
NETWORK.BIND

DATABASE.QUERY
DATABASE.WRITE

GPU.SUBMIT
```

Không dùng arbitrary strings trên hot path nếu có thể tránh.

---

# 11. Operation hierarchy

Có thể định nghĩa:

```text
FILE.*
    ├── READ
    ├── WRITE
    └── DELETE
```

Nhưng wildcard phải có semantics rõ ràng.

```text
FILE.*
```

không được vô tình bao gồm một operation mới được thêm sau này nếu policy snapshot không cho phép.

---

# 12. Resource selector

```text
resource_selector {
    type
    namespace
    path/pattern
    attributes
}
```

Có thể chọn:

```text
exact
prefix
set
attribute_match
hierarchy
```

---

# 13. Subject selector

```text
subject_selector {
    principal_type
    principal_id
    attributes
    groups
    tenant
}
```

Không được suy luận identity từ user-visible name nếu stable ID có sẵn.

---

# 14. Policy rule

```text
policy_rule {
    rule_id
    effect
    subject
    resource
    operations
    conditions
    obligations
    priority
}
```

---

# 15. Effect

Baseline:

```text
ALLOW
DENY
```

Nhưng rule evaluation có thể tạo:

```text
NOT_APPLICABLE
INDETERMINATE
```

---

# 16. Explicit deny

Deny phải có semantics deterministic.

Ví dụ:

```text
ALLOW FILE.READ
DENY FILE.READ where resource.classified
```

Policy composition phải quy định rule nào thắng.

---

# 17. Deny-overrides

Baseline profile:

```text
DENY_OVERRIDES
```

Nếu bất kỳ applicable deny rule nào match:

```text
DENY
```

---

# 18. Permit-overrides

Một số policy domains có thể cần:

```text
PERMIT_OVERRIDES
```

Nhưng không được sử dụng implicit.

Policy phải khai báo combining algorithm.

---

# 19. First-match

Có thể hỗ trợ:

```text
FIRST_MATCH
```

nhưng compiler phải bảo toàn ordering.

---

# 20. Priority

Rule có:

```text
priority : i32
```

Priority ordering phải deterministic.

Không được phụ thuộc hash-map iteration order.

---

# 21. Combining policy

```text
policy_combiner {
    DENY_OVERRIDES
    ALLOW_OVERRIDES
    FIRST_MATCH
    PRIORITY
    ALL_MATCH
}
```

Profile cụ thể phải freeze semantics.

---

# 22. Conditions

Conditions có thể kiểm tra:

```text
time
session
authentication_assurance
capability
resource_attributes
principal_attributes
tenant
purpose
device
network_context
process
environment
```

---

# 23. Condition IR

Ví dụ:

```text
condition:
    auth.assurance >= HIGH
    AND
    request.operation == FILE.WRITE
    AND
    resource.tenant == principal.tenant
```

Compiler:

```text
AST
 ↓
typed condition IR
 ↓
optimized PolicyIR
 ↓
native evaluator
```

---

# 24. Type system

Policy values phải typed:

```text
bool
integer
string
enum
timestamp
duration
identifier
set<T>
resource_ref
principal_ref
capability_ref
```

Không implicit convert nguy hiểm.

---

# 25. Comparison semantics

Ví dụ:

```text
timestamp < timestamp
```

hợp lệ.

```text
principal_id < timestamp
```

không hợp lệ.

Policy compiler phải reject.

---

# 26. Missing attribute

Nếu condition yêu cầu:

```text
device.attestation_level
```

nhưng context không có:

Không tự động coi là:

```text
false
```

hay:

```text
true
```

Mặc định:

```text
UNKNOWN
```

→ policy combining algorithm quyết định.

---

# 27. Three-valued evaluation

Condition:

```text
TRUE
FALSE
UNKNOWN
```

được xử lý explicit.

Điều này tránh security bug do missing information.

---

# 28. Context

```text
authorization_context {
    principal
    session
    capabilities
    resource
    operation
    purpose
    device
    environment
    network
    time
}
```

Context phải là immutable snapshot trong một evaluation.

---

# 29. Time

Policy không tự gọi system clock nhiều lần.

Evaluation context chứa:

```text
evaluation_time
```

Tất cả rules trong cùng request sử dụng cùng snapshot.

---

# 30. Purpose

Purpose:

```text
READ_FOR_DISPLAY
READ_FOR_BACKUP
READ_FOR_EXPORT
PROCESS_FOR_ANALYTICS
```

có thể là policy dimension.

Purpose phải do caller/security layer cung cấp hoặc được xác thực bằng context, không phải chỉ một string tùy ý mà application có thể tự khai báo để vượt policy.

---

# 31. Authentication assurance

AXPOLICY có thể kiểm tra:

```text
auth.assurance
auth.factors
auth.age
auth.method
```

Ví dụ:

```text
auth.assurance >= REQUIRED_LEVEL
```

Nguồn assurance là AXAUTH.

---

# 32. Capability condition

Policy có thể yêu cầu:

```text
capability.has(FILE.WRITE)
```

AXCAPABILITY cung cấp authority facts.

---

# 33. Capability ≠ policy

Có capability:

```text
FILE.WRITE
```

không nhất thiết nghĩa là:

```text
ALLOW
```

Policy vẫn có thể deny do:

- tenant;
- time;
- resource state;
- purpose;
- environment.

---

# 34. Policy + capability

Canonical:

```text
authority = AXCAPABILITY.check(...)
policy = AXPOLICY.evaluate(...)

final =
    authority
    AND
    policy
```

Nếu capability không đủ authority:

```text
DENY
```

Policy không thể tạo authority mà capability không có.

---

# 35. No privilege amplification

Policy không được biến:

```text
READ capability
```

thành:

```text
WRITE authority
```

---

# 36. Policy inheritance

Resources có thể kế thừa policy:

```text
/root
   └── /project
        └── /private
```

Policy inheritance phải deterministic.

---

# 37. Inheritance modes

```text
INHERIT
OVERRIDE
MERGE
DENY_BOUNDARY
```

Resource-specific semantics phải explicit.

---

# 38. Policy boundary

Một child resource có thể tạo deny boundary:

```text
parent policy
     ↓
child deny boundary
```

Không được vô tình inherit authority xuyên security boundary.

---

# 39. Attribute-based authorization

ABAC:

```text
principal.department == resource.department
```

có thể được compiler tối ưu thành typed attribute comparison.

---

# 40. Role-based authorization

RBAC có thể là policy sugar:

```text
role = editor
```

được compile thành subject attributes/rules.

Role lifecycle không thuộc AXPOLICY.

---

# 41. Group-based authorization

Group membership có thể được đưa vào context:

```text
principal.groups[]
```

Nguồn authoritative thuộc AXIDENTITY/security directory.

---

# 42. Capability-based authorization

Capability là authority input.

AXPOLICY không phát hành capability.

---

# 43. Hybrid authorization

Axiom hỗ trợ:

```text
identity
+
role
+
capability
+
attributes
+
resource state
```

trong cùng policy.

---

# 44. Resource state

Policy có thể xem:

```text
resource.state
```

Ví dụ:

```text
resource.locked
resource.owner
resource.classification
resource.lifecycle
```

Nhưng resource subsystem là nguồn authoritative.

---

# 45. Environmental context

Có thể bao gồm:

```text
device_state
network_zone
application_id
process_id
tenant
security_domain
```

Không được tự suy đoán nếu source không cung cấp.

---

# 46. Policy obligations

Decision có thể trả:

```text
obligation {
    type
    parameters
}
```

Ví dụ:

```text
REQUIRE_AUDIT
REQUIRE_ENCRYPTION
REQUIRE_REAUTH
LIMIT_OUTPUT
```

AXSECURITY chịu trách nhiệm enforce obligation.

---

# 47. Advice vs obligation

`advice`:

```text
nên thực hiện
```

không phải security requirement.

`obligation`:

```text
phải thực hiện
```

Nếu enforcement không thể thực hiện obligation:

```text
ALLOW
```

không được trả về nếu policy yêu cầu obligation bắt buộc.

---

# 48. Conditional allow

Ví dụ:

```text
ALLOW
IF
    capability = READ
AND
    encryption = ENABLED
```

Decision phải mang condition/obligation cần enforce.

---

# 49. Authorization decision token

AXPOLICY có thể tạo:

```text
policy_decision_token
```

cho downstream enforcement.

Token phải bind:

```text
request
policy version
resource
operation
principal
expiration
```

Không được reusable ngoài intended context.

---

# 50. Decision caching

Decision có thể cache nếu:

```text
policy_version
principal
resource
operation
capability_epoch
context_hash
```

đều phù hợp.

---

# 51. Cache invalidation

Cache phải invalidate khi thay đổi:

```text
policy
capability
principal authority
resource security state
revocation epoch
```

Không dùng TTL làm phương pháp duy nhất nếu security state yêu cầu immediate invalidation.

---

# 52. Immutable policy snapshot

Evaluation:

```text
policy_version = 42
```

phải dùng snapshot 42 xuyên suốt request.

Hot reload tạo:

```text
policy_version = 43
```

cho request mới.

---

# 53. Policy hot reload

```text
load
 ↓
validate
 ↓
compile
 ↓
self-test
 ↓
publish atomically
```

Policy đang chạy không bị mutate giữa evaluation.

---

# 54. Policy signing

Production policy có thể được signed:

```text
policy
   ↓
AXCRYPTO
   ↓
signature
```

Trust của policy issuer:

```text
AXTRUST
```

---

# 55. Policy provenance

```text
policy_metadata {
    policy_id
    version
    issuer
    created_at
    source_hash
    signature_ref
}
```

---

# 56. Policy rollback

Policy registry hỗ trợ:

```text
activate(version)
rollback(version)
```

nhưng rollback phải tạo explicit activation event.

Không âm thầm revert.

---

# 57. Policy compilation

Compiler pipeline:

```text
policy source
    ↓
lexer/parser
    ↓
AST
    ↓
name resolution
    ↓
type checking
    ↓
constant evaluation
    ↓
policy normalization
    ↓
PolicyIR
    ↓
optimization
    ↓
native evaluator
```

---

# 58. PolicyIR

Core instructions:

```text
LOAD_PRINCIPAL
LOAD_RESOURCE
LOAD_OPERATION
LOAD_CAPABILITY
LOAD_CONTEXT

CHECK_IDENTITY
CHECK_ROLE
CHECK_GROUP
CHECK_RIGHT

LOAD_ATTRIBUTE
COMPARE
IN_SET
MATCH_RESOURCE

CHECK_TIME
CHECK_ASSURANCE
CHECK_TENANT
CHECK_PURPOSE

AND
OR
NOT

ALLOW
DENY
UNKNOWN
REQUIRE

EMIT_OBLIGATION
EMIT_REASON
RETURN
```

---

# 59. Policy optimization

Compiler có thể:

- constant fold;
- dead-rule elimination;
- selector indexing;
- decision-tree generation;
- attribute prefetch planning;
- common-condition elimination;
- rule specialization;
- hot-path compilation.

---

# 60. Rule indexing

Thay vì:

```text
for every rule:
    evaluate
```

có thể index:

```text
operation
resource_type
tenant
principal_type
```

để giảm candidate rules.

---

# 61. Decision tree

Policy:

```text
operation
   ↓
resource type
   ↓
tenant
   ↓
principal class
   ↓
capability
   ↓
conditions
```

có thể được compile thành decision tree.

---

# 62. No dynamic allocation hot path

Evaluation nên dùng:

```text
stack locals
immutable compiled policy
arena for temporary data
```

không allocate từng rule.

---

# 63. Parallel evaluation

Independent policy branches có thể chạy song song trong large policy graphs.

Nhưng common authorization request phải ưu tiên latency thấp.

Không tạo task cho những expression nhỏ.

---

# 64. SIMD optimization

Sets/bitsets có thể sử dụng:

```text
SIMD
bit-parallel operations
```

cho membership/rights checks.

---

# 65. Policy ABI

Compiled policy:

```text
AXPOLICY_IR_1
```

có stable:

- opcode IDs;
- type IDs;
- metadata format;
- ABI version.

---

# 66. Native policy module

Compiled policy có thể trở thành:

```text
.axpolicy
```

logical artifact chứa:

```text
header
policy metadata
PolicyIR
indexes
compiled code
debug/explanation metadata
signature
```

---

# 67. Debug metadata

Release build có thể strip:

```text
source locations
rule explanations
symbol names
```

nhưng policy identity/version phải giữ.

---

# 68. Explanation

Decision có thể trả:

```text
reason {
    rule_id
    condition
    result
}
```

Ví dụ conceptual:

```text
DENY
because:
  rule R17 matched
  capability missing WRITE
```

Explanation không được tiết lộ protected policy internals cho untrusted caller.

---

# 69. Explainability levels

```text
NONE
BASIC
DETAILED
DEBUG
```

Security policy quyết định caller được xem level nào.

---

# 70. Audit

AXPOLICY có thể emit:

```text
POLICY_EVALUATED
ALLOW
DENY
INDETERMINATE
POLICY_LOADED
POLICY_ACTIVATED
POLICY_ROLLED_BACK
```

Audit sink thuộc security/audit infrastructure.

---

# 71. Sensitive policy data

Không log:

- secrets;
- capability token raw;
- private keys;
- authentication credentials.

Có thể log stable hashes/IDs.

---

# 72. Deterministic evaluation

Cùng:

```text
policy snapshot
+
same request context
```

phải tạo cùng decision.

Không được phụ thuộc:

```text
hash iteration order
thread scheduling
wall-clock calls giữa rules
```

---

# 73. Explicit nondeterminism

Nếu policy phụ thuộc external state:

```text
resource state
device state
network state
```

thì state phải snapshot vào context.

---

# 74. Simulation

```text
policy_simulation {
    policy
    requests[]
    virtual_context
}
```

có thể trả decision matrix.

---

# 75. What-if analysis

Có thể hỏi:

```text
"nếu capability WRITE được thêm thì decision thay đổi thế nào?"
```

Simulation chỉ tạo hypothetical context.

Không mutation production authority.

---

# 76. Policy testing

Mỗi policy có thể có test:

```text
policy_test {
    request
    expected_decision
    expected_obligations
}
```

Compiler/test runner thực hiện trước activation.

---

# 77. Policy coverage

Compiler có thể báo:

```text
rule coverage
condition coverage
branch coverage
resource selector coverage
```

Không phải security proof tuyệt đối.

---

# 78. Conflict detection

Compiler có thể phát hiện:

```text
unreachable rule
overlapping rules
contradictory conditions
shadowed rule
```

Nhưng không tự thay đổi semantics.

---

# 79. Policy lint

Warnings:

```text
UNREACHABLE_RULE
REDUNDANT_RULE
BROAD_SELECTOR
MISSING_EXPLICIT_DENY
UNBOUNDED_RESOURCE_PATTERN
UNKNOWN_ATTRIBUTE
```

Warnings không tự biến thành compile errors trừ khi policy profile yêu cầu.

---

# 80. Policy sandbox

Policy evaluation phải không có arbitrary side effects.

Không cho policy code:

```text
open file
network call
spawn process
modify resource
```

Policy language là declarative/pure.

---

# 81. External attributes

Nếu policy cần external attribute:

```text
device.attestation
```

attribute provider phải explicit.

Không cho policy evaluator tự ý network fetch.

---

# 82. Async attribute acquisition

Nếu cần external data:

```text
authorize_async()
```

có thể:

```text
AXTASK
+
AXASYNC
```

Nhưng compiled policy evaluation bản thân phải pure.

---

# 83. Failure semantics

Nếu required attribute provider fails:

```text
INDETERMINATE
```

Policy profile có thể map:

```text
INDETERMINATE → DENY
```

cho security-critical operations.

---

# 84. Fail-open / fail-closed

Không hard-code global behavior.

Policy profile khai báo:

```text
failure_mode = FAIL_CLOSED
```

hoặc domain-specific behavior.

Sensitive authorization defaults nên tránh implicit fail-open.

---

# 85. Resource availability

Policy không được coi:

```text
resource exists
```

là:

```text
resource accessible
```

Resource existence thuộc resource subsystem.

---

# 86. TOCTOU

Decision và enforcement phải giảm race:

```text
check
 ↓
use
```

Nếu resource có mutable security state, AXSECURITY cần atomic authorization/enforcement boundary hoặc generation validation.

---

# 87. Resource generation

Decision có thể bind:

```text
resource_generation
```

Enforcement kiểm tra generation trước operation nếu cần.

---

# 88. Cross-process policy

Process A:

```text
request
```

Process B:

```text
resource
```

AXSECURITY ở receiving boundary phải evaluate authoritative context.

Không tin policy decision do untrusted sender tự cung cấp.

---

# 89. Remote policy decision

Remote decision token phải có:

```text
issuer
policy_version
request_hash
resource
operation
expiry
integrity
```

và trust verification.

---

# 90. AI boundary

AI được phép:

- phân tích policy;
- giải thích rule conflicts;
- tìm unreachable rules;
- phát hiện overly broad selectors;
- mô phỏng policy changes;
- tạo test cases;
- đề xuất policy refactoring.

AI không được:

- tự activate policy;
- tự remove deny;
- tự grant authority;
- tự bypass missing capability;
- tự chuyển fail-closed thành fail-open;
- tự suppress audit.

---

# 91. Native API

Baseline:

```text
policy_compile()
policy_load()
policy_validate()
policy_activate()
policy_deactivate()
policy_rollback()

policy_get()
policy_get_version()
policy_get_metadata()

policy_context_create()
policy_context_set_principal()
policy_context_set_session()
policy_context_set_capabilities()
policy_context_set_resource()
policy_context_set_operation()
policy_context_set_purpose()
policy_context_set_attribute()

policy_evaluate()
policy_evaluate_async()

policy_decision_get()
policy_decision_explain()

policy_cache_create()
policy_cache_invalidate()

policy_simulate()
policy_test()
policy_lint()

policy_sign()
policy_verify()

policy_start_trace()
policy_stop_trace()

policy_get_stats()
policy_get_capabilities()
```

---

# 92. Compiler-facing API

```text
policy_compile_ir()
policy_optimize_ir()
policy_emit()
policy_load_module()
```

Artifact:

```text
.axpolicy
```

ABI:

```text
AXPOLICY_IR_1
```

---

# 93. Canonical flow — File read

```text
application
    │
    ▼
AXSECURITY
    │
    ├── authenticated session
    ├── capability READ
    ├── resource=file42
    └── operation=FILE.READ
    │
    ▼
AXPOLICY
    │
    ├── policy lookup
    ├── rule selection
    ├── capability condition
    ├── tenant condition
    └── resource condition
    │
    ▼
ALLOW
    │
    ▼
AXSECURITY
    │
    ▼
AXSTORAGE
```

---

# 94. Canonical flow — Write denied by policy

```text
authenticated principal
        │
        ▼
capability WRITE
        │
        ▼
AXPOLICY
        │
        ├── capability valid
        │
        └── resource is READ_ONLY
                 │
                 ▼
                DENY
                 │
                 ▼
             AXSECURITY
```

Capability có thể hợp lệ nhưng policy vẫn deny.

---

# 95. Canonical flow — Missing assurance

```text
principal
   ↓
capability = PAYMENT.WRITE
   ↓
AXPOLICY
   ↓
requires auth.assurance >= HIGH
   ↓
current assurance = LOW
   ↓
DENY / REAUTH_REQUIRED obligation
```

AXPOLICY không tự thực hiện reauthentication.

AXAUTH thực hiện reauthentication.

---

# 96. Canonical flow — Policy hot reload

```text
policy v41 ACTIVE
      │
      ▼
load v42
      │
      ▼
validate
      │
      ▼
compile
      │
      ▼
tests
      │
      ▼
publish atomically
      │
      ▼
v42 ACTIVE
```

Request đang evaluate bằng v41 vẫn hoàn thành với v41.

---

# 97. Canonical flow — External attribute

```text
request
   ↓
AXPOLICY
   ↓
missing device.attestation
   ↓
explicit attribute provider
   ↓
AXTRUST
   ↓
attribute result
   ↓
AXPOLICY
   ↓
decision
```

Policy engine không tự mở network.

---

# 98. Canonical flow — Capability + policy

```text
AXAUTH
   ↓
principal
   ↓
AXCAPABILITY
   ↓
READ authority
   ↓
AXPOLICY
   │
   ├── principal match
   ├── resource match
   ├── operation match
   ├── capability match
   └── contextual conditions
   ↓
decision
   ↓
AXSECURITY
   ↓
enforcement
```

---

# 99. Performance target

Common case:

```text
compiled policy
+
indexed selector
+
capability bitset
+
immutable context
```

phải có thể evaluate mà không:

- parse policy;
- allocate per rule;
- network;
- lock global registry;
- cryptographically verify lại mọi request nếu cache hợp lệ.

---

# 100. Hot-path architecture

```text
request
 ↓
policy snapshot
 ↓
operation index
 ↓
resource index
 ↓
candidate rules
 ↓
rights mask
 ↓
typed condition evaluation
 ↓
decision
```

---

# 101. Cold-path architecture

```text
source policy
 ↓
parse
 ↓
validate
 ↓
compile
 ↓
test
 ↓
sign
 ↓
activate
```

Phần này có thể tốn CPU vì không nằm trên request hot path.

---

# 102. Memory architecture

Compiled policy:

```text
read-only
shareable
memory-mapped
```

có thể được share giữa processes nếu security domain cho phép.

Temporary evaluation state:

```text
stack
TLS/local arena
small fixed buffers
```

---

# 103. NUMA

Large policy engines có thể:

- replicate read-only compiled policy;
- maintain per-NUMA caches;
- avoid cross-NUMA mutable state.

Không cần global mutable evaluator state.

---

# 104. Concurrency

Policy snapshot immutable.

Do đó nhiều threads có thể evaluate cùng snapshot đồng thời.

Mutation chỉ xảy ra ở activation boundary.

---

# 105. Policy registry

```text
policy_registry {
    policy_id
    active_version
    versions[]
}
```

Registry management là control-plane.

Evaluation là data-plane.

---

# 106. Control plane vs data plane

### Control plane

- compile;
- sign;
- validate;
- activate;
- rollback;
- distribute.

### Data plane

- evaluate;
- cache;
- return decision.

Đây là phân tách hiệu năng quan trọng.

---

# 107. Security decision cache

Cache entry:

```text
decision_cache_key {
    policy_version
    principal_id
    session_epoch
    capability_epoch
    resource_id
    resource_generation
    operation
    context_hash
}
```

---

# 108. Cache correctness

Không cache `ALLOW` nếu một dependency mutable không nằm trong cache key.

Không dùng cache để bypass revocation.

---

# 109. Formal invariants

### POL-INV-01
AXPOLICY không thực hiện authentication.

### POL-INV-02
AXPOLICY không cấp capability.

### POL-INV-03
AXPOLICY không tự thực hiện resource operation.

### POL-INV-04
AXSECURITY là enforcement boundary.

### POL-INV-05
Policy evaluation phải deterministic với cùng snapshot/context.

### POL-INV-06
Policy snapshot phải immutable trong evaluation.

### POL-INV-07
Policy version phải được xác định rõ.

### POL-INV-08
Rule ordering phải deterministic.

### POL-INV-09
Hash-map iteration order không được ảnh hưởng decision.

### POL-INV-10
Missing attributes phải có explicit semantics.

### POL-INV-11
Unknown condition không được tự động trở thành allow.

### POL-INV-12
Policy không được tự ý tạo external side effect.

### POL-INV-13
Policy không được tự ý gọi network.

### POL-INV-14
Policy không được tự ý đọc resource protected ngoài supplied context.

### POL-INV-15
Capability authority không thể được policy tăng thêm.

### POL-INV-16
Policy không thể biến READ authority thành WRITE authority.

### POL-INV-17
Resource identity phải stable.

### POL-INV-18
Resource generation phải được tôn trọng khi policy yêu cầu.

### POL-INV-19
Principal identity phải đến từ authoritative security context.

### POL-INV-20
Session authentication state phải đến từ AXAUTH.

### POL-INV-21
Trust state phải đến từ AXTRUST.

### POL-INV-22
Capability state phải đến từ AXCAPABILITY.

### POL-INV-23
Policy activation phải atomic.

### POL-INV-24
Hot reload không được mutate snapshot đang chạy.

### POL-INV-25
Rollback phải tạo explicit policy version transition.

### POL-INV-26
Policy compilation phải type-check conditions.

### POL-INV-27
Invalid policy không được activate.

### POL-INV-28
Policy ABI version phải được validate.

### POL-INV-29
Decision cache phải bind vào relevant policy version.

### POL-INV-30
Decision cache không được bypass revocation/epoch changes.

### POL-INV-31
Obligation bắt buộc phải được truyền tới enforcement layer.

### POL-INV-32
`ALLOW` không được trả nếu required obligation không thể satisfy.

### POL-INV-33
Untrusted remote policy decisions không được mặc định authoritative.

### POL-INV-34
Policy explanation không được làm lộ protected security data trái policy.

### POL-INV-35
Policy trace không được ghi secret material.

### POL-INV-36
Simulation không được mutate production policy state.

### POL-INV-37
AI không được activate hoặc weaken policy trái authority.

### POL-INV-38
Policy failure semantics phải explicit.

### POL-INV-39
AXPOLICY không được phụ thuộc hidden network/clock side effects.

### POL-INV-40
`AXPOLICY 5.0` phải duy trì separation giữa authority, policy decision và enforcement.

---

# 110. Definition of Done

`AXPOLICY 5.0` hoàn tất khi có:

- authorization request;
- principal selectors;
- resource selectors;
- operation model;
- rule model;
- allow/deny;
- NOT_APPLICABLE;
- INDETERMINATE;
- combining algorithms;
- priorities;
- conditions;
- typed policy values;
- three-valued condition evaluation;
- capability conditions;
- authentication-assurance conditions;
- role/group/attribute support;
- resource-state conditions;
- environmental context;
- purpose binding;
- tenant conditions;
- policy inheritance;
- deny boundaries;
- obligations;
- policy decision tokens;
- policy versioning;
- immutable snapshots;
- hot reload;
- rollback;
- policy signing;
- provenance;
- policy AST;
- PolicyIR;
- policy compiler;
- optimization;
- rule indexing;
- decision trees;
- compiled `.axpolicy`;
- stable policy ABI;
- decision cache;
- cache invalidation;
- deterministic simulation;
- what-if simulation;
- policy testing;
- policy lint;
- conflict/shadow detection;
- explanation;
- tracing;
- audit integration;
- async attribute acquisition boundary;
- control-plane/data-plane separation;
- NUMA/concurrency optimization;
- AXAUTH integration;
- AXCAPABILITY integration;
- AXTRUST integration;
- AXSECURITY enforcement boundary;
- 40 invariants.

**AXPOLICY 5.0 → FROZEN.**

---

# BOOTSTRAP-758 — AXSECURITY

**Native Security Enforcement, Access Control, Sandbox, Capability Enforcement, Security Context & Mandatory Security Runtime 5.0**

Kiến trúc kế tiếp sẽ hợp nhất các primitive vừa hoàn thành:

```text
AXIDENTITY
     │
AXTRUST
     │
AXAUTH
     │
AXCAPABILITY
     │
AXPOLICY
     │
     ▼
┌─────────────────────────────────────────┐
│              AXSECURITY                 │
│                                         │
│  Security Context                       │
│  Authorization Enforcement              │
│  Capability Enforcement                 │
│  Sandbox                                 │
│  Resource Protection                     │
│  Process Isolation                       │
│  Security Domains                        │
│  Mandatory Security Controls             │
│  Audit Boundary                          │
└───────────────────┬─────────────────────┘
                    │
                    ▼
       AXPROCESS / AXMEMORY / AXIPC
       AXNETWORK / AXSTORAGE / AXDEVICE
       AXWINDOW / AXAPPLICATION / ...
```

Đây là task sẽ đóng **security enforcement plane** của Axiom: `AXAUTH` xác thực, `AXCAPABILITY` mang authority, `AXPOLICY` tính decision, còn `AXSECURITY` sẽ là nơi **ngăn hoặc cho phép operation thực sự xảy ra**.