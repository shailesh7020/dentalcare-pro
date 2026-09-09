"use client";

import Link from "next/link";
import React, { useState } from "react";
import {
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Send,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Settings,
  Filter,
  RefreshCw,
  Search,
  CheckCheck,
  ChevronRight,
} from "lucide-react";
import type { DeliveryChannel, NotificationPriority, NotificationRecord, NotificationTemplate, ClinicNotificationSettings } from "./types";

const mockNotifications: NotificationRecord[] = [
  {
    id: "notif-1",
    clinic_id: "clinic-1",
    patient_id: "p-1",
    patient_name: "Donna Noble",
    notification_type: "APPOINTMENT_REMINDER",
    priority: "HIGH",
    delivery_channel: "WHATSAPP",
    title: "Appointment Reminder: Tomorrow at 2:00 PM",
    message: "Hi Donna, reminder for your upcoming Scaling & Polishing appointment tomorrow with Dr. Tennant.",
    is_read: false,
    created_at: "2026-09-08T10:30:00Z",
    delivered_at: "2026-09-08T10:30:05Z",
  },
  {
    id: "notif-2",
    clinic_id: "clinic-1",
    patient_id: "p-2",
    patient_name: "Rose Tyler",
    notification_type: "BILLING_INVOICE_GENERATED",
    priority: "NORMAL",
    delivery_channel: "EMAIL",
    title: "Invoice INV-2026-0042 Generated",
    message: "Your invoice for INR 4,500 is ready for viewing and digital settlement.",
    is_read: true,
    read_at: "2026-09-08T09:15:00Z",
    created_at: "2026-09-08T09:00:00Z",
    delivered_at: "2026-09-08T09:00:10Z",
  },
  {
    id: "notif-3",
    clinic_id: "clinic-1",
    patient_id: "p-3",
    patient_name: "Martha Jones",
    notification_type: "FOLLOW_UP_RECALL",
    priority: "NORMAL",
    delivery_channel: "SMS",
    title: "6-Month Recall Checkup Due",
    message: "Dear Martha, it is time for your 6-month routine dental cleaning and oral exam.",
    is_read: false,
    created_at: "2026-09-07T14:20:00Z",
    delivered_at: "2026-09-07T14:20:02Z",
  },
  {
    id: "notif-4",
    clinic_id: "clinic-1",
    notification_type: "SYSTEM_ALERT",
    priority: "URGENT",
    delivery_channel: "IN_APP",
    title: "Autoclave Sterilizer Maintenance Alert",
    message: "Sterilizer Unit B cycle count reached 150 cycles. Biological indicator check required.",
    is_read: true,
    created_at: "2026-09-07T08:00:00Z",
  },
];

const mockTemplates: NotificationTemplate[] = [
  {
    id: "t-1",
    name: "Appointment 24h Reminder",
    template_key: "APPT_REMINDER_24H",
    channel: "WHATSAPP",
    subject_template: "DentalCare Pro - Visit Reminder",
    body_template: "Hello {{patient_name}}, your visit with {{dentist_name}} is booked for {{appointment_date}} at {{appointment_time}} at {{clinic_name}}.",
    variables_schema: { patient_name: "string", dentist_name: "string", appointment_date: "string", appointment_time: "string" },
    is_active: true,
  },
  {
    id: "t-2",
    name: "Invoice Notification",
    template_key: "INVOICE_ISSUED",
    channel: "EMAIL",
    subject_template: "DentalCare Pro - Invoice #{{invoice_number}}",
    body_template: "Dear {{patient_name}}, your invoice #{{invoice_number}} for {{grand_total}} is available. Balance due: {{balance_due}}.",
    variables_schema: { patient_name: "string", invoice_number: "string", grand_total: "string", balance_due: "string" },
    is_active: true,
  },
  {
    id: "t-3",
    name: "Post-Op Follow-up Recall",
    template_key: "POST_OP_RECALL",
    channel: "SMS",
    subject_template: "Clinic Care Check",
    body_template: "Hi {{patient_name}}, how are you feeling after your {{procedure_name}}? Call us if you experience discomfort.",
    variables_schema: { patient_name: "string", procedure_name: "string" },
    is_active: true,
  },
];

export default function NotificationsPage() {
  const [tab, setTab] = useState<"feed" | "send" | "templates" | "settings" | "scanners">("feed");
  const [notifications, setNotifications] = useState(mockNotifications);
  const [channelFilter, setChannelFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [scanStatus, setScanStatus] = useState<string | null>(null);

  // Direct send form state
  const [sendPatient, setSendPatient] = useState("");
  const [sendChannel, setSendChannel] = useState<DeliveryChannel>("WHATSAPP");
  const [sendPriority, setSendPriority] = useState<NotificationPriority>("NORMAL");
  const [sendTitle, setSendTitle] = useState("");
  const [sendMessage, setSendMessage] = useState("");
  const [sendSuccess, setSendSuccess] = useState(false);

  const filteredNotifs = notifications.filter((n) => {
    if (channelFilter !== "ALL" && n.delivery_channel !== channelFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        n.title.toLowerCase().includes(q) ||
        n.message.toLowerCase().includes(q) ||
        (n.patient_name && n.patient_name.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const markAllAsRead = () => {
    setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
  };

  const handleSendNotification = (e: React.FormEvent) => {
    e.preventDefault();
    if (!sendTitle || !sendMessage) return;
    const newRecord: NotificationRecord = {
      id: "notif-" + Date.now(),
      clinic_id: "clinic-1",
      patient_name: sendPatient || "Walk-in Patient",
      notification_type: "SYSTEM_ALERT",
      priority: sendPriority,
      delivery_channel: sendChannel,
      title: sendTitle,
      message: sendMessage,
      is_read: false,
      created_at: new Date().toISOString(),
      delivered_at: new Date().toISOString(),
    };
    setNotifications([newRecord, ...notifications]);
    setSendSuccess(true);
    setTimeout(() => {
      setSendSuccess(false);
      setSendTitle("");
      setSendMessage("");
      setSendPatient("");
      setTab("feed");
    }, 1200);
  };

  const triggerScanner = (type: "reminders" | "recalls") => {
    setScanStatus(`Scanning and dispatching ${type}...`);
    setTimeout(() => {
      setScanStatus(`Success: ${type === "reminders" ? "8 automated reminders dispatched" : "5 recall notices scheduled"}.`);
      setTimeout(() => setScanStatus(null), 4000);
    }, 1500);
  };

  const channelIcon = (c: DeliveryChannel) => {
    switch (c) {
      case "EMAIL":
        return <Mail className="w-4 h-4 text-blue-500" />;
      case "SMS":
        return <Smartphone className="w-4 h-4 text-emerald-500" />;
      case "WHATSAPP":
        return <MessageSquare className="w-4 h-4 text-green-600" />;
      case "PUSH":
        return <Bell className="w-4 h-4 text-amber-500" />;
      default:
        return <Bell className="w-4 h-4 text-teal-600" />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900">
              ← Dashboard
            </Link>
            <span className="text-slate-300">/</span>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-teal-50 text-teal-700 rounded-lg">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-slate-900">Communication & Notification Center</h1>
                <p className="text-xs text-slate-500">Multi-channel patient messaging & automated recall engine</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                <CheckCheck className="w-4 h-4" /> Mark all read
              </button>
            )}
            <button
              onClick={() => setTab("send")}
              className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition"
            >
              <Send className="w-4 h-4" /> Send Direct Message
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto mt-4 flex gap-2 border-b border-slate-200 text-sm">
          <button
            onClick={() => setTab("feed")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "feed"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Bell className="w-4 h-4" /> Activity Feed
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-teal-100 text-teal-800 rounded-full font-bold">
                {unreadCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setTab("send")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "send"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Send className="w-4 h-4" /> Compose
          </button>
          <button
            onClick={() => setTab("templates")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "templates"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <MessageSquare className="w-4 h-4" /> Message Templates
          </button>
          <button
            onClick={() => setTab("scanners")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "scanners"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <RefreshCw className="w-4 h-4" /> Automated Scanners
          </button>
          <button
            onClick={() => setTab("settings")}
            className={`pb-2.5 px-3 font-medium border-b-2 flex items-center gap-1.5 ${
              tab === "settings"
                ? "border-teal-600 text-teal-700"
                : "border-transparent text-slate-500 hover:text-slate-900"
            }`}
          >
            <Settings className="w-4 h-4" /> Clinic Channels
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-6">
        {scanStatus && (
          <div className="mb-6 p-4 bg-teal-50 border border-teal-200 text-teal-800 rounded-xl flex items-center gap-3 animate-fade-in text-sm font-medium">
            <RefreshCw className="w-4 h-4 animate-spin" />
            {scanStatus}
          </div>
        )}

        {/* TAB 1: FEED */}
        {tab === "feed" && (
          <div className="space-y-4">
            {/* Filters Bar */}
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search logs, patients, subjects..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-1.5 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto">
                <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                  <Filter className="w-3.5 h-3.5" /> Channel:
                </span>
                {(["ALL", "WHATSAPP", "EMAIL", "SMS", "IN_APP"] as const).map((ch) => (
                  <button
                    key={ch}
                    onClick={() => setChannelFilter(ch)}
                    className={`px-2.5 py-1 rounded-md text-xs font-medium transition ${
                      channelFilter === ch
                        ? "bg-slate-900 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            {/* List */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm divide-y divide-slate-100 overflow-hidden">
              {filteredNotifs.length === 0 ? (
                <div className="p-12 text-center text-slate-400">
                  <Bell className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm font-medium">No notification records found matching criteria.</p>
                </div>
              ) : (
                filteredNotifs.map((n) => (
                  <div
                    key={n.id}
                    className={`p-4 hover:bg-slate-50/80 transition flex items-start justify-between gap-4 ${
                      !n.is_read ? "bg-teal-50/20" : ""
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-slate-100 rounded-lg mt-0.5">
                        {channelIcon(n.delivery_channel)}
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="text-sm font-semibold text-slate-900">{n.title}</h4>
                          {!n.is_read && (
                            <span className="px-1.5 py-0.2 text-[10px] font-bold bg-teal-600 text-white rounded">
                              NEW
                            </span>
                          )}
                          <span className="text-[11px] px-2 py-0.5 bg-slate-100 text-slate-600 rounded-full font-medium">
                            {n.delivery_channel}
                          </span>
                          {n.priority === "URGENT" && (
                            <span className="text-[11px] px-2 py-0.5 bg-rose-100 text-rose-700 rounded-full font-semibold">
                              URGENT
                            </span>
                          )}
                        </div>
                        <p className="text-sm text-slate-600 mt-1 leading-relaxed">{n.message}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                          {n.patient_name && (
                            <span>
                              Recipient: <strong className="text-slate-700">{n.patient_name}</strong>
                            </span>
                          )}
                          <span>Sent: {new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                          {n.delivered_at && (
                            <span className="flex items-center gap-1 text-emerald-600">
                              <CheckCircle2 className="w-3.5 h-3.5" /> Delivered
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() =>
                        setNotifications(
                          notifications.map((item) => (item.id === n.id ? { ...item, is_read: true } : item))
                        )
                      }
                      className="text-xs text-slate-400 hover:text-slate-700 p-1"
                      title="Mark as read"
                    >
                      <CheckCheck className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* TAB 2: COMPOSE */}
        {tab === "send" && (
          <div className="max-w-2xl mx-auto bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h2 className="text-base font-bold text-slate-900 mb-1">Send Patient or Clinic Broadcast</h2>
            <p className="text-xs text-slate-500 mb-6">Dispatches via selected healthcare communication gateway</p>

            {sendSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Notification queued and sent successfully!
              </div>
            )}

            <form onSubmit={handleSendNotification} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Recipient Patient Name / ID
                </label>
                <input
                  type="text"
                  placeholder="e.g. Donna Noble or P-4401 (leave empty for clinic alert)"
                  value={sendPatient}
                  onChange={(e) => setSendPatient(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Delivery Channel
                  </label>
                  <select
                    value={sendChannel}
                    onChange={(e) => setSendChannel(e.target.value as DeliveryChannel)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="WHATSAPP">WhatsApp Message</option>
                    <option value="EMAIL">Email</option>
                    <option value="SMS">SMS Text</option>
                    <option value="IN_APP">In-App Notification</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Priority
                  </label>
                  <select
                    value={sendPriority}
                    onChange={(e) => setSendPriority(e.target.value as NotificationPriority)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="NORMAL">Normal</option>
                    <option value="HIGH">High (Reminders)</option>
                    <option value="URGENT">Urgent (Clinical Alert)</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Title / Subject
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Treatment Follow-up Check or Post-op Advice"
                  value={sendTitle}
                  onChange={(e) => setSendTitle(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Message Content
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Enter custom clinical instruction or message..."
                  value={sendMessage}
                  onChange={(e) => setSendMessage(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setTab("feed")}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition flex items-center gap-1.5"
                >
                  <Send className="w-4 h-4" /> Dispatch Notification
                </button>
              </div>
            </form>
          </div>
        )}

        {/* TAB 3: TEMPLATES */}
        {tab === "templates" && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockTemplates.map((t) => (
              <div key={t.id} className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold px-2 py-0.5 bg-teal-50 text-teal-700 rounded">
                      {t.channel}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">{t.template_key}</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 mb-1">{t.name}</h3>
                  {t.subject_template && (
                    <p className="text-xs font-medium text-slate-600 mb-2">Subject: {t.subject_template}</p>
                  )}
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs font-mono text-slate-700 mb-3 leading-relaxed">
                    {t.body_template}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] text-slate-400 mb-2">
                    Variables: {Object.keys(t.variables_schema).map((k) => `{{${k}}}`).join(", ")}
                  </p>
                  <button className="w-full py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition">
                    Edit Template
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 4: SCANNERS */}
        {tab === "scanners" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Appointment Reminder Scanner</h3>
                  <p className="text-xs text-slate-500">Multi-interval reminder dispatcher</p>
                </div>
              </div>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                Scans upcoming appointments across 4 strict clinical windows (7 days, 3 days, 24 hours, and 2 hours). Deduplication hashes prevent duplicate messages.
              </p>
              <div className="bg-slate-50 p-3 rounded-lg mb-4 text-xs space-y-1">
                <div className="flex justify-between text-slate-600">
                  <span>7-day Advance notice:</span>
                  <span className="font-semibold text-emerald-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>3-day Confirmation:</span>
                  <span className="font-semibold text-emerald-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>24-hour SMS / WhatsApp:</span>
                  <span className="font-semibold text-emerald-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>2-hour Final alert:</span>
                  <span className="font-semibold text-emerald-600">Active</span>
                </div>
              </div>
              <button
                onClick={() => triggerScanner("reminders")}
                className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-4 h-4" /> Run Appointment Reminder Job
              </button>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-3 bg-teal-50 text-teal-600 rounded-xl">
                  <RefreshCw className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Procedure Recall Scanner</h3>
                  <p className="text-xs text-slate-500">Dental recall follow-up scheduler</p>
                </div>
              </div>
              <p className="text-xs text-slate-600 mb-4 leading-relaxed">
                Scans completed treatments and scheduled follow-ups according to procedure rules (Root Canal: 6 mo, Extraction: 7 days, Scaling: 6 mo, Implant: 90 days).
              </p>
              <div className="bg-slate-50 p-3 rounded-lg mb-4 text-xs space-y-1">
                <div className="flex justify-between text-slate-600">
                  <span>Root Canal Review (180d):</span>
                  <span className="font-semibold text-teal-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Surgical Extraction Check (7d):</span>
                  <span className="font-semibold text-teal-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Prophylaxis & Hygiene (180d):</span>
                  <span className="font-semibold text-teal-600">Active</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Implant Integration (90d):</span>
                  <span className="font-semibold text-teal-600">Active</span>
                </div>
              </div>
              <button
                onClick={() => triggerScanner("recalls")}
                className="w-full py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-sm transition flex items-center justify-center gap-1.5"
              >
                <RefreshCw className="w-4 h-4" /> Run Procedure Recall Job
              </button>
            </div>
          </div>
        )}

        {/* TAB 5: SETTINGS */}
        {tab === "settings" && (
          <div className="max-w-3xl mx-auto bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900">Clinic Channel Gateway Configuration</h2>
              <p className="text-xs text-slate-500">Configure connected external communications providers</p>
            </div>

            <div className="space-y-4 divide-y divide-slate-100">
              <div className="pt-4 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <MessageSquare className="w-4 h-4 text-green-600" /> WhatsApp Business Cloud API
                  </h4>
                  <p className="text-xs text-slate-500">Official Meta Cloud API gateway for instant appointment reminders & two-way chat</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-700 rounded-full">
                  Connected
                </span>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Mail className="w-4 h-4 text-blue-500" /> SendGrid / SMTP Relay
                  </h4>
                  <p className="text-xs text-slate-500">Transactional emails, PDF invoices, and signed consent copies</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-700 rounded-full">
                  Connected
                </span>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Smartphone className="w-4 h-4 text-emerald-500" /> Twilio SMS Gateway
                  </h4>
                  <p className="text-xs text-slate-500">National SMS delivery for critical recalls and booking confirmations</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-700 rounded-full">
                  Connected
                </span>
              </div>

              <div className="pt-4 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                    <Bell className="w-4 h-4 text-teal-600" /> Web Push & Staff In-App
                  </h4>
                  <p className="text-xs text-slate-500">Web browser service worker alerts for reception and chairside staff</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-100 text-emerald-700 rounded-full">
                  Active
                </span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
