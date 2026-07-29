import { useState } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { formatShortAmount } from "@/lib/utils";
import { Send, AlertCircle, Check, Loader2, Zap, Gauge, Turtle } from "lucide-react";

type FeeTier = "slow" | "average" | "fast";

const feeTiers: { key: FeeTier; label: string; icon: typeof Zap; desc: string }[] = [
  { key: "slow", label: "Slow", icon: Turtle, desc: "~1 hour" },
  { key: "average", label: "Average", icon: Gauge, desc: "~15 min" },
  { key: "fast", label: "Fast", icon: Zap, desc: "~5 min" },
];

export default function SendPage() {
  const { balance, sendToAddress, validateAddress } = useWalletStore();
  const [address, setAddress] = useState("");
  const [amount, setAmount] = useState("");
  const [label, setLabel] = useState("");
  const [subtractFee, setSubtractFee] = useState(false);
  const [useCoinJoin, setUseCoinJoin] = useState(false);
  const [feeTier, setFeeTier] = useState<FeeTier>("average");
  const [addressValid, setAddressValid] = useState<boolean | null>(null);
  const [sending, setSending] = useState(false);
  const [txid, setTxid] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateAddr = async (addr: string) => {
    setAddress(addr);
    setAddressValid(null);
    if (addr.length > 10) {
      try {
        const result = await validateAddress(addr);
        setAddressValid(result.isvalid);
      } catch {
        setAddressValid(false);
      }
    }
  };

  const handleSend = async () => {
    setSending(true);
    setError(null);
    setTxid(null);
    try {
      const amt = parseFloat(amount);
      if (!amt || amt <= 0) throw new Error("Invalid amount");
      if (!addressValid) throw new Error("Invalid address");

      const result = await sendToAddress(address, amt, subtractFee, useCoinJoin);
      setTxid(result);
      setAddress("");
      setAmount("");
      setLabel("");
      setAddressValid(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setSending(false);
    }
  };

  const available = balance?.balance ?? 0;
  const numAmount = parseFloat(amount) || 0;
  const canSend = addressValid && numAmount > 0 && !sending;

  return (
    <div className="max-w-2xl space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Send</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Send Dashbase to an address</p>
      </div>

      {txid && (
        <Card className="border-green-500/20 bg-[var(--color-success-dim)] animate-scale-in">
          <CardContent className="flex items-center gap-3 pt-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-green-500/15">
              <Check className="h-5 w-5 text-green-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-green-400">Transaction sent successfully</p>
              <p className="font-mono text-xs text-[var(--color-text-muted)] truncate">{txid}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-red-500/20 bg-[var(--color-danger-dim)] animate-scale-in">
          <CardContent className="flex items-center gap-3 pt-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-red-500/15">
              <AlertCircle className="h-5 w-5 text-red-400" />
            </div>
            <p className="text-sm text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="space-y-5 pt-5">
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Recipient Address</label>
            <Input
              placeholder="Enter Dashbase address"
              value={address}
              onChange={(e) => validateAddr(e.target.value)}
              className={addressValid === false ? "border-red-500/50" : addressValid === true ? "border-green-500/50" : ""}
            />
            {addressValid === false && (
              <p className="text-xs text-red-400">Invalid address</p>
            )}
            {addressValid === true && (
              <p className="text-xs text-green-400">Valid address</p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Amount (DASH)</label>
            <Input
              type="number"
              step="0.00000001"
              placeholder="0.00000000"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
            <div className="flex items-center justify-between text-xs">
              <span className="text-[var(--color-text-muted)]">
                Available: {formatShortAmount(available)} DASH
              </span>
              <button
                className="text-[var(--color-primary)] hover:underline cursor-pointer font-medium"
                onClick={() => setAmount(String(available / 1e8))}
              >
                Max
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Label (optional)</label>
            <Input
              placeholder="Transaction label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
            />
          </div>

          {/* Fee tier selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--color-text)]">Network Fee</label>
            <div className="grid grid-cols-3 gap-2">
              {feeTiers.map((tier) => (
                <button
                  key={tier.key}
                  onClick={() => setFeeTier(tier.key)}
                  className={`flex flex-col items-center gap-1 rounded-lg border px-3 py-2.5 transition-all cursor-pointer active:scale-95 ${
                    feeTier === tier.key
                      ? "border-[var(--color-primary)]/40 bg-[var(--color-primary)]/10"
                      : "border-[var(--color-border)] hover:border-[var(--color-border-hover)] hover:bg-[var(--color-surface-hover)]"
                  }`}
                >
                  <tier.icon className={`h-4 w-4 ${feeTier === tier.key ? "text-[var(--color-primary)]" : "text-[var(--color-text-muted)]"}`} />
                  <span className={`text-xs font-medium ${feeTier === tier.key ? "text-[var(--color-primary)]" : "text-[var(--color-text)]"}`}>
                    {tier.label}
                  </span>
                  <span className="text-[10px] text-[var(--color-text-dim)]">{tier.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <label className="flex items-center gap-2.5 text-sm text-[var(--color-text)] cursor-pointer">
              <input
                type="checkbox"
                checked={subtractFee}
                onChange={(e) => setSubtractFee(e.target.checked)}
                className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-primary)]"
              />
              Subtract fee from amount
            </label>
            <label className="flex items-center gap-2.5 text-sm text-[var(--color-text)] cursor-pointer">
              <input
                type="checkbox"
                checked={useCoinJoin}
                onChange={(e) => setUseCoinJoin(e.target.checked)}
                className="h-4 w-4 rounded border-[var(--color-border)] accent-[var(--color-accent)]"
              />
              Use CoinJoin funds only
            </label>
          </div>

          {/* TX Preview */}
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4 space-y-2">
            <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">Transaction Preview</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Amount</span>
              <span className="font-medium tabular-nums text-[var(--color-text)]">
                {numAmount.toFixed(8)} DASH
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-[var(--color-text-muted)]">Network Fee</span>
              <span className="font-medium tabular-nums text-[var(--color-text-muted)]">
                ~0.0001 DASH
              </span>
            </div>
            <div className="flex items-center justify-between text-sm border-t border-[var(--color-border)] pt-2">
              <span className="font-medium text-[var(--color-text)]">Total</span>
              <span className="font-bold tabular-nums text-[var(--color-primary)]">
                {(numAmount + 0.0001).toFixed(8)} DASH
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-[var(--color-border)] pt-4">
            <div>
              <p className="text-xs text-[var(--color-text-muted)]">Transaction amount</p>
              <p className="text-lg font-bold tabular-nums text-[var(--color-text)]">
                {numAmount.toFixed(8)} DASH
              </p>
            </div>
            <Button
              size="lg"
              disabled={!canSend}
              onClick={handleSend}
            >
              {sending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              {sending ? "Sending..." : "Send"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
