-- Fase 3: Stripe webhook idempotency/event log

create table if not exists public.stripe_webhook_events (
  id bigserial primary key,
  event_id text not null unique,
  event_type text not null,
  status text not null default 'received',
  payload jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  processed_at timestamptz
);

create index if not exists stripe_webhook_events_event_type_idx on public.stripe_webhook_events (event_type);
create index if not exists stripe_webhook_events_status_idx on public.stripe_webhook_events (status);
