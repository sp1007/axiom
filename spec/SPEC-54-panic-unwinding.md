# SPEC-54 — Canonical Panic Strategy (`--panic abort|unwind`), Deterministic Drop Unwinding, `@no_panic` Verification & FFI No-Unwind Barrier Specification

Status: draft (T521, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0107 (§1–64, AFERR-11..37)`; `specs/0119 (§247–248, §259, AFFI-22)`; `specs/0131 (§66, §88, AFN-53)`; `specs/0138 (§44–46, §100, AFFI-41..42)`; `specs/0188 (LVII §1–58, AUNW-20..38, AEPI-20..23)`; `specs/0229 (ERROR/PANIC/UNWIND-001 §1–84, AERR-20..65)`; `tasks/0351 (BOOTSTRAP-092 §1–63, AFAIL-20..77)`; `tasks/0413 (§47, §70, AFFI-41, AFFI-60..62)`; `tasks/0445 (§186.62–64, §186.161, AFFI-60..62, AFFI-83)`; `tasks/0478 (§24, §40, ASEM-49)`; `tasks/0517 (§90, §192)`; `tasks/0585 (§1, §12)`; `tasks/0700 (BOOTSTRAP-440 §440.21–44, §440.101–113, §441.28–29, §441.63–64, §441.140–141)`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`.
Covers: `REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-ABI-096`, `REQ-FFI-125`, `REQ-ABI-105` (and specifies the E13.5 contract for `T522`–`T524`: `REQ-FFI-094`, `REQ-FFI-127`).
Consumers: `compiler/driver/`, `compiler/hir/`, `compiler/sema/`, `compiler/mir/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/link/`, `std/core/panic.ax`, `std/panic/`, `T522`–`T524`.

## Tóm tắt

Tài liệu `SPEC-54` chuẩn hóa chiến lược xử lý `panic` theo hồ sơ biên dịch (`--panic abort|unwind`), cơ chế dọn dẹp tài nguyên tất định (`Drop`) khi tháo chồng (`stack unwinding`), giao diện thu hồi tại biên tác vụ/luồng (`std.panic.catch_unwind`), kiểm chứng tĩnh đồ thị lời gọi `@no_panic`, bảng tháo chồng Windows x64 SEH (`.pdata`/`.xdata`), và rào cản cấm tháo chồng qua ranh giới ngoại ngữ `extern "C"` (`FFI no-unwind barrier`) cho phân hệ `E13.5` (Phase `P13`):
- **Phân tách bốn cơ chế thất bại độc lập (`0229 AERR-20..32`, `tasks/0351 AFAIL-20..34`, `SPEC-03 AXS-SEM-070..073`)**: Lỗi khả hồi (`Result<T, E>`, `Option<T>`, toán tử `?`) là luồng điều khiển giá trị bình thường không dùng bảng ngoại lệ; hủy tác vụ (`Cancellation`) là tín hiệu hợp tác; `panic` là lỗi vi phạm bất biến chương trình; và `trap`/`abort` là dừng khẩn cấp mức máy/tiến trình. Axiom Core không có hệ thống ngoại lệ kiểu C++ (`try`/`catch`/`throw`).
- **Hai chiến lược `--panic abort` và `--panic unwind` gắn với hồ sơ thực thi (`0229 §16–18`, `tasks/0700 §440.35–36`, `SPEC-52 AXS-FRE-020..022`, `T522`–`T523`)**: Hồ sơ `freestanding` và `kernel` mặc định dùng `--panic abort` (không sinh landing pad, không kéo runtime tháo chồng) và từ chối `--panic unwind` tại thời điểm biên dịch (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`). Hồ sơ `hosted` và `system` hỗ trợ cả `--panic abort` lẫn `--panic unwind`; dưới `--panic unwind`, tiến trình tháo chồng qua từng khung hàm, chạy `Drop` tất định và cho phép chặn/thu hồi tại ranh giới tường minh `std.panic.catch_unwind`.
- **Dọn dẹp `Drop` tất định khi tháo chồng và quy tắc `double-panic` abort tức thì (`SPEC-12 AXS-DROP-001..006`, `0229 §19–21, §58–64`, `tasks/0351 §11–12`, `T522`–`T523`)**: Luồng tháo chồng dùng chung đồ thị `CleanupGraph` của MIR Drop Elaboration với luồng trả về bình thường (`return`, `?`, `break`), gọi hàm hủy của các biến cục bộ đang sống và đã khởi tạo theo **đúng thứ tự ngược với khai báo** (`reverse declaration order`) từ khung hàm trong ra khung hàm ngoài. Nếu một hàm hủy `Drop.drop` tiếp tục gây `panic` trong khi hệ thống đang tháo chồng một `panic` trước đó (`double panic`), tiến trình **phải abort ngay lập tức** (mã thoát `101`) để ngăn tháo chồng lồng nhau bất định.
- **Rào cản FFI cấm tháo chồng mặc định (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-FFI-093`, `REQ-FFI-094`, `REQ-ABI-096`, `REQ-ABI-105`, `REQ-FFI-125`, `REQ-FFI-127`) và kiểm chứng `@no_panic` (`T522`–`T524`)**: Một `panic` của Axiom **tuyệt đối không bao giờ** được tháo chồng vượt qua biên `extern "C"` (hoặc ABI ngoại lai khác) theo mặc định; khi luồng tháo chồng chạm tới khung hàm `extern "C"`, chương trình chạy xong các `Drop` nội bộ của khung Axiom rồi **abort tất định ngay tại biên** (hoặc chuyển đổi tường minh thành mã lỗi thông qua adapter `catch_unwind` / `@ffi_panic_adapter`). Ngược lại, ngoại lệ ngoại lai (C++ exception, SEH ngoại lai) không được tự động tháo chồng xuyên qua khung hàm Axiom (`REQ-FFI-093`, `REQ-ABI-096`). Mọi hàm `extern "C"` chưa gắn hợp đồng hiệu ứng tường minh đều được mô hình hóa bảo thủ là có thể đọc, ghi, làm thoát con trỏ, gây `panic`, và đồng bộ hóa (`REQ-FFI-125`). Thuộc tính `@no_panic` kiểm chứng tĩnh trên đồ thị lời gọi rằng hàm không thể gây `panic` trực tiếp hay bắc cầu (`AX_PANIC_FORBIDDEN_IN_NO_PANIC`).

---

## 1. Failure Taxonomy, Panic Strategies (`--panic abort|unwind`) & Profile Integration (`AXS-PAN-001`..`005`)

### AXS-PAN-001 — Four-Way Failure Taxonomy & Absence of General Exceptions (`0229 §1–15, §50–53, AERR-20..32, AERR-62`, `tasks/0351 §1–10, §55–59, AFAIL-20..34, AFAIL-69`, `SPEC-03 AXS-SEM-070..073`)

1. **Orthogonal Failure Categories**:
   - **Recoverable Failure (`Result<T, E>`) & Absence (`Option<T>`)**: Ordinary algebraic data types lowered to standard branches and registers without exception objects, heap allocation, or stack unwinding (`AERR-20..25`, `AFAIL-20..27`). The `?` operator desugars purely to an explicit `match` and early `return` that runs deterministic `Drop` cleanup (`AERR-23..25`).
   - **Cooperative Cancellation (`CancellationToken`)**: Explicit control-flow state observed at polling/cancellation points (`AERR-43..44`, `AFAIL-41..46`, `SPEC-34 AXS-EXEC-021`). Cancellation is never modeled as a forced asynchronous panic.
   - **Program Invariant Failure (`panic`)**: Triggered by `panic(msg)`, `assert(cond)`, `unreachable()`, checked integer overflow (`+`, `-`, `*`, `MIN / -1`), division/remainder by zero (`/`, `%`), out-of-range bit shift (`<<`, `>>`), out-of-bounds array/slice indexing (`a[i]`), or invalid `u32 as char` conversion (`SPEC-03 AXS-SEM-070..073`, `AFAIL-28..29, AFAIL-52..54`). `panic` has return type `never` (`AXS-SEM-015`).
   - **Machine / Process Terminal Failure (`trap` / `abort`)**: Immediate execution termination (`std.process.abort()`, hardware illegal-instruction trap `UD2`, unrecoverable double-panic abort, or FFI boundary abort) that halts the execution domain without running further user-level stack unwinding (`AFAIL-60..62`).
2. **No General `try`/`catch`/`throw` in Core (`AERR-62`, `AFAIL-57..59`)**:
   - Axiom Core defines no general exception-matching syntax (`try`, `catch`, `throw`, `finally`, or `throws` clauses). Stack unwinding under `--panic unwind` is strictly a resource-cleanup and boundary-containment mechanism, never an alternate recoverable error-propagation channel (`AFAIL-34`).

### AXS-PAN-002 — Compilation Panic Strategy (`--panic abort|unwind`) & Profile Matrix (`0229 §16–18, §67–71, AERR-28..30, AERR-57..58`, `tasks/0700 §440.35–36, §441.28–29`, `SPEC-52 AXS-FRE-002, AXS-FRE-020..022`, `T522`)

1. **CLI & Manifest Selection (`AX_DRIVER_INVALID_PANIC_STRATEGY`)**:
   - The compilation session selects a `PanicStrategy` (`Abort` or `Unwind`) via `--panic abort` or `--panic unwind` on the command line, or `panic = "abort" | "unwind"` under `[package]` / `[profile.*]` in `axiom.toml`.
   - Any value outside `{"abort", "unwind"}` is rejected by `compiler/driver/` with `AX_DRIVER_INVALID_PANIC_STRATEGY` (exit code `2`).
2. **Per-Profile Defaults & Legality (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`)**:

| Compilation Profile (`--profile`) | Default `--panic` Strategy | `--panic abort` | `--panic unwind` | Runtime Capability Required for `unwind` |
|---|---|---|---|---|
| `hosted` (default) | `abort` (bootstrap / CLI baseline; `unwind` when requested or when `catch_unwind` test/service profile is active) | Allowed (`RuntimeCap.Panic`) | Allowed (`RuntimeCap.Panic` + `RuntimeCap.Unwind`) | `RuntimeCap.Unwind` (`SPEC-52 AXS-FRE-020`) |
| `system` | `abort` | Allowed | Allowed (when target unwind tables are enabled) | `RuntimeCap.Unwind` |
| `freestanding` | `abort` | Allowed (`@panic_handler` or `UD2` trap) | **Forbidden** (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `data.capability = "unwind"`) | Forbidden (`SPEC-52 AXS-FRE-022`) |
| `kernel` | `abort` | Allowed (`@panic_handler` or kernel halt) | **Forbidden** (`AX_DRIVER_PROFILE_FORBIDDEN_CAP`, `data.capability = "unwind"`) | Forbidden (`SPEC-52 AXS-FRE-022`) |

3. **Dead Unwind Runtime Elimination (`AERR-30, AERR-57..58`, `tasks/0700 §440.107, §441.21`)**:
   - When `--panic abort` is active (or when `RuntimeCap.Unwind` is unreachable in the `RuntimeCapabilityGraph`), the compiler emits **zero** MIR cleanup landing pads and links **zero** stack-unwinder runtime support (`AERR-30, AERR-58`).

### AXS-PAN-003 — `--panic abort` Semantics (`0229 §16–17, §70, §77–78, AERR-28`, `tasks/0700 §440.35`, `SPEC-03 AXS-SEM-071`, `T522`, `T523`)

Under `--panic abort`:
1. When any explicit or compiler-inserted panic is triggered, **no stack unwinding occurs** and **no pending `Drop` destructors** on the call stack are executed (`SPEC-03 AXS-SEM-071`, `AFAIL-62`).
2. In `hosted` and `system` profiles, the runtime writes `panic: <message>\n` (UTF-8) to `stderr` and terminates the process immediately with exit code **`101`**.
3. In `freestanding` and `kernel` profiles, control transfers directly to the registered `@panic_handler` function (`fn(view<PanicInfo>) -> never`, `SPEC-52 AXS-FRE-011`) or, if none is defined, executes the target architectural trap (`UD2` on x86-64 / exit code `101` in `--interp`).

### AXS-PAN-004 — `--panic unwind` Semantics, Thread/Task Containment & `std.panic.catch_unwind` (`0229 §18–19, §43, §51–53, §71–72, AERR-29, AERR-41..42, AERR-61`, `tasks/0351 §10, §33, AFAIL-31..32, AFAIL-48..49`, `tasks/0700 §440.36, §440.111`, `T522`, `T523`)

Under `--panic unwind`:
1. **Unwinding & Uncaught Termination Parity**:
   - When a panic occurs, the runtime records the `PanicError` payload (`AXS-PAN-005`) and unwinds the call stack frame by frame from the panicking frame toward the entry root.
   - In every frame traversed, all live initialized local variables are dropped in reverse declaration order (`AXS-PAN-010`).
   - If the unwind reaches the root `fn main` without being intercepted by `std.panic.catch_unwind`, after `main`'s live locals are dropped, the runtime writes `panic: <message>\n` to `stderr` and exits the process with exit code **`101`** — preserving exact exit-code and `stderr` parity with `--panic abort` for uncaught panics (`SPEC-03 AXS-SEM-071`).
2. **Explicit Recovery Boundary (`std.panic.catch_unwind` and `std.panic.resume_unwind`)**:
   ```axiom
   pub struct PanicError {
       pub message: Str,
       pub file: Str,
       pub line: u32,
       pub col: u32,
   }

   pub fn catch_unwind<T>(f: fn() -> T) -> Result<T, PanicError>
   pub fn resume_unwind(err: PanicError) -> never
   ```
   - `std.panic.catch_unwind(f)` invokes `f()` inside an explicit unwind-catch frame (`MirTerminator.CatchUnwind` / native personality catch handler):
     - If `f()` returns normally with value `v`, `catch_unwind` returns `Result.Ok(v)`.
     - If `f()` panics (directly or transitively) under `--panic unwind`, the unwinder runs all `Drop` destructors in frames inside `f()` up to the `catch_unwind` boundary, stops unwinding at the boundary, suppresses process termination, and returns `Result.Err(err)` containing the captured `PanicError` (`0229 §52`, `T522`, `T523`).
     - Under `--panic abort`, `catch_unwind(f)` executes `f()` directly; any panic inside `f()` aborts immediately per `AXS-PAN-003` (`0229 §52`).
   - `std.panic.resume_unwind(err)` re-raises `err` into the unwinder without invoking the panic formatting hook a second time.
3. **OS Thread & Async Task Boundaries (`0229 §43, §72, AERR-41..42`, `tasks/0351 §33–34, AFAIL-48..49`, `SPEC-32`, `SPEC-34`)**:
   - A spawned OS thread (`std.thread.spawn`) or multi-thread executor task (`Executor.spawn`) wraps its root entry closure in an implicit `catch_unwind` boundary under `--panic unwind`, converting an uncaught panic on that worker thread into `JoinError.Panicked(err)` observed when the parent calls `join_handle.join()` without tearing down unrelated threads (`AFAIL-48..49`).

### AXS-PAN-005 — Zero-Heap `PanicInfo` & `PanicError` Payload Contract (`0107 §60–61, AFERR-37`, `0229 §45, AERR-31..32`, `tasks/0351 §9, AFAIL-30`, `tasks/0700 §440.101–105`, `SPEC-52 AXS-FRE-011`)

1. **Zero Mandatory Heap Allocation (`AFERR-37`, `AERR-31`, `AFAIL-30`)**:
   - Raising or unwinding a panic MUST NOT require a heap allocation (`RuntimeCap.HeapAlloc`). Both `PanicInfo` (`SPEC-52 AXS-FRE-011`) and `PanicError` (`AXS-PAN-004`) carry non-owning `Str` slices (`message: Str`, `file: Str`) and 32-bit source coordinates (`line: u32`, `col: u32`) stored in static thread-local / per-context unwind state or passed in registers.
   - Standard built-in panic messages (`"arithmetic overflow"`, `"division by zero"`, `"shift amount out of range"`, `"index out of bounds"`, `"invalid char value"`, `"assertion failed"`, `"entered unreachable code"`, `SPEC-03 AXS-SEM-070`) and string-literal `panic("...")` arguments reside in `.rdata` static storage with zero dynamic allocation.

---

## 2. Deterministic Drop Cleanup Across Unwinding, `@no_panic` Verification & Native SEH Unwind Tables (`AXS-PAN-010`..`014`)

### AXS-PAN-010 — Unified MIR `CleanupGraph` & Reverse-Declaration `Drop` Order During Unwinding (`0229 §19–20, §58–63, AERR-33, AERR-47..52, AERR-64`, `tasks/0351 §11, §49–52, AFAIL-32, AFAIL-37..40, AFAIL-70..73`, `tasks/0700 §440.37–38`, `SPEC-12 AXS-DROP-001..006`, `T522`, `T523`)

1. **Single Cleanup Engine Across Normal, Error (`?`), and Unwind Paths (`0229 §20, §58, AERR-47..48`, `AFAIL-70..73`)**:
   - The compiler constructs a single `CleanupGraph` during MIR Drop Elaboration (`compiler/mir/`) from ownership and initialization dataflow facts. Normal scope exit (`return`, `break`, `continue`), early `Result`/`Option` propagation (`?`), and `--panic unwind` stack unwinding all query and execute this identical cleanup schedule.
2. **Exact Reverse-Declaration Order Within Scopes & Inner-to-Outer Frame Order (`SPEC-12 AXS-DROP-002..005`, `AERR-49`)**:
   - When a panic unwinds a function activation frame $F$:
     1. Within each active lexical block of $F$ (from innermost active block to outermost parameter scope of $F$), every local variable $x$ whose type requires `Drop` and whose initialization state at the unwind point is `Init` (neither `UNINIT` nor `MOVED`, checked via runtime MIR drop flags when initialization or move is branch-dependent per `AXS-DROP-003`) is dropped in **strict reverse order of declaration**.
     2. Within a composite `struct` value dropped via `drop_in_place<S>(p)`, first the custom `impl Drop for S` method runs (if defined), and then the struct's fields are dropped in **forward declaration order** (`SPEC-12 AXS-DROP-002, AXS-DROP-005`). For an array `[N]T` or slice `[T]`, elements are dropped in index order `0..N`.
     3. Once all live locals of callee frame $F_{\text{callee}}$ have been dropped, unwinding resumes in caller frame $F_{\text{caller}}$ at the call site's cleanup landing pad, dropping $F_{\text{caller}}$'s live locals in reverse declaration order before continuing up the call stack.
3. **Partial-Move & Capability Liveness Respect (`0229 §63, AERR-52`, `tasks/0351 §50–52, AFAIL-38..39, AFAIL-72`)**:
   - Moved locals (`MOVED`) and moved fields of structs without custom `Drop` are never dropped a second time during unwinding (`AFAIL-38..39`).
   - All non-owning capabilities (`view<T>`, `mut_view<T>`) in the frame become dead before their backing owner local is dropped on the unwind path (`tasks/0351 §52, AFAIL-72`).

### AXS-PAN-011 — Double-Panic Immediate Abort Invariant (`0229 §21, §64, AERR-34, AERR-37`, `tasks/0351 §12, AFAIL-33, AFAIL-35`, `tasks/0700 §440.39`, `SPEC-12 AXS-DROP-006`, `T522`, `T523`)

1. **Destructors Are Non-Fallible (`0229 §21–24, AERR-34..36`, `AFAIL-35..36`)**:
   - `Drop.drop(self: mut_view<Self>)` returns `()` and cannot return `Result`. Resource types requiring fallible teardown expose an explicit `close(self) -> Result<(), E>` method that transitions internal state to closed before `Drop` runs (`0229 §22–24`).
2. **Panic During Active Unwind (`Double Panic`) MUST Immediately Abort (`SPEC-12 AXS-DROP-006`, `AERR-37`, `AFAIL-33`)**:
   - The runtime tracks per-thread/per-context unwind state (`unwinding_count: u32`).
   - If a destructor `Drop.drop` is invoked on a **normal** control-flow edge (`unwinding_count == 0`) and panics, it initiates an ordinary panic (which under `--panic unwind` continues unwinding remaining live locals in outer scopes).
   - If a destructor `Drop.drop` is invoked **while stack unwinding is already active** (`unwinding_count > 0`) and raises a second panic (not caught by an inner `catch_unwind` inside the destructor body itself), the runtime MUST NOT start a nested stack unwind or discard either panic: it **immediately aborts the process** with exit code **`101`** (writing `panic: panic in a destructor during unwinding\n` to `stderr` in hosted mode) (`SPEC-12 AXS-DROP-006`, `T522`, `T523`, `T524`).

### AXS-PAN-012 — MIR Unwind Control-Flow Edges & Optimizer Preservation (`0229 §76–79, AERR-57, AERR-64`, `tasks/0517 §90, §1560`, `tasks/0700 §440.38`, `SPEC-70 AXS-OPT-021`, `T522`)

1. **Explicit MIR Cleanup Terminators Under `--panic unwind`**:
   - In `compiler/mir/`, when `--panic unwind` is active:
     - `MirTerminator.Call { callee, args, destination, target, cleanup: Option<BasicBlockId> }` and `MirTerminator.Assert { cond, expected, msg, target, cleanup: Option<BasicBlockId> }` attach `cleanup = Option.Some(bb_cleanup)` whenever the callee/operation may panic and the current scope has live droppable places, an active `Drop.drop` double-panic guard, or an `extern "C"` no-unwind barrier.
     - Cleanup basic blocks (`is_cleanup = true`) execute `MirTerminator.Drop { place, target, unwind: Option.Some(bb_double_panic_abort) }` in reverse declaration order and end with `MirTerminator.Resume` (continuing unwind to caller) or `MirTerminator.Abort` (at `extern "C"` barriers and double-panic pads).
   - When `--panic abort` is active (or when the callee is verified `@no_panic`), `cleanup` is `Option.None` (`AERR-57..58`).
2. **Optimizer Preservation Contract (`0229 §61–62, §79, AERR-50..51, AERR-64`, `SPEC-70 AXS-OPT-021`)**:
   - Any `Drop` of a type with user-defined `impl Drop` (or inner fields with observable `Drop`) on a reachable `cleanup` edge is an observable side effect (`AERR-50`). Optimization passes (`DCE`, `DSE`, `SROA`, `Inlining`, `LICM`, `BCE`) MUST NOT delete, skip, or reorder observable destructors along unwind edges (`AERR-64`), though trivial empty drops may be eliminated (`AERR-51`) and proven-non-panicking `Assert` edges (`Certainty.Proven` in `BCE`) may remove unreachable `cleanup` edges (`AFAIL-67`).

### AXS-PAN-013 — Native LIR Cleanup Landing Pads & Windows x64 SEH `.pdata`/`.xdata` Unwind Metadata (`0188 §1–58, AUNW-20..38, AEPI-20..23`, `tasks/0700 §440.21–38`, `T523`)

1. **Unified `FramePlan` $\to$ `ProloguePlan` + `UnwindPlan` Derivation (`0188 §2–3, §56–58, AUNW-20..30`, `AEPI-20..23`)**:
   - On Windows x64 (`x86_64-windows`), `compiler/target/x64/` derives `.xdata` `UNWIND_INFO` (`Version = 1`, `SizeOfProlog`, `CountOfCodes`, `FrameRegister`, `UnwindCode` array in descending prologue offset order: `UWOP_PUSH_NONVOL`, `UWOP_ALLOC_SMALL`, `UWOP_ALLOC_LARGE`, `UWOP_SET_FPREG`, `UWOP_SAVE_XMM128`) directly from the semantic `FramePlan` and `ProloguePlan`, never by pattern-matching encoded machine bytes (`AUNW-22..29`).
   - Epilogues obey canonical Windows x64 unwind-recognizable sequences (`add rsp, N` / `lea rsp, [rbp+N]`, `pop nonvol...`, `ret`), with return-value materialization completed strictly before the epilogue region (`AEPI-20..23`, `AUNW-30..31`).
2. **Cleanup Landing Pads & `.pdata` Function Table Relocation (`0188 §17–22, §38–43, §52, AUNW-24, AUNW-32..35`, `T523`)**:
   - Under `--panic unwind`, functions containing MIR cleanup blocks, `catch_unwind` frames, or `extern "C"` no-unwind barriers set `UNW_FLAG_UHANDLER` / `UNW_FLAG_EHANDLER` in `UNWIND_INFO.Flags` and append the RVA of the Axiom personality routine (`__axiom_seh_personality`) plus the function's scope cleanup table mapping instruction RVA ranges `[try_begin, try_end)` to cleanup landing-pad RVAs (`T523`).
   - `compiler/obj/` emits `.pdata` and `.xdata` COFF section contributions, and `compiler/link/` merges, relocates (`BeginAddress`, `EndAddress`, `UnwindInfoAddress` as image-relative `Rva`s), sorts `.pdata` deterministically by `BeginAddress` (`AUNW-32`), and populates PE Data Directory `[3]` (`Exception Table`).
   - Under `--panic abort`, functions emit zero cleanup landing pads and set `UNW_FLAG_NHANDLER` (`Flags = 0`), avoiding any personality routine or scope-table overhead (`0188 §18, §51`, `T523`).

### AXS-PAN-014 — `@no_panic` Attribute & Static Call-Graph Verification (`tasks/0700 §441.140–141`, `T522`)

1. **Declaration & Attribute Placement (`AX_TYPE_INVALID_NO_PANIC_ATTR`)**:
   - `@no_panic` may be attached to any `fn` declaration, trait method signature, or `extern "C" fn` declaration (`@no_panic pub fn decode_header(buf: view<[u8]>) -> Option<u32>`).
   - Attaching `@no_panic` to a non-function item (`struct`, `enum`, `union`, `static`, `const`, `type`) is rejected with `AX_TYPE_INVALID_NO_PANIC_ATTR`.
2. **Transitive Call-Graph & Operation Verification (`AX_PANIC_FORBIDDEN_IN_NO_PANIC`, `T522`)**:
   - For every defined function $f$ annotated with `@no_panic`, `compiler/sema/` and `compiler/mir/` verify that $f$'s body is statically free of panic paths, rejecting with `AX_PANIC_FORBIDDEN_IN_NO_PANIC` (`data.operation`, `data.callee`, primary span at the offending expression):
     1. **Explicit Panic Intrinsics (`data.operation = "explicit_panic"`)**: Any call to `panic(...)`, `assert(...)`, `assert_eq(...)`, or `unreachable()`.
     2. **Fallible Checked Operations (`data.operation = "checked_arith" | "checked_shift" | "checked_bounds" | "checked_cast"`)**: Checked integer `+`, `-`, `*`, `/`, `%`, unary `-`, bit shifts `<<`, `>>`, checked `u32 as char` cast, or direct slice/array indexing `a[i]` whenever the corresponding `MirTerminator.Assert` is not statically proven unreachable by constant/dominating bounds conditions. Inside `@no_panic`, code must use total/fallible operations (`wrapping_add`, `saturating_add`, `checked_add`, `slice.get(i)`, or an explicit dominating `if i < a.len()` check).
     3. **Non-`@no_panic` Callees (`data.operation = "may_panic_call"`)**: Any direct call to a function or method $g$ not annotated `@no_panic` (unless $g$ is a compiler intrinsic proven panic-free), any indirect call through a function pointer or closure not carrying `@no_panic`, or any call to an `extern "C"` function not explicitly annotated `@no_panic` (`AXS-PAN-023`).

---

## 3. FFI No-Unwind Barrier, Foreign Exception Isolation & Conservative Foreign Effect Model (`AXS-PAN-020`..`023`)

### AXS-PAN-020 — Mandatory FFI No-Unwind Abort Barrier Across `extern "C"` & Foreign ABI Boundaries (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-ABI-096`, `REQ-ABI-105`, `T522`, `T523`, `T524`)

1. **Strict Default No-Unwind Invariant (`0107 §63–64 AFERR-24`, `0119 §248 AFFI-22`, `0131 §66, §88 AFN-53`, `0138 §44–45, §100 AFFI-41`, `0229 §36, §54, AERR-39`, `tasks/0351 §38, AFAIL-57`, `tasks/0445 §186.62–64, §186.161 AFFI-60, AFFI-83`, `tasks/0517 §192`, `tasks/0585 §12`, `tasks/0700 §440.40–41`)**:
   - **An Axiom panic MUST NEVER unwind across a foreign ABI boundary (`extern "C"`, `extern "system"`, `extern "win64"`, `extern "sysv64"`, `extern "stdcall"`, `extern "fastcall"`, `extern "vectorcall"`, `extern "interrupt"`, `extern "wasm"`) by default** (`REQ-FFI-004`, `REQ-FFI-010`, `REQ-FFI-019`, `REQ-FFI-023`, `REQ-FFI-041`, `REQ-FFI-061`, `REQ-ABI-096`, `REQ-ABI-105`).
2. **Compiler-Inserted Abort Guard on Exported Functions & Foreign Callbacks (`T522`, `T523`, `T524`)**:
   - Every Axiom-defined function with a foreign calling convention — including `pub extern "C" fn ...`, `@export extern "C" fn ...`, `extern "system" fn ...`, `extern "interrupt" fn ...`, and any non-capturing function/closure coerced to an `extern "C" fn(...)` callback pointer — is lowered by `compiler/mir/` and `compiler/target/x64/` with a mandatory **FFI No-Unwind Abort Barrier** enclosing its entire body:
     - Under `--panic unwind`, if a panic is raised inside the `extern "C"` function or any Axiom function it calls (and is not caught by an inner `std.panic.catch_unwind` before reaching the `extern "C"` frame), the unwinder executes all pending `Drop` destructors for live initialized locals within the Axiom frames down to and including the `extern "C"` function's own local scope (`AXS-PAN-010`), and upon reaching the `extern "C"` frame boundary, executes `MirTerminator.Abort` — **immediately terminating the process with exit code `101`** (`panic: panic cannot unwind across extern "C" FFI boundary\n`) rather than unwinding into the C/foreign caller (`REQ-FFI-004`, `REQ-FFI-019`, `REQ-ABI-096`, `REQ-ABI-105`).
     - Under `--panic abort`, the panic terminates immediately at the panic site with exit code `101` (`AXS-PAN-003`).

### AXS-PAN-021 — Foreign Exception Non-Equivalence & Prohibition of Foreign Unwinding Across Axiom Frames (`REQ-FFI-093`, `REQ-FFI-094`, `REQ-ABI-096`, `REQ-FFI-127`, `T522`, `T523`, `T524`)

1. **Axiom Panic $\ne$ Foreign Exception (`REQ-FFI-094`, `0138 §46 AFFI-42`, `tasks/0351 §38 AFAIL-56`, `tasks/0413 §47, §70`)**:
   - An Axiom panic is **not** semantically equivalent to a C++ exception, foreign language exception, or arbitrary OS software exception (`REQ-FFI-094`). Foreign exceptions never automatically convert into Axiom `Result<T, E>` values or Axiom panics (`AFAIL-56`).
2. **Foreign Unwind Cannot Cross Into Axiom Frames (`REQ-FFI-093`, `REQ-ABI-096`, `0229 §35 AERR-38`, `tasks/0413 §70`, `tasks/0445 §186.161 AFFI-61..62`)**:
   - Foreign stack unwinding (C++ `throw`, C `longjmp`, or foreign SEH unwind) MUST NOT propagate across an `extern "C"` call site into Axiom stack frames without an explicit, target-verified unwind compatibility contract (`REQ-FFI-093`, `REQ-ABI-096`). Foreign libraries that use exceptions internally must catch them on the foreign side of the `extern "C"` boundary and translate them into C ABI return codes or out-parameters (`0229 §35`, `AERR-38, AERR-40`).
3. **Preservation of Axiom's Semantic Model Across FFI (`REQ-FFI-127`, `tasks/0585 §1`)**:
   - FFI integration never weakens Axiom's semantic invariants (`REQ-FFI-127`): the compiler never assumes that foreign code respects Axiom ownership, `view`/`mut_view` aliasing exclusivity, lifetime bounds, panic containment, `Send`/`Share` thread safety, or internal `extern "axiom"` ABI layout unless wrapped in an explicit boundary contract.

### AXS-PAN-022 — Explicit FFI Error-Code / Status Adapter Contracts (`REQ-FFI-019`, `REQ-ABI-096`, `REQ-ABI-105`, `0131 §66`, `0229 §36, §54, AERR-40`, `tasks/0351 §37–38, AFAIL-58..59`, `tasks/0517 §192`, `tasks/0700 §440.41`)

1. **Converting Panics to Foreign Error Codes at the Boundary (`REQ-FFI-019`, `REQ-ABI-096`, `REQ-ABI-105`)**:
   - When an exported `extern "C"` function or callback contract specifies that Axiom panics must be reported as an integer status code or `@repr(C)` status struct rather than aborting the process (`REQ-FFI-019`, `REQ-ABI-105`), the boundary must use an explicit adapter:
     - **Library Adapter (`std.panic.catch_unwind`)**: The `extern "C"` function wraps its inner Axiom call in `std.panic.catch_unwind(|| ...)` and maps `Result.Ok(v) => v` and `Result.Err(_) => ERR_CODE` (`0229 §54`, `tasks/0445 §186.64`).
     - **Declarative Adapter (`@ffi_panic_adapter(error_code = <const_int>)`)**: Attaching `@ffi_panic_adapter(error_code = -1)` to an `extern "C" fn` returning a C integer type synthesizes the `catch_unwind` wrapper around the function body, returning `<const_int>` if an uncaught panic reaches the boundary under `--panic unwind` (`REQ-ABI-096`, `REQ-ABI-105`).
2. **Rejection of Invalid Cross-FFI Unwind Contracts (`AX_FFI_INVALID_UNWIND_CONTRACT`)**:
   - Attaching an unsupported cross-FFI unwind attribute (such as requesting raw Axiom panic unwinding across `extern "C"` without an adapter or attaching `@ffi_panic_adapter` to a function whose return type cannot represent the status code) is rejected at compile time with `AX_FFI_INVALID_UNWIND_CONTRACT` (`REQ-FFI-093`, `REQ-ABI-096`, `REQ-ABI-105`).

### AXS-PAN-023 — Conservative Semantic Effect Modeling of Unannotated `extern "C"` Functions (`REQ-FFI-125`, `tasks/0478 §40, ASEM-49`, `SPEC-50 AXS-UNS-035`, `SPEC-53 AXS-SEC-005`)

1. **Five Conservative Default Effects (`REQ-FFI-125`, `ASEM-49`)**:
   - Any foreign function (`extern "C" fn ...`) that lacks explicit verified semantic effect contracts (`@no_panic`, `@ffi_pure`, `@ffi_no_escape`, `@ffi_nosync`) MUST be conservatively modeled by `compiler/sema/`, `compiler/mir/`, and `compiler/opt/` (`SPEC-70 AXS-OPT-021`, `SPEC-71 AXS-ALIAS-003`) as potentially performing all five of the following effects (`REQ-FFI-125`):
     1. **Reading (`MayRead`)**: Reading any memory reachable through raw pointer arguments or exposed addresses;
     2. **Writing (`MayWrite`)**: Mutating any mutable memory reachable through raw pointer arguments or exposed addresses;
     3. **Escaping (`MayEscape`)**: Retaining or storing raw pointers passed to it beyond the call;
     4. **Panicking / Diverging (`MayPanic`)**: Potentially panicking, invoking a panicking callback, or terminating abnormally — so calling an unannotated `extern "C"` function inside a `@no_panic` function is rejected with `AX_PANIC_FORBIDDEN_IN_NO_PANIC` (`AXS-PAN-014`) unless the `extern` declaration is explicitly marked `@no_panic`, and under `--panic unwind` callers retain cleanup landing pads for live droppable locals across the call;
     5. **Synchronizing (`MaySync`)**: Acting as an opaque synchronization barrier across threads (`MemoryEffect.Synchronize`), preventing the optimizer from reordering shared memory accesses across the `extern "C"` call.

---

## 4. Diagnostics, Canonical Examples & Requirement Traceability (`AXS-PAN-050`..`053`)

### AXS-PAN-050 — Diagnostic Codes Owned or Referenced by `SPEC-54`

| Code | Area | Sev | Delivering Task | Condition & Normative Rule |
|---|---|---|---|---|
| `AX_DRIVER_INVALID_PANIC_STRATEGY` | `DRIVER` | `error` | `T522` | Unknown `--panic <strategy>` or `axiom.toml` `panic` value outside `{"abort", "unwind"}` (exit code `2`; `AXS-PAN-002`). |
| `AX_DRIVER_PROFILE_FORBIDDEN_CAP` | `DRIVER` | `error` | `T512` / `T522` | `--panic unwind` requested or `RuntimeCap.Unwind` required in `--profile freestanding` or `--profile kernel` (`AXS-PAN-002`, `SPEC-52 AXS-FRE-022`). |
| `AX_PANIC_FORBIDDEN_IN_NO_PANIC` | `UNSAFE` / `VERIFY` | `error` | `T522` | A `@no_panic` function directly or transitively invokes `panic(...)`, `assert(...)`, `unreachable()`, unproven checked arithmetic/shift/cast/indexing (`MirTerminator.Assert`), or a non-`@no_panic` callee / unannotated `extern "C"` function (`AXS-PAN-014`, `AXS-PAN-023`). |
| `AX_TYPE_INVALID_NO_PANIC_ATTR` | `TYPE` | `error` | `T522` | `@no_panic` attached to a non-function item (`struct`, `enum`, `union`, `static`, `const`, `type`) (`AXS-PAN-014`). |
| `AX_FFI_INVALID_UNWIND_CONTRACT` | `FFI` | `error` | `T522` | Invalid or unsupported cross-FFI unwind attribute on an `extern "C"` declaration or callback (`REQ-FFI-093`, `REQ-ABI-096`, `REQ-ABI-105`, `AXS-PAN-022`). |

### AXS-PAN-051 — Canonical Positive Examples (`=` and `.` Syntax)

#### Example 1 — `std.panic.catch_unwind`, Reverse-Order `Drop` Across Frames, `@no_panic`, and FFI Error-Code Adapter (`AXS-PAN-004`..`022`)
```axiom
// Compiled with: axiomc run --panic unwind panic_recovery.ax
module demo.panic_recovery

use std.panic.catch_unwind
use std.panic.PanicError
use std.core.result.Result
use std.core.option.Option

pub struct Guard {
    pub id: i32,
}

impl Drop for Guard {
    fn drop(self: mut_view<Guard>) {
        // Runs in reverse declaration order during unwinding (AXS-PAN-010):
        println(self.id)
    }
}

// Verified panic-free at compile time (AXS-PAN-014):
@no_panic
pub fn safe_wrapping_checksum(a: u32, b: u32) -> u32 {
    return wrapping_add(a, b)
}

fn inner_MightPanic(flag: bool) -> i32 {
    let g_inner_1 = Guard { id = 10 }
    let g_inner_2 = Guard { id = 20 }
    if flag {
        panic("boom inside inner frame")
    }
    return g_inner_1.id + g_inner_2.id
}

fn outer_work() -> i32 {
    let g_outer_1 = Guard { id = 1 }
    let g_outer_2 = Guard { id = 2 }
    let v = inner_MightPanic(true)
    return v + g_outer_1.id + g_outer_2.id
}

// Explicit FFI boundary adapter converting panics into C error code `-1` (REQ-FFI-019, REQ-ABI-105, AXS-PAN-022):
@export
@no_mangle
pub extern "C" fn axiom_ffi_entry_adapted() -> i32 {
    let res = catch_unwind(outer_work)
    match res {
        Result.Ok(v) => return v,
        Result.Err(_) => return -1i32,
    }
}

pub fn main() -> i32 {
    let check = safe_wrapping_checksum(100u32, 200u32)
    let code = axiom_ffi_entry_adapted()
    // Prints 20, 10, 2, 1 during unwind cleanup, then returns -1:
    if code == -1i32 && check == 300u32 {
        return 0
    }
    return 1
}
```

#### Example 2 — Mandatory FFI No-Unwind Abort Barrier on Uncaught `extern "C"` Callback (`AXS-PAN-020`)
```axiom
module demo.ffi_abort_barrier

// If C invokes `c_callback(0)` and `panic` is not caught inside Axiom,
// the compiler-inserted FFI barrier drops `local_guard` and immediately aborts
// with exit code 101 before unwinding can cross `extern "C"` (REQ-FFI-004, REQ-ABI-096):
@export
@no_mangle
pub extern "C" fn c_callback(x: i32) -> i32 {
    if x == 0i32 {
        panic("uncaught panic at FFI boundary")
    }
    return x
}
```

### AXS-PAN-052 — Canonical Negative Examples (`=` and `.` Syntax)

```axiom
// Compiled with: axiomc check bad_no_panic.ax
module demo.bad_no_panic

extern "C" {
    // Unannotated extern "C" function is conservatively modeled as MayPanic (REQ-FFI-125, AXS-PAN-023):
    fn foreign_may_fail(x: i32) -> i32
}

fn helper_may_panic(x: i32) -> i32 {
    if x < 0 {
        panic("negative input")
    }
    return x
}

@no_panic
pub fn bad_no_panic_fn(arr: view<[4]i32>, idx: usize, a: i32, b: i32) -> i32 {
    // ERROR [AX_PANIC_FORBIDDEN_IN_NO_PANIC]: explicit `assert` may panic inside `@no_panic` function (AXS-PAN-014)
    assert(idx < 4usize)

    // ERROR [AX_PANIC_FORBIDDEN_IN_NO_PANIC]: checked addition `a + b` may panic on overflow; use `wrapping_add` or `checked_add` (AXS-PAN-014)
    let sum = a + b

    // ERROR [AX_PANIC_FORBIDDEN_IN_NO_PANIC]: unproven bounds-checked index `arr[idx]` may panic inside `@no_panic` function (AXS-PAN-014)
    let elem = arr[idx]

    // ERROR [AX_PANIC_FORBIDDEN_IN_NO_PANIC]: calling non-`@no_panic` function `helper_may_panic` inside `@no_panic` function (AXS-PAN-014)
    let h = helper_may_panic(sum)

    // ERROR [AX_PANIC_FORBIDDEN_IN_NO_PANIC]: calling unannotated `extern "C"` function `foreign_may_fail` modeled as `MayPanic` (`REQ-FFI-125`, AXS-PAN-023)
    let ext = unsafe { foreign_may_fail(h) }
    return elem + ext
}
```

### AXS-PAN-053 — Requirement & Task Traceability Matrix (`T521`–`T524`)

| Requirement ID | Primary Rule(s) | Delivering Tasks | Verification Coverage |
|---|---|---|---|
| `REQ-FFI-004` | `AXS-PAN-020`, `AXS-PAN-051` | `T521`, `T523`, `T524` | Panic must not unwind across FFI boundary by default (`tests/run/panic_native`, `tests/conformance/p13/e13_5_panic_unwinding`). |
| `REQ-FFI-010` | `AXS-PAN-020` | `T521` | Axiom panic does not cross foreign ABI boundaries by default (`AFFI-22`). |
| `REQ-FFI-019` | `AXS-PAN-020`, `AXS-PAN-022`, `AXS-PAN-051` | `T521`, `T523`, `T524` | Axiom panics do not unwind across foreign ABI boundaries by default and are converted to error codes or abort per policy (`tests/run/panic_native`, `tests/conformance/p13/e13_5_panic_unwinding`). |
| `REQ-FFI-023` | `AXS-PAN-020`, `AXS-PAN-022` | `T521` | Axiom panics do not cross FFI ABI boundaries by default and are handled at the boundary (`AFN-53`). |
| `REQ-FFI-041` | `AXS-PAN-020` | `T521`, `T522` | Must not default unwind across C ABI (`tests/run/panic_oracle`). |
| `REQ-FFI-061` | `AXS-PAN-020` | `T521` | `AFFI-41`: Panic must not cross C ABI by default. |
| `REQ-FFI-093` | `AXS-PAN-021`, `AXS-PAN-022`, `AXS-PAN-050` | `T521`, `T522` | Foreign unwind cannot cross an ABI boundary without an explicit compatible contract (`AX_FFI_INVALID_UNWIND_CONTRACT`). |
| `REQ-FFI-094` | `AXS-PAN-021`, `AXS-PAN-013` | `T523` | Axiom panic is not automatically equivalent to a foreign exception (`tests/run/panic_native`). |
| `REQ-ABI-096` | `AXS-PAN-020`, `AXS-PAN-021`, `AXS-PAN-022` | `T521`, `T522`, `T523`, `T524` | Axiom panics never unwind across foreign ABI boundaries, foreign exceptions never unwind across Axiom frames, and unwind behavior is declared in explicit ABI contracts (`AFFI-60..62`). |
| `REQ-FFI-125` | `AXS-PAN-023`, `AXS-PAN-014`, `AXS-PAN-052` | `T521` | Foreign functions (`extern "C"`) lacking explicit contracts are conservatively modeled as potentially reading, writing, escaping, panicking, and synchronizing (`ASEM-49`). |
| `REQ-ABI-105` | `AXS-PAN-020`, `AXS-PAN-022`, `AXS-PAN-051` | `T521`, `T522` | Panic must not cross an `extern "C"` boundary unless an explicit ABI adapter contract exists (`0517 §192`). |
| `REQ-FFI-127` | `AXS-PAN-021` | `T524` | FFI integration never breaks Axiom's semantic model (`0585 §1`, `tests/conformance/p13/e13_5_panic_unwinding`). |

## Sources

- `docs/base/specs/0107 - Axiom — Error Handling, Failure & Panic Model v0.1.md` (`§1–64, AFERR-11..37`)
- `docs/base/specs/0119 - 215. Bốn tầng representation của Axiom.md` (`§247–248, §259, AFFI-22`)
- `docs/base/specs/0131 - AXIOM LANGUAGE SPECIFICATION v0.1.md` (`§66, §88, AFN-53`)
- `docs/base/specs/0138 - AXIOM LANGUAGE SPECIFICATION v0.1.md` (`§44–46, §100, AFFI-41..42`)
- `docs/base/specs/0188 - LVII — PE-UNWIND-001 Windows x64 .pdata.xdata.md` (`§1–58, AUNW-20..38, AEPI-20..23`)
- `docs/base/specs/0229 - ERRORPANICUNWIND-001.md` (`§1–84, AERR-20..65`)
- `docs/base/tasks/0351 - BOOTSTRAP-092 — Error, Result, Panic, Cancellation & Failure Architecture.md` (`§1–63, AFAIL-20..77`)
- `docs/base/tasks/0413 - BOOTSTRAP-154 — FFI, C ABI, System ABI & Foreign Function Interface Safety.md` (`§47, §70, AFFI-41, AFFI-60..62`)
- `docs/base/tasks/0445 - BOOTSTRAP-186 — FFI, C ABI, Foreign Types & Safe Interoperability Boundary.md` (`§186.62–64, §186.161, AFFI-60..62, AFFI-83`)
- `docs/base/tasks/0478 - BOOTSTRAP-219 — AXIOM FORMAL SEMANTIC KERNEL & EXECUTION MODEL.md` (`§24, §40, ASEM-49`)
- `docs/base/tasks/0517 - BOOTSTRAP-258 — AXIOM CALLING CONVENTION, FUNCTION ABI, PARAMETER PASSING, RETURN ABI & CALL LOWERING.md` (`§90, §192`)
- `docs/base/tasks/0585 - BOOTSTRAP-326 — AXIOM FOREIGN FUNCTION INTERFACE (FFI) & INTEROP CONTRACT ENGINE.md` (`§1, §12`)
- `docs/base/tasks/0700 - BOOTSTRAP-440 — DEBUG INFO, STACK UNWINDING, PANICEXCEPTION RUNTIME & NATIVE DEBUGGER CONTRACT.md` (`§440.21–44, §440.101–113, §441.28–29, §441.63–64, §441.140–141`)
- `spec/SPEC-03-core-semantics.md` (`AXS-SEM-070`..`082`)
- `spec/SPEC-12-drop.md` (`AXS-DROP-001`..`008`)
- `spec/SPEC-50-unsafe-ub-ffi.md` (`AXS-UNS-030`..`036`)
- `spec/SPEC-52-freestanding-runtime-composition.md` (`AXS-FRE-002`, `AXS-FRE-011`, `AXS-FRE-020`..`022`)
