# T050 Unblock Report

## Tóm tắt
T050 bị block do Verifier kiểm tra drop chặt chẽ khiến các bài test cũ thất bại, nguyên nhân là do `builder.c` hiện tại đang sinh ra các biến tạm (`AX_MIR_LOCAL_TMP`) nhưng không sinh lệnh `drop` cho chúng. Kỹ sư đã đối phó bằng cách loại bỏ biến tạm khỏi quá trình kiểm tra missing drop. Quyết định: Không được phép nới lỏng Verifier. Đã tạo ADR-0033 và task T133 (sửa `builder.c` sinh drop cho biến tạm). T050 giờ sẽ phụ thuộc vào T133 và bị buộc phải kiểm tra chặt chẽ mọi biến.

## Decision and Rationale
The verifier was failing existing tests because `builder.c` generates temporaries that are not explicitly dropped in the MIR. The implementer of T050 hacked the verifier to only check `USER` and `ARG` locals to bypass this. This is an architectural violation: the verifier must reject invalid MIR rather than accommodate upstream bugs. 

**Decision:**
- Wrote ADR-0033 establishing that the verifier must strictly check all locals (including temporaries) for drops, and the builder must correctly emit drops for them.
- Created T133 to fix `builder.c` to properly elaborate drops for temporaries.
- Added T133 to T050's dependencies and updated T050's scope to explicitly forbid the temporary exemption hack.

Since T050 now correctly depends on T133, it is unblocked (though execution will be held by the orchestrator until T133 is done).

## Files changed
- spec/decisions/ADR-0033-drop-temporaries.md
- _workspaces/tasks/todo/T133-builder-drop-temporaries.md
- _workspaces/tasks/doing/T050-verifier-v2-ownership-capability-drop-re-verificat.md

STATUS: UNBLOCKED
