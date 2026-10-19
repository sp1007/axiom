# T085c QA Gate Report — Port Compiler Driver & Pipeline CLI to Axiom

## Round 0

### 1. Task & Change Set Audit
- **Task File**: `_workspaces/tasks/doing/T085c-port-driver-to-axiom.md`
- **Engineer Report**: `_workspaces/reports/T085c-report.md` (ends with `STATUS: COMPLETE round=0`)
- **`taskctl.py changes T085c`**:
  - All modified and added files lie strictly within `paths: [compiler/driver, tests/selfhost/driver]` plus the task reports (`_workspaces/reports/T085c-report.md`, `_workspaces/reports/T085c-qa.md`).
  - Zero `REFUSED` lines, zero shared-file violations.

### 2. Implementation & Spec Verification
- **Driver CLI & Option Parsing (`compiler/driver/opts.ax`)**:
  - Complete port of CLI command dispatch (`help`/`--help`/`-h`, `version`, `--features`, `inspect`, `check`, `build`, `run`), emitter lookup (`ast`, `hir`, `lir`, `mc`, `mi`, `mir`, `mir-opt`, `obj`, `resolved`, `thir`, `tokens`), option parsing (`--color=never`, `--time-passes`, `--json`, `-O0`, `-O1`, `--verify-each`, `--target`, `--std-root`, `-o`, `--emit`, `--stack-reserve`, `--interp`, `--step-limit`, `--max-call-depth`, `--` pass-through), target triple validation (`x86_64-pc-windows-msvc` vs `AX_DRIVER_UNKNOWN_TARGET`), `axiom.toml` manifest parser, `find_std_root_with` / `find_std_root` hierarchy, `derive_module_path`, and multi-file `project_discover` with lexicographical sorting and implicit `std.core.{option,result,prelude,host}` injection.
- **Compilation Pipeline & Emitters (`compiler/driver/pipeline.ax`, `compiler/driver/mod.ax`)**:
  - Complete stage orchestration (`STAGE_SOURCE`, `STAGE_LEX`, `STAGE_PARSE`, `STAGE_RESOLVE`, `STAGE_HIR`, `STAGE_TYPECK`, `STAGE_OWN`, `STAGE_INTERP`, `STAGE_MONO`) with `--time-passes` nanosecond formatting (`format_pass_time`), human and `--json` diagnostic flushing (`driver_flush_diagnostics`), all 11 `inspect --emit=<kind>` emitters (including standalone `.mir` inputs), `check`, `run` (with panic message forwarding and exit codes), and `build` (emitting relocatable COFF `.obj` via `--emit=obj` or linked PE32+ `.exe` with `ax_main` symbol and `--stack-reserve`).
- **Syntax & Layer Conformance (AXS-SELF-001..004)**:
  - Canonical Axiom syntax (`=` bindings, `.` module/member paths) verified across `compiler/driver/opts.ax` (2,269 lines), `compiler/driver/pipeline.ax` (2,033 lines), and `compiler/driver/mod.ax` (115 lines).
  - `python tools/archcheck.py` inside `build-snap-T085c`: `188 files scanned, 0 violations`.
- **Mode Check**:
  - `qa_driver_cli_and_project.ax`, `qa_driver_boundary_edges.ax`, `qa_driver_inspect_diff_a.ax`, and `qa_driver_commands_a.ax` run in `modes: interp native` (`[interp]`, `[native]`, `[native-O1]`); the heavy full-std/multi-file bundles `qa_driver_inspect_diff_b.ax` and `qa_driver_commands_b.ax` (~80k lines) are paired with their `*_a.ax` interp+native twins per `axiom-testing`.

### 3. Build & Test Verification (in `build-snap-T085c`)
- **Build (`cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build`)**:
  - Built cleanly with 0 warnings.
- **Architecture Layer Check (`python tools/archcheck.py`)**:
  - `archcheck: 188 files scanned, 0 violations`
- **Relevant Test Suites (`python tools/axtest.py --compiler build/axiom0.exe selfhost/driver selfhost/backend selfhost/link selfhost/obj driver e2e`)**:
  - `TOTAL 70 PASS 70 FAIL 0 SKIP 0 XFAIL 0` (including the 3 new modes from `qa_driver_boundary_edges.ax`).

### 4. QA Boundary Cross-Check
- Added `tests/selfhost/driver/qa_driver_boundary_edges.ax` (and updated `tests/selfhost/driver/gen_driver_tests.py`) testing:
  1. `version` and `--features` with unexpected trailing arguments (`AX_EXIT_USAGE` + byte-exact error text).
  2. `inspect --emit=` with empty emitter name and `inspect --emit=ast` with multiple input files (`AX_EXIT_USAGE` + byte-exact error text).
  3. Unsupported `--target=x86_64-unknown-linux-gnu` diagnostic (`[AX_DRIVER_UNKNOWN_TARGET]` + `AX_EXIT_USAGE`).
  4. `--` argument pass-through where arguments after `--` start with `-` (`-O1`, `--json`, `--unknown-opt`), verifying they are not parsed as compiler flags and are preserved in `run_args`.
  5. `derive_module_path` with Windows backslashes (`src\nested\dir\item.ax` -> `nested.dir.item`) and root-level files (`standalone.ax` -> `standalone`).
  6. `project_discover` negative and directory-root seams: nonexistent input file (`AX_IO_FILE_NOT_FOUND`), nonexistent explicit `--std-root` (`AX_DRIVER_NO_STD`), and direct package directory path (`tests/modules/hello`).

## Files changed

- `tests/selfhost/driver/gen_driver_tests.py`
- `tests/selfhost/driver/qa_driver_boundary_edges.ax`

## Verdict

VERDICT: PASS round=0
