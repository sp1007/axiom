#!/usr/bin/env bash
# CI for axiom0 (T004). Run from anywhere: bash tools/ci.sh
#
# For each compiler in $AX_CI_COMPILERS (default "gcc clang"): configure + build axiom0 with Ninja
# (warnings are errors), run the C tests (ctest), then run every optional checker that exists in
# this checkout against that build. The optional checkers are pre-wired here so later tasks add
# their tool and never edit this script (gate tasks may):
#   tools/axtest.py --compiler <axiom0>    test runner
#   tools/archcheck.py                     layer checker
#   tools/gatecheck.py                     phase-gate checks
#   tools/fuzz.py --smoke                  fuzz smoke campaign
#
# Environment: AX_CI_COMPILERS (compilers, space separated), AX_CI_BUILD_TYPE (default Debug),
#              AX_CI_BUILD_ROOT (default <repo>/build-ci; one subdirectory per compiler).
# Exit code: 0 everything passed, otherwise the first failing step's code (non-zero).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMAKE_ROOT="$ROOT"
if command -v cygpath >/dev/null 2>&1; then
    CMAKE_ROOT="$(cygpath -w "$ROOT")"
elif command -v wslpath >/dev/null 2>&1; then
    CMAKE_ROOT="$(wslpath -w "$ROOT")"
fi
CMAKE_ROOT="${CMAKE_ROOT//\\//}"
SRC="$ROOT/bootstrap/axiom0"
COMPILERS="${AX_CI_COMPILERS:-gcc}"
BUILD_TYPE="${AX_CI_BUILD_TYPE:-Debug}"
BUILD_ROOT="${AX_CI_BUILD_ROOT:-$ROOT/build-ci}"

for d in /ucrt64/bin /c/msys64/ucrt64/bin /mnt/c/msys64/ucrt64/bin; do
    if [ -d "$d" ]; then
        PATH="$d:$PATH"
    fi
done

if ! command -v cmake >/dev/null 2>&1 && command -v cmake.exe >/dev/null 2>&1; then
    cmake() { cmake.exe "$@"; }
    ninja() { ninja.exe "$@"; }
    ctest() { ctest.exe "$@"; }
fi

PYTHON=""
for p in python3 python; do
    if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)' >/dev/null 2>&1; then
        PYTHON="$p"
        break
    fi
done

step() { printf '\n== %s\n' "$*"; }

for tool in cmake ninja; do
    command -v "$tool" >/dev/null 2>&1 || command -v "$tool.exe" >/dev/null 2>&1 || { echo "ci: missing tool: $tool" >&2; exit 127; }
done

run_checker() { # <script> [args...]: run tools/<script> only when the file exists
    local script="$1"
    shift
    if [ ! -f "$ROOT/tools/$script" ]; then
        echo "ci: tools/$script not present, skipped"
        return 0
    fi
    if [ -z "$PYTHON" ]; then
        echo "ci: tools/$script exists but no python 3 is available" >&2
        return 127
    fi
    step "$script $*"
    (cd "$ROOT" && "$PYTHON" "tools/$script" "$@")
}

for cc in $COMPILERS; do
    command -v "$cc" >/dev/null 2>&1 || command -v "$cc.exe" >/dev/null 2>&1 || { echo "ci: compiler not found: $cc" >&2; exit 127; }
    BUILD="$BUILD_ROOT/$cc"
    step "configure ($cc, $BUILD_TYPE)"
    cmake -S "$CMAKE_ROOT/bootstrap/axiom0" -B "$BUILD" -G Ninja "-DCMAKE_C_COMPILER=$cc" "-DCMAKE_BUILD_TYPE=$BUILD_TYPE"
    step "build ($cc)"
    cmake --build "$BUILD"

    EXE="$BUILD/axiom0"
    [ -f "$EXE.exe" ] && EXE="$EXE.exe"
    step "smoke: $EXE version"
    "$EXE" version

    step "determinism ($cc)"
    (
        cd "$BUILD"
        echo "fn main() -> i32 { return 0; }" > det.ax
        "$EXE" build -o det.exe det.ax
        cp det.exe det.exe.1
        "$EXE" build -o det.exe det.ax
        if ! cmp -s det.exe det.exe.1; then
            echo "ci: determinism failure: build output differs" >&2
            exit 1
        fi
        rm -f det.exe det.exe.1 det.ax
    )

    step "ctest ($cc)"
    # `ctest` fails when no tests are defined only with --no-tests=error, which we do not pass.
    (cd "$BUILD" && ctest --output-on-failure)

    run_checker axtest.py --compiler "$EXE"
    run_checker archcheck.py
    if [ -z "${AX_CI_IS_RUNNING:-}" ]; then
        export AX_CI_IS_RUNNING=1
        run_checker gatecheck.py --compiler "$EXE"
    fi
    run_checker tests/gatecheck/run_selftests.py
    run_checker fuzz.py --smoke
done

printf '\nci: OK (%s)\n' "$COMPILERS"
