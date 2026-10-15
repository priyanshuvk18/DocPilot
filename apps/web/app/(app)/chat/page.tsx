"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Plus,
  Sparkles,
  FileText,
  Check,
  ThumbsUp,
  ThumbsDown,
  Copy,
  Folder,
  Zap,
  CheckCircle2,
  X,
  ExternalLink,
  ChevronDown,
  Info,
  Clock,
  Filter,
} from "lucide-react";
import {
  fetchThreads,
  createThread,
  fetchThread,
  fetchCollections,
  fetchDocuments,
  streamChatMessage,
  confirmAction,
  rejectAction,
  submitFeedback,
  ThreadItem,
  Collection,
  DocumentItem,
  Citation,
  AgentAction,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function ChatPage() {
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<string | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>("");

  // Slide-out citation viewer
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  // Action status updates
  const [actionProcessing, setActionProcessing] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [thList, colList] = await Promise.all([
        fetchThreads(),
        fetchCollections(),
      ]);
      setThreads(thList);
      setCollections(colList);

      if (thList.length > 0) {
        selectThread(thList[0].id);
      } else {
        const newTh = await createThread("New Conversation");
        setThreads([newTh]);
        selectThread(newTh.id);
      }
    } catch (e) {
      console.error("Failed to load threads/collections", e);
    }
  };

  const selectThread = async (id: string) => {
    setActiveThreadId(id);
    try {
      const threadData = await fetchThread(id);
      setMessages(threadData.messages || []);
    } catch (e) {
      console.error("Failed to fetch thread messages", e);
    }
  };

  const handleNewThread = async () => {
    try {
      const newTh = await createThread("New Conversation");
      setThreads([newTh, ...threads]);
      selectThread(newTh.id);
    } catch (e) {
      console.error("Failed to create thread", e);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentStatus]);

  const handleSend = async () => {
    if (!inputQuery.trim() || !activeThreadId || isStreaming) return;

    const userText = inputQuery.trim();
    setInputQuery("");

    // Append user message immediately
    const userMsgObj = {
      id: `usr_${Date.now()}`,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsgObj]);

    // Prepare assistant placeholder
    const asstMsgId = `asst_${Date.now()}`;
    const asstMsgObj = {
      id: asstMsgId,
      role: "assistant",
      content: "",
      citations: [] as Citation[],
      actions: [] as AgentAction[],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, asstMsgObj]);

    setIsStreaming(true);
    setCurrentStatus("Searching documents...");

    await streamChatMessage({
      threadId: activeThreadId,
      content: userText,
      collectionId: selectedCollectionId || undefined,
      onStatus: (st) => setCurrentStatus(st),
      onToken: (tok) => {
        setMessages((prev) =>
          prev.map((m) => (m.id === asstMsgId ? { ...m, content: m.content + tok } : m))
        );
      },
      onCitation: (cit) => {
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === asstMsgId) {
              const existing = m.citations || [];
              if (!existing.some((c: any) => c.marker === cit.marker)) {
                return { ...m, citations: [...existing, cit] };
              }
            }
            return m;
          })
        );
      },
      onActionProposed: (act) => {
        setMessages((prev) =>
          prev.map((m) => {
            if (m.id === asstMsgId) {
              const existing = m.actions || [];
              return { ...m, actions: [...existing, act] };
            }
            return m;
          })
        );
      },
      onDone: () => {
        setIsStreaming(false);
        setCurrentStatus(null);
      },
      onError: (err) => {
        console.error("Stream error", err);
        setIsStreaming(false);
        setCurrentStatus(null);
      },
    });
  };

  const handleConfirmAction = async (actionId: string) => {
    setActionProcessing(actionId);
    try {
      const updated = await confirmAction(actionId);
      setMessages((prev) =>
        prev.map((m) => ({
          ...m,
          actions: m.actions?.map((a: any) => (a.id === actionId ? updated : a)),
        }))
      );
    } catch (e) {
      console.error("Failed to confirm action", e);
    } finally {
      setActionProcessing(null);
    }
  };

  const handleRejectAction = async (actionId: string) => {
    setActionProcessing(actionId);
    try {
      const updated = await rejectAction(actionId);
      setMessages((prev) =>
        prev.map((m) => ({
          ...m,
          actions: m.actions?.map((a: any) => (a.id === actionId ? updated : a)),
        }))
      );
    } catch (e) {
      console.error("Failed to reject action", e);
    } finally {
      setActionProcessing(null);
    }
  };

  const handleFeedback = async (messageId: string, rating: number, reason?: string) => {
    try {
      await submitFeedback(messageId, rating, reason);
      setMessages((prev) =>
        prev.map((m) => (m.id === messageId ? { ...m, feedbackSubmitted: rating } : m))
      );
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden">
      {/* Threads Drawer / List */}
      <div className="w-64 border-r border-white/5 bg-[#0D101A]/60 flex flex-col shrink-0">
        <div className="p-3 border-b border-white/5">
          <button
            onClick={handleNewThread}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-accent/20 border border-accent/40 py-2.5 text-xs font-semibold text-accent-light hover:bg-accent/30 transition shadow-[0_0_15px_rgba(109,94,246,0.15)]"
          >
            <Plus className="h-4 w-4" />
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {threads.map((th) => (
            <button
              key={th.id}
              onClick={() => selectThread(th.id)}
              className={cn(
                "w-full text-left rounded-xl px-3 py-2 text-xs font-medium transition truncate flex items-center justify-between",
                activeThreadId === th.id
                  ? "bg-white/10 text-white border border-white/10"
                  : "text-muted-foreground hover:bg-white/5 hover:text-white"
              )}
            >
              <span className="truncate">{th.title || "Untitled Thread"}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Chat Conversation View */}
      <div className="flex-1 flex flex-col h-full bg-[#090B11] relative">
        {/* Top Header & Collection Filter */}
        <div className="h-14 border-b border-white/5 px-6 flex items-center justify-between shrink-0 bg-[#090B11]/80 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-white">
              {threads.find((t) => t.id === activeThreadId)?.title || "Chat"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-muted-foreground" />
            <select
              value={selectedCollectionId}
              onChange={(e) => setSelectedCollectionId(e.target.value)}
              className="rounded-lg border border-white/10 bg-black/40 px-2.5 py-1 text-xs text-gray-200 focus:border-accent focus:outline-none"
            >
              <option value="">All Collections & Docs</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/20 text-accent mb-4 border border-accent/30 shadow-[0_0_20px_var(--accent-glow)]">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-1">DocPilot Assistant</h3>
              <p className="text-xs text-muted-foreground mb-6">
                Ask questions about your uploaded contracts, SOPs, and reports. Answers are verified with exact citations.
              </p>

              <div className="w-full space-y-2 text-xs">
                <button
                  onClick={() => {
                    setInputQuery("What is the termination notice period in the vendor agreement?");
                  }}
                  className="w-full text-left rounded-xl border border-white/5 bg-white/[0.02] p-3 hover:border-accent/40 hover:bg-white/5 transition text-gray-300"
                >
                  "What is the termination notice period in the vendor agreement?"
                </button>
                <button
                  onClick={() => {
                    setInputQuery("What are the invoice payment terms and late fee policies?");
                  }}
                  className="w-full text-left rounded-xl border border-white/5 bg-white/[0.02] p-3 hover:border-accent/40 hover:bg-white/5 transition text-gray-300"
                >
                  "What are the invoice payment terms and late fee policies?"
                </button>
                <button
                  onClick={() => {
                    setInputQuery("Create a task to renew the vendor contract before notice period.");
                  }}
                  className="w-full text-left rounded-xl border border-white/5 bg-white/[0.02] p-3 hover:border-accent/40 hover:bg-white/5 transition text-gray-300"
                >
                  "Create a task to renew the vendor contract before notice period."
                </button>
              </div>
            </div>
          )}

          {messages.map((m) => {
            const isUser = m.role === "user";

            return (
              <div
                key={m.id}
                className={cn(
                  "flex gap-4 max-w-3xl",
                  isUser ? "ml-auto flex-row-reverse" : "mr-auto"
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-semibold",
                    isUser
                      ? "bg-accent/20 text-accent border border-accent/30"
                      : "bg-white/10 text-white border border-white/10"
                  )}
                >
                  {isUser ? "You" : <Sparkles className="h-4 w-4 text-accent" />}
                </div>

                {/* Message Bubble & Content */}
                <div
                  className={cn(
                    "rounded-2xl p-4 text-sm leading-relaxed",
                    isUser
                      ? "bg-accent text-white shadow-[0_0_20px_var(--accent-glow)]"
                      : "bg-[#111420] border border-white/5 text-gray-200 shadow-md"
                  )}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>

                  {/* Render Inline Citation Chips */}
                  {!isUser && m.citations && m.citations.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/5 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
                        Sources:
                      </span>
                      {m.citations.map((c: Citation) => (
                        <button
                          key={c.marker}
                          onClick={() => setActiveCitation(c)}
                          className="inline-flex items-center gap-1 rounded-lg border border-accent/40 bg-accent/15 px-2 py-0.5 text-xs font-mono font-medium text-accent-light hover:bg-accent/25 transition"
                        >
                          <span>[{c.marker}]</span>
                          <span className="text-[11px] font-sans truncate max-w-[130px]">
                            {c.doc || "Document"}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Render Agent Action Card if proposed */}
                  {!isUser && m.actions && m.actions.length > 0 && (
                    <div className="mt-4 space-y-2">
                      {m.actions.map((act: AgentAction) => (
                        <div
                          key={act.id}
                          className="rounded-xl border border-accent/30 bg-accent/[0.04] p-3 text-xs"
                        >
                          <div className="flex items-center justify-between font-semibold text-white mb-1.5">
                            <span className="flex items-center gap-1.5 text-accent">
                              <Zap className="h-3.5 w-3.5" />
                              Action Proposed: {act.tool}
                            </span>
                            <span
                              className={cn(
                                "rounded px-2 py-0.5 text-[10px] uppercase font-mono",
                                act.status === "succeeded"
                                  ? "bg-emerald-500/20 text-emerald-300"
                                  : act.status === "rejected"
                                  ? "bg-red-500/20 text-red-300"
                                  : "bg-yellow-500/20 text-yellow-300"
                              )}
                            >
                              {act.status}
                            </span>
                          </div>

                          <div className="rounded-lg bg-black/40 p-2 text-gray-300 font-mono text-[11px] mb-2.5">
                            {JSON.stringify(act.params, null, 2)}
                          </div>

                          {act.status === "proposed" && (
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleConfirmAction(act.id)}
                                disabled={actionProcessing === act.id}
                                className="flex items-center gap-1 rounded-lg bg-accent px-3 py-1.5 text-xs font-semibold text-white hover:bg-accent-hover transition shadow-[0_0_15px_var(--accent-glow)] disabled:opacity-50"
                              >
                                <Check className="h-3.5 w-3.5" />
                                <span>Confirm Action</span>
                              </button>
                              <button
                                onClick={() => handleRejectAction(act.id)}
                                disabled={actionProcessing === act.id}
                                className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-gray-400 hover:bg-white/5 transition"
                              >
                                Reject
                              </button>
                            </div>
                          )}

                          {act.status === "succeeded" && act.result && (
                            <div className="text-emerald-400 text-[11px] flex items-center gap-1">
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              {act.result.message || "Executed successfully."}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Feedback bar */}
                  {!isUser && (
                    <div className="mt-3 flex items-center justify-between pt-2 text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleFeedback(m.id, 1)}
                          className={cn(
                            "rounded p-1 hover:text-white transition",
                            m.feedbackSubmitted === 1 ? "text-emerald-400" : ""
                          )}
                          title="Helpful"
                        >
                          <ThumbsUp className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleFeedback(m.id, -1, "Inaccurate or ungrounded")}
                          className={cn(
                            "rounded p-1 hover:text-white transition",
                            m.feedbackSubmitted === -1 ? "text-red-400" : ""
                          )}
                          title="Not helpful"
                        >
                          <ThumbsDown className="h-3.5 w-3.5" />
                        </button>
                      </div>

                      <button
                        onClick={() => navigator.clipboard.writeText(m.content)}
                        className="flex items-center gap-1 text-[11px] hover:text-white transition"
                      >
                        <Copy className="h-3 w-3" />
                        <span>Copy</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* AI Thinking Status Indicator */}
          {currentStatus && (
            <div className="flex items-center gap-2 text-xs text-accent-light animate-pulse ml-12">
              <Sparkles className="h-3.5 w-3.5 text-accent animate-spin" />
              <span>{currentStatus}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Composer */}
        <div className="p-4 border-t border-white/5 bg-[#090B11]/90">
          <div className="max-w-3xl mx-auto flex items-end gap-2 rounded-2xl border border-white/10 bg-[#111420] p-2 focus-within:border-accent shadow-lg transition">
            <textarea
              rows={1}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask anything about your documents, policies, or create an agent task..."
              className="flex-1 max-h-32 resize-none bg-transparent px-3 py-2 text-sm text-white placeholder-muted-foreground focus:outline-none"
            />
            <button
              onClick={handleSend}
              disabled={!inputQuery.trim() || isStreaming}
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent text-white shadow-[0_0_15px_var(--accent-glow)] transition hover:bg-accent-hover disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Slide-Out Citation Inspector Panel */}
      <AnimatePresence>
        {activeCitation && (
          <motion.div
            initial={{ x: 300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 300, opacity: 0 }}
            className="w-80 border-l border-white/5 bg-[#0D101A] p-5 shrink-0 flex flex-col shadow-2xl z-20"
          >
            <div className="flex items-center justify-between border-b border-white/5 pb-3">
              <div className="flex items-center gap-2">
                <span className="rounded bg-accent/20 px-2 py-0.5 text-xs font-mono font-bold text-accent-light">
                  [{activeCitation.marker}]
                </span>
                <span className="text-xs font-bold text-white">Source Passage</span>
              </div>
              <button
                onClick={() => setActiveCitation(null)}
                className="text-muted-foreground hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-4 space-y-3 flex-1 overflow-y-auto">
              <div>
                <span className="text-[11px] text-muted-foreground uppercase font-semibold">Document:</span>
                <div className="text-xs font-medium text-white mt-0.5 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-accent" />
                  {activeCitation.doc || "Document"}
                </div>
              </div>

              {activeCitation.page && (
                <div>
                  <span className="text-[11px] text-muted-foreground uppercase font-semibold">Page:</span>
                  <div className="text-xs font-medium text-white mt-0.5">{activeCitation.page}</div>
                </div>
              )}

              <div>
                <span className="text-[11px] text-muted-foreground uppercase font-semibold">Verified Quote:</span>
                <div className="mt-1 rounded-xl border border-white/5 bg-black/40 p-3 text-xs leading-relaxed text-gray-200 italic border-l-2 border-l-accent">
                  "{activeCitation.quote}"
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
