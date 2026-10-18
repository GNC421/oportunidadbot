"use client";

import { useEffect } from "react";
import { CircleAlert, MessageCircle, ShieldCheck } from "lucide-react";
import { Brand } from "@/components/brand";


export function LoginScreen({ error, apiBaseUrl }: { error: string | null; apiBaseUrl?: string }) {
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

