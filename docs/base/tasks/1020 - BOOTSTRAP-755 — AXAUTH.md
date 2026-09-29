# BOOTSTRAP-755 — AXAUTH

**Title:** Native Authentication, Session Establishment, Credential Presentation, Challenge/Response, Login & Security Session Runtime 5.0  
**Namespace:** `AXAUTH`  
**Phase:** Axiom Civilization Runtime / Native Authentication & Security Session Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXAUTH` là tầng chịu trách nhiệm biến:

```text
identity
+
credential
+
cryptographic proof
+
trust evidence
+
authentication protocol
```

thành:

```text
authenticated principal
+
authenticated session
```

Nó nằm giữa `AXTRUST` và `AXSECURITY`.

```text
AXIDENTITY
     │
     ▼
  credentials
     │
     ├──────────────┐
     ▼              ▼
  AXCERT        AXCRYPTO
     │              │
     └──────┬───────┘
            ▼
         AXTRUST
            │
            ▼
          AXAUTH
            │
            ▼
    authenticated session
            │
            ▼
       AXSECURITY
            │
            ▼
      authorization
```

---

# 2. Strong boundary

## AXAUTH sở hữu

- authentication protocol state;
- challenge/response;
- credential presentation;
- proof-of-possession;
- principal authentication;
- session establishment;
- session lifecycle;
- session keys/context;
- reauthentication;
- session expiration;
- authentication timeout;
- logout;
- session renewal;
- authentication factors;
- multi-factor composition;
- authentication transcripts;
- replay protection;
- channel binding;
- authentication failure handling;
- authentication event metadata.

## AXAUTH không sở hữu

### AXIDENTITY

- identity lifecycle;
- identity registration;
- identity canonical identifiers.

### AXCRYPTO

- signature;
- MAC;
- KDF;
- AEAD;
- hashing;
- random;
- key operations.

### AXCERT

- certificate mechanics;
- certificate path;
- credential structure.

### AXTRUST

- trust policy;
- evidence evaluation;
- trust result.

### AXSECURITY

- authorization;
- capability issuance;
- access control;
- sandbox enforcement.

### AXNETWORK

- transport/network protocol.

---

# 3. Authentication ≠ Authorization

Đây là invariant kiến trúc.

```text
Authentication:
"Bạn đã chứng minh mình sở hữu credential tương ứng với principal này."

Authorization:
"Principal đó có quyền thực hiện operation này không?"
```

Ví dụ:

```text
AXAUTH
    ↓
principal = user_123
authenticated = true
    ↓
AXSECURITY
    ↓
resource = file_A
operation = WRITE
    ↓
ALLOW / DENY
```

`AXAUTH` không được tự cấp quyền `WRITE`.

---

# 4. Authentication ≠ Trust

Credential có thể:

```text
cryptographically valid
```

nhưng chưa chắc:

```text
trusted for this authentication purpose
```

Do đó:

```text
AXCERT
   ↓
AXTRUST
   ↓
AXAUTH
```

là flow chính.

---

# 5. Core models

```text
auth_protocol
auth_method
auth_factor
auth_credential
auth_challenge
auth_response
auth_proof
auth_principal
auth_context
auth_session
auth_session_key
auth_binding
auth_transcript
auth_state
auth_policy
auth_result
auth_error
auth_limits
auth_provider
auth_backend
auth_trace
```

---

# 6. Authentication state machine

Baseline:

```text
CREATED
   ↓
NEGOTIATING
   ↓
CHALLENGING
   ↓
PROVING
   ↓
VERIFYING
   ↓
AUTHENTICATED
   ↓
ESTABLISHED
   ↓
REAUTHENTICATING
   ↓
ESTABLISHED
   ↓
CLOSING
   ↓
CLOSED
```

Failure states:

```text
FAILED
EXPIRED
REVOKED
ABORTED
LOCKED
```

---

# 7. State invariants

Không được chuyển trực tiếp:

```text
CREATED → AUTHENTICATED
```

mà bỏ qua proof verification.

Authentication result phải có evidence.

---

# 8. Authentication context

```text
auth_context {
    protocol
    client
    server
    principal
    purpose
    transport_binding
    timestamp
    nonce
    credentials
    trust_result
}
```

Context phải immutable trong quá trình một authentication attempt, hoặc sử dụng snapshot.

---

# 9. Principal

```text
auth_principal {
    principal_id
    identity_ref
    authentication_level
    credential_refs[]
    session_ref
}
```

`principal_id` không phải raw private key hay password.

---

# 10. Principal ≠ identity

Một identity có thể có nhiều authentication sessions:

```text
Identity X
 ├── Session A
 ├── Session B
 └── Session C
```

Do đó:

```text
identity
≠
session
```

---

# 11. Authentication method

```text
auth_method {
    method_id
    factors[]
    protocol
    security_properties
}
```

Examples:

```text
PASSWORD
PUBLIC_KEY
CERTIFICATE
DEVICE_KEY
OTP
CHALLENGE_RESPONSE
HARDWARE_ATTESTATION
COMPOSITE
```

Các method cụ thể chỉ được enable nếu provider/profile hỗ trợ.

---

# 12. Credential presentation

Authentication credential có thể là:

```text
PUBLIC_KEY_PROOF
CERTIFICATE_CHAIN
SIGNED_ASSERTION
DEVICE_ATTESTATION
PASSWORD_PROOF
ONE_TIME_CODE
```

AXAUTH không lưu plaintext secret trong authentication transcript.

---

# 13. Proof of possession

Public-key authentication:

```text
challenge
    ↓
sign(private_key, transcript)
    ↓
proof
    ↓
AXCRYPTO.verify(public_key, transcript, signature)
```

Điểm quan trọng:

> Có certificate chứa public key không đồng nghĩa caller đang sở hữu private key.

AXAUTH phải kiểm tra **proof of possession**.

---

# 14. Challenge

```text
auth_challenge {
    challenge_id
    nonce
    issued_at
    expires_at
    protocol
    session_binding
}
```

Challenge phải đủ entropy cryptographic.

Nguồn random:

```text
AXCRYPTO.random()
```

---

# 15. Challenge uniqueness

Challenge ID/nonce phải tránh reuse trong active authentication windows.

Server phải có generation/collision handling.

---

# 16. Replay resistance

Authentication protocol phải bind proof vào:

```text
challenge
+
session
+
protocol
+
purpose
```

nếu protocol yêu cầu.

Không ký chỉ:

```text
"hello"
```

rồi coi đó là authentication proof.

---

# 17. Transcript binding

```text
auth_transcript {
    protocol_version
    algorithm
    client_nonce
    server_nonce
    identities
    channel_binding
    messages
}
```

Proof phải bind vào transcript canonical representation.

---

# 18. Canonical transcript

Transcript encoding phải deterministic.

```text
same messages
+
same protocol version
+
same ordering
```

→ cùng transcript digest.

AXCODEC có thể cung cấp representation.

AXCRYPTO hash transcript.

---

# 19. Channel binding

Authentication có thể bind vào underlying secure channel:

```text
transport
    ↓
channel_binding
    ↓
authentication proof
```

Ví dụ conceptual:

```text
channel_binding = hash(channel_exporter)
```

AXAUTH không tự định nghĩa transport crypto.

---

# 20. Session

Sau authentication:

```text
auth_session {
    session_id
    principal
    created_at
    expires_at
    authentication_level
    bindings
    state
}
```

Session không chứa private credential material.

---

# 21. Session lifecycle

```text
CREATED
   ↓
AUTHENTICATING
   ↓
ACTIVE
   ↓
IDLE
   ↓
REAUTH_REQUIRED
   ↓
ACTIVE
   ↓
EXPIRED
   ↓
CLOSED
```

Immediate termination:

```text
REVOKED
SECURITY_TERMINATED
FAILED
```

---

# 22. Session expiration

Session có thể có:

```text
absolute_expiration
idle_timeout
reauthentication_interval
credential_expiration
```

Policy quyết định giá trị.

---

# 23. Reauthentication

Session có thể yêu cầu:

```text
reauthenticate()
```

mà không cần tạo application process/session mới.

Flow:

```text
ACTIVE
  ↓
REAUTH_REQUIRED
  ↓
CHALLENGE
  ↓
PROOF
  ↓
VERIFY
  ↓
ACTIVE
```

---

# 24. Step-up authentication

AXAUTH hỗ trợ:

```text
current authentication
        ↓
additional factor
        ↓
higher authentication assurance
```

Ví dụ:

```text
existing session
+
hardware key proof
```

Nhưng việc operation nào yêu cầu step-up thuộc AXSECURITY.

---

# 25. Multi-factor authentication

```text
auth_composition {
    factors[]
    threshold
}
```

Ví dụ:

```text
2 of {
    device_key
    identity_credential
    second_factor
}
```

Duplicate factor không được count nhiều lần.

---

# 26. Authentication assurance

AXAUTH có thể trả:

```text
authentication_assurance {
    level
    factors[]
    verified_at
    bindings[]
}
```

Level có meaning theo authentication profile.

Không có universal numeric security ranking.

---

# 27. Authentication policy

```text
auth_policy {
    policy_id
    version
    methods[]
    required_factors
    timeout
    replay_policy
    channel_binding_policy
}
```

Policy được compile trước.

---

# 28. Policy compiler

```text
auth policy
    ↓
parse
    ↓
type-check
    ↓
AuthPolicyIR
    ↓
compile
    ↓
native decision state machine
```

Không interpret textual policy trên hot path.

---

# 29. Authentication protocol negotiation

Client/server có thể negotiate:

```text
protocol_version
authentication_method
signature_algorithm
credential_format
channel_binding
```

Negotiation phải chống downgrade.

---

# 30. Downgrade protection

Nếu hai bên hỗ trợ:

```text
strong_method
weak_method
```

attacker không được ép:

```text
strong → weak
```

nếu policy không cho phép.

Transcript phải bao gồm negotiated parameters.

---

# 31. Algorithm agility

Authentication protocol dùng stable IDs:

```text
algorithm_id
method_id
protocol_id
```

Không bind protocol vào implementation pointer.

---

# 32. Credential verification

Flow:

```text
credential
   ↓
AXCERT
   ↓
credential validation
   ↓
AXTRUST
   ↓
trusted for purpose?
   ↓
AXAUTH
   ↓
proof-of-possession
```

---

# 33. Password authentication

Nếu Axiom hỗ trợ password-based authentication, password không được truyền raw qua authentication protocol trừ khi transport/protocol explicitly protects it.

Server-side storage không được là:

```text
plaintext password
```

hay:

```text
hash(password)
```

đơn giản.

Password verifier cần password-hardening semantics từ AXCRYPTO KDF.

---

# 34. Password proof

AXAUTH nên ưu tiên password authentication protocol có challenge/response hoặc secure channel binding thay vì thiết kế một custom protocol mới.

Axiom không nên tạo cryptographic protocol tùy tiện chỉ để tránh dependency.

---

# 35. One-time credentials

OTP-like authentication:

```text
auth_factor {
    type = ONE_TIME
    counter/time_window
}
```

Replay prevention phải explicit.

---

# 36. Device authentication

Device key:

```text
device
   ↓
hardware-bound private key
   ↓
challenge
   ↓
signature
   ↓
AXCRYPTO
```

Certificate/attestation:

```text
AXCERT
AXTRUST
```

để xác định device credential có được tin hay không.

---

# 37. Hardware-backed authentication

AXAUTH phải có provider:

```text
auth_provider
```

có thể gọi:

```text
secure_element.sign()
```

Private key không cần rời secure hardware.

---

# 38. Authentication provider

```text
auth_provider {
    authenticate()
    begin()
    continue()
    cancel()
    close()
}
```

Backend có thể là:

```text
SOFTWARE
OS
HARDWARE
REMOTE_IDENTITY_PROVIDER
```

---

# 39. No hidden network

`authenticate()` không được âm thầm tạo network request nếu API không khai báo async/network dependency.

Remote authentication phải explicit:

```text
authenticate_async()
```

với network context.

---

# 40. Session keys

Authentication có thể sinh session key material:

```text
credential proof
      ↓
KDF
      ↓
session key
```

AXCRYPTO thực hiện KDF.

AXAUTH quản lý semantic association:

```text
session_id
key_id
purpose
direction
```

---

# 41. Session key separation

Client/server directions phải có separate derived keys:

```text
client_to_server_key
server_to_client_key
```

nếu protocol cần encryption.

Không reuse một key cho cả hai directions nếu protocol không quy định.

---

# 42. Key lifetime

Session key:

```text
CREATED
ACTIVE
ROTATING
EXPIRED
DESTROYED
```

Key material được quản lý qua AXCRYPTO.

---

# 43. Key rotation

Session có thể rotate keys:

```text
session
   ↓
rekey
   ↓
new session key epoch
```

Mỗi epoch có identifier:

```text
key_epoch
```

---

# 44. Session epochs

```text
session_epoch {
    number
    key_refs[]
    created_at
}
```

Giúp chống replay giữa các key generations.

---

# 45. Session termination

Logout:

```text
session.close()
```

phải:

- invalidate session;
- destroy/release session key handles;
- invalidate authentication state;
- emit event.

---

# 46. Forced termination

AXSECURITY có thể yêu cầu:

```text
terminate_session(session_id)
```

AXAUTH thực hiện lifecycle termination.

Authorization của caller do AXSECURITY kiểm tra.

---

# 47. Credential revocation propagation

Flow:

```text
credential revoked
       ↓
AXCERT / AXTRUST
       ↓
session invalidation event
       ↓
AXAUTH
       ↓
session EXPIRED/REVOKED
```

AXAUTH không tự định nghĩa revocation truth.

---

# 48. Identity change

Nếu identity binding thay đổi:

```text
identity
credential
public key
```

session phụ thuộc credential đó có thể bị invalidated.

Policy quyết định exact behavior.

---

# 49. Concurrent sessions

Một identity có thể có:

```text
session A
session B
session C
```

AXAUTH không mặc định chỉ cho một session.

Session-count limits thuộc policy.

---

# 50. Session registry

```text
auth_session_registry
```

indexes:

```text
session_id
principal_id
credential_id
device_id
application_id
```

Không lưu private credentials trong registry.

---

# 51. Session handle

```text
ax_auth_session_handle
```

phải:

- opaque;
- generation checked;
- type checked;
- lifetime checked.

---

# 52. Session persistence

Session có thể:

```text
memory_only
persistent
checkpointable
```

Nhưng secret/session-key material không được persist mặc định.

---

# 53. Session resume

Nếu hỗ trợ resumption:

```text
old session
   ↓
resume token
   ↓
proof
   ↓
new session epoch
```

Resume token phải có:

- expiration;
- audience;
- session binding;
- replay protection.

---

# 54. Resume token

Không dùng raw session ID làm authentication credential.

```text
session_id ≠ resume_credential
```

---

# 55. Authentication tickets

Nếu protocol dùng ticket:

```text
ticket {
    issuer
    audience
    subject
    issued_at
    expires_at
    nonce
    encrypted_payload
    authentication_tag
}
```

AEAD do AXCRYPTO cung cấp.

---

# 56. Ticket validation

AXAUTH kiểm tra:

```text
ticket integrity
ticket expiry
audience
session binding
```

AXTRUST/AXSECURITY kiểm tra trust/authority khi cần.

---

# 57. Replay cache

Protocol có thể cần:

```text
replay_cache
```

Key:

```text
challenge_id
ticket_id
proof_id
```

Có bounded TTL.

---

# 58. Replay-cache scaling

Không dùng một global lock.

Có thể:

```text
sharded hash tables
per-core caches
bounded expiration queues
```

AXMEMORY cung cấp allocation primitives.

---

# 59. Authentication rate limiting

AXAUTH có thể emit metadata:

```text
failed_attempt
```

Nhưng global rate-limit policy thuộc security/control layer.

Không hard-code lockout policy vào primitive.

---

# 60. Authentication failure

Không tiết lộ quá nhiều thông tin.

Ví dụ không trả:

```text
"username exists but password wrong"
```

nếu protocol security profile cấm account enumeration.

Error có thể có:

```text
AUTHENTICATION_FAILED
```

với diagnostic detail chỉ trong privileged/internal channel.

---

# 61. Error taxonomy

```text
AUTHENTICATION_FAILED
INVALID_CREDENTIAL
INVALID_PROOF
INVALID_CHALLENGE
CHALLENGE_EXPIRED
REPLAY_DETECTED
CHANNEL_BINDING_FAILED
TRUST_REQUIRED
TRUST_FAILED
POLICY_DENIED
METHOD_UNSUPPORTED
ALGORITHM_UNSUPPORTED
DOWNGRADE_DETECTED
SESSION_EXPIRED
SESSION_REVOKED
SESSION_CLOSED
REAUTH_REQUIRED
FACTOR_REQUIRED
FACTOR_FAILED
PROVIDER_FAILURE
KEY_UNAVAILABLE
CREDENTIAL_EXPIRED
CREDENTIAL_REVOKED
TIMEOUT
CANCELLED
RATE_LIMITED
```

---

# 62. Error information partitioning

Public error:

```text
AUTHENTICATION_FAILED
```

Internal diagnostic:

```text
proof invalid
credential revoked
trust policy mismatch
```

AXAUTH phải hỗ trợ error classification.

---

# 63. Cancellation

Authentication có thể cancel:

```text
auth_cancel_token
```

Cancellation không được để authentication state ở trạng thái `AUTHENTICATED` một cách không xác định.

---

# 64. Deadline

Mọi authentication operation có thể có:

```text
absolute_deadline
```

Nếu hết deadline:

```text
TIMEOUT
```

không phải authentication success.

---

# 65. Async authentication

```text
await authenticate(...)
```

hạ xuống:

```text
AXTASK
   +
AXASYNC
```

nếu cần network/device I/O.

---

# 66. Blocking provider

Hardware/provider operation có thể block.

Không được chạy blocking provider trực tiếp trên async worker nếu backend yêu cầu blocking executor.

---

# 67. Task integration

Authentication state machine có thể suspend:

```text
CHALLENGING
    ↓
await response
    ↓
PROVING
```

Task frame chỉ giữ state cần thiết.

---

# 68. No unnecessary state allocation

Authentication context nên dùng:

```text
inline state
arena
small-object optimization
```

cho common paths.

---

# 69. Transcript memory

Large authentication payloads không được giữ vô hạn.

Limits:

```text
max_messages
max_message_size
max_transcript_size
```

---

# 70. Secure transcript handling

Transcript có thể chứa sensitive identity data.

Không ghi toàn bộ transcript vào trace mặc định.

Trace chỉ giữ:

```text
message_type
size
sequence
hash
status
```

---

# 71. Authentication audit

AXAUTH có thể emit:

```text
authentication_started
authentication_succeeded
authentication_failed
reauthenticated
session_created
session_expired
session_revoked
```

Persistent audit semantics thuộc audit/security subsystem.

---

# 72. Authentication context binding

Session phải bind:

```text
principal
protocol
purpose
authentication_method
channel
```

để tránh credential substitution.

---

# 73. Credential substitution protection

Nếu attacker thay:

```text
credential A
```

bằng:

```text
credential B
```

trong cùng transcript, proof phải fail hoặc context mismatch.

---

# 74. Audience binding

Authentication credential có thể yêu cầu:

```text
audience
```

Ví dụ:

```text
service-A
```

không tự động hợp lệ cho:

```text
service-B
```

---

# 75. Realm / tenant binding

Authentication context có thể chứa:

```text
realm_id
tenant_id
```

Credential chỉ được dùng trong allowed realm nếu policy yêu cầu.

---

# 76. Protocol confusion protection

Proof phải bind:

```text
protocol_id
protocol_version
purpose
```

để một proof cho protocol A không bị tái sử dụng trong protocol B.

---

# 77. Cross-protocol attack prevention

Axiom protocol designers phải dùng distinct domain separators:

```text
AXIOM/AUTH/<protocol>
```

qua AXCRYPTO KDF/hash primitives.

---

# 78. Authentication state serialization

Một protocol có thể serialize resumable state:

```text
auth_state_snapshot
```

nhưng:

- secret material phải được bảo vệ;
- state phải có version;
- state phải có integrity protection;
- expired state phải reject.

---

# 79. Checkpoint boundary

AXAUTH không checkpoint arbitrary process memory.

Chỉ checkpoint explicit authentication protocol state.

AXPROCESS/AXMEMORY sở hữu process-memory checkpoint.

---

# 80. Deterministic simulation

```text
auth_simulation
```

có thể mô phỏng:

- challenge;
- response;
- timeout;
- replay;
- credential failure;
- trust failure;
- network interruption;
- provider failure.

Test RNG chỉ dùng test profile.

---

# 81. Fault injection

Có thể inject:

```text
CHALLENGE_TIMEOUT
INVALID_SIGNATURE
REPLAY
PROVIDER_FAILURE
NETWORK_DISCONNECT
CREDENTIAL_REVOKED
CLOCK_SKEW
```

chỉ trong simulation/test namespace.

---

# 82. Security testing

Conformance suite phải kiểm tra:

- replay;
- downgrade;
- wrong audience;
- wrong principal;
- expired credential;
- revoked credential;
- invalid signature;
- wrong channel binding;
- concurrent session behavior;
- cancellation races;
- timeout races.

---

# 83. Race handling

Các race:

```text
authentication success
        vs
credential revocation
```

phải có explicit ordering semantics.

Không được để race tạo ra undefined session state.

---

# 84. Atomic session establishment

Session chỉ chuyển:

```text
AUTHENTICATED → ACTIVE
```

sau khi toàn bộ required authentication conditions đã pass.

Không expose partially authenticated session.

---

# 85. Security boundary

Session object có thể được cấp cho AXSECURITY:

```text
authenticated_principal
authentication_assurance
session_binding
```

AXSECURITY sau đó tạo authorization context.

---

# 86. Capability handoff

```text
AXAUTH
  ↓
authenticated principal
  ↓
AXSECURITY
  ↓
capability evaluation
```

AXAUTH không mint capability.

---

# 87. AI boundary

AI có thể:

- giải thích authentication failures;
- phân tích protocol trace;
- phát hiện downgrade;
- tìm missing channel binding;
- kiểm tra policy consistency;
- mô phỏng authentication flows.

AI không được:

- bypass authentication;
- fabricate proof;
- reveal credentials;
- disable replay protection;
- lower authentication requirements;
- mint authenticated sessions.

---

# 88. Compiler support

Compiler có thể recognize:

```text
await auth.authenticate()
await auth.reauthenticate()
session.require_authenticated()
```

và lower async operations qua AXTASK/AXASYNC.

---

# 89. Authentication intrinsics

Có thể có:

```text
auth_challenge()
auth_sign_transcript()
auth_verify_proof()
auth_establish_session()
auth_reauthenticate()
auth_close_session()
```

Các intrinsic gọi native AXAUTH ABI.

---

# 90. Native API

Baseline:

```text
auth_policy_compile()
auth_policy_load()

auth_begin()
auth_continue()
auth_cancel()

auth_create_challenge()
auth_verify_response()

auth_present_credential()
auth_verify_proof()

auth_authenticate()
auth_authenticate_async()

auth_reauthenticate()

auth_create_session()
auth_get_session()
auth_close_session()
auth_revoke_session()

auth_session_status()
auth_session_principal()
auth_session_assurance()

auth_rotate_session_key()
auth_resume_session()

auth_create_replay_cache()

auth_get_authentication_result()
auth_get_authentication_diagnostics()

auth_start_trace()
auth_stop_trace()

auth_simulate()
auth_replay()

auth_get_provider_info()
auth_get_capabilities()
```

---

# 91. Canonical flow — Public-key authentication

```text
client                          server
  │                               │
  │──── authentication request ──►│
  │                               │
  │◄──── challenge + context ─────│
  │                               │
  │ sign(transcript, private key) │
  │                               │
  │──── proof ───────────────────►│
  │                               │
  │                        AXCRYPTO.verify
  │                               │
  │                        AXTRUST.evaluate
  │                               │
  │                        proof-of-possession
  │                               │
  │◄──── authenticated session ───│
```

---

# 92. Canonical flow — Certificate authentication

```text
credential
    │
    ▼
AXCERT
    │
    ├── parse
    ├── chain
    └── key binding
    │
    ▼
AXTRUST
    │
    └── trusted for purpose?
    │
    ▼
AXAUTH
    │
    ├── challenge
    ├── proof of possession
    └── transcript verification
    │
    ▼
authenticated principal
```

---

# 93. Canonical flow — MFA

```text
             authentication
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      factor A             factor B
          │                   │
          └─────────┬─────────┘
                    ▼
              AXAUTH policy
                    │
                    ▼
              authentication
                    │
                    ▼
              authenticated
```

---

# 94. Canonical flow — Step-up

```text
existing session
       │
       ▼
AXSECURITY requires stronger authentication
       │
       ▼
AXAUTH.reauthenticate()
       │
       ▼
additional factor
       │
       ▼
new authentication assurance
       │
       ▼
AXSECURITY
```

---

# 95. Canonical flow — Session resumption

```text
old session
    │
    ▼
resume credential
    │
    ▼
verify integrity
    │
    ▼
verify expiry
    │
    ▼
verify audience/binding
    │
    ▼
new session epoch
    │
    ▼
ACTIVE
```

---

# 96. Canonical flow — Revocation

```text
credential
    │
    ▼
AXCERT
    │
    ▼
AXTRUST
    │
    ▼
REVOKED
    │
    ▼
AXAUTH session registry
    │
    ▼
dependent sessions
    │
    ▼
REVOKED / CLOSED
```

---

# 97. Performance architecture

Common authentication path phải tối ưu:

```text
prevalidated credential
        ↓
cached trust result
        ↓
challenge
        ↓
single crypto verification
        ↓
session creation
```

Không parse lại credential hoặc compile policy mỗi request.

---

# 98. Credential cache

Có thể cache:

```text
credential_fingerprint
trust_policy_version
purpose
validation_epoch
```

Nhưng **proof-of-possession không được cache như authentication success** nếu challenge/session binding yêu cầu proof mới.

---

# 99. Session lookup

Session registry nên dùng:

```text
sharded hash table
generation-safe handles
per-core read paths
```

để giảm global lock contention.

---

# 100. Memory allocation

Hot authentication path:

```text
challenge
proof
session metadata
```

nên sử dụng pool/slab.

Không allocation tùy tiện cho từng field.

---

# 101. Formal invariants

### AUTH-INV-01
Authentication và authorization là hai tầng độc lập.

### AUTH-INV-02
AXAUTH không tự cấp authorization.

### AUTH-INV-03
AXAUTH không reimplement cryptographic primitives.

### AUTH-INV-04
AXCRYPTO là nguồn cryptographic primitive duy nhất cho core AXAUTH.

### AUTH-INV-05
Credential structure thuộc AXCERT.

### AUTH-INV-06
Trust evaluation thuộc AXTRUST.

### AUTH-INV-07
Identity lifecycle thuộc AXIDENTITY.

### AUTH-INV-08
Authentication success phải có verifiable proof/evidence.

### AUTH-INV-09
Certificate possession không đồng nghĩa private-key possession.

### AUTH-INV-10
Public-key authentication phải hỗ trợ proof-of-possession.

### AUTH-INV-11
Challenge phải được tạo bằng cryptographically secure randomness.

### AUTH-INV-12
Authentication challenge phải có expiration semantics.

### AUTH-INV-13
Replay của expired challenge phải bị reject.

### AUTH-INV-14
Authentication proof phải bind vào challenge khi protocol yêu cầu.

### AUTH-INV-15
Authentication proof phải bind vào protocol identity.

### AUTH-INV-16
Authentication proof phải bind vào negotiated parameters khi cần.

### AUTH-INV-17
Authentication proof phải chống protocol confusion.

### AUTH-INV-18
Downgrade negotiation phải được detect/prevent theo policy.

### AUTH-INV-19
Authenticated session không được tạo từ partially verified state.

### AUTH-INV-20
Session identity phải bind với authenticated principal.

### AUTH-INV-21
Session key material không được lưu plaintext trong session metadata.

### AUTH-INV-22
Session key phải được quản lý bởi AXCRYPTO.

### AUTH-INV-23
Session key directions phải được tách khi protocol yêu cầu.

### AUTH-INV-24
Session key epochs phải có identity riêng.

### AUTH-INV-25
Session expiration phải invalidate authentication state.

### AUTH-INV-26
Credential revocation phải có cơ chế invalidation đối với dependent sessions.

### AUTH-INV-27
Session handles phải opaque và generation-safe.

### AUTH-INV-28
Authentication state transitions phải deterministic.

### AUTH-INV-29
Authentication cancellation không được để session ở trạng thái ambiguous.

### AUTH-INV-30
Authentication timeout không được tạo thành authentication success.

### AUTH-INV-31
Authentication policy phải versioned.

### AUTH-INV-32
Policy hot reload không được thay đổi policy snapshot của operation đang chạy.

### AUTH-INV-33
Session resumption credential không được đồng nhất với raw session ID.

### AUTH-INV-34
Replay cache phải có bounded lifetime.

### AUTH-INV-35
Duplicate authentication factors không được count nhiều lần trong MFA threshold.

### AUTH-INV-36
Authentication transcript không được ghi secret material vào trace mặc định.

### AUTH-INV-37
AI không được bypass hoặc lower authentication requirements.

### AUTH-INV-38
Remote authentication/network operations phải explicit, không hidden.

### AUTH-INV-39
Deterministic simulation không được sử dụng deterministic RNG cho production authentication.

### AUTH-INV-40
`AXAUTH 5.0` phải giữ boundary độc lập giữa authentication, trust và authorization.

---

# 102. Definition of Done

`AXAUTH 5.0` hoàn tất khi có:

- authentication context;
- principal model;
- authentication methods;
- credential presentation;
- challenge/response;
- proof-of-possession;
- authentication transcript;
- canonical transcript representation;
- replay protection;
- channel binding;
- protocol negotiation;
- downgrade protection;
- algorithm agility;
- authentication policy;
- policy compiler;
- AuthPolicyIR;
- authentication state machine;
- authentication assurance;
- MFA composition;
- threshold factors;
- step-up authentication;
- reauthentication;
- session establishment;
- session lifecycle;
- session expiration;
- idle timeout;
- session renewal;
- session resumption;
- session epochs;
- session key integration;
- key rotation;
- credential revocation propagation;
- session registry;
- replay cache;
- certificate authentication;
- public-key authentication;
- device authentication;
- hardware-backed provider;
- password-authentication abstraction;
- one-time credential abstraction;
- authentication errors;
- error-information partitioning;
- async authentication;
- cancellation;
- deadlines;
- deterministic simulation;
- fault injection;
- authentication tracing;
- policy versioning;
- policy hot reload;
- immutable evaluation snapshots;
- native ABI;
- compiler intrinsics;
- AXIDENTITY integration;
- AXCERT integration;
- AXCRYPTO integration;
- AXTRUST integration;
- AXSECURITY handoff;
- AXNETWORK/AXASYNC integration boundary;
- AI security boundary;
- 40 invariants.

**AXAUTH 5.0 → FROZEN.**

---

# Security stack hiện tại

Sau `AXAUTH`, chuỗi đã có đầy đủ bốn lớp logic quan trọng:

```text
┌─────────────────────────────────────────────────────┐
│                    AXSECURITY                       │
│ authorization / capability / sandbox / enforcement  │
└─────────────────────────▲───────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│                       AXAUTH                         │
│ authentication / proof / MFA / session               │
└─────────────────────────▲───────────────────────────┘
                          │
┌─────────────────────────┴───────────────────────────┐
│                      AXTRUST                         │
│ trust policy / evidence / trust evaluation           │
└───────────────▲──────────────────────▲───────────────┘
                │                      │
       ┌────────┴────────┐      ┌──────┴───────┐
       │     AXCERT      │      │  AXIDENTITY  │
       │ credentials     │      │ identity     │
       │ certificates    │      │ lifecycle    │
       └────────▲────────┘      └──────────────┘
                │
         ┌──────┴───────┐
         │   AXCRYPTO   │
         │ crypto       │
         │ primitives   │
         └──────────────┘
```

Về mặt semantic:

```text
AXCRYPTO
    ↓
"Proof có hợp lệ về mặt cryptography không?"

AXCERT
    ↓
"Credential/certificate/evidence có cấu trúc và chain hợp lệ không?"

AXTRUST
    ↓
"Evidence này có đáp ứng trust policy không?"

AXAUTH
    ↓
"Entity hiện tại có chứng minh được quyền sở hữu credential và tạo authenticated session không?"

AXSECURITY
    ↓
"Authenticated principal có được phép thực hiện operation này không?"
```

---

# BOOTSTRAP-756 — AXCAPABILITY

**Native Capability, Authority Token, Delegation, Object Rights & Least-Authority Runtime 5.0**

Tầng tiếp theo sẽ bắt đầu phần **authorization primitive** thực sự của Axiom.

Kiến trúc dự kiến:

```text
AXAUTH
   │
   ▼
authenticated principal
   │
   ▼
AXCAPABILITY
   │
   ├── object capability
   ├── rights
   ├── delegation
   ├── attenuation
   ├── authority scope
   ├── expiry
   └── revocation
   │
   ▼
AXSECURITY
   │
   ▼
resource access
```

Đây sẽ là bước quan trọng để biến mô hình security của Axiom từ:

```text
identity → login → permission check
```

thành một mô hình **capability-based native security**, phù hợp với mục tiêu trước đó của Axiom về handle/object identity, process isolation, IPC và least-authority design.