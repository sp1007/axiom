# Periodic Full Run 1 (`fullrun-1`, Tier 1 `non-selfhost`)

## Tóm tắt

Đợt quét định kỳ Tier-1 `non-selfhost` (`fullrun-1`) chạy trên snapshot tách biệt `build-snap-fullrun-1` tại commit `0b9ff70a` (33 tác vụ được chấp nhận kể từ `bda2296a`):

- **Xác minh trust-root (`axiom0 -> c1 -> c2 == c3 == B` ở cả `-O1` và `-O0`)**: **ĐẠT** — toàn bộ điểm bất động Stage-2/Stage-3 và đối chiếu nhị phân từ seed (`c2 == B`) trùng khớp từng byte ở cả `-O1` và `-O0` (1066.7 s).
- **Kiểm tra cấu trúc & harness**: `archcheck.py` (229 tệp, 0 vi phạm) và `harness_check.py` (`HARNESS OK`) đều **ĐẠT**; `CACHE-MISMATCH = 0` (`verify-sample` 20/121 hits, seed `512305688`).
- **Kết quả quét Tier-1 (`2,043` test IDs, `4,326` lượt chạy)**: `PASS 4241 / FAIL 5 / SKIP 80 / XFAIL 0` (0 timeout, 0 crash, 68.1 phút).
- **Phát hiện 4 test ID hồi quy mới ngoài `_workspaces/baseline-failures.txt`** (tất cả đều tái lập 100%, không phải timeout; đã bisect chính xác tới từng commit thủ phạm):
  1. **3 test formatter** (`run/fmt_engine/fmt_engine.test`, `run/fmt_cli/fmt_cli.test`, `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test`) → thủ phạm: **`bda3bb63` (`T434`, chủ sở hữu `axiom-frontend`)**. `parse_synthetic_item()` đổi span của `ITEM_IMPL` sinh từ `@derive(...)` sang `source_span.file.v` với span độ dài 0 (`start == end`), khiến `cst_is_synthetic_item()` trong `compiler/fmt/cst/mod.ax` (vẫn chỉ lọc `sp.file.v == 0` hoặc `sp.start == 0`) bỏ sót và in nhầm các `impl` tổng hợp.
  2. **1 test async native** (`std/async/executor/async_channel_pipeline.ax` ở `[native]` và `[native-O1]`, `[interp]` vẫn PASS) → thủ phạm: **`f0f98f33` (`T489`, chủ sở hữu `axiom-semantics`)**. `mb_count_generic_params_in_hir()` coi phương thức inherent của `impl<T> AsyncSender<T>` (`close`) là mẫu generic không sinh ký hiệu gốc `'close'`, nhưng `AsyncSender.drop` trong `impl<T> Drop for AsyncSender<T>` vẫn tham chiếu ký hiệu chưa chuyên biệt `'close'`, gây lỗi liên kết `AX_LINK_UNDEFINED_SYMBOL`.

Khuyến nghị điều phối viên tạo 2 tác vụ sửa lỗi ưu tiên 0 (`priority: 0`) cho `axiom-frontend` (lỗi formatter sau `T434`) và `axiom-semantics` (lỗi link `Drop` gọi inherent method generic sau `T489`), đồng thời cân nhắc bổ sung các oracle test `fmt_*` vào `tools/affected_map.txt` cho `compiler/syntax/parse.ax`.

---

## 1. Run Metadata

- **Run ID**: `fullrun-1`
- **Mode / Tier**: Tier 1 — `non-selfhost` (all non-selfhost tests + `selfhost/bundles_current.test`)
- **Snapshot commit**: `0b9ff70a4048f453bf1b6b956be5e97940f25886` (`T494`)
- **Baseline reference commit**: `bda2296a` (33 accepted tasks in `bda2296a..0b9ff70a`)
- **Snapshot worktree**: `build-snap-fullrun-1` (detached HEAD `0b9ff70a`, removed and pruned on completion)
- **Artifacts**:
  - `_workspaces/artifacts/fullrun-1-ids.txt` (2,043 test IDs)
  - `_workspaces/artifacts/fullrun-1-axtest.json` (4,326 test results)
- **Baseline file**: `_workspaces/baseline-failures.txt` (0 active entries)

---

## 2. Trust-Root Bootstrap Verification (`T487` Periodic Check)

Command run inside `build-snap-fullrun-1/`:
```powershell
python tools/build_axiomc.py --out build --trust-root --opt both
```

- **Exit code**: `0`
- **Total wall time**: `1066.7 s` (~17.8 min)
- **Host C compiler for Stage 0 (`axiom0.exe`)**: Clang 22.1.4 + Ninja (0 errors)
- **Source inputs**: 257 source files hashed in 1.79 s (`sources 554af099e40f545c`)
- **Pre-existing trust-root seed resolved from `compiler-cache/`**:
  `_workspaces/artifacts/compiler-cache/axiomc2_O1_5789d80bb26aafa6.exe` (exact inputs `5789d80bb26aafa6`, sha256 prefix `ec3b6e67f2b849bf`)

| Stage / Artifact | Opt | Size (bytes) | Wall (s) | Peak WS (MB) | Peak Commit (MB) | SHA-256 |
|---|---|---:|---:|---:|---:|---|
| `axiom0.exe` (Stage 0) | Release | — | — | — | — | `87d9a8455276e4413f40c46c2f88a62d3ca7f5e88fb92a7dad9c75afe9a66edf` |
| `axiomc1.exe` (Stage 1: `axiom0 -> c1`) | — | 28,164,608 | 134.48 | 2336.3 | 2576.0 | `d4cd880ce50f650a5b72b1f8088f170732bb273f78df3e320e4dbab181ebbe99` |
| `dir_stage2_O1/axiomc2.exe` (`c1 -> c2`) | `-O1` | 8,500,224 | 176.84 | 3085.3 | 3128.5 | `ec3b6e67f2b849bfec12e3c8137d383d698baccfa5a35c034f2d5a854c6b1a42` |
| `dir_stage3_O1/axiomc3.exe` (`c2 -> c3`) | `-O1` | 8,500,224 | 54.46 | 3063.2 | 3115.6 | `ec3b6e67f2b849bfec12e3c8137d383d698baccfa5a35c034f2d5a854c6b1a42` |
| `dir_seed_B_O1/axiomc_B.exe` (`seed -> A -> B`) | `-O1` | 8,500,224 | — | — | — | `ec3b6e67f2b849bfec12e3c8137d383d698baccfa5a35c034f2d5a854c6b1a42` |
| `dir_stage2_O0/axiomc2.exe` (`c1 -> c2`) | `-O0` | 17,252,352 | 196.98 | 3275.5 | 3367.6 | `33f3599b82732ebc0ffc94749da436837175d30c06869ce22cd39f87c0cb9e68` |
| `dir_stage3_O0/axiomc3.exe` (`c2 -> c3`) | `-O0` | 17,252,352 | 118.83 | 3131.2 | 3355.0 | `33f3599b82732ebc0ffc94749da436837175d30c06869ce22cd39f87c0cb9e68` |
| `dir_seed_B_O0/axiomc_B.exe` (`seed -> A -> B`) | `-O0` | 17,252,352 | — | — | — | `33f3599b82732ebc0ffc94749da436837175d30c06869ce22cd39f87c0cb9e68` |

Verified invariants:
- `FIXED-POINT (O1) OK`: `sha256(c2_O1) == sha256(c3_O1) == ec3b6e67f2b849bfec12e3c8137d383d698baccfa5a35c034f2d5a854c6b1a42` (distinct directories `dir_stage2_O1` vs `dir_stage3_O1`)
- `TRUST-ROOT (O1) OK`: `sha256(c2_O1) == sha256(B_O1) == ec3b6e67f2b849bfec12e3c8137d383d698baccfa5a35c034f2d5a854c6b1a42`
- `FIXED-POINT (O0) OK`: `sha256(c2_O0) == sha256(c3_O0) == 33f3599b82732ebc0ffc94749da436837175d30c06869ce22cd39f87c0cb9e68` (distinct directories `dir_stage2_O0` vs `dir_stage3_O0`)
- `TRUST-ROOT (O0) OK`: `sha256(c2_O0) == sha256(B_O0) == 33f3599b82732ebc0ffc94749da436837175d30c06869ce22cd39f87c0cb9e68`

---

## 3. Tier-1 `non-selfhost` Sweep & Static Checks

### 3.1 Static / Harness Checks
- `python tools/archcheck.py`: `archcheck: 229 files scanned, 0 violations` (`rc=0`)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK` (`rc=0`; note: optional `WARN .claude/settings.json: optional PreToolUse guard hook (guard.py) not enabled`)

### 3.2 `axtest.py` Tier-1 Run
Commands run inside `build-snap-fullrun-1/`:
```powershell
python .claude/skills/axiom-tasks/scripts/fullrun.py non-selfhost-ids "_workspaces/artifacts/fullrun-1-ids.txt" --root .
python tools/axtest.py --id-file "_workspaces/artifacts/fullrun-1-ids.txt" --compiler build/axiomc2.exe --build-dir build --gate -j 2 --exclude-requires axiom0-internal --baseline _workspaces/baseline-failures.txt --json > "_workspaces/artifacts/fullrun-1-axtest.json"
```

- **Exit code**: `1`
- **Wall time**: `4086.8 s` (~68.1 min)
- **Totals**: `TOTAL 4326 PASS 4241 FAIL 5 SKIP 80 XFAIL 0`
  - `xpass = 0`, `crash = 0`, `timeout = 0`, `weak_native = 143` (existing tests)
- **Cache statistics**:
  - `CACHED 208 HITS 121 MISS 1408 UNCACHEABLE 514 STORED 1349 dep_source=exact`
  - `VERIFY-SAMPLE seed=512305688 n=20 of 121 hits`
  - `CACHE-MISMATCH`: **0** (`mismatch: []`)
  - `store_skipped`: `{'nondeterministic (depends on std/sync)': 41, 'inputs changed during the run': 18}`
- **Timeouts**: **0** (no load-related timeouts requiring `--timeout-scale 6` retry).
- **Baseline comparison** (`_workspaces/baseline-failures.txt` has 0 active entries):
  - **4 new failing test IDs** (5 failing results):
    1. `run/fmt_engine/fmt_engine.test`
    2. `run/fmt_cli/fmt_cli.test`
    3. `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test`
    4. `std/async/executor/async_channel_pipeline.ax` (`[native]` and `[native-O1]`)

---

## 4. Regressions Outside Baseline & Culprit Bisect

All 4 failing IDs were reproduced independently with `--no-cache -v` and bisected to exact single-commit culprits in `bda2296a..0b9ff70a`.

### Regression Cluster A — Formatter Synthetic `@derive` Impl Leakage (3 test IDs)

- **Failing IDs**:
  1. `run/fmt_engine/fmt_engine.test` (exit 1; `fmt_engine_probe --interp` prints `probe[ex_fmt_01] exact_match=false idempotent=false comments_conserved=true` while `probe[ex_fmt_02_and_neg]` — which has no `@derive` — passes)
  2. `run/fmt_cli/fmt_cli.test` (exit 1; `fmt_cli_probe --interp` prints `probe[ast_verify] ok_exit=99 comments_conserved=true ast_equiv=false idempotent=false` instead of `ok_exit=0 ... ast_equiv=true idempotent=true`)
  3. `conformance/p19/e19_2_formatter/e19_2_formatter_oracle.test` (exit 1; `e19_2_formatter_probe --interp` prints `probe[corpus_idempotence_and_ast_equiv] corpus_files_verified=2 all_idempotent=false`)
- **Culprit commit**: **`bda3bb6395363af3abd40850835b13e5b4ff87a2`** — `T434: Baseline fix — derive-generated items of implicitly loaded std leak into root-file AST/resolve/HIR dumps`
- **Culprit owner**: **`axiom-frontend`** (both `T434` / `compiler/syntax/parse.ax` and `T805` / `compiler/fmt/cst/mod.ax` are owned by `axiom-frontend`)
- **Root cause**:
  - Before `T434`, `parse_synthetic_item()` in `compiler/syntax/parse.ax` lexed generated `@derive(...)` `impl` items with `FileId { v: 0u32 }` and offsets starting at `0`.
  - `T434` changed `parse_synthetic_item()` to attribute synthetic `@derive(...)` tokens to `source_span.file.v` with a zero-length span (`span.start = source_span.start`, `span.end = source_span.start`).
  - However, `cst_is_synthetic_item()` in `compiler/fmt/cst/mod.ax:535-548` still filters synthetic `@derive` `ITEM_IMPL` nodes solely via:
    ```ax
    if file_id.v != 0u32 && sp.file.v == 0u32 { return true; }
    if !is_first && k == ITEM_IMPL && sp.start == 0u32 { return true; }
    ```
  - Because `sp.file.v == file_id.v` (non-zero) and `sp.start == source_span.start` (non-zero) after `T434`, synthetic `@derive(...)` `ITEM_IMPL` nodes are no longer detected as synthetic and are emitted into the formatted output, breaking exact match, idempotence, and AST verification on every formatted input with `@derive(...)`.
- **Bisect proof** (run inside `build-snap-fullrun-1/` with `build/axiomc2.exe`):
  - At `0b9ff70a` (with `compiler/syntax/parse.ax` from `bda3bb63`):
    - `fmt_engine_oracle.py`: exit `1` (`probe[ex_fmt_01] exact_match=false idempotent=false`)
    - `fmt_cli_oracle.py`: exit `1` (`probe[ast_verify] ok_exit=99 ... ast_equiv=false idempotent=false`)
    - `e19_2_formatter_oracle.py`: exit `1` (`probe[corpus_idempotence_and_ast_equiv] corpus_files_verified=2 all_idempotent=false`)
  - With `git checkout bda3bb63~1 -- compiler/syntax/parse.ax`:
    - `fmt_engine_oracle.py`: exit `0` (`FMT-ENGINE-OK`)
    - `fmt_cli_oracle.py`: exit `0` (`FMT-CLI-OK`)
    - `e19_2_formatter_oracle.py`: exit `0` (`E19-2-FORMATTER-CONFORMANCE-OK`)
- **Gap note (why `T434`'s per-task gate missed it)**: The three formatter oracle tests dynamically bundle `compiler/syntax/parse.ax` inside Python scripts rather than importing it from `.ax` test files, so `--affected` for `compiler/syntax/parse.ax` did not select them. Consider adding `run/fmt_engine`, `run/fmt_cli`, and `conformance/p19/e19_2_formatter` to `tools/affected_map.txt` for `compiler/syntax`.

---

### Regression Cluster B — Native Link Failure Calling Generic Inherent Method from `impl<T> Drop` (1 test ID, 2 modes)

- **Failing ID**: `std/async/executor/async_channel_pipeline.ax`
  - `[interp]`: `PASS`
  - `[native]`: `FAIL`
  - `[native-O1]`: `FAIL`
- **Exact failure output** (identical for both `-O0` and `-O1`):
  ```text
  error[AX_LINK_UNDEFINED_SYMBOL]: undefined symbol 'close' (mangled: 'close') referenced by 'async_channel_pipeline.obj' in section '.text' (in function 'AsyncSender.drop')
   --> tests/std/async/executor/async_channel_pipeline.ax:4822:5
       | 
  4822 |     pub fn close(self: mut_view<AsyncSender<T>>) {
       |     ^^^
  4822 |     pub fn close(self: mut_view<AsyncSender<T>>) {
       |     --- referenced here
       | 

  1 error, 0 warnings
  ```
- **Culprit commit**: **`f0f98f33fcb76bf4d2685eba8056672cb6ab9a10`** — `T489: Fix silent miscompile — a method of a generic inherent impl reading a field of a struct that has a T-typed field returns 0`
- **Culprit owner**: **`axiom-semantics`** (`compiler/mir/builder.ax`)
- **Root cause**:
  - `T489` updated `mb_count_generic_params_in_hir()` (and `mb_item_cache()`) in `compiler/mir/builder.ax` so inherent methods inside `impl<T> Struct<T>` (such as `AsyncSender<T>::close` at `async_channel_pipeline.ax:4822`) now report `> 0` generic parameters and are treated as generic templates (only emitted when monomorphized for concrete type arguments, not as an unmangled `'close'` symbol).
  - However, `impl<T> Drop for AsyncSender<T>` (`tests/std/async/executor/async_channel_pipeline.ax:4868-4870`) defines `fn drop(self: mut_view<AsyncSender<T>>) { mut_view(*self).close(); }`, and the emitted native function `AsyncSender.drop` still references the unspecialized symbol `'close'` (mangled `'close'`), which is no longer defined in the object file.
- **Bisect proof** (exact parent vs commit using cached Stage-2 compilers in `_workspaces/artifacts/compiler-cache/`):
  - At `f0f98f33~1` (`93df5fbc` / `689f7dea` `T493`, compiler `axiomc2_O1_74139d179be888d3.exe`):
    `axtest.py --no-cache -v std/async/executor/async_channel_pipeline.ax` → **`TOTAL 3 PASS 3 FAIL 0`** (`interp` PASS, `native` PASS, `native-O1` PASS; `rc=0`)
  - At `f0f98f33` (`T489`, compiler `axiomc2_O1_8d0b29227c12f9d1.exe`):
    `axtest.py --no-cache -v std/async/executor/async_channel_pipeline.ax` → **`TOTAL 3 PASS 1 FAIL 2`** (`interp` PASS, `native` FAIL, `native-O1` FAIL with exact `AX_LINK_UNDEFINED_SYMBOL` `'close'` in `'AsyncSender.drop'`; `rc=1`)
  - At `0b9ff70a` (`T494` HEAD, built in `build-snap-fullrun-1/build/axiomc2.exe`): identical failure (`TOTAL 3 PASS 1 FAIL 2`).

---

## 5. Summary Verdict

- **Trust-root (`axiom0 -> c1 -> c2 == c3 == B`, O1 & O0)**: PASS
- **`archcheck` / `harness_check` / `axtest` cache verification**: PASS (`0` violations, `0` cache mismatches)
- **Tier-1 `non-selfhost` suite**: **FAIL — 4 new failing IDs outside `_workspaces/baseline-failures.txt`** (2 independent single-commit culprits identified: `bda3bb63` `T434` / `axiom-frontend` and `f0f98f33` `T489` / `axiom-semantics`).

`FULLRUN-1 REGRESSIONS: 4 new failing ids`
