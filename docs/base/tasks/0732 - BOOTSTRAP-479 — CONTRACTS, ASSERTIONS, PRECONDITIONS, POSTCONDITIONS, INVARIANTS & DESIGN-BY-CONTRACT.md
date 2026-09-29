# BOOTSTRAP-479 — CONTRACTS, ASSERTIONS, PRECONDITIONS, POSTCONDITIONS, INVARIANTS & DESIGN-BY-CONTRACT

**Trạng thái: COMPLETED / LOCKED**

479 bổ sung lớp contract có thể kiểm chứng lên trên type system, ownership, effect system và static analysis.

Nguyên tắc:

```text id="d6y1se"
Type
    ≠ Contract
    ≠ Assertion
    ≠ Assume
    ≠ Proof
```

và:

```text id="v8q4hm"
Contract
   ↓
Static Proof ──────┐
                   ├── Verified / Runtime Checked / Unknown
Runtime Check ─────┘
```

---

## 479.1 — Assertion

`assert(condition)` kiểm tra điều kiện tại runtime.

Nếu false:

```text
panic
```

hoặc behavior được configuration xác định.

---

## 479.2 — Debug assertion

```text
debug_assert(condition)
```

có thể bị loại khỏi release build.

---

## 479.3 — Release assertion

Assertion production-critical phải tồn tại nếu program semantics yêu cầu nó.

---

## 479.4 — Assertion không phải optimization assumption

```text
assert(x > 0)
```

kiểm tra điều kiện.

```text
assume(x > 0)
```

không kiểm tra.

Hai operation hoàn toàn khác semantics.

---

# 479.5 — Preconditions

Function có thể khai báo:

```text
@requires(x >= 0)
fn sqrt_integer(x: i32) -> ...
```

Precondition mô tả điều kiện caller phải đảm bảo.

---

## 479.6 — Preconditions runtime

Nếu compiler không chứng minh được precondition, runtime check có thể được emit tùy contract mode.

---

## 479.7 — Preconditions compile-time

Nếu arguments là comptime values, compiler có thể verify contract tại compile time.

---

## 479.8 — Postconditions

```text
@ensures(result >= 0)
fn abs(x: i32) -> i32
```

Postcondition được kiểm tra trên trạng thái sau function.

---

## 479.9 — Result reference

Contract phải có cách tham chiếu return value.

Conceptually:

```text
result
```

---

## 479.10 — Pre-state

Postcondition có thể cần giá trị trước khi function chạy:

```text
old(x)
```

`old()` phải được định nghĩa rõ về evaluation và lifetime.

---

# 479.11 — Struct invariant

Struct có thể có invariant:

```text
@invariant(self.length <= self.capacity)
struct Buffer { ... }
```

Invariant phải được duy trì tại các boundary mà contract system quy định.

---

## 479.12 — Constructor boundary

Invariant phải được establish trước khi một value được xem là fully initialized/valid.

---

## 479.13 — Mutation boundary

Public mutation API phải không phá invariant nếu invariant được khai báo là public contract.

---

# 479.14 — Trait contract

Trait method có thể có:

```text
@requires(...)
@ensures(...)
```

Implementation phải thỏa contract tương ứng.

---

## 479.15 — Generic contract

Generic function có thể yêu cầu capability/property từ type parameter.

Contract không thay thế trait bound.

---

# 479.16 — Contract inheritance

Axiom không có class inheritance.

Trait implementations phải tuân contract của trait.

Implementation không được tùy tiện làm precondition mạnh hơn contract mà caller đã được phép dựa vào.

---

## 479.17 — Postcondition strengthening

Implementation có thể cung cấp postcondition mạnh hơn, miễn không vi phạm base contract.

---

# 479.18 — Loop invariant

Loop có thể có invariant dùng cho:

- static verification;
- documentation;
- runtime checking;
- optimizer reasoning.

---

## 479.19 — Loop invariant semantics

Compiler không được giả định invariant đúng chỉ vì programmer viết nó.

Nếu invariant chỉ là assertion → check.

Nếu là `assume` → unsafe assumption.

---

# 479.20 — `assume`

Concept:

```text
assume(condition)
```

nói với optimizer rằng condition đúng tại điểm đó.

Compiler **không phải** kiểm tra condition.

---

## 479.21 — Invalid assumption

Nếu `assume` sai, behavior của chương trình nằm ngoài contract của program.

Đây là low-level/unsafe facility.

---

## 479.22 — Assume diagnostics

Compiler nên cảnh báo nếu static analysis chứng minh:

```text
condition == false
```

---

# 479.23 — Contract modes

Canonical modes:

```text id="x7x2kg"
off
debug
release-checked
release
verify
```

---

## 479.24 — `off`

Contract checks bị loại nếu không cần cho semantics.

---

## 479.25 — `debug`

Runtime contracts được bật để phát hiện violation.

---

## 479.26 — `release-checked`

Production vẫn kiểm tra các contracts được đánh dấu runtime-critical.

---

## 479.27 — `release`

Compiler loại bỏ các checks không cần thiết theo policy.

---

## 479.28 — `verify`

Ưu tiên static proof/verification.

---

# 479.29 — Contract violation

Contract violation là programming error theo contract definition.

Default behavior:

```text
panic
```

nhưng project có thể chọn:

```text
abort
```

---

## 479.30 — Result không mặc định

Contract failure không tự động trở thành:

```text
Result<T,E>
```

vì contract violation khác recoverable application failure.

---

# 479.31 — FFI contracts

451 foreign functions có thể khai báo:

```text
@requires(ptr != null)
@requires(len <= capacity)
@ensures(...)
```

Contract boundary giúp tạo safe wrapper.

---

## 479.32 — Foreign contract trust

Compiler không được coi foreign contract là mathematically verified.

Contract declaration là trust assertion trừ khi có proof.

---

# 479.33 — Ownership contracts

Có thể mô tả:

```text
@consumes(buffer)
@returns_owned
```

nhưng ownership semantics vẫn do 423/451 quyết định.

Contract không thay thế compiler ownership rules.

---

# 479.34 — Resource contracts

API có thể yêu cầu:

```text
resource.is_open()
```

và đảm bảo:

```text
resource.is_closed()
```

khi operation kết thúc.

---

# 479.35 — Concurrency contracts

Có thể mô tả:

```text
@requires_locked(mutex)
@requires_single_thread
@thread_safe
```

Contract phải tích hợp với 424/471.

---

## 479.36 — Data-race contract

`@thread_safe` không tự chứng minh data-race freedom.

Compiler phải có evidence hoặc implementation contract tương ứng.

---

# 479.37 — Realtime contracts

461 có thể dùng:

```text
@realtime
@no_alloc
@no_block
@no_panic
```

Contract analyzer 478 có thể kiểm tra call graph.

---

## 479.38 — Realtime budget

Có thể khai báo:

```text
@budget(100us)
```

nhưng đây là performance contract, không phải guarantee nếu hardware/scheduler không deterministic.

---

# 479.39 — Security contracts

445 có thể dùng contract để mô tả:

```text
input validated
buffer bounds valid
secret not exposed
```

---

## 479.40 — Taint contracts

Có thể khai báo source/sink expectations cho 478 taint analysis.

---

# 479.41 — Contract composition

Nested function contracts phải compose theo call graph.

---

## 479.42 — Generic contract instantiation

Contract của generic function được instantiate cùng generic instance.

---

# 479.43 — Contract specialization

Nếu specialization tồn tại, specialized implementation không được phá contract của generic interface.

---

# 479.44 — Contract evaluation

Contract expressions phải tuân:

- type checking;
- ownership;
- effect checking;
- purity restrictions tùy context.

---

## 479.45 — Side effects

Pre/postcondition không được mặc định có side effects.

Compiler nên giới hạn contract expression để tránh thay đổi program behavior.

---

# 479.46 — Contract purity

Contract expression nên ưu tiên:

```text
pure
deterministic
non-blocking
non-allocating
```

---

## 479.47 — Contract panic

Contract evaluation itself không nên gây hidden arbitrary side effects.

---

# 479.48 — Static verification

478 analyzer có thể prove:

```text
requires(P)
```

từ caller state.

Nếu proof thành công, runtime check có thể được loại bỏ.

---

## 479.49 — Unknown

Nếu analyzer không thể prove contract:

```text
Unknown
```

không đồng nghĩa false.

---

# 479.50 — Proof levels

Contract tooling sử dụng:

```text
Proven
Disproven
RuntimeChecked
Unknown
Assumed
```

---

## 479.51 — Disproven contract

Nếu compiler chứng minh precondition không thể thỏa tại một call site → compile error.

---

# 479.52 — Contract elimination

Runtime check có thể được loại bỏ nếu:

```text
static proof == Proven
```

---

## 479.53 — Duplicate checks

Optimizer có thể loại bỏ duplicate contract checks nếu semantics được bảo toàn.

---

# 479.54 — Bounds contracts

Contract:

```text
@requires(index < self.length)
```

có thể giúp bounds-check elimination.

---

# 479.55 — Numeric contracts

Có thể mô tả:

```text
@requires(x != 0)
@ensures(result * divisor == x)
```

nhưng overflow semantics của Axiom phải vẫn được tôn trọng.

---

# 479.56 — Floating-point contracts

Không được giả định algebraic identities như:

```text
(a + b) + c == a + (b + c)
```

trừ khi FP mode cho phép.

---

# 479.57 — Optimization interaction

Contracts có thể hỗ trợ:

- bounds elimination;
- branch elimination;
- specialization;
- vectorization;
- devirtualization;
- nullability reasoning;
- range analysis.

---

## 479.58 — Contract safety

Compiler không được dùng ordinary checked contract như một excuse để tạo UB khi contract check bị disabled.

---

# 479.59 — `assume` boundary

Chỉ `assume` và explicitly trusted compiler facts mới được phép cung cấp optimization assumption mà không runtime verification.

---

# 479.60 — Debugging

Contract violation phải cung cấp:

```text id="d8r5q2"
contract ID
source span
function
actual state where available
call site
```

---

# 479.61 — AI diagnostics

AI có thể query:

```text
why did this contract fail?
what proof is missing?
which caller violates requires?
which check was optimized away?
```

---

# 479.62 — Contract coverage

477 có thể track:

```text
contract evaluated
contract passed
contract violated
contract statically proven
```

---

## 479.63 — Static vs runtime evidence

Coverage phải phân biệt:

```text
runtime passed
```

với:

```text
statically proven
```

---

# 479.64 — Fuzz integration

435 fuzzer có thể target contract violation để tìm counterexamples.

---

# 479.65 — Property testing

Contract có thể trở thành property oracle.

---

# 479.66 — Formal verification

Formal verification có thể là external/tooling layer.

Compiler core không bắt buộc phải là theorem prover.

---

## 479.67 — Verification plugin

External verifier có thể consume semantic metadata 446.

Không được thay đổi Axiom language semantics.

---

# 479.68 — Serialization

Contract metadata có thể được lưu trong semantic artifact.

---

# 479.69 — Public API

Public contracts nên được export trong package semantic metadata.

---

## 479.70 — Contract versioning

Thay đổi public contract có thể là API compatibility change.

447 tooling phải có khả năng detect.

---

# 479.71 — Performance

Contract overhead phải benchmark qua 450/476.

---

## 479.72 — Production policy

Developer có thể chọn contract profile theo package/build.

---

# 479.73 — No hidden checks

Compiler không được thêm contract checks không xuất phát từ:

- language semantics;
- explicit contract;
- explicit sanitizer/debug policy.

---

# 479.74 — No hidden assumptions

Optimizer không được silently assume arbitrary programmer intent.

---

# 479.75 — Hard invariants

1. Contract khác type.
2. Assertion khác contract.
3. Assume khác assertion.
4. Proof khác assumption.
5. Assertion có runtime semantics.
6. Debug assertion có thể bị loại bỏ.
7. Critical release assertion có thể được giữ.
8. Preconditions được hỗ trợ.
9. Postconditions được hỗ trợ.
10. `old()` được hỗ trợ khi cần pre-state.
11. Struct invariants được hỗ trợ.
12. Trait contracts được hỗ trợ.
13. Generic contracts được hỗ trợ.
14. Loop invariants được hỗ trợ.
15. Axiom không có class-contract inheritance.
16. Trait implementation phải tuân trait contract.
17. Implementation không được phá caller-visible precondition contract.
18. `assume` không runtime-check.
19. `assume` là low-level/unsafe facility.
20. Compiler có thể cảnh báo impossible assumptions.
21. Contract modes được hỗ trợ.
22. Contract failure có explicit behavior.
23. Contract failure không mặc định là Result.
24. FFI contracts được hỗ trợ.
25. Foreign contracts không tự động được coi là proven.
26. Ownership contracts không thay ownership semantics.
27. Resource contracts được hỗ trợ.
28. Concurrency contracts tích hợp 424.
29. Realtime contracts tích hợp 461.
30. Performance budget không phải hard guarantee mặc định.
31. Security contracts tích hợp 445/478.
32. Contract expressions được type-check.
33. Contract expressions không được hidden arbitrary side effects.
34. Contract expressions ưu tiên pure/deterministic.
35. Static contract proof được hỗ trợ.
36. `Unknown` khác `Disproven`.
37. Proven contract có thể loại runtime check.
38. Disproven precondition có thể là compile error.
39. RuntimeChecked được phân biệt với Proven.
40. Assumed được phân biệt với Proven.
41. Duplicate checks có thể được tối ưu.
42. Contract có thể hỗ trợ bounds-check elimination.
43. Contract không phá numeric semantics.
44. Floating-point contracts tôn FP mode.
45. Optimizer có thể sử dụng proven contracts.
46. Ordinary contract không được âm thầm biến thành UB.
47. Only explicit assumptions có thể cung cấp unchecked optimization facts.
48. Contract violation diagnostics machine-readable.
49. AI có thể query contract evidence.
50. Coverage phân biệt runtime evidence với static proof.
51. Fuzzing có thể target contract violations.
52. Property testing tích hợp contracts.
53. Formal verifier là optional.
54. External verifier consume semantic metadata.
55. Contract metadata có thể serialize.
56. Public contract được export.
57. Contract changes được versioned.
58. Contract overhead benchmark được.
59. Contract policy configurable.
60. Không hidden contract checks.
61. Không hidden optimizer assumptions.
62. Không yêu cầu GC.
63. Không yêu cầu borrow checker.
64. Không yêu cầu runtime verification toàn chương trình.
65. **Axiom contracts phải tạo ra một cầu nối rõ ràng giữa programmer intent, static proof, runtime verification và optimization, trong đó compiler tuyệt đối không được nhầm `assert`, `assume`, `proven` và `unknown`.**

**BOOTSTRAP-479 hoàn tất / LOCKED.**

---

# BOOTSTRAP-480 — SANITIZERS, RUNTIME VALIDATION, UNDEFINED-BEHAVIOR DETECTION & DEBUG INSTRUMENTATION

480 xây dựng lớp phát hiện lỗi runtime cho những lỗi mà type system, ownership và static analysis **không thể chứng minh hoàn toàn**.

Kiến trúc:

```text id="6nq2xe"
Axiom Program
      │
      ↓
Compiler / MIR
      │
      ├── Normal Build
      │
      └── Instrumented Build
              │
       ┌──────┼───────────┐
       ↓      ↓           ↓
    Memory  Integer     Concurrency
    Checks  Checks       Checks
       │      │           │
       └──────┼───────────┘
              ↓
       Runtime Diagnostics
              ↓
       Source → IR → ASM
```

## 480.1 — Sanitizer không thay đổi language semantics

Sanitizer là **diagnostic instrumentation**.

Một program không được coi là hợp lệ chỉ vì sanitizer không phát hiện lỗi trong một execution.

---

## 480.2 — Memory sanitizer foundation

Có thể kiểm tra:

- out-of-bounds;
- use-after-free;
- double-free;
- invalid free;
- use of uninitialized memory;
- invalid alignment;
- invalid pointer operation.

---

## 480.3 — Bounds sanitizer

Instrument array/slice access khi compiler không thể loại bỏ check.

---

## 480.4 — Alignment sanitizer

Phát hiện typed access không đúng alignment.

---

## 480.5 — Lifetime sanitizer

Theo dõi dynamic ownership/lifetime trong debug builds nếu cần.

Không biến lifetime sanitizer thành mandatory runtime ownership tracking.

---

## 480.6 — Integer sanitizer

Có thể phát hiện:

```text
signed overflow
shift overflow
invalid shift amount
```

theo selected arithmetic semantics.

Không được báo lỗi đối với operations được khai báo wrapping.

---

## 480.7 — Division sanitizer

Phát hiện:

```text
divide by zero
signed MIN / -1
```

khi semantics của operation yêu cầu detection.

---

## 480.8 — Floating-point sanitizer

Có thể instrument:

```text
NaN
Inf
FP exceptions
```

nhưng phải explicit vì NaN/Inf thường là valid IEEE-754 values.

---

## 480.9 — Concurrency sanitizer

Có thể phát hiện một số:

- data races;
- lock-order violations;
- synchronization misuse;
- atomic misuse.

Không tuyên bố mọi race được tìm thấy.

---

## 480.10 — Thread sanitizer

Thread sanitizer có thể theo dõi memory accesses và synchronization events.

Overhead lớn → development-only profile.

---

## 480.11 — Uninitialized memory

Instrument hoặc poison uninitialized storage.

`MaybeUninit<T>` vẫn là explicit low-level mechanism.

---

## 480.12 — Pointer provenance

Sanitizer có thể kiểm tra pointer provenance violations trong instrumented builds.

---

## 480.13 — FFI sanitizer boundary

Foreign memory operations có thể được instrument khi runtime metadata cho phép.

Foreign code không thể được coi là fully instrumented nếu compiler không kiểm soát nó.

---

## 480.14 — Panic integration

Sanitizer violation có thể tạo diagnostic tương tự panic nhưng phải phân biệt:

```text
language panic
sanitizer violation
OS fault
```

---

## 480.15 — Stack checks

Có thể hỗ trợ:

```text
stack overflow
stack corruption
stack canary
```

ở platform/toolchain level.

---

## 480.16 — Control-flow integrity

Optional instrumentation:

```text
indirect call target
function pointer
return address
```

theo platform capability.

---

## 480.17 — Sanitizer profiles

Canonical:

```text
none
memory
integer
undefined
thread
address
control_flow
full-debug
```

Không phải target nào cũng hỗ trợ tất cả.

---

## 480.18 — Runtime validation

Runtime validation có thể kiểm tra invariants mà static analysis không chứng minh được.

Tích hợp 479 contracts.

---

## 480.19 — Optimization interaction

Sanitizer build phải hạn chế optimization transformations chỉ khi cần giữ detection semantics.

---

## 480.20 — False positives

Sanitizer phải ưu tiên factual runtime evidence.

---

## 480.21 — False negatives

Không phát hiện lỗi không có nghĩa program không có lỗi.

---

## 480.22 — Source mapping

Mọi violation nên map:

```text
machine
→ MIR
→ semantic node
→ source
```

nếu metadata tồn tại.

---

## 480.23 — AI diagnostics

AI có thể query:

```text
what happened?
where?
which memory object?
which operation?
which call path?
which contract?
which thread?
```

---

## 480.24 — Artifact separation

Sanitized binary có thể có:

```text
larger code
extra runtime
debug metadata
```

và không được nhầm với production artifact.

---

## 480.25 — Performance overhead

450/476 phải benchmark sanitizer overhead.

---

## 480.26 — No mandatory runtime

Normal Axiom executable không được link sanitizer runtime.

---

## 480.27 — Hard invariants

480 sẽ khóa tiếp toàn bộ semantics về sanitizer mà không làm phình production binary.

**BOOTSTRAP-480 sẽ là task kế tiếp được hoàn thiện trong chuỗi tự động.**