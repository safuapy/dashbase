# Dash Core Fork Guide

A comprehensive guide for forking Dash Core v18.2.2 to create a rebrandable
masternode chain base.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: Audit (Complete)](#phase-1-audit)
4. [Phase 1.5: Security Backports (Complete)](#phase-15-security-backports)
5. [Phase 2: Strip Platform Remnants (Complete)](#phase-2-strip-platform-remnants)
6. [Phase 3: Branding & Parameterization](#phase-3-branding--parameterization)
7. [Phase 4: Build & CI](#phase-4-build--ci)
8. [Post-Fork Checklist](#post-fork-checklist)
9. [Architecture Reference](#architecture-reference)

---

## Overview

This guide documents the process of forking Dash Core at tag `v18.2.2` — the
last release before Dash Platform/Evolution was merged — to create a clean,
rebrandable masternode chain base.

**What's retained:**
- DIP3 deterministic masternodes
- LLMQ (Long-Living Masternode Quorums)
- ChainLocks
- InstantSend
- Governance / Superblocks
- BLS cryptography
- CoinJoin / PrivateSend

**What's removed:**
- Dash Platform / Evolution code paths
- Platform LLMQ quorum types (`LLMQ_100_67`, `LLMQ_25_67`)
- `llmqTypePlatform` consensus parameter
- `platform-user` RPC restriction system
- `RPC_PLATFORM_RESTRICTION` error code

---

## Prerequisites

- C++17 compiler (GCC 8+, Clang 7+)
- `automake`, `libtool`, `pkg-config`, `autoconf`
- `python3` (for test suite)
- `jq` (for `scripts/new-fork.sh`)
- ~10 GB free disk space

---

## Phase 1: Audit

**Status: ✅ Complete**

See `FORK_AUDIT.md` for the full audit report covering:
- Chain identity parameters (magic bytes, ports, genesis, base58, DNS seeds, checkpoints)
- Branding strings (client name, currency unit, config file, GUI constants)
- Platform remnants identified for removal

---

## Phase 1.5: Security Backports

**Status: ✅ Complete**

See `SECURITY_BACKPORTS.md` for the full catalog of security fixes from
v19.0.0 through v23.1.2, categorized by priority (P0–P3).

**Key P0 items to backport before mainnet launch:**
1. Crash on invalid masternode payment destinations (v22.1.3)
2. BLS identity element rejection (v23.1.2)
3. ChainLockSigner unbounded memory growth (v23.1.2)
4. Concurrent ChainLock signing race (v23.1.2)

**How to backport:**
```bash
# Find the specific PR commit in dashpay/dash
git log --all --oneline | grep <PR-number>

# Cherry-pick the commit
git cherry-pick <commit-hash>

# Resolve conflicts, then test
make -j$(nproc)
./src/test/test_dash
./test/functional/test_runner.py
```

---

## Phase 2: Strip Platform Remnants

**Status: ✅ Complete**

The following files were modified to remove Platform-specific code:

| File | Change |
|------|--------|
| `src/consensus/params.h` | Removed `llmqTypePlatform` field |
| `src/chainparams.cpp` | Removed `llmqTypePlatform` assignments + `LLMQ_100_67`/`LLMQ_25_67` registrations |
| `src/llmq/params.h` | Removed `LLMQ_100_67` and `LLMQ_25_67` enum values + parameter definitions |
| `src/llmq/utils.cpp` | Removed Platform LLMQ references from `EvalSpork`, `IsQuorumTypeEnabled`, `IsInstantSendLLMQTypeShared` |
| `src/rpc/protocol.h` | Removed `RPC_PLATFORM_RESTRICTION` error code |
| `src/rpc/server.cpp` | Removed `InitPlatformRestrictions()`, `mapPlatformRestrictions`, platform-user filtering |
| `src/rpc/server.h` | Removed platform-related declarations |
| `src/init.cpp` | Removed `-platform-user` arg + `InitPlatformRestrictions()` call |
| `src/httprpc.cpp` | Removed `RPC_PLATFORM_RESTRICTION` HTTP status mapping |
| `src/test/evo_utils_tests.cpp` | Removed `llmqTypePlatform` test assertions |
| `test/functional/test_runner.py` | Removed `rpc_platform_filter.py` |
| `test/functional/rpc_platform_filter.py` | **Deleted** (entire test was Platform-specific) |

---

## Phase 3: Branding & Parameterization

### chainbrand.json

All rebrandable values are consolidated in `chainbrand.json` at the repo root.
Edit this file to customize:

- **Chain identity**: name, ticker, currency unit, client name
- **Network parameters**: magic bytes, ports, DNS seeds, base58 prefixes, genesis config
- **Binary names**: daemon, Qt, CLI, tx, wallet
- **Build metadata**: package name, copyright, URLs, version numbers
- **GUI constants**: organization name, domain, application names

### scripts/new-fork.sh

Run this script to apply branding from `chainbrand.json` across the codebase:

```bash
# Edit chainbrand.json with your values
vim chainbrand.json

# Apply branding
./scripts/new-fork.sh

# Verify build
./autogen.sh
./configure --without-gui
make -j$(nproc)
```

### What the script does:

1. Updates `configure.ac` (binary names, package name, URLs)
2. Updates `src/clientversion.cpp` (client name string)
3. Updates `src/chainparams.cpp` (magic bytes, ports, DNS seeds, base58 prefixes, coin type)
4. Updates `src/chainparamsbase.cpp` (RPC ports, data directory name)
5. Clears `src/chainparamsseeds.h` (removes Dash seed nodes)
6. Updates `src/util/system.cpp` (config file name)
7. Updates `src/qt/guiconstants.h` (GUI branding)
8. Updates `src/qt/bitcoinunits.cpp` (currency unit strings)
9. Updates Makefiles and `.pro` files (binary names)
10. Updates `src/init.cpp` (URLs)

### What the script does NOT do (manual steps):

1. **Genesis block generation**: Modify the genesis timestamp/nonce in
   `chainparams.cpp`, then run the node once to get the new genesis hash.
   Update the `assert()` statements with the new hash.

2. **Checkpoints**: Clear all Dash checkpoints in `chainparams.cpp`. Add new
   checkpoints after your chain has been running.

3. **Minimum chain work**: Set `nMinimumChainWork` to `0x00...00` for a fresh
   chain. Update after blocks have been mined.

4. **Spork addresses**: Update `vSporkAddresses` in `chainparams.cpp` with
   your own spork signing keys.

5. **Deployment windows**: The versionbits deployment start times and timeouts
   in `chainparams.cpp` are Dash-specific. Adjust or disable them for your chain.

6. **Governance parameters**: `nBudgetPaymentsStartBlock`, `nSuperblockStartBlock`,
   etc. are Dash-specific block heights. Reset them for your chain.

---

## Phase 4: Build & CI

### GitHub Actions Build Workflow

A build workflow is provided at `.github/workflows/build-wallets.yml` that
builds three targets via matrix strategy:

| Target | Runner | Output |
|--------|--------|--------|
| macOS Intel wallet | `macos-13` | `dashcore-macos-intel.tar.gz` |
| Windows wallet | `ubuntu-latest` (cross-compile) | `dashcore-windows.zip` |
| Linux daemon | `ubuntu-latest` | `dashcore-linux-daemon.tar.gz` |

**Triggers:**
- Push to `main`/`master` branch
- Tag push (`v*`) — creates a draft GitHub Release with artifacts
- Manual dispatch (`workflow_dispatch`)

**Usage:**
```bash
# Tag a release
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will build all 3 targets and attach to a draft release
```

### Local Build (Linux daemon)

```bash
cd depends
make -j$(nproc)
cd ..
./autogen.sh
./configure --prefix=$PWD/depends/x86_64-pc-linux-gnu --without-gui
make -j$(nproc)
```

### Local Build (macOS)

```bash
brew install automake libtool pkg-config libnatpmp berkeley-db boost libevent qt@5 miniupnpc zeromq sqlite ccache
cd depends
make HOST=x86_64-apple-darwin -j$(sysctl -n hw.logicalcpu)
cd ..
./autogen.sh
./configure --prefix=$PWD/depends/x86_64-apple-darwin --with-gui=yes
make -j$(sysctl -n hw.logicalcpu)
```

### Local Build (Windows cross-compile)

```bash
sudo apt install g++-mingw-w64-x86-64
cd depends
make HOST=x86_64-w64-mingw32 -j$(nproc)
cd ..
./autogen.sh
CONFIG_SITE=$PWD/depends/x86_64-w64-mingw32/share/config.site ./configure --prefix=/ --with-gui=yes
make -j$(nproc)
```

---

## Post-Fork Checklist

- [ ] Edit `chainbrand.json` with your chain's values
- [ ] Run `scripts/new-fork.sh` to apply branding
- [ ] Generate new genesis block (modify timestamp/nonce, recalculate hash)
- [ ] Update genesis hash assertions in `chainparams.cpp`
- [ ] Clear all Dash checkpoints in `chainparams.cpp`
- [ ] Set `nMinimumChainWork` to zero for fresh chain
- [ ] Clear fixed seeds in `chainparamsseeds.h`
- [ ] Update spork addresses in `chainparams.cpp`
- [ ] Reset governance block heights (`nBudgetPaymentsStartBlock`, etc.)
- [ ] Adjust versionbits deployment windows or disable them
- [ ] Verify build: `./autogen.sh && ./configure && make`
- [ ] Run unit tests: `./src/test/test_dash`
- [ ] Run functional tests: `./test/functional/test_runner.py`
- [ ] Set up regtest with masternodes to verify ChainLocks + InstantSend
- [ ] Backport P0 security fixes from `SECURITY_BACKPORTS.md`
- [ ] Backport P1 security fixes
- [ ] Test GitHub Actions build workflow
- [ ] Set up DNS seed nodes
- [ ] Generate new BLS keys for spork signing

---

## Architecture Reference

### Core Masternode Features (Retained)

```
src/evo/          — DIP3 deterministic masternodes, special transactions
src/llmq/         — Long-Living Masternode Quorums (signing, ChainLocks, InstantSend)
src/governance/   — Governance objects, proposals, superblocks
src/coinjoin/     — PrivateSend / CoinJoin mixing
src/bls/          — BLS signature scheme (used by LLMQ and masternodes)
```

### Chain Identity Files

```
src/chainparams.cpp       — Mainnet/testnet/devnet/regtest parameters
src/chainparams.h         — CChainParams class
src/chainparamsbase.cpp   — Base params (RPC ports, data dirs)
src/chainparamsseeds.h    — Fixed seed node IPs
src/clientversion.cpp     — Client name and version strings
src/qt/guiconstants.h     — GUI organization/app names
src/qt/bitcoinunits.cpp   — Currency unit display strings
configure.ac              — Build system branding (binary names, package name)
src/util/system.cpp       — Config file name (dash.conf)
```

### LLMQ Quorum Types (After Platform Stripping)

| Type | Enum | Size | Threshold | Purpose |
|------|------|------|-----------|---------|
| `LLMQ_50_60` | 1 | 50 | 30 (60%) | InstantSend (mainnet) |
| `LLMQ_400_60` | 2 | 400 | 240 (60%) | ChainLocks (mainnet) |
| `LLMQ_400_85` | 3 | 400 | 340 (85%) | MNHF (mainnet) |
| `LLMQ_60_75` | 5 | 60 | 45 (75%) | DIP0024 InstantSend (mainnet) |
| `LLMQ_TEST` | 100 | 3 | 2 (66%) | Testing/regtest |
| `LLMQ_DEVNET` | 101 | 12 | 6 (50%) | Devnets |

**Removed types:** `LLMQ_100_67` (4) and `LLMQ_25_67` (6) — Platform-only.
