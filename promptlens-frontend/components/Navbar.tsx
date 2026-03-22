"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Dashboard" },
  { href: "/analyzer", label: "Analyzer" },
  { href: "/chat", label: "Chat" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-30 border-b border-cyan-300/20 bg-slate-950/75 backdrop-blur-xl">
      <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="group inline-flex items-center gap-3">
          <span className="pulse-dot h-2.5 w-2.5 rounded-full bg-emerald-300" />
          <span className="text-lg font-semibold tracking-wide text-emerald-200 transition group-hover:text-emerald-100">
            PromptLens
          </span>
          <span className="rounded-full border border-emerald-300/30 bg-emerald-400/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] text-emerald-200">
            Live
          </span>
        </Link>

        <div className="soft-ring flex items-center gap-2 rounded-full border border-cyan-400/30 bg-slate-900/75 p-1.5">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-3.5 py-1.5 text-sm transition-all duration-200 ${
                  isActive
                    ? "bg-cyan-400/20 text-cyan-100 shadow-[0_0_0_1px_rgba(34,211,238,0.35)]"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
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
