# T438 report

## Round 0
### Root cause (reproduced in a fresh `build-snap-T438`)
- `tools/build_axiomc.py ensure_stage0` configures the snapshot build with `-DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release`
  (Release adds `-O3 -DNDEBUG`) and runs a plain `cmake --build`, which also builds every `ct_*` target.
- Under `-DNDEBUG`, `assert()` expands to nothing. The C test drivers whose only checks are `assert()`s then (a) contain unused
  variables, and clang `-Wall -Wextra -Werror` stops the build, and (b) would check nothing even if they compiled.
- A Debug build (the default) is fine, which is why the main-tree build never showed it.
- Not specific to `cdriver_abi_qa2.c`: a Release+clang build fails on SIX files (11 errors, all `-Wunused-variable` /
  `-Wunused-but-set-variable`): `tests/mc/isel/cdriver_abi_qa2.c:19`, `cdriver_abi_qa.c:19`, `cdriver_abi.c:15,29,37`,
  `cdriver_abi_edge.c:16,26,35`, `tests/mc/frame/cdriver_probe.c:44`, `cdriver_probe_edge.c:45,71`. Ninja stops at the first
  failure, so T430-qa saw only one.

### Fix
In each of the six C sources `#undef NDEBUG` is placed before `#include <assert.h>` (qa2 also carries a two-line comment saying
why). The checks stay live in every build type; no flag, CMake file or `bootstrap/axiom0` change; `-Werror` untouched.
`_workspaces/baseline-failures.txt`: removed exactly the `# --- T438 ...` header, `encode/encode.test`, `link/link.test` and
one blank line (4 deletions, nothing else).

### Evidence (fresh `build-snap-T438`: directory deleted and re-created with `taskctl snapshot`, HEAD 888b283 + task files)
- `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=clang -DCMAKE_BUILD_TYPE=Release` and a plain
  `cmake --build build` -> exit 0, `[131/132] Linking C executable tests\ct_encode_cdriver_encode.exe`; `build/axiom0.exe` plus
  18 `build/tests/ct_*.exe` (tail of the log above).
- `axtest --no-cache -j 2 -v mc/frame/cdriver mir/build/ice_unhandled obj/cdriver_coff unit/kernel ui/drop encode/encode.test
  link/link.test`: TOTAL 26 PASS 26 FAIL 0 (encode/encode.test PASS, link/link.test PASS).
- `axtest --baseline _workspaces/baseline-failures.txt encode/encode.test link/link.test` -> BASELINE OK, 2/2 PASS.
- Direct runs, rc=0: `ct_mc_isel_cdriver_abi`, `_abi_edge`, `_abi_qa`, `_abi_qa2`, `ct_mc_frame_cdriver_probe`, `_probe_edge`,
  `_verify`.
- Mutation (earlier in the same task, snapshot only, restored and cmp-verified): `sig.arg_count == 5` -> `== 6` in qa2 under
  Release gives `Assertion failed: sig.arg_count == 6 ... line 23`, rc=127, so the asserts are live with the fix.
- No Axiom sources changed, so no selfhost bundle regeneration; whole suite not run (per instructions).

### Notes
- `selfhost/drop/drop_oracle.test` fails once its `ct_selfhost_drop_cdriver_drop_oracle` exists: ICE `ax_interner_get: invalid
  StrId 0` on `tests/selfhost/drop/fixtures/d09_closures.ax`; it also happens in the main tree's Debug build, so it is
  pre-existing and not caused by this change. Routed to the architect by the coordinator.
- `link/lib/coff_lib.test`, `link/dll/*.test` need the stage-2 `axiomc` as `{compiler}`; unrelated to `ct_*`.

## Files changed
- tests/mc/isel/cdriver_abi_qa2.c
- tests/mc/isel/cdriver_abi.c
- tests/mc/isel/cdriver_abi_qa.c
- tests/mc/isel/cdriver_abi_edge.c
- tests/mc/frame/cdriver_probe.c
- tests/mc/frame/cdriver_probe_edge.c
- _workspaces/baseline-failures.txt
- _workspaces/reports/T438-report.md

STATUS: COMPLETE round=0
