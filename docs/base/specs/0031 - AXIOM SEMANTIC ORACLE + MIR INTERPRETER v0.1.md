Được. Ta đi tiếp sang **Semantic Oracle + MIR Interpreter v0.1**. Đây là checkpoint rất quan trọng: từ đây Axiom bắt đầu có một **“máy định nghĩa”** để mọi backend phải tuân theo.

# AXIOM SEMANTIC ORACLE + MIR INTERPRETER v0.1

## 1. Vai trò

Axiom không được để:

```text
x86 backend
ARM backend
LLVM backend
WASM backend
```

tự quyết định semantics.

Nguồn sự thật phải là:

```text
Axiom Source
      ↓
    HIR
      ↓
    MIR
      ↓
 Verified MIR
      ↓
┌─────────────────┐
│ Semantic Oracle  │
└────────┬────────┘
         │
         ├── Interpreter
         ├── Conformance tests
         └── Differential reference
```

Native backend chỉ cần chứng minh:

```text
Native(Source) == Oracle(Source)
```

ở observable behavior.

---

# 2. Oracle là gì?

**Semantic Oracle không phải VM của Axiom.**

Nó là một implementation tham chiếu của semantics.

Nhiệm vụ:

```text
Verified MIR
       ↓
 deterministic execution
       ↓
 observable result
```

Nó không cần:

- mô phỏng CPU
- mô phỏng cache
- register allocation
- pipeline CPU
- ABI thực tế
- instruction timing

Nó chỉ cần mô phỏng **ngữ nghĩa Axiom**.

---

# 3. Kiến trúc

Đề xuất:

```text
interpreter/
├── engine
│   ├── interpreter
│   ├── scheduler
│   └── execution
│
├── value
│   ├── runtime_value
│   ├── type_value
│   └── enum_value
│
├── memory
│   ├── allocation
│   ├── place
│   ├── region
│   └── provenance
│
├── ownership
│   ├── state
│   ├── move
│   └── drop
│
├── calls
│   ├── direct
│   ├── generic
│   └── dynamic
│
├── effects
│   ├── io
│   ├── resource
│   └── atomic
│
├── async
│   └── executor
│
├── ffi
│   ├── mock
│   └── host
│
└── trace
    ├── event
    └── formatter
```

---

# 4. RuntimeValue

Không dùng representation của native backend.

```text
RuntimeValue =
    Bool(bool)
    Integer(...)
    Float(...)
    Tuple(...)
    Struct(...)
    Enum(...)
    Array(...)
    Function(...)
    Closure(...)
    View(...)
    MutView(...)
    RawPointer(...)
```

Điểm quan trọng:

```text
RuntimeValue
```

không phải:

```text
ABIValue
```

Ví dụ `String` interpreter có thể là:

```text
StringValue {
    bytes
    encoding
}
```

trong khi native có thể là:

```text
ptr + len + capacity
```

Hai representation hoàn toàn khác nhau nhưng cùng semantics.

---

# 5. Semantic Allocation

Interpreter cần một memory model riêng.

```text
Allocation {
    id: AllocationId
    type: TypeId
    size: usize
    alignment: usize
    state: AllocationState
    data: SemanticStorage
}
```

`AllocationState`:

```text
LIVE
FREED
EXTERNAL
```

Không nhất thiết phải là byte array.

Có thể là typed tree:

```text
Struct
 ├── Field
 │    ├── value
 │    └── ownership
```

Điều này giúp debug rất dễ.

---

# 6. Tại sao không mô phỏng raw bytes ngay?

Nếu interpreter dùng:

```text
uint8_t memory[]
```

ngay từ đầu, chúng ta sẽ phải xử lý:

- alignment
- padding
- endian
- object layout
- pointer encoding
- ABI
- type punning

quá sớm.

Trong khi mục tiêu của semantic oracle là:

> kiểm tra language semantics, không phải backend ABI.

Do đó:

```text
Semantic memory
```

trước.

Raw byte semantics chỉ cần xuất hiện khi test:

```text
unsafe
FFI
repr(C)
volatile
raw pointer
```

---

# 7. Place resolution

MIR:

```text
FIELD_PLACE p, name
```

không load giá trị.

Interpreter resolve:

```text
p
 ↓
allocation
 ↓
field name
 ↓
PlaceHandle
```

Ví dụ:

```text
PlaceHandle {
    allocation: 42
    projection: [field(name)]
}
```

Sau đó:

```text
LOAD place
```

mới lấy RuntimeValue.

---

# 8. Ownership runtime state

Interpreter nên giữ debug ownership state:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

Dù Verified MIR đã chứng minh correctness.

Tại sao?

Để bắt bug compiler.

Nếu compiler tạo Verified MIR:

```text
MOVE x
LOAD x
```

thì interpreter phải báo:

```text
ORACLE_INTERNAL_ERROR:
invalid Verified MIR:
use-after-move
```

Chứ không được âm thầm chạy.

---

# 9. Đây là một invariant cực mạnh

> **Interpreter phải verify chính Verified MIR trong debug mode.**

Tức là:

```text
Verifier
    ↓
Verified MIR
    ↓
Interpreter
    ↓
runtime assertions
```

Ta có hai lớp kiểm chứng độc lập.

Nếu:

```text
Verifier says valid
Interpreter says invalid
```

=> compiler bug.

Nếu:

```text
Verifier rejects
```

thì interpreter không cần chạy program.

---

# 10. CallFrame

```text
CallFrame {
    function_id
    locals
    values
    current_block
    instruction_index
    return_target
}
```

Call stack:

```text
Frame A
 └─ Frame B
     └─ Frame C
```

Interpreter có thể trace:

```text
main
 → foo
   → bar
     → baz
```

---

# 11. Basic block execution

Pseudo-code:

```text
execute_function(fn, args):

    frame = create_frame(fn, args)

    while true:
        block = frame.current_block

        for instruction in block.instructions:
            execute(instruction, frame)

        execute_terminator(block.terminator, frame)
```

Không cần CPU simulator.

---

# 12. MIR instruction execution

Ví dụ:

```text
CONST
```

```text
result = RuntimeValue(...)
```

`COPY`:

```text
verify Copy
duplicate semantic value
```

`MOVE`:

```text
transfer ownership
invalidate source
```

`LOAD`:

```text
resolve place
read semantic value
```

`STORE`:

```text
resolve place
write semantic value
```

`DROP`:

```text
invoke semantic drop
mark ownership released
```

---

# 13. Arithmetic

Đây là chỗ Oracle phải cực kỳ nghiêm túc.

Không được dùng:

```text
host_language_integer + integer
```

một cách mù quáng.

Ví dụ Axiom:

```text
u8(255) + u8(1)
```

phải tuân theo **Axiom arithmetic mode**.

Ta cần freeze 3 dạng:

```text
checked
wrapping
saturating
```

Ví dụ:

```text
checked:
255 + 1 → overflow error/trap

wrapping:
255 + 1 → 0

saturating:
255 + 1 → 255
```

Syntax chính xác có thể freeze sau, nhưng Oracle phải có semantic operations riêng:

```text
INTEGER_ADD_CHECKED
INTEGER_ADD_WRAP
INTEGER_ADD_SAT
```

---

# 14. Không dùng host overflow semantics

Ví dụ interpreter viết bằng C/C++:

```text
int x = ...
x + y
```

không được coi là Axiom semantics.

Phải dùng helper:

```text
axiom_add_i32_checked()
axiom_add_i32_wrapping()
axiom_add_i32_saturating()
```

Nếu không, host compiler có thể phá Oracle bằng UB/optimization.

---

# 15. Bounds checking

MIR:

```text
INDEX_PLACE array, index
```

Oracle:

```text
if index >= length:
    PANIC
```

Nếu safe MIR đã proven bounds:

```text
BOUNDS_CHECK
```

có thể được optimizer loại bỏ.

Nhưng Oracle vẫn hiểu semantics.

---

# 16. Panic

Oracle event:

```text
PANIC {
    message
    source_location
}
```

Không coi panic giống return.

Execution:

```text
normal
    → return value

panic
    → cleanup according to profile
    → panic result
```

---

# 17. Trap

Trap:

```text
TRAP
```

khác:

```text
PANIC
```

Oracle result:

```text
ExecutionResult::Trap
```

Không biến thành `Result<T,E>`.

---

# 18. ExecutionResult

Đề xuất:

```text
ExecutionResult =
    Return(Value)
    Panic(PanicInfo)
    Trap(TrapInfo)
    Deadlock(DeadlockInfo)
    UnhandledFFI(FFIInfo)
    InternalError(OracleError)
```

`InternalError` tuyệt đối không phải semantics của Axiom.

Nó biểu thị:

> compiler/interpreter implementation có bug hoặc test yêu cầu unsupported behavior.

---

# 19. Event Log

Đây là phần rất đáng đầu tư.

```text
Event {
    kind
    location
    payload
}
```

Các event:

```text
CALL
RETURN
ALLOC
DEALLOC
DROP
MOVE
PANIC
TRAP
IO_READ
IO_WRITE
ATOMIC
LOCK
UNLOCK
SPAWN
SUSPEND
RESUME
```

Ví dụ:

```text
CALL File.open
ALLOC #12
CALL write
DROP File
DEALLOC #12
RETURN
```

---

# 20. Tại sao Event Log quan trọng?

Output giống nhau chưa chắc semantics giống nhau.

Ví dụ:

```text
Program A:
    write()
    close()

Program B:
    close()
    write()
```

final output có thể giống trong một test đơn giản.

Nhưng resource ordering khác.

Event trace phát hiện được.

---

# 21. Observable vs internal event

Không phải event nào cũng observable.

Ví dụ:

```text
ALLOC temporary
DEALLOC temporary
```

có thể bị optimizer eliminate.

Nhưng:

```text
WRITE stdout
LOCK mutex
UNLOCK mutex
VOLATILE STORE
```

là observable.

Do đó event có:

```text
visibility =
    INTERNAL
    OBSERVABLE
```

---

# 22. Differential testing

Đây sẽ trở thành test architecture chính:

```text
Source
  ↓
Verified MIR
  ├──────────────┐
  ↓              ↓
Interpreter    Native
  ↓              ↓
Trace          Trace
  └──────┬───────┘
         ↓
      Compare
```

Compare:

```text
Return value
Panic/trap
Observable output
Observable resource ordering
```

Không compare:

```text
register allocation
address
stack layout
instruction count
internal allocation
```

trừ khi test riêng backend.

---

# 23. Ví dụ

Source:

```axiom
fn main() -> i32 {
    let a = 10
    let b = 20
    a + b
}
```

Oracle:

```text
Return(30)
```

Native:

```text
Return(30)
```

=> pass.

---

# 24. Ownership test

```axiom
fn test() {
    let x = Buffer(...)
    consume(x)
}
```

MIR:

```text
x = ALLOC
MOVE x → consume
RETURN
```

Oracle trace:

```text
ALLOC x
CALL consume
DROP x_inside_consume
RETURN
```

Không có:

```text
DROP x
```

ở caller.

---

# 25. Partial move

```axiom
fn test() {
    let p = Person(...)
    consume(p.name)
}
```

Trace cuối:

```text
DROP p.age
```

Không:

```text
DROP p.name
```

Nếu interpreter thấy cả hai:

```text
OracleError: double ownership resolution
```

---

# 26. View

```axiom
fn test() {
    let p = Person(...)
    let v = view(p.name)

    use(v)
}
```

Event:

```text
CREATE_VIEW
USE_VIEW
END_VIEW
DROP p
```

`CREATE_VIEW` không:

```text
ALLOC
```

Không có heap allocation chỉ vì tạo view.

Đây là một test performance-semantic rất quan trọng.

---

# 27. Ephemeral view

```axiom
sum(numbers)
```

Không nhất thiết tạo persistent runtime object.

Oracle có thể ghi:

```text
BEGIN_EPHEMERAL_VIEW
CALL sum
END_EPHEMERAL_VIEW
```

Không:

```text
ALLOC view_object
```

---

# 28. Vec relocation

Oracle memory model nên có:

```text
StorageIdentity
```

Ví dụ:

```text
Vec #10
storage #42
```

Sau reallocation:

```text
Vec #10
storage #91
```

Nếu view đang trỏ:

```text
provenance = #42
```

thì view invalid.

Verified MIR không được chứa operation sử dụng view đó sau relocation.

Nếu có:

```text
OracleError
```

=> verifier bug.

---

# 29. Semantic allocation ≠ physical allocation

Ví dụ optimizer:

```text
Vec
```

có thể cuối cùng không heap allocate.

Oracle vẫn có thể mô hình hóa:

```text
ALLOC semantic storage
```

vì language semantics nói nó là owning dynamic storage.

Native optimizer có thể eliminate allocation nếu observable semantics không thay đổi.

Đây là abstraction cực kỳ quan trọng.

---

# 30. Generic functions

Oracle không cần generic interpreter.

Trước khi chạy:

```text
fn max<T>(...)
```

compiler specialize:

```text
max<i32>
```

HIR/MIR:

```text
specialized function
```

Oracle chạy function đã specialize.

Như vậy:

```text
Generic semantics
```

được kiểm tra trước:

```text
Monomorphization
```

hoặc trong specialization pipeline.

---

# 31. Trait dispatch

Static:

```axiom
x.draw()
```

MIR:

```text
CALL Drawable::draw<Circle>
```

Oracle gọi trực tiếp.

Không cần runtime vtable.

Dynamic:

```axiom
dyn Drawable
```

thì MIR:

```text
DYNAMIC_CALL
```

Oracle dùng dispatch metadata.

---

# 32. Async Oracle

Không dùng OS threads để test semantics mặc định.

Thay bằng:

```text
VirtualExecutor
```

có scheduler deterministic.

Ví dụ:

```text
Task A
Task B
Task C
```

scheduler:

```text
A → B → C → A → ...
```

hoặc explicit schedule trong test.

---

# 33. Vì sao deterministic scheduler cực kỳ quan trọng?

Nếu test concurrency bằng:

```text
real OS threads
```

thì:

```text
pass
pass
pass
fail
pass
```

rất khó debug.

Oracle có thể test:

```text
schedule #1
schedule #2
schedule #3
...
```

và reproduce chính xác:

```text
seed = 18273
```

---

# 34. Atomic semantics

Oracle phải mô hình hóa:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Nhưng **không cần mô phỏng CPU cache**.

Ở v0.1, có thể bắt đầu với sequentially consistent reference model để xây semantics, sau đó mở rộng memory-order model trước khi freeze atomics đầy đủ.

Tôi không khuyến nghị giả vờ rằng một simulator đơn giản đã chứng minh tất cả memory-order semantics.

---

# 35. FFI

Oracle không thể thực thi mọi OS API.

Do đó FFI có 3 mode:

```text
KNOWN_INTRINSIC
HOST_CALLBACK
UNSUPPORTED
```

Ví dụ:

```text
extern @abi(C) fn puts(...)
```

test có thể đăng ký:

```text
host_callback("puts")
```

và Oracle ghi:

```text
IO_WRITE("...")
```

---

# 36. Unsafe

Oracle vẫn phải chạy unsafe.

Nhưng có hai tầng:

```text
safe semantic checks
unsafe machine-like semantics
```

Raw pointer:

```text
*mut T
```

có thể mang:

```text
Pointer {
    address
    provenance
}
```

Trong debug Oracle có thể kiểm tra:

```text
bounds
alignment
allocation validity
```

nhưng phải ghi rõ:

> Đây là **debug oracle instrumentation**, không phải semantics mới của safe Axiom.

---

# 37. Oracle invariant

### AO-01

Interpreter chỉ chạy Verified MIR trong normal mode.

### AO-02

Mọi MIR instruction có semantic execution rule.

### AO-03

RuntimeValue độc lập với native ABI.

### AO-04

Semantic allocation độc lập với physical allocation.

### AO-05

Ownership violations trong Verified MIR là compiler bugs.

### AO-06

Observable event ordering phải deterministic.

### AO-07

Panic và trap khác nhau.

### AO-08

Drop events phải phản ánh Verified MIR.

### AO-09

Unsafe instrumentation không được thay đổi safe semantics.

### AO-10

Oracle không được phụ thuộc LLVM.

### AO-11

Oracle không được phụ thuộc target backend.

### AO-12

Interpreter và native backend có thể được differential-tested.

---

# 38. Một quyết định kiến trúc rất quan trọng

Tôi đề xuất **không viết interpreter trước MIR**.

Thứ tự:

```text
AST
 ↓
HIR
 ↓
MIR
 ↓
Verifier
 ↓
Drop Elaboration
 ↓
Verified MIR
 ↓
Interpreter
```

Nếu viết interpreter quá sớm, agent rất dễ:

```text
Source
 → parser
 → interpreter
```

và vô tình tạo một **ngôn ngữ thứ hai** với semantics riêng.

Ta tuyệt đối tránh.

---

# 39. Semantic Oracle không được parse Source

Oracle API nên là:

```text
execute(
    verified_mir_module,
    entry_function,
    args,
    execution_config
)
```

Không:

```text
execute(source_text)
```

Source compiler và Oracle phải tách biệt.

---

# 40. ExecutionConfig

```text
ExecutionConfig {
    panic_mode
    max_steps
    deterministic_scheduler
    ffi_mode
    trace_level
    debug_memory
    debug_ownership
}
```

Ví dụ:

```text
axiom run test.ax \
    --engine=interpreter \
    --trace \
    --panic=unwind
```

---

# 41. CLI architecture

Đề xuất:

```text
axiom check file.ax
axiom build file.ax
axiom run file.ax
axiom interpret file.ax
axiom test
axiom dump-mir file.ax
axiom dump-verified-mir file.ax
axiom trace file.ax
```

Nhưng:

```text
interpret
```

chỉ là:

```text
compile → verify → elaborate → execute
```

không phải một compiler riêng.

---

# 42. Conformance test format

Tôi khuyên ngay từ đầu dùng metadata có cấu trúc:

```text
TEST:
    id: OWN_MOVE_001
    mode: compile
    expect: reject
    diagnostic: AX_OWN_0001
```

Runtime:

```text
TEST:
    id: DROP_ORDER_001
    mode: differential
    expect:
        return: 0
        events:
            - CREATE(A)
            - CREATE(B)
            - DROP(B)
            - DROP(A)
```

---

# 43. Không snapshot toàn bộ MIR

Không nên:

```text
expected_mir.txt
```

rồi bắt compiler phải tạo chính xác từng instruction.

Thay vào đó:

```text
assert:
    contains MOVE
    contains DROP
    not_contains DROP(name)
```

hoặc:

```text
assert:
    observable_events == [...]
```

Điều này cho phép compiler evolve.

---

# 44. Ba lớp test

Axiom nên có:

```text
Level 1:
Semantic tests

Level 2:
Verified MIR property tests

Level 3:
Execution tests
```

Ví dụ:

```text
Source
 ↓
Level 1: accept/reject?
 ↓
Level 2: MOVE/DROP/VIEW đúng?
 ↓
Level 3: output/event đúng?
```

---

# 45. Differential matrix

Khi native backend đầu tiên xuất hiện:

```text
                  Interpreter
                       │
                       │
Source → Compiler → Verified MIR
                       │
                       ├────────→ x86-64
                       ├────────→ ARM64
                       ├────────→ WASM
                       └────────→ ...
```

Mỗi backend phải pass cùng semantic suite.

Đây là cách Axiom có thể thêm backend mà không làm semantics trôi.

---

# 46. Quan trọng hơn nữa: Reference Interpreter không phải production runtime

Binary:

```text
axiom program
```

không cần chứa interpreter.

Interpreter chỉ tồn tại:

```text
compiler development
testing
debugging
formal-ish validation
```

Production:

```text
Source
→ Verified MIR
→ optimized machine code
```

Không interpreter.

---

# 47. Hiện tại Axiom đã có một nền móng khá hoàn chỉnh

Ta đang có:

```text
                 AXIOM
                   │
        ┌──────────┴──────────┐
        │                     │
    Language               Compiler
        │                     │
   ┌────┴────┐          ┌─────┴─────┐
   │ semantics│          │    MIR    │
   └────┬────┘          └─────┬─────┘
        │                     │
 ownership/view        verification
 regions/effects              │
 concurrency                   │
        │                Drop elaboration
        └──────────┬──────────┘
                   ↓
             Verified MIR
                   ↓
            Semantic Oracle
                   ↓
              Conformance
                   ↓
              Optimization
                   ↓
                 LIR
                   ↓
             Native Backend
```

Và có một lợi ích rất lớn:

**Chúng ta chưa cần quyết định x86-64 assembly syntax, register allocator hay ELF writer để tiếp tục xây language.**

---

## 48. Bước tiếp theo tôi đề xuất

Bây giờ đã đủ nền tảng để chuyển sang một phần còn quan trọng hơn cả optimizer:

# **AXIOM EXECUTION SEMANTICS v0.1**

Cụ thể cần freeze chính xác:

```text
integer arithmetic
floating-point
casts
comparison
boolean short-circuit
evaluation order
assignment/replacement
indexing
enum
Option
Result
panic
trap
assert
unreachable
function calls
recursion
static/global
thread-local
atomics
volatile
I/O observable boundaries
```

Đặc biệt **numeric semantics và assignment/replacement semantics** cần làm trước backend, bởi nếu chúng chưa được freeze thì Semantic Oracle chưa thực sự là một oracle đáng tin cậy.

Sau đó ta có thể đưa Axiom tới trạng thái rất quan trọng:

```text
                 AXIOM CORE v0.1
                       │
                SEMANTIC FREEZE
                       │
              ┌────────┴────────┐
              ↓                 ↓
        Verified MIR       Semantic Oracle
              │                 │
              └────────┬────────┘
                       ↓
               CONFORMANCE SUITE
                       │
                       ↓
                Compiler Agent
```

Từ thời điểm đó, AI agent có thể **tự viết compiler và tự chứng minh implementation của nó khớp semantics**, thay vì mỗi agent tự “hiểu” Axiom theo một cách khác.