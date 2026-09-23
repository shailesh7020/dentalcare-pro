import { NextResponse } from "next/server";

const upstream =
  process.env.API_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000/api/v1";

export async function GET() {
  try {
    const response = await fetch(`${upstream}/setup/status`, {
      cache: "no-store",
    });
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return NextResponse.json({ is_initialized: false, config: {} }, { status: 200 });
  }
}
