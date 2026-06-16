"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { GitPullRequestArrow, ListChecks, ScrollText, Send, ShieldCheck } from "lucide-react";

const LINKS = [
  { href: "/", label: "Overview", icon: ShieldCheck, exact: true },
  { href: "/process", label: "Process Issue", icon: Send },
  { href: "/runs", label: "Runs", icon: ListChecks },
  { href: "/audit", label: "Audit Log", icon: ScrollText },
];

export default function NavBar() {
  const pathname = usePathname();

  const isActive = (href: string, exact?: boolean) =>
    exact ? pathname === href : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <header className="sticky top-0 z-20 border-b border-ink-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="flex items-center gap-2 text-ink-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <GitPullRequestArrow className="h-5 w-5" />
          </span>
          <span className="text-base font-bold tracking-tight">
            Issue&nbsp;<span className="text-brand-600">→</span>&nbsp;PR Console
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {LINKS.map(({ href, label, icon: Icon, exact }) => {
            const active = isActive(href, exact);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-ink-600 hover:bg-ink-50 hover:text-ink-900"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden sm:inline">{label}</span>
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
