# T498i Report — Update `conformance/stress/f001.ax` and `f002.ax` to declare `let mut p` (`fullrun-4` R1)

## Summary
Updated both early capability stress tests to declare `let mut p = Point { x: 1, y: 2 };` so `mut_view(p.x)` / `mut_view(p.y)` / `mut_view(p)` are checked on a mutable struct owner per `SPEC-02 AXS-GRM-041`, `SPEC-03 AXS-SEM-047`, and `SPEC-11 AXS-CAP-002`:
- `tests/conformance/stress/f001.ax`: changed `let p` to `let mut p`, mutated both disjoint `mut_view<i32>` fields (`*b = *b + 10;`), printed `p.x` and `p.y` with `// stdout: 11 12\n`, and returned `0` only when `p.x == 11 && p.y == 12` (`1` otherwise) so `WEAK-NATIVE 0` holds across `interp`, `native`, and `native-O1`.
- `tests/conformance/stress/f002.ax`: changed `let p` to `let mut p` so `mut_view(p)` followed by `mut_view(p.x)` reaches the capability checker and emits `AX_CAP_CONFLICT_MUT` on the annotated line.

## Files changed
- `tests/conformance/stress/f001.ax`
- `tests/conformance/stress/f002.ax`

## Verification (isolated snapshot `build-snap-T498i`)
- Snapshot creation: `python .claude/skills/axiom-tasks/scripts/taskctl.py snapshot T498i` -> created `build-snap-T498i` from HEAD `ae9a5e4` + 2 changed files of T498i.
- Stage-2 build: `python tools/build_axiomc.py --out build --root . --stage 2` -> `BUILD-AXIOMC OK` (`axiomc2.exe`, `size=8686592`, `sha256=43161765bb6b77cf3c69cc2d42c1e8b6eda641f3bbfa7bfdca0ba963f1022af6`, `FIXED-POINT (O1) OK`, `STAGE0-GUARD OK`).
- Targeted `axtest`: `python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v conformance/stress/f001.ax conformance/stress/f002.ax` -> `TOTAL 4 PASS 4 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Mutation spot-proof on `build-snap-T498i/tests/conformance/stress/f001.ax`:
  - Perturbed `// stdout: 11 12\n` -> `// stdout: 11 13\n`: `TOTAL 3 PASS 0 FAIL 3 SKIP 0 XFAIL 0` (`interp`, `native`, `native-O1` all failed at byte 4).
  - Restored byte-identical (`SHA256=756FB62356B8B23F534E947E3B2C754287DE8D780272747CA8F03A4BF94CFBCB`): `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Task gate: `python tools/taskgate.py --task T498i --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2` -> `TASKGATE T498i exit=0`, `TOTAL 58 PASS 58 FAIL 0 SKIP 0 XFAIL 0`, `BASELINE OK`, `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`, `archcheck: 232 files scanned, 0 violations`.

STATUS: COMPLETE round=0
