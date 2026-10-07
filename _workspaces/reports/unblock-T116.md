## Tóm tắt
Đã giải quyết tình trạng block của T116 (thiếu hỗ trợ tuple trong interpreter) bằng cách tạo ADR-0017: thay thế `AX_MIR_RVALUE_CHECKED_BINARY_OP` bằng `AX_MIR_RVALUE_OVERFLOWS_BINARY_OP` (trả về `bool`). Quyết định này giúp MIR builder có thể sinh ra explicit `Assert` terminator để kiểm tra tràn số bằng cách kiểm tra điều kiện tràn (`OverflowsBinaryOp` hoặc toán tử so sánh thông thường đối với phép chia/shift) trước khi thực hiện phép tính `BinaryOp` gốc, mà không đòi hỏi sự hỗ trợ từ hệ thống tuple vốn phức tạp và thuộc về task T117. T116 đã được cập nhật scope và thêm các file phụ thuộc để phản ánh thay đổi kiến trúc này, sau đó được unblock để sẵn sàng triển khai.

## Quyết định và Phương án (Decision with Options and Rationale)

**Blocker**: Opus agent báo cáo không thể biểu diễn `CheckedBinaryOp` trong MIR do nó trả về tuple `(result, bool)` giống Rust, nhưng interpreter v0.1 hiện chưa hỗ trợ tuple (locals chỉ là `uint64_t`). Tuy nhiên, T116 bị giới hạn là không mở rộng value model của interpreter (công việc này thuộc T117).

**Các phương án (Options)**:
1. **Chia task (Split task)**: Tạm dừng T116, thực hiện thêm tuple vào interpreter (có thể đưa T117 lên làm điều kiện tiên quyết). 
   - *Điểm trừ*: T117 lại cần T116 cung cấp panic terminator (Assert) để hiện thực panic format. Việc này tạo ra phụ thuộc vòng tròn, và thêm tuple vào lúc này làm phức tạp quá mức trình thông dịch vốn cần giữ thiết kế tối giản trong T116.
2. **Không sử dụng explicit Assert**: Thay đổi yêu cầu của T116 và SPEC-03, để việc kiểm tra tự động xảy ra ngầm (implicit trap) bên trong `AX_MIR_RVALUE_BINARY_OP`.
   - *Điểm trừ*: Đi ngược lại với mục tiêu của SPEC-03 và Native Backend là muốn hiển thị rõ ràng đồ thị luồng điều khiển (CFG) của panics trong kiến trúc MIR.
3. **Thay đổi kiến trúc MIR (ADR-0017)**: Tách `CheckedBinaryOp` thành 2 thao tác: một Rvalue tính toán `bool` tràn số (`AX_MIR_RVALUE_OVERFLOWS_BINARY_OP`) và `BinaryOp` thông thường. MIR Builder sẽ sinh mã kiểm tra tràn số, thực hiện `Assert`, rồi sau đó thực hiện phép tính chuẩn nếu vượt qua.
   - *Điểm cộng*: Trình thông dịch vẫn giữ nguyên kiểu `uint64_t`, giữ được đồ thị CFG và `Assert` tường minh, phá vỡ phụ thuộc vòng tròn với T117.

**Lý do chọn (Rationale)**:
Chọn phương án 3 (được ghi lại vào `ADR-0017`). Giải pháp này thỏa mãn cả yêu cầu khắt khe của SPEC-03 (cần đồ thị điều khiển tường minh cho panic) lẫn giới hạn của trình thông dịch (không đụng đến value model và tuple). Native backend sau này hoàn toàn có thể peephole optimize cụm "Overflows + Assert + BinaryOp" lại thành lệnh sinh mã máy hiệu quả.

## Files changed
- spec/decisions/ADR-0017-checked-arithmetic-mir.md
- _workspaces/tasks/todo/T116-vs0-fix-mir-builder-bitnot-asserts.md
