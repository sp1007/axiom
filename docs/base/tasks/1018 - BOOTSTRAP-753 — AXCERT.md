# BOOTSTRAP-753 — AXCERT

**Title:** Native Certificate, Credential, Trust Chain, Attestation & Trust-Object Runtime 5.0  
**Namespace:** `AXCERT`  
**Phase:** Axiom Civilization Runtime / Native Trust Object & Credential Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXCERT` là tầng quản lý **trust objects và credentials có cấu trúc** nằm giữa cryptographic primitives và security policy.

Nó giải quyết:

- certificate;
- public-key credentials;
- certificate chains;
- trust anchors;
- issuer/subject relationships;
- key binding;
- certificate extensions;
- validity periods;
- credential profiles;
- revocation evidence;
- OCSP/CRL-like evidence structures;
- attestation evidence;
- signed claims;
- trust-object parsing/validation;
- certificate path construction;
- certificate path validation *mechanics*;
- credential lifecycle metadata;
- evidence bundles;
- deterministic verification;
- trust diagnostics;
- hardware/platform attestation adapters.

Điểm cốt lõi:

> **AXCERT xác định và kiểm tra cấu trúc, chữ ký và quan hệ của trust objects; AXSECURITY quyết định có tin object đó và cấp quyền gì.**

---

# 2. Vị trí kiến trúc

```text
                         AXIDENTITY
                             │
                             ▼
                       ┌────────────┐
                       │ AXSECURITY │
                       └─────┬──────┘
                             │ policy
                             ▼
                          AXCERT
                             │
               ┌─────────────┼─────────────┐
               ▼             ▼             ▼
          certificates   credentials   attestation
               │             │             │
               └─────────────┼─────────────┘
                             ▼
                          AXCRYPTO
```

Representation:

```text
AXCODEC
   ↓
encoded certificate/credential
   ↓
AXCERT
   ↓
structured trust object
   ↓
AXCRYPTO
   ↓
cryptographic verification
```

---

# 3. Strong boundary

## AXCERT sở hữu

- certificate structure;
- credential structure;
- trust-object structure;
- chain construction;
- chain graph;
- issuer/subject relationships;
- signature linkage;
- key-binding validation;
- certificate extension interpretation;
- validity interval mechanics;
- revocation evidence structure;
- attestation evidence structure;
- trust evidence aggregation;
- certificate diagnostics.

## AXCERT không sở hữu

### AXCRYPTO

Sở hữu:

- hash;
- signature primitive;
- key operations;
- AEAD;
- MAC;
- KDF;
- secure random.

### AXSECURITY

Sở hữu:

- trust policy;
- authorization;
- identity policy;
- trust-anchor selection policy;
- allowed purposes;
- hostname/service identity policy;
- revocation policy;
- security decisions.

### AXNETWORK

Sở hữu:

- fetching certificates;
- OCSP/CRL transport;
- network protocol.

### AXSTORAGE

Sở hữu:

- persistent certificate/key storage.

---

# 4. Certificate ≠ Identity

Một certificate có thể chứa identity claims.

Nhưng:

```text
certificate
```

không đồng nghĩa:

```text
trusted identity
```

Ví dụ:

```text
Certificate:
    subject = X
    public_key = K
    issuer = Y
```

AXCERT có thể xác định:

```text
signature valid
chain structurally valid
key binding valid
```

Nhưng chỉ AXSECURITY mới quyết định:

```text
X được tin cho purpose P
```

---

# 5. Credential model

Core abstraction:

```text
credential {
    credential_id
    type
    subject
    issuer
    validity
    claims
    public_key
    evidence
    signature
}
```

Các loại:

```text
CERTIFICATE
SIGNED_CREDENTIAL
ATTESTATION
IDENTITY_CREDENTIAL
DEVICE_CREDENTIAL
SERVICE_CREDENTIAL
```

---

# 6. Trust object

Generic:

```text
trust_object {
    object_id
    object_type
    encoding
    version
    issuer
    subject
    signature
    payload
}
```

Không giả định mọi trust object là X.509.

---

# 7. Certificate abstraction

```text
certificate {
    version
    serial_number
    issuer
    subject
    validity
    public_key
    extensions
    signature_algorithm
    signature
}
```

Certificate phải giữ cả:

```text
raw_tbs_bytes
raw_signature
```

khi cần forensic/interoperability.

---

# 8. Raw representation

AXCERT không nên canonicalize certificate bằng cách thay đổi raw bytes.

Có hai view:

```text
certificate.raw
certificate.parsed
```

Điều này quan trọng vì chữ ký certificate thường được tính trên **exact encoded bytes** của phần signed payload.

---

# 9. Encoding boundary

Pipeline:

```text
bytes
  │
  ▼
AXCODEC
  │
  ▼
parsed structure
  │
  ▼
AXCERT
```

AXCERT không xây lại ASN.1/DER codec riêng nếu AXCODEC đã cung cấp primitive phù hợp.

---

# 10. Certificate signature

AXCERT gọi:

```text
AXCRYPTO.verify()
```

với:

```text
issuer public key
signed bytes
signature
algorithm
```

AXCERT không reimplement RSA/ECDSA/EdDSA.

---

# 11. Key binding

Certificate phải chứng minh:

```text
subject
   │
   └── associated with
             │
             ▼
        public key
```

AXCERT kiểm tra structural binding.

---

# 12. Issuer relationship

Certificate chain:

```text
Leaf
 │
 ▼
Intermediate
 │
 ▼
Root
```

Mỗi edge:

```text
child.issuer ≈ parent.subject
```

nhưng exact matching rules phụ thuộc certificate profile.

---

# 13. Chain graph

Không biểu diễn chain chỉ bằng array.

Internal model:

```text
trust_graph {
    nodes[]
    edges[]
}
```

vì một certificate có thể có:

- nhiều possible issuers;
- cross-signing;
- alternate chains.

---

# 14. Path candidate

```text
certificate_path {
    certificates[]
    trust_anchor
    path_length
    validation_state
}
```

AXCERT có thể xây nhiều candidate paths.

AXSECURITY quyết định policy selection.

---

# 15. Path construction

Input:

```text
leaf
intermediates
candidate anchors
```

AXCERT tìm:

```text
leaf → issuer → issuer → ... → anchor
```

Các tiêu chí structural:

- issuer relationship;
- signature verification;
- validity;
- basic constraints;
- key usage;
- path constraints.

---

# 16. Trust anchor

Trust anchor:

```text
trust_anchor {
    anchor_id
    subject
    public_key
    constraints
    metadata
}
```

Một trust anchor **không nhất thiết phải được xác thực bởi một certificate phía trên nó**.

Nó là điểm bắt đầu của trust policy.

---

# 17. Trust-anchor ownership

AXCERT có thể **consume** trust anchors.

Nhưng:

```text
"anchor nào được tin?"
```

là quyết định của:

```text
AXSECURITY
```

---

# 18. Validation phases

Certificate validation nên chia:

```text
PHASE 1
Parse

PHASE 2
Structural validation

PHASE 3
Cryptographic validation

PHASE 4
Path constraints

PHASE 5
Policy evaluation
```

AXCERT sở hữu 1–4.

AXSECURITY sở hữu 5.

---

# 19. Validity

Certificate validity:

```text
not_before
not_after
```

AXCERT kiểm tra:

```text
current_time ∈ [not_before, not_after]
```

Time source phải là explicit input.

---

# 20. Deterministic validation

Không lấy wall clock trực tiếp trong core validation nếu có thể tránh.

API:

```text
validate_at(certificate, timestamp)
```

cho phép:

- testing;
- deterministic replay;
- historical validation.

---

# 21. Clock skew

AXCERT có thể nhận:

```text
clock_skew
```

nhưng default policy không tự ý chọn tolerance.

Tolerance nên đến từ AXSECURITY profile.

---

# 22. Basic constraints

Certificate path processing phải hỗ trợ:

```text
CA
path_length
```

Ví dụ:

```text
root CA
   ↓
intermediate CA
   ↓
leaf
```

Một leaf certificate không thể tự trở thành CA chỉ vì field cấu trúc khác.

---

# 23. Key usage

Certificate có thể khai báo:

```text
DIGITAL_SIGNATURE
KEY_ENCIPHERMENT
KEY_AGREEMENT
KEY_CERT_SIGN
CRL_SIGN
```

AXCERT kiểm tra compatibility với certificate role.

---

# 24. Extended key usage

Có thể có purpose:

```text
SERVER_AUTH
CLIENT_AUTH
CODE_SIGNING
EMAIL_PROTECTION
TIME_STAMPING
```

AXCERT parse và expose.

AXSECURITY quyết định purpose nào được phép.

---

# 25. Name constraints

Certificate chain có thể chứa namespace constraints.

AXCERT phải model:

```text
permitted
excluded
```

và áp dụng structural path rules.

---

# 26. Critical extensions

Extension:

```text
critical = true
```

mà AXCERT không hiểu phải tạo:

```text
UNSUPPORTED_CRITICAL_EXTENSION
```

Không silently ignore.

---

# 27. Unknown non-critical extensions

Có thể preserve:

```text
unknown_extension {
    oid
    critical
    raw_value
}
```

để forward compatibility.

---

# 28. Extension registry

```text
certificate_extension_registry
```

mapping:

```text
OID → parser/validator
```

Known extensions được typed.

Unknown extension được giữ raw.

---

# 29. OID representation

Không dùng string làm canonical identity.

```text
oid {
    arcs[]
}
```

Có canonical encoded representation.

String rendering chỉ là presentation.

---

# 30. Distinguished Name

DN cần structured representation:

```text
name {
    attributes[]
}
```

Không so sánh DN chỉ bằng string formatting.

Comparison profile phải explicit.

---

# 31. Subject Alternative Name

Model:

```text
subject_alt_name {
    DNS
    IP
    URI
    EMAIL
    OTHER
}
```

AXCERT parse.

AXSECURITY quyết định matching policy.

---

# 32. Hostname validation boundary

AXCERT có thể cung cấp:

```text
match_name()
```

primitive structural.

Nhưng policy như:

```text
wildcard rules
acceptable name types
service purpose
```

phải thuộc AXSECURITY.

---

# 33. Serial number

Serial number phải giữ binary/integer exactness.

Không convert sang floating-point.

---

# 34. Certificate fingerprint

Fingerprint:

```text
fingerprint {
    algorithm
    digest
}
```

được tính bằng:

```text
AXCRYPTO.hash()
```

Fingerprint không phải certificate identity tuyệt đối ở mọi protocol.

---

# 35. Certificate identity

Stable object identity:

```text
certificate_id
```

có thể dựa trên:

```text
canonical object hash
```

nhưng certificate serial number và fingerprint vẫn giữ semantics riêng.

---

# 36. Revocation evidence

AXCERT model:

```text
revocation_evidence {
    type
    issuer
    produced_at
    this_update
    next_update
    status
    signature
}
```

Các dạng:

```text
CRL
OCSP
SIGNED_STATUS
```

---

# 37. Revocation policy boundary

AXCERT có thể trả:

```text
GOOD
REVOKED
UNKNOWN
STALE
INVALID_EVIDENCE
```

Nhưng policy:

```text
UNKNOWN có được chấp nhận?
stale evidence có được chấp nhận?
offline mode?
```

thuộc AXSECURITY.

---

# 38. OCSP/CRL transport

AXCERT **không tự fetch network**.

```text
AXNETWORK
   ↓
bytes
   ↓
AXCERT
```

Điều này giữ module deterministic và tránh coupling.

---

# 39. Attestation

Generic:

```text
attestation {
    attester
    subject
    claims
    evidence
    nonce
    timestamp
    signature
}
```

Ví dụ:

```text
device identity
secure boot state
hardware identity
runtime measurement
```

---

# 40. Attestation evidence ≠ trust decision

AXCERT xác định:

```text
evidence structurally valid
signature valid
claim binding valid
```

AXSECURITY quyết định:

```text
evidence đủ để cấp quyền hay không
```

---

# 41. Attestation freshness

Attestation có thể chứa:

```text
nonce
timestamp
counter
measurement_id
```

AXCERT kiểm tra structural presence.

Freshness policy thuộc AXSECURITY.

---

# 42. Hardware attestation provider

Provider abstraction:

```text
attestation_provider
```

backend:

```text
TPM
secure element
platform secure enclave
Android hardware-backed keystore
Apple hardware-backed key
```

AXCERT không phụ thuộc platform-specific API.

---

# 43. Measurement

Attestation có thể chứa measurement:

```text
measurement {
    algorithm
    digest
    component
    version
}
```

Digest được verify bằng AXCRYPTO.

Meaning của measurement thuộc security policy.

---

# 44. Credential chain

Không phải mọi credential chain là certificate chain.

Generic:

```text
credential_graph
```

cho phép:

```text
issuer → credential
device → attestation
identity → credential
service → credential
```

---

# 45. Signed claims

```text
signed_claim {
    issuer
    subject
    claims
    signing_key
    signature
}
```

AXCERT kiểm tra cryptographic binding.

---

# 46. Claim types

Generic claims:

```text
claim {
    namespace
    name
    value
}
```

Không ép mọi identity system phải dùng một schema.

---

# 47. Claim schema

Schema metadata:

```text
claim_schema {
    schema_id
    version
    fields[]
}
```

AXCODEC có thể serialize schema.

---

# 48. Credential versioning

Credential:

```text
version
schema_version
issuer_version
```

phải phân biệt.

---

# 49. Credential status

```text
ACTIVE
EXPIRED
REVOKED
SUSPENDED
UNKNOWN
```

AXCERT biểu diễn status evidence.

Authority về status thuộc issuer/security policy.

---

# 50. Evidence bundle

```text
evidence_bundle {
    credentials[]
    certificates[]
    attestations[]
    revocation_evidence[]
    signatures[]
}
```

Useful cho offline verification.

---

# 51. Offline validation

```text
bundle
  ↓
AXCERT
  ↓
parse
  ↓
build graph
  ↓
verify signatures
  ↓
validate paths
  ↓
validation report
```

Không cần network.

---

# 52. Validation report

```text
validation_report {
    status
    path
    failures[]
    warnings[]
    evidence[]
}
```

Không chỉ trả `bool`.

Điều này cần thiết cho diagnostics.

---

# 53. Validation error

Examples:

```text
MALFORMED_CERTIFICATE
INVALID_SIGNATURE
INVALID_ISSUER
NO_ISSUER
PATH_TOO_LONG
EXPIRED
NOT_YET_VALID
INVALID_BASIC_CONSTRAINTS
INVALID_KEY_USAGE
UNSUPPORTED_CRITICAL_EXTENSION
REVOKED
REVOCATION_UNKNOWN
STALE_EVIDENCE
INVALID_NAME
INVALID_ATTESTATION
MEASUREMENT_MISMATCH
```

---

# 54. Error severity

```text
FATAL
ERROR
WARNING
INFO
```

Nhưng final trust decision không do AXCERT quyết định.

---

# 55. Chain-building performance

Certificate lookup phải tránh O(N²) khi store lớn.

Index:

```text
subject_hash
issuer_hash
key_identifier
serial_number
fingerprint
```

Candidate issuer lookup:

```text
O(1) average
```

hoặc gần tương đương hash-index performance.

---

# 56. Certificate store

AXCERT có abstraction:

```text
credential_store
```

Có thể là:

```text
memory
filesystem
database
hardware
remote
```

Nhưng storage semantics thuộc AXSTORAGE/AXDATABASE.

---

# 57. Store indexing

Store nên hỗ trợ:

```text
find_by_subject()
find_by_issuer()
find_by_key_id()
find_by_fingerprint()
find_by_serial()
find_by_type()
```

---

# 58. No private-key duplication

Certificate store chỉ chứa public credential material theo mặc định.

Private key reference:

```text
key_handle
```

trỏ sang AXCRYPTO/provider.

Không copy private key vào certificate object.

---

# 59. Certificate + key association

```text
credential
    │
    ▼
public key
    │
    ⇅
key_handle
    │
    ▼
AXCRYPTO
```

Association có thể được kiểm tra bằng public-key equivalence.

---

# 60. Key identifier

Support:

```text
subject_key_identifier
authority_key_identifier
```

nhưng không coi chúng là cryptographic proof.

---

# 61. Cross-signing

Chain builder phải cho phép:

```text
Root A
  ↓
Intermediate X

Root B
  ↓
Intermediate X
```

Một intermediate có thể xuất hiện trong nhiều candidate paths.

---

# 62. Path cycle detection

Graph traversal phải detect:

```text
A → B → C → A
```

và terminate deterministically.

Không recursion không giới hạn.

---

# 63. Resource limits

Parser/validator phải có:

```text
max_certificate_size
max_chain_length
max_extensions
max_name_attributes
max_claims
max_evidence
max_graph_nodes
max_graph_edges
```

---

# 64. Malformed input

Certificate từ network/file được coi là untrusted input.

Malformed input:

```text
error
```

không:

```text
crash
```

---

# 65. Memory safety

AXCERT phải sử dụng:

```text
AXMEMORY
AXCODEC
```

với:

- bounds checking;
- checked length arithmetic;
- allocation limits;
- recursion depth limits.

---

# 66. Canonical parsing

Certificate parser phải phân biệt:

```text
accepted encoding
canonical encoding
```

Không tự động biến một malformed encoding thành canonical valid certificate.

---

# 67. DER-like strictness

Với formats yêu cầu canonical encoding, parser phải enforce canonical rules.

Ví dụ:

```text
non-minimal integer
invalid length encoding
unexpected trailing data
```

không được silently normalize thành valid object.

---

# 68. Raw preservation

Object có thể giữ:

```text
raw_bytes
```

nhưng lifecycle phải explicit.

Để tránh memory overhead, raw bytes có thể là:

```text
borrowed view
```

hoặc:

```text
owned buffer
```

---

# 69. Lazy extensions

Large certificates có thể parse header trước:

```text
certificate metadata
```

và parse extension payload on demand.

Useful cho performance.

---

# 70. Certificate caching

Validation cache:

```text
validation_cache {
    certificate_fingerprint
    policy_id
    validation_time_bucket
    result
}
```

Policy ID bắt buộc là cache key.

Không dùng một validation result cho mọi security policy.

---

# 71. Cache invalidation

Cache phải invalidate khi:

- certificate changes;
- trust anchor changes;
- policy changes;
- revocation evidence changes;
- validity window changes.

---

# 72. Deterministic mode

AXCERT hỗ trợ:

```text
validate_at(timestamp)
```

và explicit evidence set.

Do đó:

```text
same input
+
same policy
+
same timestamp
+
same evidence
```

→ same structural validation result.

---

# 73. Replay

Trace có thể lưu:

```text
certificate ID
issuer candidate
path choice
crypto verification result
policy reference
```

Không lưu private secret.

---

# 74. AI integration

AI có thể:

- giải thích certificate chain;
- tìm missing issuer;
- phân tích extension;
- phát hiện deprecated algorithms;
- giải thích validation failure;
- đề xuất diagnostics.

AI không được:

- thay đổi trust anchor;
- tự cấp trust;
- bỏ qua certificate failure;
- sửa credential để biến thành valid;
- override AXSECURITY.

---

# 75. Compiler integration

Compiler có thể recognize:

```text
certificate
credential
public_key
fingerprint
attestation
```

nhưng không embed private credentials trong executable mặc định.

---

# 76. Static credential metadata

Ứng dụng có thể declare:

```text
@credential_type("service")
@required_algorithm(...)
```

Compiler ghi metadata vào artifact.

Runtime vẫn thực hiện validation.

---

# 77. FFI/ABI

Stable ABI types:

```text
ax_cert_handle
ax_credential_handle
ax_trust_graph_handle
ax_validation_report_handle
ax_attestation_handle
```

Không expose internal graph pointers.

---

# 78. Handle safety

Handles phải:

```text
opaque
generation checked
type checked
lifetime checked
```

theo model đã thiết lập ở AXPROCESS/AXMEMORY.

---

# 79. Thread/task safety

Immutable certificate objects:

```text
thread-safe
```

mutable stores/validation contexts:

```text
explicit synchronization contract
```

Không mặc định thread-safe mọi object.

---

# 80. Async boundary

Certificate validation bản thân chủ yếu là CPU operation.

Network fetching:

```text
AXNETWORK + AXASYNC
```

sau đó:

```text
AXCERT.validate()
```

Không để AXCERT tự block network worker.

---

# 81. Native API

Core:

```text
certificate_parse()
certificate_parse_view()

certificate_get_subject()
certificate_get_issuer()
certificate_get_public_key()
certificate_get_extensions()
certificate_get_validity()
certificate_get_fingerprint()

certificate_verify_signature()

build_certificate_graph()
build_certificate_path()

validate_certificate_path()
validate_certificate_at()

create_trust_anchor()

credential_parse()
credential_validate()

attestation_parse()
attestation_validate()

parse_revocation_evidence()
validate_revocation_evidence()

create_evidence_bundle()
validate_evidence_bundle()

credential_store_open()
credential_store_add()
credential_store_remove()
credential_store_find()

get_validation_report()
```

---

# 82. Canonical flow — Certificate

```text
encoded certificate
        │
        ▼
 certificate_parse()
        │
        ▼
 certificate object
        │
        ├── issuer
        ├── subject
        ├── public key
        ├── validity
        └── extensions
```

---

# 83. Canonical flow — Chain

```text
leaf
 │
 ├── candidate issuer A
 ├── candidate issuer B
 └── candidate issuer C
          │
          ▼
    trust graph
          │
          ▼
   candidate paths
          │
          ▼
 cryptographic validation
          │
          ▼
 structural validation report
```

---

# 84. Canonical flow — Trust

```text
AXCERT
   │
   ▼
validation report
   │
   ▼
AXSECURITY
   │
   ▼
policy evaluation
   │
   ▼
authorization / trust decision
```

---

# 85. Canonical flow — Attestation

```text
attestation bytes
       │
       ▼
    AXCODEC
       │
       ▼
 AXCERT parser
       │
       ├── claims
       ├── measurement
       ├── nonce
       └── signature
               │
               ▼
           AXCRYPTO
               │
               ▼
        validation evidence
               │
               ▼
          AXSECURITY
```

---

# 86. Performance architecture

AXCERT phải ưu tiên:

- immutable parsed objects;
- zero-copy parsing;
- lazy extension parsing;
- hash-indexed certificate stores;
- iterative graph traversal;
- bounded allocations;
- cacheable fingerprints;
- batch signature verification;
- parallel independent candidate-path verification;
- compact handles;
- no unnecessary string conversion.

---

# 87. Parallel validation

Candidate paths:

```text
Path A ─┐
Path B ─┼── parallel validation
Path C ─┤
Path D ─┘
```

có thể chạy trên AXTASK/AXCOMPUTE.

AXCERT không sở hữu scheduler.

---

# 88. Batch verification

Nếu provider hỗ trợ:

```text
verify_batch()
```

AXCERT có thể gom:

```text
multiple signatures
```

để giảm dispatch overhead.

---

# 89. Security limits

Mọi public API nhận untrusted certificate data phải có limits.

Không cho:

```text
unbounded chain
unbounded recursion
unbounded extension count
unbounded claim count
```

---

# 90. Formal invariants

### CERT-INV-01
Certificate raw bytes và parsed representation là hai representation khác nhau.

### CERT-INV-02
AXCERT không reimplement cryptographic primitives thuộc AXCRYPTO.

### CERT-INV-03
Certificate signature verification phải dùng AXCRYPTO.

### CERT-INV-04
Certificate không tự động trở thành trusted identity.

### CERT-INV-05
Trust decision thuộc AXSECURITY.

### CERT-INV-06
Trust anchor selection policy thuộc AXSECURITY.

### CERT-INV-07
Certificate issuer relationship phải được kiểm tra.

### CERT-INV-08
Certificate public-key binding phải được kiểm tra.

### CERT-INV-09
Validity interval phải được kiểm tra theo explicit timestamp.

### CERT-INV-10
Clock source không được implicit trong deterministic validation.

### CERT-INV-11
Unknown critical extension không được silently ignore.

### CERT-INV-12
Unknown non-critical extension có thể được preserved.

### CERT-INV-13
OID identity không phụ thuộc string formatting.

### CERT-INV-14
DN comparison không được phụ thuộc presentation string.

### CERT-INV-15
Candidate certificate chains phải được model như graph/path.

### CERT-INV-16
Chain traversal phải detect cycles.

### CERT-INV-17
Path length phải có giới hạn.

### CERT-INV-18
Certificate parsing phải bounded.

### CERT-INV-19
Malformed untrusted certificate không được crash runtime.

### CERT-INV-20
Certificate store không được tự động copy private key.

### CERT-INV-21
Private key phải được giữ qua AXCRYPTO key handle khi có thể.

### CERT-INV-22
Fingerprint phải được tính bằng cryptographic hash primitive.

### CERT-INV-23
Fingerprint không được nhầm với trust decision.

### CERT-INV-24
Revocation evidence phải phân biệt `GOOD`, `REVOKED`, `UNKNOWN` và stale/invalid states.

### CERT-INV-25
AXCERT không tự fetch network resources.

### CERT-INV-26
AXNETWORK sở hữu certificate/revocation transport.

### CERT-INV-27
Attestation signature verification phải dùng AXCRYPTO.

### CERT-INV-28
Attestation evidence không tự động cấp authority.

### CERT-INV-29
Freshness policy thuộc AXSECURITY.

### CERT-INV-30
Validation cache phải bind với security policy identity.

### CERT-INV-31
Trust-anchor changes phải invalidate dependent validation state.

### CERT-INV-32
Revocation-evidence changes phải invalidate dependent cached results.

### CERT-INV-33
Immutable certificate objects có thể share giữa tasks/threads.

### CERT-INV-34
Mutable validation/store state phải có explicit concurrency semantics.

### CERT-INV-35
AXCERT không được ghi secret/private-key material vào diagnostic trace mặc định.

### CERT-INV-36
AI tooling không được thay đổi trust policy.

### CERT-INV-37
Certificate parsing và certificate trust decision phải là hai bước riêng.

### CERT-INV-38
Deterministic validation phải reproducible khi inputs/policy/time/evidence giống nhau.

### CERT-INV-39
Certificate representation phải versioned và forward-compatible.

### CERT-INV-40
`AXCERT 5.0` phải giữ boundary độc lập giữa certificate mechanics, cryptographic primitives và security policy.

---

# 91. Definition of Done

`AXCERT 5.0` được xem là hoàn tất khi có:

- certificate object model;
- generic credential model;
- trust-object abstraction;
- strict parsing;
- zero-copy parsing;
- raw-byte preservation;
- extension registry;
- OID model;
- DN model;
- SAN model;
- public-key binding;
- certificate signature verification;
- certificate graph;
- path construction;
- path validation;
- trust-anchor abstraction;
- validity evaluation;
- basic constraints;
- key usage;
- extended key usage;
- name constraints;
- critical-extension handling;
- fingerprinting;
- certificate store abstraction;
- indexed lookup;
- revocation evidence model;
- CRL-like evidence;
- OCSP-like evidence;
- attestation evidence;
- measurement model;
- signed claims;
- credential chains;
- evidence bundles;
- offline validation;
- deterministic validation;
- validation reports;
- bounded resource usage;
- cycle detection;
- validation caching;
- cache invalidation;
- hardware attestation provider interface;
- AXCRYPTO integration;
- AXCODEC integration;
- AXNETWORK boundary;
- AXSECURITY trust-policy boundary;
- AXSTORAGE/AXDATABASE storage boundary;
- AXTASK/AXCOMPUTE parallel-validation integration;
- AI diagnostic boundary;
- native ABI;
- 40 invariants.

**AXCERT 5.0 → FROZEN.**

---

# BOOTSTRAP-754 — AXTRUST

Tầng kế tiếp sẽ xử lý phần còn thiếu sau `AXCERT`:

**Native Trust Policy, Trust Evaluation, Authorization Evidence, Revocation Policy, Identity Binding & Security Decision Runtime 5.0**

Kiến trúc lúc đó sẽ hoàn chỉnh thành:

```text
                 AXIDENTITY
                     │
                     ▼
                 AXTRUST
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       AXCERT     AXCRYPTO    evidence
          │          │
          └──────────┘
                 │
                 ▼
             AXSECURITY
```

Trong đó cần giữ một nguyên tắc rất quan trọng:

```text
AXCRYPTO = primitive
AXCERT   = credential/evidence mechanics
AXTRUST  = trust evaluation
AXSECURITY = authorization + enforcement
AXIDENTITY = identity lifecycle
```

Như vậy security architecture của Axiom không bị dồn toàn bộ logic vào một `AXSECURITY` monolith.