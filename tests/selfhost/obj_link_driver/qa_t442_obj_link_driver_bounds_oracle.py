#!/usr/bin/env python3
"""Adversarial QA boundary oracle for T442:
1. Verifies both selfhost bundle generators (`gen_obj_link_driver_tests.py --check` and
   `gen_driver_tests.py --check`) exit 0 and report all 8 bundles up to date.
2. Verifies all 8 bundles across `tests/selfhost/driver/qa_driver_*.ax` (6) and
   `tests/selfhost/obj_link_driver/qa_obj_link_driver_*.ax` (2) have 0 CR bytes, declare
   `// test: run` + exact `// stdout: OK <bundle>\\n` in the directive header, and emit
   `print("OK <bundle>\\n");` right before returning `0` in `pub fn main() -> i32`.
3. Extracts `BLOBS` from `qa_obj_link_driver_smoke.ax` and `qa_obj_link_driver_diff.ax` via
   `extract_blobs_from_bundle`, verifies `main_42.obj` is the T431-pruned 336-byte COFF object
   (with `.axmeta`, `0` dead `std.` symbols) and `main_42.exe` is the 2,048-byte PE32+ image,
   and cross-checks against live `{compiler}` builds of single-file (`main_42.ax`) and multi-file
   package (`tests/modules/hello/src/main.ax`) targets.
4. Verifies `_workspaces/baseline-failures.txt` has 0 active baseline test IDs and no temporary
   `build/tmp_obj_link_driver_*` or `_gen_ref*` artifacts remain on disk.
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_DEFAULT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT_DEFAULT, "tests", "selfhost", "driver"))
sys.path.insert(0, HERE)

import gen_obj_link_driver_tests as gen  # noqa: E402

DRIVER_MERGED_BUNDLES = [
    ("tests/selfhost/driver/qa_driver_light.ax", ["qa_driver_cli_and_project", "qa_driver_boundary_edges"]),
    ("tests/selfhost/driver/qa_driver_full_interp.ax", ["qa_driver_inspect_diff_a", "qa_driver_commands_a"]),
    ("tests/selfhost/driver/qa_driver_full_native.ax", ["qa_driver_inspect_diff_b", "qa_driver_commands_b"]),
]

OBJ_LINK_DRIVER_BUNDLES = [
    "tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax",
    "tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax",
]


def fail(msg):
    sys.stderr.write("FAIL: %s\n" % msg)
    raise SystemExit(1)


def check_generators(root):
    for rel_script in (
        "tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py",
        "tests/selfhost/driver/gen_driver_tests.py",
    ):
        script_path = os.path.join(root, rel_script)
        proc = subprocess.run(
            [sys.executable, script_path, "--check"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            fail(
                "%s --check exited with %d: %s"
                % (rel_script, proc.returncode, proc.stderr.decode("utf-8", "replace"))
            )
        out_text = proc.stdout.decode("utf-8", "replace")
        if "up to date" not in out_text:
            fail("%s --check did not print 'up to date': %r" % (rel_script, out_text))


def check_bundle_headers_and_stdout(root):
    for rel, members in DRIVER_MERGED_BUNDLES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            fail("missing merged driver bundle: %s" % rel)
        with open(path, "rb") as f:
            raw = f.read()
        if b"\r" in raw:
            fail("CR byte found in %s" % rel)
        head_lines = raw[:2048].decode("utf-8", "replace").split("\n")
        leading_comments = []
        for ln in head_lines:
            if not ln.startswith("//"):
                break
            leading_comments.append(ln)
        if "// test: run" not in leading_comments:
            fail("%s missing '// test: run' in header" % rel)
        tail_text = raw[-4096:].decode("utf-8", "replace")
        for member in members:
            if ("// stdout: OK %s\\n" % member) not in leading_comments:
                fail("%s missing '// stdout: OK %s\\n' in header (got %r)" % (rel, member, leading_comments))
            if ('print("OK %s\\n");' % member) not in tail_text:
                fail("%s missing print(\"OK %s\\n\"); in merged main()" % (rel, member))

    for rel in OBJ_LINK_DRIVER_BUNDLES:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            fail("missing bundle: %s" % rel)
        with open(path, "rb") as f:
            raw = f.read()
        if b"\r" in raw:
            fail("CR byte found in %s" % rel)
        base = os.path.splitext(os.path.basename(rel))[0]
        allowed_tags = {base}
        if base.startswith("qa_"):
            allowed_tags.add(base[3:])
        head_lines = raw[:2048].decode("utf-8", "replace").split("\n")
        leading_comments = []
        for ln in head_lines:
            if not ln.startswith("//"):
                break
            leading_comments.append(ln)
        if "// test: run" not in leading_comments:
            fail("%s missing '// test: run' in header" % rel)
        matched_tag = None
        for cand_tag in allowed_tags:
            if ("// stdout: OK %s\\n" % cand_tag) in leading_comments:
                matched_tag = cand_tag
                break
        if matched_tag is None:
            fail("%s missing exact '// stdout: OK <bundle>\\n' in header (got %r)" % (rel, leading_comments))
        tail_text = raw[-4096:].decode("utf-8", "replace")
        expected_print = 'print("OK %s\\n");\n    0\n}' % matched_tag
        if expected_print not in tail_text:
            fail("%s missing final print pattern %r in main()" % (rel, expected_print))

    for rel in OBJ_LINK_DRIVER_BUNDLES:
        path = os.path.join(root, rel)
        with open(path, "rb") as f:
            tail_text = f.read()[-16384:].decode("utf-8", "replace")
        for needle in (
            "let is_pkg = k == 4 || k == 5;",
            "let write_disk = is_pkg && !emit_obj;",
            "if !is_pkg && !handoff_matches(false, case_blob(k, 2), case_blob(k, 1))",
            "if !is_pkg && !handoff_matches(true, case_blob(k, 5), case_blob(k, 1))",
            "if !is_pkg && !pipeline_handoff_matches(k)",
        ):
            if needle not in tail_text:
                fail("%s missing expected multi-module guard %r" % (rel, needle))


def check_blobs_and_live_compiler(compiler, tmp, root):
    smoke_path = os.path.join(root, "tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax")
    diff_path = os.path.join(root, "tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax")
    smoke_blobs = gen.drv.bc.extract_blobs_from_bundle(smoke_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
    diff_blobs = gen.drv.bc.extract_blobs_from_bundle(diff_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")

    if len(smoke_blobs) != 13 + 6 * len(gen.DIFF_CORPUS_SMOKE):
        fail("unexpected smoke blob count: %d" % len(smoke_blobs))
    if len(diff_blobs) != 13 + 6 * len(gen.DIFF_CORPUS_FULL):
        fail("unexpected diff blob count: %d" % len(diff_blobs))

    # Fixed blobs 0..12 and case 0 (main_42.ax, indices 13..18) must match identically between smoke and diff.
    for idx in range(19):
        if smoke_blobs[idx] != diff_blobs[idx]:
            fail("smoke_blobs[%d] != diff_blobs[%d] (lens %d vs %d)" % (idx, idx, len(smoke_blobs[idx]), len(diff_blobs[idx])))

    if smoke_blobs[8] != b"build/tmp_obj_link_driver_" or smoke_blobs[9] != b".exe":
        fail("unexpected temp-path blobs[8..9]: %r, %r" % (smoke_blobs[8], smoke_blobs[9]))

    main42_obj_o0 = diff_blobs[14]
    main42_exe_o0 = diff_blobs[15]
    main42_obj_o1 = diff_blobs[16]
    main42_exe_o1 = diff_blobs[17]
    main42_exe_sr = diff_blobs[18]

    # Verify T431 dead-<std> pruning and T067 .axmeta presence in main_42.obj.
    if len(main42_obj_o0) != 336:
        fail("expected pruned main_42.obj size 336, got %d" % len(main42_obj_o0))
    if main42_obj_o0[:2] != b"\x64\x86":
        fail("main_42.obj does not start with IMAGE_FILE_MACHINE_AMD64 (0x8664)")
    if b".axmeta" not in main42_obj_o0 or b"main" not in main42_obj_o0:
        fail("main_42.obj missing .axmeta or main symbol")
    if b"std." in main42_obj_o0:
        fail("main_42.obj contains unpruned std.* symbol bytes")

    if len(main42_exe_o0) != 2048 or main42_exe_o0[:2] != b"MZ":
        fail("expected 2048-byte MZ image for main_42.exe, got len=%d magic=%r" % (len(main42_exe_o0), main42_exe_o0[:2]))

    # Cross-check live compiler outputs against the embedded blobs for case 0 (main_42.ax) and case 4 (hello package).
    os.makedirs(tmp, exist_ok=True)
    live_checks = [
        (["--emit=obj"], "tests/mc/frame/main_42.ax", "m42_o0.obj", main42_obj_o0),
        ([], "tests/mc/frame/main_42.ax", "m42_o0.exe", main42_exe_o0),
        (["--emit=obj", "-O1"], "tests/mc/frame/main_42.ax", "m42_o1.obj", main42_obj_o1),
        (["-O1"], "tests/mc/frame/main_42.ax", "m42_o1.exe", main42_exe_o1),
        (["--stack-reserve=2097152"], "tests/mc/frame/main_42.ax", "m42_sr.exe", main42_exe_sr),
        ([], "tests/modules/hello/src/main.ax", "hello_o0.exe", diff_blobs[13 + 6 * 4 + 2]),
    ]
    for flags, rel_src, out_name, expected_bytes in live_checks:
        out_path = os.path.join(tmp, out_name)
        if os.path.exists(out_path):
            os.remove(out_path)
        proc = subprocess.run(
            [compiler, "build"] + flags + ["-o", out_path, rel_src],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode != 0:
            fail("live compiler build %s %r failed (rc=%d)" % (rel_src, flags, proc.returncode))
        with open(out_path, "rb") as f:
            got = f.read()
        os.remove(out_path)
        if got != expected_bytes:
            fail(
                "live compiler output for %s %r differs from bundle blob (got %d bytes, expected %d bytes)"
                % (rel_src, flags, len(got), len(expected_bytes))
            )


def check_baseline_and_temp_cleanup(root):
    baseline_path = os.path.join(root, "_workspaces", "baseline-failures.txt")
    if os.path.isfile(baseline_path):
        with open(baseline_path, "rb") as f:
            raw = f.read()
        if b"\r" in raw:
            fail("CR byte found in _workspaces/baseline-failures.txt")
        active = [
            ln.strip()
            for ln in raw.decode("utf-8", "replace").split("\n")
            if ln.strip() and not ln.lstrip().startswith("#")
        ]
        if active:
            fail("_workspaces/baseline-failures.txt still has active lines: %r" % active)

    leftovers = (
        glob.glob(os.path.join(root, "build", "tmp_obj_link_driver_*"))
        + glob.glob(os.path.join(root, "tests", "selfhost", "obj_link_driver", "_gen_ref*"))
    )
    if leftovers:
        fail("leftover temporary artifacts found: %r" % leftovers)


def main():
    if len(sys.argv) < 4:
        fail("usage: qa_t442_obj_link_driver_bounds_oracle.py <compiler> <tmp> <root>")
    compiler = os.path.abspath(sys.argv[1])
    tmp = os.path.abspath(sys.argv[2])
    root = os.path.abspath(sys.argv[3])

    check_generators(root)
    check_bundle_headers_and_stdout(root)
    check_blobs_and_live_compiler(compiler, tmp, root)
    check_baseline_and_temp_cleanup(root)
    print("T442-BOUNDS ok bundles=8 smoke_blobs=19 diff_blobs=55 main42_obj=336 main42_exe=2048")
    return 0


if __name__ == "__main__":
    sys.exit(main())
