# ADR-0033: Verifier and Builder Treatment of Temporaries

## Tóm tắt
Quyết định kiến trúc về việc giải phóng (drop) các biến tạm (temporaries). Verifier không được phép bỏ qua biến tạm khi kiểm tra missing drop. Nếu một biến tạm giữ giá trị cần drop, builder bắt buộc phải sinh ra lệnh `drop` cho biến tạm đó. Mọi giải pháp vòng vo (hack) trong verifier để phớt lờ lỗi của builder đều bị cấm.

## Context
During the implementation of Verifier v2 (T050), it was discovered that `builder.c` fails to emit implicit drops for temporary variables (`AX_MIR_LOCAL_TMP`) holding values that require dropping (e.g. function return values that are not consumed). 
Instead of fixing `builder.c`, the implementation of the verifier added a loophole exempting temporaries from the `AX_VERIFY_MISSING_DROP` check to allow existing tests to pass.
This compromises the integrity of the verifier. The verifier's purpose is to reject invalid MIR, not to accommodate known bugs in earlier stages.

## Options
1. **Option A (Relax Verifier)**: Exempt `AX_MIR_LOCAL_TMP` from drop checks in the verifier.
2. **Option B (Strict Verifier, Fix Builder)**: The verifier strictly checks all locals, including temporaries, for missing drops. The builder's missing drop elaboration for temporaries is treated as a bug and fixed in a separate task.

## Decision
**Option B is chosen.**
- **Verifier:** Must strictly enforce drop checks on all locals that are initialized and of a drop-requiring type, regardless of whether they are user locals, arguments, or temporaries.
- **Builder:** Must correctly elaborate drops for temporaries before they go out of scope.

## Consequences
- The Verifier (T050) will be implemented strictly.
- A new task (T133) is created to implement drop elaboration for temporaries in `builder.c`.
- T050 will depend on T133.
- The verifier will correctly flag un-dropped temporaries, which may cause tests to fail until T133 is completed.

## Revisit
No.
