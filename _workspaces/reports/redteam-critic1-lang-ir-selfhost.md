# Red-Team Architectural Review: Proposals #1, #3, #4, and #7

**Author**: Red-Team Critic 1 (Language, Ownership, IR, Compiler Architecture & Self-Host Risk)
**Scope**: Adversarial stress-test, grammar/ownership/lattice audit, and phase-DAG verification for Proposals #1, #3, #4, and #7.

---

## Summary Matrix

| Proposal | Verdict | Key Architectural Flaw Caught | Recommended Remedy & Phase Placement |
|---|---|---|---|
| **#1 Native `f16`/`bf16` & SIMD** | `TRIM SCOPE & SPLIT TARGETS` | `f16` (1-5-10) and `bf16` (1-8-7) have incomparable geometries under `REQ-OWNER-007`; `bf16` has zero scalar CPU math instructions; full AVX-512 EVEX/ZMM/k-mask in `P12` explodes regalloc & Win64 `XMM6..15` partial callee-save ABI. | Put `f16` in lattice (`I < f16 < f32 < f64`); make `bf16` an explicit storage/conversion + SIMD dot-product type (`to_f32`/`from_f32`/`to_bits`/`from_bits`, no scalar `+ - * /`); drop full EVEX from `P12` (`Vec512` legalized to `2x v256`); wire `ARM64 NEON` & `WASM SIMD128` to `LirType.V128` in `P16` (`T662`, `T674`). |
| **#3 Typed Inline Assembly & CFI** | `ACCEPT WITH REFINEMENTS & SPLIT ARCHITECTURES` | `asm!(...)` is an illegal Rust bang-macro leak (Axiom has zero `!` macros; normative `0137 §40` / `0232 §43` use `unsafe asm(...)`); ARM64/RISC-V encoders do not exist in `P13`; `--interp` cannot run raw asm. | Mandate canonical `unsafe asm(...)` / `unsafe asm { ... }`; implement x86-64 `unsafe asm` + Intel `CET` (`ENDBR64` + PE `GuardFlags`) in `P13` (`E13.1`/`E13.4`); implement ARM64/RISC-V `unsafe asm` + ARM64 `PAC`+`BTI` in `P16`; deterministic trap `AX_INTERP_INLINE_ASM_UNSUPPORTED` in `--interp`. |
| **#4 Async Generators & `@embed_*`** | `ACCEPT WITH REFINEMENTS & STRICT GUARDRAILS` | Prefix `for await` violates postfix `.await` (`SPEC-02 AXS-GRM-050`); `@embed_*` risks `..` path traversal & stale `P18` incremental cache; `@embed_str` requires UTF-8 check; giant `.rdata` DoS. | Consume `AsyncIterator` via canonical `while let Option.Some(x) = stream.next().await`; unify coroutine MIR lowering in `E14.3` enforcing no `view`/`mut_view` across `.await` OR `yield` + composite cancel drop glue; sandbox `@embed_bytes`/`@embed_str` inside package root (`AX_EMBED_PATH_TRAVERSAL`), hash BLAKE3 into `P18` `QueryDb`, validate UTF-8 (`AX_EMBED_INVALID_UTF8`), 64 MiB default cap. |
| **#7 `axiom dev --hot` Runner** | `RELOCATE PHASE (TO P21)` | `P19` is closed (`T319` done); `P20` `E20.7` (`T870`–`T873`) ALREADY built the full 5-phase transactional hot-reload runtime (`SPEC-115`); runner needs `FsWatcher` (`T909`) + IPC (`T910`) in `P21`. | Place CLI runner `axiom dev --hot` in `P21` (`E21.3`, `depends: [T221, T909, T910, T872]`); on ABI-breaking schema mismatch, automatically fall back from rollback to clean child-process restart with clear diagnostic. |
