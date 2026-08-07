import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

function unauthorizedResponse() {
  return new NextResponse("Autenticacion requerida.", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="Admin Dashboard"',
      "Cache-Control": "no-store",
    },
  });
}

export function proxy(request: NextRequest) {
  const adminUser = process.env.ADMIN_USERNAME;
  const adminPassword = process.env.ADMIN_PASSWORD;

  if (!adminUser || !adminPassword) {
    return new NextResponse(
      "Faltan ADMIN_USERNAME y ADMIN_PASSWORD en el entorno.",
      { status: 503 }
    );
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader || !authHeader.startsWith("Basic ")) {
    return unauthorizedResponse();
  }

  const base64Credentials = authHeader.split(" ")[1] ?? "";
  const decoded = atob(base64Credentials);
  const separatorIndex = decoded.indexOf(":");

  if (separatorIndex === -1) {
    return unauthorizedResponse();
  }

  const providedUser = decoded.slice(0, separatorIndex);
  const providedPassword = decoded.slice(separatorIndex + 1);

  if (providedUser !== adminUser || providedPassword !== adminPassword) {
    return unauthorizedResponse();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin", "/admin/:path*"],
};