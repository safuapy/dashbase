use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use rand::Rng;

static DAEMON_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

pub fn data_dir() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    if cfg!(target_os = "macos") {
        home.join("Library").join("Application Support").join("Dashbase")
    } else if cfg!(target_os = "windows") {
        home.join("AppData").join("Roaming").join("Dashbase")
    } else {
        home.join(".dashbase")
    }
}

fn find_bundled_daemon(resource_dir: Option<PathBuf>) -> Option<PathBuf> {
    let candidates: Vec<Option<PathBuf>> = vec![
        // Tauri resource_dir/resources/dashbased (Tauri preserves folder structure)
        resource_dir.as_ref().map(|rd| rd.join("resources").join("dashbased")),
        resource_dir.as_ref().map(|rd| rd.join("resources").join("dashbased.exe")),
        // macOS .app bundle: Contents/Resources/resources/dashbased
        std::env::current_exe().ok()
            .and_then(|p| p.parent().and_then(|d| d.parent())
                .map(|d| d.join("Resources").join("resources").join("dashbased"))),
        // macOS .app bundle: Contents/Resources/dashbased (fallback)
        std::env::current_exe().ok()
            .and_then(|p| p.parent().and_then(|d| d.parent())
                .map(|d| d.join("Resources").join("dashbased"))),
        // macOS Frameworks dir
        std::env::current_exe().ok()
            .and_then(|p| p.parent().and_then(|d| d.parent())
                .map(|d| d.join("Frameworks").join("dashbased"))),
        // Next to the executable
        std::env::current_exe().ok()
            .and_then(|p| p.parent().map(|d| d.join("dashbased"))),
        // Windows: same dir as exe
        std::env::current_exe().ok()
            .and_then(|p| p.parent().map(|d| d.join("dashbased.exe"))),
        // System PATH
        which::which("dashbased").ok(),
    ];

    for candidate in candidates.iter().flatten() {
        if candidate.exists() {
            return Some(candidate.clone());
        }
    }
    None
}

fn generate_random_password() -> String {
    let chars: Vec<char> = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        .chars()
        .collect();
    (0..32)
        .map(|_| chars[rand::thread_rng().gen_range(0..chars.len())])
        .collect()
}

fn ensure_conf() -> (String, String, u16) {
    let dd = data_dir();
    std::fs::create_dir_all(&dd).ok();

    let conf_path = dd.join("dashbase.conf");
    let rpc_user = "dashbase".to_string();
    let rpc_password = generate_random_password();
    let rpc_port: u16 = if cfg!(feature = "testnet") { 19998 } else { 9998 };

    let conf_content = format!(
        r#"rpcuser={}
rpcpassword={}
rpcport={}
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
server=1
daemon=0
txindex=1
listen=1
shrinkdebuglog=1
"#,
        rpc_user, rpc_password, rpc_port
    );

    // Only write if doesn't exist or is missing rpc credentials
    let needs_write = match std::fs::read_to_string(&conf_path) {
        Ok(content) => !content.contains("rpcuser=") || !content.contains("rpcpassword="),
        Err(_) => true,
    };

    if needs_write {
        std::fs::write(&conf_path, &conf_content).ok();
    }

    // Read back actual values
    let content = std::fs::read_to_string(&conf_path).unwrap_or_default();
    let mut user = rpc_user.clone();
    let mut pass = rpc_password.clone();
    let mut port = rpc_port;

    for line in content.lines() {
        let line = line.trim();
        if let Some((key, value)) = line.split_once('=') {
            match key.trim() {
                "rpcuser" => user = value.trim().to_string(),
                "rpcpassword" => pass = value.trim().to_string(),
                "rpcport" => {
                    if let Ok(p) = value.trim().parse::<u16>() {
                        port = p;
                    }
                }
                _ => {}
            }
        }
    }

    (user, pass, port)
}

pub fn start_daemon(resource_dir: Option<PathBuf>) -> Result<String, String> {
    // Check if daemon is already running (by trying to connect)
    // If we already have a child process, don't start another
    {
        let guard = DAEMON_PROCESS.lock().unwrap();
        if guard.is_some() {
            return Ok("Daemon already managed by wallet".to_string());
        }
    }

    let daemon_path = find_bundled_daemon(resource_dir)
        .ok_or_else(|| "dashbased binary not found. Place it in the app's Resources directory or install it in PATH.".to_string())?;

    let dd = data_dir();
    std::fs::create_dir_all(&dd).map_err(|e| format!("Failed to create data dir: {}", e))?;

    let conf_path = dd.join("dashbase.conf");
    if !conf_path.exists() {
        let (user, pass, port) = ensure_conf();
        // Write config
        let conf = format!(
            r#"rpcuser={}
rpcpassword={}
rpcport={}
rpcbind=127.0.0.1
rpcallowip=127.0.0.1
server=1
daemon=0
txindex=1
listen=1
shrinkdebuglog=1
"#,
            user, pass, port
        );
        std::fs::write(&conf_path, &conf).map_err(|e| format!("Failed to write config: {}", e))?;
    }

    let child = Command::new(&daemon_path)
        .arg(format!("-datadir={}", dd.display()))
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start daemon: {}", e))?;

    let pid = child.id();
    {
        let mut guard = DAEMON_PROCESS.lock().unwrap();
        *guard = Some(child);
    }

    Ok(format!("Daemon started (PID: {})", pid))
}

pub fn stop_daemon() -> Result<String, String> {
    let mut guard = DAEMON_PROCESS.lock().unwrap();
    if let Some(mut child) = guard.take() {
        child.kill().map_err(|e| format!("Failed to stop daemon: {}", e))?;
        Ok("Daemon stopped".to_string())
    } else {
        // Try sending stop via RPC
        Err("No managed daemon process".to_string())
    }
}

pub fn daemon_status() -> String {
    let mut guard = DAEMON_PROCESS.lock().unwrap();
    if let Some(child) = guard.as_mut() {
        match child.try_wait() {
            Ok(Some(status)) => format!("Daemon exited: {}", status),
            Ok(None) => "Daemon running".to_string(),
            Err(e) => format!("Daemon status error: {}", e),
        }
    } else {
        "No managed daemon".to_string()
    }
}
