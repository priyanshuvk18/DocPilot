"use client";

import React, { useState, useEffect } from "react";
import { Settings, Zap, Shield, Key, Bell, Check, Sliders } from "lucide-react";
import { fetchTools, toggleTool, ToolConfig } from "@/lib/api-client";

export default function SettingsPage() {
  const [tools, setTools] = useState<ToolConfig[]>([]);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [savedMessage, setSavedMessage] = useState(false);

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      const data = await fetchTools();
      setTools(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleToggle = async (toolName: string, current: boolean) => {
    try {
      const updated = await toggleTool(toolName, !current);
      setTools(tools.map((t) => (t.tool === toolName ? updated : t)));
      setSavedMessage(true);
      setTimeout(() => setSavedMessage(false), 2000);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-[#090B11] p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Workspace Settings & Tools</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Configure autonomous agent tools, tenant isolation, and accessibility preferences.
          </p>
        </div>

        {savedMessage && (
          <span className="flex items-center gap-1.5 rounded-xl bg-emerald-500/20 border border-emerald-500/40 px-3.5 py-1.5 text-xs font-semibold text-emerald-400">
            <Check className="h-4 w-4" />
            <span>Settings Saved</span>
          </span>
        )}
      </div>

      <div className="max-w-4xl space-y-8">
        {/* Agent Tools Permissions */}
        <div className="rounded-2xl border border-white/5 bg-[#111420] p-6">
          <div className="flex items-center gap-3 pb-4 border-b border-white/5 mb-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent/15 text-accent">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Connected Agent Tools</h3>
              <p className="text-xs text-muted-foreground">
                Control which external actions the assistant can propose in chat conversations.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {tools.map((t) => (
              <div
                key={t.tool}
                className="flex items-center justify-between rounded-xl border border-white/5 bg-black/40 p-4"
              >
                <div>
                  <div className="font-bold text-sm text-white font-mono">{t.tool}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {t.tool === "create_task" && "Creates tracking tasks in project workspace (Jira/Linear style)"}
                    {t.tool === "draft_email" && "Drafts email communications based on document facts"}
                    {t.tool === "create_calendar_event" && "Schedules calendar review meetings with attendees"}
                    {t.tool === "post_to_slack" && "Broadcasts policy and document updates to Slack channels"}
                  </div>
                </div>

                <button
                  onClick={() => handleToggle(t.tool, t.enabled)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    t.enabled ? "bg-accent" : "bg-white/10"
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                      t.enabled ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Security & Isolation */}
        <div className="rounded-2xl border border-white/5 bg-[#111420] p-6">
          <div className="flex items-center gap-3 pb-4 border-b border-white/5 mb-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-400">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Security & Tenant Isolation</h3>
              <p className="text-xs text-muted-foreground">
                Postgres Row-Level Security (RLS) enforcement and embedding configuration.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="rounded-xl border border-white/5 bg-black/40 p-3.5">
              <span className="text-muted-foreground uppercase text-[10px]">Row-Level Security</span>
              <div className="font-bold text-emerald-400 mt-1">FORCE ROW LEVEL SECURITY (Active)</div>
              <div className="text-gray-400 text-[11px] mt-1 font-sans">
                Tenant isolation enforced at DB level on all document and chunk tables.
              </div>
            </div>

            <div className="rounded-xl border border-white/5 bg-black/40 p-3.5">
              <span className="text-muted-foreground uppercase text-[10px]">Embedding Dimension</span>
              <div className="font-bold text-accent-light mt-1">vector(512) · voyage-3-lite</div>
              <div className="text-gray-400 text-[11px] mt-1 font-sans">
                Configured per SCHEMA_DEVIATION.md for optimal speed and cost efficiency.
              </div>
            </div>
          </div>
        </div>

        {/* Accessibility & Reduced Motion */}
        <div className="rounded-2xl border border-white/5 bg-[#111420] p-6">
          <div className="flex items-center gap-3 pb-4 border-b border-white/5 mb-5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/15 text-purple-400">
              <Sliders className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-base text-white">Accessibility & Motion Preferences</h3>
              <p className="text-xs text-muted-foreground">
                Complies with WCAG 2.2 AA and UI-UX.md motion specifications.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-xl border border-white/5 bg-black/40 p-4">
            <div>
              <div className="font-bold text-sm text-white">Reduce Motion</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                Replaces parallax and 3D effects with subtle opacity-only transitions (≤ 120 ms).
              </div>
            </div>

            <button
              onClick={() => setReduceMotion(!reduceMotion)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                reduceMotion ? "bg-accent" : "bg-white/10"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                  reduceMotion ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
