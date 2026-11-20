# Periodic Full Run 2 (`fullrun-2`, Tier 1 `non-selfhost`)

## Tóm tắt

Đợt quét định kỳ Tier-1 `non-selfhost` (`fullrun-2`) chạy trên snapshot tách biệt `build-snap-fullrun-2` tại commit sạch `c92e92ca` (ngay sau khi cả hai hồi quy P0 từ `fullrun-1` là `T495` và `T820` được sửa và chấp nhận; 4 tác vụ được chấp nhận trong `0b9ff70a..c92e92ca`: `T488`, `T444`, `T495`, `T820`):

- **Xây dựng Stage 1–3 (`python tools/build_axiomc.py --out build --stage 3`)**: **ĐẠT** (`449.35 s`) — xác nhận `FIXED-POINT (O1) OK` (`sha256(axiomc2_O1) == sha256(axiomc3_O1) == fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d`, 8,535,040 bytes) và `STAGE0-GUARD OK` (6 chương trình smoke, bao gồm `Xin chào thế giới`, trùng khớp từng byte giữa `axiomc1` và `B`).
- **Kiểm tra cấu trúc & harness**: `archcheck.py` (229 tệp, 0 vi phạm), `harness_check.py` (`HARNESS OK`), và `axtest_affected.py --check-map` (`MAP-CHECK OK`) đều **ĐẠT**; `CACHE-MISMATCH = 0` (`verify-sample` 20/106 hits, seed `144138376`).
- **Xác minh 4 test ID hồi quy từ `fullrun-1`**: **4/4 ĐẠT tươi (`cached=False`)**:
  - `run/fmt_engine/fmt_engine.test`: **PASS** (`40,379 ms`)
  - `run/fmt_cli/fmt_cli.test`: **PASS** (`90,089 ms`)
  - `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test`: **PASS** (`106,030 ms`)
  - `std/async/executor/async_channel_pipeline.ax`: **PASS** cả 3 mode (`interp` `1,857 ms`, `native` `1,682 ms`, `native-O1` `1,644 ms`)
- **Kết quả quét Tier-1 (`2,050` test IDs, `4,347` lượt chạy)**:
  - Lần quét song song (`-j 2`, cùng lúc có 2 tiến trình `axiomc2` nặng từ `build-snap-T446` tranh chấp CPU/RAM trên máy 4 nhân): `TOTAL 4347 PASS 4266 FAIL 1 SKIP 80 XFAIL 0` (0 timeout, 0 crash, 60.3 phút).
  - Duy nhất `perf/own_scaling/own_scaling.test` vượt ngưỡng tỷ lệ thời gian đồng hồ tường sát biên (`own(200)=0.416s own(800)=3.384s ratio 8.13 limit 8.00`).
  - **Chạy lại cô lập (`--no-cache -j 1 --timeout-scale 6`)**: **3/3 PASS liên tiếp** (`TOTAL 1 PASS 1 FAIL 0`).
  - **Đối chứng A/B xen kẽ 5 cặp (`0b9ff70a` vs `c92e92ca`)**: **0 hồi quy trong `0b9ff70a..c92e92ca`** (`c92e92ca` có trung vị `own` ratio `7.84` và `mir_build` ratio `10.87`, thực tế nhanh hơn nhẹ so với `0b9ff70a` có trung vị `own` ratio `8.47` và `mir_build` ratio `11.46`). Tuy nhiên, báo cáo ghi nhận **kiến nghị theo dõi** về hiện tượng `mir_build` (`compiler/mir/builder.ax`) vẫn tăng siêu tuyến tính (~9–12× khi đầu vào tăng 4×, đã tồn tại từ `T493`/`T489`/`T494`), khiến bài test tỷ lệ đồng hồ tường đơn phát `own_scaling.test` (`limit 8.00`) dễ rung nhiễu khi máy 4 nhân có tác vụ biên dịch song song.

---

## 1. Run Metadata

- **Run ID**: `fullrun-2`
- **Mode / Tier**: Tier 1 — `non-selfhost`
- **Snapshot commit**: `c92e92ca4db5dd23bafe5a28a831286851def377` (`T820`)
- **Reference commit (`fullrun-1`)**: `0b9ff70a` (5 commits / 4 accepted tasks in `0b9ff70a..c92e92ca`: `8117a094` `T488`, `6567f392` `fullrun-1`, `54bb796f` `T444`, `58b4e97d` `T495`, `c92e92ca` `T820`)
- **Snapshot worktree**: `build-snap-fullrun-2` (detached HEAD `c92e92ca`, removed and pruned on completion)
- **Artifacts**:
  - `_workspaces/artifacts/fullrun-2-ids.txt` (2,050 test IDs)
  - `_workspaces/artifacts/fullrun-2-axtest.json` (4,347 test results)
- **Baseline file**: `_workspaces/baseline-failures.txt` (0 active entries)

---

## 2. Stage 1–3 Compiler Build & Fixed-Point Verification

Command run inside `build-snap-fullrun-2/`:
```powershell
python tools/build_axiomc.py --out build --stage 3
```

- **Exit code**: `0`
- **Total wall time**: `449.35 s` (~7.5 min)
- **Host C compiler for Stage 0 (`axiom0.exe`)**: Clang 22.1.4 + Ninja (0 errors)
- **Source inputs**: 257 source files hashed in 1.18 s (`sources 840c6d9ad5bbf236`)
- **Seed hit from `compiler-cache/`**:
  `_workspaces/artifacts/compiler-cache/axiomc2_O1_adb3dbb652075521.exe` (exact inputs `adb3dbb652075521`, sha256 prefix `fd9166149e60e446`)

| Stage / Artifact | Opt | Size (bytes) | Wall (s) | Peak WS (MB) | Peak Commit (MB) | SHA-256 |
|---|---|---:|---:|---:|---:|---|
| `build/axiom0.exe` (Stage 0) | Release | 866,060 | — | — | — | `af875f7dda9b941415a8c701d789919e891679dbd348cac54ca9bf66bf99352c` |
| `build/axiomc1.exe` (Stage 1: `axiom0 -> c1`) | — | 28,271,104 | 177.57 | 2341.5 | 2580.2 | `9991398e59539ceb568418755388112679295ae3f487bf0f59439d68058faf6d` |
| `build/dir_seed_A_O1/axiomc_A.exe` (`seed -> A`) | `-O1` | 8,535,040 | 69.58 | 3071.4 | 3124.0 | `fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d` |
| `build/dir_stage2_O1/axiomc2.exe` (`A -> B` / Stage 2) | `-O1` | 8,535,040 | 68.47 | 3071.5 | 3124.1 | `fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d` |
| `build/dir_stage3_O1/axiomc3.exe` (`B -> C` / Stage 3) | `-O1` | 8,535,040 | 74.70 | 3071.3 | 3123.9 | `fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d` |

Verified invariants:
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == fd9166149e60e44603a050efec174bfb38631f0e1a850299279b5db35a84b94d` (8,535,040 bytes, distinct directories `dir_stage2_O1` vs `dir_stage3_O1`, `[seeded B==C]`)
- `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`-O1`, incl. `Xin chào thế giới`)

---

## 3. Static / Harness Checks & Tier-1 `non-selfhost` Sweep

### 3.1 Static & Harness Checks
- `python tools/archcheck.py`: `archcheck: 229 files scanned, 0 violations` (`rc=0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (`rc=0`; optional warning only: `.claude/settings.json: optional PreToolUse guard hook (guard.py) not enabled`)
- `python tools/axtest_affected.py --check-map`: `MAP-CHECK OK` (`rc=0`)

### 3.2 `axtest.py` Tier-1 Sweep
Commands run inside `build-snap-fullrun-2/`:
```powershell
python .claude/skills/axiom-tasks/scripts/fullrun.py non-selfhost-ids "D:\projects\compiler\new lang\_workspaces\artifacts\fullrun-2-ids.txt" --root .
python tools/axtest.py --id-file "D:\projects\compiler\new lang\_workspaces\artifacts\fullrun-2-ids.txt" --compiler build/axiomc2.exe --build-dir build --gate -j 2 --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt --json > "D:\projects\compiler\new lang\_workspaces\artifacts\fullrun-2-axtest.json"
```

- **Raw exit code**: `1` (sole failure: transient wall-clock load ratio on `perf/own_scaling/own_scaling.test`; see §4)
- **Wall time**: `3618.27 s` (~60.3 min)
- **Totals**: `TOTAL 4347 PASS 4266 FAIL 1 SKIP 80 XFAIL 0`
  - `xpass = 0`, `crash = 0`, `timeout = 0`, `weak_native = 143` (pre-existing tests)
- **Cache statistics**:
  - `CACHED 210 HITS 106 MISS 1430 UNCACHEABLE 514 STORED 1371 dep_source=exact`
  - `VERIFY-SAMPLE seed=144138376 n=20 of 106 hits`
  - `CACHE-MISMATCH`: **0** (`mismatch: []`)
  - `store_skipped`: `{'nondeterministic (depends on std/sync)': 41, 'inputs changed during the run': 18}`

### 3.3 Verification of the 4 `fullrun-1` Failing IDs
All 4 IDs that failed in `fullrun-1` (fixed by `T495` and `T820`) executed **fresh (`cached=False`)** and **PASSED**:

| Test ID | Mode | State | Cached | Duration (ms) | Fix Task |
|---|---|---|---:|---:|---|
| `run/fmt_engine/fmt_engine.test` | — | `PASS` | `False` | 40,379 | `T820` |
| `run/fmt_cli/fmt_cli.test` | — | `PASS` | `False` | 90,089 | `T820` |
| `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test` | — | `PASS` | `False` | 106,030 | `T820` |
| `std/async/executor/async_channel_pipeline.ax` | `interp` | `PASS` | `False` | 1,857 | `T495` |
| `std/async/executor/async_channel_pipeline.ax` | `native` | `PASS` | `False` | 1,682 | `T495` |
| `std/async/executor/async_channel_pipeline.ax` | `native-O1` | `PASS` | `False` | 1,644 | `T495` |

---

## 4. Investigation of `perf/own_scaling/own_scaling.test` (No Regression in `0b9ff70a..c92e92ca`)

### 4.1 Raw Sweep Failure
During the `-j 2` sweep (while 2 concurrent `axiomc2` processes from `build-snap-T446` were simultaneously consuming ~2 GB RAM and CPU cores on the 4-core host):
- `perf/own_scaling/own_scaling.test`: `FAIL` (`exit code 1`, `stderr: own(200)=0.416s own(800)=3.384s ratio 8.13 limit 8.00`).
- All 11 other tests in `perf/own_scaling/` (including `own_wave2_subtimers_and_scaling.test`) **PASSED**.

### 4.2 Isolated Retries (`--no-cache -j 1 --timeout-scale 6`)
```powershell
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 1 --timeout-scale 6 -v perf/own_scaling/own_scaling.test
```
- Retry 1: `PASS` (`TOTAL 1 PASS 1 FAIL 0`, `rc=0`)
- Retry 2: `PASS` (`TOTAL 1 PASS 1 FAIL 0`, `rc=0`)
- Retry 3: `PASS` (`TOTAL 1 PASS 1 FAIL 0`, `rc=0`)

### 4.3 Interleaved 5-Pair A/B Benchmark (`0b9ff70a` vs `c92e92ca`) & Historical Trend
To rule out any subtle scaling regression from `T495` (`compiler/mir/builder.ax`) or `T444`, we ran an interleaved 5-pair A/B comparison of `0b9ff70a` (`_workspaces/artifacts/compiler-cache/axiomc2_O1_5789d80bb26aafa6.exe`) vs `c92e92ca` (`build/axiomc2.exe`) on the generated `own_scaling_200.ax` and `own_scaling_800.ax` inputs under the same shared-host load:

| Commit | `own(200)` median | `own(800)` median | `own` ratio median (min–max) | `mir_build` ratio median (min–max) |
|---|---:|---:|---:|---:|
| `0b9ff70a` (`T494`, `fullrun-1`) | `0.562 s` | `4.715 s` | **`8.47×`** (`7.45–9.20×`) | **`11.46×`** (`10.73–12.39×`) |
| `c92e92ca` (`T820`, `fullrun-2`) | `0.561 s` | `4.228 s` | **`7.84×`** (`6.62–9.66×`) | **`10.87×`** (`8.97–13.86×`) |

Historical single-pass check across cached compilers back to `T493`:
- `T493` (`689f7dea`): `own 0.646s -> 3.941s (6.10×)` | `mir_build 0.332s -> 2.890s (8.71×)`
- `T489` (`f0f98f33`): `own 0.551s -> 3.681s (6.68×)` | `mir_build 0.285s -> 2.582s (9.06×)`
- `T494` (`0b9ff70a`): `own 0.456s -> 4.186s (9.17×)` | `mir_build 0.236s -> 2.948s (12.48×)`
- `T820` (`c92e92ca`): `own 0.547s -> 4.857s (8.88×)` | `mir_build 0.283s -> 3.578s (12.64×)`

**Conclusion**:
- **0 regressions in `0b9ff70a..c92e92ca`**: `c92e92ca` is at parity with (and in median slightly faster than) `0b9ff70a`, and passes `3/3` isolated `axtest.py -j 1` retries.
- **Follow-up recommendation (non-regression tech debt)**: Because `T493` and `T494` substantially sped up `own_cap`, `own_init`, and `mir_drop`, the remaining untouched `mir_build` sub-pass (`compiler/mir/builder.ax`, which scales ~9–12× on 4× input) now dominates ~70–75% of `time: own` at `N=800`. This puts `own_scaling.test` (single-shot wall-clock `limit 8.00`) close enough to `8.00` that concurrent builds on the shared 4-core machine can occasionally nudge it above `8.00` (e.g., `8.13`). Recommend filing a follow-up perf/hygiene task to (a) eliminate the remaining superlinear scan in `compiler/mir/builder.ax` (`mir_build`) and/or (b) harden `tests/perf/own_scaling/own_scaling.py` against single-shot wall-clock jitter (e.g. median-of-3 or CPU time).

---

## 5. Summary Verdict

- **Stage 1–3 build + `FIXED-POINT (O1) OK` + `STAGE0-GUARD OK`**: PASS
- **`archcheck` / `harness_check` / `axtest_affected --check-map` / cache verification**: PASS (`0` violations, `0` cache mismatches)
- **All 4 `fullrun-1` P0 regressions (`T495` + `T820`)**: PASS fresh (`cached=False`)
- **Tier-1 `non-selfhost` suite (`2,050` IDs / `4,347` runs)**: **0 new regressions outside `_workspaces/baseline-failures.txt`** (sole `-j 2` timing jitter on `perf/own_scaling/own_scaling.test` passed `3/3` isolated `-j 1` retries and outperformed `0b9ff70a` in interleaved 5-pair A/B comparison).

FULLRUN-2 CLEAN
