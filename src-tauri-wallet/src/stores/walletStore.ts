import { create } from "zustand";
import { invoke } from "@tauri-apps/api/core";

export interface WalletBalance {
  balance: number;
  unconfirmed_balance: number;
  immature_balance: number;
  anonymized_balance: number;
}

export interface Transaction {
  txid: string;
  amount: number;
  fee: number;
  confirmations: number;
  blockhash: string;
  blockheight: number;
  blocktime: number;
  time: number;
  timereceived: number;
  category: string;
  address: string;
  label: string;
  comment: string;
  abandoned: boolean;
}

export interface AddressBookEntry {
  address: string;
  label: string;
  purpose: string;
}

export interface PeerInfo {
  id: number;
  addr: string;
  version: number;
  subver: string;
  inbound: boolean;
  startingheight: number;
  banscore: number;
}

export interface BlockchainInfo {
  chain: string;
  blocks: number;
  headers: number;
  bestblockhash: string;
  difficulty: number;
  verificationprogress: number;
  chainwork: string;
  size_on_disk: number;
  pruned: boolean;
  initialblockdownload: boolean;
  chainlocks: boolean;
}

export interface MasternodeInfo {
  alias: string;
  status: string;
  addr: string;
  version: number;
  lastseen: number;
  activetime: number;
  lastpaid: number;
  ip: string;
  protocol: number;
  payee: string;
}

export interface GovernanceProposal {
  name: string;
  hash: string;
  fee_hash: string;
  absolute_yes_count: number;
  yes_count: number;
  no_count: number;
  abstain_count: number;
  funding_yes_count: number;
  funding_no_count: number;
  delete_yes_count: number;
  delete_no_count: number;
  cached_funding_state: boolean;
  cached_delete_state: boolean;
  cached_endored_state: boolean;
  creation_time: number;
  end_epoch_time: number;
  payment_address: string;
  payment_amount: number;
  url: string;
  is_valid: boolean;
  is_active: boolean;
}

interface WalletState {
  connected: boolean;
  loading: boolean;
  error: string | null;
  daemonStatus: string;
  dataDir: string;
  balance: WalletBalance | null;
  blockchainInfo: BlockchainInfo | null;
  transactions: Transaction[];
  addresses: AddressBookEntry[];
  peers: PeerInfo[];
  masternodes: MasternodeInfo[];
  proposals: GovernanceProposal[];

  refresh: () => Promise<void>;
  refreshMasternodes: () => Promise<void>;
  refreshProposals: () => Promise<void>;
  startDaemon: () => Promise<void>;
  stopDaemon: () => Promise<void>;
  checkDaemon: () => Promise<void>;
  sendToAddress: (
    address: string,
    amount: number,
    subtractFee: boolean,
    useCoinJoin: boolean
  ) => Promise<string>;
  getNewAddress: (label: string) => Promise<string>;
  validateAddress: (address: string) => Promise<{ isvalid: boolean }>;
  encryptWallet: (passphrase: string) => Promise<void>;
  unlockWallet: (passphrase: string) => Promise<void>;
  lockWallet: () => Promise<void>;
  walletPassphraseChange: (oldPass: string, newPass: string) => Promise<void>;
  backupWallet: (dest: string) => Promise<void>;
  masternodeStatus: () => Promise<unknown>;
  masternodeStartAlias: (alias: string) => Promise<string>;
  masternodeStartAll: () => Promise<string>;
  masternodeStartMissing: () => Promise<string>;
  masternodeOutputs: () => Promise<unknown>;
  masternodeCreate: (collateralTx: string, collateralIndex: number, ip: string, payee: string) => Promise<string>;
  voteOnProposal: (proposalHash: string, vote: string, signal: string) => Promise<string>;
  getProposalInfo: (proposalHash: string) => Promise<unknown>;
  rpcCommand: (method: string, params: string[]) => Promise<unknown>;
  getRawMempool: () => Promise<unknown>;
  getMiningInfo: () => Promise<unknown>;
  getNetworkInfo: () => Promise<unknown>;
  getWalletInfo: () => Promise<unknown>;
}

export const useWalletStore = create<WalletState>((set) => ({
  connected: false,
  loading: false,
  error: null,
  daemonStatus: "unknown",
  dataDir: "",
  balance: null,
  blockchainInfo: null,
  transactions: [],
  addresses: [],
  peers: [],
  masternodes: [],
  proposals: [],

  refresh: async () => {
    set({ loading: true, error: null });
    try {
      const [balance, blockchainInfo, transactions, addresses, peers] =
        await Promise.all([
          invoke<WalletBalance>("get_balance"),
          invoke<BlockchainInfo>("get_blockchain_info"),
          invoke<Transaction[]>("list_transactions").catch(() => []),
          invoke<AddressBookEntry[]>("list_addresses").catch(() => []),
          invoke<PeerInfo[]>("get_peers").catch(() => []),
        ]);

      set({
        connected: true,
        loading: false,
        balance,
        blockchainInfo,
        transactions,
        addresses,
        peers,
      });
    } catch (err) {
      console.error("[walletStore] refresh failed:", err);
      set({
        connected: false,
        loading: false,
        error: String(err),
      });
    }
  },

  sendToAddress: async (address, amount, subtractFee, useCoinJoin) => {
    return invoke<string>("send_to_address", {
      address,
      amount,
      subtractFee,
      useCoinJoin,
    });
  },

  getNewAddress: async (label) => {
    return invoke<string>("get_new_address", { label });
  },

  validateAddress: async (address) => {
    return invoke<{ isvalid: boolean }>("validate_address", { address });
  },

  encryptWallet: async (passphrase) => {
    await invoke("encrypt_wallet", { passphrase });
  },

  unlockWallet: async (passphrase) => {
    await invoke("unlock_wallet", { passphrase });
  },

  lockWallet: async () => {
    await invoke("lock_wallet");
  },

  walletPassphraseChange: async (oldPass, newPass) => {
    await invoke("change_passphrase", { oldPass, newPass });
  },

  backupWallet: async (dest) => {
    await invoke("backup_wallet", { dest });
  },

  startDaemon: async () => {
    try {
      await invoke("start_daemon");
      set({ daemonStatus: "starting" });
    } catch (err) {
      console.error("[walletStore] startDaemon failed:", err);
    }
  },

  stopDaemon: async () => {
    try {
      await invoke("stop_daemon");
      set({ daemonStatus: "stopped", connected: false });
    } catch (err) {
      console.error("[walletStore] stopDaemon failed:", err);
    }
  },

  checkDaemon: async () => {
    try {
      const status = await invoke<string>("daemon_status");
      const dataDir = await invoke<string>("get_data_dir");
      set({ daemonStatus: status, dataDir });
    } catch (err) {
      console.error("[walletStore] checkDaemon failed:", err);
    }
  },

  refreshMasternodes: async () => {
    try {
      const masternodes = await invoke<MasternodeInfo[]>("list_masternodes").catch(() => []);
      set({ masternodes });
    } catch (err) {
      console.error("[walletStore] refreshMasternodes failed:", err);
    }
  },

  refreshProposals: async () => {
    try {
      const proposals = await invoke<GovernanceProposal[]>("list_proposals").catch(() => []);
      set({ proposals });
    } catch (err) {
      console.error("[walletStore] refreshProposals failed:", err);
    }
  },

  masternodeStatus: async () => {
    return invoke("masternode_status");
  },

  masternodeStartAlias: async (alias) => {
    return invoke<string>("masternode_start_alias", { alias });
  },

  masternodeStartAll: async () => {
    return invoke<string>("masternode_start_all");
  },

  masternodeStartMissing: async () => {
    return invoke<string>("masternode_start_missing");
  },

  masternodeOutputs: async () => {
    return invoke("masternode_outputs");
  },

  masternodeCreate: async (collateralTx, collateralIndex, ip, payee) => {
    return invoke<string>("masternode_create", {
      collateralTx,
      collateralIndex,
      ip,
      payee,
    });
  },

  voteOnProposal: async (proposalHash, vote, signal) => {
    return invoke<string>("vote_on_proposal", { proposalHash, vote, signal });
  },

  getProposalInfo: async (proposalHash) => {
    return invoke("get_proposal_info", { proposalHash });
  },

  rpcCommand: async (method, params) => {
    return invoke("rpc_command", { method, params });
  },

  getRawMempool: async () => {
    return invoke("get_raw_mempool");
  },

  getMiningInfo: async () => {
    return invoke("get_mining_info");
  },

  getNetworkInfo: async () => {
    return invoke("get_network_info");
  },

  getWalletInfo: async () => {
    return invoke("get_wallet_info");
  },
}));
