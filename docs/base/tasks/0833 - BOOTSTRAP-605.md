Tiếp tục tự động với **BOOTSTRAP-605**, nối trực tiếp trên nền State → Config → Diagnostics → Security → IPC đã hoàn thiện.

:::writing{variant="document" id="74106" title="BOOTSTRAP-605 — Native Process & Service Supervision, Lifecycle, Health, Watchdog & Recovery Runtime 5.0"}

# BOOTSTRAP-605
## Native Application Process & Service Supervision, Lifecycle, Health, Watchdog & Recovery Runtime 5.0

**Status:** Architecture Specification  
**Phase:** Native Runtime / Application Infrastructure  
**Depends on:** BOOTSTRAP-600, 601, 602, 603, 604  
**Scope:** Process lifecycle, service lifecycle, supervision, health, watchdog, restart và recovery  
**Primary goals:** deterministic lifecycle, failure isolation, bounded recovery, native performance, cross-platform abstraction, capability-safe orchestration.

---

# 605.0 — Mục tiêu

Axiom cần một runtime có khả năng quản lý vòng đời của:

```text
Process
Service
Worker
Child Process
Plugin Process
Application
```

Hệ thống phải xử lý:

- start;
- stop;
- restart;
- crash;
- timeout;
- dependency;
- health;
- watchdog;
- resource limit;
- graceful shutdown;
- recovery;
- service activation;
- service isolation.

Runtime phải **không biến thành một operating system thu nhỏ**.

OS vẫn chịu trách nhiệm về process primitive.

Axiom chịu trách nhiệm về:

```text
policy
lifecycle
dependency
supervision
health
recovery
```

---

# 605.1 — Boundary

Architecture:

```text
Application
    ↓
Service Manager
    ↓
Process Supervisor
    ↓
IPC
    ↓
Operating System
```

Trong đó:

```text
BOOTSTRAP-604 = communication
BOOTSTRAP-605 = lifecycle
```

---

# 605.2 — Process

`Process` là đơn vị isolation do OS quản lý.

Axiom process abstraction:

```text
ProcessId
Generation
State
Identity
Capabilities
Resources
```

---

# 605.3 — Process state

State machine:

```text
Created
   ↓
Starting
   ↓
Running
   ↓
Stopping
   ↓
Stopped
```

Failure:

```text
Starting → Failed
Running  → Crashed
Stopping → Failed
```

Recovery:

```text
Crashed → Restarting
Restarting → Starting
```

---

# 605.4 — Process generation

Mỗi process instance có:

```text
ProcessId
Generation
```

Khi restart:

```text
ProcessId may reuse
Generation must change
```

Do đó:

```text
(ProcessId, Generation)
```

mới là identity đầy đủ.

---

# 605.5 — Service

Service là logical unit có thể có nhiều process implementation.

Ví dụ:

```text
ImageService
    instance 1
    instance 2
```

Service identity khác process identity.

---

# 605.6 — Service state

```text
Declared
Disabled
Starting
StartingDependencies
Ready
Running
Degraded
Stopping
Stopped
Failed
Restarting
```

---

# 605.7 — Service instance

Mỗi instance có:

```text
ServiceId
InstanceId
ProcessId
Generation
State
Health
```

---

# 605.8 — Desired state

Supervisor duy trì:

```text
DesiredState
ActualState
```

Ví dụ:

```text
desired = Running
actual = Crashed
```

Supervisor phải cố gắng converge:

```text
actual → desired
```

---

# 605.9 — Reconciliation

Supervisor loop:

```text
observe
↓
compare desired/actual
↓
apply action
↓
observe again
```

Không được tạo busy loop.

---

# 605.10 — Desired state examples

```text
Disabled
Stopped
Running
```

Higher-level orchestration có thể yêu cầu:

```text
Running
```

Supervisor tự xử lý restart nếu policy cho phép.

---

# 605.11 — No infinite restart loop

Restart policy phải có:

```text
max_restarts
restart_window
backoff
```

---

# 605.12 — Restart policy

Các mode:

```text
Never
OnFailure
Always
OnCrash
OnHealthFailure
```

---

# 605.13 — Restart backoff

Ví dụ conceptual:

```text
100ms
200ms
400ms
800ms
...
max_backoff
```

Không hard-code một giá trị duy nhất.

---

# 605.14 — Jitter

Multi-process systems có thể dùng bounded jitter để tránh simultaneous restart storm.

---

# 605.15 — Restart budget

Mỗi service có restart budget:

```text
N restarts / T
```

Nếu vượt:

```text
Failed
```

và supervisor không retry vô hạn.

---

# 605.16 — Crash loop detection

Crash loop được phát hiện dựa trên:

```text
crash count
time window
startup duration
```

Không chỉ dựa vào tổng số crash suốt lifetime.

---

# 605.17 — Startup duration

Service crash ngay sau startup là tín hiệu đặc biệt.

Supervisor ghi:

```text
startup_duration
```

để crash-loop detection.

---

# 605.18 — Dependency graph

Service dependencies:

```text
A → B
B → C
```

nghĩa A yêu cầu B và B yêu cầu C.

---

# 605.19 — Dependency types

```text
Required
Optional
Weak
StartupOnly
Runtime
```

---

# 605.20 — Required dependency

Nếu:

```text
A requires B
```

B unavailable:

```text
A không được Ready
```

---

# 605.21 — Optional dependency

Nếu:

```text
A optionally uses B
```

A vẫn có thể chạy:

```text
Degraded
```

---

# 605.22 — StartupOnly dependency

Dependency chỉ cần tồn tại lúc initialization.

Sau đó service có thể tiếp tục chạy nếu dependency mất.

---

# 605.23 — Runtime dependency

Dependency phải duy trì trong toàn bộ thời gian service hoạt động.

---

# 605.24 — Dependency cycle

Graph:

```text
A → B
B → C
C → A
```

phải bị reject hoặc yêu cầu explicit cycle-breaking mechanism.

Supervisor không tự chọn arbitrary order.

---

# 605.25 — Startup ordering

Nếu:

```text
A → B
```

thì:

```text
B start
B Ready
A start
```

---

# 605.26 — Shutdown ordering

Ngược lại:

```text
A stop
B stop
```

để tránh consumer chết trước dependency theo cách không an toàn.

---

# 605.27 — Parallel startup

Các service không phụ thuộc nhau có thể start song song.

```text
A → C
B → C

A ─┐
   ├→ C
B ─┘
```

A và B có thể start concurrently.

---

# 605.28 — Dependency readiness

Process `Running` không đồng nghĩa service `Ready`.

Ví dụ:

```text
process started
IPC endpoint created
database initialized
service ready
```

---

# 605.29 — Ready condition

Service phải explicit report readiness.

Ví dụ:

```axiom id="6f7v9m"
service.ready()
```

---

# 605.30 — Health model

Health gồm:

```text
Healthy
Degraded
Unhealthy
Unknown
```

Health không nhất thiết phản ánh process state.

---

# 605.31 — Liveness

Liveness trả lời:

```text
process còn hoạt động không?
```

---

# 605.32 — Readiness

Readiness trả lời:

```text
service có nhận request mới không?
```

---

# 605.33 — Startup health

Startup health có deadline riêng:

```text
startup_timeout
```

---

# 605.34 — Runtime health

Runtime health có thể dựa trên:

- heartbeat;
- IPC health check;
- application signal;
- OS state.

---

# 605.35 — Health check API

```axiom id="9m4pzw"
health.check()
```

Trả:

```text
HealthStatus
HealthDetails
```

---

# 605.36 — Health details

Có thể chứa:

```text
reason
component
timestamp
metrics
```

Không chứa secret.

---

# 605.37 — Health aggregation

Application health:

```text
Application
 ├── Service A: Healthy
 ├── Service B: Healthy
 └── Service C: Degraded
```

Supervisor có thể tính aggregate:

```text
Healthy
Degraded
Unhealthy
```

Policy quyết định aggregation.

---

# 605.38 — Watchdog

Watchdog phát hiện service không còn phản hồi.

Có hai cấp:

```text
Process Watchdog
Service Watchdog
```

---

# 605.39 — Process watchdog

Theo dõi OS-level liveness:

```text
process exists?
process exited?
```

---

# 605.40 — Service watchdog

Theo dõi logical health:

```text
heartbeat
response
progress
```

---

# 605.41 — Heartbeat

Heartbeat phải lightweight:

```text
PING
PONG
```

hoặc application-defined health message.

---

# 605.42 — Heartbeat timeout

Nếu heartbeat không nhận được trong:

```text
heartbeat_timeout
```

service có thể chuyển:

```text
Suspected
```

---

# 605.43 — Failure confirmation

Không restart ngay sau một missed heartbeat.

Có thể dùng:

```text
miss threshold
```

để giảm false positive.

---

# 605.44 — Watchdog state

```text
Healthy
Suspected
Unresponsive
Recovering
```

---

# 605.45 — Watchdog action

Policy:

```text
Observe
Notify
GracefulRestart
ForceRestart
Stop
```

---

# 605.46 — Force kill

Force termination chỉ được sử dụng sau graceful stop timeout hoặc explicit policy.

---

# 605.47 — Graceful stop

Sequence:

```text
StopRequested
↓
stop accepting work
↓
finish allowed work
↓
close IPC
↓
release resources
↓
exit
```

---

# 605.48 — Stop timeout

Nếu process không exit trong:

```text
shutdown_timeout
```

supervisor có thể escalate.

---

# 605.49 — Shutdown escalation

```text
GracefulStop
    ↓ timeout
Terminate
    ↓ timeout
ForceKill
```

Platform adapter thực hiện primitive.

---

# 605.50 — Shutdown reason

Process nhận reason:

```text
UserRequest
DependencyFailure
Restart
ApplicationShutdown
SystemShutdown
Policy
```

---

# 605.51 — Restart reason

Restart metadata:

```text
Crash
HealthFailure
ConfigChange
Manual
DependencyRecovery
Policy
```

---

# 605.52 — Restart identity

Restart tạo instance mới:

```text
InstanceId++
Generation++
```

Client không được assume old instance state.

---

# 605.53 — IPC integration

Supervisor sử dụng BOOTSTRAP-604 để:

- connect service;
- detect disconnect;
- health-check;
- send shutdown;
- receive readiness;
- register endpoint.

---

# 605.54 — IPC disconnect

Disconnect không luôn đồng nghĩa crash.

Có thể là:

```text
NormalStop
Network/TransportFailure
Crash
PolicyTermination
```

Supervisor lấy OS process status để phân biệt khi có thể.

---

# 605.55 — Crash classification

Crash artifact từ BOOTSTRAP-602 được liên kết:

```text
ServiceId
InstanceId
ProcessId
Generation
BuildId
```

---

# 605.56 — Crash record

Crash record:

```text
timestamp
service
instance
exit reason
signal/exception
build ID
config fingerprint
capability policy fingerprint
```

---

# 605.57 — No secret leakage

Crash record không chứa:

- Secret values;
- IPC payload;
- raw capability token.

---

# 605.58 — Process specification

Process declaration:

```text
Executable
Arguments
Environment
WorkingDirectory
Capabilities
Resources
RestartPolicy
HealthPolicy
```

---

# 605.59 — Service specification

Service declaration:

```text
ServiceId
ProcessSpec
Dependencies
Endpoints
HealthPolicy
RestartPolicy
ResourcePolicy
```

---

# 605.60 — Immutable specification

Loaded service specification phải trở thành immutable snapshot.

Phù hợp BOOTSTRAP-601.

---

# 605.61 — Environment

Environment inheritance phải explicit.

Mặc định không blindly inherit toàn bộ privileged environment.

---

# 605.62 — Working directory

Working directory phải canonicalized.

---

# 605.63 — Executable identity

Supervisor xác minh executable identity:

```text
path
build ID
optional signature
```

theo security policy.

---

# 605.64 — Binary trust

BOOTSTRAP-603 quyết định binary có được execute hay không.

Supervisor không bypass trust policy.

---

# 605.65 — Capability provisioning

Process start có thể nhận:

```text
filesystem capability
network capability
IPC capability
device capability
```

Supervisor phải tạo capability set theo policy.

---

# 605.66 — Least privilege

Service không nhận toàn bộ parent capabilities mặc định.

```text
C_service ⊆ C_supervisor
```

---

# 605.67 — Capability inheritance

Inheritance phải explicit.

Default:

```text
no inheritance
```

trừ những capability platform bắt buộc.

---

# 605.68 — Capability attenuation

Child service có thể nhận subset:

```text
READ
```

từ:

```text
READ | WRITE
```

---

# 605.69 — Resource policy

Process có:

```text
CPU
Memory
Threads
Handles
FileDescriptors
IPC
SharedMemory
```

limits.

---

# 605.70 — Memory limit

Nếu platform hỗ trợ hard memory limit, supervisor cấu hình.

Nếu không:

```text
soft monitoring
```

và health degradation.

---

# 605.71 — CPU limit

Có thể cấu hình:

```text
CPU quota
CPU affinity
priority
```

nếu platform hỗ trợ.

---

# 605.72 — Thread limit

Service không được tạo unbounded threads.

Supervisor có thể enforce OS limit hoặc runtime policy.

---

# 605.73 — Process tree

Process có thể có children.

Supervisor phải theo dõi ownership:

```text
Supervisor
 └── Service
      ├── Worker
      └── Helper
```

---

# 605.74 — Child process policy

Child process phải:

- thuộc service;
- có lifecycle policy;
- không escape supervision ngoài capability.

---

# 605.75 — Process group

Platform adapter nên hỗ trợ process group/job/container equivalent.

Mục tiêu:

```text
stop service
→ stop entire service process tree
```

---

# 605.76 — Orphan prevention

Service child không được trở thành orphan không kiểm soát khi parent chết nếu platform cho phép supervisor containment.

---

# 605.77 — Process adoption

Nếu platform yêu cầu reparenting, supervisor phải track ownership bằng platform-specific mechanism.

---

# 605.78 — Service isolation

Mỗi isolated service có thể chạy:

```text
same process
separate process
separate sandbox
```

deployment quyết định.

---

# 605.79 — In-process service

Cho low-overhead components:

```text
Service
 ↓
same process
```

Không có process crash isolation.

---

# 605.80 — Out-of-process service

Cho:

- plugins;
- untrusted modules;
- memory-heavy components;
- fault isolation.

---

# 605.81 — Isolation tradeoff

Supervisor không tự quyết định architecture.

Developer/deployment policy chọn:

```text
latency
vs
isolation
```

---

# 605.82 — Service activation

Service có thể:

```text
AlwaysOn
OnDemand
OnFirstRequest
Manual
DependencyTriggered
```

---

# 605.83 — On-demand activation

Nếu client request service chưa chạy:

```text
lookup
↓
activate
↓
wait ready
↓
request
```

Activation phải explicit policy.

---

# 605.84 — Activation timeout

Client không được chờ vô hạn.

---

# 605.85 — Activation failure

Nếu activation fail:

```text
ServiceUnavailable
```

và supervisor ghi diagnostics.

---

# 605.86 — Idle shutdown

On-demand service có thể có:

```text
idle_timeout
```

Sau đó:

```text
Running → Stopping
```

---

# 605.87 — Dependency-aware idle shutdown

Không stop service nếu service khác còn required dependency.

---

# 605.88 — Service priority

Priority có thể ảnh hưởng startup order/resource allocation.

Không được bypass security.

---

# 605.89 — Startup transaction

Startup có thể được xem như transaction:

```text
prepare
spawn
initialize
register
ready
commit
```

Nếu fail:

```text
rollback
```

---

# 605.90 — Startup rollback

Nếu A cần B và A fail:

```text
A cleanup
```

B chỉ stop nếu B được started solely for A và policy cho phép.

---

# 605.91 — Dependency ownership

Supervisor track:

```text
who caused service activation
```

để idle lifecycle chính xác.

---

# 605.92 — Service lease

On-demand service có thể có lease:

```text
acquire
renew
release
```

Lease hết hạn:

```text
idle evaluation
```

---

# 605.93 — Lease semantics

Lease không phải security capability.

Nó chỉ là lifecycle mechanism.

---

# 605.94 — Health degradation

Service có thể report:

```text
Degraded
```

mà không bị restart ngay.

Restart chỉ khi health policy yêu cầu.

---

# 605.95 — Recovery tiers

Recovery:

```text
Tier 0: observe
Tier 1: retry operation
Tier 2: reconnect
Tier 3: restart service
Tier 4: restart dependency
Tier 5: escalate application
```

Policy quyết định.

---

# 605.96 — Recovery ordering

Không restart dependency trước consumer nếu consumer vẫn đang dùng dependency.

---

# 605.97 — Cascading failure protection

Nếu dependency A fail, không được restart toàn bộ graph vô hạn.

Supervisor phải giới hạn recovery fan-out.

---

# 605.98 — Failure domain

Service group có thể khai báo:

```text
failure_domain
```

để recovery policy không lan ra toàn application.

---

# 605.99 — Bulkhead

Supervisor có thể chia:

```text
critical services
optional services
background services
```

để resource exhaustion của nhóm này không phá nhóm khác.

---

# 605.100 — Circuit breaker

Service dependency có thể có circuit:

```text
Closed
Open
HalfOpen
```

giảm request storm khi dependency liên tục fail.

---

# 605.101 — Circuit breaker scope

Circuit breaker chỉ áp dụng cho logical dependency/client path.

Không được coi là global network mechanism.

---

# 605.102 — Retry storm prevention

Retry phải có:

```text
bounded attempts
backoff
jitter
circuit breaker
```

khi cần.

---

# 605.103 — Health-check storm prevention

Health checks phải có interval và concurrency limit.

---

# 605.104 — Supervisor loop

Supervisor loop phải event-driven.

Không polling process list liên tục với tần suất cao.

---

# 605.105 — OS event integration

Platform adapter dùng:

```text
process wait primitives
job/process groups
signals
event handles
```

phù hợp platform.

---

# 605.106 — Linux adapter

Có thể sử dụng:

```text
waitpid
pidfd
signals
cgroups
```

khi capability/platform cho phép.

---

# 605.107 — Windows adapter

Có thể sử dụng:

```text
process handles
Job Objects
wait mechanisms
```

---

# 605.108 — macOS adapter

Sử dụng native process/signal mechanisms phù hợp.

---

# 605.109 — Android adapter

Supervisor phải tôn trọng Android application/service lifecycle và sandbox.

Axiom không giả định process được giữ sống vô hạn.

---

# 605.110 — iOS adapter

iOS có lifecycle/background restrictions.

Supervisor phải expose:

```text
PlatformLifecycleConstraint
```

thay vì giả lập desktop process semantics.

---

# 605.111 — WASM

WASM không có process supervisor truyền thống.

API chuyển thành host lifecycle capability.

---

# 605.112 — Embedded

Embedded target có thể chỉ hỗ trợ:

```text
Task
Service
Watchdog
```

mà không có OS process.

Architecture phải cho phép `ProcessBackend = TaskBackend`.

---

# 605.113 — Process backend abstraction

```axiom id="n1c4wh"
trait ProcessBackend {
    fn spawn(...)
    fn wait(...)
    fn terminate(...)
    fn kill(...)
}
```

---

# 605.114 — Service supervisor abstraction

```axiom id="9b6l4h"
struct Supervisor {
    ...
}

fn start(self: Supervisor, service: ServiceId)
fn stop(self: Supervisor, service: ServiceId)
fn restart(self: Supervisor, service: ServiceId)
fn status(self: Supervisor, service: ServiceId)
```

Phù hợp struct-only architecture của Axiom.

---

# 605.115 — Supervisor ownership

Supervisor là owner của process handles được nó tạo.

Không expose raw OS process handles cho application mặc định.

---

# 605.116 — Process handle

```text
ProcessHandle
```

có:

```text
ProcessId
Generation
Rights
```

---

# 605.117 — Process handle rights

Ví dụ:

```text
Observe
Stop
Restart
Kill
Inspect
```

Một service client thông thường chỉ có:

```text
Observe
```

---

# 605.118 — Privileged lifecycle operations

`Kill` và `Restart` cần capability tương ứng.

IPC connection không tự cấp quyền quản lý process.

---

# 605.119 — Supervisor capability

Supervisor API được bảo vệ bởi BOOTSTRAP-603.

---

# 605.120 — Service management API

Application có thể:

```axiom id="6rj1kw"
supervisor.status("image")
```

nhưng không mặc định:

```axiom id="k4g0f2"
supervisor.kill(any_process)
```

---

# 605.121 — Process environment isolation

Secrets từ supervisor configuration phải được truyền bằng secure mechanism.

Không ghi secret vào:

```text
command line
logs
crash reports
```

---

# 605.122 — Secret injection

Process có thể nhận opaque secret handle hoặc secure environment facility tùy platform.

---

# 605.123 — Configuration reload

BOOTSTRAP-601 config reload có thể trigger:

```text
NoAction
LiveUpdate
RestartRequired
```

---

# 605.124 — Restart-required configuration

Nếu binary/process property thay đổi:

```text
executable
arguments
capabilities
resource limits
```

có thể yêu cầu restart.

---

# 605.125 — Rolling restart

Multiple service instances:

```text
Instance A
Instance B
Instance C
```

Supervisor có thể restart từng instance để duy trì availability nếu policy cho phép.

---

# 605.126 — Rolling restart constraints

Không stop instance mới trước khi instance cũ/peer replacement đạt readiness nếu policy yêu cầu availability.

---

# 605.127 — Instance minimum

Service có thể khai báo:

```text
min_instances
max_instances
desired_instances
```

---

# 605.128 — Scaling

Dynamic scaling không thuộc core scheduler.

Supervisor chỉ cung cấp primitive:

```text
start instance
stop instance
```

Higher-level autoscaling có thể dùng chúng.

---

# 605.129 — Resource-aware activation

Nếu memory/CPU budget không đủ:

```text
ActivationDenied
```

thay vì spawn vô hạn.

---

# 605.130 — Resource reservation

Service có thể khai báo soft/hard resource requirements.

---

# 605.131 — Priority under pressure

Khi resource shortage:

```text
critical
normal
background
```

policy có thể xác định service nào bị degraded/stopped.

Không hard-code priority semantics vào core.

---

# 605.132 — Watchdog ownership

Watchdog phải có lifecycle rõ ràng.

Không được tồn tại orphan watchdog sau supervisor shutdown.

---

# 605.133 — External watchdog

Platform hardware/system watchdog có thể được adapter.

Không phụ thuộc.

---

# 605.134 — Application watchdog

Application có thể tự report progress:

```axiom id="5g7e5f"
watchdog.beat()
```

---

# 605.135 — Progress heartbeat

Long-running operation có thể báo:

```text
progress
last_activity
expected_duration
```

tránh false failure.

---

# 605.136 — Stuck operation

Supervisor không được kết luận process dead chỉ vì CPU thấp.

Health model phải phân biệt:

```text
idle
busy
blocked
dead
```

---

# 605.137 — Health timeout classes

Có:

```text
StartupTimeout
HeartbeatTimeout
RequestTimeout
ShutdownTimeout
```

không dùng một timeout global.

---

# 605.138 — Process exit code

Exit code được normalize:

```text
Exited(code)
Signaled(signal)
Exception(code)
Killed(reason)
Unknown
```

Platform-specific detail giữ riêng.

---

# 605.139 — Exit classification

Supervisor có thể classify:

```text
Success
ExpectedStop
Failure
Crash
PolicyTermination
```

---

# 605.140 — Expected stop

Nếu supervisor chủ động stop process:

```text
ExpectedStop
```

không trigger `OnFailure` restart.

---

# 605.141 — Crash reporting

Crash path:

```text
OS
 ↓
BOOTSTRAP-602
 ↓
CrashArtifact
 ↓
Supervisor
 ↓
RecoveryPolicy
```

---

# 605.142 — Crash artifact retention

Supervisor không giữ vô hạn crash artifacts.

Retention bounded theo BOOTSTRAP-601 configuration.

---

# 605.143 — Crash loop diagnostics

Nếu crash loop:

```text
service failed repeatedly
restart budget exhausted
```

Diagnostics phải ghi rõ:

```text
restart count
window
last failure
build ID
config fingerprint
```

---

# 605.144 — State checkpoint

Supervisor có thể checkpoint:

```text
desired states
service instance metadata
restart counters
dependency state
```

Không checkpoint OS process IDs như identity lâu dài.

---

# 605.145 — Recovery after supervisor restart

Sau supervisor restart:

```text
load desired state
↓
discover actual processes
↓
match generations/identity
↓
reconcile
```

Nếu process không thuộc supervisor identity:

```text
do not adopt automatically
```

trừ policy explicit.

---

# 605.146 — Adoption

Explicit adoption policy có thể dùng secure process identity token.

---

# 605.147 — Orphan services

Process còn chạy nhưng supervisor mất:

```text
Orphan
```

Policy:

```text
Terminate
Adopt
Ignore
```

---

# 605.148 — Supervisor crash safety

Supervisor itself phải:

- không corrupt state;
- persist desired state atomically;
- restore safely;
- avoid restart storms after recovery.

---

# 605.149 — Supervisor HA

High availability supervisor cluster không thuộc core native runtime.

Nếu cần, higher-level orchestration xây trên IPC/network.

---

# 605.150 — Single supervisor

Default local application:

```text
one supervisor
```

để giảm complexity.

---

# 605.151 — Multi-supervisor

Có thể có nested supervisors:

```text
Application Supervisor
 ├── Plugin Supervisor
 └── Worker Supervisor
```

Authority phải được capability-scoped.

---

# 605.152 — Supervisor hierarchy

Child supervisor không được quản lý process ngoài scope capability.

---

# 605.153 — Parent-child lifecycle

Nếu parent supervisor dừng:

```text
child supervisor
→ stop/reassign according to policy
```

---

# 605.154 — Service ownership

Mỗi service instance phải có một authoritative supervisor.

Tránh hai supervisor cùng restart một process.

---

# 605.155 — Leadership

Không dùng distributed consensus trong local supervisor.

Authority là explicit ownership.

---

# 605.156 — Process start transaction

Spawn transaction:

```text
validate spec
↓
authorize
↓
allocate resources
↓
spawn
↓
establish identity
↓
initialize IPC
↓
health check
↓
Ready
```

---

# 605.157 — Failed spawn

Nếu OS spawn fail:

```text
SpawnFailed
```

không tạo phantom process state.

---

# 605.158 — Partial startup

Nếu process start nhưng IPC initialization fail:

```text
Starting → Failed
```

Supervisor cleanup process.

---

# 605.159 — Readiness timeout

Nếu process chạy nhưng không Ready:

```text
StartupTimeout
```

Recovery policy áp dụng.

---

# 605.160 — Startup dependency failure

Nếu dependency fails:

```text
BlockedByDependency
```

không coi đó là process crash.

---

# 605.161 — Dependency recovery

Khi dependency trở lại:

```text
Blocked → Starting
```

nếu desired state vẫn Running.

---

# 605.162 — Service state events

Supervisor emits:

```text
ServiceStarted
ServiceReady
ServiceDegraded
ServiceStopped
ServiceCrashed
ServiceRestarting
ServiceFailed
```

---

# 605.163 — Event transport

Events sử dụng BOOTSTRAP-604 IPC/event infrastructure.

---

# 605.164 — Event ordering

Events của cùng service phải ordered.

Cross-service event ordering không được guarantee.

---

# 605.165 — Diagnostics

Supervisor diagnostics tích hợp BOOTSTRAP-602:

```text
lifecycle
restart
health
resource
dependency
watchdog
```

---

# 605.166 — Structured lifecycle logs

Mỗi event có:

```text
service_id
instance_id
generation
process_id
transition
reason
```

---

# 605.167 — Trace spans

Startup có thể được trace:

```text
spawn
IPC handshake
dependency wait
ready
```

---

# 605.168 — Metrics

Supervisor metrics:

```text
services_running
services_ready
services_failed
restart_count
crash_count
startup_latency
shutdown_latency
health_failures
watchdog_failures
```

---

# 605.169 — Resource metrics

Có thể track:

```text
memory
CPU
threads
handles
IPC queues
```

nếu platform hỗ trợ.

---

# 605.170 — Metric overhead

Resource polling phải configurable.

Idle supervisor phải có overhead thấp.

---

# 605.171 — Security audit

Lifecycle security events:

```text
PROCESS_START
PROCESS_STOP
PROCESS_KILL
CAPABILITY_PROVISION
SERVICE_ACTIVATION
POLICY_DENIAL
```

---

# 605.172 — Privileged operation audit

`Kill`, capability provisioning, policy override phải audit.

---

# 605.173 — Security failure

Nếu process không được cấp capability yêu cầu:

```text
StartDenied
```

Process không được start ở trạng thái privileged một phần.

---

# 605.174 — Atomic provisioning

Capability/resource setup nên hoàn thành trước khi service được công bố `Ready`.

---

# 605.175 — Service endpoint publication

Endpoint chỉ được advertise khi service:

```text
security initialized
IPC ready
application ready
```

---

# 605.176 — Endpoint withdrawal

Khi stopping:

```text
remove from discovery
stop accepting requests
```

trước khi process termination.

---

# 605.177 — Graceful service drain

Supervisor yêu cầu IPC drain:

```text
new requests rejected
existing requests finish
```

---

# 605.178 — Drain timeout

Sau deadline:

```text
terminate remaining work
```

---

# 605.179 — Request cancellation

Supervisor có thể cancel outstanding requests thông qua BOOTSTRAP-604.

---

# 605.180 — State-aware restart

Service có persistent state có thể:

```text
checkpoint
stop
restart
restore
ready
```

---

# 605.181 — Recovery checkpoint boundary

Checkpoint chỉ chứa logical state.

Không chứa:

```text
thread stack
raw pointer
OS handle
IPC socket state
```

---

# 605.182 — Stateless service

Stateless service restart đơn giản:

```text
stop → start → ready
```

---

# 605.183 — Stateful service

Stateful service phải định nghĩa:

```text
restore policy
checkpoint policy
consistency boundary
```

---

# 605.184 — Recovery failure

Nếu restore fail:

```text
RecoveryFailed
```

service không được report Ready.

---

# 605.185 — Recovery retry

Recovery retry bị giới hạn bởi restart/recovery budget.

---

# 605.186 — Degraded mode

Service có thể start ở degraded mode nếu optional dependency unavailable.

---

# 605.187 — Dependency notifications

Dependency state changes được gửi qua IPC/event.

---

# 605.188 — No polling-only architecture

Service không cần polling dependency liên tục.

Supervisor có thể push state change.

---

# 605.189 — Service contracts

Service specification có:

```text
requires
provides
health
lifecycle
capabilities
```

---

# 605.190 — Provides declaration

Ví dụ:

```text id="gkq2jd"
ImageService
provides:
    image.resize
    image.convert
```

Client discovery có thể dùng service contract.

---

# 605.191 — Requires declaration

```text id="e2kqcf"
requires:
    StorageService
```

Compiler/tooling có thể kiểm tra dependency graph.

---

# 605.192 — Static dependency validation

Build tooling nên phát hiện:

- missing service;
- cycle;
- incompatible version;
- missing capability.

---

# 605.193 — Runtime dependency validation

Runtime vẫn phải validate vì deployment có thể thay đổi.

---

# 605.194 — Service version

Service có:

```text
major
minor
patch
```

nhưng compatibility thực tế dựa trên interface schema từ BOOTSTRAP-604.

---

# 605.195 — Service replacement

Một implementation mới có thể replace implementation cũ nếu:

```text
interface compatible
capability policy compatible
resource policy compatible
```

---

# 605.196 — Blue/green

Higher-level deployment có thể chạy:

```text
old
new
```

song song.

Supervisor chỉ cung cấp primitives cần thiết.

---

# 605.197 — Service migration

Migration workflow:

```text
start new
ready new
redirect
drain old
stop old
```

---

# 605.198 — Redirect

Routing/endpoint redirection thuộc service registry layer nhưng có thể sử dụng supervisor state.

---

# 605.199 — No automatic migration semantics

Supervisor không tự di chuyển application state nếu developer không định nghĩa.

---

# 605.200 — Process priority

Priority is advisory/platform-dependent.

Không đảm bảo OS scheduling giống nhau trên mọi target.

---

# 605.201 — Affinity

CPU affinity optional.

Không được đưa vào portable correctness contract.

---

# 605.202 — Resource pressure

Supervisor có thể nhận:

```text
MemoryPressure
CPUPressure
HandlePressure
```

từ platform.

---

# 605.203 — Pressure response

Policy:

```text
Ignore
Degrade
StopOptional
Restart
Notify
```

---

# 605.204 — OOM behavior

Supervisor không được assume có thể recover sau OOM.

Critical path phải preallocate tối đa có thể.

---

# 605.205 — Supervisor emergency path

Supervisor cần emergency path nhỏ để:

```text
record failure
terminate child
persist minimal state
```

khi allocator/resource system đã cạn.

---

# 605.206 — No GC

Process supervisor không yêu cầu garbage collector.

State machines sử dụng explicit ownership.

---

# 605.207 — Memory allocation

Hot supervision loop nên dùng:

```text
preallocated state
bounded queues
object pools
```

---

# 605.208 — Event queue

Supervisor event queue bounded.

Nếu đầy:

```text
coalesce
drop low-priority diagnostics
```

nhưng không drop critical lifecycle transitions.

---

# 605.209 — Critical events

Không được drop:

```text
ProcessExited
ServiceFailed
CapabilityDenied
SecurityViolation
```

---

# 605.210 — Event coalescing

Có thể coalesce:

```text
HealthUpdate
MetricUpdate
ProgressUpdate
```

---

# 605.211 — Supervisor concurrency

Independent services có thể được reconciled parallel.

State transition của cùng một service phải serialized.

---

# 605.212 — Per-service state machine

Mỗi service có state machine riêng.

Không dùng global lock cho toàn bộ service graph.

---

# 605.213 — Dependency graph synchronization

Graph mutations phải atomic snapshot hoặc versioned.

---

# 605.214 — Configuration version

Mỗi service instance giữ:

```text
config_version
config_fingerprint
```

---

# 605.215 — Policy fingerprint

Security policy fingerprint từ BOOTSTRAP-603 được gắn vào process launch record.

---

# 605.216 — Build identity

Process launch record chứa:

```text
BuildId
CompilerVersion
Target
```

khi diagnostics bật.

---

# 605.217 — Reproducibility

Supervisor không làm thay đổi binary.

Build reproducibility thuộc compiler/build system.

Supervisor chỉ ghi identity metadata.

---

# 605.218 — Process command line

Command line được redacted trong diagnostics nếu chứa sensitive fields.

Thiết kế tốt nhất là không truyền secret qua command line.

---

# 605.219 — Environment redaction

Environment diagnostics chỉ ghi keys được allowlist.

---

# 605.220 — Working directory security

Service working directory phải nằm trong authorized filesystem capability.

---

# 605.221 — Executable path security

Executable path phải resolve dưới authorized deployment boundary.

---

# 605.222 — Path race

Supervisor nên sử dụng OS primitive an toàn khi mở/launch executable nếu platform hỗ trợ.

---

# 605.223 — Binary replacement race

Service binary update phải có deployment-level atomic replacement semantics.

Supervisor không tự assume path contents immutable.

---

# 605.224 — Build validation

Trước start:

```text
identity
signature if required
permissions
architecture
```

được validate.

---

# 605.225 — Architecture mismatch

Nếu binary không chạy trên target:

```text
InvalidBinary
```

không retry vô hạn.

---

# 605.226 — Platform availability

Service có thể khai báo target:

```text
Windows
Linux
macOS
Android
iOS
WASM
```

---

# 605.227 — Unsupported platform

Service unavailable được biểu diễn rõ:

```text
PlatformUnsupported
```

---

# 605.228 — Optional services

Unsupported optional service không làm application fail.

---

# 605.229 — Critical service

Missing required service làm application startup fail hoặc degraded theo policy.

---

# 605.230 — Application supervisor

Application itself có top-level supervisor.

```text
Application
 ├── critical services
 ├── optional services
 └── background services
```

---

# 605.231 — Application readiness

Application Ready khi required service graph đạt readiness policy.

---

# 605.232 — Application shutdown

Top-level shutdown propagates:

```text
Application
 ↓
services
 ↓
processes
```

theo dependency reverse order.

---

# 605.233 — Shutdown deadline

Global shutdown deadline được phân bổ cho service graph.

---

# 605.234 — Shutdown budget

Supervisor có thể chia deadline:

```text
critical
normal
background
```

---

# 605.235 — Shutdown failure

Nếu optional service không stop:

```text
record
continue
```

Nếu critical service không stop:

```text
escalate
```

theo policy.

---

# 605.236 — Lifecycle API

Core:

```axiom id="j7j9l0"
supervisor.start(service)
supervisor.stop(service)
supervisor.restart(service)
supervisor.status(service)
supervisor.list()
```

---

# 605.237 — Async lifecycle

```axiom id="72d4fg"
await supervisor.start_async(service)
```

---

# 605.238 — Lifecycle result

Return typed:

```text id="m1qf30"
Started
AlreadyRunning
Blocked
Denied
Failed
TimedOut
```

---

# 605.239 — Idempotent operations

`start()` trên service đã Running không spawn duplicate instance nếu desired instance count = 1.

---

# 605.240 — Stop idempotency

Stop service đã Stopped trả success-equivalent state.

---

# 605.241 — Restart semantics

Restart phải rõ:

```text stop old
wait termination
start new
wait ready
```

trừ rolling restart policy.

---

# 605.242 — Force restart

Force restart cần explicit capability.

---

# 605.243 — Service status snapshot

Status snapshot immutable:

```text
ServiceStatus {
    desired
    actual
    health
    generation
    process
    restart_count
}
```

---

# 605.244 — Status consistency

Snapshot có version:

```text
status_version
```

để tooling phát hiện stale data.

---

# 605.245 — Event subscription

Client có thể:

```axiom id="c9l9h2"
supervisor.watch(service)
```

nhận lifecycle events.

---

# 605.246 — Watcher backpressure

Supervisor watcher sử dụng BOOTSTRAP-604 backpressure semantics.

---

# 605.247 — Management IPC

Remote management sử dụng IPC capability.

Không expose management port mặc định.

---

# 605.248 — Management security

Management endpoint phải có capability riêng:

```text
service.observe
service.control
service.kill
```

---

# 605.249 — Management audit

Mọi destructive lifecycle operation được audit.

---

# 605.250 — CLI tooling

Axiom tooling có thể cung cấp:

```text
axiom service list
axiom service status
axiom service start
axiom service stop
axiom service restart
```

CLI chỉ là client của supervisor API.

---

# 605.251 — GUI tooling

GUI có thể hiển thị:

```text
service graph
health
restart count
resource usage
dependencies
```

nhưng không phải core runtime requirement.

---

# 605.252 — AI-readable lifecycle metadata

Service artifact có thể chứa:

```text
service
dependencies
capabilities
health
restart policy
resource limits
lifecycle states
```

giúp compiler/tooling/AI agents hiểu runtime topology.

---

# 605.253 — Service manifest

Artifact:

```text id="x8v8iz"
service.axsvc
```

gồm:

```text
identity
implementation
dependencies
interfaces
capabilities
resources
health
restart
platform
```

---

# 605.254 — Manifest determinism

Manifest serialization deterministic.

---

# 605.255 — Manifest security

Manifest không được chứa secret values.

---

# 605.256 — Manifest validation

Deployment validator kiểm tra:

```text
schema
dependencies
capabilities
platform
resource limits
```

---

# 605.257 — Runtime validation

Supervisor revalidates critical security properties tại startup.

---

# 605.258 — Trust boundary

Deployment manifest không phải security authority duy nhất.

Final authority:

```text
OS
→ BOOTSTRAP-603
→ Supervisor
```

---

# 605.259 — Process sandbox

Supervisor có thể request sandbox profile:

```text
Desktop
Server
Mobile
WASM
Restricted
```

Actual enforcement thuộc BOOTSTRAP-603/platform adapter.

---

# 605.260 — Sandbox failure

Nếu requested sandbox không thể áp dụng:

```text
StartDenied
```

nếu policy yêu cầu strict enforcement.

---

# 605.261 — Process environment capability

Environment access có thể bị giới hạn.

---

# 605.262 — Child capability inheritance

Child process không được inherit arbitrary parent authority.

---

# 605.263 — Supervisor authority

Supervisor là privileged component nhưng authority phải được giới hạn theo deployment.

---

# 605.264 — TCB minimization

Supervisor core chỉ chứa:

```text
state machine
process backend
dependency graph
health
recovery
```

Không chứa:

```text
serialization framework
GUI
business logic
general networking
```

---

# 605.265 — Module decomposition

Runtime modules:

```text
supervisor-core
process-backend
service-graph
health
watchdog
recovery
resource-policy
management-ipc
platform-adapter
```

---

# 605.266 — Dead stripping

Nếu application chỉ chạy một process:

```text
full service supervisor
```

không được bắt buộc link.

---

# 605.267 — Lightweight mode

Có:

```text
MinimalSupervisor
```

cho embedded/small applications.

---

# 605.268 — MinimalSupervisor

Chỉ cần:

```text
start
stop
watchdog
restart
```

---

# 605.269 — Full supervisor

Desktop/server có thêm:

```text
dependency graph
health
resource policy
activation
management IPC
```

---

# 605.270 — Embedded supervisor

Embedded có thể map:

```text
Process → Task
```

nhưng giữ cùng logical state machine.

---

# 605.271 — Testing model

Supervisor phải test với fake process backend.

---

# 605.272 — Fake process backend

Cho phép mô phỏng:

```text
spawn success
spawn failure
crash
hang
slow startup
slow shutdown
resource exhaustion
```

---

# 605.273 — Deterministic clock

Health/watchdog/restart tests phải có fake monotonic clock.

---

# 605.274 — Deterministic scheduler

Recovery tests phải có deterministic event scheduler.

---

# 605.275 — Dependency tests

Test:

```text
linear graph
parallel graph
optional dependency
cycle
missing dependency
dependency crash
dependency recovery
```

---

# 605.276 — Crash-loop tests

Test:

```text
instant crash
slow crash
intermittent crash
budget exhaustion
```

---

# 605.277 — Watchdog tests

Test:

```text
heartbeat success
single missed beat
repeated missed beats
recovery before restart
forced restart
```

---

# 605.278 — Shutdown tests

Test:

```text
graceful
timeout
force kill
child process
dependency ordering
```

---

# 605.279 — Capability tests

Verify:

```text
unauthorized start denied
unauthorized kill denied
capability attenuation
no privilege escalation
```

---

# 605.280 — Resource tests

Verify:

```text
memory limit
CPU policy
thread limit
process limit
IPC quota
```

---

# 605.281 — Recovery tests

Verify:

```text
crash
checkpoint
restart
restore
ready
```

---

# 605.282 — Supervisor crash recovery

Simulate supervisor itself crashing.

Verify:

```text
desired state persisted
actual process discovered
duplicate spawn avoided
orphan policy enforced
```

---

# 605.283 — Security fuzzing

Fuzz:

```text
service manifest
dependency graph
management requests
lifecycle commands
health payload
```

---

# 605.284 — Resource exhaustion tests

Inject:

```text
out of handles
out of memory
process creation failure
IPC unavailable
```

Supervisor phải fail predictably.

---

# 605.285 — No infinite loops invariant

Không có:

```text
restart forever
retry forever
wait forever
shutdown forever
```

mọi recovery path đều bounded hoặc explicit persistent desired-state reconciliation.

---

# 605.286 — Recovery convergence

Nếu environment ổn định và policy cho phép, supervisor phải eventually converge:

```text
actual_state = desired_state
```

---

# 605.287 — Convergence exception

Nếu permanent failure:

```text
Failed
```

và supervisor dừng retry theo budget.

---

# 605.288 — Deterministic policy

Same:

```text desired state
service spec
environment events
policy
```

phải tạo lifecycle decisions deterministic.

---

# 605.289 — Observability invariant

Mọi state transition quan trọng phải có structured diagnostic event.

---

# 605.290 — Security invariant

Supervisor không được tạo process có authority lớn hơn policy cho phép.

---

# 605.291 — Ownership invariant

Mỗi managed process phải có authoritative owner.

---

# 605.292 — Generation invariant

Restart không được reuse logical instance identity.

---

# 605.293 — Dependency invariant

Required dependency phải Ready trước dependent Ready.

---

# 605.294 — Shutdown invariant

Service không được report Stopped khi owned process vẫn còn running.

---

# 605.295 — Readiness invariant

`Ready` chỉ được công bố khi tất cả readiness requirements hoàn tất.

---

# 605.296 — Watchdog invariant

Watchdog không được kill process chỉ dựa trên một transient observation nếu policy yêu cầu confirmation.

---

# 605.297 — Resource invariant

Supervisor không được vượt quota của chính nó khi xử lý failure storm.

---

# 605.298 — Privacy invariant

Lifecycle diagnostics không chứa secret hoặc raw payload.

---

# 605.299 — Performance invariant

Supervisor phải:

```text
event-driven
bounded
low allocation
low idle CPU
```

---

# 605.300 — Minimum acceptance criteria

BOOTSTRAP-605 được coi là hoàn thành khi:

1. Có process abstraction.
2. Có service abstraction.
3. Có desired/actual state.
4. Có lifecycle state machine.
5. Có process generation.
6. Có service instance identity.
7. Có dependency graph.
8. Có startup ordering.
9. Có shutdown ordering.
10. Có parallel startup.
11. Có required/optional dependencies.
12. Có cycle detection.
13. Có readiness.
14. Có health model.
15. Có liveness.
16. Có readiness.
17. Có watchdog.
18. Có heartbeat.
19. Có startup timeout.
20. Có shutdown timeout.
21. Có restart policy.
22. Có restart budget.
23. Có exponential backoff.
24. Có crash-loop detection.
25. Có graceful shutdown.
26. Có force termination escalation.
27. Có process-tree ownership.
28. Có capability-scoped process control.
29. Có resource policy.
30. Có service activation.
31. Có on-demand service.
32. Có idle shutdown.
33. Có recovery tiers.
34. Có circuit-breaker primitive.
35. Có IPC integration.
36. Có diagnostics integration.
37. Có state/checkpoint integration.
38. Có configuration integration.
39. Có security integration.
40. Có service manifest.
41. Có AI-readable metadata.
42. Có management API.
43. Có event subscription.
44. Có deterministic tests.
45. Có fault injection.
46. Có supervisor crash recovery.
47. Có platform backend abstraction.
48. Có lightweight mode.
49. Có embedded adaptation.
50. Có bounded recovery semantics.

---

# 605.301 — Final architecture

```text
                         Axiom Application
                                │
                    ┌───────────▼───────────┐
                    │   Application         │
                    │   Supervisor          │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
        Service Graph       Health/Watchdog    Recovery
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                     Process Supervisor
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         Process A         Process B         Process C
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                         BOOTSTRAP-604
                                │
                     Native IPC / Shared Memory
                                │
                    ┌───────────▼───────────┐
                    │   OS / Platform      │
                    └──────────────────────┘

Security      → BOOTSTRAP-603
Diagnostics   → BOOTSTRAP-602
Configuration → BOOTSTRAP-601
State         → BOOTSTRAP-600
```

---

# 605.302 — Complete lifecycle

Một service production đi qua:

```text
Declared
   ↓
Policy validation
   ↓
Capability provisioning
   ↓
Resource allocation
   ↓
Process spawn
   ↓
IPC initialization
   ↓
Dependency validation
   ↓
Application initialization
   ↓
Health check
   ↓
Ready
   ↓
Running
   ↓
Health monitoring
   ↓
        ┌───────────────┐
        │               │
      Healthy        Failure
        │               │
        │        ┌──────▼──────┐
        │        │ Recovery    │
        │        └──────┬──────┘
        │               │
        │          restart budget
        │               │
        └───────────────┤
                        ↓
                    Running
                        │
                   Shutdown request
                        ↓
                     Draining
                        ↓
                      Stopped
```

---

# 605.303 — Architectural conclusion

BOOTSTRAP-605 hoàn thiện lớp **process/service lifecycle** phía trên IPC.

Axiom giờ có một chuỗi native infrastructure tương đối đầy đủ:

```text
600  State / Persistence / Recovery
601  Configuration / Secrets / Deployment
602  Logging / Diagnostics / Crash
603  Security / Capability / Permissions
604  IPC / Shared Memory / Transport
605  Process / Service Supervision / Watchdog
```

Điểm quan trọng là các lớp này không trở thành một runtime monolith.

Chúng vẫn có thể được compile/link theo module:

```text
Application
 ├── Core only
 ├── Core + Config
 ├── Core + Diagnostics
 ├── Core + IPC
 ├── Core + Supervisor
 └── Full Native Runtime
```

Axiom vì vậy vẫn giữ được mục tiêu:

```text
native
fast
small
explicit
bounded
capability-safe
no mandatory GC
no mandatory broker
no hidden ownership
```

---

# 605.304 — Task completion

**BOOTSTRAP-605 hoàn tất về mặt kiến trúc.**

## Next task

**BOOTSTRAP-606 — Native Application Resource Management, Quotas, Budgets, Scheduling & Runtime Resource Governor 5.0**

Task kế tiếp sẽ thống nhất việc quản lý:

```text
CPU
Memory
Threads
Handles
File descriptors
IPC queues
Shared memory
GPU resources
I/O
Timers
Storage
Process counts
Service budgets
```

và đặc biệt xây **Resource Governor** dùng chung cho BOOTSTRAP-601 → 605, để Axiom có một mô hình resource accounting/quota thống nhất thay vì mỗi subsystem tự quản lý giới hạn riêng.

:::