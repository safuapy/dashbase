import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatShortAmount, timeAgo, truncateAddress } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft, Wallet, Clock, Sparkles, ChevronRight } from "lucide-react";

export default function OverviewPage() {
  const { balance, blockchainInfo, transactions, connected, error } = useWalletStore();

  if (error) {
    return (
      <div className="flex h-full items-center justify-center animate-fade-in-up">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-danger-dim)]">
                <span className="h-2 w-2 rounded-full bg-red-400" />
              </div>
              <p className="text-sm font-medium text-[var(--color-danger)]">Connection Error</p>
            </div>
            <p className="text-sm text-[var(--color-text-muted)]">{error}</p>
            <p className="mt-3 text-xs text-[var(--color-text-dim)]">
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
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--color-border)] border-t-[var(--color-primary)]" />
          <p className="text-sm text-[var(--color-text-muted)]">Connecting to dashbased...</p>
        </div>
      </div>
    );
  }

  const recentTx = transactions.slice(0, 8);
  const totalBalance = balance.balance + balance.unconfirmed_balance;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Balance hero */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className="md:col-span-2 hero-gradient relative overflow-hidden">
          <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-[var(--color-primary)]/5 blur-3xl" />
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <Wallet className="h-4 w-4" />
              Available Balance
            </div>
            <p className="mt-2 text-4xl font-bold tabular-nums text-[var(--color-text)]">
              {formatShortAmount(balance.balance)}
              <span className="ml-2 text-lg font-normal text-[var(--color-text-muted)]">DASH</span>
            </p>
            {totalBalance !== balance.balance && (
              <p className="mt-1 text-xs text-[var(--color-text-dim)]">
                Total incl. pending: {formatShortAmount(totalBalance)} DASH
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
              <Clock className="h-4 w-4" />
              Pending
            </div>
            <p className="mt-2 text-2xl font-bold tabular-nums text-[var(--color-text)]">
              {formatShortAmount(balance.unconfirmed_balance)}
              <span className="ml-1.5 text-sm font-normal text-[var(--color-text-muted)]">DASH</span>
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Secondary stats row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card className="flex items-center gap-4 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-accent-dim)]">
            <Sparkles className="h-5 w-5 text-[var(--color-accent)]" />
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Anonymized</p>
            <p className="text-lg font-semibold tabular-nums text-[var(--color-accent)]">
              {formatShortAmount(balance.anonymized_balance)}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-primary)]/10">
            <span className="text-xs font-bold text-[var(--color-primary)]">IM</span>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Immature</p>
            <p className="text-lg font-semibold tabular-nums text-[var(--color-text)]">
              {formatShortAmount(balance.immature_balance ?? 0)}
            </p>
          </div>
        </Card>

        <Card className="flex items-center gap-4 p-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--color-info-dim)]">
            <span className="text-xs font-bold text-blue-400">TXs</span>
          </div>
          <div>
            <p className="text-xs text-[var(--color-text-muted)]">Total Transactions</p>
            <p className="text-lg font-semibold tabular-nums text-[var(--color-text)]">
              {transactions.length}
            </p>
          </div>
        </Card>
      </div>

      {/* Sync status */}
      {blockchainInfo && blockchainInfo.initialblockdownload && (
        <Card>
          <CardContent className="flex items-center justify-between pt-5">
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">Synchronizing</p>
              <p className="text-xs text-[var(--color-text-muted)]">
                Block {blockchainInfo.blocks.toLocaleString()} of {blockchainInfo.headers.toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-sm font-semibold tabular-nums text-[var(--color-primary)]">
                {Math.min(blockchainInfo.verificationprogress * 100, 100).toFixed(1)}%
              </span>
              <div className="h-2 w-40 overflow-hidden rounded-full bg-[var(--color-surface-hover)]">
                <div
                  className="h-full rounded-full bg-[var(--color-primary)] transition-all duration-500"
                  style={{ width: `${Math.min(blockchainInfo.verificationprogress * 100, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent transactions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Recent Transactions</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => (window.location.hash = "#/history")}
            >
              View All
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentTx.length === 0 ? (
            <div className="flex flex-col items-center py-12">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-surface-hover)]">
                <ArrowDownLeft className="h-5 w-5 text-[var(--color-text-dim)]" />
              </div>
              <p className="mt-3 text-sm text-[var(--color-text-muted)]">No transactions yet</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {recentTx.map((tx) => {
                const isSend = tx.category === "send";
                return (
                  <div
                    key={tx.txid}
                    className="group flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-[var(--color-surface-hover)] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                          isSend ? "bg-[var(--color-danger-dim)]" : "bg-[var(--color-success-dim)]"
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
                        <p className="font-mono text-xs text-[var(--color-text-dim)]">
                          {tx.address ? truncateAddress(tx.address) : "—"} · {timeAgo(tx.timereceived || tx.time)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`text-sm font-semibold tabular-nums ${
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
