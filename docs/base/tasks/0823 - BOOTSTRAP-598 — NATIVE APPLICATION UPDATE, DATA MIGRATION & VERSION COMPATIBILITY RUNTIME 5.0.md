# BOOTSTRAP-598 — NATIVE APPLICATION UPDATE, DATA MIGRATION & VERSION COMPATIBILITY RUNTIME 5.0

**Phạm vi:** quản lý toàn bộ vòng đời khi một ứng dụng Axiom chuyển từ phiên bản `N` sang `N+1`, bao gồm binary, runtime, native libraries, package, schema dữ liệu, configuration, migration, rollback và recovery.

`597` xác định **dữ liệu nằm ở đâu và được ghi như thế nào**.

`598` xác định **dữ liệu đó thay đổi như thế nào qua thời gian**.

---

## 598.1. Architectural Boundary

```text
                    Installed Application
                            │
                            ▼
                    Update Manager
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
      Binary            Dependencies        Data
         │                  │                  │
         ▼                  ▼                  ▼
   Compatibility       ABI Check         Schema Check
         │                  │                  │
         └──────────────────┼──────────────────┘
                            ▼
                    Migration Planner
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
             No Migration          Migration
                  │                   │
                  │          Stage → Verify
                  │                   │
                  └─────────┬─────────┘
                            ▼
                     Atomic Activation
                            │
                            ▼
                       New Version
```

---

# 598.2. Core Principle

Một application update **không phải chỉ là thay executable**.

Nó là một transaction giữa:

```text
Application Binary
Runtime
Native Dependencies
Package Graph
Configuration Schema
Application Data Schema
Database Schema
Resource Manifest
Permissions
```

---

# 598.3. Update Identity

```text
struct UpdateIdentity {
    application_id: AppID
    from_version: Version
    to_version: Version
    package_id: PackageID
    build_id: BuildID
    update_id: UpdateID
}
```

---

# 598.4. Version Identity

Không dùng một version duy nhất cho mọi semantic layer.

```text
ApplicationVersion
BinaryVersion
RuntimeVersion
DataSchemaVersion
DatabaseSchemaVersion
PackageGraphVersion
ABIRevision
```

---

# 598.5. Application Version

Đại diện version mà user nhìn thấy.

```text
1.8.0
```

---

# 598.6. Binary Version

Đại diện executable/compiler artifact identity.

```text
BinaryID = hash(native image + target + ABI metadata)
```

---

# 598.7. Runtime Version

Runtime ABI/API contract:

```text
RuntimeVersion {
    major
    minor
    patch
    abi_revision
}
```

---

# 598.8. Data Schema Version

Mỗi persistent data domain có schema riêng.

```text
SettingsSchema = 4
ProjectSchema = 12
UserProfileSchema = 7
```

Không ép toàn application dùng một integer schema.

---

# 598.9. Schema Identity

```text
SchemaID {
    namespace
    name
    version
    definition_hash
}
```

`definition_hash` giúp phát hiện schema thay đổi nhưng version không tăng.

---

# 598.10. Migration Identity

```text
MigrationID {
    schema
    from_version
    to_version
    implementation_hash
}
```

---

# 598.11. Migration Graph

Migration không nhất thiết là chain tuyến tính.

```text
v1 ──→ v2 ──→ v3 ──→ v4
 │                  ↘
 └────→ v2.5 ───────→ v4
```

Planner chọn đường hợp lệ.

---

# 598.12. Canonical Migration Path

Production application nên ưu tiên:

```text
Current
  ↓
Nearest Supported Intermediate
  ↓
Target
```

không chạy hàng trăm migration nhỏ nếu có migration trực tiếp tương đương.

---

# 598.13. Migration Graph Node

```text
MigrationNode {
    schema_id
    version
    compatibility
}
```

---

# 598.14. Migration Graph Edge

```text
MigrationEdge {
    migration_id
    from
    to
    cost
    reversible
    online_capable
    destructive
}
```

---

# 598.15. Migration Cost

Planner có thể tối ưu:

```text
cost =
    execution_time
  + storage_required
  + risk_class
```

Không được hy sinh correctness để giảm cost.

---

# 598.16. Migration Direction

Có ba loại:

```text
Forward
Backward
Bidirectional
```

---

# 598.17. Forward Migration

```text
vN → vN+1
```

là default.

---

# 598.18. Backward Migration

Downgrade chỉ được phép khi migration graph khai báo compatibility.

Không tự động reverse migration.

---

# 598.19. Irreversible Migration

```text
Migration {
    reversible = false
}
```

Nếu migration irreversible, update system phải biết trước khi commit.

---

# 598.20. Downgrade Protection

Nếu data đã chuyển sang schema không tương thích:

```text
old binary
    +
new data
```

không được chạy.

Hệ thống trả:

```text
IncompatibleDataVersion
```

---

# 598.21. Compatibility Matrix

```text
Compatibility {
    binary
    runtime
    ABI
    data_schema
    database_schema
    package_graph
    platform
    architecture
}
```

---

# 598.22. Compatibility State

```text
Compatible
ConditionallyCompatible
MigrationRequired
MigrationUnsupported
Incompatible
Unknown
```

---

# 598.23. Compatibility Rule

Application chỉ được activate khi:

```text
Binary
  ∧ Runtime
  ∧ ABI
  ∧ Dependencies
  ∧ Data
  ∧ Platform
```

đạt compatibility contract.

---

# 598.24. Preflight

Trước update:

```text
Inspect
→ Verify Package
→ Verify Platform
→ Verify ABI
→ Verify Dependencies
→ Verify Storage
→ Verify Migration
→ Estimate Resources
```

---

# 598.25. Preflight Result

```text
PreflightResult {
    compatible
    migration_required
    estimated_storage
    estimated_time
    rollback_possible
    blocking_reasons[]
}
```

---

# 598.26. Update State Machine

```text
Installed
   ↓
Discovered
   ↓
Downloaded
   ↓
Verified
   ↓
Staged
   ↓
Preflighted
   ↓
MigrationPrepared
   ↓
MigrationExecuted
   ↓
Validated
   ↓
Activated
   ↓
Running
```

Failure:

```text
Downloaded ─────→ Failed
Verified ────────→ Failed
MigrationExecuted → Recovery
Activated ───────→ Rollback/Recovery
```

---

# 598.27. Update Transaction

Một update transaction có:

```text
UpdateTransaction {
    update_id
    source_version
    target_version
    package
    staging_root
    migration_plan
    backup_reference
    journal
}
```

---

# 598.28. Transaction Journal

```text
UpdateJournal {
    transaction_id
    current_state
    source_manifest
    target_manifest
    migration_state
    activation_state
}
```

Journal phải durable trước các transition quan trọng.

---

# 598.29. Update Phases

```text
1. Discover
2. Acquire
3. Verify
4. Stage
5. Preflight
6. Backup
7. Migrate
8. Validate
9. Activate
10. Commit
11. Cleanup
```

---

# 598.30. Discover

Update Manager xác định:

```text
current version
target version
target package
update channel
platform
architecture
ABI
```

---

# 598.31. Acquire

Có thể lấy package từ:

```text
registry
mirror
local file
offline media
enterprise repository
peer cache
```

---

# 598.32. Verify Before Stage

Package phải được verify:

```text
signature
content hash
manifest
provenance
target
ABI
```

trước khi được đưa vào executable staging area.

---

# 598.33. Stage

Không thay đổi live application.

```text
live/
staging/
```

---

# 598.34. Staging Layout

```text
application/
├── current/
├── versions/
│   ├── v1/
│   └── v2/
├── staging/
└── update/
    └── journal/
```

Physical layout là platform-specific.

Semantic model không phụ thuộc layout.

---

# 598.35. Versioned Installation

Nếu platform cho phép, nhiều version binary có thể cùng tồn tại:

```text
v1
v2
v3
```

giúp rollback.

---

# 598.36. Active Version

```text
ActiveVersion = v2
```

được xác định bằng activation metadata/OS mechanism.

Không nhất thiết copy binary.

---

# 598.37. Atomic Activation

```text
Prepared v2
      ↓
Validate v2
      ↓
atomic activation marker
      ↓
v2 active
```

---

# 598.38. Activation Marker

```text
ActivationRecord {
    target_version
    binary_id
    package_id
    generation
}
```

---

# 598.39. Crash During Activation

Nếu process crash:

```text
journal
   ↓
inspect activation record
   ↓
complete OR rollback
```

Không được để hệ thống ở trạng thái mơ hồ.

---

# 598.40. Process Shutdown

Update Manager phải phối hợp với `594`.

```text
RequestShutdown
      ↓
ApplicationStopping
      ↓
Flush critical state
      ↓
Stop workers
      ↓
Release locks
      ↓
ProcessExited
```

---

# 598.41. Forced Shutdown

Nếu graceful shutdown timeout:

```text
ShutdownTimeout
```

Update policy quyết định:

```text
Abort
Retry
Force
```

Force không được giả định data durability.

---

# 598.42. Update Lock

Một application chỉ có một active update transaction:

```text
UpdateLock(application_id)
```

---

# 598.43. Multi-Process Update

Nếu application có nhiều processes:

```text
Supervisor
 ├── Main
 ├── Worker
 ├── Renderer
 └── Helper
```

Update Manager phải đảm bảo toàn bộ processes dùng compatible binary set.

---

# 598.44. Helper Process

Helper binary có thể có version compatibility riêng.

Không được thay helper mà không validate ABI.

---

# 598.45. Native Library Compatibility

Mỗi native library có:

```text
LibraryCompatibility {
    ABI
    target
    architecture
    cpu_features
    runtime_requirements
}
```

---

# 598.46. Dynamic Library Update

Không replace library đang được process sử dụng nếu platform không hỗ trợ an toàn.

Update phải:

```text
shutdown
→ replace
→ restart
```

hoặc side-by-side load.

---

# 598.47. Static Library

Static libraries không tồn tại độc lập trong runtime binary sau link.

Compatibility được kiểm tra ở build/link stage.

---

# 598.48. Plugin Compatibility

Plugin phải khai báo:

```text
PluginABI
PluginAPI
RuntimeRange
ApplicationRange
```

---

# 598.49. Plugin Update

Plugin incompatible không được load.

Application vẫn có thể chạy nếu plugin optional.

---

# 598.50. Required Plugin

Nếu plugin mandatory:

```text
ApplicationStartBlocked
```

thay vì chạy trong trạng thái không đầy đủ.

---

# 598.51. Package Graph Compatibility

Update package graph phải được validate như `591`.

```text
OldGraph
    ↓
TargetGraph
    ↓
ABI + version + target validation
```

---

# 598.52. Dependency Migration

Nếu dependency thay đổi data schema:

```text
Application Migration
        │
        └── Dependency Migration
```

phải có thứ tự dependency-aware.

---

# 598.53. Migration Dependency DAG

```text
Database
   ↓
Storage Schema
   ↓
Application Schema
   ↓
Application State
```

Không migrate child schema trước parent dependency nếu contract cấm.

---

# 598.54. Migration Ordering

Planner tạo DAG:

```text
M1 ──→ M3
M2 ──→ M3
M3 ──→ M4
```

topological ordering.

---

# 598.55. Cyclic Migration

Cycle là lỗi package/schema:

```text
MigrationCycle
```

không được runtime tự đoán cách phá cycle.

---

# 598.56. Migration Preconditions

```text
pre:
    schema == expected_from
    data_valid
    required_dependency_version
    sufficient_storage
```

---

# 598.57. Migration Postconditions

```text
post:
    schema == expected_to
    data_valid
    invariants_hold
```

---

# 598.58. Migration Verification

Verification có thể gồm:

```text
schema validation
checksum
record count
foreign key validation
application invariant checks
```

---

# 598.59. Data Invariants

Application có thể đăng ký:

```text
DataInvariant {
    name
    validate()
}
```

---

# 598.60. Migration Dry Run

Migration planner hỗ trợ:

```text
dry_run()
```

để ước tính:

```text
bytes
records
duration
risk
```

không thay đổi live data.

---

# 598.61. Migration Resource Estimate

```text
MigrationEstimate {
    input_bytes
    temporary_bytes
    output_bytes
    peak_bytes
    estimated_duration
}
```

---

# 598.62. Disk Space Preflight

Update phải kiểm tra:

```text
required =
    package
  + staging
  + backup
  + migration_temp
  + output
```

trước migration.

---

# 598.63. Insufficient Storage

Trả:

```text
InsufficientStorage
```

và không bắt đầu destructive migration.

---

# 598.64. Backup Before Migration

Nếu migration có risk:

```text
Backup
  ↓
Verify Backup
  ↓
Migration
```

---

# 598.65. Backup Validity

Backup phải có:

```text
BackupIdentity
SchemaVersion
ContentHash
Timestamp
ApplicationVersion
```

---

# 598.66. Backup Scope

Không backup:

```text
Cache
Temp
rebuildable artifacts
```

trừ khi policy yêu cầu.

---

# 598.67. Rollback Binary

Nếu target binary không hoạt động:

```text
v2 → v1
```

---

# 598.68. Rollback Data

Data rollback khó hơn binary rollback.

Chỉ rollback tự động nếu:

```text
backup exists
OR
migration reversible
```

---

# 598.69. Asymmetric Rollback

Có thể:

```text
binary rollback = yes
data rollback = no
```

Trong trường hợp này system phải báo rõ.

Không giả vờ rollback hoàn toàn.

---

# 598.70. Safe Rollback Policy

Nếu migration irreversible:

```text
retain old binary
retain backup
block downgrade
```

---

# 598.71. Last-Known-Good

Runtime lưu:

```text
LastKnownGoodVersion
LastKnownGoodDataSchema
```

---

# 598.72. Health Check

Sau activation:

```text
Start
 ↓
Health Check
 ↓
Ready
```

Nếu fail:

```text
CrashLoop
```

---

# 598.73. Automatic Recovery

`594` supervisor có thể báo:

```text
RepeatedStartupFailure
```

Update Manager có thể rollback binary nếu policy cho phép.

---

# 598.74. Crash Threshold

Ví dụ semantic policy:

```text
StartupFailureThreshold
```

Không hard-code số cụ thể trong core.

---

# 598.75. Recovery State Machine

```text
NewVersionActive
       ↓
Startup
       ↓
HealthCheck
   ┌───┴────┐
   │        │
 Pass      Fail
   │        │
 Stable   Retry
            │
        Threshold?
        ┌───┴───┐
        No     Yes
        │       │
      Retry   Rollback
```

---

# 598.76. Health Contract

Application có thể expose:

```text
health.startup()
health.ready()
health.liveness()
```

---

# 598.77. Startup Migration Timeout

Migration có thể lâu.

Không được coi mọi migration chậm là crash.

Phải có:

```text
MigrationProgress
MigrationHeartbeat
MigrationTimeoutPolicy
```

---

# 598.78. Migration Progress

```text
MigrationProgress {
    completed_units
    total_units
    phase
    percent
}
```

Percent chỉ xuất hiện nếu total xác định.

---

# 598.79. Durable Progress

Migration dài có thể persist checkpoint:

```text
checkpoint
→ flush
→ continue
```

---

# 598.80. Resume

Nếu migration hỗ trợ resume:

```text
Interrupted
   ↓
Validate checkpoint
   ↓
Resume
```

---

# 598.81. Non-Resumable Migration

Nếu không resume được:

```text
rollback from backup
```

---

# 598.82. Online Migration

Có thể migrate khi application đang chạy nếu schema contract cho phép.

```text
Read old
Write compatible
Migrate
Switch
```

---

# 598.83. Offline Migration

Mặc định cho destructive schema transformations:

```text
Application stopped
→ migrate
→ validate
→ start
```

---

# 598.84. Expand-Contract Pattern

Database/data migrations nên hỗ trợ:

```text
Expand
   ↓
Deploy compatible binary
   ↓
Backfill
   ↓
Switch
   ↓
Contract
```

---

# 598.85. Expand Phase

Thêm schema mới mà không xóa schema cũ.

---

# 598.86. Contract Phase

Xóa legacy schema chỉ sau khi mọi active component không còn sử dụng.

---

# 598.87. Mixed-Version Runtime

Nếu rolling deployment tồn tại:

```text
v1 + v2
```

phải có compatibility contract.

---

# 598.88. Mixed-Version Safety

Không cho mixed versions nếu:

```text
ABI incompatible
schema incompatible
protocol incompatible
```

---

# 598.89. IPC Compatibility

Theo `454`, IPC protocol phải có:

```text
ProtocolVersion
Capabilities
CompatibilityRange
```

---

# 598.90. Network Protocol Compatibility

Application update không được giả định server cũng update.

Protocol phải hỗ trợ:

```text
client capability negotiation
server capability negotiation
```

---

# 598.91. Configuration Migration

Configuration là persistent data.

```text
old config
   ↓
parse old schema
   ↓
migrate
   ↓
validate
   ↓
atomic replace
```

---

# 598.92. Unknown Configuration Fields

Mặc định nên preserve unknown fields nếu schema policy cho phép.

---

# 598.93. Removed Configuration

Removed fields có policy:

```text
Ignore
Preserve
Migrate
Reject
```

---

# 598.94. Default Changes

Changing default value không được coi là migration nếu field không tồn tại, nhưng semantic compatibility phải được document.

---

# 598.95. Environment Migration

Không migrate secrets/environment automatically.

OS credential system xử lý secrets.

---

# 598.96. User Documents

Application update không được tự động migrate arbitrary user documents.

Chỉ migrate khi:

```text
document format
schema
migration contract
```

được khai báo.

---

# 598.97. Document Compatibility

Document format có:

```text
FormatID
Version
ReaderRange
WriterVersion
```

---

# 598.98. Read-Only Compatibility

Application có thể mở document phiên bản cũ read-only nếu writer không tương thích.

---

# 598.99. Save Warning

Nếu mở legacy document và save sẽ upgrade format:

```text
FormatUpgradeRequired
```

phải được expose trước operation destructive.

---

# 598.100. Document Backup

Trước destructive format upgrade:

```text
Original
Backup
New
```

---

# 598.101. Application Cache Versioning

Cache key phải bao gồm:

```text
application version
schema version
algorithm version
compiler/build identity
```

nếu output phụ thuộc chúng.

---

# 598.102. Cache Invalidation

Sau update:

```text
invalidate incompatible cache
```

Không cần migrate cache nếu rebuild rẻ hơn.

---

# 598.103. Cache Compatibility

Cache entry có:

```text
ProducerID
FormatVersion
ContentID
```

---

# 598.104. Temp Update Data

Update staging nên dùng Temporary hoặc dedicated Update scope.

Không đưa staging vào user data.

---

# 598.105. Update Scope

```text
StorageScope::Update
```

có thể được runtime nội bộ sử dụng.

Không nhất thiết public cho application code.

---

# 598.106. Update Scope Lifetime

Update data được giữ cho tới:

```text
commit
rollback
cleanup
```

---

# 598.107. Update Package Integrity

Package hash phải xác định chính xác content.

---

# 598.108. Update Signature

Signature verify trước activation.

Signing implementation thuộc `550/587/593`.

598 chỉ orchestrate.

---

# 598.109. Trust State

```text
Unknown
Verified
Trusted
Revoked
Rejected
```

---

# 598.110. Revoked Update

Nếu package bị revoke trước activation:

```text
activation blocked
```

---

# 598.111. Already Installed Revocation

Revocation không tự động xóa binary đang chạy.

Policy security layer quyết định remediation.

---

# 598.112. Update Provenance

```text
SourceRevision
    ↓
BuildID
    ↓
ArtifactHash
    ↓
PackageHash
    ↓
UpdateID
    ↓
ActivationID
```

---

# 598.113. Update Manifest

```text
UpdateManifest {
    application_id
    source_version
    target_version
    targets[]
    dependencies[]
    migrations[]
    compatibility
    rollback_policy
    signature
    provenance
}
```

---

# 598.114. Target Selection

Update phải match:

```text
OS
architecture
ABI
CPU feature
runtime
deployment mode
```

---

# 598.115. CPU Feature Compatibility

Nếu binary yêu cầu:

```text
AVX2
SVE
NEON
```

target machine phải được kiểm tra trước activation.

---

# 598.116. Fat Package

Một update package có thể chứa nhiều variants:

```text
package
├── x86_64
├── arm64
└── wasm
```

Target selector chọn đúng artifact.

---

# 598.117. Delta Update

Update Manager có thể hỗ trợ:

```text
full package
delta package
```

Delta chỉ được apply nếu source artifact identity match.

---

# 598.118. Delta Preconditions

```text
InstalledBinaryHash == DeltaSourceHash
```

Nếu không:

```text
DeltaMismatch
```

và fallback full package nếu policy cho phép.

---

# 598.119. Delta Verification

Sau apply:

```text
result hash == target hash
```

---

# 598.120. Binary Patching Safety

Patch không được activate trước target artifact verification.

---

# 598.121. Offline Update

Offline bundle chứa:

```text
UpdateManifest
Package
Signature
Provenance
Migration metadata
```

---

# 598.122. Air-Gapped Update

Không yêu cầu internet.

Verification vẫn phải hoạt động offline.

---

# 598.123. Enterprise Update

Enterprise có thể cung cấp:

```text
UpdatePolicy
Mirror
AllowedVersions
BlockedVersions
MaintenanceWindow
```

---

# 598.124. Update Channels

```text
Stable
Beta
Nightly
Internal
Custom
```

Channel không quyết định trust; signature/provenance mới quyết định authenticity.

---

# 598.125. Pinning

Application/admin có thể pin:

```text
version
major line
dependency
runtime
```

---

# 598.126. Blocked Version

Policy có thể chặn version:

```text
BlockedVersion {
    version
    reason_code
}
```

---

# 598.127. Maintenance Window

Update có thể chờ:

```text
maintenance window
```

nhưng security-critical update policy có thể override theo deployment policy.

---

# 598.128. User Deferral

Desktop application có thể defer update.

Không làm thay đổi compatibility rules.

---

# 598.129. Restart Requirement

Manifest khai báo:

```text
RestartRequirement {
    None
    Application
    Process
    System
}
```

---

# 598.130. Hot Update

Hot update chỉ được phép nếu component contract explicit hỗ trợ.

Không tự động unload native code đang executing.

---

# 598.131. WASM Update

WASM application có thể update module:

```text
old module
   ↓
new module
```

Persistence backend `597` phải migrate state trước activation.

---

# 598.132. Browser Cache

WASM/browser cache phải version theo:

```text
origin
application
artifact hash
```

Không dùng browser cache key không xác định.

---

# 598.133. Service Worker-like Runtime

Nếu host hỗ trợ service-worker style deployment, Axiom runtime phải phân biệt:

```text
cached artifact
active artifact
installing artifact
```

---

# 598.134. Mobile Update

Mobile update phải chịu platform-managed installation.

Axiom Update Manager không bypass OS installer.

---

# 598.135. iOS

Application binary activation do OS/App Store mechanism quản lý.

Axiom chịu trách nhiệm:

```text
data compatibility
migration
first-launch recovery
```

---

# 598.136. Android

Tương tự:

```text
OS package update
      ↓
Axiom first-launch migration
```

---

# 598.137. Desktop Self-Update

Desktop có thể dùng external updater helper.

Helper phải có trust/ABI contract.

---

# 598.138. Updater Isolation

Updater nên là process riêng để binary hiện tại không tự overwrite executable đang chạy khi OS không cho phép.

---

# 598.139. Updater IPC

```text
Application
    ↕
Updater IPC
    ↕
Update Manager
```

Protocol versioned.

---

# 598.140. Update Authentication

Updater requests phải xác thực caller application identity.

---

# 598.141. Privilege Boundary

Updater không được mặc định chạy elevated.

Nếu cần privilege:

```text
user/OS authorization
```

phải explicit.

---

# 598.142. Privilege Separation

```text
User Application
       │
       ▼
Unprivileged Update Planner
       │
       ▼
OS-authorized Installer
```

---

# 598.143. Installer Boundary

Installer/deployment system `593` chịu trách nhiệm:

```text
install
uninstall
permissions
platform registration
```

598 chịu trách nhiệm:

```text
version transition
data compatibility
migration orchestration
```

---

# 598.144. Separation Rule

```text
598 ≠ installer
598 ≠ package registry
598 ≠ compiler
598 ≠ database engine
```

---

# 598.145. Update Planner

```text
UpdatePlanner {
    inspect()
    resolve()
    check_compatibility()
    plan_migration()
    estimate()
}
```

---

# 598.146. Update Executor

```text
UpdateExecutor {
    acquire()
    verify()
    stage()
    backup()
    migrate()
    activate()
    validate()
    commit()
}
```

---

# 598.147. Update Recovery Manager

```text
RecoveryManager {
    inspect_journal()
    recover_transaction()
    rollback_binary()
    restore_data()
    mark_failed()
}
```

---

# 598.148. Update Manager

```text
UpdateManager
├── Planner
├── PackageResolver
├── Verifier
├── Stager
├── MigrationEngine
├── Activator
├── HealthMonitor
└── RecoveryManager
```

---

# 598.149. Migration Engine

```text
MigrationEngine {
    discover()
    validate()
    plan()
    dry_run()
    execute()
    checkpoint()
    verify()
    rollback()
}
```

---

# 598.150. Migration Context

```text
MigrationContext {
    source_schema
    target_schema
    storage
    database
    temporary_storage
    cancellation
    progress
    logger
}
```

---

# 598.151. Migration Sandbox

Migration code không được mặc định có quyền:

```text
network
process spawn
arbitrary OS access
```

Chỉ:

```text
declared storage
declared database
declared resources
```

---

# 598.152. Migration Capability

```text
MigrationCapability {
    read_scopes
    write_scopes
    database_access
    temp_access
}
```

---

# 598.153. Migration Determinism

Migration phải deterministic với:

```text
same input
same schema
same migration version
same declared environment
```

trừ khi explicitly marked nondeterministic.

---

# 598.154. Time During Migration

Migration không nên dựa vào wall clock để quyết định data transformation.

Nếu cần timestamp, phải explicit policy.

---

# 598.155. Randomness During Migration

Không dùng random values không deterministic trừ khi schema yêu cầu và provenance ghi nhận.

---

# 598.156. External Network Migration

Mặc định:

```text
network = denied
```

Migration cần network phải khai báo capability.

---

# 598.157. Migration Failure Classification

```text
MigrationError
├── InvalidInput
├── UnsupportedVersion
├── InsufficientStorage
├── PermissionDenied
├── DependencyMissing
├── ValidationFailed
├── ExecutionFailed
├── CheckpointCorrupt
├── RollbackFailed
└── Unknown
```

---

# 598.158. Rollback Failure

Nếu rollback cũng thất bại:

```text
RecoveryRequired
```

Hệ thống không được tiếp tục startup bình thường.

---

# 598.159. Recovery Mode

Application có thể khởi động:

```text
RecoveryMode
```

với chức năng giới hạn:

```text
export data
restore backup
retry migration
rollback
diagnostics
```

---

# 598.160. Safe Mode

Safe mode:

```text
no plugins
no optional migrations
no user startup scripts
minimal services
```

nhằm cứu dữ liệu.

---

# 598.161. Recovery UI

Recovery UI phải hiển thị:

```text
current version
target version
data schema
failure stage
available backup
rollback possibility
```

Không hiển thị thông tin giả định.

---

# 598.162. AI Recovery

AI có thể:

```text
inspect
explain
propose recovery plan
```

nhưng destructive recovery phải qua capability.

---

# 598.163. AI Migration Planning

AI có thể đọc:

```text
Schema
MigrationGraph
CompatibilityMatrix
Journal
BackupMetadata
```

để giải thích trạng thái.

Không được tự viết migration production code rồi execute mà không compile/validate.

---

# 598.164. AI-Generated Migration

Nếu migration được AI sinh:

```text
generate
→ compile
→ static analyze
→ test against fixtures
→ differential validate
→ human/system approval
→ execute
```

---

# 598.165. Migration Fixtures

Mỗi migration phải có:

```text
input fixture
expected output
invariants
failure fixture
```

---

# 598.166. Migration Differential Test

```text
old data
 ├── reference migration
 └── optimized migration
          ↓
       compare
```

---

# 598.167. Property-Based Migration Test

Generate valid old-schema data.

Kiểm tra:

```text
migrate(data)
```

luôn satisfy target invariants.

---

# 598.168. Fuzz Migration

Input malformed data phải:

```text
reject safely
```

không:

```text
panic
memory corruption
silent truncation
```

---

# 598.169. Idempotency

Migration có thể khai báo:

```text
idempotent = true
```

Nếu true:

```text
M(M(x)) == M(x)
```

về semantic result.

---

# 598.170. Exactly-Once

Không giả định migration execution exactly-once.

Thiết kế phải chịu được:

```text
crash
retry
resume
```

---

# 598.171. At-Least-Once Safe Migration

Default architecture ưu tiên:

```text
at-least-once execution
+
idempotent/checkpointed effects
```

---

# 598.172. Journal Commit

Migration chỉ được coi committed khi:

```text
target data verified
+
journal durable
+
activation record durable
```

---

# 598.173. Commit Point

Có một logical commit point:

```text
MigrationPrepared
       ↓
MigrationCommitted
```

Sau commit, rollback semantics thay đổi.

---

# 598.174. Two-Phase Activation

```text
Prepare
   ↓
Commit
```

Không có live activation trước Prepare hoàn tất.

---

# 598.175. Three-Phase Update

Đối với update phức tạp:

```text
Prepare
Validate
Activate
```

---

# 598.176. Update Atomicity

Mục tiêu:

```text
old valid state
OR
new valid state
```

Không:

```text
half old + half new
```

ngoại trừ các component được thiết kế mixed-version explicit.

---

# 598.177. Mixed-State Exception

Nếu expand-contract yêu cầu mixed state:

```text
compatibility protocol
```

phải được manifest khai báo.

---

# 598.178. Update Manifest Compatibility

```text
CompatibilityPolicy {
    min_runtime
    max_runtime
    supported_data_versions
    supported_abi
    mixed_version_allowed
}
```

---

# 598.179. Data Retention

Sau update có thể giữ:

```text
old backup
old migration journal
old binary
```

theo retention policy.

---

# 598.180. Retention Policy

```text
RetentionPolicy {
    keep_last_versions
    keep_backups
    max_backup_bytes
    max_age
}
```

---

# 598.181. Cleanup

Cleanup chỉ chạy sau:

```text
new version healthy
rollback window elapsed
```

hoặc explicit policy.

---

# 598.182. Rollback Window

```text
RollbackWindow {
    duration
    startup_count
    health_requirements
}
```

---

# 598.183. Rollback Expiry

Sau expiry:

```text
old binary may be removed
```

nhưng user documents không bị xóa.

---

# 598.184. Update History

Persistent update history:

```text
UpdateRecord {
    update_id
    from
    to
    timestamp
    result
    migration_result
    rollback_result
}
```

---

# 598.185. Update History Integrity

History phải content-addressed hoặc integrity-protected nếu dùng cho security decisions.

---

# 598.186. Update Observability

Metrics:

```text
update_download_bytes
update_verify_duration
update_stage_duration
migration_duration
migration_failures
rollback_count
startup_after_update
update_recovery_count
```

---

# 598.187. Structured Update Events

```text
UpdateDiscovered
UpdateVerified
UpdateStaged
MigrationStarted
MigrationCompleted
ActivationStarted
ActivationCompleted
HealthCheckPassed
RollbackStarted
RollbackCompleted
RecoveryRequired
```

---

# 598.188. Logging

Mỗi event:

```text
update_id
application_id
version
phase
result
duration
```

---

# 598.189. Privacy

Không log:

```text
raw document contents
secret values
credential data
full sensitive paths
```

---

# 598.190. Performance

Update planning phải không đọc toàn bộ user data nếu metadata đủ.

Migration mới được phép scan data cần thiết.

---

# 598.191. Incremental Migration

Large datasets nên hỗ trợ:

```text
chunk
checkpoint
resume
```

---

# 598.192. Parallel Migration

Chỉ parallel khi dependency graph cho phép.

```text
M1 ─┐
M2 ─┼→ M4
M3 ─┘
```

M1/M2/M3 có thể chạy song song nếu không conflict.

---

# 598.193. Deterministic Parallel Migration

Output phải deterministic dù execution order khác nhau.

---

# 598.194. Resource Limits

Migration có:

```text
memory_limit
cpu_limit
storage_limit
time_limit
```

---

# 598.195. Cancellation

Migration cancellation phải chuyển sang state:

```text
Cancelling
→
RolledBack
OR
Paused
OR
RecoveryRequired
```

Không simply kill giữa destructive operation.

---

# 598.196. Pause/Resume

Migration có thể hỗ trợ:

```text
pause
checkpoint
resume
```

nếu manifest khai báo.

---

# 598.197. Update Pause

Download/staging có thể pause.

Commit/activation không được pause giữa atomic transition.

---

# 598.198. Network Failure

Download failure không ảnh hưởng live application.

---

# 598.199. Power Loss

Sau power loss:

```text
read journal
→ determine last durable state
→ recover
```

---

# 598.200. Filesystem Corruption

Nếu journal corrupt:

```text
RecoveryRequired
```

Không tự đoán.

---

# 598.201. Backup Corruption

Backup checksum mismatch:

```text
BackupInvalid
```

Không restore.

---

# 598.202. Multiple Backups

Recovery Manager có thể chọn backup gần nhất:

```text
BackupSet
├── B1 schema 4
├── B2 schema 5
└── B3 schema 6
```

---

# 598.203. Backup Compatibility

Backup chỉ restore nếu:

```text
schema migration path exists
```

---

# 598.204. Cross-Version Backup

Restore có thể:

```text
Backup v3
→ migrate
→ Current v7
```

nếu migration graph đầy đủ.

---

# 598.205. Backup Provenance

Backup phải ghi:

```text
source application version
source schema
target platform
creation time
content hashes
```

---

# 598.206. Update Security

Không chạy migration từ package chưa verified.

Đây là hard security boundary.

---

# 598.207. Migration Code Trust

Migration code phải thuộc cùng trust chain với application package hoặc được explicitly trusted.

---

# 598.208. Untrusted Migration

Không được chạy arbitrary migration script từ network.

---

# 598.209. Supply Chain

Update dependency:

```text
Package
→ Signature
→ Provenance
→ SBOM/DependencyGraph
→ Compatibility
```

tích hợp với `550/587/591`.

---

# 598.210. Reproducibility

Update artifact phải có:

```text
BuildID
SourceRevision
ToolchainID
Target
DependencyGraphHash
```

---

# 598.211. Update Rebuild

Có thể xác minh:

```text
source + toolchain + dependencies
→ expected artifact hash
```

---

# 598.212. Transparency

Update record nên cho phép truy xuất:

```text
why update selected
what changed
what migrated
what dependencies changed
```

---

# 598.213. Semantic Diff

IDE/AI có thể hiển thị:

```text
API changes
ABI changes
schema changes
dependency changes
permission changes
```

---

# 598.214. Permission Changes

Nếu update yêu cầu capability mới:

```text
NewPermissions
```

phải được phát hiện trước activation.

---

# 598.215. Permission Downgrade

Update có thể remove permission.

Không tự động retain unnecessary permissions nếu platform hỗ trợ revocation.

---

# 598.216. Capability Migration

Application data không được chứa implicit authority.

Permissions thuộc deployment/security manifest.

---

# 598.217. Update of Resource Package

Immutable resources từ `596` có thể thay đổi giữa versions.

Resource identity vẫn dùng:

```text
ResourceID
ContentID
```

---

# 598.218. Resource Compatibility

Application code chỉ được reference resource nếu:

```text
ResourceID exists
type compatible
format compatible
```

---

# 598.219. Resource Removal

Nếu resource bị remove nhưng code vẫn reference:

```text
UpdateValidationFailed
```

trước activation.

---

# 598.220. Resource Format Migration

Nếu resource cần migration:

```text
resource migration
```

phải được phân biệt với user-data migration.

---

# 598.221. Cache Rebuild After Resource Update

Cache phụ thuộc resource content phải invalidate theo:

```text
ContentID
```

---

# 598.222. AI Update Explanation

API:

```text
update.explain(update_id)
```

trả:

```text
source
target
changed components
migration path
compatibility
rollback
```

Không đưa prediction không có evidence.

---

# 598.223. AI Update Plan

```text
UpdatePlan {
    target
    compatibility
    migration_steps
    storage_estimate
    rollback
    permissions
    risks
}
```

---

# 598.224. AI Approval Boundary

AI không được tự chuyển:

```text
Plan → Commit
```

nếu policy yêu cầu user/admin approval.

---

# 598.225. IDE Update Preview

IDE có thể cung cấp:

```text
Current v5
Target v6

Binary: changed
Runtime: unchanged
Schema: v8 → v9
Migration: required
Backup: required
Restart: required
Rollback: available
```

---

# 598.226. Compiler Integration

Compiler có thể compile migration declarations:

```text
migration UserProfile 7 -> 8 {
    ...
}
```

---

# 598.227. Migration Declaration

```text
migration UserProfile from 7 to 8 {
    requires Storage.Write
    reversible false

    fn migrate(ctx) -> Result<void> {
        ...
    }
}
```

Syntax chính thức phải tích hợp với `429/430/431`.

---

# 598.228. Compile-Time Validation

Compiler kiểm tra:

```text
schema exists
from/to valid
duplicate migration
cycle possibility
capabilities
```

---

# 598.229. Migration Effect

Theo `573`:

```text
migration
→ Storage
→ Database
→ IO
→ Mutation
```

---

# 598.230. Migration Metadata

Compiler emit:

```text
MigrationMetadata {
    id
    schema
    from
    to
    effects
    capabilities
    reversible
    deterministic
    resumable
}
```

---

# 598.231. Migration Registry

Runtime build có registry:

```text
Schema
 └── Version
      └── Migration
```

---

# 598.232. Dead Migration Elimination

Migration không còn reachable từ supported upgrade paths có thể bị loại khỏi runtime artifact.

---

# 598.233. Long-Term Compatibility

Application có thể khai báo:

```text
supported_data_range = 3..10
```

---

# 598.234. Compatibility Window

Binary có thể hỗ trợ nhiều schema versions:

```text
Binary v8
    ├── schema 6
    ├── schema 7
    └── schema 8
```

giảm nhu cầu migration ngay lập tức.

---

# 598.235. Lazy Migration

Nếu schema mới không cần ngay, migration có thể deferred.

Chỉ được phép khi compatibility contract cho phép.

---

# 598.236. Lazy Migration Safety

Legacy data vẫn phải:

```text
readable
valid
non-corrupt
```

---

# 598.237. Background Migration

Có thể migrate data lớn sau startup:

```text
ApplicationReady
    ↓
BackgroundMigration
```

nhưng old/new schema coexistence phải được thiết kế explicit.

---

# 598.238. Foreground Critical Migration

Data bắt buộc cho startup phải migrate trước:

```text
ApplicationReady
```

---

# 598.239. Migration Priority

```text
Critical
Startup
Background
Optional
```

---

# 598.240. User Experience

Update state không được biểu diễn mơ hồ.

Phải có:

```text
Preparing
Migrating
Verifying
Activating
Recovering
```

---

# 598.241. Progress Accuracy

Không được hiển thị `100%` trước commit.

---

# 598.242. Error UX

Mọi fatal update error phải có:

```text
what happened
current state
data safety status
available recovery actions
```

---

# 598.243. No False Success

Update chỉ báo `Success` sau:

```text
activation
+
health check
+
journal commit
```

---

# 598.244. Update Completion

```text
UpdateSucceeded
```

chỉ khi target version thực sự active.

---

# 598.245. Update Failure

```text
UpdateFailed
```

phải giữ live application ở trạng thái hợp lệ.

---

# 598.246. Partial Success

Nếu package download thành công nhưng activation chưa xảy ra:

```text
StagedNotActive
```

Không gọi là update success.

---

# 598.247. Interrupted Update Recovery

Startup:

```text
journal exists?
 ├── no → normal
 └── yes
      ↓
 inspect
      ↓
 recover
```

---

# 598.248. Recovery Decision

Recovery dựa trên durable evidence:

```text
journal
package hash
activation record
migration checkpoint
backup
```

Không dựa trên timestamp đơn thuần.

---

# 598.249. Update Test Matrix

Phải test:

```text
N → N+1
N → N+2
N → N+many
N → downgrade
migration failure
power loss
process crash
disk full
permission denied
package corruption
signature failure
dependency conflict
ABI mismatch
runtime mismatch
CPU mismatch
```

---

# 598.250. Platform Update Tests

```text
Windows
Linux
macOS
iOS
Android
WASM
```

với backend phù hợp.

---

# 598.251. Security Tests

Phải test:

```text
unsigned update
invalid signature
wrong target
wrong architecture
tampered migration
path traversal
malicious package
privilege escalation
rollback attack
downgrade attack
```

---

# 598.252. Anti-Downgrade

Security-sensitive applications có thể khai báo:

```text
minimum_security_version
```

Version thấp hơn bị reject.

---

# 598.253. Rollback vs Anti-Downgrade

Rollback nội bộ trusted version:

```text
allowed
```

Downgrade từ external untrusted package:

```text
rejected
```

---

# 598.254. Monotonic Security Version

```text
SecurityEpoch
```

có thể tăng độc lập với semantic application version.

---

# 598.255. Update Epoch

```text
UpdateEpoch {
    application_epoch
    security_epoch
}
```

---

# 598.256. Epoch Validation

Target phải thỏa:

```text
target.security_epoch >= installed.minimum_security_epoch
```

---

# 598.257. Time-of-Check / Time-of-Use

Package hash/signature phải được verify trên artifact thực sự được activate.

Không verify một file rồi activate file khác cùng path.

---

# 598.258. Content-Addressed Staging

Staging ưu tiên:

```text
ContentID → immutable object
```

sau đó activation reference tới object.

---

# 598.259. Immutable Staged Artifact

Sau verification:

```text
verified artifact = immutable
```

Không được mutate tại chỗ.

---

# 598.260. Final Update Architecture

```text
                         UPDATE SYSTEM
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
           Planner         Verifier         Recovery
              │               │                │
              ▼               ▼                ▼
       Compatibility      Trust Chain       Journal
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                       Migration Engine
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
                  Storage           Database
                     │                 │
                     └────────┬────────┘
                              ▼
                           Staging
                              │
                              ▼
                           Activate
                              │
                              ▼
                        Health Check
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
              Success                  Recovery
                 │                         │
                 ▼                         ▼
             Commit                    Rollback
```

---

# 598.261. Integration Map

```text
550  Secure Compiler
587  Compiler Trust
588  Toolchain SDK
591  Package Registry
593  Application Packaging
594  Process Supervision
596  Resource Runtime
597  User/Application Storage
598  Update + Migration Runtime
```

---

# 598.262. Required Runtime Types

```text
UpdateID
UpdateIdentity
UpdateManifest
UpdateTransaction
UpdateState
UpdatePlan
UpdateResult

Compatibility
CompatibilityState
CompatibilityMatrix

SchemaID
SchemaVersion
MigrationID
MigrationNode
MigrationEdge
MigrationPlan
MigrationContext
MigrationProgress
MigrationResult

BackupIdentity
BackupReference
ActivationRecord
UpdateJournal
RecoveryState
HealthState
```

---

# 598.263. Required APIs

```text
update.check()
update.plan()
update.download()
update.verify()
update.stage()
update.preflight()
update.backup()
update.migrate()
update.activate()
update.validate()
update.commit()
update.rollback()
update.recover()
update.history()
```

---

# 598.264. Required Migration APIs

```text
migration.list()
migration.plan()
migration.dry_run()
migration.execute()
migration.pause()
migration.resume()
migration.verify()
migration.rollback()
```

---

# 598.265. Required Compatibility APIs

```text
compatibility.check_binary()
compatibility.check_runtime()
compatibility.check_data()
compatibility.check_dependencies()
compatibility.check_platform()
compatibility.explain()
```

---

# 598.266. Required Compiler Metadata

Compiler phải emit:

```text
ApplicationVersion
BinaryID
ABIRevision
RuntimeRequirement
SchemaMetadata
MigrationMetadata
DependencyGraphHash
Target
CPURequirements
CapabilityRequirements
```

---

# 598.267. Required Manifest

Application manifest phải mô tả:

```text
application_id
version
binary
runtime
dependencies
schemas
migrations
permissions
rollback_policy
security_epoch
update_policy
```

---

# 598.268. Hard Separation

```text
Package Registry
       ↓
Package
       ↓
Deployment
       ↓
Installed Application
       ↓
Update Manager
       ↓
Migration
       ↓
Runtime
```

Mỗi tầng có ownership rõ ràng.

---

# 598.269. No Hidden Migration

Application không được tự động sửa persistent data trong startup code mà không đăng ký migration metadata.

---

# 598.270. No Hidden Version Dependency

Code không được dựa vào physical package version mà không khai báo compatibility requirement.

---

# 598.271. No Unsafe Downgrade

Không activate binary nếu data schema không tương thích.

---

# 598.272. No Partial Activation

Không được activate một phần dependency graph.

---

# 598.273. No Unverified Artifact

Không execute artifact chưa verify identity/integrity/trust.

---

# 598.274. No Destructive Migration Without Recovery Policy

Migration destructive phải có:

```text
rollback
OR
backup
OR
explicit irreversible policy
```

---

# 598.275. No False Rollback

Nếu chỉ binary rollback mà data không rollback được, runtime phải báo chính xác:

```text
BinaryRolledBackDataRetained
```

---

# 598.276. No Silent Data Loss

Cache/temp có thể mất.

UserData/ApplicationData không được âm thầm mất do update.

---

# 598.277. No Arbitrary Installer Privilege

Update Manager không tự nâng quyền.

---

# 598.278. No Network Requirement

Core update/migration architecture phải hoạt động với offline packages.

---

# 598.279. No Third-Party Compiler Dependency

Migration runtime và update runtime đều là native Axiom components, không phụ thuộc compiler bên ngoài.

---

# 598.280. Deterministic Update Planning

Cùng:

```text
current manifest
target manifest
platform
policy
storage state
```

phải tạo cùng migration/update plan.

---

# 598.281. Deterministic Migration

Cùng input/schema/environment contract phải cho cùng semantic result.

---

# 598.282. Provenance Continuity

```text
Source
 ↓
Compiler
 ↓
Binary
 ↓
Package
 ↓
Update
 ↓
Migration
 ↓
Activation
```

phải truy vết được.

---

# 598.283. AI Truth Boundary

AI chỉ được nói:

```text
verified
observed
unknown
inferred
```

và không được biến `unknown` thành trạng thái đã xác minh.

---

# 598.284. AI Update Safety

AI có thể:

```text
analyze
plan
explain
simulate
validate
```

nhưng destructive commit phải tuân capability/permission model.

---

# 598.285. Final Hard Invariant

`BOOTSTRAP-598` chỉ được coi là hoàn chỉnh khi:

```text
1. Binary, runtime, ABI, dependency và data schema có identity độc lập.
2. Update là một state machine có journal durable.
3. Package được verify trước activation.
4. Update được stage ngoài live application.
5. Compatibility được kiểm tra trước migration.
6. Migration được biểu diễn bằng graph có version rõ ràng.
7. Migration có precondition và postcondition.
8. Migration có thể dry-run và estimate resource.
9. Migration dài có checkpoint khi cần.
10. Migration chịu được crash/retry.
11. Migration destructive có recovery policy.
12. Data backup được verify trước khi dùng.
13. Binary rollback và data rollback được phân biệt.
14. Không được rollback binary rồi giả vờ data cũng đã rollback.
15. Downgrade chỉ được phép khi compatibility contract cho phép.
16. Anti-downgrade security policy độc lập với application version.
17. Update không được activate partial dependency graph.
18. Dynamic library ABI phải được validate.
19. Plugin ABI phải được validate.
20. IPC protocol compatibility phải được validate.
21. Resource compatibility phải được validate.
22. Configuration được migrate như persistent schema.
23. User documents không bị migrate âm thầm.
24. Cache được invalidate/rebuild khi incompatible.
25. Temporary update data không trở thành user data.
26. Online migration chỉ được dùng khi compatibility contract cho phép.
27. Expand-contract được hỗ trợ cho hệ thống cần mixed-version.
28. Migration mặc định không có network privilege.
29. Migration code phải nằm trong trust boundary.
30. AI-generated migration phải qua compile/test/validation.
31. Update không yêu cầu internet.
32. WASM/mobile/desktop đều dùng cùng semantic update model.
33. OS-native installer vẫn là deployment boundary.
34. Update Manager không tự ý nâng privilege.
35. Activation có commit point rõ ràng.
36. Power loss có thể được recovery từ durable journal.
37. Update success chỉ được báo sau health validation.
38. Startup failure có thể kích hoạt recovery/rollback theo policy.
39. Recovery mode không được làm mất dữ liệu.
40. Update history có provenance.
41. Build/package/update/migration provenance liên tục.
42. Update planning deterministic.
43. Migration testing có fixture, property test và crash test.
44. Security tests bao gồm tampering, downgrade và privilege escalation.
45. Không có hidden data migration trong startup code.
46. Không có silent data loss.
47. Không có silent compatibility downgrade.
48. Không có unverified executable activation.
49. Logical application state luôn ở một trạng thái schema hợp lệ.
50. **Tại mọi thời điểm có thể quan sát, hệ thống phải có ít nhất một trạng thái Application + Data mà runtime biết là hợp lệ hoặc phải chuyển sang Recovery State; tuyệt đối không tồn tại trạng thái “không biết binary nào tương ứng với data nào”.**
```

# 598 — LOCKED

---

# NEXT — BOOTSTRAP-599

## BOOTSTRAP-599 — NATIVE APPLICATION CONFIGURATION, PREFERENCES, SECRETS & POLICY RUNTIME 5.0

Mục tiêu tiếp theo là chuẩn hóa lớp **configuration/policy** nằm phía trên `597/598`, phân biệt configuration với user data, environment, command-line arguments, secrets và runtime policy.

```text
                  Application
                       │
                Configuration
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    Defaults        User Config      System Policy
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 Config Resolver
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Environment    CLI Args      Secrets
          │            │            │
          └────────────┼────────────┘
                       ▼
                Effective Config
                       │
                ┌──────┴──────┐
                ▼             ▼
             Runtime       Components
```

`599` sẽ xử lý:

- layered configuration;
- defaults;
- user/system/application/environment/CLI precedence;
- typed configuration;
- schema validation;
- configuration migration;
- immutable runtime snapshots;
- hot reload;
- secret separation;
- OS credential/keychain integration;
- policy overrides;
- environment variables;
- command-line configuration;
- configuration provenance;
- configuration diff;
- transactional configuration update;
- configuration rollback;
- profile/debug/release configuration;
- deployment policy;
- enterprise policy;
- AI-readable effective configuration;
- deterministic configuration resolution;
- security boundary giữa **configuration**, **secret**, **user data** và **runtime state**.