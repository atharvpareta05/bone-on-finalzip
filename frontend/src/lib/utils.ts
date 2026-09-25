import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { RiskBand, CaseStatus } from "@/types/api";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(isoStr?: string | null): string {
  if (!isoStr) return "N/A";
  try {
    const d = new Date(isoStr);
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(d);
  } catch {
    return isoStr;
  }
}

export function getRiskBadgeVariant(riskBand?: string | null): "default" | "secondary" | "destructive" | "outline" | "success" {
  if (!riskBand) return "secondary";
  const r = riskBand.toLowerCase();
  if (r.includes("high")) return "destructive";
  if (r.includes("borderline") || r.includes("indeterminate")) return "secondary";
  if (r.includes("low")) return "success";
  return "default";
}

export function getStatusBadgeVariant(status?: string | null): "default" | "secondary" | "destructive" | "outline" | "success" {
  if (!status) return "secondary";
  const s = status.toLowerCase();
  if (s.includes("reviewed")) return "success";
  if (s.includes("in review")) return "default";
  return "secondary";
}

export function getRiskBandConfig(riskBand: RiskBand | string) {
  const r = riskBand?.toLowerCase() || "";
  if (r.includes("high")) {
    return {
      badgeBg: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/60",
      borderTop: "border-t-red-500",
      indicator: "bg-red-500",
      label: "High Risk (≥ 60%)",
    };
  }
  if (r.includes("borderline") || r.includes("indeterminate")) {
    return {
      badgeBg: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-900/60",
      borderTop: "border-t-amber-500",
      indicator: "bg-amber-500",
      label: "Borderline (35–60%)",
    };
  }
  return {
    badgeBg: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60",
    borderTop: "border-t-emerald-500",
    indicator: "bg-emerald-500",
    label: "Low Risk (< 35%)",
  };
}

export function getStatusConfig(status: CaseStatus | string) {
  const s = status?.toLowerCase() || "";
  if (s.includes("reviewed")) {
    return {
      badgeBg: "bg-teal-50 text-teal-800 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800",
      dotBg: "bg-teal-600",
      step: 4,
    };
  }
  if (s.includes("in review")) {
    return {
      badgeBg: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
      dotBg: "bg-blue-500",
      step: 3,
    };
  }
  if (s.includes("analyzed") || s.includes("pending")) {
    return {
      badgeBg: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
      dotBg: "bg-amber-500",
      step: 2,
    };
  }
  return {
    badgeBg: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
    dotBg: "bg-slate-400",
    step: 1,
  };
}
