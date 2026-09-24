import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { siteConfig } from "@/lib/site";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(siteConfig.url),
  title: {
    default: "OportunidadBot | Automatización y alertas para profesionales inmobiliarios",
    template: `%s | ${siteConfig.name}`,
  },
  description:
    "OportunidadBot automatiza la monitorización de fuentes online y detecta oportunidades inmobiliarias con IA. Recibe alertas por Telegram cuando aparece una publicación relevante. Acceso anticipado.",
  keywords: [
    "automatización inmobiliaria",
    "oportunidades inmobiliarias",
    "alertas inmobiliarias",
    "software para agentes inmobiliarios",
    "IA para inmobiliarias",
  ],
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    locale: siteConfig.locale,
    url: siteConfig.url,
    siteName: siteConfig.name,
    title: "OportunidadBot | Automatización y alertas para profesionales inmobiliarios",
    description:
      "Detecta oportunidades inmobiliarias en tiempo real: monitorización automática, IA y alertas por Telegram para profesionales del sector.",
  },
  twitter: {
    card: "summary_large_image",
    title: "OportunidadBot | Automatización y alertas para profesionales inmobiliarios",
    description:
      "Detecta oportunidades inmobiliarias en tiempo real: monitorización automática, IA y alertas por Telegram para profesionales del sector.",
  },
  icons: {
    icon: "/icon",
    apple: "/apple-icon",
  },
};

const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: siteConfig.name,
  url: siteConfig.url,
  description: siteConfig.description,
};

const websiteJsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  name: siteConfig.name,
  url: siteConfig.url,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="es"
      className={`${inter.variable} ${spaceGrotesk.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd) }}
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(websiteJsonLd) }}
        />
      </body>
    </html>
  );
}
