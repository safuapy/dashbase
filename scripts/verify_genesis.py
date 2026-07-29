#!/usr/bin/env python3
"""Verify genesis block computation by reproducing original Dash genesis hash."""
import struct
import x11_hash

# Original Dash genesis parameters
N_TIME = 1390095618
N_NONCE = 28917698
N_BITS = 0x1e0ffff0
N_VERSION = 1

# Original Dash merkle root (big-endian display format)
EXPECTED_MERKLE = "e0028eb9648db56b1ac77cf090b99048a8007e2bb64b68f092c03c7f56a662c7"
EXPECTED_HASH = "00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6"

# Merkle root in little-endian (as stored in block header)
merkle_root_le = bytes.fromhex(EXPECTED_MERKLE)[::-1]

# Create 80-byte header
header = struct.pack("<i", N_VERSION)           # nVersion
header += b"\x00" * 32                           # hashPrevBlock (null)
header += merkle_root_le                          # hashMerkleRoot (LE)
header += struct.pack("<I", N_TIME)              # nTime
header += struct.pack("<I", N_BITS)              # nBits
header += struct.pack("<I", N_NONCE)             # nNonce

print(f"Header hex: {header.hex()}")
print(f"Header length: {len(header)}")

# Compute X11 hash
block_hash = x11_hash.getPoWHash(header)
hash_hex = block_hash[::-1].hex()  # Convert to big-endian display

print(f"Computed hash: 0x{hash_hex}")
print(f"Expected hash: 0x{EXPECTED_HASH}")
print(f"Match: {hash_hex == EXPECTED_HASH}")
