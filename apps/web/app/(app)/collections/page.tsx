"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { FolderTree, Plus, FileText, ArrowRight, X } from "lucide-react";
import { fetchCollections, createCollection, Collection } from "@/lib/api-client";

export default function CollectionsPage() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    loadCollections();
  }, []);

  const loadCollections = async () => {
    try {
      const data = await fetchCollections();
      setCollections(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await createCollection(name.trim(), description.trim());
      setName("");
      setDescription("");
      setModalOpen(false);
      await loadCollections();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto bg-[#090B11] p-8">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Collections</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Group related documents to scope RAG search queries and assistant access.
          </p>
        </div>

        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-accent px-4 py-2 text-xs font-semibold text-white shadow-[0_0_20px_var(--accent-glow)] hover:bg-accent-hover transition"
        >
          <Plus className="h-4 w-4" />
          <span>New Collection</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {collections.map((col) => (
          <div
            key={col.id}
            className="rounded-2xl border border-white/5 bg-[#111420] p-6 hover:border-accent/40 transition flex flex-col justify-between"
          >
            <div>
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent/15 text-accent mb-4">
                <FolderTree className="h-5 w-5" />
              </div>
              <h3 className="text-lg font-bold text-white mb-1.5">{col.name}</h3>
              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                {col.description || "No description provided."}
              </p>
            </div>

            <div className="mt-6 pt-4 border-t border-white/5 flex items-center justify-between text-xs">
              <span className="text-[11px] text-muted-foreground font-mono">
                {new Date(col.created_at).toLocaleDateString()}
              </span>
              <Link
                href={`/documents?collection_id=${col.id}`}
                className="flex items-center gap-1 font-semibold text-accent hover:text-accent-light transition"
              >
                <span>View Documents</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Create Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl border border-white/10 bg-[#111420] p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-white/5 mb-4">
              <h3 className="text-base font-bold text-white">Create New Collection</h3>
              <button onClick={() => setModalOpen(false)} className="text-gray-400 hover:text-white">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium text-gray-300 mb-1">Collection Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Legal & Compliance Policies"
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-medium text-gray-300 mb-1">Description (Optional)</label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What documents belong to this group?"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3.5 py-2.5 text-sm text-white focus:border-accent focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-xl border border-white/10 px-4 py-2 text-gray-400 hover:bg-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-accent px-4 py-2 font-semibold text-white shadow-[0_0_15px_var(--accent-glow)] hover:bg-accent-hover"
                >
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
