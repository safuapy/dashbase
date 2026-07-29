import { useState, useEffect } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Server, Plus, Play, PlayCircle, AlertTriangle, X, RefreshCw } from "lucide-react";

function timeAgo(ts: number): string {
  if (!ts) return "—";
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function statusBadge(status: string) {
  const s = status.toLowerCase();
  if (s.includes("enable") || s.includes("active") || s.includes("running")) return <Badge variant="success">Enabled</Badge>;
  if (s.includes("missing") || s.includes("expired")) return <Badge variant="warning">Missing</Badge>;
  if (s.includes("remove") || s.includes("error")) return <Badge variant="danger">Removed</Badge>;
  return <Badge variant="info">{status || "Unknown"}</Badge>;
}

export default function MasternodesPage() {
  const { connected, masternodes, refreshMasternodes, masternodeStartAlias, masternodeStartAll, masternodeStartMissing, masternodeCreate } = useWalletStore();
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);
  const [busyAlias, setBusyAlias] = useState<string | null>(null);

  // Create form
  const [collateralTx, setCollateralTx] = useState("");
  const [collateralIndex, setCollateralIndex] = useState("0");
  const [ip, setIp] = useState("");
  const [payee, setPayee] = useState("");

  useEffect(() => {
    if (connected) refreshMasternodes();
  }, [connected, refreshMasternodes]);

  const showMsg = (m: string) => { setActionMsg(m); setActionErr(null); setTimeout(() => setActionMsg(null), 4000); };
  const showErr = (e: string) => { setActionErr(e); setActionMsg(null); };

  const enabledCount = masternodes.filter((m) => m.status.toLowerCase().includes("enable") || m.status.toLowerCase().includes("active")).length;

  const handleStartAlias = async (alias: string) => {
    setBusyAlias(alias);
    try {
      const result = await masternodeStartAlias(alias);
      showMsg(`Started ${alias}: ${result}`);
      await refreshMasternodes();
    } catch (e) {
      showErr(String(e));
    } finally {
      setBusyAlias(null);
    }
  };

  const handleStartAll = async () => {
    try {
      const result = await masternodeStartAll();
      showMsg(`Start all: ${result}`);
      await refreshMasternodes();
    } catch (e) {
      showErr(String(e));
    }
  };

  const handleStartMissing = async () => {
    try {
      const result = await masternodeStartMissing();
      showMsg(`Start missing: ${result}`);
      await refreshMasternodes();
    } catch (e) {
      showErr(String(e));
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      const result = await masternodeCreate(collateralTx, parseInt(collateralIndex) || 0, ip, payee);
      showMsg(`Masternode created: ${result}`);
      setShowCreate(false);
      setCollateralTx(""); setCollateralIndex("0"); setIp(""); setPayee("");
      await refreshMasternodes();
    } catch (e) {
      showErr(String(e));
    } finally {
      setCreating(false);
    }
  };

  if (!connected) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Masternodes</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Manage your masternodes</p>
        </div>
        <Card>
          <CardContent className="pt-5">
            <div className="flex flex-col items-center py-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-danger-dim)]">
                <Server className="h-6 w-6 text-red-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-[var(--color-text)]">Not connected to daemon</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">Connect to a daemon with masternode RPC commands enabled</p>
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
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Masternodes</h1>
          <p className="text-sm text-[var(--color-text-muted)]">Manage your masternodes</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => refreshMasternodes()}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
          <Button variant="secondary" size="sm" onClick={handleStartAll}>
            <PlayCircle className="h-3.5 w-3.5" />
            Start All
          </Button>
          <Button variant="secondary" size="sm" onClick={handleStartMissing}>
            <AlertTriangle className="h-3.5 w-3.5" />
            Start Missing
          </Button>
          <Button size="sm" onClick={() => setShowCreate(!showCreate)}>
            <Plus className="h-3.5 w-3.5" />
            Create
          </Button>
        </div>
      </div>

      {actionMsg && (
        <div className="rounded-lg border border-green-500/20 bg-[var(--color-success-dim)] px-4 py-3 text-sm text-green-400 animate-scale-in">{actionMsg}</div>
      )}
      {actionErr && (
        <div className="rounded-lg border border-red-500/20 bg-[var(--color-danger-dim)] px-4 py-3 text-sm text-red-400 animate-scale-in">{actionErr}</div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Total Network</p>
          <p className="text-2xl font-bold tabular-nums text-[var(--color-text)]">{masternodes.length}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Enabled</p>
          <p className="text-2xl font-bold tabular-nums text-green-400">{enabledCount}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Missing / Expired</p>
          <p className="text-2xl font-bold tabular-nums text-amber-400">{masternodes.length - enabledCount}</p>
        </div>
      </div>

      {/* Create form */}
      {showCreate && (
        <Card className="animate-scale-in">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Create Masternode</CardTitle>
                <CardDescription>Register a new masternode using collateral output</CardDescription>
              </div>
              <Button variant="ghost" size="icon" onClick={() => setShowCreate(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-text)]">Collateral TX ID</label>
              <Input
                placeholder="e.g. a1b2c3d4..."
                value={collateralTx}
                onChange={(e) => setCollateralTx(e.target.value)}
                className="font-mono"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">Collateral Output Index</label>
                <Input
                  type="number"
                  placeholder="0"
                  value={collateralIndex}
                  onChange={(e) => setCollateralIndex(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-[var(--color-text)]">IP Address</label>
                <Input
                  placeholder="e.g. 1.2.3.4:9999"
                  value={ip}
                  onChange={(e) => setIp(e.target.value)}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-[var(--color-text)]">Payee Address</label>
              <Input
                placeholder="Dashbase address for rewards"
                value={payee}
                onChange={(e) => setPayee(e.target.value)}
                className="font-mono"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating || !collateralTx || !ip || !payee}>
                {creating ? "Creating..." : "Create Masternode"}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Masternode list */}
      <Card>
        <CardHeader>
          <CardTitle>Masternode List</CardTitle>
          <CardDescription>{masternodes.length} masternodes on the network</CardDescription>
        </CardHeader>
        <CardContent>
          {masternodes.length === 0 ? (
            <div className="flex flex-col items-center py-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]">
                <Server className="h-6 w-6 text-[var(--color-text-dim)]" />
              </div>
              <p className="mt-4 text-sm font-medium text-[var(--color-text)]">No masternodes found</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">Create one or wait for the network to sync</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {/* Header row */}
              <div className="grid grid-cols-[2fr_1fr_1.5fr_1fr_1fr_auto] gap-3 px-3 py-2 text-xs font-medium text-[var(--color-text-dim)] border-b border-[var(--color-border)]">
                <span>Alias</span>
                <span>Status</span>
                <span>Address</span>
                <span>Last Seen</span>
                <span>Last Paid</span>
                <span>Actions</span>
              </div>
              {masternodes.map((mn) => (
                <div
                  key={mn.alias + mn.addr}
                  className="grid grid-cols-[2fr_1fr_1.5fr_1fr_1fr_auto] gap-3 items-center rounded-lg px-3 py-2.5 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <span className="text-sm font-medium text-[var(--color-text)] truncate">{mn.alias || "—"}</span>
                  <span>{statusBadge(mn.status)}</span>
                  <span className="font-mono text-xs text-[var(--color-text-dim)] truncate">{mn.addr || mn.ip || "—"}</span>
                  <span className="text-xs text-[var(--color-text-muted)] tabular-nums">{timeAgo(mn.lastseen)}</span>
                  <span className="text-xs text-[var(--color-text-muted)] tabular-nums">{timeAgo(mn.lastpaid)}</span>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleStartAlias(mn.alias)}
                      disabled={busyAlias === mn.alias}
                      title="Start alias"
                    >
                      {busyAlias === mn.alias ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
