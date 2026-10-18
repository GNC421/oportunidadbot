"use client";

import { useState } from "react";
import { BellRing, CircleAlert, CreditCard, Loader2, LogOut, Settings2, Users } from "lucide-react";
import { useWorkspace } from "@/hooks/use-workspace";
import { env } from "@/config/env";
import { Brand } from "@/components/brand";
import { LoginScreen } from "@/features/auth/login-screen";
import { Opportunities } from "@/features/alerts/opportunities-panel";
import { Configuration } from "@/features/sources/configuration-panel";
import { SubscriptionPanel } from "@/features/subscription/subscription-panel";
import { EnterprisePanel } from "@/features/enterprise/enterprise-panel";

type View = "opportunities" | "settings" | "subscription" | "enterprise";

const apiBaseUrl = env.apiBaseUrl;

export function PrivateWebApp() {
  const [view, setView] = useState<View>("opportunities");
  const {
    user,
    alerts,
    feeds,
    subscription,
    enterpriseTree,
    isLoading,
    isRefreshing,
    loginError,
    workspaceError,
    loadWorkspace,
    retryLoadWorkspace,
    logout,
    addFeed,
    toggleFeed,
    deleteFeed,
    startCheckout,
    openBillingPortal,
  } = useWorkspace();

  async function handleLogout() {
    await logout();
    setView("opportunities");
  }

  if (isLoading) {
    return (
      <main className="grid min-h-screen place-items-center gap-3 text-sm text-[#5d6962]">
        <Loader2 size={22} className="animate-spin text-[var(--accent)]" />
        Cargando panel...
      </main>
    );
  }

  if (!user) {
    return <LoginScreen error={loginError} apiBaseUrl={apiBaseUrl} />;
  }

  return (
    <main className="min-h-screen bg-[var(--background)]">
      <header className="border-b bg-[var(--surface)]">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:gap-5 sm:px-8 sm:py-4">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3"><Brand /><span className="truncate font-[family-name:var(--font-display)] text-sm font-semibold sm:text-base">OportunidadBot</span></div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3"><span className="hidden text-xs text-[#657168] sm:text-sm sm:block">@{user.username || "usuario"}</span><button title="Cerrar sesión" aria-label="Cerrar sesión" onClick={() => void handleLogout()} className="grid size-9 place-items-center border bg-white text-[#536158] hover:border-[var(--accent)] hover:text-[var(--accent)]"><LogOut size={17} /></button></div>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-12">
        <div className="flex flex-col justify-between gap-4 border-b pb-5 sm:gap-6 sm:pb-7 sm:flex-row sm:items-end">
          <div><p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Plan {user.plan}</p><h1 className="mt-1 font-[family-name:var(--font-display)] text-2xl font-semibold sm:mt-2 sm:text-3xl sm:text-4xl">Espacio de oportunidades</h1></div>
          <div className="flex w-full overflow-x-auto border bg-white p-1 sm:w-fit" role="tablist" aria-label="Panel">
            <button role="tab" aria-selected={view === "opportunities"} onClick={() => setView("opportunities")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "opportunities" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><BellRing size={16} />Oportunidades</button>
            <button role="tab" aria-selected={view === "settings"} onClick={() => setView("settings")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "settings" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><Settings2 size={16} />Configuración</button>
            <button role="tab" aria-selected={view === "subscription"} onClick={() => setView("subscription")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "subscription" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><CreditCard size={16} />Suscripción</button>
            {enterpriseTree && (
              <button role="tab" aria-selected={view === "enterprise"} onClick={() => setView("enterprise")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "enterprise" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><Users size={16} />Enterprise</button>
            )}
          </div>
        </div>
        {workspaceError && (
          <div className="mt-6 flex flex-col gap-3 border border-[#f0cbb8] bg-[#fdf3ea] px-4 py-3 text-sm text-[#a43820] sm:flex-row sm:items-center sm:justify-between">
            <span className="flex items-center gap-2"><CircleAlert size={16} />{workspaceError}</span>
            <button
              onClick={() => void retryLoadWorkspace()}
              disabled={isRefreshing}
              className="inline-flex h-8 shrink-0 items-center justify-center gap-2 border border-[#a43820] px-3 text-xs font-semibold text-[#a43820] disabled:opacity-50"
            >
              {isRefreshing ? <Loader2 size={14} className="animate-spin" /> : null}
              Reintentar
            </button>
          </div>
        )}
        {view === "opportunities" && <Opportunities alerts={alerts} />}
        {view === "settings" && <Configuration feeds={feeds} onAdd={addFeed} onToggle={toggleFeed} onDelete={deleteFeed} />}
        {view === "subscription" && <SubscriptionPanel subscription={subscription} onCheckout={startCheckout} onOpenPortal={openBillingPortal} />}
        {view === "enterprise" && enterpriseTree && (
          <EnterprisePanel tree={enterpriseTree} apiBaseUrl={apiBaseUrl} onReload={loadWorkspace} />
        )}
      </div>
    </main>
  );
}
