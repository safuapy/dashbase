#!/usr/bin/env python3
"""Chain Launcher — Customize and launch a new chain from the Dashbase codebase.

Usage:
  Interactive wizard:
    python3 scripts/launch_chain.py

  CLI mode (with pre-made config):
    python3 scripts/launch_chain.py --config chainbrand.json

  Generate default config template:
    python3 scripts/launch_chain.py --generate-config > chainbrand.json

This tool handles:
  - Chain branding (name, ticker, binary names, GUI, copyright)
  - Network identity (magic bytes, ports, base58, DNS seeds, data dir)
  - Genesis block mining (mainnet + testnet)
  - Spork key generation (secp256k1) + BLS masternode operator keys
  - Consensus params (DIP/BIP heights, BIP9 deployments, LLMQ, subsidy)
  - Docker/CI/NSIS/Windows resource patching
  - Post-run verification
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add scripts dir to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from lib.branding import apply_branding
from lib.network import apply_network_identity, apply_genesis_to_chainparams, apply_spork_addresses
from lib.consensus import apply_consensus_params
from lib.docker_ci import apply_docker_ci
from lib.verifier import verify_all
from lib.genesis import GenesisGenerator
from lib.keys import SporkKeyGenerator, BLSKeyGenerator
from lib.generate import generate_all_network_params
from lib.file_patcher import read_file, write_file, PatchResult


def get_repo_root() -> str:
    """Get repo root from script location."""
    return os.path.dirname(SCRIPT_DIR)


def generate_default_config() -> dict:
    """Generate a default chainbrand.json config with Dashbase values."""
    return {
        "_comment": "Chain brand configuration. Edit these values to customize your chain. Run: python3 scripts/launch_chain.py --config chainbrand.json",

        "chain": {
            "name": "Dashbase",
            "description": "A rebrandable masternode chain based on Dash Core v18.2.2",
            "ticker": "DSB",
            "currency_unit": "DSB",
            "subunit": "duffs",
            "subunit_decimals": 8,
            "client_name": "Dashbase Core",
            "conf_file": "dashbase.conf",
            "data_dir": "DashbaseCore",
            "organization": "Dashbase Project",
            "domain": "dashbase.org",
        },

        "network": {
            "mainnet": {
                "magic_bytes": [84, 130, 159, 69],
                "default_port": 19997,
                "rpc_port": 19996,
                "dns_seeds": ["dnsseed.dashbase.org"],
                "fixed_seeds": [],
                "bip44_coin_type": 153,
                "base58_prefixes": {
                    "pubkey_address": 76,
                    "script_address": 16,
                    "secret_key": 204,
                    "ext_public_key": [4, 136, 178, 30],
                    "ext_secret_key": [4, 136, 173, 228],
                },
                "genesis": {
                    "timestamp": 1753734000,
                    "nonce": 961483,
                    "bits": 486604768,
                    "version": 1,
                    "reward": 5000000000,
                    "psz_timestamp": "Wired 09/Jan/2014 The Grand Experiment Goes Live: Overstock.com Is Now Accepting Bitcoins",
                    "pubkey_hex": "040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9",
                    "hash": "00000872de437c3605386676ec196376df3c12f53ccdc0f8f7d5aa67ad883a71",
                    "merkle_root": "e0028eb9648db56b1ac77cf090b99048a8007e2bb64b68f092c03c7f56a662c7",
                },
            },
            "testnet": {
                "magic_bytes": [197, 177, 253, 114],
                "default_port": 29997,
                "rpc_port": 29996,
                "dns_seeds": ["testnet-seed.dashbase.org"],
                "fixed_seeds": [],
                "bip44_coin_type": 1,
                "base58": {
                    "pubkey_address": 139,
                    "script_address": 19,
                    "secret_key": 239,
                    "ext_public_key": [4, 136, 178, 30],
                    "ext_secret_key": [4, 136, 173, 228],
                },
                "genesis": {
                    "timestamp": 1753734001,
                    "nonce": 1340636,
                    "bits": 486604768,
                    "version": 1,
                    "reward": 5000000000,
                    "psz_timestamp": "Wired 09/Jan/2014 The Grand Experiment Goes Live: Overstock.com Is Now Accepting Bitcoins",
                    "pubkey_hex": "040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9",
                    "hash": "000005776e75d3d6325b324c553e92aff7818ad6322072b168d5ce73f8e4332e",
                    "merkle_root": "e0028eb9648db56b1ac77cf090b99048a8007e2bb64b68f092c03c7f56a662c7",
                },
            },
            "regtest": {
                "magic_bytes": [220, 231, 132, 244],
                "default_port": 19994,
                "rpc_port": 19993,
                "bip44_coin_type": 1,
                "base58": {
                    "pubkey_address": 111,
                    "script_address": 196,
                    "secret_key": 239,
                    "ext_public_key": [4, 136, 178, 30],
                    "ext_secret_key": [4, 136, 173, 228],
                },
            },
        },

        "consensus": {
            "mainnet": _default_consensus_mainnet(),
            "testnet": _default_consensus_testnet(),
        },

        "keys": {
            "generate_spork_keys": True,
            "generate_bls_keys": True,
            "spork_keys": {
                "mainnet": {"address": "", "wif": ""},
                "testnet": {"address": "", "wif": ""},
            },
            "bls_keys": {
                "masternode_operator_priv": "",
                "masternode_operator_pub": "",
            },
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
            "version_major": 18,
            "version_minor": 2,
            "version_revision": 2,
            "version_build": 0,
            "version_suffix": "",
        },

        "gui": {
            "organization_name": "Dashbase",
            "organization_domain": "dashbase.org",
            "application_name_mainnet": "Dashbase-Qt",
            "application_name_testnet": "Dashbase-Qt-testnet",
            "application_name_regtest": "Dashbase-Qt-regtest",
        },

        "docker": {
            "image_name": "safuapy/dashbased",
            "user_name": "dashbase",
            "data_dir": ".dashbase",
        },

        "options": {
            "auto_generate_network": False,
            "mine_genesis": False,
            "clear_checkpoints": True,
            "clear_fixed_seeds": True,
            "patch_docker": True,
            "patch_ci": True,
            "patch_nsis": True,
            "patch_windows_resources": True,
            "verify_after_patch": True,
            "git_commit": False,
            "git_commit_message": "feat: customize chain for {chain_name}",
        },
    }


def _default_consensus_mainnet() -> dict:
    return {
        "subsidy_halving_interval": 210000,
        "pow_target_spacing": 120,
        "pow_target_timespan": 86400,
        "pow_limit": "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "masternode_payments_start_block": 0,
        "masternode_payments_increase_block": 0,
        "masternode_payments_increase_period": 1,
        "instant_send_confirmations_required": 6,
        "instant_send_keep_lock": 24,
        "budget_payments_start_block": 0,
        "budget_payments_cycle_blocks": 10080,
        "budget_payments_window_blocks": 100,
        "superblock_start_block": 10080,
        "superblock_cycle": 10080,
        "superblock_maturity_window": 1440,
        "governance_min_quorum": 10,
        "governance_filter_elements": 20000,
        "masternode_minimum_confirmations": 15,
        "bip34_height": 1,
        "bip65_height": 1,
        "bip66_height": 1,
        "dip0001_height": 1,
        "dip0003_height": 1,
        "dip0003_enforcement_height": 1,
        "dip0008_height": 1,
        "brr_height": 1,
        "rule_change_activation_threshold": 1512,
        "miner_confirmation_window": 720,
        "deployments": {
            "TESTDUMMY": {"bit": 28, "start_time": 0, "timeout": 999999999999},
            "CSV": {"bit": 0, "start_time": 0, "timeout": 999999999999},
            "DIP0001": {"bit": 1, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
            "BIP147": {"bit": 2, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
            "DIP0003": {"bit": 3, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
            "DIP0008": {"bit": 4, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
            "REALLOC": {"bit": 5, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
            "DIP0020": {"bit": 6, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
            "DIP0024": {"bit": 7, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
        },
        "llmq_chainlocks": "LLMQ_400_60",
        "llmq_instant_send": "LLMQ_50_60",
        "llmq_dip0024_instant_send": "LLMQ_60_75",
        "llmq_mnhf": "LLMQ_400_85",
    }


def _default_consensus_testnet() -> dict:
    return {
        "subsidy_halving_interval": 210000,
        "pow_target_spacing": 120,
        "pow_target_timespan": 86400,
        "pow_limit": "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "masternode_payments_start_block": 0,
        "masternode_payments_increase_block": 0,
        "masternode_payments_increase_period": 10,
        "instant_send_confirmations_required": 2,
        "instant_send_keep_lock": 6,
        "budget_payments_start_block": 0,
        "budget_payments_cycle_blocks": 50,
        "budget_payments_window_blocks": 10,
        "superblock_start_block": 50,
        "superblock_cycle": 50,
        "superblock_maturity_window": 50,
        "governance_min_quorum": 1,
        "governance_filter_elements": 500,
        "masternode_minimum_confirmations": 1,
        "bip34_height": 1,
        "bip65_height": 1,
        "bip66_height": 1,
        "dip0001_height": 1,
        "dip0003_height": 1,
        "dip0003_enforcement_height": 1,
        "dip0008_height": 1,
        "brr_height": 1,
        "rule_change_activation_threshold": 1512,
        "miner_confirmation_window": 720,
        "deployments": {
            "TESTDUMMY": {"bit": 28, "start_time": 1199145601, "timeout": 1230767999},
            "CSV": {"bit": 0, "start_time": 0, "timeout": 999999999999},
            "DIP0001": {"bit": 1, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
            "BIP147": {"bit": 2, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
            "DIP0003": {"bit": 3, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
            "DIP0008": {"bit": 4, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
            "REALLOC": {"bit": 5, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
            "DIP0020": {"bit": 6, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
            "DIP0024": {"bit": 7, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
        },
        "llmq_chainlocks": "LLMQ_50_60",
        "llmq_instant_send": "LLMQ_50_60",
        "llmq_dip0024_instant_send": "LLMQ_60_75",
        "llmq_mnhf": "LLMQ_50_60",
    }


# ── Interactive Wizard ───────────────────────────────────────────────

def _prompt(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{msg}{suffix}: ").strip()
    return val if val else default


def _prompt_int(msg: str, default: int) -> int:
    val = _prompt(msg, str(default))
    try:
        return int(val)
    except ValueError:
        print(f"  Invalid number, using default: {default}")
        return default


def _prompt_bool(msg: str, default: bool) -> bool:
    d = "Y/n" if default else "y/N"
    val = input(f"{msg} [{d}]: ").strip().lower()
    if val in ("y", "yes"):
        return True
    if val in ("n", "no"):
        return False
    return default


def _prompt_list(msg: str, default: list) -> list:
    d = ",".join(str(x) for x in default)
    val = _prompt(msg, d)
    if not val:
        return default
    return [x.strip() for x in val.split(",")]


def run_wizard() -> dict:
    """Run interactive wizard to collect chain configuration."""
    print("=" * 70)
    print("  Chain Launcher — Interactive Configuration Wizard")
    print("=" * 70)
    print()

    config = generate_default_config()

    # ── Chain Identity ───────────────────────────────────────────────
    print("--- Chain Identity ---")
    config["chain"]["name"] = _prompt("Chain name", config["chain"]["name"])
    config["chain"]["ticker"] = _prompt("Ticker symbol", config["chain"]["ticker"])
    config["chain"]["currency_unit"] = _prompt("Currency unit", config["chain"]["currency_unit"])
    config["chain"]["subunit"] = _prompt("Subunit name", config["chain"]["subunit"])
    config["chain"]["client_name"] = _prompt("Client name", config["chain"]["client_name"])
    config["chain"]["conf_file"] = _prompt("Config filename", config["chain"]["conf_file"])
    config["chain"]["data_dir"] = _prompt("Data directory name", config["chain"]["data_dir"])
    config["chain"]["organization"] = _prompt("Organization", config["chain"]["organization"])
    config["chain"]["domain"] = _prompt("Domain", config["chain"]["domain"])
    print()

    # ── Binaries ─────────────────────────────────────────────────────
    print("--- Binaries ---")
    prefix = config["chain"]["name"].lower()
    config["binaries"]["daemon"] = _prompt("Daemon binary name", f"{prefix}d")
    config["binaries"]["qt"] = _prompt("Qt GUI binary name", f"{prefix}-qt")
    config["binaries"]["cli"] = _prompt("CLI binary name", f"{prefix}-cli")
    config["binaries"]["tx"] = _prompt("Tx tool binary name", f"{prefix}-tx")
    config["binaries"]["wallet"] = _prompt("Wallet tool binary name", f"{prefix}-wallet")
    print()

    # ── Network ──────────────────────────────────────────────────────
    print("--- Network ---")
    auto_net = _prompt_bool("Auto-generate all network params (magic bytes, ports, base58, BIP44)?", True)
    if auto_net:
        print("  Generating unique network parameters...")
        net_params = generate_all_network_params(
            chain_name=config["chain"]["name"],
            existing_mainnet=config["network"].get("mainnet", {}),
            existing_testnet=config["network"].get("testnet", {}),
        )
        # Mainnet
        config["network"]["mainnet"]["magic_bytes"] = net_params["mainnet"]["magic_bytes"]
        config["network"]["mainnet"]["default_port"] = net_params["mainnet"]["default_port"]
        config["network"]["mainnet"]["rpc_port"] = net_params["mainnet"]["rpc_port"]
        config["network"]["mainnet"]["bip44_coin_type"] = net_params["mainnet"]["bip44_coin_type"]
        config["network"]["mainnet"]["base58_prefixes"]["pubkey_address"] = net_params["mainnet"]["base58_prefixes"]["pubkey_address"]
        config["network"]["mainnet"]["base58_prefixes"]["script_address"] = net_params["mainnet"]["base58_prefixes"]["script_address"]
        config["network"]["mainnet"]["base58_prefixes"]["secret_key"] = net_params["mainnet"]["base58_prefixes"]["secret_key"]
        # Testnet
        config["network"]["testnet"]["magic_bytes"] = net_params["testnet"]["magic_bytes"]
        config["network"]["testnet"]["default_port"] = net_params["testnet"]["default_port"]
        config["network"]["testnet"]["rpc_port"] = net_params["testnet"]["rpc_port"]
        config["network"]["testnet"]["bip44_coin_type"] = net_params["testnet"]["bip44_coin_type"]
        if "base58" not in config["network"]["testnet"]:
            config["network"]["testnet"]["base58"] = {}
        config["network"]["testnet"]["base58"]["pubkey_address"] = net_params["testnet"]["base58"]["pubkey_address"]
        config["network"]["testnet"]["base58"]["script_address"] = net_params["testnet"]["base58"]["script_address"]
        config["network"]["testnet"]["base58"]["secret_key"] = net_params["testnet"]["base58"]["secret_key"]

        print(f'  Mainnet magic: [{", ".join(f"0x{b:02x}" for b in config["network"]["mainnet"]["magic_bytes"])}]')
        print(f'  Mainnet P2P port: {config["network"]["mainnet"]["default_port"]}')
        print(f'  Mainnet RPC port: {config["network"]["mainnet"]["rpc_port"]}')
        print(f'  Mainnet BIP44 coin type: {config["network"]["mainnet"]["bip44_coin_type"]}')
        print(f'  Mainnet base58 pubkey: {config["network"]["mainnet"]["base58_prefixes"]["pubkey_address"]}')
        print(f'  Testnet magic: [{", ".join(f"0x{b:02x}" for b in config["network"]["testnet"]["magic_bytes"])}]')
        print(f'  Testnet P2P port: {config["network"]["testnet"]["default_port"]}')
        print(f'  Testnet RPC port: {config["network"]["testnet"]["rpc_port"]}')
    else:
        print("--- Network (Mainnet) ---")
        config["network"]["mainnet"]["magic_bytes"] = [
            int(x, 0) for x in _prompt_list(
                "Magic bytes (4 comma-separated hex or decimal)",
                config["network"]["mainnet"]["magic_bytes"]
            )
        ]
        config["network"]["mainnet"]["default_port"] = _prompt_int("P2P port", config["network"]["mainnet"]["default_port"])
        config["network"]["mainnet"]["rpc_port"] = _prompt_int("RPC port", config["network"]["mainnet"]["rpc_port"])
        config["network"]["mainnet"]["dns_seeds"] = _prompt_list("DNS seeds (comma-separated)", config["network"]["mainnet"]["dns_seeds"])
        config["network"]["mainnet"]["bip44_coin_type"] = _prompt_int("BIP44 coin type", config["network"]["mainnet"]["bip44_coin_type"])
        config["network"]["mainnet"]["base58_prefixes"]["pubkey_address"] = _prompt_int("Base58 pubkey address prefix", config["network"]["mainnet"]["base58_prefixes"]["pubkey_address"])
        config["network"]["mainnet"]["base58_prefixes"]["script_address"] = _prompt_int("Base58 script address prefix", config["network"]["mainnet"]["base58_prefixes"]["script_address"])
        config["network"]["mainnet"]["base58_prefixes"]["secret_key"] = _prompt_int("Base58 secret key prefix", config["network"]["mainnet"]["base58_prefixes"]["secret_key"])
        print()

        print("--- Network (Testnet) ---")
        config["network"]["testnet"]["magic_bytes"] = [
            int(x, 0) for x in _prompt_list(
                "Magic bytes (4 comma-separated hex or decimal)",
                config["network"]["testnet"]["magic_bytes"]
            )
        ]
        config["network"]["testnet"]["default_port"] = _prompt_int("P2P port", config["network"]["testnet"]["default_port"])
        config["network"]["testnet"]["rpc_port"] = _prompt_int("RPC port", config["network"]["testnet"]["rpc_port"])
        config["network"]["testnet"]["dns_seeds"] = _prompt_list("DNS seeds (comma-separated)", config["network"]["testnet"]["dns_seeds"])
    print()

    # ── Genesis ──────────────────────────────────────────────────────
    print("--- Genesis Block ---")
    mine_genesis = _prompt_bool("Mine new genesis blocks? (requires x11_hash module)", False)
    config["options"]["mine_genesis"] = mine_genesis
    if mine_genesis:
        config["network"]["mainnet"]["genesis"]["timestamp"] = _prompt_int(
            "Mainnet genesis timestamp (0 = now)", 0
        )
        testnet_ts = config["network"]["mainnet"]["genesis"]["timestamp"]
        if testnet_ts == 0:
            testnet_ts = int(time.time()) + 1
        config["network"]["testnet"]["genesis"]["timestamp"] = _prompt_int(
            "Testnet genesis timestamp (0 = now+1)", testnet_ts
        )
    print()

    # ── Keys ─────────────────────────────────────────────────────────
    print("--- Keys ---")
    config["keys"]["generate_spork_keys"] = _prompt_bool("Generate new spork keys?", True)
    config["keys"]["generate_bls_keys"] = _prompt_bool("Generate BLS masternode operator key?", True)
    print()

    # ── Build & GUI ──────────────────────────────────────────────────
    print("--- Build & GUI ---")
    config["build"]["copyright_holder"] = _prompt("Copyright holder", config["chain"]["organization"])
    config["build"]["copyright_year"] = _prompt("Copyright year", str(time.localtime().tm_year))
    config["build"]["website_url"] = _prompt("Website URL", f"https://{config['chain']['domain']}")
    config["build"]["source_url"] = _prompt("Source URL", config["build"]["source_url"])
    config["gui"]["organization_name"] = _prompt("GUI organization name", config["chain"]["name"])
    config["gui"]["organization_domain"] = _prompt("GUI domain", config["chain"]["domain"])
    config["gui"]["application_name_mainnet"] = _prompt("GUI app name (mainnet)", f'{config["chain"]["name"]}-Qt')
    config["gui"]["application_name_testnet"] = _prompt("GUI app name (testnet)", f'{config["chain"]["name"]}-Qt-testnet')
    config["gui"]["application_name_regtest"] = _prompt("GUI app name (regtest)", f'{config["chain"]["name"]}-Qt-regtest')
    print()

    # ── Docker ───────────────────────────────────────────────────────
    print("--- Docker ---")
    config["docker"]["image_name"] = _prompt("Docker image name", f'safuapy/{config["binaries"]["daemon"]}')
    config["docker"]["user_name"] = _prompt("Docker user name", config["chain"]["name"].lower())
    print()

    # ── Options ──────────────────────────────────────────────────────
    print("--- Options ---")
    config["options"]["clear_checkpoints"] = _prompt_bool("Clear old checkpoints?", True)
    config["options"]["clear_fixed_seeds"] = _prompt_bool("Clear fixed seeds?", True)
    config["options"]["patch_docker"] = _prompt_bool("Patch Docker files?", True)
    config["options"]["patch_ci"] = _prompt_bool("Patch CI workflows?", True)
    config["options"]["verify_after_patch"] = _prompt_bool("Run verification after patching?", True)
    config["options"]["git_commit"] = _prompt_bool("Git commit after patching?", False)
    print()

    # ── Save config ──────────────────────────────────────────────────
    save = _prompt_bool("Save config to chainbrand.json?", True)
    if save:
        config_path = os.path.join(get_repo_root(), "chainbrand.json")
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Config saved to {config_path}")
    print()

    return config


# ── Main Execution ───────────────────────────────────────────────────

def run_launch(repo_root: str, config: dict, old_config: dict = None) -> int:
    """Execute all chain customization steps.

    Returns 0 on success, 1 on failure.
    """
    chain_name = config["chain"]["name"]
    options = config.get("options", {})

    print("=" * 70)
    print(f"  Chain Launcher — Customizing for {chain_name}")
    print("=" * 70)
    print()

    all_results = []
    errors = []

    # ── Step 0: Auto-generate network params if requested ───────────
    if options.get("auto_generate_network", False):
        print("[0/8] Auto-generating network parameters...")
        net_params = generate_all_network_params(
            chain_name=chain_name,
            existing_mainnet=config["network"].get("mainnet", {}),
            existing_testnet=config["network"].get("testnet", {}),
        )
        # Mainnet
        mn = config["network"]["mainnet"]
        mn["magic_bytes"] = net_params["mainnet"]["magic_bytes"]
        mn["default_port"] = net_params["mainnet"]["default_port"]
        mn["rpc_port"] = net_params["mainnet"]["rpc_port"]
        mn["bip44_coin_type"] = net_params["mainnet"]["bip44_coin_type"]
        mn.setdefault("base58_prefixes", {}).update(net_params["mainnet"]["base58_prefixes"])
        # Testnet
        tn = config["network"]["testnet"]
        tn["magic_bytes"] = net_params["testnet"]["magic_bytes"]
        tn["default_port"] = net_params["testnet"]["default_port"]
        tn["rpc_port"] = net_params["testnet"]["rpc_port"]
        tn["bip44_coin_type"] = net_params["testnet"]["bip44_coin_type"]
        tn.setdefault("base58", {}).update(net_params["testnet"]["base58"])

        print(f'  Mainnet magic: [{", ".join(f"0x{b:02x}" for b in mn["magic_bytes"])}]')
        print(f'  Mainnet P2P: {mn["default_port"]}, RPC: {mn["rpc_port"]}, BIP44: {mn["bip44_coin_type"]}')
        print(f'  Testnet magic: [{", ".join(f"0x{b:02x}" for b in tn["magic_bytes"])}]')
        print(f'  Testnet P2P: {tn["default_port"]}, RPC: {tn["rpc_port"]}')
        print()

    # ── Step 1: Generate keys ────────────────────────────────────────
    keys_cfg = config.get("keys", {})
    if keys_cfg.get("generate_spork_keys", False):
        print("[1/8] Generating spork keys...")
        try:
            mainnet_b58 = config["network"]["mainnet"]["base58_prefixes"]["pubkey_address"]
            testnet_b58 = config["network"]["testnet"].get("base58", config["network"]["testnet"].get("base58_prefixes", {})).get("pubkey_address", 140)
            gen = SporkKeyGenerator(mainnet_addr_prefix=mainnet_b58, testnet_addr_prefix=testnet_b58)

            mainnet_key = gen.generate("mainnet")
            testnet_key = gen.generate("testnet")

            keys_cfg["spork_keys"]["mainnet"] = {"address": mainnet_key.address, "wif": mainnet_key.wif}
            keys_cfg["spork_keys"]["testnet"] = {"address": testnet_key.address, "wif": testnet_key.wif}

            print(f"  Mainnet spork address: {mainnet_key.address}")
            print(f"  Testnet spork address:  {testnet_key.address}")
        except Exception as e:
            errors.append(f"Spork key generation failed: {e}")
            print(f"  ERROR: {e}")
        print()

    if keys_cfg.get("generate_bls_keys", False):
        print("[2/8] Generating BLS masternode operator key...")
        try:
            bls_gen = BLSKeyGenerator()
            bls_key = bls_gen.generate()
            keys_cfg["bls_keys"]["masternode_operator_priv"] = bls_key.privkey_hex
            keys_cfg["bls_keys"]["masternode_operator_pub"] = bls_key.pubkey_hex
            print(f"  BLS privkey: {bls_key.privkey_hex}")
            print(f"  BLS pubkey:  {bls_key.pubkey_hex}")
        except Exception as e:
            errors.append(f"BLS key generation failed: {e}")
            print(f"  ERROR: {e}")
        print()

    # ── Step 2: Mine genesis blocks ──────────────────────────────────
    genesis_results = {}
    if options.get("mine_genesis", False):
        for network in ["mainnet", "testnet"]:
            if network not in config["network"]:
                continue
            gen_cfg = config["network"][network].get("genesis")
            if not gen_cfg:
                continue

            print(f"[3/8] Mining {network} genesis block...")
            n_time = gen_cfg.get("timestamp", 0)
            if n_time == 0:
                n_time = int(time.time())
                if network == "testnet":
                    n_time += 1

            n_bits = gen_cfg.get("bits", 486604768)
            n_version = gen_cfg.get("version", 1)
            reward = gen_cfg.get("reward", 5000000000)
            psz = gen_cfg.get("psz_timestamp", "")
            pubkey = gen_cfg.get("pubkey_hex", "")

            gen = GenesisGenerator(
                n_time=n_time,
                n_bits=n_bits,
                n_version=n_version,
                reward=reward,
                psz_timestamp=psz.encode() if psz else b"",
                pubkey_hex=pubkey,
            )

            def progress(nonce, rate):
                print(f"\r  Tried {nonce:,} nonces ({rate:.0f} H/s)...", end="", flush=True)

            result = gen.mine(progress_callback=progress)
            print()
            print(f"  FOUND! Nonce: {result.nonce}")
            print(f"  Hash: 0x{result.hash_hex}")
            print(f"  Merkle: 0x{result.merkle_root_hex}")
            print(f"  Time: {result.elapsed_seconds:.1f}s")

            genesis_results[network] = (result, n_bits, n_version, reward)

            # Update config with found values
            gen_cfg["timestamp"] = result.n_time
            gen_cfg["nonce"] = result.nonce
            gen_cfg["hash"] = result.hash_hex
            gen_cfg["merkle_root"] = result.merkle_root_hex
            print()

        # Patch genesis into chainparams.cpp
        for network, (result, n_bits, n_version, reward) in genesis_results.items():
            print(f"  Patching {network} genesis into chainparams.cpp...")
            r = apply_genesis_to_chainparams(repo_root, network, result, n_bits, n_version, reward)
            all_results.extend(r)
    else:
        print("[3/8] Skipping genesis mining (using existing genesis)")
    print()

    # ── Step 3: Apply branding ───────────────────────────────────────
    print("[4/8] Applying branding patches...")
    results = apply_branding(repo_root, config, old_config)
    all_results.extend(results)
    _print_results(results)
    print()

    # ── Step 4: Apply network identity ───────────────────────────────
    print("[5/8] Applying network identity patches...")
    results = apply_network_identity(repo_root, config, old_config)
    all_results.extend(results)
    _print_results(results)
    print()

    # ── Step 5: Apply consensus params ───────────────────────────────
    print("[6/8] Applying consensus parameter patches...")
    results = apply_consensus_params(repo_root, config, old_config)
    all_results.extend(results)
    _print_results(results)
    print()

    # ── Step 6: Patch spork addresses ────────────────────────────────
    if keys_cfg.get("spork_keys"):
        print("[7/8] Patching spork addresses...")
        for network in ["mainnet", "testnet"]:
            spork = keys_cfg["spork_keys"].get(network, {})
            if spork.get("address"):
                results = apply_spork_addresses(repo_root, network, spork["address"])
                all_results.extend(results)
                _print_results(results)
    print()

    # ── Step 7: Apply Docker/CI patches ──────────────────────────────
    print("[8/8] Applying Docker/CI patches...")
    results = apply_docker_ci(repo_root, config, old_config)
    all_results.extend(results)
    _print_results(results)
    print()

    # ── Step 8: Save updated config ──────────────────────────────────
    config_path = os.path.join(repo_root, "chainbrand.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {config_path}")
    print()

    # ── Step 9: Save keys to keys.json ───────────────────────────────
    if keys_cfg.get("generate_spork_keys") or keys_cfg.get("generate_bls_keys"):
        keys_path = os.path.join(repo_root, "keys.json")
        with open(keys_path, "w") as f:
            json.dump(keys_cfg, f, indent=2)
        print(f"Keys saved to {keys_path} (ADD TO .gitignore!)")
        print()

    # ── Step 10: Verify ──────────────────────────────────────────────
    if options.get("verify_after_patch", True):
        print("=" * 70)
        print("  Verification")
        print("=" * 70)
        results = verify_all(repo_root, config, old_config)
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"  [{mark}] {r.check_name}: {r.detail}")

        print()
        print(f"  {passed} passed, {failed} failed")
        if failed > 0:
            errors.append(f"Verification: {failed} check(s) failed")
        print()

    # ── Step 11: Git commit ──────────────────────────────────────────
    if options.get("git_commit", False):
        msg = options.get("git_commit_message", "feat: customize chain").format(chain_name=chain_name)
        print(f"Git committing: {msg}")
        import subprocess
        try:
            subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
            subprocess.run(["git", "commit", "-m", msg], cwd=repo_root, check=True)
            print("  Committed.")
        except Exception as e:
            errors.append(f"Git commit failed: {e}")
            print(f"  ERROR: {e}")
        print()

    # ── Summary ──────────────────────────────────────────────────────
    print("=" * 70)
    if errors:
        print(f"  COMPLETED WITH {len(errors)} ERROR(S)")
        for err in errors:
            print(f"    - {err}")
    else:
        print("  COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()

    # ── Next steps ───────────────────────────────────────────────────
    _print_next_steps(config, genesis_results, keys_cfg)

    return 1 if errors else 0


def _print_results(results: list):
    """Print patch results summary."""
    changed = sum(1 for r in results if r.changed)
    total = len(results)
    for r in results:
        if r.changed:
            print(f"  {r}")
    if changed == 0 and total > 0:
        print(f"  (no changes needed — {total} check(s) all up to date)")
    elif total == 0:
        print("  (no files to patch)")


def _print_next_steps(config: dict, genesis_results: dict, keys_cfg: dict):
    """Print next steps for the user."""
    chain = config["chain"]
    binaries = config["binaries"]

    print("Next steps:")
    print()
    print("1. Build the chain:")
    print(f"   cd {get_repo_root()}")
    print("   ./autogen.sh")
    print("   ./configure")
    print("   make -j$(nproc)")
    print()
    print("2. Run the daemon:")
    print(f"   ./src/{binaries['daemon']} -daemon")
    print(f"   ./src/{binaries['cli']} getblockchaininfo")
    print()
    print("3. Configure your node (add to ~/.{}/{}):".format(
        config["chain"]["data_dir"].lower(),
        config["chain"]["conf_file"]
    ))
    if keys_cfg.get("spork_keys", {}).get("mainnet", {}).get("wif"):
        print(f"   sporkkey={keys_cfg['spork_keys']['mainnet']['wif']}")
    if keys_cfg.get("bls_keys", {}).get("masternode_operator_priv"):
        print(f"   masternodeblsprivkey={keys_cfg['bls_keys']['masternode_operator_priv']}")
    print()
    print("4. Add seed nodes to src/chainparamsseeds.h when available")
    print()
    print("5. Add checkpoints to src/chainparams.cpp after blocks are mined")
    print()
    if genesis_results:
        print("Genesis blocks mined:")
        for net, (result, _, _, _) in genesis_results.items():
            print(f"   {net}: nonce={result.nonce}, hash=0x{result.hash_hex}")
    print()
    print("IMPORTANT: Add keys.json to .gitignore to protect your private keys!")


def main():
    parser = argparse.ArgumentParser(
        description="Chain Launcher — Customize and launch a new chain from the Dashbase codebase"
    )
    parser.add_argument("--config", "-c", type=str, help="Path to chainbrand.json config file")
    parser.add_argument("--generate-config", action="store_true", help="Print default config JSON and exit")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification, don't patch")
    args = parser.parse_args()

    if args.generate_config:
        config = generate_default_config()
        print(json.dumps(config, indent=2))
        return 0

    repo_root = get_repo_root()

    if args.config:
        config_path = args.config
    else:
        config_path = os.path.join(repo_root, "chainbrand.json")

    if args.verify_only:
        if not os.path.exists(config_path):
            print(f"Error: Config file not found: {config_path}")
            return 1
        with open(config_path) as f:
            config = json.load(f)
        results = verify_all(repo_root, config)
        for r in results:
            mark = "PASS" if r.passed else "FAIL"
            print(f"[{mark}] {r.check_name}: {r.detail}")
        failed = sum(1 for r in results if not r.passed)
        return 1 if failed else 0

    if not os.path.exists(config_path):
        # No config — run wizard
        config = run_wizard()
    else:
        with open(config_path) as f:
            config = json.load(f)

        # If config has all default values, ask if user wants to customize
        if config.get("chain", {}).get("name") == "Dashbase":
            print(f"Found existing config at {config_path}")
            customize = _prompt_bool("The config has default Dashbase values. Customize now?", True)
            if customize:
                config = run_wizard()

    return run_launch(repo_root, config)


if __name__ == "__main__":
    sys.exit(main())
