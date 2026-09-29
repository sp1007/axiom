# BOOTSTRAP-254 — AXIOM SCOPE CLEANUP, `defer`, DESTRUCTOR ELABORATION & EARLY-EXIT CONTROL FLOW

**TRẠNG THÁI: FROZEN / COMPLETED**

## 1. Quyết định trung tâm

Axiom **không đưa `defer` vào Core v1**.

Thay vào đó:

```text
Drop
+
scope semantics
+
compiler-generated cleanup CFG
+
ScopeGuard library abstraction
```

đủ để giải quyết phần lớn nhu cầu cleanup.

Tuy nhiên, compiler phải có **cleanup infrastructure rất mạnh**. Đây là điểm quan trọng:

> Programmer không cần `defer`, nhưng compiler phải hiểu cleanup sâu hơn C++/Rust-style source semantics.

---

# 2. Tại sao không có `defer` Core?

`defer` có vẻ đơn giản:

```axiom
defer close(file)
```

nhưng nó tạo thêm một semantic mechanism cho:

- thứ tự cleanup;
- capture;
- ownership;
- exception/panic;
- `return`;
- `break`;
- `continue`;
- `?`;
- `yield`;
- `await`;
- nested scope;
- conditional registration.

Trong Axiom, resource cleanup đã có:

```text
Drop
```

và cleanup cần hành vi khác có thể dùng:

```text
ScopeGuard
```

library.

---

# 3. Ví dụ thông thường

```axiom
fn process() -> Result<(), Error> {
    let file = open("data.txt")?
    let buffer = allocate_buffer()?

    process_file(file, buffer)?

    Ok(())
}
```

Compiler tự tạo cleanup:

```text
return
  ↓
drop(buffer)
  ↓
drop(file)
  ↓
return
```

Không cần:

```text
defer buffer.free()
defer file.close()
```

---

# 4. Drop là semantic primitive

`Drop` không đơn giản là:

```text
destructor function
```

Nó là ownership cleanup contract.

Compiler biết:

```text
value initialized
→ value owns resource
→ scope exits
→ cleanup required
```

---

# 5. Drop order

Mặc định:

> **Reverse initialization order.**

Ví dụ:

```axiom
let a = A()
let b = B()
let c = C()
```

khi scope kết thúc:

```text
drop(c)
drop(b)
drop(a)
```

---

# 6. Vì sao reverse order?

Nó phù hợp với dependency tự nhiên:

```text
a
 ↓
b depends on a
 ↓
c depends on b
```

nên cleanup:

```text
c
 ↓
b
 ↓
a
```

---

# 7. Field Drop order

Struct:

```axiom
struct S {
    a: A
    b: B
    c: C
}
```

Nếu compiler-generated Drop:

```text
drop(c)
drop(b)
drop(a)
```

sau khi user-defined destructor logic, nếu có.

---

# 8. User-defined Drop

Axiom cho phép type định nghĩa cleanup behavior.

Conceptually:

```axiom
impl Drop for File {
    fn drop(self: mut_view<Self>) {
        ...
    }
}
```

Nhưng `Drop` không được dùng để phá ownership invariant.

---

# 9. Drop receiver

Drop phải có exclusive access tới resource state.

Do đó compiler conceptualizes:

```text
mut_view<Self>
```

nhưng đây không phải reference syntax programmer phải quản lý.

---

# 10. Drop không được Copy

Type có destructive cleanup:

```text
!Copy
```

bắt buộc.

---

# 11. Drop không được implicitly fail

Không cho:

```text
drop() -> Result
```

làm cơ chế implicit cleanup.

Lý do:

```text
scope exit
→ cleanup
→ cleanup fails
```

sẽ tạo vấn đề control-flow.

---

# 12. Fallible cleanup

Nếu cleanup có thể thất bại:

```axiom
file.close()?
```

phải explicit.

---

# 13. Ví dụ

```axiom
fn save(file: File) -> Result<(), Error> {
    write(file)?
    file.flush()?
    file.close()?
    Ok(())
}
```

`close()` có thể trả lỗi.

Drop vẫn là fallback resource release.

---

# 14. Drop không đồng nghĩa close

Đây là invariant quan trọng.

Ví dụ:

```text
Drop(File)
```

có thể release OS handle.

Nhưng:

```text
close()
```

có thể là protocol-level operation:

```text
flush
commit
shutdown
finalize
```

Hai semantic concepts khác nhau.

---

# 15. Early return

```axiom
fn f() -> Result<i32, Error> {
    let a = A()
    let b = B()

    if condition {
        return Ok(1)
    }

    Ok(2)
}
```

Return path:

```text
drop(b)
drop(a)
return
```

---

# 16. `?`

```axiom
let x = operation()?
```

Nếu operation thất bại:

```text
cleanup live locals
→ propagate error
```

---

# 17. `?` không bypass Drop

Invariant:

```text
Result propagation
```

phải đi qua cleanup.

---

# 18. `break`

```axiom
loop {
    let x = acquire()

    if done {
        break
    }
}
```

Trước `break`:

```text
drop(x)
```

---

# 19. `continue`

```axiom
loop {
    let x = acquire()

    if skip {
        continue
    }

    process(x)
}
```

`continue` cleanup những locals thuộc iteration scope trước khi quay lại loop.

---

# 20. Nested scope

```axiom
{
    let a = A()

    {
        let b = B()
    }

    let c = C()
}
```

Cleanup:

```text
drop(b)
drop(c)
drop(a)
```

---

# 21. Lexical scope là cleanup boundary

Mỗi scope có:

```text
ScopeId
```

và compiler biết:

```text
locals owned by scope
```

---

# 22. Scope không nhất thiết machine block

Optimizer có thể eliminate scope.

Nhưng semantic lifetime vẫn được xác định trước optimization.

---

# 23. Early Drop

Programmer có thể:

```axiom
drop(file)
```

để kết thúc ownership cleanup sớm.

Sau đó:

```text
file
```

không còn usable.

---

# 24. `drop(x)` không đảm bảo physical deallocation

Nó chỉ đảm bảo semantic Drop hoàn thành.

Compiler có thể:

```text
stack storage
→ dead
```

hoặc:

```text
heap storage
→ release
```

tùy storage contract.

---

# 25. Drop elaboration

Compiler stage:

```text
Typed MIR
 ↓
Ownership Verification
 ↓
Drop Elaboration
 ↓
Cleanup MIR
 ↓
Verified MIR
```

---

# 26. Tại sao Drop Elaboration sau verification?

Compiler cần biết:

```text
which values are definitely initialized
which fields moved
which capabilities live
which values need cleanup
```

sau đó mới sinh cleanup chính xác.

---

# 27. Drop flags

Compiler có thể cần internal state:

```text
drop_flag
```

cho partially initialized values.

Nhưng đây là compiler implementation detail.

---

# 28. Ví dụ partial move

```axiom
struct S {
    a: A
    b: B
}
```

Nếu:

```axiom
let s = S(...)
let x = s.a
```

thì:

```text
s.a = Moved
s.b = Owned
```

Nếu type cho phép partial move:

```text
drop(s.b)
```

không drop `s.a`.

---

# 29. User-defined Drop restriction

Nếu `S` có custom destructive Drop:

```text
partial move
```

bị hạn chế/reject theo frozen ownership rules.

---

# 30. Tại sao?

Custom Drop có thể cần toàn bộ invariant:

```text
S.a
S.b
```

nên compiler không thể coi từng field độc lập một cách an toàn.

---

# 31. Cleanup CFG

Compiler tạo explicit cleanup edges.

Ví dụ:

```text
       body
      /    \
   return  error
      \    /
      cleanup
         |
       exit
```

---

# 32. Cleanup chains

Mỗi exit point được nối vào cleanup chain tương ứng.

```text
return
break
continue
?
panic
yield
await
```

đều có thể cần cleanup/state handling.

---

# 33. Nhưng `yield` khác return

`yield` **không destroy generator state**.

Nó chỉ suspend.

Do đó:

```text
yield
→ preserve live state
```

không:

```text
yield
→ Drop locals
```

---

# 34. `await` cũng khác return

```text
await
```

giữ lại state cần thiết.

Locals không live across await có thể cleanup trước suspension.

---

# 35. Ví dụ

```axiom
async fn f() {
    let a = A()
    let result = await operation()

    use(a, result)
}
```

Nếu `a` cần sau await:

```text
a
```

trở thành Future state.

Nếu không:

```text
drop(a)
await
```

---

# 36. Generator

Tương tự:

```text
yield
```

chia control flow thành:

```text
before suspension
after suspension
```

và compiler phải xác định state ownership.

---

# 37. Cleanup + generator

Generator state:

```text
State1
 ├── A
 └── B

yield

State2
 └── A
```

Drop generator ở State1:

```text
drop(B)
drop(A)
```

State2:

```text
drop(A)
```

---

# 38. Cleanup + panic

Panic profile quyết định:

```text
abort
```

hoặc:

```text
unwind
```

Nếu unwind:

```text
panic
 ↓
cleanup
 ↓
caller
```

---

# 39. Abort profile

Nếu:

```text
panic = abort
```

không cần unwind tables/cleanup stack walking.

Tuy nhiên compiler vẫn phải đảm bảo semantics trước khi termination theo profile.

---

# 40. Unwind profile

Nếu enabled:

```text
panic
 ↓
unwind
 ↓
Drop
 ↓
catch boundary if supported
```

Axiom v1 **không có general exception catch**.

Unwind chỉ phục vụ cleanup/ABI/panic propagation.

---

# 41. No exception handler in Core

Không có:

```text
try
catch
finally
throw
```

---

# 42. `finally` vs Drop

Phần lớn:

```text
finally
```

được thay bằng ownership cleanup.

---

# 43. Nhưng arbitrary side-effect cleanup?

Dùng:

```text
ScopeGuard
```

library.

Ví dụ conceptual:

```axiom
let guard = ScopeGuard(|| cleanup())
```

Khi `guard` Drop:

```text
cleanup()
```

---

# 44. ScopeGuard không phải Core primitive

Nó chỉ là:

```text
struct ScopeGuard<F>
```

với:

```text
impl Drop
```

---

# 45. Đây là một điểm rất mạnh của Axiom

Nếu Axiom có:

```text
struct
closure
Drop
```

thì nhiều language features có thể được xây ở library.

Không cần:

```text
defer
finally
RAII keyword
cleanup keyword
```

---

# 46. ScopeGuard ownership

ScopeGuard owns closure:

```text
ScopeGuard<F>
    ↓
owns F
    ↓
F owns captured state
```

Drop chain tự động xử lý.

---

# 47. Cancel guard

Có thể implement:

```text
ScopeGuard::dismiss()
```

bằng cách chuyển state:

```text
Active
→ Dismissed
```

và Drop không chạy action.

Không cần compiler feature.

---

# 48. ScopeGuard + async

Một guard sống qua await phải tuân thủ async state rules.

Nếu guard không Send:

→ Future không Send nếu guard live across await.

---

# 49. ScopeGuard + generator

Tương tự.

Guard live across yield trở thành generator state.

---

# 50. No special-case cleanup object

Compiler chỉ thấy:

```text
ordinary owning value
+
Drop
```

---

# 51. Resource cleanup

Ví dụ File:

```text
File
  ↓
Drop
  ↓
release handle
```

---

# 52. Mutex guard

```text
MutexGuard
  ↓
Drop
  ↓
unlock
```

Do đó:

```text
scope exit
```

tự động unlock.

---

# 53. Semaphore permit

```text
Permit
 ↓
Drop
 ↓
release permit
```

---

# 54. Memory map

```text
Mapping
 ↓
Drop
 ↓
unmap
```

---

# 55. Device resource

```text
GpuResource
 ↓
Drop
 ↓
release
```

---

# 56. Compiler không cần biết từng resource

Đây là mục tiêu:

```text
Drop protocol
```

unifies cleanup semantics.

---

# 57. Nhưng không có universal Resource type

Giữ nguyên quyết định BOOTSTRAP-184:

```text
File
Socket
Process
MutexGuard
GpuBuffer
...
```

vẫn là các types khác nhau.

---

# 58. Cleanup dependency

Compiler có thể thấy:

```text
B depends on A
```

qua capability/ownership.

Drop order phải không phá invariant.

---

# 59. Capability prevents invalid Drop

Nếu:

```text
view(A)
```

đang live:

```text
drop(A)
```

bị reject.

---

# 60. Explicit `drop(A)`

Nếu còn:

```text
view(A)
```

compiler báo:

```text
ADROP-E001
cannot drop owner while dependent capability is live
```

---

# 61. Ending capability

Capability hết live khi:

```text
last semantic use
```

hoặc explicit scope termination/storage boundary.

Compiler có thể shorten capability lifetime.

---

# 62. This is not borrow syntax

Programmer không cần viết:

```text
'a
```

hay:

```text
borrow(...)
```

compiler tự phân tích.

---

# 63. Drop and alias analysis

Compiler phải biết:

```text
Drop(x)
```

invalidates capabilities/provenance liên quan đến `x`.

---

# 64. Drop and relocation

Drop không phải relocation.

Ví dụ:

```text
Vec
```

reallocation invalidates views.

Drop Vec destroys storage.

Hai events khác nhau.

---

# 65. Cleanup effect

Internal EffectInfo có:

```text
Drop
Deallocate
ExternalResource
```

---

# 66. Optimizer không được xóa observable Drop

Nếu Drop:

```text
close file
unlock mutex
zeroize secret
```

thì effect observable.

---

# 67. Nhưng pure Drop có thể optimize

Nếu compiler chứng minh Drop body không có observable effect:

```text
dead value
→ eliminate
```

nhưng chỉ sau semantic legality.

---

# 68. Zeroization exception

`SecureBuffer` có semantic zeroization requirement.

Compiler không được coi zeroization là dead store nếu contract yêu cầu observable security semantics.

---

# 69. Constant-time cleanup

Crypto types có thể có cleanup requirements compatible với constant-time/security model.

---

# 70. Drop ordering is semantic

Optimizer không được reorder:

```text
drop(B)
drop(A)
```

nếu thứ tự observable hoặc ownership dependencies yêu cầu.

---

# 71. Drop merging

Compiler có thể merge cleanup paths:

```text
error1 → cleanup
error2 → cleanup
return → cleanup
```

thành một cleanup block nếu semantics giữ nguyên.

---

# 72. Cleanup deduplication

Có thể:

```text
shared cleanup block
```

để giảm binary size.

---

# 73. Cleanup sinking

Compiler có thể kéo Drop tới điểm cuối chính xác nếu không thay đổi observable semantics.

---

# 74. Early destruction optimization

Nếu owner không còn được dùng:

```text
let x = Resource()
use(x)
...
// no more x
```

compiler có thể destroy `x` trước lexical scope end.

---

# 75. Nhưng có điều kiện

Chỉ được nếu:

```text
Drop effects
```

không thay đổi observable program behavior.

---

# 76. Ví dụ

```axiom
let lock = mutex.lock()
compute()
```

Không được unlock trước `compute()` chỉ vì compiler thấy `lock` không được đọc.

Vì `lock` giữ synchronization capability.

---

# 77. Resource lifetime may be semantically observable

Do đó:

```text
last use
```

không luôn đồng nghĩa:

```text
Drop now
```

Compiler cần effect/lifetime analysis.

---

# 78. Drop point

Internal MIR có thể có:

```text
DropPointId
```

để debugger/explain tooling truy nguyên.

---

# 79. Diagnostics

Ví dụ:

```text
AXIOM-E-DROP-001

value `file` is still required by capability `view`

drop(file) would invalidate a live capability
```

---

# 80. AI explanation

Compiler có thể trả:

```text
Owner:
    file

Dependent capability:
    view(buffer)

Conflict:
    DROP(file) vs READ(view(buffer))

Resolution:
    end capability before drop
```

---

# 81. Drop + Move

```axiom
let a = Resource()
let b = a
```

`a` moved.

Scope exit:

```text
drop(b)
```

không:

```text
drop(a)
```

---

# 82. Drop + Copy

Copy type không có destructive Drop.

Nếu:

```text
Copy(x)
```

có thể tạo independent semantic value.

---

# 83. Drop + Clone

Clone tạo owner mới nếu type semantics cho phép.

Do đó:

```text
original
+
clone
```

mỗi owner cleanup riêng.

---

# 84. Drop + function call

```axiom
consume(resource)
```

nếu function nhận ownership:

```text
caller loses ownership
callee responsible for Drop
```

---

# 85. Borrow-like view call

```axiom
inspect(resource)
```

nếu parameter expected `view<T>`:

```text
ephemeral capability
```

được tạo và hết sau call nếu không escape.

---

# 86. Mutable view call

```axiom
modify(resource)
```

compiler tạo exclusive capability trong call.

Sau call:

```text
capability ends
```

---

# 87. Cleanup after function call

Nếu function stores returned capability:

→ lifetime analysis continues.

Nếu ephemeral:

→ cleanup capability metadata only; không có physical runtime cost.

---

# 88. ScopeGuard ordering

```axiom
let a = A()
let guard = ScopeGuard(...)
```

cleanup:

```text
drop(guard)
drop(a)
```

Nếu guard cleanup cần `a`, thứ tự này phù hợp.

---

# 89. Vì vậy ScopeGuard phải được tạo sau resource nó bảo vệ

Đây là semantics tự nhiên, không cần special `defer`.

---

# 90. Nếu cần ngược lại

Programmer có thể tạo guard/resource theo thứ tự mong muốn.

---

# 91. Cleanup dependency verifier

Compiler có thể phát hiện:

```text
guard.Drop()
```

đang truy cập resource đã bị Drop trước đó.

Nếu dependency không biểu diễn được:

→ conservative handling/reject abstraction contract.

---

# 92. No hidden cleanup registration

Không có global:

```text
defer stack
```

runtime.

---

# 93. ScopeGuard physical implementation

Compiler có thể inline:

```text
ScopeGuard
```

và closure.

Có thể biến thành trực tiếp:

```text
cleanup()
```

ở exit paths.

---

# 94. Zero-cost goal

Do đó:

```axiom
let guard = ScopeGuard(...)
```

có thể compile thành zero extra allocation/object overhead.

---

# 95. Async cleanup

Không có `AsyncDrop`.

Frozen rule giữ nguyên:

> Drop không được `await`.

---

# 96. Tại sao?

Nếu Drop có thể suspend:

```text
drop(x)
→ await
→ drop(...)
```

thì mọi scope exit trở thành async state machine.

Điều đó tạo complexity rất lớn.

---

# 97. Async explicit cleanup

Nếu cần:

```axiom
await resource.close_async()
```

phải explicit.

---

# 98. Sau đó Drop fallback

Nếu resource vẫn owns handle:

```text
Drop
```

release synchronous/basic resource state.

---

# 99. Generator cleanup

Generator Drop không được implicit resume để chạy arbitrary user code sau suspension.

Cleanup phải nằm trong state machine's Drop path.

---

# 100. Generator `yield` cleanup boundary

Yield:

```text
preserve
```

Return:

```text
destroy
```

Drop generator:

```text
destroy remaining state
```

---

# 101. `break` from generator loop

Ordinary loop cleanup:

```text
iteration locals
→ continue generator execution
```

Generator remains alive.

---

# 102. `return` from generator

Cleanup all currently owned state:

```text
generator
→ Done
```

---

# 103. `panic` from generator

Follow panic profile.

---

# 104. Cleanup + FFI

Foreign function calls may establish resource ownership contracts.

Compiler uses:

```text
FfiContract
```

to determine cleanup responsibility.

---

# 105. FFI must not double release

If C API transfers ownership:

```text
Axiom owner
→ extern call
→ ownership transferred
```

Axiom no longer drops it.

---

# 106. Borrowed foreign resource

If FFI says:

```text
borrowed
```

Axiom does not Drop foreign resource.

---

# 107. Dynamic library lifetime

If symbol depends on library:

```text
Library
 ↓
Symbol
```

library cannot Drop while symbol capability remains live.

---

# 108. Thread cleanup

Thread handle Drop does not necessarily terminate thread.

Resource semantics remain explicit.

---

# 109. Process cleanup

Child handle Drop does not kill child.

`kill()` explicit.

---

# 110. File cleanup

Drop can release handle, but flush/commit is explicit.

---

# 111. Transaction cleanup

Transaction Drop must have explicitly defined semantics, e.g.:

```text
uncommitted transaction
→ rollback
```

if library contract chooses this behavior.

Not a Core rule.

---

# 112. Database cursor

Cursor Drop releases cursor resource.

It does not imply transaction commit.

---

# 113. UI resource

Widget ownership/Drop follows UI framework semantics.

---

# 114. GPU command buffer

Drop semantics must distinguish:

```text
recording
submitted
completed
```

Cannot release backing resource while GPU still uses it.

This is expressed by GPU ownership/completion contracts, not special `defer`.

---

# 115. GPU completion

```text
GpuEvent
```

can establish:

```text
GPU no longer accesses resource
```

after completion.

Then Drop becomes valid.

---

# 116. Network buffer

Async send:

```text
send(buffer)
```

may transfer ownership until completion.

Compiler ownership model prevents premature Drop.

---

# 117. Zero-copy consequence

This allows:

```text
buffer
→ network subsystem
```

without copying.

---

# 118. Memory-mapped file

```text
mapping
→ view
```

Drop mapping while view live:

→ reject.

---

# 119. Shared memory

Drop owner while shared capability exists:

→ contract must establish ownership boundary.

---

# 120. Reference counting

`Arc<T>` Drop decrements count.

Last owner releases resource.

This is library semantics, not GC.

---

# 121. Cycle

Arc cycles are not automatically collected.

Programmer uses weak references/explicit lifecycle.

No tracing GC fallback.

---

# 122. Cleanup and `Rc`

Single-threaded reference counting is deterministic:

```text
last owner
→ Drop
```

---

# 123. Cleanup and allocation

Drop may deallocate memory, but:

```text
Drop != Deallocate
```

semantic distinction remains.

---

# 124. Why?

Objects can:

```text
release OS resource
```

without deallocating storage.

Or:

```text
destroy value
```

while storage is arena-owned.

---

# 125. Arena example

```text
Arena
 ├── object A
 ├── object B
 └── object C
```

Individual Drop may run:

```text
A destructor
B destructor
C destructor
```

while physical arena memory remains until arena Drop.

---

# 126. Drop order inside arena

Arena abstraction owns policy.

Compiler only enforces type/resource contracts.

---

# 127. Compiler-generated cleanup vs allocator

Compiler must not assume:

```text
Drop == free()
```

---

# 128. Cleanup and stack

Stack storage can disappear automatically after semantic Drop.

No explicit runtime deallocation needed.

---

# 129. Cleanup and registers

Register-only value with trivial Drop may have no machine cleanup.

---

# 130. Cleanup and optimization

Physical cleanup may be eliminated if semantic effect is unobservable.

---

# 131. Cleanup and debug

Debug builds may preserve more explicit Drop points for debugging, but semantics remain identical.

---

# 132. Cleanup and `-O0`

`-O0` must not change:

```text
Drop order
ownership
capability validity
```

---

# 133. Cleanup and `-O3`

Same semantic result.

---

# 134. Cleanup and size profile

Size optimization can share cleanup blocks aggressively where legal.

---

# 135. Cleanup and LTO

LTO may discover:

```text
Drop body pure
```

and eliminate it.

Or:

```text
resource effect observable
```

and retain it.

---

# 136. Cleanup and exceptions from FFI

Foreign exception/longjmp behavior is not automatically understood.

FFI contract must declare behavior.

Unknown non-local control transfer is conservative/unsafe boundary.

---

# 137. `setjmp/longjmp`

Should be isolated in system/FFI layer.

Compiler must know that ordinary Axiom Drop guarantees can be bypassed by foreign non-local jumps.

Safe wrapper must establish appropriate contract.

---

# 138. Signal handlers

Signal handler cannot arbitrarily perform normal Drop/locking/IO unless platform contract permits.

Signal → notification → ordinary context remains preferred.

---

# 139. Thread cancellation

Forced external thread cancellation must not silently bypass Axiom cleanup.

Supported cancellation mechanisms must establish cleanup semantics.

---

# 140. Process termination

Normal:

```text
return from main
```

may execute normal process-level cleanup.

Explicit:

```text
exit
abort
```

have separate semantics.

---

# 141. `abort`

No guaranteed normal Drop after abort.

This must be documented semantic behavior.

---

# 142. `exit`

Process-level termination semantics depend on platform/runtime profile.

Resource cleanup belonging to ordinary lexical scopes still occurs before reaching explicit exit if control flow semantics require it.

---

# 143. `_Exit`-like behavior

System layer may expose immediate termination without normal cleanup.

Explicit unsafe/system semantics.

---

# 144. Initialization failure

If constructor/factory returns:

```text
Result<T,E>
```

partially initialized resources must be cleaned before returning error.

---

# 145. Struct initialization

```axiom
let s = S {
    a: make_a()?
    b: make_b()?
}
```

If `b` fails:

```text
drop(a)
```

before propagating error.

---

# 146. Field initialization order

Semantic evaluation follows source field initializer order as specified.

Cleanup applies only to successfully initialized fields.

---

# 147. Aggregate initialization

Compiler tracks:

```text
field initialized?
```

individually.

---

# 148. Array initialization

If array construction fails midway:

```text
initialized elements
```

are dropped exactly once.

---

# 149. Tuple initialization

Same field-wise rule.

---

# 150. Enum initialization

Payload is initialized before variant becomes fully initialized.

If payload initialization fails:

```text
partial payload
→ cleanup
```

variant does not become live.

---

# 151. Closure initialization

Captured values are initialized according to deterministic capture evaluation.

If later capture initialization fails:

```text
already initialized captures
→ Drop
```

---

# 152. Generator initialization

Generator creation may initialize captured/environment state.

If creation fails:

```text
partial environment
→ cleanup
```

Body itself has not run.

---

# 153. Future initialization

Same principle.

---

# 154. Comptime

Comptime resource cleanup happens in compiler execution environment.

No runtime Drop is generated unless resulting value has runtime Drop semantics.

---

# 155. Compiler architecture

Add:

```text
CleanupDB
DropDB
ScopeDB
ExitPathDB
DropElaborationDB
```

---

# 156. IDs

```text
ScopeId
DropPointId
CleanupBlockId
ExitPathId
DropFlagId
```

---

# 157. MIR additions

Conceptual:

```text
Drop(place)
CleanupBegin
CleanupEnd
```

and edge metadata:

```text
ExitKind {
    Return
    Break
    Continue
    Propagate
    Panic
    Yield
    Await
}
```

---

# 158. Important distinction

Not every `ExitKind` executes full cleanup.

For:

```text
Yield
Await
```

only non-live-across-suspension state may be destroyed.

---

# 159. Cleanup planning

Compiler algorithm:

```text
1. Build lexical scope tree
2. Determine ownership state
3. Determine capability dependencies
4. Determine Drop obligations
5. Determine exit paths
6. Compute cleanup sets
7. Generate cleanup CFG
8. Verify cleanup
9. Optimize
```

---

# 160. Cleanup correctness invariant

For every owned value:

```text
Initialized
→ exactly one of

Moved
Dropped
Live-at-program-exit
```

according to its ownership contract.

---

# 161. Exactly-once cleanup

No:

```text
double Drop
```

No:

```text
leaked required Drop
```

except explicitly permitted process-abort semantics.

---

# 162. Partial cleanup

If initialization fails:

```text
only initialized components
```

are cleaned.

---

# 163. Capability cleanup

When owner drops:

```text
dependent capabilities
```

must already be dead.

---

# 164. Escape

If value escapes scope:

```text
return
heap
thread
external
```

its ownership moves with it.

No Drop at old scope.

---

# 165. Return

```text
return x
```

means:

```text
transfer ownership
```

not:

```text
drop(x)
```

---

# 166. Returning struct field

```axiom
return s.field
```

field moves if allowed.

Remaining fields are cleaned according to partial-move rules.

---

# 167. Returning view

```text
return view(x)
```

only valid if provenance survives return.

---

# 168. Returning closure

Closure environment moves/escapes according to normal ownership.

---

# 169. Returning generator

Generator state moves out.

---

# 170. Returning Future

Future state moves out.

---

# 171. Return cleanup

Only non-returned owned state is dropped.

---

# 172. `break value`

If Core supports loop expressions:

```axiom
let x = loop {
    if done {
        break value
    }
}
```

the loop's temporary ownership state must be cleaned while the break value is transferred outward.

---

# 173. Continue

Iteration-local values drop before next iteration.

Loop-level values remain.

---

# 174. `match`

Each arm creates appropriate scope.

Only selected arm executes.

Its locals are cleaned when leaving the arm.

---

# 175. Pattern binding

Bindings are ordinary ownership values.

Move/copy rules apply.

---

# 176. Match guard

Temporary values/capabilities created by guard must end before branch execution unless semantically required.

---

# 177. `if`

Branch-local cleanup occurs when branch exits.

---

# 178. Loop body

Each iteration is a cleanup boundary for iteration-local values.

---

# 179. Loop-carried ownership

Values intentionally carried across iterations remain in loop state.

---

# 180. Infinite loops

Compiler does not assume unreachable cleanup unless termination semantics prove it.

---

# 181. `never`

A function returning `never` does not return normally.

---

# 182. Drop before diverging call

If:

```axiom
fatal(resource)
```

has type:

```text
never
```

whether `resource` is dropped first depends on semantic termination contract.

For ordinary Axiom `fn -> never`, entering the call is still a control-flow operation; required cleanup semantics must be preserved according to the call's effect/termination contract.

---

# 183. Compiler must not assume every `never` is abort

`never` means no normal return, not necessarily immediate process termination.

---

# 184. Panic

Panic is separate from `never` typing but can diverge.

---

# 185. Cleanup on panic

Configured panic profile determines whether stack cleanup is observable.

---

# 186. Panic handler

Optional runtime component.

---

# 187. No mandatory runtime

Drop implementation can compile entirely into local machine instructions.

---

# 188. Example

```axiom
struct Guard {
    lock: MutexLock
}
```

Drop:

```text
unlock
```

can inline to a single atomic instruction sequence.

No runtime object needed.

---

# 189. Scope cleanup can be extremely cheap

A high-level source program can compile approximately to:

```text
lock()
work()
unlock()
return
```

without hidden heap/runtime machinery.

---

# 190. Main architectural result

Axiom does **not** need:

```text
defer keyword
finally keyword
exception cleanup runtime
GC finalizer
```

to achieve deterministic cleanup.

---

# 191. Why `ScopeGuard` remains important

There are cases where programmer wants:

```text
action on scope exit
```

without creating a dedicated resource type.

For example:

```text
restore configuration
release temporary state
rollback logical operation
```

`ScopeGuard` handles these as ordinary library code.

---

# 192. But compiler may recognize ScopeGuard

Optional compiler optimization metadata can identify:

```text
Drop-only guard
```

and inline/eliminate its wrapper.

No semantic dependency on recognition.

---

# 193. `defer` could be future syntax

Not frozen out forever.

Future language version may add:

```text
defer
```

only if evidence shows ScopeGuard ergonomics are insufficient.

But v1 semantics do not depend on it.

---

# 194. Core philosophy preserved

```text
Language feature:
    only if it creates fundamental semantic capability.

Library abstraction:
    if existing primitives can express it.
```

`defer` falls into the second category.

---

# 195. Final cleanup architecture

```text
                    Scope
                      │
             ┌────────┴────────┐
             │                 │
          Owners          Capabilities
             │                 │
             └────────┬────────┘
                      │
                     Drop
                      │
              Cleanup Elaboration
                      │
                 Cleanup CFG
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    Return          Error          Panic
       │              │              │
     Break         `?`           Unwind
     Continue
       │
       ├──────── Yield
       │
       └──────── Await
```

---

# 196. Frozen invariants

```text
ACLEAN-20
Axiom Core v1 does not require a defer keyword.

ACLEAN-21
Deterministic cleanup is provided by ownership and Drop semantics.

ACLEAN-22
Every owned Drop-bearing value has a compiler-tracked cleanup obligation.

ACLEAN-23
Cleanup is deterministic.

ACLEAN-24
Default local cleanup order is reverse initialization order.

ACLEAN-25
Struct field cleanup follows defined field initialization/drop ordering rules.

ACLEAN-26
Cleanup does not depend on garbage collection.

ACLEAN-27
Cleanup does not require a monolithic runtime.

ACLEAN-28
Drop-bearing types are not Copy.

ACLEAN-29
Moved values are never implicitly dropped at the moved-from location.

ACLEAN-30
Copied values have independent semantic cleanup obligations only when their type semantics require them.

ACLEAN-31
Cloning is explicit.

ACLEAN-32
Partial initialization is tracked field-sensitively where permitted.

ACLEAN-33
Partially initialized values are cleaned only for initialized components.

ACLEAN-34
Moved fields are never dropped.

ACLEAN-35
Custom destructive Drop restricts partial moves.

ACLEAN-36
Cleanup executes on ordinary scope exit.

ACLEAN-37
Cleanup executes correctly on early return.

ACLEAN-38
Cleanup executes correctly on Result/Option propagation.

ACLEAN-39
Cleanup executes correctly on break.

ACLEAN-40
Cleanup executes correctly on continue.

ACLEAN-41
Cleanup executes correctly on panic according to the panic profile.

ACLEAN-42
Unwind cleanup is generated only when the selected profile requires it.

ACLEAN-43
Abort profiles do not require normal unwind cleanup machinery.

ACLEAN-44
Return transfers ownership of returned values instead of dropping them locally.

ACLEAN-45
Returning a partially moved aggregate drops only remaining owned components.

ACLEAN-46
Returned views require valid surviving provenance.

ACLEAN-47
An owner cannot be dropped while dependent safe capabilities remain live.

ACLEAN-48
Drop invalidates dependent capabilities.

ACLEAN-49
Capability lifetime is checked before cleanup elaboration.

ACLEAN-50
Unknown capability validity is never treated as valid.

ACLEAN-51
Drop is distinct from physical deallocation.

ACLEAN-52
Drop is distinct from fallible close/flush/commit operations.

ACLEAN-53
Fallible cleanup must be explicit.

ACLEAN-54
Drop must not require awaiting.

ACLEAN-55
Axiom Core has no AsyncDrop.

ACLEAN-56
Async resources requiring asynchronous cleanup use explicit async operations.

ACLEAN-57
Yield preserves state that is live across suspension.

ACLEAN-58
Yield does not perform ordinary generator destruction.

ACLEAN-59
Await preserves state that is live across suspension.

ACLEAN-60
State not live across yield/await may be cleaned before suspension.

ACLEAN-61
Suspended generator cleanup is deterministic.

ACLEAN-62
Suspended Future cleanup is deterministic.

ACLEAN-63
ScopeGuard is expressible as an ordinary owning type with Drop.

ACLEAN-64
ScopeGuard does not require a compiler primitive.

ACLEAN-65
ScopeGuard may own a closure.

ACLEAN-66
ScopeGuard cleanup follows ordinary ownership and Drop semantics.

ACLEAN-67
ScopeGuard cancellation is explicit state mutation.

ACLEAN-68
ScopeGuard does not require heap allocation.

ACLEAN-69
Scope cleanup does not require a hidden defer stack.

ACLEAN-70
Cleanup paths are represented explicitly in compiler IR.

ACLEAN-71
Cleanup blocks may be shared when semantic behavior is preserved.

ACLEAN-72
Cleanup code may be deduplicated by optimization.

ACLEAN-73
Cleanup may be inlined.

ACLEAN-74
Cleanup may be eliminated only when its semantic effects are proven unobservable.

ACLEAN-75
Observable Drop effects cannot be removed.

ACLEAN-76
Synchronization Drop effects cannot be removed or reordered illegally.

ACLEAN-77
Resource-release Drop effects cannot be removed when externally observable.

ACLEAN-78
Secure zeroization semantics cannot be removed when required by the type contract.

ACLEAN-79
Drop ordering cannot be changed when observable or required by dependency semantics.

ACLEAN-80
Compiler optimization cannot change semantic cleanup order.

ACLEAN-81
Physical storage lifetime may differ from semantic Drop lifetime.

ACLEAN-82
Stack, register, heap, arena, pool and static storage may use the same semantic Drop model.

ACLEAN-83
Drop does not imply a particular allocator.

ACLEAN-84
Arena-backed values may execute Drop without individually deallocating storage.

ACLEAN-85
Reference-counted values perform release according to their library semantics.

ACLEAN-86
Reference counting is not tracing garbage collection.

ACLEAN-87
Cycles are not automatically reclaimed.

ACLEAN-88
FFI ownership-transfer contracts determine cleanup responsibility.

ACLEAN-89
Borrowed foreign resources are not implicitly dropped by Axiom.

ACLEAN-90
Transferred foreign resources are not dropped by the old owner.

ACLEAN-91
Dynamic library lifetime dependencies prevent premature library release.

ACLEAN-92
GPU resources cannot be dropped while required GPU access remains live.

ACLEAN-93
GPU completion events may establish resource-release legality.

ACLEAN-94
Async network operations cannot observe prematurely dropped buffers.

ACLEAN-95
Database/storage resources obey explicit transaction and resource contracts.

ACLEAN-96
Process-handle Drop does not implicitly kill the process.

ACLEAN-97
Thread-handle Drop does not implicitly terminate the thread.

ACLEAN-98
Drop is not a universal OS-resource protocol.

ACLEAN-99
Distinct resource types remain distinct despite shared compiler cleanup machinery.

ACLEAN-100
`defer` is not required for deterministic resource cleanup.

ACLEAN-101
`finally` is not required for deterministic resource cleanup.

ACLEAN-102
Exception machinery is not required for deterministic resource cleanup.

ACLEAN-103
Library abstractions may implement scope-exit behavior using Drop.

ACLEAN-104
Compiler cleanup elaboration occurs before final optimization.

ACLEAN-105
Cleanup elaboration uses verified ownership and capability facts.

ACLEAN-106
Cleanup elaboration must not invent ownership.

ACLEAN-107
Cleanup elaboration must not silently discard ownership.

ACLEAN-108
Every generated cleanup path is itself subject to verification.

ACLEAN-109
Cleanup correctness is independent of optimization level.

ACLEAN-110
Cleanup correctness is independent of physical storage location.

ACLEAN-111
Cleanup correctness is independent of register allocation.

ACLEAN-112
Cleanup correctness is independent of allocator implementation.

ACLEAN-113
Cleanup correctness is independent of runtime composition.

ACLEAN-114
Cleanup state is represented in compiler-debug provenance.

ACLEAN-115
The compiler can explain why a value is dropped at a specific point.

ACLEAN-116
The compiler can explain why an early exit requires cleanup.

ACLEAN-117
The compiler can explain why an explicit drop is rejected.

ACLEAN-118
AI tooling cannot override cleanup verification.

ACLEAN-119
Comptime cleanup obeys the same ownership principles within the comptime environment.

ACLEAN-120
Comptime cleanup does not implicitly create runtime cleanup.

ACLEAN-121
Cleanup behavior is included in semantic equivalence testing.

ACLEAN-122
Cleanup behavior is included in panic/unwind conformance testing.

ACLEAN-123
Cleanup behavior is included in async conformance testing.

ACLEAN-124
Cleanup behavior is included in generator conformance testing.

ACLEAN-125
Cleanup behavior is included in FFI conformance testing.

ACLEAN-126
Cleanup behavior is included in GPU resource conformance testing.

ACLEAN-127
Cleanup behavior is included in resource adversarial testing.

ACLEAN-128
No safe program may cause double Drop.

ACLEAN-129
No safe program may read a value after semantic Drop.

ACLEAN-130
No safe program may retain a dangling capability after owner Drop.

ACLEAN-131
No safe program may bypass required cleanup through ordinary early control flow.

ACLEAN-132
Foreign non-local control flow requires an explicit FFI/system contract.

ACLEAN-133
Immediate process termination operations may bypass ordinary cleanup only when their explicit semantics permit it.

ACLEAN-134
Axiom does not guarantee cleanup after explicit abort-like termination.

ACLEAN-135
Cleanup semantics are deterministic and target-independent at the semantic level.
```

---

## Kiến trúc sau BOOTSTRAP-254

Đến đây control-flow/ownership của Axiom đã khá hoàn chỉnh:

```text
                  Axiom Control Flow
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
    Ordinary          Generator           Async
       │                 │                  │
     return            yield              await
     break             resume             resume
     continue          state              state
       │                 │                  │
       └─────────────────┼──────────────────┘
                         │
                  Ownership State
                         │
                 Capability State
                         │
                    Drop Analysis
                         │
                  Cleanup Elaboration
                         │
                     Verified MIR
```

Điểm đáng chú ý: **không cần `defer`, GC hay exception runtime để có cleanup mạnh**.

### BOOTSTRAP-255 tiếp theo

Phần tiếp theo nên chốt **AXIOM CONSTANTS, `const`, `static`, GLOBAL STATE, TLS & INITIALIZATION SEMANTICS** — đặc biệt giải quyết:

```text
const
static
static mut
TLS
global initialization
lazy initialization
init order
deinit order
cross-module globals
FFI globals
comptime-generated globals
freestanding/kernel globals
```

Đây là phần còn thiếu để mô hình **storage lifetime từ local → static → TLS → process lifetime** hoàn chỉnh.