import { describe, expect, it, vi } from "vitest";
import { api, configureApiSession } from "@/lib/api";

// Helper function to decode JWT claims on the client
export function parseJwtClaims(token: string): { sub?: string; role?: string; exp?: number } | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const json = Buffer.from(base64, "base64").toString("utf-8");
    return JSON.parse(json);
  } catch {
    return null;
  }
}

// Client-side RBAC permission guard
export function hasRequiredRole(userRole: string | undefined, allowedRoles: string[]): boolean {
  if (!userRole) return false;
  return allowedRoles.includes(userRole);
}

// Session expiration helper
export function isTokenExpired(exp?: number): boolean {
  if (!exp) return true;
  const now = Math.floor(Date.now() / 1000);
  return exp <= now;
}

describe("Frontend Authentication & Session Utilities", () => {
  it("attaches configured Bearer token to API request headers", async () => {
    const testToken = "test-jwt-token-xyz-123";
    const unauthorizedCallback = vi.fn().mockResolvedValue(undefined);

    configureApiSession(testToken, unauthorizedCallback);

    // Simulate an interceptor pass
    const config = { headers: {} as Record<string, string> };
    const requestInterceptor = (api.interceptors.request as unknown as {
      handlers: Array<{ fulfilled: (config: unknown) => unknown }>;
    }).handlers[0].fulfilled;

    const modified = requestInterceptor(config) as { headers: { Authorization: string } };
    expect(modified.headers.Authorization).toBe(`Bearer ${testToken}`);
  });

  it("decodes JWT token claims correctly", () => {
    const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString("base64url");
    const payload = Buffer.from(
      JSON.stringify({
        sub: "user-12345",
        role: "DENTIST",
        exp: Math.floor(Date.now() / 1000) + 3600,
      })
    ).toString("base64url");
    const signature = "fake-signature";
    const dummyJwt = `${header}.${payload}.${signature}`;

    const claims = parseJwtClaims(dummyJwt);
    expect(claims).not.toBeNull();
    expect(claims?.sub).toBe("user-12345");
    expect(claims?.role).toBe("DENTIST");
    expect(claims?.exp).toBeGreaterThan(Math.floor(Date.now() / 1000));
  });

  it("returns null for malformed JWT strings", () => {
    expect(parseJwtClaims("invalid-token-string")).toBeNull();
    expect(parseJwtClaims("only.two.parts.extra.parts")).toBeNull();
  });

  it("correctly validates role-based route permissions", () => {
    const adminRoles = ["CLINIC_ADMIN", "SUPER_ADMIN"];
    const clinicalRoles = ["DENTIST", "CLINIC_ADMIN", "SUPER_ADMIN"];

    expect(hasRequiredRole("CLINIC_ADMIN", adminRoles)).toBe(true);
    expect(hasRequiredRole("DENTIST", adminRoles)).toBe(false);
    expect(hasRequiredRole("DENTIST", clinicalRoles)).toBe(true);
    expect(hasRequiredRole("RECEPTIONIST", clinicalRoles)).toBe(false);
    expect(hasRequiredRole(undefined, clinicalRoles)).toBe(false);
  });

  it("correctly identifies expired vs active tokens", () => {
    const pastExp = Math.floor(Date.now() / 1000) - 60; // 1 min ago
    const futureExp = Math.floor(Date.now() / 1000) + 900; // 15 mins in future

    expect(isTokenExpired(pastExp)).toBe(true);
    expect(isTokenExpired(futureExp)).toBe(false);
    expect(isTokenExpired(undefined)).toBe(true);
  });
});
