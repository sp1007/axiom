---
id: T487
title: Tooling — seeded fast bootstrap for task gates (HEAD's stage-2 compiler builds the new source; full axiom0 chain kept as the periodic trust check), no duplicate bootstraps inside the suite
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T444c]
priority: 10
status: done
attempts: 1
timeout_min: 600
paths: [tools/bootstrap.py, tools/build_axiomc.py, tools/tests/build_axiomc, tests/selfhost/fixedpoint, tests/selfhost/obj_link_driver/axiomc_e2e_oracle.py, _workspaces/baseline-failures.txt]
locks: [tools/taskgate.py, tools/axtest.py]
spec: [spec/SPEC-20-selfhost.md, spec/SPEC-00-bootstrap.md, spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md]
covers: [REQ-BLD-028, REQ-TST-072]
started: 2026-11-19 09:33:03
finished: 2026-11-20 02:26:46
---
# T487 — Seeded fast bootstrap for gates

## Why (owner request 2026-11-18)
The earlier Axiom prototype (`D:\projects\compiler\Axiom`) cut its gate from hours to minutes mainly with a
**fast fixpoint seeded from the already-built native compiler** instead of rebuilding from the slow stage-0 path
every time (`scripts/fast_fixpoint.ps1`: seed → A → B → C, B==C; the slow chain kept only as a final check).
Measured here on 2026-11-18 (same input `tests/selfhost/parse/qa_parse_corpus_a.ax`, 11k lines):

| compiler | typeck | own | build |
|---|---|---|---|
| `axiomc1` (built by axiom0) | 1.10 s | 4.38 s | 32.9 s |
| `axiomc2` (self-built, -O1) | 0.35 s | 1.78 s | 9.5 s |

`axiomc1` is ~3.4× slower than `axiomc2`, and every gate currently spends its longest step on `axiomc1 → axiomc2`
(2228 s wall for the 281k-line compiler on the loaded box, T485 report), at O1 and again at O0, and then
`tests/selfhost/fixedpoint/fixedpoint.test` runs `bootstrap.py --check-both-opt` again inside the suite.
(Windows Defender was checked as the other cause in the old project: here a fresh exe costs ~0.1 s, not a factor.)

## Scope
1. **Measure first** (record a table in the report): the wall time of every compiler build a gate performs today —
   axiom0→c1, c1→c2 (O1, O0), c2→c3 (O1, O0), the builds inside `fixedpoint.test` and `axiomc_e2e.test` — and
   which of them are duplicates of each other.
2. **Seeded mode** in `tools/build_axiomc.py` / `tools/bootstrap.py` (`--seed <path>` or automatic from the cache):
   `A = seed(new source)`, `B = A(new source)`, `C = B(new source)` at the same opt level; require `B == C`
   byte-identical (the fixed point); the compiler under test is `B`. Do the same for O0 where the gate needs O0.
   The seed is the stage-2 compiler of the base commit, stored in a content-addressed cache
   (`_workspaces/artifacts/compiler-cache/`, keyed by the T444c input manifest) by `build_axiomc.py` whenever it
   finishes a full or seeded build; missing seed → fall back to the full chain automatically.
3. **Stage-0 guard per task (kept, cheap):** axiom0 → `axiomc1` must still succeed on the new source (INV-BOOT-005
   symbol-id headroom, ADR-0043), and `axiomc1` compiles a fixed smoke set (including "Xin chào thế giới") whose
   `.exe` bytes equal those produced by `B`. Only the long `c1 → c2` leg moves out of the per-task gate.
4. **Full chain stays the trust root:** axiom0 → c1 → c2 → c3 at O0 and O1, **plus `c2 == B` byte-identical**
   (proves the seeded compiler is exactly the compiler the trust root produces), runs in every Tier-1/Tier-2 sweep
   (`fullrun.py`), in phase gates, and in the per-task gate of any task that changes `bootstrap/axiom0`,
   `tools/bootstrap.py` or `tools/build_axiomc.py`. Document the rule in the report so the architect can update
   `.claude/agents/axiom-qa.md` and the axiom-testing skill (harness files are not in this task's paths).
5. **No duplicate bootstraps:** `fixedpoint_oracle.py` and `axiomc_e2e_oracle.py` reuse the stage binaries the gate
   already built when their input manifests match (print `REUSED …`), and rebuild otherwise. Their checks
   (two directories, both opt levels, functional parity) are unchanged.
6. **Timeouts (T485 gate F-3):** `fixedpoint_oracle.py:179` hard-codes `timeout=1500` for `bootstrap.py
   --check-both-opt` while stage 2 alone takes 36–45 min on the shared machine, so the test can never pass there.
   Derive inner timeouts from the test's own budget / `--timeout-scale` (no hard-coded inner limit shorter than the
   test timeout). Remove `selfhost/fixedpoint/fixedpoint.test` from `_workspaces/baseline-failures.txt` when it passes.

## Acceptance (quality guards — mandatory, this is a compiler)
- On at least 3 commits (HEAD and two earlier accepted commits): the seeded `B` is byte-identical to the full-chain
  `axiomc2` at O1 and O0; the report lists the sha256 values.
- A deliberately non-deterministic change (temporary, in a scratch copy) makes the seeded mode fail with `B != C`;
  a source that axiom0 cannot compile (e.g. synthetic symbol-id overflow) fails the stage-0 guard. Both shown in the
  report (mutation proof that the guards bite).
- Self-tests in `tools/tests/build_axiomc/` (fake stage driver, run in seconds): seed hit, seed miss → full chain,
  B≠C → failure, stage-0 failure → failure, reuse inside fixedpoint oracle.
- Before/after wall time of the compiler-build part of one gate on the same snapshot; target ≥ 2× less.
- Normal gate passes; `fixedpoint.test` and `axiomc_e2e.test` still pass with the same assertions.

## Out of scope
- Making the compiler itself faster (T485 own, T486 build). `taskctl.py`/harness scripts (orchestrator applies the
  documented rule after acceptance).

## Log
- 2026-11-18 created by orchestrator (owner request: apply the fast-gate approach of the earlier Axiom project)
- 2026-11-19 08:07:25 started (attempt 1) T487-impl
- 2026-11-19 08:45:35 requeue: RESOURCE_EXHAUSTED (code 429): Individual quota reached. Resets in 43m8s. (infrastructure failure: attempt refunded)
- 2026-11-19 09:33:03 started (attempt 1) T487-impl
- 2026-11-20 02:26:46 accepted by QA -> done
