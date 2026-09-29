# BOOTSTRAP-754 — AXTRUST

**Title:** Native Trust Policy, Trust Evaluation, Authorization Evidence, Revocation Policy, Identity Binding & Security Decision Runtime 5.0  
**Namespace:** `AXTRUST`  
**Phase:** Axiom Civilization Runtime / Native Trust Evaluation & Security Decision Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXTRUST` là tầng biến **credentials/evidence** thành **trust evaluation results** theo một policy xác định.

Nó nằm giữa:

```text
AXCERT
AXIDENTITY
AXCRYPTO
       │
       ▼
    AXTRUST
       │
       ▼
 AXSECURITY
```

AXTRUST chịu trách nhiệm:

- trust policy;
- trust evaluation;
- trust-anchor selection;
- certificate/credential policy;
- identity-to-key binding;
- revocation policy;
- freshness policy;
- evidence composition;
- attestation evaluation;
- claim evaluation;
- purpose validation;
- policy conditions;
- trust decisions;
- policy versioning;
- deterministic evaluation;
- explainable decision records;
- policy simulation;
- trust caching;
- distributed trust evidence;
- security decision inputs.

Điểm cốt lõi:

> **AXTRUST quyết định mức độ trust dựa trên policy và evidence; AXSECURITY dùng kết quả đó để quyết định authorization và enforcement.**

---

# 2. Kiến trúc tổng thể

```text
                    AXIDENTITY
                        │
                        ▼
                     identity
                        │
                        ▼
                     AXTRUST
                  ┌─────┼─────┐
                  │     │     │
                  ▼     ▼     ▼
               AXCERT AXCRYPTO evidence
                  │     │     │
                  └─────┼─────┘
                        │
                        ▼
                  trust evaluation
                        │
                        ▼
                  trust decision
                        │
                        ▼
                   AXSECURITY
                        │
              ┌─────────┼─────────┐
              ▼         ▼         ▼
         authorization capability sandbox
```

---

# 3. Strong boundary

## AXTRUST sở hữu

- trust policy;
- policy compilation;
- trust evaluation;
- evidence requirements;
- trust-anchor selection;
- certificate-purpose validation;
- identity/key binding evaluation;
- revocation acceptance policy;
- freshness evaluation;
- attestation policy;
- claim matching;
- trust levels;
- decision explanations;
- policy versioning;
- evaluation caching;
- trust simulation.

## AXTRUST không sở hữu

### AXCRYPTO

Primitive:

```text
hash
MAC
AEAD
signature
KDF
random
key operations
```

### AXCERT

Credential mechanics:

```text
certificate parsing
certificate chain mechanics
attestation structure
revocation evidence structure
```

### AXIDENTITY

Identity lifecycle:

```text
identity creation
identity update
identity deletion
identity identifiers
credential enrollment
```

### AXSECURITY

Enforcement:

```text
authorization
capability issuance
sandbox
access control
security enforcement
```

---

# 4. Trust ≠ Authorization

Đây là boundary bắt buộc.

Ví dụ:

```text
certificate valid
        ↓
AXCERT
        ↓
credential trusted
        ↓
AXTRUST
        ↓
identity authorized for resource?
        ↓
AXSECURITY
```

Một entity có thể:

```text
TRUSTED
```

nhưng vẫn:

```text
NOT_AUTHORIZED
```

---

# 5. Trust result

Core:

```text
trust_result {
    status
    subject
    evidence
    policy
    reasons
    constraints
    timestamp
}
```

Status baseline:

```text
TRUSTED
NOT_TRUSTED
UNKNOWN
CONDITIONAL
INVALID
EXPIRED
REVOKED
POLICY_DENIED
INSUFFICIENT_EVIDENCE
```

---

# 6. Không dùng boolean

Không thiết kế:

```text
bool is_trusted()
```

làm API duy nhất.

Trust evaluation cần biết:

- tại sao;
- dựa trên evidence nào;
- policy nào;
- thời điểm nào;
- constraint nào;
- failure nào.

---

# 7. Trust decision

```text
trust_decision {
    decision_id
    result
    policy_id
    policy_version
    subject
    evidence_ids[]
    reasons[]
    constraints[]
    evaluated_at
}
```

Decision phải reproducible khi inputs giống nhau.

---

# 8. Policy identity

```text
trust_policy {
    policy_id
    version
    profile
    rules[]
}
```

`policy_id + version` là một phần của evaluation identity.

---

# 9. Policy versioning

Không overwrite semantics của policy đang được dùng.

Ví dụ:

```text
policy/network/v1
policy/network/v2
```

Một historical decision vẫn phải xác định được policy version đã tạo ra nó.

---

# 10. Policy language

AXTRUST cần một DSL/IR đơn giản, deterministic.

Ví dụ concept:

```text
trust policy server_identity {
    require certificate
    require valid_chain
    require purpose SERVER_AUTH
    require revocation_status GOOD
    require key_algorithm allowed
    require freshness < 24h
}
```

Đây là **policy language**, không phải general-purpose programming language.

---

# 11. Trust Policy IR

Compiler policy hạ xuống:

```text
TrustPolicyIR
```

gồm:

```text
LOAD_EVIDENCE
CHECK_SIGNATURE
CHECK_VALIDITY
CHECK_ISSUER
CHECK_PURPOSE
CHECK_REVOCATION
CHECK_FRESHNESS
CHECK_CLAIM
CHECK_MEASUREMENT
AND
OR
NOT
REQUIRE
DENY
RETURN
```

---

# 12. Deterministic policy execution

Policy evaluation không được phụ thuộc:

- random;
- thread scheduling;
- hash-map iteration order;
- unspecified clock;
- network timing.

Mọi external input phải nằm trong `evaluation_context`.

---

# 13. Evaluation context

```text
trust_context {
    subject
    resource
    purpose
    timestamp
    evidence[]
    anchors[]
    environment
}
```

---

# 14. Purpose

Trust không tồn tại tuyệt đối.

Ví dụ:

```text
SERVER_AUTH
CLIENT_AUTH
CODE_SIGNING
DEVICE_AUTH
USER_AUTH
DATA_PROTECTION
SERVICE_AUTH
```

Một certificate có thể trusted cho purpose A nhưng không trusted cho B.

---

# 15. Resource context

Trust evaluation có thể phụ thuộc:

```text
resource
service
namespace
tenant
device
application
```

Nhưng resource authorization cuối cùng thuộc AXSECURITY.

AXTRUST chỉ cung cấp trust evidence/result.

---

# 16. Identity binding

AXTRUST có nhiệm vụ kiểm tra:

```text
identity
   ⇅
credential
   ⇅
public key
```

Ví dụ:

```text
Identity X
    │
    ▼
Credential C
    │
    ▼
Public Key K
```

---

# 17. Key binding verification

AXTRUST gọi:

```text
AXCRYPTO
```

để kiểm tra cryptographic proof.

Không tự implement signature.

---

# 18. Identity provider

AXTRUST không sở hữu identity database.

Nó consume:

```text
identity_reference
```

từ AXIDENTITY.

---

# 19. Claim matching

Generic:

```text
claim {
    namespace
    name
    value
}
```

Policy có thể yêu cầu:

```text
claim.namespace == "device"
claim.name == "class"
claim.value == "trusted"
```

Value comparison phải có typed semantics.

---

# 20. Claim type safety

Không so sánh:

```text
integer 10
```

với:

```text
string "10"
```

như cùng một value.

Core types:

```text
bool
integer
string
bytes
identifier
timestamp
duration
set
map
structured
```

---

# 21. Claim normalization

Normalization phải explicit.

Ví dụ:

```text
DNS name
URI
identifier
case-sensitive string
```

không được tự động normalize theo assumption của implementation.

---

# 22. Evidence

Generic:

```text
trust_evidence {
    evidence_id
    type
    issuer
    subject
    issued_at
    expires_at
    payload
    provenance
}
```

Evidence types:

```text
CERTIFICATE
SIGNATURE
ATTESTATION
REVOCATION
IDENTITY_ASSERTION
DEVICE_MEASUREMENT
POLICY_ASSERTION
```

---

# 23. Evidence provenance

Mỗi evidence nên có:

```text
source
issuer
acquired_at
valid_from
valid_until
```

để policy đánh giá freshness.

---

# 24. Evidence freshness

```text
freshness {
    produced_at
    observed_at
    expires_at
}
```

Policy có thể yêu cầu:

```text
max_age
```

AXTRUST không tự quyết định con số mặc định phù hợp mọi use case.

---

# 25. Revocation policy

AXCERT cung cấp:

```text
GOOD
REVOKED
UNKNOWN
STALE
INVALID
```

AXTRUST quyết định cách policy xử lý.

Ví dụ:

```text
if status == REVOKED
    DENY
```

hoặc:

```text
if status == UNKNOWN
    CONDITIONAL
```

---

# 26. Fail-open / fail-closed

Đây là **policy**, không phải hard-coded AXCERT behavior.

```text
revocation_failure_policy {
    FAIL_CLOSED
    FAIL_OPEN
    CONDITIONAL
}
```

Profile security-sensitive có thể yêu cầu fail-closed.

AXTRUST chỉ thực thi policy được cấu hình.

---

# 27. Offline mode

Policy có thể chỉ cho phép:

```text
local evidence
```

Không được tự động network fetch.

---

# 28. Online mode

Nếu policy cho phép remote evidence:

```text
AXNETWORK
   ↓
AXASYNC
   ↓
evidence
   ↓
AXTRUST
```

AXTRUST vẫn không sở hữu network transport.

---

# 29. Trust-anchor selection

Input:

```text
candidate anchors[]
```

Policy có thể lọc theo:

```text
purpose
issuer
namespace
algorithm
validity
tenant
environment
```

AXTRUST chọn candidate theo deterministic policy.

---

# 30. Anchor ambiguity

Nếu nhiều anchor đều hợp lệ:

```text
anchor A
anchor B
```

không được phụ thuộc iteration order.

Policy phải xác định:

```text
priority
explicit preference
deterministic tie-break
```

hoặc trả:

```text
AMBIGUOUS
```

---

# 31. Trust levels

AXTRUST có thể biểu diễn:

```text
trust_level
```

Ví dụ:

```text
NONE
UNVERIFIED
ASSERTED
VERIFIED
STRONGLY_VERIFIED
HARDWARE_VERIFIED
```

Nhưng level chỉ có meaning trong policy profile.

Không coi:

```text
5 > 4
```

là universal security truth.

---

# 32. Evidence strength

Evidence có thể có metadata:

```text
evidence_strength
```

nhưng không hard-code một global ranking.

Mỗi policy định nghĩa cách evidence đóng góp.

---

# 33. Policy composition

Policies có thể compose:

```text
base_policy
+
environment_policy
+
application_policy
```

Compiler tạo:

```text
effective_policy
```

với conflict semantics rõ ràng.

---

# 34. Deny precedence

Khi policy compose:

```text
ALLOW
DENY
```

phải có explicit conflict rule.

Baseline:

```text
explicit DENY
```

không được vô tình biến thành ALLOW do rule ordering.

---

# 35. Rule ordering

Policy engine không được phụ thuộc textual ordering nếu semantics không khai báo ordering.

Các rule có thể được compile thành decision graph.

---

# 36. Policy conditions

Core conditions:

```text
equals
not_equals
in_set
contains
prefix
range
before
after
exists
matches_type
```

Regex chỉ là optional feature, không cần dependency runtime.

---

# 37. Policy arithmetic

Chỉ hỗ trợ arithmetic cần thiết:

```text
integer
duration
timestamp
size
```

Không biến AXTRUST DSL thành general-purpose scripting engine.

---

# 38. Policy recursion

Không cho recursive policy execution mặc định.

Policy references phải được DAG hoặc có bounded recursion.

Cycle:

```text
A → B → C → A
```

phải được reject.

---

# 39. Policy compilation

```text
source policy
      ↓
parse
      ↓
type check
      ↓
policy IR
      ↓
optimize
      ↓
decision bytecode/native code
```

---

# 40. Policy optimization

Compiler có thể:

- constant fold;
- eliminate unreachable rules;
- merge equivalent checks;
- pre-index claim lookup;
- pre-index trust anchors;
- precompute algorithm sets;
- compile predicates;
- short-circuit safe boolean expressions.

---

# 41. Runtime hot path

Trust evaluation không nên:

```text
parse policy
allocate AST
interpret strings
```

mỗi request.

Policy compile một lần:

```text
policy
 ↓
compiled_policy
 ↓
many evaluations
```

---

# 42. Trust cache

```text
trust_cache_key {
    subject
    credential_fingerprint
    policy_id
    policy_version
    purpose
    resource_scope
    time_bucket
    evidence_state
}
```

Không cache chỉ bằng certificate fingerprint.

---

# 43. Cache security

Cache hit chỉ hợp lệ nếu:

```text
policy unchanged
evidence still valid
credential unchanged
purpose same
resource scope compatible
```

---

# 44. Negative cache

Có thể cache:

```text
NOT_TRUSTED
```

nhưng phải có expiration phù hợp.

Một temporary failure không được cache như permanent revocation.

---

# 45. Decision explanation

AXTRUST phải tạo explanation tree:

```text
decision
 ├── policy rule
 ├── evidence
 │    ├── certificate
 │    ├── signature
 │    └── revocation
 └── checks
```

---

# 46. Explainability

Ví dụ:

```text
DENIED
 ├─ certificate chain: VALID
 ├─ signature: VALID
 ├─ validity: VALID
 ├─ purpose: INVALID
 └─ policy: SERVER_AUTH_REQUIRED
```

Điều này giúp developer/debugging nhưng không expose sensitive material.

---

# 47. Decision provenance

```text
decision_provenance {
    policy_id
    policy_version
    evidence_ids
    evaluation_time
    engine_version
}
```

Có thể audit/replay.

---

# 48. Trust decision ≠ audit event

AXTRUST tạo decision record.

AXSECURITY/AXAUDIT mới sở hữu authoritative security audit storage nếu module audit được thiết kế riêng.

---

# 49. Security event

AXTRUST có thể emit:

```text
trust_evaluation_completed
trust_evaluation_failed
credential_revoked
policy_mismatch
insufficient_evidence
```

nhưng không tự sở hữu event bus.

---

# 50. Attestation policy

Policy có thể yêu cầu:

```text
require attestation
require measurement
require nonce
require freshness
require hardware_bound_key
```

---

# 51. Measurement policy

Ví dụ:

```text
measurement {
    component = "boot"
    digest = expected
}
```

AXTRUST so sánh evidence với policy.

Meaning của measurement vẫn do policy profile xác định.

---

# 52. Hardware-backed requirement

Policy có thể yêu cầu:

```text
key_origin == HARDWARE
```

hoặc:

```text
attestation.level >= HARDWARE_VERIFIED
```

nhưng interpretation của level phải nằm trong profile.

---

# 53. Device trust

Một device có thể có:

```text
identity
certificate
attestation
measurements
revocation status
```

AXTRUST hợp nhất evidence.

---

# 54. Composite trust

```text
device
 AND
identity
 AND
certificate
 AND
fresh_attestation
```

Policy engine tạo:

```text
composite_result
```

---

# 55. Threshold policy

Một số policy cần:

```text
2 of 3 evidence sources
```

AXTRUST hỗ trợ:

```text
threshold(k, evidence_set)
```

Ví dụ:

```text
require 2 of:
    certificate
    hardware_attestation
    organization_assertion
```

Không gán universal evidence ranking.

---

# 56. Quorum semantics

Threshold phải deterministic.

Nếu evidence duplicate:

```text
same evidence_id
```

không được tính nhiều lần.

---

# 57. Delegation

Trust có thể delegate:

```text
Root
 ↓
Organization
 ↓
Service
 ↓
Credential
```

Delegation constraints:

```text
scope
purpose
expiration
namespace
```

phải được preserve.

---

# 58. Delegation attenuation

Delegated trust không được tự động mở rộng scope.

```text
parent scope
   ↓
child scope ⊆ parent scope
```

---

# 59. Trust attenuation invariant

Một delegated credential không được cấp trust rộng hơn issuer được phép delegate.

---

# 60. Multi-tenant trust

AXTRUST phải hỗ trợ:

```text
tenant_id
policy_id
anchor_set_id
```

để hai tenants có thể có trust roots khác nhau.

Không dùng global singleton trust store làm semantic requirement.

---

# 61. Environment profiles

Policy profile có thể khác theo:

```text
DEVELOPMENT
TEST
PRODUCTION
OFFLINE
HARDENED
```

Development profile không được vô tình được embedded vào production artifact.

---

# 62. Secure policy deployment

Compiled policy nên có:

```text
policy_hash
policy_version
signature
```

để AXSECURITY có thể kiểm tra provenance.

AXTRUST verify signature bằng AXCRYPTO.

---

# 63. Policy signing

Policy artifact:

```text
policy bytes
    ↓
signature
    ↓
signed policy
```

AXTRUST kiểm tra cryptographic validity.

Authority của signer thuộc AXSECURITY.

---

# 64. Policy rollback

Policy runtime phải hỗ trợ:

```text
active version
previous version
candidate version
```

Rollback không làm mất historical decision metadata.

---

# 65. Policy hot reload

Có thể:

```text
load new policy
compile
validate
activate
```

Evaluation đang chạy tiếp tục dùng immutable policy snapshot.

Không thay policy giữa evaluation.

---

# 66. Evaluation snapshot

Mỗi evaluation có:

```text
policy snapshot
evidence snapshot
time snapshot
```

Điều này đảm bảo deterministic result.

---

# 67. Concurrency

Compiled policies immutable:

```text
many readers
```

Trust cache có concurrent implementation.

Mutable policy registry phải có explicit synchronization.

---

# 68. Async evidence

Evidence acquisition có thể chạy:

```text
AXTASK
AXASYNC
AXNETWORK
```

Nhưng final policy evaluation là một operation trên explicit evidence set.

---

# 69. No hidden network

```text
evaluate()
```

không được âm thầm:

```text
DNS
HTTP
OCSP
remote API
```

Nếu cần remote evidence:

```text
collect_evidence_async()
       ↓
evaluate()
```

hai bước explicit.

---

# 70. No hidden clock

Tương tự:

```text
evaluate(context)
```

nhận timestamp từ context.

Không tự gọi system clock giữa các policy rules.

---

# 71. Security decision handoff

AXTRUST output:

```text
trust_result
```

AXSECURITY input:

```text
authorization_context {
    subject
    resource
    operation
    trust_result
}
```

---

# 72. Authorization boundary

Ví dụ:

```text
AXTRUST:
    certificate valid
    identity trusted
    device attested

AXSECURITY:
    user may READ resource X
```

AXTRUST không trả:

```text
READ_GRANTED
```

trừ khi API nằm trong một explicitly composed security layer.

---

# 73. Capability integration

AXSECURITY có thể yêu cầu:

```text
trust_result
```

trước khi cấp capability.

```text
credential
 ↓
AXCERT
 ↓
AXTRUST
 ↓
trust_result
 ↓
AXSECURITY
 ↓
capability
```

---

# 74. Trust revocation propagation

Khi evidence bị revoked:

```text
revocation update
      ↓
AXCERT
      ↓
AXTRUST cache invalidation
      ↓
new evaluation
      ↓
AXSECURITY
```

AXTRUST phải có invalidation API.

---

# 75. Event-driven invalidation

Core có thể nhận:

```text
credential_changed
trust_anchor_changed
policy_changed
revocation_changed
identity_binding_changed
```

để invalidate dependent decisions.

---

# 76. Distributed trust

AXTRUST không giả định mọi evidence local.

Có thể nhận:

```text
remote_evidence_reference
```

nhưng phải distinguish:

```text
reference
vs
verified evidence
```

---

# 77. Remote evidence

Remote evidence phải có:

```text
issuer
signature
freshness
provenance
```

Không trust chỉ vì HTTPS transport.

---

# 78. Evidence substitution

Evidence phải có stable identity/fingerprint để chống việc thay đổi object giữa acquisition và evaluation.

---

# 79. TOCTOU protection

Giữa:

```text
evidence acquired
```

và:

```text
evidence evaluated
```

phải dùng immutable snapshot/reference.

---

# 80. Formal invariants

### TRUST-INV-01
AXTRUST là trust-evaluation layer, không phải cryptographic primitive layer.

### TRUST-INV-02
AXTRUST không reimplement AXCRYPTO primitives.

### TRUST-INV-03
Certificate mechanics thuộc AXCERT.

### TRUST-INV-04
Identity lifecycle thuộc AXIDENTITY.

### TRUST-INV-05
Authorization enforcement thuộc AXSECURITY.

### TRUST-INV-06
Trust decision phải bind với policy ID.

### TRUST-INV-07
Trust decision phải bind với policy version.

### TRUST-INV-08
Evaluation phải sử dụng explicit evaluation context.

### TRUST-INV-09
Evaluation timestamp phải explicit trong deterministic mode.

### TRUST-INV-10
Evaluation không được tự ý thực hiện network access.

### TRUST-INV-11
Evaluation không được tự ý lấy system clock giữa các checks.

### TRUST-INV-12
Policy execution phải deterministic với cùng input snapshot.

### TRUST-INV-13
Policy cycles phải được phát hiện.

### TRUST-INV-14
Policy recursion phải bounded.

### TRUST-INV-15
Unknown evidence không được tự động trở thành trusted evidence.

### TRUST-INV-16
Evidence provenance phải được preserved.

### TRUST-INV-17
Evidence freshness phải được đánh giá theo policy.

### TRUST-INV-18
Revocation policy phải explicit.

### TRUST-INV-19
Temporary evidence failure không được mặc định thành permanent revocation.

### TRUST-INV-20
Trust anchor selection phải deterministic.

### TRUST-INV-21
Trust anchor policy không được hard-code thành global universal rule.

### TRUST-INV-22
Identity-to-key binding phải có cryptographic/credential evidence phù hợp.

### TRUST-INV-23
Delegated trust không được mở rộng scope vượt parent authority.

### TRUST-INV-24
Duplicate evidence không được count nhiều lần trong threshold policy.

### TRUST-INV-25
Trust levels chỉ có meaning trong policy profile tương ứng.

### TRUST-INV-26
Composite trust phải preserve provenance của từng evidence.

### TRUST-INV-27
Trust cache key phải bao gồm policy identity.

### TRUST-INV-28
Trust cache phải invalidate khi policy thay đổi.

### TRUST-INV-29
Trust cache phải invalidate khi relevant evidence thay đổi.

### TRUST-INV-30
Historical decisions phải giữ policy provenance.

### TRUST-INV-31
Policy hot reload không được thay đổi policy snapshot của evaluation đang chạy.

### TRUST-INV-32
Compiled policies phải immutable trong evaluation hot path.

### TRUST-INV-33
AI không được thay đổi trust policy hoặc trust result.

### TRUST-INV-34
AI không được bypass evidence requirements.

### TRUST-INV-35
Remote evidence reference không đồng nghĩa verified evidence.

### TRUST-INV-36
Evidence phải immutable hoặc snapshot để tránh TOCTOU.

### TRUST-INV-37
Trust result không đồng nghĩa authorization grant.

### TRUST-INV-38
Explicit DENY trong policy composition không được biến thành ALLOW do rule-order ambiguity.

### TRUST-INV-39
Policy artifact có thể được cryptographically authenticated nhưng authority của signer vẫn thuộc AXSECURITY.

### TRUST-INV-40
`AXTRUST 5.0` phải giữ boundary độc lập giữa trust evaluation và authorization enforcement.

---

# 81. Native API

Baseline:

```text
trust_policy_compile()
trust_policy_load()
trust_policy_activate()
trust_policy_get()

trust_context_create()
trust_context_set_subject()
trust_context_set_resource()
trust_context_set_purpose()
trust_context_set_time()
trust_context_add_evidence()
trust_context_add_anchor()

trust_evaluate()

trust_result_get_status()
trust_result_get_reasons()
trust_result_get_constraints()
trust_result_get_evidence()
trust_result_get_policy()

trust_verify_identity_binding()
trust_evaluate_claim()
trust_evaluate_attestation()
trust_evaluate_revocation()

trust_cache_create()
trust_cache_lookup()
trust_cache_invalidate()

trust_policy_sign()
trust_policy_verify()

trust_simulate()
trust_replay()

trust_get_engine_info()
trust_get_policy_capabilities()
```

---

# 82. Policy DSL

Một policy Axiom có thể có dạng concept:

```text
policy server_auth v1 {
    purpose SERVER_AUTH

    require certificate

    require certificate.valid

    require certificate.chain.valid

    require certificate.key_usage DIGITAL_SIGNATURE

    require certificate.extended_usage SERVER_AUTH

    require revocation.status GOOD

    require credential.freshness <= 24h

    trust
}
```

Compiler chuyển policy thành `TrustPolicyIR`.

---

# 83. Composite policy

```text
policy device_service_auth v1 {

    require identity.valid

    require certificate.valid

    require attestation.valid

    require measurement.boot == expected

    require revocation.status GOOD

    require key.origin HARDWARE

    trust
}
```

---

# 84. Conditional policy

```text
policy service_access v1 {

    if environment == PRODUCTION {
        require attestation
        require revocation.status GOOD
    }

    if environment == DEVELOPMENT {
        require certificate.valid
    }

    trust
}
```

Việc policy nào được deploy production là responsibility của deployment/security layer.

---

# 85. Threshold policy

```text
policy high_assurance v1 {

    require 2 of {
        certificate
        hardware_attestation
        organization_credential
    }

    trust
}
```

---

# 86. Canonical evaluation flow

```text
                  policy
                    │
                    ▼
              compiled policy
                    │
                    │
evidence ───────────┤
identity ───────────┤
resource ───────────┤
purpose ────────────┤
timestamp ──────────┤
                    ▼
             AXTRUST EVALUATOR
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       AXCERT    AXCRYPTO   AXIDENTITY
          │         │         │
          └─────────┼─────────┘
                    ▼
              trust_result
                    │
                    ▼
                AXSECURITY
```

---

# 87. Canonical revocation flow

```text
revocation evidence
        │
        ▼
      AXCERT
        │
        ▼
validated status
        │
        ▼
      AXTRUST
        │
        ▼
policy evaluation
        │
        ▼
trust result
        │
        ▼
    AXSECURITY
```

---

# 88. Canonical policy update

```text
policy source
     │
     ▼
parse
     │
     ▼
type-check
     │
     ▼
compile
     │
     ▼
self-validation
     │
     ▼
signature verification
     │
     ▼
activate version N+1
     │
     ▼
invalidate cache
```

---

# 89. Canonical attestation flow

```text
device
  │
  ▼
attestation evidence
  │
  ▼
AXCERT
  │
  ├── structure
  ├── signature
  └── measurement
          │
          ▼
       AXTRUST
          │
          ├── freshness
          ├── expected measurement
          ├── issuer
          └── policy
                  │
                  ▼
             trust_result
                  │
                  ▼
              AXSECURITY
```

---

# 90. Performance architecture

AXTRUST phải được thiết kế để evaluation hàng triệu lần mà không parse/recompile policy.

### Hot path

```text
compiled policy
       +
immutable evidence
       +
pre-indexed claims
       +
pre-indexed credentials
       ↓
native decision engine
```

### Tránh

```text
string-based rule interpretation
reflection
AST allocation
network calls
global locks
repeated certificate parsing
```

---

# 91. Pre-indexing

`trust_context` có thể build indexes:

```text
claim_index
certificate_index
evidence_index
anchor_index
revocation_index
```

để policy lookup nhanh.

---

# 92. Parallel evaluation

Independent predicates:

```text
certificate validity ─┐
signature ─────────────┤
revocation ────────────┼── parallel
attestation ───────────┤
claims ────────────────┘
```

Có thể chạy trên AXTASK.

AXTRUST không sở hữu scheduler.

---

# 93. Short-circuit

Nếu policy:

```text
A AND B AND C
```

và `A = false`, có thể short-circuit.

Nhưng nếu explanation/audit profile yêu cầu full diagnostics, engine có thể tiếp tục đánh giá các predicates độc lập.

---

# 94. Diagnostic profiles

```text
FAST
NORMAL
EXPLAIN
AUDIT
DETERMINISTIC
SIMULATION
```

`FAST` tối ưu latency.

`EXPLAIN` giữ nhiều provenance.

---

# 95. Memory model

Trust evaluation objects:

- immutable where possible;
- arena-backed per evaluation;
- compact IDs;
- no repeated string copies;
- zero-copy evidence references.

AXMEMORY quản lý backing storage.

---

# 96. Persistent policy

Policy artifact có thể được lưu qua:

```text
AXSTORAGE
```

hoặc:

```text
AXDATABASE
```

AXTRUST chỉ quản lý compiled representation.

---

# 97. FFI / ABI

Stable handles:

```text
ax_trust_policy_handle
ax_trust_context_handle
ax_trust_result_handle
ax_trust_cache_handle
ax_evidence_handle
```

Không expose internal AST/policy graph pointers.

---

# 98. AI tooling boundary

AI có thể:

```text
explain_result()
analyze_policy()
find_missing_evidence()
detect_conflicting_rules()
show_policy_diff()
simulate_policy()
```

AI không được:

```text
modify active policy silently
approve trust
remove revocation requirement
change trust anchor
grant authorization
```

Mọi thay đổi policy phải là explicit artifact/deployment operation.

---

# 99. Simulation

AXTRUST phải hỗ trợ:

```text
trust_simulation
```

Input:

```text
policy
identity
credentials
attestation
revocation
timestamp
```

Output:

```text
decision
explanation
policy trace
```

Không chạm production trust state.

---

# 100. Replay

Một evaluation record đủ metadata có thể replay:

```text
policy version
evidence IDs
evidence snapshot
identity reference
resource
purpose
timestamp
engine version
```

để debug.

---

# 101. Security of replay

Replay artifact không được chứa:

- private keys;
- secrets;
- authorization capabilities.

Nếu evidence bản thân chứa sensitive information, policy phải quyết định redaction/storage.

---

# 102. Definition of Done

`AXTRUST 5.0` hoàn tất khi có:

- trust policy model;
- policy DSL;
- policy parser;
- policy type checker;
- TrustPolicyIR;
- policy compiler;
- deterministic evaluator;
- explicit evaluation context;
- trust result;
- decision provenance;
- explanation tree;
- trust-anchor selection;
- certificate-purpose evaluation;
- identity/key binding;
- claim evaluation;
- attestation evaluation;
- measurement evaluation;
- freshness evaluation;
- revocation policy;
- fail-open/fail-closed policy semantics;
- offline evaluation;
- explicit remote-evidence boundary;
- trust levels;
- evidence strength metadata;
- threshold policies;
- delegation;
- scope attenuation;
- multi-tenant trust;
- environment profiles;
- policy signing;
- policy verification;
- policy versioning;
- hot reload;
- immutable evaluation snapshots;
- trust cache;
- cache invalidation;
- deterministic simulation;
- replay;
- concurrent evaluation;
- parallel predicate evaluation;
- compiled hot path;
- native ABI;
- AXCERT integration;
- AXCRYPTO integration;
- AXIDENTITY integration;
- AXSECURITY handoff;
- AXNETWORK/AXASYNC boundary;
- AI tooling boundary;
- 40 invariants.

**AXTRUST 5.0 → FROZEN.**

---

# Kiến trúc Security Stack sau BOOTSTRAP-754

Axiom hiện có một phân tầng khá rõ:

```text
┌──────────────────────────────────────────────────┐
│                   AXSECURITY                     │
│ authorization / capabilities / sandbox / policy │
└───────────────────────┬──────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│                     AXTRUST                      │
│ trust evaluation / evidence / trust policy       │
└───────────────┬──────────────────┬───────────────┘
                │                  │
                ▼                  ▼
          ┌───────────┐      ┌────────────┐
          │  AXCERT   │      │ AXIDENTITY │
          │ credential│      │ identity   │
          │ mechanics │      │ lifecycle  │
          └─────┬─────┘      └────────────┘
                │
                ▼
          ┌────────────┐
          │  AXCRYPTO  │
          │ primitives │
          └────────────┘
```

Điểm đáng giữ nguyên trong core architecture:

```text
AXCRYPTO
    = "Can this cryptographic operation be verified?"

AXCERT
    = "What credential/evidence is this, and is its structure/chain valid?"

AXTRUST
    = "Given this evidence and this policy, what trust result follows?"

AXSECURITY
    = "What authority/access/enforcement follows from that result?"

AXIDENTITY
    = "Who/what is this identity and how is its lifecycle managed?"
```

Đây là boundary đủ mạnh để sau này Axiom có thể xây TLS, enterprise identity, device attestation, application sandbox, capability security, package signing và secure boot mà không phải biến `AXSECURITY` thành một module khổng lồ.

---

# BOOTSTRAP-755 — AXAUTH

**Native Authentication, Session Establishment, Credential Presentation, Challenge/Response, Login & Security Session Runtime 5.0**

Tầng tiếp theo sẽ xây phần **authentication**, tức biến identity credentials + trust evidence thành một **authenticated session**:

```text
identity
   +
credential
   +
challenge
   +
proof
   +
AXTRUST
      │
      ▼
  AXAUTH
      │
      ▼
authenticated principal/session
      │
      ▼
AXSECURITY
      │
      ▼
authorization
```

Và tiếp tục giữ boundary quan trọng:

```text
AXIDENTITY = identity
AXCRYPTO   = cryptographic proof
AXCERT     = credential mechanics
AXTRUST    = trust evaluation
AXAUTH     = authentication/session establishment
AXSECURITY = authorization/enforcement
```

**BOOTSTRAP-754 hoàn tất → chuỗi chuyển sang BOOTSTRAP-755.**