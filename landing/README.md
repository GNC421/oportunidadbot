# OportunidadBot Landing

Landing page de captacion para acceso anticipado de OportunidadBot.

Incluye:

- Landing publica de conversion.
- Formulario de acceso anticipado.
- Persistencia de leads en Supabase.
- Dashboard privado para revisar registros.
- Proteccion del dashboard por credenciales (Basic Auth).

## Requisitos

- Node.js 20+
- Proyecto de Supabase

## Variables de entorno

La app landing carga variables desde el archivo raiz del repositorio:

- ../.env (ruta real: OportunidadBot/.env)

Debe incluir estas variables:

```env
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_PUBLISHABLE_KEY=TU_PUBLISHABLE_KEY
SUPABASE_KEY=TU_SECRET_KEY
SUPABASE_JWKS_URL=https://TU-PROYECTO.supabase.co/auth/v1/.well-known/jwks.json

ADMIN_USERNAME=tu_usuario_admin
ADMIN_PASSWORD=tu_password_admin
```

SEO opcional (recomendada en produccion):

```env
NEXT_PUBLIC_SITE_URL=https://oportunidadbot.com
NEXT_PUBLIC_LINKEDIN_URL=https://www.linkedin.com/in/tu-perfil/
```

Se usa como dominio canonico en metadata, `sitemap.xml`, `robots.txt` y Open Graph. Si no se define, se usa `https://oportunidadbot.com` como valor por defecto.

`NEXT_PUBLIC_LINKEDIN_URL` controla el enlace a LinkedIn en el footer y en /about. Si no se define, el enlace simplemente no se muestra (no se generan enlaces rotos).

Notas:

- Para esta landing, SUPABASE_URL y SUPABASE_KEY son obligatorias para guardar/leer leads.
- SUPABASE_PUBLISHABLE_KEY y SUPABASE_JWKS_URL se mantienen para compatibilidad con el resto del proyecto.
- ADMIN_USERNAME y ADMIN_PASSWORD protegen cualquier ruta bajo /admin.

## SQL para Supabase

Ejecuta este SQL en el SQL Editor de Supabase:

```sql
create extension if not exists pgcrypto;

create table if not exists public.early_access_leads (
	id uuid primary key default gen_random_uuid(),
	name text not null,
	email text not null,
	company text,
	city text not null,
	phone text,
	created_at timestamptz not null default now()
);

create index if not exists early_access_leads_created_at_idx
	on public.early_access_leads (created_at desc);
```

## Rutas

- Landing publica: /
- Sobre nosotros: /about
- Endpoint de formulario: /api/early-access
- Dashboard privado: /admin/leads (noindex, protegido con Basic Auth)
- Sitemap: /sitemap.xml
- Robots: /robots.txt

## Desarrollo local

```bash
npm install
npm run dev
```

Nota:

- Si ejecutas comandos desde la carpeta landing, los scripts ya cargan automaticamente ../.env.

## Verificacion

```bash
npm run lint
npm run build
```

## Seguridad

- El dashboard solo es accesible con las credenciales definidas en variables de entorno.
- Recomendado usar credenciales robustas y un entorno de despliegue seguro.
- Si quieres un control de acceso mas avanzado (usuarios, sesiones, MFA), el siguiente paso seria migrar a Supabase Auth o NextAuth.
