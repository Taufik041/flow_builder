"use client";

import { useState } from "react";
import { Trash2, Plus, LogOut, MessageSquare, Pencil, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Session } from "@/services/api";

interface Props {
  sessions: Session[];
  activeSessionId: string | null;
  onSelect: (id: string) => void;
  onCreate: () => void;
  onRename: (id: string, title: string) => Promise<void>;
  onDelete: (id: string) => void;
  onLogout: () => void;
}

function FlowBadge({ status }: { status?: string | null }) {
  if (!status) return null;
  const published = status === "published";
  return (
    <span
      className={cn(
        "text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0 font-medium",
        published
          ? "bg-[#25D366]/20 text-[#25D366]"
          : "bg-zinc-700 text-zinc-400"
      )}
    >
      {published ? "pub" : "draft"}
    </span>
  );
}

function SessionItem({
  session,
  active,
  onSelect,
  onRename,
  onDelete,
}: {
  session: Session;
  active: boolean;
  onSelect: () => void;
  onRename: (title: string) => Promise<void>;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(session.title);
  const [saving, setSaving] = useState(false);

  async function commitRename() {
    const trimmed = draft.trim();
    if (!trimmed || trimmed === session.title) {
      setEditing(false);
      setDraft(session.title);
      return;
    }
    setSaving(true);
    try {
      await onRename(trimmed);
    } finally {
      setSaving(false);
      setEditing(false);
    }
  }

  function cancelRename() {
    setEditing(false);
    setDraft(session.title);
  }

  if (editing) {
    return (
      <div
        className={cn(
          "flex items-center gap-1 px-3 py-2 mx-2 rounded-lg",
          active ? "bg-zinc-700" : "bg-zinc-800"
        )}
      >
        <input
          autoFocus
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") commitRename();
            if (e.key === "Escape") cancelRename();
          }}
          onBlur={commitRename}
          disabled={saving}
          className="flex-1 bg-transparent text-xs text-zinc-100 focus:outline-none min-w-0"
        />
        <button
          onMouseDown={(e) => e.preventDefault()}
          onClick={commitRename}
          className="p-0.5 text-[#25D366] hover:text-[#1ea952] flex-shrink-0"
        >
          <Check className="w-3 h-3" />
        </button>
        <button
          onMouseDown={(e) => e.preventDefault()}
          onClick={cancelRename}
          className="p-0.5 text-zinc-500 hover:text-zinc-300 flex-shrink-0"
        >
          <X className="w-3 h-3" />
        </button>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group flex items-center gap-2 px-3 py-2 mx-2 rounded-lg cursor-pointer transition-colors",
        active
          ? "bg-zinc-700 text-zinc-100"
          : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
      )}
      onClick={onSelect}
    >
      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
      <span className="flex-1 text-xs truncate min-w-0">{session.title}</span>
      <FlowBadge status={session.flow_status} />
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setDraft(session.title);
            setEditing(true);
          }}
          className="p-0.5 text-zinc-500 hover:text-zinc-300"
          title="Rename"
        >
          <Pencil className="w-3 h-3" />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            if (confirm(`Delete "${session.title}"?`)) onDelete();
          }}
          className="p-0.5 text-zinc-500 hover:text-red-400"
          title="Delete"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
  );
}

export function SessionSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
  onRename,
  onDelete,
  onLogout,
}: Props) {
  return (
    <aside className="w-64 flex-shrink-0 border-r border-zinc-800 flex flex-col bg-zinc-900 h-full">
      <div className="px-4 py-4 border-b border-zinc-800">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-2 h-2 rounded-full bg-[#25D366]" />
          <span className="text-sm font-semibold text-zinc-100">WA Flow</span>
        </div>
        <button
          onClick={onCreate}
          className="w-full flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-lg px-3 py-2 text-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          New session
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {sessions.length === 0 ? (
          <p className="text-xs text-zinc-500 px-4 py-3">No sessions yet.</p>
        ) : (
          sessions.map((s) => (
            <SessionItem
              key={s.id}
              session={s}
              active={s.id === activeSessionId}
              onSelect={() => onSelect(s.id)}
              onRename={(title) => onRename(s.id, title)}
              onDelete={() => onDelete(s.id)}
            />
          ))
        )}
      </div>

      <div className="px-4 py-3 border-t border-zinc-800">
        <button
          onClick={onLogout}
          className="flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          Logout
        </button>
      </div>
    </aside>
  );
}
