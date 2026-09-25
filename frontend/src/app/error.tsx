"use client";

import React, { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import Link from "next/link";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Clinical Application Runtime Error:", error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-6">
      <div className="max-w-md w-full p-8 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl text-center space-y-5">
        <div className="p-3 bg-red-100 dark:bg-red-950/60 text-red-600 dark:text-red-400 rounded-full w-fit mx-auto">
          <AlertTriangle className="h-10 w-10" />
        </div>

        <div className="space-y-2">
          <h2 className="font-serif text-2xl font-bold text-slate-900 dark:text-white">
            System Communication Interrupted
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
            The clinical decision-support portal encountered an unexpected runtime error or backend communication failure. Patient data has not been lost.
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs text-slate-500 font-mono text-left break-all">
          {error.message || "An unspecified system fault occurred."}
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <Button onClick={() => reset()} className="w-full sm:w-auto bg-teal-600 hover:bg-teal-700 text-white gap-2">
            <RefreshCw className="h-4 w-4" /> Try Again
          </Button>
          <Link href="/" className="w-full sm:w-auto">
            <Button variant="outline" className="w-full sm:w-auto gap-2">
              <Home className="h-4 w-4" /> Return to Home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
