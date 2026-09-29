Tiếp tục đúng chuỗi. Task kế tiếp là **BOOTSTRAP-603**.

:::writing{variant="document" id="74163" title="BOOTSTRAP-603 — NATIVE APPLICATION SECURITY, IDENTITY, CAPABILITY & TRUST RUNTIME 5.0"}

# BOOTSTRAP-603 — NATIVE APPLICATION SECURITY, IDENTITY, CAPABILITY & TRUST RUNTIME 5.0

**Status:** Architecture Specification  
**Layer:** Bootstrap / Native Runtime  
**Depends on:** BOOTSTRAP-600, BOOTSTRAP-601, BOOTSTRAP-602  
**Target:** Windows, Linux, macOS, iOS, Android, WASM  
**Primary goals:** explicit authority, least privilege, secure identity, capability-based access, secret-safe execution, native isolation, deterministic security boundaries, zero mandatory third-party security runtime.

---

# 603.0 — Purpose

BOOTSTRAP-603 defines the foundational security model of Axiom applications.

The subsystem governs:

1. application identity;
2. execution identity;
3. capabilities;
4. resource permissions;
5. trust boundaries;
6. privilege boundaries;
7. secure handles;
8. cryptographic primitives;
9. secure randomness;
10. credential isolation;
11. process and module trust;
12. sandbox integration;
13. permission requests;
14. authorization decisions;
15. security auditing;
16. secure IPC boundaries;
17. platform security adapters;
18. secure failure behavior.

The design must avoid turning Axiom into a complicated security framework.

The fundamental rule is:

> **Code should possess authority explicitly rather than receiving unlimited authority implicitly.**

---

# 603.1 — Security Principles

Axiom security follows:

```text
least privilege
explicit authority
deny by default
capability-oriented access
immutable identity
bounded resources
secure failure
auditable decisions
platform integration
no mandatory cloud
```

---

# 603.2 — No Implicit Universal Authority

An ordinary Axiom application must not automatically receive unrestricted access to:

- filesystem;
- network;
- processes;
- devices;
- credentials;
- environment;
- system configuration.

Access must come from the platform or an explicitly declared capability.

---

# 603.3 — Capability Model

The primary abstraction is:

```axiom
Capability<T>
```

A capability represents authority to perform a specific class of operation.

Example:

```axiom
Capability<FileSystem>
Capability<Network>
Capability<Camera>
Capability<Process>
```

Possessing the capability is the authorization.

---

# 603.4 — Capability Is Not a String

This is forbidden as the primary authorization mechanism:

```axiom
if permissions.contains("filesystem.write") {
    ...
}
```

Instead:

```axiom
fn save(file: FileWriteCapability, data: Bytes)
```

The type system carries authority.

---

# 603.5 — Capability Non-Forgery

Application code must not be able to construct an arbitrary privileged capability.

For example:

```axiom
Capability<FileSystem>()
```

is invalid unless the compiler/runtime provides a legitimate authority source.

---

# 603.6 — Capability Origin

A capability originates from:

```text
platform
application manifest
parent capability
user authorization
secure subsystem
trusted bootstrap
```

---

# 603.7 — Capability Attenuation

A capability may be restricted.

Example:

```axiom
let full = filesystem
let images = full.subtree("/images")
```

The resulting capability has no authority outside `/images`.

---

# 603.8 — Capability Monotonicity

Deriving a child capability must never increase authority.

```text
child.authority ⊆ parent.authority
```

This is a core invariant.

---

# 603.9 — Capability Revocation

Capabilities may be revocable.

```axiom
capability.revoke()
```

A revoked capability must fail future operations.

Already completed operations are not retroactively undone.

---

# 603.10 — Capability Lifetime

Capabilities are ordinary native values with explicit lifetime.

They do not require garbage collection.

---

# 603.11 — Capability Transfer

A capability can be transferred between trusted execution contexts if the API explicitly allows it.

Example:

```axiom
worker.send(capability)
```

The sender may optionally relinquish its authority.

---

# 603.12 — Capability Duplication

Duplication policy depends on capability type.

Some capabilities may be:

```text
copyable
shareable
move-only
non-transferable
```

---

# 603.13 — Move-Only Security Capabilities

Highly privileged capabilities should support move semantics:

```axiom
let cap2 = move cap1
```

After transfer:

```text
cap1 = invalid
cap2 = valid
```

---

# 603.14 — Capability Scope

Capabilities may be scoped to:

```text
application
process
thread
task
session
resource
operation
```

---

# 603.15 — Resource Capability

A resource capability may represent:

```text
file
directory
socket
device
process
memory region
IPC endpoint
credential
cryptographic key
```

---

# 603.16 — File Capability

Example:

```axiom
FileReadCapability
FileWriteCapability
DirectoryCapability
```

Read and write authority are separate.

---

# 603.17 — Path Authority

A file capability should preferably contain a canonicalized authority boundary rather than repeatedly trusting arbitrary path strings.

---

# 603.18 — Path Traversal Protection

A capability restricted to:

```text
/app/data
```

must not permit:

```text
/app/data/../secrets
```

to escape its authority.

Canonicalization occurs before authorization.

---

# 603.19 — Symlink / Reparse Boundaries

Platform-specific path mechanisms such as:

- symbolic links;
- junctions;
- reparse points;

must not silently bypass a capability boundary.

The runtime adapter must define secure resolution semantics.

---

# 603.20 — File Operation API

Preferred:

```axiom
file = fs.open(capability, relative_path)
```

rather than:

```axiom
file = open("/arbitrary/path")
```

for sandboxed applications.

---

# 603.21 — Network Capability

Network authority is explicit.

Possible forms:

```axiom
NetworkConnectCapability
NetworkListenCapability
NetworkDnsCapability
```

---

# 603.22 — Network Attenuation

A network capability may be restricted by:

```text
protocol
host
port
address family
direction
```

Example:

```axiom
let api = network.connect_to("api.example.com", 443)
```

---

# 603.23 — DNS Authority

DNS access may be separated from raw socket authority.

This permits tighter sandboxing.

---

# 603.24 — Process Capability

Process authority includes:

```text
spawn
inspect
signal
terminate
debug
```

These are separate capabilities.

---

# 603.25 — Process Spawning

Axiom should not expose unrestricted shell execution as the normal process API.

Preferred:

```axiom
process.spawn(
    executable,
    arguments,
    capability
)
```

---

# 603.26 — Shell Independence

The runtime must not require:

```text
cmd.exe
powershell
/bin/sh
/bin/bash
```

to launch ordinary processes.

---

# 603.27 — Argument Safety

Process arguments are passed as structured argument arrays.

The runtime must not concatenate them into a shell command string.

---

# 603.28 — Environment Inheritance

Environment inheritance must be explicit.

Example:

```axiom
process.spawn(
    env = environment.minimal()
)
```

---

# 603.29 — Credential Capability

Credentials are represented as opaque values.

Example:

```axiom
Credential<T>
```

They must not automatically convert to:

```text
String
Bytes
DiagnosticValue
```

---

# 603.30 — Secret Integration

BOOTSTRAP-601 `Secret<T>` remains the configuration/secret representation.

BOOTSTRAP-603 defines runtime authority for using the secret.

---

# 603.31 — Secret Access

A secret should be accessed through a restricted operation:

```axiom
secret.with_value(|value| {
    use(value)
})
```

This allows future implementations to minimize exposure.

---

# 603.32 — Secret Memory

Sensitive memory may require:

```text
non-swappable memory
zeroization
restricted copying
```

when supported by the platform and appropriate for the secret class.

---

# 603.33 — Zeroization

API:

```axiom
secure.zeroize(buffer)
```

The compiler must prevent optimization from removing a required security wipe.

---

# 603.34 — Secret Copying

The runtime should discourage unnecessary copies of secret data.

The type system may mark sensitive values as:

```text
move-only
non-copyable
```

---

# 603.35 — Cryptographic Boundary

Axiom provides cryptographic primitives as native runtime facilities.

However, application-level protocols must not be silently invented by the runtime.

---

# 603.36 — Cryptographic API Categories

Core categories:

```text
hash
MAC
KDF
AEAD
signature
key generation
randomness
constant-time comparison
```

---

# 603.37 — Hash API

Example:

```axiom
hash.sha256(data)
```

The API returns a fixed-size digest type.

---

# 603.38 — Typed Digest

Example:

```axiom
Digest<sha256>
```

rather than a generic untyped byte array.

---

# 603.39 — MAC

Example:

```axiom
mac.hmac_sha256(key, data)
```

Keys remain opaque.

---

# 603.40 — KDF

Supported conceptual interface:

```axiom
kdf.derive(
    key,
    salt,
    context,
    output_length
)
```

---

# 603.41 — AEAD

Authenticated encryption provides:

```axiom
aead.encrypt(key, nonce, plaintext, associated_data)
aead.decrypt(key, nonce, ciphertext, associated_data)
```

Decryption failure must not expose partially authenticated plaintext.

---

# 603.42 — Nonce Handling

Nonce rules must be explicit.

The runtime must provide safe nonce generation where the algorithm requires uniqueness/randomness.

---

# 603.43 — Signature API

Example:

```axiom
signature.sign(private_key, data)
signature.verify(public_key, data, signature)
```

---

# 603.44 — Key Types

Keys must be strongly typed:

```axiom
PrivateKey<Algorithm>
PublicKey<Algorithm>
SymmetricKey<Algorithm>
```

---

# 603.45 — Algorithm Agility

The API must identify algorithms explicitly.

Avoid:

```axiom
encrypt(data)
```

where the algorithm is hidden.

Prefer:

```axiom
aead.encrypt(.AES256_GCM, ...)
```

or an equivalent typed key API.

---

# 603.46 — Cryptographic Primitive Policy

The runtime must distinguish:

```text
available algorithm
approved algorithm
legacy algorithm
insecure algorithm
```

Applications should receive explicit diagnostics when using deprecated primitives.

---

# 603.47 — Secure Randomness

API:

```axiom
random.secure(bytes)
```

must use the platform's cryptographically secure random source.

---

# 603.48 — General Randomness

A separate API:

```axiom
random.fast()
```

may exist for simulation and non-security workloads.

It must not be advertised as cryptographically secure.

---

# 603.49 — Random Type Separation

Security-sensitive APIs should reject ordinary pseudo-random generators where secure randomness is required.

---

# 603.50 — Constant-Time Comparison

API:

```axiom
secure.equals(a, b)
```

provides comparison suitable for sensitive byte sequences.

---

# 603.51 — Timing Resistance

The runtime should avoid obvious early-exit behavior for cryptographic comparisons.

The exact guarantees are platform/compiler dependent and must be documented.

---

# 603.52 — Key Lifecycle

Keys have explicit states:

```text
generated
active
suspended
revoked
destroyed
```

---

# 603.53 — Key Destruction

Destroying a key must invalidate its capability and, where possible, clear sensitive memory.

---

# 603.54 — Hardware-Backed Keys

The architecture supports opaque references to platform key stores.

Examples:

```text
TPM
Secure Enclave
Android Keystore
platform credential store
```

The core runtime must not assume any particular hardware exists.

---

# 603.55 — Hardware Key Abstraction

```axiom
HardwareKey<Algorithm>
```

can expose permitted cryptographic operations without exposing raw key material.

---

# 603.56 — Trust Identity

An application has:

```axiom
AppIdentity
```

containing:

```text
application_id
publisher_id
build_id
platform_identity
```

---

# 603.57 — Application ID

The application ID is stable across builds of the same logical application.

---

# 603.58 — Build ID

The build ID identifies a particular executable build.

This integrates with BOOTSTRAP-602 diagnostics.

---

# 603.59 — Publisher Identity

A publisher identity identifies the signing authority or development authority associated with an application.

---

# 603.60 — Signing Identity

A signed build may contain:

```text
publisher
certificate/key identity
signature metadata
build identity
```

The runtime can expose this information without requiring a network lookup.

---

# 603.61 — Code Signing

Axiom toolchains should support platform-native code-signing formats.

The compiler itself does not need to implement every external signing service.

---

# 603.62 — Signature Verification

API:

```axiom
trust.verify_signature(binary, public_key)
```

returns a structured result.

---

# 603.63 — Trust Result

```axiom
enum TrustStatus {
    trusted
    untrusted
    invalid
    unknown
}
```

These are descriptive security states, not political or subjective judgments.

---

# 603.64 — Trust Chain

A verification result may include:

```text
root
intermediate
leaf
artifact
```

and failure reason.

---

# 603.65 — No Automatic Trust of Local Files

A local executable is not automatically trusted merely because it exists on disk.

---

# 603.66 — Module Identity

Each native module may expose:

```text
ModuleId
BuildId
PublisherId
SignatureStatus
```

---

# 603.67 — Dynamic Library Loading

Dynamic loading requires an explicit capability in restricted environments.

---

# 603.68 — Library Trust Policy

An application may require:

```axiom
loader.require_publisher(PublisherId)
```

or:

```axiom
loader.require_signature(...)
```

before loading a module.

---

# 603.69 — Dependency Verification

A deployment manifest may specify expected:

```text
module ID
version
hash
publisher
```

---

# 603.70 — Dependency Mismatch

A mismatch should produce a structured security error.

The runtime must not silently substitute an unrelated module.

---

# 603.71 — Hash Verification

Example:

```axiom
module.require_hash(expected)
```

This protects against unexpected binary replacement.

---

# 603.72 — TOCTOU Protection

Security-sensitive resource access must minimize:

```text
check
    ↓
resource changes
    ↓
use
```

windows.

Where platform APIs support atomic secure operations, the runtime should use them.

---

# 603.73 — Secure Handle

Axiom uses opaque handles for privileged native resources:

```axiom
Handle<T>
```

The numeric native handle is not directly exposed by default.

---

# 603.74 — Handle Ownership

Handles have explicit ownership:

```text
owned
borrowed
shared
invalid
```

This should integrate with Axiom's broader resource/lifetime model without introducing a mandatory borrow checker.

---

# 603.75 — Handle Closing

Example:

```axiom
with fs.open(cap, "data.bin") as file {
    ...
}
```

leaves scope and closes the handle deterministically.

---

# 603.76 — No GC Requirement

Security-sensitive resource cleanup must not depend on garbage collection.

---

# 603.77 — Double Close

Closing an owned resource twice is invalid.

Debug builds should detect it.

Release behavior should be deterministic and safe.

---

# 603.78 — Capability Tokens

Internally, capabilities may be represented using:

```text
opaque pointer
native handle
index
kernel token
sealed structure
```

The representation is platform-specific.

---

# 603.79 — Capability Forgery Resistance

The representation must make accidental or ordinary application-level forgery impractical.

---

# 603.80 — Memory Safety Boundary

The security runtime does not replace Axiom's memory model.

Instead it defines privileged-resource boundaries independent of whether the application uses:

- stack values;
- owned values;
- flat memory;
- native handles;
- shared memory.

---

# 603.81 — Unsafe Code

Axiom may provide:

```axiom
unsafe { ... }
```

for low-level operations.

Unsafe code does not automatically gain all capabilities.

---

# 603.82 — Unsafe ≠ Privileged

This distinction is mandatory:

```text
unsafe
    ≠
authorized
```

Unsafe code can violate memory/type invariants within its authority, but cannot manufacture platform permissions.

---

# 603.83 — Capability Boundaries and FFI

An FFI call inherits only the capabilities explicitly passed to it.

Calling native code does not grant universal Axiom authority.

---

# 603.84 — Native ABI Boundary

FFI interfaces should declare security requirements.

Example:

```axiom
extern fn camera_capture(
    camera: CameraCapability
)
```

---

# 603.85 — IPC Capability

IPC endpoints are represented as:

```axiom
IpcCapability<T>
```

---

# 603.86 — IPC Authentication

An IPC endpoint may authenticate the peer using:

```text
process identity
application identity
publisher identity
session identity
cryptographic identity
platform identity
```

---

# 603.87 — IPC Authorization

Authentication answers:

```text
Who are you?
```

Authorization answers:

```text
What are you allowed to do?
```

Axiom must keep these concepts separate.

---

# 603.88 — Peer Identity

```axiom
struct PeerIdentity {
    app_id
    publisher_id
    process_id
    session_id
}
```

Fields vary by platform.

---

# 603.89 — Secure IPC Handshake

A secure channel may establish:

```text
peer identity
channel identity
capabilities
session key
```

---

# 603.90 — Capability Passing over IPC

A trusted process may explicitly transfer authority through IPC.

The receiver receives only the transferred capability.

---

# 603.91 — Capability Revocation over IPC

Revocation must propagate to transferred capabilities where the platform supports centralized capability tracking.

---

# 603.92 — Sandboxing

Axiom applications may declare a sandbox profile.

Example:

```text
filesystem.read
network.connect
camera
microphone
gpu
process.spawn
```

---

# 603.93 — Manifest Integration

BOOTSTRAP-601 deployment manifests may declare required capabilities.

Example:

```text
capabilities:
    filesystem:
        read: app_data
    network:
        connect: api.example.com:443
```

---

# 603.94 — Manifest vs Runtime

Manifest declaration expresses:

```text
what the application requests
```

Runtime capability expresses:

```text
what the application actually possesses
```

They are distinct.

---

# 603.95 — Capability Denial

If a requested capability is denied:

```axiom
CapabilityError.denied
```

is returned.

---

# 603.96 — No Silent Escalation

The runtime must never automatically retry a denied capability using a more privileged mechanism.

---

# 603.97 — User Permission

Interactive permissions may involve the user or operating system.

The runtime exposes the result:

```axiom
permission.request(camera)
```

without deciding whether the user should grant it.

---

# 603.98 — Permission State

```axiom
enum PermissionState {
    granted
    denied
    restricted
    unavailable
    unknown
}
```

---

# 603.99 — Permission Revocation

Applications must handle permissions disappearing after they were previously granted.

---

# 603.100 — Permission Cache

The runtime may cache permission state briefly but must not assume permanent authorization.

---

# 603.101 — Secure Defaults

Default policy:

```text
no capability
```

unless explicitly granted by platform/runtime.

---

# 603.102 — Development Mode

Development builds may request broader capabilities, but development mode must not silently weaken production security.

---

# 603.103 — Debugger Capability

Debugging another process is a privileged capability.

It must be separate from ordinary process inspection.

---

# 603.104 — Memory Inspection

Reading another process's memory requires explicit authorization.

The runtime must not provide unrestricted memory inspection as a normal API.

---

# 603.105 — Code Injection

Dynamic code injection is not a normal Axiom capability.

If a platform/debugging environment supports it, it belongs to explicitly privileged tooling.

---

# 603.106 — Dynamic Code Loading

Runtime-generated executable code must be controlled by the execution/security layer.

A normal application cannot silently convert arbitrary writable memory into executable code.

---

# 603.107 — W^X

Where the platform supports it, executable memory should follow:

```text
write OR execute
```

rather than:

```text
write AND execute
```

simultaneously.

---

# 603.108 — JIT Capability

JIT execution is a separate capability:

```axiom
Capability<JitExecution>
```

This is especially relevant for:

- scripting;
- dynamic compilation;
- GPU kernels;
- runtime code generation.

---

# 603.109 — Executable Memory

The runtime should expose controlled allocation:

```axiom
exec_memory.allocate(capability, size)
```

with explicit permission transitions.

---

# 603.110 — Memory Protection

Memory regions may transition:

```text
read/write
read-only
read/execute
```

according to platform constraints.

---

# 603.111 — Guard Pages

Security-sensitive native allocations may use guard pages where practical.

---

# 603.112 — Stack Protection

The toolchain should support platform stack-protection mechanisms where appropriate.

---

# 603.113 — Integer Overflow Policy

The security runtime does not redefine Axiom arithmetic semantics.

However, security-sensitive code should have explicit checked arithmetic APIs.

Example:

```axiom
checked.add(a, b)
```

---

# 603.114 — Bounds Validation

Native APIs must validate:

```text
length
offset
count
alignment
handle state
```

before unsafe operations.

---

# 603.115 — Integer-to-Size Conversion

Conversions into native allocation/index sizes must provide checked forms.

---

# 603.116 — Serialization Security

Binary deserialization must enforce:

```text
maximum size
maximum depth
maximum collection count
maximum string size
```

---

# 603.117 — No Arbitrary Deserialization Code

Deserializing external data must not execute arbitrary constructors or methods.

---

# 603.118 — Parser Isolation

Security-sensitive parsers should operate with bounded resource budgets.

---

# 603.119 — Resource Exhaustion

Capabilities may include quotas:

```text
max file size
max network bytes
max processes
max memory
max CPU
max IPC messages
```

---

# 603.120 — Quota Model

```axiom
CapabilityQuota {
    bytes
    operations
    duration
    concurrency
}
```

---

# 603.121 — Quota Enforcement

A quota violation returns:

```axiom
SecurityError.quota_exceeded
```

rather than silently truncating a security-sensitive operation.

---

# 603.122 — Rate-Limited Capabilities

Capabilities may enforce operation rates.

Example:

```text
100 requests/minute
```

---

# 603.123 — Audit Events

Security-sensitive decisions should integrate with BOOTSTRAP-602:

```text
security.capability.granted
security.capability.denied
security.permission.changed
security.signature.invalid
security.module.rejected
security.credential.access
```

---

# 603.124 — Audit Privacy

Audit events must not expose:

- passwords;
- private keys;
- raw access tokens;
- secret configuration values.

---

# 603.125 — Audit Integrity

High-security deployments may require tamper-evident audit records.

This can use chained hashes:

```text
H(event_n || H(event_n-1))
```

---

# 603.126 — Audit Storage

Audit logs remain separate from ordinary application logs.

This prevents normal log rotation from accidentally destroying security records.

---

# 603.127 — Security Event Severity

Security events use ordinary BOOTSTRAP-602 severity levels but may additionally carry a security classification.

---

# 603.128 — Security Classification

Example:

```axiom
enum SecurityEventClass {
    authentication
    authorization
    capability
    integrity
    credential
    sandbox
    cryptography
}
```

---

# 603.129 — Authentication API

The core runtime provides primitives for authenticating identities but does not mandate a universal account system.

---

# 603.130 — Identity Provider

An application may integrate:

```axiom
IdentityProvider
```

which returns an opaque identity.

---

# 603.131 — Identity Object

```axiom
Identity {
    id
    issuer
    attributes
}
```

Attributes must be explicitly typed and bounded.

---

# 603.132 — Authentication Result

```axiom
enum AuthenticationResult {
    authenticated
    rejected
    unavailable
    expired
    invalid
}
```

---

# 603.133 — Authorization

Authorization is capability-based by default.

Role-based or attribute-based systems may be implemented above the primitive capability layer.

---

# 603.134 — Role Mapping

An application may map:

```text
identity
    ↓
role
    ↓
capability set
```

but the runtime should ultimately enforce concrete capabilities.

---

# 603.135 — Session Identity

BOOTSTRAP-600 session state may expose:

```axiom
SessionIdentity
```

for diagnostics and authorization.

---

# 603.136 — Session Separation

Authentication credentials and session state must not be conflated.

---

# 603.137 — Token Handling

Tokens should be represented as opaque types:

```axiom
AccessToken
RefreshToken
SessionToken
```

rather than generic strings.

---

# 603.138 — Token Logging

Token types are automatically protected from BOOTSTRAP-602 logging.

---

# 603.139 — Token Equality

Security-sensitive token comparison uses constant-time comparison where applicable.

---

# 603.140 — Expiration

Security credentials may expose:

```axiom
expires_at()
```

without exposing secret contents.

---

# 603.141 — Clock Security

Expiration checks should account for clock manipulation where the platform provides monotonic or trusted time sources.

---

# 603.142 — Trust Store

The runtime may provide access to platform trust stores through:

```axiom
TrustStore
```

without exposing platform-specific internals.

---

# 603.143 — Certificate Object

Certificates are parsed into typed structures.

Malformed certificates return structured errors.

---

# 603.144 — Certificate Validation

Validation may check:

```text
signature
chain
validity period
key usage
hostname
policy
revocation status
```

depending on the requested operation.

---

# 603.145 — Hostname Validation

TLS-like network clients must not treat certificate-chain validity alone as hostname authorization.

---

# 603.146 — TLS Boundary

Axiom may provide secure network transports.

The application API should make certificate and hostname validation the normal behavior.

---

# 603.147 — Plaintext Transport

Plaintext networking remains possible for explicitly non-sensitive protocols.

Security-sensitive APIs should not silently downgrade to plaintext.

---

# 603.148 — Downgrade Protection

A secure connection should not automatically downgrade after:

```text
certificate failure
authentication failure
protocol mismatch
```

without an explicit application policy.

---

# 603.149 — Cryptographic Failure

Cryptographic verification failure must return a failure result.

It must not be converted into a warning and continued silently.

---

# 603.150 — Secure Error Messages

Errors should explain enough for debugging without revealing secrets.

Example:

```text
authentication failed
```

rather than:

```text
password hash for user X was ...
```

---

# 603.151 — Error Redaction

Security errors are automatically safe for BOOTSTRAP-602 diagnostic serialization.

---

# 603.152 — Panic Safety

A security failure must not cause a panic merely because the capability was denied.

---

# 603.153 — Privilege Boundary

Privilege escalation is represented explicitly:

```axiom
security.request_privilege(...)
```

The runtime cannot silently elevate.

---

# 603.154 — Privileged Helper

Some platforms may require a privileged helper process.

The helper must have:

```text
minimal capability set
authenticated IPC
explicit protocol
bounded input
```

---

# 603.155 — Helper Authentication

The main process must authenticate the helper before sending sensitive operations.

---

# 603.156 — Helper Authorization

The helper must authenticate the requesting application before accepting privileged operations.

---

# 603.157 — Confused Deputy Prevention

A privileged helper must not blindly perform arbitrary operations requested by any client.

Every request must be authorized against the caller's identity and granted capability.

---

# 603.158 — Capability Delegation

A process may delegate a restricted capability:

```text
parent
  ↓
child
```

but delegation cannot exceed the parent's authority.

---

# 603.159 — Child Process Security

When spawning a child process, the parent may specify:

```text
capabilities
environment
filesystem
network
handles
working directory
resource quotas
```

---

# 603.160 — Default Child Authority

A child process receives no additional authority merely because the parent possesses it.

---

# 603.161 — Capability Inheritance

Inheritance must be explicit.

Example:

```axiom
spawn(..., inherit = [.stdin, .stdout])
```

---

# 603.162 — Handle Inheritance

Native handle inheritance is disabled by default where platform semantics allow.

---

# 603.163 — Temporary Capabilities

Some capabilities may have expiration:

```axiom
capability.until(deadline)
```

---

# 603.164 — Time-Bounded Authority

After expiration:

```text
operation → denied
```

---

# 603.165 — One-Shot Capabilities

Some authority can be consumed once:

```axiom
OneShotCapability<T>
```

Useful for:

- secure handoff;
- installation tokens;
- one-time secrets.

---

# 603.166 — Capability Audit Identity

Every capability may have an opaque identifier for diagnostics:

```text
CapabilityId
```

This identifier does not expose the capability's secret material.

---

# 603.167 — Security Context

The runtime maintains a security context:

```axiom
SecurityContext {
    app_identity
    session_identity
    capabilities
    trust
}
```

---

# 603.168 — Context Propagation

Async tasks inherit only the security context explicitly configured for them.

---

# 603.169 — Context Isolation

A child task may receive a reduced security context.

---

# 603.170 — No Ambient Privilege Leakage

A task created from a privileged context must not accidentally become globally privileged.

---

# 603.171 — Thread Context

Thread-local storage may cache security context, but the authoritative capability state remains explicit and revocable.

---

# 603.172 — FFI Security Review Boundary

Any API declared:

```axiom
extern
```

should identify whether it:

```text
reads files
opens network
executes code
accesses devices
uses credentials
```

where this can be represented statically.

---

# 603.173 — Native Module Manifest

Native modules may declare:

```text
required_capabilities
provided_capabilities
security_level
publisher
```

---

# 603.174 — Module Loading Policy

The application may require:

```text
signed module
approved publisher
expected hash
expected ABI
expected version
```

before loading.

---

# 603.175 — ABI Trust

ABI compatibility is distinct from security trust.

A compatible module is not automatically a trusted module.

---

# 603.176 — Secure Update

The architecture supports signed application updates.

Update process:

```text
download
   ↓
verify signature
   ↓
verify identity
   ↓
verify compatibility
   ↓
stage
   ↓
activate
```

---

# 603.177 — Atomic Update

Where platform support exists, activation should be atomic.

A failed update must leave the previous known-good installation intact.

---

# 603.178 — Rollback

The deployment layer may maintain:

```text
current
previous
candidate
```

versions.

Security metadata must accompany each version.

---

# 603.179 — Update Trust

A newer version must not automatically be trusted merely because it is newer.

The signing/trust policy must still pass.

---

# 603.180 — Secure Bootstrap

At startup:

```text
platform
   ↓
executable identity
   ↓
signature/trust policy
   ↓
runtime initialization
   ↓
capability establishment
   ↓
application
```

---

# 603.181 — Bootstrap Failure

If mandatory integrity verification fails:

```text
application startup = denied
```

rather than continuing in a partially trusted state.

---

# 603.182 — Diagnostic Integration

BOOTSTRAP-602 records:

```text
build ID
publisher ID
module identity
capability denials
trust failures
security events
```

but never raw secrets.

---

# 603.183 — Crash Integration

BOOTSTRAP-602 crash artifacts may contain:

```text
security context identifier
trust status
active capability class
```

but not capability secrets.

---

# 603.184 — Configuration Integration

BOOTSTRAP-601 declares requested capabilities.

BOOTSTRAP-603 determines actual authority.

---

# 603.185 — State Integration

BOOTSTRAP-600 may persist:

```text
permission state
security migration state
session identity references
```

but sensitive credentials remain in the secure credential subsystem.

---

# 603.186 — Credential Persistence

Long-lived credentials should not be stored in ordinary BOOTSTRAP-600 application state.

They belong to:

```text
secure storage
platform credential store
hardware-backed storage
```

where available.

---

# 603.187 — Secure Storage API

```axiom
secure_store.put(key, secret)
secure_store.get(key)
secure_store.delete(key)
```

The storage provider may be platform-native.

---

# 603.188 — Secure Storage Provider

Possible providers:

```text
Windows credential facilities
macOS Keychain
iOS Keychain/Secure Enclave
Android Keystore
Linux secure store
Axiom native encrypted store
```

The API remains platform-neutral.

---

# 603.189 — Software Fallback

Where no hardware secure store exists, the runtime may use software encryption.

It must clearly distinguish:

```text
hardware-backed
OS-backed
software-protected
```

storage.

---

# 603.190 — Master Key

The runtime must not hard-code a universal master key.

Keys derive from platform/user/application-specific secure sources.

---

# 603.191 — Key Rotation

Secure storage supports versioned keys where practical.

---

# 603.192 — Credential Deletion

Deleting a credential should invalidate its application reference.

Best-effort physical erasure depends on the underlying storage technology.

---

# 603.193 — Security Events

Recommended event IDs:

```text
SEC_CAPABILITY_DENIED
SEC_CAPABILITY_REVOKED
SEC_PERMISSION_CHANGED
SEC_SIGNATURE_INVALID
SEC_MODULE_REJECTED
SEC_AUTH_FAILED
SEC_CREDENTIAL_ACCESS
SEC_TRUST_FAILED
SEC_SANDBOX_VIOLATION
SEC_QUOTA_EXCEEDED
```

---

# 603.194 — Security Event Redaction

Security event payloads must pass through the same secret-protection layer as ordinary diagnostics.

---

# 603.195 — Security Metrics

Optional counters:

```text
authorization_denied
authentication_failed
module_rejected
capability_revoked
sandbox_denied
credential_failures
```

---

# 603.196 — Security Health

```axiom
SecurityHealth {
    trust_status
    sandbox_status
    secure_storage_status
    crypto_status
}
```

---

# 603.197 — Security Self-Test

Optional:

```axiom
security.self_test()
```

may verify:

- secure random source;
- cryptographic backend;
- secure storage;
- capability subsystem;
- trust metadata.

It must not expose secrets.

---

# 603.198 — Failure Isolation

If optional security telemetry fails:

```text
security enforcement continues
```

Diagnostics must not weaken authorization merely because logging is unavailable.

---

# 603.199 — Fail-Closed Operations

For security-critical authorization:

```text
unknown
```

must normally behave as:

```text
deny
```

unless an explicitly documented policy says otherwise.

---

# 603.200 — Fail-Open Exceptions

Fail-open behavior must be explicitly declared and limited to operations where security consequences are acceptable.

It must never be an accidental default.

---

# 603.201 — Security Policy

Applications may define:

```axiom
SecurityPolicy {
    required_signer
    allowed_modules
    allowed_capabilities
    crypto_policy
    credential_policy
}
```

---

# 603.202 — Policy Immutability

Once a security-critical policy is active, ordinary application code cannot silently weaken it.

---

# 603.203 — Policy Layers

Policy precedence:

```text
platform
    ↓
deployment
    ↓
application
    ↓
resource
    ↓
operation
```

A lower layer may restrict authority but must not bypass a higher-level denial.

---

# 603.204 — Security Policy Compilation

Static policy should be compiled into compact native structures where possible.

---

# 603.205 — Policy Runtime Cost

A capability authorization check should target:

```text
O(1)
```

for ordinary capability operations.

---

# 603.206 — Security Metadata

A release executable may contain:

```text
application identity
publisher identity
requested capabilities
module requirements
security policy hash
```

---

# 603.207 — Policy Fingerprint

The active security policy may expose:

```axiom
security.policy_fingerprint()
```

This integrates with BOOTSTRAP-602 diagnostics.

---

# 603.208 — Security Context Fingerprint

A diagnostic snapshot may contain:

```text
security policy fingerprint
trust status
capability profile
```

without exposing individual secret values.

---

# 603.209 — AI-Friendly Security Metadata

The toolchain should emit machine-readable metadata describing:

```text
capability requirements
resource boundaries
trust requirements
module dependencies
security policy
```

This allows automated tooling to understand why an operation was denied.

---

# 603.210 — Security Manifest

A deployment manifest should support:

```text
security:
    capabilities:
    trusted_publishers:
    trusted_modules:
    crypto_policy:
    sandbox:
    secure_storage:
```

---

# 603.211 — Capability Diff

Tooling should be able to compare two builds:

```text
build A capabilities
        vs
build B capabilities
```

and identify added/removed requested authority.

---

# 603.212 — `ax security`

The toolchain should provide:

```text
ax security inspect
ax security manifest
ax security verify
ax security capabilities
ax security modules
```

---

# 603.213 — `ax security capabilities`

Outputs:

```text
requested
granted
denied
inherited
delegated
revoked
```

---

# 603.214 — `ax security verify`

Checks:

```text
binary signature
module signatures
build identity
manifest
policy
dependency integrity
```

---

# 603.215 — Static Capability Analysis

The compiler may determine:

```text
function → required capability
```

when capability requirements are explicit.

Example:

```text
save_document()
    requires FileWrite
```

---

# 603.216 — Capability Propagation

If:

```axiom
fn save(cap: FileWriteCapability)
```

calls:

```axiom
write_file(cap)
```

the compiler can propagate the requirement.

---

# 603.217 — Capability Requirement Graph

The compiler may generate:

```text
function
   ↓
required capability
   ↓
module
   ↓
application manifest
```

---

# 603.218 — Dead Capability Elimination

If a capability-dependent subsystem is unused, associated runtime code should be removable.

---

# 603.219 — Security Footprint

The toolchain should report:

```text
filesystem access
network access
process access
device access
credential access
JIT access
```

for an executable.

---

# 603.220 — Security Footprint Does Not Equal Runtime Permission

Static analysis describes potential authority.

The runtime determines actual granted authority.

---

# 603.221 — Sandboxed Build

A build may intentionally restrict its static capability surface.

The compiler can reject APIs requiring capabilities outside the declared profile.

---

# 603.222 — Capability Injection

At application startup:

```axiom
fn main(
    fs: FileSystemCapability,
    net: NetworkCapability
)
```

may receive capabilities explicitly.

This makes dependencies visible in the application entry point.

---

# 603.223 — Dependency Injection Without Framework

No dependency-injection framework is required.

Capabilities are ordinary typed parameters.

---

# 603.224 — Testing

Tests may inject mock capabilities:

```axiom
FakeFileSystemCapability
```

provided they implement the required restricted interface.

---

# 603.225 — Test Isolation

Tests should default to:

```text
no network
no real credentials
temporary filesystem
no process spawning
```

unless explicitly enabled.

---

# 603.226 — Security Test Capability

The test runtime may expose synthetic capabilities that cannot affect the real system.

---

# 603.227 — Fuzzing

Security-sensitive parsers and capability boundaries should be fuzz-testable without requiring real privileged resources.

---

# 603.228 — Deterministic Security Tests

Where practical, permission decisions should be testable deterministically.

---

# 603.229 — Security Error Taxonomy

Core errors:

```axiom
SecurityError {
    denied
    unavailable
    expired
    revoked
    invalid_identity
    invalid_signature
    trust_failure
    quota_exceeded
    sandbox_violation
    credential_unavailable
    policy_violation
}
```

---

# 603.230 — Error Codes

Security errors have stable numeric IDs for diagnostics and IPC.

---

# 603.231 — ABI Stability

Security error and capability ABI structures require explicit versioning.

---

# 603.232 — Platform Adapter Contract

Each platform adapter implements:

```text
identity
permissions
sandbox
secure storage
crypto
randomness
process authority
filesystem authority
network authority
code trust
```

where supported.

---

# 603.233 — Windows Adapter

Integrates with:

- process identity;
- ACL/security descriptors;
- code signing;
- credential facilities;
- protected storage where available;
- native process/token mechanisms.

---

# 603.234 — Linux Adapter

Integrates with:

- file permissions;
- user/group identity;
- namespaces where available;
- sandboxing mechanisms;
- kernel credential boundaries;
- native secure random source.

---

# 603.235 — macOS Adapter

Integrates with:

- code signing;
- entitlements;
- sandbox;
- Keychain;
- application identity;
- platform permission mechanisms.

---

# 603.236 — iOS Adapter

The architecture respects:

- application sandbox;
- entitlements;
- Keychain;
- Secure Enclave where available;
- platform permission dialogs;
- code-signing restrictions.

---

# 603.237 — Android Adapter

Integrates with:

- application identity;
- permissions;
- sandbox UID;
- Keystore;
- package signing;
- platform security policy.

---

# 603.238 — WASM Adapter

WASM authority is determined by the host.

Axiom capabilities map to host-provided imports/interfaces.

No capability is assumed merely because the WASM module exists.

---

# 603.239 — Cross-Platform Semantic Rule

The same Axiom API should preserve this invariant:

```text
operation succeeds
    only if
required capability is valid
AND
platform policy permits it
```

---

# 603.240 — Platform Differences

The runtime may expose capability state as:

```text
supported
unsupported
restricted
granted
denied
```

instead of pretending every platform provides identical security features.

---

# 603.241 — No False Security

The runtime must not label software-only protection as hardware-backed protection.

---

# 603.242 — Security Claims

Axiom documentation must distinguish:

```text
language guarantee
runtime guarantee
platform guarantee
configuration guarantee
best effort
```

---

# 603.243 — Memory Security

Security-sensitive memory APIs should provide:

```text
guarded allocation
zeroization
restricted access
optional locking
```

where supported.

---

# 603.244 — Secure Allocator

A secure allocator may exist:

```axiom
secure.alloc<T>(count)
```

It is intended for sensitive data, not ordinary application allocations.

---

# 603.245 — Secure Allocator Constraints

Secure allocation may be:

- slower;
- non-movable;
- non-swappable;
- quota-limited.

The application must opt in.

---

# 603.246 — No Universal Secure Memory Promise

The runtime cannot guarantee physical memory secrecy against a fully privileged operating system/kernel.

Documentation must state the trust boundary.

---

# 603.247 — Trust Boundary

Default trust model:

```text
Application
   ↓ trusts
Axiom runtime
   ↓ trusts
Operating system
   ↓ trusts
Hardware
```

Platform security can alter this boundary.

---

# 603.248 — Hostile Application Code

The capability model assumes application components may be mutually untrusted.

This enables future plugin/sandbox architectures.

---

# 603.249 — Plugin Capability Boundary

A plugin receives:

```text
only explicitly granted capabilities
```

not the application's entire authority.

---

# 603.250 — Plugin Manifest

Plugins may declare:

```text
required capabilities
publisher
version
hash
ABI
```

---

# 603.251 — Plugin Approval

The host application determines whether the plugin is acceptable.

The runtime enforces the granted capability boundary.

---

# 603.252 — Plugin Revocation

A plugin capability can be revoked without necessarily terminating the entire application.

---

# 603.253 — Untrusted Data

External data is treated as:

```text
data
```

not:

```text
trusted code
```

until explicitly validated.

---

# 603.254 — Trust Conversion

Converting external data into privileged objects requires validation.

---

# 603.255 — Input Validation

The runtime provides primitives for:

```text
range checking
length checking
encoding validation
schema validation
signature validation
```

---

# 603.256 — UTF-8 Security

Axiom's UTF-8 default must not imply that arbitrary byte sequences are valid text.

The runtime distinguishes:

```text
Bytes
String
```

---

# 603.257 — Invalid UTF-8

Converting bytes to String requires explicit validation or a defined lossy conversion.

---

# 603.258 — Unicode Normalization

Security-sensitive identifiers may optionally require normalization.

The runtime must not silently normalize arbitrary user data.

---

# 603.259 — Case Sensitivity

Security-sensitive resource names must respect platform-specific case semantics.

The runtime should expose canonical comparison rules.

---

# 603.260 — Filename Security

Applications must not assume:

```text
same textual path
=
same resource
```

across platforms.

Capability-bound resource handles remain authoritative.

---

# 603.261 — Environment Security

BOOTSTRAP-601 environment values are untrusted input unless explicitly declared trusted.

---

# 603.262 — Configuration Security

Configuration cannot grant itself capabilities beyond the deployment/platform policy.

---

# 603.263 — CLI Security

Command-line options cannot override mandatory security restrictions.

---

# 603.264 — Debug Configuration

A debug flag cannot disable mandatory signature or sandbox enforcement in production.

---

# 603.265 — Development Escape Hatch

Development-only bypasses must be:

```text
explicit
visible
build-identifiable
non-default
```

---

# 603.266 — Security Banner

Diagnostic metadata may identify:

```text
development security mode
```

when enabled.

---

# 603.267 — Production Build Validation

The build tool should warn or fail when production configuration contains:

```text
debug bypass
trust-all
disable-signature-check
allow-unsigned-module
```

style settings.

---

# 603.268 — Security Policy Hash

The final executable may contain the hash of the security policy actually compiled into the binary.

---

# 603.269 — Policy Mismatch Detection

At startup:

```text
runtime policy
vs
deployment policy
```

must be checked for compatibility.

---

# 603.270 — Immutable Startup Security

Mandatory security decisions should occur before untrusted application initialization.

---

# 603.271 — Early Attack Surface

The bootstrap sequence should minimize:

```text
dynamic loading
network access
configuration parsing
plugin loading
```

before security initialization.

---

# 603.272 — Secure Configuration Parsing

BOOTSTRAP-601 configuration files are untrusted input until validated.

---

# 603.273 — Manifest Validation

The deployment manifest must be:

```text
parsed
schema-checked
policy-checked
integrity-checked where applicable
```

before capabilities are established.

---

# 603.274 — Secure Defaults on Parse Failure

Invalid security configuration results in:

```text
restricted startup
```

rather than permissive fallback.

---

# 603.275 — Capability Startup Graph

Startup:

```text
identity
   ↓
trust verification
   ↓
manifest validation
   ↓
platform permissions
   ↓
capability construction
   ↓
application initialization
```

---

# 603.276 — Capability Shutdown

Shutdown invalidates or releases:

```text
temporary capabilities
session credentials
IPC channels
privileged handles
```

according to their lifecycle.

---

# 603.277 — Session Termination

BOOTSTRAP-600 session termination must invalidate session-scoped capabilities.

---

# 603.278 — User Logout

Where applicable:

```text
logout
  ↓
credential/session invalidation
  ↓
capability revocation
```

---

# 603.279 — Security Event on Revocation

Capability revocation may generate:

```text
security.capability.revoked
```

for diagnostics.

---

# 603.280 — Crash-Time Security Capture

Crash handling may record:

```text
security policy fingerprint
application identity
publisher identity
trust state
```

but must not inspect all capabilities or credentials indiscriminately.

---

# 603.281 — Security and Diagnostics Boundary

BOOTSTRAP-603 owns:

```text
authority
trust
identity
credential protection
```

BOOTSTRAP-602 owns:

```text
recording
diagnostic persistence
crash reporting
```

---

# 603.282 — Security and Configuration Boundary

BOOTSTRAP-601 declares:

```text
desired deployment configuration
```

BOOTSTRAP-603 decides:

```text
security authority actually available
```

---

# 603.283 — Security and State Boundary

BOOTSTRAP-600 owns:

```text
application state
```

BOOTSTRAP-603 owns:

```text
security state
```

Only references to security state should enter ordinary application checkpoints.

---

# 603.284 — Security State

Security state may include:

```text
permission status
capability revocation
trust state
credential references
policy version
```

---

# 603.285 — Credential References

Application state stores:

```text
CredentialId
```

not:

```text
raw credential
```

---

# 603.286 — Restore Safety

Restoring an application checkpoint must not automatically restore expired or revoked capabilities.

---

# 603.287 — Security-Aware Recovery

After crash recovery:

```text
application state restored
        +
security state revalidated
```

before privileged operations resume.

---

# 603.288 — Replay Protection

Security-sensitive operations must not be replayed merely because application state was restored.

---

# 603.289 — Transaction Identity

Security-sensitive transactions may include:

```text
TransactionId
Nonce
SessionId
```

for replay protection.

---

# 603.290 — Secure Monotonic Counter

Platforms supporting secure counters may expose them through:

```axiom
secure.counter()
```

for replay-sensitive applications.

---

# 603.291 — Atomic Security State

Permission/capability changes should be applied atomically from the application's perspective.

---

# 603.292 — Concurrent Revocation

If a capability is revoked concurrently with an operation, the runtime defines whether:

```text
operation already authorized
```

may complete.

The default rule is:

> Revocation prevents subsequent authorization; it does not necessarily cancel an already-authorized kernel operation.

---

# 603.293 — Authorization Race

Security-sensitive operations should use atomic platform primitives where available to reduce authorization races.

---

# 603.294 — Security Invariant

At all times:

```text
effective authority
    ⊆
granted authority
    ⊆
deployment authority
    ⊆
platform authority
```

---

# 603.295 — No Privilege Amplification

No combination of ordinary Axiom APIs may transform:

```text
Capability<A>
```

into:

```text
Capability<UnrelatedPrivilege>
```

without an explicit trusted boundary.

---

# 603.296 — Security Monotonicity

Capability derivation must satisfy:

```text
Authority(child) <= Authority(parent)
```

unless the operation crosses a separately authenticated privilege boundary.

---

# 603.297 — Security Boundary Crossing

Crossing into a privileged subsystem requires:

```text
authentication
authorization
input validation
bounded resource use
audit event
```

where applicable.

---

# 603.298 — No Ambient Root Capability

Axiom does not expose:

```axiom
root_capability()
```

to ordinary application code.

---

# 603.299 — Trusted Runtime Code

Some runtime operations necessarily require elevated native authority.

These are isolated inside trusted runtime components.

---

# 603.300 — Trusted Runtime Surface

The trusted computing base should be kept small.

Optional subsystems should remain outside the mandatory security core.

---

# 603.301 — Compiler Trust

The compiler is part of the build-time trust boundary.

Reproducible builds and signed compiler/toolchain artifacts are outside the mandatory application runtime but supported by the ecosystem.

---

# 603.302 — Runtime Self-Identity

The runtime exposes:

```axiom
runtime.identity()
```

including:

```text
runtime version
ABI
build identity
security feature set
```

---

# 603.303 — Feature Availability

Applications can query:

```axiom
security.features()
```

to determine platform support.

---

# 603.304 — Capability Introspection

Applications may inspect whether a capability is:

```text
valid
revoked
expired
restricted
```

but should not be able to extract privileged internal representation.

---

# 603.305 — Secure Handle Introspection

A `Handle<T>` should expose only safe metadata:

```text
valid
type
state
```

not raw kernel pointers unless explicitly requested through an unsafe API.

---

# 603.306 — Unsafe Native Handle Extraction

If required for FFI:

```axiom
unsafe native_handle(handle)
```

must be explicitly marked unsafe.

---

# 603.307 — Native Handle Lifetime

The developer is responsible for respecting the ownership contract when using extracted handles.

---

# 603.308 — Security and Memory Model

The security architecture must remain compatible with Axiom's high-performance native memory model.

It must not introduce:

- mandatory GC;
- mandatory borrow checker;
- mandatory reference counting;
- hidden heap allocations.

---

# 603.309 — Security and Performance

Security checks should use:

```text
typed capabilities
opaque handles
constant-time primitives where required
bounded authorization checks
```

rather than pervasive dynamic policy interpretation.

---

# 603.310 — Fast Path

After capability validation, hot resource operations may use a compact validated handle.

Example:

```text
Capability
    ↓ validate
NativeHandle
    ↓
fast operation
```

---

# 603.311 — Revocation Tradeoff

Instant revocation may require indirection.

The runtime may choose:

```text
generation counter
capability table
revocation epoch
kernel-backed handle
```

depending on platform.

---

# 603.312 — Generation Counters

A capability handle may encode:

```text
index
generation
```

so stale handles are rejected.

---

# 603.313 — Stale Capability

Using a stale capability returns:

```axiom
SecurityError.revoked
```

rather than accessing a reused resource.

---

# 603.314 — Resource Identity

The runtime should distinguish:

```text
resource identity
handle identity
capability identity
```

---

# 603.315 — Capability Table

A runtime implementation may maintain:

```text
CapabilityTable
```

for resources requiring centralized revocation.

---

# 603.316 — Capability Table Performance

Lookup target:

```text
O(1)
```

average case.

---

# 603.317 — Capability Table Memory

Entries are bounded by configured resource limits.

---

# 603.318 — Resource Exhaustion

Failure to create a capability due to table exhaustion returns:

```axiom
SecurityError.quota_exceeded
```

or an explicit resource-exhaustion error.

---

# 603.319 — Security Telemetry

Security metrics must not become an attack vector.

High-volume security failures must be rate-limited.

---

# 603.320 — Security Event Flood

If an attacker causes thousands of permission failures:

```text
application remains responsive
```

and diagnostic storage remains bounded.

---

# 603.321 — Security Logging Priority

Critical security events may bypass ordinary log filtering while still respecting privacy.

---

# 603.322 — Audit Durability

Applications requiring durable security auditing can configure durable storage explicitly.

Ordinary application logs do not receive this guarantee automatically.

---

# 603.323 — Audit Tamper Evidence

Optional hash chaining:

```text
H0
H1 = H(H0 || E1)
H2 = H(H1 || E2)
...
```

allows detection of modifications.

---

# 603.324 — Audit Key

Tamper-evident audit chains may use a signing key or MAC key stored through secure storage.

---

# 603.325 — Audit Verification

Tool:

```text
ax security audit verify
```

checks chain integrity.

---

# 603.326 — Secure Export

Audit export must preserve:

```text
event identity
timestamp
sequence
integrity metadata
```

---

# 603.327 — No Automatic Remote Upload

Security audit data is never automatically uploaded by the core runtime.

---

# 603.328 — Threat Model

The implementation specification must explicitly document whether it protects against:

```text
untrusted application input
untrusted plugins
untrusted local users
malicious modules
network attackers
compromised dependencies
```

---

# 603.329 — Out of Scope Threats

The core runtime cannot guarantee protection against:

```text
fully compromised operating system
fully compromised kernel
malicious hypervisor
physically compromised hardware
```

unless platform-specific trusted hardware establishes such a boundary.

---

# 603.330 — Threat Model Metadata

Build documentation may contain:

```text
security assumptions
trust boundaries
platform requirements
```

---

# 603.331 — Security Review Artifact

The toolchain may generate:

```text
.axsecurity
```

containing:

```text
capability graph
module trust graph
security policy
resource permissions
crypto usage
```

---

# 603.332 — AI Security Analysis

An AI tool can consume `.axsecurity` to answer:

```text
Which function requires network access?
Which module can access credentials?
Which plugin has filesystem write authority?
Which build gained a new capability?
```

without inspecting every source file.

---

# 603.333 — Security Diff

The tool should support:

```text
ax security diff old.axsecurity new.axsecurity
```

and identify structural changes.

The tool reports facts; it does not assign a security score.

---

# 603.334 — Compiler Diagnostics

Examples:

```text
SEC001 capability required
SEC002 capability unavailable
SEC003 secret passed to diagnostic API
SEC004 unsigned module
SEC005 invalid trust policy
SEC006 insecure random source
SEC007 unsafe credential conversion
SEC008 forbidden privilege escalation
SEC009 invalid capability attenuation
SEC010 security policy mismatch
```

---

# 603.335 — Compile-Time Secret Protection

The compiler should reject obvious flows:

```text
Secret<T>
    ↓
String
    ↓
log()
```

unless explicitly overridden through an unsafe security API.

---

# 603.336 — Static Taint Metadata

The compiler may track:

```text
secret
untrusted
trusted
privileged
```

metadata.

This is optional but strongly supported.

---

# 603.337 — Untrusted Data

External input may be marked:

```axiom
Untrusted<T>
```

and validated into:

```axiom
Trusted<T>
```

when a validator succeeds.

---

# 603.338 — Trusted Conversion

Example:

```axiom
let username = validate_username(input)?
```

returns a restricted validated type.

---

# 603.339 — Taint Propagation

The compiler may propagate security metadata through:

```text
assignment
function parameters
struct fields
serialization
FFI
logging
```

---

# 603.340 — Taint Does Not Replace Authorization

A value being marked `Trusted<T>` does not grant resource capabilities.

---

# 603.341 — Security Metadata Cost

Security metadata should be erased from runtime representations whenever it is compile-time-only.

---

# 603.342 — Zero Runtime Cost Security Types

Where possible:

```text
Trusted<T>
Untrusted<T>
Secret<T>
```

should have the same physical representation as `T`, while enforcing restrictions through the compiler.

---

# 603.343 — Runtime Secret Protection

Runtime protection remains necessary when secrets cross dynamic/native boundaries.

---

# 603.344 — Secure Serialization

Secrets cannot be serialized through generic serializers without an explicit security policy.

---

# 603.345 — Secret Persistence

`Secret<T>` does not imply persistence.

Secure storage is a separate subsystem.

---

# 603.346 — Secure Delete

Secure deletion semantics are platform-dependent.

The API must distinguish:

```text
logical delete
best-effort overwrite
secure-store destruction
```

---

# 603.347 — No False Erasure Guarantee

Axiom must not promise physical deletion on storage systems where the underlying medium cannot provide it.

---

# 603.348 — Capability Serialization

Capabilities generally cannot be serialized directly.

Instead:

```text
capability
    ↓
explicit transferable token
```

may be used.

---

# 603.349 — Capability Token

Transfer tokens must be:

```text
opaque
bounded
expiring where appropriate
single-use where appropriate
```

---

# 603.350 — Token Binding

A transfer token may be bound to:

```text
recipient identity
session
process
resource
expiration
```

---

# 603.351 — Replay Prevention

Single-use security tokens must contain replay-protection state.

---

# 603.352 — Secure IPC Token Exchange

Token exchange:

```text
sender
  ↓ authenticate
receiver
  ↓
verify token
  ↓
construct capability
```

---

# 603.353 — Capability Delegation Graph

The runtime may represent:

```text
root capability
    ↓
attenuated capability
    ↓
delegated capability
```

for audit purposes.

---

# 603.354 — Delegation Constraint

Delegated authority cannot exceed the authority of the delegating capability.

---

# 603.355 — Security Context Snapshot

A diagnostic snapshot may record the identity of the security context but not its secret internal representation.

---

# 603.356 — Security Context Recovery

After process restart, capability objects are recreated from platform authorization rather than blindly restored from serialized memory.

---

# 603.357 — Crash Recovery Security Rule

A restored application checkpoint cannot resurrect:

```text
revoked permission
expired credential
expired capability
invalid trust state
```

---

# 603.358 — Application Update Security

State migration across versions must not automatically transfer obsolete privileged capabilities.

---

# 603.359 — Capability Migration

When an application updates:

```text
old capability model
       ↓
policy reconciliation
       ↓
new capability model
```

---

# 603.360 — Policy Version

Security policy has a version identifier.

---

# 603.361 — Policy Migration

Breaking security-policy changes require explicit migration logic.

---

# 603.362 — Secure Defaults During Migration

If migration fails:

```text
restricted mode
```

rather than unrestricted mode.

---

# 603.363 — Emergency Recovery

Applications may expose a recovery mode with minimal authority:

```text
read diagnostics
repair configuration
restore state
```

but no unnecessary network/process/device authority.

---

# 603.364 — Recovery Capability

Recovery mode receives a deliberately reduced capability set.

---

# 603.365 — Safe Mode

Axiom may provide:

```axiom
application.safe_mode()
```

at the lifecycle layer.

BOOTSTRAP-603 supplies the security profile.

---

# 603.366 — Safe Mode Diagnostics

Safe mode integrates with BOOTSTRAP-602 so that security failures remain diagnosable.

---

# 603.367 — Platform Permission Prompt

Axiom must not bypass platform permission dialogs.

---

# 603.368 — Permission UX

User-facing permission explanations belong to the application/UI layer.

The security runtime exposes machine-readable permission reasons.

---

# 603.369 — Permission Reason

Example:

```axiom
PermissionReason.camera.capture
```

---

# 603.370 — Permission Minimization

The compiler/toolchain should be able to determine which declared capabilities are actually referenced.

---

# 603.371 — Unused Capability Warning

If a manifest requests a capability never used by the executable:

```text
warning: unused capability request
```

---

# 603.372 — Capability Reduction

The deployment tool may generate a minimized manifest containing only required capabilities.

---

# 603.373 — Dynamic Capability Use

Dynamic plugins may prevent complete static capability analysis.

The tool must mark such requirements as dynamic rather than pretending certainty.

---

# 603.374 — Dynamic Loading Warning

Applications using unrestricted dynamic module discovery should receive an explicit security diagnostic.

---

# 603.375 — Security Boundary Documentation

Every native platform adapter must document:

```text
what it guarantees
what it delegates
what it cannot guarantee
```

---

# 603.376 — Cross-Compilation

Security metadata must remain valid when targeting another platform.

---

# 603.377 — Unsupported Capability

When a target lacks a capability:

```text
compile-time error
```

if required statically, or:

```text
unsupported
```

at runtime if dynamically optional.

---

# 603.378 — No Silent Emulation

A capability must not silently degrade into a weaker security mechanism.

---

# 603.379 — Crypto Backend

Axiom may have a native crypto backend selected per target.

The public API remains stable.

---

# 603.380 — Backend Independence

Applications should not depend directly on the internal cryptographic implementation.

---

# 603.381 — Constant-Time Native Primitives

Security-critical primitive implementations should avoid data-dependent branches where algorithmically required.

---

# 603.382 — Side-Channel Documentation

The runtime documentation must state which side-channel protections are guaranteed and which depend on the platform.

---

# 603.383 — Hardware Acceleration

Crypto operations may use:

```text
CPU instructions
hardware security modules
platform crypto APIs
```

without changing the public API.

---

# 603.384 — CPU Feature Detection

The runtime may select accelerated crypto implementations after securely determining CPU features.

---

# 603.385 — No Unsafe Fallback

A hardware-accelerated implementation may fall back to a compatible software implementation, but not to an insecure algorithm merely because acceleration is unavailable.

---

# 603.386 — Entropy Failure

If secure randomness is unavailable:

```text
secure.random()
```

must fail.

It must not silently fall back to predictable randomness.

---

# 603.387 — Secure Time

Security protocols requiring trusted time should use platform facilities where available.

---

# 603.388 — Time-Based Authorization

Expiration checks must define behavior if the system clock moves backward or forward unexpectedly.

---

# 603.389 — Monotonic Expiration

Where practical, short-lived capabilities should use monotonic deadlines.

---

# 603.390 — Security Performance Target

Capability checks should target:

```text
O(1)
```

and minimal allocations.

---

# 603.391 — Cryptographic Performance

The runtime should expose hardware-accelerated implementations where available without changing semantics.

---

# 603.392 — Binary Size

Unused cryptographic algorithms and security providers should be dead-strippable.

---

# 603.393 — Minimal Security Runtime

A minimal native application should be able to include only:

```text
identity
capability core
secure randomness
required platform security
```

without pulling the entire diagnostics/security ecosystem.

---

# 603.394 — No Mandatory GC

Security types must not require garbage collection.

---

# 603.395 — No Mandatory Reference Counting

Security handles use deterministic ownership/lifetime semantics.

Reference counting may be used internally where useful but is not a language requirement.

---

# 603.396 — No Mandatory Borrow Checker

Capability safety is achieved through:

```text
opaque types
ownership
capability construction rules
runtime validation
```

rather than requiring a universal borrow-checking model.

---

# 603.397 — Security and Flat Memory

The security subsystem remains compatible with Axiom's native memory architecture.

Privileged resources remain represented as opaque handles rather than exposing raw security-sensitive memory addresses.

---

# 603.398 — Security and Struct-Oriented Design

Security abstractions use structs/traits rather than mandatory classes.

Example:

```axiom
struct FileCapability {
    handle: Handle<FileAuthority>
}

fn read(cap: FileCapability, path: Path)
```

---

# 603.399 — Override Compatibility

Platform-specific security adapters may override trait implementations without introducing class inheritance.

---

# 603.400 — Security Trait Example

```axiom
trait Capability {
    fn is_valid(self) -> bool
    fn revoke(self)
}
```

Concrete platform types implement the trait.

---

# 603.401 — No Virtual Security Dependency

Performance-sensitive authorization paths should prefer static dispatch.

Dynamic dispatch is permitted where plugin architecture requires it.

---

# 603.402 — Compile-Time Security Graph

The compiler may construct:

```text
module
 ↓
function
 ↓
capability
 ↓
resource
```

graphs.

---

# 603.403 — Runtime Security Graph

The runtime tracks dynamic:

```text
grant
delegation
revocation
expiration
```

relationships where required.

---

# 603.404 — Security Graph Persistence

Only metadata necessary for recovery/audit is persisted.

Raw capability internals are not serialized into ordinary application state.

---

# 603.405 — Acceptance Criteria

BOOTSTRAP-603 is complete when the Axiom implementation demonstrates:

### Capability

- typed capabilities;
- non-forgeable privileged authority;
- attenuation;
- revocation;
- expiration;
- delegation;
- quotas;
- explicit inheritance.

### Identity

- application identity;
- build identity;
- publisher identity;
- module identity;
- peer identity.

### Trust

- signature verification;
- module verification;
- policy enforcement;
- trust-state reporting.

### Secrets

- opaque secret types;
- secure storage;
- zeroization;
- secret-safe diagnostics;
- hardware-backed integration where available.

### Cryptography

- secure random;
- hashes;
- MAC;
- KDF;
- AEAD;
- signatures;
- typed keys;
- constant-time comparison.

### Platform

- Windows;
- Linux;
- macOS;
- iOS;
- Android;
- WASM.

### Isolation

- sandbox integration;
- process capability;
- filesystem capability;
- network capability;
- device capability;
- IPC capability.

### Compiler

- static capability analysis;
- capability metadata;
- security diagnostics;
- capability dead stripping;
- AI-readable security graph.

### Runtime

- O(1)-target authorization;
- no mandatory GC;
- no mandatory borrow checker;
- deterministic resource cleanup;
- bounded security metadata.

---

# 603.406 — Required Compiler/Runtime Components

Logical components:

```text
axiom.security.core
axiom.security.capability
axiom.security.identity
axiom.security.trust
axiom.security.crypto
axiom.security.secrets
axiom.security.storage
axiom.security.ipc
axiom.security.sandbox
axiom.security.audit
```

They need not become separate binaries.

---

# 603.407 — Required Tooling

The Axiom toolchain should provide:

```text
ax security inspect
ax security verify
ax security capabilities
ax security diff
ax security audit
ax security modules
```

---

# 603.408 — Security Artifact

The toolchain should generate:

```text
.axsecurity
```

containing machine-readable:

```text
capability graph
identity
trust requirements
module graph
policy
crypto usage
security boundaries
```

---

# 603.409 — AI-Agent Consumption

An AI coding agent should be able to inspect `.axsecurity` and determine:

```text
why an API requires authority
which module owns that authority
which caller supplied it
whether a capability is static or dynamic
which deployment permission is missing
```

without scanning the complete source tree.

---

# 603.410 — Security Architecture Invariants

The following invariants are mandatory:

```text
1. Authority is explicit.
2. Authority cannot increase through attenuation.
3. Privileged capabilities cannot be forged by ordinary code.
4. Unknown security state fails closed by default.
5. Secrets cannot enter ordinary diagnostics accidentally.
6. Revoked authority cannot be used for new operations.
7. Restored state cannot resurrect revoked authority.
8. Dynamic modules do not automatically become trusted.
9. Secure randomness never silently falls back to predictable randomness.
10. Security failures cannot silently downgrade to insecure behavior.
11. Security enforcement does not depend on diagnostics availability.
12. Security metadata does not require GC.
13. Platform differences remain explicit.
14. The application cannot grant itself platform authority.
15. The runtime does not require a third-party security service.
```

---

# 603.411 — Architectural Result

After BOOTSTRAP-603, the Axiom native runtime has the following security foundation:

```text
                    APPLICATION
                         │
                 ┌───────┴───────┐
                 ▼               ▼
             IDENTITY         STATE 600
                 │
                 ▼
              TRUST
                 │
                 ▼
          CAPABILITY CORE
          ┌──────┼──────┐
          ▼      ▼      ▼
       FILE    NETWORK  IPC
          │      │      │
          └──────┼──────┘
                 ▼
           SECURE HANDLES
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
     CRYPTO    SECRETS   SANDBOX
       │         │         │
       └─────────┼─────────┘
                 ▼
             SECURITY
               AUDIT
                 │
                 ▼
          BOOTSTRAP-602
```

The three preceding bootstrap layers now form a coherent native application foundation:

```text
600 = state / session / recovery
601 = configuration / environment / deployment
602 = diagnostics / crash / observability
603 = identity / authority / trust / security
```

---

# 603.412 — Task Completion

**BOOTSTRAP-603 is complete.**

The specification establishes:

- capability-based security;
- explicit authority;
- capability attenuation;
- capability revocation;
- identity and trust;
- secure handles;
- secure storage;
- secret protection;
- cryptographic primitives;
- secure randomness;
- sandbox integration;
- IPC security;
- module trust;
- code-signing integration;
- privilege separation;
- child-process security;
- secure update foundations;
- static capability analysis;
- AI-readable security metadata;
- platform-specific security adapters;
- deterministic resource ownership;
- compatibility with Axiom's native/high-performance memory model;
- no mandatory GC;
- no mandatory borrow checker;
- no mandatory third-party security runtime.

**Next task: `BOOTSTRAP-604 — NATIVE APPLICATION RESOURCE, MEMORY, CPU, GPU & ENERGY GOVERNANCE RUNTIME 5.0`**
:::