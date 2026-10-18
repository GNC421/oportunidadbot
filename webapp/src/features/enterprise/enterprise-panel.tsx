"use client";

import { useEffect, useState } from "react";
import { CircleAlert, Loader2, Plus, Trash2 } from "lucide-react";
import { parseErrorDetail } from "@/lib/api-client";
import type { EnterpriseStats, EnterpriseTree } from "./types";

const ROLE_LABELS: Record<string, string> = { OWNER: "Propietario", MANAGER: "Responsable", EMPLOYEE: "Empleado" };
const PERIOD_OPTIONS = [7, 30, 90];

export function EnterprisePanel({
  tree,
  apiBaseUrl,
  onReload,
}: {
  tree: EnterpriseTree;
  apiBaseUrl?: string;
  onReload: () => Promise<void>;
}) {
  const [periodDays, setPeriodDays] = useState(30);
  const [stats, setStats] = useState<EnterpriseStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(true);
  const [statsError, setStatsError] = useState<string | null>(null);
  const [inviteRole, setInviteRole] = useState<"MANAGER" | "EMPLOYEE">("EMPLOYEE");
  const [inviteParentId, setInviteParentId] = useState<string>("");
  const [inviteUsername, setInviteUsername] = useState("");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteError, setInviteError] = useState<string | null>(null);
  const [inviteToken, setInviteToken] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingMemberId, setPendingMemberId] = useState<number | null>(null);
  const [confirmDeactivateId, setConfirmDeactivateId] = useState<number | null>(null);

  const canManage = tree.viewer_role !== "EMPLOYEE";
  const { organization, members } = tree;

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      if (!apiBaseUrl) return;
      setIsLoadingStats(true);
      setStatsError(null);
      try {
        const response = await fetch(`${apiBaseUrl}/api/web/enterprise/stats?period_days=${periodDays}`, { credentials: "include" });
        if (!response.ok) throw new Error("No se pudieron cargar las estadísticas.");
        const body = (await response.json()) as EnterpriseStats;
        if (!cancelled) setStats(body);
      } catch {
        if (!cancelled) setStatsError("No se pudieron cargar las estadísticas. Inténtalo de nuevo.");
      } finally {
        if (!cancelled) setIsLoadingStats(false);
      }
    }
    void loadStats();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, periodDays]);

  async function handleInvite(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsInviting(true);
    setInviteError(null);
    setInviteToken(null);
    try {
      const response = await fetch(`${apiBaseUrl}/api/web/enterprise/invitations`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          role: inviteRole,
          parent_user_id: inviteParentId ? Number(inviteParentId) : null,
          telegram_username: inviteUsername.trim() || null,
        }),
      });
      if (!response.ok) {
        setInviteError(await parseErrorDetail(response, "No se pudo crear la invitación."));
        return;
      }
      const body = (await response.json()) as { token: string };
      setInviteToken(body.token);
      setInviteUsername("");
      await onReload();
    } finally {
      setIsInviting(false);
    }
  }

  async function handleReassign(userId: number, newParentId: string) {
    if (!newParentId) return;
    setActionError(null);
    setPendingMemberId(userId);
    try {
      const response = await fetch(`${apiBaseUrl}/api/web/enterprise/members/${userId}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ parent_user_id: Number(newParentId) }),
      });
      if (!response.ok) {
        setActionError(await parseErrorDetail(response, "No se pudo reasignar el responsable."));
        return;
      }
      await onReload();
    } finally {
      setPendingMemberId(null);
    }
  }

  async function handleDeactivate(userId: number) {
    setActionError(null);
    setPendingMemberId(userId);
    try {
      const response = await fetch(`${apiBaseUrl}/api/web/enterprise/members/${userId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!response.ok) {
        setActionError(await parseErrorDetail(response, "No se pudo eliminar al empleado de la organización."));
        return;
      }
      await onReload();
    } finally {
      setPendingMemberId(null);
      setConfirmDeactivateId(null);
    }
  }

  const potentialParents = members.filter((member) => member.role !== "EMPLOYEE" || canManage);

  return (
    <section className="grid gap-6 pt-4 sm:gap-8 sm:pt-8">
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="border bg-white p-4 sm:p-5">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Organización</p>
          <h2 className="mt-2 font-[family-name:var(--font-display)] text-xl font-semibold">{organization.name}</h2>
          <p className="mt-1 text-sm text-[#657168]">Tu rol: {ROLE_LABELS[tree.viewer_role]}</p>
        </div>
        <div className="border bg-white p-4 sm:p-5">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Licencias Enterprise</p>
          <p className="mt-2 text-2xl font-semibold">{organization.seats_used} / {organization.seats_purchased}</p>
          <p className="mt-1 text-sm text-[#657168]">{organization.seats_available} disponibles</p>
        </div>
        <div className="border bg-white p-4 sm:p-5">
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Equipo visible</p>
          <p className="mt-2 text-2xl font-semibold">{members.length}</p>
          <p className="mt-1 text-sm text-[#657168]">{tree.viewer_role === "OWNER" ? "Toda la organización" : "Tu rama de responsabilidad"}</p>
        </div>
      </div>

      {canManage && (
        <div className="border bg-white p-4 sm:p-6">
          <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold">Invitar empleado</h3>
          <p className="mt-1 text-sm text-[#657168]">Introduce el @usuario de Telegram de la persona que quieres invitar a tu equipo.</p>
          <form onSubmit={handleInvite} className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end">
            <label className="text-xs font-medium text-[#536158]">
              @usuario de Telegram
              <input
                type="text"
                value={inviteUsername}
                onChange={(event) => setInviteUsername(event.target.value)}
                placeholder="ej. ana_ventas"
                required
                className="mt-1 h-10 w-full border px-3 text-sm outline-none focus:border-[var(--accent)]"
              />
            </label>
            <label className="text-xs font-medium text-[#536158]">
              Rol
              <select value={inviteRole} onChange={(event) => setInviteRole(event.target.value as "MANAGER" | "EMPLOYEE")} className="mt-1 h-10 w-full border bg-white px-3 text-sm outline-none focus:border-[var(--accent)]">
                <option value="EMPLOYEE">Empleado</option>
                <option value="MANAGER">Responsable</option>
              </select>
            </label>
            <label className="text-xs font-medium text-[#536158]">
              Depende de
              <select value={inviteParentId} onChange={(event) => setInviteParentId(event.target.value)} className="mt-1 h-10 w-full border bg-white px-3 text-sm outline-none focus:border-[var(--accent)]">
                <option value="">Yo mismo</option>
                {potentialParents.map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.username || member.user_id}
                  </option>
                ))}
              </select>
            </label>
            <button type="submit" disabled={isInviting} className="inline-flex h-10 items-center justify-center gap-2 bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-50">
              {isInviting ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
              Invitar
            </button>
          </form>
          {inviteError && <p className="mt-2 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{inviteError}</p>}
          {inviteToken && (
            <p className="mt-3 border border-[var(--accent-soft)] bg-[var(--accent-soft)] px-3 py-2 text-xs text-[var(--accent-deep)]">
              Invitación creada. Comparte este código de aceptación con la persona invitada: <span className="font-mono">{inviteToken}</span>
            </p>
          )}
        </div>
      )}

      <div className="border bg-white p-4 sm:p-6">
        <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold">Jerarquía</h3>
        {actionError && <p className="mt-2 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{actionError}</p>}
        <div className="mt-4 divide-y border">
          {members.map((member) => (
            <div key={member.user_id} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-medium">{member.username || `Usuario ${member.user_id}`}</p>
                <p className="text-xs text-[#657168]">{ROLE_LABELS[member.role]}{member.parent_user_id ? ` · depende de ${members.find((candidate) => candidate.user_id === member.parent_user_id)?.username ?? member.parent_user_id}` : ""}</p>
              </div>
              {canManage && member.role !== "OWNER" && (
                <div className="flex items-center gap-2">
                  <select
                    defaultValue=""
                    disabled={pendingMemberId === member.user_id}
                    onChange={(event) => void handleReassign(member.user_id, event.target.value)}
                    className="h-9 border bg-white px-2 text-xs outline-none focus:border-[var(--accent)]"
                  >
                    <option value="">Cambiar responsable...</option>
                    {potentialParents
                      .filter((candidate) => candidate.user_id !== member.user_id)
                      .map((candidate) => (
                        <option key={candidate.user_id} value={candidate.user_id}>
                          {candidate.username || candidate.user_id}
                        </option>
                      ))}
                  </select>
                  {confirmDeactivateId === member.user_id ? (
                    <>
                      <button onClick={() => void handleDeactivate(member.user_id)} disabled={pendingMemberId === member.user_id} className="h-9 border bg-[#a43820] px-2.5 text-xs font-semibold text-white disabled:opacity-50">Confirmar</button>
                      <button onClick={() => setConfirmDeactivateId(null)} className="h-9 border bg-white px-2.5 text-xs font-semibold text-[#536158]">Cancelar</button>
                    </>
                  ) : (
                    <button
                      title="Eliminar de la organización"
                      aria-label="Eliminar de la organización"
                      onClick={() => setConfirmDeactivateId(member.user_id)}
                      disabled={pendingMemberId === member.user_id}
                      className="grid size-9 place-items-center border bg-white text-[#536158] hover:border-[#a43820] hover:text-[#a43820] disabled:opacity-50"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="border bg-white p-4 sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h3 className="font-[family-name:var(--font-display)] text-lg font-semibold">Estadísticas de uso</h3>
          <div className="flex gap-1 border bg-[#edf0ec] p-1">
            {PERIOD_OPTIONS.map((period) => (
              <button
                key={period}
                onClick={() => setPeriodDays(period)}
                className={`h-8 px-3 text-xs font-semibold ${periodDays === period ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}
              >
                {period} días
              </button>
            ))}
          </div>
        </div>
        {isLoadingStats ? (
          <div className="mt-6 flex items-center gap-2 text-sm text-[#657168]"><Loader2 size={16} className="animate-spin" />Cargando estadísticas...</div>
        ) : statsError ? (
          <p className="mt-4 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{statsError}</p>
        ) : !stats || !stats.has_data ? (
          <p className="mt-6 text-sm text-[#657168]">No hay datos suficientes todavía.</p>
        ) : (
          <div className="mt-4 grid gap-6 lg:grid-cols-2">
            <dl className="grid gap-3 text-sm">
              <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Alertas totales</dt><dd className="font-medium">{stats.total_alerts}</dd></div>
              <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Alertas en el periodo</dt><dd className="font-medium">{stats.alerts_in_period}</dd></div>
              <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Fuentes activas</dt><dd className="font-medium">{stats.active_sources} / {stats.total_sources}</dd></div>
              {stats.top_sources.length > 0 && (
                <div>
                  <dt className="mb-2 text-[#657168]">Fuentes con más alertas</dt>
                  <ul className="space-y-1 text-xs text-[#58655d]">
                    {stats.top_sources.map((source) => (
                      <li key={source.url} className="flex justify-between gap-2"><span className="truncate">{source.url}</span><span className="shrink-0 font-medium">{source.alerts}</span></li>
                    ))}
                  </ul>
                </div>
              )}
            </dl>
            <div>
              <p className="mb-2 text-sm text-[#657168]">Por empleado</p>
              <div className="divide-y border text-sm">
                {stats.members.map((member) => (
                  <div key={member.user_id} className="flex items-center justify-between px-3 py-2">
                    <span>{member.username || member.user_id}</span>
                    <span className="text-xs text-[#657168]">{member.alerts_received} alertas · {member.active_sources} fuentes activas</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
