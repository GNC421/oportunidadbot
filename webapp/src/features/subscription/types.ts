export type SubscriptionPlan = {
  identifier: string;
  name: string;
  price: string;
  currency: string;
  source_limit: number | null;
  features: string[];
};
export type Subscription = {
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
