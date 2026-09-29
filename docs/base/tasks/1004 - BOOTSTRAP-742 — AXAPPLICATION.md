# BOOTSTRAP-742 — AXAPPLICATION

**Namespace:** `AXAPPLICATION`  
**Phase:** Axiom Civilization Runtime / Native Application & Process Lifecycle Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXSHELL`, `AXDESKTOP`, `AXWINDOW`, `AXDISPLAY`, `AXCOMPOSITOR`, `AXUI`, `AXINPUT`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXCOMPUTE`, `AXSTORAGE`, `AXDATABASE`, `AXNETWORK`, `AXSECURITY`, `AXIDENTITY`, `AXASSET`

AXAPPLICATION là tầng quản lý **application identity và lifecycle của application/process**.

Điểm quan trọng:

```text
Application
    ≠ Executable file
    ≠ Process
    ≠ Process group
    ≠ Window
    ≠ Package
    ≠ Service
```

Axiom phải giữ các khái niệm này độc lập ngay từ core runtime.

```text
AXSHELL
   │
   │ launch request
   ▼
AXAPPLICATION
   │
   ├── application identity
   ├── package metadata
   ├── executable resolution
   ├── process creation
   ├── sandbox
   ├── permissions
   ├── lifecycle
   ├── resources
   ├── crash recovery
   ├── application state
   └── window association
          │
          ├── AXWINDOW
          ├── AXSECURITY
          ├── AXCOMPUTE
          ├── AXSTORAGE
          └── AXNETWORK
```

---

# 742.1 — Mục tiêu

AXAPPLICATION phải cung cấp native infrastructure cho:

```text
application identity
application registration
application metadata
executable resolution
package metadata
application launch
process creation
process lifecycle
process groups
application instances
multi-instance policy
sandbox
capabilities
permissions
resource limits
CPU affinity
memory limits
GPU access
I/O policy
background execution
service integration
IPC
application state
application checkpoint
session restore
crash detection
crash recovery
restart policy
graceful termination
forced termination
application/window mapping
application telemetry
application diagnostics
application simulation
application replay
digital twin
```

---

# 742.2 — Strong Boundary

### AXAPPLICATION owns

```text
application identity
application instance
process lifecycle
application lifecycle
launch/termination
process grouping
application resource policy
application sandbox integration
application state
application recovery
application/window association
```

### AXSTORAGE owns

```text
files
directories
storage devices
persistent data
database
```

### AXSECURITY owns

```text
authentication
authorization
capabilities
sandbox primitives
security policy
```

### AXWINDOW owns

```text
window identity
window lifecycle
window geometry
window surfaces
focus
```

### AXDESKTOP owns

```text
workspace
taskbar
dock
desktop placement
application switching
```

### AXSHELL owns

```text
launch UI
application picker
system commands
shell presentation
```

### AXCOMPUTE owns

```text
CPU/GPU/NPU resources
compute scheduling
compute resource pools
```

---

# 742.3 — Application Identity

Canonical identity:

```axiom
application_id
```

phải ổn định qua nhiều executable instances.

Ví dụ:

```text
com.example.editor
```

không phụ thuộc:

```text
C:\Apps\Editor.exe
PID 1234
window_id 567
```

---

# 742.4 — Application Descriptor

```axiom
application {
    id
    name
    version
    vendor
    executable
    package
    capabilities
    policies
}
```

---

# 742.5 — Application Version

Version phải tách:

```text
application version
package version
executable version
runtime compatibility version
state schema version
```

Không được coi chúng là cùng một version.

---

# 742.6 — Executable

```axiom
executable {
    id
    path
    format
    architecture
    entry
    code_hash
}
```

Executable có thể là:

```text
PE
ELF
Mach-O
WASM
Axiom native image
```

AXAPPLICATION không sở hữu executable format parser; compiler/object/runtime layers cung cấp artifact semantics.

---

# 742.7 — Package

```axiom
application_package {
    id
    application
    version
    artifacts
    manifest
    signatures
}
```

Package là deployment container.

Executable là một artifact bên trong package.

---

# 742.8 — Package ≠ Application

Một application có thể có:

```text
multiple packages
multiple architectures
multiple executable variants
multiple optional components
```

---

# 742.9 — Application Instance

```axiom
application_instance {
    id
    application
    process_group
    state
    started_at
}
```

Một application có thể có nhiều instance.

---

# 742.10 — Process

```axiom
process {
    id
    instance
    executable
    state
    resources
}
```

Process identity độc lập với application identity.

---

# 742.11 — Process Group

```axiom
process_group {
    id
    processes
    owner
}
```

Một application instance có thể sử dụng nhiều process:

```text
Application
   │
   └── Instance
        ├── UI process
        ├── worker process
        └── helper process
```

---

# 742.12 — Application Lifecycle

```text
REGISTERED
    ↓
AVAILABLE
    ↓
LAUNCHING
    ↓
STARTING
    ↓
RUNNING
    ↓
SUSPENDING
    ↓
SUSPENDED
    ↓
RESUMING
    ↓
RUNNING
    ↓
STOPPING
    ↓
STOPPED
```

Error states:

```text
FAILED
CRASHED
RECOVERING
```

---

# 742.13 — Process Lifecycle

```text
CREATED
STARTING
RUNNING
STOP_REQUESTED
STOPPING
TERMINATED
CRASHED
```

Process lifecycle không được thay thế application lifecycle.

---

# 742.14 — Application State vs Process State

Ví dụ:

```text
application = RUNNING
process A   = RUNNING
process B   = SUSPENDED
```

Application vẫn có thể được xem là running tùy lifecycle policy.

---

# 742.15 — Launch Request

```axiom
launch_request {
    application
    arguments
    environment
    working_directory
    instance_policy
    capabilities
    placement
}
```

---

# 742.16 — Launch Flow

```text
AXSHELL
   ↓
launch request
   ↓
resolve application
   ↓
verify package
   ↓
verify executable
   ↓
AXSECURITY
   ↓
create sandbox
   ↓
allocate resources
   ↓
create process
   ↓
start application
   ↓
AXWINDOW / AXDESKTOP
```

---

# 742.17 — Launch Authorization

Application launch phải kiểm tra:

```text
identity
package trust
requested capabilities
resource policy
execution policy
user/session policy
```

---

# 742.18 — Capability Request

```axiom
capability_request {
    capability
    reason
    scope
    lifetime
}
```

Application manifest có thể **request** capability.

Manifest không tự cấp capability.

---

# 742.19 — Capability Grant

```axiom
capability_grant {
    capability
    scope
    issuer
    expiration
}
```

Authority thuộc `AXSECURITY`.

---

# 742.20 — Sandbox

AXAPPLICATION tích hợp sandbox:

```text
application
    ↓
sandbox profile
    ├── filesystem
    ├── network
    ├── devices
    ├── IPC
    ├── GPU
    └── system resources
```

Primitive isolation thuộc security/platform backend.

---

# 742.21 — Sandbox Profile

```axiom
sandbox_profile {
    id
    filesystem_policy
    network_policy
    device_policy
    ipc_policy
    resource_policy
}
```

---

# 742.22 — Resource Policy

```axiom
resource_policy {
    cpu
    memory
    gpu
    storage
    network
    processes
    threads
}
```

---

# 742.23 — Memory Limit

Có thể định nghĩa:

```text
soft_limit
hard_limit
reservation
```

---

# 742.24 — CPU Policy

```text
normal
background
interactive
latency_sensitive
system
```

Scheduler thực tế thuộc `AXCOMPUTE`.

---

# 742.25 — GPU Policy

Application có thể request:

```text
graphics
compute
video_decode
video_encode
```

Actual device scheduling:

→ `AXCOMPUTE`.

---

# 742.26 — Background Execution

```axiom
background_policy {
    allowed
    priority
    cpu_budget
    network_budget
    wake_policy
}
```

---

# 742.27 — Suspension

Application suspension:

```text
RUNNING
   ↓
SUSPENDING
   ↓
SUSPENDED
```

Suspension không nhất thiết terminate process.

---

# 742.28 — Resume

```text
SUSPENDED
   ↓
RESUMING
   ↓
RUNNING
```

Application phải nhận lifecycle notification.

---

# 742.29 — Mobile/Constrained Runtime

Trên thiết bị hạn chế:

```text
background
   ↓
suspend
   ↓
checkpoint
   ↓
terminate process
```

Logical application state vẫn có thể được phục hồi.

---

# 742.30 — Application State

```axiom
application_state {
    schema
    data
    dirty
    timestamp
}
```

Application state không nhất thiết bằng process memory.

---

# 742.31 — State Checkpoint

```axiom
application_checkpoint {
    application
    instance
    schema_version
    state
    timestamp
}
```

---

# 742.32 — Checkpoint Storage

```text
AXAPPLICATION
      ↓
AXSTORAGE
      ↓
persistent checkpoint
```

Checkpoint phải có integrity metadata.

---

# 742.33 — State Versioning

Application state schema phải versioned:

```text
v1 → v2 → v3
```

Application mới phải xác định migration path hoặc từ chối restore.

---

# 742.34 — Crash Detection

```text
process
   ↓
exit unexpectedly
   ↓
AXAPPLICATION
   ↓
CRASHED
```

Crash event phải chứa:

```text
exit code
signal/exception
timestamp
process identity
application identity
diagnostic reference
```

---

# 742.35 — Crash ≠ Application Failure

Một helper process crash không nhất thiết làm application crash.

Application policy quyết định severity.

---

# 742.36 — Crash Classification

```text
PROCESS_CRASH
HELPER_CRASH
APPLICATION_CRASH
RESOURCE_FAILURE
STARTUP_FAILURE
DEPENDENCY_FAILURE
SECURITY_FAILURE
```

---

# 742.37 — Restart Policy

```axiom
restart_policy {
    mode
    max_attempts
    backoff
    conditions
}
```

Modes:

```text
NEVER
ON_FAILURE
ALWAYS
USER_REQUESTED
SYSTEM_POLICY
```

---

# 742.38 — Restart Safety

Không được restart vô hạn:

```text
crash
 ↓
restart
 ↓
crash
 ↓
restart
```

phải có bounded retry/backoff.

---

# 742.39 — Crash Loop

```text
STARTING
 ↓
CRASHED
 ↓
RECOVERING
 ↓
STARTING
 ↓
CRASHED
```

Nếu vượt policy:

```text
FAILED
```

---

# 742.40 — Graceful Termination

```text
RUNNING
 ↓
STOP_REQUESTED
 ↓
application save/checkpoint
 ↓
STOPPING
 ↓
TERMINATED
```

---

# 742.41 — Forced Termination

Nếu application không phản hồi:

```text
grace period
    ↓
force terminate
```

Quyền force terminate phải được security policy kiểm soát.

---

# 742.42 — Termination Reason

```axiom
termination_reason {
    user
    system
    crash
    resource_limit
    security_policy
    shutdown
    replacement
}
```

---

# 742.43 — Multi-Instance Policy

```text
ALLOW_MULTIPLE
SINGLE_INSTANCE
SINGLE_PER_USER
SINGLE_PER_WORKSPACE
CUSTOM
```

---

# 742.44 — Single Instance

Nếu application yêu cầu single instance:

```text
launch
 ↓
existing instance?
 ├── yes → activate
 └── no  → create
```

---

# 742.45 — Activation

Activation có thể:

```text
focus window
switch workspace
restore minimized window
raise application
send activation payload
```

AXDESKTOP/AXWINDOW thực hiện presentation semantics.

---

# 742.46 — Application-to-Window Mapping

```axiom
application_window_binding {
    application_instance
    window
    role
}
```

Roles:

```text
MAIN
DIALOG
UTILITY
TOOL
CHILD
OVERLAY
```

---

# 742.47 — Window Does Not Define Application

Một window phải có thể tồn tại mà không dùng path-based application inference.

---

# 742.48 — Process-to-Window Mapping

Một process có thể sở hữu:

```text
zero windows
one window
many windows
```

---

# 742.49 — Headless Application

Application không có UI:

```text
application
   ↓
process
```

không cần AXWINDOW.

---

# 742.50 — Service Application

Một application có thể cung cấp background service:

```text
application
   └── service
```

Service lifecycle phải được quản lý explicit.

---

# 742.51 — Application Service

```axiom
application_service {
    id
    application
    endpoints
    lifecycle
    capabilities
}
```

---

# 742.52 — Service vs Process

Một service không nhất thiết tương ứng 1:1 với process.

---

# 742.53 — IPC Endpoint

```axiom
application_endpoint {
    id
    application
    process
    protocol
    capabilities
}
```

---

# 742.54 — Native IPC

IPC phải hỗ trợ:

```text
typed messages
shared memory
handles
capabilities
cancellation
deadlines
streaming
events
```

Transport implementation có thể dùng native local IPC backend.

---

# 742.55 — IPC Security

Cross-process communication phải kiểm tra:

```text
principal
endpoint
action
capability
```

---

# 742.56 — Shared Memory

Đối với dữ liệu lớn:

```text
process A
   ↓
shared memory
   ↓
process B
```

ưu tiên zero-copy.

---

# 742.57 — Handle Passing

Resource handle có thể được transfer qua IPC với explicit capability attenuation.

---

# 742.58 — Application Environment

```axiom
application_environment {
    variables
    working_directory
    locale
    timezone
    identity
    capabilities
}
```

---

# 742.59 — Environment Isolation

Application không được mặc định nhìn thấy environment secrets của process khác.

---

# 742.60 — Working Directory

Working directory là process/application runtime state, không phải filesystem authority.

---

# 742.61 — Application Locale

Locale có thể được inherited từ user session nhưng application có thể override trong phạm vi policy.

---

# 742.62 — Application Data Directory

Mỗi application có thể có logical storage namespace:

```text
application_data
application_cache
application_config
application_state
```

---

# 742.63 — Storage Isolation

Application data directory không đồng nghĩa arbitrary filesystem access.

---

# 742.64 — Application Cache

Cache:

```text
rebuildable
discardable
versioned
```

không được coi là authoritative application state.

---

# 742.65 — Configuration

Configuration khác application state:

```text
configuration → user/system preference
state         → current logical progress
cache         → rebuildable data
```

---

# 742.66 — Package Trust

Package có thể chứa:

```text
manifest
executable
resources
signature
dependency metadata
```

Trust verification:

→ `AXSECURITY`.

---

# 742.67 — Artifact Integrity

Executable hash:

```axiom
artifact_hash
```

được ghi nhận để:

```text
identity
integrity
diagnostics
reproducibility
```

---

# 742.68 — Dependency Resolution

Application có thể khai báo:

```axiom
dependency {
    name
    version_range
    optional
}
```

Resolution phải deterministic.

---

# 742.69 — Dependency Failure

Nếu dependency không thỏa mãn:

```text
launch
 ↓
resolve dependencies
 ↓
failure
```

Application không được chạy với dependency version không tương thích chỉ vì "gần đúng".

---

# 742.70 — Native Runtime Compatibility

Executable có thể khai báo:

```text
architecture
ABI
runtime ABI
OS capability
minimum runtime version
```

---

# 742.71 — No Hidden Runtime Dependency

Mục tiêu Axiom:

```text
native application
      ↓
Axiom runtime primitives
```

không được ép mọi application phụ thuộc vào một monolithic external runtime.

Runtime component phải được link/package theo nhu cầu.

---

# 742.72 — Runtime Component Model

```text
application
 ├── core runtime
 ├── memory
 ├── threading
 ├── filesystem
 ├── networking
 └── graphics
```

Chỉ link những components cần thiết.

---

# 742.73 — Static vs Dynamic Runtime

AXAPPLICATION phải hỗ trợ:

```text
fully static
shared runtime
hybrid
```

nhưng semantics application không phụ thuộc deployment choice.

---

# 742.74 — Process Resource Accounting

Track:

```text
CPU time
wall time
memory
I/O
GPU time
network bytes
storage bytes
thread count
handle count
```

---

# 742.75 — Resource Quotas

```axiom
application_quota {
    cpu
    memory
    gpu
    io
    network
}
```

---

# 742.76 — Resource Exceeded

Có thể:

```text
warn
throttle
suspend
terminate
```

theo policy.

Không tự động terminate nếu policy không yêu cầu.

---

# 742.77 — Application Priority

```text
interactive
normal
background
system
```

Priority không bypass security.

---

# 742.78 — Thread Policy

AXAPPLICATION có thể đặt policy:

```text
thread_limit
priority
affinity
background_policy
```

Actual scheduling:

→ `AXCOMPUTE`.

---

# 742.79 — Application GPU Context

Application có thể có:

```text
graphics contexts
compute contexts
video contexts
```

Resource ownership thuộc graphics/compute layers.

---

# 742.80 — Application Device Access

Device access phải đi qua:

```text
AXSECURITY
+
device capability
```

Không application nào được mặc định truy cập raw hardware.

---

# 742.81 — Application Focus

Application activation flow:

```text
AXAPPLICATION
 ↓
AXDESKTOP
 ↓
AXWINDOW
```

AXAPPLICATION không trực tiếp thao tác compositor z-order.

---

# 742.82 — Application Close Request

```axiom
request_application_close(instance_id)
```

có thể dẫn tới:

```text
application receives close request
 ↓
save state
 ↓
close windows
 ↓
terminate processes
```

---

# 742.83 — Application Suspend Request

```axiom
suspend_application(instance_id)
```

Application có cơ hội:

```text
flush state
checkpoint
release resources
```

---

# 742.84 — Resource Reclamation

Khi suspended:

```text
GPU resources
temporary buffers
cache
network connections
```

có thể được reclaim theo policy.

---

# 742.85 — State Rehydration

Resume sau resource reclamation:

```text
checkpoint
   ↓
recreate resources
   ↓
restore logical state
   ↓
RUNNING
```

---

# 742.86 — Application Update

Update flow:

```text
new package
 ↓
verify
 ↓
stage
 ↓
quiesce application
 ↓
checkpoint
 ↓
switch executable
 ↓
restart
 ↓
restore state
```

---

# 742.87 — Rollback

Nếu update thất bại:

```text
new version
   ↓
failure
   ↓
previous known-good version
```

Application state migration phải reversible hoặc checkpoint trước migration.

---

# 742.88 — Application Upgrade Identity

Application identity không đổi khi version đổi.

---

# 742.89 — Application Uninstall

Uninstall phải phân biệt:

```text
remove package
remove executable
remove user data
remove cache
remove configuration
```

Các thao tác này phải explicit.

---

# 742.90 — Data Retention

Uninstall không mặc định xóa toàn bộ user data.

Policy phải xác định rõ.

---

# 742.91 — Application Events

```text
application_registered
application_updated
application_launch_requested
application_starting
application_started
application_suspended
application_resumed
application_stop_requested
application_stopped
application_crashed
application_recovering
application_failed
application_unregistered
```

---

# 742.92 — Process Events

```text
process_created
process_started
process_suspended
process_resumed
process_exit_requested
process_terminated
process_crashed
```

---

# 742.93 — Event Ordering

Application events phải có:

```axiom
application_event {
    sequence
    timestamp
    application
    instance
    process
    type
}
```

---

# 742.94 — Telemetry

Application telemetry:

```text
launch_latency
startup_latency
shutdown_latency
crash_count
restart_count
memory_peak
cpu_time
gpu_time
io_bytes
network_bytes
suspend_latency
resume_latency
checkpoint_latency
```

---

# 742.95 — Diagnostics

```axiom
application_diagnostics {
    application
    instance
    processes
    resources
    crashes
    checkpoints
    security_events
}
```

---

# 742.96 — Application Simulation

```axiom
application_simulation {
    application
    manifest
    resources
    policies
    events
}
```

Simulation có thể test:

```text
launch
suspend
resume
crash
restart
update
rollback
resource exhaustion
IPC
```

---

# 742.97 — Deterministic Replay

Cùng:

```text
application descriptor
initial state
event sequence
policy version
```

phải tạo cùng logical lifecycle state.

---

# 742.98 — Digital Twin

```axiom
application_digital_twin {
    application
    instances
    processes
    resources
    lifecycle
}
```

Dùng cho:

```text
testing
deployment simulation
crash recovery
resource planning
automation
```

---

# 742.99 — AI Application Assistant

AI có thể:

```text
suggest application grouping
suggest restart
summarize diagnostics
find crash patterns
suggest resource tuning
prepare launch configuration
```

---

# 742.100 — AI Authority Boundary

AI không được tự động:

```text
grant capability
disable sandbox
bypass security
read another application's private state
force terminate protected process
install untrusted executable
```

---

# 742.101 — Application AI Metadata

```axiom
application_ai_metadata {
    purpose
    capabilities
    resource_profile
    state_schema
    diagnostics
}
```

Metadata là machine-readable description, không phải security authority.

---

# 742.102 — Application Automation

```axiom
application_action {
    application
    action
    parameters
    capability
}
```

Automation phải capability-bound.

---

# 742.103 — Application-to-Application Activation

```text
Application A
     ↓
activation request
     ↓
AXAPPLICATION
     ↓
authorization
     ↓
Application B
```

Không truyền arbitrary memory.

---

# 742.104 — Deep Link

```axiom
application_uri {
    scheme
    path
    parameters
}
```

Resolver:

```text
URI
 ↓
handler
 ↓
application
 ↓
instance
```

---

# 742.105 — URI Security

URI parameters không được mặc định trở thành executable command hoặc capability.

---

# 742.106 — Application Notification Integration

Application có thể request notification:

```text
application
 ↓
AXSHELL / AXDESKTOP
```

AXAPPLICATION chỉ cung cấp application identity/context.

---

# 742.107 — Application Window Restore

Restore flow:

```text
checkpoint
 ↓
application launch
 ↓
state restore
 ↓
window recreation
 ↓
AXDESKTOP placement restore
```

---

# 742.108 — Native API

```axiom
register_application()
unregister_application()

get_application()
list_applications()

install_application_package()
verify_application_package()
update_application()

launch_application()
activate_application()

create_application_instance()
destroy_application_instance()

list_instances()

create_process()
terminate_process()
force_terminate_process()

suspend_application()
resume_application()

request_application_close()

create_process_group()
add_process_to_group()
remove_process_from_group()

request_capability()
release_capability()

set_resource_policy()
get_resource_usage()

create_application_checkpoint()
restore_application_checkpoint()

get_application_state()
set_application_state()

register_application_service()
unregister_application_service()

create_ipc_endpoint()
destroy_ipc_endpoint()

register_deep_link()
resolve_deep_link()

get_application_windows()

get_application_diagnostics()
get_application_telemetry()

create_application_simulation()
record_application()
replay_application()
```

---

# 742.109 — Canonical Flow: Launch

```text
AXSHELL
   ↓
AXAPPLICATION
   ↓
resolve application_id
   ↓
resolve package
   ↓
verify artifact
   ↓
AXSECURITY
   ↓
create sandbox
   ↓
allocate resources
   ↓
create process
   ↓
start executable
   ↓
application RUNNING
   ↓
create windows
   ↓
AXWINDOW
   ↓
AXDESKTOP
```

---

# 742.110 — Canonical Flow: Crash Recovery

```text
process
 ↓
unexpected exit
 ↓
AXAPPLICATION
 ↓
CRASHED
 ↓
capture diagnostics
 ↓
checkpoint lookup
 ↓
restart policy
 ↓
RECOVERING
 ↓
new process
 ↓
restore state
 ↓
RUNNING
```

---

# 742.111 — Canonical Flow: Suspend/Resume

```text
RUNNING
   ↓
SUSPENDING
   ↓
checkpoint
   ↓
release reclaimable resources
   ↓
SUSPENDED
   ↓
RESUMING
   ↓
rehydrate resources
   ↓
restore state
   ↓
RUNNING
```

---

# 742.112 — Canonical Flow: Update

```text
old package
    ↓
new package
    ↓
verify signature/integrity
    ↓
stage
    ↓
checkpoint
    ↓
stop
    ↓
activate new version
    ↓
start
    ↓
migrate state
    ↓
restore
```

---

# 742.113 — Canonical Flow: Single Instance

```text
launch request
      ↓
application identity
      ↓
instance policy
      ↓
existing instance?
   ┌──┴──┐
  yes    no
   ↓      ↓
activate  create
```

---

# 742.114 — Formal Invariants

```text
APP-INV-01   Application identity is stable across executable instances.
APP-INV-02   Application identity is distinct from executable identity.
APP-INV-03   Application identity is distinct from process identity.
APP-INV-04   Application identity is distinct from package identity.
APP-INV-05   Application instance identity is stable for its lifecycle.
APP-INV-06   Process identity is stable for its lifecycle.
APP-INV-07   Process groups have explicit membership.
APP-INV-08   Application lifecycle and process lifecycle are distinct.
APP-INV-09   Application state is distinct from process memory.
APP-INV-10   Application configuration, state, and cache are distinct.

APP-INV-11   Launch requires explicit application resolution.
APP-INV-12   Executable integrity is verified before execution when policy requires it.
APP-INV-13   Requested capabilities do not imply granted capabilities.
APP-INV-14   Capability authority remains owned by AXSECURITY.
APP-INV-15   Sandbox policy is explicit.
APP-INV-16   Resource policy is explicit.
APP-INV-17   Resource scheduling remains owned by AXCOMPUTE.
APP-INV-18   Application cannot bypass sandbox through ordinary launch APIs.
APP-INV-19   Cross-process IPC requires explicit endpoint semantics.
APP-INV-20   Cross-process resource transfer requires explicit authority.

APP-INV-21   Single-instance policy is explicit.
APP-INV-22   Application activation is distinct from process creation.
APP-INV-23   A process may exist without a window.
APP-INV-24   A window does not define application identity.
APP-INV-25   Application suspension does not necessarily imply termination.
APP-INV-26   Application checkpoint is distinct from process memory snapshot.
APP-INV-27   Restored state is schema-versioned.
APP-INV-28   Expired capabilities are never restored as valid authority.
APP-INV-29   Crash detection produces an explicit lifecycle event.
APP-INV-30   Restart policy is bounded and explicit.

APP-INV-31   Crash-loop recovery cannot restart indefinitely without policy.
APP-INV-32   Forced termination requires explicit authority.
APP-INV-33   Application update verifies the new artifact before activation.
APP-INV-34   Application identity survives version updates.
APP-INV-35   Uninstall does not implicitly imply deletion of user data.
APP-INV-36   AI suggestions cannot grant application capabilities.
APP-INV-37   AI cannot bypass sandbox or security policy.
APP-INV-38   Simulation cannot mutate production application state.
APP-INV-39   Replay cannot mutate production application state.
APP-INV-40   Identical initial application state, event sequence, and policy produce identical logical lifecycle state.
```

---

# 742.115 — Completion Criteria

`BOOTSTRAP-742` phải freeze:

1. Application identity.
2. Application descriptor.
3. Application version.
4. Executable identity.
5. Package identity.
6. Application instance.
7. Process.
8. Process group.
9. Application lifecycle.
10. Process lifecycle.
11. Launch request.
12. Launch authorization.
13. Capability request.
14. Capability grant boundary.
15. Sandbox.
16. Sandbox profile.
17. Resource policy.
18. CPU policy.
19. GPU policy.
20. Background execution.
21. Suspension.
22. Resume.
23. Constrained-device lifecycle.
24. Application state.
25. Checkpoint.
26. State persistence.
27. State schema migration.
28. Crash detection.
29. Crash classification.
30. Restart policy.
31. Crash-loop protection.
32. Graceful termination.
33. Forced termination.
34. Termination reason.
35. Multi-instance policy.
36. Single-instance activation.
37. Application/window binding.
38. Headless applications.
39. Service applications.
40. IPC endpoints.
41. Shared memory.
42. Handle transfer.
43. Environment isolation.
44. Application storage namespaces.
45. Package trust.
46. Artifact integrity.
47. Dependency resolution.
48. Runtime compatibility.
49. Runtime component model.
50. Static/dynamic runtime deployment.
51. Resource accounting.
52. Resource quotas.
53. Device access.
54. Application activation.
55. Application close.
56. Resource reclamation.
57. State rehydration.
58. Application update.
59. Rollback.
60. Uninstall/data retention.
61. Application events.
62. Process events.
63. Telemetry.
64. Diagnostics.
65. Simulation.
66. Replay.
67. Digital twin.
68. AI boundary.
69. Automation.
70. Deep links.
71. Window restore.
72. Native API.
73. Canonical lifecycle flows.
74. 40 formal invariants.

---

# 742.116 — Definition of Done

```text
BOOTSTRAP-742
STATUS: COMPLETE / FROZEN

AXAPPLICATION
 ├── Application Identity
 ├── Package / Executable Model
 ├── Application Instance
 ├── Process Model
 ├── Process Groups
 ├── Lifecycle
 ├── Launch
 ├── Termination
 ├── Multi-Instance Policy
 ├── Sandbox Integration
 ├── Capabilities
 ├── Resource Policies
 ├── Background Execution
 ├── Suspension / Resume
 ├── Application State
 ├── Checkpoints
 ├── Crash Detection
 ├── Crash Recovery
 ├── Restart Policy
 ├── IPC
 ├── Shared Memory
 ├── Service Integration
 ├── Window Binding
 ├── Package Update
 ├── Rollback
 ├── Data Retention
 ├── Diagnostics
 ├── Telemetry
 ├── AI Boundary
 ├── Simulation
 ├── Replay
 ├── Digital Twin
 ├── Native API
 ├── 40 Formal Invariants
 └── Application Runtime 5.0
```

**BOOTSTRAP-742 / AXAPPLICATION — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-743 — AXPROCESS

**Native Process, Thread & Execution Context Runtime — process address spaces, execution contexts, threads, thread groups, stacks, TLS, scheduling contracts, priorities, affinity, CPU topology, synchronization integration, cancellation, signals/exceptions, process supervision, job/process trees, resource accounting, process isolation, shared memory, handles, IPC integration, process checkpoints, crash boundaries, deterministic process simulation, execution tracing và Process Runtime 5.0.**