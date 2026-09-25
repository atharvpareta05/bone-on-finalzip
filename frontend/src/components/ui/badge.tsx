import React from "react";
import { cn, getRiskBandConfig, getStatusConfig } from "@/lib/utils";
import { CaseStatus, RiskBand } from "@/types/api";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "success";
}

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-teal-500/10 text-teal-800 border-teal-200 dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800",
    secondary: "bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700",
    destructive: "bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-900/60",
    outline: "text-slate-700 border-slate-300 dark:text-slate-300 dark:border-slate-700",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900/60",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide",
        variantStyles[variant] || variantStyles.default,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function RiskBadge({ riskBand }: { riskBand: RiskBand | string }) {
  const config = getRiskBandConfig(riskBand);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide",
        config.badgeBg
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", config.indicator)} />
      {riskBand}
    </span>
  );
}

export function StatusBadge({ status }: { status: CaseStatus | string }) {
  const config = getStatusConfig(status);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border tracking-wide",
        config.badgeBg
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", config.dotBg)} />
      {status}
    </span>
  );
}
