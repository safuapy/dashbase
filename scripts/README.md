# Chain Launcher Tool

A comprehensive automation tool for launching custom blockchain networks from the Dashbase codebase.

## Overview

The Chain Launcher (`scripts/launch_chain.py`) is a Python 3 tool that automates every customization needed to fork and launch a new blockchain from the Dashbase (Dash Core v18.2.2) codebase. Instead of manually editing dozens of source files, configuring genesis blocks, generating keys, and patching Docker/CI configs, you run one script — interactively or with a config file — and the tool handles everything end-to-end.

## What It Does

The tool automates the following categories of customization:

### 1. Chain Branding & Naming
- Chain name, ticker symbol, currency unit, subunit name
- Client name (e.g., "MyChain Core")
- Binary names (daemon, Qt GUI, CLI, tx tool, wallet tool)
- GUI application names (mainnet, testnet, regtest)
- Config filename (e.g., `mychain.conf`)
- Data directory name
- Copyright holder and year
- Website and source URLs
- Organization name and domain

**Files patched:** `configure.ac`, `src/clientversion.cpp`, `src/qt/guiconstants.h`, `src/qt/bitcoinunits.cpp`, `src/init.cpp`, `src/bitcoind.cpp`, `src/util/system.cpp`, `share/setup.nsi.in`, Windows `.rc` files, `Makefile.am`

### 2. Network Identity
- Network magic bytes (4 bytes per network — mainnet, testnet, regtest)
- P2P default ports
- RPC ports
- Base58 address prefixes (pubkey, script, secret key, extended public/secret)
- BIP44 coin type
- DNS seed nodes
- Fixed seed nodes (cleared for fresh chain)
- Data directory paths in `chainparamsbase.cpp`

**Auto-generation:** The tool can automatically generate all network identity values with collision avoidance:
- **Magic bytes**: 4 random bytes, checked against known chains (Bitcoin, Dash, Litecoin, Dogecoin, Dashbase, etc.)
- **P2P/RPC ports**: Random ports (10000-65535), RPC = P2P - 1 by convention, avoids known ports
- **Base58 prefixes**: Random pubkey/script/secret key prefixes, avoids known Bitcoin/Dash/Litecoin prefixes
- **BIP44 coin type**: Random value in 256-65535 range (above SLIP-44 registered range), avoids known types

Enable in CLI mode with `"auto_generate_network": true` in `chainbrand.json`, or answer "Y" when prompted in the interactive wizard.

**Files patched:** `src/chainparams.cpp`, `src/chainparamsbase.cpp`, `src/chainparamsseeds.h`

### 3. Genesis Block Mining
- Mines new genesis blocks for mainnet and testnet using the X11 hashing algorithm
- Searches for valid nonces that produce hashes below the target
- Patches the found nonce, hash, and merkle root into `chainparams.cpp`
- Updates genesis hash assertions (`assert(consensus.hashGenesisBlock == ...)`)
- Supports custom timestamp, bits, version, reward, psz_timestamp, and pubkey
- Verifies serialization against the original Dash genesis block before mining

**Requires:** `x11_hash` Python module (`pip install x11-hash`)

**Files patched:** `src/chainparams.cpp` (genesis creation line + hash/merkle assertions)

### 4. Spork Key Generation
- Generates ECDSA secp256k1 key pairs for spork signing
- Produces WIF-compressed private keys and chain addresses
- Generates separate keys for mainnet, testnet, devnet, and regtest
- Patches spork addresses directly into `chainparams.cpp` (`vSporkAddresses`)
- Outputs WIF private keys for use in config files

**Requires:** `ecdsa` Python module (`pip install ecdsa`)

**Files patched:** `src/chainparams.cpp` (spork address vectors)

### 5. BLS Masternode Operator Keys
- Generates BLS key pairs for masternode operator registration
- Three-tier fallback strategy:
  1. Shells out to built daemon (`mychaind -bls generate`)
  2. Uses Python BLS library (`blspy` or `py_ecc`)
  3. Falls back to random 32-byte private key with instructions
- Outputs private key for `masternodeblsprivkey` in config file
- Outputs public key for masternode registration

### 6. Consensus Parameters
- Subsidy halving interval
- PoW parameters (target spacing, target timespan, PoW limit)
- Masternode payment parameters (start block, increase block/period)
- InstantSend parameters (confirmations required, keep lock)
- Budget/governance parameters (payments start, cycle, window, superblock cycle, maturity window, min quorum, filter elements)
- Masternode minimum confirmations
- BIP34/BIP65/BIP66 activation heights
- DIP0001/DIP0003/DIP0003Enforcement/DIP0008/BRR activation heights
- Rule change activation threshold and miner confirmation window
- BIP9 soft fork deployments (all 9 deployments: TESTDUMMY, CSV, DIP0001, BIP147, DIP0003, DIP0008, REALLOC, DIP0020, DIP0024)
  - Configurable: bit, start_time, timeout, window_size, threshold_start, threshold_min, falloff_coeff
- LLMQ quorum type assignments (ChainLocks, InstantSend, DIP0024InstantSend, MNHF)

**Files patched:** `src/chainparams.cpp` (consensus parameter lines for mainnet + testnet)

### 7. Docker & CI Patching
- Dockerfiles: user name, home directory, data directory, image name, daemon name
- Docker entrypoint scripts: daemon name references, conf file name
- CI workflows: artifact names, staging directory names, binary references
- Docker Hub release workflow: image name, download URL prefixes

**Files patched:** `contrib/containers/*/Dockerfile*`, `contrib/containers/deploy/docker-entrypoint.sh`, `.github/workflows/build-wallets.yml`, `.github/workflows/build-tauri-wallet.yml`, `.github/workflows/release_docker_hub.yml`

### 8. Post-Run Verification
- Verifies all patched files contain expected new values
- Checks for stale references to old chain name, client name, and binary names
- Verifies `.rc` files were renamed correctly
- Validates conf filename was updated
- Reports pass/fail summary for all checks

### 9. Checkpoint & Seed Cleanup
- Clears old Dash checkpoints in `chainparams.cpp` (replaces with genesis-only checkpoint)
- Clears fixed seed nodes in `src/chainparamsseeds.h`
- Sets `nMinimumChainWork` and `defaultAssumeValid` to zero for fresh chain

## Quick Start

### Interactive Wizard

```bash
cd dash-core-base
python3 scripts/launch_chain.py
```

The wizard will prompt you for each value with sensible defaults. It generates a `chainbrand.json` config file and then applies all patches.

### CLI Mode (with pre-made config)

```bash
# 1. Generate a template config
python3 scripts/launch_chain.py --generate-config > chainbrand.json

# 2. Edit chainbrand.json with your values
vim chainbrand.json

# 3. Apply all customizations
python3 scripts/launch_chain.py --config chainbrand.json
```

### Verify Existing Patches

```bash
python3 scripts/launch_chain.py --verify-only
```

## Configuration File (`chainbrand.json`)

The `chainbrand.json` file is the single source of truth for all chain customizations. It contains these sections:

| Section | Description |
|---------|-------------|
| `chain` | Chain identity: name, ticker, currency unit, client name, conf file, data dir, organization, domain |
| `network` | Per-network settings: magic bytes, ports, base58 prefixes, BIP44 coin type, DNS seeds, genesis params |
| `consensus` | Per-network consensus params: subsidy, PoW, masternode payments, governance, BIP/DIP heights, BIP9 deployments, LLMQ |
| `keys` | Key generation options and generated key material (spork keys, BLS keys) |
| `binaries` | Binary executable names (daemon, qt, cli, tx, wallet, util) |
| `build` | Build metadata: package name, copyright, version, URLs |
| `gui` | GUI application names and organization info |
| `docker` | Docker image name, user name, data directory |
| `options` | Tool behavior flags: mine genesis, clear checkpoints, patch docker/CI, verify, git commit |

All fields have Dashbase defaults. You only need to override the values you want to change.

### Example: Minimal Custom Chain

```json
{
  "chain": {
    "name": "MyChain",
    "ticker": "MYC",
    "currency_unit": "MYC",
    "client_name": "MyChain Core",
    "conf_file": "mychain.conf",
    "data_dir": "MyChainCore",
    "organization": "MyChain Project",
    "domain": "mychain.org"
  },
  "network": {
    "mainnet": {
      "magic_bytes": [170, 187, 204, 221],
      "default_port": 20000,
      "rpc_port": 20001
    }
  },
  "binaries": {
    "daemon": "mychaind",
    "qt": "mychain-qt",
    "cli": "mychain-cli",
    "tx": "mychain-tx",
    "wallet": "mychain-wallet",
    "util": "mychain-util"
  },
  "options": {
    "mine_genesis": true,
    "generate_spork_keys": true
  }
}
```

## Architecture

```
scripts/
  launch_chain.py              # Main entry point — interactive wizard + CLI
  lib/
    __init__.py
    file_patcher.py            # Safe, atomic file patching utilities
    generate.py                # Auto-generation of magic bytes, ports, base58, BIP44
    branding.py                # Branding & naming patches
    network.py                 # Network identity + genesis/spork patching
    genesis.py                 # Genesis block mining (X11)
    keys.py                    # Spork (secp256k1) + BLS key generation
    consensus.py               # Consensus parameter patches
    docker_ci.py               # Docker, CI, NSIS, Windows resource patches
    verifier.py                # Post-run verification
  generate_genesis.py          # Standalone CLI: mine a genesis block
  generate_spork_keys.py       # Standalone CLI: generate spork + BLS keys
```

### Module Details

#### `lib/file_patcher.py`
Shared utilities for safe, idempotent file patching. All writes are atomic (write to temp file, then rename). Supports literal string replacement, regex replacement, line-range replacement, and insertion after/before markers.

#### `lib/genesis.py`
`GenesisGenerator` class that replicates the C++ `CreateGenesisBlock` logic. Mines genesis blocks by iterating nonces until the X11 hash falls below the target. Includes a verification mode that checks serialization against the original Dash genesis block (hash `0x00000ffd590b1485b3caadc19b22e6379c733355108f107a430458cdf3407ab6`).

#### `lib/keys.py`
- `SporkKeyGenerator`: Generates secp256k1 key pairs using the `ecdsa` library. Encodes private keys as WIF-compressed and derives chain addresses using Base58Check with configurable prefix bytes.
- `BLSKeyGenerator`: Generates BLS key pairs for masternode operators. Uses a three-tier fallback: (1) shells out to built daemon, (2) uses `blspy` or `py_ecc` Python library, (3) generates random 32-byte private key with instructions.

#### `lib/branding.py`
Patches branding across ~15 files. Handles configure.ac variable names correctly (`BITCOIN_DAEMON_NAME`, `BITCOIN_GUI_NAME`, `BITCOIN_CLI_NAME`, `BITCOIN_TX_NAME`, `BITCOIN_WALLET_TOOL_NAME`). Renames Windows `.rc` files to match new binary names.

#### `lib/network.py`
Patches network identity in `chainparams.cpp` and `chainparamsbase.cpp`. Uses regex with occurrence counting to target the correct network section (mainnet = 1st occurrence, testnet = 2nd). Also provides functions to patch genesis hash assertions and spork addresses into specific network sections.

#### `lib/consensus.py`
Patches consensus parameters for mainnet and testnet. Handles all 9 BIP9 deployments with configurable bit, start_time, timeout, window_size, threshold_start, threshold_min, and falloff_coeff. Patches LLMQ type assignments for ChainLocks, InstantSend, DIP0024InstantSend, and MNHF.

#### `lib/docker_ci.py`
Patches Docker files (Dockerfiles, entrypoint scripts, docker-compose), CI workflows (build-wallets.yml, build-tauri-wallet.yml, release_docker_hub.yml), and handles artifact name and staging directory renaming.

#### `lib/verifier.py`
Runs 14+ verification checks after patching. Checks that new values are present in key files, that stale references are gone, that `.rc` files were renamed, and that the conf filename was updated. Reports a pass/fail summary.

## Execution Flow

When you run `launch_chain.py`, it executes these steps in order:

1. **Load/validate config** — from `chainbrand.json` or interactive wizard
2. **Generate spork keys** (if enabled) — secp256k1 keypairs for mainnet + testnet
3. **Generate BLS keys** (if enabled) — masternode operator keypair
4. **Mine genesis blocks** (if enabled) — X11 mining for mainnet + testnet
5. **Apply branding patches** — names, binaries, GUI, copyright across ~15 files
6. **Apply network identity patches** — magic bytes, ports, base58, seeds, data dirs
7. **Apply consensus parameter patches** — DIP/BIP heights, deployments, LLMQ, subsidy
8. **Patch genesis hashes + spork addresses** into `chainparams.cpp`
9. **Apply Docker/CI patches** — Dockerfiles, workflows, NSIS, Windows resources
10. **Clear checkpoints + fixed seeds** — for a fresh chain
11. **Run verification** — 14+ checks for patch correctness
12. **Save updated config + keys** — `chainbrand.json` and `keys.json`
13. **Print summary + next steps** — build commands, conf file setup

## Prerequisites

### Required
- Python 3.8+
- No external dependencies for basic patching (branding, network, consensus, Docker/CI)

### For Genesis Mining
```bash
pip install x11-hash
```

### For Spork Key Generation
```bash
pip install ecdsa
```

### For BLS Key Generation (optional — falls back gracefully)
```bash
# Option 1: blspy library
pip install blspy

# Option 2: py-ecc library
pip install py-ecc

# Option 3: Use built daemon
# (no pip install needed — tool will shell out to ./src/mychaind -bls generate)
```

## Standalone CLI Tools

The refactored modules are also available as standalone CLI tools for manual use:

### Generate a Genesis Block
```bash
# Mine with default timestamp
python3 scripts/generate_genesis.py

# Mine with custom timestamp
python3 scripts/generate_genesis.py 1753734000
```

### Generate Spork + BLS Keys
```bash
python3 scripts/generate_spork_keys.py
```

This generates keys for all 4 networks (mainnet, testnet, devnet, regtest) and outputs both human-readable format and JSON.

## Files Modified by the Tool

| File | What Changes |
|------|-------------|
| `configure.ac` | AC_INIT line, binary names, copyright holder, copyright year, URLs |
| `src/chainparams.cpp` | Magic bytes, ports, base58, genesis, spork addresses, consensus params, LLMQ, checkpoints, seeds, min chain work |
| `src/chainparamsbase.cpp` | RPC ports, data directory names |
| `src/chainparamsseeds.h` | Fixed seeds cleared |
| `src/clientversion.cpp` | Client name string |
| `src/init.cpp` | Source code URL, website URL |
| `src/bitcoind.cpp` | Daemon name in usage strings |
| `src/util/system.cpp` | Config filename |
| `src/qt/guiconstants.h` | GUI org name, domain, app names |
| `src/qt/bitcoinunits.cpp` | Currency unit strings, chain name in descriptions |
| `src/*-res.rc` | Renamed to match new binary names, internal strings updated |
| `share/setup.nsi.in` | Install directory, Start Menu folder, DisplayIcon |
| `contrib/containers/*/Dockerfile*` | User, home dir, data dir, image name, daemon name |
| `contrib/containers/deploy/docker-entrypoint.sh` | Daemon name, conf file name |
| `.github/workflows/*.yml` | Artifact names, staging dirs, binary refs, Docker image |
| `chainbrand.json` | Updated with generated keys + genesis hashes |
| `keys.json` | Generated key material (add to `.gitignore`!) |

## Safety & Idempotency

- **Atomic writes**: All file patches use temp-file-then-rename for crash safety
- **Idempotent**: Running the tool twice with the same config is safe — patches that are already applied are no-ops
- **Logged**: Every patch operation logs what it changed
- **Verified**: Post-run verification catches missed patches or stale references
- **Config backup**: The original `chainbrand.json` is overwritten with updated values (including generated keys and genesis hashes), so you always have a record of what was applied

## Important Notes

- **Add `keys.json` to `.gitignore`** — it contains private keys that must not be committed
- **Magic bytes must be unique** — choose 4 bytes that don't collide with any existing chain
- **Genesis mining takes time** — with `0x1e0ffff0` bits, mining typically takes 1-10 minutes depending on hardware
- **BIP44 coin type should be unique** — use a value from the [SLIP-44 registry](https://github.com/satoshilabs/slips/blob/master/slip-0044.md) or a custom unused value
- **Clear checkpoints for fresh chains** — old Dash checkpoints are invalid for your new chain
- **Add seed nodes after launch** — populate `src/chainparamsseeds.h` once you have seed nodes running

## Post-Launch Steps

After running the tool, follow these steps to build and run your chain:

```bash
# 1. Build
./autogen.sh
./configure
make -j$(nproc)

# 2. Run the daemon
./src/mychaind -daemon
./src/mychain-cli getblockchaininfo

# 3. Configure your node
# Add to ~/.mychaincore/mychain.conf:
#   sporkkey=<WIF from keys.json>
#   masternodeblsprivkey=<BLS privkey from keys.json>

# 4. Add seed nodes to src/chainparamsseeds.h when available
# 5. Add checkpoints to src/chainparams.cpp after blocks are mined
```

## License

This tool is part of the Dashbase project and is distributed under the MIT software license.
