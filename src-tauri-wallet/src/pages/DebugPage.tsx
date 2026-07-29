import { useState, useRef, useEffect } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Terminal, Send, Trash2, ChevronDown, Activity, Database, Network, Wallet, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConsoleEntry {
  id: number;
  method: string;
  params: string;
  result?: unknown;
  error?: string;
  timestamp: number;
  loading: boolean;
}

const QUICK_COMMANDS = [
  { method: "getblockchaininfo", label: "Blockchain Info", icon: Database },
  { method: "getnetworkinfo", label: "Network Info", icon: Network },
  { method: "getwalletinfo", label: "Wallet Info", icon: Wallet },
  { method: "getmininginfo", label: "Mining Info", icon: Activity },
  { method: "getrawmempool", label: "Mempool", icon: Zap },
  { method: "getpeerinfo", label: "Peers", icon: Network },
];

export default function DebugPage() {
  const { connected, rpcCommand, getNetworkInfo, getMiningInfo, getWalletInfo, getRawMempool } = useWalletStore();
  const [method, setMethod] = useState("");
  const [params, setParams] = useState("");
  const [history, setHistory] = useState<ConsoleEntry[]>([]);
  const [expanded, setExpanded] = useState<number | null>(null);
  const idCounter = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history]);

  const executeCommand = async (cmdMethod: string, cmdParams?: string) => {
    const id = ++idCounter.current;
    const parsedParams: string[] = cmdParams
      ? cmdParams.split(",").map((p) => p.trim()).filter(Boolean)
      : [];

    const entry: ConsoleEntry = {
      id,
      method: cmdMethod,
      params: cmdParams || "",
      timestamp: Date.now(),
      loading: true,
    };
    setHistory((prev) => [...prev, entry]);

    try {
      const result = await rpcCommand(cmdMethod, parsedParams);
      setHistory((prev) =>
        prev.map((e) => (e.id === id ? { ...e, result, loading: false } : e))
      );
    } catch (err) {
      setHistory((prev) =>
        prev.map((e) => (e.id === id ? { ...e, error: String(err), loading: false } : e))
      );
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!method.trim()) return;
    executeCommand(method.trim(), params.trim());
    setMethod("");
    setParams("");
  };

  const handleQuickCommand = async (cmd: typeof QUICK_COMMANDS[0]) => {
    const id = ++idCounter.current;
    const entry: ConsoleEntry = {
      id,
      method: cmd.method,
      params: "",
      timestamp: Date.now(),
      loading: true,
    };
    setHistory((prev) => [...prev, entry]);

    try {
      let result: unknown;
      switch (cmd.method) {
        case "getnetworkinfo": result = await getNetworkInfo(); break;
        case "getmininginfo": result = await getMiningInfo(); break;
        case "getwalletinfo": result = await getWalletInfo(); break;
        case "getrawmempool": result = await getRawMempool(); break;
        default: result = await rpcCommand(cmd.method, []); break;
      }
      setHistory((prev) =>
        prev.map((e) => (e.id === id ? { ...e, result, loading: false } : e))
      );
    } catch (err) {
      setHistory((prev) =>
        prev.map((e) => (e.id === id ? { ...e, error: String(err), loading: false } : e))
      );
    }
  };

  const clearHistory = () => {
    setHistory([]);
    setExpanded(null);
  };

  if (!connected) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Debug Console</h1>
          <p className="text-sm text-[var(--color-text-muted)]">RPC command interface for CLI access</p>
        </div>
        <Card>
          <CardContent className="pt-5">
            <div className="flex flex-col items-center py-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-danger-dim)]">
                <Terminal className="h-6 w-6 text-red-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-[var(--color-text)]">Not connected to daemon</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">Connect to a daemon to use the RPC console</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Debug Console</h1>
          <p className="text-sm text-[var(--color-text-muted)]">RPC command interface for CLI access</p>
        </div>
        {history.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearHistory}>
            <Trash2 className="h-3.5 w-3.5" />
            Clear
          </Button>
        )}
      </div>

      {/* Quick commands */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Commands</CardTitle>
          <CardDescription>Common RPC calls</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            {QUICK_COMMANDS.map((cmd) => (
              <button
                key={cmd.method}
                onClick={() => handleQuickCommand(cmd)}
                className="flex items-center gap-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-elevated)] px-3 py-2.5 text-left hover:border-[var(--color-primary)]/30 hover:bg-[var(--color-surface-hover)] transition-all cursor-pointer"
              >
                <cmd.icon className="h-4 w-4 text-[var(--color-primary)] shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[var(--color-text)] truncate">{cmd.label}</p>
                  <p className="font-mono text-xs text-[var(--color-text-dim)] truncate">{cmd.method}</p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* RPC command input */}
      <Card>
        <CardHeader>
          <CardTitle>RPC Command</CardTitle>
          <CardDescription>Enter an RPC method and parameters (comma-separated)</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-[1fr_1fr_auto] gap-3">
              <Input
                placeholder="RPC method (e.g. getbalance)"
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="font-mono"
              />
              <Input
                placeholder="params (e.g. *, 0, true)"
                value={params}
                onChange={(e) => setParams(e.target.value)}
                className="font-mono"
              />
              <Button type="submit" disabled={!method.trim()}>
                <Send className="h-4 w-4" />
                Execute
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Console output */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-[var(--color-primary)]" />
            <CardTitle>Console Output</CardTitle>
            {history.length > 0 && (
              <Badge variant="info">{history.length}</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <div className="flex flex-col items-center py-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]">
                <Terminal className="h-6 w-6 text-[var(--color-text-dim)]" />
              </div>
              <p className="mt-4 text-sm font-medium text-[var(--color-text)]">No commands executed yet</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">Run a quick command or enter an RPC method above</p>
            </div>
          ) : (
            <div ref={scrollRef} className="space-y-2 max-h-[500px] overflow-y-auto">
              {history.map((entry) => (
                <div
                  key={entry.id}
                  className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-elevated)] overflow-hidden"
                >
                  {/* Command header */}
                  <div
                    onClick={() => setExpanded(expanded === entry.id ? null : entry.id)}
                    className="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-[var(--color-surface-hover)] transition-colors"
                  >
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 text-[var(--color-text-dim)] transition-transform shrink-0",
                        expanded === entry.id && "rotate-180"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium text-[var(--color-primary)]">
                          {entry.method}
                        </span>
                        {entry.params && (
                          <span className="font-mono text-xs text-[var(--color-text-dim)] truncate">
                            {entry.params}
                          </span>
                        )}
                      </div>
                    </div>
                    {entry.loading ? (
                      <Badge variant="info">Loading...</Badge>
                    ) : entry.error ? (
                      <Badge variant="danger">Error</Badge>
                    ) : (
                      <Badge variant="success">OK</Badge>
                    )}
                    <span className="text-xs text-[var(--color-text-dim)] tabular-nums shrink-0">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {/* Result */}
                  {expanded === entry.id && !entry.loading && (
                    <div className="border-t border-[var(--color-border)] p-3">
                      {entry.error ? (
                        <pre className="text-xs text-red-400 whitespace-pre-wrap break-all">
                          {entry.error}
                        </pre>
                      ) : (
                        <pre className="text-xs text-[var(--color-text-dim)] whitespace-pre-wrap break-all max-h-80 overflow-y-auto">
                          {JSON.stringify(entry.result, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
