# BOOTSTRAP-470 — CONFIGURATION, SETTINGS, PREFERENCES, ENVIRONMENT, FEATURE FLAGS & RUNTIME POLICY SYSTEM

**Trạng thái: COMPLETED / LOCKED**

470 hoàn thiện hệ thống configuration/policy mà 468 đã đặt nền móng.

Nguyên tắc trung tâm:

```text id="c0nfig1"
Compile-time Configuration
        ≠
Build Feature
        ≠
Runtime Configuration
        ≠
User Preference
        ≠
Secret
        ≠
Runtime Policy
```

---

## 470.1 — Typed configuration

Configuration phải có schema và type.

Ví dụ:

```text
config AppConfig {
    language: String
    max_connections: u32
    enable_cache: bool
    timeout: Duration
}
```

Không coi mọi configuration là `String → String`.

---

## 470.2 — Configuration source

Nguồn có thể gồm:

```text
Default
System
Machine
User
Project
Environment
CommandLine
Session
Remote
```

`Remote` chỉ là provider; không phải cơ chế bắt buộc.

---

## 470.3 — Precedence

Resolution order phải deterministic.

Mặc định:

```text
default
→ system
→ machine
→ user
→ project
→ environment
→ command line
→ session
```

Application có thể định nghĩa schema-specific policy nhưng không được tạo resolution ambiguity.

---

## 470.4 — Effective configuration

Resolver tạo immutable snapshot:

```text
EffectiveConfig
```

Snapshot gồm:

```text
key
value
source
schema_version
```

---

## 470.5 — Configuration provenance

Mọi effective value có thể truy vấn:

```text
config.get("timeout")
config.source("timeout")
```

Ví dụ source:

```text
environment: AXIOM_TIMEOUT
```

---

## 470.6 — Explain configuration

Tooling có thể hỏi:

```text
Why is timeout = 30s?
```

và nhận:

```text
value = 30s
source = project
overrode = user/default
```

---

## 470.7 — Missing values

Missing configuration không mặc định là error.

Schema quyết định:

```text
required
optional
defaulted
```

---

## 470.8 — Validation

Validation diễn ra trước khi configuration trở thành effective configuration.

---

## 470.9 — Cross-field validation

Schema có thể định nghĩa constraints:

```text
min <= max
```

---

## 470.10 — Validation errors

Configuration validation dùng `Result`, diagnostic code và source provenance.

---

# 470.11 — Immutable snapshot

Effective configuration mặc định immutable.

Điều này giúp:

- thread safety;
- deterministic behavior;
- caching;
- testing.

---

## 470.12 — Dynamic configuration

Application có thể subscribe configuration changes.

Không bắt buộc mọi subsystem hỗ trợ dynamic reload.

---

## 470.13 — Configuration transaction

Update nhiều keys phải có thể commit atomically:

```text
read
→ validate
→ prepare
→ commit
```

---

## 470.14 — Failed update

Nếu validation thất bại, effective configuration cũ tiếp tục tồn tại.

---

## 470.15 — Configuration generation

Mỗi committed configuration snapshot có generation/version.

---

# 470.16 — Preferences

Preferences biểu diễn lựa chọn của người dùng.

Ví dụ:

```text
theme
language
font_size
editor_tab_width
notifications
```

---

## 470.17 — Preference persistence

Preferences có thể persist bằng 455.

---

## 470.18 — Preference reset

API phải hỗ trợ reset:

```text
reset(key)
reset(group)
reset(all)
```

---

## 470.19 — Preferences migration

Schema version của preferences có migration.

---

# 470.20 — Environment variables

Environment là external input.

Tên biến và parser thuộc application/configuration layer.

---

## 470.21 — Environment parsing

Không tự động convert tùy tiện.

Ví dụ:

```text
"false"
```

phải được parse theo boolean grammar đã định nghĩa.

---

## 470.22 — Environment security

Environment có thể chứa secret và không được log nguyên văn mặc định.

---

# 470.23 — Command-line configuration

CLI override configuration phải explicit.

Ví dụ:

```text
--timeout=30s
--cache
--no-cache
```

---

## 470.24 — CLI provenance

Effective config phải biết value đến từ command line nào.

---

## 470.25 — Unknown options

Unknown configuration options tạo diagnostic thay vì silently ignore trong strict mode.

---

# 470.26 — Project configuration

Project configuration nằm trong build/project scope.

Tích hợp 432.

---

## 470.27 — Workspace configuration

Workspace có thể cung cấp inherited configuration.

---

## 470.28 — Package configuration

Package có thể khai báo configuration metadata nhưng không được âm thầm thay đổi configuration của consumer.

---

# 470.29 — Feature flags

Feature flag là explicit boolean/enum policy.

```text
feature logging_v2
feature gpu_acceleration
```

---

## 470.30 — Build feature

Build feature ảnh hưởng compilation/build graph.

Nó không giống runtime feature flag.

---

## 470.31 — Compile-time feature

Compile-time selection có thể loại code khỏi binary.

---

## 470.32 — Runtime feature

Runtime flag không được giả định đã loại code khỏi binary.

---

## 470.33 — Target feature

CPU/GPU/OS capability phải phân biệt với application feature flag.

---

# 470.34 — Configuration vs comptime

431 comptime có thể đọc **explicit compile-time inputs**, nhưng không được tự ý đọc user/system runtime configuration.

---

## 470.35 — Reproducibility

Build inputs phải được ghi nhận để biết configuration nào ảnh hưởng artifact.

---

## 470.36 — Configuration fingerprint

Build system có thể tạo fingerprint:

```text
ConfigHash
```

cho các configuration ảnh hưởng compilation.

---

# 470.37 — Runtime policy

Policy quyết định behavior runtime mà không thay đổi language semantics.

Ví dụ:

```text
allocation limits
network timeout
logging
cache budget
GPU selection
thread limits
```

---

## 470.38 — Policy ownership

Mỗi policy có owner:

```text
application
library
runtime
platform
```

Không được có nhiều owner ghi đè ngầm.

---

## 470.39 — Policy inheritance

Policy có thể inherit từ parent context nhưng precedence phải deterministic.

---

## 470.40 — Scoped policy

Có thể override policy trong scope:

```text
with policy(timeout = 5s) {
    ...
}
```

Nếu được library hỗ trợ.

---

# 470.41 — Allocator policy

Application có thể chọn allocator:

```text
system
arena
pool
custom
```

theo 423.

---

## 470.42 — Memory policy

Có thể đặt:

```text
memory budget
allocation limit
cache budget
```

Nhưng allocator không được âm thầm chuyển sang GC.

---

## 470.43 — Thread policy

Có thể cấu hình:

```text
worker count
affinity
stack size
scheduler policy
```

Tích hợp 424.

---

## 470.44 — Async policy

Executor có thể được cấu hình:

```text
worker_count
queue_capacity
blocking_pool
```

Không biến async thành thread tự động.

---

# 470.45 — Network policy

454 có thể sử dụng:

```text
connect timeout
read timeout
proxy
DNS policy
TLS policy
connection limits
```

---

## 470.46 — Storage policy

455 có thể sử dụng:

```text
cache size
sync policy
WAL mode
durability
```

---

## 470.47 — GPU policy

459 có thể sử dụng:

```text
preferred device
memory budget
queue count
power/performance preference
```

---

## 470.48 — Audio policy

461 có thể sử dụng:

```text
sample rate
buffer size
device
latency target
```

Nhưng `@realtime` semantics không bị thay đổi bởi configuration.

---

# 470.49 — Logging configuration

Logging level có thể là runtime configuration:

```text
off
error
warn
info
debug
trace
```

---

## 470.50 — Structured logging

Configuration phải hỗ trợ structured logging policy thay vì chỉ text.

---

## 470.51 — Secret redaction

Secret-bearing configuration values có metadata:

```text
@sensitive
```

Tooling phải redact.

---

# 470.52 — Secret reference

Configuration có thể chứa:

```text
secret://provider/key
```

nhưng secret value không nằm trực tiếp trong ordinary config.

---

## 470.53 — Secure storage

Secure storage provider thuộc platform/security layer.

Không đưa keychain/credential manager vào core.

---

## 470.54 — Secret lifetime

Secret material nên có lifetime ngắn nhất có thể.

---

## 470.55 — Secret memory

Sensitive memory có thể yêu cầu:

```text
zeroize
locked memory
non-swappable
```

khi platform hỗ trợ.

---

# 470.56 — Configuration persistence

Persistent configuration sử dụng atomic update semantics của 455.

---

## 470.57 — Corruption

Corrupt configuration không được silently interpreted as default nếu điều đó có thể làm thay đổi security behavior.

---

## 470.58 — Recovery

Có thể:

```text
restore backup
reset invalid key
reset profile
```

---

# 470.59 — Configuration watching

File-based configuration có thể watch thay đổi.

---

## 470.60 — Debounce

Rapid changes có thể được coalesce.

---

## 470.61 — Reload transaction

Reload:

```text
read
→ parse
→ validate
→ construct
→ publish
```

Không publish partial state.

---

# 470.62 — Thread safety

Configuration snapshots có thể được share giữa threads nếu type đáp ứng 424 `Share`.

---

## 470.63 — No global mutable singleton

Language/runtime không tạo một global mutable configuration object mặc định.

---

## 470.64 — Dependency injection

Subsystem có thể nhận explicit configuration/policy object.

---

# 470.65 — Testing

Configuration test phải kiểm tra:

```text
defaults
precedence
override
validation
migration
reload
rollback
provenance
secrets
```

---

## 470.66 — Property testing

Resolver phải có property tests cho precedence và deterministic resolution.

---

## 470.67 — Fuzzing

Fuzz:

```text
config files
environment
CLI
schema
migration
```

---

# 470.68 — AI metadata

446 expose:

```text
configuration schema
effective values
source
overrides
generation
policy owner
sensitivity
```

---

## 470.69 — Configuration diff

Tooling hỗ trợ:

```text
config diff A B
```

---

## 470.70 — Configuration explain

AI có thể query:

```text
why(value)
what_overrides(key)
what_depends_on(key)
```

---

# 470.71 — Security

Configuration không phải trusted input chỉ vì đến từ local file.

---

## 470.72 — Remote configuration

Remote configuration phải có:

```text
authentication
integrity
version
expiry
rollback
```

nếu application chọn sử dụng.

---

## 470.73 — Remote config failure

Mất network không được tự động biến configuration thành undefined state.

---

# 470.74 — Determinism

Compiler/build configuration resolution phải deterministic.

Runtime configuration có thể dynamic nhưng mỗi snapshot phải deterministic.

---

## 470.75 — Artifact metadata

Compiler ghi lại configuration inputs liên quan đến artifact khi cần reproducibility.

---

# 470.76 — Hard invariants

1. Configuration có type.
2. Configuration có schema.
3. Configuration có source.
4. Effective configuration là explicit snapshot.
5. Resolution deterministic.
6. Precedence deterministic.
7. Missing values có semantics.
8. Validation bắt buộc trước publish.
9. Cross-field validation được hỗ trợ.
10. Invalid update không phá snapshot cũ.
11. Configuration generation được theo dõi.
12. Dynamic reload là explicit.
13. Reload là transactional.
14. Preferences khác configuration semantics.
15. Preferences có thể reset.
16. Preferences có schema migration.
17. Environment là external input.
18. Environment parser explicit.
19. CLI override có provenance.
20. Project configuration tích hợp 432.
21. Workspace inheritance deterministic.
22. Package không âm thầm override consumer configuration.
23. Feature flag khác build feature.
24. Build feature khác runtime flag.
25. Target feature khác application feature.
26. Comptime không đọc runtime configuration ngầm.
27. Build configuration ảnh hưởng artifact phải có fingerprint/provenance.
28. Runtime policy có owner.
29. Policy inheritance deterministic.
30. Scoped policy phải explicit.
31. Allocator policy tích hợp 423.
32. Thread policy tích hợp 424.
33. Async policy không tự biến async thành threads.
34. Network policy tích hợp 454.
35. Storage policy tích hợp 455.
36. GPU policy tích hợp 459.
37. Audio policy tích hợp 461.
38. Logging configuration structured.
39. Secrets được đánh dấu sensitive.
40. Sensitive values không log mặc định.
41. Secret reference khác secret value.
42. Secure storage không thuộc core.
43. Secret lifetime phải explicit.
44. Persistent config có atomic update.
45. Corrupt security-sensitive config không silently default.
46. Configuration watcher có transactional reload.
47. Không có global mutable configuration mặc định.
48. Explicit dependency injection được hỗ trợ.
49. Configuration snapshots có thể share an toàn.
50. Configuration có fuzz testing.
51. Resolver có property testing.
52. AI có thể query provenance.
53. AI có thể query effective configuration.
54. AI có thể query overrides.
55. AI có thể query configuration diff.
56. AI có thể query policy ownership.
57. Remote configuration là optional.
58. Remote configuration phải có integrity nếu được sử dụng.
59. Remote failure không tạo undefined policy.
60. Runtime configuration không thay đổi language semantics.
61. Configuration subsystem không yêu cầu GUI.
62. Configuration subsystem không yêu cầu database.
63. Configuration subsystem không yêu cầu network.
64. Configuration subsystem không yêu cầu GC.
65. Configuration subsystem không yêu cầu hidden thread.
66. Configuration subsystem có thể bị loại khỏi freestanding binary.
67. **Axiom configuration/policy system phải biến mọi quyết định cấu hình quan trọng thành dữ liệu typed, có schema, provenance, precedence và lifecycle rõ ràng, đồng thời tuyệt đối tránh hidden global state và tránh nhầm lẫn giữa build-time, runtime, preference, feature và security policy.**

**BOOTSTRAP-470 hoàn tất.**

---

# BOOTSTRAP-471 — TASK / JOB / WORK QUEUE, SCHEDULING, THREAD POOL & PARALLEL EXECUTION FOUNDATION

471 xây lớp abstraction cao hơn 424.

Mục tiêu là cho phép:

```text
CPU
 ├── Thread
 ├── Task
 ├── Job
 ├── ThreadPool
 ├── WorkQueue
 └── Parallel Loop
```

nhưng **không biến mọi task thành OS thread**.

Kiến trúc:

```text
Application
    ↓
Job / Task
    ↓
Scheduler
    ↓
Work Queue
    ↓
Worker
 ┌──┴───────────┐
 ↓              ↓
OS Thread     Async Executor
```

### 471 sẽ khóa:

- distinction Thread / Task / Job / Future;
- worker threads;
- thread pools;
- work queues;
- FIFO/LIFO/deque;
- priority;
- deadlines;
- cancellation;
- structured task groups;
- task dependencies;
- DAG execution;
- work stealing;
- CPU affinity;
- NUMA;
- cooperative scheduling;
- blocking jobs;
- CPU-bound jobs;
- IO-bound jobs;
- async executor integration;
- parallel loops;
- map/reduce;
- fork/join;
- task-local state;
- task context;
- panic/error propagation;
- task ownership;
- result channels;
- backpressure;
- bounded queues;
- shutdown;
- drain;
- cancellation propagation;
- worker failure;
- starvation/deadlock diagnostics;
- deterministic scheduler mode cho testing;
- tracing/profiling;
- AI-readable task graph;
- GPU task interoperability với 459;
- realtime isolation với 461;
- no hidden global thread pool;
- no mandatory scheduler runtime.

Điểm quan trọng:

```text
Thread
  = execution resource

Task
  = logical unit of work

Job
  = schedulable work item

Future
  = representation of eventual result
```

và:

```text
Task ≠ Thread
Async ≠ ThreadPool
Parallelism ≠ Implicit Parallelism
```

471 sẽ cung cấp nền tảng để sau này xây **parallel algorithms, actor/message systems, dataflow, compiler parallelism, server worker pools và high-performance compute** mà vẫn giữ semantics rõ ràng của 424.