# T449b QA Gate Report (round 0)

## Scope & Audit Summary

Audited `_workspaces/tasks/doing/T449b-harness-regenerate-std-live-source-bundles.md`, `_workspaces/reports/T449b-report.md`, and the full `git diff` across all 13 modified files:
- `.claude/skills/axiom-tasks/scripts/bundles.py`
- `.claude/skills/axiom-tasks/scripts/taskctl.py`
- `.claude/skills/axiom-tasks/scripts/selftest.py`
- `.claude/skills/axiom-tasks/SKILL.md`
- `.claude/skills/axiom-testing/SKILL.md`
- 8 `tests/std/**/gen_tests.py` scripts

### 1. Independent Generator Inventory Verification
Scanned all tracked `tests/**/*.py`, `tools/*.py`, and `tests/**/*bundle*.test` outside `tests/selfhost/`:
- Confirmed **12** class-(a) live-source bundle generators exist outside `tests/selfhost/`, and all 12 are explicitly listed in `bundles.EXTRA_GENERATORS`:
  - `tests/std/async/executor/gen_tests.py` (9 bundles)
  - `tests/std/async/structured/gen_tests.py` (16 bundles)
  - `tests/std/async/waker/gen_tests.py` (4 bundles)
  - `tests/std/async/waker_qa/gen_tests.py` (5 bundles)
  - `tests/std/channel/gen_tests.py` (8 bundles)
  - `tests/std/fiber/gen_tests.py` (30 bundles)
  - `tests/std/sync/gen_tests.py` (9 bundles)
  - `tests/std/thread/native_panic_hook/gen_tests.py` (2 bundles)
  - `tests/conformance/p11/e11_3_threads_sync/gen_tests.py` (8 bundles)
  - `tests/conformance/p11/e11_5_executors/gen_tests.py` (9 bundles)
  - `tests/conformance/p11/e11_6_async_io/gen_tests.py` (1 bundle)
  - `tests/perf/p11_executor/gen_tests.py` (4 bundles)
- Confirmed **0** class-(a) live-source generators were missed and **0** class-(b) static-fixture generators (including `tests/std/num/gen_tests.py`, `tests/conformance/p12/e12_1_integers/gen_conformance.py`, `tests/std/float_fmt/{make_vectors,qa_adv_gen,qa_adv_ops_gen}.py`, `tests/std/math/{gen_tables,make_vectors}.py`, `tools/gen_encode_tests.py`, etc.) were included in `EXTRA_GENERATORS`.

### 2. Determinism & Harness Contract Verification
- All 12 `EXTRA_GENERATORS` resolve `ROOT` from `__file__`, do not invoke `subprocess` or any compiler in write mode, and support `--check`.
- All 8 modified `tests/std/**/gen_tests.py` emit `wrote <rel>` relative to `ROOT`.
- The 4 allowlisted conformance/perf generators (`tests/conformance/p11/**`, `tests/perf/p11_executor/`) emit `Generated <rel>`, which `bundles._run_group` resolves relative to the generator's directory only for `_EXTRA_SET`.
- `taskctl.py` `touches_bundle_inputs()` now treats edits to `bundles.py` as bundle-affecting so `accept` refreshes `tests/selfhost/generated-files.txt`. `bundles_for_commit()` stages regenerated bundles from the snapshot, enforces REGATE checks (exit 5 on mismatch), and removes retired outputs cleanly.
- Out-of-scope hygiene: `docs/`, `bootstrap/axiom0/`, and `.claude/settings.json` are untouched.

## Independent Verification Results

- `python .claude/skills/axiom-tasks/scripts/bundles.py list --root build-snap-T449b`: **PASS** (exit 0; 265 known generated paths covering all 105 outputs across all 12 class-(a) generators + selfhost bundles and manifest).
- `python .claude/skills/axiom-tasks/scripts/bundles.py check --root build-snap-T449b -j 4`: **PASS** (exit 0; `bundles check: 48 generator(s), 0 file(s), 31s`). Note: on the main tree, all 12 class-(a) generators also passed; 11 selfhost MIR/backend generators differed solely due to an unrelated concurrent task's uncommitted `compiler/mir/builder.ax` in the main tree.
- `python .claude/skills/axiom-tasks/scripts/selftest.py`: **PASS** (exit 0; **159/159 checks passed**, including all 3 new T449b tests verifying class-(a) std/conformance regen/snapshot/accept staging and class-(b) exclusion).
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: **PASS** (exit 0; `HARNESS OK`).
- **Simulated `std/` mutation check** (inside `build-snap-T449b/` only, cleanly restored):
  1. Appended `// T449b QA simulated mutation` to `build-snap-T449b/std/sync/atomic.ax`.
  2. `bundles.py check --root build-snap-T449b -j 4` -> **exit 1** (`bundles check: 48 generator(s), 0 file(s), 27s, 12 FAILED`) — stale bundles detected.
  3. `bundles.py regen --root build-snap-T449b -j 4` -> **exit 0** (`bundles regen: 48 generator(s), 165 file(s), 30s`).
  4. `bundles.py check --root build-snap-T449b -j 4` -> **exit 0** (`bundles check: 48 generator(s), 0 file(s), 36s`).
  5. Direct freshness checks: `tests/std/sync/gen_tests.py --check` (`OK sync bundles match live std/sync`, exit 0) and `tests/conformance/p11/e11_3_threads_sync/gen_tests.py --check` (`OK conformance bundles match live std sources`, exit 0).
  6. Restored `std/sync/atomic.ax` to original bytes, ran `bundles.py regen` (exit 0) and `bundles.py check` (exit 0) — snapshot restored cleanly.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T449b`: **PASS** (exit 0; 0 `REFUSED`, 14 stageable files matching report).

## Files changed

(none)

## Verdict

VERDICT: PASS round=0
