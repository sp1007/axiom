# T494a report

## Summary
Hardened the wall-clock scaling performance tests in `tests/perf/build_scaling/` and `tests/perf/own_scaling/` against concurrent host-load jitter (fullrun-3 §4 / fullrun-2 flakes) by sampling each input size 3 times sequentially (`--samples 3`, default) and taking the **minimum** of each timer (the estimator least affected by host contention), while printing all raw samples, minimums, and medians to `stderr` for diagnosis.

- `tests/perf/build_scaling/build_scaling.py`: added `--samples` (default `3`). Compiles each size (`N`, `4N`) 3 times sequentially, computes per-timer `min` and `median` for `build` and all `time-build:` sub-timers (`frame`, `isel`, `mir_build`, `lir`, `mir_drop`, etc.), prints all samples + `min` + `med` on `stderr`, and evaluates all ratio/budget checks using `min` with the existing limits and `max(t, 0.05)` floors. Preserves the `OK build scaling` / `SKIP build scaling` / `FAIL build scaling` stdout contract.
- `tests/perf/own_scaling/own_scaling.py`: added `--samples` (default `3`). Compiles each size (`N`, `4N`) 3 times sequentially, computes `min` and `median` of `own`, prints all samples + `min` + `med` on `stderr`, and evaluates `own(4N) / max(own(N), 0.05) <= limit` using `min`. Preserves the `OK own scaling` / `SKIP own scaling` / `FAIL own scaling` stdout contract.
- `tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py`: added `--samples` (default `3`) and `--limit` (default `2.0`). Runs `check --time-passes` 3 times sequentially for both `--small` and `--large`, verifies `time-own:` sub-timer accounting on every sample, prints all samples + `min` + `med` for `own`, `own_cap`, and `own_init` on `stderr`, and checks `min(own_cap) + min(own_init) <= limit` at `--large`. Preserves the `OK own_wave2_subtimers_and_scaling` stdout contract and `-O0`/`-O1` determinism checks.
- `.test` timeouts: none needed raising. Old vs new wall times (see table below) show 17x–32x headroom even under concurrent `-j 2` load (`900s` vs `<= 51.19s`, `300s` vs `<= 9.13s`).

## Files changed
- tests/perf/build_scaling/build_scaling.py
- tests/perf/own_scaling/own_scaling.py
- tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py

## Tests

All builds and tests were executed inside `build-snap-T494a/` against stage-2 `build/axiomc2.exe` (`sha256=17c83e14deda9744...`, `FIXED-POINT (O1) OK`).

### 1. Old vs new wall times (isolated `--no-cache -j 1`) and `.test` timeouts

| Test | Old wall (1-shot) | New wall (min-of-3) | Under `-j 2` load (min / med / max) | `.test` timeout | Timeout changed? |
|---|---:|---:|---|---:|---|
| `perf/build_scaling/build_scaling.test` | 13.38 s | 39.21 s | 37.88 s / 45.07 s / 48.64 s | 900 s | no (18x headroom) |
| `perf/build_scaling/build_scaling_o1.test` | 13.20 s | 36.91 s | 35.54 s / 45.70 s / 51.19 s | 900 s | no (17x headroom) |
| `perf/own_scaling/own_scaling.test` | 13.94 s | 35.60 s | 39.87 s / 46.96 s / 49.60 s | 900 s | no (18x headroom) |
| `perf/own_scaling/own_wave2_subtimers_and_scaling.test` | 3.88 s | 5.99 s | 7.13 s / 8.52 s / 9.13 s | 300 s | no (32x headroom) |

### 2. 10x stability run under concurrent `-j 2` load (`tests/run/struct` loop, 158 background runs)

- `perf/build_scaling/build_scaling.test`: **10/10 PASS** (`min=37.88s med=45.07s max=48.64s`)
- `perf/build_scaling/build_scaling_o1.test`: **10/10 PASS** (`min=35.54s med=45.70s max=51.19s`)
- `perf/own_scaling/own_scaling.test`: **10/10 PASS** (`min=39.87s med=46.96s max=49.60s`)
- `perf/own_scaling/own_wave2_subtimers_and_scaling.test`: **10/10 PASS** (`min=7.13s med=8.52s max=9.13s`)

### 3. Forced-limit regression verification (all must FAIL with exit 1)

- `build_scaling.py --opt O0 --units 150 --limit 1.0`: **exit 1** — `FAIL build scaling: build(150)=0.681s build(600)=2.787s ratio 4.09 > 1.00` (stderr printed all 3 samples, min, and med for `build`, `frame`, `isel`, `mir_build`, `lir`, `mir_drop`)
- `build_scaling.py --opt O1 --units 150 --limit 1.0 --frame-limit 5.5 --frame-to-ir-limit 2.6 --hot-to-ir-limit 4.0`: **exit 1** — `FAIL build scaling: build(150)=0.609s build(600)=2.571s ratio 4.22 > 1.00`
- `own_scaling.py --units 200 --limit 1.0`: **exit 1** — `FAIL own scaling: own(200)=0.268s own(800)=1.512s ratio 5.65 > 1.00`
- `own_wave2_subtimers_and_scaling.py --limit 0.0001`: **exit 1** — `FAIL intra-fn own_cap+own_init too slow: 0.0084s > 0.0001s`

### 4. Full `tests/perf` suite (`--no-cache -j 2`)

```
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --verbose --filter perf/
TOTAL 32 PASS 32 FAIL 0 SKIP 0 XFAIL 0
```

### 5. Per-task gate (`tools/taskgate.py`)

```
python tools/taskgate.py --task T494a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T494a.json
```
- `TOTAL 73 PASS 73 FAIL 0 SKIP 0 XFAIL 0` (own: 4/4, affected: 17/17, smoke: 56/56, dedup: 73/73)
- `archcheck: clean (exit 0)` (232 files scanned, 0 violations)
- `BASELINE OK`, `WEAK-NATIVE: 0 in the task's own/changed tests`, `Cache: mismatch none`
- `TASKGATE T494a exit=0`

## Audit of other perf tests (not edited; out of scope)
- `tests/perf/p11_executor/*.ax` (`src/_common.axsrc`): already uses median-of-5 (`median5`) with a generous upper bound (>= 10x slowest MIR-interp figure). No single-shot issue.
- `tests/perf/build_scaling/qa_t494_regalloc_drop_adversarial.py` and `tests/perf/build_scaling/qa_time_passes_and_determinism.py`: correctness, determinism, and sub-timer sum-accounting checks only; no wall-clock ratio/threshold checks.
- `tests/conformance/p15/e15_7_perf_contract/e15_7_conformance_oracle.py`: invokes `tools/perf.py --warmup 0 --runs 1 --check-budgets` (single-shot `--runs 1`).
- `tests/run/perf_contract/perf_contract_oracle.py`: invokes `tools/perf.py --warmup 1 --runs 2 --check-budgets` (2-shot `--runs 2`).

## Spec deviations
none

## Follow-ups
- Optional follow-up if `e15_7_conformance_oracle.py` or `perf_contract_oracle.py` ever flake under load: bump their `tools/perf.py --runs` argument to `3` (min-of-3).

STATUS: COMPLETE round=0
