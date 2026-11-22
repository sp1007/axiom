# Periodic Full Run 3 (`fullrun-3`, Tier 1 `non-selfhost`)

## Tóm tắt

Đợt quét định kỳ Tier-1 `non-selfhost` (`fullrun-3`) chạy trên snapshot `build-snap-fullrun-3` tại HEAD `3b705825` (T496a). Mốc đối chiếu là lần quét sạch trước đó `c92e92ca` (`fullrun-2`); có 28 commit trong `c92e92ca..3b705825` (T446, T447, T444a/b, T445, T453/T453a, T454, T455, T482, T483, T422a/b, T496/T496a, T497, T498/a/b/d, T499/a, T423/T423b/T423f ...).

- **Xây dựng Stage 1-3** (`python tools/build_axiomc.py --out build --stage 3`, clang Release): **ĐẠT** (`7m06s`). `FIXED-POINT (O1) OK` (`sha256(axiomc2)==sha256(axiomc3)==3ec4d671894f28a7776f5dcbaf61ea9008420f278da64e7c9b40018dec61f901`, 8,830,464 bytes) và `STAGE0-GUARD OK` (6 chương trình smoke, gồm `Xin chào thế giới`).
- **Kiểm tra tĩnh**: `archcheck` (232 tệp, 0 vi phạm), `harness_check` (`HARNESS OK`), `axtest_affected --check-map` (`MAP-CHECK OK`) đều ĐẠT.
- **Quét Tier-1** (2,573 test id, `--gate -j 2`, 58m17s): `TOTAL 5626 PASS 5583 FAIL 1 SKIP 26 XFAIL 16` (0 crash, 0 timeout, 0 XPASS). `CACHE-MISMATCH = 0` (verify-sample 60/1192 hit).
- **Một lỗi duy nhất**: `perf/build_scaling/build_scaling_o1.test` (`build(150)=0.744s build(600)=3.777s ratio 5.08 limit 5.00`). Đây là nhiễu thời gian đồng hồ tường do máy 4 nhân dùng chung: chạy lại cô lập `--no-cache -j 1 --timeout-scale 6` **3/3 PASS**; A/B xen kẽ 4 cặp giữa `c92e92ca` và HEAD cho tỷ lệ tương đương (xem mục 4), không có hồi quy.
- **Kết quả: 0 id lỗi mới** (baseline rỗng). 16 XFAIL đều là xfail có theo dõi (T423c, T423d, T454).

## 1. Run metadata

- Run ID `fullrun-3`, Tier 1 `non-selfhost`; snapshot `build-snap-fullrun-3` (detached `3b705825557329d21b0af3e2fa345a93d577d3ad`); reference `c92e92ca`; baseline `_workspaces/baseline-failures.txt` (0 active entries).
- Artifacts: `_workspaces/artifacts/fullrun-3-ids.txt` (2,573 ids), `fullrun-3-axtest.json` (5,626 results), `fullrun-3-axtest.err`, `fullrun-3-build.log`, `fullrun-3-sweep.done`, `fullrun-3-ab-build-scaling.txt`.

## 2. Build

`python tools/build_axiomc.py --out build --stage 3` (inside the snapshot), rc=0, 7m06s. Stage 1 `axiomc1` 29,309,440 B (160.5 s); seed A / Stage 2 / Stage 3 `-O1` each 8,830,464 B (56.1 / 60.9 / 59.4 s). FIXED-POINT (O1) OK; STAGE0-GUARD OK.

## 3. Static checks and sweep

- `archcheck`: 232 files scanned, 0 violations. `harness_check`: HARNESS OK (only the optional guard-hook warning). `--check-map`: MAP-CHECK OK.
- Sweep command (inside snapshot): `python tools/axtest.py --id-file <fullrun-3-ids.txt> --compiler build/axiomc2.exe --build-dir build --gate -j 2 --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt --json`; ids from `fullrun.py non-selfhost-ids --root .` (2,573). rc=1 solely because of the one timing failure.
- Counts: total 5626, pass 5583, fail 1, skip 26, xfail 16, xpass 0, crash 0, timeout 0, weak_native 143 (pre-existing).
- Cache: CACHED 3235, HITS 1192, MISS 795, UNCACHEABLE 586, STORED 754, dep_source=exact, VERIFY-SAMPLE seed=319142230 n=60, mismatch [] (0). store_skipped: `nondeterministic (depends on std/sync)`: 41.
- XFAIL (16 results, all tracked): `std/fiber/closure_generic_infer_xfail.ax` (T423c), `std/fiber/impl_generic_in_method_bound_xfail.ax` (T423d), `std/num/empty_copy_xfail.ax`, `into_xfail.test`, `static_dispatch_xfail.ax`, `trait_dispatch_xfail.ax` (T454).

## 4. `perf/build_scaling/build_scaling_o1.test` (not a regression)

- Sweep failure: `exit code 1; build(150)=0.744s build(600)=3.777s ratio 5.08 limit 5.00` (single-shot wall-clock ratio, shared 4-core host with other QA gates running).
- Isolated retries `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --no-cache -j 1 --timeout-scale 6 -v perf/build_scaling/build_scaling_o1.test`: 3/3 PASS.
- Interleaved A/B (4 pairs, `build_scaling.py --opt O1 --units 150`, limits relaxed to 50 to read raw ratios; `c92e92ca` = `compiler-cache/axiomc2_O1_adb3dbb652075521.exe` vs snapshot `axiomc2.exe`):

| pair | c92e92ca build ratio | HEAD build ratio | c92e92ca (frame+isel)/ir | HEAD (frame+isel)/ir |
|---|---:|---:|---:|---:|
| 1 | 3.08 | 2.02 | 2.66 | 2.34 |
| 2 | 2.80 | 2.68 | 2.60 | 2.33 |
| 3 | 3.31 | 3.63 | 2.65 | 2.57 |
| 4 | 3.65 | 3.28 | 2.57 | 2.42 |

  Both compilers span the same 2.0-3.7 range under load; HEAD is not slower. Raw log: `_workspaces/artifacts/fullrun-3-ab-build-scaling.txt`. No bisect needed.
- Follow-up (non-regression): like `own_scaling` in fullrun-2, single-shot wall-clock ratio perf tests (limit 5.00) flake under concurrent builds; consider median-of-3 or CPU-time measurement.

## 5. Verdict

Build/fixed-point/guard PASS; static checks PASS; Tier-1 sweep 0 new failing ids (the single timing failure passes 3/3 isolated and is at parity in A/B).

FULLRUN: CLEAN
