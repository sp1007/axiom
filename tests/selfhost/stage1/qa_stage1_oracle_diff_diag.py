#!/usr/bin/env python3
"""Adversarial boundary test for T436 (stage1_oracle failure diagnostics & driver bundle freshness)."""

import io
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stage1_oracle as oracle


def test_canonical_json_and_text_diff():
    # Empty output (axiom0 on clean file) vs explicit 0-error JSON (axiomc1 on clean file)
    c_empty = oracle.canonical_json_diag((0, b"", b""))
    c_explicit = oracle.canonical_json_diag(
        (0, b"", b'{"schema": 1, "errors": 0, "warnings": 0, "diagnostics": []}\n')
    )
    assert c_empty == (0, b"", 1, 0, 0, []), f"unexpected c_empty: {c_empty!r}"
    assert c_empty == c_explicit, f"clean JSON normalization mismatch: {c_empty!r} vs {c_explicit!r}"

    # Diagnostic sorting and id stripping
    raw_a = b"""{
      "schema": 1,
      "errors": 2,
      "warnings": 0,
      "diagnostics": [
        {"id": 99, "code": "E2", "message": "second", "primary": {"start": 20, "end": 25}},
        {"id": 1, "code": "E1", "message": "first", "primary": {"start": 5, "end": 8}}
      ]
    }"""
    raw_b = b"""{
      "schema": 1,
      "errors": 2,
      "warnings": 0,
      "diagnostics": [
        {"id": 42, "code": "E1", "message": "first", "primary": {"start": 5, "end": 8}},
        {"id": 7, "code": "E2", "message": "mutated second", "primary": {"start": 20, "end": 25}}
      ]
    }"""
    ca = oracle.canonical_json_diag((1, b"", raw_a))
    cb = oracle.canonical_json_diag((1, b"", raw_b))
    assert ca != cb, "divergent diagnostics must not compare equal"
    assert "id" not in ca[5][0] and ca[5][0]["code"] == "E1", f"unexpected sorted diags: {ca[5]!r}"

    diff_txt = oracle.format_text_diff(
        "stage0:tests/ui/lex/001.ax",
        oracle.format_canonical_diag(ca) + "\n",
        "axiomc1:tests/ui/lex/001.ax",
        oracle.format_canonical_diag(cb) + "\n",
    )
    assert "--- stage0:tests/ui/lex/001.ax" in diff_txt, diff_txt
    assert "+++ axiomc1:tests/ui/lex/001.ax" in diff_txt, diff_txt
    assert '-      "message": "second"' in diff_txt, diff_txt
    assert '+      "message": "mutated second"' in diff_txt, diff_txt


def _diag_run(code):
    doc = b'{"schema": 1, "errors": 1, "warnings": 0, "diagnostics": [{"code": "%s", "message": "m", "primary": {"start": 0, "end": 1}}]}\n' % code.encode()
    return (1, b"", doc)


def test_post_freeze_skip_rule(tmp):
    skip = oracle.stage0_reports_post_freeze
    # Only axiom0's own AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP marks a file as post-freeze.
    assert skip(_diag_run("AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP")), "bootstrap-unsupported must be skipped"
    assert not skip(_diag_run("AX_TYPE_MISMATCH")), "any other diagnostic must still be compared"
    assert not skip((0, b"", b"")), "clean output must still be compared"
    assert not skip((1, b"", b"not json")), "unparsable output must not be silently skipped"
    # A skipped file is mixed with others: still one flagged diagnostic is enough.
    mixed = b'{"diagnostics": [{"code": "AX_TYPE_MISMATCH"}, {"code": "AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP"}]}'
    assert skip((1, b"", mixed))

    # collect_sample refills from the next matching file and reports skipped / starved patterns.
    sroot = os.path.join(tmp, "sample_root")
    for d in ("a", "b"):
        os.makedirs(os.path.join(sroot, "tests", d), exist_ok=True)
    names_a = ["f1.ax", "f2.ax", "f3.ax", "f4.ax", "f5.ax"]
    for n in names_a:
        with open(os.path.join(sroot, "tests", "a", n), "w", encoding="utf-8", newline="\n") as f:
            f.write("// test: ui\n")
    with open(os.path.join(sroot, "tests", "b", "only.ax"), "w", encoding="utf-8", newline="\n") as f:
        f.write("// test: ui\n")
    bad = {"tests/a/f2.ax", "tests/b/only.ax"}
    skipped, starved = [], []
    got = oracle.collect_sample(
        sroot,
        ["tests/a/*.ax", "tests/b/*.ax"],
        per_pattern=3,
        accept=lambda rel: rel not in bad,
        skipped=skipped,
        starved=starved,
    )
    assert got == ["tests/a/f1.ax", "tests/a/f3.ax", "tests/a/f4.ax"], got
    assert skipped == ["tests/a/f2.ax", "tests/b/only.ax"], skipped
    assert starved == ["tests/b/*.ax"], starved
    # Without a filter the behaviour is unchanged (first three files).
    plain = oracle.collect_sample(sroot, ["tests/a/*.ax"], per_pattern=3)
    assert plain == ["tests/a/f1.ax", "tests/a/f2.ax", "tests/a/f3.ax"], plain


def test_bytes_diff_and_fail_step():
    # Equal-length byte divergence
    bdiff = oracle.format_bytes_diff(
        "axiomc1.obj", b"\x01\x02\x03\x00\xff", "stage2.obj", b"\x01\x02\x03\xfe\xff"
    )
    assert "axiomc1.obj len=5 vs stage2.obj len=5" in bdiff, bdiff
    assert "first diff at byte 0x3: axiomc1.obj=00ff vs stage2.obj=feff" in bdiff, bdiff

    # Length divergence with matching prefix
    ldiff = oracle.format_bytes_diff("a.exe", b"ABCD", "b.exe", b"ABCDEF")
    assert "a.exe len=4 vs b.exe len=6" in ldiff, ldiff
    assert "first diff at byte 0x4" in ldiff, ldiff

    # fail_step must write to both stdout and stderr and return 1
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = oracle.fail_step("step3:obj-bytes", ".obj bytes differ", bdiff)
    assert rc == 1, f"expected rc=1, got {rc}"
    out_val = out_buf.getvalue()
    err_val = err_buf.getvalue()
    assert out_val == err_val, f"stdout/stderr mismatch:\n{out_val!r}\nvs\n{err_val!r}"
    assert "FAIL [step3:obj-bytes]: .obj bytes differ" in err_val, err_val
    assert "first diff at byte 0x3" in err_val, err_val


def test_subprocess_failure_paths(root, tmp):
    oracle_py = os.path.join(HERE, "stage1_oracle.py")
    # 1. Bad CLI arg count -> exit 2 + stderr usage
    r_bad = subprocess.run([sys.executable, oracle_py], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert r_bad.returncode == 2, f"expected rc=2, got {r_bad.returncode}"
    assert b"usage: stage1_oracle.py" in r_bad.stderr, r_bad.stderr

    # 2. Missing stage0/compiler in isolated temp root -> step1:bootstrap fail on both stdout and stderr
    fake_root = os.path.join(tmp, "fake_root")
    os.makedirs(os.path.join(fake_root, "tools"), exist_ok=True)
    fake_boot = os.path.join(fake_root, "tools", "bootstrap.py")
    with open(fake_boot, "w", encoding="utf-8", newline="\n") as f:
        f.write('import sys\nsys.stderr.write("simulated bootstrap failure\\n")\nsys.exit(1)\n')
    r_s1 = subprocess.run(
        [sys.executable, oracle_py, os.path.join(fake_root, "missing_c.exe"), os.path.join(tmp, "s1_tmp"), fake_root],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert r_s1.returncode == 1, f"expected rc=1, got {r_s1.returncode}"
    assert b"FAIL [step1:bootstrap]:" in r_s1.stdout, r_s1.stdout
    assert b"FAIL [step1:bootstrap]:" in r_s1.stderr, r_s1.stderr
    assert b"simulated bootstrap failure" in r_s1.stderr, r_s1.stderr


def test_driver_generator_and_lf(root):
    gen_py = os.path.join(root, "tests", "selfhost", "driver", "gen_driver_tests.py")
    res = subprocess.run(
        [sys.executable, gen_py, "--check"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert res.returncode == 0, f"gen_driver_tests.py --check failed: {res.stdout!r} {res.stderr!r}"
    assert b"up to date" in res.stdout, res.stdout

    for rel in (
        "tests/selfhost/driver/gen_driver_tests.py",
        "tests/selfhost/driver/qa_driver_full_interp.ax",
        "tests/selfhost/driver/qa_driver_full_native.ax",
        "tests/selfhost/stage1/stage1_oracle.py",
    ):
        p = os.path.join(root, *rel.split("/"))
        with open(p, "rb") as f:
            data = f.read()
        assert b"\r" not in data, f"CR byte found in {rel}"


def main():
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    tmp = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(HERE, "_tmp_diag")
    os.makedirs(tmp, exist_ok=True)
    test_canonical_json_and_text_diff()
    test_post_freeze_skip_rule(tmp)
    test_bytes_diff_and_fail_step()
    test_subprocess_failure_paths(root, tmp)
    test_driver_generator_and_lf(root)
    print("QA-STAGE1-ORACLE-DIAG OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
