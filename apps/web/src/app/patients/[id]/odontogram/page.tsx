"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  DentitionType,
  NumberingSystem,
  PatientOdontogram,
  Tooth,
  ToothSurfaceEnum,
} from "./types";
import { OdontogramCanvas } from "@/components/odontogram/odontogram-canvas";
import { ClinicalToolbar, ActiveAction } from "@/components/odontogram/clinical-toolbar";
import { ToothDetailPanel } from "@/components/odontogram/tooth-detail-panel";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft,
  Activity,
  AlertTriangle,
  HeartPulse,
  Sparkles,
  FileCheck,
} from "lucide-react";

export default function OdontogramPage() {
  const params = useParams();
  const id = params?.id as string;
  const queryClient = useQueryClient();

  const [dentitionType, setDentitionType] = useState<DentitionType>("ADULT");
  const [numberingSystem, setNumberingSystem] = useState<NumberingSystem>("FDI");
  const [selectedToothId, setSelectedToothId] = useState<string | null>(null);
  const [selectedSurfaces, setSelectedSurfaces] = useState<ToothSurfaceEnum[]>([]);
  const [activeAction, setActiveAction] = useState<ActiveAction | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  // 1. Fetch Odontogram Data
  const odontogramQuery = useQuery<PatientOdontogram>({
    queryKey: ["odontogram", id, dentitionType],
    queryFn: async () => {
      const res = await api.get(`/patients/${id}/odontogram`, {
        params: { dentition: dentitionType },
      });
      return res.data;
    },
    enabled: Boolean(id),
  });

  const selectedTooth =
    odontogramQuery.data?.teeth.find((t) => t.id === selectedToothId) || null;

  // 2. Mutations
  const updateToothMutation = useMutation({
    mutationFn: async ({
      toothId,
      status,
      notes,
    }: {
      toothId: string;
      status: string;
      notes?: string;
    }) => {
      const payload: Record<string, unknown> = { primary_status: status };
      if (status === "EXTRACTION") payload.is_extracted = true;
      if (status === "IMPLANT") payload.has_implant = true;
      if (status === "CROWN") payload.has_crown = true;
      if (notes) payload.notes = notes;

      await api.patch(`/teeth/${toothId}`, payload);
    },
    onSuccess: () => {
      showToast("Tooth status successfully updated.");
      void queryClient.invalidateQueries({ queryKey: ["odontogram", id] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Clinical validation error.";
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 5000);
    },
  });

  const updateSurfaceMutation = useMutation({
    mutationFn: async ({
      toothId,
      surface,
      condition,
      treatment,
    }: {
      toothId: string;
      surface: ToothSurfaceEnum;
      condition: string;
      treatment: string;
    }) => {
      await api.patch(`/teeth/${toothId}/surfaces/${surface}`, {
        condition,
        treatment,
      });
    },
    onSuccess: () => {
      showToast("Surface condition recorded.");
      void queryClient.invalidateQueries({ queryKey: ["odontogram", id] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to update surface.";
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 5000);
    },
  });

  const addConditionMutation = useMutation({
    mutationFn: async ({
      toothId,
      condition,
      surfaces,
    }: {
      toothId: string;
      condition: string;
      surfaces: ToothSurfaceEnum[];
    }) => {
      await api.post(`/teeth/${toothId}/conditions`, {
        condition,
        surfaces: surfaces.length > 0 ? surfaces : undefined,
      });
    },
    onSuccess: () => {
      showToast("Clinical condition charted.");
      void queryClient.invalidateQueries({ queryKey: ["odontogram", id] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Validation error applying condition.";
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 5000);
    },
  });

  const addProcedureMutation = useMutation({
    mutationFn: async ({
      toothId,
      procedureName,
      procedureType,
      surfaces,
    }: {
      toothId: string;
      procedureName: string;
      procedureType: string;
      surfaces: ToothSurfaceEnum[];
    }) => {
      await api.post(`/teeth/${toothId}/procedures`, {
        procedure_name: procedureName,
        procedure_type: procedureType,
        surfaces: surfaces.length > 0 ? surfaces : undefined,
      });
    },
    onSuccess: () => {
      showToast("Procedure charted successfully.");
      void queryClient.invalidateQueries({ queryKey: ["odontogram", id] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Validation error charting procedure.";
      setErrorMessage(msg);
      setTimeout(() => setErrorMessage(null), 5000);
    },
  });

  // Handle toolbar application
  const handleApplyToolbarAction = () => {
    if (!selectedTooth || !activeAction) return;

    if (activeAction.category === "CONDITION") {
      addConditionMutation.mutate({
        toothId: selectedTooth.id,
        condition: activeAction.code,
        surfaces: selectedSurfaces,
      });
    } else if (activeAction.category === "PROCEDURE") {
      addProcedureMutation.mutate({
        toothId: selectedTooth.id,
        procedureName: activeAction.label,
        procedureType: activeAction.procedureType || activeAction.code,
        surfaces: selectedSurfaces,
      });
    }
  };

  const handleToggleSurface = (surface: ToothSurfaceEnum) => {
    setSelectedSurfaces((prev) =>
      prev.includes(surface) ? prev.filter((s) => s !== surface) : [...prev, surface]
    );
  };

  if (odontogramQuery.isLoading) {
    return (
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-24 w-full rounded-lg" />
        <Skeleton className="h-96 w-full rounded-lg" />
      </main>
    );
  }

  if (odontogramQuery.isError || !odontogramQuery.data) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-base font-semibold text-rose-600">Odontogram record unavailable</p>
        <p className="text-xs text-slate-500 mt-1">Patient record not found or access denied.</p>
        <Link href={`/patients/${id}`} className="mt-4 inline-block text-xs font-semibold text-teal-700 underline">
          Back to Patient Profile
        </Link>
      </main>
    );
  }

  const { patient_name, patient_number, teeth, stats } = odontogramQuery.data;

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-5">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 px-4 py-2.5 bg-slate-900 text-white text-xs font-semibold rounded-lg shadow-xl animate-fade-in flex items-center gap-2">
          <Sparkles size={14} className="text-teal-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Error Alert Bar */}
      {errorMessage && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-lg flex items-center gap-2">
          <AlertTriangle size={16} className="text-rose-600 shrink-0" />
          <span className="font-semibold">{errorMessage}</span>
        </div>
      )}

      {/* Top Breadcrumb & Patient Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <Link
            href={`/patients/${id}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800 mb-2 transition-colors"
          >
            <ArrowLeft size={13} /> Back to Patient Profile
          </Link>
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl font-bold text-slate-900">{patient_name}</h1>
            <Badge variant="secondary" className="font-mono text-xs">
              {patient_number}
            </Badge>
            <Badge variant="active" className="text-xs">
              Interactive Odontogram (Dental Chart)
            </Badge>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Permanent Visual Electronic Dental Record (EDR) · Independent 8-Surface Charting
          </p>
        </div>

        {/* Quick Treatment Link */}
        <div className="flex items-center gap-2.5">
          <Link
            href={`/treatments/new?patient_id=${id}`}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs rounded-md shadow-xs transition-colors"
          >
            <FileCheck size={14} /> Start New Treatment
          </Link>
        </div>
      </div>

      {/* Live Odontogram KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 flex items-center gap-1">
            <Activity size={12} /> Active Caries
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.active_caries}</p>
        </div>
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1">
            Missing Teeth
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.missing_teeth}</p>
        </div>
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-purple-600 flex items-center gap-1">
            Root Canals
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.root_canals}</p>
        </div>
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 flex items-center gap-1">
            Crowns
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.crowns}</p>
        </div>
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1">
            Implants
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.implants}</p>
        </div>
        <div className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1">
            Restorations
          </span>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats.restorations}</p>
        </div>
      </div>

      {/* Clinical Charting Toolbar */}
      <ClinicalToolbar
        selectedTooth={selectedTooth}
        selectedSurfaces={selectedSurfaces}
        activeAction={activeAction}
        onSelectAction={setActiveAction}
        onToggleSurface={handleToggleSurface}
        onApplyAction={handleApplyToolbarAction}
        onClearSelection={() => {
          setSelectedToothId(null);
          setSelectedSurfaces([]);
          setActiveAction(null);
        }}
        isApplying={
          updateToothMutation.isPending ||
          addConditionMutation.isPending ||
          addProcedureMutation.isPending
        }
      />

      {/* Main Workspace Layout (Canvas + Detail Drawer) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className={selectedTooth ? "lg:col-span-2" : "lg:col-span-3"}>
          <OdontogramCanvas
            teeth={teeth}
            dentitionType={dentitionType}
            numberingSystem={numberingSystem}
            selectedTooth={selectedTooth}
            onSelectTooth={(tooth) => {
              setSelectedToothId(tooth.id);
              setSelectedSurfaces([]);
            }}
            onSelectSurface={(surface, tooth) => {
              setSelectedToothId(tooth.id);
              handleToggleSurface(surface);
            }}
            onChangeDentition={(dent) => {
              setDentitionType(dent);
              setSelectedToothId(null);
            }}
            onChangeNumberingSystem={setNumberingSystem}
          />
        </div>

        {/* Selected Tooth Detail Panel */}
        {selectedTooth && (
          <div className="lg:col-span-1">
            <ToothDetailPanel
              tooth={selectedTooth}
              numberingSystem={numberingSystem}
              onClose={() => {
                setSelectedToothId(null);
                setSelectedSurfaces([]);
              }}
              onUpdateStatus={async (status, notes) => {
                await updateToothMutation.mutateAsync({
                  toothId: selectedTooth.id,
                  status,
                  notes,
                });
              }}
              onUpdateSurface={async (surface, condition, treatment) => {
                await updateSurfaceMutation.mutateAsync({
                  toothId: selectedTooth.id,
                  surface,
                  condition,
                  treatment,
                });
              }}
            />
          </div>
        )}
      </div>
    </main>
  );
}
