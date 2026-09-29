# BOOTSTRAP-547 — AI SYSTEM INCIDENT RESPONSE, SECURITY EVENT CORRELATION, THREAT DETECTION, FORENSICS, AUTOMATED CONTAINMENT & RECOVERY ORCHESTRATION

**Status: COMPLETED / LOCKED**

## 547.1. Mục tiêu

BOOTSTRAP-547 xây dựng lớp **Incident Response & Security Operations** phía trên các nền tảng:

- `490` — Application Security / Sandbox / Capability
- `491` — Package Registry / Artifact Service
- `501` — Distributed Foundation
- `502` — Distributed Storage / Replication
- `511–513` — Agent / Tool / External Tool Protocol
- `528` — Data Governance
- `533–534` — Model Registry / Model Fleet
- `540–541` — Workflow / Workflow Compiler
- `545` — Governance / Authorization / Quota
- `546` — Compliance / Evidence / Provenance
- `475/481` — Observability / Profiling

Mục tiêu không phải biến Axiom thành một SIEM/SOC bắt buộc.

Security Operations phải là **library/platform/control-plane capability**, chỉ được đưa vào artifact khi ứng dụng sử dụng.

```text
                 Axiom Security Events
                         │
                         ▼
                 Event Normalization
                         │
                         ▼
                 Detection / Correlation
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
            Alert                Evidence
              │                     │
              └──────────┬──────────┘
                         ▼
                     Incident
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        Triage       Containment   Forensics
            │            │            │
            └────────────┼────────────┘
                         ▼
                    Remediation
                         │
                         ▼
                     Recovery
                         │
                         ▼
                Verification / Closure
                         │
                         ▼
                 Evidence Graph 546
```

---

# 547.2. Phân biệt các khái niệm

Axiom **không được gộp** các khái niệm sau:

```text
SecurityEvent
    ↓
Observation
    ↓
Detection
    ↓
Alert
    ↓
Finding
    ↓
Incident
```

### SecurityEvent

Một sự kiện quan sát được.

Ví dụ:

```text
process_started
capability_denied
invalid_signature
unexpected_network_connection
model_loaded
tool_invoked
authentication_failed
file_modified
policy_denied
sandbox_violation
```

### Observation

Dữ liệu thô từ nguồn quan sát.

### Detection

Kết quả của một rule/model/analysis xác định rằng một observation có khả năng đáng chú ý.

### Alert

Thông báo cần được xử lý.

Một detection có thể tạo:

- 0 alert;
- 1 alert;
- nhiều alert.

### Finding

Một phát hiện có cấu trúc, thường tồn tại lâu hơn alert.

### Incident

Một tập hợp sự kiện/finding/alert có liên quan tạo thành một vấn đề cần điều tra hoặc xử lý.

### Threat

Một khả năng hoặc hành vi gây nguy cơ.

### Indicator

Một observable có thể hỗ trợ detection.

Ví dụ:

```text
IP
domain
hash
certificate
process identity
package identity
model artifact hash
tool identity
file identity
capability
```

**Không được coi indicator là bằng chứng tự thân rằng một cuộc tấn công đã xảy ra.**

---

# 547.3. SecurityEvent

Canonical representation:

```text
SecurityEvent {
    event_id
    event_type
    timestamp
    timestamp_source

    principal?
    tenant?
    environment?

    process?
    worker?
    agent?
    workflow?
    model?
    tool?
    package?
    artifact?
    resource?

    source
    action
    outcome

    object?
    network?
    location?

    evidence_refs[]
    correlation_refs[]

    confidence?
    schema_version
}
```

Các trường optional phải được biểu diễn rõ ràng.

Không được dùng:

```text
0
"unknown"
null
```

để giả vờ rằng một giá trị chưa biết là giá trị hợp lệ.

---

# 547.4. Event source

Security event có thể đến từ:

```text
Application
Compiler
Runtime
OS
Filesystem
Network
Authentication
Authorization
Capability Engine
Sandbox
Plugin
Tool Server
Agent
Workflow
Model Runtime
Model Fleet
Registry
Package Manager
Dataset System
Database
Storage
Governance
Compliance
Human Operator
External Threat Intelligence
```

External event luôn mang provenance.

```text
EventSource {
    source_id
    source_type
    version
    trust_level
    provenance
}
```

---

# 547.5. Event normalization

Các hệ thống khác nhau có thể tạo event khác nhau.

Axiom chuẩn hóa về semantic event model:

```text
Raw Event
   ↓
Parser
   ↓
Normalizer
   ↓
Canonical SecurityEvent
```

Normalizer phải giữ:

- raw source identity;
- original event ID;
- original timestamp;
- original payload reference;
- transformation version.

Không được làm mất provenance.

---

# 547.6. Event identity và deduplication

Mỗi event có:

```text
EventId
```

Nếu nguồn có ID riêng:

```text
SourceEventId
```

Deduplication có thể dựa trên:

```text
source_id
source_event_id
event_type
content_hash
time_window
```

Nhưng:

> Hai event giống nội dung không mặc nhiên là cùng một event.

Dedup phải có policy rõ ràng.

---

# 547.7. Ordering

Security events trong hệ thống phân tán không được giả định có thứ tự tuyệt đối.

Axiom phải hỗ trợ:

```text
event_time
ingest_time
sequence?
causal_parent?
logical_clock?
```

Phải phân biệt:

```text
timestamp order
ingestion order
causal order
storage order
```

Tích hợp với `474` và `501`.

---

# 547.8. Detection Engine

Detection Engine:

```text
SecurityEvent Stream
        ↓
Filter
        ↓
Enrichment
        ↓
Rule Evaluation
        ↓
Correlation
        ↓
Detection
        ↓
Alert Policy
```

Detection có thể là:

1. rule-based;
2. signature-based;
3. threshold-based;
4. sequence-based;
5. state-machine-based;
6. statistical;
7. anomaly-based;
8. graph-based;
9. policy-based;
10. ML-assisted.

---

# 547.9. Detection Rule

Ví dụ semantic:

```text
rule suspicious_tool_chain {
    when
        capability_denied
        followed_by tool_invocation
        followed_by repeated_auth_failure
    within 30s

    emit Alert
}
```

Rule compiler:

```text
Rule Source
    ↓
Rule AST
    ↓
Semantic Rule
    ↓
Rule IR
    ↓
Optimized Detector
```

Không bắt buộc runtime interpreter.

Rule có thể được compile thành:

- native code;
- state machine;
- query plan;
- stream operator graph.

---

# 547.10. Detection State

Stateful detection phải có explicit state:

```text
DetectorState {
    detector_id
    version
    state_schema
    state_data
    watermark
}
```

State có thể:

- memory;
- persistent;
- distributed.

Persistent detector state phải tích hợp `455/502`.

---

# 547.11. False Positive / False Negative

Axiom phải phân biệt:

```text
Detected
Not detected
False positive
False negative
Unknown
```

`Not detected` **không có nghĩa** `safe`.

`Detected` **không tự động có nghĩa** `confirmed attack`.

---

# 547.12. Alert

```text
Alert {
    alert_id
    detector_id
    detector_version

    created_at
    observed_window

    entities[]
    evidence_refs[]

    status
    priority
    severity?

    confidence?
    dedup_key?

    incident_id?
}
```

Severity và priority là policy dimensions.

Không định nghĩa một "universal security score".

---

# 547.13. Alert lifecycle

```text
New
 ↓
Acknowledged
 ↓
Investigating
 ↓
Escalated
 ↓
Contained
 ↓
Resolved
 ↓
Closed
```

Có thể quay lại trạng thái trước nếu policy cho phép.

Ví dụ:

```text
Resolved → Reopened
```

History phải immutable.

---

# 547.14. Incident lifecycle

Canonical:

```text
Detected
   ↓
Triage
   ↓
Investigating
   ↓
Containing
   ↓
Remediating
   ↓
Recovering
   ↓
Verifying
   ↓
Closed
```

Các trạng thái phụ:

```text
Paused
WaitingHuman
FalsePositive
Duplicate
AcceptedRisk
Unknown
```

Mỗi transition phải có:

```text
actor
timestamp
reason
evidence
policy
```

---

# 547.15. Incident identity

```text
Incident {
    incident_id
    tenant
    environment

    title
    description

    created_at
    updated_at

    status
    severity?
    priority?

    alerts[]
    findings[]
    events[]
    evidence[]

    affected_entities[]
    containment_actions[]
    remediation_actions[]

    owner?
    responders[]

    timeline
}
```

---

# 547.16. Correlation

Correlation có thể dựa trên:

```text
same principal
same process
same worker
same model
same tool
same artifact
same IP
same session
same workflow
same capability
same tenant
same causal chain
same deployment
same time window
```

Nhưng correlation không được biến thành proof.

```text
correlated_with ≠ caused_by
```

---

# 547.17. Security graph

Incident system sử dụng graph:

```text
Principal
   │
   ├── Process
   │      ├── Tool
   │      ├── File
   │      └── Network
   │
   ├── Agent
   │      └── Workflow
   │             └── Tool
   │
   ├── Model
   │      └── Deployment
   │
   └── Capability
```

Graph edges:

```text
invoked
created
modified
loaded
connected_to
authorized_by
denied_by
derived_from
deployed_as
contained_by
affected
```

Mỗi edge có provenance.

---

# 547.18. Indicator of Compromise / Indicator of Attack

Axiom hỗ trợ:

```text
Indicator {
    indicator_id
    kind
    value
    normalized_value

    source
    first_seen?
    last_seen?
    expiration?

    confidence?
    context
    provenance
}
```

Indicator có thể là:

- hash;
- hostname;
- IP;
- domain;
- URL;
- certificate;
- process characteristic;
- package hash;
- model hash;
- unusual capability pattern.

Threat intelligence là **external evidence**, không phải policy authority.

---

# 547.19. Threat intelligence

```text
ThreatIntelRecord {
    source
    version
    published_at
    observed_at?
    indicators[]
    relationships[]
    confidence?
    license?
    provenance
}
```

Axiom không tự động tin threat intelligence.

Nguồn ngoài phải chịu:

- authenticity checks;
- freshness checks;
- provenance checks;
- conflict handling.

---

# 547.20. Enrichment

Event có thể được enrich bằng:

```text
Identity
Asset
Package
Artifact
Model
Dataset
Deployment
Capability
Network metadata
Geolocation
Threat intelligence
Build provenance
Policy
Compliance evidence
```

Enrichment không được sửa raw event.

```text
RawEvent → immutable
Enrichment → derived
```

---

# 547.21. Forensics

Forensic evidence có thể gồm:

```text
Process metadata
Process tree
Loaded modules
Open files
Network connections
Configuration
Runtime state
Logs
Traces
Security events
Artifact hashes
Package metadata
Model metadata
Workflow state
Capability state
Policy state
Deployment state
```

Memory snapshot hoặc packet capture là optional platform capability.

---

# 547.22. Chain of custody

Evidence:

```text
Evidence {
    evidence_id
    type

    collected_at
    collector
    source

    content_hash
    size

    acquisition_method
    provenance

    parent_evidence?
    storage_location

    integrity_status
}
```

Mỗi transformation:

```text
Evidence A
   ↓ transform
Evidence B
```

phải giữ lineage.

---

# 547.23. Evidence integrity

Ba khái niệm vẫn độc lập:

```text
Hash integrity
Signature authenticity
Semantic correctness
```

Hash đúng không chứng minh nội dung đáng tin.

Signature hợp lệ không chứng minh nội dung đúng.

---

# 547.24. Automated containment

Axiom hỗ trợ action:

```text
RevokeCapability
DisableTool
QuarantineArtifact
DisablePackage
DrainWorker
IsolateProcess
IsolateHost
DisableDeployment
PauseWorkflow
TerminateSession
BlockNetworkEndpoint
RevokeCredential
FreezeModelVersion
DisableTenantResource
```

Containment action có classification:

```text
Reversible
PotentiallyReversible
Irreversible
```

---

# 547.25. Safety gate

Không cho phép AI tự động thực hiện mọi containment.

```text
Detection
   ↓
Policy
   ↓
Risk / Authority Check
   ↓
┌───────────────┐
│               │
Automatic     Human Approval
│               │
└───────┬───────┘
        ↓
Containment
```

Policy có thể yêu cầu:

```text
RequireApproval
RequireTwoPersonApproval
RequireStepUp
DryRunOnly
```

theo `545`.

---

# 547.26. Playbook

Playbook là workflow chuyên dụng.

```text
Incident
   ↓
Playbook Selection
   ↓
Workflow 540/541
   ↓
Investigation
   ↓
Approval
   ↓
Containment
   ↓
Remediation
   ↓
Recovery
```

Ví dụ:

```text
on IncidentDetected:
    collect_evidence
    classify
    if confirmed:
        request_approval
        isolate_worker
        revoke_tool_capability
        verify
        recover
```

Playbook phải versioned.

---

# 547.27. Không biến AI thành security authority

AI có thể:

- correlate;
- summarize;
- search;
- classify;
- suggest;
- generate hypotheses;
- recommend investigation steps.

AI **không được tự biến output của nó thành evidence**.

```text
AI hypothesis ≠ verified fact
AI recommendation ≠ authorization
AI classification ≠ incident confirmation
```

Muốn action phải đi qua policy/capability boundary.

---

# 547.28. Threat hunting

Security query API:

```text
events(...)
alerts(...)
incidents(...)
indicators(...)
evidence(...)
process_tree(...)
network_activity(...)
capability_usage(...)
tool_usage(...)
model_usage(...)
workflow_activity(...)
policy_decisions(...)
```

Ví dụ:

```text
find processes that:
    loaded artifact X
    AND contacted endpoint Y
    AND invoked tool Z
    within 10 minutes
```

Kết quả phải chứa evidence/provenance.

---

# 547.29. Attack-path analysis

Security graph có thể tìm:

```text
Principal
   ↓
Credential
   ↓
Capability
   ↓
Tool
   ↓
Process
   ↓
Network
   ↓
Resource
```

Graph analysis có thể xác định **possible path**.

Không được gọi path đó là "successful attack" nếu chưa có evidence.

---

# 547.30. Distributed incident correlation

Trong cluster:

```text
Node A → Event
Node B → Event
Node C → Event
```

Correlation engine phải hỗ trợ:

- event IDs;
- node IDs;
- process IDs;
- logical clocks;
- causal IDs;
- trace IDs;
- deployment IDs.

Partition và clock skew phải được thể hiện.

---

# 547.31. Alert storm protection

Phải hỗ trợ:

```text
deduplication
grouping
rate limiting
sampling
suppression
cooldown
maintenance window
backpressure
```

Nhưng:

> Suppression không được xóa bằng chứng gốc.

Nếu event bị drop do giới hạn:

```text
dropped_count
drop_reason
window
```

phải được ghi nhận.

---

# 547.32. Tamper resistance

Security logs/evidence phải hỗ trợ:

- append-only;
- hash chaining;
- immutable storage;
- remote replication;
- access audit;
- restricted deletion;
- retention policy.

Nếu hệ thống không thể bảo đảm chống sửa đổi thì metadata phải nói rõ:

```text
integrity_assurance = limited
```

---

# 547.33. Recovery

Recovery tách khỏi containment.

```text
Containment
    ↓
Eradication / Remediation
    ↓
Recovery
    ↓
Validation
    ↓
Return to Service
```

Recovery có thể:

- rollback deployment;
- restore artifact;
- restore snapshot;
- redeploy clean worker;
- rotate credential;
- re-enable capability;
- resume workflow.

Không được giả định rollback có thể hoàn tác external side effects.

---

# 547.34. Incident-aware deployment

Integration với `534`:

```text
Incident
   ↓
Deployment Policy
   ├── Pause rollout
   ├── Drain fleet
   ├── Freeze version
   └── Rollback
```

Deployment rollback phải giữ:

```text
old_version
new_version
trigger_incident
policy
approval
evidence
```

---

# 547.35. Model security response

Integration `533/534`:

```text
Suspicious Model
      ↓
Freeze Model Version
      ↓
Block Deployment
      ↓
Quarantine Artifact
      ↓
Trace Existing Deployments
      ↓
Contain Fleet
```

Không được xóa artifact trước khi forensic retention policy quyết định.

---

# 547.36. Tool security response

Tool có thể bị:

```text
disabled
quarantined
capability-restricted
version-pinned
moved to sandbox
```

Existing sessions phải có policy rõ:

```text
allow_existing
terminate_existing
drain_existing
```

Không silent revoke nếu semantics yêu cầu continuity, trừ emergency policy đã định nghĩa.

---

# 547.37. Agent/workflow incident response

Một incident có thể ảnh hưởng:

```text
Agent
Session
Workflow
Task
Tool Call
Memory
Model
Deployment
```

Runtime phải hỗ trợ:

```text
pause workflow
checkpoint
capture state
revoke capability
terminate session
resume after verification
```

---

# 547.38. Evidence-aware remediation

Remediation action:

```text
RemediationAction {
    action_id
    incident_id
    actor
    action_type

    target
    preconditions
    policy
    approval?

    before_state?
    after_state?

    evidence_before[]
    evidence_after[]

    reversible?
    status
}
```

---

# 547.39. Idempotency

Security response thường phải retry.

Mọi action có side effect phải hỗ trợ:

```text
idempotency_key
```

Ví dụ:

```text
revoke capability C
```

gọi hai lần không được tạo hai trạng thái không xác định.

---

# 547.40. Human-in-the-loop

Human approval phải là typed object:

```text
Approval {
    approval_id
    principal
    action
    target
    policy_version

    created_at
    expires_at

    scope
    decision
    evidence_refs[]
}
```

Approval không được dùng lại ngoài scope.

---

# 547.41. Incident budget

Incident response cũng chịu:

```text
max_actions
max_runtime
max_parallel_actions
max_network_requests
max_storage
max_workers
max_evidence_size
```

Ngăn incident automation tự tạo resource exhaustion.

---

# 547.42. Recovery verification

Không được:

```text
containment_success → assume_recovered
```

Phải có verification.

```text
Containment
    ↓
Verification
    ↓
Remediation
    ↓
Verification
    ↓
Recovery
    ↓
Verification
```

---

# 547.43. Post-incident analysis

Incident đóng phải có thể tạo:

```text
IncidentReport {
    timeline
    affected_entities
    evidence
    detections
    containment
    remediation
    recovery
    unresolved_questions
    lessons_learned
}
```

Root cause phải phân biệt:

```text
Observed
Strongly supported
Hypothesis
Unknown
```

Không cho phép hệ thống tự ghi "root cause" nếu evidence chưa đủ.

---

# 547.44. Security state machine

Canonical incident engine:

```text
                ┌──────────────┐
                │    DETECTED  │
                └──────┬───────┘
                       ↓
                   TRIAGING
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        FALSE POSITIVE       CONFIRMED
                                 ↓
                           INVESTIGATING
                                 ↓
                            CONTAINING
                                 ↓
                           REMEDIATING
                                 ↓
                            RECOVERING
                                 ↓
                            VERIFYING
                                 ↓
                              CLOSED
```

Mọi transition có event.

---

# 547.45. Deterministic simulation

Security engine phải hỗ trợ:

```text
Synthetic Events
Virtual Clock
Deterministic Scheduler
Fake Assets
Fake Network
Mock Policy
Mock Approval
Mock Threat Intelligence
```

Cho phép test:

- detection;
- correlation;
- alert storm;
- containment;
- retry;
- distributed partition;
- clock skew;
- duplicate events;
- missing events;
- malicious event source.

---

# 547.46. Replay

Replay:

```text
Recorded Security Events
       ↓
Detection Engine
       ↓
Correlation
       ↓
Simulated Actions
```

Replay mặc định **không thực hiện irreversible action**.

---

# 547.47. Performance

Security observability không được biến ordinary application thành ứng dụng chậm do hidden instrumentation.

Profiles:

```text
security = off
security = minimal
security = standard
security = forensic
```

Mỗi profile xác định rõ:

- event collection;
- storage;
- sampling;
- overhead;
- retention.

---

# 547.48. AI introspection

Compiler/runtime cung cấp:

```text
why_alerted(incident)
why_correlated(event_a,event_b)
why_contained(target)
why_not_contained(target)
why_action_blocked(action)
what_evidence_supports(finding)
what_evidence_is_missing(finding)
what_policy_allowed(action)
what_policy_denied(action)
what_changed_before_incident(incident)
what_deployments_are_affected(artifact)
what_sessions_are_affected(resource)
```

Kết quả phải phân biệt:

```text
Fact
Evidence
Inference
Hypothesis
Unknown
```

---

# 547.49. Integration với Evidence Graph 546

Security graph nối vào governance evidence:

```text
Source
  ↓
Build
  ↓
Artifact
  ↓
Deployment
  ↓
Execution
  ↓
SecurityEvent
  ↓
Detection
  ↓
Incident
  ↓
Containment
  ↓
Remediation
  ↓
Verification
```

Cho phép truy vấn hai chiều:

```text
artifact → incidents
incident → artifacts
model → incidents
tool → incidents
tenant → incidents
policy → incidents
deployment → incidents
worker → incidents
```

---

# 547.50. Hard invariants

BOOTSTRAP-547 khóa các invariant chính:

1. SecurityEvent khác Alert.
2. Alert khác Finding.
3. Finding khác Incident.
4. Threat khác Indicator.
5. Detection không phải proof.
6. External threat intelligence là untrusted evidence.
7. Raw event không bị sửa bởi enrichment.
8. Provenance không được mất qua transformation.
9. Event ordering không mặc định là causal ordering.
10. Clock skew phải được biểu diễn.
11. Dedup không được tự động hợp nhất mọi event giống nhau.
12. Dropped events phải được ghi nhận.
13. Suppression không được xóa raw evidence.
14. Detection phải có version.
15. Detection state phải có schema.
16. Stateful detector phải chịu recovery semantics.
17. False positive và false negative phải phân biệt.
18. Không có universal security score.
19. Severity là policy dimension.
20. Incident state transitions phải có audit.
21. Incident history immutable.
22. Containment phải có capability.
23. Containment phải có authorization.
24. Irreversible action cần policy gate.
25. Human approval phải scoped.
26. Approval phải expire được.
27. Approval không được biến thành ambient authority.
28. Security automation có resource budget.
29. Retry action phải hỗ trợ idempotency.
30. External side effects không được giả vờ reversible.
31. Containment không đồng nghĩa recovery.
32. Recovery phải verification.
33. AI hypothesis không phải evidence.
34. AI recommendation không phải authorization.
35. AI không được tự cấp capability.
36. Threat intelligence không được override policy.
37. Security graph phải giữ provenance.
38. Cross-tenant correlation phải chịu authorization.
39. Forensic evidence phải có integrity metadata.
40. Hash không đồng nghĩa authenticity.
41. Signature không đồng nghĩa semantic correctness.
42. Evidence transformation phải giữ lineage.
43. Incident response phải hỗ trợ deterministic replay.
44. Replay không thực hiện irreversible actions mặc định.
45. Distributed correlation phải hỗ trợ duplicate/reorder/partition.
46. Security runtime không bắt buộc với ordinary applications.
47. Không có hidden network telemetry.
48. Không có hidden background security thread.
49. Security storage phải explicit.
50. Security policy phải versioned.
51. Policy decision phải provenance-aware.
52. Containment action phải ghi before/after state nếu khả dụng.
53. Model incident phải liên kết artifact hash.
54. Tool incident phải liên kết tool version.
55. Deployment incident phải liên kết deployment revision.
56. Workflow incident phải liên kết WorkflowRunId/NodeId.
57. Agent incident phải liên kết AgentInstance/Session.
58. Evidence collection failure phải được biểu diễn.
59. Missing evidence không được coi là clean.
60. Unknown không được coi là safe.
61. "No detection" không được coi là "no threat".
62. Incident closure phải có closure reason.
63. Reopened incident phải giữ lịch sử cũ.
64. Recovery rollback phải giữ provenance.
65. Rollback không hoàn tác external effects một cách giả định.
66. Security actions phải chịu governance quota.
67. Security actions phải chịu capability boundary.
68. Security data phải chịu privacy policy.
69. Sensitive evidence phải có access control.
70. Evidence retention phải explicit.
71. Evidence deletion phải tạo audit record.
72. Forensic snapshot phải có acquisition provenance.
73. Process isolation phải phân biệt OS-level và language-level.
74. Sandbox violation phải có event identity.
75. Plugin violation phải liên kết plugin identity.
76. Package violation phải liên kết package/artifact hash.
77. Model violation phải liên kết model version.
78. Dataset incident phải liên kết dataset version.
79. Credential incident phải liên kết credential identity nhưng không log secret.
80. Secret material không được đưa vào incident logs.
81. Security logs không tự động upload.
82. Alert storm protection không được silently discard evidence without accounting.
83. Sampling phải ghi phạm vi sampling.
84. Statistical/anomaly detection phải ghi model/version/config.
85. Detection confidence không phải probability of attack unless explicitly defined.
86. Correlation không phải causation.
87. Graph path không phải confirmed attack path.
88. Root cause phải có evidence classification.
89. Hypothesis phải được đánh dấu.
90. Unknown phải được giữ nguyên.
91. Automated containment phải có policy.
92. Emergency policy phải versioned.
93. Emergency override phải audit.
94. Multi-person approval phải chống reuse.
95. Security workflow phải chịu workflow versioning.
96. Playbook phải chịu migration semantics.
97. Long-running incident workflow phải checkpoint được.
98. Incident recovery phải chống duplicate actions.
99. Distributed response phải chống stale membership.
100. Stale worker không được thực hiện containment ngoài authority.
101. Stale policy không được silently authorize critical action.
102. Security event schema phải versioned.
103. Detector schema phải versioned.
104. Incident schema phải versioned.
105. Evidence schema phải versioned.
106. Forensic artifact phải content-addressable khi phù hợp.
107. Incident identity không phụ thuộc title.
108. Alert identity không phụ thuộc message text.
109. Event identity không phụ thuộc display formatting.
110. Timestamps phải giữ nguồn clock.
111. Time uncertainty phải được thể hiện khi cần.
112. Security action phải có actor identity.
113. Machine actor phải có identity.
114. Agent actor phải có identity.
115. Human actor phải có identity.
116. Delegated authority phải giữ provenance.
117. Capability revocation phải có effective time.
118. Quarantine không đồng nghĩa deletion.
119. Freeze không đồng nghĩa withdrawal.
120. Disable không đồng nghĩa uninstall.
121. Security response phải hỗ trợ dry-run.
122. Dry-run không được tạo external side effect.
123. Simulation không được giả mạo production evidence.
124. Test evidence phải được phân biệt production evidence.
125. AI-generated analysis phải có provenance.
126. Automated classification phải có detector identity.
127. Security state machine phải deterministic với cùng input/policy.
128. Recovery phải chịu fault injection.
129. Detection engine phải chịu malformed events.
130. Detection engine phải chịu resource exhaustion.
131. Parser phải bounds-safe.
132. Threat-intel parser phải coi dữ liệu ngoài là untrusted.
133. Network evidence phải chịu security boundary.
134. Cross-process evidence phải có authority.
135. Cross-tenant evidence access mặc định deny.
136. Incident exports phải chịu data policy.
137. Incident search phải chịu authorization.
138. Security graph queries phải chịu tenant isolation.
139. Audit records không được bị incident owner tự sửa.
140. Evidence chain phải phát hiện tampering.
141. Missing collector không được coi là no events.
142. Collector outage phải observable.
143. Event ingestion backpressure phải explicit.
144. Event loss phải measurable.
145. Security engine không được tạo infinite remediation loop.
146. Playbook retry phải bounded.
147. Compensation không phải guarantee of rollback.
148. Containment escalation phải bounded.
149. Security automation không được tự mở rộng authority.
150. Incident response không được tự sửa policy authority.
151. Policy sửa đổi phải qua governance.
152. Security response không được bypass language safety guarantees.
153. Unsafe native operations vẫn chịu security boundary.
154. Security system không được yêu cầu GC.
155. Security system không được yêu cầu global runtime.
156. Security system không được yêu cầu VM.
157. Security system phải có native implementation path.
158. Security artifact phải có build provenance.
159. Security configuration là build/runtime input tùy loại.
160. Security profile phải là explicit configuration.
161. Security overhead phải đo được.
162. Security instrumentation không được ẩn.
163. Production profile có thể loại forensic instrumentation.
164. Forensic profile phải công khai overhead.
165. Incident evidence phải có retention policy.
166. Retention không được tự động vô hạn.
167. Deletion phải chịu governance.
168. Incident closure không được xóa evidence.
169. Archived incident vẫn truy vấn được theo policy.
170. Reopened incident giữ identity.
171. Incident merge phải giữ lineage.
172. Incident split phải giữ lineage.
173. Alert correlation phải reversible về evidence graph.
174. Detector update phải giữ version.
175. Rule disable phải audit.
176. Indicator expiry phải explicit.
177. Indicator source phải rõ.
178. Indicator conflict phải được biểu diễn.
179. Threat intel conflict không được silently resolve.
180. Security finding phải giữ evidence references.
181. Finding status không được thay đổi evidence.
182. Remediation phải liên kết finding.
183. Verification phải liên kết remediation.
184. Post-incident report phải có provenance.
185. Root-cause conclusion phải phân biệt evidence/inference.
186. Security metrics không phải universal quality score.
187. Incident severity không phải global objective truth.
188. Risk acceptance phải thuộc governance.
189. Accepted risk không phải resolved.
190. False positive không phải evidence deletion.
191. Suppressed alert không phải resolved incident.
192. Human dismissal phải audit.
193. Automated dismissal phải audit.
194. Security control-plane và data-plane phải tách biệt.
195. Security control-plane failure không được tự động imply application failure.
196. Security response failure phải observable.
197. Recovery failure phải giữ incident active.
198. Evidence collection failure phải giữ uncertainty.
199. **Final invariant:** Axiom phải cung cấp incident detection, correlation, investigation, forensic evidence, containment, remediation, recovery và verification với provenance, authorization, capability, audit, deterministic replay và explicit uncertainty; AI có thể hỗ trợ phân tích nhưng không trở thành authority ngầm; security operations không được trở thành hidden runtime của ứng dụng thông thường.

**BOOTSTRAP-547: LOCKED.**

---

# BOOTSTRAP-548 — AI SECURITY OPERATIONS CONTROL PLANE, THREAT INTELLIGENCE, ATTACK-SURFACE MANAGEMENT, CONTINUOUS EXPOSURE ANALYSIS & SECURITY POSTURE GRAPH

**Status: COMPLETED / LOCKED**

547 xử lý **khi incident xảy ra**.

548 bổ sung lớp quan trọng hơn ở phía trước:

> **Biết hệ thống đang phơi nhiễm ở đâu, authority nằm ở đâu, asset nào có thể bị tác động, và exposure thay đổi như thế nào trước khi trở thành incident.**

---

## 548.1. Kiến trúc

```text
                 Asset / Resource Inventory
                           │
                           ▼
                  Asset Identity Graph
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Dependencies      Capabilities      Exposure
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  Security Posture Graph
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    Threat Intel      Attack Surface    Configuration
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                 Exposure Analysis Engine
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
           Finding       Change       Trend
              │            │            │
              └────────────┼────────────┘
                           ▼
                    Risk Treatment
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
       Remediate        Mitigate         Accept
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Verification
                           │
                           ▼
                     Evidence 546
```

---

# 548.2. Asset ≠ Resource ≠ Exposure ≠ Vulnerability ≠ Risk

Axiom khóa:

```text
Asset
Resource
Exposure
Weakness
Vulnerability
Threat
Finding
Risk
Incident
```

không phải cùng một khái niệm.

Ví dụ:

```text
GPU worker
    = Asset

Model deployment
    = Resource

Public network endpoint
    = Exposure

Missing validation
    = Weakness

Known exploitable flaw
    = Vulnerability

Adversary capability
    = Threat

Detected condition
    = Finding

Potential consequence under policy
    = Risk

Observed security event
    = Incident
```

---

# 548.3. Asset identity

```text
Asset {
    asset_id
    asset_type
    owner
    tenant
    environment

    version?
    location?
    lifecycle

    capabilities
    dependencies

    provenance
    metadata
}
```

Asset có thể là:

```text
Host
Process
Container
Worker
Device
GPU
Model
Model Version
Agent
Workflow
Tool
Package
Artifact
Dataset
Database
File
Network Endpoint
Credential Reference
Service
Application
Library
Compiler
SDK
```

---

# 548.4. Attack surface

Attack surface là tập hợp các điểm mà authority hoặc data có thể đi qua boundary.

```text
AttackSurface {
    surface_id
    asset_id
    entry_type

    protocol?
    endpoint?
    capability?
    identity?
    data_flow?

    exposure_state
    evidence
}
```

Entry points:

```text
Network
HTTP
RPC
IPC
File
Plugin
Tool
Model
Dataset
User Input
Environment
Credential
Device
GPU
Workflow Trigger
Webhook
Package
Update
```

---

# 548.5. Exposure state

```text
NotExposed
InternallyExposed
ExternallyReachable
Restricted
Privileged
Unknown
```

Không được suy ra:

```text externally reachable → vulnerable
```

và cũng không được suy ra:

```text internal → safe
```

---

# 548.6. Dependency attack surface

Graph:

```text
Application
   ↓
Package
   ↓
Dependency
   ↓
Native Library
   ↓
OS API
   ↓
Kernel
   ↓
Device
```

Axiom phải hỗ trợ:

```text
what depends on X?
what can reach X?
what X can affect?
```

Tích hợp `447`, `487`, `546`.

---

# 548.7. Capability attack surface

```text
Agent
  ↓
Tool
  ↓
Capability
  ↓
Resource
```

Graph phải trả lời:

```text
which principal can invoke tool?
which tool can access filesystem?
which agent can access network?
which workflow can modify deployment?
```

---

# 548.8. Security posture

Posture là trạng thái observable hiện tại:

```text
PostureSnapshot {
    snapshot_id
    timestamp
    scope

    assets
    exposures
    controls
    findings
    policy_state
    dependency_state
    deployment_state

    evidence_refs[]
}
```

Không được tạo một universal posture score.

---

# 548.9. Continuous exposure analysis

Pipeline:

```text
Inventory
   ↓
Normalize
   ↓
Build Security Graph
   ↓
Evaluate Exposure Rules
   ↓
Correlate Threat Intelligence
   ↓
Generate Findings
   ↓
Track Changes
   ↓
Verify Controls
```

Có thể chạy:

- event-driven;
- periodic;
- deployment-triggered;
- package-change-triggered;
- policy-change-triggered.

---

# 548.10. Security control

```text
SecurityControl {
    control_id
    version
    scope
    requirement
    implementation
    evidence_rule
}
```

Ví dụ:

```text
network endpoint must require authentication
model artifact must be signed
tool must not possess filesystem write capability
deployment must use approved model version
```

Control liên kết `546`.

---

# 548.11. Control coverage

Axiom phải trả lời:

```text
control → assets
asset → controls
control → evidence
evidence → finding
finding → remediation
```

Nhưng:

```text
control exists ≠ control effective
```

---

# 548.12. Security posture graph

Canonical graph:

```text
Tenant
  ↓
Application
  ↓
Deployment
  ↓
Worker
  ↓
Process
  ↓
Tool
  ↓
Capability
  ↓
Resource
  ↓
Data
```

Song song:

```text
Artifact
   ↓
Package
   ↓
Dependency
```

và:

```text
Threat
   ↓
Indicator
   ↓
Exposure
   ↓
Finding
```

Tất cả nối bằng provenance.

---

# 548.13. Threat intelligence correlation

Threat intelligence chỉ dùng để enrich:

```text
Asset
Endpoint
Artifact
Package
Domain
IP
Hash
Certificate
```

Correlation output:

```text
ThreatMatch {
    match_id
    asset
    indicator
    source
    evidence
    observed_at
    freshness
}
```

Không được gọi match là confirmed compromise.

---

# 548.14. Threat intelligence lifecycle

```text
Imported
 ↓
Validated
 ↓
Active
 ↓
Expired
 ↓
Withdrawn
```

Threat intelligence có thể bị:

- outdated;
- revoked;
- contradicted;
- duplicated.

---

# 548.15. Vulnerability model

```text
Vulnerability {
    vulnerability_id
    affected_component
    affected_versions
    fixed_versions?

    source
    published_at
    updated_at

    exploitability?
    evidence?
    provenance
}
```

Không được tự động coi:

```text
version matches → exploitable
```

Cần context:

```text
configuration
reachability
feature usage
platform
permissions
exposure
mitigations
```

---

# 548.16. Reachability analysis

Axiom phải có thể xác định:

```text
Dependency exists
```

khác với:

```text
Dependency code reachable
```

và:

```text
Code reachable
```

khác với:

```text
Vulnerable behavior reachable from attacker-controlled input
```

Đây là integration với compiler call graph `446/478`.

---

# 548.17. Attack path

Graph query:

```text
ExternalPrincipal
    ↓
Endpoint
    ↓
Service
    ↓
Tool
    ↓
Capability
    ↓
PrivilegedResource
```

Kết quả:

```text
PossibleAttackPath
```

Không được tự động gọi là successful attack.

---

# 548.18. Exposure finding

```text
ExposureFinding {
    finding_id

    asset
    exposure
    condition

    evidence[]
    affected_scope[]

    severity?
    confidence?

    first_seen
    last_seen

    remediation?
}
```

Severity vẫn là policy.

---

# 548.19. Finding lifecycle

```text
Detected
 ↓
Validated
 ↓
Assigned
 ↓
Remediating
 ↓
Verification
 ↓
Resolved
```

Hoặc:

```text
AcceptedRisk
FalsePositive
NotApplicable
Unknown
```

`AcceptedRisk` không phải `Resolved`.

---

# 548.20. Configuration drift

Axiom phải track:

```text
DesiredState
ObservedState
```

Ví dụ:

```text
Desired:
network access = restricted

Observed:
network access = public
```

→ configuration drift finding.

---

# 548.21. Policy drift

```text
PolicyVersion N
       ↓
Observed deployment
       ↓
PolicyVersion N-1
```

Nếu deployment vẫn dùng policy cũ:

```text
policy drift
```

Không được tự động sửa production.

---

# 548.22. Dependency drift

Theo dõi:

```text
lockfile
package version
artifact hash
compiler
SDK
native dependency
model dependency
tool dependency
```

Integration `447/487/533`.

---

# 548.23. Identity drift

Track:

```text
principal
roles
capabilities
credentials
delegations
expiration
revocation
```

Ví dụ:

```text
Expected:
Agent A → read-only dataset

Observed:
Agent A → write dataset
```

→ identity/authority drift.

---

# 548.24. Security baseline

Baseline phải versioned:

```text
SecurityBaseline {
    baseline_id
    version
    scope
    rules[]
    effective_time
}
```

Baseline không phải universal standard.

Mỗi organization/project/environment có thể định nghĩa policy riêng.

---

# 548.25. Change impact

Mỗi thay đổi:

```text
Package Update
Model Update
Tool Update
Policy Update
Deployment Update
Configuration Update
Capability Update
Network Update
```

có thể trigger:

```text
Exposure Re-analysis
```

Compiler/build graph có thể cung cấp impact set.

---

# 548.26. Continuous verification

```text
Change
 ↓
Analyze
 ↓
Deploy
 ↓
Observe
 ↓
Verify Controls
 ↓
Update Posture
```

Verification có thể là:

- static;
- build-time;
- deployment-time;
- runtime;
- periodic;
- external evidence.

---

# 548.27. Remediation

Remediation action:

```text
Upgrade
Patch
Reconfigure
Disable
Restrict
Rotate
Revoke
Isolate
Rollback
Replace
Delete
```

Mọi action chịu `545`.

---

# 548.28. Mitigation ≠ Remediation

Ví dụ:

```text
Upgrade package
```

là remediation.

```text
Restrict network access
```

có thể là mitigation.

Mitigation không chứng minh vulnerability đã biến mất.

---

# 548.29. Compensating control

Nếu chưa sửa được:

```text
Vulnerability
   ↓
Compensating Control
   ↓
Residual Exposure
```

Residual exposure phải vẫn tồn tại trong graph.

Không được biến mitigation thành false "resolved".

---

# 548.30. Risk treatment

Canonical:

```text
Finding
   ↓
Treatment
 ┌───────┬────────┬────────────┐
 ↓       ↓        ↓
Fix    Mitigate  AcceptRisk
```

Có thể:

```text
Transfer
Avoid
```

nếu governance model cần.

Risk acceptance thuộc policy/governance, không phải compiler.

---

# 548.31. Security exception

```text
SecurityException {
    exception_id
    scope
    reason
    owner
    policy
    created_at
    expires_at
    compensating_controls[]
}
```

Exception phải:

- scoped;
- expirable;
- auditable.

Không có permanent wildcard exception mặc định.

---

# 548.32. Attack-surface inventory

API:

```text
list_assets()
list_entrypoints()
list_public_endpoints()
list_capabilities()
list_external_dependencies()
list_privileged_resources()
list_untrusted_inputs()
```

AI query:

```text
why_exposed(asset)
who_can_reach(asset)
what_can_reach(asset)
what_can_asset_reach(asset)
what_changed(asset)
what_controls_apply(asset)
what_evidence_exists(asset)
```

---

# 548.33. Security posture diff

Hai snapshot:

```text
Posture A
   ↓ diff
Posture B
```

Phải cho biết:

```text
new assets
removed assets
new exposures
removed exposures
new capabilities
revoked capabilities
new dependencies
changed controls
new findings
resolved findings
```

Không đưa ra một aggregate security score.

---

# 548.34. Temporal posture

Posture phải query được theo thời gian:

```text
posture_at(timestamp)
exposure_history(asset)
capability_history(principal)
deployment_security_history(deployment)
```

Integration `474`.

---

# 548.35. Security posture and incidents

```text
Exposure
   ↓
Finding
   ↓
Potential Threat
   ↓
Security Event
   ↓
Incident
```

Nhưng chain này **không bắt buộc xảy ra**.

Một exposure có thể tồn tại mà chưa có incident.

---

# 548.36. Incident feedback

`547` có thể feed back:

```text
Incident
   ↓
New Indicator
   ↓
New Detection Rule
   ↓
Exposure Analysis
   ↓
New Control
```

Nhưng incident response không được tự động thay đổi production policy nếu không có governance authorization.

---

# 548.37. Supply-chain posture

Graph:

```text
Source
 ↓
Package
 ↓
Dependency
 ↓
Build
 ↓
Artifact
 ↓
Deployment
 ↓
Execution
```

Mỗi node có:

```text
hash
version
provenance
signature?
evidence
```

Integration `546`.

---

# 548.38. Model supply-chain posture

```text
Dataset
 ↓
Training
 ↓
Checkpoint
 ↓
Optimization
 ↓
Model
 ↓
Registry
 ↓
Deployment
 ↓
Inference
```

Có thể query:

```text
which deployments use model X?
which models derive from dataset Y?
which incidents affected artifact Z?
```

---

# 548.39. Agent supply-chain posture

```text
Agent Definition
 ↓
Prompt
 ↓
Model
 ↓
Tool
 ↓
Workflow
 ↓
Memory
 ↓
Deployment
```

Security posture phải giữ version của tất cả thành phần.

---

# 548.40. Tool authority graph

Đây là một graph đặc biệt quan trọng:

```text
Principal
   ↓
Agent
   ↓
Workflow
   ↓
Tool
   ↓
Capability
   ↓
Resource
```

Có thể query transitive authority:

```text
effective_authority(principal)
```

Nhưng kết quả phải tính:

- expiration;
- tenant;
- environment;
- policy;
- delegation;
- revocation.

---

# 548.41. Blast-radius analysis

Nếu asset X bị compromise:

```text
X
 ↓
reachable resources
 ↓
reachable principals
 ↓
reachable tenants
 ↓
reachable deployments
```

Output:

```text
PotentialImpactSet
```

Không được gọi là actual impact nếu chưa có evidence.

---

# 548.42. Security graph consistency

Graph engine phải phát hiện:

```text
orphan asset
dangling capability
unknown principal
missing owner
expired delegation
stale deployment
missing provenance
conflicting identity
cross-tenant edge
```

---

# 548.43. Continuous exposure scheduler

Không cần chạy toàn bộ graph mỗi lần.

Có thể incremental:

```text
Change Event
   ↓
Affected Graph Nodes
   ↓
Affected Rules
   ↓
Selective Re-analysis
```

Integration `487`.

---

# 548.44. Cache

Exposure result cache:

```text
CacheKey =
    graph_version
    rule_version
    policy_version
    threat_intel_version
    target_scope
```

Cache hit không được bypass freshness requirement.

---

# 548.45. Freshness

Mỗi evidence có:

```text
observed_at
expires_at?
freshness_policy
```

Stale evidence phải được đánh dấu.

```text
Fresh
Stale
Expired
Unknown
```

Không được coi stale evidence là current fact.

---

# 548.46. Security posture evidence

Mỗi posture claim phải có:

```text
Claim
Evidence
Timestamp
Scope
Source
Transformation
Validity
```

Ví dụ:

```text
"Endpoint X requires authentication"
```

phải truy ngược được đến:

```text
configuration
deployment
runtime observation
policy
test
```

---

# 548.47. AI assistance

AI có thể:

- summarize attack surface;
- explain exposure;
- correlate findings;
- suggest remediation;
- identify suspicious dependency;
- generate query;
- propose policy/control;
- prioritize investigation based on explicit project policy.

AI không được:

- tự cấp quyền;
- tự accept risk;
- tự mark finding resolved;
- tự suppress evidence;
- tự alter governance policy;
- tự execute irreversible remediation.

---

# 548.48. Security knowledge graph

548 trở thành knowledge layer:

```text
Asset
 ├── Identity
 ├── Owner
 ├── Version
 ├── Dependency
 ├── Exposure
 ├── Capability
 ├── Policy
 ├── Evidence
 ├── Finding
 ├── Incident
 └── Remediation
```

Graph phải hỗ trợ temporal/provenance queries.

---

# 548.49. Hard invariants

1. Asset khác Resource.
2. Exposure khác Vulnerability.
3. Vulnerability khác Finding.
4. Finding khác Incident.
5. Threat khác Risk.
6. Attack surface không phải vulnerability list.
7. Public endpoint không mặc nhiên vulnerable.
8. Internal endpoint không mặc nhiên safe.
9. Dependency presence không chứng minh reachability.
10. Reachability không chứng minh exploitability.
11. Vulnerability match không chứng minh compromise.
12. Threat-intel match không chứng minh attack.
13. Attack path không chứng minh successful attack.
14. Posture snapshot phải versioned.
15. Posture snapshot phải có timestamp.
16. Asset identity phải stable.
17. Resource identity phải stable.
18. Asset ownership phải explicit.
19. Cross-tenant asset edge phải authorization-aware.
20. Security graph phải giữ provenance.
21. Security graph phải hỗ trợ temporal state.
22. Configuration drift phải phân biệt desired/observed.
23. Policy drift phải phân biệt desired/observed.
24. Dependency drift phải phân biệt lock state/runtime state.
25. Identity drift phải có evidence.
26. Capability drift phải có evidence.
27. Deployment drift phải có evidence.
28. Control existence không chứng minh effectiveness.
29. Control effectiveness phải có evidence.
30. Missing evidence = Unknown.
31. Stale evidence không phải current evidence.
32. Expired evidence không phải current evidence.
33. Security score universal không tồn tại trong core.
34. Severity là policy-defined.
35. Risk treatment là policy-defined.
36. Risk acceptance thuộc governance.
37. Exception phải scoped.
38. Exception phải expirable.
39. Exception phải auditable.
40. Mitigation không mặc nhiên resolve vulnerability.
41. Compensating control phải được ghi nhận.
42. Residual exposure không được ẩn.
43. Remediation phải versioned.
44. Remediation phải idempotent khi cần.
45. Irreversible remediation phải chịu approval policy.
46. Security analysis không tự sửa production.
47. Security analysis không tự cấp authority.
48. Security graph không được tạo ambient authority.
49. Threat intelligence là external input.
50. Threat intelligence phải có provenance.
51. Threat intelligence phải có freshness.
52. Threat intelligence conflict phải được giữ.
53. Indicator không phải proof.
54. Indicator expiry phải explicit.
55. Vulnerability source phải explicit.
56. Affected version range phải explicit.
57. Fixed version phải explicit nếu biết.
58. Reachability analysis phải target-specific.
59. Compiler reachability không chứng minh runtime reachability tuyệt đối.
60. Dynamic loading phải được biểu diễn.
61. Reflection/dynamic dispatch phải được biểu diễn khi ảnh hưởng analysis.
62. FFI boundary phải được biểu diễn.
63. Plugin boundary phải được biểu diễn.
64. Tool boundary phải được biểu diễn.
65. Model boundary phải được biểu diễn.
66. Workflow boundary phải được biểu diễn.
67. Capability delegation phải giữ lineage.
68. Revocation phải có effective time.
69. Expired authority không được tính là active.
70. Blast radius là potential impact.
71. Potential impact không phải actual impact.
72. Attack surface inventory phải incremental.
73. Incremental result phải phụ thuộc graph version.
74. Rule version phải là cache input.
75. Policy version phải là cache input.
76. Threat-intel version phải là cache input.
77. Cache stale không được bypass freshness.
78. Posture diff phải giữ old/new provenance.
79. Asset removal không được xóa historical evidence.
80. Finding resolution không được xóa historical exposure.
81. Incident closure không được xóa posture history.
82. Accepted risk không phải resolved finding.
83. False positive không phải deleted finding.
84. Security exception không được xóa underlying finding.
85. Security posture phải liên kết evidence.
86. Evidence phải liên kết source.
87. Source phải có identity.
88. Transformation phải có identity.
89. Derived claim phải phân biệt raw observation.
90. AI analysis phải phân biệt inference.
91. AI recommendation không phải control decision.
92. AI cannot override governance.
93. Security control-plane phải tách data-plane.
94. Security graph không phải mandatory application runtime.
95. Security graph storage phải explicit.
96. Security telemetry không được hidden.
97. Security scheduler không được hidden.
98. Security network access không được hidden.
99. Security analysis phải chịu resource budget.
100. Security analysis phải chống graph explosion.
101. Recursive dependency graph phải terminate.
102. Cyclic dependency phải được biểu diễn.
103. Graph query phải có limit.
104. Large graph query phải có pagination/streaming.
105. Multi-tenant graph query phải enforce isolation.
106. Sensitive graph edges phải ACL-aware.
107. Credential identities không được expose secret material.
108. Secret material không được lưu trong posture metadata.
109. Security findings phải có lifecycle.
110. Finding lifecycle phải auditable.
111. Control changes phải auditable.
112. Baseline changes phải auditable.
113. Threat-intel updates phải auditable.
114. Asset identity changes phải auditable.
115. Ownership changes phải auditable.
116. Capability changes phải auditable.
117. Exposure changes phải auditable.
118. Deployment changes phải auditable.
119. Model changes phải auditable.
120. Tool changes phải auditable.
121. Agent changes phải auditable.
122. Workflow changes phải auditable.
123. Package changes phải auditable.
124. Security posture must support offline evidence where configured.
125. Reproducible analysis phải giữ analysis manifest.
126. Analysis result phải gắn compiler/tool version khi compiler-derived.
127. Security analyzer không được giả định một platform universal.
128. Target-specific behavior phải được giữ.
129. OS security behavior phải được giữ.
130. Hardware capability phải được giữ.
131. GPU/device exposure phải được giữ.
132. Network topology phải có provenance.
133. Distributed graph phải chịu eventual consistency.
134. Stale membership không được tạo false authority.
135. Clock uncertainty phải được biểu diễn.
136. Temporal queries phải phân biệt event time/observation time.
137. Posture history phải immutable theo policy.
138. Security evidence deletion phải governance-controlled.
139. Security retention phải explicit.
140. Security archive phải preserve provenance.
141. Security graph export phải preserve identity.
142. Security graph import phải verify provenance.
143. Imported security data là untrusted.
144. Imported controls không tự động become active.
145. Imported threat intelligence không tự động become authoritative.
146. Imported findings không tự động become incidents.
147. Imported posture không tự động become current state.
148. External scanner results phải được phân biệt.
149. Scanner result không phải ground truth.
150. Scanner failure phải observable.
151. Scanner coverage phải observable.
152. Sampling phải record scope.
153. Incomplete inventory phải biểu diễn uncertainty.
154. Unknown assets không được coi là absent.
155. Unknown exposure không được coi là closed.
156. Unknown control effectiveness không được coi là satisfied.
157. Security baseline phải versioned.
158. Baseline phải scoped.
159. Baseline không phải universal standard.
160. Project policy có thể định nghĩa stricter requirements.
161. Security posture không được ép mọi application dùng cùng policy.
162. Security analysis phải composable.
163. Security controls phải composable.
164. Security findings phải mergeable với provenance.
165. Finding split phải giữ lineage.
166. Finding merge phải giữ lineage.
167. Exposure changes phải trigger configurable analysis.
168. Deployment changes có thể trigger analysis.
169. Package changes có thể trigger analysis.
170. Model changes có thể trigger analysis.
171. Tool changes có thể trigger analysis.
172. Policy changes có thể trigger analysis.
173. Capability changes có thể trigger analysis.
174. Threat-intel updates có thể trigger analysis.
175. Incident feedback có thể trigger analysis.
176. Feedback không được tự sửa authority.
177. Security recommendations phải có evidence.
178. Recommendation confidence không phải authorization.
179. Remediation proposal phải explicit.
180. Remediation execution phải explicit.
181. Dry-run không được có external side effects.
182. Simulation không phải production evidence.
183. Security graph phải support deterministic replay khi configured.
184. Analysis phải chịu malformed metadata.
185. Analysis phải chịu malicious package metadata.
186. Analysis phải chịu malicious model metadata.
187. Analysis phải chịu malicious tool metadata.
188. Analysis phải chịu adversarial graph input.
189. Analysis phải giới hạn resource.
190. Security posture engine không được yêu cầu GC.
191. Không yêu cầu borrow checker runtime.
192. Không yêu cầu VM.
193. Không yêu cầu LLVM/GCC/Clang.
194. Có thể compile thành native artifact.
195. Không tạo hidden runtime dependencies.
196. Không tự động upload security data.
197. Không tự động expose organizational topology.
198. Không tự động share cross-tenant intelligence.
199. **Final invariant:** Axiom phải cung cấp một Security Operations Control Plane và Security Posture Graph có khả năng lập inventory, theo dõi attack surface, dependency/capability/exposure drift, threat intelligence, vulnerability context, controls, blast radius, remediation và continuous verification với provenance và temporal semantics; nó phải phân biệt evidence, inference, exposure, threat, finding và incident, không biến AI thành security authority và không áp đặt hidden security runtime lên ứng dụng.

**BOOTSTRAP-548: LOCKED.**

---

# BOOTSTRAP-549 — AI SECURITY ARCHITECTURE REVIEW, SECURE-BY-CONSTRUCTION ANALYSIS, TRUST BOUNDARY COMPILER & SECURITY POLICY VERIFICATION

**Trạng thái: NEXT**

548 đã xây được **security posture/control plane**. Bước kế tiếp hợp lý là đưa một phần security analysis **xuống compiler/semantic layer**, để Axiom có thể phát hiện một số vấn đề ngay khi code/model/tool/workflow được xây dựng thay vì chờ deployment.

Kiến trúc dự kiến:

```text
Axiom Source / Model / Tool / Workflow
                 │
                 ▼
          Semantic Security Model
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
   Trust Flow  Authority  Data Flow
       │         │         │
       └─────────┼─────────┘
                 ▼
        Security Constraint IR
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
    Prove      Detect     Unknown
       │         │         │
       └─────────┼─────────┘
                 ▼
        Security Diagnostics
                 │
                 ▼
       Policy / Evidence 546
```

Task này sẽ tập trung vào:

- trust boundary;
- taint/data-flow security;
- capability-flow analysis;
- authority amplification;
- confused deputy;
- secret-flow analysis;
- unsafe boundary analysis;
- FFI security contracts;
- tool/agent/workflow authority;
- network/file/process security flow;
- compile-time security constraints;
- security-specific type/effect metadata;
- policy-to-code verification;
- `Proven / Violated / RuntimeChecked / Unknown`;
- secure-by-construction APIs;
- security diagnostics dành cho AI;
- proof provenance;
- integration `478/479/445/490/545/546/547/548`;
- và đặc biệt: **không biến security analyzer thành một borrow checker thứ hai hoặc làm chậm mọi chương trình không sử dụng security features**.