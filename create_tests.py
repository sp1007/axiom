import os

def write(name, content):
    with open(f"tests/conformance/adversarial/{name}", "w") as f:
        f.write(content)

write("own_001.ax", """// test: run
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn main() -> i32 {
    let a = Buffer { x: 1 };
    let b = a;
    consume(b);
    return 0;
}
""")

write("own_002.ax", """// test: ui
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn main() {
    let a = Buffer { x: 1 };
    let b = a;
    consume(a); //~ ERROR AX_MOVE_USE_AFTER_MOVE
}
""")

write("own_003.ax", """// test: ui
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn main() {
    let a = Buffer { x: 1 };
    let b = a;
    let c = a; //~ ERROR AX_MOVE_USE_AFTER_MOVE
}
""")

write("own_004.ax", """// test: run
fn main() -> i32 {
    let a: i32 = 10;
    let b = a;
    let c = a;
    return 0;
}
""")

write("own_005.ax", """// test: run
struct Buffer { x: i32 }
fn make() -> Buffer {
    let b = Buffer { x: 1 };
    return b;
}
fn main() -> i32 {
    make();
    return 0;
}
""")

write("own_branch_001.ax", """// test: ui
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn use_b(b: Buffer) {}
fn main() {
    let b = Buffer { x: 1 };
    let cond = true;
    if cond {
        consume(b);
    }
    use_b(b); //~ ERROR AX_MOVE_USE_AFTER_MOVE
}
""")

write("own_branch_002.ax", """// test: run
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn main() -> i32 {
    let b = Buffer { x: 1 };
    let cond = true;
    if cond {
        consume(b);
    } else {
        consume(b);
    }
    return 0;
}
""")

write("own_branch_004.ax", """// test: run
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn f() -> Buffer {
    let b = Buffer { x: 1 };
    let cond = true;
    if cond {
        return b;
    }
    consume(b);
    return Buffer { x: 2 };
}
fn main() -> i32 {
    f();
    return 0;
}
""")

write("own_loop_001.ax", """// test: ui
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn use_b(b: Buffer) {}
fn main() {
    let b = Buffer { x: 1 };
    let cond = true;
    while cond {
        consume(b); //~ ERROR AX_MOVE_USE_AFTER_MOVE
    }
}
""")

write("partial_001.ax", """// test: run
struct Buffer { x: i32 }
struct User { age: i32, name: Buffer }
fn main() -> i32 {
    let user = User { age: 20, name: Buffer { x: 1 } };
    let name = user.name;
    let a = user.age;
    return 0;
}
""")

# Revert e003.ax to the previous state but make it a ui test
with open("tests/conformance/stress/e003.ax", "w") as f:
    f.write("""// test: ui
struct Buffer { x: i32 }
fn read(v: view<Buffer>) {}
fn mutate(b: mut_view<Buffer>) {}
fn main() {
    let b = Buffer { x: 1 };
    let v = view(b);
    read(v);
    mutate(mut_view(b)); //~ ERROR AX_CAP_CONFLICT_MUT
}
""")
