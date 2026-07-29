import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent } from "@/components/ui/Card";
import { Server } from "lucide-react";

export default function MasternodesPage() {
  const { connected } = useWalletStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text)]">Masternodes</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Manage your masternodes</p>
      </div>

      <Card>
        <CardContent className="pt-5">
          {connected ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Total Masternodes</p>
                  <p className="text-2xl font-bold text-[var(--color-text)]">—</p>
                </div>
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Enabled</p>
                  <p className="text-2xl font-bold text-green-400">—</p>
                </div>
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
                  <p className="text-xs text-[var(--color-text-muted)]">Your Masternodes</p>
                  <p className="text-2xl font-bold text-[var(--color-primary)]">—</p>
                </div>
              </div>
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Server className="mx-auto h-10 w-10 text-[var(--color-text-dim)]" />
                  <p className="mt-3 text-sm text-[var(--color-text-muted)]">
                    Masternode list will appear here
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-text-dim)]">
                    Connect to a daemon with masternode RPC commands
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-[var(--color-text-muted)]">
              Not connected to daemon
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
