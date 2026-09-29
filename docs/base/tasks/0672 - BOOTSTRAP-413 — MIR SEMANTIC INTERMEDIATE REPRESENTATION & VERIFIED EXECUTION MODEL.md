# BOOTSTRAP-413 — MIR: SEMANTIC INTERMEDIATE REPRESENTATION & VERIFIED EXECUTION MODEL

**Trạng thái:** SPECIFIED / FROZEN  
**Phụ thuộc:** 408 Name Resolution → 409 Type System → 410 Trait System → 411 Ownership/Capability/Effect → 412 Closure/Callable

Đây là bước rất quan trọng: từ 413 trở đi, Axiom bắt đầu có **một semantic execution model trung tâm** để compiler, optimizer, debugger, verifier, AI và các backend cùng sử dụng.

Mục tiêu:

> **MIR phải đủ thấp để compiler tối ưu và codegen, nhưng đủ giàu semantic information để chứng minh ownership, capability, effect, async, GPU và concurrency trước khi biến thành machine code.**

---

# 413.1. MIR không phải AST thấp hơn

AST biểu diễn:

```text
programmer wrote what
```

HIR biểu diễn:

```text
programmer means what
```

MIR biểu diễn:

```text
program executes what
```

Machine IR biểu diễn:

```text
CPU/GPU executes how
```

Do đó:

```text
AST
 ↓
HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine IR
```

MIR là semantic boundary quan trọng nhất.

---

# 413.2. MIR phải độc lập với target

MIR không được chứa:

```text
x86 register
ARM register
RISC-V register
```

và không được phụ thuộc trực tiếp vào:

```text
PE
ELF
Mach-O
```

MIR phải mô tả semantics chung.

Ví dụ:

```text
MIR:
    add i32
```

sau đó target lowering quyết định:

```text
x86:
    add eax, ebx

ARM:
    add w0, w0, w1
```

---

# 413.3. MIR không được là “LLVM IR clone”

Axiom cần MIR riêng vì LLVM IR không phải semantic model hoàn chỉnh của Axiom.

Axiom MIR phải hiểu trực tiếp:

```text
Ownership
Capability
Region
Effect
Async state
Task
GPU domain
Storage domain
Drop
Pattern
Trait resolution
```

LLVM/không phải backend nào khác không cần hiểu các khái niệm này.

---

# 413.4. MIR là SSA-oriented

MIR dùng SSA làm nền tảng:

```text
x0
 ↓
x1
 ↓
x2
```

mỗi SSA value có definition duy nhất.

Điều này giúp:

- dataflow;
- constant propagation;
- dead-code elimination;
- alias analysis;
- register allocation;
- ownership tracking.

Nhưng Axiom MIR **không phải SSA thuần túy**.

Nó có semantic resource state.

---

# 413.5. MIR Value

Mỗi MIR value có:

```text
ValueId
TypeId
Definition
OwnershipState
CapabilityState
Region
EffectContext
StorageClass
DebugOrigin
```

Ví dụ:

```text
Value#42
type = Buffer
ownership = OWNED
storage = DYNAMIC
origin = source: line 12
```

---

# 413.6. MIR Place

Đây là abstraction rất quan trọng.

MIR phân biệt:

```text
Value
```

và:

```text
Place
```

`Place` đại diện cho vị trí có thể:

- đọc;
- ghi;
- move;
- drop.

Ví dụ:

```text
user.name
```

là:

```text
Place {
    base = user
    projection = field(name)
}
```

---

# 413.7. Place Projection

Các projection:

```text
FIELD
INDEX
SLICE
DEREF
VARIANT
TUPLE_FIELD
```

Ví dụ:

```text
matrix[row][column]
```

có thể thành:

```text
Place
 └─ index(row)
     └─ index(column)
```

Ownership/capability verifier có thể hoạt động trực tiếp trên Place.

---

# 413.8. Place là nền tảng của Partial Move

Ví dụ:

```axiom
let name = user.name
```

MIR:

```text
MOVE
    Place(user.name)
→
Value(name)
```

Ownership state:

```text
user.name = MOVED
user.id   = VALID
```

Đây là lý do MIR cần semantic Place thay vì chỉ SSA values.

---

# 413.9. Basic Block

MIR dùng CFG:

```text
BasicBlock
    statements*
    terminator
```

Ví dụ:

```text
BB0
 ↓
condition
 ├── BB1
 │
 └── BB2
      ↓
     BB3
```

Mỗi basic block kết thúc bằng terminator.

---

# 413.10. Terminators

Core:

```text
GOTO
BRANCH
SWITCH
RETURN
UNREACHABLE
CALL
INVOKE
PANIC
TRAP
AWAIT
YIELD
```

`CALL` có thể tạo continuation.

---

# 413.11. Statements

Các MIR operation cơ bản:

```text
ASSIGN
MOVE
COPY
LOAD
STORE
BORROW_READ
BORROW_MUT
DROP
ALLOC
DEALLOC
CAST
BITCAST
CALL
PHI
```

Tên có thể thay đổi trong implementation nhưng semantic categories phải giữ nguyên.

---

# 413.12. Không có “borrow instruction” runtime bắt buộc

Ví dụ:

```text
BORROW_READ
```

là semantic verifier operation.

Nó không nhất thiết compile thành:

```text
runtime borrow object
```

Optimizer có thể loại bỏ hoàn toàn.

Mục đích của nó là:

```text
ownership/capability proof
```

---

# 413.13. CALL trong MIR

Mỗi call record:

```text
CallSite {
    Target
    Arguments
    Receiver
    ReturnValues
    GenericSubstitution
    Effects
    RequiredCapabilities
    OwnershipConsumption
    ABI
}
```

Ví dụ:

```text
CALL
    target = Vec_add
    args = [a, b]
    consumes = [a, b]
    result = v3
```

---

# 413.14. Direct / Indirect / Closure / Dynamic Call

MIR phân biệt:

```text
CALL_DIRECT
CALL_FUNCTION_VALUE
CALL_CLOSURE
CALL_DYNAMIC
```

Nhưng chúng có thể được normalize thành một call semantic model.

Optimizer có thể biến:

```text
CALL_DYNAMIC
```

→

```text
CALL_DIRECT
```

nếu chứng minh target duy nhất.

---

# 413.15. Trait Calls

Sau 410, trait call đã được resolve.

Ví dụ:

```axiom
x.add(y)
```

MIR không nên giữ:

```text
"add"
```

mơ hồ.

Nó phải chứa:

```text
TraitId
ImplId
FunctionId
Substitution
DispatchKind
```

Ví dụ:

```text
CALL_DIRECT
target = Impl#42::add
```

nếu static dispatch.

---

# 413.16. Dynamic Dispatch

Nếu:

```axiom
dyn Printable
```

MIR:

```text
CALL_DYNAMIC
trait = Printable
method = print
object = v
```

Target lowering sau này mới quyết định vtable representation.

---

# 413.17. Drop trong MIR

Drop phải được **explicit hóa trước optimization cuối**.

Ví dụ:

```axiom
fn f() {
    let x = File(...)
}
```

MIR semantic:

```text
ALLOC/INIT x

...

DROP x

RETURN
```

Compiler có thể sau đó:

```text
inline
eliminate
stack-promote
```

nhưng semantic Drop event phải tồn tại trong verified MIR.

---

# 413.18. Drop Flags

Partial initialization cần drop state.

Ví dụ:

```text
User {
    id = valid
    name = moved
}
```

Compiler nội bộ có thể dùng:

```text
drop_flag(name)
```

hoặc state representation khác.

Nhưng đây là implementation detail.

Programmer không nhìn thấy drop flags.

---

# 413.19. Allocation trong MIR

MIR có semantic:

```text
ALLOC
DEALLOC
```

nhưng không có nghĩa:

```text
malloc()
free()
```

Ví dụ:

```text
ALLOC Buffer
```

có thể hạ thành:

```text
stack
heap
arena
pool
static
register
```

tùy optimizer/storage contract.

---

# 413.20. Stable Address

Nếu code yêu cầu:

```text
address_of(x)
```

thì storage address trở thành observable.

Compiler không còn được tự do:

```text
move x
scalarize x
relocate x
```

nếu phá stable-address contract.

MIR đánh dấu:

```text
ADDRESS_OBSERVABLE
```

hoặc tương đương.

---

# 413.21. Region trong MIR

Mỗi Place/Capability có region identity.

Ví dụ:

```text
Place:
    p.velocity

Region:
    R42
```

MIR verifier có thể chứng minh:

```text
R42 DISJOINT R43
```

để cho phép:

```text
WRITE(R42)
READ(R43)
```

---

# 413.22. Capability State

MIR verifier duy trì:

```text
CapabilityState {
    Reads
    Writes
    Moves
    Drops
}
```

Ví dụ:

```text
READ data
```

→

```text
Reads += R1
```

sau call:

```text
Reads -= R1
```

nếu capability chỉ ephemeral.

---

# 413.23. Effect State

MIR instruction có effect metadata.

Ví dụ:

```text
LOAD
    PURE

CALL read_file
    FS + IO

CALL send
    NETWORK + IO
```

Compiler có thể dùng để:

- sandbox;
- optimization;
- parallelization;
- compile-time validation;
- security analysis.

---

# 413.24. MIR Effect Composition

Function:

```text
A → B → C
```

effect được hợp thành:

```text
Effects(A)
 ∪ Effects(B)
 ∪ Effects(C)
```

Nhưng compiler có thể distinguish:

```text
MAY_EFFECT
MUST_EFFECT
```

ở analysis level.

Ví dụ dead branch có thể chứa FS operation nhưng không thực thi trên path đó.

---

# 413.25. Path-sensitive Verification

MIR verification phải path-sensitive ở mức cần thiết.

Ví dụ:

```axiom
if condition {
    use(x)
} else {
    move(x)
}
```

Sau merge, compiler không được coi:

```text
x = definitely valid
```

Nó phải có:

```text
VALID
or
MOVED
```

state merge.

---

# 413.26. State Join

Compiler định nghĩa lattice cho semantic states.

Ví dụ:

```text
VALID
MOVED
PARTIAL
UNKNOWN
```

Khi hai CFG branches merge:

```text
VALID + VALID
    → VALID

MOVED + MOVED
    → MOVED

VALID + MOVED
    → CONDITIONAL / UNKNOWN
```

Nếu sau đó operation yêu cầu `VALID`:

```text
→ reject
```

hoặc compiler yêu cầu branch refinement.

---

# 413.27. MIR Pattern Matching

`match` từ 409 phải được lower thành deterministic CFG.

Ví dụ:

```axiom
match value {
    Some(x) => foo(x)
    None => bar()
}
```

MIR:

```text
SWITCH variant(value)

Some:
    extract x
    ...

None:
    ...
```

Exhaustiveness đã được kiểm tra trước MIR.

MIR không cần giải lại pattern semantics.

---

# 413.28. Panic / Trap

MIR phân biệt:

```text
PANIC
TRAP
UNREACHABLE
```

`PANIC` có semantic error handling.

`TRAP` là immediate abnormal termination.

`UNREACHABLE` là compiler-proven unreachable state.

Compiler không được tự biến:

```text
PANIC
```

thành:

```text
UNREACHABLE
```

nếu panic là observable behavior.

---

# 413.29. Async MIR

Async function không nên codegen trực tiếp thành callback spaghetti.

MIR giữ:

```text
AWAIT
SUSPEND
RESUME
```

Ví dụ:

```text
BB0
 ↓
CALL io
 ↓
AWAIT
 ↓
SuspendPoint#1
 ↓
BB1
 ↓
use(result)
```

Async lowering phase sau đó chuyển thành coroutine state machine.

---

# 413.30. Coroutine State

Compiler tạo:

```text
CoroutineState {
    StateId
    LiveValues
    Captures
    DropState
}
```

Ví dụ:

```text
State 0:
    x
    task

await

State 1:
    x
    result
```

Chỉ values cần sống qua suspension mới phải tồn tại trong state.

---

# 413.31. Thread / Parallel MIR

MIR có semantic operation:

```text
SPAWN
JOIN
SEND
RECEIVE
LOCK
UNLOCK
ATOMIC
```

Nhưng đây vẫn là semantic operations.

Backend/runtime quyết định implementation.

---

# 413.32. GPU MIR

GPU operations có execution/storage domain:

```text
KERNEL_ENTRY
DEVICE_LOAD
DEVICE_STORE
BARRIER
GPU_ATOMIC
GPU_LAUNCH
GPU_SYNC
```

MIR verifier kiểm tra:

```text
CPU ↔ GPU domain
Host ↔ Device storage
```

trước khi codegen.

---

# 413.33. Memory Ordering

Atomic MIR operation phải chứa explicit semantic ordering:

```text
RELAXED
ACQUIRE
RELEASE
ACQ_REL
SEQCST
```

Compiler không được đổi ordering nếu làm thay đổi memory model.

Target lowering mới map:

```text
Axiom atomic
 ↓
x86
ARM
RISC-V
GPU
```

---

# 413.34. MIR và FFI

FFI call:

```text
CALL_EXTERN
```

phải chứa:

```text
ABI
Symbol
Parameter Layout
Return Layout
Safety
Effects
Ownership Contract
```

Ví dụ:

```text
CALL_EXTERN
    abi = C
    symbol = memcpy
    unsafe = true
```

Không cho codegen giả định FFI là pure nếu semantic metadata không nói vậy.

---

# 413.35. Verified MIR

Có hai trạng thái:

```text
MIR
VerifiedMIR
```

`VerifiedMIR` phải thỏa:

```text
type correctness
ownership correctness
capability correctness
effect correctness
drop correctness
control-flow correctness
async correctness
concurrency correctness
domain correctness
FFI correctness
```

Chỉ `VerifiedMIR` mới được phép đi vào aggressive optimization/codegen.

---

# 413.36. Optimization không được phá proof

Optimizer có thể:

```text
inline
DCE
CSE
constant fold
loop transform
vectorize
fusion
specialize
scalarize
```

nhưng phải preserve:

```text
observable semantics
ownership semantics
effects
atomic semantics
drop semantics
panic semantics
FFI semantics
```

Proof metadata có thể được invalidated và recomputed.

---

# 413.37. Semantic Optimization

Axiom nên có hai lớp optimization:

```text
Semantic Optimization
```

và:

```text
Machine Optimization
```

Semantic:

```text
inline
specialization
constant propagation
ownership-aware allocation elimination
closure elimination
async simplification
effect analysis
```

Machine:

```text
instruction selection
register allocation
scheduling
peephole
target-specific vectorization
```

Điều này giữ backend sạch.

---

# 413.38. MIR Debug Mapping

Mỗi MIR operation có:

```text
SourceSpan
ExpressionId
SymbolId
FunctionId
```

Ví dụ:

```text
MIR instruction #183
origin:
    file.ax:42:13
    ExpressionId 921
```

Cho phép debugger:

```text
source
 ↔
MIR
 ↔
machine instruction
```

kể cả khi optimized.

---

# 413.39. MIR Serialization

Axiom nên có format:

```text
.axmir
```

cho debug/research/compiler cache.

Nhưng `.axmir` không mặc định là stable public ABI.

Nó phải có:

```text
compiler semantic version
MIR schema version
target-independent semantic hash
dependency fingerprints
```

---

# 413.40. CompilerDB

Thêm:

```text
MIRDB
MIRFunctionDB
MIRBlockDB
MIRValueDB
MIRPlaceDB
MIRControlFlowDB
MIROwnershipDB
MIRCapabilityDB
MIREffectDB
MIRDropDB
MIRAsyncDB
MIRConcurrencyDB
MIRGpuDB
MIRFFIDB
MIRVerificationDB
MIRDebugDB
```

Tất cả vẫn nằm trong `CompilerDB`.

Không tạo một compiler phụ.

---

# 413.41. MIR Proof Artifacts

Các proof:

```text
MIRTypeProof
MIROwnershipProof
MIRCapabilityProof
MIREffectProof
MIRDropProof
MIRControlFlowProof
MIRAsyncProof
MIRConcurrencyProof
MIRAtomicProof
MIRGpuProof
MIRFFIProof
MIRVerificationProof
```

Đặc biệt:

```text
MIRVerificationProof
```

phải có thể trả lời:

> “Tại sao function này được phép đi tới codegen?”

---

# 413.42. AI có thể đọc MIR

AI interface:

```text
axiom emit --mir
axiom explain --mir
axiom explain --ownership
axiom explain --capability
axiom explain --effects
```

Ví dụ AI hỏi:

```text
Why can't these two calls run in parallel?
```

Compiler có thể trả:

```text
Call A:
    WRITE R42

Call B:
    READ R42

relation:
    SAME

therefore:
    execution conflict
```

AI không phải tự phân tích source một cách mù mờ.

---

# 413.43. MIR Invariants — `AMIR`

```text
AMIR-01  Every MIR value has a valid type.
AMIR-02  Every MIR definition dominates its uses.
AMIR-03  Every Place has valid provenance.
AMIR-04  Every read has a valid READ capability.
AMIR-05  Every write has a valid exclusive WRITE capability.
AMIR-06  Every move has a valid ownership source.
AMIR-07  Moved values cannot be read.
AMIR-08  Values cannot be double-dropped.
AMIR-09  Partial moves preserve field ownership state.
AMIR-10  Every Drop obligation is represented.
AMIR-11  Allocation semantics are explicit.
AMIR-12  Allocation does not imply a specific physical allocator.
AMIR-13  Stable-address observations are explicitly marked.
AMIR-14  Region provenance is preserved.
AMIR-15  Unknown overlap cannot become proven disjoint.
AMIR-16  Effect metadata is preserved across calls.
AMIR-17  Capability requirements are explicit.
AMIR-18  FFI contracts are explicit.
AMIR-19  Atomic ordering is explicit.
AMIR-20  Async suspension state is explicit.
AMIR-21  Values live across suspension are explicitly represented.
AMIR-22  Thread-crossing values satisfy transfer rules.
AMIR-23  GPU domain boundaries are explicit.
AMIR-24  Host/device capabilities cannot silently cross domains.
AMIR-25  Pattern matching lowers to deterministic control flow.
AMIR-26  Panic/trap/unreachable semantics remain distinguishable.
AMIR-27  VerifiedMIR contains no unresolved semantic entity.
AMIR-28  Optimization preserves verified semantics.
AMIR-29  MIR debug provenance is preserved where possible.
AMIR-30  Only verified MIR may reach code generation.
```

---

# 413.44. Kiến trúc compiler sau 413

Đây là hình ảnh quan trọng:

```text
                       SOURCE
                          │
                          ▼
                    ┌──────────┐
                    │    AST   │
                    └────┬─────┘
                         ▼
                    ┌──────────┐
                    │   HIR    │
                    └────┬─────┘
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
           Types       Traits      Effects
             │           │           │
             └──────┬────┴────┬──────┘
                    ▼         ▼
                Ownership  Capability
                    └────┬────┘
                         ▼
                    ┌──────────┐
                    │   MIR    │
                    └────┬─────┘
                         ▼
                ┌────────────────┐
                │  Verification  │
                └───────┬────────┘
                        ▼
                  ┌────────────┐
                  │ VerifiedMIR │
                  └──────┬─────┘
                         ▼
              Semantic Optimization
                         ▼
                    Axiom LIR
                         ▼
                  Target Lowering
                         ▼
                    Machine IR
                         ▼
                    Codegen
```

Điểm mấu chốt của BOOTSTRAP-413:

> **MIR là “nguồn sự thật thứ hai” sau semantic HIR: mọi quyết định về ownership, capability, effect, Drop, async, concurrency, GPU và FFI cuối cùng phải được biểu diễn đủ rõ trong MIR để compiler có thể kiểm chứng và tối ưu mà không cần quay lại đoán từ source.**

**BOOTSTRAP-413 — SPECIFIED / FROZEN.**