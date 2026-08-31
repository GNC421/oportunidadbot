FROM node:20-alpine AS deps
WORKDIR /webapp
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /webapp
COPY --from=deps /webapp/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /webapp

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY package.json package-lock.json ./
COPY --from=deps /webapp/node_modules ./node_modules
COPY --from=builder /webapp/.next ./.next
COPY --from=builder /webapp/public ./public

EXPOSE 3000

CMD ["npm", "run", "start"]