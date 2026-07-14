import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { config } from "dotenv";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootEnvPath = resolve(__dirname, "../../.env");

config({ path: rootEnvPath, override: false });

const [, , command, ...restArgs] = process.argv;

if (!command) {
  console.error("Expected a Next.js command: dev, build, or start.");
  process.exit(1);
}

const nextBin = resolve(__dirname, "../node_modules/next/dist/bin/next");
const result = spawnSync(process.execPath, [nextBin, command, ...restArgs], {
  env: process.env,
  stdio: "inherit",
});

if (typeof result.status === "number") {
  process.exit(result.status);
}

process.exit(1);
