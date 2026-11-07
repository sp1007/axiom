# T757 — E18.2 API, Body, and Codegen Fingerprints + Red-Green Change Propagation

## Summary

Implemented the multi-tier incremental fingerprint hierarchy and red-green (`try_mark_green`) change propagation engine over `CompilerDB` (`compiler/incremental/fingerprint/mod.ax`, `module compiler.incremental.fingerprint`) per `spec/SPEC-22-incremental-compilation.md` (`AXS-INC-001..024`, `AXS-INC-050..053`, `INV-INC-001`):

1. **Multi-Tier Domain-Separated 128-bit Fingerprints (`AXS-INC-001..004`, `AXS-INC-020..021`)**:
   - Implemented `FpStream128` 128-bit content-addressed hashing with explicit domain tags (`AXFP:v1:Source:0`, `AXFP:v1:Ast:1`, `AXFP:v1:Interface:2`, `AXFP:v1:Abi:3`, `AXFP:v1:Body:4`, `AXFP:v1:Codegen:5`, `AXFP:v1:Artifact:6`, `AXFP:v1:Action:7`), tagged scalar/string/key encoding, and zero dependency on host pointers, timestamps, or sequential `DefId`/`ModuleId` allocation indices.
   - `SourceFingerprint` (Tier 0): normalized logical path, LF-normalized byte length, and raw UTF-8 text digest.
   - `AstFingerprint` & `AstItemFingerprint` (Tier 1): comment/whitespace-insensitive canonical token stream and per-item header/body AST digests (`fp_skip_ws_and_nondoc_comments`, `fp_hash_canonical_tokens`) that strip whitespace, `//` line comments, and nested `/* ... */` block comments while preserving `///` and `//!` doc comments.
   - `InterfaceFingerprint` (Tier 2A) & `AbiFingerprint` (Tier 2B): canonical exported module/item API surface and `@repr`/`@align`/calling-convention/size/alignment layout digest sorted by `SemanticKey`. Private items and function bodies never enter `InterfaceFingerprint(M)`.
   - `BodyFingerprint` (Tier 3) & `CodegenFingerprint` (Tier 4): Verified MIR body digest and monomorphized CGU digest tracking `TargetConfig`, direct `AbiFingerprint` dependencies, `@inline` body dependencies (`DEP_KIND_INLINED_BODY`), generic body instantiations (`DEP_KIND_GENERIC_BODY`), and `const` evaluation values (`DEP_KIND_CONST_BODY`).

2. **Red-Green Verification (`try_mark_green`) & Private-Body Firewall (`AXS-INC-010..013`)**:
   - Implemented `RedGreenNode` (`Unknown`, `Green`, `Red`), `TypedDepEdge` (`DependencyKind` + `observed_fp`), `inc_try_mark_green`, and `inc_ensure_node_evaluated` with backdating (`was_backdated = true` when recomputed output equals the prior fingerprint).
   - Enforced the private-body firewall (`AXS-INC-012`): editing a non-inlined function body or private helper re-typechecks only the defining module (`0` downstream `typeck_body` queries re-run) and reuses downstream `codegen_unit`s; editing an `@inline` body invalidates only callers' `codegen_unit`s while keeping caller `typeck_body` green; editing a `const` body whose evaluated `ConstValue` is unchanged (`100` -> `60 + 40`) backdates `const_eval` to `Green`.
   - Implemented deterministic `fp_emit_fingerprints` (`--emit=fingerprints`) and `fp_emit_incremental_stats` (`--emit=incremental-stats`) sorted lexicographically by `SemanticKey` and `(node_kind, SemanticKey)`.

3. **Differential & Live Oracle Tests (`tests/run/incremental_fingerprint/`)**:
   - Added differential `.ax` tests (`modes: interp native`) covering comment/whitespace insensitivity, private-body firewall & red-green backdating, and signature/ABI invalidation.
   - Added live bundle probe + oracle (`incremental_fingerprint_engine.test`, `incremental_fingerprint_oracle.py`, `incremental_fingerprint_probe.ax.in`) compiling `compiler/incremental/fingerprint/mod.ax` with `axiomc2.exe` across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.

## Files changed

- compiler/incremental/fingerprint/mod.ax
- tests/run/incremental_fingerprint/comment_whitespace_insensitivity.ax
- tests/run/incremental_fingerprint/comment_whitespace_insensitivity.stdout
- tests/run/incremental_fingerprint/incremental_fingerprint_engine.test
- tests/run/incremental_fingerprint/incremental_fingerprint_oracle.py
- tests/run/incremental_fingerprint/incremental_fingerprint_probe.ax.in
- tests/run/incremental_fingerprint/private_body_firewall_red_green.ax
- tests/run/incremental_fingerprint/private_body_firewall_red_green.stdout
- tests/run/incremental_fingerprint/signature_abi_invalidation.ax
- tests/run/incremental_fingerprint/signature_abi_invalidation.stdout

## Verification

- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T757`
- `python build-snap-T757/tools/build_axiomc.py --root build-snap-T757 --out build-snap-T757/build` (stage1 + stage2 fixed-point verified: `axiomc2.exe sha256=7b92aaa3416b5cb88b8563d58b6e821b763b97988e6d263470fb04f1566eac5b`)
- `python build-snap-T757/tools/axtest.py --compiler build-snap-T757/build/axiomc2.exe --root build-snap-T757 -j 1 -v run/incremental_fingerprint` -> `TOTAL 10 PASS 10 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)
- `python build-snap-T757/tools/axtest.py --compiler build-snap-T757/build/axiomc2.exe --root build-snap-T757 -j 1 -v run/query_db run/intrinsics/assert_false.ax run/intrinsics/panic_abort.ax ui/intrinsics/unknown_intrinsic.ax` -> `TOTAL 17 PASS 17 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`)
- `python tools/archcheck.py` -> `194 files scanned, 0 violations`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T757` -> `10 allowed, 0 refused`

STATUS: COMPLETE round=0
