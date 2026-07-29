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

interface WalletState {
  connected: boolean;
  loading: boolean;
  error: string | null;
  balance: WalletBalance | null;
  blockchainInfo: BlockchainInfo | null;
  transactions: Transaction[];
  addresses: AddressBookEntry[];
  peers: PeerInfo[];

  refresh: () => Promise<void>;
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
}

export const useWalletStore = create<WalletState>((set) => ({
  connected: false,
  loading: false,
  error: null,
  balance: null,
  blockchainInfo: null,
  transactions: [],
  addresses: [],
  peers: [],

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
}));
