# BOOTSTRAP-795 — AXMERGE
## Native Axiom Semantic Merge Engine, Three-Way Source/AST/IR/API/ABI Merge, Conflict Detection, Symbol Identity Preservation, Struct/Enum/Trait/Generic Merge, Build Artifact Merge, Dependency-Aware Merge Planning, Deterministic Merge Graph, Conflict Model, Merge Resolution API & Merge ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXMERGE`  
**ABI:** `AXMERGE_ABI_1`  
**Schema:** `AXMERGE_SCHEMA_1`  
**Artifact:** `.axmerge`  
**Primary consumers:** `AXIDE`, `AXCODEEDITOR`, `AXCOMPILER`, `AXDOC`, `AXTEST`, `AXBUILD`, `AXPACKAGE`, `AXDIFF`, `AXABI`

---

# 1. Mục tiêu

`AXMERGE` là **semantic merge engine** của Axiom.

Nó không được thiết kế như một công cụ merge text đơn thuần.

Mô hình canonical:

```text
                 BASE
                   │
          ┌────────┴────────┐
          ▼                 ▼
        LEFT               RIGHT
          │                 │
          └────────┬────────┘
                   ▼
                AXMERGE
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Auto-Merge   Conflicts   Provenance
       │           │           │
       └───────────┼───────────┘
                   ▼
             Merge Result
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
      Source      API        ABI
        │          │          │
        └──────────┼──────────┘
                   ▼
              AXCOMPILER
```

AXMERGE phải có khả năng hiểu:

- source;
- token;
- AST;
- module;
- symbol;
- type;
- function;
- struct;
- enum;
- union;
- trait;
- generic;
- attribute;
- effect;
- API;
- ABI;
- dependency;
- build configuration;
- generated artifact;
- debug metadata;
- AI metadata.

---

# 2. Nguyên tắc thiết kế bất biến

## MERGE-PRINCIPLE-01 — Three-way là mô hình chuẩn

Mọi semantic merge chính thức phải có:

```text
BASE
LEFT
RIGHT
```

Two-way merge chỉ là compatibility mode.

---

## MERGE-PRINCIPLE-02 — Không được đoán âm thầm

Nếu engine không đủ bằng chứng:

```text
UNKNOWN
```

phải được giữ là `UNKNOWN`.

Không được biến:

```text
unknown
```

thành:

```text
unchanged
```

và không được tự chọn LEFT/RIGHT.

---

## MERGE-PRINCIPLE-03 — Semantic trước textual

Thứ tự ưu tiên:

```text
Symbol Identity
      ↓
Semantic Structure
      ↓
AST
      ↓
Token
      ↓
Text
```

Textual merge chỉ là fallback.

---

## MERGE-PRINCIPLE-04 — SymbolId được ưu tiên tuyệt đối

Nếu BASE, LEFT, RIGHT cùng chứa:

```text
SymbolId = S123
```

thì đây là cùng một symbol trừ khi metadata chứng minh artifact không tương thích.

---

## MERGE-PRINCIPLE-05 — Same change chỉ merge một lần

Nếu:

```text
BASE:  x = 10
LEFT:  x = 20
RIGHT: x = 20
```

kết quả:

```text
x = 20
```

không phải conflict.

---

## MERGE-PRINCIPLE-06 — Independent change tự động hợp nhất

```text
BASE:
a = 1
b = 2

LEFT:
a = 10
b = 2

RIGHT:
a = 1
b = 20
```

→

```text
a = 10
b = 20
```

---

## MERGE-PRINCIPLE-07 — Overlap semantic phải explicit

```text
BASE:  x = 10
LEFT:  x = 20
RIGHT: x = 30
```

→ conflict.

Không tự chọn `20` hoặc `30`.

---

# 3. Boundary

AXMERGE sở hữu:

```text
merge planning
change detection
identity matching
semantic merge
conflict generation
resolution
provenance
canonical merge serialization
```

AXMERGE không sở hữu:

```text
compiler semantics
type checker
linker
binary emission
package downloading
version solving
code execution
debugger execution
```

Các subsystem tương ứng:

```text
AXCOMPILER → semantic truth
AXDIFF     → difference analysis
AXABI      → ABI truth
AXBUILD    → build truth
AXPACKAGE  → package/dependency truth
AXTEST     → verification
AXIDE      → interaction
```

---

# 4. Kiến trúc

```text
                       AXMERGE
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   Input Loader       Merge Planner     Policy Engine
        │                 │                 │
        ▼                 ▼                 ▼
   Identity Index     Change Graph      Merge Rules
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                  Semantic Merge Engine
                          │
       ┌────────────┬─────┼─────┬────────────┐
       ▼            ▼     ▼     ▼            ▼
    Source         AST   API   ABI       Dependency
       │            │     │     │            │
       └────────────┴─────┼─────┴────────────┘
                          ▼
                    Conflict Engine
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
          Auto Resolution      Explicit Conflict
                │                   │
                └─────────┬─────────┘
                          ▼
                    Merge Result
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
          Serializer   Validator   Consumers
```

---

# 5. Merge Context

```text
struct MergeContext {
    base: MergeInput
    left: MergeInput
    right: MergeInput

    target: TargetIdentity
    abi: AbiIdentity

    policy: MergePolicy
    strategy: MergeStrategy

    identity_index: IdentityIndex
    dependency_graph: DependencyGraph

    revision: MergeRevision
}
```

`MergeContext` phải immutable sau khi merge bắt đầu.

---

# 6. MergeInput

```text
enum MergeInputKind {
    SOURCE,
    AST,
    SEMANTIC,
    IR,
    OBJECT,
    API,
    ABI,
    BUILD_CONFIG,
    PACKAGE_MANIFEST,
    LOCKFILE,
    GENERATED,
    DEBUG_INFO,
    METADATA
}
```

```text
struct MergeInput {
    id: ArtifactId
    kind: MergeInputKind

    content_hash: Hash
    semantic_hash: optional<Hash>

    target: optional<TargetIdentity>
    abi: optional<AbiIdentity>

    provenance: Provenance
}
```

---

# 7. Merge model

Canonical:

```text
Merge(BASE, LEFT, RIGHT, POLICY)
    → MergeResult
```

Pseudo-algorithm:

```text
1. validate BASE/LEFT/RIGHT
2. construct identity index
3. calculate semantic deltas:
       ΔL = Diff(BASE, LEFT)
       ΔR = Diff(BASE, RIGHT)
4. normalize changes
5. detect equivalent changes
6. detect independent changes
7. detect overlapping changes
8. apply non-conflicting changes
9. create explicit conflicts
10. apply only policy-authorized resolutions
11. validate merged semantic model
12. validate API
13. validate ABI
14. validate dependencies
15. emit provenance
16. serialize deterministic result
```

---

# 8. Change representation

```text
enum ChangeKind {
    ADD,
    REMOVE,
    MODIFY,
    RENAME,
    MOVE,
    REORDER,
    TYPE_CHANGE,
    SIGNATURE_CHANGE,
    ATTRIBUTE_CHANGE,
    VISIBILITY_CHANGE,
    EFFECT_CHANGE,
    DEPENDENCY_CHANGE,
    ABI_CHANGE,
    API_CHANGE
}
```

```text
struct MergeChange {
    id: ChangeId

    side: MergeSide
    kind: ChangeKind

    target: SemanticId
    parent: optional<SemanticId>

    before: optional<ValueHash>
    after: optional<ValueHash>

    location: SourceLocation
    provenance: Provenance

    confidence: Confidence
}
```

---

# 9. Identity system

Identity levels:

```text
Level 0: SymbolId
Level 1: DeclarationId
Level 2: TypeId
Level 3: Structural fingerprint
Level 4: Signature fingerprint
Level 5: AST similarity
Level 6: textual similarity
```

Matching must proceed from strongest to weakest.

```text
EXACT
STRUCTURAL
INFERRED
UNKNOWN
```

Every non-exact identity match must record its basis.

---

# 10. Rename detection

Example:

```text
BASE:
fn calculate_total()

LEFT:
fn compute_total()

RIGHT:
fn calculate_total() { ...changed... }
```

AXMERGE must recognize:

```text
RENAME:
calculate_total → compute_total
```

rather than:

```text
REMOVE calculate_total
ADD compute_total
```

provided semantic identity evidence is sufficient.

If rename confidence is insufficient:

```text
CONFLICT_RENAME_IDENTITY
```

must be generated rather than silently assuming identity.

---

# 11. Move detection

Moving a declaration between modules:

```text
BASE:
module a
    fn foo()

LEFT:
module b
    fn foo()

RIGHT:
module a
    fn foo() { changed }
```

must be represented as:

```text
MOVE(foo, a → b)
MODIFY(foo)
```

and not merely:

```text
REMOVE + ADD
```

---

# 12. Source merge

Source merge hierarchy:

```text
file
 ↓
module
 ↓
declaration
 ↓
member
 ↓
expression
 ↓
token
 ↓
character
```

The engine must descend to a lower level only when higher-level semantic merging cannot resolve the change.

Example:

```text
fn foo() {
    return a + b;
}
```

LEFT changes:

```text
a + c
```

RIGHT changes:

```text
a * b
```

→ expression conflict.

---

# 13. AST merge

AST nodes must be matched using:

```text
NodeId
SymbolId
parent identity
node kind
structural position
semantic fingerprint
```

AST ordering alone must never be the sole identity mechanism.

---

# 14. Function merge

Independent modifications:

```text
BASE:
fn foo(a) {
    x()
}
```

LEFT:

```text
fn foo(a) {
    x()
    y()
}
```

RIGHT:

```text
fn foo(a) {
    z()
    x()
}
```

can be merged if statement insertion positions are non-conflicting.

Conflicting replacement of the same statement produces:

```text
FUNCTION_BODY_CONFLICT
```

---

# 15. Function signature merge

```text
BASE:
fn foo(x: i32) -> i32
```

LEFT:

```text
fn foo(x: i64) -> i32
```

RIGHT:

```text
fn foo(x: i32) -> f32
```

→ two distinct signature modifications.

Result:

```text
CONFLICT_SIGNATURE
```

The engine must not synthesize:

```text
fn foo(x: i64) -> f32
```

automatically.

---

# 16. Struct merge

Example:

```text
BASE:
struct User {
    id: u64
}
```

LEFT:

```text
struct User {
    id: u64
    name: String
}
```

RIGHT:

```text
struct User {
    id: u64
    age: u32
}
```

Result:

```text
struct User {
    id: u64
    name: String
    age: u32
}
```

provided field insertion/layout policy permits it.

---

# 17. Struct same-field conflict

```text
BASE:
name: String

LEFT:
name: SmallString

RIGHT:
name: StringView
```

→

```text
STRUCT_FIELD_TYPE_CONFLICT
```

No automatic type synthesis.

---

# 18. Struct layout

Layout changes require additional ABI analysis.

A source merge may succeed:

```text
struct User {
    id: u64
    age: u32
}
```

but ABI validation may subsequently report:

```text
ABI_LAYOUT_CHANGED
```

This distinction is mandatory.

```text
SOURCE_MERGE_SUCCESS
≠
ABI_COMPATIBILITY_SUCCESS
```

---

# 19. Enum merge

Independent variant additions:

```text
BASE:
enum Color {
    Red
}
```

LEFT:

```text
Red
Green
```

RIGHT:

```text
Red
Blue
```

→

```text
Red
Green
Blue
```

unless explicit discriminants or ordering policies create a collision.

---

# 20. Enum discriminant conflict

```text
BASE:
A = 1
B = 2
```

LEFT:

```text
C = 3
```

RIGHT:

```text
C = 4
```

→ conflict.

No automatic renumbering.

Reason:

Changing discriminants may be an ABI/data-format compatibility break.

---

# 21. Union merge

Union members are identity-bearing fields.

Independent additions may merge.

Conflicting changes to the same member:

```text
BASE:
x: i32

LEFT:
x: i64

RIGHT:
x: f64
```

→ `UNION_MEMBER_CONFLICT`.

---

# 22. Trait merge

Independent associated items merge.

```text
trait Drawable {
    draw()
}
```

LEFT:

```text
draw()
bounds()
```

RIGHT:

```text
draw()
serialize()
```

→

```text
draw()
bounds()
serialize()
```

provided no signature/name collision exists.

---

# 23. Trait implementation conflicts

If both sides introduce incompatible implementations:

```text
impl Drawable for Widget
```

and:

```text
impl Drawable for Widget
```

with different bodies, AXMERGE must report:

```text
DUPLICATE_TRAIT_IMPL_CONFLICT
```

unless the language's coherence rules explicitly permit both.

---

# 24. Generic merge

Generic parameter identity is positional only as a fallback.

Preferred:

```text
GenericParamId
```

Example:

```text
fn map<T>(...)
```

LEFT:

```text
fn map<T, U>(...)
```

RIGHT:

```text
fn map<T>(...) where T: Copy
```

may merge:

```text
fn map<T, U>(...)
where
    T: Copy
```

if the added parameter and constraint are independent.

---

# 25. Generic constraint conflict

```text
BASE:
T

LEFT:
T: Copy

RIGHT:
T: !Copy
```

→ explicit generic constraint conflict.

The engine must not invent a composite constraint unless the language semantic model proves it equivalent.

---

# 26. Attributes/effects

Merge independently:

```text
@inline
@cold
@deprecated
```

but conflicting semantic attributes must be analyzed.

Example:

```text
BASE:
@inline

LEFT:
@noinline

RIGHT:
@inline
```

→ LEFT's modification is not automatically discarded.

Result depends on BASE-relative change:

```text
LEFT = changed
RIGHT = unchanged
```

therefore merged result:

```text
@noinline
```

This is a critical three-way rule.

---

# 27. Visibility merge

```text
BASE:
private fn foo()

LEFT:
public fn foo()

RIGHT:
private fn foo()
```

→ `public`.

But:

```text
LEFT:
public

RIGHT:
internal
```

→ conflict because both changed the same semantic property differently.

---

# 28. Effect merge

Effects are semantic.

Example:

```text
fn foo() -> i32
```

LEFT:

```text
fn foo() throws -> i32
```

RIGHT:

```text
fn foo() async -> i32
```

These are not text-level independent modifications.

AXMERGE must classify:

```text
EFFECT_SET_CONFLICT
```

unless the effect algebra proves composition valid.

---

# 29. Module/import merge

Imports are modeled as sets plus ordering metadata.

```text
BASE:
import A

LEFT:
import B

RIGHT:
import C
```

→

```text
import A
import B
import C
```

Duplicate equivalent imports are coalesced.

Conflicting aliases:

```text
import foo as x
import bar as x
```

→ `IMPORT_ALIAS_CONFLICT`.

---

# 30. Dependency graph

AXMERGE maintains:

```text
Package
   ↓
Module
   ↓
Import
   ↓
Symbol
   ↓
Type
   ↓
Build Target
```

Changes must propagate through this graph.

A local source merge that creates an invalid dependency cycle is not considered a complete successful merge.

---

# 31. Dependency conflict

Example:

```text
BASE:
foo = 1.4

LEFT:
foo = 2.0

RIGHT:
foo = 3.0
```

→

```text
DEPENDENCY_VERSION_CONFLICT
```

unless package constraints prove a common valid version.

---

# 32. Feature conflict

```text
BASE:
foo { default }

LEFT:
foo { gpu }

RIGHT:
foo { no-gpu }
```

→ explicit feature conflict.

---

# 33. Lockfile merge

Lockfiles are structured artifacts.

They must not be merged as arbitrary text.

Merge:

```text
package identity
version
source
checksum
dependencies
features
target
```

independently.

Checksum mismatch must produce:

```text
LOCKFILE_INTEGRITY_CONFLICT
```

---

# 34. API merge

API model:

```text
API
 ├ symbols
 ├ visibility
 ├ signatures
 ├ types
 ├ traits
 ├ constants
 ├ attributes
 └ deprecations
```

AXMERGE must generate an API delta after merging.

Example:

```text
API_REMOVE
API_ADD
API_SIGNATURE_CHANGE
API_VISIBILITY_CHANGE
API_TYPE_CHANGE
```

API merge success does not imply backward compatibility.

---

# 35. ABI merge

AXMERGE delegates ABI truth to AXABI.

Pipeline:

```text
Merged Semantic Model
        ↓
AXABI validation
        ↓
AbiCompatibilityReport
```

Potential results:

```text
ABI_COMPATIBLE
ABI_SOURCE_COMPATIBLE
ABI_BREAKING
ABI_INCOMPARABLE
ABI_UNKNOWN
```

AXMERGE never silently labels `UNKNOWN` as compatible.

---

# 36. Binary merge boundary

Native binaries are **not source merge artifacts**.

Do not attempt:

```text
LEFT.exe + RIGHT.exe → MERGED.exe
```

as the normal model.

Instead:

```text
LEFT source
RIGHT source
BASE source
       ↓
    AXMERGE
       ↓
merged source
       ↓
AXCOMPILER
       ↓
AXLINKER
       ↓
new binary
```

AXBINARY/AXDIFF can compare resulting binaries.

---

# 37. Object artifact policy

Object files may be inspected for merge planning, but native object binaries are normally rebuilt.

AXMERGE may merge:

```text
build configuration
source metadata
dependency metadata
semantic artifact metadata
```

but not arbitrarily splice machine code.

---

# 38. Generated artifact policy

Every generated artifact must declare:

```text
GeneratedPolicy {
    source_of_truth
    generator
    generator_version
    regeneration_command
    merge_policy
}
```

Possible policies:

```text
REGENERATE
MERGE_STRUCTURED
KEEP_IF_IDENTICAL
MANUAL
FORBID
```

Default:

```text
REGENERATE
```

for compiler-generated outputs.

---

# 39. Debug metadata

Debug information is derived from source/build state.

Therefore:

```text
source merge
      ↓
recompile
      ↓
new debug info
```

is preferred.

Manual merging of stale line tables must not become source truth.

---

# 40. Conflict taxonomy

```text
TEXT_CONFLICT
TOKEN_CONFLICT
AST_CONFLICT
SYMBOL_CONFLICT
RENAME_CONFLICT
MOVE_CONFLICT
SIGNATURE_CONFLICT
TYPE_CONFLICT
STRUCT_CONFLICT
ENUM_CONFLICT
UNION_CONFLICT
TRAIT_CONFLICT
GENERIC_CONFLICT
ATTRIBUTE_CONFLICT
EFFECT_CONFLICT
VISIBILITY_CONFLICT
IMPORT_CONFLICT
DEPENDENCY_CONFLICT
PACKAGE_CONFLICT
LOCKFILE_CONFLICT
API_CONFLICT
ABI_CONFLICT
BUILD_CONFLICT
GENERATED_CONFLICT
METADATA_CONFLICT
DEBUG_CONFLICT
IDENTITY_CONFLICT
POLICY_CONFLICT
VALIDATION_CONFLICT
```

---

# 41. Conflict model

```text
struct MergeConflict {
    id: ConflictId

    kind: ConflictKind
    severity: ConflictSeverity

    target: SemanticId

    base: ConflictValue
    left: ConflictValue
    right: ConflictValue

    evidence: ConflictEvidence

    resolution_state: ResolutionState

    provenance: Provenance
}
```

Severity:

```text
INFO
WARNING
ERROR
FATAL
```

---

# 42. Deterministic ConflictId

Conflict ID must be derived from canonical input:

```text
hash(
    schema_version,
    base_identity,
    left_identity,
    right_identity,
    target_identity,
    conflict_kind,
    normalized_values
)
```

No random UUID may determine semantic conflict identity.

---

# 43. Conflict evidence

```text
struct ConflictEvidence {
    identity_basis
    base_change
    left_change
    right_change

    source_locations
    semantic_paths

    confidence
    affected_symbols
    affected_dependencies
}
```

This allows IDE and AI systems to explain *why* a conflict exists.

---

# 44. Auto-resolvable conflict

Some conflicts are technically represented but policy can resolve them safely.

Examples:

```text
duplicate identical import
same annotation added twice
same field addition
same formatting change
same semantic rename
```

Resolution must still be recorded.

---

# 45. Resolution model

```text
enum ResolutionKind {
    TAKE_BASE,
    TAKE_LEFT,
    TAKE_RIGHT,
    COMBINE,
    EDIT,
    REJECT_CHANGE,
    RENAME,
    MOVE,
    REORDER,
    REGENERATE,
    DEFER
}
```

```text
struct MergeResolution {
    conflict_id: ConflictId
    kind: ResolutionKind

    value: optional<Value>
    resolver: ResolutionSource

    justification: optional<String>
}
```

---

# 46. Resolution provenance

```text
enum ResolutionSource {
    AUTOMATIC,
    USER,
    POLICY,
    SCRIPT,
    AI_PROPOSAL
}
```

`AI_PROPOSAL` is never equivalent to `USER`.

An AI-generated resolution must remain pending until explicitly accepted.

---

# 47. AI-assisted merge

Architecture:

```text
AXMERGE
   ↓
Conflict Context
   ↓
AI Proposal
   ↓
Candidate Resolution
   ↓
Human / Policy Acceptance
   ↓
AXMERGE
```

AI may:

- explain conflicts;
- propose code;
- identify likely rename;
- suggest dependency resolution;
- suggest API-compatible changes;
- summarize affected symbols.

AI may not:

- silently alter files;
- mark unresolved conflicts as resolved;
- suppress ABI conflicts;
- suppress dependency conflicts;
- execute arbitrary code.

---

# 48. Merge policy

```text
struct MergePolicy {
    identity_policy
    rename_policy
    move_policy

    source_policy
    api_policy
    abi_policy

    dependency_policy
    generated_policy

    ordering_policy
    formatting_policy

    unknown_policy
    conflict_policy
}
```

Policies must themselves have stable IDs/hashes.

---

# 49. Unknown policy

Allowed:

```text
FAIL
REPORT
REQUIRE_MANUAL
```

Default:

```text
REQUIRE_MANUAL
```

Never:

```text
ASSUME_UNCHANGED
```

as a default.

---

# 50. Ordering policy

For declarations/fields/variants:

```text
PRESERVE_BASE_ORDER
PRESERVE_SIDE_ORDER
CANONICAL_ORDER
MANUAL_ON_CONFLICT
```

Default should preserve semantic/source locality while remaining deterministic.

---

# 51. Merge graph

AXMERGE builds a DAG:

```text
MergeGraph
 ├ BaseNode
 ├ LeftNode
 ├ RightNode
 │
 ├ ChangeNode
 ├ IdentityNode
 ├ DependencyNode
 ├ ConflictNode
 └ ResolutionNode
```

Edges:

```text
DERIVES_FROM
MODIFIES
DEPENDS_ON
CONFLICTS_WITH
RESOLVES
PRESERVES
REPLACES
```

---

# 52. Merge plan

```text
struct MergePlan {
    graph: MergeGraph

    ordered_operations: [MergeOperation]

    conflicts: [ConflictId]

    estimated_cost: u64

    plan_hash: Hash
}
```

Operations must form a deterministic topological order.

---

# 53. Merge operation

```text
enum MergeOperation {
    Add
    Remove
    Modify
    Rename
    Move
    Reorder
    MergeChildren
    ResolveConflict
    Regenerate
    Validate
}
```

Every operation references stable semantic identities.

---

# 54. Dependency-aware scheduling

Example:

```text
rename type A
      ↓
update function foo
      ↓
update trait impl
      ↓
update API
      ↓
validate ABI
```

AXMERGE must not validate a dependent node against an outdated intermediate semantic model.

---

# 55. Canonical merge result

```text
struct MergeResult {
    status: MergeStatus

    merged_source
    merged_semantic_model

    conflicts
    resolutions

    api_report
    abi_report
    dependency_report

    provenance
    diagnostics

    result_hash
}
```

Status:

```text
CLEAN
RESOLVED
CONFLICTED
INVALID
INCOMPARABLE
```

---

# 56. Clean vs resolved

```text
CLEAN
```

means no conflict required resolution.

```text
RESOLVED
```

means conflicts existed but every conflict now has an accepted resolution.

These states must not be collapsed.

---

# 57. Partial merge

AXMERGE may produce:

```text
PARTIAL
```

for IDE preview.

A partial merge must not be treated as buildable source unless validation succeeds.

---

# 58. Canonical source output

Output normalization must be deterministic.

Same:

```text
BASE
LEFT
RIGHT
POLICY
```

must produce the same:

```text
merged source
semantic model
conflict IDs
provenance
result hash
```

---

# 59. Formatting

Formatting must not create semantic conflicts.

Preferred:

```text
semantic merge
    ↓
canonical source
    ↓
AXFORMAT
```

rather than treating whitespace differences as meaningful semantic changes.

---

# 60. Text conflict markers

Traditional:

```text
<<<<<<< LEFT
=======
>>>>>>> RIGHT
```

are presentation only.

They are not part of AXMERGE's semantic representation.

IDE can render conflict markers derived from:

```text
ConflictId
SourceRange
ConflictKind
```

---

# 61. AXCODEEDITOR integration

AXCODEEDITOR receives:

```text
ConflictDecoration {
    conflict_id
    range
    kind
    severity
    alternatives
}
```

Resolution creates an AXEDITOR transaction.

AXMERGE remains the semantic authority.

---

# 62. AXIDE integration

AXIDE owns:

```text
merge session
conflict navigation
resolution UI
preview
branch/worktree state
save/apply lifecycle
```

AXMERGE owns:

```text
what conflicts exist
what identities match
what merge is semantically valid
```

---

# 63. AXDOC integration

After merge:

```text
merged semantic model
        ↓
AXDOC
        ↓
new API documentation
```

AXDOC may report:

```text
API additions
API removals
signature changes
deprecation changes
```

but does not resolve semantic conflicts.

---

# 64. AXTEST integration

AXTEST must test:

```text
source merge
AST merge
semantic merge
API merge
ABI validation
dependency merge
generated artifact policy
conflict serialization
resolution
determinism
```

---

# 65. Build integration

AXBUILD receives:

```text
MergeResult
```

only after:

```text
semantic validation
dependency validation
policy validation
```

Then:

```text
AXBUILD
 ↓
AXCOMPILER
 ↓
AXLINKER
```

---

# 66. Incremental merge

For large projects:

```text
changed files
      ↓
changed semantic nodes
      ↓
affected dependency closure
      ↓
partial merge
```

Unchanged subgraphs may be reused.

Cache key:

```text
hash(
    base_node_hash,
    left_node_hash,
    right_node_hash,
    policy_hash,
    schema_version
)
```

---

# 67. Merge cache

```text
MergeCacheEntry {
    key
    result_hash
    merged_node
    conflicts
    provenance
    schema_version
}
```

Cache must never be trusted across incompatible schema/ABI versions.

---

# 68. Parallelism

Independent merge graph components may run concurrently.

Constraint:

```text
parallel execution
      ↓
canonical deterministic commit order
```

No race may affect final output.

---

# 69. Large-project performance

Target complexity:

```text
O(N + C)
```

for mostly-independent semantic nodes, where:

- `N` = number of relevant semantic nodes;
- `C` = number of detected change relationships.

Avoid:

```text
O(N²)
```

global pairwise matching.

Use:

```text
SymbolId index
signature index
structural hash index
module index
dependency index
```

---

# 70. Memory model

AXMERGE should use immutable/shared semantic snapshots.

Conceptually:

```text
BASE ──────────────┐
LEFT ──────────────┼→ shared semantic graph
RIGHT ─────────────┘
                         ↓
                   persistent nodes
```

Do not duplicate entire projects merely to merge them.

---

# 71. No execution

AXMERGE must never execute:

- source code;
- build scripts;
- package scripts;
- macros with arbitrary execution;
- generated programs;
- user commands.

Any required semantic information must come from trusted artifacts or AXCOMPILER services.

---

# 72. Macro/generated semantics

If a macro's expansion is required for identity analysis:

```text
AXCOMPILER semantic artifact
```

may be consumed.

AXMERGE itself must not execute the macro.

---

# 73. Security

Untrusted merge inputs must be treated as hostile.

Protection against:

```text
path traversal
resource exhaustion
malformed AST
hash collision abuse
deep nesting
cyclic metadata
oversized conflict payload
malformed dependency graph
malicious generated metadata
```

Limits:

```text
max_nodes
max_depth
max_file_size
max_conflicts
max_dependency_edges
max_memory
max_time
```

---

# 74. Provenance

Every merged node must be attributable:

```text
BASE
LEFT
RIGHT
BOTH_SAME
COMBINED
RESOLVED
GENERATED
POLICY
```

Example:

```text
field name
    provenance = LEFT

field age
    provenance = RIGHT

field id
    provenance = BASE

field address
    provenance = COMBINED
```

---

# 75. Audit trail

```text
MergeAuditEntry {
    sequence
    operation
    target
    source
    previous_hash
    resulting_hash
    actor
    timestamp
}
```

Timestamps are informational and must not affect deterministic merge identity.

---

# 76. Merge session

```text
struct MergeSession {
    session_id
    context
    plan
    result
    resolutions

    state
}
```

State:

```text
CREATED
PLANNED
MERGING
CONFLICTED
RESOLVING
VALIDATING
COMPLETED
FAILED
```

---

# 77. Public API

Conceptual API:

```text
axmerge.create_context()
axmerge.plan()
axmerge.merge()
axmerge.list_conflicts()
axmerge.resolve()
axmerge.validate()
axmerge.export_result()
axmerge.export_provenance()
```

Detailed:

```text
MergeContextId create_context(MergeInputs, MergePolicy)

MergePlan plan(MergeContextId)

MergeResult merge(MergePlan)

ConflictList conflicts(MergeResult)

ResolutionResult resolve(
    MergeResult,
    MergeResolution
)

ValidationResult validate(MergeResult)

Bytes serialize(MergeResult)

MergeResult deserialize(Bytes)
```

---

# 78. Programmatic resolution API

Example:

```text
resolve(
    conflict = C123,
    resolution = TAKE_LEFT
)
```

or:

```text
resolve(
    conflict = C456,
    resolution = EDIT,
    value = NewSemanticNode(...)
)
```

Resolution must be validated before becoming final.

---

# 79. Merge ABI

`AXMERGE_ABI_1` must define stable representations for:

```text
MergeContext
MergeInput
MergePlan
MergeGraph
MergeChange
MergeConflict
MergeResolution
MergeResult
Provenance
MergeDiagnostics
```

ABI compatibility requires matching:

```text
AXMERGE_ABI_1
AXMERGE_SCHEMA_1
target ABI
semantic model version
```

---

# 80. ABI boundary rules

AXMERGE ABI must not expose unstable compiler-private AST layouts.

Use stable handles:

```text
SemanticId
SymbolId
TypeId
ArtifactId
ConflictId
PlanId
```

instead of raw pointers.

---

# 81. Serialization

`.axmerge` must contain:

```text
header
schema
input identities
target/ABI identity
policy
merge graph
changes
conflicts
resolutions
provenance
diagnostics
result
checksums
```

Canonical serialization is required.

---

# 82. Streaming

Large merge artifacts must support:

```text
stream read
stream write
chunk validation
partial inspection
```

An IDE should be able to inspect conflicts without loading the entire artifact into memory.

---

# 83. Remote merge

Remote AXMERGE service may accept:

```text
semantic artifacts
source snapshots
merge policy
```

but must not receive unnecessary source contents.

Authentication and authorization belong to platform/security layers.

---

# 84. Reproducibility

Given:

```text
B
L
R
P
S
```

where:

- B = BASE identity;
- L = LEFT identity;
- R = RIGHT identity;
- P = policy;
- S = schema;

then:

```text
Merge(B,L,R,P,S)
```

must produce the same canonical result.

---

# 85. Three-way correctness properties

AXTEST must verify:

### Identity preservation

If a symbol is unchanged:

```text
SymbolId(result) = SymbolId(BASE)
```

---

### Same-change coalescing

```text
ΔL == ΔR
```

→ one change.

---

### Independent-change composition

```text
ΔL ∩ ΔR = ∅
```

→ both applied.

---

### Conflict preservation

```text
ΔL(x) != ΔR(x)
```

on the same semantic property → explicit conflict.

---

### No silent loss

Every non-base change must be:

```text
APPLIED
REJECTED
CONFLICTED
```

and never disappear without provenance.

---

# 86. Rename correctness

Tests:

```text
rename only
rename + modify
rename on both sides identically
different rename
rename vs remove
rename vs modify
rename vs move
```

---

# 87. Move correctness

Tests:

```text
move only
move + modify
same move
different move
move vs delete
move vs rename
cross-module move
cross-package move
```

---

# 88. Struct correctness

Tests:

```text
add independent fields
remove independent fields
same field modification
different type modification
field rename
field reorder
layout-sensitive change
visibility change
default-value change
```

---

# 89. Enum correctness

Tests:

```text
variant additions
variant removals
same discriminant
different discriminant
variant rename
variant payload modification
ordering change
```

---

# 90. Generic correctness

Tests:

```text
parameter addition
parameter removal
constraint addition
constraint conflict
default parameter
variance-related semantic changes
generic rename
generic reorder
```

---

# 91. Dependency correctness

Tests:

```text
independent dependency additions
same version
different versions
compatible version ranges
incompatible ranges
feature conflict
target-specific dependency
lockfile checksum conflict
cycle introduction
```

---

# 92. API correctness

AXTEST must compare:

```text
merged API
expected API
AXDIFF API diff
```

and ensure no API change is lost.

---

# 93. ABI correctness

After merge:

```text
AXABI
   ↓
ABI report
```

must be reproducible.

ABI-breaking changes must remain visible even when source merge is clean.

---

# 94. Binary correctness

Workflow:

```text
BASE → compile → BINARY_BASE
LEFT → compile → BINARY_LEFT
RIGHT → compile → BINARY_RIGHT

MERGED → compile → BINARY_MERGED
```

Then:

```text
AXDIFF
```

compares artifacts.

AXMERGE itself does not infer correctness from binary bytes.

---

# 95. Crash/profile/replay boundary

These artifacts are diagnostic evidence.

They are not normally mergeable source state.

AXMERGE may preserve references:

```text
CrashArtifactId
ProfileArtifactId
ReplayArtifactId
```

but does not combine execution histories as if they were source.

---

# 96. Deterministic diagnostics

Diagnostics ordering:

```text
severity
semantic path
source location
ConflictId
```

must be deterministic.

---

# 97. Conflict navigation

Each conflict must expose:

```text
base range
left range
right range
semantic target
dependency impact
API impact
ABI impact
resolution state
```

This gives AXIDE enough information to navigate directly to the cause.

---

# 98. Semantic impact analysis

For every conflict:

```text
Conflict
   ↓
affected symbols
   ↓
affected modules
   ↓
affected APIs
   ↓
affected ABI
   ↓
affected targets
```

Impact is advisory unless validated by AXCOMPILER/AXABI.

---

# 99. Merge modes

```text
MERGE_SOURCE
MERGE_AST
MERGE_SEMANTIC
MERGE_API
MERGE_ABI
MERGE_DEPENDENCY
MERGE_BUILD
MERGE_METADATA
MERGE_COMBINED
```

`MERGE_COMBINED` is the default full-project mode.

---

# 100. Two-way mode

Two-way:

```text
CURRENT
OTHER
```

must be internally converted into:

```text
BASE = CURRENT
LEFT = CURRENT
RIGHT = OTHER
```

or equivalent explicit semantics.

The UI must clearly indicate that no historical base exists.

---

# 101. Merge strategy

```text
SEMANTIC_FIRST
AST_FIRST
TOKEN_FIRST
TEXT_FIRST
API_FIRST
DEPENDENCY_FIRST
```

Default:

```text
SEMANTIC_FIRST
```

Fallback:

```text
AST → TOKEN → TEXT
```

---

# 102. Formatting-only changes

Formatting differences should be classified separately:

```text
FORMAT_ONLY
SEMANTIC_CHANGE
```

If one side reformats and another changes semantics, semantic changes must survive formatting normalization.

---

# 103. Comment merge

Comments have source identity where available.

Independent comment additions merge.

Conflicting edits to the same comment may be represented as textual conflicts without contaminating semantic symbol identity.

---

# 104. Documentation comments

Documentation attached to a symbol belongs to that symbol.

Thus:

```text
SymbolId
   └── DocNode
```

Two independent documentation edits can merge separately from implementation changes.

---

# 105. Source ownership model

AXMERGE must not introduce ownership semantics into Axiom source.

It consumes the language's existing semantic model.

Memory/lifetime validation remains AXCOMPILER's responsibility.

---

# 106. Compiler integration

After merge:

```text
AXMERGE
   ↓
AXCOMPILER.parse
   ↓
AXCOMPILER.resolve
   ↓
AXCOMPILER.typecheck
   ↓
AXCOMPILER.lower
```

A semantic merge is not considered build-ready until the relevant compiler validation passes.

---

# 107. Error recovery

Malformed input:

```text
ERROR_INPUT_INVALID
```

must not be transformed into a merge conflict.

Distinguish:

```text
invalid input
```

from:

```text
valid but conflicting input
```

---

# 108. Version compatibility

If:

```text
BASE schema != LEFT schema
```

AXMERGE may normalize versions only when a declared migration exists.

Otherwise:

```text
SCHEMA_INCOMPATIBLE
```

---

# 109. Artifact identity

Each input receives:

```text
ArtifactId
ContentHash
SemanticHash
TargetIdentity
AbiIdentity
SchemaVersion
```

This prevents accidental merging of artifacts from incompatible targets.

---

# 110. Cross-target merge

Source can be merged across targets when target-independent.

Example:

```text
Windows PE64
Linux ELF64
```

may share source semantic state.

Target-specific sections must be represented separately:

```text
TARGET_CONDITIONAL
```

rather than accidentally merged.

---

# 111. Conditional compilation

Example:

```text
if target == windows {
    ...
}
```

and:

```text
if target == linux {
    ...
}
```

must be merged by conditional semantic identity.

AXMERGE must not treat mutually exclusive target branches as conflicts merely because they occupy similar source locations.

---

# 112. Build configuration merge

Structured merge:

```text
targets
sources
defines
features
dependencies
compiler_options
linker_options
resources
signing
packaging
```

Conflicting compiler/linker flags must be explicit.

---

# 113. Signing metadata

Signing credentials/secrets must never become merge content.

Only public metadata/policy may be represented.

Example:

```text
signing_required = true
certificate_identity = X
```

Secrets remain external.

---

# 114. Resource merge

Structured resources may support:

```text
ADD
REMOVE
MODIFY
REPLACE
```

Binary resource payloads should normally use:

```text
identity + replacement
```

not byte-level semantic synthesis.

---

# 115. Localization merge

String tables are keyed by stable identifiers:

```text
StringId
Locale
Variant
```

Two locales can merge independently.

Same locale/key with different values produces conflict.

---

# 116. AI metadata merge

Axiom AI metadata:

```text
semantic descriptions
symbol summaries
constraints
examples
provenance
```

must merge by `SymbolId`.

Generated AI descriptions are never allowed to overwrite human-authored normative metadata without policy authorization.

---

# 117. Trust levels

```text
NORMATIVE
COMPILER_DERIVED
TEST_VERIFIED
USER_AUTHORED
AI_PROPOSED
EXTERNAL
```

When evidence conflicts, provenance is preserved rather than silently choosing based on trust ranking.

---

# 118. Merge result trust

Result fields should expose:

```text
verified
unverified
conflicted
inferred
```

An inferred identity must never look like an exact identity to AXIDE or AI consumers.

---

# 119. Canonical semantic merge tree

```text
MergedProject
 ├ modules
 │   ├ declarations
 │   │   ├ functions
 │   │   ├ structs
 │   │   ├ enums
 │   │   ├ unions
 │   │   └ traits
 │   │
 │   └ imports
 │
 ├ dependencies
 ├ build
 ├ metadata
 └ provenance
```

---

# 120. Core invariants

### MERGE-INV-01
Three-way merge uses BASE/LEFT/RIGHT.

### MERGE-INV-02
Same semantic change on both sides is applied once.

### MERGE-INV-03
Independent semantic changes are preserved.

### MERGE-INV-04
Conflicting changes produce explicit conflicts.

### MERGE-INV-05
No unresolved conflict may be silently discarded.

### MERGE-INV-06
Exact SymbolId identity is preserved.

### MERGE-INV-07
Inferred identity carries provenance.

### MERGE-INV-08
Rename is represented as rename when identity evidence permits.

### MERGE-INV-09
Move is represented as move when identity evidence permits.

### MERGE-INV-10
Struct field conflicts are explicit.

### MERGE-INV-11
Enum discriminant conflicts are explicit.

### MERGE-INV-12
Trait implementation conflicts are explicit.

### MERGE-INV-13
Generic constraint conflicts are explicit.

### MERGE-INV-14
Effect conflicts are explicit.

### MERGE-INV-15
API changes are separately reported.

### MERGE-INV-16
ABI validation is delegated to AXABI.

### MERGE-INV-17
Unknown ABI compatibility is never assumed compatible.

### MERGE-INV-18
Dependency conflicts are structurally represented.

### MERGE-INV-19
Lockfile integrity conflicts are explicit.

### MERGE-INV-20
Generated artifacts follow explicit generation policy.

### MERGE-INV-21
Native binaries are normally rebuilt, not byte-merged.

### MERGE-INV-22
No arbitrary code executes during merge.

### MERGE-INV-23
AI proposals are not automatic resolutions.

### MERGE-INV-24
Every resolution has provenance.

### MERGE-INV-25
Conflict IDs are deterministic.

### MERGE-INV-26
Merge plans are deterministic.

### MERGE-INV-27
Serialized `.axmerge` artifacts are deterministic.

### MERGE-INV-28
Parallel execution cannot alter semantic result.

### MERGE-INV-29
Merge cache keys include policy/schema identity.

### MERGE-INV-30
Invalid input is distinct from semantic conflict.

### MERGE-INV-31
Partial merge is never implicitly build-ready.

### MERGE-INV-32
Formatting does not alter semantic identity.

### MERGE-INV-33
Comments cannot destroy declaration identity.

### MERGE-INV-34
Cross-target conditional branches remain target-aware.

### MERGE-INV-35
Build configuration conflicts are explicit.

### MERGE-INV-36
Signing secrets never enter merge artifacts.

### MERGE-INV-37
Provenance survives serialization.

### MERGE-INV-38
Merged source must be compiler-valid before build approval.

### MERGE-INV-39
Merge result must be reproducible from its canonical inputs.

### MERGE-INV-40
AXMERGE never silently invents semantic intent.

---

# 121. AXMERGE ↔ AXDIFF

Relationship:

```text
AXDIFF
   ↓
detect/describe differences
   ↓
AXMERGE
   ↓
combine differences
   ↓
AXDIFF
   ↓
verify resulting differences
```

AXDIFF answers:

> What changed?

AXMERGE answers:

> How can these changes be combined without losing semantic information?

---

# 122. AXMERGE ↔ AXABI

```text
AXMERGE
    ↓
merged API/type model
    ↓
AXABI
    ↓
ABI compatibility
```

AXMERGE does not duplicate ABI layout/calling-convention logic.

---

# 123. AXMERGE ↔ AXCOMPILER

AXCOMPILER owns:

```text
meaning
typing
symbol resolution
semantic IDs
IR
ABI lowering
```

AXMERGE consumes these representations.

This avoids implementing a second compiler inside the merge engine.

---

# 124. AXMERGE ↔ AXBUILD

AXBUILD must rebuild affected targets after successful merge.

Incremental build may reuse unaffected artifacts only when:

```text
semantic hash
ABI identity
compiler fingerprint
dependency fingerprint
```

remain compatible.

---

# 125. AXMERGE ↔ AXPACKAGE

Package graph merge:

```text
AXPACKAGE
   ↓
dependency semantic model
   ↓
AXMERGE
   ↓
merged dependency graph
   ↓
AXPACKAGE resolver
```

AXMERGE does not download packages or solve external registries.

---

# 126. AXMERGE ↔ AXTEST

Every successful merge should optionally generate:

```text
MergeValidationPlan
```

containing affected:

```text
unit tests
integration tests
API tests
ABI tests
target tests
```

---

# 127. Failure model

```text
INPUT_INVALID
SCHEMA_INCOMPATIBLE
TARGET_INCOMPATIBLE
IDENTITY_UNCERTAIN
SEMANTIC_CONFLICT
DEPENDENCY_CONFLICT
ABI_CONFLICT
POLICY_CONFLICT
VALIDATION_FAILED
RESOURCE_LIMIT
SERIALIZATION_ERROR
```

Failures must be machine-readable.

---

# 128. Performance targets

For ordinary source merge:

```text
memory ≈ O(changed semantic graph + shared snapshots)
time ≈ O(relevant graph)
```

Avoid loading unrelated project artifacts.

For very large repositories:

```text
lazy parsing
lazy semantic loading
incremental identity index
parallel independent modules
streamed serialization
```

are required.

---

# 129. Definition of Done

`AXMERGE 5.0` is complete only when:

- [x] Three-way merge model is normative.
- [x] Semantic merge is primary.
- [x] Symbol identity preservation is defined.
- [x] Rename/move detection is defined.
- [x] Source/token/AST/semantic merge is defined.
- [x] Struct/enum/union/trait/generic merge is defined.
- [x] API merge is defined.
- [x] ABI boundary is defined.
- [x] Dependency graph merge is defined.
- [x] Lockfile/build configuration merge is defined.
- [x] Generated artifact policy is defined.
- [x] Binary merge boundary is defined.
- [x] Conflict taxonomy is defined.
- [x] Deterministic conflict identity is defined.
- [x] Resolution model is defined.
- [x] Provenance/audit model is defined.
- [x] AI-assisted merge boundary is defined.
- [x] AXIDE/AXCODEEDITOR integration is defined.
- [x] AXCOMPILER/AXABI/AXBUILD/AXPACKAGE integration is defined.
- [x] AXTEST requirements are defined.
- [x] Incremental/parallel merge is defined.
- [x] Security/resource limits are defined.
- [x] Deterministic serialization is defined.
- [x] `AXMERGE_ABI_1` is defined.
- [x] 40 merge invariants are frozen.

**AXMERGE 5.0 is therefore FROZEN.**

---

# 130. Vị trí trong Axiom architecture

Sau AXDIFF + AXMERGE, nhóm development intelligence hiện có:

```text
                    Axiom Development System
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
     AXDEBUGGER           AXPROFILER             AXCRASH
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                           AXDIFF
                              │
                              ▼
                           AXMERGE
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
          AXCOMPILER       AXBUILD          AXPACKAGE
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                           AXTEST
```

AXDIFF cung cấp **difference truth**.

AXMERGE cung cấp **change composition truth**.

Hai subsystem này tạo thành nền tảng cho:

- branch integration;
- IDE merge;
- AI-assisted coding;
- safe refactoring integration;
- API evolution;
- ABI-aware integration;
- dependency-aware project integration.

---

## BOOTSTRAP-796 — AXPATCH

**Native Axiom Semantic Patch Engine, Symbol-Aware Patch Representation, AST/IR/API/ABI Patch Application, Patch Composition, Patch Inversion, Patch Validation, Patch Rebasing, Patch Transformation, Patch Provenance, Deterministic Patch Serialization & Patch ABI 5.0**

Nhiệm vụ tiếp theo sẽ xây `AXPATCH` thành lớp trung gian giữa **AXDIFF → AXMERGE → AXEDITOR/AXCOMPILER**, để thay đổi không còn được biểu diễn chủ yếu bằng line-diff mà bằng **semantic patch có thể áp dụng, đảo ngược, rebase, kiểm chứng và lưu trữ độc lập với vị trí dòng**.