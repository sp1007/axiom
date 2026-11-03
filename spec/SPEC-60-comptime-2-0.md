# SPEC-60 — Canonical Comptime 2.0, Partial Evaluation, Specialization & Const/Static/TLS Initialization Specification

Status: draft (T550, 2026-11-03)
Owner: axiom-architect
Consolidates: `specs/0102 (§1–68)`; `specs/0111 (§47)`; `specs/0115 (§59, ACOMP-20..21)`; `specs/0120 (§276–278, ACOMP-22..23)`; `specs/0131 (§68–69, §88 AFN-55..56)`; `specs/0140 (Part XXI §1–48, ACOMP-25..44)`; `tasks/0340 (§1–100)`; `tasks/0346 (§1–100, ACOMP2-20..100)`; `tasks/0443 (§184.145, APROC-30..34)`; `tasks/0453 (§194.44, ATARGET-22..23, 35..36)`; `tasks/0464 (§205.19, ATIME-47..49)`; `tasks/0509 (§1–183, COMPTIME-20..100)`; `tasks/0514 (§1–202, AGLOBAL-20..165)`; `spec/SPEC-02-grammar.md`; `spec/SPEC-03-core-semantics.md`; `spec/SPEC-04-core-extensibility.md`; `spec/SPEC-10-ownership.md`; `spec/SPEC-11-capability.md`; `spec/SPEC-12-drop.md`; `spec/SPEC-30-concurrency.md`; `spec/SPEC-31-atomics.md`; `spec/SPEC-32-threads-sync.md`; `spec/SPEC-50-unsafe-ub-ffi.md`; `spec/SPEC-52-freestanding-runtime-composition.md`; `spec/SPEC-53-safety-profiles-capability-security.md`; `spec/SPEC-73-inlining-specialization-devirt.md`; `spec/SPEC-75-lto-wpo-section-gc-pgo.md`.
Covers: `REQ-CTM-001`..`007`, `REQ-CTM-012`..`018`, `REQ-CTM-023`..`038`, `REQ-CORE-683`..`697`, `REQ-CORE-2130`..`2142`, `REQ-CORE-2214`..`2243` (and specifies the E14.1 contract for `T551`–`T555`: `REQ-CTM-008`..`011`, `REQ-CTM-041`..`042`, `REQ-CTM-044`, `REQ-CTM-046`..`047`, `REQ-CORE-698`..`763`, `REQ-CORE-2150`..`2169`, `REQ-CORE-2180`..`2213`, `REQ-CORE-2244`..`2360`).
Consumers: `compiler/ast/`, `compiler/parser/`, `compiler/hir/`, `compiler/sema/`, `compiler/types/`, `compiler/own/`, `compiler/mir/`, `compiler/interp/`, `compiler/opt/`, `compiler/lir/`, `compiler/target/x64/`, `compiler/obj/`, `compiler/driver/`, `T551`–`T555`.

## Tóm tắt

Tài liệu `SPEC-60` chuẩn hóa mô hình thực thi **Comptime 2.0**, cơ chế nâng giá trị (`value lifting`) và rào cản cấm rò rỉ tài nguyên (`AX_CTM_RESOURCE_ESCAPE`), lượng giá từng phần (`partial evaluation`) và chuyên biệt hóa (`specialization`), cùng ranh giới ngữ nghĩa giữa `const`, `static`, và bộ nhớ cục bộ luồng (`@thread_local` / `TLS`) cho phân hệ `E14.1` (Phase `P14`):
- **Một ngôn ngữ duy nhất với ba chế độ thực thi (`const`, `comptime`, `runtime`) (`ACOMP2-20..34`, `COMPTIME-20..30`, `REQ-CTM-001`, `REQ-CTM-012..014`, `REQ-CTM-037`, `REQ-CORE-683..697`, `REQ-CORE-2130..2142`, `REQ-CORE-2213`)**: Thực thi tại thời điểm biên dịch là một pha thực thi của chính ngôn ngữ Axiom, không phải ngôn ngữ macro thứ hai và không có hệ thống kiểu hay ownership riêng. Code `comptime` tuân thủ cùng hệ thống kiểu, kiểm tra quyền sở hữu (`move`/`Copy`), capability (`view<T>`/`mut_view<T>`), hệ thống hiệu ứng (`effects`), và hủy tất định (`Drop`) trên MIR đã kiểm định (`Verified MIR`).
- **`comptime fn`, khối `comptime { ... }`, tham số `comptime`, sandbox mặc định và rào cản không thoát tài nguyên (`AX_CTM_CAPABILITY_DENIED`, `AX_CTM_RESOURCE_ESCAPE`, `REQ-CTM-002..011`, `REQ-CTM-016..018`, `REQ-CTM-023..034`, `REQ-CTM-036..038`, `REQ-CTM-044`, `REQ-CTM-046..047`, `T551`, `T552`)**: Mặc định, môi trường `comptime` chạy trong sandbox cô lập không có quyền hệ điều hành ngầm (cấm truy cập tệp, mạng, biến môi trường, đồng hồ thời gian thực, tiến trình ngoài, hoặc FFI tùy ý; từ chối với `AX_CTM_CAPABILITY_DENIED`). Khối `unsafe` trong `comptime` không bao giờ vượt qua ranh giới sandbox (`ACOMP2-27`, `COMPTIME-40`). Mọi cấp phát động trong `comptime` (`Vec<T>`, `String`, `Box<T>`) thuộc bộ nhớ của trình biên dịch và phải được `Drop` tất định trước khi kết thúc; mọi handle tài nguyên, `mut_view<T>`, `view<T>` trỏ tới vùng nhớ tạm, hoặc con trỏ thô của trình thông dịch thoát sang giá trị `runtime` đều bị chặn bởi `AX_CTM_RESOURCE_ESCAPE`.
- **Lượng giá từng phần, chuyên biệt hóa theo tham số `comptime`/hằng số, tách biệt Host-vs-Target và bộ nhớ đệm theo dõi phụ thuộc (`ACOMP2-63..100`, `COMPTIME-41..47`, `COMPTIME-70..91`, `REQ-CTM-031`, `REQ-CTM-035`, `REQ-CTM-041..042`, `T553`, `T555`)**: Các hàm nhận tham số `comptime` hoặc closure hằng được chuyên biệt hóa tĩnh và rút gọn nhánh `if comptime` mà vẫn bảo toàn nguyên vẹn bẫy tràn số/chia cho 0 trên các nhánh runtime còn lại. Mọi truy vấn layout (`size_of<T>()`, `align_of<T>()`, endianness) trong `comptime` luôn dùng thông số của **target** (`TargetDesc`), không dùng thông số máy host. Kết quả `comptime` được lưu đệm theo khóa băm ngữ nghĩa đầy đủ (`ComptimeCacheKey`), bảo đảm kết quả trùng khớp 100% với khi chạy mới.
- **Tam phân ngữ nghĩa `const` vs `static` vs `TLS` và hiện thực hóa `.rdata`/`.data`/`.bss` không kèm VM (`AGLOBAL-20..165`, `REQ-CTM-015`, `REQ-CORE-2214..2360`, `T552`, `T554`)**: `const` là giá trị ngữ nghĩa tại thời điểm biên dịch (không bắt buộc có địa chỉ lưu trữ cố định, được phép gộp/inline tự do); `static` là vùng lưu trữ có vòng đời mô-đun/chương trình với danh tính địa chỉ xác định và khởi tạo hằng tất định (không có constructor toàn cục ẩn kiểu C++ hay destructor khi thoát tiến trình); `@thread_local static` (`TLS`) là vùng lưu trữ gắn với từng ngữ cảnh thực thi luồng. Các cấu trúc dữ liệu phức tạp sinh từ `comptime` được hạ cấp trực tiếp xuống `.rdata`, `.data`, `.bss` mà không liên kết bất kỳ máy ảo `comptime` nào vào tệp thực thi (`COMPTIME-24..25`).

---

## 1. Unified Semantic Model: Evaluation Modes, Surface Forms & Capability Sandbox (`AXS-CTM-001`..`005`)

### AXS-CTM-001 — Unified Language Principle: One Language, Three Evaluation Modes (`ACOMP2-20..26`, `ACOMP2-34`, `COMPTIME-20..30`, `REQ-CTM-001`, `REQ-CTM-012`..`015`, `REQ-CTM-037`, `REQ-CORE-683`..`689`, `REQ-CORE-697`, `REQ-CORE-2130`..`2142`, `REQ-CORE-2213`)

1. **Three Evaluation Modes of One Language (`ACOMP2-20..21`, `COMPTIME-20..23`)**:
   - Axiom defines three distinct evaluation modes of the **exact same source language**:
     1. **`const` evaluation**: Compile-time evaluation of pure constant expressions and `const` items producing immutable compile-time semantic values (`ACOMP2-34`, `REQ-CTM-015`).
     2. **`comptime` execution**: General-purpose compile-time execution of `comptime fn` bodies, `comptime { ... }` blocks, and `comptime` generic arguments inside the compiler execution environment (`COMPTIME-23`).
     3. **`runtime` execution**: Target execution of compiled program code under the MIR oracle (`--interp`) or native machine code (`SPEC-03 AXS-SEM-001`).
   - Comptime is **another execution phase, never a second programming language** (`REQ-CTM-012`, `REQ-CTM-013`, `ACOMP2-21`, `COMPTIME-21`, `REQ-CORE-2130..2131`, `REQ-CORE-2213`). Axiom has no separate untyped macro sub-language, no token-stream preprocessor (`#define`/`#ifdef`), and no arbitrary compiler plugin hook that can corrupt compiler invariants (`REQ-CTM-012`).
2. **Identical Type, Ownership, Capability, Effect & Drop Verification (`ACOMP2-22..26`, `ACOMP-25`, `COMPTIME-26..30`, `REQ-CTM-001`, `REQ-CTM-014`, `REQ-CTM-037`)**:
   - Every `const` and `comptime` body passes through the exact same frontend and middle-end pipeline (`Source -> Lexer -> Parser -> AST -> Resolver -> HIR -> Typeck -> THIR -> Ownership/Init/Capability/Drop -> Verified MIR`) before the comptime interpreter executes a single instruction (`INV-PIPE-001`, `INV-PIPE-002`, `COMPTIME-26..30`).
   - Comptime code obeys the same type and trait resolution rules (`ACOMP2-22`, `ACOMP2-26`), move vs `Copy` ownership rules (`ACOMP2-23`, `REQ-CTM-001`), `view<T>` / `mut_view<T>` non-overlapping capability rules (`ACOMP2-25`, `COMPTIME-28`), effect tracking (`COMPTIME-29`), and deterministic lexical `Drop` rules (`ACOMP2-24`, `COMPTIME-53`) as runtime code. Comptime never bypasses safety verification (`COMPTIME-30`, `REQ-CORE-2142`).
3. **Canonical Surface Syntax (`ADR-0007`, `SPEC-02 AXS-GRM-003`, `REQ-CTM-042`)**:
   - Comptime and runtime share one surface grammar: `=` for bindings and field initializers, `.` for module, type, enum, and method paths, `<...>` for generic arguments (`size_of<T>()`), and `use` as the sole module import keyword (`import` is rejected with `AX_PARSE_IMPORT`, `REQ-CTM-042`).

### AXS-CTM-002 — Surface Forms: `comptime fn`, `comptime { ... }` Blocks & Comptime Generic Parameters (`ACOMP2-35..36`, `AFN-55`, `SPEC-04 AXS-EXT-031/033/120`, `REQ-CTM-008`, `REQ-CTM-010`, `REQ-CORE-698..699`, `REQ-CORE-2188..2189`, `T551`)

1. **`comptime fn` Declarations (`ACOMP2-35`, `AFN-55`, `REQ-CTM-008`, `REQ-CTM-010`, `REQ-CORE-698`)**:
   - A function prefixed with `comptime fn` (`HirFnFlags.is_comptime = true`, `SPEC-04 AXS-EXT-031`) executes exclusively during compile-time evaluation.
   - Calling a `comptime fn` from a runtime expression context (outside a `const` initializer, `static` constant initializer, `comptime { ... }` block, const generic argument, or another `comptime fn`) is rejected by `compiler/sema/` with `AX_CTM_RUNTIME_CALL_FORBIDDEN`.
   - Conversely, an ordinary pure function `fn f(...)` (without the `comptime` modifier) may be called inside both `comptime` and `runtime` contexts provided its body and transitive callees satisfy the comptime capability sandbox rules (`AXS-CTM-003`).
2. **`comptime { ... }` Expression Blocks (`ACOMP2-36`, `SPEC-04 AXS-EXT-033`, `REQ-CORE-699`)**:
   - A `comptime { <stmts>; <tail_expr> }` block (`ExprKind.ComptimeBlock`) inside any function body is evaluated eagerly during compilation before runtime code generation (`ACOMP2-36`).
   - Within a `comptime { ... }` block, reading a surrounding runtime local variable or runtime parameter (that is not declared `comptime` or `const`) is rejected with `AX_CTM_NON_CONST_CAPTURE` / `AX_CTM_RUNTIME_VALUE_IN_COMPTIME`.
   - The resulting compile-time value is validated across the Value Lifting Barrier (`AXS-CTM-011`) and spliced into the enclosing MIR body as a `ConstValue` / `ConstAlloc` operand.
3. **`comptime` / `const` Parameters (`COMPTIME-76..77`, `SPEC-04 AXS-EXT-031`, `REQ-CORE-2188..2189`)**:
   - Type declarations (`struct`, `enum`, `type`) and functions accept compile-time value parameters written `[T, const N: usize]` or `[T, comptime N: usize]`, as well as function-level `comptime` value parameters `fn scale(x: i32, comptime factor: i32) -> i32`.
   - Every argument passed to a `const` / `comptime` parameter MUST be a compile-time constant expression of the declared type, evaluated deterministically during type checking and monomorphization (`COMPTIME-76..77`). Two instantiated types `Matrix<f64, 4, 4>` and `Matrix<f64, 2 + 2, 4>` normalize to the identical canonical `TypeId`.

### AXS-CTM-003 — Sandboxed Authority by Default & Explicit External Capabilities (`ACOMP-23`, `ACOMP-34`, `ACOMP2-27..31`, `COMPTIME-38..42`, `COMPTIME-54`, `COMPTIME-68..69`, `COMPTIME-88..93`, `REQ-CTM-007`, `REQ-CTM-017`..`018`, `REQ-CTM-029`..`034`, `REQ-CTM-038`, `REQ-CTM-044`, `REQ-CTM-047`, `REQ-CORE-690`..`694`, `REQ-CORE-2150`..`2154`, `REQ-CORE-2166`, `REQ-CORE-2180`..`2181`, `REQ-CORE-2200`..`2205`, `REQ-CORE-2242`..`2243`, `T551`)

1. **Zero Ambient OS Authority in `comptime` (`COMPTIME-38..39`, `COMPTIME-92`, `REQ-CTM-017`, `REQ-CTM-029..030`, `SPEC-53 AXS-SEC-011`)**:
   - By default, `comptime` evaluation runs in a strict hermetic sandbox with **no ambient external authority** (`COMPTIME-39`, `REQ-CORE-2151`). Third-party packages and AI-generated comptime code receive zero implicit OS privileges (`COMPTIME-92..93`, `REQ-CTM-034`, `REQ-CORE-2204..2205`).
   - Any attempt during `comptime` or `const`/`static` initialization to invoke ambient filesystem I/O (`std.fs`, `host.open`/`read`/`write`), network I/O (`std.net`, `host.aio_*`), process environment queries (`std.env`, `host.env_get`, `REQ-CTM-044`), wall-clock or monotonic time (`std.time`, `host.monotonic_ns`, `REQ-CTM-047`), external process execution (`std.process`, `REQ-CTM-033`), or unmocked foreign `extern` FFI functions without an explicitly granted comptime capability is rejected at compile time with `AX_CTM_CAPABILITY_DENIED` (`REQ-CORE-691`, `REQ-CORE-2150`).
2. **`unsafe` Does Not Bypass Comptime Sandbox Restrictions (`ACOMP2-27`, `COMPTIME-40`, `REQ-CORE-690`, `REQ-CORE-2152`)**:
   - Inside a `comptime` context (when permitted by the active `--safety-profile`, `SPEC-53 AXS-SEC-002`), an `unsafe { ... }` block permits only raw-pointer manipulation over allocations created within the current comptime evaluation arena. `unsafe` NEVER grants host filesystem, network, environment, clock, process, or raw host-memory access (`ACOMP2-27`, `COMPTIME-40`).
3. **Explicit External Comptime Inputs & Reproducible-Build Constraints (`ACOMP-23`, `ACOMP-34`, `ACOMP2-28..31`, `COMPTIME-41..42`, `COMPTIME-88..91`, `REQ-CTM-007`, `REQ-CTM-018`, `REQ-CTM-031..033`, `REQ-CTM-038`, `REQ-CTM-044`, `REQ-CTM-047`)**:
   - External build-time inputs (such as declared compile-time environment variables `comptime_env("KEY")`, embedded project files `embed_bytes("path")` / `embed_str("path")`, or declared build-tool outputs) require explicit declaration in `axiom.toml` (`[comptime.capabilities]`) and compiler CLI policy (`COMPTIME-38`, `COMPTIME-91`, `REQ-CTM-030`, `REQ-CTM-032..033`).
   - Every external input read via an authorized comptime capability is automatically recorded as a **build dependency** (`REQ-CTM-018`, `ACOMP2-29`, `COMPTIME-41`) and hashed into the build and comptime cache identity (`ACOMP2-30`, `COMPTIME-42`, `COMPTIME-88`).
   - Under `--reproducible` / hermetic build mode (`ACOMP2-31`, `COMPTIME-89..90`, `REQ-CTM-031`, `REQ-CTM-038`, `REQ-CTM-047`), nondeterministic comptime capabilities (wall-clock time, unpinned environment variables, live network fetches, host random sources) are rejected with `AX_CTM_CAPABILITY_DENIED` unless pinned to deterministic manifest values.
4. **Disjoint Comptime vs Runtime Effect & Authority Domains (`COMPTIME-54`, `COMPTIME-68..69`, `AGLOBAL-47..48`, `REQ-CORE-2166`, `REQ-CORE-2180..2181`, `REQ-CORE-2242..2243`)**:
   - Comptime effect summaries and runtime effect summaries are tracked in separate domains (`COMPTIME-68..69`): a comptime computation that reads a declared build input produces a pure constant at runtime and does not infect the enclosing runtime function with runtime I/O or blocking effects.
   - Comptime capabilities never convert into runtime authority tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`), and runtime capabilities cannot be invoked during comptime (`COMPTIME-54`, `AGLOBAL-48`, `SPEC-53 AXS-SEC-011`).

### AXS-CTM-004 — Package Visibility, Semantic Type Generation & Re-Verification Contract (`ACOMP2-38..53`, `COMPTIME-73..75`, `REQ-CTM-025`..`028`, `REQ-CORE-701`..`716`, `REQ-CORE-2185`..`2187`, `T551`, `T552`)

1. **Visibility & Package API Boundaries (`ACOMP2-48..49`, `REQ-CTM-027`..`028`, `REQ-CORE-711`..`712`)**:
   - Comptime evaluation and compile-time reflection strictly obey module and package visibility rules (`REQ-CTM-027`, `ACOMP2-48`): a package cannot read or construct private fields, private items, or private representation internals of another package merely because execution happens in `comptime`.
   - Any `comptime` precondition or `const` generic constraint on a `pub` item is recorded in the package's semantic API fingerprint (`REQ-CTM-028`).
2. **Typed Semantic Generation, No Arbitrary IR Mutation & Mandatory Re-Verification (`ACOMP2-38..47`, `COMPTIME-73..75`, `REQ-CTM-025`..`026`, `REQ-CORE-701`..`710`, `REQ-CORE-2185`..`2187`)**:
   - Core Axiom provides structured, typed compile-time generation (`@derive`, generic/comptime specialization, and typed AST/HIR synthesis with deterministic type identity, `REQ-CTM-025..026`, `ACOMP2-46..47`) and forbids arbitrary compiler-IR mutation or unrestricted procedural token macros (`ACOMP2-44..45`, `REQ-CORE-707..708`).
   - Every comptime-generated declaration re-enters the standard semantic pipeline and must pass name resolution (`ACOMP2-39`), type checking (`ACOMP2-40`), ownership (`ACOMP2-41`), capability (`ACOMP2-42`), representation/ABI (`ACOMP2-43`, `COMPTIME-75`), FFI (`COMPTIME-74`), and GPU legality (`COMPTIME-73`) verification (`ACOMP2-38`, `REQ-CORE-701..706`).
3. **Compile-Time `Type` Values & Target Layout Queries (`ACOMP2-50..53`, `ACOMP2-97`, `REQ-CORE-713`..`716`, `REQ-CORE-760`)**:
   - `Type` descriptors and layout queries (`size_of<T>()`, `align_of<T>()`, `offset_of(T, field)`, `needs_drop<T>()`) are compile-time operations by default (`ACOMP2-50`, `ACOMP2-52`). No runtime type metadata (RTTI) is emitted into the binary unless explicitly requested by an opt-in reflection contract (`ACOMP2-51`, `ACOMP2-97`), and default Axiom struct layout does not promise stable physical field offsets across builds unless `@repr(C)` or `@abi(stable)` is declared (`ACOMP2-53`).

---

## 2. Comptime MIR Evaluator, Transient Heap, Deterministic `Drop` & Resource No-Escape Barrier (`AXS-CTM-010`..`013`)

### AXS-CTM-010 — Comptime MIR Execution, Transient Compiler Heap & Deterministic `Drop` (`ACOMP-21`, `ACOMP2-33`, `ACOMP2-57..58`, `COMPTIME-23..25`, `COMPTIME-51..53`, `REQ-CTM-001`, `REQ-CTM-003`, `REQ-CTM-005`, `REQ-CTM-016`, `REQ-CTM-036`, `REQ-CORE-686`..`687`, `REQ-CORE-696`, `REQ-CORE-720`..`721`, `REQ-CORE-2135`..`2137`, `REQ-CORE-2163`..`2165`, `T552`)

1. **Execution on Verified MIR in Isolated Compiler Memory (`COMPTIME-23`, `COMPTIME-51..52`, `ACOMP2-57..58`)**:
   - `compiler/interp` executes `const` items, `static` initializers, `comptime fn` calls, and `comptime { ... }` blocks on Verified MIR inside an isolated per-evaluation compiler arena (`ComptimeArena`).
   - Transient comptime allocations (`Vec<T>`, `String`, `Box<T>`, `HashMap<K, V>`) allocate from `ComptimeArena`, never from the target program's runtime heap (`ACOMP2-57..58`, `COMPTIME-51..52`), and the comptime VM is never linked into runtime binaries (`COMPTIME-24..25`, `REQ-CORE-2136..2137`).
2. **Deterministic Comptime `Drop` Execution (`REQ-CTM-003`, `REQ-CTM-016`, `REQ-CTM-036`, `ACOMP2-24`, `ACOMP2-33`, `COMPTIME-53`)**:
   - Every owned value constructed during comptime evaluation that is not moved into the final lifted return value executes its `Drop.drop` glue deterministically in reverse declaration order at scope exit before comptime evaluation finishes (`REQ-CTM-003`, `REQ-CTM-016`, `REQ-CTM-036`, `ACOMP2-33`, `COMPTIME-53`).
   - After top-level comptime evaluation and `Drop` completion, the evaluator verifies that no leaked un-dropped non-promoted resource handles remain in `ComptimeArena`.

### AXS-CTM-011 — Comptime-to-Runtime Value Lifting & Resource No-Escape Barrier (`AX_CTM_RESOURCE_ESCAPE`) (`ACOMP-20..22`, `ACOMP2-32..33`, `ACOMP2-59..60`, `AFN-56`, `COMPTIME-54..57`, `COMPTIME-81..82`, `REQ-CTM-002`, `REQ-CTM-004`..`006`, `REQ-CTM-009`, `REQ-CTM-011`, `REQ-CORE-695`..`696`, `REQ-CORE-722`..`723`, `REQ-CORE-2166`..`2169`, `REQ-CORE-2193`..`2194`, `T551`, `T552`)

1. **The Value Lifting Contract (`ACOMP-20..22`, `ACOMP2-32`, `ACOMP2-59..60`, `COMPTIME-55..57`, `REQ-CTM-002`, `REQ-CTM-004..006`)**:
   - Comptime evaluation produces **runtime values with valid target representations, never hidden runtime resources** (`ACOMP-20..21`, `COMPTIME-57`, `COMPTIME-82`, `REQ-CTM-004..005`).
   - When a value `v: T` exits a `comptime` boundary (`const` definition, `static` initializer, `comptime { ... }` block, or `comptime` argument), the compiler runs `lift_comptime_value(v, T)`:
     - **Permitted (Liftable) Values**:
       1. Scalar primitives (`i8..i128`, `u8..u128`, `isize`, `usize`, `f32`, `f64`, `bool`, `char`, `()`), SIMD `Vector<T, N>` / `Mask<N>`, and fieldless enums;
       2. Fixed-size arrays `[N]E`, tuples, structs, and payload enums whose active fields/elements are recursively liftable;
       3. Immutable views (`view<E>`, `view<[E]>`, `Str`) whose referent is either an existing `static` / `const` item or a comptime buffer explicitly promoted to a frozen read-only `.rdata` `ConstAlloc` table with `'static` lifetime (`ACOMP2-60`, `COMPTIME-81`);
       4. Function references (`FnDef` / `fn(...) -> ...`) naming compiled runtime functions.
     - **Forbidden Escapes (`AX_CTM_RESOURCE_ESCAPE`, `REQ-CTM-009`, `REQ-CTM-011`, `AFN-56`, `COMPTIME-55..56`)**:
       1. Unpromoted compiler-heap owners (`Box<T>`, `Vec<T>`, `String`, `HashMap<K, V>`) whose runtime representation would require a live runtime heap allocator handle;
       2. Any `view<T>` or `view<[T]>` borrowing a dead comptime stack local (`COMPTIME-56`);
       3. Any mutable capability `mut_view<T>` or `mut_view<[T]>` (comptime-lifted data is strictly immutable unless placed in a `static mut` / synchronized `static` owner);
       4. Raw pointers (`*const T`, `*mut T`) carrying transient `ComptimeAllocId` provenance (except null pointers or explicit `@addr`/`@at` hardware addresses);
       5. Compiler or OS resource handles and capability tokens (`FsCap`, `NetCap`, `EnvCap`, `ProcessCap`, `ClockCap`, file handles, sockets, locks).
   - Any value failing `lift_comptime_value` is rejected at compile time with `AX_CTM_RESOURCE_ESCAPE` (`data.type` naming the offending type or field path).

### AXS-CTM-012 — Comptime Panics, Assertions, Cycle Detection & Resource Budgets (`ACOMP2-37`, `ACOMP2-54..56`, `COMPTIME-48..50`, `COMPTIME-98`, `REQ-CTM-023`..`024`, `REQ-CORE-700`, `REQ-CORE-717`..`719`, `REQ-CORE-2160`..`2162`, `REQ-CORE-2210`, `T551`, `T552`)

1. **Comptime Failure Produces Structured Diagnostics, Never Compiler Crash or ICE (`ACOMP2-37`, `ACOMP2-54`, `COMPTIME-50`, `COMPTIME-98`, `REQ-CTM-023..024`)**:
   - The comptime evaluator runs in a fault-isolated oracle environment (`REQ-CTM-023`): arbitrary user code inside `comptime` (including `panic("...")`, `assert(false)`, checked integer overflow, division/remainder by zero, shift out of range, out-of-bounds indexing, or UB in `unsafe` comptime blocks) NEVER crashes the compiler process and NEVER triggers `AX_ICE_*` (`REQ-CTM-024`, `COMPTIME-50`).
   - Instead, the evaluator emits a located user diagnostic with the comptime call stack attached as notes: `AX_CTM_PANIC` (for explicit `panic` / failed `assert`), `AX_CONST_OVERFLOW`, `AX_CONST_DIV_ZERO`, `AX_CONST_SHIFT_RANGE`, or `AX_UNSAFE_INTERP_UB`.
2. **Deterministic Cycle Detection & Evaluation Budgets (`ACOMP2-55..56`, `COMPTIME-48..49`, `REQ-CORE-718..719`, `REQ-CORE-2160..2161`)**:
   - The evaluator tracks an active query stack of `(ItemId, CanonicalArgs)` frames; any re-entrant cycle among `const`, `static`, or `comptime` item evaluations is immediately rejected with `AX_CTM_CYCLE` (compatible with `AX_CONST_CYCLE` on `const` items, `COMPTIME-48`).
   - Every top-level comptime evaluation enforces deterministic budgets: step limit (default `10_000_000` steps, configurable via `--comptime-step-limit N`), call-stack depth limit (default `1024` frames), and arena memory budget (default `256 MiB`, configurable via `--comptime-mem-limit MiB`). Exceeding the step or depth limit emits `AX_CTM_STEP_LIMIT` (compatible with `AX_CONST_EVAL_LIMIT`); exceeding the memory budget emits `AX_CTM_MEM_LIMIT` (`ACOMP2-55..56`, `COMPTIME-49`).

### AXS-CTM-013 — Cross-Compilation Host-vs-Target Separation (`ACOMP2-92..94`, `COMPTIME-70..72`, `ATARGET-22..23, 35..36`, `REQ-CTM-046`, `REQ-CORE-755`..`757`, `REQ-CORE-2182`..`2184`, `T551`, `T552`, `T555`)

1. **Target Semantics Govern All Comptime Layout & Numeric Queries (`ACOMP2-92..93`, `COMPTIME-70..72`, `REQ-CTM-046`)**:
   - Cross-compilation strictly separates the **host execution context** (where `axiomc` runs) from the **target semantic context** (`TargetDesc`, `SPEC-04 AXS-EXT-060`, `ACOMP2-92`, `COMPTIME-70`, `REQ-CTM-046`).
   - Inside `comptime`, `size_of<T>()`, `align_of<T>()`, `offset_of(T, f)`, `usize`/`isize` bit width, byte endianness (`to_ne_bytes`/`from_ne_bytes`), struct padding, and `@cfg(target_arch = ...)` queries always evaluate using the **target** `TargetDesc` (`ACOMP2-93`, `COMPTIME-71`). Cross-compilation NEVER substitutes host layout for target layout (`COMPTIME-72`, `REQ-CORE-2184`).
   - `@cfg(...)` performs static configuration selection prior to typechecking disabled branches, whereas `comptime` performs typed semantic computation and specialization (`ACOMP2-94`, `REQ-CORE-757`).

---

## 3. Partial Evaluation, Comptime Specialization & Dependency-Tracked Caching (`AXS-CTM-020`..`022`)

### AXS-CTM-020 — `comptime` Guarantee vs Opportunistic Optimizer Folding (`ACOMP2-61..69`, `COMPTIME-78..80`, `REQ-CTM-035`, `REQ-CORE-724`..`732`, `REQ-CORE-2190`..`2192`, `T552`, `T553`)

1. **Mandatory Programmer-Visible Guarantee vs Optimization (`ACOMP2-63..69`, `COMPTIME-78..80`)**:
   - `const`, `comptime fn`, `comptime { ... }`, and `comptime` parameters provide a **mandatory compile-time execution guarantee** (`ACOMP2-65`, `COMPTIME-79`): if evaluation cannot complete at compile time, compilation fails with a diagnostic (`AXS-CTM-012`).
   - Conversely, constant folding, constant propagation (`SCCP`), and partial evaluation in `compiler/opt/` (`SPEC-70`, `SPEC-73`) are **opportunistic compiler optimizations** (`ACOMP2-63..64`, `ACOMP2-66`, `COMPTIME-78`): an ordinary function may be constant-folded without becoming a `comptime fn` (`COMPTIME-80`), unused comptime-generated declarations may be dead-code eliminated (`ACOMP2-61`), and generated runtime code is optimized normally (`ACOMP2-62`).
   - Optimizer constant folding, propagation, and branch elimination MUST preserve exact language semantics (`REQ-CTM-035`, `ACOMP2-67..69`): a runtime division by zero or overflow inside a runtime branch that is not reached at runtime must NEVER be turned into a compile-time error by opportunistic folding (`SPEC-70 AXS-OPT-021`).

### AXS-CTM-021 — Comptime Specialization of Generic, Constant & Closure Arguments (`ACOMP2-70..85`, `REQ-CORE-733`..`748`, `T553`)

1. **Semantic Specialization & `if comptime` Branch Elimination (`ACOMP2-69..79`, `REQ-CORE-732..741`)**:
   - When a function is declared with generic type parameters or `comptime` value parameters (`fn process<T, comptime UNROLL: usize>(data: view<[T]>)`), `compiler/sema/specialize.ax` produces a specialized instance keyed by canonical `(TypeArgs, ComptimeArgs)` (`ACOMP2-70`). Each concrete instance undergoes full semantic and MIR verification (`ACOMP2-71`) and emits zero runtime generic metadata (`ACOMP2-72`).
   - Inside a specialized body, `if comptime (cond) { then_branch } else { else_branch }` (and any branch condition depending solely on `comptime` parameters or `const` values) evaluates `cond` at compile time and elides the untaken branch from MIR (`ACOMP2-69`), while preserving all checked-arithmetic, bounds-check, and `Drop` semantics on the remaining runtime paths.
   - Partial evaluation in `compiler/opt/` may further specialize functions over constant call-site arguments (`ACOMP2-77`), constant closure capture environments (`ACOMP2-78`), async state machines (`ACOMP2-79`), and GPU kernels (`ACOMP2-80`), subject to `SpecializationBudget` (`SPEC-73 AXS-INL-021`, `ACOMP2-74..76`) and structural deduplication (`ACOMP2-73`).
2. **Conservative FFI, Unsafe Containment & Source Provenance (`ACOMP2-81..85`, `REQ-CORE-744..748`)**:
   - Partial evaluation treats foreign `extern` calls conservatively (`ACOMP2-81`), never promotes `unsafe` assumptions into safe semantic proofs outside `unsafe` blocks (`ACOMP2-82..83`), and preserves source spans and expansion provenance (`GenProvenanceId`) for diagnostics and debug info (`ACOMP2-84..85`).

### AXS-CTM-022 — Dependency-Tracked Comptime Cache Identity & Parallel Determinism (`ACOMP-44`, `ACOMP2-86..91`, `ACOMP2-95..100`, `COMPTIME-43..47`, `COMPTIME-83..100`, `REQ-CTM-041`, `REQ-CORE-749`..`754`, `REQ-CORE-758`..`763`, `REQ-CORE-2155`..`2159`, `REQ-CORE-2195`..`2212`, `T553`, `T555`)

1. **Semantic Content-Addressed Cache Identity (`ACOMP-44`, `ACOMP2-89..91`, `COMPTIME-43..45`, `COMPTIME-83..87`, `REQ-CTM-041`)**:
   - `compiler/driver` caches comptime evaluation results under a versioned semantic fingerprint `ComptimeCacheKey` (`COMPTIME-83`, `COMPTIME-86`):
     $$\text{ComptimeCacheKey} = H(\text{CompilerSemVer}, \text{TargetTriple}, \text{TargetFeatures}, \text{SafetyProfile}, \text{CalleeMIRHash}, \text{TransitiveDepsHash}, \text{CanonicalArgs}, \text{CapPolicyHash}, \text{ExternalInputsHash})$$
   - Invalidation is strictly content- and dependency-driven, never timestamp-only (`COMPTIME-87`, `ACOMP2-89..91`). Modifying any transitive callee, constant, target layout parameter, capability policy, or declared external input (`env`, embedded file) invalidates dependent cached results incrementally (`COMPTIME-84..85`).
2. **Observational Equivalence Across Cache Hits, Parallel Runs & Evaluator Implementations (`ACOMP2-86..88`, `COMPTIME-46..47`, `COMPTIME-94..100`)**:
   - Independent pure comptime evaluations may execute in parallel (`ACOMP2-86`, `COMPTIME-46`), while any ordered external side effects serialize deterministically (`ACOMP2-88`).
   - A cache hit, a fresh single-threaded MIR interpreter evaluation, a parallel evaluation, or an optimized ComptimeVM run MUST produce byte-identical lifted values and diagnostics (`ACOMP-44`, `ACOMP2-87`, `COMPTIME-43`, `COMPTIME-47`, `COMPTIME-96..100`, `REQ-CTM-041`). Tooling and AI agents may inspect comptime traces (`COMPTIME-94`, `ACOMP2-98`) but can never override semantic verification (`COMPTIME-95`).

---

## 4. Global Semantics: `const` vs `static` vs `TLS`, Initialization & Section Materialization (`AXS-CTM-030`..`034`)

### AXS-CTM-030 — Semantic Triad: `const` (Compile-Time Value) vs `static` (Module/Program Storage) vs `TLS` (Execution-Context Storage) (`AGLOBAL-20..30`, `AGLOBAL-40..43`, `AGLOBAL-74..77`, `AGLOBAL-149`, `REQ-CTM-015`, `REQ-CORE-697`, `REQ-CORE-2214`..`2225`, `REQ-CORE-2235`..`2238`, `REQ-CORE-2269`..`2272`, `REQ-CORE-2344`, `T550`, `T552`, `T554`)

1. **`const`: Compile-Time Semantic Value Without Mandatory Storage Identity (`AGLOBAL-20..22`, `AGLOBAL-117`, `REQ-CTM-015`, `REQ-CORE-697`, `REQ-CORE-2214..2217`)**:
   - `const NAME: T = expr` denotes a **compile-time value**, not a runtime variable (`AGLOBAL-20`, `REQ-CTM-015`). It requires no runtime storage by default (`AGLOBAL-21`) and is substituted directly as a `ConstValue` at use sites. When ABI or a slice/aggregate `view` requires memory backing, the compiler materializes the value into read-only `.rdata` (`AGLOBAL-22`) and may freely deduplicate or merge identical constants (`AGLOBAL-117`).
2. **`static`: Module/Program-Lifetime Storage With Explicit Identity (`AGLOBAL-23..30`, `AGLOBAL-40..43`, `AGLOBAL-160..161`, `REQ-CORE-2218..2225`, `REQ-CORE-2235..2238`)**:
   - `static [mut] NAME: T = expr` denotes a **storage location** with module/program lifetime (`AGLOBAL-23`, `AGLOBAL-70`, `AGLOBAL-120`), distinct from `const` value identity (`AGLOBAL-24`) and distinct from lexical locals (`AGLOBAL-40`).
   - Static storage requires zero heap allocation, zero garbage collection, and zero monolithic runtime (`AGLOBAL-25..27`, `AGLOBAL-118`, `AGLOBAL-160..161`).
   - Layout is compiler-controlled unless `@repr(C)` / `@abi(stable)` / `@align(N)` is specified (`AGLOBAL-28`). When address identity is observable (`static_addr(S)`, `address_of(S)`, `@export`, `@used`, `@at`), the unique storage address is preserved (`AGLOBAL-29`, `AGLOBAL-115..116`); when an immutable `static` has no observable address use, reads may be folded into constants (`AGLOBAL-30`, `AGLOBAL-114`).
   - In Core v1.0, `static` declarations live at module/package scope (`AGLOBAL-41`); Core v1.0 does not require function-local `static` syntax (`AGLOBAL-42`), as lazy state is expressed via explicit `OnceCell<T>` / `Lazy<T>` library abstractions (`AGLOBAL-43`).
3. **`@thread_local static` (`TLS`): Execution-Context Storage (`AGLOBAL-74..77`, `AGLOBAL-162`, `SPEC-32 AXS-SYNC-020..022`, `REQ-CORE-2269..2272`, `REQ-CORE-2357`)**:
   - `@thread_local static NAME: T = expr` denotes thread-local storage where each OS thread receives an isolated storage instance (`AGLOBAL-74..77`) without requiring a monolithic runtime (`AGLOBAL-162`). The semantic distinction among `const`, `static`, and `TLS` is preserved through MIR (`AGLOBAL-149`).

### AXS-CTM-031 — Global Ownership, Capabilities, Synchronization & Security Contracts (`AGLOBAL-31..39`, `AGLOBAL-78..82`, `AGLOBAL-131..135`, `AGLOBAL-158`, `REQ-CORE-2226`..`2234`, `REQ-CORE-2273`..`2277`, `REQ-CORE-2326`..`2330`, `REQ-CORE-2353`, `T552`, `T553`)

1. **Global Ownership vs Lexical Ownership (`AGLOBAL-37..39`, `REQ-CORE-2232..2234`)**:
   - Global ownership is permanent for the module/program lifetime (`AGLOBAL-39`): a `!Copy` value owned by a `static` or `@thread_local static` item can NEVER be moved out of static storage (`AGLOBAL-38`, rejected with `AX_CTM_STATIC_MOVE_FORBIDDEN` / `AX_MOVE_USE_AFTER_MOVE`). Replacing an inner optional resource uses explicit `Option.take` inside a synchronized guard (`tasks/0514 §172–174`).
   - An immutable `static S: T` where `T: Share` may produce a `'static` read capability `view<T>` (`AGLOBAL-37`, `REQ-CORE-2232`).
2. **Synchronized Global Mutation & No Safe Data Races (`AGLOBAL-31..36`, `AGLOBAL-158`, `REQ-CORE-2226..2231`, `REQ-CORE-2353`)**:
   - Mutable `static mut` state is not implicitly safe for concurrent mutation (`AGLOBAL-31`): accessing `static mut` requires `unsafe` (`AX_UNSAFE_REQUIRED` / `AX_CONC_UNSYNC_STATIC`, `SPEC-30 AXS-CONC-034`) and still obeys the Axiom memory model (`AGLOBAL-32`).
   - Safe mutable global state requires an explicit synchronization primitive (`Atomic<T>`, `Mutex<T>`, `RwLock<T>`, `OnceCell<T>`, `AGLOBAL-33..35`, `AGLOBAL-158`, `AGLOBAL-163`). `Atomic<T>` obeys `SPEC-31` ordering rules (`AGLOBAL-34`) and never implicitly converts to `mut_view<T>` (`AGLOBAL-36`, `AX_CONC_ATOMIC_MUT_VIEW`).
3. **TLS Containment & Global Security Rules (`AGLOBAL-78..82`, `AGLOBAL-131..135`, `REQ-CORE-2273..2277`, `REQ-CORE-2326..2330`)**:
   - TLS access obeys ordinary ownership and capability rules (`AGLOBAL-78`); a `view<T>` / `mut_view<T>` or raw address into TLS cannot escape the active thread callback or become a cross-thread capability (`AGLOBAL-79..80`, `AX_CONC_TLS_ESCAPE`), and placing a type in TLS does not make it `Send` or `Share` (`AGLOBAL-81..82`).
   - Static values serialize by value, never by runtime address (`AGLOBAL-131..132`), and cryptographic secrets in global storage remain governed by `Secret<T>` and `@constant_time` (`SPEC-53`, `AGLOBAL-133..135`).

### AXS-CTM-032 — Deterministic Constant Initialization, No Hidden Constructors & Explicit Lazy/Startup Contracts (`AGLOBAL-44..73`, `AGLOBAL-83..88`, `AGLOBAL-136..141`, `AGLOBAL-159`, `AGLOBAL-164`, `REQ-CORE-2239`..`2268`, `REQ-CORE-2278`..`2283`, `REQ-CORE-2331`..`2336`, `REQ-CORE-2354`, `REQ-CORE-2359`, `T552`)

1. **Mandatory Compile-Time Constant Initialization for Core `static` & `TLS` (`AGLOBAL-44..50`, `AGLOBAL-83..88`, `AGLOBAL-136..141`, `REQ-CORE-2239..2245`)**:
   - Every `const`, `static`, and `@thread_local static` declaration requires a compile-time-valid initializer (`AGLOBAL-44`, `AGLOBAL-83`) that obeys comptime capability restrictions (`AGLOBAL-47..49`) and materializes directly into binary sections without runtime startup code (`AGLOBAL-45..46`). Non-constant runtime initializers are rejected with `AX_CTM_NON_CONST_STATIC_INIT` identifying the unsupported initialization mechanism (`AGLOBAL-139..141`).
   - Evaluation order across `const` and `static` initializers is determined strictly by the item dependency DAG, never by source-file order or linker input order (`AGLOBAL-58..59`, `AGLOBAL-159`); cycles emit `AX_CTM_CYCLE`. External comptime inputs used during static initialization are tracked in the build dependency graph (`AGLOBAL-136..138`).
2. **No Implicit Dynamic Global Constructors or Process-Exit Destructors (`AGLOBAL-50..73`, `AGLOBAL-85..86`, `AGLOBAL-164`, `REQ-CORE-2245..2268`, `REQ-CORE-2359`)**:
   - Core Axiom has **no hidden C++-style pre-`main` dynamic constructors** (`AGLOBAL-50`, `AGLOBAL-56..57`, `AGLOBAL-64`, `AGLOBAL-85`) and **no mandatory process-exit `atexit` static destructors** (`AGLOBAL-65..66`, `AGLOBAL-69`, `AGLOBAL-72..73`, `AGLOBAL-86`, `AGLOBAL-164`).
   - Runtime-dependent global state uses explicit `Once<T>` / `OnceCell<T>` / `Lazy<T>` library types with defined concurrency, failure, and cycle semantics (`AGLOBAL-51..55`) or explicit deterministic startup/shutdown hooks (`AGLOBAL-60..63`, `AGLOBAL-67..71`).

### AXS-CTM-033 — Global Effects, Aliasing, Foreign Statics, Dynamic-Library Lifetimes & LTO Roots (`AGLOBAL-89..108`, `AGLOBAL-119..130`, `REQ-CORE-2284`..`2303`, `REQ-CORE-2314`..`2325`, `T553`, `T554`)

1. **Global Effect, Alias, Concurrency & LTO Rules (`AGLOBAL-91..108`, `REQ-CORE-2286..2303`)**:
   - Global reads and writes participate in effect, alias (`SPEC-71`), and concurrency (`SPEC-30`) analysis (`AGLOBAL-99..101`). `volatile` (`AGLOBAL-95`) and `Atomic<T>` (`AGLOBAL-96`) globals enforce hardware/compiler ordering barriers, whereas ordinary global accesses are not implicit compiler fences but cannot be reordered across synchronization barriers (`AGLOBAL-97..98`).
   - Foreign `extern` statics require explicit FFI representation contracts and act as conservative effect/synchronization boundaries (`AGLOBAL-91..94`).
   - LTO optimizes globals only when closed-world observability is proven (`AGLOBAL-102`), keeping `@export`, `@abi(stable)`, `@used`, `@at`, and reflection-retained globals as live roots with stable symbol/ABI identity (`AGLOBAL-103..108`).
2. **Module Lifetimes & Multi-Domain Storage (`AGLOBAL-89..90`, `AGLOBAL-119..130`, `REQ-CORE-2284..2285`, `REQ-CORE-2314..2325`)**:
   - Dynamic-library static and TLS storage is scoped to module lifetime rather than process lifetime, and unloading a module cannot leave dangling safe capabilities (`AGLOBAL-89..90`, `AGLOBAL-119..122`).
   - Freestanding/kernel profiles support static storage without a hosted runtime (`AGLOBAL-123..125`), WASM global lowering keeps semantic identity distinct from raw linear-memory offsets (`AGLOBAL-126..127`), and CPU static storage never implicitly becomes GPU device storage (`AGLOBAL-128..130`).

### AXS-CTM-034 — Native Materialization of Lifted Comptime Tables & `.rdata` / `.data` / `.bss` / `.tls` Emission (`AGLOBAL-109..118`, `AGLOBAL-142..157`, `AGLOBAL-165`, `COMPTIME-24..25`, `REQ-CORE-2304`..`2313`, `REQ-CORE-2337`..`2352`, `REQ-CORE-2360`, `T554`, `T555`)

1. **Deterministic Section Placement & Relocation Lowering (`AGLOBAL-109..117`, `AGLOBAL-144..151`, `T554`)**:
   - `compiler/lir`, `compiler/target/x64`, and `compiler/obj` materialize comptime-computed aggregates, lookup tables, and promoted static slices (`view<[T]>`, `Str`) into COFF/PE sections with `Addr64` internal pointer relocations, preserving global semantics independently of optimization level, section placement, linker, or allocator (`AGLOBAL-109..110`, `AGLOBAL-144..150`, `AGLOBAL-165`):
     - **`.rdata`**: Materialized `const` allocations (deduplicable, `AGLOBAL-117`) and immutable `static` items (`AGLOBAL-111`, preserving address identity when observable, `AGLOBAL-115..116`);
     - **`.bss`**: Zero-initialized mutable or interior-mutable `static` items (`AGLOBAL-112`);
     - **`.data`**: Non-zero-initialized mutable or interior-mutable `static` items;
     - **`.tls`**: `@thread_local static` templates (`AGLOBAL-113`).
   - Native binaries emitted from comptime-heavy programs contain **zero** comptime interpreter symbols or runtime VM overhead (`COMPTIME-24..25`) and expose global storage facts to debuggers and AI inspection tools without allowing tooling to override safety verification (`AGLOBAL-142..143`, `AGLOBAL-151..157`).

---

## 5. Diagnostic Taxonomy, Canonical Examples & Traceability (`AXS-CTM-050`..`053`)

### AXS-CTM-050 — Comptime & Global Initialization Diagnostic Codes (`spec/diagnostics.md`, `T551`–`T554`)

In addition to `AX_CONST_OVERFLOW`, `AX_CONST_DIV_ZERO`, and `AX_CONST_SHIFT_RANGE` (`spec/diagnostics.md §11`), self-hosted `axiomc` (`compiler/diag/code.ax`) defines the `CTM` diagnostic family (`AX_CTM_*`):

| Code | Sev | Task | Condition |
|---|---|---|---|
| `AX_CTM_RUNTIME_CALL_FORBIDDEN` | E | T551 | `comptime fn` called from a runtime expression context (`AXS-CTM-002`) |
| `AX_CTM_NON_CONST_CAPTURE` | E | T551 | `comptime { ... }` block or `const`/`static` initializer references a runtime local or non-`comptime` parameter (`AXS-CTM-002`) |
| `AX_CTM_CAPABILITY_DENIED` | E | T551 | `comptime` code invokes ambient OS filesystem, network, environment (`env`), clock (`time`), process, or foreign `extern` FFI without an explicit granted comptime capability (`AXS-CTM-003`, `REQ-CTM-044`, `REQ-CTM-047`) |
| `AX_CTM_RESOURCE_ESCAPE` | E | T551/T552 | unpromoted comptime heap handle (`Vec`, `String`, `Box`), `mut_view`, `view` to a dead comptime local, raw comptime pointer, or authority token escapes across the comptime-to-runtime value lifting barrier (`AXS-CTM-011`, `REQ-CTM-002`, `REQ-CTM-004..006`, `REQ-CTM-009`, `REQ-CTM-011`) |
| `AX_CTM_CYCLE` | E | T552 | cyclic evaluation dependency among `const`, `static`, or `comptime` items (`AXS-CTM-012`, `AXS-CTM-032`; supersedes/aliases `AX_CONST_CYCLE`) |
| `AX_CTM_STEP_LIMIT` | E | T552 | comptime evaluation exceeded the step limit or call-depth budget (`AXS-CTM-012`; supersedes/aliases `AX_CONST_EVAL_LIMIT`) |
| `AX_CTM_MEM_LIMIT` | E | T552 | comptime evaluation exceeded the compiler arena memory budget (`AXS-CTM-012`) |
| `AX_CTM_PANIC` | E | T552 | explicit `panic(...)` or failed `assert(...)` executed during comptime evaluation (`AXS-CTM-012`) |
| `AX_CTM_NON_CONST_STATIC_INIT` | E | T551/T552 | `const`, `static`, or `@thread_local static` initialized with a runtime-only expression (`AXS-CTM-032`, `AGLOBAL-139..141`) |
| `AX_CTM_STATIC_MOVE_FORBIDDEN` | E | T551/T552 | moving a `!Copy` value out of a `static` or `@thread_local static` storage place (`AXS-CTM-031`, `AGLOBAL-38`) |

### AXS-CTM-051 — Canonical Positive & Negative Examples (`axiom-syntax`: `=` and `.` only)

```axiom
module demo.comptime_table

// Positive: comptime fn using transient heap/loops, deterministic Drop, and array value lifting
comptime fn build_crc_table() -> [4]u32 {
    let mut table: [4]u32 = [0u32, 0u32, 0u32, 0u32]
    let mut i: usize = 0
    while i < 4 {
        table[i] = (i as u32) * 0x04C1_1DB7u32
        i = i + 1
    }
    table
}

pub const CRC_CONST: [4]u32 = build_crc_table()
pub static CRC_STATIC: [4]u32 = build_crc_table()

// Positive: comptime parameter specialization & dead-branch elimination
pub fn scale_value<comptime MODE: u32>(x: i32) -> i32 {
    if comptime (MODE == 0u32) {
        0
    } else {
        x * (MODE as i32)
    }
}

// Negative examples (rejected at compile time):
// comptime fn bad_io() -> i32 {
//     let h = host.open(null<u8>(), 0, 0) //~ ERROR AX_CTM_CAPABILITY_DENIED
//     h as i32
// }
//
// comptime fn bad_escape() -> *const i32 {
//     let local_val: i32 = 42
//     unsafe { address_of(local_val) }    //~ ERROR AX_CTM_RESOURCE_ESCAPE
// }
```

### AXS-CTM-052 — E14.1 Conformance Verification Matrix (`T551`–`T555`)

| Test ID | Verification Focus | Expected Outcome | Task |
|---|---|---|---|
| `CTM-T01` | `comptime fn`, `comptime { ... }` blocks, and `[T, comptime N: usize]` const generics | Compiles and evaluates identically in `--interp` and native x86-64 | T551, T555 |
| `CTM-T02` | Calling `comptime fn` at runtime or capturing runtime local in `comptime { ... }` | Rejected with `AX_CTM_RUNTIME_CALL_FORBIDDEN` / `AX_CTM_NON_CONST_CAPTURE` | T551, T555 |
| `CTM-T03` | Ambient filesystem, network, `env`, `time`, or FFI call inside `comptime` (even inside `unsafe`) | Rejected with `AX_CTM_CAPABILITY_DENIED` | T551, T555 |
| `CTM-T04` | Transient comptime `Vec`/`String`/`Box` with `impl Drop` | Deterministic reverse-order `Drop` runs at comptime before value lifting | T552, T555 |
| `CTM-T05` | Escaping comptime `Box`/`Vec`, local `view`, `mut_view`, or raw comptime pointer into runtime | Rejected with `AX_CTM_RESOURCE_ESCAPE` | T552, T555 |
| `CTM-T06` | `const`/`static` cycle, comptime `panic`/`assert(false)`, and step/memory budget exhaustion | Rejected with `AX_CTM_CYCLE`, `AX_CTM_PANIC`, `AX_CTM_STEP_LIMIT`, `AX_CTM_MEM_LIMIT` (never ICE) | T552, T555 |
| `CTM-T07` | Partial evaluation of `comptime` parameters and `if comptime` branch elimination | Untaken branch eliminated in MIR; runtime traps on taken paths preserved | T553, T555 |
| `CTM-T08` | Dependency-tracked `ComptimeCacheKey` invalidation on source, target, or external input change | Cache hit matches fresh run 100%; input mutation invalidates cache | T553, T555 |
| `CTM-T09` | Native materialization of lifted comptime structs/enums/arrays/slices into `.rdata`, `.data`, `.bss` | Zero comptime VM symbols in native PE; `static` address identity preserved | T554, T555 |

### AXS-CTM-053 — Requirement Coverage Traceability (`T550`)

- **Comptime Ownership, Deterministic Cleanup, Sandbox & External Inputs (`REQ-CTM-*`)**:
  - `REQ-CTM-001`, `REQ-CTM-003`, `REQ-CTM-016`, `REQ-CTM-036`: `AXS-CTM-001`, `AXS-CTM-010`.
  - `REQ-CTM-002`, `REQ-CTM-004`, `REQ-CTM-005`, `REQ-CTM-006`, `REQ-CTM-009`, `REQ-CTM-011`: `AXS-CTM-011`.
  - `REQ-CTM-007`, `REQ-CTM-017`, `REQ-CTM-018`, `REQ-CTM-029`, `REQ-CTM-030`, `REQ-CTM-031`, `REQ-CTM-032`, `REQ-CTM-033`, `REQ-CTM-034`, `REQ-CTM-038`, `REQ-CTM-044`, `REQ-CTM-047`: `AXS-CTM-003`.
  - `REQ-CTM-008`, `REQ-CTM-010`, `REQ-CTM-012`, `REQ-CTM-013`, `REQ-CTM-014`, `REQ-CTM-037`, `REQ-CTM-042`: `AXS-CTM-001`, `AXS-CTM-002`.
  - `REQ-CTM-015`: `AXS-CTM-001`, `AXS-CTM-030`.
  - `REQ-CTM-023`, `REQ-CTM-024`: `AXS-CTM-012`.
  - `REQ-CTM-025`, `REQ-CTM-026`, `REQ-CTM-027`, `REQ-CTM-028`: `AXS-CTM-004`.
  - `REQ-CTM-035`, `REQ-CTM-041`: `AXS-CTM-020`, `AXS-CTM-022`.
  - `REQ-CTM-046`: `AXS-CTM-013`.
- **Comptime 2.0 Frozen Invariants (`ACOMP2-20..100` / `REQ-CORE-683`..`763`)**:
  - `REQ-CORE-683`..`689`, `REQ-CORE-697`: `AXS-CTM-001`.
  - `REQ-CORE-690`..`694`: `AXS-CTM-003`.
  - `REQ-CORE-695`..`696`: `AXS-CTM-010`, `AXS-CTM-011`.
  - `REQ-CORE-698`..`716`: `AXS-CTM-002`, `AXS-CTM-004`.
  - `REQ-CORE-717`..`723`: `AXS-CTM-010`, `AXS-CTM-011`, `AXS-CTM-012`.
  - `REQ-CORE-724`..`763`: `AXS-CTM-013`, `AXS-CTM-020`, `AXS-CTM-021`, `AXS-CTM-022`.
- **Bootstrap-250 Comptime Execution (`COMPTIME-20..100` / `REQ-CORE-2130`..`2213`)**:
  - `REQ-CORE-2130`..`2142`: `AXS-CTM-001`, `AXS-CTM-010`.
  - `REQ-CORE-2150`..`2169`: `AXS-CTM-003`, `AXS-CTM-010`, `AXS-CTM-011`, `AXS-CTM-012`, `AXS-CTM-022`.
  - `REQ-CORE-2180`..`2213`: `AXS-CTM-002`, `AXS-CTM-003`, `AXS-CTM-004`, `AXS-CTM-011`, `AXS-CTM-013`, `AXS-CTM-020`, `AXS-CTM-022`.
- **Global Storage, `const` vs `static` vs `TLS` (`AGLOBAL-20..165` / `REQ-CORE-2214`..`2360`)**:
  - `REQ-CORE-2214`..`2225`, `REQ-CORE-2235`..`2238`: `AXS-CTM-030`.
  - `REQ-CORE-2226`..`2234`: `AXS-CTM-031`.
  - `REQ-CORE-2239`..`2243`: `AXS-CTM-003`, `AXS-CTM-032`.
  - `REQ-CORE-2244`..`2360`: `AXS-CTM-030`..`AXS-CTM-034`.
