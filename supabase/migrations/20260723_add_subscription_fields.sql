-- Fase 2: Subscription model fields on users
-- Safe to run multiple times

alter table if exists public.users
  add column if not exists plan text not null default 'starter',
  add column if not exists subscription_status text not null default 'active',
  add column if not exists stripe_customer_id text,
  add column if not exists stripe_subscription_id text,
  add column if not exists current_period_end timestamptz,
  add column if not exists cancel_at_period_end boolean not null default false;

-- Allowed values for plan
alter table if exists public.users
  drop constraint if exists users_plan_check;

alter table if exists public.users
  add constraint users_plan_check
  check (plan in ('starter', 'professional', 'enterprise'));

-- Allowed values for subscription status
alter table if exists public.users
  drop constraint if exists users_subscription_status_check;

alter table if exists public.users
  add constraint users_subscription_status_check
  check (
    subscription_status in (
      'active',
      'trialing',
      'past_due',
      'canceled',
      'incomplete',
      'incomplete_expired',
      'unpaid'
    )
  );

create index if not exists users_plan_idx on public.users (plan);
create index if not exists users_subscription_status_idx on public.users (subscription_status);
