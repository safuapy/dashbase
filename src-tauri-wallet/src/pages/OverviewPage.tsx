import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatShortAmount, timeAgo, truncateAddress } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft } from "lucide-react";

export default function OverviewPage() {
  const { balance, blockchainInfo, transactions, connected, error } = useWalletStore();

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-sm text-[var(--color-danger)]">{error}</p>
            <p className="mt-2 text-xs text-[var(--color-text-muted)]">
              Make sure dashbased is running and RPC credentials are configured.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!connected || !balance) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-[var(--color-text-muted)]">Connecting to dashbased...</p>
      </div>
    );
  }

  const recentTx = transactions.slice(0, 8);

  return (
    <div className="space-y-6">
      {/* Balance cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-[var(--color-text-muted)]">Available Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-[var(--color-text)]">
              {formatShortAmount(balance.balance)} <span className="text-base text-[var(--color-text-muted)]">DASH</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-[var(--color-text-muted)]">Pending</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-[var(--color-text)]">
              {formatShortAmount(balance.unconfirmed_balance)} <span className="text-base text-[var(--color-text-muted)]">DASH</span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-[var(--color-text-muted)]">Anonymized</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-[var(--color-accent)]">
              {formatShortAmount(balance.anonymized_balance)} <span className="text-base text-[var(--color-text-muted)]">DASH</span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Sync status */}
      {blockchainInfo && blockchainInfo.initialblockdownload && (
        <Card>
          <CardContent className="flex items-center justify-between pt-5">
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">Synchronizing...</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                Block {blockchainInfo.blocks.toLocaleString()} of {blockchainInfo.headers.toLocaleString()}
              </p>
            </div>
            <div className="h-2 w-40 overflow-hidden rounded-full bg-[var(--color-surface-hover)]">
              <div
                className="h-full bg-[var(--color-primary)] transition-all"
                style={{ width: `${Math.min(blockchainInfo.verificationprogress * 100, 100)}%` }}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent transactions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Transactions</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => window.location.hash = "#/history"}>
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentTx.length === 0 ? (
            <p className="py-8 text-center text-sm text-[var(--color-text-muted)]">No transactions yet</p>
          ) : (
            <div className="space-y-1">
              {recentTx.map((tx) => {
                const isSend = tx.category === "send";
                return (
                  <div
                    key={tx.txid}
                    className="flex items-center justify-between rounded-md px-3 py-2.5 hover:bg-[var(--color-surface-hover)] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-8 w-8 items-center justify-center rounded-full ${
                          isSend ? "bg-red-500/10" : "bg-green-500/10"
                        }`}
                      >
                        {isSend ? (
                          <ArrowUpRight className="h-4 w-4 text-red-400" />
                        ) : (
                          <ArrowDownLeft className="h-4 w-4 text-green-400" />
                        )}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-[var(--color-text)]">
                          {isSend ? "Sent" : "Received"}
                        </p>
                        <p className="text-xs text-[var(--color-text-dim)]">
                          {tx.address ? truncateAddress(tx.address) : "—"} · {timeAgo(tx.timereceived || tx.time)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-semibold ${
                          isSend ? "text-red-400" : "text-green-400"
                        }`}
                      >
                        {isSend ? "-" : "+"}
                        {formatShortAmount(Math.abs(tx.amount))} DASH
                      </span>
                      {tx.confirmations > 0 ? (
                        <Badge variant="success">Confirmed</Badge>
                      ) : (
                        <Badge variant="warning">Pending</Badge>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
