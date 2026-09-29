# BOOTSTRAP-599 — NATIVE APPLICATION SERVICE MODEL & LOCAL SERVICE HOSTING 6.0

## SERVICE REGISTRATION, SERVICE HOST, DAEMON, BACKGROUND SERVICE, SYSTEM SERVICE, STARTUP POLICY, HEALTH/READINESS, DEPENDENCY GRAPH, SUPERVISION, IPC BINDING, PRIVILEGE SEPARATION, SERVICE INSTALLATION, UPDATE, FAILURE RECOVERY & CROSS-PLATFORM SERVICE ABSTRACTION

**Trạng thái: COMPLETED / LOCKED**

`599` định nghĩa abstraction **Service** ở trên các primitive đã có:

```text
423  Ownership / Lifetime
424  Concurrency
441  Process Runtime
471  Tasks / Jobs
472  Actors
490  Security / Capability
593  Application Package
594  Process Supervision
597  Application Storage
598  IPC
```

Service không phải một loại process mới. Nó là **deployment + lifecycle + supervision + identity + IPC contract** của một process hoặc một nhóm process.

---

# 599.1. Service model

```text
                         Service
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Definition         Lifecycle          Identity
          │                 │                 │
          ▼                 ▼                 ▼
      Deployment        Supervisor        Security
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                         Process
                            │
                    ┌───────┼───────┐
                    ▼       ▼       ▼
                   IPC    Storage   Tasks
```

---

# 599.2. Service ≠ process

Một process có thể:

```text
không phải service
là service
host nhiều service
```

Service là logical runtime entity.

---

# 599.3. Service ≠ application

Một application có thể chứa:

```text
UI process
worker process
background service
helper service
```

---

# 599.4. Service ≠ daemon

`daemon` là platform-specific implementation concept.

Axiom dùng abstraction `Service`.

---

# 599.5. Service classes

Axiom chuẩn hóa:

```text
ForegroundService
BackgroundService
UserService
SystemService
OnDemandService
EphemeralService
```

---

# 599.6. Foreground service

Service có tương tác trực tiếp hoặc được user kích hoạt.

---

# 599.7. Background service

Service chạy không cần UI.

---

# 599.8. User service

Service chạy dưới user context.

---

# 599.9. System service

Service chạy với system-level lifecycle/privilege khi platform cho phép.

---

# 599.10. On-demand service

Chỉ khởi động khi có client request.

---

# 599.11. Ephemeral service

Service tồn tại trong một operation hoặc workflow.

---

# 599.12. Service definition

```axiom
service_definition {
    id
    version
    executable
    startup
    lifecycle
    ipc
    capabilities
    resources
    health
    restart
}
```

---

# 599.13. Service identity

```text
ServiceID
```

phải ổn định qua application updates.

---

# 599.14. Service instance identity

Mỗi running instance có:

```text
InstanceID
Generation
```

---

# 599.15. Service identity hierarchy

```text
ApplicationID
    ↓
ServiceID
    ↓
InstanceID
    ↓
ProcessID
```

---

# 599.16. Service version

Service version độc lập với process PID.

---

# 599.17. Service manifest

`593` application manifest có thể chứa:

```text
services[]
```

---

# 599.18. Service manifest example

```axiom
service worker {
    executable = "worker"
    startup = on_demand
    restart = on_failure
    ipc = ["worker.api"]
}
```

---

# 599.19. Service executable

Executable phải tồn tại trong deployment graph.

---

# 599.20. Service dependency

Service có thể phụ thuộc service khác.

```text
A → B → C
```

---

# 599.21. Dependency graph

```text
Service A
   │
   ▼
Service B
   │
   ▼
Service C
```

---

# 599.22. Dependency types

```text
Required
Optional
Startup
Runtime
Shutdown
```

---

# 599.23. Required dependency

Service không được Ready nếu required dependency chưa Ready.

---

# 599.24. Optional dependency

Service có thể Ready mà không có optional dependency.

---

# 599.25. Runtime dependency

Dependency chỉ cần tồn tại khi một operation cụ thể được thực hiện.

---

# 599.26. Startup dependency

Dependency phải Ready trước khi service start.

---

# 599.27. Shutdown dependency

Service có thể yêu cầu dependency vẫn còn sống trong quá trình shutdown.

---

# 599.28. Dependency cycle

Cycle phải được phát hiện trước activation.

---

# 599.29. Cycle handling

```text
A → B
B → A
```

→ `DependencyCycle`.

---

# 599.30. No implicit cycle breaking

Supervisor không tự ý phá dependency cycle bằng startup order ngẫu nhiên.

---

# 599.31. Startup policy

```text
Manual
OnBoot
OnLogin
OnDemand
OnInstall
OnEvent
```

---

# 599.32. Manual service

Chỉ start khi explicit request.

---

# 599.33. OnBoot

Start cùng lifecycle của host/OS nếu platform cho phép.

---

# 599.34. OnLogin

Start khi user session được tạo.

---

# 599.35. OnDemand

Client connection/request kích hoạt service.

---

# 599.36. OnEvent

External event có thể trigger service.

---

# 599.37. Startup conditions

Service có thể yêu cầu:

```text network
storage
device
user session
other service
```

---

# 599.38. Condition semantics

Condition không được giả định tồn tại trên mọi target.

---

# 599.39. Unsupported startup condition

Target không hỗ trợ condition → explicit `Unsupported`.

---

# 599.40. Service lifecycle

```text
Declared
   ↓
Installed
   ↓
Disabled / Enabled
   ↓
Starting
   ↓
Initializing
   ↓
Ready
   ↓
Running
   ↓
Draining
   ↓
Stopping
   ↓
Stopped
```

---

# 599.41. Failure state

```text
Starting
   ↓
Failed
   ↓
Restarting
```

---

# 599.42. Service state machine

```text
                 ┌───────────────┐
                 │    Disabled   │
                 └───────┬───────┘
                         │ enable
                         ▼
                    Installed
                         │ start
                         ▼
                     Starting
                    ┌────┴────┐
                    │         │
                  fail      success
                    │         │
                    ▼         ▼
                  Failed    Ready
                    │         │
                  retry       │
                    │         ▼
                    └────── Running
                              │
                           stop
                              ▼
                           Draining
                              │
                              ▼
                           Stopped
```

---

# 599.43. Starting

Process đã được tạo nhưng service chưa nhận traffic.

---

# 599.44. Initializing

Service đang tạo resources/configuration.

---

# 599.45. Ready

Service đã đáp ứng health/readiness contract.

---

# 599.46. Running

Service đang phục vụ request.

---

# 599.47. Draining

Không nhận request mới nhưng hoàn tất request đang chạy.

---

# 599.48. Stopping

Đang release resources.

---

# 599.49. Failed

Service không thể hoạt động bình thường.

---

# 599.50. Disabled

Service được cài đặt nhưng policy không cho phép start.

---

# 599.51. Service host

Service Host là process thực thi một hoặc nhiều service.

---

# 599.52. One-service-per-process

Default an toàn:

```text
1 service
=
1 supervised process
```

---

# 599.53. Multi-service host

Một host có thể chứa nhiều lightweight services nếu chúng có cùng trust boundary.

---

# 599.54. Host grouping

Service manifest có thể khai báo:

```text
host_group
```

---

# 599.55. Host isolation

Các service khác trust level không được đặt chung host.

---

# 599.56. Crash isolation

Một service crash trong isolated process không crash service khác.

---

# 599.57. Shared host crash

Nếu nhiều services cùng host, host crash có thể làm tất cả service trong host unavailable.

Manifest phải thể hiện dependency/risk.

---

# 599.58. Service process

Service process là ordinary Axiom native process được `594` supervise.

---

# 599.59. No special process ABI

Service không cần một ABI machine-level khác process bình thường.

---

# 599.60. Service entrypoint

Executable có entrypoint:

```axiom
service_main(...)
```

hoặc equivalent generated startup wrapper.

---

# 599.61. Generated startup wrapper

Compiler/runtime có thể generate wrapper:

```text
OS
 ↓
Axiom startup
 ↓
Service bootstrap
 ↓
User service code
```

---

# 599.62. Service context

Service nhận:

```text
ServiceContext
```

---

# 599.63. ServiceContext

```axiom
struct ServiceContext {
    identity
    configuration
    capabilities
    storage
    ipc
    cancellation
    logger
    clock
}
```

---

# 599.64. Context ownership

ServiceContext không sở hữu process-global resources ngoài lifetime contract.

---

# 599.65. Configuration

Service configuration lấy từ:

```text
package manifest
environment
user configuration
service manager
command line
```

---

# 599.66. Configuration precedence

```text
Explicit launch config
    ↓
Service manager config
    ↓
Application config
    ↓
Package defaults
```

---

# 599.67. No secret in manifest

Secrets không được embed plaintext vào service manifest.

---

# 599.68. Secret source

Service có thể nhận secret capability từ secure credential subsystem.

---

# 599.69. Service environment

Environment variables có thể được cấp riêng cho service.

---

# 599.70. Environment isolation

Service không mặc định inherit toàn bộ environment của launcher.

---

# 599.71. Working directory

Working directory phải explicit.

---

# 599.72. No CWD dependency

Service không được giả định current working directory là application directory.

---

# 599.73. Storage roots

Service sử dụng `597` để resolve:

```text AppData
Cache
Temp
```

---

# 599.74. Service-specific storage

Service có thể có riêng:

```text service_data
service_cache
service_temp
```

---

# 599.75. Storage isolation

Service A không tự động được quyền đọc Service B data.

---

# 599.76. IPC identity

Service endpoints sử dụng `598`.

---

# 599.77. Service API

Một service public API có thể là:

```axiom
service Database {
    fn query(...)
    fn execute(...)
}
```

---

# 599.78. Endpoint publication

Service chỉ publish IPC endpoint sau khi đạt Ready.

---

# 599.79. Early endpoint

Nếu cần endpoint trước Ready, endpoint phải reject calls với trạng thái rõ ràng.

---

# 599.80. Readiness

Readiness trả lời:

> service có thể nhận request bình thường hay chưa?

---

# 599.81. Liveness

Liveness trả lời:

> service process còn hoạt động không?

---

# 599.82. Health

Health tổng hợp:

```text
Live
Ready
Degraded
Failed
```

---

# 599.83. Health contract

```axiom
trait HealthProvider {
    fn liveness() -> HealthState
    fn readiness() -> HealthState
}
```

---

# 599.84. Health timeout

Health checks phải có deadline.

---

# 599.85. Health failure

Health failure không nhất thiết process failure.

---

# 599.86. Degraded

Service có thể:

```text Ready + Degraded
```

nếu vẫn phục vụ một subset functionality.

---

# 599.87. Health detail

Health response có:

```text state
reason
dependencies
timestamp
generation
```

---

# 599.88. No false healthy

Service không được report Ready trước khi required dependencies Ready.

---

# 599.89. Dependency health

Supervisor có thể evaluate dependency readiness.

---

# 599.90. Dependency startup ordering

```text
C Ready
   ↓
B Start
   ↓
B Ready
   ↓
A Start
```

---

# 599.91. Parallel startup

Independent services có thể start song song.

---

# 599.92. Deterministic startup

Dependency graph quyết định correctness; scheduling order giữa nodes độc lập không được ảnh hưởng semantic result.

---

# 599.93. Startup timeout

Mỗi service có startup deadline.

---

# 599.94. Startup timeout handling

Timeout → `StartupTimeout`.

---

# 599.95. Startup failure

Required dependency failure có thể ngăn dependent service startup.

---

# 599.96. Failure propagation

Propagation policy phải explicit:

```text StopDependents
KeepRunning
RestartDependents
Ignore
```

---

# 599.97. Default dependency failure

Required dependency failure → dependent service `Degraded` hoặc `Stopped` theo manifest policy; không tự động crash process.

---

# 599.98. Restart policy

```text Never
OnFailure
Always
OnCrash
OnExit
Manual
```

---

# 599.99. Restart limits

Service có:

```text max_restarts
window
backoff
```

---

# 599.100. Restart storm prevention

Repeated crashes phải trigger circuit breaker.

---

# 599.101. Restart backoff

```text 1s
2s
4s
8s
...
```

với upper bound.

---

# 599.102. Jitter

Distributed service restart có thể thêm bounded jitter.

---

# 599.103. Local service

Local service không bắt buộc jitter nếu deterministic startup được ưu tiên.

---

# 599.104. Crash classification

Supervisor phân biệt:

```text CleanExit
Crash
Killed
StartupFailure
Timeout
DependencyFailure
ResourceLimit
```

---

# 599.105. Exit code

Exit code là diagnostic signal, không phải sole failure classification.

---

# 599.106. Restart eligibility

Manifest có thể map exit classes → restart behavior.

---

# 599.107. Graceful stop

Stop sequence:

```text
StopAccepting
   ↓
CancelBackgroundWork
   ↓
Drain
   ↓
Flush
   ↓
CloseIPC
   ↓
ReleaseStorage
   ↓
Exit
```

---

# 599.108. Stop deadline

Service phải có maximum graceful shutdown time.

---

# 599.109. Forced stop

Deadline exceeded → supervisor force terminates process.

---

# 599.110. Forced stop diagnostics

Crash/termination record phải ghi rõ graceful shutdown failed.

---

# 599.111. Cancellation

ServiceContext cung cấp root cancellation token.

---

# 599.112. Child cancellation

Service tasks inherit cancellation unless explicitly detached.

---

# 599.113. Detached tasks

Detached tasks phải được khai báo và chịu process lifecycle.

---

# 599.114. No immortal task

Không có task nào có thể sống sau process exit.

---

# 599.115. Background worker

Worker là task/process được service quản lý.

---

# 599.116. Worker supervision

Critical workers có thể có riêng restart policy.

---

# 599.117. Actor service

Service có thể implement actor model `472`.

---

# 599.118. Queue service

Service có thể expose message queue.

---

# 599.119. Streaming service

Service có thể expose bidirectional stream.

---

# 599.120. RPC service

Service có thể expose RPC interface `598`.

---

# 599.121. Event service

Service có thể publish events.

---

# 599.122. Service protocol

Mỗi public service nên có explicit protocol/schema.

---

# 599.123. Protocol version

Service protocol version độc lập service implementation version.

---

# 599.124. API compatibility

Service update phải kiểm tra protocol compatibility.

---

# 599.125. Breaking update

Breaking protocol change có thể yêu cầu:

```text parallel version
migration
coordinated update
```

---

# 599.126. Side-by-side services

Có thể chạy:

```text service.v1
service.v2
```

song song.

---

# 599.127. Service routing

Client có thể resolve compatible service version.

---

# 599.128. No silent downgrade

Client không được silently chuyển sang incompatible API.

---

# 599.129. Service registry

Registry có thể là:

```text Process-local
Application-local
User-session
System
Remote
```

---

# 599.130. Registry ownership

Mỗi registry phải có owner/security boundary.

---

# 599.131. Local registry

Application supervisor `594` là candidate registry cho services trong application.

---

# 599.132. System registry

OS-native service manager có thể act as registry.

---

# 599.133. Axiom registry

Axiom không yêu cầu tự xây system-wide registry.

---

# 599.134. Platform service manager

Platform adapters:

```text Windows Service
systemd-like manager
launchd-like manager
Android service model
iOS lifecycle constraints
WASI host
```

---

# 599.135. Abstraction rule

Axiom API không expose platform manager names trong portable core.

---

# 599.136. Service install

Installation thuộc deployment layer `593`.

---

# 599.137. Service registration

Deployment có thể register service với OS manager.

---

# 599.138. Uninstall

Uninstall phải unregister service trước khi remove executable.

---

# 599.139. Running uninstall

Nếu service đang chạy:

```text stop
drain
unregister
remove
```

theo policy.

---

# 599.140. Failed uninstall

Nếu unregister/remove fail, package state phải preserve recovery metadata.

---

# 599.141. Service update

Update flow:

```text
Stage
 ↓
Verify
 ↓
Stop/Drain
 ↓
Switch
 ↓
Start
 ↓
Health check
 ↓
Commit
```

---

# 599.142. Update rollback

Nếu new version fails health check:

```text restore old version
```

nếu old artifact còn available.

---

# 599.143. Atomic service activation

Executable switching phải dùng deployment transaction khi platform hỗ trợ.

---

# 599.144. No partial activation

Package không được report successful update khi chỉ một phần required service activated.

---

# 599.145. Multi-service update

Service dependency graph quyết định update order.

---

# 599.146. Rolling update

Có thể update từng instance nếu service có nhiều replicas.

---

# 599.147. Local replica

Một application có thể chạy nhiều instances của cùng service.

---

# 599.148. Instance routing

Clients phải biết instance hoặc dùng logical service endpoint.

---

# 599.149. Load balancing

Local service manager có thể chọn instance.

---

# 599.150. No mandatory load balancer

Simple applications không cần load-balancing runtime.

---

# 599.151. Singleton service

Manifest có thể yêu cầu:

```text
max_instances = 1
```

---

# 599.152. Instance limit

Service có thể giới hạn số process instances.

---

# 599.153. Resource limits

Service manifest có thể declare:

```text CPU
memory
file descriptors
threads
storage
IPC
```

---

# 599.154. CPU limit

Platform adapter có thể apply CPU quota.

---

# 599.155. Memory limit

Platform adapter có thể apply memory limit.

---

# 599.156. Thread limit

Service có thể giới hạn worker threads.

---

# 599.157. File handle limit

Service có thể giới hạn open handles.

---

# 599.158. IPC limits

`598` quotas được áp dụng cho service.

---

# 599.159. Storage limits

`597` quotas được áp dụng cho service storage.

---

# 599.160. Network limits

`454` policy có thể giới hạn network capabilities.

---

# 599.161. Capability declaration

Service manifest:

```text
capabilities = [
    storage.app_data,
    ipc.service_x,
    network.outbound
]
```

---

# 599.162. Least privilege

Service chỉ nhận capabilities đã khai báo và được platform grant.

---

# 599.163. Capability attenuation

Supervisor có thể cấp subset capabilities cho worker.

---

# 599.164. Worker isolation

```text
Main Service
     │
     ├── full service capabilities
     │
     └── Worker
          ├── IPC
          └── limited storage
```

---

# 599.165. Privilege separation

Service architecture khuyến khích:

```text privileged broker
        +
unprivileged worker
```

---

# 599.166. Privileged broker

Broker thực hiện operation cần capability cao.

---

# 599.167. Unprivileged worker

Worker xử lý untrusted data với quyền tối thiểu.

---

# 599.168. IPC boundary

Broker ↔ worker sử dụng `598`.

---

# 599.169. Plugin service

Plugin có thể chạy như isolated service.

---

# 599.170. Plugin capabilities

Plugin chỉ nhận capabilities cần thiết.

---

# 599.171. Plugin crash

Plugin crash không làm host crash.

---

# 599.172. Plugin restart

Supervisor restart plugin theo policy.

---

# 599.173. Plugin version

Plugin protocol phải được compatibility-check trước startup.

---

# 599.174. Service trust level

```text
Trusted
ApplicationTrusted
Restricted
Untrusted
```

---

# 599.175. Trust level

Trust level quyết định default sandbox/capability profile.

---

# 599.176. No security by label alone

Trust label không thay thế actual OS sandbox enforcement.

---

# 599.177. Sandboxed service

Sandbox policy:

```text filesystem
network
IPC
device
process
memory
```

---

# 599.178. Service identity and signing

Package signing identity `489/550` có thể participate in trust verification.

---

# 599.179. Signature verification

Service executable phải được verify trước installation/activation nếu policy yêu cầu.

---

# 599.180. Runtime verification

Optional runtime integrity check trước startup.

---

# 599.181. Tamper detection

Tampered executable → activation rejected.

---

# 599.182. Provenance

Service provenance:

```text
SourceRevision
 ↓
BuildContext
 ↓
ArtifactHash
 ↓
PackageHash
 ↓
ServiceDefinition
 ↓
InstalledInstance
```

---

# 599.183. Service provenance metadata

Debugger/AI có thể query provenance.

---

# 599.184. AI service inspection

AI tooling có thể query:

```text service
state
dependencies
health
IPC
capabilities
resource usage
version
provenance
```

---

# 599.185. AI mutation restrictions

AI không được tự ý:

```text install service
start privileged service
grant capability
change restart policy
```

---

# 599.186. AI deployment plan

AI có thể generate:

```text ServiceDeploymentPlan
```

với:

```text changes
dependencies
capabilities
rollback
validation
```

---

# 599.187. Human approval

Security-sensitive service deployment có thể yêu cầu explicit user approval.

---

# 599.188. IDE service view

`590` có thể hiển thị:

```text
Application
 ├── Service A    Ready
 ├── Service B    Running
 └── Service C    Failed
```

---

# 599.189. Dependency visualization

IDE hiển thị:

```text
A ──→ B ──→ C
│
└──→ D
```

---

# 599.190. Service logs

`475` logs được tag:

```text
application_id
service_id
instance_id
process_id
```

---

# 599.191. Service tracing

IPC calls và internal work có thể share trace context.

---

# 599.192. Trace propagation

```text
Client
  ↓ trace
Service A
  ↓ trace
Service B
```

---

# 599.193. Trace security

Trace context không được chứa secrets.

---

# 599.194. Service metrics

Standard metrics:

```text
uptime
restart_count
request_count
error_count
latency
queue_depth
memory
CPU
```

---

# 599.195. Health metrics

Health state có thể được exported nhưng không đồng nghĩa metric health.

---

# 599.196. Startup metrics

Record:

```text
spawn_time
init_time
ready_time
```

---

# 599.197. Shutdown metrics

Record:

```text
drain_time
shutdown_time
forced_termination
```

---

# 599.198. Crash record

Crash record:

```text
service_id
instance_id
process_id
exit_reason
exit_code
timestamp
last_health_state
```

---

# 599.199. Crash dump integration

`589` crash dump được liên kết với service instance.

---

# 599.200. Debug attach

Debugger có thể attach theo:

```text ServiceID
InstanceID
ProcessID
```

---

# 599.201. Service source mapping

Debugger source mapping vẫn dùng compiler debug metadata.

---

# 599.202. Service breakpoint

Breakpoint có thể target service identity.

---

# 599.203. Service restart debugging

Debug mode có thể preserve debugger attachment across restart.

---

# 599.204. Test service

Testing framework `435` hỗ trợ:

```text start service
wait ready
invoke
assert
stop
```

---

# 599.205. Test isolation

Mỗi test service có thể nhận temporary storage `597`.

---

# 599.206. Test IPC

Mỗi test service có thể nhận virtual IPC `598`.

---

# 599.207. Test supervisor

Test harness có thể simulate `594`.

---

# 599.208. Fake dependency

Service test có thể inject mock service endpoint.

---

# 599.209. Dependency injection

Service dependencies có thể được bind bằng interface/service ID.

---

# 599.210. No hidden global singleton

Service dependencies không được hardcode global singleton trong application code.

---

# 599.211. Service interface

```axiom
trait Service {
    fn start(ctx: ServiceContext) -> Result<(), ServiceError>
    fn stop(ctx: StopContext) -> Result<(), ServiceError>
    fn health() -> HealthState
}
```

---

# 599.212. Service start idempotency

Repeated start request không được tạo duplicate instance nếu service singleton.

---

# 599.213. Service stop idempotency

Stop trên stopped service trả success/no-op hoặc explicit already-stopped state.

---

# 599.214. Service restart

```axiom
service.restart()
```

là:

```text
stop → start
```

với policy-defined ordering.

---

# 599.215. Restart semantics

Restart không được giả định process state preserved.

---

# 599.216. Service state persistence

Nếu cần persistent state, service phải dùng `597`.

---

# 599.217. No implicit process memory persistence

Restart luôn mất process memory.

---

# 599.218. Service checkpoint

Service có thể checkpoint persistent state trước planned restart.

---

# 599.219. Checkpoint failure

Checkpoint failure phải block graceful restart nếu state preservation là required.

---

# 599.220. Stateless service

Service có thể khai báo:

```text
state = stateless
```

---

# 599.221. Stateful service

Stateful service phải specify storage dependency.

---

# 599.222. State recovery

Service startup có thể:

```text load state
validate schema
migrate
recover
ready
```

---

# 599.223. Recovery timeout

Recovery có deadline.

---

# 599.224. Corrupt state

Service không được coi corrupt persistent state là empty state.

---

# 599.225. Recovery modes

```text Fail
Restore
Rebuild
Quarantine
ReadOnly
```

---

# 599.226. Service maintenance mode

Service có thể enter:

```text Maintenance
```

để migration/repair.

---

# 599.227. Maintenance readiness

Maintenance service không report normal Ready.

---

# 599.228. Migration

Service schema migration sử dụng `597`.

---

# 599.229. Service data version

Service data schema version độc lập service executable version.

---

# 599.230. Downgrade protection

Service có thể reject older executable opening newer data schema.

---

# 599.231. Service backup

Critical service data có thể declare backup policy.

---

# 599.232. Cache

Service cache phải dùng `597.Cache`.

---

# 599.233. Temp

Service temporary state dùng `597.Temp`.

---

# 599.234. Service documents

User-facing services có thể sử dụng `597.Documents`.

---

# 599.235. User session

User service có thể bind lifecycle với login session.

---

# 599.236. Session logout

Policy:

```text Stop
Detach
Continue
```

---

# 599.237. System service

System service có thể continue across user logout nếu platform/security policy cho phép.

---

# 599.238. Privilege

System service không tự động có administrator/root privilege.

---

# 599.239. Privilege declaration

Required privilege phải explicit.

---

# 599.240. Privilege minimization

Service nên drop privileges sau initialization nếu platform hỗ trợ.

---

# 599.241. Privilege separation pattern

```text
System broker
      │
      │ restricted IPC
      ▼
Unprivileged worker
```

---

# 599.242. Service account

Platform adapter có thể chọn dedicated OS account.

---

# 599.243. User identity

Service chạy user context phải preserve user identity metadata.

---

# 599.244. Multi-user

System service có thể phục vụ nhiều users nhưng authorization phải per-user/per-capability.

---

# 599.245. Cross-user isolation

User A không mặc định truy cập service data của User B.

---

# 599.246. Session isolation

IPC endpoints có thể scoped theo session.

---

# 599.247. Desktop integration

Desktop UI `452` có thể connect background service `598`.

---

# 599.248. UI lifecycle

UI process crash không nhất thiết stop background service.

---

# 599.249. Service lifecycle independence

Background service có lifecycle riêng nếu manifest khai báo.

---

# 599.250. On-demand activation

UI client request → supervisor starts service → waits Ready → returns endpoint.

---

# 599.251. Activation sequence

```text
Client
  │ resolve service
  ▼
Service Manager
  │ not running
  ▼
Supervisor
  │ spawn
  ▼
Service
  │ ready
  ▼
Client connects
```

---

# 599.252. Activation timeout

Nếu service không Ready trước deadline:

```text ActivationTimeout
```

---

# 599.253. Activation retry

Retry obey restart policy.

---

# 599.254. Service discovery race

Client resolve trước service startup không được tạo stale endpoint.

---

# 599.255. Endpoint generation

New process instance luôn có new generation.

---

# 599.256. Service manager API

```axiom
service.install()
service.enable()
service.disable()
service.start()
service.stop()
service.restart()
service.status()
service.logs()
```

Các API installation cần deployment privilege.

---

# 599.257. Status

```axiom
ServiceStatus {
    state
    instance
    version
    health
    dependencies
    process
}
```

---

# 599.258. Service events

```text
Installed
Enabled
Started
Ready
Degraded
Failed
Restarted
Stopped
Disabled
Updated
```

---

# 599.259. Event ordering

Events từ cùng service instance phải có sequence number.

---

# 599.260. Event persistence

Service events không mặc định persistent.

---

# 599.261. Audit events

Security-sensitive operations có thể persistent audit record.

---

# 599.262. Service command channel

Service manager có thể dùng private control IPC.

---

# 599.263. Control endpoint

Control endpoint phải không public mặc định.

---

# 599.264. Control capabilities

Commands:

```text start
stop
restart
reload
status
```

cần management capability.

---

# 599.265. Reload

`reload` phải phân biệt:

```text configuration reload
process restart
```

---

# 599.266. Hot configuration

Service có thể reload config mà không restart process.

---

# 599.267. Configuration transaction

Config reload:

```text parse
validate
prepare
commit
```

---

# 599.268. Failed reload

Failed configuration không được replace current valid configuration.

---

# 599.269. Configuration generation

Service giữ configuration generation.

---

# 599.270. Dynamic policy

Security/capability policy không được hot-reload mà không revalidate active capabilities.

---

# 599.271. Service resource lifecycle

```text
Context
  ↓
Resources
  ↓
Workers
  ↓
IPC
```

---

# 599.272. Shutdown order

Thông thường:

```text stop accepting
→ stop workers
→ drain IPC
→ flush storage
→ close resources
```

---

# 599.273. Reverse dependency shutdown

Dependency graph có thể shutdown theo reverse topological order.

---

# 599.274. Parallel shutdown

Independent services có thể shutdown song song.

---

# 599.275. Shutdown cycle

Dependency cycle không hợp lệ trong required dependency graph.

---

# 599.276. Service manager crash

Nếu service manager/supervisor crash, service behavior phải theo platform supervision contract.

---

# 599.277. Orphan service

A service process không còn supervisor phải có state:

```text Orphaned
```

nếu platform phát hiện được.

---

# 599.278. Reattach

Supervisor có thể reattach service nếu protocol hỗ trợ.

---

# 599.279. No guaranteed reattach

Reattach không phải universal guarantee.

---

# 599.280. Process exit

Service process exit phải publish terminal state nếu supervisor còn sống.

---

# 599.281. Supervisor restart

Service manager có thể reconstruct service state từ deployment manifest + runtime state.

---

# 599.282. Persistent service state

Only state declared persistent can survive manager restart.

---

# 599.283. Service metadata store

Metadata có thể được lưu trong protected AppData/system store.

---

# 599.284. Metadata integrity

Service metadata phải có version/integrity marker.

---

# 599.285. Service registration corruption

Corrupt registration → safe failure, không arbitrary code execution.

---

# 599.286. Service installation scripts

Arbitrary install scripts không được default.

---

# 599.287. Declarative service installation

Preferred:

```text manifest
+
platform adapter
```

---

# 599.288. Native installer boundary

Platform-native installer có thể thực hiện privileged operations bên ngoài compiler/runtime.

---

# 599.289. Signing boundary

Code signing vẫn nằm ngoài compiler's semantic service model.

---

# 599.290. Service package

Service package artifact có thể chứa:

```text executable
manifest
IPC schema
resource references
permissions
service metadata
provenance
```

---

# 599.291. Package validation

Before activation:

```text artifact hash
signature
target
ABI
dependencies
capabilities
```

phải validate.

---

# 599.292. Target validation

Service package target phải match host target.

---

# 599.293. Architecture validation

x86_64/AArch64/etc phải match hoặc supported translation layer.

---

# 599.294. CPU feature validation

Service executable không được activate nếu yêu cầu CPU feature unavailable.

---

# 599.295. Runtime version

Service có thể yêu cầu minimum Axiom runtime version.

---

# 599.296. Runtime compatibility

Runtime ABI mismatch → activation reject.

---

# 599.297. Native dependencies

Dynamic libraries phải resolve trước Ready.

---

# 599.298. Missing dependency

Missing library → startup failure with dependency identity.

---

# 599.299. No arbitrary library search

Service loading tuân deterministic native dependency resolution `582–584`.

---

# 599.300. Resource dependencies

Service resources từ `596` phải resolve trước use.

---

# 599.301. Resource failure

Missing critical resource → service startup failure.

---

# 599.302. Noncritical resource

Optional resource failure → service may become Degraded.

---

# 599.303. Service startup diagnostics

Startup failure phải báo:

```text service
instance
stage
dependency
error
```

---

# 599.304. Startup stages

```text
ProcessSpawn
RuntimeInit
ConfigLoad
StorageInit
IPCInit
DependencyConnect
ApplicationInit
HealthCheck
Ready
```

---

# 599.305. Stage timing

Profiler có thể record duration từng stage.

---

# 599.306. Slow startup

IDE/profiler có thể identify slow stage.

---

# 599.307. Startup optimization

Compiler không được optimize away observable service lifecycle operations.

---

# 599.308. Lazy initialization

Noncritical subsystem nên lazy initialize.

---

# 599.309. Eager initialization

Security-critical or required dependencies initialize before Ready.

---

# 599.310. Service warmup

Service có thể warm caches before Ready.

---

# 599.311. Warmup deadline

Warmup phải chịu startup deadline.

---

# 599.312. Ready semantics

Ready nghĩa là service đáp ứng **documented minimum contract**, không nhất thiết mọi optional cache đã warm.

---

# 599.313. Service heartbeat

Long-running service có thể heartbeat supervisor.

---

# 599.314. Heartbeat timeout

Missed heartbeat không tự động chứng minh process dead nếu health probe khác vẫn valid.

---

# 599.315. Health probe hierarchy

```text Process alive
      ↓
Liveness
      ↓
Readiness
      ↓
Deep health
```

---

# 599.316. Deep health

Deep health có thể query dependencies nhưng không nên được gọi quá thường xuyên.

---

# 599.317. Health probe isolation

Health endpoint phải có resource/time budget.

---

# 599.318. Health recursion

Health check dependency cycle phải được detect.

---

# 599.319. Health storm prevention

Supervisor phải tránh polling quá mức.

---

# 599.320. Event-driven health

Service có thể push state changes thay vì polling.

---

# 599.321. Service dependency events

Dependency failure có thể trigger dependent service policy.

---

# 599.322. Grace period

Dependency temporary outage có thể có grace period.

---

# 599.323. Circuit breaker

Repeated dependency failures có thể open circuit.

---

# 599.324. Circuit states

```text Closed
Open
HalfOpen
```

---

# 599.325. Circuit breaker ownership

Circuit breaker thuộc client/service protocol layer, không phải universal supervisor behavior.

---

# 599.326. Service throttling

Service có thể throttle requests khi overloaded.

---

# 599.327. Admission control

Service có thể reject new requests trước khi queue exhaustion.

---

# 599.328. Load shedding

Overload policy có thể:

```text reject
defer
drop best-effort
```

---

# 599.329. Priority traffic

Critical requests có thể có priority.

---

# 599.330. Priority abuse

Untrusted clients không được tự nâng priority vượt capability.

---

# 599.331. Service resource accounting

Resource usage có thể attribute theo service identity.

---

# 599.332. CPU accounting

Supervisor/OS có thể attribute CPU usage.

---

# 599.333. Memory accounting

Memory usage có thể attribute process/service.

---

# 599.334. IPC accounting

`598` reports IPC bytes/latency.

---

# 599.335. Storage accounting

`597` reports service data usage.

---

# 599.336. Network accounting

`454` reports service network usage.

---

# 599.337. Unified service profile

```text
ServiceProfile {
    cpu
    memory
    storage
    ipc
    network
    startup
    restarts
}
```

---

# 599.338. Performance budget

Service có thể khai báo advisory budgets.

---

# 599.339. Hard budget

OS-enforced quotas được phân biệt khỏi advisory budgets.

---

# 599.340. Budget violation

Violation có thể:

```text log
throttle
degrade
terminate
```

theo policy.

---

# 599.341. Real-time service

Service có thể request real-time scheduling capability.

---

# 599.342. Real-time privilege

Request không guarantee OS grants privilege.

---

# 599.343. UI service

UI application không nên chạy as system service chỉ để giữ UI.

---

# 599.344. Headless service

Headless service không được assume display/session.

---

# 599.345. Display availability

GUI dependency phải explicit.

---

# 599.346. Mobile service

Mobile platforms có lifecycle restrictions.

Axiom adapter phải reflect actual OS behavior.

---

# 599.347. iOS limitation

Service abstraction trên iOS phải map vào permitted background execution/lifecycle model thay vì giả lập unrestricted daemon.

---

# 599.348. Android limitation

Android service model phải map vào actual application/service lifecycle và permissions.

---

# 599.349. WASM service

WASM service có thể là logical host-managed worker rather than OS daemon.

---

# 599.350. Desktop service

Desktop targets có thể support persistent background services nếu OS policy cho phép.

---

# 599.351. Freestanding

Freestanding target có thể inject custom ServiceManager.

---

# 599.352. Service provider

```axiom
trait ServiceProvider {
    fn install(...)
    fn start(...)
    fn stop(...)
    fn status(...)
}
```

---

# 599.353. Platform provider

Native platform adapter implements provider.

---

# 599.354. Virtual provider

Test environment có `VirtualServiceProvider`.

---

# 599.355. Service simulation

Simulation supports:

```text virtual clock
virtual process
virtual IPC
virtual failure
```

---

# 599.356. Deterministic restart tests

Crash/restart sequences phải reproducible.

---

# 599.357. Fault injection

Test có thể inject:

```text spawn failure
IPC failure
storage failure
dependency timeout
health failure
crash
resource exhaustion
```

---

# 599.358. Service fuzzing

Service manifest parser và dependency graph phải fuzz.

---

# 599.359. Dependency graph validation

Compiler/tooling validate:

```text duplicate IDs
cycles
missing dependencies
incompatible versions
invalid capabilities
```

---

# 599.360. Service schema

```axiom
struct ServiceDefinition {
    id: ServiceID
    version: Version
    executable: ArtifactID
    startup: StartupPolicy
    restart: RestartPolicy
    dependencies: [ServiceDependency]
    ipc: [InterfaceID]
    capabilities: CapabilitySet
    resources: ResourceLimits
    health: HealthPolicy
}
```

---

# 599.361. Service dependency schema

```axiom
struct ServiceDependency {
    service: ServiceID
    requirement: VersionRequirement
    kind: DependencyKind
    failure_policy: DependencyFailurePolicy
}
```

---

# 599.362. Restart schema

```axiom
struct RestartPolicy {
    mode: RestartMode
    max_restarts: u32
    window: Duration
    backoff: BackoffPolicy
}
```

---

# 599.363. Health policy

```axiom
struct HealthPolicy {
    startup_timeout: Duration
    readiness_timeout: Duration
    heartbeat_interval: Duration?
    failure_threshold: u32
}
```

---

# 599.364. Resource limits

```axiom
struct ServiceResourceLimits {
    cpu: Limit?
    memory: Limit?
    threads: Limit?
    handles: Limit?
    storage: Limit?
    ipc_bytes: Limit?
}
```

---

# 599.365. Service status

```axiom
struct ServiceStatus {
    service_id: ServiceID
    instance_id: InstanceID?
    generation: u64
    state: ServiceState
    health: HealthState
    version: Version
    process_id: ProcessID?
    started_at: Instant?
    ready_at: Instant?
    restart_count: u32
}
```

---

# 599.366. Service manager

```axiom
trait ServiceManager {
    fn install(definition) -> Result
    fn uninstall(id) -> Result
    fn enable(id) -> Result
    fn disable(id) -> Result
    fn start(id) -> Result
    fn stop(id) -> Result
    fn restart(id) -> Result
    fn status(id) -> Result<ServiceStatus>
}
```

---

# 599.367. Service startup API

```axiom
fn service_main(ctx: ServiceContext) -> Result<(), ServiceError>
```

---

# 599.368. Service bootstrap

```text
OS/service-manager
       ↓
Process
       ↓
Axiom runtime
       ↓
ServiceContext
       ↓
service_main()
       ↓
register IPC
       ↓
initialize dependencies
       ↓
health/readiness
       ↓
Ready
```

---

# 599.369. Service shutdown API

```axiom
trait ShutdownHandler {
    fn prepare_stop(ctx) -> Result
    fn drain(ctx) -> Result
    fn finalize(ctx) -> Result
}
```

---

# 599.370. No forced framework

Simple services có thể chỉ implement:

```axiom
fn main() {
    ...
}
```

và package manifest có thể biến process thành managed service.

---

# 599.371. Service wrapper

Compiler/runtime có thể wrap ordinary executable thành service process.

---

# 599.372. Legacy application

Existing native application có thể được hosted as service nếu đáp ứng lifecycle contract.

---

# 599.373. Service adaptation

Adapter có thể map:

```text signal
stdin/stdout
control pipe
```

thành service lifecycle.

---

# 599.374. Console service

Development mode cho phép service chạy foreground với logs trên console.

---

# 599.375. Development mode

```text
axiom service run myservice
```

chạy service dưới terminal mà không install system service.

---

# 599.376. Production mode

```text
axiom service install
axiom service start
```

sử dụng deployment/service manager.

---

# 599.377. Debug mode

```text
axiom service debug
```

cho phép debugger attach trước Ready.

---

# 599.378. Test mode

```text
axiom service test
```

dùng virtual provider.

---

# 599.379. Service CLI

CLI surface:

```text
axiom service list
axiom service info <id>
axiom service install <package>
axiom service uninstall <id>
axiom service enable <id>
axiom service disable <id>
axiom service start <id>
axiom service stop <id>
axiom service restart <id>
axiom service logs <id>
axiom service health <id>
axiom service debug <id>
```

---

# 599.380. CLI privilege

CLI command phải respect OS privilege requirements.

---

# 599.381. No privilege escalation

Axiom CLI không tự bypass OS authorization.

---

# 599.382. Service logs

`axiom service logs` đọc qua observability API, không assume fixed log file path.

---

# 599.383. Service diagnostics

Diagnostic output phải include:

```text service ID
version
state
health
dependency
process
```

---

# 599.384. Machine-readable status

CLI hỗ trợ structured output:

```text JSON
AXON binary
```

---

# 599.385. AI-readable service status

Structured output phải preserve exact states/errors.

---

# 599.386. Service graph command

```text
axiom service graph
```

hiển thị dependency graph.

---

# 599.387. Service provenance command

```text
axiom service provenance <id>
```

hiển thị build/package/signing chain.

---

# 599.388. Service capability command

```text
axiom service capabilities <id>
```

hiển thị declared vs granted capabilities.

---

# 599.389. Declared vs granted

Phải phân biệt:

```text
Declared
Requested
Granted
Effective
Denied
```

---

# 599.390. No capability assumption

Service code không được assume declared capability đã được granted.

---

# 599.391. Capability negotiation

Startup có thể fail hoặc degrade nếu required capability denied.

---

# 599.392. Optional capability

Optional capability absence → Degraded hoặc feature disabled.

---

# 599.393. Capability revocation

Runtime có thể notify service khi dynamic capability revoked.

---

# 599.394. Revocation response

Service phải stop using capability sau revocation.

---

# 599.395. Security audit

Capability grant/revoke có thể tạo audit record.

---

# 599.396. Service attack surface

Service manifest có thể compute attack surface:

```text IPC endpoints
network listeners
filesystem capabilities
device access
privileges
```

---

# 599.397. Static security analysis

`572` có thể phân tích service capability usage.

---

# 599.398. Effect analysis

`573` có thể annotate:

```text IO
Network
Storage
IPC
ProcessSpawn
Privilege
```

---

# 599.399. Service effect contract

Service definition có thể declare expected effects.

---

# 599.400. Effect mismatch

Nếu binary sử dụng effect không khai báo, tooling có thể cảnh báo/error theo security profile.

---

# 599.401. Service sandbox profile

```axiom
sandbox {
    filesystem = [...]
    network = [...]
    ipc = [...]
    devices = [...]
}
```

---

# 599.402. Device capability

Device access phải explicit.

---

# 599.403. Hardware service

Hardware-facing service có thể chạy privileged broker + unprivileged workers.

---

# 599.404. Driver boundary

Axiom service abstraction không biến service thành kernel driver.

---

# 599.405. Kernel boundary

Kernel drivers vẫn thuộc OS-specific/native platform boundary.

---

# 599.406. Service syscall boundary

Service sử dụng ordinary native runtime/syscalls qua `441`.

---

# 599.407. No microkernel assumption

Axiom service model không yêu cầu OS phải là microkernel.

---

# 599.408. No OS replacement

Axiom ServiceManager adapts to OS lifecycle rather than replacing OS service manager.

---

# 599.409. Portable service semantics

Portable semantics tập trung vào:

```text identity
lifecycle
health
dependencies
IPC
capabilities
restart
observability
```

---

# 599.410. Platform-specific service semantics

Native adapter chịu:

```text installation
startup registration
session integration
system service
OS policy
```

---

# 599.411. Windows mapping

Có thể map SystemService → Windows service infrastructure.

---

# 599.412. Linux mapping

Có thể map SystemService → native service manager.

---

# 599.413. macOS mapping

Có thể map background/system service → launch infrastructure theo platform policy.

---

# 599.414. Android mapping

Service model phải tuân Android lifecycle/permission/background restrictions.

---

# 599.415. iOS mapping

Persistent arbitrary daemon semantics không được giả định.

---

# 599.416. WASM mapping

Service có thể map thành host-managed worker/task.

---

# 599.417. Platform capability matrix

Toolchain phải expose:

```text supports_system_service
supports_user_service
supports_background_service
supports_on_boot
supports_on_login
supports_persistent_daemon
```

---

# 599.418. Capability-aware compilation

Compile/package tooling có thể reject manifest incompatible với target.

---

# 599.419. Cross compilation

Service manifest phải được validated against target, không host.

---

# 599.420. Target-specific service profile

Package có thể chứa:

```text
target_overrides
```

nhưng semantic core vẫn giữ invariant.

---

# 599.421. Service artifact

Service executable là ordinary native artifact từ `580–584`.

---

# 599.422. No service-specific machine code

Service abstraction không yêu cầu instruction set mới.

---

# 599.423. Linker integration

Service executable có entrypoint and dependency metadata như application executable.

---

# 599.424. Startup metadata

Service metadata có thể được embedded vào artifact/package.

---

# 599.425. Native image integration

`584` final image có thể chứa:

```text
service identity
runtime requirement
entrypoint metadata
```

nếu target format hỗ trợ custom metadata.

---

# 599.426. Runtime startup

`441` startup passes service context into runtime.

---

# 599.427. Process supervision

`594` remains authoritative for:

```text spawn
monitor
restart
terminate
resource limits
```

---

# 599.428. IPC supervision

`598` remains authoritative for communication.

---

# 599.429. Storage

`597` remains authoritative for writable persistent data.

---

# 599.430. Resource

`596` remains authoritative for packaged immutable resources.

---

# 599.431. Security

`490` remains authoritative for capability/sandbox enforcement.

---

# 599.432. Deployment

`593` remains authoritative for application/service package installation.

---

# 599.433. Observability

`475/476/481` remains authoritative for logs/tracing/profiling.

---

# 599.434. Debugging

`589` remains authoritative for native debugging.

---

# 599.435. IDE

`590` remains authoritative for service visualization and management UI.

---

# 599.436. Package manager

`591` resolves service dependencies/packages but does not itself supervise runtime services.

---

# 599.437. Build system

`487/568` builds service dependency graph but does not start services during ordinary compilation.

---

# 599.438. Build/run separation

Compilation must not silently install/start services.

---

# 599.439. Deployment/run separation

Installation and activation are explicit deployment operations.

---

# 599.440. AI build separation

AI agent cannot treat successful compilation as authorization to install/start a system service.

---

# 599.441. Service installation confirmation

Privileged installation can require explicit confirmation/policy.

---

# 599.442. Service startup confirmation

Starting privileged service can require authorization.

---

# 599.443. Service update confirmation

Security-sensitive update can require approval.

---

# 599.444. No silent persistence

Application cannot silently install an always-on background service without declared deployment semantics.

---

# 599.445. User transparency

Service installation should expose:

```text purpose
capabilities
startup policy
network access
storage
IPC
```

---

# 599.446. Service manifest explainability

Manifest metadata must be machine-readable.

---

# 599.447. AI explainability

AI tooling can generate explanation:

```text "This service starts on login and listens on local IPC."
```

based only on actual manifest/runtime metadata.

---

# 599.448. No speculative state

If runtime has not confirmed a service is installed/running, tooling must report `Unknown` rather than infer it.

---

# 599.449. Service security review

Static analyzer can flag:

```text
system privilege
network listener
broad filesystem access
public IPC
```

---

# 599.450. Security warning

Warnings must describe concrete capability exposure, not generic fear.

---

# 599.451. Service attack-path graph

Security tooling may produce:

```text
Internet
   ↓
Network Service
   ↓
IPC
   ↓
Privileged Broker
   ↓
Filesystem
```

---

# 599.452. Trust boundary graph

Each capability boundary must be represented.

---

# 599.453. Privilege escalation analysis

`572/549` can identify paths where untrusted input reaches privileged service.

---

# 599.454. Input validation

Privileged services must validate all IPC input.

---

# 599.455. Parser isolation

Untrusted service protocol decoding should run before privileged operations.

---

# 599.456. Sandboxed decoder

Optional decoder worker can isolate complex/untrusted formats.

---

# 599.457. Broker architecture

```text
Untrusted Input
      ↓
Restricted Decoder
      ↓
Validated Message
      ↓
Privileged Broker
      ↓
OS Resource
```

---

# 599.458. Service boundary

Service process boundary is useful security boundary but not automatically sufficient.

---

# 599.459. Defense in depth

Security should combine:

```text process isolation
capabilities
sandbox
input validation
resource limits
audit
```

---

# 599.460. Service resource exhaustion

Supervisor can terminate service violating hard resource limits.

---

# 599.461. Graceful resource pressure

Service may enter Degraded under soft resource pressure.

---

# 599.462. Memory pressure

Service can receive memory pressure notification.

---

# 599.463. Cache purge

Service may purge `597.Cache`.

---

# 599.464. Critical state protection

Service must never purge canonical state as response to cache pressure.

---

# 599.465. Service startup cache

Cache warmup is optional and must not block Ready unnecessarily.

---

# 599.466. Service startup persistence

Only explicitly persistent state is restored.

---

# 599.467. Service startup recovery

Recovery process:

```text Load
 ↓
Verify
 ↓
Migrate
 ↓
Recover
 ↓
Health
 ↓
Ready
```

---

# 599.468. Recovery journal

Critical services may use journaled state.

---

# 599.469. Recovery idempotence

Recovery operation should be restart-safe.

---

# 599.470. Service transaction

Service state changes can be represented as transaction:

```text Prepare
Validate
Commit
```

---

# 599.471. No distributed transaction requirement

Axiom local service model does not mandate distributed two-phase commit.

---

# 599.472. Cross-service transactions

If required, application can use `501/502` distributed primitives.

---

# 599.473. Service messaging

Cross-service state synchronization should prefer `598` message/event APIs.

---

# 599.474. Shared mutable state

Cross-service shared mutable memory should be exceptional and explicitly synchronized.

---

# 599.475. Default isolation

Default service architecture:

```text Process isolation
+
IPC
```

---

# 599.476. Performance escape hatch

For high-performance services:

```text SharedMemory
+
RingBuffer
+
Typed descriptors
```

from `598`.

---

# 599.477. Media service

Media server example:

```text
UI
 ↓ IPC
Media Service
 ├── decoder
 ├── DSP
 └── encoder
```

---

# 599.478. AI service

```text
Application
    ↓
AI Service
    ├── model runtime
    ├── GPU memory
    └── inference workers
```

---

# 599.479. Database service

Database service may expose:

```text RPC
stream
bulk transfer
```

while persistent state lives in `597`.

---

# 599.480. Plugin host

```text Host
  │
  │ restricted IPC
  ▼
Plugin Service
```

---

# 599.481. Compiler service

Compiler daemon `555` can be represented as managed service but remains optional.

---

# 599.482. Language server service

LSP server can be a user service or IDE-managed process.

---

# 599.483. Build worker service

Distributed build worker `567` can use service model.

---

# 599.484. Remote worker

Remote worker is still a service concept but remote lifecycle belongs `501/567`.

---

# 599.485. Service registration metadata

```axiom
struct ServiceRegistration {
    service_id
    instance_id
    endpoint
    version
    health
    capabilities
}
```

---

# 599.486. Registration lifetime

Registration must be removed when service instance terminates.

---

# 599.487. Lease-based registration

Registry can use lease to prevent stale registration.

---

# 599.488. Lease renewal

Service renews registration periodically.

---

# 599.489. Lease expiry

No renewal → registration becomes stale.

---

# 599.490. Stale registration

Client must not trust stale registration as active endpoint.

---

# 599.491. Instance generation

New registration gets new generation.

---

# 599.492. Endpoint collision

Registration must reject conflicting owner identity.

---

# 599.493. Service ownership

Only authorized manager/service owner can register instance.

---

# 599.494. Service discovery race

Resolve result is advisory until connection/identity validation succeeds.

---

# 599.495. Client retry

Client retry must respect service idempotency policy.

---

# 599.496. Service activation

Discovery can request activation if service is OnDemand.

---

# 599.497. Activation authorization

Client needs activation capability.

---

# 599.498. No arbitrary activation

Any process cannot start privileged service solely by knowing ServiceID.

---

# 599.499. Service control authorization

Management APIs require management capability.

---

# 599.500. Service manager boundary

Application code cannot directly mutate system service database through portable API.

---

# 599.501. Native service adapter

Platform adapter performs OS-specific registration.

---

# 599.502. Adapter isolation

Platform service implementation must not leak into core language semantics.

---

# 599.503. Service provider plugin

Custom OS/embedded platforms may provide `ServiceProvider`.

---

# 599.504. Embedded service manager

Embedded target may implement service supervision entirely inside firmware/runtime.

---

# 599.505. No OS assumption

Axiom service model must remain valid even when OS service manager does not exist.

---

# 599.506. Minimal service runtime

A service that only needs:

```text process
IPC
shutdown
```

must not require full service-management stack.

---

# 599.507. Dead stripping

Unused service registry/installer components must be removable.

---

# 599.508. Static service configuration

Embedded systems can compile service graph statically.

---

# 599.509. Static service graph

```text
const ServiceGraph = {
    A → B,
    B → C
}
```

can be compile-time generated.

---

# 599.510. Dynamic service graph

Desktop systems can load service definitions dynamically.

---

# 599.511. Hybrid graph

Static base services + dynamic optional services are allowed.

---

# 599.512. Deterministic service IDs

Service IDs must be canonical and stable.

---

# 599.513. ID collision

Package tooling must detect duplicate IDs.

---

# 599.514. Namespace

Service IDs should be namespace-qualified by application/package identity.

---

# 599.515. Global service names

System-wide names require explicit registration authority.

---

# 599.516. Naming attack

Service name alone cannot authorize connection.

---

# 599.517. Service endpoint security

Endpoint + peer identity + capability must all satisfy policy.

---

# 599.518. Service identity spoofing

Client must verify actual service identity after connection.

---

# 599.519. Signed identity

Platform signing identity can strengthen service identity verification.

---

# 599.520. Version verification

Client verifies interface/version after connection.

---

# 599.521. Protocol negotiation

Service/client may negotiate protocol features.

---

# 599.522. Feature negotiation

Unknown features must be ignored/rejected according to protocol contract.

---

# 599.523. Compatibility certificate

Compiler/package tooling may emit machine-readable compatibility proof.

---

# 599.524. Service compatibility artifact

```text
ServiceCompatibility {
    interface_id
    supported_versions
    ABI_fingerprint
    schema_fingerprint
}
```

---

# 599.525. Compatibility check

Activation can reject incompatible client/server contracts before accepting traffic.

---

# 599.526. Service migration

Migration may involve:

```text old
 ↓
new
 ↓
data migration
 ↓
health
 ↓
switch clients
 ↓
retire old
```

---

# 599.527. Client migration

Client may connect to old and new services simultaneously during transition.

---

# 599.528. State migration

State migration belongs service/storage layer, not IPC transport.

---

# 599.529. Service handoff

Service can transfer ownership of logical workload to another instance.

---

# 599.530. Handoff state

Handoff must define:

```text ownership
in-flight requests
persistent state
IPC endpoint
```

---

# 599.531. No implicit handoff

Process replacement does not automatically preserve in-memory state.

---

# 599.532. Blue/green deployment

Service manager may support old/new instances side by side.

---

# 599.533. Canary

Canary deployment is optional and mostly relevant to distributed services.

---

# 599.534. Local service deployment

Local application updates may use staged replacement.

---

# 599.535. Update health gate

New version must pass declared health gate before commit.

---

# 599.536. Rollback health gate

Rollback must validate old version before declaring recovery.

---

# 599.537. Failed rollback

If rollback also fails, state becomes:

```text RecoveryFailed
```

rather than pretending healthy.

---

# 599.538. Recovery metadata

Recovery metadata must survive manager restart.

---

# 599.539. Recovery attempts

Repeated failed recovery must be bounded.

---

# 599.540. Recovery lockout

After repeated failures, service can enter Disabled/ManualRecovery.

---

# 599.541. Manual recovery

User/operator can inspect and repair service.

---

# 599.542. No infinite restart

Infinite restart loops are prohibited.

---

# 599.543. Crash-loop state

```text
CrashLooping
```

is explicit state.

---

# 599.544. Crash-loop notification

Observability system can emit alert.

---

# 599.545. Service dependency crash-loop

Dependent service may remain stopped instead of joining crash loop.

---

# 599.546. Service shutdown dependency

Shutdown order follows reverse required dependency graph.

---

# 599.547. Dependency health propagation

Health propagation policy must be explicit.

---

# 599.548. No automatic semantic inference

Supervisor must not infer business-level health from process liveness alone.

---

# 599.549. Business health

Application defines deep health semantics.

---

# 599.550. Final service architecture

```text
                         AXIOM SERVICE MODEL
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
   Definition                Lifecycle                 Identity
        │                        │                        │
        ▼                        ▼                        ▼
 Deployment                 Supervisor                Security
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 ▼
                              Process
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
             IPC              Storage            Tasks
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                           Health / Ready
                                 │
                                 ▼
                            Observability
```

---

# 599.551. Service hard invariant — identity

Service identity phải độc lập process ID và executable filename.

---

# 599.552. Service hard invariant — lifecycle

Service lifecycle phải deterministic theo definition + dependency graph + runtime events.

---

# 599.553. Service hard invariant — supervision

Service process phải có supervision policy nếu manifest yêu cầu managed service.

---

# 599.554. Service hard invariant — crash isolation

Process isolation phải ngăn service crash lan sang process độc lập.

---

# 599.555. Service hard invariant — restart bound

Restart policy phải có giới hạn để ngăn crash loops vô hạn.

---

# 599.556. Service hard invariant — dependency correctness

Required dependency chưa Ready không được làm dependent service giả vờ Ready.

---

# 599.557. Service hard invariant — IPC

Service communication sử dụng `598`; service model không tạo một IPC mechanism thứ hai.

---

# 599.558. Service hard invariant — storage

Service persistent data sử dụng `597`; process memory không được coi là persistent state.

---

# 599.559. Service hard invariant — resources

Packaged immutable resources sử dụng `596`; service không được mutate resource bundle như user storage.

---

# 599.560. Service hard invariant — security

Service chỉ có capabilities được khai báo và thực tế được grant.

---

# 599.561. Service hard invariant — privilege

Service abstraction không tự cấp administrator/root/system privilege.

---

# 599.562. Service hard invariant — platform

Portable Service API không được giả định OS có daemon/service manager.

---

# 599.563. Service hard invariant — mobile

iOS/Android/WASM không được giả lập unrestricted persistent daemon semantics nếu platform không cho phép.

---

# 599.564. Service hard invariant — deployment

Compilation không được tự động install hoặc start service.

---

# 599.565. Service hard invariant — installation

Privileged installation phải đi qua deployment/platform authorization boundary.

---

# 599.566. Service hard invariant — update

Service update phải có staged activation và health validation khi update policy yêu cầu.

---

# 599.567. Service hard invariant — rollback

Failed activation phải có rollback/recovery state rõ ràng.

---

# 599.568. Service hard invariant — health

Liveness không được bị đánh đồng với readiness hoặc business health.

---

# 599.569. Service hard invariant — observability

Service state phải có thể truy vấn chính xác.

---

# 599.570. Service hard invariant — no hallucination

IDE/AI tooling không được suy ra `Running`, `Ready`, `Installed` hoặc `Healthy` nếu runtime chưa xác nhận.

---

# 599.571. Service hard invariant — AI safety

AI agent không được tự ý cài đặt, bật persistence, cấp capability hoặc start privileged service.

---

# 599.572. Service hard invariant — deterministic

Service definition, dependency graph, generated metadata và deployment artifacts phải deterministic.

---

# 599.573. Service hard invariant — minimal runtime

Một executable thông thường không sử dụng service framework không phải mang service manager/runtime vào binary.

---

# 599.574. Service hard invariant — no hidden daemon

Axiom không được yêu cầu một daemon trung tâm để mọi application service hoạt động.

---

# 599.575. Service hard invariant — native

Service process vẫn là native executable bình thường của Axiom.

---

# 599.576. Service hard invariant — no third-party compiler

Service model không phụ thuộc LLVM/GCC/Clang/MSVC hoặc compiler bên ngoài.

---

# 599.577. Service hard invariant — ownership

Service resources phải tuân ownership/lifetime model `423`.

---

# 599.578. Service hard invariant — concurrency

Service tasks/threads/async phải tuân `424/471`.

---

# 599.579. Service hard invariant — failure

Service failure phải được phân biệt khỏi transport, dependency, configuration và storage failures.

---

# 599.580. Service hard invariant — recovery

Recovery phải là stateful, bounded và observable.

---

# 599.581. Service hard invariant — user data

Service lifecycle không được tự ý xóa user data.

---

# 599.582. Service hard invariant — secrets

Service manifest/package không được chứa plaintext credentials như cơ chế secret management mặc định.

---

# 599.583. Service hard invariant — least privilege

Default service deployment phải ưu tiên capability tối thiểu.

---

# 599.584. Service hard invariant — isolation

Services khác trust boundary không được chạy chung process chỉ để tối ưu startup/memory.

---

# 599.585. Service hard invariant — protocol

Service public API phải có version/schema identity.

---

# 599.586. Service hard invariant — ABI

Native zero-copy service interface phải kiểm tra ABI compatibility.

---

# 599.587. Service hard invariant — update

Breaking interface update phải hỗ trợ versioning/coexistence/migration thay vì silent reinterpretation.

---

# 599.588. Service hard invariant — no implicit persistence

Service restart không được giả định process memory tồn tại.

---

# 599.589. Service hard invariant — startup

Service chỉ report Ready sau khi minimum documented contract đã được thỏa mãn.

---

# 599.590. Service hard invariant — shutdown

Graceful shutdown phải có deadline và forced-stop fallback.

---

# 599.591. Service hard invariant — dependency cycle

Required service dependency cycle phải bị reject.

---

# 599.592. Service hard invariant — cross-platform honesty

Platform không hỗ trợ service mode nào phải report `Unsupported`, không tạo semantics giả.

---

# 599.593. Service hard invariant — package boundary

Service package phải có đầy đủ executable/dependency/manifest/provenance information cần để activation.

---

# 599.594. Service hard invariant — trust

Không một service executable nào được coi trusted chỉ vì nó tự khai báo trusted.

---

# 599.595. Service hard invariant — provenance

Installed service phải có thể truy nguyên về package/artifact/build identity khi provenance được bật.

---

# 599.596. Service hard invariant — audit

Privileged service lifecycle operations phải có khả năng audit.

---

# 599.597. Service hard invariant — resource limits

Service có thể bị giới hạn CPU/memory/IPC/storage/network theo platform capability.

---

# 599.598. Service hard invariant — graceful degradation

Optional dependency/capability failure có thể đưa service vào Degraded thay vì bắt buộc crash.

---

# 599.599. FINAL HARD INVARIANT

> **Axiom Service không phải một “daemon framework” riêng biệt. Nó là một semantic contract ghép `Application Package + Process + Supervisor + IPC + Storage + Capability + Health + Deployment` thành một đơn vị runtime có identity và lifecycle rõ ràng.**

Kiến trúc cuối cùng:

```text
                           AXIOM APPLICATION
                                  │
                         ┌────────┴────────┐
                         │                 │
                      UI/App            Services
                                           │
                    ┌──────────────────────┼─────────────────────┐
                    │                      │                     │
                 Service A             Service B             Service C
                    │                      │                     │
                 Process                Process               Process
                    │                      │                     │
              ┌─────┼─────┐          ┌────┼────┐          ┌─────┼─────┐
              │     │     │          │    │    │          │     │     │
             IPC  Data  Tasks        IPC Data Tasks       IPC  Data Tasks
              │     │     │          │    │    │          │     │     │
              └─────┴─────┘          └────┴────┘          └─────┴─────┘
                    │                      │                     │
                    └──────────────────────┼─────────────────────┘
                                           │
                                      Supervisor
                                           │
                               ┌───────────┼───────────┐
                               ▼           ▼           ▼
                             Health     Restart     Resource
                               │           │           │
                               └───────────┼───────────┘
                                           ▼
                                     Platform OS
```

**599 — LOCKED**

---

# NEXT — BOOTSTRAP-600

## NATIVE APPLICATION NOTIFICATION, EVENT DELIVERY & SYSTEM INTEGRATION 6.0

`600` sẽ xây lớp integration nằm trên `598/599`, chuẩn hóa **application notifications, system events, user notifications, background events, power/session/network/device events, event subscriptions, durable vs ephemeral events, event filtering, delivery guarantees, permission/capability, OS notification adapters và cross-platform event semantics**.

```text
                    AXIOM EVENT SYSTEM
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   Application         System Event       User Event
      Events              Source          Notification
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                     Event Router
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          In-Process       IPC        External OS
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Subscription
                           │
                 ┌─────────┼─────────┐
                 ▼         ▼         ▼
               Task      Service    UI
```

`600` đặc biệt phải giữ ranh giới: **event delivery không phải message queue, notification không phải RPC, và system event không được biến thành một API OS-specific trong core Axiom.**