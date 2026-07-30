"""Consensus parameter patches for chainparams.cpp.

Patches: subsidy halving, PoW params, masternode payments, budget/governance,
BIP34/65/66 heights, DIP heights, BIP9 deployments, LLMQ quorum config.
"""

import os
import re
from typing import List
from .file_patcher import (
    patch_file, patch_file_regex, read_file, write_file,
    PatchResult
)


# Map deployment names to Consensus::DeploymentPos enum values
DEPLOYMENT_MAP = {
    "TESTDUMMY": "DEPLOYMENT_TESTDUMMY",
    "CSV": "DEPLOYMENT_CSV",
    "DIP0001": "DEPLOYMENT_DIP0001",
    "BIP147": "DEPLOYMENT_BIP147",
    "DIP0003": "DEPLOYMENT_DIP0003",
    "DIP0008": "DEPLOYMENT_DIP0008",
    "REALLOC": "DEPLOYMENT_REALLOC",
    "DIP0020": "DEPLOYMENT_DIP0020",
    "DIP0024": "DEPLOYMENT_DIP0024",
}

# Map LLMQ type names to enum values
LLMQ_MAP = {
    "LLMQ_50_60": "Consensus::LLMQType::LLMQ_50_60",
    "LLMQ_60_75": "Consensus::LLMQType::LLMQ_60_75",
    "LLMQ_400_60": "Consensus::LLMQType::LLMQ_400_60",
    "LLMQ_400_85": "Consensus::LLMQType::LLMQ_400_85",
    "LLMQ_TEST": "Consensus::LLMQType::LLMQ_TEST",
    "LLMQ_TEST_INSTANTSEND": "Consensus::LLMQType::LLMQ_TEST_INSTANTSEND",
    "LLMQ_TEST_V17": "Consensus::LLMQType::LLMQ_TEST_V17",
    "LLMQ_TEST_DIP0024": "Consensus::LLMQType::LLMQ_TEST_DIP0024",
    "LLMQ_DEVNET": "Consensus::LLMQType::LLMQ_DEVNET",
    "LLMQ_DEVNET_DIP0024": "Consensus::LLMQType::LLMQ_DEVNET_DIP0024",
}


def apply_consensus_params(repo_root: str, config: dict, old_config: dict = None) -> List[PatchResult]:
    """Apply consensus parameter changes to chainparams.cpp.

    Args:
        repo_root: Absolute path to repo root
        config: New chainbrand config with 'consensus' section
        old_config: Old config (defaults to Dashbase values)
    Returns:
        List of PatchResult objects
    """
    if old_config is None:
        old_config = _default_old_consensus()

    results = []
    consensus_cfg = config.get("consensus", {})
    old_consensus = old_config.get("consensus", {})
    cp_file = os.path.join(repo_root, "src/chainparams.cpp")

    if not os.path.exists(cp_file):
        return [PatchResult(cp_file, False, "file not found")]

    # Process each network (mainnet, testnet)
    for network in ["mainnet", "testnet"]:
        net_cfg = consensus_cfg.get(network)
        old_net_cfg = old_consensus.get(network)
        if not net_cfg or not old_net_cfg:
            continue

        # Determine which class section to patch
        # mainnet = CMainParams (first occurrence of each param)
        # testnet = CTestNetParams (second occurrence)
        occurrence = 0 if network == "mainnet" else 1

        results.extend(_patch_simple_params(cp_file, net_cfg, old_net_cfg, occurrence))
        results.extend(_patch_deployments(cp_file, net_cfg, old_net_cfg, occurrence))
        results.extend(_patch_llmqs(cp_file, net_cfg, old_net_cfg, occurrence))

    return results


def _patch_simple_params(cp_file: str, net_cfg: dict, old_cfg: dict, occurrence: int) -> List[PatchResult]:
    """Patch simple consensus.nXxx = value lines."""
    results = []

    param_map = {
        "subsidy_halving_interval": ("nSubsidyHalvingInterval", int),
        "pow_target_spacing": ("nPowTargetSpacing", None),
        "pow_target_timespan": ("nPowTargetTimespan", int),
        "masternode_payments_start_block": ("nMasternodePaymentsStartBlock", int),
        "masternode_payments_increase_block": ("nMasternodePaymentsIncreaseBlock", int),
        "masternode_payments_increase_period": ("nMasternodePaymentsIncreasePeriod", int),
        "instant_send_confirmations_required": ("nInstantSendConfirmationsRequired", int),
        "instant_send_keep_lock": ("nInstantSendKeepLock", int),
        "budget_payments_start_block": ("nBudgetPaymentsStartBlock", int),
        "budget_payments_cycle_blocks": ("nBudgetPaymentsCycleBlocks", int),
        "budget_payments_window_blocks": ("nBudgetPaymentsWindowBlocks", int),
        "superblock_start_block": ("nSuperblockStartBlock", int),
        "superblock_cycle": ("nSuperblockCycle", int),
        "superblock_maturity_window": ("nSuperblockMaturityWindow", int),
        "governance_min_quorum": ("nGovernanceMinQuorum", int),
        "governance_filter_elements": ("nGovernanceFilterElements", int),
        "masternode_minimum_confirmations": ("nMasternodeMinimumConfirmations", int),
        "bip34_height": ("BIP34Height", int),
        "bip65_height": ("BIP65Height", int),
        "bip66_height": ("BIP66Height", int),
        "dip0001_height": ("DIP0001Height", int),
        "dip0003_height": ("DIP0003Height", int),
        "dip0003_enforcement_height": ("DIP0003EnforcementHeight", int),
        "dip0008_height": ("DIP0008Height", int),
        "brr_height": ("BRRHeight", int),
        "rule_change_activation_threshold": ("nRuleChangeActivationThreshold", int),
        "miner_confirmation_window": ("nMinerConfirmationWindow", int),
    }

    for cfg_key, (cpp_name, _) in param_map.items():
        if cfg_key not in net_cfg or cfg_key not in old_cfg:
            continue
        old_val = old_cfg[cfg_key]
        new_val = net_cfg[cfg_key]
        if old_val == new_val:
            continue

        # Handle pow_target_spacing which might be float (2.5 * 60)
        if cfg_key == "pow_target_spacing":
            # Try to match both integer and float expressions
            pattern = r'(consensus\.' + cpp_name + r' = )' + re.escape(str(old_val))
            replacement = rf'\g<1>{new_val}'
            r = patch_file_regex(cp_file, pattern, replacement, count=1)
            if not r.changed and isinstance(old_val, float):
                # Try as expression like "2.5 * 60"
                pattern2 = r'(consensus\.' + cpp_name + r' = ).*;'
                replacement2 = rf'\g<1>{new_val};'
                r = patch_file_regex(cp_file, pattern2, replacement2, count=1)
            if r.changed:
                results.append(r)
        else:
            pattern = r'(consensus\.' + cpp_name + r' = )' + re.escape(str(old_val))
            replacement = rf'\g<1>{new_val}'
            r = patch_file_regex(cp_file, pattern, replacement, count=1)
            if r.changed:
                results.append(r)

    # pow_limit is a uint256S string
    if "pow_limit" in net_cfg and "pow_limit" in old_cfg:
        old_pl = old_cfg["pow_limit"]
        new_pl = net_cfg["pow_limit"]
        if old_pl != new_pl:
            r = patch_file_regex(cp_file,
                r'(consensus\.powLimit = uint256S\(")[^"]*("\))',
                rf'\g<1>{new_pl}\g<2>', count=1)
            if r.changed:
                results.append(r)

    return results


def _patch_deployments(cp_file: str, net_cfg: dict, old_cfg: dict, occurrence: int) -> List[PatchResult]:
    """Patch BIP9 deployment parameters."""
    results = []

    new_deps = net_cfg.get("deployments", {})
    old_deps = old_cfg.get("deployments", {})

    for dep_name, dep_enum in DEPLOYMENT_MAP.items():
        new_dep = new_deps.get(dep_name)
        old_dep = old_deps.get(dep_name)
        if not new_dep or not old_dep:
            continue

        prefix = f'consensus.vDeployments[Consensus::{dep_enum}]'

        # bit
        if new_dep.get("bit") != old_dep.get("bit") and "bit" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.bit = )\d+',
                rf'\g<1>{new_dep["bit"]}', count=1)
            if r.changed:
                results.append(r)

        # start_time
        if new_dep.get("start_time") != old_dep.get("start_time") and "start_time" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nStartTime = )\d+',
                rf'\g<1>{new_dep["start_time"]}', count=1)
            if r.changed:
                results.append(r)

        # timeout
        if new_dep.get("timeout") != old_dep.get("timeout") and "timeout" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nTimeout = )\d+',
                rf'\g<1>{new_dep["timeout"]}', count=1)
            if r.changed:
                results.append(r)

        # window_size
        if new_dep.get("window_size") != old_dep.get("window_size") and "window_size" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nWindowSize = )\d+',
                rf'\g<1>{new_dep["window_size"]}', count=1)
            if r.changed:
                results.append(r)

        # threshold_start
        if new_dep.get("threshold_start") != old_dep.get("threshold_start") and "threshold_start" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nThresholdStart = )\d+',
                rf'\g<1>{new_dep["threshold_start"]}', count=1)
            if r.changed:
                results.append(r)

        # threshold_min
        if new_dep.get("threshold_min") != old_dep.get("threshold_min") and "threshold_min" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nThresholdMin = )\d+',
                rf'\g<1>{new_dep["threshold_min"]}', count=1)
            if r.changed:
                results.append(r)

        # falloff_coeff
        if new_dep.get("falloff_coeff") != old_dep.get("falloff_coeff") and "falloff_coeff" in new_dep:
            r = patch_file_regex(cp_file,
                r'(' + re.escape(prefix) + r'\.nFalloffCoeff = )\d+',
                rf'\g<1>{new_dep["falloff_coeff"]}', count=1)
            if r.changed:
                results.append(r)

    return results


def _patch_llmqs(cp_file: str, net_cfg: dict, old_cfg: dict, occurrence: int) -> List[PatchResult]:
    """Patch LLMQ quorum type assignments."""
    results = []

    llmq_assignments = {
        "llmq_chainlocks": "llmqTypeChainLocks",
        "llmq_instant_send": "llmqTypeInstantSend",
        "llmq_dip0024_instant_send": "llmqTypeDIP0024InstantSend",
        "llmq_mnhf": "llmqTypeMnhf",
    }

    for cfg_key, cpp_name in llmq_assignments.items():
        old_val = old_cfg.get(cfg_key)
        new_val = net_cfg.get(cfg_key)
        if not old_val or not new_val or old_val == new_val:
            continue

        old_enum = LLMQ_MAP.get(old_val, f"Consensus::LLMQType::{old_val}")
        new_enum = LLMQ_MAP.get(new_val, f"Consensus::LLMQType::{new_val}")

        r = patch_file_regex(cp_file,
            r'(consensus\.' + cpp_name + r' = )' + re.escape(old_enum),
            rf'\g<1>{new_enum}', count=1)
        if r.changed:
            results.append(r)

    return results


def _default_old_consensus() -> dict:
    """Default Dashbase consensus values."""
    return {
        "consensus": {
            "mainnet": {
                "subsidy_halving_interval": 210000,
                "pow_target_spacing": 120,
                "pow_target_timespan": 86400,
                "pow_limit": "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "masternode_payments_start_block": 0,
                "masternode_payments_increase_block": 0,
                "masternode_payments_increase_period": 1,
                "instant_send_confirmations_required": 6,
                "instant_send_keep_lock": 24,
                "budget_payments_start_block": 0,
                "budget_payments_cycle_blocks": 10080,
                "budget_payments_window_blocks": 100,
                "superblock_start_block": 10080,
                "superblock_cycle": 10080,
                "superblock_maturity_window": 1440,
                "governance_min_quorum": 10,
                "governance_filter_elements": 20000,
                "masternode_minimum_confirmations": 15,
                "bip34_height": 1,
                "bip65_height": 1,
                "bip66_height": 1,
                "dip0001_height": 1,
                "dip0003_height": 1,
                "dip0003_enforcement_height": 1,
                "dip0008_height": 1,
                "brr_height": 1,
                "rule_change_activation_threshold": 1512,
                "miner_confirmation_window": 720,
                "deployments": {
                    "TESTDUMMY": {"bit": 28, "start_time": 0, "timeout": 999999999999},
                    "CSV": {"bit": 0, "start_time": 0, "timeout": 999999999999},
                    "DIP0001": {"bit": 1, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
                    "BIP147": {"bit": 2, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
                    "DIP0003": {"bit": 3, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
                    "DIP0008": {"bit": 4, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226},
                    "REALLOC": {"bit": 5, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
                    "DIP0020": {"bit": 6, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
                    "DIP0024": {"bit": 7, "start_time": 0, "timeout": 999999999999, "window_size": 4032, "threshold_start": 3226, "threshold_min": 2420, "falloff_coeff": 5},
                },
                "llmq_chainlocks": "LLMQ_400_60",
                "llmq_instant_send": "LLMQ_50_60",
                "llmq_dip0024_instant_send": "LLMQ_60_75",
                "llmq_mnhf": "LLMQ_400_85",
            },
            "testnet": {
                "subsidy_halving_interval": 210000,
                "pow_target_spacing": 120,
                "pow_target_timespan": 86400,
                "pow_limit": "00000fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "masternode_payments_start_block": 0,
                "masternode_payments_increase_block": 0,
                "masternode_payments_increase_period": 10,
                "instant_send_confirmations_required": 2,
                "instant_send_keep_lock": 6,
                "budget_payments_start_block": 0,
                "budget_payments_cycle_blocks": 50,
                "budget_payments_window_blocks": 10,
                "superblock_start_block": 50,
                "superblock_cycle": 50,
                "superblock_maturity_window": 50,
                "governance_min_quorum": 1,
                "governance_filter_elements": 500,
                "masternode_minimum_confirmations": 1,
                "bip34_height": 1,
                "bip65_height": 1,
                "bip66_height": 1,
                "dip0001_height": 1,
                "dip0003_height": 1,
                "dip0003_enforcement_height": 1,
                "dip0008_height": 1,
                "brr_height": 1,
                "rule_change_activation_threshold": 1512,
                "miner_confirmation_window": 720,
                "deployments": {
                    "TESTDUMMY": {"bit": 28, "start_time": 1199145601, "timeout": 1230767999},
                    "CSV": {"bit": 0, "start_time": 0, "timeout": 999999999999},
                    "DIP0001": {"bit": 1, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
                    "BIP147": {"bit": 2, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
                    "DIP0003": {"bit": 3, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
                    "DIP0008": {"bit": 4, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 50},
                    "REALLOC": {"bit": 5, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
                    "DIP0020": {"bit": 6, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
                    "DIP0024": {"bit": 7, "start_time": 0, "timeout": 999999999999, "window_size": 100, "threshold_start": 80, "threshold_min": 60, "falloff_coeff": 5},
                },
                "llmq_chainlocks": "LLMQ_50_60",
                "llmq_instant_send": "LLMQ_50_60",
                "llmq_dip0024_instant_send": "LLMQ_60_75",
                "llmq_mnhf": "LLMQ_50_60",
            },
        }
    }
