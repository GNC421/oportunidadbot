import { Building2, Mail, MapPin, Phone, Users } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getSupabaseAdminClient, type EarlyAccessLead } from "@/lib/supabase-admin";

export const dynamic = "force-dynamic";

function formatDate(dateIso: string) {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateIso));
}

function toReadableText(value: string | null) {
  return value && value.trim().length > 0 ? value : "-";
}

export default async function LeadsDashboardPage() {
  const supabase = getSupabaseAdminClient();

  if (!supabase) {
    return (
      <main className="mx-auto w-full max-w-3xl px-6 py-16 text-center">
        <h1 className="text-3xl font-semibold">Configuracion incompleta</h1>
        <p className="mt-4 text-muted-foreground">
          Define SUPABASE_URL y SUPABASE_KEY para cargar el dashboard.
        </p>
      </main>
    );
  }

  const { data, error } = await supabase
    .from("early_access_leads")
    .select("id, name, email, company, city, phone, created_at")
    .order("created_at", { ascending: false })
    .limit(200);

  const leads = error ? [] : ((data ?? []) as EarlyAccessLead[]);

  const leadsToday = leads.filter((lead) => {
    const now = new Date();
    const createdAt = new Date(lead.created_at);
    return (
      createdAt.getDate() === now.getDate() &&
      createdAt.getMonth() === now.getMonth() &&
      createdAt.getFullYear() === now.getFullYear()
    );
  }).length;

  const uniqueCities = new Set(leads.map((lead) => lead.city.trim().toLowerCase())).size;

  return (
    <main className="mx-auto w-full max-w-7xl px-6 py-10 sm:px-8 lg:px-10">
      <header className="mb-8 flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">Panel privado</p>
        <h1 className="text-4xl font-semibold">Leads de acceso anticipado</h1>
        <p className="text-base text-muted-foreground">
          Este dashboard muestra los envios del formulario publico de OportunidadBot.
        </p>
      </header>

      <section className="mb-8 grid gap-4 sm:grid-cols-3">
        <Card className="rounded-3xl">
          <CardHeader className="pb-2">
            <CardDescription>Total de leads</CardDescription>
            <CardTitle className="text-3xl">{leads.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="rounded-3xl">
          <CardHeader className="pb-2">
            <CardDescription>Nuevos hoy</CardDescription>
            <CardTitle className="text-3xl">{leadsToday}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="rounded-3xl">
          <CardHeader className="pb-2">
            <CardDescription>Ciudades detectadas</CardDescription>
            <CardTitle className="text-3xl">{uniqueCities}</CardTitle>
          </CardHeader>
        </Card>
      </section>

      <Card className="overflow-hidden rounded-[2rem]">
        <CardHeader>
          <CardTitle>Ultimos registros</CardTitle>
          <CardDescription>Mostrando hasta 200 leads ordenados del mas reciente al mas antiguo.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <p className="mb-4 rounded-2xl border border-amber-500/20 bg-amber-500/8 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
              No se pudieron cargar los leads desde Supabase en este momento.
            </p>
          ) : null}
          {leads.length === 0 ? (
            <p className="rounded-2xl border border-border bg-card-strong px-4 py-8 text-center text-muted-foreground">
              Todavia no hay registros.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[860px] text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-muted-foreground">
                    <th className="px-3 py-3 font-medium">Fecha</th>
                    <th className="px-3 py-3 font-medium">Nombre</th>
                    <th className="px-3 py-3 font-medium">Email</th>
                    <th className="px-3 py-3 font-medium">Empresa</th>
                    <th className="px-3 py-3 font-medium">Ciudad</th>
                    <th className="px-3 py-3 font-medium">Telefono</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr key={lead.id} className="border-b border-border/80 align-top">
                      <td className="px-3 py-3 text-muted-foreground">{formatDate(lead.created_at)}</td>
                      <td className="px-3 py-3 font-medium">{lead.name}</td>
                      <td className="px-3 py-3">
                        <a href={`mailto:${lead.email}`} className="text-primary hover:underline">
                          {lead.email}
                        </a>
                      </td>
                      <td className="px-3 py-3">{toReadableText(lead.company)}</td>
                      <td className="px-3 py-3">{lead.city}</td>
                      <td className="px-3 py-3">{toReadableText(lead.phone)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="rounded-3xl">
          <CardHeader className="gap-2">
            <Mail className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Contacto rapido</CardTitle>
            <CardDescription>Haz click en el email de cada fila para escribir al lead.</CardDescription>
          </CardHeader>
        </Card>
        <Card className="rounded-3xl">
          <CardHeader className="gap-2">
            <Users className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Seguimiento</CardTitle>
            <CardDescription>Convierte estos registros en tareas de tu CRM comercial.</CardDescription>
          </CardHeader>
        </Card>
        <Card className="rounded-3xl">
          <CardHeader className="gap-2">
            <MapPin className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Cobertura</CardTitle>
            <CardDescription>Comprueba en que ciudades hay mayor interes inicial.</CardDescription>
          </CardHeader>
        </Card>
        <Card className="rounded-3xl">
          <CardHeader className="gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">B2B</CardTitle>
            <CardDescription>Usa el campo empresa para priorizar leads profesionales.</CardDescription>
          </CardHeader>
        </Card>
      </section>

      <section className="mt-4 grid gap-4 sm:grid-cols-1 lg:grid-cols-1">
        <Card className="rounded-3xl">
          <CardHeader className="gap-2">
            <Phone className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Telefono</CardTitle>
            <CardDescription>
              El telefono es opcional, por eso algunos registros apareceran sin este dato.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    </main>
  );
}