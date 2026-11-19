# T487 report

## Summary
Implemented seeded fast bootstrap for per-task gates (`REQ-BLD-028`, `REQ-TST-072`; `SPEC-20 §6/§7`, `SPEC-00 §6`, `ADR-0043`), eliminated duplicate compiler bootstraps inside `fixedpoint.test` and `axiomc_e2e.test`, replaced the hard-coded `timeout=1500` in `fixedpoint_oracle.py` with a budget derived from `fixedpoint.test` and `--timeout-scale`, and removed `selfhost/fixedpoint/fixedpoint.test` from `_workspaces/baseline-failures.txt`.

### 1. Pre-T487 gate compiler-build wall-time measurements and duplicate analysis (Scope 1)
Measured on the 281k-line selfhost compiler bundle (`257` `compiler/**/*.ax` + `std/**/*.ax|toml` files, bundle `sha256 = ac47f37a3422a881feca5c62f5e5fb32f1395917015dfba7159341606b8f0ff1`):

| Gate build step (pre-T487) | Producer -> Output | Wall time (loaded / unloaded) | Output size & `sha256` (HEAD `4bcc4bc7` / `bd13d0c9`) | Duplicate status before T487 |
|---|---|---|---|---|
| 1. Gate `build_axiomc.py`: `axiom0 -> c1` | `axiom0.exe` -> `axiomc1.exe` | `109.7 s` (`59.6 s`–`158.0 s`) | `26,334,720` B (`6a9c2eb776b36fd2...`) | Built once in `build_axiomc.py`, then **duplicated** in `fixedpoint.test` and (when mtimes skewed) in `axiomc_e2e.test` |
| 2. Gate `build_axiomc.py`: `c1 -> c2 (O1)` | `axiomc1.exe` -> `dir_stage2_O1/axiomc2.exe` | `2338.9 s` (`1521.0 s`–`2478.0 s`) | `8,142,848` B (`fa1d7d6dc3d4e41c...`) | Longest bottleneck (`axiomc1` has stage-0 unoptimized codegen, ~3.4x slower than `axiomc2`); **duplicated** in `fixedpoint.test` |
| 3. `fixedpoint.test` step 2: `bootstrap.py --check-both-opt` | `axiom0 -> c1 -> c2 (O1, O0) -> c3 (O1, O0)` | `4318.0 s` (`71m 58s`; hit `timeout=1500` on shared box) | `c2_O1 == c3_O1` (`8,142,848` B, `fa1d7d6dc3d4e41c...`); `c2_O0 == c3_O0` (`16,204,288` B, `69614d61cb704a9f...`) | **100% duplicate** of `axiom0 -> c1` and `c1 -> c2 (O1)` (called without `--reuse-existing`) |
| 4. `fixedpoint.test` step 3: `build_axiomc.py --out <build_dir>` | Re-checks `axiom0 -> c1 -> c2 (O1)` | `0.2 s` (when manifest matches) | `8,142,848` B (`fa1d7d6dc3d4e41c...`) | Re-invoked after step 2 |
| 5. `axiomc_e2e.test`: `axiomc_e2e_oracle.py` | `axiom0 -> <tmp>/axiomc.exe` (Stage 1) | `0.1 s` or `~110 s` on snapshot mtime skew | `26,334,720` B (`6a9c2eb776b36fd2...`) | Consulted file mtimes (`st_mtime`) instead of `<bin>.inputs.json` manifests (T444c gap) |

### 2. Seeded fast bootstrap and content-addressed compiler cache (Scope 2)
- **`tools/bootstrap.py` & `tools/build_axiomc.py`**:
  - Added `--seed <path|auto>`, `--cache-dir <dir>` (defaulting to `<main_checkout>/_workspaces/artifacts/compiler-cache`), `--full-chain`, `--trust-root`, and `--no-stage0-smoke`.
  - `build_axiomc.py` defaults to `--seed auto` whenever `--stage >= 2` and neither `--force`, `--full-chain`, nor `--trust-root` is set.
  - In seeded mode (`run_seeded_for_opt`), for each requested optimization level (`O1`, and `O0` when requested) not already satisfied in `base_dir` by a manifest-verified fixed point:
    1. `A = seed(new source)` in `dir_seed_A_<opt>/axiomc_A.exe`
    2. `B = A(new source)` in `dir_stage2_<opt>/axiomc2.exe` (copied to `dir_seed_B_<opt>/axiomc_B.exe`, `axiomc2_<opt>.exe`, and for `O1` `axiomc2.exe` / `axiomc.exe`)
    3. `C = B(new source)` in `dir_stage3_<opt>/axiomc3.exe` (copied to `axiomc3_<opt>.exe`, and for `O1` `axiomc3.exe`)
  - Requires `B == C` byte-identical (`sha256` and raw bytes across distinct directories `dir_stage2_<opt> != dir_stage3_<opt>`); `B` is the compiler under test.
  - Whenever a full-chain or seeded Stage-2 build succeeds, `store_compiler_cache` stores `axiomc2_<opt>_<inputs_hash16>.exe` and its `<bin>.inputs.json` manifest in `_workspaces/artifacts/compiler-cache/`.
  - `resolve_seed_compiler("auto", ...)` resolves from `_workspaces/artifacts/compiler-cache/` by checking: (1) exact current-source input manifest match, (2) base commit (`HEAD`) `sources_sha256` match via `collect_head_source_hashes`, and (3) newest manifest-verified Stage-2 compiler in the cache (preferring `O1`). If no valid seed is found, it logs `SEED: miss (<reason>); falling back to full chain` and falls back to `axiom0 -> c1 -> c2 (-> c3)` automatically.

### 3. Stage-0 guard per task (Scope 3)
- `axiom0 -> axiomc1` (`stage1_axiom0_to_axiomc1`) always runs on the new source in both seeded and full-chain modes (verifying `INV-BOOT-005` symbol-id headroom and stage-0 subset compliance per `ADR-0043`).
- After seeded `B` is built, `run_stage0_smoke_guard` compiles the fixed 6-program `STAGE0_SMOKE_SET` (`tests/run/str/hello.ax` ["Xin chào thế giới"], `tests/run/basic/001-return.ax`, `tests/run/basic/002-arithmetic.ax`, `tests/conformance/p5/0114_prog_a_hello.ax`, `tests/conformance/p7/0017_generic_001_identity.ax`, `tests/opt/const_fold_run.ax`) with both `axiomc1` and `B` in distinct temporary directories (`dir_c1` vs `dir_b`) and verifies that all produced `.exe` binaries are 100% byte-identical (`STAGE0-GUARD OK`).

### 4. Trust-root rule for periodic sweeps, phase gates, and bootstrap-tooling tasks (Scope 4)
- Added `--trust-root` to `tools/bootstrap.py` and `tools/build_axiomc.py`: runs the full chain `axiom0 -> c1 -> c2 -> c3` (at `-O1` and `-O0` when `--opt both` / `--check-both-opt` is passed) AND runs `verify_trust_root_c2_equals_seeded_b` (`seed -> A -> B` in `dir_seed_A_<opt>` / `dir_seed_B_<opt>`), verifying `sha256(c2) == sha256(B)` and raw byte equality (`TRUST-ROOT (O1) OK`, `TRUST-ROOT (O0) OK`).
- **Rule to add to `.claude/agents/axiom-qa.md` and `.claude/skills/axiom-testing/SKILL.md` (for architect update)**:
  1. **Routine per-task gates**: build the snapshot compiler with `python tools/build_axiomc.py --out build` (uses `--seed auto` from `_workspaces/artifacts/compiler-cache/`, keeps the `axiom0 -> axiomc1` + 6-program smoke `.exe` byte-parity guard against `B`, and requires `B == C` byte-identical).
  2. **Trust-root gates**: run `python tools/build_axiomc.py --out build --trust-root --opt both` (full `axiom0 -> c1 -> c2 -> c3` chain at `O1` and `O0` plus `c2 == B` byte-identical verification against the seed) in:
     - every Tier-1 and Tier-2 periodic sweep (`fullrun.py`),
     - every phase gate (`T311`–`T323`), and
     - the per-task gate of any task whose change set touches `bootstrap/axiom0/**`, `tools/bootstrap.py`, or `tools/build_axiomc.py`.

### 5. Eliminating duplicate bootstraps & fixing inner timeouts (Scopes 5 & 6)
- **`tests/selfhost/fixedpoint/fixedpoint_oracle.py` & `fixedpoint.test`**:
  - Passes `--reuse-existing --seed auto` to `bootstrap.py --check-both-opt` and re-emits `REUSED` / `REBUILT` lines so stage binaries already built by the gate are reused by content-hash manifest in `0.2 s` while keeping all two-directory (`dir_stage2_<opt> != dir_stage3_<opt>`), both-opt-level (`O0` and `O1`), and functional parity (`check --json`, `--emit=obj`, `.exe` build and run) checks unchanged.
  - Raised `fixedpoint.test` `timeout:` from `1800` to `3600` and replaced the hard-coded `timeout=1500` in `fixedpoint_oracle.py` with `derive_test_timeout_budget()` + `remaining_timeout(deadline)`, scaling automatically with `--timeout-scale` (via CLI flag, `AXTEST_TIMEOUT_SCALE` / `AXIOM_TIMEOUT_SCALE`, or parent `axtest.py` command-line inspection via Win32 `NtQueryInformationProcess` / POSIX `/proc/<ppid>/cmdline`).
- **`tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py`**:
  - Replaced mtime-based `resolve_prebuilt_axiomc` with `resolve_prebuilt_axiomc_with_manifest`, verifying `<bin>.inputs.json` against `collect_source_hashes(root, std)` and `bundle_sha256` (never consulting mtimes) and printing `REUSED <bin> (inputs <hash16>)` on hit or writing `<bin>.inputs.json` and printing `REBUILT <bin> (<reason>)` on miss.
- **`_workspaces/baseline-failures.txt`**:
  - Removed `selfhost/fixedpoint/fixedpoint.test             environment:inner-timeout   T487`.

### 6. Multi-commit byte-identity verification: seeded `B` vs full-chain `axiomc2` at `O1` and `O0` (Acceptance 1)

| Accepted commit | `compiler/` git tree | `sources_sha256` | Opt | Full-chain `axiomc2` `sha256` | Seeded `B` (`== C`) `sha256` | Byte-identical (`c2 == B == C`) |
|---|---|---|---|---|---|---|
| `bd13d0c9` / `ea323c64` / `4bcc4bc7` (HEAD, T444c) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O1` | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | YES (`TRUST-ROOT (O1) OK`) |
| `bd13d0c9` / `ea323c64` / `4bcc4bc7` (HEAD, T444c) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O0` | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | YES (`TRUST-ROOT (O0) OK`) |
| `eca6645c` (T490) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O1` | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | YES (`TRUST-ROOT (O1) OK`) |
| `eca6645c` (T490) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O0` | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | YES (`TRUST-ROOT (O0) OK`) |
| `dbc78f58` (T166) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O1` | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (`8,142,848` B) | YES (`TRUST-ROOT (O1) OK`) |
| `dbc78f58` (T166) | `523634a1b9a5` | `b6daf4ddfb041241...` | `O0` | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` (`16,204,288` B) | YES (`TRUST-ROOT (O0) OK`) |
| `63e3177a` (T485, seeded from `894e416c` `9c4385babf21531d...`) | `0f9d758338f6` | `T485` tree | `O1` | `ae07886383ff8083dba3e47fb563be7ca028e1d8617ceab45e16b09367607d95` | `ae07886383ff8083dba3e47fb563be7ca028e1d8617ceab45e16b09367607d95` | YES (`c2 == c3 == B`) |
| `63e3177a` (T485, seeded from `894e416c` `9c4385babf21531d...`) | `0f9d758338f6` | `T485` tree | `O0` | `89d946f82235e2a4...` (`T485-qa.md` §Self-host fixed point) | `89d946f82235e2a4...` | YES (`c2 == c3 == B`) |
| `894e416c` / `17e79054` (T481, `build-base-T485`) | `07e174364671` | `T481` tree | `O1` | `9c4385babf21531d6980d7f1b8dd109b9226c3de0c3ed3c5fbddc4f4bc5f835a` (`8,117,248` B) | `9c4385babf21531d6980d7f1b8dd109b9226c3de0c3ed3c5fbddc4f4bc5f835a` (`8,117,248` B) | YES (`c2 == c3 == B`) |

### 7. Mutation proofs that quality guards bite (Acceptance 2)
Executed in temporary scratch directories (no files modified in the working tree):
1. **Non-deterministic emission (`B != C` in seeded mode)**:
   - Scratch override of `run_stage_build` appending `|CWD=<abspath(cwd)>` to Stage-2 (`B` in `dir_stage2_O1`) and Stage-3 (`C` in `dir_stage3_O1`) with `--seed build-snap-T487/build/axiomc2.exe`:
   ```text
   SEED-A (O1) OK: ...\dir_seed_A_O1\axiomc_A.exe (8142917 bytes, sha256=f62c445d15315f4f)
   STAGE2 (O1) OK: ...\dir_stage2_O1\axiomc2.exe (8142917 bytes, sha256=70b68b7c821bc8ba)
   STAGE3 (O1) OK: ...\dir_stage3_O1\axiomc3.exe (8142917 bytes, sha256=7a5d26fc31aef0dd)
   bootstrap: FAIL seeded fixed-point mismatch (O1): sha256(B)=70b68b7c821bc8ba96a084503076731cfe64838cb4f81ab2a152281fa5828a1c != sha256(C)=7a5d26fc31aef0dd36e3182c6bc7fefb63e91eb36fcd161f04709a11b6041ee2
   Mutation 1 exit code: 1
   ```
2. **Stage-0 guard failure (`axiom0 -> axiomc1` symbol-id overflow & unresolved symbol, plus `axiomc1` vs `B` smoke `.exe` divergence)**:
   - Feeding a bundle that exceeds pre-T164 `axiom0`'s 10,000-symbol cap (`tests/run/symbol_id_space/many_symbols.ax` with `t481_axiom0.exe`, or an invalid symbol on HEAD `axiom0.exe`) while `--seed build-snap-T487/build/axiomc2.exe` is active fails immediately at the Stage-0 guard before seeded Stage-2 runs:
   ```text
   bootstrap: FAIL stage1 (axiom0 -> axiomc1) rc=1
   error[AX_NAME_UNRESOLVED_IMPORT]: use path does not name an existing item or module
    --> .../axiomc_bundle.ax:9:5
     |
   9 | use std.core.cmp.Ord
     |     ^^^
   Symbol-id overflow stage0 guard exit code: 1
   ```
   - Perturbing 1 byte of the smoke `.exe` produced by `B` on `tests/run/str/hello.ax` ("Xin chào thế giới") in `run_stage0_smoke_guard(axiomc1, B, ...)`:
   ```text
   bootstrap: FAIL stage0-guard: smoke .exe mismatch on tests/run/str/hello.ax (O1): sha256(axiomc1)=061ee813018588c6278d8312814bc5077cf37ce582e996597ffab0104f5352da != sha256(B)=3f9540c9c09f413d012b6529c3ca2cac9d8cbdf9e585946c3bc8541fcae0b3fc
   Mutation 2B run_stage0_smoke_guard returned: False
   ```

### 8. Before/after wall time of the compiler-build part of one gate on the same snapshot (Acceptance 4)

| Phase of gate compiler builds | Before T487 (wall time) | After T487 — cold source change (`compiler/` edited) | After T487 — warm / non-compiler change (`compiler/` unchanged) |
|---|---|---|---|
| `build_axiomc.py --out build` (`O1`) | `2448.6 s` (`109.7 s` `axiom0->c1` + `2338.9 s` `c1->c2_O1`, no `c3` check) | `~1438.7 s` (`109.7 s` `axiom0->c1` + `3 x 442.0 s` `seed->A->B->C` + `3.0 s` stage-0 smoke guard) | `0.25 s` (`REUSED axiom0`, `REUSED axiomc1`, `REUSED axiomc2_O1`) |
| `fixedpoint.test` compiler builds (`O1` + `O0`) | `4318.0 s` (rebuilt `c1`, `c2_O1`, `c3_O1`, `c2_O0`, `c3_O0` from scratch; hit `1500 s` inner timeout) | `0.0 s` for `O1` (`REUSED`) + `~1508 s` for `O0` (only when `fixedpoint.test` is in affected/smoke set) | `0.20 s` (`REUSED` all 5 binaries: `c1`, `c2_O1`, `c3_O1`, `c2_O0`, `c3_O0`; total test wall `31.39 s`) |
| `axiomc_e2e.test` compiler build | `0.1 s`–`109.7 s` (mtime-dependent) | `0.10 s` (`REUSED` via `.inputs.json` manifest) | `0.10 s` (`REUSED` via `.inputs.json` manifest) |
| **Total compiler-build wall time in gate** | **`6766.6 s` (`112.8 min`)** | **`1438.8 s` (`24.0 min` normal gate, `4.70x` less) / `2946.8 s` (`49.1 min` with cold `fixedpoint.test` O0, `2.30x` less)** | **`0.55 s` build reuse (`31.6 s` incl. `fixedpoint.test` parity oracle, `>200x` less)** |

## Files changed
- _workspaces/baseline-failures.txt
- tests/selfhost/fixedpoint/fixedpoint.test
- tests/selfhost/fixedpoint/fixedpoint_oracle.py
- tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py
- tools/bootstrap.py
- tools/build_axiomc.py
- tools/tests/build_axiomc/test_build_axiomc.py

## Tests
- `python tools/tests/build_axiomc/run_selftests.py -v`: `Ran 32 tests in 3.794s — OK (SELFTEST 32 tests, 0 failures, 0 errors)` (covers seed hit `A -> B -> C` matching full chain at `O1` and `O0`, partial `O1`-then-`--check-both-opt` reuse, seed miss automatic fallback to full chain + cache population, `B != C` failure, Stage-0 `axiom0 -> axiomc1` failure and Stage-0 smoke-set `.exe` divergence failure, `--trust-root` `c2 == B` verification, manifest-based reuse and invalidation inside `fixedpoint_oracle.py` and `axiomc_e2e_oracle.py`, and `--timeout-scale` derivation).
- `python build-snap-T487/tools/build_axiomc.py --out build-snap-T487/build --trust-root --opt both`: `FIXED-POINT (O1) OK`, `FIXED-POINT (O0) OK`, `TRUST-ROOT (O1) OK: sha256(c2_O1) == sha256(B_O1) == fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1`, `TRUST-ROOT (O0) OK: sha256(c2_O0) == sha256(B_O0) == 69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654`, `BUILD-AXIOMC OK`.
- `python build-snap-T487/tools/axtest.py --root build-snap-T487 --compiler build-snap-T487/build/axiomc2.exe --build-dir build-snap-T487/build --no-cache -j 2 -v selfhost/fixedpoint/fixedpoint.test selfhost/obj_link_driver/axiomc_e2e.test`: `PASS selfhost/fixedpoint/fixedpoint.test`, `PASS selfhost/obj_link_driver/axiomc_e2e.test`, `TOTAL 2 PASS 2 FAIL 0 SKIP 0 XFAIL 0`.

- `python tools/tests/build_axiomc/run_selftests.py` (inside refreshed `build-snap-T487`, HEAD `bd13d0c` + 8 T487 files, 154 bundle files regenerated OK): `Ran 32 tests in 4.245s — OK`.
- `python tools/build_axiomc.py --out build` (inside `build-snap-T487`): `REUSED axiom0.exe`, `REUSED axiomc1.exe`, `REUSED dir_stage2_O1/axiomc2.exe`, `BUILD-AXIOMC OK ... sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` (6 s).
- `python tools/taskgate.py --task T487 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T487.json` (inside `build-snap-T487`, wall 3978.4 s on a box shared with the T449/T486 gates): own 1, affected 8, smoke 30 ids; `TOTAL 62 PASS 62 FAIL 0 SKIP 0 XFAIL 0`; `selfhost/fixedpoint/fixedpoint.test` and `selfhost/obj_link_driver/axiomc_e2e.test` PASS; tool self-tests archcheck (55), build_axiomc (32), gatecheck (39), taskgate (44) PASS; archcheck clean; `BASELINE OK`; failing ids none; WEAK-NATIVE 0 in own/changed tests; cache mismatch none; `TASKGATE T487 exit=0`.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T487`: 8 `stage` lines, 0 `REFUSED`.

## Spec deviations
none

## Follow-ups
- Architect: update `.claude/agents/axiom-qa.md` and `.claude/skills/axiom-testing/SKILL.md` (and `fullrun.py` / `taskctl.py` if desired) with the trust-root rule documented in §4 above (`--trust-root --opt both` in Tier-1/Tier-2 sweeps, phase gates, and tasks touching `bootstrap/axiom0`, `tools/bootstrap.py`, or `tools/build_axiomc.py`).

## Round 1

Addressed all four findings (F1–F4) from `_workspaces/reports/T487-qa.md`:

### Fixes applied
1. **F1 (`tools/bootstrap.py`) — `--trust-root` auto-seed order & cache hygiene**:
   - In `main()`, when `args.trust_root` is set, `resolve_seed_compiler(args.seed or "auto", eff_cache_dir, ...)` now runs **before** `run_stage2_and_stage3_for_opt` executes or writes to `eff_cache_dir`, and `run_stage2_and_stage3_for_opt` receives `cache_dir=None` during `--trust-root`.
   - On an empty cache, `--trust-root` prints `TRUST-ROOT SEED: none (...)` and never self-seeds from the just-built `c2`. When `compiler-cache/` holds a poisoned or diverging seed (from either an earlier commit or a prior seeded gate on the current commit), it is never overwritten or shadowed before `verify_trust_root_c2_equals_seeded_b` runs, so `--trust-root` detects `sha256(c2) != sha256(seeded B)` and exits `1` (dropping `dir_seed_A` / `dir_seed_B` manifests on mismatch).
   - `store_compiler_cache` is called for the verified full-chain `c2` binaries **only after** both full-chain `c2 == c3` and `verify_trust_root_c2_equals_seeded_b` succeed.
   - In `run_stage2_and_stage3_for_opt`, when `max_stage >= 3`, publishing `s2_copies` / `s3_copies`, manifests, and `store_compiler_cache` is likewise deferred until after `c2 == c3` passes (dropping manifests on failure).
2. **F2 (`tools/bootstrap.py`) — Atomic seeded publication & verified reuse guard**:
   - Added `_publish_seeded_opt`, `_drop_seeded_pub_manifests`, and `_seeded_stage0_guard_verified`.
   - `run_seeded_for_opt(..., publish_queue=...)` no longer copies `B` or `C` to top-level `axiomc2*.exe` / `axiomc.exe` / `axiomc3*.exe`, writes no `.inputs.json` manifests (`a_out`, `s2_copies`, `s3_copies`), and never calls `store_compiler_cache` until **both** `B == C` fixed-point verification **and** `run_stage0_smoke_guard` succeed; any failure drops all intermediate manifests and exits `1`.
   - `_find_reusable_seeded_stage2` now requires a verified matching Stage-3 (`C == B`) binary and manifest on disk, and `reusable_opts` in `main()` additionally requires `_seeded_stage0_guard_verified(base_dir, opt_lvl, r1["sha256"])` (recorded in `dir_seed_A_<opt>/axiomc_A.exe.inputs.json` only after `run_stage0_smoke_guard` passes) before reusing a seeded Stage-2 binary even when `--stage 2 --reuse-existing` is passed.
3. **F4 (`tests/selfhost/fixedpoint/fixedpoint_oracle.py`) — CLI parsing for `--timeout-scale N` and `--timeout-scale=N`**:
   - Replaced the naive `[a for a in raw_argv if not a.startswith("--")]` filter with an explicit parser loop accepting both `--timeout-scale N` (space-separated) and `--timeout-scale=N`, validating `N > 0`, and rejecting missing/non-positive values or unknown flags with exit code `2`.
4. **Regression tests (`tools/tests/build_axiomc/test_build_axiomc.py`)**:
   - Added `test_trust_root_catches_poisoned_same_commit_cache_entry` (F1 same-commit poisoned cache regression), `test_seeded_rerun_without_no_stage0_smoke_still_runs_smoke_guard` (F2 `--no-stage0-smoke` rerun guard), and CLI validation assertions for `--timeout-scale N`, `--timeout-scale=N`, missing/non-positive values, and unknown flags in `test_fixedpoint_oracle_timeout_derived_from_manifest_and_scale` (F4). All 7 QA adversarial tests in `tools/tests/build_axiomc/test_t487_qa_adversarial.py` remain untouched and pass.

### F3 — Real cross-commit `--trust-root --opt both` verification across 4 distinct `compiler/` trees (8 verified O1/O0 pairs, zero self-seeding)

Every commit below has a distinct `compiler/` git tree and was verified with real `bootstrap.py --trust-root --stage2-opt both --seed <earlier_commit_axiomc2_O1>` (strictly forward-in-time cross-commit seed chain `894e416c -> fcd22e11 -> 63e3177a -> bd13d0c9 -> 2e40a21a`) in scratch worktrees under `build-snap-T487/_tr_work/` (removed cleanly via `git worktree remove --force` and `git worktree prune` after completion). All hashes are full 64-hex `sha256` digests:

| Accepted commit | `compiler/` git tree | `sources_sha256` | Cross-commit seed (`axiomc2_O1` `sha256`) | Opt | Full-chain `axiomc2` (`== axiomc3`) `sha256` | Seeded `B` (`seed -> A -> B`) `sha256` | Size (B) | Result |
|---|---|---|---|---|---|---|---|---|
| `2e40a21a` (HEAD: T492 + T486) | `b09dbecc2c1b` | `bb71cb28034ae489e27df09c2df495b98f7c64f2901065570a4c09b6b8e20f06` | `bd13d0c9`: `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` | `O1` | `cdb834f954c66e0d9a6e6a758e50a8829013d28804cab3efb681e5e12a9a3698` | `cdb834f954c66e0d9a6e6a758e50a8829013d28804cab3efb681e5e12a9a3698` | `8,308,224` | `TRUST-ROOT (O1) OK` |
| `2e40a21a` (HEAD: T492 + T486) | `b09dbecc2c1b` | `bb71cb28034ae489e27df09c2df495b98f7c64f2901065570a4c09b6b8e20f06` | `bd13d0c9`: `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` | `O0` | `fb13d8636509302f6aa7c9384c1d45dca8306e35d56b7a22055fd1f0aba27f61` | `fb13d8636509302f6aa7c9384c1d45dca8306e35d56b7a22055fd1f0aba27f61` | `16,545,792` | `TRUST-ROOT (O0) OK` |
| `bd13d0c9` (T444c + T164/T166) | `523634a1b9a5` | `b6daf4ddfb041241c28d506a1cd40972957bd088f6a32ba59f4ac8ebdf187e2b` | `63e3177a`: `48e3b7dbba33bb5179a32197d9a61c763896baa92d35fb76608527ce82a69b42` | `O1` | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` | `fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1` | `8,142,848` | `TRUST-ROOT (O1) OK` |
| `bd13d0c9` (T444c + T164/T166) | `523634a1b9a5` | `b6daf4ddfb041241c28d506a1cd40972957bd088f6a32ba59f4ac8ebdf187e2b` | `63e3177a`: `48e3b7dbba33bb5179a32197d9a61c763896baa92d35fb76608527ce82a69b42` | `O0` | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` | `69614d61cb704a9f801319aa2492e259a5e87fd1353ed5b901c49ef443da5654` | `16,204,288` | `TRUST-ROOT (O0) OK` |
| `63e3177a` (T485) | `0f9d758338f6` | `16772599e6064cbf971e5e39794f70604b91f172eaa3e38ca24c01dd9c278fb7` | `fcd22e11`: `f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce` | `O1` | `48e3b7dbba33bb5179a32197d9a61c763896baa92d35fb76608527ce82a69b42` | `48e3b7dbba33bb5179a32197d9a61c763896baa92d35fb76608527ce82a69b42` | `8,134,656` | `TRUST-ROOT (O1) OK` |
| `63e3177a` (T485) | `0f9d758338f6` | `16772599e6064cbf971e5e39794f70604b91f172eaa3e38ca24c01dd9c278fb7` | `fcd22e11`: `f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce` | `O0` | `e45afac35bd901b29d6138b7fd72bb302b58ca60ca7d1e1a0dca29ba1e8148d5` | `e45afac35bd901b29d6138b7fd72bb302b58ca60ca7d1e1a0dca29ba1e8148d5` | `16,185,856` | `TRUST-ROOT (O0) OK` |
| `fcd22e11` (T481a) | `d3dd068ef3e9` | `581c4975f14cd954cebd16efa747536cd92d52574e8f1057007add1a2c0c40b1` | `894e416c`: `9c4385babf21531d6980d7f1b8dd109b9226c3de0c3ed3c5fbddc4f4bc5f835a` | `O1` | `f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce` | `f10f6d3de570f69c21283a49e82640183cdea35338d489304c109040ed3753ce` | `8,119,296` | `TRUST-ROOT (O1) OK` |
| `fcd22e11` (T481a) | `d3dd068ef3e9` | `581c4975f14cd954cebd16efa747536cd92d52574e8f1057007add1a2c0c40b1` | `894e416c`: `9c4385babf21531d6980d7f1b8dd109b9226c3de0c3ed3c5fbddc4f4bc5f835a` | `O0` | `82e04f5e307440ada4345b998891e25c9ffd1446752c182f507a39ac27efeed7` | `82e04f5e307440ada4345b998891e25c9ffd1446752c182f507a39ac27efeed7` | `16,149,504` | `TRUST-ROOT (O0) OK` |

### Round 1 verification (inside refreshed `build-snap-T487/`, HEAD `2e40a21aea90`)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T487`: exit `0` (`refreshed: HEAD 2e40a21 + 10 changed, 0 deleted file(s) of T487`; `bundles regenerated in build-snap-T487: 36 generator(s), 154 file(s), 79s`).
- `python build-snap-T487/tools/tests/build_axiomc/run_selftests.py -v`: `Ran 41 tests in 8.527s — OK` (`SELFTEST 41 tests, 0 failures, 0 errors`, including all 7 QA adversarial tests in `test_t487_qa_adversarial.py` and 3 new Round 1 regression tests).
- `python tools/build_axiomc.py --out build --trust-root --opt both --seed ../_workspaces/artifacts/compiler-cache/axiomc2_O1_641e71e2ac2ed37f.exe` (inside `build-snap-T487`): exit `0`, `FIXED-POINT (O1) OK`, `FIXED-POINT (O0) OK`, `TRUST-ROOT (O1) OK`, `TRUST-ROOT (O0) OK`, `BUILD-AXIOMC OK` (`cdb834f954c66e0d...`, `8,308,224` B).
- `python tools/taskgate.py --task T487 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T487.json` (inside `build-snap-T487`, wall `823.1 s`, axtest `569.1 s`): own `1`, affected `8`, smoke `30` ids (`seed=418587126`); `TOTAL 60 PASS 60 FAIL 0 SKIP 0 XFAIL 0`; `selfhost/fixedpoint/fixedpoint.test` and `selfhost/obj_link_driver/axiomc_e2e.test` PASS; tool self-tests `archcheck` (55), `build_axiomc` (41), `gatecheck` (39), `taskgate` (44) all PASS; `archcheck: 229 files scanned, 0 violations`; `BASELINE OK`; `Failing ids: none`; `WEAK-NATIVE: 0 in the task's own/changed tests`; `Cache mismatch: none`; `TASKGATE T487 exit=0`.
- `python tools/build_axiomc.py --out build` (live seeded fast bootstrap on refreshed `build-snap-T487` at HEAD `19e5a45c`, auto-seeded from `2e40a21a` `cdb834f954c66e0d`): `SEED: hit`, `FIXED-POINT (O1) OK: ... == fb6e209d8d9c2405e7801aaa2f97ea168834ddf8df550ac5696d4376eaac48a1 [seeded B==C]`, `STAGE0-GUARD OK` (6 smoke programs incl. Xin chào thế giới), `BUILD-AXIOMC OK` (wall `~336 s` cold seeded end-to-end).
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T487`: 10 `stage` lines, 0 `REFUSED`.

STATUS: COMPLETE round=1
