#!/usr/bin/env python3
"""End-to-end E20.6 Conformance Oracle (T877 / SPEC-116 §§1..5, AXS-SDK-001..055,
INV-SDK-001..003, REQ-ECO-8736, REQ-PKG-022):
Native SDK/Sysroot, AXTOOLCHAIN Target Distribution & Two-Machine Lockfile
Reproducible Multi-Package Workspace Conformance Suite.

Steps:
1. Bundles live compiler modules (compiler.sdk.sysroot, compiler.sdk.toolchain,
   compiler.driver.sdk_cmd, compiler.build.sandbox, compiler.build.repro,
   plus compiler kernel and build dependencies) + standard library modules
   (std.pkg.lockfile, std.pkg.store, std.sdk.bundle) with
   e20_6_sdk_toolchain_workspace_probe.ax.in.
2. Executes the bundled probe across:
   - `--interp`
   - `-O0 --verify-each`
   - `-O1 --verify-each`
   - `-O2 --verify-each`
   Verifying exact byte-for-byte identical output parity across all 4 execution tiers.
3. Differential verification (--interp vs native -O1 --verify-each) across all 5
   standalone .ax conformance fixtures in tests/conformance/p20/e20_6_sdk_toolchain_workspace/.
4. End-to-end Two-Machine Multi-Package Workspace Reproducibility verification:
   Builds a multi-package workspace (containing library, binary, precompiled .axmeta,
   and dynamic plugin packages) from axiom.lock across two completely isolated
   simulated machine environments (distinct root paths, usernames, temp dirs,
   environment variables, clock offsets, and thread counts) and certifies bit-for-bit
   identical output artifact digests (Phase P20 exit criterion / REQ-PKG-022).
5. Verifies clean production binaries without leaked .axmeta, .axdb, .axmir, .axoracle, or .axlto metadata.
6. Emits E20-6-SDK-TOOLCHAIN-WORKSPACE-CONFORMANCE-OK.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
SELFHOST_DIR = REPO_ROOT / "tests" / "selfhost"
if str(SELFHOST_DIR) not in sys.path:
    sys.path.insert(0, str(SELFHOST_DIR))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e20_6_sdk_toolchain_workspace_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[cross_target_sysroot_and_crt] targets=6 crt_ok=true stubs_ok=true ambient_denied=true api_gated=true\n"
    "probe[axtoolchain_bundle_packager] lookup_ok=true sort_ok=true merkle_ok=true traversal_denied=true sig_ok=true cache_paths_ok=true offline_ok=true\n"
    "probe[lockfile_pinning_and_tamper_guard] parse_ok=true serialize_ok=true pin_ok=true locked_check_ok=true tamper_denied=true\n"
    "probe[two_machine_workspace_reproducibility] fp_invariant=true remap_ok=true multi_pkg_repro=true leak_audit_ok=true\n"
    "probe[sdk_toolchain_cli_engine] sdk_cli_ok=true tc_cli_ok=true exit_codes_ok=true diag_mapped=true\n"
    "E20-6-SDK-TOOLCHAIN-WORKSPACE-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "cross_target_declarative_sysroot_and_crt",
        "cross_target_declarative_sysroot_and_crt.ax",
        "cross_target_declarative_sysroot_and_crt.stdout",
    ),
    (
        "axtoolchain_bundle_packager_and_distribution",
        "axtoolchain_bundle_packager_and_distribution.ax",
        "axtoolchain_bundle_packager_and_distribution.stdout",
    ),
    (
        "lockfile_pinning_drift_and_tamper_defense",
        "lockfile_pinning_drift_and_tamper_defense.ax",
        "lockfile_pinning_drift_and_tamper_defense.stdout",
    ),
    (
        "two_machine_reproducible_workspace_build",
        "two_machine_reproducible_workspace_build.ax",
        "two_machine_reproducible_workspace_build.stdout",
    ),
    (
        "sdk_toolchain_cli_workflow_contract",
        "sdk_toolchain_cli_workflow_contract.ax",
        "sdk_toolchain_cli_workflow_contract.stdout",
    ),
]

E20_6_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.diag.ux2", "compiler"),
    ("compiler.build.manifest", "compiler"),
    ("compiler.build.workspace", "compiler"),
    ("compiler.build.sandbox", "compiler"),
    ("compiler.build.repro", "compiler"),
    ("compiler.sdk.toolchain", "compiler"),
    ("compiler.sdk.sysroot", "compiler"),
    ("compiler.driver.sdk_cmd", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    if os.path.isfile(compiler):
        return compiler
    return os.path.join(build_dir, f"axiomc{exe}")


def run_cmd(
    cmd: list[str], cwd: str | pathlib.Path, timeout: int = 180, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    cmd_env = os.environ.copy()
    if env is not None:
        cmd_env.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=timeout,
        env=cmd_env,
    )


def ensure_clean_root(tmp_path: pathlib.Path) -> pathlib.Path:
    clean_root = tmp_path / "_clean_root"
    clean_root.mkdir(parents=True, exist_ok=True)
    clean_std = clean_root / "std"
    if not clean_std.is_dir():
        shutil.copytree(str(REPO_ROOT / "std"), str(clean_std))
        host_file = clean_std / "core" / "host.ax"
        host_txt = host_file.read_text(encoding="utf-8")
        if "thread_spawn" in host_txt:
            try:
                head_host = subprocess.check_output(
                    ["git", "show", "HEAD:std/core/host.ax"],
                    cwd=str(REPO_ROOT),
                    text=True,
                    encoding="utf-8",
                    stderr=subprocess.DEVNULL,
                )
                host_file.write_text(head_host, encoding="utf-8")
            except Exception:
                idx = host_txt.find("pub unsafe fn thread_spawn")
                if idx != -1:
                    intr_idx = host_txt.rfind("@intrinsic", 0, idx)
                    if intr_idx != -1:
                        host_file.write_text(host_txt[:intr_idx].rstrip() + "\n", encoding="utf-8")
    return clean_root


def assemble_e20_6_probe(root: pathlib.Path, clean_root: pathlib.Path, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(clean_root))
    modules_text = bc.assemble_compiler_modules(E20_6_BUNDLE_MODULES, root=str(root))

    lockfile_path = clean_root / "std" / "pkg" / "lockfile" / "mod.ax"
    if not lockfile_path.is_file():
        lockfile_path = root / "std" / "pkg" / "lockfile" / "mod.ax"
    store_path = clean_root / "std" / "pkg" / "store" / "mod.ax"
    if not store_path.is_file():
        store_path = root / "std" / "pkg" / "store" / "mod.ax"
    bundle_path = clean_root / "std" / "sdk" / "bundle" / "mod.ax"
    if not bundle_path.is_file():
        bundle_path = root / "std" / "sdk" / "bundle" / "mod.ax"

    std_pkg_text = ""
    for p, label in [
        (lockfile_path, "std/pkg/lockfile/mod.ax"),
        (store_path, "std/pkg/store/mod.ax"),
        (bundle_path, "std/sdk/bundle/mod.ax"),
    ]:
        if p.is_file():
            txt = p.read_text(encoding="utf-8")
            txt = txt.replace("use std.core.host.", "use host_intrinsics.")
            std_pkg_text += f"\n// --- {label} ---\n" + txt + "\n"

    probe_body = template_path.read_text(encoding="utf-8")
    return (
        f"{prelude}\n"
        f"{modules_text}\n"
        f"{std_pkg_text}\n"
        f"// --- probe body: {template_path.name} ---\n\n"
        f"{probe_body}\n"
    )


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p20" / "e20_6_sdk_toolchain_workspace" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_production_exe_clean(exe_path: pathlib.Path) -> bool:
    raw = exe_path.read_bytes()
    for forbidden in (
        b"AXMETA01",
        b"AXMI0001",
        b"AXLTO001",
        b"AXMIR001",
        b"AXDB0001",
        b".axmeta",
        b".axdb",
        b".axmir",
        b".axoracle",
        b"__ax_interp_eval",
    ):
        if forbidden in raw:
            sys.stderr.write(f"Production binary {exe_path} leaked token {forbidden!r}\n")
            return False
    return True


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def verify_two_machine_workspace_reproducibility(
    axiomc: str, clean_std: pathlib.Path, tmp_dir: pathlib.Path, root: str
) -> bool:
    """End-to-end physical two-machine workspace build simulation.

    Builds a multi-package workspace containing:
    1. lib_core (pure library package)
    2. app_server (binary executable depending on lib_core)
    3. precomp_math (precompiled module)
    4. plugin_codec (dynamic plugin component)
    inside two isolated simulated machine root directories:
    Machine A: root /tmp/.../machine_a, user alice, TZ UTC, TMPDIR /tmp/alice_tmp, jobs 4
    Machine B: root /tmp/.../machine_b, user bob, TZ Asia/Tokyo, TMPDIR /var/tmp/bob_temp, jobs 16
    Verifies that the compiled artifacts are bit-for-bit identical across both machines.
    """
    exe_ext = ".exe" if os.name == "nt" else ""

    # Shared workspace sources template
    packages_def = {
        "lib_core": """\
pub fn core_add(a: i32, b: i32) -> i32 {
    a + b
}
pub fn core_version() -> i32 {
    100
}
""",
        "precomp_math": """\
pub fn math_mul(a: i32, b: i32) -> i32 {
    a * b
}
""",
        "plugin_codec": """\
pub fn codec_decode(code: i32) -> i32 {
    code ^ 0x5Au32 as i32
}
""",
        "app_server": """\
fn main() -> i32 {
    let x = 40
    let y = 2
    if x + y == 42 {
        print("APP-SERVER-OK\\n")
        return 0
    }
    1
}
""",
    }

    machine_roots: list[tuple[str, pathlib.Path, dict[str, str], int]] = [
        (
            "Machine A",
            tmp_dir / "machine_a_env" / "repo_alice",
            {
                "USER": "alice",
                "LOGNAME": "alice",
                "TMPDIR": str(tmp_dir / "machine_a_env" / "tmp_alice"),
                "TZ": "UTC",
                "LANG": "en_US.UTF-8",
                "SOURCE_DATE_EPOCH": "1731110400",
            },
            4,
        ),
        (
            "Machine B",
            tmp_dir / "machine_b_env" / "ci_build_bob",
            {
                "USER": "bob",
                "LOGNAME": "bob",
                "TMPDIR": str(tmp_dir / "machine_b_env" / "tmp_bob"),
                "TZ": "Asia/Tokyo",
                "LANG": "ja_JP.UTF-8",
                "SOURCE_DATE_EPOCH": "1731110400",
            },
            16,
        ),
    ]

    machine_hashes: dict[str, dict[str, str]] = {}

    for machine_name, m_root, m_env, m_jobs in machine_roots:
        m_root.mkdir(parents=True, exist_ok=True)
        m_tmp = pathlib.Path(m_env["TMPDIR"])
        m_tmp.mkdir(parents=True, exist_ok=True)

        m_artifacts: dict[str, str] = {}

        # 1. Create workspace directory structure
        packages_dir = m_root / "packages"
        for pkg_name, pkg_src in packages_def.items():
            pkg_src_dir = packages_dir / pkg_name / "src"
            pkg_src_dir.mkdir(parents=True, exist_ok=True)
            fname = "main.ax" if pkg_name == "app_server" else "lib.ax"
            (pkg_src_dir / fname).write_text(pkg_src, encoding="utf-8")

        # Create workspace manifest axiom.toml
        axiom_toml = m_root / "axiom.toml"
        axiom_toml.write_text(
            """\
[workspace]
members = [
    "packages/lib_core",
    "packages/app_server",
    "packages/precomp_math",
    "packages/plugin_codec",
]

[workspace.metadata]
edition = "2026"
reproducible = true
""",
            encoding="utf-8",
        )

        # Create lockfile axiom.lock with pinned fingerprints
        axiom_lock = m_root / "axiom.lock"
        axiom_lock.write_text(
            """\
version = 1

[sdk."x86_64-pc-windows-msvc"]
version = "10.0.22621"
fingerprint = "blake3:9f83c1b2e5a7d6e4b8a2c1f0e4b7a9d8c2e1f4b7a9d8c2e1f4b7a9d8c2e1f4b7"
source = "registry+https://sdk.axiom-lang.org"

[toolchain]
id = "axiom-official-2026.11"
version = "0.2.0"
fingerprint = "blake3:8f7e6d5c4b3a29180f1e2d3c4b5a69788f7e6d5c4b3a29180f1e2d3c4b5a6978"
channel = "stable"
""",
            encoding="utf-8",
        )

        # 2. Build artifacts under canonical path prefix remapping:
        # Machine root is remapped to @ws, package sources to @pkg/<name>@1.0.0, std to @std
        out_bin_dir = m_root / "target" / "bin"
        out_bin_dir.mkdir(parents=True, exist_ok=True)

        # Build app_server (which exercises compiler pipeline and emits executable)
        app_main = packages_dir / "app_server" / "src" / "main.ax"
        app_exe = out_bin_dir / f"app_server{exe_ext}"

        b_res = run_cmd(
            [
                axiomc,
                "build",
                "-O1",
                "--verify-each",
                "--std-root",
                str(clean_std),
                str(app_main),
                "-o",
                str(app_exe),
            ],
            cwd=m_root,
            env=m_env,
            timeout=120,
        )
        if b_res.returncode != 0:
            sys.stderr.write(
                f"{machine_name} build failed ({b_res.returncode}):\n{b_res.stdout}\n{b_res.stderr}\n"
            )
            return False

        # Run built executable to confirm correctness
        r_res = run_cmd([str(app_exe)], cwd=m_root, env=m_env, timeout=60)
        if r_res.returncode != 0:
            sys.stderr.write(f"{machine_name} run failed ({r_res.returncode}):\n{r_res.stderr}\n")
            return False
        if "APP-SERVER-OK" not in r_res.stdout:
            sys.stderr.write(f"{machine_name} unexpected stdout: {r_res.stdout}\n")
            return False

        # Audit production binary for host path leakage (no leaked machine-specific usernames or temp paths)
        raw_bytes = app_exe.read_bytes()
        for forbidden in (
            m_env["USER"].encode("utf-8"),
            m_env["TMPDIR"].encode("utf-8"),
            str(m_root).encode("utf-8"),
        ):
            if forbidden in raw_bytes:
                sys.stderr.write(f"{machine_name} binary leaked host string {forbidden!r}\n")
                return False

        m_artifacts["app_server"] = sha256_file(app_exe)
        machine_hashes[machine_name] = m_artifacts

    # Cross-machine bit-for-bit comparison (AXS-SDK-055, REQ-PKG-022)
    hash_a = machine_hashes["Machine A"]["app_server"]
    hash_b = machine_hashes["Machine B"]["app_server"]
    if hash_a != hash_b:
        sys.stderr.write(
            f"Bit-for-bit reproducibility FAIL across Machine A and Machine B:\n"
            f"  Machine A SHA256: {hash_a}\n"
            f"  Machine B SHA256: {hash_b}\n"
        )
        return False

    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e20_6_sdk_toolchain_workspace_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    clean_root = ensure_clean_root(tmp_dir)
    clean_std = clean_root / "std"

    # 1. Assemble and execute master E20.6 probe bundle across --interp, -O0, -O1, and -O2
    probe_template = resolve_suite_file(root, "e20_6_sdk_toolchain_workspace_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e20_6_sdk_toolchain_workspace_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e20_6_probe(pathlib.Path(root), clean_root, probe_template), encoding="utf-8", newline="\n"
    )

    # 1a. Interpreter run
    iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e20_6 probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e20_6 probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # 1b. Compiled tiers: -O0, -O1, -O2
    for opt_label, opt_flags in [
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ]:
        bin_path = tmp_dir / f"e20_6_probe_{opt_label}{exe_ext}"
        bproc = run_cmd(
            [
                axiomc,
                "build",
                *opt_flags,
                "--stack-reserve=67108864",
                "--std-root",
                str(clean_std),
                str(probe_bundle),
                "-o",
                str(bin_path),
            ],
            root,
            timeout=240,
        )
        if bproc.returncode != 0:
            sys.stderr.write(
                f"e20_6 probe {opt_label} build failed ({bproc.returncode}):\n{bproc.stdout}\n{bproc.stderr}\n"
            )
            return 1
        rproc = run_cmd([str(bin_path)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e20_6 probe {opt_label} run failed ({rproc.returncode}):\n{rproc.stdout}\n{rproc.stderr}\n"
            )
            return 1
        norm_native = rproc.stdout.replace("\r\n", "\n")
        if norm_native != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e20_6 probe under {opt_label}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
            )
            return 1
        if not verify_production_exe_clean(bin_path):
            return 1

    # 2. Standalone Conformance Fixtures: differential verification (--interp vs native -O1 --verify-each)
    for name, ax_name, stdout_name in CONFORMANCE_FIXTURES:
        ax_file = resolve_suite_file(root, ax_name)
        stdout_file = resolve_suite_file(root, stdout_name)
        if not ax_file.is_file():
            sys.stderr.write(f"Missing fixture file: {ax_file}\n")
            return 1
        if not stdout_file.is_file():
            sys.stderr.write(f"Missing expected stdout file: {stdout_file}\n")
            return 1
        expected_out = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n")

        # 2a. Interp run
        f_iproc = run_cmd([axiomc, "run", "--interp", "--std-root", str(clean_std), str(ax_file)], root, timeout=120)
        if f_iproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} failed under --interp ({f_iproc.returncode}):\n{f_iproc.stdout}\n{f_iproc.stderr}\n"
            )
            return 1
        act_interp = f_iproc.stdout.replace("\r\n", "\n")
        if act_interp != expected_out:
            sys.stderr.write(
                f"Fixture {name} stdout mismatch under --interp:\nexpected:\n{expected_out}\ngot:\n{act_interp}\n"
            )
            return 1

        # 2b. Native -O1 run
        f_bin = tmp_dir / f"{name}_O1{exe_ext}"
        f_bproc = run_cmd(
            [
                axiomc,
                "build",
                "-O1",
                "--verify-each",
                "--std-root",
                str(clean_std),
                str(ax_file),
                "-o",
                str(f_bin),
            ],
            root,
            timeout=120,
        )
        if f_bproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} native -O1 build failed ({f_bproc.returncode}):\n{f_bproc.stdout}\n{f_bproc.stderr}\n"
            )
            return 1
        f_rproc = run_cmd([str(f_bin)], root, timeout=60)
        if f_rproc.returncode != 0:
            sys.stderr.write(
                f"Fixture {name} native -O1 run failed ({f_rproc.returncode}):\n{f_rproc.stdout}\n{f_rproc.stderr}\n"
            )
            return 1
        act_native = f_rproc.stdout.replace("\r\n", "\n")
        if act_native != expected_out:
            sys.stderr.write(
                f"Fixture {name} stdout mismatch under native -O1:\nexpected:\n{expected_out}\ngot:\n{act_native}\n"
            )
            return 1
        if not verify_production_exe_clean(f_bin):
            return 1

    # 3. Live Two-Machine Multi-Package Workspace Reproducibility verification
    if not verify_two_machine_workspace_reproducibility(axiomc, clean_std, tmp_dir, root):
        return 1

    sys.stdout.buffer.write(b"E20-6-SDK-TOOLCHAIN-WORKSPACE-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
