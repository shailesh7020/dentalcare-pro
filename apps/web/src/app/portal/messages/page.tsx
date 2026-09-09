"use client";

import React, { useState } from "react";
import {
  MessageSquare,
  Send,
  CheckCheck,
  Paperclip,
  Clock,
  User,
} from "lucide-react";
import { PortalShell } from "../portal-shell";

interface PortalMsg {
  id: string;
  sender: string;
  isStaff: boolean;
  content: string;
  time: string;
}

const mockMessages: PortalMsg[] = [
  {
    id: "pm-1",
    sender: "Dr. David Tennant",
    isStaff: true,
    content: "Hello Donna, checking in to see how your tooth #14 feels after the restoration?",
    time: "10:00 AM",
  },
  {
    id: "pm-2",
    sender: "Donna Noble",
    isStaff: false,
    content: "Doctor, is it normal to have slight sensitivity to cold water after yesterday's composite filling?",
    time: "11:45 AM",
  },
  {
    id: "pm-3",
    sender: "Dr. David Tennant",
    isStaff: true,
    content: "Mild thermal sensitivity for 3-5 days is very common while the pulp settles. If it throbs spontaneously at night, let us know!",
    time: "12:15 PM",
  },
];

export default function PortalMessagesPage() {
  const [messages, setMessages] = useState<PortalMsg[]>(mockMessages);
  const [text, setText] = useState("");

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    const newMsg: PortalMsg = {
      id: "pm-" + Date.now(),
      sender: "Donna Noble",
      isStaff: false,
      content: text.trim(),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages([...messages, newMsg]);
    setText("");
  };

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Direct Chat with Clinic</h1>
          <p className="text-xs text-slate-500">Secure two-way messaging with your dentist and care team</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col h-[600px] overflow-hidden">
        {/* Messages Feed */}
        <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-slate-50/50">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${!m.isStaff ? "items-end" : "items-start"}`}
            >
              <span className="text-[11px] text-slate-400 mb-1 px-1">{m.sender}</span>
              <div
                className={`max-w-md p-3.5 rounded-2xl text-xs leading-relaxed shadow-xs ${
                  !m.isStaff
                    ? "bg-teal-600 text-white rounded-br-none"
                    : "bg-white text-slate-800 border border-slate-200 rounded-bl-none"
                }`}
              >
                {m.content}
              </div>
              <div className="flex items-center gap-1 mt-1 text-[10px] text-slate-400 px-1">
                <span>{m.time}</span>
                {!m.isStaff && <CheckCheck className="w-3.5 h-3.5 text-teal-600" />}
              </div>
            </div>
          ))}
        </div>

        {/* Compose Bar */}
        <form
          onSubmit={handleSend}
          className="p-4 bg-white border-t border-slate-200 flex items-center gap-3"
        >
          <button
            type="button"
            className="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition"
            title="Attach file or photo"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          <input
            type="text"
            placeholder="Type your message or question to the dental team..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="flex-1 px-4 py-2 text-xs border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
          <button
            type="submit"
            disabled={!text.trim()}
            className="p-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl shadow-xs transition"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </PortalShell>
  );
}
