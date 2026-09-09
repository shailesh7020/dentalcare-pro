"use client";

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";
import { usePathname } from "next/navigation";

import { configureApiSession } from "@/lib/api";

type SessionState = "loading" | "authenticated" | "expired";
type Session = { state: SessionState; accessToken: string | null; logout: () => Promise<void> };
const SessionContext = createContext<Session | null>(null);

export function AuthSessionProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [state, setState] = useState<SessionState>("loading");
  const [accessToken, setAccessToken] = useState<string | null>(null);

  useEffect(() => {
    if (pathname === "/login") { setState("expired"); return; }
    async function restore() {
      try {
        const response = await fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" });
        if (!response.ok) throw new Error("Session expired");
        setAccessToken((await response.json()).access_token as string);
        setState("authenticated");
      } catch {
        setState("expired");
        window.location.assign("/login");
      }
    }
    void restore();
  }, [pathname]);

  useEffect(() => configureApiSession(accessToken, async () => { setAccessToken(null); setState("expired"); window.location.assign("/login"); }), [accessToken]);
  const value = useMemo<Session>(() => ({ state, accessToken, logout: async () => { await fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" }); setAccessToken(null); setState("expired"); window.location.assign("/login"); } }), [accessToken, state]);
  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useAuthSession(): Session {
  const session = useContext(SessionContext);
  if (!session) throw new Error("useAuthSession must be used within AuthSessionProvider");
  return session;
}
