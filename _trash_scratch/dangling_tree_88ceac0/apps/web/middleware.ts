import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  // Auth0 SDK needs domain/client/secret; skip when auth is off or unconfigured.
  const authEnabled = process.env.NEXT_PUBLIC_AUTH_ENABLED === "true";
  const configured =
    Boolean(process.env.AUTH0_DOMAIN) &&
    Boolean(process.env.AUTH0_CLIENT_ID) &&
    Boolean(process.env.AUTH0_SECRET);

  if (!authEnabled || !configured) {
    return NextResponse.next();
  }

  const { auth0 } = await import("@/lib/auth0");
  return auth0.middleware(request);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)"],
};
