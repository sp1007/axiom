# BOOTSTRAP-501 — DISTRIBUTED SYSTEM FOUNDATION, SERVICE DISCOVERY, MEMBERSHIP, CONSISTENCY, CLOCKS, FAILURE DETECTION & FAULT-TOLERANT PRIMITIVES

**Trạng thái: COMPLETED / LOCKED**

501 xây dựng tầng nền cho distributed systems trên 474, 475, 476, 490, 499 và 500.

Mục tiêu không phải biến Axiom thành một framework distributed bắt buộc, mà cung cấp **primitive rõ ràng** để có thể xây:

- distributed service;
- cluster;
- replicated storage;
- message broker;
- distributed cache;
- scheduler;
- service mesh;
- consensus system;
- fault-tolerant application.

Kiến trúc:

```text id="7c4m2x"
                    Axiom Core
                        │
              ┌─────────┴─────────┐
              ↓                   ↓
          Networking 454       Time 474
              │                   │
              └─────────┬─────────┘
                        ↓
                 IPC / RPC 500
                        ↓
              Distributed Foundation
              ┌─────────┼─────────┐
              ↓         ↓         ↓
          Discovery   Membership  Failure
              │         │         │
              └─────────┼─────────┘
                        ↓
                Consistency / Replication
                        ↓
              Distributed Applications
```

---

## 501.1 — Distributed system ≠ network

Có network không có nghĩa application là distributed system.

---

## 501.2 — Node

`Node` là execution participant có identity trong distributed system.

---

## 501.3 — Node identity

Node identity phải stable trong lifetime được định nghĩa bởi hệ thống.

---

## 501.4 — Process identity

Node identity không nhất thiết bằng OS process ID.

---

## 501.5 — Instance identity

Restarted process có thể là instance mới của cùng logical node.

---

## 501.6 — Cluster

Cluster là tập node có membership semantics chung.

---

## 501.7 — Cluster membership

Membership phải phân biệt:

```text id="m8x3q2"
Known
Joining
Alive
Suspected
Leaving
Dead
Removed
```

---

## 501.8 — Membership authority

Không mặc định có một global authority.

---

## 501.9 — Discovery

Discovery trả lời:

> Service/node nào hiện có thể được liên lạc?

---

## 501.10 — Discovery ≠ health

Một endpoint tồn tại không có nghĩa service đang healthy.

---

## 501.11 — Discovery ≠ authorization

Discovery không cấp quyền truy cập.

---

## 501.12 — Static discovery

Configuration có thể chứa static endpoints.

---

## 501.13 — DNS discovery

DNS có thể làm discovery provider.

---

## 501.14 — Registry discovery

Service registry có thể cung cấp endpoint records.

---

## 501.15 — Local discovery

Platform/local registry có thể được sử dụng cho local services.

---

## 501.16 — Discovery record

Conceptual:

```text id="q6m2x8"
ServiceId
InstanceId
Endpoint
Protocol
Version
Capabilities
Metadata
Expiration
```

---

## 501.17 — TTL

Discovery records có thể có TTL.

---

## 501.18 — Expiration

Expired record không được coi là live endpoint nếu policy yêu cầu freshness.

---

## 501.19 — Stale discovery

Client phải chịu được discovery data stale.

---

## 501.20 — Multiple endpoints

Một service có thể có nhiều instances.

---

## 501.21 — Endpoint selection

Selection policy có thể dựa trên:

- locality;
- capability;
- health;
- load;
- priority;
- topology.

Compiler không áp đặt policy.

---

## 501.22 — Load balancing

Load balancing là library/runtime service layer.

---

## 501.23 — Health

Health có thể gồm:

```text id="h5m8x2"
Liveness
Readiness
Health
```

Ba khái niệm không đồng nhất.

---

## 501.24 — Liveness

Liveness hỏi node còn hoạt động theo failure detector hay không.

---

## 501.25 — Readiness

Readiness hỏi service có nhận workload hay không.

---

## 501.26 — Health check

Health check là application/platform contract.

---

## 501.27 — Failure detector

Failure detector cung cấp suspicion/evidence, không phải oracle tuyệt đối.

---

## 501.28 — False positive

Node có thể bị suspect dù thực tế vẫn sống.

---

## 501.29 — False negative

Failure detector có thể chưa phát hiện node đã chết.

---

## 501.30 — Failure detector state

Failure detector phải expose uncertainty.

---

## 501.31 — Heartbeat

Heartbeat là một implementation strategy.

---

## 501.32 — Phi/accrual detection

Advanced failure detectors có thể estimate suspicion level.

Không được biến estimate thành certainty.

---

## 501.33 — Network partition

Network partition phải được xem là trạng thái riêng.

---

## 501.34 — Partition ≠ node failure

Không được suy ra node chết chỉ từ việc không liên lạc được.

---

## 501.35 — Split brain

Hệ thống phải có policy ngăn hoặc giới hạn conflicting authorities.

---

## 501.36 — Leader

Leader là role/protocol concept, không phải language primitive.

---

## 501.37 — Leader election

Leader election là distributed algorithm/library.

---

## 501.38 — Election term

Election có logical term/epoch khi protocol yêu cầu.

---

## 501.39 — Fencing

Fencing token có thể ngăn stale leader tiếp tục ghi.

---

## 501.40 — Lease

Lease là time-bounded authority.

Lease phải phụ thuộc clock assumptions rõ ràng.

---

## 501.41 — Lease ≠ lock

Distributed lease và local mutex không có cùng semantics.

---

## 501.42 — Distributed lock

Distributed lock là library primitive, không phải core language feature.

---

## 501.43 — Lock safety

Distributed lock safety phụ thuộc protocol và failure assumptions.

---

## 501.44 — Consensus

Consensus là library/protocol layer.

---

## 501.45 — Consensus interface

Conceptual:

```text id="c7m3x9"
propose(value)
→ Result<Decision, ConsensusError>
```

---

## 501.46 — Consensus limitations

Axiom không tuyên bố consensus có thể giải quyết partition/liveness trong mọi failure model.

---

## 501.47 — Quorum

Quorum policy phải explicit.

---

## 501.48 — Majority

Majority là một quorum policy, không phải universal requirement.

---

## 501.49 — Read quorum

Read quorum semantics phải được document.

---

## 501.50 — Write quorum

Write quorum semantics phải được document.

---

## 501.51 — Replication

Replication copies logical state giữa nodes.

---

## 501.52 — Primary/replica

Primary/replica là topology policy.

---

## 501.53 — Multi-primary

Multi-primary cần conflict policy.

---

## 501.54 — Conflict

Conflict resolution phải explicit.

---

## 501.55 — Last-write-wins

LWW chỉ là một policy, không phải mặc định của distributed data.

---

## 501.56 — Version vectors

Version vectors có thể biểu diễn causal relationships.

---

## 501.57 — Logical clocks

Logical clocks không đo physical elapsed time.

---

## 501.58 — Lamport clock

Lamport clock biểu diễn partial ordering theo causal relation.

---

## 501.59 — Vector clock

Vector clock có thể biểu diễn concurrency giữa events.

---

## 501.60 — Hybrid logical clock

HLC kết hợp physical-time approximation với logical ordering.

---

## 501.61 — Physical clocks

474 vẫn là nguồn semantics cho local monotonic/wall clocks.

---

## 501.62 — Distributed clock assumption

Distributed algorithms phải declare clock assumptions.

---

## 501.63 — Clock skew

Clock skew phải được xem xét khi dùng wall-clock timestamps.

---

## 501.64 — Clock synchronization

NTP/PTP là platform/network mechanisms.

---

## 501.65 — Timestamp ≠ ordering

Timestamp không mặc định chứng minh event ordering.

---

## 501.66 — Causality

Distributed system có thể track causal context.

---

## 501.67 — Causal metadata

Metadata có thể gồm:

```text id="p8m4x1"
Lamport
Vector
HLC
TraceId
```

---

## 501.68 — Event identity

Distributed event có stable ID nếu deduplication cần.

---

## 501.69 — Idempotency

500 idempotency semantics được tái sử dụng.

---

## 501.70 — Deduplication

Receiver có thể maintain processed-event IDs.

---

## 501.71 — At-most-once

Delivery semantics có thể là at-most-once.

---

## 501.72 — At-least-once

Delivery semantics có thể là at-least-once.

---

## 501.73 — Exactly-once

Không được quảng bá exactly-once nếu implementation chỉ cung cấp deduplication + retry.

---

## 501.74 — Durable messaging

Durable messages phải được persist trước khi protocol tuyên bố durability.

---

## 501.75 — Backpressure

Distributed streams phải expose backpressure.

---

## 501.76 — Overload

Overload là trạng thái cần xử lý, không phải transport failure đơn thuần.

---

## 501.77 — Admission control

Node có thể reject workload trước khi resource exhaustion.

---

## 501.78 — Circuit breaker

Circuit breaker là library-level resilience primitive.

---

## 501.79 — Retry budget

Retry phải có budget để tránh retry storms.

---

## 501.80 — Exponential backoff

Backoff policy phải có bounds.

---

## 501.81 — Jitter

Jitter có thể tránh synchronized retries.

---

## 501.82 — Timeout budget

Nested calls nên propagate remaining deadline.

---

## 501.83 — Failure classification

Distributed error phải distinguish:

```text id="z5m8q2"
Timeout
Unavailable
Overloaded
Rejected
Unauthorized
InvalidRequest
ApplicationError
ProtocolError
Unknown
```

---

## 501.84 — Partial failure

Một distributed operation có thể partially succeed.

---

## 501.85 — Partial result

API phải có cách biểu diễn partial result nếu operation hỗ trợ.

---

## 501.86 — Compensation

Compensating operation không tự động rollback remote side effect.

---

## 501.87 — Saga

Saga là application/library pattern.

---

## 501.88 — Distributed transaction

Không thuộc core runtime.

---

## 501.89 — Membership changes

Membership changes là events có version/epoch khi cần.

---

## 501.90 — Stale membership

Node phải không dùng stale membership để thực hiện authority-sensitive action nếu protocol cấm.

---

## 501.91 — Fencing epochs

Epoch/fencing token dùng để invalidate stale actors.

---

## 501.92 — Service version

Service discovery phải phân biệt service version với instance version.

---

## 501.93 — Capability advertisement

Instance có thể advertise capabilities.

---

## 501.94 — Capability ≠ authorization

Advertised capability không tự cấp authority.

---

## 501.95 — Security

Discovery metadata có thể bị attacker giả mạo nếu transport/authentication không bảo vệ.

---

## 501.96 — Trust

Secure discovery phải authenticate registry/peer khi threat model yêu cầu.

---

## 501.97 — AI observability

AI tooling có thể query:

```text id="x8m2q4"
cluster_state()
membership()
suspicions()
discovery()
leaders()
epochs()
quorum()
replication()
```

---

## 501.98 — Testing

Phải test:

- partition;
- delayed packets;
- duplicated packets;
- reordered packets;
- node crash;
- restart;
- clock skew;
- stale leader;
- retry storm;
- overloaded node;
- registry failure.

---

## 501.99 — Deterministic simulation

Distributed algorithms nên có simulator với:

- virtual clock;
- deterministic message scheduler;
- fault injection.

---

## 501.100 — Hard invariants

1. Distributed system khác network.
2. Node có identity.
3. Node identity khác process ID.
4. Instance identity được phân biệt.
5. Cluster có membership semantics.
6. Membership states explicit.
7. Discovery khác health.
8. Discovery khác authorization.
9. Static discovery được hỗ trợ.
10. DNS discovery được hỗ trợ.
11. Registry discovery được hỗ trợ.
12. Local discovery được hỗ trợ.
13. Discovery record có identity.
14. Discovery record có endpoint.
15. Discovery record có protocol.
16. Discovery record có version.
17. Discovery record có capabilities.
18. TTL được hỗ trợ.
19. Expiration được xử lý.
20. Client phải chịu stale discovery.
21. Multi-instance service được hỗ trợ.
22. Endpoint selection là policy.
23. Load balancing không thuộc compiler core.
24. Liveness khác readiness.
25. Readiness khác health.
26. Failure detector không phải oracle.
27. False positive được thừa nhận.
28. False negative được thừa nhận.
29. Heartbeat chỉ là strategy.
30. Advanced failure detectors phải expose uncertainty.
31. Partition khác node failure.
32. Split-brain phải có mitigation.
33. Leader là protocol role.
34. Leader election là library.
35. Election epoch/term được hỗ trợ.
36. Fencing được hỗ trợ.
37. Lease khác lock.
38. Distributed lock không thuộc core.
39. Consensus không thuộc core.
40. Consensus interface phải expose failure.
41. Quorum explicit.
42. Majority chỉ là một policy.
43. Read/write quorum semantics explicit.
44. Replication được hỗ trợ.
45. Primary/replica là policy.
46. Multi-primary cần conflict policy.
47. Conflict resolution explicit.
48. LWW không mặc định.
49. Version vectors được hỗ trợ.
50. Logical clocks khác physical clocks.
51. Lamport clocks được hỗ trợ.
52. Vector clocks được hỗ trợ.
53. HLC được hỗ trợ.
54. 474 clock semantics được giữ.
55. Distributed clock assumptions phải explicit.
56. Clock skew phải được xét.
57. NTP/PTP không phải language primitive.
58. Timestamp không mặc định là causal ordering.
59. Causality metadata được hỗ trợ.
60. Event identity được hỗ trợ.
61. Idempotency tích hợp 500.
62. Deduplication được hỗ trợ.
63. At-most-once được định nghĩa.
64. At-least-once được định nghĩa.
65. Exactly-once không được claim giả.
66. Durable messaging phải chứng minh persistence.
67. Backpressure được hỗ trợ.
68. Overload được phân biệt.
69. Admission control được hỗ trợ.
70. Circuit breaker là library primitive.
71. Retry budget được hỗ trợ.
72. Backoff có bounds.
73. Jitter được hỗ trợ.
74. Deadline propagation tích hợp 474/500.
75. Failure classification structured.
76. Partial failure được mô hình hóa.
77. Partial result được hỗ trợ khi cần.
78. Compensation không phải rollback.
79. Saga là library/application pattern.
80. Distributed transaction không thuộc core.
81. Membership changes có epoch/version khi cần.
82. Stale membership không được dùng sai cho authority.
83. Fencing epochs được hỗ trợ.
84. Service version khác instance version.
85. Capability advertisement khác authorization.
86. Discovery security được hỗ trợ.
87. Registry/peer authentication được hỗ trợ.
88. Distributed state có thể được AI query.
89. Fault-injection testing được hỗ trợ.
90. Partition testing được hỗ trợ.
91. Clock-skew testing được hỗ trợ.
92. Retry-storm testing được hỗ trợ.
93. Deterministic distributed simulation được hỗ trợ.
94. Virtual clock được hỗ trợ.
95. Deterministic message scheduling được hỗ trợ.
96. Failure injection được hỗ trợ.
97. Distributed primitives không tạo hidden runtime.
98. Distributed system không mặc định có global scheduler/registry.
99. Performance/latency/failure assumptions phải được document.
100. **Axiom distributed foundation phải cung cấp primitive rõ ràng cho discovery, membership, failure detection, consistency và replication nhưng không che giấu bản chất uncertain của distributed systems: partition, clock skew, duplicate, reorder, timeout và partial failure luôn là những trạng thái có thể xảy ra và phải được biểu diễn đúng trong API.**

**BOOTSTRAP-501 hoàn tất / LOCKED.**

---

# BOOTSTRAP-502 — DISTRIBUTED STORAGE, REPLICATION, CONSENSUS, QUORUM, LEADER ELECTION & DURABLE STATE FOUNDATION

**Trạng thái: COMPLETED / LOCKED**

502 đưa 501 vào tầng **durable distributed state**.

Mục tiêu:

```text id="e6m2q8"
Storage 455
   ↓
Serialization 499
   ↓
IPC/RPC 500
   ↓
Distributed Foundation 501
   ↓
Replication / Consensus / Durable State 502
```

Axiom phải đủ khả năng xây distributed database, replicated KV store, metadata service hoặc distributed cache mà không yêu cầu runtime magic.

---

## 502.1 — Logical state

Distributed storage quản lý logical state:

```text id="t8x3m1"
Key → Value
```

hoặc structured records.

---

## 502.2 — Local state

Local storage là physical representation của logical state.

---

## 502.3 — Replica

Replica là một copy logical state có replication protocol.

---

## 502.4 — Replica identity

Replica có stable identity.

---

## 502.5 — Replica role

Có thể:

```text id="p4m8x2"
Leader
Follower
Candidate
Observer
Learner
ReadReplica
```

Role tùy protocol.

---

## 502.6 — Log

Replicated log:

```text id="q7m2x5"
Index
Term/Epoch
Command
Metadata
Checksum
```

---

## 502.7 — Log entry identity

Entry identity dựa trên log position + protocol epoch/term khi protocol yêu cầu.

---

## 502.8 — Commit index

Replicated log có thể maintain committed position.

---

## 502.9 — Applied index

Applied position khác committed position.

---

## 502.10 — Durable index

Durably persisted position khác merely received position.

---

## 502.11 — State machine

Replica có thể implement deterministic state machine.

---

## 502.12 — Deterministic command

Consensus state machine command phải deterministic nếu replicated execution yêu cầu.

---

## 502.13 — Nondeterminism

Random/time/external IO phải không được implicit trong deterministic replicated state machine.

---

## 502.14 — Command result

Command có thể trả result sau commit/apply.

---

## 502.15 — Linearization point

Consistency model phải define point tại đó operation được xem là committed/visible.

---

## 502.16 — Linearizable

Linearizability là explicit consistency model, không phải mặc định mọi storage.

---

## 502.17 — Sequential consistency

Có thể cung cấp sequential consistency khi protocol phù hợp.

---

## 502.18 — Eventual consistency

Eventual consistency được phép trong hệ thống không cần strong ordering.

---

## 502.19 — Causal consistency

Causal consistency có thể dùng metadata từ 501.

---

## 502.20 — Session consistency

Có thể support read-your-writes/monotonic reads tùy service.

---

## 502.21 — Consistency declaration

API phải document consistency guarantees.

---

## 502.22 — Quorum read

Quorum read cần explicit quorum size/policy.

---

## 502.23 — Quorum write

Quorum write cần explicit quorum size/policy.

---

## 502.24 — Read repair

Read repair là implementation strategy.

---

## 502.25 — Anti-entropy

Background reconciliation có thể đồng bộ divergent replicas.

---

## 502.26 — Merkle tree

Merkle structures có thể giảm dữ liệu cần compare.

---

## 502.27 — Snapshot

Replica có thể tạo snapshot durable.

---

## 502.28 — Snapshot metadata

Snapshot phải có:

```text id="w3m8x1"
state_version
log_position
schema_version
checksum
```

---

## 502.29 — Snapshot installation

Follower có thể install snapshot thay vì replay toàn bộ log.

---

## 502.30 — Snapshot atomicity

Snapshot phải atomic theo protocol semantics.

---

## 502.31 — WAL integration

455 WAL có thể làm durability layer.

---

## 502.32 — Flush semantics

Received ≠ durable.

---

## 502.33 — Fsync semantics

Durability guarantees phụ thuộc storage/platform semantics.

---

## 502.34 — Replication acknowledgment

Ack phải specify:

```text id="x6m2q8"
received
persisted
replicated
committed
applied
```

---

## 502.35 — Leader election

Leader election phải chống stale leader.

---

## 502.36 — Epoch

Mỗi authority period có epoch/term.

---

## 502.37 — Stale leader

Old leader commands phải bị fencing/rejected khi epoch stale.

---

## 502.38 — Quorum authority

Authority-sensitive writes cần protocol-defined quorum.

---

## 502.39 — Membership changes

Membership change phải itself be coordinated.

---

## 502.40 — Joint configuration

Replication protocols có thể dùng joint configuration để chuyển membership an toàn.

---

## 502.41 — Learner

New replica có thể join as learner trước khi trở thành voting member.

---

## 502.42 — Catch-up

Replica catch-up có thể dùng log hoặc snapshot.

---

## 502.43 — Lag

Replica lag phải observable.

---

## 502.44 — Stale reads

Read API phải cho phép caller biết consistency/staleness policy.

---

## 502.45 — Read-from-replica

Read replica selection explicit.

---

## 502.46 — Local read

Local read có thể nhanh nhưng không mặc định latest committed state.

---

## 502.47 — Leader read

Leader read có consistency semantics riêng.

---

## 502.48 — Lease read

Lease-based read phải expose clock assumptions.

---

## 502.49 — Follower read

Follower read cần stale-read policy.

---

## 502.50 — Conflict resolution

Multi-writer systems cần explicit conflict resolver.

---

## 502.51 — CRDT

CRDT có thể là library abstraction.

---

## 502.52 — CRDT semantics

CRDT operations/state must satisfy type-specific convergence requirements.

---

## 502.53 — Tombstone

Delete trong replicated storage có thể cần tombstones.

---

## 502.54 — Garbage collection

Tombstone GC chỉ được thực hiện khi causal/replication safety cho phép.

---

## 502.55 — Compaction

Log compaction phải preserve required recovery state.

---

## 502.56 — Snapshot + compaction

Snapshot và log truncation phải atomic theo recovery contract.

---

## 502.57 — Crash recovery

Recovery sequence:

```text id="r5m8x2"
Open
 ↓
Validate metadata
 ↓
Recover WAL/log
 ↓
Restore snapshot
 ↓
Replay committed entries
 ↓
Ready
```

---

## 502.58 — Torn write

Storage layer phải detect corrupted/torn records khi possible.

---

## 502.59 — Checksums

Replicated log entries/snapshots có integrity checksum.

---

## 502.60 — Corruption

Corruption phải chuyển thành explicit recovery/error state.

---

## 502.61 — Byzantine behavior

Byzantine fault tolerance không mặc định.

---

## 502.62 — Byzantine protocol

BFT là optional specialized library.

---

## 502.63 — Trust model

501/490 trust boundaries áp dụng cho replicas.

---

## 502.64 — Authentication

Replica communication phải authenticate khi threat model yêu cầu.

---

## 502.65 — Authorization

Replica identity không tự cấp write authority.

---

## 502.66 — Encryption

TLS or secure transport 454 được dùng khi cần.

---

## 502.67 — Key rotation

Replica security supports key rotation.

---

## 502.68 — Secret data

Replication log có thể chứa sensitive data; logging/debugging phải redact theo policy.

---

## 502.69 — Backpressure

Replication pipeline phải có bounded resource policy.

---

## 502.70 — Queue limits

Replication queues có thể bounded.

---

## 502.71 — Snapshot limits

Snapshot generation phải có memory/disk limits.

---

## 502.72 — Catch-up throttling

Replica catch-up có thể throttle để không starve foreground workload.

---

## 502.73 — Priority

Replication priority policy explicit.

---

## 502.74 — Backoff

Failed replica reconnect có bounded backoff/jitter.

---

## 502.75 — Network partition

Partition phải tạo trạng thái rõ ràng, không giả vờ thành normal operation.

---

## 502.76 — Availability tradeoff

Protocol documentation phải nêu behavior khi quorum unavailable.

---

## 502.77 — Safety vs liveness

Safety và liveness phải được mô tả riêng.

---

## 502.78 — No false durability

API không được báo durable khi chỉ buffered.

---

## 502.79 — No false commit

API không được báo committed khi protocol chưa commit.

---

## 502.80 — No false consistency

API không được claim stronger consistency than implementation provides.

---

## 502.81 — Transaction integration

455 transactions có thể được replicated.

---

## 502.82 — Transaction boundary

Local DB transaction và distributed transaction phải phân biệt.

---

## 502.83 — Two-phase commit

2PC có thể là library protocol.

---

## 502.84 — 2PC limitation

2PC không được mô tả như consensus hoặc universal fault tolerance.

---

## 502.85 — Consensus integration

Consensus có thể decide ordered commands.

---

## 502.86 — State machine replication

Consensus + deterministic state machine tạo replicated service.

---

## 502.87 — Service API

500 service endpoint có thể map tới replicated state machine.

---

## 502.88 — Schema evolution

499 schema version phải được replicate/migrate safely.

---

## 502.89 — Snapshot schema

Snapshot phải ghi schema version.

---

## 502.90 — Rolling upgrade

Cluster có thể upgrade từng node theo compatibility policy.

---

## 502.91 — Mixed versions

Mixed-version cluster phải có supported compatibility window.

---

## 502.92 — Protocol version

Replication protocol version độc lập application schema version.

---

## 502.93 — State migration

State migration phải có explicit migration plan.

---

## 502.94 — Backup

Distributed backup có thể combine snapshots + log.

---

## 502.95 — Restore

Restore phải verify checksums/schema/protocol compatibility.

---

## 502.96 — Disaster recovery

Disaster recovery policy là application/storage policy.

---

## 502.97 — AI introspection

AI queries:

```text id="u7m3x8"
replica_state()
commit_index()
applied_index()
lag()
leader()
term()
quorum()
snapshot()
recovery()
consistency()
```

---

## 502.98 — Testing

Phải test:

- crash;
- partition;
- leader failure;
- stale leader;
- duplicate;
- reorder;
- delayed messages;
- corruption;
- snapshot restore;
- membership change;
- rolling upgrade.

---

## 502.99 — Deterministic simulation

Consensus/replication phải có deterministic simulator/fault injection framework.

---

## 502.100 — Hard invariants

1. Replica là copy logical state.
2. Replica có identity.
3. Replica role explicit.
4. Replicated log có position.
5. Log epoch/term được hỗ trợ.
6. Commit index khác applied index.
7. Applied khác durable position.
8. State machine được hỗ trợ.
9. Replicated command phải deterministic khi yêu cầu.
10. Nondeterministic external state không implicit.
11. Command result semantics explicit.
12. Linearization semantics explicit.
13. Linearizability không mặc định.
14. Sequential consistency được hỗ trợ.
15. Eventual consistency được hỗ trợ.
16. Causal consistency được hỗ trợ.
17. Session consistency có thể hỗ trợ.
18. API phải document consistency.
19. Quorum read explicit.
20. Quorum write explicit.
21. Read repair là policy.
22. Anti-entropy được hỗ trợ.
23. Merkle reconciliation có thể hỗ trợ.
24. Snapshot được hỗ trợ.
25. Snapshot có version.
26. Snapshot có log position.
27. Snapshot có checksum.
28. Snapshot installation có semantics rõ.
29. Snapshot phải atomic theo contract.
30. WAL 455 được tích hợp.
31. Received khác persisted.
32. Persisted khác replicated.
33. Replicated khác committed.
34. Committed khác applied.
35. Leader election có stale-leader protection.
36. Epoch/term được sử dụng.
37. Stale leader bị fencing.
38. Authority-sensitive write có quorum policy.
39. Membership changes được coordinate.
40. Joint configuration có thể hỗ trợ.
41. Learner role được hỗ trợ.
42. Replica catch-up được hỗ trợ.
43. Replica lag observable.
44. Stale reads explicit.
45. Replica read selection explicit.
46. Local read không tự claim latest.
47. Leader read semantics explicit.
48. Lease read expose clock assumptions.
49. Follower read expose staleness.
50. Multi-writer conflict resolution explicit.
51. CRDT có thể là library.
52. CRDT convergence semantics phải explicit.
53. Replicated deletes có thể cần tombstones.
54. Tombstone GC phải causal-safe.
55. Log compaction giữ recovery state.
56. Snapshot + truncation atomic.
57. Crash recovery có deterministic phases.
58. Torn/corrupt writes được detect khi có thể.
59. Checksums được hỗ trợ.
60. Corruption tạo explicit error/recovery state.
61. Byzantine tolerance không mặc định.
62. BFT là optional library.
63. Replica trust boundary explicit.
64. Replica authentication được hỗ trợ.
65. Authentication khác authorization.
66. Secure transport được hỗ trợ.
67. Key rotation được hỗ trợ.
68. Sensitive replication data được bảo vệ.
69. Replication backpressure được hỗ trợ.
70. Replication queues có limits.
71. Snapshot resource limits được hỗ trợ.
72. Catch-up có thể throttle.
73. Replication priority explicit.
74. Reconnect backoff bounded.
75. Network partition có explicit state.
76. Quorum-unavailable behavior được document.
77. Safety và liveness được phân biệt.
78. Không false durability.
79. Không false commit.
80. Không false consistency.
81. Local transaction khác distributed transaction.
82. 2PC là library protocol.
83. 2PC không phải consensus.
84. Consensus có thể order commands.
85. State-machine replication được hỗ trợ.
86. Service 500 có thể expose replicated state.
87. Schema evolution 499 được tích hợp.
88. Snapshot schema version được ghi.
89. Rolling upgrade được hỗ trợ.
90. Mixed-version policy explicit.
91. Replication protocol version độc lập schema version.
92. State migration explicit.
93. Snapshot + log backup được hỗ trợ.
94. Restore phải verify integrity.
95. Disaster recovery là policy.
96. AI distributed-state introspection được hỗ trợ.
97. Fault-injection testing bắt buộc.
98. Deterministic simulation được hỗ trợ.
99. Performance đo riêng replication/consensus/storage/network overhead.
100. **Axiom distributed storage phải có khả năng xây replicated durable services mà không đánh tráo các khái niệm `received`, `persisted`, `replicated`, `committed`, `applied`; consistency, quorum, leader authority, durability, recovery và failure semantics phải được công khai trong contract thay vì ẩn sau một API "magical".**

**BOOTSTRAP-502 hoàn tất / LOCKED.**

---

# TIẾN ĐỘ

```text
BOOTSTRAP-497  Build Scripts / Build Plugins             LOCKED
BOOTSTRAP-498  Resource / Asset Pipeline                 LOCKED
BOOTSTRAP-499  Data Model / Serialization / Schema       LOCKED
BOOTSTRAP-500  IPC / RPC / Service                       LOCKED
BOOTSTRAP-501  Distributed Foundation                   LOCKED
BOOTSTRAP-502  Distributed Storage / Replication        LOCKED
```

**Task kế tiếp: `BOOTSTRAP-503 — AI/ML COMPUTING FOUNDATION, TENSOR, AUTODIFF, MODEL GRAPH, DEVICE MEMORY & NATIVE ACCELERATOR ABSTRACTION`.**