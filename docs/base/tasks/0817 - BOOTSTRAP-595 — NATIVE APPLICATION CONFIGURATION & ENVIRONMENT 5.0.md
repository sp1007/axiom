# BOOTSTRAP-595 — NATIVE APPLICATION CONFIGURATION & ENVIRONMENT 5.0
## CONFIG SCHEMA, TYPED CONFIGURATION, ENVIRONMENT VARIABLES, COMMAND-LINE ARGUMENTS, CONFIG FILES, SECRETS BOUNDARY, PROFILE/ENVIRONMENT OVERLAY, RUNTIME OVERRIDES, VALIDATION, MIGRATION, HOT RELOAD & DETERMINISTIC CONFIG RESOLUTION

**Trạng thái: COMPLETED / LOCKED**

`595` chuẩn hóa toàn bộ configuration pipeline của Axiom application. Nó kết nối `470` Configuration/Settings/Preferences, `468` Application State, `593` Deployment Bundle và `594` Process Runtime.

Nguyên tắc cốt lõi:

> Configuration là **data**, không phải code; configuration resolution phải typed, deterministic, observable và có provenance; secrets không được trở thành một phần của source code, package identity hoặc ordinary build artifact.

---

# 595.1. Configuration layers

```text
                    Application
                         │
                         ▼
                Configuration Engine
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
   Built-in           External          Runtime
   Defaults           Sources            Overrides
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  Merge / Resolve
                         │
                         ▼
                  Validate / Normalize
                         │
                         ▼
                 Typed Config Snapshot
```

---

# 595.2. Configuration ≠ State

Configuration mô tả **policy/intention**.

State mô tả **trạng thái hiện tại**.

Ví dụ:

```text
config.max_connections = 100
runtime.current_connections = 73
```

---

# 595.3. Configuration ≠ Secrets

Secret là dữ liệu nhạy cảm được quản lý bằng secret boundary riêng.

---

# 595.4. Configuration ≠ Environment

Environment là một nguồn configuration/runtime context, không phải configuration model itself.

---

# 595.5. Configuration identity

Mỗi resolved configuration snapshot có:

```text
ConfigSnapshotID
```

được tính từ canonical resolved representation.

---

# 595.6. Configuration snapshot

```text
ConfigSnapshot {
    schema_id
    schema_version
    values
    provenance
    source_set
    snapshot_id
}
```

---

# 595.7. Immutable snapshot

Sau khi publish, configuration snapshot là immutable.

---

# 595.8. Runtime replacement

Hot reload tạo snapshot mới thay vì mutate snapshot cũ.

---

# 595.9. Configuration schema

Axiom hỗ trợ typed configuration schema.

```text
config AppConfig {
    host: String
    port: u16
    workers: u32
    debug: bool
}
```

---

# 595.10. Schema identity

Schema có:

```text schema_name
schema_version
schema_hash
```

---

# 595.11. Typed configuration

Application nhận typed configuration thay vì tự parse string ở mọi nơi.

---

# 595.12. Primitive values

Schema có thể dùng:

```text
bool
integers
floats
string
bytes
enum
```

---

# 595.13. Compound values

Hỗ trợ:

```text
array
list
map
struct
optional
```

---

# 595.14. Enum configuration

```text
enum LogLevel {
    Error
    Warn
    Info
    Debug
}
```

---

# 595.15. Duration

Configuration hỗ trợ semantic duration:

```text
timeout = 5s
```

thay vì bắt application parse string thủ công.

---

# 595.16. Size

Hỗ trợ semantic byte sizes:

```text
cache_size = 256MiB
```

---

# 595.17. URI / URL

Nếu schema yêu cầu endpoint, runtime có thể dùng typed URI representation.

---

# 595.18. Path

Filesystem path có semantic type riêng khi target hỗ trợ filesystem.

---

# 595.19. Endpoint

Network endpoint có thể biểu diễn:

```text
Endpoint {
    host
    port
    protocol
}
```

---

# 595.20. Secret type

```text
Secret<T>
```

là logical type cho sensitive configuration.

---

# 595.21. Secret non-display

Secret không được tự động xuất hiện trong:

- logs;
- diagnostics;
- crash dumps;
- IDE hover;
- AI context.

---

# 595.22. Secret comparison

Secret API tránh conversion ngẫu nhiên thành ordinary `String`.

---

# 595.23. Secret lifetime

Secret memory nên được zeroized khi semantics/platform cho phép.

---

# 595.24. Secret provenance

Secret snapshot chỉ lưu source identity, không lưu secret plaintext trong provenance metadata.

---

# 595.25. Configuration source

Các source chuẩn:

```text
BuiltIn
ConfigFile
Environment
CommandLine
Runtime
Platform
SecretProvider
```

---

# 595.26. Source priority

Default resolution:

```text
BuiltIn
   <
ConfigFile
   <
Environment
   <
CommandLine
   <
RuntimeOverride
```

Secret provider không được coi là generic override source; nó chỉ resolve các field được schema đánh dấu secret.

---

# 595.27. Explicit priority

Application có thể khai báo source policy nhưng không được tạo ambiguity.

---

# 595.28. Deterministic resolution

Cùng:

```text schema
source contents
source identities
resolution policy
```

phải tạo cùng configuration snapshot.

---

# 595.29. Unknown configuration keys

Mặc định:

```text unknown key = error
```

---

# 595.30. Extension keys

Schema có thể khai báo explicit extension namespace.

```text
extensions.<provider>.<key>
```

---

# 595.31. Unknown-field compatibility

Strict/lenient mode phải được khai báo, không implicit.

---

# 595.32. Missing required field

Missing required field là configuration error trước khi application chuyển sang `Ready`.

---

# 595.33. Default values

Schema có thể khai báo compile-time/default values.

---

# 595.34. Default determinism

Default không được phụ thuộc wall clock, random state hoặc ambient process state trừ khi field explicitly dynamic.

---

# 595.35. Environment variables

Environment variable mapping:

```text
APP_HOST
APP_PORT
APP_WORKERS
```

có thể map vào typed schema.

---

# 595.36. Environment naming

Schema có thể khai báo canonical environment prefix.

---

# 595.37. Nested configuration

Ví dụ:

```text
database.host
database.port
```

có thể map thành:

```text
APP_DATABASE_HOST
APP_DATABASE_PORT
```

---

# 595.38. Environment parsing

String environment values được parse theo schema type.

---

# 595.39. Parse failure

Invalid environment value là structured configuration error.

---

# 595.40. Boolean parsing

Boolean syntax phải canonical và không phụ thuộc locale.

---

# 595.41. Numeric parsing

Numeric parsing phải deterministic và locale-independent.

---

# 595.42. UTF-8

Axiom configuration text mặc định UTF-8.

---

# 595.43. Unicode normalization

Configuration keys dùng canonical language rules; filesystem/path semantics phụ thuộc platform.

---

# 595.44. Command-line schema

Application có thể khai báo typed command-line options.

```text
cli {
    port: u16
    verbose: bool
}
```

---

# 595.45. CLI positional arguments

Có thể khai báo positional arguments.

---

# 595.46. CLI flags

Có:

```text
--port 8080
--verbose
```

---

# 595.47. CLI aliases

Schema có thể khai báo short aliases:

```text
-p
-v
```

---

# 595.48. CLI precedence

CLI override config file và environment theo default resolution policy.

---

# 595.49. Unknown CLI option

Unknown option là error trừ khi application explicitly cho phép passthrough.

---

# 595.50. Help generation

CLI schema có thể tự sinh help.

---

# 595.51. Version generation

CLI có thể tự sinh:

```text
--version
```

từ application artifact metadata.

---

# 595.52. Config file formats

Axiom chuẩn hóa semantic configuration model, không buộc một serialization format duy nhất.

Platform/runtime có thể hỗ trợ:

```text
AXCONF
JSON
TOML-like
YAML-like
```

nhưng semantic parser phải đưa về cùng typed model.

---

# 595.53. AXCONF

Axiom khuyến nghị native format:

```text
AXCONF
```

với mục tiêu:

- deterministic;
- UTF-8;
- typed literals;
- comments;
- stable canonicalization;
- không có executable expressions.

---

# 595.54. No executable config

Config file không được chứa arbitrary executable code.

---

# 595.55. No hidden computation

Parser không được chạy arbitrary user code để evaluate configuration.

---

# 595.56. Configuration expressions

Chỉ hỗ trợ expression set rất giới hạn nếu schema cho phép.

---

# 595.57. Environment substitution

Có thể hỗ trợ:

```text
path = "${HOME}/data"
```

nhưng substitution phải xảy ra trong controlled resolver.

---

# 595.58. Recursive substitution

Recursive expansion bị giới hạn hoặc cấm để tránh cycle.

---

# 595.59. Substitution cycle

Cycle:

```text A -> B -> A
```

là configuration error.

---

# 595.60. Include

Config file có thể include file khác.

---

# 595.61. Include policy

Include phải có root policy để tránh đọc file ngoài deployment/config boundary.

---

# 595.62. Include cycle

Circular include là error.

---

# 595.63. Include depth

Maximum include depth phải configurable nhưng bounded.

---

# 595.64. Canonical source identity

Mỗi config source có canonical identity.

---

# 595.65. Source hash

Config source được hash trước khi resolution.

---

# 595.66. Provenance

Mỗi field có thể trace về source:

```text
FieldProvenance {
    source
    location
    precedence
}
```

---

# 595.67. Configuration explain

CLI/IDE có thể trả lời:

```text
Why is port = 8080?
```

với provenance graph.

---

# 595.68. Provenance example

```text
port
 ├── default = 3000
 ├── config = 8080
 └── env = absent

effective = 8080
```

---

# 595.69. Override graph

Configuration resolution có semantic graph thay vì chỉ một flat map.

---

# 595.70. Conflict

Nếu hai source cùng precedence đưa ra incompatible values:

```text ConfigurationConflict
```

---

# 595.71. Explicit override

Priority rules phải resolve conflict deterministic.

---

# 595.72. Merge semantics

Struct:

```text
merge by field
```

---

# 595.73. Scalar merge

Scalar override thay thế giá trị cũ.

---

# 595.74. Map merge

Map mặc định merge theo key.

---

# 595.75. List merge

List mặc định replace toàn bộ, tránh semantics khó đoán.

---

# 595.76. Append lists

Append chỉ được dùng khi schema khai báo rõ.

---

# 595.77. Delete marker

Configuration source có thể cần explicit deletion marker cho inherited values.

---

# 595.78. Null semantics

`null` chỉ có ý nghĩa nếu schema field cho phép optional/null.

---

# 595.79. Validation phases

```text Parse
 ↓
Resolve
 ↓
Type-check
 ↓
Normalize
 ↓
Validate
 ↓
Freeze
```

---

# 595.80. Parse validation

Syntax errors được phát hiện trước semantic validation.

---

# 595.81. Type validation

String `"123"` không tự động trở thành arbitrary type nếu schema không cho phép conversion.

---

# 595.82. Range validation

Schema hỗ trợ:

```text min
max
```

---

# 595.83. Length validation

String/list/map có thể có size constraints.

---

# 595.84. Pattern validation

String có thể có deterministic pattern constraint.

---

# 595.85. Cross-field validation

Schema có thể khai báo:

```text if tls.enabled
then tls.certificate required
```

---

# 595.86. Validation purity

Validation function mặc định phải pure.

---

# 595.87. No network validation by default

Config validation không tự gọi network/database.

---

# 595.88. Async validation

External validation nếu cần phải là explicit startup phase, không phải schema validation primitive.

---

# 595.89. Normalization

Typed config được canonicalize sau validation.

---

# 595.90. Canonical representation

Equivalent semantic values phải tạo canonical representation giống nhau.

---

# 595.91. Snapshot hashing

```text
ConfigSnapshotID =
Hash(
    schema_hash,
    canonical_values,
    resolution_policy
)
```

---

# 595.92. Runtime overrides

Runtime override là ephemeral configuration.

---

# 595.93. Runtime override example

```text
runtime.config.set("log.level", Debug)
```

---

# 595.94. Override authority

Runtime override không được override immutable security policy.

---

# 595.95. Security configuration

Một số config được đánh dấu:

```text immutable_at_runtime
```

---

# 595.96. Immutable configuration

Ví dụ:

```text sandbox.capabilities
code_signing_policy
security_mode
```

không được hot-reload tùy tiện.

---

# 595.97. Mutable configuration

Có thể hot-reload:

```text log level
cache size
feature toggles
timeouts
```

nếu application hỗ trợ.

---

# 595.98. Hot reload

```text old snapshot
      │
      ▼
load new sources
      │
      ▼
resolve
      │
      ▼
validate
      │
      ▼
new snapshot
      │
      ▼
publish
```

---

# 595.99. Atomic publication

Application chỉ thấy old hoặc new snapshot, không thấy half-resolved state.

---

# 595.100. Subscriber

Application có thể subscribe configuration changes.

```text on_config_changed(old, new)
```

---

# 595.101. Change set

Runtime có thể compute:

```text Added
Removed
Changed
Unchanged
```

---

# 595.102. Secret change

Secret change không expose plaintext trong ChangeSet.

---

# 595.103. Reload rejection

Nếu new config invalid:

```text old snapshot remains active
```

---

# 595.104. Reload failure safety

Configuration reload failure không tự động crash application.

---

# 595.105. Critical config

Application có thể đánh dấu config change requiring restart.

---

# 595.106. Restart-required field

```text config.database.driver
```

có thể yêu cầu restart nếu runtime không thể safely replace it.

---

# 595.107. Configuration mutability declaration

Schema field:

```text mutable
restart_required
immutable
```

---

# 595.108. Runtime policy

Runtime phải reject mutation trái schema.

---

# 595.109. Configuration watcher

File watcher có thể trigger reload.

---

# 595.110. Debounce

Multiple filesystem events có thể được debounce.

---

# 595.111. Atomic file update

Recommended pattern:

```text temp file
   ↓
fsync
   ↓
rename
```

để tránh đọc partial config.

---

# 595.112. Partial write

Parser phải reject malformed partial file và giữ snapshot cũ.

---

# 595.113. Config version

Schema có semantic version.

---

# 595.114. Config migration

Migration:

```text v1
 ↓
migration
 ↓
v2
```

---

# 595.115. Migration purity

Migration nên deterministic và side-effect free.

---

# 595.116. Migration chain

Có thể:

```text v1 → v2 → v3
```

---

# 595.117. Migration skip

Runtime có thể dùng direct migration nếu explicitly registered.

---

# 595.118. Migration failure

Migration failure ngăn activation config mới.

---

# 595.119. Backward compatibility

Application có thể accept previous schema versions nếu migration tồn tại.

---

# 595.120. Forward compatibility

Unknown future schema version mặc định bị reject.

---

# 595.121. Configuration profile

Profiles:

```text dev
test
staging
production
```

là named source overlays.

---

# 595.122. Profile selection

Profile được chọn trước resolution.

---

# 595.123. Profile inheritance

```text base
 ↓
development
 ↓
local
```

---

# 595.124. Profile cycle

Profile inheritance cycle là error.

---

# 595.125. Environment identity

Environment:

```text development
production
```

không tự động thay đổi semantics của Axiom language.

---

# 595.126. No environment magic

Axiom compiler không được compile code khác chỉ vì `production` trừ khi feature/profile explicitly được build configuration yêu cầu.

---

# 595.127. Build-time vs runtime config

Build-time configuration thuộc build system.

Runtime configuration thuộc application runtime.

---

# 595.128. No secret baking

Secrets không được bake vào binary chỉ vì build-time configuration.

---

# 595.129. Feature flags

Feature flags có thể thuộc configuration.

---

# 595.130. Compile-time feature

Compile-time feature không phải runtime feature flag.

---

# 595.131. Configuration-driven behavior

Application code phải explicitly read config.

---

# 595.132. Configuration dependency

Compiler semantic metadata có thể record:

```text function → config field
```

nếu tooling hỗ trợ.

---

# 595.133. Config API

Core runtime:

```text config.load()
config.resolve()
config.snapshot()
config.get()
config.reload()
config.provenance()
```

---

# 595.134. Typed access

Preferred:

```text
let cfg: AppConfig = config.load()
```

---

# 595.135. Dynamic access

Dynamic key lookup có thể tồn tại cho generic tooling:

```text config.get_dynamic("foo.bar")
```

nhưng không thay thế typed access.

---

# 595.136. Missing dynamic key

Trả `Option`/`Result`, không panic mặc định.

---

# 595.137. Configuration errors

```text ConfigError {
    source
    path
    kind
    location
    message
}
```

---

# 595.138. Error categories

```text ParseError
TypeError
MissingField
UnknownField
RangeError
Conflict
IncludeCycle
SubstitutionCycle
MigrationError
SecretError
PolicyError
```

---

# 595.139. Multi-error reporting

Resolver nên report nhiều independent configuration errors trong một invocation.

---

# 595.140. Error source span

Config parser giữ source span.

---

# 595.141. CLI diagnostics

Diagnostics phải chỉ rõ:

```text source
field
expected
actual
```

---

# 595.142. Secret-safe diagnostics

Không print secret value khi type/validation fail.

---

# 595.143. Example

Không:

```text expected token "abc123"
```

Mà:

```text expected Secret<String>; supplied value is invalid
```

---

# 595.144. Configuration storage

Application config immutable snapshot có thể được memory-mapped hoặc shared nếu phù hợp.

---

# 595.145. Configuration performance

Read access sau resolution phải gần như direct typed field access.

---

# 595.146. No repeated parsing

Application không được parse config string mỗi lần `get()`.

---

# 595.147. Compile-time schema generation

Compiler có thể generate config parser/validator từ schema.

---

# 595.148. Generated parser

Generated parser có thể:

```text parse
validate
normalize
```

mà không cần generic reflection runtime.

---

# 595.149. Zero-cost typed config

Unused configuration fields/decoders có thể bị loại khỏi binary khi static schema generation được sử dụng.

---

# 595.150. Reflection

Dynamic schema inspection thuộc metadata/reflection system `446`, không bắt buộc trong runtime core.

---

# 595.151. AI-readable schema

Schema phải có machine-readable representation.

---

# 595.152. AI configuration query

AI tooling có thể query:

```text schema
current snapshot
provenance
validation errors
mutable fields
```

---

# 595.153. AI mutation safety

AI-generated configuration changes phải:

```text propose
→ validate
→ preview diff
→ apply
```

---

# 595.154. No silent AI config mutation

AI không được tự thay đổi production configuration nếu không có explicit authorization.

---

# 595.155. Configuration diff

```text ConfigDiff {
    path
    old
    new
    source
    requires_restart
}
```

Secrets hiển thị dưới dạng redacted markers.

---

# 595.156. Config explain graph

```text Field
 │
 ├── Schema
 ├── Default
 ├── File
 ├── Environment
 ├── CLI
 └── Runtime Override
```

---

# 595.157. Deployment integration

`593` package manifest có thể khai báo:

```text config_schema
default_config
required_environment
required_secrets
```

---

# 595.158. Deployment manifest

Deployment package không chứa runtime secrets.

---

# 595.159. Secret provider

Supported abstraction:

```text SecretProvider
    get()
    exists()
    metadata()
```

---

# 595.160. Secret provider examples

Platform adapter có thể map tới:

- OS credential store;
- secure enclave/key store;
- deployment secret service;
- environment injection.

---

# 595.161. Secret provider identity

Secret provider có stable provider ID.

---

# 595.162. Secret resolution failure

Nếu required secret unavailable:

```text application startup fails
```

trừ khi schema marks it optional.

---

# 595.163. Secret optionality

```text Secret<Option<T>>
```

hoặc equivalent typed representation.

---

# 595.164. Secret rotation

Secret provider có thể notify rotation.

---

# 595.165. Rotation semantics

Rotation tạo new config snapshot nếu field mutable.

---

# 595.166. Rotation failure

Current valid secret remains active nếu new secret invalid/unavailable.

---

# 595.167. Secret caching

Runtime có thể cache secret nhưng phải obey provider lifetime/policy.

---

# 595.168. Secret zeroization

Sensitive buffers nên được zeroized khi no longer needed.

---

# 595.169. Core dump policy

Secret-bearing memory có thể được excluded from crash dump nếu platform hỗ trợ.

---

# 595.170. Debugger policy

Debugger không tự show secret fields.

---

# 595.171. Logging policy

`Secret<T>` format mặc định:

```text
<redacted>
```

---

# 595.172. Serialization policy

Serializing `Secret<T>` yêu cầu explicit operation.

---

# 595.173. Copy policy

Secret types nên hạn chế accidental copying.

---

# 595.174. Configuration file permissions

Runtime có thể validate file ownership/permissions khi source chứa secrets.

---

# 595.175. Secret-in-file policy

Nếu config file chứa secret:

```text
schema + deployment policy
```

phải cho phép explicit.

---

# 595.176. Warning

Production runtime có thể cảnh báo secret nằm trong ordinary config file.

---

# 595.177. Config encryption

Encryption-at-rest của config file không thuộc configuration semantics; thuộc security/storage layer.

---

# 595.178. No custom crypto

Config engine không tự phát minh encryption algorithm.

---

# 595.179. Environment leakage

Environment variables không được tự đưa vào package provenance/logging.

---

# 595.180. Child process propagation

Theo `594`, child chỉ nhận environment variables được policy cho phép.

---

# 595.181. Configuration inheritance

Child process có thể inherit config subset nhưng phải explicit.

---

# 595.182. Config namespace

Process có namespace:

```text application
service
process
```

---

# 595.183. Process-local override

Worker có thể override config riêng nếu supervisor policy cho phép.

---

# 595.184. Global config

Global configuration phải distinguish khỏi process-local configuration.

---

# 595.185. Configuration scope

```text Global
Application
Service
Process
Task
```

---

# 595.186. Scope inheritance

```text Global
 ↓
Application
 ↓
Service
 ↓
Process
```

---

# 595.187. Task config

Task-local config chỉ tồn tại nếu application explicit tạo context.

---

# 595.188. Context object

```text ConfigContext
```

cho phép truyền immutable configuration scope.

---

# 595.189. Ambient configuration

Ambient global mutable config không được khuyến nghị.

---

# 595.190. Deterministic dependency injection

Application có thể inject `ConfigContext` vào services/tasks.

---

# 595.191. Configuration context lifetime

Context lifetime phải theo ownership semantics `423`.

---

# 595.192. Thread safety

Immutable snapshots có thể share giữa threads/tasks mà không lock.

---

# 595.193. Snapshot sharing

```text Arc-like shared immutable snapshot
```

có thể dùng library-level mechanism nếu cần.

---

# 595.194. Atomic pointer swap

Hot reload có thể dùng atomic snapshot replacement.

---

# 595.195. Reader behavior

Readers đang sử dụng old snapshot được phép hoàn thành.

---

# 595.196. New readers

New readers nhận latest published snapshot.

---

# 595.197. Snapshot lifetime

Old snapshot được reclaim khi không còn references.

---

# 595.198. Reload concurrency

Concurrent reload requests phải serialize hoặc coalesce.

---

# 595.199. Reload storm protection

Runtime phải debounce/coalesce repeated source changes.

---

# 595.200. Configuration cache

Parsed config sources có thể cache theo:

```text source_hash
schema_hash
parser_version
```

---

# 595.201. Cache invalidation

Source hash thay đổi thì parsed representation cũ không được sử dụng.

---

# 595.202. Config cache identity

Config cache không được phụ thuộc machine-local absolute paths ngoài provenance mapping.

---

# 595.203. Reproducibility

Build/deployment configuration phải distinguish:

```text reproducible configuration
machine-local runtime configuration
```

---

# 595.204. Runtime-only sources

Environment, CLI và secrets không nằm trong reproducible package identity mặc định.

---

# 595.205. Build identity

Build system `487/568` chỉ hash build configuration sources thực sự ảnh hưởng compilation.

---

# 595.206. Runtime identity

Runtime configuration snapshot không thay đổi binary artifact identity.

---

# 595.207. Deployment identity

Deployment package identity không thay đổi vì runtime secret value.

---

# 595.208. Provenance chain

```text
Schema
   ↓
Source Set
   ↓
Resolution Policy
   ↓
Config Snapshot
   ↓
Application Instance
```

---

# 595.209. Configuration audit

Audit có thể ghi:

```text source added
source removed
reload
validation failure
override
```

nhưng không ghi secret values.

---

# 595.210. Configuration security

Configuration có security classification:

```text Public
Internal
Sensitive
Secret
```

---

# 595.211. Classification propagation

Derived configuration phải inherit highest required classification.

---

# 595.212. Sensitive fields

Sensitive fields cũng bị redacted trong AI/debug output.

---

# 595.213. Config access authorization

Application components có thể được giới hạn field namespaces.

---

# 595.214. Least privilege

Service chỉ nên nhận configuration fields nó cần.

---

# 595.215. Config projection

```text
full_config
   ↓
project(DatabaseConfig)
```

---

# 595.216. Projection

Projection tạo typed subset mà không expose unrelated secrets.

---

# 595.217. Configuration API security

Config mutation API phải require capability:

```text config.write
```

---

# 595.218. Read-only runtime

Production application có thể chạy với configuration read-only.

---

# 595.219. Operator override

Operator runtime override phải distinguish khỏi application self-modification.

---

# 595.220. Operator provenance

Override record:

```text actor
timestamp
field
previous source
new source
```

---

# 595.221. No hidden persistence

Runtime override không tự persist thành config file.

---

# 595.222. Explicit persistence

Nếu muốn persist:

```text config.persist()
```

phải explicit và policy-controlled.

---

# 595.223. Persistence atomicity

Persist phải sử dụng transactional file replacement.

---

# 595.224. Persistence permissions

Runtime phải respect filesystem permissions/sandbox.

---

# 595.225. Configuration locking

Application có thể lock sensitive fields after startup.

---

# 595.226. Lock semantics

Locked field không thể thay đổi qua lower-priority source.

---

# 595.227. Startup lock

Một số fields có thể lock sau successful initialization.

---

# 595.228. Config lifecycle

```text Unloaded
   ↓
Loaded
   ↓
Resolved
   ↓
Validated
   ↓
Active
   ↓
Superseded
```

---

# 595.229. Invalid config lifecycle

```text Loaded
   ↓
Resolved
   ↓
ValidationFailed
```

không trở thành Active.

---

# 595.230. Configuration state machine

```text
                 ┌───────────────┐
                 │    Unloaded   │
                 └───────┬───────┘
                         ▼
                     Loading
                         │
                         ▼
                    Resolving
                         │
                 ┌───────┴────────┐
                 ▼                ▼
             Validating        Error
                 │
          ┌──────┴──────┐
          ▼             ▼
       Active        Invalid
          │
          ▼
       Reloading
          │
     ┌────┴─────┐
     ▼          ▼
  Active      Error
```

---

# 595.231. Config activation

Activation là atomic publish operation.

---

# 595.232. Startup integration

`594` process chỉ chuyển `Ready` sau required configuration validation.

---

# 595.233. Startup ordering

```text Process spawn
      ↓
Load config
      ↓
Resolve secrets
      ↓
Validate
      ↓
Initialize services
      ↓
Ready
```

---

# 595.234. Config failure and process state

Required config failure:

```text Starting → Failed
```

---

# 595.235. Restart policy

Nếu `594` restart policy cho phép, config failure có thể trigger restart nhưng phải có backoff.

---

# 595.236. Configuration health

Configuration source availability có thể là health signal.

---

# 595.237. Config service unavailable

Nếu external configuration provider unavailable:

- use cached valid config nếu policy cho phép;
- otherwise fail startup/reload.

---

# 595.238. Stale configuration

Cached config phải expose age/provenance.

---

# 595.239. Maximum staleness

Application có thể đặt:

```text max_config_age
```

---

# 595.240. Stale rejection

Nếu vượt maximum age:

```text ConfigExpired
```

---

# 595.241. Remote configuration

Remote config thuộc external provider layer, không phải mandatory core.

---

# 595.242. Network dependency

Application không nên bị ép phụ thuộc network để load basic local configuration.

---

# 595.243. Offline mode

Configuration engine phải hỗ trợ offline operation.

---

# 595.244. Air-gapped deployment

`593` air-gapped deployment có thể package schema/defaults mà không package secrets.

---

# 595.245. Config schema package

Deployment bundle có thể chứa:

```text schema
default config
documentation
migration
```

---

# 595.246. Environment-specific deployment

Deployment system có thể inject external config khi installation/runtime.

---

# 595.247. Config manifest

Ví dụ semantic:

```text
config {
    schema = "app.Config"
    version = 3

    source "config/app.axconf"
    env_prefix = "APP"

    required_secret "database.password"
}
```

---

# 595.248. Manifest validation

Deployment validation phải kiểm tra schema tồn tại và compatible.

---

# 595.249. Missing runtime secret

Package installation không được coi là thất bại chỉ vì runtime secret chưa có, trừ khi deployment policy yêu cầu preflight validation.

---

# 595.250. Preflight

Deployment có thể thực hiện:

```text package verify
config schema verify
environment verify
secret availability verify
```

---

# 595.251. Preflight no secret disclosure

Preflight chỉ report:

```text present / missing / inaccessible
```

không expose value.

---

# 595.252. Configuration CLI

Đề xuất:

```text
axiom config validate
axiom config resolve
axiom config explain
axiom config diff
axiom config schema
axiom config migrate
```

---

# 595.253. `config validate`

Validate source mà không launch application.

---

# 595.254. `config resolve`

Render effective non-secret configuration.

---

# 595.255. `config explain`

Show provenance của field.

---

# 595.256. `config diff`

Compare snapshots/source sets.

---

# 595.257. `config schema`

Show machine-readable schema.

---

# 595.258. `config migrate`

Transform old configuration version sang current schema.

---

# 595.259. Redaction

CLI output mặc định redact:

```text Secret
Sensitive
```

---

# 595.260. Explicit reveal

Secret reveal là privileged operation và không phải default CLI behavior.

---

# 595.261. IDE integration

IDE `590` có thể cung cấp:

- completion;
- schema validation;
- hover;
- provenance;
- safe refactoring;
- migration preview.

---

# 595.262. Configuration completion

Completion dựa trên schema, không phải hardcoded string lists.

---

# 595.263. Config refactoring

Rename field phải có thể update:

```text schema
config files
environment mapping
documentation
```

nếu semantic references được biết.

---

# 595.264. AI configuration planning

AI có thể phân tích configuration graph và đề xuất changes.

---

# 595.265. AI evidence

AI-generated configuration explanation phải reference:

```text schema
source
snapshot
provenance
```

---

# 595.266. No AI secret access by default

AI tooling không được đọc plaintext secrets nếu capability không được cấp.

---

# 595.267. Configuration documentation

Schema có thể chứa:

```text description
default
allowed values
security classification
reload semantics
```

---

# 595.268. Documentation generation

CLI/IDE docs có thể tự sinh từ schema.

---

# 595.269. Localization

Configuration keys không phụ thuộc localized display names.

---

# 595.270. Human-readable descriptions

Descriptions có thể localized nhưng canonical key vẫn ổn định.

---

# 595.271. Configuration tests

Test framework `435` hỗ trợ test:

```text source
resolution
validation
migration
reload
```

---

# 595.272. Golden tests

Canonical resolved configuration có thể được golden-tested.

---

# 595.273. Fuzzing

Config parser phải được fuzz.

---

# 595.274. Malformed input

Malformed configuration không được crash compiler/runtime.

---

# 595.275. Resource exhaustion

Parser phải giới hạn:

```text file size
nesting depth
string length
collection size
include depth
```

---

# 595.276. Billion-laughs-like protection

Formats hỗ trợ aliases/references phải disable hoặc giới hạn recursive expansion.

---

# 595.277. Parser sandbox

Config parser không có quyền filesystem/network ngoài explicit include/provider interface.

---

# 595.278. Deterministic parser

Parser không được phụ thuộc locale hoặc host-specific implicit behavior.

---

# 595.279. Canonical serialization

Runtime có thể serialize snapshot canonical form.

---

# 595.280. Canonical config hash

Canonical serialized snapshot phải tạo stable hash.

---

# 595.281. Equality

Two configuration snapshots equal nếu canonical semantic values + schema identity giống nhau.

---

# 595.282. Source equality

Different source files có thể tạo cùng semantic snapshot.

---

# 595.283. Snapshot identity vs source identity

Không được nhầm:

```text source hash ≠ config snapshot hash
```

---

# 595.284. Cache reuse

Nếu source set/schema/policy không đổi, resolver có thể reuse cached snapshot.

---

# 595.285. Dependency graph

Configuration dependencies:

```text schema
 ↓
source
 ↓
include
 ↓
environment
 ↓
secret
```

được biểu diễn thành graph.

---

# 595.286. Incremental reload

Chỉ source dependencies bị thay đổi cần reparse/revalidate nếu semantics cho phép.

---

# 595.287. Config query database

Compiler/IDE daemon có thể index schema/config relationships.

---

# 595.288. Config semantic index

Index:

```text field
source
consumer
validation
reloadability
```

---

# 595.289. Consumer tracking

Tooling có thể biết function/service nào consume field nào nếu compiler metadata hỗ trợ.

---

# 595.290. Dead config detection

Static analysis có thể detect config fields không được consume.

---

# 595.291. Missing config consumer

Không phải error nếu schema intentionally exposes external API.

---

# 595.292. Config deprecation

Field có thể đánh dấu:

```text deprecated_since
replacement
removal_version
```

---

# 595.293. Deprecation warning

Runtime/IDE cảnh báo khi deprecated field được sử dụng.

---

# 595.294. Config migration tooling

Migration tool có thể tự generate patch.

---

# 595.295. Configuration compatibility contract

Schema versioning phải giữ compatibility rules explicit.

---

# 595.296. Platform configuration

Platform adapter có thể cung cấp read-only system config:

```text CPU count
OS
locale
sandbox state
```

---

# 595.297. System information

System info không được trộn vào user configuration snapshot nếu nó chỉ là runtime observation.

---

# 595.298. Locale

Locale mặc định lấy từ runtime/platform, nhưng configuration có thể override application locale.

---

# 595.299. Time zone

Timezone cũng là runtime/platform context hoặc explicit configuration.

---

# 595.300. FINAL HARD INVARIANTS

### Invariant 1 — typed configuration

> Application configuration phải được resolve thành typed semantic model trước khi application đạt `Ready`.

### Invariant 2 — deterministic resolution

> Cùng schema, source contents và resolution policy phải tạo cùng snapshot.

### Invariant 3 — explicit precedence

> Source precedence phải xác định, không phụ thuộc thứ tự filesystem/environment enumeration.

### Invariant 4 — immutable snapshots

> Active configuration snapshot không bị mutate in-place.

### Invariant 5 — atomic reload

> Hot reload chỉ publish configuration đã parse, resolve và validate hoàn chỉnh.

### Invariant 6 — rollback safety

> Reload thất bại phải giữ nguyên active valid snapshot.

### Invariant 7 — no executable config

> Configuration không được tự thực thi arbitrary code.

### Invariant 8 — no implicit secret baking

> Runtime secrets không được tự động trở thành một phần của source, binary hoặc deployment package identity.

### Invariant 9 — secret redaction

> Secret/Sensitive values mặc định không xuất hiện trong log, diagnostic, crash dump, debugger hoặc AI output.

### Invariant 10 — provenance

> Mỗi effective configuration field phải có thể truy nguyên tới source khi provenance được yêu cầu.

### Invariant 11 — schema versioning

> Configuration schema evolution phải có version và migration contract rõ ràng.

### Invariant 12 — bounded parser

> Config parsing phải chống resource exhaustion và recursive expansion vô hạn.

### Invariant 13 — explicit mutability

> Field chỉ hot-reload nếu schema cho phép.

### Invariant 14 — security immutability

> Security-critical fields không được runtime override nếu deployment/security policy cấm.

### Invariant 15 — child isolation

> Child process không tự động nhận toàn bộ configuration/secrets của parent.

### Invariant 16 — typed CLI/environment

> Environment variables và CLI values phải được parse theo schema, không phải ad-hoc string handling.

### Invariant 17 — runtime/build separation

> Runtime configuration không làm thay đổi identity của binary artifact.

### Invariant 18 — offline capability

> Configuration engine phải hoạt động offline đối với local configuration.

### Invariant 19 — AI safety

> AI có thể inspect/propose configuration nhưng không được silently mutate privileged runtime configuration.

### Invariant 20 — performance

> Sau resolution, configuration read path phải có thể compile xuống gần như direct typed access; không parse lại mỗi lần đọc.

---

# 595 — LOCKED

Kiến trúc application hiện tại:

```text
593 ── Deployment Package
          │
          ▼
594 ── Process Runtime
          │
          ▼
595 ── Configuration Engine
          │
          ├── Typed Schema
          ├── Config Sources
          ├── Environment
          ├── CLI
          ├── Secrets
          ├── Validation
          ├── Hot Reload
          ├── Provenance
          └── AI/IDE Integration
```

Configuration giờ đã có ranh giới rõ với **application state**, **deployment**, **secrets** và **build configuration**.

---

# NEXT — BOOTSTRAP-596

## NATIVE APPLICATION RESOURCE & ASSET RUNTIME 5.0
### RESOURCE IDENTIFIERS, EMBEDDED ASSETS, FILESYSTEM ASSETS, STREAMING RESOURCES, LOCALIZATION, FONT/IMAGE/AUDIO/VIDEO RESOURCES, RESOURCE CACHE, MEMORY MAPPING, VERSIONING, HOT REPLACEMENT & ZERO-COPY RESOURCE ACCESS

```text
                 Application Bundle
                        │
                        ▼
                 Resource Manager
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Embedded       External      Generated
       Resources      Assets        Resources
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                 Resource Resolver
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
          Memory      Stream     MMap/ZeroCopy
          Resource    Resource      Resource
             │          │             │
             └──────────┼─────────────┘
                        ▼
                 Application API
```

`596` sẽ hợp nhất resource model đang được phân tán giữa `469`, `593`, GUI/media subsystems và filesystem layer thành một **resource abstraction thống nhất**, nhưng vẫn giữ nguyên nguyên tắc: asset immutable, content-addressed, có thể stream/memory-map và không ép toàn bộ resource phải load vào RAM.