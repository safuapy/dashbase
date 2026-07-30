#!/usr/bin/env python3
"""
Spork Key Generator for Dash-based chains.

Thin CLI wrapper around scripts/lib/keys.py.

Generates ECDSA key pairs for spork signing on each network.
Spork keys are standard Bitcoin-style secp256k1 keys (NOT BLS).

Output for each network:
  - WIF-compressed private key (for -sporkkey= in conf file)
  - Chain address (for vSporkAddresses in chainparams.cpp)
"""

import sys
import os
import json

# Add scripts dir to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from lib.keys import SporkKeyGenerator, BLSKeyGenerator


def main():
    gen = SporkKeyGenerator()

    print("=" * 70)
    print("Spork Key Generator")
    print("=" * 70)
    print()

    results = {}
    for net in ["mainnet", "testnet", "devnet", "regtest"]:
        key = gen.generate(net)
        results[net] = {"wif": key.wif, "address": key.address}

        print(f"--- {net.upper()} ---")
        print(f"  Private key (WIF):  {key.wif}")
        print(f"  Spork address:      {key.address}")
        print()

    print("=" * 70)
    print("USAGE:")
    print()
    print("1. In chainparams.cpp, update vSporkAddresses for each network:")
    for name in ["mainnet", "testnet", "devnet", "regtest"]:
        print(f"   {name:10s}: vSporkAddresses = {{\"{results[name]['address']}\"}};")
    print()
    print("2. In your conf file (for the node that signs sporks):")
    for name in ["mainnet", "testnet", "devnet", "regtest"]:
        print(f"   {name:10s}: sporkkey={results[name]['wif']}")
    print()
    print("3. Keep the private keys SECURE. Anyone with the private key")
    print("   can sign sporks and toggle network features.")
    print("=" * 70)

    # Also generate BLS key
    print()
    print("--- BLS Masternode Operator Key ---")
    bls_gen = BLSKeyGenerator()
    bls_key = bls_gen.generate()
    print(f"  Private key: {bls_key.privkey_hex}")
    print(f"  Public key:  {bls_key.pubkey_hex}")
    print()
    print("  Add to conf: masternodeblsprivkey=" + bls_key.privkey_hex)
    print("=" * 70)

    # JSON output for scripting
    print()
    print("--- JSON ---")
    output = {**results, "bls": {"priv": bls_key.privkey_hex, "pub": bls_key.pubkey_hex}}
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
