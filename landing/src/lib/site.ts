// Shared site-wide constants for metadata, canonical URLs and structured data.

const FALLBACK_SITE_URL = "https://oportunidadbot.com";

function normalizeUrl(url: string) {
  return url.replace(/\/+$/, "");
}

export const siteConfig = {
  name: "OportunidadBot",
  tagline: "IA para oportunidades inmobiliarias",
  url: normalizeUrl(process.env.NEXT_PUBLIC_SITE_URL ?? FALLBACK_SITE_URL),
  description:
    "OportunidadBot automatiza la monitorización de fuentes online y la detección de oportunidades inmobiliarias mediante IA, con alertas en tiempo real por Telegram.",
  locale: "es_ES",
  links: {
    linkedin: process.env.NEXT_PUBLIC_LINKEDIN_URL ?? "",
  },
} as const;

export function isRealUrl(value: string) {
  return /^https?:\/\//.test(value);
}

export function absoluteUrl(path = "/") {
  return `${siteConfig.url}${path.startsWith("/") ? path : `/${path}`}`;
}
