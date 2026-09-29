Tiếp tục với **BOOTSTRAP-620** — lớp này chuẩn hóa cách Axiom kết nối dữ liệu, state, UI, command và undo/redo mà không biến ngôn ngữ thành một framework reactive bắt buộc.

:::writing{variant="document" id="74153" title="BOOTSTRAP-620 — Native Application Data Binding, Reactive State, UI State Synchronization, Commands, Undo/Redo & Model/View Runtime 5.0"}
# BOOTSTRAP-620 — Native Application Data Binding, Reactive State, UI State Synchronization, Commands, Undo/Redo & Model/View Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Application State / UI Data Architecture  
**Depends on:** BOOTSTRAP-600 → 619

---

# 1. Purpose

BOOTSTRAP-620 defines the native application data architecture connecting:

- application state;
- domain models;
- UI state;
- controls;
- commands;
- validation;
- observable values;
- collections;
- derived state;
- transactions;
- undo/redo;
- persistence;
- synchronization;
- asynchronous updates.

The central design goal is:

> **Axiom applications should be able to build reactive, data-driven interfaces without requiring a mandatory global reactive framework, garbage collector, hidden runtime scheduler, or reflection system.**

---

# 2. Design Principles

620 follows:

1. Explicit ownership.
2. Typed state.
3. Deterministic updates.
4. Minimal hidden work.
5. No mandatory global state.
6. No mandatory garbage collection.
7. No mandatory reflection.
8. No automatic background execution.
9. Explicit transaction boundaries.
10. Incremental recomputation.
11. UI-thread confinement where required.
12. Async integration through 607.
13. Persistence through 600/611/612.
14. Commands remain independently testable.
15. Undo/redo is model-operation based rather than pixel/UI based.

---

# 3. Layering

```text
Application Domain
       │
       ▼
   Domain Model
       │
       ▼
  State / Store
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
Derived Commands Validation
 │     │     │
 └─────┼─────┘
       ▼
     Binding
       │
       ▼
     UI 619
```

---

# 4. Core Objects

```text
State<T>
MutableState<T>
Derived<T>
Binding<T>
Store<T>
Transaction
ChangeSet
Observer
Subscription
Command
CommandGroup
UndoManager
UndoRecord
RedoRecord
Validator<T>
ValidationResult
Computed<T>
CollectionState<T>
SelectionState<T>
AsyncState<T>
```

---

# 5. State

The fundamental abstraction is:

```text
State<T>
```

representing a typed value that may change over time.

---

# 6. Immutable Read Access

Consumers should normally receive:

```text
ReadState<T>
```

rather than mutable state access.

---

# 7. Mutable State

Mutation requires:

```text
MutableState<T>
```

or a scoped mutation API.

---

# 8. Example

```text
struct CounterState {
    value: i32
}

let count = State.new(0)

count.set(1)
```

---

# 9. Explicit Ownership

A state object has an explicit owner.

There is no implicit application-wide state singleton.

---

# 10. State Identity

Each state source has a stable identity:

```text
StateId
```

with generation protection where dynamically created.

---

# 11. Change Notification

State changes produce:

```text
Change<T>
```

containing:

```text
state_id
old_value
new_value
version
cause
```

Old/new values may be omitted when expensive and a diff is available.

---

# 12. Version

Each mutable state maintains a monotonically increasing version.

---

# 13. Version Semantics

A version changes only after a successful committed mutation.

Failed transactions do not publish versions.

---

# 14. Observer

Observers subscribe to state changes.

```text
observe(state, callback)
```

returns a `Subscription`.

---

# 15. Subscription Lifetime

Subscriptions have explicit lifetime ownership.

When the owner is destroyed, its subscriptions are cancelled.

---

# 16. No Hidden Retention

Subscriptions must not silently keep arbitrary application objects alive indefinitely.

---

# 17. Weak Subscription

Optional weak subscription:

```text
observe_weak(...)
```

is provided for long-lived publishers.

---

# 18. Notification Ordering

Within one transaction, notifications are delivered in deterministic dependency order.

---

# 19. Notification Coalescing

Multiple writes to the same state inside one transaction may produce one externally visible change.

---

# 20. Transaction

```text
Transaction
```

groups related state mutations atomically.

---

# 21. Transaction Lifecycle

```text
Begin
 ↓
Mutate
 ↓
Validate
 ↓
Commit
```

or:

```text
Begin
 ↓
Mutate
 ↓
Rollback
```

---

# 22. Atomic Visibility

Observers must not see partially committed transactional state.

---

# 23. Nested Transactions

Nested transactions form scopes inside an outer transaction.

Inner commits remain provisional until the outer transaction commits.

---

# 24. Transaction Failure

Any required validation failure can abort the transaction.

---

# 25. ChangeSet

A successful transaction produces:

```text
ChangeSet
```

containing logical state changes.

---

# 26. ChangeSet Identity

```text
ChangeSetId
```

provides deterministic identification for diagnostics, persistence and undo.

---

# 27. Change Causes

A change can identify:

```text
User
Command
System
Network
FileLoad
Undo
Redo
Synchronization
Migration
```

---

# 28. Derived State

```text
Derived<T>
```

represents a value calculated from other state.

---

# 29. Example

```text
let first = State.new("A")
let last  = State.new("xiom")

let name = Derived.compute(
    [first, last],
    fn() => first.get() + last.get()
)
```

---

# 30. Dependency Tracking

Two modes are supported:

```text
ExplicitDependencies
TrackedDependencies
```

---

# 31. Explicit Dependencies

Preferred for predictable compiled applications.

```text
Derived.compute([a, b], fn() => ...)
```

---

# 32. Tracked Dependencies

Optional runtime dependency tracking can detect reads during computation.

---

# 33. No Mandatory Reflection

Tracked dependency discovery does not require reflection metadata.

---

# 34. Derived Cache

A derived value caches:

```text
value
dependency versions
computed version
```

---

# 35. Lazy Derived State

Derived values may compute only when read.

---

# 36. Eager Derived State

Applications may request eager recomputation after dependency changes.

---

# 37. Cycle Detection

Derived-state dependency cycles must be detected.

---

# 38. Cycle Policy

A cycle results in a typed error/diagnostic rather than infinite evaluation.

---

# 39. Computed State

`Computed<T>` is a read-only derived value intended for high-frequency access.

---

# 40. Incremental Computation

Large derived computations may expose explicit incremental update functions.

---

# 41. Memoization

Memoization is optional and scoped.

There is no unrestricted global cache.

---

# 42. Binding

```text
Binding<T>
```

connects a state source with a UI property.

---

# 43. One-Way Binding

```text
State → UI
```

is the default safe binding.

---

# 44. Two-Way Binding

```text
State ↔ UI
```

is explicit.

---

# 45. Binding Adapter

Conversions can be typed:

```text
Binding<T>.map<U>()
```

---

# 46. Binding Validation

A binding can reject invalid UI values without corrupting model state.

---

# 47. Example

```text
let username = state.bind(
    text_field.text,
    parse: String,
    validate: validate_username
)
```

---

# 48. Binding Loop Prevention

A binding update includes an origin token.

The same update must not recursively bounce indefinitely between endpoints.

---

# 49. Binding Conflict

Conflicting simultaneous updates are resolved by explicit transaction policy.

---

# 50. Store

```text
Store<T>
```

is a scoped collection of application state.

---

# 51. Store Responsibilities

A Store can provide:

```text
state
actions
commands
derived state
subscriptions
transactions
```

---

# 52. Store Does Not Own UI

A Store may outlive windows or controls.

---

# 53. Store Lifetime

Store ownership is explicit.

---

# 54. Model

A model is ordinary Axiom data.

No special inheritance hierarchy is required.

---

# 55. View

The view is a 619 UI tree.

---

# 56. ViewModel

A ViewModel is optional.

It is simply a struct containing bindings/derived state/commands.

---

# 57. No Mandatory MVVM

Axiom does not require:

```text
MVC
MVVM
MVP
Redux
Flux
```

as language-level architecture.

---

# 58. Recommended Boundary

For larger applications:

```text
Domain Model
     ↓
Application Store
     ↓
ViewModel / Bindings
     ↓
UI
```

---

# 59. Commands

620 formalizes the command model introduced in 619.

```text
Command
```

contains:

```text
id
label
can_execute
execute
undo
metadata
```

---

# 60. Command Execution

A command executes inside a transaction when it mutates application state.

---

# 61. CanExecute

`can_execute()` must be side-effect free.

---

# 62. Async Commands

Commands may return:

```text
Future<Result>
```

through 607.

---

# 63. Command Cancellation

Async commands accept cancellation tokens.

---

# 64. Command Progress

Commands may expose progress:

```text
Progress<T>
```

---

# 65. Command Failure

A failed command does not publish a partial state change.

---

# 66. Command Context

Execution receives:

```text
CommandContext
```

containing:

```text
store
transaction
cancellation
security context
diagnostics context
```

---

# 67. Command Parameters

Commands may be typed:

```text
Command<TInput, TOutput>
```

---

# 68. Command Validation

Input validation happens before mutation.

---

# 69. Command History

Executed commands can produce undo records.

---

# 70. Undo

Undo is represented by logical inverse state changes.

---

# 71. Undo Manager

```text
UndoManager
```

maintains:

```text
undo stack
redo stack
transaction groups
```

---

# 72. Undo Record

```text
UndoRecord {
    id
    description
    changes
    metadata
}
```

---

# 73. Undo Granularity

One user-visible logical operation should normally produce one undo record.

---

# 74. Typing Undo

Text controls may group multiple keystrokes according to configurable edit boundaries.

---

# 75. Compound Operations

Multiple operations can be grouped:

```text
UndoGroup.begin()
...
UndoGroup.commit()
```

---

# 76. Undo Failure

Undo can fail if the affected state no longer satisfies the expected version.

---

# 77. Undo Conflict

A conflict produces:

```text
UndoConflict
```

rather than silently corrupting state.

---

# 78. Redo

Redo reapplies a committed undo record.

---

# 79. New Mutation After Undo

A new divergent mutation clears the normal redo branch.

---

# 80. Branching History

Optional advanced history can retain divergent branches.

---

# 81. History Memory Budget

606 can constrain undo memory.

---

# 82. Persistent Undo

Undo history can optionally be serialized through 612.

---

# 83. Crash Recovery

600 may restore persisted undo history only when the application explicitly enables it.

---

# 84. Undo Security

Sensitive state should not automatically enter persistent undo history.

---

# 85. Sensitive State

State may be marked:

```text
Sensitive
NonPersistent
NoUndo
```

---

# 86. Validation

```text
Validator<T>
```

provides deterministic validation.

---

# 87. Validation Result

```text
Valid
Invalid
Pending
```

---

# 88. Validation Error

```text
ValidationError {
    code
    message
    field
    severity
}
```

---

# 89. Validation Message

User-visible validation text is localized through 617.

---

# 90. Async Validation

Remote validation can return `Pending` and complete asynchronously.

---

# 91. Stale Validation

Validation results include the input version.

A stale result must not overwrite newer validation state.

---

# 92. Collection State

```text
CollectionState<T>
```

supports observable collections.

---

# 93. Collection Changes

Changes use operations:

```text
Insert
Remove
Replace
Move
Reset
```

---

# 94. Range Changes

Large updates should support range operations.

---

# 95. Collection Version

Collection mutation increments a collection version.

---

# 96. Observable Map

Maps expose:

```text
Insert
Remove
Replace
```

events.

---

# 97. Observable Set

Sets expose:

```text
Add
Remove
```

events.

---

# 98. Collection Transactions

Multiple collection operations can be committed atomically.

---

# 99. UI Virtualization

619 list/tree/table controls consume collection change ranges.

---

# 100. Selection Stability

Selection can track stable item IDs rather than array indexes.

---

# 101. Stable Item Identity

Applications should provide:

```text
ItemId
```

when collection reordering matters.

---

# 102. Async State

```text
AsyncState<T>
```

represents asynchronous lifecycle.

---

# 103. Async States

```text
Idle
Loading
Ready
Refreshing
Failed
Cancelled
```

---

# 104. Async Versioning

Each async request has a generation.

---

# 105. Stale Completion

Older requests cannot overwrite newer state unless explicitly allowed.

---

# 106. Async Resource

```text
AsyncResource<T>
```

can cache the latest successful result.

---

# 107. Retry

Retry is explicit and policy controlled.

---

# 108. Retry Budget

606 resource limits apply to retries.

---

# 109. Async UI

619 binds `AsyncState<T>` to loading/error/content controls.

---

# 110. State Synchronization

620 supports synchronization between independent stores.

---

# 111. Synchronization Direction

Possible policies:

```text
OneWay
TwoWay
Merge
Authoritative
```

---

# 112. Conflict

Concurrent changes produce explicit conflict records.

---

# 113. No Silent Last-Write-Wins

Last-write-wins must be an explicit synchronization policy.

---

# 114. Version Vector Boundary

Distributed synchronization may use:

```text
Revision
LamportTimestamp
VectorClock
```

depending on application requirements.

These are not mandatory for local UI state.

---

# 115. Network Integration

Remote state updates arrive through 609/607.

---

# 116. IPC Integration

Local multi-process state synchronization uses 604.

---

# 117. Persistence

State snapshots use 600/612.

---

# 118. State Schema

Persistent application state has:

```text
schema_id
schema_version
state_version
```

---

# 119. Migration

State migrations are explicit functions.

---

# 120. Migration Failure

Failed migration leaves the original persisted state intact.

---

# 121. State Snapshot

A snapshot represents a consistent transaction boundary.

---

# 122. Incremental Persistence

Applications can persist only changed state fields/records.

---

# 123. Debounced Persistence

Persistence can be delayed/coalesced explicitly.

---

# 124. Durable Save

A save operation must define durability:

```text
Buffered
Durable
Synchronous
```

using 611 semantics.

---

# 125. Optimistic UI

The UI may display provisional state.

---

# 126. Provisional State

Provisional changes are tagged and cannot accidentally masquerade as durable state.

---

# 127. Commit/Reconcile

Remote confirmation can:

```text
Commit
Reject
Merge
```

the provisional change.

---

# 128. State Machine

A state machine can be built directly from typed state and commands.

No separate state-machine runtime is mandatory.

---

# 129. State Transitions

```text
State<T>.update(fn)
```

must be atomic within the current transaction.

---

# 130. Compare-and-Set

Concurrent stores may use:

```text
compare_exchange(version, mutation)
```

where appropriate.

---

# 131. UI Thread Safety

UI-bound state may be confined to the UI context.

---

# 132. Background State

Non-UI application stores can be accessed from worker tasks according to 608 synchronization semantics.

---

# 133. Thread-Affine State

A state object may declare:

```text
UiAffine
ThreadAffine
Concurrent
```

---

# 134. Concurrent State

Concurrent state must use 608 atomic/synchronization primitives.

---

# 135. No Hidden Locks

A state abstraction must not silently introduce a global mutex.

---

# 136. Scheduler Integration

Observers execute on an explicit executor/context.

---

# 137. Observer Executor

```text
observe(state, executor, callback)
```

---

# 138. Synchronous Observer

A local synchronous observer may execute during transaction commit.

---

# 139. Asynchronous Observer

An async observer receives changes through 607.

---

# 140. Backpressure

High-frequency observers can use:

```text
Latest
All
Coalesced
Sampled
```

delivery policies.

---

# 141. Event Loss

`Latest`/`Sampled` explicitly allow intermediate updates to be discarded.

---

# 142. Deterministic Delivery

`All` preserves committed change order.

---

# 143. Feedback Loop Detection

Reactive cycles can be detected using transaction/change origins.

---

# 144. Reactive Cycle Policy

A cycle must terminate through:

```text
NoChange
CycleError
ExplicitFixedPoint
```

rather than unlimited propagation.

---

# 145. Fixed Point

Advanced derived systems may explicitly request fixed-point evaluation with a bounded iteration count.

---

# 146. Bounded Reactive Work

A transaction has configurable computation/update budgets.

---

# 147. Resource Integration

606 accounts for:

```text
observer callbacks
derived computations
change queues
undo history
bindings
```

---

# 148. Diagnostics

602 records:

```text
transaction duration
observer count
derived recomputation
binding latency
undo depth
validation latency
```

---

# 149. Slow Observer

Development diagnostics can identify callbacks exceeding configured thresholds.

---

# 150. State Inspection

Debug tooling can inspect:

```text
state ID
version
owner
dependencies
observers
```

without exposing sensitive values.

---

# 151. Sensitive Diagnostics

Sensitive state values are redacted.

---

# 152. Serialization

State values use 612 serializers.

No reflection is required.

---

# 153. Schema Generation

The compiler can generate:

```text
.axstate
```

metadata.

---

# 154. AI-Readable State Metadata

`.axstate` may describe:

```text
state type
fields
versions
mutability
persistence
sensitivity
dependencies
```

---

# 155. Compiler Integration

The compiler can statically identify:

```text
State<T>
Derived<T>
Binding<T>
Command<T,U>
```

patterns.

---

# 156. Optimization

Known state dependencies can be compiled into direct invalidation edges.

---

# 157. Static Dependency Graph

When dependencies are explicit, no runtime graph discovery is necessary.

---

# 158. Runtime Dependency Graph

Dynamic derived state uses a compact graph.

---

# 159. Graph Memory

Dependency edges are generation-safe and explicitly owned.

---

# 160. Dead Stripping

Applications not using reactive state need not link the reactive subsystem.

---

# 161. Minimal Profile

A command-only application can use:

```text
Command
Transaction
UndoManager
```

without derived-state machinery.

---

# 162. UI Profile

A UI application can enable:

```text
State
Binding
Derived
Validation
Command
```

---

# 163. Editor Profile

An IDE/editor can additionally enable:

```text
Undo
Persistent State
Observable Collections
Selection Models
Async State
```

---

# 164. Dataflow Profile

Large data applications can use:

```text
Derived
Incremental
CollectionState
AsyncState
```

without 619.

---

# 165. Command/Event Separation

Commands represent requested actions.

Events represent facts that occurred.

---

# 166. Event

```text
Event<T>
```

is append-only notification.

---

# 167. Event Does Not Mutate Automatically

An event handler must explicitly change state.

---

# 168. Event Ordering

Within a transaction, emitted events have deterministic ordering.

---

# 169. Event Persistence

Events may optionally be persisted through 612.

---

# 170. Event Sourcing Boundary

620 supports the primitives required for event sourcing but does not require event sourcing.

---

# 171. Outbox

Transactional state changes can emit durable outbox records through 612.

---

# 172. Inbox

Incoming commands/events can be deduplicated through stable IDs.

---

# 173. Idempotency

Commands that may be retried can expose an idempotency key.

---

# 174. Security

Commands execute under the caller's capabilities.

---

# 175. Capability Propagation

A command cannot silently acquire additional capabilities through state binding.

---

# 176. Secret State

Secret values use 601/610 secure types.

---

# 177. Secret Binding

Password controls can bind to secure state without converting secrets into ordinary diagnostic strings.

---

# 178. Clipboard Interaction

Clipboard commands remain capability-aware through 619/603.

---

# 179. Persistence Security

State marked sensitive is excluded from automatic persistence unless explicitly overridden.

---

# 180. Undo Security

Sensitive changes are excluded from persistent undo by default.

---

# 181. Error Model

Errors include:

```text
StateError
TransactionError
ValidationError
BindingError
CommandError
UndoError
ConflictError
PersistenceError
CycleError
```

---

# 182. Error Atomicity

An error during a transactional mutation leaves committed state unchanged.

---

# 183. Panic Handling

A panic during a transaction rolls back uncommitted state when the implementation can guarantee rollback safety.

---

# 184. Non-Rollbackable Operations

External side effects must not be assumed reversible.

---

# 185. Side-Effect Boundary

Commands should separate:

```text
State Mutation
External Side Effect
```

when atomicity matters.

---

# 186. Effect Result

An effect may return a result that is then committed into state.

---

# 187. Example Architecture

```text
Command
   │
   ▼
Validate
   │
   ▼
Start Transaction
   │
   ├── mutate state
   ├── perform controlled effect
   └── generate changes
   │
   ▼
Commit
   │
   ├── bindings
   ├── derived state
   ├── UI
   └── undo history
```

---

# 188. Transaction Phases

```text
Prepare
Mutate
Validate
Commit
Publish
Schedule
```

---

# 189. Publish Barrier

Observers never see state between `Mutate` and `Commit`.

---

# 190. Reentrant Mutation

Observers should not synchronously mutate the same transaction unless explicitly using a nested mutation scope.

---

# 191. Deferred Mutation

An observer may schedule a later transaction through 607/619.

---

# 192. Collection Diff

Collection changes can expose:

```text
Diff<T>
```

for efficient UI updates.

---

# 193. Diff Operations

```text
Insert
Delete
Move
Update
Replace
Reset
```

---

# 194. Diff Correctness

A diff must transform the old logical collection into the new collection exactly.

---

# 195. Diff Optimization

The implementation may choose:

```text
IncrementalDiff
RangeDiff
Reset
```

based on cost.

---

# 196. Large Collection Strategy

Applications can disable expensive fine-grained diffing and publish range/reset changes.

---

# 197. Selection Synchronization

Selection state can observe collection diffs and remove invalid selections.

---

# 198. Focus Synchronization

UI focus is kept separate from application selection.

---

# 199. Navigation State

Navigation/history state can use ordinary State and Command primitives.

---

# 200. URL/Route State

Higher-level navigation frameworks may encode route state into 620 state.

---

# 201. Undo and Navigation

Navigation changes may opt into or out of undo history.

---

# 202. Persistence Policy

Each state field can specify:

```text
PersistNever
PersistSession
PersistUser
PersistApplication
```

---

# 203. State Scope

Scopes include:

```text
Local
Window
Session
Application
User
Machine
Deployment
```

---

# 204. Scope Resolution

State scope must not override security/configuration precedence defined by 601.

---

# 205. Configuration Boundary

Configuration belongs to 601.

Application runtime state belongs to 620.

---

# 206. Example Separation

```text
Config:
theme = dark

State:
current_document = 42
selected_item = 17
```

---

# 207. State vs Cache

Caches are not authoritative state.

---

# 208. Cache Invalidation

Cache invalidation may use state versions.

---

# 209. Content-Addressed State

Large immutable state blobs can use 613 CAS.

---

# 210. State Snapshot Hash

A deterministic snapshot can produce a content hash through 610/613.

---

# 211. Reproducibility

Given the same state snapshot and deterministic command sequence, the logical result must be reproducible.

---

# 212. Time

Time-dependent state must use explicit clocks from 607/602 rather than hidden system time when deterministic testing is required.

---

# 213. Randomness

Randomized state transitions must use explicit RNG sources.

---

# 214. Testing

620 provides:

```text
StateTestContext
```

with:

```text
fake clock
fake executor
deterministic transactions
```

---

# 215. Transaction Tests

Tests can assert:

```text
before == after
```

when a transaction fails.

---

# 216. Derived Tests

Tests verify dependency invalidation.

---

# 217. Binding Tests

Tests verify:

```text
model → UI
UI → model
```

without launching a real window.

---

# 218. Undo Tests

Every undo test verifies:

```text
initial
→ operation
→ undo
== initial
```

for reversible operations.

---

# 219. Redo Tests

```text
initial
→ operation
→ undo
→ redo
== post-operation
```

---

# 220. Property Testing

Property tests verify transactional atomicity and collection diffs.

---

# 221. Fuzzing

Fuzz:

```text
transaction sequences
observer graphs
binding graphs
derived graphs
undo histories
collection diffs
validation results
async completion ordering
```

---

# 222. Concurrency Tests

Concurrent state is tested with 608 memory-model stress tests.

---

# 223. Race Detection

Development builds may attach synchronization diagnostics.

---

# 224. Deterministic Async Tests

Async commands use a deterministic scheduler.

---

# 225. Stale Completion Tests

Tests ensure older async results cannot overwrite newer generations.

---

# 226. Persistence Tests

Tests cover:

```text
crash
partial write
migration failure
schema mismatch
corruption
```

using 611/612 fault injection.

---

# 227. Performance Targets

For simple scalar state:

- no heap allocation required for every read;
- O(1) version check;
- O(1) direct mutation before observers;
- bounded notification overhead.

---

# 228. Derived Performance

Static dependency graphs should avoid dynamic dependency discovery overhead.

---

# 229. UI Performance

Binding updates should invalidate only affected controls.

---

# 230. Undo Performance

Undo records should store compact logical changes rather than full application snapshots by default.

---

# 231. Snapshot Fallback

Applications may explicitly choose snapshot-based undo for complex operations.

---

# 232. Memory Budget

Undo, derived caches, observer queues and collection diffs are resource-accounted.

---

# 233. No Mandatory GC

All runtime structures use:

```text
explicit ownership
arena
pool
reference-counted ownership where explicitly chosen
generation-safe handles
```

according to the Axiom memory model.

---

# 234. Reference Semantics

620 does not expose raw pointer/reference complexity to ordinary application code.

---

# 235. Handle Semantics

Dynamic runtime objects are accessed through safe handles where necessary.

---

# 236. API Example

```text
struct DocumentStore {
    document: State<Document>
    selected: State<ItemId?>
    dirty: Derived<bool>
}

fn DocumentStore.save(self) -> Future<Result> {
    ...
}

fn DocumentStore.undo(self) {
    ...
}
```

---

# 237. UI Example

```text
struct EditorView {
    document: Binding<String>
    status: Binding<String>
    save: Command
}
```

---

# 238. Full Application Flow

```text
User Input
    ↓
619 / 618
    ↓
Command
    ↓
620 Transaction
    ↓
Domain State
    ↓
Derived State
    ↓
Bindings
    ↓
619 UI
    ↓
615 Rendering
```

---

# 239. External Data Flow

```text
Network / IPC / File
        ↓
609 / 604 / 611
        ↓
Deserialize
        ↓
Transaction
        ↓
State
        ↓
Derived / Binding
        ↓
UI
```

---

# 240. Architectural Invariants

1. State is typed.
2. State ownership is explicit.
3. Mutations are transactional where atomicity is required.
4. Observers never see partially committed state.
5. Derived state cannot loop indefinitely.
6. Bindings cannot recursively update forever.
7. Async results are generation-aware.
8. Validation cannot overwrite newer values.
9. Undo is logical rather than pixel-based.
10. Sensitive state is not persisted automatically.
11. No mandatory GC exists.
12. No mandatory reflection exists.
13. UI state is separate from domain state.
14. Configuration remains separate from runtime state.
15. Caches are not authoritative state.
16. External side effects are not assumed reversible.
17. Concurrent state follows 608 memory semantics.
18. Persistence follows 600/611/612 durability rules.
19. Commands do not automatically gain capabilities.
20. State changes are observable through deterministic change sets.
21. Large collections support range/diff updates.
22. UI binding updates remain incremental.
23. Resource usage is bounded through 606.
24. Diagnostics never expose secrets.
25. Static dependency information is preferred over runtime tracking when possible.

---

# 241. Acceptance Criteria

### State

1. State<T>.
2. MutableState<T>.
3. State identity.
4. generation safety.
5. versions.
6. change notifications.
7. subscriptions.
8. weak subscriptions.
9. explicit ownership.
10. scoped lifetime.

### Transactions

11. begin.
12. mutate.
13. validate.
14. commit.
15. rollback.
16. nested transactions.
17. atomic visibility.
18. ChangeSet.
19. ChangeSetId.
20. change causes.

### Derived State

21. Derived<T>.
22. explicit dependencies.
23. tracked dependencies.
24. lazy computation.
25. eager computation.
26. memoization.
27. dependency cache.
28. cycle detection.
29. bounded computation.
30. incremental derived state.

### Binding

31. Binding<T>.
32. one-way binding.
33. two-way binding.
34. conversion.
35. validation.
36. loop prevention.
37. version handling.
38. UI executor.
39. async binding.
40. binding diagnostics.

### Commands

41. typed command.
42. can_execute.
43. execute.
44. command context.
45. async command.
46. cancellation.
47. progress.
48. failure atomicity.
49. command metadata.
50. command routing.

### Undo

51. UndoManager.
52. UndoRecord.
53. redo.
54. grouping.
55. conflict detection.
56. divergent history.
57. memory budget.
58. persistent undo.
59. sensitive-state exclusion.
60. snapshot undo option.

### Collections

61. CollectionState.
62. observable list.
63. observable map.
64. observable set.
65. insert/remove/replace.
66. move.
67. range operations.
68. diffs.
69. stable item IDs.
70. selection synchronization.

### Async

71. AsyncState.
72. request generations.
73. stale completion prevention.
74. cancellation.
75. retry.
76. retry budgets.
77. loading state.
78. refreshing state.
79. error state.
80. scheduler integration.

### Persistence

81. state schema.
82. version.
83. migration.
84. snapshot.
85. incremental persistence.
86. durability mode.
87. crash recovery.
88. corruption handling.
89. CAS integration.
90. secure persistence.

### Security

91. capability propagation.
92. secret-state handling.
93. no automatic persistence.
94. no automatic undo.
95. diagnostic redaction.
96. command capability checks.
97. external data isolation.
98. trusted/untrusted boundaries.
99. resource limits.
100. plugin boundary.

### Testing

101. StateTestContext.
102. deterministic executor.
103. deterministic clock.
104. transaction tests.
105. binding tests.
106. derived-state tests.
107. undo tests.
108. redo tests.
109. diff tests.
110. fuzzing.

### Performance

111. scalar state fast path.
112. O(1) version check.
113. low-allocation notifications.
114. incremental invalidation.
115. static dependency optimization.
116. compact undo records.
117. virtualized collection support.
118. bounded queues.
119. no global lock.
120. dead stripping.

### Integration

121. 600 state.
122. 602 diagnostics.
123. 603 security.
124. 604 IPC.
125. 606 resources.
126. 607 async.
127. 608 synchronization.
128. 609 network.
129. 611 storage.
130. 612 serialization.
131. 613 package/CAS.
132. 617 text.
133. 619 GUI.

---

# 242. Final Architecture

```text
                       APPLICATION
                            │
                            ▼
                     DOMAIN MODEL
                            │
                            ▼
                         STORE
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           State          Command       AsyncState
             │              │              │
             ▼              ▼              ▼
          Derived       Transaction      Versioning
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                       ChangeSet
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Binding        Undo/Redo     Validation
              │
              ▼
             619
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
      UI     Text   Input
      │       │      │
      └───────┼──────┘
              ▼
             615
```

Cross-cutting:

```text
600  Persistence / Recovery
602  Diagnostics
603  Security
604  IPC
606  Resource Governor
607  Scheduler / Async
608  Synchronization
609  Networking
611  Storage
612  Serialization
613  Package / CAS
617  Text / Unicode
619  GUI
```

---

# 243. Architectural Decision

Axiom adopts **explicit reactive primitives rather than a mandatory reactive programming paradigm**.

This means an application can be:

```text
simple:
struct + functions
```

or:

```text
data-driven:
State + Binding + Command
```

or:

```text
complex:
Store + Derived + Transaction + Undo + Async + Persistence
```

without changing the underlying language model.

The compiler can optimize explicit dependency graphs into direct invalidation edges, while applications requiring dynamic dependency graphs can opt into runtime tracking.

The resulting architecture preserves Axiom's core objectives:

- native performance;
- explicit ownership;
- predictable execution;
- no mandatory GC;
- no mandatory reflection;
- no mandatory framework architecture;
- strong UI integration;
- efficient incremental updates;
- robust undo/redo;
- deterministic testing;
- native persistence and recovery.

---

# 244. Task Completion

**BOOTSTRAP-620 — COMPLETE**

**Next queued task: BOOTSTRAP-621 — Native Application Document Model, Editing Transactions, Command History, Autosave, Versioning, Diff/Merge & Collaborative State Runtime 5.0**
:::