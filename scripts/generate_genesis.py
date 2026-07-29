#!/usr/bin/env python3
"""Generate genesis block hash for Dashbase using X11 algorithm.

Replicates the C++ CreateGenesisBlock logic from src/chainparams.cpp.
"""
import struct
import hashlib
import x11_hash
import time
import sys

# Genesis parameters from chainparams.cpp
PSZ_TIMESTAMP = b"Wired 09/Jan/2014 The Grand Experiment Goes Live: Overstock.com Is Now Accepting Bitcoins"
PUBKEY = bytes.fromhex("040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9")
GENESIS_REWARD = 5000000000  # 50 * COIN
N_BITS = 0x1e0ffff0
N_VERSION = 1
N_TIME = int(sys.argv[1]) if len(sys.argv) > 1 else 1753734000

def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def create_coinbase_tx():
    """Create the genesis coinbase transaction (Dash/Bitcoin format)."""
    # txNew.nVersion = 1
    tx = struct.pack("<i", 1)  # version

    # vin.resize(1)
    tx += struct.pack("<B", 1)  # 1 input

    # vin[0].prevout (null hash + 0xffffffff)
    tx += b"\x00" * 32  # prev txid
    tx += struct.pack("<I", 0xffffffff)  # prev vout

    # vin[0].scriptSig = CScript() << 486604799 << CScriptNum(4) << pszTimestamp
    # 486604799 = 0x1d00ffff in little-endian
    # CScriptNum(4) = 0x04
    script_sig = struct.pack("<I", 486604799)  # 4 bytes LE
    script_sig += b"\x04"  # CScriptNum(4)
    script_sig += struct.pack("<B", len(PSZ_TIMESTAMP))  # push len
    script_sig += PSZ_TIMESTAMP

    tx += struct.pack("<B", len(script_sig))  # scriptSig length
    tx += script_sig

    # vin[0].nSequence
    tx += struct.pack("<I", 0xffffffff)

    # vout.resize(1)
    tx += struct.pack("<B", 1)  # 1 output

    # vout[0].nValue = 5000000000
    tx += struct.pack("<q", GENESIS_REWARD)

    # vout[0].scriptPubKey = CScript() << pubkey << OP_CHECKSIG
    script_pubkey = struct.pack("<B", len(PUBKEY))  # push len
    script_pubkey += PUBKEY
    script_pubkey += b"\xac"  # OP_CHECKSIG

    tx += struct.pack("<B", len(script_pubkey))  # scriptPubKey length
    tx += script_pubkey

    # vout[0].nRounds = 0 (Dash-specific, added in Dash's CTxOut serialization)
    # Actually in Dash v18, CTxOut doesn't have nRounds in serialization for non-coinbase
    # Let's check - Dash uses a special serialization. For genesis, it should be standard.

    return tx

def create_block_header(merkle_root, n_time, n_nonce, n_bits, n_version):
    """Create 80-byte block header for X11 hashing."""
    header = struct.pack("<i", n_version)           # nVersion
    header += b"\x00" * 32                           # hashPrevBlock (null)
    header += merkle_root                            # hashMerkleRoot (32 bytes, LE)
    header += struct.pack("<I", n_time)              # nTime
    header += struct.pack("<I", n_bits)              # nBits
    header += struct.pack("<I", n_nonce)             # nNonce
    return header

def compute_merkle_root(tx_bytes):
    """Compute merkle root of a single transaction.
    Returns little-endian bytes (as stored in block header)."""
    tx_hash = double_sha256(tx_bytes)  # big-endian
    return tx_hash[::-1]  # reverse to little-endian for header

def bits_to_target(bits):
    """Convert compact bits to target."""
    exponent = bits >> 24
    mantissa = bits & 0x007fffff
    if exponent <= 3:
        target = mantissa >> (8 * (3 - exponent))
    else:
        target = mantissa << (8 * (exponent - 3))
    return target

def main():
    print(f"Generating genesis block for Dashbase")
    print(f"  Timestamp: {N_TIME}")
    print(f"  Bits: 0x{N_BITS:08x}")
    print(f"  Version: {N_VERSION}")
    print(f"  Reward: {GENESIS_REWARD} satoshis")
    print()

    # Create coinbase tx
    coinbase_tx = create_coinbase_tx()
    print(f"Coinbase TX: {coinbase_tx.hex()}")

    # Compute merkle root
    merkle_root = compute_merkle_root(coinbase_tx)
    print(f"Merkle Root: 0x{merkle_root[::-1].hex()}")  # display as BE

    # Target
    target = bits_to_target(N_BITS)
    target_hex = f"{target:064x}"
    print(f"Target:       0x{target_hex}")
    print()

    # Mine - search for nonce
    print("Mining genesis block (searching for valid nonce)...")
    start_time = time.time()

    # Try nonces starting from 0
    batch_size = 100000
    nonce = 0

    while True:
        header = create_block_header(merkle_root, N_TIME, nonce, N_BITS, N_VERSION)
        block_hash = x11_hash.getPoWHash(header)

        # Check if hash < target (compare as big-endian hex)
        hash_int = int.from_bytes(block_hash, 'little')
        if hash_int < target:
            elapsed = time.time() - start_time
            print()
            print(f"FOUND GENESIS BLOCK!")
            print(f"  Nonce:        {nonce}")
            print(f"  Hash:         0x{block_hash[::-1].hex()}")
            print(f"  Merkle Root:  0x{merkle_root[::-1].hex()}")
            print(f"  Time:         {elapsed:.1f}s")
            print()
            print(f"Add to chainparams.cpp:")
            print(f'  assert(consensus.hashGenesisBlock == uint256S("0x{block_hash[::-1].hex()}"));')
            print(f'  assert(genesis.hashMerkleRoot == uint256S("0x{merkle_root[::-1].hex()}"));')
            return

        nonce += 1

        if nonce % batch_size == 0:
            elapsed = time.time() - start_time
            rate = nonce / elapsed if elapsed > 0 else 0
            print(f"\r  Tried {nonce:,} nonces ({rate:.0f} H/s)...", end="", flush=True)

if __name__ == "__main__":
    main()
