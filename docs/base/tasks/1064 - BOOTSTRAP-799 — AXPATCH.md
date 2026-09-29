# BOOTSTRAP-799 — AXPATCH
## Native Axiom Semantic Patch Engine, Typed Patch IR, Symbol-Level Patch Application, Rename/Move/Extract/Inline/Split/Merge Operations, Patch Rebase & Relocation, Context Validation, Dependency-Aware Application, API/ABI Patch Validation, Three-Way Patch Adaptation, Patch Provenance, Deterministic Patch Serialization & Patch ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXPATCH`  
**ABI:** `AXPATCH_ABI_1`  
**Schema:** `AXPATCH_SCHEMA_1`  
**Artifact:** `.axpatch`

**Dependencies:**

```text
AXCOMPILER
AXDIFF
AXHISTORY
AXABI
AXOBJECT
AXTEST
AXDOC
```

---

# 1. Mục tiêu

`AXPATCH` là **semantic mutation layer** của Axiom.

Nó nhận một thay đổi được mô tả ở mức:

```text
source
token
AST
symbol
type
trait
generic
API
ABI
dependency
module
```

và biến nó thành một phép biến đổi có thể:

```text
validate
apply
reverse
relocate
rebase
compose
split
serialize
verify
audit
```

Kiến trúc:

```text
                         AXDIFF
                           │
                           ▼
                     Patch Generation
                           │
                           ▼
                        AXPATCH
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     Validate            Apply              Rebase
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                    Semantic Snapshot
                           │
                           ▼
                       AXHISTORY
```

---

# 2. Boundary

AXPATCH **owns**:

```text
Patch IR
Patch operation semantics
Patch validation
Patch application
Patch inversion
Patch relocation
Patch composition
Patch conflict detection
Patch provenance
Patch serialization
```

AXPATCH **does not own**:

```text
semantic analysis
type system
symbol identity authority
history DAG
repository storage
source diff algorithm
final binary linking
compiler code generation
```

Authority:

```text
AXCOMPILER → semantic truth
AXDIFF     → difference discovery
AXPATCH    → change application
AXMERGE    → multi-way composition
AXHISTORY  → lineage
AXVCS      → persistence/transport
```

---

# 3. Core principle

Patch không được định nghĩa đơn thuần là:

```text
line 100:
- old text
+ new text
```

Mà ưu tiên:

```text
SymbolId
SemanticPath
Operation
Precondition
Transformation
Postcondition
```

Ví dụ:

```text
RenameSymbol {
    symbol = SymbolId(...)
    new_name = "compute"
}
```

thay vì:

```text
replace "calc" with "compute"
```

---

# 4. Patch lifecycle

```text
AXDIFF
  │
  ▼
Patch IR
  │
  ├── validate
  ├── normalize
  ├── serialize
  │
  ▼
AXPATCH
  │
  ├── locate
  ├── check preconditions
  ├── transform
  ├── validate postconditions
  │
  ▼
New Semantic Snapshot
```

---

# 5. Patch identity

Mỗi patch có:

```text
PatchId
```

Canonical:

```text
PatchId =
HASH(
    PATCH_DOMAIN,
    AXPATCH_SCHEMA_1,
    canonical_patch
)
```

Patch identity không phụ thuộc:

```text
filename
filesystem path
repository
transport
timestamp
```

trừ khi metadata đó được explicitly declared semantic.

---

# 6. Patch model

```text
Patch {
    id
    schema
    base
    operations[]
    preconditions[]
    postconditions[]
    dependencies[]
    provenance
    metadata
}
```

---

# 7. Patch base

Patch có thể được tạo trên:

```text
RevisionId
SemanticSnapshotId
TreeId
```

Ví dụ:

```text
base_revision = R100
```

---

# 8. Base requirement

Patch phải khai báo mức phụ thuộc:

```text
EXACT_BASE
SEMANTIC_BASE
STRUCTURAL_BASE
CONTEXT_BASE
NONE
```

---

# 9. EXACT_BASE

Chỉ áp dụng được khi:

```text
current_revision == base_revision
```

Phù hợp với những thay đổi không thể safely relocate.

---

# 10. SEMANTIC_BASE

Cho phép áp dụng trên revision khác nếu:

```text
required SymbolIds
types
traits
dependencies
```

vẫn tồn tại tương thích.

---

# 11. STRUCTURAL_BASE

Patch dựa trên AST/structural context.

Có thể relocate nếu cấu trúc tương ứng được tìm thấy.

---

# 12. CONTEXT_BASE

Patch dựa trên source context nhưng có semantic anchors.

Đây là fallback thấp hơn semantic patch.

---

# 13. Patch operation

```text
PatchOperation {
    opcode
    target
    payload
    preconditions
    postconditions
    provenance
}
```

---

# 14. Core operation classes

```text
ADD
REMOVE
REPLACE
RENAME
MOVE
COPY
WRAP
UNWRAP
SPLIT
JOIN
REORDER
MODIFY
```

---

# 15. Semantic operation classes

```text
ADD_SYMBOL
REMOVE_SYMBOL
RENAME_SYMBOL
MOVE_SYMBOL
MODIFY_SIGNATURE
MODIFY_TYPE
MODIFY_BODY
MODIFY_ATTRIBUTE
MODIFY_VISIBILITY
MODIFY_TRAIT_IMPL
MODIFY_GENERIC
MODIFY_DEPENDENCY
```

---

# 16. Module operations

```text
CREATE_MODULE
DELETE_MODULE
RENAME_MODULE
MOVE_MODULE
SPLIT_MODULE
MERGE_MODULE
MODIFY_IMPORT
MODIFY_EXPORT
```

---

# 17. Struct operations

```text
ADD_FIELD
REMOVE_FIELD
RENAME_FIELD
MOVE_FIELD
CHANGE_FIELD_TYPE
CHANGE_FIELD_VISIBILITY
REORDER_FIELD
```

---

# 18. Enum operations

```text
ADD_VARIANT
REMOVE_VARIANT
RENAME_VARIANT
MODIFY_VARIANT_PAYLOAD
REORDER_VARIANT
```

---

# 19. Trait operations

```text
ADD_TRAIT_MEMBER
REMOVE_TRAIT_MEMBER
MODIFY_TRAIT_MEMBER
ADD_IMPL
REMOVE_IMPL
MODIFY_IMPL
```

---

# 20. Generic operations

```text
ADD_TYPE_PARAMETER
REMOVE_TYPE_PARAMETER
RENAME_TYPE_PARAMETER
MODIFY_CONSTRAINT
MODIFY_DEFAULT
```

---

# 21. Function operations

```text
ADD_PARAMETER
REMOVE_PARAMETER
RENAME_PARAMETER
CHANGE_PARAMETER_TYPE
CHANGE_RETURN_TYPE
MODIFY_EFFECT
MODIFY_BODY
```

---

# 22. Expression operations

Patch engine may operate structurally:

```text
REPLACE_EXPRESSION
INSERT_EXPRESSION
REMOVE_EXPRESSION
WRAP_EXPRESSION
REORDER_ARGUMENT
```

---

# 23. Statement operations

```text
INSERT_STATEMENT
REMOVE_STATEMENT
REPLACE_STATEMENT
MOVE_STATEMENT
```

---

# 24. Symbol target

Canonical target:

```text
SymbolTarget {
    symbol_id
}
```

If SymbolId unavailable:

```text
StructuralTarget
```

must contain explicit confidence/provenance.

---

# 25. Semantic path

```text
SemanticPath {
    module
    symbol
    nested_symbols[]
    property
}
```

Example:

```text
module Foo
 └── struct Bar
      └── method calculate
           └── body
```

---

# 26. Symbol identity preservation

Nếu SymbolId remains unchanged:

```text
before SymbolId == after SymbolId
```

unless operation explicitly creates a new identity.

Rename không được tạo symbol mới.

---

# 27. Rename

```text
RenameSymbol {
    target
    old_name
    new_name
}
```

Precondition:

```text
target.name == old_name
```

Postcondition:

```text
target.name == new_name
```

---

# 28. Rename references

Rename semantic symbol phải cập nhật các reference được compiler xác định là reference tới symbol đó.

Không được thực hiện global text replacement.

---

# 29. Move

```text
MoveSymbol {
    symbol
    source_parent
    destination_parent
}
```

Move giữ SymbolId.

---

# 30. Move dependency update

Nếu module ownership thay đổi:

```text
imports
exports
visibility
qualified paths
```

phải được cập nhật nếu semantic analysis xác định chúng bị ảnh hưởng.

---

# 31. Extract

`Extract` là composite patch:

```text
ExtractFunction {
    source_symbol
    region
    new_symbol
    parameters
    return_value
}
```

Không được coi là một text substitution đơn giản.

---

# 32. Inline

```text
InlineFunction {
    call_site
    function
}
```

AXPATCH phải kiểm tra:

```text
generic substitution
effects
evaluation order
captures
control flow
```

---

# 33. Split symbol

Ví dụ:

```text
large_function
    ↓
function_a
function_b
```

Patch phải chứa mapping:

```text
old symbol
 → new symbols[]
```

---

# 34. Merge symbols

Hai symbols có thể được hợp nhất.

```text
MergeSymbols {
    sources[]
    destination
}
```

Phải có explicit identity policy.

Không tự chọn canonical identity khi evidence không đủ.

---

# 35. Replace body

```text
ReplaceBody {
    symbol
    old_body_hash
    new_body
}
```

`old_body_hash` bảo vệ chống stale patch.

---

# 36. Patch precondition

```text
Precondition {
    kind
    target
    expected
}
```

Examples:

```text
SYMBOL_EXISTS
SYMBOL_TYPE_IS
FIELD_EXISTS
BODY_HASH_IS
REVISION_IS
DEPENDENCY_EXISTS
```

---

# 37. Patch postcondition

```text
Postcondition {
    kind
    expected
}
```

Ví dụ:

```text
SYMBOL_EXISTS
SYMBOL_NAME_IS
TYPE_IS
REFERENCE_COUNT_VALID
```

---

# 38. Preconditions are mandatory

Mọi mutation operation phải có đủ precondition để phát hiện stale state.

Không được:

```text
best effort mutation
```

trong core mode.

---

# 39. Strict mode

Default:

```text
PATCH_STRICT
```

Nếu precondition fail:

```text
PATCH_PRECONDITION_FAILED
```

Không tiếp tục âm thầm.

---

# 40. Adaptive mode

Có thể:

```text
PATCH_ADAPTIVE
```

cho phép relocation.

Nhưng mọi adaptation phải được ghi:

```text
AdaptationRecord
```

---

# 41. Relocation

Patch có thể được relocate:

```text
original target
      ↓
target changed location
      ↓
semantic matcher
      ↓
new target
```

---

# 42. Relocation confidence

```text
EXACT
HIGH
MEDIUM
LOW
UNKNOWN
```

`UNKNOWN` không được tự apply.

---

# 43. SymbolId-first relocation

Thứ tự:

```text
1. SymbolId
2. stable semantic identity
3. exact structural fingerprint
4. qualified semantic path
5. source context
6. textual fallback
```

---

# 44. Textual fallback

Textual patch chỉ được dùng khi semantic matching thất bại.

Kết quả phải ghi:

```text
fallback = TEXT
```

để AXHISTORY/AI biết độ tin cậy thấp hơn.

---

# 45. Patch context

Patch có thể chứa context:

```text
ContextAnchor {
    before
    target
    after
}
```

Nhưng context không thay thế semantic identity khi semantic identity tồn tại.

---

# 46. Patch application

Pipeline:

```text
load
 ↓
decode
 ↓
verify patch hash
 ↓
verify schema
 ↓
resolve base
 ↓
resolve targets
 ↓
check preconditions
 ↓
apply operations
 ↓
validate semantic snapshot
 ↓
validate postconditions
 ↓
emit result
```

---

# 47. Transactional application

Patch application phải atomic ở semantic snapshot level.

Nếu operation 17/20 fail:

```text
result = failure
```

không để snapshot half-mutated làm canonical result.

---

# 48. Copy-on-write implementation

Implementation được khuyến nghị:

```text
immutable snapshot
       ↓
persistent structures
       ↓
copy-on-write changed nodes
```

để patch thất bại không làm hỏng base.

---

# 49. No mandatory GC

AXPATCH không yêu cầu garbage collector.

Temporary patch state có thể sử dụng:

```text
arena
region
explicit lifetime
```

phù hợp memory model Axiom.

---

# 50. Patch transaction

```text
PatchTransaction {
    base_snapshot
    working_snapshot
    operations
    diagnostics
    commit()
    abort()
}
```

---

# 51. Operation ordering

Operations có dependency graph.

Ví dụ:

```text
ADD_SYMBOL
    ↓
ADD_REFERENCE
```

không được apply ngược.

---

# 52. Dependency graph

```text
PatchDependencyGraph {
    nodes
    edges
}
```

Engine topologically sorts operations.

Nếu cycle:

```text
PATCH_DEPENDENCY_CYCLE
```

trừ khi operation group explicitly supports transactional cycle resolution.

---

# 53. Operation groups

```text
PatchGroup {
    operations[]
    atomic
}
```

Một semantic transformation phức tạp có thể gồm nhiều primitive operations.

---

# 54. Composite patch

Ví dụ rename:

```text
RenameSymbol
 ├── rename declaration
 ├── update references
 ├── update docs references
 └── update metadata
```

Các bước thuộc cùng transaction.

---

# 55. Dependency-aware patch

Nếu sửa public API:

```text
function foo(i32) → foo(i64)
```

patch engine phải identify affected references.

AXCOMPILER cung cấp semantic dependency graph.

---

# 56. API compatibility

Patch có thể yêu cầu:

```text
API_CHECK
```

Nếu public API bị phá vỡ:

```text
API_BREAK
```

được ghi nhận.

---

# 57. ABI compatibility

Nếu patch thay đổi:

```text
struct layout
calling convention
extern signature
alignment
representation
```

AXPATCH gọi AXABI compatibility analysis.

---

# 58. ABI result

```text
ABIImpact {
    NONE
    COMPATIBLE
    CONDITIONAL
    BREAKING
    UNKNOWN
}
```

Patch engine không tự quyết định policy release.

---

# 59. Binary impact

Patch có thể đánh dấu:

```text
BinaryImpact {
    CODE
    DATA
    ABI
    DEBUG
    LINK
    UNKNOWN
}
```

AXBINARY/AXLINKER xử lý artifact consequences.

---

# 60. Dependency impact

```text
DependencyImpact {
    added[]
    removed[]
    changed[]
}
```

Package resolution thuộc AXPACKAGE.

---

# 61. Patch inversion

Patch phải có thể invert khi operation reversible.

```text
inverse(apply(P, S)) == S
```

với những patch không chứa irreversible operation.

---

# 62. Non-reversible operations

Ví dụ:

```text
delete information
external side effect
```

phải khai báo:

```text
reversible = false
```

---

# 63. Delete operation

Delete phải preserve enough metadata để tạo inverse nếu requested:

```text
deleted_symbol_snapshot
```

---

# 64. Patch composition

Hai patch:

```text
P1
P2
```

có thể compose:

```text
P1 ∘ P2
```

nếu P2 base-compatible với result của P1.

---

# 65. Composition result

```text
compose(P1, P2) → P12
```

Phải bảo toàn:

```text
semantic result
provenance
dependencies
```

---

# 66. Composition conflict

Nếu:

```text
P1: rename A → B
P2: remove A
```

thì composition phải trả conflict hoặc explicit policy result.

Không tự chọn.

---

# 67. Patch split

Composite patch có thể split:

```text
P
 ↓
P1
P2
P3
```

theo:

```text
symbol
module
operation group
semantic dependency
```

---

# 68. Patch normalization

Equivalent patches nên được canonicalize.

Ví dụ:

```text
rename A→B
rename B→C
```

có thể normalize thành:

```text
rename A→C
```

nếu không có observable intermediate semantics.

---

# 69. Do not over-normalize

Không được normalize nếu:

```text
intermediate state
provenance
identity
effects
```

có ý nghĩa observable.

---

# 70. Three-way patch adaptation

Input:

```text
BASE
PATCH
CURRENT
```

Pipeline:

```text
BASE
 │
 ├── PATCH
 │
 ▼
EXPECTED
 │
CURRENT
 │
 ▼
AXDIFF/AXMERGE
 │
 ▼
ADAPTED PATCH
```

---

# 71. Rebase patch

```text
rebase_patch(
    patch,
    old_base,
    new_base
)
```

trả:

```text
RebasedPatch
```

hoặc:

```text
PatchConflict[]
```

---

# 72. Patch conflict

```text
PatchConflict {
    operation
    target
    base_state
    current_state
    expected_state
    reason
}
```

---

# 73. Conflict categories

```text
TARGET_MISSING
TARGET_CHANGED
IDENTITY_AMBIGUOUS
TYPE_CHANGED
DEPENDENCY_CHANGED
API_CHANGED
ABI_CHANGED
STRUCTURE_CHANGED
CONTEXT_CHANGED
ORDERING_CONFLICT
```

---

# 74. Conflict resolution

AXPATCH may accept explicit resolution:

```text
PatchResolution {
    conflict_id
    action
}
```

Actions:

```text
ACCEPT_PATCH
ACCEPT_CURRENT
CUSTOM_TRANSFORM
SKIP
ABORT
```

---

# 75. No silent resolution

AI hoặc heuristic không được silently choose resolution in strict mode.

---

# 76. AI patch proposal

AI may create:

```text
PatchProposal
```

rather than directly mutating source.

```text
AI
 ↓
proposal
 ↓
AXDIFF
 ↓
AXPATCH validation
 ↓
user/system policy
 ↓
apply
```

---

# 77. AI provenance

```text
PatchProvenance {
    source
    agent_id
    model_id
    prompt_hash
    generated_at
}
```

Sensitive prompt contents need not be embedded.

---

# 78. Human-authored patch

```text
source = HUMAN
```

AI-assisted:

```text
source = AI_ASSISTED
```

Machine-generated refactoring:

```text
source = TOOL
```

---

# 79. Patch provenance chain

Patch can reference:

```text
derived_from_diff
derived_from_patch
derived_from_revision
derived_from_ai_proposal
```

---

# 80. Source patch representation

For interoperability:

```text
SourcePatch {
    file
    ranges
    context
    replacement
}
```

exists as a compatibility format.

Semantic patch remains canonical when possible.

---

# 81. AST patch

```text
AstPatch {
    node_identity
    operation
    payload
}
```

Compiler supplies AST identity mapping.

---

# 82. Semantic patch

Canonical:

```text
SemanticPatch {
    symbols
    operations
    dependencies
    constraints
}
```

---

# 83. Patch IR

Internal normalized representation:

```text
PatchIR {
    symbols
    nodes
    operations
    dependency_graph
    preconditions
    postconditions
}
```

---

# 84. Patch compiler

Pipeline:

```text
SourcePatch
ASTPatch
SemanticPatch
     ↓
PatchNormalizer
     ↓
PatchIR
```

---

# 85. Patch interpreter

```text
PatchIR
  ↓
TargetResolver
  ↓
PreconditionChecker
  ↓
MutationEngine
  ↓
Validator
```

---

# 86. Patch execution is not program execution

Applying a patch must not execute target application code.

It may invoke compiler semantic services.

---

# 87. Compiler validation

AXCOMPILER may perform:

```text
parse
resolve
typecheck
effect-check
symbol-check
```

but not execute application code.

---

# 88. Patch semantic validation

After mutation:

```text
new snapshot
```

must pass configured compiler validation.

---

# 89. Incremental validation

Only affected semantic regions should be recomputed when safe.

Global validation remains available.

---

# 90. Patch cache

Cache key:

```text
PatchApplicationCacheKey =
HASH(
    patch_id,
    base_snapshot_id,
    compiler_schema,
    policy
)
```

---

# 91. Deterministic application

Same:

```text
patch
base snapshot
compiler schema
policy
```

must yield the same semantic result.

---

# 92. Parallel application

Independent operations can be processed in parallel.

Conflicting writes must be detected before commit.

---

# 93. Conflict detection graph

```text
Operation A ──writes──> X
Operation B ──writes──> X
```

→ conflict unless operations commute.

---

# 94. Commutativity

Operations can declare:

```text
commutative = true
```

only when formally validated.

---

# 95. Patch ordering

If two operations commute, canonical order may be:

```text
target SymbolId
opcode
canonical payload
```

to ensure deterministic serialization.

---

# 96. Patch serialization

Canonical binary format:

```text
AXPATCH_SCHEMA_1
header
metadata
base
operations
dependencies
preconditions
postconditions
provenance
checksum
```

---

# 97. Text representation

Optional `.axpatch.txt` is human-readable.

It is not authoritative if binary canonical form differs.

---

# 98. Patch checksum

Serialized patch contains checksum.

The checksum verifies transport/storage integrity.

PatchId verifies canonical semantic identity.

---

# 99. Patch signing

Signing belongs to:

```text
AXCRYPTO
AXTRUST
```

AXPATCH stores/verifies signatures.

---

# 100. Patch trust

Possible:

```text
UNSIGNED
SIGNED_VALID
SIGNED_INVALID
UNKNOWN_SIGNER
```

---

# 101. Patch security

Patch parser must reject:

```text
malformed operation
invalid SymbolId
oversized payload
cyclic dependencies
invalid offsets
invalid nesting
resource bombs
```

---

# 102. Resource limits

```text
max_operations
max_payload
max_dependency_edges
max_recursion
max_symbols
max_memory
```

---

# 103. Path security

Source patch paths must be normalized and sandboxed.

Reject:

```text
../
absolute paths
device paths
```

outside repository scope.

---

# 104. Patch storage

AXVCS stores `.axpatch` objects as immutable blobs/semantic objects.

AXPATCH itself does not own repository storage.

---

# 105. History integration

After successful application:

```text
PatchId
    ↓
AXHISTORY
    ↓
ChangeLineage
```

---

# 106. Patch lineage

History records:

```text
applied_patch
source_revision
result_revision
adaptation
conflicts
resolution
```

---

# 107. Revert

Revert is:

```text
inverse(Patch)
```

when possible.

Otherwise AXDIFF generates a compensating patch.

---

# 108. Revert safety

Revert must apply against current state using normal preconditions.

Không giả định source vẫn ở trạng thái cũ.

---

# 109. Cherry-pick

Cherry-pick:

```text
Revision R
 ↓
associated patch
 ↓
rebase/adapt
 ↓
apply
```

---

# 110. Merge integration

AXMERGE may emit:

```text
MergedPatch
```

AXPATCH applies the resolved patch transactionally.

---

# 111. Merge does not bypass patch validation

Even AXMERGE output phải đi qua:

```text
AXPATCH validate/apply
```

before canonical snapshot publication.

---

# 112. IDE integration

AXIDE uses AXPATCH for:

```text
rename
extract
inline
organize imports
generate implementation
apply AI changes
refactor
```

---

# 113. Refactoring API

```text
RefactorRequest {
    kind
    target
    parameters
}
```

returns:

```text
Patch
```

rather than directly modifying editor state.

---

# 114. Editor integration

```text
AXCODEEDITOR
     ↓
AXEDITOR transaction
     ↓
AXPATCH
     ↓
compiler validation
```

Editor remains presentation/editing authority.

---

# 115. Undo model

AXEDITOR may maintain local text undo.

AXPATCH inverse handles semantic undo/revert.

These are distinct concepts.

---

# 116. Patch diagnostics

```text
PatchDiagnostic {
    severity
    code
    target
    location
    message
}
```

---

# 117. Diagnostic categories

```text
PATCH_PARSE_ERROR
PATCH_SCHEMA_ERROR
PATCH_BASE_MISMATCH
PATCH_TARGET_MISSING
PATCH_PRECONDITION_FAILED
PATCH_CONFLICT
PATCH_VALIDATION_FAILED
PATCH_API_BREAK
PATCH_ABI_BREAK
PATCH_RESOURCE_LIMIT
```

---

# 118. Source mapping

Each operation should retain:

```text
source_location
```

when originating from source/IDE/AI.

---

# 119. Semantic mapping

Preferred:

```text
SymbolId
NodeId
PropertyId
```

over line numbers.

---

# 120. Patch and documentation

If public symbol renamed:

```text
documentation references
examples
cross-links
```

may be included as dependent operations.

AXDOC validates documentation semantics.

---

# 121. Patch and tests

Patch can declare affected tests:

```text
AffectedTestSet
```

AXTEST decides whether to execute them.

---

# 122. Patch and build

Patch can declare:

```text
BuildImpact
```

AXBUILD determines incremental rebuild scope.

---

# 123. Patch and ABI

A patch changing a public struct:

```text
struct S {
    a: i32
}
```

to:

```text
struct S {
    a: i32
    b: i64
}
```

must expose potential layout/ABI impact through AXABI.

AXPATCH does not itself label the release as compatible/incompatible without AXABI evidence.

---

# 124. Patch and generated code

Generated files should normally be represented by source-level transformations.

If generated output is tracked, patch metadata identifies:

```text
generated = true
generator_identity
```

---

# 125. External files

Patch may reference external files only through explicit object/reference mechanisms.

No implicit filesystem dependency.

---

# 126. Patch portability

A semantic patch should be portable across repositories if required symbols and schema exist.

Repository identity is not intrinsic to PatchId.

---

# 127. Patch application across platforms

Semantic patch should remain platform-neutral.

Platform-specific source changes may include explicit:

```text
target_constraints
```

---

# 128. Conditional patch

```text
ConditionalOperation {
    condition
    then
    else
}
```

Condition evaluation must use static semantic metadata, not arbitrary code execution.

---

# 129. Macro-generated code

Patch should normally target macro source, not expanded output.

If expanded output is patched:

```text
generated_target = true
```

and regeneration policy must be explicit.

---

# 130. Unsafe code

AXPATCH can modify unsafe code but does not downgrade safety checks.

Compiler remains authority for unsafe boundaries.

---

# 131. Concurrency semantics

Patch application is isolated from running application state.

No live process mutation.

---

# 132. Runtime patching

Hot reload is not AXPATCH core.

If later introduced:

```text
AXHOTRELOAD
```

must consume validated patch artifacts through a separate ABI.

---

# 133. Patch serialization compatibility

Readers must reject unknown mandatory operations.

Optional operations may be skipped only if semantics remain explicitly representable.

---

# 134. Forward compatibility

Unknown fields may be preserved as opaque metadata where safe.

Unknown semantic operations must not be ignored.

---

# 135. Backward compatibility

`AXPATCH_SCHEMA_1` reader must accept all canonical v1 operations.

---

# 136. Patch migration

```text
AXPATCH v1
    ↓
migration adapter
    ↓
AXPATCH v2
```

must preserve semantic intent or report loss.

---

# 137. Patch equivalence

Two patches may produce the same result on a particular base while being structurally different.

Therefore:

```text
PatchId != behavioral equivalence
```

in general.

---

# 138. Behavioral equivalence

Optional compiler-assisted validation can establish:

```text
same semantic result
```

but must not be confused with formal program equivalence.

---

# 139. Patch minimization

AXPATCH may minimize redundant operations.

Example:

```text
rename A→B
rename B→C
```

→

```text
rename A→C
```

when safe.

---

# 140. Patch canonicalization

Canonical order:

```text
module
symbol
property
opcode
payload
```

ensures deterministic PatchId.

---

# 141. Large patch streaming

Patch files must support streaming decoding.

Do not require full patch in RAM.

---

# 142. Large source transformation

For huge repositories:

```text
module-level
symbol-level
chunk-level
```

processing should avoid cloning unchanged trees.

---

# 143. Persistent semantic trees

Recommended:

```text
SemanticTree
 ├── immutable unchanged nodes
 └── copied changed nodes
```

This provides efficient patch application without GC.

---

# 144. Memory target

Typical small patch application should allocate only:

```text
patch state
changed semantic nodes
temporary indexes
diagnostics
```

not duplicate the entire repository.

---

# 145. Failure atomicity

If validation fails:

```text
base snapshot remains untouched
```

---

# 146. Patch transaction commit

Only after:

```text
all preconditions
all transformations
all semantic checks
all postconditions
```

succeed.

---

# 147. Patch result

```text
PatchResult {
    status
    new_snapshot
    applied_operations
    skipped_operations
    adaptations
    conflicts
    diagnostics
    impact
}
```

---

# 148. Status values

```text
APPLIED
ADAPTED
PARTIAL
CONFLICT
REJECTED
INVALID
```

`PARTIAL` is allowed only in explicitly non-strict mode.

---

# 149. Strict default

Default:

```text
mode = STRICT
```

Thus normal Axiom refactoring cannot accidentally produce partial changes.

---

# 150. Patch API

Core:

```text
parse_patch()
validate_patch()
normalize_patch()

apply_patch()
reverse_patch()
compose_patch()
split_patch()

relocate_patch()
rebase_patch()

serialize_patch()
deserialize_patch()

inspect_patch()
compute_patch_id()
verify_patch()
```

---

# 151. Target resolver API

```text
resolve_symbol()
resolve_structural_target()
resolve_semantic_path()
resolve_context_anchor()
```

---

# 152. Mutation API

```text
begin_transaction()
apply_operation()
validate_transaction()
commit_transaction()
abort_transaction()
```

---

# 153. Conflict API

```text
detect_conflicts()
list_conflicts()
resolve_conflict()
resume_patch()
abort_patch()
```

---

# 154. Impact API

```text
analyze_api_impact()
analyze_abi_impact()
analyze_dependency_impact()
analyze_build_impact()
analyze_test_impact()
```

---

# 155. AXPATCH ABI

`AXPATCH_ABI_1` must expose stable opaque interfaces:

```text
PatchHandle
PatchOperationHandle
PatchTransactionHandle
PatchConflictHandle
PatchResultHandle
```

Internal IR layout is not ABI.

---

# 156. ABI ownership

Compiler-owned semantic structures must not become accidentally frozen by AXPATCH ABI.

AXPATCH references stable semantic IDs/interfaces.

---

# 157. Patch ABI and compiler versions

Patch must record:

```text
compiler_schema
semantic_schema
```

when semantics depend on compiler representation.

---

# 158. Patch ABI and AXHISTORY

AXHISTORY stores PatchId and provenance.

It does not depend on internal PatchIR layout.

---

# 159. Patch ABI and AXVCS

AXVCS stores:

```text
AXPATCH object
```

without interpreting its semantic operations.

---

# 160. Patch ABI and AXDIFF

AXDIFF may generate AXPATCH.

AXPATCH may consume only validated PatchIR.

---

# 161. Patch ABI and AXMERGE

AXMERGE may compose multiple patches.

AXPATCH performs final application.

---

# 162. Patch ABI and AXIDE

IDE refactoring commands return patch artifacts.

This allows:

```text
preview
diff
undo
audit
apply
```

before source mutation.

---

# 163. Preview mode

```text
preview_patch()
```

must produce:

```text
semantic diff
source diff
API impact
ABI impact
conflicts
```

without modifying canonical state.

---

# 164. Dry run

```text
apply_patch(dry_run=true)
```

performs all checks but commits no mutation.

---

# 165. Explainability

Each operation should expose:

```text
why_target_matched
why_precondition_passed
why_transformation_applied
```

especially for relocated/AI-generated patches.

---

# 166. AI-readable patch

Canonical metadata:

```text
PatchExplanation {
    summary
    affected_symbols
    dependencies
    risks
    confidence
}
```

This is metadata, not semantic authority.

---

# 167. No confidence masquerading as truth

A confidence value must never replace:

```text
precondition
semantic validation
ABI validation
```

---

# 168. Patch audit

```text
PatchAudit {
    operation_id
    before_hash
    after_hash
    target
    resolver
    adaptation
}
```

---

# 169. Reproducibility

Given:

```text
same base
same patch
same compiler semantic schema
same policy
```

the result must be deterministic.

---

# 170. Nondeterministic compiler services

If a compiler service returns nondeterministic matching:

```text
PatchResult
```

must record that condition and deterministic mode must reject or canonicalize it.

---

# 171. Test strategy

AXTEST must cover:

```text
unit
integration
property
fuzz
differential
golden
round-trip
rebase
merge
rollback
performance
security
```

---

# 172. Property tests

Important properties:

```text
apply(inverse(P), apply(P,S)) == S
```

for reversible patches.

Also:

```text
serialize(deserialize(P)) == canonical(P)
```

---

# 173. Composition property

For compatible P1/P2:

```text
apply(compose(P1,P2), S)
==
apply(P2, apply(P1,S))
```

---

# 174. Idempotence

Applying an already-applied patch in strict mode should normally fail its preconditions rather than silently apply twice.

---

# 175. Rename property

Rename:

```text
A → B
```

must preserve SymbolId unless explicitly configured otherwise.

---

# 176. Move property

Move must preserve symbol identity.

---

# 177. Delete/restore property

For reversible delete:

```text
restore(delete(S)) == S
```

modulo canonical formatting.

---

# 178. Rebase property

If no conflicting changes exist:

```text
apply(rebase(P, B1, B2), B2)
```

must produce semantic equivalent of applying P to B1 then transporting result to B2.

---

# 179. Conflict property

Ambiguous target resolution must produce:

```text
CONFLICT
```

rather than arbitrary mutation.

---

# 180. Fuzzing

Fuzz:

```text
patch parser
binary decoder
operation graph
target resolver
serialization
rebase
composition
```

---

# 181. Malformed patch testing

Must reject:

```text
truncated patch
invalid enum
invalid object ID
cyclic graph
overflow
invalid UTF-8 where prohibited
duplicate operation IDs
```

---

# 182. Differential testing

Compare:

```text
semantic patch
```

against:

```text
equivalent source transformation
```

through AXCOMPILER.

---

# 183. Compiler bootstrap testing

AXPATCH must operate on Axiom compiler source itself.

Required scenarios:

```text
rename
move
API change
struct evolution
trait evolution
generic evolution
module split
```

---

# 184. Performance testing

Measure:

```text
patch decode time
target resolution
precondition validation
mutation
semantic validation
serialization
memory allocation
```

separately.

---

# 185. Performance target

For a patch touching `N` semantic nodes in a repository of `M` nodes:

Preferred complexity:

```text
O(N log M)
```

or better with indexes.

Full repository traversal should not be mandatory.

---

# 186. Incremental target resolution

Maintain:

```text
SymbolId index
qualified-name index
semantic fingerprint index
dependency index
```

as derived compiler data.

---

# 187. Index invalidation

After patch:

```text
only affected index entries
```

should be updated when safe.

---

# 188. Cache correctness

Cache hit is valid only when:

```text
base snapshot
patch ID
schema
policy
compiler semantic version
```

match.

---

# 189. No stale cache mutation

A stale cached target must never be accepted as current semantic truth.

---

# 190. Repository integration

A patch can be:

```text
stored in AXVCS
referenced by AXHISTORY
generated by AXDIFF
applied by AXPATCH
combined by AXMERGE
```

---

# 191. Commit integration

Canonical commit flow:

```text
AXVCS base revision
        ↓
working changes
        ↓
AXDIFF
        ↓
AXPATCH
        ↓
validated snapshot
        ↓
AXHISTORY revision
        ↓
AXVCS commit
```

---

# 192. Branch integration

Branches remain AXVCS refs.

AXPATCH never owns branches.

---

# 193. Remote patch transport

A patch can be transferred independently of repository source if all referenced semantic objects are available.

---

# 194. Patch bundle

Optional:

```text
PatchBundle {
    patch
    required_objects[]
    signatures[]
}
```

Useful for:

```text
code review
offline transfer
AI-generated change delivery
```

---

# 195. Patch bundle security

Required objects must be individually hash-verified.

Bundle container integrity does not replace object integrity.

---

# 196. Code review integration

Review system can display:

```text
Patch
 ↓
AXDIFF
 ↓
source diff
semantic diff
API diff
ABI diff
```

This is substantially richer than line-only review.

---

# 197. Review approval

Approval belongs to higher-level policy.

AXPATCH only applies an approved patch.

---

# 198. Release integration

Release tooling can query:

```text
PatchImpact
```

to determine:

```text
source change
API change
ABI change
dependency change
```

AXPATCH does not decide release versioning policy.

---

# 199. 40 invariants

### PATCH-INV-01
Patch identity is deterministic.

### PATCH-INV-02
Patch serialization is canonical.

### PATCH-INV-03
Patch base requirements are explicit.

### PATCH-INV-04
Patch operations have explicit preconditions.

### PATCH-INV-05
Failed preconditions do not silently mutate state.

### PATCH-INV-06
Patch application is transactional.

### PATCH-INV-07
Base snapshots remain immutable.

### PATCH-INV-08
Semantic SymbolId is preferred over textual matching.

### PATCH-INV-09
Rename preserves SymbolId by default.

### PATCH-INV-10
Move preserves SymbolId by default.

### PATCH-INV-11
Ambiguous target resolution produces conflict.

### PATCH-INV-12
Textual fallback is explicitly marked.

### PATCH-INV-13
Operation dependencies are explicit.

### PATCH-INV-14
Dependency cycles are rejected unless explicitly supported.

### PATCH-INV-15
Equivalent independent operations may execute in parallel.

### PATCH-INV-16
Concurrent conflicting writes are detected.

### PATCH-INV-17
Postconditions are validated before commit.

### PATCH-INV-18
Semantic validation does not execute application code.

### PATCH-INV-19
AXCOMPILER remains semantic authority.

### PATCH-INV-20
AXDIFF remains difference-discovery authority.

### PATCH-INV-21
AXMERGE remains multi-way integration authority.

### PATCH-INV-22
AXHISTORY remains lineage authority.

### PATCH-INV-23
AXVCS remains storage/transport authority.

### PATCH-INV-24
API impact is distinct from ABI impact.

### PATCH-INV-25
ABI impact is delegated to AXABI.

### PATCH-INV-26
Binary artifacts are not directly source-patched as canonical semantic state.

### PATCH-INV-27
Patch inversion is explicit about reversibility.

### PATCH-INV-28
Rebase preserves semantic intent or reports conflict.

### PATCH-INV-29
Conflict resolution is explicit.

### PATCH-INV-30
AI-generated patches are proposals unless explicitly accepted.

### PATCH-INV-31
Patch provenance is preserved.

### PATCH-INV-32
Malformed patches are rejected.

### PATCH-INV-33
Resource exhaustion is bounded.

### PATCH-INV-34
Path traversal is rejected.

### PATCH-INV-35
Patch application is deterministic under identical inputs/policy.

### PATCH-INV-36
Patch caches cannot override semantic validation.

### PATCH-INV-37
Preview/dry-run cannot mutate canonical state.

### PATCH-INV-38
Patch schema is explicitly versioned.

### PATCH-INV-39
Unknown mandatory semantic operations cannot be ignored.

### PATCH-INV-40
AXPATCH never invents semantic meaning absent compiler evidence.

---

# 200. Definition of Done

`AXPATCH 5.0` hoàn thành khi có:

- [x] Semantic Patch IR.
- [x] Source/AST compatibility patch forms.
- [x] Symbol-centric targeting.
- [x] Preconditions/postconditions.
- [x] Transactional application.
- [x] Rename/move.
- [x] Struct/enum/trait/generic/function operations.
- [x] Module transformations.
- [x] Extract/inline/split/merge operations.
- [x] Dependency-aware ordering.
- [x] Conflict detection.
- [x] Relocation.
- [x] Rebase.
- [x] Composition.
- [x] Inversion.
- [x] Provenance.
- [x] API impact.
- [x] ABI impact boundary.
- [x] Build/test impact metadata.
- [x] AI proposal boundary.
- [x] Deterministic serialization.
- [x] Patch identity.
- [x] Streaming.
- [x] Resource limits.
- [x] Security validation.
- [x] AXCOMPILER integration.
- [x] AXDIFF integration.
- [x] AXMERGE integration.
- [x] AXHISTORY integration.
- [x] AXVCS integration.
- [x] AXIDE integration.
- [x] AXTEST conformance.
- [x] `AXPATCH_ABI_1`.
- [x] `AXPATCH_SCHEMA_1`.
- [x] 40 `PATCH-INV`.

**AXPATCH 5.0 — FROZEN.**

---

# Hợp nhất kiến trúc Change System

Đến đây bộ thay đổi của Axiom đã có đầy đủ primitive:

```text
                 ┌─────────────┐
                 │ AXCOMPILER  │
                 │ semantic    │
                 │ authority   │
                 └──────┬──────┘
                        │
             ┌──────────▼──────────┐
             │       AXDIFF        │
             │ discover difference │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │      AXPATCH        │
             │ apply transformation│
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │      AXMERGE        │
             │ combine changes     │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │     AXHISTORY       │
             │ lineage/revisions   │
             └──────────┬──────────┘
                        │
             ┌──────────▼──────────┐
             │       AXVCS         │
             │ store/sync/remote   │
             └─────────────────────┘
```

Đây là một ranh giới kiến trúc rất quan trọng: **không component nào trong chuỗi này phải biết implementation nội bộ của component bên cạnh nó**. Chúng giao tiếp bằng semantic IDs, canonical artifacts và ABI/schema ổn định.

---

# BOOTSTRAP-800 — AXPACKAGE

**Native Axiom Package & Dependency System, Package Identity, Semantic Versioning, Dependency Graph, Version Constraints, Lockfile, Registry, Source/Artifact Resolution, Repository Integration, Content-Addressed Package Cache, Platform/Target Variants, Feature Resolution, Reproducible Dependency Graph, Package Signing & Trust Boundary, Offline/Private Registry, Workspace/Monorepo Packages, Build Integration & Package ABI 5.0**

Tiếp theo sẽ xử lý một phần rất quan trọng còn thiếu giữa:

```text
AXVCS
  ↓
source repository
  ↓
AXPACKAGE
  ↓
AXBUILD
  ↓
AXCOMPILER
```

và đặc biệt phải giữ nguyên nguyên tắc của Axiom: **package manager không được trở thành một runtime dependency bắt buộc của executable cuối cùng**.