# BOOTSTRAP — Trust Chain, Reproducible Fixed Point, and `axiom0` Freeze

## Tóm tắt
Tài liệu chuẩn hóa chuỗi tin cậy tự biên dịch (bootstrap trust chain) của trình biên dịch Axiom từ Stage-0 (`axiom0` viết bằng C11) tới Stage-1 (`axiomc1`), Stage-2 (`axiomc2`) và Stage-3 (`axiomc3` viết hoàn toàn bằng Axiom), quy trình tái lập điểm cố định (`axiomc2 == axiomc3` đồng nhất từng byte ở cả `-O0` và `-O1` trên hai thư mục độc lập khi đã loại bỏ hoàn toàn `gcc`/`ld`/`as` khỏi `PATH`), lệnh chuẩn `tools/build_axiomc.py --out <dir>` cho các task từ Phase 11 trở đi, quy tắc chuyển trình biên dịch kiểm thử sang `axiomc`, và quy tắc đóng băng `bootstrap/axiom0` qua thẻ nội bộ `axiom0-frozen` (ROADMAP R3, ADR-0005 §15, SPEC-00 §6, SPEC-20 §6–§7).

Status: canonical (T087, 2026-11-02).
Invariants: `INV-DET-001`, `INV-DET-002`, `INV-DET-004`, `INV-BOOT-001`, `INV-BOOT-002`, `INV-BOOT-003`, `INV-BOOT-004`.
Decisions: `ADR-0003` (64 MB stack reserve), `ADR-0005 §7/§15` (self-compile budget, `axiom0-frozen` tag, `tools/build_axiomc.py`), `ADR-0034` (independent oracle subset), `ADR-0035` (deterministic local symbols).

---

## 1. Bootstrap Trust Chain (`BOOT-36..38`, `SPEC-20 §6.1`)

The Axiom compiler bootstrap chain consists of four deterministic stages on Windows x86-64 (`PE32+` / `COFF`):

```
[Host C11 Compiler (Clang/GCC)]
       │
       ▼  (CMake + Ninja, once per snapshot)
  Stage 0: axiom0.exe          (bootstrap/axiom0/src/**, C11)
       │
       ▼  (compiles compiler/**/*.ax + std/**/*.ax, -O0, --stack-reserve 67108864)
  Stage 1: axiomc1.exe         (Axiom compiler binary built by axiom0)
       │
       ▼  (compiles compiler/**/*.ax + std/**/*.ax in dir_stage2_<opt>, -O1 and -O0)
  Stage 2: axiomc2.exe         (Self-compiled Axiom compiler binary, directory A)
       │
       ▼  (compiles compiler/**/*.ax + std/**/*.ax in dir_stage3_<opt>, -O1 and -O0)
  Stage 3: axiomc3.exe         (Rebuilt Axiom compiler binary, directory B)
       │
       ▼
  Fixed Point: sha256(axiomc2.exe) == sha256(axiomc3.exe)  (100% byte-identical)
```

### 1.1 Stage Definitions
1. **Stage 0 (`axiom0.exe`)**:
   - Source: `bootstrap/axiom0/` (C11).
   - Role: Minimal seed compiler implementing the exact self-host subset (`spec/SPEC-00-bootstrap.md §9`, `spec/selfhost-subset.tsv`).
   - Built once from source by the host C11 toolchain (`cmake` + `ninja`).
2. **Stage 1 (`axiomc1.exe`)**:
   - Source: `compiler/**/*.ax` (121 modules assembled in canonical topological dependency order by `tools/bootstrap.py`) + `std/**/*.ax`.
   - Built by: `axiom0.exe` with `--stack-reserve 67108864` (`64 MB` per `ADR-0003`) and `--std-root <repo>/std`.
   - Environment: `SOURCE_DATE_EPOCH=0`, `AXIOM_STD` unset, and all external C/assembler/linker tools (`gcc`, `clang`, `ld`, `as`, `link`, `cl`, `lld`) stripped from `PATH` (`INV-BOOT-003`, `ABOOT-74/75`).
3. **Stage 2 (`axiomc2.exe` / `axiomc.exe`)**:
   - Source: Identical `compiler/**/*.ax` + `std/**/*.ax` sources.
   - Built by: `axiomc1.exe` executing inside an isolated working directory `dir_stage2_<opt>` (`<build>/dir_stage2_O1` for `-O1`, `<build>/dir_stage2_O0` for `-O0`) with `--stack-reserve 67108864 --std-root <repo>/std`.
   - Role: Production self-hosted compiler (`axiomc2.exe`, copied to `axiomc.exe`) used as the compiler under test from `T087` onward.
4. **Stage 3 (`axiomc3.exe`)**:
   - Source: Identical `compiler/**/*.ax` + `std/**/*.ax` sources.
   - Built by: `axiomc2.exe` executing inside a second, distinct working directory `dir_stage3_<opt>` (`<build>/dir_stage3_O1` for `-O1`, `<build>/dir_stage3_O0` for `-O0`) with identical flags.
   - Role: Fixed-point verification artifact (`sha256(axiomc2.exe) == sha256(axiomc3.exe)`).

---

## 2. Hermeticity & Determinism Guarantees (`INV-BOOT-003`, `INV-DET-001..004`)

1. **Zero External Toolchain in the Production Path (`INV-BOOT-003`, `ABOOT-74/75`)**:
   - `axiom0` and `axiomc` lower `Source -> AST -> HIR -> THIR -> MIR -> LIR -> x86-64 Machine IR -> Machine Code Bytes -> COFF .obj -> PE32+ .exe` completely in-memory.
   - `tools/bootstrap.py` removes every directory containing `gcc.exe`, `ld.exe`, `as.exe`, `clang.exe`, `link.exe`, `cl.exe`, `lld.exe`, or `lld-link.exe` from `PATH` before invoking `axiom0`, `axiomc1`, or `axiomc2`, and verifies via `verify_no_external_tools_on_path()` that none remain reachable.
2. **Path-Independent & Timestamp-Free Binary Emission (`INV-DET-001`, `INV-DET-002`, `INV-DET-004`)**:
   - COFF object headers and PE32+ executable headers emit `TimeDateStamp = 0`.
   - Internal symbol names (including `.Lstr.<fn>.<k>` and `.Lpanic.<n>`) are numbered deterministically per function/module (`ADR-0035`), never from memory addresses or file paths.
   - Building `axiomc2.exe` in `<build>/dir_stage2_<opt>` and `axiomc3.exe` in `<build>/dir_stage3_<opt>` yields **100% bitwise-identical** PE32+ executables at both `-O0` and `-O1`.

---

## 3. Reproduction Steps & Recorded Digests

### 3.1 Per-Task Stage-2 Compiler Build (`tools/build_axiomc.py`)
Every task from `T087` / Phase 11 onward builds the Stage-2 self-hosted compiler inside its isolated snapshot directory (`build-snap-<ID>/build`) using:

```bash
python tools/build_axiomc.py --out build-snap-<ID>/build
```

- If `build-snap-<ID>/build/axiom0.exe` is not yet built, `tools/build_axiomc.py` automatically configures and builds `bootstrap/axiom0` with CMake + Ninja into `build-snap-<ID>/build`.
- It then invokes `tools/bootstrap.py` to produce `build-snap-<ID>/build/axiomc1.exe`, `build-snap-<ID>/build/axiomc2.exe`, and `build-snap-<ID>/build/axiomc.exe` (an exact copy of `axiomc2.exe`).
- Pass `--force` to force a full rebuild from Stage 1 even when existing binaries are newer than `compiler/**/*.ax` and `std/**/*.ax`.

### 3.2 Full Stage-1 -> Stage-2 -> Stage-3 Fixed-Point Verification (`tools/bootstrap.py`)
To reproduce the complete fixed-point verification across both `-O1` and `-O0` in distinct directories:

```bash
python tools/bootstrap.py --stage0 build-snap-T087/build/axiom0.exe --build-dir build-snap-T087/build --check-both-opt --time-passes
```

Or via the `axtest` harness test (`MS-P10b` gate test):

```bash
python tools/axtest.py selfhost/fixedpoint/fixedpoint.test --compiler build-snap-T087/build/axiomc2.exe -j 1
```

### 3.3 Recorded Binary Sizes & SHA-256 Digests (`T087`)

| Stage / Artifact | Opt Level | Working Directory | Size (bytes) | SHA-256 Digest |
|---|---|---|---:|---|
| `axiom0.exe` (Stage 0, C11) | `-O3` (Clang) | `build-snap-T087/build` | `866,060` | `000eae25548ef4947c1ebb9ed270792bc9789567114e3ad2444aa118c9dc3910` |
| `axiomc1.exe` (Stage 1, `axiom0 -> axiomc1`) | `-O0` | `build-snap-T087/build` | `15,644,160` | `c1ac76db1249c2b37cd688af149f3740b2b81360feb977e3238d288e9a091ce0` |
| `axiomc2_O1.exe` (Stage 2, `axiomc1 -> axiomc2`) | `-O1` | `build-snap-T087/build/dir_stage2_O1` | `15,594,496` | `9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6` |
| `axiomc3_O1.exe` (Stage 3, `axiomc2 -> axiomc3`) | `-O1` | `build-snap-T087/build/dir_stage3_O1` | `15,594,496` | `9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6` |
| `axiomc2_O0.exe` (Stage 2, `axiomc1 -> axiomc2`) | `-O0` | `build-snap-T087/build/dir_stage2_O0` | `15,643,136` | `f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d` |
| `axiomc3_O0.exe` (Stage 3, `axiomc2 -> axiomc3`) | `-O0` | `build-snap-T087/build/dir_stage3_O0` | `15,643,136` | `f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d` |

At `-O0`, `axiomc2_O0.exe` (built by `axiomc1` in `dir_stage2_O0`) and `axiomc3_O0.exe` (built by `axiomc2_O0` in `dir_stage3_O0`) are **100% byte-identical** (`f2e4d6a6...`, `15,643,136` bytes). At `-O1`, `axiomc2_O1.exe` (built by `axiomc1` in `dir_stage2_O1`) and `axiomc3_O1.exe` (built by `axiomc2_O1` in `dir_stage3_O1`) are **100% byte-identical** (`9a0c7e51...`, `15,594,496` bytes).

---

## 4. Compiler-Under-Test Switch (`axiomc` Default Workflow)

After `T087`, the compiler under test for all language, backend, and standard library work (Phases `P11`–`P23`) is **`axiomc`** (`build-snap-<ID>/build/axiomc2.exe` / `build-snap-<ID>/build/axiomc.exe`):

1. **Building the compiler in a task snapshot**:
   ```bash
   python tools/build_axiomc.py --out build-snap-<ID>/build
   ```
2. **Running `tools/axtest.py` with `axiomc`**:
   Because `tools/axtest.py` and `tests/README.md` are owned by `T005` (completed in Phase 0), `tools/axtest.py` is never edited to change its fallback path; instead, pass `--compiler` and `--exclude-requires axiom0-internal` explicitly:
   ```bash
   python tools/axtest.py --compiler build-snap-<ID>/build/axiomc2.exe --exclude-requires axiom0-internal -j 1
   ```
   (The 21 `exec` manifests carrying `requires: axiom0-internal` exercise C-internal unit flags `--self-test-*` and `cdriver_*` harnesses specific to `axiom0`).
3. **Running `tools/gatecheck.py` with `axiomc`**:
   ```bash
   python tools/gatecheck.py --compiler build-snap-<ID>/build/axiomc2.exe
   ```

---

## 5. `axiom0` Freeze Rule (`ROADMAP R3`, `ADR-0005 §15`, `INV-BOOT-004`)

1. **Local Freeze Tag (`axiom0-frozen`)**:
   - Immediately upon accepting `T087`, the orchestrator creates the local Git tag `axiom0-frozen` at the `T087` commit (`git tag axiom0-frozen`).
   - In accordance with project safety rules, tags are local-only and are **never pushed** to any remote.
2. **Mechanical Enforcement via `harness_check.py` (`INV-BOOT-004`)**:
   - Once `refs/tags/axiom0-frozen` exists, `.claude/skills/axiom-tasks/scripts/harness_check.py` inspects `git log axiom0-frozen..HEAD -- bootstrap/axiom0`.
   - Any commit after `axiom0-frozen` that touches `bootstrap/axiom0/**` is **rejected** (`PROBLEM: axiom0 frozen (tag axiom0-frozen) but commit touches bootstrap/axiom0`) unless its commit subject references an emergency bootstrap fix task titled `AX0-FIX-<nn> ...` (in phase `P10-selfhost`, filed by `axiom-architect`).
   - Furthermore, `harness_check.py` forbids any post-self-host task (`P11`+) from listing `bootstrap/axiom0` in `paths:` or `locks:`.
3. **Where P11+ Changes Live**:
   - All Phase 11–23 compiler features, optimizations, register allocation, target backends, and bug fixes are implemented exclusively in `compiler/**` (Axiom) and `std/**` (Axiom).
