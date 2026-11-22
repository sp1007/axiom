# T494a QA report

## Round 0

Independent QA gate review of T494a by `axiom-architect` (task owned by `axiom-qa`). All builds, adversarial invocations, and test suites ran inside `build-snap-T494a/` against freshly verified stage-2 `build/axiomc2.exe` (`HEAD 2d69ea8d1487`, `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`, `sha256=60c096c3ff5c8ab75676806a99421ed8a2d147b2f4ac433e15725d09dbebfb68`).

### 1. Harness and change-set checks

- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T494a`:
  ```
  stage _workspaces/reports/T494a-report.md
  stage tests/perf/build_scaling/build_scaling.py
  stage tests/perf/own_scaling/own_scaling.py
  stage tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py
  ```
  0 `REFUSED` lines; all 3 code edits are within T494a's `paths:`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (exit 0).
- `git -C build-snap-T494a status -s`: only the 3 Python scripts and `_workspaces/reports/T494a-report.md` modified/untracked. None of the 4 `.test` manifests were weakened or broken (`timeout: 900` / `300`, `exit: 0`, `stdout-contains` intact).

### 2. Code review of changed scripts

- `tests/perf/build_scaling/build_scaling.py`:
  - Uses `--samples` (default `3`, guarded by `if a.samples < 1: raise ValueError(...)`).
  - Uses `min(...)` per timer (`build`, `frame`, `isel`, `mir_build`, `lir`, `mir_drop`) for all ratio/budget checks while computing and printing `samples=[...]`, `min`, and `med` on `stderr`.
  - Preserves all limits and `max(t, 0.05)` floors on `build`, `frame`, `frame/ir`, and `(frame+isel)/ir`.
  - Any non-zero compiler or executable exit raises `RuntimeError` immediately (no crash hiding).
- `tests/perf/own_scaling/own_scaling.py`:
  - Uses `--samples` (default `3`, guarded by `a.samples < 1`), computes `min` and `median` of `own`, prints all samples + `min` + `med` on `stderr`, and checks `own(4N) / max(own(N), 0.05) <= limit` using `min`.
- `tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py`:
  - Uses `--samples` (default `3`, guarded by `a.samples < 1`) and `--limit` (default `2.0`).
  - Validates `parse_own_timers` (`time-own:` order and sum accounting) on every sample, takes `min` of `own_cap` and `own_init`, prints all samples + `min` + `med` on `stderr`, and checks `min(own_cap) + min(own_init) <= a.limit`.
  - Preserves `-O0`/`-O1` determinism and `OWN_WAVE2_OK` execution checks.

### 3. Adversarial and edge-case verification (in `build-snap-T494a/`)

1. **Invalid `--samples` handling** (all 3 scripts):
   - `--samples 0`: exit 1 (`ValueError: --samples must be >= 1`)
   - `--samples -1`: exit 1 (`ValueError: --samples must be >= 1`)
   - `--samples abc`: exit 2 (`error: argument --samples: invalid int value: 'abc'`)
2. **Single failing compile sample inside min-of-3** (shim compiler crashing with exit 3 on sample 2 of 3):
   - `build_scaling.py --samples 3 --units 10`: exit 1, surfaced `SIMULATED COMPILER CRASH ON SAMPLE 2`
   - `own_scaling.py --samples 3 --units 10`: exit 1, surfaced `SIMULATED COMPILER CRASH ON SAMPLE 2`
   - `own_wave2_subtimers_and_scaling.py --samples 3 --small 5 --large 10`: exit 1, surfaced `SIMULATED COMPILER CRASH ON SAMPLE 2`
3. **`--samples 1` single-sample mode**:
   - `own_scaling.py --units 20 --samples 1`: exit 0, `own(20)=min 0.030s`, `own(80)=min 0.161s`, `ratio 3.21` (confirms `max(0.030, 0.05) = 0.05` floor is active: `0.161 / 0.05 = 3.21`).
   - `own_wave2_subtimers_and_scaling.py --small 10 --large 20 --samples 1`: exit 0, `OK own_wave2_subtimers_and_scaling`.
   - `build_scaling.py --units 20 --samples 1`: printed 1-element `samples=[...]` with `min == med` as expected.
4. **Forced-limit regression checks (default `--samples 3`, all must FAIL with exit 1)**:
   - `python tests/perf/build_scaling/build_scaling.py --compiler build/axiomc2.exe --tmp build/qa_adv_tmp --opt O0 --units 60 --limit 1.0`:
     - exit 1, stdout: `FAIL build scaling: build(60)=0.270s build(240)=1.052s ratio 3.90 > 1.00`
     - stderr confirmed `samples=[0.280, 0.270, 0.274] min=0.270s med=0.274s` and `samples=[1.079, 1.052, 1.184] min=1.052s med=1.079s`, ratio `3.90` computed from `min` (not `med 3.93`).
   - `python tests/perf/build_scaling/build_scaling.py --compiler build/axiomc2.exe --tmp build/qa_adv_tmp --opt O1 --units 60 --limit 1.0 --frame-limit 5.5 --frame-to-ir-limit 2.6 --hot-to-ir-limit 4.0`:
     - exit 1, stdout: `FAIL build scaling: build(60)=0.244s build(240)=1.076s ratio 4.41 > 1.00`
     - stderr confirmed `samples=[0.247, 0.316, 0.244] min=0.244s` and `samples=[1.076, 1.313, 1.160] min=1.076s` (rejected jitter spike `1.313s`).
   - `python tests/perf/own_scaling/own_scaling.py --compiler build/axiomc2.exe --tmp build/qa_adv_tmp --units 80 --limit 1.0`:
     - exit 1, stdout: `FAIL own scaling: own(80)=0.100s own(320)=0.457s ratio 4.59 > 1.00`
     - stderr confirmed `samples=[0.102, 0.100, 0.165] min=0.100s` and `samples=[0.507, 0.562, 0.457] min=0.457s`.
   - `python tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py --compiler build/axiomc2.exe --tmp build/qa_adv_tmp --limit 0.0001`:
     - exit 1, stdout: `FAIL intra-fn own_cap+own_init too slow: 0.0094s > 0.0001s`
     - stderr confirmed `own_cap min=0.0026s`, `own_init min=0.0068s`, `own_cap+own_init min=0.0094s (med 0.0107s)`.

### 4. Full `tests/perf` suite (`--no-cache -j 2`)

```
python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 --verbose --filter perf/
CACHED 0 HITS 0 MISS 9 UNCACHEABLE 11 STORED 9 dep_source=exact (reads disabled: --no-cache)
WEAK-NATIVE 0
TOTAL 32 PASS 32 FAIL 0 SKIP 0 XFAIL 0
```

### 5. Per-task gate (`tools/taskgate.py`)

```
python tools/taskgate.py --task T494a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T494a.json
```

### taskgate T494a (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T494a`, HEAD `2d69ea8d1487`, compiler `D:/projects/compiler/new lang/build-snap-T494a/build/axiomc2.exe`, `-j 2`
- change set: 4 file(s) (working tree of build-snap-T494a vs HEAD)
  - `_workspaces/reports/T494a-report.md`
  - `tests/perf/build_scaling/build_scaling.py`
  - `tests/perf/own_scaling/own_scaling.py`
  - `tests/perf/own_scaling/own_wave2_subtimers_and_scaling.py`
- wall time: 96.6 s (axtest 92.3 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 4 | 4 | 4 | 0 | 0 | 0 | 0 |
| affected | 13 | 17 | 17 | 0 | 0 | 0 | 0 |
| smoke | 33 | 54 | 54 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 46 | 71 | 71 | 0 | 0 | 0 | 0 |

- Affected-set derivation: 13 ids across `perf/build_scaling/` and `perf/own_scaling/`; unmatched changed files: none.
- Cache: `CACHED 0, miss 10, uncacheable 16, stored 9, dep_source exact, verification sample seed=1137651955 n=20 of 20 hits, mismatch none, rejected {}, producer snapshot`
- `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
- `Baseline: BASELINE OK`, `Failing ids: none`
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 24 s`
- `axtest: TOTAL 71 PASS 71 FAIL 0 SKIP 0 XFAIL 0 (exit 0)`
- `TASKGATE T494a exit=0`

### Findings
none

## Files changed
none

VERDICT: PASS round=0
