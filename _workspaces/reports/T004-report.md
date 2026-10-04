# T004 report

## Summary
Repository skeleton, CMake/Ninja build and CI scripts for `axiom0` (C11). After this task nobody edits
`CMakeLists.txt`, `cmake/*`, `main.c` or the CI scripts; later tasks only add files.

- **Build** (`bootstrap/axiom0/CMakeLists.txt` + `cmake/AxiomRegistry.cmake`, `cmake/AxiomTests.cmake`,
  templates `registry.c.in`, `unit_main.c.in`): C11 without extensions, `-Wall -Wextra -Wpedantic -Werror`
  for gcc and clang (shared `ax_flags` interface library; `-DAX_WERROR=OFF` to relax, `-DAX_SANITIZE=ON` for
  ASan+UBSan), default build type Debug, other compilers rejected at configure time. `src/**/*.c` (all but
  `driver/main.c`) goes into the static library `axiom0_core` (+ the generated registry); `axiom0` is
  `main.c` + the library, output `build/axiom0(.exe)`. Globs use `CONFIGURE_DEPENDS` and are sorted.
- **Driver as registries (ADR-0005 section 2)**: `src/driver/driver.h` is the public header (exit codes
  `AX_EXIT_*`, `AxIo`, `AxCommand`, `AxEmitter`). `cmd_<name>.c` defines `const AxCommand axcmd_<name>`,
  `emit_<name>.c` defines `const AxEmitter axemit_<name>`; CMake generates NULL-terminated tables at
  configure time (plain C11, no constructor attributes). The user-visible name is the struct's `name`
  field, so `cmd_features.c` exposes `--features`. Shipped: `cmd_version.c` (`axiom0 0.1.0 (stage0)`),
  `cmd_inspect.c` (`--emit=<name>` dispatch through the emitter table; unknown/missing name -> usage
  error 2, lists emitters), `cmd_features.c` (empty capability list: prints nothing, exit 0). `main.c`
  switches stdout/stderr to binary mode (`ax_io_set_binary`, `io.c`, `_setmode` on Windows) and only
  dispatches; `help`/`--help`/`-h` print usage (exit 0), no/unknown command -> 2.
- **C tests**: `tests/unit/**/*.c` -> `axiom0-unit` with a generated `main` (the `AX_TEST(name)` markers are
  scanned at configure time; `--list`, run by name, `PASS/FAIL` lines, `UNIT n tests, f failed`, exit
  0/1/2); `tests/**/cdriver_*.c` -> its own executable `build/tests/ct_<path>`; `fixtures/` directories
  are never compiled; with no such files nothing is created and the build succeeds. Both are registered
  with `ctest`. `tests/unit/unit.h` provides `AX_TEST`, `AX_CHECK`, `AX_CHECK_EQ_INT`, `AX_CHECK_EQ_STR`
  (and `AX_UNIT_STANDALONE` for own-main tests).
- **CI**: `tools/ci.sh` and `tools/ci.ps1` (same behaviour): for each of `AX_CI_COMPILERS` (default
  `gcc clang`) configure+build into `build-ci/<cc>`, smoke `version`, `ctest`, then run
  `tools/axtest.py --compiler <exe>`, `archcheck.py`, `gatecheck.py`, `fuzz.py --smoke` each only if the
  file exists; any failing step fails the script with a non-zero code.
- Module directories under `src/` each have a one-line `README.md` (purpose + layer); `driver/README.md`
  also states the registry convention. Top-level `README.md`: layout, build, options, registries, exit
  codes, CI, binary-fixture policy. `.gitignore`: added `compile_commands.json`, `CMakeUserPresets.json`,
  `*.ilk` and a comment on the fixture exemption (`build/`, `build-*/`, `*.exe`, `*.obj`,
  `_workspaces/artifacts/` were already there).

Design decisions (no ADR needed, all local to T004): exit code 3 = ICE, 2 = usage, 1 = diagnostics, 0 = ok
(as in T016/axiom-testing); registry entry = struct with name, not a file-name mapping, so names like
`--features` are possible; emitter/command `argv[0]` is the command name and `inspect` passes the
remaining arguments (without `--emit=`) to the emitter; version line contains no build date (determinism).

## Files changed
- .gitignore
- README.md
- bootstrap/axiom0/CMakeLists.txt
- bootstrap/axiom0/cmake/AxiomRegistry.cmake
- bootstrap/axiom0/cmake/AxiomTests.cmake
- bootstrap/axiom0/cmake/registry.c.in
- bootstrap/axiom0/cmake/unit_main.c.in
- bootstrap/axiom0/src/abi/README.md
- bootstrap/axiom0/src/diag/README.md
- bootstrap/axiom0/src/driver/README.md
- bootstrap/axiom0/src/driver/cmd_features.c
- bootstrap/axiom0/src/driver/cmd_inspect.c
- bootstrap/axiom0/src/driver/cmd_version.c
- bootstrap/axiom0/src/driver/driver.h
- bootstrap/axiom0/src/driver/io.c
- bootstrap/axiom0/src/driver/main.c
- bootstrap/axiom0/src/driver/registry.c
- bootstrap/axiom0/src/hir/README.md
- bootstrap/axiom0/src/interp/README.md
- bootstrap/axiom0/src/kernel/README.md
- bootstrap/axiom0/src/lex/README.md
- bootstrap/axiom0/src/link/README.md
- bootstrap/axiom0/src/lir/README.md
- bootstrap/axiom0/src/mir/README.md
- bootstrap/axiom0/src/obj/README.md
- bootstrap/axiom0/src/objmodel/README.md
- bootstrap/axiom0/src/opt/README.md
- bootstrap/axiom0/src/own/README.md
- bootstrap/axiom0/src/resolve/README.md
- bootstrap/axiom0/src/source/README.md
- bootstrap/axiom0/src/syntax/README.md
- bootstrap/axiom0/src/target/x64/README.md
- bootstrap/axiom0/src/traits/README.md
- bootstrap/axiom0/src/types/README.md
- bootstrap/axiom0/src/verify/README.md
- tests/unit/unit.h
- tools/ci.ps1
- tools/ci.sh

## Tests
Toolchain (MSYS2 ucrt64): gcc 16.1.0 (Rev3, MSYS2), clang 22.1.4, cmake 4.3.2, ninja 1.13.2, Python 3.12.10.
All commands were run in the snapshot `build-snap-T004` (HEAD aca558c + the 38 files above).

1. `cmake -S build-snap-T004/bootstrap/axiom0 -B build-snap-T004/build-<cc> -G Ninja -DCMAKE_C_COMPILER=<cc>`
   then `cmake --build ...` for `gcc` and `clang`: both succeed, 9/10 ninja steps, zero warnings (build
   output contains no `warning`; flags include `-Wall -Wextra -Wpedantic -Werror`).
2. `axiom0.exe version | od -c` -> `a x i o m 0   0 . 1 . 0   ( s t a g e 0 ) \n`, exit 0, one `\n`, no
   `\r`. `od -tx1` of `help` stdout (336 bytes, 9 newlines) and of stderr usage shows zero `0d` bytes.
   `--features` prints 0 bytes, exit 0. No command -> usage on stderr, exit 2; `bogus` -> exit 2;
   `version x` -> exit 2; `inspect` / `inspect --emit=tokens x.ax` -> exit 2 ("no emitters are available").
3. `bash tools/ci.sh` in the snapshot: configure+build+smoke+ctest for gcc and clang, optional tools
   reported "not present, skipped", last line `ci: OK (gcc clang)`, exit 0. `powershell -File tools/ci.ps1`:
   same result, exit 0 (checked with and without `AX_CI_COMPILERS=gcc`). ctest prints "No tests were found"
   and exits 0 (no tests exist yet).
4. Registry/test globs demonstrated in a scratch copy (`<scratchpad>/demo`, not committed; copy of the
   snapshot's `bootstrap/` and `tests/unit/unit.h`). Baseline build, then added `src/driver/emit_dummy.c`,
   `src/driver/cmd_dummy.c`, `tests/unit/dummy/t.c` (two `AX_TEST`s) and `tests/x/cdriver_y.c` and ran only
   `cmake --build build` (the globs re-ran CMake by themselves): `axiom0 inspect --emit=dummy a b` printed
   `emit dummy: argc=3 first=a`; `axiom0 dummy` printed `cmd dummy` exit 7 and appears in `help`;
   `build/axiom0-unit` -> `PASS dummy_pass`, `PASS dummy_second`, `UNIT 2 tests, 0 failed`;
   `build/tests/ct_x_cdriver_y.exe` ran, exit 0; `ctest` 2/2 passed. `sha256sum -c` confirmed
   `CMakeLists.txt` and `main.c` unchanged. Appending a failing `AX_TEST` was picked up on the next build:
   `FAIL dummy_fail` with file:line and values, exit 1, `ctest` failed, `ci.sh` stopped with exit 8; an unknown
   test name gives exit 2. The same scratch tree also built with clang: zero warnings, all three executables.
   Stub `tools/axtest.py` (exit 0) and `tools/archcheck.py` (exit 5) in the scratch tree were invoked by
   `ci.sh` with `--compiler <axiom0>` and the failing one made `ci.sh` exit 5 (pre-wiring works).
5. No test runner, archcheck or Axiom tests exist yet (T005/T006), so there is no suite beyond the ctest
   targets, which are empty by design in this task. `taskctl changes T004` lists the 38 files above.

## Spec deviations
none

## Follow-ups
- T016 will extend `cmd_features.c` (derive capabilities from registered stages) and `cmd_version.c` if the
  version line needs more fields; both are plain files, no shared-file edit is needed.
- T005 may want `axiom0 --features` to print nothing for the empty list (done) and exec manifests can use
  `{build}/axiom0-unit` and `{build}/tests/ct_*` (output locations are fixed by `cmake/AxiomTests.cmake`).

STATUS: COMPLETE round=0
