FROM node:20-alpine

WORKDIR /app
RUN npm install --global pnpm@9.15.0

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile

COPY apps/web apps/web

ARG NEXT_PUBLIC_API_URL=/api
ARG NEXT_PUBLIC_AUTH_ENABLED=false
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_AUTH_ENABLED=${NEXT_PUBLIC_AUTH_ENABLED}
ENV NODE_ENV=production

RUN pnpm --dir apps/web build

EXPOSE 3000
CMD ["sh", "-c", "pnpm --dir apps/web start -p ${PORT:-3000}"]
