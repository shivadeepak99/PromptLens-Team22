"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Metrics Dashboard" },
  { href: "/analyzer", label: "Predictive Analytics Lab" },
  { href: "/chat", label: "Llama-3 Data Agent" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-slate-700 bg-slate-900 shadow-sm">
      <nav className="mx-auto flex w-full max-w-[1400px] items-center justify-between px-4 py-3 xl:px-8">
        <Link href="/" className="inline-flex items-center gap-3">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-blue-600 font-bold text-white shadow-sm">
            PL
          </div>
          <span className="text-lg font-semibold tracking-tight text-slate-100">
            PromptLens <span className="text-slate-400 font-normal ml-1">v1.2 Prod</span>
          </span>
          <span className="ml-2 rounded border border-emerald-500/30 bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-400">
            SYSTEM ONLINE
          </span>
        </Link>

        <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-md border border-slate-700">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-slate-700 text-blue-400 shadow-sm"
                    : "text-slate-400 hover:bg-slate-700/50 hover:text-slate-200"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
