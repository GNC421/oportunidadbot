import { ImageResponse } from "next/og";
import { siteConfig } from "@/lib/site";

export const size = {
  width: 1200,
  height: 630,
};
export const contentType = "image/png";

export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(135deg, #07111f 0%, #0f172a 60%, #0f766e 140%)",
          color: "#f8fafc",
          fontFamily: "sans-serif",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "#0f766e",
              borderRadius: 20,
              fontSize: 32,
              fontWeight: 700,
            }}
          >
            O
          </div>
          <span style={{ fontSize: 34, fontWeight: 700 }}>{siteConfig.name}</span>
        </div>

        <div style={{ display: "flex", marginTop: 48, fontSize: 50, fontWeight: 700, lineHeight: 1.15 }}>
          Sobre nosotros
        </div>

        <div style={{ display: "flex", marginTop: 28, fontSize: 28, color: "#cbd5e1", maxWidth: 900 }}>
          Quién está detrás de OportunidadBot y por qué existe.
        </div>
      </div>
    ),
    { ...size }
  );
}
