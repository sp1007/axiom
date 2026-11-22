#!/usr/bin/env python3
"""End-to-end CLI, axiom.toml, and structured --json diagnostic oracle for T512 (SPEC-52)."""

import json
import pathlib
import subprocess
import sys


def run_cmd(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def assert_true(cond, msg):
    if not cond:
        raise AssertionError(msg)


def main():
    compiler = sys.argv[1]
    tmp_dir = pathlib.Path(sys.argv[2])
    root_dir = pathlib.Path(sys.argv[3])
    std_root = str(root_dir / "std")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    valid_sys = str(root_dir / "tests" / "ui" / "freestanding" / "valid_system_profile.ax")

    # 1. CLI unknown --profile exits 2 with AX_DRIVER_INVALID_PROFILE
    for flag_args in (["--profile", "bogus"], ["--profile=unknown_prof"]):
        res = run_cmd([compiler, "check", "--std-root", std_root] + flag_args + [valid_sys])
        assert_true(res.returncode == 2, f"expected exit 2 for {flag_args}, got {res.returncode}: {res.stderr}")
        assert_true(
            "AX_DRIVER_INVALID_PROFILE" in res.stderr,
            f"expected AX_DRIVER_INVALID_PROFILE in stderr, got: {res.stderr}",
        )

    # 2. axiom.toml [package] / [target] invalid profile exits 2 with AX_DRIVER_INVALID_PROFILE
    bad_pkg = tmp_dir / "bad_prof_pkg"
    (bad_pkg / "src").mkdir(parents=True, exist_ok=True)
    (bad_pkg / "axiom.toml").write_text(
        '[package]\nname = "bad_prof_pkg"\nversion = "0.1.0"\n\n[target]\nprofile = "not_a_profile"\n',
        encoding="utf-8",
    )
    (bad_pkg / "src" / "main.ax").write_text(
        "module bad_prof_pkg\npub fn main() -> i32 { 0 }\n",
        encoding="utf-8",
    )
    res_pkg = run_cmd([compiler, "check", "--std-root", std_root, "--json", str(bad_pkg / "src" / "main.ax")])
    assert_true(res_pkg.returncode == 2, f"expected exit 2 for invalid manifest profile, got {res_pkg.returncode}: {res_pkg.stderr}")
    doc_pkg = json.loads(res_pkg.stderr)
    codes_pkg = [d.get("code") for d in doc_pkg.get("diagnostics", [])]
    assert_true("AX_DRIVER_INVALID_PROFILE" in codes_pkg, f"expected AX_DRIVER_INVALID_PROFILE in JSON: {doc_pkg}")

    # 3. Structured --json data & call-chain notes for SPEC-52 capability & interrupt diagnostics
    spec_neg = str(root_dir / "tests" / "ui" / "freestanding" / "spec52_bad_freestanding.ax")
    res_neg = run_cmd([compiler, "check", "--std-root", std_root, "--profile", "freestanding", "--json", spec_neg])
    assert_true(res_neg.returncode == 1, f"expected exit 1 on spec52_bad_freestanding.ax, got {res_neg.returncode}: {res_neg.stderr}")
    doc_neg = json.loads(res_neg.stderr)
    diags_neg = doc_neg.get("diagnostics", [])
    by_code = {d.get("code"): d for d in diags_neg}
    for req_code in (
        "AX_NAME_FREESTANDING_FORBIDDEN_IMPORT",
        "AX_TYPE_ENTRY_SIGNATURE",
        "AX_UNSAFE_INTERRUPT_FORBIDDEN_OP",
        "AX_TYPE_INVALID_NAKED_FN",
    ):
        assert_true(req_code in by_code, f"missing {req_code} in {list(by_code.keys())}")

    imp_d = by_code["AX_NAME_FREESTANDING_FORBIDDEN_IMPORT"]
    assert_true(imp_d.get("data", {}).get("module") == "std.fs", f"bad import data: {imp_d}")
    assert_true(imp_d.get("data", {}).get("profile") == "freestanding", f"bad import profile: {imp_d}")

    irq_d = by_code["AX_UNSAFE_INTERRUPT_FORBIDDEN_OP"]
    assert_true(irq_d.get("data", {}).get("capability") == "heap_alloc", f"bad irq capability: {irq_d}")
    assert_true(
        any("call chain: bad_irq_handler -> box_new" in n for n in irq_d.get("notes", [])),
        f"missing call chain note on irq diag: {irq_d}",
    )

    cap_neg = str(root_dir / "tests" / "ui" / "freestanding" / "profile_forbidden_caps.ax")
    res_cap = run_cmd([compiler, "check", "--std-root", std_root, "--profile", "freestanding", "--json", cap_neg])
    assert_true(res_cap.returncode == 1, f"expected exit 1 on profile_forbidden_caps.ax, got {res_cap.returncode}")
    doc_cap = json.loads(res_cap.stderr)
    cap_diags = [d for d in doc_cap.get("diagnostics", []) if d.get("code") == "AX_DRIVER_PROFILE_FORBIDDEN_CAP"]
    assert_true(len(cap_diags) >= 5, f"expected >= 5 AX_DRIVER_PROFILE_FORBIDDEN_CAP diags, got {cap_diags}")
    assert_true(
        any(
            d.get("data", {}).get("capability") == "heap_alloc"
            and any("call chain: _start -> alloc_indirect_mid -> alloc_indirect_leaf -> box_new" in n for n in d.get("notes", []))
            for d in cap_diags
        ),
        f"missing transitive heap_alloc call-chain note in {cap_diags}",
    )

    print("T512-PROFILE-CLI-MANIFEST-JSON-OK")


if __name__ == "__main__":
    main()
