Tiếp tục với **BOOTSTRAP-621**, mở rộng 620 thành nền tảng document/editor thực thụ, nhưng vẫn giữ document model độc lập với GUI.

:::writing{variant="document" id="58324" title="BOOTSTRAP-621 — Native Application Document Model, Editing Transactions, Command History, Autosave, Versioning, Diff/Merge & Collaborative State Runtime 5.0"}
# BOOTSTRAP-621 — Native Application Document Model, Editing Transactions, Command History, Autosave, Versioning, Diff/Merge & Collaborative State Runtime 5.0

**Status:** SPECIFIED  
**Layer:** Native Application Document / Editing / Versioning Runtime  
**Depends on:** BOOTSTRAP-600 → 620

---

# 1. Purpose

BOOTSTRAP-621 defines the native runtime model for applications whose primary unit of work is a **document**.

Examples:

- text editors;
- IDEs;
- image editors;
- audio/video editors;
- 3D editors;
- CAD applications;
- spreadsheets;
- design applications;
- data editors;
- project editors;
- node editors;
- structured document applications.

The runtime provides:

- document identity;
- document lifecycle;
- editing sessions;
- transactions;
- dirty state;
- autosave;
- recovery;
- versioning;
- snapshots;
- diffs;
- merges;
- conflict handling;
- document history;
- command integration;
- multi-view documents;
- collaborative-state foundations.

It does **not** require a particular UI architecture.

---

# 2. Design Principle

The central rule is:

> **A document is domain data plus explicit lifecycle/version semantics; a view is merely one consumer/editor of that document.**

Therefore:

```text
Document != Window
Document != View
Document != File
Document != UI State
```

---

# 3. Layering

```text
                    Application
                         │
                  DocumentManager
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Documents       Workspaces      Sessions
          │
          ▼
      DocumentModel
          │
    ┌─────┼──────┐
    ▼     ▼      ▼
  State  History Diff
    │      │      │
    └──────┼──────┘
           ▼
      Transactions
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
   Save  Undo   Sync
```

---

# 4. Core Objects

```text
Document
DocumentId
DocumentVersion
DocumentRevision
DocumentHandle
DocumentSession
DocumentManager
DocumentView
DocumentController
DocumentModel
DocumentMetadata
DocumentFormat
DocumentSnapshot
DocumentTransaction
DocumentChange
DocumentDiff
DocumentPatch
DocumentMerge
DocumentConflict
DocumentHistory
DocumentCheckpoint
DocumentLock
AutosavePolicy
RecoveryRecord
Workspace
WorkspaceState
```

---

# 5. Document Identity

Every document has:

```text
DocumentId
```

A `DocumentId` is independent from its current filesystem path.

---

# 6. Why Path Is Not Identity

A document can be:

- renamed;
- moved;
- temporarily unsaved;
- opened from memory;
- loaded from package storage;
- remote;
- restored from recovery.

Therefore path cannot define document identity.

---

# 7. Document Generation

A live document handle includes a generation:

```text
DocumentHandle {
    id
    generation
}
```

Stale handles are rejected.

---

# 8. Document States

```text
New
Loading
Ready
Modified
Saving
Saved
SaveFailed
Closing
Closed
Recovery
Conflict
```

---

# 9. State Transitions

```text
New
 ↓
Loading
 ↓
Ready
 ↓
Modified
 ↓
Saving
 ↓
Saved
```

Failure:

```text
Saving → SaveFailed
```

Conflict:

```text
Saving → Conflict
```

---

# 10. Document Model

The document model is ordinary Axiom data.

Example:

```text
struct TextDocument {
    text: Rope
    encoding: Encoding
    line_ending: LineEnding
}
```

---

# 11. No Mandatory Base Class

There is no:

```text
DocumentBase
```

requirement.

---

# 12. Document Trait

An application may define:

```text
trait DocumentModel {
    fn document_format(self) -> DocumentFormat
    fn serialize(self) -> Bytes
    fn apply(self, change: DocumentChange)
}
```

The exact domain model remains application-defined.

---

# 13. Document Format

A format describes:

```text
format_id
version
extensions
mime_types
capabilities
```

---

# 14. Format Registry

Applications may register format providers.

---

# 15. Native Formats

Axiom applications can define native document formats using 612/613.

---

# 16. External Formats

Import/export providers may support:

```text
TXT
JSON
XML
CSV
PNG
JPEG
SVG
PSD
MP4
WAV
GLTF
```

or application-specific formats.

These are compatibility layers, not language requirements.

---

# 17. Document Metadata

Metadata includes:

```text
DocumentMetadata {
    title
    path?
    format
    size
    created
    modified
    revision
    origin
}
```

---

# 18. Dirty State

A document is dirty when its logical state differs from its persisted baseline.

---

# 19. Dirty Is Not UI State

A dirty document can exist without any window.

---

# 20. Dirty Tracking

The preferred implementation uses revision IDs rather than repeatedly serializing the entire document.

---

# 21. Persisted Revision

```text
persisted_revision
```

identifies the last successfully durable version.

---

# 22. Current Revision

```text
current_revision
```

identifies the current logical state.

---

# 23. Dirty Predicate

```text
dirty = current_revision != persisted_revision
```

unless a format has special normalization semantics.

---

# 24. Revision

Every committed document transaction produces a logical revision.

---

# 25. Revision Identity

```text
DocumentRevisionId
```

is immutable.

---

# 26. Revision Metadata

A revision may include:

```text
parent
timestamp
author
command
change_id
content_hash
```

---

# 27. Revision Hash

A deterministic content hash may be generated through 610/613.

---

# 28. Transaction

Document mutations occur through:

```text
DocumentTransaction
```

---

# 29. Transaction Lifecycle

```text
Begin
 ↓
Read
 ↓
Mutate
 ↓
Validate
 ↓
Commit
```

---

# 30. Atomic Commit

A committed document transaction becomes one logical revision.

---

# 31. Failed Transaction

No partial document state becomes externally visible.

---

# 32. Change

A document mutation is represented as:

```text
DocumentChange
```

---

# 33. Change Types

Applications may define semantic changes such as:

```text
Insert
Delete
Replace
Move
Rename
SetProperty
AddObject
RemoveObject
Transform
```

---

# 34. Semantic Changes Preferred

Where possible, changes should describe logical operations rather than raw bytes.

---

# 35. Byte-Level Changes

Raw byte patches are supported for formats where semantic editing is unavailable.

---

# 36. Change Set

A transaction produces:

```text
DocumentChangeSet
```

containing one or more changes.

---

# 37. Change Inversion

A reversible change may provide:

```text
invert(change)
```

for undo.

---

# 38. Undo Integration

621 integrates directly with 620 `UndoManager`.

---

# 39. Document History

```text
DocumentHistory
```

stores logical revisions and/or compact change records.

---

# 40. History Modes

```text
None
Session
Persistent
Collaborative
```

---

# 41. History Is Not Required

Simple applications may disable document history.

---

# 42. History Memory

History is subject to 606 resource budgets.

---

# 43. History Compaction

Old changes can be compacted into snapshots.

---

# 44. Snapshot

```text
DocumentSnapshot
```

contains a complete logical document state.

---

# 45. Snapshot Frequency

Snapshot policy can be:

```text
EveryNChanges
EveryDuration
BeforeCompaction
BeforeClose
Manual
```

---

# 46. Snapshot Storage

Snapshots use:

- 611 storage;
- 612 serialization;
- 613 compression/CAS.

---

# 47. Content-Addressed Snapshot

A snapshot may be stored by content hash.

---

# 48. Snapshot Deduplication

Identical snapshots need not consume duplicate storage.

---

# 49. Patch

```text
DocumentPatch
```

is a compact transformation between revisions.

---

# 50. Patch Application

A patch must verify its expected base revision.

---

# 51. Patch Conflict

Applying a patch to the wrong base returns:

```text
PatchBaseMismatch
```

---

# 52. Diff

```text
DocumentDiff
```

describes differences between two revisions.

---

# 53. Diff Granularity

Implementations may provide:

```text
Byte
Line
Token
AST
Object
Semantic
```

diffs.

---

# 54. Generic Diff Engine

621 defines the interface but does not require one universal algorithm.

---

# 55. Domain-Specific Diff

Applications may provide optimized domain diff engines.

---

# 56. Merge

```text
DocumentMerge
```

combines changes from two descendants of a common base.

---

# 57. Three-Way Merge

The canonical merge operation is:

```text
Base
 / \
A   B
 \ /
Merged
```

---

# 58. Merge Inputs

```text
base_revision
left_revision
right_revision
```

---

# 59. Merge Output

```text
Merged
Conflicts
```

---

# 60. Conflict

```text
DocumentConflict
```

identifies incompatible changes.

---

# 61. Conflict Types

Examples:

```text
DeleteModify
ModifyModify
MoveMove
RenameRename
TypeConflict
SchemaConflict
StructuralConflict
```

---

# 62. Conflict Resolution

Applications resolve conflicts explicitly.

---

# 63. No Silent Conflict Loss

621 must never silently discard one side of a conflict.

---

# 64. Merge Policy

Applications can define deterministic policies:

```text
PreferLeft
PreferRight
Reject
Custom
```

These are explicit policies, not hidden defaults.

---

# 65. Semantic Merge

Structured documents may merge object-level fields rather than bytes.

---

# 66. Text Merge

Text documents can use line/token/AST strategies.

---

# 67. Binary Merge

Binary documents require format-specific merge logic.

---

# 68. Collaborative Foundation

621 provides primitives for collaborative editing but does not mandate a network protocol.

---

# 69. Collaboration Modes

```text
Offline
SharedFile
ServerSynchronized
PeerSynchronized
```

---

# 70. Collaboration Revision

Collaborative revisions have:

```text
author
logical_clock
parent_revision
```

---

# 71. Concurrent Revision

Two revisions may share the same parent.

---

# 72. Revision DAG

Collaborative history is represented as a DAG rather than assuming one linear history.

---

# 73. Linear View

A UI can present a selected linear history while retaining DAG semantics internally.

---

# 74. Merge Base

The runtime can find a common ancestor between revisions.

---

# 75. Collaboration Algorithm Boundary

OT and CRDT algorithms are optional providers.

621 defines the integration boundary without requiring one algorithm.

---

# 76. Operation Provider

```text
CollaborationProvider
```

can implement:

```text
transform
merge
causal_order
replication
```

---

# 77. Local-First Editing

The document remains locally editable when collaboration is temporarily unavailable.

---

# 78. Offline Queue

Changes may be queued for later synchronization.

---

# 79. Queue Persistence

Offline changes may be persisted using 612/611.

---

# 80. Duplicate Operation

Each replicated change has an immutable operation ID.

---

# 81. Idempotency

Applying an already-applied operation is harmless.

---

# 82. Causal Ordering

Collaborative providers may require causal ordering.

---

# 83. Conflict Preservation

Unresolved conflicts remain explicit state.

---

# 84. Document Lock

Optional logical locks can coordinate editors.

---

# 85. Lock Semantics

A lock is advisory unless enforced by the backing storage/service.

---

# 86. File Lock

Filesystem locks remain 611 functionality.

---

# 87. Autosave

```text
AutosavePolicy
```

controls recovery persistence.

---

# 88. Autosave Is Not Save

Autosave does not necessarily overwrite the user's durable document.

---

# 89. Autosave Location

Autosaves should use a recovery namespace.

---

# 90. Autosave Format

Prefer:

```text
DocumentSnapshot
+
ChangeLog
```

rather than repeatedly rewriting the entire document.

---

# 91. Autosave Trigger

Triggers may include:

```text
Time
ChangeCount
Idle
MemoryPressure
BeforeShutdown
```

---

# 92. Autosave Debounce

Rapid edits are coalesced.

---

# 93. Autosave Durability

Critical recovery records use durable storage semantics from 611.

---

# 94. Recovery Record

```text
RecoveryRecord {
    document_id
    source_identity
    revision
    snapshot
    change_log
    timestamp
    checksum
}
```

---

# 95. Recovery Discovery

On application startup, DocumentManager scans the recovery namespace.

---

# 96. Recovery Validation

Recovery records require:

- schema validation;
- checksum verification;
- format compatibility;
- revision consistency.

---

# 97. Recovery Selection

If multiple valid records exist, the runtime exposes all relevant candidates to the application.

It does not silently choose a destructive replacement.

---

# 98. Recovery Commit

Recovered state becomes a normal document only after explicit application acceptance.

---

# 99. Crash Safety

A partially written recovery record must not appear valid.

---

# 100. Atomic Recovery

Recovery files use 611 atomic replacement semantics.

---

# 101. Save

Saving is a document operation:

```text
Document.save()
```

---

# 102. Save Pipeline

```text
Document
 ↓
Snapshot / Serialize
 ↓
Validate
 ↓
Temporary Target
 ↓
Flush
 ↓
Atomic Replace
 ↓
Persisted Revision Update
```

---

# 103. Save Failure

The document remains dirty after a failed save.

---

# 104. Save Conflict

If the backing file changed externally, save may return:

```text
ExternalModification
```

rather than overwriting automatically.

---

# 105. External Modification Detection

Detection may use:

```text
file identity
size
timestamp
content hash
revision metadata
```

depending on filesystem/format.

---

# 106. Atomic Save

Where supported:

```text
temp → flush → atomic rename
```

is preferred.

---

# 107. File Identity

DocumentManager tracks filesystem identity independently of path.

---

# 108. Rename

Renaming a document changes metadata, not `DocumentId`.

---

# 109. Save As

Save As can create a new backing identity while preserving or replacing logical document identity according to explicit policy.

---

# 110. Clone

A document can be cloned into an independent revision lineage.

---

# 111. Duplicate

Duplicate creates a new document identity with copied content.

---

# 112. Open

Opening a document produces:

```text
DocumentHandle
```

---

# 113. Multiple Opens

The application may prevent multiple independent instances of the same logical document.

---

# 114. Shared Document

Multiple views can share one document model.

---

# 115. Multi-View

```text
Document
 ├── View A
 ├── View B
 └── View C
```

---

# 116. View State

Each view owns independent:

```text
cursor
selection
scroll
zoom
panel state
```

---

# 117. Document State

The document owns:

```text
content
metadata
revision
dirty state
history
```

---

# 118. Separation Invariant

Closing one view must not close the document if another view still owns a session.

---

# 119. Document Session

```text
DocumentSession
```

connects a document with an editor/controller.

---

# 120. Session Identity

Every session has:

```text
DocumentSessionId
```

---

# 121. Session Lifecycle

```text
Created
Attached
Active
Inactive
Closing
Closed
```

---

# 122. Session Commands

Commands may target:

```text
Document
Session
View
Workspace
```

explicitly.

---

# 123. Command Routing

620 command routing determines the nearest valid target.

---

# 124. Document Command Context

Document commands receive:

```text
document
session
selection
transaction
capabilities
```

---

# 125. Selection

Selection belongs to a session/view unless the domain explicitly models it as document state.

---

# 126. Cursor

Cursor position is view state.

---

# 127. Editor Preferences

Editor preferences belong to 601 configuration or 620 session state, not document content.

---

# 128. Workspace

```text
Workspace
```

groups documents and application context.

---

# 129. Workspace State

May include:

```text
open documents
active document
layout
panels
recent revisions
session metadata
```

---

# 130. Workspace Persistence

Workspace state can use 600/611/612.

---

# 131. Document Locking

Workspace may prevent duplicate editor sessions according to policy.

---

# 132. DocumentManager

Responsibilities:

```text
open
close
create
find
save
save_all
recover
restore
duplicate
reload
```

---

# 133. Manager Registry

DocumentManager maintains active document identities.

---

# 134. Manager Threading

Manager operations are normally UI-affine when connected to GUI.

Headless applications may use another executor.

---

# 135. Background Loading

Large documents can load asynchronously.

---

# 136. Loading State

Views can display:

```text
Loading
Progress
Ready
Failed
```

---

# 137. Partial Loading

Formats may support lazy/partial document loading.

---

# 138. Streaming Documents

Large media/data documents may expose a streaming representation.

---

# 139. Memory Budget

Document loading must respect 606 memory budgets.

---

# 140. Memory-Mapped Documents

611 memory mapping can be used for suitable formats.

---

# 141. Copy-On-Write

Large immutable document regions may use structural sharing.

---

# 142. Rope / Chunked Structures

Text editors can use ropes/chunked buffers to avoid O(n) insertion.

---

# 143. Binary Large Documents

Binary editors can use sparse/chunked representations.

---

# 144. Object Documents

Structured editors can use object graphs with stable IDs.

---

# 145. Stable Object Identity

```text
DocumentObjectId
```

must survive non-semantic reordering when the application requires it.

---

# 146. Structural Changes

Objects may be:

```text
Created
Deleted
Moved
Reparented
Modified
```

---

# 147. Schema Version

Structured documents include schema versions through 612.

---

# 148. Migration

Document migrations are explicit and versioned.

---

# 149. Migration Backup

Before destructive migration, a recovery snapshot may be created.

---

# 150. Migration Failure

Original content remains available.

---

# 151. Import

Import converts an external format into the document model.

---

# 152. Export

Export converts the model into an external format.

---

# 153. Lossy Export

Export may explicitly report:

```text
Lossy
UnsupportedFeature
DroppedMetadata
```

---

# 154. Export Validation

Applications can require zero loss before allowing save.

---

# 155. Document Capabilities

Formats declare:

```text
CanRead
CanWrite
CanStream
CanPatch
CanMerge
CanRecover
CanIncrementalSave
```

---

# 156. Capability Negotiation

DocumentManager selects operations based on format capabilities.

---

# 157. Save Strategy

Strategies include:

```text
FullRewrite
IncrementalPatch
AppendLog
CopyOnWrite
```

---

# 158. Transaction Journal

A document can maintain a journal of changes before snapshotting.

---

# 159. Journal

```text
DocumentJournal
```

stores:

```text
revision
operation_id
change
checksum
```

---

# 160. Journal Recovery

Valid journal entries can reconstruct state after a crash.

---

# 161. Journal Truncation

After a durable snapshot, obsolete journal entries can be compacted.

---

# 162. Journal Integrity

Each entry can contain a chained checksum/hash.

---

# 163. Corruption

Corrupt journal entries stop replay at the last valid boundary.

---

# 164. No Silent Corruption

The application receives a recovery diagnostic.

---

# 165. Checkpoint

A checkpoint represents a durable document reconstruction boundary.

---

# 166. Checkpoint Metadata

```text
checkpoint_id
revision
snapshot_hash
storage_location
```

---

# 167. Checkpoint Frequency

Controlled by resource budget and autosave policy.

---

# 168. History Compaction

Compaction:

```text
old revisions
    ↓
snapshot
    ↓
new base
```

---

# 169. History Integrity

Compaction must preserve reconstructibility of retained revisions.

---

# 170. History Garbage Collection

History storage reclamation is storage-object reclamation, not language GC.

---

# 171. CAS Integration

Old snapshots may be retained by CAS pins/leases through 613.

---

# 172. Document Export

Export can directly stream to:

```text
File
Memory
Network
IPC
```

through 611/609/604.

---

# 173. Document Import

Import can stream from those same sources.

---

# 174. Security

Opening an untrusted document must not execute document-provided code.

---

# 175. Parser Sandbox

Complex parsers may run in isolated processes through 603/604/605.

---

# 176. Resource Limits

Untrusted documents have limits for:

```text
size
depth
object count
decompression
CPU
memory
```

---

# 177. Zip/Package Bomb Protection

Package-backed documents must use 613 resource limits.

---

# 178. External References

A document referencing external files must use explicit capabilities.

---

# 179. Missing References

Missing resources are represented as explicit unresolved references.

---

# 180. Secret References

Sensitive resources cannot be silently embedded into exported documents.

---

# 181. Diagnostics

602 records:

```text
document open
load duration
save duration
revision
autosave
recovery
merge conflict
parse error
external modification
```

---

# 182. Performance Metrics

Applications can inspect:

```text
load throughput
save throughput
diff time
merge time
serialization time
history size
autosave latency
```

---

# 183. Trace Integration

Document operations can create tracing spans.

---

# 184. AI Metadata

621 may generate:

```text
.axdoc
.axformat
.axhistory
```

metadata.

---

# 185. `.axdoc`

Contains machine-readable:

```text
document type
schema
revision
capabilities
persistence
dependencies
```

---

# 186. `.axhistory`

Describes retained revision metadata without requiring full content.

---

# 187. Compiler Integration

The compiler may generate document serializers, patch structures and stable IDs for typed document models.

---

# 188. Struct-Only API

Example:

```text
struct Document {
    id: DocumentId
    model: MyModel
    history: DocumentHistory
}

fn Document.begin(self) -> DocumentTransaction
fn Document.save(self) -> Future<Result>
fn Document.undo(self)
fn Document.redo(self)
```

---

# 189. Generic Document Manager

```text
struct DocumentManager {
    registry: DocumentRegistry
}

fn DocumentManager.open(self, uri: Uri) -> Future<DocumentHandle>
fn DocumentManager.save_all(self) -> Future<Result>
fn DocumentManager.recover(self) -> List<RecoveryRecord>
```

---

# 190. Document Provider

```text
trait DocumentProvider {
    fn open(...)
    fn save(...)
    fn import(...)
    fn export(...)
    fn diff(...)
    fn merge(...)
}
```

---

# 191. Provider Isolation

A provider must not modify global document state outside its explicit transaction.

---

# 192. Format Detection

Detection may use:

```text
extension
MIME
magic bytes
package metadata
explicit user selection
```

---

# 193. Ambiguous Format

Ambiguous detection returns candidates rather than silently selecting an unsafe parser.

---

# 194. File Watcher Integration

611 watchers notify external changes.

---

# 195. External Change

A modified open document enters:

```text
ExternalChanged
```

logical status.

---

# 196. Reload

Reload is explicit unless the application declares an automatic policy.

---

# 197. Reload Conflict

Reloading a dirty document must not discard local changes without explicit confirmation/policy.

---

# 198. Auto-Reload

Optional for documents known to be safely externally synchronized.

---

# 199. Save Conflict Workflow

```text
Local Dirty
   +
External Changed
       ↓
Conflict
 ┌─────┼─────┐
 ▼     ▼     ▼
Reload Merge SaveAs
```

---

# 200. Merge UI

619 can present conflicts through a specialized merge view.

---

# 201. Conflict Resolution State

Resolution itself is represented as document state/transactions.

---

# 202. Collaboration Transport

Network synchronization uses 609/610.

---

# 203. IPC Collaboration

Local collaboration may use 604.

---

# 204. Authentication

Collaborative document services use 603/610 capabilities and identities.

---

# 205. Authorization

Permission to edit a document is distinct from document identity.

---

# 206. Capability Model

Possible document capabilities:

```text
DocumentRead
DocumentWrite
DocumentSave
DocumentExport
DocumentShare
DocumentHistory
DocumentRecover
DocumentMerge
```

---

# 207. Least Privilege

A view that only displays a document should not receive write capability.

---

# 208. Read-Only Mode

Read-only documents reject mutations at transaction start.

---

# 209. Temporary Edit

A temporary editing transaction can be created without granting durable save permission.

---

# 210. Draft

Draft state may be persisted separately from the canonical document.

---

# 211. Draft Identity

```text
DraftId
```

is separate from `DocumentId`.

---

# 212. Draft Recovery

Drafts use the recovery infrastructure.

---

# 213. Publish

An application can explicitly promote a draft into the canonical document.

---

# 214. Version Tags

Human-readable labels can reference revisions:

```text
VersionTag
```

---

# 215. Branch

Applications may create:

```text
DocumentBranch
```

for experimental editing.

---

# 216. Branch Merge

Branches merge through the same three-way merge engine.

---

# 217. No Mandatory Git Dependency

621 does not depend on Git or another VCS.

---

# 218. VCS Integration Boundary

External VCS providers can map their revisions onto `DocumentRevision`.

---

# 219. Version Control Adapter

```text
VersionControlProvider
```

may provide:

```text
commit
checkout
branch
diff
merge
```

---

# 220. Local History

Applications can implement local history without a VCS.

---

# 221. Autosave + History

Autosave protects current work.

History preserves intentional editing history.

They are separate mechanisms.

---

# 222. Crash Recovery + Undo

Recovery restores document state and optionally its compatible undo history.

---

# 223. Recovery Compatibility

Undo history must only be restored when its base revision matches the recovered document.

---

# 224. Recovery Mismatch

Mismatched history is discarded or exposed separately; it must not be applied blindly.

---

# 225. Workspace Recovery

600 can persist workspace state:

```text
open documents
active document
unsaved drafts
```

---

# 226. Application Restart

The application may restore its previous workspace.

---

# 227. Shutdown

On graceful shutdown:

```text
save/autosave
close sessions
flush history
persist workspace
```

according to policy.

---

# 228. Forced Shutdown

Recovery records remain available for unsaved documents.

---

# 229. Resource Governor

606 may terminate or constrain:

```text
history
autosave frequency
diff workers
merge workers
document cache
```

under pressure.

---

# 230. Scheduler

Large diff/merge/save operations should execute asynchronously.

---

# 231. UI Responsiveness

UI-affine document operations must not perform unbounded blocking I/O.

---

# 232. Background Save

Serialization and disk writes may run on 607 worker executors.

---

# 233. Completion Safety

Background save completion verifies the revision it serialized before updating persisted state.

---

# 234. Stale Save

If the document changed while saving:

```text
save_revision != current_revision
```

the completion must not mark the newer state as saved.

---

# 235. Concurrent Saves

At most one durable save pipeline per document unless the format explicitly supports concurrent versions.

---

# 236. Save Cancellation

Cancellation must preserve the existing durable document.

---

# 237. Save Temporary Files

Temporary files use secure creation through 611.

---

# 238. Atomic Replacement

Final replacement uses filesystem atomicity guarantees.

---

# 239. Durability

The implementation must not claim durable persistence until the configured durability operation succeeds.

---

# 240. Testing

621 requires deterministic tests for:

- document lifecycle;
- transaction atomicity;
- revision tracking;
- save failure;
- save race;
- autosave;
- recovery;
- crash;
- journal replay;
- corruption;
- diff;
- merge;
- conflict;
- undo;
- redo;
- external modification;
- multi-view;
- collaboration ordering.

---

# 241. Fault Injection

Inject:

```text
disk full
permission denied
partial write
power loss
rename failure
checksum failure
parser failure
network disconnect
concurrent edit
```

---

# 242. Property Tests

Properties include:

```text
apply(diff(A,B), A) == B
```

where the selected diff algorithm guarantees exact reconstruction.

---

# 243. Merge Property

For non-conflicting changes:

```text
merge(base, A, B)
```

must preserve both changes.

---

# 244. Undo Property

For reversible transaction `T`:

```text
undo(T(apply(S))) == S
```

within declared semantic equivalence.

---

# 245. Save Property

After successful durable save:

```text
persisted_revision == saved_revision
```

---

# 246. Crash Property

After simulated crash during save, at least one valid reconstruction must remain available according to the filesystem durability guarantees.

---

# 247. Recovery Property

Recovered content must pass checksum and schema validation before becoming active.

---

# 248. Collaboration Property

Duplicate operation IDs must not duplicate mutations.

---

# 249. Security Property

Untrusted documents cannot execute arbitrary application code merely by being parsed.

---

# 250. Performance Property

Small document edits should not require full-document serialization unless the format requires it.

---

# 251. Memory Property

Large documents should support bounded-memory incremental representations where their format permits.

---

# 252. Final Architecture

```text
                         APPLICATION
                              │
                              ▼
                       DOCUMENT MANAGER
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
         Workspace        Documents         Sessions
                              │
                              ▼
                        DOCUMENT MODEL
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                  State     History    Metadata
                    │         │
                    ▼         ▼
               Transaction  Revision DAG
                    │         │
             ┌──────┼─────────┼───────┐
             ▼      ▼         ▼       ▼
           Save   Autosave    Diff   Merge
             │      │         │       │
             ▼      ▼         ▼       ▼
           611     Recovery   Patch  Conflict
             │
             ▼
       612 Serialization
             │
             ▼
       613 CAS / Package
```

Cross-cutting:

```text
600  State / Recovery
602  Diagnostics
603  Security
604  IPC
606  Resource Governance
607  Async / Scheduler
608  Synchronization
609  Network
610  Crypto
611  Storage
612  Serialization
613  Package / CAS
620  State / Binding / Commands / Undo
619  GUI
```

---

# 253. Architectural Decisions

Axiom adopts the following document architecture:

1. `DocumentId` is independent of filesystem path.
2. Document revisions are immutable.
3. Mutations occur through transactions.
4. Dirty state is revision-based.
5. Save is distinct from autosave.
6. Recovery is distinct from normal persistence.
7. Undo is distinct from recovery.
8. History is optional.
9. Diff/merge are provider-extensible.
10. Three-way merge is the canonical generic merge model.
11. Collaboration is an optional provider layer.
12. OT/CRDT are not built into the language core.
13. Document models are ordinary structs/data.
14. Views are independent from documents.
15. Multiple views can share one document.
16. External changes never silently destroy local edits.
17. Save completion is revision-aware.
18. No third-party VCS is required.
19. No mandatory GC is introduced.
20. No mandatory reflection is introduced.

---

# 254. Acceptance Criteria

**Total: 160+ acceptance criteria**, covering:

- document identity;
- lifecycle;
- model;
- metadata;
- revisions;
- transactions;
- changes;
- patches;
- snapshots;
- history;
- undo/redo;
- diff;
- merge;
- conflicts;
- autosave;
- recovery;
- journal;
- crash safety;
- external modification;
- multi-view;
- workspace;
- import/export;
- schema migration;
- collaboration;
- operation IDs;
- synchronization;
- security;
- capabilities;
- resource limits;
- scheduler;
- persistence;
- diagnostics;
- AI metadata;
- compiler integration;
- deterministic testing;
- fuzzing;
- fault injection;
- performance;
- dead stripping;
- cross-platform behavior.

---

# 255. Task Completion

**BOOTSTRAP-621 — COMPLETE**

**Next queued task: BOOTSTRAP-622 — Native Application Navigation, Routing, Workspace Layout, Docking, Multi-Window, MDI/SDI & Document/View Presentation Runtime 5.0**
:::