import { useState } from "react";
import { useWalletStore } from "@/stores/walletStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { truncateAddress } from "@/lib/utils";
import { Copy, Check, Plus, QrCode } from "lucide-react";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import QRCode from "qrcode";

export default function ReceivePage() {
  const { addresses, getNewAddress, refresh } = useWalletStore();
  const [label, setLabel] = useState("");
  const [newAddr, setNewAddr] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [qrSrc, setQrSrc] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const receiveAddresses = addresses.filter((a) => a.purpose === "receive");

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const addr = await getNewAddress(label || "Receive");
      setNewAddr(addr);
      setLabel("");
      await refresh();
      generateQR(addr);
    } catch (err) {
      console.error(err);
    } finally {
      setGenerating(false);
    }
  };

  const generateQR = async (addr: string) => {
    const qr = await QRCode.toDataURL(`dashbase:${addr}`, {
      width: 256,
      margin: 2,
      color: { dark: "#0a0b0d", light: "#ffffff" },
    });
    setQrSrc(qr);
  };

  const copyAddr = async (addr: string) => {
    await writeText(addr);
    setCopied(addr);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="max-w-3xl space-y-6 animate-fade-in-up">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-[var(--color-text)]">Receive</h1>
        <p className="text-sm text-[var(--color-text-muted)]">Generate a new address or use an existing one</p>
      </div>

      {/* Generate new address */}
      <Card>
        <CardHeader>
          <CardTitle>Generate New Address</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Input
              placeholder="Label (optional)"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              className="flex-1"
            />
            <Button onClick={handleGenerate} disabled={generating}>
              <Plus className="h-4 w-4" />
              Generate
            </Button>
          </div>

          {newAddr && (
            <div className="flex items-center gap-6 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-elevated)] p-4 animate-scale-in">
              {qrSrc && (
                <div className="rounded-lg bg-white p-2">
                  <img src={qrSrc} alt="QR code" className="h-32 w-32" />
                </div>
              )}
              <div className="flex-1">
                <p className="text-xs text-[var(--color-text-muted)] mb-1">New address</p>
                <p className="font-mono text-sm text-[var(--color-text)] break-all">{newAddr}</p>
                <Button
                  variant="secondary"
                  size="sm"
                  className="mt-3"
                  onClick={() => copyAddr(newAddr)}
                >
                  {copied === newAddr ? (
                    <><Check className="h-3.5 w-3.5" /> Copied</>
                  ) : (
                    <><Copy className="h-3.5 w-3.5" /> Copy</>
                  )}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Existing addresses */}
      <Card>
        <CardHeader>
          <CardTitle>Your Addresses</CardTitle>
        </CardHeader>
        <CardContent>
          {receiveAddresses.length === 0 ? (
            <div className="flex flex-col items-center py-12">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-surface-hover)]">
                <Plus className="h-5 w-5 text-[var(--color-text-dim)]" />
              </div>
              <p className="mt-3 text-sm text-[var(--color-text-muted)]">No addresses yet</p>
              <p className="mt-1 text-xs text-[var(--color-text-dim)]">Generate one above to get started</p>
            </div>
          ) : (
            <div className="space-y-0.5">
              {receiveAddresses.map((addr) => (
                <div
                  key={addr.address}
                  className="group flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--color-text)]">
                      {addr.label || "No label"}
                    </p>
                    <p className="font-mono text-xs text-[var(--color-text-dim)]">
                      {truncateAddress(addr.address, 12)}
                    </p>
                  </div>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => copyAddr(addr.address)}
                    >
                      {copied === addr.address ? (
                        <Check className="h-4 w-4 text-green-400" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => generateQR(addr.address)}
                    >
                      <QrCode className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* QR modal */}
      {qrSrc && !newAddr && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 animate-scale-in"
          onClick={() => setQrSrc(null)}
        >
          <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <div className="rounded-lg bg-white p-3">
              <img src={qrSrc} alt="QR code" className="h-48 w-48" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
