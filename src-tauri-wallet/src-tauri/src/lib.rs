mod config;
mod rpc;

use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct WalletBalance {
    pub balance: f64,
    pub unconfirmed_balance: f64,
    pub immature_balance: f64,
    pub anonymized_balance: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct Transaction {
    pub txid: String,
    pub amount: f64,
    pub fee: f64,
    pub confirmations: i64,
    pub blockhash: String,
    pub blockheight: i64,
    pub blocktime: i64,
    pub time: i64,
    pub timereceived: i64,
    pub category: String,
    pub address: String,
    pub label: String,
    pub comment: String,
    pub abandoned: bool,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AddressBookEntry {
    pub address: String,
    pub label: String,
    pub purpose: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PeerInfo {
    pub id: i64,
    pub addr: String,
    pub version: i64,
    pub subver: String,
    pub inbound: bool,
    pub startingheight: i64,
    pub banscore: i64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct BlockchainInfo {
    pub chain: String,
    pub blocks: i64,
    pub headers: i64,
    pub bestblockhash: String,
    pub difficulty: f64,
    pub verificationprogress: f64,
    pub chainwork: String,
    pub size_on_disk: i64,
    pub pruned: bool,
    pub initialblockdownload: bool,
    pub chainlocks: bool,
}

#[tauri::command]
async fn get_balance() -> Result<WalletBalance, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;

    let balance: f64 = client
        .call("getbalance", &[])
        .await
        .map_err(|e| e.to_string())?;

    let unconfirmed: f64 = client
        .call("getunconfirmedbalance", &[])
        .await
        .map_err(|e| e.to_string())?;

    let immature: f64 = client
        .call("getbalance", &["".into(), 0.into(), true.into()])
        .await
        .map_err(|e| e.to_string())?;

    let info: serde_json::Value = client
        .call("getwalletinfo", &[])
        .await
        .map_err(|e| e.to_string())?;
    let anonymized = info
        .get("anonymized_balance")
        .and_then(|v| v.as_f64())
        .unwrap_or(0.0);

    Ok(WalletBalance {
        balance,
        unconfirmed_balance: unconfirmed,
        immature_balance: immature,
        anonymized_balance: anonymized,
    })
}

#[tauri::command]
async fn get_blockchain_info() -> Result<BlockchainInfo, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let info: serde_json::Value = client
        .call("getblockchaininfo", &[])
        .await
        .map_err(|e| e.to_string())?;

    Ok(BlockchainInfo {
        chain: info.get("chain").and_then(|v| v.as_str()).unwrap_or("").to_string(),
        blocks: info.get("blocks").and_then(|v| v.as_i64()).unwrap_or(0),
        headers: info.get("headers").and_then(|v| v.as_i64()).unwrap_or(0),
        bestblockhash: info.get("bestblockhash").and_then(|v| v.as_str()).unwrap_or("").to_string(),
        difficulty: info.get("difficulty").and_then(|v| v.as_f64()).unwrap_or(0.0),
        verificationprogress: info.get("verificationprogress").and_then(|v| v.as_f64()).unwrap_or(0.0),
        chainwork: info.get("chainwork").and_then(|v| v.as_str()).unwrap_or("").to_string(),
        size_on_disk: info.get("size_on_disk").and_then(|v| v.as_i64()).unwrap_or(0),
        pruned: info.get("pruned").and_then(|v| v.as_bool()).unwrap_or(false),
        initialblockdownload: info.get("initialblockdownload").and_then(|v| v.as_bool()).unwrap_or(false),
        chainlocks: info.get("chainlocks").and_then(|v| v.as_bool()).unwrap_or(false),
    })
}

#[tauri::command]
async fn list_transactions() -> Result<Vec<Transaction>, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let txs: Vec<serde_json::Value> = client
        .call("listtransactions", &["".into(), 100.into(), 0.into(), true.into()])
        .await
        .map_err(|e| e.to_string())?;

    let result = txs
        .into_iter()
        .map(|tx| Transaction {
            txid: tx.get("txid").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            amount: tx.get("amount").and_then(|v| v.as_f64()).unwrap_or(0.0),
            fee: tx.get("fee").and_then(|v| v.as_f64()).unwrap_or(0.0),
            confirmations: tx.get("confirmations").and_then(|v| v.as_i64()).unwrap_or(0),
            blockhash: tx.get("blockhash").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            blockheight: tx.get("blockheight").and_then(|v| v.as_i64()).unwrap_or(0),
            blocktime: tx.get("blocktime").and_then(|v| v.as_i64()).unwrap_or(0),
            time: tx.get("time").and_then(|v| v.as_i64()).unwrap_or(0),
            timereceived: tx.get("timereceived").and_then(|v| v.as_i64()).unwrap_or(0),
            category: tx.get("category").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            address: tx.get("address").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            label: tx.get("label").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            comment: tx.get("comment").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            abandoned: tx.get("abandoned").and_then(|v| v.as_bool()).unwrap_or(false),
        })
        .collect();
    Ok(result)
}

#[tauri::command]
async fn list_addresses() -> Result<Vec<AddressBookEntry>, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let groups: Vec<serde_json::Value> = client
        .call("listaddressgroupings", &[])
        .await
        .map_err(|e| e.to_string())?;

    let mut entries = Vec::new();
    for group in groups {
        if let Some(arr) = group.as_array() {
            for addr_entry in arr {
                if let Some(inner) = addr_entry.as_array() {
                    let address = inner.first().and_then(|v| v.as_str()).unwrap_or("").to_string();
                    let label = inner.get(2).and_then(|v| v.as_str()).unwrap_or("").to_string();
                    entries.push(AddressBookEntry {
                        address,
                        label,
                        purpose: "receive".to_string(),
                    });
                }
            }
        }
    }
    Ok(entries)
}

#[tauri::command]
async fn get_peers() -> Result<Vec<PeerInfo>, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let peers: Vec<serde_json::Value> = client
        .call("getpeerinfo", &[])
        .await
        .map_err(|e| e.to_string())?;

    let result = peers
        .into_iter()
        .map(|p| PeerInfo {
            id: p.get("id").and_then(|v| v.as_i64()).unwrap_or(0),
            addr: p.get("addr").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            version: p.get("version").and_then(|v| v.as_i64()).unwrap_or(0),
            subver: p.get("subver").and_then(|v| v.as_str()).unwrap_or("").to_string(),
            inbound: p.get("inbound").and_then(|v| v.as_bool()).unwrap_or(false),
            startingheight: p.get("startingheight").and_then(|v| v.as_i64()).unwrap_or(0),
            banscore: p.get("banscore").and_then(|v| v.as_i64()).unwrap_or(0),
        })
        .collect();
    Ok(result)
}

#[tauri::command]
async fn send_to_address(
    address: String,
    amount: f64,
    subtract_fee: bool,
    use_coinjoin: bool,
) -> Result<String, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let txid: String = client
        .call(
            "sendtoaddress",
            &[
                address.into(),
                amount.into(),
                "".into(),
                "".into(),
                subtract_fee.into(),
                false.into(),
                use_coinjoin.into(),
            ],
        )
        .await
        .map_err(|e| e.to_string())?;
    Ok(txid)
}

#[tauri::command]
async fn get_new_address(label: String) -> Result<String, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let addr: String = client
        .call("getnewaddress", &[label.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(addr)
}

#[tauri::command]
async fn validate_address(address: String) -> Result<serde_json::Value, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let result: serde_json::Value = client
        .call("validateaddress", &[address.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(result)
}

#[tauri::command]
async fn encrypt_wallet(passphrase: String) -> Result<String, String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let result: String = client
        .call("encryptwallet", &[passphrase.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(result)
}

#[tauri::command]
async fn unlock_wallet(passphrase: String) -> Result<(), String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let _: serde_json::Value = client
        .call("walletpassphrase", &[passphrase.into(), 60.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn lock_wallet() -> Result<(), String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let _: serde_json::Value = client
        .call("walletlock", &[])
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn change_passphrase(old_pass: String, new_pass: String) -> Result<(), String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let _: serde_json::Value = client
        .call("walletpassphrasechange", &[old_pass.into(), new_pass.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
async fn backup_wallet(dest: String) -> Result<(), String> {
    let client = rpc::get_client().await.map_err(|e| e.to_string())?;
    let _: serde_json::Value = client
        .call("backupwallet", &[dest.into()])
        .await
        .map_err(|e| e.to_string())?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .setup(|_app| {
            tauri::async_runtime::block_on(async {
                config::init_config().await;
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            get_balance,
            get_blockchain_info,
            list_transactions,
            list_addresses,
            get_peers,
            send_to_address,
            get_new_address,
            validate_address,
            encrypt_wallet,
            unlock_wallet,
            lock_wallet,
            change_passphrase,
            backup_wallet,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
