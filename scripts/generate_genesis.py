#!/usr/bin/env python3
"""Generate genesis block hash for Dash-based chains using X11 algorithm.

Thin CLI wrapper around scripts/lib/genesis.py.

Usage:
  python3 scripts/generate_genesis.py [timestamp]

Replicates the C++ CreateGenesisBlock logic from src/chainparams.cpp.
Verified against original Dash genesis block hash.
"""

import sys
import os

# Add scripts dir to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from lib.genesis import GenesisGenerator, DEFAULT_N_BITS, DEFAULT_N_VERSION, DEFAULT_REWARD, DEFAULT_PSZ_TIMESTAMP, DEFAULT_PUBKEY_HEX


def main():
    n_time = int(sys.argv[1]) if len(sys.argv) > 1 else 1753734000

    print(f"Generating genesis block")
    print(f"  Timestamp: {n_time}")
    print(f"  Bits: 0x{DEFAULT_N_BITS:08x}")
    print(f"  Version: {DEFAULT_N_VERSION}")
    print(f"  Reward: {DEFAULT_REWARD} satoshis")
    print()

    # First verify against original Dash genesis
    print("=== Verifying against original Dash genesis ===")
    if not GenesisGenerator.verify_against_dash():
        print("ERROR: Verification failed, aborting genesis generation")
        sys.exit(1)
    print("  Verification passed!")
    print()

    # Now generate with our timestamp
    print(f"=== Generating genesis (nTime={n_time}) ===")

    gen = GenesisGenerator(
        n_time=n_time,
        n_bits=DEFAULT_N_BITS,
        n_version=DEFAULT_N_VERSION,
        reward=DEFAULT_REWARD,
        psz_timestamp=DEFAULT_PSZ_TIMESTAMP,
        pubkey_hex=DEFAULT_PUBKEY_HEX,
    )

    def progress(nonce, rate):
        print(f"\r  Tried {nonce:,} nonces ({rate:.0f} H/s)...", end="", flush=True)

    result = gen.mine(progress_callback=progress)

    print()
    print()
    print("FOUND GENESIS BLOCK!")
    print(f"  Nonce:        {result.nonce}")
    print(f"  Hash:         0x{result.hash_hex}")
    print(f"  Merkle Root:  0x{result.merkle_root_hex}")
    print(f"  Time:         {result.elapsed_seconds:.1f}s")
    print()
    print("Add to chainparams.cpp:")
    print(f'  {gen.generate_cpp_snippet(result)}')


if __name__ == "__main__":
    main()
