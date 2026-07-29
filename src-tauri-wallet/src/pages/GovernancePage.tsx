import { useState, useEffect } from "react";
import { useWalletStore, type GovernanceProposal } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Vote, ThumbsUp, ThumbsDown, Minus, ExternalLink, RefreshCw, X } from "lucide-react";
import { cn } from "@/lib/utils";

function timeAgo(ts: number): string {
  if (!ts) return "—";
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function timeUntil(ts: number): string {
  if (!ts) return "—";
  const diff = ts - Date.now() / 1000;
  if (diff < 0) return "expired";
  if (diff < 3600) return `${Math.floor(diff / 60)}m left`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h left`;
  return `${Math.floor(diff / 86400)}d left`;
}

export default function GovernancePage() {
  const { connected, proposals, refreshProposals, voteOnProposal, getProposalInfo } = useWalletStore();
  const [selected, setSelected] = useState<GovernanceProposal | null>(null);
  const [proposalDetail, setProposalDetail] = useState<unknown>(null);
  const [voting, setVoting] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);

  useEffect(() => {
    if (connected) refreshProposals();
  }, [connected, refreshProposals]);

  const showMsg = (m: string) => { setActionMsg(m); setActionErr(null); setTimeout(() => setActionMsg(null), 4000); };
  const showErr = (e: string) => { setActionErr(e); setActionMsg(null); };

  const handleVote = async (proposalHash: string, vote: string) => {
    setVoting(true);
    try {
      const result = await voteOnProposal(proposalHash, vote, "funding");
      showMsg(`Vote submitted: ${result}`);
      await refreshProposals();
    } catch (e) {
      showErr(String(e));
    } finally {
      setVoting(false);
    }
  };

  const handleSelectProposal = async (proposal: GovernanceProposal) => {
    setSelected(proposal);
    setProposalDetail(null);
    try {
      const detail = await getProposalInfo(proposal.hash);
      setProposalDetail(detail);
    } catch {
      // ignore
    }
  };

  const activeCount = proposals.filter((p) => p.is_active).length;
  const fundedCount = proposals.filter((p) => p.cached_funding_state).length;
  const totalVotes = proposals.reduce((sum, p) => sum + p.absolute_yes_count, 0);

  if (!connected) {
    return (
      <div className="space-y-6 animate-fade-in-up">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Governance</h1>
          <p className="text-sm text-[var(--color-text-muted)]">View and vote on proposals</p>
        </div>
        <Card>
          <CardContent className="pt-5">
            <div className="flex flex-col items-center py-12">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-danger-dim)]">
                <Vote className="h-6 w-6 text-red-400" />
              </div>
              <p className="mt-4 text-sm font-medium text-[var(--color-text)]">Not connected to daemon</p>
              <p className="mt-1 text-xs text-[var(--color-text-muted)]">Connect to a daemon with governance RPC commands enabled</p>
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
          <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Governance</h1>
          <p className="text-sm text-[var(--color-text-muted)]">View and vote on proposals</p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => refreshProposals()}>
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {actionMsg && (
        <div className="rounded-lg border border-green-500/20 bg-[var(--color-success-dim)] px-4 py-3 text-sm text-green-400 animate-scale-in">{actionMsg}</div>
      )}
      {actionErr && (
        <div className="rounded-lg border border-red-500/20 bg-[var(--color-danger-dim)] px-4 py-3 text-sm text-red-400 animate-scale-in">{actionErr}</div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Total Proposals</p>
          <p className="text-2xl font-bold tabular-nums text-[var(--color-text)]">{proposals.length}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Active</p>
          <p className="text-2xl font-bold tabular-nums text-green-400">{activeCount}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Funded</p>
          <p className="text-2xl font-bold tabular-nums text-[var(--color-primary)]">{fundedCount}</p>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4">
          <p className="text-xs text-[var(--color-text-muted)]">Total Votes</p>
          <p className="text-2xl font-bold tabular-nums text-[var(--color-accent)]">{totalVotes}</p>
        </div>
      </div>

      {/* Proposal list + detail */}
      <div className="grid grid-cols-[1fr_400px] gap-6">
        {/* List */}
        <Card>
          <CardHeader>
            <CardTitle>Proposals</CardTitle>
            <CardDescription>{proposals.length} proposals on the network</CardDescription>
          </CardHeader>
          <CardContent>
            {proposals.length === 0 ? (
              <div className="flex flex-col items-center py-12">
                <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[var(--color-surface-hover)]">
                  <Vote className="h-6 w-6 text-[var(--color-text-dim)]" />
                </div>
                <p className="mt-4 text-sm font-medium text-[var(--color-text)]">No proposals found</p>
                <p className="mt-1 text-xs text-[var(--color-text-muted)]">Governance proposals will appear here when available</p>
              </div>
            ) : (
              <div className="space-y-0.5">
                {proposals.map((p) => (
                  <div
                    key={p.hash}
                    onClick={() => handleSelectProposal(p)}
                    className={cn(
                      "cursor-pointer rounded-lg px-3 py-3 transition-colors",
                      selected?.hash === p.hash
                        ? "bg-[var(--color-primary)]/10"
                        : "hover:bg-[var(--color-surface-hover)]"
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium text-[var(--color-text)] truncate">{p.name || "Unnamed"}</p>
                          {p.is_active && <Badge variant="success">Active</Badge>}
                          {p.cached_funding_state && <Badge variant="info">Funded</Badge>}
                        </div>
                        <p className="mt-0.5 font-mono text-xs text-[var(--color-text-dim)] truncate">{p.hash.slice(0, 24)}...</p>
                      </div>
                      <div className="flex items-center gap-3 ml-3">
                        <div className="text-right">
                          <div className="flex items-center gap-1.5">
                            <ThumbsUp className="h-3 w-3 text-green-400" />
                            <span className="text-xs tabular-nums text-[var(--color-text)]">{p.yes_count}</span>
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5">
                            <ThumbsDown className="h-3 w-3 text-red-400" />
                            <span className="text-xs tabular-nums text-[var(--color-text)]">{p.no_count}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detail panel */}
        {selected && (
          <Card className="animate-scale-in h-fit">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Proposal Details</CardTitle>
                <Button variant="ghost" size="icon" onClick={() => setSelected(null)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Name</p>
                <p className="text-sm font-medium text-[var(--color-text)]">{selected.name || "Unnamed"}</p>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Hash</p>
                <p className="font-mono text-xs text-[var(--color-text-dim)] break-all">{selected.hash}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Payment Amount</p>
                  <p className="text-sm font-medium tabular-nums text-[var(--color-text)]">{selected.payment_amount} DASH</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Created</p>
                  <p className="text-sm text-[var(--color-text)]">{timeAgo(selected.creation_time)}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Expires</p>
                  <p className="text-sm text-[var(--color-text)]">{timeUntil(selected.end_epoch_time)}</p>
                </div>
                <div>
                  <p className="text-xs text-[var(--color-text-muted)]">Status</p>
                  <div className="flex gap-1">
                    {selected.is_valid ? <Badge variant="success">Valid</Badge> : <Badge variant="danger">Invalid</Badge>}
                    {selected.is_active && <Badge variant="info">Active</Badge>}
                  </div>
                </div>
              </div>
              <div>
                <p className="text-xs text-[var(--color-text-muted)] mb-1">Payment Address</p>
                <p className="font-mono text-xs text-[var(--color-text-dim)] break-all">{selected.payment_address}</p>
              </div>
              {selected.url && (
                <div>
                  <a
                    href={selected.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm text-[var(--color-primary)] hover:underline"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    View Proposal Details
                  </a>
                </div>
              )}
              {/* Vote counts */}
              <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-3 space-y-2">
                <p className="text-xs font-medium text-[var(--color-text-muted)]">Vote Counts</p>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-xs text-green-400">Yes</p>
                    <p className="text-lg font-bold tabular-nums text-[var(--color-text)]">{selected.yes_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-red-400">No</p>
                    <p className="text-lg font-bold tabular-nums text-[var(--color-text)]">{selected.no_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-muted)]">Abstain</p>
                    <p className="text-lg font-bold tabular-nums text-[var(--color-text)]">{selected.abstain_count}</p>
                  </div>
                </div>
                <div className="border-t border-[var(--color-border)] pt-2 text-center">
                  <p className="text-xs text-[var(--color-text-muted)]">Net Votes</p>
                  <p className="text-lg font-bold tabular-nums text-[var(--color-primary)]">{selected.absolute_yes_count}</p>
                </div>
              </div>
              {/* Voting buttons */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1"
                  onClick={() => handleVote(selected.hash, "yes")}
                  disabled={voting}
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                  Yes
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1"
                  onClick={() => handleVote(selected.hash, "no")}
                  disabled={voting}
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                  No
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  className="flex-1"
                  onClick={() => handleVote(selected.hash, "abstain")}
                  disabled={voting}
                >
                  <Minus className="h-3.5 w-3.5" />
                  Abstain
                </Button>
              </div>
              {proposalDetail !== null && (
                <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-3">
                  <p className="text-xs font-medium text-[var(--color-text-muted)] mb-2">Raw Data</p>
                  <pre className="text-xs text-[var(--color-text-dim)] overflow-x-auto whitespace-pre-wrap break-all max-h-48 overflow-y-auto">
                    {JSON.stringify(proposalDetail, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
