# SPEC-62 — Canonical Generators, `yield` Suspension, Iterator State Machines & MIR Verification Specification

Status: draft (T561, 2026-11-03)
Owner: axiom-architect
Consolidates: `tasks/0512 (§1–203, AGEN-20..140)`; `tasks/0539 (§1–89, AMIR-20..90)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-33-async.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-60-comptime-2-0.md`; `spec/SPEC-72-loops-scev-bce.md`; `spec/SPEC-73-inlining-specialization-devirt.md`.
Covers: `REQ-CORE-2989`..`2998` (and specifies the E14.3 contract for `T562`–`T565`: `REQ-CORE-2999`..`3030`, `REQ-EXP-325`..`447`).
Consumers: `compiler/ast/`, `compiler/parser/`, `compiler/hir/`, `compiler/own/`, `compiler/mir/gen_lower.ax`, `compiler/verify/`, `compiler/interp/`, `compiler/lowering/`, `std/iter/`, `T562`–`T565`.

## Tóm tắt

Tài liệu `SPEC-62` chuẩn hóa ngữ nghĩa ngôn ngữ và MIR cho hàm sinh đồng bộ (**synchronous generators**: `gen fn`, `yield`), máy trạng thái bộ lặp không cấp phát heap (**zero-heap iterator state machines**), quy tắc ownership/capability qua điểm tạm dừng `yield`, cơ chế dọn dẹp `Drop` tất định theo từng trạng thái, và ranh giới hạ bậc HIR → MIR cho phân hệ `E14.3` (Phase `P14`):
- **Generator là máy trạng thái hữu hạn kéo (`pull-based`) không cần runtime và không bắt buộc cấp phát heap (`AGEN-20..28`, `AGEN-71..84`, `AGEN-111..112`, `AGEN-134..140`, `AMIR-60`, `REQ-EXP-325`, `REQ-EXP-327..335`, `REQ-CORE-3030`)**: Khai báo `gen fn name(...) -> Yield<T>` (hoặc `Generator<T>` / `impl Iterator<Item = T>`) được trình biên dịch hạ bậc thành một struct máy trạng thái không ngăn xếp riêng (`stackless state machine`) thực thi giao diện `Iterator<Item = T>`. Việc gọi `gen fn` là lười (`lazy`): chỉ khởi tạo giá trị máy trạng thái ở `state_tag = 0` cùng các tham số đầu vào mà không thực thi bất kỳ câu lệnh nào trong thân hàm cho đến khi `next(mut_view(g))` được gọi.
- **Quy tắc ownership, phân tích biến sống qua `yield` (`LiveAcrossYield`) và an toàn capability (`AGEN-29..64`, `AMIR-29..37`, `AMIR-47..55`, `REQ-EXP-326`, `REQ-EXP-336..371`, `REQ-CORE-2999..3007`, `T562`)**: Generator tuân thủ mô hình ownership chuẩn (`SPEC-10`), mặc định là `!Copy`, chuyển quyền sở hữu qua `Move` và chỉ nhân bản tường minh qua `Clone`. Chỉ các biến cục bộ thực sự còn sống qua một điểm tạm dừng `YieldPointId` mới được lưu giữ trong struct trạng thái; các biến chết trước `yield` bị loại khỏi khung trạng thái. Theo nguyên tắc `UNKNOWN != SAFE`, mọi capability tạm thời (`view<T>`, `mut_view<T>`) hoặc phép mượn tự tham chiếu vào biến cục bộ của generator đều bị từ chối tĩnh nếu đi qua `yield` (`AX_GEN_VIEW_ACROSS_YIELD`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`), và mọi view được `yield` ra ngoài phải có nguồn gốc (`provenance`) hợp lệ từ tham số đầu vào hoặc vùng nhớ tĩnh sống lâu hơn lần gọi `next()`.
- **Hoàn tất kết thúc (`Terminal Completion`), dọn dẹp `Drop` theo từng trạng thái và ranh giới hạ bậc HIR → MIR (`AGEN-37..49`, `AGEN-65..70`, `AMIR-20..28`, `AMIR-38..46`, `REQ-CORE-2989..2998`, `REQ-CORE-3008..3018`, `T563`)**: Khi thân hàm kết thúc (`return` không kèm giá trị) hoặc bị panic, generator chuyển sang trạng thái kết thúc vĩnh viễn (`STATE_COMPLETE = u32.MAX`) và mọi lần gọi `next()` tiếp theo luôn trả về `Option.None`. Khi một generator đang tạm dừng ở trạng thái `k` bị hủy sớm (ví dụ `break` khỏi vòng lặp `for`), hàm hủy `Drop` theo trạng thái chỉ dọn dẹp đúng các biến đang sở hữu tại trạng thái `k` theo thứ tự ngược khai báo mà không rò rỉ tài nguyên hay hủy kép. Phép hạ bậc HIR → MIR tiêu thụ trực tiếp sự kiện ngữ nghĩa từ Typed HIR mà không suy đoán lại kiểu, tên, quá tải hay ép kiểu ngầm (`REQ-CORE-2989..2998`).
- **Tích hợp `for-in`, bộ kết hợp `std.iter` lười và thực thi `comptime` (`AGEN-92..110`, `AGEN-127..133`, `AMIR-49..60`, `REQ-CORE-3019..3030`, `T564`, `T565`)**: Máy trạng thái generator tích hợp trực tiếp với vòng lặp `for x in gen(...)`, các bộ biến đổi lười trong `std.iter` (`map`, `filter`, `take`, `skip`, `zip`, `chain`, `enumerate`, `flatten`, `fold`, `collect`), ủy quyền lồng nhau và đánh giá `comptime` dưới ngân sách bước thực thi.

---

## 1. Generator Syntax, Lazy Semantics & Iterator Protocol (`AXS-GEN-001`..`004`)

### AXS-GEN-001 — Generator Architecture: Zero-Runtime Pull-Based State Machine (`AGEN-20..28`, `AGEN-71..72`, `AGEN-78..81`, `AGEN-134..139`, `AMIR-60`, `REQ-EXP-325`, `REQ-EXP-327`..`335`, `REQ-CORE-3030`)

1. **Compiler-Generated State Machine Implementing `Iterator` (`tasks/0512 §1–14, §201 AGEN-20..21, AGEN-71..72`, `REQ-EXP-325`, `REQ-EXP-327..328`, `REQ-EXP-378..379`)**:
   - Axiom Core v1.0 supports `yield` inside generator contexts (`AGEN-20`, `REQ-EXP-327`). A generator is not a special runtime object or second object model (`AGEN-72`, `REQ-EXP-379`); it is a compiler-synthesized stackless state machine implementing the standard library `Iterator<Item = T>` protocol (`AGEN-21`, `AGEN-71`, `REQ-EXP-325`, `REQ-EXP-328`, `REQ-EXP-378`).
2. **Pull-Based, Zero-Runtime & Zero-Heap By Default (`AGEN-24..28`, `AGEN-78..81`, `AGEN-134..139`, `AMIR-60`, `REQ-EXP-331..335`, `REQ-EXP-385..388`, `REQ-EXP-441..446`, `REQ-CORE-3030`)**:
   - Generator execution is strictly pull-based (`AGEN-78`, `REQ-EXP-385`): progress is controlled exclusively by explicit consumer `next(mut_view(gen))` calls (`AGEN-24`, `REQ-EXP-331`) without implicit buffering or backpressure queues (`AGEN-79..81`, `REQ-EXP-386..388`).
   - Generators never implicitly spawn OS threads (`AGEN-25`), never schedule async tasks (`AGEN-26`), never become stackful `Fiber` coroutines (`AGEN-134..135`), require no runtime scheduler, executor, or object headers (`AGEN-27`, `AGEN-136..139`), and require no mandatory heap allocation (`AGEN-28`, `AMIR-60`, `REQ-EXP-332..335`, `REQ-CORE-3030`).

### AXS-GEN-002 — Surface Syntax (`gen fn`, `Yield<T>` / `Generator<T>` / `impl Iterator<Item = T>`, `yield expr`, `return`) (`AGEN-20`, `AGEN-67..70`, `AGEN-84`, `AGEN-87`, `T562`)

1. **Generator Function Declarations (`tasks/0512 §3, §12–13, §101, §120–123`, `AGEN-20`, `AGEN-87`, `T562`)**:
   - A synchronous generator function is declared with `gen fn name<...>(params...) -> Yield<T>` (or with return type annotation `Generator<T>` / `impl Iterator<Item = T>`, where `Yield<T>` and `Generator<T>` denote the generator's yielded item contract `Iterator<Item = T>`). Generic parameters and `where` bounds obey ordinary Axiom generic rules (`AGEN-87`, `REQ-EXP-394`).
   - Direct or mutual unboxed recursion in a generator state machine that would construct an infinite-size state struct is rejected at compile time with `AX_GEN_RECURSIVE` unless explicit pointer/heap indirection (`Box<dyn Iterator<Item = T>>`) is used (`AGEN-84`, `REQ-EXP-391`).
2. **`yield` Expressions & Context Legality (`tasks/0512 §65–69, §120–122`, `AGEN-20`, `T562`)**:
   - Inside a `gen fn` body, `yield <expr>` evaluates `<expr>` of type `T` (unifying `type(expr)` with the declared `Item = T` type) and yields it to the caller (`0512 §120–122`).
   - `yield` binds to the innermost enclosing `gen fn` body and cannot cross a nested non-generator closure or ordinary `fn` boundary (`0512 §65–68`). Using `yield` outside a generator context is rejected with `AX_GEN_YIELD_OUTSIDE_GEN` (`0512 §67`, `T562`).
3. **`return` and `?` Inside Generators (`AGEN-67..70`, `REQ-EXP-374..377`, `T562`)**:
   - Inside a `gen fn`, a value-less `return` statement immediately transitions the generator to its terminal completed state and returns `Option.None` to the consumer (`AGEN-67..68`, `REQ-EXP-374..375`). Writing `return <expr>` with a value inside a `gen fn` is rejected with `AX_GEN_RETURN_VALUE`.
   - Generator errors are represented as ordinary yielded values such as `Yield<Result<T, E>>` (`AGEN-69`, `REQ-EXP-376`); the compiler never implicitly rewrites errors into yielded items (`AGEN-70`, `REQ-EXP-377`).

### AXS-GEN-003 — Lazy Creation (`MakeGenerator`) & Deterministic `yield` Evaluation Order (`AGEN-22..24`, `AGEN-40..42`, `AMIR-33`, `REQ-EXP-329`..`331`, `REQ-EXP-347`..`349`, `REQ-CORE-3003`, `T562`, `T563`)

1. **Lazy Construction (`AGEN-22..23`, `REQ-EXP-329..330`, `0512 §4–6, §134`)**:
   - Calling `let g = numbers(1_000_000)` evaluates the call arguments left-to-right (`SPEC-03 AXS-SEM-040`) and executes `MakeGenerator` to construct the initial state machine `{ state_tag = 0, ...params }` without executing any statement or side effect of the generator body (`AGEN-22..23`, `REQ-EXP-329..330`).
2. **Deterministic `yield expr` Suspension & Resume Sequence (`AGEN-40..42`, `AMIR-33`, `REQ-EXP-347..349`, `REQ-CORE-3003`, `0512 §7, §188`)**:
   - When `next(mut_view(g))` reaches `yield expr` at suspension point `YieldPointId(k)` (`k >= 1`), execution proceeds in exact deterministic order:
     1. Evaluate `expr` completely to value `v: T` following source evaluation order (`AGEN-40`, `AMIR-33`, `REQ-EXP-347`, `REQ-CORE-3003`);
     2. Drop any temporary values created within `expr` that do not survive the statement (`SPEC-12 AXS-DROP-001`);
     3. Persist all locals in `LiveAcrossYield(k)` into the generator state struct and write `self.state_tag = k` (`AGEN-41`, `REQ-EXP-348`);
     4. Return `Option.Some(v)` to the caller (`AGEN-42`, `REQ-EXP-349`).
   - On the subsequent `next(mut_view(g))` call, `SwitchInt(self.state_tag)` dispatches to `k`, restores live locals, and resumes execution immediately after `yield expr`.

### AXS-GEN-004 — Terminal Completion (`STATE_COMPLETE`), Panic Poisoning & Infinite Generators (`AGEN-43..44`, `AGEN-65..68`, `AGEN-82..83`, `REQ-EXP-350`..`351`, `REQ-EXP-372`..`375`, `REQ-EXP-389`..`390`, `T563`)

1. **Terminal Completion (`STATE_COMPLETE = u32.MAX`) (`AGEN-43..44`, `REQ-EXP-350..351`, `0512 §60–62`)**:
   - When a generator body falls off the end or executes `return`, all remaining in-scope locals and owned parameters are dropped in reverse declaration order, `self.state_tag` is set to `STATE_COMPLETE` (`u32.MAX`), and `next()` returns `Option.None`.
   - Completion is strictly terminal (`AGEN-43`, `REQ-EXP-350`): a completed generator never implicitly restarts (`AGEN-44`, `REQ-EXP-351`), and every subsequent call to `next(mut_view(g))` immediately returns `Option.None` without re-running body code or double-dropping state.
2. **Panic & Unwind Transitions (`AGEN-65..66`, `REQ-EXP-372..373`, `SPEC-54`, `0512 §82, §195`)**:
   - If a panic occurs while executing `next(mut_view(g))`, `self.state_tag` is set to `STATE_COMPLETE` (`u32.MAX`, poisoned/completed) before propagating the panic, and all live locals in the active state are cleaned up according to the active panic profile (`--panic abort|unwind`, `AGEN-65..66`). If the panic is caught via `std.panic.catch_unwind`, subsequent calls to `next(mut_view(g))` observe `STATE_COMPLETE` and return `Option.None`.
3. **Infinite Generators (`AGEN-82..83`, `REQ-EXP-389..390`, `0512 §74–76`)**:
   - Unbounded generator loops (`loop { yield n; n += 1 }`) are valid (`AGEN-82`, `REQ-EXP-389`). Dropping an infinite generator while suspended deterministically terminates the producer and runs per-state `Drop` cleanup on all owned resources (`AGEN-83`, `REQ-EXP-390`).

---

## 2. Ownership, Live-Across-Yield Analysis & Capability Rules (`AXS-GEN-010`..`014`)

### AXS-GEN-010 — Generator Ownership, Non-`Copy` Default, `Move` & Explicit `Clone` (`AGEN-29..34`, `AGEN-88..91`, `REQ-EXP-336`..`341`, `REQ-EXP-395`..`398`, `SPEC-10`, `T562`)

1. **Ordinary Storage & Single-Owner Semantics (`AGEN-29..34`, `REQ-EXP-336..341`, `SPEC-10 AXS-OWN-001..007`)**:
   - Generator storage and ownership obey standard Axiom storage and ownership semantics (`AGEN-29..30`, `REQ-EXP-336..337`). Every compiler-generated generator state machine is **non-`Copy` by default** (`AGEN-31`, `REQ-EXP-338`).
   - Assigning or passing a generator by value performs a semantic `Move` that transfers ownership of the entire suspended state machine and invalidates the source binding (`AGEN-32`, `REQ-EXP-339`, `0512 §47`). Duplicating a generator requires an explicit `.clone()` call when all captured state implements `Clone` (`AGEN-33`, `REQ-EXP-340`).
   - All captured parameters and locals in a generator state machine are verified by the ownership checker (`AGEN-34`, `REQ-EXP-341`).
2. **Owned Yield Transfer & Partial Consumption (`AGEN-88..91`, `REQ-EXP-395..398`, `0512 §124–128`)**:
   - Yielding an owned value transfers ownership to the consumer via ordinary `Move` semantics without implicit `Clone` (`AGEN-88..89`, `REQ-EXP-395..396`).
   - A partially consumed generator retains ownership of all remaining unyielded elements and live locals (`AGEN-90`, `REQ-EXP-397`), which are deterministically dropped when the generator itself is dropped (`AGEN-91`, `REQ-EXP-398`).

### AXS-GEN-011 — `YieldPointId`, `LiveAcrossYield` Analysis & State Minimization (`AGEN-35..38`, `AGEN-107..110`, `AMIR-55`, `REQ-EXP-342`..`345`, `REQ-CORE-3025`, `T562`, `T563`)

1. **Typed Suspension Identities (`AGEN-37..38`, `REQ-EXP-344..345`, `0512 §16–17, §172`)**:
   - Every `yield` expression in a generator body is assigned a stable, deterministic `YieldPointId` (`1..K`) corresponding to a valid resumable `GeneratorStateId` (`AGEN-37..38`, `REQ-EXP-344..345`).
2. **Minimal Live-State Capture (`AGEN-35..36`, `AGEN-107..110`, `AMIR-55`, `REQ-EXP-342..343`, `REQ-EXP-414..417`, `REQ-CORE-3025`, `0512 §18–21, §163`)**:
   - `compiler/own` computes `LiveAcrossYield(k)` for each `YieldPointId(k)`: the exact set of parameters and local places initialized before `yield k` and read, moved, or dropped on any control-flow path reachable after resuming from `yield k` (`AMIR-55`, `REQ-CORE-3025`).
   - Locals live across `yield` are promoted to fields of the generated state-machine struct (`AGEN-35`, `REQ-EXP-342`). Temporaries and locals whose lifetimes are strictly contained between two suspension points (dead before `yield`) are dropped before suspension and are NOT stored in the generator state struct (`AGEN-36`, `AGEN-108`, `REQ-EXP-343`, `REQ-EXP-415`).

### AXS-GEN-012 — Prohibition of Ephemeral Capabilities & Self-Referential Borrows Across `yield` (`AGEN-50..57`, `AMIR-35`, `AMIR-37`, `AMIR-47..48`, `REQ-EXP-326`, `REQ-EXP-357`..`364`, `REQ-CORE-3005`, `REQ-CORE-3007`, `REQ-CORE-3017`..`3018`, `SPEC-11`, `T562`)

1. **No Self-Referential State or Ephemeral Capabilities Across `yield` (`AGEN-50..57`, `REQ-EXP-326`, `REQ-EXP-357..364`, `SPEC-11 AXS-CAP-004..006`)**:
   - Axiom Core v1.0 does not use `Pin<T>` (`0512 §40–44`) and keeps generator state machines relocatable by value move (`AGEN-56..57`, `REQ-EXP-363..364`). Therefore, a generator state machine CANNOT implicitly become self-referential (`AGEN-54..55`, `REQ-EXP-361..362`).
   - **Self-Borrow Rejection (`AX_GEN_SELF_BORROW_ACROSS_YIELD`)**: Any capability (`view<T>`, `mut_view<T>`, `Str`, slice view, or composite containing a view) whose provenance is rooted in a generator local variable or by-value parameter captured inside the generator state machine MUST NOT remain live across a `yield` suspension point (`AGEN-50`, `AGEN-54`, `T562`). Attempting to hold a borrow of a generator local across `yield` is rejected at compile time with `AX_GEN_SELF_BORROW_ACROSS_YIELD`.
   - **Ephemeral Capability Rejection (`AX_GEN_VIEW_ACROSS_YIELD`)**: Under the fundamental invariant `UNKNOWN != SAFE` (`REQ-EXP-326`, `AGEN-53`, `REQ-EXP-360`), any ephemeral capability (`view<T>`, `mut_view<T>`), `@thread_local` view, or container element view subject to relocation (`AMIR-48`, `REQ-CORE-3018`) that cannot be statically proven valid across suspension — or that escapes out of `yield` from a generator-internal owner (`AGEN-51`, `REQ-EXP-358`) — is rejected with `AX_GEN_VIEW_ACROSS_YIELD` (`T562`).
   - Capabilities created and consumed entirely between two `yield` points without crossing a suspension boundary are valid (`AMIR-35`, `AMIR-37`, `AMIR-47`, `REQ-CORE-3005`, `REQ-CORE-3007`, `REQ-CORE-3017`).

### AXS-GEN-013 — Yielded Value Provenance, Reentrancy Prevention & `Send`/`Share` Derivation (`AGEN-52`, `AGEN-58..64`, `AGEN-85..86`, `REQ-EXP-359`, `REQ-EXP-365`..`371`, `REQ-EXP-392`..`393`, `SPEC-30`, `T562`)

1. **Provenance of Yielded Views (`AGEN-52`, `REQ-EXP-359`, `0512 §36–39`)**:
   - When a generator yields a view type (`Yield<view<T>>`, `Yield<Str>`, `Yield<view<[U]>>`), the yielded view's provenance MUST be rooted in an input view parameter passed into `gen fn` (or a `'static` item) that outlives the generator and remains non-conflicting for the consumer's observable lifetime (`AGEN-52`, `REQ-EXP-359`). Yielding a view rooted in a generator-owned local or buffer is rejected with `AX_GEN_VIEW_ACROSS_YIELD` (`AGEN-51`).
2. **Non-Reentrancy & Exclusive Resume (`AGEN-85..86`, `REQ-EXP-392..393`, `0512 §45, §111–114`)**:
   - `next(self: mut_view<Self>)` requires an exclusive `mut_view` capability on the generator state machine (`0512 §28, §45`). Consequently, a generator can never safely re-enter an active mutable `next()` call (`AGEN-85..86`, `REQ-EXP-392..393`).
3. **`Send`, `Share`, Synchronization & Effect Observability (`AGEN-58..64`, `REQ-EXP-365..371`, `SPEC-30`)**:
   - A generator type implements `Send` iff all captured parameters and all locals in the union of `LiveAcrossYield(k)` implement `Send` (`AGEN-58`, `REQ-EXP-365`).
   - `Send` and `Share` remain distinct (`AGEN-59`, `REQ-EXP-366`): because advancing a generator mutates `state_tag` and live fields, concurrent iteration across threads requires explicit synchronization such as `Arc<Mutex<G>>` (`AGEN-60..61`, `REQ-EXP-367..368`). Atomic, synchronization, and I/O effects inside a generator remain strictly observable in program order (`AGEN-62..64`, `REQ-EXP-369..371`).

### AXS-GEN-014 — Representation Opacity, FFI/ABI & Non-Serialization Boundaries (`AGEN-73..77`, `AMIR-58`, `REQ-EXP-380`..`384`, `REQ-CORE-3028`)

1. **Compiler-Controlled Layout & Explicit FFI/Checkpoint Contracts (`AGEN-73..77`, `AMIR-58`, `REQ-EXP-380..384`, `REQ-CORE-3028`)**:
   - Generator state-machine layout is compiler-controlled (`AGEN-73`), is not a stable C/FFI ABI by default (`AGEN-74`), and requires explicit ABI polling adapters across explicit `extern` FFI boundaries (`AGEN-75`, `AMIR-58`, `REQ-EXP-380..382`, `REQ-CORE-3028`).
   - Compiler-generated generator state is not implicitly serializable (`AGEN-76`); persistent resumable workflows require explicit user-defined checkpoint structs (`AGEN-77`, `REQ-EXP-383..384`).

---

## 3. HIR → MIR Semantic Boundary, State-Machine Lowering & Per-State `Drop` Cleanup (`AXS-GEN-020`..`024`)

### AXS-GEN-020 — Authoritative HIR → MIR Semantic Boundary & Structural Invariants (`AMIR-20..37`, `REQ-CORE-2989`..`3007`, `SPEC-03`)

1. **No Semantic Re-Inference in MIR (`tasks/0539 §1, §89 AMIR-28..33`, `REQ-CORE-2989`, `REQ-CORE-2998..3003`)**:
   - MIR lowering consumes validated Typed HIR (`THIR`) and NEVER re-guesses or re-infers semantics already determined by HIR (`0539 §1`, `REQ-CORE-2989`). Specifically, MIR does not perform overload resolution (`AMIR-28`, `REQ-CORE-2998`), does not perform generic type inference (`AMIR-29`, `REQ-CORE-2999`), does not perform name resolution (`AMIR-30`, `REQ-CORE-3000`), and never invents implicit coercions (`AMIR-31`, `REQ-CORE-3001`); all semantic coercions are explicit before or within validated lowering (`AMIR-32`, `REQ-CORE-3002`), and MIR strictly preserves source left-to-right evaluation order (`AMIR-33`, `REQ-CORE-3003`).
2. **Core MIR Structural & Place/Operand Invariants (`tasks/0539 §89 AMIR-20..27, AMIR-34..37`, `REQ-CORE-2990..2997`, `REQ-CORE-3004..3007`)**:
   - Every production MIR function (including synthesized generator `next` and `drop` bodies) has exactly one entry block `bb0` (`AMIR-20`, `REQ-CORE-2990`), every basic block has exactly one terminator (`AMIR-21`, `REQ-CORE-2991`), and every block reference resolves to a valid `BasicBlockId` (`AMIR-22`, `REQ-CORE-2992`).
   - MIR uses strongly typed compiler IDs (`AMIR-23`, `REQ-CORE-2993`), represents places via semantic `LocalId`s and `FieldId`s (`AMIR-24`, `REQ-CORE-2994`), and explicitly distinguishes `Operand.Copy` from `Operand.Move` (`AMIR-25`, `REQ-CORE-2995`) while keeping semantic `Copy` and `Move` independent of physical machine memory copies or moves (`AMIR-26..27`, `REQ-CORE-2996..2997`).
   - MIR preserves all semantic ownership operations (`AMIR-34`, `REQ-CORE-3004`) and capability creation/destruction markers (`AMIR-35`, `REQ-CORE-3005`), carrying complete information for authoritative ownership (`AMIR-36`, `REQ-CORE-3006`) and capability (`AMIR-37`, `REQ-CORE-3007`) verification.

### AXS-GEN-021 — State-Machine Struct Synthesis & `SwitchInt` Resume Lowering (`compiler/mir/gen_lower.ax`) (`AGEN-21`, `AGEN-37..39`, `AGEN-111..113`, `T563`)

1. **Synthesized State-Machine ADT (`compiler/mir/gen_lower.ax`, `AGEN-21`, `AGEN-37..38`, `T563`)**:
   - Before MIR verification and optimization, `compiler/mir/gen_lower.ax` lowers each `gen fn` body containing `MirTerminator.Yield { value, resume_bb, drop_bb, yield_id }` into a synthesized struct `GenState_<fn>` containing:
     - `state_tag: u32`: `0` = unstarted (`STATE_INITIAL`), `1..K` = suspended at `YieldPointId(k)`, `u32.MAX` = completed/poisoned (`STATE_COMPLETE`);
     - Captured function parameters and the union of `LiveAcrossYield(k)` locals (`AXS-GEN-011`).
2. **Ordinary MIR Control-Flow Dispatch (`AGEN-39`, `AGEN-111..113`, `REQ-EXP-346`, `REQ-EXP-418..420`, `T563`)**:
   - The generated `next(self: mut_view<GenState_<fn>>) -> Option<T>` method lowers to ordinary MIR basic blocks (`AGEN-111`, `REQ-EXP-418`) without requiring special backend machinery (`AGEN-112`, `REQ-EXP-419`):
     - Entry block `bb0` executes `SwitchInt(self.state_tag)`: `0 => bb_start`, `k => bb_resume_k` (`k in 1..=K`), `otherwise => bb_complete` (`return Option.None`).
     - At `YieldPointId(k)`, live locals are written to `self`, `self.state_tag = k` is stored, and the block returns `Option.Some(yielded_val)`.
     - Invalid state transitions or unreachable resume entries are rejected by semantic/MIR verification (`AGEN-39`, `REQ-EXP-346`). The MIR oracle (`compiler/interp`, `--interp`) executes the lowered generator state machine directly and deterministically (`AGEN-113`, `REQ-EXP-420`).

### AXS-GEN-022 — Deterministic Per-State `Drop` Glue & Cleanup Graph Verification (`AGEN-45..49`, `AGEN-66`, `AGEN-90..91`, `AMIR-38..46`, `REQ-CORE-3008`..`3016`, `SPEC-12`, `T563`)

1. **Per-State `Drop` Dispatch (`AGEN-45..49`, `REQ-EXP-352..356`, `SPEC-12 AXS-DROP-001..006`, `T563`)**:
   - Dropping a generator value in any state runs its synthesized `Drop.drop(self: mut_view<GenState_<fn>>)` glue (`AGEN-45`, `AGEN-49`, `REQ-EXP-352`, `REQ-EXP-356`):
     - If `self.state_tag == 0` (`STATE_INITIAL`), only captured owned parameters are dropped in reverse parameter declaration order;
     - If `self.state_tag == k` (`1 <= k <= K`), only the owned places live and initialized at `YieldPointId(k)` are dropped in exact reverse declaration order (`AGEN-46..47`, `REQ-EXP-353..354`);
     - If `self.state_tag == u32.MAX` (`STATE_COMPLETE`), all locals have already been dropped or moved out, so `drop` is a no-op;
     - After running state-specific cleanup, `self.state_tag` is set to `u32.MAX` so moved or completed generator state is never dropped twice (`AGEN-48`, `REQ-EXP-355`).
2. **MIR Cleanup Graph Invariants (`AMIR-38..46`, `REQ-CORE-3008..3016`, `T563`)**:
   - MIR retains complete facts for `Drop` verification (`AMIR-38`, `REQ-CORE-3008`): every reachable control-flow path has valid cleanup (`AMIR-39`, `REQ-CORE-3009`), and all `return` (`AMIR-40`), `break` (`AMIR-41`), `continue` (`AMIR-42`), and panic/unwind (`AMIR-43`) paths pass through their required cleanup blocks (`REQ-CORE-3010..3013`).
   - Moved values are never implicitly dropped (`AMIR-44`, `REQ-CORE-3014`), partially moved aggregates are tracked at place granularity (`AMIR-45`, `REQ-CORE-3015`), and custom-`Drop` partial-move prohibitions (`SPEC-10 AXS-OWN-005`) are strictly preserved (`AMIR-46`, `REQ-CORE-3016`).

### AXS-GEN-023 — Preservation of `unsafe`, Provenance, Atomic/Volatile, Sync, Closure, GPU & Comptime Contracts in MIR (`AMIR-49..60`, `AGEN-127..133`, `REQ-CORE-3019`..`3030`, `T564`, `T565`)

1. **Cross-Domain MIR Preservation (`tasks/0539 §89 AMIR-49..60`, `REQ-CORE-3019..3030`)**:
   - Across all generator and control-flow lowering, MIR preserves explicit `unsafe` boundaries (`AMIR-49`, `REQ-CORE-3019`), pointer/view provenance contracts (`AMIR-50`, `REQ-CORE-3020`), distinct `atomic` (`AMIR-51`, `REQ-CORE-3021`) and `volatile` (`AMIR-52`, `REQ-CORE-3022`) operations, synchronization barriers (`AMIR-53`, `REQ-CORE-3023`), explicit async suspension points (`AMIR-54`, `REQ-CORE-3024`), identifiable live-across-suspension sets (`AMIR-55`, `REQ-CORE-3025`), closure capture modes (`AMIR-56`, `REQ-CORE-3026`), explicit GPU execution/storage domains (`AMIR-57`, `REQ-CORE-3027`), explicit FFI boundaries (`AMIR-58`, `REQ-CORE-3028`), separation of comptime vs runtime execution (`AMIR-59`, `REQ-CORE-3029`), and zero mandatory heap allocation for high-level constructs (`AMIR-60`, `REQ-CORE-3030`).
2. **Comptime Generators, Async Composition & GPU Restriction (`AGEN-127..133`, `REQ-EXP-434..440`, `T562`, `T564`)**:
   - Generators may be evaluated at `comptime` under `SPEC-60` capability sandboxing and step budgets without causing runtime allocation (`AGEN-127..128`, `REQ-EXP-434..435`).
   - Async generators (`AsyncIterator`) compose `SPEC-33` async suspension with `yield` semantics without introducing a third runtime primitive (`AGEN-130..133`, `REQ-EXP-437..440`). General generator suspension inside a `@gpu` kernel is forbidden in v1.0 and rejected with `AX_GEN_GPU_FORBIDDEN` (`AGEN-129`, `REQ-EXP-436`).

### AXS-GEN-024 — `for-in` Integration, Lazy `std.iter` Combinators & Optimizer Fusion Contract (`AGEN-92..106`, `AGEN-114..126`, `AGEN-140`, `T564`, `T565`)

1. **`for-in` Loop & Lazy `std.iter` Pipeline Integration (`AGEN-92..94`, `REQ-EXP-399..401`, `T564`)**:
   - `for pat in gen_expr { body }` lowers via the standard `IntoIterator` / `Iterator.next(mut_view(it))` protocol (`AGEN-71`). Exiting the loop via normal exhaustion, `break`, `return`, `?`, or panic deterministically runs `Drop` on the generator state machine (`AXS-GEN-022`).
   - `std.iter` combinators (`map`, `filter`, `take`, `skip`, `zip`, `chain`, `enumerate`, `flatten`, `fold`, `collect`) compose lazily over generators without intermediate collection materialization (`AGEN-92..93`, `REQ-EXP-399..400`).
2. **Optimizer Fusion & State-Elimination Legality (`AGEN-94..106`, `AGEN-114..126`, `AGEN-140`, `REQ-EXP-401..413`, `REQ-EXP-421..433`, `REQ-EXP-447`)**:
   - Generator fusion, inlining, scalarization (`SROA`), dead state-field elimination, and complete state-machine elimination (`AGEN-94..96`, `AGEN-107..110`, `AGEN-140`, `SPEC-72 AXS-LOOP-016`) are legal only when observable yielded order, cleanup, panics, external I/O, synchronization, ownership, capability validity, and `Send`/`Share` semantics are preserved (`AGEN-97..106`, `AGEN-120..122`). Analysis is incremental and deterministic, and diagnostics expose yield points and live state (`AGEN-123..126`).

---

## 4. Diagnostic Taxonomy, Canonical Examples & Conformance Matrix (`AXS-GEN-050`..`052`)

### AXS-GEN-050 — Generator Diagnostic Codes (`spec/diagnostics.md`, `T562`–`T563`)

Self-hosted `axiomc` (`compiler/diag/code.ax`) defines the `GEN` (`AX_GEN_*`) diagnostic codes:

| Code | Sev | Task | Condition |
|---|---|---|---|
| `AX_GEN_YIELD_OUTSIDE_GEN` | E | T562 | `yield` expression used outside a `gen fn` body (`AXS-GEN-002`, `AGEN-20`) |
| `AX_GEN_SELF_BORROW_ACROSS_YIELD` | E | T562 | capability (`view<T>`, `mut_view<T>`, `Str`, slice view) borrowing a generator local or captured parameter is held live across a `yield` suspension point (`AXS-GEN-012`, `AGEN-50`, `AGEN-54`) |
| `AX_GEN_VIEW_ACROSS_YIELD` | E | T562 | ephemeral capability (`view<T>`, `mut_view<T>`), `@thread_local` view, or view into a generator-owned local escapes through `yield` or is held across `yield` without proven outer provenance (`AXS-GEN-012..013`, `AGEN-51..53`) |
| `AX_GEN_RETURN_VALUE` | E | T562 | `return <expr>` with a value used inside a `gen fn` body instead of bare `return` (`AXS-GEN-002`, `AGEN-67..68`) |
| `AX_GEN_RECURSIVE` | E | T562 | direct or mutual recursion among `gen fn` bodies creates an unboxed infinite-size generator state machine (`AXS-GEN-002`, `AGEN-84`) |
| `AX_GEN_GPU_FORBIDDEN` | E | T562 | `gen fn` or `yield` used inside a `@gpu` kernel execution domain (`AXS-GEN-023`, `AGEN-129`) |

### AXS-GEN-051 — Canonical Positive & Negative Examples (`axiom-syntax`: `=` and `.` only)

```axiom
module demo.generators

gen fn range_step(start: i32, stop: i32, step: i32) -> Yield<i32> {
    let mut cur = start
    while cur < stop {
        yield cur
        cur += step
    }
}

pub fn sum_first_three() -> i32 {
    let mut total = 0
    for x in range_step(10, 50, 5).take(3) {
        total += x
    }
    return total
}

// Negative examples (rejected at compile time):
// fn not_a_gen() -> i32 {
//     yield 1 //~ ERROR AX_GEN_YIELD_OUTSIDE_GEN
//     return 0
// }
//
// gen fn bad_self_borrow() -> Yield<i32> {
//     let x = 42
//     let v: view<i32> = view(x)
//     yield 1 //~ ERROR AX_GEN_SELF_BORROW_ACROSS_YIELD
//     yield *v
// }
//
// gen fn bad_escape_view() -> Yield<view<i32>> {
//     let local_val = 99
//     yield view(local_val) //~ ERROR AX_GEN_VIEW_ACROSS_YIELD
// }
```

### AXS-GEN-052 — E14.3 Conformance Verification Matrix (`T562`–`T565`)

| Test ID | Verification Focus | Expected Outcome | Task |
|---|---|---|---|
| `GEN-T01` | `gen fn`, `yield`, lazy creation & live-across-yield capability/ownership checks | Rejects `AX_GEN_YIELD_OUTSIDE_GEN`, `AX_GEN_SELF_BORROW_ACROSS_YIELD`, `AX_GEN_VIEW_ACROSS_YIELD` | T562, T565 |
| `GEN-T02` | MIR state-machine synthesis, `SwitchInt` dispatch & terminal `STATE_COMPLETE` (`None`) | Synthesizes minimal state struct; subsequent `next()` after return/panic returns `Option.None` | T563, T565 |
| `GEN-T03` | Per-state `Drop` cleanup on early `break` / drop while suspended vs full consumption | Drops only live initialized locals at active `YieldPointId` in reverse declaration order; zero double-drop | T563, T565 |
| `GEN-T04` | `for x in gen(...)`, nested `yield` delegation, `std.iter` lazy adapters & comptime generators | Identical results across `--interp` and native x86-64 (`-O0`/`-O1`, `0 WEAK-NATIVE`) with zero heap allocation | T564, T565 |

---

## 5. Sources & Traceability

- **Corpus Specifications & Tasks**: `tasks/0512 (§1–203, AGEN-20..140)`; `tasks/0539 (§1–89, AMIR-20..90)`.
- **Canonical Specs & ADRs**: `ADR-0007` (canonical `=` and `.` syntax); `ADR-0011` (diagnostic taxonomy); `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-33-async.md`; `spec/SPEC-54-panic-unwinding.md`; `spec/SPEC-60-comptime-2-0.md`.
- **Requirements Covered**: `REQ-CORE-2989`..`3030`, `REQ-EXP-325`..`447`.
