import os

def write(name, content):
    with open(f"tests/conformance/{name}", "w") as f:
        f.write(content)

write("adversarial/own_branch_003.ax", """// test: ui
struct Buffer { x: i32 }
fn consume(b: Buffer) {}
fn main() {
    let b = Buffer { x: 1 };
    let cond = true;
    if cond {
        consume(b);
    }
    drop(b); //~ ERROR AX_MOVE_USE_AFTER_MOVE
}
""")

write("stress/e001.ax", """// test: run
struct Buffer { x: i32 }
fn read(v: view<Buffer>) {}
fn main() -> i32 {
    let x = Buffer { x: 1 };
    let v = view(x);
    read(v);
    return 0;
}
""")

write("stress/e002.ax", """// test: ui
struct Buffer { x: i32 }
fn mutate(b: mut_view<Buffer>) {}
fn main() {
    let x = Buffer { x: 1 };
    let v = view(x);
    mutate(mut_view(x)); //~ ERROR AX_CAP_CONFLICT_MUT
}
""")

write("stress/f001.ax", """// test: run
struct Point { x: i32, y: i32 }
fn mutate(b: mut_view<i32>) {}
fn main() -> i32 {
    let p = Point { x: 1, y: 2 };
    let a = mut_view(p.x);
    let b = mut_view(p.y);
    mutate(a);
    mutate(b);
    return 0;
}
""")

write("stress/f002.ax", """// test: ui
struct Point { x: i32, y: i32 }
fn mutate(b: mut_view<i32>) {}
fn mutate_p(b: mut_view<Point>) {}
fn main() {
    let p = Point { x: 1, y: 2 };
    let a = mut_view(p);
    let b = mut_view(p.x); //~ ERROR AX_CAP_CONFLICT_MUT
    mutate(b);
    mutate_p(a);
}
""")
