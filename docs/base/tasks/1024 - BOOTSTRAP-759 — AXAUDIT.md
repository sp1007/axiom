# BOOTSTRAP-759 — AXAUDIT

**Title:** Native Security Audit, Event Provenance, Tamper-Evident Log, Compliance Evidence & Security Telemetry Runtime 5.0  
**Namespace:** `AXAUDIT`  
**Phase:** Axiom Civilization Runtime / Native Audit & Evidence Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET 5.0**

---

## 1. Mục tiêu

`AXAUDIT` là **evidence plane** của Axiom.

Nó ghi nhận các sự kiện có giá trị về:

- security;
- authentication;
- authorization;
- capability;
- policy;
- process;
- memory;
- IPC;
- network;
- storage;
- device;
- application;
- configuration;
- administrative action;
- runtime failure;
- security transition.

Kiến trúc:

```text id="audit01"
AXAUTH ───────────┐
AXTRUST ──────────┤
AXCAPABILITY ─────┤
AXPOLICY ─────────┤
AXSECURITY ───────┤
AXPROCESS ────────┤
AXMEMORY ─────────┤
AXIPC ────────────┤
AXNETWORK ────────┤
AXSTORAGE ────────┤
AXDEVICE ─────────┤
AXAPPLICATION ────┤
                   ▼
                AXAUDIT
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
    events     provenance    evidence
       │           │           │
       └───────────┼───────────┘
                   ▼
          tamper-evident log
                   │
                   ▼
             AXSTORAGE
```

---

# 2. Strong boundary

### AXAUDIT sở hữu

- audit event model;
- event collection;
- event normalization;
- provenance;
- correlation;
- sequence numbers;
- tamper-evident chaining;
- signed checkpoints;
- audit streams;
- retention metadata;
- audit filtering;
- audit queries;
- evidence bundles;
- audit replay;
- audit simulation;
- audit integrity verification;
- audit export;
- audit telemetry.

### AXAUDIT không sở hữu

- authorization;
- authentication;
- cryptography;
- policy decisions;
- process lifecycle;
- storage semantics;
- network transport;
- security enforcement.

Đặc biệt:

> **AXAUDIT ghi nhận security decision nhưng không được tạo ra hoặc thay đổi security decision.**

---

# 3. Audit ≠ telemetry

Axiom phân biệt:

```text
AUDIT
    = security/accountability evidence

TELEMETRY
    = operational observation

TRACE
    = execution/debug timing information

LOG
    = application/system diagnostic text
```

Một event có thể được đưa vào nhiều pipeline, nhưng semantics không được trộn lẫn.

---

# 4. Audit event

Core model:

```text id="audit02"
audit_event {
    event_id
    event_type
    timestamp
    monotonic_time
    sequence
    source
    principal
    session
    process
    security_domain
    resource
    operation
    decision
    reason
    policy_version
    capability_epoch
    resource_generation
    correlation_id
    parent_event_id
    payload
    classification
}
```

---

# 5. Event identity

Mỗi event có:

```text id="audit03"
event_id
```

`event_id` không được dựa đơn thuần vào timestamp.

Có thể dùng:

```text
node_id
+
boot_epoch
+
counter
```

hoặc equivalent generation-safe scheme.

---

# 6. Event ordering

Audit event có:

```text id="audit04"
sequence
```

Sequence chỉ đảm bảo ordering trong phạm vi được định nghĩa.

Không được giả định:

```text global sequence
```

trên toàn distributed system nếu không có distributed ordering mechanism.

---

# 7. Timestamp

Mỗi event nên chứa:

```text id="audit05"
wall_clock
monotonic_clock
```

Wall clock phục vụ correlation bên ngoài.

Monotonic clock phục vụ duration/order tương đối.

---

# 8. Clock uncertainty

Nếu wall clock chưa synchronized:

```text id="audit06"
timestamp_quality = UNSYNCHRONIZED
```

Không được giả định timestamp tuyệt đối chính xác.

---

# 9. Event source

```text id="audit07"
audit_source {
    subsystem
    component
    instance
}
```

Ví dụ:

```text
AXSECURITY
AXAUTH
AXPROCESS
```

---

# 10. Security event

Baseline:

```text id="audit08"
SECURITY_CHECK
SECURITY_ALLOW
SECURITY_DENY
CAPABILITY_ISSUED
CAPABILITY_DELEGATED
CAPABILITY_ATTENUATED
CAPABILITY_REVOKED
POLICY_ACTIVATED
POLICY_REVOKED
AUTH_SUCCESS
AUTH_FAILURE
SESSION_CREATED
SESSION_REVOKED
SANDBOX_ENTERED
SANDBOX_RESTRICTED
DOMAIN_TRANSITION
```

---

# 11. Process events

```text id="audit09"
PROCESS_CREATED
PROCESS_STARTED
PROCESS_STOP_REQUESTED
PROCESS_TERMINATED
PROCESS_CRASHED
PROCESS_RESTARTED
PROCESS_QUARANTINED
PROCESS_DEBUG_ATTEMPT
```

---

# 12. Resource events

```text id="audit10"
RESOURCE_CREATED
RESOURCE_OPENED
RESOURCE_CLOSED
RESOURCE_DELETED
RESOURCE_PERMISSION_CHANGED
RESOURCE_LABEL_CHANGED
RESOURCE_EXPORTED
RESOURCE_IMPORTED
```

---

# 13. Administrative events

```text id="audit11"
ADMIN_POLICY_CHANGE
ADMIN_SECURITY_PROFILE_CHANGE
ADMIN_CAPABILITY_CHANGE
ADMIN_DOMAIN_CHANGE
ADMIN_SESSION_REVOKE
ADMIN_PROCESS_QUARANTINE
ADMIN_CONFIGURATION_CHANGE
```

---

# 14. Audit severity

Severity:

```text id="audit12"
DEBUG
INFO
NOTICE
WARNING
ERROR
SECURITY
CRITICAL
```

Severity là telemetry/audit classification, không phải security decision.

---

# 15. Event classification

Event có thể mang:

```text id="audit13"
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
SECRET
```

Classification quyết định retention/export/access policy.

Không được coi classification là encryption.

---

# 16. Payload model

Payload có hai dạng:

```text id="audit14"
STRUCTURED
OPAQUE
```

Structured payload được schema hóa.

Opaque payload chỉ dùng cho subsystem-specific diagnostics.

---

# 17. Structured events

Ví dụ:

```text id="audit15"
security.deny {
    principal_id
    resource_id
    operation
    reason_code
    policy_version
}
```

Không dùng text parsing để phục hồi semantics.

---

# 18. Schema

Mỗi event schema có:

```text id="audit16"
schema_id
schema_version
field_definitions
compatibility
```

Schema evolution phải explicit.

---

# 19. Forward compatibility

Reader mới có thể đọc event cũ.

Reader cũ phải xử lý unknown fields mà không crash.

---

# 20. Provenance

`audit_provenance`:

```text id="audit17"
audit_provenance {
    origin_event
    parent_event
    causation_id
    correlation_id
    actor
    source_component
    execution_context
}
```

Phân biệt:

```text correlation
≠
causation
```

---

# 21. Correlation

Ví dụ:

```text id="audit18"
AUTH_SUCCESS
      │
      ▼
SESSION_CREATED
      │
      ▼
FILE_ACCESS
      │
      ▼
AUDIT_EXPORT
```

Các event có cùng:

```text
correlation_id
```

nhưng vẫn giữ event identity riêng.

---

# 22. Causation

Nếu event B được tạo trực tiếp bởi event A:

```text id="audit19"
B.causation_id = A.event_id
```

Điều này tạo causal graph.

---

# 23. Audit graph

AXAUDIT hỗ trợ:

```text id="audit20"
event
 ↓
cause
 ↓
effect
```

Có thể dùng cho forensic reconstruction.

---

# 24. Tamper-evident chain

Audit record có:

```text id="audit21"
previous_hash
event_hash
```

Conceptual:

```text
E1 ─hash─> H1
           │
E2 ────────┘
   previous_hash = H1

E3
   previous_hash = H2
```

Thay đổi event giữa chuỗi sẽ phá integrity chain.

---

# 25. Hash algorithm

AXAUDIT sử dụng AXCRYPTO.

Không tự implement cryptographic primitive.

Algorithm identifier phải nằm trong chain metadata.

---

# 26. Chain segments

Không bắt buộc một chain vô hạn.

Có thể chia:

```text id="audit22"
segment_001
segment_002
segment_003
```

Mỗi segment có:

```text
start_event
end_event
previous_segment_commitment
```

---

# 27. Signed checkpoint

Định kỳ:

```text id="audit23"
audit_checkpoint {
    segment_id
    last_sequence
    root_hash
    event_count
    timestamp
    signature
}
```

Signature dùng AXCRYPTO.

---

# 28. Checkpoint purpose

Checkpoint cho phép chứng minh:

```text id="audit24"
"chuỗi audit tại thời điểm T có commitment H"
```

Không có nghĩa rằng mọi event đều hợp lệ về mặt nội dung.

Integrity ≠ truth.

---

# 29. Audit integrity verification

API:

```text id="audit25"
audit_verify_chain()
audit_verify_segment()
audit_verify_checkpoint()
```

Kết quả:

```text
VALID
BROKEN
INCOMPLETE
UNKNOWN
```

---

# 30. Append-only mode

Security audit quan trọng có thể chạy:

```text id="audit26"
APPEND_ONLY
```

Trong mode này event không được update/delete.

Retention chỉ thực hiện bằng explicit archival/expiration mechanism.

---

# 31. Audit buffer

Hot path:

```text id="audit27"
producer
   ↓
per-core ring buffer
   ↓
batch
   ↓
audit writer
```

Security decision không được block lâu chỉ vì audit sink chậm, trừ khi policy yêu cầu mandatory synchronous audit.

---

# 32. Loss policy

Mỗi audit stream có:

```text id="audit28"
LOSSLESS
BOUNDED_LOSS
BEST_EFFORT
```

Security-critical stream nên sử dụng `LOSSLESS` hoặc policy xác định hành vi khi capacity cạn.

---

# 33. Full buffer

Nếu `LOSSLESS`:

```text id="audit29"
buffer full
   ↓
backpressure / reserved emergency buffer
```

Nếu không thể đảm bảo audit:

```text
policy → DENY / DEGRADE / FAIL
```

Không tự ý drop security events.

---

# 34. Emergency audit buffer

AXAUDIT nên giữ một reserved buffer:

```text id="audit30"
emergency_security_buffer
```

dành cho:

- security deny;
- crash;
- privilege transition;
- revocation;
- critical administrative actions.

---

# 35. Asynchronous audit

Normal events:

```text id="audit31"
producer
   ↓
enqueue
   ↓
return
```

Không block application.

---

# 36. Synchronous audit

Một security profile có thể yêu cầu:

```text id="audit32"
AUDIT_BEFORE_OPERATION
AUDIT_AFTER_OPERATION
```

Flow:

```text
prepare audit
      ↓
commit audit
      ↓
operation
```

hoặc:

```text
operation
      ↓
commit audit
```

Semantics phải explicit.

---

# 37. Audit transaction

Một protected operation có thể tạo:

```text id="audit33"
audit_transaction {
    begin_event
    completion_event
    outcome
}
```

Nếu operation crash giữa chừng:

```text
INCOMPLETE
```

thay vì giả định success.

---

# 38. Audit queries

AXAUDIT hỗ trợ indexed query:

```text id="audit34"
audit_query {
    time_range
    event_type
    principal
    process
    resource
    operation
    decision
    correlation_id
}
```

---

# 39. Query execution

Query path:

```text id="audit35"
query
 ↓
index
 ↓
segment selection
 ↓
filter
 ↓
event decode
 ↓
result
```

Không scan toàn bộ audit store nếu index có thể loại bỏ segment.

---

# 40. Indexes

Có thể index theo:

```text
timestamp
event_type
principal
session
process
resource
operation
correlation_id
```

Không bắt buộc index mọi field.

---

# 41. Retention

Retention policy:

```text id="audit36"
retention_policy {
    minimum_age
    maximum_age
    minimum_events
    archive_target
    deletion_rule
}
```

Security policy có thể override ordinary retention.

---

# 42. Legal/compliance boundary

AXAUDIT cung cấp primitives cho retention/evidence.

Nó **không định nghĩa luật pháp** hoặc tự tuyên bố rằng một audit log đáp ứng một quy định pháp lý cụ thể.

Compliance semantics thuộc higher-level systems.

---

# 43. Evidence bundle

```text id="audit37"
evidence_bundle {
    bundle_id
    events[]
    schemas[]
    checkpoints[]
    provenance
    integrity_metadata
}
```

Bundle dùng để export một tập evidence có context đầy đủ.

---

# 44. Evidence snapshot

Snapshot phải chứa:

```text
event data
+
schema versions
+
policy references
+
integrity commitments
```

để reader tương lai có thể diễn giải event.

---

# 45. Evidence chain

```text id="audit38"
event
 ↓
causation
 ↓
checkpoint
 ↓
evidence bundle
 ↓
signature
```

Mỗi bước có identity riêng.

---

# 46. Audit export

Export formats có thể gồm:

```text id="audit39"
AXAUDIT_NATIVE
JSON
CBOR
BINARY
TEXT
```

Native binary là canonical format.

---

# 47. Canonical encoding

Audit native format phải:

- deterministic;
- versioned;
- length-bounded;
- endian-defined;
- schema-aware.

AXCODEC chịu encoding primitives.

---

# 48. Compression

Audit segments có thể compress:

```text id="audit40"
events
 ↓
AXCODEC compression
 ↓
storage
```

Compression không được phá tamper-evidence semantics.

Hash nên được xác định rõ là hash trên:

```text canonical uncompressed event representation
```

hoặc canonical stored representation.

Không được để implementation tự chọn.

**Baseline:** hash trên canonical event representation trước compression.

---

# 49. Encryption

Confidential audit storage có thể dùng AXCRYPTO.

Encryption:

```text id="audit41"
confidentiality
```

Tamper evidence:

```text
integrity
```

là hai property riêng.

---

# 50. Key rotation

Audit encryption key có thể rotate.

Chain integrity không được phụ thuộc vào một encryption key duy nhất.

---

# 51. Audit access control

Đọc audit cũng là protected operation:

```text id="audit42"
AUDIT.READ
AUDIT.EXPORT
AUDIT.DELETE
AUDIT.ADMIN
```

AXSECURITY enforce.

---

# 52. Audit self-protection

Audit process không được tự cấp:

```text
AUDIT.ADMIN
```

cho chính mình.

Audit writer chỉ có authority tối thiểu:

```text
APPEND
CHECKPOINT
```

nếu architecture cho phép.

---

# 53. Separation of duties

Có thể tách:

```text
event producer
audit writer
audit reader
audit administrator
checkpoint signer
```

thành các authority khác nhau.

---

# 54. Audit reader isolation

Một reader không nên có quyền:

```text
modify
delete
rewrite
```

audit events chỉ vì có:

```text
AUDIT.READ
```

---

# 55. Audit administrator

`AUDIT.ADMIN` có thể:

- configure streams;
- configure retention;
- configure indexes;
- rotate storage;
- activate checkpoints.

Không tự động được quyền sửa historical evidence.

---

# 56. Historical immutability

Historical event đã committed:

```text
READ ONLY
```

Modification tạo event mới:

```text
CORRECTION
```

không rewrite event cũ.

---

# 57. Corrections

Nếu event sai metadata:

```text id="audit43"
original event
      ↓
CORRECTION event
```

Correction chứa:

```text
target_event_id
correction_reason
corrected_fields
actor
```

---

# 58. Deletion

Nếu retention yêu cầu deletion:

```text id="audit44"
logical retention expiration
```

phải tạo evidence rằng:

```text
segment X expired under policy Y
```

nếu policy yêu cầu.

Không giả vờ rằng event chưa từng tồn tại.

---

# 59. Privacy minimization

Audit không nên thu thập dữ liệu không cần thiết.

Default:

```text id="audit45"
metadata > payload
```

Chỉ record sensitive payload khi policy yêu cầu.

---

# 60. Secret redaction

Các trường như:

```text
password
private_key
session_secret
access_token
raw credential
```

không được ghi plaintext.

AXAUDIT có typed secret classification để tự động reject/redact.

---

# 61. Redaction

```text id="audit46"
SECRET
 ↓
REDACTED
```

hoặc:

```text
SECRET
 ↓
HASHED_IDENTIFIER
```

tùy field policy.

---

# 62. PII boundary

AXAUDIT hỗ trợ field classification:

```text
NORMAL
SENSITIVE
SECRET
PERSONAL
```

nhưng không tự quyết định nghĩa pháp lý của PII.

---

# 63. Audit sampling

Operational telemetry có thể sampling.

Security audit không được sampling nếu event được policy đánh dấu mandatory.

---

# 64. Event filtering

Producer có thể khai báo:

```text
audit_emit(level, event)
```

Runtime filter theo stream profile.

Security-critical events không thể bị application-level filter nếu mandatory policy yêu cầu.

---

# 65. Multi-tenant audit

Audit event có:

```text id="audit47"
tenant_id
```

khi relevant.

Tenant reader không được đọc event của tenant khác nếu AXSECURITY không cấp authority.

---

# 66. Cross-process audit

Process có thể gửi event tới AXAUDIT qua:

```text
AXIPC
```

Nhưng event phải authenticate source.

Không tin:

```text
claimed_process_id
```

từ untrusted payload.

---

# 67. Source authentication

Audit ingestion có thể bind:

```text id="audit48"
process identity
security domain
session
```

với producer channel.

---

# 68. Anti-spoofing

Một process không được emit:

```text
principal = SYSTEM
```

chỉ bằng cách set field đó.

Identity của producer phải đến từ trusted context.

---

# 69. Kernel/privileged events

Một số events có source:

```text id="audit49"
KERNEL
HYPERVISOR
SECURE_RUNTIME
```

Axiom phải giữ source authenticity metadata.

---

# 70. Crash audit

Crash event:

```text id="audit50"
PROCESS_CRASHED {
    process_id
    fault_class
    instruction_context_ref
    dump_ref
    restart_state
}
```

Không lưu raw memory vào audit event.

Core dump thuộc AXPROCESS/diagnostics.

---

# 71. Security violation

Ví dụ:

```text id="audit51"
SECURITY_VIOLATION {
    process
    operation
    resource
    reason
    enforcement_point
}
```

---

# 72. Audit severity escalation

Repeated events có thể tạo aggregate:

```text id="audit52"
event_count
window
threshold
```

Nhưng AXAUDIT không tự quyết định quarantine/kill.

AXSECURITY hoặc higher-level monitoring thực hiện action.

---

# 73. Audit analytics

AXAUDIT có thể cung cấp:

```text
count
rate
timeline
correlation
graph
aggregation
```

Không biến thành full SIEM bắt buộc trong core.

---

# 74. Alert boundary

`AXAUDIT` có thể phát:

```text
AUDIT_ALERT
```

nhưng alert không tự động thay đổi authority.

---

# 75. Event subscriptions

```text id="audit53"
audit_subscribe(filter)
```

Có thể nhận:

- security denies;
- auth failures;
- process crashes;
- policy changes;
- capability revocations.

Subscription có backpressure.

---

# 76. Audit stream

```text id="audit54"
audit_stream {
    stream_id
    schema
    filter
    durability
    retention
    integrity
    classification
}
```

---

# 77. Stream lifecycle

```text id="audit55"
CREATED
   ↓
CONFIGURING
   ↓
ACTIVE
   ↓
DRAINING
   ↓
SEALED
   ↓
ARCHIVED
```

Failure states:

```text
DEGRADED
FAILED
CORRUPTED
```

---

# 78. Segment lifecycle

```text id="audit56"
OPEN
 ↓
SEALED
 ↓
CHECKPOINTED
 ↓
ARCHIVED
 ↓
EXPIRED
```

---

# 79. Backpressure

Audit stream có:

```text
BLOCK
BUFFER
DROP_NONCRITICAL
FAIL
```

`DROP_NONCRITICAL` chỉ áp dụng cho events explicitly marked droppable.

---

# 80. Audit writer

Writer có thể batch:

```text
event × N
 ↓
canonical encode
 ↓
hash
 ↓
append
 ↓
checkpoint
```

Giảm syscall/storage overhead.

---

# 81. Group commit

Nhiều events có thể commit cùng batch.

Mỗi event vẫn giữ identity và sequence riêng.

---

# 82. Crash consistency

Audit writer phải đảm bảo:

```text
partial record
```

không được nhìn thấy như committed event hợp lệ.

Storage format cần record boundaries/checksums.

---

# 83. Recovery

Startup:

```text
open segment
 ↓
scan last valid record
 ↓
detect incomplete tail
 ↓
truncate/recover
 ↓
emit recovery event
```

Không sửa historical committed records.

---

# 84. Corruption handling

Nếu chain bị broken:

```text
CORRUPTED
```

Không silently continue như không có vấn đề.

Có thể mở segment mới với:

```text
previous_segment_status = CORRUPTED
```

---

# 85. Distributed audit

Các node có:

```text
node_id
boot_epoch
sequence
```

Global ordering không mặc định.

Distributed causal graph dùng:

```text
correlation_id
causation_id
logical_clock
```

nếu subsystem cần.

---

# 86. Remote audit sink

AXAUDIT có thể export qua:

```text
AXNETWORK
AXIPC
AXSTREAM
```

Nhưng transport thuộc các subsystem tương ứng.

---

# 87. Remote delivery

Delivery semantics:

```text
AT_MOST_ONCE
AT_LEAST_ONCE
```

Exactly-once không phải baseline.

Event ID cho phép receiver deduplicate.

---

# 88. Audit acknowledgment

Remote sink có thể trả:

```text
ack(event_id)
```

nhưng local committed status không được phụ thuộc vào remote ACK trừ khi stream profile yêu cầu.

---

# 89. Audit replication

Replication có thể:

```text
PRIMARY
SECONDARY
ARCHIVE
```

Integrity chain phải được giữ.

---

# 90. Audit recovery point

Stream có:

```text
last_committed_sequence
last_checkpoint
last_replicated_sequence
```

cho recovery/replication.

---

# 91. Deterministic simulation

Simulation phải hỗ trợ:

- event ordering;
- dropped events;
- delayed sink;
- storage failure;
- clock changes;
- process crash;
- chain corruption;
- duplicate remote delivery;
- checkpoint interruption.

---

# 92. Audit replay

Replay không được re-execute security actions.

Nó chỉ tái tạo:

```text
event graph
timeline
derived state
```

---

# 93. Forensic replay

Input:

```text
evidence_bundle
```

Output:

```text
timeline
causal_graph
integrity_report
```

Không tự kết luận motive/intent.

---

# 94. Audit derived state

Có thể reconstruct:

```text
session lifecycle
capability lifecycle
policy activation history
process lifecycle
security-domain transitions
```

từ events.

---

# 95. Event sourcing boundary

AXAUDIT **không phải event-sourcing database chung của Axiom**.

Một subsystem chỉ sử dụng audit events để accountability/evidence.

Canonical application state vẫn thuộc subsystem sở hữu state.

---

# 96. Compiler integration

Compiler có thể generate:

```text
@audit
@audit(category = security)
@audit(redact = true)
```

metadata.

Compiler không được bypass runtime audit requirement.

---

# 97. Compile-time audit metadata

Type/function có thể khai báo:

```text id="audit57"
audit_event_type
security_class
sensitive_fields
```

AXAUDIT runtime dùng metadata này để giảm reflection.

---

# 98. Zero-cost disabled telemetry

Operational debug telemetry có thể compile out:

```text id="audit58"
@if_debug
```

Nhưng mandatory security audit không được compile out bằng build flag thông thường.

---

# 99. Performance target

Audit path phải hướng tới:

```text
small event:
    fixed-size allocation / stack record
    lock-free enqueue
    batch persistence
```

Không heap allocation bắt buộc cho mỗi event.

---

# 100. Per-core buffers

```text id="audit59"
CPU 0 → ring 0
CPU 1 → ring 1
CPU 2 → ring 2
...
```

Writer merge theo event metadata.

---

# 101. NUMA

Server lớn:

```text
NUMA node
 └── local audit buffers
       └── local writer
```

Cross-NUMA movement chỉ xảy ra trong persistence/aggregation path khi cần.

---

# 102. Memory bounds

Mọi audit stream có:

```text
max_memory
max_event_size
max_queue_depth
max_segment_size
```

Không được để audit subsystem tự làm cạn memory hệ thống.

---

# 103. Audit priority

Events:

```text
CRITICAL
SECURITY
NORMAL
DEBUG
```

Queue pressure ưu tiên giữ critical/security.

---

# 104. Security event reservation

Một stream có thể reserve:

```text
critical_capacity
security_capacity
```

để ordinary telemetry không chiếm hết buffer.

---

# 105. Native API

Baseline:

```text id="audit60"
audit_init()
audit_shutdown()

audit_event_create()
audit_event_set()
audit_event_add_field()
audit_event_commit()

audit_emit()
audit_emit_security()
audit_emit_admin()

audit_stream_create()
audit_stream_configure()
audit_stream_activate()
audit_stream_pause()
audit_stream_seal()
audit_stream_archive()

audit_query_create()
audit_query_execute()
audit_query_next()
audit_query_close()

audit_checkpoint_create()
audit_checkpoint_verify()

audit_verify_chain()
audit_verify_segment()
audit_verify_bundle()

audit_bundle_create()
audit_bundle_add_event()
audit_bundle_finalize()
audit_bundle_export()
audit_bundle_import()

audit_subscribe()
audit_unsubscribe()

audit_flush()
audit_sync()

audit_get_stats()
audit_get_stream_stats()

audit_start_trace()
audit_stop_trace()

audit_simulate()
audit_replay()

audit_get_capabilities()
```

---

# 106. Native ABI

```text id="audit61"
AXAUDIT_ABI_1
```

Core ABI objects:

```text
audit_event_handle
audit_stream_handle
audit_query_handle
audit_bundle_handle
audit_checkpoint_handle
audit_subscription_handle
```

Opaque handles, generation-safe.

---

# 107. Event ABI

```text id="audit62"
audit_event_header {
    version
    event_type
    event_size
    event_id
    sequence
    source_id
    timestamp
    flags
}
```

Payload follows canonical schema.

---

# 108. Error model

Baseline:

```text id="audit63"
AUDIT_INVALID_EVENT
AUDIT_SCHEMA_MISMATCH
AUDIT_EVENT_TOO_LARGE
AUDIT_QUEUE_FULL
AUDIT_STORAGE_FULL
AUDIT_STORAGE_FAILURE
AUDIT_CHECKPOINT_FAILURE
AUDIT_INTEGRITY_FAILURE
AUDIT_CORRUPTED
AUDIT_PERMISSION_DENIED
AUDIT_STREAM_CLOSED
AUDIT_STREAM_FAILED
AUDIT_QUERY_INVALID
AUDIT_EXPORT_FAILURE
AUDIT_IMPORT_FAILURE
AUDIT_VERSION_UNSUPPORTED
AUDIT_TIMEOUT
AUDIT_CANCELLED
AUDIT_REPLAY_INVALID
AUDIT_SIMULATION_INVALID
```

---

# 109. Canonical flow — security deny

```text id="audit64"
operation
    ↓
AXSECURITY
    ↓
DENY
    ↓
AXAUDIT
    ↓
SECURITY_DENY event
    ↓
per-core buffer
    ↓
batch
    ↓
canonical encode
    ↓
hash
    ↓
append
```

---

# 110. Canonical flow — capability revoke

```text id="audit65"
AXCAPABILITY
      ↓
REVOKE
      ↓
AXSECURITY
      ↓
enforcement state update
      ↓
AXAUDIT
      ↓
CAPABILITY_REVOKED
```

---

# 111. Canonical flow — authentication

```text id="audit66"
AXAUTH
  │
  ├── AUTH_SUCCESS
  │
  └── SESSION_CREATED
          │
          ▼
       AXAUDIT
```

Passwords/private keys/session secrets không được đưa vào events.

---

# 112. Canonical flow — policy change

```text id="audit67"
policy compile
     ↓
policy validate
     ↓
policy activate
     ↓
AXPOLICY
     ↓
AXSECURITY
     ↓
AXAUDIT
     ↓
POLICY_ACTIVATED
```

Event chứa:

```text
policy_id
policy_version
activation_id
actor
```

---

# 113. Canonical flow — process crash

```text id="audit68"
AXPROCESS
    ↓
PROCESS_CRASHED
    ↓
AXAUDIT
    ├── process identity
    ├── fault class
    ├── dump reference
    └── correlation
```

Raw crash dump không nằm trong audit event.

---

# 114. Canonical flow — evidence bundle

```text id="audit69"
query
  ↓
events
  ↓
provenance expansion
  ↓
checkpoint lookup
  ↓
integrity verification
  ↓
bundle
  ↓
canonical encode
  ↓
optional sign
  ↓
export
```

---

# 115. AI boundary

AI được phép:

- tìm event liên quan;
- nhóm event;
- xây timeline;
- xây causal graph;
- phát hiện pattern;
- giải thích reason codes;
- phát hiện audit gaps;
- đề xuất retention/index configuration;
- mô phỏng incident reconstruction.

AI không được:

- sửa historical events;
- xóa evidence;
- giả mạo event source;
- thay đổi security decision;
- tự suppress mandatory audit;
- tự cấp quyền truy cập audit;
- thay đổi checkpoint integrity.

---

# 116. Security boundary

AXAUDIT itself phải chịu:

```text
AXSECURITY
```

Ví dụ:

```text
audit_query
    ↓
AXSECURITY
    ├── AUDIT.READ
    ├── tenant restriction
    └── classification restriction
```

Sau đó mới:

```text
AXAUDIT
```

---

# 117. Audit trust hierarchy

Không phải event nào cũng có cùng evidence strength.

Event metadata có:

```text
source_trust
```

Ví dụ:

```text
KERNEL_ATTESTED
SECURE_RUNTIME
TRUSTED_SERVICE
AUTHENTICATED_PROCESS
UNTRUSTED_INPUT
```

Không được suy luận trust chỉ từ event text.

---

# 118. Event authenticity

Một event có thể có:

```text
producer_signature
```

nếu required.

Signature verification dùng AXCRYPTO.

Không phải mọi event đều cần chữ ký riêng; chain/checkpoint có thể đủ cho local integrity profile.

---

# 119. Evidence confidence

Không dùng một trường:

```text confidence = 0.9
```

để thay thế provenance.

Thay vào đó:

```text
source
integrity
authentication
provenance
verification_status
```

được biểu diễn riêng.

---

# 120. Formal invariants

`AXAUDIT 5.0` định nghĩa tối thiểu 40 invariants:

```text id="audit70"
AUDIT-INV-01   Event ID phải unique trong boot/domain scope đã định nghĩa.
AUDIT-INV-02   Event schema phải versioned.
AUDIT-INV-03   Event type phải xác định trước khi commit.
AUDIT-INV-04   Event committed không được mutate.
AUDIT-INV-05   Event ordering phải có scope rõ ràng.
AUDIT-INV-06   Wall-clock và monotonic-clock không được đánh đồng.
AUDIT-INV-07   Causation và correlation phải là hai trường khác nhau.
AUDIT-INV-08   Producer identity không được lấy từ untrusted payload.
AUDIT-INV-09   Security events mandatory không được application filter bỏ.
AUDIT-INV-10   Secret plaintext không được audit mặc định.
AUDIT-INV-11   Private key không được xuất hiện trong event.
AUDIT-INV-12   Session secret không được xuất hiện trong event.
AUDIT-INV-13   Audit reader không có quyền sửa event.
AUDIT-INV-14   Audit read không mặc định cấp audit admin.
AUDIT-INV-15   Historical correction phải tạo event mới.
AUDIT-INV-16   Chain hash phải được tính trên canonical representation.
AUDIT-INV-17   Compression không được làm thay đổi canonical hash semantics.
AUDIT-INV-18   Checkpoint phải bind vào segment cụ thể.
AUDIT-INV-19   Broken chain phải được phát hiện.
AUDIT-INV-20   Corrupted segment không được silently coi là valid.
AUDIT-INV-21   Partial record không được coi là committed.
AUDIT-INV-22   Stream phải có bounded resource policy.
AUDIT-INV-23   Queue full phải có explicit loss semantics.
AUDIT-INV-24   Mandatory lossless stream không được tự ý drop event.
AUDIT-INV-25   Emergency audit capacity phải không bị ordinary telemetry chiếm hết.
AUDIT-INV-26   Audit subsystem không được tự cấp security authority.
AUDIT-INV-27   Audit không được thay đổi authorization decision.
AUDIT-INV-28   Audit replay không được re-execute security actions.
AUDIT-INV-29   Remote duplicate event phải deduplicate được bằng event identity.
AUDIT-INV-30   Remote delivery semantics phải explicit.
AUDIT-INV-31   Audit export phải giữ schema metadata cần thiết.
AUDIT-INV-32   Evidence bundle phải giữ integrity metadata.
AUDIT-INV-33   Retention không được âm thầm rewrite historical evidence.
AUDIT-INV-34   Deletion/expiration phải có explicit retention semantics.
AUDIT-INV-35   Cross-tenant audit access phải qua AXSECURITY.
AUDIT-INV-36   Audit event không được tự tuyên bố legal compliance.
AUDIT-INV-37   Event provenance phải phân biệt source và claimed actor.
AUDIT-INV-38   Checkpoint verification phải phát hiện tampering.
AUDIT-INV-39   Audit hot path không được bắt buộc heap allocation cho mỗi event.
AUDIT-INV-40   AI không được thay đổi, xóa hoặc giả mạo audit evidence.
```

---

# 121. Definition of Done

`AXAUDIT 5.0` được xem là hoàn tất khi Axiom có:

- canonical audit event model;
- event schemas/versioning;
- event identity;
- sequence semantics;
- wall/monotonic timestamps;
- provenance;
- causation/correlation;
- security events;
- process events;
- resource events;
- administrative events;
- classification;
- secret redaction;
- privacy minimization;
- append-only streams;
- bounded queues;
- emergency buffers;
- per-core buffering;
- batching;
- group commit;
- crash consistency;
- segment lifecycle;
- tamper-evident hash chain;
- checkpoints;
- cryptographic signatures;
- integrity verification;
- audit queries;
- indexes;
- retention;
- evidence bundles;
- correction events;
- controlled expiration;
- multi-tenant isolation;
- remote export;
- delivery semantics;
- deduplication;
- replication metadata;
- deterministic simulation;
- replay;
- compiler metadata;
- native ABI;
- native APIs;
- security boundary;
- performance architecture;
- AI boundary;
- 40 formal invariants.

**AXAUDIT 5.0 → FROZEN.**

---

# BOOTSTRAP-760 — AXDIAGNOSTICS

**Native Diagnostics, Crash Analysis, Dump, Error Context, Runtime Health, Profiling & Failure Investigation Runtime 5.0**

Tầng tiếp theo sẽ tách phần **diagnostics/observability kỹ thuật** khỏi `AXAUDIT`.

Ranh giới sẽ là:

```text
                         Axiom Runtime
                              │
              ┌───────────────┴───────────────┐
              │                               │
          AXAUDIT                       AXDIAGNOSTICS
              │                               │
       accountability                   technical diagnosis
       security evidence                crash/debug/profile
       provenance                        health
       tamper evidence                   performance
              │                               │
              └───────────────┬───────────────┘
                              ▼
                       AXSTORAGE / AXPROCESS
```

Điều này giúp Axiom tránh biến `AXAUDIT` thành một module khổng lồ vừa làm **security evidence**, vừa làm **crash dump**, vừa làm **profiler**, vừa làm **runtime health monitor**.