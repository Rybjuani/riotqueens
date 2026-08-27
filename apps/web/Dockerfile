FROM node:20-alpine

WORKDIR /app

# Build context = repo root (see docker-compose.yml). Standalone Next app under apps/web.
COPY apps/web/package.json ./
RUN npm install

COPY apps/web ./

ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_AUTH_ENABLED=false
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_AUTH_ENABLED=${NEXT_PUBLIC_AUTH_ENABLED}
ENV NODE_ENV=production

RUN npm run build

EXPOSE 3000
CMD ["sh", "-c", "npx next start -p ${PORT:-3000}"]
