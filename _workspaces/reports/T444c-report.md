# T444c report — build_axiomc/bootstrap reuse by content hash of the inputs, not mtime

## Problem (T444 report F3)
`bootstrap.py --reuse-existing` reused `axiomc1/2/3` when `mtime(binary) >= max mtime(compiler/**/*.ax, std/**/*.ax)`.
`taskctl snapshot` copies sources with their main-tree mtimes, so an edit inside a snapshot (older mtime than the
binary) left the stale `axiomc2.exe` in use (wall 0.00 s, old sha256). `ensure_stage0` reused any `axiom0.exe`, even
after `bootstrap/axiom0` changed (AX0-FIX tasks such as T164).

## Design (kept small and deterministic so that T487 can key a content-addressed seed cache on it)
Every produced stage binary gets a manifest `<bin>.inputs.json` (JSON, sorted keys, compact, LF). A binary is reused
only when the manifest equals the inputs of the build about to run; mtimes are never read.

| field | meaning |
|---|---|
| `schema` | 1 |
| `kind` | `axiom0`, `stage1`, `stage2`, `stage3` |
| `producer_sha256` | sha256 of the compiler binary that produced `<bin>` (axiom0 for stage1, axiomc1 for stage2, axiomc2 for stage3; empty for axiom0) |
| `bundle_sha256` | sha256 of the bundle text actually compiled (`axiomc_bundle_text()` bytes) |
| `flags` | stages: `{"opt": default/O0/O1, "stack_reserve": N}`; axiom0: `{"cc", "build_type"}` |
| `sources_sha256` | sha256 of the sorted lines `<relative path> <sha256>` of every hashed source |
| `inputs_hash` | sha256 of the canonical JSON of the five fields above: the reuse key (first 16 hex printed) |
| `files` | `{relative path: sha256}` behind `sources_sha256`; only used to name the changed files in a `REBUILT` reason |
| `output_sha256`, `output_size` | of `<bin>` itself: a binary replaced or truncated behind its manifest is never reused |

Hashed sources: stages `compiler/**/*.ax`, `std/**/*.ax`, `std/**/*.toml` (std keyed by content under the fixed prefix
`std/`; the absolute std-root path is deliberately not an input, the output does not depend on it, INV-DET-004, and
this makes manifests identical across build directories, which is what a seed cache needs). axiom0: every file under
`bootstrap/axiom0` (C sources, headers, `CMakeLists.txt`, `cmake/*`) except CMake build trees (a directory holding
`CMakeCache.txt` or `build.ninja`, `CMakeFiles`, `.cache`, `.git`, `__pycache__`) and binaries/objects
(`*.exe *.obj *.o *.a *.lib *.pdb *.ilk *.pyc *.log`). Source directories that merely start with `build`
(`src/driver/build_native`, `src/mir/build`) are inputs.

Chain by content: stage 2's producer is the sha256 of `axiomc1`, stage 3's that of `axiomc2`. If axiom0 changes but
the rebuilt `axiomc1` is byte-identical, stages 2 and 3 are `REUSED`.

Output lines: `REUSED <bin> (inputs <hash16>)` or `REBUILT <bin> (<reason>)` (`no previous binary`, `no input
manifest next to the previous binary`, `input manifest unreadable`, `binary does not match its manifest (replaced or
damaged)`, `producing compiler changed`, `bundle text changed`, `flags changed (old -> new)`, `sources changed:
<first 3 files> (+n more)`, `reuse not requested` for `--force` / no `--reuse-existing`). `bootstrap.py` also prints
`INPUTS: <n> source files hashed in <s>s (sources <hash16>)`.

`ensure_stage0` (`build_axiomc.py`): same rule over `bootstrap/axiom0`, cc and build type, manifest
`<out>/axiom0.exe.inputs.json`. On a mismatch it re-runs configure and `cmake --build --parallel 2`, with
`--clean-first` whenever an old build tree exists: Ninja trusts mtimes, so an edited C file with an old mtime would
otherwise not be recompiled. An existing `axiom0.exe` without a manifest (built before this task) is rebuilt once.
`--stage0 <path>` is still used as is (its sha256 enters the stage-1 manifest as the producer).

`--force` is unchanged (every stage rebuilt, manifests rewritten so that a later non-forced run can reuse them).

## Files changed
- tools/bootstrap.py
- tools/build_axiomc.py
- tools/tests/build_axiomc/run_selftests.py
- tools/tests/build_axiomc/test_build_axiomc.py

## Evidence

### 1. Self-tests and full-tree hashing cost (< 2 s)
```
$ python build-snap-T444c/tools/tests/build_axiomc/run_selftests.py -v
T444c: hashed 257 compiler/std source files in 0.09s
SELFTEST 22 tests, 0 failures, 0 errors
```

### 2. Real `build_axiomc.py --out build-snap-T444c/build` (rebuild -> reuse -> backdated edit rebuild -> `--force` byte-identical)
- First run (and after `bootstrap/axiom0/src/driver/build_native/build.c` updated at `HEAD dbc78f5`):
```
REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (sources changed: bootstrap/axiom0/src/driver/build_native/build.c)
INPUTS: 257 source files hashed in 0.10s (sources b6daf4ddfb041241)
REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (producing compiler changed)
STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=62.44s, peak_ws=2174.9MB, peak_commit=2406.4MB)
REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe (producing compiler changed)
STAGE2 (O1) OK: D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe [dir=D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1] (8142848 bytes, sha256=fa1d7d6dc3d4e41c, wall=1954.19s, peak_ws=5374.6MB, peak_commit=5835.9MB)
BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc2.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=8142848 sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1
```
- Second run without changes (`REUSED` across stage 0, stage 1, stage 2):
```
REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
INPUTS: 257 source files hashed in 0.08s (sources b6daf4ddfb041241)
REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (inputs b372e08eeb0758fd)
STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=0.00s, peak_ws=0.0MB, peak_commit=0.0MB)
REUSED D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe (inputs 2021320f4f621c53)
STAGE2 (O1) OK: D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1\axiomc2.exe [dir=D:\projects\compiler\new lang\build-snap-T444c\build\dir_stage2_O1] (8142848 bytes, sha256=fa1d7d6dc3d4e41c, wall=0.00s, peak_ws=0.0MB, peak_commit=0.0MB)
BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc2.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=8142848 sha256=fa1d7d6dc3d4e41c34abbc51f5cffc56a63faa326a5f71a5fc398819e60e16f1
```
- Third run after modifying `std/core/cmp.ax` and setting its mtime back to `1000000000` (older than the binary):
```
REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
INPUTS: 257 source files hashed in 0.13s (sources 4f20f87249aa8ede)
REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (sources changed: std/core/cmp.ax)
STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=60.53s, peak_ws=2171.3MB, peak_commit=2403.5MB)
BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=26334720 sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083
```
- Fourth run with `--force` on restored sources (rebuilds with `(reuse not requested)` and produces byte-identical binary `sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083`, after which stage-2 reuse succeeds with `inputs 2021320f4f621c53`):
```
REUSED D:\projects\compiler\new lang\build-snap-T444c\build\axiom0.exe (inputs 2754e62dc264ce73)
INPUTS: 257 source files hashed in 0.09s (sources b6daf4ddfb041241)
REBUILT D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (reuse not requested)
STAGE1 OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (26334720 bytes, sha256=6a9c2eb776b36fd2, wall=86.86s, peak_ws=2171.1MB, peak_commit=2403.9MB)
BUILD-AXIOMC OK: D:\projects\compiler\new lang\build-snap-T444c\build\axiomc1.exe (also D:\projects\compiler\new lang\build-snap-T444c\build\axiomc.exe) size=26334720 sha256=6a9c2eb776b36fd25e86fff018353b966ed849d0bde742f7e0d8c85643e50083
```

### 3. Per-task gate (`tools/taskgate.py --task T444c`)
```
### taskgate T444c (`tools/taskgate.py`)

- root `D:/projects/compiler/new lang/build-snap-T444c`, HEAD `dbc78f586aef`, compiler `D:/projects/compiler/new lang/build-snap-T444c/build/axiomc2.exe`, `-j 2`
- change set: 5 file(s) (working tree of build-snap-T444c vs HEAD)
  - `_workspaces/reports/T444c-report.md`
  - `tools/bootstrap.py`
  - `tools/build_axiomc.py`
  - `tools/tests/build_axiomc/run_selftests.py`
  - `tools/tests/build_axiomc/test_build_axiomc.py`
- wall time: 299.1 s (axtest 9.2 s)

Tool self-tests: `tools/tests/archcheck` PASS (SELFTEST 55 tests, 0 failures, 0 errors, 5.2 s); `tools/tests/build_axiomc` PASS (SELFTEST 22 tests, 0 failures, 0 errors, 1.9 s); `tools/tests/gatecheck` PASS (SELFTEST 39 tests, 0 failures, 0 errors, 42.9 s); `tools/tests/taskgate` PASS (SELFTEST 44 tests, 0 failures, 0 errors, 196.0 s)
archcheck: clean (exit 0) archcheck: 229 files scanned, 0 violations
axtest: `TOTAL 49 PASS 49 FAIL 0 SKIP 0 XFAIL 0` (exit 0)

TASKGATE T444c exit=0
```

STATUS: COMPLETE round=0
