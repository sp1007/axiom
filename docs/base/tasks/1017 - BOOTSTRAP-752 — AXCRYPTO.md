# BOOTSTRAP-752 — AXCRYPTO

**Namespace:** `AXCRYPTO`  
**Phase:** Axiom Civilization Runtime / Native Cryptography, Hashing, Key Material & Secure Randomness Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXCRYPTO` là tầng cryptographic primitive native của Axiom.

Nó cung cấp:

- cryptographic hashing;
- MAC;
- KDF;
- AEAD;
- symmetric encryption;
- public-key primitives;
- digital signatures;
- key generation;
- key import/export;
- secure randomness;
- key derivation;
- nonce/IV management;
- secure comparison;
- key zeroization;
- cryptographic algorithm capabilities;
- cryptographic provider abstraction;
- hardware acceleration;
- constant-time primitives;
- deterministic test vectors;
- cryptographic self-tests;
- versioned algorithm identifiers.

Mục tiêu quan trọng:

> **AXCRYPTO cung cấp primitive; AXSECURITY quyết định primitive đó được dùng để làm gì và ai có quyền sử dụng nó.**

---

# 2. Vị trí kiến trúc

```text
                    AXAPPLICATION
                           │
                           ▼
                       AXSECURITY
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
         AXIDENTITY                   AXCRYPTO
                                           │
                    ┌──────────┬───────────┼──────────┐
                    ▼          ▼           ▼          ▼
                   HASH       MAC         AEAD       SIGN
                                           │
                                           ▼
                                        AXCODEC
                                           │
                                           ▼
                                        AXSTREAM
```

`AXCRYPTO` nằm dưới các security protocols nhưng trên primitive machine implementation.

---

# 3. Boundary

## AXCRYPTO sở hữu

- cryptographic algorithms;
- hash;
- MAC;
- KDF;
- encryption/decryption;
- AEAD;
- signature;
- key material;
- secure random;
- cryptographic contexts;
- nonce handling;
- secure memory handling;
- constant-time operations;
- algorithm negotiation metadata;
- hardware crypto acceleration.

## AXCRYPTO không sở hữu

### AXSECURITY

Sở hữu:

- authorization;
- capability;
- sandbox;
- policy;
- access control.

### AXIDENTITY

Sở hữu:

- identity;
- credential lifecycle;
- identity binding.

### AXCODEC

Sở hữu:

- serialization;
- binary representation;
- framing;
- compression;
- non-cryptographic checksum.

### AXNETWORK

Sở hữu:

- TLS-like/network protocol semantics;
- transport.

### AXSTORAGE

Sở hữu:

- persistent storage semantics.

---

# 4. Không có “Crypto Authority”

Một key object không tự động cấp quyền.

```text
key
```

chỉ có nghĩa:

```text
cryptographic material
```

Không có nghĩa:

```text
"application được phép dùng key này"
```

Quyền sử dụng key thuộc:

```text
AXSECURITY policy
```

---

# 5. Core model

```text
crypto_algorithm
crypto_provider

crypto_key
crypto_key_handle
crypto_key_spec

crypto_hash
crypto_mac
crypto_kdf

crypto_cipher
crypto_aead

crypto_signature
crypto_verifier

crypto_nonce
crypto_random

crypto_context
crypto_limits
crypto_error
crypto_capability

crypto_test_vector
crypto_trace
```

---

# 6. Algorithm identity

Mỗi algorithm có stable identifier:

```text
crypto_algorithm_id {
    namespace
    name
    version
}
```

Không dùng:

- function pointer;
- vtable address;
- implementation address;

làm algorithm identity.

---

# 7. Algorithm lifecycle

Algorithm descriptor:

```text
algorithm {
    id
    class
    security_level
    key_sizes
    nonce_sizes
    output_sizes
    capabilities
    backend
}
```

Backend có thể là:

```text
SOFTWARE
CPU_INSTRUCTION
OS_CRYPTO
HARDWARE_DEVICE
SECURE_ELEMENT
```

---

# 8. Provider model

Axiom core phải cho phép:

```text
crypto_provider
```

Ví dụ:

```text
Axiom software provider
Windows native provider
Apple hardware provider
CPU accelerated provider
secure-element provider
```

Nhưng semantic contract của AXCRYPTO không phụ thuộc provider.

---

# 9. Dependency-free requirement

Axiom compiler/runtime không được yêu cầu:

```text
OpenSSL
libsodium
BoringSSL
third-party crypto library
```

để hoạt động ở baseline.

Common cryptographic primitives được chọn làm mandatory standard phải có implementation do Axiom sở hữu hoặc được thực hiện bởi platform backend mà Axiom tích hợp qua native ABI.

---

# 10. Hash abstraction

```text
crypto_hash
```

API concept:

```text
init()
update(data)
final()
reset()
```

Streaming:

```text
data chunk 1
data chunk 2
data chunk 3
      ↓
    hash
```

Không cần giữ toàn bộ input trong memory.

---

# 11. Hash output

Hash result phải là fixed-size byte representation:

```text
hash_result {
    algorithm
    bytes
}
```

Không trả string hex từ core API.

Hex/Base64 thuộc formatting layer.

---

# 12. Hash algorithm selection

AXCRYPTO phải phân biệt:

```text
FAST_NONCRYPTO_HASH
CRYPTOGRAPHIC_HASH
```

Không cho phép application nhầm một hash nhanh phục vụ table/cache với cryptographic digest.

---

# 13. Cryptographic hash baseline

Standard baseline có thể bao gồm các họ cryptographic hash hiện đại được Axiom chuẩn hóa.

Việc chọn algorithm cụ thể phải đi cùng:

- security review;
- test vectors;
- known attack status;
- platform support;
- implementation complexity.

Không coi một algorithm là an toàn chỉ vì nó phổ biến.

---

# 14. MAC

Core:

```text
crypto_mac
```

flow:

```text
key
 +
message
 ↓
MAC
 ↓
tag
```

API:

```text
init(key)
update(data)
final()
verify(tag)
```

---

# 15. MAC verification

Verification phải có constant-time comparison.

Không:

```text
memcmp()
```

nếu implementation có timing behavior không phù hợp.

Có:

```text
secure_compare(a, b)
```

---

# 16. KDF

```text
crypto_kdf
```

Mục đích:

```text
input key material
       ↓
     KDF
       ↓
derived key
```

Hỗ trợ domain separation:

```text
context
label
salt
info
```

---

# 17. Domain separation

Các derived keys cho các mục đích khác nhau phải có domain distinction:

```text
"AXIOM/NETWORK"
"AXIOM/STORAGE"
"AXIOM/SESSION"
```

Không dùng cùng một raw derived key cho nhiều protocol semantics nếu protocol không quy định.

---

# 18. Password KDF

Password-derived key phải dùng password-hardening KDF riêng.

Không:

```text
hash(password)
```

rồi dùng trực tiếp làm encryption key.

AXCRYPTO phải có explicit API:

```text
derive_password_key()
```

với:

- salt;
- cost;
- memory parameter;
- parallelism;
- version.

---

# 19. AEAD

Core authenticated encryption:

```text
crypto_aead
```

concept:

```text
key
nonce
plaintext
associated_data
        ↓
      AEAD
        ↓
ciphertext + authentication tag
```

Decryption chỉ trả plaintext sau khi authentication thành công.

---

# 20. Associated data

AAD:

```text
associated_data
```

được authenticate nhưng không encrypt.

Ví dụ:

```text
protocol header
message metadata
version
sequence number
```

---

# 21. AEAD failure

Nếu authentication thất bại:

```text
AUTHENTICATION_FAILED
```

Không trả plaintext một phần.

Không cho caller sử dụng unauthenticated plaintext.

---

# 22. Nonce model

```text
crypto_nonce
```

phải explicit.

AXCRYPTO không được âm thầm generate random nonce mỗi lần nếu protocol yêu cầu uniqueness/state tracking.

---

# 23. Nonce uniqueness

AEAD API phải document:

```text
nonce uniqueness requirement
```

đối với từng algorithm.

Application có thể sử dụng:

```text
counter
sequence
random
derived nonce
```

nhưng semantics phải algorithm-specific.

---

# 24. Nonce reuse

Provider có thể detect nonce reuse trong stateful contexts nếu khả thi.

Baseline không được giả định rằng mọi provider có thể phát hiện.

Protocol-level prevention thuộc caller/protocol.

---

# 25. Symmetric cipher

```text
crypto_cipher
```

hỗ trợ streaming/block semantics khi algorithm yêu cầu.

Tuy nhiên:

> Application code nên ưu tiên AEAD thay vì raw unauthenticated encryption.

Raw cipher vẫn tồn tại cho low-level/protocol implementations.

---

# 26. Public-key abstraction

```text
crypto_public_key
crypto_private_key
```

Private key phải được phân biệt khỏi public key ngay ở type system.

Không dùng:

```text
bytes
```

đơn thuần cho cả hai nếu API có thể tránh.

---

# 27. Key type

```text
crypto_key {
    algorithm
    usage
    material
    metadata
}
```

Usage constraints:

```text
SIGN
VERIFY
ENCRYPT
DECRYPT
DERIVE
WRAP
UNWRAP
```

---

# 28. Key usage restriction

Key có:

```text
allowed_operations
```

Một signing key không tự động được dùng để encryption.

AXCRYPTO enforce algorithm-level constraints; AXSECURITY enforce authorization policy.

---

# 29. Key lifetime

Key state:

```text
GENERATED
IMPORTED
ACTIVE
EXPIRED
REVOKED
DESTROYED
```

AXCRYPTO cung cấp primitive state support.

Identity/security systems sở hữu authoritative lifecycle policy.

---

# 30. Key material

Ba loại:

```text
RAW
DERIVED
HARDWARE_BOUND
```

Hardware-bound key có thể không cho export raw material.

---

# 31. Non-exportable key

```text
key.is_exportable = false
```

Provider phải reject:

```text
export_raw()
```

Không có API escape hatch.

---

# 32. Secure key memory

Private key material nên nằm trong secure memory:

```text
AXMEMORY
    ↓
secure allocation
    ↓
crypto_key
```

Hỗ trợ:

- locking;
- zeroization;
- guard pages;
- restricted access;
- memory pressure policy.

---

# 33. Zeroization

Khi key material không còn cần:

```text
secure_zero()
```

phải được sử dụng.

Compiler/runtime không được optimize away explicit secure zeroization.

Implementation có thể dùng:

- volatile stores;
- compiler barrier;
- platform secure wipe primitive.

---

# 34. Key copy semantics

Private key không nên vô tình copy bằng:

```text
memcpy()
```

Key object nên có explicit semantics:

```text
move
clone_explicit
reference
destroy
```

---

# 35. Constant-time requirement

Các operation nhạy timing phải có constant-time implementation khi algorithm yêu cầu.

Đặc biệt:

- MAC verification;
- signature primitive;
- private-key operations;
- secret comparison;
- secret-dependent arithmetic.

---

# 36. Constant-time annotation

Compiler có thể hỗ trợ:

```text
@constant_time
```

để đánh dấu code primitive.

Compiler diagnostics có thể cảnh báo:

```text
secret-dependent branch
secret-dependent memory access
```

trong vùng được annotate.

---

# 37. Không overpromise constant-time

Axiom không được tuyên bố:

> “Toàn bộ AXCRYPTO luôn constant-time trên mọi CPU.”

Timing behavior còn phụ thuộc:

- CPU;
- cache;
- branch predictor;
- hardware;
- provider.

Contract phải xác định chính xác operation nào có constant-time guarantee.

---

# 38. Digital signatures

```text
crypto_signature
```

flow:

```text
message
private_key
   ↓
sign
   ↓
signature
```

Verification:

```text
message
public_key
signature
   ↓
verify
```

---

# 39. Streaming signatures

Hash-then-sign architecture:

```text
large file
   ↓
streaming hash
   ↓
signature primitive
```

Không cần load toàn file.

Signature algorithm nào hỗ trợ streaming trực tiếp phải expose capability.

---

# 40. Signature encoding

Signature representation phải explicit:

```text
RAW
FIXED_WIDTH
STRUCTURED
```

Không để provider tự ý thay đổi wire representation.

---

# 41. Secure randomness

```text
crypto_random
```

phải cung cấp CSPRNG-backed random bytes.

API:

```text
random_bytes(n)
random_u32()
random_u64()
random_fill(buffer)
```

---

# 42. Random source hierarchy

```text
hardware RNG
     ↓
OS secure RNG
     ↓
Axiom CSPRNG
```

Không fallback xuống:

```text
time()
process_id
rand()
```

cho cryptographic randomness.

Nếu không có secure entropy:

```text
NO_ENTROPY
```

phải là error.

---

# 43. CSPRNG state

CSPRNG phải hỗ trợ:

```text
reseed
health state
entropy source
generation counter
```

Fork/process creation phải có reseed/rekey semantics để tránh child process sinh cùng random stream.

---

# 44. Deterministic random

Testing cần:

```text
crypto_test_rng(seed)
```

nhưng API này phải:

```text
TEST_ONLY
```

và không được dùng như secure RNG production path.

---

# 45. Key generation

```text
generate_key(spec)
```

Key generation sử dụng secure random.

Ví dụ:

```text
key_spec {
    algorithm
    size
    usage
    export_policy
}
```

---

# 46. Key import

Supported categories:

```text
raw key material
structured private key
structured public key
provider key reference
hardware key reference
```

Parser/representation thuộc AXCODEC; cryptographic validation thuộc AXCRYPTO.

---

# 47. Key export

Policies:

```text
EXPORT_RAW
EXPORT_STRUCTURED
EXPORT_PUBLIC_ONLY
NON_EXPORTABLE
```

Không cho export private material khi provider policy cấm.

---

# 48. Key wrapping

AXCRYPTO có thể hỗ trợ:

```text
wrap_key()
unwrap_key()
```

Nhưng key management policy vẫn thuộc AXSECURITY/identity infrastructure.

---

# 49. Hardware acceleration

AXCRYPTO có capability detection:

```text
crypto_capabilities {
    aes
    sha
    vector
    hardware_rng
    secure_element
}
```

Compiler/runtime có thể chọn:

```text
scalar
SIMD
CPU instruction
OS provider
hardware
```

---

# 50. Dispatch architecture

Fast path:

```text
compile-time known CPU
        ↓
direct specialized implementation
```

Portable binary:

```text
runtime CPU detection
        ↓
dispatch table
        ↓
optimized implementation
```

Không cần dynamic dispatch ở mỗi block.

---

# 51. CPU feature dispatch

Ví dụ:

```text
AES-NI
SHA extensions
NEON
SVE
AVX2
AVX-512
```

chỉ được sử dụng khi runtime/compiler xác nhận capability.

---

# 52. SIMD

Crypto implementation có thể dùng:

```text
Axiom SIMD/vector IR
```

để compiler generate native code.

Không yêu cầu external compiler.

---

# 53. Secure memory integration

```text
AXCRYPTO
   │
   ▼
AXMEMORY
   │
   ├── secure allocation
   ├── page lock
   ├── zeroization
   ├── guard
   └── memory protection
```

Nếu platform không hỗ trợ một feature:

```text
capability = unsupported
```

không giả lập security guarantee sai lệch.

---

# 54. Crash behavior

Không để private key material nằm trong crash diagnostic mặc định.

Crash subsystem phải:

```text
exclude secure regions
```

nếu AXMEMORY/AXPROCESS hỗ trợ.

---

# 55. Trace behavior

Crypto tracing mặc định **không ghi plaintext hoặc private keys**.

Trace chỉ có metadata:

```text
algorithm
operation
input_size
duration
provider
status
```

---

# 56. Error model

Core errors:

```text
INVALID_KEY
INVALID_KEY_SIZE
INVALID_NONCE
NONCE_REUSE
INVALID_SIGNATURE
AUTHENTICATION_FAILED
INVALID_PARAMETER
UNSUPPORTED_ALGORITHM
UNSUPPORTED_OPERATION
KEY_NOT_EXPORTABLE
KEY_EXPIRED
KEY_REVOKED
NO_ENTROPY
RNG_FAILURE
PROVIDER_FAILURE
SELF_TEST_FAILURE
INVALID_ENCODING
INVALID_TAG
BUFFER_TOO_SMALL
LIMIT_EXCEEDED
```

---

# 57. Self-test

Provider phải có known-answer tests:

```text
algorithm
input
expected_output
```

Self-test chạy:

- build/test;
- provider initialization;
- optionally startup based on security profile.

Nếu mandatory primitive fail self-test:

```text
CRYPTO_SELF_TEST_FAILURE
```

Provider không được báo healthy.

---

# 58. FIPS-like provider profiles

Axiom có thể hỗ trợ provider profiles:

```text
STANDARD
HARDENED
VALIDATED
```

`VALIDATED` chỉ là capability metadata khi provider thực sự đáp ứng validation tương ứng.

Không tự tuyên bố compliance.

---

# 59. Algorithm deprecation

Algorithm descriptor có:

```text
ACTIVE
DEPRECATED
DISABLED
```

Application policy quyết định có cho phép deprecated algorithm hay không.

---

# 60. Algorithm agility

Protocol không nên hard-code implementation pointer.

Thay vào đó:

```text
algorithm_id
```

để có thể chuyển:

```text
implementation A
→
implementation B
```

mà giữ protocol representation.

---

# 61. Versioning

Crypto algorithm version phải phân biệt:

```text
algorithm version
provider version
key format version
protocol version
```

Không gộp thành một version number.

---

# 62. Secure comparison

Native API:

```text
secure_equal(a, b)
```

Semantics:

- same-length comparison;
- no early exit based on first differing byte;
- documented timing guarantees.

---

# 63. Secret-dependent branching

Trong primitive implementation:

```text
if secret_bit ...
```

phải tránh nếu algorithm yêu cầu constant-time.

Compiler static analysis có thể phát hiện một số pattern nhưng không thay thế cryptographic review.

---

# 64. Side-channel boundary

AXCRYPTO phải xem xét:

- timing;
- cache;
- branch;
- memory access;
- power/EM trên hardware provider.

Không tuyên bố bảo vệ hoàn toàn khỏi side-channel.

---

# 65. Fault handling

Crypto hardware fault:

```text
HARDWARE_FAILURE
```

không được tự động fallback sang insecure behavior.

Fallback chỉ xảy ra nếu policy cho phép.

---

# 66. Provider fallback

Ví dụ:

```text
hardware AES
   ↓ failure
software AES
```

chỉ được phép nếu:

```text
fallback_policy = ALLOW
```

và security semantics không bị phá vỡ.

---

# 67. Session keys

AXCRYPTO có primitive để tạo derived/session key.

Protocol lifecycle:

```text
master secret
     ↓
KDF
     ↓
session key
     ↓
AEAD
```

AXCRYPTO không sở hữu session state của network protocol.

---

# 68. Key separation

Derived keys phải hỗ trợ domain:

```text
encryption_key
authentication_key
export_key
storage_key
```

không nên dùng một key cho nhiều cryptographic purpose nếu protocol không yêu cầu.

---

# 69. Associated metadata

Crypto operation có thể nhận:

```text
crypto_context {
    algorithm
    purpose
    provider
    security_domain
}
```

`purpose` hỗ trợ diagnostics/policy nhưng không thay thế AXSECURITY authorization.

---

# 70. Memory ownership

Crypto APIs phải rõ:

```text
borrowed input
owned output
borrowed key
owned key
```

Không copy secret buffer ngoài ý muốn.

---

# 71. In-place operations

Có thể hỗ trợ:

```text
encrypt_in_place(buffer)
decrypt_in_place(buffer)
```

nhưng chỉ khi algorithm/provider cho phép.

Overlap rules phải explicit.

---

# 72. Large-data crypto

Streaming:

```text
file
 ↓
hash.update()
 ↓
hash.update()
 ↓
...
 ↓
final()
```

hoặc:

```text
stream
 ↓
AEAD chunks
```

không cần load toàn bộ data.

---

# 73. Chunked AEAD

Nếu protocol sử dụng chunk encryption:

```text
chunk_0
chunk_1
chunk_2
```

mỗi chunk phải có nonce/sequence semantics rõ.

AXCRYPTO cung cấp primitive; protocol định nghĩa:

```text
nonce = derive(base_nonce, sequence)
```

nếu cần.

---

# 74. Replay resistance

AXCRYPTO không tự giải quyết replay.

Replay prevention thuộc protocol/security layer:

```text
sequence number
timestamp
nonce tracking
session state
```

AXCRYPTO chỉ cung cấp primitive cần thiết.

---

# 75. Random nonce tracking

Stateful AEAD context có thể expose:

```text
nonce_counter
nonce_state
```

nhưng không tự đảm bảo protocol-level uniqueness nếu application tạo nonce ngoài context.

---

# 76. Cryptographic context

```text
crypto_context {
    algorithm
    provider
    key
    state
    limits
}
```

Context không nên chứa authority capability trực tiếp; security authorization nằm ở AXSECURITY.

---

# 77. Context reuse

Hash contexts có thể:

```text
reset()
reuse()
```

để giảm allocation.

Key contexts phải có explicit reset/destroy semantics.

---

# 78. Thread safety

Mặc định:

```text
crypto_context = not thread-safe
```

nếu state mutable.

Stateless algorithm descriptors:

```text
thread-safe
```

Provider phải khai báo concurrency capability.

---

# 79. Task safety

Crypto context không tự động gắn với OS thread.

Có thể được dùng trong AXTASK nếu ownership contract cho phép.

---

# 80. Async crypto

CPU-bound crypto không được biến mọi operation thành fake asynchronous API.

Nếu operation lớn:

```text
AXTASK
   ↓
AXCOMPUTE
   ↓
crypto worker
```

GPU/device crypto có thể tích hợp qua async backend.

---

# 81. GPU crypto

AXCRYPTO có thể expose provider capability:

```text
GPU_ACCELERATED
```

nhưng không mặc định đưa cryptographic secret vào GPU memory.

Việc đó phải explicit và có security policy.

---

# 82. Secure element

Hardware key provider:

```text
SECURE_ELEMENT
```

có thể expose:

```text
sign()
decrypt()
derive()
```

mà không bao giờ export private key.

---

# 83. Certificate boundary

Certificate representation có thể được parse bằng:

```text
AXCODEC
```

Cryptographic signature verification:

```text
AXCRYPTO
```

Certificate trust decision:

```text
AXSECURITY
```

Ba tầng không được nhập thành một.

---

# 84. Trust chain

```text
certificate bytes
      ↓
AXCODEC
      ↓
certificate structure
      ↓
AXCRYPTO
      ↓
signature verification
      ↓
AXSECURITY
      ↓
trust decision
```

---

# 85. TLS boundary

TLS-like protocol không thuộc AXCRYPTO.

Nó sử dụng:

```text
AXNETWORK
AXCRYPTO
AXSECURITY
AXCODEC
AXSTREAM
```

---

# 86. Serialization boundary

Key representation:

```text
crypto_key
```

có thể serialize qua:

```text
AXCODEC
```

nhưng AXCODEC không được tự động serialize secret material nếu policy không cho phép.

---

# 87. Secret serialization policy

```text
key.export()
```

phải kiểm tra:

```text
exportable
authorization
format
provider policy
```

Không expose raw secret qua generic `encode()` mặc định.

---

# 88. Build-time crypto metadata

Compiler artifact có thể chứa:

```text
supported_crypto_algorithms
required_cpu_features
provider requirements
```

nhưng không chứa private keys.

---

# 89. AI integration

AI tooling có thể phân tích:

- algorithm usage;
- deprecated algorithms;
- key lifetime metadata;
- performance;
- provider selection;
- missing authentication;
- accidental raw cipher usage.

AI không được:

- extract private keys;
- bypass key policy;
- disable authentication;
- downgrade security policy;
- export non-exportable material.

---

# 90. Compiler integration

Compiler intrinsics:

```text
crypto_hash()
crypto_mac()
crypto_aead()
secure_compare()
secure_zero()
crypto_random()
```

có thể được lowered trực tiếp:

```text
Axiom IR
   ↓
crypto intrinsic
   ↓
CPU instruction / provider ABI
```

---

# 91. Compile-time specialization

Ví dụ:

```text
hash<SHA256>(data)
```

có thể specialize algorithm.

Runtime generic:

```text
hash(algorithm_id, data)
```

sử dụng provider dispatch.

---

# 92. No unnecessary allocation

Hot path không được yêu cầu:

```text
heap allocation
virtual dispatch
temporary string
```

mỗi crypto operation.

---

# 93. Small-message fast path

Ví dụ:

```text
secure_compare()
hash_small()
mac_small()
```

có thể dùng stack/local state.

---

# 94. Batch operations

AXCRYPTO có thể hỗ trợ:

```text
hash_batch()
verify_batch()
encrypt_batch()
```

để tận dụng SIMD/hardware acceleration.

---

# 95. Parallel hashing

Large input có thể dùng tree/parallel hash nếu algorithm hỗ trợ.

Không thay đổi semantics của standard hash.

---

# 96. Deterministic test vectors

Mỗi mandatory implementation phải có test vectors:

```text
algorithm
key
nonce
input
AAD
expected ciphertext
expected tag
```

hoặc tương ứng với operation.

---

# 97. Cross-platform conformance

Mọi provider phải pass:

```text
AXCRYPTO_CONFORMANCE_5
```

bao gồm:

- output;
- error;
- key validation;
- nonce validation;
- edge cases;
- test vectors;
- state transitions.

---

# 98. Native API

Core API baseline:

```text
crypto_random()
crypto_random_fill()

hash_create()
hash_update()
hash_final()
hash_reset()

mac_create()
mac_update()
mac_final()
mac_verify()

kdf_derive()
password_kdf()

cipher_create()
cipher_update()
cipher_final()

aead_encrypt()
aead_decrypt()

signature_sign()
signature_verify()

generate_key()
import_key()
export_key()
destroy_key()

wrap_key()
unwrap_key()

secure_compare()
secure_zero()

list_algorithms()
get_algorithm_info()
get_provider_info()

get_crypto_capabilities()

run_self_tests()

start_crypto_trace()
stop_crypto_trace()
```

---

# 99. Canonical flow — Hash

```text
input stream
     │
     ▼
hash_create()
     │
     ▼
update(chunk)
     │
     ▼
update(chunk)
     │
     ▼
final()
     │
     ▼
digest
```

---

# 100. Canonical flow — AEAD

```text
key
nonce
AAD
plaintext
  │
  ▼
AEAD encrypt
  │
  ▼
ciphertext + tag
```

Decrypt:

```text
ciphertext + tag
       │
       ▼
authenticate
       │
   ┌───┴────┐
   ▼        ▼
 failure   success
   │        │
 error   plaintext
```

---

# 101. Canonical flow — Secure key

```text
secure RNG
    │
    ▼
generate_key()
    │
    ▼
secure memory
    │
    ▼
crypto_key
    │
    ├── use
    │
    └── destroy
          │
          ▼
      secure_zero
```

---

# 102. Canonical flow — Hardware provider

```text
crypto operation
       │
       ▼
capability lookup
       │
       ▼
hardware provider
       │
   ┌───┴────┐
   ▼        ▼
success   failure
            │
            ▼
       fallback policy
```

---

# 103. Canonical flow — Certificate verification

```text
certificate bytes
       │
       ▼
     AXCODEC
       │
       ▼
certificate structure
       │
       ▼
    AXCRYPTO
       │
       ▼
signature verification
       │
       ▼
   AXSECURITY
       │
       ▼
 trust decision
```

---

# 104. Formal invariants

### CRYPTO-INV-01
Cryptographic primitive identity phải stable.

### CRYPTO-INV-02
Algorithm identity không phụ thuộc memory address.

### CRYPTO-INV-03
Provider không được thay đổi semantic result của cùng algorithm.

### CRYPTO-INV-04
Mandatory algorithms phải có conformance tests.

### CRYPTO-INV-05
Private key type phải khác public key type ở API semantics.

### CRYPTO-INV-06
Non-exportable key không được export raw material.

### CRYPTO-INV-07
Key usage restrictions phải được enforce.

### CRYPTO-INV-08
Key destruction phải có secure-zeroization semantics.

### CRYPTO-INV-09
Crypto APIs không được fallback sang insecure randomness.

### CRYPTO-INV-10
Secure random failure phải được báo explicit.

### CRYPTO-INV-11
Test RNG không được là production CSPRNG.

### CRYPTO-INV-12
MAC verification phải dùng secure comparison.

### CRYPTO-INV-13
AEAD authentication failure không được trả authenticated plaintext.

### CRYPTO-INV-14
Nonce semantics phải explicit theo algorithm.

### CRYPTO-INV-15
Nonce reuse requirement phải được documentation/API capability thể hiện.

### CRYPTO-INV-16
KDF phải hỗ trợ context/domain separation.

### CRYPTO-INV-17
Password KDF không được đồng nhất với generic hash.

### CRYPTO-INV-18
Cryptographic hash phải phân biệt với non-cryptographic hash.

### CRYPTO-INV-19
Secret-dependent operations phải tuân constant-time contract khi applicable.

### CRYPTO-INV-20
AXCRYPTO không tự tạo authorization authority.

### CRYPTO-INV-21
AXSECURITY sở hữu authorization policy.

### CRYPTO-INV-22
AXIDENTITY sở hữu identity lifecycle.

### CRYPTO-INV-23
AXCODEC sở hữu representation, không sở hữu cryptographic authority.

### CRYPTO-INV-24
Crypto trace không capture secrets mặc định.

### CRYPTO-INV-25
Crash diagnostics không được expose private key material mặc định.

### CRYPTO-INV-26
Provider capability phải được khai báo chính xác.

### CRYPTO-INV-27
Unsupported hardware capability không được giả lập thành hardware security guarantee.

### CRYPTO-INV-28
Provider fallback phải tuân explicit policy.

### CRYPTO-INV-29
Algorithm deprecation phải có machine-readable state.

### CRYPTO-INV-30
Algorithm agility không được phá key semantics.

### CRYPTO-INV-31
Large-data crypto phải hỗ trợ streaming khi algorithm cho phép.

### CRYPTO-INV-32
Crypto context mutable không mặc định thread-safe.

### CRYPTO-INV-33
Crypto hot path không bắt buộc heap allocation.

### CRYPTO-INV-34
Crypto operation không được âm thầm downgrade algorithm.

### CRYPTO-INV-35
Key serialization phải respect export policy.

### CRYPTO-INV-36
Certificate parsing và trust decision phải tách khỏi primitive crypto.

### CRYPTO-INV-37
TLS/network protocol semantics không thuộc AXCRYPTO.

### CRYPTO-INV-38
AI tooling không được bypass security/key policy.

### CRYPTO-INV-39
Deterministic crypto testing không được nhầm với production randomness.

### CRYPTO-INV-40
`AXCRYPTO 5.0` phải giữ semantic contract độc lập với OS crypto provider và hardware backend.

---

# 105. Definition of Done

`AXCRYPTO 5.0` hoàn tất khi có:

- stable algorithm identifiers;
- provider abstraction;
- cryptographic hash;
- streaming hash;
- MAC;
- KDF;
- password KDF;
- symmetric cipher abstraction;
- AEAD;
- public/private key model;
- signature;
- signature verification;
- key generation;
- key import/export;
- non-exportable keys;
- key wrapping;
- secure randomness;
- CSPRNG;
- deterministic test RNG;
- nonce abstraction;
- secure comparison;
- secure zeroization;
- constant-time primitives;
- CPU feature dispatch;
- SIMD acceleration;
- hardware crypto provider;
- secure-element provider interface;
- secure memory integration;
- crash-safe secret handling;
- algorithm deprecation;
- algorithm agility;
- self-tests;
- test-vector framework;
- conformance suite;
- streaming large-data crypto;
- batch crypto;
- trace metadata;
- compiler intrinsics;
- crypto IR;
- native provider ABI;
- cross-platform backend contract;
- AI diagnostic boundary;
- 40 invariants.

**AXCRYPTO 5.0 → FROZEN.**

---

# Kiến trúc Axiom hiện tại

Chuỗi security/data representation đã đạt hình dạng:

```text
                    ┌──────────────┐
                    │ AXAPPLICATION│
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
         AXSECURITY                 AXIDENTITY
              │
              ▼
          AXCRYPTO
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
     HASH    AEAD     SIGN
       │      │        │
       └──────┼────────┘
              ▼
           AXCODEC
              │
              ▼
           AXSTREAM
              │
       ┌──────┼───────┐
       ▼      ▼       ▼
   AXSTORAGE AXNETWORK AXIPC
```

Điểm thiết kế quan trọng nhất của chuỗi này là **không biến `AXSECURITY` thành một module khổng lồ**. `AXSECURITY` quyết định *quyền và policy*, `AXCRYPTO` thực hiện *cryptographic primitive*, `AXCODEC` xử lý *representation*, còn `AXSTREAM` xử lý *data flow*.

---

# BOOTSTRAP-753 — AXCERT

**Native Certificate, Credential, Trust Chain, Attestation & Trust-Object Runtime 5.0**

Task kế tiếp sẽ xây tầng nằm **trên AXCRYPTO nhưng dưới AXSECURITY**, xử lý:

```text
certificate
credential
trust anchor
certificate chain
key binding
attestation
revocation metadata
trust evidence
```

và đặc biệt giữ nguyên boundary:

```text
AXCRYPTO  → "chữ ký này có hợp lệ không?"
AXCERT    → "credential/certificate này nói gì và chain của nó thế nào?"
AXSECURITY → "có tin và cấp quyền dựa trên evidence đó hay không?"
```

**BOOTSTRAP-752 hoàn tất → chuyển sang BOOTSTRAP-753.**