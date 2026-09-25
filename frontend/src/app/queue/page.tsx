"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/context/AuthContext";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getRiskBadgeVariant, formatDate } from "@/lib/utils";
import { CaseResponse } from "@/types/api";
import {
  Inbox,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Cpu,
  Search,
  ArrowUpDown,
  ChevronRight,
  Filter,
  ShieldAlert,
  Flame,
} from "lucide-react";

export default function DoctorQueuePage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const [page, setPage] = useState(1);
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [sortBy, setSortBy] = useState<"created_at" | "probability">("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Fetch pending cases
  const {
    data: queueData,
    isLoading: casesLoading,
    refetch,
  } = useQuery({
    queryKey: ["doctor-queue", page],
    queryFn: () => api.getCases({ status: "pending", page, limit: 20 }),
    enabled: isAuthenticated && user?.role === "doctor",
  });

  // Fetch clinical dashboard stats
  const { data: statsData } = useQuery({
    queryKey: ["clinical-stats"],
    queryFn: () => api.getDashboardStats(),
    enabled: isAuthenticated && user?.role === "doctor",
    refetchInterval: 30000,
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
        <p className="text-sm text-slate-600 dark:text-slate-400">
          This triage queue is restricted to authorized physicians and radiologists. Please sign in with a clinical account.
        </p>
        <Button onClick={() => router.push("/login")} className="bg-indigo-600 hover:bg-indigo-700 text-white">
          Switch Account
        </Button>
      </div>
    );
  }

  // Filter and sort items locally
  const rawItems: CaseResponse[] = queueData?.items || [];
  const filteredItems = rawItems
    .filter((c: CaseResponse) => (riskFilter === "ALL" ? true : c.risk_band === riskFilter))
    .sort((a: CaseResponse, b: CaseResponse) => {
      const probA = a.calibrated_probability ?? a.cancer_probability ?? 0;
      const probB = b.calibrated_probability ?? b.cancer_probability ?? 0;
      if (sortBy === "probability") {
        return sortOrder === "desc" ? probB - probA : probA - probB;
      }
      return sortOrder === "desc"
        ? new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        : new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
    });

  return (
    <div className="space-y-8">
      {/* Clinician Dashboard Header */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-t-4 border-t-amber-500 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center justify-between">
              <span>Pending Reviews</span>
              <Clock className="h-4 w-4 text-amber-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {statsData ? statsData.pending_cases : queueData?.total || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Awaiting specialist evaluation</p>
          </CardContent>
        </Card>

        <Card className="border-t-4 border-t-red-600 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center justify-between">
              <span>High-Risk Priority</span>
              <Flame className="h-4 w-4 text-red-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {statsData?.high_risk_pending ?? rawItems.filter((i: CaseResponse) => i.risk_band === "High Risk").length}
            </div>
            <p className="text-xs text-slate-500 mt-1">Recommended expedited review</p>
          </CardContent>
        </Card>

        <Card className="border-t-4 border-t-emerald-500 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center justify-between">
              <span>Total Reviewed</span>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-slate-900 dark:text-white">
              {statsData?.reviewed_cases ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Archived verified cases</p>
          </CardContent>
        </Card>

        <Card className="border-t-4 border-t-indigo-600 shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wider text-slate-500 font-semibold flex items-center justify-between">
              <span>Active Model</span>
              <Cpu className="h-4 w-4 text-indigo-500" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-bold text-slate-900 dark:text-white truncate">
              {statsData?.model_version || "ResNet-50 v2.0"}
            </div>
            <p className="text-xs text-slate-500 mt-1 uppercase font-mono">
              Device: {statsData?.model_device || statsData?.device || "CUDA/CPU"}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Triage Workspace Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
            Clinical Triage Queue
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Specialist review queue sorted by risk urgency. High risk cases trigger automatic priority flags.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Risk Band Filter */}
          <div className="inline-flex items-center gap-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg p-1 text-xs">
            <Filter className="h-3.5 w-3.5 text-slate-400 ml-1" />
            {["ALL", "High Risk", "Borderline", "Low Risk"].map((rf) => (
              <button
                key={rf}
                onClick={() => setRiskFilter(rf)}
                className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                  riskFilter === rf
                    ? "bg-slate-900 text-white dark:bg-teal-600"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                {rf}
              </button>
            ))}
          </div>

          {/* Sort By Probability toggle */}
          <Button
            size="sm"
            variant="outline"
            className="text-xs gap-1.5 h-8"
            onClick={() => {
              if (sortBy === "probability") {
                setSortOrder(sortOrder === "desc" ? "asc" : "desc");
              } else {
                setSortBy("probability");
                setSortOrder("desc");
              }
            }}
          >
            <ArrowUpDown className="h-3.5 w-3.5" />
            {sortBy === "probability"
              ? `Risk ${sortOrder === "desc" ? "↓ High First" : "↑ Low First"}`
              : "Sort by Risk %"}
          </Button>

          {/* Sort by Date toggle */}
          <Button
            size="sm"
            variant="outline"
            className="text-xs gap-1.5 h-8"
            onClick={() => {
              if (sortBy === "created_at") {
                setSortOrder(sortOrder === "desc" ? "asc" : "desc");
              } else {
                setSortBy("created_at");
                setSortOrder("desc");
              }
            }}
          >
            <Clock className="h-3.5 w-3.5" />
            {sortBy === "created_at"
              ? `Date ${sortOrder === "desc" ? "↓ Newest" : "↑ Oldest"}`
              : "Sort by Date"}
          </Button>
        </div>
      </div>

      {/* Case Table / Card List */}
      {casesLoading ? (
        <div className="py-20 text-center space-y-3">
          <div className="h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-500">Loading cases in queue...</p>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-800 p-12 text-center space-y-3">
          <CheckCircle2 className="h-10 w-10 text-emerald-500 mx-auto" />
          <h3 className="font-serif text-lg font-bold text-slate-800 dark:text-slate-200">
            Triage Queue Clear
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {riskFilter !== "ALL"
              ? `No pending cases matching "${riskFilter}". Try selecting "ALL" filters.`
              : "All submitted cases have been thoroughly reviewed. Check the Reviewed Archive for historical cases."}
          </p>
          <Link href="/reviewed">
            <Button variant="outline" size="sm" className="mt-2 text-xs">
              Open Reviewed Archive
            </Button>
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-xs uppercase tracking-wider text-slate-500 font-semibold">
                <tr>
                  <th className="px-6 py-3.5">Priority / Case ID</th>
                  <th className="px-6 py-3.5">Patient Identifier</th>
                  <th className="px-6 py-3.5">AI Prediction</th>
                  <th className="px-6 py-3.5">Calibrated Probability</th>
                  <th className="px-6 py-3.5">Risk Tier</th>
                  <th className="px-6 py-3.5">Submitted</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredItems.map((c: CaseResponse) => {
                  const isHighPriority = c.risk_band === "High Risk";
                  const isBorderline = c.risk_band === "Borderline" || c.risk_band === "Borderline / Indeterminate";
                  const prob = c.calibrated_probability ?? c.cancer_probability ?? 0;
                  const pred = c.predicted_class || c.model_prediction || "AI Scanned";

                  return (
                    <tr
                      key={c.id}
                      className={`hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition ${
                        isHighPriority ? "bg-red-50/30 dark:bg-red-950/10" : ""
                      }`}
                    >
                      <td className="px-6 py-4 font-mono font-medium flex items-center gap-2">
                        {isHighPriority && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 animate-pulse">
                            URGENT
                          </span>
                        )}
                        {isBorderline && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
                            UNCERTAIN
                          </span>
                        )}
                        <span>#{c.id}</span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-900 dark:text-white">
                          {c.patient_name || `Patient #${c.patient_id}`}
                        </div>
                        <div className="text-xs text-slate-400">ID: {c.patient_id}</div>
                      </td>

                      <td className="px-6 py-4 font-medium text-slate-800 dark:text-slate-200">
                        {pred}
                      </td>

                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-white">
                        {(prob * 100).toFixed(1)}%
                      </td>

                      <td className="px-6 py-4">
                        <Badge variant={getRiskBadgeVariant(c.risk_band)}>
                          {c.risk_band}
                        </Badge>
                      </td>

                      <td className="px-6 py-4 text-xs text-slate-500">
                        {formatDate(c.created_at)}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Link href={`/queue/${c.id}`}>
                          <Button
                            size="sm"
                            className={
                              isHighPriority
                                ? "bg-red-600 hover:bg-red-700 text-white font-semibold gap-1.5 shadow-sm"
                                : "bg-indigo-600 hover:bg-indigo-700 text-white font-medium gap-1.5"
                            }
                          >
                            Review Workspace <ChevronRight className="h-4 w-4" />
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
