"use client";

import { useState } from "react";
import { CircleAlert, Loader2, Pause, Play, Plus, SlidersHorizontal, Trash2 } from "lucide-react";
import { formatDate } from "@/lib/format";
import type { Feed } from "./types";


export function Configuration({
  feeds,
  onAdd,
  onToggle,
  onDelete,
}: {
  feeds: Feed[];
  onAdd: (url: string) => Promise<string | null>;
  onToggle: (feed: Feed) => Promise<string | null>;
  onDelete: (feedId: number) => Promise<string | null>;
}) {
  const [newUrl, setNewUrl] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [pendingActionId, setPendingActionId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);

  async function handleAddSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newUrl.trim() || isAdding) return;
    setIsAdding(true);
    setAddError(null);
    const error = await onAdd(newUrl.trim());
    if (error) {
      setAddError(error);
    } else {
      setNewUrl("");
    }
    setIsAdding(false);
  }

  async function handleToggle(feed: Feed) {
    setActionError(null);
    setPendingActionId(feed.id);
    const error = await onToggle(feed);
    if (error) setActionError(error);
    setPendingActionId(null);
  }

  async function handleConfirmDelete(feedId: number) {
    setActionError(null);
    setPendingActionId(feedId);
    const error = await onDelete(feedId);
    if (error) setActionError(error);
    setPendingActionId(null);
    setConfirmDeleteId(null);
  }

  return (
    <section className="grid gap-8 pt-8 lg:grid-cols-[1.4fr_0.6fr]">
      <div>
        <h2 className="font-[family-name:var(--font-display)] text-xl font-semibold">Fuentes activas</h2>
        <p className="mt-1 text-sm text-[#657168]">Estas fuentes determinan dónde busca OportunidadBot.</p>

        <form onSubmit={handleAddSubmit} className="mt-5 flex flex-col gap-2 border bg-white p-3 sm:flex-row sm:items-center sm:gap-3 sm:p-4">
          <input
            type="text"
            value={newUrl}
            onChange={(event) => setNewUrl(event.target.value)}
            placeholder="https://reddit.com/r/murcia"
            aria-label="URL de la nueva fuente"
            className="h-11 flex-1 border px-3 text-sm outline-none focus:border-[var(--accent)] sm:h-10"
          />
          <button
            type="submit"
            disabled={isAdding || !newUrl.trim()}
            className="inline-flex h-11 items-center justify-center gap-2 bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-50 sm:h-10"
          >
            {isAdding ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
            Añadir fuente
          </button>
        </form>
        {addError && <p className="mt-2 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{addError}</p>}
        {actionError && <p className="mt-2 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{actionError}</p>}

        <div className="mt-5 divide-y border bg-white">
          {feeds.length === 0 ? (
            <div className="px-4 py-12 text-center text-sm text-[#657168] sm:px-5 sm:py-10">No hay fuentes configuradas.</div>
          ) : (
            feeds.map((feed) => (
              <div key={feed.id} className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5 sm:py-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{feed.url}</p>
                  <p className="mt-1 text-xs text-[#657168]">{feed.last_check ? `Última revisión: ${formatDate(feed.last_check)}` : "Aún sin revisiones"}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className={`px-2 py-1 text-xs font-semibold ${feed.is_active ? "bg-[var(--accent-soft)] text-[var(--accent-deep)]" : "bg-[#edf0ec] text-[#617066]"}`}>
                    {feed.is_active ? "Activa" : "Pausada"}
                  </span>
                  {confirmDeleteId === feed.id ? (
                    <>
                      <span className="text-xs text-[#657168]">¿Eliminar?</span>
                      <button
                        onClick={() => void handleConfirmDelete(feed.id)}
                        disabled={pendingActionId === feed.id}
                        className="h-9 border bg-[#a43820] px-2.5 text-xs font-semibold text-white disabled:opacity-50 sm:h-8 sm:px-3"
                      >
                        Confirmar
                      </button>
                      <button onClick={() => setConfirmDeleteId(null)} className="h-9 border bg-white px-2.5 text-xs font-semibold text-[#536158] sm:h-8 sm:px-3">
                        Cancelar
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        title={feed.is_active ? "Pausar fuente" : "Reanudar fuente"}
                        aria-label={feed.is_active ? "Pausar fuente" : "Reanudar fuente"}
                        onClick={() => void handleToggle(feed)}
                        disabled={pendingActionId === feed.id}
                        className="grid size-9 place-items-center border bg-white text-[#536158] hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:opacity-50 sm:size-8"
                      >
                        {pendingActionId === feed.id ? <Loader2 size={15} className="animate-spin" /> : feed.is_active ? <Pause size={15} /> : <Play size={15} />}
                      </button>
                      <button
                        title="Eliminar fuente"
                        aria-label="Eliminar fuente"
                        onClick={() => setConfirmDeleteId(feed.id)}
                        disabled={pendingActionId === feed.id}
                        className="grid size-9 place-items-center border bg-white text-[#536158] hover:border-[#a43820] hover:text-[#a43820] disabled:opacity-50 sm:size-8"
                      >
                        <Trash2 size={15} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
      <aside className="border bg-[#e4efe7] p-6">
        <SlidersHorizontal className="text-[var(--accent)]" size={22} />
        <h2 className="mt-5 font-[family-name:var(--font-display)] text-xl font-semibold">Criterios de búsqueda</h2>
        <p className="mt-2 text-sm leading-6 text-[#526158]">La configuración avanzada se añadirá sobre este espacio sin cambiar tus fuentes ni tus alertas actuales.</p>
      </aside>
    </section>
  );
}

