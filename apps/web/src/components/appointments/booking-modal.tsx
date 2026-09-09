"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Search,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface PatientOption {
  id: string;
  first_name: string;
  last_name: string;
  patient_number: string;
  mobile_number: string;
  medical_history?: {
    cardiac_disease?: boolean;
    hypertension?: boolean;
    diabetes?: boolean;
    allergies?: string;
    pregnancy?: boolean;
  };
}

interface DentistOption {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface ChairOption {
  id: string;
  name: string;
  room_number?: string;
  status: string;
}

interface BookingModalProps {
  isOpen: boolean;
  onClose: () => void;
  preselectedPatient?: {
    id: string;
    name: string;
    patientNumber: string;
    alerts?: string[];
  };
  initialDate?: string;
  initialTime?: string;
  initialChairId?: string;
  onSuccess?: () => void;
}

export function BookingModal({
  isOpen,
  onClose,
  preselectedPatient,
  initialDate,
  initialTime,
  initialChairId,
  onSuccess,
}: BookingModalProps) {
  const queryClient = useQueryClient();

  // Form states
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<{
    id: string;
    name: string;
    patientNumber: string;
    alerts?: string[];
  } | null>(preselectedPatient ?? null);

  const [dentistId, setDentistId] = useState("");
  const [chairId, setChairId] = useState(initialChairId ?? "");
  const [appointmentDate, setAppointmentDate] = useState(
    initialDate ?? new Date().toISOString().split("T")[0]
  );
  const [startTime, setStartTime] = useState(initialTime ?? "10:00");
  const [duration, setDuration] = useState<number>(30);
  const [visitType, setVisitType] = useState("CONSULTATION");
  const [priority, setPriority] = useState("NORMAL");
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [notes, setNotes] = useState("");
  const [isEmergencyOverride, setIsEmergencyOverride] = useState(false);
  const [conflictError, setConflictError] = useState<string | null>(null);

  // Query dentists
  const dentistsQuery = useQuery<DentistOption[]>({
    queryKey: ["clinic-dentists"],
    queryFn: async () => {
      const res = await api.get("/dentists");
      return res.data;
    },
    enabled: isOpen,
  });

  // Query chairs
  const chairsQuery = useQuery<ChairOption[]>({
    queryKey: ["clinic-chairs"],
    queryFn: async () => {
      const res = await api.get("/chairs");
      return res.data;
    },
    enabled: isOpen,
  });

  // Derived state: fallback to defaults/props without setState cascading renders
  const effectivePatient = selectedPatient ?? preselectedPatient ?? null;
  const effectiveDentistId = dentistId || (dentistsQuery.data?.[0]?.id ?? "");
  const effectiveChairId = chairId || initialChairId || (chairsQuery.data?.[0]?.id ?? "");
  const effectiveDate = appointmentDate || initialDate || new Date().toISOString().split("T")[0];
  const effectiveStartTime = startTime || initialTime || "10:00";

  // Search patients
  const patientSearchQuery = useQuery<PatientOption[]>({
    queryKey: ["patient-search-booking", patientSearch],
    queryFn: async () => {
      if (!patientSearch.trim()) return [];
      const res = await api.get("/patients", { params: { search: patientSearch.trim(), limit: 5 } });
      return res.data;
    },
    enabled: isOpen && patientSearch.trim().length > 1 && !effectivePatient,
  });

  // Mutation
  const bookMutation = useMutation({
    mutationFn: async () => {
      setConflictError(null);
      if (!effectivePatient) throw new Error("Please select a patient.");
      if (!effectiveDentistId) throw new Error("Please select a dentist.");
      if (!effectiveChairId) throw new Error("Please select a dental chair.");

      const payload = {
        patient_id: effectivePatient.id,
        dentist_id: effectiveDentistId,
        chair_id: effectiveChairId,
        date: effectiveDate,
        start_time: effectiveStartTime.length === 5 ? `${effectiveStartTime}:00` : effectiveStartTime,
        duration: Number(duration),
        visit_type: visitType,
        priority,
        chief_complaint: chiefComplaint || null,
        notes: notes || null,
        is_emergency_override: isEmergencyOverride,
      };

      const res = await api.post("/appointments", payload);
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["calendar-day"] });
      void queryClient.invalidateQueries({ queryKey: ["calendar-week"] });
      void queryClient.invalidateQueries({ queryKey: ["calendar-month"] });
      void queryClient.invalidateQueries({ queryKey: ["appointment-queue"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      if (effectivePatient) {
        void queryClient.invalidateQueries({ queryKey: ["patient-timeline", effectivePatient.id] });
      }
      onClose();
      if (onSuccess) onSuccess();
    },
    onError: (err: unknown) => {
      const axiosErr = err as { response?: { data?: { detail?: string } }; message?: string };
      const msg = axiosErr.response?.data?.detail || axiosErr.message || "Failed to book appointment.";
      setConflictError(msg);
    },
  });

  const durationOptions = [15, 30, 45, 60, 90, 120];

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl">
        <DialogHeader className="border-b border-slate-100 dark:border-slate-800 pb-4">
          <DialogTitle className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Calendar size={20} className="text-teal-600" />
            Book New Appointment
          </DialogTitle>
        </DialogHeader>

        {conflictError && (
          <div className="mt-4 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-3">
            <AlertTriangle className="text-rose-600 shrink-0 mt-0.5" size={16} />
            <div className="flex-1">
              <strong className="font-semibold block mb-1">Scheduling Conflict Detected</strong>
              <p>{conflictError}</p>
              <label className="mt-3 flex items-center gap-2 text-rose-900 font-medium cursor-pointer">
                <input
                  type="checkbox"
                  checked={isEmergencyOverride}
                  onChange={(e) => setIsEmergencyOverride(e.target.checked)}
                  className="rounded text-rose-600 focus:ring-rose-500"
                />
                Override with Emergency Admin Authorization
              </label>
            </div>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            bookMutation.mutate();
          }}
          className="space-y-5 mt-4"
        >
          {/* Patient Selection */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Patient *
            </label>
            {effectivePatient ? (
              <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-teal-700 text-white flex items-center justify-center font-bold text-xs">
                    {effectivePatient.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-teal-950">{effectivePatient.name}</h4>
                    <p className="text-[11px] text-teal-700">{effectivePatient.patientNumber}</p>
                  </div>
                  {effectivePatient.alerts && effectivePatient.alerts.length > 0 && (
                    <div className="flex gap-1 ml-2">
                      {effectivePatient.alerts.map((a, i) => (
                        <Badge key={i} variant="destructive" className="text-[10px] py-0 px-1.5">
                          {a}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
                {!preselectedPatient && (
                  <button
                    type="button"
                    onClick={() => setSelectedPatient(null)}
                    className="text-teal-700 hover:text-teal-900 text-xs flex items-center gap-1 font-medium"
                  >
                    <X size={14} /> Change
                  </button>
                )}
              </div>
            ) : (
              <div className="relative">
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    value={patientSearch}
                    onChange={(e) => setPatientSearch(e.target.value)}
                    placeholder="Search by name, phone, or patient ID..."
                    className="w-full pl-9 pr-3 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 focus:border-transparent"
                  />
                </div>
                {patientSearchQuery.data && patientSearchQuery.data.length > 0 && (
                  <div className="absolute z-20 w-full mt-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xl max-h-56 overflow-y-auto">
                    {patientSearchQuery.data.map((p) => {
                      const fullName = `${p.first_name} ${p.last_name}`;
                      const alerts: string[] = [];
                      if (p.medical_history?.cardiac_disease) alerts.push("Cardiac");
                      if (p.medical_history?.hypertension) alerts.push("High BP");
                      if (p.medical_history?.allergies) alerts.push("Allergy");
                      if (p.medical_history?.pregnancy) alerts.push("Pregnant");

                      return (
                        <button
                          key={p.id}
                          type="button"
                          onClick={() => {
                            setSelectedPatient({
                              id: p.id,
                              name: fullName,
                              patientNumber: p.patient_number,
                              alerts,
                            });
                            setPatientSearch("");
                          }}
                          className="w-full text-left px-3 py-2 text-xs hover:bg-slate-50 dark:hover:bg-slate-800 border-b border-slate-100 dark:border-slate-800 last:border-none flex items-center justify-between text-slate-800 dark:text-slate-200 cursor-pointer"
                        >
                          <div>
                            <span className="font-semibold text-slate-800">{fullName}</span>
                            <span className="text-slate-400 ml-2">({p.patient_number} · {p.mobile_number})</span>
                          </div>
                          {alerts.length > 0 && (
                            <div className="flex gap-1">
                              {alerts.map((a, idx) => (
                                <Badge key={idx} variant="destructive" className="text-[10px] py-0 px-1">
                                  {a}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Clinician & Chair */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Dentist *
              </label>
              <select
                value={effectiveDentistId}
                onChange={(e) => setDentistId(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
              >
                <option value="">Select Dentist</option>
                {dentistsQuery.data?.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dr. {d.first_name} {d.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Dental Chair / Operatory *
              </label>
              <select
                value={effectiveChairId}
                onChange={(e) => setChairId(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
              >
                <option value="">Select Chair</option>
                {chairsQuery.data?.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} {c.room_number ? `(${c.room_number})` : ""}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Date, Time, Duration */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Date *
              </label>
              <input
                type="date"
                value={effectiveDate}
                onChange={(e) => setAppointmentDate(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Start Time *
              </label>
              <input
                type="time"
                value={effectiveStartTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Duration
              </label>
              <div className="flex gap-1">
                {durationOptions.map((mins) => (
                  <button
                    key={mins}
                    type="button"
                    onClick={() => setDuration(mins)}
                    className={`flex-1 py-1.5 text-[11px] font-semibold rounded border transition-colors ${
                      duration === mins
                        ? "bg-teal-700 text-white border-teal-700"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {mins}m
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Visit Type & Priority */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Visit Type *
              </label>
              <select
                value={visitType}
                onChange={(e) => setVisitType(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
              >
                <option value="CONSULTATION">Consultation / Checkup</option>
                <option value="EMERGENCY">Emergency</option>
                <option value="FOLLOW_UP">Follow-up</option>
                <option value="CLEANING">Dental Cleaning (Scaling)</option>
                <option value="ROOT_CANAL">Root Canal Treatment (RCT)</option>
                <option value="EXTRACTION">Extraction</option>
                <option value="CROWN">Crown / Bridge Fitting</option>
                <option value="IMPLANT">Implant</option>
                <option value="SURGERY">Oral Surgery</option>
                <option value="ORTHODONTICS">Orthodontics (Braces)</option>
                <option value="PEDIATRIC">Pediatric Visit</option>
                <option value="OTHER">Other Procedure</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Priority
              </label>
              <div className="flex gap-2">
                {(["NORMAL", "HIGH", "URGENT"] as const).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriority(p)}
                    className={`flex-1 py-2 text-xs font-semibold rounded-lg border transition-colors ${
                      priority === p
                        ? p === "URGENT"
                          ? "bg-rose-600 text-white border-rose-600"
                          : p === "HIGH"
                          ? "bg-amber-600 text-white border-amber-600"
                          : "bg-teal-700 text-white border-teal-700"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Chief Complaint & Notes */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Chief Complaint
            </label>
            <input
              type="text"
              value={chiefComplaint}
              onChange={(e) => setChiefComplaint(e.target.value)}
              placeholder="e.g. Sharp pain in lower right molar, sensitive to cold"
              className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
              Clinical & Administrative Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Internal notes for clinician or reception..."
              className="w-full text-xs px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={bookMutation.isPending || !selectedPatient}
              className="px-5 py-2 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 disabled:opacity-50 rounded-lg shadow-xs flex items-center gap-2"
            >
              {bookMutation.isPending ? "Scheduling..." : "Schedule Appointment"}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
