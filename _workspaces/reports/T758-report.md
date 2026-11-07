# T758 Report — E18.2 Persistent on-disk query/codegen cache, action digest validation & no-op fast path

## Summary
Implemented the persistent on-disk incremental query/codegen cache (`.axiom-cache`), hermetic `ActionDigest` / `EnvironmentDigest` validation, versioned & checksummed binary schema (`AXCACHE1`), atomic temp-file + rename publication protocol, graceful corruption/version/compiler-digest eviction fallback, and `< 100 ms` root workspace manifest no-op fast path in `compiler/incremental/cache/mod.ax`, together with live bundled compiler oracle and differential regression tests in `tests/run/incremental_cache/*` (`SPEC-22 §3-§7`, `AXS-INC-020..053`).

### Key Components Implemented
1. **Versioned, Checksummed `.axcache` Binary Schema & Atomic Commit Protocol (`AXS-INC-020`, `AXS-INC-022`)**:
   - Defined `AXIC_MAGIC` (`"AXCACHE1"`, `0x3145484341435841`), `AXIC_SCHEMA_VERSION = 1`, fixed 32-byte header, and trailing 16-byte 128-bit payload checksum (`inc_cache_compute_payload_checksum`).
   - Implemented full binary serialization (`inc_cache_serialize`) and bounds/checksum-verified deserialization (`inc_cache_deserialize`) for:
     - Extended `ActionDigest` & target configuration metadata;
     - Workspace Input Manifest (`WorkspaceSourceEntry`: `file_id`, `module_id`, `logical_path`, `normalized_len`, `last_size_bytes`, `last_mtime_ns`, `source_fp`);
     - Multi-tier module & item fingerprints (`SourceFingerprint`, `AstFingerprint`, `InterfaceFingerprint`, `AbiFingerprint`, `BodyFingerprint`, `CodegenFingerprint`);
     - Red-green query dependency graph (`RedGreenNode` and typed `TypedDepEdge` edges);
     - Cached diagnostics (`CachedDiagEntry`, replayed in canonical `AXD-060` order via `inc_cache_emit_diagnostics`);
     - Content-addressed per-CGU COFF `.obj` artifacts (`CachedCguArtifact`, `TimeDateStamp = 0` per `INV-DET-001`) and linked PE32+/archive output artifacts (`INV-DET-002`).
   - Implemented on-disk persistence (`inc_cache_save_to_disk`, `inc_cache_load_from_disk`) writing `.tmp` files and atomically committing `<cache_dir>/dep-graph.axcache` and `<cache_dir>/objects/<fp128_hex>.obj`.

2. **Hermetic `ActionDigest` Validation & Graceful Eviction Fallback (`AXS-INC-021`, `AXS-INC-022`, `AXS-INC-024 §2`)**:
   - Implemented `inc_cache_compute_action_digest` and `inc_cache_compute_action_digest_with_host_noise` hashing `"AXIOM-ENV-v1"`, `compiler_binary_digest`, `schema_version`, `target_triple`, `abi_profile`, `cpu_feature_mask`, `opt_level`, `safety_profile`, `panic_strategy`, `artifact_kind`, and `manifest_digest` while strictly excluding undeclared host environment variables, working directory strings, and wall-clock timestamps.
   - Implemented `inc_cache_validate_action_digest` and graceful eviction (`AX_INC_CACHE_CORRUPT = 9250`, `CACHE_EVICT_SCHEMA_MISMATCH`, `CACHE_EVICT_COMPILER_CHANGED`, `CACHE_EVICT_ENV_MISMATCH`, `CACHE_EVICT_CORRUPT_CHECKSUM`, `CACHE_EVICT_TRUNCATED`, `CACHE_EVICT_MISSING_OBJECT`), falling back transparently to a clean rebuild without panic or memory corruption.
   - Enforced Error Non-Pollution (`AXS-INC-024 §2`): modules with error diagnostics never publish a `Ready` `.obj` artifact into the cache.

3. **`< 100 ms` Root Workspace Manifest No-Op Fast Path & Clean Equivalence (`AXS-INC-023`, `AXS-INC-024`, `AXS-INC-050`)**:
   - Implemented `inc_cache_try_noop_fastpath` verifying `ActionDigest`, output artifact presence, and all workspace source inputs (using `(size, mtime_ns)` pre-check backed by normalized UTF-8 `SourceFingerprint` content hashing when `mtime_ns` changes on `touch` or in strict mode) in `< 100 ms` with `0` semantic queries executed and `0` CGUs rebuilt.
   - Implemented `inc_cache_build_clean_no_incremental` (`--no-incremental`) and verified byte-for-byte `.obj` and linked artifact equivalence against warm incremental builds, plus deterministic telemetry (`inc_cache_emit_stats`, `inc_cache_inspect_dump`).

## Files changed
- `compiler/incremental/cache/mod.ax`
- `tests/run/incremental_cache/incremental_cache_engine.test`
- `tests/run/incremental_cache/incremental_cache_oracle.py`
- `tests/run/incremental_cache/incremental_cache_probe.ax.in`
- `tests/run/incremental_cache/cold_to_warm_cache_and_noop_fastpath.ax`
- `tests/run/incremental_cache/cold_to_warm_cache_and_noop_fastpath.stdout`
- `tests/run/incremental_cache/cache_corruption_and_version_eviction.ax`
- `tests/run/incremental_cache/cache_corruption_and_version_eviction.stdout`
- `tests/run/incremental_cache/clean_vs_cached_artifact_equivalence.ax`
- `tests/run/incremental_cache/clean_vs_cached_artifact_equivalence.stdout`

## Verification
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T758`
- `python build-snap-T758/tools/axtest.py --root build-snap-T758 --build-dir build-snap-T758/build -j 1 run/incremental_cache run/incremental_fingerprint run/query_db run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `WEAK-NATIVE 0`, `TOTAL 40 PASS 40 FAIL 0 SKIP 0 XFAIL 0`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T758` -> `0 REFUSED`
- `python build-snap-T758/tools/archcheck.py` -> `archcheck: 193 files scanned, 0 violations`

STATUS: COMPLETE round=0
