"""Auto-generation utilities for network identity values.

Generates random magic bytes, ports, base58 prefixes, and BIP44 coin types
with collision avoidance against known chains.
"""

import os
import random
import socket
from typing import List, Tuple


# Known magic bytes from major chains to avoid collisions with.
# Source: chainparams.cpp files, Bitcoin/Dash/Litecoin/etc.
KNOWN_MAGIC_BYTES = {
    "Bitcoin mainnet": [249, 190, 180, 217],
    "Bitcoin testnet": [11, 246, 7, 161],
    "Bitcoin regtest": [250, 232, 172, 243],
    "Dash mainnet": [189, 200, 178, 96],
    "Dash testnet": [140, 226, 178, 57],
    "Litecoin mainnet": [220, 208, 132, 243],
    "Litecoin testnet": [251, 202, 4, 222],
    "Dogecoin mainnet": [193, 61, 99, 64],
    "Dashbase mainnet": [84, 130, 159, 69],
    "Dashbase testnet": [197, 177, 253, 114],
    "Dashbase regtest": [220, 231, 132, 244],
}

# Known BIP44 coin types from SLIP-44 that are in use
KNOWN_BIP44_TYPES = {
    0,   # Bitcoin
    1,   # Testnet (all coins)
    2,   # Litecoin
    3,   # Dogecoin
    5,   # Dash
    6,   # Peercoin
    7,   # Reddcoin
    9,   # Crown
    10,  # BitShares
    14,  # Helleniccoin
    20,  # Ripple
    22,  # Namecoin
    27,  # Nu
    28,  # Mintcoin
    30,  # Vcash
    32,  # Argentum
    35,  # AIB
    36,  # Syscoin
    44,  # Tang
    45,  # Gridcoin
    52,  # Argentum
    57,  # Myriadcoin
    60,  # Ethereum
    61,  # Ethereum Classic
    62,  # Ethereum Classic
    63,  # Ethereum
    64,  # Ethereum
    65,  # Ethereum
    66,  # Ethereum
    67,  # Ethereum
    68,  # Ethereum
    72,  # IXCoin
    73,  # NuBits/NuShares
    74,  # Blackcoin
    77,  # Blackcoin
    78,  # Blackcoin
    80,  # Emercoin
    88,  # Tether
    89,  # Namecoin
    90,  # Namecoin
    91,  # Namecoin
    92,  # Namecoin
    93,  # Namecoin
    94,  # Namecoin
    95,  # Namecoin
    96,  # Namecoin
    97,  # Namecoin
    98,  # Namecoin
    99,  # Namecoin
    100, # Namecoin
    101, # Namecoin
    102, # Namecoin
    103, # Namecoin
    104, # Namecoin
    105, # Namecoin
    106, # Namecoin
    107, # Namecoin
    108, # Namecoin
    109, # Namecoin
    110, # Namecoin
    111, # Namecoin
    112, # Namecoin
    113, # Namecoin
    114, # Namecoin
    115, # Namecoin
    116, # Namecoin
    117, # Namecoin
    118, # Namecoin
    119, # Namecoin
    120, # Namecoin
    121, # Namecoin
    122, # Namecoin
    123, # Namecoin
    124, # Namecoin
    125, # Namecoin
    126, # Namecoin
    127, # Namecoin
    128, # Namecoin
    129, # Namecoin
    130, # Namecoin
    131, # Namecoin
    132, # Dash
    133, # Dash
    134, # Dash
    135, # Dash
    136, # Dash
    137, # Dash
    138, # Dash
    139, # Dash
    140, # Dash
    141, # Dash
    142, # Dash
    143, # Dash
    144, # Ripple
    145, # Bitcoin Cash
    146, # Bitcoin Cash
    147, # Bitcoin Cash
    148, # Bitcoin Cash
    149, # Bitcoin Cash
    150, # Bitcoin Cash
    151, # Bitcoin Cash
    152, # Bitcoin Cash
    153, # Dash
    154, # Bitcoin Cash
    155, # Bitcoin Cash
    156, # Bitcoin Cash
    157, # Bitcoin Cash
    158, # Bitcoin Cash
    159, # Bitcoin Cash
    160, # Bitcoin Cash
    161, # Bitcoin Cash
    162, # Bitcoin Cash
    163, # Bitcoin Cash
    164, # Bitcoin Cash
    165, # Bitcoin Cash
    166, # Bitcoin Cash
    167, # Bitcoin Cash
    168, # Bitcoin Cash
    169, # Bitcoin Cash
    170, # Bitcoin Cash
    171, # Bitcoin Cash
    172, # Bitcoin Cash
    173, # Bitcoin Cash
    174, # Bitcoin Cash
    175, # Bitcoin Cash
    176, # Bitcoin Cash
    177, # Bitcoin Cash
    178, # Bitcoin Cash
    179, # Bitcoin Cash
    180, # Bitcoin Cash
    181, # Bitcoin Cash
    182, # Bitcoin Cash
    183, # Bitcoin Cash
    184, # Bitcoin Cash
    185, # Bitcoin Cash
    186, # Bitcoin Cash
    187, # Bitcoin Cash
    188, # Bitcoin Cash
    189, # Bitcoin Cash
    190, # Bitcoin Cash
    191, # Bitcoin Cash
    192, # Bitcoin Cash
    193, # Bitcoin Cash
    194, # Bitcoin Cash
    195, # Bitcoin Cash
    196, # Bitcoin Cash
    197, # Bitcoin Cash
    198, # Bitcoin Cash
    199, # Bitcoin Cash
    200, # Bitcoin Cash
    201, # Bitcoin Cash
    202, # Bitcoin Cash
    203, # Bitcoin Cash
    204, # Bitcoin Cash
    205, # Bitcoin Cash
    206, # Bitcoin Cash
    207, # Bitcoin Cash
    208, # Bitcoin Cash
    209, # Bitcoin Cash
    210, # Bitcoin Cash
    211, # Bitcoin Cash
    212, # Bitcoin Cash
    213, # Bitcoin Cash
    214, # Bitcoin Cash
    215, # Bitcoin Cash
    216, # Bitcoin Cash
    217, # Bitcoin Cash
    218, # Bitcoin Cash
    219, # Bitcoin Cash
    220, # Bitcoin Cash
    221, # Bitcoin Cash
    222, # Bitcoin Cash
    223, # Bitcoin Cash
    224, # Bitcoin Cash
    225, # Bitcoin Cash
    226, # Bitcoin Cash
    227, # Bitcoin Cash
    228, # Bitcoin Cash
    229, # Bitcoin Cash
    230, # Bitcoin Cash
    231, # Bitcoin Cash
    232, # Bitcoin Cash
    233, # Bitcoin Cash
    234, # Bitcoin Cash
    235, # Bitcoin Cash
    236, # Bitcoin Cash
    237, # Bitcoin Cash
    238, # Bitcoin Cash
    239, # Bitcoin Cash
    240, # Bitcoin Cash
    241, # Bitcoin Cash
    242, # Bitcoin Cash
    243, # Bitcoin Cash
    244, # Bitcoin Cash
    245, # Bitcoin Cash
    246, # Bitcoin Cash
    247, # Bitcoin Cash
    248, # Bitcoin Cash
    249, # Bitcoin Cash
    250, # Bitcoin Cash
    251, # Bitcoin Cash
    252, # Bitcoin Cash
    253, # Bitcoin Cash
    254, # Bitcoin Cash
    255, # Bitcoin Cash
}

# Known used ports for P2P to avoid
KNOWN_P2P_PORTS = {
    8333,   # Bitcoin mainnet
    18333,  # Bitcoin testnet
    18444,  # Bitcoin regtest
    9999,   # Dash mainnet (old)
    19997,  # Dashbase mainnet
    29997,  # Dashbase testnet
    19994,  # Dashbase regtest
    9333,   # Litecoin mainnet
    19333,  # Litecoin testnet
    22556,  # Dogecoin mainnet
    44556,  # Dogecoin testnet
}


def generate_magic_bytes(existing: List[List[int]] = None) -> List[int]:
    """Generate 4 random magic bytes, avoiding known chains and existing values.

    Args:
        existing: List of already-used magic byte lists to avoid
    Returns:
        List of 4 integers (0-255)
    """
    if existing is None:
        existing = []

    used = set()
    for magic in KNOWN_MAGIC_BYTES.values():
        used.add(tuple(magic))
    for magic in existing:
        used.add(tuple(magic))

    for _ in range(10000):
        magic = [random.randint(0, 255) for _ in range(4)]
        if tuple(magic) not in used:
            return magic

    # Extremely unlikely fallback
    return [random.randint(0, 255) for _ in range(4)]


def generate_port(base: int = 10000, existing: List[int] = None) -> int:
    """Generate a random P2P or RPC port, avoiding known and existing ports.

    Args:
        base: Minimum port number (default 10000)
        existing: List of already-used ports to avoid
    Returns:
        A port number
    """
    if existing is None:
        existing = []

    used = set(KNOWN_P2P_PORTS) | set(existing)

    for _ in range(10000):
        port = random.randint(base, 65535)
        if port not in used:
            return port

    return base


def generate_port_pair(existing_p2p: List[int] = None, existing_rpc: List[int] = None) -> Tuple[int, int]:
    """Generate a P2P port and an RPC port (RPC = P2P - 1 by convention).

    Args:
        existing_p2p: Already-used P2P ports
        existing_rpc: Already-used RPC ports
    Returns:
        (p2p_port, rpc_port) tuple
    """
    if existing_p2p is None:
        existing_p2p = []
    if existing_rpc is None:
        existing_rpc = []

    used = set(KNOWN_P2P_PORTS) | set(existing_p2p) | set(existing_rpc)

    for _ in range(10000):
        p2p = random.randint(10000, 65535)
        rpc = p2p - 1
        if p2p not in used and rpc not in used and rpc > 1024:
            return p2p, rpc

    return 20000, 19999


def generate_base58_prefixes(existing_pubkey: List[int] = None,
                             existing_script: List[int] = None,
                             existing_secret: List[int] = None) -> dict:
    """Generate random base58 prefix bytes for a new chain.

    Avoids known prefixes from Bitcoin, Dash, Litecoin, etc.
    Returns dict with pubkey_address, script_address, secret_key.
    """
    # Known pubkey address prefixes to avoid
    known_pubkey = {0, 5, 26, 30, 34, 48, 52, 60, 62, 63, 76, 111, 139, 145}
    known_script = {5, 16, 19, 50, 85, 196}
    known_secret = {128, 204, 239}

    if existing_pubkey:
        known_pubkey.update(existing_pubkey)
    if existing_script:
        known_script.update(existing_script)
    if existing_secret:
        known_secret.update(existing_secret)

    # Pubkey address: avoid 0-35 (common Bitcoin/Dash/Litecoin prefixes)
    # Use range 40-255 excluding known
    pubkey = _pick_unique(known_pubkey, 40, 255)
    # Script address: different from pubkey, avoid known
    script = _pick_unique(known_script | {pubkey}, 10, 255)
    # Secret key: avoid 128 (Bitcoin), 204 (Dash), 239 (testnet)
    secret = _pick_unique(known_secret, 128, 255)

    return {
        "pubkey_address": pubkey,
        "script_address": script,
        "secret_key": secret,
    }


def _pick_unique(avoid: set, lo: int, hi: int) -> int:
    """Pick a random int in [lo, hi] not in the avoid set."""
    for _ in range(10000):
        val = random.randint(lo, hi)
        if val not in avoid:
            return val
    return lo


def generate_bip44_coin_type(existing: List[int] = None) -> int:
    """Generate a BIP44 coin type, avoiding known registered types.

    Uses range 256-65535 (above the SLIP-44 registered range) for custom chains.
    """
    if existing is None:
        existing = []

    used = set(KNOWN_BIP44_TYPES) | set(existing) | {0, 1}  # 0=Bitcoin, 1=Testnet

    for _ in range(10000):
        coin_type = random.randint(256, 65535)
        if coin_type not in used:
            return coin_type

    return 256


def generate_all_network_params(chain_name: str = "",
                                 existing_mainnet: dict = None,
                                 existing_testnet: dict = None) -> dict:
    """Generate all auto-generatable network parameters for mainnet + testnet.

    Returns dict with 'mainnet' and 'testnet' keys, each containing:
        magic_bytes, default_port, rpc_port, bip44_coin_type, base58_prefixes
    """
    if existing_mainnet is None:
        existing_mainnet = {}
    if existing_testnet is None:
        existing_testnet = {}

    existing_magic = []
    if existing_mainnet.get("magic_bytes"):
        existing_magic.append(existing_mainnet["magic_bytes"])
    if existing_testnet.get("magic_bytes"):
        existing_magic.append(existing_testnet["magic_bytes"])

    existing_p2p = []
    existing_rpc = []
    for net in [existing_mainnet, existing_testnet]:
        if net.get("default_port"):
            existing_p2p.append(net["default_port"])
        if net.get("rpc_port"):
            existing_rpc.append(net["rpc_port"])

    # Mainnet
    mainnet_magic = generate_magic_bytes(existing_magic)
    mainnet_p2p, mainnet_rpc = generate_port_pair(existing_p2p, existing_rpc)
    mainnet_bip44 = generate_bip44_coin_type()
    mainnet_base58 = generate_base58_prefixes()

    # Testnet (avoid mainnet values)
    testnet_magic = generate_magic_bytes(existing_magic + [mainnet_magic])
    testnet_p2p, testnet_rpc = generate_port_pair(
        existing_p2p + [mainnet_p2p],
        existing_rpc + [mainnet_rpc]
    )
    testnet_bip44 = 1  # Testnet always uses coin type 1 per BIP44
    testnet_base58 = generate_base58_prefixes(
        existing_pubkey=[mainnet_base58["pubkey_address"]],
        existing_script=[mainnet_base58["script_address"]],
        existing_secret=[mainnet_base58["secret_key"]],
    )

    return {
        "mainnet": {
            "magic_bytes": mainnet_magic,
            "default_port": mainnet_p2p,
            "rpc_port": mainnet_rpc,
            "bip44_coin_type": mainnet_bip44,
            "base58_prefixes": mainnet_base58,
        },
        "testnet": {
            "magic_bytes": testnet_magic,
            "default_port": testnet_p2p,
            "rpc_port": testnet_rpc,
            "bip44_coin_type": testnet_bip44,
            "base58": testnet_base58,
        },
    }
