# T087 Report — Stage-2/3 fixed point + reproducible bootstrap (VS2 of 0263 §51)

## Summary

Implemented and verified the Stage-2 / Stage-3 reproducible fixed-point bootstrap (`VS2` of `0263 §51`, `BOOT-36..38`, `MS-P10b`):
1. Updated `tools/bootstrap.py` to build Stage 2 (`axiomc1 -> axiomc2`) and Stage 3 (`axiomc2 -> axiomc3`) in two distinct directories (`dir_stage2_<opt>` and `dir_stage3_<opt>`) with identical flags and host C/assembler/linker toolchains (`gcc`, `clang`, `ld`, `as`, `link`, `cl`, `lld`) stripped from `PATH` (`INV-BOOT-003`, `ABOOT-74/75`), verifying byte-identical SHA-256 and raw-byte equality at **both `-O0` and `-O1`** (`INV-DET-004`).
2. Created `tools/build_axiomc.py`, the standard per-task Stage-2 compiler build driver (`python tools/build_axiomc.py --out build-snap-<ID>/build`).
3. Created `tests/selfhost/fixedpoint/fixedpoint.test` and `tests/selfhost/fixedpoint/fixedpoint_oracle.py` to verify two-directory fixed-point equality at `-O0` and `-O1`, `PATH` hermeticity, `tools/build_axiomc.py`, and functional equivalence (`check --json`, `--emit=obj`, `.exe`, and runtime execution) between `axiomc1`, `axiomc2`, and `axiomc3`.
4. Created `spec/BOOTSTRAP.md` documenting the 4-stage bootstrap trust chain, reproduction commands, recorded SHA-256 digests, the compiler-under-test switch to `axiomc`, and the `axiom0-frozen` tag and freeze rule (`ROADMAP R3`, `ADR-0005 §15`, `INV-BOOT-004`).
5. Updated `tests/selfhost/interp/unit_main.ax.in` (`InterpValue { vals: [0u64; 32] }` matching `T163`'s 256-byte `InterpValue`) and regenerated `tests/selfhost/interp/qa_interp_unit.ax`.
6. Verified functional equivalence and full-suite / `ADR-0034 §3` independent-subset execution under `build-snap-T087/build/axiomc2.exe` (`-j 1`): **`TOTAL 2909 PASS 2888 FAIL 0 SKIP 21 XFAIL 0`** (`100%` of all `1,319` active test files and `2,888` active test entries pass with `0 FAIL`).

- **Per-task Stage-2 compiler build command**:
  - `python tools/build_axiomc.py --out build-snap-T087/build`
- **Full Stage-2/3 fixed-point verification command**:
  - `python tools/bootstrap.py --stage0 build-snap-T087/build/axiom0.exe --build-dir build-snap-T087/build --check-both-opt --time-passes`

## Files changed

- `tools/bootstrap.py`
- `tools/build_axiomc.py`
- `tests/selfhost/fixedpoint/fixedpoint.test`
- `tests/selfhost/fixedpoint/fixedpoint_oracle.py`
- `tests/selfhost/interp/unit_main.ax.in`
- `tests/selfhost/interp/qa_interp_unit.ax`
- `spec/BOOTSTRAP.md`

## Acceptance Criteria Verification

### 1. Stage-2 / Stage-3 Fixed Point in Two Distinct Directories at `-O0` and `-O1` (`INV-DET-004`, `ABOOT-73/79`) — PASS

| Artifact | Opt | Build Directory | Size (bytes) | SHA-256 | Wall Time | Peak Working Set | Fixed-Point Match |
|---|---|---|---:|---|---:|---:|---|
| `axiom0.exe` (Stage 0) | `-O3` (Clang) | `build-snap-T087/build` | `866,060` | `000eae25548ef4947c1ebb9ed270792bc9789567114e3ad2444aa118c9dc3910` | — | — | Seed C11 compiler |
| `axiomc1.exe` (Stage 1) | `-O0` | `build-snap-T087/build` | `15,644,160` | `c1ac76db1249c2b37cd688af149f3740b2b81360feb977e3238d288e9a091ce0` | `30.33 s` | `1257.7 MB` | Built by `axiom0` |
| `axiomc2_O1.exe` (Stage 2) | `-O1` | `build-snap-T087/build/dir_stage2_O1` | `15,594,496` | `9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6` | `126.55 s` | `2581.4 MB` | **Byte-identical to `axiomc3_O1.exe`** |
| `axiomc3_O1.exe` (Stage 3) | `-O1` | `build-snap-T087/build/dir_stage3_O1` | `15,594,496` | `9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6` | `134.17 s` | `2581.1 MB` | **Byte-identical to `axiomc2_O1.exe`** |
| `axiomc2_O0.exe` (Stage 2) | `-O0` | `build-snap-T087/build/dir_stage2_O0` | `15,643,136` | `f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d` | `106.10 s` | `2583.9 MB` | **Byte-identical to `axiomc3_O0.exe`** |
| `axiomc3_O0.exe` (Stage 3) | `-O0` | `build-snap-T087/build/dir_stage3_O0` | `15,643,136` | `f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d` | `107.77 s` | `2582.1 MB` | **Byte-identical to `axiomc2_O0.exe`** |

### 2. No External Tool in the Bootstrap Chain (`INV-BOOT-003`, `ABOOT-74/75`) — PASS

`tools/bootstrap.py` (`clean_bootstrap_env` + `verify_no_external_tools_on_path`) strips all directories containing `gcc`, `clang`, `ld`, `as`, `link`, `cl`, or `lld` from `PATH` and sets `SOURCE_DATE_EPOCH=0` before running every stage.

### 3. Per-Task Stage-2 Build Driver (`tools/build_axiomc.py`) & Freeze Documentation (`spec/BOOTSTRAP.md`) — PASS

- `python tools/build_axiomc.py --out build-snap-T087/build` builds/verifies `build-snap-T087/build/axiomc2.exe` (and `build-snap-T087/build/axiomc.exe`) and prints:
  `BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T087\build\axiomc2.exe (also D:\projects\compiler\new lang\build-snap-T087\build\axiomc.exe) size=15594496 sha256=9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6`
- `spec/BOOTSTRAP.md` documents the trust chain, reproduction steps, the compiler-under-test switch (`--compiler build-snap-<ID>/build/axiomc2.exe`), and the `axiom0-frozen` freeze rule (`ROADMAP R3`, `ADR-0005 §15`, `INV-BOOT-004`).

### 4. Fixed-Point Test (`tests/selfhost/fixedpoint/fixedpoint.test`) — PASS

- `python tools/axtest.py selfhost/fixedpoint/fixedpoint.test --compiler build-snap-T087/build/axiom0.exe -j 1` -> **`TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`)
- `python tools/axtest.py selfhost/fixedpoint/fixedpoint.test --compiler build-snap-T087/build/axiomc2.exe -j 1` -> **`TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`** (`WEAK-NATIVE 0`)

### 5. Functional Equivalence & Full-Suite (`-j 1`) Verification with `axiomc2.exe` — PASS (`0 FAIL`)

Executed all `1,340` discovered test files (`2,909` test entries) under `build-snap-T087/build/axiomc2.exe` with `--exclude-requires axiom0-internal -j 1` across slices covering 100% of the repository (`Missing: 0`):

| Slice | Filter Directories | `WEAK-NATIVE` | `TOTAL` | `PASS` | `FAIL` | `SKIP` | `XFAIL` |
|---|---|---:|---:|---:|---:|---:|---:|
| **Slice A (ADR-0034 §3 core + std)** | `run/numeric run/drop run/ptr run/native_ std/` | 0 | 1,033 | 1,033 | 0 | 0 | 0 |
| **Slice C (remaining `run/` dirs)** | `run/array .. run/vars` | 124 | 440 | 440 | 0 | 0 | 0 |
| **Slice B1 (all non-`selfhost` categories)** | `conformance diff driver encode fuzz hir lex link lir mc mir modules obj opt parse perf programs resolve typeck ui unit verify` | 53 | 1,175 | 1,155 | 0 | 20 | 0 |
| **Slice B2 (`selfhost` + `run/parity` + `run/intrinsics` + `bundles_current.test`)** | `run/intrinsics run/native/ run/parity selfhost/abi selfhost/ast selfhost/backend/qa_backend_edge.ax selfhost/cap selfhost/diag selfhost/drop selfhost/interp/ selfhost/intrinsics selfhost/isel selfhost/kernel selfhost/own/ selfhost/source selfhost/stage1 selfhost/traits selfhost/types bundles_current.test` | 0 | 362 | 361 | 0 | 1 | 0 |
| **Fixed-Point Gate Test** | `selfhost/fixedpoint/fixedpoint.test` | 0 | 1 | 1 | 0 | 0 | 0 |
| **Deduplicated Full Suite** | **All `1,340` test files (`1,319` active, `21` skipped)** | **165** | **2,909** | **2,888** | **0** | **21** | **0** |

- **Independent Subset (`ADR-0034 §3`)**: **`443 / 443` test files (`1,148 / 1,148` test entries) PASS** (`0 FAIL`, `0 SKIP`, `WEAK-NATIVE 0` in `run/numeric`, `run/drop`, `run/ptr`, `run/native_*`, and `std/`).
- **Functional Equivalence (`tasks/0262 §42`)**: `axiomc2.exe` passes the exact same `1,319` active test files (`2,888` active test entries) as `axiomc1.exe` with `0 FAIL` and produces byte-identical `--json` diagnostics, `.obj` files, `.exe` images, and runtime execution results.

## Verification Gates Summary

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T087` -> **0 `REFUSED`**
- `python tools/gatecheck.py --gate T087 --no-run` -> **Exit 0 (`MS-P1 PASS .. MS-P10b PASS`)**
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> **Exit 0 (`COVERAGE OK`, `gaps: 0`)**
- `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> **Exit 0 (`HARNESS OK`)**
- `python tools/archcheck.py` -> **Exit 0 (`archcheck: 192 files scanned, 0 violations`)**

STATUS: COMPLETE
