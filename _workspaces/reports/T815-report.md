# T815 Report — E19.4 Diagnostics UX 2.0, Explain Codes, Machine-Applicable Fixes & AI-Agent Fact Interface Conformance Suite

STATUS: COMPLETE

## Summary

Created the end-to-end E19.4 conformance suite (`tests/conformance/p19/e19_4_diagnostics_ai/`) certifying `SPEC-103-diagnostics-ux-ai-interface.md` (`AXS-DIAG-001..022`, `AXS-AI-001..021`, `AXS-DIAG-050..053`; `INV-DIAG-009..011`; `REQ-TOOL-004`, `REQ-TOOL-180..182`, `REQ-TOOL-185..187`, `REQ-TOOL-190`, `REQ-TOOL-298`):

1. **Multi-Span Causal Provenance, `DiagnosticFingerprint` & `PoisonTaint` Cascade Suppression (`AXS-DIAG-001..005`, `REQ-TOOL-298`)**:
   - `causal_provenance_fingerprints_and_cascade_suppression.ax` and `e19_4_diagnostics_ai_probe.ax.in` verify ordered `CausalProvenanceChain` steps across `MOVE` (`Origin -> Transfer -> Violation`), `CAP` (`Origin -> BorrowShared/BorrowMut -> ContainerMutation/ScopeExit/AliasOverlap -> Violation` with symbolic `region` and `owner`), `CONC`/`TRAIT` (`ObligationOrigin -> Violation` + structural derivation path), and `ASYNC`/`GEN` (`SuspensionPoint -> Violation`).
   - Certifies 128-bit `DiagnosticFingerprint` invariance across line/byte shifts above an item, deduplication, `PoisonTaint` suppression of secondary cascading errors (`0` artificial cascades), ownership taint clearing upon re-initialization (`x = new_val`), unpoisoned sibling independence, zero internal ID leakage (`TypeId(...)`, `HirId(...)`, `RegionId(...)`, `DefId(...)`, `MirBodyId(...)`), and Unicode UTF-8 extended grapheme display column alignment (`"Xin chào"` -> `8` columns).
2. **`axiomc explain <AX_CODE>` Encyclopedia & Transactional `axiomc fix` Convergence (`AXS-DIAG-010..014`, `AXS-DIAG-020..022`, `REQ-TOOL-185`, `REQ-TOOL-186`)**:
   - `explain_registry_and_transactional_fix_convergence.ax` and `e19_4_diagnostics_ai_probe.ax.in` verify 4-tier fix applicability (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`, `Unspecified`), `0146 §65 ADIAG-26` safety enforcement (rejecting `MachineApplicable` fixes that introduce `unsafe`, `@allow_unsafe`, `bitcast`, or non-canonical syntax), conflict deferral across overlapping edits, mandatory `CompilerDB` re-verification under the zero-codegen firewall, transactional rollback when a candidate fix introduces a new error, multi-iteration fix-point idempotence, and `axiomc explain` coverage across all `18` core areas + `12` domain prefixes (`30` areas, `37` entries), shorthand normalization, and exit code `2` on unknown codes.
3. **Type Layout Inspector (`axiomc inspect layout`), `.axmeta` Container Contracts & `std.meta_effects` (`AXS-AI-010..012`, `REQ-TOOL-004`, `REQ-TOOL-181`, `REQ-TOOL-190`)**:
   - `layout_inspector_container_contracts_and_std_effects.ax` and `e19_4_diagnostics_ai_probe.ax.in` verify `axiomc inspect layout` / `axiomc query layout` across `x86_64-windows`, `aarch64-linux`, and `wasm32-wasi` (`PacketHeader`, `PaddedRecord`, `Vec<i32>`, `Pair`, field offsets, internal/tail padding bytes, stride, niche compression, and ABI passing classification), all `8` canonical `ContainerContract` entries (`Vec`, `HashMap`, `Slice`, `String`, `Array`, `Str`, `Box`, `Arc`), all `12` normative `std.meta_effects` `ApiEffectSummary` entries, and binary `"AXMETA01"` section headers (`EffectsCapabilities = 9`, `AIIndex = 13`).
4. **`AXCP v1` AI Semantic Fact Protocol, AI Patch Gate & Production Binary Separation (`AXS-AI-001..005`, `AXS-AI-020..021`, `REQ-TOOL-180`, `REQ-TOOL-182`, `REQ-TOOL-185`, `REQ-TOOL-186`, `REQ-TOOL-187`)**:
   - `ai_fact_protocol_patch_gate_and_binary_separation.ax`, `e19_4_diagnostics_ai_probe.ax.in`, and `e19_4_diagnostics_ai_oracle.py` verify the `AXCP v1` envelope (`"codegen_invoked": false`), `FactDomain` (`semantic`, `layout_abi`, `optimization`) vs `FactCertainty` (`Proven`, `Inferred`, `Observed`, `Possible`, `Unknown`) separation, all `axiomc query` subcommands (`symbol`, `type`, `ownership`, `capabilities`, `trait`, `container`, `effects`, `unsafe-map`, `deps`, `context`, `facts`, `opt-remarks`), transactional `axiomc query verify-patch` rejection of `@trust_ai`/`@skip_verify`/`@ai_bypass` safety bypasses, container relocation invalidation (`AX_CAP_CONTAINER_RELOC`), and use-after-move (`AX_MOVE_USE_AFTER_MOVE`), and strict stripping/separation of `.axmeta`, `.axdb`, `.axlto`, `.axmir`, and `.axdbg` from linked production `.exe` binaries.

## Verification

Executed with `-j 1`:
- `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal conformance/p19/e19_4_diagnostics_ai`
  - Result: `TOTAL 13 PASS 13 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

## Files changed
- tests/conformance/p19/e19_4_diagnostics_ai/README.md
- tests/conformance/p19/e19_4_diagnostics_ai/ai_fact_protocol_patch_gate_and_binary_separation.ax
- tests/conformance/p19/e19_4_diagnostics_ai/ai_fact_protocol_patch_gate_and_binary_separation.stdout
- tests/conformance/p19/e19_4_diagnostics_ai/causal_provenance_fingerprints_and_cascade_suppression.ax
- tests/conformance/p19/e19_4_diagnostics_ai/causal_provenance_fingerprints_and_cascade_suppression.stdout
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_oracle.py
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_oracle.test
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_probe.ax.in
- tests/conformance/p19/e19_4_diagnostics_ai/explain_registry_and_transactional_fix_convergence.ax
- tests/conformance/p19/e19_4_diagnostics_ai/explain_registry_and_transactional_fix_convergence.stdout
- tests/conformance/p19/e19_4_diagnostics_ai/layout_inspector_container_contracts_and_std_effects.ax
- tests/conformance/p19/e19_4_diagnostics_ai/layout_inspector_container_contracts_and_std_effects.stdout
