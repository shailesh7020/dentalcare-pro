"use client";

import { useState } from "react";
import {
  Megaphone,
  Plus,
  AlertCircle,
  Bell,
  Radio,
  CheckCircle2,
} from "lucide-react";
import { EnterpriseNav } from "../nav";
import { AnnouncementScope, AnnouncementType, EnterpriseAnnouncement } from "../types";

const INITIAL_ANNOUNCEMENTS: EnterpriseAnnouncement[] = [
  {
    id: "ann-1",
    organization_id: "org-1",
    title: "Annual Accreditation & Infection Control Audit",
    message: "All branch heads must submit biological sterilization test logs by Friday 5 PM.",
    announcement_type: "BROADCAST",
    target_scope: "ALL",
    is_active: true,
    created_at: "2026-09-08T09:00:00Z",
    updated_at: "2026-09-08T09:00:00Z",
  },
  {
    id: "ann-2",
    organization_id: "org-1",
    title: "Water Main Supply Notice: South Hub Clinics",
    message: "Municipal maintenance scheduled in Indiranagar; backup reverse-osmosis autoclaves activated.",
    announcement_type: "BRANCH_ALERT",
    target_scope: "REGION",
    is_active: true,
    created_at: "2026-09-07T14:00:00Z",
    updated_at: "2026-09-07T14:00:00Z",
  },
];

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState<EnterpriseAnnouncement[]>(INITIAL_ANNOUNCEMENTS);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    message: "",
    announcement_type: "BROADCAST" as AnnouncementType,
    target_scope: "ALL" as AnnouncementScope,
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.title || !formData.message) return;

    const newAnn: EnterpriseAnnouncement = {
      id: `ann-${Date.now()}`,
      organization_id: "org-1",
      title: formData.title,
      message: formData.message,
      announcement_type: formData.announcement_type,
      target_scope: formData.target_scope,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setAnnouncements([newAnn, ...announcements]);
    setShowModal(false);
    setFormData({
      title: "",
      message: "",
      announcement_type: "BROADCAST",
      target_scope: "ALL",
    });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Corporate Announcements & Emergency Broadcasts</h1>
            <p className="text-xs text-slate-500 mt-1">
              Distribute administrative memos, regional directives, and clinical alerts to branch practice teams.
            </p>
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            Publish Announcement
          </button>
        </div>

        <div className="space-y-4">
          {announcements.map((ann) => (
            <div
              key={ann.id}
              className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`p-2 rounded-lg ${
                      ann.announcement_type === "EMERGENCY"
                        ? "bg-rose-50 text-rose-600"
                        : "bg-indigo-50 text-indigo-600"
                    }`}
                  >
                    <Megaphone className="w-4 h-4" />
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-900 text-sm">{ann.title}</h2>
                    <span className="text-[11px] text-slate-400">
                      Scope: {ann.target_scope} • Type: {ann.announcement_type}
                    </span>
                  </div>
                </div>

                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" /> Live
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed pl-10">{ann.message}</p>
            </div>
          ))}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-6 space-y-4">
              <h2 className="text-lg font-bold text-slate-900">Publish Corporate Notice</h2>
              <form onSubmit={handleCreate} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Headline / Title</label>
                  <input
                    type="text"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="e.g. Q4 Regional Dentists Forum"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Notice Type</label>
                    <select
                      value={formData.announcement_type}
                      onChange={(e) =>
                        setFormData({ ...formData, announcement_type: e.target.value as AnnouncementType })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    >
                      <option value="BROADCAST">BROADCAST</option>
                      <option value="REGIONAL">REGIONAL</option>
                      <option value="BRANCH_ALERT">BRANCH_ALERT</option>
                      <option value="EMERGENCY">EMERGENCY</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Scope</label>
                    <select
                      value={formData.target_scope}
                      onChange={(e) =>
                        setFormData({ ...formData, target_scope: e.target.value as AnnouncementScope })
                      }
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    >
                      <option value="ALL">ALL (Entire Network)</option>
                      <option value="REGION">REGION</option>
                      <option value="BRANCH">BRANCH</option>
                      <option value="ROLE">ROLE</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Message Content</label>
                  <textarea
                    required
                    rows={3}
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    placeholder="Provide full details of policy change or announcement..."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-semibold shadow-xs"
                  >
                    Broadcast
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
