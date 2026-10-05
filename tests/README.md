# Axiom tests and the runner `tools/axtest.py`

Every feature is proven by tests; a feature without tests does not exist. Tests are plain files under
`tests/`; the runner discovers them, so **adding a test never edits the runner** (ADR-0005 section 2).
Only T005 edits `tools/axtest.py`.

```
python tools/axtest.py                         # everything (compiler: build/axiom0.exe or $AXIOM0)
python tools/axtest.py run/struct --verbose    # ids containing "run/struct" (positional or --filter)
python tools/axtest.py --json > _workspaces/artifacts/test-results.json
python tools/axtest.py --bless lex/            # rewrite golden files of the selected tests, then review the diff
python tools/axtest.py --list-directive native-after:T033   # files still carrying a directive
python tools/tests/axtest/run_selftests.py     # self-tests of the runner (stub compiler)
```

The runner builds nothing. A task's verdict is given from inside its snapshot with
`--compiler build/axiom0.exe` (see `taskctl.py snapshot`).

## Options

| Option | Meaning |
|---|---|
| `FILTER...`, `--filter TEXT` | run only tests whose id (path under `tests/`, forward slashes) contains the text; repeatable |
| `--compiler PATH` | compiler under test (default `build/axiom0.exe`, env `AXIOM0`); a `*.py` path is run with python; a relative path is taken from the current directory if it exists there, else from the root |
| `--std-root DIR` | passed to the compiler as `--std-root DIR`; default: `--std-root std` **if** the directory `std/` exists, otherwise nothing is passed |
| `--build-dir DIR` | value of the `{build}` placeholder (default: directory of the compiler) |
| `-j N` | parallel tests (default min(8, cpus)); results are always reported sorted by id |
| `--timeout-scale N` | multiply every step timeout (default 1) |
| `--exclude-requires NAME` | SKIP tests with `requires: NAME` (`axiom0-internal` when the compiler under test is axiomc) |
| `--verbose` | print every result and mismatch details |
| `--json` | one JSON document on stdout (`schema`, `features`, `results[]`, `counts`, `total_line`); the `TOTAL` line goes to stderr |
| `--bless` | update golden files (only golden tests run) |
| `--list`, `--list-directive NAME[:VALUE]` | list entries / files and exit 0 |

Output ends with `TOTAL n PASS p FAIL f SKIP s XFAIL x`; FAIL includes XPASS, CRASH and TIMEOUT.
Exit status: 0 when FAIL = 0, 1 otherwise, 2 for a usage error. Zero tests is not a failure.

## Test kinds

A test is one of:

* an `.ax` file whose **leading `//` lines** hold directives (first one: `// test: <kind>`);
* a `*.test` manifest (always kind `exec`);
* a **project directory**: a directory containing `axiom.toml` is one test; its directives are read from
  `src/main.ax`; nothing inside it is discovered separately (the compiler receives the directory;
  `input: src/other.ax` overrides what is passed).

An `.ax` file without a `test:` directive is a FAIL ("missing directive"); a source file that is only a
helper says `// test: helper`. Directories named `fixtures` are never scanned.

| Kind | What the runner does | Result |
|---|---|---|
| `run` | per mode `interp`: `axiom0 run --interp [flags] file [-- args]`; per mode `native`: `axiom0 build [flags] -o exe file`, then the exe. When the compiler advertises `opt` (see Features) every native test also runs as `native-O1` (adds `-O1`) unless the test sets its own `-O` flag | exit code and exact bytes |
| `ui` | `axiom0 check --json [flags] file`; reads the JSON document (schema 1) from **stderr** and compares `(severity, code, line)` with the inline annotations. Missing and unexpected diagnostics both fail; the exit code must be 1 when there are errors, else 0 | annotations |
| `golden` | for every sibling `x.<ext>` of `x.ax`: `axiom0 inspect --emit=<ext> file` stdout must equal the file byte for byte (`.tokens`, `.ast`, `.resolved`, `.hir`, `.thir`, `.mir`, `.lir`, `.mi`, `.mc`, or any new emitter: no runner edit). `emit: ext...` names extensions that `--bless` may create | bytes |
| `diff` | compiles/runs the program as interp, native -O0 and (with `opt`) native -O1; all exit codes and stdout must agree (and match `exit`/`stdout` if given). Fewer than two available executors = SKIP | agreement |
| `exec` | a `*.test` manifest runs one command (see below) | exit, stdout, stderr |

### Features and modes

`<compiler> --features` prints one capability per line (`interp`, `native`, `opt`, ...). A run mode the
compiler does not advertise is SKIP "mode unavailable: <mode>"; a missing, crashing or failing
`--features` means no capabilities, never an error. `ui`, `golden` and `exec` need no capability.

### Exec manifests

```
# tests/unit/kernel.test
cmd: {build}/axiom0-unit
exit: 0
stdout-contains: UNIT
skip-unless: tool gcc
requires: axiom0-internal
```

Lines are `name: value`; `#` starts a comment line; unknown names are an error. Placeholders in `cmd:`
(expanded per word after splitting, so paths with spaces are safe): `{compiler}`, `{build}`, `{root}`,
`{test_dir}`, `{tmp}` (a private scratch directory, removed afterwards), `{std_root}`. A first word of
`python`/`python3` or ending in `.py` runs the interpreter that runs axtest; a path without extension
gets `.exe` if needed. Commands run with the repository root as working directory.

## Directives

| Directive | Applies to | Meaning |
|---|---|---|
| `test: run\|ui\|golden\|diff\|helper` | .ax | the kind (manifests are `exec`) |
| `exit: N` | run, diff, golden, exec | expected exit code (default 0; for `golden` the exit code of `inspect`) |
| `stdout: TEXT` | run, diff, exec | exact expected stdout; repeated lines are concatenated; **no newline is implied**, write `\n` |
| `stderr: TEXT` | same | exact expected stderr |
| `stdout-contains: TEXT`, `stderr-contains: TEXT` | same | substring must occur; repeatable |
| `stdin: TEXT` | run, diff, exec | bytes sent to the program (interp: to the `run --interp` process) |
| `args: A B 'C D'` | run, diff, exec | program arguments (shell-like splitting, not Windows backslash rules) |
| `env: NAME=value` | run, diff, exec | environment of the program (interp: of the compiler process); repeatable |
| `modes: interp native` | run | restrict the modes; QA fails a restriction without an accepted reason (axiom-testing) |
| `target: TRIPLE` | all but exec | `--target TRIPLE` |
| `flags: -O1 ...` | all but exec | extra compiler flags (before the input) |
| `timeout: S` | all | seconds per step (default 10; `--timeout-scale` multiplies) |
| `xfail: T123 reason` | all | expected failure for a spec gap with an ADR and an open task |
| `native-after: T033` | run, diff | native mode is SKIP "native after T033" until the named catch-up task removes the directive |
| `skip-unless: tool NAME`, `skip-unless: feature NAME` | all | SKIP when the tool is not on PATH / the compiler does not advertise the feature |
| `requires: axiom0-internal` | all | test of the C implementation; SKIP under `--exclude-requires axiom0-internal` |
| `emit: ext...` | golden | extensions `--bless` may create |
| `input: path` | project dirs, files | what is passed to the compiler (relative to the test) |
| `cmd: ...` | exec | the command |

Values of `stdout`, `stderr`, `stdin` and `*-contains` are decoded as UTF-8 text with the escapes
`\n \r \t \0 \\ \xHH \u{HHHH}`; `\xHH` is one raw byte, so an invalid UTF-8 sequence can be written.
Only the first space after the colon is dropped. Unknown comment lines such as `// Note: ...` are
ignored; a malformed value of a known directive is a FAIL of the test.

Inline annotations of `ui` tests: `//~ ERROR AX_CODE` (this line), `//~^ ERROR AX_CODE` (the previous
line, `^^` two lines up), `//~ WARN AX_CODE`, and `//~? ERROR AX_CODE` for a diagnostic that has no
position. In project directories an annotation in a file other than `src/main.ax` only matches a
diagnostic whose `primary.file` ends with that file's path relative to the project.

## States

| State | Meaning | Counts as |
|---|---|---|
| PASS | all expectations met | PASS |
| FAIL | an expectation was not met (message names it, with a hex window for byte mismatches) | FAIL |
| SKIP | never silent: the reason is printed (`--verbose`) and in the JSON | SKIP |
| XFAIL | a test with `xfail:` failed (only FAIL becomes XFAIL; a crash or timeout stays one) | XFAIL |
| XPASS | a test with `xfail:` passed: remove the directive | FAIL |
| CRASH | the compiler crashed (ICE banner below, or death by signal / access violation), or a program died with a crash status it was not expected to have | FAIL |
| TIMEOUT | a step exceeded its timeout, or the interpreter hit a limit (below) | FAIL |

**Compiler crash is recognised by the banner, not by exit code 3** (SPEC-03 AXS-SEM-082): a test
program may legitimately exit with 3, and the compiler step and the program are separate. The runner
looks for a line of the compiler's stderr starting with `internal compiler error` or
`error: internal compiler error` (case-insensitive). The pattern is the single constant
`ICE_BANNER_RE` in `tools/axtest.py`; T009/T016 fix the final banner text and, if it differs from this
pattern, the constant is the only thing to edit. Exit code 3 without the banner is an ordinary exit code.

**Interpreter limits** (AXS-SEM-090/091): `axiom0 run --interp` that exits 124 *and* prints a
diagnostic whose code starts with `AX_DRIVER_INTERP_` (step limit or call-depth limit) is TIMEOUT, not
FAIL. A test that deliberately expects the limit says `exit: 124` (and `stderr-contains:
AX_DRIVER_INTERP_`); then it is an ordinary comparison. Exit 124 without such a diagnostic is a normal
exit code. Exit 125 (`AX_UNSAFE_INTERP_UB`) is an ordinary exit code: tests of it say `exit: 125`.

## Byte exactness

All subprocess I/O is binary. The runner never decodes stdout/stderr through a text layer: a stray
`\r` or a wrong UTF-8 byte is a FAIL. The canonical sample is `Xin chào thế giới` (22 bytes + LF):

```axiom
// test: run
// stdout: Xin chào thế giới\n
fn main() { ... }
```

Write test and golden files with the Write/Edit tools (LF, UTF-8); from Python on Windows use
`open(path, "w", encoding="utf-8", newline="\n")`. Blessed golden files must be reviewed.

## How later tasks add tests (no runner edit)

* a run/ui/golden/diff test: add `tests/<area>/<name>.ax` with its directives (and `<name>.<ext>` goldens);
* a C unit test: `tests/unit/**/*.c` (globbed by CMake); a C driver: `tests/**/cdriver_*.c` plus a
  `*.test` manifest that runs `{build}/tests/ct_<path>`;
* an encoder/object/link check: a `*.test` manifest running a script or driver, `skip-unless: tool gcc`;
* a catch-up task for a `native-after: Txxx` directive removes it and verifies
  `python tools/axtest.py --list-directive native-after:Txxx` prints nothing;
* a new compiler capability: advertise it in `--features`; a new `inspect --emit=<ext>` emitter needs
  only golden files with that extension.

Binary fixtures are allowed only under `tests/**/fixtures/` (git-ignored elsewhere).

## Self-tests

`python tools/tests/axtest/run_selftests.py [-v] [substring]` runs the runner against the stub compiler
`tools/tests/axtest/stubcc.py`, whose behaviour comes from `//@` lines in the test source (see its
docstring). They cover every directive, kind and state, including the exact 23-byte greeting, a CRLF
variant, a wrong-UTF-8-byte variant, `native-after`, `xfail`/XPASS, ICE-banner CRASH, exit-code-3 program,
TIMEOUT, interpreter limit, missing `--features`, `--exclude-requires`, exec manifests and project directories.
The hidden option `--exe-suffix` lets the stub write Python scripts as "executables".
