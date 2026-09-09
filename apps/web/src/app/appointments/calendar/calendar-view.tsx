"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  Filter,
  Layers,
  Plus,
  RefreshCw,
  User,
} from "lucide-react";
import { api } from "@/lib/api";
import {
  Appointment,
  AppointmentStatus,
  CalendarDayData,
  CalendarMonthData,
  CalendarWeekData,
  Chair,
  Dentist,
} from "../types";

export type CalendarMode = "day" | "week" | "month";

interface CalendarViewProps {
  onSelectAppointment: (appointment: Appointment) => void;
  onNewBooking: (opts: { date?: string; time?: string; chairId?: string }) => void;
}

export function CalendarView({ onSelectAppointment, onNewBooking }: CalendarViewProps) {
  const [mode, setMode] = useState<CalendarMode>("day");
  const [currentDate, setCurrentDate] = useState<Date>(new Date());
  const [selectedDentistId, setSelectedDentistId] = useState<string>("ALL");
  const [selectedChairId, setSelectedChairId] = useState<string>("ALL");

  // Format date helper: YYYY-MM-DD
  const formatDateISO = (d: Date): string => {
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const currentDateStr = useMemo(() => formatDateISO(currentDate), [currentDate]);

  // Dentists list query
  const dentistsQuery = useQuery({
    queryKey: ["dentists"],
    queryFn: async () => {
      const res = await api.get<Dentist[]>("/dentists");
      return res.data;
    },
  });

  // Chairs list query
  const chairsQuery = useQuery({
    queryKey: ["chairs"],
    queryFn: async () => {
      const res = await api.get<Chair[]>("/chairs");
      return res.data;
    },
  });

  // Day view query
  const dayQuery = useQuery({
    queryKey: ["calendar-day", currentDateStr],
    queryFn: async () => {
      const res = await api.get<CalendarDayData>("/calendar/day", {
        params: { target_date: currentDateStr },
      });
      return res.data;
    },
    enabled: mode === "day",
  });

  // Week calculation (Monday - Sunday)
  const weekRange = useMemo(() => {
    const d = new Date(currentDate);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 1); // adjust when day is sunday
    const monday = new Date(d.setDate(diff));
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);
    return {
      start: formatDateISO(monday),
      end: formatDateISO(sunday),
      startDate: monday,
    };
  }, [currentDate]);

  const weekQuery = useQuery({
    queryKey: ["calendar-week", weekRange.start],
    queryFn: async () => {
      const res = await api.get<CalendarWeekData>("/calendar/week", {
        params: { start_date: weekRange.start },
      });
      return res.data;
    },
    enabled: mode === "week",
  });

  // Month calculation
  const monthParams = useMemo(() => {
    return {
      year: currentDate.getFullYear(),
      month: currentDate.getMonth() + 1,
    };
  }, [currentDate]);

  const monthQuery = useQuery({
    queryKey: ["calendar-month", monthParams.year, monthParams.month],
    queryFn: async () => {
      const res = await api.get<CalendarMonthData>("/calendar/month", {
        params: { year: monthParams.year, month: monthParams.month },
      });
      return res.data;
    },
    enabled: mode === "month",
  });

  // Navigation handlers
  const handlePrev = () => {
    const next = new Date(currentDate);
    if (mode === "day") {
      next.setDate(next.getDate() - 1);
    } else if (mode === "week") {
      next.setDate(next.getDate() - 7);
    } else {
      next.setMonth(next.getMonth() - 1);
    }
    setCurrentDate(next);
  };

  const handleNext = () => {
    const next = new Date(currentDate);
    if (mode === "day") {
      next.setDate(next.getDate() + 1);
    } else if (mode === "week") {
      next.setDate(next.getDate() + 7);
    } else {
      next.setMonth(next.getMonth() + 1);
    }
    setCurrentDate(next);
  };

  const handleToday = () => {
    setCurrentDate(new Date());
  };

  // Status badge styling
  const getStatusBadge = (status: AppointmentStatus) => {
    switch (status) {
      case "SCHEDULED":
        return {
          bg: "bg-sky-50 border-sky-200 text-sky-800",
          dot: "bg-sky-500",
          label: "Scheduled",
        };
      case "CONFIRMED":
        return {
          bg: "bg-indigo-50 border-indigo-200 text-indigo-800",
          dot: "bg-indigo-500",
          label: "Confirmed",
        };
      case "CHECKED_IN":
        return {
          bg: "bg-amber-50 border-amber-200 text-amber-800",
          dot: "bg-amber-500",
          label: "In Lobby",
        };
      case "IN_CHAIR":
        return {
          bg: "bg-purple-50 border-purple-200 text-purple-800",
          dot: "bg-purple-500",
          label: "In Treatment",
        };
      case "COMPLETED":
        return {
          bg: "bg-emerald-50 border-emerald-200 text-emerald-800",
          dot: "bg-emerald-500",
          label: "Completed",
        };
      case "CANCELLED":
        return {
          bg: "bg-rose-50 border-rose-200 text-rose-800 line-through opacity-75",
          dot: "bg-rose-500",
          label: "Cancelled",
        };
      case "NO_SHOW":
        return {
          bg: "bg-slate-100 border-slate-300 text-slate-700 opacity-75",
          dot: "bg-slate-400",
          label: "No Show",
        };
      default:
        return {
          bg: "bg-slate-50 border-slate-200 text-slate-800",
          dot: "bg-slate-400",
          label: status,
        };
    }
  };

  // Visit type chip color
  const getVisitTypeBadge = (type: string) => {
    switch (type) {
      case "EMERGENCY":
        return "bg-rose-100 text-rose-800 border-rose-300 font-bold";
      case "SURGERY":
        return "bg-red-50 text-red-700 border-red-200";
      case "PROCEDURE":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "CLEANING":
        return "bg-teal-50 text-teal-700 border-teal-200";
      case "CHECKUP":
        return "bg-cyan-50 text-cyan-700 border-cyan-200";
      case "FOLLOW_UP":
        return "bg-violet-50 text-violet-700 border-violet-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  // Filter appointments by selected dentist and chair
  const filterAppointments = (items: Appointment[]) => {
    return items.filter((apt) => {
      if (selectedDentistId !== "ALL" && apt.dentist_id !== selectedDentistId) return false;
      if (selectedChairId !== "ALL" && apt.chair_id !== selectedChairId) return false;
      return true;
    });
  };

  // Time slots for Day and Week views (08:00 to 19:00 in 30-min increments)
  const timeSlots = useMemo(() => {
    const slots: string[] = [];
    for (let hour = 8; hour <= 19; hour++) {
      slots.push(`${String(hour).padStart(2, "0")}:00`);
      slots.push(`${String(hour).padStart(2, "0")}:30`);
    }
    return slots;
  }, []);

  // Title formatting
  const displayTitle = useMemo(() => {
    if (mode === "day") {
      return currentDate.toLocaleDateString("en-US", {
        weekday: "long",
        month: "long",
        day: "numeric",
        year: "numeric",
      });
    } else if (mode === "week") {
      const start = new Date(weekRange.startDate);
      const end = new Date(weekRange.startDate);
      end.setDate(start.getDate() + 6);
      return `${start.toLocaleDateString("en-US", { month: "short", day: "numeric" })} - ${end.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}`;
    } else {
      return currentDate.toLocaleDateString("en-US", {
        month: "long",
        year: "numeric",
      });
    }
  }, [mode, currentDate, weekRange]);

  const chairs = chairsQuery.data ?? [];
  const dentists = dentistsQuery.data ?? [];

  return (
    <div className="space-y-4">
      {/* Calendar Control Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Navigation & Title */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center border border-slate-200 rounded-lg overflow-hidden shadow-2xs">
            <button
              onClick={handlePrev}
              className="p-2 bg-white hover:bg-slate-50 text-slate-600 transition-colors border-r border-slate-200"
              aria-label="Previous date"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={handleToday}
              className="px-3 py-1.5 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors"
            >
              Today
            </button>
            <button
              onClick={handleNext}
              className="p-2 bg-white hover:bg-slate-50 text-slate-600 transition-colors border-l border-slate-200"
              aria-label="Next date"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CalendarIcon size={18} className="text-teal-600" />
            {displayTitle}
          </h2>
        </div>

        {/* Right: Filters, Mode Switch & Book CTA */}
        <div className="flex items-center gap-3 flex-wrap">
          {/* Dentist Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <User size={13} className="text-slate-400" />
            <select
              value={selectedDentistId}
              onChange={(e) => setSelectedDentistId(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
              aria-label="Filter by Clinician"
            >
              <option value="ALL">All Clinicians</option>
              {dentists.map((dentist) => (
                <option key={dentist.id} value={dentist.id}>
                  Dr. {dentist.first_name} {dentist.last_name}
                </option>
              ))}
            </select>
          </div>

          {/* Chair Filter */}
          <div className="flex items-center gap-1.5 text-xs">
            <Layers size={13} className="text-slate-400" />
            <select
              value={selectedChairId}
              onChange={(e) => setSelectedChairId(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
              aria-label="Filter by Chair"
            >
              <option value="ALL">All Operatories</option>
              {chairs.map((chair) => (
                <option key={chair.id} value={chair.id}>
                  {chair.name}
                </option>
              ))}
            </select>
          </div>

          {/* View Mode Buttons */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setMode("day")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                mode === "day"
                  ? "bg-white text-teal-700 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Day (Chairs)
            </button>
            <button
              onClick={() => setMode("week")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                mode === "week"
                  ? "bg-white text-teal-700 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setMode("month")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                mode === "month"
                  ? "bg-white text-teal-700 shadow-2xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Month
            </button>
          </div>

          {/* New Booking CTA */}
          <button
            onClick={() => onNewBooking({ date: currentDateStr })}
            className="inline-flex items-center gap-1 px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors"
          >
            <Plus size={14} /> Book Visit
          </button>
        </div>
      </div>

      {/* VIEW: DAY VIEW (Operatories / Chairs) */}
      {mode === "day" && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          {dayQuery.isLoading ? (
            <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
              <RefreshCw size={16} className="animate-spin text-teal-600" />
              Loading operatory calendar...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-[800px]">
                {/* Chair Headers */}
                <div
                  className="grid border-b border-slate-200 bg-slate-50/80 sticky top-0 z-10"
                  style={{
                    gridTemplateColumns: `100px repeat(${Math.max(
                      1,
                      (dayQuery.data?.chairs ?? []).filter(
                        (c) => selectedChairId === "ALL" || c.id === selectedChairId
                      ).length
                    )}, minmax(220px, 1fr))`,
                  }}
                >
                  <div className="p-3 text-xs font-bold text-slate-500 uppercase tracking-wider border-r border-slate-200 flex items-center justify-center">
                    Time
                  </div>
                  {(dayQuery.data?.chairs ?? [])
                    .filter((c) => selectedChairId === "ALL" || c.id === selectedChairId)
                    .map((chair) => (
                      <div
                        key={chair.id}
                        className="p-3 border-r border-slate-200 last:border-r-0 flex items-center justify-between"
                      >
                        <div>
                          <h3 className="text-xs font-bold text-slate-900">{chair.name}</h3>
                          {chair.room_number && (
                            <p className="text-[11px] text-slate-500">Room: {chair.room_number}</p>
                          )}
                        </div>
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                            chair.status === "ACTIVE"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-amber-50 text-amber-700 border-amber-200"
                          }`}
                        >
                          {chair.status}
                        </span>
                      </div>
                    ))}
                </div>

                {/* Day Time Rows */}
                <div className="divide-y divide-slate-100">
                  {timeSlots.map((timeSlot) => {
                    const activeChairs = (dayQuery.data?.chairs ?? []).filter(
                      (c) => selectedChairId === "ALL" || c.id === selectedChairId
                    );

                    return (
                      <div
                        key={timeSlot}
                        className="grid hover:bg-slate-50/30 transition-colors"
                        style={{
                          gridTemplateColumns: `100px repeat(${Math.max(
                            1,
                            activeChairs.length
                          )}, minmax(220px, 1fr))`,
                        }}
                      >
                        {/* Time label */}
                        <div className="p-2.5 text-xs font-mono text-slate-500 border-r border-slate-200 text-center flex items-center justify-center bg-slate-50/40">
                          {timeSlot}
                        </div>

                        {/* Chair cells */}
                        {activeChairs.map((chair) => {
                          // Find appointment starting at this time slot in this chair
                          const matchingApt = filterAppointments(
                            dayQuery.data?.appointments ?? []
                          ).find(
                            (apt) =>
                              apt.chair_id === chair.id &&
                              apt.start_time.slice(0, 5) === timeSlot
                          );

                          // Also check if slot falls inside an ongoing appointment (starts earlier)
                          const ongoingApt = filterAppointments(
                            dayQuery.data?.appointments ?? []
                          ).find((apt) => {
                            if (apt.chair_id !== chair.id) return false;
                            const aptStart = apt.start_time.slice(0, 5);
                            const aptEnd = apt.end_time.slice(0, 5);
                            return timeSlot > aptStart && timeSlot < aptEnd;
                          });

                          return (
                            <div
                              key={chair.id}
                              className="p-1.5 border-r border-slate-200 last:border-r-0 min-h-[56px] relative group"
                            >
                              {matchingApt ? (
                                <button
                                  onClick={() => onSelectAppointment(matchingApt)}
                                  className={`w-full text-left p-2.5 rounded-lg border shadow-xs transition-all hover:shadow-md ${
                                    getStatusBadge(matchingApt.status).bg
                                  }`}
                                >
                                  <div className="flex items-center justify-between gap-1 mb-1">
                                    <span className="font-bold text-xs truncate text-slate-900">
                                      {matchingApt.patient_name || "Patient"}
                                    </span>
                                    <span
                                      className={`text-[9px] uppercase px-1.5 py-0.5 rounded border ${getVisitTypeBadge(
                                        matchingApt.visit_type
                                      )}`}
                                    >
                                      {matchingApt.visit_type}
                                    </span>
                                  </div>

                                  <div className="flex items-center justify-between text-[11px] text-slate-600">
                                    <span className="flex items-center gap-1 font-mono">
                                      <Clock size={11} className="text-slate-400" />
                                      {matchingApt.start_time.slice(0, 5)} -{" "}
                                      {matchingApt.end_time.slice(0, 5)} ({matchingApt.duration}m)
                                    </span>
                                    <span className="truncate max-w-[90px] text-slate-500">
                                      Dr. {matchingApt.dentist_name?.split(" ").pop()}
                                    </span>
                                  </div>

                                  {matchingApt.chief_complaint && (
                                    <p className="text-[11px] text-slate-500 truncate mt-1 italic">
                                      &ldquo;{matchingApt.chief_complaint}&rdquo;
                                    </p>
                                  )}

                                  {matchingApt.is_emergency_override && (
                                    <div className="mt-1 inline-flex items-center gap-1 text-[10px] text-rose-700 font-bold bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                                      <AlertTriangle size={10} /> Emergency Override
                                    </div>
                                  )}
                                </button>
                              ) : ongoingApt ? (
                                <div className="h-full bg-slate-50/60 border border-dashed border-slate-200 rounded-lg flex items-center justify-center text-[10px] text-slate-400 italic">
                                  In progress ({ongoingApt.patient_name})
                                </div>
                              ) : (
                                <button
                                  onClick={() =>
                                    onNewBooking({
                                      date: currentDateStr,
                                      time: timeSlot,
                                      chairId: chair.id,
                                    })
                                  }
                                  className="w-full h-full min-h-[44px] rounded-lg border border-transparent hover:border-teal-200 hover:bg-teal-50/40 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100 text-teal-700 text-xs font-medium gap-1"
                                >
                                  <Plus size={12} /> Book slot
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW: WEEK VIEW */}
      {mode === "week" && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          {weekQuery.isLoading ? (
            <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
              <RefreshCw size={16} className="animate-spin text-teal-600" />
              Loading weekly schedule...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <div className="min-w-[900px]">
                {/* 7 Days Header */}
                <div className="grid grid-cols-8 border-b border-slate-200 bg-slate-50/80 sticky top-0 z-10">
                  <div className="p-3 text-xs font-bold text-slate-500 uppercase tracking-wider border-r border-slate-200 text-center">
                    Time
                  </div>
                  {Array.from({ length: 7 }).map((_, idx) => {
                    const dayDate = new Date(weekRange.startDate);
                    dayDate.setDate(dayDate.getDate() + idx);
                    const dayStr = formatDateISO(dayDate);
                    const isToday = formatDateISO(new Date()) === dayStr;

                    return (
                      <div
                        key={dayStr}
                        className={`p-3 border-r border-slate-200 last:border-r-0 text-center ${
                          isToday ? "bg-teal-50/70" : ""
                        }`}
                      >
                        <div className="text-xs font-semibold text-slate-500 uppercase">
                          {dayDate.toLocaleDateString("en-US", { weekday: "short" })}
                        </div>
                        <div
                          className={`text-sm font-bold mt-0.5 ${
                            isToday ? "text-teal-700" : "text-slate-900"
                          }`}
                        >
                          {dayDate.getDate()}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Week Time Rows */}
                <div className="divide-y divide-slate-100">
                  {timeSlots.map((timeSlot) => (
                    <div key={timeSlot} className="grid grid-cols-8 hover:bg-slate-50/30">
                      <div className="p-2 text-xs font-mono text-slate-500 border-r border-slate-200 text-center flex items-center justify-center bg-slate-50/40">
                        {timeSlot}
                      </div>

                      {Array.from({ length: 7 }).map((_, idx) => {
                        const dayDate = new Date(weekRange.startDate);
                        dayDate.setDate(dayDate.getDate() + idx);
                        const dayStr = formatDateISO(dayDate);

                        const matchingApts = filterAppointments(
                          weekQuery.data?.appointments ?? []
                        ).filter(
                          (apt) => apt.date === dayStr && apt.start_time.slice(0, 5) === timeSlot
                        );

                        return (
                          <div
                            key={dayStr}
                            className="p-1 border-r border-slate-200 last:border-r-0 min-h-[50px] relative group"
                          >
                            {matchingApts.length > 0 ? (
                              matchingApts.map((apt) => (
                                <button
                                  key={apt.id}
                                  onClick={() => onSelectAppointment(apt)}
                                  className={`w-full text-left p-1.5 mb-1 rounded border shadow-2xs transition-all hover:scale-[1.01] ${
                                    getStatusBadge(apt.status).bg
                                  }`}
                                >
                                  <div className="font-bold text-[11px] truncate text-slate-900">
                                    {apt.patient_name}
                                  </div>
                                  <div className="text-[10px] text-slate-500 truncate flex items-center justify-between">
                                    <span>{apt.chair_name?.split(" - ")[0]}</span>
                                    <span>{apt.duration}m</span>
                                  </div>
                                </button>
                              ))
                            ) : (
                              <button
                                onClick={() =>
                                  onNewBooking({
                                    date: dayStr,
                                    time: timeSlot,
                                  })
                                }
                                className="w-full h-full min-h-[40px] rounded border border-transparent hover:border-teal-200 hover:bg-teal-50/40 opacity-0 group-hover:opacity-100 text-teal-700 text-[10px] font-medium flex items-center justify-center"
                              >
                                + Book
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW: MONTH VIEW */}
      {mode === "month" && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          {monthQuery.isLoading ? (
            <div className="p-12 text-center text-slate-500 text-sm flex items-center justify-center gap-2">
              <RefreshCw size={16} className="animate-spin text-teal-600" />
              Loading monthly calendar...
            </div>
          ) : (
            <div>
              {/* Day of week headers */}
              <div className="grid grid-cols-7 border-b border-slate-200 bg-slate-50 text-center text-xs font-bold text-slate-500 uppercase tracking-wider py-2.5">
                <div>Sun</div>
                <div>Mon</div>
                <div>Tue</div>
                <div>Wed</div>
                <div>Thu</div>
                <div>Fri</div>
                <div>Sat</div>
              </div>

              {/* Month Grid Cells */}
              <div className="grid grid-cols-7 divide-x divide-y divide-slate-200 border-b border-slate-200">
                {(() => {
                  const year = monthParams.year;
                  const month = monthParams.month - 1;
                  const firstDay = new Date(year, month, 1);
                  const lastDay = new Date(year, month + 1, 0);
                  const totalDays = lastDay.getDate();
                  const startOffset = firstDay.getDay();

                  const cells = [];

                  // Leading empty cells
                  for (let i = 0; i < startOffset; i++) {
                    cells.push(
                      <div
                        key={`empty-${i}`}
                        className="bg-slate-50/40 min-h-[110px] p-2 text-slate-300"
                      />
                    );
                  }

                  // Day cells
                  for (let d = 1; d <= totalDays; d++) {
                    const currentCellDate = new Date(year, month, d);
                    const dateStr = formatDateISO(currentCellDate);
                    const isToday = formatDateISO(new Date()) === dateStr;

                    const dayApts = filterAppointments(
                      monthQuery.data?.appointments ?? []
                    ).filter((a) => a.date === dateStr);

                    cells.push(
                      <div
                        key={dateStr}
                        className={`min-h-[110px] p-2 relative group flex flex-col justify-between ${
                          isToday ? "bg-teal-50/30" : "hover:bg-slate-50/50"
                        }`}
                      >
                        {/* Day header */}
                        <div className="flex items-center justify-between mb-1.5">
                          <span
                            className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center ${
                              isToday
                                ? "bg-teal-600 text-white shadow-2xs"
                                : "text-slate-700"
                            }`}
                          >
                            {d}
                          </span>
                          {dayApts.length > 0 && (
                            <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded border border-teal-200">
                              {dayApts.length} {dayApts.length === 1 ? "apt" : "apts"}
                            </span>
                          )}
                        </div>

                        {/* Appointments mini pills */}
                        <div className="space-y-1 overflow-y-auto max-h-[80px]">
                          {dayApts.slice(0, 3).map((apt) => (
                            <button
                              key={apt.id}
                              onClick={() => onSelectAppointment(apt)}
                              className={`w-full text-left px-1.5 py-0.5 rounded text-[11px] font-medium border flex items-center justify-between gap-1 truncate ${
                                getStatusBadge(apt.status).bg
                              }`}
                            >
                              <span className="truncate font-semibold text-slate-900">
                                {apt.start_time.slice(0, 5)} {apt.patient_name}
                              </span>
                              <span
                                className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                  getStatusBadge(apt.status).dot
                                }`}
                              />
                            </button>
                          ))}
                          {dayApts.length > 3 && (
                            <div className="text-[10px] text-slate-500 font-medium text-center">
                              +{dayApts.length - 3} more
                            </div>
                          )}
                        </div>

                        {/* Quick Add trigger on hover */}
                        <button
                          onClick={() => onNewBooking({ date: dateStr })}
                          className="mt-1 w-full py-0.5 text-[10px] text-teal-700 font-semibold rounded hover:bg-teal-100 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-0.5"
                        >
                          <Plus size={10} /> Add
                        </button>
                      </div>
                    );
                  }

                  return cells;
                })()}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
