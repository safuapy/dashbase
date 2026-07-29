import { useEffect } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  ArrowUpRight,
  ArrowDownLeft,
  History,
  Server,
  Vote,
  Settings,
  RefreshCw,
  Wifi,
  WifiOff,
} from "lucide-react";
import { useWalletStore } from "@/stores/walletStore";
import { cn } from "@/lib/utils";
import { formatShortAmount } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/send", label: "Send", icon: ArrowUpRight },
  { to: "/receive", label: "Receive", icon: ArrowDownLeft },
  { to: "/history", label: "History", icon: History },
  { to: "/masternodes", label: "Masternodes", icon: Server },
  { to: "/governance", label: "Governance", icon: Vote },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AppLayout() {
  const { connected, balance, blockchainInfo, refresh, loading } = useWalletStore();

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--color-bg)]">
      {/* Sidebar */}
      <aside className="flex w-60 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        <div className="flex items-center gap-2 px-5 py-5 border-b border-[var(--color-border)]">
          <img src="/dashbase.svg" alt="Dashbase" className="h-7 w-7" />
          <span className="text-base font-bold text-[var(--color-text)]">Dashbase</span>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]"
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Connection status */}
        <div className="border-t border-[var(--color-border)] px-4 py-3">
          <div className="flex items-center gap-2 text-xs">
            {connected ? (
              <>
                <Wifi className="h-3.5 w-3.5 text-green-400" />
                <span className="text-[var(--color-text-muted)]">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3.5 w-3.5 text-red-400" />
                <span className="text-[var(--color-text-muted)]">Disconnected</span>
              </>
            )}
          </div>
          {blockchainInfo && (
            <div className="mt-1 text-xs text-[var(--color-text-dim)]">
              Block {blockchainInfo.blocks.toLocaleString()}
              {blockchainInfo.initialblockdownload && " · Syncing..."}
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-14 items-center justify-between border-b border-[var(--color-border)] px-6">
          <div className="flex items-center gap-4">
            {balance && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-[var(--color-text-muted)]">Balance</span>
                <span className="text-sm font-semibold text-[var(--color-text)]">
                  {formatShortAmount(balance.balance)} DASH
                </span>
                {balance.anonymized_balance > 0 && (
                  <span className="text-xs text-[var(--color-accent)]">
                    ({formatShortAmount(balance.anonymized_balance)} mixed)
                  </span>
                )}
              </div>
            )}
          </div>
          <button
            onClick={() => refresh()}
            disabled={loading}
            className="flex items-center gap-2 rounded-md px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
            Refresh
          </button>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
