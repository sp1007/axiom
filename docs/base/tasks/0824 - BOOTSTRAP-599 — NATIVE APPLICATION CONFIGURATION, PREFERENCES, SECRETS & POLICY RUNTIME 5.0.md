# BOOTSTRAP-599 — NATIVE APPLICATION CONFIGURATION, PREFERENCES, SECRETS & POLICY RUNTIME 5.0

**Phạm vi:** thiết kế lớp configuration/policy runtime thống nhất cho Axiom, tách rõ **configuration**, **user preferences**, **secrets**, **environment**, **CLI arguments**, **system policy** và **runtime state**.

`597` quản lý dữ liệu ghi được.  
`598` quản lý thay đổi dữ liệu theo phiên bản.  
`599` xác định **giá trị cấu hình hiệu lực của application được hình thành như thế nào**.

---

## 599.1. Mục tiêu kiến trúc

Axiom phải tránh tình trạng application tự đọc:

```text
%APPDATA%
%LOCALAPPDATA%
HOME
XDG_*
Registry
Environment Variables
argv
JSON files
INI files
Credential stores
```

rồi tự quyết định precedence.

Thay vào đó:

```text
External Sources
       ↓
Configuration Providers
       ↓
Schema Validation
       ↓
Precedence Resolver
       ↓
Effective Configuration Snapshot
       ↓
Application
```

---

## 599.2. Architectural Boundary

```text
                         Application
                              │
                              ▼
                    Configuration Runtime
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
         Config Data      Secrets           Policy
              │               │                │
              ▼               ▼                ▼
        User/System       OS Vault        Deployment
        Defaults          Keychain        Enterprise
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                     Config Resolver
                              │
                    Effective Snapshot
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
           Startup          Runtime          Hot Reload
```

---

# 599.3. Configuration không phải một loại dữ liệu duy nhất

Axiom định nghĩa sáu lớp:

```text
Configuration
Preference
Secret
Environment
CommandLine
Policy
```

và một lớp trạng thái riêng:

```text
RuntimeState
```

---

# 599.4. Configuration

Giá trị điều khiển behavior của application.

Ví dụ:

```text
network.timeout = 30s
render.vsync = true
logging.level = "info"
```

---

# 599.5. Preference

Giá trị phản ánh lựa chọn của user:

```text
ui.theme
ui.language
editor.font_size
window.position
```

Preference có thể được lưu persistent.

---

# 599.6. Secret

Thông tin cần bảo vệ:

```text
password
access_token
private_key
credential
encryption_key
```

Secret **không phải configuration bình thường**.

---

# 599.7. Environment

Thông tin do process/OS/deployment cung cấp:

```text
PATH
HOME
TEMP
LANG
deployment-specific variables
```

---

# 599.8. Command-Line

Runtime startup input:

```text
axiom-app --profile release --log-level debug
```

---

# 599.9. Policy

Quy tắc có authority cao hơn application/user preference.

Ví dụ:

```text
network.allowed = false
plugins.allowed = false
telemetry.allowed = false
```

---

# 599.10. RuntimeState

Trạng thái runtime không phải configuration.

Ví dụ:

```text
connected
active_window
worker_count
current_session
```

Không được persist tự động vào configuration.

---

# 599.11. Configuration Source Model

```text
ConfigSource {
    source_id
    kind
    priority
    trust
    mutable
    persistent
}
```

---

# 599.12. Source Kinds

```text
BuiltinDefault
SystemConfig
ApplicationConfig
UserConfig
ProfileConfig
Environment
CommandLine
RemoteConfig
EnterprisePolicy
RuntimeOverride
SecretProvider
```

---

# 599.13. Precedence

Không hard-code precedence trong từng subsystem.

Resolver sử dụng policy:

```text
SourcePriorityPolicy
```

---

# 599.14. Default Precedence

Default policy:

```text
BuiltinDefault
    <
SystemConfig
    <
ApplicationConfig
    <
UserConfig
    <
ProfileConfig
    <
Environment
    <
CommandLine
```

Policy/security constraints có thể nằm ngoài value precedence và **không bị user override**.

---

# 599.15. Policy Boundary

Ví dụ:

```text
User:
    network.enabled = true

EnterprisePolicy:
    network.enabled = false
```

Effective:

```text
network.enabled = false
```

---

# 599.16. Policy không phải Override thông thường

Policy có semantic:

```text
allow
deny
require
limit
```

thay vì chỉ:

```text
value = X
```

---

# 599.17. Policy Types

```text
Allow
Deny
Require
Limit
Pin
Mask
```

---

# 599.18. Typed Configuration

Configuration schema phải có type.

```text
ConfigKey<Bool>
ConfigKey<Int32>
ConfigKey<String>
ConfigKey<Duration>
ConfigKey<Path>
ConfigKey<Enum>
```

---

# 599.19. No Untyped Configuration in Core

Core API không khuyến khích:

```text
get("foo") -> Any
```

thay vào đó:

```text
get(ConfigKey<T>) -> T
```

---

# 599.20. Configuration Key

```text
ConfigKey<T> {
    namespace
    name
    type
    schema_version
    default
    constraints
}
```

---

# 599.21. Key Identity

```text
ConfigKeyID =
    hash(namespace + name + schema_identity)
```

---

# 599.22. Namespace

Ví dụ:

```text
app.network.timeout
app.ui.theme
app.audio.buffer_size
```

Namespace tránh collision giữa subsystem.

---

# 599.23. Schema

Configuration schema:

```text
ConfigSchema {
    schema_id
    version
    keys[]
    constraints[]
}
```

---

# 599.24. Configuration Type System

Configuration được kiểm tra bởi Axiom type system.

Ví dụ:

```text
timeout: Duration
port: UInt16
fullscreen: Bool
```

Không coi `"8080"` tương đương `8080`.

---

# 599.25. Unit-Aware Values

Core nên hỗ trợ typed units cho configuration:

```text
Duration
Bytes
Frequency
Percentage
Pixels
Degrees
```

giảm lỗi do nhầm đơn vị.

---

# 599.26. Range Constraint

```text
port ∈ 1..65535
volume ∈ 0..100
timeout >= 0ms
```

---

# 599.27. Enum Constraint

```text
log.level ∈ {
    trace,
    debug,
    info,
    warn,
    error
}
```

---

# 599.28. String Constraint

Có thể có:

```text
min_length
max_length
pattern
allowed_values
```

---

# 599.29. Path Constraint

Path configuration có thể khai báo:

```text
PathKind {
    File
    Directory
    ExistingFile
    ExistingDirectory
}
```

---

# 599.30. Path Security

Configuration path không được mặc định vượt storage sandbox.

---

# 599.31. Secret Type

Secret có type riêng:

```text
Secret<T>
```

Không implicit convert:

```text
Secret<String> → String
```

---

# 599.32. Secret Exposure

API phải tránh:

```text
print(secret)
log(secret)
serialize(secret)
```

một cách vô tình.

---

# 599.33. Secret Redaction

Formatter/logging mặc định:

```text
password = <redacted>
```

---

# 599.34. Secret Equality

Không nên expose secret comparison qua generic string formatting.

Runtime có thể cung cấp constant-time comparison cho cryptographic secret khi cần.

---

# 599.35. Secret Provider

```text
SecretProvider {
    get(id)
    exists(id)
    metadata(id)
}
```

---

# 599.36. Secret Provider Sources

```text
OSCredentialStore
ApplicationVault
EnvironmentSecret
MemoryOnly
HardwareBackedStore
```

---

# 599.37. OS Credential Boundary

Axiom không tự định nghĩa lại secure storage của từng OS.

Platform adapter ánh xạ tới:

```text
Windows Credential infrastructure
macOS/iOS Keychain
Android Keystore-backed mechanisms
Linux secret-store integration
```

Semantic API thống nhất.

---

# 599.38. Secret Persistence

Secret persistence phải explicit.

```text
SecretPersistence {
    MemoryOnly
    OSProtected
    ApplicationVault
}
```

---

# 599.39. Secret Lifetime

Secret memory nên được quản lý theo lifetime rõ ràng.

Khi có thể:

```text
zeroize
```

sau khi lifetime kết thúc.

---

# 599.40. Secret Memory

Runtime không đảm bảo zeroization tuyệt đối nếu OS/hardware không cho phép, nhưng API phải tránh copy secret không cần thiết.

---

# 599.41. Secret Serialization

Secret không được serialize vào configuration file thông thường nếu chưa explicit opt-in.

---

# 599.42. Configuration Serialization

Configuration provider có thể hỗ trợ:

```text
AXON
JSON
TOML-like
INI
Binary
Registry/platform store
```

nhưng semantic layer không phụ thuộc format.

---

# 599.43. Canonical Internal Representation

```text
ConfigValue
├── Null
├── Bool
├── Integer
├── Float
├── String
├── Bytes
├── Duration
├── Path
├── List
└── Object
```

---

# 599.44. Typed Conversion

Parser tạo `ConfigValue`.

Resolver chuyển sang schema type.

```text
RawValue
   ↓
Schema Conversion
   ↓
TypedValue
```

---

# 599.45. Invalid Type

```text
"abc" → UInt32
```

trả:

```text
ConfigTypeMismatch
```

không tự thành `0`.

---

# 599.46. Numeric Conversion

Không tự động truncate:

```text
1.9 → Int
```

nếu conversion không được schema cho phép.

---

# 599.47. Boolean Parsing

Có thể hỗ trợ canonical:

```text
true
false
```

Các alias như `yes/no` phải do parser/provider policy khai báo.

---

# 599.48. Unknown Keys

Schema có policy:

```text
Reject
Ignore
Preserve
Warn
```

---

# 599.49. Strict Configuration

Production có thể dùng:

```text
unknown_keys = Reject
```

để phát hiện typo.

---

# 599.50. Forward Compatibility

Nếu muốn forward compatibility:

```text
unknown_keys = Preserve
```

---

# 599.51. Configuration Object

```text
ConfigObject {
    schema_id
    values
    source_map
    provenance
}
```

---

# 599.52. Effective Configuration

```text
EffectiveConfig {
    schema_id
    revision
    values
    provenance
}
```

---

# 599.53. Immutable Snapshot

Application đọc configuration từ immutable snapshot:

```text
snapshot = config.current()
```

Snapshot không bị mutate phía sau.

---

# 599.54. Revision

```text
ConfigRevision {
    generation
    content_hash
}
```

---

# 599.55. Snapshot Consistency

Một operation dài có thể giữ:

```text
ConfigSnapshot
```

để toàn bộ operation dùng cùng configuration.

---

# 599.56. Hot Reload

Khi config thay đổi:

```text
OldSnapshot
     ↓
Parse
     ↓
Validate
     ↓
Resolve
     ↓
NewSnapshot
     ↓
Publish
```

---

# 599.57. Atomic Configuration Publication

New snapshot chỉ publish sau khi toàn bộ schema validation thành công.

---

# 599.58. Invalid Reload

Config mới invalid:

```text
OldSnapshot remains active
```

Không đưa partial configuration vào runtime.

---

# 599.59. Configuration Reload State

```text
Idle
 ↓
Detected
 ↓
Loading
 ↓
Parsing
 ↓
Validating
 ↓
Resolving
 ↓
Publishing
 ↓
Applied
```

Failure:

```text
Rejected
```

---

# 599.60. Watcher Integration

`597` file watching cung cấp event:

```text
FileChanged
```

599 biến thành:

```text
ConfigSourceChanged
```

---

# 599.61. Debouncing

Nhiều filesystem events cho cùng một logical update phải được coalesce.

---

# 599.62. Atomic Config File Update

Configuration writer sử dụng semantics của `597`:

```text
write temp
→ fsync/flush according to policy
→ atomic replace
```

---

# 599.63. Config Write Transaction

```text
ConfigTransaction {
    base_revision
    changes[]
}
```

---

# 599.64. Optimistic Concurrency

Commit chỉ thành công nếu:

```text
current_revision == base_revision
```

---

# 599.65. Conflict

Nếu configuration thay đổi trước commit:

```text
ConfigConflict
```

Không silently overwrite.

---

# 599.66. Merge

Có thể hỗ trợ:

```text
config.merge(base, ours, theirs)
```

theo schema-aware semantics.

---

# 599.67. Scalar Conflict

```text
ours.port = 8080
theirs.port = 9000
```

phải báo conflict nếu không có merge policy.

---

# 599.68. Object Merge

Object fields độc lập có thể merge:

```text
ours:
    port = 8080

theirs:
    timeout = 5s
```

→ cả hai nếu không conflict.

---

# 599.69. List Merge

List mặc định không nên merge tùy tiện.

Policy:

```text
Replace
Append
SetUnion
Custom
```

---

# 599.70. Config Transaction API

```text
tx = config.begin()
tx.set(key, value)
tx.remove(key)
tx.commit()
```

---

# 599.71. Transaction Abort

```text
tx.abort()
```

không thay đổi persistent configuration.

---

# 599.72. Config Rollback

Configuration history có thể lưu revisions:

```text
r1 → r2 → r3 → r4
```

---

# 599.73. Rollback Revision

```text
config.restore(r3)
```

thực hiện như transaction mới, không xóa history.

---

# 599.74. Configuration History

```text
ConfigHistoryEntry {
    revision
    timestamp
    source
    actor
    changes
    content_hash
}
```

---

# 599.75. Actor

Actor có thể là:

```text
User
Application
Installer
Policy
Administrator
AI
System
```

---

# 599.76. AI Configuration Change

AI không được trực tiếp mutate configuration production nếu capability không cho phép.

---

# 599.77. AI Config Proposal

```text
ConfigChangeProposal {
    base_revision
    changes
    reason
    expected_effects
}
```

---

# 599.78. AI Validation

Pipeline:

```text
AI Proposal
   ↓
Schema Validate
   ↓
Policy Validate
   ↓
Conflict Check
   ↓
Preview
   ↓
Apply if Authorized
```

---

# 599.79. Configuration Provenance

Mỗi effective value có thể truy ra:

```text
key
value
source
revision
policy
```

---

# 599.80. Provenance Example

```text
network.timeout
value = 10s
source = CommandLine
overrode = UserConfig
policy = Allowed
```

---

# 599.81. Explain API

```text
config.explain("network.timeout")
```

trả:

```text
EffectiveValue
Source
OverriddenSources
Constraints
Policy
```

---

# 599.82. Effective Configuration Explain

```text
config.explain_all()
```

có thể tạo semantic snapshot cho IDE/AI.

---

# 599.83. Environment Provider

Environment được expose qua typed resolver.

```text
env.get("PORT")
```

chỉ là raw source.

Schema:

```text
config.bind(key, Env("PORT"))
```

mới tạo typed configuration.

---

# 599.84. Environment Security

Environment không mặc định được coi là trusted.

Một process có thể nhận environment từ parent không đáng tin.

---

# 599.85. Environment Normalization

Environment variable names có thể map:

```text
AXIOM_APP_NETWORK_TIMEOUT
```

→

```text
app.network.timeout
```

mapping phải deterministic.

---

# 599.86. CLI Provider

CLI parser cung cấp source có priority cao.

---

# 599.87. CLI Schema Binding

Manifest có thể khai báo:

```text
--port → app.network.port
--verbose → logging.level
```

---

# 599.88. CLI Help Generation

CLI help có thể sinh từ schema:

```text
ConfigKey
→ type
→ default
→ allowed range
→ description
```

---

# 599.89. CLI Secret Warning

CLI không nên khuyến khích truyền secret trực tiếp:

```text
--password=...
```

vì process listing/logging có thể expose.

---

# 599.90. Secret CLI Input

Nếu cần:

```text
--password-from-stdin
--credential-id
```

hoặc OS secret provider.

---

# 599.91. System Configuration

System config áp dụng cho machine/user environment.

Application không được giả định physical location.

---

# 599.92. User Configuration

User config nằm trong storage scope `597`.

Semantic API:

```text
StorageScope.UserConfig
```

---

# 599.93. Application Configuration

Application-owned persistent config:

```text
StorageScope.ApplicationData
```

---

# 599.94. Preference Storage

Preferences có thể nằm trong:

```text
UserConfig
```

nhưng semantic type phải là `Preference`.

---

# 599.95. System Policy

Policy có thể đến từ:

```text
OS
Enterprise
Administrator
DeploymentManifest
```

---

# 599.96. Policy Authority

Mỗi policy source có:

```text
authority_level
trust
scope
```

---

# 599.97. Policy Scope

```text
Machine
User
Application
Process
Component
Feature
```

---

# 599.98. Policy Conflict

Nếu hai policy cùng authority và conflict:

```text
PolicyConflict
```

hoặc deterministic tie-break được policy schema khai báo.

Không dùng dictionary iteration order.

---

# 599.99. Policy Deny

`Deny` không thể bị override bởi normal configuration.

---

# 599.100. Policy Require

Ví dụ:

```text
TLS.required = true
```

application chỉ có thể:

```text
TLS = true
```

---

# 599.101. Policy Limit

Ví dụ:

```text
max_memory = 2GB
```

application có thể chọn thấp hơn nhưng không cao hơn.

---

# 599.102. Policy Pin

```text
runtime.version = pinned
```

application không được tự thay đổi.

---

# 599.103. Policy Mask

Secret hoặc sensitive config có thể bị mask khỏi diagnostic/AI view.

---

# 599.104. Profile

Configuration profile:

```text
Development
Debug
Release
Testing
Production
Custom
```

---

# 599.105. Profile Composition

```text
Base
 ↓
Profile
 ↓
User
 ↓
Environment
 ↓
CLI
```

---

# 599.106. Profile Identity

```text
ProfileID {
    name
    definition_hash
}
```

---

# 599.107. Profile Inheritance

Profile có thể inherit:

```text
release
   ↓
production
```

Cycle không được phép.

---

# 599.108. Profile Resolution

Profile graph phải được resolve deterministic.

---

# 599.109. Feature Flags

Feature flag là configuration có lifecycle riêng.

```text
feature.renderer_v2 = true
```

---

# 599.110. Feature Flag Types

```text
Boolean
Enum
Percentage
Targeted
```

Remote/percentage flags phải có deterministic evaluation nếu dùng cho reproducibility.

---

# 599.111. Deterministic Feature Selection

Có thể dùng stable hash:

```text
hash(subject_id, feature_id)
```

Không dùng random runtime nếu cần reproducibility.

---

# 599.112. Remote Configuration

Remote config là optional provider.

```text
Local
  +
Remote
  ↓
Resolver
```

---

# 599.113. Remote Config Trust

Remote configuration phải verify:

```text
identity
signature/integrity
schema
policy
expiry
```

---

# 599.114. Remote Config Failure

Network failure không được làm mất last-known-good configuration.

---

# 599.115. Remote Config Cache

```text
last_known_good
```

được lưu persistent nếu policy cho phép.

---

# 599.116. Remote Config TTL

Remote source có thể có:

```text
ttl
expires_at
```

Expired config không nhất thiết bị xóa; policy quyết định fallback.

---

# 599.117. Configuration Source Availability

Source có trạng thái:

```text
Available
Unavailable
Invalid
Expired
Unauthorized
```

---

# 599.118. Fallback

Nếu remote source unavailable:

```text
last-known-good
```

hoặc local source theo policy.

---

# 599.119. No Silent Security Fallback

Security policy không được fallback từ:

```text
Deny
```

sang:

```text
Allow
```

chỉ vì provider unavailable.

---

# 599.120. Configuration Encryption

Application config thông thường không mặc định phải encrypted.

Secret phải dùng secret store.

Encryption-at-rest có thể là deployment policy.

---

# 599.121. Secret-in-Config Prohibition

Schema có thể đánh dấu:

```text
sensitive = true
```

Runtime yêu cầu SecretProvider thay vì plaintext file.

---

# 599.122. Sensitive Configuration

Ngoài secret còn có:

```text
PII
tokens
internal endpoints
security settings
```

Schema có thể đánh dấu:

```text
sensitive
```

---

# 599.123. Diagnostic Redaction

Diagnostics phải respect sensitivity metadata.

---

# 599.124. AI Redaction

AI semantic configuration API mặc định không trả secret.

---

# 599.125. AI Config View

```text
AIConfigView {
    key
    type
    effective_value
    source
    provenance
    sensitivity
}
```

Sensitive value:

```text
<redacted>
```

---

# 599.126. Configuration Documentation

Schema key có:

```text
description
default
example
deprecation
replacement
```

---

# 599.127. Deprecated Key

```text
deprecated_since
replacement_key
removal_version
```

---

# 599.128. Configuration Migration

Kết nối `598`:

```text
ConfigSchema v3
      ↓
Migration
      ↓
ConfigSchema v4
```

---

# 599.129. Config Migration Trigger

Migration xảy ra khi:

```text
stored_schema < runtime_schema
```

---

# 599.130. Config Migration Before Resolution

Persistent config phải migrate trước khi trở thành source hiệu lực.

```text
Storage
 ↓
Load
 ↓
Migrate
 ↓
Validate
 ↓
Resolve
```

---

# 599.131. Invalid Stored Config

Không được silently reset toàn bộ configuration.

Recovery:

```text
preserve old file
backup
report invalid fields
apply safe defaults only where policy allows
```

---

# 599.132. Safe Defaults

Schema có thể khai báo:

```text
safe_default
```

khác với:

```text
default
```

---

# 599.133. Safe Mode Configuration

Recovery mode sử dụng minimal configuration:

```text
network = disabled
plugins = disabled
optional_features = disabled
```

theo application policy.

---

# 599.134. Configuration Validation Levels

```text
Syntax
Type
Schema
Semantic
Policy
Environment
Dependency
```

---

# 599.135. Semantic Validation

Ví dụ:

```text
min_threads <= max_threads
```

---

# 599.136. Cross-Key Constraints

```text
if encryption.enabled:
    encryption.key_id != null
```

---

# 599.137. Constraint Graph

Configuration validator có thể biểu diễn dependencies:

```text
A → B
A → C
B → D
```

Cycle phải được phát hiện.

---

# 599.138. Validation Cycle

```text
ConstraintCycle
```

là schema error.

---

# 599.139. Validation Diagnostics

Mỗi error:

```text
ConfigDiagnostic {
    key
    source
    expected
    actual
    constraint
    severity
    fix
}
```

---

# 599.140. Fix Suggestions

IDE/AI có thể đề xuất:

```text
port = 8080
```

nhưng không tự sửa nếu không được authorize.

---

# 599.141. Config Diff

```text
ConfigDiff {
    added[]
    removed[]
    changed[]
}
```

---

# 599.142. Semantic Diff

Không chỉ so sánh text.

Ví dụ:

```text
timeout = "5s"
```

và:

```text
timeout = 5000ms
```

có thể semantic-equal.

---

# 599.143. Config Hash

Canonical effective configuration:

```text
ConfigHash = hash(canonical_typed_values)
```

Secret value không nhất thiết đưa trực tiếp vào hash; dùng secret identity/fingerprint phù hợp.

---

# 599.144. Build Configuration

Compiler/build configuration phải tách khỏi runtime application configuration.

```text
BuildConfig
≠
AppConfig
```

---

# 599.145. Compiler Configuration

Compiler config thuộc toolchain/IDE.

Không tự chảy vào application runtime.

---

# 599.146. Deployment Configuration

Deployment manifest có thể inject policy/config nhưng phải giữ provenance.

---

# 599.147. Configuration Provenance Chain

```text
Builtin
 ↓
System
 ↓
Application
 ↓
User
 ↓
Profile
 ↓
Environment
 ↓
CLI
 ↓
Effective
```

Policy được ghi riêng.

---

# 599.148. Provenance Record

```text
ConfigProvenance {
    source_id
    source_revision
    overridden_by[]
    policy_decisions[]
}
```

---

# 599.149. Configuration Snapshot Identity

```text
ConfigSnapshotID =
    hash(
        schema_id,
        revision,
        effective_values,
        policy_revision
    )
```

---

# 599.150. Runtime Config Context

```text
ConfigContext {
    snapshot
    cancellation
    diagnostics
    capabilities
}
```

---

# 599.151. Dependency Injection

Component có thể nhận:

```text
ConfigSnapshot
```

thay vì đọc global configuration.

---

# 599.152. No Hidden Global Mutable Config

Tránh:

```text
global_config.foo = ...
```

---

# 599.153. Component Configuration

Component có thể khai báo subset:

```text
NetworkConfig
RendererConfig
AudioConfig
```

---

# 599.154. Config Projection

```text
network_config =
    config.project(NetworkSchema)
```

---

# 599.155. Projection Isolation

Component chỉ thấy keys mà nó cần.

---

# 599.156. Configuration Capability

Component có thể được cấp:

```text
ConfigCapability<NetworkConfig>
```

thay vì toàn bộ configuration tree.

---

# 599.157. Write Capability

Read-only:

```text
ConfigRead
```

write:

```text
ConfigWrite
```

tách biệt.

---

# 599.158. Runtime Override

Testing/debugging có thể dùng:

```text
RuntimeOverride
```

nhưng không được tự persist.

---

# 599.159. Override Lifetime

```text
Process
Session
Scope
OneOperation
```

---

# 599.160. Debug Override

Ví dụ:

```text
renderer.debug_wireframe = true
```

chỉ tồn tại trong session.

---

# 599.161. Test Override

Test framework có thể tạo isolated snapshot:

```text
base
 ↓
test overrides
 ↓
test snapshot
```

Không sửa user config.

---

# 599.162. Configuration Isolation

Mỗi test có thể có:

```text
ConfigSandbox
```

---

# 599.163. Parallel Tests

Config sandbox phải tránh shared mutable global state.

---

# 599.164. Deterministic Tests

Test phải có thể freeze:

```text
environment
profile
policy
clock
config
```

---

# 599.165. Configuration and Time

Config có thể chứa duration nhưng không nên trực tiếp capture current time khi resolving.

---

# 599.166. Configuration and Randomness

Resolver không được random.

---

# 599.167. Configuration and Platform

Platform-specific values:

```text
windows.*
linux.*
macos.*
ios.*
android.*
wasm.*
```

được chọn theo target.

---

# 599.168. Target Conditional Configuration

```text
when target.os == Windows {
    ...
}
```

Semantic schema phải deterministic.

---

# 599.169. Unsupported Target Key

Target không hỗ trợ feature:

```text
UnsupportedConfiguration
```

hoặc ignored nếu schema policy cho phép.

---

# 599.170. WASM Configuration

WASM có thể nhận config từ:

```text
Host
URL/bootstrap
embedded defaults
persistent browser storage
```

nhưng host boundary phải explicit.

---

# 599.171. Mobile Configuration

Mobile storage phải sử dụng semantic scopes của `597`, không hard-code sandbox paths.

---

# 599.172. Desktop Configuration

Desktop có thể có system/user configuration providers.

Physical path là platform adapter detail.

---

# 599.173. Portable Mode

Portable application có thể dùng:

```text
PortableConfigProvider
```

với root do application package/deployment xác định.

---

# 599.174. Portable Security

Portable mode không được tự động phá sandbox/security policy.

---

# 599.175. Environment Isolation

Application có thể chạy với restricted environment.

Configuration runtime phải hoạt động dù một số source unavailable.

---

# 599.176. Configuration Provider Interface

```text
ConfigProvider {
    id()
    load(schema)
    revision()
    capabilities()
}
```

---

# 599.177. Writable Provider

```text
WritableConfigProvider {
    begin_transaction()
    commit()
    rollback()
}
```

---

# 599.178. Watchable Provider

```text
WatchableConfigProvider {
    subscribe_changes()
}
```

---

# 599.179. Secret Provider Interface

```text
SecretProvider {
    resolve(secret_id)
    metadata(secret_id)
}
```

---

# 599.180. Policy Provider

```text
PolicyProvider {
    load(scope)
    revision()
    authority()
}
```

---

# 599.181. Resolver

```text
ConfigResolver {
    collect_sources()
    validate()
    apply_precedence()
    apply_policy()
    produce_snapshot()
}
```

---

# 599.182. Resolver Algorithm

```text
1. Load schema
2. Discover providers
3. Load source revisions
4. Parse values
5. Validate types
6. Merge according to precedence
7. Apply policy
8. Validate cross-key constraints
9. Resolve secrets
10. Produce immutable snapshot
11. Compute identity/provenance
```

---

# 599.183. Resolver Failure

Resolver phải fail atomically:

```text
OldSnapshot
```

vẫn active nếu new snapshot invalid.

---

# 599.184. Partial Source Failure

Một optional source fail:

```text
SourceUnavailable
```

Resolver fallback theo policy.

---

# 599.185. Required Source Failure

Nếu source required:

```text
ConfigurationUnavailable
```

application startup có thể bị block.

---

# 599.186. Source Requirements

Schema/manifest có thể khai báo:

```text
required = true
optional = true
fallback = ...
```

---

# 599.187. Configuration Startup

```text
ProcessStart
 ↓
Load schema
 ↓
Resolve configuration
 ↓
Validate policy
 ↓
Publish initial snapshot
 ↓
ApplicationStart
```

---

# 599.188. No Application Start Before Required Config

Nếu required config invalid, application không được chạy với giá trị ngầm đoán.

---

# 599.189. Configuration Lifecycle

```text
Uninitialized
 ↓
Loading
 ↓
Resolved
 ↓
Published
 ↓
Reloading
 ↓
Published
```

Failure:

```text
Rejected
```

---

# 599.190. Hot Reload Subscriber

```text
ConfigSubscriber {
    on_config_changed(old, new)
}
```

---

# 599.191. Subscriber Ordering

Subscriber order phải deterministic hoặc được đánh dấu independent.

---

# 599.192. Subscriber Failure

Một subscriber failure không được làm rollback global config snapshot.

Component tự xử lý failure.

---

# 599.193. Component Reconfiguration

Component có thể trả:

```text
Applied
Deferred
Rejected
RestartRequired
```

---

# 599.194. Restart Required

Một config change có thể yêu cầu restart:

```text
RestartRequired
```

nhưng snapshot semantics vẫn rõ ràng.

---

# 599.195. Dynamic vs Static Keys

Schema:

```text
reloadable = true
```

hoặc:

```text
reloadable = false
```

---

# 599.196. Immutable Runtime Keys

Ví dụ:

```text
process.architecture
runtime.abi
application.id
```

không reload.

---

# 599.197. Configuration Event

```text
ConfigChanged {
    old_revision
    new_revision
    changed_keys[]
}
```

---

# 599.198. Configuration Audit

Security-sensitive changes có thể yêu cầu:

```text
actor
timestamp
reason
authorization
```

---

# 599.199. Audit Integrity

Audit log security-sensitive có thể dùng append-only/integrity-protected storage.

---

# 599.200. Configuration Export

API:

```text
config.export()
```

mặc định:

```text
secrets = redacted
```

---

# 599.201. Configuration Import

Import pipeline:

```text
Parse
→ Validate
→ Preview
→ Transaction
→ Commit
```

---

# 599.202. Import Never Auto-Executes

Configuration data không được interpreted như executable code.

---

# 599.203. Configuration Code Injection

Template/expression support nếu có phải sandboxed.

Không cho config mặc định thực thi Axiom code.

---

# 599.204. Expression Configuration

Nếu cần expression:

```text
expression
→ restricted evaluator
```

không truy cập arbitrary filesystem/network.

---

# 599.205. Configuration Templates

Có thể hỗ trợ:

```text
${HOME}
${PORT}
```

nhưng expansion phải deterministic và typed.

---

# 599.206. Template Cycle

```text
A = ${B}
B = ${A}
```

→

```text
ConfigExpansionCycle
```

---

# 599.207. Template Missing Variable

Không silently thành empty string.

Policy:

```text
Error
Default
Preserve
```

---

# 599.208. Secret Template

Secret interpolation phải explicit:

```text
secret://credential/id
```

không dump secret vào ordinary string source nếu không cần.

---

# 599.209. Configuration URI

Provider có thể được xác định bằng:

```text
config://application
config://user
config://system
secret://...
policy://...
```

Semantic URI không phụ thuộc filesystem.

---

# 599.210. Configuration Namespace Graph

```text
config://
├── system
├── application
├── user
├── profile
├── environment
├── command
└── runtime
```

---

# 599.211. Secret Namespace

```text
secret://
├── application
├── user
└── system
```

---

# 599.212. Policy Namespace

```text
policy://
├── system
├── enterprise
├── deployment
└── application
```

---

# 599.213. Access Control

Configuration key có thể khai báo:

```text
read_scope
write_scope
```

---

# 599.214. Secret Access Control

Secret:

```text
secret.read
secret.write
secret.export
```

là capability riêng.

---

# 599.215. Export Permission

Application có thể đọc secret nhưng không có quyền export raw secret.

---

# 599.216. Secret Handle

API ưu tiên handle:

```text
SecretHandle
```

thay vì plaintext lâu dài.

---

# 599.217. Secret Materialization

```text
secret.materialize()
```

là explicit sensitive operation.

---

# 599.218. Secret Memory Copy

Compiler/runtime nên giảm implicit copies của `Secret<T>`.

---

# 599.219. Secret Logging Compiler Analysis

Static analyzer có thể cảnh báo:

```text
Secret → Logger
Secret → String interpolation
Secret → Config export
```

---

# 599.220. Configuration Static Analysis

Compiler/IDE có thể phát hiện:

```text
unknown key
deprecated key
invalid type
invalid range
unused key
secret misuse
policy conflict
```

---

# 599.221. Unused Configuration

Có thể cảnh báo nếu key được định nghĩa nhưng application không đọc.

---

# 599.222. Dead Configuration

Package manager/IDE có thể phát hiện configuration key đã obsolete.

---

# 599.223. Configuration Schema Registry

Application binary chứa:

```text
ConfigSchemaMetadata
```

IDE có thể truy vấn mà không chạy application.

---

# 599.224. Compiler Metadata

Compiler emit:

```text
ConfigMetadata {
    schema_id
    version
    keys
    types
    defaults
    constraints
    sensitivity
    reloadability
    provenance
}
```

---

# 599.225. AI Semantic Query

AI có thể hỏi:

```text
config.describe("network.timeout")
config.explain("network.timeout")
config.diff(revision_a, revision_b)
```

---

# 599.226. AI No-Hallucination Contract

Nếu metadata không tồn tại:

```text
UnknownConfigurationKey
```

AI API không tự tạo key.

---

# 599.227. IDE Completion

IDE có thể autocomplete:

```text
app.network.timeout
app.network.proxy
app.network.tls
```

từ semantic schema.

---

# 599.228. Documentation Generation

Config schema có thể sinh:

```text
CLI help
reference docs
IDE help
AI metadata
sample config
```

---

# 599.229. Sample Configuration

Generated sample phải phân biệt:

```text
default
required
secret
optional
```

---

# 599.230. Secret Sample

Không bao giờ generate real secret.

Ví dụ:

```text
api_key = "<YOUR_SECRET>"
```

---

# 599.231. Configuration Test Contract

Mỗi schema cần test:

```text
valid values
invalid values
boundary values
unknown keys
migration
precedence
policy
reload
serialization
```

---

# 599.232. Precedence Tests

Ví dụ:

```text
Default = 1
User = 2
Env = 3
CLI = 4

Effective = 4
```

---

# 599.233. Policy Tests

```text
User = true
Policy = deny

Effective = false
```

---

# 599.234. Reload Tests

```text
old valid
→ new valid
```

phải atomically publish.

---

# 599.235. Reload Failure Test

```text
old valid
→ new invalid
```

kết quả:

```text
old remains active
```

---

# 599.236. Crash Test

Crash trong config write phải để:

```text
old config
OR
new config
```

không corrupted intermediate.

---

# 599.237. Power-Loss Test

Test matrix của `597` áp dụng cho config transactions.

---

# 599.238. Migration Tests

Config schema:

```text
v1 → v2 → v3
```

phải test direct/legacy paths theo migration graph `598`.

---

# 599.239. Secret Tests

Phải kiểm tra:

```text
redaction
access control
export denial
memory lifetime
serialization denial
logging denial
```

---

# 599.240. Policy Security Tests

```text
override attempt
source spoofing
lower-authority override
expired policy
invalid signature
policy rollback
```

---

# 599.241. Remote Configuration Tests

```text
valid remote
invalid remote
network failure
expired remote
signature failure
schema mismatch
rollback
```

---

# 599.242. Determinism Test

Cùng:

```text
schema
sources
revisions
policy
environment
```

phải tạo cùng:

```text
EffectiveConfigHash
```

---

# 599.243. Configuration Performance

Application hot path không nên parse config file.

Default architecture:

```text
Startup parse
→ Typed immutable snapshot
→ O(1)/near-O(1) key access
```

---

# 599.244. Snapshot Access

Compiled configuration access có thể được tối ưu thành:

```text
offset/index lookup
```

khi schema statically known.

---

# 599.245. Compile-Time Config

Build-time constant configuration có thể được compile vào binary:

```text
comptime config
```

nhưng phải phân biệt với runtime config.

---

# 599.246. Runtime Config Elimination

Nếu compiler chứng minh config immutable:

```text
config.key
```

có thể constant-fold.

---

# 599.247. Dynamic Config Boundary

Hot-reloadable key không được constant-fold qua runtime boundary.

---

# 599.248. Configuration Cache

Resolver có thể cache:

```text
SourceRevisionSet
→ EffectiveSnapshot
```

---

# 599.249. Cache Key

```text
ConfigCacheKey {
    schema_hash
    source_revisions
    policy_revision
    target
}
```

---

# 599.250. Cache Invalidation

Nếu bất kỳ input identity nào thay đổi:

```text
cache invalid
```

---

# 599.251. Memory Model

Config snapshots immutable nên có thể share giữa threads:

```text
Arc-like shared immutable snapshot
```

nhưng không bắt buộc reference-counting nếu lifetime của process/session đủ rõ.

---

# 599.252. Concurrency

Readers không cần lock nếu snapshot immutable.

Writer tạo snapshot mới rồi atomic publish.

```text
Reader → old/new snapshot
Writer → new snapshot
```

---

# 599.253. Atomic Snapshot Pointer

Implementation có thể sử dụng atomic pointer/reference nội bộ.

Chi tiết pointer không lộ ra application API.

---

# 599.254. Snapshot Lifetime

Snapshot được giữ sống tới khi không còn reader sử dụng.

Có thể dùng:

```text
RC
epoch reclamation
arena generation
```

theo runtime implementation.

---

# 599.255. No Global Config Lock

Không dùng global mutex cho mọi config read.

---

# 599.256. Configuration Event Queue

Reload events có thể đi qua `471/472/473`.

Không tạo một event-loop riêng nếu hệ thống đã có event infrastructure.

---

# 599.257. Configuration and Reactive System

`473` có thể expose:

```text
signal<ConfigSnapshot>
```

---

# 599.258. Configuration and Tasks

Reload callbacks chạy trên task system `471`, không block config resolver lâu dài.

---

# 599.259. Configuration and Logging

Logging system `475` lấy initial logging config từ `599`, sau đó subscribe vào reload nếu key reloadable.

---

# 599.260. Configuration and Security

`490` policy/capability system là authority cho sensitive configuration.

---

# 599.261. Configuration and Deployment

`593` deployment manifest có thể khai báo:

```text
default config
required policy
required secrets
```

---

# 599.262. Configuration and Update

`598` migration schema có thể migrate:

```text
stored configuration
```

trước khi application version mới activate.

---

# 599.263. Configuration and Storage

`597` cung cấp:

```text
UserConfig
ApplicationConfig
Temporary
```

598/599 không tự định nghĩa physical directories.

---

# 599.264. Configuration and Resource Runtime

`596` resource system có thể đọc configuration:

```text
resource compression policy
cache limits
locale
theme
```

nhưng resource manager không được tự mutate configuration.

---

# 599.265. Configuration and Localization

`464` có thể dùng:

```text
ui.language
ui.locale
```

nhưng locale resolution phải có fallback deterministic.

---

# 599.266. Configuration and GUI

`452` UI có thể bind preference:

```text
ui.theme
ui.scale
```

thông qua snapshot/transaction API.

---

# 599.267. Configuration and Accessibility

`466` có thể consume system accessibility policy/configuration nhưng không override OS-required settings.

---

# 599.268. Configuration and Network

`454` có thể consume:

```text
proxy
timeout
TLS policy
DNS policy
```

nhưng security policy vẫn authoritative.

---

# 599.269. Configuration and Database

`455` có thể lấy:

```text
database path
pool size
timeout
```

nhưng secret credential phải qua `SecretProvider`.

---

# 599.270. Configuration and AI

`503–545` AI subsystems có thể khai báo typed configuration schemas.

Không được tạo configuration API riêng biệt cho từng AI subsystem.

---

# 599.271. Configuration and GPU

GPU backend có thể khai báo:

```text
device
memory_limit
precision
```

policy có thể giới hạn.

---

# 599.272. Configuration and Compiler

Compiler tools sử dụng cùng semantic config model nhưng **BuildConfig vẫn tách khỏi AppConfig**.

---

# 599.273. Configuration API Surface

Public core:

```text
config.schema()
config.current()
config.get(key)
config.explain(key)
config.begin()
config.watch()
config.reload()
```

---

# 599.274. Preference API

```text
preferences.get(key)
preferences.set(key, value)
preferences.reset(key)
preferences.watch(key)
```

Preference API chỉ là typed facade trên configuration storage.

---

# 599.275. Secret API

```text
secrets.get(id)
secrets.exists(id)
secrets.metadata(id)
```

Raw export cần capability.

---

# 599.276. Policy API

```text
policy.get(key)
policy.explain(key)
policy.is_allowed(capability)
```

---

# 599.277. Environment API

```text
environment.get(name)
environment.list()
```

Raw environment chỉ là source, không phải effective configuration.

---

# 599.278. CLI API

```text
commandline.arguments()
commandline.config()
```

---

# 599.279. Effective Configuration API

```text
effective_config.get(key)
effective_config.snapshot()
effective_config.explain(key)
```

---

# 599.280. Error Model

```text
ConfigError
├── ParseError
├── TypeMismatch
├── ConstraintViolation
├── UnknownKey
├── MissingRequiredValue
├── ProviderUnavailable
├── PolicyDenied
├── SecretUnavailable
├── Conflict
├── MigrationRequired
├── MigrationFailed
├── ReloadRejected
└── PermissionDenied
```

---

# 599.281. Configuration State Model

```text
                    ┌─────────────┐
                    │ Uninitialized│
                    └──────┬──────┘
                           ▼
                       Loading
                           │
                           ▼
                       Validating
                           │
                     ┌─────┴─────┐
                     ▼           ▼
                  Invalid       Valid
                     │           │
                     ▼           ▼
                  Rejected    Published
                                  │
                                  ▼
                              Reloading
                                  │
                         ┌────────┴────────┐
                         ▼                 ▼
                      Rejected          Published
```

---

# 599.282. Configuration Transaction State

```text
Open
 ↓
Modified
 ↓
Validated
 ↓
Committing
 ↓
Committed
```

Failure:

```text
Conflict
ValidationFailed
PermissionDenied
```

---

# 599.283. Secret Access State

```text
Unavailable
    ↓
Resolving
    ↓
Available
    ↓
Materialized
    ↓
Released
```

---

# 599.284. Policy Evaluation State

```text
Unknown
 ↓
Loaded
 ↓
Verified
 ↓
Evaluated
 ↓
Effective
```

---

# 599.285. Configuration File Layout

Một application có thể có:

```text
config/
├── schema.axcfg
├── application.axcfg
├── profiles/
│   ├── debug.axcfg
│   └── release.axcfg
└── migrations/
```

Physical path vẫn do `597` quyết định.

---

# 599.286. Secrets Không nằm trong layout trên

Secret provider độc lập:

```text
secret://application/*
```

---

# 599.287. Configuration Package Metadata

Package `591` có thể chứa schema:

```text
ConfigSchema
MigrationMetadata
DefaultConfig
PolicyMetadata
```

---

# 599.288. Package Configuration Ownership

Package không được tự ghi vào user configuration khi install trừ khi deployment contract cho phép.

---

# 599.289. Uninstall

Uninstall không mặc định xóa:

```text
UserPreferences
ApplicationData
Documents
Secrets
```

Policy `593/597` quyết định.

---

# 599.290. Reset Application

Reset có thể có scopes:

```text
ResetRuntime
ResetConfig
ResetPreferences
ResetCache
ResetApplicationData
ResetSecrets
```

Mỗi scope phải explicit.

---

# 599.291. Factory Reset

Factory reset là destructive operation và phải xác nhận capability/user intent.

---

# 599.292. Configuration Export for Support

Support bundle nên chứa:

```text
effective config
schema
versions
provenance
diagnostics
```

nhưng redact secrets/sensitive values.

---

# 599.293. Configuration Snapshot for Crash

Crash dump `589` có thể lưu:

```text
ConfigSnapshotID
```

thay vì toàn bộ sensitive config.

---

# 599.294. Debugger Integration

Debugger có thể query:

```text
config.current()
config.explain(key)
```

nhưng respect secret redaction.

---

# 599.295. Profiling Integration

Performance profiler có thể ghi:

```text
ConfigSnapshotID
```

để benchmark reproducibility.

---

# 599.296. Reproducibility

Một benchmark/config-dependent build phải record:

```text
ConfigSnapshotID
ToolchainID
Target
DependencyGraphHash
```

---

# 599.297. Security Boundary Summary

```text
                 Configuration
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      Ordinary      Sensitive      Secret
         │             │             │
      File/etc.     Redacted       Vault
         │             │             │
         └─────────────┼─────────────┘
                       ▼
                    Policy
                       │
                       ▼
                 Effective State
```

---

# 599.298. Required Compiler/Runtime Contracts

Compiler phải cung cấp:

```text
typed schema metadata
constraints
sensitivity metadata
reloadability
migration metadata
documentation
```

Runtime phải cung cấp:

```text
provider resolution
snapshot
precedence
policy
transactions
watch/reload
secret boundary
provenance
```

---

# 599.299. Implementation Order

Compiler/runtime implementation nên theo:

```text
1. ConfigValue
2. ConfigSchema
3. ConfigKey<T>
4. Provider API
5. Parser
6. Type validation
7. Resolver
8. Immutable Snapshot
9. Provenance
10. Policy engine
11. Writable transactions
12. File provider
13. Environment provider
14. CLI provider
15. Secret provider
16. Hot reload
17. Migration integration
18. Remote provider
19. IDE/AI integration
20. Tests/security
```

---

# 599.300. FINAL HARD INVARIANT

Axiom `599` chỉ được coi là hoàn chỉnh khi:

```text
1. Configuration, Preference, Secret, Environment, CLI, Policy và RuntimeState là các semantic concepts riêng biệt.

2. Configuration luôn typed.

3. Configuration schema có identity và version.

4. Configuration keys có namespace ổn định.

5. Effective configuration được tạo bởi resolver deterministic.

6. Precedence được định nghĩa bởi policy, không phụ thuộc implementation order.

7. Security policy không thể bị normal configuration override.

8. Policy authority được xác định rõ.

9. Secret không được coi là plaintext configuration thông thường.

10. Secret có access-control boundary riêng.

11. Secret mặc định không xuất hiện trong logs.

12. Secret mặc định không xuất hiện trong AI metadata.

13. Secret không được serialize vào config thông thường một cách implicit.

14. Configuration snapshot là immutable.

15. Configuration readers không cần global lock.

16. Configuration reload được atomic.

17. Configuration reload thất bại không làm mất valid snapshot trước đó.

18. Configuration transaction có optimistic concurrency hoặc equivalent conflict detection.

19. Configuration write sử dụng atomic storage semantics của 597.

20. Crash/power-loss không được tạo configuration file half-written.

21. Unknown keys có policy rõ ràng.

22. Type mismatch không được silently coerce thành giá trị khác.

23. Numeric truncation không được implicit.

24. Cross-key constraints được validate trước publication.

25. Constraint cycle được phát hiện.

26. Required provider failure không được biến thành fabricated default.

27. Remote configuration không được phá local last-known-good state khi network thất bại.

28. Remote configuration phải qua trust/schema/policy validation.

29. Configuration migration tích hợp với 598.

30. Migration xảy ra trước effective configuration resolution.

31. Configuration version không được thay đổi âm thầm.

32. Deprecated keys có metadata.

33. Runtime-reloadable và restart-required keys được phân biệt.

34. Component reconfiguration failure không được corrupt global snapshot.

35. Runtime override không mặc định được persist.

36. Test configuration được isolate khỏi global application configuration.

37. Configuration hash deterministic.

38. Configuration provenance phải xác định được source của effective value.

39. `config.explain()` phải giải thích được precedence và policy decision.

40. IDE/AI chỉ được truy vấn semantic configuration metadata đã tồn tại.

41. AI không được tự phát minh configuration key.

42. AI không được tự ý commit configuration thay đổi nếu thiếu capability.

43. BuildConfig không bị trộn với AppConfig.

44. Physical storage paths không xuất hiện như requirement trong application code.

45. Mobile/Desktop/WASM dùng cùng semantic configuration API.

46. OS credential store được truy cập qua platform adapter.

47. Configuration không được tự động thực thi code.

48. Template/expression configuration nếu tồn tại phải bị giới hạn và sandbox.

49. Policy `Deny` không thể bị normal configuration override.

50. Policy `Limit` không thể bị application vượt qua.

51. Security-sensitive configuration changes có thể audit.

52. Configuration export mặc định redacts sensitive data.

53. Crash/debug/profiling metadata ưu tiên ConfigurationSnapshotID thay vì dump secrets.

54. Configuration cache được identity bằng schema/source/policy revisions.

55. Configuration cache không được dùng khi bất kỳ dependency identity nào thay đổi.

56. Configuration resolution không phụ thuộc wall-clock hoặc randomness.

57. Configuration behavior có thể tái lập từ schema + source revisions + policy.

58. Update system `598` có thể xác định và migrate configuration schema.

59. Deployment system `593` có thể cung cấp configuration/policy nhưng không phá semantic ownership của 599.

60. Storage system `597` cung cấp persistence nhưng không quyết định configuration precedence.

61. Secret store không trở thành arbitrary filesystem storage.

62. Configuration provider không được tự ý cấp thêm privilege.

63. Configuration data không được tự động trở thành executable content.

64. Effective configuration chỉ được publish khi toàn bộ required validation hoàn tất.

65. Không tồn tại trạng thái effective configuration “nửa cũ, nửa mới”.

66. Không có hidden global mutable configuration.

67. Không có silent data loss khi configuration transaction thất bại.

68. Không có silent security-policy downgrade.

69. Không có fabricated value khi source chưa được xác minh.

70. **Tại mọi thời điểm application chỉ được nhìn thấy một Effective Configuration Snapshot hợp lệ, immutable và có provenance xác định; mọi thay đổi configuration phải chuyển từ một snapshot hợp lệ sang một snapshot hợp lệ khác hoặc bị từ chối hoàn toàn.**
```

# 599 — LOCKED

---

# NEXT — BOOTSTRAP-600

## BOOTSTRAP-600 — NATIVE APPLICATION STATE, SESSION, CHECKPOINT & CRASH-RESILIENT STATE RUNTIME 5.0

`600` sẽ tách **persistent configuration** của `599` khỏi **runtime/application state**, đồng thời xây dựng cơ chế session/checkpoint/recovery thống nhất:

```text
                    Application
                         │
                  ┌──────┴──────┐
                  ▼             ▼
             Configuration   Runtime State
                  │             │
                  │       ┌─────┼─────┐
                  │       ▼     ▼     ▼
                  │    Session  State  Checkpoint
                  │             │
                  │             ▼
                  │          Journal
                  │             │
                  └─────────────┤
                                ▼
                         Crash Recovery
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
                 Restore                  Reset
```

Trọng tâm `600`:

- application state model;
- session state;
- transient vs durable state;
- checkpoint;
- journaling;
- crash-consistent state;
- autosave;
- state snapshots;
- recovery;
- interrupted operation recovery;
- undo/redo persistence;
- workspace/session restoration;
- multi-window state;
- background task state;
- actor/task recovery;
- state versioning;
- state migration qua `598`;
- state ownership/lifetime;
- state consistency giữa nhiều processes;
- state transaction;
- incremental checkpoint;
- large-state streaming;
- state compression;
- state encryption;
- state integrity;
- crash dump/state correlation;
- deterministic recovery;
- mobile suspend/resume;
- desktop sleep/wake;
- WASM page/session persistence;
- AI-readable state snapshot;
- state provenance;
- recovery testing;
- **hard invariant: application không bao giờ phải suy đoán trạng thái cuối cùng sau crash.**