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
  Terminal,
} from "lucide-react";
import { useWalletStore } from "@/stores/walletStore";
import { cn, formatShortAmount } from "@/lib/utils";

const navItems = [
  { to: "/", label: "Overview", icon: LayoutDashboard },
  { to: "/send", label: "Send", icon: ArrowUpRight },
  { to: "/receive", label: "Receive", icon: ArrowDownLeft },
  { to: "/history", label: "History", icon: History },
  { to: "/masternodes", label: "Masternodes", icon: Server },
  { to: "/governance", label: "Governance", icon: Vote },
  { to: "/settings", label: "Settings", icon: Settings },
  { to: "/debug", label: "Debug", icon: Terminal },
];

export function AppLayout() {
  const { connected, balance, blockchainInfo, refresh, loading, error } = useWalletStore();

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, [refresh]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[var(--color-bg)]">
      {/* Sidebar */}
      <aside className="flex w-60 flex-col border-r border-[var(--color-border)] bg-[var(--color-surface)]">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[var(--color-border)]">
          <div className="relative">
            <img src="/dashbase.svg" alt="Dashbase" className="h-7 w-7" />
            <div className="absolute inset-0 blur-lg opacity-30">
              <img src="/dashbase.svg" alt="" className="h-7 w-7" />
            </div>
          </div>
          <span className="text-base font-bold tracking-tight text-[var(--color-text)]">
            Dashbase
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-0.5 px-3 py-4">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-[var(--color-primary)]/10 text-[var(--color-primary)]"
                    : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)]"
                )
              }
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-[var(--color-primary)]" />
                  )}
                  <item.icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Connection status */}
        <div className="border-t border-[var(--color-border)] px-4 py-3.5">
          <div className="flex items-center gap-2 text-xs">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                connected
                  ? "bg-green-400 pulse-glow"
                  : "bg-red-400"
              )}
            />
            {connected ? (
              <span className="text-[var(--color-text-muted)]">Connected</span>
            ) : (
              <span className="text-[var(--color-text-muted)]">Disconnected</span>
            )}
            {error && !connected && (
              <span
                className="text-[var(--color-text-dim)] truncate"
                title={error}
              >
                · {error}
              </span>
            )}
          </div>
          {blockchainInfo && (
            <div className="mt-1.5 text-xs text-[var(--color-text-dim)]">
              Block {blockchainInfo.blocks.toLocaleString()}
              {blockchainInfo.initialblockdownload && (
                <span className="text-[var(--color-primary)]"> · Syncing</span>
              )}
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
                <span className="text-sm font-semibold tabular-nums text-[var(--color-text)]">
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
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)] hover:text-[var(--color-text)] transition-all cursor-pointer active:scale-95"
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
