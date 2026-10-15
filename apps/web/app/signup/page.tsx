"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Sparkles } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [workspaceName, setWorkspaceName] = useState("Acme Workspace");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
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
          <h1 className="text-2xl font-bold text-white">Create your Workspace</h1>
          <p className="mt-1.5 text-xs text-muted-foreground">
            Get started with grounded AI document search and agent actions
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Workspace Name</label>
            <input
              type="text"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              required
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white focus:border-accent focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Work Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="lead@company.com"
              required
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white focus:border-accent focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white focus:border-accent focus:outline-none"
            />
          </div>

          <button
            type="submit"
            className="w-full rounded-xl bg-accent py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_var(--accent-glow)] hover:bg-accent-hover transition"
          >
            Create Workspace
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-muted-foreground">
          Already have a workspace?{" "}
          <Link href="/login" className="text-accent hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
