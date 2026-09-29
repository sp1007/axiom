Tiếp tục với **BOOTSTRAP-634**.

:::writing{variant="document" id="85217" title="BOOTSTRAP-634 — Native Distributed Event Bus, Pub/Sub, Message Broker Boundary, Topic Partitioning, Consumer Groups, Delivery Guarantees & Stream Processing Runtime 5.0"}

# BOOTSTRAP-634
## Native Distributed Event Bus, Pub/Sub, Message Broker Boundary, Topic Partitioning, Consumer Groups, Delivery Guarantees & Stream Processing Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Event / Messaging / Stream Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-633

---

# 1. Purpose

BOOTSTRAP-634 defines the native Axiom runtime for distributed event-driven applications.

It provides:

- publish/subscribe;
- distributed topics;
- partitions;
- consumer groups;
- durable event streams;
- transient event streams;
- message delivery;
- acknowledgements;
- retries;
- dead-letter queues;
- ordering;
- replay;
- offsets;
- event retention;
- compaction;
- stream processing;
- filtering;
- transformation;
- windowing;
- aggregation;
- joins;
- checkpointing;
- backpressure;
- event routing;
- event schema management;
- distributed event observability.

The runtime is designed to work without requiring Kafka, RabbitMQ, NATS, Pulsar, Redis Streams, or another mandatory external broker.

External brokers are provider adapters.

---

# 2. Architectural Position

```text
                         PRODUCER
                            │
                            ▼
                    ┌───────────────┐
                    │     634       │
                    │ EVENT RUNTIME │
                    ├───────────────┤
                    │ Topics        │
                    │ Partitions    │
                    │ Log           │
                    │ Routing       │
                    │ ConsumerGroup │
                    │ Delivery      │
                    │ Retry/DLQ    │
                    │ Stream Proc. │
                    └───────┬───────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
             Consumer A  Consumer B  Processor
                            │
                            ▼
                          628
```

---

# 3. Relationship With BOOTSTRAP-628

628 defines distributed data replication and event-log primitives.

634 builds the application-facing event distribution model above those primitives.

```text
628
 = replicated data/log foundation

634
 = event distribution + consumer semantics + stream processing
```

---

# 4. Relationship With BOOTSTRAP-629

629 handles durable workflows and jobs.

634 provides the event trigger and event transport used by workflows.

```text
634 Event
   ↓
629 Workflow
   ↓
Activities
```

---

# 5. Relationship With BOOTSTRAP-633

633 defines event schemas.

634 transports and processes instances of those schemas.

---

# 6. Event Model

An event consists of:

```text
EventId
EventType
SchemaFingerprint
ProducerId
Timestamp
PartitionKey
Headers
Payload
```

---

# 7. Event Identity

Each event has a globally unique logical identity when durable identity is required.

The identity must not depend on consumer attempts.

---

# 8. Event Sequence

Within a partition:

```text
PartitionOffset
```

provides a monotonic sequence.

Offsets are scoped to the partition.

---

# 9. Topic

```text
Topic:
    TopicId
    Name
    SchemaPolicy
    RetentionPolicy
    PartitionPolicy
    DeliveryPolicy
    SecurityPolicy
```

---

# 10. Topic Identity

A topic has a stable:

```text
TopicId
```

independent of its human-readable name.

---

# 11. Topic Naming

Topic names use canonical UTF-8 identifiers.

Names must not contain ambiguous normalization variants.

---

# 12. Topic Namespace

Namespaces can separate:

```text
application
tenant
environment
organization
system
```

---

# 13. Topic Lifecycle

```text
Created
 ↓
Active
 ↓
Draining
 ↓
Archived
 ↓
Deleted
```

---

# 14. Topic Creation

Creation requires authorization.

Applications cannot create arbitrary topics without the corresponding capability.

---

# 15. Topic Configuration

Configuration includes:

```text
partitions
replication
retention
maximum message size
ordering
compression
encryption
consumer policy
```

---

# 16. Partition

A topic consists of one or more partitions.

```text
Topic
 ├── Partition 0
 ├── Partition 1
 ├── Partition 2
 └── ...
```

---

# 17. Partition Identity

```text
PartitionId =
    TopicId + PartitionNumber + Generation
```

---

# 18. Partition Ordering

Events within one partition have a strict append order.

Cross-partition global ordering is not guaranteed.

---

# 19. Partition Key

Producer can provide:

```text
PartitionKey
```

to preserve related events in the same partition.

---

# 20. Partition Selection

Default selection:

```text
hash(PartitionKey) % partition_count
```

A configurable deterministic partitioner may be used.

---

# 21. No Ordering Illusion

A system must never claim total ordering merely because multiple partitions are consumed sequentially by one client.

---

# 22. Partition Rebalancing

Changing partition count may alter key distribution.

The runtime must explicitly distinguish:

```text
PartitionExpansion
```

from ordinary consumer rebalancing.

---

# 23. Stable Key Ordering

Applications requiring stable per-key ordering should use a partition strategy that preserves key-to-partition mapping.

---

# 24. Producer

```text
Producer:
    ProducerId
    Topic
    Policy
```

---

# 25. Publish API

```text
fn Producer.publish(
    event: Event
) -> Future<Result<PublishReceipt>>
```

---

# 26. Batch Publish

```text
fn Producer.publish_batch(
    events: EventBatch
) -> Future<Result<BatchPublishReceipt>>
```

---

# 27. Publish Receipt

Contains:

```text
EventId
TopicId
PartitionId
Offset
Timestamp
```

---

# 28. Acknowledgement

Publish acknowledgement levels:

```text
None
Accepted
Persisted
Replicated
Committed
```

---

# 29. Delivery Guarantees

Supported semantics:

```text
AtMostOnce
AtLeastOnce
EffectivelyOnce
```

The runtime does not claim magical distributed exactly-once semantics.

---

# 30. At-Most-Once

Event is delivered at most once but may be lost.

---

# 31. At-Least-Once

Event may be delivered multiple times.

Consumers must support idempotency where required.

---

# 32. Effectively-Once

Achieved through:

```text
stable EventId
deduplication
idempotent consumer
transactional state update
```

rather than relying on an unrestricted global exactly-once transaction.

---

# 33. Consumer

```text
Consumer:
    ConsumerId
    Topic
    Subscription
```

---

# 34. Consumer Group

A consumer group allows multiple consumers to share partitions.

```text
Topic
 ├── P0 → Consumer A
 ├── P1 → Consumer B
 └── P2 → Consumer C
```

---

# 35. Consumer Group Identity

```text
ConsumerGroupId
```

is independent of individual process identity.

---

# 36. Group Membership

Each member has:

```text
MemberId
Generation
Capabilities
Health
Lease
```

---

# 37. Rebalancing

When membership changes:

```text
join
leave
failure
capacity change
```

partitions may be reassigned.

---

# 38. Rebalance Generation

Every assignment has a generation.

Stale consumers cannot commit offsets against a newer generation unless explicitly permitted.

---

# 39. Assignment Strategies

```text
Range
RoundRobin
Sticky
Cooperative
LoadAware
LocalityAware
```

---

# 40. Cooperative Rebalancing

Preferred where supported to minimize unnecessary partition movement.

---

# 41. Partition Affinity

Consumers may express:

```text
zone
region
device
GPU
CPU architecture
data locality
```

preferences.

---

# 42. Consumer Poll

```text
fn Consumer.poll(
    max_events: usize,
    deadline: Deadline
) -> Future<Result<EventBatch>>
```

---

# 43. Push Subscription

Optional provider mode:

```text
subscribe(callback)
```

must still obey bounded concurrency and backpressure.

---

# 44. Pull Preferred Core

The canonical core consumer model uses pull semantics because they provide explicit flow control.

---

# 45. Offset

A consumer tracks:

```text
Topic
Partition
Offset
```

---

# 46. Offset Commit

```text
fn Consumer.commit(
    offset: Offset
) -> Result<void>
```

---

# 47. Commit Semantics

The runtime must distinguish:

```text
received
processed
side_effect_completed
committed
```

---

# 48. Safe Commit Rule

For at-least-once processing:

```text
process
 ↓
durable side effect
 ↓
commit offset
```

is the default safe sequence.

---

# 49. Auto Commit

Auto-commit is optional and must never be presented as equivalent to processing acknowledgement.

---

# 50. Offset Store

Offsets may be stored in:

```text
local
628 distributed store
durable log
external provider
```

---

# 51. Offset Retention

Offset history may have retention independent from event retention.

---

# 52. Start Position

Consumer can start:

```text
Earliest
Latest
Timestamp
Offset
EventId
Snapshot
```

---

# 53. Replay

Consumers can intentionally replay historical events.

---

# 54. Replay Isolation

Replay must not accidentally modify production state unless explicitly configured.

---

# 55. Replay Mode

```text
Live
Replay
CatchUp
ReplayThenLive
```

---

# 56. Consumer Pause

A consumer can pause consumption while preserving assignment and/or lease within configured limits.

---

# 57. Consumer Resume

Resume starts from the last valid committed or explicitly selected position.

---

# 58. Backpressure

Consumers advertise capacity:

```text
max events
max bytes
max concurrent processing
```

---

# 59. Producer Backpressure

A topic can reject or delay publishing when:

```text
storage pressure
replication lag
partition overload
quota exhaustion
```

occurs.

---

# 60. Bounded Queues

No mandatory internal queue may grow without a configured bound.

---

# 61. Event Size

Topic policies define:

```text
max event bytes
max header bytes
max batch bytes
```

---

# 62. Event Headers

Headers are typed metadata:

```text
name
type
value
```

---

# 63. Header Security

Sensitive headers can be marked:

```text
Secret
Internal
```

and excluded from telemetry.

---

# 64. Event Schema

Every typed event may reference:

```text
SchemaFingerprint
```

from 633.

---

# 65. Schema Validation

Producer can validate before publish.

Consumer must not assume producers are trustworthy.

---

# 66. Consumer Validation

A consumer may reject incompatible schemas before decoding payloads.

---

# 67. Schema Evolution

Events follow 633 compatibility rules.

---

# 68. Schema Registry

634 can resolve schema metadata from 633.

---

# 69. Schema Cache

Frequently used schemas should be cached locally.

---

# 70. Schema Mismatch

A consumer receiving an incompatible schema produces a typed:

```text
SchemaMismatch
```

error.

---

# 71. Dead-Letter Queue

Failed events can be redirected to:

```text
DLQ
```

with failure metadata.

---

# 72. DLQ Event

A dead-letter record contains:

```text
OriginalEvent
FailureReason
FailureCount
FirstFailure
LastFailure
ConsumerId
ConsumerGeneration
```

---

# 73. Retry Queue

Retry scheduling can use:

```text
Immediate
Delayed
ExponentialBackoff
FixedDelay
Calendar
```

---

# 74. Retry Budget

Retries are bounded by:

```text
max attempts
max elapsed time
max bytes
```

---

# 75. Retry Storm Prevention

Backoff uses bounded exponential delay plus jitter.

---

# 76. Poison Event

An event repeatedly failing deterministic validation should not remain indefinitely in the primary queue.

---

# 77. Poison Handling

Policy:

```text
Retry
Quarantine
DLQ
Skip
StopPartition
StopConsumer
```

---

# 78. Partition Stop

Stopping one partition must not automatically stop unrelated partitions.

---

# 79. Event Ordering With Retry

A topic can choose:

```text
StrictPartitionOrder
BestEffortOrder
```

---

# 80. Strict Ordering

A failed event blocks later events in the same partition until policy resolves it.

---

# 81. Best-Effort Ordering

Failed events may be delayed or redirected while later events continue.

---

# 82. Event Retention

Retention can be:

```text
TimeBased
SizeBased
CountBased
Compacted
UntilAcknowledged
Manual
```

---

# 83. Time-Based Retention

Events older than the configured retention period become eligible for reclamation.

---

# 84. Size-Based Retention

Partition storage is bounded by configured capacity.

---

# 85. Compaction

Compaction may retain the latest value per logical key.

---

# 86. Compaction Safety

Compaction is valid only when topic semantics declare the key/value model.

---

# 87. Tombstones

Compacted topics can represent deletion using tombstone records.

---

# 88. Tombstone Retention

Tombstones must remain long enough to prevent stale replicas from resurrecting deleted state.

---

# 89. Event Log

Each durable partition is an append-oriented log.

---

# 90. Segment

A partition log is divided into segments for:

```text
storage
retention
compaction
recovery
```

---

# 91. Segment Index

Indexes support efficient lookup by:

```text
offset
timestamp
event ID
```

---

# 92. Checksum

Each durable segment/block has integrity protection using 610 primitives.

---

# 93. Compression

Segments may use 613 compression providers.

---

# 94. Encryption

Encrypted-at-rest storage uses 610 and 611.

---

# 95. Replication

Durable topics may replicate through 628.

---

# 96. Replica Modes

```text
LeaderFollower
MultiLeader
LeaderlessProvider
GeoReplica
ReadReplica
```

---

# 97. Leader

A partition leader is responsible for ordered append where leader-based replication is selected.

---

# 98. Fencing

Leadership changes use an epoch/fencing token.

---

# 99. Stale Leader

A stale leader must be unable to continue accepting writes after losing authority.

---

# 100. Replica Lag

Consumers may observe replica lag.

Read policies can specify:

```text
LeaderOnly
LocalReplica
BoundedStaleness
AnyAvailable
```

---

# 101. Cross-Region Replication

Replication can span regions.

Cross-region latency is explicitly represented in availability/consistency policies.

---

# 102. Geo Failover

Failover policy must define:

```text
data loss tolerance
stale-read tolerance
write fencing
```

---

# 103. No Automatic Split-Brain Writes

A partition cannot accept concurrent writes from two leaders without an explicit conflict model.

---

# 104. Multi-Primary

Multi-primary mode requires an explicit conflict-resolution policy.

---

# 105. Conflict Metadata

Conflicts may use:

```text
version vectors
logical clocks
Lamport timestamps
causal metadata
```

from 628.

---

# 106. Consumer Exactly-Once Boundary

634 does not claim exactly-once execution across arbitrary external side effects.

---

# 107. Transactional Consumer

Optional transactional consumer integrates:

```text
event offset
+
628 state mutation
```

into one supported atomic boundary.

---

# 108. Outbox Integration

Application state changes can publish events through 628 outbox semantics.

---

# 109. Inbox Integration

Consumers can use 628 inbox/deduplication semantics.

---

# 110. Event ID Deduplication

Deduplication key:

```text
EventId
```

or an application-defined stable key.

---

# 111. Deduplication Window

Deduplication state has explicit retention.

---

# 112. Duplicate Delivery

Consumers must assume duplicates are possible under at-least-once semantics.

---

# 113. Event Bus

A logical event bus contains:

```text
topics
subscriptions
routing
authorization
consumer groups
```

---

# 114. Subscription

```text
Subscription:
    SubscriptionId
    TopicPattern
    Filter
    DeliveryPolicy
    ConsumerPolicy
```

---

# 115. Topic Patterns

Subscriptions may match:

```text
exact topic
namespace
prefix
declared topic group
```

Wildcard access requires explicit capability.

---

# 116. Event Filter

Filters can use:

```text
event type
header
key
schema
metadata
```

---

# 117. Filter Execution

Filters are compiled into bounded evaluation plans.

---

# 118. No Arbitrary Filter Code

The core event bus does not execute arbitrary user code to decide every event.

---

# 119. Stream Processing

634 supports stream processing pipelines.

```text
Source
 ↓
Filter
 ↓
Map
 ↓
Window
 ↓
Aggregate
 ↓
Join
 ↓
Sink
```

---

# 120. Stream

```text
Stream<T>
```

represents an ordered sequence of events.

---

# 121. Stream Operator

Operators include:

```text
map
filter
flat_map
key_by
window
aggregate
reduce
join
merge
split
buffer
throttle
deduplicate
```

---

# 122. Map

Transforms:

```text
Event<A> → Event<B>
```

---

# 123. Filter

Selects events matching a deterministic predicate.

---

# 124. Key By

Partitions a stream by a derived key.

---

# 125. Windowing

Supported windows:

```text
Tumbling
Sliding
Session
Count
Global
```

---

# 126. Tumbling Window

Non-overlapping fixed intervals.

---

# 127. Sliding Window

Overlapping time or count ranges.

---

# 128. Session Window

Groups events separated by inactivity.

---

# 129. Event Time

Stream processing distinguishes:

```text
event time
processing time
ingestion time
```

---

# 130. Watermark

A watermark represents the processor's progress assumption about event time.

---

# 131. Late Event

Late events are handled by explicit policy:

```text
Drop
UpdateWindow
SideOutput
DeadLetter
```

---

# 132. Allowed Lateness

Each window can define:

```text
AllowedLateness
```

---

# 133. Window State

Window state is stored through:

```text
628
612
```

rather than requiring GC-managed objects.

---

# 134. Aggregation

Supported aggregation primitives:

```text
count
sum
min
max
average
distinct
custom stateful aggregate
```

---

# 135. Stateful Operator

A stateful operator owns an explicit state namespace.

---

# 136. State Identity

State key:

```text
ProcessorId
OperatorId
Partition
UserKey
```

---

# 137. State Recovery

Processor checkpoints include:

```text
input offsets
operator state generation
window state
```

---

# 138. Checkpoint

Checkpointing integrates with 600 and 628.

---

# 139. Checkpoint Frequency

Configurable by:

```text
time
events
bytes
operator policy
```

---

# 140. Recovery

After failure:

```text
restore checkpoint
 ↓
restore offsets
 ↓
replay subsequent events
```

---

# 141. Deterministic Processing

For reproducible recovery, stateful operators should avoid uncontrolled nondeterministic external effects.

---

# 142. Side Effects

External side effects require explicit sink semantics.

---

# 143. Sink

```text
EventSink<T>
```

can write to:

```text
topic
database
file
service
workflow
HTTP endpoint
```

through provider abstractions.

---

# 144. Sink Retry

Sink failures use explicit retry policy.

---

# 145. Sink Idempotency

Where possible, sink writes should use event identity.

---

# 146. Stream Join

Supported join types:

```text
Inner
Left
Windowed
Temporal
```

subject to bounded state.

---

# 147. Join State

Join state requires explicit retention.

No unbounded join state is allowed.

---

# 148. Temporal Join

A stream may join against a versioned 628 state snapshot.

---

# 149. Broadcast Stream

A topic may intentionally deliver every event to every subscriber.

---

# 150. Work Queue

A consumer group behaves as a distributed work queue.

---

# 151. Pub/Sub

Independent subscriptions receive the same logical event stream.

---

# 152. Event Fan-Out

Fan-out can be:

```text
broker-side
consumer-side
hybrid
```

---

# 153. Event Routing

Routing rules may select topics based on:

```text
event type
tenant
region
schema
metadata
```

---

# 154. Event Transformation

Transformation is explicit and schema-aware.

---

# 155. Dead-Letter Routing

A failed event can be routed to a dedicated DLQ topic.

---

# 156. Audit Topic

Security-sensitive events may be published into an audit stream.

---

# 157. Event Security

Topic access uses 603 capabilities.

---

# 158. Producer Capability

Producer receives explicit:

```text
PublishCapability<Topic>
```

---

# 159. Consumer Capability

Consumer receives:

```text
SubscribeCapability<Topic>
```

---

# 160. Topic Administration

Administration requires stronger capability:

```text
ManageTopicCapability
```

---

# 161. Tenant Isolation

Tenant topics and consumer groups can be isolated.

---

# 162. Cross-Tenant Access

Cross-tenant subscriptions require explicit authorization.

---

# 163. Secret Events

Secret payloads must be explicitly classified.

Default telemetry does not inspect payload contents.

---

# 164. Encryption

Topic-level encryption can use 610.

---

# 165. End-to-End Encryption

Producer and consumer can encrypt payloads so the broker does not possess plaintext.

---

# 166. TLS

Transport security uses 610/609.

---

# 167. Authentication

Broker/service authentication integrates with 627.

---

# 168. Authorization

Authorization is evaluated at:

```text
topic
publish
subscribe
consumer group
administration
```

levels.

---

# 169. Quotas

606 governs:

```text
publish rate
consume rate
storage
connections
consumer groups
partitions
event bytes
```

---

# 170. Tenant Quotas

Quota dimensions can be independent.

---

# 171. Fair Scheduling

Partition processing must prevent a hot tenant from starving unrelated tenants.

---

# 172. Hot Partition

The runtime detects partitions with abnormal load.

---

# 173. Hot Partition Policy

Possible actions:

```text
Alert
Throttle
Split
Redirect
Repartition
```

Only explicit policies may automatically change partition topology.

---

# 174. Partition Split

Partition splitting changes ordering topology and therefore requires explicit migration semantics.

---

# 175. Consumer Lag

Lag metrics:

```text
offset lag
time lag
bytes lag
```

---

# 176. Lag-Based Autoscaling

External or 605/630 orchestration may scale consumers based on lag.

---

# 177. Consumer Health

Health combines:

```text
heartbeat
poll activity
processing latency
commit progress
resource pressure
```

---

# 178. Stalled Consumer

A consumer that stops progressing can be revoked after lease expiry.

---

# 179. Cooperative Shutdown

Consumer shutdown:

```text
stop fetching
finish bounded work
commit safe offsets
release assignment
close
```

---

# 180. Forced Shutdown

On deadline expiry, uncommitted work is eligible for redelivery.

---

# 181. Message Visibility

Work-queue providers may use visibility leases.

---

# 182. Lease

```text
LeaseId
ConsumerGeneration
Expiry
Partition
OffsetRange
```

---

# 183. Lease Fencing

Expired leases cannot commit successful processing after ownership changes.

---

# 184. Delivery Attempt

Every delivery attempt has:

```text
AttemptNumber
ConsumerId
Timestamp
```

---

# 185. Retry Metadata

Retry metadata must not mutate the original event identity.

---

# 186. Event Trace

Trace metadata may identify:

```text
producer
topic
partition
offset
consumer
attempt
```

---

# 187. Metrics

Required metrics include:

```text
published
consumed
acked
retried
dead_lettered
bytes
lag
processing_latency
publish_latency
replication_lag
```

---

# 188. High Cardinality

Raw EventId values must not automatically become unbounded metric labels.

---

# 189. Diagnostics

602 receives:

```text
consumer failure
partition failure
rebalance
lag
schema mismatch
DLQ event
replication failure
```

---

# 190. Structured Logs

Event logs contain stable identifiers but never arbitrary payload dumps by default.

---

# 191. Distributed Tracing

Trace propagation uses 602/633 RequestContext metadata.

---

# 192. Configuration

601 defines:

```text
topic
consumer
producer
retention
partition
security
stream
```

configuration.

---

# 193. Configuration Reload

Safe runtime policy can reload atomically.

Topology-changing operations require explicit lifecycle transitions.

---

# 194. Package Integration

Event schemas and stream definitions can be packaged via 613/625.

---

# 195. Compiler Metadata

Supported annotations:

```text
@event
@topic
@producer
@consumer
@subscription
@partition
@key
@ordered
@retention
@stream
@window
@aggregate
@checkpoint
@dead_letter
@delivery
```

---

# 196. Generated Artifacts

Compiler may generate:

```text
.axevent
.axtopic
.axconsumer
.axstream
.axschema
```

---

# 197. Generated Producer

```text
struct UserEventProducer

fn UserEventProducer.publish(
    ctx: RequestContext,
    event: UserCreated
) -> Future<Result<PublishReceipt>>
```

---

# 198. Generated Consumer

```text
struct UserEventConsumer

fn UserEventConsumer.poll(
    ctx: RequestContext
) -> Future<Result<EventBatch<UserCreated>>>
```

---

# 199. Generated Stream

```text
struct UserStream

fn UserStream.filter(...)
fn UserStream.map(...)
fn UserStream.window(...)
fn UserStream.aggregate(...)
```

---

# 200. Compiler Validation

Compiler validates:

```text
event type
schema
topic binding
partition key
security requirements
stream operator types
window state
sink type
```

---

# 201. Type-Safe Pipelines

Invalid stream composition should be rejected at compile time where statically knowable.

---

# 202. Example

```text
events UserCreated
    |> key_by(.tenant_id)
    |> window(tumbling(1m))
    |> aggregate(count)
    |> publish(UserStatistics)
```

---

# 203. Stream Lowering

Compiler lowers pipelines into:

```text
source
operator graph
state
checkpoint
sink
```

---

# 204. Operator Graph

The graph must be acyclic unless an explicit feedback operator exists.

---

# 205. Cycle Detection

Unintentional cycles are compile-time errors.

---

# 206. Operator Parallelism

Operators may declare:

```text
parallelism
partitioning
state affinity
```

---

# 207. State Affinity

Stateful operators should execute consistently for the same key.

---

# 208. Repartition Operator

Explicit repartitioning can change key distribution.

---

# 209. Repartition Cost

Runtime reports network/storage cost for repartition operations.

---

# 210. Batch Processing

Stream operators can process batches for CPU efficiency.

---

# 211. Vectorized Processing

Provider/optimizer may use SIMD for suitable operators.

---

# 212. GPU Stream Processing

630/614/615 can provide optional GPU execution for computational operators.

---

# 213. GPU Safety

GPU stream processing must not block the ordinary gateway/event loop.

---

# 214. CPU/GPU Scheduling

606/607 determine resource allocation.

---

# 215. Memory Model

Stream state uses explicit ownership and bounded storage.

---

# 216. No Mandatory GC

Large state is managed through:

```text
arena
page
buffer
persistent collection
```

where appropriate.

---

# 217. Spill to Storage

Large state may spill to 611.

---

# 218. Spill Policy

Spilling requires:

```text
storage capability
quota
latency policy
encryption policy
```

---

# 219. Crash Consistency

State and checkpoint updates use 611/612 durability primitives.

---

# 220. Stream Upgrade

A running processor can be upgraded using:

```text
drain
checkpoint
replace
restore
replay
```

---

# 221. Processor Version

Each stream processor has:

```text
ProcessorId
Version
Generation
StateSchemaFingerprint
```

---

# 222. State Migration

State schema changes require explicit migration.

---

# 223. No Implicit State Migration

Runtime must never reinterpret arbitrary serialized state as a new schema.

---

# 224. Processor Rollback

Rollback requires a compatible checkpoint/state schema.

---

# 225. Event Replay After Upgrade

Replay can rebuild state from a compatible event history.

---

# 226. Deterministic Replay

Replay uses recorded event ordering and timestamps where required.

---

# 227. External Time

Stream operators must explicitly choose:

```text
EventTime
ProcessingTime
```

rather than silently using wall-clock time.

---

# 228. Randomness

Deterministic replay requires seeded or recorded randomness.

---

# 229. External Calls

External calls inside stream operators are side effects and must be explicitly modeled.

---

# 230. Side-Effect Isolation

Recommended pattern:

```text
stream
 ↓
decision
 ↓
durable command/event
 ↓
external worker
```

rather than unrestricted side effects inside deterministic operators.

---

# 231. Event-Sourced Applications

634 can act as the event transport for event-sourced applications built on 628.

---

# 232. Snapshot Integration

State snapshots use 612/628.

---

# 233. Event Retention and Snapshots

Snapshotting does not automatically permit deletion of historical events unless recovery requirements remain satisfied.

---

# 234. Event Archival

Expired events may be archived into:

```text
611 storage
613 package/archive
628 object store
```

---

# 235. Event Export

Export formats may include:

```text
AXBIN
JSON
CSV
external broker format
```

where explicitly configured.

---

# 236. External Broker Providers

Optional adapters:

```text
KafkaProvider
NatsProvider
RabbitMqProvider
PulsarProvider
RedisStreamProvider
CloudEventProvider
```

These are interoperability modules, not core dependencies.

---

# 237. Provider Contract

All providers implement the common event semantics as far as the underlying system permits.

---

# 238. Semantic Gaps

If an external provider cannot provide a requested guarantee, the runtime must report the limitation rather than silently pretending the guarantee exists.

---

# 239. Cloud Provider Boundary

Cloud-managed queues/event buses are optional providers.

---

# 240. Local Embedded Bus

A small-process event bus should be available without networking.

---

# 241. In-Process Fast Path

For same-process producers and consumers:

```text
publish
 ↓
lock-free/bounded queue
 ↓
consumer
```

may bypass serialization while preserving contract semantics.

---

# 242. Same-Node IPC

604 may provide the next-level fast path.

---

# 243. Cross-Process Semantics

The same EventId/schema/security semantics must survive IPC transport.

---

# 244. Cross-Service Semantics

631/626 can carry the same event contract across services.

---

# 245. Gateway Integration

632 may expose event submission APIs such as:

```text
POST /events/UserCreated
```

mapped to 634 topics.

---

# 246. Authentication

Gateway-authenticated identity becomes producer context only through explicit policy.

---

# 247. Event API Rate Limiting

632/606 can limit:

```text
events/sec
bytes/sec
batch size
```

at the external boundary.

---

# 248. Administrative API

Administrative operations include:

```text
list topics
inspect topic
list partitions
inspect consumer group
inspect lag
pause consumer
resume consumer
replay
purge
inspect schema
inspect stream
```

---

# 249. Dangerous Operations

Operations such as:

```text
purge
truncate
rewind
force-leader
delete-topic
```

require elevated capability.

---

# 250. Audit

Administrative event operations generate 602 audit records.

---

# 251. Security Invariants

1. Publish requires authorization.
2. Subscribe requires authorization.
3. Consumer-group access is separately controlled.
4. Topic administration requires elevated capability.
5. Cross-tenant subscription requires explicit authorization.
6. Payloads are not automatically trusted.
7. Event headers are not automatically trusted.
8. Secret fields are excluded from ordinary telemetry.
9. External broker providers cannot silently elevate capabilities.
10. Replay cannot bypass authorization.

---

# 252. Performance Invariants

1. Local publish must avoid unnecessary serialization.
2. Consumer queues are bounded.
3. Partition processing is parallelizable.
4. Stateful operators preserve key affinity.
5. Hot paths avoid global locks.
6. Buffer reuse is supported.
7. Large events can stream.
8. Batch operations are supported.
9. Dead features are removable.
10. No GC is mandatory.

---

# 253. Reliability Invariants

1. Partition ordering is explicit.
2. Offset generation prevents stale commits.
3. Lease expiry fences stale consumers.
4. Retries are bounded.
5. DLQ prevents poison-event loops.
6. Checkpoints are durable where configured.
7. Recovery replays from a known position.
8. Replication uses fencing.
9. Split-brain writes are prevented.
10. Data-loss semantics are explicit.

---

# 254. Stream-Processing Invariants

1. Operator graphs are typed.
2. Unbounded state requires explicit policy.
3. Windows have explicit retention.
4. Late events have explicit handling.
5. Checkpoints identify input offsets.
6. State schema is versioned.
7. State migration is explicit.
8. External side effects are explicit.
9. Replay semantics are deterministic where promised.
10. Backpressure propagates.

---

# 255. Acceptance Criteria

The implementation must demonstrate at least:

### Event Bus
- topic creation;
- topic deletion;
- topic metadata;
- partitions;
- partition offsets;
- publish;
- batch publish;
- event IDs;
- event headers;
- schema references.

### Consumer
- consumer groups;
- membership;
- leases;
- partition assignment;
- rebalance;
- offset commit;
- replay;
- pause/resume;
- cooperative shutdown.

### Delivery
- at-most-once;
- at-least-once;
- deduplication;
- retry;
- delayed retry;
- retry budgets;
- DLQ;
- poison-event handling.

### Ordering
- partition ordering;
- keyed ordering;
- strict ordering;
- best-effort ordering;
- partition affinity.

### Storage
- durable log;
- retention;
- compaction;
- tombstones;
- segment indexing;
- checksums;
- compression;
- encryption;
- replication.

### Stream Processing
- map;
- filter;
- key-by;
- merge;
- split;
- window;
- aggregation;
- join;
- repartition;
- stateful operator;
- checkpoint;
- recovery;
- replay;
- state migration.

### Security
- producer capabilities;
- consumer capabilities;
- topic administration;
- tenant isolation;
- encrypted transport;
- encrypted storage;
- secret metadata;
- audit.

### Integration
- 600 state/checkpoint;
- 601 configuration;
- 602 diagnostics;
- 603 capabilities;
- 604 IPC;
- 605 supervision;
- 606 resources;
- 607 async;
- 608 synchronization;
- 609 networking;
- 610 cryptography;
- 611 storage;
- 612 serialization;
- 613 compression/package;
- 625 distribution;
- 628 distributed data;
- 629 workflows;
- 630 distributed compute;
- 631 services;
- 632 gateway;
- 633 API contracts.

### Testing
- deterministic event bus;
- deterministic scheduler;
- partition failure;
- broker failure;
- consumer crash;
- duplicate delivery;
- rebalance;
- stale commit;
- retry storm;
- poison event;
- schema mismatch;
- state recovery;
- late event;
- watermark;
- stream upgrade;
- state migration;
- fuzzing.

**Target: ≥300 acceptance criteria.**

---

# 256. Runtime Profiles

```text
AXEVENT_NONE
    no event runtime

AXEVENT_LOCAL
    in-process event bus

AXEVENT_IPC
    local distributed-process messaging

AXEVENT_DURABLE
    durable event log

AXEVENT_PUBSUB
    distributed pub/sub

AXEVENT_STREAM
    stream processing

AXEVENT_REPLICATED
    replicated event infrastructure

AXEVENT_EXTERNAL
    external broker providers

AXEVENT_FULL
    complete event platform
```

---

# 257. Final Architecture

```text
                         PRODUCERS
                            │
                            ▼
                    ┌────────────────┐
                    │      634       │
                    │ EVENT RUNTIME  │
                    ├────────────────┤
                    │ Auth / Policy  │
                    │ Topics         │
                    │ Partitions     │
                    │ Durable Log    │
                    │ Replication    │
                    │ Consumer Group │
                    │ Offset Store   │
                    │ Retry / DLQ    │
                    │ Pub/Sub        │
                    │ Stream Engine  │
                    │ Checkpoints    │
                    └───────┬────────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         Consumer       Workflow       Stream Sink
             │              │              │
             ▼              ▼              ▼
            629            628            611
             │
             ▼
            630

         ┌───────────────────────────────────┐
         │ Foundations                       │
         │ 603 Security                      │
         │ 606 Resources                     │
         │ 607 Scheduler                     │
         │ 608 Synchronization               │
         │ 610 Crypto                        │
         │ 612 Serialization                 │
         │ 633 Contracts                     │
         └───────────────────────────────────┘
```

---

# 258. Completion

**BOOTSTRAP-634 — COMPLETE**

Axiom now has a complete distributed event path:

```text
633 Contract
      ↓
634 Event Bus
      ↓
Topic / Partition
      ↓
Consumer Group
      ↓
Stream Processor
      ↓
628 State / 629 Workflow / 630 Compute / 631 Service
```

This establishes the event-driven backbone needed for large distributed Axiom applications while keeping broker implementations replaceable.

**NEXT TASK: BOOTSTRAP-635 — Native Distributed Scheduler, Cluster Membership, Leader Election, Consensus Boundary, Placement, Service Coordination & Control-Plane Runtime 5.0**
:::