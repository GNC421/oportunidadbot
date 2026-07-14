import { NextResponse } from "next/server";

import { getSupabaseAdminClient } from "@/lib/supabase-admin";

type LeadPayload = {
  name?: string;
  email?: string;
  company?: string;
  city?: string;
  phone?: string;
};

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export async function POST(request: Request) {
  const payload = (await request.json()) as LeadPayload;

  const lead = {
    name: payload.name?.trim() ?? "",
    email: payload.email?.trim().toLowerCase() ?? "",
    company: payload.company?.trim() ?? "",
    city: payload.city?.trim() ?? "",
    phone: payload.phone?.trim() ?? "",
    created_at: new Date().toISOString(),
  };

  if (!lead.name || !lead.city || !lead.email) {
    return NextResponse.json(
      { message: "Nombre, email y ciudad son obligatorios." },
      { status: 400 }
    );
  }

  if (!isValidEmail(lead.email)) {
    return NextResponse.json(
      { message: "Introduce un email válido." },
      { status: 400 }
    );
  }

  const supabase = getSupabaseAdminClient();

  if (!supabase) {
    console.error(
      "[early-access] Missing Supabase configuration. Expected SUPABASE_URL and SUPABASE_KEY."
    );
    return NextResponse.json(
      { message: "No hemos podido registrar tu solicitud en este momento." },
      { status: 503 }
    );
  }

  const { error } = await supabase.from("early_access_leads").insert(lead);

  if (error) {
    console.error("[early-access] Supabase insert failed", error);
    return NextResponse.json(
      { message: "No hemos podido registrar tu solicitud en este momento." },
      { status: 502 }
    );
  }

  return NextResponse.json({
    message: "Solicitud enviada. Te contactaremos antes del lanzamiento.",
  });
}