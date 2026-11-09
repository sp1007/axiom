# Adversarial Architectural Review: Proposals #2, #5, #6, #8, and #9

**Author**: Red-Team Critic 2 (Systems, Async I/O, FFI, Fuzzing, Networking/Crypto Security & SDK Ecosystem)
**Scope**: Adversarial stress-test, security audit, DAG/phase dependency verification, ABI traps, and task design for Roadmap Proposals #2, #5, #6, #8, and #9.

---

## Executive Summary Matrix

| # | Proposal Title | Verdict | Core Finding / Trap Caught | Recommended Phase Placement |
|---|---|---|---|---|
| **#2** | Cross-OS Async I/O Reactors (`io_uring`/`epoll`, `kqueue`) | **RELOCATE PHASE & REFINE** | Target absence in P11 (circular DAG); `io_uring` container/seccomp failure; kernel DMA write-after-free upon future drop. | Relocate from P11 to **P21** (new Epic `E21.10`, `depends: [T221, T311, T316]`). |
| **#5** | Apple `std.ffi.objc`, WASM `std.ffi.wasm_js` + WIT, `axiom bindgen` | **TRIM SCOPE & RELOCATE PART** | `objc_msgSend` AAPCS64 casting & ARC unwind traps; WASI Preview 2 scope explosion; C header parsing without clang fails on `<windows.h>`. | `std.ffi.objc` & lightweight `wasm_js` in **P16**; `bindgen` restricted to C99/C11 FFI headers and relocated to **P20**. |
| **#6** | Built-in Coverage & Structure-Aware Fuzzer (`axiom test --fuzz`) | **ACCEPT WITH REFINEMENTS** | P19 is closed (`T319` done); in-process crash kills coordinator; needs process isolation + deterministic corpus replay in `< 1s`. | **P17** (Epic `E17.8`, `depends: [T217, T316, T722, T726]`). |
| **#8** | SIMD `std.json`, Pure-Axiom TLS 1.3 + HTTP/2/WS/SSE, Linear `std.regex` | **ACCEPT WITH REFINEMENTS** | **Critical Security Flaw**: TLS 1.3 lacking P-256, RSA-PSS & AES-128-GCM cannot connect to real HTTPS (RFC 8446); HTTP/2 Rapid Reset CVE-2023-44487. | **P21** (`E21.8` crypto expansion, `E21.4` transport hardening, `E21.7` JSON, `E21.2` regex). |
| **#9** | Polyglot SDK Auto-Exporter (`axiom build --export-sdk`) | **RELOCATE PHASE & REFINE** | Violates P23 semantic freeze; bleeds into P24; must be 100% self-contained without requiring Swift/Kotlin/Node runtimes on Windows host. | Relocate from P23 to **P20** (Epic `E20.8`, `depends: [T220, T316, T318]`). |

---

## Key Security, ABI & DAG Guardrails Enforced

1. **Proposal #2 (`E21.10` Cross-OS Native Async Reactors)**:
   - Must NOT sit in `P11` (Linux/macOS/Android/iOS targets are created in `P16`). Place in `P21` (`depends: [T221, T311, T316]`) and wire `T913` / `T321` appropriately.
   - Linux reactor must probe `io_uring_setup()` at runtime and transparently fall back to `epoll_create1` + `epoll_pwait2` on `ENOSYS` / `EPERM` / `EACCES` (Docker/K8s seccomp & Android).
   - Completion backends (`IOCP`, `io_uring`) MUST enforce `SPEC-35` `AXS-AIO-010`: `IoBuf` owned inside `IoOpSlot`; on early `Future` drop, transition to `IoOpState.CancellingZombie` (`IORING_OP_ASYNC_CANCEL` / `CancelIoEx`) and NEVER free or reclaim buffer memory until kernel CQE/completion harvest.
   - Windows-host testability for `kqueue`: `--interp` virtual reactor + Mach-O symbol/relocation validator (`_kqueue`, `_kevent64`) + Windows mock harness DLL.

2. **Proposal #5 (`std.ffi.objc`, `std.ffi.wasm_js`, `axiom bindgen`)**:
   - `std.ffi.objc` (`P16` `E16.4` / `E16.13`): `objc_msgSend` MUST be cast to exact C function-pointer types matching selector arguments/returns (never variadic on ARM64); direct `dyld` trampoline calls for ARM64e PAC; exception guard at FFI boundary; `ObjcStrong<T>` retain/release + `with_autorelease_pool` lifetime-gated via `view<AutoreleasePool>`; tested on Windows x64 via mock `libobjc` DLL (matching `T671` JNI precedent) + Mach-O `__objc_selrefs` validator.
   - `std.ffi.wasm_js` (`P16` `E16.6`): Do NOT build a 150k-LoC WASI Preview 2 Component Model runtime. Ship `@wasm_import`/`@wasm_export`, `JsValue` handle table, UTF-8 linear-memory slice marshaling, `--emit-ts-defs` `.d.ts` + ESM glue, and exported `.wit` signature generator.
   - `axiom bindgen` (`P20` `E20.8`): Pure-Axiom C99/C11 FFI header preprocessor (`#include`, `#define` constants, `#ifdef` guards) + `typedef`/`struct`/`union`/`enum`/`extern` function parser emitting canonical `@repr(C)` + `extern "C"` `.ax` modules; cleanly reject C++ templates/classes/function bodies with `AX_BINDGEN_CPP_UNSUPPORTED`.

3. **Proposal #6 (`P17` `E17.8` Coverage-Guided & Structure-Aware Fuzzer)**:
   - Coordinator + sandboxed child Worker process sharing a 64 KiB edge-coverage bitmap (`CreateFileMappingW` on Windows / `shm_open` on POSIX) so `STATUS_ACCESS_VIOLATION` or timeouts in `unsafe` code never kill the coordinator.
   - `Arbitrary` trait + `@derive(Arbitrary)` leveraging `P14` `TypeInfo` reflection.
   - Running normal `axiom test` (without `--fuzz`) automatically replays `fuzz/corpus/` and `fuzz/crashes/` deterministically in `< 1.0s`.

4. **Proposal #8 (`P21` `std.json`, Hardened `TLS 1.3` + `HTTP/2`/`WS`/`SSE`, Linear-Time `std.regex`)**:
   - `std.crypto` + `std.net.tls`: MUST include RFC 8446 mandatory `TLS_AES_128_GCM_SHA256` + `TLS_AES_256_GCM_SHA384` (AES-NI/ARMv8-CE via `@multiversion` + constant-time bit-sliced software fallback & constant-time GHASH — zero lookup tables!) AND `ECDSA P-256` + `RSA-PSS` signature verification + strict RFC 5280 DER X.509v3 + OS system root trust store (`CertVerifyCertificateChainPolicy` on Windows, `/etc/ssl/certs` on Linux, `Security.framework` on Apple).
   - `HTTP/2`, `WebSocket`, `SSE`: enforce leaky-bucket `RST_STREAM` rate limit against Rapid Reset (CVE-2023-44487), `max_header_list_size` cap against `CONTINUATION` floods, HPACK decompression expansion bounds, and WebSocket frame limits.
   - `std.json`: SIMD structural indexing (`P12` `Vector<u8, N>`) with exact scalar fallback + `derive(Serialize)` integration.
   - `std.regex`: Thompson NFA / PikeVM + bounded-memory Lazy DFA (512 KiB state cache cap), strictly `O(n * m)` time, zero catastrophic backtracking, Unicode-aware, cancellable via `view<CancellationToken>`.

5. **Proposal #9 (`P20` `E20.8` `axiom build --export-sdk c|python|swift|kotlin|ts`)**:
   - Relocated out of `P23` (preserving `P23` semantic freeze) into `P20` (`T320` gate is still `todo`).
   - Consumes `ForeignInterface` IR to emit pure zero-dependency text wrappers: C99 `.h`, zero-build Python `ctypes`, Swift `module.modulemap` + `.swift`, Kotlin JNI `.kt` (`T671`), and TypeScript `.d.ts` + WASM ESM glue — testable on Windows x64 without Swift/Kotlin/Node installed.
