#!/usr/bin/env python3
"""Generator and checker for the selfhost drop-elaboration differential (T082d).

    python tests/selfhost/drop/gen_drop_tests.py goldens --oracle <ct_selfhost_drop_cdriver_drop_oracle> --axiom0 <axiom0>
        Re-creates, for every fixture fixtures/<name>.ax, <name>.pre.mir (`axiom0 inspect
        --emit=mir`) and <name>.drop.mir (C `ax_mir_drop_elaborate`, printed by
        cdriver_drop_oracle.c).

    python tests/selfhost/drop/gen_drop_tests.py bundles
        Re-creates qa_drop_<group>.ax: the compiler modules (see MODULES) as one multi-module
        program, the fixtures and their goldens as byte tables, and the main() of harness_main.ax.in,
        which lowers every fixture with the Axiom port and compares the printed MIR before and
        after drop elaboration with the goldens byte for byte.

    python tests/selfhost/drop/gen_drop_tests.py check --oracle <ct_selfhost_drop_cdriver_drop_oracle>
        Exits 0 when the C oracle still prints exactly the committed goldens, and when every
        synthetic-destructor golden <name>.synth.mir (produced by the Axiom port) matches the C
        elaboration of <name>.impl.ax up to type and symbol numbering. Run by drop_oracle.test.

    python tests/selfhost/drop/gen_drop_tests.py bless-synth <harness stdout>
        Writes <name>.synth.mir from the "ACTUAL (synthetic destructor)" sections of a failing
        harness run. Review the result with `check` before committing it.

Run from the repository root. Files are written with LF line endings.
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
FIXTURES = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

# Compiler modules in dependency order, all loaded from HEAD `compiler/`.
MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.kernel_source_diag.session", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.lex.scanner", "compiler"),
    ("compiler.lexer.session", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.syntax.parse", "compiler"),
    ("compiler.parser.session", "compiler"),
    ("compiler.resolve.symtab", "compiler"),
    ("compiler.resolve.rib", "compiler"),
    ("compiler.resolve.resolver", "compiler"),
    ("compiler.hir.hir", "compiler"),
    ("compiler.hir.lower", "compiler"),
    ("compiler.resolve_hir.session", "compiler"),
    ("compiler.types.types", "compiler"),
    ("compiler.types.layout", "compiler"),
    ("compiler.types.exhaust", "compiler"),
    ("compiler.traits.solver", "compiler"),
    ("compiler.traits.mono", "compiler"),
    ("compiler.types.typeck", "compiler"),
    ("compiler.types", "compiler"),
    ("compiler.traits", "compiler"),
    ("compiler.typeck.session", "compiler"),
    ("compiler.typeck", "compiler"),
    ("compiler.typeck_traits.session", "compiler"),
    ("compiler.typeck_traits", "compiler"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
]

# Test files and the fixture each one checks: one fixture per file, because every case runs the
# whole front end two or three times and the MIR interpreter needs several minutes per pass.
GROUPS = [
    ("d01", "d01", ["d01_scope_exit"]),
    ("d02", "d02", ["d02_conditional_move"]),
    ("d03", "d03", ["d03_struct_fields"]),
    ("d04", "d04", ["d04_enum_variants"]),
    ("d05", "d05", ["d05_mixed_nesting"]),
    ("d06", "d06", ["d06_control_flow"]),
    ("d07", "d07", ["d07_call_results"]),
    ("d09", "d09", ["d09_closures"]),
    ("d10", "d10", ["d10_destructor"]),
    ("d11", "d11", ["d11_qa_edges"]),
    ("d12", "d12", ["d12_scalar_destructor"]),
]

# Fixtures whose C goldens are kept (and checked by drop_oracle.test) but that no Axiom harness
# runs yet, because the Axiom front end cannot lower them (follow-ups in the T082d report):
#   d08_generic_containers - the Axiom type checker rejects every generic struct literal and
#                            generic enum constructor with AX_TYPE_MISMATCH.
BLOCKED_FIXTURES = ["d08_generic_containers"]

PRELUDE = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=ROOT)

SYNTH_MARK = "--- ACTUAL (synthetic destructor) ---"



# ------------------------------------------------------------------------------------------------
# Files and processes
# ------------------------------------------------------------------------------------------------

def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def fixture_names():
    """Fixture base names: fixtures/<name>.ax without a further dot (d10_destructor.impl.ax is an
    oracle-only input)."""
    return sorted(f[:-3] for f in os.listdir(FIXTURES) if f.endswith(".ax") and "." not in f[:-3])


def fixture_rel(name, suffix=".ax"):
    return "tests/selfhost/drop/fixtures/%s%s" % (name, suffix)


def fixture_path(name, suffix):
    return os.path.join(FIXTURES, name + suffix)


def has_synth(name):
    return os.path.isfile(fixture_path(name, ".impl.ax"))


def run(cmd):
    exe = cmd[0]
    if not os.path.isfile(exe) and os.path.isfile(exe + ".exe"):
        exe = exe + ".exe"
    cmd = [os.path.abspath(exe)] + cmd[1:]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        sys.stderr.write(res.stderr.decode("utf-8", "replace"))
        raise SystemExit("command failed (%d): %s" % (res.returncode, " ".join(cmd)))
    return res.stdout


def oracle_output(oracle, rel, pre):
    cmd = [oracle, "--std-root", "std"]
    if pre:
        cmd.append("--pre")
    cmd.append(rel)
    out = run(cmd)
    header = ("== %s\n" % rel).encode("utf-8")
    if not out.startswith(header):
        raise SystemExit("unexpected oracle output for %s" % rel)
    return out[len(header):]


def arg_value(args, flag):
    if flag not in args or args.index(flag) + 1 >= len(args):
        raise SystemExit("missing %s <path>" % flag)
    return args[args.index(flag) + 1]


# ------------------------------------------------------------------------------------------------
# Synthetic destructor comparison
# ------------------------------------------------------------------------------------------------

def split_bodies(text):
    """MIR dump -> list of `mir_body { ... }` texts."""
    bodies = []
    current = []
    for line in text.split("\n"):
        if line == "mir_body {":
            current = [line]
        elif line == "}" and current:
            current.append(line)
            bodies.append("\n".join(current))
            current = []
        elif current:
            current.append(line)
    return bodies


def canonical(body):
    """Renumbers `type#N` and called fn constants by first appearance, so two elaborations that
    differ only in how the front end numbered types and symbols compare equal."""
    names = {}

    def rename(kind, value):
        key = (kind, value)
        if key not in names:
            names[key] = "%s%d" % (kind, sum(1 for k in names if k[0] == kind))
        return names[key]

    body = re.sub(r"type#(\d+)", lambda m: rename("T", m.group(1)), body)
    body = re.sub(r"= const (\d+)\(", lambda m: "= const " + rename("F", m.group(1)) + "(", body)
    return body


def synth_matches_c(oracle, name):
    synth = read_bytes(fixture_path(name, ".synth.mir")).decode("utf-8")
    c_text = oracle_output(oracle, fixture_rel(name, ".impl.ax"), False).decode("utf-8")
    ours = split_bodies(synth)
    theirs = split_bodies(c_text)
    # The C dump also holds the destructor's own body, after the bodies of the plain fixture.
    if len(theirs) < len(ours):
        return False
    return all(canonical(a) == canonical(b) for a, b in zip(ours, theirs))


# ------------------------------------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------------------------------------

def cmd_goldens(args):
    oracle = arg_value(args, "--oracle")
    axiom0 = arg_value(args, "--axiom0")
    for name in fixture_names():
        pre = run([axiom0, "inspect", "--emit=mir", fixture_rel(name)])
        if pre != oracle_output(oracle, fixture_rel(name), True):
            raise SystemExit("%s: oracle --pre differs from inspect --emit=mir" % name)
        write_bytes(fixture_path(name, ".pre.mir"), pre)
        write_bytes(fixture_path(name, ".drop.mir"), oracle_output(oracle, fixture_rel(name), False))
        print("golden", name)


def cmd_check(args):
    oracle = arg_value(args, "--oracle")
    bad = 0
    names = fixture_names()
    for name in names:
        for pre, ext in ((True, ".pre.mir"), (False, ".drop.mir")):
            want = read_bytes(fixture_path(name, ext))
            got = oracle_output(oracle, fixture_rel(name), pre)
            if got != want:
                print("MISMATCH %s%s" % (name, ext))
                bad += 1
        if has_synth(name) and not synth_matches_c(oracle, name):
            print("MISMATCH %s.synth.mir vs C elaboration of %s.impl.ax" % (name, name))
            bad += 1
    if bad:
        raise SystemExit(1)
    print("OK drop oracle goldens (%d fixtures)" % len(names))


def cmd_bless_synth(args):
    if not args:
        raise SystemExit("usage: bless-synth <harness stdout>")
    text = read_bytes(args[0]).decode("utf-8")
    pattern = re.compile(r"^tests/selfhost/drop/fixtures/(\w+)\.ax\n" + re.escape(SYNTH_MARK) +
                         r"\n(.*?)--- EXPECTED ---\n", re.S | re.M)
    count = 0
    for m in pattern.finditer(text):
        write_bytes(fixture_path(m.group(1), ".synth.mir"), m.group(2).encode("utf-8"))
        print("blessed", m.group(1))
        count += 1
    if count == 0:
        raise SystemExit("no synthetic-destructor sections found")


def byte_table(name, data):
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, values):
    lines = ["const %s: [%d]u32 = [" % (name, len(values))]
    for i in range(0, len(values), 10):
        chunk = values[i:i + 10]
        lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def main_module(group_upper, names):
    blobs = []
    synth_flags = []
    for name in names:
        blobs.append(fixture_rel(name).encode("utf-8"))
        blobs.append(read_bytes(fixture_path(name, ".ax")))
        blobs.append(read_bytes(fixture_path(name, ".pre.mir")))
        blobs.append(read_bytes(fixture_path(name, ".drop.mir")))
        if has_synth(name):
            synth_path = fixture_path(name, ".synth.mir")
            blobs.append(read_bytes(synth_path) if os.path.isfile(synth_path) else b"")
            synth_flags.append(1)
        else:
            blobs.append(b"")
            synth_flags.append(0)
    data = b"".join(blobs)
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))
    template = read_bytes(os.path.join(HERE, "harness_main.ax.in")).decode("utf-8")
    text = template.replace("@CASE_COUNT@", str(len(names)))
    text = text.replace("@GROUP@", group_upper)
    text = text.replace("@DATA_TABLE@", byte_table("DROP_DATA", data))
    text = text.replace("@OFFSET_TABLE@", u32_table("DROP_OFF", offsets))
    text = text.replace("@SYNTH_TABLE@", u32_table("DROP_SYNTH", synth_flags))
    return text


def build_bundles():
    modules_text = bc.assemble_compiler_modules(MODULES, root=ROOT)
    outs = []
    for group, upper, names in GROUPS:
        header = (
            "// test: run\n"
            "// timeout: 1200\n"
            "// stdout: OK drop elaboration %s (%d cases)\\n\n"
            "// Generated by tests/selfhost/drop/gen_drop_tests.py bundles; do not edit.\n"
            "// Differential: Axiom compiler/mir/drop.ax vs C ax_mir_drop_elaborate (fixtures/*.drop.mir)\n"
            "// and the Axiom MIR builder vs `axiom0 inspect --emit=mir` (fixtures/*.pre.mir).\n\n"
        ) % (upper, len(names))
        text = header + PRELUDE + "\n" + modules_text + "\n" + main_module(upper, names)
        out = os.path.join(HERE, "qa_drop_%s.ax" % group)
        outs.append((out, text))
    return outs


def cmd_bundles(args):
    check_mode = "--check" in args
    rc = bc.write_or_check_bundles(build_bundles(), check_mode, root=ROOT)
    if rc != 0:
        raise SystemExit(rc)


COMMANDS = {
    "goldens": cmd_goldens,
    "bundles": cmd_bundles,
    "check": cmd_check,
    "bless-synth": cmd_bless_synth,
}


def main():
    args = sys.argv[1:]
    if not args or args == ["--check"]:
        cmd_bundles(args)
        return 0
    if args[0] == "check" and "--oracle" not in args:
        cmd_bundles(["--check"])
        return 0
    if args[0] not in COMMANDS:
        print(__doc__)
        return 2
    COMMANDS[args[0]](args[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
