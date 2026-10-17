# Architect Report — Relax P10 Port Sub-Task Dependencies for True Module DAG Parallelism

## Tóm tắt
Nới phụ thuộc chuỗi tuyến tính không cần thiết giữa các sub-task port P10 (`T083a..T085c`) về đúng đồ thị phụ thuộc thực tế giữa các module:
- `T083a` (`compiler/interp`) và `T084a` (`compiler/lir`) chỉ phụ thuộc vào `T082d` (`compiler/mir` + `compiler/own` đã hoàn thành), không cần chờ `T082e` (`compiler/verify`).
- `T083b` (`compiler/opt`) phụ thuộc `T082e` (`compiler/verify`), không phụ thuộc `T083a` (`compiler/interp`).
- `T085a` (`compiler/obj`) chỉ phụ thuộc `T077` (`compiler/kernel`), đồng thời cung cấp `objmodel` cho `T084d` (`compiler/target/x64/encode.ax`) và `T085b` (`compiler/link`).
- `T084c` (`compiler/target/x64`) phụ thuộc `[T084b, T084d]`.
- Các task tích hợp `T083`, `T084`, `T085c`, `T085` giữ đầy đủ phụ thuộc hội tụ.

## Files changed
- _workspaces/tasks/todo/T083a-port-interpreter-to-axiom.md
- _workspaces/tasks/todo/T083b-port-optimizer-to-axiom.md
- _workspaces/tasks/todo/T083-port-interpreter-optimizer-to-axiom.md
- _workspaces/tasks/todo/T084a-port-lir-to-axiom.md
- _workspaces/tasks/todo/T084c-port-isel-frame-to-axiom.md
- _workspaces/tasks/todo/T084d-port-encoder-to-axiom.md
- _workspaces/tasks/todo/T084-port-lir-x64-backend-encoder-to-axiom.md
- _workspaces/tasks/todo/T085a-port-coff-writer-to-axiom.md
- _workspaces/tasks/todo/T085c-port-driver-to-axiom.md
- spec/ROADMAP.md
- CLAUDE.md
