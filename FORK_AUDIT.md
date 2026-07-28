# FORK AUDIT — Dash Core v18.2.2

**Base version:** Dash Core v18.2.2 (tag `v18.2.2`, March 2023)  
**Audit date:** 2025-07-28  
**Purpose:** Inventory all chain-identity, branding, and Platform/Evolution remnants before any modifications.

---

## 1. Platform / Evolution Remnants

**Finding:** v18.2.2 is the last release before Platform/Evolution code was introduced in v19.0.0. There is **no** Platform/Evolution subsystem code (no GroveDB, no Rust FFI, no DAPI, no Drive, no evonode registration types, no credit pool routing). However, there are **minor Platform-related hooks** already present in the Core layer that should be stripped or neutralized in Phase 2.

### 1.1 `llmqTypePlatform` — Consensus Parameter

| File | Line(s) | Description |
|------|---------|-------------|
| `src/consensus/params.h` | 124 | `LLMQType llmqTypePlatform{LLMQType::LLMQ_NONE};` — field declaration |
| `src/chainparams.cpp` | 298 | Mainnet: `consensus.llmqTypePlatform = Consensus::LLMQType::LLMQ_100_67;` |
| `src/chainparams.cpp` | 519 | Testnet: `consensus.llmqTypePlatform = Consensus::LLMQType::LLMQ_25_67;` |
| `src/chainparams.cpp` | 721 | Devnet: `consensus.llmqTypePlatform = Consensus::LLMQType::LLMQ_100_67;` |
| `src/chainparams.cpp` | 990 | Regtest: `consensus.llmqTypePlatform = Consensus::LLMQType::LLMQ_TEST;` |

**Action:** Remove the `llmqTypePlatform` field and all assignments. This LLMQ type was reserved for Dash Platform's use and is not needed for ChainLocks/InstantSend.

### 1.2 Platform LLMQ Quorum Types

| File | Line(s) | Description |
|------|---------|-------------|
| `src/llmq/params.h` | 372–378 | `LLMQ_100_67` quorum — comment: "Used by Dash Platform" |
| `src/llmq/params.h` | 399–405 | `LLMQ_25_67` quorum — comment: "Used by Dash Platform" |
| `src/chainparams.cpp` | 294 | Mainnet: `AddLLMQ(Consensus::LLMQType::LLMQ_100_67);` |
| `src/chainparams.cpp` | 514–515 | Testnet: `AddLLMQ` for `LLMQ_100_67` and `LLMQ_25_67` |
| `src/chainparams.cpp` | 715 | Devnet: `AddLLMQ(Consensus::LLMQType::LLMQ_100_67);` |

**Action:** Remove `LLMQ_100_67` and `LLMQ_25_67` quorum type registrations and their parameter definitions. These are Platform-only quorum types.

### 1.3 Platform RPC User Restrictions

| File | Line(s) | Description |
|------|---------|-------------|
| `src/init.cpp` | 751 | `-platform-user=<user>` argument definition |
| `src/rpc/server.cpp` | 32 | `mapPlatformRestrictions` parameter in `ExecuteCommand` |
| `src/rpc/server.cpp` | 34–35 | `defaultPlatformUser = "platform-user"` |
| `src/rpc/server.cpp` | 140–150 | `InitPlatformRestrictions()` — restricts platform-user to a whitelist of RPCs |
| `src/rpc/server.cpp` | 147 | References `Params().GetConsensus().llmqTypePlatform` |
| `src/rpc/server.cpp` | 469–477 | `ExecuteCommand` passes `mapPlatformRestrictions` |
| `src/rpc/server.cpp` | 480–541 | Platform-user filtering logic in `ExecuteCommand` |
| `src/rpc/server.h` | 139 | `mapPlatformRestrictions` member declaration |
| `src/rpc/server.h` | 144 | `InitPlatformRestrictions()` method declaration |
| `src/rpc/protocol.h` | 51 | `RPC_PLATFORM_RESTRICTION = -33` error code |

**Action:** Remove the entire platform-user RPC restriction subsystem: the `-platform-user` argument, `InitPlatformRestrictions()`, `mapPlatformRestrictions`, the filtering logic in `ExecuteCommand`, and the `RPC_PLATFORM_RESTRICTION` error code.

### 1.4 LLMQ Utility — Platform Type Check

| File | Line(s) | Description |
|------|---------|-------------|
| `src/llmq/utils.cpp` | 640 | `IsInstantSendLLMQTypeShared()` checks if InstantSend LLMQ type equals `llmqTypePlatform` |

**Action:** Remove the `llmqTypePlatform` comparison from this function (will be resolved when the field is removed from consensus params).

### 1.5 Test — Platform LLMQ Type References

| File | Line(s) | Description |
|------|---------|-------------|
| `src/test/evo_utils_tests.cpp` | 34–36 | `BOOST_CHECK_EQUAL` assertions referencing `consensus_params.llmqTypePlatform` |

**Action:** Remove these three test assertions.

### 1.6 Summary of Platform Remnants

| Category | Files | Severity |
|----------|-------|----------|
| `llmqTypePlatform` consensus field | 5 files | Low — unused without Platform, but should be removed for cleanliness |
| Platform LLMQ quorum types (`LLMQ_100_67`, `LLMQ_25_67`) | 2 files | Low — registered but never used for Core operations |
| Platform RPC user restrictions | 4 files | Low — feature is inert without Platform, but adds dead code |
| Test references | 1 file | Low — test assertions only |

**Verdict:** No Platform/Evolution subsystem code exists. All remnants are minor hooks that can be safely removed in Phase 2 with no impact on Core functionality (DIP3, LLMQ, ChainLocks, InstantSend, governance, CoinJoin, PoSe).

---

## 2. Chain Identity Files

### 2.1 `src/chainparams.cpp` — Primary Chain Parameters

This is the **most critical file** for forking. It defines parameters for four networks.

#### Mainnet (`CMainParams`)

| Parameter | Value | Line(s) |
|-----------|-------|---------|
| **Network ID** | `CBaseChainParams::MAIN` ("main") | 140 |
| **Subsidy halving interval** | 210240 | 141 |
| **MN payments start block** | 100000 | 142 |
| **MN payments increase block** | 158000 | 143 |
| **MN payments increase period** | 576×30 (17280) | 144 |
| **InstantSend confirmations** | 6 | 145 |
| **InstantSend keep lock** | 24 | 146 |
| **Budget payments start block** | 328008 | 147 |
| **Budget cycle blocks** | 16616 | 148 |
| **Budget window blocks** | 100 | 149 |
| **Superblock start block** | 614820 | 150 |
| **Superblock start hash** | `0x0000000000020cb2...` | 151 |
| **Superblock cycle** | 16616 | 152 |
| **Superblock maturity window** | 1662 | 153 |
| **Governance min quorum** | 10 | 154 |
| **Governance filter elements** | 20000 | 155 |
| **MN min confirmations** | 15 | 156 |
| **BIP34 height** | 951 | 157 |
| **BIP34 hash** | `0x000001f35e70...` | 158 |
| **BIP65 height** | 619382 | 159 |
| **BIP66 height** | 245817 | 160 |
| **DIP0001 height** | 782208 | 161 |
| **DIP0003 height** | 1028160 | 162 |
| **DIP0003 enforcement height** | 1047200 | 163 |
| **Message start (magic bytes)** | `0xbf 0x0c 0x6b 0xbd` | 252–255 |
| **Default P2P port** | 9999 | 256 |
| **Prune after height** | 100000 | 257 |
| **Assumed blockchain size** | 45 GB | 258 |
| **Assumed chainstate size** | 1 GB | 259 |
| **Genesis timestamp** | 1390095618 | 261 |
| **Genesis nonce** | 28917698 | 261 |
| **Genesis difficulty** | 0x1e0ffff0 | 261 |
| **Genesis version** | 1 | 261 |
| **Genesis reward** | 50 COIN (5000000000 duffs) | 261 |
| **Genesis block hash** | `0x00000ffd590b1485...` | 263 |
| **Genesis Merkle root** | `0xe0028eb9648db56b...` | 264 |
| **DNS seeds** | `dnsseed.dash.org` | 271 |
| **Base58 pubkey prefix** | 76 ('X') | 274 |
| **Base58 script prefix** | 16 ('7') | 276 |
| **Base58 secret key prefix** | 204 | 278 |
| **BIP32 ext public key** | `0x0488B21E` (xpub) | 280 |
| **BIP32 ext secret key** | `0x0488ADE4` (xprv) | 282 |
| **BIP44 coin type** | 5 | 285 |
| **LLMQ ChainLocks type** | `LLMQ_400_60` | 295 |
| **LLMQ InstantSend type** | `LLMQ_50_60` | 296 |
| **LLMQ DIP0024 IS type** | `LLMQ_60_75` | 297 |
| **LLMQ Platform type** | `LLMQ_100_67` | 298 (remove) |
| **LLMQ MNHF type** | `LLMQ_400_85` | 299 |
| **Spork addresses** | `Xgtyuk76vhuFW2iT7UAiHgNdWXCf3J34wh` | 314 |
| **Min spork keys** | 1 | 315 |
| **BIP9 check MNs upgraded** | true | 316 |
| **Checkpoints** | 20 entries (blocks 1500–1796500) | 318–355 |
| **Chain tx data** | timestamp 1672374042, tx count 5722721 | 357–359 |

#### Testnet (`CTestNetParams`)

| Parameter | Value | Line(s) |
|-----------|-------|---------|
| **Network ID** | `CBaseChainParams::TESTNET` ("test") | 413 |
| **Message start** | `0xce 0xe2 0xca 0xff` | 474–477 |
| **Default P2P port** | 19999 | 478 |
| **Genesis timestamp** | 1390666206 | 483 |
| **Genesis nonce** | 3861367235 | 483 |
| **Genesis difficulty** | 0x1e0ffff0 | 483 |
| **Genesis reward** | 50 COIN | 483 |
| **Genesis block hash** | `0x00000bafbc94add7...` | 485 |
| **DNS seeds** | `testnet-seed.dashdot.io` | 493 |
| **Base58 pubkey prefix** | 140 ('y') | 496 |
| **Base58 script prefix** | 19 ('8'/'9') | 498 |
| **Base58 secret key prefix** | 239 | 500 |
| **BIP44 coin type** | 1 | 507 |
| **LLMQ Platform type** | `LLMQ_25_67` | 519 (remove) |
| **Spork addresses** | `yjPtiKh2uwk3bDutTEA2q9mCtXyiZRWn55` | 535 |
| **Checkpoints** | 9 entries (blocks 261–808000) | 539–551 |

#### Devnet (`CDevNetParams`)

| Parameter | Value | Line(s) |
|-----------|-------|---------|
| **Network ID** | `CBaseChainParams::DEVNET` ("devnet") | 569 |
| **Message start** | `0xe2 0xca 0xff 0xce` | 674–677 |
| **Default P2P port** | 19799 | 678 |
| **Genesis timestamp** | 1417713337 | 684 |
| **Genesis nonce** | 1096447 | 684 |
| **Genesis difficulty** | 0x207fffff | 684 |
| **Genesis block hash** | `0x000008ca1832a4ba...` | 686 |
| **Base58 prefixes** | Same as testnet (140, 19, 239) | 697–705 |
| **BIP44 coin type** | 1 | 708 |
| **LLMQ Platform type** | `LLMQ_100_67` | 721 (remove) |
| **Spork addresses** | `yjPtiKh2uwk3bDutTEA2q9mCtXyiZRWn55` | 743 |

#### Regtest (`CRegTestParams`)

| Parameter | Value | Line(s) |
|-----------|-------|---------|
| **Network ID** | `CBaseChainParams::REGTEST` ("regtest") | 842 |
| **Message start** | `0xfc 0xc1 0xb7 0xdc` | 915–918 |
| **Default P2P port** | 19899 | 919 |
| **Genesis timestamp** | 1417713337 | 929 |
| **Genesis nonce** | 1096447 | 929 |
| **Genesis difficulty** | 0x207fffff | 929 |
| **Genesis block hash** | `0x000008ca1832a4ba...` | 931 |
| **Base58 prefixes** | Same as testnet (140, 19, 239) | 969–977 |
| **BIP44 coin type** | 1 | 980 |
| **LLMQ Platform type** | `LLMQ_TEST` | 990 (remove) |
| **Spork addresses** | `yj949n1UH6fDhw6HtVE5VMj2iSTaSWBMcW` | 951 |

### 2.2 `src/chainparams.h` — CChainParams Class

| Item | Line(s) | Description |
|------|---------|-------------|
| `pchMessageStart` | 119 | Message start chars array (4 bytes) |
| `nDefaultPort` | 120 | P2P port |
| `genesis` | 128 | Genesis block |
| `devnetGenesis` | 129 | Devnet genesis block |
| `base58Prefixes[]` | 125 | Array of Base58 prefix vectors |
| `nExtCoinType` | 126 | BIP44 coin type |
| `strNetworkID` | 127 | Network identifier string |
| `vFixedSeeds` | 130 | Fixed seed nodes |
| `GenesisBlock()` | 65 | Accessor for genesis block |
| `GetDefaultPort()` | 63 | Accessor for P2P port |
| `MessageStart()` | 62 | Accessor for magic bytes |

### 2.3 `src/chainparamsbase.cpp` — Base Chain Parameters (RPC ports, data dirs)

| Network | RPC Port | Data Dir | Line(s) |
|---------|----------|----------|---------|
| Main | 9998 | `""` (default) | 54 |
| Testnet | 19998 | `"testnet3"` | 56 |
| Devnet | 19798 | `gArgs.GetDevNetName()` | 58 |
| Regtest | 19898 | `"regtest"` | 60 |

### 2.4 `src/chainparamsseeds.h` — Fixed Seed Nodes

| Array | Description | Line(s) |
|-------|-------------|---------|
| `pnSeed6_main[]` | Mainnet fixed seeds (all port 9999) | 10–97 |
| `pnSeed6_test[]` | Testnet fixed seeds (all port 19999) | 99–193 |

**Action:** Clear both arrays for a new fork. New seeds will be added as the fork's network grows.

### 2.5 `src/consensus/params.h` — Consensus Parameters

| Field | Line | Description |
|-------|------|-------------|
| `nSubsidyHalvingInterval` | — | Block reward halving interval |
| `nMasternodePaymentsStartBlock` | — | MN payments start |
| `nInstantSendConfirmationsRequired` | — | IS confirmations |
| `nBudgetPaymentsStartBlock` | — | Budget payments start |
| `nSuperblockStartBlock` | — | Superblock start |
| `nSuperblockCycle` | — | Superblock cycle length |
| `llmqTypeChainLocks` | 121 | LLMQ type for ChainLocks |
| `llmqTypeInstantSend` | 122 | LLMQ type for InstantSend |
| `llmqTypeDIP0024InstantSend` | 123 | LLMQ type for DIP24 IS |
| `llmqTypePlatform` | 124 | **Remove** — Platform LLMQ type |
| `llmqTypeMnhf` | 125 | LLMQ type for MNHF |
| `hashGenesisBlock` | — | Genesis block hash |
| `powLimit` | — | PoW difficulty limit |
| `fPowAllowMinDifficultyBlocks` | — | Allow min difficulty |
| `nPowTargetSpacing` | — | Block time target |
| `nPowTargetTimespan` | — | Difficulty adjustment window |

---

## 3. Hardcoded Branding Strings

### 3.1 Client Name & Version

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `src/clientversion.cpp` | 15 | `"Dash Core"` | `CLIENT_NAME` — reported in version message |
| `configure.ac` | 2–4 | `18`, `2`, `2` | Client version major/minor/build |
| `configure.ac` | 9 | `[Dash Core]` | `COPYRIGHT_HOLDERS_SUBSTITUTION` |
| `configure.ac` | 10 | `Dash Core` | `AC_INIT` package name |
| `configure.ac` | 10 | `dashcore` | Package tarname |
| `configure.ac` | 10 | `https://dash.org/` | Package URL |
| `configure.ac` | 10 | `https://github.com/dashpay/dash/issues` | Bug report URL |

### 3.2 Binary Names

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `configure.ac` | 16 | `dashd` | Daemon name (`BITCOIN_DAEMON_NAME`) |
| `configure.ac` | 17 | `dash-qt` | GUI name (`BITCOIN_GUI_NAME`) |
| `configure.ac` | 18 | `dash-cli` | CLI name (`BITCOIN_CLI_NAME`) |
| `configure.ac` | 19 | `dash-tx` | TX tool name (`BITCOIN_TX_NAME`) |
| `configure.ac` | 20 | `dash-wallet` | Wallet tool name (`BITCOIN_WALLET_TOOL_NAME`) |

### 3.3 Currency Unit

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `src/policy/feerate.cpp` | 10 | `"DASH"` | `CURRENCY_UNIT` constant |

### 3.4 Config File Name

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `src/util/system.cpp` | 92 | `"dash.conf"` | `BITCOIN_CONF_FILENAME` |

### 3.5 GUI Branding

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `src/qt/guiconstants.h` | 40 | `"Dash"` | `QAPP_ORG_NAME` |
| `src/qt/guiconstants.h` | 41 | `"dash.org"` | `QAPP_ORG_DOMAIN` |
| `src/qt/guiconstants.h` | 42 | `"Dash-Qt"` | `QAPP_APP_NAME_DEFAULT` |
| `src/qt/guiconstants.h` | 43 | `"Dash-Qt-testnet"` | `QAPP_APP_NAME_TESTNET` |
| `src/qt/guiconstants.h` | 44 | `"Dash-Qt-%s"` | `QAPP_APP_NAME_DEVNET` |
| `src/qt/guiconstants.h` | 45 | `"Dash-Qt-regtest"` | `QAPP_APP_NAME_REGTEST` |
| `src/qt/bitcoinunits.cpp` | 21–24 | `DASH`, `mDASH`, `uDASH`, `duffs` | Unit enum values |

### 3.6 URLs (Source Code, Website, Docs)

| File | Line(s) | URL | Description |
|------|---------|-----|-------------|
| `src/init.cpp` | 801 | `https://github.com/dashpay/dash` | `URL_SOURCE_CODE` |
| `src/init.cpp` | 802 | `https://dash.org` | `URL_WEBSITE` |
| `src/qt/utilitydialog.cpp` | 144 | `https://docs.dash.org/en/stable/wallets/dashcore/coinjoin-instantsend.html` | CoinJoin docs link |
| `src/qt/sendcoinsdialog.cpp` | 411 | `https://docs.dash.org/en/stable/wallets/dashcore/coinjoin-instantsend.html#inputs` | CoinJoin privacy docs link |

### 3.7 DNS Seeds

| File | Line(s) | String | Network |
|------|---------|--------|---------|
| `src/chainparams.cpp` | 271 | `dnsseed.dash.org` | Mainnet |
| `src/chainparams.cpp` | 493 | `testnet-seed.dashdot.io` | Testnet |

### 3.8 Resource Files (Icons, Pixmaps, Windows RC)

| File | Description |
|------|-------------|
| `src/dashd-res.rc` | Windows resource file for dashd |
| `src/dash-tx-res.rc` | Windows resource file for dash-tx |
| `src/dash-cli-res.rc` | Windows resource file (unused, but named) |
| `src/qt/res/dash-qt-res.rc` | Windows resource file for dash-qt |
| `src/qt/dash.qrc` | Qt resource file |
| `src/qt/dashstrings.cpp` | Qt translatable strings |
| `share/pixmaps/dash*.{png,xpm,ico,svg}` | ~25 icon files |
| `src/qt/res/icons/dash.png` | GUI icon |
| `src/qt/res/images/dash_logo_toolbar.png` | Toolbar logo |
| `src/qt/res/images/dash_logo_toolbar_blue.png` | Toolbar logo (blue) |

### 3.9 Debian/Init Packaging

| File | Description |
|------|-------------|
| `contrib/debian/dash.conf` | Example config file |
| `contrib/debian/dash-qt.desktop` | Desktop entry |
| `contrib/debian/dash-qt.protocol` | URL protocol handler |
| `contrib/debian/dashd.install` | Install file |
| `contrib/debian/dashd.manpages` | Manpage list |
| `contrib/debian/dashd.bash-completion` | Bash completion |
| `contrib/debian/dash-qt.install` | Install file |
| `contrib/debian/dash-qt.manpages` | Manpage list |
| `contrib/debian/dash-tx.install` | Install file |
| `contrib/debian/dash-tx.manpages` | Manpage list |
| `contrib/debian/dash-tx.bash-completion` | Bash completion |
| `contrib/init/dashd.service` | Systemd service |
| `contrib/init/dashd.init` | SysV init script |
| `contrib/init/dashd.openrc` | OpenRC script |
| `contrib/init/dashd.openrcconf` | OpenRC config |
| `contrib/init/dashd.conf` | Init config |

### 3.3 Man Pages

| File | Description |
|------|-------------|
| `doc/man/dashd.1` | Daemon manpage |
| `doc/man/dash-cli.1` | CLI manpage |
| `doc/man/dash-qt.1` | GUI manpage |
| `doc/man/dash-tx.1` | TX tool manpage |
| `doc/man/dash-wallet.1` | Wallet tool manpage |

### 3.11 Other Branding References

| File | Line(s) | String | Description |
|------|---------|--------|-------------|
| `src/rpc/governance.cpp` | 473, 497, 514 | `"dash.conf"` | Key in governance vote results |
| `src/pow.cpp` | 82 | `evan@dash.org` | Author comment in DarkGravityWave |
| `src/init.h` | 31, 49, 59 | `"Dash Core"` | Doxygen comments |
| `src/rpc/server.cpp` | 186 | `"Dash Core server"` | RPC help text |
| `doc/dash-conf.md` | — | Documentation for dash.conf |

---

## 4. Build System References

### 4.1 `configure.ac`

| Line(s) | Item | Description |
|---------|------|-------------|
| 9 | `_COPYRIGHT_HOLDERS_SUBSTITUTION` | `[Dash Core]` |
| 10 | `AC_INIT` | Package name, bug URL, tarname, URL |
| 16–20 | Binary names | `dashd`, `dash-qt`, `dash-cli`, `dash-tx`, `dash-wallet` |
| 30–31 | `AH_TOP` | `DASH_CONFIG_H` guard |

### 4.2 `src/Makefile.am`

Contains references to `dashd`, `dash-qt`, `dash-cli`, `dash-tx`, `dash-wallet` binary names and build targets.

### 4.3 `Makefile.am` (root)

Contains references to package name and build configuration.

---

## 5. Ambiguous Items Flagged for Human Decision

### 5.1 `src/evo/` Directory

The `src/evo/` directory name contains "evo" which could be confused with "Evolution." However, this directory contains **DIP3 deterministic masternode code** (ProRegTx, ProUpServTx, ProUpRegTx, ProUpRevTx, deterministic MN list, special tx processing, CBTX, MN auth, simplified MN list). This is **Core-layer functionality** and must be **retained**.

**Files in `src/evo/`:** `cbtx.cpp/h`, `deterministicmns.cpp/h`, `dmnstate.cpp/h`, `evodb.cpp/h`, `mnauth.cpp/h`, `mnhftx.cpp/h`, `providertx.cpp/h`, `simplifiedmns.cpp/h`, `specialtx.cpp/h`, `specialtxman.cpp/h`

**Decision:** Keep all files. The directory name is historical — it predates Dash Platform "Evolution." Consider renaming to `src/dmn/` (deterministic masternodes) in a future cleanup if desired, but this is cosmetic and not required.

### 5.2 `src/rpc/evo.cpp`

Contains RPC commands for deterministic masternodes (`protx` commands). This is Core-layer DIP3 functionality. **Keep.**

### 5.3 `LLMQ_100_67` and `LLMQ_25_67` Quorum Types

These are commented as "Used by Dash Platform" but the LLMQ types themselves are generic threshold signing quorums. A fork could theoretically repurpose them. However, since they are not used by any Core functionality (ChainLocks, InstantSend, MNHF), removing them is cleaner.

**Decision needed:** Remove entirely, or keep the type definitions but remove the `llmqTypePlatform` assignments and `AddLLMQ` registrations? **Recommendation:** Remove entirely — they add dead code and confusion.

### 5.4 Copyright Headers

All source files contain `"The Dash Core developers"` in copyright headers. These are informational and don't affect functionality. **Decision needed:** Update to new project name, or leave as-is for attribution? **Recommendation:** Keep original Dash attribution, add new copyright line for the fork.

---

## 6. Files Summary — Must Touch for New Fork

### Critical (chain identity — must change)

| # | File | Changes |
|---|------|---------|
| 1 | `src/chainparams.cpp` | Magic bytes, ports, genesis, base58 prefixes, DNS seeds, checkpoints, consensus params, spork addresses, BIP44 coin type |
| 2 | `src/chainparams.h` | (Structural — no direct changes needed, but defines the fields) |
| 3 | `src/chainparamsbase.cpp` | RPC ports, data dir names |
| 4 | `src/chainparamsseeds.h` | Fixed seed node IPs |
| 5 | `src/consensus/params.h` | Remove `llmqTypePlatform` field |
| 6 | `src/policy/feerate.cpp` | `CURRENCY_UNIT` string |
| 7 | `src/util/system.cpp` | `BITCOIN_CONF_FILENAME` string |
| 8 | `src/clientversion.cpp` | `CLIENT_NAME` string |
| 9 | `configure.ac` | Package name, version, binary names, copyright holders, URLs |

### Important (branding — should change)

| # | File | Changes |
|---|------|---------|
| 10 | `src/qt/guiconstants.h` | `QAPP_ORG_NAME`, `QAPP_ORG_DOMAIN`, `QAPP_APP_NAME_*` |
| 11 | `src/qt/bitcoinunits.cpp` | Unit enum names (DASH, mDASH, uDASH, duffs) |
| 12 | `src/init.cpp` | `URL_SOURCE_CODE`, `URL_WEBSITE`, remove `-platform-user` arg |
| 13 | `src/qt/utilitydialog.cpp` | Docs URLs |
| 14 | `src/qt/sendcoinsdialog.cpp` | Docs URLs |
| 15 | `src/rpc/server.cpp` | Remove platform-user restriction system |
| 16 | `src/rpc/server.h` | Remove `mapPlatformRestrictions`, `InitPlatformRestrictions` |
| 17 | `src/rpc/protocol.h` | Remove `RPC_PLATFORM_RESTRICTION` |
| 18 | `src/llmq/params.h` | Remove `LLMQ_100_67` and `LLMQ_25_67` definitions |
| 19 | `src/llmq/utils.cpp` | Remove `llmqTypePlatform` reference in `IsInstantSendLLMQTypeShared` |
| 20 | `src/test/evo_utils_tests.cpp` | Remove `llmqTypePlatform` test assertions |

### Cosmetic (packaging/icons — change before release)

| # | File(s) | Changes |
|---|---------|---------|
| 21 | `src/Makefile.am` | Binary names |
| 22 | `Makefile.am` | Package name |
| 23 | `share/pixmaps/dash*` | Replace icons |
| 24 | `src/qt/res/icons/dash.png` | Replace icon |
| 25 | `src/qt/res/images/dash_logo*` | Replace logos |
| 26 | `src/dashd-res.rc`, `src/dash-tx-res.rc`, `src/qt/res/dash-qt-res.rc` | Windows resource files |
| 27 | `src/qt/dash.qrc`, `src/qt/dashstrings.cpp` | Qt resources |
| 28 | `contrib/debian/*` | Debian packaging |
| 29 | `contrib/init/*` | Init scripts |
| 30 | `doc/man/*` | Man pages |
| 31 | `doc/dash-conf.md` | Config documentation |
| 32 | `contrib/dash-qt.pro` | Qt project file |
| 33 | `contrib/*.bash-completion` | Bash completion files |

---

## 7. What Is NOT Present (Confirmed Absent)

The following Platform/Evolution components are **not present** in v18.2.2 and require no stripping:

- **GroveDB** bindings or FFI
- **Rust toolchain** dependencies or build steps
- **Drive** (data store) code
- **DAPI** (Dash Platform API) code
- **Evonode** registration types or credit pool
- **Platform RPCs** (beyond the platform-user restriction wrapper)
- **Platform-specific consensus rules**
- **L2 transaction types**
- **Data contracts / state transitions**
- **Document store / data store validation**

---

## 8. Conclusion

The v18.2.2 base is remarkably clean for forking purposes. The Platform remnants are limited to:

1. A single consensus field (`llmqTypePlatform`) with 4 assignments
2. Two Platform-only LLMQ quorum type registrations
3. A platform-user RPC restriction subsystem (~60 lines across 4 files)
4. Three test assertions

**Total stripping effort:** Minimal — estimated at removing ~100 lines of code across 8 files, with no impact on Core functionality.

The primary forking work will be in **chain identity parameterization** (`chainparams.cpp`, `chainparamsbase.cpp`, `chainparamsseeds.h`) and **branding string replacement** (~33 files, many cosmetic/packaging).
