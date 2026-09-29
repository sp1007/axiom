# BOOTSTRAP-762 — AXCONFIG

**Title:** Native Configuration, Environment, Profiles, Feature Flags, Runtime Settings & Immutable Configuration Snapshot Runtime 5.0  
**Namespace:** `AXCONFIG`  
**Phase:** Axiom Civilization Runtime / Native Configuration & Runtime Settings  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXCONFIG` là hệ thống cấu hình native thống nhất của Axiom.

Nó quản lý:

- application configuration;
- system configuration;
- environment;
- configuration profiles;
- defaults;
- overrides;
- feature flags;
- runtime settings;
- immutable configuration snapshots;
- schema;
- validation;
- versioning;
- hot reload;
- rollback;
- configuration provenance;
- configuration subscriptions.

Mục tiêu quan trọng:

> **Mọi execution context phải nhìn thấy một configuration snapshot nhất quán, immutable và có version xác định.**

---

# 2. Kiến trúc tổng thể

```text
                       AXCONFIG
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Defaults      Profiles    Environment
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Merge / Resolve
                           │
                           ▼
                 Schema + Validation
                           │
                           ▼
                Immutable Snapshot
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       AXPROCESS         AXTASK        APPLICATION
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                      AXOBSERVABILITY
```

---

# 3. Strong boundary

## AXCONFIG sở hữu

- configuration schema;
- configuration values;
- default values;
- profile selection;
- environment overlays;
- override precedence;
- snapshot creation;
- snapshot versioning;
- validation;
- feature flags;
- runtime settings;
- change detection;
- atomic activation;
- rollback;
- subscriptions;
- configuration provenance.

## AXCONFIG không sở hữu

- secrets vault;
- authentication;
- authorization;
- security policy;
- process lifecycle;
- persistent database;
- network transport;
- filesystem implementation.

Secrets chỉ được **tham chiếu**, không thuộc AXCONFIG plaintext storage.

---

# 4. Configuration ≠ capability

Đây là invariant kiến trúc quan trọng.

Không được phép:

```text
config.admin = true
```

tự động biến thành:

```text
ADMIN_CAPABILITY
```

Configuration thay đổi behavior.

`AXSECURITY` quyết định authority.

---

# 5. Configuration hierarchy

Một configuration value có thể được tạo từ:

```text
BUILTIN_DEFAULT
SYSTEM_DEFAULT
PROFILE
ENVIRONMENT
APPLICATION
USER
SESSION
RUNTIME_OVERRIDE
```

Nhưng thứ tự precedence phải deterministic.

---

# 6. Canonical precedence

Baseline:

```text
BUILTIN_DEFAULT
      ↓
SYSTEM_DEFAULT
      ↓
PROFILE
      ↓
ENVIRONMENT
      ↓
APPLICATION
      ↓
USER
      ↓
SESSION
      ↓
EXPLICIT_RUNTIME_OVERRIDE
```

Layer cao hơn override layer thấp hơn nếu schema cho phép.

---

# 7. Configuration source

```text
config_source {
    source_id
    source_type
    priority
    version
    origin
}
```

Source types:

```text
BUILTIN
FILE
ENVIRONMENT
COMMAND_LINE
APPLICATION
USER
SESSION
IPC
REMOTE
RUNTIME
```

---

# 8. Source trust

Source metadata không có nghĩa source được tin tưởng tuyệt đối.

Ví dụ:

```text
REMOTE
```

không tự động có quyền override:

```text
SECURITY_CONFIGURATION
```

AXSECURITY vẫn enforce authority.

---

# 9. Configuration key

Canonical key:

```text
config_key {
    namespace
    name
    schema_id
}
```

Ví dụ:

```text
network.http.timeout
graphics.renderer.backend
application.language
```

---

# 10. Naming

Key names phải:

- UTF-8;
- deterministic;
- case policy rõ ràng;
- không chứa ambiguous separators.

Canonical representation:

```text
namespace.name
```

---

# 11. Configuration value types

Native types:

```text
BOOL
I8
I16
I32
I64
U8
U16
U32
U64
F32
F64
STRING
BYTES
ENUM
DURATION
SIZE
PATH
UUID
IP_ADDRESS
ENDPOINT
ARRAY
MAP
STRUCT
OPTION
```

Không dùng dynamic scripting language làm canonical configuration format.

---

# 12. Strong typing

Schema:

```text
timeout: duration
max_memory: size
enabled: bool
workers: u32
```

không được silently convert:

```text
"abc"
```

thành số.

---

# 13. Schema

```text
config_schema {
    schema_id
    version
    fields[]
    constraints[]
    defaults[]
}
```

Schema là authoritative description của configuration structure.

---

# 14. Schema version

Mỗi schema có:

```text
major
minor
revision
```

Compatibility phải explicit.

---

# 15. Field definition

```text
config_field {
    key
    type
    required
    default
    constraints
    mutability
    sensitivity
}
```

---

# 16. Mutability

Mỗi setting có một trong:

```text
STATIC
RESTART_REQUIRED
RELOADABLE
DYNAMIC
```

Ví dụ:

```text
binary_path = STATIC
worker_count = RELOADABLE
log_level = DYNAMIC
```

---

# 17. Immutable snapshot

Core object:

```text
config_snapshot {
    snapshot_id
    schema_id
    schema_version
    source_versions[]
    created_at
    values
}
```

Sau khi activate:

```text
snapshot.values
```

không được mutate.

---

# 18. Atomic activation

Configuration transition:

```text
Snapshot N
    │
    │ prepare
    ▼
Snapshot N+1
    │
 validation
    │
    ▼
   ACTIVE
```

Không có trạng thái:

```text
50% old
50% new
```

trong cùng execution context.

---

# 19. Snapshot visibility

Mỗi operation có thể bind:

```text
operation → snapshot_id
```

Operation tiếp tục dùng snapshot cũ cho tới khi boundary kết thúc.

---

# 20. Task semantics

`AXTASK` mặc định kế thừa snapshot từ parent execution context.

Một task mới có thể:

```text
INHERIT
PIN
EXPLICIT
```

configuration snapshot.

---

# 21. Async semantics

Một async continuation không được vô tình chuyển sang configuration snapshot khác chỉ vì reload xảy ra trong lúc suspended.

```text
await
  ↓
resume
  ↓
same snapshot
```

trừ khi application explicit refresh.

---

# 22. Process semantics

Process có:

```text
process_config_context {
    active_snapshot
    available_snapshots
    policy
}
```

Child process inheritance phải explicit.

---

# 23. Thread semantics

Không cần copy toàn bộ configuration vào mỗi thread.

Thread có thể tham chiếu immutable process snapshot.

---

# 24. Lookup fast path

Ideal lookup:

```text
config.get("graphics.renderer.backend")
```

được compile thành descriptor lookup khi key known statically.

Không nhất thiết phải hash string mỗi lần.

---

# 25. Compiled configuration descriptors

Compiler có thể emit:

```text
config_descriptor {
    key_id
    type
    offset
    constraints
}
```

Runtime lookup:

```text
key_id → descriptor → snapshot value
```

---

# 26. Zero-allocation reads

Normal read:

```text
config.get()
```

không được heap allocate.

---

# 27. Configuration handle

Opaque handle:

```text
config_handle
```

có thể đại diện:

- snapshot;
- schema;
- field;
- source.

---

# 28. Default values

Defaults phải nằm trong schema hoặc immutable default descriptor.

Không để application code rải rác:

```text
if missing => 123
```

ở hàng trăm nơi.

---

# 29. Required fields

Field `required` mà không có value hợp lệ:

```text
CONFIG_MISSING_REQUIRED
```

và snapshot không được activate.

---

# 30. Constraint system

Baseline:

```text
MIN
MAX
RANGE
LENGTH
ENUM_SET
REGEX
PATTERN
DEPENDENCY
MUTUAL_EXCLUSION
REQUIRED_IF
```

Không cần full constraint programming engine.

---

# 31. Cross-field validation

Ví dụ:

```text
tls.enabled = true
```

yêu cầu:

```text
tls.certificate_ref != null
```

Validation phải chạy trước activation.

---

# 32. Configuration transaction

```text
config_transaction {
    base_snapshot
    changes[]
}
```

Flow:

```text
begin
 ↓
set
 ↓
validate
 ↓
prepare
 ↓
commit
```

---

# 33. Conflict detection

Nếu base snapshot không còn active:

```text
CONFIG_CONFLICT
```

Transaction không được silently overwrite thay đổi của process khác.

---

# 34. Compare-and-swap activation

Canonical primitive:

```text
config_activate_if_current(
    expected_snapshot_id,
    new_snapshot
)
```

Atomic.

---

# 35. Rollback

Mọi snapshot activated thành công có thể được giữ metadata đủ để rollback theo retention policy.

```text
N+2
 ↓ rollback
N+1
```

Rollback phải tạo activation event mới, không rewrite lịch sử.

---

# 36. Configuration history

AXCONFIG lưu metadata:

```text
configuration_revision {
    revision_id
    parent_revision
    snapshot_id
    source
    actor
    timestamp
}
```

Persistent history implementation có thể dùng AXSTORAGE.

---

# 37. Audit integration

Các hành động administrative:

```text
CONFIG_CHANGE
CONFIG_ACTIVATE
CONFIG_ROLLBACK
CONFIG_POLICY_CHANGE
CONFIG_SECRET_REFERENCE_CHANGE
```

có thể được đưa sang `AXAUDIT`.

AXCONFIG không tự trở thành audit log.

---

# 38. Provenance

Mỗi resolved value có thể truy xuất:

```text
value
  ↓
source
  ↓
source_version
  ↓
override chain
```

Ví dụ:

```text
timeout = 30s
source = production-profile
```

---

# 39. Effective configuration

API:

```text
config_explain(key)
```

trả:

```text
effective_value
source
overridden_values
schema
constraints
snapshot_id
```

Rất hữu ích cho debugging.

---

# 40. Environment variables

Environment có thể map:

```text
AX_HTTP_TIMEOUT
```

vào:

```text
network.http.timeout
```

mapping phải explicit.

Không tự động expose toàn bộ environment thành configuration.

---

# 41. Command-line overrides

CLI có thể override allowed fields:

```text
--network.http.timeout=5s
```

Schema quyết định field có cho phép override hay không.

---

# 42. File configuration

AXCONFIG có parser abstraction.

Native formats có thể gồm:

```text
AXCFG
JSON
TOML-compatible
YAML-compatible
```

Nhưng external parsers không phải dependency runtime bắt buộc.

Canonical internal representation vẫn là typed configuration tree.

---

# 43. AXCFG

Axiom nên có native configuration format:

```text
application {
    name = "demo"
    workers = 8
    timeout = 5s
}
```

Mục tiêu:

- typed;
- deterministic;
- compact;
- easy for humans;
- easy for AI;
- easy for compiler.

---

# 44. Feature flags

```text
feature_flag {
    flag_id
    name
    type
    default
    state
    version
}
```

Baseline types:

```text
BOOLEAN
PERCENTAGE
ENUM
VALUE
```

---

# 45. Feature flag evaluation

```text
feature.enabled("new_renderer")
```

phải deterministic đối với cùng:

```text
flag version
snapshot
evaluation context
```

---

# 46. Percentage rollout

Có thể:

```text
0%
10%
25%
50%
100%
```

Nhưng rollout hash phải ổn định.

Không dùng random mới ở mỗi request.

---

# 47. Targeting

Feature flag có thể dựa trên explicit attributes:

```text
platform
version
environment
tenant
```

Không được tự động dùng sensitive identity attributes nếu policy không cho phép.

---

# 48. Feature flag ≠ authorization

```text
feature.enabled("admin_ui")
```

không thay thế:

```text
AXSECURITY authorization
```

---

# 49. Feature flag consistency

Một request/operation phải nhìn thấy cùng flag snapshot.

Không được:

```text
function A → flag=false
function B → flag=true
```

trong cùng logical operation chỉ vì reload xảy ra giữa chừng.

---

# 50. Runtime settings

Dynamic setting có thể thay đổi mà không restart:

```text
cache.size
thread_pool.limit
telemetry.sample_rate
ui.refresh_rate
```

Nhưng setting phải được schema đánh dấu `DYNAMIC` hoặc `RELOADABLE`.

---

# 51. Change subscription

```text
config_subscribe(key, callback)
```

Callback nhận:

```text
old_snapshot
new_snapshot
changed_keys
```

---

# 52. Callback safety

Configuration callback không được chạy dưới global configuration lock.

Flow:

```text
activate
 ↓
publish snapshot
 ↓
release internal lock
 ↓
notify subscribers
```

---

# 53. Subscriber failure

Một subscriber lỗi không được rollback snapshot đã commit.

Thay vào đó:

```text
subscriber_error
```

được ghi nhận.

Nếu setting yêu cầu coordinated restart/reconfiguration thì subsystem đó phải có transaction riêng.

---

# 54. Prepare/apply model

Một subsystem có thể implement:

```text
prepare(snapshot)
apply(snapshot)
```

Ví dụ network listener.

Nếu `prepare` fail:

```text
new snapshot = not active
```

---

# 55. Partial application

Không cho phép configuration engine tuyên bố:

```text
ACTIVE
```

nếu một field mandatory của subsystem chưa apply thành công.

Có thể có distinction:

```text
CONFIGURATION_ACTIVE
SUBSYSTEM_APPLYING
```

để tránh giả tạo trạng thái.

---

# 56. Configuration lifecycle

```text
DISCOVERED
 ↓
PARSED
 ↓
RESOLVED
 ↓
VALIDATED
 ↓
PREPARED
 ↓
ACTIVATED
 ↓
SUPERSEDED
 ↓
RETIRED
```

---

# 57. Invalid configuration

Invalid configuration không được trở thành active snapshot.

Application có thể tiếp tục chạy snapshot cũ.

---

# 58. Safe reload

Canonical flow:

```text
current N
    ↓
load sources
    ↓
merge
    ↓
schema validate
    ↓
policy validate
    ↓
prepare
    ↓
activate atomically
    ↓
N+1
```

---

# 59. Reload failure

```text
N
│
├── candidate N+1 → INVALID
│
└── remains ACTIVE
```

Không crash process chỉ vì một reload thất bại, trừ khi policy của application yêu cầu.

---

# 60. Configuration security

Configuration values có classification:

```text
PUBLIC
INTERNAL
SENSITIVE
SECRET_REFERENCE
```

Plaintext secrets không được mặc định lưu trong AXCONFIG.

---

# 61. Secret references

Ví dụ:

```text
database.password = secret("db/prod/password")
```

AXCONFIG chỉ lưu:

```text
secret_ref
```

Secret resolution thuộc subsystem chuyên trách.

---

# 62. Sensitive values

`config_explain()` không được trả plaintext sensitive value nếu caller không có authority.

---

# 63. Configuration encryption

Nếu configuration persistence cần encryption:

```text
AXCONFIG
    ↓
AXSTORAGE
    ↓
AXCRYPTO
```

AXCONFIG không tự implement cryptography.

---

# 64. Tenant isolation

Multi-tenant configuration:

```text
tenant
  ↓
namespace
  ↓
snapshot
```

Tenant A không được đọc snapshot Tenant B nếu AXSECURITY không cấp quyền.

---

# 65. Namespace isolation

Configuration namespace:

```text
system.*
network.*
graphics.*
application.*
user.*
```

Subsystem chỉ được phép sửa namespace được cấp.

---

# 66. Protected configuration

Các namespace như:

```text
security.*
identity.*
capability.*
```

có thể bị đánh dấu:

```text
SECURITY_PROTECTED
```

AXCONFIG không bypass AXSECURITY.

---

# 67. Configuration capability

Có thể định nghĩa capability:

```text
CONFIG_READ
CONFIG_WRITE
CONFIG_ACTIVATE
CONFIG_ROLLBACK
CONFIG_READ_SENSITIVE
CONFIG_ADMIN
```

Authorization do AXSECURITY.

---

# 68. Observability integration

AXOBSERVABILITY metrics:

```text
config_reload_count
config_reload_failure
config_active_snapshot
config_validation_failure
config_activation_latency
config_subscription_failure
```

---

# 69. Diagnostic integration

AXDIAGNOSTICS có thể lấy:

```text
active_snapshot_id
schema_version
configuration_revision
```

để crash/failure report biết runtime đang chạy configuration nào.

Không dump plaintext secrets.

---

# 70. Process integration

AXPROCESS dùng AXCONFIG để xác định:

- startup settings;
- resource limits;
- environment;
- runtime profile.

Process lifecycle vẫn thuộc AXPROCESS.

---

# 71. Task integration

AXTASK có:

```text
task.config_snapshot
```

nhưng không copy configuration tree.

Chỉ giữ immutable snapshot reference.

---

# 72. Compiler integration

Compiler hỗ trợ:

```text
@config("network.http.timeout")
```

và có thể generate:

```text
ConfigField<Duration>
```

descriptor.

---

# 73. Compile-time configuration

Build profile:

```text
@compile_config("target.arch")
```

có thể constant-fold.

Nhưng runtime configuration không được nhầm với compile-time configuration.

---

# 74. Dead-code elimination

Nếu feature flag là compile-time constant:

```text
if compile_feature("debug") { ... }
```

compiler có thể loại bỏ branch.

Runtime feature flag thì không.

---

# 75. AI metadata

Schema có thể cung cấp:

```text
description
type
allowed_range
examples
dependencies
mutability
sensitivity
```

AI tooling có thể dùng metadata để hiểu configuration.

---

# 76. AI boundary

AI có thể:

- giải thích configuration;
- phát hiện conflict;
- đề xuất thay đổi;
- generate config;
- validate candidate;
- compare snapshots.

AI không được tự activate privileged configuration nếu không có explicit authority.

---

# 77. Configuration diff

```text
config_diff(snapshot_a, snapshot_b)
```

trả:

```text
added
removed
changed
unchanged
```

Sensitive values phải redacted.

---

# 78. Configuration query

API hỗ trợ:

```text
config_get()
config_has()
config_type()
config_source()
config_explain()
config_diff()
```

Query read-only.

---

# 79. Native API — registry

```text
config_init()
config_shutdown()

config_schema_register()
config_schema_get()

config_source_register()
config_source_remove()
```

---

# 80. Native API — snapshot

```text
config_snapshot_current()
config_snapshot_get()
config_snapshot_retain()
config_snapshot_release()

config_snapshot_diff()
config_snapshot_explain()
```

---

# 81. Native API — transaction

```text
config_transaction_begin()
config_transaction_set()
config_transaction_remove()
config_transaction_validate()
config_transaction_prepare()
config_transaction_commit()
config_transaction_abort()
```

---

# 82. Native API — activation

```text
config_activate()
config_activate_if_current()
config_reload()
config_rollback()
config_revision_get()
```

---

# 83. Native API — subscriptions

```text
config_subscribe()
config_unsubscribe()
config_subscription_pause()
config_subscription_resume()
```

---

# 84. Native API — feature flags

```text
feature_register()
feature_get()
feature_enabled()
feature_evaluate()

feature_activate()
feature_deactivate()
feature_rollout_set()
```

---

# 85. Native API — environment

```text
config_environment_get()
config_environment_import()
config_environment_refresh()
```

---

# 86. Native API — validation

```text
config_validate()
config_validate_field()
config_validate_schema()
config_get_validation_errors()
```

---

# 87. Native ABI

```text
AXCONFIG_ABI_1
```

Core ABI objects:

```text
config_schema_handle
config_source_handle
config_snapshot_handle
config_transaction_handle
config_subscription_handle
feature_handle
```

---

# 88. Error model

```text
CONFIG_NOT_FOUND
CONFIG_INVALID_TYPE
CONFIG_INVALID_VALUE
CONFIG_MISSING_REQUIRED
CONFIG_SCHEMA_MISMATCH
CONFIG_CONSTRAINT_FAILED
CONFIG_CONFLICT
CONFIG_PERMISSION_DENIED
CONFIG_PROTECTED
CONFIG_SECRET_UNAVAILABLE
CONFIG_SOURCE_FAILED
CONFIG_PARSE_FAILED
CONFIG_PREPARE_FAILED
CONFIG_ACTIVATION_FAILED
CONFIG_ROLLBACK_FAILED
CONFIG_RELOAD_FAILED
CONFIG_RESOURCE_LIMIT
CONFIG_SUBSCRIBER_FAILED
CONFIG_INVALID_TRANSACTION
CONFIG_SNAPSHOT_EXPIRED
CONFIG_UNSUPPORTED
```

---

# 89. Performance architecture

Configuration reads là hot path trong nhiều ứng dụng.

Baseline:

```text
immutable snapshot
+
compiled field descriptor
+
direct offset/reference
```

thay vì:

```text
string lookup
→ parse
→ lock
→ allocate
```

mỗi lần đọc.

---

# 90. Snapshot representation

Implementation có thể dùng:

```text
immutable arena
```

hoặc:

```text
persistent tree
```

hoặc:

```text
typed flat table
```

Canonical requirement không phải representation cụ thể.

Requirement là:

- immutable;
- stable;
- bounded;
- cheap lookup;
- atomic publication.

---

# 91. Copy-on-write

Khi tạo snapshot mới:

```text
Snapshot N
   ↓
copy-on-write
   ↓
Snapshot N+1
```

Không cần copy toàn bộ configuration nếu implementation có structural sharing.

---

# 92. Memory lifetime

Snapshot chỉ được reclaim khi không còn execution context giữ reference.

Có thể dùng:

```text
reference count
epoch reclamation
hazard mechanism
```

Implementation choice.

Không bắt buộc GC.

---

# 93. Concurrency

Configuration activation phải:

- lock-minimized;
- atomic;
- deterministic;
- wait-free/read-mostly nếu có thể.

Reads không nên block vì reload.

---

# 94. Global state

Không cho phép mỗi library tự tạo một hidden global configuration universe.

Mỗi process/application có configuration root rõ ràng.

---

# 95. Library configuration

Library có thể khai báo schema:

```text
library.network.*
```

Application quyết định source/activation.

Library không được tự ý thay đổi global configuration.

---

# 96. Plugin configuration

Plugin namespace:

```text
plugin.<plugin_id>.*
```

Plugin chỉ truy cập namespace được cấp.

---

# 97. Configuration inheritance

```text
system
   ↓
process
   ↓
application
   ↓
task
```

Inheritance là snapshot composition/reference, không phải mutable global state.

---

# 98. Environment isolation

Child process environment phải explicit.

Không mặc định expose parent secrets/configuration.

---

# 99. Remote configuration

Remote configuration có thể tồn tại:

```text
remote source
    ↓
authentication
    ↓
authorization
    ↓
fetch
    ↓
validate
    ↓
candidate snapshot
```

Không remote source nào được bypass local validation.

---

# 100. Remote failure

Nếu remote configuration server mất kết nối:

```text
active snapshot remains
```

cho tới khi policy quy định expiration.

Không tự động xóa configuration hợp lệ.

---

# 101. Configuration TTL

Một source có thể có:

```text
expires_at
```

Nếu hết TTL:

```text
SOURCE_EXPIRED
```

Candidate resolution quyết định fallback theo profile.

---

# 102. Deterministic resolution

Cùng:

```text
source set
source versions
schema
precedence
```

phải tạo cùng:

```text
snapshot
```

---

# 103. Resolution conflict

Nếu hai source cùng priority cùng sửa một key:

```text
CONFIG_CONFLICT
```

Không dùng ordering ngầm dựa trên arrival time.

---

# 104. Transaction isolation

Candidate snapshot không visible cho readers trước activation.

```text
prepare(candidate)
```

không ảnh hưởng:

```text
current_snapshot
```

---

# 105. Crash consistency

Nếu process crash trong activation:

```text
old snapshot
```

hoặc:

```text
new snapshot
```

được chọn theo atomic publication.

Không để trạng thái không hợp lệ.

Persistent configuration commit cần AXSTORAGE transactional semantics nếu yêu cầu durable atomicity.

---

# 106. Configuration recovery

Startup:

```text
load last valid revision
    ↓
verify schema compatibility
    ↓
validate
    ↓
activate
```

Nếu revision cuối invalid:

```text
previous valid revision
```

được chọn theo recovery policy.

---

# 107. Configuration migration

Schema migration:

```text
schema N
 ↓
migration
 ↓
schema N+1
 ↓
validation
```

Migration phải deterministic.

---

# 108. No implicit destructive migration

Không tự động xóa unknown fields chỉ vì schema mới không còn field đó.

Migration policy phải explicit.

---

# 109. Unknown fields

Modes:

```text
REJECT
WARN
IGNORE
PRESERVE
```

theo schema.

---

# 110. Compatibility

Configuration schema có compatibility rules:

```text
BACKWARD_COMPATIBLE
FORWARD_COMPATIBLE
EXACT
INCOMPATIBLE
```

---

# 111. Version pinning

Application có thể yêu cầu:

```text
schema_version = 5
```

để tránh silent semantic changes.

---

# 112. Canonical flow — startup

```text
process start
    ↓
discover sources
    ↓
load schema
    ↓
resolve precedence
    ↓
validate
    ↓
prepare subsystems
    ↓
activate snapshot
    ↓
application start
```

---

# 113. Canonical flow — hot reload

```text
active N
   ↓
source change
   ↓
candidate N+1
   ↓
merge
   ↓
validate
   ↓
prepare
   ↓
atomic activate
   ↓
publish
   ↓
notify
```

---

# 114. Canonical flow — failed reload

```text
active N
   ↓
candidate N+1
   ↓
validation failure
   ↓
reject
   ↓
N remains active
   ↓
observability event
```

---

# 115. Canonical flow — rollback

```text
N+2 ACTIVE
    ↓
rollback request
    ↓
select valid N+1
    ↓
validate
    ↓
prepare
    ↓
activate N+3
    │
    └── content equivalent to N+1
```

Rollback tạo revision mới; không rewrite history.

---

# 116. Canonical flow — feature flag

```text
request
  ↓
current snapshot
  ↓
feature evaluation
  ↓
stable result
  ↓
application behavior
```

---

# 117. Canonical flow — configuration + security

```text
configuration request
       ↓
AXCONFIG
       ↓
schema validation
       ↓
AXSECURITY authorization
       ↓
candidate snapshot
       ↓
prepare
       ↓
activate
       ↓
AXAUDIT
```

---

# 118. Canonical flow — AI-generated configuration

```text
AI
 ↓
candidate configuration
 ↓
schema validation
 ↓
constraint validation
 ↓
security authorization
 ↓
human/system-authorized activation
 ↓
snapshot
```

AI-generated configuration không bypass validation.

---

# 119. Canonical flow — library

```text
library
 ↓
register schema
 ↓
application supplies values
 ↓
AXCONFIG resolves
 ↓
library receives immutable view
```

Library không sở hữu global configuration engine.

---

# 120. Formal invariants

```text
CONFIG-INV-01
Mỗi active configuration phải thuộc một schema hợp lệ.

CONFIG-INV-02
Mỗi active snapshot phải có snapshot_id duy nhất.

CONFIG-INV-03
Active snapshot là immutable.

CONFIG-INV-04
Một snapshot không được mutate sau activation.

CONFIG-INV-05
Configuration read phải thấy một snapshot nhất quán.

CONFIG-INV-06
Atomic activation không được tạo mixed-version snapshot.

CONFIG-INV-07
Snapshot chưa validate không được activate.

CONFIG-INV-08
Snapshot chưa prepare thành công không được activate nếu field yêu cầu prepare.

CONFIG-INV-09
Precedence giữa các source phải deterministic.

CONFIG-INV-10
Hai source cùng priority conflict phải được xử lý explicit.

CONFIG-INV-11
Configuration key phải có schema/type identity.

CONFIG-INV-12
Typed value không được silently convert sai semantic type.

CONFIG-INV-13
Required field thiếu value không được validate thành công.

CONFIG-INV-14
Constraint violation không được tạo active snapshot.

CONFIG-INV-15
Runtime read thông thường không được bắt buộc heap allocation.

CONFIG-INV-16
Configuration snapshot không được yêu cầu GC để bảo đảm correctness.

CONFIG-INV-17
Async continuation phải giữ snapshot semantics nhất quán.

CONFIG-INV-18
Task inheritance phải explicit và deterministic.

CONFIG-INV-19
Process configuration inheritance phải explicit.

CONFIG-INV-20
Child process không được tự động nhận sensitive configuration.

CONFIG-INV-21
Feature flag không được thay thế authorization.

CONFIG-INV-22
Feature evaluation phải deterministic trong cùng snapshot/context.

CONFIG-INV-23
Dynamic setting chỉ được reload nếu schema cho phép.

CONFIG-INV-24
STATIC setting không được hot-reload silently.

CONFIG-INV-25
Subscriber failure không được corrupt active snapshot.

CONFIG-INV-26
Subscriber callback không được yêu cầu giữ global configuration lock.

CONFIG-INV-27
Failed reload phải giữ active snapshot cũ nếu policy cho phép fallback.

CONFIG-INV-28
Rollback không được rewrite lịch sử revision.

CONFIG-INV-29
Mọi activation phải tạo revision identity mới.

CONFIG-INV-30
Configuration provenance phải có thể truy nguyên tới source khi metadata được yêu cầu.

CONFIG-INV-31
Sensitive value không được expose qua explain/diff nếu caller thiếu authority.

CONFIG-INV-32
Plaintext secret không phải canonical AXCONFIG storage.

CONFIG-INV-33
Secret reference không tự cấp secret access.

CONFIG-INV-34
Protected configuration không được bypass AXSECURITY.

CONFIG-INV-35
Administrative configuration changes phải có thể tích hợp AXAUDIT.

CONFIG-INV-36
Configuration state phải có thể liên kết với AXOBSERVABILITY.

CONFIG-INV-37
Configuration state tại crash có thể được xác định mà không dump plaintext secrets.

CONFIG-INV-38
Schema migration phải deterministic.

CONFIG-INV-39
AI-generated configuration không được bypass schema/security/activation controls.

CONFIG-INV-40
AXCONFIG không được tự cấp security authority thông qua configuration values.
```

---

# 121. Definition of Done

`AXCONFIG 5.0` được xem là hoàn thành khi Axiom có:

- typed configuration;
- schemas;
- defaults;
- deterministic precedence;
- sources;
- profiles;
- environment overlays;
- CLI overrides;
- native AXCFG format;
- immutable snapshots;
- atomic activation;
- transactions;
- conflict detection;
- validation;
- constraints;
- cross-field validation;
- hot reload;
- rollback;
- revision history;
- provenance;
- configuration diff;
- explain API;
- feature flags;
- stable rollout;
- runtime settings;
- subscriptions;
- security classification;
- secret references;
- tenant isolation;
- protected namespaces;
- AXSECURITY integration;
- AXAUDIT integration;
- AXOBSERVABILITY integration;
- AXDIAGNOSTICS integration;
- compiler descriptors;
- compile-time configuration;
- AI metadata;
- deterministic resolution;
- migration;
- recovery;
- crash consistency;
- native ABI;
- native APIs;
- 40 invariants.

**AXCONFIG 5.0 → FROZEN.**

---

# BOOTSTRAP-763 — AXLOGGING

**Native Structured Logging, Log Records, Log Levels, Sinks, Filtering, Rotation & Application Log Runtime 5.0**

Đây là module hợp lý tiếp theo vì sau khi đã tách:

```text
AXAUDIT
    security/accountability evidence

AXDIAGNOSTICS
    crash/failure investigation

AXOBSERVABILITY
    metrics/traces/health/telemetry

AXCONFIG
    configuration/state of runtime
```

Axiom vẫn cần một lớp **human-readable structured logging** riêng:

```text
AXLOGGING
    ↓
application/runtime logs
    ↓
console / file / GUI / remote sink
```

Điểm kiến trúc cần giữ rất rõ: **log không phải audit, metric không phải log, diagnostic dump không phải log**. Điều này sẽ giúp Axiom tránh tình trạng một “logger” khổng lồ trở thành dependency của toàn bộ runtime.