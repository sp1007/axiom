# BOOTSTRAP-798 — AXVCS
## Native Axiom Version Control Abstraction, Content-Addressed Repository, Semantic Revision/Branch/Tag Transport, Distributed Object Store, Repository Protocol, Commit/Fetch/Push/Pull, Conflict-Aware Integration, Sparse/Partial History, CAS Storage, Pack/Delta Compression, Repository Integrity & Version-Control ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXVCS`  
**ABI:** `AXVCS_ABI_1`  
**Schema:** `AXVCS_SCHEMA_1`  
**Artifact:** `.axrepo`

**Dependencies:**

```text
AXHISTORY
AXMERGE
AXPATCH
AXDIFF
AXOBJECT
AXBINARY
AXABI
AXBUILD
AXPACKAGE
AXTEST
AXCRYPTO
AXIDE
```

---

# 1. Mục tiêu

`AXVCS` là lớp **repository và synchronization** native của Axiom.

Nó không thay thế:

- `AXHISTORY` — semantic history;
- `AXMERGE` — semantic merge;
- `AXPATCH` — patch application;
- `AXDIFF` — difference analysis.

AXVCS cung cấp:

```text
repository
object storage
refs
branch/tag transport
commit storage
fetch/push/pull
remote synchronization
CAS
packfiles
partial clone
sparse checkout
integrity
locking
authentication boundary
```

Kiến trúc tổng thể:

```text
                    AXVCS
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
 Repository       Object Store    Transport
       │              │              │
       ▼              ▼              ▼
   AXHISTORY         CAS         Remote
       │
       ├── AXMERGE
       ├── AXPATCH
       └── AXDIFF
```

---

# 2. Boundary

AXVCS **owns**:

```text
Repository
Object
ObjectStore
Ref
BranchRef
TagRef
RemoteRef
Pack
Transport
Fetch
Push
Pull
Clone
Integrity
GC
Lock
RepositoryConfig
```

AXVCS **does not own**:

```text
type checking
compiler semantics
source merge
semantic diff
patch semantics
ABI rules
build execution
package resolution
authentication policy
UI
```

---

# 3. Core design principle

Axiom không thiết kế VCS dựa trên:

```text
file → line → commit
```

mà:

```text
content
   ↓
semantic snapshot
   ↓
revision
   ↓
content-addressed repository
```

Do đó:

```text
AXHISTORY
      ↓
RevisionId
      ↓
AXVCS
      ↓
Object Store
```

---

# 4. Repository model

Một repository:

```text
Repository {
    id
    format_version
    config
    refs
    object_store
    remotes
    capabilities
}
```

---

# 5. Repository identity

```text
RepositoryId =
hash(
    schema,
    repository_namespace
)
```

Repository identity không được phụ thuộc vào:

- filesystem path;
- hostname;
- username;
- branch name.

---

# 6. Object model

Tất cả object đều content-addressed.

```text
Object {
    id: ObjectId
    kind: ObjectKind
    size
    payload
}
```

`ObjectId`:

```text
ObjectId =
HASH(
    domain_separator,
    schema,
    kind,
    canonical_payload
)
```

---

# 7. Object kinds

Core:

```text
enum ObjectKind {
    BLOB
    TREE
    SEMANTIC
    PATCH
    REVISION
    PACK_INDEX
    METADATA
}
```

Native binary artifacts chỉ được lưu nếu repository policy cho phép.

---

# 8. Blob

`BLOB` chứa raw bytes:

```text
Blob {
    bytes
}
```

Ví dụ:

```text
source.ax
image
documentation
configuration
```

---

# 9. Tree

Tree biểu diễn filesystem namespace:

```text
Tree {
    entries[]
}
```

Entry:

```text
TreeEntry {
    name
    kind
    object_id
    mode
}
```

---

# 10. Canonical tree ordering

Entries phải được canonicalize:

```text
sort(
    normalized_name,
    entry_kind
)
```

Không phụ thuộc filesystem ordering.

---

# 11. Unicode filenames

Axiom hỗ trợ UTF-8.

Repository phải xác định canonical filename policy để tránh:

```text
NFC vs NFD
case sensitivity
platform-specific normalization
```

Repository identity phải bảo toàn sự khác biệt nếu policy coi chúng là khác nhau.

---

# 12. Semantic object

`SEMANTIC` tham chiếu dữ liệu từ AXHISTORY:

```text
SemanticObject {
    schema
    semantic_root
}
```

Không duplicate semantic database không cần thiết.

---

# 13. Revision object

```text
RevisionObject {
    revision_id
    parents[]
    root_tree
    semantic_root
    patch_set
    metadata
}
```

Revision semantics thuộc AXHISTORY.

AXVCS chỉ serialize/store/transport.

---

# 14. Ref

Ref là mutable pointer:

```text
Ref {
    name
    target
}
```

Ví dụ:

```text
refs/heads/main
refs/heads/dev
refs/tags/v1.0
```

---

# 15. Ref identity

Ref name không nằm trong RevisionId.

Do đó:

```text
main → R10
dev  → R10
```

không tạo revision mới.

---

# 16. Branch

Branch:

```text
Branch {
    name
    head: RevisionId
}
```

Branch là mutable.

Revision là immutable.

---

# 17. Tag

Tag:

```text
Tag {
    name
    target: RevisionId
    metadata
}
```

Annotated tag có metadata riêng.

---

# 18. Immutable tag policy

Repository có thể khai báo:

```text
tag_policy = IMMUTABLE
```

Khi đó:

```text
v1.0 → R10
```

không thể chuyển sang R11 nếu không có explicit administrative override.

---

# 19. HEAD

Repository có:

```text
HEAD
```

trỏ tới:

```text
branch
```

hoặc detached:

```text
RevisionId
```

---

# 20. Working tree

AXVCS không coi working tree là semantic truth.

Model:

```text
WORKING TREE
     ↓
AXCOMPILER
     ↓
semantic snapshot
     ↓
AXHISTORY
     ↓
AXVCS commit
```

---

# 21. Index/staging

Axiom không bắt buộc Git-style staging area.

Có thể có:

```text
StagingSnapshot
```

nhưng semantic commit có thể trực tiếp tạo từ:

```text
working tree
+ selected changes
```

thông qua AXPATCH/AXDIFF.

---

# 22. Change selection

User có thể commit:

```text
module A
symbol X
property Y
```

thay vì chỉ:

```text
file A
```

Đây là điểm khác biệt quan trọng của AXVCS.

---

# 23. Semantic staging

```text
StageSelection {
    files[]
    symbols[]
    changes[]
}
```

Compiler/AXDIFF xác định semantic boundaries.

---

# 24. Commit pipeline

```text
Working Tree
     ↓
AXCOMPILER
     ↓
Semantic Snapshot
     ↓
AXDIFF
     ↓
Change Set
     ↓
AXPATCH
     ↓
AXHISTORY
     ↓
Revision
     ↓
AXVCS
     ↓
Object Store
```

---

# 25. Commit operation

Conceptual:

```text
commit(
    base_revision,
    working_snapshot,
    selection,
    metadata
)
```

Kết quả:

```text
RevisionId
```

---

# 26. Atomic commit

Commit phải atomic:

```text
either:
    all referenced objects + revision + ref
exist

or:
    repository state remains unchanged
```

Không được tạo branch trỏ vào revision chưa đầy đủ.

---

# 27. Object transaction

```text
ObjectTransaction {
    staged_objects
    expected_refs
    commit()
    abort()
}
```

---

# 28. Ref transaction

Atomic ref update:

```text
RefTransaction {
    expected_old
    new_value
}
```

---

# 29. Compare-and-swap ref

```text
update_ref(
    ref,
    expected_old,
    new_revision
)
```

Nếu current ref khác `expected_old`:

```text
REF_CONFLICT
```

Không overwrite silent.

---

# 30. Concurrent commits

Hai client:

```text
A: R10 → R11
B: R10 → R12
```

cả hai có thể commit local.

Push chỉ thành công khi remote ref vẫn:

```text
R10
```

Nếu remote đã thành:

```text
R11
```

B phải integrate.

---

# 31. Push

```text
LOCAL
  │
  ├── discover remote state
  │
  ├── compute object closure
  │
  ├── send missing objects
  │
  ├── validate
  │
  └── atomic ref update
       ↓
REMOTE
```

---

# 32. Push must not mutate source

Push chỉ:

```text
transfer objects
update remote refs
```

Không tự sửa working tree.

---

# 33. Fetch

```text
REMOTE
  ↓
advertised refs
  ↓
object negotiation
  ↓
missing objects
  ↓
LOCAL object store
  ↓
remote-tracking refs
```

---

# 34. Remote-tracking refs

Ví dụ:

```text
refs/remotes/origin/main
```

là local reference.

Nó không tự động thay đổi local branch.

---

# 35. Pull

Canonical:

```text
fetch
  ↓
integrate
  ↓
merge/rebase policy
```

AXVCS fetches.

AXMERGE performs semantic merge.

AXPATCH performs rebase/application where appropriate.

---

# 36. Pull must not silently merge

Repository policy:

```text
pull_policy:
    FAST_FORWARD
    MERGE
    REBASE
    PROMPT
```

Nếu policy không cho phép automatic integration:

```text
PULL_REQUIRES_INTEGRATION
```

---

# 37. Fast-forward

Nếu:

```text
local = R10
remote = R12
R10 ancestor of R12
```

thì:

```text
local → R12
```

không cần merge.

---

# 38. Non-fast-forward

Nếu:

```text
       R11
      /
R10
      \
       R12
```

thì phải:

```text
merge
```

hoặc:

```text
rebase
```

theo policy.

---

# 39. Semantic merge boundary

AXVCS không thực hiện merge semantics.

```text
AXVCS
  ↓
common ancestor
left revision
right revision
  ↓
AXMERGE
```

---

# 40. Merge result

AXMERGE trả:

```text
MergeResult {
    merged_snapshot
    conflicts[]
    resolutions[]
    provenance
}
```

AXVCS sau đó có thể commit kết quả.

---

# 41. Conflict handling

Conflict không phải repository corruption.

```text
MERGE_CONFLICT
```

là trạng thái bình thường.

AXVCS phải giữ đủ object để người dùng tiếp tục resolution.

---

# 42. Merge session

```text
MergeSession {
    base
    left
    right
    result
    conflicts
    resolutions
}
```

Session có thể persist.

---

# 43. Interrupted merge

Nếu IDE/process bị crash:

```text
MergeSession
```

có thể được phục hồi.

AXIDE/AXMERGE quản lý semantics.

AXVCS lưu session state nếu repository policy yêu cầu.

---

# 44. Rebase

Rebase:

```text
old base
   ↓
patch sequence
   ↓
new base
   ↓
AXPATCH
   ↓
new revisions
```

Mỗi resulting revision có provenance tới original revision.

---

# 45. Rebase identity

Rebased revision **không** giữ RevisionId cũ nếu parent hoặc semantic revision identity thay đổi.

Ví dụ:

```text
R20 → R30
```

sau rebase có:

```text
R40
```

với provenance:

```text
rebased_from = R30
```

---

# 46. Cherry-pick

AXVCS locates source revision.

AXPATCH performs semantic transformation.

Result is new revision.

---

# 47. Clone

Clone pipeline:

```text
remote
 ↓
repository metadata
 ↓
object negotiation
 ↓
pack transfer
 ↓
verify
 ↓
refs
 ↓
working tree
```

---

# 48. Full clone

Full clone guarantees:

```text
all reachable revisions
all required semantic objects
all required trees
```

subject to repository policy for generated/external artifacts.

---

# 49. Shallow clone

Repository may specify:

```text
depth
```

Then older ancestors may be unavailable.

AXHISTORY reports:

```text
PARTIAL
```

rather than inventing history.

---

# 50. Sparse clone

Sparse checkout selects:

```text
module/
subtree/
files
```

But semantic dependencies may require additional objects.

---

# 51. Semantic sparse checkout

Example:

```text
checkout symbol Foo
```

may require:

```text
Foo
trait dependencies
types
imports
module metadata
```

AXCOMPILER determines semantic dependencies.

---

# 52. Partial semantic clone

Repository can fetch:

```text
revision
+
requested semantic closure
```

without retrieving unrelated source.

---

# 53. Object reachability

Reachability is defined from:

```text
refs
merge sessions
pins
required metadata
```

not merely filesystem files.

---

# 54. Object garbage collection

Unreachable objects may be collected only after grace period.

```text
GC
 ↓
mark
 ↓
grace
 ↓
sweep
```

---

# 55. Repository pins

Temporary operations may pin objects:

```text
Pin {
    object_id
    reason
    expiration
}
```

Prevents GC during builds/merge/fetch.

---

# 56. Content-addressed storage

Object path/layout must not depend on:

```text
source filename
branch
author
timestamp
```

Only canonical content identity.

---

# 57. Hash algorithm

`AXVCS_SCHEMA_1` must specify a cryptographic hash family supported by `AXCRYPTO`.

Repository metadata records:

```text
hash_algorithm
```

Hash migration must support multiple generations.

---

# 58. Hash agility

Do not permanently hard-code a single digest into the conceptual model.

```text
ObjectId {
    algorithm
    digest
}
```

---

# 59. Integrity

On object read:

```text
stored_id == hash(payload)
```

must hold.

Otherwise:

```text
OBJECT_CORRUPTION
```

---

# 60. Pack files

Many small objects may be packed:

```text
Pack {
    objects[]
    compressed_data
    index
}
```

Pack representation is storage optimization, not semantic representation.

---

# 61. Delta compression

Objects may use delta compression:

```text
Object B
  ↓
delta against A
```

The canonical object remains:

```text
B
```

Delta encoding must never alter ObjectId.

---

# 62. Delta safety

Delta chains must have bounded depth.

Reject pathological chains that cause resource exhaustion.

---

# 63. Pack index

Pack index supports:

```text
ObjectId → offset
```

It is derived metadata.

It must be rebuildable.

---

# 64. Streaming fetch

Large pack transfer:

```text
network
 ↓
stream
 ↓
verify chunk
 ↓
temporary storage
 ↓
finalize
```

Avoid requiring entire pack in RAM.

---

# 65. Resumable transfer

Transport may support:

```text
resume(offset)
```

with integrity verification.

---

# 66. Object negotiation

Client advertises:

```text
known object roots
known refs
capabilities
```

Server determines missing closure.

---

# 67. Capability negotiation

Examples:

```text
CAP_PACK
CAP_DELTA
CAP_SEMANTIC
CAP_PARTIAL
CAP_SPARSE
CAP_RESUME
CAP_SIGNED_REFS
CAP_COMPRESSION
```

Unknown capabilities are ignored safely.

---

# 68. Protocol boundary

```text
AXVCS Repository
       │
       ▼
AXVCS Transport API
       │
 ┌─────┼─────┐
 ▼     ▼     ▼
HTTP  SSH   local
adapter adapter adapter
```

Actual protocols belong to transport adapters.

---

# 69. No mandatory network protocol

AXVCS core must work:

```text
offline
local filesystem
removable storage
LAN
remote server
```

---

# 70. Local repository

Minimum implementation:

```text
.axrepo/
```

with:

```text
objects/
refs/
packs/
metadata/
locks/
```

Exact physical layout remains implementation detail.

---

# 71. Repository lock

Concurrent writers require repository-level synchronization.

Readers should remain concurrent where safe.

---

# 72. Lock hierarchy

Recommended:

```text
repository lock
    ↓
ref transaction
    ↓
object transaction
```

Avoid lock inversion.

---

# 73. Crash safety

Commit sequence:

```text
write objects
 ↓
fsync/commit durable storage
 ↓
update ref atomically
 ↓
fsync ref metadata
```

Platform adapter determines exact durability primitive.

---

# 74. Crash recovery

After crash:

```text
orphan objects
```

are safe because they are immutable.

Ref update must either:

```text
old
```

or:

```text
new
```

never partially written.

---

# 75. Repository recovery

API:

```text
verify_repository()
recover_repository()
rebuild_indexes()
repack()
gc()
```

---

# 76. Repository metadata

```text
RepositoryConfig {
    schema
    hash
    default_branch
    policies
    capabilities
}
```

---

# 77. Branch policy

Policies may control:

```text
fast_forward_only
protected_branch
required_checks
signed_commits
signed_refs
```

Authorization remains outside core.

---

# 78. Commit verification

Repository may require:

```text
signature
provenance
AXTEST result
ABI compatibility
build status
```

These are metadata gates.

AXVCS does not itself run tests.

---

# 79. Signed revision

Revision may reference:

```text
Signature {
    algorithm
    signer
    signature
}
```

Cryptographic implementation belongs to AXCRYPTO/AXTRUST.

---

# 80. Signed ref

Remote can publish:

```text
SignedRef {
    ref
    revision
    signature
}
```

Consumers can verify before accepting.

---

# 81. Trust boundary

```text
AXVCS
  ↓
AXCRYPTO / AXTRUST
```

AXVCS asks:

```text
verify_signature()
```

rather than implementing cryptography itself.

---

# 82. Authentication

Transport authentication is outside AXVCS semantic core.

Possible adapters:

```text
SSH keys
TLS
OS credentials
tokens
local permissions
```

---

# 83. Authorization

Repository may ask external policy:

```text
can_read
can_write
can_update_ref
can_force_update
```

AXVCS enforces returned authorization decisions.

---

# 84. Force update

Force-update must be explicit:

```text
force_update_ref()
```

Never silently overwrite remote refs.

---

# 85. Remote discovery

Remote advertises:

```text
repository id
schema
refs
capabilities
object format
policy
```

Client verifies compatibility.

---

# 86. Repository compatibility

A client must reject incompatible repository schema unless a migration adapter exists.

```text
UNSUPPORTED_SCHEMA
```

is preferable to corrupt interpretation.

---

# 87. Semantic capability

Older servers may not understand semantic objects.

AXVCS can fallback to raw source/tree objects where policy allows.

However:

```text
semantic history unavailable
```

must be explicit.

---

# 88. Git interoperability

Git adapter architecture:

```text
Git
 │
 ▼
AXVCS Adapter
 │
 ├── blobs
 ├── trees
 ├── commits
 └── refs
 │
 ▼
AXHISTORY
```

A Git commit can be imported as external/history metadata.

---

# 89. Git import identity

Imported Git commit IDs are stored as:

```text
ExternalRevisionRef
```

They are not automatically Axiom `RevisionId`.

---

# 90. Git export

Axiom revision can be exported to Git.

Semantic constructs not representable in Git must be encoded through:

```text
metadata
commit message
sidecar data
```

without pretending that line history is equivalent to semantic history.

---

# 91. Repository adapters

AXVCS adapter interface:

```text
RepositoryAdapter {
    open()
    fetch()
    push()
    import()
    export()
    list_refs()
}
```

---

# 92. Package integration

AXPACKAGE may store repository source references:

```text
PackageSource {
    repository
    revision
}
```

AXVCS supplies object/revision retrieval.

Package resolution remains AXPACKAGE.

---

# 93. Build integration

AXBUILD can request:

```text
checkout_revision(R)
```

AXVCS materializes required source.

AXBUILD determines build.

---

# 94. Reproducible checkout

Given:

```text
RevisionId
```

checkout must produce the same canonical source tree.

Platform-specific filesystem metadata must not alter source identity.

---

# 95. File modes

Executable bit or platform-specific mode metadata may be represented in TreeEntry.

But semantic source identity must distinguish only fields defined by schema.

---

# 96. Generated files

Repository policy:

```text
generated_policy =
    IGNORE
    TRACK
    TRACK_METADATA
```

Generated native binaries should normally be rebuilt from source rather than treated as source truth.

---

# 97. Large files

AXVCS should support large blobs through:

```text
streaming
external object providers
content references
```

rather than forcing RAM-sized buffers.

---

# 98. External artifact reference

```text
ExternalObjectRef {
    provider
    object_id
    size
    digest
}
```

The referenced artifact is not automatically embedded.

---

# 99. Binary artifact boundary

For native binaries:

```text
source/config
    ↓
AXVCS
    ↓
AXBUILD
    ↓
AXBINARY
```

If two binaries need comparison:

```text
AXBINARY
    ↓
AXDIFF
```

Do not byte-merge executables.

---

# 100. Semantic repository query

AXVCS can expose:

```text
resolve_revision()
resolve_ref()
has_object()
fetch_object()
```

Semantic queries remain AXHISTORY's responsibility.

---

# 101. Repository transaction API

```text
RepositoryTxn {
    begin()
    put_object()
    stage_ref()
    verify()
    commit()
    abort()
}
```

---

# 102. Atomic publication

A remote push should conceptually be:

```text
receive objects
 ↓
verify closure
 ↓
verify policy
 ↓
atomic ref update
```

If ref update fails:

```text
objects may remain unreachable
```

and can later be GC'd.

---

# 103. Fetch atomicity

Fetched objects can safely become visible before refs because objects are immutable.

Remote-tracking refs should update atomically after verification.

---

# 104. Object visibility

An object is valid if:

```text
hash(payload) == ObjectId
```

Reachability determines whether it is retained, not whether it is structurally valid.

---

# 105. History reachability

Root set:

```text
branches
tags
remote refs
pins
active sessions
```

Then traverse:

```text
revision
 ↓
parents
 ↓
tree
 ↓
semantic root
 ↓
patch references
```

---

# 106. Semantic object deduplication

If two revisions reference identical semantic roots:

```text
same semantic object
```

must be stored once.

---

# 107. Tree deduplication

Identical directory trees share the same Tree ObjectId.

This makes large repositories naturally incremental.

---

# 108. Repository performance target

Typical operations:

```text
lookup object       O(1) expected
ref lookup          O(1)
revision read       O(1) + referenced objects
```

using indexes.

---

# 109. Fetch scalability

Transfer should be proportional to:

```text
new reachable objects
```

rather than total repository size.

---

# 110. Parallelism

Safe parallelism:

```text
object hashing
compression
pack creation
pack verification
object transfer
index construction
```

Final ref update remains serialized/atomic.

---

# 111. Deterministic pack creation

Given same:

```text
object set
schema
compression policy
```

pack ordering should be deterministic where reproducibility is requested.

---

# 112. Non-semantic metadata

The following should not alter semantic object identity unless explicitly part of schema:

```text
local filesystem timestamp
cache location
network transport
temporary path
```

---

# 113. Semantic commit metadata

Metadata that can affect repository identity must be explicitly classified:

```text
semantic
historical
administrative
ephemeral
```

---

# 114. Repository export

Export may produce:

```text
full
thin
sparse
semantic-only
source-only
```

representations.

---

# 115. Repository import

Import pipeline:

```text
external VCS
 ↓
adapter
 ↓
canonical objects
 ↓
AXHISTORY normalization
 ↓
AXVCS repository
```

Imported uncertainty must remain marked.

---

# 116. Offline mode

All local operations must work without network:

```text
commit
branch
tag
diff
merge
history
revert
rebase
```

where required objects exist locally.

---

# 117. Offline merge

```text
local R10
local feature R15
```

can merge entirely offline if:

```text
base + left + right
```

are present.

---

# 118. Missing object behavior

If required object is absent:

```text
OBJECT_MISSING
```

not:

```text
empty content
```

---

# 119. Missing semantic data

If source exists but semantic object does not:

```text
SEMANTIC_DATA_UNAVAILABLE
```

AXHISTORY/AXCOMPILER may reconstruct if permitted.

---

# 120. Repository repair philosophy

AXVCS may repair:

```text
indexes
pack indexes
temporary files
cache
```

It must not invent:

```text
revisions
parents
symbol lineage
```

---

# 121. Audit log

Administrative actions may generate:

```text
AuditEvent {
    actor
    action
    target
    previous
    new
    timestamp
}
```

Audit logs are separate from immutable revision history.

---

# 122. History versus audit

```text
AXHISTORY
    = what changed

AXVCS audit
    = repository administrative action
```

These must not be conflated.

---

# 123. Repository events

Optional events:

```text
FETCH
PUSH
REF_UPDATE
BRANCH_CREATE
TAG_CREATE
GC
REPACK
IMPORT
EXPORT
```

---

# 124. IDE integration

AXIDE exposes:

```text
current branch
history
fetch
push
pull
branch
tag
merge
rebase
stash-equivalent
```

But semantic operations delegate to AXHISTORY/AXMERGE/AXPATCH.

---

# 125. Stash equivalent

Axiom can provide:

```text
WorkspaceSnapshot
```

rather than Git-specific stash semantics.

Pipeline:

```text
working changes
 ↓
temporary AXHISTORY revision
 ↓
private ref/pin
```

No public branch required.

---

# 126. Workspace snapshot

```text
WorkspaceSnapshot {
    base_revision
    tree
    semantic_root
    selected_changes
}
```

Can restore without creating a public commit.

---

# 127. Shelving

For IDE use:

```text
shelf()
unshelf()
list_shelves()
delete_shelf()
```

Shelves are repository-local temporary objects.

---

# 128. No hidden source mutation

Operations such as:

```text
pull
checkout
rebase
merge
```

must either:

```text
modify working tree explicitly
```

or return a pending operation.

No silent destructive overwrite.

---

# 129. Checkout conflict

If working tree contains uncommitted changes conflicting with target:

```text
CHECKOUT_CONFLICT
```

must be returned.

---

# 130. Force checkout

Destructive checkout requires explicit:

```text
force=true
```

and policy permission.

---

# 131. Semantic checkout

Checkout should ideally preserve semantic boundaries:

```text
module
symbol
generated files
configuration
```

and report conflicts at semantic level when possible.

---

# 132. Repository state machine

```text
CLEAN
  │
  ├── edit
  ▼
DIRTY
  │
  ├── commit
  ▼
CLEAN

DIRTY
  ├── merge
  ├── rebase
  └── checkout
       ↓
   operation state
```

Operations can be:

```text
MERGING
REBASING
CHERRY_PICKING
CHECKOUT_PENDING
```

---

# 133. Operation recovery

Each multi-step operation has:

```text
OperationId
state
base
targets
progress
```

After crash:

```text
recover_operation(OperationId)
```

---

# 134. Cancellation

Long-running:

```text
clone
fetch
push
repack
gc
checkout
```

must support cancellation at safe boundaries.

Already committed immutable objects remain valid.

---

# 135. Resource control

Operations accept:

```text
memory_limit
disk_limit
cpu_limit
network_limit
object_limit
depth_limit
```

---

# 136. Untrusted repository defense

Reject:

```text
malformed object
hash mismatch
invalid tree
duplicate invalid entries
path traversal
oversized metadata
DAG cycles
pack bombs
delta bombs
```

---

# 137. Path traversal

Tree names must never allow materialization outside checkout root.

Reject:

```text
../
absolute paths
invalid platform path forms
```

according to target platform policy.

---

# 138. Case collision

On case-insensitive filesystem:

```text
Foo.ax
foo.ax
```

may collide.

Checkout must detect this before writing.

---

# 139. Symlink policy

Symlink support is target/platform policy.

Never follow repository-controlled symlinks outside checkout root during materialization.

---

# 140. Submodules / nested repositories

Axiom should prefer explicit:

```text
RepositoryRef
```

rather than implicit nested repository magic.

---

# 141. Repository dependencies

A project may reference another repository:

```text
RepositoryDependency {
    repository_id
    revision
}
```

Resolution belongs to AXPACKAGE, retrieval to AXVCS.

---

# 142. Monorepo support

AXVCS naturally supports monorepos because Tree and Semantic objects can represent large project graphs.

Sparse semantic checkout avoids loading irrelevant modules.

---

# 143. Multi-project repository

One repository may contain:

```text
project A
project B
shared library
tools
documentation
```

Semantic roots can be independent or shared.

---

# 144. Subtree extraction

AXVCS can export a subtree as a new repository.

Semantic identity mapping must be recorded if AXHISTORY lineage is preserved.

---

# 145. Repository federation

Multiple repositories can reference immutable objects by:

```text
RepositoryId
ObjectId
RevisionId
```

Federation does not imply trust.

---

# 146. Remote object cache

Build systems may use remote CAS:

```text
AXVCS ObjectStore
        ↕
Remote CAS
```

AXBUILD controls build cache semantics.

---

# 147. VCS versus build cache

Do not conflate:

```text
source history object
```

with:

```text
compiled artifact cache
```

AXBINARY/AXBUILD remain authorities for compiled artifacts.

---

# 148. AI integration

AI can query:

```text
branch history
symbol history
changed files
pending changes
remote changes
merge candidates
```

through AXIDE/AXHISTORY.

---

# 149. AI operation policy

AI may suggest:

```text
commit message
branch name
merge resolution
rebase plan
```

but cannot silently execute destructive repository operations.

---

# 150. AI commit

AI-generated commit message may be accepted by user.

The semantic revision remains determined by actual source state.

---

# 151. AI provenance

If AI generated metadata:

```text
metadata.provenance = AI_ASSISTED
```

Actual authorship remains explicit.

---

# 152. Repository query API

Core:

```text
open_repository()
init_repository()

read_object()
write_object()

read_revision()
write_revision()

read_ref()
update_ref()

create_branch()
delete_branch()

create_tag()
delete_tag()

fetch()
push()
pull()
clone()

checkout()
shelf()
unshelf()

verify()
recover()
gc()
repack()
```

---

# 153. Object API

```text
ObjectId put_object(
    ObjectKind,
    Bytes
)

Object read_object(
    ObjectId
)

bool has_object(
    ObjectId
)

stream<ObjectChunk> stream_object(
    ObjectId
)
```

---

# 154. Ref API

```text
RevisionId resolve_ref(
    RefName
)

void update_ref(
    RefName,
    expected_old,
    new_target
)
```

---

# 155. Fetch API

```text
FetchResult fetch(
    RemoteId,
    FetchSpec,
    FetchPolicy
)
```

---

# 156. Push API

```text
PushResult push(
    RemoteId,
    RefUpdate[],
    PushPolicy
)
```

---

# 157. Clone API

```text
Repository clone(
    RemoteEndpoint,
    CloneSpec
)
```

---

# 158. Checkout API

```text
CheckoutResult checkout(
    RevisionId,
    CheckoutPolicy
)
```

---

# 159. Repository status

```text
Status {
    head
    branch
    working_tree
    staged_changes
    merge_state
    rebase_state
    remote_state
}
```

---

# 160. Semantic status

Status can include:

```text
added symbols
removed symbols
renamed symbols
moved symbols
API changes
ABI changes
dependency changes
```

provided by AXDIFF/AXHISTORY.

---

# 161. Repository ABI

`AXVCS_ABI_1` exposes opaque handles:

```text
RepositoryHandle
ObjectStoreHandle
TransactionHandle
RemoteHandle
OperationHandle
RefHandle
```

Internal storage layout is not ABI.

---

# 162. ABI rule

Applications must not depend on:

```text
.axrepo/
pack physical format
object filename layout
index implementation
compression implementation
```

Only canonical repository protocol/schema is stable.

---

# 163. Schema versioning

`AXVCS_SCHEMA_1` identifies:

```text
object encoding
tree schema
revision encoding
ref metadata
pack format
transport capabilities
```

---

# 164. Transport ABI

Transport adapter interface:

```text
connect()
advertise()
negotiate()
receive()
send()
close()
```

No specific network protocol is mandatory.

---

# 165. Testing

AXTEST phải kiểm tra:

```text
object hashing
object integrity
tree canonicalization
revision storage
ref atomicity
branch
tag
commit
clone
fetch
push
pull
merge boundary
rebase boundary
partial clone
sparse checkout
pack
delta
GC
crash recovery
concurrency
security
Git interoperability
determinism
```

---

# 166. Crash tests

Inject failures:

```text
during object write
during pack write
after object fsync
before ref update
during ref update
after ref update
during fetch
during push
during checkout
```

Repository phải luôn recover về trạng thái hợp lệ.

---

# 167. Atomicity invariant

Nếu commit transaction thất bại:

```text
observable repository state
```

phải tương đương:

```text
trước transaction
```

ngoại trừ unreachable garbage objects được phép tồn tại cho tới GC.

---

# 168. Push safety invariant

Push không được làm mất remote revision reachable trước push nếu policy không cho phép force update.

---

# 169. Fetch safety invariant

Fetch không được làm thay đổi local branch head.

---

# 170. Checkout safety invariant

Checkout conflict không được silently destroy uncommitted changes.

---

# 171. Merge boundary invariant

AXVCS không được tự tạo semantic merge.

AXMERGE là authority.

---

# 172. Patch boundary invariant

AXVCS không tự áp dụng semantic patch.

AXPATCH là authority.

---

# 173. History boundary invariant

AXVCS không tự suy diễn symbol lineage.

AXHISTORY là authority.

---

# 174. Diff boundary invariant

AXVCS không tự đánh giá semantic difference.

AXDIFF là authority.

---

# 175. Binary boundary invariant

Native executable không phải merge unit của AXVCS.

Source/configuration là canonical change unit.

---

# 176. Deterministic repository

Cùng object set:

```text
canonical tree
canonical revision
```

phải tạo cùng:

```text
ObjectId
RevisionId
semantic roots
```

---

# 177. Repository-local metadata

Repository-local settings như:

```text
remote URL
cache directory
local branch configuration
```

không được làm thay đổi content identity.

---

# 178. Remote URL privacy

Remote endpoint có thể chứa sensitive information.

Không được đưa vào:

```text
ObjectId
RevisionId
semantic snapshot
```

trừ khi explicit repository metadata.

---

# 179. Performance target

Repository phải có khả năng xử lý:

```text
millions of objects
hundreds of thousands of revisions
large monorepos
large binary-adjacent source trees
```

mà không yêu cầu load toàn bộ repository vào RAM.

---

# 180. Memory model

Object reads nên hỗ trợ:

```text
mmap
stream
zero-copy
paged access
```

khi platform cho phép.

---

# 181. Parallel checkout

Independent files/objects có thể materialize song song.

Filesystem finalization phải xử lý:

```text
path conflicts
case collisions
symlink policy
```

deterministically.

---

# 182. Repository compression

Compression policy:

```text
NONE
FAST
BALANCED
MAX
```

không được ảnh hưởng ObjectId.

---

# 183. Pack compaction

Repack thay đổi:

```text
physical layout
```

nhưng không thay đổi:

```text
ObjectId
RevisionId
semantic state
```

---

# 184. Garbage collection safety

GC phải respect:

```text
all refs
pins
active operations
remote-tracking refs
shelves
merge sessions
```

---

# 185. Remote GC

Remote repository không được GC object chỉ vì client chưa biết ref mới, nếu protocol chưa đảm bảo visibility/lease semantics.

---

# 186. Lease

Push có thể sử dụng:

```text
expected_remote_head
```

tương đương optimistic concurrency.

---

# 187. Protected refs

Server policy có thể yêu cầu:

```text
main
release/*
```

chỉ fast-forward hoặc phải qua validation.

AXVCS chỉ enforce policy result.

---

# 188. Required checks

Remote có thể yêu cầu metadata:

```text
build passed
tests passed
ABI compatible
signature valid
```

AXVCS không tự thực thi.

---

# 189. Repository event hooks

Hook boundary:

```text
pre_push
post_push
pre_checkout
post_checkout
```

Hooks phải explicit và sandboxable.

Không được thực thi repository-controlled arbitrary code automatically trong secure/default mode.

---

# 190. No arbitrary code execution

Reading/fetching/merging repository data must not automatically execute:

```text
build scripts
hooks
macros
generators
post-checkout programs
```

Execution requires explicit AXBUILD/AXIDE policy.

---

# 191. Repository protocol security

Transport must authenticate:

```text
endpoint
peer
repository identity
```

according to configured trust policy.

---

# 192. Repository trust

A repository may be:

```text
TRUSTED
UNTRUSTED
UNKNOWN
```

Trust metadata must not alter source semantics.

---

# 193. Semantic trust

Signed revision proves:

```text
signature validity
```

not:

```text
code correctness
```

AXTEST/AXBUILD remain separate.

---

# 194. History trust

A signed history object does not automatically prove that its semantic interpretation is correct.

Schema and compiler provenance remain relevant.

---

# 195. Reproducible clone

A clone of the same revision must yield identical:

```text
canonical source tree
semantic root
revision identity
```

regardless of transport.

---

# 196. Repository migration

Migration:

```text
SCHEMA_1 → SCHEMA_2
```

must preserve:

```text
object identity where possible
revision lineage
external refs
provenance
```

or provide explicit mapping.

---

# 197. Compatibility modes

Clients may support:

```text
READ_OLD
READ_WRITE_OLD
MIGRATE
```

according to schema compatibility.

---

# 198. Repository export/import verification

After round trip:

```text
export(repo)
import(export)
```

must preserve canonical semantics where the target format supports them.

---

# 199. 40 invariants

### VCS-INV-01
Objects are content-addressed.

### VCS-INV-02
ObjectId is deterministic.

### VCS-INV-03
Object integrity is verified before acceptance.

### VCS-INV-04
Revision objects are immutable.

### VCS-INV-05
Refs are mutable pointers.

### VCS-INV-06
RevisionId does not depend on branch name.

### VCS-INV-07
RevisionId does not depend on filesystem path.

### VCS-INV-08
RevisionId does not depend on transport.

### VCS-INV-09
Tree ordering is deterministic.

### VCS-INV-10
Repository object storage is incrementally deduplicated.

### VCS-INV-11
Commit publication is atomic.

### VCS-INV-12
Failed commit cannot publish partial ref state.

### VCS-INV-13
Ref updates support optimistic concurrency.

### VCS-INV-14
Fetch never changes local branch heads.

### VCS-INV-15
Push cannot silently overwrite remote refs.

### VCS-INV-16
Pull integration is policy-controlled.

### VCS-INV-17
Semantic merge belongs to AXMERGE.

### VCS-INV-18
Patch application belongs to AXPATCH.

### VCS-INV-19
Semantic history belongs to AXHISTORY.

### VCS-INV-20
Difference analysis belongs to AXDIFF.

### VCS-INV-21
Native binaries are not ordinary merge units.

### VCS-INV-22
Generated artifacts follow explicit repository policy.

### VCS-INV-23
Partial history is explicitly represented.

### VCS-INV-24
Missing objects are errors, not empty values.

### VCS-INV-25
GC cannot collect reachable objects.

### VCS-INV-26
GC respects active pins and operations.

### VCS-INV-27
Pack layout does not affect object identity.

### VCS-INV-28
Compression does not affect object identity.

### VCS-INV-29
Pack indexes are rebuildable derived data.

### VCS-INV-30
Repository crash recovery preserves canonical state.

### VCS-INV-31
Checkout does not silently destroy uncommitted changes.

### VCS-INV-32
Repository-controlled data does not trigger arbitrary execution.

### VCS-INV-33
Transport is replaceable.

### VCS-INV-34
Git interoperability is adapter-based.

### VCS-INV-35
Authentication is outside semantic repository identity.

### VCS-INV-36
Administrative metadata does not silently alter source identity.

### VCS-INV-37
Canonical repository export is deterministic.

### VCS-INV-38
Repository schema changes are explicit and versioned.

### VCS-INV-39
AI operations cannot silently perform destructive repository mutations.

### VCS-INV-40
Repository storage never invents semantic history.

---

# 200. Definition of Done

`AXVCS 5.0` được xem là hoàn thành khi:

- [x] Content-addressed object model.
- [x] Blob/tree/revision/semantic objects.
- [x] Canonical tree serialization.
- [x] Repository identity.
- [x] Branch/ref/tag model.
- [x] Atomic ref transactions.
- [x] Commit transaction.
- [x] Object integrity.
- [x] Pack/delta storage.
- [x] Incremental storage.
- [x] Garbage collection.
- [x] Crash recovery.
- [x] Fetch.
- [x] Push.
- [x] Pull.
- [x] Clone.
- [x] Partial/shallow history.
- [x] Sparse checkout.
- [x] Semantic sparse checkout boundary.
- [x] Checkout safety.
- [x] Rebase/cherry-pick boundaries.
- [x] Merge-session boundary.
- [x] Remote-tracking refs.
- [x] Transport abstraction.
- [x] Authentication/authorization boundaries.
- [x] Signed revision/ref boundary.
- [x] Git interoperability boundary.
- [x] AXHISTORY integration.
- [x] AXMERGE integration.
- [x] AXPATCH integration.
- [x] AXDIFF integration.
- [x] AXBUILD/AXPACKAGE integration.
- [x] AI safety boundary.
- [x] Deterministic serialization.
- [x] Large repository scalability model.
- [x] Resource-exhaustion protection.
- [x] 40 invariants.
- [x] `AXVCS_ABI_1`.
- [x] `AXVCS_SCHEMA_1`.

**AXVCS 5.0 — FROZEN.**

---

# Vị trí của AXVCS trong Axiom

Sau `AXDIFF → AXMERGE → AXHISTORY → AXVCS`, hệ thống thay đổi của Axiom hiện có kiến trúc:

```text
                         Axiom Source
                              │
                              ▼
                         AXCOMPILER
                              │
                      Semantic Snapshot
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          AXDIFF           AXPATCH          AXHISTORY
        Difference          Change           Lineage
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                           AXMERGE
                         Composition
                              │
                              ▼
                         AXHISTORY
                        New Revision
                              │
                              ▼
                            AXVCS
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          Object Store      Refs            Transport
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                           Remote
```

Điểm quan trọng là **Axiom không biến compiler thành một Git clone**:

```text
AXDIFF    → hiểu sự khác biệt
AXPATCH   → hiểu thay đổi
AXMERGE   → hiểu cách kết hợp thay đổi
AXHISTORY → hiểu nguồn gốc thay đổi
AXVCS     → lưu trữ và vận chuyển các kết quả đó
```

Điều này giữ cho compiler, IDE và AI có thể làm việc với **symbol/semantic identity** thay vì phải quay về mô hình file/line của VCS truyền thống.

---

# BOOTSTRAP-799 — AXPATCH

**Native Axiom Semantic Patch Engine, Typed Patch IR, Symbol-Level Patch Application, Rename/Move/Extract/Inline/Split/Merge Operations, Patch Rebase & Relocation, Context Validation, Dependency-Aware Application, API/ABI Patch Validation, Three-Way Patch Adaptation, Patch Provenance, Deterministic Patch Serialization & Patch ABI 5.0**

Chuỗi tiếp theo sẽ hoàn thiện lớp còn thiếu trong bộ:

```text
AXDIFF
   ↓
AXPATCH
   ↓
AXMERGE
   ↓
AXHISTORY
   ↓
AXVCS
```

Trong đó `AXPATCH` sẽ là **primitive mutation layer**: biến một thay đổi semantic đã được mô tả thành một phép biến đổi có thể áp dụng, kiểm tra, relocate và rebase trên source/AST/semantic state.