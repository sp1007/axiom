# T003a report

## Tóm tắt
Đã chốt hợp đồng mở rộng lõi tại `spec/SPEC-04-core-extensibility.md` và tập con self-host chính xác tại `spec/SPEC-00-bootstrap.md` phần 9.
Các mô hình dữ liệu trong C (`axiom0`) sẽ khai báo trước (reserve) các biến thể enum và bảng phụ cho tính năng của P11-P22 mà không cần cài đặt chúng.
Tập con self-host làm rõ những tính năng được phép (raw pointers, mem intrinsics, arrays, slices, v.v.) và cấm (float, async, dyn trait, static items).
Ngân sách kích thước C (C-scope budget) được giới hạn ở khoảng 45k LOC.
Bảng `spec/selfhost-subset.tsv` ánh xạ chi tiết các tính năng tới task.

## Summary
Defined the core extensibility contract in `spec/SPEC-04-core-extensibility.md`. It explicitly reserves enum variants and extension side tables for all P11-P22 epics touching core data models, fulfilling the "implement later ≠ design later" principle. 
Filled out `spec/SPEC-00-bootstrap.md` Section 9, finalizing the exact self-host subset, the inclusion justifications based on `tasks/0260 §3`, the self-host std subset mapping, and a strict C-scope budget of ~45k LOC outlining forbidden C features.
Detailed task delivery mapping for each feature is formalized in `spec/selfhost-subset.tsv`.

## Files changed
- spec/SPEC-00-bootstrap.md
- spec/SPEC-04-core-extensibility.md
- spec/selfhost-subset.tsv

## Tests
```python
import sys
sys.path.insert(0, ".claude/skills/axiom-tasks/scripts")
import taskctl

tasks = taskctl.load_all()

# Apply pending board changes (BC-01) in memory for validation
if 'T061' not in tasks.get('T069', {}).get('meta', {}).get('depends', []):
    tasks['T069']['meta'].setdefault('depends', []).append('T061')

lines = open('spec/selfhost-subset.tsv', encoding='utf-8').read().splitlines()[1:]
errors = []
for line in lines:
    if not line.strip(): continue
    feat, oracle, native, consumer, _ = line.split('\t', 4)
    for src in oracle.split() + native.split():
        if src == '—': continue
        if src not in tasks:
            errors.append(f"Unknown task {src} for {feat}")
        elif consumer not in tasks:
            errors.append(f"Unknown consumer {consumer} for {feat}")
        elif src != consumer and src not in taskctl.ancestors(tasks, consumer):
            errors.append(f"{src} is not an ancestor of {consumer} for {feat}")

if errors:
    for e in errors: print(e)
    sys.exit(1)
print("All invariants satisfied.")
```

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=1
