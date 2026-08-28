# ADR 0008 — Auth0 CA como IAM externo, UUID RiotQueens como identidad durable

**Estado:** aceptado para desarrollo no productivo

**Fecha:** 2026-08-15

## Decisión

Auth0 Public Cloud Canadá se usa exclusivamente para IAM/sesión no productiva.
La API valida access tokens RS256 por JWKS, issuer, audience, expiración e
`iat`, y falla cerrada. Antes de llegar al dominio, `sub` se resuelve en una
transacción PostgreSQL a `users.id` UUID propio mediante:

`external_identities(provider='auth0', provider_subject=sub) -> users.id`

`UNIQUE(provider, provider_subject)` impide bindings duplicados. El navegador
puede enviar un identificador de conversación, pero nunca decide el actor.

Auth0 metadata no contiene clickwrap +18, conversaciones, memoria, tiers,
entitlements, media, preferencias sensibles, autorización ni estado de Queen.
La autenticación crea solamente una identidad T0 sin aceptación ni entitlement.

## Consecuencias

- `ops/migrations/0001_identity.sql` crea el mapa durable antes de activar el
  runtime protegido.
- El SDK FastAPI publicado actualmente por Auth0 es beta; se usa PyJWT estable
  con `PyJWKClient`, no criptografía manual ni dependencia beta.
- La web usa `@auth0/nextjs-auth0` v4.22.0 con Next 14.2.35: `/auth/*` se monta
  mediante middleware y Caddy conserva `/api/*` exclusivamente para FastAPI.
  El backend recibe sólo access tokens para su Custom API/Audience.
- Producción sigue bloqueada hasta la confirmación escrita de Auth0 sobre +18,
  subprocesadores/transferencias del tenant CA y transferencias desde Argentina.
