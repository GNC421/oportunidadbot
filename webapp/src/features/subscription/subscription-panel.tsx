"use client";

import { useState } from "react";
import { CircleAlert, CreditCard, Loader2 } from "lucide-react";
import { formatDate } from "@/lib/format";
import type { Subscription } from "./types";


const STATUS_LABELS: Record<string, string> = {
  active: "Activa",
  trialing: "En prueba",
  past_due: "Pago pendiente",
  canceled: "Cancelada",
  incomplete: "Incompleta",
  incomplete_expired: "Incompleta expirada",
  unpaid: "Impagada",
};

export function SubscriptionPanel({
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

