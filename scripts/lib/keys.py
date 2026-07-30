"""Spork (secp256k1) and BLS key generation for Dash-based chains.

Refactored from scripts/generate_spork_keys.py into reusable classes.
"""

import hashlib
import os
import sys
import json
import subprocess
import secrets
from dataclasses import dataclass
from typing import Tuple, Optional


B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58_encode(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = B58_ALPHABET[rem] + encoded
    for byte in data:
        if byte == 0:
            encoded = "1" + encoded
        else:
            break
    return encoded


def _base58check_encode(payload: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    return _base58_encode(payload + checksum)


def _wif_encode(privkey_bytes: bytes, testnet: bool) -> str:
    prefix = bytes([239]) if testnet else bytes([204])
    payload = prefix + privkey_bytes + bytes([0x01])
    return _base58check_encode(payload)


def _address_encode(pubkey_bytes: bytes, addr_prefix: int) -> str:
    prefix = bytes([addr_prefix])
    sha256 = hashlib.sha256(pubkey_bytes).digest()
    try:
        ripemd160 = hashlib.new("ripemd160", sha256).digest()
    except Exception:
        import hashlib as _hl
        ripemd160 = _hl.new("ripemd160", sha256).digest() if "ripemd160" in _hl.algorithms_available else sha256[:20]
    return _base58check_encode(prefix + ripemd160)


@dataclass
class SporkKeyPair:
    address: str
    wif: str
    privkey_hex: str
    pubkey_hex: str


@dataclass
class BLSKeyPair:
    privkey_hex: str
    pubkey_hex: str


class SporkKeyGenerator:
    """Generate ECDSA secp256k1 key pairs for spork signing."""

    def __init__(self, mainnet_addr_prefix: int = 76, testnet_addr_prefix: int = 140):
        self.mainnet_addr_prefix = mainnet_addr_prefix
        self.testnet_addr_prefix = testnet_addr_prefix

    @staticmethod
    def _generate_keypair() -> Tuple[bytes, bytes]:
        try:
            import ecdsa
        except ImportError:
            print("ERROR: 'ecdsa' library required. Install with: pip install ecdsa")
            sys.exit(1)

        sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        privkey_bytes = sk.to_string()
        vk = sk.get_verifying_key()
        x = int.from_bytes(vk.to_string()[:32], "big")
        y = int.from_bytes(vk.to_string()[32:], "big")
        prefix = b"\x02" if y % 2 == 0 else b"\x03"
        compressed_pubkey = prefix + x.to_bytes(32, "big")
        return privkey_bytes, compressed_pubkey

    def generate(self, network: str = "mainnet") -> SporkKeyPair:
        privkey, pubkey = self._generate_keypair()
        is_testnet = network != "mainnet"
        addr_prefix = self.testnet_addr_prefix if is_testnet else self.mainnet_addr_prefix
        wif = _wif_encode(privkey, is_testnet)
        address = _address_encode(pubkey, addr_prefix)
        return SporkKeyPair(
            address=address,
            wif=wif,
            privkey_hex=privkey.hex(),
            pubkey_hex=pubkey.hex(),
        )

    def generate_all(self) -> dict:
        """Generate spork keys for all networks."""
        results = {}
        for net in ["mainnet", "testnet", "devnet", "regtest"]:
            results[net] = self.generate(net)
        return results


class BLSKeyGenerator:
    """Generate BLS key pairs for masternode operators.

    Tries multiple strategies:
    1. Shell out to built daemon's `bls generate` command
    2. Use a Python BLS library if available
    3. Fallback: generate a random 32-byte private key with instructions
    """

    def __init__(self, daemon_path: Optional[str] = None, daemon_name: str = "dashbased"):
        self.daemon_path = daemon_path
        self.daemon_name = daemon_name

    def _try_daemon(self) -> Optional[BLSKeyPair]:
        """Try to use the built daemon's BLS generation."""
        daemon = self.daemon_path
        if not daemon:
            for candidate in [f"./src/{self.daemon_name}", "./src/dashbased", "./src/dashd"]:
                if os.path.exists(candidate):
                    daemon = candidate
                    break

        if not daemon or not os.path.exists(daemon):
            return None

        try:
            result = subprocess.run(
                [daemon, "-bls", "generate"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                for line in output.split("\n"):
                    if "sk" in line.lower() and "pk" in line.lower():
                        parts = line.split()
                        for i, p in enumerate(parts):
                            if p in ("sk:", "sk") and i + 1 < len(parts):
                                sk = parts[i + 1]
                            if p in ("pk:", "pk") and i + 1 < len(parts):
                                pk = parts[i + 1]
                        if sk and pk:
                            return BLSKeyPair(privkey_hex=sk, pubkey_hex=pk)
        except Exception:
            pass
        return None

    def _try_python_bls(self) -> Optional[BLSKeyPair]:
        """Try to use a Python BLS library."""
        try:
            import blspy
            sk = blspy.PrivateKey.from_seed(secrets.token_bytes(32))
            pk = sk.get_g1()
            return BLSKeyPair(
                privkey_hex=bytes(sk).hex(),
                pubkey_hex=bytes(pk).hex(),
            )
        except ImportError:
            pass

        try:
            from py_ecc.bls import G2ProofOfPossession as bls
            sk_int = secrets.randbelow(bls.curve_order)
            sk_bytes = sk_int.to_bytes(32, "big")
            pk = bls.SkToPk(sk_int)
            return BLSKeyPair(
                privkey_hex=sk_bytes.hex(),
                pubkey_hex=pk.hex(),
            )
        except ImportError:
            pass

        return None

    def _fallback_random(self) -> BLSKeyPair:
        """Generate a random 32-byte private key (user must derive pubkey via daemon)."""
        privkey = secrets.token_bytes(32)
        return BLSKeyPair(
            privkey_hex=privkey.hex(),
            pubkey_hex=f"(run: {self.daemon_name} -bls generate 0x{privkey.hex()} to get pubkey)",
        )

    def generate(self) -> BLSKeyPair:
        """Generate a BLS key pair using the best available method."""
        result = self._try_daemon()
        if result:
            return result

        result = self._try_python_bls()
        if result:
            return result

        print(f"WARNING: Could not find BLS library or built daemon. Generating random private key.")
        print(f"  You will need to derive the public key using: {self.daemon_name} -bls generate 0x<privkey>")
        return self._fallback_random()

    def generate_conf_snippet(self, keypair: BLSKeyPair) -> str:
        """Generate a conf file snippet for masternode setup."""
        lines = [
            "# Masternode BLS keys",
            f"masternodeblsprivkey={keypair.privkey_hex}",
            f"# masternodeblspubkey={keypair.pubkey_hex}",
            "",
            "# Spork signing key (add the spork WIF from key generation)",
            "# sporkkey=<WIF from generated spork keys>",
        ]
        return "\n".join(lines)
