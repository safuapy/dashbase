import { useState, useMemo } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatShortAmount, timeAgo, truncateAddress } from "@/lib/utils";
import { ArrowUpRight, ArrowDownLeft, Search, Download } from "lucide-react";

type FilterType = "all" | "sent" | "received" | "pending";

export default function HistoryPage() {
  const { transactions } = useWalletStore();
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterType>("all");

  const filtered = useMemo(() => {
    return transactions.filter((tx) => {
      if (filter === "sent" && tx.category !== "send") return false;
      if (filter === "received" && tx.category !== "receive") return false;
      if (filter === "pending" && tx.confirmations > 0) return false;
      if (search) {
        const q = search.toLowerCase();
        if (
          !tx.txid.toLowerCase().includes(q) &&
          !tx.address?.toLowerCase().includes(q) &&
          !tx.label?.toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    });
  }, [transactions, search, filter]);

  const exportCSV = () => {
    const rows = ["txid,category,amount,address,label,confirmations,time"];
    for (const tx of filtered) {
      rows.push(
        `${tx.txid},${tx.category},${tx.amount},${tx.address ?? ""},${tx.label ?? ""},${tx.confirmations},${tx.time}`
      );
    }
    const blob = new Blob([rows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transactions.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const filters: { key: FilterType; label: string }[] = [
    { key: "all", label: "All" },
    { key: "sent", label: "Sent" },
    { key: "received", label: "Received" },
    { key: "pending", label: "Pending" },
  ];

  return (
    <div className="space-y-6 animate-fade-in-up">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Transaction History</h1>
          <p className="text-sm text-[var(--color-text-muted)]">{filtered.length} transactions</p>
        </div>
        <Button variant="secondary" size="sm" onClick={exportCSV}>
          <Download className="h-3.5 w-3.5" />
          Export CSV
        </Button>
      </div>

      <Card>
        <CardContent className="space-y-4 pt-5">
          {/* Search + filters */}
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-text-dim)]" />
              <Input
                placeholder="Search by txid, address, or label..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-1">
              {filters.map((f) => (
                <button
                  key={f.key}
                  onClick={() => setFilter(f.key)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all cursor-pointer ${
                    filter === f.key
                      ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                      : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Transaction list */}
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center py-16">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-surface-hover)]">
                <Search className="h-5 w-5 text-[var(--color-text-dim)]" />
              </div>
              <p className="mt-3 text-sm text-[var(--color-text-muted)]">No transactions found</p>
              <p className="mt-1 text-xs text-[var(--color-text-dim)]">Try adjusting your search or filters</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {filtered.map((tx) => {
                const isSend = tx.category === "send";
                return (
                  <div
                    key={tx.txid + tx.address}
                    className="group flex items-center justify-between rounded-lg px-3 py-3 hover:bg-[var(--color-surface-hover)] transition-colors"
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
                          {tx.label && ` · ${tx.label}`}
                        </p>
                        <p className="font-mono text-xs text-[var(--color-text-dim)]">
                          {tx.address ? truncateAddress(tx.address, 10) : "—"} · {timeAgo(tx.timereceived || tx.time)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p
                          className={`text-sm font-semibold tabular-nums ${
                            isSend ? "text-red-400" : "text-green-400"
                          }`}
                        >
                          {isSend ? "-" : "+"}
                          {formatShortAmount(Math.abs(tx.amount))} DASH
                        </p>
                        {tx.fee > 0 && (
                          <p className="text-xs text-[var(--color-text-dim)]">
                            fee: {formatShortAmount(tx.fee)}
                          </p>
                        )}
                      </div>
                      {tx.confirmations > 6 ? (
                        <Badge variant="success">Confirmed</Badge>
                      ) : tx.confirmations > 0 ? (
                        <Badge variant="info">{tx.confirmations} conf</Badge>
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
