Tiếp tục với **BOOTSTRAP-624**, tập trung vào scripting/automation nhưng giữ nguyên nguyên tắc: **scripting là tầng ứng dụng tùy chọn, không làm phình language core và không biến Axiom thành một VM-first language**.

:::writing{variant="document" id="38154" title="BOOTSTRAP-624 — Native Application Scripting, Embedded Language Boundary, Automation, Macro, Expression Runtime & Sandboxed Dynamic Behavior 5.0"}
# BOOTSTRAP-624 — Native Application Scripting, Embedded Language Boundary, Automation, Macro, Expression Runtime & Sandboxed Dynamic Behavior 5.0

**Status:** SPECIFIED  
**Layer:** Application Automation / Dynamic Behavior  
**Depends on:** BOOTSTRAP-600 → 623

---

# 1. Purpose

BOOTSTRAP-624 defines the optional dynamic-behavior layer for Axiom applications:

- scripting;
- automation;
- macros;
- command sequences;
- expressions;
- user-defined actions;
- embedded DSLs;
- application automation;
- configuration expressions;
- extension scripting;
- dynamic rules;
- sandboxed computation;
- script debugging;
- script persistence;
- script state;
- script package distribution.

The architecture must **not** require scripting for ordinary Axiom applications.

---

# 2. Primary Design Principle

Axiom has three different execution categories:

```text
Native Axiom
    ↓
compiled native machine code

Dynamic Axiom behavior
    ↓
optional interpreter / bytecode / JIT

External automation
    ↓
IPC / command protocol
```

These are intentionally separate.

---

# 3. Non-Goals

BOOTSTRAP-624 does not require:

- a mandatory scripting VM;
- JavaScript compatibility;
- Python compatibility;
- Lua compatibility;
- garbage collection;
- dynamic typing throughout Axiom;
- runtime compilation of arbitrary native code;
- unrestricted `eval`;
- reflection over all application internals.

---

# 4. Architecture

```text id="f7tq3z"
Application
    │
    ├── Native Axiom
    │
    ├── 623 Extensions
    │
    └── 624 Automation
          │
          ├── Expression Engine
          ├── Script Engine
          ├── Macro Engine
          ├── Command Engine
          ├── DSL Runtime
          └── Sandboxed Runtime
```

---

# 5. Three Dynamic Execution Levels

## Level 1 — Expression

Small deterministic expressions.

Example:

```text id="xqz9k1"
width * 0.5 + padding
```

---

## Level 2 — Automation

Structured command/action sequences.

```text id="4x6f4j"
open_document(path)
select_all()
transform(scale = 0.5)
save()
```

---

## Level 3 — Script

General-purpose dynamic program execution.

```text id="d4x6w2"
for document in workspace.documents {
    process(document)
}
```

---

# 6. Why Three Levels

Most application automation does not require a complete programming language runtime.

Therefore:

```text id="k1t6nq"
Expression
    ↓
smallest runtime

Automation
    ↓
command interpreter

Script
    ↓
full optional runtime
```

This minimizes startup cost and binary size.

---

# 7. Script Engine Abstraction

Core interface:

```text id="qz4e3r"
ScriptEngine
```

provides:

```text
compile
load
execute
pause
resume
cancel
inspect
dispose
```

---

# 8. Script Engine Is a Provider

The runtime does not mandate one scripting implementation.

Providers can be:

```text id="8r2f3m"
AxiomScript
ExpressionEngine
ExternalScriptProvider
WASMProvider
ApplicationSpecificDSL
```

---

# 9. Native AxiomScript

The preferred built-in scripting language is a restricted dynamic subset of Axiom.

It should reuse Axiom syntax where practical.

---

# 10. Syntax Compatibility

Example:

```text id="b0k4d8"
let x = 10

for item in items {
    print(item)
}
```

This reduces the number of languages developers and AI systems must learn.

---

# 11. Script ≠ Native Axiom

The same syntax does not imply identical execution semantics.

Script mode may impose:

- runtime checks;
- sandbox restrictions;
- dynamic values;
- resource limits;
- deterministic execution.

---

# 12. Script File

Suggested extension:

```text id="n9w5t7"
.axs
```

---

# 13. Script Metadata

Optional:

```text id="7zq3ma"
.axscript
```

contains:

```text
engine
version
permissions
entry
dependencies
resources
state_schema
```

---

# 14. Script Package

Scripts may be packaged using 613.

```text id="4b3c8n"
AXPK
 ├── manifest
 ├── script
 ├── schemas
 ├── resources
 └── signature
```

---

# 15. Script Identity

Every persistent script has:

```text id="1f8c6r"
ScriptId
Version
PublisherId
Hash
```

---

# 16. Script Compilation

A script may be:

```text id="d5x9jp"
source
→ parsed AST
→ validated
→ bytecode/IR
→ executed
```

---

# 17. Cached Compilation

Compiled script artifacts may be cached through 613.

---

# 18. Cache Key

Cache key contains:

```text id="w9q2za"
source_hash
engine_version
compiler_version
target
policy
feature_set
```

---

# 19. Invalid Cache

Any mismatch invalidates the cached executable representation.

---

# 20. Bytecode

AxiomScript may use a compact bytecode.

The bytecode is an implementation detail.

---

# 21. Bytecode Is Not Native ABI

Axiom bytecode must never be treated as a native module ABI.

---

# 22. Bytecode Verification

Before execution:

```text id="7s1d9q"
format
version
stack behavior
control flow
resource limits
capabilities
```

are validated.

---

# 23. Bytecode Security

Malformed bytecode must not:

- escape the sandbox;
- access arbitrary memory;
- forge capabilities;
- bypass host API checks.

---

# 24. Dynamic Values

The scripting layer may provide:

```text id="5y7k2c"
DynamicValue
```

for script interoperability.

---

# 25. DynamicValue

Possible variants:

```text id="f6q0ma"
Null
Bool
Integer
Float
String
Bytes
Array
Map
Struct
Handle
Function
Future
Error
```

---

# 26. DynamicValue Is Not Core Type

`DynamicValue` belongs to the scripting layer.

The native language remains statically typed.

---

# 27. Dynamic Type Checking

Invalid dynamic operations produce runtime errors rather than memory corruption.

---

# 28. Handles

Scripts interact with host resources through opaque handles.

---

# 29. No Raw Pointer Exposure

Scripts must never receive arbitrary native pointers.

---

# 30. Host Object Model

A script can see only registered host objects.

---

# 31. Script API Registry

```text id="v2m6nx"
ScriptApiRegistry
```

contains explicitly exposed APIs.

---

# 32. API Exposure

Example:

```text id="r6c4jw"
@script_api
struct DocumentApi {
    fn open(...)
    fn save(...)
}
```

---

# 33. No Automatic Reflection

Ordinary native structs are not automatically script-visible.

---

# 34. Explicit Exposure

Only declared APIs become script APIs.

---

# 35. API Metadata

Each exposed function includes:

```text id="2d9n8s"
name
arguments
return_type
permissions
threading
async
errors
```

---

# 36. Capability Integration

Script permissions map directly to 603 capabilities.

---

# 37. Example

```text id="g8v4k1"
@script_api(
    requires = ["filesystem.read"]
)
fn read_text(path: Path) -> Result<String>
```

---

# 38. Capability Attenuation

A script can receive a capability narrower than the host application.

---

# 39. No Capability Forging

Scripts cannot construct privileged capabilities from ordinary values.

---

# 40. Script Context

Every execution has:

```text id="7j3q8m"
ScriptContext
```

containing:

```text script_id
instance_id
capabilities
resource_budget
cancellation
deadline
environment
```

---

# 41. Script Isolation

Each script execution receives an explicit context.

---

# 42. Global State

Global mutable state is disabled by default.

---

# 43. Script State

Scripts may have explicit state objects.

---

# 44. Persistent Script State

State uses:

- 600;
- 611;
- 612.

---

# 45. Script State Schema

Persistent state requires a versioned schema.

---

# 46. Script Migration

State migrations are explicit and transactional.

---

# 47. No Arbitrary State Serialization

Executable code is never serialized as persistent state.

---

# 48. Script Resource Budget

A script can be limited by:

```text id="4z2n6q"
CPU
memory
execution time
instructions
tasks
handles
IPC
network
storage
GPU
```

---

# 49. Resource Integration

606 is authoritative for runtime resource accounting.

---

# 50. Instruction Budget

The interpreter may count executed instructions.

---

# 51. Time Budget

A script can have:

```text id="m3x7w8"
deadline
maximum_runtime
```

---

# 52. Cooperative Cancellation

Scripts must periodically observe cancellation.

---

# 53. Forced Cancellation

The engine may terminate execution at safe VM boundaries.

---

# 54. Native Calls

A script may call native APIs only through registered bindings.

---

# 55. Native Call Boundary

```text id="e8n2q4"
Script
  ↓
Binding
  ↓
Capability Check
  ↓
Native API
```

---

# 56. Binding Validation

Bindings validate:

- argument count;
- type;
- range;
- ownership;
- capability;
- thread affinity.

---

# 57. Error Model

Native errors become script errors.

---

# 58. Panic Boundary

Native panics do not cross into script execution.

---

# 59. Script Exception

Script errors are structured values:

```text id="x6q9pa"
ScriptError {
    code
    message
    source
    stack
    cause
}
```

---

# 60. Error Propagation

Async script calls propagate errors through futures/promises.

---

# 61. Stack Traces

Script stack traces use script source locations.

---

# 62. Source Maps

Compiled script artifacts preserve:

```text id="4g6n8w"
source_file
line
column
instruction_range
```

---

# 63. Debugging

Script engine supports:

```text id="p7z1w4"
breakpoint
step
continue
inspect
watch
stack
locals
```

when debugging is enabled.

---

# 64. Debug Capability

Attaching a debugger requires explicit 603 debug capability.

---

# 65. Production Mode

Production scripts may omit debug metadata.

---

# 66. Script Inspector

Runtime can expose:

```text id="9j2f0k"
script state
tasks
memory
resource usage
capabilities
```

without exposing secrets.

---

# 67. Macro Engine

Macros are recorded or authored command sequences.

---

# 68. Macro Representation

```text id="5g7x1z"
Macro {
    id
    version
    commands[]
}
```

---

# 69. Macro vs Script

Macro:

```text deterministic command sequence
```

Script:

```text programmable logic
```

---

# 70. Macro Recording

Applications can record user commands from 620.

---

# 71. Recorded Macro

Example:

```text id="0j5m2c"
OpenDocument
SelectAll
SetProperty
SaveDocument
```

---

# 72. Macro Sanitization

Recorded macros must not capture:

- passwords;
- secrets;
- private capability tokens;
- sensitive clipboard data.

---

# 73. Macro Parameters

Macros can contain typed parameters.

---

# 74. Macro Reuse

A macro can be exposed as a command.

---

# 75. Macro Versioning

Macros are versioned independently from application state.

---

# 76. Macro Execution

Macros execute through 620 commands rather than directly manipulating private application state.

---

# 77. Undo Integration

Macro execution can be represented as one undo transaction.

---

# 78. Macro Failure

Failure can:

```text id="f1v8n2"
rollback
stop
continue
```

according to macro policy.

---

# 79. Automation Engine

Automation combines commands, conditions and values.

---

# 80. Automation Graph

```text id="j5k9r0"
Trigger
   ↓
Condition
   ↓
Action
   ↓
Condition
   ↓
Action
```

---

# 81. Trigger Types

Examples:

```text id="8z3m6v"
ApplicationStart
ApplicationExit
DocumentOpen
DocumentSave
CommandExecuted
Timer
FileChanged
NetworkEvent
DeviceEvent
UserEvent
```

---

# 82. Trigger Security

Triggers require the capability appropriate to their source.

---

# 83. Timer Automation

Timers use 607.

---

# 84. File Automation

File watchers use 611.

---

# 85. Network Automation

Network events use 609.

---

# 86. Device Automation

Device events use 614.

---

# 87. GUI Automation

GUI events use 618/619.

---

# 88. Workspace Automation

Workspace events use 622.

---

# 89. Automation State

Each automation instance has explicit state.

---

# 90. Automation Persistence

Automation definitions can persist through 612/613.

---

# 91. Automation Scheduling

Long-running automation uses 607 tasks.

---

# 92. Automation Limits

606 controls:

- concurrent executions;
- memory;
- CPU;
- queues;
- event rate.

---

# 93. Event Storm Protection

Automation engine must apply bounded queues and rate limits.

---

# 94. Recursion Protection

An automation triggered by its own action must not recursively execute without an explicit policy.

---

# 95. Cycle Detection

Automation graphs are validated for cycles.

---

# 96. Maximum Depth

Execution depth is bounded.

---

# 97. Command Palette Integration

624 may provide dynamically registered commands through 620/622.

---

# 98. Dynamic Commands

Scripts can register commands if explicitly granted registration capability.

---

# 99. Command Lifetime

Commands are owned by the script/module instance.

---

# 100. Cleanup

When the script/module is unloaded:

```text id="v5m2w7"
commands unregister
```

---

# 101. Script Routes

624 may register routes through 622.

---

# 102. Route Security

A route does not grant capability.

---

# 103. Route Parameters

Route parameters become typed `DynamicValue` or explicitly generated schema types.

---

# 104. Deep Links

Scripts can respond to application deep links only if permitted.

---

# 105. Document Automation

Scripts may manipulate documents through 621 APIs.

---

# 106. Transactional Document Operations

Script changes can be grouped into document transactions.

---

# 107. Undo

Script operations can integrate with 620/621 undo/redo.

---

# 108. Save

Scripts cannot bypass document save policies.

---

# 109. Workspace Automation

Scripts can:

- open documents;
- rearrange views;
- execute commands;
- modify workspace state.

All actions remain subject to 622 policy.

---

# 110. UI Automation

Scripts may operate semantic UI objects.

---

# 111. UI Object Access

Prefer:

```text id="8f4c2a"
semantic_id
control_id
command_id
```

over coordinates.

---

# 112. Coordinate Automation

Raw coordinate automation is an optional compatibility feature.

---

# 113. Coordinate Security

Coordinate automation must not be treated as equivalent to semantic application APIs.

---

# 114. Clipboard Automation

Clipboard access uses 619/603.

---

# 115. File Dialog Automation

Scripts may invoke file dialogs but cannot silently bypass capability restrictions.

---

# 116. Expression Engine

Expression engine supports:

```text id="2j9m5c"
literals
arithmetic
comparison
boolean logic
conditional
property access
function calls
collections
```

---

# 117. Expression Purity

Expressions are pure by default.

---

# 118. Side Effects

Side-effecting functions must be explicitly marked.

---

# 119. Deterministic Expressions

Pure expressions can be evaluated deterministically.

---

# 120. Expression Context

Expressions may access an explicit variable environment.

---

# 121. Expression Compilation

Expressions can compile to compact bytecode or native code where safe.

---

# 122. Native Expression Compilation

Optional JIT may compile pure expressions.

---

# 123. JIT Capability

JIT requires 603 dynamic-code capability.

---

# 124. Interpreter Fallback

Interpreter remains available where JIT is unavailable.

---

# 125. WASM

WASM hosts may execute scripts through a WASM-compatible runtime boundary.

---

# 126. Embedded DSL

Applications may define domain-specific syntax.

---

# 127. DSL Parser

DSL parser produces:

```text id="6v3q8k"
AST
```

validated against a schema.

---

# 128. DSL Execution

DSL execution can target:

```text id="w8k1q5"
commands
expressions
native APIs
bytecode
```

---

# 129. DSL Sandbox

A DSL receives only explicitly registered functions.

---

# 130. No Arbitrary Native Escape

A DSL cannot invoke arbitrary native symbols.

---

# 131. Configuration Expressions

601 may optionally use the expression engine.

---

# 132. Configuration Safety

Configuration expressions cannot execute arbitrary shell commands.

---

# 133. Environment Access

Environment access is explicit and capability-controlled.

---

# 134. Shell Execution

Shell execution is not part of the expression engine.

---

# 135. Process Automation

Process creation uses 603/605.

---

# 136. Shell Provider

If an application wants shell automation, it must expose an explicit provider.

---

# 137. Shell Sandboxing

The provider controls:

- executable;
- arguments;
- environment;
- working directory;
- timeout;
- resources.

---

# 138. No Shell String Expansion

The core automation API should prefer typed argument arrays over shell command strings.

---

# 139. External Automation

Other processes can automate an Axiom application through 604 IPC.

---

# 140. Automation Protocol

Optional service:

```text id="r5w8x2"
ApplicationAutomation
```

---

# 141. IPC Commands

Commands use 612 schemas.

---

# 142. Remote Automation Security

Remote automation requires explicit authentication and capability authorization.

---

# 143. Local Automation

Local IPC still requires authentication/authorization where the platform does not provide sufficient isolation.

---

# 144. Script-to-IPC

Scripts can call IPC services only through declared APIs.

---

# 145. Script Networking

Scripts may use network APIs only when granted capability.

---

# 146. Script Storage

Scripts may use storage APIs only through capability-scoped handles.

---

# 147. Script Device Access

Device access follows 614/603.

---

# 148. Script GPU

GPU access is through 615/614 interfaces and resource quotas.

---

# 149. Script Media

Media automation uses 616 APIs.

---

# 150. Script Text

Text processing uses 617 APIs.

---

# 151. Script GUI

GUI manipulation uses 619 APIs.

---

# 152. Script Navigation

Navigation uses 622 APIs.

---

# 153. Script Extensions

A 623 plugin may expose its own script APIs.

---

# 154. Plugin Script API

A plugin declares:

```text id="x8z1k4"
@script_api
```

functions.

---

# 155. Plugin Unload

When a plugin unloads, its script bindings become invalid.

---

# 156. Script Handle Generation

Bindings carry module generation IDs.

---

# 157. Stale Binding

Calling a stale binding produces a deterministic error.

---

# 158. Script Module Dependency

Scripts can depend on 623 modules.

---

# 159. Script Dependency Resolution

Uses the same package/dependency system when appropriate.

---

# 160. Script Package

Script packages may include:

```text id="p3v6z9"
script
manifest
schemas
resources
dependencies
signature
```

---

# 161. Script Trust

Script package trust is separate from host application trust.

---

# 162. Unsigned Scripts

Unsigned scripts can be permitted only by explicit local/development policy.

---

# 163. Production Policy

Production applications may disable unsigned dynamic scripts entirely.

---

# 164. Script Permissions

Manifest declares required permissions.

---

# 165. Permission Review

Application can inspect requested permissions before activation.

---

# 166. Least Privilege

Scripts receive only permissions necessary for their declared operation.

---

# 167. Script Profiles

Recommended profiles:

```text id="1c5v7x"
Pure
Automation
Application
Privileged
```

---

# 168. Pure Profile

No external side effects.

---

# 169. Automation Profile

Can access application commands.

---

# 170. Application Profile

Can use explicitly granted application services.

---

# 171. Privileged Profile

Requires explicit administrator/application policy.

---

# 172. No Ambient Privileged Script

There is no equivalent of:

```text id="j8n3x4"
eval_as_root()
```

---

# 173. Script Environment

Environment contains only declared variables.

---

# 174. Deterministic Mode

For testing/reproducibility:

```text id="w4m7z2"
clock
random
filesystem
network
device
```

are replaced by deterministic providers where configured.

---

# 175. Randomness

Scripts use an explicit random provider.

---

# 176. Clock

Scripts use an explicit clock abstraction.

---

# 177. Time Travel Testing

Test runtime can provide a deterministic virtual clock.

---

# 178. Network Simulation

Test runtime can provide fake network services.

---

# 179. Storage Simulation

Test runtime can provide fake storage.

---

# 180. UI Simulation

Test runtime can provide semantic UI automation.

---

# 181. Script Testing

Scripts should be testable without launching the complete application.

---

# 182. Script Unit Test

Example:

```text id="z2n7m6"
@test
fn calculate_total() {
    ...
}
```

---

# 183. Script Integration Test

Tests execute against a deterministic application host.

---

# 184. Security Tests

Test:

- capability denial;
- sandbox escape attempts;
- malformed bytecode;
- invalid handles;
- resource exhaustion;
- stale module bindings.

---

# 185. Fuzzing

Fuzz:

- parser;
- bytecode;
- expressions;
- DynamicValue;
- script API bindings;
- macro files;
- automation graphs.

---

# 186. Resource Exhaustion

Engine must terminate or throttle scripts exceeding limits.

---

# 187. Infinite Loop

Instruction/time budgets detect uncooperative scripts.

---

# 188. Native Blocking

A script calling a blocking native operation must either:

- use an async API;
- execute through a blocking worker;
- be rejected by policy.

---

# 189. UI Blocking

Long-running scripts must not block the UI executor.

---

# 190. Async Script

Scripts can use:

```text id="j7v4q1"
async
await
```

if the engine supports async execution.

---

# 191. Async Lowering

Async scripts compile to runtime state machines.

---

# 192. No Hidden Thread Per Script

Scripts do not automatically create one OS thread each.

---

# 193. Script Executor

Scripts run on 607 executors.

---

# 194. Script Concurrency

Multiple scripts may execute concurrently under 606 limits.

---

# 195. Script Synchronization

Scripts can use safe runtime synchronization primitives.

---

# 196. Shared Script State

Shared mutable state requires explicit synchronization.

---

# 197. Script Channels

Scripts may use channels exposed by 608.

---

# 198. Script IPC

IPC operations are asynchronous by default where appropriate.

---

# 199. Cancellation Tree

Script tasks belong to a structured cancellation tree.

---

# 200. Script Shutdown

Application shutdown cancels active scripts according to policy.

---

# 201. Graceful Shutdown

Scripts receive cancellation before forced termination.

---

# 202. Shutdown Deadline

Script cleanup is bounded by application shutdown deadlines.

---

# 203. Script Persistence

Active execution is not persisted as executable VM state.

---

# 204. Recovery

After restart:

```text id="0m5r8v"
script definition
+
persistent state
```

may be restored and execution restarted from a declared checkpoint.

---

# 205. No Arbitrary VM Snapshot

The system does not require serializing arbitrary interpreter stack/register state.

---

# 206. Automation Checkpoints

Long automation workflows can explicitly declare checkpoints.

---

# 207. Workflow State

Checkpoint contains only schema-defined data.

---

# 208. Workflow Resume

Execution resumes from a stable workflow node.

---

# 209. Exactly-Once

624 does not promise distributed exactly-once execution.

---

# 210. Idempotency

Automation authors should use idempotent commands where retries are possible.

---

# 211. Retry Policy

Actions may define:

```text id="k3v8z6"
Never
Once
Bounded
UntilDeadline
```

---

# 212. Compensation

Automation can provide compensation actions.

---

# 213. Transaction Boundary

Actions that support 620/621 transactions can participate in transactional undo.

---

# 214. External Side Effects

External side effects such as network requests cannot automatically be rolled back.

---

# 215. Audit

Privileged automation actions are recorded through 602.

---

# 216. Secret Redaction

Script logs automatically redact `Secret<T>` values.

---

# 217. Script Diagnostics

Metrics include:

```text id="q8x2m4"
execution_count
failure_count
cpu_time
memory
queue_time
await_time
cancel_count
```

---

# 218. Script Trace

602 spans may identify:

```text id="s3v9j1"
script_id
execution_id
workflow_id
```

---

# 219. Script Crash

A script failure must not crash the host process.

---

# 220. Native Extension Failure

If the script calls a faulty in-process plugin, 623's native crash semantics still apply.

---

# 221. Script Engine Failure

A script engine provider should be isolated if it is not trusted.

---

# 222. Out-of-Process Script Engine

624 may execute scripts through a 623/604 isolated provider.

---

# 223. Engine Restart

Out-of-process script engine can restart without application restart.

---

# 224. Script Engine Version

Engine version is part of the script cache key.

---

# 225. Script Compatibility

Scripts declare minimum engine version.

---

# 226. Engine Migration

Breaking script language changes require a new language/runtime version.

---

# 227. Language Profiles

AxiomScript may define profiles:

```text id="z7q4m1"
Expression
Automation
Script
Full
```

---

# 228. Restricted Grammar

Expression profile parses only the expression subset.

---

# 229. Parser Security

Parser rejects:

- malformed syntax;
- excessive nesting;
- pathological token streams.

---

# 230. Parser Limits

Limits include:

```text id="v4m8q2"
max_source_bytes
max_tokens
max_nesting
max_ast_nodes
```

---

# 231. Bytecode Limits

Limits include:

```text id="c2j7x9"
max_code_size
max_constants
max_call_depth
max_stack_depth
```

---

# 232. DynamicValue Limits

Limits include:

```text id="n8v3q5"
max_string
max_array
max_map
max_nesting
```

---

# 233. Deserialization

612 decoding limits apply to script packages/state.

---

# 234. Macro File Security

Macros are treated as untrusted data until validated.

---

# 235. Automation Graph Validation

Graph validator detects:

- missing commands;
- invalid parameters;
- cycles;
- unsupported triggers;
- permission violations.

---

# 236. Static Validation

Scripts can be validated without execution.

---

# 237. Capability Analysis

Compiler/tooling reports required capabilities.

---

# 238. Example Capability Report

```text id="j6q3m8"
Script: build_assets.axs

Requires:
    filesystem.read
    filesystem.write
    process.execute

Optional:
    network.connect
```

---

# 239. AI-Friendly Metadata

624 generates:

```text id="p7m2x4"
.axscriptmeta
```

containing:

- APIs;
- types;
- capabilities;
- commands;
- events;
- schemas;
- examples.

---

# 240. AI Tooling

AI agents can inspect the script API without parsing private native implementation details.

---

# 241. Generated Bindings

Script bindings may be generated from Axiom API metadata.

---

# 242. Binding Stability

Generated bindings carry API fingerprints.

---

# 243. API Evolution

Bindings are regenerated when API fingerprints change.

---

# 244. No Reflection Requirement

Generated bindings can be completely static.

---

# 245. Performance

Common expression evaluation should be low overhead.

---

# 246. Constant Folding

Pure expressions may be folded at compile time.

---

# 247. Inline Host Functions

Safe pure host functions may be inlined into compiled expressions.

---

# 248. JIT

Optional JIT may optimize hot script code.

---

# 249. JIT Isolation

JIT memory must follow 603 W^X/dynamic-code policy.

---

# 250. AOT Script Compilation

Scripts can optionally be precompiled into package artifacts.

---

# 251. AOT vs Runtime

AOT improves startup while preserving script-level semantics.

---

# 252. Native Compilation

A trusted script may optionally compile to native code through the normal Axiom compiler pipeline.

This is an explicit build/deployment operation, not implicit `eval`.

---

# 253. Native Compilation Security

Generated native code receives the capabilities of its declared package/module, not unrestricted host privileges.

---

# 254. Script Engine Removal

If no scripting is used, the entire engine can be removed from the application binary.

---

# 255. Profile Matrix

```text
Application
│
├── No scripting
├── Expressions only
├── Automation only
├── AxiomScript
├── External script provider
└── Full scripting + JIT
```

---

# 256. Architecture Invariants

1. Scripting is optional.
2. Native Axiom remains the primary performance model.
3. Dynamic values are not core language values.
4. Raw native pointers never enter scripts.
5. Capabilities are explicit.
6. Script permissions are separate from package trust.
7. Script execution is resource-bounded.
8. Scripts cannot crash the host through ordinary script errors.
9. Native extension failures retain 623 semantics.
10. Script state is schema-defined.
11. Arbitrary VM execution state is not persisted.
12. Script APIs are explicitly registered.
13. Reflection is not mandatory.
14. Macro execution uses application commands.
15. Automation uses typed actions.
16. Side effects are explicit.
17. Pure expressions are deterministic where configured.
18. Dynamic code cannot silently elevate privileges.
19. Shell execution is not implicit.
20. Network access is not implicit.
21. Filesystem access is not implicit.
22. Device access is not implicit.
23. JIT is optional.
24. JIT requires dynamic-code policy.
25. Interpreter fallback is available where required.
26. Scripts use 607 scheduling.
27. Script resources use 606 accounting.
28. Script synchronization uses 608.
29. Script persistence uses 600/612/611.
30. Script packages use 613.
31. Script signatures use 610.
32. Script security uses 603.
33. Script process isolation uses 604/605.
34. Script UI uses 619.
35. Script navigation uses 622.
36. Script document operations use 621.
37. Script commands use 620.
38. Script bindings are generation-safe.
39. Unloaded plugins invalidate their script APIs.
40. Automation cycles are detected.
41. Automation event queues are bounded.
42. Infinite scripts are bounded by resource limits.
43. Macro recording does not capture secrets.
44. Persistent scripts cannot contain executable serialized state.
45. Dynamic behavior can be completely dead-stripped.

---

# 257. Acceptance Criteria

### Engine
1. Expression engine.
2. Automation engine.
3. Macro engine.
4. Script engine.
5. Engine provider interface.
6. AxiomScript provider.
7. External provider boundary.
8. WASM provider boundary.
9. engine versioning.
10. engine capability metadata.

### Language
11. parser.
12. AST.
13. DynamicValue.
14. bytecode.
15. bytecode validation.
16. source mapping.
17. error model.
18. stack traces.
19. async.
20. cancellation.

### Security
21. explicit API exposure.
22. capability checks.
23. capability attenuation.
24. no raw pointers.
25. no capability forging.
26. resource limits.
27. parser limits.
28. bytecode limits.
29. dynamic-value limits.
30. JIT policy.

### Automation
31. command execution.
32. macro recording.
33. macro parameters.
34. undo integration.
35. triggers.
36. conditions.
37. actions.
38. graph validation.
39. cycle detection.
40. retry policy.

### Persistence
41. script identity.
42. package metadata.
43. state schema.
44. state migration.
45. checkpoint.
46. workflow resume.
47. configuration integration.
48. package integration.
49. cache integration.
50. deterministic cache keys.

### Application Integration
51. commands.
52. documents.
53. workspace.
54. navigation.
55. GUI.
56. text.
57. media.
58. graphics.
59. device.
60. IPC.

### Runtime
61. executor integration.
62. task scopes.
63. structured cancellation.
64. resource accounting.
65. async I/O.
66. event queue.
67. bounded backpressure.
68. UI-thread protection.
69. blocking-operation isolation.
70. graceful shutdown.

### Debugging
71. breakpoints.
72. stepping.
73. locals.
74. stack.
75. watch.
76. execution metrics.
77. tracing.
78. failure diagnostics.
79. capability diagnostics.
80. deterministic test host.

### Testing
81. parser fuzzing.
82. bytecode fuzzing.
83. DynamicValue fuzzing.
84. API-binding fuzzing.
85. macro fuzzing.
86. automation graph fuzzing.
87. capability tests.
88. resource exhaustion tests.
89. cancellation tests.
90. stale-binding tests.

### Performance
91. constant folding.
92. expression caching.
93. bytecode caching.
94. optional JIT.
95. optional AOT.
96. lazy engine initialization.
97. no mandatory VM.
98. no mandatory GC.
99. no hidden thread per script.
100. dead stripping.

---

# 258. Reference API

```text id="3x8m1q"
struct ScriptEngine {
    fn compile(
        source: StringView,
        options: ScriptCompileOptions
    ) -> Result<ScriptArtifact>

    fn execute(
        artifact: ScriptArtifact,
        context: ScriptContext
    ) -> Result<ScriptExecution>

    fn cancel(
        execution: ScriptExecutionHandle
    ) -> Result<void>

    fn inspect(
        execution: ScriptExecutionHandle
    ) -> Result<ScriptInspection>
}
```

---

# 259. Script Context

```text id="n4v7k2"
struct ScriptContext {
    script: ScriptId
    capabilities: CapabilitySet
    resources: ResourceBudget
    cancellation: CancelToken
    deadline: Deadline
    variables: VariableScope
}
```

---

# 260. Macro API

```text id="q8m3x5"
struct Macro {
    id: MacroId
    version: Version
    commands: Array<CommandInvocation>
}

fn execute_macro(
    macro: Macro,
    context: AutomationContext
) -> Result<MacroResult>
```

---

# 261. Automation API

```text id="v6k2p9"
struct Automation {
    id: AutomationId
    triggers: Array<Trigger>
    graph: AutomationGraph
    policy: AutomationPolicy
}
```

---

# 262. Expression API

```text id="r3x7m1"
fn evaluate(
    expression: Expression,
    context: ExpressionContext
) -> Result<DynamicValue>
```

---

# 263. Extension Script API

```text id="z5n8q4"
@script_api(
    requires = ["document.read"]
)
fn document_title(
    document: DocumentHandle
) -> Result<String>
```

---

# 264. Example

```text id="k7m2x8"
script "batch_resize" {

    for document in workspace.documents() {

        if document.is_image() {

            document.begin_transaction()

            document.resize(
                width = document.width() / 2,
                height = document.height() / 2
            )

            document.commit()
            document.save()
        }
    }
}
```

The actual execution path is:

```text
Script
  ↓
Script Parser
  ↓
Validation
  ↓
Capability Analysis
  ↓
Bytecode
  ↓
Script Context
  ↓
607 Executor
  ↓
620/621 APIs
```

---

# 265. Final Architecture

```text id="n0p7x4"
                         AXIOM APPLICATION
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
           NATIVE            623 EXTENSIONS      624
          Axiom Code              │               │
                                  │        ┌──────┼─────────┐
                                  │        ▼      ▼         ▼
                                  │    Expression Macro   Script
                                  │        │      │         │
                                  └────────┼──────┼─────────┘
                                           ▼
                                   SCRIPT API BOUNDARY
                                           │
                                  Capability Validation
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                            620          621          622
                          Commands     Documents    Workspace
                              │            │            │
                              └────────────┼────────────┘
                                           ▼
                              607 / 608 / 606 / 603
```

---

# 266. Design Conclusion

624 deliberately makes dynamic behavior a **layer**, not a fundamental property of every Axiom program.

The resulting model is:

```text
Axiom native code
    ↓
maximum performance

Axiom expression
    ↓
small dynamic behavior

Axiom automation
    ↓
structured application control

AxiomScript
    ↓
general dynamic behavior

623 extension
    ↓
native application integration

IPC
    ↓
strong process isolation
```

This allows a tiny native application to contain almost none of the scripting infrastructure while a large desktop application can expose a powerful automation environment.

Most importantly, **native Axiom does not pay for scripting merely because scripting exists somewhere in the ecosystem**.

---

# 267. Task Completion

**BOOTSTRAP-624 — COMPLETE**

**Next queued task: BOOTSTRAP-625 — Native Application Plugin Marketplace/Repository Boundary, Package Registry, Dependency Resolution Service, Update Channel, Rollback & Application Distribution Runtime 5.0**
:::