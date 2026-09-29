Tiếp tục với **BOOTSTRAP-628**, xây tầng dữ liệu phân tán trên 627 nhưng giữ rõ ranh giới giữa storage cục bộ, replication, consistency và các mô hình eventual/CRDT.

:::writing{variant="document" id="31685" title="BOOTSTRAP-628 — Native Distributed Data, Replicated Storage, Consistency Models, Distributed Cache, CRDT Boundary, Event Log & Data Replication Runtime 5.0"}
# BOOTSTRAP-628 — Native Distributed Data, Replicated Storage, Consistency Models, Distributed Cache, CRDT Boundary, Event Log & Data Replication Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Distributed Data / Replication Runtime  
**Depends on:** BOOTSTRAP-600 → 627

---

# 1. Purpose

BOOTSTRAP-628 defines the Axiom runtime foundation for distributed data.

It provides standardized boundaries for:

- replicated data;
- distributed key/value storage;
- replicated logs;
- distributed caches;
- consistency models;
- replication streams;
- conflict detection;
- conflict resolution;
- CRDT providers;
- event logs;
- change feeds;
- snapshots;
- data synchronization;
- offline replicas;
- anti-entropy;
- version vectors;
- causal metadata;
- quorum reads/writes;
- read repair;
- hinted handoff;
- compaction;
- tombstones;
- distributed garbage collection of obsolete replicas;
- replica placement;
- replication policies.

It builds on:

```text id="fcz7o6"
611 Storage
612 Serialization
613 Package/CAS
627 Distributed Coordination
626 Networking
610 Cryptography
606 Resource Governance
```

---

# 2. Core Principle

Axiom must never hide the consistency model.

Every distributed data API must make its consistency semantics explicit.

For example:

```text id="6j2x8a"
Eventual
Causal
Session
Quorum
Linearizable
```

are different guarantees.

The runtime must not expose all of them through one ambiguous `get()` operation without a declared policy.

---

# 3. Layering

```text id="k86h7u"
Application
    │
    ▼
Distributed Data
    │
    ├── Replicated Store
    ├── Distributed Cache
    ├── Event Log
    ├── Change Feed
    ├── CRDT
    └── Replication
    │
    ▼
628
    │
    ├── 627 Coordination
    ├── 612 Serialization
    ├── 611 Storage
    └── 626 Networking
```

---

# 4. Non-Goals

628 does not mandate:

- SQL;
- a relational database;
- NoSQL;
- a particular database engine;
- a particular CRDT;
- a particular consensus algorithm;
- distributed transactions;
- globally synchronized clocks;
- exactly-once delivery.

---

# 5. Local vs Distributed Storage

Axiom maintains a hard distinction:

```text id="n1s7jj"
LocalStore
```

versus:

```text id="5h2k31"
ReplicatedStore
```

A local store does not become distributed merely because an application sends copies elsewhere.

---

# 6. Store Model

```text id="d8d9kn"
DistributedStore {
    open()
    get()
    put()
    delete()
    scan()
    snapshot()
}
```

---

# 7. Store Identity

Each store has:

```text id="z5l24a"
StoreId
Namespace
SchemaFingerprint
ReplicationPolicy
ConsistencyPolicy
```

---

# 8. Replica Identity

A replica is identified by:

```text id="4kmt7n"
StoreId
ReplicaId
Generation
```

---

# 9. Replica State

```text id="9f6y7d"
Joining
CatchingUp
Serving
Degraded
ReadOnly
Leaving
Offline
Failed
```

---

# 10. Replication

Replication copies durable/logical state between replicas.

---

# 11. Replication Modes

Supported boundaries:

```text id="c29h5u"
PrimaryReplica
MultiPrimary
Leaderless
ReadReplica
AsyncReplica
SynchronousReplica
```

---

# 12. Primary Replica

A single authoritative writer can be selected through 627.

---

# 13. Multi-Primary

Multiple replicas may accept writes.

Conflict resolution becomes mandatory.

---

# 14. Leaderless

Reads/writes can use configurable replica quorums.

---

# 15. Async Replication

Writes may become visible locally before remote replicas acknowledge them.

---

# 16. Synchronous Replication

A write may require a configured replica quorum before commit.

---

# 17. Replication Policy

```text id="0egzob"
ReplicationPolicy {
    factor
    write_quorum
    read_quorum
    placement
    consistency
}
```

---

# 18. Replication Factor

Replication factor determines desired number of replicas.

---

# 19. Placement

Placement can consider:

- node;
- rack;
- zone;
- region;
- hardware class.

---

# 20. Failure Domains

Replica placement should avoid putting every replica in the same declared failure domain.

---

# 21. Quorum

For a replica set of `N`:

```text id="a9z9r7"
R + W > N
```

may provide overlap semantics where the underlying protocol supports them.

---

# 22. Quorum Warning

Quorum arithmetic alone does not guarantee linearizability.

---

# 23. Linearizability

Requires an implementation/protocol that actually establishes a single valid ordering.

---

# 24. Read Consistency

```text id="spk78m"
ReadConsistency {
    Local
    Session
    Causal
    Quorum
    Linearizable
    Eventual
}
```

---

# 25. Write Consistency

```text id="g2e9q4"
WriteConsistency {
    Local
    Async
    Quorum
    Linearizable
}
```

where supported.

---

# 26. Session Consistency

Session state can track:

```text id="7q4r6u"
ConsistencyToken
```

to ensure read-your-writes behavior.

---

# 27. Causal Consistency

Operations can carry causal metadata.

---

# 28. Version Vector

```text id="s7e0hj"
VersionVector {
    node
    counter
}
```

with multiple entries.

---

# 29. Vector Comparison

Two versions can be:

```text id="czwz82"
Before
After
Equal
Concurrent
```

---

# 30. Conflict

Concurrent versions are not automatically errors.

---

# 31. Conflict Object

```text id="6c3a5b"
Conflict<T> {
    versions
    metadata
}
```

---

# 32. Conflict Resolver

```text id="y2oz9f"
resolve(conflict) -> T
```

---

# 33. Last-Write-Wins

LWW may be offered as an explicit policy.

It must not be the implicit universal conflict strategy.

---

# 34. LWW Timestamp

LWW requires a clearly documented timestamp source.

---

# 35. Clock Safety

Physical timestamps may be skewed.

Applications requiring causal correctness should use causal metadata.

---

# 36. Deterministic Tie Breaker

If LWW uses timestamps, ties must have deterministic ordering.

---

# 37. Tombstone

Deletion in eventually replicated storage may create a tombstone.

---

# 38. Tombstone Lifetime

Tombstones cannot be removed until the replication protocol knows that obsolete replicas can no longer resurrect deleted data.

---

# 39. Anti-Entropy

```text id="w5m9nj"
AntiEntropy {
    synchronize()
    compare()
    repair()
}
```

---

# 40. Merkle Tree

Replication providers may use Merkle trees to efficiently identify differing ranges.

---

# 41. Content Hash

612/610 hashes identify data versions where appropriate.

---

# 42. Repair

Repair must preserve declared consistency semantics.

---

# 43. Read Repair

A read may detect divergence and schedule repair.

---

# 44. Hinted Handoff

Leaderless stores may temporarily store writes on substitute nodes.

---

# 45. Handoff Metadata

Hints contain:

```text id="c1kgjv"
original_replica
target_replica
version
expiration
```

---

# 46. Handoff Expiration

Expired hints are safely discarded only according to replication guarantees.

---

# 47. Replication Stream

```text id="j35xmi"
ReplicationStream {
    subscribe()
    checkpoint()
    resume()
}
```

---

# 48. Change Sequence

Changes have a monotonic sequence within a replication domain.

---

# 49. Change Record

```text id="v7v3lj"
Change {
    key
    operation
    version
    causal_context
    payload
}
```

---

# 50. Change Types

```text id="g30m7j"
Insert
Update
Delete
Merge
Metadata
```

---

# 51. Change Feed

Applications may subscribe to committed changes.

---

# 52. Change Feed Semantics

Delivery semantics must be declared:

```text id="9t7csm"
AtLeastOnce
AtMostOnce
BestEffort
```

---

# 53. Exactly Once

Exactly-once change-feed processing is not assumed.

---

# 54. Consumer Offset

```text id="5b2tkw"
ConsumerOffset {
    stream_id
    partition
    sequence
}
```

---

# 55. Offset Persistence

Offsets may use 611/612.

---

# 56. Event Log

```text id="1jyg1c"
EventLog {
    append()
    read()
    subscribe()
    checkpoint()
}
```

---

# 57. Event Identity

Each event has:

```text id="g0d08f"
EventId
StreamId
Sequence
SchemaFingerprint
```

---

# 58. Event Ordering

Ordering is guaranteed within a defined stream/partition scope.

---

# 59. Global Ordering

Global ordering is optional and generally more expensive.

It must never be implied by per-stream ordering.

---

# 60. Event Partitioning

Events may be partitioned by key.

---

# 61. Partition

```text id="8o9l5f"
PartitionId
```

defines a replication/ordering domain.

---

# 62. Partition Assignment

Partition ownership can use 627 coordination.

---

# 63. Partition Rebalancing

Rebalancing must preserve declared ordering semantics.

---

# 64. Consumer Group

```text id="4x1a3f"
ConsumerGroup {
    members
    assignments
    offsets
}
```

---

# 65. Consumer Group Coordination

Uses 627 leases/coordination.

---

# 66. Consumer Failure

Expired consumer lease causes reassignment.

---

# 67. Duplicate Processing

A reassigned partition may replay records.

Consumers must be idempotent.

---

# 68. Event Replay

Applications can replay historical events where retained.

---

# 69. Replay Isolation

Replay should not accidentally invoke external side effects.

---

# 70. Event Handler

Applications should distinguish:

```text id="6z9h5d"
replay mode
live mode
```

---

# 71. Snapshot + Event Log

A stateful application can recover:

```text id="r0a9i3"
snapshot
+
events after snapshot
```

---

# 72. Snapshot Metadata

Snapshot contains:

```text id="1o4t9y"
event_sequence
schema_version
state_fingerprint
```

---

# 73. Event Schema

Event payloads use 612.

---

# 74. Schema Evolution

Old events must remain readable or have an explicit migration strategy.

---

# 75. Event Version

Each event type has a schema version.

---

# 76. Event Compatibility

Backward compatibility follows 612 rules.

---

# 77. Event Upcasting

Optional transformation:

```text id="cbr6we"
old_event → current_event
```

---

# 78. Compaction

Event logs may support compaction.

---

# 79. Compaction Safety

Compaction must not remove events still required by registered consumers.

---

# 80. Retention

Retention policies may use:

```text id="q4ovc0"
time
size
sequence
consumer requirements
```

---

# 81. Distributed Cache

```text id="z4j6mo"
DistributedCache {
    get()
    put()
    remove()
    invalidate()
}
```

---

# 82. Cache Semantics

Cache is not authoritative storage unless explicitly declared.

---

# 83. Cache Failure

Cache failure should not imply application data loss.

---

# 84. Cache Consistency

Possible:

```text id="c3y5f7"
Local
Eventual
Session
Coherent
```

where provider supports it.

---

# 85. Cache TTL

Entries can have expiration.

---

# 86. Cache Eviction

Possible policies:

```text id="z0bcb4"
LRU
LFU
TTL
Size
Cost
```

---

# 87. Cache Stampede

Runtime may provide request coalescing.

---

# 88. Cache Coalescing

Concurrent requests for the same key can share one load operation.

---

# 89. Negative Cache

Optional caching of known misses.

---

# 90. Negative Cache TTL

Must be separately configurable.

---

# 91. Cache Invalidation

Invalidation messages may be delivered asynchronously.

---

# 92. Stale Data

Consumers must be able to declare whether stale values are acceptable.

---

# 93. Cache Admission

Large objects may be rejected from cache based on resource policy.

---

# 94. Cache Resource Limits

606 controls:

```text id="31u9yu"
entries
bytes
requests
network traffic
CPU
```

---

# 95. CRDT Boundary

Axiom provides an abstraction boundary for CRDTs.

---

# 96. CRDT Types

Possible provider families:

```text id="9r0h0x"
GCounter
PNCounter
LWWRegister
MVRegister
ORSet
ORMap
LWWMap
```

---

# 97. CRDT Contract

A CRDT must document:

- merge operation;
- convergence assumptions;
- metadata cost;
- deletion semantics.

---

# 98. Merge

A valid state-based CRDT requires a merge operation satisfying its declared convergence properties.

---

# 99. State-Based CRDT

```text id="8cy6w0"
merge(a, b)
```

must be deterministic.

---

# 100. Operation-Based CRDT

Operation-based providers define:

```text id="9gq1v5"
operation
causal delivery requirement
deduplication
```

---

# 101. Delta CRDT

Delta-state synchronization may reduce bandwidth.

---

# 102. CRDT Metadata

Metadata can become larger than application data.

Runtime must account for this explicitly.

---

# 103. CRDT Tombstones

CRDT deletion metadata requires safe reclamation rules.

---

# 104. CRDT Garbage Collection

Distributed metadata can only be reclaimed after the provider establishes required causal stability.

---

# 105. Causal Stability

A provider may expose:

```text id="p9i3od"
CausalStableVersion
```

---

# 106. No Blind Metadata Deletion

Applications cannot arbitrarily delete causal metadata.

---

# 107. CRDT Security

CRDT merge does not bypass authorization.

---

# 108. CRDT Resource Limits

Malicious replication cannot create unlimited metadata.

---

# 109. Conflict Resolver

Custom merge functions must be deterministic where replicas require convergence.

---

# 110. Non-Deterministic Merge

Non-deterministic merges are allowed only when the application explicitly accepts divergence.

---

# 111. Replica Synchronization

```text id="t7m24j"
ReplicaSync {
    pull()
    push()
    reconcile()
}
```

---

# 112. Sync Session

A sync session contains:

```text id="2mxv4j"
source
target
protocol
checkpoint
security_context
```

---

# 113. Incremental Sync

Sync should transfer only missing changes where possible.

---

# 114. Full Sync

Full snapshot transfer is available for bootstrap/recovery.

---

# 115. Resume

Interrupted replication resumes from a durable checkpoint.

---

# 116. Checksum

Transferred chunks are integrity checked.

---

# 117. Encryption

Replication traffic uses 610.

---

# 118. Authentication

Replica identities use 603/610.

---

# 119. Authorization

Only authorized replicas can participate.

---

# 120. Replica Revocation

Revoked replicas must stop receiving authoritative data.

---

# 121. Offline Replica

A replica can operate offline according to its consistency policy.

---

# 122. Offline Writes

Offline writes require:

```text id="4q2w9z"
conflict policy
version metadata
reconciliation policy
```

---

# 123. Reconnection

Offline replica:

```text id="g0q5vy"
authenticate
exchange versions
detect conflicts
merge
publish
```

---

# 124. Sync Conflict

Conflict can be:

```text id="6lh6tt"
resolved
deferred
rejected
```

---

# 125. Manual Conflict

Applications can surface unresolved conflicts to 619/622 UI.

---

# 126. Conflict Storage

Unresolved conflicts can be persisted as structured objects.

---

# 127. Conflict History

Conflict resolution may retain audit information.

---

# 128. Data Ownership

A distributed store declares its authority model:

```text id="8d7vqt"
single_authority
multi_authority
derived
cache
```

---

# 129. Derived Data

Derived replicas can be rebuilt from authoritative events/data.

---

# 130. Materialized View

```text id="2gk0aa"
MaterializedView {
    refresh()
    query()
}
```

---

# 131. View Consistency

Views expose their lag/version.

---

# 132. Replication Lag

Metrics include:

```text id="m3h8wd"
bytes
events
time
sequence
```

---

# 133. Stale Read Indicator

APIs may expose:

```text id="1xqk5v"
served_version
source_version
staleness
```

---

# 134. Read Preference

Possible:

```text id="m3t5u9"
Primary
Nearest
Local
Replica
Any
```

---

# 135. Read Routing

Routing uses 626 service discovery and 627 topology.

---

# 136. Write Routing

Writes follow store authority semantics.

---

# 137. Write Forwarding

A replica may forward writes to the current authority.

---

# 138. Write Fencing

Primary changes can use 627 fence tokens.

---

# 139. Stale Primary

A stale primary must be rejected by fencing-aware storage.

---

# 140. Replication Epoch

Each replication configuration has an epoch.

---

# 141. Replica Epoch

Replicas reject stale replication streams.

---

# 142. Snapshot Transfer

Large snapshots can use 611 streaming and 613 compression.

---

# 143. Chunking

Snapshots should be transferred in bounded chunks.

---

# 144. Parallel Transfer

Independent snapshot chunks may transfer concurrently.

---

# 145. Resource Governor

606 controls snapshot bandwidth/CPU/memory.

---

# 146. Compression

613 compression may reduce replication traffic.

---

# 147. Deduplication

613 CAS can avoid retransmitting identical immutable chunks.

---

# 148. Encryption at Rest

611/610 provide storage encryption boundaries.

---

# 149. Key Rotation

Replicated data encryption can rotate keys without changing logical records.

---

# 150. Secret Data

Sensitive replicated fields should use 601/610 secret handling.

---

# 151. Diagnostics

602 receives replication events.

---

# 152. Metrics

Required metrics:

```text id="9s6w1o"
replication_lag
conflicts
repair_rate
bytes_sent
bytes_received
write_quorum_latency
read_quorum_latency
snapshot_progress
```

---

# 153. Logging

Replication logs must avoid application payloads by default.

---

# 154. Trace

Replication operations can carry trace context.

---

# 155. Backpressure

Replication cannot consume unlimited application resources.

---

# 156. Replication Priority

Applications may assign:

```text id="o9h4x0"
critical
normal
background
```

priority.

---

# 157. Fairness

One replication stream must not starve local application traffic.

---

# 158. Network Isolation

Replication may use dedicated resource groups.

---

# 159. Storage Isolation

Replication writes may have separate 606 quotas.

---

# 160. Compaction

Replicated storage may compact:

- old versions;
- tombstones;
- log segments;
- metadata.

---

# 161. Compaction Safety

Compaction must respect:

- active readers;
- replication checkpoints;
- causal stability;
- snapshots;
- consumer offsets.

---

# 162. Version Retention

Store must retain enough versions for its declared consistency model.

---

# 163. MVCC Boundary

Optional MVCC provider:

```text id="j2j1zv"
VersionedRecord
SnapshotRead
```

---

# 164. Snapshot Isolation

If provided, snapshot isolation semantics must be explicit.

---

# 165. Serializable

Serializable distributed transactions are not mandatory.

---

# 166. Transaction Boundary

Local 612/611 transactions remain distinct from distributed transactions.

---

# 167. Distributed Transaction

A separate higher-level provider may implement:

```text id="x4w5j7"
2PC
3PC
Saga
TCC
```

but 628 does not require them.

---

# 168. Eventual Workflow

Applications can use:

```text id="u8p6h9"
event
projection
retry
compensation
```

instead of distributed transactions.

---

# 169. Outbox

628 may provide an outbox abstraction.

---

# 170. Outbox Record

```text id="15b34x"
OutboxEntry {
    id
    aggregate
    event
    status
}
```

---

# 171. Outbox Atomicity

Outbox storage and local business-state transaction can share 611/612 transactional boundaries.

---

# 172. Publisher

A background publisher sends outbox events.

---

# 173. Inbox

Consumers can persist processed event IDs.

---

# 174. Idempotent Consumer

Inbox deduplication is explicit.

---

# 175. Delivery

Outbox publication is at-least-once by default.

---

# 176. Duplicate Events

Consumers must tolerate duplicates.

---

# 177. Event Ordering

Outbox ordering is scoped by aggregate/partition where configured.

---

# 178. Event Replay

Outbox events can feed projections.

---

# 179. Materialized Projection

Projection state can be rebuilt.

---

# 180. Projection Checkpoint

Projection records:

```text id="pfv9a2"
last_applied_sequence
schema_version
```

---

# 181. Projection Failure

Failed projection processing retries without losing committed source events.

---

# 182. Dead Letter

Repeatedly failing events may enter an explicit dead-letter stream.

---

# 183. Dead Letter Policy

No automatic deletion of failed events.

---

# 184. Event Ordering and Parallelism

Partitions provide parallelism while preserving per-partition ordering.

---

# 185. Partition Key

Application explicitly defines partition key.

---

# 186. Hot Partition

Diagnostics detect disproportionate partition load.

---

# 187. Repartitioning

Changing partition strategy requires migration semantics.

---

# 188. Consistent Hashing

Optional provider can use consistent hashing for distributed cache/storage placement.

---

# 189. Rebalancing

Rebalancing must avoid uncontrolled simultaneous data movement.

---

# 190. Migration Throttle

606 limits migration bandwidth/CPU/storage.

---

# 191. Replica Repair

Repair runs at controlled priority.

---

# 192. Repair Safety

Repair cannot overwrite newer authoritative data.

---

# 193. Compare-and-Set

Distributed store may expose:

```text id="p4z3nc"
compare_and_set(expected_version, value)
```

---

# 194. Conditional Write

Conditions may use:

```text id="5k5m1f"
version
etag
fence_token
predicate
```

---

# 195. Atomic Compare

Provider must document whether conditional writes are linearizable.

---

# 196. Batch

Distributed batch operations are atomic only within declared scope.

---

# 197. Batch Scope

Possible:

```text id="9u6fbb"
single_key
single_partition
single_replica
transaction
```

---

# 198. Multi-Key Atomicity

Never implied unless explicitly provided.

---

# 199. Scan

Distributed scans can be:

```text id="b0r8qg"
snapshot
eventual
partition-local
```

---

# 200. Pagination

Cursor-based pagination is preferred over offset pagination for changing distributed datasets.

---

# 201. Cursor

Cursor contains:

```text id="3xqzqt"
partition
position
snapshot/version
```

---

# 202. Cursor Security

Cursors should be opaque to external clients where required.

---

# 203. Query Layer

628 does not define SQL.

Higher-level database modules may expose SQL/query languages.

---

# 204. Index

Distributed indexes are higher-level providers.

---

# 205. Search

Full-text/vector search is outside the core distributed data layer.

---

# 206. AI Data

AI/vector stores can build on:

```text id="u2l1fp"
distributed store
event log
replication
CAS
```

without being hardcoded into 628.

---

# 207. Blob Data

Large binary objects use 611/613.

---

# 208. Metadata

Large-object metadata can be replicated through 628.

---

# 209. Content Addressing

Immutable content can use 613 object IDs.

---

# 210. Immutable Data

Immutable replicated objects simplify conflict handling.

---

# 211. Mutable Data

Mutable objects require explicit consistency/version policy.

---

# 212. Versioned Object

```text id="nq3i5r"
ObjectVersion {
    version
    causal_context
    payload
}
```

---

# 213. Merge

Version merge can return:

```text id="iy9b84"
Merged
Conflict
Rejected
```

---

# 214. Conflict Audit

Merge decisions may be logged.

---

# 215. Security

Replicas must not receive data beyond their authorization.

---

# 216. Field-Level Authorization

Optional provider may filter fields before replication.

---

# 217. Encryption

Sensitive fields can use application-level encryption.

---

# 218. Key Availability

Replica must possess required decryption authority before serving protected data.

---

# 219. Revocation

Revoked replicas cannot automatically decrypt newly encrypted data.

---

# 220. Multi-Tenant Storage

Tenant identity can be part of store namespace.

---

# 221. Tenant Isolation

Resource and capability limits can be applied per tenant.

---

# 222. Tenant Data

Cross-tenant reads require explicit authorization.

---

# 223. Namespace Isolation

Namespaces are not security boundaries unless enforced by 603.

---

# 224. Audit

Data-management operations can emit audit records.

---

# 225. Data Deletion

Distributed deletion semantics must document:

```text id="k0v8jx"
logical deletion
physical reclamation
replica propagation
backup retention
```

---

# 226. Secure Deletion

Physical secure deletion remains storage/provider dependent.

---

# 227. Retention

Retention policies are explicit.

---

# 228. Legal Hold Boundary

Higher-level compliance systems may prevent deletion.

---

# 229. Garbage Collection

628 uses the term reclamation for distributed data cleanup to avoid confusion with language GC.

---

# 230. Reclamation

Reclaim only data proven obsolete under the provider's consistency model.

---

# 231. Snapshot Retention

Snapshots pin required data.

---

# 232. Replica Retention

Offline replicas may prevent safe reclamation.

---

# 233. Offline Replica Policy

Operators can explicitly declare a maximum offline interval.

---

# 234. Stale Replica

A replica exceeding allowed staleness may be forced to full resync.

---

# 235. Full Resync

Full resync can discard local derived replica state.

---

# 236. Authoritative State

Authoritative data must never be discarded merely because a replica is stale.

---

# 237. Disaster Recovery

Recovery can rebuild a replica from snapshot + change log.

---

# 238. Recovery Verification

Recovered state is checked against schema/hash metadata.

---

# 239. Checksum

Every persisted replicated segment has integrity metadata.

---

# 240. Corruption

Corrupt replica data enters degraded/recovery state.

---

# 241. Automatic Repair

Repair is allowed only if a trusted authoritative source exists.

---

# 242. No Peer Blind Repair

Two divergent peers must not blindly overwrite one another without version/authority rules.

---

# 243. Replication Authentication

Every replication connection is authenticated.

---

# 244. Replication Authorization

Replication permission is distinct from application read permission where required.

---

# 245. Provider Isolation

Experimental replication providers can run through 623 + 604/605.

---

# 246. Plugin Safety

Plugins cannot automatically access all replicated stores.

---

# 247. Script Safety

Scripts receive only declared data capabilities.

---

# 248. Configuration

601 controls:

```text id="o6qv4b"
replication
consistency
retention
cache
repair
resource limits
security
```

---

# 249. State

600 can checkpoint application-level replication progress.

---

# 250. Scheduler

607 schedules:

- replication;
- repair;
- compaction;
- event publishing;
- cache refresh.

---

# 251. Synchronization

608 provides local concurrency.

---

# 252. Network

626 provides service/RPC transport.

---

# 253. Storage

611 provides local durability.

---

# 254. Serialization

612 provides wire/storage schema.

---

# 255. Compression

613 reduces snapshot/replication storage and bandwidth.

---

# 256. Consensus

627 provides leader/quorum/lease coordination.

---

# 257. Diagnostics

602 receives replication and consistency telemetry.

---

# 258. Resource Governor

606 limits distributed data activity.

---

# 259. Package

613 packages provider implementations.

---

# 260. Compiler Integration

Compiler recognizes:

```text id="9g8jif"
@replicated
@consistency
@partition
@versioned
@event
@crdt
@materialized
```

metadata.

---

# 261. Generated Schema

Compiler emits:

```text id="0jz3f4"
.axdata
.axreplica
.axevent
.axcrdt
```

---

# 262. Static Analysis

Compiler may detect:

```text id="o9f6td"
non-deterministic merge
missing conflict policy
unsafe retry
unsupported serialization
unbounded replicated object
```

---

# 263. No Mandatory Reflection

All common paths use generated metadata.

---

# 264. Dead Stripping

Unused:

```text id="j5q0by"
CRDT
event log
cache
replication
consensus adapters
```

are removable.

---

# 265. API Example

```text id="l5t7y8"
let store =
    await DistributedStore.open("users")?

let user =
    await store.get(
        key,
        ReadConsistency.Session
    )?
```

---

# 266. Conditional Write

```text id="09kq5p"
await store.compare_and_set(
    key,
    expected_version,
    new_value
)?
```

---

# 267. Event Log

```text id="0k2lq5"
let stream =
    await events.open("orders")?

await stream.append(order_created)?
```

---

# 268. Subscription

```text id="4g6j6e"
let subscription =
    await events.subscribe("orders", checkpoint)?

while let event = await subscription.next() {
    process(event)
}
```

---

# 269. CRDT

```text id="zq7f1d"
let counter =
    GCounter.new()

counter.increment(1)

await replica.merge(counter)?
```

---

# 270. Cache

```text id="9v4w4c"
if let value = await cache.get(key)? {
    return value
}

let value = await database.load(key)?

await cache.put(key, value, ttl)?

return value
```

---

# 271. Architecture Invariants

1. Distributed data always declares consistency.
2. Local storage remains distinct.
3. Replica identity includes generation.
4. Membership comes from 627.
5. Network comes from 626/609.
6. Serialization comes from 612.
7. Durability comes from 611.
8. Compression comes from 613.
9. Security comes from 603/610.
10. Resource governance comes from 606.
11. Scheduling comes from 607.
12. Synchronization comes from 608.
13. Supervision comes from 605.
14. Diagnostics come from 602.
15. Quorum does not automatically imply linearizability.
16. Exactly-once is never silently assumed.
17. Retries may duplicate writes.
18. Request identity is required for duplicate suppression.
19. Conflict resolution is explicit.
20. LWW is not the universal conflict strategy.
21. Tombstones require safe retention.
22. Causal metadata requires safe reclamation.
23. Offline replicas can become stale.
24. Stale replicas can require full resync.
25. Replica repair cannot overwrite newer state blindly.
26. Distributed locks are not sufficient without fencing for external resources.
27. Consensus remains a provider boundary.
28. Distributed transactions remain optional.
29. Event logs have scoped ordering.
30. Consumer delivery is not automatically exactly-once.
31. Event replay must be distinguishable from live execution.
32. Cache is not authoritative by default.
33. Cache failure does not imply data loss.
34. Snapshot consistency is explicit.
35. Compaction respects consumers and replicas.
36. Resource usage is bounded.
37. Replication cannot starve local workloads.
38. Security authorization remains separate from membership.
39. Namespace is not automatically a security boundary.
40. Field-level replication is optional.
41. No mandatory SQL engine.
42. No mandatory database.
43. No mandatory CRDT.
44. No mandatory distributed transaction.
45. No mandatory external coordinator.
46. No mandatory cloud infrastructure.
47. No mandatory GC.
48. No hidden distributed synchronization.
49. APIs remain struct/function based.
50. Minimal local applications do not link distributed-data machinery.

---

# 272. Acceptance Criteria

### Storage
1. distributed store.
2. replica identity.
3. replica lifecycle.
4. primary replication.
5. multi-primary boundary.
6. leaderless boundary.
7. async replication.
8. synchronous replication.
9. replication factor.
10. placement policy.

### Consistency
11. local read.
12. session consistency.
13. causal consistency.
14. quorum read.
15. linearizable boundary.
16. eventual consistency.
17. consistency tokens.
18. version vectors.
19. causal metadata.
20. stale-read metadata.

### Replication
21. replication stream.
22. checkpoints.
23. resume.
24. anti-entropy.
25. Merkle repair.
26. read repair.
27. hinted handoff.
28. replica lag.
29. snapshot transfer.
30. full resync.

### Conflict
31. concurrent version detection.
32. conflict object.
33. resolver.
34. LWW explicit policy.
35. deterministic tie-breaking.
36. tombstone.
37. tombstone retention.
38. causal stability.
39. metadata reclamation.
40. offline conflict.

### Events
41. event log.
42. event identity.
43. partition.
44. per-partition ordering.
45. consumer group.
46. offset.
47. replay.
48. snapshot + replay.
49. retention.
50. compaction.
51. dead-letter stream.
52. outbox.
53. inbox.
54. idempotent consumer.

### CRDT
55. CRDT provider.
56. state-based CRDT.
57. op-based boundary.
58. delta-state boundary.
59. merge.
60. convergence metadata.
61. CRDT deletion.
62. CRDT metadata reclamation.

### Cache
63. distributed cache.
64. TTL.
65. eviction.
66. invalidation.
67. request coalescing.
68. negative cache.
69. stale policy.
70. cache quotas.

### Security
71. replica authentication.
72. replica authorization.
73. mTLS.
74. capability integration.
75. credential protection.
76. field-level security boundary.
77. audit.
78. encryption boundary.
79. key rotation.
80. tenant isolation.

### Recovery
81. crash recovery.
82. snapshot restore.
83. corruption detection.
84. degraded replica.
85. automatic repair.
86. partition recovery.
87. offline replica.
88. full resync.
89. stale replica detection.
90. retention safety.

### Runtime
91. scheduler integration.
92. synchronization.
93. resource governance.
94. diagnostics.
95. configuration.
96. supervision.
97. package/provider integration.
98. compiler metadata.
99. dead stripping.
100. AI-readable schema.

### Testing
101. partition.
102. message loss.
103. duplication.
104. reordering.
105. delay.
106. concurrent writes.
107. conflict.
108. clock skew.
109. stale replica.
110. repair.
111. crash.
112. corruption.
113. replay.
114. compaction.
115. CRDT convergence.
116. cache stampede.
117. resource exhaustion.
118. security.
119. fuzzing.
120. deterministic simulation.

---

# 273. Final Architecture

```text id="5n8yq7"
                        APPLICATION
                            │
                            ▼
                  ┌──────────────────┐
                  │       628        │
                  │ Distributed Data │
                  ├──────────────────┤
                  │ Store             │
                  │ Replication       │
                  │ Consistency       │
                  │ Conflict          │
                  │ CRDT              │
                  │ Event Log         │
                  │ Change Feed       │
                  │ Cache             │
                  │ Snapshot          │
                  │ Repair            │
                  └────────┬─────────┘
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          627 Coord      612 Data      611 Storage
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                         626
                           │
                           ▼
                         609
                           │
                         Network
```

---

# 274. Profile Architecture

## AXDATA-LOCAL

```text id="a8q8dl"
611 + 612
```

No distributed runtime.

## AXDATA-REPLICA

```text id="8n3bso"
local store
+
replication
```

## AXDATA-EVENT

```text id="lq4y0k"
event log
+
change feed
+
outbox/inbox
```

## AXDATA-CRDT

```text id="r3u8y9"
CRDT
+
causal metadata
+
replication
```

## AXDATA-CACHE

```text id="gq5y2d"
distributed cache
+
service discovery
```

## AXDATA-CONSISTENT

```text id="0k2qj3"
627 quorum
+
replicated state
+
linearizable provider
```

## AXDATA-FULL

```text id="b9y3f8"
replication
+
events
+
cache
+
CRDT
+
consistency
+
repair
```

Unused components remain removable.

---

# 275. Final Design Decision

Axiom's distributed-data architecture deliberately separates:

```text
611 = local durable storage
612 = structured data
627 = distributed coordination
628 = distributed data
626 = network services
```

This produces an important property:

```text
local application
      │
      └── local storage only

distributed cache
      │
      └── 628 cache

event-driven system
      │
      └── 628 event log

eventually consistent system
      │
      └── 628 replication/CRDT

strongly consistent service
      │
      └── 627 consensus
             +
          628 replicated state
```

Axiom therefore does not force one universal distributed-storage model onto every application.

# 276. Task Completion

**BOOTSTRAP-628 — COMPLETE**

**Next queued task: BOOTSTRAP-629 — Native Distributed Workflow, Jobs, Scheduling, Orchestration, Durable Tasks, Sagas, Compensation & Long-Running Process Runtime 5.0**
:::