# BOOTSTRAP-456 — CRYPTOGRAPHY, HASHING, RANDOMNESS, KEY MANAGEMENT & SECURE-COMPUTING PRIMITIVES

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 456 là định nghĩa nền tảng cryptographic/security primitives cho Axiom mà không biến chúng thành một phần bắt buộc của language core hoặc native runtime.

Kiến trúc:

```text
Axiom Core
    ↓
Integer / SIMD / Memory primitives
    ↓
Crypto primitives
    ↓
Hash / MAC / KDF / AEAD / Signature
    ↓
TLS / Authentication / Secure Storage
    ↓
Application Security
```

Nguyên tắc quan trọng:

> Axiom cung cấp **nền tảng để implement cryptography native và hiệu năng cao**, nhưng không tự tuyên bố rằng mọi primitive cryptographic đều an toàn chỉ vì chúng được viết bằng Axiom.

---

## 456.1 — Crypto layering

Crypto được chia thành:

```text
crypto-core
crypto-hash
crypto-mac
crypto-kdf
crypto-cipher
crypto-aead
crypto-signature
crypto-key
crypto-rng
crypto-secure-memory
crypto-protocol
```

---

## 456.2 — No mandatory crypto runtime

Application không sử dụng cryptography không được link crypto runtime.

---

## 456.3 — No mandatory global crypto provider

Không có một global crypto provider bắt buộc trong language runtime.

---

## 456.4 — Algorithm abstraction

Algorithms được biểu diễn bằng concrete types/traits, không bằng string tên thuật toán ở low-level API.

---

## 456.5 — Algorithm agility

Protocol-level code có thể lựa chọn algorithm, nhưng security-sensitive defaults phải tránh việc developer vô tình chọn primitive yếu.

---

# 456.6 — Hashing

Core crypto library cung cấp cryptographic hash abstraction.

Conceptual:

```text
trait Hash {
    type Output
    fn update(...)
    fn finalize(...) -> Output
}
```

---

## 456.7 — Streaming hash

Hash phải hỗ trợ incremental input.

---

## 456.8 — One-shot hash

Convenience API:

```text
hash(data) -> Digest
```

---

## 456.9 — Digest type

Digest phải là fixed-size value type khi algorithm có fixed output.

---

## 456.10 — Digest equality

Digest comparison trong security-sensitive context có thể yêu cầu constant-time comparison.

---

## 456.11 — SHA-family

Standard ecosystem có thể cung cấp SHA-2/SHA-3 family.

---

## 456.12 — BLAKE-family

Các modern hash families có thể được cung cấp như packages.

---

## 456.13 — Non-cryptographic hash

Hash table không nhất thiết dùng cryptographic hash.

Standard library có separate fast hash abstraction.

---

## 456.14 — Hash distinction

API names/types phải giúp phân biệt:

```text
FastHash
CryptoHash
Checksum
```

---

## 456.15 — Checksum

Checksum dùng phát hiện lỗi truyền/storage, không được coi là authentication.

---

## 456.16 — Hash collision semantics

Hash collision phải luôn được coi là khả năng tồn tại.

---

## 456.17 — Hash output encoding

Hex/Base64 encoding là separate utility.

---

## 456.18 — Domain separation

Crypto protocols có thể dùng domain-separated hashes.

---

## 456.19 — Hash context reuse

Hash state reuse phải reset explicit.

---

## 456.20 — Hash finalization

Sau `finalize`, state không được tiếp tục sử dụng trừ khi API explicitly hỗ trợ reset.

---

# 456.21 — MAC

Message Authentication Code abstraction:

```text
Mac
```

---

## 456.22 — HMAC

HMAC là standard package primitive.

---

## 456.23 — MAC verification

Verification phải cung cấp constant-time comparison semantics.

---

## 456.24 — MAC key

MAC key là sensitive secret type.

---

## 456.25 — MAC output

MAC tag phải fixed-size typed value khi algorithm cho phép.

---

## 456.26 — MAC streaming

Large messages phải hỗ trợ streaming MAC.

---

## 456.27 — MAC failure

Invalid tag trả về typed failure, không panic.

---

## 456.28 — MAC vs hash

API không được cho phép developer nhầm hash với authentication.

---

## 456.29 — Keyed hash

Keyed hash phải có explicit key type/API.

---

## 456.30 — MAC truncation

Tag truncation phải explicit và algorithm-specific.

---

# 456.31 — KDF

Key Derivation Function abstraction:

```text
Kdf
```

---

## 456.32 — HKDF

HKDF là standard package primitive.

---

## 456.33 — Password KDF

Password-derived keys dùng dedicated password KDF.

---

## 456.34 — Password hashing

Password storage không được khuyến khích dùng raw SHA/BLAKE.

---

## 456.35 — Password KDF parameters

Cost parameters phải explicit.

---

## 456.36 — Salt

Password KDF salt phải là independent random value.

---

## 456.37 — Salt storage

Salt không phải secret và có thể lưu cùng password verifier.

---

## 456.38 — Pepper

Optional secret pepper thuộc application/key-management layer.

---

## 456.39 — KDF context

KDF APIs phải support context/info để domain-separate derived keys.

---

## 456.40 — Key separation

Các protocol keys khác mục đích phải được derive separately.

---

# 456.41 — Symmetric encryption

Symmetric cipher abstraction:

```text
Cipher
```

---

## 456.42 — Block cipher

Block cipher primitive có thể được cung cấp.

---

## 456.43 — AES

AES implementation có thể exploit CPU hardware acceleration.

---

## 456.44 — ChaCha family

ChaCha-based implementations có thể dùng software-friendly constant-time operations.

---

## 456.45 — No insecure mode by default

Bare ECB-like modes không được trở thành high-level encryption default.

---

# 456.46 — AEAD

Authenticated Encryption with Associated Data là primary high-level symmetric encryption abstraction.

Conceptual:

```text
seal(key, nonce, plaintext, aad) -> ciphertext
open(key, nonce, ciphertext, aad) -> plaintext
```

---

## 456.47 — AEAD authentication

Authentication tag được tích hợp vào AEAD operation.

---

## 456.48 — AAD

Additional authenticated data không được encrypted nhưng được authenticated.

---

## 456.49 — Nonce

Nonce type phải phụ thuộc algorithm.

---

## 456.50 — Nonce uniqueness

API documentation phải làm rõ nonce reuse có thể phá security guarantee.

---

## 456.51 — Nonce generation

Library có thể cung cấp safe nonce generation helpers.

---

## 456.52 — Random nonce

Random nonce chỉ phù hợp khi algorithm/message volume và nonce size cho phép.

---

## 456.53 — Counter nonce

Deterministic counter-based nonce có thể được dùng với persistent state.

---

## 456.54 — Nonce exhaustion

Library/protocol phải detect hoặc define behavior khi nonce space exhausted.

---

## 456.55 — Tag verification

AEAD decryption phải verify authentication trước khi expose plaintext.

---

## 456.56 — Invalid ciphertext

Invalid ciphertext trả về error.

---

## 456.57 — No unauthenticated plaintext

High-level AEAD API không trả plaintext nếu authentication thất bại.

---

## 456.58 — Streaming AEAD

Nếu algorithm/protocol hỗ trợ streaming authenticated encryption, API phải define chunk boundaries và finalization.

---

## 456.59 — Chunk authentication

Streaming protocol phải bảo đảm attacker không thể reorder/truncate chunks mà không detection.

---

## 456.60 — Associated-data ordering

AAD phải được incorporated theo deterministic protocol order.

---

# 456.61 — Public-key cryptography

Public-key APIs được chia:

```text
KeyExchange
Signature
PublicKeyEncryption
```

Không gom tất cả thành một `CryptoKey` generic mơ hồ.

---

## 456.62 — Key exchange

Key exchange dùng để establish shared secret.

---

## 456.63 — Diffie-Hellman family

Modern DH mechanisms có thể được cung cấp.

---

## 456.64 — Elliptic-curve key exchange

Curve-specific types phải distinguish nhau.

---

## 456.65 — X25519-style APIs

Curve-specific modern key exchange có thể được package cung cấp.

---

## 456.66 — Post-quantum boundary

Post-quantum algorithms thuộc crypto provider/package layer.

Không hard-code toàn bộ PQC ecosystem vào compiler.

---

## 456.67 — Signature abstraction

```text
Signer
Verifier
Signature
```

---

## 456.68 — Signature verification

Verification phải trả:

```text
Result<unit, SignatureError>
```

hoặc equivalent.

---

## 456.69 — No boolean ambiguity

Security-sensitive verification API nên tránh một `bool` không giải thích được error state.

---

## 456.70 — Signature encoding

DER/raw/fixed-width encoding phải là explicit algorithm-specific representation.

---

# 456.71 — Key types

Key material phải có type distinction:

```text
PublicKey
PrivateKey
SecretKey
DerivedKey
SigningKey
VerificationKey
```

---

## 456.72 — No universal key type

Không sử dụng một byte array generic làm security-sensitive key API mặc định.

---

## 456.73 — Key validity

Constructing key từ bytes phải validate algorithm-specific representation.

---

## 456.74 — Invalid key

Invalid key material trả typed error.

---

## 456.75 — Public key export

Public keys có thể serialize.

---

## 456.76 — Private key export

Private-key export phải là explicit operation.

---

## 456.77 — Secret-key export

Secret extraction từ secure key abstraction phải explicit.

---

## 456.78 — Key ownership

Key object ownership deterministic.

---

## 456.79 — Key destruction

Secret key memory nên được zeroized khi lifetime kết thúc nếu platform/compiler semantics cho phép.

---

## 456.80 — Compiler optimization and zeroization

Compiler phải tránh optimize-away required secret clearing trong APIs có secure-memory contract.

---

# 456.81 — Secure random

Crypto cần CSPRNG abstraction:

```text
SecureRandom
```

---

## 456.82 — OS entropy

Native default phải lấy entropy từ OS/platform secure source.

---

## 456.83 — No predictable default

Ordinary PRNG không được dùng làm default source cho cryptographic secrets.

---

## 456.84 — PRNG distinction

Axiom phân biệt:

```text
Random
SecureRandom
```

---

## 456.85 — Deterministic RNG

Deterministic RNG được hỗ trợ cho testing/simulation khi explicitly selected.

---

## 456.86 — Test RNG

Test code có thể inject deterministic RNG.

---

## 456.87 — RNG failure

Nếu secure entropy unavailable, API phải return failure hoặc explicit platform-specific behavior.

Không âm thầm fallback sang predictable randomness.

---

## 456.88 — RNG seeding

Application không tự cần seed OS CSPRNG.

---

## 456.89 — Random bytes

Primitive:

```text
fill_secure(bytes)
```

---

## 456.90 — Random integer

Bounded random integer API phải avoid modulo bias.

---

# 456.91 — Constant-time operations

Security-sensitive code có thể require:

```text
@constant_time
```

hoặc equivalent contract.

---

## 456.92 — Constant-time scope

Contract áp dụng cho function/block phù hợp, không phải toàn chương trình.

---

## 456.93 — Constant-time comparison

Crypto library cung cấp:

```text
constant_time_eq(a, b)
```

---

## 456.94 — Constant-time select

Có thể cung cấp branchless/select primitive.

---

## 456.95 — Constant-time arithmetic

Crypto implementation có thể dùng explicit fixed-width arithmetic.

---

## 456.96 — Branching

Compiler không được tự động assume source-level branchless code luôn constant-time.

---

## 456.97 — Optimization awareness

Optimizer phải preserve declared semantic/security constraints.

---

## 456.98 — CPU feature variation

Hardware acceleration phải maintain required security semantics.

---

## 456.99 — Timing leakage

Axiom không thể guarantee absence of all side channels.

---

## 456.100 — Side-channel declaration

Crypto API documentation phải distinguish:

```text
functional correctness
constant-time intent
hardware side-channel resistance
```

---

# 456.101 — Secure memory

Axiom có secure-memory abstraction:

```text
Secret<T>
SecureBuffer
```

---

## 456.102 — Secret storage

Secrets không nên mặc định sống trong immutable global/static memory.

---

## 456.103 — Secret copy

Secret copies nên được minimize.

---

## 456.104 — Move secrets

Move semantics 423 cho phép transfer ownership mà không cần duplicate.

---

## 456.105 — Secret clone

Clone secret phải explicit.

---

## 456.106 — Zeroization

Secure buffer có deterministic cleanup.

---

## 456.107 — Memory locking

OS memory locking (`mlock`-like capability) là optional platform feature.

---

## 456.108 — Locked memory failure

Failure to lock memory không được silently claim protection.

---

## 456.109 — Swap

Axiom không thể guarantee secret memory never reaches swap trên mọi OS.

---

## 456.110 — Core dump

Applications xử lý secrets phải có platform-specific core-dump policy.

---

# 456.111 — Key storage

Key storage abstraction:

```text
KeyStore
```

---

## 456.112 — OS key stores

Native integrations có thể use:

```text
Windows credential/key facilities
Apple key facilities
Linux desktop/system facilities
Android keystore
```

---

## 456.113 — Hardware-backed keys

Hardware-backed key storage là optional capability.

---

## 456.114 — TPM/HSM

TPM/HSM integration thuộc platform/crypto provider.

---

## 456.115 — Non-exportable keys

Key store phải support keys mà private material không bao giờ được export.

---

## 456.116 — Key handles

Non-exportable key được đại diện bằng opaque handle.

---

## 456.117 — Key operations

Handle có thể expose:

```text
sign
decrypt
derive
```

mà không expose raw private bytes.

---

## 456.118 — Key lifecycle

Key states có thể gồm:

```text
generated
active
disabled
destroyed
```

---

## 456.119 — Key rotation

Rotation là explicit application/protocol operation.

---

## 456.120 — Key version

Persistent key stores phải support key versioning khi cần.

---

# 456.121 — Certificate foundation

Certificate parsing/validation là package layer.

---

## 456.122 — X.509

X.509 parser phải xử lý untrusted input safely.

---

## 456.123 — Certificate chain

Chain validation là policy-aware operation.

---

## 456.124 — Hostname validation

Hostname verification phải được thực hiện riêng biệt nhưng tích hợp trong secure TLS client defaults.

---

## 456.125 — Trust anchors

Trust anchors phải đến từ explicit trust store.

---

## 456.126 — Certificate expiry

Validity periods phải được kiểm tra theo configured time source.

---

## 456.127 — Revocation

CRL/OCSP/revocation checking là provider/policy layer.

---

## 456.128 — Certificate parsing limits

Parser phải có resource limits.

---

## 456.129 — Certificate errors

Errors phải preserve enough context nhưng không leak secrets.

---

## 456.130 — Certificate serialization

Encoding phải preserve canonical wire format where required.

---

# 456.131 — Secure protocol composition

Crypto primitives không nên được ghép tùy tiện trong application code khi có standardized construction.

---

## 456.132 — Safe high-level construction

Library nên expose high-level constructions:

```text
SecureChannel
AuthenticatedMessage
EncryptedStore
SignedToken
```

khi protocol semantics đã được xác định.

---

## 456.133 — Primitive escape hatch

Advanced developers vẫn có low-level primitives.

---

## 456.134 — Explicit unsafe crypto

Unsafe operations như raw assembly, hardware registers, invalid memory access vẫn obey 445.

---

## 456.135 — No magic security

Axiom type safety không đồng nghĩa cryptographic security.

---

## 456.136 — Protocol misuse

Library phải cố gắng make insecure configurations difficult.

---

## 456.137 — Deprecated algorithms

Weak/deprecated algorithms có thể bị đánh dấu compatibility-only.

---

## 456.138 — Compatibility mode

Legacy crypto phải explicit opt-in.

---

## 456.139 — Security policy

Application/build profile có thể forbid weak algorithms.

---

## 456.140 — Security lint

Compiler/tooling có thể cảnh báo misuse patterns.

---

# 456.141 — Password APIs

Password API nhận user password dưới dạng secret-aware type.

---

## 456.142 — Password comparison

Password verification phải constant-time ở relevant stages.

---

## 456.143 — Password storage

Chỉ lưu password verifier/KDF result, không raw password.

---

## 456.144 — Password memory

Password buffers nên được cleared khi lifetime kết thúc.

---

## 456.145 — Password normalization

Normalization phải được protocol/application quy định; không tự động thay đổi user password semantics.

---

## 456.146 — Password policy

Complexity requirements thuộc application policy.

---

## 456.147 — Rate limiting

Authentication rate limiting thuộc application/network layer.

---

## 456.148 — MFA

MFA không thuộc crypto core.

---

## 456.149 — Token signing

JWT/other token formats thuộc protocol package.

---

## 456.150 — Token verification

Token verification phải validate algorithm, issuer/audience/time claims theo explicit policy.

---

# 456.151 — Cryptographic encoding

Base64:

```text
standard
url_safe
```

có thể là utility.

---

## 456.152 — Hex

Hex encoding/decoding là utility.

---

## 456.153 — PEM

PEM parser/encoder là certificate/key package.

---

## 456.154 — DER

DER là binary encoding, không phải generic serialization.

---

## 456.155 — Canonical encoding

Signature schemes phải sử dụng canonical encoding khi protocol yêu cầu.

---

## 456.156 — Malformed encoding

Malformed encoded data trả error.

---

## 456.157 — Length limits

Decoders phải support explicit maximum lengths.

---

## 456.158 — Recursion limits

Nested ASN.1/structured formats phải có recursion limits.

---

## 456.159 — Integer limits

Big integer decoding phải có resource limits.

---

## 456.160 — Big integers

`i128/u128` hoặc arbitrary precision crypto integers thuộc appropriate library layer, không yêu cầu language core phải có arbitrary precision.

---

# 456.161 — Big integer representation

Crypto big integers phải có explicit ownership and allocation behavior.

---

## 456.162 — Constant-time big integers

Crypto-specific big integer implementation có thể cần constant-time operations.

---

## 456.163 — Generic BigInt

General-purpose `BigInt` không tự động được coi là constant-time.

---

## 456.164 — Allocation control

Crypto implementation có thể use preallocated buffers.

---

## 456.165 — Stack crypto

Small fixed-size cryptographic operations có thể chạy hoàn toàn trên stack.

---

## 456.166 — Heap crypto

Large keys/data có thể allocate explicitly.

---

## 456.167 — `@no_alloc`

Crypto routines có thể expose allocation-free variants.

---

## 456.168 — `@no_block`

Pure crypto functions không nên block.

---

## 456.169 — `@no_panic`

Parsing/verification APIs có thể expose no-panic contracts.

---

## 456.170 — Error propagation

Crypto failures dùng `Result`, không exception/panic mặc định.

---

# 456.171 — Hardware acceleration

Compiler/backend phải cho phép:

```text
AES instructions
SHA instructions
carryless multiplication
vector instructions
```

khi target hỗ trợ.

---

## 456.172 — CPU feature detection

Runtime có thể query CPU features.

---

## 456.173 — Static CPU targeting

Build có thể target known CPU features.

---

## 456.174 — Dispatch

Crypto library có thể chọn implementation:

```text
generic
SIMD
hardware accelerated
```

---

## 456.175 — Function multiversioning

Compiler có thể support target-feature-specific function variants.

---

## 456.176 — Runtime dispatch

Runtime dispatch phải không thay đổi cryptographic semantics.

---

## 456.177 — Deterministic output

Cryptographic computations deterministic given same inputs, except RNG-dependent operations.

---

## 456.178 — Secure RNG boundary

RNG calls là explicit source of nondeterminism.

---

## 456.179 — Benchmarking crypto

Benchmark phải distinguish:

```text
software
hardware accelerated
single-shot
streaming
key setup
steady state
```

---

## 456.180 — Benchmark security

Benchmarking tools không được vô tình log secret test vectors.

---

# 456.181 — FFI crypto

Crypto libraries có thể wrap external/native implementations through FFI 451.

---

## 456.182 — Native provider

Provider ABI phải be explicit.

---

## 456.183 — Provider ownership

Buffers passed to provider phải define ownership/lifetime.

---

## 456.184 — Provider errors

Foreign errors map sang typed Axiom errors.

---

## 456.185 — Provider secret handling

Foreign provider memory semantics phải được documented.

---

## 456.186 — Provider verification

Axiom can verify ABI/layout but cannot automatically prove foreign crypto correctness.

---

## 456.187 — Pure Axiom implementation

Axiom must be capable of implementing cryptographic algorithms directly in Axiom.

---

## 456.188 — No compiler crypto dependency

Compiler does not require OpenSSL/libsodium/etc. to compile ordinary Axiom programs.

---

## 456.189 — Optional system crypto

System crypto providers can be selected by package configuration.

---

## 456.190 — Static/dynamic selection

Provider may be statically linked or dynamically loaded according to application policy.

---

# 456.191 — Crypto testing

Crypto libraries phải có:

```text
known-answer tests
test vectors
property tests
fuzzing
negative tests
cross-provider tests
```

---

## 456.192 — Known-answer tests

Standard vectors phải được reproducibly encoded.

---

## 456.193 — Negative vectors

Invalid tags, signatures, keys, encodings phải được test.

---

## 456.194 — Differential tests

Independent implementations có thể được dùng để validate output.

---

## 456.195 — Differential testing limitation

Agreement giữa implementations không phải proof of correctness.

---

## 456.196 — Fuzzing

Parser, decoder, protocol state machines phải fuzz.

---

## 456.197 — Mutation tests

Crypto tests có thể mutate ciphertext/tag/signature để ensure rejection.

---

## 456.198 — Nonce misuse tests

Test suite phải verify nonce-reuse detection/policy khi API có capability này.

---

## 456.199 — RNG tests

CSPRNG statistical tests không thay thế entropy-source validation.

---

## 456.200 — Secret leakage tests

Debug/logging tooling phải test rằng secret values không bị accidentally emitted.

---

# 456.201 — Formal/security properties

Axiom metadata có thể represent claims:

```text
@constant_time
@secret
@no_alloc
@no_panic
```

---

## 456.202 — Claims vs proof

Attribute không tự biến implementation thành mathematically proven secure code.

---

## 456.203 — Security contracts

Compiler có thể verify một số local properties.

Ví dụ:

- secret cannot be passed to logging API;
- secret buffer gets cleanup;
- constant-time API used for secret comparison.

---

## 456.204 — Information-flow analysis

Future compiler tooling có thể track:

```text
secret
public
untrusted
trusted
```

taint categories.

---

## 456.205 — Taint is advisory initially

Taint analysis không được trở thành mandatory language type system ở 456.

---

## 456.206 — Secret annotations

API designers có thể annotate sensitive types/functions.

---

## 456.207 — AI security query

AI tooling có thể query:

```text
where does this secret originate?
where is it copied?
where is it logged?
where is it transmitted?
```

---

## 456.208 — Security call graph

Crypto/network/storage call graphs integrate with metadata 446.

---

## 456.209 — Dependency audit

Crypto package metadata phải identify algorithm/provider/dependencies.

---

## 456.210 — Algorithm inventory

Build tooling có thể enumerate cryptographic algorithms included in binary.

---

# 456.211 — Binary crypto footprint

Unused algorithms phải được linker-prune.

---

## 456.212 — Provider isolation

Một application chỉ dùng SHA-256 không được kéo toàn bộ asymmetric crypto suite vào binary.

---

## 456.213 — Embedded profile

Embedded builds có thể chỉ link:

```text
hash
mac
rng
```

---

## 456.214 — Freestanding crypto

Pure crypto algorithms phải có khả năng chạy without OS runtime nếu không cần entropy/key store.

---

## 456.215 — Entropy capability

CSPRNG cần OS/hardware entropy capability trên target native.

---

## 456.216 — Deterministic embedded mode

Embedded systems có thể inject hardware RNG/provider.

---

## 456.217 — Hardware crypto

Hardware security module APIs là optional platform layer.

---

## 456.218 — Accelerator abstraction

Crypto accelerator interface không được assume a particular vendor.

---

## 456.219 — DMA safety

Hardware crypto buffers obey ownership/lifetime and unsafe DMA rules.

---

## 456.220 — DMA memory

DMA-capable memory là platform-specific allocator capability.

---

# 456.221 — Secure boot integration

Secure boot verification là platform/bootloader layer.

---

## 456.222 — Code signing

Axiom can produce artifacts suitable for platform signing.

---

## 456.223 — Signing tool boundary

Private signing keys không cần nằm trong compiler process.

---

## 456.224 — Artifact digest

Compiler/linker có thể expose deterministic artifact hash.

---

## 456.225 — Reproducible signing

Reproducible artifact generation giúp external signing workflows.

---

## 456.226 — Package signing

Package ecosystem 447 có thể sign packages.

---

## 456.227 — Dependency verification

Dependency signatures/hashes được kiểm tra trước build theo policy.

---

## 456.228 — Trust roots

Trust roots thuộc package/security configuration, không hard-code language semantics.

---

## 456.229 — Supply-chain metadata

Crypto dependencies phải carry provenance metadata.

---

## 456.230 — AI supply-chain query

AI tooling có thể query:

```text
which crypto implementation is linked?
which version?
which provider?
which algorithms?
```

---

# 456.231 — Secure storage integration

Encrypted storage 455 có thể consume AEAD/KDF/key-store APIs.

---

## 456.232 — Network integration

TLS 454 consumes crypto provider APIs.

---

## 456.233 — Authentication integration

RPC/HTTP authentication consumes signature/MAC/KDF primitives.

---

## 456.234 — IPC integration

Secure IPC có thể use OS credential/key APIs.

---

## 456.235 — No cyclic core dependency

Crypto must not become a dependency of:

```text
core
lexer
parser
type checker
basic runtime
```

---

## 456.236 — Runtime layering

Dependency direction:

```text
core
 ↓
platform
 ↓
crypto
 ↓
TLS
 ↓
HTTP/RPC
```

Không được đảo ngược.

---

## 456.237 — Compile-time crypto

Comptime có thể tính pure cryptographic functions cho build-time data nếu deterministic.

---

## 456.238 — No secret externalization

Comptime must not provide a hidden mechanism to read secret environment/filesystem data.

---

## 456.239 — Compile-time RNG

Secure RNG không được tự động available trong deterministic comptime.

---

## 456.240 — Build secrets

Build systems xử lý signing secrets phải nằm ngoài language comptime sandbox.

---

# 456.241 — Cryptographic API ergonomics

API phải ưu tiên typed construction:

```text
AeadKey
Nonce
Tag
Ciphertext
Plaintext
```

thay vì:

```text
[]u8
[]u8
[]u8
[]u8
```

ở high-level API.

---

## 456.242 — Type distinction

Different semantic byte sequences nên có distinct types khi misuse có security impact.

---

## 456.243 — Explicit conversion

Raw bytes → key/ciphertext/signature phải là explicit validated conversion.

---

## 456.244 — No implicit secret exposure

Secret type không tự convert thành String/bytes printable.

---

## 456.245 — Debug formatting

Secret types phải disable ordinary debug formatting hoặc redact output.

---

## 456.246 — Error messages

Crypto errors không được include secret material.

---

## 456.247 — Logging

Crypto APIs không tự log input/output.

---

## 456.248 — Metrics

Metrics phải avoid key/plaintext content.

---

## 456.249 — Telemetry

Tracing crypto operations chỉ record metadata như algorithm/size/duration khi safe.

---

## 456.250 — Secret-safe observability

Observability APIs phải distinguish public metadata và secret payload.

---

# 456.251 — API evolution

Crypto APIs phải version algorithms independently.

---

## 456.252 — Algorithm deprecation

Deprecated algorithms có migration guidance.

---

## 456.253 — Compatibility

Legacy protocol support được isolate trong compatibility modules.

---

## 456.254 — Security profiles

Build profiles:

```text
secure
legacy
embedded
fips-like/provider-constrained
```

có thể constrain available providers/algorithms.

---

## 456.255 — Policy enforcement

Compiler/package manager có thể reject forbidden algorithms based on explicit project policy.

---

# 456.256 — Hard invariants

1. Cryptography không thuộc language core.
2. Cryptography không thuộc mandatory runtime.
3. Không có global crypto provider bắt buộc.
4. Hash, MAC, KDF, cipher, AEAD, signature và key exchange phải là abstractions riêng.
5. Cryptographic hash phải phân biệt với fast hash.
6. Checksum không được coi là authentication.
7. Digest phải có typed representation khi fixed-size.
8. MAC verification phải constant-time.
9. MAC key phải là sensitive type.
10. KDF phải có explicit context/domain separation khi protocol yêu cầu.
11. Password hashing phải dùng password KDF, không raw hash.
12. Salt phải được generate độc lập.
13. Key separation phải được hỗ trợ.
14. AEAD là high-level symmetric encryption primitive ưu tiên.
15. AEAD phải authenticate ciphertext.
16. AEAD AAD phải được hỗ trợ.
17. Nonce phải là algorithm-aware type.
18. Nonce reuse risk phải được thể hiện rõ.
19. Nonce exhaustion phải được xử lý.
20. AEAD decryption không expose unauthenticated plaintext.
21. Invalid authentication phải trả error.
22. Public-key APIs phải phân biệt key exchange và signatures.
23. PublicKey/PrivateKey/SecretKey phải có semantic distinction.
24. Invalid key encoding phải trả typed error.
25. Private-key export phải explicit.
26. Non-exportable keys phải được hỗ trợ.
27. Key ownership phải deterministic.
28. Secret memory phải có secure cleanup capability.
29. Compiler phải preserve required zeroization semantics.
30. Memory locking là optional capability và không được overclaim.
31. Swap/core-dump limitations phải được document.
32. Secure RNG phải dùng OS/hardware entropy trên native targets.
33. Ordinary PRNG không phải secure RNG.
34. Deterministic RNG phải explicit.
35. Secure RNG failure không được silently fallback sang predictable randomness.
36. Bounded random integer phải tránh modulo bias.
37. Constant-time comparison phải có primitive riêng.
38. `@constant_time` là semantic/security contract, không phải magic proof.
39. Compiler không được tuyên bố source branchless là automatically constant-time.
40. Axiom phải acknowledge side-channel limitations.
41. SecureBuffer/Secret abstraction phải integrate ownership model 423.
42. Secret clone phải explicit.
43. Secret không tự convert thành printable string.
44. Secret debug output phải bị disable/redact.
45. Crypto errors không được leak secrets.
46. X.509/certificate parsing phải safe đối với untrusted input.
47. Certificate validation phải policy-aware.
48. Hostname validation phải được thực hiện cho secure TLS clients.
49. Trust anchors phải explicit.
50. Revocation là policy/provider layer.
51. Malformed cryptographic encodings phải return error.
52. Parsers phải có length/resource limits.
53. High-level crypto APIs phải làm insecure misuse khó hơn.
54. Weak algorithms phải được isolate/deprecate.
55. Legacy algorithms phải explicit opt-in.
56. Security policies có thể forbid algorithms.
57. Crypto implementations có thể dùng hardware acceleration.
58. CPU feature dispatch không được thay đổi security semantics.
59. Crypto có thể có allocation-free implementations.
60. Crypto functions có thể expose `@no_alloc`.
61. Pure crypto functions không nên block.
62. Crypto failure dùng Result model.
63. Axiom phải có khả năng implement crypto algorithms trực tiếp.
64. Compiler không được phụ thuộc OpenSSL/libsodium hay crypto compiler dependency.
65. External crypto providers có thể dùng qua FFI.
66. Foreign crypto correctness không được compiler tự claim.
67. Provider ownership/lifetime phải explicit.
68. Crypto libraries phải có known-answer tests.
69. Negative test vectors phải được kiểm tra.
70. Fuzzing phải được áp dụng cho crypto parsers/decoders.
71. Differential testing là useful validation nhưng không phải proof.
72. Nonce misuse phải được test.
73. Secret leakage qua logging/debugging phải được test.
74. Security metadata phải phân biệt claim và proof.
75. AI tooling phải query được secret/data flow khi metadata hỗ trợ.
76. Crypto algorithm inventory phải có thể inspect.
77. Unused crypto algorithms phải được linker-prune.
78. Embedded/freestanding crypto phải khả dụng.
79. Secure entropy phải là explicit platform capability.
80. Hardware crypto accelerator abstraction không phụ thuộc vendor.
81. DMA crypto buffers phải obey ownership/safety model.
82. Secure boot/code signing nằm ngoài crypto core semantics.
83. Signing private keys không cần nằm trong compiler.
84. Artifact hashes phải deterministic.
85. Package signatures integrate package supply-chain model 447.
86. Dependency trust roots phải configurable.
87. Crypto không được trở thành dependency của core compiler.
88. Crypto không được trở thành dependency của basic runtime.
89. TLS/HTTP/storage consume crypto through layered APIs.
90. Comptime crypto chỉ được dùng cho deterministic pure computations.
91. Comptime không có hidden secure-random access.
92. Build secrets không thuộc comptime sandbox.
93. High-level crypto APIs nên distinguish `Plaintext`, `Ciphertext`, `Nonce`, `Tag`, `Key`.
94. Raw byte conversions phải explicit.
95. Crypto observability không được log sensitive payload.
96. Algorithm versioning phải độc lập package versioning.
97. Security profiles có thể constrain algorithms/providers.
98. AI tooling có thể identify linked crypto providers.
99. Axiom không tuyên bố type safety đồng nghĩa cryptographic security.
100. **Axiom phải cho phép xây cryptographic software native, allocation-aware, SIMD/hardware-accelerated và freestanding, đồng thời giữ toàn bộ crypto stack optional đối với application không sử dụng nó.**

**BOOTSTRAP-456 hoàn tất.**

---

# BOOTSTRAP-457 — TEXT, UNICODE, INTERNATIONALIZATION, LOCALIZATION, COLLATION & HUMAN-LANGUAGE FOUNDATION

Task kế tiếp khóa một phần rất quan trọng đối với Axiom vì **UTF-8 đã được chọn làm mặc định**:

```text
UTF-8
Unicode scalar values
grapheme clusters
normalization
case mapping
collation
locale
date/time localization
pluralization
formatting
text segmentation
terminal/display text
```

Đặc biệt sẽ tách rõ:

```text
byte
→ UTF-8 code unit
→ Unicode scalar value
→ grapheme cluster
→ word/sentence
→ locale-aware human text
```

để tránh lỗi thiết kế phổ biến kiểu:

```text
char == character == grapheme == byte
```

và xác định chính xác `String`, `StringSlice`, `char`, indexing, slicing, Unicode normalization và text iteration trong Axiom.