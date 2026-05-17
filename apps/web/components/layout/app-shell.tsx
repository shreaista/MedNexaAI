import Link from "next/link";

import { cn } from "@/lib/utils";

const nav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/facilities", label: "Facilities" },
  { href: "/billing-queue", label: "Billing queue" },
  { href: "/visits/new", label: "New visit" },
];

export function AppShell({
  children,
  currentPath,
}: {
  children: React.ReactNode;
  currentPath: string;
}) {
  return (
    <div className="flex min-h-screen bg-zinc-50">
      <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-zinc-200 bg-white shadow-sm">
        <div className="flex h-16 items-center border-b border-zinc-100 px-5">
          <Link href="/dashboard" className="flex flex-col leading-tight">
            <span className="text-sm font-bold tracking-tight text-emerald-800">
              MedNexa AI
            </span>
            <span className="text-[10px] font-medium uppercase tracking-widest text-zinc-400">
              Clinical workspace
            </span>
          </Link>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 p-3">
          {nav.map((item) => {
            const active =
              currentPath === item.href ||
              (item.href !== "/dashboard" && currentPath.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  active
                    ? "bg-emerald-50 text-emerald-900 ring-1 ring-emerald-100"
                    : "text-zinc-600 hover:bg-zinc-50 hover:text-zinc-900",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-zinc-100 p-4 text-[11px] leading-snug text-zinc-400">
          Enterprise healthcare revenue integrity — Phase 1
        </div>
      </aside>
      <div className="flex flex-1 flex-col pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-zinc-200 bg-white/90 px-8 backdrop-blur">
          <div />
          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-zinc-500 sm:inline">MedNexa AI</span>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800">
              Phase 1
            </span>
          </div>
        </header>
        <main className="flex-1 px-6 py-8 sm:px-8">{children}</main>
      </div>
    </div>
  );
}
