import Link from "next/link";
import { ArrowRight, Radar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="relative flex min-h-screen w-full flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[48rem] bg-[radial-gradient(circle_at_top,rgba(20,184,166,0.18),transparent_38%),radial-gradient(circle_at_75%_0%,rgba(245,158,11,0.14),transparent_20%)]" />

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col items-center justify-center px-6 py-16 text-center sm:px-8">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/25">
          <Radar className="h-7 w-7" />
        </div>

        <Badge variant="accent" className="mt-8 w-fit gap-2 px-4 py-1.5 text-sm">
          Error 404
        </Badge>

        <h1 className="mt-6 text-balance text-4xl font-semibold leading-tight sm:text-5xl">
          Esta oportunidad se nos ha escapado.
        </h1>

        <p className="mt-5 max-w-xl text-pretty text-lg leading-8 text-muted-foreground">
          La página que buscas no existe o ya no está disponible.
        </p>

        <div className="mt-10 flex flex-col gap-4 sm:flex-row">
          <Button asChild size="lg">
            <Link href="/">
              Volver a OportunidadBot
              <ArrowRight className="h-4 w-4" />
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/#contacto">Ir al inicio</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
