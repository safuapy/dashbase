#!/usr/bin/env python3
"""
Dashbase Spork Key Generator

Generates ECDSA key pairs for spork signing on each network.
Spork keys are standard Bitcoin-style secp256k1 keys (NOT BLS).

Output for each network:
  - WIF-compressed private key (for -sporkkey= in dashbase.conf)
  - Dashbase address (for vSporkAddresses in chainparams.cpp)

Address version bytes:
  Mainnet:  PUBKEY_ADDRESS = 76  (prefix 'X')
  Testnet:  PUBKEY_ADDRESS = 140 (prefix 'y')
  Devnet:   PUBKEY_ADDRESS = 140 (prefix 'y')
  Regtest:  PUBKEY_ADDRESS = 140 (prefix 'y')

Private key WIF prefix:
  Mainnet:  SECRET_KEY = 204 (prefix '7' or 'X')
  Testnet/Devnet/Regtest: SECRET_KEY = 239 (prefix '9' or 'c')
"""

import hashlib
import os
import sys

# --- secp256k1 via Python's ecdsa library or fallback to hashlib ---
try:
    import ecdsa
    HAVE_ECDSA = True
except ImportError:
    HAVE_ECDSA = False
    print("WARNING: 'ecdsa' library not found. Install with: pip install ecdsa", file=sys.stderr)


# --- Base58 encoding ---
B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_encode(data: bytes) -> str:
    """Encode bytes to Base58Check string (without checksum)."""
    num = int.from_bytes(data, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = B58_ALPHABET[rem] + encoded
    # Leading zero bytes -> '1' prefix
    for byte in data:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded


def base58check_encode(payload: bytes) -> str:
    """Encode bytes with 4-byte SHA256d checksum."""
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return base58_encode(payload + checksum)


def wif_encode(privkey_bytes: bytes, testnet: bool) -> str:
    """Encode private key as WIF (compressed)."""
    prefix = bytes([239]) if testnet else bytes([204])
    payload = prefix + privkey_bytes + bytes([0x01])  # 0x01 = compressed
    return base58check_encode(payload)


def address_encode(pubkey_bytes: bytes, testnet: bool) -> str:
    """Derive Dashbase address from compressed public key."""
    prefix = bytes([140]) if testnet else bytes([76])
    sha256 = hashlib.sha256(pubkey_bytes).digest()
    ripemd160 = hashlib.new("ripemd160", sha256).digest()
    return base58check_encode(prefix + ripemd160)


def generate_keypair():
    """Generate a secp256k1 key pair. Returns (privkey_bytes, compressed_pubkey_bytes)."""
    if HAVE_ECDSA:
        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        privkey_bytes = sk.to_string()
        vk = sk.get_verifying_key()
        # Compressed public key
        x = int.from_bytes(vk.to_string()[:32], "big")
        y = int.from_bytes(vk.to_string()[32:], "big")
        prefix = b"\x02" if y % 2 == 0 else b"\x03"
        compressed_pubkey = prefix + x.to_bytes(32, "big")
        return privkey_bytes, compressed_pubkey
    else:
        # Fallback: use os.urandom for private key, but can't derive pubkey without ecdsa
        print("ERROR: Cannot generate keypair without 'ecdsa' library.", file=sys.stderr)
        sys.exit(1)


def main():
    networks = [
        ("mainnet", 76, 204, False),
        ("testnet", 140, 239, True),
        ("devnet", 140, 239, True),
        ("regtest", 140, 239, True),
    ]

    print("=" * 70)
    print("Dashbase Spork Key Generator")
    print("=" * 70)
    print()

    results = {}

    for name, addr_prefix, wif_prefix, is_testnet in networks:
        privkey, pubkey = generate_keypair()
        wif = wif_encode(privkey, is_testnet)
        address = address_encode(pubkey, is_testnet)
        results[name] = {"wif": wif, "address": address}

        print(f"--- {name.upper()} ---")
        print(f"  Private key (WIF):  {wif}")
        print(f"  Spork address:      {address}")
        print()

    print("=" * 70)
    print("USAGE:")
    print()
    print("1. In chainparams.cpp, update vSporkAddresses for each network:")
    for name in ["mainnet", "testnet", "devnet", "regtest"]:
        print(f"   {name:10s}: vSporkAddresses = {{\"{results[name]['address']}\"}};")
    print()
    print("2. In dashbase.conf (for the node that signs sporks):")
    print(f"   mainnet:  sporkkey={results['mainnet']['wif']}")
    print(f"   testnet:  sporkkey={results['testnet']['wif']}")
    print(f"   devnet:   sporkkey={results['devnet']['wif']}")
    print(f"   regtest:  sporkkey={results['regtest']['wif']}")
    print()
    print("3. Keep the private keys SECURE. Anyone with the private key")
    print("   can sign sporks and toggle network features.")
    print("=" * 70)

    # Also output as JSON for scripting
    import json
    print()
    print("--- JSON ---")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
