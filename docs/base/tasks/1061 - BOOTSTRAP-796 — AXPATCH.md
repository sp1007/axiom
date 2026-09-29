# BOOTSTRAP-796 — AXPATCH
## Native Axiom Semantic Patch Engine, Symbol-Aware Patch Representation, AST/IR/API/ABI Patch Application, Patch Composition, Patch Inversion, Patch Validation, Patch Rebasing, Patch Transformation, Patch Provenance, Deterministic Patch Serialization & Patch ABI 5.0

**Status:** FROZEN — Architecture Specification v5.0  
**Namespace:** `AXPATCH`  
**ABI:** `AXPATCH_ABI_1`  
**Schema:** `AXPATCH_SCHEMA_1`  
**Artifact:** `.axpatch`

**Dependencies:**
```text
AXCOMPILER
AXDIFF
AXMERGE
AXABI
AXDOC
AXBUILD
AXPACKAGE
AXTEST
AXEDITOR
AXCODEEDITOR
AXIDE
```

---

# 1. Mục tiêu

`AXPATCH` là lớp biểu diễn và thao tác **thay đổi có cấu trúc** của Axiom.

Nó biến:

```text
"file X, dòng 41 thay A bằng B"
```

thành:

```text
"Symbol S123, member M456, semantic property P,
 chuyển từ ValueHash A → ValueHash B"
```

Kiến trúc:

```text
AXDIFF
   │
   ▼
Semantic Changes
   │
   ▼
AXPATCH
   │
   ├── apply
   ├── reverse
   ├── compose
   ├── rebase
   ├── transform
   ├── validate
   └── serialize
   │
   ├──────────────┬──────────────┐
   ▼              ▼              ▼
AXEDITOR      AXCOMPILER       AXMERGE
```

AXPATCH phải hỗ trợ:

- source patch;
- token patch;
- AST patch;
- semantic patch;
- API patch;
- ABI-aware patch;
- dependency patch;
- build configuration patch;
- metadata patch;
- patch composition;
- patch inversion;
- patch rebasing;
- patch validation;
- patch provenance;
- deterministic serialization.

---

# 2. Nguyên tắc nền tảng

## PATCH-PRINCIPLE-01 — Semantic identity trước source location

Ưu tiên:

```text
SymbolId
DeclarationId
MemberId
TypeId
NodeId
SourceRange
TextOffset
```

Source range chỉ là fallback.

---

## PATCH-PRINCIPLE-02 — Patch không phụ thuộc tuyệt đối vào dòng

Một patch hợp lệ phải tiếp tục có khả năng áp dụng sau khi:

- thêm dòng phía trên;
- format lại file;
- di chuyển declaration;
- thay đổi whitespace;
- thay đổi comment.

nếu semantic target vẫn tồn tại.

---

## PATCH-PRINCIPLE-03 — Patch phải có precondition

Patch không được chỉ chứa:

```text
old → new
```

mà phải có:

```text
target identity
expected state
operation
new state
```

Ví dụ:

```text
target = S123
expected_hash = H1
operation = MODIFY
new_hash = H2
```

Nếu target hiện tại có hash `H3`:

```text
PATCH_PRECONDITION_FAILED
```

---

# 3. Boundary

AXPATCH sở hữu:

```text
patch representation
patch creation
patch application
patch inversion
patch composition
patch rebasing
patch transformation
patch validation
patch provenance
patch serialization
```

Không sở hữu:

```text
compiler semantics
text editor storage
merge policy
type checking
ABI implementation
dependency solving
build execution
```

---

# 4. Architecture

```text
                    AXPATCH
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
 Patch Model       Patch Planner    Patch Validator
       │               │                │
       ▼               ▼                ▼
 Semantic Ops      Dependency DAG    Preconditions
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                Patch Transformer
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        Apply        Rebase       Compose
          │            │            │
          └────────────┼────────────┘
                       ▼
                Canonical Result
```

---

# 5. Patch kinds

```text
enum PatchKind {
    TEXT,
    TOKEN,
    AST,
    SEMANTIC,
    API,
    ABI,
    DEPENDENCY,
    BUILD,
    METADATA,
    COMBINED
}
```

Default:

```text
SEMANTIC
```

---

# 6. Patch identity

```text
struct PatchId {
    hash: Hash
}
```

Canonical:

```text
PatchId =
hash(
    schema,
    target_identity,
    operations,
    preconditions,
    metadata
)
```

Patch ID must not depend on:

- wall-clock time;
- process ID;
- random UUID;
- machine hostname.

---

# 7. Core Patch

```text
struct Patch {
    id: PatchId

    kind: PatchKind
    schema: SchemaVersion

    target: TargetIdentity
    abi: optional<AbiIdentity>

    preconditions: [PatchPrecondition]
    operations: [PatchOperation]

    dependencies: [PatchDependency]

    provenance: PatchProvenance

    metadata: PatchMetadata
}
```

---

# 8. Patch operation

```text
enum PatchOperation {
    Add
    Remove
    Modify
    Rename
    Move
    Reorder

    ReplaceType
    ReplaceSignature
    ReplaceBody

    AddField
    RemoveField
    ModifyField

    AddVariant
    RemoveVariant
    ModifyVariant

    AddTraitItem
    RemoveTraitItem
    ModifyTraitItem

    AddGenericParameter
    RemoveGenericParameter
    ModifyConstraint

    AddImport
    RemoveImport
    ModifyImport

    ChangeVisibility
    ChangeAttribute
    ChangeEffect

    DependencyChange
    BuildSettingChange

    MetadataChange
}
```

---

# 9. Operation identity

```text
struct PatchOperation {
    id: OperationId

    target: SemanticId
    parent: optional<SemanticId>

    kind: OperationKind

    before: optional<Value>
    after: optional<Value>

    precondition: optional<Hash>

    position: optional<SemanticPosition>

    provenance: Provenance
}
```

---

# 10. SemanticPosition

Position phải có semantic preference:

```text
enum SemanticPosition {
    BEFORE(SymbolId)
    AFTER(SymbolId)
    FIRST
    LAST
    INDEX(u32)
}
```

`INDEX` là fallback yếu hơn `BEFORE/AFTER`.

---

# 11. Add

```text
Add(
    parent = S100,
    value = Function F123,
    position = AFTER(F122)
)
```

Nếu `F122` không còn tồn tại, engine có thể dùng policy fallback:

```text
AFTER semantic neighbor
→ canonical location
→ structural insertion
→ conflict
```

---

# 12. Remove

Remove phải chứa expected identity:

```text
Remove {
    target = F123
    expected_hash = H123
}
```

Nếu F123 đã thay đổi:

```text
REMOVE_PRECONDITION_FAILED
```

Không được xóa phiên bản mới một cách âm thầm.

---

# 13. Modify

```text
Modify {
    target = F123
    expected_hash = H1
    new_value = V2
}
```

Patch application:

```text
current_hash == H1
        │
       yes
        ↓
apply V2
```

Nếu không:

```text
CONFLICT
```

---

# 14. Rename

```text
Rename {
    target = SymbolId
    old_name = "calculate"
    new_name = "compute"
}
```

Rename phải giữ:

```text
SymbolId
```

không được tạo symbol mới nếu semantic identity không thay đổi.

---

# 15. Move

```text
Move {
    target = S123
    from_parent = M1
    to_parent = M2
    position = AFTER(S122)
}
```

Move không được biểu diễn mặc định bằng:

```text
Remove + Add
```

vì như vậy sẽ phá identity.

---

# 16. Reorder

```text
Reorder {
    parent = S100
    target = S123
    before = S124
}
```

Reorder chỉ thay đổi ordering metadata nếu semantic identity không thay đổi.

---

# 17. Struct field patch

```text
AddField {
    struct = User
    field = age: u32
}
```

Patch phải có:

```text
StructId
FieldId
TypeId
layout_policy
```

---

# 18. Enum patch

```text
AddVariant {
    enum = Color
    variant = Blue
    discriminant = 3
}
```

Nếu discriminant đã được sử dụng:

```text
PATCH_ENUM_DISCRIMINANT_CONFLICT
```

---

# 19. Trait patch

```text
AddTraitItem {
    trait = Drawable
    item = bounds()
}
```

Trait coherence/semantic validity được kiểm tra thông qua AXCOMPILER.

---

# 20. Generic patch

```text
ModifyConstraint {
    function = F123
    parameter = T
    before = Copy
    after = Clone
}
```

AXPATCH chỉ mô tả thay đổi.

AXCOMPILER xác định constraint có hợp lệ hay không.

---

# 21. API patch

```text
ApiPatch {
    symbol
    old_signature
    new_signature
    visibility
    compatibility
}
```

API patch không tự kết luận compatibility.

AXDIFF/AXABI cung cấp compatibility analysis.

---

# 22. ABI patch

ABI-aware patch chứa:

```text
target
abi
symbol
calling_convention
layout_before
layout_after
export_state
import_state
```

Ví dụ thay đổi:

```text
struct field
```

có thể tạo:

```text
ABI_AFFECTING_PATCH
```

nhưng AXABI mới xác định mức độ break.

---

# 23. Dependency patch

```text
DependencyPatch {
    package
    old_constraint
    new_constraint

    old_features
    new_features

    target_conditions
}
```

---

# 24. Build patch

```text
BuildPatch {
    target
    property
    old_value
    new_value
}
```

Ví dụ:

```text
optimization = O2 → O3
```

không phải source semantic change nhưng vẫn là reproducibility-relevant change.

---

# 25. Preconditions

```text
struct PatchPrecondition {
    target: SemanticId
    expected_kind: NodeKind
    expected_hash: Hash

    optional_parent: SemanticId
    optional_signature: SignatureHash
}
```

---

# 26. Preconditions policy

```text
enum PreconditionPolicy {
    STRICT
    SEMANTIC
    STRUCTURAL
    TEXTUAL
    NONE
}
```

Default:

```text
STRICT
```

`NONE` chỉ được phép trong explicit low-level tooling.

---

# 27. Patch application

```text
apply(
    patch,
    target,
    policy
) → ApplyResult
```

Algorithm:

```text
1. validate patch schema
2. validate target identity
3. validate target ABI
4. resolve semantic IDs
5. evaluate preconditions
6. construct operation DAG
7. apply operations
8. validate resulting semantic model
9. emit provenance
10. produce result hash
```

---

# 28. Atomicity

Patch application phải atomic.

Không được:

```text
operation 1 → success
operation 2 → conflict
operation 3 → silently remain applied
```

Default:

```text
all-or-nothing
```

---

# 29. Transaction model

```text
PatchTransaction {
    base_revision
    patch
    working_snapshot

    operations
    result
}
```

Commit:

```text
validate
  ↓
commit
```

Failure:

```text
rollback
```

---

# 30. AXEDITOR integration

AXPATCH không sửa buffer trực tiếp.

Pipeline:

```text
AXPATCH
   ↓
PatchApplication
   ↓
AXEDITOR Transaction
   ↓
TextBuffer
```

AXEDITOR quyết định:

- text ranges;
- undo/redo;
- cursor preservation;
- selection preservation.

AXPATCH quyết định:

- semantic operation;
- identity;
- precondition.

---

# 31. Undo

Undo có thể được biểu diễn bằng inverse patch.

```text
P
↓
apply
↓
P⁻¹
```

AXEDITOR vẫn có quyền quản lý UI undo stack.

---

# 32. Patch inversion

Mỗi invertible operation:

```text
ADD       ↔ REMOVE
MODIFY    ↔ MODIFY(reverse)
RENAME    ↔ RENAME(reverse)
MOVE      ↔ MOVE(reverse)
REORDER   ↔ REORDER(reverse)
```

Không phải mọi patch đều invertible.

Ví dụ:

```text
REGENERATE
```

có thể không có inverse nếu generator state không được lưu.

---

# 33. Inverse patch

```text
invert(P) → P_inverse
```

Yêu cầu:

```text
apply(P)
apply(P_inverse)
```

phải khôi phục semantic state ban đầu nếu không có external mutation.

---

# 34. Patch composition

```text
P1
 ↓
P2
 ↓
P3
```

có thể compose:

```text
compose(P1, P2) → P12
compose(P12, P3) → P123
```

---

# 35. Composition correctness

Nếu:

```text
S1 = apply(P1, S0)
S2 = apply(P2, S1)
```

thì:

```text
apply(compose(P1,P2), S0) = S2
```

với điều kiện preconditions tương thích.

---

# 36. Composition conflict

Nếu:

```text
P1:
x = 10 → 20

P2:
x = 10 → 30
```

thì:

```text
compose(P1,P2)
```

phải tạo conflict.

Không được chọn 20 hoặc 30 âm thầm.

---

# 37. Patch rebase

Rebase:

```text
Patch P
   ↓
Base A
   ↓
New Base B
```

Mục tiêu:

```text
P' applies to B
```

và giữ nguyên semantic intent của P.

---

# 38. Rebase algorithm

```text
rebase(P, A → B)
```

Pipeline:

```text
1. identify P targets
2. diff A → B
3. transform P against Δ(A,B)
4. preserve SymbolId
5. update positions
6. validate preconditions
7. emit conflicts if intent cannot be preserved
```

---

# 39. Rebase example

BASE:

```text
fn foo()
fn bar()
```

Patch:

```text
modify foo
```

New base:

```text
fn new_function()
fn foo()
fn bar()
```

Patch vẫn áp dụng vào `foo` vì identity không thay đổi.

Line-based patch có thể thất bại; semantic patch không.

---

# 40. Rebase rename

BASE:

```text
foo()
```

Patch:

```text
modify foo
```

New base:

```text
compute()
```

Nếu `foo → compute` được AXDIFF/semantic identity xác nhận:

```text
rebase(P)
```

sẽ chuyển target:

```text
foo → compute
```

nhưng giữ nguyên `SymbolId`.

Nếu identity không chắc chắn:

```text
REBASE_IDENTITY_CONFLICT
```

---

# 41. Patch transformation

```text
transform(P, Q)
```

tìm patch `P'` sao cho:

```text
apply(P)
then Q
```

tương đương về semantic state với:

```text
apply(Q)
then P'
```

nếu hai patch có thể commute.

---

# 42. Commutativity

Hai patch có thể commute nếu:

```text
targets independent
```

hoặc semantic algebra chứng minh rằng thứ tự không ảnh hưởng kết quả.

Không giả định mọi operation đều commute.

---

# 43. Dependency DAG

Patch operations được biểu diễn:

```text
Operation A
   ↓
Operation B
   ↓
Operation C
```

Ví dụ:

```text
Rename Type
    ↓
Update Field
    ↓
Update Function Signature
    ↓
Update API
```

---

# 44. Patch ordering

Canonical ordering:

```text
identity changes
→ structural changes
→ declaration changes
→ body changes
→ dependency changes
→ metadata
→ validation
```

Trong mỗi lớp:

```text
semantic path
then OperationId
```

để đảm bảo determinism.

---

# 45. Patch conflict

```text
struct PatchConflict {
    id: ConflictId

    patch_a: PatchId
    patch_b: PatchId

    target: SemanticId

    kind: PatchConflictKind

    evidence
    resolution
}
```

---

# 46. Conflict kinds

```text
TARGET_COLLISION
PRECONDITION_CONFLICT
VALUE_CONFLICT
TYPE_CONFLICT
IDENTITY_CONFLICT
ORDER_CONFLICT
DEPENDENCY_CONFLICT
API_CONFLICT
ABI_CONFLICT
POLICY_CONFLICT
REBASE_CONFLICT
```

---

# 47. Patch compatibility

```text
PatchCompatibility {
    COMPATIBLE
    COMMUTATIVE
    ORDER_DEPENDENT
    CONFLICTING
    INCOMPARABLE
}
```

`INCOMPARABLE` không được tự chuyển thành `COMPATIBLE`.

---

# 48. Patch validation

Validation layers:

```text
syntax
 ↓
identity
 ↓
structure
 ↓
semantic
 ↓
API
 ↓
ABI
 ↓
dependency
 ↓
build
```

Không nhất thiết mọi patch đều cần mọi layer.

---

# 49. Fast validation

IDE interactive mode:

```text
identity
structure
local semantic
```

Full commit mode:

```text
semantic
API
ABI
dependency
tests/build as configured
```

---

# 50. Patch impact

Mỗi patch có thể chứa:

```text
Impact {
    symbols
    modules
    APIs
    ABI
    dependencies
    targets
    tests
}
```

Impact được AXCOMPILER/AXABI/AXBUILD cung cấp hoặc xác nhận.

---

# 51. Patch provenance

```text
PatchProvenance {
    source_kind
    source_artifact
    source_commit
    source_change
    author
    parent_patch
    generated_by
}
```

Không yêu cầu timestamp để xác định patch identity.

---

# 52. AI provenance

Nếu AI tạo patch:

```text
generated_by = AI_PROPOSAL
```

Phải lưu:

```text
model_identifier
prompt/context identifier
input semantic hashes
```

khi policy cho phép.

Không lưu secret/prompt-sensitive data mặc định nếu không cần thiết.

---

# 53. AI patch acceptance

```text
AI
 ↓
Patch Proposal
 ↓
AXPATCH validation
 ↓
Human/explicit policy
 ↓
Apply
```

AI không được bypass preconditions.

---

# 54. Patch signatures

Patch artifact có thể được ký ở lớp AXTRUST/AXCRYPTO.

AXPATCH chỉ cung cấp:

```text
canonical bytes
artifact hash
```

Không tự định nghĩa cryptographic primitives.

---

# 55. Patch storage

`.axpatch`:

```text
header
schema
target
abi
base identity
operations
preconditions
dependencies
provenance
metadata
hash
optional signature reference
```

---

# 56. Binary vs source patch

AXPATCH phân biệt:

```text
SOURCE_PATCH
SEMANTIC_PATCH
BINARY_PATCH
```

Binary patch không được tự động coi là source patch.

Native executable modification thuộc binary tooling và không được chuyển ngược thành source mutation nếu không có semantic evidence.

---

# 57. Object patch

Object artifacts có thể được patch ở mức:

```text
section
symbol
relocation
metadata
```

nhưng việc tạo executable cuối cùng vẫn thuộc:

```text
AXLINKER
```

---

# 58. ABI patch restrictions

Một patch thay đổi:

```text
struct layout
calling convention
export
symbol visibility
parameter type
return type
```

phải được đánh dấu:

```text
ABI_AFFECTING
```

và có thể yêu cầu AXABI validation trước apply.

---

# 59. Dependency patch restrictions

Dependency patch phải xác định:

```text
package identity
constraint
feature set
target
source/checksum
```

Không được thay checksum mà không thay package identity/version/source tương ứng nếu policy yêu cầu integrity.

---

# 60. Generated patch

Generated artifact patch:

```text
GENERATOR_ID
GENERATOR_VERSION
INPUT_HASHES
OUTPUT_HASH
```

Nếu generator inputs chưa thay đổi, patch không được ghi nhận output khác biệt như source change mà không có explanation.

---

# 61. Metadata patch

AI/doc/debug metadata có thể được patch riêng.

Ví dụ:

```text
ModifyDocumentation(S123)
```

không cần sửa implementation của S123.

---

# 62. Patch scopes

```text
PROJECT
PACKAGE
MODULE
FILE
DECLARATION
SYMBOL
MEMBER
EXPRESSION
TOKEN
TEXT
```

Engine chọn scope nhỏ nhất đủ biểu diễn thay đổi.

---

# 63. Minimal patch

AXPATCH phải cố gắng tạo patch semantic tối thiểu.

Ví dụ:

```text
rename foo → bar
```

không nên sinh:

```text
remove foo
add bar
```

nếu identity vẫn giữ được.

---

# 64. Patch normalization

Equivalent patches phải có thể normalize về cùng semantic representation.

Ví dụ:

```text
ADD import A
ADD import A
```

normalize:

```text
ADD import A
```

nếu import set semantics cho phép.

---

# 65. Canonical patch

Canonicalization:

```text
normalize
→ deduplicate
→ resolve identity aliases
→ sort independent operations
→ normalize values
→ canonical serialize
```

---

# 66. Patch equality

Có ba mức:

```text
TEXT_EQUAL
STRUCTURAL_EQUAL
SEMANTIC_EQUAL
```

Hai patch khác text vẫn có thể:

```text
SEMANTIC_EQUAL
```

---

# 67. Patch hashing

AXPATCH phải cung cấp:

```text
text_hash
structural_hash
semantic_hash
```

Semantic hash là hash của normalized operation graph, không phải text bytes.

---

# 68. Patch caching

Cache key:

```text
hash(
    patch_id,
    target_semantic_hash,
    policy_hash,
    compiler_schema,
    abi
)
```

---

# 69. Patch replay

AXTEST và AXIDE có thể replay:

```text
base snapshot
+
patch sequence
```

để tái tạo trạng thái.

Replay phải deterministic nếu input/environment deterministic.

---

# 70. Patch chain

```text
P1 → P2 → P3 → P4
```

Có thể compact:

```text
compose(P1,P2,P3,P4)
→ P1234
```

Nhưng provenance của từng patch phải được giữ.

---

# 71. Patch squashing

Squash chỉ thay đổi representation.

Không được làm mất:

```text
original PatchIds
provenance
authors
source changes
resolution records
```

nếu audit policy yêu cầu.

---

# 72. Patch splitting

Một patch có thể split theo:

```text
module
symbol
semantic layer
dependency
API
ABI
```

Ví dụ:

```text
P
 ↓
P-source
P-api
P-dependency
P-metadata
```

---

# 73. Patch extraction từ AXDIFF

```text
AXDIFF
   ↓
DiffResult
   ↓
AXPATCH.from_diff()
```

Mọi semantic diff có thể được chuyển thành patch nếu change có đủ information để apply.

Nếu chỉ có evidence:

```text
NON_APPLICABLE_DIFF
```

---

# 74. Patch generation từ AXMERGE

AXMERGE:

```text
BASE
LEFT
RIGHT
 ↓
MergeResult
```

có thể xuất:

```text
Patch(BASE → MERGED)
```

Điều này cho phép:

```text
merge preview
→ review patch
→ apply
```

---

# 75. Patch extraction from editor

AXEDITOR transaction:

```text
text edit
 ↓
AXCOMPILER incremental semantics
 ↓
AXPATCH
```

Cho phép IDE lưu semantic history thay vì chỉ text history.

---

# 76. Patch review

AXIDE có thể hiển thị:

```text
Patch
 ├ semantic target
 ├ old state
 ├ new state
 ├ API impact
 ├ ABI impact
 ├ dependency impact
 └ provenance
```

Không bắt buộc người dùng đọc raw diff.

---

# 77. Patch application modes

```text
APPLY_STRICT
APPLY_SEMANTIC
APPLY_REBASE
APPLY_FORCE
PREVIEW_ONLY
VALIDATE_ONLY
```

`APPLY_FORCE` không được bypass safety-critical ABI/dependency validation; nó chỉ có thể relax explicitly permitted preconditions.

---

# 78. Preview

```text
preview(patch)
```

không thay đổi persistent project state.

Output:

```text
PreviewResult {
    affected_symbols
    proposed_source
    conflicts
    api_report
    abi_report
    dependency_report
}
```

---

# 79. Failure atomicity

Nếu validation cuối cùng fail:

```text
working snapshot
```

bị hủy.

Không commit partial semantic state.

---

# 80. Concurrency

Hai editor sessions:

```text
Session A → P1
Session B → P2
```

có thể:

```text
compose(P1,P2)
```

nếu independent.

Nếu cùng target:

```text
conflict
```

unless semantic transform proves compatibility.

---

# 81. Optimistic concurrency

Patch application sử dụng:

```text
base_revision
semantic_hash
```

Nếu target đã thay đổi:

```text
STALE_PATCH
```

→ rebase hoặc conflict.

---

# 82. Multi-user collaboration

AXPATCH là nền tảng cho collaborative editing nhưng không tự sở hữu transport.

```text
AXPATCH
   ↓
collaboration protocol
```

Transport/session/auth thuộc subsystem khác.

---

# 83. Large project scaling

Không materialize toàn bộ AST nếu không cần.

Use:

```text
lazy semantic nodes
symbol index
persistent snapshots
operation DAG
incremental validation
```

---

# 84. Parallel patch application

Independent operations có thể xử lý song song:

```text
Module A ──┐
Module B ──┼→ validation → canonical commit
Module C ──┘
```

Commit order deterministic.

---

# 85. Security

Patch input là untrusted.

Phải giới hạn:

```text
operation_count
graph_depth
dependency_edges
payload_size
string_size
AST_depth
memory
CPU
```

Không thực thi code để áp dụng semantic patch.

---

# 86. Path security

File paths trong patch phải canonicalize.

Không cho phép:

```text
../
absolute escape
symlink escape
```

vượt project sandbox/policy.

---

# 87. No hidden mutation

AXPATCH API phải phân biệt:

```text
preview()
validate()
apply()
commit()
```

Không API nào ngoài `apply/commit` được phép thay đổi persistent state.

---

# 88. Determinism

Cùng:

```text
Patch
Target
Policy
CompilerSchema
Abi
```

phải tạo cùng:

```text
ApplyResult
conflict IDs
semantic hash
canonical serialization
```

---

# 89. API

Core:

```text
create_patch()
from_diff()
validate()
apply()
preview()
invert()
compose()
rebase()
transform()
normalize()
split()
squash()
serialize()
deserialize()
```

---

# 90. API signatures

Conceptual:

```text
Patch create_patch(ChangeSet)

Patch from_diff(DiffResult)

PatchValidation validate(
    Patch,
    Target,
    PatchPolicy
)

ApplyResult apply(
    Patch,
    Target,
    ApplyPolicy
)

PreviewResult preview(
    Patch,
    Target,
    ApplyPolicy
)

Patch invert(Patch)

ComposeResult compose(Patch, Patch)

RebaseResult rebase(
    Patch,
    BaseSnapshot,
    NewBaseSnapshot
)

TransformResult transform(
    Patch,
    Patch
)
```

---

# 91. ABI

`AXPATCH_ABI_1` phải ổn định cho:

```text
Patch
PatchOperation
PatchPrecondition
PatchDependency
PatchConflict
PatchResolution
PatchProvenance
PatchMetadata
ApplyResult
PreviewResult
ValidationResult
```

Dùng stable IDs thay vì compiler-private pointers.

---

# 92. Schema

`AXPATCH_SCHEMA_1` phải version hóa:

```text
operation kinds
value encoding
semantic identity
provenance
serialization
policy fields
```

Không deserialize schema mới như schema cũ nếu semantics không tương thích.

---

# 93. `.axpatch`

Canonical layout:

```text
AXPATCH
├── Header
├── Schema
├── Target
├── ABI
├── BaseIdentity
├── Operations
├── Preconditions
├── Dependencies
├── Provenance
├── Metadata
└── Integrity
```

---

# 94. Provenance graph

Patch provenance:

```text
Source
  ↓
AXDIFF
  ↓
Patch P1
  ↓
Patch P2
  ↓
Merged Patch
  ↓
Applied Revision
```

Có thể truy ngược từ merged state về source changes.

---

# 95. AI context export

AXPATCH có thể tạo compact AI context:

```text
PatchContext {
    target_symbols
    before
    after
    affected_dependencies
    conflicts
    API impact
    ABI impact
    provenance
}
```

AI không cần nhận toàn repository.

---

# 96. AI semantic patch generation

AI được phép đề xuất:

```text
Rename
Modify
Add
Remove
Move
```

nhưng output bắt buộc phải parse/validate thành `Patch`.

Không cho phép AI trực tiếp trả:

```text
"hãy sửa file này"
```

rồi bypass semantic validation.

---

# 97. AXDOC

Documentation change:

```text
DocPatch
```

có thể target:

```text
SymbolId + DocNodeId
```

AXDOC đảm bảo documentation model hợp lệ.

---

# 98. AXTEST requirements

AXTEST phải kiểm thử:

```text
apply
inverse
compose
rebase
transform
normalization
determinism
preconditions
identity preservation
API
ABI
dependency
generated artifacts
AI proposal validation
```

---

# 99. Algebraic tests

### Identity

```text
apply(identity_patch, S) = S
```

### Inverse

```text
apply(invert(P), apply(P,S)) = S
```

### Composition

```text
apply(compose(P,Q),S)
=
apply(Q,apply(P,S))
```

### Idempotence

Patch không có side effects ngoài semantic state phải thỏa:

```text
apply(P, apply(P,S))
```

→ conflict/stale hoặc semantic equivalent theo policy; không được tạo duplicate unintended changes.

---

# 100. Rebase correctness

Nếu:

```text
S1 = apply(P, A)
```

và rebase tạo `P'` trên B:

```text
S2 = apply(P', B)
```

thì `S2` phải giữ semantic intent của P tương ứng với những thay đổi của A→B.

Không yêu cầu byte-for-byte equality.

---

# 101. Conflict correctness

AXTEST phải chứng minh:

```text
conflicting P/Q
```

không bị compose thành một patch có semantic meaning không được chứng minh.

---

# 102. Rename tests

```text
rename
rename + modify
rename after base rename
rename conflict
rename vs delete
rename vs move
same rename
```

---

# 103. Struct tests

```text
add independent fields
same field modification
field type conflict
field rename
field reorder
layout change
```

---

# 104. Enum tests

```text
same variant
different variant
same discriminant
different discriminant
variant payload
variant rename
```

---

# 105. Generic tests

```text
add parameter
remove parameter
constraint change
constraint conflict
generic rename
```

---

# 106. Dependency tests

```text
version update
same update
conflicting update
feature addition
feature conflict
lockfile checksum
target-specific dependency
```

---

# 107. ABI tests

Verify patches affecting:

```text
struct layout
alignment
calling convention
parameter type
return type
export visibility
symbol name
TLS
```

produce appropriate AXABI validation.

---

# 108. Serialization tests

Require:

```text
serialize(P)
deserialize(bytes)
semantic_equal(P,P')
```

and:

```text
serialize(P)
==
serialize(P')
```

for equivalent canonical patches.

---

# 109. Security tests

Fuzz:

```text
malformed patch
deep operation DAG
huge payload
invalid IDs
cyclic dependencies
invalid paths
schema confusion
```

Expected behavior:

```text
reject safely
```

never crash or execute arbitrary content.

---

# 110. Performance target

For a patch affecting `K` semantic nodes:

```text
time ≈ O(K + affected_dependency_edges)
```

rather than:

```text
O(total_repository_size)
```

when indexes permit localized resolution.

---

# 111. Memory target

Patch representation must scale approximately with:

```text
O(number_of_operations + referenced_semantic_nodes)
```

not full project size.

---

# 112. Patch compaction

Large patch chains may be compacted using:

```text
persistent semantic snapshots
+
operation DAG
+
provenance references
```

without copying unchanged source.

---

# 113. Failure codes

```text
PATCH_INVALID
PATCH_SCHEMA_UNSUPPORTED
PATCH_TARGET_NOT_FOUND
PATCH_TARGET_AMBIGUOUS
PATCH_PRECONDITION_FAILED
PATCH_IDENTITY_CONFLICT
PATCH_OPERATION_CONFLICT
PATCH_TYPE_CONFLICT
PATCH_API_CONFLICT
PATCH_ABI_CONFLICT
PATCH_DEPENDENCY_CONFLICT
PATCH_REBASE_CONFLICT
PATCH_TRANSFORM_CONFLICT
PATCH_VALIDATION_FAILED
PATCH_RESOURCE_LIMIT
PATCH_SECURITY_VIOLATION
PATCH_SERIALIZATION_FAILED
```

---

# 114. 40 invariants

### PATCH-INV-01
Patch IDs are deterministic.

### PATCH-INV-02
Semantic identity has priority over source location.

### PATCH-INV-03
Every mutating operation has an explicit target.

### PATCH-INV-04
Every destructive operation has an expected state.

### PATCH-INV-05
Precondition failure never silently applies the patch.

### PATCH-INV-06
Patch application is atomic by default.

### PATCH-INV-07
Rename preserves SymbolId.

### PATCH-INV-08
Move preserves SymbolId.

### PATCH-INV-09
Independent operations may be parallelized.

### PATCH-INV-10
Parallel execution cannot alter result ordering.

### PATCH-INV-11
Add operations cannot silently overwrite an existing semantic identity.

### PATCH-INV-12
Remove cannot delete a changed target under strict policy.

### PATCH-INV-13
Modify validates expected state.

### PATCH-INV-14
Reorder does not alter semantic identity.

### PATCH-INV-15
Formatting does not alter semantic identity.

### PATCH-INV-16
Equivalent operations may be normalized.

### PATCH-INV-17
Semantic equality is distinct from textual equality.

### PATCH-INV-18
Inverse patches preserve provenance.

### PATCH-INV-19
Non-invertible operations explicitly report non-invertibility.

### PATCH-INV-20
Composition cannot silently resolve conflicting writes.

### PATCH-INV-21
Rebase preserves identity when identity evidence permits.

### PATCH-INV-22
Ambiguous rebase produces explicit conflict.

### PATCH-INV-23
Transformation cannot discard a semantic change silently.

### PATCH-INV-24
API-affecting patches are explicitly marked.

### PATCH-INV-25
ABI-affecting patches are explicitly marked.

### PATCH-INV-26
ABI compatibility is delegated to AXABI.

### PATCH-INV-27
Dependency patches preserve package identity/integrity metadata.

### PATCH-INV-28
Generated artifacts obey declared generation policy.

### PATCH-INV-29
Binary patches cannot masquerade as source patches.

### PATCH-INV-30
AI-generated patches remain proposals until accepted.

### PATCH-INV-31
AI cannot bypass validation.

### PATCH-INV-32
Every applied operation has provenance.

### PATCH-INV-33
Persistent mutation occurs only through explicit apply/commit paths.

### PATCH-INV-34
Patch serialization is canonical.

### PATCH-INV-35
Deserialization validates schema before semantic interpretation.

### PATCH-INV-36
Untrusted patches cannot trigger arbitrary code execution.

### PATCH-INV-37
Resource limits are enforced.

### PATCH-INV-38
Cache keys include semantic/schema/policy identity.

### PATCH-INV-39
Equivalent canonical patches produce identical semantic hashes.

### PATCH-INV-40
AXPATCH never silently invents semantic intent.

---

# 115. Definition of Done

`AXPATCH 5.0` được coi là hoàn thành khi:

- [x] Semantic patch model được định nghĩa.
- [x] Symbol-aware identity được định nghĩa.
- [x] Preconditions được định nghĩa.
- [x] Atomic application được định nghĩa.
- [x] AST/semantic/API/ABI patch được định nghĩa.
- [x] Struct/enum/union/trait/generic operation được định nghĩa.
- [x] Rename/move/reorder được định nghĩa.
- [x] Inverse patch được định nghĩa.
- [x] Patch composition được định nghĩa.
- [x] Patch transformation được định nghĩa.
- [x] Patch rebase được định nghĩa.
- [x] Conflict model được định nghĩa.
- [x] Dependency patch được định nghĩa.
- [x] Build/generated artifact boundary được định nghĩa.
- [x] Provenance được định nghĩa.
- [x] AI proposal boundary được định nghĩa.
- [x] AXEDITOR integration được định nghĩa.
- [x] AXCOMPILER integration được định nghĩa.
- [x] AXDIFF integration được định nghĩa.
- [x] AXMERGE integration được định nghĩa.
- [x] AXABI integration được định nghĩa.
- [x] AXBUILD/AXPACKAGE integration được định nghĩa.
- [x] Deterministic serialization được định nghĩa.
- [x] Incremental/parallel operation được định nghĩa.
- [x] Security/resource limits được định nghĩa.
- [x] 40 invariants được đóng băng.
- [x] `AXPATCH_ABI_1` được đóng băng.
- [x] `AXPATCH_SCHEMA_1` được đóng băng.

**AXPATCH 5.0 — FROZEN.**

---

# 116. Vị trí mới trong kiến trúc Axiom

Ba lớp hiện tạo thành một pipeline rất rõ:

```text
                 CHANGE INTELLIGENCE
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       AXDIFF         AXMERGE        AXPATCH
          │              │              │
       detect          combine         apply
       change          changes         changes
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                    AXCOMPILER
                         │
                    semantic truth
                         │
                         ▼
                      AXBUILD
```

Có thể hiểu ngắn gọn:

```text
AXDIFF  = "đã thay đổi gì?"
AXMERGE = "các thay đổi kết hợp thế nào?"
AXPATCH = "biểu diễn và áp dụng thay đổi đó ra sao?"
```

Đây là một boundary quan trọng: **Axiom không còn phụ thuộc vào text diff để xây dựng hệ thống versioning/IDE/AI/refactoring.**

---

# BOOTSTRAP-797 — AXHISTORY

**Native Axiom Semantic History Engine, Symbol-Centric Revision Graph, Semantic Commit Model, Change Lineage, Patch/Commit DAG, Branch/Tag/Revision Semantics, Rename/Move-Aware History, API/ABI History, Dependency History, Blame/Attribution, Reproducible Revision Identity, Incremental History Index, Semantic Log & History ABI 5.0**

AXHISTORY sẽ xây lớp **semantic version history** phía trên `AXDIFF + AXPATCH + AXMERGE`: thay vì lịch sử chỉ là danh sách commit và line numbers, Axiom sẽ có lịch sử theo **SymbolId → semantic change → patch → revision → branch/merge lineage**, phục vụ IDE, refactoring, AI và phân tích API/ABI lâu dài.