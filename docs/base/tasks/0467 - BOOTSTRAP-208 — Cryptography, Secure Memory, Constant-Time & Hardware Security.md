# BOOTSTRAP-208 — Cryptography, Secure Memory, Constant-Time & Hardware Security

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 208:

> **Axiom phải cho phép xây dựng cryptographic software hiệu năng cao mà compiler hiểu được các security contract quan trọng, thay vì coi crypto chỉ là một hàm `extern`.**

Điểm quan trọng: **constant-time không thể chỉ là lời hứa của programmer**. Compiler phải hiểu đây là một semantic/security contract để không tối ưu làm mất tính chất đó.

---

# 208.1. Phân tầng Cryptography

Kiến trúc:

```text
Application
    │
    ├── Authentication
    ├── Authorization
    ├── Secure Channel
    └── Protocol
            │
            ▼
     Cryptographic Library
            │
    ┌───────┼────────┐
    ▼       ▼        ▼
   AEAD    Hash      Signature
    │       │        │
    └───────┼────────┘
            ▼
       Crypto Backend
            │
      ┌─────┼─────┐
      ▼     ▼     ▼
    CPU    SIMD   Hardware
```

Core không chứa thuật toán cụ thể.

---

# 208.2. Cryptographic primitive là typed API

Không dùng API kiểu:

```text
encrypt(bytes, bytes)
```

một cách mơ hồ.

Nên có các type:

```text
Key
Nonce
Ciphertext
Plaintext
Tag
Signature
PublicKey
PrivateKey
Digest
```

để compiler và programmer không dễ truyền nhầm dữ liệu.

---

# 208.3. Key không phải Bytes

Ví dụ:

```text
Key<AES256>
```

khác:

```text
Bytes
```

Một key có semantic contract riêng:

```text
secret
algorithm
length
lifetime
usage
```

---

# 208.4. Key typing

Conceptual:

```axiom
key: Key<AES256>
nonce: Nonce<AESGCM>
```

Không cho phép implicit:

```text
Key<AES256> → Key<ChaCha20>
```

---

# 208.5. Secret data

Compiler có thể biết một value là:

```text
Secret<T>
```

và áp dụng security metadata:

```text
no-debug
no-logging
no-implicit-copy
secure-drop
```

---

# 208.6. Secret ≠ immutable

Secret có thể mutable nếu thuật toán cần:

```text
SecretBuffer
```

nhưng capability vẫn kiểm soát mutation.

---

# 208.7. Secret copying

Không cấm mọi copy tuyệt đối, nhưng copy secret phải là semantic operation có thể quan sát qua security tooling.

Mục tiêu:

```text
không vô tình copy key
```

---

# 208.8. Secret lifetime

Key có thể được:

```text
create
use
rotate
destroy
```

và compiler/library đảm bảo ownership.

---

# 208.9. Zeroization

Một secret buffer có thể có:

```text
SecureDrop
```

để zero memory trước khi resource/storage được release.

Compiler không được loại bỏ operation này nếu semantic contract yêu cầu.

---

# 208.10. Dead-store elimination exception

Thông thường:

```text
x = 0
```

ngay trước deallocation có thể bị optimizer loại.

Nhưng với:

```text
SecureZero(x)
```

đây là observable security operation và **không được loại bỏ**.

---

# 208.11. Constant-time

Axiom định nghĩa security property:

> **Execution behavior không được phụ thuộc vào secret data theo các kênh được contract bảo vệ.**

Không giới hạn đơn giản ở "số instruction luôn giống nhau".

---

# 208.12. Constant-time scope

Constant-time có thể áp dụng cho:

```text
@constant_time
fn verify(...)
```

hoặc block:

```text
@constant_time {
    ...
}
```

---

# 208.13. Secret-dependent branch

Trong constant-time region:

```axiom
if secret_bit {
    ...
}
```

phải bị compiler kiểm tra.

Nếu branch ảnh hưởng observable timing:

```text
compile error
```

hoặc yêu cầu explicit unsafe/security escape.

---

# 208.14. Secret-dependent memory access

Nguy hiểm:

```text
table[secret]
```

Compiler phải phát hiện trong constant-time code nếu index có thể leak qua cache/memory behavior.

---

# 208.15. Constant-time ≠ no branch

Branch trên public data vẫn hợp lệ:

```text
if packet_length > 0 {
    ...
}
```

Vấn đề là dependency:

```text
public
```

hay:

```text
secret
```

---

# 208.16. Data classification

Compiler security analysis có thể phân biệt:

```text
PUBLIC
SECRET
SENSITIVE
UNKNOWN
```

`UNKNOWN` không được tự động coi là PUBLIC trong constant-time proof.

---

# 208.17. Secret flow

Ví dụ:

```text
key
 ↓
hash
 ↓
digest
```

ta cần security taint:

```text
SECRET → derived SECRET
```

hoặc primitive-specific declassification.

---

# 208.18. Public declassification

Hash của secret không mặc định trở thành public.

Ví dụ password hash:

```text
hash(password)
```

vẫn có thể là sensitive.

Do đó:

```text
Secret
 ↓
Hash
 ↓
SensitiveDigest
```

---

# 208.19. Declassification

Nếu application muốn công khai một derived value:

```text
declassify(x)
```

phải là explicit security operation.

Không implicit.

---

# 208.20. Constant-time comparison

Không dùng:

```text
a == b
```

cho cryptographic secret nếu implementation có early exit.

Library cung cấp:

```text
constant_time_equal(a, b)
```

Compiler có thể recognize primitive này.

---

# 208.21. Compiler recognition

Compiler có thể có intrinsic:

```text
ct_eq
ct_select
ct_compare
ct_swap
```

nhưng chúng vẫn có semantic definitions.

---

# 208.22. Constant-time select

Ví dụ conceptual:

```text
result = ct_select(condition, a, b)
```

không branch theo secret.

---

# 208.23. Constant-time arithmetic

Compiler phải tránh biến đổi:

```text
constant-time arithmetic
```

thành implementation có secret-dependent control flow nếu contract cấm.

---

# 208.24. Division

Một vấn đề quan trọng:

```text
secret / public
```

có thể tạo instruction latency khác nhau tùy architecture.

Constant-time verifier không được chỉ kiểm tra source-level branch.

Backend security metadata phải tồn tại.

---

# 208.25. Variable-latency instructions

Backend có thể đánh dấu instruction:

```text
ConstantLatency
VariableLatency
UnknownLatency
```

Trong strict constant-time profile:

```text
VariableLatency
UnknownLatency
```

không được dùng trên secret-dependent operands nếu contract không cho phép.

---

# 208.26. CPU instruction selection

Compiler có thể chọn:

```text
AES-NI
AVX2
AVX-512
SHA extensions
NEON
```

nhưng phải giữ security contract.

---

# 208.27. Hardware acceleration

Crypto backend:

```text
AES-GCM
ChaCha20
SHA-256
SHA-3
```

có thể sử dụng hardware instructions.

Không cần programmer viết assembly.

---

# 208.28. SIMD crypto

Compiler có thể vectorize independent operations.

Nhưng vectorization phải giữ:

```text
constant-time
memory access
observable behavior
```

---

# 208.29. Constant-time vectorization

Nếu source có:

```text
ct loop
```

compiler có thể vectorize nếu proof vẫn hợp lệ.

Nếu không:

```text
do not transform
```

---

# 208.30. Fast-math interaction

Crypto code không được tự động áp dụng fast-math.

Đặc biệt:

```text
floating-point
```

không phải lựa chọn mặc định cho cryptographic arithmetic.

---

# 208.31. Cryptographic randomness

Randomness có nhiều cấp:

```text
PseudoRandom
SecureRandom
HardwareRandom
DeterministicRandom
```

không được gộp thành `Random`.

---

# 208.32. CSPRNG

API:

```text
SecureRandom
```

phải có explicit security source.

Ví dụ:

```text
OS entropy
hardware RNG
approved DRBG
```

---

# 208.33. Randomness failure

Nếu hệ thống không lấy được entropy:

```text
Result<RandomBytes, RandomError>
```

Không silently fallback sang insecure PRNG.

---

# 208.34. Deterministic cryptographic tests

Test environment có thể inject:

```text
DeterministicRandom
```

nhưng production API không được âm thầm dùng implementation này.

---

# 208.35. Nonce

Nonce là type riêng:

```text
Nonce<Algorithm>
```

không chỉ là `[u8; 12]`.

---

# 208.36. Nonce uniqueness

Một số algorithm yêu cầu:

```text
unique nonce per key
```

Đây là semantic protocol invariant, không chỉ type-level length check.

---

# 208.37. AEAD

High-level API:

```text
seal(key, nonce, plaintext, associated_data)
open(key, nonce, ciphertext, associated_data)
```

---

# 208.38. Authentication failure

AEAD failure:

```text
AuthenticationFailed
```

là recoverable Result.

Không trả plaintext một phần.

---

# 208.39. Partial plaintext

Nếu authentication chưa thành công:

```text
plaintext capability
```

không được expose cho caller.

---

# 208.40. Hash

Hash API:

```text
Hash<Algorithm>
```

và incremental:

```text
Hasher
```

---

# 208.41. Hash state ownership

Hasher state có ownership bình thường:

```text
Hasher
 ↓ move
finalize()
```

Finalize có thể consume state.

---

# 208.42. MAC

MAC:

```text
Mac<KeyedAlgorithm>
```

khác Hash.

---

# 208.43. Signature

Signature:

```text
Signature<Algorithm>
```

khác MAC vì verification không yêu cầu secret key phía verifier.

---

# 208.44. Public/private key distinction

Compiler type system không cho:

```text
PrivateKey → PublicKey
```

trừ explicit derivation:

```text
derive_public_key()
```

---

# 208.45. Key exchange

Ví dụ:

```text
PrivateKey
    ↓
KeyExchange
    ↓
SharedSecret
```

`SharedSecret` không tự động trở thành application key.

---

# 208.46. KDF

Key derivation:

```text
KDF
 ↓
DerivedKey<Context>
```

Context/domain separation phải explicit.

---

# 208.47. Domain separation

Cryptographic APIs nên hỗ trợ:

```text
context
purpose
label
```

để tránh reuse cùng secret material cho các protocol khác nhau.

---

# 208.48. Key usage restrictions

Có thể metadata:

```text
Key<EncryptOnly>
Key<SignOnly>
Key<KeyExchange>
```

để hạn chế misuse.

---

# 208.49. Key rotation

Key lifecycle:

```text
Active
 ↓
Rotating
 ↓
Deprecated
 ↓
Revoked
```

là library/security state, không phải Core type state bắt buộc.

---

# 208.50. Certificate

Certificate:

```text
Certificate
PublicKey
Signature
Validity
Extensions
```

---

# 208.51. Trust store

Trust store là external policy:

```text
TrustStore
```

không hard-code vào compiler.

---

# 208.52. Certificate verification

Verification trả structured result/error:

```text
Expired
NotYetValid
UnknownIssuer
InvalidSignature
HostnameMismatch
Revoked
UnsupportedAlgorithm
```

---

# 208.53. Secure channel

Network stack:

```text
TcpStream
    ↓
TlsStream
    ↓
HttpConnection
```

đã phù hợp với architecture 206.

---

# 208.54. Authentication

Authentication và encryption là hai vấn đề khác nhau.

Axiom không gộp:

```text
encrypted
```

với:

```text
authenticated
```

---

# 208.55. Authorization

Authorization nằm trên authentication:

```text
Identity
 ↓
Authentication
 ↓
Authorization
 ↓
Action
```

---

# 208.56. Capability tokens

Axiom có thể xây capability token:

```text
CapabilityToken<Resource>
```

nhưng đây là library/security abstraction.

Không phải Core `capability` memory type.

Hai khái niệm phải giữ riêng:

```text
Memory Capability
        ≠
Security Authority Capability
```

---

# 208.57. Security authority

Security capability có thể đại diện:

```text
NetworkAccess
FileAccess
DatabaseAccess
DeviceAccess
```

nhưng không thay đổi memory verifier.

---

# 208.58. Memory capability vs authority

Đây là distinction quan trọng:

```text
view<T>
```

nói:

> được đọc vùng memory này.

Trong khi:

```text
NetworkCapability
```

nói:

> được thực hiện network operation này.

---

# 208.59. Secure memory storage

Có thể có:

```text
SecureBuffer<T>
```

với:

- locked pages nếu OS hỗ trợ;
- zero-on-drop;
- no swap policy nếu hỗ trợ;
- restricted debugging policy.

---

# 208.60. Không guarantee tuyệt đối

Compiler không được tuyên bố:

```text
SecureBuffer
```

đảm bảo secret không bao giờ xuất hiện ở swap/dump/register/cache trên mọi hardware.

Chỉ guarantee những semantics mà target/platform thực sự hỗ trợ.

---

# 208.61. Sensitive debug policy

Compiler/debugger nên biết:

```text
Secret
```

không nên mặc định hiển thị trong:

```text
debugger
crash dump
AI context
logs
```

---

# 208.62. AI security boundary

Đây đặc biệt quan trọng với Axiom.

CompilerDB/AI tooling phải tránh đưa:

```text
private keys
passwords
secret buffers
```

vào AI context mặc định.

AI có thể nhận:

```text
type
ownership
security classification
proof
```

thay vì raw secret value.

---

# 208.63. Compiler diagnostics

Không được diagnostic kiểu:

```text
expected key:
"actual secret value..."
```

Compiler phải redact sensitive values.

---

# 208.64. Secure logging

`Secret<T>` không tự động implement debug formatting:

```text
Debug(Secret)
```

nên cho:

```text
<redacted>
```

---

# 208.65. Side-channel model

Axiom security model nhận diện các kênh:

```text
Timing
Cache
Branch prediction
Memory access
Power
EM
Speculation
Resource contention
```

Compiler chỉ có thể kiểm soát một phần.

---

# 208.66. Constant-time scope

`@constant_time` không có nghĩa:

> chống mọi side channel.

Nó là một contract giới hạn phạm vi:

> compiler không được tạo các secret-dependent behaviors thuộc các lớp mà target/profile có thể kiểm chứng.

---

# 208.67. Speculation

Compiler/security backend có thể cung cấp primitive:

```text
speculation_barrier()
```

ở system layer.

---

# 208.68. Secret-dependent indexing

Trong strict mode:

```text
table[secret]
```

có thể bị reject.

Có thể thay bằng:

```text
constant_time_lookup(table, secret)
```

---

# 208.69. Constant-time verification

Compiler pipeline:

```text
Typed MIR
   ↓
Security Taint Analysis
   ↓
Constant-Time Analysis
   ↓
Verified MIR
   ↓
Optimization
   ↓
Backend Security Validation
```

---

# 208.70. Optimization legality

Optimization pass phải khai báo:

```text
preserves_constant_time = true
```

nếu áp dụng lên constant-time region.

Nếu không chứng minh được:

```text
skip transformation
```

---

# 208.71. Security-aware alias analysis

Compiler có thể sử dụng:

```text
SecretRegion
PublicRegion
```

để tránh những optimization tạo side-channel.

---

# 208.72. Security-aware vectorization

Vectorization được phép nếu:

```text
semantic correctness
+
constant-time contract
```

đều được bảo toàn.

---

# 208.73. FFI crypto

Foreign crypto library phải khai báo:

```text
FfiContract
```

bao gồm:

```text
constant-time
secret handling
memory ownership
thread safety
```

---

# 208.74. Assembly crypto

Inline assembly/system intrinsic có thể khai báo:

```text
@constant_time
@secret_safe
```

nhưng compiler không được tin annotation vô điều kiện nếu có machine-verifiable contract.

Unsafe vẫn là trust boundary.

---

# 208.75. Hardware crypto

Hardware acceleration có contract:

```text
CryptoBackend
```

và có thể fallback:

```text
software backend
```

nhưng security profile phải biết backend nào đang được dùng.

---

# 208.76. CPU feature dispatch

Có thể:

```text
AES-NI
AVX2
AVX-512
NEON
SHA extensions
```

với multiversioning.

Compiler đảm bảo mỗi variant có cùng security semantics.

---

# 208.77. Hardware security

Platform layer có thể expose:

```text
TPM
Secure Enclave
HSM
KeyStore
Hardware RNG
```

---

# 208.78. TPM

TPM resource:

```text
TpmDevice
TpmKey
```

không expose private key bytes nếu key nằm hardware.

---

# 208.79. Hardware-backed key

Một key có thể có:

```text
HardwareKey
```

không thể `Copy` ra `Bytes`.

---

# 208.80. HSM

HSM API tương tự:

```text
Remote/HardwareKeyHandle
```

operations chạy bên ngoài process memory.

---

# 208.81. Secure enclave

Secure enclave execution là execution/storage domain riêng ở platform layer.

Không giả định CPU memory capability có thể truy cập trực tiếp enclave memory.

---

# 208.82. Key handles

Hardware key identity:

```text
KeyHandle
```

khác:

```text
PrivateKeyBytes
```

---

# 208.83. Secure deletion

Hardware-backed key có thể:

```text
destroy()
```

nhưng semantics phụ thuộc device.

Không tuyên bố physical destruction nếu hardware chỉ revoke key.

---

# 208.84. Password handling

Password phải được coi là:

```text
Secret<Text>
```

không plain `String` trong security API.

---

# 208.85. Password hashing

Password storage nên dùng dedicated password KDF:

```text
Argon2
scrypt
bcrypt
```

ở library layer.

Không dùng raw SHA-256 như password hashing API.

---

# 208.86. Password verification

Verification nên dùng constant-time comparison khi thích hợp.

---

# 208.87. Cryptographic API misuse resistance

High-level API nên làm impossible hoặc khó:

```text
wrong key type
wrong nonce size
wrong algorithm
plaintext after auth failure
secret accidental logging
```

---

# 208.88. Algorithm agility

Protocol có thể support nhiều algorithms nhưng selection phải explicit và policy-controlled.

Không tự động downgrade sang insecure algorithm.

---

# 208.89. Deprecated algorithms

Library metadata có thể đánh dấu:

```text
Secure
Legacy
Deprecated
Forbidden
```

Tooling cảnh báo hoặc reject theo security profile.

---

# 208.90. Cryptographic protocol versioning

Security protocol version phải tham gia:

```text
SchemaFingerprint
ProtocolFingerprint
```

hoặc security-specific fingerprint khi cần.

---

# 208.91. Security profile

Build profile có thể:

```text
security-strict
security-hardened
constant-time
embedded
```

nhưng không thay đổi Core semantics.

---

# 208.92. Hardened build

Hardened profile có thể bật:

```text
stack protection
CFI
ASLR-compatible output
RELRO
W^X
shadow stack
control-flow protection
```

tùy target.

---

# 208.93. Security metadata

Compiler có thể xuất:

```text
.axsec
```

hoặc tích hợp vào `.axmeta`.

Metadata có thể mô tả:

```text
secret flows
constant-time regions
FFI security contracts
required hardware features
security profile
```

---

# 208.94. Security metadata không phải runtime

Không được biến security metadata thành mandatory runtime dependency.

---

# 208.95. Security verification boundary

Final compiler pipeline:

```text
Source
 ↓
Typed HIR
 ↓
MIR
 ↓
Ownership
 ↓
Capability
 ↓
Concurrency
 ↓
Security/Taint
 ↓
Constant-Time
 ↓
Verified MIR
 ↓
Optimization
 ↓
Backend Security Validation
 ↓
Machine Code
```

---

# 208.96. Crypto testing

Testing phải bao gồm:

```text
known-answer tests
test vectors
property tests
fuzzing
differential tests
negative tests
constant-time checks
fault injection
```

---

# 208.97. Constant-time testing

Timing tests chỉ là evidence.

Không được coi:

```text
"benchmark thấy timing giống nhau"
```

là proof.

Proof phải dựa vào compiler/security model.

---

# 208.98. Formal security properties

Những property có thể formalize:

```text
NoSecretBranch
NoSecretIndex
NoSecretDependentLoop
NoSecretLeakToIO
NoSecretDebug
NoSecretImplicitCopy
```

tùy security profile.

---

# 208.99. Crypto compiler contract

Mỗi crypto/security-sensitive optimization phải có:

```text
Preconditions
Transformation
PreservedSecurityProperties
Validation
```

Nếu không chứng minh:

```text
NO TRANSFORM
```

---

# 208.100. Cryptography & security invariants — `ASEC2`

### `ASEC2-20`
Cryptographic primitives shall remain library/system abstractions above Core.

### `ASEC2-21`
Cryptographic keys shall use typed semantic representations.

### `ASEC2-22`
Keys shall not implicitly convert to arbitrary byte buffers.

### `ASEC2-23`
Secret values shall carry security classification where required.

### `ASEC2-24`
Secret data shall not be implicitly exposed through debugging or diagnostics.

### `ASEC2-25`
Required secure-zeroization operations shall be semantically observable to the optimizer.

### `ASEC2-26`
Constant-time shall be an explicit compiler-visible security contract.

### `ASEC2-27`
Secret-dependent control flow shall be rejected or explicitly authorized in strict constant-time regions.

### `ASEC2-28`
Secret-dependent memory access shall be rejected or explicitly authorized according to the active security profile.

### `ASEC2-29`
Unknown security classification shall not silently become public inside strict constant-time analysis.

### `ASEC2-30`
Security taint shall propagate through derived cryptographic values according to primitive contracts.

### `ASEC2-31`
Declassification shall be explicit.

### `ASEC2-32`
Constant-time comparison shall use a dedicated semantic primitive.

### `ASEC2-33`
Variable-latency machine operations shall be tracked by the security-aware backend.

### `ASEC2-34`
Optimization shall not violate constant-time contracts.

### `ASEC2-35`
Vectorization shall preserve constant-time guarantees.

### `ASEC2-36`
CPU feature specialization shall preserve cryptographic semantics and security contracts.

### `ASEC2-37`
Hardware crypto acceleration shall remain semantically equivalent to the approved software implementation.

### `ASEC2-38`
CSPRNG failure shall not silently fall back to insecure randomness.

### `ASEC2-39`
Nonce types shall remain algorithm-specific where nonce uniqueness/format is security-critical.

### `ASEC2-40`
AEAD authentication failure shall not expose unauthenticated plaintext.

### `ASEC2-41`
Hash, MAC, signature and encryption semantics shall remain distinct.

### `ASEC2-42`
Private and public key types shall remain distinct.

### `ASEC2-43`
Key derivation shall support explicit domain separation.

### `ASEC2-44`
Cryptographic keys shall support explicit lifecycle and rotation semantics.

### `ASEC2-45`
Hardware-backed keys shall not implicitly become extractable private-key bytes.

### `ASEC2-46`
TPM/HSM/secure-enclave resources shall obey ordinary Axiom resource ownership.

### `ASEC2-47`
Security authority capabilities shall remain distinct from memory capabilities.

### `ASEC2-48`
Authentication shall remain distinct from authorization.

### `ASEC2-49`
Encryption shall not imply authentication.

### `ASEC2-50`
Security profiles shall not silently weaken cryptographic guarantees.

### `ASEC2-51`
Deprecated or forbidden cryptographic algorithms shall be enforceable by tooling/profile policy.

### `ASEC2-52`
Password hashing shall use dedicated password-KDF APIs rather than generic hashes.

### `ASEC2-53`
Security-sensitive FFI shall declare relevant security contracts.

### `ASEC2-54`
Unsafe assembly shall not automatically gain verified constant-time status merely through an annotation.

### `ASEC2-55`
Constant-time testing shall not be treated as a substitute for compiler-level security verification.

### `ASEC2-56`
Security metadata shall remain optional tooling/build metadata rather than mandatory runtime state.

### `ASEC2-57`
Compiler diagnostics shall redact secret values.

### `ASEC2-58`
AI tooling shall not expose secret values merely to explain compiler behavior.

### `ASEC2-59`
Security properties shall be visible through CompilerDB.

### `ASEC2-60`
Security-sensitive generated code shall pass ordinary compiler verification.

### `ASEC2-61`
Crypto code shall remain compatible with zero-cost abstraction principles.

### `ASEC2-62`
Crypto APIs shall not require garbage collection.

### `ASEC2-63`
Crypto APIs shall not require a monolithic runtime.

### `ASEC2-64`
Security contracts shall compose with Ownership, Capability, Concurrency, Async, FFI and GPU models.

### `ASEC2-65`
Security verification shall occur before optimization.

### `ASEC2-66`
Security-aware backend validation shall occur after machine lowering.

### `ASEC2-67`
An optimization lacking a proof of security-contract preservation shall not be applied to protected code.

### `ASEC2-68`
Constant-time guarantees shall be target/profile-specific where hardware behavior differs.

### `ASEC2-69`
Axiom shall distinguish memory safety from cryptographic side-channel security.

### `ASEC2-70`
Axiom shall not claim protection against physical side channels beyond the guarantees established by the target and security profile.

### `ASEC2-71`
Cryptographic protocol compatibility shall remain distinct from Axiom ABI compatibility.

### `ASEC2-72`
Security failures shall be represented through explicit Result/error semantics where recovery is possible.

### `ASEC2-73`
Cryptographic verification shall remain deterministic under fixed inputs and approved randomness sources.

### `ASEC2-74`
Security regression tests shall become permanent compiler/library conformance tests.

### `ASEC2-75`
AI-generated cryptographic code shall receive exactly the same security verification as human-written code.

---

# Kiến trúc security cuối cùng

Axiom hiện có một pipeline khá mạnh:

```text
                 SOURCE
                    │
                    ▼
               Typed HIR
                    │
                    ▼
                  MIR
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   Ownership    Capability   Concurrency
        │           │            │
        └───────────┼────────────┘
                    ▼
              Security/Taint
                    │
                    ▼
             Constant-Time
                    │
                    ▼
             VERIFIED MIR
                    │
                    ▼
              Optimization
                    │
                    ▼
          Security-aware Backend
                    │
                    ▼
               MACHINE CODE
```

Điểm quan trọng nhất là **security không trở thành một hệ thống compiler riêng biệt**. Nó sử dụng chính nền móng Axiom đã xây:

```text
Ownership
Capability
Effect
Concurrency
FFI
CompilerDB
Verified MIR
```

và bổ sung:

```text
Security Classification
Taint
Constant-Time Contract
Security-aware Optimization
```

Điều này giữ đúng triết lý:

> **Compiler phức tạp hơn, nhưng ngôn ngữ không bắt programmer phải phức tạp hơn.**

---

# BOOTSTRAP-209 — AI/ML, Tensor, Automatic Differentiation & Heterogeneous Computing

**TRẠNG THÁI: NEXT**

Đây là bước đặc biệt quan trọng đối với mục tiêu ban đầu của Axiom: **AI support trên CPU + GPU nhưng vẫn giữ hiệu năng native**.

209 sẽ hợp nhất:

```text
Tensor
Shape
Stride
Layout
DType
SIMD
GPU
CPU
Autodiff
Graph
Kernel
Fusion
Memory planning
Training
Inference
Quantization
Sparse tensor
Distributed training
Collective communication
CUDA
ROCm
Metal
DirectML
CPU backend
```

và đặc biệt giải quyết vấn đề:

> **Làm thế nào để Axiom có khả năng AI/Tensor gần với PyTorch nhưng không biến ngôn ngữ thành một framework AI, không bắt buộc runtime AI, và vẫn cho phép compiler tối ưu tensor operation xuống CPU SIMD/GPU kernel/native code?**