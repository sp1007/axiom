Tiếp tục với **BOOTSTRAP-627**, tập trung vào nền tảng distributed systems nhưng giữ consensus/cluster ở đúng boundary, không biến Axiom core thành một hệ thống phân tán bắt buộc.

:::writing{variant="document" id="58314" title="BOOTSTRAP-627 — Native Distributed Systems Runtime, Cluster Coordination, Membership, Leases, Leader Election, Distributed Locks & Consensus Boundary 5.0"}
# BOOTSTRAP-627 — Native Distributed Systems Runtime, Cluster Coordination, Membership, Leases, Leader Election, Distributed Locks & Consensus Boundary 5.0

**Status:** SPECIFIED  
**Layer:** Distributed Systems / Coordination Runtime  
**Depends on:** BOOTSTRAP-600 → 626

---

# 1. Purpose

BOOTSTRAP-627 defines the Axiom runtime boundary for applications that operate across multiple processes, machines, nodes, availability zones, or administrative domains.

It provides common primitives for:

- node identity;
- cluster membership;
- service membership;
- health state;
- leases;
- heartbeats;
- failure detection;
- leader election;
- distributed locks;
- fencing;
- distributed coordination;
- replicated state-machine boundaries;
- consensus-provider abstraction;
- quorum;
- cluster configuration;
- membership epochs;
- topology;
- distributed clocks;
- logical clocks;
- causal metadata;
- distributed request identity;
- cluster diagnostics;
- deterministic testing.

The design deliberately distinguishes **coordination primitives** from **distributed application semantics**.

---

# 2. Core Principle

627 must not pretend that distributed systems can provide the same guarantees as local memory.

The runtime explicitly models:

```text
latency
partial failure
message loss
reordering
duplication
partition
node crash
clock skew
restart
stale membership
```

---

# 3. Layering

```text
Application
    │
    ▼
Distributed Application
    │
    ▼
627 Distributed Runtime
    ├── Membership
    ├── Failure Detection
    ├── Lease
    ├── Election
    ├── Lock
    ├── Coordination
    ├── Cluster State
    └── Consensus Boundary
    │
    ▼
626 RPC / Service Networking
    │
    ▼
609 Network
```

---

# 4. Non-Goals

627 does not provide a mandatory:

- database;
- distributed filesystem;
- service mesh;
- cloud control plane;
- Kubernetes replacement;
- consensus algorithm implementation in every build;
- distributed transaction manager;
- global shared-memory abstraction;
- exactly-once distributed execution.

---

# 5. Fundamental Rule

No distributed primitive may silently convert an uncertain network event into a certainty.

For example:

```text
timeout != proof of node death
```

and:

```text
connection lost != proof that remote operation failed
```

---

# 6. Node Model

```text
Node {
    node_id
    generation
    incarnation
    endpoint_set
    capabilities
    labels
    metadata
}
```

---

# 7. NodeId

`NodeId` is globally unique within the configured cluster domain.

---

# 8. Node Generation

Every node process instance has a generation.

```text
NodeId + Generation
```

uniquely identifies a running incarnation.

---

# 9. Restart

Restart increments generation/incarnation.

Old messages cannot automatically apply to the new generation.

---

# 10. ClusterId

A cluster has a stable:

```text
ClusterId
```

distinct from its current membership.

---

# 11. Cluster Epoch

Membership-changing operations advance:

```text
ClusterEpoch
```

where supported.

---

# 12. Epoch Rule

Operations carrying an older epoch may be rejected as stale.

---

# 13. Membership

```text
Membership {
    join()
    leave()
    members()
    watch()
}
```

---

# 14. Membership States

```text
Joining
Alive
Suspect
Leaving
Left
Failed
Unknown
```

---

# 15. Membership Semantics

Membership is a view, not absolute truth.

---

# 16. Failure Detector

```text
FailureDetector {
    observe()
    suspect()
    status()
}
```

---

# 17. Failure Detector Inputs

May include:

- heartbeat;
- RPC response;
- local process state;
- transport failures;
- lease expiration;
- indirect probes.

---

# 18. Failure Detector Output

```text
Healthy
Suspected
Unreachable
Failed
Unknown
```

---

# 19. Suspicion

Suspicion must remain distinguishable from confirmed failure.

---

# 20. Phi Accrual

An optional statistical failure detector may expose a suspicion score.

It is never treated as absolute proof.

---

# 21. Heartbeat

Heartbeats contain:

```text
node_id
generation
membership_epoch
sequence
timestamp
```

---

# 22. Heartbeat Frequency

Configurable and bounded by 606 resource budgets.

---

# 23. Heartbeat Transport

Uses 626 service/network transport.

---

# 24. Failure Detection

Failure detector must tolerate transient packet loss.

---

# 25. Network Partition

A partition can produce:

```text
Node A believes B unreachable
Node B believes A unreachable
```

without either node being crashed.

---

# 26. Split Brain

Systems requiring a single active leader must use fencing/quorum/consensus.

---

# 27. Quorum

For an odd-sized voting set:

```text
quorum = floor(N / 2) + 1
```

---

# 28. Quorum Safety

A minority partition must not independently claim exclusive leadership when quorum is required.

---

# 29. Quorum Availability

A system requiring quorum may become unavailable during a partition.

This is an intentional safety tradeoff.

---

# 30. Lease

```text
Lease {
    lease_id
    holder
    expiration
    epoch
}
```

---

# 31. Lease Semantics

A lease grants authority only while its validity conditions remain satisfied.

---

# 32. Lease Renewal

```text
renew()
```

must happen before expiration.

---

# 33. Lease Expiration

After expiration, holder must stop relying on the lease.

---

# 34. Clock Safety

Wall-clock time alone must not be used as proof of remote lease expiration unless the protocol explicitly provides clock-bound guarantees.

---

# 35. Lease Provider

Lease implementations may use:

```text
ConsensusStore
Database
ExternalCoordinator
StaticAuthority
```

---

# 36. Fencing Token

Every exclusive lease may produce a monotonically increasing:

```text
FenceToken
```

---

# 37. Fencing

Resource owners should reject operations carrying an older fencing token.

---

# 38. Example

```text
Node A owns token 41
Node A becomes partitioned

Node B obtains token 42

Storage accepts:
    token >= 42

Storage rejects:
    token 41
```

---

# 39. Distributed Lock

```text
DistributedLock {
    acquire()
    renew()
    release()
}
```

---

# 40. Lock Identity

A lock has:

```text
LockName
LeaseId
FenceToken
Owner
Epoch
```

---

# 41. Lock Safety

A distributed lock is not equivalent to a local mutex.

---

# 42. Lock Expiration

Expiration can occur without explicit release.

---

# 43. Lock Usage

Critical resources should use fencing rather than trusting lock ownership alone.

---

# 44. Lock Fairness

Distributed lock fairness is optional and must not compromise safety.

---

# 45. Reentrant Lock

Reentrant distributed locks are not required by the core runtime.

---

# 46. Leader Election

```text
LeaderElection {
    campaign()
    resign()
    leader()
    watch()
}
```

---

# 47. Leader Identity

Leader identity includes:

```text
NodeId
Generation
Epoch
FenceToken
```

---

# 48. Leadership

Leadership is valid only within its protocol-defined epoch/term.

---

# 49. Stale Leader

A node that loses leadership must stop performing leader-exclusive operations.

---

# 50. Fencing Leader

Leader-controlled external resources should validate the current fencing token.

---

# 51. Election Algorithms

627 defines an abstraction.

Possible providers:

```text
Raft
Paxos-family
external consensus service
database-backed election
platform coordinator
```

---

# 52. No Mandatory Algorithm

Axiom applications do not depend on a single consensus algorithm at the language/runtime level.

---

# 53. Consensus Boundary

Consensus provider exposes:

```text
propose()
read()
watch()
term()
commit_index()
```

where supported.

---

# 54. Replicated State Machine

Applications may build:

```text
StateMachine {
    apply(command)
    snapshot()
    restore()
}
```

above the consensus provider.

---

# 55. Determinism

A replicated state machine must produce deterministic results for identical committed commands.

---

# 56. Forbidden State

Consensus-applied state must not depend on:

- local wall clock;
- random numbers;
- local filesystem state;
- network timing;

unless explicitly modeled as replicated input.

---

# 57. Snapshot

Consensus providers may create snapshots.

---

# 58. Snapshot Version

Snapshots contain:

```text
state_machine_version
log_index
term
schema_fingerprint
```

---

# 59. Log

Replicated logs consist of ordered entries.

---

# 60. Log Entry

```text
LogEntry {
    index
    term
    command
    schema
}
```

---

# 61. Commit

Only committed entries become authoritative state.

---

# 62. Apply

Application state is updated only according to provider commit semantics.

---

# 63. Read Consistency

Distributed reads must explicitly declare consistency.

---

# 64. Consistency Modes

Possible:

```text
Local
Leader
Quorum
Linearizable
BoundedStale
Eventual
```

subject to provider support.

---

# 65. No Fake Linearizability

The API must not label a read linearizable unless the provider actually supplies the required guarantee.

---

# 66. Eventual Consistency

Applications may explicitly select eventual-consistency models.

---

# 67. Read-Your-Writes

Optional session-level consistency token:

```text
ConsistencyToken
```

---

# 68. Causal Metadata

Optional causal metadata may use logical clocks.

---

# 69. Lamport Clock

```text
LamportClock {
    value
    tick()
    observe()
}
```

---

# 70. Vector Clock

Optional:

```text
VectorClock
```

for systems requiring richer causality.

---

# 71. Hybrid Logical Clock

Optional HLC provider may combine physical and logical time.

---

# 72. Physical Time

627 never assumes synchronized physical clocks without explicit bounds.

---

# 73. Distributed Timestamp

Distributed timestamps carry their clock domain/version.

---

# 74. Request Identity

Distributed calls use:

```text
RequestId
TraceId
AttemptId
```

---

# 75. Duplicate Detection

Applications may use request IDs to detect duplicate operations.

---

# 76. Exactly-Once Boundary

Duplicate suppression is application/storage-specific.

627 does not claim universal exactly-once execution.

---

# 77. Idempotent Command

Distributed commands should declare whether they are idempotent.

---

# 78. Retry

Retries must preserve:

```text
RequestId
```

while changing:

```text
AttemptId
```

---

# 79. Retry Budget

Distributed clients inherit 626 retry-budget semantics.

---

# 80. Membership Watch

Applications can subscribe to membership changes.

---

# 81. Watch Semantics

Watch streams may experience:

- duplicate events;
- reconnect;
- compaction;
- missed events.

Consumers must handle resynchronization.

---

# 82. Snapshot + Watch

Preferred pattern:

```text
snapshot()
+
watch(from_version)
```

---

# 83. Watch Version

Each membership/state update has a monotonic version where provider semantics permit.

---

# 84. Resync

When history is unavailable:

```text
watch → resync snapshot → watch
```

---

# 85. Cluster Configuration

Cluster configuration contains:

```text
ClusterId
members
roles
protocol_version
epoch
security_policy
```

---

# 86. Configuration Changes

Membership/config changes should be transactional where consensus is available.

---

# 87. Membership Roles

Possible roles:

```text
Voter
Observer
Learner
Worker
Witness
Client
```

---

# 88. Observer

Observer does not participate in quorum unless explicitly configured.

---

# 89. Learner

Learner receives replicated state without voting authority.

---

# 90. Witness

Witness may participate in quorum without holding full application state, depending on provider.

---

# 91. Node Labels

Nodes may expose labels:

```text
region
zone
rack
device
platform
capacity
```

---

# 92. Labels

Labels are descriptive metadata, not automatically trusted authorization attributes.

---

# 93. Capability

Distributed capability authorization remains controlled by 603.

---

# 94. Node Trust

Membership does not imply full application trust.

---

# 95. Secure Membership

Node authentication uses:

```text
610 TLS
mTLS
signed identity
platform identity
```

---

# 96. Join

Joining a cluster requires explicit admission policy.

---

# 97. Join Token

Join credentials are treated as secrets.

---

# 98. Join Bootstrap

A node may obtain:

```text
cluster identity
membership configuration
trust roots
protocol version
```

---

# 99. Join Verification

Cluster verifies node identity before admission.

---

# 100. Rejoin

A restarted node joins with a new generation.

---

# 101. Removed Node

Removed nodes must not automatically regain authority.

---

# 102. Revocation

Membership revocation integrates with 603/610 trust policy.

---

# 103. Cluster Key

Optional cluster-wide keys must use 610 key-management mechanisms.

---

# 104. Encryption

Inter-node communication should use TLS/mTLS or equivalent authenticated transport.

---

# 105. Message Authentication

Consensus providers may use authenticated channels.

---

# 106. Replay Protection

Distributed coordination messages carry:

```text
epoch
term
sequence
generation
```

where applicable.

---

# 107. Stale Message

Messages from old generations/epochs/terms must be rejected.

---

# 108. Resource Limits

606 controls:

```text
membership size
connections
heartbeats
watchers
replicated-log memory
snapshot size
coordination tasks
```

---

# 109. Watcher Limits

Unbounded watch subscriptions are forbidden.

---

# 110. Log Limits

Consensus providers must bound retained log memory/storage.

---

# 111. Snapshot Compaction

Providers may compact committed logs after snapshots.

---

# 112. Storage

Consensus persistence can use 611/612.

---

# 113. Durable Log

Durable consensus providers must define:

```text
append durability
flush semantics
recovery semantics
```

---

# 114. Crash Recovery

After restart:

```text
load persistent state
validate checksum
recover log
restore snapshot
rejoin
```

---

# 115. Corruption

Corrupt consensus state must not silently become authoritative.

---

# 116. Quarantine

Corrupt nodes may enter a recovery/quarantine state.

---

# 117. Supervision

605 can restart failed coordination services.

---

# 118. No Automatic Split-Brain Recovery

Recovery policies must respect quorum and fencing.

---

# 119. Cluster Service

```text
Cluster {
    id()
    membership()
    health()
    topology()
}
```

---

# 120. Coordination Service

```text
Coordinator {
    lease()
    lock()
    election()
    watch()
}
```

---

# 121. Cluster Client

```text
ClusterClient {
    connect()
    endpoint()
    health()
}
```

---

# 122. Distributed Task

A distributed task is represented as an application-level object.

627 provides coordination primitives, not a mandatory distributed task scheduler.

---

# 123. Distributed Job Queue

Can be built using:

```text
RPC
lease
fencing
persistent storage
```

but is not core.

---

# 124. Work Claim

Work claims should carry:

```text
TaskId
LeaseId
FenceToken
AttemptId
```

---

# 125. Task Completion

Completion must be idempotent or deduplicated.

---

# 126. Leader Work

Leader-only work must be protected by epoch/fencing.

---

# 127. Leader Handoff

Leadership transfer should be explicit where provider supports it.

---

# 128. Graceful Leadership Transfer

Outgoing leader should:

```text
stop new work
finish safe work
persist state
transfer leadership
```

---

# 129. Election Storm

Repeated election failures must use bounded backoff.

---

# 130. Clock Drift

Clock drift must not create false lease guarantees.

---

# 131. Lease Duration

Lease duration must account for:

```text
network latency
scheduler delay
clock uncertainty
GC-independent runtime pauses
```

Axiom itself has no mandatory GC, but provider pauses still matter.

---

# 132. Monotonic Clock

Local lease timers should use monotonic time where possible.

---

# 133. Wall Clock

Wall clock is for timestamps, not elapsed-time measurement.

---

# 134. Quorum Loss

Consensus-backed services should enter:

```text
ReadOnly
Unavailable
```

according to policy rather than inventing authority.

---

# 135. Minority Behavior

Minority nodes may:

- serve stale reads if permitted;
- expose health;
- reconnect;
- refuse writes.

---

# 136. Network Partition

Applications must be able to distinguish:

```text
No quorum
No route
Remote unavailable
Local failure
```

where observable.

---

# 137. Partition Healing

After reconnection:

```text
authenticate
exchange epoch
synchronize membership
synchronize state
resume
```

---

# 138. State Conflict

Consensus-backed state resolves according to consensus.

Eventually consistent state requires application-defined merge rules.

---

# 139. CRDT Boundary

CRDTs are optional higher-level data structures.

627 may provide interfaces but does not require one CRDT model.

---

# 140. Merge Function

Eventual state may define:

```text
merge(a, b) -> state
```

which must satisfy the declared convergence properties.

---

# 141. Distributed Cache

627 may expose cache-coordination hooks.

It does not mandate coherent distributed cache semantics.

---

# 142. Cache Invalidation

Invalidation is explicitly best-effort unless backed by a consistency protocol.

---

# 143. Service Membership

Service membership may differ from cluster membership.

---

# 144. Multiple Clusters

One process can participate in multiple coordination domains.

---

# 145. Isolation

Each cluster has independent:

```text
ClusterId
epoch
membership
credentials
policies
```

---

# 146. Namespace

Coordination objects use:

```text
ClusterId + Namespace + ObjectId
```

---

# 147. Namespaces

Examples:

```text
locks/
leases/
leaders/
services/
config/
jobs/
```

---

# 148. Naming

Names use canonical UTF-8 identifiers.

---

# 149. Path Safety

Names cannot escape namespace boundaries.

---

# 150. Metadata

Coordination objects may contain typed metadata.

---

# 151. TTL

Object TTL is supported where provider semantics allow.

---

# 152. TTL Safety

Expiration must not be treated as a universal proof of failure.

---

# 153. Watch Notifications

Notifications may be delivered asynchronously.

---

# 154. Notification Ordering

Ordering is guaranteed only within the documented scope.

---

# 155. Delivery

Default watch semantics:

```text
at-least-once notification
```

unless provider specifies otherwise.

---

# 156. Deduplication

Consumers should use object/version IDs.

---

# 157. Snapshot Consistency

Cluster snapshots identify their consistency level.

---

# 158. Snapshot Export

Snapshots can be persisted through 611/612.

---

# 159. Snapshot Encryption

Sensitive snapshots may use 610-backed encryption.

---

# 160. Snapshot Packaging

Snapshots may use 613 compression/package mechanisms.

---

# 161. Cluster Backup

Backup is outside the coordination core but has provider hooks.

---

# 162. Disaster Recovery

DR workflows are higher-level application/deployment concerns.

---

# 163. Region

A cluster may have topology labels for regions/zones.

---

# 164. Locality

Endpoint selection can prefer local nodes.

---

# 165. Failure Domains

Cluster policy may distinguish:

```text
node
rack
zone
region
```

---

# 166. Quorum Placement

Consensus providers can enforce placement constraints.

---

# 167. Availability

627 does not promise availability under arbitrary partitions.

---

# 168. Consistency vs Availability

Applications explicitly choose provider semantics.

---

# 169. Distributed Lock Warning

API documentation must clearly distinguish:

```text
lock acquisition
resource fencing
resource correctness
```

---

# 170. Fencing Resource

Storage/database/device providers can implement:

```text
validate_fence(token)
```

---

# 171. Fence Token Monotonicity

Fence tokens must never decrease within a coordination domain.

---

# 172. Fence Persistence

Provider persists token state when required for safety.

---

# 173. Leadership Token

Leadership can expose a fencing token.

---

# 174. Service Gateway

626 gateway can consume 627 discovery/leadership data.

---

# 175. Load Balancing

Service endpoint selection can consume cluster membership.

---

# 176. Health

605 service health feeds 627 membership where appropriate.

---

# 177. Security Policy

603 controls cluster-management operations.

---

# 178. Administrative Operations

Operations such as:

```text
add_node
remove_node
change_quorum
force_leader
```

require elevated capabilities.

---

# 179. No Self-Elevation

A node cannot grant itself cluster-admin authority.

---

# 180. Audit

Administrative operations generate 602 audit events.

---

# 181. Diagnostics

Metrics include:

```text
leader_changes
membership_changes
election_count
quorum_state
lease_renewals
lease_expirations
lock_wait
watch_lag
replication_lag
commit_index
```

---

# 182. Trace

Coordination operations can create trace spans.

---

# 183. Failure Reason

Diagnostics distinguish:

```text
timeout
partition
authentication failure
quorum loss
storage failure
protocol mismatch
stale epoch
```

---

# 184. Redaction

Cluster credentials and secrets are excluded from diagnostics.

---

# 185. Configuration

601 configures:

```text
heartbeat
election
lease
quorum
timeouts
limits
security
```

---

# 186. Configuration Reload

Safety-sensitive coordination configuration may require restart/reconfiguration protocol rather than immediate mutation.

---

# 187. Immutable Runtime Snapshot

Active coordination policy uses immutable configuration snapshots.

---

# 188. Resource Governance

606 accounts:

```text
network traffic
coordination CPU
storage
memory
watchers
connections
```

---

# 189. Scheduler

607 handles:

- heartbeat tasks;
- retry tasks;
- watch streams;
- election timers;
- lease renewal.

---

# 190. Synchronization

608 handles local coordination state.

---

# 191. Network

626 provides RPC/service transport.

---

# 192. Storage

611 provides persistent logs/snapshots.

---

# 193. Serialization

612 defines coordination message schemas.

---

# 194. Cryptography

610 protects cluster communication and identities.

---

# 195. Package

613 packages cluster-provider modules.

---

# 196. Plugin

623 allows alternate coordination providers.

---

# 197. Script

624 may inspect cluster state under capability restrictions.

---

# 198. GUI

619/622 may display cluster topology and health.

---

# 199. Compiler Metadata

Compiler can emit:

```text
.axcluster
.axcoord
.axconsensus
```

---

# 200. Provider ABI

Consensus providers expose a stable provider interface.

---

# 201. Provider Isolation

Experimental consensus providers can run out-of-process through 604/605.

---

# 202. In-Process Provider

Trusted provider may run in-process for performance.

---

# 203. Provider Failure

Provider crash must not silently produce valid leadership state.

---

# 204. Provider Generation

Provider handles use generation-safe identity.

---

# 205. Hot Replacement

Consensus-provider replacement requires explicit migration protocol.

---

# 206. No Blind Hot Reload

A live consensus engine cannot be hot-reloaded merely because the binary changed.

---

# 207. State Migration

Migration requires:

```text
snapshot
schema migration
verification
activation
```

---

# 208. Schema Compatibility

State schema changes follow 612.

---

# 209. Consensus Schema

Consensus log entries must remain decodable across rolling upgrades.

---

# 210. Rolling Upgrade

Cluster upgrades should support:

```text
old + new compatible versions
```

where protocol compatibility exists.

---

# 211. Protocol Version

Every coordination protocol has explicit versioning.

---

# 212. Version Negotiation

Nodes negotiate supported versions before participating.

---

# 213. Incompatible Node

An incompatible node remains non-voting/non-serving until compatible.

---

# 214. Downgrade

Downgrade requires explicit compatibility validation.

---

# 215. Cluster Upgrade

Upgrade sequencing must preserve quorum.

---

# 216. Upgrade Failure

605 can restart failed nodes, but cannot violate quorum safety.

---

# 217. Emergency Removal

Force-removing a node requires administrative capability and explicit confirmation semantics at the API level.

---

# 218. No Automatic Force Removal

Network failure alone must not automatically reconfigure consensus membership.

---

# 219. Membership Change

Consensus-backed membership changes must use provider-defined safe reconfiguration.

---

# 220. Joint Configuration

Providers may use joint consensus or equivalent mechanisms.

---

# 221. Observer Promotion

Promotion to voter must be explicit and safe.

---

# 222. Bootstrap

Cluster bootstrap must prevent accidental creation of multiple clusters with the same identity.

---

# 223. Bootstrap Token

Bootstrap authority is single-use or explicitly bounded.

---

# 224. Cluster Identity

Cluster identity is cryptographically bound where provider supports it.

---

# 225. Split-Brain Prevention

Cluster identity + membership + quorum + fencing form the primary safety boundary.

---

# 226. Distributed Event

Optional event stream:

```text
ClusterEvent
MembershipEvent
LeadershipEvent
LeaseEvent
```

---

# 227. Event Schema

All events are versioned.

---

# 228. Event Persistence

Persistence is provider-specific.

---

# 229. Event Ordering

Ordering guarantees are explicitly documented.

---

# 230. Cluster Clock

627 may expose a logical distributed clock but never claim global exact time.

---

# 231. Monotonic Sequence

Every coordination domain should expose monotonic sequence numbers where useful.

---

# 232. Epoch

Epoch changes invalidate stale operations.

---

# 233. Term

Consensus term is distinct from cluster epoch.

---

# 234. Generation

Node generation is distinct from both.

---

# 235. Fence Token

Fence token is distinct from all three.

---

# 236. Identity Model

```text
ClusterId
    +
NodeId
    +
Generation
    +
Epoch
    +
Term
    +
FenceToken
```

must never be conflated.

---

# 237. Distributed Error

```text
DistributedError {
    category
    node
    generation
    epoch
    retryable
}
```

---

# 238. Retryability

Retryability is explicitly classified.

---

# 239. Stale Operation

Returns:

```text
StaleEpoch
StaleGeneration
StaleTerm
FenceRejected
```

where appropriate.

---

# 240. Network Error

Transport errors remain distinct from coordination errors.

---

# 241. Application Error

Business errors remain distinct from distributed-runtime errors.

---

# 242. API Example — Lease

```text
let lease =
    await coordinator.lease("leader", duration)?

defer lease.release()

await lease.run_while_valid(fn() async {
    do_leader_work()
})
```

---

# 243. API Example — Lock

```text
let lock =
    await coordinator.lock("resource")?

let token = lock.fence_token()

await storage.write(resource, value, token)?

await lock.release()
```

---

# 244. API Example — Election

```text
let election =
    await cluster.election("primary")?

await election.campaign()

if election.is_leader() {
    run_primary_service()
}
```

---

# 245. API Example — Membership

```text
let members =
    await cluster.membership.snapshot()?

for member in members {
    if member.is_alive() {
        connect(member)
    }
}
```

---

# 246. API Example — Consensus

```text
let result =
    await consensus.propose(command)?
```

The application receives the provider's documented commit semantics.

---

# 247. Deterministic Testing

627 provides fake:

```text
Cluster
Clock
Network
Membership
LeaseStore
Consensus
Storage
```

providers.

---

# 248. Partition Test

Tests must simulate:

```text
A ↔ B disconnected
```

without killing either process.

---

# 249. Clock Test

Tests must simulate clock skew.

---

# 250. Delay Test

Tests must inject arbitrary bounded/unbounded network delay.

---

# 251. Duplication Test

Messages can be duplicated.

---

# 252. Reordering Test

Messages can arrive out of order.

---

# 253. Loss Test

Messages can be dropped.

---

# 254. Restart Test

Node generation changes after restart.

---

# 255. Stale Message Test

Old-generation messages must be rejected.

---

# 256. Split-Brain Test

Partitioned nodes must not both become authoritative leaders when quorum/fencing is required.

---

# 257. Lease Test

Expired lease must not continue to authorize protected operations.

---

# 258. Fence Test

Older fencing token must be rejected by a fencing-aware resource.

---

# 259. Election Test

Repeated election failures must converge according to provider semantics.

---

# 260. Quorum Test

Loss of quorum must produce the documented state.

---

# 261. Recovery Test

Partition healing must trigger resynchronization.

---

# 262. Snapshot Test

Snapshot restore must reproduce equivalent state.

---

# 263. Log Corruption Test

Corrupt entries must be detected.

---

# 264. Membership Test

Join/leave/rejoin must preserve generation semantics.

---

# 265. Upgrade Test

Rolling upgrade must preserve quorum.

---

# 266. Security Test

Unauthorized membership mutation must fail.

---

# 267. Credential Test

Expired/revoked node credentials must be rejected.

---

# 268. Resource Test

Watcher/connection/log quotas must be enforced.

---

# 269. Fuzz Test

Coordination message parsers must be fuzzed.

---

# 270. Model Testing

Consensus-provider implementations should support model checking where practical.

---

# 271. Performance

Targets:

```text
low coordination overhead
bounded heartbeat cost
bounded watcher memory
efficient membership lookup
low allocation
no global hot-path lock
```

---

# 272. Scalability

Membership implementation should support:

- small clusters;
- medium clusters;
- large membership sets.

Provider-specific scaling limits must be explicit.

---

# 273. Small Cluster

A 3-node consensus cluster is a valid common configuration.

---

# 274. Large Cluster

Large clusters may use hierarchical/service-specific coordination rather than one global consensus group.

---

# 275. Hierarchical Coordination

627 allows:

```text
global cluster
    ↓
regional group
    ↓
service group
```

without requiring global consensus for every operation.

---

# 276. Avoid Global Consensus

Applications should not place unrelated state in one consensus group merely because the runtime allows it.

---

# 277. Coordination Scope

Every coordination object declares its scope.

---

# 278. Failure Domain

Every critical service can declare failure-domain assumptions.

---

# 279. Availability Policy

Availability requirements remain application-specific.

---

# 280. Consensus Provider Profiles

Possible profiles:

```text
AXCOORD-LOCAL
AXCOORD-LEASE
AXCOORD-ELECTION
AXCOORD-RAFT
AXCOORD-EXTERNAL
AXCOORD-FULL
```

---

# 281. AXCOORD-LOCAL

Single-process coordination.

---

# 282. AXCOORD-LEASE

Lease/lock abstraction without full replicated state.

---

# 283. AXCOORD-ELECTION

Leader election only.

---

# 284. AXCOORD-RAFT

Optional full consensus provider.

---

# 285. AXCOORD-EXTERNAL

Adapter for external coordination systems.

---

# 286. AXCOORD-FULL

Complete distributed runtime.

---

# 287. Binary Size

Applications must not link consensus code unless required.

---

# 288. Runtime Dependency

No external coordinator is mandatory for ordinary Axiom programs.

---

# 289. Offline Operation

Local applications continue to work without a cluster.

---

# 290. Embedded

Embedded targets may implement a minimal membership provider.

---

# 291. WASM

WASM may consume host-provided distributed coordination APIs.

---

# 292. Mobile

Mobile applications should not assume continuous cluster membership.

---

# 293. Background Constraints

Mobile providers must handle suspended processes and stale leases.

---

# 294. Desktop

Desktop applications can participate as non-voting clients or workers.

---

# 295. Server

Server deployments can use full consensus providers.

---

# 296. Security Profile

Sensitive cluster administration requires elevated capability.

---

# 297. Developer Mode

Developer/test clusters may use simplified authentication only under explicit development configuration.

---

# 298. Production Mode

Production profiles can require:

```text
mTLS
signed membership
strict quorum
fencing
audit
```

---

# 299. Audit

Administrative events:

```text
cluster_created
node_joined
node_removed
leader_changed
lease_granted
lock_granted
membership_changed
policy_changed
```

---

# 300. Privacy

Diagnostics must avoid exposing:

- credentials;
- private keys;
- tokens;
- sensitive application payloads.

---

# 301. AI Metadata

Compiler/runtime metadata must describe:

```text
cluster
provider
consistency
leadership
lease
lock
fencing
```

semantics so AI tooling can reason about distributed guarantees.

---

# 302. Generated Documentation

`.axcluster` metadata can generate:

- topology;
- node roles;
- coordination objects;
- protocol versions;
- required capabilities.

---

# 303. Compiler Diagnostics

Compiler can warn when:

```text
distributed lock
```

is used without a fencing-aware resource where the declared API requires fencing.

---

# 304. Static Analysis

Potential diagnostics:

```text
leader-only operation without leadership check
lease use without renewal handling
retry of non-idempotent operation
unchecked stale generation
unbounded distributed watch
```

---

# 305. Runtime Assertions

Debug profiles may assert:

```text
valid epoch
valid generation
valid lease
valid fence token
```

---

# 306. Production Assertions

Safety checks remain active where required for correctness.

---

# 307. Memory Safety

No distributed object may expose raw unmanaged pointer semantics.

---

# 308. Handle Safety

Cluster/lease/lock/election handles use generation-safe IDs.

---

# 309. Lifetime

Closing a coordinator invalidates outstanding local handles.

---

# 310. No GC Dependency

627 does not require garbage collection.

---

# 311. Cleanup

Distributed handles support deterministic cleanup.

---

# 312. Async

All remote coordination operations are async-first.

---

# 313. Cancellation

Cancellation of a local operation does not automatically cancel an already committed remote operation.

---

# 314. Remote Cancellation

Where supported, cancellation is sent explicitly.

---

# 315. Commit Boundary

Applications must distinguish:

```text
request sent
request accepted
request committed
request applied
```

---

# 316. Network Disconnect

A disconnected client cannot infer which commit stage occurred unless the protocol provides confirmation.

---

# 317. Retry After Unknown Result

Application must use idempotency/request identity or query status before retrying unsafe operations.

---

# 318. Distributed Transaction Boundary

No hidden two-phase commit.

---

# 319. External Transaction

A higher-level transaction coordinator may be implemented as a separate module.

---

# 320. Final Invariants

1. Distributed state is not shared memory.
2. Network timeout is not proof of failure.
3. Membership is a view.
4. Suspicion is not failure proof.
5. Node generation identifies process incarnation.
6. Cluster epoch identifies membership/configuration generation.
7. Consensus term is distinct from cluster epoch.
8. Fence token is distinct from leadership term.
9. Quorum is explicit.
10. Minority cannot silently claim quorum authority.
11. Lease is time/protocol bounded.
12. Expired lease cannot authorize protected work.
13. Fencing protects external resources.
14. Distributed locks are not local mutexes.
15. Leader status is epoch/term scoped.
16. Stale messages are rejected.
17. Exactly-once execution is not universally promised.
18. Retry must consider idempotency.
19. Request identity survives retry.
20. Attempt identity changes per attempt.
21. Consensus state must be deterministic.
22. Physical clock is not consensus.
23. Wall clock is not a monotonic timer.
24. Membership does not imply trust.
25. Discovery does not imply authentication.
26. Authentication does not imply authorization.
27. Authorization cannot bypass 603.
28. Credentials use 601/610.
29. Network transport uses 626/609.
30. Durable state uses 611/612.
31. Resource limits use 606.
32. Scheduling uses 607.
33. Synchronization uses 608.
34. Supervision uses 605.
35. Diagnostics use 602.
36. Unused distributed modules can be stripped.
37. No mandatory external coordinator.
38. No mandatory cloud.
39. No mandatory service mesh.
40. No mandatory database.
41. No automatic consensus membership mutation after timeout.
42. Split-brain safety requires protocol support.
43. Recovery must revalidate authority.
44. Rejoining node receives a new generation.
45. Old credentials can be revoked.
46. Watch streams require bounded resources.
47. Snapshots require explicit consistency semantics.
48. Schema changes require compatibility handling.
49. Rolling upgrades preserve quorum.
50. Administrative changes are capability-protected.

---

# 321. Acceptance Criteria

The implementation is accepted when it provides:

### Identity
1. NodeId.
2. Node generation.
3. ClusterId.
4. Cluster epoch.
5. request identity.
6. attempt identity.
7. fence token.

### Membership
8. join.
9. leave.
10. rejoin.
11. membership snapshot.
12. membership watch.
13. health state.
14. suspicion.
15. failure detection.
16. stale generation detection.

### Coordination
17. lease.
18. renewal.
19. expiration.
20. distributed lock.
21. fencing.
22. leader election.
23. leadership watch.
24. quorum state.
25. coordination namespaces.

### Consensus
26. provider abstraction.
27. proposal.
28. commit.
29. replicated log.
30. snapshot.
31. restore.
32. term.
33. commit index.
34. deterministic state machine.
35. provider replacement boundary.

### Consistency
36. local read.
37. leader read.
38. quorum read.
39. linearizable boundary.
40. bounded-stale boundary.
41. eventual consistency boundary.
42. logical clock.
43. causal metadata.

### Security
44. secure join.
45. mTLS.
46. credential protection.
47. capability authorization.
48. admin authorization.
49. revocation.
50. audit.

### Resilience
51. network partition.
52. message loss.
53. duplication.
54. reordering.
55. delay.
56. restart.
57. crash.
58. quorum loss.
59. recovery.
60. stale message rejection.

### Resource Governance
61. watcher limits.
62. connection limits.
63. heartbeat limits.
64. log limits.
65. snapshot limits.
66. memory limits.
67. CPU accounting.
68. storage quotas.

### Integration
69. 600 state.
70. 601 configuration.
71. 602 diagnostics.
72. 603 security.
73. 604 IPC.
74. 605 supervision.
75. 606 resources.
76. 607 scheduler.
77. 608 synchronization.
78. 609 network.
79. 610 crypto.
80. 611 storage.
81. 612 serialization.
82. 613 package.
83. 623 plugins.
84. 624 scripting.
85. 625 distribution.
86. 626 application networking.

### Testing
87. partition tests.
88. stale-message tests.
89. generation tests.
90. lease tests.
91. fencing tests.
92. election tests.
93. quorum tests.
94. crash recovery tests.
95. snapshot tests.
96. corruption tests.
97. upgrade tests.
98. fuzzing.
99. race tests.
100. deterministic simulation.

---

# 322. Final Architecture

```text
                         AXIOM APPLICATION
                                │
                ┌───────────────┴───────────────┐
                │                               │
          Distributed API                 Local State
                │                               │
                ▼                               ▼
       ┌───────────────────┐            ┌──────────────┐
       │       627         │            │     600      │
       │ Distributed       │            │ Application  │
       │ Coordination      │            │ State        │
       ├───────────────────┤            └──────────────┘
       │ Membership        │
       │ Failure Detector  │
       │ Lease             │
       │ Lock              │
       │ Fencing           │
       │ Election          │
       │ Quorum            │
       │ Consensus API     │
       │ Logical Clocks    │
       │ Cluster State     │
       └─────────┬─────────┘
                 │
                 ▼
       ┌───────────────────┐
       │       626         │
       │ RPC / HTTP / WS   │
       └─────────┬─────────┘
                 │
                 ▼
       ┌───────────────────┐
       │       609         │
       │ Network Transport │
       └─────────┬─────────┘
                 │
          ┌──────┴──────┐
          ▼             ▼
        610           611/612
        TLS         Durable State
```

---

# 323. Final Design Decision

Axiom's distributed runtime deliberately uses a **layered capability model**:

```text
609 = transport
626 = application networking
627 = distributed coordination
```

Consensus is a provider boundary rather than an unavoidable dependency.

This allows:

```text
tiny local application
        ↓
HTTP client

small server
        ↓
HTTP + RPC

distributed application
        ↓
HTTP/RPC + discovery

clustered service
        ↓
membership + lease + election

strongly consistent cluster
        ↓
consensus provider
```

without forcing the smallest Axiom executable to contain distributed-systems machinery.

# 324. Task Completion

**BOOTSTRAP-627 — COMPLETE**

**Next queued task: BOOTSTRAP-628 — Native Distributed Data, Replicated Storage, Consistency Models, Distributed Cache, CRDT Boundary, Event Log & Data Replication Runtime 5.0**
:::