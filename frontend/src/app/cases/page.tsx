"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { casesApi } from "@/lib/api-client";
import { CaseResponse, PaginatedCasesResponse } from "@/types/api";
import { FileText, UploadCloud, ChevronRight, Clock, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RiskBadge, StatusBadge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";
import { DisclaimerBanner } from "@/components/ui/disclaimer-banner";

export default function PatientCasesPage() {
  const [data, setData] = useState<PaginatedCasesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadCases() {
      try {
        const res = await casesApi.listCases(1, 30);
        setData(res);
      } catch (err: any) {
        setError(err.message || "Failed loading clinical records.");
      } finally {
        setIsLoading(false);
      }
    }
    loadCases();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="font-serif text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            My Radiograph Submissions
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Track submitted X-ray scans, AI saliency projections, and physician reviews.
          </p>
        </div>
        <Link href="/upload">
          <Button variant="primary" size="md">
            <UploadCloud className="w-4 h-4 mr-2" />
            Upload New Scan
          </Button>
        </Link>
      </div>

      <DisclaimerBanner />

      {error && (
        <div
          role="alert"
          className="mb-6 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 text-sm text-red-700 dark:text-red-300 flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-xl bg-slate-200 dark:bg-slate-800 animate-pulse" />
          ))}
        </div>
      ) : !data?.items || data.items.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-400 mx-auto mb-3">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="font-serif text-lg font-bold text-slate-800 dark:text-slate-200">No Scans Submitted Yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-5">
              Upload a plain bone radiograph to receive automated Grad-CAM interpretability maps and physician reviews.
            </p>
            <Link href="/upload">
              <Button variant="primary" size="md">
                <UploadCloud className="w-4 h-4 mr-2" />
                Upload Your First Scan
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {data.items.map((c) => (
            <Link key={c.id} href={`/cases/${c.id}`} className="block group">
              <Card className="hover:border-teal-500 dark:hover:border-teal-600 transition-colors shadow-xs">
                <CardContent className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  {/* Left: Thumbnail & Info */}
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-lg bg-black border border-slate-700 overflow-hidden shrink-0 flex items-center justify-center">
                      <img
                        src={casesApi.getMediaUrl(c.id, "original")}
                        alt={`Scan ${c.id}`}
                        className="w-full h-full object-cover"
                        loading="lazy"
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-slate-900 dark:text-slate-100">
                          {c.id}
                        </span>
                        <StatusBadge status={c.status} />
                      </div>
                      <span className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mt-1">
                        {c.model_prediction}
                      </span>
                      <span className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-0.5">
                        <Clock className="w-3.5 h-3.5" />
                        Submitted on {formatDate(c.created_at)}
                      </span>
                    </div>
                  </div>

                  {/* Right: Risk Badge, Verdict & Arrow */}
                  <div className="flex items-center justify-between sm:justify-end gap-4 border-t sm:border-t-0 pt-3 sm:pt-0 border-slate-100 dark:border-slate-800">
                    <div className="text-left sm:text-right">
                      <RiskBadge riskBand={c.risk_band} />
                      {c.doctor_verdict && (
                        <span className="block text-xs font-bold text-teal-800 dark:text-teal-300 mt-1">
                          Verdict: {c.doctor_verdict}
                        </span>
                      )}
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-400 group-hover:text-teal-600 transition-colors shrink-0" />
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
