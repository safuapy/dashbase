"""Post-run verification for chain launcher.

Verifies that all patches were applied correctly and no stale references remain.
"""

import os
import re
from typing import List, Tuple
from .file_patcher import read_file, find_files


class VerificationResult:
    def __init__(self, check_name: str, passed: bool, detail: str = ""):
        self.check_name = check_name
        self.passed = passed
        self.detail = detail

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.check_name}: {self.detail}"


def verify_all(repo_root: str, config: dict, old_config: dict = None) -> List[VerificationResult]:
    """Run all verification checks.

    Returns list of VerificationResult objects.
    """
    if old_config is None:
        old_config = _default_old_config()

    results = []
    chain = config["chain"]
    binaries = config["binaries"]
    old_chain = old_config["chain"]
    old_binaries = old_config["binaries"]

    # ── 1. Check configure.ac has new values ─────────────────────────
    ac_file = os.path.join(repo_root, "configure.ac")
    if os.path.exists(ac_file):
        content = read_file(ac_file)
        results.append(VerificationResult(
            "configure.ac: client name",
            chain["client_name"] in content,
            f'expected "{chain["client_name"]}"'
        ))
        ac_var_map = {"daemon": "DAEMON", "qt": "GUI", "cli": "CLI", "tx": "TX", "wallet": "WALLET_TOOL"}
        for key, var_suffix in ac_var_map.items():
            results.append(VerificationResult(
                f"configure.ac: {key} binary name",
                f'BITCOIN_{var_suffix}_NAME={binaries[key]}' in content,
                f'expected "{binaries[key]}"'
            ))

    # ── 2. Check clientversion.cpp ───────────────────────────────────
    cv_file = os.path.join(repo_root, "src/clientversion.cpp")
    if os.path.exists(cv_file):
        content = read_file(cv_file)
        results.append(VerificationResult(
            "clientversion.cpp: client name",
            chain["client_name"] in content,
            f'expected "{chain["client_name"]}"'
        ))

    # ── 3. Check guiconstants.h ──────────────────────────────────────
    gui_file = os.path.join(repo_root, "src/qt/guiconstants.h")
    if os.path.exists(gui_file):
        content = read_file(gui_file)
        gui = config["gui"]
        results.append(VerificationResult(
            "guiconstants.h: org name",
            gui["organization_name"] in content,
            f'expected "{gui["organization_name"]}"'
        ))
        results.append(VerificationResult(
            "guiconstants.h: app name",
            gui["application_name_mainnet"] in content,
            f'expected "{gui["application_name_mainnet"]}"'
        ))

    # ── 4. Check chainparams.cpp for new magic bytes ─────────────────
    cp_file = os.path.join(repo_root, "src/chainparams.cpp")
    if os.path.exists(cp_file):
        content = read_file(cp_file)
        net = config["network"]
        if "mainnet" in net:
            magic = net["mainnet"]["magic_bytes"]
            for i, b in enumerate(magic):
                hex_val = f"0x{b:02x}"
                results.append(VerificationResult(
                    f"chainparams.cpp: mainnet magic[{i}]",
                    hex_val in content,
                    f'expected "{hex_val}"'
                ))

    # ── 5. Check for stale references ────────────────────────────────
    stale_names = set()
    if old_chain["name"] != chain["name"]:
        stale_names.add(old_chain["name"])
    if old_chain["client_name"] != chain["client_name"]:
        stale_names.add(old_chain["client_name"])

    # Check in critical files (not in comments/copyright which are OK)
    critical_files = [
        os.path.join(repo_root, "configure.ac"),
        os.path.join(repo_root, "src/clientversion.cpp"),
        os.path.join(repo_root, "src/qt/guiconstants.h"),
        os.path.join(repo_root, "src/qt/bitcoinunits.cpp"),
        os.path.join(repo_root, "src/util/system.cpp"),
    ]

    for stale in stale_names:
        for cf in critical_files:
            if os.path.exists(cf):
                content = read_file(cf)
                # Check for stale name outside of comments
                lines = content.split("\n")
                stale_lines = [l for l in lines if stale in l and not l.strip().startswith("//")]
                if stale_lines:
                    results.append(VerificationResult(
                        f"stale ref: {stale} in {os.path.basename(cf)}",
                        False,
                        f"found in {len(stale_lines)} line(s)"
                    ))
                else:
                    results.append(VerificationResult(
                        f"stale ref: {stale} in {os.path.basename(cf)}",
                        True,
                        "no stale references"
                    ))

    # ── 6. Check old binary names are gone from key files ─────────────
    stale_binaries = set()
    for key in ["daemon", "qt", "cli", "tx", "wallet"]:
        if old_binaries[key] != binaries[key]:
            stale_binaries.add(old_binaries[key])

    if stale_binaries:
        src_files = find_files(os.path.join(repo_root, "src"), ["*.cpp", "*.h", "*.am"])
        for stale_bin in stale_binaries:
            found_in = []
            for sf in src_files:
                content = read_file(sf)
                if stale_bin in content:
                    # Check it's not in a comment
                    lines = content.split("\n")
                    stale_lines = [l for l in lines if stale_bin in l and not l.strip().startswith("//")]
                    if stale_lines:
                        found_in.append(os.path.relpath(sf, repo_root))
            if found_in:
                results.append(VerificationResult(
                    f"stale binary: {stale_bin}",
                    False,
                    f"found in {len(found_in)} file(s): {', '.join(found_in[:5])}"
                ))
            else:
                results.append(VerificationResult(
                    f"stale binary: {stale_bin}",
                    True,
                    "no stale references in source"
                ))

    # ── 7. Check .rc files are renamed ───────────────────────────────
    for key in ["daemon", "cli", "tx", "wallet"]:
        old_rc = os.path.join(repo_root, "src", f'{old_binaries[key]}-res.rc')
        new_rc = os.path.join(repo_root, "src", f'{binaries[key]}-res.rc')
        if old_binaries[key] != binaries[key]:
            results.append(VerificationResult(
                f"rc rename: {key}",
                not os.path.exists(old_rc) and os.path.exists(new_rc),
                f'expected "{binaries[key]}-res.rc"'
            ))

    # ── 8. Check conf filename ───────────────────────────────────────
    sys_file = os.path.join(repo_root, "src/util/system.cpp")
    if os.path.exists(sys_file):
        content = read_file(sys_file)
        results.append(VerificationResult(
            "system.cpp: conf filename",
            chain["conf_file"] in content,
            f'expected "{chain["conf_file"]}"'
        ))

    # ── 9. Summary ───────────────────────────────────────────────────
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    results.append(VerificationResult(
        "SUMMARY",
        failed == 0,
        f"{passed} passed, {failed} failed"
    ))

    return results


def _default_old_config() -> dict:
    return {
        "chain": {
            "name": "Dashbase",
            "ticker": "DSB",
            "currency_unit": "DSB",
            "client_name": "Dashbase Core",
            "conf_file": "dashbase.conf",
            "data_dir": "DashbaseCore",
            "organization": "Dashbase Project",
            "domain": "dashbase.org",
        },
        "binaries": {
            "daemon": "dashbased",
            "qt": "dash-qt",
            "cli": "dashbase-cli",
            "tx": "dashbase-tx",
            "wallet": "dashbase-wallet",
            "util": "dashbase-util",
        },
        "gui": {
            "organization_name": "Dashbase",
            "organization_domain": "dashbase.org",
            "application_name_mainnet": "Dashbase-Qt",
            "application_name_testnet": "Dashbase-Qt-testnet",
            "application_name_regtest": "Dashbase-Qt-regtest",
        },
        "network": {
            "mainnet": {
                "magic_bytes": [84, 130, 159, 69],
                "default_port": 19997,
                "rpc_port": 19996,
            },
        },
    }
