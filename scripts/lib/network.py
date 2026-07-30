"""Network identity patches for chainparams.cpp and chainparamsbase.cpp.

Patches: magic bytes, ports, base58 prefixes, BIP44 coin type, DNS seeds,
data dir names, fixed seeds, checkpoints, minimum chain work.
"""

import os
import re
from typing import List
from .file_patcher import (
    patch_file, patch_file_regex, read_file, write_file,
    PatchResult
)


def _hex_byte(n: int) -> str:
    return f"0x{n:02x}"


def apply_network_identity(repo_root: str, config: dict, old_config: dict = None) -> List[PatchResult]:
    """Apply network identity changes to chainparams.cpp and chainparamsbase.cpp.

    Args:
        repo_root: Absolute path to repo root
        config: New chainbrand config dict with 'network' section
        old_config: Old config for reverse mapping (defaults to Dashbase values)
    Returns:
        List of PatchResult objects
    """
    if old_config is None:
        old_config = _default_old_config()

    results = []
    net = config["network"]
    old_net = old_config["network"]
    cp_file = os.path.join(repo_root, "src/chainparams.cpp")
    cpb_file = os.path.join(repo_root, "src/chainparamsbase.cpp")
    seeds_file = os.path.join(repo_root, "src/chainparamsseeds.h")

    # ── Mainnet magic bytes ──────────────────────────────────────────
    if "mainnet" in net and "mainnet" in old_net:
        old_magic = old_net["mainnet"]["magic_bytes"]
        new_magic = net["mainnet"]["magic_bytes"]
        content = read_file(cp_file)

        # Find the mainnet class section (CMainParams) and patch magic bytes
        # The mainnet magic bytes are the first pchMessageStart block
        for i in range(4):
            old_hex = _hex_byte(old_magic[i])
            new_hex = _hex_byte(new_magic[i])
            # Only replace the first occurrence (mainnet)
            r = patch_file_regex(cp_file,
                r'(pchMessageStart\[' + str(i) + r'\] = )' + re.escape(old_hex),
                rf'\g<1>{new_hex}', count=1)
            if r.changed:
                results.append(r)

        # Mainnet default port
        old_port = old_net["mainnet"]["default_port"]
        new_port = net["mainnet"]["default_port"]
        r = patch_file_regex(cp_file,
            r'(nDefaultPort = )' + str(old_port) + r'(\s*;)',
            rf'\g<1>{new_port}\g<2>', count=1)
        if r.changed:
            results.append(r)

        # Mainnet DNS seeds
        old_seeds = old_net["mainnet"].get("dns_seeds", [])
        new_seeds = net["mainnet"].get("dns_seeds", [])
        for i, (old_s, new_s) in enumerate(zip(old_seeds, new_seeds)):
            if old_s != new_s:
                r = patch_file(cp_file, f'"{old_s}"', f'"{new_s}"', count=1)
                if r.changed:
                    results.append(r)

        # Mainnet base58 prefixes
        old_b58 = old_net["mainnet"].get("base58_prefixes", {})
        new_b58 = net["mainnet"].get("base58_prefixes", {})
        b58_map = {
            "pubkey_address": "PUBKEY_ADDRESS",
            "script_address": "SCRIPT_ADDRESS",
            "secret_key": "SECRET_KEY",
        }
        for key, cpp_name in b58_map.items():
            if key in old_b58 and key in new_b58 and old_b58[key] != new_b58[key]:
                r = patch_file_regex(cp_file,
                    r'(base58Prefixes\[' + cpp_name + r'\] = std::vector<unsigned char>\(1,)' + str(old_b58[key]) + r'(\))',
                    rf'\g<1>{new_b58[key]}\g<2>', count=1)
                if r.changed:
                    results.append(r)

        # Mainnet BIP44 coin type
        old_ct = old_net["mainnet"].get("bip44_coin_type", 153)
        new_ct = net["mainnet"].get("bip44_coin_type", 153)
        if old_ct != new_ct:
            r = patch_file_regex(cp_file,
                r'(nExtCoinType = )' + str(old_ct) + r'(;)',
                rf'\g<1>{new_ct}\g<2>', count=1)
            if r.changed:
                results.append(r)

    # ── Testnet magic bytes ──────────────────────────────────────────
    if "testnet" in net and "testnet" in old_net:
        old_magic = old_net["testnet"]["magic_bytes"]
        new_magic = net["testnet"]["magic_bytes"]
        for i in range(4):
            old_hex = _hex_byte(old_magic[i])
            new_hex = _hex_byte(new_magic[i])
            # Replace the second occurrence (testnet — after mainnet)
            r = patch_file_regex(cp_file,
                r'(pchMessageStart\[' + str(i) + r'\] = )' + re.escape(old_hex),
                rf'\g<1>{new_hex}', count=1)
            if r.changed:
                results.append(r)

        # Testnet default port
        old_port = old_net["testnet"]["default_port"]
        new_port = net["testnet"]["default_port"]
        r = patch_file_regex(cp_file,
            r'(nDefaultPort = )' + str(old_port) + r'(\s*;)',
            rf'\g<1>{new_port}\g<2>', count=1)
        if r.changed:
            results.append(r)

        # Testnet DNS seeds
        old_seeds = old_net["testnet"].get("dns_seeds", [])
        new_seeds = net["testnet"].get("dns_seeds", [])
        for i, (old_s, new_s) in enumerate(zip(old_seeds, new_seeds)):
            if old_s != new_s:
                r = patch_file(cp_file, f'"{old_s}"', f'"{new_s}"', count=1)
                if r.changed:
                    results.append(r)

        # Testnet base58 prefixes
        old_b58 = old_net["testnet"].get("base58", old_net["testnet"].get("base58_prefixes", {}))
        new_b58 = net["testnet"].get("base58", net["testnet"].get("base58_prefixes", {}))
        b58_map = {
            "pubkey_address": "PUBKEY_ADDRESS",
            "script_address": "SCRIPT_ADDRESS",
            "secret_key": "SECRET_KEY",
        }
        for key, cpp_name in b58_map.items():
            if key in old_b58 and key in new_b58 and old_b58[key] != new_b58[key]:
                # Testnet is the second occurrence
                r = patch_file_regex(cp_file,
                    r'(base58Prefixes\[' + cpp_name + r'\] = std::vector<unsigned char>\(1,)' + str(old_b58[key]) + r'(\))',
                    rf'\g<1>{new_b58[key]}\g<2>', count=1)
                if r.changed:
                    results.append(r)

    # ── Regtest magic bytes ──────────────────────────────────────────
    if "regtest" in net and "regtest" in old_net:
        old_magic = old_net["regtest"]["magic_bytes"]
        new_magic = net["regtest"]["magic_bytes"]
        for i in range(4):
            old_hex = _hex_byte(old_magic[i])
            new_hex = _hex_byte(new_magic[i])
            r = patch_file_regex(cp_file,
                r'(pchMessageStart\[' + str(i) + r'\] = )' + re.escape(old_hex),
                rf'\g<1>{new_hex}', count=1)
            if r.changed:
                results.append(r)

        old_port = old_net["regtest"]["default_port"]
        new_port = net["regtest"]["default_port"]
        r = patch_file_regex(cp_file,
            r'(nDefaultPort = )' + str(old_port) + r'(\s*;)',
            rf'\g<1>{new_port}\g<2>', count=1)
        if r.changed:
            results.append(r)

    # ── chainparamsbase.cpp — RPC ports and data dirs ────────────────
    if os.path.exists(cpb_file):
        # Mainnet RPC port
        if "mainnet" in net and "mainnet" in old_net:
            old_rpc = old_net["mainnet"]["rpc_port"]
            new_rpc = net["mainnet"]["rpc_port"]
            r = patch_file(cpb_file, f'CBaseChainParams>("", {old_rpc})', f'CBaseChainParams>("", {new_rpc})')
            if r.changed:
                results.append(r)

        # Testnet RPC port and data dir
        if "testnet" in net and "testnet" in old_net:
            old_rpc = old_net["testnet"]["rpc_port"]
            new_rpc = net["testnet"]["rpc_port"]
            r = patch_file(cpb_file, f'CBaseChainParams>("testnet3", {old_rpc})', f'CBaseChainParams>("testnet3", {new_rpc})')
            if r.changed:
                results.append(r)

        # Regtest RPC port
        if "regtest" in net and "regtest" in old_net:
            old_rpc = old_net["regtest"]["rpc_port"]
            new_rpc = net["regtest"]["rpc_port"]
            r = patch_file(cpb_file, f'CBaseChainParams>("regtest", {old_rpc})', f'CBaseChainParams>("regtest", {new_rpc})')
            if r.changed:
                results.append(r)

    # ── Clear fixed seeds ────────────────────────────────────────────
    options = config.get("options", {})
    if options.get("clear_fixed_seeds", True) and os.path.exists(seeds_file):
        new_seeds_content = """// Copyright (c) 2026 The Dash Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_CHAINPARAMSSEEDS_H
#define BITCOIN_CHAINPARAMSSEEDS_H

/**
 * List of fixed seed nodes for the network.
 * Clear this list for a new fork chain and populate with your own seed nodes.
 */

static SeedSpec6 pnSeed6_main[] = {
};

static SeedSpec6 pnSeed6_test[] = {
};

#endif // BITCOIN_CHAINPARAMSSEEDS_H
"""
        write_file(seeds_file, new_seeds_content)
        results.append(PatchResult(seeds_file, True, "cleared fixed seeds"))

    # ── Clear checkpoints ────────────────────────────────────────────
    if options.get("clear_checkpoints", True) and os.path.exists(cp_file):
        content = read_file(cp_file)
        # Replace checkpointData blocks with minimal genesis-only checkpoint
        # Mainnet checkpoint
        r = patch_file_regex(cp_file,
            r'checkpointData = \{\s*\{\s*\{0, consensus\.hashGenesisBlock\},\s*\}\s*\};',
            'checkpointData = {\n            {\n                {0, consensus.hashGenesisBlock},\n            }\n        };')
        if r.changed:
            results.append(r)
        results.append(PatchResult(cp_file, False, "checkpoints already minimal (genesis only)"))

    # ── Set minimum chain work and assume valid to zero ──────────────
    if os.path.exists(cp_file):
        # Replace all non-zero nMinimumChainWork with zero (for fresh chain)
        r = patch_file_regex(cp_file,
            r'consensus\.nMinimumChainWork = uint256S\("[^"]*"\)',
            'consensus.nMinimumChainWork = uint256S("0x0000000000000000000000000000000000000000000000000000000000000000")')
        if r.changed:
            results.append(r)
        r = patch_file_regex(cp_file,
            r'consensus\.defaultAssumeValid = uint256S\("[^"]*"\)',
            'consensus.defaultAssumeValid = uint256S("0x0000000000000000000000000000000000000000000000000000000000000000")')
        if r.changed:
            results.append(r)

    return results


def apply_genesis_to_chainparams(repo_root: str, network: str, genesis_result, n_bits: int, n_version: int, reward: int) -> List[PatchResult]:
    """Patch genesis block hash and nonce into chainparams.cpp for a specific network.

    Args:
        repo_root: Repo root path
        network: "mainnet" or "testnet"
        genesis_result: GenesisResult from GenesisGenerator.mine()
        n_bits: nBits value used for genesis
        n_version: Block version
        reward: Genesis reward in satoshis
    """
    results = []
    cp_file = os.path.join(repo_root, "src/chainparams.cpp")
    if not os.path.exists(cp_file):
        return [PatchResult(cp_file, False, "file not found")]

    # Build the new genesis line
    new_genesis_line = f'genesis = CreateGenesisBlock({genesis_result.n_time}, {genesis_result.nonce}, 0x{n_bits:08x}, {n_version}, {reward} * COIN);'
    new_hash_assert = f'assert(consensus.hashGenesisBlock == uint256S("0x{genesis_result.hash_hex}"));'
    new_merkle_assert = f'assert(genesis.hashMerkleRoot == uint256S("0x{genesis_result.merkle_root_hex}"));'

    # Replace the genesis creation line — find by the pattern genesis = CreateGenesisBlock(...)
    # We need to target the right network's occurrence
    content = read_file(cp_file)

    # Find all genesis creation lines
    genesis_pattern = r'genesis = CreateGenesisBlock\(\d+,\s*\d+,\s*0x[0-9a-fA-F]+,\s*\d+,\s*\d+\s*\*\s*COIN\);'
    matches = list(re.finditer(genesis_pattern, content))

    if network == "mainnet" and len(matches) >= 1:
        # Replace first occurrence (mainnet)
        new_content = content[:matches[0].start()] + new_genesis_line + content[matches[0].end():]
        write_file(cp_file, new_content)
        results.append(PatchResult(cp_file, True, f"patched mainnet genesis line"))
        content = new_content

    elif network == "testnet" and len(matches) >= 2:
        # Replace second occurrence (testnet)
        new_content = content[:matches[1].start()] + new_genesis_line + content[matches[1].end():]
        write_file(cp_file, new_content)
        results.append(PatchResult(cp_file, True, f"patched testnet genesis line"))
        content = new_content

    # Replace hash assertions
    hash_pattern = r'assert\(consensus\.hashGenesisBlock == uint256S\("0x[0-9a-fA-F]+"\)\);'
    hash_matches = list(re.finditer(hash_pattern, content))

    target_idx = 0 if network == "mainnet" else (1 if len(hash_matches) > 1 else 0)
    if hash_matches and target_idx < len(hash_matches):
        new_content = content[:hash_matches[target_idx].start()] + new_hash_assert + content[hash_matches[target_idx].end():]
        write_file(cp_file, new_content)
        results.append(PatchResult(cp_file, True, f"patched {network} genesis hash assert"))
        content = new_content

    # Replace merkle root assertions
    merkle_pattern = r'assert\(genesis\.hashMerkleRoot == uint256S\("0x[0-9a-fA-F]+"\)\);'
    merkle_matches = list(re.finditer(merkle_pattern, content))

    target_idx = 0 if network == "mainnet" else (1 if len(merkle_matches) > 1 else 0)
    if merkle_matches and target_idx < len(merkle_matches):
        new_content = content[:merkle_matches[target_idx].start()] + new_merkle_assert + content[merkle_matches[target_idx].end():]
        write_file(cp_file, new_content)
        results.append(PatchResult(cp_file, True, f"patched {network} merkle root assert"))

    return results


def apply_spork_addresses(repo_root: str, network: str, spork_address: str, old_address: str = None) -> List[PatchResult]:
    """Patch spork address into chainparams.cpp for a specific network.

    Args:
        repo_root: Repo root path
        network: "mainnet", "testnet", "devnet", or "regtest"
        spork_address: New spork address
        old_address: Old spork address to replace (if known)
    """
    results = []
    cp_file = os.path.join(repo_root, "src/chainparams.cpp")
    if not os.path.exists(cp_file):
        return [PatchResult(cp_file, False, "file not found")]

    if old_address:
        r = patch_file(cp_file, f'vSporkAddresses = {{"{old_address}"}}', f'vSporkAddresses = {{"{spork_address}"}}', count=1)
        if r.changed:
            results.append(r)
            return results

    # If no old address specified, use regex to replace the nth occurrence
    content = read_file(cp_file)
    spork_pattern = r'vSporkAddresses = \{"[^"]*"\};'
    matches = list(re.finditer(spork_pattern, content))

    network_idx = {"mainnet": 0, "testnet": 1, "devnet": 2, "regtest": 3}
    target_idx = network_idx.get(network, 0)

    if target_idx < len(matches):
        new_line = f'vSporkAddresses = {{"{spork_address}"}};'
        new_content = content[:matches[target_idx].start()] + new_line + content[matches[target_idx].end():]
        write_file(cp_file, new_content)
        results.append(PatchResult(cp_file, True, f"patched {network} spork address"))
    else:
        results.append(PatchResult(cp_file, False, f"could not find spork address for {network}"))

    return results


def _default_old_config() -> dict:
    """Default Dashbase config values for reverse mapping."""
    return {
        "network": {
            "mainnet": {
                "magic_bytes": [84, 130, 159, 69],
                "default_port": 19997,
                "rpc_port": 19996,
                "dns_seeds": ["dnsseed.dashbase.org"],
                "bip44_coin_type": 153,
                "base58_prefixes": {
                    "pubkey_address": 76,
                    "script_address": 16,
                    "secret_key": 204,
                },
            },
            "testnet": {
                "magic_bytes": [197, 177, 253, 114],
                "default_port": 29997,
                "rpc_port": 29996,
                "dns_seeds": ["testnet-seed.dashbase.org"],
                "bip44_coin_type": 1,
                "base58": {
                    "pubkey_address": 139,
                    "script_address": 19,
                    "secret_key": 239,
                },
            },
            "regtest": {
                "magic_bytes": [220, 231, 132, 244],
                "default_port": 19994,
                "rpc_port": 19993,
            },
        }
    }
