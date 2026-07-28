# Masternode Chain Base (Dash Core v18.2.2 Fork)

A clean, rebrandable masternode blockchain base forked from Dash Core v18.2.2 —
the last release before Dash Platform/Evolution was merged. This project strips
Platform-specific code and provides a parameterized foundation for launching a
new masternode-based cryptocurrency.

## What This Is

- **Fork of Dash Core v18.2.2** — battle-tested masternode consensus, governance, and LLMQ
- **Platform code removed** — no Evolution/Platform remnants (LLMQ_100_67, LLMQ_25_67, `platform-user` RPC restrictions)
- **Rebrandable** — all chain identity parameters centralized in [`chainbrand.json`](chainbrand.json)
- **Automated branding** — [`scripts/new-fork.sh`](scripts/new-fork.sh) applies branding changes across the codebase
- **CI builds** — GitHub Actions workflow builds Linux daemon, Windows, and macOS binaries

## What's Retained

- DIP3 deterministic masternodes
- LLMQ (Long-Living Masternode Quorums) for ChainLocks and InstantSend
- On-chain governance (proposals, superblocks, voting)
- CoinJoin privacy features
- SPV wallet support with Qt GUI

## Build Status

| Platform | Status |
|----------|--------|
| Linux Daemon | [![Build](https://github.com/safuapy/dashbase/actions/workflows/build-wallets.yml/badge.svg?branch=main)](https://github.com/safuapy/dashbase/actions) |
| Windows | [![Build](https://github.com/safuapy/dashbase/actions/workflows/build-wallets.yml/badge.svg?branch=main)](https://github.com/safuapy/dashbase/actions) |
| macOS Intel | [![Build](https://github.com/safuapy/dashbase/actions/workflows/build-wallets.yml/badge.svg?branch=main)](https://github.com/safuapy/dashbase/actions) |

## Quick Start

### Build from Source

```bash
# Linux daemon (no GUI)
cd depends && make HOST=x86_64-pc-linux-gnu NO_QT=1 -j$(nproc) && cd ..
./autogen.sh
./configure --prefix=/usr/local --without-gui \
  CPPFLAGS="-I$PWD/depends/x86_64-pc-linux-gnu/include" \
  LDFLAGS="-L$PWD/depends/x86_64-pc-linux-gnu/lib"
make -j$(nproc)
make install DESTDIR="$PWD/release"
```

See [`doc/build-generic.md`](doc/build-generic.md) and [`doc/build-cross.md`](doc/build-cross.md)
for cross-compilation instructions (Windows, macOS).

### Rebrand the Chain

1. Edit [`chainbrand.json`](chainbrand.json) with your chain's parameters
2. Run `bash scripts/new-fork.sh` to apply branding across the codebase
3. Rebuild

See [`FORK_GUIDE.md`](FORK_GUIDE.md) for the complete fork guide.

## Documentation

- [**Fork Guide**](FORK_GUIDE.md) — comprehensive step-by-step fork process
- [**Fork Audit**](FORK_AUDIT.md) — chain identity parameters and Platform remnants audit
- [**Security Backports**](SECURITY_BACKPORTS.md) — security fixes from Dash Core v19-v23 for backporting
- [**Chain Brand Config**](chainbrand.json) — centralized rebrandable values
- [**Branding Script**](scripts/new-fork.sh) — automated branding application

## Project Structure

```
├── .github/workflows/    # CI build workflows
├── chainbrand.json        # Centralized branding configuration
├── scripts/new-fork.sh    # Automated branding script
├── depends/               # Cross-compilation dependency system
├── src/                   # Core node implementation
│   ├── evo/               # DIP3 deterministic masternodes
│   ├── llmq/              # Long-Living Masternode Quorums
│   ├── governance/         # On-chain governance
│   └── qt/                # Qt wallet GUI
├── FORK_GUIDE.md          # Complete fork documentation
├── FORK_AUDIT.md          # Chain identity audit
└── SECURITY_BACKPORTS.md  # Security backport tracking
```

## License

MIT License — see [COPYING](COPYING) for details.

## Acknowledgements

Based on [Dash Core](https://github.com/dashpay/dash) v18.2.2 by the Dash Core Team.
Dash Core is itself based on [Bitcoin Core](https://github.com/bitcoin/bitcoin).
