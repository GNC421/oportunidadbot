import { defineRailway, project, service } from "railway/iac";

export default defineRailway(() => {
  const webapp = service("webapp", {
    build: "npm run build",
    start: "npm run start",
    healthcheck: "/",
    healthcheckTimeout: 30,
    replicas: 1,
  });
  return project("OportunidadBot Web App", {
    resources: [webapp],
  });
});
