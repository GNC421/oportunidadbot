import type { NextConfig } from "next";

console.info(
  "[webapp] NEXT_PUBLIC_API_BASE_URL:",
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "not configured"
);

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
