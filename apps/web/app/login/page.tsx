"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, UserCheck, Shield } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handlePersonaSelect = (roleName: string) => {
    // In dev with AUTH_DISABLED=true, simply route to /chat
    router.push("/chat");
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    router.push("/chat");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#090B11] px-4 text-[#F1F3F9]">
      <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111420] p-8 shadow-2xl">
        <div className="text-center mb-8">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-accent text-white shadow-[0_0_20px_var(--accent-glow)] mb-4">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold text-white">Sign in to DocPilot</h1>
          <p className="mt-1.5 text-xs text-muted-foreground">
            AI workspace assistant over your private documents
          </p>
        </div>

        {/* Persona Quick-Login for easy role exploration */}
        <div className="mb-6 rounded-xl border border-accent/20 bg-accent/[0.04] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-accent mb-3">
            <UserCheck className="h-3.5 w-3.5" />
            <span>Select a Demo Persona (1-Click Login):</span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              onClick={() => handlePersonaSelect("Priya")}
              className="flex flex-col text-left rounded-lg border border-white/5 bg-black/40 p-2.5 hover:border-accent hover:bg-accent/10 transition"
            >
              <span className="font-semibold text-white">Priya</span>
              <span className="text-[11px] text-muted-foreground">Operations Lead</span>
            </button>
            <button
              onClick={() => handlePersonaSelect("Arjun")}
              className="flex flex-col text-left rounded-lg border border-white/5 bg-black/40 p-2.5 hover:border-accent hover:bg-accent/10 transition"
            >
              <span className="font-semibold text-white">Arjun</span>
              <span className="text-[11px] text-muted-foreground">Manager (Agent)</span>
            </button>
            <button
              onClick={() => handlePersonaSelect("Meera")}
              className="flex flex-col text-left rounded-lg border border-white/5 bg-black/40 p-2.5 hover:border-accent hover:bg-accent/10 transition"
            >
              <span className="font-semibold text-white">Meera</span>
              <span className="text-[11px] text-muted-foreground">AI Platform Eng</span>
            </button>
            <button
              onClick={() => handlePersonaSelect("Admin")}
              className="flex flex-col text-left rounded-lg border border-white/5 bg-black/40 p-2.5 hover:border-accent hover:bg-accent/10 transition"
            >
              <span className="font-semibold text-white">Admin</span>
              <span className="text-[11px] text-muted-foreground">Workspace Owner</span>
            </button>
          </div>
        </div>

        <div className="relative my-6 text-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/5" />
          </div>
          <span className="relative bg-[#111420] px-3 text-xs text-muted-foreground">or email</span>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="priya@acme.com"
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white placeholder-muted-foreground focus:border-accent focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white placeholder-muted-foreground focus:border-accent focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--accent-glow)] hover:bg-accent-hover transition"
          >
            Sign In
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-muted-foreground">
          Don't have an account?{" "}
          <Link href="/signup" className="text-accent hover:underline">
            Create workspace
          </Link>
        </div>
      </div>
    </div>
  );
}
