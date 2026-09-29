# BOOTSTRAP-601 — NATIVE APPLICATION CONFIGURATION, SECRETS, ENVIRONMENT & DEPLOYMENT RUNTIME 5.0

**Status:** SPECIFICATION  
**Phase:** Bootstrap / Native Runtime Architecture  
**Task ID:** `BOOTSTRAP-601`  
**Depends on:** `BOOTSTRAP-600`  
**Priority:** High  
**Target:** Axiom Core / Native Runtime / Application Infrastructure

---

## 601.0. Mục tiêu

Axiom cần một hệ thống native thống nhất để ứng dụng đọc và quản lý:

- application configuration;
- environment configuration;
- command-line configuration;
- user configuration;
- machine configuration;
- deployment configuration;
- runtime feature flags;
- credentials/secrets;
- configuration profiles;
- development/staging/production environments;
- immutable deployment parameters.

Mục tiêu là tránh tình trạng mỗi ứng dụng phải tự xây:

```text
.env parser
JSON config
INI parser
registry adapter
secret loader
environment parser
command-line parser
```

nhưng **không biến Configuration Runtime thành một framework nặng**.

---

# 601.1. Design Principles

### P1 — Configuration ≠ State

`BOOTSTRAP-600` quản lý state.

`BOOTSTRAP-601` quản lý **inputs vào application runtime**.

```text
Configuration
    ↓
Application initialization
    ↓
Runtime state
```

Configuration không tự động trở thành persistent application state.

---

### P2 — Secret ≠ Configuration thường

Secret phải có lifecycle và protection khác configuration thông thường.

```text
Config
Secret
State
Cache
```

là bốn loại dữ liệu khác nhau.

---

### P3 — Explicit precedence

Khi nhiều nguồn cùng định nghĩa một giá trị, precedence phải deterministic.

---

### P4 — Native first

Core phải hỗ trợ:

```text
CLI
environment
files
embedded defaults
OS-native mechanisms
```

mà không cần third-party dependency.

---

### P5 — Type-safe

Configuration không nên trả mọi thứ dưới dạng:

```text
String
```

rồi để application tự parse.

Ví dụ:

```axiom
port: u16
debug: bool
timeout: Duration
workers: u32
```

---

# 601.2. Configuration Object

API cơ bản:

```axiom
let config = ApplicationConfig.load()
```

Configuration object là read-oriented.

---

# 601.3. Configuration Declaration

Application có thể khai báo:

```axiom
config AppConfig {
    host: String = "127.0.0.1"
    port: u16 = 8000
    debug: bool = false
    timeout: Duration = 30s
}
```

Compiler sinh metadata tương ứng.

---

# 601.4. Typed Configuration

Application sử dụng:

```axiom
let port: u16 = config.port
```

thay vì:

```axiom
let port = parse_u16(env("PORT"))
```

---

# 601.5. Configuration Sources

Axiom hỗ trợ các source:

```text
1. Built-in defaults
2. Application config
3. User config
4. Machine config
5. Environment variables
6. Command-line arguments
7. Deployment/runtime overrides
```

Thứ tự chính xác phải deterministic và configurable.

---

# 601.6. Default Configuration

Default value được compile vào application metadata:

```axiom
config AppConfig {
    workers: u32 = 4
}
```

Nếu không có external override:

```text
workers = 4
```

---

# 601.7. Configuration Precedence

Default policy:

```text
deployment/runtime override
        ↓
command line
        ↓
environment
        ↓
user config
        ↓
machine config
        ↓
application config
        ↓
built-in default
```

Nguồn cao hơn override nguồn thấp hơn.

---

# 601.8. Explicit Precedence Metadata

Tooling phải có thể giải thích:

```text
config.port = 9000

source:
    environment variable PORT
```

thay vì chỉ trả về giá trị cuối cùng.

---

# 601.9. Configuration Origin

Mỗi resolved value có thể có metadata:

```text
ConfigOrigin {
    source
    location
    key
}
```

Ví dụ:

```text
source = Environment
key = PORT
```

---

# 601.10. Configuration File

Axiom phải có native configuration format.

Ưu tiên:

```text
compact
typed
human-readable
commentable
deterministic
```

Reference syntax:

```axiom
application {
    port = 8000
    debug = false

    server {
        host = "127.0.0.1"
        workers = 4
    }
}
```

Format này được gọi là:

```text
AXCFG
```

---

# 601.11. AXCFG

AXCFG không phải programming language.

Nó chỉ hỗ trợ:

```text
string
integer
float
boolean
duration
size
array
map
object
null
```

Không cho phép arbitrary function execution.

---

# 601.12. No Code Execution

Configuration không được chứa:

```text
executable code
function calls
loops
imports có side effects
```

Mục tiêu:

> Configuration phải là data, không phải program.

---

# 601.13. Configuration Parser

Parser phải:

- UTF-8;
- deterministic;
- bounded;
- zero third-party dependency;
- có error location.

Ví dụ:

```text
config.axcfg:14:17
invalid integer
```

---

# 601.14. Environment Variables

API:

```axiom
env.get("PORT")
```

hoặc typed:

```axiom
env.get_u16("PORT")
```

Nhưng configuration layer nên ưu tiên:

```axiom
config.port
```

---

# 601.15. Environment Naming

Configuration field:

```text
server.port
```

có thể map:

```text
AXIOM_SERVER_PORT
```

Default naming convention:

```text
uppercase
dot → underscore
```

---

# 601.16. Explicit Environment Mapping

Có thể:

```axiom
config AppConfig {
    port @env("PORT"): u16 = 8000
}
```

---

# 601.17. Command-Line Integration

Axiom application runtime có thể expose:

```axiom
app.args
```

Configuration schema có thể tự động map CLI:

```text
--port 9000
--debug
--workers 8
```

---

# 601.18. Generated CLI Schema

Compiler có thể generate:

```text
--help
--version
--config
```

từ application metadata.

---

# 601.19. Configuration Validation

Sau resolution:

```text
sources
 ↓
merge
 ↓
parse
 ↓
type conversion
 ↓
validation
 ↓
ApplicationConfig
```

---

# 601.20. Validation Rules

Ví dụ:

```axiom
config AppConfig {
    port: u16 where port > 0
    workers: u32 where workers >= 1
}
```

---

# 601.21. Cross-Field Validation

Có thể:

```axiom
validate AppConfig {
    assert tls.enabled implies tls.certificate != null
}
```

---

# 601.22. Configuration Error

Typed error:

```axiom
enum ConfigError {
    NotFound
    InvalidSyntax
    InvalidType
    InvalidValue
    DuplicateKey
    UnknownKey
    MissingRequired
    SourceUnavailable
    SecretUnavailable
}
```

---

# 601.23. Unknown Configuration Keys

Default:

```text
warning
```

hoặc strict mode:

```text
error
```

Application có thể chọn:

```axiom
config.policy {
    unknown_keys = .Error
}
```

---

# 601.24. Required Configuration

```axiom
config AppConfig {
    database_url: String required
}
```

Application startup phải fail nếu không có value.

---

# 601.25. Optional Configuration

```axiom
cache_path: Path?
```

Không có value:

```text
null
```

---

# 601.26. Secret Declaration

Secret phải được khai báo riêng:

```axiom
secret DatabasePassword
```

hoặc:

```axiom
config AppConfig {
    database_password: Secret<String>
}
```

---

# 601.27. Secret Type

`Secret<T>` là opaque type.

Không cho phép implicit conversion:

```axiom
String = Secret<String>
```

---

# 601.28. Secret Access

Explicit unwrap:

```axiom
let password = secret.expose()
```

Việc expose phải là một operation rõ ràng.

---

# 601.29. Secret Logging Protection

Runtime/debugger không được mặc định in:

```text
password
token
private_key
api_key
```

---

# 601.30. Secret Formatting

Không cho phép implicit:

```axiom
log("password={}", password)
```

nếu type là `Secret<T>`.

Phải explicit:

```text
secret.redacted()
```

hoặc API tương đương.

---

# 601.31. Secret Redaction

Default display:

```text
<redacted>
```

---

# 601.32. Secret Sources

Native runtime có thể lấy secret từ:

```text
environment
OS credential store
protected file
deployment secret provider
stdin
```

Core không phụ thuộc cloud provider cụ thể.

---

# 601.33. Environment Secret Warning

Secret qua environment variable được hỗ trợ nhưng tooling có thể cảnh báo rằng environment có thể bị OS/process tooling quan sát.

---

# 601.34. Secret Persistence

Secret không được tự động ghi vào `BOOTSTRAP-600` application state.

Nếu developer muốn persist:

```axiom
persistent secret ...
```

phải có security policy tương ứng.

---

# 601.35. Secret Encryption

Axiom Core không tự định nghĩa cryptographic algorithm mới.

Runtime security layer sẽ cung cấp implementation bằng các primitive/platform facilities phù hợp.

---

# 601.36. No Homemade Cryptography

Axiom tuyệt đối không khuyến khích application tự implement:

```text
AES
ChaCha
RSA
ECC
KDF
```

trong configuration runtime.

Crypto subsystem riêng sẽ được đặc tả ở task phù hợp.

---

# 601.37. Secret Lifetime

Secret value trong memory phải có lifecycle rõ ràng.

Khi không còn cần:

```text
destroy
```

theo deterministic lifetime semantics.

---

# 601.38. Secret Memory

Runtime có thể cung cấp:

```text
protected memory
```

trên OS hỗ trợ.

Nhưng core semantics không giả định rằng OS luôn có secure memory tuyệt đối.

---

# 601.39. Configuration Immutability

Sau:

```axiom
let config = app.config()
```

configuration mặc định immutable.

Điều này tránh:

```text
thread A reads config
thread B changes config
```

gây race.

---

# 601.40. Runtime Reconfiguration

Nếu application cần dynamic configuration:

```axiom
config.reload()
```

phải tạo một **configuration snapshot mới**.

Không mutate object configuration đang được thread khác sử dụng.

---

# 601.41. Configuration Version

Mỗi resolved configuration có:

```text
config_version
```

Ví dụ:

```text
configuration #42
```

---

# 601.42. Reload Semantics

Flow:

```text
old config
    ↓
load new sources
    ↓
parse
    ↓
validate
    ↓
new immutable config
    ↓
publish atomically
```

Nếu validation fail:

```text
old config remains active
```

---

# 601.43. Configuration Watch

API:

```axiom
config.watch()
```

Có thể phát:

```text
ConfigChanged
```

sau khi new config đã được validate.

---

# 601.44. Atomic Configuration Publication

Không có trạng thái:

```text
port = 9000
workers = old
timeout = new
```

do partial reload.

Một configuration version phải được publish atomically.

---

# 601.45. Configuration Snapshot

```axiom
let cfg = app.config.snapshot()
```

Snapshot immutable.

Thread-safe bằng semantics thay vì lock toàn application.

---

# 601.46. Profiles

Application có thể định nghĩa:

```text
development
test
staging
production
```

Ví dụ:

```text
config/
    base.axcfg
    development.axcfg
    production.axcfg
```

---

# 601.47. Profile Selection

Profile được chọn bằng:

```text
--profile production
```

hoặc:

```text
AXIOM_PROFILE=production
```

---

# 601.48. Profile Merge

```text
base
 +
profile
 +
environment
 +
CLI
```

tạo final configuration.

---

# 601.49. Profile Safety

Production profile không được vô tình override bằng development setting nếu precedence policy không cho phép.

---

# 601.50. Build-Time vs Runtime Configuration

Phân biệt:

```text
Build Configuration
Runtime Configuration
Deployment Configuration
Application State
```

---

# 601.51. Build Configuration

Ví dụ:

```text
target = x86_64-linux
optimization = release
features = gpu
```

được xử lý bởi toolchain.

Không nằm trong runtime config.

---

# 601.52. Runtime Configuration

Ví dụ:

```text
port
workers
logging level
cache size
```

được đọc khi application chạy.

---

# 601.53. Deployment Configuration

Ví dụ:

```text
service identity
resource limits
environment
endpoint
```

được cung cấp bởi deployment environment.

---

# 601.54. Application State

Ví dụ:

```text
opened documents
user workspace
last cursor
```

thuộc `BOOTSTRAP-600`.

---

# 601.55. Configuration → State Boundary

Configuration có thể khởi tạo state:

```text
configuration
   ↓
initial state
```

nhưng sau initialization:

```text
state != config
```

---

# 601.56. Config Precedence Does Not Apply to State

State recovery không được overwrite bằng config mỗi lần startup nếu state đã tồn tại.

Ví dụ:

```text
config.theme = dark
state.theme = light
```

Application phải quyết định migration semantics.

---

# 601.57. Configuration Schema

Compiler-generated schema:

```text
ConfigDescriptor {
    name
    type
    default
    required
    source_mapping
    validation
    secret
}
```

---

# 601.58. Schema Introspection

Tooling có thể query:

```axiom
config.schema()
```

để tạo:

```text
documentation
CLI help
GUI settings editor
validation
deployment templates
```

---

# 601.59. AI-Friendly Configuration Metadata

Metadata phải mô tả được:

```text
key
type
default
description
allowed values
secret
required
source
```

Ví dụ:

```text
server.port
type: u16
default: 8000
range: 1..65535
env: AXIOM_SERVER_PORT
```

---

# 601.60. Documentation Generation

Toolchain có thể generate:

```text
axiom config docs
```

từ config schema.

---

# 601.61. Configuration Diff

Runtime/tooling phải hỗ trợ:

```text
config diff old new
```

Ví dụ:

```text
server.port: 8000 → 9000
workers: 4 → 8
```

---

# 601.62. Sensitive Diff

Secret changes phải hiển thị:

```text
database.password: <changed>
```

không hiển thị plaintext.

---

# 601.63. Configuration Export

Có thể export effective configuration:

```text
axiom config export
```

nhưng secret mặc định:

```text
<redacted>
```

---

# 601.64. Configuration Import

Import phải validate schema trước khi activate.

---

# 601.65. Atomic Config File Update

Nếu runtime cung cấp:

```axiom
config.save()
```

phải dùng atomic replacement semantics.

Không ghi trực tiếp file đang active theo cách có thể tạo file hỏng sau crash.

---

# 601.66. Configuration Backup

Trước destructive rewrite, runtime có thể giữ:

```text
config.previous
```

theo retention policy.

---

# 601.67. Config Recovery

Nếu config file bị truncate:

```text
load
 ↓
invalid
 ↓
try previous valid version
```

nếu policy cho phép.

Configuration recovery đơn giản hơn application-state recovery và không sử dụng journal của `BOOTSTRAP-600` mặc định.

---

# 601.68. Machine Configuration

OS-wide configuration có thể nằm ở:

```text
/etc
registry
Application Support
ProgramData
```

nhưng Axiom API phải abstract path/platform details.

---

# 601.69. User Configuration

User-specific configuration:

```text
~/.config/<app>
```

hoặc platform-native equivalent.

Không hard-code Linux path vào core.

---

# 601.70. Application Configuration

Installed application configuration có thể nằm ở application directory hoặc OS-native location.

---

# 601.71. Configuration Search Paths

Runtime cung cấp logical locations:

```axiom
paths.config.user()
paths.config.machine()
paths.config.application()
paths.cache()
paths.data()
paths.state()
```

Các path này phải thuộc filesystem/platform runtime.

---

# 601.72. Config Directory Separation

Không trộn:

```text
config
data
cache
state
logs
```

Ví dụ:

```text
config/ → settings
data/   → user content
cache/  → disposable data
state/  → crash-resilient runtime state
logs/   → diagnostics
```

---

# 601.73. Cache Is Disposable

Cache có thể bị xóa mà application vẫn hoạt động.

---

# 601.74. Config Is Reconstructible

Configuration file có thể được regenerate từ defaults + deployment inputs nếu policy cho phép.

---

# 601.75. State Is Authoritative

Application state có semantics khác:

```text
state loss ≠ config loss
```

State cần recovery guarantees mạnh hơn configuration.

---

# 601.76. Environment Snapshot

Khi application start:

```axiom
let env = Environment.snapshot()
```

Snapshot immutable.

---

# 601.77. Why Snapshot

Environment của process thường không nên thay đổi tùy tiện trong runtime.

Axiom ưu tiên:

```text
process startup environment
→ immutable snapshot
```

---

# 601.78. Process Arguments Snapshot

Tương tự:

```axiom
app.args
```

phải là immutable process arguments.

---

# 601.79. Configuration Security

Configuration parser phải chống:

```text
path traversal
resource exhaustion
oversized values
recursive structures
malformed UTF-8
```

---

# 601.80. Include Directive

AXCFG có thể hỗ trợ:

```text
include "server.axcfg"
```

nhưng include phải:

- deterministic;
- có giới hạn depth;
- detect cycle;
- có root policy.

---

# 601.81. Include Security

Application không nên mặc định cho config include arbitrary paths.

Có policy:

```axiom
config.policy {
    allowed_roots = [...]
}
```

---

# 601.82. Environment Expansion

Có thể hỗ trợ:

```text
"${HOME}/data"
```

nhưng expansion phải là data substitution, không shell execution.

---

# 601.83. No Shell Evaluation

Không:

```text
$(command)
```

hoặc tương đương.

Configuration không được trở thành shell script.

---

# 601.84. Typed Duration

AXCFG phải hỗ trợ:

```text
timeout = 30s
retry_delay = 250ms
```

map trực tiếp tới Axiom `Duration`.

---

# 601.85. Typed Size

```text
cache_size = 512MiB
```

map tới native size type.

---

# 601.86. Typed Paths

Configuration path được parse thành:

```text
Path
```

thay vì plain string khi schema yêu cầu.

---

# 601.87. Enum Configuration

```axiom
config {
    log_level: LogLevel = .Info
}
```

Configuration parser hỗ trợ symbolic enum values.

---

# 601.88. Enum Validation

Invalid:

```text
log_level = "verbose123"
```

phải fail tại configuration loading.

---

# 601.89. Lists

```text
workers.allowed_hosts = [
    "127.0.0.1",
    "192.168.1.10"
]
```

---

# 601.90. Maps

```text
labels = {
    environment = "production"
    region = "asia"
}
```

---

# 601.91. Configuration Merge Semantics

Map:

```text
base:
    server:
        port = 8000
        workers = 4

override:
    server:
        workers = 8
```

kết quả:

```text
port = 8000
workers = 8
```

---

# 601.92. Array Merge

Default:

```text
array = replace
```

không implicit concatenate.

Nếu muốn append phải khai báo operation rõ ràng.

---

# 601.93. Null Semantics

`null` phải có semantics rõ:

```text
unset
```

hoặc:

```text
explicitly null
```

Schema phải phân biệt nếu cần.

---

# 601.94. Secret Reference

Production deployment có thể dùng:

```text
secret://database/password
```

thay vì lưu plaintext.

Resolver của secret provider trả:

```text
Secret<String>
```

---

# 601.95. Secret Provider Interface

Conceptual:

```text
SecretProvider {
    resolve(name)
}
```

Native providers:

```text
EnvironmentSecretProvider
FileSecretProvider
OSSecretProvider
```

---

# 601.96. External Provider

Cloud/enterprise secret systems có thể implement provider adapter.

Core không phụ thuộc vendor.

---

# 601.97. Configuration Source Interface

Tương tự:

```text
ConfigSource {
    load()
}
```

Native sources:

```text
DefaultSource
FileSource
EnvironmentSource
CommandLineSource
DeploymentSource
```

---

# 601.98. Source Ordering

Sources được compose:

```text
Source[]
```

theo explicit priority.

Không phụ thuộc thứ tự plugin load.

---

# 601.99. Deterministic Resolution

Cùng:

```text
sources
+
source contents
+
schema
```

phải cho cùng:

```text
resolved configuration
```

---

# 601.100. Configuration Hash

Resolved config có thể tạo:

```text
config.fingerprint()
```

để:

```text
deployment tracking
cache invalidation
diagnostics
reproducibility
```

---

# 601.101. Secret Exclusion From Fingerprint

Secret plaintext không được đưa trực tiếp vào diagnostic fingerprint.

Có thể dùng opaque identifier/version từ secret provider.

---

# 601.102. Reproducible Configuration

Toolchain phải có khả năng ghi lại:

```text
config source versions
profile
schema version
```

để tái tạo runtime configuration.

---

# 601.103. Deployment Manifest

Axiom có thể định nghĩa:

```text
AXDEP
```

deployment metadata:

```text
application
version
target
profile
required capabilities
configuration schema
```

---

# 601.104. Deployment Manifest ≠ Installer

`AXDEP` chỉ mô tả deployment.

Installer/package manager là subsystem khác.

---

# 601.105. Application Identity

Runtime cần metadata:

```text
application_id
application_name
version
build_id
```

---

# 601.106. Build ID

Mỗi native binary có thể chứa:

```text
build_id
```

để diagnostics biết chính xác binary nào đang chạy.

---

# 601.107. Configuration Compatibility

Application binary có:

```text
config_schema_version
```

Nếu config version incompatible:

```text
ConfigError.VersionMismatch
```

---

# 601.108. Migration

Configuration migration có thể:

```text
config v1
   ↓
migration
   ↓
config v2
```

Migration phải không làm mất dữ liệu ngoài policy.

---

# 601.109. Config Migration ≠ State Migration

Hai migration system độc lập:

```text
Configuration Migration
Application State Migration
```

State migration thuộc `BOOTSTRAP-600`.

---

# 601.110. Runtime Feature Flags

Configuration có thể định nghĩa:

```axiom
feature gpu_backend: bool = true
```

Feature flag không được biến thành dynamic code loading.

---

# 601.111. Compile-Time Feature

Compile-time:

```text
when feature("gpu")
```

là compiler/build feature.

Runtime flag:

```text
config.gpu_backend
```

là runtime behavior.

Không đánh đồng hai loại.

---

# 601.112. Capability Discovery

Application có thể kiểm tra:

```axiom
runtime.capabilities()
```

Ví dụ:

```text
GPU
AVX2
AVX-512
Vulkan
Metal
DirectX
WASM
```

Configuration có thể yêu cầu capability:

```axiom
require capability GPU
```

---

# 601.113. Capability Failure

Nếu deployment yêu cầu capability không tồn tại:

```text
startup failure
```

với typed diagnostic.

---

# 601.114. Configuration and Native Targets

Configuration runtime phải hoạt động nhất quán trên:

```text
Windows
Linux
macOS
iOS
Android
WASM
```

trong phạm vi platform capabilities.

---

# 601.115. Restricted Platforms

Trên iOS/WASM, filesystem/config paths có thể khác.

Axiom runtime phải expose logical locations thay vì giả định filesystem layout.

---

# 601.116. Embedded Configuration

Tiny applications có thể embed configuration:

```axiom
const config AppConfig = ...
```

Không cần file parser.

---

# 601.117. Zero-Config Application

Application có thể chạy chỉ với:

```text
compiled defaults
```

không cần external config file.

---

# 601.118. Configuration File Optionality

File configuration mặc định:

```text
optional
```

trừ khi schema đánh dấu required.

---

# 601.119. Configuration Reload Failure

Nếu reload fail:

```text
old configuration remains active
```

Đây là invariant quan trọng.

---

# 601.120. Atomic Config Activation

Flow:

```text
Load
 ↓
Parse
 ↓
Resolve
 ↓
Validate
 ↓
Build immutable snapshot
 ↓
Publish
```

Chỉ publish bước cuối.

---

# 601.121. Configuration Concurrency

Multiple readers:

```text
lock-free/read-only
```

là target.

Reload chỉ thay root pointer/snapshot reference theo native synchronization primitive.

---

# 601.122. No Global Config Lock

Không sử dụng global mutex cho mọi configuration read.

---

# 601.123. Configuration Access Cost

Resolved configuration read target:

```text
O(1)
```

đối với field trực tiếp.

Không parse file mỗi lần:

```axiom
config.port
```

---

# 601.124. Lazy Source Loading

Source có thể lazy-load khi cần, nhưng sau resolution final config phải immutable.

---

# 601.125. Startup Pipeline

Native application startup:

```text
OS process
   ↓
runtime init
   ↓
platform paths
   ↓
environment snapshot
   ↓
CLI snapshot
   ↓
configuration sources
   ↓
resolve
   ↓
validate
   ↓
secret resolution
   ↓
application init
   ↓
state recovery
   ↓
application ready
```

Thứ tự giữa secret resolution và state recovery có thể thay đổi khi state schema cần secret, nhưng không được tạo dependency cycle.

---

# 601.126. State Interaction

Nếu `BOOTSTRAP-600` state cần configuration:

```text
config
 ↓
state recovery policy
```

nhưng recovered state vẫn là authoritative state.

---

# 601.127. Logging Configuration

Logging subsystem có thể lấy:

```text
config.logging
```

nhưng logging phải có bootstrap defaults trước khi full config load hoàn tất.

---

# 601.128. Early Startup Logging

Trước configuration resolution:

```text
minimal logger
```

được dùng.

Không được crash chỉ vì logging configuration chưa tồn tại.

---

# 601.129. Configuration Diagnostics

Error phải hiển thị:

```text
source
key
line
column
expected type
actual value
```

nhưng secret phải redacted.

---

# 601.130. Example Error

```text
Configuration error:

key: server.port
source: environment
variable: PORT
value: <redacted if secret>
expected: u16
received: invalid integer
```

---

# 601.131. Configuration Schema Documentation

Schema field nên hỗ trợ description:

```axiom
config AppConfig {
    /// TCP listening port.
    port: u16 = 8000
}
```

Tooling dùng comment/document metadata để generate docs.

---

# 601.132. Human-Friendly Config

Configuration file phải ưu tiên khả năng chỉnh sửa thủ công.

---

# 601.133. Machine-Friendly Config

Parser phải deterministic và không phụ thuộc whitespace ngoài những rule đã định nghĩa.

---

# 601.134. UTF-8

AXCFG mặc định UTF-8.

Identifiers/config strings phải tuân theo Unicode rules của Axiom.

---

# 601.135. Unicode Normalization

Runtime không tự động normalize configuration strings nếu schema không yêu cầu.

Điều này tránh thay đổi dữ liệu người dùng ngoài ý muốn.

---

# 601.136. Comments

AXCFG hỗ trợ comments.

Comments không ảnh hưởng semantic configuration.

---

# 601.137. Duplicate Keys

Default:

```text
error
```

Không silently lấy key cuối cùng.

---

# 601.138. Deterministic Maps

Nếu map iteration cần deterministic serialization, runtime phải có ordered serialization mode.

---

# 601.139. Configuration Serialization

Resolved config có thể serialize lại nhưng không nhất thiết giữ nguyên:

```text
comments
source ordering
formatting
```

---

# 601.140. Secret Serialization

Resolved configuration export mặc định không serialize secret value.

---

# 601.141. Redacted Export

Ví dụ:

```text
database {
    host = "db.internal"
    password = "<redacted>"
}
```

---

# 601.142. Environment Export

Tooling có thể generate:

```text
AXIOM_SERVER_PORT=8000
AXIOM_SERVER_WORKERS=4
```

nhưng secret vẫn redacted.

---

# 601.143. Configuration Testing

Test harness phải cho phép inject source:

```axiom
config.test {
    environment {
        PORT = "9000"
    }
}
```

Không cần sửa process environment thật.

---

# 601.144. In-Memory Config Source

Testing:

```axiom
ConfigSource.memory(...)
```

---

# 601.145. Configuration Fuzzing

Parser phải được fuzz-test với:

```text
random bytes
huge strings
deep nesting
invalid UTF-8
truncated files
duplicate keys
```

---

# 601.146. Parser Resource Limits

Có giới hạn:

```text
max file size
max nesting depth
max key length
max string length
max collection elements
```

---

# 601.147. No Unbounded Recursion

Configuration parser không được phụ thuộc recursive parser depth vô hạn.

---

# 601.148. Configuration Performance

Mục tiêu:

```text
startup parse cost = O(config size)
```

Sau resolution:

```text
field access = O(1)
```

---

# 601.149. Small Application Optimization

Tiny native application có thể bỏ toàn bộ external configuration machinery nếu không sử dụng.

Compiler/linker phải dead-strip unused configuration runtime.

---

# 601.150. Runtime Footprint

Configuration support không được làm mọi Axiom executable lớn lên đáng kể nếu application không dùng:

```text
AXCFG
secrets
reload
profiles
```

---

# 601.151. Static Linking

Configuration runtime phải tương thích static linking.

---

# 601.152. No Third-Party Runtime Dependency

Reference implementation chỉ sử dụng:

```text
Axiom runtime
OS APIs
Axiom standard library
```

---

# 601.153. Configuration Backend

Abstract:

```text
ConfigSource
```

Concrete:

```text
BuiltinConfigSource
FileConfigSource
EnvironmentConfigSource
CommandLineConfigSource
MemoryConfigSource
```

---

# 601.154. Secret Backend

Abstract:

```text
SecretProvider
```

Không hard-code cloud provider.

---

# 601.155. Deployment Backend

Abstract:

```text
DeploymentSource
```

cho phép container/service manager/platform tích hợp.

---

# 601.156. Container Environment

Container có thể cung cấp:

```text
environment
mounted config
mounted secrets
CLI
```

Axiom không cần container-specific core.

---

# 601.157. Service Environment

Native services có thể dùng:

```text
configuration
environment
service manager integration
```

nhưng service manager API thuộc platform layer.

---

# 601.158. Desktop Application

Desktop application có thể có:

```text
machine config
user config
session state
application state
```

mỗi loại ở đúng subsystem.

---

# 601.159. CLI Application

CLI có thể chỉ cần:

```text
defaults
environment
arguments
```

và linker loại bỏ phần không dùng.

---

# 601.160. GUI Application

GUI có thể expose configuration schema cho Settings UI tự động:

```text
schema
 ↓
generated settings UI
```

đây là tooling/application framework phía trên, không phải core UI.

---

# 601.161. AI Application

AI application có thể khai báo:

```axiom
config ModelConfig {
    model_path: Path
    device: Device = .auto
    batch_size: u32 = 1
}
```

Runtime type system xử lý configuration như data bình thường.

---

# 601.162. Configuration and GPU

GPU selection:

```text
device = .auto
```

được resolve bởi application/runtime capability layer.

Không hard-code CUDA vào configuration core.

---

# 601.163. Configuration Provenance

Mỗi field có thể truy xuất:

```text
effective value
source
schema
version
```

Phục vụ debugging/deployment.

---

# 601.164. Configuration Explain

CLI:

```text
axiom config explain server.port
```

có thể trả:

```text
effective value: 9000
source: environment
key: PORT
default: 8000
```

---

# 601.165. Configuration Lock

Deployment có thể đánh dấu field:

```text
immutable
```

Application không được runtime override.

---

# 601.166. Deployment-Managed Field

Ví dụ:

```axiom
config {
    environment: String @deployment_managed
}
```

---

# 601.167. User-Managed Field

Ngược lại:

```axiom
config {
    theme: Theme @user_managed
}
```

---

# 601.168. Configuration Ownership

Mỗi field có thể xác định:

```text
developer
deployment
machine
user
runtime
```

ownership.

---

# 601.169. Conflict Detection

Nếu policy cấm override:

```text
deployment owns server.port
```

mà CLI:

```text
--port 9000
```

runtime phải:

```text
error
```

hoặc policy-defined behavior.

Không silently violate ownership.

---

# 601.170. Configuration Policy

```axiom
config.policy {
    precedence = [...]
    unknown_keys = .Error
    allow_env_override = true
    allow_cli_override = true
}
```

---

# 601.171. Secure Production Policy

Production có thể:

```axiom
config.policy {
    allow_local_override = false
    allow_cli_override = false
}
```

---

# 601.172. Configuration Snapshot in Diagnostics

Crash diagnostics có thể lưu:

```text
config fingerprint
config schema version
profile
```

không lưu secret/plaintext config mặc định.

---

# 601.173. Crash Interaction

Nếu application crash:

```text
BOOTSTRAP-600
    ↓
recover state
```

configuration phải được load lại từ trusted sources.

Không lưu toàn bộ configuration vào crash state journal.

---

# 601.174. Last Known Configuration

Application có thể tùy chọn persist:

```text
configuration fingerprint
```

để diagnostics biết state được tạo dưới config nào.

---

# 601.175. Configuration Fingerprint in State

Checkpoint metadata có thể chứa:

```text
config_schema_version
config_fingerprint
application_version
```

Điều này giúp phát hiện:

```text
state created under different configuration
```

---

# 601.176. State/Config Compatibility

Application có thể định nghĩa:

```axiom
validate_state_config(state, config)
```

Nếu incompatible:

```text
migration
safe fallback
or startup error
```

---

# 601.177. No Automatic Destructive Migration

Runtime không được tự động reset user state chỉ vì config/schema mismatch.

---

# 601.178. Configuration Rollback

Nếu application hỗ trợ config persistence:

```text
config version 10
 ↓ bad change
config version 11
 ↓ validation/runtime failure
rollback
 ↓
config version 10
```

---

# 601.179. Config Transaction

Config file updates có thể sử dụng atomic transaction semantics:

```text
prepare
write
validate
activate
```

Không nhất thiết dùng State Journal.

---

# 601.180. Separation From State Journal

`BOOTSTRAP-600` journal:

```text
application state durability
```

`BOOTSTRAP-601` config update:

```text
configuration activation
```

Hai journal không được phụ thuộc lẫn nhau.

---

# 601.181. Configuration Package

Deployment có thể bundle:

```text
application
config schema
default config
documentation
```

Secret không nên bundle plaintext.

---

# 601.182. Secret Injection

Deployment system inject secret tại runtime:

```text
deployment
 ↓
SecretProvider
 ↓
Secret<T>
```

---

# 601.183. Secret Rotation

Provider có thể hỗ trợ:

```axiom
secret.watch()
```

Nếu secret đổi:

```text
new secret version
```

Application nhận event.

---

# 601.184. Secret Rotation Atomicity

Application không được nhìn thấy secret nửa cập nhật.

Secret snapshot mới được publish atomically.

---

# 601.185. Secret Rotation and Existing Connections

Runtime không tự động restart network connections chỉ vì secret đổi.

Application policy quyết định.

---

# 601.186. Configuration Hot Reload

Hot reload phải explicit:

```axiom
config.enable_reload()
```

Không mặc định poll filesystem vô hạn.

---

# 601.187. Reload Mechanism

Native backend có thể dùng:

```text
filesystem notification
timer
explicit reload
```

---

# 601.188. Resource Usage

Configuration watcher phải:

```text
event-driven
```

nếu OS hỗ trợ, thay vì polling liên tục.

---

# 601.189. Configuration Lifecycle

```text
UNINITIALIZED
    ↓
LOADING
    ↓
RESOLVING
    ↓
VALIDATING
    ↓
READY
    ↓
RELOADING
    ↓
READY
```

---

# 601.190. Failure Lifecycle

Nếu initial load fail:

```text
LOADING
 ↓
FAILED
```

Application startup có thể terminate.

Nếu reload fail:

```text
RELOADING
 ↓
old READY config remains
```

---

# 601.191. Configuration API Example

```axiom
config AppConfig {
    host: String = "127.0.0.1"
    port: u16 = 8000
    workers: u32 = 4
    timeout: Duration = 30s

    database_url: Secret<String> required
}

fn main() -> Result {
    let app = Application.init()?

    let config = app.config.load::<AppConfig>()?

    server.start(
        host: config.host,
        port: config.port,
        workers: config.workers,
        timeout: config.timeout
    )?

    app.run()
}
```

---

# 601.192. CLI Example

```text
myapp --port 9000 --workers 8 --profile production
```

Resolved:

```text
port    = 9000
workers = 8
profile = production
```

---

# 601.193. File Example

```text
server {
    host = "0.0.0.0"
    port = 8000
    workers = 4
    timeout = 30s
}
```

---

# 601.194. Environment Example

```text
AXIOM_SERVER_PORT=9000
AXIOM_SERVER_WORKERS=8
```

---

# 601.195. Resolution Example

```text
default       port = 8000
user config   port = 8080
environment   port = 8500
CLI           port = 9000

effective     port = 9000
```

---

# 601.196. Configuration Test Example

```axiom
test "config precedence" {
    source defaults {
        port = 8000
    }

    source environment {
        PORT = "9000"
    }

    let cfg = resolve<AppConfig>()?

    assert cfg.port == 9000
}
```

---

# 601.197. Secret Test

Test runtime phải cung cấp fake provider:

```axiom
test "secret resolution" {
    secrets.set("db/password", "test")
    ...
}
```

Secret không được ghi vào test logs.

---

# 601.198. Parser Acceptance Tests

Bắt buộc:

```text
valid scalar
valid arrays
valid maps
nested objects
comments
unicode
duration
size
enum
null
include
```

---

# 601.199. Parser Rejection Tests

Bắt buộc:

```text
duplicate key
invalid UTF-8
unterminated string
invalid number
invalid duration
invalid nesting
oversized input
include cycle
unknown type
```

---

# 601.200. Bootstrap Acceptance Criteria

`BOOTSTRAP-601` chỉ hoàn thành khi:

### Configuration

- typed schema;
- defaults;
- file source;
- environment source;
- CLI source;
- precedence;
- validation;
- profiles;
- immutable snapshots;
- reload;
- diagnostics.

### Secrets

- `Secret<T>`;
- redaction;
- provider abstraction;
- deterministic lifetime;
- no accidental serialization;
- rotation-compatible architecture.

### Deployment

- application identity;
- build ID;
- configuration schema version;
- deployment source;
- capability requirements;
- logical platform paths.

### Performance

- O(config size) startup;
- O(1) resolved field access;
- no global config lock;
- unused features dead-strippable;
- no third-party runtime dependency.

### Security

- bounded parser;
- no arbitrary code execution;
- no shell expansion;
- secret redaction;
- safe file handling;
- no silent secret persistence.

---

# 601.201. Architecture Decision

Axiom 5.0 chốt:

```text
Typed Configuration Schema
          +
Deterministic Source Resolution
          +
Immutable Configuration Snapshot
          +
Atomic Reload
          +
Dedicated Secret Type
          +
Provider-Based Secret Resolution
          +
Deployment/Capability Metadata
```

và giữ ranh giới rõ:

```text
                ┌─────────────────────┐
                │ Configuration       │
                │ BOOTSTRAP-601       │
                └──────────┬──────────┘
                           │
                    Application Init
                           │
                ┌──────────▼──────────┐
                │ Application Runtime │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │ Persistent State    │
                │ BOOTSTRAP-600       │
                └─────────────────────┘
```

Điểm quan trọng: **configuration không trở thành state, state không bị overwrite bởi configuration một cách ngầm định, và secret không được coi như String thông thường.**

---

# 601.202. Core Principle

Axiom application phải có khả năng đi từ:

```text
Native Binary
    +
Deployment Environment
    +
Typed Configuration
    +
Secrets
```

đến:

```text
Deterministic Application Initialization
```

mà không cần một configuration framework bên thứ ba.

Đồng thời, compiler/linker phải loại bỏ toàn bộ infrastructure không được application sử dụng, để một CLI nhỏ không phải mang theo toàn bộ configuration/secret/deployment runtime.

---

# 601.203. Task completion

```text
BOOTSTRAP-600
Native State / Session / Checkpoint / Recovery
             ↓
BOOTSTRAP-601
Configuration / Secrets / Environment / Deployment
```

`BOOTSTRAP-601` hoàn tất về mặt kiến trúc.

**Next task: `BOOTSTRAP-602`.**