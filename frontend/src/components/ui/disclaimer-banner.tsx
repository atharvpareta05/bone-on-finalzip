import React from "react";
import { AlertTriangle, ShieldCheck } from "lucide-react";

export function DisclaimerBanner({ compact = false }: { compact?: boolean }) {
  if (compact) {
    return (
      <div
        role="note"
        aria-label="Clinical Decision-Support Notice"
        className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/60 rounded text-xs text-amber-800 dark:text-amber-300"
      >
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
        <span>
          <strong>Investigational Decision Support:</strong> AI output assists but does not replace qualified medical diagnosis.
        </span>
      </div>
    );
  }

  return (
    <aside
      role="note"
      aria-label="Clinical AI Regulatory Disclaimer"
      className="bg-teal-50/70 dark:bg-teal-950/30 border-l-4 border-teal-600 dark:border-teal-500 p-3.5 rounded-r-lg my-3 shadow-xs"
    >
      <div className="flex items-start gap-3">
        <ShieldCheck className="w-5 h-5 text-teal-700 dark:text-teal-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
          <span className="font-semibold text-teal-900 dark:text-teal-200 uppercase tracking-wide mr-1.5">
            Clinical Decision-Support System
          </span>
          CareLens plain radiograph analytics and Grad-CAM interpretability maps are intended solely to assist credentialed physicians.
          This system is not an autonomous diagnostic medical device. Final clinical management must correlate with patient history, physical examination, and multi-modal diagnostic confirmation.
        </div>
      </div>
    </aside>
  );
}
