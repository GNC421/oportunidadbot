export type EnterpriseOrganization = {
  id: number;
  name: string;
  seats_purchased: number;
  seats_used: number;
  seats_available: number;
};
export type EnterpriseMember = {
  user_id: number;
  parent_user_id: number | null;
  role: "OWNER" | "MANAGER" | "EMPLOYEE";
  status: string;
  username: string;
};
export type EnterpriseTree = {
  organization: EnterpriseOrganization;
  viewer_role: "OWNER" | "MANAGER" | "EMPLOYEE";
  members: EnterpriseMember[];
};
export type EnterpriseTopSource = { url: string; alerts: number };
export type EnterpriseMemberStats = { user_id: number; username: string; role: string; alerts_received: number; active_sources: number };
export type EnterpriseStats = {
  period_days: number;
  has_data: boolean;
  total_alerts: number;
  alerts_in_period: number;
  active_sources: number;
  total_sources: number;
  top_sources: EnterpriseTopSource[];
  members: EnterpriseMemberStats[];
};
