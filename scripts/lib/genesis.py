"""Genesis block generation for Dash-based chains using X11 hashing.

Refactored from scripts/generate_genesis.py into a reusable class.
"""

import struct
import hashlib
import time
import sys
from dataclasses import dataclass
from typing import Tuple


# Default genesis parameters (Dash original)
DEFAULT_PSZ_TIMESTAMP = b"Wired 09/Jan/2014 The Grand Experiment Goes Live: Overstock.com Is Now Accepting Bitcoins"
DEFAULT_PUBKEY_HEX = "040184710fa689ad5023690c80f3a49c8f13f8d45b8c857fbcbc8bc4a8e4d3eb4b10f4d4604fa08dce601aaf0f470216fe1b51850b4acf21b179c45070ac7b03a9"
DEFAULT_N_BITS = 0x1e0ffff0
DEFAULT_N_VERSION = 1
DEFAULT_REWARD = 5000000000  # 50 * COIN

# Original Dash genesis for verification
DASH_TIME = 1390095618
DASH_NONCE = 28917698
DASH_HASH = "00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6"
DASH_MERKLE = "e0028eb9648db56b1ac77cf090b99048a8007e2bb64b68f092c03c7f56a662c7"


@dataclass
class GenesisResult:
    nonce: int
    hash_hex: str
    merkle_root_hex: str
    n_time: int
    elapsed_seconds: float


def _double_sha256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def _script_num_serialize(n: int) -> bytes:
    if n == 0:
        return b""
    result = []
    neg = n < 0
    absval = -n if neg else n
    while absval:
        result.append(absval & 0xff)
        absval >>= 8
    if result and result[-1] & 0x80:
        result.append(0x80 if neg else 0x00)
    elif neg:
        result[-1] |= 0x80
    return bytes(result)


def _push_data(data: bytes) -> bytes:
    n = len(data)
    if n < 0x4c:
        return bytes([n]) + data
    elif n <= 0xff:
        return b"\x4c" + bytes([n]) + data
    elif n <= 0xffff:
        return b"\x4d" + struct.pack("<H", n) + data
    else:
        return b"\x4e" + struct.pack("<I", n) + data


def _create_coinbase_tx(psz_timestamp: bytes, pubkey_hex: str, reward: int) -> bytes:
    pubkey = bytes.fromhex(pubkey_hex)
    tx = b""
    tx += struct.pack("<i", 1)  # n32bitVersion
    tx += b"\x01"  # 1 input
    tx += b"\x00" * 32  # COutPoint hash
    tx += struct.pack("<I", 0xffffffff)  # COutPoint n
    script_sig = _push_data(_script_num_serialize(486604799))
    script_sig += _push_data(b"\x04")
    script_sig += _push_data(psz_timestamp)
    tx += bytes([len(script_sig)]) if len(script_sig) < 253 else b"\xfd" + struct.pack("<H", len(script_sig))
    tx += script_sig
    tx += struct.pack("<I", 0xffffffff)  # nSequence
    tx += b"\x01"  # 1 output
    tx += struct.pack("<q", reward)
    script_pubkey = _push_data(pubkey) + b"\xac"  # OP_CHECKSIG
    tx += bytes([len(script_pubkey)]) if len(script_pubkey) < 253 else b"\xfd" + struct.pack("<H", len(script_pubkey))
    tx += script_pubkey
    tx += struct.pack("<I", 0)  # nLockTime
    return tx


def _create_block_header(merkle_root: bytes, n_time: int, n_nonce: int, n_bits: int, n_version: int) -> bytes:
    header = struct.pack("<i", n_version)
    header += b"\x00" * 32
    header += merkle_root
    header += struct.pack("<I", n_time)
    header += struct.pack("<I", n_bits)
    header += struct.pack("<I", n_nonce)
    return header


def _compute_merkle_root(tx_bytes: bytes) -> bytes:
    return _double_sha256(tx_bytes)


def _bits_to_target(bits: int) -> int:
    exponent = bits >> 24
    mantissa = bits & 0x007fffff
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


class GenesisGenerator:
    """Generate genesis blocks for Dash-based chains using X11 hashing."""

    def __init__(
        self,
        n_time: int = 0,
        n_bits: int = DEFAULT_N_BITS,
        n_version: int = DEFAULT_N_VERSION,
        reward: int = DEFAULT_REWARD,
        psz_timestamp: bytes = DEFAULT_PSZ_TIMESTAMP,
        pubkey_hex: str = DEFAULT_PUBKEY_HEX,
    ):
        self.n_time = n_time
        self.n_bits = n_bits
        self.n_version = n_version
        self.reward = reward
        self.psz_timestamp = psz_timestamp
        self.pubkey_hex = pubkey_hex

    @staticmethod
    def verify_against_dash() -> bool:
        """Verify our serialization matches the original Dash genesis block."""
        try:
            import x11_hash
        except ImportError:
            print("WARNING: x11_hash module not found, skipping verification")
            return True

        coinbase_tx = _create_coinbase_tx(DEFAULT_PSZ_TIMESTAMP, DEFAULT_PUBKEY_HEX, DEFAULT_REWARD)
        merkle_root = _compute_merkle_root(coinbase_tx)
        merkle_hex = merkle_root[::-1].hex()

        if merkle_hex != DASH_MERKLE:
            print(f"  MERKLE ROOT MISMATCH: got {merkle_hex}, expected {DASH_MERKLE}")
            return False

        header = _create_block_header(merkle_root, DASH_TIME, DASH_NONCE, DEFAULT_N_BITS, DEFAULT_N_VERSION)
        block_hash = x11_hash.getPoWHash(header)
        hash_hex = block_hash[::-1].hex()

        if hash_hex != DASH_HASH:
            print(f"  HASH MISMATCH: got {hash_hex}, expected {DASH_HASH}")
            return False

        return True

    def mine(self, progress_callback=None) -> GenesisResult:
        """Mine a genesis block. Returns GenesisResult with nonce, hash, merkle root."""
        try:
            import x11_hash
        except ImportError:
            print("ERROR: x11_hash module is required for genesis mining.")
            print("Install with: pip install x11-hash")
            sys.exit(1)

        if self.n_time == 0:
            self.n_time = int(time.time())

        coinbase_tx = _create_coinbase_tx(self.psz_timestamp, self.pubkey_hex, self.reward)
        merkle_root = _compute_merkle_root(coinbase_tx)
        merkle_hex = merkle_root[::-1].hex()

        target = _bits_to_target(self.n_bits)
        start_time = time.time()
        nonce = 0
        batch_size = 100000

        while True:
            header = _create_block_header(merkle_root, self.n_time, nonce, self.n_bits, self.n_version)
            block_hash = x11_hash.getPoWHash(header)
            hash_int = int.from_bytes(block_hash, "little")

            if hash_int < target:
                elapsed = time.time() - start_time
                hash_hex = block_hash[::-1].hex()
                return GenesisResult(
                    nonce=nonce,
                    hash_hex=hash_hex,
                    merkle_root_hex=merkle_hex,
                    n_time=self.n_time,
                    elapsed_seconds=elapsed,
                )

            nonce += 1
            if nonce % batch_size == 0:
                elapsed = time.time() - start_time
                rate = nonce / elapsed if elapsed > 0 else 0
                if progress_callback:
                    progress_callback(nonce, rate)
                else:
                    print(f"\r  Tried {nonce:,} nonces ({rate:.0f} H/s)...", end="", flush=True)

    def generate_cpp_snippet(self, result: GenesisResult) -> str:
        """Generate C++ code snippet for chainparams.cpp."""
        return (
            f'genesis = CreateGenesisBlock({result.n_time}, {result.nonce}, 0x{self.n_bits:08x}, {self.n_version}, {self.reward} * COIN);\n'
            f'consensus.hashGenesisBlock = genesis.GetHash();\n'
            f'assert(consensus.hashGenesisBlock == uint256S("0x{result.hash_hex}"));\n'
            f'assert(genesis.hashMerkleRoot == uint256S("0x{result.merkle_root_hex}"));'
        )
