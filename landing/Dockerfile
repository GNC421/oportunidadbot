FROM node:20-alpine AS deps
WORKDIR /landing
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /landing
COPY --from=deps /landing/node_modules ./node_modules
COPY . .
RUN npm run build


FROM node:20-alpine AS runner
WORKDIR /landing

ENV NODE_ENV=production
ENV PORT=8001
ENV HOSTNAME=0.0.0.0

# Copy package metadata (not strictly required if node_modules provided)
COPY package.json package-lock.json ./

# Prefer reusing installed deps from deps stage to avoid network installs at runtime
COPY --from=deps /landing/node_modules ./node_modules

# Copy build output and static assets
COPY --from=builder /landing/.next ./.next
COPY --from=builder /landing/public ./public
COPY --from=builder /landing/scripts ./scripts

EXPOSE 8001

CMD ["npm", "run", "start"]