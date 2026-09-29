# BOOTSTRAP-549 — AI SECURITY ARCHITECTURE REVIEW, SECURE-BY-CONSTRUCTION ANALYSIS, TRUST BOUNDARY COMPILER & SECURITY POLICY VERIFICATION

**Status: COMPLETED / LOCKED**

## 549.1. Mục tiêu

`548` trả lời:

> Hệ thống hiện đang phơi nhiễm ở đâu?

`549` trả lời:

> Ngay từ lúc viết/biên dịch code, model, tool và workflow, Axiom có thể chứng minh hoặc phát hiện những đường đi nguy hiểm nào?

Mục tiêu là đưa **security semantics vào compiler**, nhưng **không biến Axiom thành một ngôn ngữ có security checker nặng như một hệ thống type/lifetime checker thứ hai**.

Nguyên tắc:

```text id="9c0x1k"
Security Analysis
    ≠
Type Checking
    ≠
Ownership Checking
    ≠
Static Analysis tổng quát
```

Security analysis sử dụng kết quả của `430`, `445`, `478`, `479`, `490`, `545`, `546`, `548`, thay vì tái xây dựng toàn bộ semantic engine.

---

# 549.2. Secure-by-construction

Axiom ưu tiên:

```text id="xg7j2n"
Unsafe Design
      ↓
Prevent by Type / Capability / API
```

thay vì:

```text id="q0j2aa"
Everything allowed
      ↓
Scan later
```

Ví dụ API:

```text id="h7v4p3"
fn open_file(path: Path) -> Result<File, IoError>
```

không tự động có filesystem authority.

Caller phải có capability phù hợp:

```text id="k5p8y1"
FileCapability
```

Như vậy compiler có thể kiểm tra authority flow.

---

# 549.3. Security semantic model

Compiler tạo:

```text id="9t0d1c"
SecuritySemanticModel {
    trust_boundaries
    capabilities
    principals
    resources
    data_classes
    taint_sources
    taint_sinks
    sanitizers
    authority_flows
    security_contracts
    policy_bindings
    unsafe_boundaries
}
```

Model này là phần mở rộng của semantic database `446`.

Không cần runtime nếu analysis chỉ dùng compile-time.

---

# 549.4. Trust Boundary

Trust boundary là nơi mức độ tin cậy thay đổi.

Ví dụ:

```text id="b6x8m0"
User Input
    ↓
Application
    ↓
Database
```

hoặc:

```text id="9f1v7a"
Agent
    ↓
Tool
    ↓
External API
```

hoặc:

```text id="q4w6s2"
Axiom
    ↓
FFI
    ↓
Foreign Code
```

Compiler biểu diễn:

```text id="m0p9x2"
TrustDomain
TrustBoundary
BoundaryCrossing
```

---

# 549.5. Trust domain

Canonical:

```text id="r3z8k1"
TrustDomain {
    id
    name
    trust_level
    authority
    data_policy
}
```

Trust level không phải universal numeric score.

Có thể dùng semantic classes:

```text id="u2a5v9"
Trusted
Internal
External
Untrusted
Unknown
```

---

# 549.6. Boundary crossing

```text id="p4k1d7"
BoundaryCrossing {
    from_domain
    to_domain
    operation
    data
    authority
    validation?
    sanitization?
}
```

Mỗi crossing có source span.

Ví dụ:

```text id="m8y2s4"
HTTP request
    → parser
    → application state
```

là boundary crossing.

---

# 549.7. Taint model

Axiom hỗ trợ data-flow security:

```text id="c9q4n6"
Source
  ↓
Tainted Data
  ↓
Transform
  ↓
Sanitizer
  ↓
Sink
```

Taint state:

```text id="f2x8a1"
Clean
Tainted
Sanitized
Sensitive
Secret
Unknown
```

Có thể có nhiều labels đồng thời.

---

# 549.8. Taint source

Ví dụ:

```text id="d7r5v2"
network_input()
file_input()
user_input()
environment_variable()
ipc_input()
plugin_input()
tool_result()
model_output()
dataset_record()
foreign_function()
```

API/library metadata khai báo source.

---

# 549.9. Taint sink

Ví dụ:

```text id="v8k3p5"
execute_process()
execute_sql()
write_file()
load_library()
send_network()
render_html()
invoke_tool()
change_policy()
grant_capability()
```

Sink metadata phải khai báo security requirements.

---

# 549.10. Sanitizer

Sanitizer chuyển data từ một security state sang state an toàn hơn **chỉ khi contract chứng minh điều đó**.

Ví dụ:

```text id="q3m8x6"
validate_filename(path)
```

có thể đảm bảo:

```text id="j6p1v4"
PathTraversalSafe
```

nhưng compiler không tự coi tên hàm `validate_*` là sanitizer.

Sanitizer phải được khai báo bằng contract/metadata.

---

# 549.11. Security labels

Axiom hỗ trợ label tùy policy:

```text id="k1y6w8"
Public
Internal
Confidential
Restricted
Secret
Untrusted
Validated
```

Labels có thể đến từ:

- type;
- attribute;
- API metadata;
- data governance;
- compile-time policy.

---

# 549.12. Label propagation

Ví dụ:

```text id="z5p8q2"
secret : Secret<String>

copy(secret)
    → Secret<String>

format(secret)
    → Secret<String>

hash(secret)
    → policy-dependent
```

Không được giả định mọi transformation loại bỏ sensitivity.

---

# 549.13. Secret flow

Compiler có thể kiểm tra:

```text id="a8m4t1"
Secret
  ↓
logger
```

hoặc:

```text id="y2c6k9"
Secret
  ↓
network
```

Nếu policy cấm, diagnostic:

```text id="j7n5s3"
SECURITY-E549001
secret data reaches prohibited sink
```

---

# 549.14. Secret sink policy

Ví dụ:

```text id="b2f7x0"
sink logger {
    requires data != Secret
}
```

Hoặc metadata:

```text id="n8c3v5"
@security_sink(
    accepts = [Public, Internal]
)
```

Compiler kiểm tra statically khi có đủ evidence.

---

# 549.15. Unknown

Nếu compiler không biết flow:

```text id="s6y1q8"
Unknown
```

không được biến thành:

```text id="w3r9k4"
Safe
```

Có thể yêu cầu:

- explicit sanitizer;
- runtime validation;
- unsafe boundary;
- policy exception.

---

# 549.16. Security proof states

Chuẩn hóa:

```text id="d2m8p7"
Proven
Violated
RuntimeChecked
Unknown
Assumed
```

`Assumed` phải explicit.

Không được coi:

```text Unknown == Proven
```

---

# 549.17. Security constraint IR

Compiler tạo security constraints:

```text id="p9k3x6"
SecurityConstraintIR {
    source
    flow
    required_property
    proof_state
    policy
    evidence
}
```

Ví dụ:

```text id="x4m7c1"
Secret(data)
    ↓
NetworkSend(endpoint)
    requires:
        endpoint.policy allows Secret
```

---

# 549.18. Capability-flow analysis

Authority cũng là data-flow.

```text id="n5v2z8"
Principal
   ↓
Capability
   ↓
Function
   ↓
Resource
```

Compiler phải theo dõi capability use.

---

# 549.19. Capability possession

Một function có thể yêu cầu:

```text id="r7k4m2"
fn deploy(
    cap: DeploymentCapability,
    artifact: Artifact
)
```

Việc truyền `cap` thể hiện authority.

Không truyền capability:

```text id="s8q1y6"
→ no authority
```

trừ khi API/platform contract định nghĩa authority khác.

---

# 549.20. Authority amplification

Nguy hiểm:

```text id="m1z5p9"
LowAuthority
    ↓
function
    ↓
HighAuthority
```

Compiler phải phát hiện khi một function có khả năng tạo/obtain authority lớn hơn authority được cấp mà không có explicit trusted boundary.

Diagnostic:

```text id="c4x8n2"
SECURITY-E549020
possible authority amplification
```

---

# 549.21. Authority attenuation

Ngược lại:

```text id="q8m3v6"
FullFileCapability
       ↓
ReadOnlyFileCapability
```

là attenuation.

Compiler/semantic metadata có thể chứng minh capability subset.

---

# 549.22. Confused deputy

Mô hình:

```text id="z1p6k4"
LowPrivilegeCaller
        ↓
PrivilegedService
        ↓
Resource chosen by caller
```

Nếu service sử dụng authority của chính nó để thực hiện arbitrary operation cho caller, compiler/security analyzer phải có khả năng cảnh báo.

Fix:

```text id="u5r9x2"
capability passed explicitly
```

hoặc:

```text id="a7k3m8"
resource authorization tied to caller
```

---

# 549.23. Ambient authority

Axiom coi các API kiểu:

```text id="g2v8n5"
global_file_write()
global_network_send()
global_process_spawn()
```

là security-sensitive.

Không cấm chúng ở language core, nhưng security metadata phải có thể đánh dấu:

```text id="j4x7p1"
@ambient_authority
```

Project policy có thể:

- allow;
- warn;
- deny.

---

# 549.24. Unsafe boundary

`unsafe` từ `445` được đưa vào security graph.

```text id="p6m2z9"
Safe
  ↓
unsafe
  ↓
raw pointer / syscall / asm / FFI
```

Compiler biết:

```text id="n3q8v4"
where unsafe enters
where unsafe propagates
which safe APIs encapsulate it
```

---

# 549.25. Unsafe propagation

Không phải mọi caller của unsafe function đều tự động trở thành unsafe.

Nếu wrapper chứng minh invariant:

```text id="f8k1y5"
unsafe implementation
      ↓
safe wrapper
      ↓
validated API
```

thì boundary có thể được đóng.

Nếu không:

```text id="w6p3r9"
unsafe requirement propagates
```

---

# 549.26. FFI security

`451` cung cấp:

```text id="c2m7x8"
@owned
@borrowed
@consumes
@returns_owned
```

549 bổ sung:

```text id="v9n4p1"
@security_source
@security_sink
@trust_boundary
@requires_capability
@taints
@sanitizes
```

FFI không được mặc định là safe source/sink semantics nếu metadata chưa có.

---

# 549.27. Native syscall analysis

Ví dụ:

```text id="k8x2m6"
raw_syscall(...)
```

là security boundary.

Compiler có thể yêu cầu:

```text id="z4p7q1"
unsafe
```

và security policy có thể yêu cầu:

```text id="r3m9v5"
@approved_syscall
```

---

# 549.28. Process execution

API:

```text id="u7k2n8"
spawn_process(command)
```

có thể khai báo:

```text id="f5q9x3"
security effects:
    ProcessExecution
    ExternalEffect
```

Static analysis kiểm tra:

- command source;
- argument provenance;
- capability;
- sandbox;
- policy.

---

# 549.29. Path security

Compiler/library metadata có thể phân biệt:

```text id="p1v6m8"
RawPath
ValidatedPath
SandboxedPath
```

Không nhất thiết tạo nhiều built-in types; có thể dùng semantic wrappers trong standard library.

---

# 549.30. SQL/data-query security

Ví dụ:

```text id="c7x4n2"
SQLQuery::raw(user_input)
```

có thể tạo taint violation.

Trong khi:

```text id="m9p3k8"
SQLQuery::parameterized(user_input)
```

có sanitizer contract tương ứng.

Compiler không cần hiểu toàn bộ SQL grammar.

---

# 549.31. Network security flow

```text id="d4z8q1"
External Input
      ↓
Parser
      ↓
Validated Request
      ↓
Internal API
```

Boundary metadata cho phép analyzer biết validation nào đã thực hiện.

---

# 549.32. Tool security

Tool ABI `513` tích hợp:

```text id="x6k2p9"
Tool Input
Tool Output
Tool Effects
Tool Capabilities
Tool Trust
```

Tool result mặc định:

```text id="v8m4r1"
untrusted data
```

Tool output không tự động trở thành instruction.

---

# 549.33. Agent security

Agent `511`:

```text id="n2q7x5"
Model Output
    ↓
Agent Decision
    ↓
Tool Call
```

Security analyzer phải phân biệt:

```text id="a5m8k3"
model-generated value
model-generated instruction
trusted policy
tool result
user input
```

Model output không có authority mặc định.

---

# 549.34. Workflow security

`540/541` cung cấp effect graph.

Ví dụ:

```text id="y7p2c9"
Model
 ↓
Tool
 ↓
Write Database
```

Analyzer có thể xác định:

```text id="g4m8x1"
AI-derived data reaches irreversible sink
```

và yêu cầu:

```text id="r6n3v5"
validation
approval
transaction
```

tùy policy.

---

# 549.35. Human approval

Security policy có thể yêu cầu:

```text id="k3x7p2"
@requires_approval(
    action = "deploy",
    scope = "production"
)
```

Compiler kiểm tra workflow có approval node hay không.

---

# 549.36. Policy-to-code binding

Policy `545` có thể bind vào code:

```text id="b8q4m1"
Policy
   ↓
Security Contract
   ↓
Function / Tool / Workflow
```

Ví dụ:

```text id="f2z9x6"
policy:
    only principal.role == "deployer"
    may call deploy()
```

Compiler không hardcode role.

Policy compiler chịu trách nhiệm tạo semantic rule.

---

# 549.37. Compile-time policy verification

Pipeline:

```text id="v6m3p8"
Source
 ↓
Semantic Model
 ↓
Security Constraints
 ↓
Policy Resolution
 ↓
Proof / Violation / Unknown
```

Policy có thể:

```text id="j1x7n4"
allow
deny
require runtime check
require approval
```

---

# 549.38. Runtime security checks

Nếu compile-time không chứng minh được:

```text id="q5k8r2"
Unknown
```

policy có thể yêu cầu runtime check.

Ví dụ:

```text id="d9m4x7"
if check_capability(cap) {
    execute()
}
```

Compiler ghi:

```text id="p3v6n1"
proof_state = RuntimeChecked
```

---

# 549.39. Security contracts

Tích hợp `479`:

```text id="z8k2m5"
@requires(...)
@ensures(...)
@security_requires(...)
@security_ensures(...)
```

Security contracts vẫn là contracts, không phải một type system riêng.

---

# 549.40. Security effect system

Function metadata có thể có:

```text id="x3p7v9"
SecurityEffects {
    reads_untrusted
    writes_sensitive
    accesses_network
    accesses_filesystem
    spawns_process
    invokes_tool
    changes_capability
    crosses_trust_boundary
}
```

Effects được propagate theo call graph.

---

# 549.41. Effect propagation

```text id="m8q4z1"
A → B → C
```

Nếu C:

```text id="y5p2x7"
writes_secret
```

thì A có thể được đánh dấu:

```text id="r9k3v6"
security_effect = writes_secret
```

trừ khi boundary/contract chặn flow.

---

# 549.42. Effect polymorphism

Generic function:

```text id="u4m8k2"
fn process<T>(value: T)
```

không nên bị gán một security effect cố định nếu effect phụ thuộc T.

Có thể dùng:

```text id="c6x1p9"
effect parameter
```

hoặc instantiate-time effect inference.

---

# 549.43. Security metadata for libraries

Package metadata có thể khai báo:

```text id="q7n3v5"
security_sources
security_sinks
sanitizers
trust_boundaries
capability_requirements
security_effects
```

Consumer không cần source code để thực hiện nhiều analysis.

Đây là điểm nối trực tiếp với `446/447`.

---

# 549.44. Binary security metadata

Native package có thể mang:

```text id="k1x8m4"
security metadata
ABI metadata
capability metadata
effect metadata
provenance
```

Metadata có thể được strip nếu policy cho phép.

---

# 549.45. Security metadata trust

Metadata từ package ngoài là:

```text id="v5p2q9"
untrusted until verified
```

Không được tin metadata chỉ vì package compile thành công.

Có thể yêu cầu:

- signed metadata;
- verified package;
- trusted registry;
- explicit policy.

---

# 549.46. Interprocedural analysis

Security flow cần:

```text id="d8m3x7"
function
→ caller
→ callee
→ closure
→ callback
→ trait dispatch
→ function pointer
```

Nhưng dynamic dispatch có thể khiến kết quả:

```text id="f2k9p4"
Unknown
```

thay vì false proof.

---

# 549.47. Dynamic dispatch

Nếu:

```text id="s7x1n5"
dyn Tool
```

compiler biết tất cả implementations:

```text id="j4m8q2"
analyze closed-world set
```

Nếu open-world:

```text id="z6p3v9"
conservative effect summary
```

---

# 549.48. Function pointers

Function pointer có thể làm mất precision:

```text id="n9q2x5"
fnptr → ?
```

Compiler có thể:

- resolve exact target;
- maintain target set;
- use effect summary;
- return Unknown.

Không được tự assume safe.

---

# 549.49. Generic security analysis

Generic function được phân tích:

```text id="m3x7k1"
generic semantic template
```

và specialize khi cần.

Không duplicate analysis unnecessarily.

---

# 549.50. Security-aware optimization

Security analysis không được phá semantics của optimizer.

Ví dụ compiler không được:

```text id="a8q4m6"
eliminate validation
```

chỉ vì optimizer coi nó redundant nếu validation có security effect.

Security checks chỉ được loại bỏ khi:

```text id="y2p9v5"
security property proven elsewhere
```

và proof được giữ trong metadata.

---

# 549.51. Constant-time security

Axiom hỗ trợ annotation:

```text id="f6m3x8"
@constant_time
fn compare_secret(...)
```

Compiler có thể:

- reject data-dependent branches;
- warn;
- use specialized implementation;
- report unknown.

Không tuyên bố rằng constant-time đã được chứng minh tuyệt đối trên mọi CPU.

---

# 549.52. Side-channel metadata

Có thể đánh dấu:

```text id="r1k7p4"
@secret_dependent_control_flow
@secret_dependent_memory
@secret_dependent_timing
```

Analysis target-specific.

---

# 549.53. Security-sensitive memory

Memory policy có thể khai báo:

```text id="c8x5n2"
SecretMemory
```

với yêu cầu:

- zeroization;
- no logging;
- restricted copying;
- restricted serialization.

Không cần runtime tracking cho mọi `String`.

---

# 549.54. Zeroization

Compiler chỉ được loại bỏ zeroization nếu chứng minh:

```text id="m4q9x7"
memory is no longer security-relevant
```

hoặc platform primitive cho phép semantics tương đương.

`volatile`/secure erase primitive có thể được dùng khi cần.

---

# 549.55. Security-sensitive serialization

```text id="p7z3k1"
Secret
   ↓
serialize()
```

có thể bị policy deny.

Hoặc serializer phải có:

```text id="x5m8q2"
@allows_secret
```

explicit.

---

# 549.56. Security diagnostics

Diagnostic phải chứa:

```text id="v9k4n6"
code
severity
message
source_span
data_path
authority_path
policy
evidence
proof_state
suggested_fix
```

Ví dụ:

```text id="b3x7p1"
SECURITY-E549041

Secret data reaches network sink.

Source:
    credentials.token

Path:
    credentials.token
      → request.headers
      → http.send()

Policy:
    production.network.no_secret_export

Proof:
    Violated
```

---

# 549.57. AI-readable diagnostic

AI có thể query:

```text id="q6m2z8"
why_security_error(E549041)
show_data_flow(E549041)
show_authority_flow(E549041)
show_policy(E549041)
show_evidence(E549041)
suggest_safe_fix(E549041)
```

Fix suggestion phải dựa trên semantic graph, không phải regex.

---

# 549.58. Security fix-it

Compiler có thể đề xuất:

```text id="n8x4p2"
use parameterized query
validate path
require capability
add approval node
insert explicit sanitizer
move operation into trusted boundary
restrict tool capability
```

Nhưng AI/compiler không tự thay đổi security policy để làm error biến mất.

---

# 549.59. Security review report

Compiler có thể xuất:

```text id="m1q7v5"
SecurityReview {
    build_id
    target
    policy_version

    trust_boundaries[]
    sources[]
    sinks[]
    flows[]
    capability_paths[]
    violations[]
    runtime_checks[]
    unknowns[]
    unsafe_sites[]
}
```

---

# 549.60. Unknown inventory

Một feature rất quan trọng:

```text id="z4p8k3"
security unknowns
```

Ví dụ:

```text
unknown external callback target
unknown FFI behavior
unknown plugin capability
unknown dynamic library
unknown runtime configuration
unknown remote tool behavior
```

Security report phải hiển thị rõ các unknowns.

---

# 549.61. Closed-world vs open-world

Project có thể khai báo:

```text id="x7n2m9"
security_analysis = closed_world
```

hoặc:

```text id="p5k8q1"
security_analysis = open_world
```

Closed-world cho phép mạnh hơn:

```text id="a3v6m4"
all implementations known
```

Open-world phải conservative.

---

# 549.62. Build profile

Security analysis profile:

```text id="k9x4r2"
security = off
security = basic
security = strict
security = verify
```

`off` không thay đổi language semantics; chỉ tắt analyzer/reporting.

Những property bắt buộc bởi language safety vẫn giữ nguyên.

---

# 549.63. No performance tax

Ordinary application:

```text id="w3m7p8"
security analysis
    ↓
compile-time only
```

Production binary không phải mang security analyzer.

Runtime checks chỉ được sinh khi policy yêu cầu hoặc compile-time không chứng minh được property.

---

# 549.64. Incremental security analysis

Security query cache:

```text id="q1x5n8"
SecurityQueryKey =
    semantic_hash
    security_metadata_hash
    policy_hash
    dependency_security_hash
    target
```

Nếu code không thay đổi:

```text id="z6m3p2"
reuse result
```

Integration `487`.

---

# 549.65. Security analysis and build graph

```text id="r8k4y1"
Source
 ↓
Semantic DB
 ↓
Security DB
 ↓
Policy
 ↓
Security Result
```

Thay đổi policy không nhất thiết recompile machine code nếu chỉ thay đổi compile-time security report.

Nếu policy yêu cầu runtime checks → artifact phải rebuild.

---

# 549.66. Security provenance

Mọi security claim phải có:

```text id="v2p7m5"
source
compiler_version
policy_version
dependency_versions
target
analysis_version
evidence
```

Ví dụ:

```text
Proven:
"No secret reaches logger"
```

phải truy được proof path.

---

# 549.67. Formal verification boundary

549 không cố trở thành theorem prover.

Có thể export:

```text id="n4x8q2"
SecurityConstraintIR
```

cho formal verifier bên ngoài.

Kết quả external verifier:

```text id="m7p3z9"
verified
unverified
```

phải có provenance.

---

# 549.68. Security proof ≠ program correctness

Ngay cả:

```text id="x5k1r8"
"No tainted input reaches SQL sink"
```

cũng không chứng minh:

```text id="q9m4v2"
program is secure
```

Chỉ chứng minh property cụ thể trong scope cụ thể.

---

# 549.69. Integration toàn hệ thống

549 nối:

```text id="f3z8k5"
430 Type System
        ↓
445 Security Boundary
        ↓
478 Static Analysis
        ↓
479 Contracts
        ↓
490 Capabilities/Sandbox
        ↓
545 Governance
        ↓
546 Evidence
        ↓
547 Incident
        ↓
548 Posture
```

Security architecture trở thành một **semantic graph xuyên suốt compiler → artifact → deployment → runtime**.

---

# 549.70. Hard invariants

1. Security analysis không thay thế type checking.
2. Security analysis không thay thế ownership checking.
3. Security analysis không thay thế static analysis tổng quát.
4. Trust domain phải explicit.
5. Trust boundary phải explicit.
6. Boundary crossing phải có provenance.
7. External input mặc định untrusted khi API metadata yêu cầu.
8. Taint phải propagate theo semantic flow.
9. Taint không được tự biến mất.
10. Sanitizer phải có contract.
11. Tên hàm không đủ để chứng minh sanitizer.
12. Sink phải có security metadata.
13. Source phải có security metadata.
14. Unknown không phải Safe.
15. Assumed phải explicit.
16. Proven phải có evidence.
17. Violated phải có evidence/path.
18. RuntimeChecked phải chỉ rõ runtime guard.
19. Secret label phải được preserve qua các transformation phù hợp.
20. Sensitive label không được tự động mất.
21. Serialization phải preserve security semantics.
22. Logging là potential security sink.
23. Network send là potential security sink.
24. Process execution là security-sensitive effect.
25. Library loading là security-sensitive effect.
26. Raw syscall là security boundary.
27. FFI là trust boundary khi metadata yêu cầu.
28. Unsafe site phải được machine-readable.
29. Safe wrapper phải chứng minh invariant.
30. Unsafe implementation không mặc định làm toàn bộ program unsafe.
31. Capability flow phải explicit.
32. Authority không được tự tăng qua function call.
33. Authority amplification phải detectable.
34. Capability attenuation phải preserve provenance.
35. Ambient authority phải detectable.
36. Confused deputy phải có analysis model.
37. Global mutable authority phải policy-visible.
38. Capability delegation phải giữ principal provenance.
39. Revocation phải được xem xét trong runtime policy.
40. Expired capability không được coi active.
41. Tool output mặc định không phải trusted instruction.
42. Model output không phải authority.
43. Agent output không phải policy.
44. Workflow node effect phải explicit.
45. Irreversible action phải policy-aware.
46. Human approval phải machine-readable.
47. Security policy phải versioned.
48. Policy-to-code binding phải có identity.
49. Policy change phải invalidate security analysis.
50. Security metadata phải versioned.
51. External security metadata là untrusted cho tới khi được verify.
52. Signed metadata vẫn không đồng nghĩa semantic correctness.
53. Compiler không được invent security evidence.
54. AI không được invent security evidence.
55. AI recommendation không phải authorization.
56. AI recommendation không phải proof.
57. Security diagnostic phải có source path.
58. Security diagnostic phải có policy context.
59. Security diagnostic phải có proof state.
60. Fix-it không được thay đổi security policy.
61. Security analyzer phải phân biệt closed-world/open-world.
62. Dynamic dispatch phải có conservative handling.
63. Function pointers phải có uncertainty handling.
64. FFI unknown behavior phải trở thành Unknown.
65. Plugin unknown behavior phải trở thành Unknown.
66. Runtime configuration uncertainty phải được biểu diễn.
67. Remote service uncertainty phải được biểu diễn.
68. Generic security effects phải được instantiate đúng.
69. Effect propagation phải deterministic.
70. Security analysis phải incremental.
71. Security cache phải include policy identity.
72. Security cache phải include dependency security identity.
73. Security cache phải include target khi target affects property.
74. Security result phải có build identity.
75. Security result phải có compiler identity.
76. Security result phải có policy identity.
77. Security result phải có analysis identity.
78. Security proof phải có provenance.
79. Security unknowns phải được xuất ra.
80. Unknown external callback không được assume safe.
81. Unknown dynamic library không được assume safe.
82. Unknown tool không được assume safe.
83. Unknown model behavior không được assume safe.
84. Unknown workflow effect không được assume safe.
85. Security check không được implicit network.
86. Security analyzer không được implicit telemetry.
87. Security analyzer không được bắt buộc runtime.
88. Security analyzer không được yêu cầu GC.
89. Security analyzer không được yêu cầu VM.
90. Security analyzer không được yêu cầu LLVM.
91. Security analyzer phải có native compiler integration.
92. Security metadata có thể strip theo policy.
93. Strip metadata không được giả mạo rằng analysis đã chạy.
94. Runtime guard phải observable trong metadata.
95. Compiler có thể eliminate security check chỉ khi property được chứng minh tương đương.
96. Optimizer không được xóa security-relevant validation trái contract.
97. Constant-time annotation không phải universal guarantee.
98. Secret memory phải có explicit semantics.
99. Zeroization không được silently eliminate khi còn security obligation.
100. Secret data không được mặc định đi vào log.
101. Secret data không được mặc định serialize.
102. Security effect không được tự động biến mất qua wrapper.
103. Wrapper có thể attenuate effect nếu contract chứng minh.
104. Security contracts tích hợp `479`.
105. Security capability tích hợp `490`.
106. Governance tích hợp `545`.
107. Evidence tích hợp `546`.
108. Incident feedback tích hợp `547`.
109. Posture feedback tích hợp `548`.
110. Security findings phải liên kết evidence.
111. Security evidence phải liên kết source/semantic artifact.
112. Security review phải reproducible.
113. Security review phải deterministic với cùng inputs.
114. Security report phải distinguish fact/inference.
115. Security analyzer không tạo universal security score.
116. Severity là policy-defined.
117. Risk là policy-defined.
118. Security policy không được thay đổi language semantics silently.
119. Security profile phải explicit.
120. `security=off` không tắt language memory/type safety.
121. Runtime security checks chỉ sinh khi semantic/policy yêu cầu.
122. Security checks phải chịu target semantics.
123. Security checks phải chịu ABI semantics.
124. Security checks không được phá ownership.
125. Security checks không được phá realtime contract.
126. Security checks không được hidden allocate trong `@realtime`.
127. Security checks không được hidden block.
128. Security analysis phải chịu resource budget.
129. Graph traversal phải terminate.
130. Recursive flows phải có cycle handling.
131. Call graph incomplete phải biểu diễn uncertainty.
132. Dynamic code loading phải biểu diễn uncertainty.
133. Reflection phải biểu diễn uncertainty khi relevant.
134. Security metadata của generated code phải giữ provenance.
135. Comptime-generated code phải giữ security provenance.
136. Macro/generator output phải được phân tích sau lowering.
137. FFI generated bindings phải giữ security metadata.
138. Package binary metadata phải compatible với compiler schema.
139. Dependency security metadata phải được version-check.
140. Security policy không được tự cấp capability.
141. Security analyzer không được bypass capability checks.
142. Formal verifier output phải có external provenance.
143. Formal proof chỉ chứng minh property trong stated scope.
144. "No finding" không phải "secure".
145. "All checks passed" không phải universal security guarantee.
146. Static proof không phải runtime observation.
147. Runtime observation không phải static proof.
148. Incident absence không phải security proof.
149. Exposure absence không phải vulnerability proof.
150. **Final invariant:** Axiom phải cho phép compiler chứng minh, phát hiện hoặc xác định rõ Unknown đối với trust flow, taint flow, secret flow, capability flow, authority amplification, confused deputy, unsafe/FFI boundaries và security-policy constraints; toàn bộ kết quả phải có provenance và versioning, tích hợp với governance/evidence/incident/posture, nhưng không biến security analysis thành borrow checker thứ hai, không áp đặt runtime overhead lên code không cần, và tuyệt đối không biến AI thành security authority.

**BOOTSTRAP-549: LOCKED.**

---

# BOOTSTRAP-550 — SECURE COMPILER, SUPPLY-CHAIN HARDENING, COMPILER-SELF-PROTECTION, TRUSTED BUILD, SIGNED TOOLCHAIN & MALICIOUS COMPILER DEFENSE

**Trạng thái: NEXT**

Sau `549`, một lỗ hổng kiến trúc còn lại là **chính compiler/toolchain** trở thành mục tiêu tấn công.

Chuỗi mới sẽ là:

```text id="2qf7n9"
Source
 ↓
Compiler
 ↓
Artifact
 ↓
Deployment
 ↓
Runtime
```

Nếu compiler bị thay đổi, toàn bộ:

```text
type safety
memory safety
security analysis
provenance
reproducibility
```

đều có thể bị ảnh hưởng.

`550` vì vậy sẽ thiết kế **Trusted Axiom Toolchain**:

- compiler integrity;
- signed compiler/toolchain;
- trusted bootstrap;
- compiler provenance;
- hermetic compiler builds;
- compiler input isolation;
- malicious package/build-script defense;
- compromised dependency defense;
- poisoned cache defense;
- compiler/plugin isolation;
- deterministic compiler verification;
- stage0/stage1/stage2 trust;
- diverse double compilation;
- reproducible compiler artifacts;
- compiler self-integrity;
- secure update/rollback;
- signed SDK/sysroot;
- trusted target metadata;
- compiler capability minimization;
- build-time secret isolation;
- artifact provenance;
- compiler security evidence;
- và đặc biệt **compiler không được tự coi chính nó là trusted chỉ vì nó nói rằng nó trusted**.