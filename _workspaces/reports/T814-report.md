# T814 Report — E19.4 AI-agent semantic fact graph exporter, layout/container/std effect metadata inspector & `.axmeta` separation

STATUS: COMPLETE

## Summary

Implemented E19.4 (`T814`) across `std/meta_effects/mod.ax`, `compiler/ai_query/mod.ax`, `compiler/driver/query_cmd/mod.ax`, and `tests/run/ai_query/` in compliance with `SPEC-103 §§4..7` and `SPEC-24 §§1..3` (`AXS-AI-001..021`, `AXS-DIAG-050..053`, `REQ-TOOL-004`, `REQ-TOOL-180`, `REQ-TOOL-181`, `REQ-TOOL-182`, `REQ-TOOL-185`, `REQ-TOOL-186`, `REQ-TOOL-187`, `REQ-TOOL-190`, `INV-DIAG-010`):

1. **`std.meta_effects` Container & API Effect Registry (`std/meta_effects/mod.ax`)**:
   - Implemented `StorageKind` (`InlineFixed`, `HeapContiguous`, `HeapTable`, `HeapNodeGraph`, `BorrowedContiguous`, `SharedRefCounted`) and `ContainerContract` covering all 8 canonical containers (`Vec`, `HashMap`, `Slice`, `String`, `Array` `[N]T`, `Str`, `Box`, `Arc`) with contiguity, relocatability, address stability, ordering preservation, concurrency model, and view-invalidation rules (`AXS-AI-011`, `REQ-TOOL-181`).
   - Implemented `AllocBehavior`, `BlockingBehavior`, `SyncBehavior`, and `ApiEffectSummary` covering 12 canonical `std` APIs (`std.core.Str.len`, `std.collections.Vec.len`, `std.collections.Vec.push`, `std.collections.Vec.get`, `std.collections.HashMap.insert`, `std.sync.Mutex.lock`, `std.sync.Atomic.load`, `std.fs.File.read`, `std.io.AsyncFile.read`, `std.mem.volatile_load`, `std.alloc.Box.new`, `std.collections.String.push_str`) with receiver modes, allocation/blocking/synchronization contracts, view-invalidation details, authority capabilities (`FsCap`), and `unsafe` preconditions (`AXS-AI-012`, `REQ-TOOL-190`).
2. **AI-Agent Semantic Fact Graph Exporter & Inspectors (`compiler/ai_query/mod.ax`)**:
   - Implemented `AXCP v1` JSON (`--json`) and NDJSON (`--jsonl`) envelopes (`"protocol": "AXCP"`, `"schema_version": 1`, `"codegen_invoked": false`), strict `FactDomain` (`semantic`, `layout_abi`, `optimization`) and `FactCertainty` (`Proven`, `Inferred`, `Observed`, `Possible`, `Unknown`) separation (`ai_validate_domain_certainty`), and zero-codegen `CompilerDB` query evaluation (`ai_eval_semantic_queries_zero_codegen`, `AXS-AI-001..005`, `REQ-TOOL-180`, `REQ-TOOL-185`).
   - Implemented `FieldLayoutFact`, `TypeLayoutFact`, `ai_inspect_type_layout`, `ai_render_layout_human`, and `ai_render_layout_json` for `axiomc inspect layout` and `axiomc query layout` across targets (`x86_64-windows`, `aarch64-linux`, `wasm32-wasi`) without codegen (`AXS-AI-010`, `REQ-TOOL-004`).
   - Implemented ownership & capability lifeline fact graphs (`ai_render_ownership_lifeline_json`, `ai_render_capabilities_json`), trait `why`/`why-not` proof trees (`ai_query_trait_resolution`, `ai_render_trait_trace_json`), symbol/type/unsafe-map/deps/context/facts/opt-remarks query exporters, and `.axmeta` container/effect binary serialization & inspection (`ai_export_axmeta_container_effects`, `ai_inspect_axmeta_container_effects`).
   - Implemented the transactional AI patch verification gate (`ai_verify_patch_candidate`, `ai_render_verify_patch_json`) rejecting `@trust_ai`/`@skip_verify` bypasses, container relocation hazards (`AX_CAP_CONTAINER_RELOC`), use-after-move (`AX_MOVE_USE_AFTER_MOVE`), conflicting mutable borrows (`AX_CAP_CONFLICT_MUT`), unguarded unsafe calls (`AX_UNSAFE_REQUIRED`), and non-canonical syntax (`::`, `:=`, `var `) without modifying disk files or invoking codegen (`AXS-AI-020`, `REQ-TOOL-186`).
   - Implemented the production binary `.axmeta`/`.axdb`/debug separation verifier (`ai_build_mock_pe_image`, `ai_verify_production_binary`, `ai_render_binary_separation_json`) verifying that linked production PE executables contain zero `.axmeta`, `.axlto`, `.axmir`, `.axdb`, or `.axdbg` sections and zero leaked metadata magic headers (`AXS-AI-021`, `REQ-TOOL-182`, `REQ-TOOL-187`).
3. **`axiomc query` & `axiomc inspect layout` CLI Driver (`compiler/driver/query_cmd/mod.ax`)**:
   - Implemented `InspectLayoutCliConfig`, `inspect_layout_parse_arg`, `inspect_layout_execute`, `QueryCliConfig`, `query_cmd_parse_arg`, and `query_cmd_execute` routing all `inspect layout` and `query` subcommands (`symbol`, `type`, `layout`, `ownership`, `capabilities`, `trait`, `container`, `effects`, `unsafe-map`, `deps`, `context`, `facts`, `opt-remarks`, `verify-patch`, `verify-production-binary`).

## Verification

- Executed `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/ai_query`:
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

## Files changed

- compiler/ai_query/mod.ax
- compiler/driver/query_cmd/mod.ax
- std/meta_effects/mod.ax
- tests/run/ai_query/ai_patch_gate_and_axmeta_strip.ax
- tests/run/ai_query/ai_patch_gate_and_axmeta_strip.stdout
- tests/run/ai_query/ai_query.test
- tests/run/ai_query/ai_query_oracle.py
- tests/run/ai_query/ai_query_probe.ax.in
- tests/run/ai_query/layout_and_container_meta.ax
- tests/run/ai_query/layout_and_container_meta.stdout
- tests/run/ai_query/semantic_fact_graph_and_effects.ax
- tests/run/ai_query/semantic_fact_graph_and_effects.stdout
