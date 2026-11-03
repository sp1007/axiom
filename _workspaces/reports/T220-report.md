# T220 — Plan phase P20: Build system & package ecosystem

## Tóm tắt
Hoàn tất lập kế hoạch giai đoạn **P20 (`P20-build-system-package-ecosystem`)** theo `spec/ROADMAP.md` §3–§4 và `.claude/agents/axiom-architect.md`. Đã mở rộng đầy đủ 7 epic của P20 (`E20.1`–`E20.7`) thành **28 task cụ thể** (`T850`–`T877`, mỗi epic 4 task: 1 spec task của `axiom-architect` cho `SPEC-110`..`SPEC-116`, 2 task cài đặt của `axiom-frontend`/`axiom-semantics`/`axiom-backend`/`axiom-stdlib`, và 1 task kiểm thử hợp chuẩn của `axiom-qa` với `reviewer: axiom-architect`), nối toàn bộ phụ thuộc với cổng P16 (`T316`), cổng P18 (`T318`) và cổng P20 (`T320`), đồng thời ánh xạ đầy đủ hai chiều toàn bộ yêu cầu P20 (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `REQ-ECO-8734`, `REQ-ECO-8736`) trong `spec/requirements/CATALOG.md` sang mã task cụ thể (`T850`–`T877`).

## Summary

Expanded Phase **P20 (`P20-build-system-package-ecosystem`)** from the 7 epics in `spec/ROADMAP.md` §3 (`E20.1`–`E20.7`) into **28 concrete tasks** (`T850`–`T877`, 4 tasks per epic, all depending on `T220`, P16 gate `T316`, and P18 gate `T318`):

1. **E20.1 — Build graph & driver (`T850`–`T853`)**:
   - `T850` (`axiom-architect`): `spec/SPEC-110-build-graph-driver.md` — declarative `axiom.toml` package/workspace manifests, acyclic package/build/link graph separation (`0168`, `tasks/0356`, `tasks/0372`, `tasks/0661`), deterministic `@cfg` & feature flags (`REQ-PKG-025`), host-vs-target cross-build split (`tasks/0411`), content-addressed cache keys (`SemanticFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, `BuildFingerprint`), and `CompilerDB`-backed workspace CLI (`REQ-PKG-022`, `REQ-PKG-024`).
   - `T851` (`axiom-frontend`): Declarative `axiom.toml` package/workspace manifest parser, feature/`@cfg` evaluator & acyclic package graph builder (`compiler/build/manifest`, `compiler/build/workspace`).
   - `T852` (`axiom-backend`): `CompilerDB` build graph planner, host/target cross-build split, content-addressed cache & workspace CLI (`compiler/build/graph`, `compiler/build/cache`, `compiler/driver/workspace_cmd`).
   - `T853` (`axiom-qa`): Build graph, workspace orchestration, feature/profile determinism & driver CLI conformance suite (`tests/conformance/p20/e20_1_build_graph_driver`).

2. **E20.2 — Package manager, resolution, lockfiles (`T854`–`T857`)**:
   - `T854` (`axiom-architect`): `spec/SPEC-111-package-manager-resolution-lockfiles.md` — `AXPACKAGE` package identity (`0098`, `tasks/0412`, `tasks/0446`, `tasks/1065`), SemVer 2.0 constraint solver, monotonic additive feature unification (`REQ-PKG-025`), side-by-side major-version isolation (`tasks/0661`), and `axiom.lock` reproducibility contract (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-ECO-8736`).
   - `T855` (`axiom-semantics`): Deterministic SemVer 2.0 constraint solver, monotonic feature unifier & side-by-side package version isolation (`compiler/pkg/semver`, `compiler/pkg/resolver`).
   - `T856` (`axiom-stdlib`): Canonical `axiom.lock` serializer/verifier, content-addressed package store, offline vendoring & `axiomc pkg` CLI (`std/pkg/lockfile`, `std/pkg/store`, `compiler/driver/pkg_cmd`).
   - `T857` (`axiom-qa`): `AXPACKAGE` dependency resolution, monotonic feature unification, `axiom.lock` & offline vendoring conformance suite (`tests/conformance/p20/e20_2_package_manager_lockfile`).

3. **E20.3 — Registry & distribution (`T858`–`T861`)**:
   - `T858` (`axiom-architect`): `spec/SPEC-112-package-registry-distribution.md` — Native Application Package Registry & sparse repository protocol (`tasks/0665`, `tasks/0858`, `REQ-ECO-8736`, `REQ-PKG-024`), deterministic `.axpkg` content-addressed archive format, offline mirrors, multi-repository priority/trust routing, and precompiled `.axmeta` binary/interface package consumption (`tasks/0739`).
   - `T859` (`axiom-stdlib`): Deterministic `.axpkg` archive packer/unpacker, Merkle content verifier & sparse/local registry repository client (`std/pkg/archive`, `std/pkg/registry`).
   - `T860` (`axiom-backend`): Multi-repository priority/trust routing, precompiled `.axmeta`/binary package consumption & `axiomc pkg publish|fetch|mirror` CLI (`compiler/pkg/distribution`, `compiler/driver/registry_cmd`).
   - `T861` (`axiom-qa`): Package registry protocol, `.axpkg` deterministic archive, offline mirror & binary/interface distribution conformance suite (`tests/conformance/p20/e20_3_registry_distribution`).

4. **E20.4 — Hermetic/reproducible builds & supply-chain trust (`T862`–`T865`)**:
   - `T862` (`axiom-architect`): `spec/SPEC-113-hermetic-builds-supply-chain-trust.md` — hermetic build sandbox (`tasks/0590`, `REQ-PKG-022`), `--remap-path-prefix` cross-machine reproducibility, dependency capability-escalation policy (`tasks/0449`, `REQ-PKG-024`), Ed25519 package/toolchain signing, provenance attestation, and DDC bootstrap trust (`tasks/0772`).
   - `T863` (`axiom-backend`): Hermetic build sandbox, filesystem/env/network/clock isolation, `--remap-path-prefix` & bit-for-bit reproducibility verifier (`compiler/build/sandbox`, `compiler/build/repro`).
   - `T864` (`axiom-stdlib`): Dependency capability-escalation auditor, Ed25519 package/toolchain signature verifier, provenance attestation & `axiomc trust` CLI (`std/pkg/trust`, `compiler/driver/trust_cmd`).
   - `T865` (`axiom-qa`): Hermetic build sandbox, cross-directory/cross-machine bit-for-bit reproducibility & supply-chain trust conformance suite (`tests/conformance/p20/e20_4_hermetic_supply_chain`).

5. **E20.5 — ABI stability, versioning, binary compatibility (`T866`–`T869`)**:
   - `T866` (`axiom-architect`): `spec/SPEC-114-abi-stability-versioning-binary-compat.md` — three ABI tiers (`Internal`, `Package Interface`, `Stable Binary` via `@abi(stable, version = "...")`; `0104`, `tasks/0452`, `tasks/0583`, `tasks/0739`), Stable Axiom ABI type contract (`REQ-ECO-8734`), distinct `ApiFingerprint`/`SemanticFingerprint`/`AbiFingerprint`, symbol versioning, and `axiomc abi-check` SemVer diff classification (`REQ-PKG-022`, `REQ-PKG-024`).
   - `T867` (`axiom-semantics`): `@abi(stable)` boundary typechecker, `StableStruct`/handle layout verifier & `AbiFingerprint`/`ApiFingerprint` calculator (`compiler/abi/stability`, `compiler/abi/fingerprint`).
   - `T868` (`axiom-backend`): Versioned symbol mangling/export tables, `.axmeta` binary compatibility checker & `axiomc abi-check` SemVer diff CLI (`compiler/abi/compat_diff`, `compiler/driver/abi_cmd`).
   - `T869` (`axiom-qa`): ABI stability tiers, versioned symbol exports, `.axmeta` binary compatibility & `axiomc abi-check` conformance suite (`tests/conformance/p20/e20_5_abi_stability_compat`).

6. **E20.7 — Axiom dynamic components: plugins, hot-reload, versioned Axiom ABI (`T870`–`T873`)**:
   - `T870` (`axiom-architect`): `spec/SPEC-115-dynamic-components-plugins-hot-reload.md` — Axiom-to-Axiom dynamic components (`@component_interface`, `@plugin_export`, `.axcomp` manifest; `tasks/0584`, `tasks/0856`, `0104`, `REQ-ECO-8734`), load-time version/capability negotiation, cross-boundary ownership/capability/allocator isolation (`ComponentBox<T>`, `ComponentHandle<T>`, epoch leases), and state-migrating hot-reload (`Quiesce` → `ExportState` → `LoadNewEpoch` → `MigrateState` → `Resume`).
   - `T871` (`axiom-semantics`): `@component_interface` & `@plugin_export` boundary verifier, cross-component ownership/capability/allocator guard & `.axcomp` emitter (`compiler/component/interface`, `compiler/component/verify`).
   - `T872` (`axiom-stdlib`): `std.component` dynamic plugin loader, version/capability negotiator, epoch lease table & state-hand-off hot-reload runtime (`std/component/loader`, `std/component/hot_reload`).
   - `T873` (`axiom-qa`): Dynamic components, plugin discovery, cross-boundary ownership/capability isolation & hot-reload state migration conformance suite (`tests/conformance/p20/e20_7_dynamic_components_hot_reload`).

7. **E20.6 — SDK / sysroot / toolchain distribution (`T874`–`T877`)**:
   - `T874` (`axiom-architect`): `spec/SPEC-116-sdk-sysroot-toolchain-distribution.md` — C-free Native SDK (`.axsdk`), declarative sysroot metadata, `AXTOOLCHAIN` target/ABI/object-pipeline descriptors (`tasks/0605`, `tasks/1034`), cryptographic `SdkFingerprint` pinning in `axiom.lock` (`REQ-PKG-022`), and hermetic toolchain/sysroot bundle distribution (`REQ-ECO-8736`).
   - `T875` (`axiom-backend`): Declarative `.axsdk` sysroot loader, `SdkFingerprint` verifier, C-free platform import/CRT resolver & `AXTOOLCHAIN` target registry (`compiler/sdk/sysroot`, `compiler/sdk/toolchain`).
   - `T876` (`axiom-stdlib`): Hermetic multi-target SDK/sysroot & toolchain archive packager, `axiom.lock` SDK pinning & `axiomc sdk|toolchain` CLI (`std/sdk/bundle`, `compiler/driver/sdk_cmd`).
   - `T877` (`axiom-qa`): Native SDK/sysroot, `AXTOOLCHAIN` distribution & two-machine lockfile reproducible multi-package workspace conformance suite (`tests/conformance/p20/e20_6_sdk_toolchain_workspace`).

## Files changed

- ./spec/ROADMAP.md
- ./spec/requirements/CATALOG.md
- ./_workspaces/tasks/todo/T320-phase-p20-gate-build-system-package-ecosystem.md
- ./_workspaces/tasks/todo/T475-e12-5-cpu-features-multiversioning-spec.md
- ./_workspaces/tasks/todo/T850-e20-1-build-graph-workspace-driver-spec.md
- ./_workspaces/tasks/todo/T851-e20-1-axiom-toml-manifest-workspace-feature-graph.md
- ./_workspaces/tasks/todo/T852-e20-1-compilerdb-build-graph-cache-workspace-cli.md
- ./_workspaces/tasks/todo/T853-e20-1-build-graph-workspace-driver-conformance.md
- ./_workspaces/tasks/todo/T854-e20-2-axpackage-semver-resolver-lockfile-spec.md
- ./_workspaces/tasks/todo/T855-e20-2-semver-solver-feature-unifier-version-isolation.md
- ./_workspaces/tasks/todo/T856-e20-2-axiom-lock-content-store-vendor-pkg-cli.md
- ./_workspaces/tasks/todo/T857-e20-2-axpackage-resolver-lockfile-conformance.md
- ./_workspaces/tasks/todo/T858-e20-3-package-registry-axpkg-distribution-spec.md
- ./_workspaces/tasks/todo/T859-e20-3-axpkg-archive-merkle-verifier-registry-client.md
- ./_workspaces/tasks/todo/T860-e20-3-multi-repo-routing-binary-pkg-registry-cli.md
- ./_workspaces/tasks/todo/T861-e20-3-registry-distribution-conformance.md
- ./_workspaces/tasks/todo/T862-e20-4-hermetic-build-sandbox-supply-chain-trust-spec.md
- ./_workspaces/tasks/todo/T863-e20-4-hermetic-sandbox-path-remap-repro-verifier.md
- ./_workspaces/tasks/todo/T864-e20-4-capability-audit-ed25519-provenance-trust-cli.md
- ./_workspaces/tasks/todo/T865-e20-4-hermetic-repro-supply-chain-conformance.md
- ./_workspaces/tasks/todo/T866-e20-5-abi-stability-versioning-binary-compat-spec.md
- ./_workspaces/tasks/todo/T867-e20-5-abi-stable-typeck-layout-fingerprint.md
- ./_workspaces/tasks/todo/T868-e20-5-versioned-symbols-axmeta-compat-abi-check-cli.md
- ./_workspaces/tasks/todo/T869-e20-5-abi-stability-binary-compat-conformance.md
- ./_workspaces/tasks/todo/T870-e20-7-dynamic-components-plugins-hot-reload-spec.md
- ./_workspaces/tasks/todo/T871-e20-7-component-interface-boundary-verify-axcomp.md
- ./_workspaces/tasks/todo/T872-e20-7-std-component-loader-lease-hot-reload-runtime.md
- ./_workspaces/tasks/todo/T873-e20-7-dynamic-components-hot-reload-conformance.md
- ./_workspaces/tasks/todo/T874-e20-6-native-sdk-sysroot-axtoolchain-distribution-spec.md
- ./_workspaces/tasks/todo/T875-e20-6-axsdk-sysroot-loader-fingerprint-axtoolchain.md
- ./_workspaces/tasks/todo/T876-e20-6-sdk-toolchain-bundle-lock-pinning-cli.md
- ./_workspaces/tasks/todo/T877-e20-6-sdk-toolchain-two-machine-repro-conformance.md

## Tests

- `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P20-build-system-package-ecosystem --strict` → `5 rows` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` → `v1-full epic=807  implemented=468  planned=7556`, `gaps: 0`, `COVERAGE OK` (`exit 0`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py lint` on `T320` and `T850`–`T877` → `OK` (`29 files`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py validate` → `OK (535 tasks)`
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` → `HARNESS OK`
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T220` → `31 stage, 0 REFUSED`

## Spec deviations

None.

## Follow-ups

None.

STATUS: COMPLETE round=0
