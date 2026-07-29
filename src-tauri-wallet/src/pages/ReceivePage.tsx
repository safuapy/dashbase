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
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-[var(--color-text)]">Receive</h1>
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
            <div className="flex items-center gap-6 rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] p-4">
              {qrSrc && (
                <img src={qrSrc} alt="QR code" className="h-32 w-32 rounded-md" />
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
            <p className="py-6 text-center text-sm text-[var(--color-text-muted)]">No addresses yet</p>
          ) : (
            <div className="space-y-1">
              {receiveAddresses.map((addr) => (
                <div
                  key={addr.address}
                  className="flex items-center justify-between rounded-md px-3 py-2.5 hover:bg-[var(--color-surface-hover)] transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--color-text)]">
                      {addr.label || "No label"}
                    </p>
                    <p className="font-mono text-xs text-[var(--color-text-dim)]">
                      {truncateAddress(addr.address, 12)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
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
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
          onClick={() => setQrSrc(null)}
        >
          <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <img src={qrSrc} alt="QR code" className="h-48 w-48 rounded-md" />
          </div>
        </div>
      )}
    </div>
  );
}
