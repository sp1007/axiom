# BOOTSTRAP-794 — AXDIFF

**Native Axiom Binary/Source/ABI/IR/Debug/Crash/Replay Difference Engine, Semantic Diff, API/ABI Compatibility Analysis, Executable/Object Comparison, Structural Binary Diff, Compiler Regression Diff, Crash/Replay Diff, Deterministic Comparison Artifacts & Difference Analysis ABI 5.0**

**Status:** FROZEN — 5.0  
**Namespace:** `AXDIFF`  
**ABI:** `AXDIFF_ABI_1`  
**Artifact:** `.axdiff`  
**Schema:** `AXDIFF_SCHEMA_1`

**Depends on:** `AXCOMPILER`, `AXABI`, `AXOBJECT`, `AXBINARY`, `AXLINKER`, `AXDEBUGGER`, `AXCRASH`, `AXREPLAY`, `AXPROFILER`, `AXDOC`, `AXTEST`, `AXBUILD`, `AXTOOLCHAIN`, `AXPACKAGE`, `AXSTANDARD`

**Optional integrations:** `AXIDE`, `AXCODEEDITOR`, `AXDIAGNOSTICS`, `AXOBSERVABILITY`, `AXTRUST`, `AXCRYPTO`

---

# 1. Purpose

AXDIFF is the canonical difference-analysis subsystem of Axiom.

Its purpose is to answer:

> **What exactly changed between artifact A and artifact B, and what does that change mean?**

It must support multiple comparison layers:

```text
SOURCE
  ↓
AST / SEMANTIC MODEL
  ↓
HIR / MIR / IR
  ↓
OBJECT
  ↓
BINARY
  ↓
ABI/API
  ↓
DEBUG
  ↓
CRASH
  ↓
REPLAY
  ↓
PROFILE
```

The central architectural principle is:

```text
byte difference ≠ semantic difference
semantic difference ≠ ABI difference
ABI difference ≠ behavioral difference
```

AXDIFF therefore provides multiple explicit diff levels rather than one generic binary comparison algorithm.

---

# 2. Core Architecture

```text
                  AXDIFF
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
   Structural     Semantic     Behavioral
      Diff           Diff          Diff
       │              │             │
       ├──────┬───────┼──────┬──────┤
       ▼      ▼       ▼      ▼      ▼
    Source   IR      ABI   Crash  Replay
       │      │       │      │      │
       └──────┴───────┴──────┴──────┘
                    │
                    ▼
               Diff IR
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      Human Report         AI Report
          │                   │
          └─────────┬─────────┘
                    ▼
                 .axdiff
```

---

# 3. Fundamental Rule

AXDIFF must preserve the distinction between:

```text id="9h7x9g"
IDENTICAL
CHANGED
ADDED
REMOVED
MOVED
RENAMED
UNKNOWN
UNAVAILABLE
INCOMPARABLE
```

It must never convert `UNKNOWN` into `UNCHANGED`.

---

# 4. Scope Boundary

### AXDIFF owns

- difference computation;
- comparison models;
- structural matching;
- semantic matching;
- ABI compatibility analysis;
- binary structural analysis;
- IR comparison;
- debug metadata comparison;
- crash comparison;
- replay comparison;
- profile comparison;
- diff artifact generation;
- compatibility reports.

### AXDIFF does not own

- compilation;
- optimization;
- linking;
- debugging;
- crash capture;
- replay execution;
- profiling;
- package versioning;
- source control.

---

# 5. Diff Modes

```text
DIFF_BYTE
DIFF_STRUCTURAL
DIFF_SOURCE
DIFF_SEMANTIC
DIFF_IR
DIFF_OBJECT
DIFF_BINARY
DIFF_ABI
DIFF_API
DIFF_DEBUG
DIFF_CRASH
DIFF_REPLAY
DIFF_PROFILE
DIFF_COMBINED
```

---

# 6. Comparison Context

```text
DiffContext {
    id
    generation
    mode
    left
    right
    target
    abi
    policy
    matcher
    result
}
```

---

# 7. Diff Input

```text
DiffInput {
    kind
    source?
    object?
    binary?
    ir?
    abi?
    debug?
    crash?
    replay?
    profile?
}
```

---

# 8. Comparison Identity

Every comparison records:

```text
left_identity
right_identity
comparison_policy
tool_version
schema_version
```

---

# 9. Artifact Identity

Artifact identity should use:

```text
content_hash
build_id
target
ABI
schema
```

where available.

---

# 10. Exact Equality

AXDIFF first performs cheap exact checks:

```text same content hash
same build ID
same canonical representation
```

before expensive semantic analysis.

---

# 11. Structural Equality

Two artifacts may have different serialization but identical logical structure.

AXDIFF canonicalizes them before comparison.

---

# 12. Canonicalization

Canonicalization may normalize:

```text ordering
padding
non-semantic metadata
timestamps
debug paths
build-local identifiers
```

according to the selected policy.

---

# 13. Never Normalize Semantics

Canonicalization must never remove information that can affect:

```text ABI
behavior
security
loading
memory layout
```

unless the policy explicitly says that dimension is excluded.

---

# 14. Diff Policy

```text DiffPolicy {
    ignore_debug
    ignore_build_metadata
    ignore_paths
    ignore_timestamps
    compare_abi
    compare_symbols
    compare_layout
    compare_code
    compare_semantics
    compare_behavior
}
```

---

# 15. Diff Result

```text
DiffResult {
    id
    status
    summary
    changes[]
    compatibility
    evidence
    diagnostics[]
}
```

---

# 16. Change Model

```text
DiffChange {
    id
    kind
    severity
    left_location?
    right_location?
    left_symbol?
    right_symbol?
    explanation
    evidence
}
```

---

# 17. Change Kinds

```text
ADDED
REMOVED
MODIFIED
MOVED
RENAMED
TYPE_CHANGED
SIGNATURE_CHANGED
LAYOUT_CHANGED
VALUE_CHANGED
CODE_CHANGED
METADATA_CHANGED
UNKNOWN
```

---

# 18. Change Severity

Severity is descriptive, not a universal judgment:

```text
INFO
NOTICE
COMPATIBILITY
BREAKING
SECURITY_RELEVANT
UNKNOWN
```

`BREAKING` must always refer to a defined compatibility contract.

---

# 19. Source Diff

AXDIFF supports ordinary textual diff but does not stop there.

---

# 20. Text Diff

Text diff operates on:

```text lines
tokens
UTF-8 code points
```

according to mode.

---

# 21. UTF-8

Axiom source is UTF-8.

Invalid UTF-8 is reported explicitly rather than silently converted.

---

# 22. Token Diff

Token-level diff distinguishes:

```text
identifier
keyword
literal
operator
punctuation
comment
whitespace
```

---

# 23. AST Diff

AXCOMPILER can provide semantic syntax trees to AXDIFF.

```text
AST A
  ↕
AST B
```

---

# 24. AST Matching

Nodes are matched by:

```text
kind
semantic identity
source structure
parent relationship
```

rather than line position alone.

---

# 25. Rename Detection

If:

```text
SymbolId A
```

maps confidently to:

```text
SymbolId B
```

AXDIFF may classify the change as:

```text RENAMED
```

instead of remove + add.

---

# 26. Move Detection

A symbol moved between modules can be identified as:

```text MOVED
```

when semantic identity proves continuity.

---

# 27. Semantic Diff

Semantic diff compares:

```text types
functions
traits
fields
enum variants
generic constraints
attributes
effects
ownership
visibility
```

---

# 28. Semantic Symbol Identity

Preferred identity:

```text SymbolId
```

from AXCOMPILER.

---

# 29. Stable Matching

If SymbolId changes across builds, AXDIFF can use a secondary structural identity:

```text module
qualified name
signature
semantic hash
```

but the result must identify that the match is inferred.

---

# 30. Evidence Levels

```text EXACT
STRONG
INFERRED
HEURISTIC
UNKNOWN
```

---

# 31. No Heuristic Certainty

A heuristic match must never be reported as exact identity.

---

# 32. Function Diff

Function comparison includes:

```text name
signature
generic parameters
constraints
receiver
effects
panic behavior
visibility
ABI
```

---

# 33. Struct Diff

Compare:

```text fields
field types
field order
alignment
packing
offsets
size
visibility
attributes
```

---

# 34. Struct ABI Change

A change to field layout can be marked ABI-relevant even if source-level APIs remain unchanged.

---

# 35. Enum Diff

Compare:

```text variants
discriminants
payload types
representation
layout
```

---

# 36. Union Diff

Compare:

```text members
alignment
size
tagging
representation
```

---

# 37. Trait Diff

Compare:

```text methods
associated types
constraints
required functions
default implementations
visibility
ABI contracts
```

---

# 38. Generic Diff

Compare:

```text type parameters
constraints
defaults
monomorphization-visible semantics
```

---

# 39. Method Receiver Diff

Changing:

```text receiver type
receiver ownership
receiver mutability
```

is explicitly represented.

---

# 40. Effect Diff

AXDIFF compares declared effects:

```text
allocation
blocking
IO
network
panic
unsafe
threading
```

when available.

---

# 41. Visibility Diff

```text PUBLIC → PRIVATE
PRIVATE → PUBLIC
```

is explicitly represented.

---

# 42. API Diff

AXDIFF generates API compatibility reports from AXDOC/compiler metadata.

---

# 43. API Surface

```text ApiDiff {
    added[]
    removed[]
    changed[]
    unchanged[]
}
```

---

# 44. API Compatibility Profiles

```text SOURCE_COMPATIBILITY
BINARY_COMPATIBILITY
ABI_COMPATIBILITY
BEHAVIORAL_COMPATIBILITY
```

These are separate dimensions.

---

# 45. Source Compatibility

Determines whether existing source can still compile under the new API.

AXDIFF does not itself compile the source; it compares semantic contracts.

---

# 46. Binary Compatibility

Determines whether an existing binary artifact can interact with the new artifact under the declared ABI contract.

---

# 47. ABI Compatibility

AXABI provides the canonical ABI rules.

AXDIFF compares:

```text calling convention
parameter representation
return representation
alignment
aggregate layout
TLS ABI
unwind ABI
symbol identity
```

---

# 48. ABI Fingerprint

Each public binary interface may expose an ABI fingerprint.

AXDIFF compares fingerprints before detailed analysis.

---

# 49. ABI Fingerprint Mismatch

A mismatch triggers detailed ABI comparison.

---

# 50. ABI Compatibility Result

```text
AbiCompatibility {
    status
    changed_symbols[]
    layout_changes[]
    calling_convention_changes[]
    representation_changes[]
}
```

---

# 51. Calling Convention Diff

Compare:

```text register allocation contract
stack layout
return registers
aggregate passing
variadic rules
```

---

# 52. Struct Passing Diff

A change from:

```text register aggregate
```

to:

```text indirect pointer
```

is ABI-visible.

---

# 53. Return ABI Diff

Return representation changes are ABI-visible even if source signatures appear equivalent.

---

# 54. Generic ABI

AXDIFF compares monomorphized exported instantiations where they are part of a binary interface.

---

# 55. Function Value ABI

Compare function-value representation including:

```text code pointer
environment pointer
calling convention
```

where applicable.

---

# 56. Slice ABI

Compare:

```text pointer
length
capacity
representation
```

or the canonical Axiom representation.

---

# 57. String ABI

Compare Axiom String/Str representations at ABI boundaries.

---

# 58. C ABI

`extern "C"` interfaces are compared according to the relevant platform C ABI.

---

# 59. ABI Compatibility Does Not Mean Behavior

AXDIFF must never report:

```text ABI compatible = behavior compatible
```

as a general conclusion.

---

# 60. Object Diff

AXOBJECT exposes canonical object structure.

AXDIFF compares:

```text sections
symbols
relocations
COMDAT
TLS
debug
metadata
```

---

# 61. Section Diff

Compare:

```text section type
flags
alignment
size
content hash
relocations
```

---

# 62. Symbol Diff

Compare:

```text symbol name
binding
visibility
section
value
size
type
ABI
```

---

# 63. Relocation Diff

Compare:

```text relocation type
offset
symbol
addend
expression
```

---

# 64. Relocation Compatibility

A relocation change is classified according to target ABI and linker semantics.

---

# 65. Archive Diff

Static libraries are compared at member level.

---

# 66. Archive Member Matching

Matching uses:

```text object identity
module identity
symbol set
content hash
```

---

# 67. Binary Diff

AXBINARY provides normalized binary structures.

AXDIFF compares:

```text headers
segments
sections
imports
exports
TLS
dynamic metadata
entry point
debug references
```

---

# 68. Binary Byte Diff

Raw byte diff remains available for:

```text patch analysis
reproducibility
exact artifact comparison
```

---

# 69. Binary Structural Diff

Structural comparison avoids false differences from:

```text file ordering
padding
non-semantic metadata
```

when policy allows.

---

# 70. Address Differences

Different ASLR-related or relocation-dependent addresses are normalized when they do not alter logical structure.

---

# 71. Layout Diff

AXDIFF compares:

```text virtual address
file offset
size
alignment
permissions
```

for loadable segments.

---

# 72. W^X Diff

A transition involving:

```text RWX
```

is explicitly reported as security-relevant metadata.

---

# 73. Import Diff

Compare:

```text imported module
symbol
ordinal
binding
```

---

# 74. Export Diff

Compare:

```text exported symbol
ordinal
visibility
ABI
```

---

# 75. TLS Diff

Compare:

```text TLS sections
alignment
size
initialization
ABI metadata
```

---

# 76. Entry Point Diff

Entry-point changes are explicitly reported.

---

# 77. PE64 Diff

AXDIFF understands:

```text PE headers
sections
imports
exports
relocations
TLS
debug directory
```

---

# 78. ELF64 Diff

AXDIFF understands:

```text ELF headers
program headers
sections
dynamic metadata
GOT/PLT
TLS
notes
```

---

# 79. Mach-O Diff

AXDIFF understands:

```text Mach headers
load commands
segments
symbols
dyld metadata
TLS
code-signing references
```

---

# 80. WASM Diff

Compare:

```text imports
exports
functions
tables
memories
globals
data
elements
custom sections
```

---

# 81. Code Diff

Machine code can be compared at multiple levels:

```text bytes
instructions
basic blocks
control flow
functions
```

---

# 82. Disassembly

AXDIFF may use AXASSEMBLER/architecture metadata to decode instructions.

It does not become the assembler.

---

# 83. Function Matching

Functions are matched using:

```text SymbolId
symbol name
signature
build metadata
semantic hash
```

---

# 84. Instruction Diff

Instruction changes are normalized where possible.

---

# 85. Register Allocation Noise

Equivalent compiler register allocation changes should be distinguishable from semantic control-flow changes.

---

# 86. Basic Block Diff

Compare:

```text operations
successors
predecessors
block identity
```

---

# 87. Control Flow Diff

```text CFG_A
   ↕
 CFG_B
```

identifies:

```text added branch
removed branch
changed condition
changed loop
changed call
```

---

# 88. Optimization Noise

Compiler optimization can produce large machine-code differences for small semantic changes.

AXDIFF therefore reports both:

```text semantic diff
machine diff
```

independently.

---

# 89. Code Size Diff

Reports:

```text total bytes
function bytes
section bytes
padding
```

---

# 90. Code Generation Regression

AXDIFF can compare compiler outputs from two compiler versions.

---

# 91. Compiler Diff

```text source
   ↓
compiler A → artifact A
compiler B → artifact B
   ↓
AXDIFF
```

---

# 92. IR Diff

Compare:

```text HIR
MIR
SSA
CFG
typed IR
```

where available.

---

# 93. IR Identity

Prefer stable compiler IR IDs.

---

# 94. Optimization Pass Diff

Compiler-generated metadata can expose:

```text pass name
input hash
output hash
```

for debugging compiler regressions.

---

# 95. IR Change Attribution

AXDIFF can report:

```text semantic change
vs
optimization-only change
```

when compiler metadata supports the distinction.

---

# 96. Debug Metadata Diff

Compare:

```text source mappings
line tables
inline trees
variable locations
type metadata
unwind info
```

---

# 97. Debug Compatibility

Debug metadata changes do not necessarily imply binary incompatibility.

They receive their own classification.

---

# 98. Symbol Artifact Diff

AXDIFF can compare external:

```text PDB-like
DWARF
dSYM-like
Axiom debug
```

artifacts through normalized metadata.

---

# 99. Crash Diff

AXCRASH artifacts can be compared.

---

# 100. Crash Identity

Compare:

```text executable build
module builds
fault class
exception/signal
fault address class
instruction symbol
stack
source location
task/thread state
```

---

# 101. Crash Similarity

AXDIFF can identify similar crash structures.

Similarity is not proof that two crashes have the same root cause.

---

# 102. Crash Diff

Example result model:

```text
CrashDiff {
    fault_changed
    instruction_changed
    stack_changes[]
    module_changes[]
    thread_changes[]
    task_changes[]
    metadata_changes[]
}
```

---

# 103. Stack Diff

Compare frames by:

```text ModuleId
FunctionId
source location
inline identity
```

rather than raw addresses.

---

# 104. Optimized Crash Diff

Missing/optimized-out frames remain explicit.

---

# 105. Replay Diff

AXREPLAY artifacts can be compared.

---

# 106. Replay Sequence Diff

Compare:

```text event kind
event order
thread
task
payload/hash
```

---

# 107. Replay Divergence Diff

Two replay sessions may show:

```text same prefix
different event
different downstream execution
```

---

# 108. First Divergence

AXDIFF identifies the earliest divergence that can be proven from available evidence.

---

# 109. Divergence Does Not Equal Cause

The report must state whether the difference is:

```text observed
derived
inferred
```

---

# 110. Checkpoint Diff

Compare replay checkpoints using:

```text state hashes
selected memory
task state
logical clocks
```

---

# 111. Profile Diff

AXPROFILER artifacts can be compared.

---

# 112. Profile Metrics

Compare:

```text CPU sample distribution
call tree
inclusive/exclusive time
allocation sites
wait time
task latency
lock contention
```

---

# 113. Statistical Profile Diff

Profile differences are statistical.

AXDIFF must retain:

```text sample counts
sampling mode
confidence/quality metadata
```

rather than presenting small sample fluctuations as exact execution changes.

---

# 114. Profile Build Matching

Profiles are normalized against:

```text build ID
module identity
symbol identity
```

---

# 115. Performance Regression

AXDIFF can identify changed measurements but does not automatically declare a performance regression unless the comparison policy defines a threshold.

---

# 116. Threshold Policy

```text absolute_delta
relative_delta
minimum_sample_count
confidence_requirement
```

---

# 117. Semantic Hash

Axiom compiler artifacts may expose semantic hashes.

---

# 118. Semantic Hash Purpose

Semantic hashes allow fast comparison of:

```text equivalent semantic structures
```

without requiring full tree traversal every time.

---

# 119. Hash Collision

Hash equality is an optimization.

For authoritative equivalence claims, AXDIFF may perform structural verification.

---

# 120. Content Hash

Content hashes remain exact for byte identity.

---

# 121. Diff Hash

Each canonical diff result receives:

```text diff_hash
```

derived from normalized comparison input and policy.

---

# 122. Deterministic Diff

Identical inputs + identical policy + identical AXDIFF version must produce canonical output.

---

# 123. Diff Artifact

`.axdiff` contains:

```text Header
InputIdentities
Target
ABI
Policy
Summary
Changes
Compatibility
Evidence
Diagnostics
Indexes
Integrity
```

---

# 124. Diff Artifact Header

```text
DiffHeader {
    magic
    schema_version
    diff_version
    mode
    session_id
}
```

---

# 125. Change Record

```text
ChangeRecord {
    id
    kind
    severity
    confidence
    left_ref?
    right_ref?
    semantic_identity?
    evidence[]
}
```

---

# 126. Evidence Record

```text
Evidence {
    source
    kind
    exact
    location
    hash?
}
```

---

# 127. Evidence Sources

```text COMPILER
AXABI
AXOBJECT
AXBINARY
AXDEBUGGER
AXCRASH
AXREPLAY
AXPROFILER
AXDOC
```

---

# 128. AI Diff Model

```text
AIDiffContext {
    summary
    changes[]
    compatibility
    evidence[]
    affected_symbols[]
    affected_files[]
    affected_modules[]
}
```

---

# 129. AI Evidence Rule

AI consumers must distinguish:

```text EXACT
INFERRED
HEURISTIC
UNKNOWN
```

---

# 130. AI Explanation

AI can explain a change but must not fabricate why a developer made it.

---

# 131. Source Navigation

AXIDE can navigate:

```text diff change
   ↓
left source
right source
```

---

# 132. Binary Navigation

Binary changes can navigate:

```text section
symbol
function
instruction
```

---

# 133. ABI Navigation

An ABI change can navigate to:

```text source declaration
ABI descriptor
object symbol
binary symbol
```

---

# 134. Crash Navigation

Crash changes can navigate to:

```text crash frame
source
debug symbol
replay cursor
```

---

# 135. Replay Navigation

Replay changes can navigate to:

```text sequence
task
thread
checkpoint
source
```

---

# 136. Profile Navigation

Profile changes can navigate to:

```text function
call tree node
source
```

---

# 137. IDE Diff View

AXIDE provides the orchestration layer.

AXDIFF remains headless.

---

# 138. Three-Way Diff

AXDIFF supports:

```text BASE
LEFT
RIGHT
```

for semantic merge analysis.

---

# 139. Three-Way Semantic Merge

The engine can identify:

```text LEFT_ONLY
RIGHT_ONLY
BOTH_SAME
BOTH_DIFFERENT
CONFLICT
```

---

# 140. Merge Boundary

AXDIFF detects and describes conflicts.

A future dedicated merge subsystem may perform source transformation.

AXDIFF does not silently rewrite source.

---

# 141. API Diff

```text diff_api()
diff_source()
diff_semantic()
diff_ir()
diff_object()
diff_binary()
diff_abi()
```

---

# 142. Debug/Crash/Replay API

```text diff_debug()
diff_crash()
diff_replay()
diff_profile()
```

---

# 143. Generic API

```text diff_create()
diff_add_left()
diff_add_right()
diff_set_policy()
diff_execute()
diff_result()
diff_validate()
```

---

# 144. Navigation API

```text diff_change_at()
diff_find_symbol()
diff_find_source()
diff_find_section()
diff_find_instruction()
```

---

# 145. Compatibility API

```text diff_check_source_compatibility()
diff_check_binary_compatibility()
diff_check_abi_compatibility()
diff_check_api_compatibility()
```

---

# 146. Artifact API

```text diff_write()
diff_read()
diff_validate_artifact()
diff_export_json()
diff_export_text()
```

---

# 147. Query API

```text diff_list_changes()
diff_filter_changes()
diff_summary()
diff_evidence()
diff_policy()
```

---

# 148. Security

AXDIFF operates on potentially untrusted artifacts.

---

# 149. Untrusted Input

Input may include malformed:

```text source
object
binary
debug
crash
replay
profile
```

---

# 150. Parser Isolation

Each artifact parser must enforce:

```text bounded sizes
integer overflow checks
recursion limits
allocation limits
```

---

# 151. No Execution

AXDIFF must never execute:

```text binaries
embedded code
foreign plugins
replay payloads
```

during comparison.

---

# 152. Replay Safety

Comparing `.axreplay` must remain analysis-only.

---

# 153. Crash Safety

Comparing `.axcrash` must not attempt to attach to the crashed process.

---

# 154. Binary Safety

Binary comparison is static analysis only.

---

# 155. Path Privacy

Source paths can be normalized or redacted according to policy.

---

# 156. Secret Filtering

Embedded metadata that resembles:

```text credentials
tokens
keys
environment values
```

must be subject to configured redaction.

---

# 157. Resource Limits

```text max_input_size
max_nodes
max_symbols
max_changes
max_recursion
max_runtime
```

---

# 158. Streaming

Large binary/object artifacts should support streaming structural comparison.

---

# 159. Memory Mapping

When safe and useful, AXDIFF may use memory mapping for large immutable artifacts.

---

# 160. Parallel Comparison

Independent modules/functions/sections may be compared in parallel.

---

# 161. Deterministic Parallelism

Parallel comparison must produce deterministic final ordering.

---

# 162. Change Ordering

Canonical ordering:

```text target
module
symbol
source location
change kind
change id
```

---

# 163. Incremental Diff

AXBUILD can reuse previous canonical hashes to avoid re-comparing unchanged artifacts.

---

# 164. Cache

```text DiffCache {
    left_hash
    right_hash
    policy_hash
    tool_version
    result_hash
}
```

---

# 165. Cache Invalidation

Changing any semantic comparison input invalidates the result.

---

# 166. Cross-Version Diff

AXDIFF can compare artifacts produced by different compiler versions if parsers understand both schemas.

---

# 167. Schema Compatibility

Unknown required metadata results in:

```text INCOMPARABLE
```

not fabricated compatibility.

---

# 168. Platform Diff

Cross-platform artifacts can be compared structurally.

ABI compatibility is only evaluated where the target contracts are compatible.

---

# 169. Architecture Diff

Comparing:

```text x86_64 ↔ AArch64
```

can produce structural/code differences but cannot claim binary compatibility.

---

# 170. Source-to-Binary Mapping

With compiler debug metadata:

```text source symbol
 ↓
IR
 ↓
machine function
 ↓
object
 ↓
binary
```

AXDIFF can connect corresponding changes.

---

# 171. Change Provenance

A change can be attributed to:

```text SOURCE_CHANGE
COMPILER_CHANGE
LINKER_CHANGE
TOOLCHAIN_CHANGE
BUILD_CONFIGURATION_CHANGE
UNKNOWN
```

only when evidence supports the attribution.

---

# 172. Compiler Regression Workflow

```text source unchanged
       │
       ├── compiler A
       │       ↓
       │    binary A
       │
       └── compiler B
               ↓
            binary B
               ↓
             AXDIFF
```

---

# 173. Reproducibility Workflow

```text build A
build B
   ↓
AXDIFF
   ↓
structural difference
   ↓
non-deterministic metadata identification
```

---

# 174. Reproducibility Policy

A policy can ignore known nondeterministic metadata such as timestamps when appropriate.

---

# 175. Security Diff

AXDIFF can compare security-relevant properties:

```text segment permissions
imports
exports
W^X
TLS
signing metadata
sandbox declarations
capabilities
```

---

# 176. Security Interpretation Boundary

AXDIFF reports concrete differences.

It does not decide whether a software release is “secure” overall.

---

# 177. Package Diff

AXPACKAGE can expose package contents to AXDIFF.

AXDIFF compares:

```text package metadata
modules
artifacts
dependencies
ABI declarations
```

without owning package resolution.

---

# 178. Documentation Diff

AXDOC provides semantic documentation nodes.

AXDIFF can identify:

```text API documentation added
documentation removed
signature documentation changed
examples changed
```

---

# 179. Documentation/API Consistency

AXDIFF can identify a changed public API whose documentation did not change.

This is a consistency signal, not proof of incomplete documentation.

---

# 180. Test Diff

AXTEST results may be compared externally through normalized test artifacts.

---

# 181. Test Coverage Diff

If coverage metadata is available:

```text covered symbols
uncovered symbols
coverage changes
```

can be compared.

---

# 182. Behavioral Diff Boundary

AXDIFF cannot prove arbitrary program behavioral equivalence.

It can compare recorded behavior from AXREPLAY and test observations.

---

# 183. Formal Equivalence Boundary

Formal semantic equivalence remains a separate compiler/verification capability.

AXDIFF may consume formal proof results but does not become a theorem prover.

---

# 184. Unknown Semantics

If semantic information is unavailable:

```text UNKNOWN
```

must be emitted.

---

# 185. Incomparable Inputs

Examples:

```text incompatible schema
corrupt artifact
missing target metadata
unsupported architecture
```

produce:

```text INCOMPARABLE
```

---

# 186. Diff Confidence

```text EXACT
HIGH
MEDIUM
LOW
UNKNOWN
```

is permitted only as evidence confidence, not as a general software quality score.

---

# 187. Change Count

Summary may report:

```text added
removed
modified
moved
unknown
```

---

# 188. No Overall Ranking

AXDIFF must never collapse differences into a single “better/worse” score.

---

# 189. ABI Report Example

Conceptual:

```text
ABI compatibility:
  function foo: unchanged
  function bar: parameter ABI changed
  struct User: size 32 → 40
  enum State: discriminant representation unchanged
```

---

# 190. Binary Report Example

```text
PE64:
  .text: +184 bytes
  .rdata: unchanged
  import: +1
  export: unchanged
  entry point: unchanged
```

---

# 191. Replay Report Example

```text
Replay:
  common prefix: 12,481 events
  first divergence: sequence 12,482
  expected: TASK_RESUME
  actual: TIMER_FIRE
```

---

# 192. Crash Report Example

```text
Crash:
  fault class: unchanged
  module: changed
  top function: changed
  common stack prefix: 7 frames
  replay correlation: available
```

---

# 193. Profile Report Example

```text
Profile:
  samples: 2,000,000 → 2,000,000
  function X: 12.4% → 17.1%
  allocation site Y: unchanged
```

---

# 194. Diff Serialization

`.axdiff` must support:

```text binary canonical form
JSON export
text report
```

---

# 195. Binary Diff Schema

`AXDIFF_SCHEMA_1` is canonical.

---

# 196. Schema Evolution

Optional fields can be added without invalidating old readers.

Required semantic changes require a new schema version.

---

# 197. ABI Evolution

`AXDIFF_ABI_1` defines runtime APIs independently from `.axdiff` serialization.

---

# 198. Deterministic Output

The same inputs and policy produce byte-identical canonical `.axdiff` output.

---

# 199. Artifact Integrity

`.axdiff` includes:

```text checksum
content hash
input identities
policy hash
```

---

# 200. Optional Signature

Signing is delegated to:

```text AXTRUST
AXCRYPTO
```

---

# 201. Remote Diff

AXDIFF can compare artifacts located remotely through authenticated artifact services.

The remote storage/transport layer is outside AXDIFF.

---

# 202. Remote Security

No unauthenticated artifact source is trusted automatically.

---

# 203. API ABI

Canonical runtime interface:

```text
AXDIFF_ABI_1
```

---

# 204. Core APIs

```text
diff_create()
diff_destroy()

diff_set_mode()
diff_set_policy()
diff_set_target()
diff_set_abi()

diff_add_left()
diff_add_right()

diff_execute()
diff_cancel()

diff_status()
diff_result()
diff_summary()

diff_list_changes()
diff_get_change()
diff_get_evidence()

diff_validate()
```

---

# 205. Source APIs

```text
diff_source()
diff_tokens()
diff_ast()
diff_semantic()
```

---

# 206. Compiler APIs

```text
diff_hir()
diff_mir()
diff_ir()
diff_codegen()
```

---

# 207. Binary APIs

```text
diff_object()
diff_archive()
diff_binary()
diff_sections()
diff_symbols()
diff_relocations()
```

---

# 208. ABI APIs

```text
diff_api()
diff_abi()
diff_struct_layout()
diff_function_abi()
diff_export_surface()
```

---

# 209. Diagnostic APIs

```text
diff_debug()
diff_crash()
diff_replay()
diff_profile()
```

---

# 210. Artifact APIs

```text
diff_write()
diff_read()
diff_validate_artifact()
diff_export_json()
diff_export_text()
```

---

# 211. Navigation APIs

```text
diff_find_symbol()
diff_find_source()
diff_find_section()
diff_find_instruction()
diff_find_event()
```

---

# 212. Cache APIs

```text
diff_cache_lookup()
diff_cache_store()
diff_cache_invalidate()
```

---

# 213. Error Model

```text
DIFF_INVALID_CONTEXT
DIFF_INVALID_INPUT
DIFF_UNSUPPORTED_FORMAT
DIFF_SCHEMA_MISMATCH
DIFF_TARGET_MISMATCH
DIFF_ABI_MISMATCH
DIFF_CORRUPT_ARTIFACT
DIFF_RESOURCE_LIMIT
DIFF_CANCELLED
DIFF_INCOMPARABLE
DIFF_METADATA_MISSING
DIFF_MAPPING_FAILED
DIFF_CACHE_ERROR
```

---

# 214. AXTEST Conformance

AXTEST must verify:

- byte diff;
- token diff;
- AST diff;
- semantic diff;
- symbol matching;
- rename detection;
- move detection;
- struct layout comparison;
- enum/union comparison;
- generic comparison;
- API comparison;
- ABI comparison;
- object comparison;
- relocation comparison;
- PE64 comparison;
- ELF64 comparison;
- Mach-O comparison;
- WASM comparison;
- machine-code comparison;
- IR comparison;
- debug metadata comparison;
- crash comparison;
- replay comparison;
- profile comparison;
- three-way comparison;
- canonical serialization;
- incremental cache;
- malformed artifact handling;
- resource limits;
- privacy filtering;
- deterministic parallel execution.

---

# 215. Golden Tests

Canonical `.axdiff` results are stored as versioned golden artifacts.

---

# 216. Property Tests

Properties include:

```text diff(A,A) = EMPTY
```

and:

```text canonicalize(A) == canonicalize(A)
```

---

# 217. Symmetry

Where semantics permit:

```text diff(A,B)
```

must correspond predictably to:

```text diff(B,A)
```

with left/right roles reversed.

---

# 218. Identity Test

For byte-identical artifacts:

```text exact equality
```

must be reported.

---

# 219. Unknown Test

Missing metadata must produce:

```text UNKNOWN / INCOMPARABLE
```

rather than false equality.

---

# 220. ABI Test

Changing a public struct field layout must be detected as an ABI-relevant difference.

---

# 221. Compiler Regression Test

Equivalent source compiled by two compiler versions should expose:

```text semantic equivalence
```

separately from:

```text machine-code difference
```

when semantic metadata is available.

---

# 222. Replay Test

Two replay artifacts with one changed event must identify the first differing event.

---

# 223. Crash Test

Two crash artifacts with identical symbolized stacks but different addresses should be structurally comparable.

---

# 224. Profile Test

Profile comparison must preserve sample-count and measurement-mode metadata.

---

# 225. Fuzzing

Fuzz all parsers and canonicalizers.

Particularly:

```text PE64
ELF64
Mach-O
WASM
DWARF/CodeView-like metadata
.axcrash
.axreplay
.axprof
.axdiff
```

---

# 226. Differential Testing

Where an external parser exists, it may be used in AXTEST as a differential oracle.

AXDIFF itself remains native.

---

# 227. Performance Targets

For unchanged canonical artifacts:

```text hash path → near O(1) after metadata lookup
```

For large structural artifacts:

```text approximately O(N + M)
```

for matched structures where possible.

---

# 228. Large Binary Diff

AXDIFF must avoid loading multiple multi-gigabyte artifacts fully into RAM when streaming/mmap comparison is possible.

---

# 229. Parallelism

Independent modules and sections may be compared concurrently.

---

# 230. Memory Bound

All expensive operations have configurable resource limits.

---

# 231. Incremental IDE Diff

AXIDE can request:

```text changed symbol only
changed function only
changed source region only
```

instead of recomputing the entire project.

---

# 232. Editor Integration

AXCODEEDITOR displays:

```text added lines
removed lines
modified ranges
semantic changes
ABI annotations
```

but AXDIFF remains presentation-independent.

---

# 233. AI Integration

AI receives structured semantic changes rather than raw binary noise whenever possible.

---

# 234. AI Context Example

```text
Changed symbol:
  foo

Signature:
  old: foo(Str) -> Result<i32,E>
  new: foo(Str, Options) -> Result<i32,E>

ABI:
  parameter added

Evidence:
  compiler semantic metadata
  AXABI comparison
```

---

# 235. Provenance

Every generated explanation can point back to:

```text source range
symbol
IR node
object record
binary section
replay event
crash frame
profile node
```

---

# 236. No Hidden Mutation

AXDIFF is read-only.

It never modifies source, binaries, crash files, replay files, or project state during analysis.

---

# 237. Security-Relevant Diff

AXDIFF may expose concrete security-related changes such as:

```text new executable import
new writable segment
permission change
capability declaration change
```

but does not independently certify security.

---

# 238. Reproducible Builds

AXBUILD may use AXDIFF as a verification stage:

```text Build A
Build B
   ↓
AXDIFF
   ↓
canonical comparison
```

---

# 239. Package Upgrade Analysis

AXPACKAGE can invoke:

```text AXDIFF ABI comparison
AXDIFF API comparison
```

before accepting an upgrade.

---

# 240. Final Architecture

```text
                       AXDIFF
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
     Source            Binary             Runtime
        │                 │                  │
   AST/IR/API       Object/PE/ELF       Crash/Replay
        │                 │                  │
        └─────────────────┼──────────────────┘
                          │
                    Diff IR
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
          Compatibility           Evidence
              │                       │
              └───────────┬───────────┘
                          ▼
                       .axdiff
                          │
                  ┌───────┴────────┐
                  ▼                ▼
                 AXIDE             AI
```

---

# 241. AXDIFF Invariants

### DIFF-INV-01
Every comparison has a unique context identity.

### DIFF-INV-02
Both inputs are identified before comparison.

### DIFF-INV-03
Target identity is explicit.

### DIFF-INV-04
ABI identity is explicit where relevant.

### DIFF-INV-05
Byte equality is distinguished from semantic equality.

### DIFF-INV-06
Unknown information is never treated as unchanged.

### DIFF-INV-07
Incomparable artifacts are explicitly reported.

### DIFF-INV-08
Canonicalization never silently changes semantics.

### DIFF-INV-09
Semantic identity uses compiler-provided identity when available.

### DIFF-INV-10
Heuristic matching is marked as inferred.

### DIFF-INV-11
Renames are distinguishable from remove/add.

### DIFF-INV-12
Moves are distinguishable from remove/add.

### DIFF-INV-13
Struct layout changes are explicitly detected.

### DIFF-INV-14
Enum representation changes are explicitly detected.

### DIFF-INV-15
Union representation changes are explicitly detected.

### DIFF-INV-16
Function ABI changes are explicitly detected.

### DIFF-INV-17
Generic ABI changes are explicitly detected where exported.

### DIFF-INV-18
C ABI boundaries use the appropriate target ABI.

### DIFF-INV-19
Object symbols are compared structurally.

### DIFF-INV-20
Relocations are compared structurally.

### DIFF-INV-21
PE64 structure is supported.

### DIFF-INV-22
ELF64 structure is supported.

### DIFF-INV-23
Mach-O structure is supported.

### DIFF-INV-24
WASM structure is supported.

### DIFF-INV-25
Machine-code differences are distinguished from semantic differences.

### DIFF-INV-26
IR differences can be analyzed independently of machine code.

### DIFF-INV-27
Debug metadata differences are separately classified.

### DIFF-INV-28
Crash differences preserve evidence provenance.

### DIFF-INV-29
Replay differences preserve event ordering.

### DIFF-INV-30
Profile differences preserve statistical metadata.

### DIFF-INV-31
First replay divergence is distinguished from root-cause inference.

### DIFF-INV-32
No binary, replay, or crash artifact is executed during comparison.

### DIFF-INV-33
All parsers enforce resource limits.

### DIFF-INV-34
Canonical diff serialization is deterministic.

### DIFF-INV-35
Parallel comparison produces deterministic ordering.

### DIFF-INV-36
Diff cache keys include comparison policy.

### DIFF-INV-37
Sensitive metadata can be redacted.

### DIFF-INV-38
AI-facing evidence preserves provenance.

### DIFF-INV-39
AXTEST can deterministically verify diff behavior.

### DIFF-INV-40
Every conforming implementation satisfies all mandatory AXDIFF invariants.

---

# 242. Definition of Done

AXDIFF 5.0 is complete when:

- `AXDIFF_ABI_1` is frozen.
- `AXDIFF_SCHEMA_1` is frozen.
- generic diff context exists.
- source diff works.
- token diff works.
- AST diff works.
- semantic diff works.
- SymbolId matching works.
- rename detection works.
- move detection works.
- API diff works.
- source compatibility analysis works.
- binary compatibility analysis works.
- ABI analysis works.
- struct layout comparison works.
- enum/union comparison works.
- generic ABI comparison works.
- object diff works.
- archive diff works.
- relocation diff works.
- PE64 diff works.
- ELF64 diff works.
- Mach-O diff works.
- WASM diff works.
- machine-code diff works.
- CFG/function diff works.
- HIR/MIR/IR diff works where metadata exists.
- debug metadata diff works.
- crash diff works.
- replay diff works.
- profile diff works.
- three-way diff works.
- deterministic canonical serialization works.
- `.axdiff` read/write works.
- incremental diff cache works.
- large artifact streaming works.
- parallel comparison works deterministically.
- resource limits work.
- security isolation works.
- privacy filtering works.
- AXIDE integration works.
- AXCODEEDITOR integration works.
- AXDOC integration works.
- AXTEST integration works.
- AI semantic context works with provenance.
- all `DIFF-INV-01..40` pass.
- self-hosted Axiom can compare its own compiler/toolchain artifacts.

**BOOTSTRAP-794 — AXDIFF 5.0 is frozen.**

---

# Next task

## BOOTSTRAP-795 — AXMERGE

**Native Axiom Semantic Merge Engine, Three-Way Source/AST/IR/API/ABI Merge, Conflict Detection, Symbol Identity Preservation, Struct/Enum/Trait/Generic Merge, Build Artifact Merge, Dependency-Aware Merge Planning, Deterministic Merge Graph, Conflict Model, Merge Resolution API & Merge ABI 5.0**