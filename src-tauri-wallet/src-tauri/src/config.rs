use std::sync::LazyLock;
use tokio::sync::RwLock;
use std::sync::Arc;

pub struct Config {
    pub rpc_host: String,
    pub rpc_port: u16,
    pub rpc_user: String,
    pub rpc_password: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            rpc_host: "127.0.0.1".to_string(),
            rpc_port: 9988,
            rpc_user: "dashbase".to_string(),
            rpc_password: "dashbase".to_string(),
        }
    }
}

static CONFIG: LazyLock<Arc<RwLock<Option<Config>>>> = LazyLock::new(|| Arc::new(RwLock::new(None)));

pub async fn init_config() {
    let mut config = Config::default();

    // Try reading from dashbase.conf
    if let Some(conf_path) = find_conf_file() {
        if let Ok(content) = std::fs::read_to_string(&conf_path) {
            for line in content.lines() {
                let line = line.trim();
                if line.is_empty() || line.starts_with('#') {
                    continue;
                }
                if let Some((key, value)) = line.split_once('=') {
                    let key = key.trim();
                    let value = value.trim();
                    match key {
                        "rpcuser" => config.rpc_user = value.to_string(),
                        "rpcpassword" => config.rpc_password = value.to_string(),
                        "rpcport" => {
                            if let Ok(port) = value.parse::<u16>() {
                                config.rpc_port = port;
                            }
                        }
                        "rpcbind" | "rpcconnect" => {
                            config.rpc_host = value.to_string();
                        }
                        _ => {}
                    }
                }
            }
        }
    }

    // Override with env vars if present
    if let Ok(user) = std::env::var("DASHBASE_RPC_USER") {
        config.rpc_user = user;
    }
    if let Ok(pass) = std::env::var("DASHBASE_RPC_PASSWORD") {
        config.rpc_password = pass;
    }
    if let Ok(host) = std::env::var("DASHBASE_RPC_HOST") {
        config.rpc_host = host;
    }
    if let Ok(port) = std::env::var("DASHBASE_RPC_PORT") {
        if let Ok(p) = port.parse::<u16>() {
            config.rpc_port = p;
        }
    }

    let mut guard = CONFIG.write().await;
    *guard = Some(config);
}

pub fn get_config() -> Config {
    let guard = CONFIG.blocking_read();
    guard
        .as_ref()
        .cloned()
        .unwrap_or_default()
}

impl Clone for Config {
    fn clone(&self) -> Self {
        Self {
            rpc_host: self.rpc_host.clone(),
            rpc_port: self.rpc_port,
            rpc_user: self.rpc_user.clone(),
            rpc_password: self.rpc_password.clone(),
        }
    }
}

fn find_conf_file() -> Option<std::path::PathBuf> {
    if let Ok(path) = std::env::var("DASHBASE_CONF") {
        let p = std::path::PathBuf::from(path);
        if p.exists() {
            return Some(p);
        }
    }

    let home = dirs::home_dir()?;
    let candidates = [
        home.join(".dashbase").join("dashbase.conf"),
        home.join(".dashbase").join("dash.conf"),
        home.join("Library").join("Application Support").join("Dashbase").join("dashbase.conf"),
        home.join("AppData").join("Roaming").join("Dashbase").join("dashbase.conf"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            return Some(candidate.clone());
        }
    }
    None
}
