"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const response = await fetch("/api/auth/login", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: data.get("email"), password: data.get("password") }) });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.message ?? "Unable to sign in");
      setPending(false);
      return;
    }
    router.replace("/");
    router.refresh();
  }

  return <main className="login-page"><form className="login-form" onSubmit={submit}><div className="brand"><span className="brand-mark">DC</span><span>DentalCare <b>Pro</b></span></div><h1>Sign in</h1><p>Access your clinic workspace.</p><label>Email<input name="email" type="email" autoComplete="email" required /></label><label>Password<input name="password" type="password" autoComplete="current-password" required /></label>{error && <p className="login-error" role="alert">{error}</p>}<button className="new-button" disabled={pending}>{pending ? "Signing in..." : "Sign in"}</button></form></main>;
}
