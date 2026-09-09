"use client";

import Link from "next/link";
import React, { useState } from "react";
import {
  MessageSquare,
  Search,
  Send,
  Paperclip,
  Check,
  CheckCheck,
  User,
  Phone,
  Calendar,
  Clock,
  Plus,
  ArrowLeft,
  Smile,
} from "lucide-react";
import type { ConversationRead, MessageRead } from "./types";

const mockConversations: ConversationRead[] = [
  {
    id: "conv-1",
    clinic_id: "clinic-1",
    conversation_type: "PATIENT_CLINIC",
    patient_id: "p-1",
    patient_name: "Donna Noble",
    title: "Donna Noble (P-4401)",
    is_active: true,
    last_message_at: "2026-09-08T11:45:00Z",
    created_at: "2026-09-01T10:00:00Z",
    unread_count: 1,
    last_message: "Doctor, is it normal to have slight sensitivity after yesterday's composite filling?",
    participants: [
      { id: "part-1", conversation_id: "conv-1", name: "Donna Noble", role: "PATIENT", joined_at: "2026-09-01T10:00:00Z" },
      { id: "part-2", conversation_id: "conv-1", name: "Dr. David Tennant", role: "DENTIST", joined_at: "2026-09-01T10:00:00Z" },
    ],
  },
  {
    id: "conv-2",
    clinic_id: "clinic-1",
    conversation_type: "PATIENT_CLINIC",
    patient_id: "p-2",
    patient_name: "Rose Tyler",
    title: "Rose Tyler (P-4402)",
    is_active: true,
    last_message_at: "2026-09-07T16:20:00Z",
    created_at: "2026-09-02T12:00:00Z",
    unread_count: 0,
    last_message: "Thank you Dr. Iyer, the prescription has been received.",
    participants: [
      { id: "part-3", conversation_id: "conv-2", name: "Rose Tyler", role: "PATIENT", joined_at: "2026-09-02T12:00:00Z" },
      { id: "part-4", conversation_id: "conv-2", name: "Dr. M. Iyer", role: "DENTIST", joined_at: "2026-09-02T12:00:00Z" },
    ],
  },
  {
    id: "conv-3",
    clinic_id: "clinic-1",
    conversation_type: "STAFF_INTERNAL",
    title: "Morning Huddle - Chair Allocation",
    is_active: true,
    last_message_at: "2026-09-08T08:30:00Z",
    created_at: "2026-09-08T08:00:00Z",
    unread_count: 0,
    last_message: "Chair 3 is reserved for the implant surgery from 2 PM onwards.",
    participants: [
      { id: "part-5", conversation_id: "conv-3", name: "Dr. Ananya Shah", role: "ADMIN", joined_at: "2026-09-08T08:00:00Z" },
      { id: "part-6", conversation_id: "conv-3", name: "Reception Desk", role: "RECEPTIONIST", joined_at: "2026-09-08T08:00:00Z" },
    ],
  },
];

const mockInitialMessages: Record<string, MessageRead[]> = {
  "conv-1": [
    {
      id: "m-1",
      conversation_id: "conv-1",
      sender_name: "Dr. David Tennant",
      content: "Hello Donna, checking in to see how your tooth #14 feels after the restoration?",
      is_read: true,
      created_at: "2026-09-08T10:00:00Z",
    },
    {
      id: "m-2",
      conversation_id: "conv-1",
      sender_name: "Donna Noble",
      content: "Doctor, is it normal to have slight sensitivity after yesterday's composite filling?",
      is_read: false,
      created_at: "2026-09-08T11:45:00Z",
    },
  ],
  "conv-2": [
    {
      id: "m-3",
      conversation_id: "conv-2",
      sender_name: "Dr. M. Iyer",
      content: "Hi Rose, your e-prescription for Amoxicillin and Ibuprofen is ready.",
      is_read: true,
      created_at: "2026-09-07T15:00:00Z",
    },
    {
      id: "m-4",
      conversation_id: "conv-2",
      sender_name: "Rose Tyler",
      content: "Thank you Dr. Iyer, the prescription has been received.",
      is_read: true,
      created_at: "2026-09-07T16:20:00Z",
    },
  ],
};

export default function MessagesPage() {
  const [conversations, setConversations] = useState(mockConversations);
  const [activeConvId, setActiveConvId] = useState<string>("conv-1");
  const [messages, setMessages] = useState<Record<string, MessageRead[]>>(mockInitialMessages);
  const [inputText, setInputText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"ALL" | "PATIENT" | "STAFF">("ALL");

  const activeConv = conversations.find((c) => c.id === activeConvId);
  const currentMessages = messages[activeConvId] || [];

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || !activeConvId) return;

    const newMsg: MessageRead = {
      id: "m-" + Date.now(),
      conversation_id: activeConvId,
      sender_name: "Dr. David Tennant",
      content: inputText.trim(),
      is_read: true,
      created_at: new Date().toISOString(),
    };

    setMessages({
      ...messages,
      [activeConvId]: [...(messages[activeConvId] || []), newMsg],
    });

    setConversations(
      conversations.map((c) =>
        c.id === activeConvId
          ? { ...c, last_message: inputText.trim(), last_message_at: new Date().toISOString(), unread_count: 0 }
          : c
      )
    );

    setInputText("");
  };

  const filteredConversations = conversations.filter((c) => {
    if (filterType === "PATIENT" && c.conversation_type !== "PATIENT_CLINIC") return false;
    if (filterType === "STAFF" && c.conversation_type !== "STAFF_INTERNAL") return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        (c.title && c.title.toLowerCase().includes(q)) ||
        (c.patient_name && c.patient_name.toLowerCase().includes(q)) ||
        (c.last_message && c.last_message.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="h-screen flex flex-col bg-slate-100 text-slate-900 overflow-hidden">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/" className="text-sm font-medium text-slate-500 hover:text-slate-900">
            ← Dashboard
          </Link>
          <span className="text-slate-300">/</span>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-teal-50 text-teal-700 rounded-lg">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900">Clinic & Patient Messaging</h1>
              <p className="text-xs text-slate-500">HIPAA/GDPR-compliant two-way dental communication</p>
            </div>
          </div>
        </div>

        <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-lg shadow-sm transition">
          <Plus className="w-4 h-4" /> New Conversation
        </button>
      </header>

      {/* Main Split-Pane */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar: Thread List */}
        <aside className="w-80 lg:w-96 bg-white border-r border-slate-200 flex flex-col shrink-0">
          <div className="p-3 border-b border-slate-200 space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search messages or patients..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <div className="flex gap-1">
              {(["ALL", "PATIENT", "STAFF"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilterType(f)}
                  className={`flex-1 py-1 text-xs font-medium rounded-md transition ${
                    filterType === f ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {f === "ALL" ? "All" : f === "PATIENT" ? "Patients" : "Internal"}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
            {filteredConversations.map((c) => {
              const isSelected = c.id === activeConvId;
              return (
                <button
                  key={c.id}
                  onClick={() => {
                    setActiveConvId(c.id);
                    setConversations(
                      conversations.map((item) => (item.id === c.id ? { ...item, unread_count: 0 } : item))
                    );
                  }}
                  className={`w-full text-left p-3.5 flex items-start gap-3 transition ${
                    isSelected ? "bg-teal-50/50 border-r-4 border-teal-600" : "hover:bg-slate-50"
                  }`}
                >
                  <div className="w-9 h-9 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xs shrink-0">
                    {c.patient_name
                      ? c.patient_name.split(" ").map((n) => n[0]).join("")
                      : "IN"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-900 truncate">{c.title}</h4>
                      <span className="text-[10px] text-slate-400">
                        {c.last_message_at
                          ? new Date(c.last_message_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                          : ""}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 truncate mt-0.5">{c.last_message}</p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded font-medium ${
                          c.conversation_type === "PATIENT_CLINIC"
                            ? "bg-blue-50 text-blue-700"
                            : "bg-purple-50 text-purple-700"
                        }`}
                      >
                        {c.conversation_type === "PATIENT_CLINIC" ? "Patient Chat" : "Staff Internal"}
                      </span>
                      {c.unread_count ? (
                        <span className="px-1.5 py-0.2 bg-teal-600 text-white rounded-full text-[10px] font-bold">
                          {c.unread_count}
                        </span>
                      ) : null}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </aside>

        {/* Center: Active Chat Feed */}
        <section className="flex-1 flex flex-col bg-slate-50 min-w-0">
          {activeConv ? (
            <>
              {/* Thread Header */}
              <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-sm">
                    {activeConv.patient_name
                      ? activeConv.patient_name.split(" ").map((n) => n[0]).join("")
                      : "IN"}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">{activeConv.title}</h3>
                    <p className="text-xs text-slate-500">
                      {activeConv.conversation_type === "PATIENT_CLINIC"
                        ? "Patient direct communication · End-to-end encrypted"
                        : "Staff team channel"}
                    </p>
                  </div>
                </div>

                {activeConv.patient_name && (
                  <Link
                    href={`/patients`}
                    className="px-3 py-1.5 text-xs font-medium text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition"
                  >
                    View Patient Chart
                  </Link>
                )}
              </div>

              {/* Messages Scroll Area */}
              <div className="flex-1 p-6 overflow-y-auto space-y-4">
                <div className="text-center">
                  <span className="px-3 py-1 bg-slate-200/80 text-slate-600 text-[11px] font-medium rounded-full">
                    Conversation encrypted & secured
                  </span>
                </div>

                {currentMessages.map((m) => {
                  const isClinicStaff = m.sender_name?.includes("Dr.") || m.sender_name?.includes("Reception");
                  return (
                    <div
                      key={m.id}
                      className={`flex flex-col ${isClinicStaff ? "items-end" : "items-start"}`}
                    >
                      <span className="text-[11px] text-slate-400 font-medium mb-1 px-1">
                        {m.sender_name}
                      </span>
                      <div
                        className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed shadow-sm ${
                          isClinicStaff
                            ? "bg-teal-600 text-white rounded-br-none"
                            : "bg-white text-slate-800 border border-slate-200 rounded-bl-none"
                        }`}
                      >
                        {m.content}
                      </div>
                      <div className="flex items-center gap-1 mt-1 text-[10px] text-slate-400 px-1">
                        <span>
                          {new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        </span>
                        {isClinicStaff && <CheckCheck className="w-3.5 h-3.5 text-teal-600" />}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Input Compose Bar */}
              <form
                onSubmit={handleSendMessage}
                className="bg-white border-t border-slate-200 p-4 flex items-center gap-3 shrink-0"
              >
                <button
                  type="button"
                  className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
                  title="Attach file or clinical document"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
                <input
                  type="text"
                  placeholder="Type message to patient or staff..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  className="flex-1 px-4 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <button
                  type="submit"
                  disabled={!inputText.trim()}
                  className="p-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl shadow-sm transition"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-sm font-medium">
              Select a conversation to start chatting
            </div>
          )}
        </section>

        {/* Right Sidebar: Quick Patient Insight (if patient chat) */}
        {activeConv?.patient_name && (
          <aside className="w-72 bg-white border-l border-slate-200 p-5 hidden xl:block shrink-0">
            <div className="text-center pb-4 border-b border-slate-100">
              <div className="w-16 h-16 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xl mx-auto mb-2">
                {activeConv.patient_name.split(" ").map((n) => n[0]).join("")}
              </div>
              <h3 className="text-sm font-bold text-slate-900">{activeConv.patient_name}</h3>
              <p className="text-xs text-slate-500">Patient ID: P-4401</p>
            </div>

            <div className="py-4 border-b border-slate-100 space-y-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-600">
                <Phone className="w-4 h-4 text-slate-400" />
                <span>+91 99112 23344</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>Next Appt: Tomorrow, 2:00 PM</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Clock className="w-4 h-4 text-slate-400" />
                <span>Dr. David Tennant</span>
              </div>
            </div>

            <div className="pt-4 space-y-2">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">Quick Actions</h4>
              <Link
                href="/appointments?book=true"
                className="block w-full py-1.5 text-center text-xs font-medium text-teal-700 bg-teal-50 hover:bg-teal-100 rounded-lg transition"
              >
                Schedule Visit
              </Link>
              <Link
                href="/billing/new"
                className="block w-full py-1.5 text-center text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
              >
                Send Payment Request
              </Link>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
