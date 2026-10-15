"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  FileText,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Search,
  Zap,
  Activity,
  Layers,
  Check,
  Lock,
  ChevronRight,
  Sliders,
  Send,
  ExternalLink,
} from "lucide-react";

export default function MarketingPage() {
  const [activeTab, setActiveTab] = useState<"rag" | "agent" | "evals" | "security">("rag");
  const [demoQuery, setDemoQuery] = useState("What is the notice period for contract termination?");
  const [demoResponse, setDemoResponse] = useState<string | null>(null);
  const [demoStreaming, setDemoStreaming] = useState(false);

  const runDemo = () => {
    setDemoStreaming(true);
    setDemoResponse("");
    const fullText =
      "Based on the vendor agreement, either party may terminate the contract with a written notice period of 60 days [1]. In case of a material breach, a written notice specifying the breach must be provided, allowing a 15-day cure period before termination takes effect [1].";
    let i = 0;
    const interval = setInterval(() => {
      i += 8;
      if (i >= fullText.length) {
        setDemoResponse(fullText);
        setDemoStreaming(false);
        clearInterval(interval);
      } else {
        setDemoResponse(fullText.slice(0, i));
      }
    }, 30);
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#090B11] text-[#F1F3F9]">
      {/* Background glowing gradients */}
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[600px] w-[800px] -translate-x-1/2 rounded-full bg-gradient-to-tr from-accent/20 via-purple-600/10 to-transparent blur-[120px]" />
      <div className="pointer-events-none absolute top-[800px] -left-40 h-[500px] w-[500px] rounded-full bg-accent/15 blur-[100px]" />

      {/* Navigation */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#090B11]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-white shadow-[0_0_20px_var(--accent-glow)]">
              <Sparkles className="h-5 w-5" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white">
              Doc<span className="text-accent">Pilot</span>
            </span>
          </div>

          <nav className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex">
            <a href="#features" className="transition hover:text-white">
              Features
            </a>
            <a href="#interactive-demo" className="transition hover:text-white">
              Interactive Demo
            </a>
            <a href="#architecture" className="transition hover:text-white">
              Architecture
            </a>
            <a href="#evals" className="transition hover:text-white">
              Evals & Safety
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition hover:text-white"
            >
              Sign In
            </Link>
            <Link
              href="/chat"
              className="group flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white shadow-[0_0_20px_var(--accent-glow)] transition-all hover:bg-accent-hover hover:scale-[1.02]"
            >
              Open Workspace
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative mx-auto max-w-7xl px-6 pt-20 pb-28 text-center md:pt-32">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-xs font-semibold text-accent-light"
        >
          <Sparkles className="h-3.5 w-3.5 text-accent" />
          <span>Next-Generation Enterprise RAG & Autonomous Agent</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl md:text-7xl"
        >
          Your workspace documents,{" "}
          <span className="bg-gradient-to-r from-accent via-indigo-400 to-purple-300 bg-clip-text text-transparent">
            grounded with verified citations.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground sm:text-xl"
        >
          DocPilot answers questions from your private PDFs, manuals, and policies with exact inline
          citations, executes human-approved agent actions, and proves quality through built-in evals.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-4"
        >
          <Link
            href="/chat"
            className="group flex items-center gap-2.5 rounded-xl bg-accent px-7 py-3.5 text-base font-semibold text-white shadow-[0_0_28px_var(--accent-glow)] transition-all hover:bg-accent-hover hover:scale-[1.02]"
          >
            Launch Assistant
            <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
          </Link>
          <a
            href="#interactive-demo"
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3.5 text-base font-semibold text-white backdrop-blur-sm transition hover:bg-white/10"
          >
            Try Live Demo
          </a>
        </motion.div>

        {/* 3D Stack Motion Preview */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="relative mx-auto mt-16 max-w-5xl rounded-2xl border border-white/10 bg-[#111420]/80 p-4 shadow-2xl backdrop-blur-xl"
        >
          <div className="flex items-center justify-between border-b border-white/5 pb-3 px-2">
            <div className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-red-500/80" />
              <span className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <span className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs font-mono text-muted-foreground">DocPilot Workspace Core</span>
            </div>
            <div className="flex items-center gap-3 text-xs text-muted-foreground font-mono">
              <span className="flex items-center gap-1 text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
                Live Hybrid Index: 512-dim
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 text-left">
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <div className="flex items-center gap-2 text-accent font-semibold text-sm mb-2">
                <FileText className="h-4 w-4" />
                <span>1. Multi-Doc Ingestion</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                PDF, DOCX, TXT parsed with PyMuPDF, chunked with heading awareness, embedded into 512-dim vectors.
              </p>
              <div className="rounded-lg bg-black/40 p-2.5 text-[11px] font-mono text-gray-400 border border-white/5">
                <div className="flex items-center justify-between text-white/90">
                  <span>Vendor_Contract_2026.pdf</span>
                  <span className="text-emerald-400">Ready</span>
                </div>
                <div className="mt-1 text-[10px] text-muted-foreground">3 Pages · 3 Chunks · HNSW Indexed</div>
              </div>
            </div>

            <div className="rounded-xl border border-accent/30 bg-accent/[0.04] p-4 shadow-[0_0_20px_rgba(109,94,246,0.1)]">
              <div className="flex items-center gap-2 text-accent font-semibold text-sm mb-2">
                <Search className="h-4 w-4" />
                <span>2. Hybrid RRF Retrieval</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Reciprocal Rank Fusion merges dense cosine similarity with keyword search before Voyage reranking.
              </p>
              <div className="rounded-lg bg-black/40 p-2.5 text-[11px] font-mono text-gray-400 border border-white/5">
                <div className="text-accent-light">RRF Score: 0.0326 (Rank #1)</div>
                <div className="text-white/80 mt-1 line-clamp-2">
                  "Either party may terminate this agreement with a written notice period of 60 days..."
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
              <div className="flex items-center gap-2 text-accent font-semibold text-sm mb-2">
                <Zap className="h-4 w-4" />
                <span>3. Human-In-Loop Action</span>
              </div>
              <p className="text-xs text-muted-foreground mb-3">
                Actions never run unsupervised. Proposed tool cards require one-click confirm, edit, or reject.
              </p>
              <div className="rounded-lg bg-black/40 p-2.5 text-[11px] border border-white/5">
                <div className="font-semibold text-white">create_task</div>
                <div className="text-muted-foreground mt-0.5">Renew Vendor Agreement (Net 30)</div>
                <div className="mt-2 flex gap-1.5">
                  <span className="rounded bg-accent/30 px-2 py-0.5 text-[10px] text-accent-light">Confirm</span>
                  <span className="rounded bg-white/5 px-2 py-0.5 text-[10px] text-gray-400">Edit</span>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Interactive Demo Section */}
      <section id="interactive-demo" className="mx-auto max-w-7xl px-6 py-20 border-t border-white/5">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Experience Grounded Citations in Action
          </h2>
          <p className="mt-3 text-muted-foreground">
            Test how DocPilot pulls verified snippets from documents and generates answers with clickable source markers.
          </p>
        </div>

        <div className="mx-auto max-w-3xl rounded-2xl border border-white/10 bg-[#111420] p-6 shadow-2xl">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Target Document: Vendor_Contract_Policy_2026.pdf
              </span>
              <span className="inline-flex items-center gap-1.5 text-xs text-accent">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Verified Ingestion
              </span>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={demoQuery}
                onChange={(e) => setDemoQuery(e.target.value)}
                placeholder="Ask about notice periods, payment terms, or SLAs..."
                className="flex-1 rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white placeholder-muted-foreground focus:border-accent focus:outline-none"
              />
              <button
                onClick={runDemo}
                disabled={demoStreaming}
                className="flex items-center gap-2 rounded-xl bg-accent px-5 py-3 text-sm font-semibold text-white transition hover:bg-accent-hover disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
                <span>Ask</span>
              </button>
            </div>

            <div className="flex flex-wrap gap-2 pt-1 text-xs">
              <span className="text-muted-foreground">Try asking:</span>
              <button
                onClick={() => {
                  setDemoQuery("What is the notice period for contract termination?");
                  runDemo();
                }}
                className="rounded-lg bg-white/5 px-2.5 py-1 text-gray-300 hover:bg-white/10 transition"
              >
                "Notice period"
              </button>
              <button
                onClick={() => {
                  setDemoQuery("What are the invoice payment terms and late penalties?");
                  runDemo();
                }}
                className="rounded-lg bg-white/5 px-2.5 py-1 text-gray-300 hover:bg-white/10 transition"
              >
                "Payment terms"
              </button>
              <button
                onClick={() => {
                  setDemoQuery("Create a task to review vendor contract renewal");
                  runDemo();
                }}
                className="rounded-lg bg-white/5 px-2.5 py-1 text-gray-300 hover:bg-white/10 transition"
              >
                "Create a task"
              </button>
            </div>

            {/* Answer Display */}
            {(demoResponse !== null || demoStreaming) && (
              <div className="mt-4 rounded-xl border border-accent/20 bg-accent/[0.03] p-5 text-sm leading-relaxed text-gray-200">
                <div className="flex items-center gap-2 text-xs font-semibold text-accent mb-2">
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>DocPilot Answer</span>
                </div>
                <p>
                  {demoResponse || "Searching documents..."}
                  {demoStreaming && <span className="inline-block h-4 w-1 animate-pulse bg-accent ml-1 align-middle" />}
                </p>

                {demoResponse && (
                  <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5 text-accent-light">
                      <span className="rounded bg-accent/20 px-1.5 py-0.5 font-mono text-[11px]">[1]</span>
                      Vendor_Contract_Policy_2026.pdf (Page 1)
                    </span>
                    <span>100% Grounded</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Feature Pillars */}
      <section id="features" className="mx-auto max-w-7xl px-6 py-20 border-t border-white/5">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Engineered for Grounded Accuracy
          </h2>
          <p className="mt-3 text-muted-foreground">
            The three layers of DocPilot: High-Fidelity RAG, Agentic Execution, and Built-In Quality Evals.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="rounded-2xl border border-white/10 bg-[#111420] p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent/15 text-accent mb-5">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Verified Citations</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Every factual assertion references an exact chunk ID and page number. Hallucinated or forged citations are stripped before reaching the client.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#111420] p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-400 mb-5">
              <Zap className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Agent Action Cards</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Turn answers into tasks, emails, calendar invites, or Slack messages. Human-in-the-loop safeguards require explicit user confirmation.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-[#111420] p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/15 text-purple-400 mb-5">
              <Activity className="h-6 w-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Built-In Evals & Traces</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Measure Faithfulness, Answer Relevance, and Context Precision across golden benchmark sets. Full trace viewer for every query.
            </p>
          </div>
        </div>
      </section>

      {/* Target Personas */}
      <section className="mx-auto max-w-7xl px-6 py-20 border-t border-white/5">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Designed for High-Performing Teams
          </h2>
          <p className="mt-3 text-muted-foreground">
            Explore persona-tailored workflows built right into the platform.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Link
            href="/chat"
            className="group rounded-2xl border border-white/10 bg-[#111420] p-6 transition hover:border-accent hover:shadow-[0_0_25px_rgba(109,94,246,0.15)]"
          >
            <div className="text-xs font-semibold text-accent uppercase tracking-wider mb-2">Primary Persona</div>
            <h4 className="text-lg font-bold text-white group-hover:text-accent-light transition">Priya</h4>
            <div className="text-xs text-muted-foreground mb-3">Operations & Support Lead</div>
            <p className="text-xs text-gray-300">
              Needs fast, trustworthy answers with clickable citations to update SOPs and resolve vendor queries.
            </p>
          </Link>

          <Link
            href="/chat"
            className="group rounded-2xl border border-white/10 bg-[#111420] p-6 transition hover:border-accent hover:shadow-[0_0_25px_rgba(109,94,246,0.15)]"
          >
            <div className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Agent User</div>
            <h4 className="text-lg font-bold text-white group-hover:text-indigo-300 transition">Arjun</h4>
            <div className="text-xs text-muted-foreground mb-3">Founder / Manager</div>
            <p className="text-xs text-gray-300">
              Turns document discoveries into actionable Jira/Linear tasks and email drafts with 1-click approval.
            </p>
          </Link>

          <Link
            href="/evals"
            className="group rounded-2xl border border-white/10 bg-[#111420] p-6 transition hover:border-accent hover:shadow-[0_0_25px_rgba(109,94,246,0.15)]"
          >
            <div className="text-xs font-semibold text-purple-400 uppercase tracking-wider mb-2">Platform Lead</div>
            <h4 className="text-lg font-bold text-white group-hover:text-purple-300 transition">Meera</h4>
            <div className="text-xs text-muted-foreground mb-3">AI / Platform Engineer</div>
            <p className="text-xs text-gray-300">
              Runs golden test benchmarks, inspects retrieval traces, and tracks latency, tokens, and cost.
            </p>
          </Link>

          <Link
            href="/documents"
            className="group rounded-2xl border border-white/10 bg-[#111420] p-6 transition hover:border-accent hover:shadow-[0_0_25px_rgba(109,94,246,0.15)]"
          >
            <div className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Governance</div>
            <h4 className="text-lg font-bold text-white group-hover:text-emerald-300 transition">Admin</h4>
            <div className="text-xs text-muted-foreground mb-3">Security & Compliance</div>
            <p className="text-xs text-gray-300">
              Controls workspace permissions, audit logs, tool configurations, and tenant isolation policies.
            </p>
          </Link>
        </div>
      </section>

      {/* CTA Footer */}
      <footer className="border-t border-white/10 bg-black/60 py-16">
        <div className="mx-auto max-w-7xl px-6 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-white">
              <Sparkles className="h-4 w-4" />
            </div>
            <span className="font-bold text-white">DocPilot</span>
            <span className="text-xs text-muted-foreground">© 2026 DocPilot AI Inc.</span>
          </div>

          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/chat" className="hover:text-white transition">Chat</Link>
            <Link href="/documents" className="hover:text-white transition">Documents</Link>
            <Link href="/actions" className="hover:text-white transition">Actions</Link>
            <Link href="/evals" className="hover:text-white transition">Evals</Link>
            <Link href="/monitoring" className="hover:text-white transition">Monitoring</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
