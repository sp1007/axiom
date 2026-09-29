# BOOTSTRAP-594 — NATIVE APPLICATION RUNTIME & PROCESS SUPERVISION 5.0
## PROCESS TREE, APPLICATION INSTANCE, STARTUP/SHUTDOWN, CHILD PROCESS, CRASH RECOVERY, SERVICE LIFECYCLE, IPC SUPERVISION, RESOURCE LIMITS, SIGNALS, HEALTH STATE, GRACEFUL TERMINATION & CROSS-PLATFORM PROCESS MODEL

**Trạng thái: COMPLETED / LOCKED**

`594` định nghĩa **process/application runtime model** của Axiom ở tầng application/runtime, nối `441` OS process model với `593` deployment package, `424` concurrency, `471` task/job, `472` actor/message passing, `454` IPC và `589` debugger/crash model.

Mục tiêu:

> Một chương trình Axiom phải có process model rõ ràng, deterministic ở mức semantic, tận dụng native OS primitives khi có thể, nhưng không ép application code phải hiểu sự khác biệt giữa Windows/Linux/macOS/iOS/Android/WASM.

---

# 594.1. Layering

```text
Axiom Application
       │
       ▼
Application Runtime
       │
       ├── Lifecycle
       ├── Process Supervisor
       ├── Child Processes
       ├── Health
       ├── Recovery
       ├── Resource Limits
       └── IPC
              │
              ▼
       Platform Process Adapter
              │
       ┌──────┼────────┐
       ▼      ▼        ▼
    Windows  Unix     Mobile/WASM
```

---

# 594.2. Process abstraction

Axiom định nghĩa logical:

```text
Process
```

không expose trực tiếp toàn bộ OS-specific process API.

---

# 594.3. Native process

Một `Process` map tới native OS process nếu target hỗ trợ.

---

# 594.4. WASM process

WASM host có thể map logical process thành:

- worker;
- host task;
- sandbox instance;

tùy host.

---

# 594.5. Application instance

```text
ApplicationInstance {
    application_id
    version
    instance_id
    process_tree
    lifecycle_state
}
```

---

# 594.6. Instance identity

Mỗi running application instance có unique runtime identity.

---

# 594.7. Process identity

```text
ProcessID
```

không được dùng làm persistent application identity.

---

# 594.8. PID boundary

Native PID là platform detail.

---

# 594.9. Logical process ID

Axiom runtime cấp logical ID ổn định trong lifecycle của application supervisor.

---

# 594.10. Process tree

```text
Application
    │
    ├── Main
    │
    ├── Worker
    │     ├── Worker-A
    │     └── Worker-B
    │
    └── Helper
```

---

# 594.11. Parent-child relationship

Logical process tree biểu diễn ownership/supervision relationship, không nhất thiết giống OS PPID.

---

# 594.12. Process roles

Process có thể có role:

```text
main
worker
helper
service
plugin
sandbox
```

---

# 594.13. Main process

Main process đại diện application instance.

---

# 594.14. Worker process

Worker thực hiện workload tách biệt khỏi main process.

---

# 594.15. Helper process

Helper cung cấp service phụ trợ.

---

# 594.16. Service process

Service có lifecycle dài hơn một application UI session.

---

# 594.17. Plugin process

Plugin process được supervised bởi host.

---

# 594.18. Sandbox process

Sandbox process có capability subset.

---

# 594.19. Process descriptor

```text
ProcessSpec {
    name
    role
    executable
    arguments
    environment
    capabilities
    resource_limits
    restart_policy
}
```

---

# 594.20. Executable identity

`ProcessSpec.executable` phải reference artifact identity hoặc package-local executable.

---

# 594.21. Arbitrary executable prohibition

Process supervisor không được tự động chạy executable ngoài deployment policy.

---

# 594.22. Startup sequence

```text
Create
 ↓
Validate
 ↓
Spawn
 ↓
Initialize
 ↓
Ready
 ↓
Running
```

---

# 594.23. Lifecycle states

```text
Created
Starting
Ready
Running
Stopping
Stopped
Failed
Restarting
```

---

# 594.24. Terminal states

```text
Stopped
Failed
```

có thể là terminal cho một process instance.

---

# 594.25. Startup failure

Startup failure phải produce structured error.

---

# 594.26. Ready state

`Ready` nghĩa process đã hoàn tất initialization cần thiết và có thể nhận workload.

---

# 594.27. Running state

`Running` nghĩa process đang actively executing.

---

# 594.28. Health state

Health state độc lập lifecycle state.

```text
Unknown
Starting
Healthy
Degraded
Unhealthy
```

---

# 594.29. Health ≠ process state

Process có thể:

```text Running + Unhealthy
```

hoặc:

```text Ready + Degraded
```

---

# 594.30. Health provider

Application có thể register health provider.

```text
HealthCheck {
    name
    check()
}
```

---

# 594.31. Health timeout

Health check phải có timeout.

---

# 594.32. Health isolation

Health check không được block supervisor indefinitely.

---

# 594.33. Startup timeout

Supervisor có startup deadline.

---

# 594.34. Shutdown timeout

Supervisor có graceful shutdown deadline.

---

# 594.35. Forced termination

Nếu graceful shutdown vượt deadline:

```text graceful stop
       ↓ timeout
forced termination
```

Platform adapter quyết định primitive cuối cùng.

---

# 594.36. Graceful shutdown

Application nhận lifecycle event:

```text shutdown_requested
```

---

# 594.37. Shutdown ordering

Process tree shutdown mặc định:

```text children
 ↓
workers/helpers
 ↓
main
```

---

# 594.38. Reverse dependency shutdown

Nếu dependency graph yêu cầu thứ tự khác, dependency ordering được ưu tiên.

---

# 594.39. Shutdown idempotency

Shutdown request có thể được gửi nhiều lần mà không tạo undefined behavior.

---

# 594.40. Cancellation

Lifecycle cancellation tích hợp với cancellation model của `424/471`.

---

# 594.41. Cancellation token

```text
CancellationToken
```

có thể propagate xuống process/task tree.

---

# 594.42. Process cancellation

Cancellation không đồng nghĩa kill.

---

# 594.43. Cooperative cancellation

Application trước tiên được yêu cầu terminate cooperatively.

---

# 594.44. Forced termination boundary

Forced termination không đảm bảo destructors/drop/defer hoàn tất.

---

# 594.45. Resource cleanup

Graceful termination phải chạy cleanup semantics bình thường.

---

# 594.46. Crash

Crash là abnormal process termination.

---

# 594.47. Crash classification

```text
ExitCode
Signal
Panic
FatalRuntimeError
OSException
Killed
Unknown
```

---

# 594.48. Panic integration

Panic model `425` truyền structured panic information vào supervisor.

---

# 594.49. Crash record

```text
CrashRecord {
    process_id
    timestamp
    reason
    exit_status
    stack_reference
    artifact_identity
}
```

---

# 594.50. No fake crash state

Nếu debugger/crash handler không biết nguyên nhân:

```text reason = Unknown
```

không được suy đoán.

---

# 594.51. Crash dump

Crash dump generation dùng infrastructure `589`.

---

# 594.52. Crash provenance

Crash record reference:

```text source revision
binary hash
package hash
deployment instance
```

---

# 594.53. Crash restart policy

```text Never
OnFailure
Always
OnCrash
```

---

# 594.54. Restart backoff

Restart policy có:

```text initial_delay
maximum_delay
backoff
jitter_policy
```

---

# 594.55. Jitter

Jitter chỉ dùng khi deployment/distributed environment cần tránh restart synchronization.

---

# 594.56. Restart budget

Supervisor có thể giới hạn số restart trong một khoảng thời gian.

---

# 594.57. Crash loop

Nếu restart liên tục vượt policy:

```text CrashLoop
```

process chuyển sang failed state.

---

# 594.58. Crash-loop protection

Supervisor không được restart vô hạn không kiểm soát.

---

# 594.59. Manual restart

Operator có thể reset crash-loop state.

---

# 594.60. Restart identity

Mỗi restart tạo process instance mới nhưng có thể giữ logical service identity.

---

# 594.61. Process incarnation

```text ProcessIdentity
+
Incarnation
```

giúp phân biệt process cũ và process mới.

---

# 594.62. IPC endpoint identity

IPC endpoint không được phụ thuộc trực tiếp vào OS PID.

---

# 594.63. IPC supervision

Supervisor theo dõi IPC health giữa processes.

---

# 594.64. IPC disconnect

IPC disconnect tạo structured event:

```text PeerDisconnected
```

---

# 594.65. IPC reconnect

Service clients có thể reconnect theo policy.

---

# 594.66. Message semantics

IPC messaging tích hợp với `472`.

---

# 594.67. Request-response

Runtime cung cấp primitive:

```text request()
response()
```

---

# 594.68. One-way message

```text send()
```

không yêu cầu response.

---

# 594.69. IPC timeout

Request phải hỗ trợ deadline/timeout.

---

# 594.70. IPC cancellation

Cancelled request không được để runtime giữ resources vô hạn.

---

# 594.71. IPC backpressure

Channel/IPC endpoint phải hỗ trợ bounded capacity.

---

# 594.72. Queue overflow

Policy:

```text reject
block
drop
disconnect
```

phải explicit.

---

# 594.73. Shared-memory IPC

Có thể hỗ trợ shared memory nhưng phải khai báo capability/resource.

---

# 594.74. Shared-memory ownership

Shared memory lifetime phải thuộc một managed resource object.

---

# 594.75. Process handle

```text ProcessHandle
```

là managed logical resource.

---

# 594.76. Handle ownership

ProcessHandle có explicit ownership/drop semantics theo `423`.

---

# 594.77. Wait

```text process.wait()
```

chờ process termination.

---

# 594.78. Wait result

```text ProcessExit {
    status
    reason
    duration
}
```

---

# 594.79. Exit status

Exit status gồm:

```text success
code
signal
abnormal
```

---

# 594.80. Exit code

Axiom standardize logical exit code nhưng preserve native status.

---

# 594.81. Environment

Process có environment snapshot.

---

# 594.82. Environment inheritance

Child process không tự động inherit sensitive capability state.

---

# 594.83. Environment filtering

ProcessSpec có thể khai báo:

```text inherit
allowlist
denylist
explicit
```

---

# 594.84. Secret environment variables

Runtime không tự expose secret environment values trong logs/debug metadata.

---

# 594.85. Working directory

ProcessSpec có logical working directory.

---

# 594.86. Path isolation

Working directory không được phép escape sandbox policy.

---

# 594.87. Arguments

Arguments là structured UTF-8 strings ở Axiom layer.

---

# 594.88. Native argument conversion

Platform adapter thực hiện conversion sang native representation.

---

# 594.89. Standard streams

Process có:

```text stdin
stdout
stderr
```

nếu target hỗ trợ.

---

# 594.90. Stream inheritance

Inheritance phải explicit.

---

# 594.91. Pipe

Supervisor/runtime cung cấp native pipe abstraction.

---

# 594.92. Process logging

stdout/stderr có thể route vào logging subsystem `475`.

---

# 594.93. Log isolation

Một process không được tự động ghi vào log namespace của process khác.

---

# 594.94. Resource limits

ProcessSpec có:

```text cpu
memory
threads
handles
file_descriptors
io
```

---

# 594.95. CPU limit

CPU limits là best-effort nếu OS không hỗ trợ hard limit.

---

# 594.96. Memory limit

Memory limit semantics phải distinguish:

```text hard
soft
advisory
```

---

# 594.97. Resource-limit capability

Process chỉ được set resource limits khi host/platform cho phép.

---

# 594.98. Thread limit

Supervisor có thể giới hạn process-created threads/tasks.

---

# 594.99. File descriptor limit

Unix-like target có thể map logical descriptor limit sang OS limit.

---

# 594.100. I/O limit

I/O quota là optional platform facility.

---

# 594.101. Resource violation

Violation tạo structured event:

```text ResourceLimitExceeded
```

---

# 594.102. OOM

Out-of-memory termination phải distinguish được nếu platform cung cấp signal/status.

---

# 594.103. Supervisor memory safety

Supervisor không được allocate unbounded metadata khi child process crash liên tục.

---

# 594.104. Supervisor persistence

Persistent service supervisor có thể lưu lifecycle state.

---

# 594.105. Application supervisor

Application-local supervisor thường sống cùng main process.

---

# 594.106. External supervisor

OS/service manager có thể supervise entire application.

---

# 594.107. Dual supervision

```text OS Supervisor
       │
       ▼
Axiom Supervisor
       │
       ▼
Application Processes
```

Hai tầng không được tranh quyền lifecycle một cách không xác định.

---

# 594.108. Supervisor authority

Outer supervisor có final authority over process termination.

---

# 594.109. Application authority

Application supervisor quản lý logical children.

---

# 594.110. Service integration

Axiom service package từ `593` map tới OS service manager khi target hỗ trợ.

---

# 594.111. Service restart

Service restart policy có thể được delegated cho OS.

---

# 594.112. Duplicate supervision

Không restart cùng process từ cả Axiom và OS supervisor nếu policy không phối hợp.

---

# 594.113. Supervisor contract

```text Supervisor {
    spawn()
    stop()
    restart()
    status()
    health()
    wait()
}
```

---

# 594.114. Spawn result

```text SpawnResult {
    process
    endpoint
    incarnation
}
```

---

# 594.115. Spawn validation

Trước spawn:

```text executable
target
ABI
capabilities
resource limits
```

phải validate.

---

# 594.116. Spawn failure

Không tạo phantom process handle khi native spawn thất bại.

---

# 594.117. Process startup protocol

Child process có thể gửi:

```text STARTING
READY
FAILED
```

---

# 594.118. Readiness handshake

Parent không được coi child ready chỉ vì OS process tồn tại.

---

# 594.119. Startup handshake timeout

Nếu READY không xuất hiện trước deadline:

```text startup failure
```

---

# 594.120. Child initialization failure

Child phải trả structured startup reason khi có thể.

---

# 594.121. Process supervision tree

```text
Supervisor
│
├── Main
│
├── Worker-A
│
├── Worker-B
│
└── Helper
```

---

# 594.122. Supervisor restart scope

Restart một child không mặc định restart toàn application.

---

# 594.123. Escalation

Nếu critical process fail:

```text child failure
 ↓
supervisor policy
 ↓
restart child OR
restart subtree OR
shutdown application
```

---

# 594.124. Criticality

ProcessSpec:

```text critical = true/false
```

---

# 594.125. Critical process

Failure của critical process có thể escalate theo policy.

---

# 594.126. Non-critical process

Failure của non-critical process không tự động terminate application.

---

# 594.127. Dependency graph

Process dependencies có thể khai báo:

```text Worker depends_on Database
```

---

# 594.128. Startup dependency order

Dependency phải ready trước dependent process.

---

# 594.129. Shutdown dependency order

Dependent shutdown trước dependency.

---

# 594.130. Dependency cycle

Process dependency cycle là configuration error trừ khi explicit cycle policy tồn tại.

---

# 594.131. Restart dependency

Restart dependency có thể require dependent restart.

---

# 594.132. Restart propagation

Propagation policy:

```text none
dependent
subtree
application
```

---

# 594.133. Health propagation

Child unhealthy có thể làm parent degraded theo policy.

---

# 594.134. Health aggregation

Application health:

```text Healthy
Degraded
Unhealthy
```

được tính từ process health + application health checks.

---

# 594.135. Health hysteresis

Health transitions có thể yêu cầu consecutive failures/successes để tránh flapping.

---

# 594.136. Health flapping

Repeated Healthy/Unhealthy transitions có thể trigger diagnostics.

---

# 594.137. Process events

Event stream:

```text ProcessCreated
ProcessStarting
ProcessReady
ProcessHealthy
ProcessUnhealthy
ProcessStopping
ProcessExited
ProcessCrashed
ProcessRestarting
```

---

# 594.138. Event ordering

Events từ cùng process incarnation phải có monotonic sequence number.

---

# 594.139. Event sequence

```text ProcessEvent {
    process_id
    incarnation
    sequence
    timestamp
    event
}
```

---

# 594.140. Timestamp semantics

Timestamp dùng monotonic clock cho duration/order và wall clock cho human-readable time.

---

# 594.141. Clock integration

Dùng temporal semantics của `474`.

---

# 594.142. Event persistence

Persistent supervisor có thể persist lifecycle events.

---

# 594.143. Event durability

Không yêu cầu mọi event phải durable; policy phải explicit.

---

# 594.144. Process metrics

Supervisor có thể expose:

```text CPU
memory
startup_time
restart_count
uptime
IPC latency
```

---

# 594.145. Metrics integration

Metrics dùng infrastructure `475/476`.

---

# 594.146. Profiling integration

Process identity phải map tới profiler identity.

---

# 594.147. Debugger integration

Debugger `589` phải có thể attach theo logical process identity.

---

# 594.148. Attach after restart

Debugger phải detect incarnation change.

---

# 594.149. Breakpoint persistence

Breakpoint source/function có thể survive process restart; address breakpoint không mặc định survive.

---

# 594.150. Crash debugger integration

Crash record reference exact binary identity.

---

# 594.151. Async task integration

Process chứa:

```text threads
tasks
actors
```

nhưng chúng là runtime substructures.

---

# 594.152. Process vs thread

Process có address space/resource boundary.

Thread chia sẻ process address space.

---

# 594.153. Process vs task

Task là scheduling unit của runtime; không nhất thiết OS thread.

---

# 594.154. Process vs actor

Actor là isolated concurrency abstraction; có thể nằm cùng process hoặc process riêng.

---

# 594.155. No accidental process creation

Spawning process là explicit operation/capability.

---

# 594.156. Capability

```text process.spawn
```

là privileged runtime capability trong sandboxed environments.

---

# 594.157. Child capability set

Child capability set mặc định là subset parent capability set.

---

# 594.158. Capability attenuation

Parent có thể cấp ít capability hơn cho child.

---

# 594.159. Capability amplification

Child không được tự nâng capability.

---

# 594.160. Process sandbox

Sandbox process có explicit:

```text filesystem
network
IPC
device
resource
```

capabilities.

---

# 594.161. Sandboxed process failure

Sandbox violation phải tạo structured runtime error/event.

---

# 594.162. Signal abstraction

Axiom expose logical signals:

```text Interrupt
Terminate
Hangup
User
```

chỉ khi target hỗ trợ.

---

# 594.163. Native signals

Unix signals/Windows control events nằm platform adapter.

---

# 594.164. Signal safety

Signal handlers không được phép tùy tiện gọi toàn bộ runtime API.

---

# 594.165. Signal delivery

Runtime chuyển signal thành event/task-safe notification khi có thể.

---

# 594.166. Termination request

`terminate()` là cooperative request trước khi force kill.

---

# 594.167. Kill

`kill()` là force termination primitive và được đánh dấu dangerous/system-level API.

---

# 594.168. Process group

Supervisor có thể quản lý process group/tree để terminate subtree.

---

# 594.169. Orphan handling

Child process không được trở thành unmanaged orphan nếu supervisor policy yêu cầu ownership.

---

# 594.170. Adoption

External OS supervisor có thể adopt/reparent process theo platform semantics.

---

# 594.171. Zombie prevention

Unix process adapter phải ensure child status được reaped.

---

# 594.172. Handle closure

Process handles phải được close/drop deterministic.

---

# 594.173. Resource cleanup

Supervisor shutdown phải release:

```text process handles
pipes
IPC endpoints
timers
monitoring resources
```

---

# 594.174. Defer interaction

Axiom `defer`/drop semantics chạy trong graceful shutdown.

---

# 594.175. Abnormal termination

Crash/kill không guarantee cleanup.

---

# 594.176. Recovery journal

Durable supervisor có thể dùng journal:

```text desired state
observed state
transition
```

---

# 594.177. Desired state

Supervisor model:

```text DesiredState
ObservedState
```

---

# 594.178. Reconciliation

Supervisor continuously reconcile:

```text desired
   vs
observed
```

---

# 594.179. Service reconciliation

Nếu process chết ngoài ý muốn và policy `Always`:

```text observed = stopped
desired = running
→ restart
```

---

# 594.180. Reconciliation idempotency

Repeated reconciliation không được spawn duplicate processes.

---

# 594.181. Duplicate prevention

Process identity/lock mechanism phải ngăn duplicate activation.

---

# 594.182. Single-instance application

Manifest có thể khai báo:

```text single_instance = true
```

---

# 594.183. Single-instance coordination

Nếu platform hỗ trợ, second instance gửi activation request tới first instance.

---

# 594.184. Activation request

```text ApplicationActivate {
    arguments
    files
    deep_link
}
```

---

# 594.185. Activation failure

Nếu first instance unavailable, policy xác định whether second instance starts.

---

# 594.186. Multi-instance

Default application policy có thể cho phép multiple instances.

---

# 594.187. Instance discovery

Application có thể discover sibling instances only through explicit API/capability.

---

# 594.188. Session identity

GUI applications có:

```text user session
application instance
window/session state
```

từ `468`.

---

# 594.189. Background lifecycle

Application có thể chuyển:

```text foreground
background
suspended
resumed
```

trên mobile/GUI targets.

---

# 594.190. Mobile process termination

Mobile OS có thể terminate process bất kỳ lúc nào khi background.

Runtime phải không giả định persistent background process.

---

# 594.191. Mobile suspension

Suspension không phải crash.

---

# 594.192. Suspension event

Nếu platform cung cấp lifecycle event, runtime expose structured event.

---

# 594.193. Resume

Resume tạo lifecycle transition mà không tạo process incarnation mới nếu process vẫn tồn tại.

---

# 594.194. WASM lifecycle

WASM host lifecycle được adapter mapping.

---

# 594.195. Browser worker

Worker có thể được represented như logical process role `worker`.

---

# 594.196. No universal OS semantics

Axiom không giả định mọi target có:

- fork;
- signals;
- background service;
- arbitrary child processes.

---

# 594.197. Capability discovery

Runtime:

```text platform.supports(feature)
```

cho process facilities.

---

# 594.198. Unsupported operation

Unsupported process feature trả structured error.

---

# 594.199. No silent emulation

Runtime không được giả vờ hỗ trợ process semantics nếu host không thể cung cấp tương đương.

---

# 594.200. Process API

Core API:

```text
process.current()
process.spawn()
process.wait()
process.status()
process.terminate()
process.kill()
process.children()
```

---

# 594.201. Supervisor API

```text
supervisor.create()
supervisor.start()
supervisor.stop()
supervisor.restart()
supervisor.status()
supervisor.health()
```

---

# 594.202. Lifecycle API

```text
application.on_start()
application.on_ready()
application.on_shutdown()
application.on_suspend()
application.on_resume()
```

---

# 594.203. Lifecycle callback safety

Callbacks phải chạy trong runtime lifecycle context.

---

# 594.204. Reentrant shutdown

Shutdown callback không được trigger recursive shutdown indefinitely.

---

# 594.205. Lifecycle state machine

```text
Created
  │
  ▼
Starting
  │
  ▼
Ready
  │
  ▼
Running
  │
  ├──────→ Stopping → Stopped
  │
  └──────→ Failed
              │
              ▼
          Restarting
              │
              └──→ Starting
```

---

# 594.206. Invalid transition

Invalid lifecycle transition là runtime invariant violation/configuration error.

---

# 594.207. State transition atomicity

Lifecycle state changes phải observable như atomic logical transitions.

---

# 594.208. Supervisor serialization

State mutation của một supervisor phải serialized hoặc synchronization-safe.

---

# 594.209. Parallel supervision

Health monitoring, metrics và process I/O có thể chạy song song.

---

# 594.210. Deterministic event sequence

Concurrent events phải được linearized per process incarnation.

---

# 594.211. Cross-process clock

Không dùng wall-clock timestamps để quyết định ordering.

---

# 594.212. Deadline semantics

Supervisor deadlines dùng monotonic clock.

---

# 594.213. Resource accounting

Supervisor phải distinguish process-owned resources và shared resources.

---

# 594.214. Shared resource failure

Shared resource failure không mặc định terminate tất cả processes.

---

# 594.215. Dependency-aware recovery

Nếu shared dependency chết:

```text dependency restart
→ dependent health check
→ dependent restart if required
```

---

# 594.216. Backoff persistence

Persistent services có thể persist restart backoff state để tránh crash-loop sau supervisor restart.

---

# 594.217. Backoff reset

Successful stable runtime có thể reset restart counter.

---

# 594.218. Stable-period policy

```text stable_duration
```

xác định khi restart budget được reset.

---

# 594.219. Recovery policy

```text RecoveryPolicy {
    restart
    backoff
    budget
    escalation
}
```

---

# 594.220. No infinite recovery

Recovery phải luôn có finite policy hoặc explicit unlimited mode.

---

# 594.221. Unlimited mode

Unlimited restart chỉ được phép khi deployment policy explicitly chọn.

---

# 594.222. Crash diagnostics

Mỗi automatic restart nên giữ reference tới previous failure.

---

# 594.223. Crash aggregation

Crash loop diagnostics aggregate theo:

```text application
process
binary hash
failure class
```

---

# 594.224. No speculative diagnosis

Supervisor không được suy luận nguyên nhân crash ngoài evidence.

---

# 594.225. Process log correlation

Logs có:

```text application_id
instance_id
process_id
incarnation
```

---

# 594.226. Trace correlation

Tracing `475` sử dụng cùng process identity model.

---

# 594.227. Metrics correlation

Metrics labels không được chứa high-cardinality unbounded process identifiers trong default mode.

---

# 594.228. Debug correlation

Debugger sử dụng stable application/artifact identity + runtime process identity.

---

# 594.229. Security boundary

Supervisor privileged operations phải tách khỏi ordinary application code.

---

# 594.230. Privileged helper

Nếu OS yêu cầu privilege:

```text Application
   ↓ IPC
Privileged Supervisor Helper
   ↓
OS
```

---

# 594.231. Privilege minimization

Helper chỉ expose required operations.

---

# 594.232. No arbitrary privileged execution

Application không được dùng supervisor helper như generic root/admin shell.

---

# 594.233. Audit

Privileged lifecycle operations phải audit được.

---

# 594.234. Audit fields

```text action
requester
target_process
timestamp
result
```

---

# 594.235. Secret exclusion

Audit không chứa command secrets/tokens.

---

# 594.236. Process tree export

Debugging API có thể export:

```text process tree
state
health
resources
dependencies
```

---

# 594.237. AI process inspection

AI tooling có thể query structured process state.

---

# 594.238. AI safety

AI không được tự ý:

- kill critical process;
- change restart policy;
- elevate privilege;

nếu không có explicit authorization.

---

# 594.239. AI diagnostics

AI phải phân biệt:

```text observed
reported
unknown
inferred
```

---

# 594.240. AI no hallucination

Không được tạo process state chưa được runtime report.

---

# 594.241. Process semantic snapshot

```text ProcessSnapshot {
    identity
    state
    health
    parent
    children
    resources
    artifact
    capabilities
}
```

---

# 594.242. Snapshot consistency

Snapshot phải có revision/generation.

---

# 594.243. Stale snapshot

Tooling phải biết snapshot đã stale.

---

# 594.244. Supervisor generation

Mỗi state mutation increment generation.

---

# 594.245. Race-free control

Control operation có thể specify expected generation:

```text stop(process, expected_generation)
```

---

# 594.246. Stale control rejection

Nếu generation mismatch:

```text StaleStateError
```

---

# 594.247. Prevent accidental kill

Cơ chế generation giúp tránh kill process incarnation mới bằng stale handle.

---

# 594.248. Process handle incarnation

ProcessHandle phải reference incarnation.

---

# 594.249. Process restart safety

```text old ProcessHandle
      ↓
restart
      ↓
new incarnation
```

old handle không được điều khiển new process.

---

# 594.250. Process tree correctness

Supervisor phải maintain parent-child relationships không mâu thuẫn.

---

# 594.251. Child adoption

Nếu child survives parent unexpectedly, supervisor phải classify:

```text orphaned
external
adopted
terminated
```

---

# 594.252. Default orphan policy

Application-managed child mặc định không được orphan silently.

---

# 594.253. Process groups

Platform adapter map logical subtree to native process groups where possible.

---

# 594.254. Kill subtree

`terminate_tree()` là explicit operation.

---

# 594.255. Service shutdown

Service stop phải propagate cancellation tới child process tree.

---

# 594.256. Shutdown deadline propagation

Parent deadline được chia sẻ/propagate cho children.

---

# 594.257. Deadline inheritance

Child có thể có shorter deadline nhưng không override parent global deadline.

---

# 594.258. Child deadline

```text child_deadline <= parent_deadline
```

ở logical shutdown scope.

---

# 594.259. Resource cleanup deadline

Nếu deadline hết:

```text graceful cleanup abandoned
```

và forced termination policy áp dụng.

---

# 594.260. No cleanup guarantee after kill

Documentation/API phải rõ rằng force kill bỏ qua normal cleanup.

---

# 594.261. Process startup environment

Runtime sets only declared environment variables.

---

# 594.262. Application identity propagation

Child có thể nhận:

```text AXIOM_APPLICATION_ID
AXIOM_INSTANCE_ID
AXIOM_PROCESS_ID
```

qua structured runtime metadata thay vì environment nếu platform hỗ trợ.

---

# 594.263. Metadata propagation

Runtime metadata không được giả mạo bởi ordinary child input.

---

# 594.264. Process authentication

IPC peer identity phải verify bằng OS mechanism hoặc authenticated protocol.

---

# 594.265. PID authentication

PID alone không đủ làm authentication identity.

---

# 594.266. Local IPC security

Named pipes/unix sockets/shared memory phải có access policy.

---

# 594.267. Remote process

Remote processes thuộc distributed system layer `501+`, không phải local process primitive.

---

# 594.268. Local/remote distinction

`Process` API không được giả định network transparency.

---

# 594.269. Process migration

Không có process migration semantic trong core.

---

# 594.270. Container execution

Container có thể được platform/deployment adapter expose như external execution environment.

---

# 594.271. Container ≠ process

Container không được model như ordinary process nếu semantics khác biệt.

---

# 594.272. VM execution

VM cũng là deployment/execution environment, không phải process primitive.

---

# 594.273. Testing process

Test harness có thể spawn supervised processes.

---

# 594.274. Test isolation

Tests có thể chạy isolated process để test crash/resource behavior.

---

# 594.275. Fault injection

Development/testing runtime có thể inject:

```text crash
timeout
IPC failure
resource exhaustion
```

---

# 594.276. Fault injection isolation

Fault injection disabled trong release runtime mặc định.

---

# 594.277. Deterministic testing

Process supervisor test mode có deterministic fake clock/scheduler khi cần.

---

# 594.278. Fake process adapter

Testing có thể thay platform process adapter bằng deterministic simulator.

---

# 594.279. Native integration tests

Mỗi supported OS phải có native process adapter test suite.

---

# 594.280. Cross-platform contract tests

Logical process semantics được test trên tất cả targets.

---

# 594.281. Platform divergence

Nếu semantics không thể giống nhau:

```text capability + documented difference
```

thay vì giả lập sai.

---

# 594.282. Process API layering

```text core
  ↓
runtime
  ↓
platform adapter
  ↓
OS
```

---

# 594.283. Core process model

Core chỉ định nghĩa:

- identity;
- lifecycle;
- ownership;
- state;
- capability;
- dependency;
- supervision.

---

# 594.284. Platform process model

Platform layer định nghĩa:

- PID;
- native signals;
- handles;
- service manager;
- job objects;
- cgroups;
- launchd/systemd-like integration.

---

# 594.285. Native process performance

Process abstraction không được thêm mandatory runtime scheduler vào OS process creation path.

---

# 594.286. Zero-cost ordinary process

Nếu application chỉ cần spawn/wait:

> API phải lower trực tiếp tới native OS primitive khi có thể.

---

# 594.287. Supervisor overhead

Health/restart supervision chỉ được activate khi application khai báo/sử dụng.

---

# 594.288. No mandatory daemon

Ordinary console application không cần supervisor daemon.

---

# 594.289. No mandatory runtime process

Axiom executable có thể chạy trực tiếp với OS entrypoint.

---

# 594.290. Freestanding compatibility

Freestanding programs không cần process supervisor runtime.

---

# 594.291. Static runtime

Process runtime components có thể statically link.

---

# 594.292. Optional runtime

Unused lifecycle/supervisor components phải được dead-strip.

---

# 594.293. Binary-size preservation

Process subsystem không được làm mọi executable tăng kích thước chỉ vì language runtime tồn tại.

---

# 594.294. Native ABI

Process APIs phải có stable ABI boundary.

---

# 594.295. FFI

Native process handles có thể expose qua `451`.

---

# 594.296. Handle wrapping

Foreign native process handles phải được wrap trong safe Axiom resource type.

---

# 594.297. Unsafe escape hatch

Raw native process handles có thể access trong `unsafe`.

---

# 594.298. Ownership of foreign handles

FFI handle ownership phải explicit:

```text borrowed
owned
duplicated
```

---

# 594.299. Resource lifetime

Owned process handle tự release theo `423`.

---

# 594.300. FINAL HARD INVARIANTS

### Invariant 1 — process abstraction

> Axiom có logical process model độc lập với native PID/handle semantics.

### Invariant 2 — no mandatory supervisor

> Ordinary Axiom executable không bắt buộc chạy qua supervisor daemon/runtime.

### Invariant 3 — native efficiency

> Simple process operations phải lower trực tiếp tới native OS primitives khi có thể.

### Invariant 4 — explicit lifecycle

> Process lifecycle phải có state machine xác định.

### Invariant 5 — incarnation safety

> Process restart tạo incarnation mới; stale handle không được điều khiển process mới.

### Invariant 6 — graceful-first

> Termination phải ưu tiên cooperative shutdown trước forced termination.

### Invariant 7 — no fake cleanup

> Force termination không được tuyên bố rằng destructor/drop/defer đã chạy.

### Invariant 8 — dependency correctness

> Process startup/shutdown/recovery phải tôn trọng declared dependency graph.

### Invariant 9 — bounded recovery

> Crash recovery phải có restart budget/backoff hoặc explicit unlimited policy.

### Invariant 10 — crash truth

> Supervisor chỉ report nguyên nhân crash khi có evidence; otherwise `Unknown`.

### Invariant 11 — capability inheritance

> Child process không được tự nâng capability; mặc định capability là subset của parent.

### Invariant 12 — privilege isolation

> Privileged process operations phải nằm sau explicit security boundary.

### Invariant 13 — IPC identity

> IPC authentication không được dựa đơn thuần trên PID.

### Invariant 14 — cross-platform honesty

> Unsupported OS process semantics phải được báo là unsupported, không giả lập sai.

### Invariant 15 — deterministic event ordering

> Events của cùng process incarnation phải có ordering xác định.

### Invariant 16 — monotonic deadlines

> Timeout/deadline semantics dùng monotonic clock.

### Invariant 17 — resource ownership

> Process handles, pipes và IPC resources phải có deterministic ownership/lifetime.

### Invariant 18 — AI observability

> AI tooling chỉ được sử dụng observed structured process state và phải phân biệt stale/unknown/inferred state.

### Invariant 19 — no hidden mutation

> IDE/AI/runtime không được silently kill, restart hoặc elevate process ngoài authorized policy.

### Invariant 20 — minimal runtime overhead

> Không-used process supervision functionality phải có khả năng bị loại bỏ khỏi final binary.

---

# 594 — LOCKED

Axiom hiện có:

```text
593 Deployment Package
        │
        ▼
594 Application Runtime
        │
        ├── Process
        ├── Supervisor
        ├── Lifecycle
        ├── Health
        ├── Recovery
        ├── IPC
        └── Resource Control
```

Điểm quan trọng là `594` **không biến mọi Axiom application thành một framework runtime nặng**. Một chương trình đơn giản vẫn có thể là native executable gần như trực tiếp trên OS; supervisor/process orchestration chỉ xuất hiện khi được sử dụng.

---

# NEXT — BOOTSTRAP-595

## NATIVE APPLICATION CONFIGURATION & ENVIRONMENT 5.0
### CONFIG SCHEMA, TYPED CONFIGURATION, ENVIRONMENT VARIABLES, COMMAND-LINE ARGUMENTS, CONFIG FILES, SECRETS BOUNDARY, PROFILE/ENVIRONMENT OVERLAY, RUNTIME OVERRIDES, VALIDATION, MIGRATION, HOT RELOAD & DETERMINISTIC CONFIG RESOLUTION

```text
              Application
                   │
                   ▼
           Configuration Engine
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Defaults     Config File   Environment
       │           │           │
       └───────────┼───────────┘
                   ▼
             CLI Overrides
                   │
                   ▼
            Typed Config Tree
                   │
          ┌────────┴────────┐
          ▼                 ▼
       Runtime           Secrets
       Policy            Boundary
          │                 │
          └────────┬────────┘
                   ▼
             Application
```

`595` sẽ chuẩn hóa một vấn đề hiện đang nằm rải rác giữa `470`, `468`, `593` và `594`: **application lấy configuration từ đâu, thứ tự override thế nào, làm sao đảm bảo typed/safe/deterministic, và đặc biệt làm sao giữ secrets tách khỏi source/package/build artifacts.**