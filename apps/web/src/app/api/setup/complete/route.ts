import { NextRequest, NextResponse } from "next/server";

const upstream =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";

export async function POST(request: NextRequest) {
  const response = await fetch(`${upstream}/setup/complete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await request.text(),
    cache: "no-store",
  });
  const body = await response.text();
  if (!response.ok) {
    return new NextResponse(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  }
  const data = JSON.parse(body) as {
    status: string;
    clinic_id: string;
    clinic_name: string;
    admin_email: string;
    access_token: string;
    refresh_token: string;
  };
  const next = NextResponse.json({
    status: data.status,
    clinic_id: data.clinic_id,
    clinic_name: data.clinic_name,
    admin_email: data.admin_email,
    access_token: data.access_token,
  });
  if (data.refresh_token) {
    next.cookies.set("dcp_refresh", data.refresh_token, {
      httpOnly: true,
      sameSite: "strict",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 14,
    });
  }
  return next;
}
