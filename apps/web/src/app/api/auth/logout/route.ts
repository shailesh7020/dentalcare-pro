import { NextRequest, NextResponse } from "next/server";

const upstream = process.env.API_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get("dcp_refresh")?.value;
  if (refreshToken) await fetch(`${upstream}/auth/logout`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ refresh_token: refreshToken }), cache: "no-store" });
  const next = new NextResponse(null, { status: 204 });
  next.cookies.delete("dcp_refresh");
  return next;
}
