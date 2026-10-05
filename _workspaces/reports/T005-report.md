# T005 report

## Summary
`tools/axtest.py` (Python 3 stdlib only) is the complete test runner: discovery of `tests/**.ax`, `*.test`
manifests and project directories; kinds `run`, `ui`, `golden`, `diff`, `exec`; every directive of the task
scope; the seven result states; `--filter` (also positional), `--verbose`, `--json`, `--bless`, `--compiler`,
`--std-root`, `-j`, `--timeout-scale`, `--exclude-requires`, `--list`, `--list-directive`. All subprocess I/O is
binary; expected `stdout:` is decoded from UTF-8 escapes and compared byte for byte, with a hex window in the
message. Documentation: `tests/README.md`. Self-tests: `tools/tests/axtest/` (67 tests, ~27 s).

### Verification (inside `build-snap-T005`)
- `python tools/tests/axtest/run_selftests.py` -> `SELFTEST 67 tests, 0 failures, 0 errors`.
- `bash tools/ci.sh` (gcc and clang, ctest, then `axtest.py --compiler <abs msys path>`) -> `ci: OK (gcc clang)`,
  `TOTAL 0 PASS 0 FAIL 0 SKIP 0 XFAIL 0` (there are no tests yet).
- Against the real `axiom0.exe` with scratch exec manifests (`version`, `--features`, `inspect --emit=nope`
  exit 2): PASS, and run tests SKIP "mode unavailable" because `--features` is empty.
- The self-tests use a root path that contains a space (like the real repository path).

### Additional requirement from the architect (SPEC-03 AXS-SEM-082/091), done
1. `axiom0 run --interp` that exits 124 **and** prints an `AX_DRIVER_INTERP_*` diagnostic is TIMEOUT, not FAIL
   (constants `INTERP_LIMIT_EXIT`, `INTERP_LIMIT_CODE_PREFIX`). Decision: a test that itself says `exit: 124`
   is an ordinary comparison (so tests of the limit can exist and PASS); exit 124 without such a diagnostic is a
   plain exit code. Exit 125 (`AX_UNSAFE_INTERP_UB`) is an ordinary exit code too.
2. A compiler crash (CRASH) is detected by the ICE banner on the compiler's stderr, **not** by exit code 3. The
   banner pattern is the single constant `ICE_BANNER_RE` in `tools/axtest.py` (a line starting with
   `internal compiler error` or `error: internal compiler error`, case-insensitive, multiline), documented in
   `tests/README.md`; T009/T016 may only need to edit that constant. A banner with exit code 1 is CRASH; exit
   code 3 without banner is an ordinary exit code (a program that exits 3 passes when `exit: 3`); a death by
   signal / status >= 0xC0000000 is CRASH too. The program's own stderr is never scanned for the banner.
   Self-tests: `test_crash_by_ice_banner_exit_3`, `test_crash_by_banner_with_other_exit_code`,
   `test_program_exit_3_without_banner_is_not_a_crash`, `test_banner_only_counts_on_compiler_stderr_lines_start`,
   `test_ice_banner_pattern`, `test_interp_limit_exit_124_with_diagnostic_is_timeout`,
   `test_exit_124_without_limit_diagnostic_is_plain_fail`, `test_limit_test_that_expects_124_passes`.
- Coordinator note (T002 gate): diagnostics, human and `--json`, are on stderr. The `ui` kind reads the schema-1
  JSON document from stderr (last stderr line that is a JSON object with `diagnostics`) and keeps stdout for
  program output; self-tests use a stub that writes JSON to stderr only.

### Design decisions (recorded, no ADR needed; all local to the runner)
- Compiler CLI contract assumed (from T016/T004/AXD-043/063): `--features`; `check --json [flags] input`;
  `inspect --emit=<ext> [flags] input`; `run --interp [flags] input [-- args]`; `build [flags] -o exe input`.
  Flags order: `--std-root`, `--target`, `flags:`, then input. A project directory is passed as the input
  (`input:` overrides); T060 can change that only through the `input:` directive.
- `--std-root`: passed when given explicitly, or `--std-root std` when `<root>/std` exists; otherwise nothing is
  passed (a compiler older than T060 would reject an unknown option and every test would fail).
- Features advertised by `--features` used by the runner: `interp`, `native`, `opt`. With `opt`, native run
  tests also run as `native-O1` (skill: "every run test also runs at -O1 when the optimizer lands") unless the
  test has its own `-O` flag; `diff` compares interp, native -O0 and (with `opt`) native -O1, needing >= 2.
- `.ax` file without `test:` is a FAIL (a silently unrun test is worse); `test: helper` opts out; `fixtures`
  directories are never scanned; unknown comment lines are ignored, malformed values of known directives fail.
- `xfail`: only FAIL becomes XFAIL; CRASH/TIMEOUT stay failures (an implementation crash is not a spec gap).
- `--json`: JSON document on stdout, the `TOTAL` line on stderr (keeps stdout parseable).
- Extensions beyond the task text, all documented: `stdout-contains`/`stderr-contains`, `emit:` (names golden
  extensions `--bless` may create), `input:`, `skip-unless: feature <name>`, `//~? ERROR CODE` (diagnostic
  without position), `--build-dir`, `--list`, positional filters, hidden `--exe-suffix` (self-test hook).
- Windows details: MSYS paths (`/d/x/axiom0.exe`, as `bash tools/ci.sh` passes) are converted to `D:/x/...`;
  relative `--compiler` is taken from the cwd, else from the root; timeouts kill the process tree (`taskkill`).
  Placeholders of exec manifests are substituted per word after splitting, so paths with spaces work (found by
  the space in the real repo path while writing the self-tests).

## Follow-ups
- MS-P1 in `spec/SPEC-00-bootstrap.md` lists `tests/axtest` in `must_pass`. A manifest `tests/axtest/selftests.test`
  (`cmd: python tools/tests/axtest/run_selftests.py`, `timeout: 120`, `requires: axiom0-internal` not needed) would
  make the runner self-tests part of the suite and satisfy that entry; it is outside this task's paths, so the
  architect / gate T022 should add it (or reword `must_pass`).
- T016 should print the final ICE banner and either match `ICE_BANNER_RE` or adjust that constant (QA of T016).

## Files changed
- tools/axtest.py
- tools/tests/axtest/run_selftests.py
- tools/tests/axtest/stubcc.py
- tools/tests/axtest/test_axtest.py
- tests/README.md

STATUS: COMPLETE round=0
