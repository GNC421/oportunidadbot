"use client";

import { useEffect, useState } from "react";
import { env } from "@/config/env";
import { parseErrorDetail } from "@/lib/api-client";
import type { CurrentUser } from "@/types/user";
import type { Alert } from "@/features/alerts/types";
import type { Feed } from "@/features/sources/types";
import type { Subscription } from "@/features/subscription/types";
import type { EnterpriseTree } from "@/features/enterprise/types";

const apiBaseUrl = env.apiBaseUrl;

export function useWorkspace() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [feeds, setFeeds] = useState<Feed[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [enterpriseTree, setEnterpriseTree] = useState<EnterpriseTree | null>(null);
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

    try {
      const treeResponse = await fetch(`${apiBaseUrl}/api/web/enterprise/tree`, { credentials: "include" });
      setEnterpriseTree(treeResponse.ok ? ((await treeResponse.json()) as EnterpriseTree) : null);
    } catch {
      setEnterpriseTree(null);
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
    setEnterpriseTree(null);
    setWorkspaceError(null);
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

  return {
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
  };
}
