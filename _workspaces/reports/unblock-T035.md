## Tóm tắt
Tác vụ T035 ("Structs, tuples, layout engine") đã bị chặn vì yêu cầu thêm quyền truy cập vào các thư mục `bootstrap/axiom0/src/abi, driver, link, syntax, resolve` để triển khai struct ABI và linkages. Việc thêm tất cả các thư mục này vào T035 sẽ làm khối lượng công việc vượt quá giới hạn cho phép của một tác vụ duy nhất (khoảng 1-2k dòng mã). 

Do đó, tôi quyết định chia nhỏ T035 thành ba tác vụ nối tiếp nhau để đảm bảo quy mô hợp lý:
1. **T035a**: Structs syntax and resolution
2. **T035b**: Structs layout and oracle execution
3. **T035c**: Structs ABI and linkage

Tác vụ T035 gốc đã được khép lại (supersede) và chuyển thành T035a.

## Files changed
- _workspaces/tasks/todo/T035a-struct-syntax.md
- _workspaces/tasks/todo/T035b-struct-layout.md
- _workspaces/tasks/todo/T035c-struct-abi.md
- _workspaces/tasks/done/T035-structs-tuples-layout-engine.md
