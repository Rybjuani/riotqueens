import { NextResponse } from "next/server";

import { auth0 } from "@/lib/auth0";

export async function GET() {
  const session = await auth0.getSession();
  if (!session?.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return NextResponse.json(
    { accessToken: session.accessToken },
    { headers: { "Cache-Control": "no-store" } },
  );
}
