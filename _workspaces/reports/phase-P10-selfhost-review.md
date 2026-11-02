# Phase Review — `P10-selfhost` (Self-Hosting Compiler `axiomc` & Stage-2/3 Fixed Point)

## Tóm tắt
Báo cáo thẩm định kiến trúc khi hoàn tất trọn vẹn **Phase 10 (`P10-selfhost`)** tại commit `031058d` (`T087`):
1. **Hoàn thành 63/63 task của `P10-selfhost`**: toàn bộ thư viện chuẩn `std` (`core`, `alloc`, `collections`, `io`, `fs`, `path`, `env`, `process`, `hash`, `fmt`, `test`) và trình biên dịch tự thân `compiler/` gồm **121 module viết hoàn toàn bằng Axiom** (từ `kernel`, `source`, `diag`, `lex`, `parse`, `ast`, `hir`, `modules`, `resolve`, `types`, `typeck`, `mir`, `own`, `verify`, `interp`, `opt`, `lir`, `target/x64`, `obj`, `link`, tới `driver` và `main`) đã hoàn tất và vượt qua kiểm định QA.
2. **Đạt điểm cố định (Fixed Point) đồng nhất từng byte ở cả `-O0` và `-O1` (`MS-P10b`, `INV-DET-004`, `INV-BOOT-003`)**:
   - Chuỗi bootstrap 4 giai đoạn (`axiom0 -> axiomc1 -> axiomc2 -> axiomc3`) chạy trên hai thư mục độc lập (`dir_stage2_<opt>` và `dir_stage3_<opt>`) khi đã gỡ bỏ hoàn toàn mọi trình biên dịch C / hợp ngữ / trình liên kết ngoài (`gcc`, `clang`, `ld`, `as`, `link`, `cl`, `lld`) khỏi `PATH`.
   - Tại **`-O0`**: `axiomc2_O0.exe` và `axiomc3_O0.exe` đồng nhất 100% từng byte (`15,643,136` bytes, `sha256=f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d`).
   - Tại **`-O1`**: `axiomc2_O1.exe` và `axiomc3_O1.exe` đồng nhất 100% từng byte (`15,594,496` bytes, `sha256=9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6`).
3. **Vượt qua 100% bộ kiểm thử toàn cục (`MS-P10a/b`)**: `axiomc2.exe` vượt qua **`2,888 / 2,888` mục kiểm thử hoạt động** trên `1,319` tệp kiểm thử (`0 FAIL`, `0 XFAIL`, `21 SKIP` có thẻ `requires: axiom0-internal`), bao gồm `443 / 443` tệp (`1,148 / 1,148` mục) trong tập kiểm chứng độc lập `ADR-0034 §3` với `WEAK-NATIVE 0`.
4. **Đóng băng `bootstrap/axiom0` (`axiom0-frozen`) & chuyển sang `P11-concurrency`**: thẻ nội bộ `axiom0-frozen` đã được gắn tại `031058d` (`ROADMAP R3`, `ADR-0005 §15`, `INV-BOOT-004`); từ nay mọi phát triển ngôn ngữ, tối ưu hóa và backend thực hiện hoàn toàn trên `compiler/` và `std/` bằng Axiom, mở đầu với `T211` (`Plan phase P11 — Concurrency & async`).

---

## 1. Phase 10 (`P10-selfhost`) Completion Summary

- **Phase Tasks**: `63 / 63` tasks in `P10-selfhost` are `done` (`202` total `done` tasks across `P0`–`P10`, `0 doing`, `0 blocked`, `0 parked`).
- **Stage-1 / Stage-2 / Stage-3 Bootstrap Chain (`T086`, `T087`, `spec/BOOTSTRAP.md`)**:
  - `axiom0.exe` (Stage 0, C11 seed): `866,060` bytes (`sha256=000eae25548ef4947c1ebb9ed270792bc9789567114e3ad2444aa118c9dc3910`).
  - `axiomc1.exe` (Stage 1, built by `axiom0` from 121 `compiler/**/*.ax` modules + `std/**/*.ax`): `15,644,160` bytes (`sha256=c1ac76db1249c2b37cd688af149f3740b2b81360feb977e3238d288e9a091ce0`).
  - `axiomc2.exe` == `axiomc3.exe` at **`-O0`** (in `dir_stage2_O0` vs `dir_stage3_O0`): `15,643,136` bytes (`sha256=f2e4d6a65abb7caadd8ad283823d428d158c2e55cdb44702b471f0653d394f8d`).
  - `axiomc2.exe` == `axiomc3.exe` at **`-O1`** (in `dir_stage2_O1` vs `dir_stage3_O1`): `15,594,496` bytes (`sha256=9a0c7e51b482a924ac802a376f12d4705abed0eaea930ac5f01a7dbd6b5981c6`).
- **Full Test Suite & `ADR-0034 §3` Independent Oracle Subset**:
  - Full suite under `axiomc2.exe`: `TOTAL 2909 PASS 2888 FAIL 0 SKIP 21 XFAIL 0` (`1,319` active test files, `21` C-internal `axiom0-internal` manifests excluded).
  - `ADR-0034 §3` independent subset (`run/numeric`, `run/drop`, `run/ptr`, `run/native_*`, `std/`): `443 / 443` test files (`1,148 / 1,148` test entries) `PASS` with `WEAK-NATIVE 0`.

---

## 2. Spec Drift & Shortcuts to Retire

- **Spec Drift**: None blocking. All `P0`–`P10` (`v1-core`) semantic discrepancies discovered during self-hosting were resolved via canonical ADRs (`ADR-0032` through `ADR-0035`) and dedicated `P10-selfhost` parity tasks (`T134`–`T164`) prior to closing `T086` and `T087`.
- **Shortcuts Retired & `bootstrap/axiom0` Freeze (`ROADMAP R3`, `ADR-0005 §15`, `INV-BOOT-004`)**:
  - Every `native-after: T086` marker and temporary Stage-0 divergence was retired before `T086` / `T087` acceptance.
  - Local Git tag `axiom0-frozen` is present at `031058dae2779b6e800e7c3df201376d69c781fa` (`HEAD`).
  - `bootstrap/axiom0/` is now permanently frozen as the Stage-0 seed compiler. `harness_check.py` mechanically rejects any post-`axiom0-frozen` commit or `P11+` task that touches `bootstrap/axiom0/`.
  - All per-task builds from `P11` onward use `python tools/build_axiomc.py --out build-snap-<ID>/build` and test against `build-snap-<ID>/build/axiomc2.exe` (`spec/BOOTSTRAP.md §4`).

---

## 3. Governance, Traceability & Milestone Gate Checks

1. **Harness & Freeze Tag Check (`harness_check.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/harness_check.py`
   - Result: `HARNESS OK` (exit `0`, verified with local tag `axiom0-frozen` present at `031058d`).
2. **Board Reconciliation & Validation (`taskctl.py reconcile` / `validate`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py reconcile`
   - Result: `reconcile: every done task has its commit` (exit `0`).
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py validate`
   - Result: `OK (242 tasks)` (exit `0`).
3. **Requirements Coverage (`reqcov.py`)**:
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --phase P10-selfhost`
   - Result: All 34 `P10-selfhost` requirement mappings (`REQ-ABI-106..108`, `REQ-CORE-3181`, `REQ-DRP-183`, `REQ-DRV-020..022`, `REQ-ERR-087`, `REQ-GEN-100`, `REQ-LAY-298`, `REQ-LEX-114`, `REQ-LIR-030`, `REQ-MIR-338..340`, `REQ-MOD-142`, `REQ-OPT-387..389`, `REQ-OWN-001..006`, `REQ-OWN-338`, `REQ-PKG-023`, `REQ-RES-243`, `REQ-TGT-327`, `REQ-TRT-139`, `REQ-TYP-354..355`, `REQ-X64-001`) are `done`.
   - Command: `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`
   - Result:
     - `requirements: 32308`
     - `v1-core: implemented=5864` (100% of `v1-core` implemented in `P0`–`P10`)
     - `v1-full: epic=8788 implemented=2 planned=41`
     - `post-v1: epic=17598 planned=15`
     - `gaps: 0` — **`COVERAGE OK`** (exit `0`).
4. **Milestone Gate Check (`gatecheck.py`)**:
   - Command: `python tools/gatecheck.py --gate T087 --no-run`
   - Result: `MS-P1 PASS`, `MS-P2 PASS`, `MS-P3 PASS`, `MS-P4 PASS`, `MS-P5 PASS`, `MS-P6 PASS`, `MS-P7 PASS`, `MS-P8 PASS`, `MS-P9 PASS`, `MS-P10a PASS`, `MS-P10b PASS` (exit `0`).
5. **Architecture Layer Check (`archcheck.py`)**:
   - Command: `python tools/archcheck.py`
   - Result: `archcheck: 192 files scanned, 0 violations` (exit `0`).

---

## 4. Backlog Readiness for Phase 11 (`P11-concurrency-async`)

- `python .claude/skills/axiom-tasks/scripts/taskctl.py status`:
  - `total 242 | done 202 | doing 0 | todo 38 | blocked 0 | parked 0 | deferred 2`
  - `ready: T211`
- Next ready task: **`T211`** (`Plan phase P11 — Concurrency & async (expand roadmap epics into tasks)`, owner `axiom-architect`, `priority: 6`, `depends: [T087]`), which will expand `E11.*` epics in `spec/ROADMAP.md §3` into concrete `T400`–`T449` tasks targeting `compiler/` and `std/` and wire them into gate `T311`.

## Files changed
- _workspaces/reports/phase-P10-selfhost-review.md
