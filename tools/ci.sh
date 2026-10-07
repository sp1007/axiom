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
SRC="$ROOT/bootstrap/axiom0"
COMPILERS="${AX_CI_COMPILERS:-gcc clang}"
BUILD_TYPE="${AX_CI_BUILD_TYPE:-Debug}"
BUILD_ROOT="${AX_CI_BUILD_ROOT:-$ROOT/build-ci}"

# MSYS2 ucrt64 toolchain may not be on PATH in a plain Git Bash.
if ! command -v cmake >/dev/null 2>&1; then
    for d in /ucrt64/bin /c/msys64/ucrt64/bin; do
        if [ -x "$d/cmake" ] || [ -x "$d/cmake.exe" ]; then
            PATH="$d:$PATH"
            break
        fi
    done
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
    command -v "$tool" >/dev/null 2>&1 || { echo "ci: missing tool: $tool" >&2; exit 127; }
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
    command -v "$cc" >/dev/null 2>&1 || { echo "ci: compiler not found: $cc" >&2; exit 127; }
    BUILD="$BUILD_ROOT/$cc"
    step "configure ($cc, $BUILD_TYPE)"
    cmake -S "$SRC" -B "$BUILD" -G Ninja "-DCMAKE_C_COMPILER=$cc" "-DCMAKE_BUILD_TYPE=$BUILD_TYPE"
    step "build ($cc)"
    cmake --build "$BUILD"

    EXE="$BUILD/axiom0"
    [ -f "$EXE.exe" ] && EXE="$EXE.exe"
    step "smoke: $EXE version"
    "$EXE" version

    step "ctest ($cc)"
    # `ctest` fails when no tests are defined only with --no-tests=error, which we do not pass.
    (cd "$BUILD" && ctest --output-on-failure)

    run_checker axtest.py --compiler "$EXE"
    run_checker archcheck.py
    run_checker gatecheck.py --compiler "$EXE"
    run_checker tests/gatecheck/run_selftests.py
    run_checker fuzz.py --smoke
done

printf '\nci: OK (%s)\n' "$COMPILERS"
