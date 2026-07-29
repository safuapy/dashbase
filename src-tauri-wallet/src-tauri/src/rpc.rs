use serde::Deserialize;

#[derive(Clone)]
pub struct RpcClient {
    url: String,
    auth_header: String,
}

#[derive(Debug, thiserror::Error)]
pub enum RpcError {
    #[error("RPC error: {0}")]
    Rpc(String),
    #[error("HTTP error: {0}")]
    Http(String),
    #[error("Parse error: {0}")]
    Parse(String),
}

impl RpcClient {
    pub fn new(host: &str, port: u16, user: &str, password: &str) -> Self {
        let url = format!("http://{}:{}", host, port);
        let credentials = base64::Engine::encode(
            &base64::engine::general_purpose::STANDARD,
            format!("{}:{}", user, password),
        );
        Self {
            url,
            auth_header: format!("Basic {}", credentials),
        }
    }

    pub async fn call<T: for<'de> Deserialize<'de>>(
        &self,
        method: &str,
        params: &[serde_json::Value],
    ) -> Result<T, RpcError> {
        let id: u64 = rand::random();
        let body = serde_json::json!({
            "jsonrpc": "1.0",
            "id": id,
            "method": method,
            "params": params,
        });

        let client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .map_err(|e| RpcError::Http(e.to_string()))?;

        let resp = client
            .post(&self.url)
            .header("Authorization", &self.auth_header)
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .map_err(|e| RpcError::Http(e.to_string()))?;

        let text = resp
            .text()
            .await
            .map_err(|e| RpcError::Http(e.to_string()))?;

        let json: serde_json::Value =
            serde_json::from_str(&text).map_err(|e| RpcError::Parse(e.to_string()))?;

        if let Some(error) = json.get("error") {
            if !error.is_null() {
                let msg = error
                    .get("message")
                    .and_then(|m| m.as_str())
                    .unwrap_or("Unknown RPC error");
                return Err(RpcError::Rpc(msg.to_string()));
            }
        }

        let result = json
            .get("result")
            .ok_or_else(|| RpcError::Parse("Missing result field".to_string()))?;

        serde_json::from_value(result.clone()).map_err(|e| RpcError::Parse(e.to_string()))
    }
}

pub async fn get_client() -> Result<RpcClient, String> {
    let config = crate::config::get_config();
    Ok(RpcClient::new(
        &config.rpc_host,
        config.rpc_port,
        &config.rpc_user,
        &config.rpc_password,
    ))
}
