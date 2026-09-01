"use client";

import { useEffect, useState } from "react";
import {
  BellRing,
  Building2,
  CheckCircle2,
  CircleAlert,
  CreditCard,
  ExternalLink,
  Loader2,
  LogOut,
  MessageCircle,
  Pause,
  Play,
  Plus,
  Radio,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";

type CurrentUser = { id: number; username: string; plan: string };
type Alert = {
  id: number;
  title: string;
  content: string;
  url: string | null;
  author: string;
  detected_at: string | null;
  sent_at: string | null;
  source_url: string | null;
};
type Feed = { id: number; url: string; is_active: boolean; last_check: string | null };
type SubscriptionPlan = {
  identifier: string;
  name: string;
  price: string;
  currency: string;
  source_limit: number | null;
  features: string[];
};
type Subscription = {
  plan: string;
  status: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  source_limit: number | null;
  sources_used: number;
  remaining_sources: number | null;
  has_stripe_customer: boolean;
  plans: SubscriptionPlan[];
};
type View = "opportunities" | "settings" | "subscription";

const STATUS_LABELS: Record<string, string> = {
  active: "Activa",
  trialing: "En prueba",
  past_due: "Pago pendiente",
  canceled: "Cancelada",
  incomplete: "Incompleta",
  incomplete_expired: "Incompleta expirada",
  unpaid: "Impagada",
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

function formatDate(value: string | null) {
  if (!value) return "Fecha no disponible";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Fecha no disponible"
    : new Intl.DateTimeFormat("es-ES", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

async function parseErrorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body?.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export function PrivateWebApp() {
  const [view, setView] = useState<View>("opportunities");
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  async function loadWorkspace() {
    if (!apiBaseUrl) {
      setLoginError("La URL de la API no está configurada en este despliegue.");
      return;
    }
    const meResponse = await fetch(`${apiBaseUrl}/api/web/me`, { credentials: "include" });
    if (!meResponse.ok) {
      setUser(null);
      return;
    }
    const currentUser = (await meResponse.json()) as CurrentUser;
    setUser(currentUser);

    try {
      const [alertsResponse, feedsResponse, subscriptionResponse] = await Promise.all([
        fetch(`${apiBaseUrl}/api/web/alerts`, { credentials: "include" }),
        fetch(`${apiBaseUrl}/api/web/feeds`, { credentials: "include" }),
        fetch(`${apiBaseUrl}/api/web/subscription`, { credentials: "include" }),
      ]);
      if (!alertsResponse.ok || !feedsResponse.ok || !subscriptionResponse.ok) {
        throw new Error("No se pudo cargar el espacio de trabajo.");
      }
      setAlerts((await alertsResponse.json()) as Alert[]);
      setFeeds((await feedsResponse.json()) as Feed[]);
      setSubscription((await subscriptionResponse.json()) as Subscription);
      setWorkspaceError(null);
    } catch {
      setWorkspaceError("No se pudieron cargar tus datos. Comprueba tu conexión e inténtalo de nuevo.");
    }
  }

  useEffect(() => {
    void Promise.resolve()
      .then(loadWorkspace)
      .catch(() => setLoginError("No se pudo conectar con OportunidadBot."))
      .finally(() => setIsLoading(false));
  }, []);

  async function retryLoadWorkspace() {
    setIsRefreshing(true);
    try {
      await loadWorkspace();
    } catch {
      setWorkspaceError("No se pudieron cargar tus datos. Comprueba tu conexión e inténtalo de nuevo.");
    } finally {
      setIsRefreshing(false);
    }
  }

  async function logout() {
    await fetch(`${apiBaseUrl}/api/web/auth/logout`, { method: "POST", credentials: "include" });
    setUser(null);
    setAlerts([]);
    setFeeds([]);
    setSubscription(null);
    setWorkspaceError(null);
    setView("opportunities");
  }

  async function addFeed(url: string): Promise<string | null> {
    const response = await fetch(`${apiBaseUrl}/api/web/feeds`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!response.ok) {
      return parseErrorDetail(response, "No se pudo añadir la fuente.");
    }
    const created = (await response.json()) as Feed;
    setFeeds((current) => [...current, created]);
    return null;
  }

  async function toggleFeed(feed: Feed): Promise<string | null> {
    const response = await fetch(`${apiBaseUrl}/api/web/feeds/${feed.id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_active: !feed.is_active }),
    });
    if (!response.ok) {
      return parseErrorDetail(response, "No se pudo actualizar la fuente.");
    }
    const updated = (await response.json()) as Feed;
    setFeeds((current) => current.map((item) => (item.id === updated.id ? updated : item)));
    return null;
  }

  async function deleteFeed(feedId: number): Promise<string | null> {
    const response = await fetch(`${apiBaseUrl}/api/web/feeds/${feedId}`, {
      method: "DELETE",
      credentials: "include",
    });
    if (!response.ok) {
      return parseErrorDetail(response, "No se pudo eliminar la fuente.");
    }
    setFeeds((current) => current.filter((item) => item.id !== feedId));
    return null;
  }

  async function startCheckout(plan: string): Promise<string | null> {
    const response = await fetch(`${apiBaseUrl}/api/web/subscription/checkout`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ plan }),
    });
    if (!response.ok) {
      return parseErrorDetail(response, "No se pudo iniciar el pago.");
    }
    const body = (await response.json()) as { url: string };
    window.open(body.url, "_blank", "noopener,noreferrer");
    return null;
  }

  async function openBillingPortal(): Promise<string | null> {
    const response = await fetch(`${apiBaseUrl}/api/web/subscription/portal`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      return parseErrorDetail(response, "No se pudo abrir el portal de facturación.");
    }
    const body = (await response.json()) as { url: string };
    window.open(body.url, "_blank", "noopener,noreferrer");
    return null;
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
          <div className="flex shrink-0 items-center gap-2 sm:gap-3"><span className="hidden text-xs text-[#657168] sm:text-sm sm:block">@{user.username || "usuario"}</span><button title="Cerrar sesión" aria-label="Cerrar sesión" onClick={() => void logout()} className="grid size-9 place-items-center border bg-white text-[#536158] hover:border-[var(--accent)] hover:text-[var(--accent)]"><LogOut size={17} /></button></div>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-8 sm:py-12">
        <div className="flex flex-col justify-between gap-4 border-b pb-5 sm:gap-6 sm:pb-7 sm:flex-row sm:items-end">
          <div><p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Plan {user.plan}</p><h1 className="mt-1 font-[family-name:var(--font-display)] text-2xl font-semibold sm:mt-2 sm:text-3xl sm:text-4xl">Espacio de oportunidades</h1></div>
          <div className="flex w-full overflow-x-auto border bg-white p-1 sm:w-fit" role="tablist" aria-label="Panel">
            <button role="tab" aria-selected={view === "opportunities"} onClick={() => setView("opportunities")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "opportunities" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><BellRing size={16} />Oportunidades</button>
            <button role="tab" aria-selected={view === "settings"} onClick={() => setView("settings")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "settings" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><Settings2 size={16} />Configuración</button>
            <button role="tab" aria-selected={view === "subscription"} onClick={() => setView("subscription")} className={`flex h-9 shrink-0 items-center gap-2 px-2.5 text-xs sm:px-3 sm:text-sm ${view === "subscription" ? "bg-[var(--accent)] text-white" : "text-[#516057]"}`}><CreditCard size={16} />Suscripción</button>
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
      </div>
    </main>
  );
}


function Brand() {
  return <div className="grid size-9 place-items-center bg-[var(--accent)] text-white"><Building2 size={18} /></div>;
}

function LoginScreen({ error, apiBaseUrl }: { error: string | null; apiBaseUrl?: string }) {
  const telegramBotUsername = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;
  useEffect(() => {
    if (!telegramBotUsername || typeof window === "undefined") return;
    const widgetId = "ob-telegram-widget";
    const existing = document.getElementById(widgetId);
    if (existing) existing.remove();

    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    window.onOportunidadBotTelegramLogin = async (telegramUser: any) => {
      try {
        await fetch(`${apiBaseUrl}/api/web/auth/telegram/widget`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify(telegramUser),
        });
        window.location.reload();
      } catch (e) {
        /* ignore */
      }
    };

    const script = document.createElement("script");
    script.id = widgetId;
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.setAttribute("data-telegram-login", telegramBotUsername);
    script.setAttribute("data-onauth", "onOportunidadBotTelegramLogin(user)");
    script.setAttribute("data-size", "large");
    script.async = true;
    const container = document.getElementById("telegram-widget-container");
    if (container) container.appendChild(script);

    return () => {
      try {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        delete window.onOportunidadBotTelegramLogin;
      } catch (e) {}
      try {
        if (container) container.innerHTML = "";
      } catch (e) {}
    };
  }, [telegramBotUsername, apiBaseUrl]);

  async function startTelegramAuthClick() {
    if (!apiBaseUrl) return;
    try {
      const resp = await fetch(`${apiBaseUrl}/api/web/auth/telegram/start`, {
        method: "GET",
        credentials: "include",
        redirect: "manual",
      });
      const loc = resp.headers.get("location") || resp.headers.get("Location");
      if (loc) {
        if (loc.startsWith("tg://")) {
          // Try native app using hidden iframe, then fallback to t.me link or web.telegram.org
          try {
            const iframe = document.createElement("iframe");
            iframe.style.display = "none";
            iframe.src = loc;
            document.body.appendChild(iframe);
            const bot = process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME;
            const startMatch = loc.match(/[?&](?:startapp|start)=([^&]+)/);
            const startToken = startMatch ? decodeURIComponent(startMatch[1]) : null;
            setTimeout(() => {
              try {
                if (document.body.contains(iframe)) document.body.removeChild(iframe);
              } catch (e) {
                /* ignore */
              }
              if (bot && startToken) {
                // Open t.me in a new tab and show the token for manual use (phone-number flows need native app)
                window.open(`https://t.me/${bot}?start=${encodeURIComponent(startToken)}`, "_blank");
                try {
                  // show token so user can send /start <token> manually if needed
                  // eslint-disable-next-line no-alert
                  alert(`Si inicias sesión por número en este navegador, abre https://t.me/${bot} y envía:\n\n/start ${startToken}`);
                } catch (e) {
                  /* ignore */
                }
              } else {
                window.open("https://web.telegram.org/", "_blank");
              }
            }, 1200);
          } catch (e) {
            // If iframe approach fails, fallback to direct navigation
            window.location.href = loc;
          }
        } else {
          window.location.href = loc;
        }
      } else {
        // fallback: navigate directly
        window.location.href = `${apiBaseUrl}/api/web/auth/telegram/start`;
      }
    } catch (e) {
      window.location.href = `${apiBaseUrl}/api/web/auth/telegram/start`;
    }
  }

  return <main className="relative grid min-h-screen overflow-hidden px-5 py-8 sm:px-10"><div className="absolute -left-32 top-0 h-72 w-72 rounded-full bg-[#dcebd8] blur-3xl" /><div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-[#f3d8b6] blur-3xl" /><section className="relative m-auto w-full max-w-md border bg-[var(--surface)] p-7 shadow-[0_24px_80px_-40px_rgba(23,34,31,0.45)] sm:p-10"><div className="mb-10 flex items-center gap-3"><Brand /><span className="font-[family-name:var(--font-display)] text-lg font-semibold">OportunidadBot</span></div><p className="mb-3 text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Acceso privado</p><h1 className="font-[family-name:var(--font-display)] text-3xl font-semibold leading-tight">Tus oportunidades, en un solo lugar.</h1><p className="mt-4 text-sm leading-6 text-[#5d6962]">Accede con la cuenta de Telegram vinculada a tu suscripción Professional o Enterprise.</p>
    <div id="telegram-widget-container" className="mt-6" />
    <div className="mt-4 text-center text-xs text-[#6c766f]">Si el botón de Telegram no aparece, pulsa "Continuar con Telegram" para intentar el flujo alternativo.</div>
    {apiBaseUrl ? <button onClick={() => void startTelegramAuthClick()} className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 bg-[#229ed9] px-4 text-sm font-semibold text-white transition hover:bg-[#168ac2]"><MessageCircle size={19} />Continuar con Telegram</button> : <span className="mt-6 inline-flex h-11 w-full items-center justify-center gap-2 bg-[#a7b1aa] px-4 text-sm font-semibold text-white"><MessageCircle size={19} />Continuar con Telegram</span>}
    {error && <p className="mt-4 flex gap-2 text-sm text-[#a43820]"><CircleAlert size={18} />{error}</p>}
    <div className="mt-10 flex gap-3 border-t pt-5 text-xs leading-5 text-[#6c766f]"><ShieldCheck className="mt-0.5 shrink-0 text-[var(--accent)]" size={16} />Tu identidad se verifica directamente con Telegram.</div></section></main>;
}

function Opportunities({ alerts }: { alerts: Alert[] }) {
  if (!alerts.length) return <section className="pt-4 sm:pt-8"><div className="border border-dashed bg-white px-4 py-10 text-center sm:px-6 sm:py-14"><BellRing className="mx-auto text-[var(--accent)]" size={24} /><h2 className="mt-3 font-[family-name:var(--font-display)] text-base font-semibold sm:mt-4 sm:text-lg">Sin alertas todavía</h2><p className="mt-1 text-xs text-[#657168] sm:mt-2 sm:text-sm">Las oportunidades aparecerán aquí cuando se detecten en tus fuentes activas.</p></div></section>;
  return <section className="min-w-0 pt-4 sm:pt-8"><div className="mb-4 flex min-w-0 items-center justify-between gap-3 sm:mb-6"><div className="min-w-0"><h2 className="font-[family-name:var(--font-display)] text-lg font-semibold sm:text-xl">Alertas recientes</h2><p className="mt-0.5 text-xs text-[#657168] sm:mt-1 sm:text-sm">{alerts.length} oportunidades detectadas</p></div><SlidersHorizontal className="shrink-0 text-[#6d7b71]" size={20} /></div><div className="grid min-w-0 gap-3 sm:gap-4">{alerts.map((alert) => <article key={alert.id} className="min-w-0 overflow-hidden border bg-white p-4 transition hover:border-[#98b7a8] sm:p-6"><div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div className="min-w-0"><div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium text-[#657168]"><Radio size={14} className="shrink-0 text-[var(--accent)]" /><span className="min-w-0 break-all">{alert.source_url ?? "Fuente no disponible"}</span><span className="h-1 w-1 shrink-0 bg-[#9da69f]" /><span className="shrink-0">{formatDate(alert.detected_at)}</span></div><h3 className="mt-3 break-words font-[family-name:var(--font-display)] text-lg font-semibold leading-6 sm:text-xl sm:leading-7">{alert.title}</h3></div><span className={`inline-flex w-fit shrink-0 items-center gap-1.5 px-2.5 py-1 text-xs font-semibold ${alert.sent_at ? "bg-[var(--accent-soft)] text-[var(--accent-deep)]" : "bg-[#fff0df] text-[var(--amber)]"}`}>{alert.sent_at ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}{alert.sent_at ? "Enviada" : "Pendiente"}</span></div>{alert.content && <p className="mt-4 max-w-3xl whitespace-pre-wrap break-words text-sm leading-6 text-[#58655d]">{alert.content}</p>}<div className="mt-5 flex min-w-0 flex-col gap-2 border-t pt-4 text-sm sm:flex-row sm:items-center sm:justify-between sm:gap-3"><span className="min-w-0 break-words text-[#657168]">{alert.author ? `Publicado por ${alert.author}` : "Autor no disponible"}</span>{alert.url && <a href={alert.url} target="_blank" rel="noreferrer" className="inline-flex w-fit shrink-0 items-center gap-1.5 font-semibold text-[var(--accent)] hover:text-[var(--accent-deep)]">Ver publicación <ExternalLink size={15} /></a>}</div></article>)}</div></section>;
}

function Configuration({
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

function SubscriptionPanel({
  subscription,
  onCheckout,
  onOpenPortal,
}: {
  subscription: Subscription | null;
  onCheckout: (plan: string) => Promise<string | null>;
  onOpenPortal: () => Promise<string | null>;
}) {
  const [pendingPlan, setPendingPlan] = useState<string | null>(null);
  const [isOpeningPortal, setIsOpeningPortal] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  if (!subscription) {
    return <section className="pt-8"><div className="border border-dashed bg-white px-6 py-14 text-center text-sm text-[#657168]">No se pudo cargar tu suscripción.</div></section>;
  }

  async function handleCheckout(plan: string) {
    setActionError(null);
    setPendingPlan(plan);
    const error = await onCheckout(plan);
    if (error) setActionError(error);
    setPendingPlan(null);
  }

  async function handleOpenPortal() {
    setActionError(null);
    setIsOpeningPortal(true);
    const error = await onOpenPortal();
    if (error) setActionError(error);
    setIsOpeningPortal(false);
  }

  const remainingLabel = subscription.remaining_sources === null ? "Ilimitadas" : `${subscription.remaining_sources}`;
  const limitLabel = subscription.source_limit === null ? "Ilimitadas" : `${subscription.source_limit}`;

  return (
    <section className="grid gap-6 pt-4 sm:gap-8 sm:pt-8 lg:grid-cols-[0.9fr_1.1fr]">
      <div className="border bg-white p-4 sm:p-6">
        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--accent)]">Plan actual</p>
        <h2 className="mt-2 font-[family-name:var(--font-display)] text-2xl font-semibold capitalize">{subscription.plan}</h2>
        <span className={`mt-3 inline-flex w-fit px-2 py-1 text-xs font-semibold ${subscription.status === "active" ? "bg-[var(--accent-soft)] text-[var(--accent-deep)]" : "bg-[#fff0df] text-[var(--amber)]"}`}>
          {STATUS_LABELS[subscription.status] ?? subscription.status}
        </span>
        <dl className="mt-4 grid gap-3 text-sm sm:mt-6 sm:gap-4">
          <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Fuentes usadas</dt><dd className="font-medium">{subscription.sources_used} / {limitLabel}</dd></div>
          <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Fuentes disponibles</dt><dd className="font-medium">{remainingLabel}</dd></div>
          <div className="flex justify-between border-b pb-3"><dt className="text-[#657168]">Próxima renovación</dt><dd className="font-medium">{formatDate(subscription.current_period_end)}</dd></div>
          {subscription.cancel_at_period_end && <p className="text-sm text-[var(--amber)]">Tu suscripción se cancelará al final del periodo actual.</p>}
        </dl>
        <button
          onClick={() => void handleOpenPortal()}
          disabled={!subscription.has_stripe_customer || isOpeningPortal}
          className="mt-4 inline-flex h-11 w-full items-center justify-center gap-2 border bg-white px-4 text-sm font-semibold text-[#536158] hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:opacity-50 sm:mt-6 sm:h-10"
        >
          {isOpeningPortal ? <Loader2 size={16} className="animate-spin" /> : <CreditCard size={16} />}
          Gestionar en Stripe Portal
        </button>
        {!subscription.has_stripe_customer && <p className="mt-1.5 text-xs text-[#657168] leading-5">Aún no tienes un cliente de Stripe asociado. Contrata un plan para activarlo.</p>}
        {actionError && <p className="mt-3 flex items-center gap-2 text-sm text-[#a43820]"><CircleAlert size={16} />{actionError}</p>}
      </div>

      <div className="grid gap-3 sm:gap-4 sm:grid-cols-3">
        {subscription.plans.map((plan) => {
          const isCurrent = plan.identifier === subscription.plan;
          return (
            <div key={plan.identifier} className={`flex flex-col border bg-white p-4 sm:p-5 ${isCurrent ? "border-[var(--accent)] border-2" : ""}`}>
              <p className="font-[family-name:var(--font-display)] text-base font-semibold sm:text-lg">{plan.name}</p>
              <p className="mt-1 text-xl font-semibold sm:text-2xl">{plan.price} {plan.currency}<span className="text-xs font-normal text-[#657168] sm:text-sm">/mes</span></p>
              <ul className="mt-3 flex-1 space-y-1.5 text-xs text-[#58655d] sm:mt-4 sm:space-y-2 sm:text-sm">
                {plan.features.map((feature) => <li key={feature}>• {feature}</li>)}
              </ul>
              <button
                onClick={() => void handleCheckout(plan.identifier)}
                disabled={isCurrent || pendingPlan === plan.identifier}
                className="mt-4 inline-flex h-11 items-center justify-center gap-2 bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-50 sm:mt-5 sm:h-10"
              >
                {pendingPlan === plan.identifier ? <Loader2 size={16} className="animate-spin" /> : null}
                {isCurrent ? "Plan actual" : "Contratar"}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}