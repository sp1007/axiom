# T498i QA Report — Update `conformance/stress/f001.ax` and `f002.ax` to declare `let mut p` (`fullrun-4` R1)

## Round 0

### Checks performed

1. **Task spec, report, and diff audit**:
   - `_workspaces/tasks/doing/T498i-fix-stress-f001-f002-mutable-point-binding.md`: owns only `[tests/conformance/stress/f001.ax, tests/conformance/stress/f002.ax]`; locks `[]`; covers `[REQ-TST-072]`.
   - `_workspaces/reports/T498i-report.md`: lists exact two changed files under `## Files changed` and ends with `STATUS: COMPLETE round=0`.
   - `tests/conformance/stress/f001.ax`: declares `let mut p = Point { x: 1, y: 2 };`, takes disjoint `mut_view(p.x)` and `mut_view(p.y)`, mutates both via `*b = *b + 10;`, prints `p.x` and `p.y` matching `// stdout: 11 12\n`, and returns `0` iff `p.x == 11 && p.y == 12` (`1` otherwise). Byte-identical between main tree and `build-snap-T498i/` (`SHA256=756FB62356B8B23F534E947E3B2C754287DE8D780272747CA8F03A4BF94CFBCB`).
   - `tests/conformance/stress/f002.ax`: declares `let mut p = Point { x: 1, y: 2 };` so `let a = mut_view(p);` followed by `let b = mut_view(p.x); //~ ERROR AX_CAP_CONFLICT_MUT` reaches the capability checker without being shadowed by `AX_TYPE_ASSIGN_IMMUTABLE`. Byte-identical between main tree and `build-snap-T498i/` (`SHA256=A26CBAC1F8D1799174F541E526312B6A33191879D3AF50CF19FFD3B97F8802E0`).
   - No extra untracked files added under `tests/conformance/stress/` in main workspace (per task ownership constraint).

2. **Hygiene & freeze checks**:
   - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T498i`: exit 0, 0 `REFUSED` lines (`stage _workspaces/reports/T498i-report.md`, `stage tests/conformance/stress/f001.ax`, `stage tests/conformance/stress/f002.ax`).
   - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: exit 0, `HARNESS OK`.

3. **Stage-2 build inside `build-snap-T498i/`**:
   - Command: `python tools/build_axiomc.py --out build --root . --stage 2`
   - Result: exit 0, `BUILD-AXIOMC OK: build/axiomc2.exe` (`size=8686592`, `sha256=43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6`).

4. **Targeted `axtest.py` (`--no-cache`) inside `build-snap-T498i/`**:
   - Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v conformance/stress/f001.ax conformance/stress/f002.ax`
   - Result: exit 0, `TOTAL 4 PASS 4 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`:
     - `PASS conformance/stress/f001.ax [interp]`
     - `PASS conformance/stress/f001.ax [native]`
     - `PASS conformance/stress/f001.ax [native-O1]`
     - `PASS conformance/stress/f002.ax`

5. **Native-evidence mutation spot-proof inside `build-snap-T498i/` ONLY**:
   - Mutated `build-snap-T498i/tests/conformance/stress/f001.ax` expected stdout from `// stdout: 11 12\n` to `// stdout: 11 13\n`.
   - Command: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v conformance/stress/f001.ax`
   - Mutated result: exit 1, `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` — `interp`, `native`, and `native-O1` all failed at byte 4 (`expected: 11 13\n`, `actual: 11 12\n`).
   - Restored `build-snap-T498i/tests/conformance/stress/f001.ax` byte-identical (`SHA256=756FB62356B8B23F534E947E3B2C754287DE8D780272747CA8F03A4BF94CFBCB`) and re-ran: exit 0, `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.

6. **Task gate (`tools/taskgate.py`) inside `build-snap-T498i/`**:
   - Command: `python tools/taskgate.py --task T498i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T498i.json`

### taskgate T498i (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T498i`, HEAD `ae9a5e4c45f8`, compiler `D:/projects/compiler/new lang/build-snap-T498i/build/axiomc2.exe`, `-j 2`
- change set: 3 file(s) (working tree of build-snap-T498i vs HEAD)
  - `_workspaces/reports/T498i-report.md`
  - `tests/conformance/stress/f001.ax`
  - `tests/conformance/stress/f002.ax`
- wall time: 29.2 s (axtest 25.4 s)

| part | ids | results | PASS | FAIL | SKIP | XFAIL | CACHED |
|---|---|---|---|---|---|---|---|
| own | 2 | 4 | 4 | 0 | 0 | 0 | 0 |
| affected | 2 | 4 | 4 | 0 | 0 | 0 | 0 |
| smoke | 33 | 54 | 54 | 0 | 0 | 0 | 0 |
| **total (dedup)** | 35 | 58 | 58 | 0 | 0 | 0 | 0 |

Counts per group:

| group | ids | failing | parts |
|---|---|---|---|
| build_native | 1 | 0 | smoke |
| conformance | 3 | 0 | affected, own, smoke |
| diff | 2 | 0 | smoke |
| driver | 1 | 0 | smoke |
| encode | 1 | 0 | smoke |
| fuzz | 1 | 0 | smoke |
| hir | 1 | 0 | smoke |
| inspect | 1 | 0 | smoke |
| lex | 1 | 0 | smoke |
| link | 1 | 0 | smoke |
| link2 | 1 | 0 | smoke |
| lir | 1 | 0 | smoke |
| mc | 1 | 0 | smoke |
| mir | 1 | 0 | smoke |
| modules | 1 | 0 | smoke |
| obj | 1 | 0 | smoke |
| opt | 1 | 0 | smoke |
| opt2 | 1 | 0 | smoke |
| parse | 1 | 0 | smoke |
| perf | 1 | 0 | smoke |
| programs | 1 | 0 | smoke |
| resolve | 1 | 0 | smoke |
| run | 2 | 0 | smoke |
| selfhost | 1 | 0 | smoke |
| std | 1 | 0 | smoke |
| tools | 1 | 0 | smoke |
| typeck | 1 | 0 | smoke |
| ui | 2 | 0 | smoke |
| unit | 1 | 0 | smoke |
| verify | 1 | 0 | smoke |

Affected-set derivation (rule per id; rules in `tools/axtest_affected.py`):

- `conformance/stress/f001.ax` <- exact: dependency tests/conformance/stress/f001.ax (+1 more)
- `conformance/stress/f002.ax` <- exact: dependency tests/conformance/stress/f002.ax (+1 more)
- no-op (select nothing): `_workspaces/reports/T498i-report.md`
- unmatched changed files: none

Smoke: seed=1549573189, always `run/str/hello.ax`, `ui/typeck/type_unknown.ax`, `diff/002-arithmetic.ax`; picks build_native=`build_native/stress_4096_jumps.ax`, conformance=`conformance/p5/0114_prog_a_hello.ax`, diff=`diff/opt/const_fold.ax`, driver=`driver/no_args.test`, encode=`encode/atomics/encode_atomics.ax`, fuzz=`fuzz/qa_seed_test.ax`, hir=`hir/basic.ax`, inspect=`inspect/async_layout.test`, lex=`lex/L02_tuple_index.ax`, link=`link/objdump_validate.test`, link2=`link2/multi_mod_pkg`, lir=`lir/div.test`, mc=`mc/isel/vs1_return.ax`, mir=`mir/build/first_mir.ax`, modules=`modules/hello`, obj=`obj/determinism/string_symbols.test`, opt=`opt/qa_dce_run.ax`, opt2=`opt2/qa_boundary_sroa_inline_seam.ax`, parse=`parse/async/async_fn_and_await.ax`, perf=`perf/loop.ax`, programs=`programs/expr_interp.ax`, resolve=`resolve/simple.ax`, run=`run/basic/001-return.ax`, selfhost=`selfhost/kernel/hash_native_current.test`, std=`std/core/qa_primitives.ax`, tools=`tools/build_axiomc_fallback/seed_works.test`, typeck=`typeck/async/await_outside_async_neg.ax`, ui=`ui/typeck/type_return.ax`, unit=`unit/kernel/hash_vectors_current.test`, verify=`verify/uninit_use.test`

Cache: CACHED 0, miss 8, uncacheable 10, stored 7, dep_source exact, verification sample seed=1675066973 n=17 of 17 hits, mismatch none, rejected {}, producer snapshot
WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests
Baseline (`D:\projects\compiler\new lang\build-snap-T498i\_workspaces\baseline-failures.txt`): BASELINE OK
Failing ids: none
archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations
smoke-check (tests/smoke.list): OK; est. worst-case draw 17 s
axtest: `TOTAL 58 PASS 58 FAIL 0 SKIP 0 XFAIL 0` (exit 0)
TASKGATE T498i exit=0

### Findings
None.

## Files changed
(none)

VERDICT: PASS round=0
