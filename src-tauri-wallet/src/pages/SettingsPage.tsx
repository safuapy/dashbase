import { useState } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Lock, Unlock, Key, Save, Shield, HardDrive, Network } from "lucide-react";

export default function SettingsPage() {
  const { blockchainInfo, peers, encryptWallet, unlockWallet, lockWallet, walletPassphraseChange, backupWallet } = useWalletStore();
  const [passphrase, setPassphrase] = useState("");
  const [newPassphrase, setNewPassphrase] = useState("");
  const [oldPassphrase, setOldPassphrase] = useState("");
  const [backupPath, setBackupPath] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const showMsg = (m: string) => { setMsg(m); setErr(null); setTimeout(() => setMsg(null), 3000); };
  const showErr = (e: string) => { setErr(e); setMsg(null); };

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Settings</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Wallet and network settings</p>
      </div>

      {msg && (
        <div className="rounded-lg border border-green-500/20 bg-[var(--color-success-dim)] px-4 py-3 text-sm text-green-400 animate-scale-in">{msg}</div>
      )}
      {err && (
        <div className="rounded-lg border border-red-500/20 bg-[var(--color-danger-dim)] px-4 py-3 text-sm text-red-400 animate-scale-in">{err}</div>
      )}

      {/* Wallet security */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-primary)]/10">
              <Shield className="h-4 w-4 text-[var(--color-primary)]" />
            </div>
            <div>
              <CardTitle>Wallet Security</CardTitle>
              <CardDescription>Encrypt, unlock, or change your wallet passphrase</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Encrypt Wallet</label>
            <div className="flex gap-2">
              <Input
                type="password"
                placeholder="New passphrase"
                value={passphrase}
                onChange={(e) => setPassphrase(e.target.value)}
              />
              <Button
                variant="secondary"
                onClick={async () => {
                  try { await encryptWallet(passphrase); showMsg("Wallet encrypted"); setPassphrase(""); } catch (e) { showErr(String(e)); }
                }}
              >
                <Lock className="h-4 w-4" />
                Encrypt
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Unlock Wallet</label>
            <div className="flex gap-2">
              <Input
                type="password"
                placeholder="Passphrase"
                value={passphrase}
                onChange={(e) => setPassphrase(e.target.value)}
              />
              <Button
                variant="secondary"
                onClick={async () => {
                  try { await unlockWallet(passphrase); showMsg("Wallet unlocked"); setPassphrase(""); } catch (e) { showErr(String(e)); }
                }}
              >
                <Unlock className="h-4 w-4" />
                Unlock
              </Button>
              <Button
                variant="outline"
                onClick={async () => {
                  try { await lockWallet(); showMsg("Wallet locked"); } catch (e) { showErr(String(e)); }
                }}
              >
                <Lock className="h-4 w-4" />
                Lock
              </Button>
            </div>
          </div>

          <div className="space-y-2 border-t border-[var(--color-border)] pt-4">
            <label className="text-sm font-medium text-[var(--color-text)]">Change Passphrase</label>
            <Input
              type="password"
              placeholder="Old passphrase"
              value={oldPassphrase}
              onChange={(e) => setOldPassphrase(e.target.value)}
            />
            <Input
              type="password"
              placeholder="New passphrase"
              value={newPassphrase}
              onChange={(e) => setNewPassphrase(e.target.value)}
            />
            <Button
              variant="secondary"
              onClick={async () => {
                try { await walletPassphraseChange(oldPassphrase, newPassphrase); showMsg("Passphrase changed"); setOldPassphrase(""); setNewPassphrase(""); } catch (e) { showErr(String(e)); }
              }}
            >
              <Key className="h-4 w-4" />
              Change
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Backup */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-accent-dim)]">
              <HardDrive className="h-4 w-4 text-[var(--color-accent)]" />
            </div>
            <div>
              <CardTitle>Backup</CardTitle>
              <CardDescription>Backup your wallet.dat file</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="/path/to/backup.dat"
              value={backupPath}
              onChange={(e) => setBackupPath(e.target.value)}
            />
            <Button
              variant="secondary"
              onClick={async () => {
                try { await backupWallet(backupPath); showMsg("Wallet backed up"); setBackupPath(""); } catch (e) { showErr(String(e)); }
              }}
            >
              <Save className="h-4 w-4" />
              Backup
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Network info */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--color-info-dim)]">
              <Network className="h-4 w-4 text-blue-400" />
            </div>
            <CardTitle>Network</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {blockchainInfo && (
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-[var(--color-text-muted)]">Chain</p>
                <p className="font-medium text-[var(--color-text)]">{blockchainInfo.chain}</p>
              </div>
              <div>
                <p className="text-[var(--color-text-muted)]">Blocks</p>
                <p className="font-medium tabular-nums text-[var(--color-text)]">{blockchainInfo.blocks.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[var(--color-text-muted)]">Headers</p>
                <p className="font-medium tabular-nums text-[var(--color-text)]">{blockchainInfo.headers.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[var(--color-text-muted)]">ChainLocks</p>
                <Badge variant={blockchainInfo.chainlocks ? "success" : "warning"}>
                  {blockchainInfo.chainlocks ? "Enabled" : "Disabled"}
                </Badge>
              </div>
              <div>
                <p className="text-[var(--color-text-muted)]">Connected Peers</p>
                <p className="font-medium tabular-nums text-[var(--color-text)]">{peers.length}</p>
              </div>
              <div>
                <p className="text-[var(--color-text-muted)]">Disk Size</p>
                <p className="font-medium tabular-nums text-[var(--color-text)]">
                  {(blockchainInfo.size_on_disk / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
