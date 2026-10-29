# OportunidadBot Web App

Aplicación privada para usuarios con plan Professional o Enterprise. Es independiente de `landing/` y utiliza la API FastAPI existente.

## Variables de entorno

Crear `webapp/.env.local` con:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

En el entorno del backend deben configurarse además:

```env
WEB_SESSION_SECRET=un-secreto-aleatorio-largo
WEB_SESSION_COOKIE_SECURE=false
WEB_APP_ORIGIN=http://localhost:3000
TELEGRAM_LOGIN_CLIENT_ID=tu-client-id-de-botfather
TELEGRAM_LOGIN_CLIENT_SECRET=tu-client-secret-de-botfather
TELEGRAM_LOGIN_REDIRECT_URI=http://localhost:8000/api/web/auth/telegram/callback
```

Usar `WEB_SESSION_COOKIE_SECURE=true` en producción. En BotFather, registrar `WEB_APP_ORIGIN` como Trusted Origin y `TELEGRAM_LOGIN_REDIRECT_URI` como Redirect URL. El Client Secret solo se configura en el backend.

## Desarrollo

```bash
npm install
npm run dev
```

La API debe ejecutarse en la URL indicada por `NEXT_PUBLIC_API_BASE_URL`.
