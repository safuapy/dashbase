"""Branding and naming patches across the codebase.

Patches: configure.ac, clientversion.cpp, guiconstants.h, bitcoinunits.cpp,
init.cpp, bitcoind.cpp, util/system.cpp, Windows .rc files, NSIS setup.nsi.in.
"""

import os
import re
from typing import List
from .file_patcher import (
    patch_file, patch_file_regex, read_file, write_file,
    find_files, PatchResult, verify_contains
)


def apply_branding(repo_root: str, config: dict, old_config: dict = None) -> List[PatchResult]:
    """Apply all branding changes across the codebase.

    Args:
        repo_root: Absolute path to repo root
        config: New chainbrand config dict
        old_config: Current/old config for reverse mapping (defaults to Dashbase values)
    Returns:
        List of PatchResult objects
    """
    if old_config is None:
        old_config = {
            "chain": {
                "name": "Dashbase",
                "ticker": "DSB",
                "currency_unit": "DSB",
                "subunit": "duffs",
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
            "build": {
                "package_name": "dashbase-core",
                "copyright_holder": "Dashbase Project",
                "copyright_year": "2026",
                "website_url": "https://dashbase.org",
                "source_url": "https://github.com/safuapy/dashbase",
            },
            "gui": {
                "organization_name": "Dashbase",
                "organization_domain": "dashbase.org",
                "application_name_mainnet": "Dashbase-Qt",
                "application_name_testnet": "Dashbase-Qt-testnet",
                "application_name_regtest": "Dashbase-Qt-regtest",
            },
        }

    results = []
    chain = config["chain"]
    binaries = config["binaries"]
    build = config["build"]
    gui = config["gui"]

    old_chain = old_config["chain"]
    old_binaries = old_config["binaries"]
    old_build = old_config["build"]
    old_gui = old_config["gui"]

    # ── 1. configure.ac ──────────────────────────────────────────────
    ac_file = os.path.join(repo_root, "configure.ac")
    if os.path.exists(ac_file):
        r = patch_file(ac_file, f'[{old_chain["client_name"]}]', f'[{chain["client_name"]}]')
        results.append(r)
        r = patch_file(ac_file, old_build["source_url"], build["source_url"])
        results.append(r)
        r = patch_file(ac_file, old_chain["domain"], chain["domain"])
        results.append(r)
        r = patch_file(ac_file, f'[{old_build["copyright_holder"]}]', f'[{build["copyright_holder"]}]')
        results.append(r)
        # Binary names
        ac_var_map = {"daemon": "DAEMON", "qt": "GUI", "cli": "CLI", "tx": "TX", "wallet": "WALLET_TOOL"}
        for key, var_suffix in ac_var_map.items():
            r = patch_file(ac_file, f'BITCOIN_{var_suffix}_NAME={old_binaries[key]}', f'BITCOIN_{var_suffix}_NAME={binaries[key]}')
            results.append(r)
        # Copyright year
        r = patch_file_regex(ac_file, r'define\(_COPYRIGHT_YEAR,\s*\d+\)', f'define(_COPYRIGHT_YEAR, {build["copyright_year"]})')
        results.append(r)

    # ── 2. clientversion.cpp ─────────────────────────────────────────
    cv_file = os.path.join(repo_root, "src/clientversion.cpp")
    if os.path.exists(cv_file):
        r = patch_file(cv_file, f'"{old_chain["client_name"]}"', f'"{chain["client_name"]}"')
        results.append(r)

    # ── 3. guiconstants.h ────────────────────────────────────────────
    gui_file = os.path.join(repo_root, "src/qt/guiconstants.h")
    if os.path.exists(gui_file):
        r = patch_file(gui_file, f'QAPP_ORG_NAME "{old_gui["organization_name"]}"', f'QAPP_ORG_NAME "{gui["organization_name"]}"')
        results.append(r)
        r = patch_file(gui_file, f'QAPP_ORG_DOMAIN "{old_gui["organization_domain"]}"', f'QAPP_ORG_DOMAIN "{gui["organization_domain"]}"')
        results.append(r)
        r = patch_file(gui_file, f'QAPP_APP_NAME_DEFAULT "{old_gui["application_name_mainnet"]}"', f'QAPP_APP_NAME_DEFAULT "{gui["application_name_mainnet"]}"')
        results.append(r)
        r = patch_file(gui_file, f'QAPP_APP_NAME_TESTNET "{old_gui["application_name_testnet"]}"', f'QAPP_APP_NAME_TESTNET "{gui["application_name_testnet"]}"')
        results.append(r)
        r = patch_file(gui_file, f'QAPP_APP_NAME_REGTEST "{old_gui["application_name_regtest"]}"', f'QAPP_APP_NAME_REGTEST "{gui["application_name_regtest"]}"')
        results.append(r)
        # Devnet name uses %s pattern
        old_devnet = old_gui["application_name_mainnet"].replace("-Qt", "-Qt-%s")
        new_devnet = gui["application_name_mainnet"].replace("-Qt", "-Qt-%s")
        r = patch_file(gui_file, f'QAPP_APP_NAME_DEVNET "{old_devnet}"', f'QAPP_APP_NAME_DEVNET "{new_devnet}"')
        results.append(r)

    # ── 4. bitcoinunits.cpp ──────────────────────────────────────────
    units_file = os.path.join(repo_root, "src/qt/bitcoinunits.cpp")
    if os.path.exists(units_file):
        old_unit = old_chain["currency_unit"]
        new_unit = chain["currency_unit"]
        # Currency unit strings: "DSB" -> "MYC", "mDSB" -> "mMYC", etc.
        r = patch_file(units_file, f'"{old_unit}"', f'"{new_unit}"')
        results.append(r)
        r = patch_file(units_file, f'"m{old_unit}"', f'"m{new_unit}"')
        results.append(r)
        r = patch_file(units_file, f'"t{old_unit}"', f'"t{new_unit}"')
        results.append(r)
        r = patch_file(units_file, f'"mt{old_unit}"', f'"mt{new_unit}"')
        results.append(r)
        # micro symbol variants
        r = patch_file_regex(units_file, r'μt?' + old_unit, lambda m: m.group(0).replace(old_unit, new_unit))
        results.append(r)
        # Subunit name (duffs -> mycuffs)
        old_subunit = old_chain.get("subunit", "duffs")
        new_subunit = chain.get("subunit", "duffs")
        if old_subunit != new_subunit:
            r = patch_file(units_file, f'"{old_subunit}"', f'"{new_subunit}"')
            results.append(r)
            r = patch_file(units_file, f'"t{old_subunit}"', f'"t{new_subunit}"')
            results.append(r)
        # Chain name in descriptions
        r = patch_file(units_file, f'"{old_chain["name"]}"', f'"{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Test{old_chain["name"]}"', f'"Test{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Milli-{old_chain["name"]}"', f'"Milli-{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Micro-{old_chain["name"]}"', f'"Micro-{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Milli-Test{old_chain["name"]}"', f'"Milli-Test{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Micro-Test{old_chain["name"]}"', f'"Micro-Test{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Ten Nano-{old_chain["name"]}"', f'"Ten Nano-{chain["name"]}"')
        results.append(r)
        r = patch_file(units_file, f'"Ten Nano-Test{old_chain["name"]}"', f'"Ten Nano-Test{chain["name"]}"')
        results.append(r)

    # ── 5. init.cpp ──────────────────────────────────────────────────
    init_file = os.path.join(repo_root, "src/init.cpp")
    if os.path.exists(init_file):
        r = patch_file(init_file, old_build["source_url"], build["source_url"])
        results.append(r)
        r = patch_file(init_file, old_build["website_url"], build["website_url"])
        results.append(r)

    # ── 6. bitcoind.cpp ──────────────────────────────────────────────
    bd_file = os.path.join(repo_root, "src/bitcoind.cpp")
    if os.path.exists(bd_file):
        # Replace daemon name references in comments and usage strings
        r = patch_file(bd_file, old_binaries["daemon"], binaries["daemon"])
        results.append(r)

    # ── 7. util/system.cpp ───────────────────────────────────────────
    sys_file = os.path.join(repo_root, "src/util/system.cpp")
    if os.path.exists(sys_file):
        r = patch_file(sys_file, f'BITCOIN_CONF_FILENAME = "{old_chain["conf_file"]}"', f'BITCOIN_CONF_FILENAME = "{chain["conf_file"]}"')
        results.append(r)
        # Comment references
        r = patch_file(sys_file, f'Create an empty {old_chain["conf_file"]}', f'Create an empty {chain["conf_file"]}')
        results.append(r)

    # ── 8. Windows .rc files ─────────────────────────────────────────
    rc_files = find_files(os.path.join(repo_root, "src"), ["*-res.rc"])
    for rc_file in rc_files:
        r = patch_file(rc_file, f'"CompanyName",        "{old_gui["organization_name"]}"', f'"CompanyName",        "{gui["organization_name"]}"')
        results.append(r)
        # Replace old daemon/binary names in FileDescription, InternalName, OriginalFilename, ProductName
        for key in ["daemon", "qt", "cli", "tx", "wallet"]:
            r = patch_file(rc_file, old_binaries[key], binaries[key])
            results.append(r)
        # Replace old client name
        r = patch_file(rc_file, old_chain["client_name"], chain["client_name"])
        results.append(r)

    # Rename .rc files to match new binary names
    rc_dir = os.path.join(repo_root, "src")
    renames = [
        (f'{old_binaries["daemon"]}-res.rc', f'{binaries["daemon"]}-res.rc'),
        (f'{old_binaries["cli"]}-res.rc', f'{binaries["cli"]}-res.rc'),
        (f'{old_binaries["tx"]}-res.rc', f'{binaries["tx"]}-res.rc'),
        (f'{old_binaries["wallet"]}-res.rc', f'{binaries["wallet"]}-res.rc'),
    ]
    for old_name, new_name in renames:
        old_path = os.path.join(rc_dir, old_name)
        new_path = os.path.join(rc_dir, new_name)
        if os.path.exists(old_path) and old_name != new_name:
            os.rename(old_path, new_path)
            results.append(PatchResult(new_path, True, f"renamed from {old_name}"))

    # Qt .rc file
    qt_rc_old = os.path.join(repo_root, "src/qt/res", f'{old_binaries["qt"]}-res.rc')
    qt_rc_new = os.path.join(repo_root, "src/qt/res", f'{binaries["qt"]}-res.rc')
    if os.path.exists(qt_rc_old) and old_binaries["qt"] != binaries["qt"]:
        os.rename(qt_rc_old, qt_rc_new)
        results.append(PatchResult(qt_rc_new, True, f"renamed from {old_binaries["qt"]}-res.rc"))

    # ── 9. NSIS setup.nsi.in ─────────────────────────────────────────
    nsi_file = os.path.join(repo_root, "share/setup.nsi.in")
    if os.path.exists(nsi_file):
        r = patch_file(nsi_file, f'InstallDir $PROGRAMFILES64\\{old_chain["client_name"].split()[0]}', f'InstallDir $PROGRAMFILES64\\{chain["client_name"].split()[0]}')
        results.append(r)
        r = patch_file(nsi_file, f'MUI_STARTMENUPAGE_DEFAULTFOLDER "{old_chain["name"]}"', f'MUI_STARTMENUPAGE_DEFAULTFOLDER "{chain["name"]}"')
        results.append(r)
        # DisplayIcon references old binary name
        r = patch_file(nsi_file, f'DisplayIcon $INSTDIR\\{old_binaries["qt"]}.exe', f'DisplayIcon $INSTDIR\\{binaries["qt"]}.exe')
        results.append(r)
        # URL Protocol
        r = patch_file(nsi_file, f'URL:Dash', f'URL:{chain["name"]}')
        results.append(r)

    # ── 10. Makefile.am (top-level) ──────────────────────────────────
    mk_file = os.path.join(repo_root, "Makefile.am")
    if os.path.exists(mk_file):
        # Update OSX installer icon and app name references
        r = patch_file(mk_file, f'OSX_INSTALLER_ICONS=$(top_srcdir)/share/pixmaps/dash.icns', f'OSX_INSTALLER_ICONS=$(top_srcdir)/share/pixmaps/{chain["name"].lower()}.icns')
        results.append(r)
        # OSX app name
        r = patch_file(mk_file, f'$(APP_DIST_DIR)/$(OSX_APP)/Contents/MacOS/{old_gui["application_name_mainnet"]}', f'$(APP_DIST_DIR)/$(OSX_APP)/Contents/MacOS/{gui["application_name_mainnet"]}')
        results.append(r)

    # ── 11. Makefile.am references in src/ ───────────────────────────
    # The Makefiles use autoconf variables, but some may have hardcoded names
    src_am_files = find_files(os.path.join(repo_root, "src"), ["Makefile.am"])
    for am_file in src_am_files:
        for key in ["daemon", "qt", "cli", "tx", "wallet"]:
            if old_binaries[key] != binaries[key]:
                r = patch_file(am_file, old_binaries[key], binaries[key])
                if r.changed:
                    results.append(r)

    return results
