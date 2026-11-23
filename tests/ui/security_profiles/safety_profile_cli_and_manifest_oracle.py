#!/usr/bin/env python3
"""End-to-end CLI, axiom.toml, module-hierarchy, native sandbox build, and --json oracle for T517 (SPEC-53)."""

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

    sandbox_ok = str(root_dir / "tests" / "ui" / "security_profiles" / "sandbox_capability_ok.ax")
    spec53_neg = str(root_dir / "tests" / "ui" / "security_profiles" / "spec53_canonical_neg.ax")
    sandbox_amb = str(root_dir / "tests" / "ui" / "security_profiles" / "sandbox_ambient_authority_neg.ax")
    comptime_neg = str(root_dir / "tests" / "ui" / "security_profiles" / "comptime_ambient_isolation_neg.ax")

    # 1. CLI invalid --safety-profile exits 2 with AX_DRIVER_INVALID_SAFETY_PROFILE
    for flag_args in (["--safety-profile", "bogus"], ["--safety-profile=unknown_mode"]):
        res = run_cmd([compiler, "check", "--std-root", std_root] + flag_args + [sandbox_ok])
        assert_true(res.returncode == 2, f"expected exit 2 for {flag_args}, got {res.returncode}: {res.stderr}")
        assert_true(
            "AX_DRIVER_INVALID_SAFETY_PROFILE" in res.stderr,
            f"expected AX_DRIVER_INVALID_SAFETY_PROFILE in stderr, got: {res.stderr}",
        )

    # 2. axiom.toml [security] invalid safety_profile exits 2 with AX_DRIVER_INVALID_SAFETY_PROFILE
    bad_pkg = tmp_dir / "bad_sec_pkg"
    (bad_pkg / "src").mkdir(parents=True, exist_ok=True)
    (bad_pkg / "axiom.toml").write_text(
        '[package]\nname = "bad_sec_pkg"\nversion = "0.1.0"\n\n[security]\nsafety_profile = "not_a_mode"\n',
        encoding="utf-8",
    )
    (bad_pkg / "src" / "main.ax").write_text(
        "module bad_sec_pkg\npub fn main() -> i32 { 0i32 }\n",
        encoding="utf-8",
    )
    res_pkg = run_cmd([compiler, "check", "--std-root", std_root, "--json", str(bad_pkg / "src" / "main.ax")])
    assert_true(res_pkg.returncode == 2, f"expected exit 2 for invalid manifest safety_profile, got {res_pkg.returncode}: {res_pkg.stderr}")
    doc_pkg = json.loads(res_pkg.stderr)
    codes_pkg = [d.get("code") for d in doc_pkg.get("diagnostics", [])]
    assert_true("AX_DRIVER_INVALID_SAFETY_PROFILE" in codes_pkg, f"expected AX_DRIVER_INVALID_SAFETY_PROFILE in JSON: {doc_pkg}")

    # 3. axiom.toml [security] safety_profile = "sandbox" enforces sandbox across package,
    #    and explicit CLI `--safety-profile system` overrides manifest setting.
    sbx_pkg = tmp_dir / "sbx_pkg"
    (sbx_pkg / "src").mkdir(parents=True, exist_ok=True)
    (sbx_pkg / "axiom.toml").write_text(
        '[package]\nname = "sbx_pkg"\nversion = "0.1.0"\n\n[security]\nsafety_profile = "sandbox"\n',
        encoding="utf-8",
    )
    (sbx_pkg / "src" / "main.ax").write_text(
        'module sbx_pkg\nuse std.io.File\npub fn main() -> i32 {\n    let _ = File.open("x.txt");\n    unsafe { let x: i32 = 1i32; let _ = x; }\n    0i32\n}\n',
        encoding="utf-8",
    )
    res_sbx = run_cmd([compiler, "check", "--std-root", std_root, "--json", str(sbx_pkg / "src" / "main.ax")])
    assert_true(res_sbx.returncode == 1, f"expected exit 1 under manifest sandbox, got {res_sbx.returncode}: {res_sbx.stderr}")
    doc_sbx = json.loads(res_sbx.stderr)
    sbx_codes = {d.get("code") for d in doc_sbx.get("diagnostics", [])}
    assert_true("AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN" in sbx_codes, f"missing ambient diag: {sbx_codes}")
    assert_true("AX_SEC_UNSAFE_FORBIDDEN" in sbx_codes, f"missing unsafe diag: {sbx_codes}")

    res_override = run_cmd(
        [compiler, "check", "--std-root", std_root, "--safety-profile", "system", str(sbx_pkg / "src" / "main.ax")]
    )
    assert_true(
        res_override.returncode == 0,
        f"expected CLI --safety-profile system to override manifest sandbox, got {res_override.returncode}: {res_override.stderr}",
    )

    # 4. axiom.toml [security] forbid_unsafe = true + multi-file @forbid_unsafe module hierarchy inheritance:
    #    `@forbid_unsafe module hier_pkg.auth` locks `hier_pkg.auth.sub` (including rejecting `@allow_unsafe`),
    #    while sibling `hier_pkg.sys` stays in `system` mode!
    hier_pkg = tmp_dir / "hier_pkg"
    (hier_pkg / "src" / "auth").mkdir(parents=True, exist_ok=True)
    (hier_pkg / "axiom.toml").write_text(
        '[package]\nname = "hier_pkg"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (hier_pkg / "src" / "main.ax").write_text(
        "module hier_pkg\nuse hier_pkg.auth.auth_entry\nuse hier_pkg.sys.sys_ok\npub fn main() -> i32 { auth_entry() + sys_ok() }\n",
        encoding="utf-8",
    )
    (hier_pkg / "src" / "sys.ax").write_text(
        "module hier_pkg.sys\npub fn sys_ok() -> i32 { unsafe { 10i32 } }\n",
        encoding="utf-8",
    )
    (hier_pkg / "src" / "auth" / "mod.ax").write_text(
        "@forbid_unsafe module hier_pkg.auth\nuse hier_pkg.auth.sub.sub_fn\npub fn auth_entry() -> i32 { sub_fn() }\n",
        encoding="utf-8",
    )
    (hier_pkg / "src" / "auth" / "sub.ax").write_text(
        "@allow_unsafe\nmodule hier_pkg.auth.sub\npub fn sub_fn() -> i32 { unsafe { 5i32 } }\n",
        encoding="utf-8",
    )
    res_hier = run_cmd([compiler, "check", "--std-root", std_root, "--json", str(hier_pkg / "src" / "main.ax")])
    assert_true(res_hier.returncode == 1, f"expected exit 1 on submodule escalation, got {res_hier.returncode}: {res_hier.stderr}")
    doc_hier = json.loads(res_hier.stderr)
    hier_diags = doc_hier.get("diagnostics", [])
    hier_codes = {d.get("code") for d in hier_diags}
    assert_true("AX_SEC_CONFLICTING_SAFETY_POLICY" in hier_codes, f"missing conflicting policy on child module: {hier_diags}")
    assert_true("AX_SEC_UNSAFE_FORBIDDEN" in hier_codes, f"missing inherited unsafe_forbidden on child module: {hier_diags}")
    assert_true(
        all("sys.ax" not in ((d.get("primary") or {}).get("file") or "") for d in hier_diags),
        f"sibling module hier_pkg.sys must remain unaffected: {hier_diags}",
    )

    # Also check manifest `forbid_unsafe = true` locks `hier_pkg.sys` too!
    (hier_pkg / "axiom.toml").write_text(
        '[package]\nname = "hier_pkg"\nversion = "0.1.0"\n\n[security]\nforbid_unsafe = true\n',
        encoding="utf-8",
    )
    res_pkg_fu = run_cmd([compiler, "check", "--std-root", std_root, "--json", str(hier_pkg / "src" / "main.ax")])
    doc_pkg_fu = json.loads(res_pkg_fu.stderr)
    assert_true(
        any("sys.ax" in ((d.get("primary") or {}).get("file") or "") and d.get("code") == "AX_SEC_UNSAFE_FORBIDDEN"
            for d in doc_pkg_fu.get("diagnostics", [])),
        f"expected manifest forbid_unsafe = true to lock sys.ax: {doc_pkg_fu}",
    )

    # 5. Structured --json diagnostic payload keys (SPEC-53 AXS-SEC-051..052)
    res_spec = run_cmd([compiler, "check", "--std-root", std_root, "--safety-profile", "sandbox", "--json", spec53_neg])
    assert_true(res_spec.returncode == 1, f"expected exit 1 on spec53_canonical_neg.ax, got {res_spec.returncode}")
    doc_spec = json.loads(res_spec.stderr)
    by_code = {d.get("code"): d for d in doc_spec.get("diagnostics", [])}
    for req_code in ("AX_SEC_UNSAFE_FORBIDDEN", "AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN", "AX_SEC_CAPABILITY_FORGERY"):
        assert_true(req_code in by_code, f"missing {req_code} in {list(by_code.keys())}")

    assert_true(by_code["AX_SEC_UNSAFE_FORBIDDEN"].get("data", {}).get("construct") == "unsafe_block", f"bad unsafe data: {by_code['AX_SEC_UNSAFE_FORBIDDEN']}")
    amb_data = by_code["AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN"].get("data", {})
    assert_true(amb_data.get("required_cap") == "FsCap" and amb_data.get("profile") == "sandbox", f"bad ambient data: {amb_data}")
    forg_data = by_code["AX_SEC_CAPABILITY_FORGERY"].get("data", {})
    assert_true("source" in forg_data and "target" in forg_data, f"bad forgery data: {forg_data}")

    # Verify transitive call-chain note on sandbox_ambient_authority_neg.ax
    res_amb = run_cmd([compiler, "check", "--std-root", std_root, "--safety-profile", "sandbox", "--json", sandbox_amb])
    doc_amb = json.loads(res_amb.stderr)
    assert_true(
        any(
            d.get("code") == "AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN"
            and any("call chain:" in n and "indirect_leaf" in n for n in d.get("notes", []))
            for d in doc_amb.get("diagnostics", [])
        ),
        f"expected transitive call chain note in sandbox_ambient_authority_neg.ax: {doc_amb}",
    )

    # Verify comptime isolation structured reason fields (`ASEC-24` & `ASEC-25`)
    res_ct = run_cmd([compiler, "check", "--std-root", std_root, "--json", comptime_neg])
    doc_ct = json.loads(res_ct.stderr)
    ct_reasons = {d.get("data", {}).get("reason") for d in doc_ct.get("diagnostics", []) if d.get("code") == "AX_SEC_AMBIENT_AUTHORITY_FORBIDDEN"}
    assert_true("comptime_to_runtime_authority" in ct_reasons, f"missing ASEC-24 reason in {ct_reasons}")
    assert_true("runtime_to_comptime_authority" in ct_reasons, f"missing ASEC-25 reason in {ct_reasons}")

    # 6. Native build & run under `--safety-profile sandbox` with deterministic non-zero exit code 73
    sbx_exe_src = tmp_dir / "sandbox_native_bin.ax"
    sbx_exe_out = tmp_dir / "sandbox_native_bin.exe"
    sbx_exe_src.write_text(
        "module sandbox_native_bin\n"
        "use std.time.Duration\n"
        "struct FsCap { quota: i32 }\n"
        "fn compute_scoped(cap: view<FsCap>, d: Duration) -> i32 {\n"
        "    cap.quota + (d.as_secs() as i32)\n"
        "}\n"
        "pub fn main() -> i32 {\n"
        "    let c = FsCap { quota: 43i32 };\n"
        "    compute_scoped(view(c), Duration.from_secs(30u64))\n"
        "}\n",
        encoding="utf-8",
    )
    res_build = run_cmd(
        [compiler, "build", "--std-root", std_root, "--safety-profile", "sandbox", "-O1", "-o", str(sbx_exe_out), str(sbx_exe_src)]
    )
    assert_true(res_build.returncode == 0, f"sandbox native build failed ({res_build.returncode}): {res_build.stderr}")
    res_exec = run_cmd([str(sbx_exe_out)])
    assert_true(res_exec.returncode == 73, f"expected native sandbox binary exit 73, got {res_exec.returncode}")

    print("T517-SAFETY-PROFILE-CLI-MANIFEST-JSON-OK")


if __name__ == "__main__":
    main()
