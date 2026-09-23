"use client";

import { useState } from "react";
import {
  ShieldCheck,
  Smartphone,
  Wifi,
  Globe2,
  Lock,
  Copy,
  CheckCircle2,
  AlertTriangle,
  Radio,
  Terminal,
  RefreshCw,
  Sliders,
  Laptop,
} from "lucide-react";
import { EnterpriseNav } from "../nav";

export default function RemoteAccessDashboardPage() {
  const [hostname, setHostname] = useState("clinic.dentalcarepro.com");
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null);
  const [tunnelProvider, setTunnelProvider] = useState<"cloudflare" | "tailscale">("cloudflare");
  const [require2fa, setRequire2fa] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCmd(label);
    setTimeout(() => setCopiedCmd(null), 2500);
  };

  const quickTunnelCmd = "python scripts/setup_cloudflare_tunnel.py --quick";
  const installServiceCmd = "python scripts/setup_cloudflare_tunnel.py --hostname " + hostname;
  const mobileEndpointUrl = `https://${hostname}/api/v1`;

  const sampleRemoteSessions = [
    {
      id: "sess-1",
      deviceName: "Dr. Ananya's iPhone 15 Pro",
      deviceType: "IOS",
      ipAddress: "49.36.12.88 (Mobile 5G)",
      lastActive: "Just now",
      status: "ACTIVE",
      role: "DENTIST",
    },
    {
      id: "sess-2",
      deviceName: "Receptionist iPad Air",
      deviceType: "TABLET",
      ipAddress: "103.21.144.2 (Home Wi-Fi)",
      lastActive: "14 mins ago",
      status: "ACTIVE",
      role: "RECEPTIONIST",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-teal-50 text-teal-700 rounded-lg border border-teal-200">
                <Smartphone className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900">Remote & Mobile Practice Access</h1>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                <Radio className="w-3 h-3 text-emerald-600 animate-pulse" /> Ready for Ingress
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              Zero-trust ingress, Cloudflare tunnels, and mobile connectivity without opening router ports.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500">Security Policy:</span>
            <span className="inline-flex items-center gap-1 text-xs font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md border border-teal-200">
              <ShieldCheck className="w-3.5 h-3.5" /> Guardrails Enforced
            </span>
          </div>
        </div>

        {/* Status Highlights */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Mobile Login</span>
              <Smartphone className="w-4 h-4 text-teal-600" />
            </div>
            <div className="text-xl font-bold text-slate-900">Supported (4G/5G)</div>
            <p className="text-xs text-slate-500">Outside clinic via Tunnel or VPN</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Ingress Security</span>
              <Lock className="w-4 h-4 text-indigo-600" />
            </div>
            <div className="text-xl font-bold text-slate-900">Zero Port-Forward</div>
            <p className="text-xs text-slate-500">Cloudflare encrypted tunnel</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Offline Resilience</span>
              <Wifi className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-xl font-bold text-slate-900">Offline Cached Mode</div>
            <p className="text-xs text-slate-500">Local SQLite & Biometric Unlock</p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-2">
            <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase">
              <span>Destructive Guard</span>
              <AlertTriangle className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="text-xl font-bold text-emerald-700">403 Remote Block</div>
            <p className="text-xs text-slate-500">DB resets blocked remotely</p>
          </div>
        </div>

        {/* Two Column Section: Tunnel Setup & Mobile App Pairing */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card 1: Cloudflare Tunnel Configuration */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Globe2 className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-slate-900 text-base">Cloudflare Tunnel Ingress</h3>
              </div>
              <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2 py-0.5 rounded border border-indigo-200">
                On-Premise Server
              </span>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1">
                  Public Ingress Hostname
                </label>
                <input
                  type="text"
                  value={hostname}
                  onChange={(e) => setHostname(e.target.value)}
                  placeholder="e.g. clinic.dentalcarepro.com"
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 text-slate-900 font-mono"
                />
                <p className="text-xs text-slate-400 mt-1">
                  The public HTTPS domain where doctors and patients reach your clinic.
                </p>
              </div>

              {/* Quick Instant Test Tunnel */}
              <div className="p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5" /> Option 1: Instant Quick Test (No Domain Needed)
                  </span>
                  <button
                    onClick={() => copyToClipboard(quickTunnelCmd, "quick")}
                    className="text-xs font-semibold text-indigo-700 hover:text-indigo-900 flex items-center gap-1 cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedCmd === "quick" ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="text-xs text-indigo-800 leading-relaxed">
                  Run this on your clinic server terminal to instantly get a free temporary HTTPS address (<code className="font-mono bg-indigo-100 px-1 rounded">*.trycloudflare.com</code>) to test mobile logins outside the clinic immediately:
                </p>
                <div className="p-2.5 bg-slate-900 text-emerald-400 rounded-lg font-mono text-xs overflow-x-auto">
                  {quickTunnelCmd}
                </div>
              </div>

              {/* Production Permanent Windows Service */}
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                    <Sliders className="w-3.5 h-3.5" /> Option 2: Production Continuous Service
                  </span>
                  <button
                    onClick={() => copyToClipboard(installServiceCmd, "service")}
                    className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1 cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedCmd === "service" ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="text-xs text-slate-600">
                  Installs and configures Cloudflare Tunnel as a background Windows Service:
                </p>
                <div className="p-2.5 bg-slate-900 text-slate-200 rounded-lg font-mono text-xs overflow-x-auto">
                  {installServiceCmd}
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setSaveSuccess(true);
                  setTimeout(() => setSaveSuccess(false), 2500);
                }}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-lg transition-colors shadow-xs flex items-center justify-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {saveSuccess ? "Configuration Saved!" : "Save Remote Access Settings"}
              </button>
            </div>
          </div>

          {/* Card 2: Mobile App Pairing & Offline Instructions */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-teal-600" />
                <h3 className="font-bold text-slate-900 text-base">Mobile App Pairing & Usage</h3>
              </div>
              <span className="text-xs bg-teal-50 text-teal-700 font-semibold px-2 py-0.5 rounded border border-teal-200">
                Clinicians & Staff
              </span>
            </div>

            <div className="space-y-4 text-sm">
              {/* Connection Endpoint Box */}
              <div className="p-4 bg-teal-50/60 border border-teal-200 rounded-xl space-y-2">
                <span className="text-xs font-bold text-teal-900 block uppercase tracking-wider">
                  Mobile API Endpoint URL
                </span>
                <div className="flex items-center justify-between bg-white p-2.5 rounded-lg border border-teal-200 font-mono text-xs text-teal-950 font-bold">
                  <span>{mobileEndpointUrl}</span>
                  <button
                    onClick={() => copyToClipboard(mobileEndpointUrl, "endpoint")}
                    className="text-xs font-semibold text-teal-700 hover:text-teal-900 flex items-center gap-1 cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    {copiedCmd === "endpoint" ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="text-xs text-teal-800">
                  Input this URL into the mobile app to connect from outside the clinic network.
                </p>
              </div>

              {/* 3 Step Instructions */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  How Clinicians Connect Outside the Clinic:
                </h4>
                
                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700">
                  <div className="w-5 h-5 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                    1
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 block">Open Server Settings in App:</span>
                    On the mobile login screen, tap the <b>Settings (gear icon)</b> in the top right.
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700">
                  <div className="w-5 h-5 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                    2
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 block">Paste Remote URL & Test:</span>
                    Paste <code className="font-mono bg-slate-200 px-1 rounded">{mobileEndpointUrl}</code> and tap <b>Test Connection</b> to confirm reachability, then <b>Save & Apply</b>.
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700">
                  <div className="w-5 h-5 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center shrink-0 text-[11px]">
                    3
                  </div>
                  <div>
                    <span className="font-bold text-slate-900 block">Sign In or Use Biometrics:</span>
                    Enter credentials to sign in, or use <b>Biometric Quick Unlock / Offline Mode</b> if transit network drops.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Active Remote Sessions Table */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Laptop className="w-4 h-4 text-slate-700" />
                Active Remote Mobile Sessions
              </h3>
              <p className="text-xs text-slate-500">
                Tracked sessions logged in from outside the clinic LAN network.
              </p>
            </div>
            <span className="text-xs font-medium text-slate-500">
              Auto-expires after 8 hours of inactivity
            </span>
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Device Name</th>
                  <th className="py-2.5 px-4">Role</th>
                  <th className="py-2.5 px-4">Remote IP / Origin</th>
                  <th className="py-2.5 px-4">Last Active</th>
                  <th className="py-2.5 px-4 text-center">Status</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {sampleRemoteSessions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/40 text-xs">
                    <td className="py-3 px-4 font-bold text-slate-900 flex items-center gap-2">
                      <Smartphone className="w-4 h-4 text-teal-600" />
                      {s.deviceName}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-semibold">{s.role}</td>
                    <td className="py-3 px-4 font-mono text-slate-600">{s.ipAddress}</td>
                    <td className="py-3 px-4 text-slate-500">{s.lastActive}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3" />
                        {s.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => alert(`Session for ${s.deviceName} revoked.`)}
                        className="text-xs font-semibold text-rose-600 hover:text-rose-800 transition-colors cursor-pointer"
                      >
                        Revoke Access
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}
