"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api, getMediaUrl } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getRiskBadgeVariant, formatDate } from "@/lib/utils";
import { CaseResponse } from "@/types/api";
import {
  Archive,
  Search,
  Filter,
  Download,
  CheckCircle2,
  Calendar,
  FileCheck,
  ChevronRight,
  ShieldAlert,
  Clock,
} from "lucide-react";

export default function DoctorReviewedArchivePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [verdictFilter, setVerdictFilter] = useState("ALL");

  const {
    data: reviewedData,
    isLoading,
  } = useQuery({
    queryKey: ["reviewed-archive"],
    queryFn: () => api.getCases({ status: "reviewed", limit: 50 }),
    enabled: isAuthenticated && user?.role === "doctor",
  });

  if (authLoading) {
    return (
      <div className="flex justify-center py-24">
        <div className="h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (user?.role !== "doctor") {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <ShieldAlert className="h-12 w-12 text-amber-600 mx-auto" />
        <h2 className="font-serif text-2xl font-bold">Clinician Access Required</h2>
        <Button onClick={() => router.push("/login")} className="bg-indigo-600 text-white">
          Sign In
        </Button>
      </div>
    );
  }

  const items: CaseResponse[] = reviewedData?.items || [];

  const filteredItems = items.filter((c: CaseResponse) => {
    const matchesSearch =
      (c.patient_name?.toLowerCase() || "").includes(searchTerm.toLowerCase()) ||
      c.id.toString().includes(searchTerm) ||
      (c.doctor_explanation?.toLowerCase() || "").includes(searchTerm.toLowerCase()) ||
      (c.recommendation?.toLowerCase() || "").includes(searchTerm.toLowerCase());

    const matchesVerdict =
      verdictFilter === "ALL" ||
      (c.doctor_verdict?.toLowerCase() || "").includes(verdictFilter.toLowerCase());

    return matchesSearch && matchesVerdict;
  });

  const handleDownloadPdf = async (id: string | number) => {
    try {
      const blob = await api.downloadPdfReport(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `CareLens_Clinical_Report_${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      alert("Unable to generate PDF report.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Archive className="h-6 w-6 text-indigo-600" /> Reviewed Cases Archive
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Historical record of finalized diagnostic reviews, pathology conclusions, and clinical exports.
          </p>
        </div>

        <Link href="/queue">
          <Button variant="outline" className="text-xs gap-1.5">
            <Clock className="h-4 w-4" /> Go to Triage Queue
          </Button>
        </Link>
      </div>

      {/* Search and Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by patient name, case #, notes, or findings..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Verdict filter tabs */}
        <div className="flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1 text-xs shrink-0">
          <Filter className="h-3.5 w-3.5 text-slate-400 ml-1" />
          {["ALL", "Benign", "Malignant", "Inconclusive"].map((v) => (
            <button
              key={v}
              onClick={() => setVerdictFilter(v)}
              className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                verdictFilter === v
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </div>

      {/* Archive List */}
      {isLoading ? (
        <div className="py-20 text-center space-y-3">
          <div className="h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-500">Loading archived case records...</p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-12 text-center space-y-3">
          <CheckCircle2 className="h-10 w-10 text-slate-400 mx-auto" />
          <h3 className="font-serif text-lg font-bold text-slate-800 dark:text-slate-200">
            No Cases Found
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            No reviewed cases match your search criteria.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Case #</th>
                  <th className="px-6 py-3.5">Patient</th>
                  <th className="px-6 py-3.5">AI Classification</th>
                  <th className="px-6 py-3.5">Clinical Verdict</th>
                  <th className="px-6 py-3.5">Reviewer</th>
                  <th className="px-6 py-3.5">Reviewed Date</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredItems.map((c: CaseResponse) => {
                  const prob = c.calibrated_probability ?? c.cancer_probability ?? 0;
                  const pred = c.predicted_class || c.model_prediction || "AI Scanned";

                  return (
                    <tr key={c.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition">
                      <td className="px-6 py-4 font-mono font-medium text-slate-900 dark:text-white">
                        #{c.id}
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900 dark:text-white">
                          {c.patient_name || `Patient #${c.patient_id}`}
                        </div>
                        <div className="text-xs text-slate-400">ID: {c.patient_id}</div>
                      </td>

                      <td className="px-6 py-4">
                        <span className="font-medium">{pred}</span>
                        <div className="text-xs text-slate-500">
                          {(prob * 100).toFixed(1)}% • {c.risk_band}
                        </div>
                      </td>

                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {c.doctor_verdict}
                      </span>
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-600 dark:text-slate-400">
                      Dr. {c.reviewed_by_doctor_id || "Physician"}
                    </td>

                    <td className="px-6 py-4 text-xs text-slate-500">
                      {formatDate(c.reviewed_at)}
                    </td>

                    <td className="px-6 py-4 text-right space-x-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadPdf(c.id)}
                        className="text-xs gap-1.5"
                      >
                        <Download className="h-3.5 w-3.5" /> PDF
                      </Button>
                      <Link href={`/queue/${c.id}`}>
                        <Button size="sm" variant="ghost" className="text-xs gap-1">
                          Inspect <ChevronRight className="h-3.5 w-3.5" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
