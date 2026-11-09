# ADR-0039 — Integration of Red-Team Refined Architecture: Systems, Security, Web, Zero-Day Defense & OpenGL Expansion (P12–P22)

Status: accepted (2026-11-09, architect; owner-delegated decision)

## Tóm tắt
- Tiếp nối đợt mở rộng GPU (ADR-0038) và 6 báo cáo thẩm định đối kháng chuyên sâu (Red-Team Adversarial Reviews 1–6), kiến trúc sư hợp nhất toàn bộ 13 đề xuất kiến trúc đã qua tinh chỉnh vào lộ trình chuẩn của Axiom:
  1. **Hệ số học & Comptime (P12, P14)**: Bổ sung kiểu vô hướng `f16` (IEEE-754) vào thang thăng cấp số học (`I < f16 < f32 < f64`) hạ cấp qua `F16C`/SSE2; bổ sung kiểu `bf16` lưu trữ/chuyển đổi và SIMD dot-product thuần túy (không hỗ trợ toán tử số học vô hướng `+ - * /`); loại bỏ AVX-512 EVEX khỏi P12; nhúng tài nguyên an toàn tại compile-time (`@embed_bytes`, `@embed_str`) có kiểm tra UTF-8, giới hạn trong thư mục gói, băm BLAKE3 vào `QueryDb` của P18, giới hạn 64 MiB; hỗ trợ async generators (`async gen fn` -> `AsyncIterator`) với cú pháp `while let Option.Some(x) = stream.next().await`, cấm `view`/`mut_view` xuyên qua `.await`/`yield`, quản lý drop glue hủy coroutine phức hợp.
  2. **Bảo mật hệ thống & Phòng thủ khai thác nhị phân (P13, P14, P21)**: Chuẩn hóa cú pháp `unsafe asm(...)` trên HIR/MIR/LIR, kiểm tra clobber/ownership, sinh mã x86-64 và bẫy tất định trên `--interp`; khởi tạo 0 tất định cho toàn bộ alignment padding bytes trong struct `@repr(C)` / `@repr(packed)` chống rò rỉ ASLR; tích hợp khiên bảo vệ nhị phân `--hardened` (Intel CET `ENDBR64` + PE GuardFlags, 32-bit KCFI signature hash check `--cfi=type-hash`, `--stack-protector=strong` canaries, stack-clash guard 4 KiB, `std.security.spectre_index`); bố trí vtables `dyn Trait` vào `.rdata` chỉ đọc với kiểm tra 32-bit `trait_id_hash`; bộ cấp phát an toàn `IsoHeap` / `HardenedAllocator` phân vùng theo `TypeId(T)`, zero-on-free, 64-slot quarantine ring, XOR freelist cookies, guard pages.
  3. **Nền tảng mục tiêu & FFI Đa ngữ (P16, P20, P21)**: Bổ sung AArch64 NEON (`LirType.V128`), ARM64 `unsafe asm(...)` và ARM64 PAC+BTI (`+pauth`, `+bti`); lớp binding Objective-C an toàn `std.ffi.objc` với trampoline exact-cast `objc_msgSend` AAPCS64, `ObjcStrong<T>`, `AutoreleasePool` scoped, rào cản ngoại lệ FFI, mock `libobjc` DLL trên Windows; WASM `SIMD128` + `std.ffi.wasm_js` (`@wasm_import`/`@wasm_export`, `JsValue`, slice UTF-8, `--emit-ts-defs`, `.wit`); bộ tiền xử lý C99/C11 thuần Axiom và `axiom bindgen <header.h>` từ chối C++; bộ xuất SDK đa ngữ `axiom build --export-sdk` (C99, Python ctypes, Swift, Kotlin JNI, TypeScript .d.ts/WASM) trong P20; bộ reactor bất đồng bộ đa nền tảng trong P21 (`SPEC-129`: Linux `io_uring` + `epoll` có fallback container/seccomp và chống DMA write-after-free `IoOpState.CancellingZombie`, macOS/iOS `kqueue`).
  4. **Fuzzing & Quét tĩnh lỗ hổng 0-Day C++ (P17)**: Fuzzing có hướng dẫn độ phủ và nhận biết cấu trúc (`SPEC-99`: coordinator + worker đa tiến trình chia sẻ 64 KiB coverage map, `@derive(Arbitrary)` qua reflection P14, `axiom test --fuzz`, phát lại regression test `< 1.0s`); Quét tĩnh lỗ hổng 0-Day C++ (`SPEC-151`: abstract interpretation MIR $O(\text{CFG})$, bắt 10 mẫu lỗ hổng 0-day Project Zero/MSRC gồm allocation overflow, narrowing cast, static UAF/double-free, view pointer escape, union type confusion, padding infoleak, TOCTOU race, path traversal, command injection, kiểm tra dùng sai nguyên thủy crypto cổ điển `AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`, phát sinh định dạng chuẩn SARIF 2.1).
  5. **Mạng & Framework Web FastAPI-Grade (P21)**: Hoàn thiện thư viện regex tuyến tính không backtracking `std.regex`; nguyên thủy mật mã WebPKI (`AES-128/256-GCM`, `ECDSA P-256`, `RSA-PSS`); giao thức TLS 1.3 thuần Axiom + HTTP/1.1 + HTTP/2 chống CVE-2023-44487 Rapid Reset và CONTINUATION flood; thư viện web hiện đại `std.web` (`SPEC-152`: radix router, dependency injection `FromRequest`, kiểm tra chữ ký handler qua `comptime` `TypeInfo` không dùng RTTI, `@derive(Validate)` RFC 9457 `422`, OpenAPI 3.1 comptime `/openapi.json`, Swagger UI offline qua `@embed_str`, phòng thủ Slowloris/DoS/path-traversal, streaming Multipart, SSE và WebSocket).
  6. **Đồ họa tương thích OpenGL 4.5+ & GLES 3.1+ (P22)**: Bổ sung Epic E22.9 (`SPEC-138`: sinh mã `AGIR -> GLSL 450 / ESSL 310`, chuẩn hóa clip-space Z `[0, 1]` và Y-flip; driver `std/sys/gpu/opengl` WGL/EGL/GLX tuân thủ boundary `0846 §216`, tách biệt thread-affinity bằng hàng đợi submit replay với Direct State Access hoặc shadow state tracker; kiểm thử headless FBO kết hợp bộ rasterizer CPU).
  7. **Hệ mật mã đầy đủ, Mã hóa thời gian thực & Cách ly Crypto kế thừa (P21)**: Bổ sung `SHA-384`, `SHA-3` (`Sha3_256`, `Sha3_512`, `Shake128`, `Shake256`, `Keccak256`), băm mật khẩu `Argon2id` & `PBKDF2` (`ZeroizeOnDrop`, chặn DoS bộ nhớ), `AES-CTR`, `AES-CBC` unpad PKCS#7 thời gian hằng số, RFC 3394 `AesKw`, mã hóa không rẽ nhánh `std.encoding.{base64, hex}`; đồng thời cách ly các thuật toán cũ vào không gian tên riêng `std.crypto.legacy` (`Sha1`, `HmacSha1` cho RFC 6455 WebSocket / RFC 6238 TOTP, `Md5`, `Des`/`TripleDes` bit-sliced thời gian hằng số).

---

## 1. Context & Adversarial Findings

Following the acceptance of GPU graphics and platform expansions in ADR-0038, a comprehensive set of twelve architectural proposals was submitted to elevate Axiom into an industrial-grade, secure, polyglot, web-capable systems programming language. To ensure maximum architectural integrity, zero regression on self-hosting timelines, and strict adherence to language invariants, five independent Red-Team critics subjected all twelve proposals to adversarial audits:

1. **Critic 1 (Language, Ownership, IR, Compiler Architecture & Self-Host Risk)** evaluated Proposals #1 (`f16`/`bf16`), #3 (Inline ASM & CFI), #4 (Async Generators & `@embed_*`), and #7 (`axiom dev --hot`).
2. **Critic 2 (Systems, Async I/O, FFI, Fuzzing, Networking/Crypto & SDK Export)** evaluated Proposals #2 (Cross-OS Reactors), #5 (ObjC, WASM JS, Bindgen), #6 (Fuzzing), #8 (SIMD JSON, TLS 1.3, HTTP/2, Linear Regex), and #9 (Polyglot SDK Exporter).
3. **Critic 3 (Web Framework, Type Extractors, HTTPS & OpenAPI)** evaluated Proposal #10 (FastAPI-Grade `std.web`).
4. **Critic 4 (Zero-Day Vulnerability Research & Binary Exploit Mitigations)** evaluated Proposal #11 (C++ Zero-Day Static Scanner & Hardened Exploit Shield).
5. **Critic 5 (Graphics Architecture & Hardware Conformance)** evaluated Proposal #12 (OpenGL 4.5+ / OpenGL ES 3.1+ Compatibility Backend per `0846 §216`).
6. **Critic 6 (Cryptographic Integrity, Padding Safety & Legacy Hash Isolation)** evaluated Proposal #13 (Complete `std.crypto` Suite, Constant-Time `Base64`/`Hex`, and Quarantined `std.crypto.legacy` for RFC 6455/6238 compatibility).

The critics identified crucial pitfalls in naive implementations:
- Incompatible promotion geometries between `f16` and `bf16` under `REQ-OWNER-007` (since `bf16` has no scalar arithmetic instructions on standard CPUs).
- Register-allocator and ABI explosion if full AVX-512 EVEX/ZMM were introduced in P12 rather than legalized to 2x `v256`.
- Illegal Rust bang-macro leak (`asm!(...)`) violating Axiom's pure canonical syntax (`unsafe asm(...)`).
- Circular dependencies if cross-OS async reactors (`io_uring`/`kqueue`) were placed in P11 before non-Windows targets exist in P16.
- Kernel DMA write-after-free hazards in `io_uring` upon premature `Future` drop.
- Inability to establish real-world WebPKI HTTPS connections if TLS 1.3 lacked ECDSA P-256 and AES-GCM primitives.
- DoS and Rapid Reset vulnerabilities (CVE-2023-44487) in HTTP/2.
- SMT solver bloat risking the `< 100 ms` incremental compilation contract if static security analysis relied on heavyweight formal verifiers instead of fast $O(\text{CFG})$ abstract interpretation.
- Global mutable state and thread-affinity crashes if an OpenGL compatibility layer was architected around legacy C++ `glBind*` paradigms rather than modern explicit command-replay.

---

## 2. Architectural Decisions

### Pillar 1 — Language, Numeric Types, Asset Embedding & Coroutines (P12, P14)
1. **IEEE-754 `f16` & Storage/SIMD `bf16` (`P12` `E12.2`, `T480`)**:
   - `f16` enters the numeric promotion lattice: `i8/u8 < i16/u16 < i32/u32 < i64/u64/isize/usize < f16 < f32 < f64`.
   - On x86-64 without native FP16 execution units, `f16` arithmetic promotes to `f32` (via `F16C` `vcvtph2ps` or bit-exact software emulation), executes scalar SSE2 operations, and converts back (`vcvtps2ph`).
   - `bf16` (Bfloat16) is defined strictly as an opaque storage, conversion (`to_f32()`, `from_f32()`, `to_bits()`, `from_bits()`), and SIMD dot-product type (`std.simd.dot_bf16`). Scalar arithmetic operators (`+`, `-`, `*`, `/`) on `bf16` are explicitly rejected at type-check (`AX_TYPE_BF16_NO_ARITHMETIC`) to prevent ill-defined lattice joins.
   - AVX-512 EVEX vector registers are kept out of P12; 512-bit vector types are legalized into paired 256-bit operations.

2. **Sandboxed Compile-Time Asset Embedding (`P14` `E14.1`, `T573`)**:
   - Compile-time intrinsics `@embed_bytes("path")` -> `view<u8>` and `@embed_str("path")` -> `view<str>` embed static assets into `.rdata`.
   - Enforce strict confinement within the package root; reject directory traversal containing `..` or symlink escapes (`AX_CONST_EMBED_PATH_TRAVERSAL`).
   - `@embed_str` verifies UTF-8 compliance during compile-time evaluation (`AX_CONST_EMBED_INVALID_UTF8`).
   - Assets are tracked in `CompilerDB` (`P18`) via BLAKE3 hashes for hermetic incremental invalidation, with a 64 MiB default file size limit (`AX_CONST_EMBED_TOO_LARGE`).

3. **Async Generators & Unified Coroutine Lowering (`P14` `E14.3`, `T574`)**:
   - Enable `async gen fn name(...) -> YieldType` yielding values via `yield expr` and consumed through canonical syntax:
     ```axiom
     while let Option.Some(item) = stream.next().await {
         // handle item
     }
     ```
   - Unified coroutine MIR state machine lowering prohibits holding `view` or `mut_view` capabilities across yield points or await suspension boundaries (`AX_CAP_CROSS_SUSPENSION_VIEW`).
   - Per-state composite cancellation `Drop` glue ensures all in-flight resources and generator frame places are cleanly finalized if an `AsyncIterator` is dropped prematurely.

---

### Pillar 2 — Low-Level Systems, Inline Assembly & Exploit Shield (P13, P14, P21)
1. **Canonical Typed Inline Assembly (`P13` `E13.1`, `T534`)**:
   - Syntax: `unsafe asm("template", in("reg") val, out("reg") res, clobbers("flags", "memory"))`.
   - Lowered across HIR, MIR (`MirStatement.InlineAsm`), and LIR (`LirInst.InlineAsm`) with full liveness and register-clobber tracking.
   - Evaluation under `--interp` traps with deterministic diagnostic `AX_VERIFY_INLINE_ASM_IN_ORACLE`.

2. **ASLR Padding Infoleak Elimination (`P13` `E13.2`, `T507`/`T508`/`T535`)**:
   - All `@repr(C)` and `@repr(packed)` struct constructors deterministically zero-initialize all alignment padding bytes before populating fields, preventing kernel or IPC infoleaks across foreign boundaries.

3. **Binary Exploit Mitigations Shield (`--hardened`) (`P13` `E13.4`, `P14` `E14.4`, `P21` `E21.9`)**:
   - **`P13` (`T535`)**:
     * Intel CET: Emit `ENDBR64` landing pads on all indirect call targets and set PE `IMAGE_GUARD_CF_INSTRUMENTED` in headers.
     * Fine-grained 32-bit KCFI signature check (`--cfi=type-hash`): Call sites hash parameter/return types and emit a branch-trap prefix verifying the callee's pre-amble hash word.
     * `--stack-protector=strong` canary insertion on functions with stack buffers.
     * 4 KiB page-probing stack-clash protection (`__chkstk`).
     * `std.security.spectre_index(idx, len)` branchless speculation mask barrier.
   - **`P14` (`T567`)**:
     * `dyn Trait` vtables are placed into read-only `.rdata` bounded by linker symbols `__ax_vtables_start` and `__ax_vtables_end`. Indirect dynamic calls verify that the target vtable address falls strictly within this range and matches the expected 32-bit `trait_id_hash`.
   - **`P21` (`T939`)**:
     * Production hardened allocator `HardenedAllocator` (`IsoHeap`): Segregates allocations into distinct memory pools by compile-time `TypeId(T)`, zeroes memory upon deallocation, uses a 64-slot FIFO quarantine ring, XORs freelist pointers with random CSPRNG cookies, and places guard pages adjacent to heap slabs.

---

### Pillar 3 — Target Architecture & Multi-Platform Runtime (P16, P21)
1. **AArch64 NEON, ARM64 ASM & PAC+BTI (`P16` `E16.3`, `T664a`)**:
   - Support `LirType.V128` on AArch64 using 128-bit NEON registers (`V0..V31`).
   - Implement ARM64 `unsafe asm(...)` syntax and lowering.
   - Implement ARM64 Pointer Authentication (`PAC`, `+pauth`, `paciasp`/`autiasp`) and Branch Target Identification (`BTI`, `+bti`, `bti c`).

2. **Capability-Safe Apple Objective-C Layer (`P16` `E16.4`, `T668a`)**:
   - Module `std.ffi.objc` provides type-safe Cocoa and UIKit bindings.
   - Direct trampoline calls to `objc_msgSend` cast to exact function pointers matching selector argument and return types (ensuring correct AAPCS64 ABI register assignments).
   - `ObjcStrong<T>` handles ARC retain/release semantics.
   - `AutoreleasePool` blocks enforce lexical containment via `view<AutoreleasePool>`.
   - FFI exception boundaries intercept `@catch` and translate ObjC exceptions into `Result<T, ObjcError>`.
   - Windows x64 testing uses a mock `libobjc.dll` and Mach-O `__objc_selrefs` relocation validator. `T969` (Metal driver) depends on `T668a`.

3. **WASM SIMD128 & JS Binding Layer (`P16` `E16.6`, `T675a`)**:
   - WASM `SIMD128` (`0xFD` opcodes) lowering for `LirType.V128`.
   - `std.ffi.wasm_js` provides `@wasm_import` and `@wasm_export` attributes, `JsValue` opaque handles, UTF-8 linear-memory slice adapters, TypeScript definition export (`--emit-ts-defs`), and WebAssembly Interface Type (`.wit`) signature extraction. `T978` (WebGPU bridge) depends on `T675a`.

4. **Cross-OS Native Async Reactors (`P21` `E21.10`, `SPEC-129`, `T940`–`T943`)**:
   - Relocated from P11 to P21 to respect the target availability DAG (since non-Windows targets are authored in P16).
   - Linux: Dual-engine architecture with runtime probe of `io_uring_setup()` falling back automatically to `epoll_create1` + `epoll_pwait2` in restricted containers or older kernels.
   - DMA write-after-free prevention: When an async `Future` is dropped while a kernel read/write is in-flight, the slot transitions to `IoOpState.CancellingZombie`, issuing `IORING_OP_ASYNC_CANCEL` / `CancelIoEx`. The underlying buffer memory is retained until the kernel CQE completion event is collected.
   - macOS / iOS: Native `kqueue` / `kevent64` reactor.
   - Conformance: WSL2 execution and Windows mock harness DLL stress-tested with 10,000 cancellation cycles.

---

### Pillar 4 — Tooling, Fuzzing, Static 0-Day Scanner & Polyglot SDK (P17, P20, P21)
1. **Coverage-Guided & Structure-Aware Fuzzer (`P17` `E17.8`, `SPEC-99`, `T727`–`T730`)**:
   - Compiler pass instruments basic-block edges (`-fsanitize-coverage=trace-pc-guard`) updating a 64 KiB shared-memory edge-frequency bitmap.
   - Two-process runner: Coordinator communicates with an isolated child Worker via shared memory, surviving child segfaults (`STATUS_ACCESS_VIOLATION`), panics, or hangs.
   - Structure-aware generation: `Arbitrary` trait with `@derive(Arbitrary)` synthesized using P14 `TypeInfo` reflection.
   - CLI: `axiom test --fuzz`. Deterministic regression replay of `fuzz/crashes/` runs as part of standard `axiom test` in `< 1.0s`.

2. **Static C++ Zero-Day Vulnerability Scanner (`P17` `E17.9`, `SPEC-151`, `T731`–`T734`)**:
   - Fast $O(\text{CFG})$ intraprocedural and summary-based interprocedural abstract interpretation over MIR, preserving the `< 100 ms` incremental rebuild SLA.
   - Detects 10 major C++ vulnerability classes across unsafe/FFI boundaries:
     1. Unchecked `count * stride` allocation integer overflow (`AX_VERIFY_UNCHECKED_ALLOC_OVERFLOW`)
     2. Narrowing or sign-flipping casts into buffer lengths (`AX_VERIFY_TRUNCATING_LEN_CAST`)
     3. Static Use-After-Free on error paths (`AX_UNSAFE_STATIC_USE_AFTER_FREE`)
     4. Static Double-Free / mismatched allocator (`AX_UNSAFE_STATIC_DOUBLE_FREE`)
     5. Stack/view pointer escaping scope (`AX_UNSAFE_STACK_PTR_ESCAPE`)
     6. Untagged union active-variant confusion (`AX_UNSAFE_UNION_TYPE_CONFUSION`)
     7. Uninitialized `@repr(C)` padding leakage (`AX_FFI_UNINIT_PADDING_LEAK`)
     8. Filesystem TOCTOU race (`AX_IO_TOCTOU_RACE`)
     9. Untrusted path traversal (`AX_IO_TAINTED_PATH_TRAVERSAL`)
     10. Untrusted OS command injection (`AX_IO_TAINTED_COMMAND_SINK`)
   - CLI: `axiom audit --zero-day`, `--deny-zero-day-patterns`, `@suppress`, and standard SARIF 2.1 JSON output (`--emit=sarif`).

3. **Polyglot FFI Header Importer & SDK Exporter (`P20` `E20.8`, `SPEC-117`, `T878`–`T881`)**:
   - `axiom bindgen <header.h>`: Pure-Axiom C99/C11 preprocessor (`#include`, `#define`, `#ifdef`) and parser generating canonical `@repr(C)` types and `extern "C"` declarations. Rejects C++ templates/classes with `AX_PARSE_CPP_HEADER_UNSUPPORTED`.
   - `axiom build --export-sdk c|python|swift|kotlin|ts`: Emits zero-dependency wrapper files from `ForeignInterface` IR: C99 `.h`, Python `ctypes`, Swift `.modulemap` + `.swift`, Kotlin JNI `.kt`, and TypeScript `.d.ts` + WASM ESM loader. Testable on Windows without requiring third-party toolchains.

4. **Live Stateful Hot-Reload Runner (`P21` `E21.3`, `T937`)**:
   - CLI runner `axiom dev --hot` connects filesystem event watching (`T909`), IPC (`T910`), and `E20.7` transactional component state migration (`T872`).
   - If an edit introduces an ABI-breaking schema change that cannot be migrated, the runner gracefully falls back to a clean child-process restart without crashing the developer loop.

---

### Pillar 5 — Standard Library Completion: WebPKI TLS 1.3, SIMD JSON, Linear Regex & FastAPI-Grade `std.web` (P21)
1. **Linear-Time Bounded Regex (`P21` `E21.2`, `T936`)**:
   - Pure-Axiom Thompson NFA PikeVM with bounded-memory Lazy DFA (512 KiB cache cap).
   - Strictly $O(n \cdot m)$ time, zero catastrophic backtracking, full Unicode support, and cancellable via `view<CancellationToken>`.

2. **WebPKI & TLS 1.3 Mandatory Crypto Primitives (`P21` `E21.8`, `T938`)**:
   - Add RFC 8446 mandatory cryptographic primitives to `std.crypto`: `AES-128/256-GCM` (`@multiversion` hardware AES-NI/ARMv8-CE + constant-time bit-sliced software fallback & constant-time GHASH), `ECDSA P-256`, and `RSA-PSS` verification.
   - `T931` and `T914` depend on `T938`.

3. **Hardened Pure-Axiom TLS 1.3 & HTTP/2 (`P21` `E21.4`, `T914`)**:
   - RFC 8446 TLS 1.3 client/server engine, strict RFC 5280 DER X.509 chain validation, and OS system root trust store integration (`CertVerifyCertificateChainPolicy` on Windows, `/etc/ssl/certs` on Linux, `Security.framework` on macOS).
   - HTTP/2 transport engine with built-in defenses against Rapid Reset (CVE-2023-44487 leaky-bucket stream reset rate limiting), `CONTINUATION` flood caps, and bounded HPACK decompression.

4. **SIMD-Accelerated JSON (`P21` `E21.7`, `T924`/`T925`/`T927`)**:
   - Vectorized structural character indexing (`Vector<u8, N>`) with bit-exact scalar fallback and `@derive(Serialize)` / `@derive(Deserialize)` integration.

5. **FastAPI-Grade Web Application Framework (`P21` `E21.11`, `SPEC-152`, `T944`–`T947`)**:
   - Route registration: High-performance radix tree router supporting typed route parameters (`/users/{id: u64}`).
   - Typed extractors & dependency injection: `FromRequest<S>` trait for `Path<T>`, `Query<T>`, `Json<T>`, `Header<T>`, and `State<T>`, validated at compile-time using P14 `comptime` `TypeInfo` reflection (pinpoint diagnostic `AX_TYPE_HANDLER_PARAM_NOT_EXTRACTOR`).
   - Request validation & RFC 9457: `@derive(Validate)` with constraint attributes (`@validate(min = 1, max = 100, regex = "...")`), automatically emitting RFC 9457 `422 Unprocessable Content` JSON errors on validation failure.
   - Compile-time OpenAPI 3.1 & Air-gapped `/docs`: Derives OpenAPI 3.1 JSON (`/openapi.json`) during compile-time reflection. Embeds interactive Swagger UI HTML/JS via `@embed_str` (`T573`) for air-gapped deployments with zero external CDN dependencies.
   - Production server hardening: Slowloris read/write timeouts, `max_body_bytes` pre-check (`413 Content Too Large`), streaming `Multipart` processing in 64 KiB chunks, path-traversal resistant `StaticDir` (rejecting NUL, `\`, `..`, NTFS `::$DATA`, and DOS device names), streaming SSE (`SseStream`), and WebSocket upgrades.

---

### Pillar 6 — OpenGL 4.5+ / OpenGL ES 3.1+ Compatibility Backend (P22 E22.9, SPEC-138, T985–T988)
1. **Normative Architecture Boundary (`0846 §216`)**:
   - OpenGL is introduced strictly as an optional compatibility backend behind `std.gpu` / `std.gfx`. The core architecture remains modern explicit graphics (`CommandEncoder`, `ComputePipeline`, `GraphicsPipeline`, `DeviceBuffer`). Global mutable OpenGL state (`glBind*`) is never exposed in Axiom APIs.

2. **Thread-Affinity Decoupling**:
   - `CommandEncoder` records command streams on any thread (`Send`).
   - `Queue.submit` replays recorded commands deterministically on the context-owning OS thread using Direct State Access (`GL_ARB_direct_state_access` on GL 4.5+) or a shadow state-diff tracker on GL 4.3 / GLES 3.1+.

3. **Coordinate System & Clip-Space Normalization**:
   - Normalize NDC depth from OpenGL's default `[-1, 1]` to Axiom's standard `[0, 1]` using `glClipControl(GL_LOWER_LEFT, GL_ZERO_TO_ONE)` when available, or by emitting an automatic vertex epilogue `gl_Position.z = gl_Position.z * 2.0 - gl_Position.w` in `compiler/target/glsl`.
   - Normalizes framebuffer Y-axis inversion across render-to-texture passes.

4. **Target Scope & Fallback**:
   - Desktop: OpenGL 4.3–4.6 Core via WGL (Windows) and EGL/GLX (Linux).
   - Mobile/Embedded: OpenGL ES 3.1–3.2 via EGL 1.5 (Android, Embedded Linux ARM/RISC-V). Apple platforms always use Metal (`E22.5`).
   - Testing: Offscreen FBO rendering and differential image comparison against the CPU Software Rasterizer (`E22.6`).

---

### Pillar 7 — Complete Crypto Suite, Constant-Time Encodings & Quarantined Legacy Cryptography (P21 E21.8, SPEC-127, T948–T949)
1. **Modern Cryptographic Suite Breadth (`T948`)**:
   - Extended digest algorithms: `Sha384` (required for `TLS_AES_256_GCM_SHA384`), FIPS 202 `Sha3_256`, `Sha3_512`, `Shake128`, `Shake256` (`0x06` pad byte), and distinct `Keccak256` (`0x01` pad byte).
   - Memory-hard password hashing: RFC 9106 `Argon2id` (PHC string format) and RFC 8018 `Pbkdf2HmacSha256`/`Pbkdf2HmacSha512`. All working memory blocks implement `ZeroizeOnDrop`; verification enforces strict `max_memory_kib` / `max_time_cost` caps against memory-exhaustion DoS.
   - Symmetric modes: `Aes128Ctr`/`Aes256Ctr`, `Aes128Cbc`/`Aes256Cbc`, and RFC 3394 `AesKw` (Key Wrap). `AesCbc` PKCS#7 unpadding evaluates all 16 bytes in constant time (`ct_eq`/`ct_select`) with zero early exit.
   - Constant-time encoding: `std.encoding.hex` and `std.encoding.base64` (`Standard` and `UrlSafe`) implemented via branchless constant-time arithmetic to eliminate cache-timing leaks.

2. **Quarantined Legacy Cryptography (`std.crypto.legacy`, `T949`)**:
   - Legacy primitives (`Sha1`, `HmacSha1`, `Md5`, `Des`, `TripleDes`) are quarantined under `std.crypto.legacy` for RFC 6455 WebSocket handshakes, RFC 6238 TOTP 2FA, Git object hashing, and legacy HSM/PKCS#12 interoperability.
   - `Des` and `TripleDes` are implemented exclusively with constant-time bit-sliced S-boxes.
   - Misuse of `std.crypto.legacy` primitives in modern cryptographic sinks without `@suppress` is statically detected and rejected by `P17` `E17.9` (`AX_VERIFY_WEAK_CRYPTO_PRIMITIVE`).

---

## 3. Implementation Plan & Phase Integration

The implementation is mapped into canonical tasks across the active phases:

| Phase | Task ID | Epic | Title | Depends On |
|---|---|---|---|---|
| **P12** | `T480` | `E12.2` | IEEE-754 `f16` scalar lattice, `bf16` storage/SIMD model & SSE2/F16C lowering | `[T457, T459]` |
| **P13** | `T534` | `E13.1` | Canonical `unsafe asm(...)` HIR/MIR/LIR & x86-64 inline assembly codegen | `[T501, T504]` |
| **P13** | `T535` | `E13.4` | Binary exploit mitigation shield: CET, KCFI, stack canaries, clash guard & zero-padding | `[T508, T518]` |
| **P14** | `T573` | `E14.1` | Sandboxed compile-time asset embedding (`@embed_bytes`, `@embed_str`) | `[T551, T554]` |
| **P14** | `T574` | `E14.3` | Async generators (`async gen fn` -> `AsyncIterator`) & coroutine state machine | `[T562, T563, T417]` |
| **P16** | `T664a` | `E16.3` | AArch64 NEON (`LirType.V128`), ARM64 `unsafe asm(...)` & ARM64 PAC+BTI lowering | `[T662, T663, T534]` |
| **P16** | `T668a` | `E16.4` | Apple Objective-C runtime layer (`std.ffi.objc`), ARC & autorelease pool | `[T666, T667]` |
| **P16** | `T675a` | `E16.6` | WASM `SIMD128` (`0xFD`) lowering & `std.ffi.wasm_js` binding layer | `[T674, T675]` |
| **P17** | `T727` | `E17.8` | Canonical specification for coverage-guided and structure-aware fuzzing (`SPEC-99`) | `[T217, T316]` |
| **P17** | `T728` | `E17.8` | Edge coverage instrumentation (`trace-pc-guard`) & shared-memory bitmap | `[T727, T720]` |
| **P17** | `T729` | `E17.8` | Crash-isolated fuzz coordinator/worker runner, `Arbitrary` derive & CLI | `[T728, T558]` |
| **P17** | `T730` | `E17.8` | Crash minimization, `< 1.0s` regression replay & fuzzing conformance suite | `[T729]` |
| **P17** | `T731` | `E17.9` | Canonical specification for static C++ zero-day vulnerability scanning (`SPEC-151`) | `[T217, T316]` |
| **P17** | `T732` | `E17.9` | MIR abstract interpretation for memory, type confusion & padding infoleaks | `[T731, T720]` |
| **P17** | `T733` | `E17.9` | MIR abstract interpretation for TOCTOU, path traversal, command injection & SARIF | `[T732]` |
| **P17** | `T734` | `E17.9` | CLI `axiom audit --zero-day`, `@suppress` & CVE-modeled exploit-litmus suite | `[T733]` |
| **P20** | `T878` | `E20.8` | Canonical specification for polyglot FFI importer and SDK exporter (`SPEC-117`) | `[T220, T316, T318]` |
| **P20** | `T879` | `E20.8` | Pure-Axiom C99/C11 FFI preprocessor & header parser (`axiom bindgen`) | `[T878, T851]` |
| **P20** | `T880` | `E20.8` | `ForeignInterface` IR lowering to C99, Python, Swift, Kotlin & TypeScript | `[T879, T867]` |
| **P20** | `T881` | `E20.8` | CLI `axiom build --export-sdk` & multi-language golden conformance | `[T880]` |
| **P21** | `T936` | `E21.2` | Linear-time, bounded-memory Thompson PikeVM / Lazy DFA `std.regex` | `[T221, T905]` |
| **P21** | `T937` | `E21.3` | Stateful live hot-reload CLI runner `axiom dev --hot` | `[T221, T909, T910, T872]` |
| **P21** | `T938` | `E21.8` | WebPKI & TLS 1.3 crypto primitives (`AES-GCM`, `ECDSA P-256`, `RSA-PSS`) | `[T221, T930]` |
| **P21** | `T939` | `E21.9` | Production `HardenedAllocator` (`IsoHeap`) with partition isolation & quarantine | `[T221, T933, T535]` |
| **P21** | `T940` | `E21.10` | Canonical specification for cross-OS native async reactors (`SPEC-129`) | `[T221, T311, T316]` |
| **P21** | `T941` | `E21.10` | Linux `io_uring` + `epoll` dual reactor with DMA zombie cancellation safety | `[T940, T652]` |
| **P21** | `T942` | `E21.10` | macOS and iOS `kqueue` / `kevent64` async reactor | `[T940, T667]` |
| **P21** | `T943` | `E21.10` | Cross-OS async reactor conformance suite, WSL2 & mock test harness | `[T941, T942]` |
| **P21** | `T944` | `E21.11` | Canonical specification for FastAPI-grade `std.web` framework (`SPEC-152`) | `[T221, T914, T573, T936]` |
| **P21** | `T945` | `E21.11` | Radix tree router, `FromRequest` extractors & comptime handler verification | `[T944, T558]` |
| **P21** | `T946` | `E21.11` | `@derive(Validate)` RFC 9457 `422` & comptime OpenAPI 3.1 + air-gapped `/docs` | `[T945, T573, T936]` |
| **P21** | `T947` | `E21.11` | Hardened HTTPS/H2 server, DoS guards, streaming Multipart & SSE/WebSocket | `[T946, T914, T574]` |
| **P21** | `T948` | `E21.8` | Complete modern crypto suite: SHA-3, Argon2id, PBKDF2, AES-CTR/CBC/KW & constant-time Base64/Hex | `[T221, T938]` |
| **P21** | `T949` | `E21.8` | Quarantined `std.crypto.legacy` (`Sha1`, `HmacSha1`, `Md5`, bit-sliced `Des`/`TripleDes`) | `[T221, T948]` |
| **P22** | `T985` | `E22.9` | Canonical specification for OpenGL 4.5+ / GLES 3.1+ compatibility (`SPEC-138`) | `[T222, T311, T312, T316]` |
| **P22** | `T986` | `E22.9` | `compiler/target/glsl` GLSL 450 & ESSL 310 emitter with NDC clip normalization | `[T985, T959]` |
| **P22** | `T987` | `E22.9` | `std/sys/gpu/opengl` thread-safe WGL/EGL/GLX command replay driver & state tracker | `[T986, T963]` |
| **P22** | `T988` | `E22.9` | Headless FBO & Software-Rasterizer differential conformance suite | `[T987, T974]` |

---

## 4. Consequences & Invariants Maintained

1. **Language Invariants**: Canonical syntax (`=` and `.`) is strictly maintained. Zero macro syntax (`asm!`), zero unbacked RTTI, and zero backtracking regex.
2. **Deterministic Drop & Memory Safety**: Coroutines, async reactors, and WebPKI transports enforce strict capability and lifetime bounds. Premature future drops never lead to kernel DMA corruption.
3. **Hardened Defense Posture**: Axiom binaries built with `--hardened` achieve state-of-the-art defense against ROP, JOP, ASLR infoleaks, and heap spray attacks with `< 3%` CPU runtime overhead.
4. **Developer Experience & Ecosystem Independence**: From pure-Axiom C header binding generation to FastAPI-grade web applications with zero CDN dependencies, Axiom provides a complete, autonomous development ecosystem.
5. **No Regressions on Gates**: All newly introduced tasks wire cleanly into their respective phase gates (`T312`, `T313`, `T314`, `T316`, `T317`, `T320`, `T321`, `T322`), maintaining full traceability and validation.
