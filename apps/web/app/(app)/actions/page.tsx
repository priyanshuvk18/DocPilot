"use client";

import React, { useState, useEffect } from "react";
import { Zap, CheckCircle2, XCircle, Clock, Check, X, ShieldAlert } from "lucide-react";
import { fetchActions, confirmAction, rejectAction, AgentAction } from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function ActionsPage() {
  const [actions, setActions] = useState<AgentAction[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    loadActions();
  }, []);

  const loadActions = async () => {
    try {
      const data = await fetchActions();
      setActions(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleConfirm = async (id: string) => {
    setProcessingId(id);
    try {
      const res = await confirmAction(id);
      setActions(actions.map((a) => (a.id === id ? res : a)));
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (id: string) => {
    setProcessingId(id);
    try {
      const res = await rejectAction(id);
      setActions(actions.map((a) => (a.id === id ? res : a)));
    } catch (e) {
      console.error(e);
    } finally {
      setProcessingId(null);
    }
  };

  const filtered = actions.filter((a) => (statusFilter === "all" ? true : a.status === statusFilter));

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-[#090B11] p-8">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Agent Actions Hub</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Human-in-the-loop review queue for autonomous tool executions across your connected apps.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          {["all", "proposed", "succeeded", "rejected"].map((tab) => (
            <button
              key={tab}
              onClick={() => setStatusFilter(tab)}
              className={cn(
                "rounded-xl px-3 py-1.5 font-medium capitalize transition",
                statusFilter === tab
                  ? "bg-accent text-white shadow-[0_0_15px_var(--accent-glow)]"
                  : "bg-[#111420] text-muted-foreground hover:text-white"
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {filtered.length === 0 && (
          <div className="rounded-2xl border border-white/5 bg-[#111420] p-12 text-center max-w-md mx-auto">
            <Zap className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
            <p className="text-sm font-semibold text-white">No actions in this queue</p>
            <p className="text-xs text-muted-foreground mt-1">
              Ask DocPilot in chat to create a task, draft an email, or notify the team.
            </p>
          </div>
        )}

        {filtered.map((act) => {
          const isProposed = act.status === "proposed";
          const isSucceeded = act.status === "succeeded";
          const isRejected = act.status === "rejected";

          return (
            <div
              key={act.id}
              className="rounded-2xl border border-white/5 bg-[#111420] p-6 hover:border-accent/30 transition flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/15 text-accent">
                    <Zap className="h-4 w-4" />
                  </span>
                  <div>
                    <h3 className="font-bold text-sm text-white font-mono">{act.tool}</h3>
                    <span className="text-[11px] text-muted-foreground font-mono">
                      ID: {act.id.slice(0, 8)}...
                    </span>
                  </div>

                  <span
                    className={cn(
                      "rounded-full px-2.5 py-0.5 text-[10px] font-mono uppercase font-semibold ml-2",
                      isSucceeded
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : isRejected
                        ? "bg-red-500/15 text-red-400 border border-red-500/30"
                        : "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30"
                    )}
                  >
                    {act.status}
                  </span>
                </div>

                <div className="rounded-xl bg-black/40 p-3 text-xs font-mono text-gray-300 max-w-2xl overflow-x-auto">
                  {JSON.stringify(act.params, null, 2)}
                </div>

                {act.result && (
                  <div className="text-xs text-emerald-400 font-mono flex items-center gap-1.5 pt-1">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Result: {act.result.message || JSON.stringify(act.result)}
                  </div>
                )}
              </div>

              {isProposed && (
                <div className="flex items-center gap-2 self-end md:self-center">
                  <button
                    onClick={() => handleConfirm(act.id)}
                    disabled={processingId === act.id}
                    className="flex items-center gap-1.5 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white shadow-[0_0_15px_var(--accent-glow)] hover:bg-accent-hover transition disabled:opacity-50"
                  >
                    <Check className="h-3.5 w-3.5" />
                    <span>Confirm</span>
                  </button>
                  <button
                    onClick={() => handleReject(act.id)}
                    disabled={processingId === act.id}
                    className="flex items-center gap-1.5 rounded-xl border border-white/10 px-3.5 py-2 text-xs text-gray-400 hover:bg-white/5 transition disabled:opacity-50"
                  >
                    <X className="h-3.5 w-3.5" />
                    <span>Reject</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
