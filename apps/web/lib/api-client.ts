/**
 * Typed client for DocPilot FastAPI backend.
 * Uses NEXT_PUBLIC_API_BASE_URL or defaults to http://localhost:8000.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export interface Workspace {
  id: string;
  name: string;
  created_at: string;
}

export interface Collection {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  workspace_id: string;
  collection_id?: string;
  filename: string;
  storage_path: string;
  status: "queued" | "parsing" | "embedding" | "ready" | "failed";
  error?: string;
  page_count: number;
  version: number;
  created_at: string;
}

export interface ChunkItem {
  id: string;
  ordinal: number;
  page?: number;
  heading?: string;
  content: string;
  tokens: number;
}

export interface Citation {
  marker: number;
  chunk_id?: string;
  doc?: string;
  page?: number;
  quote: string;
}

export interface AgentAction {
  id: string;
  tool: string;
  params: Record<string, any>;
  status: "proposed" | "confirmed" | "rejected" | "succeeded" | "failed";
  result?: Record<string, any>;
  created_at?: string;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  model?: string;
  created_at: string;
  citations?: Citation[];
  actions?: AgentAction[];
}

export interface ThreadItem {
  id: string;
  workspace_id: string;
  user_id: string;
  title: string;
  created_at: string;
  messages?: MessageItem[];
}

export interface EvalRun {
  id: string;
  eval_set_id: string;
  config: Record<string, any>;
  started_at: string;
  finished_at?: string;
  summary?: {
    cases_count: number;
    mean_faithfulness: number;
    mean_relevance: number;
    mean_ctx_precision: number;
    mean_ctx_recall: number;
    citation_validity_rate: number;
    status: string;
  };
  results?: Array<{
    case_id: string;
    answer: string;
    faithfulness: number;
    relevance: number;
    ctx_precision: number;
    ctx_recall: number;
    citation_valid: boolean;
  }>;
}

export interface EvalSet {
  id: string;
  name: string;
  created_at: string;
  cases: Array<{
    id: string;
    question: string;
    reference_answer?: string;
  }>;
  runs: EvalRun[];
}

export interface UsageAnalytics {
  total_requests: number;
  total_tokens: number;
  total_cost_usd: number;
  avg_ttft_ms: number;
  p95_ttft_ms: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  daily_volume: Array<{ date: string; queries: number; cost: number }>;
}

export interface QualityAnalytics {
  positive_feedback_count: number;
  negative_feedback_count: number;
  satisfaction_rate_percent: number;
  citation_coverage_rate: number;
  avg_faithfulness_score: number;
  avg_relevance_score: number;
  guardrail_blocks_count: number;
}

export interface ToolConfig {
  workspace_id: string;
  tool: string;
  enabled: boolean;
  scopes?: Record<string, any>;
}

// ─── Client Methods ──────────────────────────────────────────────────────────

export async function fetchWorkspace(): Promise<Workspace> {
  const res = await fetch(`${API_BASE}/v1/workspaces/me`);
  if (!res.ok) throw new Error("Failed to fetch workspace");
  return res.json();
}

export async function fetchCollections(): Promise<Collection[]> {
  const res = await fetch(`${API_BASE}/v1/collections`);
  if (!res.ok) throw new Error("Failed to fetch collections");
  return res.json();
}

export async function createCollection(name: string, description?: string): Promise<Collection> {
  const res = await fetch(`${API_BASE}/v1/collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description }),
  });
  if (!res.ok) throw new Error("Failed to create collection");
  return res.json();
}

export async function fetchDocuments(collectionId?: string): Promise<DocumentItem[]> {
  const url = collectionId
    ? `${API_BASE}/v1/documents?collection_id=${collectionId}`
    : `${API_BASE}/v1/documents`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function uploadDocument(file: File, collectionId?: string): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);
  if (collectionId) formData.append("collection_id", collectionId);

  const res = await fetch(`${API_BASE}/v1/documents/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to upload document");
  return res.json();
}

export async function fetchDocumentChunks(documentId: string): Promise<ChunkItem[]> {
  const res = await fetch(`${API_BASE}/v1/documents/${documentId}/chunks`);
  if (!res.ok) throw new Error("Failed to fetch chunks");
  return res.json();
}

export async function reindexDocument(documentId: string): Promise<DocumentItem> {
  const res = await fetch(`${API_BASE}/v1/documents/${documentId}/reindex`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to reindex document");
  return res.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/documents/${documentId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete document");
}

export async function fetchThreads(): Promise<ThreadItem[]> {
  const res = await fetch(`${API_BASE}/v1/chat/threads`);
  if (!res.ok) throw new Error("Failed to fetch threads");
  return res.json();
}

export async function createThread(title?: string): Promise<ThreadItem> {
  const res = await fetch(`${API_BASE}/v1/chat/threads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create thread");
  return res.json();
}

export async function fetchThread(threadId: string): Promise<ThreadItem> {
  const res = await fetch(`${API_BASE}/v1/chat/threads/${threadId}`);
  if (!res.ok) throw new Error("Failed to fetch thread");
  return res.json();
}

export async function deleteThread(threadId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/chat/threads/${threadId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete thread");
}

export async function fetchActions(): Promise<AgentAction[]> {
  const res = await fetch(`${API_BASE}/v1/actions`);
  if (!res.ok) throw new Error("Failed to fetch actions");
  return res.json();
}

export async function confirmAction(actionId: string): Promise<AgentAction> {
  const res = await fetch(`${API_BASE}/v1/actions/${actionId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to confirm action");
  return res.json();
}

export async function rejectAction(actionId: string): Promise<AgentAction> {
  const res = await fetch(`${API_BASE}/v1/actions/${actionId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error("Failed to reject action");
  return res.json();
}

export async function submitFeedback(messageId: string, rating: number, reason?: string) {
  const res = await fetch(`${API_BASE}/v1/messages/${messageId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rating, reason }),
  });
  if (!res.ok) throw new Error("Failed to submit feedback");
  return res.json();
}

export async function fetchEvalSets(): Promise<EvalSet[]> {
  const res = await fetch(`${API_BASE}/v1/eval-sets`);
  if (!res.ok) throw new Error("Failed to fetch eval sets");
  return res.json();
}

export async function triggerEvalRun(evalSetId: string): Promise<EvalRun> {
  const res = await fetch(`${API_BASE}/v1/eval-sets/${evalSetId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!res.ok) throw new Error("Failed to trigger eval run");
  return res.json();
}

export async function fetchAnalyticsUsage(): Promise<UsageAnalytics> {
  const res = await fetch(`${API_BASE}/v1/analytics/usage`);
  if (!res.ok) throw new Error("Failed to fetch usage analytics");
  return res.json();
}

export async function fetchAnalyticsQuality(): Promise<QualityAnalytics> {
  const res = await fetch(`${API_BASE}/v1/analytics/quality`);
  if (!res.ok) throw new Error("Failed to fetch quality analytics");
  return res.json();
}

export async function fetchTools(): Promise<ToolConfig[]> {
  const res = await fetch(`${API_BASE}/v1/tools`);
  if (!res.ok) throw new Error("Failed to fetch tools");
  return res.json();
}

export async function toggleTool(toolName: string, enabled: boolean): Promise<ToolConfig> {
  const res = await fetch(`${API_BASE}/v1/tools/${toolName}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!res.ok) throw new Error("Failed to update tool");
  return res.json();
}

// ─── SSE Stream Handler ───────────────────────────────────────────────────────

export async function streamChatMessage({
  threadId,
  content,
  collectionId,
  onStatus,
  onToken,
  onCitation,
  onActionProposed,
  onDone,
  onError,
}: {
  threadId: string;
  content: string;
  collectionId?: string;
  onStatus?: (status: string) => void;
  onToken: (token: string) => void;
  onCitation?: (citation: Citation) => void;
  onActionProposed?: (action: AgentAction) => void;
  onDone?: (info: any) => void;
  onError?: (err: any) => void;
}) {
  try {
    const response = await fetch(`${API_BASE}/v1/chat/threads/${threadId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, collection_id: collectionId }),
    });

    if (!response.ok || !response.body) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/event:\s*([^\n]+)/);
        const dataMatch = block.match(/data:\s*([^\n]+)/);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1].trim();
          try {
            const data = JSON.parse(dataMatch[1].trim());
            if (eventType === "status" && onStatus) {
              onStatus(data.stage || data);
            } else if (eventType === "token") {
              onToken(data.text);
            } else if (eventType === "citation" && onCitation) {
              onCitation(data);
            } else if (eventType === "action_proposed" && onActionProposed) {
              onActionProposed({
                id: data.action_id,
                tool: data.tool,
                params: data.params,
                status: "proposed",
              });
            } else if (eventType === "done" && onDone) {
              onDone(data);
            }
          } catch (e) {
            console.error("Error parsing SSE block", e);
          }
        }
      }
    }
  } catch (err) {
    if (onError) onError(err);
    else console.error(err);
  }
}
