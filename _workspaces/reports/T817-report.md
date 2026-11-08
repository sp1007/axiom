# T817 Report — E19.5 CompilerDB Documentation Extractor, HTML/JSON Site Renderer, Search Index & Executable Doc-Test Runner (`axiomc doc`)

STATUS: COMPLETE

## Summary

Implemented the self-hosted Axiom documentation extractor, semantic intra-doc link resolver, offline-first static HTML/CSS/JS renderer, `search-index.json` and `doc-graph.json` (`schema_version: 1`) emitters, executable doc-test synthesizer/span-remapper/runner, and `axiomc doc` CLI subcommand driver (`compiler/docgen/mod.ax` and `compiler/driver/doc_cmd/mod.ax`) in accordance with `SPEC-104` (`AXS-DOC-001` through `AXS-DOC-053`) and `REQ-TOOL-002`.

1. **Zero-Codegen `CompilerDB` Extraction & Non-Semantic Invariance (`AXS-DOC-001`, `AXS-DOC-002`, `AXS-DOC-005`)**:
   - Implemented `docgen_eval_semantic_queries_zero_codegen` querying `parse_module`, `module_def_map`, `resolve_module`, `item_signature`, `typeck_body`, `trait_solve`, `const_eval`, `layout_of`, and `effect_summary` with `mir_lower_evaluated == 0` and `codegen_unit_evaluated == 0`.
   - Implemented `///` outer doc, `//!` inner module doc, CommonMark paragraph summary extraction, `# ` hidden setup line stripping (`docgen_strip_hidden_setup_lines`), and `DocFingerprint` vs `AstFingerprint` non-semantic invariance verification (`docgen_verify_non_semantic_invariance`).

2. **First-Class Semantic Contracts & Intra-Doc Link Resolution (`AXS-DOC-003`, `AXS-DOC-004`)**:
   - Extracted and rendered value/capability parameter contracts (`move`, `copy`, `view`, `mut_view`), trait object-safety diagnostics, `@container_contract` (`storage_kind`, `relocates_on_grow`, `invalidates_views_on_mutate`, `element_drop_order`), and `@api_effect` badges (`alloc_behavior`, `blocking_behavior`, `panics_possible`, `unsafe_required`, `sync_safety`, `complexity_time`, `complexity_space`).
   - Implemented `docgen_resolve_intra_doc_links` and `docgen_write_broken_link_diag_json` emitting `AX_NAME_UNRESOLVED` (`E1001`) warnings by default and escalating to hard errors under `--deny-broken-links` with `"data":{"context":"doc_link","doc_link":"..."}`.

3. **Deterministic HTML Site, `search-index.json`, and `doc-graph.json` (`AXS-DOC-010`, `AXS-DOC-011`, `AXS-DOC-012`)**:
   - Implemented canonical package graph sorting (`docgen_sort_package_graph`) by `(module_path, kind_ordinal, name, semantic_key.fingerprint)`.
   - Implemented byte-for-byte deterministic offline-first HTML/CSS/JS rendering (`docgen_render_html_site`), client-side search index (`docgen_render_search_index_json`), and `doc-graph.json` (`docgen_render_doc_graph_json`, `format: "AXDOC"`, `schema_version: 1`) respecting `--include-private` and `--include-hidden`.

4. **Executable Doc-Test Synthesizer, Span Remapper, Runner & `axiomc doc` CLI Driver (`AXS-DOC-050`–`AXS-DOC-053`)**:
   - Implemented `docgen_parse_fence_info`, `docgen_synthesize_doctest_harness`, `docgen_remap_doctest_span`, `docgen_run_doctest_block`, and `docgen_run_package_doctests` supporting `axiom` (`run`), `no_run`, `compile_fail(AX_...)`, `should_panic(expected = "...")`, and `ignore`.
   - Implemented `compiler/driver/doc_cmd/mod.ax` (`doc_parse_cli_args`, `doc_cmd_execute`, `doc_cmd_write_summary_json`) handling `--out-dir`, `--json`, `--test`, `--no-test`, `--include-private`, `--include-hidden`, `--deny-broken-links`, `--no-deps`, `--open`, and exit codes `0` / `1` / `2`.

## Verification

- Executed `python tools/axtest.py --compiler build/axiomc2.exe -j 1 --exclude-requires axiom0-internal run/docgen`:
  - `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`) across `interp`, `native`, and `native-O1`, plus the 12-probe self-hosted compiler bundle (`docgen.test` / `docgen_oracle.py`).

## Files changed

- compiler/docgen/mod.ax
- compiler/driver/doc_cmd/mod.ax
- tests/run/docgen/docgen.test
- tests/run/docgen/docgen_oracle.py
- tests/run/docgen/docgen_probe.ax.in
- tests/run/docgen/doc_extract_and_links.ax
- tests/run/docgen/doc_extract_and_links.stdout
- tests/run/docgen/html_json_determinism.ax
- tests/run/docgen/html_json_determinism.stdout
- tests/run/docgen/doctest_runner_and_binary_invariance.ax
- tests/run/docgen/doctest_runner_and_binary_invariance.stdout
