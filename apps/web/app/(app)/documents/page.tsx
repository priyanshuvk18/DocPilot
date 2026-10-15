"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Trash2,
  Folder,
  Layers,
  ChevronRight,
  X,
  FileUp,
} from "lucide-react";
import {
  fetchDocuments,
  uploadDocument,
  reindexDocument,
  deleteDocument,
  fetchDocumentChunks,
  fetchCollections,
  DocumentItem,
  ChunkItem,
  Collection,
} from "@/lib/api-client";
import { cn } from "@/lib/utils";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // Chunks inspector
  const [inspectingDoc, setInspectingDoc] = useState<DocumentItem | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [loadingChunks, setLoadingChunks] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadData();
  }, [selectedCollection]);

  const loadData = async () => {
    try {
      const [docs, cols] = await Promise.all([
        fetchDocuments(selectedCollection || undefined),
        fetchCollections(),
      ]);
      setDocuments(docs);
      setCollections(cols);
    } catch (e) {
      console.error("Failed to load documents", e);
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setUploading(true);

    try {
      for (let i = 0; i < files.length; i++) {
        await uploadDocument(files[i], selectedCollection || undefined);
      }
      await loadData();
    } catch (e) {
      console.error("Upload failed", e);
    } finally {
      setUploading(false);
    }
  };

  const handleInspect = async (doc: DocumentItem) => {
    setInspectingDoc(doc);
    setLoadingChunks(true);
    try {
      const c = await fetchDocumentChunks(doc.id);
      setChunks(c);
    } catch (e) {
      console.error("Failed to load chunks", e);
    } finally {
      setLoadingChunks(false);
    }
  };

  const handleReindex = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await reindexDocument(docId);
      await loadData();
    } catch (err) {
      console.error("Reindex failed", err);
    }
  };

  const handleDelete = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this document and all its indexed chunks?")) return;
    try {
      await deleteDocument(docId);
      setDocuments(documents.filter((d) => d.id !== docId));
      if (inspectingDoc?.id === docId) {
        setInspectingDoc(null);
      }
    } catch (err) {
      console.error("Delete failed", err);
    }
  };

  return (
    <div className="flex h-full w-full overflow-hidden bg-[#090B11]">
      <div className="flex-1 flex flex-col h-full overflow-y-auto p-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Documents</h1>
            <p className="text-xs text-muted-foreground mt-1">
              Upload PDF, DOCX, TXT, or MD documents. Chunks are automatically extracted and indexed.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              className="rounded-xl border border-white/10 bg-[#111420] px-3.5 py-2 text-xs text-gray-200 focus:border-accent focus:outline-none"
            >
              <option value="">All Collections</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>

            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white shadow-[0_0_20px_var(--accent-glow)] hover:bg-accent-hover transition disabled:opacity-50"
            >
              <FileUp className="h-4 w-4" />
              <span>{uploading ? "Ingesting..." : "Upload File"}</span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => handleFileUpload(e.target.files)}
              multiple
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
            />
          </div>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            handleFileUpload(e.dataTransfer.files);
          }}
          className={cn(
            "mb-8 flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all",
            dragActive
              ? "border-accent bg-accent/[0.08] scale-[1.01]"
              : "border-white/10 bg-[#111420]/40 hover:border-white/20"
          )}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/15 text-accent mb-3">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-semibold text-white">Drag & drop your files here, or browse</p>
          <p className="text-xs text-muted-foreground mt-1">Supports PDF, DOCX, TXT, MD up to 25 MB</p>
        </div>

        {/* Document Cards List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => {
            const isReady = doc.status === "ready";
            const isFailed = doc.status === "failed";

            return (
              <div
                key={doc.id}
                onClick={() => handleInspect(doc)}
                className="group relative cursor-pointer rounded-2xl border border-white/5 bg-[#111420] p-5 transition hover:border-accent/40 hover:shadow-[0_4px_20px_rgba(109,94,246,0.1)]"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/5 text-accent">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="overflow-hidden">
                      <h3 className="font-semibold text-sm text-white truncate group-hover:text-accent-light transition">
                        {doc.filename}
                      </h3>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {doc.page_count} {doc.page_count === 1 ? "page" : "pages"} · v{doc.version}
                      </p>
                    </div>
                  </div>

                  {/* Status Pill matching UI-UX.md §2.2 */}
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-medium font-mono",
                      isReady
                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                        : isFailed
                        ? "bg-red-500/15 text-red-400 border border-red-500/30"
                        : "bg-yellow-500/15 text-yellow-300 border border-yellow-500/30 animate-pulse"
                    )}
                  >
                    {isReady && <CheckCircle2 className="h-3 w-3" />}
                    {isFailed && <AlertCircle className="h-3 w-3" />}
                    <span className="capitalize">{doc.status}</span>
                  </span>
                </div>

                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="text-[11px] font-mono">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </span>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => handleReindex(doc.id, e)}
                      title="Re-index"
                      className="rounded p-1 hover:text-white hover:bg-white/5 transition"
                    >
                      <RefreshCw className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={(e) => handleDelete(doc.id, e)}
                      title="Delete document"
                      className="rounded p-1 hover:text-red-400 hover:bg-red-500/10 transition"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Slide-out Chunks Inspector */}
      <AnimatePresence>
        {inspectingDoc && (
          <motion.div
            initial={{ x: 380, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 380, opacity: 0 }}
            className="w-96 border-l border-white/5 bg-[#0D101A] p-6 shrink-0 flex flex-col shadow-2xl z-20"
          >
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div>
                <span className="text-xs text-muted-foreground uppercase font-mono">Chunk Inspector</span>
                <h3 className="font-bold text-sm text-white truncate max-w-[220px]">
                  {inspectingDoc.filename}
                </h3>
              </div>
              <button
                onClick={() => setInspectingDoc(null)}
                className="text-muted-foreground hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto mt-4 space-y-3">
              {loadingChunks && <p className="text-xs text-muted-foreground">Loading chunks...</p>}
              {!loadingChunks && chunks.length === 0 && (
                <p className="text-xs text-muted-foreground">No chunks found for this document.</p>
              )}

              {chunks.map((chunk) => (
                <div key={chunk.id} className="rounded-xl border border-white/5 bg-black/40 p-3.5 text-xs">
                  <div className="flex items-center justify-between text-[11px] font-mono text-accent-light mb-1.5">
                    <span>Ordinal #{chunk.ordinal}</span>
                    <span>Page {chunk.page || 1} · {chunk.tokens} tokens</span>
                  </div>
                  {chunk.heading && (
                    <div className="text-xs font-semibold text-white mb-1">{chunk.heading}</div>
                  )}
                  <p className="text-gray-300 leading-relaxed line-clamp-4">{chunk.content}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
