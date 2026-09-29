# BOOTSTRAP-797 — AXHISTORY
## Native Axiom Semantic History Engine, Symbol-Centric Revision Graph, Semantic Commit Model, Change Lineage, Patch/Commit DAG, Branch/Tag/Revision Semantics, Rename/Move-Aware History, API/ABI History, Dependency History, Blame/Attribution, Reproducible Revision Identity, Incremental History Index, Semantic Log & History ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXHISTORY`  
**ABI:** `AXHISTORY_ABI_1`  
**Schema:** `AXHISTORY_SCHEMA_1`  
**Artifact:** `.axhistory`

**Dependencies:**
```text
AXCOMPILER
AXDIFF
AXPATCH
AXMERGE
AXABI
AXDOC
AXBUILD
AXPACKAGE
AXTEST
AXIDE
AXCODEEDITOR
```

---

# 1. Mục tiêu

`AXHISTORY` cung cấp lịch sử **semantic** của một project Axiom.

Lịch sử truyền thống:

```text
Commit
  ↓
files
  ↓
lines
```

không đủ tốt cho Axiom vì:

- một function có thể bị di chuyển;
- một struct có thể đổi tên;
- một symbol có thể thay đổi file;
- code có thể được format lại;
- một API có thể thay đổi nhưng line history không còn liên quan;
- ABI có thể thay đổi mà source diff rất nhỏ;
- AI cần biết **nguồn gốc semantic của symbol**.

AXHISTORY xây:

```text id="5uyxk2"
                 AXHISTORY
                     │
             Semantic Revision DAG
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
     Revision      Symbol       Change
        │          Lineage      Lineage
        │            │            │
        └────────────┼────────────┘
                     ▼
                  AXPATCH
                     │
                  AXDIFF
```

---

# 2. Mô hình canonical

Một revision:

```text id="r1y3f4"
Revision
 ├ parents
 ├ semantic snapshot
 ├ patch set
 ├ symbols
 ├ dependencies
 ├ API state
 ├ ABI state
 └ provenance
```

Lịch sử:

```text id="p7rj4k"
R0
│
├── R1
│    └── R2
│         └── R3
│
└── R4
     └── R5
          └── R6
```

Merge:

```text id="o8w3ea"
R3 ─────┐
        ├── R7
R6 ─────┘
```

AXHISTORY phải giữ nguyên cả hai lineage.

---

# 3. Boundary

AXHISTORY sở hữu:

```text id="sh1j3x"
revision identity
revision graph
semantic commit
symbol lineage
change lineage
branch/tag metadata
semantic blame
history indexing
history queries
history serialization
```

Không sở hữu:

```text id="c1jv85"
source merge
patch application
compiler semantics
ABI implementation
package registry
build execution
authentication
remote transport
```

---

# 4. Architecture

```text id="xk5g1q"
                         AXHISTORY
                             │
       ┌─────────────────────┼─────────────────────┐
       ▼                     ▼                     ▼
 Revision Store         Semantic Index        Query Engine
       │                     │                     │
       ▼                     ▼                     ▼
 Revision DAG           Symbol Lineage       History Queries
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
                    Change Lineage Engine
                             │
                 ┌───────────┼───────────┐
                 ▼           ▼           ▼
              AXDIFF       AXPATCH     AXMERGE
                 │           │           │
                 └───────────┼───────────┘
                             ▼
                       AXCOMPILER
```

---

# 5. Revision

```text id="0k1b7v"
struct Revision {
    id: RevisionId

    parents: [RevisionId]

    root_tree: TreeHash
    semantic_root: SemanticHash

    patch_set: optional<PatchSetId>

    author: AuthorId
    message: String

    target: TargetIdentity
    abi: AbiIdentity

    provenance: RevisionProvenance
}
```

---

# 6. RevisionId

Revision identity phải tách:

```text id="3e9j4v"
content identity
```

khỏi:

```text id="g9n3q5"
external VCS identity
```

Canonical:

```text id="1o9m2s"
RevisionId =
hash(
    schema,
    parent_ids,
    root_tree,
    semantic_root,
    patch_set,
    metadata_policy
)
```

Timestamp không được quyết định RevisionId.

---

# 7. External commit identity

Có thể liên kết:

```text id="f9a7c0"
ExternalRevisionRef {
    provider
    repository
    external_id
}
```

AXHISTORY không phụ thuộc vào Git hoặc hệ thống VCS cụ thể.

---

# 8. Parent semantics

Revision có:

```text id="3r7n8d"
0 parents → root
1 parent  → normal revision
2+ parents → merge revision
```

AXHISTORY hỗ trợ DAG tự nhiên.

---

# 9. Semantic snapshot

Mỗi revision có thể tham chiếu:

```text id="8v0kqm"
SemanticSnapshot {
    modules
    symbols
    types
    dependencies
    API
    ABI
    metadata
}
```

Không bắt buộc lưu toàn bộ snapshot vật lý nếu có thể tái tạo bằng persistent storage.

---

# 10. Snapshot storage

```text id="m4j7z1"
Revision
   ↓
RootHash
   ↓
Merkle DAG
   ├── module
   ├── symbol
   ├── type
   ├── dependency
   └── metadata
```

Chỉ node thay đổi cần lưu mới.

---

# 11. Symbol history

Symbol được theo dõi bằng:

```text id="c3q7f9"
SymbolId
```

Ví dụ:

```text id="5n8k2d"
S123
 ↓
R1
 ↓
R2
 ↓
R3
```

AXHISTORY có thể trả lời:

> Symbol này đã tồn tại từ revision nào?

> Nó thay đổi khi nào?

> Nó từng có tên gì?

> Nó từng nằm trong module nào?

> API/ABI của nó thay đổi ra sao?

---

# 12. Symbol lineage

```text id="h8y2v1"
SymbolLineage {
    symbol_id

    first_revision
    last_revision

    names
    locations
    parents
    descendants

    events
}
```

---

# 13. Rename lineage

```text id="x2m5n7"
R1:
foo

R2:
compute
```

nếu SymbolId giữ nguyên:

```text id="d5r9k1"
S123:
foo → compute
```

đây là một symbol lineage duy nhất.

---

# 14. Move lineage

```text id="q8w1e4"
R1:
module.a::foo

R2:
module.b::foo
```

vẫn:

```text id="j4t6p2"
SymbolId = S123
```

AXHISTORY ghi:

```text id="z6c8r0"
MOVE:
a → b
```

---

# 15. Identity recovery

Nếu một lịch sử cũ không có SymbolId:

```text id="a7k9m2"
structural identity
signature
AST similarity
name history
location
```

có thể được dùng để dựng lineage.

Nhưng phải đánh dấu:

```text id="p1s4d7"
INFERRED
```

không phải `EXACT`.

---

# 16. Change event

```text id="u3n5q8"
enum HistoryEventKind {
    ADD
    REMOVE
    MODIFY
    RENAME
    MOVE
    REORDER
    TYPE_CHANGE
    SIGNATURE_CHANGE
    API_CHANGE
    ABI_CHANGE
    DEPENDENCY_CHANGE
    ATTRIBUTE_CHANGE
    EFFECT_CHANGE
}
```

---

# 17. HistoryEvent

```text id="r5t7y9"
struct HistoryEvent {
    id: HistoryEventId

    revision: RevisionId
    symbol: optional<SymbolId>

    kind: HistoryEventKind

    before: optional<Hash>
    after: optional<Hash>

    patch: optional<PatchId>

    provenance: Provenance
}
```

---

# 18. Change lineage

```text id="n2m4b6"
ChangeLineage {
    symbol
    events[]
    revisions[]
}
```

Cho phép:

```text id="c6v8x0"
S123
 ↓
ADD
 ↓
MODIFY
 ↓
RENAME
 ↓
MOVE
 ↓
ABI_CHANGE
 ↓
REMOVE
```

---

# 19. Semantic blame

Traditional blame:

```text id="z1x3c5"
line → commit
```

Axiom blame:

```text id="f7h9j2"
semantic property → revision
```

Ví dụ:

```text id="q4w6e8"
User.name.type
    ↓
R42
```

---

# 20. Blame model

```text id="s9d2f4"
SemanticBlame {
    target: SemanticId
    property: PropertyId

    introduced_by: RevisionId
    last_changed_by: RevisionId

    lineage
}
```

---

# 21. Property-level blame

Một symbol có nhiều independently tracked properties:

```text id="k3m5n7"
visibility
signature
body
attributes
documentation
effects
ABI
```

Ví dụ:

```text id="a6c8e0"
foo.visibility → R10
foo.signature → R17
foo.body → R22
foo.doc → R24
```

---

# 22. API history

AXHISTORY lưu:

```text id="v5b7n9"
APIHistory {
    symbol
    visibility
    signature
    exported_state
    deprecation_state
}
```

Cho phép truy vấn:

```text id="p2r4t6"
when did public API change?
```

---

# 23. ABI history

ABI changes được theo dõi riêng:

```text id="d8f0h2"
ABIHistory {
    symbol
    abi_fingerprint
    layout_fingerprint
    calling_convention
    export_state
}
```

AXABI vẫn là authority.

AXHISTORY chỉ lưu history.

---

# 24. ABI timeline

```text id="j4l6n8"
R10
ABI = H1

R20
ABI = H2

R35
ABI = H3
```

Có thể xác định:

```text id="m7q9s1"
ABI changed between R19 and R20
```

---

# 25. Dependency history

```text id="w2e4r6"
Package
 ├ version history
 ├ feature history
 ├ target conditions
 ├ checksum history
 └ dependency graph history
```

---

# 26. Dependency event

```text id="c8v0x2"
DependencyEvent {
    package
    old_constraint
    new_constraint
    revision
}
```

---

# 27. Branch

Branch là named pointer:

```text id="n4p6s8"
Branch {
    name
    head: RevisionId
}
```

Branch name không ảnh hưởng RevisionId.

---

# 28. Tag

```text id="q1w3e5"
Tag {
    name
    revision
    metadata
}
```

Tags are immutable by default.

Moving a tag requires explicit administrative operation.

---

# 29. Branch history

```text id="r7t9y1"
main
 │
 R1
 │
 R2
 ├──── feature
 │       R3
 │       R4
 │
 R5
```

AXHISTORY không yêu cầu branch topology phải tuyến tính.

---

# 30. Merge revision

Merge revision:

```text id="u3i5o7"
parents = [R5, R4]
```

và:

```text id="l2k4m6"
patch_set = merge_patch
```

AXMERGE là engine tạo semantic merge.

AXHISTORY lưu kết quả và lineage.

---

# 31. Merge lineage

```text id="a8s0d2"
R5 ───────┐
          ├── R6
R4 ───────┘
```

History query có thể trả:

```text id="f1g3h5"
ancestor paths
common ancestor
merge origin
change ancestry
```

---

# 32. Common ancestor

```text id="j7k9l1"
common_ancestor(A,B)
```

phải dựa trên DAG topology.

Không dựa vào timestamps.

---

# 33. Revision ancestry

API:

```text id="m2n4b6"
is_ancestor(A,B)
ancestors(R)
descendants(R)
merge_base(A,B)
```

---

# 34. Semantic ancestry

Không chỉ revision ancestry.

Ví dụ:

```text id="p8q0r2"
R10:
foo

R20:
foo renamed bar

R30:
bar moved

R40:
bar modified
```

`semantic_ancestors(bar)` phải có thể truy về:

```text id="s4t6v8"
foo@R10
```

nếu lineage evidence đủ mạnh.

---

# 35. Symbol birth/death

Events:

```text id="x1y3z5"
BORN
RENAMED
MOVED
MODIFIED
DEPRECATED
REMOVED
```

Một symbol bị remove không nhất thiết lineage bị xóa.

---

# 36. Resurrection

Nếu symbol bị remove rồi sau đó xuất hiện lại:

```text id="d7e9f1"
R20 remove S123
R30 add semantically-new S456
```

không được mặc định coi S456 là resurrection của S123.

Chỉ nối lineage nếu identity evidence đủ.

---

# 37. Symbol fork

Một refactoring có thể tạo:

```text id="g2h4j6"
S123
 ↓
S200
S201
```

Ví dụ split function.

AXHISTORY phải hỗ trợ lineage graph:

```text id="k8l0m2"
one → many
```

---

# 38. Symbol merge

Hai symbols có thể hợp nhất:

```text id="n4p6q8"
S123 ──┐
       ├── S300
S124 ──┘
```

History phải giữ cả hai ancestors.

---

# 39. Semantic refactoring event

AXPATCH có thể cung cấp:

```text id="r1s3t5"
RENAME
MOVE
EXTRACT
INLINE
SPLIT
MERGE
```

AXHISTORY lưu như semantic events.

---

# 40. Commit model

Axiom semantic commit:

```text id="u7v9w1"
Commit {
    revision
    patch_set
    semantic_summary
    affected_symbols
    affected_api
    affected_abi
    affected_dependencies
}
```

---

# 41. Commit message

Message là human metadata.

Không ảnh hưởng semantic identity.

Có thể:

```text id="x2y4z6"
change message
```

mà không thay đổi semantic snapshot.

---

# 42. Author attribution

```text id="a8b0c2"
Author {
    identity
    display_name
}
```

Identity/authentication thuộc security/VCS layer.

AXHISTORY chỉ lưu reference.

---

# 43. Co-authorship

Commit có thể có:

```text id="d4e6f8"
authors[]
```

AI contribution có thể được ghi:

```text id="g0h2j4"
AI_ASSISTED
```

nhưng không được tự biến thành author nếu không có explicit policy.

---

# 44. AI history

AXHISTORY có thể ghi:

```text id="k6l8m0"
AIHistory {
    proposal_id
    patch_id
    accepted
    accepted_by
}
```

AI proposal và accepted change phải phân biệt.

---

# 45. History query

Core:

```text id="n2p4r6"
history(symbol)
history(file)
history(module)
history(api)
history(abi)
history(dependency)
```

---

# 46. Symbol query

```text id="t8v0x2"
find_symbol_history(SymbolId)
```

Output:

```text id="y4z6a8"
timeline
renames
moves
modifications
API changes
ABI changes
```

---

# 47. Property history

```text id="b0c2d4"
history_property(
    SymbolId,
    PropertyId
)
```

Ví dụ:

```text id="e6f8g0"
history_property(
    S123,
    Signature
)
```

---

# 48. API timeline query

```text id="i2j4k6"
api_at(revision)
api_changes(from,to)
```

---

# 49. ABI timeline query

```text id="m8n0p2"
abi_at(revision)
abi_changes(from,to)
```

AXABI validates compatibility; AXHISTORY retrieves historical state.

---

# 50. Dependency timeline

```text id="q4r6s8"
dependencies_at(revision)
dependency_changes(from,to)
```

---

# 51. Semantic diff across history

```text id="u0v2w4"
history.diff(R1,R2)
```

delegates actual difference calculation to:

```text id="x6y8z0"
AXDIFF
```

AXHISTORY provides snapshots/lineage.

---

# 52. Historical patch

```text id="a2b4c6"
history.patch(R1,R2)
```

can return:

```text id="d8e0f2"
AXPATCH
```

when an applicable patch representation exists.

---

# 53. Revert

A revert is:

```text id="g4h6j8"
inverse semantic patch
```

not merely:

```text id="k0l2m4"
reverse text diff
```

Pipeline:

```text id="n6p8r0"
Rcurrent
   ↓
AXPATCH.invert/change
   ↓
validate against current state
   ↓
new revision
```

---

# 54. Revert conflict

Nếu sau revision A đã có:

```text id="t2u4v6"
A → B → C
```

và muốn revert A:

patch may conflict with B/C.

Không được overwrite C.

AXPATCH handles conflict.

---

# 55. Cherry-pick

Semantic cherry-pick:

```text id="x8y0z2"
Revision R
   ↓
extract PatchSet
   ↓
rebase onto target
   ↓
validate
   ↓
apply
```

AXHISTORY owns history selection.

AXPATCH owns application/rebase.

---

# 56. History-aware cherry-pick

If target symbol moved:

```text id="b4c6d8"
old location → new location
```

semantic identity permits patch relocation.

If identity is ambiguous:

```text id="f0g2h4"
CHERRY_PICK_IDENTITY_CONFLICT
```

---

# 57. Revert/cherry-pick provenance

Every resulting revision must preserve:

```text id="j6k8l0"
source_revision
source_patch
source_lineage
transformation
```

---

# 58. Squash

Multiple revisions:

```text id="n2p4q6"
R1 → R2 → R3
```

may become:

```text id="r8s0t2"
R4
```

but semantic history may retain:

```text id="v4w6x8"
R1,R2,R3
```

as hidden/original lineage references according to repository policy.

---

# 59. History compaction

History storage may compact unchanged snapshots.

But compaction must preserve:

```text id="y0z2a4"
revision identity
symbol lineage
change lineage
ancestry
provenance
```

---

# 60. Garbage collection

Unreachable history may be pruned only by explicit repository policy.

Do not automatically delete revisions merely because no branch points to them.

---

# 61. Immutable history

Revision objects are immutable.

Changing:

```text id="c6d8e0"
message
```

may be represented as metadata update depending on VCS policy, but changing semantic content creates a new revision.

---

# 62. Merkle storage

Recommended:

```text id="g2h4j6"
Revision
   ↓
MerkleRoot
   ↓
persistent content-addressed nodes
```

Advantages:

- deduplication;
- integrity;
- fast equality;
- incremental storage;
- reproducibility.

---

# 63. History index

Indexes:

```text id="k8l0m2"
RevisionId → Revision
SymbolId → Timeline
Name → Symbol candidates
API symbol → revisions
ABI symbol → revisions
Dependency → revisions
PatchId → revisions
```

---

# 64. Index rebuild

Index can be rebuilt from canonical revision data.

Therefore index is:

```text id="n4p6r8"
derived
```

not semantic source of truth.

---

# 65. Incremental indexing

New revision:

```text id="t0u2w4"
Rnew
 ↓
changed symbols only
 ↓
update lineage indexes
```

Unchanged symbols need not be reprocessed.

---

# 66. History cache

Cache key:

```text id="x6y8z0"
history_schema
revision_root
query
query_policy
```

---

# 67. Determinism

Same revision graph must produce identical:

```text id="a2c4e6"
revision IDs
semantic hashes
lineage
query ordering
serialized history
```

Timestamp does not affect semantic ordering.

---

# 68. Ordering

When multiple events have no semantic ordering:

```text id="g8h0j2"
sort by:
semantic path
event kind
EventId
```

This prevents nondeterministic query results.

---

# 69. History serialization

`.axhistory`:

```text id="k4l6m8"
Header
Schema
RepositoryIdentity
RevisionTable
RevisionParents
SemanticRoots
PatchReferences
SymbolLineage
ChangeLineage
BranchRefs
TagRefs
DependencyHistory
APIHistory
ABIHistory
Provenance
Indexes
Integrity
```

---

# 70. Schema evolution

`AXHISTORY_SCHEMA_1` must support explicit migration.

Unknown event kinds must not be silently interpreted as known kinds.

---

# 71. Remote history

AXHISTORY can operate over remote object storage.

But transport is outside its semantic core.

Required interface:

```text id="n0p2r4"
fetch_revision
fetch_snapshot
fetch_patch
fetch_symbol_lineage
```

---

# 72. Partial history

A shallow/partial repository may not possess all ancestors.

Then queries return:

```text id="t6u8v0"
COMPLETE
PARTIAL
UNKNOWN
```

Never infer missing history as absence of change.

---

# 73. Missing ancestor

If:

```text id="x2y4z6"
R20
```

references parent:

```text id="a8b0c2"
R10
```

but R10 is unavailable:

```text id="d4e6f8"
ancestor_state = UNKNOWN
```

---

# 74. Historical semantic validation

Old revisions may no longer compile under the current compiler.

AXHISTORY must distinguish:

```text id="g0h2j4"
historically recorded valid
```

from:

```text id="k6l8m0"
currently compilable
```

Historical truth must not be rewritten by modern compiler changes.

---

# 75. Compiler version

Revision metadata should record:

```text id="n2p4r6"
compiler_fingerprint
semantic_schema
ABI
target
```

This allows historical interpretation.

---

# 76. Reproducible revision

For source-based revisions:

```text id="t8v0x2"
source_root
compiler_fingerprint
dependency_root
build_configuration
```

can be used to reconstruct artifacts.

AXBUILD remains responsible for actual build.

---

# 77. Build history

```text id="y4z6a8"
BuildHistoryEntry {
    revision
    target
    compiler
    dependency_root
    artifact_hash
}
```

AXBINARY/AXBUILD remain artifact authorities.

---

# 78. Binary history

AXHISTORY stores references:

```text id="b0c2d4"
BinaryArtifactId
BinaryHash
Target
BuildFingerprint
```

not arbitrary executable contents.

AXDIFF compares binaries.

---

# 79. API release history

Tags can be associated with API snapshots:

```text id="e6f8g0"
v1.0 → API Root A
v1.1 → API Root B
v2.0 → API Root C
```

This enables historical API comparison.

---

# 80. ABI release history

Similarly:

```text id="i2j4k6"
release
 ↓
ABI fingerprint
```

AXABI validates compatibility between release states.

---

# 81. History-aware documentation

AXDOC can query:

```text id="m8n0p2"
documentation_at(SymbolId, RevisionId)
```

AXHISTORY supplies historical semantic/document nodes.

---

# 82. IDE integration

AXIDE can expose:

```text id="q4r6s8"
Go to definition at revision
Show symbol history
Show rename history
Show API history
Show ABI history
Show dependency history
Blame semantic property
Compare revisions
Create patch from historical change
Revert semantic change
```

---

# 83. Code editor integration

AXCODEEDITOR can highlight:

```text id="u0v2w4"
symbol introduction
last semantic modification
API change
ABI change
```

without embedding history logic into the editor.

---

# 84. AI integration

AI query:

```text id="x6y8z0"
"Why did this API change?"
```

AXHISTORY can provide:

```text id="a2b4c6"
symbol
change lineage
patch
affected dependencies
API impact
ABI impact
provenance
```

AI then summarizes.

---

# 85. AI history context

Compact form:

```text id="g8h0j2"
HistoryContext {
    symbol
    relevant_revisions
    changes
    patches
    conflicts
    API
    ABI
    dependency
    provenance
}
```

Only relevant history should be supplied.

---

# 86. AI cannot rewrite history

AI may:

- summarize history;
- identify likely reason;
- find related changes;
- suggest revert;
- generate explanation.

AI may not silently:

- rewrite revision;
- delete history;
- alter authorship;
- alter provenance.

---

# 87. Security

History may contain sensitive source/provenance.

Access control belongs to repository/security layer.

AXHISTORY must still support:

```text id="k4l6m8"
redacted views
metadata filtering
source-content omission
```

---

# 88. Secret handling

Secrets must never be automatically embedded in:

```text id="n0p2r4"
commit metadata
patch metadata
history indexes
AI context
```

---

# 89. Resource limits

Untrusted history repositories must be protected against:

```text id="t6u8v0"
DAG explosion
deep ancestry
huge symbol lineage
cyclic malformed metadata
oversized messages
malformed hashes
index explosion
```

---

# 90. Cycle detection

Revision graph must be acyclic.

```text id="x2y4z6"
R1 → R2 → R3 → R1
```

is invalid.

Repository load must reject it.

---

# 91. Symbol lineage cycles

Symbol lineage may contain complex transformations but must not contain impossible identity cycles.

Invalid lineage:

```text id="a8b0c2"
S1 → S2 → S1
```

without explicit historical fork/merge semantics.

---

# 92. History consistency

For every revision:

```text id="d4e6f8"
parents exist
root exists
semantic hash matches
patch references valid
target identity valid
ABI metadata valid
```

unless repository is intentionally partial.

---

# 93. History validation

API:

```text id="g0h2j4"
validate_repository()
validate_revision()
validate_lineage()
validate_indexes()
```

---

# 94. Repair

Derived indexes may be rebuilt.

Canonical revision data must not be automatically rewritten during repair.

If canonical data is corrupt:

```text id="k6l8m0"
CORRUPT_HISTORY
```

must be reported.

---

# 95. History query language

A future query API may support:

```text id="n2p4r6"
symbol S123
between R10..R40
where event == ABI_CHANGE
```

and:

```text id="t8v0x2"
find symbols
where visibility changed
and public == true
```

The query language must remain read-only.

---

# 96. Semantic blame example

Traditional:

```text id="y4z6a8"
line 421 → revision R88
```

Axiom:

```text id="b0c2d4"
User.age.type
    → R88

User.age.default
    → R103

User.visibility
    → R77
```

This is much more useful for refactoring and AI analysis.

---

# 97. Historical dependency impact

When package `foo` changes at R100:

```text id="e6f8g0"
AXHISTORY
 ↓
dependency graph
 ↓
affected modules
 ↓
affected APIs
```

This is evidence for history exploration, not a substitute for current build validation.

---

# 98. Historical ABI impact

When struct layout changes:

```text id="i2j4k6"
R100
 ↓
ABI fingerprint H1

R101
 ↓
ABI fingerprint H2
```

AXHISTORY records transition.

AXABI determines whether that transition is compatible.

---

# 99. History + merge

AXMERGE can request:

```text id="m8n0p2"
common ancestor
symbol lineage
prior renames
prior moves
```

This improves three-way merge identity detection.

---

# 100. History + patch

AXPATCH can request:

```text id="q4r6s8"
historical target identity
current symbol identity
rename/move lineage
```

for robust rebase/cherry-pick.

---

# 101. History + diff

AXDIFF can compare:

```text id="u0v2w4"
revision snapshots
```

without reloading source manually.

---

# 102. History + test

AXTEST can identify:

```text id="x6y8z0"
tests affected by historical change
regression introduction window
API/ABI change history
```

Actual regression proof remains AXTEST's responsibility.

---

# 103. Regression search

AXHISTORY may provide candidate revisions:

```text id="a2b4c6"
R10
R11
R12
...
R17
```

AXTEST executes tests against selected revisions.

AXHISTORY does not execute code.

---

# 104. Semantic bisect support

Pipeline:

```text id="g8h0j2"
AXHISTORY
   ↓
candidate revision
   ↓
AXBUILD
   ↓
AXTEST
   ↓
pass/fail
   ↓
AXHISTORY narrows interval
```

This creates a semantic-aware bisect foundation.

---

# 105. Bisect semantics

Candidate selection may use:

```text id="k4l6m8"
revision DAG topology
semantic change density
affected symbol lineage
```

but actual pass/fail comes from AXTEST.

---

# 106. Performance

History query target:

```text id="n0p2r4"
O(log N + K)
```

where:

- `N` = history size;
- `K` = returned events.

Symbol history should not require scanning every revision.

---

# 107. Storage efficiency

Use:

```text id="t6u8v0"
content addressing
Merkle DAG
structural sharing
compressed event streams
incremental indexes
```

to avoid storing duplicate source/semantic state.

---

# 108. Deterministic export

Export:

```text id="x2y4z6"
history(symbol)
```

must have deterministic ordering.

No dependence on:

- hash-map iteration;
- filesystem ordering;
- thread completion order.

---

# 109. Public API

Core:

```text id="a8b0c2"
create_revision()
read_revision()
list_parents()
is_ancestor()
merge_base()

symbol_history()
property_history()
change_history()

api_history()
abi_history()
dependency_history()

semantic_blame()

diff_revisions()
patch_between()

branches()
tags()

validate()
index()
```

---

# 110. API signatures

Conceptual:

```text id="d4e6f8"
RevisionId commit(
    Snapshot,
    PatchSet,
    CommitMetadata
)

Revision get_revision(RevisionId)

RevisionList ancestors(RevisionId)

optional<RevisionId> merge_base(
    RevisionId,
    RevisionId
)

SymbolHistory symbol_history(
    SymbolId
)

PropertyHistory property_history(
    SemanticId,
    PropertyId
)

ApiHistory api_history(
    RevisionRange
)

AbiHistory abi_history(
    RevisionRange
)

PatchSet patch_between(
    RevisionId,
    RevisionId
)
```

---

# 111. ABI

`AXHISTORY_ABI_1` exposes stable handles:

```text id="g0h2j4"
RevisionId
SymbolId
ChangeId
PatchId
BranchId
TagId
HistoryEventId
SnapshotId
```

Không expose internal graph pointers.

---

# 112. ABI stability

Changing:

```text id="k6l8m0"
Revision
SymbolHistory
HistoryEvent
```

binary layout requires a new ABI revision or compatible extension mechanism.

---

# 113. Serialization

Canonical `.axhistory` must include:

```text id="n2p4r6"
schema
repository identity
revision graph
semantic roots
patch references
lineage
refs
provenance
indexes
integrity hashes
```

---

# 114. Partial loading

Client chỉ cần:

```text id="t8v0x2"
Revision R
Symbol S123
```

không phải load toàn bộ repository.

---

# 115. Streaming history

Large history can stream:

```text id="y4z6a8"
revision events
```

in canonical order.

Useful for:

- IDE timeline;
- AI context;
- export;
- migration.

---

# 116. Migration

A history schema migration must be:

```text id="b0c2d4"
explicit
deterministic
versioned
testable
```

Never mutate old data ambiguously.

---

# 117. Repository integrity

Canonical history root:

```text id="e6f8g0"
HistoryRoot =
hash(
    schema,
    refs,
    revision_graph_root,
    lineage_root
)
```

provides repository-level identity.

---

# 118. History snapshot

```text id="i2j4k6"
HistorySnapshot {
    root
    schema
    refs
    timestamp_info
}
```

Timestamp may be informational only.

---

# 119. Reproducibility

Given the same canonical revision graph:

```text id="m8n0p2"
history query
```

must return identical semantic results.

---

# 120. Repository-independent semantic history

Một project có thể được chuyển giữa:

```text id="q4r6s8"
Git
Mercurial
custom VCS
local-only history
```

mà semantic history vẫn giữ nguyên nếu Revision/Patch/Snapshot identities được preserved.

Đây là mục tiêu quan trọng của AXHISTORY.

---

# 121. VCS adapter boundary

```text id="u0v2w4"
External VCS
     ↓
AXVCS adapter
     ↓
AXHISTORY
```

AXHISTORY không được hard-code Git semantics vào core.

---

# 122. Branch operations

AXHISTORY có thể cung cấp:

```text id="x6y8z0"
create_branch()
move_branch()
delete_branch()
get_head()
```

nhưng permission/authentication nằm ngoài semantic core.

---

# 123. Tag operations

```text id="a2b4c6"
create_tag()
get_tag()
list_tags()
```

Immutable tags được khuyến nghị ở repository policy level.

---

# 124. History graph visualization data

AXHISTORY có thể xuất:

```text id="g8h0j2"
RevisionGraphView
SymbolTimelineView
DependencyTimelineView
APIChangeView
ABIChangeView
```

UI rendering thuộc AXIDE/AXGUI.

---

# 125. AI history explanation

AI context có thể chứa:

```text id="k4l6m8"
Symbol:
    S123

Timeline:
    R10 add
    R18 modify
    R22 rename
    R31 move
    R40 API change

Patch:
    P88

ABI:
    H1 → H2
```

AI chỉ diễn giải evidence đã được AXHISTORY cung cấp.

---

# 126. Provenance hierarchy

History event provenance:

```text id="n0p2r4"
SOURCE
PATCH
MERGE
GENERATED
AI_PROPOSAL
USER
EXTERNAL
```

---

# 127. Merge provenance

Merge revision phải ghi:

```text id="t6u8v0"
parents
merge_base
AXMERGE result
resolution set
conflict count
```

---

# 128. Resolution provenance

Nếu merge conflict được giải quyết:

```text id="x2y4z6"
Conflict C1
 ↓
Resolution R1
 ↓
Patch P2
 ↓
Revision R50
```

History phải giữ chuỗi này.

---

# 129. Auditability

Một semantic change phải có khả năng truy ngược:

```text id="a8b0c2"
Current Symbol
 ↓
Current Revision
 ↓
Patch
 ↓
Historical Revision
 ↓
Original Change
```

nếu repository vẫn chứa lineage.

---

# 130. 40 invariants

### HISTORY-INV-01
Revision graph is a DAG.

### HISTORY-INV-02
RevisionId is deterministic.

### HISTORY-INV-03
Revision semantic content is immutable.

### HISTORY-INV-04
Parent relationships are explicit.

### HISTORY-INV-05
Merge revisions preserve all parents.

### HISTORY-INV-06
Revision identity does not depend on timestamp.

### HISTORY-INV-07
Symbol lineage prefers SymbolId.

### HISTORY-INV-08
Inferred lineage is explicitly marked.

### HISTORY-INV-09
Rename preserves lineage when identity is preserved.

### HISTORY-INV-10
Move preserves lineage when identity is preserved.

### HISTORY-INV-11
One-to-many symbol transformations are representable.

### HISTORY-INV-12
Many-to-one symbol transformations are representable.

### HISTORY-INV-13
Remove does not erase historical lineage.

### HISTORY-INV-14
Reappearance does not imply identity automatically.

### HISTORY-INV-15
Property-level history is supported.

### HISTORY-INV-16
API history is distinct from source history.

### HISTORY-INV-17
ABI history is distinct from API history.

### HISTORY-INV-18
AXABI remains ABI authority.

### HISTORY-INV-19
Dependency history is structurally represented.

### HISTORY-INV-20
Patch history references canonical AXPATCH identities.

### HISTORY-INV-21
Merge history references AXMERGE provenance.

### HISTORY-INV-22
AXDIFF provides difference analysis.

### HISTORY-INV-23
AXHISTORY does not execute source code.

### HISTORY-INV-24
AI cannot silently rewrite history.

### HISTORY-INV-25
AI proposals are distinct from accepted changes.

### HISTORY-INV-26
Derived indexes are not canonical truth.

### HISTORY-INV-27
Indexes can be deterministically rebuilt.

### HISTORY-INV-28
Partial history never implies absence of history.

### HISTORY-INV-29
Missing ancestors are represented as unknown.

### HISTORY-INV-30
Historical compiler validity is distinct from current validity.

### HISTORY-INV-31
Revision target/ABI identity is preserved.

### HISTORY-INV-32
Canonical serialization is deterministic.

### HISTORY-INV-33
Query ordering is deterministic.

### HISTORY-INV-34
History compaction preserves semantic lineage.

### HISTORY-INV-35
Revert uses semantic patch semantics.

### HISTORY-INV-36
Cherry-pick uses patch/rebase semantics.

### HISTORY-INV-37
Untrusted history is resource-limited.

### HISTORY-INV-38
Malformed cycles are rejected.

### HISTORY-INV-39
Provenance survives serialization.

### HISTORY-INV-40
AXHISTORY never invents historical facts absent from its evidence.

---

# 131. AXTEST requirements

AXTEST phải có test suite:

```text id="g0h2j4"
revision identity
parent DAG
merge revisions
symbol lineage
rename
move
split
merge
remove
resurrection ambiguity
property blame
API history
ABI history
dependency history
patch references
partial history
index rebuild
serialization
determinism
security
```

---

# 132. Algebraic tests

### Revision identity

Same canonical revision content:

```text id="k6l8m0"
→ same RevisionId
```

---

### Parent sensitivity

Same semantic tree but different parent:

```text id="n2p4r6"
→ different RevisionId
```

because ancestry is part of revision identity.

---

### Timestamp independence

Changing timestamp metadata:

```text id="t8v0x2"
→ semantic RevisionId unchanged
```

when timestamp is non-semantic metadata.

---

### Index equivalence

```text id="y4z6a8"
query(indexed_history)
=
query(rebuilt_index)
```

---

# 133. Performance Definition

For symbol history with `K` relevant events:

```text id="b0c2d4"
O(log N + K)
```

is target behavior.

Repository-wide scans should not be required for normal symbol-history queries.

---

# 134. Definition of Done

`AXHISTORY 5.0` hoàn thành khi:

- [x] Semantic revision DAG được định nghĩa.
- [x] Revision identity được định nghĩa.
- [x] Symbol-centric lineage được định nghĩa.
- [x] Rename/move lineage được định nghĩa.
- [x] Symbol split/merge lineage được định nghĩa.
- [x] Property-level history được định nghĩa.
- [x] Semantic blame được định nghĩa.
- [x] API history được định nghĩa.
- [x] ABI history được định nghĩa.
- [x] Dependency history được định nghĩa.
- [x] Branch/tag semantics được định nghĩa.
- [x] Merge revision được định nghĩa.
- [x] Revert/cherry-pick boundary được định nghĩa.
- [x] AXDIFF/AXPATCH/AXMERGE integration được định nghĩa.
- [x] AXCOMPILER/AXABI integration được định nghĩa.
- [x] AXBUILD/AXPACKAGE integration được định nghĩa.
- [x] AI history context được định nghĩa.
- [x] AI history mutation restrictions được định nghĩa.
- [x] Incremental Merkle storage được định nghĩa.
- [x] History indexing được định nghĩa.
- [x] Partial history semantics được định nghĩa.
- [x] Deterministic serialization được định nghĩa.
- [x] Security/resource limits được định nghĩa.
- [x] 40 invariants được đóng băng.
- [x] `AXHISTORY_ABI_1` được đóng băng.
- [x] `AXHISTORY_SCHEMA_1` được đóng băng.

**AXHISTORY 5.0 — FROZEN.**

---

# 135. Vị trí trong hệ thống hiện tại

Chuỗi **Change/Version Intelligence** của Axiom hiện là:

```text
                         SOURCE
                           │
                           ▼
                       AXCOMPILER
                           │
                     Semantic Model
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
         AXDIFF         AXPATCH        AXHISTORY
            │              │              │
       detect change      apply        remember
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                        AXMERGE
                           │
                      combine changes
                           │
                           ▼
                       AXHISTORY
                     new revision
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
           AXBUILD       AXTEST         AXIDE
```

Có thể coi:

```text
AXDIFF    = Difference
AXPATCH   = Change
AXMERGE   = Composition
AXHISTORY = Lineage
```

Bốn lớp này tạo thành **semantic change infrastructure** của Axiom.

---

# BOOTSTRAP-798 — AXVCS

**Native Axiom Version Control Abstraction, Content-Addressed Repository, Semantic Revision/Branch/Tag Transport, Distributed Object Store, Repository Protocol, Commit/Fetch/Push/Pull, Remote Synchronization, Conflict-Aware Integration, Sparse/Partial History, CAS Storage, Pack/Delta Compression, Repository Integrity & Version-Control ABI 5.0**

AXVCS sẽ là lớp **version-control transport/storage** phía dưới `AXHISTORY`, nhưng giữ ranh giới rất rõ:

```text
AXVCS  = lưu trữ + đồng bộ + repository
AXHISTORY = ý nghĩa + lineage + semantic history
AXPATCH = thay đổi
AXMERGE = hợp nhất
AXDIFF = so sánh
```

Mục tiêu là Axiom có **native VCS abstraction**, không buộc compiler/IDE/AI phải phụ thuộc trực tiếp vào Git, đồng thời vẫn cho phép adapter Git và các VCS khác ở lớp ngoài.