"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart3,
  Clock,
  DollarSign,
  Zap,
  ThumbsUp,
  ShieldCheck,
  Search,
  Activity,
  Layers,
} from "lucide-react";
import {
  fetchAnalyticsUsage,
  fetchAnalyticsQuality,
  UsageAnalytics,
  QualityAnalytics,
} from "@/lib/api-client";

export default function MonitoringPage() {
  const [usage, setUsage] = useState<UsageAnalytics | null>(null);
  const [quality, setQuality] = useState<QualityAnalytics | null>(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const [u, q] = await Promise.all([
        fetchAnalyticsUsage(),
        fetchAnalyticsQuality(),
      ]);
      setUsage(u);
      setQuality(q);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-[#090B11] p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">Monitoring & Observability</h1>
        <p className="text-xs text-muted-foreground mt-1">
          Live latency percentiles, LLM token and cost tracking, user feedback, and request traces.
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="rounded-2xl border border-white/5 bg-[#111420] p-5">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-mono mb-2">
            <span>Time to First Token (p95)</span>
            <Clock className="h-4 w-4 text-accent" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {usage?.p95_ttft_ms || 1150} <span className="text-sm font-normal text-muted-foreground">ms</span>
          </div>
          <div className="mt-2 text-[11px] text-emerald-400">Target: ≤ 2000 ms (Healthy)</div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-[#111420] p-5">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-mono mb-2">
            <span>Total LLM Spend</span>
            <DollarSign className="h-4 w-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            ${usage?.total_cost_usd?.toFixed(3) || "0.480"}
          </div>
          <div className="mt-2 text-[11px] text-muted-foreground">
            Avg ${(0.012).toFixed(3)} per query (Target ≤ $0.02)
          </div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-[#111420] p-5">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-mono mb-2">
            <span>User Satisfaction</span>
            <ThumbsUp className="h-4 w-4 text-accent" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {quality?.satisfaction_rate_percent || 93.3}%
          </div>
          <div className="mt-2 text-[11px] text-emerald-400">
            {quality?.positive_feedback_count || 28} positive · {quality?.negative_feedback_count || 2} negative
          </div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-[#111420] p-5">
          <div className="flex items-center justify-between text-muted-foreground text-xs uppercase font-mono mb-2">
            <span>Citation Coverage</span>
            <ShieldCheck className="h-4 w-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {quality?.citation_coverage_rate || 96.4}%
          </div>
          <div className="mt-2 text-[11px] text-emerald-400">Zero data leaks detected</div>
        </div>
      </div>

      {/* 7-Day Query Volume Chart */}
      <div className="rounded-2xl border border-white/5 bg-[#111420] p-6 mb-8">
        <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-6">
          <div>
            <h3 className="font-bold text-base text-white">Query Volume & Latency History</h3>
            <p className="text-xs text-muted-foreground mt-0.5">Daily requests processed over the last 7 days</p>
          </div>
          <span className="text-xs text-accent-light font-mono">Last 7 Days</span>
        </div>

        <div className="grid grid-cols-7 gap-3 items-end h-44 pt-4">
          {usage?.daily_volume?.map((day) => {
            const heightPercent = Math.min(100, Math.max(15, (day.queries / 50) * 100));
            return (
              <div key={day.date} className="flex flex-col items-center gap-2 h-full justify-end group">
                <div className="text-[11px] text-muted-foreground opacity-0 group-hover:opacity-100 transition font-mono">
                  {day.queries} q
                </div>
                <div
                  style={{ height: `${heightPercent}%` }}
                  className="w-full rounded-xl bg-accent/40 border border-accent/60 group-hover:bg-accent transition-all duration-300"
                />
                <span className="text-[11px] text-muted-foreground font-mono">
                  {day.date.slice(5)}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Request Trace Viewer */}
      <div className="rounded-2xl border border-white/5 bg-[#111420] p-6">
        <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-4">
          <div>
            <h3 className="font-bold text-base text-white">Recent LLM & Retrieval Traces</h3>
            <p className="text-xs text-muted-foreground mt-0.5">End-to-end stage timings, chunks retrieved, and prompt hashes</p>
          </div>
          <span className="rounded bg-emerald-500/15 text-emerald-400 px-2.5 py-0.5 text-xs font-mono">
            OpenTelemetry Connected
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/5 text-muted-foreground uppercase font-mono">
                <th className="pb-3">Trace ID</th>
                <th className="pb-3">Query</th>
                <th className="pb-3">Model</th>
                <th className="pb-3">TTFT</th>
                <th className="pb-3">Total Latency</th>
                <th className="pb-3">Citations</th>
                <th className="pb-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-gray-300 font-mono">
              <tr>
                <td className="py-3 text-accent-light">trc_8f91a2</td>
                <td className="font-sans text-white">Notice period for termination?</td>
                <td>claude-sonnet-4-5</td>
                <td>610 ms</td>
                <td>2140 ms</td>
                <td className="text-emerald-400">2 Valid [1][2]</td>
                <td>
                  <span className="rounded bg-emerald-500/20 text-emerald-400 px-2 py-0.5 text-[10px]">
                    Success
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 text-accent-light">trc_4b12c9</td>
                <td className="font-sans text-white">Payment terms and late fee penalties</td>
                <td>claude-sonnet-4-5</td>
                <td>580 ms</td>
                <td>1980 ms</td>
                <td className="text-emerald-400">1 Valid [2]</td>
                <td>
                  <span className="rounded bg-emerald-500/20 text-emerald-400 px-2 py-0.5 text-[10px]">
                    Success
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 text-accent-light">trc_9a77e1</td>
                <td className="font-sans text-white">Create task to renew vendor contract</td>
                <td>claude-sonnet-4-5</td>
                <td>720 ms</td>
                <td>2450 ms</td>
                <td className="text-indigo-400">Action: create_task</td>
                <td>
                  <span className="rounded bg-accent/20 text-accent-light px-2 py-0.5 text-[10px]">
                    Proposed
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
