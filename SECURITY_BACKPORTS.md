# Security Backports from Dash Core v19–v23

Base: **Dash Core v18.2.2**
Scan range: **v19.0.0 → v23.1.2**

This document catalogs security-relevant fixes and bug fixes from Dash Core
releases v19 through v23 that should be evaluated for backporting to the
v18.2.2 fork base. Items are categorized by priority.

---

## Priority Levels

- **P0 — Critical**: Exploitable vulnerabilities or consensus-breaking bugs.
- **P1 — High**: Crashes, deadlocks, or data-loss scenarios.
- **P2 — Medium**: Correctness fixes, minor DoS hardening, or robustness improvements.
- **P3 — Low**: Build/CI/doc fixes; optional for a fork base.

---

## P0 — Critical (Backport Before Launch)

| Version | PR/Issue | Description | Files Affected |
|---------|----------|-------------|----------------|
| v22.1.3 | dash#6740 | Fixed crash when processing invalid masternode payment destinations — unsafe assertion replaced with proper error handling | `src/evo/cbtx.cpp`, validation |
| v23.1.2 | dash#7193 | Reject identity elements in BLS deserialization and key generation to prevent invalid keys from being accepted | `src/bls/bls_*` |
| v23.1.2 | dash#7208 | Skip collecting block txids during IBD to prevent unbounded memory growth in `ChainLockSigner` | `src/llmq/chainlocks.cpp` |
| v23.1.2 | dash#7209 | Serialize `TrySignChainTip` to prevent concurrent signing races that could split signing shares across different block hashes | `src/llmq/chainlocks.cpp` |

---

## P1 — High (Backport Before Launch)

| Version | PR/Issue | Description | Files Affected |
|---------|----------|-------------|----------------|
| v19.0.0 | — | BIP61 reject message removal (reduces attack surface for untrusted peers) | `src/net_processing.cpp` |
| v20.0.2 | — | Fixed crash when upgrading from v19.x to v20.0.0 after v20 activation without re-indexing | validation/index code |
| v20.0.3 | — | Wallet decryption fix for reported wallet decryption issues | `src/wallet/` |
| v20.1.1 | — | Deadlock fix: nodes became non-responsive with "Work depth queue exceeded", causing masternode PoSe bans | `src/rpc/server.cpp` |
| v21.0.2 | — | Transaction retrieval bug: clients (incl. mobile wallets) couldn't receive transactions before mining due to partial misclassification as block-only connections | `src/net_processing.cpp` |
| v22.1.1 | dash#6574 | Fixed v2→v1 P2P downgrade issues affecting Dash-specific connection types (mixing, masternode probes), causing increased connection count and masternode load | `src/net_*`, `src/llmq/` |
| v23.1.2 | dash#7191 | Fixed quorum labels not being correctly reseated when new quorum types are inserted | `src/llmq/` |
| v23.1.0 | dash#6924, #6940 | Fixed various race conditions in ChainLock processing | `src/llmq/chainlocks.cpp` |
| v23.1.0 | dash#6938, #6944, #6945, #6939 | Improved wallet encryption robustness and HD chain decryption error logging | `src/wallet/` |
| v23.0.2 | dash#6944 | Fixed HD chain encryption check ordering: `LoadHDChain()` failed if `CRYPTED_HDCHAIN` records read before `MASTER_KEY` records during wallet loading | `src/wallet/` |
| v23.0.2 | dash#6961 | Corrected BLS scheme setting in `MigrateLegacyDiffs()` when `nVersion` is present — legacy scheme was only set when `nVersion` missing instead of whenever `pubKeyOperator` present | `src/evo/deterministicmns.cpp` |

---

## P2 — Medium (Backport When Feasible)

| Version | PR/Issue | Description | Files Affected |
|---------|----------|-------------|----------------|
| v20.0.0 | — | Transaction rebroadcast: mempool tracks unbroadcast transactions, improving initial broadcast guarantees | `src/net_processing.cpp`, `src/txmempool.*` |
| v20.0.1 | — | Masternode fix: old quorum data cleanup mechanism was slowing down masternodes during DKG sessions and causing PoSe scoring | `src/llmq/` |
| v20.0.3 | — | Reduced memory usage during old quorum data cleanup | `src/llmq/` |
| v20.0.4 | — | Governance: triggers from the past are now ignored when voting | `src/governance/` |
| v20.1.0 | — | Removal of Legacy InstantSend logic (reduces attack surface) | `src/llmq/instantsend.cpp` |
| v20.1.0 | — | Transaction version numbers treated as unsigned 16-bit integers (matches consensus logic) | `src/primitives/transaction.h` |
| v22.0.0 | — | Bad port protection: system ports (<1024) and common auth ports are avoided to prevent DDoS | `src/net.cpp` |
| v22.0.0 | — | Improved onion connectivity: maintain ≥2 outbound onion connections, protect from eviction | `src/net.cpp` |
| v22.0.0 | — | Multi-network connectivity: nodes with multiple reachable networks maintain outbound connections to each, improving eclipse/partition attack resistance | `src/net.cpp` |
| v22.0.0 | — | BIP324 v2 P2P protocol encryption (experimental, opt-in) | `src/net.*` |
| v22.1.0 | — | BIP324 v2 P2P enabled by default (backward compatible) | `src/net.*` |
| v22.1.2 | dash#6632 | Optimized versionbits calculation to avoid unnecessary computations during block operations, improving reorg performance | `src/versionbits.cpp` |
| v22.1.3 | dash#6744 | Fixed misleading error logs triggered by legitimate RPC queries for non-existent transaction data | `src/rpc/` |
| v23.0.0 | dash#6685 | Change output amounts randomized to prevent fingerprinting transactions created by Dash Core wallet | `src/wallet/` |
| v23.1.0 | dash#7079 | Peers that re-propagate stale quorum final commitments (`QFCOMMIT`) are now banned | `src/net_processing.cpp` |
| v23.1.0 | dash#7045 | Masternodes trickle transactions to non-masternode peers, reducing information leakage | `src/net_processing.cpp` |
| v23.1.2 | dash#7154 | Fixed MN update notifications where old and new masternode lists were swapped, causing incorrect change detection | GUI / `src/evo/` |
| v23.1.2 | dash#7222 | Properly skip evodb repair when reindexing to prevent unnecessary repair attempts | `src/evo/evodb.cpp` |
| v23.0.2 | dash#6964 | Removed duplicated check of the same key in the InstantSend database | `src/llmq/instantsend.cpp` |
| v23.0.2 | dash#6969, #6999 | Added `evodb verify` and `evodb repair` RPC commands + automatic verification/repair of evodb diffs at startup | `src/evo/evodb.cpp` |

---

## P3 — Low (Optional / Build-Only)

| Version | PR/Issue | Description |
|---------|----------|-------------|
| v20.0.0 | — | Switch from Gitian to Guix deterministic builds |
| v20.0.1 | — | Qt testnet crash fix (QT clients only) |
| v20.0.3 | — | macOS build system improvements, FreeBSD compilation fixes |
| v20.0.4 | — | Windows binary miner disabled via Guix (antivirus false positives) |
| v20.1.0 | — | Docker build system: exclude `dash-qt` from Docker image |
| v22.1.0 | — | macOS distribution packaged as ZIP instead of DMG |
| v22.1.2 | dash#6586 | Pinned QEMU version to avoid segfaults during container builds |
| v23.0.2 | dash#7009 | Fixed build issue on Debian 13 (QDebug include) |
| v23.0.2 | dash#6949 | Updated Qt 5.15.14→5.15.18 (CVE-2025-4211, CVE-2025-5455, CVE-2025-30348) |
| v23.1.2 | dash#7221 | Renamed `bitcoin-util` manpage/test references to `dash-util` |

---

## Not Applicable (Platform-Only / Feature-Only)

These items are explicitly **excluded** from backporting as they relate to
Dash Platform, Evolution, or features not present in the fork base:

- v21.0.0: MN_RR hard fork and Dash Platform Genesis Chain activation
- v21.0.0: Mainnet spork hardening (tied to Platform launch)
- v21.1.0: EHF resigning (Platform activation related)
- v21.1.1: Asset unlock transaction categorization (Platform transfers)
- v22.0.0: Asset Unlock Transactions / withdrawals fork
- v22.0.0: `platformban` P2P message
- v23.0.0: EvoDB migration from v19/v20 (Platform-related)
- v23.0.0: Block filter index format update (Platform-related)
- v23.1.0: Credit pool statistics (Platform-related)

---

## Backport Strategy

1. **Cherry-pick approach**: For each P0/P1 item, locate the specific PR in
   the dashpay/dash repository and cherry-pick the commit(s).
2. **Conflict resolution**: v18.2.2 is significantly behind v19+; expect
   merge conflicts. Resolve carefully, preserving the fix logic.
3. **Test verification**: After each backport, run:
   - `./src/test/test_dash` (unit tests)
   - `./test/functional/test_runner.py` (functional tests)
   - Regtest with masternode setup (ChainLocks, InstantSend)
4. **Platform code exclusion**: When cherry-picking, skip any hunks that
   touch Platform-only code (asset unlocks, credit pool, platformban, etc.).
5. **Dependency updates**: Consider updating bundled libraries (Qt, libevent,
   etc.) independently of Dash Core release backports for CVE coverage.

---

## Summary

| Priority | Count | Action |
|----------|-------|--------|
| P0 Critical | 4 | Must backport before any mainnet launch |
| P1 High | 11 | Should backport before launch |
| P2 Medium | 18 | Backport when feasible, especially networking/DoS fixes |
| P3 Low | 10 | Optional, build/CI improvements |
| N/A | 8+ | Excluded (Platform-only) |
