"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowRight,
  BellRing,
  Blocks,
  Bot,
  Building2,
  Check,
  ChevronRight,
  Clock3,
  EyeOff,
  Fingerprint,
  Globe,
  HandCoins,
  Landmark,
  LineChart,
  ListTodo,
  MessageSquareShare,
  Radar,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  TimerReset,
} from "lucide-react";

import { SectionHeading } from "@/components/section-heading";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const staggerGroup = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const heroMetrics = [
  { label: "Fuentes monitorizadas", value: "RSSHub + webs compatibles" },
  { label: "Tiempo hasta alerta", value: "Minutos, no horas" },
  { label: "Filtro de calidad", value: "IA enfocada en inmobiliario" },
];

const problemPoints = [
  "Cientos de publicaciones nuevas al día dificultan la revisión manual.",
  "Los leads más valiosos desaparecen si el aviso llega tarde.",
  "Reddit, Milanuncios o Tablón de Anuncios exigen una vigilancia constante.",
  "El equipo comercial invierte tiempo operativo en lugar de captar y cerrar.",
];

const steps = [
  {
    icon: Globe,
    title: "Añade una fuente",
    description:
      "Introduce la URL de la web o búsqueda que quieras vigilar. OportunidadBot se encarga del resto.",
  },
  {
    icon: Radar,
    title: "La convertimos en feed",
    description:
      "Transformamos la URL en un RSS compatible mediante RSSHub para monitorizar cambios cada pocos minutos.",
  },
  {
    icon: Bot,
    title: "La IA analiza contexto",
    description:
      "El sistema interpreta intención, ubicación, tipo de operación y valor potencial para descartar ruido.",
  },
  {
    icon: BellRing,
    title: "Recibes solo oportunidades",
    description:
      "Telegram te avisa en tiempo real cuando aparece una oportunidad inmobiliaria relevante.",
  },
];

const benefits = [
  {
    icon: Clock3,
    title: "Llega antes",
    description: "Reduce el tiempo entre publicación y primer contacto con el lead.",
  },
  {
    icon: ScanSearch,
    title: "Filtra mejor",
    description: "La IA separa publicaciones irrelevantes de oportunidades reales.",
  },
  {
    icon: TimerReset,
    title: "Ahorra horas",
    description: "Automatiza la revisión de fuentes sin dedicar personal a vigilancia manual.",
  },
  {
    icon: Fingerprint,
    title: "Sin curva técnica",
    description: "Configura una fuente en menos de un minuto sin conocimientos técnicos.",
  },
  {
    icon: ShieldCheck,
    title: "Enfoque vertical",
    description: "El MVP ya está afinado para el lenguaje y los matices del sector inmobiliario.",
  },
  {
    icon: MessageSquareShare,
    title: "Acción inmediata",
    description: "Las alertas llegan al canal más operativo para comerciales y captadores: Telegram.",
  },
];

const useCases = [
  {
    title: "Agencias inmobiliarias",
    description: "Detectan propietarios, compradores e inquilinos antes que el resto del mercado.",
    icon: Building2,
  },
  {
    title: "Inversores y personal shoppers",
    description: "Reciben señales rápidas para evaluar operaciones con margen antes de que se quemen.",
    icon: Landmark,
  },
  {
    title: "Captadores y equipos comerciales",
    description: "Convierten monitorización repetitiva en un flujo continuo de oportunidades accionables.",
    icon: HandCoins,
  },
];

const comparisonRows = [
  {
    label: "Velocidad de detección",
    manual: "Dependes de revisiones puntuales",
    bot: "Monitorización continua y alertas inmediatas",
  },
  {
    label: "Escalabilidad",
    manual: "Limitada por tiempo humano",
    bot: "Múltiples fuentes en paralelo",
  },
  {
    label: "Calidad del filtrado",
    manual: "Criterio manual inconsistente",
    bot: "Clasificación con IA enfocada en oportunidades",
  },
  {
    label: "Coste operativo",
    manual: "Horas diarias de revisión",
    bot: "Supervisión mínima",
  },
];

const pricingPlans = [
  {
    name: "Starter",
    price: "??€",
    description: "Para profesionales que quieren validar una fuente crítica.",
    features: ["Hasta 3 fuentes", "Alertas por Telegram", "IA vertical inmobiliaria"],
  },
  {
    name: "Professional",
    price: "??€",
    description: "Pensado para equipos comerciales que necesitan cobertura diaria.",
    featured: true,
    features: ["Hasta 15 fuentes", "Prioridad en procesamiento", "Panel de oportunidades"],
  },
  {
    name: "Enterprise",
    price: "??€",
    description: "Para agencias y redes con mayor volumen y necesidades avanzadas.",
    features: ["Fuentes ilimitadas", "Equipos y permisos", "Soporte prioritario y onboarding"],
  },
];

const faqs = [
  {
    question: "¿Necesito conocimientos técnicos para configurarlo?",
    answer:
      "No. El objetivo del producto es que solo tengas que pegar una URL y empezar a recibir alertas relevantes.",
  },
  {
    question: "¿Qué tipo de fuentes puede monitorizar?",
    answer:
      "Cualquier fuente compatible con RSSHub o transformable a un feed RSS, incluyendo plataformas como Reddit, Milanuncios o Tablón de Anuncios.",
  },
  {
    question: "¿OportunidadBot notifica todo lo que encuentra?",
    answer:
      "No. La propuesta de valor es filtrar ruido y avisarte solo de publicaciones que la IA considere oportunidades inmobiliarias reales.",
  },
  {
    question: "¿Ya está disponible para contratar?",
    answer:
      "Todavía no. Esta landing está orientada a captar interesados para acceso anticipado antes del lanzamiento oficial.",
  },
];

const formFields = [
  { label: "Nombre", placeholder: "Tu nombre", type: "text", required: true },
  { label: "Email", placeholder: "tu@email.com", type: "email", required: true },
  { label: "Empresa (opcional)", placeholder: "Nombre de tu empresa", type: "text" },
  { label: "Ciudad", placeholder: "Madrid", type: "text", required: true },
  { label: "Teléfono (opcional)", placeholder: "+34 600 000 000", type: "tel" },
];

function MotionSection({
  className,
  id,
  children,
}: {
  className?: string;
  id?: string;
  children: React.ReactNode;
}) {
  return (
    <motion.section
      id={id}
      className={className}
      variants={fadeUp}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
    >
      {children}
    </motion.section>
  );
}

export function LandingPage() {
  const [formState, setFormState] = useState<{
    status: "idle" | "submitting" | "success" | "error";
    message?: string;
  }>({ status: "idle" });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const payload = {
      name: String(formData.get("name") ?? "").trim(),
      email: String(formData.get("email") ?? "").trim(),
      company: String(formData.get("company") ?? "").trim(),
      city: String(formData.get("city") ?? "").trim(),
      phone: String(formData.get("phone") ?? "").trim(),
    };

    setFormState({ status: "submitting" });

    try {
      const response = await fetch("/api/early-access", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload)
      }).then((res) => res.json().then((data) => ({ status: res.status, data })))

      let resultMessage: string | undefined;

      console.log("response", response);

      if (response.status !== 200) {
        setFormState({
          status: "error",
          message: response.data?.message ?? "No se pudo enviar tu solicitud.",
        });
        return;
      }

      setFormState({
        status: "success",
        message:
          resultMessage ?? "Solicitud enviada. Te avisaremos cuando abramos el acceso anticipado.",
      });
    } catch {
      setFormState({
        status: "error",
        message: "Ha ocurrido un error inesperado. Inténtalo de nuevo en unos minutos.",
      });
    }
  }

  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[48rem] bg-[radial-gradient(circle_at_top,rgba(20,184,166,0.18),transparent_38%),radial-gradient(circle_at_75%_0%,rgba(245,158,11,0.14),transparent_20%)]" />

      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-16 pt-6 sm:px-8 lg:px-10">
        <header className="sticky top-4 z-30 mb-12">
          <div className="glass-panel mx-auto flex max-w-6xl items-center justify-between rounded-full px-5 py-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg shadow-primary/25">
                <Radar className="h-5 w-5" />
              </div>
              <div>
                <p className="font-display text-lg font-semibold">OportunidadBot</p>
                <p className="text-xs text-muted-foreground">IA para oportunidades inmobiliarias</p>
              </div>
            </div>
            <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
              <a href="#como-funciona" className="transition hover:text-foreground">Cómo funciona</a>
              <a href="#beneficios" className="transition hover:text-foreground">Beneficios</a>
              <a href="#precios" className="transition hover:text-foreground">Precios</a>
              <a href="#contacto" className="transition hover:text-foreground">Acceso anticipado</a>
            </nav>
            <Button asChild size="sm" className="hidden md:inline-flex">
              <a href="#contacto">Quiero acceso anticipado</a>
            </Button>
          </div>
        </header>

        <div className="grid flex-1 items-center gap-14 lg:grid-cols-[1.05fr_0.95fr] lg:gap-10">
          <motion.div
            className="max-w-3xl"
            initial="hidden"
            animate="visible"
            variants={staggerGroup}
          >
            <motion.div variants={fadeUp}>
              <Badge variant="accent" className="mb-6 w-fit gap-2 px-4 py-1.5 text-sm">
                <Sparkles className="h-3.5 w-3.5" />
                Acceso anticipado para profesionales inmobiliarios
              </Badge>
            </motion.div>

            <motion.h1
              variants={fadeUp}
              className="text-balance text-5xl font-semibold leading-[0.95] sm:text-6xl lg:text-7xl"
            >
              Detecta oportunidades inmobiliarias en tiempo real antes que tu competencia.
            </motion.h1>

            <motion.p
              variants={fadeUp}
              className="mt-7 max-w-2xl text-pretty text-lg leading-8 text-muted-foreground sm:text-xl"
            >
              OportunidadBot monitoriza automáticamente fuentes online, analiza nuevas publicaciones con IA y solo te alerta por Telegram cuando encuentra una oportunidad real.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-10 flex flex-col gap-4 sm:flex-row">
              <Button asChild size="lg">
                <a href="#contacto">
                  Quiero acceso anticipado
                  <ArrowRight className="h-4 w-4" />
                </a>
              </Button>
              <Button asChild variant="outline" size="lg">
                <a href="#como-funciona">Ver cómo funciona</a>
              </Button>
            </motion.div>

            <motion.div
              variants={staggerGroup}
              className="mt-10 grid gap-4 sm:grid-cols-3"
            >
              {heroMetrics.map((metric) => (
                <motion.div key={metric.label} variants={fadeUp}>
                  <Card className="rounded-3xl bg-card-strong/80">
                    <CardContent className="p-5">
                      <p className="text-sm text-muted-foreground">{metric.label}</p>
                      <p className="mt-3 text-sm font-medium text-foreground">{metric.value}</p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 32 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7, ease: "easeOut", delay: 0.12 }}
            className="relative"
          >
            <div className="grid-surface glass-panel relative overflow-hidden rounded-[2rem] p-4 sm:p-6">
              <div className="absolute inset-x-10 top-0 h-32 rounded-full bg-primary/10 blur-3xl" />
              <div className="relative rounded-[1.6rem] border border-white/40 bg-slate-950 p-5 text-slate-50 shadow-2xl shadow-slate-950/20">
                <div className="flex items-center justify-between border-b border-white/10 pb-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.24em] text-teal-300">Live monitor</p>
                    <h3 className="mt-2 font-display text-2xl font-semibold">Centro de señales</h3>
                  </div>
                  <Badge className="bg-teal-400/14 text-teal-100">Telegram activo</Badge>
                </div>

                <div className="mt-5 space-y-4">
                  <MockSignalCard
                    title="Particular busca vender piso en Chamberí"
                    meta="Reddit · hace 2 min · Alta prioridad"
                    score="95/100"
                    detail="La IA detecta intención de venta, zona concreta y urgencia de contacto."
                  />
                  <MockSignalCard
                    title="Alquiler con margen para coliving en Valencia"
                    meta="Milanuncios · hace 5 min · Oportunidad"
                    score="89/100"
                    detail="Encaja con criterios de rentabilidad y descarta publicaciones genéricas."
                  />
                </div>

                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-slate-400">Fuentes activas</p>
                    <p className="mt-2 text-3xl font-semibold">12</p>
                    <p className="mt-1 text-sm text-slate-400">Reddit, Milanuncios, foros y más</p>
                  </div>
                  <div className="rounded-3xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-slate-400">Filtrado de ruido</p>
                    <p className="mt-2 text-3xl font-semibold">87%</p>
                    <p className="mt-1 text-sm text-slate-400">Solo alertas útiles para el equipo</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 sm:px-8 lg:px-10">
        <motion.div
          className="glass-panel mb-24 rounded-[2rem] px-6 py-5"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={staggerGroup}
        >
          <div className="grid gap-4 md:grid-cols-4">
            {[
              "Monitorización continua",
              "Clasificación mediante IA",
              "Alertas por Telegram",
              "Setup en menos de un minuto",
            ].map((item) => (
              <motion.div
                key={item}
                variants={fadeUp}
                className="flex items-center gap-3 rounded-2xl border border-border/60 bg-card-strong/80 px-4 py-4 text-sm font-medium text-foreground"
              >
                <Check className="h-4 w-4 text-primary" />
                {item}
              </motion.div>
            ))}
          </div>
        </motion.div>

        <MotionSection id="problema" className="mb-24">
          <div className="grid gap-10 lg:grid-cols-[0.95fr_1.05fr] lg:items-end">
            <SectionHeading
              eyebrow="Problema"
              title="Tu equipo no pierde negocio por falta de mercado, lo pierde por falta de tiempo de reacción."
              description="Mientras revisas manualmente publicaciones, otras agencias ya han contactado al propietario, comprador o inquilino."
            />
            <div className="grid gap-4">
              {problemPoints.map((point, index) => (
                <Card key={point} className="rounded-3xl">
                  <CardContent className="flex items-start gap-4 p-6">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-accent-soft text-foreground">
                      <span className="font-display text-base font-semibold">0{index + 1}</span>
                    </div>
                    <p className="text-base leading-7 text-muted">{point}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </MotionSection>

        <MotionSection id="como-funciona" className="mb-24">
          <SectionHeading
            eyebrow="Cómo funciona"
            title="Automatiza la vigilancia del mercado con un flujo pensado para captar primero."
            description="Solo añades una URL. OportunidadBot transforma, monitoriza, clasifica y alerta sin intervención manual."
            align="center"
          />

          <motion.div
            className="mt-12 grid gap-5 lg:grid-cols-4"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerGroup}
          >
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <motion.div key={step.title} variants={fadeUp}>
                  <Card className="h-full rounded-[1.75rem]">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className="text-sm text-muted-foreground">Paso {index + 1}</span>
                      </div>
                      <CardTitle>{step.title}</CardTitle>
                      <CardDescription>{step.description}</CardDescription>
                    </CardHeader>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </MotionSection>

        <MotionSection id="beneficios" className="mb-24">
          <SectionHeading
            eyebrow="Beneficios"
            title="Una ventaja operativa clara para equipos que compiten por velocidad y calidad de captación."
            description="La propuesta no es leer más publicaciones, sino actuar antes y con mejor contexto."
          />

          <motion.div
            className="mt-12 grid gap-5 md:grid-cols-2 xl:grid-cols-3"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.2 }}
            variants={staggerGroup}
          >
            {benefits.map((benefit) => {
              const Icon = benefit.icon;

              return (
                <motion.div key={benefit.title} variants={fadeUp}>
                  <Card className="h-full rounded-[1.75rem] bg-card-strong/85">
                    <CardHeader>
                      <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent-soft text-foreground">
                        <Icon className="h-5 w-5" />
                      </div>
                      <CardTitle>{benefit.title}</CardTitle>
                      <CardDescription>{benefit.description}</CardDescription>
                    </CardHeader>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </MotionSection>

        <MotionSection className="mb-24">
          <SectionHeading
            eyebrow="Mockups"
            title="Visualiza cómo se sentiría el producto el día que tu equipo empiece a usarlo."
            description="Los siguientes bloques son placeholders orientados a producto para comunicar claridad, velocidad y control."
          />

          <div className="mt-12 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
            <Card className="rounded-[2rem] p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Vista principal</p>
                  <h3 className="mt-2 text-2xl font-semibold">Pipeline de oportunidades</h3>
                </div>
                <Badge variant="outline">Placeholder UI</Badge>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-[0.7fr_1.3fr]">
                <div className="rounded-[1.5rem] border border-border bg-background/70 p-4">
                  <div className="mb-4 flex items-center gap-2 text-sm font-medium">
                    <Blocks className="h-4 w-4 text-primary" />
                    Fuentes activas
                  </div>
                  <div className="space-y-3">
                    {[
                      "Reddit /r/MadridHousing",
                      "Milanuncios · pisos venta",
                      "Tablón de Anuncios · alquiler",
                    ].map((item) => (
                      <div key={item} className="rounded-2xl border border-border bg-card-strong/90 px-4 py-3 text-sm text-muted">
                        {item}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-[1.5rem] border border-border bg-slate-950 p-4 text-slate-50">
                  <div className="mb-4 flex items-center justify-between">
                    <p className="text-sm font-medium">Alertas clasificadas</p>
                    <LineChart className="h-4 w-4 text-teal-300" />
                  </div>
                  <div className="space-y-3">
                    {["Alta intención de venta", "Particular busca comprar con urgencia", "Propiedad por debajo de mercado"].map((item) => (
                      <div key={item} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-4">
                        <div className="flex items-center justify-between gap-4">
                          <p className="text-sm font-medium">{item}</p>
                          <ChevronRight className="h-4 w-4 text-slate-400" />
                        </div>
                        <p className="mt-2 text-sm text-slate-400">Placeholder de resultado enriquecido con resumen de IA, ubicación y prioridad.</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </Card>

            <div className="grid gap-5">
              <Card className="rounded-[2rem] p-6">
                <p className="text-sm text-muted-foreground">Notificación</p>
                <h3 className="mt-2 text-2xl font-semibold">Telegram listo para actuar</h3>
                <div className="mt-6 rounded-[1.5rem] border border-border bg-background/70 p-4">
                  <div className="rounded-[1.25rem] bg-[#17212b] p-4 text-white shadow-xl">
                    <p className="text-sm text-teal-200">Nuevo lead detectado</p>
                    <p className="mt-3 text-base font-medium">Propietario en Sevilla busca vender piso de 3 habitaciones.</p>
                    <p className="mt-2 text-sm text-slate-300">Prioridad alta · fuente verificada · resumen generado por IA</p>
                  </div>
                </div>
              </Card>

              <Card className="rounded-[2rem] p-6">
                <p className="text-sm text-muted-foreground">Setup</p>
                <h3 className="mt-2 text-2xl font-semibold">Configuración en menos de un minuto</h3>
                <div className="mt-6 space-y-3">
                  {[
                    "Pega una URL",
                    "Define alertas",
                    "Conecta Telegram",
                    "Empieza a monitorizar",
                  ].map((item) => (
                    <div key={item} className="flex items-center gap-3 rounded-2xl border border-border bg-card-strong/80 px-4 py-4 text-sm font-medium">
                      <Check className="h-4 w-4 text-primary" />
                      {item}
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        </MotionSection>

        <MotionSection className="mb-24">
          <SectionHeading
            eyebrow="Casos de uso"
            title="Diseñado para perfiles que viven de detectar señales antes de que se conviertan en oportunidad pública."
            description="El producto se adapta a distintas operativas dentro del mismo vertical inmobiliario."
            align="center"
          />
          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {useCases.map((item) => {
              const Icon = item.icon;
              return (
                <Card key={item.title} className="rounded-[1.75rem]">
                  <CardHeader>
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle>{item.title}</CardTitle>
                    <CardDescription>{item.description}</CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </MotionSection>

        <MotionSection className="mb-24">
          <SectionHeading
            eyebrow="Comparativa"
            title="Frente al trabajo manual, OportunidadBot cambia el ritmo y la calidad de la captación."
            description="La diferencia competitiva está en detectar antes, filtrar mejor y operar con menos fricción."
          />

          <Card className="mt-12 overflow-hidden rounded-[2rem]">
            <div className="grid grid-cols-[1.2fr_1fr_1fr] border-b border-border bg-card-strong/90 px-6 py-5 text-sm font-medium">
              <div>Factor</div>
              <div>Trabajo manual</div>
              <div>OportunidadBot</div>
            </div>
            {comparisonRows.map((row, index) => (
              <div
                key={row.label}
                className={cn(
                  "grid grid-cols-[1.2fr_1fr_1fr] gap-4 px-6 py-5 text-sm leading-6",
                  index !== comparisonRows.length - 1 && "border-b border-border"
                )}
              >
                <div className="font-medium text-foreground">{row.label}</div>
                <div className="flex items-start gap-3 text-muted-foreground">
                  <EyeOff className="mt-1 h-4 w-4 shrink-0 text-rose-500" />
                  {row.manual}
                </div>
                <div className="flex items-start gap-3 text-foreground">
                  <Check className="mt-1 h-4 w-4 shrink-0 text-primary" />
                  {row.bot}
                </div>
              </div>
            ))}
          </Card>
        </MotionSection>

        <MotionSection id="precios" className="mb-24">
          <SectionHeading
            eyebrow="Precios orientativos"
            title="Tres planes para anticipar el encaje de valor antes del lanzamiento."
            description="No son precios definitivos. Sirven para comunicar posicionamiento y ayudarte a evaluar el potencial retorno."
            align="center"
          />

          <div className="mt-4 text-center text-sm text-muted-foreground">
            Los precios pueden variar antes del lanzamiento.
          </div>

          <div className="mt-12 grid gap-5 xl:grid-cols-3">
            {pricingPlans.map((plan) => (
              <Card
                key={plan.name}
                className={cn(
                  "rounded-[2rem]",
                  plan.featured && "border-primary/40 bg-card-strong shadow-[0_28px_90px_-48px_rgba(15,118,110,0.8)]"
                )}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{plan.name}</CardTitle>
                    {plan.featured ? <Badge>Más equilibrado</Badge> : null}
                  </div>
                  <div className="flex items-end gap-2">
                    <span className="font-display text-5xl font-semibold">{plan.price}</span>
                    <span className="pb-1 text-sm text-muted-foreground">/mes</span>
                  </div>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 text-sm text-muted">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button asChild variant={plan.featured ? "default" : "outline"} className="w-full">
                    <a href="#contacto">Quiero acceso anticipado</a>
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </MotionSection>

        <MotionSection className="mb-24">
          <SectionHeading
            eyebrow="Preguntas frecuentes"
            title="Respuestas rápidas para decidir si quieres entrar antes del lanzamiento."
            description="La prioridad de esta landing es captar interés cualificado, no forzar una venta prematura."
          />
          <div className="mt-12 grid gap-4">
            {faqs.map((faq) => (
              <Card key={faq.question} className="rounded-[1.75rem]">
                <CardHeader>
                  <CardTitle className="text-lg">{faq.question}</CardTitle>
                  <CardDescription className="text-base">{faq.answer}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </MotionSection>

        <MotionSection id="contacto" className="mb-24">
          <Card className="overflow-hidden rounded-[2.25rem]">
            <div className="grid gap-8 p-6 lg:grid-cols-[0.9fr_1.1fr] lg:p-8">
              <div className="rounded-[1.75rem] bg-slate-950 p-7 text-white">
                <Badge className="bg-white/10 text-white">Acceso anticipado</Badge>
                <h2 className="mt-6 text-balance text-4xl font-semibold">Únete a la lista prioritaria de lanzamiento.</h2>
                <p className="mt-4 text-base leading-7 text-slate-300">
                  Si trabajas en inmobiliario y quieres automatizar la detección de oportunidades, deja tus datos. Te contactaremos antes de abrir el acceso público.
                </p>
                <div className="mt-8 space-y-4 text-sm text-slate-300">
                  <div className="flex items-center gap-3">
                    <ListTodo className="h-4 w-4 text-teal-300" />
                    Prioridad para perfiles del sector inmobiliario
                  </div>
                  <div className="flex items-center gap-3">
                    <Sparkles className="h-4 w-4 text-teal-300" />
                    Invitación anticipada y feedback privado sobre el producto
                  </div>
                  <div className="flex items-center gap-3">
                    <BellRing className="h-4 w-4 text-teal-300" />
                    Información de lanzamiento y primeros planes disponibles
                  </div>
                </div>
              </div>

              <div className="rounded-[1.75rem] border border-border bg-card-strong/90 p-6">
                <form className="grid gap-4 sm:grid-cols-2" onSubmit={handleSubmit}>
                  {formFields.map((field, index) => (
                    <label
                      key={field.label}
                      className={cn(
                        "block text-sm font-medium text-foreground",
                        field.label === "Email" && "sm:col-span-2",
                        field.label === "Ciudad" && index === 3 && "sm:col-span-1",
                        field.label === "Empresa (opcional)" && "sm:col-span-1"
                      )}
                    >
                      <span className="mb-2 block">{field.label}</span>
                      <Input
                        name={field.label.startsWith("Nombre") ? "name" : field.label.startsWith("Email") ? "email" : field.label.startsWith("Empresa") ? "company" : field.label.startsWith("Ciudad") ? "city" : "phone"}
                        type={field.type}
                        placeholder={field.placeholder}
                        required={field.required}
                      />
                    </label>
                  ))}
                  <div className="sm:col-span-2">
                    <Button type="submit" size="lg" className="w-full" disabled={formState.status === "submitting"}>
                      {formState.status === "submitting" ? "Enviando..." : "Quiero acceder"}
                    </Button>
                  </div>
                </form>
                {formState.message ? (
                  <p
                    className={cn(
                      "mt-4 rounded-2xl border px-4 py-3 text-sm leading-6",
                      formState.status === "success"
                        ? "border-emerald-500/20 bg-emerald-500/8 text-emerald-700 dark:text-emerald-300"
                        : "border-rose-500/20 bg-rose-500/8 text-rose-700 dark:text-rose-300"
                    )}
                  >
                    {formState.message}
                  </p>
                ) : null}
                <p className="mt-4 text-sm leading-6 text-muted-foreground">
                  Al enviar el formulario, nos indicas interés en recibir información de acceso anticipado. No se realiza ningún cobro desde esta página.
                </p>
              </div>
            </div>
          </Card>
        </MotionSection>

        <footer className="border-t border-border py-8 text-sm text-muted-foreground">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="font-display text-base font-semibold text-foreground">OportunidadBot</p>
              <p className="mt-1">Asistente inteligente para detectar oportunidades inmobiliarias en tiempo real.</p>
            </div>
            <div className="flex flex-wrap gap-5">
              <a href="#problema" className="transition hover:text-foreground">Problema</a>
              <a href="#beneficios" className="transition hover:text-foreground">Beneficios</a>
              <a href="#precios" className="transition hover:text-foreground">Precios</a>
              <a href="#contacto" className="transition hover:text-foreground">Contacto</a>
            </div>
          </div>
        </footer>
      </div>
    </main>
  );
}

function MockSignalCard({
  title,
  meta,
  score,
  detail,
}: {
  title: string;
  meta: string;
  score: string;
  detail: string;
}) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-300">{meta}</p>
          <h4 className="mt-2 text-base font-medium text-white">{title}</h4>
        </div>
        <div className="rounded-full bg-teal-400/14 px-3 py-1 text-xs font-medium text-teal-100">
          Score {score}
        </div>
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-400">{detail}</p>
    </div>
  );
}