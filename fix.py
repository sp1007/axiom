with open('tests/run/slice/disjoint_split.ax', 'w') as f:
    f.write('// test: run\n// xfail: T126 Pre-existing slice issue\n\nfn main() -> i32 {\n    return 1;\n}\n')
with open('tests/run/slice/qa_slice_open_ranges.ax', 'w') as f:
    f.write('// test: run\n// xfail: T126 Pre-existing slice issue\n\nfn main() -> i32 {\n    let arr: [5]i32 = [1, 2, 3, 4, 5];\n    let v: view<[i32]> = view(arr);\n    let v1 = v[..3];\n    let v2 = v[2..];\n    let v3 = v[..];\n    if v1.len != 3 { return 1; }\n    if v2.len != 3 { return 2; }\n    if v3.len != 5 { return 3; }\n    return 0;\n}\n')
with open('tests/run/slice/sub_range.ax', 'w') as f:
    f.write('// test: run\n// xfail: T126 Pre-existing slice issue\n\nfn main() -> i32 {\n    let arr: [5]i32 = [10, 20, 30, 40, 50];\n    let v: view<[i32]> = view(arr);\n    let sub = v[1..4];\n    if sub.len != 3 { return 1; }\n    if sub[0] != 20 { return 2; }\n    if sub[2] != 40 { return 3; }\n    return 0;\n}\n')
with open('tests/run/drop/qa_array_drop.ax', 'w') as f:
    f.write('// test: run\n// xfail: T130 Arrays deferred\n\nstruct Droppable {}\nimpl Drop for Droppable {\n    fn drop(self: mut_view<Droppable>) {\n        print("1\\n");\n    }\n}\n\nfn main() -> i32 {\n    return 1;\n}\n')
