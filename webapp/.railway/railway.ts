import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const OportunidadBot = service("OportunidadBot", {
    start: "sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'",
    healthcheck: "/health",
    healthcheckTimeout: 30,
    replicas: 1,
    // builder from CaC: "DOCKERFILE"
  });
  const landing = service("landing", {
    start: "sh -c 'npm run start'",
    healthcheck: "/health",
    healthcheckTimeout: 30,
    replicas: 1,
    // builder from CaC: "DOCKERFILE"
  });
  return project("oportunidadbot", {
    resources: [OportunidadBot, landing],
  });
});
