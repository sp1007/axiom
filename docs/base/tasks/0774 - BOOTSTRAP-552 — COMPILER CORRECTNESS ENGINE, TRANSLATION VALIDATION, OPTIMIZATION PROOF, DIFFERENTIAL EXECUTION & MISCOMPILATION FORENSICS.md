# BOOTSTRAP-552 — COMPILER CORRECTNESS ENGINE, TRANSLATION VALIDATION, OPTIMIZATION PROOF, DIFFERENTIAL EXECUTION & MISCOMPILATION FORENSICS

**Trạng thái: COMPLETED / LOCKED**

`551` định nghĩa semantics. `552` biến semantics đó thành **cơ chế kiểm chứng compiler thực tế**.

Mục tiêu không phải formal-proof toàn bộ compiler ngay từ đầu, mà xây một hệ thống nhiều tầng:

```text id="c8q2m7"
                 Axiom Source
                      │
                      ▼
              Reference Semantics
                      │
                      ▼
                    HIR
                      │
                      ▼
                    MIR₀
                      │
             ┌────────┴────────┐
             ▼                 ▼
        Optimization A    Optimization B
             │                 │
             ▼                 ▼
            MIR₁              MIR₂
             │                 │
             └────────┬────────┘
                      ▼
             Translation Validator
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        Proven       Tested      Unknown
                      │
                      ▼
               Native Execution
                      │
                      ▼
             Differential Oracle
                      │
                 ┌────┴────┐
                 ▼         ▼
             Equivalent  Mismatch
                            │
                            ▼
                    Forensic Analysis
```

---

## 552.1. Compiler correctness ≠ test pass

A compiler passing test suite không có nghĩa compiler đúng.

Phải phân biệt:

```text
TestPassed
ReferenceEquivalent
FormallyProven
Reproducible
Unknown
```

---

## 552.2. Correctness evidence

Mỗi compilation có thể tạo:

```text
CorrectnessEvidence {
    source_hash
    semantic_hash
    compiler_build_id
    target
    optimization_profile

    transformations[]
    proofs[]
    differential_tests[]
    runtime_tests[]

    status
}
```

---

## 552.3. Evidence states

```text
Proven
Validated
DifferentiallyTested
Tested
Heuristic
Unknown
Failed
```

Không được chuyển `Unknown` thành `Proven`.

---

# 552.4. Translation validation

Mỗi transformation:

```text
IR_before
    ↓
optimization pass
    ↓
IR_after
```

có thể được kiểm tra.

Đây là **translation validation**, khác với việc chứng minh optimizer đúng cho mọi input.

---

# 552.5. Pass identity

Mỗi pass có:

```text
PassId
PassVersion
RuleSetVersion
```

Ví dụ:

```text
const-fold.v3
gvn.v2
dce.v4
bounds-elim.v5
vectorize.v2
```

---

# 552.6. Pass provenance

Compiler ghi:

```text
OptimizationRecord {
    pass_id
    version
    input_region
    output_region
    assumptions
    evidence
}
```

---

# 552.7. Transformation chain

Ví dụ:

```text id="m7p2x9"
MIR0
 ↓ const-fold
MIR1
 ↓ simplify-cfg
MIR2
 ↓ dce
MIR3
 ↓ inline
MIR4
 ↓ bounds-elim
MIR5
```

Có thể truy ngược tại sao instruction biến mất.

---

# 552.8. Local validation

Ưu tiên validate transformation nhỏ thay vì toàn bộ program.

```text
Region before
      ↓
Transformation
      ↓
Region after
```

giảm đáng kể chi phí verification.

---

# 552.9. Semantic slicing

Validator chỉ lấy:

```text
affected instructions
+
dependencies
+
observable effects
```

thay vì toàn bộ compiler IR.

---

# 552.10. Equivalence classes

Có nhiều mức:

```text
ExactValueEquivalent
MemoryEquivalent
EffectEquivalent
TraceEquivalent
BehaviorEquivalent
AllowedBehaviorEquivalent
```

---

# 552.11. Pure expression equivalence

Ví dụ:

```text
(a + 2) + 3
```

và:

```text
a + 5
```

chỉ equivalent nếu integer/overflow semantics cho phép.

---

# 552.12. Memory equivalence

Validator có thể cần chứng minh:

```text
load(p)
```

trước và sau optimization đọc cùng logical object/value.

---

# 552.13. Effect equivalence

Hai chương trình không cần instruction giống nhau nếu observable effects giống nhau:

```text
write(fd, data)
```

không thể bị xóa chỉ vì return value không dùng.

---

# 552.14. Trace equivalence

Với effectful code:

```text
EffectTrace(P)
```

được so với:

```text
EffectTrace(P')
```

theo allowed trace relation.

---

# 552.15. Partial-order equivalence

Concurrent programs có thể có nhiều execution order hợp lệ.

Validator không nên yêu cầu một trace duy nhất nếu memory model cho phép nhiều trace.

---

# 552.16. Concurrency equivalence

So sánh theo:

```text
allowed executions
```

thay vì:

```text
single deterministic execution
```

khi semantics vốn nondeterministic.

---

# 552.17. Symbolic execution

Validator có thể dùng symbolic values:

```text
x = symbolic()
```

và reason:

```text
condition
range
memory
effects
```

---

# 552.18. SMT integration

SMT solver là **optional verification backend**, không phải compiler runtime dependency.

Có thể dùng để chứng minh:

```text
range
arithmetic
bit operations
branch equivalence
bounds
```

---

# 552.19. Solver timeout

Nếu solver timeout:

```text
Unknown
```

không phải failure và cũng không phải proof.

---

# 552.20. Solver trust

Compiler không được tin solver tuyệt đối.

Có thể hỗ trợ:

```text
proof-producing solver
independent checker
```

cho critical proofs.

---

# 552.21. Proof artifact

```text
ProofArtifact {
    rule_id
    input_hash
    assumptions
    proof
    checker_version
}
```

---

# 552.22. Independent proof checker

Proof checker nhỏ hơn solver/compiler, nhằm giảm trust base.

```text
Solver
  ↓
Proof
  ↓
Small Checker
  ↓
Accepted
```

---

# 552.23. Optimization proof levels

```text
Level 0 — no validation
Level 1 — invariant checked
Level 2 — randomized validation
Level 3 — symbolic validation
Level 4 — proof-producing validation
Level 5 — independently checked proof
```

Không bắt buộc mọi pass đạt Level 5.

---

# 552.24. Critical optimization classes

Ưu tiên verification:

```text
bounds-check elimination
alias-sensitive optimization
integer overflow transformation
atomic optimization
memory reordering
vectorization
loop transformation
ABI lowering
```

---

# 552.25. Constant folding validator

Ví dụ:

```text
a = 2 * 3
```

→

```text
a = 6
```

Validator phải biết:

- integer type;
- overflow mode;
- numeric policy;
- target differences.

---

# 552.26. DCE validator

Instruction chỉ được xóa nếu:

```text
no observable result
no observable effect
no required cleanup
no volatile
no atomic
no panic
no externally visible allocation behavior
```

---

# 552.27. CFG simplification validator

Nếu:

```text
if true {
    A
} else {
    B
}
```

thì B chỉ bị loại khi condition thực sự constant under semantics.

---

# 552.28. Branch elimination

Branch elimination phải preserve:

```text
branch side effects
branch cleanup
branch panic
branch external effects
```

---

# 552.29. Inlining validation

Inlining phải preserve:

```text
argument evaluation
evaluation order
ownership
cleanup
panic
effects
return semantics
```

---

# 552.30. Tail-call transformation

Tail call chỉ hợp lệ nếu ABI/runtime semantics cho phép.

Phải preserve:

```text
arguments
return
cleanup
unwind
stack-observable contract
```

---

# 552.31. Loop transformation

Loop optimization phải preserve:

```text
iteration semantics
overflow
side effects
memory dependencies
termination behavior
```

---

# 552.32. Loop vectorization

Vectorization cần chứng minh:

```text
no illegal dependency
valid alias assumptions
valid bounds
numeric policy
remainder semantics
```

---

# 552.33. Floating vectorization

Strict FP không được tự ý reassociate.

Fast numeric mode có thể cho phép nếu policy bật.

---

# 552.34. Bounds elimination

Ví dụ:

```text
for i in 0..n {
    a[i]
}
```

validator cần chứng minh:

```text
0 <= i < len(a)
```

ở mọi iteration.

---

# 552.35. Alias-sensitive optimization

Nếu:

```text
*p
*q
```

có thể alias:

```text
```

thì optimizer không được assume independent memory.

---

# 552.36. Alias proof

Allowed evidence:

```text
ownership proof
noalias contract
allocation identity
range separation
type/representation guarantee
```

---

# 552.37. Memory optimization

Load/store forwarding chỉ hợp lệ nếu memory state equivalent.

---

# 552.38. Store elimination

Store:

```text
*p = x
```

có thể eliminate nếu:

```text
object overwritten before observable read
```

và không phải volatile/externally observable operation.

---

# 552.39. Atomic optimization

Atomic operation không được optimize như ordinary memory operation.

Validator phải preserve memory-order relation.

---

# 552.40. Fence optimization

Fence elimination/changing phải chứng minh không phá allowed executions.

---

# 552.41. Lock optimization

Lock elision/merging chỉ hợp lệ nếu synchronization semantics preserved.

Axiom không mặc định assume lock operations invisible.

---

# 552.42. Allocation optimization

Escape analysis evidence từ `423` có thể feed validator.

```text
heap allocation
→ stack allocation
```

chỉ hợp lệ nếu lifetime/identity/observable allocation contract preserved.

---

# 552.43. Scalar replacement

Struct:

```text
Point { x, y }
```

có thể trở thành:

```text
x_register
y_register
```

nếu address/alias/ABI/destructor semantics không yêu cầu physical object.

---

# 552.44. SROA boundary

Nếu code lấy address:

```text
&point
```

object identity có thể trở thành observable.

SROA phải xử lý trường hợp này.

---

# 552.45. Closure optimization

Closure:

```text
(code_ptr, env_ptr)
```

có thể inline/eliminate environment nếu escape analysis chứng minh an toàn.

---

# 552.46. Dynamic dispatch optimization

`dyn Trait` call có thể devirtualize nếu concrete type được chứng minh.

Nếu dynamic type unknown:

```text
Unknown
```

không được assume.

---

# 552.47. Generic specialization

Specialization phải preserve generic semantics.

---

# 552.48. Monomorphization validation

Generic instance:

```text
T = i32
```

phải giữ đúng trait constraints/associated types/layout/effects.

---

# 552.49. ABI lowering validation

Validator phải check:

```text
argument placement
return placement
stack alignment
register preservation
aggregate classification
sret
varargs
```

---

# 552.50. Machine instruction validation

Machine IR phải satisfy target ISA constraints.

Ví dụ:

```text
register class
operand width
immediate range
addressing mode
```

---

# 552.51. Machine code semantic validation

Ở mức cao:

```text
Machine IR
 ↓
Encoder
 ↓
Machine Bytes
 ↓
Decoder / Reference Model
```

để kiểm tra encoder không tạo instruction khác semantic intent.

---

# 552.52. Decoder round-trip

Có thể kiểm tra:

```text
Instruction
→ encode
→ decode
→ Instruction'
```

với canonical equivalence.

---

# 552.53. Object validation

Object writer phải validate:

```text
section
symbol
relocation
alignment
flags
architecture
```

---

# 552.54. Linker validation

Linker phải validate:

```text
symbol resolution
relocation result
section addresses
entry point
permissions
TLS
imports/exports
```

---

# 552.55. End-to-end validation

Critical tests:

```text
Axiom source
 ↓
MIR
 ↓
Machine
 ↓
Object
 ↓
Linker
 ↓
Executable
 ↓
OS
 ↓
result
```

---

# 552.56. Reference interpreter

`551` semantic interpreter là oracle nền.

```text
Source
 ├── Reference execution
 └── Native execution
```

---

# 552.57. Differential execution

So sánh:

```text
reference_result
native_result
```

bao gồm:

- return;
- panic;
- stdout;
- stderr;
- defined file effects;
- defined exit state.

---

# 552.58. Side-effect sandbox

Differential tests phải chạy trong controlled environment.

Không để test arbitrary network/process/filesystem phá môi trường.

---

# 552.59. Effect capture

External effects có thể được virtualize:

```text
virtual FS
virtual clock
virtual RNG
mock network
mock process
mock device
```

---

# 552.60. Deterministic execution

Cho phép:

```text
seed
virtual clock
deterministic scheduler
controlled environment
```

để reproduce mismatch.

---

# 552.61. Randomized differential testing

Generate nhiều input:

```text
input_i
```

và compare:

```text
reference(input_i)
native(input_i)
```

---

# 552.62. Input generator

Generator dựa semantic types:

```text
i32
enum
struct
array
string
option
result
```

thay vì random bytes đơn thuần.

---

# 552.63. Structure-aware fuzzing

Ví dụ compiler có thể generate:

```text
nested match
generic structs
ownership transitions
async state
atomic operations
```

theo grammar + semantic constraints.

---

# 552.64. Mutation testing

Một optimization pass có thể cố tình mutate IR để kiểm tra validator có phát hiện semantic mismatch.

---

# 552.65. Oracle hierarchy

```text id="r9x3m7"
Formal proof
    ↓
Reference semantics
    ↓
Independent implementation
    ↓
Differential execution
    ↓
Property testing
    ↓
Golden tests
```

Mỗi oracle có độ mạnh và giới hạn riêng.

---

# 552.66. Independent backend

Có thể có backend reference đơn giản:

```text
MIR
 ↓
portable interpreter
```

không tối ưu.

Dùng làm oracle cho optimized backend.

---

# 552.67. Independent code generator

Trong compiler development, một backend đơn giản khác có thể generate native code để differential test backend tối ưu.

Không cần tồn tại trong production toolchain.

---

# 552.68. Cross-backend differential

```text
MIR
 ├── x86 backend
 ├── AArch64 backend
 └── interpreter
```

trên semantics tương thích.

---

# 552.69. Cross-optimization differential

```text
-O0
-O1
-O2
-O3
```

phải produce equivalent observable behavior.

---

# 552.70. Optimization bisect

Khi:

```text
-O0 works
-O3 fails
```

compiler tự binary-search optimization passes:

```text
O0
 ↓
pass A
 ↓
pass B
 ↓
pass C  ← suspect
 ↓
pass D
```

---

# 552.71. Miscompilation minimization

Sau khi phát hiện mismatch:

```text
large program
 ↓
semantic reducer
 ↓
minimal program
```

---

# 552.72. Reducer phải preserve failure

Reducer thử:

- remove function;
- remove statement;
- simplify expression;
- shrink constants;
- remove type fields;
- reduce generic parameters;
- simplify control flow.

Chỉ giữ transformation nếu mismatch còn tồn tại.

---

# 552.73. Semantic reduction

Reducer không chỉ text-based.

Nó phải hiểu:

```text
AST
HIR
types
MIR
dependencies
```

để giảm nhanh hơn.

---

# 552.74. Crash vs miscompile

Compiler outcomes:

```text
Success
Diagnostic
CompilerCrash
WrongCode
Timeout
ResourceExhaustion
```

không được gộp chung.

---

# 552.75. Wrong-code report

```text
MiscompilationReport {
    testcase_id
    source_hash

    compiler_build
    target
    optimization

    expected
    observed

    first_divergence
    suspect_pass
    transformation_chain

    minimized_source
    reproduction_command
}
```

---

# 552.76. First divergence

Nếu reference:

```text
x = 42
```

native:

```text
x = 41
```

report cần tìm semantic divergence gần nhất có thể.

---

# 552.77. IR differential snapshot

Có thể so:

```text
MIR_reference
MIR_after_pass
MIR_after_next_pass
```

để tìm first invalid transformation.

---

# 552.78. Optimization rollback

Development compiler có thể:

```text
disable pass X
```

để xác định failure.

Không dùng runtime rollback.

---

# 552.79. Pass quarantine

Nếu pass có bug nghiêm trọng:

```text
pass status = quarantined
```

release policy có thể disable pass.

---

# 552.80. Regression testcase

Mỗi miscompilation được minimize thành:

```text
regression test
```

và giữ lâu dài.

---

# 552.81. Compiler bug database

Mỗi bug có:

```text
bug_id
affected_pass
affected_targets
affected_versions
trigger_pattern
fixed_version
testcase
```

---

# 552.82. Pattern-based affected build analysis

Nếu bug có trigger pattern machine-readable, `546` có thể tìm artifact có khả năng bị ảnh hưởng.

---

# 552.83. Compiler security + correctness

Compiler vulnerability có thể là:

```text
security bug
+
miscompilation
```

Hai classification được giữ riêng.

---

# 552.84. Differential security semantics

Security-sensitive code có thể được kiểm tra:

```text
normal build
sanitized build
hardened build
```

với expected semantics.

---

# 552.85. Constant-time validation

Nếu `@constant_time`:

```text
secret-dependent branch
secret-dependent memory access
```

có thể được static analyzer phát hiện.

`552` có thể validate machine transformation không phá contract.

---

# 552.86. Debug preservation

Optimization không được làm sai:

```text
source location
variable mapping
inline stack
```

dù variable có thể optimized out.

---

# 552.87. Coverage integration

Regression testcase phải được gắn:

```text
coverage regions
compiler pass
semantic rule
```

---

# 552.88. Sanitizer integration

Mismatch test có thể chạy thêm sanitizer để phân biệt:

```text
source UB
compiler bug
runtime bug
```

---

# 552.89. Source UB distinction

Nếu testcase có UB:

```text
not valid evidence of compiler miscompilation
```

trừ khi đang kiểm tra UB-specific compiler diagnostics.

---

# 552.90. Safe differential corpus

Wrong-code corpus ưu tiên:

```text
well-defined programs
```

để tránh ambiguous results.

---

# 552.91. Undefined behavior corpus

UB tests tồn tại riêng để test:

```text
sanitizer
diagnostics
unsafe boundary
```

---

# 552.92. Floating differential testing

Comparison phải theo numeric policy:

```text
strict → exact/defined relation
fast → allowed tolerance/relation
```

Không dùng universal epsilon.

---

# 552.93. Cross-platform differential

Không so byte-for-byte output nếu platform semantics khác.

So:

```text
common semantic contract
```

---

# 552.94. Endianness differential

Serialization tests phải kiểm tra explicit endian semantics.

---

# 552.95. ABI differential

Test:

```text
Axiom caller
 ↔
C function
```

với tất cả supported ABI classes.

---

# 552.96. Async differential

Reference async scheduler:

```text
deterministic scheduler
```

để test native executor.

---

# 552.97. Concurrency differential

Có thể kiểm tra bounded schedules:

```text
schedule A
schedule B
schedule C
```

và verify mọi result đều nằm trong allowed behavior.

---

# 552.98. Atomic litmus tests

Axiom có corpus các memory-model tests:

```text
load buffering
store buffering
message passing
```

và các pattern tương ứng.

---

# 552.99. Thread sanitizer distinction

Race detector failure không tự chứng minh compiler wrong.

Cần xác định:

```text
program race
vs
compiler transformation race
```

---

# 552.100. GPU differential

Kernel có thể chạy:

```text
CPU reference
GPU implementation
```

và compare trong numerical policy.

---

# 552.101. Tensor differential

Graph compiler:

```text
unoptimized graph
optimized graph
```

so output tensor shape/dtype/value/layout/effects.

---

# 552.102. Model graph differential

Model execution:

```text
eager
graph-optimized
fused
quantized
```

chỉ equivalent trong policy đã chọn.

---

# 552.103. Quantization distinction

Quantized model thường không bitwise equivalent FP32.

Do đó validator phải dùng:

```text
declared numerical error contract
```

---

# 552.104. Workflow differential

Workflow compiler:

```text
interpreted workflow
compiled workflow
```

so:

```text
state transitions
events
effects
checkpoint
retry
```

---

# 552.105. Agent differential

Agent workflows có model nondeterminism.

Validation cần pin:

```text
model
seed where applicable
tool results
memory snapshot
policy
environment
```

---

# 552.106. External nondeterminism

Nếu external system không deterministic:

```text
comparison scope
```

phải được giới hạn.

---

# 552.107. Reference implementation drift

Reference interpreter cũng có thể có bug.

Do đó không dựa duy nhất vào reference implementation.

---

# 552.108. Multiple oracles

Critical semantics nên có:

```text
reference interpreter
+
property tests
+
differential implementation
+
formal checker where feasible
```

---

# 552.109. Oracle disagreement

Nếu:

```text
Oracle A ≠ Oracle B
```

status:

```text
OracleConflict
```

Không tự chọn một oracle.

---

# 552.110. Compiler correctness dashboard

Machine-readable view:

```text
CompilerCorrectnessStatus {
    passes
    validated_passes
    proven_passes
    unknown_passes
    regressions
    open_miscompilations
}
```

Không tạo một universal correctness score.

---

# 552.111. Pass coverage

Có thể thống kê:

```text
pass
tests
proofs
fuzz cases
differential cases
known bugs
```

---

# 552.112. No correctness score

Axiom không xuất:

```text
compiler correctness = 97%
```

vì không có semantics hợp lệ cho con số đó.

---

# 552.113. Release gate

Project policy có thể yêu cầu:

```text
no known wrong-code regressions
critical passes validated
bootstrap tests pass
cross-target tests pass
```

Đây là **policy**, không phải universal language rule.

---

# 552.114. Continuous correctness testing

CI:

```text
commit
 ↓
unit tests
 ↓
semantic tests
 ↓
IR verifier
 ↓
differential tests
 ↓
fuzzing
 ↓
backend tests
 ↓
cross-target
```

---

# 552.115. Nightly deep validation

Có thể chạy:

```text
large fuzz corpus
SMT validation
randomized differential execution
cross-optimization testing
```

mà không làm compile developer chậm.

---

# 552.116. Deterministic replay

Mọi failure quan trọng phải cố lưu:

```text
seed
compiler build
target
optimization config
environment
input
```

---

# 552.117. Reproduction package

Có thể tạo:

```text
.axfail
```

conceptually:

```text
manifest
source
compiler identity
target
config
expected
observed
reproduction command
```

---

# 552.118. Failure artifact security

Failure artifact có thể chứa proprietary source.

Chia:

```text
private
redacted
public-minimized
```

---

# 552.119. Automatic publication

Không tự động publish compiler failure testcase ra Internet.

---

# 552.120. Miscompilation severity

Severity là metadata/policy:

```text
critical
high
medium
low
```

Không phải universal correctness score.

---

# 552.121. First-class compiler invariant

Compiler phải đảm bảo:

```text
verified IR
```

trước khi truyền sang phase kế tiếp.

---

# 552.122. Fail-fast verifier

Nếu MIR invalid:

```text
stop compilation
```

không tiếp tục generate machine code từ malformed MIR.

---

# 552.123. Trusted boundary

Critical pipeline:

```text
Parser
 → Type Checker
 → MIR Verifier
 → Optimizer
 → MIR Verifier
 → Backend
 → Machine Verifier
 → Encoder
 → Object Verifier
 → Linker Verifier
```

---

# 552.124. Verifier independence

Verifier nên đơn giản hơn producer.

```text
complex optimizer
       ↓
simple verifier
```

---

# 552.125. No optimizer self-certification

Optimizer không được tự ghi:

```text
valid = true
```

và coi đó là proof.

---

# 552.126. Validation artifacts

Mỗi stage có thể tạo:

```text
InputHash
OutputHash
VerifierVersion
Status
Evidence
```

---

# 552.127. Incremental validation

Chỉ validate changed regions nếu dependency graph chứng minh phần còn lại unaffected.

---

# 552.128. Cache validation

Proof cache phải verify:

```text
semantic hash
rule version
compiler analysis version
target
```

---

# 552.129. Stale proof

Nếu rule version thay đổi:

```text
old proof → invalid/stale
```

không reuse mù quáng.

---

# 552.130. Proof invalidation

Thay đổi:

```text
type rules
memory model
ABI
numeric policy
optimization rule
target
```

có thể invalidate proof.

---

# 552.131. Machine-checkable invariant database

Compiler lưu:

```text
Invariant {
    id
    version
    domain
    preconditions
    postconditions
    verifier
}
```

---

# 552.132. Semantic rule linkage

Mỗi optimization evidence trỏ tới:

```text
semantic_rule_id
```

---

# 552.133. Source linkage

Evidence cũng trỏ tới:

```text
FileId
SymbolId
SemanticNodeId
```

---

# 552.134. AI forensic query

AI có thể hỏi:

```text
why_wrong_code()
first_divergence()
suspect_passes()
show_transformation_chain()
show_assumptions()
show_proof()
show_failed_invariant()
minimize_failure()
reproduce_failure()
affected_compiler_versions()
```

---

# 552.135. AI must preserve uncertainty

AI không được nói:

> pass X chắc chắn gây lỗi

nếu evidence mới chỉ là correlation.

Phải phân biệt:

```text
Confirmed
Likely
Candidate
Unknown
```

---

# 552.136. Compiler bisect

Có thể bisect theo:

```text
compiler revision
optimization pass
target feature
optimization level
```

---

# 552.137. Target-feature bisect

Nếu bug chỉ xuất hiện với:

```text
-avx2
```

compiler phải có khả năng isolate feature.

---

# 552.138. Backend bisect

Nếu:

```text
-O3 + x86
```

fail nhưng:

```text
-O3 + interpreter
```

pass:

→ backend trở thành candidate.

---

# 552.139. Linker bisect

Nếu object đúng nhưng executable sai:

```text
object
 ↓
linker
 ↓
wrong executable
```

thì linker được isolate.

---

# 552.140. Runtime distinction

Wrong result có thể đến từ:

```text
compiler
runtime
OS
foreign library
hardware
```

forensic engine không được tự quy kết nếu evidence chưa đủ.

---

# 552.141. Hardware faults

Machine mismatch có thể do hardware fault.

Test harness cần hỗ trợ repeat/cross-machine validation.

---

# 552.142. Cross-machine reproduction

```text
Machine A
Machine B
```

so sánh cùng:

```text
compiler
binary
input
```

---

# 552.143. Cross-architecture reproduction

Khi common semantics tồn tại:

```text
x86-64
AArch64
```

có thể dùng làm differential oracle.

---

# 552.144. Binary equivalence

Không yêu cầu optimized binaries giống nhau.

Correctness dựa trên behavior, không binary identity.

---

# 552.145. Performance independence

Compiler correctness không phụ thuộc performance.

Một binary chậm nhưng đúng vẫn đúng.

---

# 552.146. Optimization success independence

Không optimize được không phải compiler bug.

```text
MissedOptimization
≠
Miscompilation
```

---

# 552.147. False positive

Validator báo mismatch nhưng source/reference không đáng tin:

```text
FalsePositive
```

phải có classification riêng.

---

# 552.148. False negative

Không phát hiện mismatch không chứng minh compiler đúng.

---

# 552.149. Soundness vs completeness

Verifier cần ưu tiên:

```text
sound evidence
```

hơn:

```text
claim everything verified
```

---

# 552.150. Final architecture

```text id="f2q7m8"
                    Compiler
                       │
             ┌─────────┴─────────┐
             ↓                   ↓
        Transformation       Reference Model
             │                   │
             ↓                   ↓
          IR'              Expected Semantics
             │                   │
             └─────────┬─────────┘
                       ↓
               Validation Engine
                       │
       ┌───────────────┼───────────────┐
       ↓               ↓               ↓
   Invariant        Symbolic       Differential
    Checker          Checker          Runner
       │               │               │
       └───────────────┼───────────────┘
                       ↓
                  Evidence DB
                       │
              ┌────────┴────────┐
              ↓                 ↓
         Pass / Release      Forensics
```

---

# 552.151–552.199 — Hard invariants

`552` khóa các invariant sau:

1. Compiler correctness phải được kiểm chứng bằng evidence.
2. Test pass không đồng nghĩa correctness proof.
3. Translation validation phải được hỗ trợ.
4. Optimization pass phải có identity.
5. Optimization pass phải có version.
6. Transformation provenance phải được ghi.
7. Semantic assumptions phải queryable.
8. Unknown không phải Proven.
9. Solver timeout phải là Unknown.
10. Verifier phải độc lập với optimizer ở mức hợp lý.
11. Optimizer không được tự certify chính nó.
12. MIR phải được verify trước optimization.
13. MIR phải được verify sau optimization.
14. Machine IR phải được verify.
15. Object phải được verify.
16. Linker output phải được verify.
17. Reference semantics phải tồn tại cho semantic subset.
18. Reference interpreter không phải production runtime.
19. Differential execution phải được hỗ trợ.
20. Differential testing phải có controlled environment.
21. Randomized differential testing phải được hỗ trợ.
22. Semantic-aware input generation phải được hỗ trợ.
23. Structure-aware fuzzing phải được hỗ trợ.
24. Metamorphic testing phải được hỗ trợ.
25. Mutation testing phải được hỗ trợ.
26. Miscompilation phải phân biệt compiler crash.
27. Miscompilation phải phân biệt source UB.
28. Miscompilation phải phân biệt runtime failure.
29. Miscompilation phải phân biệt external-system failure.
30. Miscompilation report phải reproducible.
31. Wrong-code testcase phải có compiler identity.
32. Wrong-code testcase phải có target identity.
33. Wrong-code testcase phải có optimization configuration.
34. Wrong-code testcase phải có expected result.
35. Wrong-code testcase phải có observed result.
36. Wrong-code testcase phải có source hash.
37. Wrong-code testcase phải cố định random seed khi có thể.
38. Wrong-code testcase phải cố định virtual clock khi cần.
39. Wrong-code testcase phải cố định deterministic scheduler khi cần.
40. Compiler phải hỗ trợ optimization bisect.
41. Compiler phải hỗ trợ pass isolation.
42. Compiler phải hỗ trợ target-feature isolation.
43. Compiler phải hỗ trợ backend isolation.
44. Compiler phải hỗ trợ linker isolation.
45. Compiler phải hỗ trợ testcase minimization.
46. Minimization phải ưu tiên semantic reduction.
47. Reduced testcase phải giữ failure mới được chấp nhận.
48. Regression testcase phải được lưu.
49. Compiler bug phải có affected-version metadata.
50. Compiler bug phải có affected-target metadata.
51. Compiler bug phải có triggering pattern khi biết.
52. Compiler bug phải có fixed-version metadata.
53. Compiler bug không được tự biến thành language semantics.
54. Constant folding phải preserve arithmetic semantics.
55. DCE phải preserve observable effects.
56. CFG simplification phải preserve control semantics.
57. Inlining phải preserve evaluation order.
58. Inlining phải preserve cleanup.
59. Tail-call optimization phải preserve ABI.
60. Loop optimization phải preserve iteration semantics.
61. Loop vectorization phải validate dependencies.
62. Loop vectorization phải respect numeric policy.
63. Alias optimization phải có alias evidence.
64. Unknown alias không phải NoAlias.
65. Load elimination phải preserve memory semantics.
66. Store elimination phải preserve observable writes.
67. Allocation elimination phải preserve observable lifetime.
68. Scalar replacement phải preserve address observability.
69. Dynamic devirtualization phải có type evidence.
70. Generic specialization phải preserve generic semantics.
71. Atomic optimization phải preserve memory order.
72. Fence transformation phải preserve synchronization.
73. Lock optimization phải preserve synchronization.
74. Async transformation phải preserve suspension state.
75. Cancellation semantics phải được preserve.
76. Channel transformations phải preserve ordering.
77. Actor transformations phải preserve mailbox semantics.
78. Reactive transformations phải preserve propagation semantics.
79. Workflow transformations phải preserve durable state.
80. Workflow transformations phải preserve external effects.
81. Agent transformations không được duplicate irreversible actions.
82. Tensor transformations phải preserve declared numerical contract.
83. Quantization transformations phải use explicit error contract.
84. GPU transformations phải preserve synchronization.
85. GPU memory transformations phải preserve ownership.
86. FFI transformations phải preserve ABI.
87. FFI unknown behavior phải remain Unknown.
88. Volatile operations không được eliminate tùy tiện.
89. Random effects không được duplicate tùy tiện.
90. External I/O không được eliminate tùy tiện.
91. Reference/native comparisons phải respect nondeterminism.
92. Concurrency validation phải compare allowed behavior sets.
93. Distributed validation phải respect partition/delay/reordering.
94. Floating validation phải respect numeric policy.
95. Cross-target validation phải compare common semantics.
96. Binary equality không phải correctness requirement.
97. Performance không phải correctness criterion.
98. Missed optimization không phải miscompilation.
99. No universal compiler correctness score.
100. Evidence phải có provenance.
101. Evidence phải có semantic hash.
102. Evidence phải có compiler build identity.
103. Evidence phải có target.
104. Evidence phải có optimization configuration.
105. Proof cache phải có rule version.
106. Proof cache phải có semantic identity.
107. Stale proof phải bị invalidate.
108. Changed memory model phải invalidate relevant proofs.
109. Changed ABI phải invalidate relevant proofs.
110. Changed numeric semantics phải invalidate relevant proofs.
111. Changed optimization rule phải invalidate relevant proofs.
112. Machine encoder phải được differential-tested.
113. Instruction encoder phải hỗ trợ round-trip validation.
114. Object writer phải được differential-tested.
115. Linker phải được differential-tested.
116. ABI phải có cross-language golden tests.
117. Safe-code differential corpus phải ưu tiên defined programs.
118. UB corpus phải được tách riêng.
119. Sanitizer evidence không phải compiler correctness proof.
120. Static-analysis evidence không phải compiler correctness proof.
121. Formal proof phải ghi scope.
122. Formal proof phải ghi assumptions.
123. Formal proof phải ghi checker identity.
124. Solver identity phải được ghi.
125. Solver version phải được ghi.
126. Solver failure không được trở thành proof.
127. Oracle disagreement phải được giữ lại.
128. Multiple oracles phải được hỗ trợ cho critical semantics.
129. Reference implementation drift phải được phát hiện.
130. Independent backend/interpreter có thể được dùng làm oracle.
131. Compiler stage0/1/2 phải được differential-tested.
132. Cross-optimization levels phải được differential-tested.
133. Cross-target testing phải được hỗ trợ.
134. Cross-machine reproduction phải được hỗ trợ.
135. Hardware-related anomalies phải được distinguish.
136. Compiler/runtime/OS/foreign-library boundaries phải được distinguish.
137. Miscompilation evidence không được tự động quy trách nhiệm.
138. AI forensic analysis phải preserve uncertainty.
139. AI không được biến candidate thành confirmed.
140. AI không được invent expected result.
141. AI không được invent proof.
142. AI không được suppress failed validation.
143. Failure artifact phải hỗ trợ privacy.
144. Source không được tự động upload.
145. Public testcase phải được explicit publish.
146. Build/reproduction environment phải được recorded.
147. Differential runner phải có resource limits.
148. Fuzzing phải có timeout.
149. Symbolic execution phải có timeout.
150. Minimizer phải có timeout.
151. Validation phải có cancellation.
152. Validation cache phải immutable/content-addressed.
153. Validation artifact phải có integrity hash.
154. Corrupted proof artifact phải reject.
155. Corrupted testcase phải reject.
156. Malformed IR phải reject.
157. Malformed machine IR phải reject.
158. Malformed object phải reject.
159. Invalid linker state phải reject.
160. Critical verifier failure phải stop pipeline.
161. Compiler không được emit trusted artifact từ invalid verified IR.
162. Release policy có thể yêu cầu zero known wrong-code regressions.
163. Release policy không phải language semantic.
164. Correctness evidence phải phân biệt policy với proof.
165. Formal verification không bắt buộc cho toàn bộ compiler.
166. Critical passes phải có verification roadmap.
167. Verification system không được bắt buộc application runtime.
168. Verification system không được thêm GC.
169. Verification system không được thêm VM.
170. Verification system không được thêm hidden thread vào application.
171. Verification system không được thêm hidden telemetry.
172. Verification system không được thêm hidden network.
173. Verification phải hỗ trợ freestanding compiler builds.
174. Verification phải hỗ trợ native targets.
175. Verification phải hỗ trợ WASM.
176. Verification phải hỗ trợ cross compilation.
177. Verification phải hỗ trợ incremental compilation.
178. Verification evidence phải tích hợp `446`.
179. Translation semantics phải tích hợp `551`.
180. Bootstrap differential testing phải tích hợp `482/488`.
181. Build provenance phải tích hợp `487`.
182. Security analysis phải tích hợp `549`.
183. Sanitizer phải tích hợp `480`.
184. Static analysis phải tích hợp `478`.
185. Contracts phải tích hợp `479`.
186. Profiling/benchmark evidence phải giữ riêng khỏi correctness evidence.
187. Debug evidence phải giữ riêng khỏi correctness proof.
188. Package provenance phải giữ riêng nhưng liên kết được.
189. Compiler security evidence phải liên kết được.
190. Miscompilation impact analysis phải liên kết được với artifact graph.
191. Compiler bug phải truy ngược tới affected artifacts khi evidence đủ.
192. Artifact phải truy ngược compiler.
193. Artifact phải truy ngược optimization configuration.
194. Artifact phải truy ngược target features.
195. Artifact phải truy ngược linker.
196. Semantic transformation chain phải queryable.
197. First divergence phải queryable khi có thể.
198. Unknown phải được giữ nguyên xuyên toàn bộ pipeline.
199. Compiler correctness claims phải có evidence tương ứng.
200. **Final invariant:** Axiom phải có khả năng phát hiện, tái tạo, cô lập và điều tra miscompilation từ source → semantic model → MIR → optimization → machine code → object → linker → executable bằng verifier, translation validation, differential execution, fuzzing, minimization và formal checking có chọn lọc; đồng thời không được nhầm test pass, signature, reproducibility, performance hay self-certification với bằng chứng rằng compiler thực sự bảo toàn semantics.

**BOOTSTRAP-552: LOCKED.**

---

# BOOTSTRAP-553 — COMPILER OPTIMIZATION FRAMEWORK 2.0, PASS MANAGER, COST MODEL, PROFILE-GUIDED OPTIMIZATION, LTO, AUTOVECTORIZATION & WHOLE-PROGRAM OPTIMIZATION

Đây là bước tiếp theo.

Sau `551` + `552`, Axiom đã có **semantic contract + correctness validation**. `553` sẽ xây phần còn thiếu để đạt mục tiêu hiệu năng thực tế:

```text id="b7m3q1"
Typed HIR
   ↓
MIR
   ↓
Canonicalization
   ↓
Scalar Optimization
   ↓
Memory Optimization
   ↓
Loop Optimization
   ↓
Vectorization
   ↓
Inlining / Devirtualization
   ↓
Interprocedural Optimization
   ↓
LTO
   ↓
PGO
   ↓
Machine-aware Optimization
   ↓
Register / Instruction Optimization
   ↓
Native Code
```

Trọng tâm của `553` sẽ là **không biến compiler thành một tập optimization pass rời rạc** mà xây một framework thống nhất có:

- pass dependency;
- analysis invalidation;
- preservation contract;
- cost model;
- target-aware optimization;
- profile feedback;
- PGO;
- LTO;
- whole-program analysis;
- interprocedural optimization;
- devirtualization;
- inlining;
- loop transformations;
- vectorization;
- memory optimization;
- code-size optimization;
- hot/cold splitting;
- instruction combining;
- machine scheduling;
- specialization;
- optimization budgets;
- compile-time budgets;
- deterministic optimization;
- optimization cache;
- optimization explainability;
- `why_optimized`;
- `why_not_optimized`;
- và đặc biệt **552 translation validation phải được tích hợp trực tiếp vào framework**, để optimizer có thể mạnh tay mà vẫn có đường kiểm chứng khi transformation thay đổi semantics-sensitive code.