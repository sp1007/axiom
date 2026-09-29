Tiếp tục với **BOOTSTRAP-610**, tập trung hoàn thiện lớp cryptography/TLS thực sự phía dưới boundary của BOOTSTRAP-609, nhưng vẫn giữ nguyên nguyên tắc provider-based và không ép Axiom phụ thuộc vào một thư viện crypto bên thứ ba.

:::writing{variant="document" id="74163" title="BOOTSTRAP-610 — Native Cryptography, TLS, Certificate Trust, Key Management & Secure Transport Runtime 5.0"}

# BOOTSTRAP-610
# Native Cryptography, TLS, Certificate Trust, Key Management & Secure Transport Runtime 5.0

**Status:** ARCHITECTURE SPECIFICATION — COMPLETE  
**Layer:** Native Security Runtime / Cryptographic Runtime  
**Depends on:** BOOTSTRAP-600 → 609  
**Primary integrations:** Security, Secrets, Diagnostics, Configuration, Resource Governor, Scheduler, Networking, IPC, FFI  
**Targets:** Windows, Linux, macOS, Android, iOS, WASM, Embedded

---

# 1. Purpose

BOOTSTRAP-610 defines Axiom's cryptographic and secure-transport architecture.

It provides the native abstraction required for:

- cryptographic hashing
- MAC
- authenticated encryption
- public-key cryptography
- digital signatures
- key generation
- key import/export
- certificate parsing
- certificate-chain validation
- trust stores
- hostname verification
- TLS client/server sessions
- secure random generation
- key derivation
- password/key derivation
- secure key storage
- cryptographic provider selection
- hardware-backed keys
- TLS session resumption
- certificate rotation
- secure memory handling
- crypto diagnostics
- deterministic cryptographic testing

The architecture must support both:

```text
Axiom-native cryptographic implementation
```

and:

```text
platform cryptographic provider
```

without changing application-level APIs.

---

# 2. Core Design Goals

Axiom cryptography MUST provide:

1. explicit algorithm selection
2. secure defaults
3. constant-time implementations where required
4. opaque key material
5. secure random generation
6. bounded parsing
7. explicit trust configuration
8. hostname verification
9. asynchronous TLS
10. provider abstraction
11. hardware-backed key support
12. certificate rotation
13. key lifetime control
14. secret zeroization where technically possible
15. deterministic testing interfaces
16. FIPS/compliance-capable provider boundaries
17. minimal runtime overhead
18. dead-strippable algorithms/providers

---

# 3. Non-Goals

The core layer does not attempt to provide:

- password management UI
- identity-provider infrastructure
- certificate authority administration
- OAuth
- OpenID Connect
- SSH
- PGP application semantics
- blockchain cryptography
- arbitrary custom cryptographic algorithms
- insecure legacy algorithms merely for compatibility

Higher-level security protocols may build on this layer.

---

# 4. Security Principle

The architecture follows:

```text
Application
    ↓
Security Policy
    ↓
Cryptographic Operation
    ↓
Provider
    ↓
Native CPU / OS / Hardware
```

No application should need to know whether a cryptographic operation was performed by:

```text
Axiom native implementation
CPU instruction
OS crypto API
TPM
Secure Enclave
Android hardware-backed keystore
external provider
```

---

# 5. Provider Architecture

Core abstraction:

```text
CryptoProvider
```

A provider exposes capabilities:

```text
hash
mac
aead
signature
key_exchange
random
kdf
certificate
tls
key_store
```

Provider selection is explicit.

---

# 6. Provider Types

Supported provider classes:

```text
NativeProvider
PlatformProvider
HardwareProvider
ExternalProvider
TestProvider
```

The implementation must distinguish provider trust and implementation provenance.

---

# 7. Native Provider

The Axiom runtime may provide native implementations for selected algorithms.

The native provider must be:

- memory-safe
- audited
- constant-time where required
- fuzz-tested
- independently testable
- versioned

Algorithms are enabled individually.

---

# 8. Platform Provider

Examples:

```text
Windows → CNG / platform crypto
Apple   → Security / CryptoKit-compatible platform facilities
Android → platform keystore/crypto
Linux   → configured native/provider backend
```

Platform APIs are wrapped behind Axiom interfaces.

---

# 9. Hardware Provider

Hardware-backed operations may use:

```text
TPM
Secure Enclave
Android Keystore hardware
HSM
platform secure hardware
```

Private keys may never become exportable.

---

# 10. Test Provider

Testing uses a deterministic provider.

It may provide:

```text
deterministic random
known test keys
fault injection
record/replay
```

It must never be used accidentally by production builds.

---

# 11. Algorithm Registry

Algorithms are identified by stable IDs:

```text
HashAlgorithm
MacAlgorithm
AeadAlgorithm
SignatureAlgorithm
KeyExchangeAlgorithm
KdfAlgorithm
```

The registry must be deterministic.

---

# 12. Cryptographic Agility

Application APIs must not hard-code provider-specific objects.

Example:

```text
HashAlgorithm.Sha256
```

rather than:

```text
OpenSSL_SHA256
```

---

# 13. Secure Defaults

The default security profile should prefer contemporary algorithms and reject obsolete constructions.

Legacy algorithms require explicit compatibility configuration.

---

# 14. Hashing

Axiom provides streaming hashing:

```text
HashContext
```

API:

```text
ctx.update(data)
ctx.finalize()
```

---

# 15. Hash Result

Hash outputs are fixed-size typed values where possible:

```text
Hash256
Hash384
Hash512
```

rather than arbitrary strings.

---

# 16. Hash Streaming

Hashing must support:

```text
file
network stream
memory buffer
multiple chunks
```

without requiring the entire input in memory.

---

# 17. Hash Context Ownership

A hash context is mutable and should not be concurrently modified.

It can be finalized only once unless an explicit `clone/fork` operation exists.

---

# 18. MAC

Core MAC abstraction:

```text
MacContext
```

Operations:

```text
init(key)
update(data)
finalize()
verify(tag)
```

---

# 19. MAC Verification

Verification must use constant-time comparison where the MAC semantics require it.

A mismatch returns:

```text
AuthenticationFailed
```

rather than exposing partial comparison information.

---

# 20. AEAD

Authenticated encryption abstraction:

```text
AeadCipher
```

supports:

```text
encrypt
decrypt
```

with:

```text
key
nonce
plaintext
associated_data
```

---

# 21. AEAD Semantics

The encrypted result includes authentication information.

Conceptually:

```text
ciphertext + authentication tag
```

The implementation must reject modified ciphertext before exposing plaintext.

---

# 22. Nonce Safety

Nonce reuse rules are algorithm-specific.

The API must make accidental reuse difficult.

A session may own a nonce generator or sequence.

---

# 23. Nonce State

For protocols requiring monotonic counters:

```text
NonceSequence
```

provides controlled progression.

Counter exhaustion is a hard error.

---

# 24. AEAD Streaming

Where an algorithm supports safe streaming, Axiom may expose:

```text
AeadStream
```

otherwise encryption is chunk-based under a higher-level framing protocol.

---

# 25. Key Types

Cryptographic keys are strongly typed:

```text
SymmetricKey
PublicKey
PrivateKey
SecretKey
KeyHandle
```

A private key is not equivalent to an arbitrary byte array.

---

# 26. Private Key Opacity

Safe code should not receive raw private key bytes unless the key was explicitly created as exportable.

Hardware-backed keys are represented only by opaque handles.

---

# 27. Key Usage Policy

Each key can declare allowed operations:

```text
Sign
Verify
Encrypt
Decrypt
Derive
KeyExchange
Wrap
Unwrap
```

A key cannot silently be reused for an incompatible purpose.

---

# 28. Key Lifetime

Keys may have:

```text
ephemeral
session
application
persistent
hardware
```

lifetimes.

The key manager owns persistent-key lifecycle.

---

# 29. Key IDs

Persistent keys have stable opaque identifiers:

```text
KeyId
```

rather than exposing storage paths.

---

# 30. Key Generation

Example:

```text
KeyManager.generate(
    KeySpec {
        algorithm
        usage
        persistence
        export_policy
    }
)
```

---

# 31. Export Policy

A key can be:

```text
NonExportable
ExportPublicOnly
Exportable
```

The default for sensitive persistent private keys is non-exportable where the provider supports it.

---

# 32. Key Import

Imported keys are validated before becoming usable.

Malformed or inconsistent key material must fail closed.

---

# 33. Key Destruction

Key destruction removes access to the key.

For software-held secret material, the provider attempts secure zeroization.

For hardware keys, destruction delegates to the secure provider.

---

# 34. Secure Memory

Axiom defines:

```text
SecureBuffer
```

with properties:

- restricted access
- zeroization on release where possible
- optional locked pages
- no automatic logging
- no ordinary diagnostic serialization

---

# 35. Secure Memory Limitations

The runtime must document that software zeroization cannot guarantee removal from:

- CPU caches
- copies made by the OS
- swap before locking
- external hardware
- crash snapshots already produced

The abstraction reduces exposure; it does not make impossible guarantees.

---

# 36. Secret Integration

BOOTSTRAP-601 `Secret<T>` integrates with:

```text
SecureBuffer
KeyHandle
PrivateKey
Credential
```

Secrets remain opaque in ordinary formatting/debugging.

---

# 37. Randomness

Axiom defines:

```text
SecureRandom
```

for security-sensitive randomness.

It must use an operating-system or hardware-backed CSPRNG.

---

# 38. No Application PRNG for Security

Ordinary pseudo-random generators cannot satisfy `SecureRandom`.

The type system keeps these APIs distinct.

---

# 39. Random Failure

If secure randomness is unavailable:

```text
SecureRandomError
```

is returned.

The runtime must not silently fall back to a predictable PRNG.

---

# 40. Randomness Provider

Possible sources:

```text
Windows CNG
Linux getrandom
Apple Security APIs
Android platform
hardware RNG
```

depending on backend.

---

# 41. KDF

Core KDF abstraction:

```text
KeyDerivation
```

supports approved constructions through typed algorithm IDs.

Inputs can include:

```text
secret
salt
context
info
length
```

---

# 42. Password Derivation

Password-based derivation is separate:

```text
PasswordKdf
```

because its resource behavior differs from ordinary key derivation.

---

# 43. Password KDF Resource Limits

Password derivation may consume substantial CPU/memory.

It therefore integrates with BOOTSTRAP-606.

No arbitrary attacker-controlled cost parameter may bypass runtime limits.

---

# 44. Digital Signatures

Core abstraction:

```text
Signer
Verifier
```

Supported algorithms depend on provider capability.

The architecture can accommodate contemporary signature families without embedding one algorithm into the language syntax.

---

# 45. Signing API

```text
signature = signer.sign(message)
```

For large data:

```text
SignContext
```

supports streaming where the algorithm permits it.

---

# 46. Verification API

```text
verifier.verify(message, signature)
```

returns:

```text
Valid
Invalid
Malformed
Unsupported
```

---

# 47. Key Exchange

Core abstraction:

```text
KeyExchange
```

produces a shared secret.

The resulting secret must immediately be represented as an opaque secret/key object.

---

# 48. Ephemeral Keys

Ephemeral key exchange keys have automatic lifetime.

After the exchange completes, temporary material is released.

---

# 49. Hybrid/PQ Readiness

The API must allow future hybrid or post-quantum key-exchange/signature algorithms without changing:

```text
KeyHandle
KeyExchange
TlsProvider
```

interfaces.

The architecture must not assume every algorithm has the same key size or structure.

---

# 50. Certificate Model

Axiom defines:

```text
Certificate
CertificateChain
CertificatePolicy
TrustAnchor
```

---

# 51. Certificate Parsing

Certificate parsing is bounded.

A certificate may not allocate memory based on an unchecked attacker-controlled length.

---

# 52. Certificate Representation

A parsed certificate may expose:

```text
subject
issuer
serial
validity
public_key
extensions
signature_algorithm
```

Raw DER remains available through an explicitly owned immutable byte buffer.

---

# 53. Certificate Chain

A chain is:

```text
leaf
 ↓
intermediate
 ↓
...
 ↓
trust anchor
```

Validation is a separate operation from parsing.

---

# 54. Trust Store

Axiom defines:

```text
TrustStore
```

which may obtain trust anchors from:

```text
system
application
deployment
custom
```

---

# 55. Trust Store Isolation

Trust stores are explicit objects.

There is no requirement for a mutable global trust store.

---

# 56. System Trust

The platform provider may expose the operating system trust store.

The exact trust roots are platform-owned.

Applications can choose system trust explicitly.

---

# 57. Application Trust

Applications may provide a private trust store.

Useful for:

- private PKI
- internal services
- development environments
- enterprise deployments

---

# 58. Trust Store Precedence

Trust configuration follows the explicit policy hierarchy established by BOOTSTRAP-601.

An application must not accidentally combine incompatible trust sources.

---

# 59. Certificate Validation

Validation evaluates:

```text
chain
trust anchors
time
key usage
extended key usage
basic constraints
name constraints where applicable
policy
```

---

# 60. Validation Time

Certificate validity is evaluated against an explicit clock.

Testing can inject:

```text
Clock
```

to reproduce expiration conditions.

---

# 61. Hostname Verification

Hostname verification is a distinct policy step after chain validation.

It checks the requested host against permitted certificate identity fields according to the provider's standards.

---

# 62. Wildcard Rules

Wildcard matching must follow the applicable certificate naming rules.

The implementation must not implement naive substring matching.

---

# 63. Certificate Revocation

The architecture allows:

```text
RevocationPolicy
```

with modes such as:

```text
Disabled
ProviderDefault
CRL
OCSP
Stapled
Strict
```

Availability and platform behavior may vary.

---

# 64. Revocation Boundary

The core certificate model does not force network access merely to validate every certificate.

Revocation behavior is controlled by policy/provider.

---

# 65. OCSP

If supported, OCSP is a validation component rather than a property of raw TLS transport.

It has its own:

- timeout
- cache
- resource limit
- capability requirements

---

# 66. Certificate Pinning

Axiom may expose explicit pinning policies:

```text
CertificatePin
PublicKeyPin
```

Pinning is application/deployment policy, not the universal default.

---

# 67. Pin Rotation

Pin sets can contain multiple valid entries to support rotation:

```text
current
next
```

The application can update them before replacing the old key.

---

# 68. TLS Provider Architecture

BOOTSTRAP-609 defined:

```text
TlsProvider
```

BOOTSTRAP-610 specifies its full responsibilities:

```text
create_client
create_server
handshake
read
write
shutdown
certificate
session
key
```

---

# 69. TLS Version Policy

The provider exposes negotiated protocol version.

The security policy controls permitted versions.

Obsolete versions must not be silently selected merely because a peer offers them.

---

# 70. Cipher Suite Policy

The application specifies a policy rather than directly depending on implementation-specific cipher objects.

Example:

```text
TlsPolicy {
    minimum_version
    maximum_version
    allowed_algorithms
}
```

---

# 71. TLS Client

```text
TlsClient.connect(
    tcp_stream,
    server_name,
    policy
)
```

returns:

```text
TlsStream
```

after successful handshake.

---

# 72. TLS Server

```text
TlsServer.accept(
    tcp_stream,
    certificate_selector
)
```

performs the server-side handshake.

---

# 73. Certificate Selection

Server configuration can select certificates based on:

```text
SNI
algorithm
policy
tenant
```

without exposing private keys to application code.

---

# 74. Server Key Storage

Server private keys may be:

```text
software protected
OS protected
hardware backed
```

The TLS provider performs signing/decryption through the key handle where possible.

---

# 75. TLS Async Handshake

Handshake is a state machine:

```text
Created
 ↓
Negotiating
 ↓
CertificateProcessing
 ↓
KeyExchange
 ↓
Established
```

Every state can suspend on network I/O.

---

# 76. TLS Cancellation

Handshake cancellation:

```text
cancel
 ↓
abort handshake
 ↓
close or return underlying transport according to policy
```

No partially initialized TLS object remains usable.

---

# 77. TLS Shutdown

Graceful shutdown may send the protocol close notification before closing the underlying stream.

Deadline applies.

---

# 78. TLS Close Timeout

If graceful close exceeds the deadline:

```text
transport close
```

may be forced.

---

# 79. TLS Record Buffering

The provider controls record framing and internal buffering.

The Axiom API exposes bounded application-level reads/writes.

---

# 80. TLS Backpressure

TLS must propagate transport backpressure rather than buffering unlimited plaintext.

---

# 81. TLS Zero-Copy

Provider implementations may optimize record processing but must preserve the ownership rules of BOOTSTRAP-609.

---

# 82. TLS Session Resumption

Session resumption is represented as:

```text
TlsSessionTicket
```

or opaque provider state.

Application code must not parse provider-private session-ticket structures.

---

# 83. Session Ticket Protection

Ticket keys belong to the TLS provider/server key-management layer.

They must not appear in logs.

---

# 84. TLS 0-RTT

If supported, 0-RTT is explicitly represented because replay characteristics differ from ordinary application data.

The default application policy should require opt-in for operations that may have side effects.

---

# 85. TLS Early Data

The API distinguishes:

```text
EarlyData
AuthenticatedData
```

so applications cannot accidentally treat early data as equivalent to fully established-session data.

---

# 86. ALPN

The provider exposes negotiated ALPN:

```text
tls.negotiated_protocol()
```

HTTP transport can use this to select:

```text
HTTP/1.1
HTTP/2
```

---

# 87. SNI

SNI is part of the explicit client TLS configuration.

Server TLS uses it to select the appropriate certificate/policy.

---

# 88. TLS Peer Information

After handshake, applications may query:

```text
peer_certificate
peer_chain
protocol_version
negotiated_cipher
negotiated_alpn
```

where provider policy permits.

---

# 89. TLS Peer Identity

The application must not infer identity merely from a successful TCP connection.

Identity comes from:

```text
certificate validation
hostname policy
optional application authentication
```

---

# 90. TLS Authentication Modes

Supported conceptual modes:

```text
Anonymous
ServerAuthenticated
MutualAuthenticated
```

Anonymous TLS modes should be restricted to explicit specialized use cases.

---

# 91. Mutual TLS

Client certificate configuration:

```text
ClientIdentity
```

contains:

```text
certificate chain
private key handle
selection policy
```

---

# 92. Private Key Operations

The TLS provider should request operations from:

```text
KeyProvider
```

instead of requiring extraction of raw private key bytes.

---

# 93. Hardware-backed TLS

Architecture:

```text
TLS Provider
    ↓
Key Handle
    ↓
Hardware Provider
    ↓
TPM / Secure Enclave / Keystore
```

The private key remains inside the secure provider.

---

# 94. Key Store

Axiom defines:

```text
KeyStore
```

operations:

```text
generate
import
open
delete
list_metadata
```

Private key enumeration is metadata-only unless explicitly authorized.

---

# 95. Key Store Namespaces

Keys may belong to:

```text
application
service
user
deployment
hardware
```

namespaces.

---

# 96. Key Access Policy

Key access is controlled by:

```text
KeyUsage
Capability
ProviderPolicy
```

A key may be usable for TLS server authentication but not arbitrary signing.

---

# 97. Key Rotation

Key rotation workflow:

```text
generate new key
 ↓
issue new certificate
 ↓
publish new identity
 ↓
accept old + new during transition
 ↓
retire old identity
 ↓
destroy old key
```

---

# 98. Atomic Identity Rotation

A TLS server should be able to switch certificate/key pairs atomically from the perspective of new connections.

Existing connections continue using their established session.

---

# 99. Certificate Reload

Configuration reload may update:

```text
trust store
server certificates
TLS policy
```

without mutating established TLS sessions.

New sessions use the new configuration.

---

# 100. Trust Store Reload

Existing sessions remain valid according to the policy under which they were established unless explicit security policy requires termination.

---

# 101. Crypto Resource Accounting

BOOTSTRAP-606 accounts:

```text
crypto operations
key objects
TLS sessions
certificate objects
secure memory
hardware sessions
KDF CPU budget
```

---

# 102. Crypto DoS Protection

Untrusted input must not trigger unlimited:

```text
certificate parsing
signature verification
KDF work
OCSP requests
TLS handshakes
```

Resource limits apply.

---

# 103. TLS Handshake Limits

Server configuration supports:

```text
max_handshakes
max_pending_handshakes
handshake_timeout
certificate_chain_size
```

---

# 104. Certificate Size Limit

Certificate chains are bounded by configurable maximum encoded size and element count.

---

# 105. Public-Key Operation Limits

Applications may impose rate limits on expensive verification operations.

This is particularly relevant for untrusted inbound connections.

---

# 106. Secure Random Rate

Secure random generation may be accounted for diagnostic purposes, but normal entropy reads should not be artificially throttled in ways that compromise protocol correctness.

---

# 107. Constant-Time Boundary

Operations handling secret-dependent data should use provider implementations designed to minimize timing leakage.

The language/runtime cannot guarantee constant-time behavior for arbitrary application code.

---

# 108. Secret Comparison

Axiom provides:

```text
constant_time_equal(a, b)
```

for equal-length secret buffers.

---

# 109. Secret Formatting

Private keys and secrets cannot implement ordinary implicit string formatting.

This prevents accidental:

```text
print(secret)
log(secret)
serialize(secret)
```

---

# 110. Debugging

Debugger inspection of secret material is controlled by the security/debug policy.

Production crash diagnostics must redact it.

---

# 111. Crash Dumps

Crypto contexts should mark sensitive memory regions so platform crash-dump integrations can exclude them where supported.

---

# 112. Compiler Security Metadata

Compiler annotations may express:

```text
@secret
@constant_time
@non_exportable
@key_usage(...)
```

These are metadata, not magical guarantees.

---

# 113. Unsafe Crypto

Custom cryptographic primitives may require:

```text
unsafe crypto
```

and explicit provider registration.

They cannot silently replace approved algorithms in secure profiles.

---

# 114. Algorithm Deprecation

Algorithms may be marked:

```text
Supported
Deprecated
Restricted
Disabled
```

Security policy determines whether deprecated algorithms can be used.

---

# 115. Provider Versioning

Each provider reports:

```text
provider_id
provider_version
algorithm_set
security_profile
```

This becomes part of diagnostic/build metadata where relevant.

---

# 116. Provider Isolation

A provider must not modify global process crypto state without explicit runtime ownership.

---

# 117. External Provider

External crypto providers use:

```text
CryptoProvider
```

FFI boundary.

They must declare:

```text
memory ownership
threading model
blocking behavior
error model
key ownership
```

---

# 118. Blocking Provider

A provider performing blocking operations must integrate with BOOTSTRAP-607's blocking pool.

It must not block ordinary async workers.

---

# 119. Provider Concurrency

Provider capabilities declare whether contexts are:

```text
Send
Sync
ThreadAffine
```

using the concurrency model from BOOTSTRAP-608.

---

# 120. Provider Fault Isolation

A faulty provider must not corrupt Axiom runtime ownership structures.

Where practical, high-risk external providers may run behind process isolation.

---

# 121. FIPS / Compliance Boundary

Compliance-specific cryptographic modes are provider/profile concerns.

The core language does not claim that every Axiom build is automatically compliant with a particular certification.

---

# 122. Compliance Metadata

A provider can declare:

```text
compliance_profile
validated_module_id
approved_algorithms
```

for deployment/audit systems.

---

# 123. Secure Boot Integration

If platform security facilities expose trust information, the key/trust provider may use it.

The core cryptography API does not require Secure Boot.

---

# 124. Hardware Attestation Boundary

Future platform providers may expose:

```text
AttestationProvider
```

for hardware-backed identity.

Attestation is not part of basic TLS.

---

# 125. Certificate Transparency

Certificate-transparency verification can be implemented as an optional validation policy.

It does not belong in the raw certificate parser.

---

# 126. Trust Decision Object

Certificate validation returns:

```text
TrustDecision
```

containing:

```text
trusted
failure_reason
chain
policy
```

Diagnostic metadata must not expose secret information.

---

# 127. Verification Context

Validation accepts an explicit:

```text
VerificationContext
```

containing:

```text time
hostname
usage
trust_store
revocation_policy
pin_policy
```

This avoids hidden global state.

---

# 128. TLS Policy Object

```text
TlsPolicy {
    versions
    algorithms
    trust_store
    hostname_policy
    revocation_policy
    client_identity
    alpn
    early_data_policy
}
```

---

# 129. Immutable Policy

Once a TLS session starts, its policy snapshot is immutable.

Configuration reload creates a new policy snapshot.

---

# 130. TLS Policy Fingerprint

The policy can produce:

```text
TlsPolicyFingerprint
```

used for:

- diagnostics
- connection-pool partitioning
- reproducibility
- security auditing

---

# 131. Connection Pool Integration

Two TLS connections may be reused only if their TLS policy fingerprints are compatible.

---

# 132. HTTP Integration

BOOTSTRAP-609's HTTPS transport becomes:

```text
HTTP
 ↓
TLS Policy
 ↓
TLS Provider
 ↓
TCP
```

---

# 133. HTTP Certificate Error

HTTP clients preserve TLS errors:

```text
HttpError {
    cause = TlsError(...)
}
```

The original error remains inspectable.

---

# 134. TLS Diagnostics

Structured events:

```text
tls.session.created
tls.handshake.started
tls.handshake.completed
tls.handshake.failed
tls.certificate.rejected
tls.session.resumed
tls.session.closed
```

---

# 135. Certificate Diagnostics

Safe metadata:

```text
subject
issuer
serial
expiration
algorithm
```

Private-key contents are never emitted.

---

# 136. Crypto Metrics

Metrics may include:

```text
hash_operations
signature_operations
verification_operations
aead_operations
tls_handshakes
tls_resumptions
certificate_failures
key_store_operations
```

---

# 137. Secret Redaction

Diagnostics automatically classify:

```text
PrivateKey
SymmetricKey
Password
SessionTicket
Credential
```

as sensitive.

---

# 138. Error Redaction

Errors must never include raw:

```text
private key
password
authorization header
session ticket
```

even if a provider accidentally supplies them as context.

---

# 139. Config Integration

BOOTSTRAP-601 configures:

```text
TLS versions
trust source
certificate paths/references
key references
provider
proxy
revocation
timeouts
handshake limits
```

---

# 140. Secret Provider Integration

Private key references should normally point to:

```text
SecretProvider
KeyStore
HardwareProvider
```

rather than embedding private-key bytes in ordinary configuration.

---

# 141. Configuration Example

Conceptual:

```text
tls {
    provider = "platform"
    min_version = "modern"
    trust = "system"
    verify_hostname = true
    revocation = "provider_default"
}
```

The exact configuration syntax belongs to BOOTSTRAP-601.

---

# 142. Network Capability Integration

TLS may require:

```text
network.connect
```

but cryptographic operations themselves may require only:

```text
crypto.use
```

depending on deployment policy.

---

# 143. Key Capability

Persistent key access may require:

```text
KeyCapability
```

with usage restrictions.

---

# 144. Hardware Key Capability

Hardware-backed key operations may additionally require:

```text
hardware.crypto
```

capability.

---

# 145. Capability Chain

Secure HTTPS connection:

```text
network.connect
       +
crypto.use
       +
trust.read
       +
key.use (server/client identity)
```

Only the required subset is granted.

---

# 146. Scheduler Integration

Crypto operations are classified:

```text
cheap
moderate
expensive
blocking
```

Expensive operations may use dedicated executor resources.

---

# 147. Async TLS

TLS handshake/read/write are async operations.

Crypto computation may execute on:

```text
CPU executor
crypto worker
hardware async queue
```

depending on provider.

---

# 148. GPU Crypto

General-purpose GPU cryptography is not required by this core runtime.

A provider may expose specialized acceleration separately.

The default secure path remains CPU/hardware-provider based.

---

# 149. SIMD Acceleration

Native crypto providers may use CPU SIMD instructions.

This is an implementation optimization hidden behind stable APIs.

---

# 150. CPU Feature Detection

The provider may select optimized implementations based on:

```text
CPU feature set
```

while retaining a portable fallback.

---

# 151. Deterministic Tests

Crypto tests use known-answer vectors.

Examples:

```text
hash vectors
MAC vectors
AEAD vectors
signature vectors
KDF vectors
certificate vectors
TLS handshake transcripts
```

---

# 152. Test Provider Restrictions

Deterministic test randomness must never be silently selected in production.

Build/link metadata identifies test providers.

---

# 153. Fault Injection

Provider tests may inject:

```text
random failure
key-store failure
hardware unavailable
certificate parser failure
TLS alert
provider timeout
```

---

# 154. Interoperability Tests

TLS providers should test against known external implementations.

The test harness validates:

```text
protocol negotiation
certificate verification
ALPN
SNI
session resumption
close behavior
```

---

# 155. Cross-Platform Tests

The same Axiom TLS test suite runs against:

```text
Windows
Linux
macOS
Android
iOS
```

where supported.

---

# 156. WASM Crypto

Pure cryptographic operations can run inside WASM if implemented by the provider.

Hardware-backed key operations require host capabilities.

---

# 157. WASM TLS

WASM TLS may use:

```text
Axiom TLS provider
```

or:

```text
host secure transport
```

depending on the host.

---

# 158. Embedded Crypto

Embedded targets can provide a minimal provider implementing only required algorithms.

Unused algorithms are dead-stripped.

---

# 159. Minimal Profile

A minimal Axiom application might link only:

```text
SHA-256
AES-GCM
SecureRandom
```

without:

```text
TLS
HTTP
certificate parser
key store
```

if unused.

---

# 160. TLS-only Profile

An HTTPS client may link:

```text
TCP
DNS
TLS
certificate validation
secure random
required crypto
HTTP
```

and nothing else.

---

# 161. Server Profile

A TLS server may additionally link:

```text
certificate/key store
server identity
key provider
TLS listener
```

---

# 162. Static Dead Stripping

The linker removes:

```text
unused algorithms
unused providers
unused certificate formats
unused key stores
unused TLS versions
```

where compile-time usage permits.

---

# 163. Certificate Format Boundary

DER/ASN.1 parsing belongs to the certificate subsystem.

Other certificate formats can be adapters.

---

# 164. ASN.1 Parser

If ASN.1 is required internally, the parser must be:

- bounded
- incremental where useful
- integer-overflow safe
- recursion-bounded
- fuzz-tested

---

# 165. Recursive Certificate Structures

Parser recursion depth must be bounded.

An attacker cannot exhaust the stack through malformed nesting.

---

# 166. Certificate Chain Depth

Maximum chain depth is configurable and bounded.

---

# 167. Key Size Policy

Security policy can restrict unacceptable key sizes.

The cryptographic provider remains responsible for algorithm-specific validation.

---

# 168. Algorithm Parameters

Parameters are strongly typed rather than passed as arbitrary byte arrays whenever possible.

This reduces malformed configuration.

---

# 169. Generic Crypto Escape Hatch

An advanced provider API may expose raw algorithm parameters, but it belongs to:

```text
unsafe.crypto
```

or explicit provider-level APIs.

---

# 170. No Implicit Algorithm Downgrade

If the configured policy rejects an algorithm, the provider must return:

```text
AlgorithmNotAllowed
```

rather than silently selecting a weaker algorithm.

---

# 171. Negotiation

Negotiation may select among algorithms permitted by policy.

The selected result must be observable for diagnostics.

---

# 172. TLS Downgrade Protection

The TLS provider is responsible for protocol downgrade protections applicable to the negotiated protocol.

---

# 173. Certificate Name Constraints

Where supported, certificate validation must preserve relevant name constraints rather than reducing validation to simple root trust.

---

# 174. Extended Key Usage

TLS server/client authentication must respect relevant extended key usage policy.

---

# 175. Key Usage

Certificates used for signing/encryption must satisfy the requested operation's usage constraints.

---

# 176. Certificate Time Validation

Validity checks use:

```text not_before <= current_time <= not_after
```

with appropriate provider semantics.

---

# 177. Clock Failure

If the platform clock is unavailable or clearly invalid, certificate validation returns an explicit error rather than assuming validity.

---

# 178. Time Synchronization

Network time synchronization is outside this subsystem.

The runtime may expose clock diagnostics.

---

# 179. Secure Transport Boundary

Final stack:

```text
Application
   ↓
Protocol
   ↓
TlsStream
   ↓
TlsProvider
   ↓
CryptoProvider / KeyProvider
   ↓
TCP
   ↓
NetworkBackend
```

---

# 180. Key Boundary

```text
TLS
 ↓
KeyHandle
 ↓
KeyProvider
 ├── Software
 ├── OS
 ├── TPM
 ├── Secure Enclave
 ├── Android Keystore
 └── HSM
```

---

# 181. Trust Boundary

```text
Certificate
 ↓
Parser
 ↓
Chain Builder
 ↓
Trust Store
 ↓
Verification Policy
 ↓
TrustDecision
```

---

# 182. Randomness Boundary

```text
SecureRandom
 ↓
OS / Hardware entropy
 ↓
Crypto Provider
```

No insecure fallback.

---

# 183. Complete HTTPS Architecture

```text
HttpClient
    ↓
ConnectionPool
    ↓
Proxy (optional)
    ↓
TlsStream
    ↓
TlsProvider
    ↓
Certificate Validation
    ↓
KeyProvider
    ↓
TcpStream
    ↓
NetworkReactor
    ↓
Executor
    ↓
OS
```

---

# 184. Secure Service Architecture

```text
Supervisor
    ↓
Service
    ↓
Network Capability
    ↓
Listener
    ↓
TLS Server
    ↓
Certificate + Key Provider
    ↓
Application Protocol
```

---

# 185. Build Metadata

The executable may record:

```text
crypto provider
TLS provider
enabled algorithms
trust mode
key-provider type
security profile
```

This is useful for auditing and reproducibility.

---

# 186. AI-Readable Metadata

Compiler artifacts may expose:

```text
crypto:
    sha256
    aes_gcm
tls:
    enabled
    provider = platform
trust:
    system
keys:
    hardware_backed
```

without exposing secrets.

---

# 187. FFI Metadata

External providers declare:

```text
blocking
threading
memory
key ownership
ABI version
```

and are validated during integration.

---

# 188. Security Boundary Verification

Linker/deployment validation checks:

```text
requested crypto capability
requested key capability
requested network capability
provider availability
algorithm policy
```

---

# 189. Runtime Provider Verification

At startup:

```text
provider selected
 ↓
provider capabilities validated
 ↓
security profile validated
 ↓
runtime enabled
```

If required capabilities are unavailable, startup fails explicitly.

---

# 190. Provider Substitution

A deployment may substitute:

```text
NativeProvider
```

with:

```text
PlatformProvider
```

without recompiling application code if ABI/provider compatibility permits.

---

# 191. Provider Pinning

Security-sensitive deployments may pin the provider identity/version.

This becomes part of deployment policy.

---

# 192. Provider Update

Provider updates should not silently change security semantics.

A provider version change may invalidate cached cryptographic artifacts or trigger deployment validation.

---

# 193. Secure Cache

Cryptographic caches may include:

```text
certificate validation results
TLS session tickets
OCSP results
```

All caches are bounded and policy controlled.

---

# 194. Cache Privacy

Cache entries may contain sensitive metadata.

They must be protected according to the applicable security policy.

---

# 195. Session Ticket Persistence

Persistent TLS tickets are optional.

If persisted, they are treated as secrets.

---

# 196. Certificate Cache

Certificate parsing may be cached by fingerprint.

The cache contains public certificate data and remains bounded.

---

# 197. Revocation Cache

Revocation information has explicit expiry.

Stale results cannot silently become permanent trust decisions.

---

# 198. Trust Decision Cache

A cached trust decision must include the policy fingerprint and validation time context needed to determine whether reuse remains valid.

---

# 199. Security Events

Events include:

```text
crypto.provider.loaded
crypto.provider.failed
key.created
key.destroyed
certificate.validation.failed
certificate.validation.succeeded
tls.handshake.started
tls.handshake.completed
tls.handshake.failed
tls.policy.rejected
```

No secrets.

---

# 200. Audit Events

Security-sensitive operations can be audited:

```text
key access
key generation
key deletion
certificate replacement
trust-policy change
provider change
```

---

# 201. Resource Metrics

The runtime exposes:

```text
active_tls_sessions
handshakes
handshake_failures
crypto_cpu_time
key_objects
secure_memory_bytes
certificate_cache_entries
```

---

# 202. Error Model

Base:

```text
CryptoError
```

categories:

```text
RandomUnavailable
InvalidKey
InvalidNonce
AuthenticationFailed
SignatureInvalid
UnsupportedAlgorithm
AlgorithmNotAllowed
ProviderUnavailable
ProviderFailure
KeyUnavailable
KeyNotExportable
CertificateInvalid
CertificateExpired
CertificateUntrusted
HostnameMismatch
RevocationFailure
TlsHandshakeFailed
TlsProtocolError
TlsPolicyViolation
```

---

# 203. Error Composition

HTTPS errors preserve:

```text
HTTP
 ← TLS
 ← Crypto
 ← Key/Certificate
 ← Network
```

without flattening the causal chain.

---

# 204. Error Redaction

Error formatting must remove sensitive provider diagnostics automatically.

---

# 205. Constant-Time Equality

The runtime exposes:

```text
constant_time_equal()
```

and provider-level equivalent operations.

---

# 206. Secure Erase

```text
SecureBuffer.clear()
```

attempts explicit zeroization before release.

---

# 207. Move Semantics

Secret-bearing values should be movable without implicit duplication where practical.

Compiler/runtime metadata may mark:

```text
@secret
```

to discourage accidental copies.

---

# 208. Serialization

Private keys and secret-bearing objects do not implement generic serialization by default.

Explicit export APIs are required.

---

# 209. Logging

The crypto layer must never call generic:

```text
to_string()
```

on secret-bearing objects.

---

# 210. Debug Formatting

Default output:

```text
PrivateKey(<redacted>)
Secret(<redacted>)
```

---

# 211. Testing Secret Erasure

Tests verify that:

- secret buffers are cleared where promised
- copies are minimized
- logs contain no secret values
- crash diagnostics redact sensitive objects

---

# 212. Provider Test Matrix

Each provider must test:

```text
correctness
concurrency
error handling
resource exhaustion
cancellation
provider shutdown
key lifetime
```

---

# 213. Cryptographic Known-Answer Tests

All native algorithm implementations must be validated against independently generated known-answer vectors.

---

# 214. Differential Testing

Where multiple providers exist:

```text
NativeProvider
PlatformProvider
TestProvider
```

can be compared against identical test vectors.

---

# 215. Fuzzing

Mandatory fuzz targets:

```text
certificate parser
ASN.1 parser
key parser
TLS handshake parser
TLS record parser
algorithm parameter parser
```

---

# 216. State-Machine Fuzzing

TLS state machines should be fuzzed with:

```text
unexpected messages
truncated records
reordered events
timeouts
disconnects
invalid certificates
```

---

# 217. Fault Injection

Test providers can simulate:

```text
random unavailable
hardware unavailable
key deleted
certificate expired
trust store failure
TLS alert
provider crash/failure
```

---

# 218. Concurrency Tests

Test:

```text
parallel TLS handshakes
parallel certificate validation
key-store access
provider shutdown
session cache access
```

---

# 219. Resource Tests

Verify bounded behavior under:

```text
thousands of certificate chains
many handshakes
large certificate chains
KDF pressure
key-store exhaustion
```

---

# 220. Security Regression Tests

Every discovered security issue should become a deterministic regression test.

---

# 221. Performance Targets

Target:

```text
near-native crypto throughput
minimal allocations
hardware acceleration when available
asynchronous TLS
bounded handshake memory
low per-connection overhead
```

---

# 222. TLS Handshake Performance

A TLS handshake must not create an unnecessary OS thread.

---

# 223. Crypto Allocation

Common operations should reuse provider contexts where safe.

---

# 224. Certificate Parsing Performance

Certificate parsing should avoid repeated conversion between:

```text
DER
temporary object
DER
```

and use immutable views where safe.

---

# 225. Key Store Performance

Persistent key lookup should use opaque indexed IDs rather than scanning every key.

---

# 226. Hardware Provider Performance

Hardware-backed operations may be slower than software operations.

The provider exposes capability/latency metadata without changing semantic behavior.

---

# 227. Secure Memory Performance

Secure memory is used only where necessary.

Ordinary public data should not be forced through secure-memory allocation.

---

# 228. Minimal Binary Profile

An application using only:

```text
SecureRandom
SHA-256
```

must not link:

```text
TLS
HTTP
certificate validation
key store
```

---

# 229. TLS Client Binary Profile

An HTTPS client links only the required:

```text
TCP
DNS
TLS
certificate
crypto
HTTP
```

modules.

---

# 230. TLS Server Binary Profile

A TLS server links:

```text
TCP
TLS
certificate
key provider
crypto
```

plus its application protocol.

---

# 231. Embedded Profile

Embedded builds may omit:

```text
certificate revocation
system trust store
HTTP
hardware abstraction
```

when not needed.

---

# 232. WASM Profile

WASM may provide:

```text
hash
AEAD
signature
KDF
```

locally while delegating:

```text
hardware key
network TLS
```

to the host.

---

# 233. Mobile Profile

Mobile builds prefer platform secure storage and hardware-backed identities where available.

---

# 234. Desktop Profile

Desktop builds may select:

```text
platform provider
native provider
```

according to deployment requirements.

---

# 235. Server Profile

Server builds emphasize:

```text
high handshake concurrency
connection reuse
session resumption
hardware key providers
resource quotas
```

---

# 236. Configuration Example

Conceptual:

```text
security.crypto {
    provider = "platform"
    secure_random = "os"
}

security.tls {
    provider = "platform"
    trust = "system"
    verify_hostname = true
}

security.keys {
    provider = "platform"
    private_keys = "non_exportable"
}
```

---

# 237. Policy Example

Conceptual:

```text
tls_policy {
    allow_modern_protocols = true
    allow_legacy = false
    require_hostname_verification = true
    require_trusted_chain = true
}
```

The actual configuration grammar remains owned by BOOTSTRAP-601.

---

# 238. Deployment Manifest

Compiled deployment metadata may contain:

```text
crypto_provider
tls_provider
trust_store
required_algorithms
required_key_capabilities
```

---

# 239. Capability Manifest

Example:

```text
capabilities:
    network.connect
    crypto.use
    key.use(server_identity)
```

---

# 240. No Hidden Privilege

Selecting a TLS provider must not automatically grant unrelated:

```text
filesystem
process
device
network.listen
```

authority.

---

# 241. TLS Certificate Files

If certificates are loaded from files, access requires filesystem capability.

A better deployment may reference a platform key store instead.

---

# 242. Private Key Files

Private key files require:

```text
filesystem.read
```

plus:

```text
key.import
```

policy.

---

# 243. Key Store Isolation

The application cannot access another service's private keys merely because both run under the same user identity.

The key store provider must enforce namespace/policy isolation.

---

# 244. Process Isolation

High-security key operations may run in a separate process:

```text
Application
 ↓ IPC
Key Service
 ↓
Hardware
```

This composes with BOOTSTRAP-604/605.

---

# 245. Remote HSM

A remote HSM provider may exist above the key-provider boundary.

It must explicitly declare:

```text
network dependency
latency
availability
credential requirements
```

---

# 246. HSM Failure

If an HSM becomes unavailable:

```text
KeyUnavailable
```

is returned.

The application decides whether to failover.

---

# 247. Key Failover

Multiple providers can be configured:

```text
primary
secondary
```

but automatic failover must respect key identity and security policy.

---

# 248. Certificate Rotation With HSM

The server can rotate certificates while retaining hardware-backed private keys.

---

# 249. Trust Policy Rotation

Trust roots can be rotated using:

```text
old + new
 ↓
new
```

with overlap.

---

# 250. Root Removal

Removing a trust root affects new validations.

Existing TLS sessions are not automatically invalidated unless deployment policy requires it.

---

# 251. Revocation Emergency

Deployment policy may force termination of connections associated with a revoked identity.

Such behavior is explicitly configured.

---

# 252. TLS Session Termination

A session may terminate because of:

```text
peer close
policy revocation
certificate policy change
transport failure
protocol alert
service shutdown
```

The reason is preserved.

---

# 253. Application Notification

The application receives a structured terminal event rather than a generic EOF alone when the distinction matters.

---

# 254. TLS Stream Safety

TLS stream implements the `ByteStream` contract from BOOTSTRAP-609.

It must preserve:

```text
partial reads
partial writes
EOF
cancellation
deadline
backpressure
```

---

# 255. Secure Transport Composition

The final abstraction remains:

```text
ByteStream
```

allowing protocols to operate over:

```text
TCP
TLS
Proxy
```

without knowing provider details.

---

# 256. HTTP/2 Compatibility

HTTP/2 uses:

```text
TLS provider
ALPN
ByteStream
```

without needing direct crypto access.

---

# 257. QUIC Compatibility

Future QUIC can use crypto primitives from BOOTSTRAP-610 while maintaining its own transport implementation.

This is important because QUIC encryption is not equivalent to simply placing TLS over TCP.

---

# 258. Future Protocol Compatibility

The cryptographic layer is deliberately reusable by:

```text
QUIC
VPN
custom secure protocols
secure IPC
device protocols
```

where policy permits.

---

# 259. IPC Security

BOOTSTRAP-604 may use cryptographic primitives for authenticated/encrypted IPC.

The same:

```text
CryptoProvider
KeyProvider
TrustStore
```

interfaces are reusable.

---

# 260. Secure IPC

Possible architecture:

```text
IPC
 ↓
authenticated channel
 ↓
AEAD
 ↓
shared key / key exchange
```

without coupling IPC to TLS.

---

# 261. Application Cryptography

Applications can use the crypto API directly for legitimate cryptographic operations.

However, higher-level protocol libraries should be preferred over constructing security protocols manually.

---

# 262. Algorithm API Design

Application code should write:

```text
AeadCipher.open(AeadAlgorithm.AesGcm)
```

rather than manually managing implementation-specific contexts.

---

# 263. Algorithm Policy

Security policy can prohibit specific algorithms globally for a deployment.

---

# 264. Policy Enforcement

Algorithm requests pass through:

```text
requested algorithm
 ↓
provider capability
 ↓
security policy
 ↓
resource policy
 ↓
operation
```

---

# 265. Provider Capability Cache

Provider capability discovery can be cached in immutable runtime metadata.

---

# 266. No Global Mutable Crypto State

The runtime avoids mutable process-wide:

```text
current provider
current trust store
current key
```

objects.

---

# 267. Explicit Context

Crypto operations receive explicit:

```text
Provider
Policy
Key
Clock
Random
```

references as appropriate.

---

# 268. Runtime Context

For convenience, application-level contexts may group these:

```text
SecurityContext
```

but the context remains an explicit object, not hidden global state.

---

# 269. SecurityContext

Conceptually:

```text
SecurityContext {
    crypto_provider
    key_provider
    trust_store
    policy
}
```

---

# 270. Service-Specific Security Context

Each service may own a distinct security context.

This prevents one service from accidentally sharing trust/key state with another.

---

# 271. Tenant Isolation

Multi-tenant services can use separate:

```text
SecurityContext
KeyNamespace
TrustStore
TlsPolicy
```

---

# 272. Context Fingerprint

A security context produces:

```text
SecurityContextFingerprint
```

for diagnostics and reproducibility.

---

# 273. Security Context Lifetime

Security contexts should outlive their sessions but remain explicitly shutdown during service termination.

---

# 274. Compiler Integration

The compiler recognizes security metadata:

```text
@secret
@key_usage
@requires_crypto
@requires_key
```

---

# 275. IR Operations

Possible IR operations:

```text
crypto.hash
crypto.mac
crypto.aead.encrypt
crypto.aead.decrypt
crypto.sign
crypto.verify
crypto.random
crypto.kdf
crypto.key.generate
crypto.key.use
tls.handshake
tls.read
tls.write
```

---

# 276. Linker Optimization

If only:

```text
crypto.hash
```

is used, the linker removes TLS and key-store infrastructure.

---

# 277. Static Security Analysis

Compiler diagnostics may detect obvious mistakes:

```text
secret → string conversion
private key → generic serialization
TLS without hostname verification in secure profile
```

These are compile-time warnings/errors where statically knowable.

---

# 278. Unsafe Boundary

Low-level cryptographic implementations may require:

```text
unsafe
```

but calling a normal cryptographic API does not.

---

# 279. No Language-Level Crypto Syntax

Axiom does not add special keywords for:

```text
AES
TLS
RSA
certificate
```

These belong to standard library/runtime APIs.

---

# 280. Struct-Only Design

Public APIs follow Axiom's struct-only object model.

Example:

```text
struct TlsClient {
    provider: TlsProvider
}

async fn TlsClient.connect(...)
```

No mandatory classes are introduced.

---

# 281. Override/Provider Model

Provider specialization uses traits/interfaces:

```text
trait CryptoProvider
trait KeyProvider
trait TlsProvider
```

Implementations can override behavior through trait conformance rather than class inheritance.

---

# 282. Error Trait Model

Crypto errors implement the common Axiom error abstraction.

No exception-based control flow is required.

---

# 283. No Hidden Allocation

Small hashes, signatures, key IDs and algorithm descriptors should use stack/inline storage where practical.

---

# 284. Large Operations

Large certificate chains, secure buffers and TLS contexts use bounded heap/pool allocation.

---

# 285. Resource Accounting

Every large allocation is charged to the current resource scope.

---

# 286. Shutdown Ordering

Crypto shutdown occurs after:

```text
TLS sessions closed
network sessions closed
application protocols stopped
```

but before:

```text
process runtime teardown
```

---

# 287. Provider Shutdown

Providers must finish/cancel outstanding operations before unloading.

---

# 288. Dynamic Provider Unloading

A provider cannot be unloaded while:

```text
KeyHandle
TlsSession
CryptoContext
```

still references it.

---

# 289. Generation-Safe Provider Handles

Provider handles use generation IDs to prevent stale references after reload.

---

# 290. Security Event Ordering

Security events preserve causal ordering:

```text
key.created
certificate.loaded
tls.handshake
tls.established
tls.closed
key.retired
```

---

# 291. Audit Integrity

Where required, audit records may be chained using cryptographic hashes.

The audit subsystem itself belongs to BOOTSTRAP-602/603.

---

# 292. Tamper-Evident Audit

Optional:

```text
AuditChain
```

can hash consecutive records.

This is an audit feature, not a replacement for secure logging/storage.

---

# 293. Privacy

Certificate metadata may be sensitive in some deployments.

Policies can redact:

```text
subject
issuer
hostnames
peer identity
```

from diagnostics.

---

# 294. Network Privacy

TLS diagnostics should not record plaintext request bodies.

---

# 295. Secure Defaults Summary

Default secure profile:

```text
secure random
modern TLS
hostname verification
system/application trust
bounded certificate parsing
non-exportable hardware keys where available
no secret logging
bounded handshakes
explicit capabilities
```

---

# 296. Testing Matrix

Minimum matrix:

```text
native provider × platform
platform provider × platform
TLS client × server
TLS server × external client
certificate valid/invalid
key export/non-export
hardware/software key
IPv4/IPv6
HTTP/1.1
HTTP/2 when enabled
WASM
mobile
```

---

# 297. Acceptance Criterion A01

Secure random uses a platform CSPRNG.

# 298. Acceptance Criterion A02

No insecure PRNG fallback occurs.

# 299. Acceptance Criterion A03

Hashing supports streaming.

# 300. Acceptance Criterion A04

MAC verification uses appropriate constant-time comparison.

# 301. Acceptance Criterion A05

AEAD rejects modified ciphertext.

# 302. Acceptance Criterion A06

Nonce misuse is explicitly controlled.

# 303. Acceptance Criterion A07

Private keys are strongly typed.

# 304. Acceptance Criterion A08

Hardware-backed keys remain opaque.

# 305. Acceptance Criterion A09

Key usage restrictions are enforced.

# 306. Acceptance Criterion A10

Secret-bearing objects cannot be implicitly formatted.

# 307. Acceptance Criterion A11

Secure buffers support explicit clearing.

# 308. Acceptance Criterion A12

Certificate parsing is bounded.

# 309. Acceptance Criterion A13

Certificate-chain validation is separate from parsing.

# 310. Acceptance Criterion A14

Trust stores are explicit objects.

# 311. Acceptance Criterion A15

Hostname verification is independently enforced.

# 312. Acceptance Criterion A16

TLS provider is replaceable.

# 313. Acceptance Criterion A17

TLS handshake is asynchronous.

# 314. Acceptance Criterion A18

TLS supports cancellation.

# 315. Acceptance Criterion A19

TLS supports deadlines.

# 316. Acceptance Criterion A20

TLS supports ALPN.

# 317. Acceptance Criterion A21

TLS supports SNI.

# 318. Acceptance Criterion A22

TLS policy prevents prohibited protocol versions.

# 319. Acceptance Criterion A23

TLS cannot silently downgrade to a prohibited algorithm.

# 320. Acceptance Criterion A24

TLS session resumption is provider-controlled.

# 321. Acceptance Criterion A25

TLS 0-RTT is explicitly policy-controlled.

# 322. Acceptance Criterion A26

Client certificate authentication is supported.

# 323. Acceptance Criterion A27

Server certificate selection supports SNI.

# 324. Acceptance Criterion A28

Private key operations can remain inside hardware.

# 325. Acceptance Criterion A29

Key rotation can occur without restarting the process.

# 326. Acceptance Criterion A30

Trust-store rotation affects new validations predictably.

# 327. Acceptance Criterion A31

Crypto operations integrate with resource budgets.

# 328. Acceptance Criterion A32

Handshake resource limits are enforced.

# 329. Acceptance Criterion A33

Certificate chains have bounded depth/size.

# 330. Acceptance Criterion A34

Crypto failures preserve structured causes.

# 331. Acceptance Criterion A35

Secret material is excluded from diagnostics.

# 332. Acceptance Criterion A36

Provider capabilities are discoverable.

# 333. Acceptance Criterion A37

Provider version is auditable.

# 334. Acceptance Criterion A38

External providers declare threading/ownership behavior.

# 335. Acceptance Criterion A39

Blocking providers use the blocking executor.

# 336. Acceptance Criterion A40

WASM can use host-provided crypto/key services.

# 337. Acceptance Criterion A41

Mobile platforms can use platform secure key stores.

# 338. Acceptance Criterion A42

Embedded builds can select a reduced crypto profile.

# 339. Acceptance Criterion A43

Unused algorithms are dead-strippable.

# 340. Acceptance Criterion A44

TLS is reusable by HTTP/2 and future QUIC layers.

# 341. Acceptance Criterion A45

Crypto APIs follow the struct-only Axiom object model.

# 342. Acceptance Criterion A46

Provider implementations are fuzzable.

# 343. Acceptance Criterion A47

Certificate parsers are fuzzable.

# 344. Acceptance Criterion A48

TLS state machines support deterministic testing.

# 345. Acceptance Criterion A49

Known-answer crypto vectors are mandatory.

# 346. Acceptance Criterion A50

Provider differential testing is supported.

# 347. Acceptance Criterion A51

Fault injection is supported.

# 348. Acceptance Criterion A52

Key-store failures are recoverable as explicit errors.

# 349. Acceptance Criterion A53

Hardware-provider failure does not silently expose private keys.

# 350. Acceptance Criterion A54

Security policy fingerprints are deterministic.

# 351. Acceptance Criterion A55

Compiler metadata records cryptographic requirements.

# 352. Acceptance Criterion A56

Linker metadata records provider/algorithm requirements.

# 353. Acceptance Criterion A57

Network capability and crypto capability remain separate.

# 354. Acceptance Criterion A58

Existing TLS sessions are not unpredictably mutated by configuration reload.

# 355. Acceptance Criterion A59

TLS shutdown integrates with BOOTSTRAP-605.

# 356. Acceptance Criterion A60

No garbage collector is required.

# 357. Acceptance Criterion A61

No specific third-party crypto library is mandatory.

# 358. Acceptance Criterion A62

No secret is automatically serialized into checkpoints.

# 359. Acceptance Criterion A63

Crypto providers can be statically linked or dynamically provided.

# 360. Acceptance Criterion A64

Provider unloading is generation/lifetime safe.

# 361. Acceptance Criterion A65

The architecture supports future cryptographic algorithms without changing the application-level key API.

---

# 362. Final Architecture

```text
                         APPLICATION
                              │
                    ┌─────────┴─────────┐
                    │                   │
                HTTP/WebSocket       Crypto API
                    │                   │
                    ▼                   ▼
                 TLS Layer        CryptoProvider
                    │                   │
                    │             ┌─────┼─────┐
                    │             │     │     │
                    │            Hash   AEAD  Sign
                    │             │     │     │
                    │             └─────┼─────┘
                    │                   │
                    ▼                   ▼
               KeyProvider         SecureRandom
                    │                   │
             ┌──────┼──────┐            │
             │      │      │            │
          Software  OS    Hardware      │
             │      │      │            │
             └──────┼──────┘            │
                    │                   │
                    ▼                   ▼
              Secure Storage       OS / Hardware
                    │
                    ▼
              Certificate /
               Trust Store
                    │
                    ▼
              Trust Decision
                    │
                    ▼
                 TLS Session
                    │
                    ▼
                TCP Stream
                    │
                    ▼
              Network Runtime
                    │
                    ▼
              Async Executor
```

---

# 363. Full Axiom Runtime Stack

After BOOTSTRAP-610:

```text
600  State / Persistence / Recovery
601  Configuration / Secrets / Deployment
602  Logging / Diagnostics / Crash Reporting
603  Security / Capabilities / Permissions
604  IPC / Shared Memory / Message Transport
605  Process / Service Supervision / Watchdog
606  Resource Governor / Budgets / Quotas
607  Scheduler / Threads / Async Runtime
608  Synchronization / Atomics / Memory Semantics
609  Networking / Sockets / DNS / Network Transport
610  Cryptography / TLS / Certificates / Keys
```

The dependency direction remains:

```text
higher-level application protocols
              ↓
             TLS
              ↓
        crypto / trust
              ↓
          networking
              ↓
      scheduler/sync
              ↓
        security/resources
              ↓
       native platform
```

---

# 364. Architectural Decision Summary

BOOTSTRAP-610 establishes six important Axiom principles.

### 1. Cryptography is a first-class runtime service

It is not an application-specific collection of FFI calls.

### 2. TLS is provider-based

Axiom can use native, platform, hardware or external implementations without changing application APIs.

### 3. Keys are objects, not byte arrays

Private-key material is opaque by default.

### 4. Trust is explicit

Trust stores, validation policy and hostname verification are explicit inputs.

### 5. Hardware security is composable

TPM, Secure Enclave, Android Keystore and HSM-like providers fit into the same architecture.

### 6. Security does not destroy performance

Unused algorithms/providers are dead-stripped, cryptographic acceleration is allowed, and asynchronous TLS integrates directly with Axiom's executor.

---

# 365. BOOTSTRAP-610 Completion

**BOOTSTRAP-610 is COMPLETE.**

Axiom now has a complete secure-transport foundation:

```text
SecureRandom
    ↓
Cryptographic Primitives
    ↓
Key Management
    ↓
Certificate / Trust
    ↓
TLS Provider
    ↓
TLS Session
    ↓
Network Transport
```

while retaining:

```text
no mandatory GC
no mandatory third-party crypto library
no global mutable security state
explicit capabilities
explicit resource limits
native async execution
hardware-backed key support
dead-strippable implementation
```

---

# 366. Next Architecture Task

**BOOTSTRAP-611 — Native Storage, Filesystem, Virtual Filesystem, File I/O, Memory Mapping, Storage Transactions & Durable Data Runtime 5.0**

This is the next major missing native subsystem because Axiom now has:

```text
Memory
Execution
Synchronization
IPC
Process lifecycle
Resources
Networking
Cryptography
```

but does not yet have the equally fundamental **persistent storage/I/O layer** required for a complete native application runtime.

BOOTSTRAP-611 should define the filesystem/storage model from the OS boundary upward, including asynchronous file I/O, file handles, directories, atomic rename, memory mapping, durable writes, file locking, virtual filesystems, storage quotas, sandboxed paths, capability-controlled filesystem access, crash-safe persistence, and integration with BOOTSTRAP-600/601/603/606/607/608.
:::

**BOOTSTRAP-610 hoàn tất.** Chuỗi kiến trúc tiếp tục tự động sang **BOOTSTRAP-611 — Native Storage & Filesystem Runtime 5.0**.