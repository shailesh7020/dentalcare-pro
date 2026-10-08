"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@dentalcare.com");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  const [needsSetup, setNeedsSetup] = useState(false);

  useEffect(() => {
    fetch("/api/setup/status")
      .then((r) => r.json())
      .then((data) => {
        if (data && data.is_initialized === false) {
          setNeedsSetup(true);
        }
      })
      .catch(() => null);
  }, []);

  async function performLogin(loginEmail: string, loginPassword: string) {
    setPending(true);
    setError("");
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: loginEmail, password: loginPassword }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null);
      setError(body?.message ?? body?.detail ?? "Unable to sign in");
      setPending(false);
      return;
    }
    router.replace("/");
    router.refresh();
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await performLogin(email, password);
  }

  return (
    <main className="login-page">
      <form className="login-form" onSubmit={submit}>
        <div className="brand">
          <span className="brand-mark">DC</span>
          <span>
            DentalCare <b>Pro</b>
          </span>
        </div>
        <h1>Welcome, Doctor</h1>
        <p>Click below to open your clinic workspace.</p>
        {needsSetup && (
          <div
            style={{
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              padding: "10px 14px",
              borderRadius: "10px",
              marginBottom: "12px",
              fontSize: "13px",
              color: "#166534",
              textAlign: "left",
            }}
          >
            <div style={{ fontWeight: 600 }}>✨ First-Time Clinic Setup</div>
            <div style={{ fontSize: "12px", marginTop: "2px", color: "#15803d" }}>
              Configure clinic details in 5 minutes with the Setup Wizard, or sign in directly below.
            </div>
          </div>
        )}
        <button
          type="button"
          className="new-button"
          style={{ marginBottom: "8px", background: "#0d9488", fontWeight: 700 }}
          disabled={pending}
          onClick={() => performLogin("admin@dentalcare.com", "Password123!")}
        >
          {pending ? "Opening Clinic Workspace..." : "1-Click Doctor Sign In →"}
        </button>
        <button
          type="button"
          className="new-button"
          style={{
            marginBottom: "12px",
            background: needsSetup ? "#0f766e" : "#f1f5f9",
            color: needsSetup ? "#ffffff" : "#0f172a",
            border: needsSetup ? "none" : "1px solid #cbd5e1",
            fontWeight: 600,
          }}
          onClick={() => router.push("/setup")}
        >
          🛠 First Launch Clinic Setup Wizard
        </button>
        <label>
          Email
          <input
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && (
          <p className="login-error" role="alert">
            {error}
          </p>
        )}
        <button className="new-button" disabled={pending}>
          {pending ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </main>
  );
}
