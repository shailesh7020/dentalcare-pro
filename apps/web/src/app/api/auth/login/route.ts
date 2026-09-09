import { NextRequest, NextResponse } from "next/server";

const upstream = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: NextRequest) {
  const response = await fetch(`${upstream}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: await request.text(), cache: "no-store" });
  const body = await response.text();
  if (!response.ok) return new NextResponse(body, { status: response.status, headers: { "Content-Type": "application/json" } });
  const tokens = JSON.parse(body) as { access_token: string; refresh_token: string };
  const next = NextResponse.json({ access_token: tokens.access_token });
  next.cookies.set("dcp_refresh", tokens.refresh_token, { httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 60 * 60 * 24 * 14 });
  return next;
}
