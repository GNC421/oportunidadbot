import Link from "next/link";
import { ArrowLeft, ExternalLink, Radar, Sparkles } from "lucide-react";

import type { Metadata } from "next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { isRealUrl, siteConfig } from "@/lib/site";

const title = "Sobre nosotros";
const description =
  "Quién está detrás de OportunidadBot y por qué existe: automatizar con IA una tarea manual y repetitiva para profesionales inmobiliarios.";

export const metadata: Metadata = {
  title,
  description,
  alternates: {
    canonical: "/about",
  },
  openGraph: {
    type: "profile",
    url: `${siteConfig.url}/about`,
    title: `${title} | ${siteConfig.name}`,
    description,
  },
  twitter: {
    card: "summary_large_image",
    title: `${title} | ${siteConfig.name}`,
    description,
  },
};

const personJsonLd = {
  "@context": "https://schema.org",
  "@type": "Person",
  name: "Guillermo Núñez",
  jobTitle: "Ingeniero Informático",
  description:
    "Ingeniero Informático con formación en Ingeniería Informática e Ingeniería del Software, y experiencia profesional en desarrollo de software, automatización y QA/SDET.",
  ...(isRealUrl(siteConfig.links.linkedin) ? { sameAs: [siteConfig.links.linkedin] } : {}),
};

export default function AboutPage() {
  return (
    <main className="relative mx-auto flex w-full max-w-4xl flex-col px-6 py-12 sm:px-8 lg:px-10">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(personJsonLd) }}
      />

      <Link
        href="/"
        className="mb-10 inline-flex w-fit items-center gap-2 text-sm text-muted-foreground transition hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver a OportunidadBot
      </Link>

      <Badge variant="accent" className="mb-6 w-fit gap-2 px-4 py-1.5 text-sm">
        <Sparkles className="h-3.5 w-3.5" />
        Sobre nosotros
      </Badge>

      <h1 className="text-balance text-4xl font-semibold leading-tight sm:text-5xl">
        Automatizar una tarea repetitiva: vigilar fuentes y detectar oportunidades.
      </h1>

      <p className="mt-6 max-w-2xl text-pretty text-lg leading-8 text-muted-foreground">
        OportunidadBot nace de una motivación concreta: aplicar automatización e inteligencia
        artificial para reducir el trabajo manual que hoy dedican los profesionales inmobiliarios
        a revisar fuentes online en busca de nuevas oportunidades.
      </p>

      <div className="mt-12 grid gap-6 sm:grid-cols-2">
        <Card className="rounded-[1.75rem]">
          <CardContent className="p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Radar className="h-5 w-5" />
            </div>
            <h2 className="mt-5 text-xl font-semibold">¿Quién está detrás?</h2>
            <p className="mt-3 text-base leading-7 text-muted-foreground">
              <strong className="text-foreground">Guillermo Núñez</strong>, Ingeniero Informático
              con formación en Ingeniería Informática e Ingeniería del Software, y experiencia
              profesional en desarrollo de software, automatización y QA/SDET.
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-[1.75rem]">
          <CardContent className="p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-foreground">
              <Sparkles className="h-5 w-5" />
            </div>
            <h2 className="mt-5 text-xl font-semibold">¿Por qué existe OportunidadBot?</h2>
            <p className="mt-3 text-base leading-7 text-muted-foreground">
              Monitorizar fuentes y detectar oportunidades a mano consume tiempo y es difícil de
              escalar. OportunidadBot automatiza esa vigilancia con IA para que ese tiempo se
              pueda dedicar a captar y cerrar, no a revisar publicaciones.
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-[1.75rem]">
          <CardContent className="p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
              <Radar className="h-5 w-5" />
            </div>
            <h2 className="mt-5 text-xl font-semibold">¿Qué se quiere conseguir?</h2>
            <p className="mt-3 text-base leading-7 text-muted-foreground">
              Construir una herramienta útil para profesionales que necesitan estar atentos a
              nuevas oportunidades sin dedicar horas a revisar fuentes manualmente.
            </p>
          </CardContent>
        </Card>

        <Card className="rounded-[1.75rem]">
          <CardContent className="p-6">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-foreground">
              <Sparkles className="h-5 w-5" />
            </div>
            <h2 className="mt-5 text-xl font-semibold">¿Para quién?</h2>
            <p className="mt-3 text-base leading-7 text-muted-foreground">
              Principalmente para profesionales y empresas del sector inmobiliario: agentes,
              agencias y equipos comerciales que necesitan reaccionar rápido ante nuevas
              publicaciones.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="mt-12 flex flex-wrap items-center gap-4">
        <Button asChild size="lg">
          <Link href="/#contacto">Quiero acceso anticipado</Link>
        </Button>
        {isRealUrl(siteConfig.links.linkedin) ? (
          <Button asChild variant="outline" size="lg">
            <a href={siteConfig.links.linkedin} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4" />
              LinkedIn
            </a>
          </Button>
        ) : null}
      </div>
    </main>
  );
}
