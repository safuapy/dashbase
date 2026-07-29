import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent } from "@/components/ui/Card";
import { Vote } from "lucide-react";

export default function GovernancePage() {
  const { connected } = useWalletStore();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text)]">Governance</h1>
        <p className="text-sm text-[var(--color-text-muted)]">View and vote on proposals</p>
      </div>

      <Card>
        <CardContent className="pt-5">
          {connected ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <Vote className="mx-auto h-10 w-10 text-[var(--color-text-dim)]" />
                <p className="mt-3 text-sm text-[var(--color-text-muted)]">
                  Governance proposals will appear here
                </p>
                <p className="mt-1 text-xs text-[var(--color-text-dim)]">
                  Connect to a daemon with governance RPC commands
                </p>
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
