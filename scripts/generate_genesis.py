#!/usr/bin/env python3
"""Generate genesis block hash for Dashbase using X11 algorithm.

Replicates the C++ CreateGenesisBlock logic from src/chainparams.cpp.
Verified against original Dash genesis block hash.
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

# Original Dash genesis for verification
DASH_TIME = 1390095618
DASH_NONCE = 28917698
DASH_HASH = "00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6"
DASH_MERKLE = "e0028eb9648db56b1ac77cf090b99048a8007e2bb64b68f092c03c7f56a662c7"


def double_sha256(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def script_num_serialize(n):
    """Serialize an integer as a CScriptNum (compact signed little-endian)."""
    if n == 0:
        return b""
    result = []
    neg = n < 0
    absval = -n if neg else n
    while absval:
        result.append(absval & 0xff)
        absval >>= 8
    if result[-1] & 0x80:
        result.append(0x80 if neg else 0x00)
    elif neg:
        result[-1] |= 0x80
    return bytes(result)


def push_data(data):
    """Serialize a push opcode + data as CScript does."""
    n = len(data)
    if n < 0x4c:  # OP_PUSHDATA1
        return bytes([n]) + data
    elif n <= 0xff:
        return b"\x4c" + bytes([n]) + data
    elif n <= 0xffff:
        return b"\x4d" + struct.pack("<H", n) + data
    else:
        return b"\x4e" + struct.pack("<I", n) + data


def create_coinbase_tx():
    """Create the genesis coinbase transaction matching C++ serialization exactly.

    C++ code:
      CMutableTransaction txNew;
      txNew.nVersion = 1;  // int16_t
      txNew.nType = TRANSACTION_NORMAL;  // uint16_t = 0
      txNew.vin.resize(1);
      txNew.vout.resize(1);
      txNew.vin[0].scriptSig = CScript() << 486604799 << CScriptNum(4) << pszTimestamp;
      txNew.vout[0].nValue = genesisReward;
      txNew.vout[0].scriptPubKey = genesisOutputScript;
      // nLockTime = 0 (default)

    CTransaction::Serialize writes:
      int32_t n32bitVersion = nVersion | (nType << 16);  // = 1
      s << n32bitVersion;   // 4 bytes LE
      s << vin;             // vector<CTxIn>
      s << vout;            // vector<CTxOut>
      s << nLockTime;       // 4 bytes LE = 0
      // nVersion=1, not 3, so no vExtraPayload
    """
    tx = b""

    # n32bitVersion = nVersion(1) | nType(0) << 16 = 1, as int32 LE
    tx += struct.pack("<i", 1)

    # vin: compactSize count(1) + CTxIn
    tx += b"\x01"  # 1 input

    # CTxIn: COutPoint + scriptSig + nSequence
    # COutPoint: hash(32 null bytes) + n(uint32 0xffffffff)
    tx += b"\x00" * 32
    tx += struct.pack("<I", 0xffffffff)

    # scriptSig = CScript() << 486604799 << CScriptNum(4) << pszTimestamp
    # << 486604799 (int64_t): not 0/-1/1-16, so serialize as CScriptNum then push
    script_sig = push_data(script_num_serialize(486604799))
    # << CScriptNum(4): getvch() = [0x04], push as vector (no OP_N shortcut for vectors)
    script_sig += push_data(b"\x04")
    # << pszTimestamp: push as vector
    script_sig += push_data(PSZ_TIMESTAMP)

    # scriptSig length (compactSize)
    tx += bytes([len(script_sig)]) if len(script_sig) < 253 else b"\xfd" + struct.pack("<H", len(script_sig))
    tx += script_sig

    # nSequence
    tx += struct.pack("<I", 0xffffffff)

    # vout: compactSize count(1) + CTxOut
    tx += b"\x01"  # 1 output

    # CTxOut: nValue(int64 LE) + scriptPubKey
    tx += struct.pack("<q", GENESIS_REWARD)

    # scriptPubKey = CScript() << pubkey << OP_CHECKSIG
    script_pubkey = push_data(PUBKEY) + b"\xac"  # OP_CHECKSIG = 0xac
    tx += bytes([len(script_pubkey)]) if len(script_pubkey) < 253 else b"\xfd" + struct.pack("<H", len(script_pubkey))
    tx += script_pubkey

    # nLockTime = 0 (uint32 LE) — THIS WAS MISSING
    tx += struct.pack("<I", 0)

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
    For a single tx, merkle root = txid = double_sha256(serialized_tx).
    Returns little-endian bytes (as stored in block header)."""
    tx_hash = double_sha256(tx_bytes)
    return tx_hash  # already in LE storage order


def bits_to_target(bits):
    """Convert compact bits to target."""
    exponent = bits >> 24
    mantissa = bits & 0x007fffff
    if exponent <= 3:
        target = mantissa >> (8 * (3 - exponent))
    else:
        target = mantissa << (8 * (exponent - 3))
    return target


def verify():
    """Verify our serialization matches the original Dash genesis."""
    print("=== Verifying against original Dash genesis ===")
    coinbase_tx = create_coinbase_tx()
    merkle_root = compute_merkle_root(coinbase_tx)
    merkle_hex = merkle_root[::-1].hex()  # display as BE

    print(f"  Coinbase TX hex: {coinbase_tx.hex()}")
    print(f"  Computed merkle: 0x{merkle_hex}")
    print(f"  Expected merkle: 0x{DASH_MERKLE}")

    if merkle_hex != DASH_MERKLE:
        print("  MERKLE ROOT MISMATCH!")
        return False

    header = create_block_header(merkle_root, DASH_TIME, DASH_NONCE, N_BITS, N_VERSION)
    block_hash = x11_hash.getPoWHash(header)
    hash_hex = block_hash[::-1].hex()

    print(f"  Computed hash:   0x{hash_hex}")
    print(f"  Expected hash:   0x{DASH_HASH}")

    if hash_hex != DASH_HASH:
        print("  HASH MISMATCH!")
        return False

    print("  ✅ Verification passed!")
    print()
    return True


def main():
    print(f"Generating genesis block for Dashbase")
    print(f"  Timestamp: {N_TIME}")
    print(f"  Bits: 0x{N_BITS:08x}")
    print(f"  Version: {N_VERSION}")
    print(f"  Reward: {GENESIS_REWARD} satoshis")
    print()

    # First verify against original Dash genesis
    if not verify():
        print("ERROR: Verification failed, aborting genesis generation")
        sys.exit(1)

    # Now generate with our timestamp
    print(f"=== Generating genesis for Dashbase (nTime={N_TIME}) ===")

    coinbase_tx = create_coinbase_tx()
    merkle_root = compute_merkle_root(coinbase_tx)
    print(f"  Merkle Root: 0x{merkle_root[::-1].hex()}")

    target = bits_to_target(N_BITS)
    target_hex = f"{target:064x}"
    print(f"  Target:      0x{target_hex}")
    print()

    print("Mining genesis block (searching for valid nonce)...")
    start_time = time.time()

    batch_size = 100000
    nonce = 0

    while True:
        header = create_block_header(merkle_root, N_TIME, nonce, N_BITS, N_VERSION)
        block_hash = x11_hash.getPoWHash(header)

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
            print(f'  genesis = CreateGenesisBlock({N_TIME}, {nonce}, 0x{N_BITS:08x}, 1, 50 * COIN);')
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
