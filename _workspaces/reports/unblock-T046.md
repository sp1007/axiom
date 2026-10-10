## Tóm tắt
Nhiệm vụ T046 đã bị chặn do thuật toán dòng dữ liệu quá phức tạp làm cho phạm vi nhiệm vụ quá lớn. Dựa theo quy trình giải quyết vấn đề, T046 đã được tách (split) thành hai nhiệm vụ riêng biệt:
- **T120**: Chịu trách nhiệm về mô hình bộ nhớ, phân loại sao chép (copy classification) và thiết lập pipeline cơ bản.
- **T121**: Chịu trách nhiệm về phân tích dòng dữ liệu (dataflow analysis) và các chẩn đoán lỗi use-after-move / partial-move.
Quyết định này đã được ghi lại bằng công cụ `taskctl.py adr-next` trong tệp `ADR-0019`. Nhiệm vụ T046 cũ đã được thay thế (supersede) bằng T120 và T121.

## Files changed
- spec/decisions/ADR-0019-split-t046-move-analysis.md
- _workspaces/tasks/todo/T120-place-model-copy-classification.md
- _workspaces/tasks/todo/T121-move-dataflow-analysis.md
- _workspaces/tasks/done/T046-place-model-move-copy-analysis-use-after-move-part.md
