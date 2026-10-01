# ADR-0003 — Backend pipeline: ABI lowering on LIR, machine-IR verifier, stack probes, stack reserve

## Tóm tắt
Ba quyết định cho backend của axiom0 để axiomc (do axiom0 biên dịch) chạy ổn định:
(1) **ABI lowering là một pass LIR→LIR trước chọn lệnh** — giữ ABI ngoài MIR như tài liệu yêu cầu,
chỉ khác vị trí so với sơ đồ 0262 §19 vì LIR đã có bộ nhớ tường minh (cần cho bản sao aggregate);
(2) **bộ kiểm tra machine IR** chạy trước encoder trong mọi bản build dùng để test, để lỗi chọn lệnh
thành ICE đúng chỗ thay vì exe bị crash; (3) **stack probe** cho khung > 4 KB (Windows bắt buộc chạm
từng trang) và tuỳ chọn `--stack-reserve`; axiomc được build với stack 64 MB. Không đụng R7 (vẫn
không có regalloc linear scan trước T087). Task liên quan: T025, T025b (mới), T027, T028, T037, T086.
Revisit: không.

Status: **Accepted** (architect, audit 2026-09-30, findings A2-11, A2-12, A1-02).
Date: 2026-09-30. Revisit: no.

## Context

- Layer order in axiom-c-stage0 is `… lir < abi < target/x64`; tasks/0262 §19 draws
  "MIR → ABI lowering → LIR → Machine", 0264 §22 lists `abi: [mir]`. The ABI must stay out of MIR
  (0262 §19) — both orders satisfy that.
- 0181 §31 requires a MachineVerifier before encoding and an EncodingVerifier after it.
- Naive lowering gives every MIR local and temp a stack slot (T023, BOOTSTRAP-SHORTCUT). axiomc
  functions (parser, isel, encoder tables) will have frames above 4 KB; Windows commits the stack
  page by page through a guard page, so a frame larger than one page must be probed in order
  (0188 §12). The default PE stack reserve is 1 MB (pe-coff.md). No task implemented either.

## Options

A. ABI placement: (A1) ABI lowering between MIR and LIR (new layer order `mir < abi < lir`);
   (A2) ABI lowering as a LIR→LIR pass before isel, keep the layer order.
B. Machine checks: (B1) rely on GNU-as-validated encoder tables only; (B2) machine-IR verifier.
C. Stack: (C1) inline probe loop for frames > 4096 bytes + configurable reserve; (C2) call a CRT
   `__chkstk` (forbidden: no CRT); (C3) slot reuse only.

## Decision

- **A2.** MIR→LIR lowering emits calls with abstract ABI placeholders; the `abi` module rewrites LIR
  into ABI-explicit LIR (argument/return locations, hidden return pointer, by-reference copies of
  large aggregates, shadow space and alignment as frame requirements) before x64 isel. Reason: the
  by-reference aggregate copies need explicit memory, which LIR has and MIR must not; the result is
  the same separation 0262 §19 asks for. SysV (E16.9) and other ABIs plug in as another `abi`
  description + the same pass. The x64 skill pipeline text is updated accordingly.
- **B2.** A machine-IR verifier (operand-form legality per encoder table, register classes, 16-byte
  call-site alignment, shadow space present, frame size consistency) runs before the encoder in every
  build used by tools/axtest.py and CI; violations are ICEs. The round-trip decoder (EncodingVerifier)
  waits for E17/E16 work.
- **C1.** Frame lowering emits, for frames > 4096 bytes, an inline loop that touches each page from
  the top of the new frame downward before the final `sub rsp` (no CRT call). The linker/driver take
  `--stack-reserve <bytes>` (default 0x100000, SizeOfStackReserve; commit stays 0x1000).
  `tools/bootstrap.py` (T086/T087) builds axiomc with `--stack-reserve 67108864`. Slot reuse is not
  required (optional optimisation inside T023 if cheap).

## Consequences

- T025 is narrowed to ABI lowering + machine IR + baseline isel; new T025b does frame lowering, stack
  probes, the machine-IR verifier and `--emit=mc`.
- T027 implements `--stack-reserve` in the linker; T028 exposes it in the driver; T037 adds native
  tests with a 64 KB local array and deep recursion over > 4 KB frames; T086 uses 64 MB.
- Linear-scan register allocation stays post-T087 (R7); T086 measures compile time (ADR-0005 §6).

## Sources
0181 §31-32, 0188 §12, 0263 §27 §49, tasks/0262 §19, 0264 §22, 0172 §16,
`.claude/skills/axiom-x64-backend/references/pe-coff.md`; audit A2-11, A2-12, A1-02.
