---
description: Build the Tauri wallet for all platforms (macOS ARM/Intel, Windows, Linux) via GitHub Actions
---

## Build Tauri Wallet via GitHub Actions

The workflow at `.github/workflows/build-tauri-wallet.yml` builds the wallet for all platforms.

### Trigger a release build

1. Tag and push:
   ```
   git tag v0.1.0
   git push origin v0.1.0
   ```
   This triggers builds for macOS (ARM + Intel), Windows, and Linux in parallel.

2. Or trigger manually from GitHub Actions tab → "Build Tauri Wallet" → "Run workflow".

### Outputs

Each platform produces installers attached to a draft GitHub Release:

- **macOS ARM**: `Dashbase Wallet_*_aarch64.dmg`
- **macOS Intel**: `Dashbase Wallet_*_x64.dmg`
- **Windows**: `Dashbase Wallet_*_x64-setup.exe` (NSIS) + `*.msi`
- **Linux**: `dashbase-wallet_*.AppImage` + `dashbase-wallet_*.deb`

### Code signing (optional)

Set these GitHub secrets for macOS signing + notarization:

- `APPLE_CERTIFICATE` — base64-encoded .p12 certificate
- `APPLE_CERTIFICATE_PASSWORD` — certificate password
- `APPLE_SIGNING_IDENTITY` — signing identity name (e.g. "Developer ID Application: ...")
- `APPLE_TEAM_ID` — Apple Team ID
- `APPLE_ID` — Apple ID email (for notarization)
- `APPLE_PASSWORD` — app-specific password (for notarization)

Without these secrets, builds produce unsigned/ad-hoc signed packages.
