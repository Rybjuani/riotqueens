# Despliegue inicial

**Última verificación:** 2026-08-17

## Estado verificado

- VPS OVH activo en `148.113.167.121`, Ubuntu 24.04, 4 vCPU, 8 GB RAM y 75 GB de disco.
- acceso administrativo por clave pública con usuario `ubuntu`;
- login SSH por contraseña y login de root deshabilitados;
- UFW activo: entrada denegada por defecto y solo `22/tcp`, `80/tcp`, `443/tcp` y `443/udp` permitidos;
- Docker y Compose activos;
- release de diseño Qwen y runtime real: ver `RELEASE_SHA` de la release activa bajo
  `/opt/riotqueens/releases/<sha>` (post-2026-08-17: incluye UI Qwen, Gemini primary,
  Euryale fallback, y a partir del corte durable/clickwrap las migraciones 0002/0003);
- servicios `postgres`, `api`, `web` y `caddy` healthy; Caddy publica HTTP en `148.113.167.121`;
- runtime compartido en `/opt/riotqueens/shared/runtime.env` (modo `0600`) con prefijo `RIOTQUEENS_*`;
- casting de voz Bardera **cerrado** (2026-08-17): primario Gemini 3.1 Flash Lite; fallback de lab
  Euryale 70B vía OpenRouter; no reabrir Dolphin ni nueva matriz de casting;
- provider real verificado: `/api/v1/runtime/status` → `mode=real`,
  `model=gemini-3.1-flash-lite`, `fallback_model=sao10k/l3.3-euryale-70b`;
- con `RIOTQUEENS_AUTH_ENABLED=false` (preprod abierto por IP), `/api/v1/chat` requiere `user_id`
  en el body y devuelve solo `response.content` con `Cache-Control: no-store`;
- con `DATABASE_URL` presente, conversaciones y memorias son **durables en PostgreSQL**
  (migraciones `0002_conversations_memories.sql`); reiniciar `api` no borra el hilo;
- clickwrap +18 versionado implementado (`/v1/consent/status`, `/v1/consent/accept`, migración
  `0003_clickwrap_acceptances.sql`); el gate `acceptance_required` aplica **solo** cuando
  `RIOTQUEENS_AUTH_ENABLED=true`;
- Queens no registradas responden `404 queen_not_found`;
- el logo entregado por HTTP conserva el SHA-256 oficial
  `e47df47761cdee8da0b7674b0bdb8f35a71086c24474a33d2b496de67ad3e3b1`;
- `/.env` y `/.ssh/authorized_keys` responden `404`;
- **DNS/TLS bloqueados:** el dominio `riotqueens.ai` **no está registrado** (WHOIS 2026-08-17:
  available). No hay `A`/`AAAA` ni HTTPS hasta comprar/registrar el dominio y apuntarlo al VPS.

## Contrato

- el código vive bajo `/opt/riotqueens/releases/<git-sha>`;
- la configuración runtime vive fuera de la release, en `/opt/riotqueens/shared/runtime.env`, con modo `0600`;
- Caddy es el único proceso publicado;
- `/api/*` se reescribe hacia FastAPI y las demás rutas hacia Next.js;
- provider primario de producto: Gemini 3.1 Flash Lite; fallback de lab: Euryale 70B (OpenRouter);
- conversación/memoria: Postgres cuando hay `DATABASE_URL`; si no, in-process (tests/local sin DB);
- no se sirven `/home`, `.git`, `.env`, masters ni biblioteca privada.

## Activación controlada

1. Construir y validar Compose desde una release identificada por commit.
2. Aplicar migraciones en orden:

   ```bash
   docker compose --env-file .env --env-file /opt/riotqueens/shared/runtime.env \
     exec -T postgres psql -U riotqueens -d riotqueens -v ON_ERROR_STOP=1 \
     < ops/migrations/0001_identity.sql
   # idem 0002_conversations_memories.sql y 0003_clickwrap_acceptances.sql
   ```

3. Levantar `api`, `web` y `caddy` combinando configuración no sensible y secretos:

   ```bash
   docker compose \
     --env-file .env \
     --env-file /opt/riotqueens/shared/runtime.env \
     up -d --build
   ```

   El primer archivo conserva los defaults y parámetros no sensibles del release;
   el segundo aporta las claves server-side. No copiar secretos dentro de la
   release ni usar el archivo runtime externo como única fuente, porque los
   defaults de Compose volverían silenciosamente al proveedor `mock`.

4. Verificar healthchecks, logs y puertos locales.
5. Probar `/`, `/legal`, `/privacy`, `/api/health`, `/api/v1/runtime/status` y un turno de
   `/api/v1/chat` por IP.
6. **DNS (owner):** registrar `riotqueens.ai` (hoy disponible), crear `A` → `148.113.167.121`
   y decidir alias `www`.
7. **TLS:** cambiar `SITE_ADDRESS` al dominio y recrear Caddy para emitir certificados.
8. **Auth0 protegido (owner + ops):**

   - en el dashboard del tenant `riotqueens-ai-ca`, Application `riotqueens-ai`, agregar:
     - Allowed Callback URLs: `http://148.113.167.121/auth/callback`,
       `https://riotqueens.ai/auth/callback`, `http://localhost:3000/auth/callback`
     - Allowed Logout / Web Origins coherentes con esos hosts;
   - copiar secretos Auth0 al `runtime.env` del VPS (nunca a Git):
     `AUTH0_*`, `RIOTQUEENS_AUTH0_*`, `AUTH0_SECRET`, `APP_BASE_URL`;
   - set `RIOTQUEENS_AUTH_ENABLED=true`, `NEXT_PUBLIC_AUTH_ENABLED=true` y rebuild de `web`
     (el flag público es build-arg);
   - smoke: login Universal → clickwrap → chat; M2M con audience API solo para lab de API.

No declarar producción lista mientras DNS/TLS, Auth0 en browser y smoke externo HTTPS estén pendientes.
