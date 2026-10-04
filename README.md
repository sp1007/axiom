# Axiom

A new systems language and its compiler. `axiom0` is the Stage-0 compiler written in C11 (Windows x64
first); it exists to reach self-hosting quickly, after which the compiler is written in Axiom itself
(`axiomc`). Canonical specs are in `spec/` (decisions in `spec/decisions/`, plan in `spec/ROADMAP.md`).
Syntax: binding and assignment use `=` only, paths use `.` only.

## Layout

| Directory | Contents |
|-----------|----------|
| `bootstrap/axiom0/` | the Stage-0 compiler: `CMakeLists.txt`, `cmake/`, `src/<module>/` (one README per module states its purpose and layer) |
| `tests/` | all tests: `unit/` (C unit tests), `lex/ parse/ ui/ run/ mir/ ...` (Axiom-source and golden tests) |
| `tools/` | test runner, layer checker, CI scripts (`ci.sh`, `ci.ps1`), helpers; Python 3 standard library only |
| `std/` | Axiom-source libraries (written in Axiom) |
| `spec/` | canonical specifications, ADRs, roadmap, requirements |
| `docs/` | the owner's original design corpus (read-only for agents) |

## Build

Toolchain: gcc or clang (MSYS2 ucrt64 on Windows), CMake 3.20+, Ninja.

```
cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc
cmake --build build                  # -> build/axiom0.exe (Windows) or build/axiom0
build/axiom0.exe version
```

Options: `-DCMAKE_BUILD_TYPE=Debug|Release` (default Debug), `-DAX_WERROR=ON|OFF` (warnings are errors by
default; `-Wall -Wextra -Wpedantic`, C11 without extensions), `-DAX_SANITIZE=ON` (ASan + UBSan, where the
toolchain supports them). Build directories `build/`, `build-*/` are git-ignored.

Nobody lists source files in CMake: `src/**/*.c` and the test globs below are discovered at configure
time, so a new task adds files and never edits `CMakeLists.txt`.

| Add a file | Effect |
|------------|--------|
| `src/driver/cmd_<name>.c` defining `const AxCommand axcmd_<name>` | new `axiom0` command |
| `src/driver/emit_<name>.c` defining `const AxEmitter axemit_<name>` | new `axiom0 inspect --emit=<name>` emitter |
| any `.c` below `tests/unit/` containing `AX_TEST(name) { ... }` (see `tests/unit/unit.h`) | test inside `build/axiom0-unit` |
| `tests/<dir>/cdriver_<name>.c` (own `main`) | test executable `build/tests/ct_<dir>_cdriver_<name>` |

`ctest --test-dir build` runs all C tests. Files under a `fixtures` directory are data, never compiled.

## Exit codes of `axiom0`

`0` success, `1` the input produced error diagnostics, `2` usage error (unknown command/option, missing
argument), `3` internal compiler error. Output is byte-exact: stdout and stderr are binary on Windows, so
every line ends in `\n`, never `\r\n`.

## CI

`bash tools/ci.sh` (or `powershell -File tools/ci.ps1`) configures and builds with gcc and clang, runs the C
tests, and then each of `tools/axtest.py`, `tools/archcheck.py`, `tools/gatecheck.py`, `tools/fuzz.py --smoke`
that exists. `AX_CI_COMPILERS="gcc"` limits the compilers.

## Binary fixtures

Object files, executables and other binary test inputs are git-ignored (`*.exe`, `*.obj`, ...) except below
`tests/**/fixtures/`, which is exempt in `.gitignore` and marked `binary` in `.gitattributes`. Anywhere else
a binary file is a build product and must not be committed.
