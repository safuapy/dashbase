#!/usr/bin/env bash
#
# new-fork.sh — Apply chain branding from chainbrand.json to the Dash Core fork
#
# Usage: ./scripts/new-fork.sh [path/to/chainbrand.json]
#
# This script reads the chainbrand.json configuration file and applies all
# branding, chain identity, and binary name changes across the codebase.
#
# It uses jq for JSON parsing and sed for text replacement.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="${1:-$REPO_ROOT/chainbrand.json}"

if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed. Install with: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "=== Dash Core Fork Branding Script ==="
echo "Config: $CONFIG_FILE"
echo ""

# Helper: read a value from the JSON config
jq_val() {
    jq -r "$1" "$CONFIG_FILE"
}

# Helper: read an array as space-separated values
jq_arr() {
    jq -r "$1 | join(\" \")" "$CONFIG_FILE"
}

# ── Read chain identity values ────────────────────────────────────
CHAIN_NAME=$(jq_val '.chain.name')
CHAIN_TICKER=$(jq_val '.chain.ticker')
CURRENCY_UNIT=$(jq_val '.chain.currency_unit')
CLIENT_NAME=$(jq_val '.chain.client_name')
CONF_FILE=$(jq_val '.chain.conf_file')
DATA_DIR=$(jq_val '.chain.data_dir')
ORG_NAME=$(jq_val '.chain.organization')
DOMAIN=$(jq_val '.chain.domain')

# Binaries
BIN_DAEMON=$(jq_val '.binaries.daemon')
BIN_QT=$(jq_val '.binaries.qt')
BIN_CLI=$(jq_val '.binaries.cli')
BIN_TX=$(jq_val '.binaries.tx')
BIN_WALLET=$(jq_val '.binaries.wallet')
BIN_UTIL=$(jq_val '.binaries.util')

# Build
PKG_NAME=$(jq_val '.build.package_name')
COPYRIGHT_HOLDER=$(jq_val '.build.copyright_holder')
COPYRIGHT_YEAR=$(jq_val '.build.copyright_year')
WEBSITE_URL=$(jq_val '.build.website_url')
SOURCE_URL=$(jq_val '.build.source_url')

# GUI
GUI_ORG_NAME=$(jq_val '.gui.organization_name')
GUI_ORG_DOMAIN=$(jq_val '.gui.organization_domain')
GUI_APP_MAINNET=$(jq_val '.gui.application_name_mainnet')
GUI_APP_TESTNET=$(jq_val '.gui.application_name_testnet')
GUI_APP_REGTEST=$(jq_val '.gui.application_name_regtest')

# Network
MAIN_MAGIC=$(jq_arr '.network.mainnet.magic_bytes')
MAIN_PORT=$(jq_val '.network.mainnet.default_port')
MAIN_RPC_PORT=$(jq_val '.network.mainnet.rpc_port')
MAIN_DNS_SEED=$(jq_val '.network.mainnet.dns_seeds[0]')
MAIN_COIN_TYPE=$(jq_val '.network.mainnet.bip44_coin_type')
MAIN_PUBKEY_PREFIX=$(jq_val '.network.mainnet.base58_prefixes.pubkey_address')
MAIN_SCRIPT_PREFIX=$(jq_val '.network.mainnet.base58_prefixes.script_address')
MAIN_SECRET_PREFIX=$(jq_val '.network.mainnet.base58_prefixes.secret_key')

TEST_MAGIC=$(jq_arr '.network.testnet.magic_bytes')
TEST_PORT=$(jq_val '.network.testnet.default_port')
TEST_RPC_PORT=$(jq_val '.network.testnet.rpc_port')
TEST_DNS_SEED=$(jq_val '.network.testnet.dns_seeds[0]')
TEST_COIN_TYPE=$(jq_val '.network.testnet.bip44_coin_type')
TEST_PUBKEY_PREFIX=$(jq_val '.network.testnet.base58.pubkey_address')
TEST_SCRIPT_PREFIX=$(jq_val '.network.testnet.base58.script_address')
TEST_SECRET_PREFIX=$(jq_val '.network.testnet.base58.secret_key')

REGTEST_MAGIC=$(jq_arr '.network.regtest.magic_bytes')
REGTEST_PORT=$(jq_val '.network.regtest.default_port')
REGTEST_RPC_PORT=$(jq_val '.network.regtest.rpc_port')

echo "Chain: $CHAIN_NAME ($CHAIN_TICKER)"
echo "Client: $CLIENT_NAME"
echo "Binaries: $BIN_DAEMON, $BIN_QT, $BIN_CLI, $BIN_TX, $BIN_WALLET"
echo ""

# ── Confirm before proceeding ─────────────────────────────────────
read -p "This will modify files in $REPO_ROOT. Continue? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# ── Helper: replace in file with backup ───────────────────────────
replace_in_file() {
    local file="$1"
    local old="$2"
    local new="$3"
    if [ -f "$file" ]; then
        sed -i.bak "s|$old|$new|g" "$file" && rm -f "${file}.bak"
    fi
}

# ── 1. configure.ac ───────────────────────────────────────────────
echo "[1/12] Updating configure.ac..."
AC_FILE="$REPO_ROOT/configure.ac"
if [ -f "$AC_FILE" ]; then
    replace_in_file "$AC_FILE" "Dash Core" "$CLIENT_NAME"
    replace_in_file "$AC_FILE" "dashpay/dash" "$(echo "$SOURCE_URL" | sed 's|https://github.com/||')"
    replace_in_file "$AC_FILE" "https://github.com/dashpay/dash" "$SOURCE_URL"
    replace_in_file "$AC_FILE" "dash.org" "$DOMAIN"
    # Binary names in configure.ac
    replace_in_file "$AC_FILE" "dashd" "$BIN_DAEMON"
    replace_in_file "$AC_FILE" "dash-qt" "$BIN_QT"
    replace_in_file "$AC_FILE" "dash-cli" "$BIN_CLI"
    replace_in_file "$AC_FILE" "dash-tx" "$BIN_TX"
    replace_in_file "$AC_FILE" "dash-wallet" "$BIN_WALLET"
fi

# ── 2. clientversion.cpp ──────────────────────────────────────────
echo "[2/12] Updating clientversion.cpp..."
CV_FILE="$REPO_ROOT/src/clientversion.cpp"
if [ -f "$CV_FILE" ]; then
    replace_in_file "$CV_FILE" '"Dash Core"' "\"$CLIENT_NAME\""
fi

# ── 3. chainparams.cpp — Mainnet identity ─────────────────────────
echo "[3/12] Updating chainparams.cpp (mainnet)..."
CP_FILE="$REPO_ROOT/src/chainparams.cpp"
if [ -f "$CP_FILE" ]; then
    # Message start bytes (mainnet)
    IFS=' ' read -r -a MAGIC <<< "$MAIN_MAGIC"
    replace_in_file "$CP_FILE" "pchMessageStart\[0\] = 0xbf" "pchMessageStart[0] = 0x$(printf '%02x' ${MAGIC[0]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[1\] = 0x0c" "pchMessageStart[1] = 0x$(printf '%02x' ${MAGIC[1]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[2\] = 0x6b" "pchMessageStart[2] = 0x$(printf '%02x' ${MAGIC[2]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[3\] = 0xbd" "pchMessageStart[3] = 0x$(printf '%02x' ${MAGIC[3]})"

    # Default port (mainnet)
    replace_in_file "$CP_FILE" "nDefaultPort = 9999" "nDefaultPort = $MAIN_PORT"

    # DNS seed
    replace_in_file "$CP_FILE" "dnsseed.dash.org" "$MAIN_DNS_SEED"

    # Base58 prefixes (mainnet)
    replace_in_file "$CP_FILE" "base58Prefixes\[PUBKEY_ADDRESS\] = std::vector<unsigned char>(1,76)" "base58Prefixes[PUBKEY_ADDRESS] = std::vector<unsigned char>(1,$MAIN_PUBKEY_PREFIX)"
    replace_in_file "$CP_FILE" "base58Prefixes\[SCRIPT_ADDRESS\] = std::vector<unsigned char>(1,16)" "base58Prefixes[SCRIPT_ADDRESS] = std::vector<unsigned char>(1,$MAIN_SCRIPT_PREFIX)"
    replace_in_file "$CP_FILE" "base58Prefixes\[SECRET_KEY\] =     std::vector<unsigned char>(1,204)" "base58Prefixes[SECRET_KEY] =     std::vector<unsigned char>(1,$MAIN_SECRET_PREFIX)"

    # BIP44 coin type
    replace_in_file "$CP_FILE" "nExtCoinType = 5;" "nExtCoinType = $MAIN_COIN_TYPE;"

    # Genesis block hash assertions — comment them out (new genesis will have different hash)
    # User must recalculate and re-add assertions after genesis generation
    echo "  NOTE: Genesis hash assertions must be updated manually after genesis generation."
fi

# ── 4. chainparams.cpp — Testnet identity ─────────────────────────
echo "[4/12] Updating chainparams.cpp (testnet)..."
if [ -f "$CP_FILE" ]; then
    IFS=' ' read -r -a TMAGIC <<< "$TEST_MAGIC"
    # Testnet message start bytes
    replace_in_file "$CP_FILE" "pchMessageStart\[0\] = 0xfc" "pchMessageStart[0] = 0x$(printf '%02x' ${TMAGIC[0]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[1\] = 0xc3" "pchMessageStart[1] = 0x$(printf '%02x' ${TMAGIC[1]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[2\] = 0xb6" "pchMessageStart[2] = 0x$(printf '%02x' ${TMAGIC[2]})"
    replace_in_file "$CP_FILE" "pchMessageStart\[3\] = 0x31" "pchMessageStart[3] = 0x$(printf '%02x' ${TMAGIC[3]})"

    # Testnet default port
    replace_in_file "$CP_FILE" "nDefaultPort = 19999" "nDefaultPort = $TEST_PORT"

    # Testnet DNS seed
    replace_in_file "$CP_FILE" "testnet-seed.dashdot.io" "$TEST_DNS_SEED"

    # Testnet base58
    replace_in_file "$CP_FILE" "base58Prefixes\[PUBKEY_ADDRESS\] = std::vector<unsigned char>(1,139)" "base58Prefixes[PUBKEY_ADDRESS] = std::vector<unsigned char>(1,$TEST_PUBKEY_PREFIX)"
    replace_in_file "$CP_FILE" "base58Prefixes\[SCRIPT_ADDRESS\] = std::vector<unsigned char>(1,19)" "base58Prefixes[SCRIPT_ADDRESS] = std::vector<unsigned char>(1,$TEST_SCRIPT_PREFIX)"
    replace_in_file "$CP_FILE" "base58Prefixes\[SECRET_KEY\] =     std::vector<unsigned char>(1,239)" "base58Prefixes[SECRET_KEY] =     std::vector<unsigned char>(1,$TEST_SECRET_PREFIX)"

    # Testnet BIP44 coin type
    # Note: This appears as "nExtCoinType = 1;" in testnet section
    # Already handled by mainnet replacement if same value; skip if already replaced
fi

# ── 5. chainparamsbase.cpp — RPC ports and data dirs ──────────────
echo "[5/12] Updating chainparamsbase.cpp..."
CPB_FILE="$REPO_ROOT/src/chainparamsbase.cpp"
if [ -f "$CPB_FILE" ]; then
    # Mainnet RPC port
    replace_in_file "$CPB_FILE" "nRPCPort = 9998" "nRPCPort = $MAIN_RPC_PORT"
    # Testnet RPC port
    replace_in_file "$CPB_FILE" "nRPCPort = 19998" "nRPCPort = $TEST_RPC_PORT"
    # Regtest RPC port
    replace_in_file "$CPB_FILE" "nRPCPort = 19993" "nRPCPort = $REGTEST_RPC_PORT"
    # Data directory name
    replace_in_file "$CPB_FILE" "DashCore" "$DATA_DIR"
fi

# ── 6. chainparamsseeds.h — Clear fixed seeds ─────────────────────
echo "[6/12] Clearing fixed seeds..."
SEEDS_FILE="$REPO_ROOT/src/chainparamsseeds.h"
if [ -f "$SEEDS_FILE" ]; then
    # Replace seed entries with empty arrays
    cat > "$SEEDS_FILE" << 'SEEDS_EOF'
// Copyright (c) 2026 The Dash Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_CHAINPARAMSSEEDS_H
#define BITCOIN_CHAINPARAMSSEEDS_H

/**
 * List of fixed seed nodes for the Dash network.
 * This file is generated and updated by the seeds script.
 * Clear this list for a new fork chain and populate with your own seed nodes.
 */

static SeedSpec6 pnSeed6_main[] = {
};

static SeedSpec6 pnSeed6_test[] = {
};

#endif // BITCOIN_CHAINPARAMSSEEDS_H
SEEDS_EOF
    echo "  Fixed seeds cleared. Add your own seed nodes to chainparamsseeds.h"
fi

# ── 7. util/system.cpp — Config file name ─────────────────────────
echo "[7/12] Updating config file name..."
SYS_FILE="$REPO_ROOT/src/util/system.cpp"
if [ -f "$SYS_FILE" ]; then
    replace_in_file "$SYS_FILE" "dash.conf" "$CONF_FILE"
fi

# ── 8. guiconstants.h — GUI branding ──────────────────────────────
echo "[8/12] Updating GUI constants..."
GUI_FILE="$REPO_ROOT/src/qt/guiconstants.h"
if [ -f "$GUI_FILE" ]; then
    replace_in_file "$GUI_FILE" "Dash Core" "$CLIENT_NAME"
    replace_in_file "$GUI_FILE" "DashCore" "$DATA_DIR"
    replace_in_file "$GUI_FILE" "dash.org" "$DOMAIN"
    replace_in_file "$GUI_FILE" "DashPay" "$ORG_NAME"
    replace_in_file "$GUI_FILE" "Dash-Qt" "$GUI_APP_MAINNET"
    replace_in_file "$GUI_FILE" "Dash-Qt-testnet" "$GUI_APP_TESTNET"
    replace_in_file "$GUI_FILE" "Dash-Qt-regtest" "$GUI_APP_REGTEST"
fi

# ── 9. bitcoinunits.cpp — Currency unit ───────────────────────────
echo "[9/12] Updating currency units..."
UNITS_FILE="$REROOOT/src/qt/bitcoinunits.cpp"
UNITS_FILE="$REPO_ROOT/src/qt/bitcoinunits.cpp"
if [ -f "$UNITS_FILE" ]; then
    replace_in_file "$UNITS_FILE" '"DASH"' "\"$CURRENCY_UNIT\""
    replace_in_file "$UNITS_FILE" '"mDASH"' "\"m$CURRENCY_UNIT\""
    replace_in_file "$UNITS_FILE" '"uDASH"' "\"u$CURRENCY_UNIT\""
fi

# ── 10. Makefiles and build files — Binary names ──────────────────
echo "[10/12] Updating binary names in build files..."
# Find all Makefile.am and .pro files that reference dash binaries
find "$REPO_ROOT/src" -name "Makefile.am" -o -name "*.pro" | while read -r f; do
    replace_in_file "$f" "dashd" "$BIN_DAEMON"
    replace_in_file "$f" "dash-qt" "$BIN_QT"
    replace_in_file "$f" "dash-cli" "$BIN_CLI"
    replace_in_file "$f" "dash-tx" "$BIN_TX"
    replace_in_file "$f" "dash-wallet" "$BIN_WALLET"
done

# ── 11. init.cpp — URLs and branding ──────────────────────────────
echo "[11/12] Updating init.cpp URLs..."
INIT_FILE="$REPO_ROOT/src/init.cpp"
if [ -f "$INIT_FILE" ]; then
    replace_in_file "$INIT_FILE" "https://github.com/dashpay/dash" "$SOURCE_URL"
    replace_in_file "$INIT_FILE" "https://www.dash.org" "$WEBSITE_URL"
fi

# ── 12. Clear checkpoints ─────────────────────────────────────────
echo "[12/12] Clearing checkpoints..."
if [ -f "$CP_FILE" ]; then
    # Comment out checkpoint data — user should add new checkpoints after chain launch
    echo "  NOTE: Checkpoints in chainparams.cpp should be cleared manually for a fresh chain."
    echo "  The existing Dash checkpoints are not valid for your new chain."
fi

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo "=== Branding Complete ==="
echo ""
echo "Manual steps remaining:"
echo "  1. Generate new genesis block and update genesis hash assertions in chainparams.cpp"
echo "  2. Clear old Dash checkpoints in chainparams.cpp (mainnet + testnet)"
echo "  3. Update minimum_chain_work and default_assume_valid in chainparams.cpp"
echo "  4. Add your own seed nodes to chainparamsseeds.h"
echo "  5. Update spork addresses in chainparams.cpp"
echo "  6. Run ./autogen.sh && ./configure && make to verify build"
echo "  7. Run tests: ./src/test/test_dash && ./test/functional/test_runner.py"
echo ""
echo "IMPORTANT: The genesis block hash will change when you modify timestamp/nonce."
echo "You must recalculate it and update the assert() statements in chainparams.cpp."
