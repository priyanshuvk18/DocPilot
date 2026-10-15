"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  MessageSquare,
  FileText,
  FolderTree,
  Zap,
  Activity,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Shield,
  Layers,
  Search,
  ExternalLink,
} from "lucide-react";
import { spring } from "@/lib/utils";

const NAV_ITEMS = [
  { name: "Chat", href: "/chat", icon: MessageSquare },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Collections", href: "/collections", icon: FolderTree },
  { name: "Agent Actions", href: "/actions", icon: Zap },
  { name: "Evals & Safety", href: "/evals", icon: Activity },
  { name: "Monitoring", href: "/monitoring", icon: BarChart3 },
  { name: "Settings & Tools", href: "/settings", icon: Settings },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden bg-[#090B11] text-[#F1F3F9]">
      {/* Sidebar */}
      <aside
        className={`relative flex flex-col border-r border-white/5 bg-[#0D101A] transition-all duration-300 ease-in-out ${
          collapsed ? "w-20" : "w-64"
        }`}
      >
        {/* Workspace Brand / Header */}
        <div className="flex h-16 items-center justify-between border-b border-white/5 px-4">
          <Link href="/" className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent text-white shadow-[0_0_15px_var(--accent-glow)]">
              <Sparkles className="h-5 w-5" />
            </div>
            {!collapsed && (
              <div className="flex flex-col">
                <span className="text-base font-bold tracking-tight text-white">
                  Doc<span className="text-accent">Pilot</span>
                </span>
                <span className="text-[10px] text-muted-foreground truncate">Acme Workspace</span>
              </div>
            )}
          </Link>

          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="rounded-lg p-1.5 text-muted-foreground hover:bg-white/5 hover:text-white transition"
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <nav className="flex-1 space-y-1.5 px-3 py-4 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? "text-white bg-accent/15 border border-accent/30 shadow-[0_0_15px_rgba(109,94,246,0.15)]"
                    : "text-muted-foreground hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon className={`h-4 w-4 shrink-0 ${isActive ? "text-accent" : ""}`} />
                {!collapsed && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer User Profile & System Status */}
        <div className="border-t border-white/5 p-3">
          <div className="flex items-center gap-3 rounded-xl bg-white/[0.03] p-2.5">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent/20 text-accent font-semibold text-xs border border-accent/30">
              P
            </div>
            {!collapsed && (
              <div className="flex flex-col overflow-hidden text-left">
                <span className="text-xs font-semibold text-white truncate">Priya Sharma</span>
                <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Owner · Online
                </span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-[#090B11]">
        {children}
      </main>
    </div>
  );
}
