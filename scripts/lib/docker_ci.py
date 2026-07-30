"""Docker, CI workflow, NSIS, and Windows resource patches.

Patches: Dockerfiles (user, data dir, image name), entrypoint scripts,
CI workflows (artifact names, binary refs), release_docker_hub.yml.
"""

import os
import re
from typing import List
from .file_patcher import (
    patch_file, patch_file_regex, read_file, write_file,
    find_files, PatchResult
)


def apply_docker_ci(repo_root: str, config: dict, old_config: dict = None) -> List[PatchResult]:
    """Apply Docker, CI, NSIS, and Windows resource patches.

    Args:
        repo_root: Absolute path to repo root
        config: New chainbrand config dict
        old_config: Old config for reverse mapping
    Returns:
        List of PatchResult objects
    """
    if old_config is None:
        old_config = _default_old_config()

    results = []
    chain = config["chain"]
    binaries = config["binaries"]
    docker = config.get("docker", {})
    old_chain = old_config["chain"]
    old_binaries = old_config["binaries"]
    old_docker = old_config.get("docker", {})

    options = config.get("options", {})

    # ── Docker files ─────────────────────────────────────────────────
    if options.get("patch_docker", True):
        results.extend(_patch_dockerfiles(repo_root, chain, old_chain, docker, old_docker, binaries, old_binaries))

    # ── CI workflows ─────────────────────────────────────────────────
    if options.get("patch_ci", True):
        results.extend(_patch_ci_workflows(repo_root, chain, old_chain, binaries, old_binaries))

    return results


def _patch_dockerfiles(repo_root: str, chain: dict, old_chain: dict,
                       docker: dict, old_docker: dict,
                       binaries: dict, old_binaries: dict) -> List[PatchResult]:
    """Patch all Docker-related files."""
    results = []
    containers_dir = os.path.join(repo_root, "contrib/containers")

    old_user = old_docker.get("user_name", "dashbase")
    new_user = docker.get("user_name", chain["name"].lower())
    old_data = old_docker.get("data_dir", ".dashbase")
    new_data = docker.get("data_dir", f".{chain['name'].lower()}")
    old_image = old_docker.get("image_name", "safuapy/dashbased")
    new_image = docker.get("image_name", f"safuapy/{binaries['daemon']}")
    old_daemon = old_binaries["daemon"]
    new_daemon = binaries["daemon"]
    old_conf = old_chain["conf_file"]
    new_conf = chain["conf_file"]

    # Find all Dockerfiles and shell scripts in containers/
    docker_files = find_files(containers_dir, ["Dockerfile*", "*.sh", "*.yml"])

    for df in docker_files:
        # User name
        r = patch_file(df, old_user, new_user)
        if r.changed:
            results.append(r)
        # Data dir (.dashbase -> .mychain)
        r = patch_file(df, f".{old_user}", f".{new_user}")
        if r.changed:
            results.append(r)
        # Home dir (/home/dashbase -> /home/mychain)
        r = patch_file(df, f"/home/{old_user}", f"/home/{new_user}")
        if r.changed:
            results.append(r)
        # Source dir (/src/dashbase -> /src/mychain)
        r = patch_file(df, f"/src/{old_user}", f"/src/{new_user}")
        if r.changed:
            results.append(r)
        # Daemon name in entrypoint
        r = patch_file(df, old_daemon, new_daemon)
        if r.changed:
            results.append(r)
        # Conf file name
        r = patch_file(df, old_conf, new_conf)
        if r.changed:
            results.append(r)
        # Labels: "Dashbase" -> chain name
        r = patch_file(df, f'"{old_chain["name"]}"', f'"{chain["name"]}"')
        if r.changed:
            results.append(r)
        # Old client name in labels
        r = patch_file(df, old_chain["client_name"], chain["client_name"])
        if r.changed:
            results.append(r)

    # ── release_docker_hub.yml ───────────────────────────────────────
    release_file = os.path.join(repo_root, ".github/workflows/release_docker_hub.yml")
    if os.path.exists(release_file):
        r = patch_file(release_file, old_image, new_image)
        if r.changed:
            results.append(r)
        # Also replace dashcore in download URLs
        r = patch_file(release_file, "dashcore-", f'{chain["name"].lower()}-')
        if r.changed:
            results.append(r)

    return results


def _patch_ci_workflows(repo_root: str, chain: dict, old_chain: dict,
                        binaries: dict, old_binaries: dict) -> List[PatchResult]:
    """Patch CI workflow files."""
    results = []
    workflows_dir = os.path.join(repo_root, ".github/workflows")
    old_pkg = old_chain["name"].lower()
    new_pkg = chain["name"].lower()

    # build-wallets.yml
    bw_file = os.path.join(workflows_dir, "build-wallets.yml")
    if os.path.exists(bw_file):
        # Artifact names: dashcore-macos-intel -> mychain-macos-intel
        r = patch_file(bw_file, f'{old_pkg}-macos', f'{new_pkg}-macos')
        if r.changed:
            results.append(r)
        r = patch_file(bw_file, f'{old_pkg}-windows', f'{new_pkg}-windows')
        if r.changed:
            results.append(r)
        r = patch_file(bw_file, f'{old_pkg}-linux', f'{new_pkg}-linux')
        if r.changed:
            results.append(r)
        # Staging dir names
        r = patch_file(bw_file, f'{old_pkg}-${{', f'{new_pkg}-${{')
        if r.changed:
            results.append(r)
        # release/opt/dashbase -> release/opt/mychain
        r = patch_file(bw_file, f'release/opt/{old_chain["name"].lower()}', f'release/opt/{chain["name"].lower()}')
        if r.changed:
            results.append(r)

    # build-tauri-wallet.yml
    bt_file = os.path.join(workflows_dir, "build-tauri-wallet.yml")
    if os.path.exists(bt_file):
        r = patch_file(bt_file, f'{old_pkg}-macos', f'{new_pkg}-macos')
        if r.changed:
            results.append(r)
        r = patch_file(bt_file, f'{old_pkg}-windows', f'{new_pkg}-windows')
        if r.changed:
            results.append(r)
        r = patch_file(bt_file, f'{old_pkg}-linux', f'{new_pkg}-linux')
        if r.changed:
            results.append(r)

    return results


def _default_old_config() -> dict:
    """Default Dashbase config for Docker/CI reverse mapping."""
    return {
        "chain": {
            "name": "Dashbase",
            "client_name": "Dashbase Core",
            "conf_file": "dashbase.conf",
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
        "docker": {
            "image_name": "safuapy/dashbased",
            "user_name": "dashbase",
            "data_dir": ".dashbase",
        },
    }
