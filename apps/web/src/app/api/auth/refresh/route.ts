import { NextRequest, NextResponse } from "next/server";

const upstream = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("dcp_refresh")?.value;
  if (!refreshToken) return NextResponse.json({ message: "Session expired" }, { status: 401 });
  const response = await fetch(`${upstream}/auth/refresh`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: refreshToken }), cache: "no-store" });
  if (!response.ok) { const next = NextResponse.json({ message: "Session expired" }, { status: 401 }); next.cookies.delete("dcp_refresh"); return next; }
  const tokens = await response.json() as { access_token: string; refresh_token: string };
  const next = NextResponse.json({ access_token: tokens.access_token });
  next.cookies.set("dcp_refresh", tokens.refresh_token, { httpOnly: true, sameSite: "strict", secure: process.env.NODE_ENV === "production", path: "/", maxAge: 60 * 60 * 24 * 14 });
  return next;
}
